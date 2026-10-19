import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_openloop import load_runs

OUT = Path(__file__).resolve().parent / "results_vision"
TRAIN_PHIS = [-60.0, -30.0]
TRAIN_V = "v_0p5"


def main():
    df = load_runs()
    phisub = df[df.cond_id.isin([f"phi_{int(p)}" for p in TRAIN_PHIS])]
    left_mean = float(phisub.lr_diff.mean())
    data_sign = -1.0 if left_mean > 0 else 1.0
    bias = float(df[df.cond_id == TRAIN_V].lr_diff.median())
    ref_pool = np.abs(phisub.lr_diff.to_numpy() - bias)
    lr_ref = float(np.percentile(ref_pool, 90))
    calib = {"data_sign": data_sign, "left_target_lr_mean": left_mean, "bias": bias, "lr_ref": lr_ref,
             "k_turn_deg_s": 400.0, "v_fly_ms": 0.05,
             "train_conditions": [f"phi_{int(p)}" for p in TRAIN_PHIS] + [TRAIN_V, "static"],
             "note": "data_sign from left-target lr mean on training conditions only; bias from v_0p5 (phi=0) training condition; frozen for all test trajectories"}
    (OUT / "calib.json").open("w").write(json.dumps(calib, indent=1))
    print(json.dumps(calib))


if __name__ == "__main__":
    main()
