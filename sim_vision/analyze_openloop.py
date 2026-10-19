import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "results_vision"
CMD_TYPES = ["DNp01", "DNa02", "DNp04", "DNb01"]


def load_runs(name="openloop.jsonl"):
    rows = [json.loads(l) for l in (OUT / name).open()]
    df = pd.DataFrame(rows)
    df["lr_diff"] = 0.0
    for ct in CMD_TYPES:
        df["lr_diff"] += df[f"{ct}_left"] - df[f"{ct}_right"]
    df["cmd_rate"] = df["n_cmd_spikes"] / 0.6
    return df


def summarize(df):
    g = df.groupby("cond_id").agg(
        cmd_med=("cmd_rate", "median"),
        lr_med=("lr_diff", "median"),
        lr_iqr_lo=("lr_diff", lambda x: np.percentile(x, 25)),
        lr_iqr_hi=("lr_diff", lambda x: np.percentile(x, 75)),
        lr_sign_consistent=("lr_diff", lambda x: (np.sign(x) == np.sign(x.median())).mean()),
        tot_med=("n_total_spikes", "median"),
        n=("seed", "count"),
    )
    return g


def main():
    df = load_runs()
    g = summarize(df)
    g.to_csv(OUT / "openloop_summary.csv")
    print(g.round(1).to_string())
    none_row = df[df.cond_id == "none"]
    print("\nnone: max cmd_rate across seeds =", none_row.cmd_rate.max())
    loom = df[df.cond_id.str.startswith("phi_")].copy()
    loom["phi"] = loom.cond_id.str.replace("phi_", "").astype(int)
    piv = loom.groupby("phi").lr_diff.agg(["median", "min", "max"])
    print("\nLR diff by azimuth (median, min, max over seeds):")
    print(piv.round(1).to_string())
    psi = df[df.cond_id.str.startswith("psi_")].copy()
    if len(psi):
        psi["elev"] = psi.cond_id.str.replace("psi_", "").astype(int)
        print("\nElevation dose (cmd_med, lr_med):")
        print(psi.groupby("elev")[["cmd_rate", "lr_diff"]].median().round(1).to_string())
    for key in ["v_0p5", "v_2p0", "r_0p5", "r_2p0"]:
        sub = df[df.cond_id == key]
        if len(sub):
            print(f"\n{key}: cmd_med={sub.cmd_rate.median():.1f} tot_med={sub.n_total_spikes.median():.0f}")


if __name__ == "__main__":
    main()
