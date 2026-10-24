"""Compare every inherited Git file with the pre-V10 byte manifest.

Only explicit current-entry/manuscript updates are permitted. Historical raw,
registrations, generating sources and named PDFs have no exception. This is a
read-only check; it never restores, deletes or normalizes a file.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '43bcd4d6a99b2d9b258cf8a198a4545d237b5c39'
ALLOWED_UPDATES = {
    'README.md', 'REPRODUCE.md', 'ARTIFACT_README.md', 'REVIEW_MATERIALS.md',
    'GITHUB_SNAPSHOT.md', 'docs/STATE.md', 'paper/README.md', 'paper/refs.bib',
    'paper/main.tex', 'paper/main.pdf', 'paper/supplement.tex',
    'paper/supplement.pdf', 'tools/check_reproduction.py',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    before = json.loads(a.baseline.read_text())
    if before['commit'] != BASE or len(before['files']) != 3992:
        raise ValueError('Expected the complete pre-V10 3992-file V9 manifest')
    protected, changed, errors = {}, {}, []
    for name, expected in before['files'].items():
        p = (ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file():
            errors.append('Missing or unsafe inherited path: '+name)
            continue
        actual = sha(p)
        if actual != expected:
            changed[name] = dict(before=expected, after=actual)
            if name not in ALLOWED_UPDATES:
                errors.append('Protected inherited bytes changed: '+name)
        if name not in ALLOWED_UPDATES:
            protected[name] = actual
    report = dict(
        passed=not errors, errors=errors, baseline_commit=BASE,
        baseline_manifest_sha256=sha(a.baseline), inherited_files_checked=3992,
        utc=datetime.now(timezone.utc).isoformat(),
        allowed_current_entry_and_paper_changes=changed,
        files_sha256=protected, checker_sha256=sha(Path(__file__)),
        scope='Inherited-file byte preservation, not a scientific validity check; no file mutation',
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'files_sha256'}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
