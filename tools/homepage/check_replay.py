"""Independently check animation frame states against the frozen replay exports.

Read-only by default. --out creates one NEW JSON result and never overwrites it.
No neural dynamics, model training, input edits or media rendering are performed.
"""
from pathlib import Path
import argparse
import bisect
import csv
import hashlib
import importlib.util
import json
import math
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_state(record, simulation_ms):
    contact = record["contact_ms"]
    shown = min(simulation_ms, contact) if contact is not None else simulation_ms
    segment = next((s for s in record["segments"] if s["t0"] <= shown < s["t1"]), record["segments"][-1])
    fraction = (shown-segment["t0"])/(segment["t1"]-segment["t0"])
    points = [a+(b-a)*fraction for a,b in zip(segment["fly0"]+segment["target0"], segment["fly1"]+segment["target1"])]
    heading = segment["heading1"] if shown == segment["t1"] else segment["heading0"]
    return shown, points, heading


def expected_clock(wall, knots):
    for (w0,t0),(w1,t1) in zip(knots[:-1],knots[1:]):
        if wall <= w1+1e-10:
            fraction = max(0.,min(1.,(wall-w0)/(w1-w0)))
            return t0+fraction*(t1-t0), (t1-t0)/(w1-w0)/1000
    return knots[-1][1], 0.


class LineCapture:
    def __init__(self):
        self.lines = []

    def line(self, points, color=None, width=1):
        self.lines.append((points,color,width))

    def text(self, *args, **kwargs):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--examples", type=Path, default=Path("docs/homepage-animation/examples.json"))
    ap.add_argument("--media", type=Path, default=Path("media/paper-v10.1"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.out and args.out.exists():
        raise FileExistsError(args.out)
    examples = json.loads(args.examples.read_text())
    manifest = json.loads((args.media/"render-manifest.json").read_text())
    renderer_path = Path(__file__).resolve().parent/"render.py"
    assert sha(renderer_path) == manifest["renderer_sha256"]
    assert sha(args.examples) == manifest["example_manifest_sha256"]
    records = {}
    for item in examples["exports"]:
        path = args.examples.parent/item["replay_file"]
        assert sha(path) == item["replay_sha256"]
        record = json.loads(path.read_text())
        assert record["id"] == item["id"] and record["source_sha256"] == item["source_sha256"]
        records[item["id"]] = record
    results, total_rows = [], 0
    max_position_error = max_heading_error = 0.
    for clip in ["demo-a-delay","demo-b-control","demo-c-horizon"]:
        with (args.media/"qa"/(clip+"-frame-data.csv")).open(encoding="utf-8",newline="") as f:
            rows = list(csv.DictReader(f))
        info = manifest["clips"][clip]
        expected_ids = set(info["condition_ids"])
        assert len(rows) == info["frames"]*len(expected_ids)
        assert info["frames"] == round(info["duration_s"]*info["fps"])
        frames, at900, at_contact, at1000 = {}, set(), set(), set()
        for row in rows:
            frame, wall, simulation = int(row["frame"]), float(row["wall_s"]), float(row["simulation_ms"])
            record = records[row["record_id"]]
            frames.setdefault(frame,[]).append(row)
            assert abs(wall-frame/info["fps"]) < 1e-10
            time_expected, speed = expected_clock(wall,info["simulation_knots"])
            assert abs(simulation-time_expected) < 1e-9 and abs(float(row["playback_factor"])-speed) < 1e-12
            shown, points, heading = expected_state(record,simulation)
            assert abs(float(row["display_ms"])-shown) < 1e-9
            displayed = [float(row[k]) for k in ["fly_x_m","fly_y_m","pursuer_x_m","pursuer_y_m"]]
            position_error = max(abs(a-b) for a,b in zip(points,displayed))
            heading_error = abs(heading-float(row["heading_deg"]))
            max_position_error = max(max_position_error,position_error)
            max_heading_error = max(max_heading_error,heading_error)
            assert position_error < 1e-12 and heading_error < 1e-9
            separation = math.dist(displayed[:2],displayed[2:])
            assert abs(separation-float(row["separation_m"])) < 1e-12
            latched = row["contact_latched"] == "True"
            assert latched == (record["contact_ms"] is not None and simulation >= record["contact_ms"]-1e-8)
            if latched:
                assert abs(separation-.05) < 1e-10
                at_contact.add(frame)
            if abs(simulation-900) < 1e-9 and speed == 0:
                at900.add(frame)
            if abs(simulation-1000) < 1e-9:
                at1000.add(frame)
        assert set(frames) == set(range(info["frames"]))
        assert all({r["record_id"] for r in rows} == expected_ids for rows in frames.values())
        assert all(len({r["simulation_ms"] for r in rows}) == 1 for rows in frames.values())
        assert at1000 and float(frames[max(frames)][0]["simulation_ms"]) == 1000
        total_rows += len(rows)
        results.append(dict(clip=clip,frames=info["frames"],state_rows=len(rows),final_simulation_ms=1000,
                            frames_at_900_pause=len(at900),contact_latched_frames=len(at_contact),frames_at_1000_endpoint=len(at1000)))

    # Exercise the actual renderer query methods against a separate segment evaluator.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("homepage_animation_renderer",renderer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    renderer = module.Renderer(args.examples)
    assert list(renderer.bounds) == manifest["coordinate_bounds_m"]
    sampled_checks = rate_checks = curve_checks = 0
    for record in renderer.records.values():
        obj = record.r
        critical = {0.,1000.,record.trigger,record.onset,record.end}
        if record.contact is not None:
            critical.update([record.contact-1e-5,record.contact,record.contact+1e-5])
        critical.update(i/3 for i in range(3001))
        for t in sorted(x for x in critical if 0 <= x <= 1000):
            shown, points, heading = expected_state(obj,t)
            state = record.state(t)
            assert max(abs(a-b) for a,b in zip(points,state["fly"]+state["target"])) < 1e-12
            assert abs(state["heading"]-heading) < 1e-9
            sampled_checks += 1
            index = max(i for i,v in enumerate(obj["command_times_ms"]) if v <= shown+1e-10)
            assert record.rate(t) == obj["command_hz"][index]
            rate_checks += 1
        for t in [0.,100.,record.trigger,record.onset,record.end,1000.]:
            capture = LineCapture()
            box = (10.,20.,1000.,100.)
            renderer.signal(capture,record,t,box)
            actual = [p for p,color,width in capture.lines if color == module.SIGNAL and width == 2]
            assert len(actual) == 1
            shown,_,_ = expected_state(obj,t)
            points = [];last=obj["command_hz"][0]
            for when,value in zip(obj["command_times_ms"],obj["command_hz"]):
                if when > shown+1e-10:break
                if points:points.append((10.+when,20.+100.*(1-last/renderer.signalmax)))
                points.append((10.+when,20.+100.*(1-value/renderer.signalmax)));last=value
            points.append((10.+shown,20.+100.*(1-last/renderer.signalmax)))
            assert max(abs(a-b) for p,q in zip(actual[0],points) for a,b in zip(p,q)) < 1e-10
            assert len(actual[0]) == len(points)
            curve_checks += 1
    bp,br = [records[item["id"]] for item in examples["B"]["records"]]
    for field in ["mask_sha256","uniform_sha256","input_map_sha256","calibration_sha256","trigger_ms","onset_ms","B_ms"]:
        assert bp[field] == br[field]
    assert examples["C"]["records"][0]["id"] == bp["id"]
    overview = manifest["clips"]["overview"]
    assert overview["frames"] == 624 and overview["fps"] == 24 and overview["duration_s"] == 26
    result = dict(passed=True,source_commit=examples["source_commit"],renderer_sha256=manifest["renderer_sha256"],
                  example_manifest_sha256=manifest["example_manifest_sha256"],state_rows=total_rows,
                  max_position_error_m=max_position_error,max_heading_error_deg=max_heading_error,
                  sampled_state_checks=sampled_checks,post_step_rate_checks=rate_checks,post_step_curve_checks=curve_checks,
                  common_bounds_m=list(renderer.bounds),clips=results,
                  overview_manifest_frames=624,overview_manifest_fps=24,overview_manifest_duration_s=26,
                  scope="Frame-state, renderer and source-export consistency; media decoding/browser/GitHub checks are separate")
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open("x",encoding="utf-8",newline="\n") as f:
            json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
