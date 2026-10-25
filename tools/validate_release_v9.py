"""Bind the final PDFs to sources, complete tests, measurements and visual QA.

These checks establish artifact consistency, not scientific generalization,
hardware certification, acceptance, or submission-portal certification.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['main-build','supplement-build','main-qa','supplement-qa','tests','preservation','visual','out']:
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();errors=[];bound={}
    def read(p):
        p=Path(p).resolve();bound[p.relative_to(ROOT).as_posix()]=sha(p)
        return json.loads(p.read_text())
    def require(ok,message):
        if not ok:errors.append(message)
    for label,count in [('core',288),('stress',96)]:
        summary=read(ROOT/f'audit/acceptance-v9/{label}-v2/summary.json')
        regpath=ROOT/f'runs/task-v9-frozen/registration-{label}.json';reg=read(regpath)
        require(summary['complete'] and summary['records']==count,f'{label} matrix incomplete')
        require(summary['registration_sha256']==sha(regpath),f'{label} registration changed')
        analyzer=ROOT/'tools/analyze_task_v9_exportfix.py'
        require(summary['analysis_source_sha256']==sha(analyzer),f'{label} corrected analyzer changed')
        bound[analyzer.relative_to(ROOT).as_posix()]=sha(analyzer)
        require(reg['calibration_sha256']==sha(ROOT/'runs/task-v9-frozen/calibration.json'),f'{label} calibration changed')
        for name,value in reg['validation_input_sha256'].items():
            require(sha(ROOT/name)==value,f'healthy validation changed: {name}');bound[name]=value
        for name,value in summary['raw_input_sha256'].items():
            require(sha(ROOT/name)==value,f'raw record changed: {name}')
            bound[name.replace('\\','/')]=value
        for name,value in reg['frozen_source_sha256'].items():
            require(sha(ROOT/name)==value,f'frozen source changed: {name}')
            bound[name]=value
        replay=read(ROOT/f'audit/acceptance-v9/replay-{label}/replay.json')
        numbers=read(ROOT/f'audit/acceptance-v9/numbers-{label}/check.json')
        require(replay['passed'] and numbers['passed'],f'{label} independent audit failed')
        require(replay['audit_source_sha256']==sha(ROOT/'tools/replay_audit_v9.py'),f'{label} replay code changed')
        require(numbers['summary_sha256']==sha(ROOT/f'audit/acceptance-v9/{label}-v2/summary.json'),f'{label} arithmetic report stale')
    calibration=read(ROOT/'runs/task-v9-frozen/calibration.json')
    comparison=read(ROOT/'audit/acceptance-v9/warning-comparisons-core/comparisons.json')
    require(comparison['metrics_sha256']==sha(ROOT/'audit/acceptance-v9/core-v2/metrics.csv'),'paired warning comparison stale')
    require(comparison['source_sha256']==sha(ROOT/'tools/compare_warnings_v9.py'),'paired warning code changed')
    diagnostic=read(ROOT/'audit/acceptance-v9/control-diagnostic-core-v2/diagnostic.json')
    require(diagnostic['source_sha256']==sha(ROOT/'tools/diagnose_control_v9.py'),'control diagnostic code changed')
    for name,value in calibration['input_sha256'].items():
        p=ROOT/'runs/task-v9-development/episodes'/name
        require(sha(p)==value,f'decoder development changed: {name}');bound[p.relative_to(ROOT).as_posix()]=value
    causal=read(ROOT/'audit/acceptance-v9/causal/summary.json')
    causal_reg=read(ROOT/'runs/task-v9-frozen/registration-causal.json')
    causal_replay=read(ROOT/'audit/acceptance-v9/replay-causal/replay.json')
    require(causal['complete'] and causal['records']==64 and causal_replay['passed'] and causal_replay['records']==64,'causal diagnostic incomplete or failed replay')
    require(causal['registration_sha256']==sha(ROOT/'runs/task-v9-frozen/registration-causal.json'),'causal registration changed')
    for name,value in causal['raw_input_sha256'].items():
        require(sha(ROOT/name)==value,f'causal raw changed: {name}');bound[name]=value
    for name,value in causal_reg['frozen_source_sha256'].items():
        require(sha(ROOT/name)==value,f'causal frozen source changed: {name}');bound[name]=value
    cli=read(ROOT/'audit/acceptance-v9/reproduction-preflight.json')
    require(cli['passed'] and len(cli['documented_commands'])>=20,'documented CLI preflight failed')
    require(cli['reproduce_sha256']==sha(ROOT/'REPRODUCE.md'),'reproduction document changed after CLI preflight')
    require(cli['script_sha256']==sha(ROOT/'tools/check_reproduction.py'),'CLI checker changed after preflight')
    test=read(a.tests);preservation=read(a.preservation);visual=read(a.visual)
    require(test['passed'] and test['tests_run']>=59 and test['skipped']==0,'test suite failed, incomplete or skipped')
    for name,value in test['source_sha256'].items():
        require(sha(ROOT/name)==value,f'code changed after final tests: {name}')
        bound[name]=value
    require(preservation['passed'],'baseline experimental records changed')
    for name,value in preservation['files_sha256'].items():
        require(sha(ROOT/name)==value,f'inherited experimental file changed: {name}')
    require(visual.get('passed') is True,'visual review not completed')
    for label,qa_dir,pdf in [('main',a.main_qa,ROOT/'paper/main.pdf'),
                             ('supplement',a.supplement_qa,ROOT/'paper/supplement.pdf')]:
        qa=read(qa_dir/'qa.json');h=sha(pdf);bound[pdf.relative_to(ROOT).as_posix()]=h
        require(qa['pdf_sha256']==h,f'{label} QA stale')
        require(not qa['type3'] and not qa['unembedded'],f'{label} fonts invalid')
        require(not qa['outside_page'],f'{label} text outside page')
        require(visual[label+'_pdf_sha256']==h,f'{label} visual review stale')
        require(visual[label+'_pages_checked']==list(range(1,qa['pages']+1)),f'{label} not every page visually reviewed')
        if label=='main':
            require(qa['pages']<=5 and qa['references_only_fifth_page'],'main exceeds four technical pages / fifth references-only rule')
            require(not qa['submission_feature_errors'],'main has prohibited PDF features')
            require(all(abs(r[2]-612)<1 and abs(r[3]-792)<1 for r in qa['page_sizes']),'main not US letter')
            require(pdf.stat().st_size<5_000_000,'main PDF exceeds 5 MB')
    require(sha(a.main_build/'main.pdf')==sha(ROOT/'paper/main.pdf'),'main PDF differs from build')
    require(sha(a.supplement_build/'supplement.pdf')==sha(ROOT/'paper/supplement.pdf'),'supplement PDF differs from build')
    require(sha(a.supplement_build/'supplement.tex')==sha(ROOT/'paper/supplement.tex'),'supplement TeX differs from build')
    actual_sources=set()
    def tex_sources(p):
        p=p.resolve()
        if p in actual_sources:return
        actual_sources.add(p);text=p.read_text()
        for name in re.findall(r'\\input\{([^}]+)\}',text):
            q=ROOT/'paper'/name
            tex_sources(q if q.suffix else q.with_suffix('.tex'))
        for name in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',text):
            q=ROOT/'paper'/name;actual_sources.add(q.resolve())
    tex_sources(ROOT/'paper/main.tex');actual_sources.add(ROOT/'paper/refs.bib')
    for p in actual_sources:
        name=p.relative_to(ROOT/'paper');require(sha(p)==sha(a.main_build/name),f'main build source differs: {name}')
        bound[p.relative_to(ROOT).as_posix()]=sha(p)
    sm=read(a.supplement_build/'manifest.json')
    require(not sm['latex_problems'],'supplement LaTeX diagnostics failed')
    require(sm['pdf_sha256']==sha(ROOT/'paper/supplement.pdf'),'supplement manifest stale')
    for name,value in sm['source_sha256'].items():
        require(sha(ROOT/name)==value,f'supplement input changed: {name}');bound[name]=value
    for build,stem in [(a.main_build,'main'),(a.supplement_build,'supplement')]:
        log=(build/(stem+'.log')).read_text(errors='replace')
        require(not re.search(r'Citation .+ undefined|Reference .+ undefined|There were undefined|Overfull \\[hv]box|Float too large|Missing character:',log),f'{stem} unresolved reference/overflow/glyph')
    aux=(a.main_build/'main.aux').read_text();bbl=(a.main_build/'main.bbl').read_text()
    citations={x for group in re.findall(r'\\citation\{([^}]+)\}',aux) for x in group.split(',')} - {'IEEEcontrol'}
    items=set(re.findall(r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}',bbl))
    require(citations<=items,f'missing bibliography entries: {sorted(citations-items)}')
    report=dict(passed=not errors,errors=errors,utc=datetime.now(timezone.utc).isoformat(),
        main_pdf_sha256=sha(ROOT/'paper/main.pdf'),supplement_pdf_sha256=sha(ROOT/'paper/supplement.pdf'),
        bound_sha256=bound,actual_main_source_files=sorted(p.relative_to(ROOT).as_posix() for p in actual_sources),
        core_clusters=24,stress_clusters_separate=8,independent_core_stress_records=384,
        secondary_causal_clusters_separate=8,secondary_causal_records=64,
        limitations='Consistency and layout checks do not validate the assumed RF map, neural-state correctness, physical faults, hardware benefits or acceptance. Historical missing manifests remain unresolved.')
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='bound_sha256'},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
