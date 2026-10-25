"""Fit a frozen calibration from passive, controller-independent fresh episodes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from closedloop_protocol import PROTOCOL_VERSION, episode_key, validate_calibration


def fit_calibration(paths):
    episodes, hashes, keys = [], {}, set()
    for path in sorted(paths):
        row = json.loads(path.read_text())
        if (row.get('protocol_version') != PROTOCOL_VERSION or row.get('mode') != 'observe'
                or row.get('evaluation_role') != 'calibration' or row.get('fault') is not None):
            raise ValueError(f'not a passive geometry-v2 calibration episode: {path}')
        key = episode_key(row)
        if key in keys:
            raise ValueError(f'duplicate calibration episode: {key}')
        keys.add(key)
        hashes[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
        episodes.append(row)
    if not episodes:
        raise ValueError('no calibration episodes')
    seeds = {seed for _, seed in keys}
    if len(seeds) < 3 or keys != {(phi, seed) for phi in (-60.0, -30.0, 0.0) for seed in seeds}:
        raise ValueError('require a complete -60/-30/0 degree calibration grid with at least three seeds')
    configs = {(e['rf_seed'], e['threat_speed'], e['frame_dt_ms']) for e in episodes}
    if len(configs) != 1:
        raise ValueError('mixed calibration configurations')
    rf_seed, speed, frame_dt = configs.pop()
    peaks, negative_lr, frontal_lr = [], [], []
    for e in episodes:
        window = [q for q in e['log'] if 250 <= q.get('t_end_ms',q['t_ms']+frame_dt) <= 300]
        if not window or window[-1].get('t_end_ms',window[-1]['t_ms']+frame_dt) < 300:
            raise ValueError('episode does not cover calibration window [250,300] ms')
        if e['phi_t_deg'] < 0:
            peaks.append(max(q['cmd_s'] for q in window))
            negative_lr.append(float(np.mean([q['lr_s'] for q in window])))
        else:
            frontal_lr.append(float(np.mean([q['lr_s'] for q in window])))
    bias = float(np.median(frontal_lr))
    lr_mean = float(np.mean(negative_lr))
    result = dict(protocol_version=PROTOCOL_VERSION, theta_demo_hz=float(np.median(peaks)),
                  data_sign=-1.0 if lr_mean > bias else 1.0, bias=bias,
                  lr_ref=float(np.percentile(np.abs(np.asarray(negative_lr) - bias), 90)),
                  rf_seed=rf_seed, threat_speed=speed, frame_dt_ms=frame_dt,
                  calibration_keys=[dict(phi=p, seed=s) for p, s in sorted(keys)],
                  source_sha256=hashes,
                  theta_source='median of negative-azimuth episode maxima with frame end in [250,300] ms',
                  note='passive observe mode: no steering, threshold, or burst used for calibration')
    validate_calibration(result)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    result = fit_calibration(args.input.glob('*.json'))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(f'frozen calibration: {len(result["calibration_keys"])} episodes -> {args.out}')


if __name__ == '__main__':
    main()
