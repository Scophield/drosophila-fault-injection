"""Plot the completed prospective matrix without estimating population reliability."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.summary.read_text())
    if not data.get('complete'):
        raise ValueError('a completed experiment matrix is required')
    if len(data['test_seed_clusters']) != 6 or data['azimuths'] != [-30.,30.]:
        raise ValueError('this figure requires six seeds and the declared -30/+30 degree grid')
    for name, expected in data['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'prospective input changed: {name}')
    args.out.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.size':8, 'pdf.fonttype':42, 'svg.fonttype':'none',
                         'axes.spines.top':False, 'axes.spines.right':False})
    labels = ['Healthy', '25% deletion', '50% deletion', 'Readout off']
    groups = [data['groups'][name] for name in
              ('brain/healthy','brain/F2_25','brain/F2_50','readout_disabled/healthy')]
    fig, axes = plt.subplots(2,1,figsize=(3.45,3.05),layout='constrained')
    ax = axes[0]
    colors = ['#286b9a','#b66a18']
    for j, phi in enumerate(data['azimuths']):
        values = [g['azimuth_collision_free_counts'][str(phi)] for g in groups]
        x = np.arange(4) + (j-.5)*.34
        ax.bar(x,values,width=.32,color=colors[j],hatch=None if phi<0 else '///',label=f'{phi:g} deg')
        for position, value in zip(x,values):
            ax.text(position,value+.12,f'{value}/6',ha='center',va='bottom',fontsize=7)
    ax.set(xticks=range(4),xticklabels=['Healthy','25%\ndeletion','50%\ndeletion','Readout\noff'],ylim=(0,6.9),yticks=[0,3,6],
           ylabel='Collision-free count',
           title='(a) Fixed 1000 ms horizon')
    ax.legend(frameon=False,loc='upper right',fontsize=7)
    ax = axes[1]
    for j, phi in enumerate(data['azimuths']):
        for k, seed in enumerate(data['test_seed_clusters']):
            offset = np.linspace(-.04,.04,6)[k]
            values = [next(r['ratio'] for r in data['groups'][f'brain/{fault}']['activity_pairs']
                           if r['window_ms']==400 and r['phi']==phi and r['seed']==seed)
                      for fault in ('F2_25','F2_50')]
            ax.plot(np.arange(2)+(j-.5)*.18+offset, values, color=colors[j],
                    lw=.65, alpha=.3, zorder=1)
    for index, fault in enumerate(('F2_25','F2_50')):
        rows = [r for r in data['groups'][f'brain/{fault}']['activity_pairs']
                if r['window_ms']==400]
        for j, phi in enumerate(data['azimuths']):
            values = [next(r['ratio'] for r in rows if r['phi']==phi and r['seed']==s)
                      for s in data['test_seed_clusters']]
            offset = np.linspace(-.04,.04,len(values))
            ax.scatter(index+(j-.5)*.18+offset,values,color=colors[j],marker='o' if phi<0 else '^',
                       facecolors=colors[j] if phi<0 else 'none',s=28,zorder=3)
        median = np.median([r['ratio'] for r in rows])
        ax.plot([index-.25,index+.25],[median,median],color='#222222',lw=1.5)
    ax.axhline(1,color='.55',ls='--',lw=.8)
    ax.set(xticks=[0,1],xticklabels=labels[1:3],
           ylabel='Paired spike ratio (log)',yscale='log',
           title='(b) Common first 400 ms')
    ax.yaxis.set_major_locator(FixedLocator([0.75,1,1.25]))
    ax.yaxis.set_major_formatter(FixedFormatter(['0.75','1','1.25']))
    ax.yaxis.set_minor_locator(NullLocator())
    for suffix in ('pdf','png','svg'):
        fig.savefig(args.out/f'prospective_outcomes.{suffix}',dpi=200,bbox_inches='tight')
    plt.close(fig)
    manifest = dict(summary_sha256=hashlib.sha256(args.summary.read_bytes()).hexdigest(),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    interpretation='Raw six-seed directional counts; no population confidence interval')
    (args.out/'prospective_plot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(args.out/'prospective_outcomes.pdf')


if __name__=='__main__':
    main()
