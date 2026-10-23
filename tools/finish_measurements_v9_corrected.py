"""In-turn fixed workflow: await core, verify, run registered stress, verify.

No parameters or samples are selected from outcomes. Progress is written every
45 seconds. No raw file, registration or frozen source is edited.
"""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'audit/acceptance-v9'


def progress(stage,**data):
    print(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),stage=stage,**data)),flush=True)


def frozen_check(reg):
    changed=[p for p,h in reg['frozen_source_sha256'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    if changed:raise ValueError(f'frozen sources changed: {changed}')


def wait_complete(folder,expected,label):
    while True:
        executions=sorted(folder.glob('execution-*.json'))
        if executions:
            r=json.loads(executions[-1].read_text())
            if any(r['exit_codes']):raise RuntimeError(f'{label} worker failed: {r}')
            if len(list((folder/'episodes').glob('*.json')))!=expected:raise RuntimeError('completed count differs')
            progress(label+' complete',records=expected,elapsed_seconds=r['elapsed_seconds'])
            return r
        progress(label+' running',records=len(list((folder/'episodes').glob('*.json'))),expected=expected)
        time.sleep(45)


def run_stage(label,command):
    progress(label+' started')
    with (AUDIT/(label+'.log')).open('x') as log:
        result=subprocess.run([sys.executable,'-u','tools/run_v9.py',*command],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    progress(label+' finished',exit_code=result.returncode)
    if result.returncode:raise RuntimeError(f'{label} failed; inspect audit log')


def verify(name,folder,registration):
    run_stage(name+'-analysis-v2',['tools/analyze_task_v9_exportfix.py','--root',folder,'--registration',registration,'--out',f'audit/acceptance-v9/{name}-v2'])
    run_stage(name+'-replay',['tools/replay_audit_v9.py','--root',folder,'--calibration','runs/task-v9-frozen/calibration.json','--out',f'audit/acceptance-v9/replay-{name}'])
    run_stage(name+'-numbers',['tools/check_task_numbers_v9.py','--root',folder,'--analysis',f'audit/acceptance-v9/{name}-v2',
        '--registration',registration,'--out',f'audit/acceptance-v9/numbers-{name}'])


def main():
    marker=AUDIT/'measurement-workflow-corrected-start.json'
    with marker.open('x') as f:json.dump(dict(started_utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid()),f)
    core_reg='runs/task-v9-frozen/registration-core.json';stress_reg='runs/task-v9-frozen/registration-stress.json'
    reg=json.loads((ROOT/core_reg).read_text());frozen_check(reg)
    core=wait_complete(ROOT/'runs/task-v9-test',288,'core')
    frozen_check(reg);verify('core','runs/task-v9-test',core_reg)
    deadline=datetime(2026,10,23,4,59,tzinfo=timezone.utc)
    if (deadline-datetime.now(timezone.utc)).total_seconds()<4*3600:
        (AUDIT/'stress-deferred.json').write_text(json.dumps(dict(reason='deadline protection, not outcome selection',core_complete=True),indent=2))
        progress('stress deferred to protect paper deadline');return
    if (ROOT/'runs/task-v9-stress').exists():raise FileExistsError('stress run already exists; do not duplicate')
    frozen_check(reg)
    command=[sys.executable,'-u','tools/run_v9.py','tools/launch_task_v9.py','--out','runs/task-v9-stress',
        '--seeds','1100,1101,1102,1103,1104,1105,1106,1107','--phis=-45,45','--calibration',
        'runs/task-v9-frozen/calibration.json','--role','test','--registration',stress_reg]
    log=(AUDIT/'stress-launcher.log').open('x')
    child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    progress('registered stress launched',pid=child.pid)
    stress=wait_complete(ROOT/'runs/task-v9-stress',96,'stress')
    if child.wait()!=0:raise RuntimeError('stress launcher failed')
    log.close();frozen_check(reg);verify('stress','runs/task-v9-stress',stress_reg)
    result=dict(completed_utc=datetime.now(timezone.utc).isoformat(),core=core,stress=stress,
        records=384,independent_core_clusters=24,independent_stress_clusters=8,
        note='core/stress remain separate; no outcome-based tuning or stopping')
    with (AUDIT/'measurements-complete.json').open('x') as f:json.dump(result,f,indent=2)
    progress('all registered measurements verified',records=384)


if __name__=='__main__':main()
