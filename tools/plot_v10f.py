"""Final V10 quantitative evidence. Never touch or regenerate locked Blender art.

Read complete checked cohorts and export source CSVs, PDFs, SVGs and previews.
The three-figure alternative combines the two NEW single-column PDFs at their
original sizes; the approved overview is referenced unchanged by both layouts.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pymupdf

from aggregate_transfer_v10 import primary, descriptive

ROOT = Path(__file__).resolve().parents[1]
BLUE, GREEN, ORANGE, PURPLE = '#337BA0', '#2A8276', '#BC5A3D', '#7763B1'
INK, GRAY, LINE = '#243B49', '#677983', '#D6DFE3'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def style():
    plt.rcParams.update({'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans'], 'font.size': 8,
        'axes.labelsize': 8, 'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.linewidth': .7, 'lines.linewidth': 1.05,
        'text.color': INK, 'axes.labelcolor': INK, 'legend.frameon': False,
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none'})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--reuse-only', action='store_true', help='Export only Fig.2, preserving other approved figures')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    inputs = {Path(__file__).resolve().relative_to(ROOT).as_posix(): sha(__file__)}

    def read(name):
        p = ROOT/name
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
        return json.loads(p.read_text())

    def raw(summary):
        rows = []
        for name, h in summary['raw_input_sha256'].items():
            p = ROOT/name
            if sha(p) != h:
                raise ValueError('Changed record: '+name)
            inputs[p.relative_to(ROOT).as_posix()] = h
            rows.append(json.loads(p.read_text()))
        return rows

    def table(name, rows):
        with (a.out/name).open('x', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)

    def save(fig, name):
        for ext in ['pdf', 'svg', 'png']:
            fig.savefig(a.out/(name+'.'+ext), dpi=600, facecolor='white')
        plt.close(fig)

    core = read('audit/acceptance-v9/core-v2/summary.json')
    transfer = read('audit/v10/transfer-01/summary.json')
    if not core['complete'] or core['records'] != 288 or not transfer['complete']:
        raise ValueError('Complete checked cohorts required')
    for name in ['independent-score-check.json', 'rf-input-binding.json']:
        if not read('audit/v10/transfer-01/'+name)['passed']:
            raise ValueError(name)
    summaries, records, ps = {'RF-0': core}, {'RF-0': raw(core)}, {}
    reg = read('runs/task-v9-frozen/registration-core.json')
    ps['RF-0'] = primary(records['RF-0'], reg)
    for q in transfer['maps']:
        tag = 'RF-'+q['map_id']; folder = 'audit/v10/transfer-01/map-'+q['map_id']
        s = read(folder+'/analysis/summary.json')
        if s['records'] != 144 or not s['complete']:
            raise ValueError('Partial RF matrix')
        for name in ['numbers/check.json', 'replay/replay.json', 'evidence.json']:
            if not read(folder+'/'+name)['passed']:
                raise ValueError('RF check failed')
        summaries[tag], records[tag], ps[tag] = s, raw(s), q['primary']
    tags = ['RF-0', 'RF-A', 'RF-B']
    sizes = {'RF-0': 24, 'RF-A': 12, 'RF-B': 12}
    nominal = {tag: descriptive(records[tag]) for tag in tags}
    assert all(not q['gains'] for s in summaries.values() for q in s['counts'])

    evidence = read('audit/v10/evidence-05/check.json')
    history = read('audit/v10/legacy-timing-01/check.json')
    if not evidence['passed'] or not evidence['untrusted_neural_witness']['trace_check_passed']:
        raise ValueError('Canonical evidence/witness check failed')
    cases, layers = [], {}
    for adapter, cc in evidence['corruption_cases'].items():
        generic = native = 0
        for case in cc:
            common = any(not code.startswith('adapter-') for code in case['issue_codes'])
            generic += common; native += not common
            cases.append(dict(adapter=adapter, error=case['error'],
                detected=case['detected'], layer='common' if common else 'native-only',
                issue_codes=';'.join(case['issue_codes'])))
        if (generic, native) != (11, 3) or not all(c['detected'] for c in cc):
            raise ValueError('Unexpected error-layer counts')
        layers[adapter] = (generic, native)
    table('checker_source.csv', cases)

    # Same registered first seed/condition as the earlier tank figure, with no
    # outcome-based selection. Plot existing objects, never generate new trials.
    tank = []
    for p in sorted((ROOT/'audit/v10/evidence-05/tank-raw').glob('*.json')):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
        tank.append(json.loads(p.read_text()))
    assert len(tank) == 96
    lookup = {(r['seed'],r['condition'],r['law'],r['fault']):r for r in tank}
    h = lookup[9000, 'high', 'proportional', 'healthy']
    f = lookup[9000, 'high', 'proportional', 'F2_50']
    tank_csv = []
    for row in [h, f]:
        for q in row['log']:
            tank_csv.append(dict(seed=row['seed'], condition=row['condition'],
                law=row['law'], fault=row['fault'], end_s=q['end_s'], level=q['level'],
                requested=q['requested'], decision_s=q['decision_s'], available_s=q['available_s']))
    table('tank_source.csv', tank_csv)
    style()
    fig = plt.figure(figsize=(3.5, 2.72))
    level = fig.add_axes([.15, .56, .34, .29])
    delay = fig.add_axes([.66, .56, .32, .29])
    bars = fig.add_axes([.15, .13, .82, .19])
    for row, color, ls, label in [(h, BLUE, '-', 'Healthy'), (f, ORANGE, '--', '50% deletion')]:
        level.plot([0]+[q['end_s'] for q in row['log']], [.5]+[q['level'] for q in row['log']], color=color, ls=ls, label=label)
    level.set(xlim=(0,4), xticks=[0,2,4], ylim=(.49,.59), yticks=[.50,.55], xlabel='Time (s)', ylabel='Tank level')
    fig.text(.06,.93,'a  Tank response',weight='bold',fontsize=8.5)
    fig.text(.58,.93,'b  Delayed outflow',weight='bold',fontsize=8.5)
    seg = [s for q in f['log'] for s in q['segments']]
    delay.step([0]+[q['decision_s'] for q in f['log']], [.18]+[q['requested'] for q in f['log']], where='post',color=ORANGE,ls='--',label='Requested')
    delay.step([s['start_s'] for s in seg]+[seg[-1]['end_s']], [s['outflow'] for s in seg]+[seg[-1]['outflow']],where='post',color=BLUE,label='Applied')
    td = next(q for q in f['log'] if abs(q['requested']-.18)>1e-12)
    delay.annotate('',xy=(td['available_s'],.264),xytext=(td['decision_s'],.264),arrowprops=dict(arrowstyle='<->',color=GRAY,lw=.75))
    delay.text((td['available_s']+td['decision_s'])/2,.269,'150 ms',ha='center',fontsize=7.5)
    for t in [.4,.5,.6,.7,.8]:delay.axvline(t,lw=.4,color=LINE,zorder=0)
    delay.set(xlim=(.4,.85),ylim=(.17,.29),xticks=[.4,.6,.8],yticks=[.18,.24],xlabel='Time (s)',ylabel='Outflow (1/s)')
    # Each panel has its own semantic key; colors retain the original curves.
    fig.text(.15,.385,'Healthy',color=BLUE,fontsize=7.5)
    fig.text(.32,.385,'50% deletion',color=ORANGE,fontsize=7.5)
    fig.text(.66,.385,'Applied',color=BLUE,fontsize=7.5)
    fig.text(.82,.385,'Requested',color=ORANGE,fontsize=7.5)
    for y, adapter in [(1,'fly'),(0,'tank')]:
        g,n = layers[adapter]; bars.barh(y,g,color=BLUE,height=.52)
        bars.barh(y,n,left=g,color=PURPLE,height=.52)
        bars.text(g/2,y,str(g),ha='center',va='center',color='white',fontsize=8)
        bars.text(g+n/2,y,str(n),ha='center',va='center',color='white',fontsize=8)
    bars.set(yticks=[0,1],yticklabels=['Tank','Fly'],xlim=(0,14),xticks=[])
    bars.tick_params(axis='y',length=0)
    for spine in bars.spines.values():spine.set_visible(False)
    fig.text(.06,.335,'c  Predefined challenges detected',weight='bold',fontsize=8.5)
    fig.legend(handles=[Patch(color=BLUE,label='Common checker'),Patch(color=PURPLE,label='Native replay only')],loc='lower center',ncol=2,fontsize=7.5,bbox_to_anchor=(.53,.005),columnspacing=.9,handlelength=1.)
    save(fig,'v10f_reuse')
    if a.reuse_only:
        (a.out/'reuse-check.json').write_text(json.dumps(dict(source_sha256=inputs,
            figure='v10f_reuse',only_panel_legends_changed=True,new_simulations=False),indent=2)+'\n')
        return

    # Primary task loss, prespecified SECONDARY contrast, descriptive reserve.
    effects = {(tag,q['fault'],q['mode']):q['estimands']['loss'] for tag in tags for q in ps[tag]}
    outrows = []
    fig = plt.figure(figsize=(7.16,2.22))
    loss = fig.add_axes([.10,.27,.32,.50])
    contrast = fig.add_axes([.55,.27,.20,.50])
    reserve = fig.add_axes([.85,.27,.13,.50])
    tick, lab = [], []
    for idx,tag in enumerate(tags):
        c = 5-2*idx
        for dose,off in [('F2_25',.35),('F2_50',-.35)]:
            yy=c+off;tick.append(yy);lab.append(f'{tag}, {dose[3:]}%')
            for mode,shift,color,marker in [('proportional',.09,BLUE,'o'),('relay',-.09,GREEN,'s')]:
                q=effects[tag,dose,mode];lo,hi=100*np.array(q['ci95']);point=100*q['estimate']
                loss.plot([lo,hi],[yy+shift]*2,color=color,lw=1)
                loss.scatter(point,yy+shift,color=color,marker=marker,s=14,zorder=3)
                cc=[r for r in summaries[tag]['counts'] if r['mode']==mode and r['fault']==dose]
                fail=sum(r['losses'] for r in cc);den=sum(r['n'] for r in cc)
                outrows.append(dict(map=tag,clusters=sizes[tag],law=mode,dose=dose,losses=fail,paired_scenarios=den,estimate_percent=point,ci_low_percent=lo,ci_high_percent=hi))
            # Failures/paired-scenarios are the actual primary-loss counts.
            both=[q for q in outrows if q['map']==tag and q['dose']==dose]
            loss.text(1.22,yy,f"{both[0]['losses']}/{both[0]['paired_scenarios']} | {both[1]['losses']}/{both[1]['paired_scenarios']}",transform=loss.get_yaxis_transform(),ha='right',va='center',fontsize=7.5)
        q=summaries[tag]['cluster_effects']['F2_50_interaction']
        contrast.plot([100*q['low'],100*q['high']],[c]*2,color=INK,lw=1.15)
        contrast.scatter(100*q['estimate'],c,color=INK,s=18,zorder=3)
        pv=core['interaction_holm_p']['F2_50'] if tag=='RF-0' else transfer['secondary_interaction_holm_p'][tag[-1]+'/F2_50']
        contrast.text(3,c,f'{100*q["estimate"]:.1f}',fontsize=7.5,va='center',ha='left')
        # The exact p/CI and all3effect roles are exported to the source table.
        outrows.append(dict(map=tag,clusters=sizes[tag],law='R minus P (secondary)',dose='F2_50',losses='',paired_scenarios='',estimate_percent=100*q['estimate'],ci_low_percent=100*q['low'],ci_high_percent=100*q['high']))
        values={r['mode']:{(p['seed'],p['phi_deg']):p['clearance_to_first_contact_or_horizon_mm'] for p in r['rows']} for r in nominal[tag]}
        keys=sorted(values['proportional']);jitter=np.random.default_rng(20261024+idx).uniform(-.05,.05,len(keys))
        for j,k in enumerate(keys):reserve.plot([values['proportional'][k],values['relay'][k]],[c+.13+jitter[j],c-.13+jitter[j]],lw=.35,color=LINE,zorder=0)
        for mode,shift,color,marker in [('proportional',.13,BLUE,'o'),('relay',-.13,GREEN,'s')]:
            v=[values[mode][k] for k in keys]
            reserve.scatter(v,c+shift+jitter,s=3,color=color,alpha=.35,marker=marker)
            reserve.plot(np.median(v),c+shift,marker='|',ms=9,mew=1.8,color=color)
    table('rf_source.csv',outrows)
    loss.set(yticks=tick,yticklabels=lab,xlim=(-2,36),xticks=[0,10,20,30],ylim=(.2,5.8),xlabel='Paired task loss (%)')
    loss.tick_params(axis='y',length=0,pad=2);loss.axvline(0,color=GRAY,ls=':',lw=.7)
    contrast.set(yticks=[5,3,1],yticklabels=tags,xlim=(-36,9),xticks=[-30,-15,0],ylim=(.2,5.8),xlabel='50% contrast (pp)')
    contrast.tick_params(axis='y',length=0,pad=3);contrast.axvline(0,color=GRAY,ls=':',lw=.7)
    reserve.set(yticks=[5,3,1],yticklabels=tags,xlabel='Healthy clearance\n(mm)',ylim=(.2,5.8),xticks=[0,20,40])
    reserve.tick_params(axis='y',length=0,pad=3)
    for ax in [loss,contrast,reserve]:
        for y in [2,4]:ax.axhline(y,color=LINE,lw=.4,zorder=0)
    loss.scatter([],[],s=14,color=BLUE,label='Proportional');loss.scatter([],[],s=14,color=GREEN,marker='s',label='Relay')
    fig.legend(*loss.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.095,.925),ncol=2,fontsize=7.5,columnspacing=.9,handlelength=.8)
    fig.text(.015,.97,'a  Primary loss',fontsize=9,weight='bold',va='top')
    fig.text(.48,.97,'b  Secondary law contrast',fontsize=9,weight='bold',va='top')
    fig.text(.80,.97,'c  Healthy reserve',fontsize=9,weight='bold',va='top')
    fig.text(.38,.815,'P | R loss counts',fontsize=7.5,color=GRAY)
    fig.text(.105,.045,'95% whole-seed CIs; n = 24 / 12 / 12. Zero-event caveats apply.',fontsize=7.5,color=GRAY)
    save(fig,'v10f_rf')

    # Warning observations are the frozen secondary operating points, not ROC.
    methods=[('transmission','Command',BLUE,'o'),('equal_duration_two_sided','Activity',ORANGE,'^'),('deadline','Forecast*',PURPLE,'s')]
    fig=plt.figure(figsize=(3.5,2.55));miss=fig.add_axes([.23,.34,.30,.45]);alarm=fig.add_axes([.65,.34,.30,.45])
    warnings=[]
    for i,tag in enumerate(tags):
        y=2-i
        for j,(name,label,color,marker) in enumerate(methods):
            q=summaries[tag]['warning_scores'][name]['all'];yy=y+(1-j)*.18
            for ax,metric in [(miss,'false_negative_rate'),(alarm,'false_positive_rate')]:
                val=100*q[metric];ci=100*np.array(q[metric+'_interval'])
                ax.plot(ci,[yy]*2,color=color,lw=.9)
                ax.scatter(val,yy,color=color,marker=marker,s=15,zorder=3)
            warnings.append(dict(map=tag,clusters=sizes[tag],criterion=label,tp=q['tp'],fn=q['fn'],fp=q['fp'],tn=q['tn'],fnr=q['false_negative_rate'],fnr_low=q['false_negative_rate_interval'][0],fnr_high=q['false_negative_rate_interval'][1],fpr=q['false_positive_rate'],fpr_low=q['false_positive_rate_interval'][0],fpr_high=q['false_positive_rate_interval'][1]))
    table('warning_source.csv',warnings)
    labels=[]
    for tag in tags:
        q=summaries[tag]['warning_scores']['transmission']['all']
        labels.append(f'{tag}\n{q["tp"]+q["fn"]} / {q["fp"]+q["tn"]}')
    miss.set(yticks=[2,1,0],yticklabels=labels,ylim=(-.45,2.45),xlim=(-5,105),xticks=[0,50,100],xlabel='Missed contacts (%)')
    alarm.set(yticks=[2,1,0],yticklabels=[],ylim=(-.45,2.45),xlim=(-2,42),xticks=[0,20,40],xlabel='False alarms (%)')
    for ax in [miss,alarm]:ax.tick_params(axis='y',length=0);ax.axvline(0,color=LINE,lw=.5,zorder=0)
    fig.text(.03,.94,'a  Misses',weight='bold',fontsize=8.5);fig.text(.59,.94,'b  False alarms',weight='bold',fontsize=8.5)
    for name,label,color,marker in methods:miss.scatter([],[],s=15,color=color,marker=marker,label=label)
    fig.legend(*miss.get_legend_handles_labels(),loc='lower center',ncol=3,fontsize=7.5,bbox_to_anchor=(.53,.08),columnspacing=.6,handlelength=.8,handletextpad=.3)
    fig.text(.20,.025,'* Exact simulated state; not neural-only.',fontsize=7.5,color=GRAY)
    save(fig,'v10f_warning')

    # The 3-figure alternative preserves each quantitative panel's printed scale.
    combined=pymupdf.open();page=combined.new_page(width=7.16*72,height=2.72*72)
    for name,x,y in [('v10f_reuse',0,0),('v10f_warning',3.66,.085)]:
        doc=pymupdf.open(a.out/(name+'.pdf'))
        page.show_pdf_page(pymupdf.Rect(x*72,y*72,(x+3.5)*72,(y+doc[0].rect.height/72)*72),doc,0)
        doc.close()
    combined.save(a.out/'v10f_reuse_warning.pdf');combined.close()
    overview=ROOT/'paper/figs/evidence_v10_overview.pdf'
    inputs[overview.relative_to(ROOT).as_posix()]=sha(overview)
    inputs['tools/aggregate_transfer_v10.py']=sha(ROOT/'tools/aggregate_transfer_v10.py')
    manifest=dict(passed=True,input_sha256=inputs,script_sha256=sha(__file__),
        outputs={p.name:sha(p) for p in a.out.iterdir()},
        locked_overview_sha256=sha(overview),error_layers=layers,
        v8_real_errors={k:len(history[k]) for k in ['horizon_flag_errors','delay_errors','completed_duration_errors']},
        pdf_fonttype=42,minimum_new_font_pt=7.5,
        sizes_inches=dict(reuse=[3.5,2.72],rf=[7.16,2.22],warning=[3.5,2.55]),
        scope='No simulation/calibration/threshold/data change. Conditional source-bound plots, not coverage, causality, execution authentication or hardware protection.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['input_sha256','outputs']},indent=2))


if __name__=='__main__':
    main()
