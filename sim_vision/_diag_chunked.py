import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from vision_core import VisionSim
from run_openloop import get_dn_sides
from encoder import load_sensory
from brian2 import ms, Hz

sim = VisionSim()
sens = load_sensory()
sim.arm_stim_weights(sens.root_id.tolist())
cmd_df, dn_all = get_dn_sides()
sim.reset_state()
base = np.zeros(len(sim.pool_flyids))
base[[sim.pool_pos[int(f)] for f in sim.sens_flyids]] = 150.0
sim.stim.rates = base * Hz
sim.net.run(600 * ms)
rec = sim.spike_records(cmd_df.flyid.tolist())
out = {"engine": "chunked_default", "n_total": int(sim.mon_all.num_spikes), "n_cmd": int(len(rec["t_ms"])),
       "dn_rates_Hz": round(len(rec["t_ms"]) / 0.6, 1)}
print(json.dumps(out))
