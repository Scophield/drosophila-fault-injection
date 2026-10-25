"""Check local Markdown targets, including case errors hidden by Windows.

Read-only. Remote access/licensing is separately verified; this is not a web
availability crawler. Historical documents can be audited without editing them.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]


def check_document(document):
    problems=[];checked=0
    for lineno,line in enumerate(document.read_text(encoding='utf-8').splitlines(),1):
        for raw in re.findall(r'\]\(([^)]+)\)',line):
            target=raw.split(' "',1)[0].strip('<> ')
            parsed=urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:continue
            target=unquote(parsed.path).replace('\\','/');current=ROOT if target.startswith('/') else document.parent
            mismatched=False;missing=False
            for part in target.strip('/').split('/'):
                if part in ['', '.']:continue
                if part=='..':current=current.parent;continue
                if not current.is_dir():missing=True;break
                names={p.name:p for p in current.iterdir()}
                if part in names:current=names[part];continue
                candidates=[p for n,p in names.items() if n.casefold()==part.casefold()]
                if len(candidates)==1:current=candidates[0];mismatched=True
                else:missing=True;break
            checked+=1
            if missing or not current.exists():kind='missing target'
            elif not current.resolve().is_relative_to(ROOT):kind='target outside repository'
            elif mismatched:kind='case-sensitive URL would fail'
            else:continue
            problems.append(dict(document=document.relative_to(ROOT).as_posix(),line=lineno,target=raw,
                problem=kind,suggested_relative_target=None if missing else os.path.relpath(current,document.parent).replace('\\','/')))
    return checked,problems


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--files',nargs='+',type=Path,default=[Path('README.md'),Path('REPRODUCE.md'),Path('docs/REPRODUCE_V10.md'),Path('docs/EVIDENCE_INTERFACE_V10.md'),Path('docs/THIRD_PARTY_INPUTS_V10.md')])
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    issues=[];count=0
    for p in a.files:
        n,bad=check_document(p.resolve());count+=n;issues.extend(bad)
    result=dict(passed=not issues,local_targets_checked=count,issues=issues,
        documents_sha256={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in a.files},
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Local target existence, repository boundary and URL case; no remote availability or license assertion')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
    if issues:raise SystemExit(1)


if __name__=='__main__':main()
