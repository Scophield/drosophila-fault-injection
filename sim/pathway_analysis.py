import numpy as np
from scipy import sparse
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from engine import load_edges, get_type_ids
from project_paths import PATH_COMP
from run_provenance import output_dir, prepare

OUT = prepare(output_dir('graph'),dict(producer='pathway_analysis',er_seed=17,
              deletion_seed_rules=['100+int(f*1000)','200+int(f*1000)'],deletion_unit='original edge-table row'))
ids = get_type_ids()
comp_ids = None

import pandas as pd
comp = pd.read_csv(PATH_COMP, index_col=0)
flyid2i = {int(j): i for i, j in enumerate(comp.index.astype("int64"))}
inp = np.array([flyid2i[int(f)] for f in ids["LC4"] + ids["LPLC2"]])
dn = np.array([flyid2i[int(f)] for f in ids["DN_ALL"]])
N = len(comp)

rng = np.random.default_rng(17)

def build_A(j_override=None):
    i_pre, i_post, w0 = load_edges(j_override)
    return i_pre, i_post, np.abs(w0)

def pathway_mass(A, f, seed):
    r = np.random.default_rng(seed)
    pre, post, weights = A
    # Sample original connections before CSR coalesces repeated null graph pairs.
    kept_weights = weights * (r.random(len(weights)) >= f)
    Af = sparse.csr_matrix((kept_weights,(pre,post)),shape=(N,N))
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
