"""Replot verified V9 observations with consistent V10 warning terminology.

No controller, threshold, classification, estimate or interval is changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
INK,MUTED,LINE='#243B49','#677983','#CED9DE'
BLUE,GREEN,ORANGE='#337BA0','#2A8276','#BC5A3D'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':7.4,'axes.labelsize':7.3,'xtick.labelsize':6.7,'ytick.labelsize':6.7,
    'text.color':INK,'axes.labelcolor':INK,'axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':.65,'legend.frameon':False,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(fig,out,name):
    for ext in ['pdf','svg','png']:fig.savefig(out/(name+'.'+ext),dpi=600,facecolor='white')
    plt.close(fig)


def warning_plot(out,d,metrics,thresholds):
    fig=plt.figure(figsize=(7.16,2.50))
    a=fig.add_axes([.12,.32,.30,.48]);b=fig.add_axes([.69,.32,.28,.48])
    rng=np.random.default_rng(20261023) # positional jitter only
    for y,collision,color in [(1,False,MUTED),(0,True,ORANGE)]:
        g=metrics[metrics.collision==collision]
        a.scatter(g.command_hz,y+rng.uniform(-.17,.17,len(g)),s=8 if collision else 4,
            color=color,alpha=.9 if collision else .35,marker='x' if collision else 'o',linewidths=.65)
    threshold=thresholds['command_lower_hz'];a.axvline(threshold,color=BLUE,lw=.9,ls='--')
    a.set(ylim=(-.48,1.48),yticks=[0,1],yticklabels=['Contact\n(n=13)','No contact\n(n=275)'],
        xlabel='Mean command rate, 100–400 ms (Hz)')
    a.text(threshold+.6,1.3,'Frozen cutoff',fontsize=6.4,color=BLUE)
    a.text(.02,.06,'Only 2/13 contacts flagged',transform=a.transAxes,fontsize=6.5,color=ORANGE)
    a.tick_params(axis='y',length=0,pad=3)
    names=['equal_duration_upper','transmission','equal_duration_two_sided','schedule_only','deadline']
    labels=['Activity upper','Command criterion','Activity two-sided',
        'Actuator-schedule forecast\n(exact state)','Held-command forecast\n(exact state)']
    for i,name in enumerate(names):
        q=d['warning_scores'][name]['all']
        for offset,metric,color,marker in [(.12,'sensitivity',ORANGE,'o'),(-.12,'false_positive_rate',BLUE,'s')]:
            y=4-i+offset;value=100*q[metric];ci=100*np.array(q[metric+'_interval'])
            b.plot(ci,[y,y],color=color,lw=.9);b.scatter(value,y,color=color,marker=marker,s=15,zorder=3)
    b.set(yticks=range(5),yticklabels=labels[::-1],ylim=(-.5,4.5),xlim=(-4,104),xticks=[0,50,100],xlabel='Rate (%)')
    b.tick_params(axis='y',length=0,pad=5)
    b.scatter([],[],color=ORANGE,s=15,label='Detection / 13 contacts')
    b.scatter([],[],color=BLUE,marker='s',s=15,label='False alarms / 275 successes')
    b.legend(loc='upper right',bbox_to_anchor=(1.06,-.24),fontsize=6.4,handletextpad=.3)
    fig.text(.055,.94,'a  Neural output versus task outcome',fontsize=8.1,fontweight='bold')
    fig.text(.48,.94,'b  Frozen warning operating points',fontsize=8.1,fontweight='bold')
    fig.text(.12,.035,'288 paired episodes / 24 seed clusters; all observations shown.',fontsize=6.3,color=MUTED)
    fig.text(.48,.035,'Intervals: whole-seed bootstrap; zero misses ≠ zero risk.',fontsize=6.3,color=MUTED)
    save(fig,out,'task_v10_warnings')


def assessment_plot(out,d,pairs):
    fig=plt.figure(figsize=(7.16,2.55));a=fig.add_axes([.09,.29,.34,.52]);b=fig.add_axes([.59,.29,.38,.52])
    for j,mode in enumerate(['proportional','relay']):
        g=pairs[(pairs['mode']==mode)&(pairs['fault']=='F2_50')]
        for _,r in g.iterrows():a.plot([j*2,j*2+1],[r.stop_ratio,r.common_ratio],color=MUTED,alpha=.28,lw=.6)
        a.scatter([j*2,j*2+1],[g.stop_ratio.median(),g.common_ratio.median()],color=INK,s=18,zorder=3)
    a.set(xticks=range(4),xticklabels=['Own stop','Common','Own stop','Common'],ylabel='Fault / paired healthy spikes')
    a.text(.19,-.33,'Proportional',transform=a.transAxes,ha='center',fontsize=7)
    a.text(.80,-.33,'Relay',transform=a.transAxes,ha='center',fontsize=7)
    names=['transmission','equal_duration_two_sided','schedule_only','deadline']
    labels=['Command\ncriterion','Activity\ntwo-sided','Actuator-schedule\nforecast','Held-command\nforecast']
    for offset,metric,color,marker in [(-.10,'sensitivity',ORANGE,'o'),(.10,'specificity',BLUE,'s')]:
        for i,name in enumerate(names):
            q=d['warning_scores'][name]['all'];value=q[metric];low,high=q[metric+'_interval']
            b.plot([i+offset,i+offset],[low,high],color=color,lw=.9)
            b.scatter(i+offset,value,marker=marker,s=16,color=color)
        b.scatter([],[],color=color,marker=marker,s=16,label=metric.capitalize())
    b.set(xticks=range(4),xticklabels=labels,ylim=(-.04,1.08),yticks=[0,.5,1],ylabel='Task classification rate')
    b.legend(loc='lower left',bbox_to_anchor=(-.02,1.01),ncol=2,fontsize=6.5)
    b.text(.52,-.37,'Both forecasts use exact state.',transform=b.transAxes,ha='center',fontsize=6.5,color=MUTED)
    fig.text(.05,.94,'a  Same records: 50% deletion exposure',fontsize=8.1,fontweight='bold')
    fig.text(.55,.94,'b  Frozen secondary warning scores',fontsize=8.1,fontweight='bold')
    diff=np.abs(pairs.stop_ratio-pairs.common_ratio).max()
    fig.text(.09,.035,f'Max paired |own stop − common| = {diff:.5f}; black markers: medians.',fontsize=6.3,color=MUTED)
    fig.text(.59,.035,'95% whole-seed CIs; sparse/zero-event caveats apply.',fontsize=6.3,color=MUTED)
    save(fig,out,'task_v9_assessment')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--analysis',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=json.loads((a.analysis/'summary.json').read_text());assert d['complete'] and d['records']==288
    regpath=Path('runs/task-v9-frozen/registration-core.json');reg=json.loads(regpath.read_text())
    assert sha(regpath)==d['registration_sha256']
    inputs={p.as_posix():sha(p) for p in a.analysis.glob('*') if p.is_file()}
    for name,h in d['raw_input_sha256'].items():
        p=Path(name);assert sha(p)==h;inputs[p.as_posix()]=h
    inputs[regpath.as_posix()]=sha(regpath);inputs[Path(__file__).resolve().relative_to(ROOT).as_posix()]=sha(__file__)
    a.out.mkdir(parents=True,exist_ok=False)
    warning_plot(a.out,d,pd.read_csv(a.analysis/'metrics.csv'),reg['thresholds'])
    assessment_plot(a.out,d,pd.read_csv(a.analysis/'pairs.csv'))
    (a.out/'manifest.json').write_text(json.dumps(dict(input_sha256=inputs,
        outputs={p.name:sha(p) for p in a.out.iterdir()},pdf_fonttype=42,
        scope='Same verified baseline observations, classifications and whole-seed intervals; terminology/layout only'),indent=2)+'\n')


if __name__=='__main__':main()
