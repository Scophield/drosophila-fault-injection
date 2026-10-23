"""Fit bilateral direction mapping using development data only; preserve inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    paths=sorted((args.root/'episodes').glob('*.json'))
    rows=[json.loads(p.read_text()) for p in paths]
    expected={(s,float(p)) for s in range(200,204) for p in [-60,-30,0,30,60]}
    if {(r['seed'],r['phi_deg']) for r in rows}!=expected or len(rows)!=20:
        raise ValueError('require complete prespecified development matrix (20 episodes)')
    X=[];y=[];active=[]
    for r in rows:
        if r['mode']!='observe' or r['fault']!='healthy' or r['horizon_ms']!=400:
            raise ValueError('development inputs only')
        for q in r['log']:
            if 200<=q['t_end_ms']<=400:
                X.append(q['smooth_rates']); y.append(q['phi_now']/60)
        active.append(np.mean([q['cmd_hz'] for q in r['log'] if 200<=q['t_end_ms']<=300]))
    X=np.array(X);y=np.array(y)
    mean=X.mean(axis=0); scale=np.maximum(X.std(axis=0),1)
    A=np.column_stack([(X-mean)/scale,np.ones(len(X))])
    penalty=np.eye(9)*10;penalty[-1,-1]=0
    coef=np.linalg.solve(A.T@A+penalty,A.T@y)
    weights=coef[:-1]/scale; intercept=coef[-1]-np.dot(mean,weights)
    prediction=X@weights+intercept
    cal=dict(protocol='task-v9-causal-exact-events',development_seeds=list(range(200,204)),
        development_phis=[-60,-30,0,30,60],training_window_ms=[200,400],ridge_penalty=10,
        feature='five-frame means of eight ordered command-cell rates; bearing/60 target',
        command_flyids=rows[0]['command_flyids'],direction_weights=weights.tolist(),
        direction_intercept=float(intercept),turn_gain_deg_s=400.,
        trigger_hz=float(max(2.5,np.quantile(active,.1)/2)),
        trigger_rule='first post-cue five-frame mean crossing; threshold half development active 10th percentile, floor 2.5 Hz',
        input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        development_fit_rmse=float(np.sqrt(np.mean((prediction-y)**2))),
        development_direction_accuracy=float(np.mean(np.sign(prediction[y!=0])==np.sign(y[y!=0]))),
        note='development fit quality is not held-out accuracy; final evaluation requires new clusters')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as f: json.dump(cal,f,indent=2)
    print(json.dumps(cal,indent=2))


if __name__=='__main__': main()
