import sys
import time
import numpy as np

from engine import FlyBrainSim, get_type_ids

set_name = sys.argv[1] if len(sys.argv) > 1 else "LC4"
r_poi = int(sys.argv[2]) if len(sys.argv) > 2 else 150
t_run = int(sys.argv[3]) if len(sys.argv) > 3 else 100
n_trial = int(sys.argv[4]) if len(sys.argv) > 4 else 2

ids = get_type_ids()
exc = ids[set_name]
ro = ids["DNp01"] + ids["DNa02"] + ids["DNp04"] + ids["DNb01"]
ro_names = {i: n for n in ["DNp01", "DNa02", "DNp04", "DNb01"] for i in ids[n]}
print(f"stim={set_name}({len(exc)}) r_poi={r_poi}Hz t_run={t_run}ms readout={len(ro)}", flush=True)

sim = FlyBrainSim()
ro_names = {int(i): n for n in ["DNp01", "DNa02", "DNp04", "DNb01"] for i in ids[n]}
for k in range(n_trial):
    t1 = time.time()
    res = sim.trial(exc, t_run=t_run, r_poi=r_poi, readout_flyids=ro)
    per = {}
    for i, t in zip(res["i"], res["t"]):
        fid = int(sim.i2flyid[int(i)])
        per[ro_names[fid]] = per.get(ro_names[fid], 0) + 1
    lat = np.min(res["t"]) if len(res["t"]) else -1
    print(f"trial{k}: wall={time.time()-t1:.1f}s total={res['n_total_spikes']} "
          f"readout={len(res['t'])} rate={len(res['t'])/(len(ro)*t_run/1000):.1f}Hz "
          f"first={lat:.1f}ms per_neuron={per}", flush=True)
