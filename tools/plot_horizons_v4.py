"""Figure contract: show late activity crossings without changing observation duration.

Python quantitative grid; raw paired trajectories and exact crossing times.
Main: single-column PDF with embedded text; supplement: paired stopping estimands.
No confidence bands or independent-sample inference from three shared seeds.
"""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'audit/horizon-figures-v4b')
    args=ap.parse_args()
    source=ROOT/'audit/horizons-v4/horizons.json'
    data=json.loads(source.read_text())
    for name,h in data['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h: raise ValueError(name)
    out=args.out
    out.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.size':8,'axes.titlesize':8.5,'pdf.fonttype':42,
                          'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(3.45,1.9),layout='constrained')
    colors={-60:'#39785c',-30:'#286b9a',30:'#b66a18',60:'#715387'}
    markers={-60:'o',-30:'s',30:'^',60:'D'}
    for phi in (-60,-30,30,60):
        rows=[p for p in data['pairs'] if p['fault']=='F4_1pct' and p['phi']==phi]
        for i,p in enumerate(rows):
            times=np.array([int(t) for t in p['ratios']])
            ratios=list(p['ratios'].values())
            ax.plot(times,ratios,color=colors[phi],lw=.8,alpha=.8,
                    marker=markers[phi],markevery=[0,-1],ms=2.5,
                    label=f'{phi:+d}°'+(' (cal.)' if phi<0 else '') if i==0 else None)
            if p['first_twofold_ms'] is not None:
                t=p['first_twofold_ms']
                ax.scatter(t,p['ratios'][str(t)],color=colors[phi],marker='x',s=18,zorder=4)
    ax.axhline(2,color='.3',ls='--',lw=.8)
    ax.axvline(400,color='.6',ls=':',lw=.8)
    ax.text(410,1.06,'400 ms',fontsize=7,color='.4')
    ax.set(xlabel='Observation horizon (ms)',ylabel='Fault / healthy spikes',
           xticks=[200,400,600,800,1000],ylim=(1.02,2.7),xlim=(190,1010))
    ax.legend(loc='upper left',fontsize=6.8,ncol=2,handlelength=1.5,columnspacing=.8,frameon=False)
    for ext in ('pdf','svg','png'): fig.savefig(out/f'late_hubs.{ext}',dpi=250,bbox_inches='tight',pad_inches=.03)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(7.1,2.7),layout='constrained')
    for ax,fault,title in zip(axes,['F2_50','F4_1pct'],['(a) Unequal stopping times: 50% deletion','(b) Equal 1000-ms records: full hubs']):
        rows=[p for p in data['pairs'] if p['fault']==fault]
        for i,p in enumerate(rows):
            values=[p['whole_ratio'],p['common_ratio'],p['ratios']['400']]
            ax.plot(np.arange(3)+(i-5.5)*.006,values,color=colors[p['phi']],alpha=.55,lw=.7,
                    marker=markers[p['phi']],ms=3)
        ax.plot(range(3),[np.median([p[k] if k!='ratios' else p[k]['400'] for p in rows])
                         for k in ('whole_ratio','common_ratio','ratios')],color='.15',lw=2)
        ax.axhline(2,color='.4',ls='--',lw=.8)
        ax.set(xticks=range(3),xticklabels=['Whole totals','Common duration','First 400 ms'],
               ylabel='Fault / healthy spikes',title=title)
    handles=[Line2D([],[],color=colors[phi],marker=markers[phi],lw=.8,
                    label=f'{phi:+d} deg'+(' (calibration)' if phi<0 else ''))
             for phi in (-60,-30,30,60)]
    handles.append(Line2D([],[],color='.15',lw=2,label='Median of 12 pairs'))
    fig.legend(handles=handles,loc='outside lower center',ncol=3,frameon=False,fontsize=7)
    for ext in ('pdf','svg','png'): fig.savefig(out/f'estimands.{ext}',dpi=250,bbox_inches='tight',pad_inches=.03)
    plt.close(fig)
    (out/'manifest.json').write_text(json.dumps(dict(source=str(source.relative_to(ROOT)),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')


if __name__=='__main__': main()
