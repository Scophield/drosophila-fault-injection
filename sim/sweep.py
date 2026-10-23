import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from engine import FlyBrainSim, get_type_ids
from hub_selection import for_sim, save_manifest
from run_provenance import output_dir, prepare

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / "results"

THETA = 51.4
T_RUN = 600
R_POI = 150
N_TRIALS = 12

LEVELS = {
    "F1_wvar": [0.05, 0.10, 0.20, 0.50],
    "F2_drop": [0.05, 0.10, 0.25, 0.50],
    "F3_loss": [0.01, 0.02, 0.05, 0.10],
}


def cond_list():
    conds = [("healthy", {})]
    for lv in LEVELS["F1_wvar"]:
        conds.append((f"F1_wvar_{int(lv*100):02d}", {"type": "wvar", "sigma": lv}))
    for lv in LEVELS["F2_drop"]:
        conds.append((f"F2_drop_{int(lv*100):02d}", {"type": "drop", "frac": lv}))
    for lv in LEVELS["F3_loss"]:
        conds.append((f"F3_loss_{int(lv*100):02d}", {"type": "loss", "frac": lv}))
    conds.append(("F4_hub_1pct", {"type": "hub", "frac": 0.01}))
    conds.append(("F4_hub_2pct", {"type": "hub", "frac": 0.02}))
    conds.append(("F4_hub_5pct", {"type": "hub", "frac": 0.05}))
    conds.append(("F5_in_LC4", {"type": "in", "which": "LC4"}))
    conds.append(("F5_in_LPLC2", {"type": "in", "which": "LPLC2"}))
    conds.append(("F5_in_both", {"type": "in", "which": "both"}))
    return conds


def trial_seed(phase, cond, k):
    h = hashlib.sha256(f"{phase}|{cond}|{k}".encode()).hexdigest()
    return int(h[:16], 16)


def apply_fault(sim, spec, exc_ids, ro_ids, rng):
    if not spec:
        return None
    t = spec["type"]
    if t == "wvar":
        sigma = spec["sigma"]
        return sim.w0 * np.exp(rng.standard_normal(sim.n_syn) * sigma - 0.5 * sigma ** 2)
    if t == "drop":
        mask = rng.random(sim.n_syn) < spec["frac"]
        w = sim.w0.copy()
        w[mask] = 0.0
        return w
    if t == "loss":
        protected = set(exc_ids) | set(ro_ids)
        pool = np.asarray([i for i, f in sim.i2flyid.items() if f not in protected], dtype=np.int64)
        k = int(round(spec["frac"] * len(pool)))
        dead = rng.choice(pool, size=k, replace=False)
        mask = sim.out_mask(dead)
        w = sim.w0.copy()
        w[mask] = 0.0
        return w
    if t == "hub":
        protected = set(exc_ids) | set(ro_ids)
        hubs = for_sim(sim, protected, spec['frac'])
        mask = sim.out_mask(hubs)
        w = sim.w0.copy()
        w[mask] = 0.0
        return w
    if t == "in":
        ids = get_type_ids()
        which = spec["which"]
        names = ["LC4", "LPLC2"] if which == "both" else [which]
        targets = [sim.flyid2i[int(f)] for n in names for f in ids[n]]
        mask = sim.out_mask(targets)
        w = sim.w0.copy()
        w[mask] = 0.0
        return w
    raise ValueError(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="real")
    ap.add_argument("--budget", type=float, default=780.0)
    ap.add_argument("--er-seed", type=int, default=17)
    ap.add_argument('--trials', type=int, default=N_TRIALS)
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()

    out_dir = prepare(output_dir('core') / args.phase,
                      dict(phase=args.phase, er_seed=args.er_seed, trials=args.trials,
                           drive_hz=R_POI, duration_ms=T_RUN, seed_rule='sha256 phase|condition|trial'), args.resume)
    ids = get_type_ids()
    exc = ids["LC4"] + ids["LPLC2"]
    ro = ids["DNp01"] + ids["DNa02"] + ids["DNp04"] + ids["DNb01"]
    ro2 = ids["DN_ALL"]
    conds = cond_list()

    if args.phase == "real":
        sim = FlyBrainSim()
    elif args.phase == "er":
        from engine import load_edges
        i_pre, i_post, _ = load_edges()
        rng_er = np.random.default_rng(args.er_seed)
        j_perm = rng_er.permutation(i_post)
        sim = FlyBrainSim(j_override=j_perm)
        with open(out_dir / "permutation.json", "w") as f:
            json.dump({"er_seed": args.er_seed, "note": "postsynaptic targets permuted, out-degree and weights preserved"}, f, indent=2)
    else:
        raise SystemExit("phase must be real or er")

    t_start = time.time()
    protected = set(exc) | set(ro)
    hub_hashes = {f: save_manifest(out_dir / f'hubs_{f}.json', sim,
                                 for_sim(sim, protected, f), protected) for f in (.01,.02,.05)}
    for cond, spec in conds:
        f_out = out_dir / f"{cond}.jsonl"
        done = set()
        if f_out.exists():
            for line in f_out.read_text().splitlines():
                if line.strip():
                    done.add(json.loads(line)["trial"])
        for k in range(args.trials):
            if k in done:
                continue
            if time.time() - t_start > args.budget:
                print(f"[budget] stopping at {cond} trial {k}", flush=True)
                return
            rng = np.random.default_rng(trial_seed(args.phase, cond, k))
            w_f = apply_fault(sim, spec, exc, ro, rng)
            t1 = time.time()
            res = sim.trial(exc, t_run=T_RUN, r_poi=R_POI, readout_flyids=ro,
                            readout2_flyids=ro2, w_fault=w_f)
            rate = len(res["t"]) / (len(ro) * T_RUN / 1000)
            lat = float(np.min(res["t"])) if len(res["t"]) else None
            n_mod = None
            if w_f is not None:
                n_mod = float(np.mean(w_f != sim.w0))
            rec = {
                'condition': cond, 'phase': args.phase, 'fault_seed': trial_seed(args.phase,cond,k),
                'hub_sha256': hub_hashes.get(spec.get('frac')) if spec.get('type') == 'hub' else None,
                "trial": k,
                "pop_rate": rate,
                "success": bool(rate >= THETA),
                "latency_ms": lat,
                "n_total_spikes": res["n_total_spikes"],
                "frac_edges_modified": n_mod,
                "dn2_n": res["dn2_n"],
                "dn2_first": res["dn2_first"],
                "dn2_counts": res["dn2_counts"],
                "t_readout": res["t"].tolist(),
                "i_readout": res["i"].tolist(),
                "wall": time.time() - t1,
            }
            with open(f_out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{cond} t{k}: rate={rate:.1f} ok={rec['success']} lat={lat} "
                  f"tot={res['n_total_spikes']} dn2={res['dn2_n']} "
                  f"mod={n_mod} ({time.time()-t1:.1f}s)", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
