"""Read-only audit of the selected Blender graph against registered v9 inputs.

External tables are read for identity/weight checks only. No neural simulation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--model',type=Path,required=True)
    ap.add_argument('--annotations',type=Path,default=ROOT/'sim/data/annotations.tsv')
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();d=json.loads((a.source/'connectome_data.json').read_text())
    manifest=json.loads((a.source/'data_manifest.json').read_text())
    regpath=ROOT/'runs/task-v9-frozen/registration-core.json'
    reg=json.loads(regpath.read_text())
    calpath=ROOT/'runs/task-v9-frozen/calibration.json';cal=json.loads(calpath.read_text())
    mappath=ROOT/'runs/task-v9-test/input-map.json';im=json.loads(mappath.read_text())
    sources={str(p.resolve()):sha(p) for p in [a.model/'Completeness_783.csv',
        a.model/'Connectivity_783.parquet',a.annotations,regpath,calpath,mappath,
        a.source/'connectome_data.json',a.source/'data_manifest.json']}
    for p in [a.model/'Completeness_783.csv',a.model/'Connectivity_783.parquet',a.annotations]:
        expected=[v['sha256'] for k,v in manifest['sources'].items() if Path(k).name==p.name]
        assert expected==[sha(p)],'Blender source hash mismatch: '+p.name
    model_hashes=set(reg['model_inputs_sha256'].values())
    assert sha(a.model/'Completeness_783.csv') in model_hashes
    assert sha(a.model/'Connectivity_783.parquet') in model_hashes
    assert sha(a.annotations)==reg['annotations_sha256']
    comp=pd.read_csv(a.model/'Completeness_783.csv',index_col=0)
    roots=comp.index.to_numpy(dtype=np.int64)
    ann=pd.read_csv(a.annotations,sep='\t',low_memory=False).set_index('root_id')
    assert ann.index.is_unique
    ann=ann.reindex(roots)
    nodes={n['index']:n for n in d['nodes']}
    assert len(nodes)==len(d['nodes'])==410
    for i,n in nodes.items():
        assert str(roots[i])==n['root_id']
        assert ann.loc[roots[i],'cell_type']==n['cell_type']
        np.testing.assert_array_equal(ann.loc[roots[i],['pos_x','pos_y','pos_z']].to_numpy(dtype=float),n['anchor_voxels'])
    sensory={n['root_id'] for n in nodes.values() if n['role'] in {'LC4','LPLC2'}}
    commands={n['root_id'] for n in nodes.values() if n['role']=='command'}
    assert sensory=={str(n['flyid']) for n in im['sensory']} and len(sensory)==314
    assert commands=={str(n) for n in cal['command_flyids']} and len(commands)==8
    pre,post,w,ct='Presynaptic_Index','Postsynaptic_Index','Excitatory x Connectivity','Connectivity'
    con=pd.read_parquet(a.model/'Connectivity_783.parquet',columns=[pre,post,w,ct])
    c=con[con[pre].isin(nodes) & con[post].isin(nodes)].groupby([pre,post],sort=True)[[w,ct]].sum()
    seen=set()
    for e in d['edges']:
        pair=(e['source'],e['target']);assert pair not in seen;seen.add(pair)
        row=c.loc[pair]
        assert int(row[w])==e['signed_model_weight'] and int(row[ct])==e['contacts']
    assert len(seen)==1050
    roles=Counter(n['role'] for n in nodes.values())
    edge_roles=Counter(nodes[e['source']]['role']+'->'+nodes[e['target']]['role'] for e in d['edges'])
    # The spatial display is a common-scale rigid transform of representative
    # anchors. It is not a measured-neurite or soma reconstruction.
    center=np.asarray(manifest['coordinate_transform']['center_um'])
    scale=manifest['coordinate_transform']['um_per_blender_unit']
    for n in d['nodes']:
        q=(np.asarray(n['anchor_voxels'])*[.004,.004,.04]-center)/scale
        np.testing.assert_allclose(n['position'],q[[0,2,1]]*[1,1,-1],atol=.000000501,rtol=0)
    result=dict(passed=True,script_sha256=sha(__file__),input_sha256=sources,
        node_roles=dict(roles),edge_role_pairs=dict(edge_roles),nodes_verified=len(nodes),
        edges_verified=len(seen),sensory_match=314,command_match=8,
        original_model_rows=len(con),within_group_edges=sum(v for k,v in edge_roles.items() if len(set(k.split('->')))==1),
        scope='Read-only node/edge/coordinate audit. Selected graph is not the full recurrent graph. No neural rerun or biological spatial registration.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))


if __name__=='__main__':main()
