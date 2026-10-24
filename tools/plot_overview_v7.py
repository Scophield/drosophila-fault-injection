"""Schematic overview: model flow, distinct endpoints and assessment choices.

Contract: transmission, network activity and bounded task outcome require separate
reporting with declared cohorts, exposure and control laws. Schematic-led composite;
Python only; 3.5 x 2.65 inches; editable SVG/PDF plus 600-dpi PNG. Icons and traces
illustrate definitions, not measured wiring, spike trains or trajectories.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INK, BLUE, ORANGE, GREY = '#243746', '#336E91', '#B46A24', '#65727B'
PALE, LINE = '#F0F5F7', '#CAD5DB'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def generate(out):
    out.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':7,
                         'pdf.fonttype':42, 'ps.fonttype':42, 'svg.fonttype':'none'})
    fig = plt.figure(figsize=(3.5, 2.65), facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 350), ylim=(0, 265), aspect='equal')
    ax.axis('off')
    def text(x,y,s,size=7,weight='normal',color=INK,ha='center',**kw):
        return ax.text(x,y,s,fontsize=size,fontweight=weight,color=color,
                       ha=ha,va='center',**kw)
    def arrow(a,b,color=BLUE,style='-|>',lw=1,**kw):
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle=style,mutation_scale=7,
                                    linewidth=lw,color=color,**kw))
    def heading(y,letter,title):
        text(7,y,letter,9,'bold',ha='left')
        text(22,y,title,8,'bold',ha='left')
    heading(254,'a','From visual input to movement')
    # Looming cue: concentric outlines denote an approaching visual object.
    for r,alpha in [(19,.2),(13,.45),(7,1)]:
        ax.add_patch(Circle((43,216),r,fc='none',ec=BLUE,lw=1,alpha=alpha))
    arrow((21,239),(32,230),lw=.8)
    arrow((79,216),(110,216))
    # Diagrammatic network, deliberately not an anatomical reconstruction.
    nodes=np.array([[127,219],[140,233],[152,211],[166,229],[181,215],
                    [134,201],[170,198]])
    for i,j in [(0,1),(0,2),(0,5),(1,3),(2,3),(2,4),(2,5),(2,6),(3,4),(4,6),(5,6)]:
        ax.plot(nodes[[i,j],0],nodes[[i,j],1],color=LINE,lw=.8,zorder=1)
    ax.scatter(nodes[:,0],nodes[:,1],s=14,color=BLUE,zorder=2)
    ax.add_patch(Polygon([[155,242],[148,230],[155,231],[151,221],
                         [163,235],[156,234]],fc=ORANGE,ec='white',lw=.35,zorder=3))
    text(96,238,'Faults\nF1-F5',6.3,color=ORANGE)
    arrow((114,237),(147,235),color=ORANGE,lw=.7)
    arrow((198,216),(240,216))
    text(219,232,'8 command\ncells',6.4)
    # Stylized fly and direction arrow; no behavioral trajectory is invented.
    ax.add_patch(Ellipse((270,221),11,24,angle=-32,fc=PALE,ec=BLUE,lw=.8))
    ax.add_patch(Ellipse((287,221),11,24,angle=32,fc=PALE,ec=BLUE,lw=.8))
    ax.add_patch(Ellipse((278.5,213),7,21,fc=INK,ec='none'))
    ax.add_patch(Circle((278.5,226),4,fc=INK,ec='none'))
    arrow((300,209),(326,226),lw=1.2)
    for x,label,sub in [(43,'Visual input','314 sensory cells'),
                         (154,'Spiking model','138,639 neurons'),
                         (285,'Motion','steering + burst')]:
        text(x,185,label,7,'bold')
        text(x,173,sub,6.5,color=GREY)
    # Feedback applies only to the geometric episodes, not the open-loop archive.
    ax.plot([285,285,43,43],[162,153,153,162],color=GREY,lw=.8)
    arrow((43,160),(43,168),color=GREY,lw=.8)
    text(164,153,'visual feedback in geometric tests',6.3,color=GREY,
         bbox={'facecolor':'white','edgecolor':'none','pad':1.8})
    ax.plot([7,343],[142,142],color=LINE,lw=.7)
    heading(131,'b','Measure three different outcomes')
    # Each icon is schematic, with equal visual weight and no pass/fail coloring.
    for lo,hi in [(15,101),(130,216),(245,331)]:
        ax.plot([lo,hi],[100,100],color=LINE,lw=.65)
    ax.plot([17,34,34,37,37,56,56,59,59,80,80,83,83,99],
            [100,100,115,100,100,100,110,100,100,100,115,100,100,100],color=BLUE,lw=1)
    for row,xx in enumerate([[137,153,180,204],[144,160,168,198],[139,174,190,209]]):
        for x in xx:
            ax.plot([x,x],[102+row*5,105+row*5],color=BLUE,lw=.8)
    # Bounded task illustration: a moving agent and an obstacle, not a data trace.
    ax.add_patch(Circle((311,109),7,fc='none',ec=GREY,lw=.8))
    ax.add_patch(Polygon([[251,103],[258,109],[251,115]],fc=BLUE,ec='none'))
    arrow((261,109),(296,109),lw=.8)
    for x,label,sub in [(58,'Transmission','command rate'),(173,'Activity','network spikes'),
                         (288,'Task outcome','survival at 1 s')]:
        text(x,86,label,7.1,'bold')
        text(x,74,sub,6.5,color=GREY)
    ax.plot([7,343],[62,62],color=LINE,lw=.7)
    heading(51,'c','Declare the assessment conditions')
    for x,label in [(7,'Which trials?'),(122,'How long?'),(237,'Which control?')]:
        ax.add_patch(FancyBboxPatch((x,22),106,19,boxstyle='round,pad=0,rounding_size=3',
                                   fc=PALE,ec=LINE,lw=.65))
        text(x+53,31.5,label,7)
    text(175,10,'Cohort     |     paired exposure + full horizon     |     feedback law',6.2,color=GREY)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    outside=[]
    for t in ax.texts:
        if not fig.bbox.contains(*t.get_window_extent(renderer).get_points()[0]) or not fig.bbox.contains(*t.get_window_extent(renderer).get_points()[1]):
            outside.append(t.get_text())
    if outside:
        raise ValueError(f'text outside figure: {outside}')
    for suffix in ('pdf','svg','png'):
        fig.savefig(out/f'assessment_overview.{suffix}',dpi=600)
    plt.close(fig)
    sources=['paper/sections/methods.tex','paper/sections/results.tex',
             'paper/sections/controller_results.tex','tools/plot_overview_v7.py']
    manifest={'version':'assessment-v7','archetype':'schematic-led composite',
              'dimensions_inches':[3.5,2.65], 'minimum_font_pt':6.2,
              'claim':'Report transmission, activity and bounded task outcome with declared assessment conditions.',
              'schematic_only':True,'simulations_executed':False,
              'notes':['Icons are not measured spike trains, wiring or trajectories.',
                       'Visual feedback applies to geometric episodes; archived open-loop runs use prescribed drive.',
                       'Transmission and activity criteria are distinct from the bounded task outcome.'],
              'source_sha256':{p:sha(ROOT/p) for p in sources},
              'output_sha256':{p.name:sha(p) for p in out.glob('assessment_overview.*')},
              'text_outside_canvas':outside}
    (out/'overview_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'output':str(out),'formats':['pdf','svg','png'],'text_outside_canvas':outside}))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    generate(ap.parse_args().out.resolve())
