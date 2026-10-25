"""Prepare a frozen raw-record fixture catalogue, then score four unchanged arms.

New software fixtures are never neural experimental records. No SNN runs,
threshold fitting or population inference is performed.
"""
from pathlib import Path
import argparse
import copy
import ctypes
import gc
import gzip
import hashlib
import itertools
import json
import math
import platform
import re
import statistics
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.dont_write_bytecode=True
import numpy as np
from evidence_v10.contract import Campaign,audit,_validate_record_shape
from evidence_v10.fly_adapter import FlyAdapter
from evidence_v10.tank import TankAdapter

BASE='22999d28d8fe22f863fc8f62eaa45a57256083d0'
FROZEN=['evidence_v10/contract.py','evidence_v10/fly_adapter.py','evidence_v10/tank.py',
        'tools/replay_audit_v9.py','sim_vision/task_v9.py','sim_vision/closedloop_protocol.py']
CONFIGS={
 'RF-0':('runs/task-v9-test','runs/task-v9-frozen/calibration.json','runs/task-v9-frozen/registration-core.json'),
 'RF-A':('runs/task-v10-transfer/map-A/test','runs/task-v10-transfer/map-A/calibration.json','runs/task-v10-transfer/map-A/registration.json'),
 'RF-B':('runs/task-v10-transfer/map-B/test','runs/task-v10-transfer/map-B/calibration.json','runs/task-v10-transfer/map-B/registration.json')}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encoded(obj):return json.dumps(obj,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
def digest(obj):return hashlib.sha256(encoded(obj)).hexdigest()
def write_new(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def load_inputs():
    start=time.perf_counter();base=read(ROOT/'PUBLIC_SCOPE.json')
    for n in FROZEN:
        expected=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
        assert hashlib.sha256(expected).hexdigest()==sha(ROOT/n),n
    adapters={name:FlyAdapter(ROOT/paths[0],ROOT/paths[1],ROOT/paths[2]) for name,paths in CONFIGS.items()}
    adapters['tank']=TankAdapter();groups={'fly':[],'tank':[]};sources={};registry={}
    for tag,adapter in adapters.items():
        folder=ROOT/CONFIGS[tag][0]/'episodes' if tag!='tank' else ROOT/'audit/v10/evidence-05/tank-raw'
        native=[]
        for p in sorted(folder.glob('*.json')):
            name=p.relative_to(ROOT).as_posix();assert sha(p)==base['files'][name]['sha256'],name
            r=read(p);native.append(r);sources[name]=sha(p)
            e=adapter.normalize(r);_validate_record_shape(e)
            if tag=='tank':fields=['adapter','config','source_sha256','uniform_sha256','mask_sha256','deleted']
            else:fields=['protocol','input_map_sha256','calibration_sha256','run_manifest_sha256','uniform_sha256','mask_sha256','deleted_rows','n_connection_rows','command_flyids']
            registry[(tag,e.key)]={k:r[k] for k in fields}
        for seed in sorted({r['seed'] for r in native}):
            s=adapter.spec
            group=dict(adapter_key=tag,clusters=(seed,),conditions=s.conditions,laws=s.laws,faults=s.faults,
                horizon_s=s.horizon_s,frame_s=s.frame_s,records=[r for r in native if r['seed']==seed])
            groups['tank' if tag=='tank' else 'fly'].append(group)
    return adapters,groups,sources,registry,time.perf_counter()-start


def normalize(rows,adapter):
    records=[];issues=[]
    for i,row in enumerate(rows):
        try:
            e=adapter.normalize(row);_validate_record_shape(e);records.append(e)
        except (ValueError,AssertionError,KeyError,TypeError,IndexError) as error:
            issues.append('native-schema:'+str(i)+':'+str(error)[:300])
    return records,issues


def baseline(records,spec,tag,registry):
    issues=[];keys=[r.key for r in records]
    expected=set(itertools.product(spec.clusters,spec.conditions,spec.laws,spec.faults))
    if set(keys)!=expected or len(keys)!=len(expected):issues.append('baseline-matrix')
    for r in records:
        trusted=registry.get((tag,r.key))
        if trusted is None:issues.append('baseline-identity');continue
        for k,v in trusted.items():
            if r.native.get(k)!=v:issues.append('baseline-header:'+k)
        for value in [r.uniform_sha256,r.mask_sha256]:
            if not re.fullmatch('[0-9a-f]{64}',value):issues.append('baseline-digest-format')
        if not math.isfinite(r.horizon_s) or not math.isfinite(r.frame_s) or min(r.horizon_s,r.frame_s)<=0:issues.append('baseline-clock-range')
        if r.failure_s is not None and (not math.isfinite(r.failure_s) or not 0<=r.failure_s<=r.horizon_s):issues.append('baseline-failure-range')
        if r.deleted<0:issues.append('baseline-negative-deletion')
        for q in r.frames:
            for k in ['start_s','end_s','decision_s','usable_after_s','resource']:
                value=q.get(k)
                if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):issues.append('baseline-field:'+k)
            if isinstance(q.get('resource'),(int,float)) and q['resource']<0:issues.append('baseline-resource-range')
        for k in ['burst_delay_ms','burst_duration_ms']:
            if k in r.native and (not isinstance(r.native[k],(int,float)) or not math.isfinite(r.native[k]) or r.native[k]<=0):issues.append('baseline-burst-range')
    return sorted(set(issues))


def native_only(records,spec,adapter):
    issues=[]
    for r in sorted(records,key=lambda e:repr(e.key)):
        try:adapter.check_native(r)
        except (ValueError,AssertionError,KeyError,TypeError,IndexError) as e:issues.append('adapter-replay:'+str(e)[:300])
    for seed in spec.clusters:
        group=[r for r in records if r.cluster==seed]
        try:adapter.check_pair(group)
        except (ValueError,AssertionError,KeyError,TypeError,IndexError) as e:issues.append('adapter-pair-replay:'+str(e)[:300])
    return issues


class Counters(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in
        ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage']]


def rss():
    if sys.platform!='win32':return None
    p=Counters();p.cb=ctypes.sizeof(p)
    fn=ctypes.windll.psapi.GetProcessMemoryInfo
    ok=fn(ctypes.c_void_p(-1),ctypes.byref(p),p.cb)
    return p.WorkingSetSize if ok else None


def score(case,arm,adapter,registry):
    if isinstance(adapter,FlyAdapter):adapter.streams.cache_clear()
    gc.collect();start_rss=rss();samples=[start_rss] if start_rss is not None else []
    stop=threading.Event()
    def sample():
        while not stop.wait(.005):
            value=rss()
            if value is not None:samples.append(value)
    thread=threading.Thread(target=sample,daemon=True);thread.start()
    t=time.perf_counter();cpu=time.process_time()
    records,parse=normalize(case['records'],adapter)
    s=case['spec'];spec=Campaign(tuple(s['clusters']),tuple(s['conditions']),tuple(s['laws']),tuple(s['faults']),s['horizon_s'],s['frame_s'],'network spikes' if case['plant']=='fly' else 'valid sensor updates')
    a=baseline(records,spec,case['adapter_key'],registry)
    extra=[]
    if arm=='B':extra=[i.code+':'+i.detail[:300] for i in audit(records,spec,None)]
    if arm=='C':extra=native_only(records,spec,adapter)
    if arm=='D':extra=[i.code+':'+i.detail[:300] for i in audit(records,spec,adapter)]
    seconds=time.perf_counter()-t;cpu_seconds=time.process_time()-cpu
    stop.set();thread.join();end=rss()
    if end is not None:samples.append(end)
    return dict(id=case['id'],plant=case['plant'],adapter_key=case['adapter_key'],family=case['family'],arm=arm,
                applicable=case['applicable'],input_sha256=digest({k:case[k] for k in ['adapter_key','spec','records']}),
                expected_invalid=case['expected_invalid'],detected=bool(parse or a or extra),parse_findings=parse,baseline_findings=a,layer_findings=extra,
                normalized_records=len(records),parse_exclusions=len(case['records'])-len(records),
                wall_seconds=seconds,process_cpu_seconds=cpu_seconds,start_rss_bytes=start_rss,
                sampled_peak_rss_bytes=max(samples) if samples else None,rss_sample_interval_seconds=.005)


def prepare(out):
    total_start=time.perf_counter()
    from tools.ablation.challenges import build_cases
    adapters,groups,sources,registry,seconds=load_inputs()
    cases=build_cases(groups['fly'],groups['tank'],seed=2026102501)
    assert len({c['id'] for c in cases})==len(cases)
    out.mkdir(parents=True,exist_ok=False)
    payload=encoded(cases)
    (out/'fixtures.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    index=[]
    for c in cases:
        index.append({**{k:v for k,v in c.items() if k!='records'},'fixture_sha256':digest(c),
            'input_sha256':digest({k:c[k] for k in ['adapter_key','spec','records']}),'records':len(c['records'])})
    source_files=[Path(__file__).resolve().relative_to(ROOT).as_posix(),'tools/ablation/challenges.py','experiments/checker-ablation-v10_1/PROTOCOL.md','experiments/checker-ablation-v10_1/challenge-spec.json']
    source_hashes={n:sha(ROOT/n) for n in source_files}
    # Exactly first three deterministic cases per plant, independent of outcomes.
    repeats=[c['id'] for plant in ['fly','tank'] for c in [q for q in cases if q['plant']==plant][:3]]
    result=dict(base_commit=BASE,prepared_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        design='fixed additional evaluation, not blind generalization',generation_seed=2026102501,
        case_count=len(cases),cases=index,input_sha256=sources,source_sha256=source_hashes,
        frozen_checker_sha256={n:sha(ROOT/n) for n in FROZEN},fixtures_sha256=sha(out/'fixtures.json.gz'),
        header_registry_sha256=digest(sorted([(str(k),v) for k,v in registry.items()])),
        initialization_registry_seconds=seconds,complete_preparation_seconds=time.perf_counter()-total_start,
        unique_applicable_inputs=len({r['input_sha256'] for r in index if r['applicable']}),
        technical_repeat_case_ids=repeats,technical_repeats=3)
    write_new(out/'frozen-plan.json',result)
    print(json.dumps(dict(prepared=True,cases=len(cases),invalid=sum(c['expected_invalid'] and c['applicable'] for c in cases),valid=sum(not c['expected_invalid'] and c['applicable'] for c in cases),inapplicable=sum(not c['applicable'] for c in cases),plan_sha256=sha(out/'frozen-plan.json')),indent=2))


def execute(plan_dir,out):
    plan=read(plan_dir/'frozen-plan.json')
    for name,h in {**plan['source_sha256'],**plan['frozen_checker_sha256'],**plan['input_sha256']}.items():assert sha(ROOT/name)==h,name
    assert sha(plan_dir/'fixtures.json.gz')==plan['fixtures_sha256']
    cases=json.loads(gzip.decompress((plan_dir/'fixtures.json.gz').read_bytes()))
    for case,index in zip(cases,plan['cases']):assert digest(case)==index['fixture_sha256']
    adapters,groups,sources,registry,setup=load_inputs()
    assert digest(sorted([(str(k),v) for k,v in registry.items()]))==plan['header_registry_sha256']
    out.mkdir(parents=True,exist_ok=False)
    meta=dict(plan_sha256=sha(plan_dir/'frozen-plan.json'),base_commit=BASE,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              setup_seconds=setup,python=platform.python_version(),numpy=np.__version__,platform=platform.platform(),cpu=platform.processor(),
              rss_method='5-ms self-process working-set sampling; absolute RSS, not per-case allocation or independent worker peak')
    write_new(out/'run.json',meta);rows=[];start=time.perf_counter()
    with (out/'rows.jsonl').open('x',encoding='utf-8') as log:
        for j,case in enumerate(cases):
            for arm in 'ABCD'[j%4:]+'ABCD'[:j%4]:
                row=score(case,arm,adapters[case['adapter_key']],registry)
                row.update(repeat=0);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
            if (j+1)%10==0:print(json.dumps(dict(completed_cases=j+1,total=len(cases),elapsed_seconds=time.perf_counter()-start)),flush=True)
        for case in cases:
            if case['id'] not in plan['technical_repeat_case_ids']:continue
            for repeat in range(1,4):
                for arm in 'ABCD':
                    row=score(case,arm,adapters[case['adapter_key']],registry)
                    row.update(repeat=repeat);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    summary={}
    for plant in ['fly','tank','all']:
        summary[plant]={}
        for arm in 'ABCD':
            selected=[r for r in rows if r['arm']==arm and r['repeat']==0 and r['applicable'] and (plant=='all' or r['plant']==plant)]
            values=[r['wall_seconds'] for r in selected]
            summary[plant][arm]=dict(cases=len(selected),invalid=sum(r['expected_invalid'] for r in selected),valid=sum(not r['expected_invalid'] for r in selected),
                tp=sum(r['expected_invalid'] and r['detected'] for r in selected),fn=sum(r['expected_invalid'] and not r['detected'] for r in selected),
                fp=sum(not r['expected_invalid'] and r['detected'] for r in selected),tn=sum(not r['expected_invalid'] and not r['detected'] for r in selected),
                total_seconds=sum(values),median_seconds=statistics.median(values),max_sampled_rss_bytes=max((r['sampled_peak_rss_bytes'] or 0) for r in selected))
    # Full must agree with the measured union; no desired detection count is asserted.
    table={(r['id'],r['arm']):r for r in rows if r['repeat']==0}
    assert all(table[(c['id'],'D')]['detected']==(table[(c['id'],'B')]['detected'] or table[(c['id'],'C')]['detected']) for c in cases)
    result=dict(completed=True,summary=summary,elapsed_seconds=time.perf_counter()-start,
        inapplicable=[dict(id=c['id'],reason=c['applicability_reason']) for c in cases if not c['applicable']],
        plan_sha256=meta['plan_sha256'],new_neural_simulations=0,checker_source_unchanged=True,
        scope='Designed fixed cases and technical source repetitions; not population error rates or blind coverage')
    write_new(out/'results.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare');p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('run');p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.mode=='prepare':prepare(a.out)
    else:execute(a.plan,a.out)
