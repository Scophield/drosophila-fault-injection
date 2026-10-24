"""Geometry and evaluation rules for fresh runs; archive semantics stay unchanged."""
import json
from pathlib import Path

import numpy as np

PROTOCOL_VERSION = 'geometry-v2'


def wrap_degrees(angle):
    return (np.asarray(angle) + 180.0) % 360.0 - 180.0


def retinal_input(rf, relative_xy, heading_rad, radius_m, dt_s,
                  previous_angle=None, closing_speed=0.0, enabled=True):
    distance = max(float(np.linalg.norm(relative_xy)), 1e-9)
    bearing = float(wrap_degrees(np.degrees(np.arctan2(relative_xy[1], relative_xy[0]))
                                 - np.degrees(heading_rad)))
    angle = float(np.degrees(np.arctan(radius_m / distance)))
    expansion = (np.degrees(radius_m * closing_speed / (distance**2 + radius_m**2))
                 if previous_angle is None else (angle - previous_angle) / dt_s)
    gain = float(np.clip(max(0.0, expansion) / 150.0 * np.exp(-angle / 60.0), 0, 1))
    if not enabled:
        gain = 0.0
    dphi = np.radians(wrap_degrees(np.asarray(rf['phi_deg']) - bearing))
    dpsi = np.radians(np.asarray(rf['psi_deg']) - 0.0)
    sigma = np.radians(max(30.0, angle))
    rates = np.clip(150.0 * np.asarray(rf['w_grad']) *
                    np.exp(-(dphi**2 + dpsi**2) / (2 * sigma**2)) * gain, 0, 150)
    return rates, dict(phi_now=bearing, half_angle=angle, u=gain, distance=distance)


def segment_min_distance(before, after):
    before, after = np.asarray(before, dtype=float), np.asarray(after, dtype=float)
    delta = after - before
    norm2 = float(delta @ delta)
    fraction = np.clip(-float(before @ delta) / norm2, 0, 1) if norm2 else 0.0
    return float(np.linalg.norm(before + fraction * delta))


def frame_count(duration_ms, frame_ms):
    if not np.isfinite(duration_ms) or not np.isfinite(frame_ms) or frame_ms <= 0:
        raise ValueError('duration and frame interval must be finite; interval must be positive')
    n = int(round(duration_ms / frame_ms))
    if n < 1 or not np.isclose(n * frame_ms, duration_ms):
        raise ValueError('duration must be a positive whole number of frames')
    return n


def episode_key(row):
    return float(row['phi_t_deg']), int(row['seed'])


def calibration_keys(calibration, episode_dir=None):
    if 'calibration_keys' in calibration:
        return {(float(r['phi']), int(r['seed'])) for r in calibration['calibration_keys']}
    if episode_dir is None or not Path(episode_dir).is_dir():
        raise ValueError('calibration keys or original calibration episode directory required')
    paths = sorted(Path(episode_dir).glob('brain_healthy_phi*.json'))
    if not paths:
        raise ValueError('no original calibration episodes found')
    return {episode_key(json.loads(p.read_text())) for p in paths}


def validate_test_keys(phis, seeds, training_keys):
    overlap = {(float(phi), int(seed)) for phi in phis for seed in seeds} & training_keys
    shared_seeds = set(seeds) & {seed for _, seed in training_keys}
    if overlap or shared_seeds:
        raise ValueError(f'calibration/test overlap: {sorted(overlap)}, shared seeds {sorted(shared_seeds)}; select new seeds')


def validate_calibration(calibration):
    if not calibration or calibration.get('protocol_version') != PROTOCOL_VERSION:
        raise ValueError('fresh geometry runs require a geometry-v2 calibration; collect observe episodes first')
    for name in ('theta_demo_hz', 'lr_ref', 'bias', 'data_sign'):
        if not np.isfinite(calibration[name]):
            raise ValueError(f'nonfinite calibration value: {name}')
    if calibration['lr_ref'] <= 0 or calibration['theta_demo_hz'] <= 0:
        raise ValueError('calibration reference and threshold must be positive')
    if calibration['data_sign'] not in (-1, 1):
        raise ValueError('calibration data_sign must be -1 or 1')
