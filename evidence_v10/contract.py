"""Plant-neutral checks. Adapters own semantics, input replay and dynamics checks.

The interface does not infer physical validity, authenticate a dishonest logger,
verify unlogged neural state, guarantee CRN variance reduction or certify safety.
"""
from dataclasses import dataclass,field
import itertools
import math
import re
from typing import Any,Protocol


@dataclass
class Evidence:
    cluster:int
    condition:Any
    law:str
    fault:str
    horizon_s:float
    frame_s:float
    bindings:dict
    uniform_sha256:str
    mask_sha256:str
    deleted:int
    frames:list
    failure_s:float|None
    success:bool
    native:dict=field(repr=False)

    @property
    def key(self):return self.cluster,self.condition,self.law,self.fault


@dataclass(frozen=True)
class Campaign:
    clusters:tuple
    conditions:tuple
    laws:tuple
    faults:tuple
    horizon_s:float
    frame_s:float
    resource_unit:str

    def __post_init__(self):
        for name in ['clusters','conditions','laws','faults']:
            values=getattr(self,name)
            try:unique=len(set(values))
            except TypeError as exc:raise ValueError(name+' must contain hashable identities') from exc
            if not values or unique!=len(values):raise ValueError(name+' must be nonempty and unique')
        try:
            valid=math.isfinite(self.horizon_s) and math.isfinite(self.frame_s) and self.horizon_s>0 and self.frame_s>0
        except TypeError:valid=False
        if not valid:raise ValueError('positive finite horizon/frame durations in seconds required')
        frames=self.horizon_s/self.frame_s
        if not math.isclose(frames,round(frames),rel_tol=0,abs_tol=1e-9):raise ValueError('horizon must contain complete observation frames')
        if not isinstance(self.resource_unit,str) or not self.resource_unit.strip():raise ValueError('resource unit required')


@dataclass(frozen=True)
class Issue:
    code:str
    key:tuple|None
    detail:str


class Adapter(Protocol):
    def check_native(self,record:Evidence)->None:...
    def check_pair(self,records:list[Evidence])->None:...


def prefix(record:Evidence,end_s:float)->list:
    """Only completed observations available by the requested time, no labels."""
    if not math.isfinite(end_s) or not 0<=end_s<=record.horizon_s:raise ValueError('prefix time')
    return [dict(q) for q in record.frames if q['end_s']<=end_s+1e-12]


def audit(records:list[Evidence],spec:Campaign,adapter:Adapter|None=None)->list[Issue]:
    issues=[]
    def issue(code,key,detail):issues.append(Issue(code,key,str(detail)))
    expected=set(itertools.product(spec.clusters,spec.conditions,spec.laws,spec.faults))
    keys=[r.key for r in records]
    if len(keys)!=len(set(keys)):issue('duplicate-cell',None,'duplicate cluster/condition/law/fault')
    if set(keys)!=expected:issue('matrix-membership',None,f'missing={len(expected-set(keys))}, extra={len(set(keys)-expected)}')
    if not records:return issues
    binding=records[0].bindings
    for r in sorted(records,key=lambda r:repr(r.key)):
        if r.bindings!=binding:issue('mixed-bindings',r.key,'map/calibration/source/config differ')
        for name,value in [('uniform',r.uniform_sha256),('mask',r.mask_sha256)]:
            if not re.fullmatch('[0-9a-f]{64}',value):issue('invalid-digest',r.key,name)
        if not math.isfinite(r.horizon_s) or not math.isfinite(r.frame_s) or r.horizon_s<=0 or r.frame_s<=0:
            issue('invalid-clock',r.key,'horizon/frame must be positive finite seconds');continue
        if not math.isclose(r.horizon_s,spec.horizon_s,abs_tol=1e-12) or not math.isclose(r.frame_s,spec.frame_s,abs_tol=1e-12):
            issue('exposure-contract',r.key,'wrong declared horizon/frame')
        if not math.isclose(len(r.frames)*r.frame_s,r.horizon_s,abs_tol=1e-9):issue('incomplete-exposure',r.key,'missing/extra frames')
        if r.failure_s is not None and (not math.isfinite(r.failure_s) or not 0<=r.failure_s<=r.horizon_s):issue('invalid-failure-time',r.key,'outside horizon')
        if r.success!=(r.failure_s is None):issue('outcome-label',r.key,'success must mean no failure through horizon')
        last=0.
        for i,q in enumerate(r.frames):
            required=['start_s','end_s','decision_s','usable_after_s','resource']
            if any(k not in q or not isinstance(q[k],(int,float)) or isinstance(q[k],bool) or not math.isfinite(q[k]) for k in required):
                issue('invalid-frame-schema',r.key,f'nonfinite/missing/nonnumeric field in frame {i}');continue
            start,end=i*r.frame_s,(i+1)*r.frame_s
            if not math.isclose(q['start_s'],start,abs_tol=1e-9) or not math.isclose(q['end_s'],end,abs_tol=1e-9):issue('frame-clock',r.key,f'frame {i}')
            if q['decision_s']>q['usable_after_s']+1e-12 or q['decision_s']<q['end_s']-1e-12:issue('decision-availability',r.key,f'frame {i}')
            value=q['resource']
            if not math.isfinite(value) or value<last:issue('resource-accounting',r.key,f'frame {i}')
            last=value
        if r.deleted<0:issue('fault-accounting',r.key,'negative deleted count')
        if adapter is not None:
            try:adapter.check_native(r)
            except (ValueError,AssertionError,KeyError,TypeError,IndexError) as error:issue('adapter-replay',r.key,error)
    for seed in spec.clusters:
        group=[r for r in records if r.cluster==seed]
        if len({r.uniform_sha256 for r in group})>1:issue('unpaired-uniforms',(seed,),'common variates differ; realized events need not match')
        for fault in spec.faults:
            rr=[r for r in group if r.fault==fault]
            if len({(r.mask_sha256,r.deleted) for r in rr})>1:issue('unpaired-mask',(seed,fault),'mask differs across law/condition')
        if adapter is not None:
            try:adapter.check_pair(group)
            except (ValueError,AssertionError,KeyError,TypeError,IndexError) as error:issue('adapter-pair-replay',(seed,),error)
    return issues


def decode_and_audit(rows,spec,adapter):
    """Normalize untrusted native rows, retaining parse errors as audit findings."""
    records=[];errors=[]
    for i,row in enumerate(rows):
        try:records.append(adapter.normalize(row))
        except (ValueError,AssertionError,KeyError,TypeError,IndexError) as error:
            errors.append(Issue('native-schema',None,f'row {i}: {error}'))
    return records,errors+audit(records,spec,adapter)
