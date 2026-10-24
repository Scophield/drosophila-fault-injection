"""Overlay an audited visual revision on the verified v9 scientific archive.

Keep the preceding archive intact. All historical experiment/analysis bytes
must agree; only presentation/source/document paths may differ.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path,PurePosixPath
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(data):return hashlib.sha256(data).hexdigest()


def presentation(name):
    p=PurePosixPath(name)
    return (p.parts[0] in ['paper','docs','tools'] or len(p.parts)==1 and p.suffix=='.md')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['base','validation','extra','out']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();validation=json.loads(a.validation.read_text())
    if not validation['passed']:raise ValueError('final validation must pass')
    for name,h in validation['bound_sha256'].items():
        if digest((ROOT/name).read_bytes())!=h:raise ValueError('changed after validation: '+name)
    data={}
    with zipfile.ZipFile(a.base) as z:
        if z.testzip():raise ValueError('preceding archive CRC failed')
        before=json.loads(z.read('MANIFEST.json'))
        if set(z.namelist())!=set(before['files'])|{'MANIFEST.json'}:raise ValueError('base membership differs')
        for name,q in before['files'].items():
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:raise ValueError('unsafe base path')
            value=z.read(name)
            if len(value)!=q['bytes'] or digest(value)!=q['sha256']:raise ValueError('base bytes differ: '+name)
            current=ROOT/name
            if current.is_file() and digest(current.read_bytes())!=q['sha256'] and not presentation(name):
                raise ValueError('historical non-presentation file changed: '+name)
            data[name]=value
    def add(path):
        path=path.resolve()
        if not path.is_relative_to(ROOT):raise ValueError('outside repository')
        name=path.relative_to(ROOT).as_posix()
        if path.name in ['Connectivity_783.parquet','Completeness_783.csv']:raise ValueError('external matrix')
        data[name]=path.read_bytes()
    for folder,exts in [('paper',{'.tex','.bib','.md','.pdf','.svg','.png'}),
                        ('docs',{'.md','.json'}),('tools',{'.py','.ps1'})]:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and p.suffix in exts and '__pycache__' not in p.parts:add(p)
    for p in ROOT.glob('*.md'):add(p)
    for p in a.extra.rglob('*'):
        if p.is_file() and p.suffix in {'.json','.csv','.md','.txt','.log','.patch','.py','.tex','.pdf','.svg','.png','.blend','.bbl','.blg','.aux'}:add(p)
    add(a.validation)
    for name in validation['bound_sha256']:add(ROOT/name)
    entries={name:dict(bytes=len(value),sha256=digest(value)) for name,value in sorted(data.items())}
    manifest=dict(before,version='assessment-v9-visual',created_utc=datetime.now(timezone.utc).isoformat(),
        files=entries,main_pdf_sha256=validation['main_pdf_sha256'],supplement_pdf_sha256=validation['supplement_pdf_sha256'],
        validation_file=a.validation.resolve().relative_to(ROOT).as_posix(),validation_sha256=digest(a.validation.read_bytes()),
        base_source_archive_sha256=digest(a.base.read_bytes()),published=False,
        scope='Visual revision of the same v9 data/protocol. All preceding archive members retained, presentation paths updated, raw experiment/analysis bytes unchanged. Intermediate builds are not the final manuscript.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,value in sorted(data.items()):z.writestr(name,value)
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with a.out.with_suffix('.manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    receipt=dict(path=str(a.out.resolve()),files=len(entries),bytes=a.out.stat().st_size,
        sha256=digest(a.out.read_bytes()),base_archive_sha256=manifest['base_source_archive_sha256'],published=False)
    with a.out.with_suffix('.receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
