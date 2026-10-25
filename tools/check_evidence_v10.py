"""Execute two-adapter adoption and labelled record-corruption/boundary challenges.

Only genuine tank simulations go in its separate example directory. Synthetic
corruption witnesses are audit fixtures, never scientific neural run results.
"""
import argparse
import copy
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from evidence_v10.contract import audit,prefix,Campaign
from evidence_v10.fly_adapter import FlyAdapter
from evidence_v10.tank import TankAdapter,run


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def challenge(records,spec,adapter):
    base=records[:];cases=[]
    def test(name,mutator,layer):
        rr=copy.deepcopy(base);mutator(rr);issues=audit(rr,spec,adapter)
        cases.append(dict(error=name,expected='detected',detected=bool(issues),layer=layer,
                          issue_codes=sorted({i.code for i in issues})))
    test('missing paired condition',lambda rs:rs.pop(),'generic matrix')
    test('duplicate trial replacing a condition',lambda rs:rs.__setitem__(1,copy.deepcopy(rs[0])),'generic matrix')
    test('swapped source/config/map/calibration binding',lambda rs:rs[0].bindings.__setitem__('swapped','foreign'),'generic binding')
    test('same seed label but different shared input stream',lambda rs:setattr(rs[0],'uniform_sha256','f'*64),'generic pairing')
    test('fault mask changed across laws/bearings',lambda rs:setattr(rs[0],'mask_sha256','f'*64),'generic pairing + adapter')
    test('milliseconds mislabelled as seconds',lambda rs:rs[0].frames[0].__setitem__('end_s',1000*rs[0].frames[0]['end_s']),'generic timing')
    test('truncated resource exposure',lambda rs:rs[0].frames.pop(),'generic exposure')
    test('decreasing cumulative resource',lambda rs:rs[0].frames[2].__setitem__('resource',-1),'generic accounting')
    test('decision used before it exists',lambda rs:rs[0].frames[0].__setitem__('usable_after_s',-.1),'generic causality')
    test('nonfinite decision time',lambda rs:rs[0].frames[0].__setitem__('decision_s',float('nan')),'generic schema')
    test('success despite a recorded failure',lambda rs:setattr(rs[0],'success',rs[0].failure_s is not None),'generic endpoint')
    if isinstance(adapter,TankAdapter):
        test('missing native measurement field',lambda rs:rs[0].native['log'][0].pop('measurement'),'adapter schema')
        test('rounded delayed actuation to frame boundary',lambda rs:rs[0].native['log'][1].__setitem__('available_s',.4),'tank exact-event replay')
        test('same-frame applied control',lambda rs:rs[0].native['log'][3]['segments'][0].__setitem__('outflow',.399),'tank dynamics/causality replay')
    else:
        test('missing native smoothing field',lambda rs:rs[0].native['log'][0].pop('smooth_rates'),'adapter schema')
        test('wrong exact-horizon burst flag',lambda rs:rs[0].native.__setitem__('burst_active_at_horizon',not rs[0].native['burst_active_at_horizon']),'fly exact-event replay')
        test('altered body-frame bearing',lambda rs:rs[0].native['log'][6].__setitem__('phi_now',rs[0].native['log'][6]['phi_now']+10),'fly geometry/input replay')
    x=copy.deepcopy(base[0]);before=prefix(x,.4)
    x.failure_s=.8 if x.failure_s is None else None;x.success=x.failure_s is None
    for q in x.frames:
        if q['end_s']>.4:q['resource']+=99999
    assert prefix(x,.4)==before,'prefix API leaked future frames/labels'
    return cases


def untrusted_neural_witness(adapter,original):
    """Concrete blind spot: a dishonest logger with zeroed, unverified readouts.

    No neural equations are executed. The internally consistent synthetic trace
    is explicitly an audit fixture and cannot enter any experimental analysis.
    """
    import task_v9
    import pandas as pd
    class SyntheticReadout:
        w0=range(original['n_connection_rows'])
        pool_flyids=np.array([int(x) for x in adapter.im['pool_flyids']])
        pool_pos={int(x):i for i,x in enumerate(adapter.im['pool_flyids'])}
        flyid2i={int(x):i for i,x in enumerate(adapter.im['pool_flyids']+[q['flyid'] for q in adapter.im['commands']])}
        sens_flyids=np.array([int(x['flyid']) for x in adapter.im['sensory']])
        mon_all=SimpleNamespace(num_spikes=0)
        def reset_state(self):pass
        def apply_weights(self,w):raise ValueError('healthy audit fixture only')
        def set_frame_rates(self,rates):
            base=np.zeros(len(self.pool_flyids));positions=[self.pool_pos[int(x)] for x in self.sens_flyids];base[positions]=rates
            u=task_v9.input_uniforms(self.input_seed,self.input_frame,len(base));self.uniform_hash.update(u.tobytes())
            times,indices=np.nonzero(u<base[None,:]*.0001)
            self.event_hash.update(np.column_stack([times,indices]).astype('<i4').tobytes());self.input_frame+=1
        def run_frame(self,t):pass
        def spike_records(self,ids):return dict(i=np.array([],dtype=int),t_ms=np.array([]))
    rf=pd.DataFrame([dict(root_id=int(q['flyid']),phi_deg=q['phi_deg'],psi_deg=q['psi_deg'],w_grad=q['w_grad']) for q in adapter.im['sensory']])
    cmd=pd.DataFrame([dict(flyid=int(q['flyid'])) for q in adapter.im['commands']])
    synthetic=task_v9.run(SyntheticReadout(),rf,cmd,original['seed'],original['phi_deg'],'healthy',original['mode'],adapter.cal)
    witness={**original,**synthetic,'audit_fixture_kind':'SYNTHETIC_UNTRUSTED_LOGGER_NO_NEURAL_DYNAMICS'}
    e=adapter.normalize(witness);spec=Campaign((e.cluster,),(e.condition,),(e.law,),(e.fault,),1.,.02,'network spikes')
    issues=audit([e],spec,adapter)
    return dict(expected='not certified by trace/input audit',trace_check_passed=not issues,
        neural_dynamics_executed=False,zero_readout_fixture=True,scientific_result=False,
        fixture_sha256=hashlib.sha256(json.dumps(witness,sort_keys=True).encode()).hexdigest(),
        interpretation='Consistent records and matching claimed source hashes do not authenticate execution or prove the neural equations were solved.',issues=[asdict(i) for i in issues])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    for p in [Path(__file__).resolve(),*(ROOT/'evidence_v10').glob('*.py')]:
        target=a.out/'source'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    tank=TankAdapter();raw=a.out/'tank-raw';raw.mkdir()
    tr=[]
    for seed,c,m,f in itertools.product(tank.spec.clusters,tank.spec.conditions,tank.spec.laws,tank.spec.faults):
        row=run(seed,c,m,f);(raw/f'{seed}_{c}_{m}_{f}.json').write_text(json.dumps(row)+'\n');tr.append(tank.normalize(row))
    tank_issues=audit(tr,tank.spec,tank)
    fly=FlyAdapter(ROOT/'runs/task-v9-test',ROOT/'runs/task-v9-frozen/calibration.json',ROOT/'runs/task-v9-frozen/registration-core.json')
    fr=fly.load();fly_issues=audit(fr,fly.spec,fly)
    cases={}
    for name,records,spec,adapter in [('tank',tr,tank.spec,tank),('fly',fr,fly.spec,fly)]:
        seed=min(spec.clusters);subset=[r for r in records if r.cluster==seed]
        sub=Campaign((seed,),spec.conditions,spec.laws,spec.faults,spec.horizon_s,spec.frame_s,spec.resource_unit)
        cases[name]=challenge(subset,sub,adapter)
    original=next(r.native for r in fr if r.fault=='healthy')
    witness=untrusted_neural_witness(fly,original)
    passed=not tank_issues and not fly_issues and all(q['detected'] for v in cases.values() for q in v) and witness['trace_check_passed']
    result=dict(passed=passed,seconds=time.perf_counter()-started,
        clean_records=dict(tank=len(tr),fly=len(fr)),clean_issues=dict(tank=[asdict(i) for i in tank_issues],fly=[asdict(i) for i in fly_issues]),
        corruption_cases=cases,prefix_future_invariance=True,untrusted_neural_witness=witness,
        tank_success=sum(r.success for r in tr),tank_records=len(tr),tank_scope='Independent small adoption example; sensor deletions, no neural performance comparison or cross-plant pooling.',
        source_sha256={str(p.resolve().relative_to(ROOT)):sha(p) for p in [Path(__file__),*(ROOT/'evidence_v10').glob('*.py')]},
        raw_fly_inputs={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'runs/task-v9-test/episodes').glob('*.json')},
        boundaries=['Conditional on trusted configuration and logs; not execution attestation','No neural-state/solver certification','No biological/physical validity or hardware/energy/safety guarantee','CRN does not guarantee variance reduction for arbitrary feedback systems'])
    (a.out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['raw_fly_inputs','source_sha256']},indent=2))
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
