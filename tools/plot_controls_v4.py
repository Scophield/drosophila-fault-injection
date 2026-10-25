"""Paired control evidence: every outcome and six-cluster effect uncertainty.

Python quantitative grid, PDF/SVG/PNG supplementary export with embedded text.
Keep paired directions together; bootstrap ranges are conditional, exploratory.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'audit/controls-v4/controls.json'
    d=json.loads(source.read_text())
    if not d['complete']: raise ValueError('incomplete campaign')
    for p,h in d['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h: raise ValueError(p)
    out=ROOT/'audit/control-figures-v4b'
    out.mkdir(parents=True,exist_ok=False)
    modes=d['modes']; seeds=d['test_seed_clusters']; phis=d['azimuths']
    labels=['Original law','Pre-cue gate','Offset only','No steering']
    matrix=np.array([[next(int(r['survived']) for r in d['pairs'] if
                          (r['mode'],r['phi'],r['seed'])==(mode,phi,s))
                      for phi in phis for s in seeds] for mode in modes])
    plt.rcParams.update({'font.size':8,'pdf.fonttype':42,'svg.fonttype':'none',
                          'axes.spines.right':False,'axes.spines.top':False})
    fig,axes=plt.subplots(1,2,figsize=(7.1,2.7),width_ratios=[1.6,1],layout='constrained')
    ax=axes[0]
    ax.imshow(matrix,cmap=ListedColormap(['#e8e8e8','#286b9a']),vmin=0,vmax=1,aspect='auto')
    for (i,j),v in np.ndenumerate(matrix): ax.text(j,i,str(v),ha='center',va='center',color='white' if v else '.2')
    ax.set(yticks=range(4),yticklabels=labels,xticks=range(12),xticklabels=seeds+seeds,
           xlabel='Paired seed (1: collision-free at 1000 ms)',title='(a) Every paired outcome')
    ax.axvline(5.5,color='white',lw=2)
    ax.text(2.5,-.8,'-30°',ha='center'); ax.text(8.5,-.8,'+30°',ha='center')
    ax.set_title('(a) Every paired outcome',pad=25)
    ax=axes[1]
    for i,mode in enumerate(modes[1:]):
        q=d['contrasts'][mode]; mid=q['mean_difference']; lo,hi=q['conditional_cluster_bootstrap95']
        ax.errorbar(mid,i,xerr=[[mid-lo],[hi-mid]],fmt='o',color='#286b9a',capsize=3,ms=4)
        values=q['seed_mean_differences']
        ax.scatter(values,i+np.linspace(-.12,.12,6),s=12,facecolor='none',edgecolor='.4')
    ax.axvline(0,color='.4',lw=.8,ls='--')
    ax.set(yticks=range(3),yticklabels=labels[1:],xlim=(-1,1),xticks=[-1,-.5,0,.5,1],
           xlabel='Survival difference vs original',title='(b) Six seed clusters')
    ax.invert_yaxis()
    ax.set_title('(b) Six seed clusters',pad=25)
    fig.supxlabel('Blue: mean with conditional 95% bootstrap range; open circles: seed means.',fontsize=7)
    for ext in ('pdf','svg','png'): fig.savefig(out/f'paired_controls.{ext}',dpi=250,bbox_inches='tight')
    plt.close(fig)
    (out/'manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        interval='conditional 95% bootstrap over six seed clusters, 20000 draws'),indent=2)+'\n')


if __name__=='__main__': main()
