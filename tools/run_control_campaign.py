"""Run the declared paired controller controls on six new seed clusters."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'runs/controller-v4a'
    out.mkdir(parents=True,exist_ok=False)
    vision=out/'vision'
    vision.mkdir()
    old=ROOT/'runs/geometry-v3/vision'
    shutil.copyfile(old/'calib-geometry-v3.json',vision/'calib-frozen.json')
    shutil.copytree(old/'episodes_calibration',vision/'episodes_calibration')
    config=dict(seeds=list(range(12,18)),phis=[-30,30],
                modes=['brain','precue_gated','bias_only','steer_disabled'],faults=[None],
                horizon_ms=1000,calibration='copied without refitting from geometry-v3',
                comparisons='paired seeds and bearings; all four laws retain the same neural burst trigger',
                interpretation='closed-loop interventions change subsequent retinal input; triggers follow the same law, not necessarily the same times')
    (out/'campaign.json').write_text(json.dumps(config,indent=2)+'\n')
    env=os.environ.copy()
    env.update(FLY_RUN_DIR=str(out),FLY_CODEGEN_TARGET='numpy')
    env['PATH']=r'C:\Program Files\Git\cmd'+os.pathsep+env.get('PATH','')
    search=[str(ROOT/'sim_vision'),str(ROOT/'sim')]+[str(Path(p).resolve()) for p in sys.path if p]
    code='import sys; sys.path[:0]='+repr(search)+'; import _distutils_hack; _distutils_hack.add_shim(); import runpy; runpy.run_path("sim_vision/run_closedloop.py",run_name="__main__")'
    started=time.time()
    workers=[]
    for i,seeds in enumerate(('12,13','14,15','16,17')):
        log=(out/f'worker-{i}.log').open('w')
        args=[sys.executable,'-u','-c',code,'--tag','controls','--modes',','.join(config['modes']),
              '--phis=-30,30','--seeds',seeds,'--faults','none','--calibration',str(vision/'calib-frozen.json')]
        workers.append((subprocess.Popen(args,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT),log))
    while any(p.poll() is None for p,_ in workers):
        time.sleep(2)
    for _,log in workers: log.close()
    result=dict(exit_codes=[p.returncode for p,_ in workers],wall_seconds=time.time()-started,
                started_unix=started,completed_unix=time.time(),workers=len(workers))
    (out/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    if any(result['exit_codes']): raise SystemExit(1)


if __name__=='__main__': main()
