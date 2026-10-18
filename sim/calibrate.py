import json
import time
from pathlib import Path

import numpy as np

from engine import FlyBrainSim, get_type_ids

OUT = Path(__file__).parent / "results" / "calib"
OUT.mkdir(parents=True, exist_ok=True)

ids = get_type_ids()
ro = ids["DNp01"] + ids["DNa02"] + ids["DNp04"] + ids["DNb01"]
T_RUN = 600
R_POI = 150

sim = FlyBrainSim()
print("built", flush=True)

conds = {
    "healthy": ids["LC4"] + ids["LPLC2"],
    "background": [int(f) for f in sim.pool_flyids if f not in set(ids["LC4"]) | set(ids["LPLC2"])][:len(ids["LC4"]) + len(ids["LPLC2"])],
}
print(f"healthy n={len(conds['healthy'])} background n={len(conds['background'])}", flush=True)

summary = {"t_run": T_RUN, "r_poi": R_POI, "conds": {}}
for name, exc in conds.items():
    rates, lats, per_dn = [], [], {}
    for k in range(10):
        t1 = time.time()
        res = sim.trial(exc, t_run=T_RUN, r_poi=R_POI, readout_flyids=ro)
        r_pop = len(res["t"]) / (len(ro) * T_RUN / 1000)
        lat = float(np.min(res["t"])) if len(res["t"]) else None
        rates.append(r_pop)
        lats.append(lat)
        for i in res["i"]:
            fid = int(sim.i2flyid[int(i)])
            per_dn.setdefault(fid, 0)
            per_dn[fid] += 1
        np.savez(OUT / f"{name}_trial{k}.npz", t=res["t"], i=res["i"],
                 n_total=res["n_total_spikes"])
        print(f"{name} t{k}: wall={time.time()-t1:.1f}s pop_rate={r_pop:.1f}Hz "
              f"first={lat} total={res['n_total_spikes']}", flush=True)
    rates = np.asarray(rates, dtype=float)
    summary["conds"][name] = {
        "pop_rates": rates.tolist(),
        "median": float(np.median(rates)),
        "p10": float(np.percentile(rates, 10)),
        "p90": float(np.percentile(rates, 90)),
        "latencies": lats,
        "per_dn_counts": per_dn,
    }
    print(f"{name}: median={np.median(rates):.1f}Hz p10={np.percentile(rates,10):.1f} "
          f"p90={np.percentile(rates,90):.1f}", flush=True)

med_h = summary["conds"]["healthy"]["median"]
med_b = summary["conds"]["background"]["median"]
summary["threshold"] = float((med_h + med_b) / 2)
with open(OUT / "calibration.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"threshold={summary['threshold']:.1f}Hz saved", flush=True)
