"""Independent raw-outcome arithmetic and saved-metric denominator check."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--analysis',type=Path,required=True)
    ap.add_argument('--registration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();d=json.loads((a.analysis/'summary.json').read_text());reg=json.loads(a.registration.read_text())
    paths=sorted((a.root/'episodes').glob('*.json'));rs=[json.loads(p.read_text()) for p in paths]
    if len(rs)!=reg['expected_test_episodes'] or not d['complete']:raise ValueError('incomplete records')
    key=lambda r:(r['seed'],r['phi_deg'],r['mode'],r['fault'])
    lookup={key(r):r for r in rs};seeds=reg['test_seeds'];errors=[]
    for row in d['counts']:
        m,f,phi=row['mode'],row['fault'],row['phi_deg']
        H=[lookup[(s,phi,m,'healthy')]['escaped'] for s in seeds]
        F=[lookup[(s,phi,m,f)]['escaped'] for s in seeds]
        expected=dict(n=len(F),success=sum(F),losses=sum(h and not v for h,v in zip(H,F)),
            gains=sum(not h and v for h,v in zip(H,F)),healthy_at_risk=sum(H))
        if any(row[k]!=v for k,v in expected.items()):errors.append(f'outcome cell {m}/{f}/{phi}')
    vectors={}
    for m in reg['modes']:
        for f in ['F2_25','F2_50']:
            vectors[f'{m}_{f}_net_loss']=[statistics.mean(
                int(lookup[(s,p,m,'healthy')]['escaped'])-int(lookup[(s,p,m,f)]['escaped']) for p in reg['phis']) for s in seeds]
    for f in ['F2_25','F2_50']:
        vectors[f'{f}_interaction']=[r-p for r,p in zip(vectors[f'relay_{f}_net_loss'],vectors[f'proportional_{f}_net_loss'])]
        # Polynomial convolution, independently of the analysis Counter DP.
        dist=np.array([1.]);origin=0
        for value in vectors[f'{f}_interaction']:
            w=abs(int(round(2*value)));new=np.zeros(len(dist)+2*w)
            new[:len(dist)]+=dist/2;new[2*w:]+=dist/2
            dist=new;origin+=w
        observed=abs(int(round(2*sum(vectors[f'{f}_interaction']))))
        p=float(sum(prob for i,prob in enumerate(dist) if abs(i-origin)>=observed))
        if not np.isclose(p,d['interaction_raw_p'][f],atol=1e-12):errors.append(f'sign-flip p {f}')
    rng=np.random.default_rng(reg['bootstrap']['seed'])
    draws=rng.integers(len(seeds),size=(reg['bootstrap']['draws'],len(seeds)))
    for name,v in vectors.items():
        samples=np.mean(np.asarray(v)[draws],axis=1)
        expected=[statistics.mean(v),float(np.quantile(samples,.025)),float(np.quantile(samples,.975))]
        observed=[d['cluster_effects'][name][k] for k in ['estimate','low','high']]
        if not np.allclose(expected,observed,atol=1e-12,rtol=0):errors.append(f'cluster effect/interval {name}')
    with (a.analysis/'metrics.csv').open(newline='') as f:metrics=list(csv.DictReader(f))
    metrics={(int(r['seed']),float(r['phi_deg']),r['mode'],r['fault']):r for r in metrics}
    names=['transmission','stop_count_upper','equal_duration_upper','equal_duration_two_sided','schedule_only','deadline']
    for name in names:
        for subset in ['all','faulty','healthy']:
            group=[r for r in rs if subset=='all' or (r['fault']=='healthy')==(subset=='healthy')]
            c=dict(tp=0,fp=0,tn=0,fn=0)
            for r in group:
                predicted=metrics[key(r)][name].lower()=='true';positive=not r['escaped']
                c[('t' if predicted==positive else 'f')+('p' if predicted else 'n')]+=1
            saved=d['warning_scores'][name][subset]
            if any(c[k]!=saved[k] for k in c):errors.append(f'confusion denominator {name}/{subset}')
    # A true prefix check: zero input before the cue must not contain inherited
    # spikes from an earlier restored episode in this non-spontaneous model.
    if any(q['n_total']!=0 for r in rs for q in r['log'] if q['t_end_ms']<=100):
        errors.append('nonzero pre-cue activity / state carryover')
    if len(metrics)!=len(rs):errors.append('metric CSV coverage')
    report=dict(passed=not errors,errors=errors,records=len(rs),clusters=len(seeds),
        verified='raw outcome cells, losses/gains/risk sets, cluster means/intervals, polynomial exact sign-flip tails, saved-metric confusion counts, pre-cue state reset',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        summary_sha256=hashlib.sha256((a.analysis/'summary.json').read_bytes()).hexdigest())
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
