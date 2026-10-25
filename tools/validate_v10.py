"""Bind V10 PDFs to protected V9 evidence, complete RF tests, checks and visual QA.

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
    for name in ['main-build','supplement-build','main-qa','supplement-qa','main-native','supplement-native','tests','preservation','visual','out']:
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();errors=[];bound={}
    def read(p):
        p=Path(p).resolve();bound[p.relative_to(ROOT).as_posix()]=sha(p)
        return json.loads(p.read_text())
    def require(ok,message):
        if not ok:errors.append(message)
    require(sha(ROOT/'paper/REVIEW_2026-10-23_V9.txt')=='2481583e6bd9fa2039c37ace00f4731b070efd5e08b92497ce4bde5dc81481f9','V9 review bytes changed')
    require(read(ROOT/'audit/v10/model-input-preflight-01.json')['passed'],'exact input/runtime preflight failed')
    require(read(ROOT/'audit/v10/upstream-access/model-input-origin-resolved.json')['passed'],'external input origin unresolved')
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
    design=read(ROOT/'runs/task-v10-design/design.json')
    require(read(ROOT/'audit/v10/calibration-check-01/check.json')['passed'],'development-only calibration reconstruction failed')
    completed=read(ROOT/'runs/task-v10-transfer/completed.json')
    transfer=read(ROOT/'audit/v10/transfer-01/summary.json')
    require(completed['expected_episodes']==392 and completed['design_sha256']==sha(ROOT/'runs/task-v10-design/design.json'),'RF campaign not complete/source bound')
    require(transfer['complete'] and len(transfer['maps'])==2,'RF analysis incomplete')
    require(transfer['source_sha256']==sha(ROOT/'tools/aggregate_transfer_v10.py'),'RF collector changed after analysis')
    require(transfer['design_sha256']==sha(ROOT/'runs/task-v10-design/design.json'),'RF design changed after analysis')
    require(len(transfer['secondary_interaction_holm_p'])==4,'secondary family must span both maps and both doses')
    for spec in design['maps']:
        tag=spec['map_id'];base=ROOT/('runs/task-v10-transfer/map-'+tag);folder=ROOT/('audit/v10/transfer-01/map-'+tag)
        reg=read(base/'registration.json');summary=read(folder/'analysis/summary.json')
        cal=read(base/'calibration.json')
        require(reg['calibration_sha256']==sha(base/'calibration.json'),'RF calibration changed')
        for name,h in cal['input_sha256'].items():
            require(sha(ROOT/name)==h,'RF development record changed: '+name);bound[name]=h
        require(reg['test_seeds']==spec['test_seeds'] and len(reg['test_seeds'])==12,'RF seed cohort changed')
        require(reg['rf_map_sha256']==spec['sha256'],'RF map binding changed')
        require(summary['complete'] and summary['records']==144 and summary['seed_clusters']==12,'RF paired test matrix incomplete')
        require(summary['analysis_source_sha256']==sha(ROOT/'tools/analyze_task_v10.py'),'registered RF analyzer changed')
        require(summary['registration_sha256']==sha(base/'registration.json'),'RF registration changed')
        for name,h in {**reg['frozen_source_sha256'],**summary['raw_input_sha256'],**reg['validation_input_sha256']}.items():
            require(sha(ROOT/name)==h,'RF raw/frozen input changed: '+name);bound[name]=h
        for relative in ['numbers/check.json','replay/replay.json','evidence.json']:
            require(read(folder/relative)['passed'],'RF verification failed: '+tag+'/'+relative)
    require(read(ROOT/'audit/v10/transfer-01/rf-input-binding.json')['passed'],'RF-to-input binding failed')
    require(read(ROOT/'audit/v10/transfer-01/independent-score-check.json')['passed'],'independent RF primary/warning arithmetic failed')
    challenge=read(ROOT/'audit/v10/evidence-05/check.json')
    require(challenge['passed'] and challenge['clean_records']=={'fly':288,'tank':96},'cross-plant evidence challenge incomplete')
    for adapter,cases in challenge['corruption_cases'].items():
        require(len(cases)==14 and all(q['detected'] for q in cases),'corruption challenge failed: '+adapter)
    require(read(ROOT/'audit/v10/clean-install-replay-01/check.json')['passed'],'fresh core replay failed')
    extra=read(ROOT/'audit/v10/clean-additional-01/check.json')
    require(extra['passed'] and extra['total_including_previously_verified_core']==448,'fresh additional replay failed')
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
    cli=read(ROOT/'audit/v10/reproduction-preflight-final.json')
    require(cli['passed'] and len(cli['documented_commands'])>=20,'documented CLI preflight failed')
    require(cli['reproduce_sha256']==sha(ROOT/'REPRODUCE.md'),'reproduction document changed after CLI preflight')
    require(cli['script_sha256']==sha(ROOT/'tools/check_reproduction.py'),'CLI checker changed after preflight')
    for name,h in cli['reproduction_documents_sha256'].items():
        require(sha(ROOT/name)==h,'reproduction entry changed after preflight: '+name);bound[name]=h
    require(read(ROOT/'audit/v10/document-links-final.json')['passed'],'current documentation link check failed')
    test=read(a.tests);preservation=read(a.preservation);visual=read(a.visual)
    require(test['passed'] and test['tests_run']>=79 and test['skipped']==0,'test suite failed, incomplete or skipped')
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
        native=read((a.main_native if label=='main' else a.supplement_native)/'check.json')
        require(native['passed'] and native['pdf_sha256']==h and native['pages']==qa['pages'],f'{label} native rendering/font check stale or failed')
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
    require('V10_PENDING' not in (ROOT/'paper/main.tex').read_text(),'unfinished main draft')
    tex_sources(ROOT/'paper/main.tex');actual_sources.add(ROOT/'paper/refs.bib')
    require(all('V10_PENDING' not in p.read_text() for p in actual_sources if p.suffix=='.tex'),'unfinished main section')
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
        validator_sha256=sha(Path(__file__)),
        main_build=a.main_build.resolve().relative_to(ROOT).as_posix(),
        supplement_build=a.supplement_build.resolve().relative_to(ROOT).as_posix(),
        main_pdf_sha256=sha(ROOT/'paper/main.pdf'),supplement_pdf_sha256=sha(ROOT/'paper/supplement.pdf'),
        bound_sha256=bound,actual_main_source_files=sorted(p.relative_to(ROOT).as_posix() for p in actual_sources),
        core_clusters=24,stress_clusters_separate=8,independent_core_stress_records=384,
        rf_clusters_conditional_per_map=12,rf_maps=2,rf_test_records=288,
        secondary_causal_clusters_separate=8,secondary_causal_records=64,
        publication='V10 is a local checked working snapshot; no V10 public commit or Release is authenticated by this report.',
        limitations='Consistency and layout checks do not validate RF realism, neural-state correctness, physical faults, hardware benefits or acceptance. Same-prior maps with separate calibration/cohorts do not isolate an RF causal effect. Historical missing manifests remain unresolved.')
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='bound_sha256'},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
