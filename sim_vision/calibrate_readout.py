import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_openloop import load_runs

OUT = Path(__file__).resolve().parent / "results_vision"
TRAIN_PHIS = [-60.0, -30.0]
TRAIN_V = "v_0p5"


def calibrate_theta_demo(out_dir=OUT):
    import glob
    import numpy as np
    peaks = []
    for f in sorted(glob.glob(str(out_dir / "episodes_train" / "brain_healthy_phi-*.json"))):
        e = json.load(open(f))
        win = [q["cmd_s"] for q in e["log"] if 250 <= q["t_ms"] <= 300]
        if win:
            peaks.append(max(win))
    if not peaks:
        return None
    return float(np.median(peaks))


def main():
    df = load_runs()
    phisub = df[df.cond_id.isin([f"phi_{int(p)}" for p in TRAIN_PHIS])]
    left_mean = float(phisub.lr_diff.mean())
    data_sign = -1.0 if left_mean > 0 else 1.0
    bias = float(df[df.cond_id == TRAIN_V].lr_diff.median())
    ref_pool = np.abs(phisub.lr_diff.to_numpy() - bias)
    lr_ref = float(np.percentile(ref_pool, 90))
    theta_demo = calibrate_theta_demo()
    if theta_demo is None:
        raise SystemExit("no archived training episodes found (results_vision/episodes_train); refusing to overwrite calib.json")
    prev = None
    if (OUT / "calib.json").exists():
        prev = json.loads((OUT / "calib.json").open().read()).get("theta_demo_hz")
    if prev is not None and abs(prev - theta_demo) > 1e-9:
        print(f"[calib] theta_demo changes {prev} -> {theta_demo}")
    calib = {"data_sign": data_sign, "train_neg_phi_lr_mean": left_mean, "bias": bias, "lr_ref": lr_ref,
             "theta_demo_hz": theta_demo,
             "k_turn_deg_s": 400.0, "v_fly_ms": 0.05,
             "train_conditions": [f"phi_{int(p)}" for p in TRAIN_PHIS] + [TRAIN_V, "static"],
             "theta_source": "episodes_train/brain_healthy_phi{-60,-30}_s{0,1,2}.json, median of per-episode max cmd_avg over t in [250,300] ms",
             "note": "data_sign from neg-phi (right-field) training-condition lr mean on training conditions only; bias from v_0p5 (phi=0) training condition; frozen for all test trajectories"}
    (OUT / "calib.json").open("w").write(json.dumps(calib, indent=1))
    print(json.dumps(calib))


if __name__ == "__main__":
    main()
