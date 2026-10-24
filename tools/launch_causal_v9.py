"""Execute only the registered secondary action-ablation matrix."""
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
    ap.add_argument('--registration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();reg=json.loads(a.registration.read_text());out=a.out.resolve()
    if reg['expected_test_episodes']!=64 or reg['faults']!=['healthy']:raise ValueError('wrong diagnostic registration')
    out.mkdir(parents=True,exist_ok=False);start=time.time();workers=[]
    (out/'launch.json').write_text(json.dumps(dict(registration_sha256=hashlib.sha256(a.registration.read_bytes()).hexdigest(),seeds=reg['test_seeds'],modes=reg['modes']),indent=2))
    for i in range(3):
        seeds=reg['test_seeds'][i::3]
        command=[sys.executable,'-u','tools/run_v9.py','tools/run_task_v9.py','--out',str(out),
            '--seeds',','.join(map(str,seeds)),'--phis='+','.join(map(str,reg['phis'])),
            '--modes',','.join(reg['modes']),'--faults','healthy','--calibration',
            str((ROOT/'runs/task-v9-frozen/calibration.json').resolve()),'--role','test',
            '--registration',str(a.registration.resolve())]
        log=(out/f'worker-{i}.log').open('x')
        child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        workers.append((child,log,command))
    (out/'active.json').write_text(json.dumps(dict(started_unix=start,pids=[p.pid for p,_,_ in workers],commands=[c for _,_,c in workers]),indent=2))
    while any(p.poll() is None for p,_,_ in workers):time.sleep(2)
    for _,log,_ in workers:log.close()
    report=dict(started_unix=start,completed_unix=time.time(),elapsed_seconds=time.time()-start,
        exit_codes=[p.returncode for p,_,_ in workers],episodes=len(list((out/'episodes').glob('*.json'))))
    (out/f'execution-{int(start)}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    if any(report['exit_codes']) or report['episodes']!=64:raise SystemExit(1)


if __name__=='__main__':main()
