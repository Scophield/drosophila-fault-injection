import argparse
import json
import time
from pathlib import Path

import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sim'))
from hub_selection import for_sim, profile, save_manifest
from run_provenance import output_dir, prepare, sha256
from closedloop_protocol import (PROTOCOL_VERSION, retinal_input, segment_min_distance,
                                 frame_count, calibration_keys, validate_test_keys,
                                 validate_calibration)

OUT = Path(__file__).resolve().parent / "results_vision"
FRAME_DT_MS = 20.0
RF_SEED = 20260201
PARAMS = {'r_ref_m': 0.05, 't_start_ms': 100.0}
K_TURN_DEG_S = 400.0
V_FLY = 0.05
D_CONTACT = 0.05
D0 = 0.25
V_TARGET = 0.3
EP_DUR_MS = 1000.0
V_BURST = 0.35
BURST_S = 0.45
BURST_DELAY_MS = 250.0
HEADING_LIMIT_RAD = np.radians(100.0)

SMOOTH_N = 5


CALIBRATION = OUT / 'calib.json'


def load_calib():
    return json.loads(CALIBRATION.read_text())


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


def steering_rate(mode, lr_s, calibration, t_ms, phi_now):
    """Declared steering interventions; the neural burst trigger is separate."""
    if mode in {'brain', 'precue_gated', 'bias_only', 'flip'}:
        if mode == 'precue_gated' and t_ms < PARAMS['t_start_ms']:
            return 0.0
        readout = 0.0 if mode == 'bias_only' else lr_s
        c = calibration
        omega = -K_TURN_DEG_S * np.clip(c['data_sign'] * (readout-c['bias']) / c['lr_ref'], -1.0, 1.0)
        return -omega if mode == 'flip' else omega
    if mode in {'steer_disabled', 'readout_disabled', 'observe'}:
        return 0.0
    if mode == 'geometry_rule':
        return -K_TURN_DEG_S * (1.0 if phi_now > 0 else -1.0)
    if mode == 'handrule':
        return -K_TURN_DEG_S * np.clip(phi_now / 60.0, -1.0, 1.0)
    raise ValueError(f'unknown controller mode: {mode}')


def run_episode(sim, rf_map, cmd_df, seed, phi_t_deg, fault=None, mode="brain",
                calibration=None, duration_ms=EP_DUR_MS, threat_speed=V_TARGET,
                burst_delay_ms=BURST_DELAY_MS):
    import brian2
    brian2.seed(20_000 + seed)
    rng = np.random.default_rng(10_000 + seed)
    sim.reset_state()
    w_fault = None
    if fault is not None:
        w_fault = build_fault(sim, fault, rng)
        if w_fault is not None:
            sim.apply_weights(w_fault)
    n_frames = frame_count(duration_ms, FRAME_DT_MS)
    if mode != 'observe':
        validate_calibration(calibration)
    fly_x, fly_y, heading = 0.0, 0.0, 0.0
    tx, ty = D0 * np.cos(np.radians(phi_t_deg)), D0 * np.sin(np.radians(phi_t_deg))
    radius = PARAMS["r_ref_m"]
    lr_hist = []
    cmd_hist = []
    burst_until = -1.0
    trigger_ms = None
    log = []
    t_ms = 0.0
    total_spikes = 0
    previous_angle = None
    min_dist = D0
    collided = False
    for k in range(n_frames):
        dx, dy = tx - fly_x, ty - fly_y
        rates, stimulus = retinal_input(rf_map, (dx, dy), heading, radius,
                                        FRAME_DT_MS / 1000.0, previous_angle,
                                        threat_speed + V_FLY * np.cos(np.arctan2(dy, dx) - heading),
                                        enabled=t_ms >= PARAMS['t_start_ms'])
        previous_angle = stimulus['half_angle']
        phi_now = stimulus['phi_now']
        before = np.array([dx, dy])
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
        omega = steering_rate(mode, lr_s, calibration, t_ms, phi_now)
        cmd_hist.append(cmd_sum)
        cmd_avg = float(np.mean(cmd_hist[-SMOOTH_N:])) / len(cmd_rates)
        cmd_s = cmd_avg
        if mode == 'geometry_rule' and t_ms >= PARAMS['t_start_ms'] and burst_until < 0.0:
            trigger_ms = t_ms + FRAME_DT_MS
            burst_until = t_ms + FRAME_DT_MS + burst_delay_ms + BURST_S * 1000.0
        elif mode not in {"readout_disabled", "observe"} and cmd_avg >= calibration['theta_demo_hz'] and burst_until < 0.0:
            if len(cmd_hist) >= 2 and cmd_hist[-2] / len(cmd_rates) >= calibration['theta_demo_hz']:
                trigger_ms = t_ms + FRAME_DT_MS
                burst_until = t_ms + FRAME_DT_MS + burst_delay_ms + BURST_S * 1000.0
        bursting = (t_ms >= burst_until - BURST_S * 1000.0) and (t_ms < burst_until) and burst_until > 0.0
        v_now = V_BURST if bursting else V_FLY
        if not bursting:
            heading_new = heading + np.radians(omega) * (FRAME_DT_MS / 1000.0)
            heading = np.clip(heading_new, -HEADING_LIMIT_RAD, HEADING_LIMIT_RAD)
        fly_x += v_now * np.cos(heading) * (FRAME_DT_MS / 1000.0)
        fly_y += v_now * np.sin(heading) * (FRAME_DT_MS / 1000.0)
        gapx, gapy = fly_x - tx, fly_y - ty
        gap = max(np.hypot(gapx, gapy), 1e-9)
        tx += gapx / gap * threat_speed * (FRAME_DT_MS / 1000.0)
        ty += gapy / gap * threat_speed * (FRAME_DT_MS / 1000.0)
        step_min = segment_min_distance(before, (tx - fly_x, ty - fly_y))
        min_dist = min(min_dist, step_min)
        log.append({"k": k, "t_ms": t_ms, "t_end_ms": t_ms + FRAME_DT_MS,
                    "fly_x": fly_x, "fly_y": fly_y, "heading_deg": np.degrees(heading),
                    "target_x": tx, "target_y": ty, "dist": float(np.hypot(fly_x - tx, fly_y - ty)),
                    "phi_now": phi_now, "lr_s": lr_s, "omega": omega, "u": stimulus['u'], "half_angle": stimulus['half_angle'],
                    "step_min_dist": step_min,
                    "n_total": int(total_spikes), "cmd_rates": cmd_rates, "cmd_s": cmd_s, "burst": bool(bursting)})
        t_ms += FRAME_DT_MS
        if step_min <= D_CONTACT:
            collided = True
            break
    return {"seed": seed, "phi_t_deg": phi_t_deg, "mode": mode, "fault": fault, "min_dist": min_dist,
            "escaped": not collided, "n_total": int(total_spikes), "log": log,
            "duration_ms": t_ms, "horizon_ms": duration_ms, "frame_dt_ms": FRAME_DT_MS,
            "termination_reason": 'collision' if collided else 'horizon',
            "burst_active_at_horizon": bool(not collided and bursting),
            "trigger_ms": trigger_ms,
            "protocol_version": PROTOCOL_VERSION, "endpoint": 'collision_free_fixed_horizon'}


def build_fault(sim, fault, rng):
    w0 = sim.w0
    if fault == "F2_25":
        drop = rng.random(len(w0)) < 0.25
        return np.where(drop, 0.0, w0)
    if fault == "F2_50":
        drop = rng.random(len(w0)) < 0.50
        return np.where(drop, 0.0, w0)
    if fault in ("F4_1pct", "HUB_inh", "HUB_exc"):
        from engine import get_type_ids
        ids = get_type_ids()
        protected = set(ids['LC4'] + ids['LPLC2'] + ids['DNp01'] + ids['DNa02'] + ids['DNp04'] + ids['DNb01'])
        hubs = for_sim(sim, protected, .01)
        if fault != "F4_1pct":
            _, sign = profile(sim)
            keep = sign[hubs] < 0 if fault == "HUB_inh" else sign[hubs] > 0
            hubs = hubs[keep]
        if hasattr(sim, '_hub_manifest_dir'):
            sim._last_hub_hash = save_manifest(sim._hub_manifest_dir/f'{fault}.json', sim, hubs, protected)
        w = w0.copy()
        w[np.isin(sim._pre_idx, hubs)] = 0.0
        return w
    raise ValueError(f'unknown fault: {fault}')


def main():
    global CALIBRATION
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="brain")
    ap.add_argument("--phis", default="-60,-30,0,30,60")
    ap.add_argument("--seeds", default="6,7,8,9,10,11")
    ap.add_argument("--faults", default="")
    ap.add_argument("--tag", default="closedloop")
    ap.add_argument('--calibration', type=Path, default=CALIBRATION)
    ap.add_argument('--evaluation-role', choices=['calibration', 'test'], default='test')
    ap.add_argument('--duration-ms', type=float, default=EP_DUR_MS)
    ap.add_argument('--threat-speed', type=float, default=V_TARGET)
    ap.add_argument('--burst-delay-ms', type=float, default=BURST_DELAY_MS)
    ap.add_argument('--rf-seed', type=int, default=RF_SEED)
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()
    CALIBRATION = args.calibration.resolve()
    phis = [float(x) for x in args.phis.split(',')]
    seeds = [int(x) for x in args.seeds.split(',')]
    modes = args.modes.split(',')
    allowed = {'brain', 'precue_gated', 'bias_only', 'steer_disabled', 'readout_disabled', 'flip', 'handrule', 'observe', 'geometry_rule'}
    if not set(modes) <= allowed or len(set(phis)) != len(phis) or len(set(seeds)) != len(seeds):
        raise ValueError('unknown mode or duplicate azimuths/seeds')
    frame_count(args.duration_ms, FRAME_DT_MS)
    if not all(np.isfinite(x) for x in phis + [args.threat_speed, args.burst_delay_ms]) or args.threat_speed <= 0 or args.burst_delay_ms < 0:
        raise ValueError('invalid geometry parameters')
    observing = modes == ['observe']
    if 'observe' in modes and not observing:
        raise ValueError('observe must run alone')
    if observing != (args.evaluation_role == 'calibration') or (observing and args.faults):
        raise ValueError('calibration requires observe mode without faults; other modes require test role')
    calibration = None if observing else load_calib()
    if calibration is not None:
        validate_calibration(calibration)
        if (calibration['rf_seed'] != args.rf_seed or calibration['threat_speed'] != args.threat_speed
                or calibration['frame_dt_ms'] != FRAME_DT_MS):
            raise ValueError('calibration RF seed/threat speed differ; collect a matching calibration')
        validate_test_keys(phis, seeds, calibration_keys(calibration))
    if not args.tag.replace('_','').isalnum():
        raise ValueError('tag must contain only letters, numbers and underscores')
    faults = [f if f != 'none' else None for f in args.faults.split(',')] if args.faults else [None]
    if any(f not in {None,'F2_25','F2_50','F4_1pct','HUB_inh','HUB_exc'} for f in faults):
        raise ValueError('unknown fault name')
    from encoder import load_sensory, build_rf_map
    from vision_core import VisionSim
    from run_openloop import get_dn_sides
    import hashlib
    parameters = dict(tag=args.tag,modes=args.modes,phis=args.phis,seeds=args.seeds,faults=args.faults,
                       calibration_sha256=sha256(CALIBRATION) if calibration else None,
                       protocol_version=PROTOCOL_VERSION, evaluation_role=args.evaluation_role,
                       duration_ms=args.duration_ms, threat_speed=args.threat_speed,
                       burst_delay_ms=args.burst_delay_ms, rf_seed=args.rf_seed,
                        frame_dt_ms=FRAME_DT_MS, neural_dt_ms=0.1, retinal_elevation_deg=0.0,
                       brian_seed_rule='20000+seed',fault_seed_rule='10000+seed')
    key = hashlib.sha256(json.dumps(parameters,sort_keys=True).encode()).hexdigest()[:12]
    out_dir = output_dir('vision')
    batch = prepare(out_dir/'batches'/f'{args.tag}_{key}', parameters, args.resume)
    episode_dir = out_dir/f'episodes_{args.tag}'
    episode_dir.mkdir(parents=True,exist_ok=True)
    df_sens = load_sensory()
    rf_map = build_rf_map(df_sens, seed=args.rf_seed)
    cmd_df, dn_all = get_dn_sides()
    build_started = time.perf_counter()
    sim = VisionSim()
    build_seconds = time.perf_counter()-build_started
    sim._hub_manifest_dir = out_dir/'hubs'
    sim.arm_stim_weights(rf_map.root_id.tolist())
    unknown = [m for m in modes if m not in allowed]
    if unknown:
        raise SystemExit(f"unknown mode(s) {unknown}; allowed: {sorted(allowed)}")
    rows = []
    for mode in modes:
        for fault in faults:
            for phi in phis:
                for seed in seeds:
                    episode_path = episode_dir/f"{mode}_{fault or 'healthy'}_phi{phi:g}_s{seed}.json"
                    if episode_path.exists():
                        if args.resume:
                            previous=json.loads(episode_path.read_text())
                            if previous.get('run_manifest_sha256') != sha256(batch/'run_manifest.json'):
                                raise ValueError(f'episode belongs to another configuration: {episode_path}')
                            rows.append({k:v for k,v in previous.items() if k!='log'})
                            continue
                        raise FileExistsError(f'refusing to overwrite {episode_path}')
                    episode_started = time.perf_counter()
                    res = run_episode(sim, rf_map, cmd_df, seed, phi, fault=fault, mode=mode,
                                      calibration=calibration, duration_ms=args.duration_ms,
                                      threat_speed=args.threat_speed, burst_delay_ms=args.burst_delay_ms)
                    res.update(run_seconds=time.perf_counter()-episode_started, build_seconds=build_seconds,
                               brian_seed=20000+seed,fault_seed=10000+seed,
                               evaluation_role=args.evaluation_role, rf_seed=args.rf_seed,
                               threat_speed=args.threat_speed,
                               run_manifest_sha256=sha256(batch/'run_manifest.json'),
                               calibration_sha256=parameters['calibration_sha256'],
                               hub_sha256=getattr(sim,'_last_hub_hash',None) if fault in {'F4_1pct','HUB_inh','HUB_exc'} else None)
                    rows.append({k: v for k, v in res.items() if k != "log"})
                    with episode_path.open('x') as fh:
                        json.dump(res, fh)
                    print(json.dumps({k: rows[-1][k] for k in ("mode", "fault", "phi_t_deg", "seed", "min_dist", "escaped", "n_total", "run_seconds")}), flush=True)
    out = batch/'summary.jsonl'
    with out.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} -> {out}")


if __name__ == "__main__":
    main()
