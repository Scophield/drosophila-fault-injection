"""Independent raw-outcome and exact-bootstrap audit of the factorial summary."""
import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np

from cross_records_v8 import ROOT, sha


def check_cross(summary):
    data = json.loads(Path(summary).read_text())
    records = [json.loads((ROOT/name).read_text()) for name in data['source_sha256']]
    raw = {(r['mode'],r['fault'],r['phi_t_deg'],r['seed']):r for r in records}
    if len(raw) != 72 or len(records) != 72:
        raise AssertionError('72 unique raw records required')
    errors, exact_intervals = [], {}
    for name,g in data['groups'].items():
        mode,condition = name.split('/')
        fault = None if condition=='healthy' else condition
        rows = [r for r in records if (r['mode'],r['fault'])==(mode,fault)]
        if len(rows)!=12 or sum(r['termination_reason']=='horizon' for r in rows)!=g['collision_free']:
            errors.append(f'raw group count differs: {name}')
    for pair in data['pairs']:
        m,f,p,s = (pair[k] for k in ('mode','fault','phi','seed'))
        h,r = raw[(m,None,p,s)],raw[(m,f,p,s)]
        yh,yf = (int(v['termination_reason']=='horizon') for v in (h,r))
        if (int(yh==1 and yf==0),int(yh==0 and yf==1),yh-yf) != tuple(pair[k] for k in ('task_loss','task_gain','net_loss')):
            errors.append('loss/gain sign differs from raw outcomes')
        for w,reported in [(int(k),v) for k,v in pair['windows'].items()]+[(pair['common_duration_ms'],pair['common_ratio'])]:
            counts = [{q['t_end_ms']:q['n_total'] for q in v['log']}[w] for v in (h,r)]
            if not np.isclose(reported,counts[1]/counts[0],rtol=0,atol=1e-14):
                errors.append('activity differs from completed raw frames')
    for fault,q in data['interactions'].items():
        scores = []
        for s in data['test_seed_clusters']:
            score = 0
            for p in data['azimuths']:
                d = [int(raw[(m,None,p,s)]['escaped'])-int(raw[(m,fault,p,s)]['escaped'])
                     for m in ('brain','precue_gated')]
                score += d[1]-d[0]
            scores.append(score/2)
        if scores!=q['seed_values'] or not np.isclose(np.mean(scores),q['mean']):
            errors.append('interaction differs from raw survival')
        draws = np.mean(np.array(list(itertools.product(scores,repeat=6))),axis=1)
        exact = np.percentile(draws,[2.5,97.5]).tolist()
        exact_intervals[fault] = dict(ordered_resamples=len(draws),exact_bootstrap95=exact,
                                     monte_carlo95=q['conditional_cluster_bootstrap95'])
        flips = np.asarray(list(itertools.product((-1,1),repeat=6)))
        null_means = (flips*np.asarray(scores)).mean(axis=1)
        exact_intervals[fault]['posthoc_sign_flip_sensitivity'] = dict(
            sign_patterns=len(flips), nonzero_clusters=sum(v!=0 for v in scores),
            two_sided_p=float(np.mean(np.abs(null_means)>=abs(np.mean(scores))-1e-12)),
            assumption='Independent seed clusters with a symmetric zero-centered interaction null; post-hoc exploratory sensitivity, not a randomized controller assignment.')
        if not np.allclose(exact,q['conditional_cluster_bootstrap95'],atol=1/12):
            errors.append('Monte Carlo range differs materially from exact bootstrap')
    for q in data['thresholds']:
        mode,fault,w,c = (q[k] for k in ('mode','fault','window_ms','c'))
        counts = dict(flagged_collisions=0,unflagged_collisions=0,flagged_survivors=0,unflagged_survivors=0)
        for p in data['azimuths']:
            for s in data['test_seed_clusters']:
                h,f = raw[(mode,None,p,s)],raw[(mode,fault,p,s)]
                spike = lambda r: next(v['n_total'] for v in r['log'] if v['t_end_ms']==w)
                flag = spike(f)>c*spike(h)
                key = ('flagged_' if flag else 'unflagged_')+('survivors' if f['escaped'] else 'collisions')
                counts[key] += 1
        if any(q[k]!=v for k,v in counts.items()):
            errors.append('threshold table differs from raw counts')
    return dict(passed=not errors,errors=errors,raw_records=len(records),paired_records=len(data['pairs']),
                threshold_rows=len(data['thresholds']),exact_intervals=exact_intervals,
                summary_sha256=sha(Path(summary)),auditor_sha256=sha(Path(__file__)))


def archive_thresholds():
    def load(path):
        return [json.loads(v) for v in path.read_text().splitlines() if v.strip()]
    core = ROOT/'sim/results/real'
    healthy = load(core/'healthy.jsonl')
    rate,spikes = [np.median([r[k] for r in healthy]) for k in ('pop_rate','n_total_spikes')]
    cohorts = {p.stem:load(p) for p in core.glob('*.jsonl') if p.stem!='healthy'}
    cohorts.update({p.stem:load(p) for p in (ROOT/'sim_vision/results_vision/openloop_controls').glob('*.jsonl')
                    if p.stem.startswith(('HUB_','EIm_','INHrand_'))})
    groups = {'all':list(cohorts),'no_inhibitory_hubs':[k for k in cohorts if k!='HUB_inh'],
              'no_targeted_hubs':[k for k in cohorts if not k.startswith(('F4_','HUB_','EIm_'))],
              'main_nonhub':[k for k in cohorts if k.startswith(('F1_','F2_','F3_','F5_'))]}
    output = []
    for label,names in groups.items():
        rows = [r for name in names for r in cohorts[name]]
        for c in (1.5,2,3,4):
            t = sum(r['pop_rate']>=51.4 for r in rows)
            j = int(sum(r['pop_rate']>=51.4 and r['pop_rate']<=c*rate and r['n_total_spikes']<=c*spikes for r in rows))
            output.append(dict(cohort=label,c=c,n=len(rows),transmission=t,joint=j,additional=t-j))
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args = ap.parse_args()
    result = check_cross(args.summary)
    args.out.mkdir(parents=True,exist_ok=False)
    result['archive_thresholds'] = archive_thresholds()
    (args.out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    with (args.out/'archive_thresholds.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(result['archive_thresholds'][0]))
        writer.writeheader()
        writer.writerows(result['archive_thresholds'])
    print(json.dumps(result,indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
