"""Build a checked local v9 source/data artifact, never publish or push it."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--validation',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();validation=json.loads(a.validation.read_text())
    if not validation['passed']:raise ValueError('release validation must pass')
    for name,value in validation['bound_sha256'].items():
        if digest((ROOT/name).read_bytes())!=value:raise ValueError(f'changed after validation: {name}')
    paths=set()
    def add(p):
        p=Path(p).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file():raise ValueError(f'invalid artifact path: {p}')
        if p.name in ['Connectivity_783.parquet','Completeness_783.csv']:raise ValueError('external table accidentally bundled')
        paths.add(p)
    def tree(folder,suffixes=None):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and not any(x in p.parts for x in ['__pycache__','.git']) and (
                suffixes is None or p.suffix in suffixes or p.name=='UPSTREAM_LICENSE'):
                add(p)
    for name in ['README.md','REPRODUCE.md','ARTIFACT_README.md','REVIEW_MATERIALS.md',
        'RESEARCH_V9_REPORT_zh.md','FINAL_REVIEW_V9_zh.md','REVISION_V8_REPORT_zh.md',
        'LICENSE','requirements.txt','requirements-v9.txt','requirements-v8-recorded.txt',
        'requirements-historical.txt','sim/data/annotations.tsv']:
        add(ROOT/name)
    for folder in ['sim','sim_vision','tools','tests']:
        for p in (ROOT/folder).glob('*.py'):add(p)
    for p in (ROOT/'tools').glob('*.ps1'):add(p)
    tree('docs',{'.md','.json'})
    for p in (ROOT/'paper').glob('*'):
        if p.is_file() and p.suffix in {'.md','.tex','.bib','.pdf'}:add(p)
    tree('paper/sections',{'.tex'});tree('paper/figs',{'.pdf','.svg','.png'})
    # Full saved episodes, registrations, maps, exact generating snapshots and
    # upstream licenses are small; dependency caches and matrices are elsewhere.
    tree('runs',{'.json','.jsonl','.csv','.md','.py','.log','.txt'})
    tree('sim/results',{'.json','.jsonl','.csv'})
    tree('sim_vision/results_vision',{'.json','.jsonl','.csv'})
    tree('audit/acceptance-v9',{'.json','.jsonl','.csv','.md','.txt','.log','.patch','.py','.tex','.pdf','.svg','.bbl','.blg','.aux'})
    tree('audit/verified-hubs',{'.json','.csv','.md'})
    tree('audit/review-v8-20261022',{'.json','.md','.txt'})
    add(a.validation)
    # Every file directly bound by final validation must be available at its
    # portable repository-relative location, including selected analysis logs.
    for name in validation['bound_sha256']:add(ROOT/name)
    entries={p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in sorted(paths)}
    manifest=dict(version='assessment-v9',created_utc=datetime.now(timezone.utc).isoformat(),
        files=entries,main_pdf_sha256=validation['main_pdf_sha256'],
        supplement_pdf_sha256=validation['supplement_pdf_sha256'],
        validation_file=a.validation.resolve().relative_to(ROOT).as_posix(),
        validation_sha256=digest(a.validation.read_bytes()),published=False,
        external_inputs='Drosophila_brain_model/model.py, Completeness_783.csv and Connectivity_783.parquet; sources and expected hashes are in registrations. Full tables and dependency caches are excluded.',
        scope='Complete 24-cluster core and separate 8-cluster angle stress; independent geometry/input replay is not full neural replication. Local packaging is not public availability or submission.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(paths):z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(a.out) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC failed')
        for name,entry in entries.items():
            if digest(z.read(name))!=entry['sha256']:raise ValueError(f'packaged bytes differ: {name}')
    sidecar=a.out.with_suffix('.manifest.json')
    with sidecar.open('x') as f:json.dump(manifest,f,indent=2)
    receipt=dict(path=str(a.out.resolve()),files=len(entries),bytes=a.out.stat().st_size,
        sha256=digest(a.out.read_bytes()),every_file_sha256_verified=True,published=False)
    with a.out.with_suffix('.receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
