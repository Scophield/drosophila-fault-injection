"""Prepare a traceable Blender view of the existing local FlyWire v783 inputs.

Only creates visualization files; never edits the research project or its data.
Run using the bundled CPython 3.12 runtime.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'drosophila-fault-injection/tmp/v9-deps'))
import numpy as np
import pandas as pd

MODEL = ROOT / 'Drosophila_brain_model'
ANNOT = ROOT / 'drosophila-fault-injection/sim/data/annotations.tsv'
COMP = MODEL / 'Completeness_783.csv'
CON = MODEL / 'Connectivity_783.parquet'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    comp = pd.read_csv(COMP, index_col=0)
    roots = comp.index.to_numpy(dtype=np.int64)
    ann = pd.read_csv(ANNOT, sep='\t', low_memory=False).set_index('root_id')
    assert ann.index.is_unique, 'Ambiguous annotation ID'
    ann = ann.reindex(roots)
    ann['cell_type'] = ann['cell_type'].fillna('untyped')
    ann['side'] = ann['side'].fillna('unknown')
    precol, postcol, wcol = 'Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'
    con = pd.read_parquet(CON, columns=[precol, postcol, wcol, 'Connectivity'])
    pre = con[precol].to_numpy(dtype=np.int64)
    post = con[postcol].to_numpy(dtype=np.int64)
    weight = con[wcol].to_numpy(dtype=np.int64)
    assert pre.min() >= 0 and pre.max() < len(roots)
    assert post.min() >= 0 and post.max() < len(roots)
    types = ann.cell_type.to_numpy()
    sources = np.flatnonzero(np.isin(types, ['LC4', 'LPLC2']))
    targets = np.flatnonzero(np.isin(types, ['DNp01', 'DNa02', 'DNp04', 'DNb01']))
    sm, tm = np.isin(pre, sources), np.isin(post, targets)
    relays = np.intersect1d(np.unique(post[sm]), np.unique(pre[tm]))
    s2m = sm & np.isin(post, relays)
    m2t = np.isin(pre, relays) & tm
    score = np.bincount(post[s2m], weights=np.abs(weight[s2m]), minlength=len(roots))
    score += np.bincount(pre[m2t], weights=np.abs(weight[m2t]), minlength=len(roots))
    # Same relay ranking as the existing local sim/fig_pathway.py.
    relays_top = relays[np.argsort(-score[relays], kind='stable')[:90]]
    selected = np.unique(np.r_[sources, relays_top, targets])
    role = {int(i): ('command' if i in targets else types[i] if i in sources else 'relay') for i in selected}
    keep = (sm & np.isin(post, relays_top)) | (np.isin(pre, relays_top) & tm) | (sm & tm)
    edges = con.loc[keep, [precol, postcol, wcol, 'Connectivity']].copy()
    edges = edges.groupby([precol, postcol], as_index=False, sort=True).sum()
    # Keep the strongest incident edge of every endpoint, then the strongest
    # remaining edges up to 1,050. Every displayed edge exists in the local data.
    order = edges[wcol].abs().sort_values(ascending=False, kind='stable').index
    ranked = edges.loc[order]
    chosen = set(ranked.groupby(precol, sort=False).head(1).index)
    chosen.update(ranked.groupby(postcol, sort=False).head(1).index)
    for index in order:
        if len(chosen) >= 1050:
            break
        chosen.add(index)
    shown = edges.loc[sorted(chosen)]
    xyz = ann[['pos_x', 'pos_y', 'pos_z']].to_numpy(dtype=float)
    valid = np.isfinite(xyz).all(axis=1)
    # Official annotations README defines native 4 x 4 x 40 nm voxels.
    xyz_um = xyz * np.array([.004, .004, .04])
    center = (np.nanmin(xyz_um, axis=0) + np.nanmax(xyz_um, axis=0)) / 2

    def point(i):
        delta = (xyz_um[i] - center) / 85.0
        # Rigid axis reorientation with one common scale, not per-axis warping.
        return [round(float(delta[0]), 6), round(float(delta[2]), 6), round(float(-delta[1]), 6)]

    nodes = []
    for i in selected:
        assert valid[i], f'Selected neuron lacks an anchor: {roots[i]}'
        nodes.append(dict(index=int(i), root_id=str(roots[i]), role=role[int(i)],
                          cell_type=str(types[i]), side=str(ann.iloc[i]['side']),
                          position=point(i), anchor_voxels=xyz[i].tolist()))
    rng = np.random.default_rng(20261023)
    background_ids = np.setdiff1d(np.flatnonzero(valid), selected)
    background_ids = np.sort(rng.choice(background_ids, size=min(8500, len(background_ids)), replace=False))
    background = [dict(index=int(i), position=point(i),
                       group='optic' if str(ann.iloc[i]['super_class']) == 'optic' else 'other')
                  for i in background_ids]
    out_edges = [dict(source=int(row[precol]), target=int(row[postcol]),
                      signed_model_weight=int(row[wcol]), contacts=int(row['Connectivity']))
                 for row in shown.to_dict('records')]
    summary = dict(model_neurons=len(roots), model_edge_rows=len(con),
                   model_contacts=int(con.Connectivity.sum()),
                   annotated_valid_anchors=int(valid.sum()),
                   LC4=int((types[sources] == 'LC4').sum()),
                   LPLC2=int((types[sources] == 'LPLC2').sum()),
                   command_neurons=len(targets), all_two_hop_relays=len(relays),
                   displayed_relays=len(relays_top), displayed_pathway_neurons=len(nodes),
                   distinct_relay_nodes=sum(n['role'] == 'relay' for n in nodes),
                   relay_endpoint_overlap=len(relays_top) - sum(n['role'] == 'relay' for n in nodes),
                   candidate_pathway_edges=len(edges), displayed_edges=len(out_edges),
                   background_sample=len(background))
    data = dict(summary=summary, nodes=nodes, edges=out_edges, background=background)
    (OUT / 'connectome_data.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    with (OUT / 'displayed_neurons.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=['index', 'root_id', 'role', 'cell_type', 'side'])
        writer.writeheader()
        writer.writerows({k: node[k] for k in writer.fieldnames} for node in nodes)
    with (OUT / 'displayed_edges.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=['source', 'target', 'signed_model_weight', 'contacts'])
        writer.writeheader()
        writer.writerows(out_edges)
    manifest = dict(summary=summary,
        sources={str(p): dict(bytes=p.stat().st_size, sha256=sha256(p)) for p in [COMP, CON, ANNOT, Path(__file__)]},
        coordinate_reference='https://github.com/flyconnectome/flywire_annotations/blob/main/supplemental_files/README.md',
        coordinate_transform=dict(voxel_size_nm=[4, 4, 40], center_um=center.tolist(),
                                  um_per_blender_unit=85, blender_axes=['+x', '+z', '-y']),
        sampling_seed=20261023,
        selection='LC4 + LPLC2 inputs; DNp01/DNa02/DNp04/DNb01 outputs; top 90 of all two-hop relays by absolute incident model weight; strongest incident edge per endpoint, then strongest remaining to 1050.',
        integrity='Actual local IDs, annotations, anchors and edge weights. Brain points are representative anchors, not soma positions. Connecting curves show abstract connectivity and are not measured axon paths. The separate fly is an illustrative model. No research inputs, experiments or paper figures were changed.')
    (OUT / 'data_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
