"""Validate the complete 72-record controller-by-fault matrix and its provenance."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODES = ('brain', 'precue_gated')
FAULTS = (None, 'F2_25', 'F2_50')
SEEDS = tuple(range(12, 18))
PHIS = (-30.0, 30.0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_records(root):
    root = Path(root).resolve()
    execution = json.loads((root / 'execution.json').read_text())
    if execution['exit_codes'] != [0, 0, 0]:
        raise ValueError('not all three fault workers completed successfully')
    campaign = json.loads((root / 'campaign.json').read_text())
    if campaign['seeds'] != list(SEEDS) or campaign['modes'] != list(MODES):
        raise ValueError('campaign seed/controller plan differs')
    calibration = root / 'vision/calib-frozen.json'
    calibration_hash = sha(calibration)
    if calibration_hash != sha(ROOT / 'runs/geometry-v3/vision/calib-geometry-v3.json'):
        raise ValueError('frozen calibration changed')
    c = json.loads(calibration.read_text())
    if set(SEEDS) & {k['seed'] for k in c['calibration_keys']}:
        raise ValueError('test seeds overlap calibration')
    for name, expected in c['source_sha256'].items():
        if sha(root / 'vision/episodes_calibration' / Path(name).name) != expected:
            raise ValueError('calibration input changed')
    manifests = {}
    runtime = None
    source_reference = None
    for p in (root / 'vision/batches').glob('*/run_manifest.json'):
        m = json.loads(p.read_text())
        for name, expected in m['source_sha256'].items():
            if sha(p.parent / 'source' / name) != expected:
                raise ValueError(f'generating snapshot changed: {name}')
        aggregate = ''.join(f'{name}:{m["source_sha256"][name]}\n'
                            for name in sorted(m['source_sha256'])
                            if not name.startswith('external/'))
        if hashlib.sha256(aggregate.encode()).hexdigest() != m['code_sha256']:
            raise ValueError('aggregate generating-source hash differs')
        source_reference = source_reference or m['source_sha256']
        if source_reference != m['source_sha256']:
            raise ValueError('healthy/fault generating sources differ')
        comparable = {k: m[k] for k in ('model_inputs', 'annotations_sha256', 'packages',
                       'neural_dt_ms', 'runtime_backend', 'sensory_refractory_ms')}
        geometry = ('duration_ms', 'threat_speed', 'burst_delay_ms', 'rf_seed',
                    'frame_dt_ms', 'retinal_elevation_deg', 'protocol_version')
        comparable['geometry'] = {k: m['parameters'][k] for k in geometry}
        runtime = runtime or comparable
        if comparable != runtime or m['neural_dt_ms'] != .1 or m['runtime_backend'] != 'numpy':
            raise ValueError('mixed runtime, model inputs or geometry')
        manifests[sha(p)] = m
    records, hashes = {}, {}
    for p in (root / 'vision/episodes_controls').glob('*.json'):
        r = json.loads(p.read_text())
        key = (r['mode'], r['fault'], float(r['phi_t_deg']), r['seed'])
        if key in records:
            raise ValueError(f'duplicate episode: {key}')
        m = manifests[r['run_manifest_sha256']]
        params = m['parameters']
        declared_faults = [None if v == 'none' else v for v in params['faults'].split(',')]
        if (r['mode'] not in params['modes'].split(',') or r['fault'] not in declared_faults
                or r['seed'] not in list(map(int, params['seeds'].split(',')))
                or float(r['phi_t_deg']) not in list(map(float, params['phis'].split(',')))):
            raise ValueError('record differs from declared generation matrix')
        if (r['calibration_sha256'] != calibration_hash or params['calibration_sha256'] != calibration_hash
                or r['evaluation_role'] != 'test' or params['evaluation_role'] != 'test'
                or r['protocol_version'] != 'geometry-v2'):
            raise ValueError('role/protocol/calibration mismatch')
        if (r['brian_seed'] != 20000 + r['seed'] or r['fault_seed'] != 10000 + r['seed']
                or r['horizon_ms'] != 1000 or params['duration_ms'] != 1000
                or any(r[k] != c[k] for k in ('rf_seed', 'threat_speed', 'frame_dt_ms'))):
            raise ValueError('seed or geometry mismatch')
        log = r['log']
        if [q['t_end_ms'] for q in log] != list(np.arange(20, r['duration_ms'] + 1, 20)):
            raise ValueError('missing, reordered or duplicate frames')
        spikes = np.array([q['n_total'] for q in log])
        if np.any(np.diff(spikes) < 0) or spikes[-1] != r['n_total']:
            raise ValueError('inconsistent cumulative activity')
        collision = min(q['step_min_dist'] for q in log) <= .05
        if collision != (not r['escaped']) or r['termination_reason'] != ('collision' if collision else 'horizon'):
            raise ValueError('collision outcome differs from trajectory')
        if not collision and r['duration_ms'] != 1000:
            raise ValueError('survivor does not reach the requested horizon')
        hist, trigger = [], None
        for q in log:
            hist.append(sum(q['cmd_rates'].values()) / 8)
            if trigger is None and len(hist) >= 2 and np.mean(hist[-5:]) >= c['theta_demo_hz'] and hist[-2] >= c['theta_demo_hz']:
                trigger = q['t_end_ms']
            expected = -400 * np.clip(c['data_sign'] * (q['lr_s'] - c['bias']) / c['lr_ref'], -1, 1)
            if r['mode'] == 'precue_gated' and q['t_ms'] < 100:
                expected = 0
            if not np.isclose(q['omega'], expected):
                raise ValueError('steering law differs from frozen calibration')
        if trigger != r['trigger_ms']:
            raise ValueError('trigger differs from raw command rates')
        if r['fault'] is None:
            original = ROOT / 'runs/controller-v4a/vision/episodes_controls' / p.name
            if sha(original) != sha(p) or campaign['reused_healthy'][str(original.relative_to(ROOT))] != sha(p):
                raise ValueError('reused healthy episode changed')
        records[key] = r
        hashes[str(p.relative_to(ROOT))] = sha(p)
    expected = {(m, f, p, s) for m in MODES for f in FAULTS for p in PHIS for s in SEEDS}
    if set(records) != expected:
        raise ValueError(f'incomplete matrix: missing={expected-set(records)}, extra={set(records)-expected}')
    return records, dict(complete=True, record_count=len(records), new_records=48,
        reused_healthy_records=24, calibration_sha256=calibration_hash, runtime=runtime,
        source_sha256=hashes, generation_manifests=manifests, execution=execution,
        campaign_sha256=sha(root / 'campaign.json'), test_seed_clusters=list(SEEDS),
        modes=list(MODES), faults=list(FAULTS), azimuths=list(PHIS))
