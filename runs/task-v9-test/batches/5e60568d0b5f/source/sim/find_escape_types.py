import pandas as pd
from project_paths import PATH_COMP, PATH_ANN

ann = pd.read_csv(PATH_ANN, sep="\t", dtype={"root_id": "int64"})
comp = pd.read_csv(PATH_COMP, index_col=0)
comp_ids = set(comp.index.astype("int64"))
print(f"annotations rows={len(ann)}, completeness={len(comp_ids)}")
print(f"columns={list(ann.columns)}")

# how many annotated neurons are in the model's neuron set
ann_in = ann[ann.root_id.isin(comp_ids)]
print(f"annotated ∩ model = {len(ann_in)} ({len(ann_in)/len(ann):.1%})")

# escape-pathway candidate types
pats = ["LC4", "LPLC", "LC10", "DNp01", "DNa02", "DNp04", "DNb01", "GF", "MN9"]
for p in pats:
    m = ann_in[ann_in.cell_type.astype(str).str.fullmatch(p, na=False)]
    print(f"  {p:8s}: {len(m)} neurons")
    if len(m) and len(m) <= 5:
        print(f"            ids={list(m.root_id)}")

# also check substring hits (in case of type-name variants)
print("\n-- substring scan (first 5 each) --")
for p in ["LC4", "LPLC2", "DNp01", "DNa02", "DNp04"]:
    m = ann_in[ann_in.cell_type.astype(str).str.contains(p, na=False)]
    print(f"  ~{p}: {len(m)} -> {list(m.cell_type.astype(str).unique())[:5]}")
