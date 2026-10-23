"""Descriptive same-trigger and precontact steering diagnostics, no tuning."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();paths=sorted((a.root/'episodes').glob('*.json'));rs=[json.loads(p.read_text()) for p in paths]
    if len(rs) not in [288,96]:raise ValueError('complete core or stress required')
    lookup={(r['seed'],r['phi_deg'],r['fault'],r['mode']):r for r in rs};checks=[];rows=[]
    for r in rs:
        q=next(q for q in r['log'] if q['t_end_ms']==400)
        if r['collision_ms'] is not None and r['collision_ms']<=400:raise ValueError('postcontact diagnostic prefix')
        rows.append(dict(seed=r['seed'],phi_deg=r['phi_deg'],fault=r['fault'],mode=r['mode'],
            trigger_ms=r['trigger_ms'],heading_400_deg=q['heading_deg'],
            collision_ms=r['collision_ms'],escaped=r['escaped']))
        if r['mode']!='proportional':continue
        other=lookup[(r['seed'],r['phi_deg'],r['fault'],'relay')]
        td=r['trigger_ms'];same=td==other['trigger_ms']
        prefix_equal=same and all(x['cmd_rates']==y['cmd_rates'] and x['n_total']==y['n_total']
            and x['fly']==y['fly'] and x['target']==y['target']
            for x,y in zip(r['log'],other['log']) if td is None or x['t_end_ms']<=td)
        checks.append(dict(seed=r['seed'],phi_deg=r['phi_deg'],fault=r['fault'],same_trigger=same,same_predecision_trace=prefix_equal))
    groups=[]
    for mode in ['proportional','relay']:
        for fault in ['healthy','F2_25','F2_50']:
            group=[r for r in rows if (r['mode'],r['fault'])==(mode,fault)]
            groups.append(dict(mode=mode,fault=fault,n=len(group),median_trigger_ms=statistics.median(r['trigger_ms'] for r in group if r['trigger_ms'] is not None),
                median_abs_heading_400_deg=statistics.median(abs(r['heading_400_deg']) for r in group)))
    a.out.mkdir(parents=True,exist_ok=False)
    for name,items in [('episodes.csv',rows),('pair-checks.csv',checks),('groups.csv',groups)]:
        with (a.out/name).open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    report=dict(complete=True,role='post hoc descriptive mechanism diagnostic; no metric threshold or new hypothesis test',
        records=len(rs),paired_law_scenarios=len(checks),same_trigger_pairs=sum(r['same_trigger'] for r in checks),
        same_predecision_trace_pairs=sum(r['same_predecision_trace'] for r in checks),groups=groups,
        interpretation='Both laws share their first trigger because steering is gated below that same threshold. Their later turning differs; equal maximum turn rate does not match executed turning effort. Heading at400ms is before every contact. This is not an actuator-energy measurement or a causal mediation estimate.',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        raw_input_sha256={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (a.out/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='raw_input_sha256'},indent=2))


if __name__=='__main__':main()
