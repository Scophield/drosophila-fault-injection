"""Count-domain warning re-scoring of frozen observations; no neural simulation.

Thresholds use ONLY the original healthy validation cohorts. Original records,
registrations, calibrations and historical score products are read-only.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'sim_vision')]
from task_metrics_v9 import (bind_count_cutoff,bootstrap_indices,command_count,
    confusion,features,flags)

CONFIG={
    'RF-0':('runs/task-v9-frozen/registration-core.json','audit/acceptance-v9/core-v2/summary.json',20261022),
    'RF-A':('runs/task-v10-transfer/map-A/registration.json','audit/v10/transfer-01/map-A/analysis/summary.json',20261023),
    'RF-B':('runs/task-v10-transfer/map-B/registration.json','audit/v10/transfer-01/map-B/analysis/summary.json',20261023),
}
METHODS=['transmission','equal_duration_upper','equal_duration_two_sided','deadline','schedule_only']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_csv(path,rows):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def scored(records,values,seeds,indices):
    result=confusion(records,values)
    cells=['tp','fp','tn','fn']
    matrix=[]
    for seed in seeds:
        jj=[i for i,r in enumerate(records) if r['seed']==seed]
        c=confusion([records[i] for i in jj],[values[i] for i in jj])
        matrix.append([c[k] for k in cells])
    sums=np.asarray(matrix,dtype=np.int64)[indices].sum(axis=1)
    for metric,a,b in [('sensitivity',0,3),('specificity',2,1),('false_positive_rate',1,2),('false_negative_rate',3,0)]:
        denominator=sums[:,a]+sums[:,b];valid=denominator>0
        result[metric+'_interval']=[float(x) for x in np.quantile(sums[valid,a]/denominator[valid],[.025,.975],method='linear')] if valid.any() else None
        result[metric+'_undefined_draws']=int((~valid).sum())
    result['positive_seed_clusters']=sum(r[0]+r[3]>0 for r in matrix)
    result['negative_seed_clusters']=sum(r[1]+r[2]>0 for r in matrix)
    result['seed_confusion_counts']={str(s):dict(zip(cells,v)) for s,v in zip(seeds,matrix)}
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--draws',type=int,default=20000)
    a=ap.parse_args()
    if a.draws<1:raise ValueError('Positive bootstrap draws required')
    a.out.mkdir(parents=True,exist_ok=False)
    protected=read(ROOT/'PUBLIC_SCOPE.json')['files']
    # The original manifest remains an immutable input during this operation.
    before={p:sha(ROOT/p) for p in protected}
    inputs={};maps={};allrows=[];validrows=[];boundary=[];flat=[]
    def checked(name,expected=None):
        p=ROOT/name;h=sha(p)
        if expected is not None and h!=expected:raise ValueError('Changed frozen input: '+name)
        inputs[name]=h
        return read(p)
    for tag,(regname,summaryname,rng) in CONFIG.items():
        reg=checked(regname);old=checked(summaryname)
        validation=[checked(n,h) for n,h in sorted(reg['validation_input_sha256'].items())]
        if len(validation)!=32 or any(r['fault']!='healthy' for r in validation):
            raise ValueError('Expected the complete frozen 32-record healthy validation cohort')
        thresholds=bind_count_cutoff(reg['thresholds'],validation)
        cutoff=thresholds['command_count_cutoff']
        for n,r in zip(sorted(reg['validation_input_sha256']),validation):
            validrows.append(dict(RF=tag,source=n,source_sha256=inputs[n],seed=r['seed'],law=r['mode'],
                bearing_deg=r['phi_deg'],command_count=command_count(r),cutoff_numerator=cutoff['numerator'],cutoff_denominator=cutoff['denominator']))
        source_names=sorted(old['raw_input_sha256'])
        records=[checked(n,old['raw_input_sha256'][n]) for n in source_names]
        seeds=reg['test_seeds'];expected={(s,p,m,f) for s in seeds for p in reg['phis'] for m in reg['modes'] for f in reg['faults']}
        key=lambda r:(r['seed'],r['phi_deg'],r['mode'],r['fault'])
        if len(records)!=len(expected) or {key(r) for r in records}!=expected:
            raise ValueError('Incomplete or duplicate test matrix')
        if any(r['collision_ms'] is not None and r['collision_ms']<=400 for r in records):
            raise ValueError('Warning prefix is not pre-contact')
        current=[];legacy=[];alternative=[]
        for source,r in zip(source_names,records):
            fs=features(r);decision=flags(r,thresholds)
            rows=[q for q in r['log'] if 100<q['t_end_ms']<=400]
            old_hz=sum(sum(q['cmd_rates'])*.02 for q in rows)/(8*.3)
            alt_hz=sum(sum(q['cmd_rates']) for q in rows)/(8*15)
            original=old_hz<reg['thresholds']['command_lower_hz']
            alt=alt_hz<reg['thresholds']['command_lower_hz']
            legacy.append(original);alternative.append(alt);current.append(decision)
            row=dict(RF=tag,source=source,source_sha256=inputs[source],seed=r['seed'],condition=r['fault'],
                law=r['mode'],bearing_deg=r['phi_deg'],collision=not r['escaped'],collision_ms=r['collision_ms'],
                command_count=fs['command_count'],command_hz=fs['command_hz'],
                cutoff_numerator=cutoff['numerator'],cutoff_denominator=cutoff['denominator'],
                legacy_hz=old_hz,legacy_hz_hex=old_hz.hex(),alternative_hz=alt_hz,alternative_hz_hex=alt_hz.hex(),
                frozen_hz=reg['thresholds']['command_lower_hz'],canonical_flag=decision['transmission'],legacy_flag=original,alternative_flag=alt)
            allrows.append(row)
            if original!=alt:boundary.append(row)
        indices=bootstrap_indices(len(seeds),a.draws,rng)
        scores={}
        for name in METHODS:
            scores[name]={}
            for subset in ['all','faulty','healthy']:
                ids=[i for i,r in enumerate(records) if subset=='all' or (r['fault']=='healthy')==(subset=='healthy')]
                scores[name][subset]=scored([records[i] for i in ids],[current[i][name] for i in ids],seeds,indices)
            q=scores[name]['all']
            flat.append(dict(RF=tag,criterion=name,seed_clusters=len(seeds),records=len(records),
                **{k:q[k] for k in ['tp','fp','tn','fn','sensitivity','specificity','false_negative_rate','false_positive_rate']},
                fnr_low=q['false_negative_rate_interval'][0],fnr_high=q['false_negative_rate_interval'][1],
                fpr_low=q['false_positive_rate_interval'][0],fpr_high=q['false_positive_rate_interval'][1],
                no_positive_draws=q['false_negative_rate_undefined_draws']))
        canon=[d['transmission'] for d in current]
        compare={name:scored(records,v,seeds,indices) for name,v in [('legacy',legacy),('alternative',alternative)]}
        old_command=old['warning_scores']['transmission']['all']
        if any(compare['legacy'][k]!=old_command[k] for k in ['tp','fp','tn','fn']):
            raise ValueError('Historical command score could not be reproduced')
        unchanged={}
        for name in METHODS:
            q=scores[name]['all'];p=old['warning_scores'][name]['all']
            keys=['tp','fp','tn','fn','sensitivity','specificity','false_negative_rate','false_positive_rate']
            keys += [m+'_interval' for m in ['sensitivity','specificity','false_negative_rate','false_positive_rate']]
            unchanged[name]=all(q[k]==p[k] for k in keys) if a.draws==20000 else None
        maps[tag]=dict(records=len(records),seed_clusters=len(seeds),validation_records=32,
            threshold=cutoff,frozen_threshold_hz=reg['thresholds']['command_lower_hz'],warning_scores=scores,
            historical_comparison=compare,canonical_vs_legacy_changed_labels=sum(x!=y for x,y in zip(canon,legacy)),
            alternative_vs_legacy_changed_labels=sum(x!=y for x,y in zip(alternative,legacy)),
            all_methods_point_and_interval_equal_to_saved=unchanged,bootstrap_seed=rng)
    if any(sha(ROOT/p)!=h for p,h in before.items()):raise ValueError('Input changed during re-scoring')
    outputs={'all-records.csv':allrows,'validation-counts.csv':validrows,'boundary-records.csv':boundary,'warning-summary.csv':flat}
    for name,rows in outputs.items():write_csv(a.out/name,rows)
    result=dict(complete=True,records=len(allrows),healthy_validation_records=len(validrows),maps=maps,
        boundary_records=len(boundary),raw_input_sha256={k:v for k,v in inputs.items() if '/episodes/' in k},
        input_sha256=inputs,analysis_source_sha256={p:sha(ROOT/p) for p in ['tools/rescore_warnings_v10_1.py','tools/task_metrics_v9.py','sim_vision/task_v9.py']},
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        runtime=dict(python=platform.python_version(),numpy=np.__version__),
        bootstrap=dict(draws=a.draws,unit='whole seed cluster; all bearings, laws and doses retained',quantile='linear/type-7',undefined_class_rates='omit only draws whose corresponding denominator is zero'),
        frozen_manifest_entries_unchanged=len(before),frozen_data_modified=False,neural_simulation=False,
        statistic='Lossless integer counts reconstructed from native 50-Hz rate lattice; no saved spike timestamps',
        semantics='Healthy-validation linear fifth percentile; exact rational count comparison <; equality does not flag',
        historical_status='Saved analyses/registrations remain unchanged; current count re-scoring is an implementation clarification, not new samples or a new confirmatory test')
    with (a.out/'results.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(complete=True,records=result['records'],boundary_records=len(boundary),maps={t:dict(cutoff=q['threshold'],command=q['warning_scores']['transmission']['all'],unchanged=q['all_methods_point_and_interval_equal_to_saved']) for t,q in maps.items()}),indent=2))


if __name__=='__main__':main()
