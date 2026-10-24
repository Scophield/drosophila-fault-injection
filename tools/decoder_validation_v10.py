"""Descriptive held-out decoder error in the declared pre-contact control window.

No fitting or threshold selection. Cluster intervals resample entire validation
seeds, retaining both laws and bearings; they are not frame-level confidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['root','calibration','out']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();cal=json.loads(a.calibration.read_text())
    paths=sorted((a.root/'episodes').glob('*.json'));rs=[json.loads(p.read_text()) for p in paths]
    seeds=sorted({r['seed'] for r in rs});assert len(seeds)==8 and len(rs)==32
    expected={(s,p,m) for s in seeds for p in [-30.,30.] for m in ['proportional','relay']}
    assert {(r['seed'],r['phi_deg'],r['mode']) for r in rs}==expected
    errors=[];rows=[];byseed={s:[] for s in seeds}
    weights=np.array(cal['direction_weights']);bias=cal['direction_intercept']
    for r in rs:
        assert r['fault']=='healthy' and (r['collision_ms'] is None or r['collision_ms']>400)
        assert r['calibration_sha256']==hashlib.sha256(a.calibration.read_bytes()).hexdigest()
        for q in r['log']:
            if not 200<=q['t_end_ms']<=400:continue
            target=q['phi_now'];prediction=float(np.array(q['smooth_rates'])@weights+bias)*60
            error=prediction-target;byseed[r['seed']].append(error);errors.append(error)
            rows.append(dict(seed=r['seed'],phi_deg=r['phi_deg'],mode=r['mode'],
                frame_end_ms=q['t_end_ms'],target_bearing_deg=target,predicted_bearing_deg=prediction,error_deg=error))
    assert len(rows)==352
    rng=np.random.default_rng(20261023);ids=rng.integers(0,8,(20000,8))
    mse=np.array([np.mean(np.square(byseed[s])) for s in seeds]);mae=np.array([np.mean(np.abs(byseed[s])) for s in seeds])
    boot_rmse=np.sqrt(mse[ids].mean(axis=1));boot_mae=mae[ids].mean(axis=1)
    report=dict(role='held-out healthy validation, descriptive diagnostic; no fitting or test tuning',
        episodes=32,seed_clusters=8,frames=352,window_frame_end_ms=[200,400],
        target='body-frame bearing used to encode each input frame, in degrees',
        feature='five-frame smoothed rates, un-clipped affine decoder output times 60',
        rmse_deg=float(np.sqrt(np.mean(np.square(errors)))),mae_deg=float(np.mean(np.abs(errors))),
        rmse_ci95_deg=np.quantile(boot_rmse,[.025,.975]).tolist(),mae_ci95_deg=np.quantile(boot_mae,[.025,.975]).tolist(),
        bootstrap=dict(unit='entire validation seed, both laws and bearings retained',draws=20000,seed=20261023),
        per_seed=[dict(seed=s,rmse_deg=float(np.sqrt(mse[i])),mae_deg=float(mae[i])) for i,s in enumerate(seeds)],
        per_law_bearing=[dict(mode=m,phi_deg=p,frames=len(sub),
            rmse_deg=float(np.sqrt(np.mean(np.square([q['error_deg'] for q in sub])))),
            mae_deg=float(np.mean(np.abs([q['error_deg'] for q in sub]))))
            for m in ['proportional','relay'] for p in [-30.,30.]
            for sub in [[q for q in rows if q['mode']==m and q['phi_deg']==p]]],
        calibration_sha256=hashlib.sha256(a.calibration.read_bytes()).hexdigest(),
        raw_sha256={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out/'frames.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['raw_sha256','per_seed']},indent=2))


if __name__=='__main__':main()
