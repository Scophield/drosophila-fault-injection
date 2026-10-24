"""Reanalyse/replay immutable V9 records in an explicitly selected checkout.

No connectome, neural simulator, old dependency cache or network is required.
Use a new environment with requirements-saved-v10.txt. This validates saved
evidence on the current host, not neural resimulation or cross-host identity.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

V9 = '43bcd4d6a99b2d9b258cf8a198a4545d237b5c39'
KEYS = ('records', 'seed_clusters', 'counts', 'cluster_effects',
        'interaction_raw_p', 'interaction_holm_p', 'activity_ratios',
        'horizon_sensitivity', 'warning_scores', 'thresholds', 'raw_input_sha256')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--checkout', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    checkout, out = a.checkout.resolve(), a.out.resolve()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    if commit != V9:
        raise ValueError('Expected the immutable full V9 research commit: ' + V9)
    if (checkout/'tmp/v9-deps').exists():
        raise ValueError('Remove dependency-cache ambiguity: select a fresh checkout without tmp/v9-deps')
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    tasks = [
        ('analysis', ['tools/analyze_task_v9_exportfix.py', '--root', 'runs/task-v9-test',
                      '--registration', 'runs/task-v9-frozen/registration-core.json']),
        ('replay', ['tools/replay_audit_v9.py', '--root', 'runs/task-v9-test',
                    '--calibration', 'runs/task-v9-frozen/calibration.json'])]
    commands = []
    for name, args in tasks:
        cmd = [sys.executable, '-I', '-X', 'utf8', 'tools/run_v9.py', *args, '--out', str(out/name)]
        with (out/(name+'.log')).open('x', encoding='utf-8') as log:
            result = subprocess.run(cmd, cwd=checkout, stdout=log, stderr=subprocess.STDOUT)
        commands.append(dict(command=cmd, cwd=str(checkout), exit_code=result.returncode))
        if result.returncode:
            raise RuntimeError('Saved-data operation failed; inspect '+str(out/(name+'.log')))
    original = json.loads((checkout/'audit/acceptance-v9/core-v2/summary.json').read_text())
    actual = json.loads((out/'analysis/summary.json').read_text())
    equal = {k: original[k] == actual[k] for k in KEYS}
    replay = json.loads((out/'replay/replay.json').read_text())
    report = dict(passed=all(equal.values()) and replay['passed'] and replay['records'] == 288,
                  utc=datetime.now(timezone.utc).isoformat(), source_commit=commit,
                  clean_dependency_install=True, dependency_cache_reused=False,
                  python=sys.version, executable=sys.executable,
                  packages={p: importlib.metadata.version(p) for p in ['numpy', 'setuptools']},
                  quantitative_keys_identical=equal, records_replayed=replay['records'],
                  commands=commands, seconds=time.perf_counter()-started,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='Fresh remote checkout and isolated dependency install on the same host; saved-record analysis/input/geometry replay only. No neural resimulation or independent host.')
    (out/'check.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'commands'}, indent=2))
    if not report['passed']:
        raise RuntimeError('Saved results differ from the public reference')


if __name__ == '__main__':
    main()
