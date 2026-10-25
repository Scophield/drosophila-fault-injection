"""Summarize a completed fixed four-arm checker evaluation without new scoring.

The input cases, expected validity and arms are already frozen. This entry only
validates and aggregates their saved outcomes/costs. Technical repeats never
enlarge efficacy denominators. No confidence interval or hypothesis test is run.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import csv
import hashlib
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
ARMS = ('A', 'B', 'C', 'D')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0]) if rows else ['none']
    with path.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, separators=(',', ':'))
                             if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})


def distribution(values):
    values = [value for value in values if value is not None]
    if not values:
        return dict(n=0, total=None, median=None, minimum=None, maximum=None)
    return dict(n=len(values), total=sum(values), median=statistics.median(values),
                minimum=min(values), maximum=max(values))


def confusion(rows):
    applicable = [row for row in rows if row['applicable']]
    return dict(cases=len(applicable), invalid=sum(row['expected_invalid'] for row in applicable),
                valid=sum(not row['expected_invalid'] for row in applicable),
                tp=sum(row['expected_invalid'] and row['detected'] for row in applicable),
                fn=sum(row['expected_invalid'] and not row['detected'] for row in applicable),
                fp=sum(not row['expected_invalid'] and row['detected'] for row in applicable),
                tn=sum(not row['expected_invalid'] and not row['detected'] for row in applicable))


def costs(rows):
    return dict(cases=len(rows),
                wall_seconds=distribution([row['wall_seconds'] for row in rows]),
                process_cpu_seconds=distribution([row['process_cpu_seconds'] for row in rows]),
                start_rss_bytes=distribution([row['start_rss_bytes'] for row in rows]),
                sampled_peak_rss_bytes=distribution([row['sampled_peak_rss_bytes'] for row in rows]))


def overlap(case_ids, cases, table):
    ids = {case_id for case_id in case_ids
           if cases[case_id]['applicable'] and cases[case_id]['expected_invalid']}
    detections = {arm: {case_id for case_id in ids if table[case_id, arm, 0]['detected']}
                  for arm in ARMS}
    a, b, c, d = [detections[arm] for arm in ARMS]
    result = dict(invalid_cases=len(ids), baseline_detected=len(a),
                  common_detected_including_baseline=len(b),
                  native_detected_including_baseline=len(c), full_detected=len(d),
                  common_above_baseline=len(b-a), native_above_baseline=len(c-a),
                  full_above_baseline=len(d-a),
                  common_native_overlap_above_baseline=len((b & c)-a),
                  common_only_beyond_native=len(b-c), native_only_beyond_common=len(c-b),
                  missed_by_full=len(ids-d))
    result['case_ids'] = dict(baseline_detected=sorted(a), common_above_baseline=sorted(b-a),
                             native_above_baseline=sorted(c-a), full_above_baseline=sorted(d-a),
                             overlap_above_baseline=sorted((b & c)-a),
                             common_only=sorted(b-c), native_only=sorted(c-b),
                             full_missed=sorted(ids-d))
    return result


def first_layer(case_id, table):
    observed = {arm: table[case_id, arm, 0]['detected'] for arm in ARMS}
    if observed['A']:
        return 'baseline'
    if observed['B'] and observed['C']:
        return 'common-and-native'
    if observed['B']:
        return 'common-only'
    if observed['C']:
        return 'native-only'
    return 'undetected'


def md_table(headers, rows):
    return ('| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'
            + ''.join('| '+' | '.join(str(value) for value in row)+' |\n' for row in rows))


def fmt(value, digits=4):
    return 'NA' if value is None else f'{value:.{digits}f}'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan', required=True, type=Path,
                    help='Frozen plan directory, or its frozen-plan.json file')
    ap.add_argument('--results', required=True, type=Path,
                    help='Completed evaluation directory containing rows.jsonl/results.json')
    ap.add_argument('--out', required=True, type=Path, help='New output directory; never overwritten')
    args = ap.parse_args()
    plan_path = args.plan/'frozen-plan.json' if args.plan.is_dir() else args.plan
    plan = read(plan_path); run = read(args.results/'run.json')
    completed = read(args.results/'results.json')
    if args.out.exists():
        raise FileExistsError(args.out)
    assert completed['completed'], 'Evaluation must be complete before summarizing'
    plan_hash = sha(plan_path)
    assert run['plan_sha256'] == completed['plan_sha256'] == plan_hash
    assert sha(plan_path.parent/'fixtures.json.gz') == plan['fixtures_sha256']
    assert plan['case_count'] == len(plan['cases']) == 111
    assert plan['technical_repeats'] == 3
    repeat_ids = plan['technical_repeat_case_ids']
    assert len(repeat_ids) == len(set(repeat_ids)) == 6
    cases = {case['id']: case for case in plan['cases']}
    assert len(cases) == 111
    assert Counter(cases[case_id]['plant'] for case_id in repeat_ids) == {'fly': 3, 'tank': 3}
    rows = [json.loads(line) for line in (args.results/'rows.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows) == 516, f'Expected 516 primary/technical rows, got {len(rows)}'
    table = {}
    for row in rows:
        key = row['id'], row['arm'], row['repeat']
        assert key not in table, ('Duplicate execution row', key)
        assert row['id'] in cases and row['arm'] in ARMS
        case = cases[row['id']]
        for field in ['plant', 'adapter_key', 'family', 'expected_invalid', 'applicable', 'input_sha256']:
            assert row[field] == case[field], (key, field)
        assert isinstance(row['detected'], bool)
        assert row['wall_seconds'] >= 0 and row['process_cpu_seconds'] >= 0
        assert row['repeat'] in ([0, 1, 2, 3] if row['id'] in repeat_ids else [0])
        assert row['detected'] == bool(row['parse_findings'] or row['baseline_findings'] or row['layer_findings'])
        table[key] = row
    expected_keys = {(case_id, arm, repeat) for case_id in cases for arm in ARMS
                     for repeat in ([0, 1, 2, 3] if case_id in repeat_ids else [0])}
    assert set(table) == expected_keys, 'Missing or unexpected case/arm/repeat'
    primary = [row for row in rows if row['repeat'] == 0]
    technical = [row for row in rows if row['repeat'] > 0]
    assert len(primary) == 444 and len(technical) == 72
    for case_id in cases:
        for repeat in ([0, 1, 2, 3] if case_id in repeat_ids else [0]):
            arm_rows = {arm: table[case_id, arm, repeat] for arm in ARMS}
            assert arm_rows['D']['detected'] == (arm_rows['B']['detected'] or arm_rows['C']['detected'])
            assert not arm_rows['A']['detected'] or all(arm_rows[a]['detected'] for a in ARMS)
            assert len({json.dumps(row['parse_findings']) for row in arm_rows.values()}) == 1
            assert len({json.dumps(row['baseline_findings']) for row in arm_rows.values()}) == 1

    # Deduplicate only by the frozen raw/spec/adapter payload, never by outcome.
    unique_groups = defaultdict(list)
    for case in plan['cases']:
        if case['applicable']:
            unique_groups[case['input_sha256']].append(case['id'])
    assert len(unique_groups) == plan['unique_applicable_inputs'] == 107
    representatives = []
    for ids in unique_groups.values():
        representative = ids[0]  # deterministic first manifest occurrence
        representatives.append(representative)
        assert len({cases[case_id]['expected_invalid'] for case_id in ids}) == 1
        assert len({cases[case_id]['plant'] for case_id in ids}) == 1
        for arm in ARMS:
            assert len({table[case_id, arm, 0]['detected'] for case_id in ids}) == 1, ('Identical input yielded different decisions', ids, arm)

    counts, unique_counts, intersections, cost_summary, valid_costs = {}, {}, {}, {}, {}
    paired_costs = {}; count_csv = []; cost_csv = []
    for plant in ['fly', 'tank', 'all']:
        ids = [case_id for case_id, case in cases.items() if plant == 'all' or case['plant'] == plant]
        unique_ids = [case_id for case_id in representatives if case_id in ids]
        counts[plant] = {}; unique_counts[plant] = {}; cost_summary[plant] = {}; valid_costs[plant] = {}; paired_costs[plant] = {}
        intersections[plant] = dict(designed_cases=overlap(ids, cases, table), unique_inputs=overlap(unique_ids, cases, table))
        for arm in ARMS:
            selected = [table[case_id, arm, 0] for case_id in ids if cases[case_id]['applicable']]
            unique = [table[case_id, arm, 0] for case_id in unique_ids]
            counts[plant][arm] = confusion(selected)
            unique_counts[plant][arm] = confusion(unique)
            cost_summary[plant][arm] = costs(selected)
            valid_costs[plant][arm] = costs([row for row in selected if not row['expected_invalid']])
            for label, item in [('designed_cases', counts[plant][arm]), ('unique_inputs', unique_counts[plant][arm])]:
                count_csv.append(dict(plant=plant, arm=arm, unit=label, **item))
            for label, item in [('all_applicable', cost_summary[plant][arm]), ('valid_controls', valid_costs[plant][arm])]:
                cost_csv.append(dict(plant=plant, arm=arm, subset=label, cases=item['cases'],
                                     wall_total_seconds=item['wall_seconds']['total'], wall_median_seconds=item['wall_seconds']['median'],
                                     cpu_total_seconds=item['process_cpu_seconds']['total'], cpu_median_seconds=item['process_cpu_seconds']['median'],
                                     start_rss_median_bytes=item['start_rss_bytes']['median'], sampled_peak_rss_max_bytes=item['sampled_peak_rss_bytes']['maximum']))
            # Independently check the runner's already-saved efficacy summary.
            assert all(counts[plant][arm][k] == completed['summary'][plant][arm][k] for k in counts[plant][arm])
        for high, low in [('B', 'A'), ('C', 'A'), ('D', 'B'), ('D', 'C')]:
            for subset in ['all_applicable', 'valid_controls']:
                selected_ids = [case_id for case_id in ids if cases[case_id]['applicable'] and (subset == 'all_applicable' or not cases[case_id]['expected_invalid'])]
                paired_costs[plant][high+'-'+low+':'+subset] = dict(
                    cases=len(selected_ids),
                    wall_seconds=distribution([table[case_id, high, 0]['wall_seconds']-table[case_id, low, 0]['wall_seconds'] for case_id in selected_ids]),
                    process_cpu_seconds=distribution([table[case_id, high, 0]['process_cpu_seconds']-table[case_id, low, 0]['process_cpu_seconds'] for case_id in selected_ids]))

    family_rows = []; case_rows = []; misses = []; false_positives = []
    for plant in ['fly', 'tank']:
        for family in dict.fromkeys(case['family'] for case in plan['cases'] if case['plant'] == plant):
            ids = [case_id for case_id, case in cases.items() if case['plant'] == plant and case['family'] == family]
            applicable_ids = [case_id for case_id in ids if cases[case_id]['applicable']]
            item = dict(plant=plant, family=family, designed_cases=len(ids), applicable=len(applicable_ids),
                        unique_inputs=len({cases[case_id]['input_sha256'] for case_id in applicable_ids}),
                        invalid=sum(cases[case_id]['expected_invalid'] for case_id in applicable_ids),
                        valid=sum(not cases[case_id]['expected_invalid'] for case_id in applicable_ids))
            for arm in ARMS:
                c = confusion([table[case_id, arm, 0] for case_id in applicable_ids])
                item.update({arm+'_'+key: c[key] for key in ['tp', 'fn', 'fp', 'tn']})
            family_rows.append(item)
    for case_id, case in cases.items():
        item = {field: case[field] for field in ['id', 'plant', 'adapter_key', 'family', 'expected_invalid', 'applicable', 'input_sha256']}
        item.update(raw_records=case['records'], first_detection=first_layer(case_id, table),
                    original_target_key=case['original_target_key'], mutation=case['mutation'])
        for arm in ARMS:
            row = table[case_id, arm, 0]
            item[arm+'_detected'] = row['detected']
            detail = dict(id=case_id, plant=case['plant'], adapter_key=case['adapter_key'], family=case['family'], arm=arm,
                          input_sha256=case['input_sha256'], target=case['original_target_key'], mutation=case['mutation'],
                          findings=row['parse_findings']+row['baseline_findings']+row['layer_findings'])
            if case['applicable'] and case['expected_invalid'] and not row['detected']:
                misses.append(detail)
            if case['applicable'] and not case['expected_invalid'] and row['detected']:
                false_positives.append(detail)
        case_rows.append(item)

    repeat_rows = []
    for case_id in repeat_ids:
        for arm in ARMS:
            observed = [table[case_id, arm, repeat] for repeat in [1, 2, 3]]
            initial = table[case_id, arm, 0]
            item = dict(id=case_id, plant=cases[case_id]['plant'], arm=arm,
                        technical_repetitions=3, primary_wall_seconds=initial['wall_seconds'],
                        wall_seconds=[row['wall_seconds'] for row in observed],
                        cpu_seconds=[row['process_cpu_seconds'] for row in observed],
                        wall_median_seconds=statistics.median(row['wall_seconds'] for row in observed),
                        wall_min_seconds=min(row['wall_seconds'] for row in observed),
                        wall_max_seconds=max(row['wall_seconds'] for row in observed),
                        cpu_median_seconds=statistics.median(row['process_cpu_seconds'] for row in observed),
                        decisions_equal_primary=all(row['detected'] == initial['detected'] for row in observed))
            assert item['decisions_equal_primary']
            repeat_rows.append(item)

    result = dict(completed=True, plan_sha256=plan_hash, plan_case_count=111, primary_rows=444,
                  technical_rows=72, total_execution_rows=516, unique_applicable_inputs=107,
                  designed_validity_counts=dict(invalid=sum(case['expected_invalid'] and case['applicable'] for case in cases.values()),
                                               valid=sum(not case['expected_invalid'] and case['applicable'] for case in cases.values()),
                                               inapplicable=sum(not case['applicable'] for case in cases.values())),
                  primary_confusion=counts, unique_input_confusion=unique_counts,
                  overlap_and_increment=intersections, primary_costs=cost_summary, valid_control_costs=valid_costs,
                  paired_incremental_costs=paired_costs, technical_repeats=repeat_rows,
                  family_matrix=family_rows, all_primary_misses=misses, all_primary_false_positives=false_positives,
                  duplicate_input_groups=[dict(input_sha256=h,case_ids=ids) for h,ids in unique_groups.items() if len(ids)>1],
                  initialization_registry_seconds=plan.get('initialization_registry_seconds'),
                  complete_preparation_seconds=plan.get('complete_preparation_seconds'), run_setup_seconds=run.get('setup_seconds'),
                  evaluation_elapsed_seconds=completed['elapsed_seconds'],
                  input_sha256={name:sha(args.results/name) for name in ['run.json','rows.jsonl','results.json']},
                  summarizer_sha256=sha(Path(__file__)),
                  scope='Designed additional cases; no blind coverage, population detection rate, CI, hypothesis test, or new neural samples',
                  memory_scope='5-ms sampled absolute self-process working set, including retained fixtures; not per-case allocation, independent worker peak, energy or hardware cost')

    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out/'summary.json', result)
    write_csv(args.out/'confusion.csv', count_csv)
    write_csv(args.out/'costs.csv', cost_csv)
    write_csv(args.out/'family-matrix.csv', family_rows)
    write_csv(args.out/'case-matrix.csv', case_rows)
    detail_fields = ['id','plant','adapter_key','family','arm','input_sha256','target','mutation','findings']
    write_csv(args.out/'all-misses.csv', misses, detail_fields)
    write_csv(args.out/'all-false-positives.csv', false_positives, detail_fields)
    write_csv(args.out/'technical-repeats.csv', repeat_rows)

    text = '# Fixed additional four-arm checker evaluation\n\n'
    text += (f'The frozen catalogue has {result["plan_case_count"]} designed case IDs '
             f'({result["designed_validity_counts"]["invalid"]} known corruptions and '
             f'{result["designed_validity_counts"]["valid"]} valid controls), '
             f'{result["unique_applicable_inputs"]} unique applicable raw/spec inputs. '
             'All 444 primary and 72 technical execution rows are complete. '
             'Six preselected source cases have three extra technical runs per arm; '
             'these runs do not add efficacy samples.\n\n')
    text += 'A is the trusted header-registry baseline; B adds the complete Common audit; C adds native record/pair replay; D combines all obligations. This is an author-designed fixed additional evaluation, not blind generalization or a comparison with unexecuted external tools.\n\n'
    for label, source in [('Designed case counts',counts),('Unique raw/spec input counts',unique_counts)]:
        text += '## '+label+'\n\n'
        text += md_table(['Plant','Arm','Invalid','Valid','Detected invalid','Missed invalid','False alarms','Accepted valid'],
                         [[plant,arm]+[source[plant][arm][key] for key in ['invalid','valid','tp','fn','fp','tn']]
                          for plant in ['fly','tank','all'] for arm in ARMS])+'\n'
    text += '## Nonredundant information above A\n\n'
    text += md_table(['Plant','Unit','B−A','C−A','D−A','B-only','C-only','B/C overlap above A','Full misses'],
                     [[plant,unit]+[intersections[plant][unit][key] for key in ['common_above_baseline','native_above_baseline','full_above_baseline','common_only_beyond_native','native_only_beyond_common','common_native_overlap_above_baseline','missed_by_full']]
                      for plant in ['fly','tank','all'] for unit in ['designed_cases','unique_inputs']])+'\n'
    text += 'Counts describe this fixed catalogue only. B/C overlap includes neither duplicate input IDs nor baseline findings when labelled “above A.” The measured Full decision equals B-or-C for every completed execution.\n\n'
    text += '## Primary costs\n\n'
    text += md_table(['Plant','Arm','Cases','Wall total (s)','Wall median (s)','CPU total (s)','CPU median (s)','Sampled RSS max (MiB)'],
                     [[plant,arm,cost_summary[plant][arm]['cases'],fmt(cost_summary[plant][arm]['wall_seconds']['total']),fmt(cost_summary[plant][arm]['wall_seconds']['median']),fmt(cost_summary[plant][arm]['process_cpu_seconds']['total']),fmt(cost_summary[plant][arm]['process_cpu_seconds']['median']),fmt(None if cost_summary[plant][arm]['sampled_peak_rss_bytes']['maximum'] is None else cost_summary[plant][arm]['sampled_peak_rss_bytes']['maximum']/2**20,1)]
                      for plant in ['fly','tank','all'] for arm in ARMS])+'\n'
    text += '### Valid controls only\n\n'
    text += md_table(['Plant','Arm','Valid cases','Wall median (s)','CPU total (s)','Starting RSS median (MiB)','Sampled RSS max (MiB)'],
                     [[plant,arm,valid_costs[plant][arm]['cases'],fmt(valid_costs[plant][arm]['wall_seconds']['median']),fmt(valid_costs[plant][arm]['process_cpu_seconds']['total']),fmt(None if valid_costs[plant][arm]['start_rss_bytes']['median'] is None else valid_costs[plant][arm]['start_rss_bytes']['median']/2**20,1),fmt(None if valid_costs[plant][arm]['sampled_peak_rss_bytes']['maximum'] is None else valid_costs[plant][arm]['sampled_peak_rss_bytes']['maximum']/2**20,1)]
                      for plant in ['fly','tank','all'] for arm in ARMS])+'\n'
    text += (f'Frozen-plan initialization/registry: {fmt(result["initialization_registry_seconds"])} s; '
             f'complete preparation: {fmt(result["complete_preparation_seconds"])} s; '
             f'run initialization: {fmt(result["run_setup_seconds"])} s. '
             'These are separate from per-case costs. RSS is 5-ms sampled absolute process memory, '
             'including retained fixtures, not per-case allocation or an independent worker peak. '
             'Short peaks may be missed; coarse CPU clock resolution can yield zero for fast checks. '
             'Paired cost differences and three-run technical ranges are in summary.json and technical-repeats.csv; '
             'they are not confidence intervals.\n\n')
    text += '## Family-level decisions\n\n'
    text += md_table(['Plant','Family','Invalid/valid','A TP/FN/FP','B TP/FN/FP','C TP/FN/FP','D TP/FN/FP'],
                     [[row['plant'],row['family'],f'{row["invalid"]}/{row["valid"]}']+
                      [f'{row[arm+"_tp"]}/{row[arm+"_fn"]}/{row[arm+"_fp"]}' for arm in ARMS]
                      for row in family_rows])+'\n'
    full_misses = [row for row in misses if row['arm']=='D']
    text += f'Full misses: {len(full_misses)}. All primary false alarms across arms: {len(false_positives)}. '
    text += 'Every arm-specific miss/false alarm and its mutation/source context is retained in all-misses.csv / all-false-positives.csv, not removed from the denominator.\n\n'
    if full_misses:
        text += md_table(['Full-missed case','Plant','Family'],[[row['id'],row['plant'],row['family']] for row in full_misses])+'\n'
    text += 'Validity is a frozen source-corruption oracle, not a label chosen from checker output. The trusted registry is a prerequisite; consistent unlogged neural fabrication remains outside trace authentication. Original development challenges, genuine V8 errors, and these additional fixtures are separate evidence sets. No new neural simulation, population claim, or hypothetical collision effect is inferred here.\n'
    with (args.out/'REPORT.md').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(text)
    print(json.dumps(dict(passed=True, primary_rows=444, technical_rows=72,
                          unique_applicable_inputs=107, all_case_confusion=counts['all'],
                          all_unique_confusion=unique_counts['all'],
                          output=str(args.out)), indent=2))


if __name__ == '__main__':
    main()
