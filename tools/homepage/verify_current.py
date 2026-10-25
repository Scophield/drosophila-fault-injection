"""Bind reused animations and homepage numbers to the current fixed science.

Reads saved records only. No neural simulation, fitting, resampling or data edits.
An existing --out file is rejected.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import json
import statistics
import subprocess
import sys

COMMIT = '22999d28d8fe22f863fc8f62eaa45a57256083d0'
ROOT = Path(__file__).resolve().parents[2]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-root', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    if args.out and args.out.exists():
        raise FileExistsError(args.out)
    science = args.data_root.resolve()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=science, text=True).strip()
    assert commit == COMMIT, (commit, COMMIT)
    scope = read(science/'PUBLIC_SCOPE.json')
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(science/'tools'), str(science/'sim_vision')]
    from task_metrics_v9 import bind_count_cutoff, command_count, command_alert
    from analyze_burst_end import reconstruct
    examples = read(ROOT/'docs/homepage-animation/examples.json')
    legacy_summary = read(ROOT/'docs/homepage-animation/summary.json')
    for name, h in legacy_summary['input_sha256'].items():
        assert sha(science/name) == h, name
    media = ROOT/'media/paper-v10.1'
    manifest = read(media/'render-manifest.json')
    for name, item in manifest['files'].items():
        assert sha(media/name) == item['sha256'], name
    for name, h in examples['replay_code_sha256'].items():
        assert sha(science/name) == h, name
    index = list(csv.DictReader((science/'output/trigger-timing-20261025-03/all-records.csv').open(encoding='utf-8')))
    records = {}
    for row in index:
        name = row['source']
        assert sha(science/name) == row['source_sha256'] == scope['files'][name]['sha256']
        r = read(science/name)
        reconstruct(r)
        key = row['RF'], r['seed'], r['phi_deg'], r['mode'], r['fault']
        assert key not in records
        records[key] = r
    assert len(records) == 576
    clusters = {rf: len({k[1] for k in records if k[0] == rf}) for rf in ['RF-0', 'RF-A', 'RF-B']}
    assert list(clusters.values()) == [24, 12, 12]
    delays, pairs, discordant = {}, 0, 0
    for rf in clusters:
        healthy = [k for k in records if k[0] == rf and k[3:] == ('proportional', 'healthy')]
        ds = [records[k[:4]+('F2_50',)]['trigger_ms']-records[k]['trigger_ms'] for k in healthy]
        delays[rf] = dict(mean_ms=statistics.mean(ds), sd_ms=statistics.stdev(ds), bearing_pairs=len(ds), independent_seed_clusters=clusters[rf])
    assert [d['mean_ms'] for d in delays.values()] == [80., 57.5, 57.5]
    for k, p in records.items():
        if k[3] != 'proportional':
            continue
        r = records[k[:3]+('relay', k[4])]
        for field in ['mask_sha256', 'uniform_sha256', 'input_map_sha256', 'calibration_sha256', 'trigger_ms', 'burst_delay_ms', 'burst_duration_ms']:
            assert p[field] == r[field], (k, field)
        pairs += 1
        discordant += p['escaped'] != r['escaped']
    assert (pairs, discordant) == (288, 15)
    horizons = {}
    expected = {'RF-0': [(46, 37), (48, 48)], 'RF-A': [(23, 22), (23, 23)], 'RF-B': [(24, 23), (24, 24)]}
    for rf in clusters:
        horizons[rf] = {}
        for law, wanted in zip(['proportional', 'relay'], expected[rf]):
            rows = [r for k, r in records.items() if k[0] == rf and k[3:] == (law, 'F2_50')]
            counts = [sum(r['collision_ms'] is None or r['collision_ms'] > h for r in rows) for h in [900, 1000]]
            assert tuple(counts) == wanted
            horizons[rf][law] = dict(deletion_fraction=.5, n=len(rows), at_900_ms=counts[0], at_1000_ms=counts[1])
    warning = read(science/'output/warning-counts-v10_1-02/results.json')
    regpaths = {'RF-0': 'runs/task-v9-frozen/registration-core.json', 'RF-A': 'runs/task-v10-transfer/map-A/registration.json', 'RF-B': 'runs/task-v10-transfer/map-B/registration.json'}
    scores = {}
    for rf in clusters:
        reg = read(science/regpaths[rf])
        validation = [read(science/n) for n in reg['validation_input_sha256']]
        cutoff = bind_count_cutoff(reg['thresholds'], validation)['command_count_cutoff']
        c = Counter(dict(tp=0, fp=0, tn=0, fn=0))
        for k, r in records.items():
            if k[0] != rf:
                continue
            flag = command_alert(command_count(r), cutoff)
            hit = not r['escaped']
            c['tp' if flag and hit else 'fp' if flag else 'fn' if hit else 'tn'] += 1
        assert all(c[n] == warning['maps'][rf]['warning_scores']['transmission']['all'][n] for n in c)
        scores[rf] = dict(c)
    selected = []
    for item in examples['exports']:
        assert sha(science/item['source']) == item['source_sha256']
        exported = read(ROOT/'docs/homepage-animation'/item['replay_file'])
        assert sha(ROOT/'docs/homepage-animation'/item['replay_file']) == item['replay_sha256']
        raw = read(science/item['source'])
        assert raw['trigger_ms'] == item['trigger_ms'] == exported['trigger_ms']
        assert raw['collision_ms'] == item['contact_ms'] == exported['contact_ms']
        assert exported['B_ms'] == raw['trigger_ms']+raw['burst_delay_ms']+raw['burst_duration_ms']
        selected.append(dict(id=item['id'], source=item['source'], sha256=item['source_sha256'], trigger_ms=raw['trigger_ms'], contact_ms=raw['collision_ms']))
    result = dict(passed=True, scientific_commit=commit, media_generation_commit=examples['source_commit'], media_bytes_unchanged=True,
                  raw_records=576, independently_reconstructed_records=576, independent_seed_clusters=clusters,
                  mean_trigger_delays=delays, P_R_pairs=pairs, P_R_discordant=discordant, horizon_counts=horizons,
                  canonical_count_warning_confusion=scores, selected_sources=selected,
                  public_pdf_sha256=scope['candidate_pdf_sha256'], new_neural_simulation=False,
                  new_threshold_fitting=False, new_confirmatory_test=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
