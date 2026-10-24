"""Render EVERY PDF page with Poppler and independently inspect font embedding.

Read-only with respect to the input PDF; all outputs use a new directory.
Text/geometry/reference checks remain in qa_pdf.py and final visual review.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pdf',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--main',action='store_true')
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    binaries={name:shutil.which(name) for name in ['pdftoppm','pdffonts','pdfinfo']}
    if not all(binaries.values()):raise RuntimeError('Poppler utilities missing: '+repr(binaries))
    def run(name,args):
        r=subprocess.run([binaries[name],*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        (a.out/(name+'.stdout.txt')).write_text(r.stdout,encoding='utf-8')
        (a.out/(name+'.stderr.txt')).write_text(r.stderr,encoding='utf-8')
        if r.returncode:raise RuntimeError(name+' failed; see output logs')
        return r.stdout
    info=run('pdfinfo',[a.pdf.resolve()])
    fonts=run('pdffonts',[a.pdf.resolve()])
    pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1))
    lines=fonts.splitlines()
    header=next(i for i,line in enumerate(lines) if line.startswith('name') and 'encoding' in line and 'emb' in line)
    emb=lines[header].index('emb')
    rows=[s for s in lines[header+2:] if re.search(r'\d+\s+\d+\s*$',s)]
    errors=[]
    if not rows:errors.append('No fonts found in textual manuscript')
    if any(re.search(r'Type\s*3',row) for row in rows):errors.append('Type 3 font present')
    if any(row[emb:emb+3].strip()!='yes' for row in rows):errors.append('Unembedded font present')
    if a.main and (pages>5 or a.pdf.stat().st_size>=5_000_000):errors.append('Main page-count/size limit exceeded')
    run('pdftoppm',['-r','130','-png',a.pdf.resolve(),(a.out/'page').resolve()])
    images=sorted(p.name for p in a.out.glob('page-*.png'))
    if len(images)!=pages:errors.append('Not every page rendered')
    report=dict(passed=not errors,errors=errors,pdf_sha256=hashlib.sha256(a.pdf.read_bytes()).hexdigest(),
                pages=pages,bytes=a.pdf.stat().st_size,font_rows=len(rows),rendered_pages=images,
                dpi=130,tools=binaries,utc=datetime.now(timezone.utc).isoformat(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Native Poppler all-page rendering and font/size checks; not visual approval, references-only-page verification or scientific validation.')
    (a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
