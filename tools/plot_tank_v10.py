"""Show real standalone tank records and the declared non-grid actuation delay.

Illustrative first-seed traces, not selected for failure/success. Every supplied
tank record is independently checked before plotting; no neural comparisons.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_v10.contract import audit
from evidence_v10.tank import TankAdapter


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();paths=sorted(a.root.glob('*.json'));rows=[json.loads(p.read_text()) for p in paths]
    adapter=TankAdapter();issues=audit([adapter.normalize(r) for r in rows],adapter.spec,adapter)
    if issues:raise ValueError('tank evidence failed: '+repr(issues[:4]))
    assert len(rows)==96
    lookup={(r['seed'],r['condition'],r['law'],r['fault']):r for r in rows}
    healthy=lookup[9000,'high','proportional','healthy'];faulty=lookup[9000,'high','proportional','F2_50']
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axs=plt.subplots(1,2,figsize=(7.16,2.35));fig.subplots_adjust(left=.08,right=.98,bottom=.24,top=.82,wspace=.34)
    blue,orange,gray='#337BA0','#BC5A3D','#677983'
    all_levels=[]
    for r,label,color,style in [(healthy,'Healthy',blue,'-'),(faulty,'Deletion f=0.50',orange,'--')]:
        times=[0.]+[q['end_s'] for q in r['log']];levels=[.5]+[q['level'] for q in r['log']]
        all_levels.extend(levels)
        axs[0].plot(times,levels,color=color,ls=style,lw=1.2,label=label)
    padding=.12*(max(all_levels)-min(all_levels))
    axs[0].axhline(.5,color=gray,lw=.6,ls=':');axs[0].set(xlim=(0,4),ylim=(min(all_levels)-padding,max(all_levels)+padding),xlabel='Time (s)',ylabel='Tank level (normalized)')
    axs[0].legend(loc='lower right',bbox_to_anchor=(1,.16),fontsize=6.5,frameon=False)
    axs[0].text(0,-.40,'Declared safe interval: [0.2, 0.8]; all 96 example tasks safe.',transform=axs[0].transAxes,fontsize=6.5,color=gray)
    q=faulty['log'];decisions=[r['decision_s'] for r in q];requested=[r['requested'] for r in q]
    axs[1].step([0.]+decisions,[.18]+requested,where='post',color=orange,ls='--',lw=1,label='Requested at frame end')
    segments=[s for r in q for s in r['segments']]
    axs[1].step([s['start_s'] for s in segments]+[segments[-1]['end_s']],
        [s['outflow'] for s in segments]+[segments[-1]['outflow']],where='post',color=blue,lw=1.2,label='Actually applied')
    for x in np.arange(0,1.01,.1):axs[1].axvline(x,color='#CED9DE',lw=.5,zorder=0)
    changed=next(r for r in q if abs(r['requested']-.18)>1e-12)
    td,ta=changed['decision_s'],changed['available_s']
    axs[1].annotate('',xy=(ta,.255),xytext=(td,.255),arrowprops=dict(arrowstyle='<->',color=gray,lw=.7))
    axs[1].text((td+ta)/2,.259,'150 ms',ha='center',fontsize=6.7,color=gray)
    axs[1].set(xlim=(0,.8),ylim=(.17,.28),xlabel='Time (s), first 0.8 s',ylabel='Outflow (normalized / s)')
    axs[1].legend(loc='upper left',fontsize=6.4,frameon=False)
    axs[1].text(0,-.40,f'100-ms grid; first changed command {td:.2f} s → {ta:.2f} s.',transform=axs[1].transAxes,fontsize=6.5,color=gray)
    fig.text(.08,.93,'a  Distinct plant, same checked interface',fontsize=8.2,fontweight='bold')
    fig.text(.59,.93,'b  Exact delayed actuation',fontsize=8.2,fontweight='bold')
    a.out.mkdir(parents=True,exist_ok=False)
    for ext in ['pdf','svg','png']:fig.savefig(a.out/('tank_v10.'+ext),dpi=600)
    plt.close(fig)
    manifest=dict(checked_records=96,selected_seed=9000,condition='high',law='proportional',
        selection='lexically first registered seed, illustrative high-inflow pair, not an outcome-selected example',
        input_sha256={p.as_posix():sha(p) for p in paths},script_sha256=sha(__file__),
        outputs={p.name:sha(p) for p in a.out.iterdir()},pdf_fonttype=42,
        scope='Independent small adoption example; no neural result or resilience superiority claim')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
