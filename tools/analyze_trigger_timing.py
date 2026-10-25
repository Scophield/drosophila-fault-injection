"""All-record retrospective trigger/turning audit; no neural simulation or fitting."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'sim_vision')]
import task_v9
from analyze_burst_end import reconstruct, sha, export


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def distribution(values):
    v=np.array(values,float)
    if not len(v):return dict(n=0)
    return dict(n=len(v),mean=float(v.mean()),sd=float(v.std(ddof=1)) if len(v)>1 else None,
        median=float(np.median(v)),q25=float(np.quantile(v,.25)),q75=float(np.quantile(v,.75)),
        minimum=float(v.min()),maximum=float(v.max()),earlier=int(np.sum(v<0)),
        tied=int(np.sum(v==0)),later=int(np.sum(v>0)))


def midrank(values):
    v=np.array(values,float);order=np.argsort(v,kind='stable');r=np.empty(len(v),float)
    for value in np.unique(v):
        positions=np.flatnonzero(v[order]==value);r[order[positions]]=positions.mean()+1
    return r


def spearman(x,y):
    if len(x)<3:return None
    a,b=midrank(x),midrank(y)
    if not np.ptp(a) or not np.ptp(b):return None
    return float(np.corrcoef(a,b)[0,1])


def onset_state(r):
    """State at exact burst onset, including its within-frame walk segment."""
    fly=np.zeros(2);target=.25*np.array([np.cos(np.radians(r['phi_deg'])),np.sin(np.radians(r['phi_deg']))])
    heading=0.;omega=0.;trigger=None;turn=commanded=active_ms=0.;on=r['trigger_ms']+250
    found=None
    for q in r['log']:
        a,b=q['t_ms'],q['t_end_ms']
        if a<on<=b:
            f,t,h,segments=task_v9.motion(fly.copy(),target.copy(),heading,omega,a,on,trigger)
            dt=on-a
            turn+=abs(np.degrees(h-heading));commanded+=abs(omega)*dt/1000
            active_ms+=dt if abs(omega)>1e-10 else 0
            found=dict(heading_on_deg=float(np.degrees(h)),abs_heading_on_deg=abs(float(np.degrees(h))),
                clearance_on_mm=1000*(float(np.linalg.norm(t-f))-.05),
                actual_turn_path_before_on_deg=float(turn),commanded_turn_before_on_deg=float(commanded),
                nonzero_turn_duration_before_on_ms=float(active_ms))
            break
        f,t,h,segments=task_v9.motion(fly,target,heading,omega,a,b,trigger)
        turn+=abs(np.degrees(h-heading));commanded+=abs(omega)*(b-a)/1000
        active_ms+=(b-a) if abs(omega)>1e-10 else 0
        assert np.allclose(f,q['fly'],atol=1e-10,rtol=0) and np.allclose(t,q['target'],atol=1e-10,rtol=0)
        assert abs(np.degrees(h)-q['heading_deg'])<1e-8
        fly,target,heading=f,t,h;omega=q['next_omega'];trigger=q['trigger_ms']
    assert found is not None
    return found


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    baseline=read(ROOT/'PUBLIC_SCOPE.json')
    protected={p:sha(ROOT/p) for p in baseline['files']}
    preexisting_changes=[p for p,h in protected.items() if h!=baseline['files'][p]['sha256']]
    configs={tag:(summary,reg,cal) for tag,summary,reg,cal in [
        ('RF-0','audit/acceptance-v9/core-v2/summary.json','runs/task-v9-frozen/registration-core.json','runs/task-v9-frozen/calibration.json'),
        ('RF-A','audit/v10/transfer-01/map-A/analysis/summary.json','runs/task-v10-transfer/map-A/registration.json','runs/task-v10-transfer/map-A/calibration.json'),
        ('RF-B','audit/v10/transfer-01/map-B/analysis/summary.json','runs/task-v10-transfer/map-B/registration.json','runs/task-v10-transfer/map-B/calibration.json')]}
    prior_rows=list(csv.DictReader((ROOT/'output/burst-end-20261025-01/all-records.csv').open(encoding='utf-8',newline='')))
    prior={q['key']:q for q in prior_rows};records={};rows=[];gate_rows=[];raw_hashes={};calibrations={};fixtures=[]
    assert sha(task_v9.__file__)==baseline['files']['sim_vision/task_v9.py']['sha256']
    for tag,(summary_path,reg_path,cal_path) in configs.items():
        summary,reg,cal=read(ROOT/summary_path),read(ROOT/reg_path),read(ROOT/cal_path)
        assert sha(ROOT/cal_path)==reg['calibration_sha256'];calibrations[tag]=cal
        assert cal['gate_silent'] and cal['trigger_hz']>0
        for law in ['proportional','relay']:
            off=dict(cal,gate_silent=False)
            for name,features,c in [('zero_gated',np.zeros(8),cal),
                ('zero_ungated',np.zeros(8),off),('active_gated',np.full(8,cal['trigger_hz']+10),cal)]:
                omega=task_v9.steering(features,c,law,900.)
                assert (abs(omega)<1e-12)==(name=='zero_gated')
                fixtures.append(dict(RF=tag,law=law,fixture=name,features_mean=float(features.mean()),
                    trigger_hz=c['trigger_hz'],gate_silent=c['gate_silent'],turn_deg_s=omega,
                    scope='synthetic helper-only check, not a neural experiment'))
        for name,h in summary['raw_input_sha256'].items():
            p=ROOT/name;assert sha(p)==h;raw_hashes[name]=h;r=read(p);states,_=reconstruct(r)
            key=f"{tag}/{r['seed']}/{r['phi_deg']:g}/{r['mode']}/{r['fault']}"
            row0=prior[key];assert h==row0['source_sha256']
            history=[];cross=None;prezero=True
            for q in r['log']:
                history.append(q['cmd_rates']);smooth=np.mean(history[-5:],axis=0)
                assert np.allclose(smooth,q['smooth_rates'],atol=1e-10,rtol=0)
                assert abs(float(smooth.mean())-q['cmd_hz'])<1e-10
                if cross is None and q['t_end_ms']>100 and q['cmd_hz']>=cal['trigger_hz']:cross=q['t_end_ms']
                assert q['trigger_ms']==cross
                omega=task_v9.steering(smooth,cal,r['mode'],q['t_end_ms'])
                assert abs(omega-q['next_omega'])<1e-8
                if q['t_end_ms']<(cross or 1001):prezero &= abs(omega)<1e-12
            assert cross==r['trigger_ms'] and cross is not None and prezero
            trigq=next(q for q in r['log'] if q['t_end_ms']==cross)
            assert abs(trigq['heading_deg'])<1e-10
            on,B=cross+250,cross+700;contact=r['collision_ms']
            assert contact is None or cross<contact
            segments=[s for q in r['log'] for s in q['segments'] if s['burst']]
            assert min(s['start_ms'] for s in segments)==on
            assert abs(sum(s['end_ms']-s['start_ms'] for s in segments)-min(450,1000-on))<1e-9
            state=onset_state(r)
            if B<=1000:assert abs(np.degrees(states[B]['heading'])-state['heading_on_deg'])<1e-8
            row=dict(key=key,RF=tag,seed=r['seed'],bearing_deg=r['phi_deg'],law=r['mode'],fault=r['fault'],
                trigger_ms=cross,trigger_threshold_hz=cal['trigger_hz'],trigger_mean_hz=trigq['cmd_hz'],
                heading_at_trigger_deg=trigq['heading_deg'],pretrigger_steering_zero=bool(prezero),
                burst_on_ms=on,scheduled_B_ms=B,scheduled_H_minus_B_ms=1000-B,
                observed_burst_ms=sum(s['end_ms']-s['start_ms'] for s in segments),
                burst_status=row0['burst_status'],landmark_status=row0['landmark_status'],
                onset_before_contact=contact is None or on<contact,postcontact_onset_state=contact is not None and contact<=on,
                first_contact_ms=contact,contact_phase=row0['contact_phase'],success_through_H=r['escaped'],
                mask_sha256=r['mask_sha256'],uniform_sha256=r['uniform_sha256'],source=name,source_sha256=h,**state)
            for feature in ['clearance_B_mm','margin_radial_mm','remaining_ms','bearing_to_pursuer_B_deg']:
                row[feature]=float(row0[feature]) if row0.get(feature) else None
            if B<=1000:
                s=states[B];rel=s['target']-s['fly'];d=float(np.linalg.norm(rel))
                beta=float(np.arccos(np.clip((rel/d)@np.array([np.cos(s['heading']),np.sin(s['heading'])]),-1,1)))
                independent=dict(clearance_B_mm=1000*(d-.05),remaining_ms=1000-B,
                    margin_radial_mm=1000*((d-.05)-(.30+.05*np.cos(beta))*(1000-B)/1000),
                    bearing_to_pursuer_B_deg=float(np.degrees(beta)))
                assert all(abs(row[f]-value)<1e-7 for f,value in independent.items())
            if row['landmark_status']=='at_risk':
                end=min(1000,contact or 1000)
                qq=[q for q in r['log'] if B<=q['t_end_ms']<end]
                assert all(q['cmd_hz']==0 and all(x==0 for x in q['smooth_rates']) and q['next_omega']==0 for q in qq)
                complete=[q for q in r['log'] if B<q['t_end_ms']<=end]
                n_at_B=next(q['n_total'] for q in r['log'] if q['t_end_ms']==B)
                global_spikes=complete[-1]['n_total']-n_at_B if complete else None
                gate_rows.append(dict(key=key,RF=tag,seed=r['seed'],law=r['mode'],fault=r['fault'],
                    decisions=len(qq),max_command_hz=max(q['cmd_hz'] for q in qq),
                    threshold_hz=cal['trigger_hz'],positive_input_gain_decisions=sum(q['u']>0 for q in qq),
                    zero_input_gain_decisions=sum(q['u']==0 for q in qq),all_eight_features_zero=True,
                    complete_neural_post_B_frames=len(complete),post_B_global_spikes=global_spikes,
                    latest_effective_decision_ms=max(q['t_end_ms'] for q in qq)))
            records[key]=r;rows.append(row)
    assert len(rows)==576
    lookup={q['key']:q for q in rows};pairs=[];lawpairs=[]
    for row in rows:
        if row['fault']!='healthy':
            ref=lookup[f"{row['RF']}/{row['seed']}/{row['bearing_deg']:g}/{row['law']}/healthy"]
            both_end=row['landmark_status']==ref['landmark_status']=='at_risk'
            both_on=row['onset_before_contact'] and ref['onset_before_contact']
            delta=row['trigger_ms']-ref['trigger_ms']
            q=dict(RF=row['RF'],seed=row['seed'],bearing_deg=row['bearing_deg'],law=row['law'],fault=row['fault'],
                key=row['key'],reference_key=ref['key'],healthy_trigger_ms=ref['trigger_ms'],fault_trigger_ms=row['trigger_ms'],
                trigger_delta_ms=delta,input_uniforms_matched=row['uniform_sha256']==ref['uniform_sha256'],
                onset_both_precontact=both_on,B_both_eligible=both_end,row_status=row['landmark_status'],
                reference_status=ref['landmark_status'],contact_phase=row['contact_phase'],
                first_contact_ms=row['first_contact_ms'],task_contact=not row['success_through_H'])
            for f in ['abs_heading_on_deg','actual_turn_path_before_on_deg','clearance_on_mm']:
                q[f+'_delta']=row[f]-ref[f] if both_on else None
            for f in ['clearance_B_mm','margin_radial_mm','remaining_ms']:
                q[f+'_delta']=row[f]-ref[f] if both_end else None
            assert q['input_uniforms_matched'];pairs.append(q)
        if row['law']=='proportional':
            refkey=row['key'].replace('/proportional/','/relay/');ref=lookup[refkey]
            r,s=records[row['key']],records[refkey]
            assert row['trigger_ms']==ref['trigger_ms'] and row['burst_on_ms']==ref['burst_on_ms'] and row['scheduled_B_ms']==ref['scheduled_B_ms']
            assert row['mask_sha256']==ref['mask_sha256'] and row['uniform_sha256']==ref['uniform_sha256']
            prefix=[(x,y) for x,y in zip(r['log'],s['log']) if x['t_end_ms']<=row['trigger_ms']]
            for x,y in prefix:
                for field in ['cmd_rates','smooth_rates','cmd_hz','fly','target','heading_deg','phi_now','u','half_angle','n_total']:
                    assert x[field]==y[field],(row['key'],field)
            onset_valid=row['onset_before_contact'] and ref['onset_before_contact']
            end_valid=row['landmark_status']==ref['landmark_status']=='at_risk'
            lawpairs.append(dict(RF=row['RF'],seed=row['seed'],bearing_deg=row['bearing_deg'],fault=row['fault'],
                P_key=row['key'],R_key=refkey,trigger_ms=row['trigger_ms'],onset_ms=row['burst_on_ms'],scheduled_B_ms=row['scheduled_B_ms'],
                prefix_frames_equal=len(prefix),schedule_matched=True,mask_matched=True,uniform_matched=True,
                P_contact=not row['success_through_H'],R_contact=not ref['success_through_H'],
                task_discordant=row['success_through_H']!=ref['success_through_H'],onset_both_precontact=onset_valid,
                abs_heading_on_P_minus_R=row['abs_heading_on_deg']-ref['abs_heading_on_deg'] if onset_valid else None,
                clearance_on_P_minus_R=row['clearance_on_mm']-ref['clearance_on_mm'] if onset_valid else None,
                B_both_eligible=end_valid,clearance_B_P_minus_R=row['clearance_B_mm']-ref['clearance_B_mm'] if end_valid else None))
    assert len(pairs)==384 and len(lawpairs)==288
    export(a.out/'all-records.csv',rows);export(a.out/'all-healthy-fault-pairs.csv',pairs)
    export(a.out/'all-P-R-pairs.csv',lawpairs);export(a.out/'post-B-gate-records.csv',gate_rows)
    export(a.out/'steering-helper-fixtures.csv',fixtures)
    summaries=[];freq=[];seed_rows=[];bearing=[];associations=[];stages=[];gate_groups=[];dosepairs=[]
    for tag in configs:
        for fault in ['F2_25','F2_50']:
            # P/R have identical trigger delays, so do not double the distribution n.
            selected=[p for p in pairs if p['RF']==tag and p['fault']==fault and p['law']=='proportional']
            byseed=defaultdict(list)
            for q in selected:byseed[q['seed']].append(q['trigger_delta_ms'])
            for seed,values in byseed.items():
                assert len(values)==2
                seed_rows.append(dict(RF=tag,fault=fault,seed=seed,delta_mean_ms=float(np.mean(values)),
                    min_delta_ms=min(values),max_delta_ms=max(values)))
            summaries.append(dict(RF=tag,fault=fault,independent_seed_clusters=len(byseed),
                distribution_unit='paired bearing context; P/R timing duplicates shown once',
                **distribution([q['trigger_delta_ms'] for q in selected]),
                seed_mean_sd_ms=float(np.std([np.mean(v) for v in byseed.values()],ddof=1))))
            for value,count in sorted(Counter(q['trigger_delta_ms'] for q in selected).items()):
                freq.append(dict(RF=tag,fault=fault,delta_ms=value,n_bearing_pairs=count))
            for phi in [-30.,30.]:
                pp=[q for q in selected if q['bearing_deg']==phi]
                bearing.append(dict(RF=tag,fault=fault,bearing_deg=phi,**distribution([q['trigger_delta_ms'] for q in pp])))
            for law in ['proportional','relay']:
                pp=[p for p in pairs if p['RF']==tag and p['fault']==fault and p['law']==law]
                for feature,valid in [('abs_heading_on_deg_delta','onset_both_precontact'),
                    ('clearance_on_mm_delta','onset_both_precontact'),('clearance_B_mm_delta','B_both_eligible'),
                    ('margin_radial_mm_delta','B_both_eligible')]:
                    good=[p for p in pp if p[valid]]
                    associations.append(dict(RF=tag,fault=fault,law=law,feature=feature,eligible_pairs=len(good),
                        excluded_pairs=len(pp)-len(good),spearman_with_trigger_delta=spearman([p['trigger_delta_ms'] for p in good],[p[feature] for p in good]),
                        scope='descriptive conditional association only; no p-value or mediation model'))
        for q in [p for p in pairs if p['RF']==tag and p['law']=='proportional' and p['fault']=='F2_50']:
            ref=next(p for p in pairs if p['RF']==tag and p['law']=='proportional' and p['fault']=='F2_25' and p['seed']==q['seed'] and p['bearing_deg']==q['bearing_deg'])
            dosepairs.append(dict(RF=tag,seed=q['seed'],bearing_deg=q['bearing_deg'],
                delta50_minus_delta25_ms=q['trigger_delta_ms']-ref['trigger_delta_ms']))
        for law in ['proportional','relay']:
            for fault in ['healthy','F2_25','F2_50']:
                rr=[r for r in rows if r['RF']==tag and r['law']==law and r['fault']==fault]
                on=[r for r in rr if r['onset_before_contact']];end=[r for r in rr if r['landmark_status']=='at_risk']
                stages.append(dict(RF=tag,law=law,fault=fault,n=len(rr),trigger_mean_ms=float(np.mean([r['trigger_ms'] for r in rr])),
                    trigger_sd_ms=float(np.std([r['trigger_ms'] for r in rr],ddof=1)),
                    valid_onset=len(on),abs_heading_on_median=float(np.median([r['abs_heading_on_deg'] for r in on])),
                    actual_turn_path_median=float(np.median([r['actual_turn_path_before_on_deg'] for r in on])),
                    nonzero_turn_duration_median_ms=float(np.median([r['nonzero_turn_duration_before_on_ms'] for r in on])),
                    commanded_turn_before_on_median_deg=float(np.median([r['commanded_turn_before_on_deg'] for r in on])),
                    clearance_on_median_mm=float(np.median([r['clearance_on_mm'] for r in on])),
                    eligible_B=len(end),clearance_B_median_mm=float(np.median([r['clearance_B_mm'] for r in end])),
                    late_contacts=sum(r['contact_phase']=='post_burst' for r in rr),
                    prior_contacts=sum(r['contact_phase'] in ['pre_burst','during_or_at_burst_end'] for r in rr),
                    ongoing_burst_at_H=sum(r['burst_status']=='ongoing_at_H' for r in rr),
                    zero_followup=sum(r['landmark_status']=='zero_followup' for r in rr)))
                gg=[r for r in gate_rows if r['RF']==tag and r['law']==law and r['fault']==fault]
                gate_groups.append(dict(RF=tag,law=law,fault=fault,eligible_records=len(gg),decisions=sum(r['decisions'] for r in gg),
                    all_eight_command_features_zero=all(r['all_eight_features_zero'] for r in gg),
                    positive_input_gain_decisions=sum(r['positive_input_gain_decisions'] for r in gg)))
    export(a.out/'paired-delay-summary.csv',summaries);export(a.out/'paired-delay-frequencies.csv',freq)
    export(a.out/'seed-average-delays.csv',seed_rows);export(a.out/'paired-delays-by-bearing.csv',bearing)
    export(a.out/'conditional-stage-associations.csv',associations);export(a.out/'stage-summary.csv',stages)
    export(a.out/'post-B-gate-groups.csv',gate_groups);export(a.out/'dose-order-pairs.csv',dosepairs)
    export(a.out/'earlier-trigger-counterexamples.csv',[p for p in pairs if p['trigger_delta_ms']<0])
    export(a.out/'all-contact-pairs.csv',[p for p in pairs if p['task_contact']])
    assert all(sha(ROOT/p)==h for p,h in protected.items())
    result=dict(classification='Retrospective descriptive analysis, no new confirmatory inference',
        baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        formal_pdf_unchanged_sha256=sha(ROOT/'paper/main.pdf'),protected_existing_files=len(protected),
        preexisting_manuscript_changes_preserved=preexisting_changes,records=len(rows),healthy_fault_pairs=len(pairs),P_R_pairs=len(lawpairs),
        no_trigger=sum(r['trigger_ms'] is None for r in rows),all_triggers_before_contact=True,
        all_P_R_trigger_onset_end_and_prefix_matches=True,zero_pretrigger_steering_records=len(rows),
        paired_delay_summary=summaries,burst_status=dict(Counter(r['burst_status'] for r in rows)),
        landmark_status=dict(Counter(r['landmark_status'] for r in rows)),
        post_B=dict(eligible_records=len(gate_rows),decisions=sum(r['decisions'] for r in gate_rows),
            all_eight_command_features_zero=True,positive_input_gain_decisions=sum(r['positive_input_gain_decisions'] for r in gate_rows),
            records_with_post_B_global_spikes=sum(r['post_B_global_spikes'] is not None and r['post_B_global_spikes']>0 for r in gate_rows),
            observed_not_a_post_B_code_invariant=True),
        P_R_task_discordance=sum(p['task_discordant'] for p in lawpairs),
        dose_order_counts={tag:dict(Counter(p['delta50_minus_delta25_ms'] for p in dosepairs if p['RF']==tag)) for tag in configs},
        thresholds={k:v['trigger_hz'] for k,v in calibrations.items()},neural_simulation=False,
        threshold_fitting=False,hypothesis_tests=False,new_confidence_intervals=False,
        raw_input_sha256=raw_hashes,calibration_sha256={k:sha(ROOT/v[2]) for k,v in configs.items()},
        prior_landmark_table_sha256=sha(ROOT/'output/burst-end-20261025-01/all-records.csv'),
        prior_landmarks_independently_rechecked=True,
        source_sha256=sha(__file__),plan_sha256=sha(ROOT/'docs/V10_1_TIMING_PROTOCOL.md'),
        runtime=dict(python=platform.python_version(),numpy=np.__version__,seconds=time.perf_counter()-started),
        utc=datetime.now(timezone.utc).isoformat())
    (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['raw_input_sha256','paired_delay_summary','dose_order_counts']},indent=2))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
