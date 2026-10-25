"""Plot canonical-count warning operating points from executed saved-record analysis.

Produces Fig. 4 only, in a fresh output directory. No neural execution, threshold
selection, source-record writes or modifications to approved figures are made.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import platform

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.text import Text


ROOT = Path(__file__).resolve().parents[1]
TAGS = ['RF-0', 'RF-A', 'RF-B']
EXPECTED_RECORDS = dict(zip(TAGS, [288, 144, 144]))
EXPECTED_CLUSTERS = dict(zip(TAGS, [24, 12, 12]))
EXPECTED_CONTACTS = dict(zip(TAGS, [13, 3, 1]))
BLUE, ORANGE, PURPLE = '#337BA0', '#BC5A3D', '#7763B1'
INK, GRAY, LINE = '#243B49', '#677983', '#D6DFE3'
METHODS = [
    ('transmission', 'Command', BLUE, 'o'),
    ('equal_duration_two_sided', 'Activity', ORANGE, '^'),
    ('deadline', 'Forecast*', PURPLE, 's'),
]
BASENAME = 'v10_1_warning_count'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_probability(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name}: expected a numeric probability')
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{name}: probability outside [0,1]')


def validate(data):
    maps = data['maps']
    if set(maps) != set(TAGS):
        raise ValueError('Expected exactly RF-0, RF-A and RF-B')
    total = 0
    for tag in TAGS:
        info = maps[tag]
        if info['records'] != EXPECTED_RECORDS[tag] or info['seed_clusters'] != EXPECTED_CLUSTERS[tag]:
            raise ValueError(f'{tag}: unexpected record or independent-seed count')
        total += info['records']
        for name, _, _, _ in METHODS:
            q = info['warning_scores'][name]['all']
            counts = [q[k] for k in ['tp', 'fp', 'tn', 'fn']]
            if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in counts):
                raise ValueError(f'{tag}/{name}: invalid confusion count')
            if sum(counts) != EXPECTED_RECORDS[tag] or q['tp']+q['fn'] != EXPECTED_CONTACTS[tag]:
                raise ValueError(f'{tag}/{name}: changed cohort or contact denominator')
            for metric, num, den in [
                ('false_negative_rate', q['fn'], q['tp']+q['fn']),
                ('false_positive_rate', q['fp'], q['fp']+q['tn']),
            ]:
                point = q[metric]
                finite_probability(point, f'{tag}/{name}/{metric}')
                if not math.isclose(point, num/den, rel_tol=0, abs_tol=1e-14):
                    raise ValueError(f'{tag}/{name}: rate/count mismatch')
                ci = q[metric+'_interval']
                if not isinstance(ci, list) or len(ci) != 2:
                    raise ValueError(f'{tag}/{name}: missing two-sided interval')
                for endpoint in ci:
                    finite_probability(endpoint, f'{tag}/{name}/{metric}/CI')
                if not ci[0] <= point <= ci[1]:
                    raise ValueError(f'{tag}/{name}: interval does not bracket estimate')
                if metric == 'false_positive_rate' and ci[1] > .42:
                    raise ValueError('False-alarm CI exceeds the preserved axis; revise layout explicitly')
    if total != 576:
        raise ValueError('Incomplete core cohort')
    return maps


def style():
    # Keep the approved quantitative-figure typography and semantic palette.
    findfont(FontProperties(family='Arial'), fallback_to_default=False)
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': ['Arial'], 'font.size': 8,
        'axes.labelsize': 8, 'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .7,
        'lines.linewidth': 1.05, 'text.color': INK, 'axes.labelcolor': INK,
        'legend.frameon': False, 'pdf.fonttype': 42, 'ps.fonttype': 42,
        'svg.fonttype': 'none', 'savefig.facecolor': 'white',
    })


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError('Use a fresh figure output directory')
    data = json.loads(args.input.read_text(encoding='utf-8-sig'))
    maps = validate(data)
    style()
    fig = plt.figure(figsize=(3.5, 2.55), facecolor='white')
    miss = fig.add_axes([.23, .34, .30, .45])
    alarm = fig.add_axes([.65, .34, .30, .45])
    rows = []
    for i, tag in enumerate(TAGS):
        y = 2-i
        for j, (name, label, color, marker) in enumerate(METHODS):
            q = maps[tag]['warning_scores'][name]['all']
            yy = y+(1-j)*.18
            for ax, metric in [(miss, 'false_negative_rate'), (alarm, 'false_positive_rate')]:
                ci = 100*np.asarray(q[metric+'_interval'])
                ax.plot(ci, [yy]*2, color=color, lw=.9)
                ax.scatter(100*q[metric], yy, color=color, marker=marker, s=15, zorder=3)
            rows.append(dict(
                map=tag, records=maps[tag]['records'], seed_clusters=maps[tag]['seed_clusters'],
                criterion=name, display_label=label, tp=q['tp'], fp=q['fp'], tn=q['tn'], fn=q['fn'],
                contact_denominator=q['tp']+q['fn'], success_denominator=q['fp']+q['tn'],
                false_negative_rate=q['false_negative_rate'],
                false_negative_rate_low=q['false_negative_rate_interval'][0],
                false_negative_rate_high=q['false_negative_rate_interval'][1],
                false_positive_rate=q['false_positive_rate'],
                false_positive_rate_low=q['false_positive_rate_interval'][0],
                false_positive_rate_high=q['false_positive_rate_interval'][1],
            ))
    labels = []
    for tag in TAGS:
        q = maps[tag]['warning_scores']['transmission']['all']
        labels.append(f'{tag}\n{q["tp"]+q["fn"]} / {q["fp"]+q["tn"]}')
    miss.set(yticks=[2, 1, 0], yticklabels=labels, ylim=(-.45, 2.45),
             xlim=(-5, 105), xticks=[0, 50, 100], xlabel='Missed contacts (%)')
    alarm.set(yticks=[2, 1, 0], yticklabels=[], ylim=(-.45, 2.45),
              xlim=(-2, 42), xticks=[0, 20, 40], xlabel='False alarms (%)')
    for ax in [miss, alarm]:
        ax.tick_params(axis='y', length=0)
        ax.axvline(0, color=LINE, lw=.5, zorder=0)
    fig.text(.03, .94, '(a) Misses', weight='bold', fontsize=8.5)
    fig.text(.59, .94, '(b) False alarms', weight='bold', fontsize=8.5)
    for _, label, color, marker in METHODS:
        miss.scatter([], [], s=15, color=color, marker=marker, label=label)
    fig.legend(*miss.get_legend_handles_labels(), loc='lower center', ncol=3,
               fontsize=7.5, bbox_to_anchor=(.53, .08), columnspacing=.6,
               handlelength=.8, handletextpad=.3)
    fig.text(.20, .025, '* Exact simulated state; not neural-only.', fontsize=7.5, color=GRAY)
    fig.canvas.draw()
    sizes = [obj.get_fontsize() for obj in fig.findobj(Text) if obj.get_text()]
    if min(sizes) < 7.5:
        raise ValueError('Font below the preserved 7.5-pt minimum')
    args.out.mkdir(parents=True, exist_ok=False)
    source_csv = args.out/(BASENAME+'_source.csv')
    with source_csv.open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    for ext in ['pdf', 'svg', 'png']:
        fig.savefig(args.out/(BASENAME+'.'+ext), dpi=600, facecolor='white')
    plt.close(fig)
    contract = ROOT/'docs/WARNING_FIGURE_CONTRACT_V10_1.md'
    manifest = dict(
        input_file=args.input.as_posix(), input_sha256=sha(args.input), script_sha256=sha(__file__),
        figure_contract_sha256=sha(contract), figure=BASENAME,
        outputs={p.name:dict(bytes=p.stat().st_size, sha256=sha(p)) for p in args.out.iterdir()},
        size_inches=[3.5, 2.55], png_dpi=600, minimum_font_pt=min(sizes),
        font_family='Arial', pdf_fonttype=42, svg_text='editable',
        runtime=dict(python=platform.python_version(), numpy=np.__version__, matplotlib=matplotlib.__version__),
        total_records=576, independent_seed_clusters=EXPECTED_CLUSTERS,
        positive_class_seed_clusters=dict(zip(TAGS, [12, 2, 1])),
        intervals='Pointwise 95% whole-seed percentile bootstrap CIs from the executed input analysis',
        scientific_boundary='Sparse class-conditional empirical intervals do not establish zero population error. Exact-state forecast is not neural-only. These are frozen operating points, not matched-information ROC comparisons.',
        original_records_modified=False, thresholds_selected=False, neural_simulation=False,
        fig1_to_3_modified=False, blender_modified=False,
    )
    with (args.out/'figure-manifest.json').open('x', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2); f.write('\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
