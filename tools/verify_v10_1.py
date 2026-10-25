"""Verify the V10.1 publication and reproduce its reported timing counts."""
from pathlib import Path
import csv
import hashlib
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'sim_vision')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name):
    with (ROOT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def verify_warning_stage():
    from task_metrics_v9 import bind_count_cutoff,command_alert,command_count
    folder='output/warning-counts-v10_1-02/'
    warning=json.loads((ROOT/folder/'results.json').read_text())
    assert warning['complete'] and warning['records']==576 and warning['healthy_validation_records']==96
    for name,h in {**warning['input_sha256'],**warning['analysis_source_sha256']}.items():
        assert digest(ROOT/name)==h,name
    current=rows(folder+'all-records.csv');boundary=rows(folder+'boundary-records.csv')
    assert len(current)==576 and len(boundary)==19
    for tag,report in warning['maps'].items():
        regname={'RF-0':'runs/task-v9-frozen/registration-core.json','RF-A':'runs/task-v10-transfer/map-A/registration.json','RF-B':'runs/task-v10-transfer/map-B/registration.json'}[tag]
        reg=json.loads((ROOT/regname).read_text())
        validation=[json.loads((ROOT/name).read_text()) for name in reg['validation_input_sha256']]
        cutoff=bind_count_cutoff(reg['thresholds'],validation)['command_count_cutoff']
        assert cutoff==report['threshold']
        derived=dict(tp=0,fp=0,tn=0,fn=0)
        for row in [r for r in current if r['RF']==tag]:
            record=json.loads((ROOT/row['source']).read_text());count=command_count(record)
            alert=command_alert(count,cutoff);contact=not record['escaped']
            assert count==int(row['command_count']) and alert==(row['canonical_flag']=='True')
            derived['tp' if contact and alert else 'fn' if contact else 'fp' if alert else 'tn']+=1
        assert all(report['warning_scores']['transmission']['all'][k]==v for k,v in derived.items())
        assert report['canonical_vs_legacy_changed_labels']==0
        assert all(report['all_methods_point_and_interval_equal_to_saved'].values())
    assert all(r['RF']=='RF-0' and r['command_count']=='14' and r['collision']=='False' and r['canonical_flag']=='False' and r['alternative_flag']=='True' for r in boundary)
    stage=json.loads((ROOT/'output/postburst-stage-recheck-03/results.json').read_text())
    for name,h in {**stage['raw_input_sha256'],**stage['registration_sha256'],**stage['calibration_sha256']}.items():
        assert digest(ROOT/name)==h,name
    assert digest(ROOT/'tools/analyze_postburst_stage_v10_1.py')==stage['source_sha256']
    assert stage['records']==576 and stage['eligible_records']==543 and stage['effective_postburst_decisions']==3114
    assert stage['all_eight_features_zero'] and stage['all_postburst_turn_requests_zero']
    assert stage['records_with_post_B_global_spikes']==474 and stage['postburst_contacts']==13
    return {k:{n:v['warning_scores']['transmission']['all'][n] for n in ['tp','fp','tn','fn']} for k,v in warning['maps'].items()}


def main():
    scope = json.loads((ROOT / "PUBLIC_SCOPE.json").read_text())
    for name, expected in scope["files"].items():
        p = ROOT / name
        assert p.is_file() and p.stat().st_size == expected["bytes"], name
        assert digest(p) == expected["sha256"], name
    pdf = ROOT / "paper/iscas2027-v10.1-timing-candidate.pdf"
    assert digest(pdf) == digest(ROOT / "paper/main.pdf") == scope["candidate_pdf_sha256"]
    sources = [ROOT / "paper" / n for n in ["main.tex", "main_v10_1_timing.tex", "main_v10_horizon.tex"]]
    assert len({digest(p) for p in sources}) == 1
    output = "output/trigger-timing-20261025-03/"
    result = json.loads((ROOT / output / "results.json").read_text())
    for name, h in result["raw_input_sha256"].items():
        assert digest(ROOT / name) == h, name
    for name, h in result["calibration_sha256"].items():
        p = {"RF-0": "runs/task-v9-frozen/calibration.json", "RF-A": "runs/task-v10-transfer/map-A/calibration.json", "RF-B": "runs/task-v10-transfer/map-B/calibration.json"}[name]
        assert digest(ROOT / p) == h
    assert digest(ROOT / "provenance/analysis-source/analyze_trigger_timing.py") == result["source_sha256"]
    paired = rows(output + "all-healthy-fault-pairs.csv")
    lawpairs = rows(output + "all-P-R-pairs.csv")
    assert len(rows(output + "all-records.csv")) == 576 and len(paired) == 384 and len(lawpairs) == 288
    assert all(q["schedule_matched"] == q["mask_matched"] == q["uniform_matched"] == "True" for q in lawpairs)
    assert sum(q["task_discordant"] == "True" for q in lawpairs) == 15
    summary = []
    for tag, mean, sd, n, seeds in [("RF-0", 80., 42.87537606062978, 48, 24),
                                    ("RF-A", 57.5, 46.555250019174274, 24, 12),
                                    ("RF-B", 57.5, 29.672121302810414, 24, 12)]:
        selected = [q for q in paired if q["RF"] == tag and q["fault"] == "F2_50" and q["law"] == "proportional"]
        delays = [float(q["trigger_delta_ms"]) for q in selected]
        assert len(delays) == n and len({q["seed"] for q in selected}) == seeds
        assert abs(statistics.mean(delays)-mean) < 1e-10 and abs(statistics.stdev(delays)-sd) < 1e-10
        summary.append(dict(RF=tag, mean_ms=mean, sd_ms=sd, bearing_pairs=n, seed_clusters=seeds))
    contacts25 = [q for q in paired if q["RF"] == "RF-0" and q["law"] == "proportional" and q["fault"] == "F2_25" and q["task_contact"] == "True"]
    assert len(contacts25) == 2 and all(float(q["trigger_delta_ms"]) == 0 for q in contacts25)
    print(json.dumps(dict(passed=True, version="V10.1", distributed_files=len(scope["files"]),
                          pdf_sha256=digest(pdf), frozen_neural_records=576,
                          healthy_fault_pairs=384, P_R_pairs=288, P_R_task_discordant=15,
                          paired_delay_summary=summary,canonical_warning_confusion=verify_warning_stage(),
                          warning_boundary_records_verified=19,postburst_at_risk_records=543,
                          postburst_decisions=3114), indent=2))


if __name__ == "__main__":
    main()
