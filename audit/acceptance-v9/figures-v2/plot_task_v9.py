"""Publication figures from verified data; schematic can be generated alone."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
    'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,
    'ps.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':.7,'savefig.facecolor':'white'})
BLUE='#34739b';ORANGE='#c97730';GRAY='#777777'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def save(fig,out,name):
    for ext in ['pdf','svg','png']:
        fig.savefig(out/f'{name}.{ext}',dpi=220,bbox_inches='tight',pad_inches=.04)
    plt.close(fig)


def overview(out):
    fig,ax=plt.subplots(figsize=(3.5,2.5));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    ax.text(0,.98,'a',fontweight='bold',va='top')
    ax.text(.07,.98,'One paired seed: 2 bearings × 2 laws × 3 networks',va='top',fontsize=7.5)
    labels=['Retinal\nrates','LIF\nnetwork','Turn +\ntrigger','Delayed\nactuator','Task +\ncounts']
    for i,label in enumerate(labels):
        x=.01+i*.20
        ax.add_patch(FancyBboxPatch((x,.70),.17,.16,boxstyle='round,pad=0.008',
            facecolor='#edf2f5',edgecolor=BLUE,linewidth=.7))
        ax.text(x+.085,.78,label,ha='center',va='center',fontsize=7.5)
        if i<4:ax.annotate('',xy=(x+.196,.78),xytext=(x+.174,.78),arrowprops=dict(arrowstyle='->',lw=.7))
    ax.annotate('',xy=(.09,.685),xytext=(.89,.685),
        arrowprops=dict(arrowstyle='->',connectionstyle='bar,fraction=-0.10',lw=.7,color=GRAY))
    ax.text(.5,.54,'Body-frame geometry feeds back; realized inputs may differ',ha='center',fontsize=7)
    ax.text(0,.45,'b',fontweight='bold')
    ax.text(.07,.45,'Distinct clocks and endpoints',fontweight='bold')
    x=lambda t:.07+.86*t/1000
    ax.plot([x(0),x(1000)],[.30,.30],color=GRAY,lw=.8)
    for t,label in [(0,'0'),(100,'Cue'),(400,'Assess'),(1000,'Task')]:
        ax.plot([x(t)]*2,[.28,.32],color=BLUE,lw=.8)
        ax.text(x(t),.35,label,ha='center',fontsize=7.5)
        ax.text(x(t),.23,f'{t:g}',ha='center',fontsize=7.5)
    ax.plot([x(200),x(450)],[.12,.12],color=GRAY,lw=1.3,linestyle='--')
    ax.plot([x(450),x(900)],[.12,.12],color=ORANGE,lw=5,solid_capstyle='butt')
    ax.text(x(325),.01,'250 ms delay',ha='center',fontsize=7.5)
    ax.text(x(675),.01,'450 ms burst',ha='center',fontsize=7.5)
    ax.text(.5,-.10,'20 ms feedback; 0.1 ms neural step; exact actuator events',ha='center',fontsize=7.5)
    save(fig,out,'task_v9_overview')


def quantitative(out,analysis):
    d=json.loads((analysis/'summary.json').read_text())
    if not d['complete'] or d['records']!=288: raise ValueError('verified complete data required')
    pairs=pd.read_csv(analysis/'pairs.csv'); metrics=pd.read_csv(analysis/'metrics.csv')
    fig,axs=plt.subplots(1,2,figsize=(7.16,2.4),layout='constrained')
    for ax,mode,label in zip(axs,['proportional','relay'],['a','b']):
        for j,phi in enumerate([-30,30]):
            rows=[next(r for r in d['counts'] if (r['mode'],r['fault'],r['phi_deg'])==(mode,f,phi))
                  for f in ['healthy','F2_25','F2_50']]
            x=np.arange(3)+(j-.5)*.32
            ax.bar(x,[r['success']/r['n'] for r in rows],width=.30,color=[BLUE,ORANGE][j],
                label=f'{phi:+g}°',edgecolor='white',linewidth=.5)
            for a,r in zip(x,rows):ax.text(a,r['success']/r['n']+.03,f"{r['success']}/{r['n']}",ha='center',fontsize=7.5)
        ax.set(xticks=range(3),xticklabels=['Healthy','25%','50%'],ylim=(0,1.19),
               yticks=[0,.25,.5,.75,1],ylabel='Collision-free fraction',xlabel='Connection-row deletion')
        ax.text(-.13,1.04,label,fontweight='bold',transform=ax.transAxes)
        ax.set_title(mode.capitalize(),fontsize=9)
    fig.legend(*axs[0].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
    save(fig,out,'task_v9_outcomes')
    fig,axs=plt.subplots(1,2,figsize=(7.16,2.5),layout='constrained')
    for j,mode in enumerate(['proportional','relay']):
        g=pairs[(pairs['mode']==mode)&(pairs['fault']=='F2_50')]
        for _,r in g.iterrows():
            axs[0].plot([j*2,j*2+1],[r['stop_ratio'],r['common_ratio']],
                color=GRAY,alpha=.28,lw=.6)
        axs[0].scatter([j*2,j*2+1],[g.stop_ratio.median(),g.common_ratio.median()],
            color='black',s=20,zorder=3)
    axs[0].set(xticks=[0,1,2,3],xticklabels=['Stop','Common','Stop','Common'],
               ylabel='Fault / paired healthy spikes',ylim=(0,None))
    axs[0].text(.19,-.25,'Proportional',ha='center',transform=axs[0].transAxes)
    axs[0].text(.80,-.25,'Relay',ha='center',transform=axs[0].transAxes)
    axs[0].text(-.13,1.04,'a',fontweight='bold',transform=axs[0].transAxes)
    axs[0].set_title('Same records, 50% deletion',fontsize=9)
    names=['transmission','equal_duration_two_sided','schedule_only','deadline']
    labels=['Command\nlow','Activity\ntwo-sided','Actuator\nschedule','Deadline\ncandidate']
    x=np.arange(4)
    for j,(metric,color) in enumerate([('sensitivity',ORANGE),('specificity',BLUE)]):
        values=np.array([d['warning_scores'][n]['all'][metric] for n in names],float)
        ints=np.array([d['warning_scores'][n]['all'][metric+'_interval'] or [np.nan,np.nan] for n in names],float)
        positions=x+(j-.5)*.20
        axs[1].scatter(positions,values,marker='o' if j==0 else 's',s=16,color=color,label=metric.capitalize())
        # Draw the actual percentile endpoints even if an unusually skewed
        # bootstrap interval does not contain the observed point estimate.
        for position,value,(low,high) in zip(positions,values,ints):
            if np.isfinite(low) and np.isfinite(high):
                axs[1].vlines(position,low,high,color=color,lw=.9)
                axs[1].hlines([low,high],position-.035,position+.035,color=color,lw=.9)
            if not np.isfinite(value):
                axs[1].text(position,.48,'Undefined',ha='center',rotation=90,fontsize=6.5,color=color)
    axs[1].set(xticks=x,xticklabels=labels,ylim=(-.04,1.08),yticks=[0,.25,.5,.75,1],ylabel='Held-out task classification')
    axs[1].set_title('400 ms assessment; all test episodes',fontsize=9)
    fig.legend(*axs[1].get_legend_handles_labels(),loc='outside upper center',ncol=2,frameon=False)
    axs[1].text(-.13,1.04,'b',fontweight='bold',transform=axs[1].transAxes)
    save(fig,out,'task_v9_assessment')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--analysis',type=Path)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    overview(args.out)
    if args.analysis: quantitative(args.out,args.analysis)
    result=dict(script_sha256=sha(Path(__file__)),
        input_sha256={str(p):sha(p) for p in args.analysis.glob('*') if p.is_file()} if args.analysis else {},
        outputs={p.name:sha(p) for p in args.out.iterdir() if p.is_file()},
        schematic_only=args.analysis is None,pdf_fonttype=42)
    (args.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__': main()
