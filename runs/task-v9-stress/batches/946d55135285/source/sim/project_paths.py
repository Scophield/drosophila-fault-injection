"""Portable input locations. Set FLY_MODEL_DIR for any non-sibling checkout."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(os.environ.get('FLY_MODEL_DIR', ROOT.parent / 'Drosophila_brain_model')).expanduser().resolve()
PATH_COMP = MODEL_DIR / 'Completeness_783.csv'
PATH_CON = MODEL_DIR / 'Connectivity_783.parquet'
PATH_ANN = ROOT / 'sim/data/annotations.tsv'


def require_model():
    missing = [str(p) for p in (MODEL_DIR/'model.py', PATH_COMP, PATH_CON) if not p.is_file()]
    if missing:
        raise FileNotFoundError('Missing upstream model inputs (set FLY_MODEL_DIR): ' + ', '.join(missing))
    return MODEL_DIR
