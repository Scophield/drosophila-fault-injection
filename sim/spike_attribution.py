import numpy as np

from engine import FlyBrainSim, get_type_ids

ids = get_type_ids()
exc = ids["LC4"] + ids["LPLC2"]


def split(sim, sensory_idx, label):
    i = np.asarray(sim.mon_ro.i[:])
    m = np.isin(i, list(sensory_idx))
    print(f"{label}: sensory={int(m.sum())} rest={int((~m).sum())} total={len(i)}")


sim = FlyBrainSim()
sensory_idx = np.asarray(sorted(sim.flyid2i[int(f)] for f in exc))
sim.trial(exc, 600, 150)
split(sim, sensory_idx, "healthy")
w = sim.w0.copy()
w[sim.out_mask(sim.flyid2i[int(f)] for f in exc)] = 0.0
sim.trial(exc, 600, 150, w_fault=w)
split(sim, sensory_idx, "F5_both")
del sim

i_pre, i_post, _ = __import__("engine").load_edges()
rng_er = np.random.default_rng(17)
sim_er = FlyBrainSim(j_override=rng_er.permutation(i_post))
sensory_idx_er = np.asarray(sorted(sim_er.flyid2i[int(f)] for f in exc))
sim_er.trial(exc, 600, 150)
split(sim_er, sensory_idx_er, "ER healthy")
