"""Reconstruct fixed RF calibration from development only using augmented least squares.

Checks source/data/role separation and validation-derived cutoffs without reading
any test episode. This verifies saved provenance, not absence of unlogged tuning.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from task_metrics_v9 import calibration_thresholds

ROOT = Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--design',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();inputs={};results=[];errors=[]
    def read(p):
        inputs[p.resolve().relative_to(ROOT).as_posix()]=sha(p)
        return json.loads(p.read_text())
    design=read(a.design)
    for spec in design['maps']:
        tag=spec['map_id'];base=a.root/('map-'+tag)
        cal=read(base/'calibration.json');reg=read(base/'registration.json')
        development=[read(p) for p in sorted((base/'development/episodes').glob('*.json'))]
        validation=[read(p) for p in sorted((base/'validation/episodes').glob('*.json'))]
        if len(development)!=20 or len(validation)!=32:raise ValueError('Incomplete pre-test cohorts')
        keys={(r['seed'],r['phi_deg']) for r in development}
        if keys!={(s,p) for s in spec['development_seeds'] for p in design['phyis_development']}:raise ValueError('Development matrix/role')
        if any(r['mode']!='observe' or r['fault']!='healthy' or r['horizon_ms']!=400 for r in development):raise ValueError('Development condition')
        if any(r['command_flyids']!=cal['command_flyids'] or r['rf_map_sha256']!=spec['sha256'] for r in development):raise ValueError('Feature identities/map')
        cohorts=[set(spec[k]) for k in ['development_seeds','validation_seeds','test_seeds']]
        if any(cohorts[i]&cohorts[j] for i in range(3) for j in range(i)):raise ValueError('Seed leakage')
        for name,h in {**cal['input_sha256'],**reg['validation_input_sha256']}.items():
            if sha(ROOT/name)!=h:raise ValueError('Calibration input changed: '+name)
        if set(cal['input_sha256'])!={p.relative_to(ROOT).as_posix() for p in (base/'development/episodes').resolve().glob('*.json')}:raise ValueError('Unexpected calibration input set')
        X=np.array([q['smooth_rates'] for r in development for q in r['log'] if 200<=q['t_end_ms']<=400])
        target=np.array([q['phi_now']/60 for r in development for q in r['log'] if 200<=q['t_end_ms']<=400])
        mean=X.mean(0);scale=np.maximum(X.std(0),1)
        A=np.column_stack([(X-mean)/scale,np.ones(len(X))])
        penalty=np.diag(np.r_[np.repeat(np.sqrt(10.),8),0.])
        coef=np.linalg.lstsq(np.vstack([A,penalty]),np.r_[target,np.zeros(9)],rcond=None)[0]
        weights=coef[:8]/scale;intercept=coef[8]-mean@weights
        trigger=max(2.5,np.percentile([np.mean([q['cmd_hz'] for q in r['log'] if 200<=q['t_end_ms']<=300]) for r in development],10)/2)
        checks=dict(
            ridge_weights=np.allclose(weights,cal['direction_weights'],rtol=0,atol=1e-10),
            ridge_intercept=bool(np.isclose(intercept,cal['direction_intercept'],rtol=0,atol=1e-10)),
            trigger=bool(np.isclose(trigger,cal['trigger_hz'],rtol=0,atol=1e-12)),
            fixed_control=cal['turn_gain_deg_s']==600 and cal['gate_silent'] is True,
            validation_cutoffs=calibration_thresholds(validation)==reg['thresholds'],
            calibration_binding=sha(base/'calibration.json')==reg['calibration_sha256'],
            design_binding=sha(a.design)==reg['design_sha256'],
            validation_seed_set={r['seed'] for r in validation}==cohorts[1],
            validation_role=all(r['fault']=='healthy' and r['calibration_sha256']==sha(base/'calibration.json') for r in validation),
        )
        checks={k:bool(v) for k,v in checks.items()}
        errors.extend(tag+'/'+k for k,v in checks.items() if not v)
        results.append(dict(map=tag,checks=checks,development_records=20,validation_records=32,
                            coefficient_max_abs_error=float(np.max(np.abs(weights-cal['direction_weights']))),
                            test_episode_files_read=0))
    report=dict(passed=not errors,errors=errors,maps=results,input_sha256=inputs,
                source_sha256=sha(Path(__file__)),
                scope='Development-only augmented least-squares reconstruction independent of normal-equation fitting; validation cutoff provenance uses the frozen feature helper. No test outcomes read, no refitting of deployed parameters, no external timestamp or execution-authentication claim.')
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='input_sha256'},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
