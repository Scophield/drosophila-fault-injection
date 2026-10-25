"""V10 RF-transfer worker; unchanged V9 neural/task dynamics, explicit frozen map."""
import argparse
import json
import os
from pathlib import Path
import time
import hashlib
import numpy as np
from run_provenance import prepare,sha256


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--rf-map',type=Path,required=True)
    ap.add_argument('--design',type=Path,required=True)
    ap.add_argument('--seeds',required=True)
    ap.add_argument('--phis',default='-30,30')
    ap.add_argument('--modes',default='observe')
    ap.add_argument('--faults',default='healthy')
    ap.add_argument('--calibration',type=Path)
    ap.add_argument('--horizon',type=float,default=1000.)
    ap.add_argument('--role',choices=['development','validation','test'],default='development')
    ap.add_argument('--registration',type=Path)
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args()
    import task_v9
    import pandas as pd
    from resource_v10 import resources
    from run_openloop import get_dn_sides
    from vision_v9 import PairedVisionSim
    out=args.out.resolve(); os.environ['FLY_RUN_DIR']=str(out)
    cal=json.loads(args.calibration.read_text()) if args.calibration else None
    mapping=json.loads(args.rf_map.read_text());design=json.loads(args.design.read_text())
    spec=next(q for q in design['maps'] if q['map_id']==mapping['map_id'])
    if sha256(args.rf_map)!=spec['sha256']:raise ValueError('RF mapping changed after design freeze')
    if cal and cal['rf_map_sha256']!=spec['sha256']:raise ValueError('calibration/RF mismatch')
    config=dict(protocol=task_v9.VERSION,seeds=[int(x) for x in args.seeds.split(',')],
        phis=[float(x) for x in args.phis.split(',')],modes=args.modes.split(','),faults=args.faults.split(','),
        horizon=args.horizon,calibration_sha256=sha256(args.calibration) if cal else None,
        role=args.role,registration_sha256=sha256(args.registration) if args.registration else None,
        rf_seed=mapping['rf_seed'],rf_map_sha256=sha256(args.rf_map),design_sha256=sha256(args.design),background_pool_seed=0,neural_dt_ms=.1,feedback_dt_ms=20.,
        threat_speed_m_s=.3,walk_speed_m_s=.05,burst_speed_m_s=.35,initial_distance_m=.25,
        collision_radius_m=.05,looming_radius_m=.05,cue_ms=100.,burst_delay_ms=250.,burst_duration_ms=450.,
        entrypoint_sha256={p:sha256(Path(p)) for p in ['tools/run_v9.py','tools/run_task_v10.py','tools/calibrate_task_v10.py','tools/prepare_rf_v10.py','tools/resource_v10.py']},
        stimulus_note='Common frame-indexed Bernoulli uniforms; independent deletion stream; hashes recorded. Seed traceability does not promise cross-platform bit identity.')
    if config['modes']!=['observe'] and cal is None: raise ValueError('calibration required')
    if len(set(config['seeds']))!=len(config['seeds']) or len(set(config['phis']))!=len(config['phis']):
        raise ValueError('duplicate seed/bearing')
    if args.horizon<=0 or args.horizon%20 or not all(__import__('math').isfinite(x) for x in config['phis']):
        raise ValueError('invalid horizon or bearing')
    if cal and set(config['seeds']) & set(cal['development_seeds']):
        raise ValueError('calibration/evaluation seed overlap')
    if args.role=='test':
        if args.registration is None: raise ValueError('independent tests require prior registration')
        reg=json.loads(args.registration.read_text())
        if (not set(config['seeds'])<=set(reg['test_seeds']) or config['phis']!=reg['phis']
            or config['modes']!=reg['modes'] or config['faults']!=reg['faults']
            or config['horizon']!=reg['horizon_ms'] or config['calibration_sha256']!=reg['calibration_sha256']):
            raise ValueError('test configuration differs from frozen registration')
        if any(sha256(Path(name))!=value for name,value in reg['frozen_source_sha256'].items()):
            raise ValueError('source changed after test registration')
        from project_paths import MODEL_DIR,PATH_COMP,PATH_CON,PATH_ANN
        if ({p.name:sha256(p) for p in [MODEL_DIR/'model.py',PATH_COMP,PATH_CON]}!=reg['model_inputs_sha256']
                or sha256(PATH_ANN)!=reg['annotations_sha256']):
            raise ValueError('model inputs changed after registration')
        if any(config[name]!=value for name,value in reg['geometry'].items()):
            raise ValueError('geometry differs from registration')
        import importlib.metadata
        import sys
        if (sys.version!=reg['runtime']['python'] or any(importlib.metadata.version(name)!=value
                for name,value in reg['runtime']['packages'].items())):
            raise ValueError('runtime differs from frozen registration; use a new replication registration')
    key=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:12]
    batch=prepare(out/'batches'/key,config,args.resume)
    for name,expected in config['entrypoint_sha256'].items():
        path=batch/'source'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists(): path.write_bytes(Path(name).read_bytes())
        if sha256(path)!=expected: raise ValueError('runner snapshot mismatch')
    (out/'episodes').mkdir(exist_ok=True)
    rf=pd.DataFrame(mapping['rows']);rf['root_id']=rf.root_id.astype(np.int64);cmd,_=get_dn_sides()
    for source in [args.rf_map,args.design]:
        target=batch/'source'/source.resolve().relative_to(Path.cwd().resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.write_bytes(source.read_bytes())
        if sha256(target)!=sha256(source):raise ValueError('RF/design snapshot mismatch')
    if cal and ([int(f) for f in cmd.flyid]!=cal['command_flyids'] or
                cal['protocol']!=task_v9.VERSION):
        raise ValueError('command mapping or calibration protocol differs')
    t=time.perf_counter(); sim=PairedVisionSim(cmd.flyid); build=time.perf_counter()-t
    sim.arm_stim_weights(rf.root_id.tolist())
    input_map=dict(pool_flyids=[str(f) for f in sim.pool_flyids],
        sensory=[dict(flyid=str(int(r.root_id)),phi_deg=float(r.phi_deg),psi_deg=float(r.psi_deg),w_grad=float(r.w_grad))
                 for r in rf.itertuples()],
        commands=[dict(flyid=str(int(r.flyid)),cell_type=r.cell_type,side=r.side) for r in cmd.itertuples()],
        note='pool includes inactive background entries; all non-sensory input rates/weights are zero')
    encoded=json.dumps(input_map,sort_keys=True,indent=2).encode()
    map_path=out/'input-map.json'
    try:
        with map_path.open('xb') as f: f.write(encoded)
    except FileExistsError:
        for attempt in range(20):
            if map_path.read_bytes()==encoded: break
            time.sleep(.05)
        else: raise ValueError('mixed input/RF maps in run directory')
    damage_cache={}
    original_mass=float(np.abs(sim.w0).sum())
    for seed in config['seeds']:
        for phi in config['phis']:
            for mode in config['modes']:
                for fault in config['faults']:
                    path=out/'episodes'/f'{mode}_{fault}_phi{phi:g}_s{seed}.json'
                    if path.exists():
                        if args.resume:
                            if json.loads(path.read_text())['run_manifest_sha256']!=sha256(batch/'run_manifest.json'):
                                raise ValueError('incompatible resume')
                            continue
                        raise FileExistsError(path)
                    t=time.perf_counter()
                    res=task_v9.run(sim,rf,cmd,seed,phi,fault,mode,cal,horizon=args.horizon)
                    damage_key=(seed,fault)
                    if damage_key not in damage_cache:
                        mask=task_v9.deletion_mask(len(sim.w0),seed,{'healthy':0.,'F2_25':.25,'F2_50':.5}[fault])
                        if task_v9.mask_hash(mask)!=res['mask_sha256']: raise ValueError('cannot reconstruct generated mask')
                        damage_cache[damage_key]=dict(deleted_abs_weight_fraction=float(np.abs(sim.w0[mask]).sum()/original_mass),
                            deleted_exc_rows=int(np.sum(mask&(sim.w0>0))),deleted_inh_rows=int(np.sum(mask&(sim.w0<0))),
                            deleted_zero_rows=int(np.sum(mask&(sim.w0==0))))
                    res.update(wall_seconds=time.perf_counter()-t,build_seconds=build,
                        experiment_version=design['experiment'],map_id=mapping['map_id'],rf_map_sha256=spec['sha256'],worker_resources=resources(),
                        input_map_sha256=hashlib.sha256(encoded).hexdigest(),
                        n_neurons=sim.n_neurons,n_connection_rows=sim.n_syn,
                        run_manifest_sha256=sha256(batch/'run_manifest.json'),calibration_sha256=config['calibration_sha256'],
                        **damage_cache[damage_key])
                    with path.open('x') as f: json.dump(res,f)
                    print(json.dumps({k:v for k,v in res.items() if k!='log'}),flush=True)


if __name__=='__main__': main()
