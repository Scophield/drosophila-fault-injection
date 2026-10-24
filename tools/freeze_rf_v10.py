"""Freeze per-map test registrations after complete untuned healthy validation."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from task_metrics_v9 import calibration_thresholds


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['design','rf-map','validation','calibration','out']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();design=json.loads(a.design.read_text());mapping=json.loads(a.rf_map.read_text())
    spec=next(q for q in design['maps'] if q['map_id']==mapping['map_id'])
    paths=sorted((a.validation/'episodes').glob('*.json'));rs=[json.loads(p.read_text()) for p in paths]
    expected={(s,phi,m,'healthy') for s in spec['validation_seeds'] for phi in design['phis'] for m in design['modes']}
    assert len(rs)==32 and {(r['seed'],r['phi_deg'],r['mode'],r['fault']) for r in rs}==expected
    assert all(r['rf_map_sha256']==spec['sha256'] and r['calibration_sha256']==sha(a.calibration) for r in rs)
    assert all(r['collision_ms'] is None or r['collision_ms']>400 for r in rs)
    reg=json.loads(Path('runs/task-v9-frozen/registration-core.json').read_text())
    sources=dict(reg['frozen_source_sha256'])
    for n in ['run_task_v10.py','calibrate_task_v10.py','prepare_rf_v10.py','resource_v10.py','freeze_rf_v10.py','campaign_rf_v10.py','analyze_task_v10.py']:
        sources['tools/'+n]=sha(Path('tools')/n)
    for n,h in sources.items():assert sha(n)==h,'V9/frozen source changed: '+n
    counts={f'{m}/{phi:g}':sum(r['escaped'] for r in rs if (r['mode'],r['phi_deg'])==(m,phi)) for m in design['modes'] for phi in design['phis']}
    reg.update(created_utc=datetime.now(timezone.utc).isoformat(),experiment_version=design['experiment'],map_id=spec['map_id'],
        design_sha256=sha(a.design),rf_map_sha256=spec['sha256'],development_seeds=spec['development_seeds'],
        discarded_configuration_seeds=[],validation_seeds=spec['validation_seeds'],test_seeds=spec['test_seeds'],
        expected_test_episodes=144,independent_units=12,calibration_sha256=sha(a.calibration),
        thresholds=calibration_thresholds(rs),validation_successes=counts,
        validation_input_sha256={p.as_posix():sha(p) for p in paths},frozen_source_sha256=sources,
        geometry={**reg['geometry'],'rf_seed':spec['rf_seed']},
        primary_estimands=design['test']['primary'],secondary_estimands=design['test']['secondary'],
        bootstrap={**reg['bootstrap'],'seed':20261023,'interval':'95% percentile, whole seed within map, conditional on one map'},
        interaction_test=design['test']['multiplicity'],stopping_rule=design['stopping'],precision=design['test']['precision'],
        provenance_note='Prospective V10 RF-transfer design before pilot; this per-map registration freezes validation-derived thresholds before new test launch. Local timestamp, no test tuning or outcome filtering.',
        validation_capability_pass=min(counts.values())>=6,
        validation_capability_note='All maps retained and tested under fixed recipe; failures limit interpretation, no controller/map replacement.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(reg,f,indent=2)
    print(json.dumps(dict(registration=str(a.out),sha256=sha(a.out),validation_successes=counts),indent=2))


if __name__=='__main__':main()
