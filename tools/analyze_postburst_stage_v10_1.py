"""Recheck the observed post-burst regime in all frozen V10.1 core records.

This is retrospective descriptive record/plant replay, not a neural rerun or a
causal intervention. Existing results, registrations and calibrations are read
only. Output directories must be new. No warning thresholds are fitted here.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'),str(ROOT/'sim_vision')]
from analyze_burst_end import reconstruct
import task_v9

SCIENTIFIC_BASE = '75313d7740491e7f7830e2fc554c21e1aaefe655'
CONFIGS = {
    'RF-0': ('audit/acceptance-v9/core-v2/summary.json','runs/task-v9-frozen/registration-core.json','runs/task-v9-frozen/calibration.json'),
    'RF-A': ('audit/v10/transfer-01/map-A/analysis/summary.json','runs/task-v10-transfer/map-A/registration.json','runs/task-v10-transfer/map-A/calibration.json'),
    'RF-B': ('audit/v10/transfer-01/map-B/analysis/summary.json','runs/task-v10-transfer/map-B/registration.json','runs/task-v10-transfer/map-B/calibration.json'),
}


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def export(p, rows):
    if not rows:
        return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with p.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)


def status(trigger, B, H, contact):
    # Prior contact takes priority over an incomplete burst: such a state cannot
    # enter a prospective post-burst risk set.
    if contact is not None and (B is None or contact <= B):
        return 'prior_contact'
    if trigger is None:
        return 'no_trigger'
    if B > H:
        return 'ongoing_at_H'
    if B == H:
        return 'zero_followup'
    return 'at_risk'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    rows=[];decisions=[];calibration_hashes={};registration_hashes={};raw_hashes={}
    records={};helper_rows=[];summary_hashes={}
    for rf,(summary_name,registration_name,calibration_name) in CONFIGS.items():
        summary=read(ROOT/summary_name);registration=read(ROOT/registration_name);cal=read(ROOT/calibration_name)
        summary_hashes[summary_name]=sha(ROOT/summary_name)
        registration_hashes[registration_name]=sha(ROOT/registration_name)
        calibration_hashes[calibration_name]=sha(ROOT/calibration_name)
        assert registration['calibration_sha256']==calibration_hashes[calibration_name]
        assert cal['gate_silent'] and cal['trigger_hz']>0
        # Helper fixtures expose the code boundary. These are not neural trials:
        # steering has no post-burst-time suppression; nonzero late features can
        # still request a turn. Disabled gating exposes the affine intercept.
        for law in ['proportional','relay']:
            fixtures=[('zero_gated',np.zeros(8),cal),
                      ('zero_ungated',np.zeros(8),dict(cal,gate_silent=False)),
                      ('active_gated',np.full(8,cal['trigger_hz']+10),cal)]
            for name,features,c in fixtures:
                omega=task_v9.steering(features,c,law,900.)
                if name=='zero_gated':assert omega==0
                helper_rows.append(dict(RF=rf,law=law,fixture=name,decision_ms=900,
                    feature_mean_hz=float(features.mean()),gate_silent=c['gate_silent'],
                    trigger_hz=c['trigger_hz'],turn_deg_s=float(omega),
                    classification='synthetic function fixture, not a neural experiment'))
        for name,expected_hash in summary['raw_input_sha256'].items():
            path=ROOT/name;actual_hash=sha(path);assert actual_hash==expected_hash
            raw_hashes[name]=actual_hash;r=read(path);states,_=reconstruct(r)
            assert r['calibration_sha256']==calibration_hashes[calibration_name]
            assert len(r['command_flyids'])==8 and r['command_flyids']==cal['command_flyids']
            H=r['horizon_ms'];trigger=r['trigger_ms'];contact=r['collision_ms']
            assert H==1000 and r['burst_delay_ms']==250 and r['burst_duration_ms']==450
            B=None if trigger is None else trigger+r['burst_delay_ms']+r['burst_duration_ms']
            on=None if trigger is None else trigger+r['burst_delay_ms']
            landmark=status(trigger,B,H,contact)
            key=(rf,r['seed'],r['phi_deg'],r['mode'],r['fault'])
            assert key not in records;records[key]=r
            history=[];cross=None
            for q in r['log']:
                rates=q['cmd_rates'];assert len(rates)==8 and all(x>=0 for x in rates)
                # The recorded raw rates are integer spike counts / 0.020 s.
                assert all(float(x/50).is_integer() for x in rates)
                history.append(rates);smooth=np.mean(history[-5:],axis=0)
                assert np.array_equal(smooth,np.array(q['smooth_rates']))
                assert float(smooth.mean())==q['cmd_hz']
                if cross is None and q['t_end_ms']>100 and q['cmd_hz']>=cal['trigger_hz']:
                    cross=q['t_end_ms']
                assert cross==q['trigger_ms']
                assert abs(task_v9.steering(smooth,cal,r['mode'],q['t_end_ms'])-q['next_omega'])<1e-8
            assert cross==trigger
            row=dict(RF=rf,seed=r['seed'],bearing_deg=r['phi_deg'],law=r['mode'],fault=r['fault'],
                source=name,source_sha256=actual_hash,trigger_ms=trigger,burst_start_ms=on,
                burst_end_ms=B,horizon_ms=H,first_contact_ms=contact,
                landmark_status=landmark,eligible=landmark=='at_risk',
                remaining_ms=None if B is None else H-B,contact_after_B=landmark=='at_risk' and contact is not None,
                gate_silent=cal['gate_silent'],trigger_threshold_hz=cal['trigger_hz'])
            if landmark=='at_risk':
                stop=min(H,contact if contact is not None else H)
                # The boundary decision at B is included: it controls the first
                # walking interval. A decision at first contact or H is excluded
                # because it cannot affect any observed pre-contact follow-up.
                qq=[q for q in r['log'] if B<=q['t_end_ms']<stop]
                assert qq
                complete=[q for q in r['log'] if B<q['t_end_ms']<=stop]
                n_B=next(q['n_total'] for q in r['log'] if q['t_end_ms']==B)
                global_spikes=(complete[-1]['n_total']-n_B) if complete else None
                start_heading=float(np.degrees(states[B]['heading']))
                center=float(np.linalg.norm(states[B]['target']-states[B]['fly']))
                all_zero=all(all(x==0 for x in q['smooth_rates']) for q in qq)
                raw_zero=all(all(x==0 for x in q['cmd_rates']) for q in qq)
                zero_turn=all(q['next_omega']==0 for q in qq)
                assert all_zero and raw_zero and zero_turn
                assert all(abs(q['heading_deg']-start_heading)<1e-8 for q in qq+complete)
                row.update(decisions=len(qq),all_eight_features_zero=all_zero,all_raw_rates_zero=raw_zero,
                    all_requested_turns_zero=zero_turn,center_distance_B_mm=center*1000,
                    clearance_B_mm=(center-.05)*1000,heading_B_deg=start_heading,
                    fully_observed_post_B_neural_frames=len(complete),post_B_global_spikes=global_spikes,
                    full_window_all_network_spiking_observed=global_spikes is not None and global_spikes>0,
                    latest_effective_decision_ms=qq[-1]['t_end_ms'])
                for q in qq:
                    decisions.append(dict(RF=rf,seed=r['seed'],bearing_deg=r['phi_deg'],law=r['mode'],fault=r['fault'],
                        source=name,decision_ms=q['t_end_ms'],burst_end_ms=B,followup_end_ms=stop,
                        cmd_hz=q['cmd_hz'],next_omega_deg_s=q['next_omega'],input_gain=q['u'],
                        **{f'feature_{j}_hz':v for j,v in enumerate(q['smooth_rates'])}))
            rows.append(row)
    assert len(rows)==576
    pair_rows=[];delay_rows=[]
    for key,r in records.items():
        rf,seed,bearing,law,fault=key
        if law=='proportional':
            other=records[(rf,seed,bearing,'relay',fault)]
            fields=['seed','phi_deg','fault','mask_sha256','uniform_sha256','input_map_sha256','calibration_sha256',
                    'trigger_ms','burst_delay_ms','burst_duration_ms']
            assert all(r[f]==other[f] for f in fields)
            prefix_frames=0
            for p,q in zip(r['log'],other['log']):
                if p['t_end_ms']>r['trigger_ms']:break
                for f in ['cmd_rates','smooth_rates','cmd_hz','fly','target','heading_deg','phi_now','u','half_angle','n_total']:
                    assert p[f]==q[f]
                # At the trigger boundary both neural inputs/past motion still
                # match, but the newly requested next-frame turns can differ.
                if p['t_end_ms']<r['trigger_ms']:
                    assert p['next_omega']==q['next_omega']==0
                prefix_frames+=1
            pair_rows.append(dict(RF=rf,seed=seed,bearing_deg=bearing,fault=fault,
                trigger_ms=r['trigger_ms'],burst_start_ms=r['trigger_ms']+250,burst_end_ms=r['trigger_ms']+700,
                shared_mask_uniform_map_calibration=True,pretrigger_prefix_frames=prefix_frames,
                P_first_contact_ms=r['collision_ms'],R_first_contact_ms=other['collision_ms'],
                task_discordant=r['escaped']!=other['escaped']))
            if fault!='healthy':
                healthy=records[(rf,seed,bearing,law,'healthy')]
                assert r['uniform_sha256']==healthy['uniform_sha256']
                delay_rows.append(dict(RF=rf,seed=seed,bearing_deg=bearing,fault=fault,
                    healthy_trigger_ms=healthy['trigger_ms'],fault_trigger_ms=r['trigger_ms'],
                    delay_ms=r['trigger_ms']-healthy['trigger_ms'],P_R_duplicate_counted_once=True))
    assert len(pair_rows)==288 and len(delay_rows)==192
    groups=[]
    for rf in CONFIGS:
        for law in ['proportional','relay']:
            for fault in ['healthy','F2_25','F2_50']:
                group=[q for q in rows if q['RF']==rf and q['law']==law and q['fault']==fault]
                eligible=[q for q in group if q['eligible']]
                counts=Counter(q['landmark_status'] for q in group)
                groups.append(dict(RF=rf,law=law,fault=fault,records=len(group),
                    **{s:counts[s] for s in ['at_risk','prior_contact','ongoing_at_H','zero_followup','no_trigger']},
                    post_B_decisions=sum(q['decisions'] for q in eligible),
                    records_with_post_B_global_spikes=sum(q['full_window_all_network_spiking_observed'] for q in eligible),
                    later_contacts=sum(q['contact_after_B'] for q in eligible),
                    all_eight_features_zero=all(q['all_eight_features_zero'] for q in eligible)))
    delays=[]
    for rf in CONFIGS:
        for fault in ['F2_25','F2_50']:
            qq=[q for q in delay_rows if q['RF']==rf and q['fault']==fault];values=[q['delay_ms'] for q in qq]
            delays.append(dict(RF=rf,fault=fault,bearing_pairs=len(qq),seed_clusters=len({q['seed'] for q in qq}),
                mean_ms=statistics.mean(values),sd_ms=statistics.stdev(values),median_ms=statistics.median(values),
                minimum_ms=min(values),maximum_ms=max(values),earlier=sum(x<0 for x in values),
                tied=sum(x==0 for x in values),later=sum(x>0 for x in values)))
    export(a.out/'all-records.csv',rows);export(a.out/'postburst-decisions.csv',decisions)
    export(a.out/'groups.csv',groups);export(a.out/'all-P-R-pairs.csv',pair_rows)
    export(a.out/'healthy-fault-delays.csv',delay_rows);export(a.out/'delay-summary.csv',delays)
    export(a.out/'steering-helper-fixtures.csv',helper_rows)
    for name,h in {**raw_hashes,**calibration_hashes,**registration_hashes}.items():
        assert sha(ROOT/name)==h
    eligible=[q for q in rows if q['eligible']]
    result=dict(classification='Retrospective descriptive recheck, no new neural samples or causal intervention',
        scientific_base=SCIENTIFIC_BASE,execution_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        records=len(rows),landmark_status=dict(Counter(q['landmark_status'] for q in rows)),
        eligible_records=len(eligible),effective_postburst_decisions=len(decisions),
        all_eight_features_zero=all(q['all_eight_features_zero'] for q in eligible),
        all_raw_command_rates_zero=all(q['all_raw_rates_zero'] for q in eligible),
        all_postburst_turn_requests_zero=all(q['all_requested_turns_zero'] for q in eligible),
        records_with_post_B_global_spikes=sum(q['full_window_all_network_spiking_observed'] for q in eligible),
        postburst_contacts=sum(q['contact_after_B'] for q in eligible),
        P_R_pairs=len(pair_rows),P_R_shared_schedule_mask_inputs_and_prefix=len(pair_rows),
        P_R_discordant_outcomes=sum(q['task_discordant'] for q in pair_rows),paired_trigger_delays=delays,
        observed_regime_not_structural_code_invariant=True,neural_simulation=False,threshold_fitting=False,
        new_confirmatory_inference=False,raw_input_sha256=raw_hashes,
        calibration_sha256=calibration_hashes,registration_sha256=registration_hashes,summary_sha256=summary_hashes,
        source_sha256=sha(__file__),reconstruct_sha256=sha(ROOT/'tools/analyze_burst_end.py'),
        plant_sha256=sha(ROOT/'sim_vision/task_v9.py'),
        runtime=dict(python=platform.python_version(),numpy=np.__version__,seconds=time.perf_counter()-start),
        utc=datetime.now(timezone.utc).isoformat(),
        scope_notes=[
            'Risk set requires burst end B < H and no prior or concurrent contact.',
            'Decision at B is included; decisions at first contact or H are excluded.',
            'Post-B global spikes use only complete pre-contact frames, with B-frame counts subtracted.',
            'Features are eight nonnegative five-frame command-rate means, not all-network activity.',
            'Zero features plus positive-threshold silent gating imply zero requested turn in these records.',
            'No estimator score or classifier performance is inferred from deterministic geometry replay.',
            'Finite follow-up, unequal healthy reserve, recalibration and cohorts remain interpretation limits.'])
    (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('sha256') and k not in ['paired_trigger_delays']},indent=2))


if __name__=='__main__':
    main()
