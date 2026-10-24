"""Create a local, hash-bound V10 review snapshot; never publish or commit it.

Includes inherited Git files and explicit V10 sources/data/audits. It excludes
temporary installations, external matrices, secrets, unrelated untracked history,
and redundant draft build/QA directories. Existing output files are refused.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '43bcd4d6a99b2d9b258cf8a198a4545d237b5c39'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--validation', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    receipt = a.out.with_suffix('.receipt.json')
    if a.out.exists() or receipt.exists():
        raise FileExistsError('Select a new local archive/receipt path')
    validation = json.loads(a.validation.read_text())
    if not validation['passed']:
        raise ValueError('Final scientific/layout/source validation required')
    for name,h in validation['bound_sha256'].items():
        if sha(ROOT/name) != h:
            raise ValueError('Changed after final validation: '+name)
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch = subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if head != BASE or branch != 'research/iscas2027-v10':
        raise ValueError('Unexpected V10 baseline/branch; review version metadata first')
    paths = set()

    def add(p):
        p = p.resolve()
        if not p.is_relative_to(ROOT) or not p.is_file() or p.is_symlink():
            raise ValueError('Unsafe/missing snapshot member: '+str(p))
        paths.add(p)

    for name in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'):
        if name:
            add(ROOT/name)
    for pattern in ['tools/*v10*.py','tools/*v10*.ps1','tests/*v10*.py',
                    'paper/main_v10.tex','paper/*_v10.pdf','paper/*_v10.tex',
                    'paper/sections/v10_*.tex','paper/figs/*v10*.pdf',
                    'docs/*V10*.md','docs/history/V9_*_at_43bcd4d.md',
                    'docs/history/V10_STATE*.md',
                    '*V10*.md','paper/*V10*.md','requirements-saved-v10.txt','paper/REVIEW_2026-10-23_V9.txt']:
        for p in ROOT.glob(pattern):
            add(p)
    for folder in ['evidence_v10','examples','docs/history/v9-paper-at-43bcd4d','runs/task-v10-design',
                   'runs/task-v10-map-A-pilot','runs/task-v10-map-B-pilot','runs/task-v10-transfer']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}:
                add(p)
    # Keep all provenance/challenge attempts, but not repeated draft-build trees.
    for folder in (ROOT/'audit/v10').iterdir():
        if folder.name.startswith(('native-render-draft','main-draft-','main-build-','main-final-','si-build-','si-final-','main-qa-','supplement-qa-','delivery')):
            continue
        candidates = folder.rglob('*') if folder.is_dir() else [folder]
        for p in candidates:
            if p.is_file() and '__pycache__' not in p.parts:
                add(p)
    for name in validation['bound_sha256']:
        add(ROOT/name)
    add(a.validation)
    # Exact final staged TeX inputs/logs are enough; unused copied figures need
    # not be duplicated. QA images are retained in the working tree separately.
    for buildkey,stem in [('main_build','main'),('supplement_build','supplement')]:
        build = ROOT/validation[buildkey]
        for p in build.rglob('*'):
            if p.is_file() and p.suffix in {'.tex','.bib','.bbl','.blg','.aux','.log','.txt','.json'}:
                add(p)
        for name in validation['actual_main_source_files'] if stem=='main' else []:
            add(build/Path(name).relative_to('paper'))
        if stem=='supplement':
            for p in (build/'figs').glob('*.pdf'):
                add(p)
        add(build/(stem+'.pdf'))
    if a.out.resolve() in paths or receipt.resolve() in paths:
        raise ValueError('Archive cannot contain itself')
    members = {p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)}
    manifest = dict(version='assessment-v10-local-review',utc=datetime.now(timezone.utc).isoformat(),
                    baseline_commit=BASE,working_branch=branch,v10_git_commit=None,
                    final_validation=a.validation.resolve().relative_to(ROOT).as_posix(),
                    final_validation_sha256=sha(a.validation),files=members,
                    publication='LOCAL ONLY; no upload, Git commit, tag or Release is performed',
                    exclusions='Git history, external model matrices, dependency caches, credentials, unrelated untracked archives and redundant internal draft builds; this is not an installed full environment',
                    licensing='Project code license does not relicense third-party datasets; see docs/THIRD_PARTY_INPUTS_V10.md')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,meta in members.items():
            data=(ROOT/name).read_bytes()
            if hashlib.sha256(data).hexdigest()!=meta['sha256']:
                raise ValueError('Concurrent mutation while packaging: '+name)
            z.writestr(name,data)
        z.writestr('V10_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    result=dict(archive=a.out.name,bytes=a.out.stat().st_size,sha256=sha(a.out),members=len(members),
                manifest_sha256=hashlib.sha256((json.dumps(manifest,indent=2)+'\n').encode()).hexdigest(),
                final_validation_sha256=sha(a.validation),published=False)
    receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
