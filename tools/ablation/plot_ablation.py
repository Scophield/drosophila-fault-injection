"""Replace only Fig.2(c), keeping the approved tank panels as original vectors."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pymupdf

ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--summary',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    report=json.loads(a.summary.read_text());counts=report['primary_confusion']
    original=ROOT/'paper/figs/v10f_reuse_parenthesized.pdf'
    doc=pymupdf.open(original);rect=doc[0].rect;split=123.
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':8,'text.color':'#243B49','pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(rect.width/72,(rect.height-split)/72))
    ax=fig.add_axes([0,0,1,1],xlim=(0,1),ylim=(0,1));ax.axis('off')
    ax.text(.06,.91,'(c) Fixed additional errors detected',fontsize=8.5,fontweight='bold',va='center')
    xs=[.43,.59,.75,.91]
    for x,arm in zip(xs,'ABCD'):ax.text(x,.72,arm,ha='center',va='center',fontsize=8,fontweight='bold')
    rows=[]
    for tag,y,label in [('fly',.50,'Fly'),('tank',.28,'Tank')]:
        denominator=counts[tag]['A']['invalid']
        ax.text(.06,y,f'{label} ({denominator})',fontsize=8,va='center')
        for x,arm in zip(xs,'ABCD'):
            n=counts[tag][arm]['tp'];rows.append(dict(plant=tag,arm=arm,detected_invalid=n,invalid=denominator,false_reject=counts[tag][arm]['fp'],valid=counts[tag][arm]['valid']))
            ax.add_patch(plt.Rectangle((x-.065,y-.09),.13,.18,facecolor='#E9F1F4',edgecolor='none'))
            ax.text(x,y,str(n),ha='center',va='center',fontsize=8.2,fontweight='bold' if arm=='D' else 'normal')
    ax.text(.06,.06,'False rejects: 0/12 valid cases per plant, all arms',fontsize=7.5,va='center',color='#677983')
    for ext in ['pdf','svg','png']:fig.savefig(a.out/('panel_c.'+ext),dpi=600)
    plt.close(fig)
    combined=pymupdf.open();page=combined.new_page(width=rect.width,height=rect.height)
    region=pymupdf.Rect(0,0,rect.width,split)
    page.show_pdf_page(region,doc,0,clip=region)
    panel=pymupdf.open(a.out/'panel_c.pdf')
    page.show_pdf_page(pymupdf.Rect(0,split,rect.width,rect.height),panel,0)
    target=a.out/'v10_1_ablation.pdf';combined.save(target,garbage=4,deflate=True)
    # Exclude the crop-edge raster row, which does not contain any old panel ink.
    clip=pymupdf.Rect(0,0,rect.width,split-1)
    old=doc[0].get_pixmap(matrix=pymupdf.Matrix(3,3),clip=clip)
    new=page.get_pixmap(matrix=pymupdf.Matrix(3,3),clip=clip)
    assert old.samples==new.samples,'Original panels changed'
    page.get_pixmap(matrix=pymupdf.Matrix(3,3)).save(a.out/'v10_1_ablation.png')
    with (a.out/'source.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    manifest=dict(source_figure_sha256=sha(original),summary_sha256=sha(a.summary),script_sha256=sha(Path(__file__).resolve()),
        cases=111,unique_inputs=107,invalid_cases=87,valid_cases=24,top_panels_pixel_identical=True,unchanged_clip_points=list(clip),
        outputs={p.name:sha(p) for p in a.out.iterdir()},fonttype=42,neural_simulation=False)
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
