"""Actually exercise a curated export without reading omitted external tables.

Uses an explicit already-installed isolated interpreter; installs nothing.
Saved-data analyses/replays and tiny tank tests, never full neural simulation.
"""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--checkout',type=Path,required=True)
    ap.add_argument('--python',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    checkout=a.checkout.resolve();python=a.python.resolve();start=time.perf_counter()
    if (checkout/'sim/data/annotations.tsv').exists():raise ValueError('annotation dump accidentally distributed')
    if list(checkout.rglob('*.parquet')) or list(checkout.rglob('*.blend')):raise ValueError('external/private resource accidentally distributed')
    (checkout/'tmp').mkdir(exist_ok=True)
    commands=[]
    sets=[('core','runs/task-v9-test','runs/task-v9-frozen/registration-core.json','runs/task-v9-frozen/calibration.json','tools/analyze_task_v9_exportfix.py'),
          ('map-A','runs/task-v10-transfer/map-A/test','runs/task-v10-transfer/map-A/registration.json','runs/task-v10-transfer/map-A/calibration.json','tools/analyze_task_v10.py'),
          ('map-B','runs/task-v10-transfer/map-B/test','runs/task-v10-transfer/map-B/registration.json','runs/task-v10-transfer/map-B/calibration.json','tools/analyze_task_v10.py')]
    for tag,root,reg,cal,script in sets:
        commands.append((tag+'-score',['tools/run_v9.py',script,'--root',root,'--registration',reg,'--out','output/check-'+tag]))
        commands.append((tag+'-replay',['tools/run_v9.py','tools/replay_audit_v9.py','--root',root,'--calibration',cal,'--out','output/replay-'+tag]))
    commands += [('tank',['examples/tank_v10.py','--out','output/check-tank']),
                 ('contract-tests',['-m','unittest','discover','-s','tests','-p','test_evidence_v10.py','-v'])]
    def execute(job):
        name,args=job;cmd=[str(python),'-X','utf8',*args];ts=time.perf_counter()
        with (a.out/(name+'.log')).open('x',encoding='utf-8') as f:
            result=subprocess.run(cmd,cwd=checkout,stdout=f,stderr=subprocess.STDOUT)
        return dict(name=name,command=cmd,exit_code=result.returncode,seconds=time.perf_counter()-ts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs=list(pool.map(execute,commands))
    errors=[q['name'] for q in jobs if q['exit_code']]
    comparisons=[]
    for tag,root,reg,cal,script in sets:
        produced=checkout/('output/check-'+tag+'/summary.json')
        reference=ROOT/('audit/acceptance-v9/core-v2/summary.json' if tag=='core' else 'audit/v10/transfer-01/'+tag+'/analysis/summary.json')
        if not produced.is_file():continue
        x=json.loads(produced.read_text());y=json.loads(reference.read_text())
        # Analysis wall time is not a scientific estimand. All other fields,
        # including source hashes, matrix checks, thresholds and CIs, must match.
        x.pop('analysis_seconds',None);y.pop('analysis_seconds',None)
        matched=x==y
        if not matched:errors.append('summary mismatch:'+tag)
        replay=json.loads((checkout/('output/replay-'+tag+'/replay.json')).read_text())
        if not replay['passed'] or replay['records']!=(288 if tag=='core' else 144):errors.append('replay:'+tag)
        comparisons.append(dict(cohort=tag,all_summary_fields_except_analysis_time_equal=matched,records=replay['records'],replay_passed=replay['passed']))
    manifest=json.loads((checkout/'PUBLIC_SCOPE.json').read_text())
    for name,q in manifest['files'].items():
        if sha(checkout/name)!=q['sha256']:errors.append('curation bytes changed:'+name)
    result=dict(passed=not errors,errors=errors,checkout=str(checkout),jobs=jobs,
        comparisons=comparisons,neural_records=576,tank_example_records=96,
        omitted_annotations_absent=True,omitted_connectivity_absent=True,
        external_matrices_used=False,neural_dynamics_resimulated=False,
        environment='Already-installed isolated NumPy/setuptools environment; no dependency installation in this check, SAME host.',
        source_sha256=sha(__file__),seconds=time.perf_counter()-start)
    (a.out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
