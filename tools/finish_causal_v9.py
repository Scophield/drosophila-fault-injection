"""Wait for core/stress verification, then run the separate fixed causal check."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];AUDIT=ROOT/'audit/acceptance-v9'


def stage(label,args):
    print(label,datetime.now(timezone.utc).isoformat(),flush=True)
    with (AUDIT/(label+'.log')).open('x') as f:
        result=subprocess.run([sys.executable,'-u','tools/run_v9.py',*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{label} failed: inspect its log')


def main():
    with (AUDIT/'causal-workflow-start.json').open('x') as f:
        json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid()),f)
    while not (AUDIT/'measurements-complete.json').exists():
        print('Waiting for core/stress verification; no causal neural work started',flush=True);time.sleep(45)
    if (datetime(2026,10,23,4,59,tzinfo=timezone.utc)-datetime.now(timezone.utc)).total_seconds()<3*3600:
        (AUDIT/'causal-deferred.json').write_text(json.dumps(dict(reason='deadline protection, not outcome selection')))
        return
    registration='runs/task-v9-frozen/registration-causal.json'
    stage('causal-launcher',['tools/launch_causal_v9.py','--registration',registration,'--out','runs/task-v9-causal'])
    stage('causal-analysis',['tools/analyze_causal_v9.py','--root','runs/task-v9-causal','--registration',registration,'--out','audit/acceptance-v9/causal'])
    stage('causal-replay',['tools/replay_causal_v9.py','--root','runs/task-v9-causal','--calibration','runs/task-v9-frozen/calibration.json','--out','audit/acceptance-v9/replay-causal'])
    (AUDIT/'causal-complete.json').write_text(json.dumps(dict(complete=True,records=64,separate_clusters=8,utc=datetime.now(timezone.utc).isoformat()),indent=2))
    print('Separate causal check complete and replay verified',flush=True)


if __name__=='__main__':main()
