"""Additional checks of the retrospective burst-end analysis; no neural runs.

Synthetic motion fixtures below are software tests, never experimental samples.
No forecast thresholds are selected or fitted. The original analysis is retained.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_burst_end import ROOT, R, VP, VW, CMIN, CMAX, forecast, hit, read, sha, export


def prefix_state(prefix):
    """Accept prefix frames only, with no episode outcome or suffix argument."""
    q = prefix[-1]
    trigger = q['trigger_ms']
    assert trigger is not None and q['t_end_ms'] == trigger + 700
    return dict(fly=q['fly'], target=q['target'], heading=np.radians(q['heading_deg']),
                omega=q['next_omega']), q['t_end_ms']


def software_tests():
    assert hit(np.array([.1, 0]), np.array([.04, 0])) == (0.1-.05)/(.1-.04)
    assert hit(np.array([.1, .1]), np.array([.04, .1])) is None
    assert hit(np.array([.04, 0]), np.array([.1, 0])) == 0
    # Agent toward / away from pursuer: analytically known contact times.
    for target_x, closure in [(.1, .35), (-.1, .25)]:
        p = forecast(dict(fly=[0, 0], target=[target_x, 0], heading=0.), 0, 400)
        assert abs(p['contact_ms']-1000*.05/closure) < 1e-7
    rng = np.random.default_rng(20261025)
    checked = 0
    for _ in range(2000):
        # Adversarially varied headings, not fitted to any archived trajectory.
        C = rng.uniform(.0001, .10)
        rel = np.array([R+C, 0.])
        T = float(rng.choice([.02, .06, .10, .16, .30]))
        first = None
        for k in range(round(T/.02)):
            angle = rng.uniform(-np.pi, np.pi)
            vel = -VP*rel/np.linalg.norm(rel) - VW*np.array([np.cos(angle), np.sin(angle)])
            after = rel+.02*vel
            u = hit(rel, after)
            if u is not None:
                first = .02*(k+u)
                break
            rel = after
        if C < CMIN*T:
            assert first is not None
        if C > CMAX*T:
            assert first is None
        checked += 1
    return dict(analytic_contact_fixtures=5, randomized_heading_bound_fixtures=checked,
                synthetic_fixtures_are_not_experiment_records=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    import csv
    raw_rows = list(csv.DictReader((a.input/'all-records.csv').open(encoding='utf-8', newline='')))
    metadata = read(a.input/'results.json')
    configs = dict(zip(['RF-0', 'RF-A', 'RF-B'], ['runs/task-v9-frozen/calibration.json',
        'runs/task-v10-transfer/map-A/calibration.json', 'runs/task-v10-transfer/map-B/calibration.json']))
    calibrations = {k: read(ROOT/v) for k, v in configs.items()}
    registrations = {k: read(ROOT/v) for k, v in zip(configs,
        ['runs/task-v9-frozen/registration-core.json', 'runs/task-v10-transfer/map-A/registration.json',
         'runs/task-v10-transfer/map-B/registration.json'])}
    for tag, p in configs.items():
        assert sha(ROOT/p) == registrations[tag]['calibration_sha256']
    bykey = {r['key']: r for r in raw_rows}
    tests = software_tests()
    gating, late, phase = [], [], []
    prefix_checks, collision_errors = 0, []
    for row in raw_rows:
        p = ROOT/row['source']
        assert sha(p) == row['source_sha256']
        r = read(p)
        B = r['trigger_ms']+700
        c = calibrations[row['RF']]
        if row['landmark_status'] == 'at_risk':
            # Discard the suffix and all episode-level outcome fields before predicting.
            prefix = [q for q in r['log'] if q['t_end_ms'] <= B]
            s, t = prefix_state(prefix)
            for kind, omega in [('held_heading', 0.), ('held_turn', s['omega'])]:
                f = forecast(s, t, 1000., omega)
                saved = row[kind+'_contact_ms']
                assert (f['contact_ms'] is None) == (saved == '')
                if saved:
                    assert abs(f['contact_ms']-float(saved)) < 1e-7
                assert abs(1000*f['min_clearance_m']-float(row[kind+'_margin_mm'])) < 1e-8
            prefix_checks += 1
            end = min(1000, r['collision_ms'] or 1000)
            # Decisions at B and later that can affect any pre-contact interval.
            decisions = [q for q in r['log'] if B <= q['t_end_ms'] < end]
            for q in decisions:
                feature = np.array(q['smooth_rates'])
                gate = c.get('gate_silent', False) and float(feature.mean()) < c['trigger_hz']
                score = float(feature@c['direction_weights']+c['direction_intercept'])
                expected = 0. if gate else -c['turn_gain_deg_s']*(np.clip(score,-1,1)
                    if r['mode']=='proportional' else np.sign(score))
                assert abs(expected-q['next_omega']) < 1e-8
            gating.append(dict(key=row['key'], RF=row['RF'], seed=r['seed'], law=r['mode'], fault=r['fault'],
                decisions=len(decisions), silent_gated=sum(c.get('gate_silent',False) and q['cmd_hz']<c['trigger_hz'] for q in decisions),
                zero_turn=sum(abs(q['next_omega'])<1e-9 for q in decisions),
                nonzero_command_max=max([0.]+[abs(q['next_omega']) for q in decisions]),
                pre_B_radial_m_s=float(row['radial_velocity_pre_B_m_s']),
                post_B_radial_m_s=float(row['radial_velocity_post_B_m_s'])))
            if r['collision_ms'] is not None:
                collision_errors.append(abs(r['collision_ms']-float(row['held_heading_contact_ms'])))
                late.append(row)
        if r['collision_ms'] is not None:
            phase.append(dict(key=row['key'], RF=row['RF'], phase=row['contact_phase'],
                warning_400=row['command_warning_400']=='True', first_contact_ms=r['collision_ms'],
                B_ms=B, precontact_warning_lead_ms=r['collision_ms']-400))
    export(a.out/'late-contacts.csv', late)
    export(a.out/'feedback-phase.csv', gating)
    export(a.out/'all-contact-phases.csv', phase)
    tests.update(prefix_only_forecasts_verified=prefix_checks,
                 max_held_heading_first_contact_error_ms=max(collision_errors))
    rng = np.random.default_rng(20261026)
    pairs = []
    for row in raw_rows:
        if row['fault'] == 'healthy':
            continue
        reference = bykey[f"{row['RF']}/{row['seed']}/{float(row['bearing_deg']):g}/{row['law']}/healthy"]
        pairs.append(dict(RF=row['RF'], seed=int(row['seed']), law=row['law'], fault=row['fault'],
            bearing=float(row['bearing_deg']), scheduled_B_delay_ms=float(row['burst_end_ms'])-float(reference['burst_end_ms']),
            row_status=row['landmark_status'], reference_status=reference['landmark_status']))
    export(a.out/'all-healthy-fault-schedule-pairs.csv', pairs)
    timing = []
    for tag in configs:
        for law in ['proportional','relay']:
            for fault in ['F2_25','F2_50']:
                pp = [p for p in pairs if p['RF']==tag and p['law']==law and p['fault']==fault]
                byseed = defaultdict(list)
                for p in pp:
                    byseed[p['seed']].append(p['scheduled_B_delay_ms'])
                v = np.array([np.mean(values) for values in byseed.values()])
                boot = v[rng.integers(len(v), size=(10000,len(v)))].mean(axis=1)
                timing.append(dict(RF=tag, law=law, fault=fault, all_pairs=len(pp), seeds=len(v),
                    scheduled_B_delay_mean_ms=float(v.mean()), delay_CI95=list(np.quantile(boot,[.025,.975])),
                    delay_min_ms=min(p['scheduled_B_delay_ms'] for p in pp),
                    delay_max_ms=max(p['scheduled_B_delay_ms'] for p in pp),
                    row_status_counts=dict(Counter(p['row_status'] for p in pp))))
    export(a.out/'all-pair-timing.csv', timing)
    pr = []
    for row in raw_rows:
        if row['law']=='proportional':
            ref = bykey[row['key'].replace('/proportional/','/relay/')]
            assert row['burst_end_ms']==ref['burst_end_ms'] and row['mask_sha256']==ref['mask_sha256']
            pr.append(row['key'])
    support = []
    for tag in configs:
        risk = [r for r in raw_rows if r['RF']==tag and r['landmark_status']=='at_risk']
        failed_seeds = {r['seed'] for r in risk if r['late_contact']=='True'}
        safe_seeds = {r['seed'] for r in risk if r['late_contact']=='False'}
        support.append(dict(RF=tag, failure_seed_clusters=len(failed_seeds), safe_seed_clusters=len(safe_seeds),
            # One-sided exact bounds on a seed-level any-error probability.
            # Assumes exchangeable clusters; not a trajectory-level FNR interval.
            miss_cluster_probability_95_upper_if_zero_misses=1-.05**(1/len(failed_seeds)),
            false_alarm_cluster_probability_95_upper_if_zero_false_alarms=1-.05**(1/len(safe_seeds))))
    tests['all_P_R_schedule_and_mask_matches'] = len(pr)
    risk_rows = [r for r in raw_rows if r['landmark_status']=='at_risk']
    capture_upper = [float(r['burst_end_ms'])+float(r['clearance_B_mm'])/CMIN for r in risk_rows]
    extrapolation = dict(
        classification='Analytic model consequence, not an observed outcome or extended neural simulation',
        assumptions='continued same pursuer, fixed walk speed after the single burst, unchanged collision radius and frame time',
        eventual_capture_bound_ms_min=min(capture_upper), eventual_capture_bound_ms_max=max(capture_upper),
        observed_success_means='no first contact through 1000 ms only')
    result = dict(classification='Post-hoc validation and uncertainty supplement; no tuning or new samples',
        tests=tests, all_pair_timing=timing, zero_error_cluster_uncertainty=support,
        feedback=dict(risk_records=len(gating), decisions=sum(q['decisions'] for q in gating),
            silent_gated=sum(q['silent_gated'] for q in gating), zero_turn=sum(q['zero_turn'] for q in gating),
            all_trajectories_radially_separating_before_B=all(q['pre_B_radial_m_s']>0 for q in gating),
            all_trajectories_radially_closing_after_B=all(q['post_B_radial_m_s']<0 for q in gating)),
        model_extrapolation=extrapolation,
        lead_time_ms=dict(min=min(float(r['time_to_contact_from_B_ms']) for r in late),
            median=float(np.median([float(r['time_to_contact_from_B_ms']) for r in late])),
            max=max(float(r['time_to_contact_from_B_ms']) for r in late)),
        input_result_sha256=sha(a.input/'results.json'), source_sha256=sha(__file__),
        calibration_sha256={tag:sha(ROOT/p) for tag,p in configs.items()},
        baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        timing_bootstrap=dict(draws=10000, seed=20261026, unit='whole seed within RF'),
        utc=datetime.now(timezone.utc).isoformat())
    (a.out/'validation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__=='__main__':
    main()
