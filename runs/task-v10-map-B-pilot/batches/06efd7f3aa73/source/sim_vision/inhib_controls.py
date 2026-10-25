import argparse
import json
import time
from pathlib import Path

import numpy as np
from brian2 import Hz, ms

import controls_openloop as C
from run_provenance import output_dir, prepare
from hub_selection import save_manifest

OUT = Path(__file__).resolve().parent / "results_vision" / "openloop_controls"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=12)
    ap.add_argument("--cond", nargs="*", default=["INHrand_cells", "INHrand_mass"])
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()

    if not set(args.cond) <= {'INHrand_cells','INHrand_mass'}:
        raise ValueError('unknown inhibitory control')
    out = prepare(output_dir('inhib_controls'), dict(producer='inhib_controls',trials=args.trials,
                  conditions=args.cond,seed_rule='sha256 ctrl|condition|trial'), args.resume)
    st = C.Setup()
    st.save_hubs(out)
    s = st.sim
    hub_inh = st.hubs[0.01][st.pre_sign[st.hubs[0.01]] < 0]
    mass = float(st.out_deg[hub_inh].sum())
    mean_deg = float(st.out_deg[st.inh_pool].mean())
    n_mass = int(round(mass / mean_deg))
    print(f"inh hubs {len(hub_inh)} cells, {mass:.0f} contacts; "
          f"mass-matched random inhibitory needs {n_mass} cells (mean {mean_deg:.0f} contacts/cell)", flush=True)

    for cond in args.cond:
        f_out = out / f"{cond}.jsonl"
        done = set()
        if f_out.exists():
            done = {json.loads(l)["trial"] for l in f_out.read_text().splitlines() if l.strip()}
        for k in range(args.trials):
            if k in done:
                continue
            rng = np.random.default_rng(C.trial_seed(cond, k))
            n = len(hub_inh) if cond == "INHrand_cells" else n_mass
            pick = rng.choice(st.inh_pool, size=n, replace=False)
            selection_hash = save_manifest(out/f'{cond}_trial{k}_cells.json',s,pick,st.protected)
            w = st.w0.copy()
            w[C.out_mask(s, pick)] = 0.0
            s.net.restore("init")
            s.arm_stim_weights(st.exc)
            rates = np.zeros(len(s.pool_flyids))
            for f in st.exc:
                rates[s.pool_pos[f]] = 150.0
            s.stim.rates = rates * Hz
            s.apply_weights(w)
            t1 = time.time()
            s.net.run(C.T_RUN * ms)
            t_all = np.asarray(s.mon_ro.t[:] / ms, dtype=np.float64)
            i_all = np.asarray(s.mon_ro.i[:], dtype=np.int64)
            keep = np.isin(i_all, st.ro_idx)
            rec = {
                'condition': cond, 'fault_seed': C.trial_seed(cond,k), 'selection_sha256':selection_hash,
                'matched_quantity':'expected outgoing contact mass' if cond=='INHrand_mass' else 'cell count',
                'target_contacts':mass, 'actual_contacts':int(st.out_deg[pick].sum()),
                "trial": k,
                "pop_rate": len(t_all[keep]) / (len(st.ro) * C.T_RUN / 1000),
                "n_total_spikes": int(s.mon_all.num_spikes),
                "latency_ms": float(t_all[keep].min()) if keep.any() else None,
                "frac_edges_modified": float(np.mean(w != st.w0)),
                "n_cells": int(n),
                "wall": time.time() - t1,
            }
            with open(f_out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{cond} t{k}: rate={rec['pop_rate']:.1f} tot={rec['n_total_spikes']} "
                  f"({rec['wall']:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
