"""Bind stored RF realizations to every phase's actual exported input map.

Metadata/input check only: no outcome inspection, completed-matrix assertion or
neural execution attestation. Independent input-event replay is a separate check.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['root','design','out']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();design=json.loads(a.design.read_text());results=[]
    for spec in design['maps']:
        p=Path(spec['path']).resolve();assert p.is_relative_to(ROOT) and sha(p)==spec['sha256']
        mapping=json.loads(p.read_text());ids=[int(r['root_id']) for r in mapping['rows']]
        assert ids==sorted(ids) and len(ids)==len(set(ids))==314
        expected=[dict(flyid=str(r['root_id']),phi_deg=float(r['phi_deg']),psi_deg=float(r['psi_deg']),w_grad=float(r['w_grad'])) for r in mapping['rows']]
        checks=[];phase_hashes=[]
        for phase in ['development','validation','test']:
            base=a.root/('map-'+spec['map_id'])/phase;mp=base/'input-map.json'
            actual=json.loads(mp.read_text());assert actual['sensory']==expected,'stored input map differs from frozen RF: '+str(mp)
            assert set(ids)<=set(map(int,actual['pool_flyids']))
            phase_hashes.append(sha(mp));snapshots=[]
            for manifest_path in sorted((base/'batches').glob('*/run_manifest.json')):
                m=json.loads(manifest_path.read_text());cfg=m['parameters']
                assert cfg['rf_map_sha256']==spec['sha256'] and cfg['design_sha256']==sha(a.design)
                snapshot=manifest_path.parent/'source'/p.relative_to(ROOT)
                ds=manifest_path.parent/'source'/a.design.resolve().relative_to(ROOT)
                assert sha(snapshot)==spec['sha256'] and sha(ds)==sha(a.design)
                snapshots.append(manifest_path.as_posix())
            assert len(snapshots)==2,'expected two phase-worker source snapshots'
            checks.append(dict(phase=phase,input_map_sha256=sha(mp),sensory_rows=314,worker_manifests=snapshots))
        assert len(set(phase_hashes))==1,'input identities/RF changed across phases'
        results.append(dict(map_id=spec['map_id'],rf_map_sha256=spec['sha256'],canonical_order=True,phases=checks))
    report=dict(passed=True,input_binding_only=True,maps=results,design_sha256=sha(a.design),
        source_sha256=sha(__file__),scope='Frozen RF contents, canonical FlyID order, phase input maps and worker input snapshots; not test completion, neural-state validation or execution authentication')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='maps'},indent=2))


if __name__=='__main__':main()
