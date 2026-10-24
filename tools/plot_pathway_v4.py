"""Instrumented pathway schematic: mapped L/R identities and output-silencing labels.

Python schematic-led composite, single-column PDF/PNG; contact encoding is descriptive.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sim'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from project_paths import ROOT, PATH_CON, PATH_COMP, PATH_ANN
from pathlib import Path
import argparse
ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
args.out.mkdir(parents=True,exist_ok=False)
con = pd.read_parquet(PATH_CON, columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"])
i_pre = con["Presynaptic_Index"].values.astype(np.int64)
i_post = con["Postsynaptic_Index"].values.astype(np.int64)
w = np.abs(con["Excitatory x Connectivity"].values.astype(float))
ann = pd.read_csv(PATH_ANN, sep="\t", usecols=["root_id", "cell_type", "side"], low_memory=False)
comp = pd.read_csv(PATH_COMP, index_col=0)
f2i = {int(j): i for i, j in enumerate(comp.index.astype("int64"))}
c2t = dict(zip(ann.root_id.astype("int64"), ann.cell_type))
c2s = dict(zip(ann.root_id.astype('int64'),ann.side))
S_lc4 = [f2i[int(f)] for f in comp.index.astype("int64") if c2t.get(int(f)) == "LC4"]
S_lplc2 = [f2i[int(f)] for f in comp.index.astype("int64") if c2t.get(int(f)) == "LPLC2"]
T = [f2i[int(f)] for t in ["DNp01", "DNa02", "DNp04", "DNb01"] for f in ann.loc[ann.cell_type == t, "root_id"].astype("int64") if int(f) in f2i]
S = np.array(S_lc4 + S_lplc2)
T = np.array(T)

Sm = np.isin(i_pre, S)
Tm = np.isin(i_post, T)
Mset = np.intersect1d(np.unique(i_post[Sm]), np.unique(i_pre[Tm]))
direct = Sm & Tm
s2m = Sm & np.isin(i_post, Mset)
m2t = np.isin(i_pre, Mset) & Tm

m_in = np.bincount(i_post[s2m], weights=w[s2m], minlength=len(comp))[Mset]
m_out = np.bincount(i_pre[m2t], weights=w[m2t], minlength=len(comp))[Mset]
top = np.argsort(-(m_in + m_out))[:90]
Mtop = Mset[top]

rng = np.random.default_rng(7)
fig, ax = plt.subplots(figsize=(3.5, 1.65), dpi=300)
ax.set_position([0.01, 0.03, 0.98, 0.74])
ax.set_xlim(-0.38, 1.55)
ax.set_ylim(-0.22, 1.16)
ax.axis("off")

xS, xM, xT = 0.0, 0.5, 1.0
ysL = 0.98 - 0.9 * (np.arange(len(S_lc4)) + 0.5) / len(S_lc4)
ysP = 0.06 - 0.94 * (np.arange(len(S_lplc2)) + 0.5) / len(S_lplc2) + 0.94
yS = np.concatenate([ysL, ysP])
rngS = rng.uniform(-0.012, 0.012, len(S))
yS = yS + rngS
yM = np.linspace(0.99, 0.01, len(Mtop))
yT = np.linspace(0.94, 0.06, len(T))

posS = {n: (xS, y) for n, y in zip(S, yS)}
posM = {int(m): (xM, y) for m, y in zip(Mtop, yM)}
posT = {int(t): (xT, y) for t, y in zip(T, yT)}

di, dj = i_pre[direct], i_post[direct]
dw = w[direct]
dmax = dw.max()
for a, b, ww in zip(di, dj, dw):
    ax.plot([xS, xT], [posS[a][1], posT[b][1]], color="#2e7d32", lw=0.25, alpha=0.05 + 0.20 * (ww / dmax), zorder=1, solid_capstyle="round")

si, sj = i_pre[s2m], i_post[s2m]
sw = w[s2m]
order = np.argsort(-sw)[:260]
smax = sw.max()
for a, b, ww in zip(si[order], sj[order], sw[order]):
    if int(b) in posM:
        ax.plot([xS, xM], [posS[a][1], posM[int(b)][1]], color="#3b6ea5", lw=0.25 + 0.7 * (ww / smax), alpha=0.02 + 0.16 * (ww / smax), zorder=2, solid_capstyle="round")

mi, mj = i_pre[m2t], i_post[m2t]
mw = w[m2t]
order = np.argsort(-mw)[:260]
mmax = mw.max()
for a, b, ww in zip(mi[order], mj[order], mw[order]):
    if int(a) in posM:
        ax.plot([xM, xT], [posM[int(a)][1], posT[b][1]], color="#6d6d6d", lw=0.25 + 0.7 * (ww / mmax), alpha=0.02 + 0.16 * (ww / mmax), zorder=2, solid_capstyle="round")

ax.scatter(np.full(len(ysL), xS), ysL, s=2.2, color="#3b6ea5", zorder=4)
ax.scatter(np.full(len(ysP), xS), ysP, s=2.2, color="#e08214", zorder=4)
ax.scatter(np.full(len(Mtop), xM), yM, s=2.6, color="#8a8a8a", zorder=4)
ax.scatter(np.full(len(T), xT), yT, s=9, color="#1b5e20", marker="D", zorder=5)
lab = [c2t[int(comp.index[t])]+' '+{'left':'L','right':'R'}[c2s[int(comp.index[t])]] for t in T]
for k, (t, y) in enumerate(zip(T, yT)):
    ax.text(xT + 0.025, y, lab[k], fontsize=7.2, va="center", color="#1b5e20")

ax.annotate("", xy=(-0.035, 0.5), xytext=(-0.125, 0.5), arrowprops=dict(arrowstyle="-|>", color="#b03a2e", lw=0.9))
ax.text(-0.34, 0.65, "150 Hz\ninput", fontsize=7.2, color="#b03a2e", ha="left")

def badge(x, y, s):
    ax.text(x, y, s, fontsize=7.2, color="#8b1a1a", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.22", fc="#fdecea", ec="#b03a2e", ls=(0, (2, 1.4)), lw=0.6))

badge(0.0, -0.16, "F5 channels")
badge(0.25, 0.545, "F1 weights\nF2 edges")
badge(0.73, -0.16, "F3/F4 output silencing")
ax.annotate("", xy=(0.0, -0.005), xytext=(0.0, -0.028), arrowprops=dict(arrowstyle="-|>", color="#b03a2e", lw=0.7, ls="--"))
ax.annotate("", xy=(0.62, 0.28), xytext=(0.32, 0.50), arrowprops=dict(arrowstyle="-|>", color="#b03a2e", lw=0.7, ls="--"))
ax.annotate("", xy=(0.97, 0.028), xytext=(0.80, 0.035), arrowprops=dict(arrowstyle="-|>", color="#b03a2e", lw=0.7, ls="--"))
ax.annotate("", xy=(1.38, 0.5), xytext=(1.29, 0.5), arrowprops=dict(arrowstyle="-|>", color="#1b5e20", lw=0.9))
ax.text(1.4, 0.5, "rate\nvs. $\\theta$", fontsize=7.2, color="#1b5e20", va="center", ha="left")

ax.text(0.0, 1.03, "LC4: 104\nLPLC2: 210", fontsize=7.2, ha="center", color="#444444")
ax.text(0.5, 1.03, "90 / 849\nrelays", fontsize=7.2, ha="center", color="#444444")
ax.text(1.0, 1.03, "8 command\nneurons", fontsize=7.2, ha="center", color="#1b5e20")

fig.savefig(args.out/"fig0_pathway.pdf", bbox_inches="tight", pad_inches=0.01)
fig.savefig(args.out/"fig0_pathway.png", bbox_inches="tight", pad_inches=0.01, dpi=200)
import hashlib
import json
sources = [PATH_CON, PATH_COMP, PATH_ANN, Path(__file__)]
(args.out/'pathway_manifest.json').write_text(json.dumps(dict(
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
    command_labels=lab, relay_count=int(len(Mset)), displayed_relays=int(len(Mtop))), indent=2)+'\n')
print("saved")
