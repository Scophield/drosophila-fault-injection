"""Verify a local V10 ZIP without extraction or third-party dependencies.

Checks exact members, safe names, CRC, hashes, sizes and PDF/source validation
bindings. A consistent archive is not authenticated execution or public access.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    with zipfile.ZipFile(a.archive) as z:
        names = z.namelist()
        if len(set(names)) != len(names):
            raise ValueError('Duplicate ZIP members')
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe member name')
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        manifest_bytes = z.read('V10_MANIFEST.json')
        manifest = json.loads(manifest_bytes)
        if set(names) != set(manifest['files']) | {'V10_MANIFEST.json'}:
            raise ValueError('Undeclared or missing ZIP members')
        for name,meta in manifest['files'].items():
            data = z.read(name)
            if len(data) != meta['bytes'] or digest(data) != meta['sha256']:
                raise ValueError('Member bytes/hash mismatch: '+name)
        raw = z.read(manifest['final_validation'])
        if digest(raw) != manifest['final_validation_sha256']:
            raise ValueError('Final validation binding mismatch')
        validation = json.loads(raw)
        if not validation['passed']:
            raise ValueError('Final validation failed')
        for name,h in validation['bound_sha256'].items():
            if digest(z.read(name)) != h:
                raise ValueError('Final source/data binding mismatch: '+name)
        for name,field in [('paper/main.pdf','main_pdf_sha256'),('paper/supplement.pdf','supplement_pdf_sha256')]:
            if digest(z.read(name)) != validation[field]:
                raise ValueError('Final PDF binding mismatch')
    report = dict(passed=True,archive_sha256=digest(a.archive.read_bytes()),
                  manifest_sha256=digest(manifest_bytes),members=len(manifest['files']),
                  published=False,neural_resimulation=False,
                  scope='Local ZIP integrity and source/data/PDF consistency only; no execution authentication, license grant, public availability, portal acceptance or scientific generalization claim.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
