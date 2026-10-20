import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from brian2 import Hz, ms

from vision_core import VisionSim
from engine import get_type_ids

OUT = Path(__file__).resolve().parent / "results_vision" / "openloop_controls"
T_RUN = 600
N_TRIALS = 12
THETA = 51.4
DRIVES = (75.0, 150.0, 300.0)


def trial_seed(cond, k):
    h = hashlib.sha256(f"ctrl|{cond}|{k}".encode()).hexdigest()
    return int(h[:16], 16)


def out_mask(sim, ids):
    m = np.zeros(sim.n_neurons, dtype=bool)
    m[np.asarray(ids, dtype=np.int64)] = True
    return m[sim._pre_idx]


class Setup:
    def __init__(self):
        self.sim = VisionSim()
        ids = get_type_ids()
        self.exc = [int(f) for f in ids["LC4"] + ids["LPLC2"]]
        self.ro = [int(f) for f in ids["DNp01"] + ids["DNa02"] + ids["DNp04"] + ids["DNb01"]]
        self.ro2 = [int(f) for f in ids["DN_ALL"]]
        self.protected = set(self.exc) | set(self.ro)
        s = self.sim
        self.w0 = s.w0.copy()
        sign_idx = np.unique(s._pre_idx, return_index=True)[1]
        self.pre_sign = np.zeros(s.n_neurons, dtype=np.int64)
        self.pre_sign[s._pre_idx[sign_idx]] = np.sign(self.w0[sign_idx]).astype(np.int64)
        self.out_deg = np.bincount(
            s._pre_idx, weights=np.abs(self.w0) / 2.75e-4, minlength=s.n_neurons
        )
        self.inh_pool = np.asarray(
            [i for i in range(s.n_neurons)
             if self.pre_sign[i] < 0 and s.i2flyid[i] not in self.protected], dtype=np.int64
        )
        self.exc_pool = np.asarray(
            [i for i in range(s.n_neurons)
             if self.pre_sign[i] > 0 and s.i2flyid[i] not in self.protected], dtype=np.int64
        )
        self.ro_idx = np.asarray([s.flyid2i[int(f)] for f in self.ro], dtype=np.int64)
        self.hubs = {}
        for frac in (0.01, 0.02):
            self.hubs[frac] = self._top_cells(int(round(frac * s.n_neurons)))

    def _top_cells(self, n):
        order = np.argsort(-self.out_deg)
        out = []
        for i in order:
            if int(i) not in self.protected:
                out.append(int(i))
            if len(out) >= n:
                break
        return np.asarray(out, dtype=np.int64)

    def hub_inh_frac(self, frac=0.01):
        h = self.hubs[frac]
        return float((self.pre_sign[h] < 0).mean())


def build(cond, st, rng):
    s = st.sim
    w = st.w0
    if cond.startswith("healthy") or cond.startswith("drive"):
        return w
    if cond.startswith("F2_50"):
        mask = rng.random(s.n_syn) < 0.50
        w = w.copy()
        w[mask] = 0.0
        return w
    if cond.startswith("F4_1"):
        w = w.copy()
        w[out_mask(s, st.hubs[0.01])] = 0.0
        return w
    if cond.startswith("F4_2"):
        w = w.copy()
        w[out_mask(s, st.hubs[0.02])] = 0.0
        return w
    if cond.startswith("EIm_1") or cond.startswith("EIm_2"):
        frac = 0.01 if cond.startswith("EIm_1") else 0.02
        h = st.hubs[frac]
        n_inh = int(round(float((st.pre_sign[h] < 0).sum())))
        n_exc = len(h) - n_inh
        pick = np.concatenate([
            rng.choice(st.inh_pool, size=n_inh, replace=False),
            rng.choice(st.exc_pool, size=n_exc, replace=False),
        ])
        w = w.copy()
        w[out_mask(s, pick)] = 0.0
        return w
    if cond.startswith("HUB_inh"):
        h = st.hubs[0.01]
        w = w.copy()
        w[out_mask(s, h[st.pre_sign[h] < 0])] = 0.0
        return w
    if cond.startswith("HUB_exc"):
        h = st.hubs[0.01]
        w = w.copy()
        w[out_mask(s, h[st.pre_sign[h] > 0])] = 0.0
        return w
    raise ValueError(cond)


def conditions():
    conds = []
    for d in DRIVES:
        sub = f"d{int(d)}"
        for base in ("healthy", "F2_50", "F4_1pct"):
            conds.append((f"{base}_{sub}", base, d))
    for base in ("EIm_1pct", "EIm_2pct", "HUB_inh", "HUB_exc"):
        conds.append((base, base, 150.0))
    return conds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--trials", type=int, default=N_TRIALS)
    ap.add_argument("--budget", type=float, default=2400.0)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    st = Setup()
    print(f"built: n_neurons={st.sim.n_neurons} hubs1={len(st.hubs[0.01])} "
          f"inh_frac={st.hub_inh_frac():.3f} inh_pool={len(st.inh_pool)} exc_pool={len(st.exc_pool)}",
          flush=True)

    t_start = time.time()
    for name, base, drive in conditions():
        if args.only and args.only not in name:
            continue
        f_out = OUT / f"{name}.jsonl"
        done = set()
        if f_out.exists():
            for line in f_out.read_text().splitlines():
                if line.strip():
                    done.add(json.loads(line)["trial"])
        for k in range(args.trials):
            if k in done:
                continue
            if time.time() - t_start > args.budget:
                print("[budget] stop", name, k, flush=True)
                return
            rng = np.random.default_rng(trial_seed(name, k))
            w_f = build(base, st, rng)
            st.sim.net.restore("init")
            st.sim.arm_stim_weights(st.exc)
            rates = np.zeros(len(st.sim.pool_flyids))
            for f in st.exc:
                rates[st.sim.pool_pos[f]] = drive
            st.sim.stim.rates = rates * Hz
            if w_f is not st.w0:
                st.sim.apply_weights(w_f)
            t1 = time.time()
            st.sim.net.run(T_RUN * ms)
            t_ms = np.asarray(st.sim.mon_ro.t[:] / ms, dtype=np.float64)
            i_sp = np.asarray(st.sim.mon_ro.i[:], dtype=np.int64)
            keep = np.isin(i_sp, st.ro_idx)
            t_ro = t_ms[keep]
            rate = len(t_ro) / (len(st.ro) * T_RUN / 1000)
            rec = {
                "trial": k,
                "cond": name,
                "base": base,
                "drive_hz": drive,
                "pop_rate": rate,
                "success": bool(rate >= THETA),
                "latency_ms": float(t_ro.min()) if len(t_ro) else None,
                "n_total_spikes": int(st.sim.mon_all.num_spikes),
                "frac_edges_modified": float(np.mean(w_f != st.w0)) if w_f is not st.w0 else None,
                "wall": time.time() - t1,
            }
            with open(f_out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{name} t{k}: rate={rate:.1f} tot={rec['n_total_spikes']} "
                  f"mod={rec['frac_edges_modified']} ({time.time()-t1:.1f}s)", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
