"""Transmission-only re-scoring of records, not execution of external FI tools."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_archive import load, summarize, protocols


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--core',type=Path,default=ROOT/'sim/results/real')
    ap.add_argument('--controls',type=Path,action='append',help='repeat for separate control directories')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    controls=args.controls or [ROOT/'sim_vision/results_vision/openloop_controls']
    result=protocols(args.core,controls,summarize(load(args.core/'healthy.jsonl')))
    files=[args.core/'healthy.jsonl']+[Path(c['source']) if Path(c['source']).is_absolute() else ROOT/c['source'] for c in result['conditions']]
    result['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as f:
        json.dump(result,f,indent=2)
    print(f"{result['transmission_only_pass']}/{result['trials']} transmission; {result['envelope_pass']}/{result['trials']} joint")


if __name__=='__main__':
    main()
