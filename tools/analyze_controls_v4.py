"""Strict completed campaign summary with seed-paired controller contrasts."""
import hashlib
import json
from pathlib import Path
import numpy as np
from summarize_prospective import ROOT,summarize

MODES=('brain','precue_gated','bias_only','steer_disabled')
SEEDS=list(range(12,18))
PHIS=[-30.,30.]


def analyze():
    root=ROOT/'runs/controller-v4a'
    execution=json.loads((root/'execution.json').read_text())
    if execution['exit_codes']!=[0,0,0]: raise ValueError('campaign workers failed')
    result=summarize(root,root/'vision/calib-frozen.json',SEEDS,PHIS,MODES,(None,))
    if result['calibration_sha256']!=hashlib.sha256((ROOT/'runs/geometry-v3/vision/calib-geometry-v3.json').read_bytes()).hexdigest():
        raise ValueError('calibration changed')
    for manifest in result['generation_manifests'].values():
        candidates=[p for p in (root/'vision/batches').glob('*/run_manifest.json')
                    if json.loads(p.read_text())==manifest]
        if len(candidates)!=1: raise ValueError('ambiguous manifest')
        batch=candidates[0].parent
        for name,expected in manifest['source_sha256'].items():
            if hashlib.sha256((batch/'source'/name).read_bytes()).hexdigest()!=expected:
                raise ValueError('snapshot mismatch')
        aggregate=''.join(f'{name}:{manifest["source_sha256"][name]}\n'
                          for name in sorted(manifest['source_sha256']) if not name.startswith('external/'))
        if hashlib.sha256(aggregate.encode()).hexdigest()!=manifest['code_sha256']:
            raise ValueError('aggregate source snapshot differs from code hash')
    rows=[json.loads(p.read_text()) for p in (root/'vision/episodes_controls').glob('*.json')]
    records={(r['mode'],r['phi_t_deg'],r['seed']):r for r in rows}
    result['pairs']=[]
    for mode in MODES:
        for phi in PHIS:
            for seed in SEEDS:
                r=records[(mode,phi,seed)]; h=records[('brain',phi,seed)]
                pre=next(q for q in r['log'] if q['t_end_ms']==100)
                if pre['n_total']!=0: raise ValueError('unexpected pre-cue activity')
                expected=0 if mode in ('precue_gated','steer_disabled') else -400*20/70*.1
                if not np.isclose(pre['heading_deg'],expected): raise ValueError('pre-cue law mismatch')
                if mode=='precue_gated' and any(q['omega']!=0 for q in r['log'] if q['t_ms']<100):
                    raise ValueError('pre-cue gate not applied')
                if mode=='bias_only' and any(not np.isclose(q['omega'],-400*20/70) for q in r['log']):
                    raise ValueError('bias-only law not applied')
                if mode=='steer_disabled' and any(q['omega']!=0 for q in r['log']):
                    raise ValueError('steering not disabled')
                # Reconstruct the trigger independently from per-frame command counts.
                hist=[]; trigger=None
                for q in r['log']:
                    hist.append(sum(q['cmd_rates'].values())/8)
                    if len(hist)>=2 and np.mean(hist[-5:])>=18.125 and hist[-2]>=18.125:
                        trigger=q['t_end_ms']; break
                if trigger!=r['trigger_ms']: raise ValueError('neural trigger changed')
                result['pairs'].append(dict(mode=mode,phi=phi,seed=seed,survived=r['escaped'],
                    baseline_survived=h['escaped'],difference=int(r['escaped'])-int(h['escaped']),
                    precue_heading_deg=pre['heading_deg'],trigger_ms=trigger,
                    duration_ms=r['duration_ms'],burst_active_at_horizon=r['burst_active_at_horizon']))
    result['contrasts']={}
    for mode in MODES[1:]:
        pairs=[r for r in result['pairs'] if r['mode']==mode]
        scores=np.array([np.mean([p['difference'] for p in pairs if p['seed']==s]) for s in SEEDS])
        rng=np.random.default_rng(0)
        draws=np.mean(rng.choice(scores,size=(20000,len(scores))),axis=1)
        result['contrasts'][mode]=dict(seed_mean_differences=scores.tolist(),mean_difference=float(scores.mean()),
            conditional_cluster_bootstrap95=np.percentile(draws,[2.5,97.5]).tolist(),
            direction_differences={str(phi):sum(p['difference'] for p in pairs if p['phi']==phi)/6 for phi in PHIS},
            interpretation='six paired seed clusters, bearings kept together; exploratory, conditional on frozen calibration')
    result['execution']=execution
    for mode in MODES:
        group=result['groups'][f'{mode}/healthy']
        group['survival_by_horizon_ms']={str(t):sum(
            r['mode']==mode and (r['duration_ms']>t or r['escaped'] and r['duration_ms']>=t)
            for r in rows) for t in (800,1000)}
    result['episode_seconds_total']=sum(r['run_seconds'] for r in rows)
    result['trigger_counts']={mode:sum(r['trigger_ms'] is not None for r in rows if r['mode']==mode) for mode in MODES}
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main():
    result=analyze()
    out=ROOT/'audit/controls-v4'
    out.mkdir(parents=True,exist_ok=False)
    (out/'controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('groups','contrasts','execution','episode_seconds_total')},indent=2))


if __name__=='__main__': main()
