import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
import numpy as np
import vision_core as vc
vc._load_edges_lean_orig = vc._load_edges_lean
def loader64():
    i, j, w = vc._load_edges_lean_orig()
    return i.astype(np.int64), j.astype(np.int64), w.astype(np.float64)
vc._load_edges_lean = loader64
import engine as _engine
def load64(j_override=None):
    i, j, w = loader64()
    if j_override is not None:
        j = np.asarray(j_override, dtype=np.int64)
    return i, j, w
_engine.load_edges = load64
from engine import FlyBrainSim, W_IN_V
from brian2 import ms, Hz, volt
from encoder import load_sensory

sim = FlyBrainSim()
sens = load_sensory()
w = np.zeros(len(sim.pool_flyids))
for f in sens.root_id.tolist():
    w[sim.pool_pos[int(f)]] = W_IN_V
sim.net.restore("init")
sim.syn_stim.w[:] = (w * 1.0) * volt
base = np.zeros(len(sim.pool_flyids))
for f in sens.root_id.tolist():
    base[sim.pool_pos[int(f)]] = 150.0
sim.stim.rates = 150 * Hz
sim.net.run(600 * ms)
print(json.dumps({"variant": "manual_scalar_rates", "n_total": int(sim.mon_all.num_spikes)}))
