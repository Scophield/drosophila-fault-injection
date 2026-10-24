"""Non-mutating regression probe for genuine timing errors in the old V8 logs.

V8 and V9 are different protocols. This probe does not normalize V8 as V9 or
pool their scientific outcomes; it establishes that challenge failure modes
include errors actually observed in archived engineering data.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();paths=sorted(Path('runs/controller-fault-v8/vision/episodes_controls').glob('*.json'))
    assert paths
    records=[];flag_errors=[];delay_errors=[];completed_duration_errors=[]
    for p in paths:
        r=json.loads(p.read_text());trigger=r['trigger_ms'];horizon=r['horizon_ms']
        row=dict(path=p.as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),trigger_ms=trigger)
        if r['escaped'] and trigger is not None:
            exact=trigger+250<=horizon<trigger+700
            if r['burst_active_at_horizon']!=exact:
                flag_errors.append(dict(path=p.as_posix(),recorded=r['burst_active_at_horizon'],expected_at_exact_horizon=exact))
        active=[q for q in r['log'] if q['burst']]
        if active:
            delay=active[0]['t_ms']-trigger;duration=sum(q['t_end_ms']-q['t_ms'] for q in active)
            ended=any(q['t_ms']>=active[-1]['t_end_ms'] and not q['burst'] for q in r['log'])
            row.update(realized_delay_ms=delay,observed_burst_ms=duration,completed_burst=ended)
            if delay!=250:delay_errors.append(dict(path=p.as_posix(),nominal_ms=250,realized_ms=delay))
            if ended and duration!=450:completed_duration_errors.append(dict(path=p.as_posix(),nominal_ms=450,realized_ms=duration))
        records.append(row)
    a.out.mkdir(parents=True,exist_ok=False)
    report=dict(completed=True,records=len(records),protocol_scope='V8 archived engineering regression only; no new neural simulation or pooling with V9/V10',
        horizon_flag_errors=flag_errors,delay_errors=delay_errors,completed_duration_errors=completed_duration_errors,
        all_records=records,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        interpretation='These genuine archived error types motivate the deliberately corrupted V10 regression cases. Current V9 exact-event traces are separately checked by independent replay.')
    (a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(records=len(records),horizon_flag_errors=len(flag_errors),delay_errors=len(delay_errors),completed_duration_errors=len(completed_duration_errors)),indent=2))


if __name__=='__main__':main()
