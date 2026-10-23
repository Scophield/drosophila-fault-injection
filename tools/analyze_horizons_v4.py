"""Separate stopping-time matching from horizon selection in immutable legacy data."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_revision import ROOT, exposure


def analyze():
    vision=ROOT/'sim_vision/results_vision'
    sources={}
    def read(p):
        sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        return json.loads(p.read_text())
    calibration=read(vision/'calib.json')
    from closedloop_protocol import calibration_keys
    keys=calibration_keys(calibration,vision/'episodes_train')
    pairs=[]
    for fault,tag in [('F2_50','v4'),('F4_1pct','v4'),('HUB_inh','v4c')]:
        for p in sorted((vision/f'episodes_{tag}').glob(f'brain_{fault}_phi*.json')):
            f=read(p)
            h=read(vision/'episodes_v4'/p.name.replace(f'brain_{fault}_','brain_healthy_'))
            tf,th=exposure(f)['duration_ms'],exposure(h)['duration_ms']
            common=min(tf,th)
            ratios={str(t):exposure(f,t)['spikes']/exposure(h,t)['spikes']
                    for t in range(200,int(common)+1,20)}
            crossing=next((t for t in range(20,int(common)+1,20)
                           if exposure(h,t)['spikes']>0 and
                           exposure(f,t)['spikes']/exposure(h,t)['spikes']>2),None)
            pairs.append(dict(fault=fault,phi=f['phi_t_deg'],seed=f['seed'],
                              calibration_scenario=(f['phi_t_deg'],f['seed']) in keys,
                              fault_duration_ms=tf,healthy_duration_ms=th,common_duration_ms=common,
                              whole_ratio=exposure(f)['spikes']/exposure(h)['spikes'],
                              common_ratio=exposure(f,common)['spikes']/exposure(h,common)['spikes'],
                              ratios=ratios,first_twofold_ms=crossing))
    groups={}
    for fault in ('F2_50','F4_1pct','HUB_inh'):
        rows=[p for p in pairs if p['fault']==fault]
        if len(rows)!=12: raise ValueError('incomplete legacy matrix')
        groups[fault]=dict(n=12,whole_median=float(np.median([p['whole_ratio'] for p in rows])),
                          common_median=float(np.median([p['common_ratio'] for p in rows])),
                          windows={str(t):dict(median=float(np.median([p['ratios'][str(t)] for p in rows])),
                              exceedances=sum(p['ratios'][str(t)]>2 for p in rows))
                              for t in range(200,int(min(p['common_duration_ms'] for p in rows))+1,100)})
    return dict(estimands=dict(whole='Sf(Tf)/Sh(Th)',common='Sf(min(Tf,Th))/Sh(min(Tf,Th))',
                               fixed='Sf(t)/Sh(t), provided both records reach t'),
                pairs=pairs,groups=groups,source_sha256=sources,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def main():
    out=ROOT/'audit/horizons-v4'
    out.mkdir(parents=True,exist_ok=False)
    result=analyze()
    (out/'horizons.json').write_text(json.dumps(result,indent=2)+'\n')
    with (out/'pairs.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=[k for k in result['pairs'][0] if k!='ratios'])
        writer.writeheader()
        writer.writerows({k:v for k,v in p.items() if k!='ratios'} for p in result['pairs'])
    print(json.dumps(result['groups'],indent=2))


if __name__=='__main__': main()
