"""Independent small delayed tank/controller adoption example.

Sensor sample deletions are not fly connection deletions. This is an executable
reuse/record-integrity example, not another neural performance benchmark.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from .contract import Campaign,Evidence

DT=.1
N=40
DELAY=.15
LEAK=.04
CONFIG=dict(dt_s=DT,horizon_s=N*DT,delay_s=DELAY,leak_per_s=LEAK,
    initial_level=.5,safe_interval=[.2,.8],inflow_mean={'low':.15,'high':.28},
    initial_outflow=.18,measurement_noise_width=.02,resource_unit='valid sensor updates')


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def streams(seed):
    return np.random.default_rng(np.random.SeedSequence([20261023,seed,11])).random((N,2),dtype=np.float32)


def mask(seed,fault):
    f={'healthy':0.,'F2_25':.25,'F2_50':.5}[fault]
    return np.random.default_rng(np.random.SeedSequence([20261023,seed,12])).random(N)<f


def run(seed,condition,law,fault):
    u=streams(seed);removed=mask(seed,fault);level=.5;measurement=.5
    commands=[];last_action=.18;failure=None;updates=0;log=[]
    for k in range(N):
        start,end=k*DT,(k+1)*DT
        inflow=CONFIG['inflow_mean'][condition]+.08*(float(u[k,0])-.5)
        for when,value in commands:
            if when<=start+1e-12:last_action=value
        pending=[(when,value) for when,value in commands if start+1e-12<when<end-1e-12]
        cuts=[start]+[p[0] for p in pending]+[end];segments=[]
        for a,b in zip(cuts[:-1],cuts[1:]):
            for when,value in commands:
                if when<=a+1e-12:last_action=value
            initial=level;equilibrium=(inflow-last_action)/LEAK
            level=equilibrium+(level-equilibrium)*math.exp(-LEAK*(b-a))
            crossed=None
            for bound in [.2,.8]:
                if (initial-bound)*(level-bound)<=0 and initial!=level:
                    ratio=(bound-equilibrium)/(initial-equilibrium)
                    if ratio>0:
                        hit=a-math.log(ratio)/LEAK
                        if a-1e-9<=hit<=b+1e-9:crossed=hit if crossed is None else min(hit,crossed)
            if failure is None and crossed is not None:failure=crossed
            segments.append(dict(start_s=a,end_s=b,initial=initial,final=level,inflow=inflow,outflow=last_action,failure_s=crossed))
        if not removed[k]:measurement=level+.02*(float(u[k,1])-.5);updates+=1
        requested=float(np.clip(.18+1.2*(measurement-.5),0,.4)) if law=='proportional' else (.35 if measurement>.5 else .05)
        available=end+DELAY;commands.append((available,requested))
        log.append(dict(start_s=start,end_s=end,decision_s=end,available_s=available,resource=updates,
            level=level,measurement=measurement,valid_sample=not bool(removed[k]),requested=requested,segments=segments))
    return dict(adapter='tank-v1',seed=seed,condition=condition,law=law,fault=fault,config=CONFIG,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),uniform_sha256=hashlib.sha256(u.tobytes()).hexdigest(),
        mask_sha256=hashlib.sha256(np.packbits(removed).tobytes()).hexdigest(),deleted=int(removed.sum()),
        failure_s=failure,success=failure is None,log=log)


class TankAdapter:
    spec=Campaign(tuple(range(9000,9008)),('low','high'),('proportional','relay'),('healthy','F2_25','F2_50'),N*DT,DT,'valid sensor updates')

    def normalize(self,r):
        frames=[dict(start_s=q['start_s'],end_s=q['end_s'],decision_s=q['decision_s'],
                     usable_after_s=q['available_s'],resource=q['resource']) for q in r['log']]
        return Evidence(r['seed'],r['condition'],r['law'],r['fault'],r['config']['horizon_s'],r['config']['dt_s'],
            dict(adapter=r['adapter'],config=digest(r['config']),source=r['source_sha256']),r['uniform_sha256'],r['mask_sha256'],
            r['deleted'],frames,r['failure_s'],r['success'],r)

    def check_pair(self,group):
        for r in group:
            m=mask(r.cluster,r.fault)
            if r.mask_sha256!=hashlib.sha256(np.packbits(m).tobytes()).hexdigest() or r.deleted!=int(m.sum()):raise ValueError('sensor mask replay')
        if group:
            a,b=mask(group[0].cluster,'F2_25'),mask(group[0].cluster,'F2_50')
            if np.any(a&~b):raise ValueError('non-nested sensor masks')

    def check_native(self,e):
        r=e.native
        def close(x,y,label):
            if not math.isclose(x,y,rel_tol=0,abs_tol=1e-9):raise ValueError(label)
        if r['config']!=CONFIG:raise ValueError('plant config binding')
        if r['source_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise ValueError('source binding')
        us=streams(e.cluster);removed=mask(e.cluster,e.fault)
        if hashlib.sha256(us.tobytes()).hexdigest()!=e.uniform_sha256:raise ValueError('uniform regeneration')
        h=.5;measured=.5;queue=[];last=.18;resource=0;first_failure=None
        for k,q in enumerate(r['log']):
            a,b=k*.1,(k+1)*.1
            close(q['decision_s'],b,'causal decision time');close(q['available_s'],b+.15,'exact actuator delay')
            rate=CONFIG['inflow_mean'][e.condition]+.08*(float(us[k,0])-.5)
            boundaries=sorted({a,b}|{t for t,v in queue if a+1e-12<t<b-1e-12})
            if len(q['segments'])!=len(boundaries)-1:raise ValueError('actuator event partition')
            for (t0,t1),segment in zip(zip(boundaries[:-1],boundaries[1:]),q['segments']):
                close(segment['start_s'],t0,'segment start');close(segment['end_s'],t1,'segment end')
                for when,value in queue:
                    if when<=t0+1e-12:last=value
                close(segment['outflow'],last,'applied historical control');close(segment['inflow'],rate,'physical input')
                decay=math.exp(-.04*(t1-t0));new=h*decay+(rate-last)*(1-decay)/.04
                close(segment['initial'],h,'plant state continuity');close(segment['final'],new,'independent tank transition')
                local=None
                for boundary in [.2,.8]:
                    if (h-boundary)*(new-boundary)<=0 and h!=new:
                        eq=(rate-last)/.04;z=(boundary-eq)/(h-eq)
                        if z>0:
                            hit=t0-math.log(z)/.04
                            if t0-1e-9<=hit<=t1+1e-9:local=hit if local is None else min(hit,local)
                if (local is None)!=(segment['failure_s'] is None):raise ValueError('within-segment failure')
                if local is not None:close(local,segment['failure_s'],'failure time')
                if first_failure is None:first_failure=local
                h=new
            close(q['level'],h,'frame state')
            if not removed[k]:measured=h+.02*(float(us[k,1])-.5);resource+=1
            if q['valid_sample']!=bool(not removed[k]):raise ValueError('faulted sample use')
            close(q['measurement'],measured,'measurement/hold semantics');close(q['resource'],resource,'sensor resource accounting')
            requested=max(0.,min(.4,.18+1.2*(measured-.5))) if e.law=='proportional' else (.35 if measured>.5 else .05)
            close(q['requested'],requested,'controller law');queue.append((b+.15,requested))
        if (first_failure is None)!=(r['failure_s'] is None):raise ValueError('final task label')
        if first_failure is not None:close(first_failure,r['failure_s'],'final first failure')
