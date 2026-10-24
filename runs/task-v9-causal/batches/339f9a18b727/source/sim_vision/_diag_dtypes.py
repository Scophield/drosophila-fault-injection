import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import vision_core as vc
from brian2 import ms, Hz
from encoder import load_sensory
from run_openloop import get_dn_sides

orig_loader = vc._load_edges_lean
mode = sys.argv[1] if len(sys.argv) > 1 else "int64f64"

def loader64():
    i_pre, i_post, w0 = orig_loader()
    return i_pre.astype(np.int64), i_post.astype(np.int64), w0.astype(np.float64)

if "int64" in mode:
    vc._load_edges_lean = loader64

sim = vc.VisionSim()
sens = load_sensory()
sim.arm_stim_weights(sens.root_id.tolist())
sim.reset_state()
base = np.zeros(len(sim.pool_flyids))
base[[sim.pool_pos[int(f)] for f in sim.sens_flyids]] = 150.0
sim.stim.rates = base * Hz
sim.net.run(600 * ms)
print(json.dumps({"mode": mode, "n_total": int(sim.mon_all.num_spikes)}))
