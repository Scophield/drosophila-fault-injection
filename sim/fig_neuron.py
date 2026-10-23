import json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from project_paths import PATH_COMP, PATH_ANN, ROOT
from pathlib import Path
import argparse
ap=argparse.ArgumentParser()
ap.add_argument('--results',type=Path,default=ROOT/'sim/results/real')
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
args.out.mkdir(parents=True,exist_ok=False)
import pandas as pd
comp = pd.read_csv(PATH_COMP, index_col=0)
i2fid = comp.index.astype("int64").values
ann = pd.read_csv(PATH_ANN, sep="\t", usecols=["root_id", "cell_type"], low_memory=False)
cmap = dict(zip(ann.root_id.astype("int64"), ann.cell_type.fillna("?")))

def counts(pat):
    c = {}
    for fn in sorted(glob.glob(pat)):
        for line in open(fn):
            d = json.loads(line)
            for i in d["i_readout"]:
                c[i] = c.get(i, 0) + 1
    return c

h, f2 = counts(str(args.results/"healthy.jsonl")), counts(str(args.results/"F2_drop_50.jsonl"))
cells = sorted(set(h) | set(f2), key=lambda i: -h.get(i, 0))
labels = [f"{cmap.get(int(i2fid[i]), '?')} #{i}" for i in cells]
hv = [h.get(i, 0) for i in cells]
fv = [f2.get(i, 0) for i in cells]
y = np.arange(len(cells))[::-1]
fig, ax = plt.subplots(figsize=(3.5, 2.1), dpi=300)
ax.barh(y + 0.2, hv, height=0.38, color="#4878CF", label="healthy")
ax.barh(y - 0.2, fv, height=0.38, color="#EE854E", label="50% connection loss")
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=6)
ax.set_xlabel("readout spikes over 12 trials", fontsize=7)
ax.tick_params(labelsize=6)
ax.legend(fontsize=6, frameon=False, loc="lower right")
ax.set_title("Per-neuron command readout composition", fontsize=7.5)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
fig.tight_layout()
fig.savefig(args.out/"fig_neuron.png", bbox_inches="tight")
print("saved", len(cells), "cells; totals", sum(hv), sum(fv))
