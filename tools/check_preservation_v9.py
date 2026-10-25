"""Verify all inherited experiment files and named v8 PDFs against safe backup."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();baseline=json.loads(a.baseline.read_text());checked={};errors=[]
    for r in baseline['files']:
        name=r['path'].replace('\\','/')
        if not (name.startswith(('runs/','sim/results/','sim_vision/results_vision/','audit/')) or
            name in ['paper/fly_connectome_fault_assessment_v8.pdf','paper/fly_connectome_supplement_v8.pdf']):continue
        p=ROOT/name
        if not p.is_file():errors.append(dict(file=name,error='missing'));continue
        h=hashlib.sha256(p.read_bytes()).hexdigest();checked[name]=h
        if h!=r['sha256']:errors.append(dict(file=name,error='changed',before=r['sha256'],after=h))
    if len(checked)<100:raise ValueError('unexpectedly small baseline coverage')
    report=dict(passed=not errors,checked=len(checked),errors=errors,files_sha256=checked,
        baseline_manifest_sha256=hashlib.sha256(a.baseline.read_bytes()).hexdigest(),
        scope='Every baseline runs/, archive results/, audit/ file and both named v8 PDFs; new v9 files are separate.',
        utc=datetime.now(timezone.utc).isoformat())
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files_sha256'},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
