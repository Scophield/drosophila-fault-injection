"""Secondary paired action-ablation analysis; separate from core inference."""
import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--registration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();reg=json.loads(a.registration.read_text());paths=sorted((a.root/'episodes').glob('*.json'))
    rs=[json.loads(p.read_text()) for p in paths];key=lambda r:(r['seed'],r['phi_deg'],r['mode'],r['fault'])
    expected={(s,p,m,'healthy') for s in reg['test_seeds'] for p in reg['phis'] for m in reg['modes']}
    if len(rs)!=64 or {key(r) for r in rs}!=expected:raise ValueError('incomplete or duplicate diagnostic matrix')
    active=json.loads((a.root/'active.json').read_text())
    if active['started_unix']<datetime.fromisoformat(reg['created_utc']).timestamp():raise ValueError('launch before registration')
    for name,value in reg['frozen_source_sha256'].items():
        if sha(ROOT/name)!=value:raise ValueError(f'frozen source changed: {name}')
    manifests={sha(p):json.loads(p.read_text()) for p in (a.root/'batches').glob('*/run_manifest.json')}
    for p in (a.root/'batches').glob('*/run_manifest.json'):
        m=manifests[sha(p)]
        if (m['parameters']['registration_sha256']!=sha(a.registration) or m['model_inputs']!=reg['model_inputs_sha256']
            or m['annotations_sha256']!=reg['annotations_sha256'] or m['python']!=reg['runtime']['python']
            or m['packages']!=reg['runtime']['packages']):
            raise ValueError('diagnostic inputs/registration differ')
        for name,value in {**m['source_sha256'],**m['parameters']['entrypoint_sha256']}.items():
            if sha(p.parent/'source'/name)!=value:raise ValueError('generating snapshot mismatch')
    lookup={key(r):r for r in rs};counts=[];paired=[]
    for r in rs:
        if (r['calibration_sha256']!=reg['calibration_sha256'] or r['input_map_sha256']!=sha(a.root/'input-map.json')
            or r['run_manifest_sha256'] not in manifests or r['duration_ms']!=1000):raise ValueError('diagnostic record provenance')
    for s in reg['test_seeds']:
        if len({r['uniform_sha256'] for r in rs if r['seed']==s})!=1:raise ValueError('noncommon diagnostic input uniforms')
    for mode in reg['modes']:
        for phi in reg['phis']:
            group=[r for r in rs if (r['mode'],r['phi_deg'])==(mode,phi)]
            counts.append(dict(mode=mode,phi_deg=phi,n=len(group),success=sum(r['escaped'] for r in group),
                triggers=sum(r['trigger_ms'] is not None for r in group)))
    ix=np.random.default_rng(20261022).integers(8,size=(20000,8));effects={}
    for normal in ['proportional','relay']:
        for control in ['disabled','observe']:
            values=[]
            for s in reg['test_seeds']:
                losses=gains=0
                for p in reg['phis']:
                    h=lookup[(s,p,normal,'healthy')]['escaped'];c=lookup[(s,p,control,'healthy')]['escaped']
                    losses+=h and not c;gains+=not h and c
                    paired.append(dict(seed=s,phi_deg=p,normal=normal,control=control,normal_success=h,control_success=c,
                        loss=int(h and not c),gain=int(not h and c)))
                values.append((losses-gains)/2)
            samples=np.array(values)[ix].mean(axis=1)
            effects[f'{normal}-minus-{control}']=dict(estimate=float(np.mean(values)),low=float(np.quantile(samples,.025)),high=float(np.quantile(samples,.975)))
    a.out.mkdir(parents=True,exist_ok=False)
    for name,rows in [('counts.csv',counts),('pairs.csv',paired)]:
        with (a.out/name).open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result=dict(complete=True,records=64,seed_clusters=8,role=reg['role'],counts=counts,cluster_effects=effects,
        interpretation='disabled removes neural steering only and retains neural burst triggering; observe removes both steering and burst action. These diagnostic action ablations do not establish connectome-specific superiority or biological behavior.',
        registration_sha256=sha(a.registration),raw_input_sha256={p.as_posix():sha(p) for p in paths},
        compute=dict(episode_wall_seconds_sum=sum(r['wall_seconds'] for r in rs),episode_wall_seconds_median=float(np.median([r['wall_seconds'] for r in rs]))),
        source_sha256=sha(Path(__file__)))
    (a.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts'],indent=2))


if __name__=='__main__':main()
