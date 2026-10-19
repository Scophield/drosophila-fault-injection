import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from encoder import load_sensory, build_rf_map, loom_trajectory, encode_rates, encode_none, FRAME_DT_MS
from vision_core import VisionSim
from run_openloop import get_dn_sides, PARAMS

OUT = Path(__file__).resolve().parent / "results_vision"
K_TURN_DEG_S = 400.0
V_FLY = 0.05
D_CONTACT = 0.05
D0 = 0.25
V_TARGET = 0.3
EP_DUR_MS = 1000.0
V_BURST = 0.35
BURST_S = 0.45
BURST_DELAY_MS = 250.0
THETA_HZ = 51.4
SMOOTH_N = 5


def load_calib():
    return json.loads((OUT / "calib.json").open().read())


def frame_lr_diff(rec, t0_ms, t1_ms, cmd_df, sim):
    t = rec["t_ms"]
    m = (t >= t0_ms) & (t < t1_ms)
    idx = rec["i"][m]
    val = 0.0
    for ct in ["DNp01", "DNa02", "DNp04", "DNb01"]:
        for side in ["left", "right"]:
            fids = cmd_df[(cmd_df.cell_type == ct) & (cmd_df.side == side)].flyid.tolist()
            n = int(np.isin(idx, np.asarray([sim.flyid2i[f] for f in fids], dtype=np.int64)).sum())
            r = n / ((t1_ms - t0_ms) / 1000.0)
            val += r if side == "left" else -r
    return val


def run_episode(sim, rf_map, cmd_df, seed, phi_t_deg, fault=None, mode="brain"):
    rng = np.random.default_rng(10_000 + seed)
    sim.reset_state()
    w_fault = None
    if fault is not None:
        w_fault = build_fault(sim, fault, rng)
        if w_fault is not None:
            sim.apply_weights(w_fault)
    n_frames = int(round(EP_DUR_MS / FRAME_DT_MS))
    fly_x, fly_y, heading = 0.0, 0.0, 0.0
    tx, ty = D0 * np.cos(np.radians(phi_t_deg)), D0 * np.sin(np.radians(phi_t_deg))
    radius = PARAMS["r_ref_m"]
    lr_hist = []
    cmd_hist = []
    burst_until = -1.0
    log = []
    t_ms = 0.0
    total_spikes = 0
    for k in range(n_frames):
        dx, dy = tx - fly_x, ty - fly_y
        dist = max(np.hypot(dx, dy), 0.02)
        phi_now = np.degrees(np.arctan2(dy, dx)) - np.degrees(heading)
        phi_now = (phi_now + 180.0) % 360.0 - 180.0
        tr = loom_trajectory(radius, V_TARGET, FRAME_DT_MS * (k + 1), PARAMS["t_start_ms"])
        u_frame = tr["u"][-1]
        half_angle = tr["half_angle_deg"][-1]
        phi_abs = (np.degrees(heading) + phi_now + 180.0) % 360.0 - 180.0
        rates = np.zeros(len(rf_map))
        if u_frame > 0:
            dphi = np.radians(rf_map["phi_deg"].to_numpy() - phi_abs)
            dpsi = np.radians(rf_map["psi_deg"].to_numpy() - PARAMS["psi_ref_deg"])
            sig = np.radians(max(30.0, half_angle))
            rates = np.minimum(150.0 * rf_map["w_grad"].to_numpy() * np.exp(-(dphi**2 + dpsi**2) / (2 * sig**2)) * u_frame, 150.0)
        t0 = sim.mon_all.num_spikes
        sim.set_frame_rates(rates)
        sim.run_frame(FRAME_DT_MS)
        total_spikes = sim.mon_all.num_spikes
        rec = sim.spike_records(cmd_df.flyid.tolist())
        lr = frame_lr_diff(rec, t_ms, t_ms + FRAME_DT_MS, cmd_df, sim)
        lr_hist.append(lr)
        lr_s = float(np.mean(lr_hist[-SMOOTH_N:]))
        m = (rec["t_ms"] >= t_ms) & (rec["t_ms"] < t_ms + FRAME_DT_MS)
        idx_f = rec["i"][m]
        cmd_rates = {}
        cmd_sum = 0.0
        for ct in ["DNp01", "DNa02", "DNp04", "DNb01"]:
            for side in ["left", "right"]:
                fids = cmd_df[(cmd_df.cell_type == ct) & (cmd_df.side == side)].flyid.tolist()
                n = int(np.isin(idx_f, np.asarray([sim.flyid2i[f] for f in fids], dtype=np.int64)).sum())
                r = n / (FRAME_DT_MS / 1000.0)
                cmd_rates[f"{ct}_{side}"] = r
                cmd_sum += r
        if mode == "brain":
            c = load_calib()
            omega = -K_TURN_DEG_S * np.clip(c["data_sign"] * (lr_s - c["bias"]) / c["lr_ref"], -1.0, 1.0)
        elif mode == "silence":
            omega = 0.0
        elif mode == "flip":
            c = load_calib()
            omega = K_TURN_DEG_S * np.clip(c["data_sign"] * (lr_s - c["bias"]) / c["lr_ref"], -1.0, 1.0)
        elif mode == "handrule":
            omega = -K_TURN_DEG_S * np.clip(phi_now / 60.0, -1.0, 1.0)
        cmd_hist.append(cmd_sum)
        cmd_s = float(np.mean(cmd_hist[-SMOOTH_N:]))
        if cmd_s >= THETA_HZ and burst_until < 0.0:
            if len(cmd_hist) >= 2 and cmd_hist[-2] >= THETA_HZ:
                burst_until = t_ms + BURST_DELAY_MS + BURST_S * 1000.0
        bursting = (t_ms >= burst_until - BURST_S * 1000.0) and (t_ms < burst_until) and burst_until > 0.0
        v_now = V_BURST if bursting else V_FLY
        if not bursting:
            heading += np.radians(omega) * (FRAME_DT_MS / 1000.0)
        fly_x += v_now * np.cos(heading) * (FRAME_DT_MS / 1000.0)
        fly_y += v_now * np.sin(heading) * (FRAME_DT_MS / 1000.0)
        gapx, gapy = fly_x - tx, fly_y - ty
        gap = max(np.hypot(gapx, gapy), 1e-9)
        tx += gapx / gap * V_TARGET * (FRAME_DT_MS / 1000.0)
        ty += gapy / gap * V_TARGET * (FRAME_DT_MS / 1000.0)
        log.append({"k": k, "t_ms": t_ms, "fly_x": fly_x, "fly_y": fly_y, "heading_deg": np.degrees(heading),
                    "target_x": tx, "target_y": ty, "dist": float(np.hypot(fly_x - tx, fly_y - ty)),
                    "phi_now": phi_now, "phi_abs": phi_abs, "lr_s": lr_s, "omega": omega, "u": float(u_frame), "half_angle": float(half_angle),
                    "n_total": int(total_spikes), "cmd_rates": cmd_rates, "cmd_s": cmd_s, "burst": bool(bursting)})
        t_ms += FRAME_DT_MS
        if np.hypot(fly_x - tx, fly_y - ty) <= D_CONTACT:
            break
    min_dist = min(r["dist"] for r in log)
    return {"seed": seed, "phi_t_deg": phi_t_deg, "mode": mode, "fault": fault, "min_dist": min_dist,
            "escaped": bool(min_dist > D_CONTACT), "n_total": int(total_spikes), "log": log}


def build_fault(sim, fault, rng):
    w0 = sim.w0
    if fault == "F2_25":
        drop = rng.random(len(w0)) < 0.25
        return np.where(drop, 0.0, w0)
    if fault == "F2_50":
        drop = rng.random(len(w0)) < 0.50
        return np.where(drop, 0.0, w0)
    if fault == "F4_1pct":
        exc = set(int(f) for f in sim.sens_flyids)
        ro = set()
        import pandas as pd
        from run_openloop import get_dn_sides
        cmd_df, dn_all = get_dn_sides()
        ro = set(cmd_df.flyid.tolist())
        pool = np.asarray([i for i, f in sim.i2flyid.items() if f not in exc and f not in ro], dtype=np.int64)
        outdeg = np.bincount(sim._pre_idx, weights=sim.w0 / 2.75e-4, minlength=sim.n_neurons)
        cand = np.argsort(-outdeg[pool])[: int(round(0.01 * len(pool)))]
        hub = set(pool[cand].tolist())
        w = w0.copy()
        for k in range(len(sim._pre_idx)):
            if sim._pre_idx[k] in hub:
                w[k] = 0.0
        return w
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="brain")
    ap.add_argument("--phis", default="-60,-30,0,30,60")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--faults", default="")
    ap.add_argument("--tag", default="closedloop")
    args = ap.parse_args()
    df_sens = load_sensory()
    rf_map = build_rf_map(df_sens)
    cmd_df, dn_all = get_dn_sides()
    sim = VisionSim()
    sim.arm_stim_weights(rf_map.root_id.tolist())
    phis = [float(x) for x in args.phis.split(",")]
    seeds = [int(x) for x in args.seeds.split(",")]
    modes = args.modes.split(",")
    faults = [f if f != "none" else None for f in args.faults.split(",")] if args.faults else [None]
    rows = []
    for mode in modes:
        for fault in faults:
            for phi in phis:
                for seed in seeds:
                    res = run_episode(sim, rf_map, cmd_df, seed, phi, fault=fault, mode=mode)
                    rows.append({k: v for k, v in res.items() if k != "log"})
                    (OUT / f"episodes_{args.tag}").mkdir(exist_ok=True)
                    with (OUT / f"episodes_{args.tag}" / f"{mode}_{fault or 'healthy'}_phi{int(phi)}_s{seed}.json").open("w") as fh:
                        json.dump(res, fh)
                    print(json.dumps({k: rows[-1][k] for k in ("mode", "fault", "phi_t_deg", "seed", "min_dist", "escaped", "n_total")}), flush=True)
    out = OUT / f"closedloop_{args.tag}_{args.modes.replace(',', '_')}{'_' + args.faults.replace(',', '_') if args.faults else ''}.jsonl"
    with out.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} -> {out}")


if __name__ == "__main__":
    main()
