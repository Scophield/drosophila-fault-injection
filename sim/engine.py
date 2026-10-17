import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Drosophila_brain_model"))

from model import default_params
from brian2 import Network, NeuronGroup, Synapses, SpikeMonitor, PoissonGroup, volt, second, ms, Hz, prefs

prefs.codegen.target = "cython"

ROOT = Path(__file__).resolve().parents[1]
PATH_COMP = ROOT / "Drosophila_brain_model" / "Completeness_783.csv"
PATH_CON = ROOT / "Drosophila_brain_model" / "Connectivity_783.parquet"
PATH_ANN = ROOT / "sim" / "data" / "annotations.tsv"

INPUT_TYPES = ["LC4", "LPLC2"]
READOUT_TYPES = ["DNp01", "DNa02", "DNp04", "DNb01"]
N_BACKGROUND = 600

W_SCALE = float(default_params["w_syn"] / volt)
W_IN_V = float(default_params["w_syn"] * default_params["f_poi"] / volt)


def get_type_ids():
    ann = pd.read_csv(PATH_ANN, sep="\t", usecols=["root_id", "cell_type", "super_class"], low_memory=False)
    comp = pd.read_csv(PATH_COMP, index_col=0)
    comp_ids = set(comp.index.astype("int64"))
    ann = ann[ann.root_id.isin(comp_ids)]
    out = {}
    for t in set(INPUT_TYPES + READOUT_TYPES):
        out[t] = sorted(ann.loc[ann.cell_type == t, "root_id"].astype("int64").tolist())
    out["DN_ALL"] = sorted(ann.loc[ann.super_class == "descending", "root_id"].astype("int64").tolist())
    return out


def load_edges(j_override=None):
    df_con = pd.read_parquet(PATH_CON)
    i_pre = df_con["Presynaptic_Index"].values.astype(np.int64)
    i_post = df_con["Postsynaptic_Index"].values.astype(np.int64)
    if j_override is not None:
        i_post = np.asarray(j_override, dtype=np.int64)
    w0 = df_con["Excitatory x Connectivity"].values.astype(np.float64) * W_SCALE
    return i_pre, i_post, w0


class FlyBrainSim:
    def __init__(self, j_override=None, background_seed=0):
        self.params = dict(default_params)
        p = self.params
        comp = pd.read_csv(PATH_COMP, index_col=0)
        self.n_neurons = len(comp)
        self.flyid2i = {int(j): i for i, j in enumerate(comp.index.astype("int64"))}
        self.i2flyid = {i: j for j, i in self.flyid2i.items()}
        neu = NeuronGroup(
            N=self.n_neurons,
            model=p["eqs"],
            method="linear",
            threshold=p["eq_th"],
            reset=p["eq_rst"],
            refractory="rfc",
            name="default_neurons",
            namespace=p,
        )
        neu.v = p["v_0"]
        neu.g = 0 * volt
        neu.rfc = p["t_rfc"]
        syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=p["t_dly"], name="default_synapses")
        i_pre, i_post, w0 = load_edges(j_override)
        syn.connect(i=i_pre, j=i_post)
        syn.w = w0 * volt
        self.neu, self.syn = neu, syn
        self.w0 = np.array(syn.w[:], dtype=np.float64, copy=True)
        self.n_syn = len(self.w0)
        self.rfc0 = np.array(neu.rfc[:], dtype=np.float64, copy=True)
        self._pre_idx = np.array(syn.i[:], dtype=np.int64, copy=True)

        ids = get_type_ids()
        pool = list(ids["LC4"]) + list(ids["LPLC2"])
        rng = np.random.default_rng(background_seed)
        all_ids = np.asarray(list(self.flyid2i.keys()), dtype=np.int64)
        bg = rng.choice(all_ids, size=N_BACKGROUND, replace=False)
        pool = sorted(set(pool) | set(int(b) for b in bg))
        self.pool_flyids = np.asarray(pool, dtype=np.int64)
        self.pool_idx = np.asarray([self.flyid2i[int(f)] for f in self.pool_flyids], dtype=np.int64)
        self.pool_pos = {int(f): k for k, f in enumerate(self.pool_flyids)}
        self.stim = PoissonGroup(len(self.pool_flyids), rates=150 * Hz)
        self.syn_stim = Synapses(self.stim, self.neu, model="w : volt", on_pre="v += w", delay=0 * ms)
        self.syn_stim.connect(i=np.arange(len(self.pool_flyids)), j=self.pool_idx)
        self.syn_stim.w[:] = 0 * volt
        self.mon_all = SpikeMonitor(self.neu, record=False)
        self.mon_ro = SpikeMonitor(self.neu)
        self.net = Network(self.neu, self.syn, self.stim, self.syn_stim, self.mon_all, self.mon_ro)
        self.net.store("init")

    def apply_weights(self, w_new):
        self.syn.w[:] = np.asarray(w_new, dtype=np.float64) * volt

    def reset_weights(self):
        self.syn.w[:] = self.w0 * volt

    def out_mask(self, neuron_indices):
        m = np.zeros(self.n_neurons, dtype=bool)
        m[np.asarray(list(neuron_indices), dtype=np.int64)] = True
        return m[self._pre_idx]

    def trial(self, exc_flyids, t_run=600, r_poi=150, readout_flyids=None, readout2_flyids=None, w_fault=None):
        self.net.restore("init")
        if w_fault is not None:
            self.apply_weights(w_fault)
        exc_set = set(int(f) for f in exc_flyids)
        missing = exc_set - set(self.pool_pos)
        if missing:
            raise ValueError(f"{len(missing)} exc neurons not in stim pool")
        act = np.array([1.0 if int(f) in exc_set else 0.0 for f in self.pool_flyids])
        self.syn_stim.w[:] = (act * W_IN_V) * volt
        self.stim.rates = r_poi * Hz
        self.net.run(t_run * ms)
        res = {"n_total_spikes": int(self.mon_all.num_spikes), "t_run_ms": t_run}
        if readout_flyids is not None:
            ro_idx = np.asarray([self.flyid2i[int(f)] for f in readout_flyids], dtype=np.int64)
            keep = np.isin(self.mon_ro.i[:], ro_idx)
            res["t"] = np.asarray(self.mon_ro.t[:][keep] / ms, dtype=np.float64)
            res["i"] = np.asarray(self.mon_ro.i[:][keep], dtype=np.int64)
        if readout2_flyids is not None:
            ro2_idx = np.asarray([self.flyid2i[int(f)] for f in readout2_flyids], dtype=np.int64)
            keep2 = np.isin(self.mon_ro.i[:], ro2_idx)
            uni, cnt = np.unique(self.mon_ro.i[:][keep2], return_counts=True)
            res["dn2_n"] = int(keep2.sum())
            res["dn2_first"] = float(np.min(self.mon_ro.t[:][keep2] / ms)) if keep2.any() else None
            res["dn2_counts"] = {str(self.i2flyid[int(i)]): int(c) for i, c in zip(uni, cnt)}
        return res
