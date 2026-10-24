"""Analyse only the complete fixed two-map campaign; apply the FOUR-test family.

Per-map conditional intervals are kept separate. Never use this collector to
select maps, change thresholds, or pool repeated conditions as independent data.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_v10.contract import audit
from evidence_v10.fly_adapter import FlyAdapter


def holm(pvalues):
    if not pvalues or any(not math.isfinite(p) or not 0<=p<=1 for p in pvalues.values()):
        raise ValueError('invalid complete p-value family')
    ordered=sorted(pvalues,key=lambda k:(pvalues[k],k));result={};prior=0.
    for i,k in enumerate(ordered):
        prior=max(prior,min(1.,(len(ordered)-i)*pvalues[k]));result[k]=prior
    return result


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def descriptive(rs):
    """400-ms heading and clearance capped at first contact; not mediation."""
    output=[]
    for mode in ['proportional','relay']:
        group=[r for r in rs if r['mode']==mode and r['fault']=='healthy'];rows=[]
        for r in group:
            logs=[q for q in r['log'] if q['t_end_ms']<=400]
            if r['collision_ms'] is not None and r['collision_ms']<=400:raise ValueError('post-contact control diagnostic')
            angles=np.array([0.]+[q['heading_deg'] for q in logs])
            rows.append(dict(seed=r['seed'],phi_deg=r['phi_deg'],success=r['escaped'],
                clearance_to_first_contact_or_horizon_mm=0. if not r['escaped'] else 1000*(r['min_distance']-.05),
                abs_heading_400_deg=abs(angles[-1]),heading_total_variation_400_deg=float(np.abs(np.diff(angles)).sum())))
        output.append(dict(mode=mode,episodes=len(rows),successes=sum(q['success'] for q in rows),
            median_clearance_mm=float(np.median([q['clearance_to_first_contact_or_horizon_mm'] for q in rows])),
            median_abs_heading_400_deg=float(np.median([q['abs_heading_400_deg'] for q in rows])),
            median_heading_total_variation_400_deg=float(np.median([q['heading_total_variation_400_deg'] for q in rows])),rows=rows))
    return output


def primary(rs,reg):
    seeds=reg['test_seeds'];lookup={(r['seed'],r['phi_deg'],r['mode'],r['fault']):r for r in rs}
    ids=np.random.default_rng(reg['bootstrap']['seed']).integers(0,len(seeds),(reg['bootstrap']['draws'],len(seeds)))
    output=[]
    for mode in reg['modes']:
        for fault in ['F2_25','F2_50']:
            rows=[]
            for seed in seeds:
                pairs=[(lookup[seed,p,mode,'healthy']['escaped'],lookup[seed,p,mode,fault]['escaped']) for p in reg['phis']]
                losses=np.mean([h and not f for h,f in pairs]);gains=np.mean([not h and f for h,f in pairs])
                rows.append(dict(seed=seed,loss=float(losses),gain=float(gains),net_loss=float(losses-gains)))
            estimates={}
            for k in ['loss','gain','net_loss']:
                values=np.array([q[k] for q in rows]);boot=values[ids].mean(axis=1)
                estimates[k]=dict(estimate=float(values.mean()),ci95=np.quantile(boot,[.025,.975]).tolist(),
                    role='derived' if k=='net_loss' else 'registered_primary',unit='proportion',
                    display_scale=100,display_unit='percentage points' if k=='net_loss' else 'percent of paired scenarios')
                if k in ['loss','gain']:
                    estimates[k]['zero_event_any_cluster_upper95']=float(1-.05**(1/len(seeds))) if np.all(values==0) else None
            output.append(dict(mode=mode,fault=fault,estimands=estimates,per_seed=rows))
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['root','design','out']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();started=time.perf_counter();design=json.loads(a.design.read_text())
    complete=json.loads((a.root/'completed.json').read_text())
    if complete['expected_episodes']!=392 or complete['design_sha256']!=sha(a.design):raise ValueError('campaign completion/design')
    assert [q['map_id'] for q in design['maps']]==['A','B']
    a.out.mkdir(parents=True,exist_ok=False)
    binding_cmd=[sys.executable,'-X','utf8','tools/check_rf_input_binding_v10.py',
                 '--root',str(a.root),'--design',str(a.design),'--out',str(a.out/'rf-input-binding.json')]
    with (a.out/'rf-input-binding.log').open('x') as log:
        done=subprocess.run(binding_cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    if done.returncode:raise RuntimeError('frozen RF/phase input binding failed')
    def one(spec):
        tag=spec['map_id'];base=a.root/('map-'+tag);out=a.out/('map-'+tag);out.mkdir()
        regpath=base/'registration.json';reg=json.loads(regpath.read_text())
        if reg['test_seeds']!=spec['test_seeds'] or reg['rf_map_sha256']!=spec['sha256']:raise ValueError('wrong registered cohort/map')
        commands=[]
        for name,target,args in [
            ('analysis','analyze_task_v10.py',['--root',base/'test','--registration',regpath]),
            ('numbers','check_task_numbers_v9.py',['--root',base/'test','--analysis',out/'analysis','--registration',regpath]),
            ('replay','replay_audit_v9.py',['--root',base/'test','--calibration',base/'calibration.json']),
            ('decoder','decoder_validation_v10.py',['--root',base/'validation','--calibration',base/'calibration.json'])]:
            cmd=[sys.executable,'-X','utf8','tools/run_v9.py','tools/'+target,*map(str,args),'--out',str(out/name)]
            with (out/(name+'.log')).open('x') as log:done=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            commands.append(dict(command=cmd,exit_code=done.returncode))
            if done.returncode:raise RuntimeError('failed '+tag+'/'+name+'; see '+str(out/(name+'.log')))
        adapter=FlyAdapter(base/'test',base/'calibration.json',regpath);records=adapter.load();issues=audit(records,adapter.spec,adapter)
        if issues:raise ValueError('evidence contract rejected map '+tag+': '+repr(issues[:5]))
        (out/'evidence.json').write_text(json.dumps(dict(passed=True,records=len(records),issues=[],
            interface_source_sha256={p.as_posix():sha(p) for p in Path('evidence_v10').glob('*.py')},
            scope='same generic contract and fly native adapter; no neural resimulation'),indent=2)+'\n')
        raw=[r.native for r in records];summary=json.loads((out/'analysis/summary.json').read_text())
        result=dict(map_id=tag,seed_clusters=len(spec['test_seeds']),records=len(raw),
            registration_sha256=sha(regpath),rf_map_sha256=spec['sha256'],
            validation_successes=reg['validation_successes'],validation_capability_pass=reg['validation_capability_pass'],
            counts=summary['counts'],primary=primary(raw,reg),
            secondary_interaction={dose:summary['cluster_effects'][dose+'_interaction'] for dose in ['F2_25','F2_50']},
            secondary_raw_p=summary['interaction_raw_p'],
            warning_scores=summary['warning_scores'],activity_ratios=summary['activity_ratios'],
            healthy_descriptive=descriptive(raw),commands=commands)
        (out/'map-summary.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    with ThreadPoolExecutor(max_workers=2) as pool:maps=list(pool.map(one,design['maps']))
    raw={q['map_id']+'/'+dose:p for q in maps for dose,p in q['secondary_raw_p'].items()}
    assert len(raw)==4
    corrected=holm(raw)
    report=dict(complete=True,experiment=design['experiment'],maps=maps,
        independent_unit='seed cluster conditional on map; 12 clusters per map, not pooled',
        primary='registered loss/gain and exposure; net loss is derived L minus G, not an additional primary endpoint; per-map complete seed bootstrap',
        secondary_interaction_raw_p=raw,secondary_interaction_holm_p=corrected,
        multiplicity_family='both maps x both doses, exactly four secondary interaction sensitivity tests',
        zero_event_caution='A degenerate bootstrap interval from no observed events does not prove zero population risk; sparse positive clusters limit warning inference.',
        reporting_safeguard='Post-registration reporting diagnostic: when all cluster losses/gains are zero, report 1-0.05^(1/n) for probability of ANY such event in a new identically defined cluster, not conditional FNR or a two-sided interval for signed net loss.',
        source_sha256=sha(__file__),design_sha256=sha(a.design),seconds=time.perf_counter()-started)
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(complete=True,maps=2,secondary_interaction_raw_p=raw,secondary_interaction_holm_p=corrected,seconds=report['seconds']),indent=2))


if __name__=='__main__':main()
