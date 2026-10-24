"""Use the fixed V9-B recipe on each new map's development records only."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['root','design','rf-map','out']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();design=json.loads(a.design.read_text());mapping=json.loads(a.rf_map.read_text())
    spec=next(q for q in design['maps'] if q['map_id']==mapping['map_id'])
    paths=sorted((a.root/'episodes').glob('*.json'));rows=[json.loads(p.read_text()) for p in paths]
    expected={(s,p) for s in spec['development_seeds'] for p in design['phyis_development']}
    assert len(rows)==20 and {(r['seed'],r['phi_deg']) for r in rows}==expected
    X=[];y=[];active=[]
    map_sha=hashlib.sha256(a.rf_map.read_bytes()).hexdigest();assert map_sha==spec['sha256']
    for r in rows:
        assert r['mode']=='observe' and r['fault']=='healthy' and r['horizon_ms']==400
        assert r['rf_map_sha256']==map_sha
        for q in r['log']:
            if 200<=q['t_end_ms']<=400:X.append(q['smooth_rates']);y.append(q['phi_now']/60)
        active.append(np.mean([q['cmd_hz'] for q in r['log'] if 200<=q['t_end_ms']<=300]))
    X=np.asarray(X);y=np.asarray(y);mean=X.mean(axis=0);scale=np.maximum(X.std(axis=0),1)
    A=np.column_stack([(X-mean)/scale,np.ones(len(X))]);penalty=np.eye(9)*10;penalty[-1,-1]=0
    coef=np.linalg.solve(A.T@A+penalty,A.T@y);weights=coef[:-1]/scale;intercept=coef[-1]-mean@weights
    pred=X@weights+intercept
    cal=dict(protocol='task-v9.1-causal-exact-events',experiment_version=design['experiment'],map_id=mapping['map_id'],rf_map_sha256=map_sha,
        development_seeds=spec['development_seeds'],development_phis=design['phyis_development'],training_window_ms=[200,400],ridge_penalty=10,
        feature='five-frame means of eight ordered command-cell rates; bearing/60 target',command_flyids=rows[0]['command_flyids'],
        direction_weights=weights.tolist(),direction_intercept=float(intercept),turn_gain_deg_s=600.,gate_silent=True,
        trigger_hz=float(max(2.5,np.quantile(active,.1)/2)),trigger_rule=design['calibration']['trigger'],
        input_sha256={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        development_fit_rmse=float(np.sqrt(np.mean((pred-y)**2))),
        development_direction_accuracy=float(np.mean(np.sign(pred[y!=0])==np.sign(y[y!=0]))),
        note='Development fit is not held-out decoder accuracy. No validation/fault/test outcome used; common V9-B recipe fixed before new runs.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(cal,f,indent=2)
    print(json.dumps(cal,indent=2))


if __name__=='__main__':main()
