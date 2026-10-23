import argparse
import json
import time
from pathlib import Path

import numpy as np
from brian2 import Hz, ms

from vision_core import VisionSim
from engine import get_type_ids
import controls_openloop as C
from run_provenance import output_dir, prepare

OUT = Path(__file__).resolve().parents[1] / "sim" / "results" / "real"
T_RUN = 600
THETA = 51.4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=12)
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()
    out = prepare(output_dir('recheck_real'), dict(producer='f4_recheck',trials=args.trials,
                  drive_hz=150,duration_ms=T_RUN,seed_rule='sha256 ctrl|condition|trial'), args.resume)

    st = C.Setup()
    st.hubs[0.05] = st._top_cells(int(round(0.05 * st.sim.n_neurons)))
    hashes = st.save_hubs(out)
    ro2 = np.asarray([st.sim.flyid2i[int(f)] for f in st.ro2], dtype=np.int64)
    print(f"hubs {[(k, len(v)) for k, v in sorted(st.hubs.items())]}", flush=True)

    for frac, name in ((None,'healthy'), (0.01, "F4_hub_1pct"), (0.02, "F4_hub_2pct"), (0.05, "F4_hub_5pct")):
        f_out = out / f"{name}.jsonl"
        done = set()
        if f_out.exists():
            for line in f_out.read_text().splitlines():
                if line.strip():
                    done.add(json.loads(line)["trial"])
        for k in range(args.trials):
            if k in done:
                continue
            rng = np.random.default_rng(C.trial_seed(name, k))
            w = st.w0.copy()
            if frac is not None:
                w[C.out_mask(st.sim, st.hubs[frac])] = 0.0
            st.sim.net.restore("init")
            st.sim.arm_stim_weights(st.exc)
            rates = np.zeros(len(st.sim.pool_flyids))
            for f in st.exc:
                rates[st.sim.pool_pos[f]] = 150.0
            st.sim.stim.rates = rates * Hz
            st.sim.apply_weights(w)
            t1 = time.time()
            st.sim.net.run(T_RUN * ms)
            t_all = np.asarray(st.sim.mon_ro.t[:] / ms, dtype=np.float64)
            i_all = np.asarray(st.sim.mon_ro.i[:], dtype=np.int64)
            keep = np.isin(i_all, st.ro_idx)
            keep2 = np.isin(i_all, ro2)
            t_ro = t_all[keep]
            uni, cnt = np.unique(i_all[keep2], return_counts=True)
            rec = {
                'fault_seed': C.trial_seed(name,k), 'hub_sha256': hashes.get(frac),
                "trial": k,
                "pop_rate": len(t_ro) / (len(st.ro) * T_RUN / 1000),
                "success": bool(len(t_ro) / (len(st.ro) * T_RUN / 1000) >= THETA),
                "latency_ms": float(t_ro.min()) if len(t_ro) else None,
                "n_total_spikes": int(st.sim.mon_all.num_spikes),
                "frac_edges_modified": float(np.mean(w != st.w0)),
                "dn2_n": int(keep2.sum()),
                "dn2_first": float(t_all[keep2].min()) if keep2.any() else None,
                "dn2_counts": {str(st.sim.i2flyid[int(i)]): int(c) for i, c in zip(uni, cnt)},
                "t_readout": t_ro.tolist(),
                "i_readout": i_all[keep].tolist(),
                "wall": time.time() - t1,
                "engine": "vision_core N_CHUNKS=8",
            }
            with open(f_out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"{name} t{k}: rate={rec['pop_rate']:.1f} tot={rec['n_total_spikes']} "
                  f"dn2={rec['dn2_n']} ({time.time()-t1:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
