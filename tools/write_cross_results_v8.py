"""Generate the main factorial table and bounded prose from verified results."""
import argparse
import json
from pathlib import Path

from cross_records_v8 import ROOT, sha
from audit_cross_v8 import check_cross


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary', type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.summary.read_text())
    if not data['complete'] or data['record_count'] != 72:
        raise ValueError('complete matrix required')
    for name, expected in data['source_sha256'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('measurement changed')
    lines = [r'''\begin{table}[t]
\caption{Frozen controller $\times$ fault comparison, seeds 12--17. Six clusters share both bearings and all conditions. L/G: paired healthy-to-fault losses/gains out of 12; healthy survivors at risk are four/six under original/gated laws. Healthy rows reuse preserved records.}
\label{tab:steering}
\centering\small
\setlength{\tabcolsep}{3pt}
\begin{tabular}{llrrrr}
\toprule
Law & Network & $-30^\circ$ & $+30^\circ$ & Total & L/G\\
\midrule''']
    for mode, label in zip(data['modes'], ['Original', 'Pre-cue gate']):
        for fault in data['faults']:
            g = data['groups'][f'{mode}/{fault or "healthy"}']
            network = 'Healthy' if fault is None else fault[-2:]+r'\% deletion'
            loss_gain = '---' if fault is None else f"{g['task_losses']}/{g['task_gains']}"
            lines.append(f"{label} & {network} & {g['by_bearing']['-30.0']}/6 & "
                         f"{g['by_bearing']['30.0']}/6 & {g['collision_free']}/12 & {loss_gain}"+r'\\')
    lines += [r'\bottomrule\end{tabular}\end{table}']
    lines = ['\n'.join(lines)]
    lines.append(r'''The 72-record matrix directly pairs each fault with its
same-law healthy reference (Table~\ref{tab:steering}). The healthy gate advantage
is two episodes out of 12 (+16.7 percentage points); its six-cluster conditional
range includes zero. Offset-only and no-steering healthy controls triggered
bursts in 11/12 and 12/12 cases but yielded 0/12 survival (Supplementary
Tables~S12--S14). These compare complete feedback laws, which can change sensory
trajectories and trigger timing.''')
    sentences = []
    independent = check_cross(args.summary)
    if not independent['passed']:
        raise ValueError('independent outcome audit failed')
    for fault, q in data['interactions'].items():
        lo, hi = q['conditional_cluster_bootstrap95']
        sentences.append(f"At {fault[-2:]}\\% deletion, gated-minus-original net task loss was "
                         f"{100*q['mean']:+.1f} percentage points "
                         f"(conditional 95\\% range {100*lo:.1f} to {100*hi:.1f}).")
    for fault, q in data['interactions'].items():
        lo,hi = q['conditional_cluster_bootstrap95']
        sensitivity = independent['exact_intervals'][fault]['posthoc_sign_flip_sensitivity']
        if not lo <= 0 <= hi:
            sentences.append(f"The {fault[-2:]}\\% range excludes zero, but only {sensitivity['nonzero_clusters']} seed clusters have nonzero interactions; "
                             f"a post-hoc symmetric-null sign-flip sensitivity gives $p={sensitivity['two_sided_p']:.2f}$ "
                             '(Supplementary Section~13).')
    if all(data['groups'][m+'/F2_50']['collision_free']==0 for m in data['modes']):
        sentences.append('At 50\\% deletion, both controllers yield 0/12; their net-loss contrast reflects different healthy baselines.')
    sentences.append('Loss and gain counts are retained separately; a healthy success difference alone is not a fault-tolerance comparison.')
    lines.append(' '.join(sentences))
    groups = [data['groups'][f'{mode}/{fault}'] for mode in data['modes'] for fault in data['faults'][1:]]
    collisions = sum(g['n']-g['collision_free'] for g in groups)
    max_ratio = max(p['windows'][str(w)] for p in data['pairs'] for w in (200,300,400,500))
    if all(q['flagged_collisions']==0 for q in data['thresholds']):
        false_flags = sum(q['flagged_survivors'] for q in data['thresholds']
                          if q['window_ms']==500 and q['c']==1.5)
        lines.append(f"Among 48 faulty episodes, {collisions} collided; none of these collisions was flagged at any tested "
                     r"$c=1.5,2,3,4$ over 200--500\,ms. "
                     f"At 500\\,ms, $c=1.5$ instead flagged {false_flags} surviving fault episodes. "
                     'This activity-only criterion did not distinguish the observed collisions under these settings; '
                     'it does not establish that spike count is generally uninformative. '
                     'Supplementary Table~S22 and the threshold CSV report the full sensitivity.')
    elif max_ratio <= 1.5:
        lines.append(f"Across 200--500\\,ms, no paired spike ratio exceeded 1.5, despite {collisions}/48 fault episodes colliding. "
                     r"Consequently $c=1.5,2,3,4$ flagged none of these collisions. "
                     'This activity-only criterion did not distinguish the observed outcomes under these settings; '
                     'it does not establish that spike count is generally uninformative.')
    else:
        lines.append(r'Activity-only flags and unflagged collisions for $c=1.5,2,3,4$ are reported at each shared window in Supplementary Table~S22 and the threshold CSV; this is distinct from the archived joint rule.')
    target = ROOT/'paper/sections/controller_results.tex'
    target.write_text('\n\n'.join(lines)+'\n', encoding='ascii')
    print(target)


if __name__ == '__main__':
    main()
