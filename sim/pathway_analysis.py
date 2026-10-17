import numpy as np
from scipy import sparse
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from engine import load_edges, get_type_ids

OUT = Path(__file__).parent / "results" / "graph"
OUT.mkdir(parents=True, exist_ok=True)
ids = get_type_ids()
comp_ids = None

import pandas as pd
comp = pd.read_csv(Path(__file__).resolve().parents[1] / "Drosophila_brain_model" / "Completeness_783.csv", index_col=0)
flyid2i = {int(j): i for i, j in enumerate(comp.index.astype("int64"))}
inp = np.array([flyid2i[int(f)] for f in ids["LC4"] + ids["LPLC2"]])
dn = np.array([flyid2i[int(f)] for f in ids["DN_ALL"]])
N = len(comp)

rng = np.random.default_rng(17)

def build_A(j_override=None):
    i_pre, i_post, w0 = load_edges(j_override)
    A = sparse.csr_matrix((np.abs(w0), (i_pre, i_post)), shape=(N, N))
    return A

def pathway_mass(A, f, seed):
    r = np.random.default_rng(seed)
    Af = A.copy()
    Af.data = Af.data * (r.random(len(Af.data)) >= f)
    v = np.zeros(N)
    v[inp] = 1.0
    masses = []
    for k in range(1, 9):
        v = Af.T @ v
        masses.append(float(v[dn].sum()))
    return masses

res = {}
A_real = build_A()
i_post_orig = load_edges()[1]
A_er = build_A(rng.permutation(i_post_orig))

for f in [0.0, 0.05, 0.10, 0.25, 0.50]:
    res[f"real_{f}"] = pathway_mass(A_real, f, seed=100 + int(f * 1000))
    res[f"er_{f}"] = pathway_mass(A_er, f, seed=200 + int(f * 1000))

base_r = np.array(res["real_0.0"])
base_e = np.array(res["er_0.0"])
print("hops:            " + " ".join(f"{k:>7d}" for k in range(1, 9)))
for f in [0.0, 0.05, 0.10, 0.25, 0.50]:
    r = np.array(res[f"real_{f}"]) / base_r
    e = np.array(res[f"er_{f}"]) / base_e
    print(f"f={f:.2f} real: " + " ".join(f"{x:7.3f}" for x in r))
    print(f"       er:   " + " ".join(f"{x:7.3f}" for x in e))
print(f"baseline real mass k=1..4: {base_r[:4]}")
print(f"baseline er   mass k=1..4: {base_e[:4]}")
with open(OUT / "pathway_mass.json", "w") as fh:
    json.dump(res, fh, indent=2)
print("saved", flush=True)
