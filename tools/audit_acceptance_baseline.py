"""Independent raw-data and PDF checks; never modify historical records."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pymupdf

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'audit/acceptance-v9/baseline'
    out.mkdir(parents=True,exist_ok=False)
    source=ROOT/'runs/controller-fault-v8/vision/episodes_controls'
    records=[(p,json.loads(p.read_text())) for p in sorted(source.glob('*.json'))]
    counts=[]; timings=[]; mismatches=[]; hashes={}
    for p,r in records:
        hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        if r['trigger_ms'] is not None:
            exact=bool(r['escaped'] and r['trigger_ms']+250<=r['horizon_ms']<r['trigger_ms']+700)
            if exact!=r['burst_active_at_horizon']:
                mismatches.append(dict(file=p.name,recorded=r['burst_active_at_horizon'],exact=exact))
            on=[q for q in r['log'] if q['burst']]
            if on:
                ended=on[-1]['t_end_ms']<r['duration_ms']
                timings.append(dict(file=p.name,delay=on[0]['t_ms']-r['trigger_ms'],
                    observed_duration=sum(q['t_end_ms']-q['t_ms'] for q in on),completed=ended))
    for mode in ['brain','precue_gated']:
        for fault in [None,'F2_25','F2_50']:
            group=[r for _,r in records if r['mode']==mode and r['fault']==fault]
            counts.append(dict(mode=mode,fault=fault,n=len(group),success=sum(r['escaped'] for r in group),
                by_bearing={str(phi):sum(r['escaped'] for r in group if r['phi_t_deg']==phi) for phi in [-30,30]}))
    interaction=[]
    for seed in range(12,18):
        D={}
        for mode in ['brain','precue_gated']:
            d=[]
            for phi in [-30,30]:
                h=next(r for _,r in records if (r['mode'],r['fault'],r['seed'],r['phi_t_deg'])==(mode,None,seed,phi))
                f=next(r for _,r in records if (r['mode'],r['fault'],r['seed'],r['phi_t_deg'])==(mode,'F2_25',seed,phi))
                d.append(int(h['escaped'])-int(f['escaped']))
            D[mode]=np.mean(d)
        interaction.append(float(D['precue_gated']-D['brain']))
    flips=np.array(np.meshgrid(*[[-1,1]]*6)).reshape(6,-1).T
    p=float(np.mean(np.abs(np.mean(flips*np.array(interaction),axis=1))>=abs(np.mean(interaction))-1e-12))
    doc=pymupdf.open(ROOT/'paper/main.pdf')
    page5=doc[4].get_text()
    result=dict(records=len(records),source_sha256=hashes,counts=counts,
        interaction_25=interaction,interaction_mean=float(np.mean(interaction)),sign_flip_p=p,
        delays=sorted(set(t['delay'] for t in timings)),completed_durations=sorted(set(t['observed_duration'] for t in timings if t['completed'])),
        completed_bursts=sum(t['completed'] for t in timings),horizon_mismatches=mismatches,
        main_pages=len(doc),page_five_has_technical_content='IMPLICATIONS' in page5 or 'Legacy full-hub' in page5,
        main_sha256=hashlib.sha256((ROOT/'paper/main.pdf').read_bytes()).hexdigest())
    (out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))


if __name__=='__main__': main()
