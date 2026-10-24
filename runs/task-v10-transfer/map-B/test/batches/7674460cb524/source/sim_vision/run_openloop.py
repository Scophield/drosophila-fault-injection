import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from encoder import load_sensory, build_rf_map, loom_trajectory, encode_rates, encode_none, FRAME_DT_MS
from vision_core import VisionSim
from project_paths import PATH_COMP
from run_provenance import output_dir, prepare

OUT = Path(__file__).resolve().parent / "results_vision"
PARAMS = {"d0_m": 0.25, "r_ref_m": 0.05, "v_ref_ms": 0.3, "t_start_ms": 100.0, "dur_ms": 600.0, "psi_ref_deg": 40.0, "phi_ref_deg": 0.0}


def get_dn_sides():
    import sys
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / "sim"))
    from engine import get_type_ids
    ann = pd.read_csv(ROOT / "sim" / "data" / "annotations.tsv", sep="\t", usecols=["root_id", "cell_type", "side"], low_memory=False)
    comp = pd.read_csv(PATH_COMP, index_col=0)
    ann = ann[ann.root_id.isin(set(comp.index.astype("int64")))]
    ids = get_type_ids()
    cmd = []
    for t in ["DNp01", "DNa02", "DNp04", "DNb01"]:
        for f in ids[t]:
            side = ann.loc[ann.root_id == f, "side"].iloc[0]
            cmd.append({"flyid": int(f), "cell_type": t, "side": side})
    dn_all = [int(f) for f in ids["DN_ALL"]]
    return pd.DataFrame(cmd), dn_all


def run_condition(sim, rf_map, cond, seeds, cmd_df, dn_all):
    rows = []
    for seed in seeds:
        import brian2
        brian2.seed(20000 + seed)
        rates = None
        if cond["kind"] == "none":
            rates = encode_none(rf_map, cond["dur_ms"])
        elif cond["kind"] == "static":
            tr = loom_trajectory(PARAMS["r_ref_m"] * cond["r_scale"], 0.0, cond["dur_ms"], PARAMS["t_start_ms"])
            rates = np.zeros_like(encode_rates(rf_map, tr, cond["phi_deg"], cond["psi_deg"]))
        else:
            tr = loom_trajectory(PARAMS["r_ref_m"] * cond["r_scale"], PARAMS["v_ref_ms"] * cond["v_scale"], cond["dur_ms"], PARAMS["t_start_ms"])
            rates = encode_rates(rf_map, tr, cond["phi_deg"], cond["psi_deg"])
        sim.reset_state()
        t0 = time.time()
        n_frames=int(round(cond['dur_ms']/FRAME_DT_MS))
        if len(rates)<n_frames:
            raise ValueError('insufficient stimulus frames')
        # Trajectories contain both endpoints; do not simulate the extra endpoint frame.
        for k in range(n_frames):
            sim.set_frame_rates(rates[k])
            sim.run_frame(FRAME_DT_MS)
        wall = time.time() - t0
        rec = sim.spike_records(cmd_df.flyid.tolist())
        counts_cmd = int(len(rec["t_ms"]))
        counts_all = int(sim.mon_all.num_spikes)
        n_dn_all = sim.count_dn_all(dn_all)
        rates_cmd = {}
        for ct in ["DNp01", "DNa02", "DNp04", "DNb01"]:
            for side in ["left", "right"]:
                fids = cmd_df[(cmd_df.cell_type == ct) & (cmd_df.side == side)].flyid.tolist()
                idx = np.asarray([sim.flyid2i[f] for f in fids], dtype=np.int64)
                n = int(np.isin(rec["i"], idx).sum())
                rates_cmd[f"{ct}_{side}"] = n / (cond["dur_ms"] / 1000.0)
        row = dict(cond_id=cond["id"], kind=cond["kind"], seed=seed, brian_seed=20000+seed, duration_ms=cond["dur_ms"], n_readout=len(cmd_df), wall_s=round(wall, 1),
                   n_cmd_spikes=counts_cmd, n_total_spikes=counts_all, n_dn_all=n_dn_all, **rates_cmd)
        rows.append(row)
    return rows


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    OUT = prepare(output_dir('vision_openloop'),dict(producer='run_openloop',smoke=args.smoke,
                  brian_seed_rule='20000+seed',rf_seed=20260201))
    seeds = [0, 1] if args.smoke else [0, 1, 2, 3, 4, 5]
    out_file = OUT / ("openloop_smoke.jsonl" if args.smoke else "openloop.jsonl")
    df_sens = load_sensory()
    rf_map = build_rf_map(df_sens)
    rf_map.to_csv(OUT / "rf_map.csv", index=False)
    cmd_df, dn_all = get_dn_sides()
    conditions = [
        {"id": "none", "kind": "none", "dur_ms": PARAMS["dur_ms"]},
        {"id": "static", "kind": "static", "phi_deg": 0.0, "psi_deg": PARAMS["psi_ref_deg"], "r_scale": 1.0, "dur_ms": PARAMS["dur_ms"]},
    ]
    for phi in [-60.0, -30.0, 0.0, 30.0, 60.0]:
        conditions.append({"id": f"phi_{int(phi)}", "kind": "loom", "phi_deg": phi, "psi_deg": PARAMS["psi_ref_deg"], "v_scale": 1.0, "r_scale": 1.0, "dur_ms": PARAMS["dur_ms"]})
    for psi in [-30.0, 0.0]:
        conditions.append({"id": f"psi_{int(psi)}", "kind": "loom", "phi_deg": 0.0, "psi_deg": psi, "v_scale": 1.0, "r_scale": 1.0, "dur_ms": PARAMS["dur_ms"]})
    for vs in [0.5, 2.0]:
        conditions.append({"id": f"v_{str(vs).replace('.', 'p')}", "kind": "loom", "phi_deg": 0.0, "psi_deg": PARAMS["psi_ref_deg"], "v_scale": vs, "r_scale": 1.0, "dur_ms": PARAMS["dur_ms"]})
    for rs in [0.5, 2.0]:
        conditions.append({"id": f"r_{str(rs).replace('.', 'p')}", "kind": "loom", "phi_deg": 0.0, "psi_deg": PARAMS["psi_ref_deg"], "v_scale": 1.0, "r_scale": rs, "dur_ms": PARAMS["dur_ms"]})
    if args.smoke:
        conditions = [c for c in conditions if c["id"] in ("none", "phi_0", "phi_30", "phi_-60")]
    sim = VisionSim()
    sim.arm_stim_weights(rf_map.root_id.tolist())
    all_rows = []
    for cond in conditions:
        rows = run_condition(sim, rf_map, cond, seeds, cmd_df, dn_all)
        all_rows.extend(rows)
        print(json.dumps(rows[0]))
    with open(out_file, "w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(all_rows)} rows -> {out_file}")


if __name__ == "__main__":
    main()
