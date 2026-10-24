"""Primary conditional task loss and descriptive nominal reserve/action.

Requires complete independently checked matrices. The plot does not test RF
causality, pool maps, or turn secondary interactions into primary endpoints.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from aggregate_transfer_v10 import descriptive,primary

ROOT=Path(__file__).resolve().parents[1]
INK,MUTED,LINE='#243B49','#677983','#CED9DE'
P,R='#337BA0','#2A8276'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--transfer',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();inputs={}
    def read(p):
        inputs[p.resolve().relative_to(ROOT).as_posix()]=sha(p);return json.loads(p.read_text())
    def records(summary):
        rows=[]
        for name,h in summary['raw_input_sha256'].items():
            p=ROOT/name
            if sha(p)!=h:raise ValueError('raw source changed: '+name)
            inputs[p.relative_to(ROOT).as_posix()]=h;rows.append(json.loads(p.read_text()))
        return rows
    old=read(a.baseline/'summary.json');new=read(a.transfer/'summary.json')
    assert old['complete'] and old['records']==288 and new['complete'] and len(new['maps'])==2
    baseline_raw=records(old);reg=read(ROOT/'runs/task-v9-frozen/registration-core.json')
    effects={};nominal={'RF-0':descriptive(baseline_raw)};sizes={'RF-0':24}
    for row in primary(baseline_raw,reg):effects['RF-0',row['fault'],row['mode']]=row['estimands']['loss']
    for q in new['maps']:
        tag='RF-'+q['map_id'];folder=a.transfer/('map-'+q['map_id'])
        summary=read(folder/'analysis/summary.json');replay=read(folder/'replay/replay.json')
        arithmetic=read(folder/'numbers/check.json');evidence=read(folder/'evidence.json')
        if not all(x['passed'] for x in [replay,arithmetic,evidence]):raise ValueError('unchecked RF matrix')
        if summary['records']!=144:raise ValueError('partial RF matrix')
        raw=records(summary)
        if descriptive(raw)!=q['healthy_descriptive']:raise ValueError('descriptive binding')
        nominal[tag]=q['healthy_descriptive'];sizes[tag]=q['seed_clusters']
        for row in q['primary']:
            assert row['estimands']['loss']['role']=='registered_primary'
            effects[tag,row['fault'],row['mode']]=row['estimands']['loss']
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':7.2,'axes.labelsize':7,'xtick.labelsize':6.5,'ytick.labelsize':6.6,
        'text.color':INK,'axes.labelcolor':INK,'axes.spines.top':False,'axes.spines.right':False,
        'axes.linewidth':.65,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(7.16,2.35));forest=fig.add_axes([.16,.27,.38,.54])
    reserve=fig.add_axes([.66,.27,.13,.54]);action=fig.add_axes([.85,.27,.13,.54])
    tags=['RF-0','RF-A','RF-B'];ticks=[];labels=[];limits=[]
    for group,tag in enumerate(tags):
        center=5-2*group
        for dose,offset in [('F2_25',.35),('F2_50',-.35)]:
            y=center+offset;ticks.append(y);labels.append(f'{tag}, {dose[3:]}%')
            for mode,shift,color in [('proportional',.10,P),('relay',-.10,R)]:
                q=effects[tag,dose,mode];low,high=100*np.array(q['ci95']);point=100*q['estimate']
                limits.extend([low,high]);forest.plot([low,high],[y+shift,y+shift],color=color,lw=1)
                forest.scatter(point,y+shift,color=color,s=16,zorder=3)
        for ax,field in [(reserve,'clearance_to_first_contact_or_horizon_mm'),(action,'abs_heading_400_deg')]:
            values={q['mode']:{(r['seed'],r['phi_deg']):r[field] for r in q['rows']} for q in nominal[tag]}
            keys=sorted(values['proportional']);assert set(keys)==set(values['relay'])
            rng=np.random.default_rng(20261023+group);jitter=rng.uniform(-.055,.055,len(keys))
            for j,k in enumerate(keys):
                ax.plot([values['proportional'][k],values['relay'][k]],
                    [center+.14+jitter[j],center-.14+jitter[j]],color=LINE,lw=.35,zorder=0)
            for mode,shift,color in [('proportional',.14,P),('relay',-.14,R)]:
                v=[values[mode][k] for k in keys]
                ax.scatter(v,center+shift+jitter,s=4,color=color,alpha=.30,zorder=1)
                ax.scatter(np.median(v),center+shift,s=22,color=color,marker='|',linewidths=1.6,zorder=4)
    low=min(-3.,min(limits)-4);high=max(10.,max(limits)+5)
    forest.axvline(0,color=MUTED,lw=.65,ls=':');forest.set(yticks=ticks,yticklabels=labels,xlim=(low,high),ylim=(.2,5.8),
        xlabel='Paired scenarios with task loss (%)')
    forest.tick_params(axis='y',length=0,pad=4)
    for ax in [reserve,action]:ax.set(yticks=[5,3,1],yticklabels=tags,ylim=(.2,5.8));ax.tick_params(axis='y',length=0,pad=3)
    reserve.set(xlabel='Clearance\n(mm)');action.set(xlabel='|Heading at 400 ms|\n(deg)',xlim=(-4,104),xticks=[0,50,100])
    for ax in [forest,reserve,action]:
        for y in [2,4]:ax.axhline(y,color=LINE,lw=.45,zorder=0)
    forest.scatter([],[],color=P,s=16,label='Proportional');forest.scatter([],[],color=R,s=16,label='Relay')
    forest.legend(loc='lower left',bbox_to_anchor=(-.01,1.01),ncol=2,frameon=False,fontsize=6.5,handletextpad=.3,columnspacing=.8)
    fig.text(.025,.94,'a  Primary paired task loss',fontsize=8.1,fontweight='bold')
    fig.text(.60,.94,'b  Healthy reserve',fontsize=8.1,fontweight='bold')
    fig.text(.81,.94,'c  Healthy action',fontsize=8.1,fontweight='bold')
    fig.text(.16,.035,'Pointwise 95% seed CIs; n=24 / 12 / 12. Zero-event caveats apply.',fontsize=6.2,color=MUTED)
    fig.text(.65,.035,'Paired observations; bars: medians.',fontsize=6.2,color=MUTED)
    a.out.mkdir(parents=True,exist_ok=False)
    for ext in ['pdf','svg','png']:fig.savefig(a.out/('task_v10_transfer.'+ext),dpi=600,facecolor='white')
    plt.close(fig)
    inputs[Path(__file__).resolve().relative_to(ROOT).as_posix()]=sha(__file__)
    inputs['tools/aggregate_transfer_v10.py']=sha(ROOT/'tools/aggregate_transfer_v10.py')
    (a.out/'manifest.json').write_text(json.dumps(dict(input_sha256=inputs,
        outputs={p.name:sha(p) for p in a.out.iterdir()},primary_estimand='healthy-to-fault loss; gains reported separately; derived net loss is not relabelled primary',
        independent_clusters=sizes,secondary_interactions_in_supplement=True,pdf_fonttype=42,
        scope='Map-conditional estimates with descriptive unmatched healthy reserve/actions; no pooled inference, map causal attribution, hardware benefit or zero-risk certification'),indent=2)+'\n')


if __name__=='__main__':main()
