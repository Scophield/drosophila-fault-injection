import gc
import sys
import numpy as np
import pandas as pd
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parent
sys.path.insert(0, str(ROOT / "sim"))

import engine as _engine
from engine import W_IN_V, N_BACKGROUND, get_type_ids
from brian2 import Network, NeuronGroup, Synapses, SpikeMonitor, PoissonGroup, volt, second, ms, Hz

N_CHUNKS = 8


def _load_edges_lean():
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(_engine.PATH_CON)
    n = pf.metadata.num_rows
    i_pre = np.empty(n, dtype=np.int32)
    i_post = np.empty(n, dtype=np.int32)
    w0 = np.empty(n, dtype=np.float32)
    cols = ["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]
    off = 0
    for batch in pf.iter_batches(batch_size=2_000_000, columns=cols):
        m = batch.num_rows
        i_pre[off:off + m] = batch.column(0).to_numpy()
        i_post[off:off + m] = batch.column(1).to_numpy()
        w0[off:off + m] = batch.column(2).to_numpy()
        off += m
        del batch
    assert off == n
    w0 = w0.astype(np.float64) * _engine.W_SCALE
    del pf
    gc.collect()
    return i_pre, i_post, w0


class VisionSim:
    def __init__(self, background_seed=0):
        _engine.defaultclock.dt = 0.1 * ms
        p = dict(_engine.default_params)
        self.params = p
        comp = pd.read_csv(_engine.PATH_COMP, index_col=0)
        self.n_neurons = len(comp)
        self.flyid2i = {int(j): i for i, j in enumerate(comp.index.astype("int64"))}
        self.i2flyid = {i: j for j, i in self.flyid2i.items()}
        del comp
        self.neu = NeuronGroup(
            N=self.n_neurons,
            model=p["eqs"],
            method="linear",
            threshold=p["eq_th"],
            reset=p["eq_rst"],
            refractory="rfc",
            name="neurons",
            namespace=p,
        )
        self.neu.v = p["v_0"]
        self.neu.g = 0 * volt
        self.neu.rfc = p["t_rfc"]
        i_pre, i_post, w0 = _load_edges_lean()
        self.syn_list = []
        edges = np.linspace(0, len(i_pre), N_CHUNKS + 1).astype(np.int64)
        for k in range(N_CHUNKS):
            syn = Synapses(self.neu, self.neu, "w : volt", on_pre="g += w", delay=p["t_dly"], name=f"syn_{k}")
            syn.connect(i=i_pre[edges[k]:edges[k + 1]], j=i_post[edges[k]:edges[k + 1]])
            syn.w = w0[edges[k]:edges[k + 1]] * volt
            self.syn_list.append(syn)
        del i_pre, i_post, w0
        gc.collect()
        self.n_syn = int(sum(len(s.w[:]) for s in self.syn_list))
        self.w0 = np.concatenate([np.array(s.w[:], dtype=np.float64) for s in self.syn_list])
        self._pre_idx = np.concatenate([np.array(s.i[:], dtype=np.int64) for s in self.syn_list])
        ids = get_type_ids()
        pool = list(ids["LC4"]) + list(ids["LPLC2"])
        rng = np.random.default_rng(background_seed)
        all_ids = np.asarray(list(self.flyid2i.keys()), dtype=np.int64)
        bg = rng.choice(all_ids, size=N_BACKGROUND, replace=False)
        pool = sorted(set(pool) | set(int(b) for b in bg))
        self.pool_flyids = np.asarray(pool, dtype=np.int64)
        self.pool_idx = np.asarray([self.flyid2i[int(f)] for f in self.pool_flyids], dtype=np.int64)
        self.pool_pos = {int(f): k for k, f in enumerate(self.pool_flyids)}
        self.stim = PoissonGroup(len(self.pool_flyids), rates=0 * Hz)
        self.syn_stim = Synapses(self.stim, self.neu, model="w : volt", on_pre="v += w", delay=0 * ms, name="stim_syn")
        self.syn_stim.connect(i=np.arange(len(self.pool_flyids)), j=self.pool_idx)
        self.syn_stim.w[:] = 0 * volt
        self.mon_all = SpikeMonitor(self.neu, record=False)
        self.mon_ro = SpikeMonitor(self.neu)
        self.net = Network(self.neu, *self.syn_list, self.stim, self.syn_stim, self.mon_all, self.mon_ro)
        self.net.store("init")

    def apply_weights(self, w_new):
        w = np.asarray(w_new, dtype=np.float64)
        off = 0
        for syn in self.syn_list:
            n = len(syn.w[:])
            syn.w[:] = w[off:off + n] * volt
            off += n

    def reset_state(self):
        self.net.restore("init")
        if getattr(self, "_stim_w", None) is not None:
            self.syn_stim.w[:] = (self._stim_w * 1.0) * volt

    def set_frame_rates(self, sens_rates_hz):
        base = np.zeros(len(self.pool_flyids), dtype=np.float64)
        sens_pos = np.asarray([self.pool_pos[int(f)] for f in self.sens_flyids], dtype=np.int64)
        base[sens_pos] = np.asarray(sens_rates_hz, dtype=np.float64)
        self.stim.rates = base * Hz

    def arm_stim_weights(self, sensory_flyids):
        self.sens_flyids = np.asarray(sorted(int(f) for f in sensory_flyids), dtype=np.int64)
        w = np.zeros(len(self.pool_flyids), dtype=np.float64)
        for f in self.sens_flyids:
            w[self.pool_pos[int(f)]] = W_IN_V
        self._stim_w = w
        self.syn_stim.w[:] = (w * 1.0) * volt

    def run_frame(self, t_ms):
        self.net.run(t_ms * ms)

    def spike_records(self, ro_flyids):
        ro_idx = np.asarray([self.flyid2i[int(f)] for f in ro_flyids], dtype=np.int64)
        keep = np.isin(self.mon_ro.i[:], ro_idx)
        return {
            "t_ms": np.asarray(self.mon_ro.t[:][keep] / ms, dtype=np.float64),
            "i": np.asarray(self.mon_ro.i[:][keep], dtype=np.int64),
        }

    def count_dn_all(self, dn_all_flyids):
        ro_idx = np.asarray([self.flyid2i[int(f)] for f in dn_all_flyids], dtype=np.int64)
        return int(np.isin(self.mon_ro.i[:], ro_idx).sum())
