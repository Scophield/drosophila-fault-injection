"""Cohort and exposure sensitivity of the immutable archive, without simulation."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

from audit_archive import load
from audit_revision import analyze, exposure

ROOT = Path(__file__).resolve().parents[1]


def score(rows, rate_ref, spike_ref, factor=2):
    transmission = [r['pop_rate'] >= 51.4 for r in rows]
    joint = [ok and r['pop_rate'] <= factor * rate_ref and
             r['n_total_spikes'] <= factor * spike_ref for r, ok in zip(rows, transmission)]
    return dict(n=len(rows), transmission=sum(transmission), joint=sum(joint),
                additional_rejections=sum(transmission) - sum(joint))


def cohort_scores(core, controls):
    healthy = load(core / 'healthy.jsonl')
    rate_ref = float(np.median([r['pop_rate'] for r in healthy]))
    spike_ref = float(np.median([r['n_total_spikes'] for r in healthy]))
    cohorts = {p.stem: load(p) for p in sorted(core.glob('*.jsonl')) if p.stem != 'healthy'}
    cohorts.update({p.stem: load(p) for p in sorted(controls.glob('*.jsonl'))
                    if p.stem.startswith(('HUB_', 'EIm_', 'INHrand_'))})
    main = [name for name in cohorts if name.startswith('F')]
    exclusions = {
        'all_faults_controls': set(),
        'excluding_HUB_inh': {'HUB_inh'},
        'excluding_all_targeted_hub_cohorts': {n for n in cohorts if n.startswith(('F4_', 'HUB_', 'EIm_'))},
        'main_F1_F2_F3_F5_only': set(cohorts) - {n for n in main if not n.startswith('F4_')},
    }
    output = dict(healthy_reference=dict(rate_hz=rate_ref, spikes=spike_ref),
                  healthy_resubstitution=score(healthy, rate_ref, spike_ref),
                  cohorts={n: score(rows, rate_ref, spike_ref) for n, rows in cohorts.items()},
                  exclusions={})
    for label, exclude in exclusions.items():
        names = sorted(set(cohorts) - exclude)
        rows = [r for n in names for r in cohorts[n]]
        output['exclusions'][label] = dict(conditions=names, **score(rows, rate_ref, spike_ref))
    return output


def independent_median_effect(fault, healthy, field, repetitions=20000):
    """Resample independent trials in both groups; no nonexistent seed pairing."""
    rng = np.random.default_rng(0)
    a = np.asarray([r[field] for r in fault], dtype=float)
    b = np.asarray([r[field] for r in healthy], dtype=float)
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError('effect requires complete finite observations')
    am = np.median(rng.choice(a, size=(repetitions, len(a))), axis=1)
    bm = np.median(rng.choice(b, size=(repetitions, len(b))), axis=1)
    return dict(ratio=float(np.median(a) / np.median(b)),
                ratio_ci95=np.percentile(am / bm, [2.5, 97.5]).tolist(),
                difference=float(np.median(a) - np.median(b)),
                difference_ci95=np.percentile(am - bm, [2.5, 97.5]).tolist())


def exact_cluster_summary(rows):
    groups = {seed: [r['ratio'] for r in rows if r['seed'] == seed]
              for seed in sorted({r['seed'] for r in rows})}
    draws = [float(np.median([v for s in sample for v in groups[s]]))
             for sample in itertools.product(groups, repeat=len(groups))]
    return dict(seed_medians={str(s): float(np.median(v)) for s, v in groups.items()},
                ordered_resamples=len(draws), distinct_statistics=len(set(draws)),
                exact_percentile_range=np.percentile(draws, [2.5, 97.5]).tolist())


def window_sensitivity(vision, windows=(200, 300, 400, 500)):
    healthy = { (float(r['phi_t_deg']), int(r['seed'])): r
               for p in sorted((vision / 'episodes_v4').glob('brain_healthy_phi*.json'))
               for r in [json.loads(p.read_text())] }
    output = {}
    for tag, fault in [('v4', 'F2_25'), ('v4', 'F2_50'), ('v4', 'F4_1pct'), ('v4c', 'HUB_inh')]:
        episodes = [json.loads(p.read_text()) for p in sorted(
            (vision / f'episodes_{tag}').glob(f'brain_{fault}_phi*.json'))]
        output[fault] = {}
        for window in windows:
            pairs = []
            for e in episodes:
                key = (float(e['phi_t_deg']), int(e['seed']))
                h = healthy[key]
                denominator = exposure(h, window)['spikes']
                if not denominator:
                    raise ValueError(f'zero healthy activity at {window} ms')
                pairs.append(dict(phi=key[0], seed=key[1],
                                  ratio=exposure(e, window)['spikes'] / denominator))
            output[fault][str(window)] = dict(n=len(pairs), pairs=pairs,
                median=float(np.median([p['ratio'] for p in pairs])),
                exceedances=sum(p['ratio'] > 2 for p in pairs),
                **exact_cluster_summary(pairs))
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError(f'choose a new output directory: {args.out}')
    core = ROOT / 'sim/results/real'
    vision = ROOT / 'sim_vision/results_vision'
    healthy = load(core / 'healthy.jsonl')
    result = dict(cohort_scores=cohort_scores(core, vision / 'openloop_controls'),
                  windows=window_sensitivity(vision), effects={})
    for dose in (5, 10, 25, 50):
        name = f'F2_drop_{dose:02}'
        rows = load(core / f'{name}.jsonl')
        result['effects'][name] = {field: independent_median_effect(rows, healthy, field)
                                  for field in ('pop_rate', 'latency_ms')}
    result['legacy_partitions'] = analyze(vision)['healthy_splits']
    sources = sorted(set(list(core.glob('*.jsonl')) +
        list((vision / 'openloop_controls').glob('*.jsonl')) +
        list(vision.glob('episodes_*/*.json')) + [vision / 'calib.json']))
    result['manifest'] = dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        numpy=np.__version__, exploratory=True, simulations_executed=False,
        note='Windows and exclusions are post-hoc sensitivity analyses; healthy resubstitution is not held-out specificity.')
    args.out.mkdir(parents=True)
    (args.out / 'assessment.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['cohort_scores'], indent=2))
    print('F2_50 effects:', json.dumps(result['effects']['F2_drop_50']))
    print('Windows:', json.dumps({f:{w:dict(median=q['median'], exceedances=q['exceedances'], seed_medians=q['seed_medians'])
                                      for w,q in windows.items()} for f,windows in result['windows'].items()}))


if __name__ == '__main__':
    main()
