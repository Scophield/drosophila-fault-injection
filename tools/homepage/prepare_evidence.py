"""Select and replay traceable illustrative examples from frozen V10.1 records.

No neural dynamics, training, parameter fitting or raw-file writes are performed.
Display positions interpolate only within the task's verified original segments.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import csv
import hashlib
import importlib
import json
import math
import platform
import statistics
import subprocess
import sys

import numpy as np

COMMIT = "75313d7740491e7f7830e2fc554c21e1aaefe655"
REPOSITORY = "https://github.com/Scophield/drosophila-fault-injection"
CONFIGS = {
    "RF-0": ("audit/acceptance-v9/core-v2/summary.json", "runs/task-v9-frozen/registration-core.json", "runs/task-v9-frozen/calibration.json"),
    "RF-A": ("audit/v10/transfer-01/map-A/analysis/summary.json", "runs/task-v10-transfer/map-A/registration.json", "runs/task-v10-transfer/map-A/calibration.json"),
    "RF-B": ("audit/v10/transfer-01/map-B/analysis/summary.json", "runs/task-v10-transfer/map-B/registration.json", "runs/task-v10-transfer/map-B/calibration.json"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def dump_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def close(a, b, tolerance=1e-9):
    assert np.allclose(a, b, atol=tolerance, rtol=0), (a, b)


def key(rf, raw):
    return (rf, int(raw["seed"]), float(raw["phi_deg"]), raw["mode"], raw["fault"])


def alive_at(raw, horizon):
    return raw["collision_ms"] is None or raw["collision_ms"] > horizon


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root, out = args.data_root.resolve(), args.out.resolve()
    assert root != out and root not in out.parents, "Do not write inside the frozen data checkout"
    assert not (out / "examples.json").exists() and not (out / "summary.json").exists()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert commit == COMMIT, (commit, COMMIT)
    scope = read(root / "PUBLIC_SCOPE.json")
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root / "tools"), str(root / "sim_vision")]
    task = importlib.import_module("task_v9")
    old_replay = importlib.import_module("analyze_burst_end")
    independent = importlib.import_module("replay_audit_v9")
    for module_path in ["sim_vision/task_v9.py", "tools/analyze_burst_end.py", "tools/replay_audit_v9.py"]:
        assert sha(root / module_path) == scope["files"][module_path]["sha256"]

    index_name = "output/trigger-timing-20261025-03/all-records.csv"
    with (root / index_name).open(encoding="utf-8", newline="") as f:
        index = list(csv.DictReader(f))
    assert len(index) == 576
    records, raw_info, input_hashes = {}, {}, {}
    summaries, registrations, calibrations = {}, {}, {}
    for rf, paths in CONFIGS.items():
        summaries[rf], registrations[rf], calibrations[rf] = [read(root / p) for p in paths]
        assert sha(root / paths[2]) == registrations[rf]["calibration_sha256"]
        input_hashes.update({p: sha(root / p) for p in paths})
    for row in index:
        source = row["source"].replace("\\", "/")
        path, rf = root / source, row["RF"]
        digest = sha(path)
        assert digest == row["source_sha256"] == scope["files"][source]["sha256"]
        raw = read(path)
        k = key(rf, raw)
        assert k not in records
        assert raw["trigger_ms"] == float(row["trigger_ms"])
        assert raw["protocol"] == task.VERSION
        assert raw["horizon_ms"] == raw["duration_ms"] == 1000
        old_replay.reconstruct(raw)
        input_map_path = Path(source).parent.parent / "input-map.json"
        assert sha(root / input_map_path) == raw["input_map_sha256"]
        assert raw["calibration_sha256"] == sha(root / CONFIGS[rf][2])
        history, crossing = [], None
        for frame in raw["log"]:
            history.append(frame["cmd_rates"])
            smoothed = np.mean(history[-5:], axis=0)
            close(smoothed, frame["smooth_rates"])
            close(smoothed.mean(), frame["cmd_hz"])
            if crossing is None and frame["t_end_ms"] > 100 and frame["cmd_hz"] >= calibrations[rf]["trigger_hz"]:
                crossing = frame["t_end_ms"]
            assert frame["trigger_ms"] == crossing
            close(task.steering(smoothed, calibrations[rf], raw["mode"], frame["t_end_ms"]), frame["next_omega"])
        assert crossing == raw["trigger_ms"]
        records[k] = raw
        raw_info[k] = dict(source=source, source_sha256=digest, input_map_source=input_map_path.as_posix())
        input_hashes[source] = digest
    assert Counter(k[0] for k in records) == {"RF-0": 288, "RF-A": 144, "RF-B": 144}

    # All P/R comparisons, including healthy and both doses, are checked explicitly.
    pr = []
    prefix_fields = ["fly", "target", "heading_deg", "cmd_rates", "smooth_rates", "cmd_hz", "u", "phi_now", "half_angle", "n_total"]
    for k, p in records.items():
        if k[3] != "proportional":
            continue
        r = records[k[:3] + ("relay", k[4])]
        for field in ["mask_sha256", "uniform_sha256", "input_map_sha256", "calibration_sha256", "trigger_ms", "burst_delay_ms", "burst_duration_ms"]:
            assert p[field] == r[field], (k, field)
        t = p["trigger_ms"]
        for pq, rq in zip(p["log"], r["log"]):
            if pq["t_end_ms"] <= t:
                assert all(pq[field] == rq[field] for field in prefix_fields), k
                # The command first computed AT crossing can differ by law;
                # it only acts in the next frame, after the shared prefix.
                if pq["t_end_ms"] < t:
                    assert pq["next_omega"] == rq["next_omega"], k
        pr.append(dict(RF=k[0], seed=k[1], bearing_deg=k[2], fault=k[4],
                       trigger_ms=t, onset_ms=t+250, planned_burst_end_ms=t+700,
                       P_contact_ms=p["collision_ms"], R_contact_ms=r["collision_ms"],
                       task_discordant=p["escaped"] != r["escaped"]))
    assert len(pr) == 288 and sum(x["task_discordant"] for x in pr) == 15

    # A: choose a timing-vector example without looking at its outcome.
    contexts = sorted({(k[1], k[2]) for k in records if k[0] == "RF-0" and k[3] == "proportional"})
    candidates_a = []
    for seed, bearing in contexts:
        rr = {f: records[("RF-0", seed, bearing, "proportional", f)] for f in ["healthy", "F2_25", "F2_50"]}
        candidates_a.append(dict(seed=seed, bearing_deg=bearing,
                                 delay25_ms=rr["F2_25"]["trigger_ms"]-rr["healthy"]["trigger_ms"],
                                 delay50_ms=rr["F2_50"]["trigger_ms"]-rr["healthy"]["trigger_ms"]))
    means = [statistics.mean(x[f] for x in candidates_a) for f in ["delay25_ms", "delay50_ms"]]
    for item in candidates_a:
        item["squared_distance_to_mean_ms2"] = (item["delay25_ms"]-means[0])**2 + (item["delay50_ms"]-means[1])**2
    chosen_a = min(candidates_a, key=lambda x: (x["squared_distance_to_mean_ms2"], x["seed"], x["bearing_deg"]))
    a_keys = [("RF-0", chosen_a["seed"], chosen_a["bearing_deg"], "proportional", f) for f in ["healthy", "F2_25", "F2_50"]]

    # B: median first-contact example among RF-0 50% P/R discordances.
    candidates_b = [x for x in pr if x["RF"] == "RF-0" and x["fault"] == "F2_50" and x["task_discordant"] and x["P_contact_ms"] is not None]
    median_contact = statistics.median(x["P_contact_ms"] for x in candidates_b)
    chosen_b = min(candidates_b, key=lambda x: (abs(x["P_contact_ms"]-median_contact), x["seed"], x["bearing_deg"]))
    b_keys = [("RF-0", chosen_b["seed"], chosen_b["bearing_deg"], law, "F2_50") for law in ["proportional", "relay"]]
    if 900 < chosen_b["P_contact_ms"] < 1000:
        c_key, reused_c = b_keys[0], True
    else:
        late = [k for k, raw in records.items() if k[0] == "RF-0" and k[3:] == ("proportional", "F2_50") and raw["collision_ms"] is not None and 900 < raw["collision_ms"] < 1000]
        median_late = statistics.median(records[k]["collision_ms"] for k in late)
        c_key = min(late, key=lambda k: (abs(records[k]["collision_ms"]-median_late), k[1], k[2]))
        reused_c = False
    selected = list(dict.fromkeys(a_keys+b_keys+[c_key]))

    def identifier(k):
        return f"{k[0]}-s{k[1]}-b{k[2]:g}-{k[3]}-{k[4]}"

    # Additional independent input/plant replay is run for every selected source.
    uniforms_cache = {}
    exported = {}
    for k in selected:
        raw, rf = records[k], k[0]
        cal = calibrations[rf]
        input_map = read(root / raw_info[k]["input_map_source"])
        ukey = (k[1], len(input_map["pool_flyids"]))
        if ukey not in uniforms_cache:
            uniforms = [task.input_uniforms(k[1], frame, ukey[1]) for frame in range(50)]
            h = hashlib.sha256()
            for u in uniforms:
                h.update(u.tobytes())
            uniforms_cache[ukey] = (uniforms, h.hexdigest())
        uniforms, uniform_digest = uniforms_cache[ukey]
        independent.check_record(raw, cal, input_map, uniforms, uniform_digest)
        fly = np.zeros(2)
        target = .25*np.array([np.cos(np.radians(k[2])), np.sin(np.radians(k[2]))])
        heading, omega, trigger, segments = 0., 0., None, []
        for frame in raw["log"]:
            for observed in frame["segments"]:
                t0, t1 = observed["start_ms"], observed["end_ms"]
                fly0, target0, heading0 = fly.copy(), target.copy(), heading
                fly, target, heading, computed = task.motion(fly, target, heading, omega, t0, t1, trigger)
                assert len(computed) == 1
                close(computed[0]["min_distance"], observed["min_distance"])
                assert computed[0]["contact_ms"] == observed["contact_ms"]
                segments.append(dict(t0=t0, t1=t1, fly0=fly0.tolist(), fly1=fly.tolist(),
                                     target0=target0.tolist(), target1=target.tolist(),
                                     heading0=float(np.degrees(heading0)), heading1=float(np.degrees(heading)),
                                     omega_deg_s=omega, burst=observed["burst"],
                                     contact_ms=observed["contact_ms"], min_distance_m=observed["min_distance"]))
            close(fly, frame["fly"]);close(target, frame["target"]);close(np.degrees(heading), frame["heading_deg"])
            omega, trigger = frame["next_omega"], frame["trigger_ms"]
        contact = raw["collision_ms"]
        if contact is not None:
            segment = next(s for s in segments if s["t0"] <= contact <= s["t1"])
            fraction = (contact-segment["t0"])/(segment["t1"]-segment["t0"])
            fp = np.array(segment["fly0"])+fraction*(np.array(segment["fly1"])-segment["fly0"])
            tp = np.array(segment["target0"])+fraction*(np.array(segment["target1"])-segment["target0"])
            close(np.linalg.norm(tp-fp), .05, 1e-10)
        mean400 = sum(sum(q["cmd_rates"])*.02 for q in raw["log"] if 100 < q["t_end_ms"] <= 400)/(8*.3)
        t = raw["trigger_ms"]
        meta = dict(id=identifier(k), RF=rf, seed=k[1], bearing_deg=k[2], law=k[3], condition=k[4],
                    condition_label={"healthy": "Healthy", "F2_25": "25% row deletion", "F2_50": "50% row deletion"}[k[4]],
                    control_label={"proportional": "Proportional (P)", "relay": "Relay (R)"}[k[3]],
                    source_commit=COMMIT, **raw_info[k], source_url=f"{REPOSITORY}/blob/{COMMIT}/{raw_info[k]['source']}",
                    mask_sha256=raw["mask_sha256"], uniform_sha256=raw["uniform_sha256"],
                    input_map_sha256=raw["input_map_sha256"], calibration_sha256=raw["calibration_sha256"],
                    trigger_ms=t, onset_ms=t+250, planned_burst_end_ms=t+700,
                    B_ms=t+700, actual_burst_end_ms=t+700 if t+700 <= 1000 else None,
                    contact_ms=contact, first_contact_ms=contact, horizon_ms=1000,
                    contact_free_at_900_ms=alive_at(raw,900), contact_free_through_1000_ms=raw["escaped"],
                    trigger_threshold_hz=cal["trigger_hz"], theta=cal["trigger_hz"],
                    command_warning_400=dict(window_ms=400, mean_rate_hz=mean400,
                        cutoff_hz=registrations[rf]["thresholds"]["command_lower_hz"],
                        flagged=mean400 < registrations[rf]["thresholds"]["command_lower_hz"]),
                    illustrative_example=True, coordinate_units="m", time_units="ms", heading_units="degrees",
                    contact_rule="Center separation <= 0.05 m; decorative icons do not define radius",
                    interpolation="Positions only: affine interpolation inside verified original subsegments. Hold heading0 until t1; then apply heading1.",
                    post_contact_display="Hold pose at exact first contact, latch label, omit counterfactual post-contact motion.",
                    segments=segments,
                    command_times_ms=[0]+[q["t_end_ms"] for q in raw["log"]],
                    command_hz=[0]+[q["cmd_hz"] for q in raw["log"]],
                    raw_command_hz=[0]+[float(np.mean(q["cmd_rates"])) for q in raw["log"]],
                    logged_heading_deg=[0]+[q["heading_deg"] for q in raw["log"]],
                    logged_t_ms=[0]+[q["t_end_ms"] for q in raw["log"]],
                    event=dict(cue_ms=100, neural_trigger_ms=t, action_start_ms=t+250, burst_end_ms=t+700, first_contact_ms=contact, horizon_ms=1000),
                    verification=dict(original_reconstruct_passed=True, independent_input_and_plant_replay_passed=True,
                                      exact_contact_distance_checked=contact is not None))
        filename = "data/"+meta["id"]+".json"
        dump_new(out / filename, meta)
        exported[k] = {q: meta[q] for q in ["id","RF","seed","bearing_deg","law","condition","source","source_sha256","trigger_ms","onset_ms","B_ms","contact_ms","contact_free_at_900_ms","contact_free_through_1000_ms","illustrative_example"]}
        exported[k].update(replay_file=filename, replay_sha256=sha(out / filename))

    delay_summary, horizon_summary, warnings = [], [], {}
    for rf in CONFIGS:
        hf = [k for k in records if k[0] == rf and k[3] == "proportional" and k[4] == "healthy"]
        for fault in ["F2_25", "F2_50"]:
            values = [records[k[:4]+(fault,)]["trigger_ms"]-records[k]["trigger_ms"] for k in hf]
            delay_summary.append(dict(RF=rf, fault=fault, n_bearing_pairs=len(values), seed_clusters=len({k[1] for k in hf}),
                                      mean_ms=statistics.mean(values), sd_ms=statistics.stdev(values), median_ms=statistics.median(values),
                                      minimum_ms=min(values), maximum_ms=max(values), earlier=sum(v<0 for v in values),
                                      tied=sum(v==0 for v in values), later=sum(v>0 for v in values), P_R_duplicates_counted_once=True))
        for horizon in [900,1000]:
            for law in ["proportional","relay"]:
                rows = [raw for k,raw in records.items() if k[0] == rf and k[3:] == (law,"F2_50")]
                horizon_summary.append(dict(RF=rf,law=law,horizon_ms=horizon,contact_free=sum(alive_at(r,horizon) for r in rows),n=len(rows)))
        confusion = Counter()
        for k,raw in records.items():
            if k[0] != rf:continue
            mean400=sum(sum(q["cmd_rates"])*.02 for q in raw["log"] if 100<q["t_end_ms"]<=400)/(8*.3)
            flag=mean400<registrations[rf]["thresholds"]["command_lower_hz"]
            hit=raw["collision_ms"] is not None
            confusion["tp" if flag and hit else "fp" if flag else "fn" if hit else "tn"]+=1
        expected=summaries[rf]["warning_scores"]["transmission"]["all"]
        assert all(confusion[n] == expected[n] for n in ["tp","fp","fn","tn"])
        warnings[rf]=dict(source=CONFIGS[rf][0],source_sha256=sha(root/CONFIGS[rf][0]),
                          independently_recomputed_command_confusion=dict(confusion),
                          criteria={name:value["all"] for name,value in summaries[rf]["warning_scores"].items()})
    summary=dict(source_commit=COMMIT,source_pdf_sha256=scope["candidate_pdf_sha256"],frozen_records=576,
                 independent_seed_clusters={rf:len({k[1] for k in records if k[0]==rf}) for rf in CONFIGS},
                 paired_trigger_delays=delay_summary,P_R_pairs=288,P_R_shared_schedules=288,P_R_distinct_task_outcomes=15,
                 horizon_counts_50pct=horizon_summary,warning_scores=warnings,
                 warning_definition="Frozen 400-ms command-rate criterion compared with later first contact; all healthy/25%/50% core trials retained.",
                 checker_evidence=dict(source="audit/v10/evidence-05/check.json",sha256=sha(root/"audit/v10/evidence-05/check.json"),
                                       challenge_counts_per_adapter={"common":11,"native":3},population_coverage_claim=False),
                 classification="Retrospective descriptive re-use of frozen records; no new samples, training, fitting or hypothesis tests",
                 input_sha256=input_hashes)
    dump_new(out / "summary.json",summary)
    manifest=dict(source_commit=COMMIT,source_branch="artifact/iscas2027-v10.1-timing",main_baseline="8463020054538e8b9989c0ee8848047d833c4a0c",
                  selection_rules={
                      "A":"RF-0 proportional: minimize squared Euclidean distance of (25%-healthy,50%-healthy) trigger delays to the complete 48-context mean vector; tie ascending seed, then bearing; no outcome-based filtering.",
                      "B":"RF-0 50% deletion: among P-contact/R-contact-free discordant pairs, minimize distance to the median P first-contact time of those pairs; tie ascending seed, then bearing.",
                      "C":"Reuse B proportional record when 900 < first contact < 1000 ms; otherwise choose the median-contact example among RF-0 proportional 50% late-contact records, with seed/bearing tie-break."},
                  example_scope="Illustrative examples selected retrospectively for explanation, not estimates of population incidence or isolated mechanisms.",
                  A=dict(records=[exported[k] for k in a_keys],target_delay_vector_ms=means,selected_score=chosen_a["squared_distance_to_mean_ms2"],candidates=candidates_a),
                  B=dict(records=[exported[k] for k in b_keys],median_P_contact_ms=median_contact,candidates=candidates_b,
                         same_mask=True,same_uniforms=True,same_input_map=True,same_calibration=True,same_schedule=True,pretrigger_prefix_identical=True),
                  C=dict(records=[exported[c_key]],reuses_B_proportional=reused_c),
                  exports=[exported[k] for k in selected],
                  replay_code_sha256={p:sha(root/p) for p in ["sim_vision/task_v9.py","tools/analyze_burst_end.py","tools/replay_audit_v9.py"]},
                  pipeline_sha256=sha(__file__),runtime=dict(python=platform.python_version(),numpy=np.__version__),
                  all_576_source_hashes_verified=True,all_576_geometry_reconstructed=True,all_288_P_R_prefixes_verified=True,
                  selected_sources_independently_replayed=len(selected),
                  physical_model=dict(radius_m=.05,frame_ms=20,walk_m_s=.05,burst_m_s=.35,pursuer_m_s=.3,delay_ms=250,burst_duration_ms=450,horizon_ms=1000),
                  rendering_contract=dict(position_rule="Affine only within original validated linear subsegments",heading_rule="Hold segment-start heading until original segment end",post_contact_rule="Freeze exact first-contact pose; no counterfactual suffix motion",icons_are_decorative=True))
    dump_new(out / "examples.json",manifest)
    # Read-only input contract: no selected source changed during the operation.
    for name,h in input_hashes.items():assert sha(root/name)==h
    print(json.dumps(dict(passed=True,records=576,selected={name:[r['id'] for r in manifest[name]['records']] for name in ['A','B','C']},
                          A_delays=chosen_a,B_contact_ms=chosen_b["P_contact_ms"],exported_sources=len(selected)),indent=2))


if __name__ == "__main__":
    main()
