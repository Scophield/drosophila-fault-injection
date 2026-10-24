"""V10 per-map analysis: registered bootstrap RNG, no cross-map pooling.

Within-map Holm is descriptive; the fixed four-test family is adjusted only
after both complete map outputs are available. V9 estimands/code are unchanged.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
from datetime import datetime
import numpy as np
from task_metrics_v9 import (features,flags,prefix,stop_time,confusion,
    bootstrap_indices,mean_interval,sign_flip_p)
from task_v9 import burst_active,deletion_mask,mask_hash,VERSION

ROOT=Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path,rows):
    with path.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def interval(samples): return [float(np.quantile(samples,.025)),float(np.quantile(samples,.975))]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--registration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); started=time.perf_counter()
    reg=json.loads(args.registration.read_text()); seeds=reg['test_seeds']
    active=json.loads((args.root/'active.json').read_text())
    if active['started_unix']<datetime.fromisoformat(reg['created_utc']).timestamp():
        raise ValueError('test launch precedes registration')
    paths=sorted((args.root/'episodes').glob('*.json'))
    records=[json.loads(p.read_text()) for p in paths]
    key=lambda r:(r['seed'],r['phi_deg'],r['mode'],r['fault'])
    expected={(s,phi,m,f) for s in seeds for phi in reg['phis'] for m in reg['modes'] for f in reg['faults']}
    if len(records)!=len(expected) or {key(r) for r in records}!=expected:
        raise ValueError(f'incomplete or duplicated independent matrix: {len(records)}/{len(expected)}')
    lookup={key(r):r for r in records}; errors=[]
    manifests={sha(p):p for p in (args.root/'batches').glob('*/run_manifest.json')}
    source_maps=[]
    input_map_hash=sha(args.root/'input-map.json')
    for digest,p in manifests.items():
        m=json.loads(p.read_text()); cfg=m['parameters'];source_maps.append(m['source_sha256'])
        if cfg['role']!='test' or cfg['registration_sha256']!=sha(args.registration):
            errors.append(f'registration/role mismatch: {p}')
        if m['model_inputs']!=reg['model_inputs_sha256'] or m['annotations_sha256']!=reg['annotations_sha256']:
            errors.append(f'generating external inputs differ: {p}')
        if m['python']!=reg['runtime']['python'] or m['packages']!=reg['runtime']['packages']:
            errors.append(f'mixed or unexpected runtime: {p}')
        for name,value in {**m['source_sha256'],**cfg['entrypoint_sha256']}.items():
            if sha(p.parent/'source'/name)!=value: errors.append(f'snapshot mismatch: {p}/{name}')
    if any(m!=source_maps[0] for m in source_maps): errors.append('mixed neural generating sources')
    for name,expected_sha in reg['frozen_source_sha256'].items():
        if sha(Path(name))!=expected_sha: errors.append(f'frozen analysis/implementation changed: {name}')
    uniform_checks={}; masks={}
    if len({r['n_connection_rows'] for r in records})!=1: errors.append('mixed connection-row counts')
    n_rows=records[0]['n_connection_rows']
    for seed in seeds:
        group=[r for r in records if r['seed']==seed]
        uniform_checks[str(seed)]=len({r['uniform_sha256'] for r in group})==1
        if not uniform_checks[str(seed)]: errors.append(f'non-common input uniforms: {seed}')
        for fault in reg['faults']:
            rs=[r for r in group if r['fault']==fault]
            if len({r['mask_sha256'] for r in rs})!=1 or len({r['deleted_rows'] for r in rs})!=1:
                errors.append(f'mask differs across law/bearing: {seed}/{fault}')
            masks[f'{seed}/{fault}']=dict(sha256=rs[0]['mask_sha256'],deleted_rows=rs[0]['deleted_rows'])
        # Rebuild masks once per seed from the input table row count, never from
        # the observed task outcome or firing. Verify nesting and saved hashes.
        a=deletion_mask(n_rows,seed,.25); b=deletion_mask(n_rows,seed,.5)
        if np.any(a&~b): errors.append(f'doses not nested: {seed}')
        for fault,mask in [('F2_25',a),('F2_50',b)]:
            if mask_hash(mask)!=masks[f'{seed}/{fault}']['sha256'] or int(mask.sum())!=masks[f'{seed}/{fault}']['deleted_rows']:
                errors.append(f'cannot reconstruct mask: {seed}/{fault}')
    for r in records:
        if r['input_map_sha256']!=input_map_hash: errors.append(f'input map differs: {key(r)}')
        if r['protocol']!=VERSION or r['duration_ms']!=1000 or r['horizon_ms']!=1000 or len(r['log'])!=50:
            errors.append(f'wrong exposure/protocol: {key(r)}')
        if r['run_manifest_sha256'] not in manifests: errors.append(f'missing manifest: {key(r)}')
        if r['calibration_sha256']!=reg['calibration_sha256']: errors.append(f'changed calibration: {key(r)}')
        if r['escaped']!=(r['collision_ms'] is None): errors.append(f'outcome mismatch: {key(r)}')
        if r['collision_ms'] is not None and r['collision_ms']<=400: errors.append(f'prefix post-contact: {key(r)}')
        if r['burst_active_at_horizon']!=burst_active(1000,r['trigger_ms'],r['burst_delay_ms']):
            errors.append(f'wrong exact-horizon flag: {key(r)}')
        segs=[q for frame in r['log'] for q in frame['segments']]
        observed=sum(q['end_ms']-q['start_ms'] for q in segs if q['burst'])
        planned=0 if r['trigger_ms'] is None else max(0,min(1000,r['trigger_ms']+700)-(r['trigger_ms']+250))
        if not np.isclose(observed,planned): errors.append(f'wrong realized burst: {key(r)}')
    if errors: raise ValueError('\n'.join(errors))
    args.out.mkdir(parents=True,exist_ok=False)
    ix=bootstrap_indices(len(seeds),draws=reg['bootstrap']['draws'],seed=reg['bootstrap']['seed']); seed_index={s:i for i,s in enumerate(seeds)}
    counts=[]; cluster=[]; pair_rows=[]; metric_rows=[]; raw_rows=[]
    for m in reg['modes']:
        for fault in reg['faults']:
            for phi in reg['phis']:
                rs=[r for r in records if (r['mode'],r['fault'],r['phi_deg'])==(m,fault,phi)]
                successes=sum(r['escaped'] for r in rs)
                H=[lookup[(s,phi,m,'healthy')] for s in seeds]
                losses=sum(h['escaped'] and not r['escaped'] for h,r in zip(H,sorted(rs,key=lambda r:r['seed'])))
                gains=sum(not h['escaped'] and r['escaped'] for h,r in zip(H,sorted(rs,key=lambda r:r['seed'])))
                counts.append(dict(mode=m,fault=fault,phi_deg=phi,n=len(rs),success=successes,
                    losses=losses,gains=gains,healthy_at_risk=sum(h['escaped'] for h in H)))
    for seed in seeds:
        row=dict(seed=seed)
        for m in reg['modes']:
            for fault in ['F2_25','F2_50']:
                differences=[]
                for phi in reg['phis']:
                    h=lookup[(seed,phi,m,'healthy')];f=lookup[(seed,phi,m,fault)]
                    differences.append(int(h['escaped'])-int(f['escaped']))
                    T=min(stop_time(f),stop_time(h))
                    pair=dict(seed=seed,mode=m,fault=fault,phi_deg=phi,
                        healthy_success=h['escaped'],fault_success=f['escaped'],
                        healthy_stop_ms=stop_time(h),fault_stop_ms=stop_time(f),common_ms=T,
                        stop_ratio=prefix(f,stop_time(f))['n_total']/prefix(h,stop_time(h))['n_total'],
                        common_ratio=prefix(f,T)['n_total']/prefix(h,T)['n_total'],
                        early_ratio=prefix(f,400)['n_total']/prefix(h,400)['n_total'],
                        full_ratio=f['n_total']/h['n_total'])
                    pair_rows.append(pair)
                row[f'{m}_{fault}_net_loss']=float(np.mean(differences))
        for fault in ['F2_25','F2_50']:
            row[f'{fault}_interaction']=row[f'relay_{fault}_net_loss']-row[f'proportional_{fault}_net_loss']
        cluster.append(row)
    effects={name:mean_interval([r[name] for r in cluster],ix) for name in cluster[0] if name!='seed'}
    pvals={fault:sign_flip_p([r[f'{fault}_interaction'] for r in cluster]) for fault in ['F2_25','F2_50']}
    ordered=sorted(pvals,key=pvals.get); adjusted={ordered[0]:min(1.,2*pvals[ordered[0]])}
    adjusted[ordered[1]]=max(adjusted[ordered[0]],pvals[ordered[1]])
    ratios={}
    for m in reg['modes']:
        for fault in ['F2_25','F2_50']:
            group=[r for r in pair_rows if (r['mode'],r['fault'])==(m,fault)]
            ratios[f'{m}/{fault}']={}
            for name in ['stop_ratio','common_ratio','early_ratio','full_ratio']:
                values=np.array([[r[name] for r in group if r['seed']==s] for s in seeds])
                boot=np.median(values[ix].reshape(len(ix),-1),axis=1)
                ratios[f'{m}/{fault}'][name]=dict(median=float(np.median(values)),cluster_interval=interval(boot))
    for p,r in zip(paths,records):
        h=lookup[(r['seed'],r['phi_deg'],r['mode'],'healthy')]
        ff=features(r); decisions=flags(r,reg['thresholds'],h)
        # Numeric margins and Boolean warnings must have distinct CSV fields.
        ff['deadline_margin_m']=ff.pop('deadline')
        ff['schedule_margin_m']=ff.pop('schedule_only')
        metric_rows.append(dict(seed=r['seed'],mode=r['mode'],fault=r['fault'],phi_deg=r['phi_deg'],
            collision=not r['escaped'],**ff,**decisions))
        raw_rows.append(dict(file=p.as_posix(),sha256=sha(p),**{k:r[k] for k in ['seed','phi_deg','mode','fault','escaped',
            'collision_ms','min_distance','trigger_ms','burst_active_at_horizon','n_total','wall_seconds',
            'mask_sha256','uniform_sha256','event_sha256','run_manifest_sha256']}))
    horizons=[];activity_profiles=[]
    for m in reg['modes']:
        for fault in reg['faults']:
            rs=[r for r in records if (r['mode'],r['fault'])==(m,fault)]
            for t in [800,900,1000]:
                outcomes=[r['collision_ms'] is None or r['collision_ms']>t for r in rs]
                horizons.append(dict(mode=m,fault=fault,horizon_ms=t,n=len(rs),success=sum(outcomes)))
            if fault!='healthy':
                for t in [200,400,600,800,1000]:
                    values=[prefix(r,t)['n_total']/prefix(lookup[(r['seed'],r['phi_deg'],m,'healthy')],t)['n_total'] for r in rs]
                    activity_profiles.append(dict(mode=m,fault=fault,window_ms=t,n_pairs=len(rs),median_ratio=float(np.median(values)),
                        faulty_contact_by_window=sum(r['collision_ms'] is not None and r['collision_ms']<=t for r in rs)))
    scores={}
    for name in ['transmission','stop_count_upper','equal_duration_upper','equal_duration_two_sided','schedule_only','deadline']:
        scores[name]={}
        for subset in ['all','faulty','healthy']:
            ids=[i for i,r in enumerate(records) if subset=='all' or (r['fault']=='healthy')==(subset=='healthy')]
            rs=[records[i] for i in ids]; values=[metric_rows[i][name] for i in ids]
            result=confusion(rs,values)
            by_seed=[]
            for s in seeds:
                jj=[j for j,r in enumerate(rs) if r['seed']==s]
                cc=confusion([rs[j] for j in jj],[values[j] for j in jj])
                by_seed.append([cc[k] for k in ['tp','fp','tn','fn']])
            c=np.asarray(by_seed); sums=c[ix].sum(axis=1)
            for key,a,b in [('sensitivity',0,3),('specificity',2,1),('false_positive_rate',1,2),('false_negative_rate',3,0)]:
                den=sums[:,a]+sums[:,b]; good=den>0
                result[key+'_interval']=interval(sums[good,a]/den[good]) if good.any() else None
            clusters_any_fp=sum(cc[1]>0 for cc in c)
            result['clusters_with_false_positive']=int(clusters_any_fp)
            result['zero_cluster_false_positive_one_sided_95_upper']=float(1-.05**(1/len(seeds))) if clusters_any_fp==0 else None
            clusters_any_fn=sum(cc[3]>0 for cc in c)
            result['clusters_with_false_negative']=int(clusters_any_fn)
            result['zero_cluster_false_negative_one_sided_95_upper']=float(1-.05**(1/len(seeds))) if clusters_any_fn==0 else None
            scores[name][subset]=result
        scores[name]['strata']={}
        for m in reg['modes']:
            for phi in reg['phis']:
                ids=[i for i,r in enumerate(records) if (r['mode'],r['phi_deg'])==(m,phi)]
                scores[name]['strata'][f'{m}/{phi:g}']=confusion([records[i] for i in ids],[metric_rows[i][name] for i in ids])
    # One-sided resource excursion is not expected to detect deletion-induced
    # hypofunction; report the calibrated two-sided comparator alongside it.
    result=dict(complete=True,protocol=VERSION,records=len(records),seed_clusters=len(seeds),
        registration_sha256=sha(args.registration),raw_input_sha256={p.as_posix():sha(p) for p in paths},
        validation_input_sha256=reg['validation_input_sha256'],counts=counts,cluster_effects=effects,
        interaction_raw_p=pvals,interaction_holm_within_map_p=adjusted,interaction_holm_p=None,
        interaction_multiplicity_note='Final Holm over four map/dose tests is computed jointly after both matrices; no per-map adjusted p is confirmatory.',
        experiment_version=reg['experiment_version'],map_id=reg['map_id'],activity_ratios=ratios,
        horizon_sensitivity=horizons,activity_profiles=activity_profiles,
        warning_scores=scores,thresholds=reg['thresholds'],mask_checks=masks,
        common_uniform_checks=uniform_checks,burst_timing_verified=True,
        all_prefixes_pre_contact=True,minimum_collision_ms=min([r['collision_ms'] for r in records if r['collision_ms'] is not None],default=None),
        compute=dict(episode_wall_seconds_sum=sum(r['wall_seconds'] for r in records),
            episode_wall_seconds_median=float(np.median([r['wall_seconds'] for r in records])),
            note='overlapping episode wall times are not CPU seconds or elapsed campaign time'),
        analysis_seconds=time.perf_counter()-started,analysis_source_sha256=sha(Path(__file__)))
    write_csv(args.out/'counts.csv',counts); write_csv(args.out/'pairs.csv',pair_rows)
    write_csv(args.out/'clusters.csv',cluster);write_csv(args.out/'metrics.csv',metric_rows)
    write_csv(args.out/'raw-index.csv',raw_rows)
    write_csv(args.out/'horizons.csv',horizons);write_csv(args.out/'activity-profiles.csv',activity_profiles)
    (args.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['complete','records','seed_clusters','counts','cluster_effects','interaction_raw_p','interaction_holm_p','activity_ratios','warning_scores','compute']},indent=2))


if __name__=='__main__': main()
