"""Render every page and inspect PDF fonts/text geometry; no LaTeX execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import pymupdf
from PIL import Image, ImageDraw


def submission_features(doc):
    version = re.search(r'PDF\s*(\d+)\.(\d+)', doc.metadata.get('format', ''))
    encrypted = bool(doc.needs_pass or doc.metadata.get('encryption'))
    return dict(pdf_version='.'.join(version.groups()) if version else None,
                encrypted=encrypted,
                links_per_page=[len(p.get_links()) for p in doc],
                bookmarks=len(doc.get_toc()),
                widgets_per_page=[len(list(p.widgets() or [])) for p in doc],
                form_fields=int(doc.is_form_pdf or 0))


def submission_errors(features):
    errors = []
    version = features['pdf_version']
    if version is None or tuple(map(int, version.split('.'))) < (1, 4):
        errors.append('PDF version is below 1.4 or unavailable')
    if features['encrypted']:
        errors.append('PDF is encrypted')
    if sum(features['links_per_page']):
        errors.append('PDF contains link annotations')
    if features['bookmarks']:
        errors.append('PDF contains bookmarks')
    if features['form_fields'] or sum(features['widgets_per_page']):
        errors.append('PDF contains form fields or widgets')
    return errors


def references_only_fifth_page(doc):
    """ISCAS permits four content pages plus an optional reference-only fifth."""
    if len(doc)<5:
        return True
    if len(doc)>5:
        return False
    page=doc[4]
    return bool(page.get_text().lstrip().startswith('REFERENCES')
                and not page.get_image_info() and not page.get_drawings())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pdf',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--submission',action='store_true',
                    help='Fail for interactive features, encryption or PDF versions below 1.4')
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    doc=pymupdf.open(args.pdf)
    pages=[];fonts={};text=[];outside=[]
    for i,page in enumerate(doc):
        dest=args.out/f'page-{i+1}.png'
        page.get_pixmap(dpi=130).save(dest)
        pages.append(dest)
        text.append(page.get_text())
        for font in page.get_fonts(full=True):
            xref=font[0]
            data=doc.extract_font(xref)
            fonts[str(xref)]=dict(type=font[2],name=font[3],embedded_bytes=len(data[3]))
        for word in page.get_text('words'):
            if not page.rect.contains(pymupdf.Rect(word[:4])):
                outside.append(dict(page=i+1,text=word[4],bbox=word[:4]))
    thumb_w=440;thumb_h=600
    sheet=Image.new('RGB',(thumb_w*3,thumb_h*((len(pages)+2)//3)),'#dddddd')
    draw=ImageDraw.Draw(sheet)
    for i,path in enumerate(pages):
        im=Image.open(path).convert('RGB');im.thumbnail((thumb_w-12,thumb_h-28))
        x=(i%3)*thumb_w+6;y=(i//3)*thumb_h+22
        sheet.paste(im,(x,y));draw.text((x,y-18),f'Page {i+1}',fill='black')
    sheet.save(args.out/'contact-sheet.png')
    (args.out/'text.txt').write_text('\n\f\n'.join(text),encoding='utf-8')
    result: dict = dict(pdf_sha256=hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
                references_only_fifth_page=references_only_fifth_page(doc),
                pages=len(doc),page_sizes=[list(p.rect) for p in doc],fonts=fonts,
                type3=[v for v in fonts.values() if v['type']=='Type3'],
                unembedded=[v for v in fonts.values() if not v['embedded_bytes']],
                outside_page=outside)
    result.update(submission_features(doc))
    result['submission_feature_errors'] = submission_errors(result)
    (args.out/'qa.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if args.submission and result['submission_feature_errors']:
        raise SystemExit(1)


if __name__=='__main__':main()
