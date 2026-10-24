"""Audit frozen map identities, independent assignments and cohort separation.

No external connectome or simulation is loaded. This checks the supplied
artifacts, not biological RF validity or uniform-prior adequacy.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--design',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();design=json.loads(a.design.read_text())
    old=json.loads(Path('runs/task-v9-test/input-map.json').read_text())['sensory']
    reference={str(q['flyid']):q for q in old}
    with Path('sim/data/annotations.tsv').open(encoding='utf-8',newline='') as f:
        annotations={r['root_id']:r for r in csv.DictReader(f,delimiter='\t') if r['root_id'] in reference}
    assert set(annotations)==set(reference)
    comparisons=[];allseeds=set(range(1000,1024))|set(range(1100,1108))|set(range(1200,1208))
    maps=[]
    for spec in design['maps']:
        p=Path(spec['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==spec['sha256']
        mapping=json.loads(p.read_text());rows=mapping['rows']
        assert len(rows)==len(reference)==314
        assert [int(r['root_id']) for r in rows]==sorted(int(r['root_id']) for r in rows),'canonical FlyID order required by stimulation assignment'
        assert {r['side'] for r in rows}=={'left','right'}
        assert len({r['root_id'] for r in rows})==314
        assert {r['root_id'] for r in rows}==set(reference)
        rng=np.random.default_rng(spec['rf_seed']);n=len(rows)
        expected=np.where(np.array([r['side'] for r in rows])=='left',rng.uniform(10,90,n),rng.uniform(-90,-10,n))
        assert np.array_equal(expected,np.array([r['phi_deg'] for r in rows]))
        for r in rows:
            prior=reference[r['root_id']]
            assert all(r[k]==prior[k] for k in ['psi_deg','w_grad'])
            assert all(r[k]==annotations[r['root_id']][k] for k in ['cell_type','side'])
            assert (r['phi_deg']>0)==(prior['phi_deg']>0)
            assert (10<=r['phi_deg']<=90) if r['side']=='left' else (-90<=r['phi_deg']<=-10)
        cohorts=[[spec['pilot_seed']],spec['development_seeds'],spec['validation_seeds'],spec['test_seeds']]
        for seeds in cohorts:
            assert len(seeds)==len(set(seeds)) and not allseeds.intersection(seeds)
            allseeds.update(seeds)
        changed=sum(r['phi_deg']!=reference[r['root_id']]['phi_deg'] for r in rows)
        assert changed==314
        comparisons.append(dict(map_id=spec['map_id'],azimuths_changed_from_baseline=changed,
            identities_hemisphere_vertical_gradient_preserved=True,draw_reconstructed=True,
            canonical_flyid_order=True,seed_cohorts_disjoint=True,map_sha256=spec['sha256']))
        maps.append(rows)
    assert all(x['phi_deg']!=y['phi_deg'] for x,y in zip(*maps))
    a.out.mkdir(parents=True,exist_ok=False)
    report=dict(passed=True,maps=comparisons,independent_map_azimuths_differ=314,
        design_created_utc=design['created_utc'],design_sha256=hashlib.sha256(a.design.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Artifact independence and specified-prior consistency; not measured RFs, a different prior, or evidence of transfer performance.')
    (a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
