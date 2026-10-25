"""Run the lightweight suite once and bind the actual result to tested sources."""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ['tests','sim','sim_vision','tools'] for p in (ROOT/folder).glob('*.py')}
    start=time.perf_counter()
    with (a.out/'unittest.log').open('x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    report=dict(passed=result.wasSuccessful(),tests_run=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        elapsed_seconds=time.perf_counter()-start,utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sources,log_sha256=hashlib.sha256((a.out/'unittest.log').read_bytes()).hexdigest())
    (a.out/'check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
