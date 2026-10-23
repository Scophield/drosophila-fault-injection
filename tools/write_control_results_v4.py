"""Build manuscript/supplement tables only from a verified complete control summary."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    from analyze_controls_v4 import analyze
    source=ROOT/'audit/controls-v4/controls.json'
    d=json.loads(source.read_text())
    if not d['complete'] or d!=analyze(): raise ValueError('unverified control summary')
    names=dict(brain='Original law',precue_gated='Pre-cue gate',bias_only='Offset only',steer_disabled='No steering')
    rows=[]
    for mode in d['modes']:
        g=d['groups'][f'{mode}/healthy']
        counts=g['azimuth_collision_free_counts']
        rows.append(f"{names[mode]} & {counts['-30.0']}/6 & {counts['30.0']}/6 & {g['collision_free']}/12 & {g['burst_active_at_horizon']}\\\\")
    text=r'''\begin{table}[t]
\caption{New paired healthy controls, seeds 12--17. Each law retains the neural burst-trigger rule. B: survivors still bursting at 1000\,ms. Bearings share six seed clusters.}
\label{tab:steering}
\centering\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrrr}
\toprule
Control law & $-30^\circ$ & $+30^\circ$ & Total & B\\
\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule
\end{tabular}
\end{table}
'''
    gate=d['contrasts']['precue_gated']
    lo,hi=gate['conditional_cluster_bootstrap95']
    differences=gate['seed_mean_differences']
    improved=sum(v>0 for v in differences)
    worsened=sum(v<0 for v in differences)
    unchanged=sum(v==0 for v in differences)
    text+=f"On seeds 12--17, gating versus the original law yielded {100*gate['mean_difference']:+.1f} percentage points (conditional 95\\% percentile bootstrap range {100*lo:.1f}--{100*hi:.1f}). "
    text+=f"The six paired seed clusters included {improved} improving, {worsened} worsening and {unchanged} unchanged clusters. The range includes zero difference, and every positive-bearing test collided. "
    text+="Offset-only and steering-disabled controls triggered bursts in 11/12 and 12/12 cases yet always collided. Under these settings, offset and triggering alone were insufficient. Feedback changes subsequent input and trigger timing; these comparisons concern complete closed-loop laws. The supplement reports every seed and termination.\n"
    (ROOT/'paper/sections/controller_results.tex').write_text(text)
    md=['# Completed controller evidence','',
        '| Law | -30 degrees | +30 degrees | Total | Active burst at horizon | Neural triggers |',
        '|---|---:|---:|---:|---:|---:|']
    for mode in d['modes']:
        g=d['groups'][f'{mode}/healthy']; c=g['azimuth_collision_free_counts']
        md.append(f"| {names[mode]} | {c['-30.0']}/6 | {c['30.0']}/6 | {g['collision_free']}/12 | {g['burst_active_at_horizon']} | {d['trigger_counts'][mode]}/12 |")
    md+=['','| Paired contrast vs original | Mean survival difference | Conditional 95% cluster interval | Seed differences (12--17) |',
           '|---|---:|---|---|']
    for mode,q in d['contrasts'].items():
        md.append(f"| {names[mode]} | {q['mean_difference']:.6f} | {q['conditional_cluster_bootstrap95']} | {q['seed_mean_differences']} |")
    md+=['','Differences average both bearings within seed. Six seed clusters are resampled together; no iid 12-record inference is made. These intervals are exploratory and conditional on the calibration.',
         '', '| Law | Survive 800 ms | Survive 1000 ms |', '|---|---:|---:|']
    for mode in d['modes']:
        g=d['groups'][f'{mode}/healthy']['survival_by_horizon_ms']
        md.append(f"| {names[mode]} | {g['800']}/12 | {g['1000']}/12 |")
    md+=['','| Seed | Original (-30,+30) | Gate (-30,+30) | Offset (-30,+30) | No steering (-30,+30) |',
          '|---|---|---|---|---|']
    for s in d['test_seed_clusters']:
        values=[','.join(str(int(next(p['survived'] for p in d['pairs'] if
                          (p['mode'],p['phi'],p['seed'])==(mode,phi,s)))) for phi in d['azimuths']) for mode in d['modes']]
        md.append('| '+str(s)+' | '+' | '.join(values)+' |')
    r=json.loads((ROOT/'audit/refractory-v4/summary.json').read_text())
    md+=['','## Measured compute','',
         '| Campaign | Neural episodes | Elapsed wall seconds | Sum of episode wall seconds |',
         '|---|---:|---:|---:|',
         f"| Paired controls, three workers | 48 | {d['execution']['wall_seconds']:.1f} | {d['episode_seconds_total']:.1f} |",
         f"| Refractory sensitivity, one worker | 12 | {r['wall_seconds']:.1f} (after construction) | {r['trial_wall_seconds']:.1f} |",
         '',f"Refractory network construction: {r['build_seconds']:.1f} seconds. Control episode timings include state restoration and frame processing; their sum is not CPU time. Campaign elapsed time includes parallel overlap. Complete older campaign runtime is unavailable.",
         '', 'Each control batch preserves the exact source used for the simulation. Every trigger and pre-cue heading was reconstructed from completed records. No threshold was refitted.']
    (source.parent/'results.md').write_text('\n'.join(md)+'\n')


if __name__=='__main__': main()
