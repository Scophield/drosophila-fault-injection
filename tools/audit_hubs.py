"""Reconstruct selectors from external inputs, without constructing a Brian2 network.

Reconstructed old-code sets are not evidence of the actual historical run sets.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import subprocess
import hashlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sim'))
from project_paths import require_model, PATH_CON, PATH_COMP, PATH_ANN
from run_provenance import sha256


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    require_model()  # Fail before importing optional heavy data libraries.
    import numpy as np
    import pandas as pd
    from hub_selection import select_hubs, manifest
    if args.out.exists():
        raise FileExistsError(args.out)
    comp=pd.read_csv(PATH_COMP,index_col=0)
    ids=comp.index.astype('int64').to_numpy()
    mapping=dict(enumerate(map(int,ids)))
    ann=pd.read_csv(PATH_ANN,sep='\t',usecols=['root_id','cell_type'])
    protected=set(map(int,ann.loc[ann.cell_type.isin(['LC4','LPLC2','DNp01','DNa02','DNp04','DNb01']) & ann.root_id.isin(ids),'root_id']))
    frame=pd.read_parquet(PATH_CON,columns=['Presynaptic_Index','Excitatory x Connectivity'])
    pre=frame['Presynaptic_Index'].to_numpy(dtype=np.int64)
    weights=frame['Excitatory x Connectivity'].to_numpy(dtype=np.float64)*2.75e-4
    sim=SimpleNamespace(_pre_idx=pre,w0=weights,n_neurons=len(ids),i2flyid=mapping)
    scores=np.bincount(pre,weights=np.rint(np.abs(weights)/2.75e-4),minlength=len(ids)).astype(np.int64)
    float_scores=np.bincount(pre,weights=np.abs(weights)/2.75e-4,minlength=len(ids))
    comparison={}
    for fraction in (.01,.02,.05):
        n=round(fraction*len(ids))
        old_order=np.argsort(-float_scores)
        old_index=np.array([i for i in old_order if int(i) not in protected][:n])
        old_mapped=np.array([i for i in old_order if mapping[int(i)] not in protected][:n])
        fixed=select_hubs(scores,mapping,protected,n)
        groups={'old_index_check':old_index,'old_mapped_check':old_mapped,'corrected':fixed}
        comparison[str(fraction)]={}
        for label,pick in groups.items():
            # Old invalid sets may intersect protected; describe them without asserting validity.
            value=manifest(sim,pick,protected if label=='corrected' else set())
            value['actual_protected_overlap']=sorted(set(value['flyids']) & protected)
            value['removed_vs_corrected']=sorted(set(value['flyids'])-set(map(int,ids[fixed])))
            value['added_by_correction']=sorted(set(map(int,ids[fixed]))-set(value['flyids']))
            comparison[str(fraction)][label]=value
    args.out.mkdir(parents=True)
    from hub_selection import profile
    _,signs=profile(sim)
    inh_pool=(signs<0)&~np.isin(ids,list(protected))
    average_inh_contacts=float(scores[inh_pool].mean())
    mass_matching={}
    for name,group in comparison['0.01'].items():
        selected=np.isin(ids,group['flyids'])&(signs<0)
        mass_matching[name]=dict(inhibitory_cells=int(selected.sum()),
                                inhibitory_contacts=int(scores[selected].sum()),
                                eligible_inhibitory_mean_contacts=average_inh_contacts,
                                expected_mass_random_cells=round(scores[selected].sum()/average_inh_contacts))
    (args.out/'mass_matching.json').write_text(json.dumps(mass_matching,indent=2)+'\n')
    (args.out/'selector_comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    from hub_selection import for_sim, profile
    for fraction in (.01,.02,.05):
        pick=for_sim(sim,protected,fraction)
        (args.out/f'corrected_hubs_{fraction}.json').write_text(json.dumps(manifest(sim,pick,protected),indent=2)+'\n')
        if fraction==.01:
            _,sign=profile(sim)
            for name,subset in [('HUB_inh',pick[sign[pick]<0]),('HUB_exc',pick[sign[pick]>0])]:
                (args.out/f'corrected_{name}.json').write_text(json.dumps(manifest(sim,subset,protected),indent=2)+'\n')
    blob=subprocess.check_output(['git','show','HEAD:Completeness_783.csv'],cwd=PATH_COMP.parent)
    (args.out/'manifest.json').write_text(json.dumps(dict(
        sources={str(p):sha256(p) for p in (PATH_CON,PATH_COMP,PATH_ANN)},
        upstream_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=PATH_COMP.parent,text=True).strip(),
        model_py_sha256=sha256(PATH_COMP.parent/'model.py'),
        completeness_git_blob_sha256=hashlib.sha256(blob).hexdigest(),
        completeness_matches_after_crlf_normalization=PATH_COMP.read_bytes().replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n'),
        python=sys.version,numpy=np.__version__,pandas=pd.__version__,script_sha256=sha256(Path(__file__)),
        caveat='old sets reconstructed from current code/data, not recovered historical manifests; no activity simulated',
        null_note='target-only permutation cannot change fixed source-selected sets or outgoing row counts; old index/mapped reconstructions match archived damage counts, but are not historical run manifests'),indent=2)+'\n')


if __name__=='__main__':
    main()
