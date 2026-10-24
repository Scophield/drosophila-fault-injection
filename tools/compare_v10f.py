"""All-page old/new visual comparison, source word counts and Blender integrity.

Only author-side comparison artifacts are created. Input papers and all locked
assets remain unchanged. Prose-token counts exclude maths/figures/tables and are
reported separately from PDF tokens; they are not a scientific-quality score.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import pymupdf
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def words(text):
    text=re.sub(r'(?<!\\)%[^\n]*','',text)
    text=re.sub(r'\\begin\{(figure\*?|table\*?)\}.*?\\end\{\1\}','',text,flags=re.S)
    text=re.sub(r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}','',text,flags=re.S)
    text=re.sub(r'\$[^$]*\$',' ',text)
    text=re.sub(r'\\(?:section|subsection|label|ref|cite|input)\*?(?:\[[^]]*\])?\{[^}]*\}',' ',text)
    text=re.sub(r'\\[A-Za-z]+|\\[,;% ]',' ',text)
    return len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*|\d+(?:\.\d+)?",text))


def image_data(doc):
    result=[]
    for i,page in enumerate(doc):
        for q in page.get_image_info(hashes=True,xrefs=True):
            result.append(dict(page=i+1,width=q['width'],height=q['height'],
                digest=q['digest'].hex(),bbox=list(q['bbox']),
                printed_size_pt=[q['bbox'][2]-q['bbox'][0],q['bbox'][3]-q['bbox'][1]]))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--backup',type=Path,required=True)
    ap.add_argument('--after',type=Path,required=True)
    ap.add_argument('--three',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    bm=json.loads((a.backup/'manifest.json').read_text())
    before=a.backup/'files/drosophila-fault-injection/paper/main.pdf'
    old=pymupdf.open(before);new=pymupdf.open(a.after);three=pymupdf.open(a.three)
    if len(old)!=len(new) or len(new)!=5 or len(three)!=5:raise ValueError('Expected5page candidates')
    locked=[];errors=[]
    for name,q in bm['files'].items():
        if q['locked']:
            okay=Path(q['source']).is_file() and sha(q['source'])==q['sha256']
            locked.append(dict(path=name,unchanged=okay,sha256=q['sha256']))
            if not okay:errors.append('locked asset changed:'+name)
    oi,ni,ti=image_data(old),image_data(new),image_data(three)
    for q in oi:
        for label,rows in [('four',ni),('three',ti)]:
            match=[v for v in rows if (v['digest'],v['width'],v['height'])==(q['digest'],q['width'],q['height'])]
            if len(match)!=1 or any(abs(x-y)>1e-5 for x,y in zip(q['printed_size_pt'],match[0]['printed_size_pt'])):
                errors.append('Blender pixels or printed scale changed:'+label)
    pairs=pymupdf.open();page_rows=[]
    for i in range(5):
        left=old[i].get_pixmap(dpi=130);right=new[i].get_pixmap(dpi=130)
        li=Image.frombytes('RGB',[left.width,left.height],left.samples)
        ri=Image.frombytes('RGB',[right.width,right.height],right.samples)
        plate=Image.new('RGB',(li.width+ri.width,max(li.height,ri.height)+30),'white')
        plate.paste(li,(0,30));plate.paste(ri,(li.width,30))
        draw=ImageDraw.Draw(plate);draw.text((12,8),'Previous V10',fill='black');draw.text((li.width+12,8),'Revised V10,4figures',fill='black')
        plate.save(a.out/f'page-{i+1}-before-after.png')
        p=pairs.new_page(width=1224,height=816)
        p.show_pdf_page(pymupdf.Rect(0,24,612,816),old,i)
        p.show_pdf_page(pymupdf.Rect(612,24,1224,816),new,i)
        p.insert_text((12,16),'Previous V10',fontsize=11)
        p.insert_text((624,16),'Revised V10: four-figure layout',fontsize=11)
        # IEEE body size remains10pt; titles/figure labels are counted separately.
        row=dict(page=i+1,before_pdf_tokens=len(old[i].get_text('words')),
            after_pdf_tokens=len(new[i].get_text('words')),
            three_pdf_tokens=len(three[i].get_text('words')))
        page_rows.append(row)
    pairs.save(a.out/'V10_before_after.pdf');pairs.close()
    groups={
        'abstract':(['main.tex'],['v10f_abstract.tex']),
        'introduction_related':(['v10_intro.tex','v10_related.tex'],['v10f_intro.tex']),
        'contract':(['v10_contract.tex'],['v10f_contract.tex']),
        'methods':(['v10_methods.tex'],['v10f_methods.tex']),
        'results':(['v10_results.tex'],['v10f_results.tex']),
        'artifact_discussion_conclusion':(['v10_artifact.tex','v10_discussion.tex'],['v10f_limits.tex'])}
    wc={}
    for name,(olds,news) in groups.items():
        otext=''
        for file in olds:
            p=a.backup/'files/drosophila-fault-injection/paper'/('' if file=='main.tex' else 'sections')/file
            t=p.read_text()
            if file=='main.tex':t=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',t,re.S).group(1)
            otext+=t+'\n'
        ntext='\n'.join((ROOT/'paper/sections'/file).read_text() for file in news)
        wc[name]=dict(before=words(otext),after=words(ntext))
    ob=sum(v['before'] for v in wc.values());nb=sum(v['after'] for v in wc.values())
    counts=dict(by_section=wc,before=ob,after=nb,reduction_percent=100*(ob-nb)/ob,
        definition='Deterministic English/numeric source prose tokens; excludes maths, headings, citations, figures/tables/captions. Separate PDF tokens include plot labels/captions. Not a quality score or deleted-scientific-content measure.')
    # Direct native raster placement identity supplies stronger evidence than
    # subjective similarity. Its pixel dimensions/digest AND printed size match.
    result=dict(passed=not errors,errors=errors,previous_pdf_sha256=sha(before),
        revised_pdf_sha256=sha(a.after),three_pdf_sha256=sha(a.three),
        locked_assets=locked,approved_raster_before=oi,approved_raster_after=ni,
        approved_raster_three=ti,pages=page_rows,prose_counts=counts,
        image_integrity='Locked file bytes, embedded raster pixels/dimensions and printed scale unchanged; no Blender asset regenerated/cropped/resampled. Pageplates are comparisons, not replacement art.',
        source_sha256=sha(__file__),visual_review='Separate human/agent all-page inspection required; this script does not certify legibility.')
    (a.out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],errors=errors,locked_count=len(locked),prose_counts=counts,pages=page_rows),indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
