"""Re-analyze archived trials with calibration separation and equal spike exposure."""
import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sim_vision'))
from closedloop_protocol import calibration_keys, episode_key
from audit_archive import load, summarize, protocols


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exposure(episode, window_ms=None):
    log = episode['log']
    if len(log) < 2:
        raise ValueError('cannot recover frame duration from fewer than two frames')
    deltas = np.diff([q['t_ms'] for q in log])
    dt = float(deltas[0])
    if dt <= 0 or not np.allclose(deltas, dt) or log[0]['t_ms'] != 0:
        raise ValueError('nonuniform episode timestamps')
    duration = len(log) * dt
    window = duration if window_ms is None else float(window_ms)
    n = int(round(window / dt))
    if n < 1 or window > duration + 1e-6 or not np.isclose(n * dt, window):
        raise ValueError('window is unavailable or not frame-aligned')
    return dict(duration_ms=duration, window_ms=window, spikes=int(log[n - 1]['n_total']),
                spikes_per_second=float(log[n - 1]['n_total']) / (window / 1000.0))


def split_summary(episodes, training_keys):
    groups = {'calibration_reuse': [], 'nonoverlap_negative': [], 'positive_azimuth': [], 'frontal': []}
    for episode in episodes:
        phi, seed = episode_key(episode)
        group = ('calibration_reuse' if (phi, seed) in training_keys else
                 'frontal' if phi == 0 else 'positive_azimuth' if phi > 0 else 'nonoverlap_negative')
        groups[group].append(episode)
    return {name: dict(n=len(rows), survived=sum(r['escaped'] for r in rows),
                       keys=[dict(phi=episode_key(r)[0], seed=episode_key(r)[1]) for r in rows])
            for name, rows in groups.items()}


def cluster_interval(rows, field):
    seeds = sorted({r['seed'] for r in rows})
    rng = np.random.default_rng(0)
    samples = rng.choice(seeds, size=(20000, len(seeds)))
    groups = {s: [r[field] for r in rows if r['seed'] == s] for s in seeds}
    values = [np.median([v for s in sample for v in groups[s]]) for sample in samples]
    return np.percentile(values, [2.5, 97.5]).tolist()


def analyze(vision):
    calib_path = vision / 'calib.json'
    training_paths = sorted((vision / 'episodes_train').glob('brain_healthy_phi*.json'))
    keys = calibration_keys(json.loads(calib_path.read_text()), vision / 'episodes_train')
    healthy = {}
    for path in sorted((vision / 'episodes_v4').glob('brain_healthy_phi*.json')):
        row = json.loads(path.read_text())
        if episode_key(row) in healthy:
            raise ValueError('duplicate healthy key')
        healthy[episode_key(row)] = row
    overlaps = []
    for path in training_paths:
        row = json.loads(path.read_text())
        other = healthy.get(episode_key(row))
        overlaps.append(dict(phi=episode_key(row)[0], seed=episode_key(row)[1],
                             identical_log=other is not None and row['log'] == other['log']))
    output = dict(healthy_splits=split_summary(list(healthy.values()), keys),
                  calibration_overlap=overlaps, common_window_ms=400.0, conditions={})
    for tag, fault in [('v4', 'F2_25'), ('v4', 'F2_50'), ('v4', 'F4_1pct'), ('v4c', 'HUB_inh')]:
        rows = []
        for path in sorted((vision / f'episodes_{tag}').glob(f'brain_{fault}_phi*.json')):
            episode = json.loads(path.read_text())
            key = episode_key(episode)
            reference = healthy[key]
            e, h = exposure(episode), exposure(reference)
            common = min(e['duration_ms'], h['duration_ms'])
            rows.append(dict(phi=key[0], seed=key[1], survived=episode['escaped'],
                       calibration_scenario=key in keys,
                       episode_ratio=e['spikes'] / h['spikes'],
                       rate_ratio=e['spikes_per_second'] / h['spikes_per_second'],
                       common_exposure_ms=common,
                       common_ratio=exposure(episode, common)['spikes'] / exposure(reference, common)['spikes'],
                       fixed400_ratio=exposure(episode, 400)['spikes'] / exposure(reference, 400)['spikes'],
                       duration_ms=e['duration_ms'], healthy_duration_ms=h['duration_ms']))
        if len(rows) != 12 or len({(r['phi'], r['seed']) for r in rows}) != 12:
            raise ValueError(f'incomplete fault grid: {fault}')
        output['conditions'][fault] = dict(n=len(rows), survived=sum(r['survived'] for r in rows), pairs=rows,
            median_episode_ratio=float(np.median([r['episode_ratio'] for r in rows])),
            median_common_ratio=float(np.median([r['common_ratio'] for r in rows])),
            median_fixed400_ratio=float(np.median([r['fixed400_ratio'] for r in rows])),
            fixed400_cluster_ci95=cluster_interval(rows, 'fixed400_ratio'),
            sensitivity={str(c): {metric: sum(r[metric] > c for r in rows)
                                 for metric in ('episode_ratio', 'common_ratio', 'fixed400_ratio')}
                         for c in (1.5, 2, 3, 4)})
    return output


def wilson(successes, total):
    z = 1.959963984540054
    p, den = successes / total, 1 + z*z/total
    mid = (p + z*z/(2*total)) / den
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / den
    return [mid-half, mid+half]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    core = ROOT / 'sim/results/real'
    ctrl = ROOT / 'sim_vision/results_vision/openloop_controls'
    vision = ROOT / 'sim_vision/results_vision'
    records = {p.stem: load(p) for p in sorted(core.glob('*.jsonl'))}
    baseline = summarize(records['healthy'])
    families = {name: summarize(rows) for name, rows in records.items()}
    summary = analyze(vision)
    summary['fault_families'] = families
    summary['protocols'] = protocols(core, ctrl, baseline)
    summary['random_inhibitory_failure_wilson95_iid_reference'] = wilson(2, 12)
    summary['openloop_sensitivity'] = {}
    all_rows = [rows for name, rows in records.items() if name != 'healthy']
    all_rows += [load(p) for p in ctrl.glob('*.jsonl') if p.stem.startswith(('HUB_', 'EIm_', 'INHrand_'))]
    for c in (1.5, 2, 3, 4):
        summary['openloop_sensitivity'][str(c)] = sum(
            r['pop_rate'] >= 51.4 and r['pop_rate'] <= c*baseline['rate_med'] and
            r['n_total_spikes'] <= c*baseline['tot_med'] for rows in all_rows for r in rows)
    sources = sorted(set(list((ROOT/'sim/results').rglob('*.jsonl')) +
                        list(ctrl.glob('*.jsonl')) + list(vision.glob('episodes_*/*.json')) + [vision/'calib.json']))
    summary['manifest'] = dict(numpy=np.__version__, python=sys.version, script_sha256=sha256(Path(__file__)),
                              source_sha256={str(p.relative_to(ROOT)):sha256(p) for p in sources},
                              caveat='archive re-analysis only; fresh geometry-v2 dynamics and corrected hubs unmeasured',
                              interval='20000 bootstrap draws over 3 seeds, keeping azimuths together; conditional on calibration')
    (args.out/'revision_analysis.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    columns = ['condition', 'n', 'rate_med', 'rate_ci95_low', 'rate_ci95_high', 'lat_med', 'tot_med', 'transmission_pass']
    with (args.out/'fault_families.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for name, values in families.items():
            writer.writerow(dict(condition=name, n=values['n'], rate_med=values['rate_med'],
                                 rate_ci95_low=values['rate_ci95'][0], rate_ci95_high=values['rate_ci95'][1],
                                 lat_med=values['lat_med'], tot_med=values['tot_med'], transmission_pass=values['transmission_pass']))
    print(json.dumps(summary['healthy_splits'], indent=2))
    for name, condition in summary['conditions'].items():
        print(name, json.dumps({k:v for k,v in condition.items() if k != 'pairs'}))
    print('open-loop envelope sensitivity:', summary['openloop_sensitivity'])


if __name__ == '__main__':
    main()

