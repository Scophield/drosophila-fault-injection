"""Verify the saved repair, immutable archive, staged build and regression behavior."""
import argparse
from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'sim')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--analysis', type=Path, required=True)
    ap.add_argument('--plots', type=Path, required=True)
    ap.add_argument('--pathway', type=Path)
    ap.add_argument('--experiment', type=Path)
    ap.add_argument('--controls',type=Path)
    ap.add_argument('--horizons',type=Path)
    ap.add_argument('--refractory',type=Path)
    ap.add_argument('--prospective-plots',type=Path)
    ap.add_argument('--horizon-plots',type=Path)
    ap.add_argument('--control-plots',type=Path)
    ap.add_argument('--supplement',type=Path)
    ap.add_argument('--overview',type=Path)
    ap.add_argument('--cross',type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    errors = []

    with (args.out / 'tests.txt').open('x', encoding='utf-8') as handle:
        result = unittest.TextTestRunner(stream=handle, verbosity=2).run(
            unittest.defaultTestLoader.discover(str(ROOT / 'tests')))
    if not result.wasSuccessful() or result.testsRun < 23:
        errors.append('regression suite failed or fewer than 23 checks ran')

    analysis = json.loads(args.analysis.read_text())
    prior = json.loads((ROOT / 'audit/verified-analysis/manifest.json').read_text())
    source_hashes = dict(prior['source_sha256'])
    source_hashes.update(analysis['manifest']['source_sha256'])
    changed = [p for p, expected in source_hashes.items() if digest(ROOT / p) != expected]
    if changed:
        errors.append('archived input hashes changed')
    git_diff = subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--',
                              'sim/results', 'sim_vision/results_vision'],
                             cwd=ROOT, capture_output=True, text=True)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--',
                                        'sim/results', 'sim_vision/results_vision'],
                                       cwd=ROOT, text=True).splitlines()
    if git_diff.returncode or untracked:
        errors.append('historical directory differs from tracked archive')

    plots = json.loads((args.plots / 'plot_manifest.json').read_text())
    plot_mismatches = [p for p, expected in plots['source_sha256'].items()
                       if digest(ROOT / p) != expected]
    if digest(ROOT / 'tools/plot_revision.py') != plots['script_sha256']:
        plot_mismatches.append('tools/plot_revision.py')
    for name in ('revision_curves', 'revision_activity', 'revision_demo'):
        if digest(args.plots / f'{name}.pdf') != digest(ROOT / 'paper/figs' / f'{name}.pdf'):
            plot_mismatches.append(name)
    if plot_mismatches:
        errors.append('publication plot source or output provenance mismatch')
    if digest(ROOT / 'tools/audit_revision.py') != analysis['manifest']['script_sha256']:
        errors.append('archive analysis script changed since saved analysis')
    pathway_mismatches = []
    if args.pathway:
        from project_paths import MODEL_DIR
        pathway = json.loads((args.pathway/'pathway_manifest.json').read_text())
        for name, expected in pathway['sources'].items():
            path = Path(name)
            if path.is_absolute() and not path.is_relative_to(ROOT):
                path = MODEL_DIR/path.name
            elif not path.is_absolute():
                path = ROOT/path
            if digest(path) != expected:
                pathway_mismatches.append(name)
        if digest(args.pathway/'fig0_pathway.pdf') != digest(ROOT/'paper/figs/fig0_pathway.pdf'):
            pathway_mismatches.append('paper/figs/fig0_pathway.pdf')
        if pathway_mismatches:
            errors.append('pathway figure provenance mismatch')

    overview_mismatches = []
    if args.overview:
        om = json.loads((args.overview/'overview_manifest.json').read_text())
        for name, expected in om['source_sha256'].items():
            if digest(ROOT/name) != expected:
                overview_mismatches.append(name)
        for name, expected in om['output_sha256'].items():
            if digest(args.overview/name) != expected:
                overview_mismatches.append(name)
        if digest(args.overview/'assessment_overview.pdf') != digest(ROOT/'paper/figs/assessment_overview.pdf'):
            overview_mismatches.append('paper/figs/assessment_overview.pdf')
        if not om['schematic_only'] or om['simulations_executed'] or om['text_outside_canvas']:
            overview_mismatches.append('overview scope or geometry')
        if overview_mismatches:
            errors.append('overview source, output or geometry mismatch')

    sources = [ROOT / 'paper/main.tex', ROOT / 'paper/refs.bib']
    sources += sorted((ROOT / 'paper/sections').glob('*.tex'))
    main_text = sources[0].read_text()
    for fig in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',
                          '\n'.join(p.read_text() for p in sources if p.suffix == '.tex')):
        sources.append(ROOT / 'paper' / fig)
    staged_changes = [str(p.relative_to(ROOT)) for p in sources
                      if digest(p) != digest(args.build / p.relative_to(ROOT / 'paper'))]
    if staged_changes or digest(ROOT / 'paper/main.pdf') != digest(args.build / 'main.pdf'):
        errors.append('paper differs from its staged compiled sources')
    log = (args.build / 'main.log').read_text(errors='replace')
    bad_log = re.findall(r'[^\n]*(?:undefined|Overfull \\[hv]box|Missing character:)[^\n]*', log)
    if bad_log:
        errors.append('LaTeX log has undefined citations, overflow or missing glyphs')
    bbl = (args.build / 'main.bbl').read_text()
    cited = set()
    for source in sources:
        if source.suffix == '.tex':
            for group in re.findall(r'\\cite\{([^}]+)\}', source.read_text()):
                cited.update(group.split(','))
    bibitems = set(re.findall(r'\\bibitem\{([^}]+)\}', bbl))
    if cited != bibitems or not cited:
        errors.append('compiled bibliography differs from manuscript citations')
    if 'Shuchao Gao' not in main_text or 'Waseda University' not in main_text:
        errors.append('author information changed')

    import qa_pdf
    with (args.out / 'pdf-qa-output.json').open('x', encoding='utf-8') as handle:
        with redirect_stdout(handle), patch.object(sys, 'argv', ['qa_pdf.py', '--pdf',
                str(ROOT / 'paper/main.pdf'), '--out', str(args.out / 'pdf')]):
            qa_pdf.main()
    qa = json.loads((args.out / 'pdf/qa.json').read_text())
    errors.extend(qa_pdf.submission_errors(qa))
    with pymupdf.open(ROOT / 'paper/main.pdf') as pdf:
        reference_only = qa_pdf.references_only_fifth_page(pdf)
        letter = all(abs(page.rect.width - 612) < .01 and abs(page.rect.height - 792) < .01
                     for page in pdf)
    if not reference_only:
        errors.append('page five must contain references only (no technical content or figures)')
    if (qa['pages'] != 5 or not letter or qa['type3'] or qa['unembedded']
            or qa['outside_page'] or (ROOT / 'paper/main.pdf').stat().st_size > 5_000_000):
        errors.append('PDF pagination, font or geometry check failed')

    documents = ['REVISION_REPORT.md', 'ASSESSMENT_FIX_REPORT.md', 'ARTIFACT_README.md', 'REPRODUCE.md', 'README.md', 'paper/README.md',
                 'paper/PROTOCOL_v2.md', 'paper/PROTOCOL_v3.md', 'requirements.txt', 'requirements-historical.txt']
    if args.overview:
        documents+=['OVERVIEW_FIGURE_REPORT.md']
    if args.controls:
        documents+=['paper/PROTOCOL_v4.md','CONTROL_FIX_REPORT.md']
    supplement_sha256 = None
    if args.supplement:
        manifest_path = args.supplement/'supplement_manifest.json'
        sm = json.loads(manifest_path.read_text())
        if sm['generator_sha256'] != digest(ROOT/'tools/build_supplement_v5.py'):
            errors.append('supplement generator changed')
        if any(digest(ROOT/name) != expected for name,expected in sm['source_sha256'].items()):
            errors.append('supplement input changed')
        supplement_sha256 = digest(ROOT/'paper/supplement.pdf')
        if (sm['pdf_sha256'] != supplement_sha256 or
                digest(args.supplement/'supplement.pdf') != supplement_sha256 or
                sm['tex_sha256'] != digest(args.supplement/'supplement.tex') or sm['latex_problems']):
            errors.append('supplement differs from compiled sources')
        for name in sm['source_sha256']:
            if name.endswith('.pdf') and digest(args.supplement/'figures'/Path(name).name) != digest(ROOT/name):
                errors.append('staged supplement figure changed')
        with (args.out/'supplement-qa-output.json').open('x') as handle:
            with redirect_stdout(handle), patch.object(sys,'argv',['qa_pdf.py','--pdf',
                    str(ROOT/'paper/supplement.pdf'),'--out',str(args.out/'supplement')]):
                qa_pdf.main()
        sq=json.loads((args.out/'supplement/qa.json').read_text())
        if sq['type3'] or sq['unembedded'] or sq['outside_page'] or qa_pdf.submission_errors(sq):
            errors.append('supplement font, geometry or PDF feature problem')
        documents+=['paper/supplement.pdf','REVIEW_MATERIALS.md','EDITORIAL_FIX_REPORT.md','SUBMISSION_FIX_REPORT.md']
        tracked_selectors = sorted((ROOT/'audit/verified-hubs').glob('*.json'))
        if len(tracked_selectors) != 8:
            errors.append('selector reconstruction evidence is incomplete')
        sources += tracked_selectors
    code = [p for folder in ('sim', 'sim_vision', 'tools', 'tests')
            for p in (ROOT / folder).glob('*.py')]
    tracked_outputs = sources + code + [ROOT / p for p in documents]
    cross_audit = None
    if args.cross:
        from analyze_controller_fault_v8 import analyze as analyze_cross
        from audit_cross_v8 import check_cross
        cross = json.loads(args.cross.read_text())
        if analyze_cross(ROOT/'runs/controller-fault-v8') != cross:
            errors.append('cross-factorial summary does not reproduce')
        cross_audit = check_cross(args.cross)
        errors.extend(cross_audit['errors'])
        cross_plot = ROOT/'audit/cross-figures-v8-final'
        pm = json.loads((cross_plot/'plot_manifest.json').read_text())
        if (pm['summary_sha256'] != digest(args.cross)
                or pm['script_sha256'] != digest(ROOT/'tools/plot_controller_fault_v8.py')
                or any(digest(cross_plot/name) != value for name,value in pm['output_sha256'].items())):
            errors.append('factorial figure provenance mismatch')
        tracked_outputs += [args.cross, ROOT/'paper/PROTOCOL_v8.md', ROOT/'REVISION_V8_REPORT_zh.md']
    experiment = json.loads(args.experiment.read_text()) if args.experiment else None
    if experiment and not experiment.get('complete'):
        errors.append('prospective experiment matrix is incomplete')
    if experiment:
        from summarize_prospective import summarize
        recomputed = summarize(ROOT / experiment['experiment_root'],
                               ROOT / experiment['calibration_path'],
                               experiment['test_seed_clusters'],experiment['azimuths'],
                               experiment['modes'],experiment['faults'])
        if recomputed != experiment:
            errors.append('prospective summary differs from its raw inputs or manifests')
    controls=json.loads(args.controls.read_text()) if args.controls else None
    if controls:
        from analyze_controls_v4 import analyze as analyze_controls
        if not controls.get('complete') or analyze_controls()!=controls:
            errors.append('controller campaign summary does not reproduce')
    horizons=json.loads(args.horizons.read_text()) if args.horizons else None
    if horizons:
        from analyze_horizons_v4 import analyze as analyze_horizons
        if analyze_horizons()!=horizons:
            errors.append('horizon analysis does not reproduce')
    refractory=json.loads(args.refractory.read_text()) if args.refractory else None
    if refractory and (not refractory.get('complete') or len(refractory['trials'])!=12 or
                       refractory.get('neurons')!=138639 or refractory.get('connections')!=15091983):
        errors.append('refractory experiment incomplete or wrong network')
    if args.refractory:
        from analyze_refractory_v4 import analyze as analyze_refractory
        saved=ROOT/'audit/refractory-v4/summary.json'
        if not saved.is_file() or analyze_refractory()!=json.loads(saved.read_text()):
            errors.append('refractory paired analysis does not reproduce')
    for directory,manifest_name,source,script,figure in [
            (args.prospective_plots,'prospective_plot_manifest.json',args.experiment,'plot_prospective.py','prospective_outcomes'),
            (args.horizon_plots,'manifest.json',args.horizons,'plot_horizons_v4.py','late_hubs'),
            (args.control_plots,'manifest.json',args.controls,'plot_controls_v4.py',None)]:
        if directory:
            m=json.loads((directory/manifest_name).read_text())
            expected=m.get('summary_sha256',m.get('source_sha256'))
            if expected!=digest(source) or m['script_sha256']!=digest(ROOT/'tools'/script):
                errors.append(f'{script} figure inputs changed')
            if figure and digest(directory/f'{figure}.pdf')!=digest(ROOT/'paper/figs'/f'{figure}.pdf'):
                errors.append(f'{figure} output differs from manuscript')
    manuscript='\n'.join(p.read_text() for p in sources if p.suffix=='.tex')
    if args.controls and any(s in manuscript for s in ('campaign is running','must be inserted','TODO','TBD')):
        errors.append('unresolved manuscript placeholder')
    summary = dict(passed=not errors, errors=errors,
                    cross_audit=cross_audit,
                   tests=dict(run=result.testsRun, failures=len(result.failures),
                              errors=len(result.errors), skipped=len(result.skipped)),
                   archived_sources_checked=len(source_hashes), changed_raw_sources=changed,
                   archive_git_diff_exit=git_diff.returncode, archive_untracked=untracked,
                   plot_source_mismatches=plot_mismatches, staged_source_mismatches=staged_changes,
                    pathway_source_mismatches=pathway_mismatches,
                    overview_mismatches=overview_mismatches,
                    pdf_sha256=digest(ROOT / 'paper/main.pdf'),
                   pdf_bytes=(ROOT / 'paper/main.pdf').stat().st_size,
                   pdf_pages=qa['pages'], font_count=len(qa['fonts']),
                   type3_count=len(qa['type3']), unembedded_count=len(qa['unembedded']),
                    pdf_version=qa['pdf_version'], encrypted=qa['encrypted'],
                    links=sum(qa['links_per_page']), bookmarks=qa['bookmarks'],
                    widgets=sum(qa['widgets_per_page']), form_fields=qa['form_fields'],
                   references_only_page_five=reference_only, citations=len(cited),
                   latex_log_errors=bad_log,
                   analysis=str(args.analysis), plots=str(args.plots), build=str(args.build),
                    source_sha256={str(p.resolve().relative_to(ROOT)): digest(p) for p in tracked_outputs},
                   experiment_sha256=digest(args.experiment) if args.experiment else None,
                   controls_sha256=digest(args.controls) if args.controls else None,
                   horizons_sha256=digest(args.horizons) if args.horizons else None,
                   refractory_sha256=digest(args.refractory) if args.refractory else None,
                    supplement_sha256=supplement_sha256,
                   simulations_executed=False,
                   saved_neural_campaign_complete=bool(experiment and experiment.get('complete')),
                   regression_scope='synthetic-input behavior plus immutable archive reanalysis',
                   visual_review='rendered pages require separate human/model inspection')
    (args.out / 'validation.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'source_sha256'}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
