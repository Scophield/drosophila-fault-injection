import pandas as pd
import numpy as np
import time

t0 = time.time()
from project_paths import PATH_COMP as comp_path, PATH_CON as con_path

df_comp = pd.read_csv(comp_path, index_col=0)
print(f"[completeness] shape={df_comp.shape} load={time.time()-t0:.1f}s")
print(f"[completeness] columns={list(df_comp.columns)[:8]}")
print(f"[completeness] index name={df_comp.index.name}, head={list(df_comp.index[:3])}")
print(f"[completeness] unique root_ids={df_comp.index.nunique()}")

t1 = time.time()
df_con = pd.read_parquet(con_path)
print(f"[connectivity] shape={df_con.shape} load={time.time()-t1:.1f}s")
print(f"[connectivity] columns={list(df_con.columns)}")
print(df_con.head(3))
print(f"[connectivity] dtypes=\n{df_con.dtypes}")
print(f"[connectivity] unique pre={df_con.iloc[:,0].nunique()}, unique post={df_con.iloc[:,1].nunique()}")
wcol = [c for c in df_con.columns if 'Connectivity' in c or 'Excit' in c]
for c in wcol:
    s = df_con[c]
    print(f"[{c}] min={s.min()} max={s.max()} mean={s.mean():.2f} neg_frac={(s<0).mean():.3f} zero_frac={(s==0).mean():.3f}")
print(f"TOTAL elapsed={time.time()-t0:.1f}s")
