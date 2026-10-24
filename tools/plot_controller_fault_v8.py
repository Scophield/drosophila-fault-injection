"""Draw all same-seed activity pairs from the completed factorial experiment."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
import numpy as np

from cross_records_v8 import ROOT, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.summary.read_text())
    if not data['complete'] or data['record_count'] != 72:
        raise ValueError('a completed 72-record matrix is required')
    for name, expected in data['source_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f'changed measurement: {name}')
    args.out.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.size': 8, 'pdf.fonttype': 42, 'svg.fonttype': 'none',
                         'axes.spines.top': False, 'axes.spines.right': False})
    colors = ['#286b9a', '#b66a18']
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.7), layout='constrained', sharey=True)
    for ax, mode, title in zip(axes, data['modes'], ['Original law', 'Pre-cue gate']):
        pairs = [p for p in data['pairs'] if p['mode'] == mode]
        for j, phi in enumerate(data['azimuths']):
            for k, seed in enumerate(data['test_seed_clusters']):
                x = np.arange(2) + (j-.5)*.2 + np.linspace(-.035, .035, 6)[k]
                y = [next(p['windows']['400'] for p in pairs
                          if (p['fault'],p['phi'],p['seed']) == (fault,phi,seed))
                     for fault in ('F2_25','F2_50')]
                ax.plot(x, y, color=colors[j], lw=.7, alpha=.35, zorder=1)
                ax.scatter(x, y, marker='o' if j == 0 else '^', s=25,
                           facecolors=colors[j] if j == 0 else 'none',
                           edgecolors=colors[j], zorder=3,
                           label=f'{phi:g} deg' if k == 0 else None)
        for i, fault in enumerate(('F2_25','F2_50')):
            median = np.median([p['windows']['400'] for p in pairs if p['fault'] == fault])
            ax.plot([i-.25,i+.25], [median,median], color='#222222', lw=1.5, zorder=4)
        ax.axhline(1, color='.6', ls='--', lw=.8)
        ax.axhline(1.5, color='.65', ls=':', lw=.8)
        ax.set(xticks=[0,1], xticklabels=['25% deletion','50% deletion'], title=title,
               yscale='log', xlabel='Connection-table row deletion')
    axes[0].set_ylabel('Fault / same-law healthy spikes\nCommon first 400 ms')
    axes[0].yaxis.set_major_locator(FixedLocator([.75,1,1.25,1.5]))
    axes[0].yaxis.set_major_formatter(FixedFormatter(['0.75','1','1.25','1.5']))
    axes[0].yaxis.set_minor_locator(NullLocator())
    axes[1].legend(frameon=False, fontsize=7, loc='best')
    for extension in ('pdf', 'svg', 'png'):
        fig.savefig(args.out / f'controller_fault_pairs.{extension}', dpi=400)
    plt.close(fig)
    outputs = {p.name:sha(p) for p in args.out.iterdir()}
    (args.out/'plot_manifest.json').write_text(json.dumps(dict(
        summary_sha256=sha(args.summary), script_sha256=sha(Path(__file__)),
        output_sha256=outputs, independent_seed_clusters=6,
        interpretation='Every measured pair; lines retain shared seed/bearing and nested dose identity; black bars are medians.'), indent=2)+'\n')
    print(args.out/'controller_fault_pairs.pdf')


if __name__ == '__main__':
    main()
