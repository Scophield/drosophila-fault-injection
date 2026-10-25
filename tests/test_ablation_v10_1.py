"""Traceability and accounting regressions for the saved engineering evaluation.

These tests do not regenerate challenges, rerun the 516 measurements or execute
neural dynamics. Small tank examples exercise the unchanged checker boundary;
the remaining checks independently reconcile frozen inputs and saved outputs.
"""
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = '22999d28d8fe22f863fc8f62eaa45a57256083d0'
EXP = ROOT/'experiments/checker-ablation-v10_1'
ARMS = ('A', 'B', 'C', 'D')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value):
    data = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def csv_rows(path):
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def boolean(text):
    if text == '':
        return None
    if text not in ('True', 'False'):
        raise ValueError(text)
    return text == 'True'


class SavedAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan_path = EXP/'frozen-02/frozen-plan.json'
        cls.plan = read(cls.plan_path)
        cls.cases = json.loads(gzip.decompress((EXP/'frozen-02/fixtures.json.gz').read_bytes()))
        cls.by_id = {case['id']: case for case in cls.cases}
        cls.rows = [json.loads(line) for line in (EXP/'evaluation-01/rows.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        cls.primary = [row for row in cls.rows if row['repeat'] == 0]
        cls.table = {(row['id'], row['arm']): row for row in cls.primary}
        cls.summary = read(EXP/'summary-01/summary.json')

    def test_preexecution_hash_chain_and_frozen_checker_match_base(self):
        self.assertEqual(self.plan['base_commit'], BASE)
        plan_hash = sha(self.plan_path)
        self.assertEqual(read(EXP/'evaluation-01/run.json')['plan_sha256'], plan_hash)
        self.assertEqual(read(EXP/'evaluation-01/results.json')['plan_sha256'], plan_hash)
        self.assertEqual(self.summary['plan_sha256'], plan_hash)
        self.assertEqual(sha(EXP/'frozen-02/fixtures.json.gz'), self.plan['fixtures_sha256'])
        for name, expected in self.plan['source_sha256'].items():
            with self.subTest(source=name):
                self.assertEqual(sha(ROOT/name), expected)
        for name, expected in self.plan['frozen_checker_sha256'].items():
            with self.subTest(checker=name):
                baseline_bytes = subprocess.check_output(['git', 'show', BASE+':'+name], cwd=ROOT)
                self.assertEqual(hashlib.sha256(baseline_bytes).hexdigest(), expected)
                self.assertEqual(sha(ROOT/name), expected)
        for name, expected in self.summary['input_sha256'].items():
            self.assertEqual(sha(EXP/'evaluation-01'/name), expected)

    def test_fixture_oracles_and_input_deduplication(self):
        self.assertEqual(len(self.cases), self.plan['case_count'])
        self.assertEqual(len(self.by_id), len(self.cases))
        self.assertEqual(len(self.cases), read(EXP/'challenge-spec.json')['expected_case_counts']['total'])
        self.assertEqual(Counter(c['expected_invalid'] for c in self.cases), {True: 87, False: 24})
        index = {entry['id']: entry for entry in self.plan['cases']}
        same_input = defaultdict(list)
        for case in self.cases:
            entry = index[case['id']]
            self.assertTrue(case['applicable'])
            self.assertEqual(canonical_digest(case), entry['fixture_sha256'])
            input_hash = canonical_digest({key: case[key] for key in ('adapter_key', 'spec', 'records')})
            self.assertEqual(input_hash, entry['input_sha256'])
            self.assertEqual(case['expected_invalid'], entry['expected_invalid'])
            same_input[input_hash].append(case)
        self.assertEqual(len(same_input), self.plan['unique_applicable_inputs'])
        self.assertEqual(len(same_input), self.summary['unique_applicable_inputs'])
        self.assertEqual(len(same_input), 107)
        for grouped in same_input.values():
            self.assertEqual(len({case['expected_invalid'] for case in grouped}), 1)
            for arm in ARMS:
                self.assertEqual(len({self.table[case['id'], arm]['detected'] for case in grouped}), 1)

    def test_worker_controls_retain_two_true_blocks_and_unchanged_negative_inputs(self):
        for case in self.cases:
            if case['expected_invalid']:
                continue
            with self.subTest(case=case['id']):
                self.assertEqual(canonical_digest(case['records']), case['source_group_digest'])
                self.assertTrue(all(not self.table[case['id'], arm]['detected'] for arm in ARMS))
                if case['family'] == 'legal_worker_seed_partition':
                    self.assertEqual(len(case['records']), 24)
                    self.assertEqual(len(case['spec']['clusters']), 2)
                    self.assertEqual(Counter(r['seed'] for r in case['records']),
                                     {seed: 12 for seed in case['spec']['clusters']})
                    if case['plant'] == 'fly':
                        workers = [{r['run_manifest_sha256'] for r in case['records'] if r['seed'] == seed}
                                   for seed in case['spec']['clusters']]
                        self.assertTrue(all(workers))
                        self.assertTrue(workers[0].isdisjoint(workers[1]))
                    else:
                        self.assertIn('no worker manifests', case['worker_evidence'])
                else:
                    self.assertEqual(len(case['records']), 12)

    def test_all_original_neural_and_tank_input_bytes_remain_bound(self):
        sources = self.plan['input_sha256']
        self.assertEqual(len(sources), 672)
        expected = {'runs/task-v9-test/episodes/': 288,
                    'runs/task-v10-transfer/map-A/test/episodes/': 144,
                    'runs/task-v10-transfer/map-B/test/episodes/': 144,
                    'audit/v10/evidence-05/tank-raw/': 96}
        for prefix, count in expected.items():
            self.assertEqual(sum(name.startswith(prefix) for name in sources), count)
        for name, expected_hash in sources.items():
            with self.subTest(source=name):
                self.assertEqual(sha(ROOT/name), expected_hash)
        historical = read(EXP/'historical-01/input-hashes.json')['inputs']
        self.assertFalse(set(sources).intersection(historical))

    def test_every_case_and_arm_is_retained_in_the_primary_and_repeat_matrices(self):
        expected_primary = {(case['id'], arm) for case in self.cases for arm in ARMS}
        self.assertEqual(len(self.primary), len(expected_primary))
        self.assertEqual(set(self.table), expected_primary)
        self.assertEqual(len(self.primary), self.summary['primary_rows'])
        index = {entry['id']: entry for entry in self.plan['cases']}
        for row in self.primary:
            case = self.by_id[row['id']]
            self.assertEqual(row['expected_invalid'], case['expected_invalid'])
            self.assertEqual(row['input_sha256'], index[row['id']]['input_sha256'])
            self.assertEqual(row['normalized_records']+row['parse_exclusions'], len(case['records']))
            if case['family'] == 'missing_required_header':
                self.assertEqual(row['parse_exclusions'], 1)
                self.assertTrue(row['parse_findings'])
                self.assertTrue(row['detected'])
        repeated = [row for row in self.rows if row['repeat'] != 0]
        repeat_ids = self.plan['technical_repeat_case_ids']
        wanted = {(case_id, arm, repeat) for case_id in repeat_ids for arm in ARMS
                  for repeat in range(1, self.plan['technical_repeats']+1)}
        self.assertEqual(len(repeated), len(wanted))
        self.assertEqual({(r['id'], r['arm'], r['repeat']) for r in repeated}, wanted)
        self.assertEqual(len(repeated), self.summary['technical_rows'])
        self.assertEqual(len(self.rows), self.summary['total_execution_rows'])
        for row in repeated:
            original = self.table[row['id'], row['arm']]
            for key in ('detected', 'expected_invalid', 'input_sha256', 'normalized_records', 'parse_exclusions'):
                self.assertEqual(row[key], original[key])
            self.assertEqual(self.by_id[row['id']]['family'], 'unaltered')

    def test_saved_confusions_are_recomputed_from_case_decisions_not_fixed_scores(self):
        for plant in ('fly', 'tank', 'all'):
            for arm in ARMS:
                selected = [r for r in self.primary if r['arm'] == arm and (plant == 'all' or r['plant'] == plant)]
                derived = Counter(('tp' if r['expected_invalid'] and r['detected'] else
                                   'fn' if r['expected_invalid'] else
                                   'fp' if r['detected'] else 'tn') for r in selected)
                saved = self.summary['primary_confusion'][plant][arm]
                self.assertEqual(saved['cases'], len(selected))
                for key in ('tp', 'fn', 'fp', 'tn'):
                    self.assertEqual(saved[key], derived[key])
                self.assertEqual(saved['invalid'], derived['tp']+derived['fn'])
                self.assertEqual(saved['valid'], derived['fp']+derived['tn'])
        for row in self.rows:
            self.assertTrue(math.isfinite(row['wall_seconds']) and row['wall_seconds'] >= 0)
            self.assertTrue(math.isfinite(row['process_cpu_seconds']) and row['process_cpu_seconds'] >= 0)
            self.assertGreaterEqual(row['sampled_peak_rss_bytes'], row['start_rss_bytes'])
        self.assertIn('not per-case allocation', self.summary['memory_scope'])

    def test_full_is_measured_union_and_all_blind_spots_remain_visible(self):
        common_only, native_only, missed = set(), set(), set()
        for case in self.cases:
            detected = {arm: self.table[case['id'], arm]['detected'] for arm in ARMS}
            self.assertEqual(detected['D'], detected['B'] or detected['C'])
            self.assertFalse(detected['A'] and not all(detected.values()))
            if case['expected_invalid']:
                if detected['B'] and not detected['C']:
                    common_only.add(case['id'])
                if detected['C'] and not detected['B']:
                    native_only.add(case['id'])
                if not detected['D']:
                    missed.add(case['id'])
        self.assertTrue(common_only)
        self.assertTrue(native_only)
        self.assertEqual({self.by_id[key]['family'] for key in missed},
                         {'declared_burst_header', 'monotone_resource_bias'})
        self.assertTrue(all(self.by_id[key]['plant'] == 'fly' for key in missed))
        miss_rows = csv_rows(EXP/'summary-01/all-misses.csv')
        self.assertEqual({row['id'] for row in miss_rows if row['arm'] == 'D'}, missed)
        self.assertEqual({row['id'] for row in miss_rows if row['arm'] == 'D'},
                         {row['id'] for row in self.summary['all_primary_misses'] if row['arm'] == 'D'})

    def test_historical_overlap_exposure_and_endpoint_counts_from_record_table(self):
        rows = csv_rows(EXP/'historical-01/all-historical-records.csv')
        result = read(EXP/'historical-01/historical-results.json')
        self.assertEqual(len(rows), 72)
        self.assertEqual(len({r['source'] for r in rows}), len(rows))
        historical_hashes = read(EXP/'historical-01/input-hashes.json')['inputs']
        delay = set()
        for r in rows:
            self.assertEqual(r['sha256'], historical_hashes[r['source']])
            self.assertEqual(sha(ROOT/r['source']), r['sha256'])
            if r['realized_onset_ms']:
                onset_difference = float(r['realized_onset_ms'])-float(r['declared_onset_ms'])
                self.assertAlmostEqual(onset_difference, float(r['onset_error_ms']))
                if onset_difference != 0:
                    delay.add(r['source'])
        duration = {r['source'] for r in rows if boolean(r['completed_with_explicit_following_off_frame'])
                    and float(r['observed_active_ms']) != float(r['declared_full_burst_ms'])}
        flags = {r['source'] for r in rows if boolean(r['horizon_was_observed'])
                 and boolean(r['recorded_horizon_flag']) != boolean(r['realized_frame_grid_flag_at_H'])}
        self.assertEqual(len(delay | duration | flags), result['unique_records_with_any_published_timing_error'])
        self.assertEqual(len(delay | duration | flags), 17)
        self.assertTrue(duration <= delay)
        self.assertTrue(flags <= delay)
        exposed = 0.
        for r in rows:
            elapsed = float(r['elapsed_record_ms'])
            if r['trigger_ms']:
                onset = float(r['trigger_ms'])+float(r['declared_delay_ms'])
                nominal = max(0., min(elapsed, onset+float(r['declared_full_burst_ms']))-onset)
            else:
                nominal = 0.
            self.assertAlmostEqual(nominal, float(r['declared_exposure_within_record_ms']))
            exposed += nominal-float(r['observed_active_ms'])
        self.assertAlmostEqual(exposed, result['timing_exposure_overstatement_total_ms'])
        self.assertAlmostEqual(exposed, 180.)
        observed = sum(boolean(r['recorded_horizon_flag']) is True for r in rows)
        realized = sum(boolean(r['horizon_was_observed']) is True and
                       boolean(r['realized_frame_grid_flag_at_H']) is True for r in rows)
        self.assertEqual((observed, realized), (13, 7))
        self.assertEqual((observed, realized), (result['recorded_active_flags'], result['actual_active_flags_at_H']))
        self.assertTrue(all(boolean(r['task_label_matches_recorded_geometry']) for r in rows))
        self.assertIn('Not identifiable', result['change_in_task_labels_under_corrected_actuation'])

    def _tank_evidence(self, family):
        from evidence_v10.contract import Campaign
        from evidence_v10.tank import TankAdapter
        case = next(c for c in self.cases if c['plant'] == 'tank' and c['family'] == family)
        adapter = TankAdapter(); s = case['spec']
        spec = Campaign(tuple(s['clusters']), tuple(s['conditions']), tuple(s['laws']), tuple(s['faults']),
                        s['horizon_s'], s['frame_s'], 'valid sensor updates')
        records = [adapter.normalize(r) for r in case['records']]
        return case, adapter, spec, records

    def test_small_tank_subset_confirms_common_only_semantic_obligations(self):
        from evidence_v10.contract import audit
        for family, code in [('task_label_contradiction', 'outcome-label'),
                             ('truncated_exposure', 'incomplete-exposure')]:
            case, adapter, spec, records = self._tank_evidence(family)
            self.assertIn(code, {issue.code for issue in audit(records, spec, None)})
            # The unchanged native checker accepts these plant histories; its
            # omissions are retained rather than patched to improve results.
            for record in records:
                adapter.check_native(record)

    def test_small_tank_subset_confirms_native_only_timing_obligation(self):
        from evidence_v10.contract import audit
        case, adapter, spec, records = self._tank_evidence('actuator_start')
        self.assertEqual(audit(records, spec, None), [])
        with self.assertRaisesRegex(ValueError, 'exact actuator delay'):
            adapter.check_native(records[case['target_record_index']])


if __name__ == '__main__':
    unittest.main()
