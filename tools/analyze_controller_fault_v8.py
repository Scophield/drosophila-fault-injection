"""Paired task loss, controller interaction and activity sensitivity; no refitting."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from cross_records_v8 import FAULTS, MODES, PHIS, ROOT, SEEDS, load_records, sha


def cluster_interval(values):
    values = np.asarray(values, dtype=float)
    draws = np.random.default_rng(0).choice(values, size=(20000, len(values))).mean(axis=1)
    return dict(mean=float(values.mean()), seed_values=values.tolist(),
                conditional_cluster_bootstrap95=np.percentile(draws, [2.5, 97.5]).tolist())


def activity_ratio(fault, healthy, end):
    f = next(q['n_total'] for q in fault['log'] if q['t_end_ms'] == end)
    h = next(q['n_total'] for q in healthy['log'] if q['t_end_ms'] == end)
    if h <= 0:
        raise ValueError('healthy activity denominator is zero')
    return f / h


def analyze(root):
    records, result = load_records(root)
    result.update(groups={}, pairs=[], interactions={}, thresholds=[],
                  interpretation='six paired seed clusters; both bearings retained; exploratory conditional intervals, not population coverage')
    for mode in MODES:
        for fault in FAULTS:
            rows = [records[(mode, fault, phi, seed)] for phi in PHIS for seed in SEEDS]
            group = dict(n=len(rows), collision_free=sum(r['escaped'] for r in rows),
                         by_bearing={str(p): sum(r['escaped'] for r in rows if r['phi_t_deg'] == p) for p in PHIS},
                         active_burst_survivors=sum(r['burst_active_at_horizon'] for r in rows))
            result['groups'][f'{mode}/{fault or "healthy"}'] = group
            if fault is None:
                continue
            pairs = []
            for phi in PHIS:
                for seed in SEEDS:
                    h, f = records[(mode, None, phi, seed)], records[(mode, fault, phi, seed)]
                    end = min(h['duration_ms'], f['duration_ms'])
                    if end < 500:
                        raise ValueError('a declared common activity window is unavailable')
                    pair = dict(mode=mode, fault=fault, phi=phi, seed=seed,
                        healthy_survived=h['escaped'], fault_survived=f['escaped'],
                        task_loss=int(h['escaped'] and not f['escaped']),
                        task_gain=int(not h['escaped'] and f['escaped']),
                        net_loss=int(h['escaped']) - int(f['escaped']),
                        healthy_duration_ms=h['duration_ms'], fault_duration_ms=f['duration_ms'],
                        common_duration_ms=end, common_ratio=activity_ratio(f, h, end),
                        windows={str(w): activity_ratio(f, h, w) for w in (200, 300, 400, 500)})
                    pairs.append(pair)
            result['pairs'].extend(pairs)
            group.update(task_losses=sum(p['task_loss'] for p in pairs),
                         task_gains=sum(p['task_gain'] for p in pairs),
                         healthy_survivors=sum(p['healthy_survived'] for p in pairs),
                         net_loss=cluster_interval([np.mean([p['net_loss'] for p in pairs if p['seed'] == s]) for s in SEEDS]),
                         activity_medians={str(w): float(np.median([p['windows'][str(w)] for p in pairs])) for w in (200, 300, 400, 500)},
                         common_duration_median=float(np.median([p['common_ratio'] for p in pairs])))
            for window in (200, 300, 400, 500):
                for c in (1.5, 2.0, 3.0, 4.0):
                    flags = [p['windows'][str(window)] > c for p in pairs]
                    collision = [not p['fault_survived'] for p in pairs]
                    result['thresholds'].append(dict(mode=mode, fault=fault, window_ms=window, c=c,
                        flagged_collisions=sum(a and b for a, b in zip(flags, collision)),
                        unflagged_collisions=sum(not a and b for a, b in zip(flags, collision)),
                        flagged_survivors=sum(a and not b for a, b in zip(flags, collision)),
                        unflagged_survivors=sum(not a and not b for a, b in zip(flags, collision))))
    for fault in FAULTS[1:]:
        scores = []
        for seed in SEEDS:
            net = {mode: np.mean([p['net_loss'] for p in result['pairs']
                                 if p['mode'] == mode and p['fault'] == fault and p['seed'] == seed]) for mode in MODES}
            scores.append(net['precue_gated'] - net['brain'])
        result['interactions'][fault] = cluster_interval(scores)
    result['new_episode_seconds_total'] = sum(r['run_seconds'] for r in records.values() if r['fault'] is not None)
    result['analysis_sha256'] = sha(Path(__file__))
    result['validator_sha256'] = sha(ROOT / 'tools/cross_records_v8.py')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT / 'runs/controller-fault-v8')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    result = analyze(args.root)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'cross.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    flat = [{**{k:v for k,v in p.items() if k != 'windows'},
             **{f'ratio_{w}ms':v for w,v in p['windows'].items()}} for p in result['pairs']]
    with (args.out / 'pairs.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    with (args.out / 'thresholds.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(result['thresholds'][0]))
        writer.writeheader()
        writer.writerows(result['thresholds'])
    lines = ['# Frozen controller-by-fault results', '',
             '72 records: 24 reused healthy, 48 new fault episodes; six seed clusters.', '',
             '| Law / condition | -30 | +30 | Total | Loss / 12 | Gain / 12 |',
             '|---|---:|---:|---:|---:|---:|']
    for name, g in result['groups'].items():
        lines.append(f'| {name} | {g["by_bearing"]["-30.0"]}/6 | {g["by_bearing"]["30.0"]}/6 | {g["collision_free"]}/12 | {g.get("task_losses", "-")} | {g.get("task_gains", "-")} |')
    lines += ['', 'Interaction = gated minus original net task loss; each net loss is healthy minus fault survival.']
    for fault, contrast in result['interactions'].items():
        lines.append(f'{fault}: {contrast}')
    (args.out / 'results.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(groups=result['groups'], interactions=result['interactions'],
                          execution=result['execution']), indent=2))


if __name__ == '__main__':
    main()
