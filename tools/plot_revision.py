"""Publication plots of archived observations; never execute a simulator."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.size':8.5, 'axes.titlesize':9, 'axes.labelsize':8.5,
                     'pdf.fonttype':42, 'ps.fonttype':42, 'axes.spines.top':False,
                     'axes.spines.right':False, 'lines.linewidth':1.3})
BLUE, ORANGE, RED, GREEN = '#286b9a', '#b66a18', '#ad3544', '#39785c'
SOURCES = set()


def read(path):
    path = path.resolve()
    SOURCES.add(path)
    return json.loads(path.read_text())


def records(path):
    path = path.resolve()
    SOURCES.add(path)
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def save(fig, out, name):
    fig.savefig(out/f'{name}.pdf', bbox_inches='tight', pad_inches=.04)
    fig.savefig(out/f'{name}.png', bbox_inches='tight', pad_inches=.04, dpi=200)
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--assessment', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    analysis=read(args.analysis)
    core=ROOT/'sim/results/real'
    ctrl=ROOT/'sim_vision/results_vision/openloop_controls'
    vision=ROOT/'sim_vision/results_vision'
    conditions=['healthy']+[f'F2_drop_{dose:02}' for dose in (5,10,25,50)]
    trials=[records(core/f'{c}.jsonl') for c in conditions]
    fig, axes=plt.subplots(2,1,figsize=(3.45,2.65), layout='constrained')
    for ax,field,color,title,ylabel in zip(axes,['pop_rate','latency_ms'],[BLUE,ORANGE],
            ['(a) Command transmission','(b) First readout spike'],['Command rate (Hz)','Latency (ms)']):
        values=[np.array([r[field] for r in rows]) for rows in trials]
        meds=np.array([np.median(v) for v in values])
        bounds=np.array([np.percentile(v,[10,90]) for v in values]).T
        ax.errorbar([0,5,10,25,50],meds,yerr=np.abs(bounds-meds),color=color,marker='o',ms=3.5,capsize=2)
        ax.axhline(meds[0],color='.65',lw=.7)
        ax.set(xlabel='Connections deleted (%)',ylabel=ylabel,title=title,xticks=[0,5,10,25,50])
        ax.grid(axis='y',alpha=.15)
    axes[0].axhline(51.4,color=RED,ls='--',lw=.9)
    axes[0].text(49,53.2,'Transmission threshold',ha='right',color=RED,fontsize=7.5)
    axes[0].set_ylim(46,105)
    save(fig,args.out,'revision_curves')

    fig,ax=plt.subplots(figsize=(3.45,1.62), layout='constrained')
    labels=['Healthy','Full\nhubs','Inhib.\nhubs','Random\nmass']
    data=[trials[0],records(core/'F4_hub_1pct.jsonl'),records(ctrl/'HUB_inh.jsonl'),records(ctrl/'INHrand_mass.jsonl')]
    for i,(rows,color) in enumerate(zip(data,[BLUE,GREEN,RED,ORANGE])):
        ys=np.array([r['n_total_spikes'] for r in rows])/1000
        ax.scatter(i+np.linspace(-.12,.12,len(ys)),ys,s=8,color=color,alpha=.7,zorder=3)
        ax.hlines(np.median(ys),i-.23,i+.23,color=color,lw=2.2)
    ax.axhline(2*39694/1000,color='.35',ls='--',lw=.9)
    ax.set(yscale='log',ylabel='Total spikes (thousands, log)',xticks=range(4),xticklabels=labels,ylim=(25,1500))
    ax.set_yticks([40,80,300,1000],labels=['40','80','300','1000'])
    ax.text(3.3,87,'Operational limit: 2 x healthy',ha='right',fontsize=7,color='.3')
    ax.plot([],[],color='.25',lw=2.2,label='Horizontal segment: median')
    ax.legend(frameon=False,fontsize=7,loc='lower left',bbox_to_anchor=(0,1.01),borderaxespad=0)
    save(fig,args.out,'revision_activity')

    fig,axes=plt.subplots(2,1,figsize=(3.45,3.15),layout='constrained')
    for fault,label,color in [('healthy','Healthy',BLUE),('F2_50','F2 50%',ORANGE),('F4_1pct','Full hubs',GREEN),('HUB_inh','Inhib. hubs',RED)]:
        tag='v4c' if fault=='HUB_inh' else 'v4'
        e=read(vision/f'episodes_{tag}/brain_{fault}_phi30_s0.json')
        axes[0].plot([0]+[q['t_ms']+20 for q in e['log']], [.25]+[q['dist'] for q in e['log']],color=color,label=label)
    axes[0].axhline(.05,ls='--',color='.35',lw=.9)
    axes[0].set(xlabel='Recorded time (ms)',ylabel='Separation (m)',title='(a) Legacy separation (+30 deg, seed 0)',xlim=(0,1000),ylim=(0,.27))
    axes[0].legend(fontsize=7,frameon=False,ncol=2,loc='upper right',columnspacing=.8)
    ax=axes[1]
    for i,(fault,color) in enumerate(zip(['F2_25','F2_50','F4_1pct','HUB_inh'],[BLUE,ORANGE,GREEN,RED])):
        c=analysis['conditions'][fault]
        for j,r in enumerate(c['pairs']):
            ax.scatter(i+.10+(j-5.5)*.014,r['fixed400_ratio'],s=10,
                       facecolor='white' if r['calibration_scenario'] else color,edgecolor=color,linewidth=.6)
        ax.plot([i-.18,i+.18],[c['median_episode_ratio'],c['median_fixed400_ratio']],color=color,lw=1)
        ax.plot(i-.18,c['median_episode_ratio'],'s',ms=4,color=color)
        ax.plot(i+.18,c['median_fixed400_ratio'],'D',ms=4,color=color)
    ax.axhline(2,ls='--',color='.45',lw=.8)
    ax.text(3.43, 2.2, '2 x reference', ha='right', fontsize=7, color='.35')
    ax.set(yscale='log',ylabel='Paired spike ratio',title='(b) Whole totals vs first 400 ms',
           xticks=range(4),xticklabels=['F2 25%','F2 50%','Full hubs','Inhib. hubs'],ylim=(.15,250))
    ax.plot([],[],'s-',color='.3',ms=3,label='Whole episode')
    ax.plot([],[],'D-',color='.3',ms=3,label='First 400 ms')
    ax.legend(fontsize=7,frameon=False,loc='upper left')
    save(fig,args.out,'revision_demo')
    assessment_path = args.assessment or args.analysis.parent/'assessment.json'
    if args.assessment and not assessment_path.is_file():
        raise FileNotFoundError(assessment_path)
    if assessment_path.is_file():
        assessment = read(assessment_path)
        fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.7), layout='constrained')
        colors = [BLUE, ORANGE, GREEN, RED]
        for fault,color in zip(['F2_25','F2_50','F4_1pct','HUB_inh'],colors):
            q=assessment['windows'][fault]
            windows=np.array([int(w) for w in q])
            axes[0].plot(windows, [q[str(w)]['median'] for w in windows], marker='o',
                         color=color,label=fault)
            for seed in range(3):
                axes[1].plot(windows,[q[str(w)]['seed_medians'][str(seed)] for w in windows],
                             marker=['o','s','^'][seed], color=color, alpha=.7)
        for ax in axes:
            ax.axhline(2,ls='--',color='.4',lw=.8)
            ax.set(yscale='log',xlabel='Common window (ms)',xticks=[200,300,400,500],
                   ylabel='Paired spike ratio (log)')
        axes[0].set_title('(a) Median of 12 scenario pairs')
        axes[1].set_title('(b) Medians within each of three seeds')
        axes[0].legend(fontsize=7,frameon=False,ncol=2)
        save(fig,args.out,'assessment_windows')
    manifest=dict(matplotlib=matplotlib.__version__, numpy=np.__version__,
                  source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCES)},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.out/'plot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Generated {len(list(args.out.glob("*.pdf")))} PDF/PNG figures from {len(SOURCES)} saved sources in {args.out}')


if __name__=='__main__': main()
