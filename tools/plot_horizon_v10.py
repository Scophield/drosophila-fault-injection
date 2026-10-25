"""Descriptive horizon rescoring across RFs; unchanged RF-0 first-contact curve.

Append a vector strip to the unchanged Figure3(a-c). No new neural episodes,
threshold fitting, confidence intervals or hypothesis tests are generated.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
BLUE,GREEN,INK,GRAY='#337BA0','#2A8276','#243B49','#677983'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    original=ROOT/'paper/figs/v10f_rf.pdf'
    summary_path=ROOT/'audit/acceptance-v9/core-v2/summary.json'
    summary=json.loads(summary_path.read_text());records=[];hashes={}
    for name,h in summary['raw_input_sha256'].items():
        p=ROOT/name;assert sha(p)==h;hashes[name]=h
        r=json.loads(p.read_text());assert r['horizon_ms']==r['duration_ms']==1000.
        assert r['escaped']==(r['collision_ms'] is None)
        records.append((p,r))
    assert len(records)==288 and len({r['seed'] for _,r in records})==24
    selected=[(p,r) for p,r in records if r['fault']=='F2_50']
    assert len(selected)==96
    lookup={(r['seed'],r['phi_deg'],r['mode'],r['fault']):r for _,r in records}
    source=[]
    for p,r in selected:
        other=lookup[(r['seed'],r['phi_deg'],'relay' if r['mode']=='proportional' else 'proportional','F2_50')]
        assert r['mask_sha256']==other['mask_sha256'] and r['uniform_sha256']==other['uniform_sha256']
        assert lookup[(r['seed'],r['phi_deg'],r['mode'],'healthy')]['escaped']
        source.append(dict(seed=r['seed'],phi_deg=r['phi_deg'],law=r['mode'],fault=r['fault'],
            first_contact_ms=r['collision_ms'],success900=r['collision_ms'] is None or r['collision_ms']>900,
            success1000=r['escaped'],mask_sha256=r['mask_sha256'],uniform_sha256=r['uniform_sha256'],
            source=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    table=[];curves=[]
    for t in [900.,1000.]:
        row=dict(horizon_ms=t)
        for mode in ['proportional','relay']:
            group=[r for _,r in selected if r['mode']==mode]
            assert len(group)==48
            count=sum(r['collision_ms'] is None or r['collision_ms']>t for r in group)
            row[mode+'_success']=count;row[mode+'_n']=len(group)
        table.append(row)
    assert [(r['proportional_success'],r['relay_success']) for r in table]==[(46,48),(37,48)]
    for row in source:row['map']='RF-0'
    all_table=[dict(map='RF-0',**r) for r in table]
    summary_hashes={'RF-0':sha(summary_path)}
    for tag in ['A','B']:
        path=ROOT/f'audit/v10/transfer-01/map-{tag}/analysis/summary.json'
        saved=json.loads(path.read_text());summary_hashes['RF-'+tag]=sha(path);rows=[]
        for name,h in saved['raw_input_sha256'].items():
            p=ROOT/name;assert sha(p)==h;hashes[name]=h
            r=json.loads(p.read_text());assert r['horizon_ms']==r['duration_ms']==1000.
            assert r['escaped']==(r['collision_ms'] is None);rows.append((p,r))
        assert len(rows)==144 and len({r['seed'] for _,r in rows})==12
        pairs={(r['seed'],r['phi_deg'],r['mode'],r['fault']):r for _,r in rows}
        fault_rows=[(p,r) for p,r in rows if r['fault']=='F2_50'];assert len(fault_rows)==48
        for p,r in fault_rows:
            other=pairs[r['seed'],r['phi_deg'],'relay' if r['mode']=='proportional' else 'proportional','F2_50']
            assert r['mask_sha256']==other['mask_sha256'] and r['uniform_sha256']==other['uniform_sha256']
            assert pairs[r['seed'],r['phi_deg'],r['mode'],'healthy']['escaped']
            source.append(dict(seed=r['seed'],phi_deg=r['phi_deg'],law=r['mode'],fault=r['fault'],
                first_contact_ms=r['collision_ms'],success900=r['collision_ms'] is None or r['collision_ms']>900,
                success1000=r['escaped'],mask_sha256=r['mask_sha256'],uniform_sha256=r['uniform_sha256'],
                source=p.relative_to(ROOT).as_posix(),sha256=sha(p),map='RF-'+tag))
        for t in [900.,1000.]:
            q=dict(map='RF-'+tag,horizon_ms=t)
            for mode in ['proportional','relay']:
                group=[r for _,r in fault_rows if r['mode']==mode];assert len(group)==24
                q[mode+'_success']=sum(r['collision_ms'] is None or r['collision_ms']>t for r in group)
                q[mode+'_n']=24
            all_table.append(q)
    assert [(q['proportional_success'],q['relay_success']) for q in all_table]==[(46,48),(37,48),(23,23),(22,23),(24,24),(23,24)]
    for mode in ['proportional','relay']:
        events=sorted(r['collision_ms'] for _,r in selected if r['mode']==mode and r['collision_ms'] is not None)
        times=[0.,*events,1000.];counts=[0,*range(1,len(events)+1),len(events)]
        curves.extend(dict(law=mode,time_ms=t,cumulative_contacts=c,n=48,cumulative_percent=100*c/48) for t,c in zip(times,counts))
    for name,rows in [('first-contacts.csv',source),('horizon-counts.csv',all_table),('curve-points.csv',curves)]:
        with (a.out/name).open('x',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':8,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,
        'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,
        'lines.linewidth':1.1,'legend.frameon':False,'text.color':INK,'axes.labelcolor':INK,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    with pymupdf.open(original) as source_doc:figure_width=source_doc[0].rect.width/72
    fig=plt.figure(figsize=(figure_width,1.5));ax=fig.add_axes([.075,.38,.53,.41])
    for mode,color,label,marker in [('proportional',BLUE,'P','o'),('relay',GREEN,'R','s')]:
        values=[r for r in curves if r['law']==mode]
        ax.step([r['time_ms']/1000 for r in values],[r['cumulative_percent'] for r in values],
            where='post',color=color,label=label)
        ax.scatter([.9,1.],[100*(48-q[mode+'_success'])/48 for q in table],color=color,marker=marker,s=13,zorder=5)
    ax.axvline(.9,color=GRAY,ls=':',lw=.8)
    ax.set(xlim=(0,1.015),ylim=(-1.4,25),xticks=[0,.4,.9,1.],yticks=[0,10,20],
        xlabel='Time since episode start (s)',ylabel='First contacts (%)')
    ax.legend(loc='upper left',ncol=2,fontsize=8,handlelength=1.5,borderaxespad=.1)
    fig.text(.01,.94,'d  RF-0 first contacts; 50% deletion outcomes across horizons',fontsize=9,fontweight='bold',va='top')
    fig.text(.81,.77,'Contact-free tasks (P, R)',ha='center',fontsize=8.5,fontweight='bold')
    for x,label in [(.66,'RF'),(.78,'900 ms'),(.935,'1000 ms')]:fig.text(x,.60,label,ha='center',fontsize=8,color=GRAY)
    for y,tag in zip([.43,.27,.11],['RF-0','RF-A','RF-B']):
        fig.text(.66,y,tag,ha='center',fontsize=8.5)
        for x,t in [(.78,900.),(.935,1000.)]:
            q=next(q for q in all_table if q['map']==tag and q['horizon_ms']==t);n=q['proportional_n']
            fig.text(x,y,f"{q['proportional_success']}/{n}, {q['relay_success']}/{n}",ha='center',fontsize=8.5)
    fig.text(.075,.025,'Same trajectories at both horizons; 24/12/12 seed clusters. No new samples or hypothesis tests.',fontsize=8,color=GRAY)
    for ext in ['pdf','svg','png']:fig.savefig(a.out/('horizon-strip.'+ext),dpi=600,facecolor='white')
    plt.close(fig)
    old=pymupdf.open(original);strip=pymupdf.open(a.out/'horizon-strip.pdf')
    assert abs(old[0].rect.width-strip[0].rect.width)<.01
    width=old[0].rect.width;old_h=old[0].rect.height;new_h=strip[0].rect.height;gap=5.
    merged=pymupdf.open();page=merged.new_page(width=width,height=old_h+gap+new_h)
    page.show_pdf_page(pymupdf.Rect(0,0,width,old_h),old,0)
    page.show_pdf_page(pymupdf.Rect(0,old_h+gap,width,old_h+gap+new_h),strip,0)
    merged.save(a.out/'rf-with-horizon.pdf',garbage=4,deflate=True)
    page.get_pixmap(dpi=180).save(a.out/'preview.png')
    result=dict(passed=True,classification='descriptive same-record horizon rescoring',
        independent_seed_clusters={'RF-0':24,'RF-A':12,'RF-B':12},
        tasks_per_law={'RF-0':48,'RF-A':24,'RF-B':24},source_records=576,plotted_records=96,tabulated_records=192,
        horizon_counts=all_table,original_figure_sha256=sha(original),
        original_panels_imported_without_scaling=True,original_dimensions_pt=list(old[0].rect),
        composite_dimensions_pt=list(page.rect),raw_input_sha256=hashes,
        frozen_summary_sha256=sha(summary_path),all_summary_sha256=summary_hashes,script_sha256=sha(Path(__file__).resolve()),
        runtime=dict(python=platform.python_version(),numpy=np.__version__,matplotlib=matplotlib.__version__),
        confidence_intervals_added=False,hypothesis_tests=False,new_neural_simulations=False,
        unequal_healthy_reserve_and_cohort_calibration_confounding_retained=True)
    (a.out/'check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='raw_input_sha256'},indent=2))


if __name__=='__main__':main()
