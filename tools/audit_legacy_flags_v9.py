"""Audit ALL source-qualified old horizon flags; deduplicate reused records."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    manifests={sha(p):p for p in (ROOT/'runs').glob('*/vision/batches/*/run_manifest.json')}
    unique={}
    for p in (ROOT/'runs').glob('*/vision/episodes*/*.json'):
        r=json.loads(p.read_text())
        if 'burst_active_at_horizon' not in r or r.get('protocol_version')!='geometry-v2':continue
        unique.setdefault(sha(p),dict(paths=[],record=r))['paths'].append(p.relative_to(ROOT).as_posix())
    rows=[];unverified=[]
    for digest,item in unique.items():
        r=item['record'];path=manifests.get(r.get('run_manifest_sha256'))
        if path is None:
            unverified.append(dict(sha256=digest,paths=item['paths'],reason='generation manifest unavailable'));continue
        m=json.loads(path.read_text());name=next((n for n in m.get('source_sha256',{}) if n.replace('\\','/')=='sim_vision/run_closedloop.py'),None)
        source=path.parent/'source'/name.replace('\\','/') if name else None
        if source is None or not source.is_file() or sha(source)!=m['source_sha256'][name]:
            unverified.append(dict(sha256=digest,paths=item['paths'],reason='exact generating source unavailable'));continue
        match=re.search(r'^BURST_S\s*=\s*([0-9.]+)',source.read_text(),re.M)
        delay=m['parameters'].get('burst_delay_ms')
        if not match or delay is None:
            unverified.append(dict(sha256=digest,paths=item['paths'],reason='cannot recover scheduled timing'));continue
        duration=float(match.group(1))*1000;trigger=r['trigger_ms'];horizon=r['horizon_ms']
        exact=bool(r['escaped'] and trigger is not None and trigger+delay<=horizon<trigger+delay+duration)
        rows.append(dict(sha256=digest,paths=sorted(item['paths']),seed=r['seed'],mode=r['mode'],fault=r['fault'],
            phi_deg=r['phi_t_deg'],escaped=r['escaped'],horizon_ms=horizon,
            trigger_ms=trigger,delay_ms=delay,burst_ms=duration,
            recorded=r['burst_active_at_horizon'],at_exact_horizon=exact,
            mismatch=exact!=r['burst_active_at_horizon']))
    args.out.mkdir(parents=True,exist_ok=False)
    report=dict(unique_records=len(unique),qualified=len(rows),unverified=unverified,
        mismatches=[r for r in rows if r['mismatch']],records=rows,
        note='old scheduled state at frame-aligned horizons; source-qualified, reused records deduplicated; raw records unchanged')
    (args.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['records','unverified']},indent=2))
    print('Unverified:',len(unverified))


if __name__=='__main__':main()
