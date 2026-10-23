import sys, json, gc
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
import numpy as np
import pandas as pd
import engine as _engine

def load_edges_lean64(j_override=None):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(_engine.PATH_CON)
    n = pf.metadata.num_rows
    i_pre = np.empty(n, dtype=np.int32); i_post = np.empty(n, dtype=np.int32); w0 = np.empty(n, dtype=np.float32)
    off = 0
    for batch in pf.iter_batches(batch_size=2_000_000, columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]):
        m = batch.num_rows
        i_pre[off:off+m] = batch.column(0).to_numpy(); i_post[off:off+m] = batch.column(1).to_numpy(); w0[off:off+m] = batch.column(2).to_numpy()
        off += m; del batch
    i_pre = i_pre.astype(np.int64); i_post = i_post.astype(np.int64); w0 = w0.astype(np.float64) * _engine.W_SCALE
    del pf; gc.collect()
    if j_override is not None:
        i_post = np.asarray(j_override, dtype=np.int64)
    return i_pre, i_post, w0

_engine.load_edges = load_edges_lean64
from engine import FlyBrainSim, get_type_ids
ids = get_type_ids()
sim = FlyBrainSim()
exc = ids["LC4"] + ids["LPLC2"]
res = sim.trial(exc, t_run=600, r_poi=150, readout_flyids=None)
print(json.dumps({"engine": "default_codegen", "n_total": res["n_total_spikes"]}))
