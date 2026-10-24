"""V10 checked evidence overview using preserved audited Blender context.

No experimental data are drawn as anatomy. Footer states the checked interface
and its two executed adapters; all numbers bind to the evidence report.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, Arc
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
INK,MUTED,LINE='#243B49','#677983','#CED9DE'
TEAL,ORANGE,PURPLE,ROSE='#167F94','#BD7417','#7763B1','#B83D68'
P,R,CONTACT='#337BA0','#2A8276','#BC5A3D'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--renders',type=Path,required=True)
    ap.add_argument('--graph-audit',type=Path,required=True)
    ap.add_argument('--evidence',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    graph=json.loads(a.graph_audit.read_text());assert graph['passed']
    evidence=json.loads(a.evidence.read_text());assert evidence['passed']
    assert evidence['clean_records']==dict(tank=96,fly=288)
    assert all(len(v)==14 and all(q['detected'] for q in v) for v in evidence['corruption_cases'].values())
    rm=json.loads((a.renders/'render-manifest.json').read_text())
    for name,q in rm['outputs'].items():assert sha(a.renders/name)==q
    assert rm['scenes']['brain']['identities']==rm['scenes']['pathway']['identities']
    assert rm['scenes']['brain']['identities']['nodes']==410
    assert rm['scenes']['brain']['identities']['edges']==1050
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':7,'text.color':INK,'pdf.fonttype':42,'ps.fonttype':42,
        'svg.fonttype':'none','savefig.facecolor':'white'})
    # Coordinates are 100 units/inch; no image anisotropic stretching or crops.
    fig=plt.figure(figsize=(7.16,2.62))
    ax=fig.add_axes([0,0,1,1],xlim=(0,716),ylim=(-50,212));ax.axis('off')
    def text(x,y,s,size=7,ha='left',weight='normal',color=INK,**kw):
        return ax.text(x,y,s,fontsize=size,ha=ha,va='center',fontweight=weight,color=color,**kw)
    def arrow(start,end,color=P,**kw):
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=7,
            color=color,linewidth=.8,**kw))
    def picture(stem,box):
        im=plt.imread(a.renders/(stem+'.png'));x0,y0,x1,y1=box
        w,h=im.shape[1],im.shape[0];scale=min((x1-x0)/w,(y1-y0)/h)
        cx,cy=(x0+x1)/2,(y0+y1)/2
        ax.imshow(im,extent=[cx-w*scale/2,cx+w*scale/2,cy-h*scale/2,cy+h*scale/2],
                  interpolation='hanning',zorder=1)
    # a: actual representative-anchor arrangement, with an unregistered fly icon.
    text(4,202,'a',9,weight='bold');text(19,202,'Fly-connectome substrate',8.2,weight='bold')
    picture('brain',(3,78,214,186))
    text(108,184,'138,639-neuron LIF model',7,ha='center',weight='bold')
    picture('fly',(5,7,83,77))
    text(89,66,'Fly exterior:',6.6,color=MUTED)
    text(89,55,'illustration only',6.6,color=MUTED)
    text(89,33,'Brain: sampled anchors',6.4,color=MUTED)
    text(89,22,'8,500 background cells',6.4,color=MUTED)
    # b: preserved selected graph, rendered in a schematic clustered layout.
    text(232,202,'b',9,weight='bold');text(247,202,'Selected visual-to-command graph',8.2,weight='bold')
    picture('pathway',(268,31,539,177))
    text(247,182,'Visual input',6.8,weight='bold')
    text(394,182,'Relays',6.8,ha='center',weight='bold')
    text(516,182,'Readout',6.8,ha='center',weight='bold')
    text(239,145,'LC4',6.8,color=TEAL,weight='bold')
    text(239,134,'104',6.8,color=TEAL)
    text(237,62,'LPLC2',6.8,color=ORANGE,weight='bold')
    text(237,51,'210',6.8,color=ORANGE)
    text(408,22,'88',6.8,ha='center',color=PURPLE)
    text(527,22,'8 DNs',6.8,ha='center',color=ROSE)
    text(386,7,'410 cells / 1,050 selected connections; schematic layout',6.3,ha='center',color=MUTED)
    # c: explicit synthetic plant and feedback, not a fly body reconstruction.
    text(555,202,'c',9,weight='bold');text(570,202,'Task and exact clocks',8.0,weight='bold')
    text(632,183,'20-ms input → SNN → decision',6.6,ha='center',weight='bold')
    # Geometric task in body frame. Distances/angles are illustrative here.
    agent=np.array([581.,148.]);target=np.array([682.,157.])
    ax.plot([*agent[:1],target[0]],[agent[1],target[1]],ls='--',color=MUTED,lw=.65)
    ax.scatter(*agent,s=18,color=P,zorder=4)
    arrow(agent,agent+np.array([28.,15.]));arrow(target,target-np.array([16.,2.]))
    ax.add_patch(Circle(target,12,fill=False,ec=CONTACT,ls=':',lw=.75))
    ax.scatter(*target,s=22,color=CONTACT,zorder=4)
    ax.add_patch(Arc(agent,35,35,theta1=5,theta2=28,color=P,lw=.7))
    text(603,149,'φ',7,color=P);text(636,166,'d',7,color=MUTED)
    text(581,131,'Agent',6.4,color=P,ha='center');text(682,137,'Pursuer',6.4,color=CONTACT,ha='center')
    ax.plot([698,706,706,554,554],[151,151,115,115,182],lw=.65,color=MUTED)
    arrow((554,182),(563,182),color=MUTED)
    text(630,121,'Next-frame action → body → new input',6.0,ha='center',color=MUTED)
    # t_d=200-ms example only: exact 250-ms delay then 450-ms burst.
    x=lambda t:564+136*t/1000
    y=77;ax.plot([x(0),x(1000)],[y,y],color=LINE,lw=1)
    for t,label in [(0,'0'),(100,'100'),(400,'400'),(1000,'1000')]:
        ax.plot([x(t),x(t)],[y-3,y+3],color=MUTED,lw=.65)
        text(x(t),y+13,label,6.2,ha='center' if t!=1000 else 'right')
    text(x(100),y+26,'Cue',6.2,ha='center');text(x(400),y+26,'Assess',6.2,ha='center')
    text(x(1000),y+26,'Task',6.2,ha='right')
    text(704,y,'ms',6.2)
    ax.plot([x(200),x(450)],[49,49],ls='--',color=MUTED,lw=.9)
    ax.plot([x(450),x(900)],[49,49],color=R,lw=4,solid_capstyle='butt')
    text(x(200),64,r'$t_d=200$ ms',6.2,ha='center')
    text(x(300),35,'250 ms delay',6.2,ha='center')
    text(x(750),35,'450 ms burst',6.2,ha='center',color=R)
    text(631,19,'Paired seed: 2 bearings × 2 laws',6.3,ha='center',color=MUTED)
    text(631,7,'× 3 network conditions',6.3,ha='center',color=MUTED)
    # Subtle whitespace dividers, not enclosing boxes.
    for xpos in [222,546]:ax.plot([xpos,xpos],[13,190],color=LINE,lw=.6)
    # Shared contract with two genuinely executed native adapters.
    ax.plot([5,711],[-3,-3],color=LINE,lw=.6)
    text(4,-15,'d',9,weight='bold');text(19,-15,'Checked evidence interface',7.5,weight='bold')
    text(9,-32,'Fly traces / tank traces',6.8)
    arrow((128,-32),(154,-32),color=MUTED)
    text(161,-22,'Declare matrix + bindings',6.6)
    text(161,-36,'Pairing / clocks / exposure',6.6,color=MUTED)
    arrow((310,-32),(335,-32),color=MUTED)
    text(342,-22,'Common checks + native replay',6.6)
    text(342,-36,'14 error types tested per adapter',6.6,color=MUTED)
    arrow((519,-32),(542,-32),color=MUTED)
    text(550,-22,'Pass → endpoint analysis',6.6)
    text(550,-36,'Issues → investigate; no attestation',6.0,color=MUTED)
    for ext in ['pdf','svg','png']:
        fig.savefig(a.out/f'evidence_v10_overview.{ext}',dpi=600,facecolor='white')
    plt.close(fig)
    inputs={}
    for p in [Path(__file__),a.graph_audit,a.renders/'render-manifest.json',a.evidence,
              *[a.renders/(stem+'.png') for stem in ['fly','brain','pathway']]]:
        inputs[p.resolve().relative_to(ROOT).as_posix()]=sha(p)
    result=dict(script_sha256=sha(__file__),input_sha256=inputs,
        outputs={p.name:sha(p) for p in a.out.iterdir() if p.is_file()},
        final_size_inches=[7.16,2.62],pdf_fonttype=42,
        scope='Preserved selected graph/representative anchors/illustrative fly; vector input/action/contract arrows are schematic. No new anatomy or neural data.')
    (a.out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['input_sha256','outputs']},indent=2))


if __name__=='__main__':main()
