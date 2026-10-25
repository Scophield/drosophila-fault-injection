"""Retrospective all-record burst-end diagnosis. No neural simulation or fitting."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
R,VP,VW,VB,DT=.05,.30,.05,.35,.02
CMAX=VP+VW
CMIN=VP*np.sqrt(1-(VW*DT/R)**2)-VW
SEED=20261025
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))


def hit(a,b):
    if a@a<=R*R:return 0.
    d=b-a;aa=d@d;bb=2*(a@d);cc=a@a-R*R;disc=bb*bb-4*aa*cc
    if aa==0 or disc<0:return None
    u=(-bb-np.sqrt(disc))/(2*aa)
    return float(u) if 0<=u<=1 else None


def closest(a,b):
    d=b-a;n=d@d;t=float(np.clip(-(a@d)/n,0,1)) if n else 0.
    return float(np.linalg.norm(a+t*d))


def forecast(state,start,end,omega=0.):
    """No record/outcome/future-command argument: landmark state and physics only."""
    fly=np.array(state['fly'],float).copy();target=np.array(state['target'],float).copy()
    heading=float(state['heading']);minimum=float(np.linalg.norm(target-fly));contact=None
    t=float(start)
    while t<end-1e-8:
        stop=min(t+20.,end);dt=(stop-t)/1000.;a=target-fly
        vf=VW*np.array([np.cos(heading),np.sin(heading)]);vt=-VP*a/np.linalg.norm(a)
        fly+=vf*dt;target+=vt*dt;b=target-fly
        minimum=min(minimum,closest(a,b));u=hit(a,b)
        if contact is None and u is not None:contact=t+u*(stop-t)
        heading=float(np.clip(heading+np.radians(omega)*dt,-np.radians(100),np.radians(100)))
        t=stop
    return dict(min_clearance_m=minimum-R,contact_ms=contact)


def reconstruct(r):
    """Check saved geometry and exact first contact using recorded prior commands."""
    fly=np.zeros(2);target=.25*np.array([np.cos(np.radians(r['phi_deg'])),np.sin(np.radians(r['phi_deg']))])
    heading=0.;omega=0.;trigger=None;first=None;minimum=.25;states={};pre_vel={}
    assert len(r['log'])==50 and r['horizon_ms']==1000.
    for k,q in enumerate(r['log']):
        assert q['t_ms']==20*k and q['t_end_ms']==20*(k+1)
        cuts=[q['t_ms'],q['t_end_ms']]
        if trigger is not None:cuts+=[x for x in [trigger+250,trigger+700] if cuts[0]<x<cuts[1]]
        cuts=sorted(cuts);assert len(q['segments'])==len(cuts)-1
        for (a,b),seg in zip(zip(cuts[:-1],cuts[1:]),q['segments']):
            assert a==seg['start_ms'] and b==seg['end_ms']
            active=trigger is not None and trigger+250<=a<trigger+700
            assert bool(seg['burst'])==active
            before=target-fly;vf=(VB if active else VW)*np.array([np.cos(heading),np.sin(heading)])
            vt=-VP*before/np.linalg.norm(before);dt=(b-a)/1000
            fly=fly+vf*dt;target=target+vt*dt;after=target-fly
            sep=closest(before,after);assert abs(sep-seg['min_distance'])<1e-10
            minimum=min(minimum,sep);u=hit(before,after);contact=None if u is None else a+u*(b-a)
            assert (contact is None)==(seg['contact_ms'] is None)
            if contact is not None:
                assert abs(contact-seg['contact_ms'])<1e-6
                if first is None:first=contact
            pre_vel[b]=float((after/np.linalg.norm(after))@(vt-vf))
            if not active:heading=float(np.clip(heading+np.radians(omega)*dt,-np.radians(100),np.radians(100)))
        assert np.allclose(fly,q['fly'],atol=1e-11,rtol=0)
        assert np.allclose(target,q['target'],atol=1e-11,rtol=0)
        assert abs(np.degrees(heading)-q['heading_deg'])<1e-8
        assert abs(np.linalg.norm(target-fly)-q['distance'])<1e-10
        states[q['t_end_ms']]=dict(fly=fly.copy(),target=target.copy(),heading=heading,omega=q['next_omega'])
        trigger=q['trigger_ms'];omega=q['next_omega']
    assert (first is None)==(r['collision_ms'] is None) and r['escaped']==(first is None)
    if first is not None:assert abs(first-r['collision_ms'])<1e-6
    assert abs(minimum-r['min_distance'])<1e-10
    assert trigger==r['trigger_ms']
    return states,pre_vel


def outcome_record(tag,p,r,thresholds):
    states,pre=reconstruct(r);trig=r['trigger_ms'];H=r['horizon_ms'];tc=r['collision_ms']
    B=None if trig is None else trig+r['burst_delay_ms']+r['burst_duration_ms']
    on=None if trig is None else trig+r['burst_delay_ms']
    assert r['burst_delay_ms']==250. and r['burst_duration_ms']==450.
    key=f"{tag}/{r['seed']}/{r['phi_deg']:g}/{r['mode']}/{r['fault']}"
    row=dict(key=key,RF=tag,seed=r['seed'],bearing_deg=r['phi_deg'],law=r['mode'],fault=r['fault'],
        trigger_ms=trig,burst_start_ms=on,burst_end_ms=B,horizon_ms=H,
        remaining_ms=None if B is None else max(0,H-B),first_contact_ms=tc,success_through_H=r['escaped'],
        mask_sha256=r['mask_sha256'],uniform_sha256=r['uniform_sha256'],source=p.relative_to(ROOT).as_posix(),source_sha256=sha(p))
    if trig is None:burst='no_trigger'
    elif on>=H:burst='not_started_by_H'
    elif B>H:burst='ongoing_at_H'
    elif B==H:burst='ended_at_H'
    else:burst='ended_before_H'
    if tc is None:phase='no_contact'
    elif trig is None:phase='contact_without_trigger'
    elif tc<on:phase='pre_burst'
    elif tc<=B:phase='during_or_at_burst_end'
    else:phase='post_burst'
    if tc is not None and (B is None or tc<=B):status='prior_contact'
    elif burst=='ended_before_H':status='at_risk'
    elif burst=='ended_at_H':status='zero_followup'
    else:status=burst
    row.update(burst_status=burst,contact_phase=phase,landmark_status=status,
        valid_prospective_state=status=='at_risk',post_contact_counterfactual_state=bool(tc is not None and B is not None and tc<=B),
        late_contact=None if status!='at_risk' else tc is not None,
        time_to_contact_from_B_ms=None if status!='at_risk' or tc is None else tc-B)
    cmd400=[q for q in r['log'] if 100<q['t_end_ms']<=400]
    row['command_hz_400']=sum(sum(q['cmd_rates'])*.02 for q in cmd400)/(8*.3)
    row['command_warning_400']=row['command_hz_400']<thresholds['command_lower_hz']
    if B is not None and B<=H:
        assert B in states,'Never snap an unobserved event to a nearby frame'
        s=states[B];rel=s['target']-s['fly'];d=float(np.linalg.norm(rel));u=np.array([np.cos(s['heading']),np.sin(s['heading'])])
        cosbeta=float((rel/d)@u);beta=float(np.degrees(np.arccos(np.clip(cosbeta,-1,1))))
        T=(H-B)/1000;C=d-R
        row.update(center_distance_B_mm=1000*d,clearance_B_mm=1000*C,
            heading_B_deg=float(np.degrees(s['heading'])),abs_heading_B_deg=abs(float(np.degrees(s['heading']))),
            bearing_to_pursuer_B_deg=beta,cos_bearing_B=cosbeta,current_turn_B_deg_s=s['omega'],
            radial_velocity_pre_B_m_s=pre[B],radial_velocity_post_B_m_s=-VP-VW*cosbeta,
            speed_transition_reverses_radial_motion=pre[B]>0,
            clearance_per_remaining_s_m_s=None if T<=0 else C/T,
            margin_stationary_mm=1000*(C-VP*T),margin_radial_mm=1000*(C-(VP+VW*cosbeta)*T),
            margin_slow_bound_mm=1000*(C-CMIN*T),margin_fast_bound_mm=1000*(C-CMAX*T))
        if status=='at_risk':
            assert C>0 and T>0
            row['bound_zone']='unavoidable' if C<CMIN*T-1e-10 else 'guaranteed_safe' if C>CMAX*T+1e-10 else 'ambiguous'
            if row['bound_zone']=='unavoidable':assert tc is not None,'Contradiction of model lower closure bound'
            if row['bound_zone']=='guaranteed_safe':assert tc is None,'Contradiction of model upper closure bound'
            for prefix,turn in [('held_heading',0.),('held_turn',s['omega'])]:
                f=forecast(s,B,H,turn);row[prefix+'_margin_mm']=1000*f['min_clearance_m'];row[prefix+'_contact_ms']=f['contact_ms']
                row[prefix+'_warning']=f['contact_ms'] is not None
                f100=forecast(s,B,B+100,turn) if H-B>=100 else None
                row[prefix+'_margin_100ms_mm']=None if f100 is None else 1000*f100['min_clearance_m']
                row[prefix+'_warning_100ms']=None if f100 is None else f100['contact_ms'] is not None
            row['late_contact_100ms']=None if H-B<100 else tc is not None and tc<=B+100
            before_failure=[q for q in r['log'] if B<q['t_end_ms']<=min(H,tc if tc is not None else H)]
            row['future_max_heading_change_diagnostic_deg']=max([0.]+[abs(q['heading_deg']-row['heading_B_deg']) for q in before_failure])
            row['future_nonzero_command_frames_diagnostic']=sum(abs(q['next_omega'])>1e-9 for q in before_failure)
            row['diagnostic_future_frames_observed']=len(before_failure)
    return row


def export(path,rows):
    if not rows:return
    columns=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,columns);w.writeheader();w.writerows(rows)


def auc(y,score):
    p=score[y];n=score[~y]
    if not len(p) or not len(n):return None
    return float(np.mean((p[:,None]>n[None,:])+.5*(p[:,None]==n[None,:])))


def interval(x):
    x=x[np.isfinite(x)]
    return None if not len(x) else list(map(float,np.quantile(x,[.025,.975])))


def score_set(rows,seeds,pred,score,label,draws,endpoint='late_contact'):
    y=np.array([r[endpoint] for r in rows],bool);s=np.array([score(r) for r in rows],float)
    seed_index={s:i for i,s in enumerate(seeds)};ix=np.array([seed_index[r['seed']] for r in rows],int)
    pos=np.bincount(ix[y],minlength=len(seeds));neg=np.bincount(ix[~y],minlength=len(seeds))
    bp=draws@pos;bn=draws@neg
    result=dict(metric=label,n=len(rows),contacts=int(y.sum()),successes=int((~y).sum()),independent_seeds=len(seeds),
        failure_seeds=int(np.sum(pos>0)),AUROC=auc(y,s),class_absent_bootstraps=int(np.sum((bp==0)|(bn==0))))
    kernel=np.zeros((len(seeds),len(seeds)))
    for i in range(len(seeds)):
        a=s[y&(ix==i)]
        for j in range(len(seeds)):
            b=s[(~y)&(ix==j)]
            if len(a) and len(b):kernel[i,j]=np.sum((a[:,None]>b[None,:])+.5*(a[:,None]==b[None,:]))
    with np.errstate(divide='ignore',invalid='ignore'):
        ba=np.einsum('bi,ij,bj->b',draws,kernel,draws)/(bp*bn)
    result['AUROC_CI95_conditional']=interval(ba)
    if pred is not None:
        p=np.array([pred(r) for r in rows],bool)
        tp=int(np.sum(y&p));fn=int(np.sum(y&~p));fp=int(np.sum(~y&p));tn=int(np.sum(~y&~p))
        result.update(tp=tp,fn=fn,fp=fp,tn=tn,sensitivity=tp/(tp+fn) if tp+fn else None,
            specificity=tn/(tn+fp) if tn+fp else None,FPR=fp/(fp+tn) if fp+tn else None)
        btp=draws@np.bincount(ix[y&p],minlength=len(seeds));bfp=draws@np.bincount(ix[(~y)&p],minlength=len(seeds))
        with np.errstate(divide='ignore',invalid='ignore'):
            result['sensitivity_CI95_conditional']=interval(btp/bp);result['FPR_CI95_conditional']=interval(bfp/bn)
        result['positive_class_absent_bootstraps']=int(np.sum(bp==0));result['negative_class_absent_bootstraps']=int(np.sum(bn==0))
    return result


def summaries(rows):
    result=[]
    for tag in ['RF-0','RF-A','RF-B']:
        for law in ['proportional','relay']:
            for fault in ['healthy','F2_25','F2_50']:
                group=[r for r in rows if r['RF']==tag and r['law']==law and r['fault']==fault]
                risk=[r for r in group if r['landmark_status']=='at_risk']
                item=dict(RF=tag,law=law,fault=fault,n=len(group),seeds=len({r['seed'] for r in group}),
                    all_contacts=sum(not r['success_through_H'] for r in group),at_risk=len(risk),
                    later_contacts=sum(bool(r['late_contact']) for r in risk))
                for status in ['prior_contact','no_trigger','not_started_by_H','ongoing_at_H','zero_followup']:item[status]=sum(r['landmark_status']==status for r in group)
                for zone in ['unavoidable','ambiguous','guaranteed_safe']:item[zone]=sum(r['bound_zone']==zone for r in risk)
                for feature in ['burst_end_ms','remaining_ms','clearance_B_mm','abs_heading_B_deg','margin_radial_mm']:
                    a=np.array([r[feature] for r in risk],float);item[feature+'_median']=float(np.median(a)) if len(a) else None
                    item[feature+'_range']=','.join(map(str,[a.min(),a.max()])) if len(a) else None
                result.append(item)
    return result


def pair_records(rows):
    lookup={(r['RF'],r['seed'],r['bearing_deg'],r['law'],r['fault']):r for r in rows};pairs=[]
    fields=['clearance_B_mm','remaining_ms','abs_heading_B_deg','margin_radial_mm']
    for r in rows:
        counterparts=[]
        if r['fault']!='healthy':counterparts.append(('fault_minus_healthy',lookup[r['RF'],r['seed'],r['bearing_deg'],r['law'],'healthy']))
        if r['law']=='proportional':counterparts.append(('P_minus_R',lookup[r['RF'],r['seed'],r['bearing_deg'],'relay',r['fault']]))
        for kind,b in counterparts:
            good=r['landmark_status']==b['landmark_status']=='at_risk'
            q=dict(kind=kind,RF=r['RF'],seed=r['seed'],bearing_deg=r['bearing_deg'],law=r['law'],fault=r['fault'],
                row_key=r['key'],reference_key=b['key'],row_status=r['landmark_status'],reference_status=b['landmark_status'],
                both_eligible=good,row_contact=not r['success_through_H'],reference_contact=not b['success_through_H'],
                endpoint_loss_difference=int(not r['success_through_H'])-int(not b['success_through_H']),
                mask_matched=r['mask_sha256']==b['mask_sha256'],uniform_matched=r['uniform_sha256']==b['uniform_sha256'])
            for f in fields:q[f+'_difference']=r[f]-b[f] if good else None
            pairs.append(q)
    assert sum(p['kind']=='fault_minus_healthy' for p in pairs)==384
    assert sum(p['kind']=='P_minus_R' for p in pairs)==288
    return pairs


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--draws',type=int,default=10000)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    manifests=[('RF-0','audit/acceptance-v9/core-v2/summary.json','runs/task-v9-frozen/registration-core.json'),
        ('RF-A','audit/v10/transfer-01/map-A/analysis/summary.json','runs/task-v10-transfer/map-A/registration.json'),
        ('RF-B','audit/v10/transfer-01/map-B/analysis/summary.json','runs/task-v10-transfer/map-B/registration.json')]
    baseline=read(ROOT/'PUBLIC_SCOPE.json');hashes={};rows=[];all_seeds={}
    for tag,summary,reg in manifests:
        summary=read(ROOT/summary);registration=read(ROOT/reg)
        for name,h in summary['raw_input_sha256'].items():
            p=ROOT/name;assert sha(p)==h;hashes[name]=h
            r=read(p);rows.append(outcome_record(tag,p,r,registration['thresholds']))
        group=[r for r in rows if r['RF']==tag];all_seeds[tag]=sorted({r['seed'] for r in group})
        assert len(group)==(288 if tag=='RF-0' else 144)
        for seed in all_seeds[tag]:
            s=[r for r in group if r['seed']==seed];assert len(s)==12 and len({r['uniform_sha256'] for r in s})==1
            for fault in ['healthy','F2_25','F2_50']:assert len({r['mask_sha256'] for r in s if r['fault']==fault})==1
    assert len(rows)==576;export(a.out/'all-records.csv',rows)
    accounting=summaries(rows);export(a.out/'accounting.csv',accounting)
    pairs=pair_records(rows);export(a.out/'all-pairs.csv',pairs)
    rng=np.random.default_rng(SEED);metrics=[];fixed=[];counterexamples=[]
    candidates=[('clearance_only',None,lambda r:-r['clearance_B_mm']),
        ('stationary_budget',lambda r:r['margin_stationary_mm']<=0,lambda r:-r['margin_stationary_mm']),
        ('radial_budget',lambda r:r['margin_radial_mm']<=0,lambda r:-r['margin_radial_mm']),
        ('held_heading',lambda r:r['held_heading_warning'],lambda r:-r['held_heading_margin_mm']),
        ('held_turn',lambda r:r['held_turn_warning'],lambda r:-r['held_turn_margin_mm']),
        ('unavoidable_bound',lambda r:r['bound_zone']=='unavoidable',lambda r:-r['margin_slow_bound_mm']),
        ('outside_guaranteed_safe_bound',lambda r:r['bound_zone']!='guaranteed_safe',lambda r:-r['margin_fast_bound_mm']),
        ('command_warning_400',lambda r:r['command_warning_400'],lambda r:-r['command_hz_400'])]
    for tag in all_seeds:
        seeds=all_seeds[tag];draws=rng.multinomial(len(seeds),np.ones(len(seeds))/len(seeds),size=a.draws)
        risk=[r for r in rows if r['RF']==tag and r['landmark_status']=='at_risk']
        for name,pred,score in candidates:
            result=score_set(risk,seeds,pred,score,name,draws);result['RF']=tag;metrics.append(result)
            if pred is not None:
                for r in risk:
                    if bool(pred(r))!=r['late_contact']:counterexamples.append(dict(metric=name,error='false_positive' if pred(r) else 'false_negative',**r))
        eligible=[r for r in risk if r['remaining_ms']>=100]
        for name in ['held_heading','held_turn']:
            result=score_set(eligible,seeds,lambda r:r[name+'_warning_100ms'],lambda r:-r[name+'_margin_100ms_mm'],name,draws,'late_contact_100ms')
            result.update(RF=tag,short_followup_ineligible=len(risk)-len(eligible));fixed.append(result)
    export(a.out/'counterexamples.csv',counterexamples)
    paired=[]
    for tag in all_seeds:
        for kind in ['fault_minus_healthy','P_minus_R']:
            for fault in ['healthy','F2_25','F2_50']:
                for law in (['proportional','relay'] if kind=='fault_minus_healthy' else ['proportional']):
                    selected=[p for p in pairs if p['RF']==tag and p['kind']==kind and p['fault']==fault and p['law']==law]
                    if not selected:continue
                    valid=[p for p in selected if p['both_eligible']];q=dict(RF=tag,kind=kind,fault=fault,law=law,total_pairs=len(selected),eligible_pairs=len(valid),
                        discordant_task_pairs=sum(p['row_contact']!=p['reference_contact'] for p in selected))
                    byseed=defaultdict(list)
                    for p in valid:byseed[p['seed']].append(p)
                    q['eligible_seeds']=len(byseed)
                    if byseed:
                        bs=rng.integers(len(byseed),size=(a.draws,len(byseed)))
                        for feature in ['clearance_B_mm','remaining_ms','abs_heading_B_deg','margin_radial_mm']:
                            v=np.array([np.mean([p[feature+'_difference'] for p in pp]) for pp in byseed.values()])
                            q[feature+'_mean_difference']=float(v.mean());q[feature+'_CI95']=interval(v[bs].mean(axis=1))
                    paired.append(q)
    export(a.out/'paired-summaries.csv',paired)
    all_unchanged=all(sha(ROOT/name)==v['sha256'] for name,v in baseline['files'].items())
    assert all_unchanged
    result=dict(completed=True,classification='Exploratory retrospective all-record landmark analysis; not preregistered or confirmatory',
        baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        records=len(rows),clusters={k:len(v) for k,v in all_seeds.items()},landmark_accounting=dict(Counter(r['landmark_status'] for r in rows)),
        failure_phases=dict(Counter(r['contact_phase'] for r in rows if not r['success_through_H'])),
        predictor_metrics=metrics,fixed_100ms_metrics=fixed,paired_summaries=paired,
        constants=dict(radius_m=R,pursuer_m_s=VP,walk_m_s=VW,burst_m_s=VB,frame_s=DT,cmin_m_s=CMIN,cmax_m_s=CMAX),
        threshold_fitting=False,neural_simulation=False,post_contact_states_not_predictors=True,
        bootstrap=dict(draws=a.draws,unit='whole seed within RF',seed=SEED,interval='descriptive percentile, conditional on class presence'),
        immutable_baseline_files_verified=len(baseline['files']),unchanged_paper_and_frozen_data=all_unchanged,
        source_sha256=sha(__file__),plan_sha256=sha(ROOT/'docs/V10_1_BURST_PROTOCOL.md'),raw_input_sha256=hashes,
        runtime=dict(python=platform.python_version(),numpy=np.__version__),seconds=time.perf_counter()-started,utc=datetime.now(timezone.utc).isoformat())
    (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['predictor_metrics','fixed_100ms_metrics','paired_summaries','raw_input_sha256']},indent=2))
    for q in metrics:print(q['RF'],q['metric'],{k:q.get(k) for k in ['contacts','n','AUROC','tp','fn','fp','tn']})


if __name__=='__main__':main()
