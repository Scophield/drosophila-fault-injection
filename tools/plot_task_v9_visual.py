"""Data-preserving visual revision: model, motion, paired outcomes and warnings.

Conceptual icons are explicitly schematic. All plotted observations/statistics
come from the complete source-bound v9 core, without new neural execution.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Arc, Rectangle
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INK, MUTED, LINE = '#243B49', '#677983', '#CED9DE'
P, R, CONTACT, PALE = '#337BA0', '#2A8276', '#BC5A3D', '#E6EEF1'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':7.5,'axes.labelsize':7.5,'axes.titlesize':8.5,'axes.titleweight':'bold',
    'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
    'axes.edgecolor':MUTED,'axes.labelcolor':INK,'text.color':INK,
    'xtick.color':MUTED,'ytick.color':MUTED,'pdf.fonttype':42,
    'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(fig,out,name):
    # Preserve the specified final print dimensions, rather than stretching a
    # cropped bounding box into a different font scale in the manuscript.
    for ext in ['pdf','svg','png']:
        fig.savefig(out/f'{name}.{ext}',dpi=600,facecolor='white')
    plt.close(fig)


def overview(out):
    fig=plt.figure(figsize=(3.5,2.90))
    ax=fig.add_axes([0,0,1,1],xlim=(0,350),ylim=(0,290));ax.axis('off')
    def txt(x,y,s,size=7,ha='center',weight='normal',color=INK):
        ax.text(x,y,s,ha=ha,va='center',fontsize=size,fontweight=weight,color=color)
    def arrow(a,b,color=P,lw=.9,**kw):
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=7,
            linewidth=lw,color=color,**kw))
    def title(y,letter,s):
        txt(7,y,letter,9,ha='left',weight='bold')
        txt(22,y,s,8,ha='left',weight='bold')
    title(280,'a','From visual drive to closed-loop action')
    # Conceptual retinal cue, recurrent circuit and motor interface.
    for rad,alpha in [(17,.25),(12,.5),(6,1)]:
        ax.add_patch(Circle((41,249),rad,fill=False,ec=P,lw=1,alpha=alpha))
    arrow((22,270),(30,262),lw=.8)
    txt(41,222,'LC4 / LPLC2',7,weight='bold')
    txt(41,211,'104 / 210 cells',6.6,color=MUTED)
    arrow((67,249),(112,249))
    for c in [148,181]:
        ax.add_patch(Ellipse((c,249),55,43,angle=8 if c==148 else -8,
            fc='#F1F5F6',ec=LINE,lw=.8))
    nodes=np.array([[127,249],[139,265],[143,239],[156,255],[164,238],
        [172,261],[180,246],[188,267],[200,250],[187,233]])
    edges=[(0,1),(0,2),(0,3),(1,3),(1,5),(2,3),(2,4),(3,5),(3,6),
        (4,6),(4,9),(5,6),(5,7),(6,8),(6,9),(7,8),(8,9)]
    for i,j in edges:
        ax.plot(nodes[[i,j],0],nodes[[i,j],1],color=LINE,lw=.7,zorder=1)
    ax.scatter(nodes[:,0],nodes[:,1],s=7,color=P,zorder=3)
    ax.plot(nodes[[3,5],0],nodes[[3,5],1],color=CONTACT,lw=1,ls='--',zorder=4)
    txt(207,273,'Row deletion',6.5,color=CONTACT)
    arrow((190,270),(166,259),color=CONTACT,lw=.7)
    txt(164,222,'Connectome LIF model',7,weight='bold')
    txt(164,211,'138,639 neurons',6.6,color=MUTED)
    arrow((211,249),(265,249));txt(238,263,'8 DN rates',6.6)
    # Fly icon is an abstract body, not a reconstructed animal morphology.
    ax.add_patch(Ellipse((291,248),8,23,fc=INK,ec='none'))
    ax.add_patch(Circle((291,263),3,fc=INK,ec='none'))
    for x,ang in [(283,-25),(299,25)]:
        ax.add_patch(Ellipse((x,250),10,20,angle=ang,fc='#E6EEF1',ec=P,lw=.7))
    arrow((308,248),(327,260))
    txt(292,222,'P / R + burst',7,weight='bold')
    txt(292,211,'Turn and actuation',6.6,color=MUTED)
    ax.plot([328,338,338,9,9,20],[240,240,199,199,249,249],color=MUTED,lw=.65)
    arrow((9,249),(20,249),color=MUTED,lw=.65)
    txt(174,190,'Motion changes the next retinal input',6.5,color=MUTED)
    title(174,'b','A task with explicit geometry and contact')
    a=np.array([61.,139.]);b=np.array([277.,153.])
    ax.plot([a[0],b[0]],[a[1],b[1]],ls=(0,(3,2)),lw=.8,color=MUTED)
    ax.add_patch(Ellipse(a,17,8,angle=27,fc=P,ec='none',zorder=5))
    for dy,ang in [(5,65),(-5,-15)]:
        ax.add_patch(Ellipse((57,139+dy),13,5,angle=ang,fc=PALE,ec=P,lw=.6,zorder=4))
    arrow(a,a+np.array([42,21]),lw=1)
    ax.add_patch(Arc(a,61,61,theta1=4,theta2=27,ec=P,lw=.8))
    txt(98,141,'φ',8,color=P)
    ax.add_patch(Circle(b,8,fc=CONTACT,ec='none'))
    ax.add_patch(Circle(b,15,fill=False,ec=CONTACT,lw=.6,ls=':'))
    arrow((264,150),(241,148),color=CONTACT)
    txt(172,157,'Separation d',6.8)
    txt(61,120,'Agent heading',6.5,color=P)
    txt(277,130,'Pursuer',6.5,color=CONTACT)
    txt(176,113,'Body bearing φ = world bearing − heading',6.4,color=MUTED)
    title(96,'c','Separate neural, actuator and task clocks')
    x=lambda t:20+310*t/1000
    ax.plot([x(0),x(1000)],[66,66],color=LINE,lw=1)
    for t,s in [(0,''),(100,'Cue'),(400,'Assess'),(1000,'Task')]:
        ax.plot([x(t)]*2,[62,70],color=P,lw=.8)
        txt(x(t),79,s,6.7);txt(x(t),56,f'{t:g}',6.3)
    ax.plot([x(200),x(450)],[36,36],ls=(0,(3,2)),color=MUTED,lw=.9)
    ax.add_patch(Rectangle((x(450),32),x(900)-x(450),8,fc=R,ec='none'))
    txt(x(200),43,r'$t_d$ = 200 ms',6.2)
    txt(x(325),22,'250 ms delay',6.5)
    txt(x(685),22,'450 ms burst',6.5,color=R)
    txt(175,7,'One paired seed: 2 bearings × 2 laws × 3 conditions',6.4)
    save(fig,out,'task_v9_overview')


def precontact_xy(record):
    phi=np.deg2rad(record['phi_deg'])
    times=np.r_[0,[r['t_end_ms'] for r in record['log']]]
    fly=np.vstack([[0,0],[r['fly'] for r in record['log']]])
    threat=np.vstack([[.25*np.cos(phi),.25*np.sin(phi)],
                      [r['target'] for r in record['log']]])
    contact=record['collision_ms']
    if contact is not None:
        ix=np.searchsorted(times,contact,side='right')
        if ix<len(times):
            # The selected example's contact frame contains no actuator event.
            # Never interpolate across a speed boundary or after contact.
            if len(record['log'][ix-1]['segments'])!=1:
                raise ValueError('example contact frame needs segmented interpolation')
            f=(contact-times[ix-1])/(times[ix]-times[ix-1])
            fly=np.vstack([fly[:ix],fly[ix-1]+f*(fly[ix]-fly[ix-1])])
            threat=np.vstack([threat[:ix],threat[ix-1]+f*(threat[ix]-threat[ix-1])])
        if not np.isclose(np.linalg.norm(fly[-1]-threat[-1]),.05,atol=1e-8):
            raise ValueError('drawn contact does not match the physical radius')
    return 1000*fly,1000*threat


def outcomes(out,summary,records,reg):
    lookup={(r['seed'],r['phi_deg'],r['mode'],r['fault']):r for r in records}
    seeds=reg['test_seeds'];modes=reg['modes'];phis=reg['phis']
    example=next(s for s in seeds if not lookup[s,-30.,'proportional','F2_50']['escaped'])
    fig=plt.figure(figsize=(7.16,2.86))
    ta=fig.add_axes([.07,.24,.245,.61])
    for mode,fault,color,label in [('proportional','healthy',MUTED,'Healthy (P)'),
        ('proportional','F2_50',P,'P, 50%'),('relay','F2_50',R,'R, 50%')]:
        rec=lookup[example,-30.,mode,fault];fly,threat=precontact_xy(rec)
        ta.plot(fly[:,0],fly[:,1],color=color,lw=1.4,label=label)
        ta.plot(threat[:,0],threat[:,1],color=color,lw=.75,ls='--',alpha=.7)
        ta.scatter(fly[0,0],fly[0,1],s=9,color=color,zorder=5)
        if rec['collision_ms'] is not None:
            ta.scatter(*fly[-1],marker='x',s=31,lw=1.2,color=CONTACT,zorder=6)
            ta.add_patch(Circle(fly[-1],50,fc='none',ec=CONTACT,lw=.7,ls=':'))
            ta.scatter(*threat[-1],s=10,fc=CONTACT,ec='none',zorder=5)
    ta.set(xlim=(-35,245),ylim=(-150,210),xlabel='x (mm)',ylabel='y (mm)',aspect='equal')
    ta.set_xticks([0,100,200]);ta.set_yticks([-100,0,100,200])
    ta.text(.02,.98,f'Seed {example}, −30°',transform=ta.transAxes,va='top',fontsize=7)
    handles=[Line2D([0],[0],color=c,lw=1.6,label=l) for c,l in
             [(MUTED,'Healthy (P)'),(P,'P, 50%'),(R,'R, 50%')]]
    fig.legend(handles=handles,loc='lower left',bbox_to_anchor=(.055,.035),
        ncol=3,frameon=False,handlelength=1.1,columnspacing=.9,fontsize=6.5)
    fig.text(.06,.02,'Solid: agent; dashed: pursuer; ×: first contact.',fontsize=6.3,color=MUTED)
    ma=fig.add_axes([.405,.24,.305,.61]);ma.spines[:].set_visible(False)
    ma.set(xlim=(-.5,11.5),ylim=(25.8,-5.1))
    cols=[(m,f,p) for m in modes for f in ['healthy','F2_25','F2_50'] for p in phis]
    for j,(m,f,p) in enumerate(cols):
        values=[lookup[s,p,m,f]['escaped'] for s in seeds]
        match=next(q for q in summary['counts'] if (q['mode'],q['fault'],q['phi_deg'])==(m,f,p))
        if sum(values)!=match['success']:raise ValueError('matrix and published counts disagree')
        for i,success in enumerate(values):
            ma.add_patch(Rectangle((j-.45,i-.45),.9,.9,
                fc=PALE if success else CONTACT,ec='white',lw=.15))
            if not success:ma.plot(j,i,'x',ms=2.8,mew=.6,color='white')
        ma.text(j,-1.1,'−' if p<0 else '+',ha='center',va='center',fontsize=6.8)
        ma.text(j,25.1,str(sum(values)),ha='center',va='center',fontsize=6.5,fontweight='bold')
    for offset,m,c in [(0,'Proportional',P),(6,'Relay',R)]:
        ma.text(offset+2.5,-4.2,m,ha='center',fontsize=7.6,fontweight='bold',color=c)
        for j,label in [(0,'H'),(2,'25%'),(4,'50%')]:
            ma.text(offset+j+.5,-2.6,label,ha='center',fontsize=6.8)
    ma.axvline(5.5,color='white',lw=3)
    ma.set_xticks([]);ma.set_yticks([0,5,10,15,20,23],labels=[str(seeds[i]) for i in [0,5,10,15,20,23]])
    ma.tick_params(axis='y',length=0,pad=3,labelsize=6.5)
    fig.text(.404,.108,'Column totals / 24; bearings − / +30°',fontsize=6.4,color=MUTED)
    fig.text(.404,.060,'Pale: no contact    ×: contact by 1 s',fontsize=6.4,color=MUTED)
    ea=fig.add_axes([.803,.32,.18,.45])
    ea.axvline(0,color=LINE,lw=.8,ls='--')
    for y,f,label in [(1.65,'F2_25','25%'),(.58,'F2_50','50%')]:
        q=summary['cluster_effects'][f+'_interaction'];v,lo,hi=[100*q[k] for k in ['estimate','low','high']]
        ea.plot([lo,hi],[y,y],color=R,lw=1.7)
        ea.vlines([lo,hi],y-.06,y+.06,color=R,lw=.8)
        ea.scatter(v,y,s=21,color=R,zorder=4)
        ea.text(-38,y-.28,f'{v:.1f} [{lo:.1f}, {hi:g}]',fontsize=6.4)
        p=summary['interaction_holm_p'][f]
        ea.text(-38,y-.51,'Holm p = '+('0.50' if p==.5 else '0.00195'),fontsize=6.4,color=MUTED)
    ea.set(xlim=(-40,5),ylim=(-.1,2.25),yticks=[1.65,.58],yticklabels=['25%','50%'],xticks=[-40,-20,0])
    ea.tick_params(axis='y',length=0,pad=3);ea.tick_params(axis='x',labelsize=6.5)
    ea.set_xlabel('Δ net loss (pp)\nRelay − proportional',fontsize=7)
    fig.text(.78,.08,'Healthy success: 96/96\nSafety reserves differ.',fontsize=6.5,color=MUTED)
    for x,s in [(.055,'a  Matched motion'),(.397,'b  Every test outcome'),(.77,'c  Paired loss contrast')]:
        fig.text(x,.945,s,fontsize=8.2,fontweight='bold')
    save(fig,out,'task_v9_outcomes')
    return example


def warnings(out,summary,metrics,thresholds):
    fig=plt.figure(figsize=(7.16,1.75))
    a=fig.add_axes([.12,.28,.31,.54]);b=fig.add_axes([.60,.28,.37,.54])
    rng=np.random.default_rng(20261023) # positional jitter only; no statistical resampling
    for y,collision,color in [(1,False,MUTED),(0,True,CONTACT)]:
        g=metrics[metrics.collision==collision]
        a.scatter(g.command_hz,y+rng.uniform(-.17,.17,len(g)),s=8 if collision else 4,
            color=color,alpha=.9 if collision else .35,marker='x' if collision else 'o',linewidths=.65)
    threshold=thresholds['command_lower_hz']
    a.axvline(threshold,color=P,lw=.9,ls='--')
    a.set(ylim=(-.48,1.48),yticks=[0,1],yticklabels=['Contact\n(n=13)','No contact\n(n=275)'],
        xlabel='Mean command rate, 100–400 ms (Hz)')
    a.text(threshold+.6,1.3,'Frozen cutoff',fontsize=6.5,color=P)
    a.text(.02,.06,'Only 2/13 later contacts flagged',transform=a.transAxes,fontsize=6.7,color=CONTACT)
    a.tick_params(axis='y',length=0,pad=3)
    labels=[('equal_duration_upper','Activity upper',MUTED,'s',(4,5)),
        ('transmission','Command',P,'o',(6,-3)),
        ('equal_duration_two_sided','Activity two-sided',P,'s',(4,6)),
        ('schedule_only','Actuator schedule',R,'^',(5,-13)),
        ('deadline','Held command',R,'D',(-25,-13))]
    for key,label,color,marker,offset in labels:
        q=summary['warning_scores'][key]['all'];x=100*q['false_positive_rate'];y=100*q['sensitivity']
        xi=100*np.asarray(q['false_positive_rate_interval']);yi=100*np.asarray(q['sensitivity_interval'])
        b.plot(xi,[y,y],color=color,lw=.8,alpha=.7);b.plot([x,x],yi,color=color,lw=.8,alpha=.7)
        b.scatter(x,y,s=19,color=color,marker=marker,zorder=4)
        b.annotate(label,(x,y),xytext=offset,textcoords='offset points',fontsize=6.5,color=color)
    b.set(xlim=(-1.5,45),ylim=(-7,113),xticks=[0,10,20,30,40],yticks=[0,50,100],
        xlabel='False alarms among 275 successes (%)',ylabel='Detection (%)')
    for x,s in [(.06,'a  Neural output is not the task endpoint'),(.54,'b  Detection versus false alarms')]:
        fig.text(x,.94,s,fontsize=8.2,fontweight='bold')
    fig.text(.12,.035,'288 paired episodes / 24 seed clusters; markers are observations.',fontsize=6.4,color=MUTED)
    fig.text(.60,.035,'Intervals: whole-seed bootstrap; zero misses ≠ zero risk.',fontsize=6.4,color=MUTED)
    save(fig,out,'task_v9_warnings')


def assessment(out,analysis):
    # Preserve the original quantitative SI panel bytes. This revision adds a
    # richer main warning plot rather than relabeling old statistics or moving
    # their uncertainty into a different estimand.
    import shutil
    old=ROOT/'audit/acceptance-v9/figures-v3'
    for ext in ['pdf','svg','png']:
        shutil.copyfile(old/f'task_v9_assessment.{ext}',out/f'task_v9_assessment.{ext}')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analysis',type=Path,default=ROOT/'audit/acceptance-v9/core-v2')
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();summary=json.loads((a.analysis/'summary.json').read_text())
    if not summary['complete'] or summary['records']!=288:raise ValueError('complete core required')
    regpath=ROOT/'runs/task-v9-frozen/registration-core.json';reg=json.loads(regpath.read_text())
    if sha(regpath)!=summary['registration_sha256']:raise ValueError('registration mismatch')
    records=[];inputs={p.as_posix():sha(p) for p in a.analysis.glob('*') if p.is_file()}
    for name,h in summary['raw_input_sha256'].items():
        p=ROOT/name
        if sha(p)!=h:raise ValueError(f'raw changed: {name}')
        records.append(json.loads(p.read_text()));inputs[name]=h
    calpath=ROOT/'runs/task-v9-frozen/calibration.json';cal=json.loads(calpath.read_text())
    inputs[calpath.relative_to(ROOT).as_posix()]=sha(calpath)
    a.out.mkdir(parents=True,exist_ok=False)
    overview(a.out);example=outcomes(a.out,summary,records,reg)
    warnings(a.out,summary,pd.read_csv(a.analysis/'metrics.csv'),reg['thresholds'])
    assessment(a.out,a.analysis)
    result=dict(script_sha256=sha(Path(__file__)),input_sha256=inputs,
        outputs={p.name:sha(p) for p in a.out.iterdir() if p.is_file()},
        example_seed=example,example_selection='first registered negative-bearing proportional F2_50 collision; descriptive, all outcomes shown alongside',
        changes='visual only; raw data, thresholds, masks, estimates, intervals and p-values unchanged',
        pdf_fonttype=42,schematic_only=False)
    (a.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['input_sha256','outputs']},indent=2))


if __name__=='__main__':main()
