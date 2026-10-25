"""Run a fixed matrix in bounded workers, recording actual elapsed time."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seeds',required=True)
    ap.add_argument('--calibration',type=Path,required=True)
    ap.add_argument('--role',choices=['validation','test'],required=True)
    ap.add_argument('--registration',type=Path)
    ap.add_argument('--faults',default='healthy,F2_25,F2_50')
    ap.add_argument('--phis',default='-30,30')
    ap.add_argument('--workers',type=int,default=3)
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args()
    out=args.out.resolve()
    seeds=[int(s) for s in args.seeds.split(',')]
    if args.workers<1 or args.workers>3: raise ValueError('use 1--3 workers')
    config=dict(seeds=seeds,calibration_sha256=hashlib.sha256(args.calibration.read_bytes()).hexdigest(),
        role=args.role,faults=args.faults,phis=args.phis,workers=args.workers,
        registration_sha256=hashlib.sha256(args.registration.read_bytes()).hexdigest() if args.registration else None)
    out.mkdir(parents=True,exist_ok=True)
    marker=out/'launch.json'
    if args.resume:
        if json.loads(marker.read_text())!=config: raise ValueError('changed launch configuration')
    else:
        with marker.open('x') as f: json.dump(config,f,indent=2)
    started=time.time(); workers=[]
    for i in range(args.workers):
        group=seeds[i::args.workers]
        if not group: continue
        command=[sys.executable,'-u','tools/run_v9.py','tools/run_task_v9.py','--out',str(out),
            '--seeds',','.join(map(str,group)),'--phis='+args.phis,'--modes','proportional,relay',
            '--faults',args.faults,'--calibration',str(args.calibration.resolve()),'--role',args.role]
        if args.registration: command+=['--registration',str(args.registration.resolve())]
        if args.resume: command+=['--resume']
        log=(out/f'worker-{i}.log').open('a' if args.resume else 'x')
        p=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        workers.append((p,log,command))
    (out/'active.json').write_text(json.dumps(dict(started_unix=started,
        pids=[p.pid for p,_,_ in workers],commands=[c for _,_,c in workers]),indent=2))
    while any(p.poll() is None for p,_,_ in workers): time.sleep(2)
    for _,log,_ in workers: log.close()
    result=dict(started_unix=started,completed_unix=time.time(),elapsed_seconds=time.time()-started,
        exit_codes=[p.returncode for p,_,_ in workers],episodes=len(list((out/'episodes').glob('*.json'))))
    with (out/f'execution-{int(started)}.json').open('x') as f: json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)
    if any(result['exit_codes']): raise SystemExit(1)


if __name__=='__main__': main()
