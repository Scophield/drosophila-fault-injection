"""Prepare a curated, byte-preserving public layer; NEVER publish or use Git.

Scientific ancestry is the full V9 research baseline. Distribution is a clean
export, not that history: unknown-license annotation/transformed tables and
private Blender projects stay outside the new publication layer. Recorded
author-generated input configurations and simulation traces are retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--paper-build',type=Path,required=True)
    ap.add_argument('--plot-root',type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve()
    for p in [ROOT/'paper/refs.bib',*(ROOT/'paper/sections').glob('v10f_*.tex')]:
        staged=a.paper_build/p.relative_to(ROOT/'paper')
        if not staged.is_file() or sha(p)!=sha(staged):
            raise ValueError('Paper build does not match current source: '+str(p))
    if sha(a.paper_build/'main.tex')!=sha(ROOT/'paper/main_v10_final4.tex'):
        raise ValueError('The selected4figure manuscript must match its actual staged source')
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    chosen=set()
    def add(p):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.pyo']:
            chosen.add(p.resolve())
    for folder in ['tools','sim','sim_vision','tests','evidence_v10','examples']:
        for p in (ROOT/folder).glob('*.py'):add(p)
    for p in (ROOT/'tools').glob('*.ps1'):add(p)
    for name in ['EVIDENCE_INTERFACE_V10.md','THIRD_PARTY_INPUTS_V10.md',
                 'V10_ANALYSIS_NOTES.md','V10_CAPABILITY_COMPARISON.md',
                 'V10_ERROR_CASES.md','V10_DATA_INDEX.md',
                 'PUBLIC_REPRODUCE_V10_FINAL.md','V10_FINAL_FIGURE_CONTRACT.md',
                 'V10_FINAL_CHANGELOG.md']:
        add(ROOT/'docs'/name)
    for p in (ROOT/'paper/sections').glob('v10f_*.tex'):add(p)
    for p in (ROOT/'paper').glob('main_v10_final*.tex'):add(p)
    for p in (ROOT/'paper').glob('PROTOCOL_v9*.md'):add(p)
    for p in [ROOT/'paper/refs.bib',ROOT/'LICENSE',ROOT/'requirements-v9.txt',ROOT/'requirements-saved-v10.txt']:add(p)
    for name in ['evidence_v10_overview.pdf','v10f_reuse.pdf','v10f_rf.pdf','v10f_warning.pdf','v10f_reuse_warning.pdf']:add(ROOT/'paper/figs'/name)
    # Original bytes, including frozen generating snapshots. These directories
    # contain our code/configuration/outputs, plus MIT upstream model.py copies;
    # no annotation dump or connectivity/completeness table is selected.
    for pattern in ['task-v9-*','task-v10-*']:
        for folder in (ROOT/'runs').glob(pattern):
            for p in folder.rglob('*'):add(p)
    audit_folders=[
        'audit/acceptance-v9/core-v2','audit/acceptance-v9/stress-v2',
        'audit/acceptance-v9/causal','audit/acceptance-v9/baseline',
        'audit/v10/transfer-01','audit/v10/evidence-05',
        'audit/v10/legacy-timing-01','audit/v10/tests-final',
        'audit/v10/calibration-check-01','audit/v10/rf-design-02',
        'audit/v10/decoder-baseline-02','audit/v10/clean-install-replay-01',
        'audit/v10/clean-additional-01']
    for folder in audit_folders:
        for p in (ROOT/folder).rglob('*'):
            if p.suffix in ['.json','.csv','.py','.txt','.log']:add(p)
    # Include the actual72-record historical probe, not all unknown legacy data.
    hist=json.loads((ROOT/'audit/v10/legacy-timing-01/check.json').read_text())
    for item in hist['all_records']:
        name=item.get('path',item.get('file'))
        if name:add(ROOT/name)
    for p in a.plot_root.rglob('*'):add(p)
    add(ROOT/'audit/v10-final/public-checks.json')
    # The plotter validates graph context from the locked PDF; no source tables
    # or Blender project are needed to rebuild the main LaTeX document.
    forbidden=[]
    for p in sorted(chosen):
        if p.name in ['annotations.tsv','Connectivity_783.parquet','Completeness_783.csv'] or p.suffix.lower() in ['.blend','.blend1','.parquet']:
            forbidden.append(str(p));continue
        rel=p.relative_to(ROOT);dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dst)
    if forbidden:raise ValueError('Disallowed selection: '+repr(forbidden))
    # Preserve upstream MIT notices for every allowed external/model.py snapshot.
    notice=ROOT/'audit/blender-integration-20261023/source/UPSTREAM_MODEL_LICENSE.txt'
    if not notice.is_file():notice=ROOT.parent/'blender_drosophila/UPSTREAM_MODEL_LICENSE.txt'
    (out/'THIRD_PARTY_LICENSES').mkdir()
    shutil.copyfile(notice,out/'THIRD_PARTY_LICENSES/model-MIT.txt')
    for name in ['main.tex','main.pdf']:
        shutil.copyfile(a.paper_build/name,out/'paper'/name)
    shutil.copyfile(a.paper_build/'main.pdf',out/'paper/fly_connectome_fault_assessment_v10_final.pdf')
    shutil.copyfile(ROOT/'docs/PUBLIC_REPRODUCE_V10_FINAL.md',out/'README.md')
    (out/'.gitattributes').write_text('* -text\n',encoding='utf-8')
    (out/'.gitignore').write_text('__pycache__/\n*.pyc\n.venv/\n/tmp/\n/output/\n',encoding='utf-8')
    omissions=[]
    for name in ['sim/data/annotations.tsv']:
        p=ROOT/name
        omissions.append(dict(path=name,sha256=sha(p),reason='annotation-dump redistribution terms unresolved; obtain pinned upstream separately',source='https://github.com/flyconnectome/flywire_annotations/blob/a83b2776d60d5764cef36b927f5f9679c16c47a2/supplemental_files/Supplemental_file1_neuron_annotations.tsv'))
    reg=json.loads((ROOT/'runs/task-v9-frozen/registration-core.json').read_text())
    for name,h in reg['model_inputs_sha256'].items():
        if name=='model.py':continue
        omissions.append(dict(path='external/'+name,sha256=h,reason='external transformed input; redistribution terms not established',source='https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960'))
    manifest=dict(status='PREPARED_LOCAL_NOT_PUBLISHED',scientific_baseline='43bcd4d6a99b2d9b258cf8a198a4545d237b5c39',
        distribution='Curated clean export; no inherited V9 Git history, external tables, caches, credentials or private Blender projects.',
        omitted=omissions,
        generating_source='Frozen batch snapshots and original run metadata retain their generation-time parent HEAD; a later publication commit must not be backfilled.',
        attribution='Underlying FlyWire v783 data: DOI10.5281/zenodo.10676866(CC-BY4.0). Model code copies:MIT Philip Shiu/Nico Spiller, notice in THIRD_PARTY_LICENSES. Generated configs/observations are experimental outputs, not a relicensing of source datasets.',
        files={p.relative_to(out).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()})
    (out/'PUBLIC_SCOPE.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(prepared=str(out),files=len(manifest['files']),MiB=round(sum(q['bytes'] for q in manifest['files'].values())/2**20,2),published=False,omitted_tables=[q['path'] for q in omissions]),indent=2))


if __name__=='__main__':main()
