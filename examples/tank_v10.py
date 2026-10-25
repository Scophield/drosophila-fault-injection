"""Standalone adoption of the evidence interface; no fly data or Brian2 imports.

The fixed tank scenario is a record-integrity example, not a neural benchmark.
Use a new output directory. Custom seeds define a separate example campaign.
"""
import argparse
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_v10.contract import Campaign,audit
from evidence_v10.tank import TankAdapter,run


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seeds',default='9000,9001,9002,9003,9004,9005,9006,9007')
    a=ap.parse_args();seeds=tuple(int(v) for v in a.seeds.split(','))
    if not seeds or len(set(seeds))!=len(seeds) or min(seeds)<0:raise ValueError('unique nonnegative seeds required')
    a.out.mkdir(parents=True,exist_ok=False);raw=a.out/'episodes';raw.mkdir();start=time.perf_counter()
    adapter=TankAdapter();s=adapter.spec
    spec=Campaign(seeds,s.conditions,s.laws,s.faults,s.horizon_s,s.frame_s,s.resource_unit)
    rows=[];hashes={}
    for seed,c,m,f in itertools.product(spec.clusters,spec.conditions,spec.laws,spec.faults):
        r=run(seed,c,m,f);p=raw/f'{seed}_{c}_{m}_{f}.json';p.write_text(json.dumps(r)+'\n')
        hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest();rows.append(adapter.normalize(r))
    issues=audit(rows,spec,adapter)
    loaded={m for m in sys.modules if m.startswith(('brian2','evidence_v10.fly_adapter','task_v9'))}
    if loaded:raise RuntimeError('standalone example imported fly/simulator modules: '+repr(loaded))
    report=dict(passed=not issues,records=len(rows),seed_clusters=len(seeds),campaign=asdict(spec),
        issues=[asdict(i) for i in issues],successes=sum(r.success for r in rows),
        raw_sha256=hashes,source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__).resolve(),ROOT/'evidence_v10/contract.py',ROOT/'evidence_v10/tank.py']},
        fly_or_simulator_imports=sorted(loaded),seconds=time.perf_counter()-start,
        scope='Small independent plant adoption/integrity example; sensor deletions; no neural performance comparison, physical safety certificate or pooling with fly outcomes.')
    (a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['raw_sha256','source_sha256']},indent=2))
    if issues:raise SystemExit(1)


if __name__=='__main__':main()
