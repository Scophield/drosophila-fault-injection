"""Read-only descriptive audit of original V8 execution timing and generation cost.

No neural simulation, refitting, counterfactual trajectories or hypothesis tests.
Outputs are NEW files outside either input checkout. Historical V8 and current
V9/V10 costs are distinct products and are never pooled as scientific samples.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import ast
import csv
import hashlib
import json
import math
import platform
import shutil
import statistics
import subprocess


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_new(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, allow_nan=False); f.write('\n')


def csv_new(p, rows):
    with p.open('x', encoding='utf-8', newline='') as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0])); out.writeheader(); out.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--archive-root', type=Path)
    ap.add_argument('--legacy-bundle', type=Path, help='Portable folder with manifests/*.json and source/run_closedloop_v8.py')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); root = a.root.resolve(); archive = a.archive_root.resolve() if a.archive_root else None; out = a.out.resolve()
    assert bool(a.archive_root) != bool(a.legacy_bundle), 'Select original archive or a portable legacy bundle'
    assert root not in out.parents and (archive is None or archive not in out.parents)
    out.mkdir(parents=True, exist_ok=False)
    base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert base == '22999d28d8fe22f863fc8f62eaa45a57256083d0', base
    inputs = {}; manifests = {}; scope = read(root/'PUBLIC_SCOPE.json')
    manifest_paths = list((archive/'runs/controller-fault-v8/vision/batches').glob('*/run_manifest.json')) if archive else list((a.legacy_bundle/'manifests').glob('*.json'))
    for p in manifest_paths:
        m = read(p); h = sha(p); source = p.parent/'source/sim_vision/run_closedloop.py' if archive else a.legacy_bundle/'source/run_closedloop_v8.py'
        hashes = {k.replace('\\','/'):v for k,v in m['source_sha256'].items()}
        assert source.is_file() and sha(source) == hashes['sim_vision/run_closedloop.py']
        batch = p.parent.name if archive else p.stem
        manifests[h] = dict(manifest_sha256=h, batch=batch, source_sha256=sha(source),
            parameters=m['parameters'], hardware=m['hardware'], python=m['python'], packages=m['packages'],
            neural_dt_ms=m['neural_dt_ms'], runtime_backend=m['runtime_backend'])
        dest = out/'local-manifests'/f'{batch}.json';dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(p, dest)
    assert len(manifests) == 6
    assert len({m['source_sha256'] for m in manifests.values()}) == 1
    source = next((archive/'runs/controller-fault-v8/vision/batches').glob('*/source/sim_vision/run_closedloop.py')) if archive else a.legacy_bundle/'source/run_closedloop_v8.py'
    source_hash = sha(source)
    assert source_hash == sha(root/'sim_vision/run_closedloop.py')
    (out/'source').mkdir(); shutil.copyfile(source,out/'source/run_closedloop_v8.py')
    constants = {}
    for node in ast.parse(source.read_text()).body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    delay = constants['BURST_DELAY_MS']; burst = 1000*constants['BURST_S']; frame = constants['FRAME_DT_MS']
    assert (delay,burst,frame) == (250.,450.,20.)
    rows = []; error_sets = dict(delay=set(),completed_before_horizon_duration=set(),horizon_flag=set())
    selected = sorted((root/'runs/controller-fault-v8/vision/episodes_controls').glob('*.json'))
    assert len(selected) == 72
    partial_spike_upper = 0; global_burst_spikes = 0; source_matches = []
    for path in selected:
        name = path.relative_to(root).as_posix(); r = read(path); h = sha(path); inputs[name] = h
        assert scope['files'][name]['sha256'] == h
        if archive:
            original = archive/name
            assert original.is_file() and sha(original) == h
        assert r['run_manifest_sha256'] in manifests
        m = manifests[r['run_manifest_sha256']]
        assert m['parameters']['burst_delay_ms'] == delay
        source_matches.append(dict(source=name,source_sha256=h,manifest_sha256=r['run_manifest_sha256'],batch=m['batch']))
        trigger = r['trigger_ms']; horizon = r['horizon_ms']; duration = r['duration_ms']
        active = []; cumulative = 0; previous_xy = (0.,0.); speed_max_error = 0.; geometric_error = 0.
        previous_target = (constants['D0']*math.cos(math.radians(r['phi_t_deg'])), constants['D0']*math.sin(math.radians(r['phi_t_deg'])))
        nominal_lower = nominal_upper = actual_count = 0
        nominal_on = trigger+delay if trigger is not None else None
        nominal_end = trigger+delay+burst if trigger is not None else None
        for q in r['log']:
            t0,t1=q['t_ms'],q['t_end_ms']; dt=(t1-t0)/1000.
            assert t1-t0 == frame
            increment = q['n_total']-cumulative; cumulative = q['n_total']
            assert increment >= 0 and isinstance(increment,int)
            xy=q['fly_x'],q['fly_y']; speed=math.hypot(xy[0]-previous_xy[0],xy[1]-previous_xy[1])/dt
            expected_speed=constants['V_BURST'] if q['burst'] else constants['V_FLY']
            speed_max_error=max(speed_max_error,abs(speed-expected_speed))
            assert abs(speed-expected_speed) < 1e-12
            # Independently recompute the native discrete model's relative-segment minimum.
            before = (previous_target[0]-previous_xy[0],previous_target[1]-previous_xy[1])
            target = q['target_x'],q['target_y']; after = target[0]-xy[0],target[1]-xy[1]
            delta = after[0]-before[0],after[1]-before[1]; norm2 = delta[0]**2+delta[1]**2
            fraction = max(0.,min(1.,-(before[0]*delta[0]+before[1]*delta[1])/norm2)) if norm2 else 0.
            minimum = math.hypot(before[0]+fraction*delta[0],before[1]+fraction*delta[1])
            geometric_error = max(geometric_error,abs(minimum-q['step_min_dist']))
            assert abs(minimum-q['step_min_dist']) < 1e-12
            previous_xy=xy;previous_target=target
            if q['burst']:
                active.append(q); actual_count += increment
            if trigger is not None and max(t0,nominal_on)<min(t1,nominal_end):
                nominal_upper += increment
                if t0>=nominal_on and t1<=nominal_end:
                    nominal_lower += increment
        assert cumulative == r['n_total']
        assert r['escaped'] == all(q['step_min_dist'] > constants['D_CONTACT'] for q in r['log'])
        assert r['escaped'] == (r['termination_reason']=='horizon')
        if r['escaped']:assert duration==horizon
        onset=active[0]['t_ms'] if active else None
        realized_delay=onset-trigger if active else None
        observed_burst=sum(q['t_end_ms']-q['t_ms'] for q in active)
        has_off=bool(active and any(not q['burst'] and q['t_ms']>=active[-1]['t_end_ms'] for q in r['log']))
        endpoint_reached = duration==horizon
        declared_flag=bool(trigger is not None and nominal_on<=horizon<nominal_end) if endpoint_reached else None
        actual_interval_on=frame*math.ceil(nominal_on/frame) if trigger is not None else None
        actual_interval_end=frame*math.ceil(nominal_end/frame) if trigger is not None else None
        realized_flag=bool(trigger is not None and actual_interval_on<=horizon<actual_interval_end) if endpoint_reached else None
        if active:assert onset==actual_interval_on
        declared_exposure=max(0.,min(duration,nominal_end)-max(0.,nominal_on)) if trigger is not None else 0.
        full_end_observed=bool(active and duration>=actual_interval_end)
        at_boundary=bool(full_end_observed and actual_interval_end==horizon)
        if realized_delay is not None and realized_delay!=delay:error_sets['delay'].add(name)
        if has_off and observed_burst!=burst:error_sets['completed_before_horizon_duration'].add(name)
        if endpoint_reached and r['burst_active_at_horizon']!=declared_flag:error_sets['horizon_flag'].add(name)
        if active:
            assert declared_exposure-observed_burst==10.
            assert actual_count==nominal_lower
        partial_spike_upper+=nominal_upper-actual_count
        global_burst_spikes+=actual_count
        rows.append(dict(source=name,sha256=h,mode=r['mode'],fault=r['fault'],seed=r['seed'],bearing_deg=r['phi_t_deg'],
            trigger_ms=trigger,declared_delay_ms=delay,declared_onset_ms=nominal_on,realized_onset_ms=onset,
            onset_error_ms=realized_delay-delay if active else None,declared_full_burst_ms=burst,
            observed_active_ms=observed_burst,declared_exposure_within_record_ms=declared_exposure,
            exposure_overstatement_ms=declared_exposure-observed_burst,
            completed_with_explicit_following_off_frame=has_off,full_event_end_within_observation=full_end_observed,
            event_end_exactly_at_H=at_boundary,elapsed_record_ms=duration,horizon_ms=horizon,
            recorded_horizon_flag=r['burst_active_at_horizon'],declared_half_open_flag_at_H=declared_flag,
            realized_frame_grid_flag_at_H=realized_flag,horizon_was_observed=endpoint_reached,
            observed_total_global_spikes=r['n_total'],actual_burst_marked_global_spikes=actual_count,
            declared_interval_spike_lower=nominal_lower,declared_interval_spike_upper=nominal_upper,
            observed_task_success=r['escaped'],task_label_matches_recorded_geometry=True,
            observed_rate_per_s=r['n_total']/(duration/1000),nominal_H_denominator_rate_per_s=r['n_total']/(horizon/1000),
            nominal_rate_divided_by_observed_rate=duration/horizon,max_velocity_error_m_s=speed_max_error,
            max_recomputed_segment_min_distance_error_m=geometric_error))
    # Compare the independent sets against the prior published probe.
    old=read(root/'audit/v10/legacy-timing-01/check.json')
    for ours,key in [('delay','delay_errors'),('completed_before_horizon_duration','completed_duration_errors'),('horizon_flag','horizon_flag_errors')]:
        assert error_sets[ours] == {x['path'] for x in old[key]}
    active_rows=[r for r in rows if r['realized_onset_ms'] is not None]
    full_rows=[r for r in rows if r['full_event_end_within_observation']]
    failures=[r for r in rows if not r['observed_task_success']]
    union=set().union(*error_sets.values()); actual_positive=sum(r['realized_frame_grid_flag_at_H'] is True for r in rows)
    summary=dict(protocol='V8 geometry-v2 historical engineering logs only',records=72,
        unique_records_with_any_published_timing_error=len(union),error_counts={k:len(v) for k,v in error_sets.items()},
        overlaps={k:sorted(v) for k,v in error_sets.items()},triggered=sum(r['trigger_ms'] is not None for r in rows),
        actual_burst_started=len(active_rows),ended_before_H_with_explicit_off_frame=sum(r['completed_with_explicit_following_off_frame'] for r in rows),
        full_end_within_observation=len(full_rows),full_end_at_H=sum(r['event_end_exactly_at_H'] for r in rows),
        realized_delay_ms=sorted(set(r['realized_onset_ms']-r['trigger_ms'] for r in active_rows)),
        full_burst_observed_duration_ms=sorted(set(r['observed_active_ms'] for r in full_rows)),
        onset_bias_ms=[10.,10.],timing_exposure_overstatement_total_ms=sum(r['exposure_overstatement_ms'] for r in rows),
        nominal_interval_overlaps_logged_record=sum(r['declared_exposure_within_record_ms']>0 for r in rows),
        exposure_overstatement_started_records_ms=sum(r['exposure_overstatement_ms'] for r in active_rows),
        scheduled_without_observed_burst=[dict(source=r['source'],trigger_ms=r['trigger_ms'],duration_ms=r['elapsed_record_ms'],declared_exposure_within_record_ms=r['declared_exposure_within_record_ms']) for r in rows if r['trigger_ms'] is not None and r['realized_onset_ms'] is None],
        recorded_active_flags=sum(r['recorded_horizon_flag'] for r in rows),actual_active_flags_at_H=actual_positive,
        horizon_reached=sum(r['horizon_was_observed'] for r in rows),
        flag_excess_percentage_points_all_records=(sum(r['recorded_horizon_flag'] for r in rows)-actual_positive)/72*100,
        flag_excess_percentage_points_horizon_reaching=(sum(r['recorded_horizon_flag'] for r in rows)-actual_positive)/len(active_rows)*100,
        task_labels_inconsistent_with_logged_geometry=0,
        change_in_task_labels_under_corrected_actuation='Not identifiable: would require a full closed-loop intervention; not simulated',
        actual_burst_marked_global_spikes=global_burst_spikes,
        extra_global_spikes_assigned_to_declared_burst_interval_bounds=[0,partial_spike_upper],
        burst_spike_bound_reason='Only 20-ms cumulative bins are archived; the missing onset half-bin is 10 ms. No uniform spike-time interpolation is justified.',
        elapsed_exposure_ms=sum(r['elapsed_record_ms'] for r in rows),declared_H_exposure_ms=sum(r['horizon_ms'] for r in rows),
        stopped_records=len(failures),stopped_duration_ms_range=[min(r['elapsed_record_ms'] for r in failures),max(r['elapsed_record_ms'] for r in failures)],
        nominal_H_denominator_rate_relative_understatement_pct_range=[100*(1-max(r['nominal_rate_divided_by_observed_rate'] for r in failures)),100*(1-min(r['nominal_rate_divided_by_observed_rate'] for r in failures))],
        exposure_note='Using nominal H instead of logged duration changes rate denominators; it does not identify post-stop neural activity, counterfactual energy or changed contacts.')
    assert summary['error_counts']==dict(delay=17,completed_before_horizon_duration=4,horizon_flag=6)
    assert len(union)==17 and len(full_rows)==10 and summary['full_end_at_H']==6
    csv_new(out/'all-historical-records.csv',rows)
    write_new(out/'historical-results.json',summary)
    write_new(out/'generation-provenance.json',dict(source_sha256=source_hash,source_copy='source/run_closedloop_v8.py',
        archived_source_matches_curated_source=True,constants={k:constants[k] for k in ['FRAME_DT_MS','V_FLY','V_BURST','BURST_S','BURST_DELAY_MS','D_CONTACT']},
        original_manifests_available_in_local_archive=True,original_manifests_distributed_in_22999d2=False,
        manifests=list(manifests.values()),record_manifest_bindings=source_matches))
    write_new(out/'input-hashes.json',dict(base_commit=base,inputs=inputs,
        reference_probe_sha256=sha(root/'audit/v10/legacy-timing-01/check.json'),script_sha256=sha(Path(__file__)),python=platform.python_version()))
    budget=[];batch_resources={};batches={}
    for label,folder in [('RF-0','runs/task-v9-test'),('RF-A','runs/task-v10-transfer/map-A/test'),('RF-B','runs/task-v10-transfer/map-B/test')]:
        for p in (root/folder/'batches').glob('*/run_manifest.json'):
            m=read(p);mh=sha(p);batches[mh]=dict(RF=label,path=p.relative_to(root).as_posix(),sha256=mh,hardware=m['hardware'],python=m['python'],packages=m['packages'],runtime_backend=m['runtime_backend'])
        for p in (root/folder/'episodes').glob('*.json'):
            r=read(p);w=r.get('worker_resources',{});mh=r['run_manifest_sha256'];assert mh in batches
            budget.append(dict(RF=label,source=p.relative_to(root).as_posix(),sha256=sha(p),manifest_sha256=mh,
                wall_seconds=r['wall_seconds'],repeated_worker_build_seconds=r['build_seconds'],
                worker_peak_working_set_bytes=w.get('worker_peak_working_set_bytes'),worker_private_bytes=w.get('worker_private_bytes'),
                physical_memory_bytes=w.get('physical_memory_bytes'),processor_model=w.get('processor_model'),logical_cpus=w.get('logical_cpus')))
            if w:
                b=batch_resources.setdefault(mh,dict(RF=label,manifest_sha256=mh,records=0,max_reported_process_lifetime_peak_bytes=0,processor_model=w['processor_model'],physical_memory_bytes=w['physical_memory_bytes'],logical_cpus=w['logical_cpus']))
                b['records']+=1;b['max_reported_process_lifetime_peak_bytes']=max(b['max_reported_process_lifetime_peak_bytes'],w['worker_peak_working_set_bytes'])
    assert len(budget)==576
    csv_new(out/'all-generation-costs.csv',budget)
    csv_new(out/'transfer-worker-costs.csv',list(batch_resources.values()))
    times=[r['wall_seconds'] for r in budget]
    cost=dict(test_episodes=576,episode_wall_seconds_sum=sum(times),sum_in_hours=sum(times)/3600,
        median_episode_wall_seconds=statistics.median(times),range_episode_wall_seconds=[min(times),max(times)],
        mean_episode_wall_seconds=statistics.mean(times),worker_build_values_repeated_per_episode=True,
        hardware_manifest_records=list(batches.values()),transfer_worker_resources=list(batch_resources.values()),
        RF0_process_memory_not_recorded=True,campaign_elapsed_wall_time_not_identifiable=True,CPU_time_not_recorded=True,
        budget_note='wall_seconds includes task run and per-episode damage-cache accounting; elapsed sums are neither CPU-hours nor actual campaign duration. Peak working set is a cumulative worker-lifetime value, not a per-episode peak.')
    write_new(out/'generation-costs.json',cost)
    for name,h in inputs.items():assert sha(root/name)==h
    print(json.dumps(dict(passed=True,historical=summary,budget={k:v for k,v in cost.items() if k not in ['hardware_manifest_records','transfer_worker_resources']}),indent=2))


if __name__=='__main__':main()
