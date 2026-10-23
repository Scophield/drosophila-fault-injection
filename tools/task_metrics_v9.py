"""Fixed-prefix metrics and seed-cluster statistics; no access to future labels."""
from collections import Counter
import numpy as np
from task_v9 import motion

WINDOW=400.


def reference_key(record,references):
    exact=f"{record['mode']}/{record['phi_deg']:g}"
    if exact in references: return exact
    # Prespecified off-angle stress transfer: retain the calibration reference
    # on the SAME side. Never estimate a new threshold from stress outcomes.
    side=30 if record['phi_deg']>0 else -30
    return f"{record['mode']}/{side:g}"


def prefix(record,t=WINDOW):
    return next(q for q in record['log'] if q['t_end_ms']==t)


def features(record,t=WINDOW):
    rows=[q for q in record['log'] if 100<q['t_end_ms']<=t]
    q=prefix(record,t)
    command=sum(sum(r['cmd_rates'])*.02 for r in rows)/(8*((t-100)/1000))
    return dict(command_hz=command,activity=q['n_total'],
                deadline=forecast_margin(q,record['burst_delay_ms'],record['horizon_ms']),
                schedule_only=forecast_margin({**q,'next_omega':0.},record['burst_delay_ms'],record['horizon_ms']))


def forecast_margin(q,delay,horizon):
    """Held-command kinematic forecast, using ONLY information at the prefix.

    Future turn command is held constant. If no burst is scheduled, assume the
    earliest next-frame trigger. This is an optimistic extrapolation, not a
    reachable-set proof. State estimates are exact simulated geometry, so this
    is not a neural-only detector or a deployable sensor implementation.
    """
    fly=np.array(q['fly']); target=np.array(q['target'])
    heading=np.radians(q['heading_deg']); omega=q['next_omega']
    trigger=q['trigger_ms'] if q['trigger_ms'] is not None else q['t_end_ms']+20
    minimum=float(np.linalg.norm(target-fly))
    for t in np.arange(q['t_end_ms'],horizon,20):
        fly,target,heading,segs=motion(fly,target,heading,omega,float(t),float(t+20),trigger,delay=delay)
        minimum=min(minimum,*[s['min_distance'] for s in segs])
    return minimum-.05


def stop_time(record):
    if record['collision_ms'] is None: return record['horizon_ms']
    return next(q['t_end_ms'] for q in record['log'] if q['collision_ms'] is not None)


def calibration_thresholds(records):
    healthy=[r for r in records if r['fault']=='healthy']
    fs=[features(r) for r in healthy]
    references={}
    for mode in ['proportional','relay']:
        for phi in [-30.,30.]:
            values=[features(r)['activity'] for r in healthy if (r['mode'],r['phi_deg'])==(mode,phi)]
            references[f'{mode}/{phi:g}']=float(np.median(values))
    ratios=[f['activity']/references[f"{r['mode']}/{r['phi_deg']:g}"] for r,f in zip(healthy,fs)]
    radius=float(np.quantile(np.abs(np.log(ratios)),.95))
    return dict(window_ms=WINDOW,command_lower_hz=float(np.quantile([f['command_hz'] for f in fs],.05)),
        activity_reference=references,activity_lower=float(np.exp(-radius)),
        activity_upper=float(np.exp(radius)),activity_abs_log_upper=radius,
        deadline_lower_m=float(np.quantile([f['deadline'] for f in fs],.05)),
        schedule_lower_m=float(np.quantile([f['schedule_only'] for f in fs],.05)),
        method='healthy-validation-only 5th percentile of command/margin, 95th percentile absolute log activity ratio; same nominal 5% healthy flag rate. All healthy records retained, including failed tasks; no fault outcomes used. This is not guaranteed task FPR.',
        n_healthy=len(healthy))


def flags(record,thresholds,healthy_pair=None):
    f=features(record)
    reference=thresholds['activity_reference'][reference_key(record,thresholds['activity_reference'])]
    ratio=f['activity']/reference
    result=dict(transmission=f['command_hz']<thresholds['command_lower_hz'],
        equal_duration_upper=ratio>2,
        equal_duration_two_sided=ratio<thresholds['activity_lower'] or ratio>thresholds['activity_upper'],
        deadline=f['deadline']<thresholds['deadline_lower_m'])
    result['schedule_only']=f['schedule_only']<thresholds['schedule_lower_m']
    if healthy_pair is not None:
        stopped=prefix(record,stop_time(record))['n_total']
        ref=prefix(healthy_pair,stop_time(healthy_pair))['n_total']
        result['stop_count_upper']=stopped>2*ref
    return result


def bootstrap_indices(n,draws=20000,seed=20261022):
    return np.random.default_rng(seed).integers(n,size=(draws,n))


def mean_interval(values,indices):
    v=np.asarray(values,float)
    samples=v[indices].mean(axis=1)
    return dict(estimate=float(v.mean()),low=float(np.quantile(samples,.025)),high=float(np.quantile(samples,.975)))


def sign_flip_p(values):
    # Each cluster contrast is in multiples of 1/2. Dynamic programming exactly
    # enumerates the signed-sum distribution, including zero-valued clusters.
    vals=np.asarray(values)*2
    if not np.allclose(vals,np.rint(vals)): raise ValueError('non-half-integer contrast')
    counts=Counter({0:1})
    for v in np.rint(vals).astype(int):
        nxt=Counter()
        for total,n in counts.items():
            nxt[total+int(v)]+=n; nxt[total-int(v)]+=n
        counts=nxt
    observed=abs(int(round(vals.sum())))
    return sum(n for total,n in counts.items() if abs(total)>=observed)/(2**len(vals))


def confusion(records,values):
    y=np.array([not r['escaped'] for r in records]); p=np.asarray(values,bool)
    tp=int(np.sum(y&p)); fp=int(np.sum(~y&p)); tn=int(np.sum(~y&~p)); fn=int(np.sum(y&~p))
    return dict(tp=tp,fp=fp,tn=tn,fn=fn,sensitivity=tp/(tp+fn) if tp+fn else None,
        specificity=tn/(tn+fp) if tn+fp else None,false_positive_rate=fp/(fp+tn) if fp+tn else None,
        false_negative_rate=fn/(fn+tp) if fn+tp else None)
