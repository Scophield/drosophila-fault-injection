"""Complete the frozen controller-by-deletion matrix, preserving healthy inputs."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runs/controller-v4a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()
    out = args.out.resolve()
    if ROOT / 'runs' not in out.parents:
        raise ValueError('output must be a new directory under runs/')
    manifests = list((SOURCE / 'vision/batches').glob('*/run_manifest.json'))
    if len(manifests) != 3:
        raise ValueError('expected three original healthy generation manifests')
    for path in manifests:
        manifest = json.loads(path.read_text())
        for name, expected in manifest['source_sha256'].items():
            if sha(path.parent / 'source' / name) != expected:
                raise ValueError(f'corrupt healthy source snapshot: {name}')
            if not name.startswith('external/') and sha(ROOT / name) != expected:
                raise ValueError(f'neural source changed since healthy generation: {name}')
        for package, expected in manifest['packages'].items():
            if importlib.metadata.version(package) != expected:
                raise ValueError(f'package version differs from healthy generation: {package}')
    reused = [p for p in (SOURCE / 'vision/episodes_controls').glob('*.json')
              if json.loads(p.read_text())['mode'] in ('brain', 'precue_gated')]
    if len(reused) != 24:
        raise ValueError('expected 24 frozen healthy episodes')
    config = dict(seeds=list(range(12, 18)), phis=[-30, 30],
                  modes=['brain', 'precue_gated'], faults=[None, 'F2_25', 'F2_50'],
                  new_faults=['F2_25', 'F2_50'], horizon_ms=1000,
                  analysis='paired loss, gain, net loss, controller interaction; same-law healthy activity',
                  selection='six existing held-out seed clusters; no outcome-based exclusions',
                  reused_healthy={str(p.relative_to(ROOT)): sha(p) for p in reused},
                  runner_sha256=sha(Path(__file__)))
    if args.resume:
        if json.loads((out / 'campaign.json').read_text()) != config:
            raise ValueError('campaign configuration changed')
    else:
        out.mkdir(parents=True, exist_ok=False)
        vision = out / 'vision'
        vision.mkdir()
        shutil.copyfile(SOURCE / 'vision/calib-frozen.json', vision / 'calib-frozen.json')
        shutil.copytree(SOURCE / 'vision/episodes_calibration', vision / 'episodes_calibration')
        shutil.copytree(SOURCE / 'vision/batches', vision / 'batches')
        (vision / 'episodes_controls').mkdir()
        for p in reused:
            shutil.copyfile(p, vision / 'episodes_controls' / p.name)
        (out / 'campaign.json').write_text(json.dumps(config, indent=2) + '\n')
    env = os.environ.copy()
    env.update(FLY_RUN_DIR=str(out), FLY_CODEGEN_TARGET='numpy', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    env['PATH'] = r'C:\Program Files\Git\cmd' + os.pathsep + env.get('PATH', '')
    search = [str(ROOT / 'sim_vision'), str(ROOT / 'sim')]
    search += [str(Path(p).resolve()) for p in sys.path if p]
    code = ('import sys; sys.path[:0]=' + repr(search)
            + '; import _distutils_hack; _distutils_hack.add_shim(); '
            + 'import runpy; runpy.run_path("sim_vision/run_closedloop.py",run_name="__main__")')
    started = time.time()
    workers = []
    for i, seeds in enumerate(('12,13', '14,15', '16,17')):
        log = (out / f'worker-{i}.log').open('a' if args.resume else 'x')
        command = [sys.executable, '-u', '-c', code, '--tag', 'controls', '--modes',
                   'brain,precue_gated', '--phis=-30,30', '--seeds', seeds,
                   '--faults', 'F2_25,F2_50', '--duration-ms', '1000',
                   '--calibration', str(out / 'vision/calib-frozen.json')]
        if args.resume:
            command.append('--resume')
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        workers.append((process, log))
    (out / 'active.json').write_text(json.dumps(dict(started_unix=started,
        worker_pids=[p.pid for p, _ in workers], parent_pid=os.getpid()), indent=2) + '\n')
    while any(p.poll() is None for p, _ in workers):
        time.sleep(2)
    for _, log in workers:
        log.close()
    result = dict(exit_codes=[p.returncode for p, _ in workers], workers=len(workers),
                  wall_seconds=time.time() - started, started_unix=started,
                  completed_unix=time.time(), runner_sha256=sha(Path(__file__)))
    (out / 'execution.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    if any(result['exit_codes']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
