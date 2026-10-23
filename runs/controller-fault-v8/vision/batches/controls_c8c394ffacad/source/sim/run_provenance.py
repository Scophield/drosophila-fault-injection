"""Require an explicit run tree; refuse accidental archive writes and mixed resumes."""
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from project_paths import ROOT, MODEL_DIR, PATH_COMP, PATH_CON, PATH_ANN


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def code_hash():
    paths = sorted(list((ROOT/'sim').glob('*.py')) + list((ROOT/'sim_vision').glob('*.py')))
    return hashlib.sha256(''.join(f'{p.relative_to(ROOT)}:{sha256(p)}\n' for p in paths).encode()).hexdigest()


def run_root():
    value = os.environ.get('FLY_RUN_DIR')
    if not value:
        raise ValueError('Set FLY_RUN_DIR to a NEW run directory; archived outputs are read-only')
    root = Path(value).expanduser().resolve()
    for archive in (ROOT/'sim/results',ROOT/'sim_vision/results_vision',ROOT/'audit'):
        if root == archive or archive in root.parents:
            raise ValueError('FLY_RUN_DIR must not be inside an archive or audit directory')
    return root


def output_dir(component):
    return run_root()/component


def prepare(out, parameters, resume=False):
    out = Path(out).resolve()
    if run_root() not in out.parents:
        raise ValueError('all new results must be inside FLY_RUN_DIR')
    versions = {}
    for package in ('numpy','brian2','pandas','pyarrow','matplotlib','scipy','Cython','joblib'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    brian = sys.modules.get('brian2')
    runtime_backend = str(brian.prefs.codegen.target) if brian is not None else None
    current = dict(code_sha256=code_hash(), parameters=parameters, neural_dt_ms=0.1,
                   runtime_backend=runtime_backend, sensory_refractory_ms=2.2,
                   model_inputs={str(p.relative_to(MODEL_DIR)):sha256(p) for p in
                                 (MODEL_DIR/'model.py',PATH_COMP,PATH_CON) if p.is_file()},
                   git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                   python=sys.version, packages=versions,
                   annotations_sha256=sha256(PATH_ANN),
                   stimulus_note='fault seeds traceable; unseeded open-loop Poisson stream is not bit-identical on resume')
    sources = {str(p.relative_to(ROOT)):p for folder in ('sim','sim_vision')
               for p in sorted((ROOT/folder).glob('*.py'))}
    sources['external/model.py'] = MODEL_DIR/'model.py'
    current['source_sha256'] = {name:sha256(p) for name,p in sources.items()}
    current['hardware'] = dict(system=platform.system(), release=platform.release(),
                               processor=platform.processor(), logical_cpus=os.cpu_count())
    marker=out/'run_manifest.json'
    if out.exists() and any(out.iterdir()):
        if not resume or not marker.is_file() or json.loads(marker.read_text()) != current:
            raise ValueError(f'nonempty or incompatible run directory: {out}; use a new FLY_RUN_DIR')
    else:
        out.mkdir(parents=True,exist_ok=True)
        for name,p in sources.items():
            target=out/'source'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(p.read_bytes())
        marker.write_text(json.dumps(current,indent=2)+'\n')
    for name,expected in current['source_sha256'].items():
        if sha256(out/'source'/name) != expected:
            raise ValueError(f'generating source snapshot mismatch: {name}')
    return out
