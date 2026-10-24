"""Fixed two-map V10 campaign, at most four hidden workers, durable phase logs.

No efficacy stopping, map selection, seed replacement or test-dependent tuning.
Resume validates every already executed worker configuration/source snapshot.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--design',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--resume',action='store_true')
    a=ap.parse_args();design=json.loads(a.design.read_text());a.out.mkdir(parents=True,exist_ok=a.resume)
    marker=a.out/'campaign.json';config=dict(design_sha256=sha(a.design),script_sha256=sha(__file__),workers_per_map=2,total_workers=4)
    if a.resume:assert json.loads(marker.read_text())==config
    else:marker.write_text(json.dumps(config,indent=2)+'\n')
    def run_map(spec):
        tag=spec['map_id'];base=a.out/('map-'+tag);base.mkdir(exist_ok=a.resume)
        state=base/'state.json';started=time.time()
        def update(**kw):state.write_text(json.dumps(dict(map_id=tag,utc=datetime.now(timezone.utc).isoformat(),**kw),indent=2)+'\n')
        def command(script,args,log):
            cmd=[sys.executable,'-u','tools/run_v9.py','tools/'+script,*map(str,args)]
            with log.open('a' if a.resume else 'x') as f:
                result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            if result.returncode:raise RuntimeError(f'{tag}: {script} failed ({result.returncode}); {log}')
        def matrix(phase,seeds,phis,modes,faults,horizon,cal=None,reg=None):
            folder=base/phase;folder.mkdir(exist_ok=a.resume)
            marker=folder/'phase.json'
            params=dict(phase=phase,seeds=seeds,phis=phis,modes=modes,faults=faults,horizon=horizon,
                calibration_sha256=sha(cal) if cal else None,registration_sha256=sha(reg) if reg else None,rf_map_sha256=spec['sha256'])
            if marker.exists():assert json.loads(marker.read_text())==params
            else:marker.write_text(json.dumps(params,indent=2)+'\n')
            procs=[];logs=[];commands=[];t=time.time()
            for i in range(2):
                args=['--out',folder,'--rf-map',spec['path'],'--design',a.design,'--seeds',','.join(map(str,seeds[i::2])),
                    '--phis='+','.join(map(str,phis)),'--modes',','.join(modes),'--faults',','.join(faults),'--horizon',horizon,
                    '--role','development' if phase=='development' else 'validation' if phase=='validation' else 'test']
                if cal:args+=['--calibration',cal]
                if reg:args+=['--registration',reg]
                if a.resume:args+=['--resume']
                cmd=[sys.executable,'-u','tools/run_v9.py','tools/run_task_v10.py',*map(str,args)]
                f=(folder/f'worker-{i}.log').open('a' if a.resume else 'x');logs.append(f);commands.append(cmd)
                procs.append(subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
            (folder/'active.json').write_text(json.dumps(dict(started_unix=t,pids=[p.pid for p in procs],commands=commands),indent=2)+'\n')
            update(phase=phase,status='running',pids=[p.pid for p in procs],output=str(folder))
            codes=[p.wait() for p in procs]
            for f in logs:f.close()
            n=len(list((folder/'episodes').glob('*.json')));expected=len(seeds)*len(phis)*len(modes)*len(faults)
            result=dict(started_unix=t,completed_unix=time.time(),elapsed_seconds=time.time()-t,exit_codes=codes,episodes=n,expected=expected)
            (folder/f'execution-{int(t)}.json').write_text(json.dumps(result,indent=2)+'\n')
            if any(codes) or n!=expected:raise RuntimeError(f'{tag} {phase}: incomplete {result}')
        try:
            for phase in ['development','validation','test']:
                cal=base/'calibration.json';reg=base/'registration.json'
                if phase=='development':
                    matrix(phase,spec['development_seeds'],design['phyis_development'],['observe'],['healthy'],400)
                    if not cal.exists():command('calibrate_task_v10.py',['--root',base/phase,'--design',a.design,'--rf-map',spec['path'],'--out',cal],base/'calibration.log')
                elif phase=='validation':
                    matrix(phase,spec['validation_seeds'],design['phis'],design['modes'],['healthy'],1000,cal)
                    if not reg.exists():command('freeze_rf_v10.py',['--validation',base/phase,'--calibration',cal,'--design',a.design,'--rf-map',spec['path'],'--out',reg],base/'freeze.log')
                else:matrix(phase,spec['test_seeds'],design['phis'],design['modes'],design['faults'],1000,cal,reg)
            update(phase='test',status='completed',elapsed_seconds=time.time()-started)
        except Exception as error:
            update(status='failed',error=str(error));raise
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(run_map,design['maps']))
    (a.out/'completed.json').write_text(json.dumps(dict(completed_utc=datetime.now(timezone.utc).isoformat(),maps=2,expected_episodes=392,design_sha256=sha(a.design)),indent=2)+'\n')


if __name__=='__main__':main()
