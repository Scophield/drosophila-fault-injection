"""Package an explicit scientific artifact manifest, excluding caches and private state."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--analysis',type=Path,required=True)
    ap.add_argument('--assessment',type=Path,required=True)
    ap.add_argument('--plots',type=Path,required=True)
    ap.add_argument('--pathway',type=Path,required=True)
    ap.add_argument('--validation',type=Path,required=True)
    ap.add_argument('--prospective',type=Path,required=True)
    ap.add_argument('--prospective-plots',type=Path)
    ap.add_argument('--controls',type=Path)
    ap.add_argument('--horizons',type=Path)
    ap.add_argument('--refractory',type=Path)
    ap.add_argument('--version',default='assessment-v3')
    ap.add_argument('--extra-figures',type=Path,action='append',default=[])
    ap.add_argument('--supplement',type=Path)
    ap.add_argument('--cross',type=Path)
    args=ap.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    validation=json.loads((args.validation/'validation.json').read_text())
    prospective=json.loads(args.prospective.read_text())
    if not validation['passed'] or not prospective['complete']:
        raise ValueError('verification and experiment matrix must be complete')
    for name, expected in validation['source_sha256'].items():
        if digest((ROOT/name).read_bytes()) != expected:
            raise ValueError(f'source changed after validation: {name}')
    if digest((ROOT/'paper/main.pdf').read_bytes()) != validation['pdf_sha256']:
        raise ValueError('paper changed after validation')
    if digest(args.prospective.read_bytes()) != validation['experiment_sha256']:
        raise ValueError('prospective results changed after validation')
    for label,path in [('controls',args.controls),('horizons',args.horizons),('refractory',args.refractory)]:
        if path and digest(path.read_bytes())!=validation[f'{label}_sha256']:
            raise ValueError(f'{label} changed after validation')
    paths=set()
    def add(p):
        p=p.resolve()
        if not p.is_relative_to(ROOT):
            raise ValueError(f'external input cannot be bundled implicitly: {p}')
        if not p.is_file():
            raise FileNotFoundError(p)
        paths.add(p)
    if args.cross:
        cross = json.loads(args.cross.read_text())
        if (not cross['complete'] or not validation.get('cross_audit', {}).get('passed')
                or digest(args.cross.read_bytes()) != validation['cross_audit']['summary_sha256']):
            raise ValueError('cross experiment changed or lacks independent verification')
        for p in ['paper/PROTOCOL_v8.md','REVISION_V8_REPORT_zh.md','docs/revision_v8_plan.md',
                  'paper/fly_connectome_fault_assessment_v8.pdf','paper/fly_connectome_supplement_v8.pdf']:
            add(ROOT/p)
        for directory in [args.cross.parent, ROOT/'audit/cross-audit-v8', ROOT/'runs/controller-fault-v8']:
            for p in directory.rglob('*'):
                if p.is_file() and p.suffix in {'.json','.jsonl','.csv','.md','.py','.log'} and '__pycache__' not in p.parts:
                    add(p)
        add(ROOT/'runs/controller-fault-v8/UPSTREAM_LICENSE')
    for p in ['README.md','ARTIFACT_README.md','REPRODUCE.md','ASSESSMENT_FIX_REPORT.md',
              'REVISION_REPORT.md','REPAIR_REPORT.md','LICENSE',
              'requirements.txt','requirements-historical.txt','paper/README.md',
              'paper/PROTOCOL_v2.md','paper/PROTOCOL_v3.md','paper/main.tex',
              'paper/main.pdf','paper/refs.bib','sim/data/annotations.tsv',
              'tools/build_paper.ps1','audit/verified-analysis/manifest.json']:
        add(ROOT/p)
    if args.controls:
        for p in ['paper/PROTOCOL_v4.md','CONTROL_FIX_REPORT.md']:
            add(ROOT/p)
    if args.supplement:
        sm=json.loads((args.supplement/'supplement_manifest.json').read_text())
        if (digest((ROOT/'paper/supplement.pdf').read_bytes()) != validation['supplement_sha256'] or
                sm['pdf_sha256'] != validation['supplement_sha256']):
            raise ValueError('supplement changed after validation')
        for name, expected in sm['source_sha256'].items():
            path = ROOT/name
            if digest(path.read_bytes()) != expected:
                raise ValueError(f'supplement input changed: {name}')
            add(path)
        for p in ['paper/supplement.pdf','REVIEW_MATERIALS.md','EDITORIAL_FIX_REPORT.md','SUBMISSION_FIX_REPORT.md']:
            add(ROOT/p)
        if args.version in {'assessment-v7','assessment-v8'}:
            add(ROOT/'OVERVIEW_FIGURE_REPORT.md')
        for p in (ROOT/'audit/verified-hubs').glob('*.json'):
            add(p)
        for p in args.supplement.rglob('*'):
            if p.is_file() and p.suffix in {'.tex','.pdf','.png','.json','.txt','.log'}:
                add(p)
    for folder,pattern in [('paper/sections','*.tex'),('sim','*.py'),('sim_vision','*.py'),
                           ('tools','*.py'),('tests','*.py')]:
        for p in (ROOT/folder).glob(pattern): add(p)
    for tex in [ROOT/'paper/main.tex']+list((ROOT/'paper/sections').glob('*.tex')):
        for name in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',tex.read_text()):
            add(ROOT/'paper'/name)
    for directory in [args.analysis,args.assessment,args.plots,args.pathway,args.validation]:
        files = directory.rglob('*') if directory == args.validation else directory.glob('*')
        for p in files:
            if p.is_file() and p.suffix in {'.json','.csv','.txt','.pdf','.png'}: add(p)
    if args.prospective_plots:
        plot_manifest = json.loads((args.prospective_plots/'prospective_plot_manifest.json').read_text())
        if (plot_manifest['summary_sha256'] != digest(args.prospective.read_bytes()) or
                plot_manifest['script_sha256'] != digest((ROOT/'tools/plot_prospective.py').read_bytes())):
            raise ValueError('prospective figure inputs changed')
        for p in args.prospective_plots.glob('*'):
            if p.is_file() and p.suffix in {'.json','.pdf','.png'}: add(p)
    for p in [args.prospective,ROOT/'runs/simulator-v3/validation.json',
              ROOT/'runs/task-reference-v3/reference.json',
              ROOT/'runs/geometry-v3/vision/calib-geometry-v3.json']:
        add(p)
    for p in (ROOT/'runs/geometry-v3/vision').rglob('*.json'): add(p)
    for path in [args.controls,args.horizons,args.refractory]:
        if path:
            add(path)
            for p in path.parent.glob('*'):
                if p.is_file() and p.suffix in {'.json','.csv','.md'}: add(p)
    if args.controls:
        for root in ['runs/controller-v4a','runs/refractory-v4']:
            add(ROOT/root/'UPSTREAM_LICENSE')
            for p in (ROOT/root).rglob('*'):
                if p.is_file() and p.suffix in {'.json','.jsonl','.py','.log'} and '__pycache__' not in p.parts:
                    add(p)
    for directory in args.extra_figures:
        for p in directory.glob('*'):
            if p.is_file() and p.suffix in {'.pdf','.svg','.png','.json'}: add(p)
    for analysis in [json.loads((args.analysis/'revision_analysis.json').read_text()),
                     json.loads((args.assessment/'assessment.json').read_text())]:
        for p,expected in analysis['manifest']['source_sha256'].items():
            path=ROOT/p
            if digest(path.read_bytes())!=expected:
                raise ValueError(f'archive changed: {p}')
            add(path)
    entries={str(p.relative_to(ROOT)).replace('\\','/'):dict(sha256=digest(p.read_bytes()),bytes=p.stat().st_size)
             for p in sorted(paths)}
    manifest=dict(version=args.version,files=entries,remote_published=False,
                  pdf_sha256=digest((ROOT/'paper/main.pdf').read_bytes()),
                   supplement_sha256=validation.get('supplement_sha256'),
                  external_dependencies='Connectome and completeness tables remain external; see REPRODUCE.md',
                  scope='Archive sensitivity and focused prospective evaluation; no acceptance or hardware certification')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(paths): z.write(p,str(p.relative_to(ROOT)).replace('\\','/'))
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(args.out) as z:
        if z.testzip() is not None:
            raise ValueError('zip CRC verification failed')
        for name,entry in entries.items():
            if digest(z.read(name))!=entry['sha256']:
                raise ValueError(f'packaged byte mismatch: {name}')
    sidecar=args.out.with_suffix('.manifest.json')
    with sidecar.open('x') as f: json.dump(manifest,f,indent=2)
    print(json.dumps(dict(path=str(args.out),files=len(entries),bytes=args.out.stat().st_size,
                         sha256=digest(args.out.read_bytes()),verified=True),indent=2))


if __name__=='__main__':
    main()
