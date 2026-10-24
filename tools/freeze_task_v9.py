"""Freeze independent test registration only after complete healthy validation."""
import argparse
import hashlib
import importlib.metadata
import json
from datetime import datetime,timezone
from pathlib import Path
import sys
from task_metrics_v9 import calibration_thresholds


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--validation',type=Path,required=True)
    ap.add_argument('--calibration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--stress-out',type=Path)
    args=ap.parse_args()
    paths=sorted((args.validation/'episodes').glob('*.json'))
    rs=[json.loads(p.read_text()) for p in paths]
    expected={(s,float(phi),m,'healthy') for s in range(400,408) for phi in [-30,30] for m in ['proportional','relay']}
    if len(rs)!=32 or {(r['seed'],r['phi_deg'],r['mode'],r['fault']) for r in rs}!=expected:
        raise ValueError('require all 32 prespecified validation-B healthy episodes')
    counts={f'{m}/{phi:g}':sum(r['escaped'] for r in rs if (r['mode'],r['phi_deg'])==(m,phi))
        for m in ['proportional','relay'] for phi in [-30.,30.]}
    if min(counts.values())<6: raise ValueError(f'capability screen failed: {counts}')
    if any(r['calibration_sha256']!=sha(args.calibration) for r in rs): raise ValueError('calibration differs')
    if any(r['collision_ms'] is not None and r['collision_ms']<=400 for r in rs): raise ValueError('400 ms prefix is not pre-contact')
    source_paths=sorted(list(Path('sim').glob('*.py'))+list(Path('sim_vision').glob('*.py')))
    source_paths += [Path('tools')/name for name in ['task_metrics_v9.py','freeze_task_v9.py',
        'analyze_task_v9.py','run_task_v9.py','launch_task_v9.py','run_v9.py','calibrate_task_v9.py','replay_audit_v9.py']]
    source_paths.append(Path('requirements-v9.txt'))
    sources={p.as_posix():sha(p) for p in source_paths}
    from project_paths import MODEL_DIR,PATH_COMP,PATH_CON,PATH_ANN
    model_inputs={p.name:sha(p) for p in [MODEL_DIR/'model.py',PATH_COMP,PATH_CON]}
    validation_manifests={sha(p):p for p in (args.validation/'batches').glob('*/run_manifest.json')}
    for r in rs:
        if r['run_manifest_sha256'] not in validation_manifests: raise ValueError('missing validation manifest')
    for p in validation_manifests.values():
        m=json.loads(p.read_text())
        if m['model_inputs']!=model_inputs or m['annotations_sha256']!=sha(PATH_ANN):
            raise ValueError('validation model inputs differ from planned test')
        for name,value in m['source_sha256'].items():
            portable=name.replace('\\','/')
            if portable=='sim/run_provenance.py': continue # path canonicalization only, no neural dynamics
            current=MODEL_DIR/'model.py' if portable=='external/model.py' else Path(portable)
            if sha(current)!=value: raise ValueError(f'neural source changed since validation: {name}')
    reg=dict(protocol='task-v9.1-causal-exact-events',created_utc=datetime.now(timezone.utc).isoformat(),
        development_seeds=list(range(200,204)),discarded_configuration_seeds=[300,301,302,303],
        validation_seeds=list(range(400,408)),test_seeds=list(range(1000,1024)),
        phis=[-30.,30.],modes=['proportional','relay'],faults=['healthy','F2_25','F2_50'],
        horizon_ms=1000,expected_test_episodes=288,independent_units=24,
        geometry=dict(initial_distance_m=.25,collision_radius_m=.05,looming_radius_m=.05,
            threat_speed_m_s=.3,walk_speed_m_s=.05,burst_speed_m_s=.35,cue_ms=100.,
            burst_delay_ms=250.,burst_duration_ms=450.,feedback_dt_ms=20.,neural_dt_ms=.1,rf_seed=20260201),
        calibration_sha256=sha(args.calibration),thresholds=calibration_thresholds(rs),
        validation_successes=counts,validation_input_sha256={p.as_posix():sha(p) for p in paths},
        frozen_source_sha256=sources,
        model_inputs_sha256=model_inputs,annotations_sha256=sha(PATH_ANN),
        runtime=dict(python=sys.version,packages={name:importlib.metadata.version(name) for name in
            ['numpy','brian2','pandas','pyarrow','matplotlib','scipy','Cython','joblib']}),
        primary_estimands=['seed-cluster paired healthy-to-fault loss and gain at both deletion doses',
            'same-record stopping-time versus common-duration spike ratios, with separate fixed-400-ms and fixed-1000-ms resource estimands'],
        secondary_estimands=['relay-minus-proportional net loss interaction, both bearings averaged within seed',
            '400-ms warning sensitivity/specificity/FPR/FNR on ALL independent test records, and fault-only/healthy subgroups',
            'prespecified repeated task horizons 800/900/1000 ms and activity prefixes 200/400/600/800/1000 ms; no optimal-window selection',
            'held-command deadline candidate versus command-rate, two-sided-activity and actuator-schedule/zero-future-turn comparators; upper activity limits are resource criteria'],
        bootstrap=dict(unit='complete seed cluster with all bearings/laws/doses',draws=20000,seed=20261022,interval='percentile 95%; conditional on one model/map/task'),
        interaction_test='exact symmetric-null cluster sign-flip, Holm over two deletion doses; not a randomized-treatment test',
        stopping_rule='exactly 24 test clusters; no efficacy stopping, seed replacement, threshold tuning, or post-outcome extension',
        precision='24 independent bounded cluster means give worst-case approximate 95% half-width 0.20; report actual intervals, sparse/zero-event limitations. Not powered for small interactions.',
        deadline_candidate='400-ms state and neural command held to horizon; earliest next-frame trigger if absent; exact known synthetic geometry; not neural-only, reachability proof, or deployable sensor implementation',
        full_exposure='continue counterfactual post-contact trajectory, latch failure; 1-s activity is resource accounting, not warning evidence',
        exclusions='none; retain all directions, failed healthy cases, gains, and unfavorable conditions',
        provenance_note='local prospective registration, not external timestamping; no final test outcomes inspected')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as f: json.dump(reg,f,indent=2)
    if args.stress_out:
        stress={**reg,'test_seeds':list(range(1100,1108)),'phis':[-45.,45.],
            'expected_test_episodes':96,'independent_units':8,
            'primary_estimands':['prespecified off-angle stress transfer of outcomes and paired exposure; descriptive, do not pool with core 24-cluster inference'],
            'activity_reference_transfer':'nearest same-side +/-30-degree validation reference; no new thresholds',
            'stopping_rule':'exactly eight new stress clusters, independent of core outcomes; optional cancellation only for deadline/resource constraints, disclosed',
            'precision':'eight clusters are a stress check with wide uncertainty, not powered confirmation',
            'core_registration_sha256':sha(args.out)}
        with args.stress_out.open('x') as f: json.dump(stress,f,indent=2)
    print(json.dumps(dict(registration=str(args.out),sha256=sha(args.out),validation_successes=counts,thresholds=reg['thresholds']),indent=2))


if __name__=='__main__': main()
