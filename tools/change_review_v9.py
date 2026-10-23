"""Review this task's source changes relative to the inherited dirty baseline."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def sha(data):return hashlib.sha256(data).hexdigest()


def in_scope(name):
    p=Path(name)
    if p.suffix not in {'.py','.ps1','.tex','.bib','.md','.txt'} and p.name!='.gitignore':return False
    return (len(p.parts)==1 or p.parts[0] in ['sim','sim_vision','tools','tests','paper','docs']) and not any(
        part in ['__pycache__','results','results_vision','history','data'] for part in p.parts)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline',type=Path,required=True,help='Baseline folder containing workspace.zip and manifest.json')
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();baseline=json.loads((a.baseline/'manifest.json').read_text())
    old={r['path'].replace('\\','/'):r for r in baseline['files'] if in_scope(r['path'])}
    current={p.relative_to(ROOT).as_posix():p for folder in ['sim','sim_vision','tools','tests','paper','docs']
        for p in (ROOT/folder).rglob('*') if p.is_file() and in_scope(p.relative_to(ROOT).as_posix())}
    current.update({p.name:p for p in ROOT.glob('*') if p.is_file() and in_scope(p.name)})
    rows=[];patch=[]
    with zipfile.ZipFile(a.baseline/'workspace.zip') as z:
        for name in sorted(set(old)|set(current)):
            before=z.read(name) if name in old else b'';after=current[name].read_bytes() if name in current else b''
            if before==after:continue
            rows.append(dict(file=name,status='modified' if name in old and name in current else 'added' if name in current else 'deleted',
                before_sha256=sha(before) if name in old else None,after_sha256=sha(after) if name in current else None,
                before_bytes=len(before),after_bytes=len(after)))
            try:
                left=before.decode('utf-8').splitlines(keepends=True);right=after.decode('utf-8').splitlines(keepends=True)
            except UnicodeDecodeError:continue
            patch.extend(difflib.unified_diff(left,right,fromfile='a/'+name,tofile='b/'+name))
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'source-review.patch').write_text(''.join(patch),encoding='utf-8')
    report=dict(baseline_branch=baseline['branch'],baseline_head=baseline['head'],files=rows,
        note='Diff against the inherited dirty workspace, not just Git HEAD. Raw experiments are indexed separately and not rewritten. Existing user changes are preserved.',
        patch_sha256=sha((a.out/'source-review.patch').read_bytes()))
    (a.out/'changes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(changed_source_documents=len(rows),deleted=[r['file'] for r in rows if r['status']=='deleted'],patch_bytes=(a.out/'source-review.patch').stat().st_size),indent=2))


if __name__=='__main__':main()
