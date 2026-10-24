"""Run the complete lightweight regression suite with a source-bound receipt."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    with (a.out/'tests.log').open('x', encoding='utf-8') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    paths = {Path(__file__).resolve()}
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            p = Path(name).resolve()
            if p.is_file() and p.is_relative_to(ROOT) and p.suffix == '.py' and 'tmp' not in p.relative_to(ROOT).parts:
                paths.add(p)
    report = dict(
        passed=result.wasSuccessful() and not result.skipped,
        tests_run=result.testsRun, skipped=len(result.skipped),
        failures=len(result.failures), errors=len(result.errors),
        utc=datetime.now(timezone.utc).isoformat(), seconds=time.perf_counter()-start,
        python=sys.version, source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},
        log_sha256=sha(a.out/'tests.log'),
        scope='Executed lightweight regression tests and source hashes of loaded local Python modules; not full neural resimulation or proof of untested code paths.',
    )
    (a.out/'check.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}, indent=2))
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
