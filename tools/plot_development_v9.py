"""Development/validation diagnostics, explicitly separate from independent tests."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    devpaths=sorted((ROOT/'runs/task-v9-development/episodes').glob('*.json'))
    valpaths=sorted((ROOT/'runs/task-v9-validation-B/episodes').glob('*.json'))
    dev=[json.loads(p.read_text()) for p in devpaths];val=[json.loads(p.read_text()) for p in valpaths]
    if len(dev)!=20 or len(val)!=32:raise ValueError('complete development and validation cohorts required')
    timing=json.loads((ROOT/'audit/acceptance-v9/baseline/check.json').read_text())
    old_delay=timing['delays'][0];old_duration=timing['completed_durations'][0]
    if len(timing['delays'])!=1 or len(timing['completed_durations'])!=1:
        raise ValueError('old timing requires a more detailed display')
    a.out.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'ps.fonttype':42,
        'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7})
    fig,axs=plt.subplots(1,3,figsize=(7.16,2.55),layout='constrained')
    points=[];angles=[-60,-30,0,30,60]
    for r in dev:
        rates=np.mean([q['smooth_rates'] for q in r['log'] if 200<=q['t_end_ms']<=400],axis=0)
        points.append(dict(role='development',seed=r['seed'],phi_deg=r['phi_deg'],mean_command_hz=float(rates.mean()),
            dnp04_left_hz=float(rates[4]),dnp04_right_hz=float(rates[5])))
    for j,phi in enumerate(angles):
        group=[r for r in points if r['phi_deg']==phi]
        for offset,name,color,marker in [(-.13,'dnp04_left_hz','#34739b','o'),(.13,'dnp04_right_hz','#c97730','^')]:
            values=[r[name] for r in group]
            axs[0].scatter(j+offset+np.linspace(-.04,.04,4),values,s=10,color=color,marker=marker,
                label=('DNp04 L' if 'left' in name else 'DNp04 R') if j==0 else None)
            axs[0].plot([j+offset-.09,j+offset+.09],[np.median(values)]*2,color='black',lw=.8)
    axs[0].set(xticks=range(5),xticklabels=[str(p) for p in angles],xlabel='Bearing (deg)',ylabel='Smoothed rate (Hz)',ylim=(0,105),yticks=[0,25,50,75,100])
    axs[0].set_title('Passive development',fontsize=9);axs[0].legend(loc='upper right',fontsize=7.5,frameon=False)
    groups=[('proportional',-30),('proportional',30),('relay',-30),('relay',30)]
    validation=[]
    for j,(mode,phi) in enumerate(groups):
        values=[]
        for r in val:
            if (r['mode'],r['phi_deg'])!=(mode,phi):continue
            first=next(seg for q in r['log'] for seg in q['segments'] if seg['burst'])
            duration=sum(seg['end_ms']-seg['start_ms'] for q in r['log'] for seg in q['segments'] if seg['burst'])
            values.append(r['trigger_ms'])
            validation.append(dict(role='validation',seed=r['seed'],mode=mode,phi_deg=phi,trigger_ms=r['trigger_ms'],
                first_burst_ms=first['start_ms'],observed_burst_ms=duration,escaped=r['escaped']))
        axs[1].scatter(j+np.linspace(-.12,.12,len(values)),values,color='#34739b' if phi<0 else '#c97730',s=12,marker='o' if phi<0 else '^')
        axs[1].plot([j-.15,j+.15],[np.median(values)]*2,color='black',lw=1)
    axs[1].set(xticks=range(4),xticklabels=['P\n-30','P\n+30','R\n-30','R\n+30'],ylabel='Neural decision time (ms)',xlabel='Law / bearing',ylim=(100,None))
    axs[1].set_title('Healthy validation (8/8 each)',fontsize=9)
    new_delay=sorted({r['first_burst_ms']-r['trigger_ms'] for r in validation})
    new_duration=sorted({r['observed_burst_ms'] for r in validation})
    if len(new_delay)!=1 or len(new_duration)!=1:raise ValueError('validation timing is not uniform')
    axs[2].broken_barh([(old_delay,old_duration)],(1.05,.45),facecolors='#999999')
    axs[2].broken_barh([(new_delay[0],new_duration[0])],(.15,.45),facecolors='#34739b')
    axs[2].axvline(250,color='black',ls='--',lw=.7);axs[2].axvline(700,color='black',ls='--',lw=.7)
    axs[2].set(xlim=(200,730),ylim=(0,1.9),yticks=[.375,1.275],yticklabels=['Exact events','Old frame gate'],
        xticks=[250,500,700],xlabel='Time after decision (ms)')
    axs[2].text(old_delay+old_duration/2,1.27,f'{old_duration:g} ms',ha='center',va='center',color='white',fontsize=8)
    axs[2].text(new_delay[0]+new_duration[0]/2,.375,f'{new_duration[0]:g} ms',ha='center',va='center',color='white',fontsize=8)
    axs[2].set_title('Realized actuator intervals',fontsize=9)
    for letter,ax in zip('abc',axs):ax.text(-.15,1.06,letter,fontweight='bold',transform=ax.transAxes)
    for ext in ['pdf','svg','png']:fig.savefig(a.out/f'development_v9.{ext}',bbox_inches='tight',dpi=220,pad_inches=.04)
    plt.close(fig)
    for name,rows in [('development.csv',points),('validation.csv',validation)]:
        with (a.out/name).open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    manifest=dict(role='development/validation only, not independent test evidence',script_sha256=sha(Path(__file__)),
        input_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in devpaths+valpaths},
        old_timing_source='audit/acceptance-v9/baseline/check.json',
        old_timing_sha256=sha(ROOT/'audit/acceptance-v9/baseline/check.json'),
        outputs={p.name:sha(p) for p in a.out.iterdir() if p.is_file()})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
