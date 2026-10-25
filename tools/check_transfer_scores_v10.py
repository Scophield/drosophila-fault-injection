"""Independent warning intervals and primary loss/gain/exposure arithmetic.

This consumes complete checked outputs; it neither fits thresholds nor changes
the registered analysis. Bootstrap support counts disclose draws with no class.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['transmission', 'stop_count_upper', 'equal_duration_upper',
         'equal_duration_two_sided', 'schedule_only', 'deadline']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--transfer', type=Path, required=True)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    top = json.loads((a.transfer/'summary.json').read_text())
    if not top['complete'] or len(top['maps']) != 2:
        raise ValueError('Both complete RF matrices required')
    inputs, errors, reports = {(a.transfer/'summary.json').resolve().relative_to(ROOT).as_posix():sha(a.transfer/'summary.json')}, [], {}

    def read(p):
        inputs[p.resolve().relative_to(ROOT).as_posix()] = sha(p)
        return json.loads(p.read_text())

    for mapped in top['maps']:
        tag = mapped['map_id']
        reg = read(a.root/('map-'+tag)/'registration.json')
        folder = a.transfer/('map-'+tag)/'analysis'
        summary = read(folder/'summary.json')
        raw = []
        for name, expected in summary['raw_input_sha256'].items():
            p = ROOT/name
            if sha(p) != expected:
                raise ValueError('Raw input changed: '+name)
            raw.append(read(p))
        if len(raw) != 144 or len(reg['test_seeds']) != 12:
            raise ValueError('Incomplete map')
        lookup = {(r['seed'], r['phi_deg'], r['mode'], r['fault']):r for r in raw}
        seeds = reg['test_seeds']
        draws = np.random.default_rng(reg['bootstrap']['seed']).integers(
            len(seeds), size=(reg['bootstrap']['draws'], len(seeds)))
        for item in mapped['primary']:
            for name in ['loss', 'gain', 'net_loss']:
                values = []
                for seed in seeds:
                    h = [lookup[seed,p,item['mode'],'healthy']['escaped'] for p in reg['phis']]
                    f = [lookup[seed,p,item['mode'],item['fault']]['escaped'] for p in reg['phis']]
                    loss = sum(x and not y for x,y in zip(h,f))/len(h)
                    gain = sum(not x and y for x,y in zip(h,f))/len(h)
                    values.append({'loss':loss,'gain':gain,'net_loss':loss-gain}[name])
                expected = [np.mean(values), *np.percentile(np.asarray(values)[draws].mean(1), [2.5,97.5])]
                saved = item['estimands'][name]
                if not np.allclose(expected, [saved['estimate'],*saved['ci95']], rtol=0, atol=1e-12):
                    errors.append(f'{tag}/{item["mode"]}/{item["fault"]}/{name}')
        def stop(r):
            if r['collision_ms'] is None:
                return r['horizon_ms']
            return min(q['t_end_ms'] for q in r['log'] if q['t_end_ms']+1e-8>=r['collision_ms'])
        def count(r,t):
            return next(q['n_total'] for q in r['log'] if q['t_end_ms']==t)
        for mode in reg['modes']:
            for fault in ['F2_25','F2_50']:
                values = {k:[] for k in ['stop_ratio','common_ratio','early_ratio','full_ratio']}
                for seed in seeds:
                    rows = {k:[] for k in values}
                    for phi in reg['phis']:
                        h,f = lookup[seed,phi,mode,'healthy'],lookup[seed,phi,mode,fault]
                        ht,ft = stop(h),stop(f)
                        common = min(ht,ft)
                        rows['stop_ratio'].append(count(f,ft)/count(h,ht))
                        rows['common_ratio'].append(count(f,common)/count(h,common))
                        rows['early_ratio'].append(count(f,400)/count(h,400))
                        rows['full_ratio'].append(count(f,1000)/count(h,1000))
                    for name in values:
                        values[name].append(rows[name])
                for name,matrix in values.items():
                    samples = np.median(np.asarray(matrix)[draws].reshape(len(draws),-1),axis=1)
                    expected = [np.median(matrix),*np.percentile(samples,[2.5,97.5])]
                    saved = summary['activity_ratios'][mode+'/'+fault][name]
                    if not np.allclose(expected,[saved['median'],*saved['cluster_interval']],rtol=0,atol=1e-12):
                        errors.append(f'{tag}/{mode}/{fault}/{name} exposure interval')
        metric_path = folder/'metrics.csv'
        inputs[metric_path.resolve().relative_to(ROOT).as_posix()] = sha(metric_path)
        with metric_path.open(newline='') as f:
            metrics = list(csv.DictReader(f))
        mlookup = {(int(r['seed']),float(r['phi_deg']),r['mode'],r['fault']):r for r in metrics}
        if set(mlookup) != set(lookup) or len(metrics) != len(lookup):
            raise ValueError('Warning metric coverage')
        support = {}
        for subset in ['all','healthy','faulty']:
            selected = [r for r in raw if subset == 'all' or (r['fault']=='healthy') == (subset=='healthy')]
            support[subset] = {}
            for name in NAMES:
                cells = []
                for seed in seeds:
                    row = [0,0,0,0]  # TP, FP, TN, FN
                    for r in selected:
                        if r['seed'] != seed:
                            continue
                        key = (seed,r['phi_deg'],r['mode'],r['fault'])
                        flag = mlookup[key][name].lower() == 'true'
                        positive = not r['escaped']
                        row[0 if flag and positive else 1 if flag else 3 if positive else 2] += 1
                    cells.append(row)
                totals = np.asarray(cells)[draws].sum(1)
                saved = summary['warning_scores'][name][subset]
                for label,num,den in [('sensitivity',0,3),('specificity',2,1),
                                      ('false_positive_rate',1,2),('false_negative_rate',3,0)]:
                    denominator = totals[:,num]+totals[:,den]
                    valid = denominator > 0
                    expected = np.percentile(totals[valid,num]/denominator[valid], [2.5,97.5]).tolist() if valid.any() else None
                    actual = saved[label+'_interval']
                    equal = actual is None if expected is None else actual is not None and np.allclose(expected,actual,rtol=0,atol=1e-12)
                    if not equal:
                        errors.append(f'{tag}/{subset}/{name}/{label} interval')
                    support[subset][label] = dict(valid_draws=int(valid.sum()),undefined_draws=int((~valid).sum()))
        reports[tag] = dict(records=144,clusters=12,bootstrap_draws=reg['bootstrap']['draws'],
                            class_support=support,primary_loss_gain_exposure_and_warning_intervals_checked=True)
    result = dict(passed=not errors,errors=errors,maps=reports,
                  source_sha256=sha(Path(__file__)),input_sha256=inputs,
                  scope='Independent arithmetic from unchanged raw outcomes/cumulative resource and saved Boolean warning decisions; does not retest warning feature equations, neural dynamics or physical validity. Undefined-class draws are omitted for the corresponding conditional rate.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
