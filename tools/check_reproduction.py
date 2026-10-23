"""Static CLI and input preflight, without importing or running any simulator."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shlex
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sim'))
from project_paths import MODEL_DIR, require_model


def declared_flags(tree):
    """Read literal options and simple string-list option declaration loops."""
    flags=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='add_argument':
            flags.update(arg.value for arg in node.args if isinstance(arg,ast.Constant)
                         and isinstance(arg.value,str) and arg.value.startswith('--'))
        if (isinstance(node,ast.For) and isinstance(node.target,ast.Name)
                and isinstance(node.iter,(ast.List,ast.Tuple))):
            values=[v.value for v in node.iter.elts if isinstance(v,ast.Constant) and isinstance(v.value,str)]
            if len(values)!=len(node.iter.elts):continue
            for statement in node.body:
                for call in ast.walk(statement):
                    if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                            and call.func.attr=='add_argument'):continue
                    for arg in call.args:
                        if (isinstance(arg,ast.BinOp) and isinstance(arg.op,ast.Add)
                                and isinstance(arg.left,ast.Constant) and arg.left.value=='--'
                                and isinstance(arg.right,ast.Name) and arg.right.id==node.target.id):
                            flags.update('--'+value for value in values)
    return flags


def option_supported(option,flags,allow_abbrev=True):
    return option in flags or (allow_abbrev and sum(f.startswith(option) for f in flags)==1)


def check_command(line):
    tokens=shlex.split(line)
    if not tokens or tokens[0] not in ['python','python3']:return None
    i=1
    while i<len(tokens) and tokens[i].startswith('-'):
        if tokens[i]=='-m':return None # pip/unittest module options are not script options
        i+=2 if tokens[i] in ['-X','-W'] else 1
    if i>=len(tokens):return None
    if tokens[i]=='tools/run_v9.py':i+=1
    if i>=len(tokens) or tokens[i]=='-m':return None
    script=tokens[i]
    if not re.match(r'^(sim/|sim_vision/|tools/)\S+\.py$',script):return None
    source=(ROOT/script).resolve()
    if not source.is_relative_to(ROOT) or not source.is_file():raise ValueError(f'missing/invalid script: {script}')
    tree=ast.parse(source.read_text(encoding='utf-8'));flags=declared_flags(tree)
    allow_abbrev=not any(isinstance(n,ast.keyword) and n.arg=='allow_abbrev'
        and isinstance(n.value,ast.Constant) and n.value.value is False for n in ast.walk(tree))
    actual={v.split('=')[0] for v in tokens[i+1:] if v.startswith('--')}
    bad={option for option in actual if not option_supported(option,flags,allow_abbrev)}
    if bad:raise ValueError(f'unsupported or ambiguous CLI flag(s): {bad} in {line}')
    return dict(script=script,flags=sorted(actual),wrapped='tools/run_v9.py' in tokens)


def check_commands():
    checked=[]
    for line in (ROOT/'REPRODUCE.md').read_text(encoding='utf-8').splitlines():
        if not line.startswith(('python ','python3 ')):continue
        result=check_command(line)
        if result:checked.append(result)
    return checked


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--require-model',action='store_true')
    ap.add_argument('--out',type=Path,help='New JSON receipt; existing files are not overwritten')
    args=ap.parse_args()
    result=dict(documented_commands=check_commands(),model_directory=str(MODEL_DIR),
                input_files={f:(MODEL_DIR/f).is_file() for f in ('model.py','Completeness_783.csv','Connectivity_783.parquet')},
                execution='static CLI/input check only; no simulator imports or trials',
                reproduce_sha256=hashlib.sha256((ROOT/'REPRODUCE.md').read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if args.require_model:
        require_model()
    result['passed']=True
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
