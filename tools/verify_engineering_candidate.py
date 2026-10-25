"""Read-only integrity and PDF checks for the additional engineering candidate.

Requires the base Git object and PyMuPDF. Output directories must be new.
Visual inspection and the submission portal are separate from automated checks.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
BASE = '22999d28d8fe22f863fc8f62eaa45a57256083d0'
AUTHORIZED = {
    'README.md', 'REPRODUCE.md', 'PUBLICATION.md',
    'paper/main.tex', 'paper/main_v10_1_timing.tex', 'paper/main_v10_horizon.tex',
    'paper/main.pdf', 'paper/iscas2027-v10.1-count-candidate.pdf',
    'paper/iscas2027-v10.1-timing-candidate.pdf', 'paper/refs.bib',
    *['paper/sections/'+n+'.tex' for n in (
        'v10f_methods', 'v10h_abstract', 'v10h_contract', 'v10h_figures',
        'v10h_intro', 'v10h_limits', 'v10h_results')],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(name):
    return subprocess.check_output(['git', 'show', BASE+':'+name], cwd=ROOT)


def embedded_images(doc):
    return Counter(sha(doc.extract_image(x)['image']) for x in {
        item[0] for page in doc for item in page.get_images()})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--pdf', type=Path, default=ROOT/'paper/iscas2027-v10.1-count-candidate.pdf')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    baseline = json.loads(git_bytes('PUBLIC_SCOPE.json'))
    protected = {}
    for name, expected in baseline['files'].items():
        if name in AUTHORIZED:
            continue
        data = (ROOT/name).read_bytes()
        assert sha(data) == expected['sha256'] and len(data) == expected['bytes'], name
        protected[name] = expected
    engineering = json.loads((ROOT/'ENGINEERING_SCOPE.json').read_text())
    for name, expected in engineering['files'].items():
        data = (ROOT/name).read_bytes()
        assert sha(data) == expected['sha256'] and len(data) == expected['bytes'], name
    pdf = args.pdf.resolve()
    pdfbytes = pdf.read_bytes()
    if pdf == (ROOT/'paper/iscas2027-v10.1-count-candidate.pdf').resolve():
        assert all((ROOT/name).read_bytes() == pdfbytes for name in (
            'paper/main.pdf', 'paper/iscas2027-v10.1-timing-candidate.pdf'))
    doc = pymupdf.open(stream=pdfbytes, filetype='pdf')
    assert len(doc) == 5 and len(pdfbytes) < 5_000_000
    assert not doc.is_encrypted and not doc.is_form_pdf and not doc.get_toc()
    assert all(tuple(page.rect) == (0., 0., 612., 792.) for page in doc)
    assert all(not page.get_links() and not list(page.annots() or []) for page in doc)
    fonts = {f[0]: f for page in doc for f in page.get_fonts()}
    assert all(f[2] != 'Type3' and bool(doc.extract_font(x)[3]) for x, f in fonts.items())
    text = [page.get_text() for page in doc]
    assert text[4].startswith('REFERENCES\n')
    assert not re.search(r'\b(?:Abstract|Conclusion|IV\.|V\.)\b', text[4])
    refs = sorted(int(n) for n in re.findall(r'^\[(\d+)\]', text[4], re.M))
    assert refs == list(range(1, 17)), refs
    old = pymupdf.open(stream=git_bytes('paper/iscas2027-v10.1-count-candidate.pdf'), filetype='pdf')
    assert embedded_images(old) == embedded_images(doc)
    oldfig = pymupdf.open(ROOT/'paper/figs/v10f_reuse_parenthesized.pdf')
    newfig = pymupdf.open(ROOT/'paper/figs/v10_1_ablation.pdf')
    clip = pymupdf.Rect(0, 0, oldfig[0].rect.width, 122)
    args_image = dict(matrix=pymupdf.Matrix(4, 4), clip=clip, alpha=False)
    oldpixels = oldfig[0].get_pixmap(**args_image)
    newpixels = newfig[0].get_pixmap(**args_image)
    assert oldpixels.samples == newpixels.samples
    log = args.log.read_text(errors='replace')
    bad = [line for line in log.splitlines() if re.search(
        r'Overfull|undefined|Missing character', line, re.I)]
    assert not bad, bad
    page_stats = []
    for i, page in enumerate(doc, 1):
        page.get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), alpha=False).save(args.out/f'page-{i}.png')
        (args.out/f'page-{i}.txt').write_text(text[i-1], encoding='utf8')
        page_stats.append(dict(page=i, words=len(text[i-1].split())))
    result = dict(
        passed=True, base_commit=BASE, candidate_pdf=str(pdf.relative_to(ROOT)),
        candidate_pdf_sha256=sha(pdfbytes), bytes=len(pdfbytes), pages=5,
        technical_pages=4, references_only_page=5, references=16,
        all_fonts_embedded=True, type3_fonts=0, embedded_fonts=len(fonts),
        undefined_references=0, overfull_boxes=0, missing_glyph_warnings=0,
        protected_baseline_files=len(protected), protected_sha256=protected,
        engineering_snapshot_files_verified=len(engineering['files']),
        existing_raster_images_unchanged=True,
        fig2_ab_pixel_comparison=dict(equal=True, scale=4, clip_pt=list(clip)),
        compiled_log_sha256=sha(args.log.read_bytes()), page_stats=page_stats,
        visual_inspection='Separate human/agent inspection is required.',
        submission_portal_validation='Not performed.',
    )
    (args.out/'check.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='protected_sha256'}, indent=2))


if __name__ == '__main__':
    main()
