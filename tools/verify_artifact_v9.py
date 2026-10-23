"""Verify a v9 ZIP using only the Python standard library; do not extract it."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import zipfile


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--zip',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();errors=[]
    with zipfile.ZipFile(a.zip) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('duplicate ZIP names')
        bad=z.testzip()
        if bad:errors.append('CRC: '+bad)
        m=json.loads(z.read('MANIFEST.json'));entries=m['files']
        if set(z.namelist())!=set(entries)|{'MANIFEST.json'}:errors.append('unmanifested or missing ZIP entry')
        for name,r in entries.items():
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
                errors.append('unsafe/nonportable member: '+name);continue
            data=z.read(name)
            if len(data)!=r['bytes'] or sha(data)!=r['sha256']:errors.append('byte mismatch: '+name)
        validation_data=z.read(m['validation_file'])
        if sha(validation_data)!=m['validation_sha256']:errors.append('validation binding')
        validation=json.loads(validation_data)
        if not validation['passed']:errors.append('failed validation report')
        for name,value in validation['bound_sha256'].items():
            name=name.replace('\\','/')
            if name not in entries or entries[name]['sha256']!=value:errors.append('validation input not bound: '+name)
        for name,key in [('paper/main.pdf','main_pdf_sha256'),('paper/supplement.pdf','supplement_pdf_sha256')]:
            if sha(z.read(name))!=m[key] or m[key]!=validation[key]:errors.append('PDF binding: '+name)
    result=dict(passed=not errors,errors=errors,files=len(entries),zip_sha256=sha(a.zip.read_bytes()),
        scope='ZIP CRC, every member SHA256/size/path, final-validation inputs and both PDF bindings; does not rerun experiments or infer scientific validity',
        published=m['published'])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
