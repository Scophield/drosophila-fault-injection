import sys, json, gc
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
import numpy as np
import pandas as pd
import engine as _engine
from vision_core import _load_edges_lean

def load_edges_lean64(j_override=None):
    i_pre, i_post, w0 = _load_edges_lean()
    i_pre = i_pre.astype(np.int64); i_post = i_post.astype(np.int64)
    if j_override is not None:
        i_post = np.asarray(j_override, dtype=np.int64)
    w0 = w0.astype(np.float64)
    return i_pre, i_post, w0

_engine.load_edges = load_edges_lean64
from engine import FlyBrainSim, get_type_ids
ids = get_type_ids()
sim = FlyBrainSim()
exc = ids["LC4"] + ids["LPLC2"]
res = sim.trial(exc, t_run=600, r_poi=150, readout_flyids=None)
print(json.dumps({"engine": "origin_single_synapse", "n_total": res["n_total_spikes"]}))
