"""Descriptive paired warning differences and sparse-bootstrap diagnostics.

Added after campaign registration: these are secondary descriptive analyses,
not new confirmatory tests, threshold calibration, or a reason to add samples.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();summary=json.loads((a.analysis/'summary.json').read_text())
    if not summary['complete']:raise ValueError('complete analysis required')
    with (a.analysis/'metrics.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    seeds=sorted({int(r['seed']) for r in rows});rng=np.random.default_rng(20261022)
    ix=rng.integers(len(seeds),size=(20000,len(seeds)))
    names=['transmission','equal_duration_upper','equal_duration_two_sided','schedule_only','deadline']
    diagnostics={};comparisons={}
    def boolean(v):
        if v.lower() not in ['true','false']:raise ValueError('boolean field')
        return v.lower()=='true'
    def interval(values):return [float(np.quantile(values,.025)),float(np.quantile(values,.975))] if len(values) else None
    for subset in ['all','faulty','healthy']:
        group=[r for r in rows if subset=='all' or (r['fault']=='healthy')==(subset=='healthy')]
        counts={}
        for name in names:
            cc=[]
            for seed in seeds:
                rs=[r for r in group if int(r['seed'])==seed];x=np.zeros(4,dtype=int)
                for r in rs:
                    positive=boolean(r['collision']);pred=boolean(r[name])
                    x[(0 if pred else 3) if positive else (1 if pred else 2)]+=1
                cc.append(x)
            cc=np.array(cc);counts[name]=cc
            boot=cc[ix].sum(axis=1)
            diagnostics[f'{subset}/{name}']=dict(
                positive_seed_clusters=int(np.sum((cc[:,0]+cc[:,3])>0)),
                negative_seed_clusters=int(np.sum((cc[:,1]+cc[:,2])>0)),
                sensitivity_valid_resamples=int(np.sum((boot[:,0]+boot[:,3])>0)),
                specificity_valid_resamples=int(np.sum((boot[:,1]+boot[:,2])>0)),total_resamples=20000)
        for candidate,baseline in [('deadline','schedule_only'),('equal_duration_two_sided','transmission'),
                                   ('equal_duration_two_sided','equal_duration_upper')]:
            c,b=counts[candidate],counts[baseline];cb=c[ix].sum(axis=1);bb=b[ix].sum(axis=1)
            result={}
            for metric,index,other in [('sensitivity',0,3),('specificity',2,1)]:
                den=cb[:,index]+cb[:,other];good=den>0;total=int(c[:,index].sum()+c[:,other].sum())
                samples=(cb[good,index]-bb[good,index])/den[good]
                result[metric]=dict(difference=float((c[:,index].sum()-b[:,index].sum())/total) if total else None,
                    cluster_interval=interval(samples),valid_resamples=int(good.sum()))
            samples=((cb[:,1]+cb[:,3])-(bb[:,1]+bb[:,3]))/cb.sum(axis=1)
            result['error_rate']=dict(difference=float(((c[:,1]+c[:,3])-(b[:,1]+b[:,3])).sum()/c.sum()),
                cluster_interval=interval(samples))
            disagreement=[r for r in group if boolean(r[candidate])!=boolean(r[baseline])]
            result['disagreement_records']=len(disagreement)
            comparisons[f'{subset}/{candidate}-minus-{baseline}']=result
    report=dict(complete=True,role='secondary descriptive analysis added after registration; no tuning or new confirmatory hypothesis',
        records=len(rows),seed_clusters=len(seeds),bootstrap_seed=20261022,bootstrap_draws=20000,
        diagnostics=diagnostics,comparisons=comparisons,
        metrics_sha256=hashlib.sha256((a.analysis/'metrics.csv').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'comparisons.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='diagnostics'},indent=2))


if __name__=='__main__':main()
