import time
import resource
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, "Drosophila_brain_model")

from model import default_params, create_model, poi
from brian2 import Network, Hz, ms, prefs

prefs.codegen.target = "cython"

t0 = time.time()
neu, syn, spk_mon = create_model(
    "Drosophila_brain_model/Completeness_783.csv",
    "Drosophila_brain_model/Connectivity_783.parquet",
    default_params,
)
print(f"[build] wall={time.time()-t0:.1f}s "
      f"n_neurons={len(neu)} n_syn={len(syn)} "
      f"maxrss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6:.2f}GB", flush=True)

# stimulate 20 random presynaptic neurons (timing probe only)
rng = np.random.default_rng(0)
exc_idx = rng.choice(len(neu), 20, replace=False)
pois, neu = poi(neu, list(exc_idx), [], default_params)

net = Network(neu, syn, spk_mon, *pois)
import gc
for trial in range(2):
    t1 = time.time()
    net.run(duration=1000 * ms)
    gc.collect()
    vm_rss = int([l for l in open("/proc/self/status") if l.startswith("VmRSS")][0].split()[1]) / 1e6
    print(f"[run {trial}] wall={time.time()-t1:.1f}s total_spikes={spk_mon.num_spikes} "
          f"VmRSS={vm_rss:.2f}GB maxrss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6:.2f}GB", flush=True)
