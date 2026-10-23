"""Summarize an explicit completed geometry-v2 test matrix without refitting."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sim_vision'))
from closedloop_protocol import calibration_keys, validate_calibration, validate_test_keys


def summarize(root, calibration, seeds, phis, modes=('brain',), faults=(None, 'F2_25', 'F2_50')):
    root, calibration = Path(root).resolve(), Path(calibration).resolve()
    if any(not values or len(set(values)) != len(values) for values in (seeds, phis, modes, faults)):
        raise ValueError('matrix dimensions must be nonempty and unique')
    if 'brain' not in modes or None not in faults:
        raise ValueError('matrix must include the healthy brain reference')
    c = json.loads(calibration.read_text())
    validate_calibration(c)
    validate_test_keys(phis, seeds, calibration_keys(c))
    calibration_hash = hashlib.sha256(calibration.read_bytes()).hexdigest()
    calibration_sources = {p.name:p for p in (root/'vision/episodes_calibration').glob('*.json')}
    if len(calibration_sources) != len(c['source_sha256']):
        raise ValueError('calibration source grid differs from frozen inputs')
    for original, expected_hash in c['source_sha256'].items():
        source=calibration_sources[Path(original).name]
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected_hash:
            raise ValueError(f'calibration input changed: {source}')
    manifests={hashlib.sha256(p.read_bytes()).hexdigest():json.loads(p.read_text())
               for p in (root/'vision/batches').glob('*/run_manifest.json')}
    output = dict(complete=True, calibration_sha256=calibration_hash,
                  experiment_root=str(root.relative_to(ROOT)),
                  calibration_path=str(calibration.relative_to(ROOT)),
                  modes=list(modes),faults=list(faults),
                  calibration_seed_clusters=sorted({s for _,s in calibration_keys(c)}),
                  test_seed_clusters=seeds, azimuths=phis, groups={}, source_sha256={},
                  generation_manifests={})
    source_files = list((root / 'vision/episodes_evaluation').glob('*.json'))
    source_files += list((root / 'vision/episodes_controls').glob('*.json'))
    records = {}
    runtime_reference = None
    for p in source_files:
        row = json.loads(p.read_text())
        key = (row['mode'],row['fault'],row['phi_t_deg'],row['seed'])
        if key in records:
            raise ValueError(f'duplicate test scenario: {key}')
        if row.get('protocol_version') != 'geometry-v2' or row.get('evaluation_role') != 'test':
            raise ValueError(f'not a prospective test record: {p}')
        if row.get('calibration_sha256') != calibration_hash:
            raise ValueError(f'mixed calibration: {p}')
        manifest=manifests.get(row.get('run_manifest_sha256'))
        if manifest is None:
            raise ValueError(f'missing generation manifest: {p}')
        parameters=manifest['parameters']
        if parameters['evaluation_role']!='test' or parameters['calibration_sha256']!=calibration_hash:
            raise ValueError(f'manifest role/calibration mismatch: {p}')
        if manifest.get('runtime_backend')!='numpy' or manifest['neural_dt_ms']!=.1:
            raise ValueError(f'not the declared NumPy / 0.1-ms runtime: {p}')
        if (row['mode'] not in parameters['modes'].split(',') or
                float(row['phi_t_deg']) not in [float(v) for v in parameters['phis'].split(',')] or
                int(row['seed']) not in [int(v) for v in parameters['seeds'].split(',')]):
            raise ValueError(f'scenario differs from generation manifest: {p}')
        declared_faults = [None if v in ('','none') else v for v in parameters['faults'].split(',')]
        if row['fault'] not in declared_faults:
            raise ValueError(f'fault differs from generation manifest: {p}')
        if (row['horizon_ms'] != parameters['duration_ms'] or
                row['frame_dt_ms'] != parameters['frame_dt_ms'] or
                row['rf_seed'] != parameters['rf_seed'] or
                row['threat_speed'] != parameters['threat_speed']):
            raise ValueError(f'episode parameters differ from generation manifest: {p}')
        if any(row[name] != c[name] for name in ('frame_dt_ms','rf_seed','threat_speed')):
            raise ValueError(f'episode configuration differs from calibration: {p}')
        runtime = {name:manifest.get(name) for name in
                   ('model_inputs','annotations_sha256','packages','neural_dt_ms',
                    'runtime_backend','sensory_refractory_ms')}
        runtime['geometry'] = {name:parameters.get(name) for name in
                               ('duration_ms','threat_speed','burst_delay_ms','rf_seed',
                                'frame_dt_ms','retinal_elevation_deg','protocol_version')}
        if runtime_reference is None:
            runtime_reference = runtime
        elif runtime != runtime_reference:
            raise ValueError(f'mixed simulator inputs or runtime: {p}')
        if row['termination_reason'] not in {'horizon','collision'} or (
                bool(row['escaped']) != (row['termination_reason']=='horizon')):
            raise ValueError(f'inconsistent collision endpoint: {p}')
        if (row['duration_ms'] > row['horizon_ms'] or
                row['log'][-1]['t_end_ms'] != row['duration_ms'] or
                row['escaped'] and row['duration_ms'] != row['horizon_ms']):
            raise ValueError(f'inconsistent observation horizon: {p}')
        output['generation_manifests'][row['run_manifest_sha256']] = manifest
        records[key] = row
        output['source_sha256'][str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    expected = {(mode,fault,float(phi),seed) for mode in modes for fault in
                (faults if mode=='brain' else (None,)) for phi in phis for seed in seeds}
    if set(records) != expected:
        raise ValueError(f'matrix mismatch: missing {sorted(expected-set(records),key=str)}, extra {sorted(set(records)-expected,key=str)}')
    for mode in modes:
        for fault in (faults if mode=='brain' else (None,)):
            rows = [records[(mode,fault,float(phi),s)] for phi in phis for s in seeds]
            by_seed = {str(s):sum(r['escaped'] for r in rows if r['seed']==s) for s in seeds}
            output['groups'][f'{mode}/{fault or "healthy"}'] = dict(
                n=len(rows),collision_free=sum(r['escaped'] for r in rows),
                collisions=sum(r['termination_reason']=='collision' for r in rows),
                horizon_ms=sorted({r['horizon_ms'] for r in rows}),
                seed_collision_free_counts=by_seed,
                azimuth_collision_free_counts={str(phi):sum(r['escaped'] for r in rows if r['phi_t_deg']==phi)
                                               for phi in phis},
                burst_active_at_horizon=sum(r['burst_active_at_horizon'] for r in rows))
    for fault in [f for f in faults if f is not None]:
        pairs=[]
        for phi in phis:
            for s in seeds:
                h=records[('brain',None,float(phi),s)]
                r=records[('brain',fault,float(phi),s)]
                end=min(h['duration_ms'],r['duration_ms'])
                for window in (200,300,400,500):
                    if window>end:
                        raise ValueError(f'common window {window} unavailable: {phi}, {s}')
                    hs=next(q['n_total'] for q in h['log'] if q['t_end_ms']==window)
                    rs=next(q['n_total'] for q in r['log'] if q['t_end_ms']==window)
                    if hs<=0:
                        raise ValueError('zero healthy reference activity')
                    pairs.append(dict(phi=phi,seed=s,window_ms=window,ratio=rs/hs))
        output['groups'][f'brain/{fault}']['activity_windows']={str(w):dict(
            median=float(np.median([r['ratio'] for r in pairs if r['window_ms']==w])),
            exceedances=sum(r['ratio']>2 for r in pairs if r['window_ms']==w),
            azimuth_medians={str(phi):float(np.median([r['ratio'] for r in pairs
                            if r['window_ms']==w and r['phi']==phi])) for phi in phis},
            seed_medians={str(s):float(np.median([r['ratio'] for r in pairs
                          if r['window_ms']==w and r['seed']==s])) for s in seeds})
            for w in (200,300,400,500)}
        output['groups'][f'brain/{fault}']['activity_pairs']=pairs
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--calibration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seeds',default='6,7,8,9,10,11')
    ap.add_argument('--phis',default='-30,30')
    ap.add_argument('--modes',default='brain')
    ap.add_argument('--faults',default='none,F2_25,F2_50')
    args=ap.parse_args()
    result=summarize(args.root,args.calibration,[int(s) for s in args.seeds.split(',')],
                     [float(p) for p in args.phis.split(',')],args.modes.split(','),
                     [None if f=='none' else f for f in args.faults.split(',')])
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False)
        f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':
    main()
