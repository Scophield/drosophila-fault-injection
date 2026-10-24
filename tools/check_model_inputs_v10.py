"""Read-only exact frozen inputs/runtime preflight; no normalization or trials."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sim'))
from project_paths import MODEL_DIR,PATH_ANN,PATH_COMP,PATH_CON


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--registration',type=Path,required=True)
    ap.add_argument('--runtime',action='store_true')
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();reg=json.loads(a.registration.read_text());errors=[];inputs={}
    for p in [MODEL_DIR/'model.py',PATH_COMP,PATH_CON,PATH_ANN]:
        expected=reg['annotations_sha256'] if p==PATH_ANN else reg['model_inputs_sha256'][p.name]
        actual=sha(p) if p.is_file() else None
        inputs[p.name]=dict(actual_sha256=actual,expected_sha256=expected,matched=actual==expected)
        if actual!=expected:errors.append('missing or different frozen input bytes: '+p.name)
    runtime=None
    if a.runtime:
        packages={}
        for name,expected in reg['runtime']['packages'].items():
            try:actual=importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:actual=None
            packages[name]=actual
            if actual!=expected:errors.append('runtime package: '+name)
        if sys.version!=reg['runtime']['python']:errors.append('Python build/platform differs from frozen runtime')
        runtime=dict(python=sys.version,packages=packages)
    result=dict(passed=not errors,errors=errors,model_directory=str(MODEL_DIR),inputs=inputs,
        runtime=runtime,registration_sha256=sha(a.registration),source_sha256=sha(Path(__file__)),
        scope='Read-only exact input/runtime preflight, no trials. Mismatch requires a labelled replication environment/registration, not silent normalization of generating files.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
