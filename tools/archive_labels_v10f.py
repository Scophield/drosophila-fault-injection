"""Create a separately named research archive; preserve the frozen V10 SI.

Label/caption edits only. No data, inference, figures, registrations or original
PDFs are rewritten. The result is research history, not an ISCAS attachment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    original = ROOT / 'paper/supplement_v10.tex'
    frozen = ROOT / 'paper/supplement.pdf'
    original_hash, frozen_hash = sha(original), sha(frozen)
    text = original.read_text(encoding='utf-8')
    revised = text.replace('Supplementary Information', 'Research Archive')
    revised = revised.replace(
        'This document separates the independent core test, a prespecified angle stress',
        'This archive is not an ISCAS submission attachment. The four-page main paper is self-contained.\n'
        'This document separates the independent core test, a prespecified angle stress')
    for old, new in {
        r'stop\_ratio': 'Own-stop ratio',
        r'common\_ratio': 'Common-duration ratio',
        r'early\_ratio': '400-ms ratio',
        r'full\_ratio': '1-s ratio',
    }.items():
        revised = revised.replace(old, new)
    revised = revised.replace(
        'Every actual independent cluster contrast. P/R and 25/50 match the preceding table; interaction is R minus P net loss.',
        'Every actual independent cluster contrast. Entries are proportions, not percentage points. '
        'P/R and 25/50 match the preceding table; interaction is R minus P net loss.')
    # All scientific numbers remain identical; numbers in replacement labels
    # merely spell out the already defined duration endpoints.
    def table_numbers(t):
        tables = re.findall(r'\\begin\{(?:tabular|longtable)\}.*?\\end\{(?:tabular|longtable)\}', t, re.S)
        return [re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?',
                           re.sub(r'(?:400-ms|1-s) ratio', '', q)) for q in tables]
    assert table_numbers(text) == table_numbers(revised), 'A table number changed'
    (out / 'main.tex').write_text(revised, encoding='utf-8')
    shutil.copytree(ROOT / 'paper/figs', out / 'figs')
    exe = shutil.which('pdflatex')
    if not exe:
        raise RuntimeError('pdflatex is required')
    for n in [1, 2]:
        r = subprocess.run([exe, '--disable-installer', '-interaction=nonstopmode',
                            '-halt-on-error', '-file-line-error', 'main.tex'],
                           cwd=out, capture_output=True)
        (out / f'pass{n}.txt').write_bytes(r.stdout + r.stderr)
        if r.returncode:
            raise RuntimeError(f'pdflatex failed, pass{n}')
    log = (out / 'main.log').read_text(errors='replace')
    issues = re.findall(r'Overfull \\[hv]box[^\n]*|Missing character:[^\n]*|Float too large[^\n]*', log)
    assert sha(original) == original_hash and sha(frozen) == frozen_hash
    result = dict(passed=not issues, issues=issues,
                  original_tex_sha256=original_hash, frozen_pdf_sha256=frozen_hash,
                  original_files_unchanged=True, table_numbers_unchanged=True,
                  revised_tex_sha256=sha(out/'main.tex'), revised_pdf_sha256=sha(out/'main.pdf'),
                  scope='Research archive label/caption errata only; NOT a submission attachment; no new data or recomputation.')
    (out / 'check.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
