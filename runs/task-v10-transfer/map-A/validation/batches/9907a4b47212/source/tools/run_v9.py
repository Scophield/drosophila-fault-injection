"""Bootstrap the isolated CPython 3.12 environment; never import v8 CP313 wheels."""
from pathlib import Path
import os
import runpy
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tmp/v9-deps'), str(ROOT/'sim'), str(ROOT/'sim_vision')]
os.environ['PYTHONPATH'] = os.pathsep.join(sys.path[:3])
tempfile.tempdir = str(ROOT/'tmp')
os.environ.update(FLY_CODEGEN_TARGET='numpy', OMP_NUM_THREADS='1',
                 OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
import _distutils_hack
_distutils_hack.add_shim()
target = sys.argv[1]
sys.argv = sys.argv[1:]
if target == '-':
    exec(compile(sys.stdin.read(), '<stdin>', 'exec'), {'__name__': '__main__'})
elif target == '-m':
    target = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_module(target, run_name='__main__', alter_sys=True)
else:
    sys.path.insert(0, str((ROOT/target).parent))
    runpy.run_path(target, run_name='__main__')
