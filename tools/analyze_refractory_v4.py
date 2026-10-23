"""Validate the completed model-variant matrix and report paired rate retention."""
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def analyze():
    path=ROOT/'runs/refractory-v4/paired/results.json'
    d=json.loads(path.read_text())
    if not d['complete'] or d['neurons']!=138639 or d['connections']!=15091983:
        raise ValueError('incomplete or wrong network')
    expected={(s,r,f) for s in (12,13,14) for r in (2.2,0.) for f in (None,'F2_50')}
    rows={(r['seed'],r['sensory_refractory_ms'],r['fault']):r for r in d['trials']}
    if len(d['trials'])!=12 or set(rows)!=expected: raise ValueError('matrix mismatch')
    manifest_path=path.with_name('run_manifest.json')
    manifest=json.loads(manifest_path.read_text())
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest()!=d['manifest_sha256']:
        raise ValueError('generation manifest changed')
    for p,h in manifest['source_sha256'].items():
        if hashlib.sha256((path.parent/'source'/p).read_bytes()).hexdigest()!=h:
            raise ValueError('source snapshot changed')
    groups={}
    for refractory in (2.2,0.):
        healthy=[rows[(s,refractory,None)] for s in (12,13,14)]
        fault=[rows[(s,refractory,'F2_50')] for s in (12,13,14)]
        ratios=[f['command_spikes']/h['command_spikes'] for f,h in zip(fault,healthy)]
        for r in healthy+fault:
            if not np.isclose(r['rate_hz'],r['command_spikes']/4.8): raise ValueError('rate/count mismatch')
        groups[str(refractory)]=dict(healthy_median_hz=float(np.median([r['rate_hz'] for r in healthy])),
             fault_median_hz=float(np.median([r['rate_hz'] for r in fault])),
             paired_retentions=ratios,paired_median=float(np.median(ratios)),paired_range=[min(ratios),max(ratios)])
    return dict(complete=True,groups=groups,trial_wall_seconds=sum(r['run_seconds'] for r in d['trials']),
                build_seconds=d['build_seconds'],wall_seconds=d['wall_seconds'],
                source_sha256={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest(),
                               str(manifest_path.relative_to(ROOT)):hashlib.sha256(manifest_path.read_bytes()).hexdigest()},
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def main():
    d=analyze()
    out=ROOT/'audit/refractory-v4'
    out.mkdir(parents=True,exist_ok=False)
    (out/'summary.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps(d['groups'],indent=2))


if __name__=='__main__': main()
