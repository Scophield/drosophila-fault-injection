"""Build V10 SI from complete source-bound baseline and RF evidence; no imputation."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import statistics

WARNING_NAMES={'transmission':'Command criterion','stop_count_upper':'Own-stop upper',
    'equal_duration_upper':'Activity upper','equal_duration_two_sided':'Activity two-sided',
    'schedule_only':'Actuator-schedule forecast','deadline':'Held-command forecast'}


def effect_label(name):
    if name.endswith('_interaction'):
        return name.replace('_interaction','').replace('F2_','')+'% R minus P (secondary)'
    for mode,short in [('proportional','P'),('relay','R')]:
        if name.startswith(mode+'_F2_'):
            return short+', '+name.split('_')[2]+'% net loss (derived)'
    return name


ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def esc(s):
    m={'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#',
       '{':r'\{','}':r'\}','$':r'\$','^':r'\textasciicircum{}','~':r'\textasciitilde{}'}
    return ''.join(m.get(c,c) for c in str(s))


def number(v,digits=3):return '--' if v is None else f'{v:.{digits}f}'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--core',type=Path,required=True)
    ap.add_argument('--stress',type=Path,required=True)
    ap.add_argument('--causal',type=Path,default=ROOT/'audit/acceptance-v9/causal')
    ap.add_argument('--figures',type=Path,required=True)
    ap.add_argument('--development-figure',type=Path,
        default=ROOT/'audit/acceptance-v9/development-figures-v3/development_v9.pdf')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--transfer',type=Path,required=True)
    ap.add_argument('--evidence',type=Path,required=True)
    ap.add_argument('--tank-figure',type=Path,default=ROOT/'audit/v10/tank-figure-03/tank_v10.pdf')
    ap.add_argument('--warning-figure',type=Path,default=ROOT/'audit/v10/baseline-figures-02/task_v10_warnings.pdf')
    ap.add_argument('--main-source',type=Path,default=ROOT/'paper/main_v10.tex')
    args=ap.parse_args(); sources={}
    def remember(path):
        path=Path(path).resolve()
        sources[path.relative_to(ROOT).as_posix()]=sha(path)
    def read(path):
        path=Path(path);remember(path)
        return json.loads(path.read_text())
    def records(summary):
        rows=[]
        for name,value in summary['raw_input_sha256'].items():
            p=ROOT/name
            if sha(p)!=value:raise ValueError(f'raw measurement changed: {name}')
            sources[name]=value;rows.append(json.loads(p.read_text()))
        return rows
    transfer=read(args.transfer/'summary.json');evidence=read(args.evidence)
    access=read(ROOT/'audit/v10/clean-install-replay-01/check.json')
    additional_access=read(ROOT/'audit/v10/clean-additional-01/check.json')
    if not additional_access['passed'] or additional_access['total_including_previously_verified_core']!=448:raise ValueError('additional clean replay incomplete')
    score_check=read(args.transfer/'independent-score-check.json')
    if not score_check['passed']:raise ValueError('independent RF warning/primary arithmetic failed')
    calibration_check=read(ROOT/'audit/v10/calibration-check-01/check.json')
    if not calibration_check['passed']:raise ValueError('independent development-only calibration check failed')
    decoder=read(ROOT/'audit/v10/decoder-baseline-02/summary.json')
    if not transfer['complete'] or len(transfer['maps'])!=2 or not evidence['passed'] or not access['passed']:raise ValueError('V10 evidence incomplete')
    core=read(args.core/'summary.json');stress=read(args.stress/'summary.json')
    causal=read(args.causal/'summary.json')
    if not core['complete'] or core['records']!=288 or not stress['complete'] or stress['records']!=96:
        raise ValueError('complete 288-record core and 96-record stress analyses required')
    if not causal['complete'] or causal['records']!=64:raise ValueError('complete separate 64-record action check required')
    cr=read(ROOT/'runs/task-v9-frozen/registration-core.json')
    sr=read(ROOT/'runs/task-v9-frozen/registration-stress.json')
    ar=read(ROOT/'runs/task-v9-frozen/registration-causal.json')
    cal=read(ROOT/'runs/task-v9-frozen/calibration.json')
    development={}
    for name,expected in [('task-v9-development',20),('task-v9-validation',6),
                          ('task-v9-validation-B',32),('task-v9-fault-screen',16)]:
        rr=[read(p) for p in sorted((ROOT/'runs'/name/'episodes').glob('*.json'))]
        if len(rr)!=expected:raise ValueError(f'incomplete development history: {name}')
        development[name]=rr
    if sum(r['escaped'] for r in development['task-v9-validation-B'])!=32:
        raise ValueError('healthy validation claim differs from raw records')
    if sum(r['escaped'] for r in development['task-v9-fault-screen'])!=15:
        raise ValueError('developmental fault-screen claim differs from raw records')
    raw=records(core);stress_raw=records(stress)
    causal_raw=records(causal)
    input_map=read(ROOT/'runs/task-v9-test/input-map.json')
    if core['registration_sha256']!=sha(ROOT/'runs/task-v9-frozen/registration-core.json'):
        raise ValueError('wrong core registration')
    for p in [ROOT/f'audit/acceptance-v9/replay-{label}/replay.json' for label in ['core','stress','causal']]:
        report=read(p)
        if not report['passed']:raise ValueError('independent replay must pass')
    archive=read(ROOT/'audit/acceptance-v9/archive-recomputed/summary.json')
    dropout=read(ROOT/'audit/acceptance-v9/archive-recomputed/dropout.json')
    controls=read(ROOT/'audit/acceptance-v9/archive-recomputed/bootstrap_controls.json')
    legacy=read(ROOT/'audit/acceptance-v9/archive-recomputed/closedloop_pairs.json')
    baseline=read(ROOT/'audit/acceptance-v9/baseline/check.json')
    flags=read(ROOT/'audit/acceptance-v9/legacy-horizon-flags/check.json')
    comparison=read(ROOT/'audit/acceptance-v9/warning-comparisons-core/comparisons.json')
    stress_comparison=read(ROOT/'audit/acceptance-v9/warning-comparisons-stress/comparisons.json')
    diagnostic=read(ROOT/'audit/acceptance-v9/control-diagnostic-core-v2/diagnostic.json')
    if comparison['metrics_sha256']!=sha(args.core/'metrics.csv') or stress_comparison['metrics_sha256']!=sha(args.stress/'metrics.csv'):
        raise ValueError('descriptive warning comparison does not match supplied cohort metrics')
    if set(diagnostic['raw_input_sha256'].values())!=set(core['raw_input_sha256'].values()):
        raise ValueError('control diagnostic does not match supplied core raw records')
    figure_manifest=read(args.figures/'manifest.json')
    summary_bindings=[h for p,h in figure_manifest['input_sha256'].items() if p.replace('\\','/').endswith('/summary.json')]
    if summary_bindings!=[sha(args.core/'summary.json')]:raise ValueError('figure summary binding differs')
    remember(ROOT/'paper/PROTOCOL_v9_NOTES.md')
    args.out.mkdir(parents=True,exist_ok=False);figdir=args.out/'figs';figdir.mkdir()
    for name in ['task_v9_assessment']:
        p=args.figures/f'{name}.pdf'
        if figure_manifest['outputs'][p.name]!=sha(p):raise ValueError('figure bytes changed after generation')
        remember(p);shutil.copyfile(p,figdir/'task_v10_assessment.pdf')
    remember(args.development_figure)
    shutil.copyfile(args.development_figure,figdir/'development_v10.pdf')
    for p in [args.tank_figure,args.warning_figure]:
        remember(p);shutil.copyfile(p,figdir/p.name)
    remember(args.main_source)
    title=re.search(r'\\title\{([^}]+)\}',args.main_source.read_text(),re.S).group(1).replace('\\\\',' ')
    parts=[r'''\documentclass[10pt,letterpaper]{article}
\usepackage[margin=0.72in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,graphicx,float,array,longtable,url}
\usepackage[font=small,labelfont=bf]{caption}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setlength{\tabcolsep}{4pt}
\raggedbottom
\begin{document}
\begin{center}{\Large\bfseries Supplementary Information}\\[5pt]
''',esc(title),r'''\\[5pt]Shuchao Gao, Waseda University\\
Assessment v9: matched source, data and protocol\end{center}
This document separates the independent core test, a prespecified angle stress
test, development, and historical audits. Every new table is reconstructed from
saved raw records and frozen registrations. Historical observations are retained
with their original limitations; they are not silently relabeled as new experiments.
\section{Protocol, software and calibration}
The current task is \texttt{task-v9.1-causal-exact-events}. The main Methods and
\path{paper/PROTOCOL_v9.md} define the sampled plant, common-random-number coupling,
first-passage task outcome and resource estimands. All test parameters were frozen
before outcomes. The neural substrate uses released FlyWire v783 tables and Shiu
parameters; the original publication used v630. The synthetic visual/body coupling
is not validated fly behavior. Functional row deletions are not physical bit faults.
Between spikes the voltage and voltage-valued synaptic drive obey
\[
\dot v_i=(v_0-v_i+g_i)/(20\,\mathrm{ms}),\qquad
\dot g_i=-g_i/(5\,\mathrm{ms}).
\]
Recurrent events add signed contact counts times 0.275\,mV to $g_i$ after
1.8\,ms. At threshold $-45$\,mV, reset sets $v_i$ to $v_0=-52$\,mV and
$g_i$ to zero; both equations pause during 2.2\,ms refractoriness. Sensory
cells retain this refractoriness, a variant of upstream stimulation. External
events add 68.75\,mV to voltage; all non-sensory external rates are zero.
Initial neural states, monitors and unmodified recurrent weights are restored
before each episode. A separate tiny actual Brian2 test verifies this reset,
including reapplying external weights, without loading a full connectome.
''']
    def para(s):parts.append(s+'\n')
    def table(caption,headers,rows,spec=None,long=False):
        spec=spec or 'l'+'r'*(len(headers)-1)
        # Short tables remain with adjacent explanation. Only genuinely long
        # matrices need a page-cleared longtable; this avoids stranded headings.
        long=long and len(rows)>30
        h=' & '.join(headers)+r'\\'
        body='\n'.join(' & '.join(str(v) for v in row)+r'\\' for row in rows)
        if long:
            parts.append('\\par\\clearpage\n{\\small\n\\begin{longtable}{'+spec+'}\n\\caption{'+caption+r'}\\'+'\n\\toprule\n'+h+
                '\n\\midrule\\endfirsthead\n\\toprule\n'+h+'\n\\midrule\\endhead\n'+body+'\n\\bottomrule\n\\end{longtable}\n}\n')
        else:
            parts.append('\\begin{table}[H]\n\\centering\\small\n\\caption{'+caption+'}\n\\begin{tabular}{'+spec+'}\n\\toprule\n'+h+
                '\n\\midrule\n'+body+'\n\\bottomrule\n\\end{tabular}\n\\end{table}\n')
    def outcomes(rows,caption):
        lookup={(r['seed'],r['phi_deg'],r['mode'],r['fault']):int(r['escaped']) for r in rows}
        values=[]
        for seed in sorted({r['seed'] for r in rows}):
            for phi in sorted({r['phi_deg'] for r in rows}):
                values.append([seed,f'{phi:+g}']+[lookup[(seed,phi,m,f)] for m in ['proportional','relay'] for f in ['healthy','F2_25','F2_50']])
        table(caption,['Seed',r'$\phi$ (deg)','P H','P 25','P 50','R H','R 25','R 50'],values,long=True)
    def counts(d,caption):
        table(caption,['Law','Network',r'$\phi$ (deg)','Success','L','G','H at risk'],[
            [esc(r['mode']),esc(r['fault']),f"{r['phi_deg']:+g}",f"{r['success']}/{r['n']}",r['losses'],r['gains'],r['healthy_at_risk']]
            for r in d['counts']])
    def effects(d,caption):
        rows=[]
        for name,r in d['cluster_effects'].items():
            rows.append([esc(effect_label(name)),number(100*r['estimate'],1),f"[{100*r['low']:.1f}, {100*r['high']:.1f}]"])
        table(caption,['Seed-level estimand / hierarchy','Mean (pp)',r'95\% interval (pp)'],rows)
    def metric_table(d,caption):
        labels=WARNING_NAMES
        rows=[]
        for name,label in labels.items():
            for subset in ['all','faulty','healthy']:
                r=d['warning_scores'][name][subset]
                rows.append([label,subset]+[r[k] for k in ['tp','fp','tn','fn']]+[
                    number(r[k]) for k in ['sensitivity','specificity','false_positive_rate','false_negative_rate']])
        table(caption,['Criterion','Subset','TP','FP','TN','FN','Sens','Spec','FPR','FNR'],rows,spec='p{1.85in}lrrrrrrrr',long=True)
    # Put current V10 evidence first. Reconstruct retained V9 tables below;
    # all legacy material is moved to a separate audit appendix at the end.
    marker=parts[-1].index(r'\section{Protocol, software and calibration}')
    baseline_intro=parts[-1][marker:]
    parts[-1]=parts[-1][:marker].replace('Assessment v9: matched source, data and protocol',
        'Assessment v10: checked interface, independent RF realizations and retained V9 evidence')
    para(r'\section{Executable evidence contract and independent adoption}')
    para(r'The interface accepts a complete Cartesian campaign declaration, native observations and a plant-specific adapter. Time is in seconds; failure is a first-passage event through the declared horizon. It returns structured issues for matrix membership, duplicates, source/configuration bindings, paired variates/masks, clocks, decision availability, resource accounting and endpoint labels. Native parsing errors are retained, not silently dropped. Adapters supply independent input and plant replay. Common uniforms do not imply identical feedback-dependent input events. See \path{docs/EVIDENCE_INTERFACE_V10.md}.')
    table('Executed adoption and integrity evidence; plants and resource units are not pooled.',
        ['Adapter','Seed clusters','Conditions/laws/faults','Episodes','Clean issues'],
        [['Fly baseline',24,'2/2/3',evidence['clean_records']['fly'],len(evidence['clean_issues']['fly'])],
         ['Delayed tank',8,'2/2/3',evidence['clean_records']['tank'],len(evidence['clean_issues']['tank'])]])
    para(r'The tank uses an independent native schema and analytic leaky dynamics: leakage 0.04/s, initial level 0.5, safe interval [0.2,0.8], two inflows 0.15/0.28 with shared exogenous variation, 100-ms sampling, 150-ms delayed outflow control and a 4-s horizon. Sensor-sample deletion holds the last measurement; these faults are not neural connection deletions. Algebraic replay verifies piecewise transitions, measurement holds, historical commands and exact boundary crossings. All 96 example episodes are safe, which supports adoption/integrity checking but establishes no fault-tolerance advantage or additional neural generalization.')
    para(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figs/tank_v10.pdf}\caption{Independent small-plant adoption. The first registered seed (9000), high inflow and proportional law are selected descriptively, without outcome selection. Left: healthy and nominal deletion probability $f=0.50$ traces; the full declared safe interval is stated rather than implied by the zoomed level axis. Right: the first changed request reaches the plant 150 ms later, between 100-ms grid boundaries. These are real tank records, not neural experiments or evidence of comparative fault tolerance.}\end{figure}')
    challenges=[]
    for i,(fly,tank) in enumerate(zip(evidence['corruption_cases']['fly'],evidence['corruption_cases']['tank']),1):
        challenges.append([i,esc(fly['error']),int(fly['detected']),int(tank['detected'])])
    table('Fourteen predefined corruption types per adapter, 28 instances total; not 28 independent error types, exhaustive coverage or a random error benchmark. The last two rows have domain-specific counterparts in the tank.',
        ['Type','Fly case','Fly caught','Tank caught'],challenges,spec='rp{4.3in}rr',long=True)
    para(r'Tank counterparts to the final two cases are rounded actuator timing and same-frame control application. Additional regressions reject swapped worker entry points, omitted generating sources and calibration/registration disagreement while permitting different worker seed partitions. These checks are engineering contracts, not new CRN or inference algorithms. Genuine archived V8 timing probes find 6 wrong horizon flags, 17 delays realized as 260 rather than 250 ms, and 4 completed bursts of 440 rather than 450 ms. Those older records remain separate from V9/V10 science.')
    para(r'A controlled all-sensor-dropout unit fixture exercises an actual boundary crossing and its latched first-failure time; changing that time is rejected by native replay. This fixture adds no independent Monte Carlo sample and is excluded from the 96-record adoption matrix and all neural statistics.')
    witness=evidence['untrusted_neural_witness']
    assert witness['trace_check_passed'] and not witness['neural_dynamics_executed'] and not witness['scientific_result']
    para(r'An explicitly synthetic zero-neural-readout fixture passes the input/plant consistency checks without solving neural equations. It is tagged as untrusted and excluded from all scientific episode directories and statistics. This constructive blind spot shows that matching claimed hashes and internally consistent traces do not authenticate execution, unlogged neural state, physical adequacy or safety. Prefix invariance tests alter future frames/outcome labels without changing 400-ms observations; decision causality still requires native replay.')
    for name,h in evidence['source_sha256'].items():
        p=ROOT/name.replace('\\','/')
        if sha(p)!=h:raise ValueError('evidence implementation changed after challenge: '+name)
        remember(p)
    para(r'\section{Prospective independent RF realizations}')
    design=read(ROOT/'runs/task-v10-design/design.json')
    para(r'Two map seeds were frozen before feasibility pilots and neural test outcomes. Both redraw azimuth independently from the SAME hemisphere-constrained uniform prior: left 10--90 deg, right -90 to -10 deg. Identities, vertical mapping and LPLC2 gradient are preserved. All 314 azimuth assignments differ from the baseline and between the two maps; the stored draws are independently reconstructible. These are assumed RF realizations, not measured biological RFs or different RF families. The same fixed ridge/trigger recipe is refitted per map on development data: this is protocol transfer with recalibration, not zero-shot decoder transfer.')
    table('Frozen RF cohorts; all conditions within a seed are paired. Both maps were retained, without validation- or test-outcome selection.',
        ['Map','RF seed','Dev seeds','Validation seeds','Test seeds'],
        [[q['map_id'],q['rf_seed'],f"{q['development_seeds'][0]}--{q['development_seeds'][-1]}",
          f"{q['validation_seeds'][0]}--{q['validation_seeds'][-1]}",f"{q['test_seeds'][0]}--{q['test_seeds'][-1]}"] for q in design['maps']])
    para(r'Each map uses 20 passive 400-ms development episodes, 32 healthy 1-s validation episodes in eight independent clusters, and 144 1-s test episodes in 12 new independent clusters. Each test seed crosses two bearings, two frozen control laws and healthy/25/50 percent deletion. The design total is 392 episodes plus two separately stored excluded feasibility pilots. The common calibration recipe fixes ridge penalty 10, 200--400-ms five-frame features, 600 deg/s shared turn limit, silence gate and the development-derived trigger rule. No new test outcomes tune controllers, select maps or replace seeds. Registration freezes validation-derived warning cutoffs before test launch. Local timestamps are not external preregistration timestamps.')
    para(r'An independent development-only check reconstructs coefficients by augmented least squares instead of normal-equation fitting; maximum coefficient differences are below $1.7\times10^{-16}$. Trigger values, input identities, role-separated seeds, calibration hashes and validation-derived cutoffs match. That check reads no test episode. It verifies saved provenance and arithmetic, not absence of unlogged tuning or authentic execution.')
    for q in transfer['maps']:
        tag=q['map_id'];folder=args.transfer/('map-'+tag)
        summary=read(folder/'analysis/summary.json');rr=records(summary)
        replay_report=read(folder/'replay/replay.json');ev=read(folder/'evidence.json')
        dec=read(folder/'decoder/summary.json')
        if summary['records']!=144 or not replay_report['passed'] or replay_report['records']!=144 or not ev['passed']:raise ValueError('map incomplete or unreplayed')
        if q['counts']!=summary['counts']:raise ValueError('transfer count binding')
        para(r'\subsection{Map '+tag+r': every paired test condition}')
        if list(q['validation_successes'].values())!=[8,8,8,8]:raise ValueError('unexpected validation counts; retain and describe actual failures')
        para('All eight healthy validation seeds survive in each law/bearing stratum (32/32 episodes in eight clusters). The complete test below represents 12 different clusters, not 144 independent replicates.')
        counts(summary,'Map '+tag+': complete task counts, with losses/gains relative to the same healthy seed/bearing/law. Bearings are degrees.')
        outcomes(rr,'Map '+tag+': every test outcome. No failure, direction, law or seed is omitted; 1 means no contact through 1 s.')
        rows=[]
        for item in q['primary']:
            for estimand,v in item['estimands'].items():
                label={'loss':'Loss (primary)','gain':'Gain (primary)','net_loss':'Net loss (derived)'}[estimand]
                rows.append([esc(item['mode']),esc(item['fault']),label,number(100*v['estimate'],2),
                    f"[{100*v['ci95'][0]:.2f},{100*v['ci95'][1]:.2f}]"])
        table('Map '+tag+': registered PRIMARY loss/gain and DERIVED net loss. Units: loss/gain are percent of paired scenarios; net loss is percentage points. 20,000 whole-seed percentile resamples, RNG 20261023, conditional on this map. Zero-event intervals are not zero-risk guarantees.',
            ['Law','Dose','Estimand / role','Estimate',r'95\% interval'],rows)
        zero_rows=[]
        for item in q['primary']:
            for estimand in ['loss','gain']:
                bound=item['estimands'][estimand]['zero_event_any_cluster_upper95']
                if bound is not None:zero_rows.append([esc(item['mode']),esc(item['fault']),estimand,number(100*bound,2)])
        if zero_rows:
            table('Post-registration zero-event reporting safeguard: one-sided 95 percent upper bound for ANY event in a new identically defined seed cluster at the SAME law/dose, across both bearings. Not conditional FNR, a signed-net-loss interval or a simultaneous bound over groups.',
                ['Law','Dose','No observed event','Any-cluster upper bound (percent)'],zero_rows)
        exposure_rows=[]
        for group,values in summary['activity_ratios'].items():
            mode,dose=group.split('/')
            formatted=[]
            for field in ['stop_ratio','common_ratio','early_ratio','full_ratio']:
                value=values[field];ci=value['cluster_interval']
                formatted.append(f"{value['median']:.3f} [{ci[0]:.3f},{ci[1]:.3f}]")
            exposure_rows.append([esc(mode),esc(dose)]+formatted)
        table('Map '+tag+': registered PRIMARY paired exposure estimands, median ratio and 95 percent whole-seed bootstrap interval. Own-stop uses each trace\'s contact-frame end; common duration uses the earlier contact-frame end; resolution 20 ms. Fixed 400-ms and 1-s ratios use their stated complete windows. Common duration does not equate sensory histories; post-contact full-window activity is counterfactual accounting, not warning evidence.',
            ['Law','Dose','Own-stop','Common','400 ms','1 s'],exposure_rows)
        pairpath=folder/'analysis/pairs.csv';remember(pairpath)
        with pairpath.open(newline='') as f:map_pairs=list(csv.DictReader(f))
        delta_rows=[]
        for mode in ['proportional','relay']:
            for dose in ['F2_25','F2_50']:
                delta=[float(r['stop_ratio'])-float(r['common_ratio']) for r in map_pairs if (r['mode'],r['fault'])==(mode,dose)]
                if len(delta)!=24:raise ValueError('incomplete RF exposure pairs')
                delta_rows.append([esc(mode),esc(dose),len(delta),number(statistics.median(delta),6),number(max(abs(v) for v in delta),6)])
        table('Map '+tag+': paired own-stop minus common-duration ratio differences. Descriptive reporting diagnostic, not an additional registered primary endpoint. All 24 pairs per law/dose are repeated observations in 12 seed clusters.',
            ['Law','Dose','Pairs','Median difference','Maximum absolute difference'],delta_rows)
        metric_table(summary,'Map '+tag+': SECONDARY frozen warning scores. Forecasts use exact simulated state. Own-stop upper is retrospective and uses a different reference; all subsets overlap.')
        interval_rows=[]
        def percent_ci(value,interval):
            if value is None:return '--'
            return f'{100*value:.1f} [{100*interval[0]:.1f},{100*interval[1]:.1f}]'
        for name,label in WARNING_NAMES.items():
            w=summary['warning_scores'][name]['all']
            interval_rows.append([label,percent_ci(w['sensitivity'],w['sensitivity_interval']),
                percent_ci(w['false_positive_rate'],w['false_positive_rate_interval'])])
        table('Map '+tag+': secondary warning sensitivity and false-positive rate, percent with 95 percent whole-seed percentile interval, all 144 paired observations. Forecasts use exact state; own-stop upper is retrospective. Class-absent bootstrap draws are omitted only for the corresponding conditional rate; undefined observed rates remain blank.',
            ['Criterion','Sensitivity [interval]','False-positive rate [interval]'],interval_rows,spec='p{2.25in}p{2.1in}p{2.1in}')
        supports=score_check['maps'][tag]['class_support']['all']
        para('Map '+tag+' bootstrap class support: sensitivity/FNR use '+str(supports['sensitivity']['valid_draws'])+
            ' of 20000 draws; specificity/FPR use '+str(supports['specificity']['valid_draws'])+
            ' draws. Intervals conditional on class presence and degenerate zero-event intervals do not establish population certainty. These calculations were independently checked from unchanged raw outcomes and saved warning decisions.')
        failures=[r for r in rr if not r['escaped']]
        if failures:
            table('Map '+tag+': all failed tasks and first contact times; rows are paired observations, not independent samples.',
                ['Seed','Bearing (deg)','Law','Dose','Contact (ms)'],
                [[r['seed'],f"{r['phi_deg']:+g}",esc(r['mode']),esc(r['fault']),number(r['collision_ms'],3)] for r in failures],long=True)
        else:para('No contacts occurred in the 144 observed map '+tag+' test episodes. This does not establish zero population failure risk or equivalence of laws.')
        table('Map '+tag+': descriptive healthy reserve and action summaries. Clearance is measured to first contact or the horizon, with 0 assigned at contact; heading is measured before all contacts.',
            ['Law','Success','Median clearance (mm)',r'Median $|\theta(400)|$ (deg)'],
            [[esc(r['mode']),f"{r['successes']}/{r['episodes']}",number(r['median_clearance_mm'],2),number(r['median_abs_heading_400_deg'],2)] for r in q['healthy_descriptive']])
    table('Prespecified SECONDARY interaction sensitivity family across BOTH maps and BOTH doses. Symmetric-null sign flips; no cross-map pooling.',
        ['Map/dose','Raw p','Four-test Holm p'],
        [[esc(k),number(v,6),number(transfer['secondary_interaction_holm_p'][k],6)] for k,v in transfer['secondary_interaction_raw_p'].items()])
    para(r'Only 12 independent clusters per new map constrain precision. All intervals are pointwise and conditional on the stored map, calibration and thresholds, not estimates over biological maps. Calibration data are not resampled and no simultaneous interval coverage is asserted. The old 24-cluster baseline uses its original two-dose family; new four-test adjustment is separate and prespecified. No inference treats the two map realizations as 24 map replicates. Healthy failures, gains, sparse positives, degenerate empirical intervals and warning false alarms remain visible.')
    decoder_rows=[]
    for label,dec in [('Baseline',decoder)]+[(q['map_id'],read(args.transfer/('map-'+q['map_id'])/'decoder/summary.json')) for q in transfer['maps']]:
        for name,h in dec['raw_sha256'].items():
            p=ROOT/name
            if sha(p)!=h:raise ValueError('decoder validation inputs changed: '+name)
            remember(p)
        decoder_rows.append([label,dec['seed_clusters'],dec['frames'],number(dec['rmse_deg'],2),
            f"[{dec['rmse_ci95_deg'][0]:.2f},{dec['rmse_ci95_deg'][1]:.2f}]",number(dec['mae_deg'],2)])
    table('Held-out healthy closed-loop decoder error, 200--400-ms frame ends, raw unclipped affine prediction times60 versus body-frame input bearing. 352 frames are repeated observations in EIGHT clusters, not 352 independent samples. Intervals resample whole validation seeds 20,000 times, RNG 20261023.',
        ['Map','Clusters','Frames','RMSE (deg)',r'95\% interval','MAE (deg)'],decoder_rows)
    para(r'These errors include the distribution shift after feedback changes body-frame bearing; passive development fit quality does not establish closed-loop bearing accuracy. The controller uses a calibrated steering score, not a validated angle sensor. Large errors are retained and no test-set recalibration is performed. Per-seed/per-law/bearing errors and all frame predictions accompany the raw diagnostics.')
    parts.append(baseline_intro.replace('Protocol, software and calibration','Retained V9 baseline: protocol, software and calibration'))
    table('Fixed baseline physical settings. No hardware power or area is inferred.',['Parameter','Value'],[
        ['Neural / feedback step','0.1 / 20 ms'],['Cue / task horizon','100 / 1000 ms'],
        ['Pursuer speed / initial separation','0.3 m/s / 0.25 m'],['Contact / looming radius','0.05 / 0.05 m'],
        ['Walk / burst speed','0.05 / 0.35 m/s'],['Burst delay / duration','250 / 450 ms'],
        ['Common turn limit / heading cap',r'600 deg/s / $\pm100$ deg'],['RF seed / inactive pool seed','20260201 / 0']])
    para(r'Independent input streams use SeedSequence [20261022, seed, frame, 1]; deletion uses [20261022, seed, 2]. The former supplies float32 cell/time uniforms and the latter float64 row uniforms. Both doses reuse the same row variates. Actual realized contact mass and sign composition are saved, not forced to equal their expectations. The input map saves pool/sensory/command identities and RF parameters. Exact source and table hashes are bound by the JSON registrations.')
    table('Fitted direction decoder coefficients, raw five-frame Hz features. Intercept is '+number(cal['direction_intercept'],9)+'.',
        ['FlyWire ID','Type','Side',r'$\beta_i$'],[[esc(c['flyid']),esc(c['cell_type']),esc(c['side']),number(b,9)]
            for c,b in zip(input_map['commands'],cal['direction_weights'])])
    para(r'Development fits bearing/$60^\circ$ with standardized inputs, ridge penalty 10 and an unpenalized intercept over 200--400 ms. The burst threshold is half the tenth percentile of per-episode 200--300 ms mean command rate, floor 2.5 Hz; here it is 4.03125 Hz. Development fit quality is not held-out prediction accuracy. The published B gain/silence gate followed a failed developmental attempt; all attempts remain available.')
    table('Unique V9 record files by role. The fault screen uses 16 distinct episodes but shares seed labels 400/401 with healthy validation; these are not 16 new independent clusters. No healthy test file is reused.',['Role','Seeds','Episodes','Horizon','Outcome use'],[
        ['Passive development','200--203',20,'400 ms','Fit only'],['Stopped A configuration','300--302',6,'1000 ms','Development'],
        ['Healthy B validation','400--407',32,'1000 ms','32/32 survived'],['B fault screen','400,401',16,'1000 ms','15/16 survived'],
        ['Independent core','1000--1023',288,'1000 ms','24 clusters'],['Angle stress','1100--1107',96,'1000 ms','8 separate clusters'],
        ['Action ablations','1200--1207',64,'1000 ms','8 separate clusters']])
    para(r'The initial A configuration stopped after healthy success was 1/3, making its predeclared 3/4-per-stratum screen impossible. Its three F2\_25 records included two survivors. B changes the common gain to 600 deg/s and gates steering during silence, preserving the fitted decoder/trigger. All 32 B healthy validations survived (8/8 in every law/bearing stratum). The two-seed fault screen retained a proportional/-30/F2\_50 collision at 977.0661 ms. These are developmental observations, not independent confirmation.')
    para(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figs/development_v10.pdf}\caption{Retained V9 development and validation diagnostics, not independent-test evidence. (a) DNp04 mean smoothed rates in 200--400 ms; all four developmental seeds per bearing, slight horizontal jitter for visibility, black median. (b) All eight validation seeds per law/bearing; P/R denote proportional/relay, black median. The same seed is shared across conditions. (c) Observed old completed bursts (four v8 records) and all 32 complete B-validation bursts, relative to decision time. This timing comparison does not isolate the cause of old-versus-new task outcomes; other controller/protocol components also changed. The V10 presentation filename preserves the original V9 figure.}\end{figure}')
    para(r'\section{Independent core outcomes and seed clusters}')
    counts(core,'Core outcomes. Each direction/law/dose has 24 seed clusters. L/G: healthy-to-fault losses/gains; H: healthy survivors at risk. Healthy rows compare to themselves.')
    outcomes(raw,'Every core task outcome, 1=collision-free through 1000 ms. P/R: proportional/relay. H/25/50: healthy and row deletion percentages. No direction or failed seed is omitted.')
    effects(core,'Derived net losses and prespecified secondary interactions in percentage points; 20,000 percentile bootstrap resamples, seed 20261022, conditional on this model/map/task.')
    with (args.core/'clusters.csv').open(newline='') as f:clusters=list(csv.DictReader(f))
    remember(args.core/'clusters.csv')
    table('Every actual independent cluster contrast. P/R and 25/50 match the preceding table; interaction is R minus P net loss.',
        ['Seed','P25','R25',r'$\Delta25$','P50','R50',r'$\Delta50$'],[
            [r['seed']]+[number(float(r[k]),2) for k in ['proportional_F2_25_net_loss','relay_F2_25_net_loss','F2_25_interaction',
                'proportional_F2_50_net_loss','relay_F2_50_net_loss','F2_50_interaction']] for r in clusters],long=True)
    table('Prespecified SECONDARY symmetric-null sign-flip sensitivity; not a randomized-controller assignment test.',['Dose','Raw p','Holm p'],[
        [esc(f),number(core['interaction_raw_p'][f],6),number(core['interaction_holm_p'][f],6)] for f in ['F2_25','F2_50']])
    para(r'The originally frozen analyzer passed the complete input/source/timing checks but then failed on duplicate numeric-margin/Boolean-warning CSV keys, before reporting statistics. The original script, failure log and output directory are retained. The documented exportfix analyzer renames only numeric CSV fields, preserving all numerical definitions, thresholds, source guards and raw records; canonical analyses are core-v2 and stress-v2. This is a post-registration analytical export correction, not a new hypothesis or neural rerun. See \path{paper/PROTOCOL_v9_NOTES.md}.')
    para(f"A post-hoc timing/heading diagnostic verifies identical first trigger times and pre-decision traces in all {diagnostic['paired_law_scenarios']} paired law/scenario cells. Both laws gate steering below the trigger threshold, so their first action divergence follows that same decision. Table entries at 400 ms precede every contact. Equal maximum turn rate does not match executed turning effort; these diagnostics are not causal mediation estimates or energy measurements.")
    table('Descriptive precontact control diagnostics on all core records; medians pool the two paired directions, without adding independent samples.',
        ['Law','Network','Median trigger (ms)',r'Median $|\theta(400)|$ (deg)'],[[esc(r['mode']),esc(r['fault']),number(r['median_trigger_ms'],1),number(r['median_abs_heading_400_deg'],2)] for r in diagnostic['groups']])
    table('Healthy baseline safety reserve over the full 1-s episode. No healthy record collided, so these values contain no post-contact continuation. Matching binary success does not match clearance or executed effort.',
        ['Law','Episodes','Median clearance (mm)','Minimum (mm)','Maximum (mm)'],[[esc(r['mode']),r['n'],number(r['median_min_clearance_mm'],2),number(r['minimum_min_clearance_mm'],2),number(r['maximum_min_clearance_mm'],2)] for r in diagnostic['healthy_margins']])
    para(r'\section{Frozen warnings, information and error denominators}')
    para(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figs/task_v10_warnings.pdf}\caption{Same baseline warning data, readable labels. Every command-rate observation is shown, with vertical jitter only. Secondary frozen operating points show detection among 13 contacts and false alarms among 275 successes, with 95\% whole-seed bootstrap intervals. Both forecasts use exact simulated state. Degenerate zero-event intervals do not imply population zero risk.}\end{figure}')
    table('Thresholds from 32 healthy validation episodes in EIGHT seed clusters, not 32 independent samples.',['Criterion','Threshold'],[
        ['Command mean, 100--400 ms',number(cr['thresholds']['command_lower_hz'],9)+' Hz'],
        ['Two-sided activity log score',number(cr['thresholds']['activity_abs_log_upper'],9)],
        ['Held-command forecast clearance (exact state)',number(cr['thresholds']['deadline_lower_m'],9)+' m'],
        ['Actuator-schedule forecast clearance (exact state)',number(cr['thresholds']['schedule_lower_m'],9)+' m'],['Upper resource excursion',r'$2\times$ reference']])
    para(r'All prospective warnings use data through 400 ms, verified before first contact in every record. The two-sided activity score is the absolute log count ratio to the law/side-specific validation median. Its cutoff is the healthy 95th percentile; command and forecast cutoffs are fifth percentiles. The same nominal 5\% healthy flag calibration is not a guarantee of task FPR. Held-command and schedule forecasts share exact simulated geometry and the pending actuator schedule; the held-command forecast holds the current neural-derived turn command, the baseline sets future turn to zero. If no trigger exists, both assume the earliest next-frame decision. This is an optimistic extrapolation, not a neural-only detector or reachability proof.')
    metric_table(core,'Core confusion counts. Positives are collisions through 1 s. The own-stop upper criterion is retrospective resource scoring, not a 400-ms warning. All/faulty/healthy subsets are overlapping views of the same seed clusters. A dash means the conditional rate is undefined because its class is absent.')
    para(r'The retrospective own-stop upper flag divides by its paired healthy stopped count. The prospective 400-ms activity flags instead use frozen law/side validation medians. Their classification difference therefore changes both observation and reference, and is not a pure exposure ablation. The duration-isolated comparison is $R_{\rm stop}$ versus $R_{\rm common}$ within the same healthy/fault pair. The two-sided score also detects low activity; it addresses a different hypothesis from an upper resource limit.')
    paired_rows=[]
    for subset in ['all','faulty','healthy']:
        rr=comparison['comparisons'][f'{subset}/deadline-minus-schedule_only']
        for name in ['sensitivity','specificity','error_rate']:
            r=rr[name];ci=r['cluster_interval']
            paired_rows.append([subset,esc(name),number(None if r['difference'] is None else 100*r['difference'],2),
                '--' if ci is None else f'[{100*ci[0]:.2f}, {100*ci[1]:.2f}]'])
    table('Secondary descriptive paired held-command minus schedule comparison (pp), added after registration. The same bootstrap draws keep complete seed clusters together. No extra confirmatory test or threshold tuning is introduced.',
        ['Subset','Metric','Difference (pp)',r'95\% interval (pp)'],paired_rows)
    table('Sparse-class bootstrap diagnostics. A missing positive class makes sensitivity undefined; such draws are not silently treated as zero.',
        ['Subset','Positive clusters','Negative clusters','Valid sens. draws','Valid spec. draws'],[[s]+[comparison['diagnostics'][f'{s}/transmission'][k] for k in ['positive_seed_clusters','negative_seed_clusters','sensitivity_valid_resamples','specificity_valid_resamples']] for s in ['all','faulty','healthy']])
    stratum=[]
    for name in ['transmission','equal_duration_upper','equal_duration_two_sided','schedule_only','deadline']:
        for label,r in core['warning_scores'][name]['strata'].items():
            stratum.append([WARNING_NAMES[name],esc(label)]+[r[k] for k in ['tp','fp','tn','fn']]+[number(r[k]) for k in ['sensitivity','specificity']])
    table('Direction/law disaggregation of the same core warning records.',['Criterion','Stratum','TP','FP','TN','FN','Sens','Spec'],stratum,long=True)
    para(r'Full conditional cluster intervals for sensitivity, specificity, FPR and FNR are in the source summary JSON. Resampling keeps every law/bearing/dose within seed together. Zero observed errors may produce a degenerate bootstrap interval; the one-sided 95\% bound for the probability of at least one error in an otherwise identically defined seed cluster is $1-0.05^{1/n}$. This is a cluster-any-error bound, not a conditional FPR/FNR guarantee. No population or hardware zero-risk claim follows.')
    para(r'The original registration gives an approximate 0.20 planning half-width without stating its range explicitly. This normal maximum-variance approximation applies only to $[0,1]$ success/loss/gain cluster means. Signed net loss spans $[-1,1]$, and its between-law contrast can span $[-2,2]$, yielding range-based planning approximations about 0.40 and 0.80, respectively. These are not finite-sample coverage guarantees. The clarification in \path{paper/PROTOCOL_v9_NOTES.md} preserves the registration bytes, sample size and analysis. Actual intervals are reported; small interactions and equivalence are not established by the sample size.')
    para(r'\section{Exposure and observation horizon}')
    rows=[]
    for group,values in core['activity_ratios'].items():
        for name,r in values.items():rows.append([esc(group),esc(name),number(r['median'],4),f"[{r['cluster_interval'][0]:.4f}, {r['cluster_interval'][1]:.4f}]"])
    table('Paired network-spike estimands. Own-stop and common-duration use recorded first-contact frame ends. Fixed 1-s activity includes explicitly simulated post-contact continuation.',
        ['Law/dose','Estimand','Median',r'95\% cluster interval'],rows,long=True)
    with (args.core/'pairs.csv').open(newline='') as f:paired_rows=list(csv.DictReader(f))
    remember(args.core/'pairs.csv');differences=[]
    for mode in ['proportional','relay']:
        for fault in ['F2_25','F2_50']:
            values=[float(r['stop_ratio'])-float(r['common_ratio']) for r in paired_rows if r['mode']==mode and r['fault']==fault]
            differences.append([esc(mode),esc(fault),len(values),number(statistics.median(values),8),number(max(map(abs,values)),8),
                sum(v<0 for v in values),sum(v==0 for v in values),sum(v>0 for v in values)])
    table('Paired own-stop MINUS common-duration ratios on the SAME scenarios. Equal group medians alone do not establish equality of pairs.',
        ['Law','Dose','Pairs','Median diff.','Max abs. diff.','Negative','Zero','Positive'],differences)
    horizons=[]
    for m in ['proportional','relay']:
        for f in ['healthy','F2_25','F2_50']:
            rr=[next(r for r in core['horizon_sensitivity'] if (r['mode'],r['fault'],r['horizon_ms'])==(m,f,t)) for t in [800,900,1000]]
            horizons.append([esc(m),esc(f)]+[f"{r['success']}/{r['n']}" for r in rr])
    table('Repeated fixed task horizons; these do not add independent samples. No endpoint was selected for significance.',['Law','Network','800 ms','900 ms','1000 ms'],horizons)
    para(r'Common duration is outcome-dependent and does not hold closed-loop sensory histories fixed. Full-horizon activity after first contact is a specified counterfactual resource measure, not a prospective predictor or a claim about physical contact dynamics. Activity profiles at 200/400/600/800/1000 ms, including counts of prior contacts at each window, are provided in activity-profiles.csv.')
    para(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figs/task_v10_assessment.pdf}\caption{Retained core exposure estimands and frozen warning performance with updated readable labels. Every line in the left panel is a matched scenario; black markers are medians. Right-panel intervals use complete seed-cluster resampling. The upper resource criterion and all subgroup errors remain tabulated even if they are not emphasized in the main figure.}\end{figure}')
    para(r'\section{Prespecified off-angle stress transfer}')
    para(r'The $\pm45^\circ$ test uses eight NEW seed clusters and unchanged laws, map, actuator and thresholds. These angles were absent from calibration and validation. The activity reference transfers from the same-side $30^\circ$ stratum. No threshold is fitted on stress outcomes, and stress records are not pooled with core records to strengthen inference. It tests angle transfer, not a new connectome or RF map. Eight-cluster uncertainty is necessarily wide.')
    counts(stress,'Stress outcomes, eight clusters per law/direction/dose. Counts are separate from the 24-cluster core.')
    outcomes(stress_raw,'Every stress outcome. Definitions match the core outcome table.')
    metric_table(stress,'Stress warning confusion counts; unchanged calibration and exact simulated geometry. Missing conditional rates remain undefined.')
    valid=stress_comparison['diagnostics']['all/transmission']['sensitivity_valid_resamples']
    para(f"The stress set has only two failure clusters. Of 20000 bootstrap draws, {valid} contain a positive class and {20000-valid} contain none. Reported sensitivity intervals condition on the valid draws; the zero observed miss interval is not a finite-sample guarantee. The joint new-cluster-any-miss upper bound is 31.2 percent, not a conditional FNR guarantee. The two-sided activity criterion also flags 22/32 healthy stress episodes: transferring the same-side 30-degree reference does not preserve its healthy flag calibration at 45 degrees.")
    effects(stress,'Descriptive stress cluster effects, kept separate from the core analysis.')
    para(r'\section{Separate motor-interface ablations}')
    para(r'Baseline walking remains 0.05 m/s when neural actions are disabled; the agent is not immobilized. Burst necessity follows from this toy plant by construction. For a walk-only segment of duration $\Delta t\leq0.02$ s with precontact separation $d\geq0.05$ m, the pursuer moves $0.3\Delta t$ toward the segment-start agent position and the agent moves at most $0.05\Delta t$. Since $d>0.3\Delta t$, triangle inequality gives $d_{\rm next}\leq d-(0.3-0.05)\Delta t$. From $d_0=0.25$ m, contact must occur by 0.8 s without a burst, regardless of heading commands. A lightweight geometry property test checks this bound over arbitrary commands. It is not an additional neural experiment or a newly fitted warning metric.')
    para(r'This diagnostic matrix was registered after the original core launch, before complete core analysis. It is not part of the original confirmatory registration and contributes no primary significance test. Eight new seeds 1200--1207 cross the two core bearings with normal proportional/relay, turn-disabled and steering-and-burst-disabled interfaces on healthy networks. The turn-disabled interface retains neural burst triggering; the other removes both neural actions. Common uniforms, calibration and physical settings remain fixed. Every normal failure and every ablated success is retained. The pair of ablations does not separately isolate burst necessity; the kinematic bound above establishes its necessity for this plant. These checks do not establish connectome-specific superiority or biological escape.')
    table('Independent diagnostic action outcomes. Each law/direction has eight clusters; this cohort is not pooled with core or stress.',
        ['Interface','Bearing','Success','Triggered'],[[esc(r['mode']),f"{r['phi_deg']:+g}",f"{r['success']}/{r['n']}",r['triggers']] for r in causal['counts']])
    causal_lookup={(r['seed'],r['phi_deg'],r['mode']):int(r['escaped']) for r in causal_raw}
    table('All action-ablation outcomes, 1=collision-free through 1 s. Turn off retains burst triggering; act off removes both actions.',
        ['Seed','Bearing','P','R','Turn off','Act off'],[[s,f'{p:+g}']+[causal_lookup[(s,p,m)] for m in ['proportional','relay','disabled','observe']] for s in ar['test_seeds'] for p in ar['phis']],long=True)
    action_rows=[]
    for mode,label in [('proportional','P'),('relay','R')]:
        for ablation,alabel in [('disabled','Turn off'),('observe','Both actions off')]:
            normal=[causal_lookup[s,p,mode] for s in ar['test_seeds'] for p in ar['phis']]
            ablated=[causal_lookup[s,p,ablation] for s in ar['test_seeds'] for p in ar['phis']]
            action_rows.append([label,alabel,f'{sum(normal)}/{len(normal)}',f'{sum(ablated)}/{len(ablated)}',len(normal)])
    table('Paired action diagnostic: observed counts, not certainty from degenerate [100,100] percent intervals. Eight clusters per comparison; no primary significance test.', ['Normal law','Ablation','Normal successes','Ablated successes','Paired scenarios'],action_rows)
    para(r'Every observed normal-minus-ablated cluster contrast equals one, so an empirical percentile bootstrap would be degenerate. This finite set does not prove a population success difference of one. Counts and the complete outcome table are reported instead.')
    para(r'\section{Historical audit and preserved exploratory evidence}')
    para(r'These tables describe older protocols and are not independent v9 evidence. The v8 original/pre-cue-gated laws, global Brian2 input seeds and stop-on-collision semantics differ from v9. Its six clusters cannot be pooled with the new laws or called confirmed by a different controller comparison. The original 25\% interaction vector [0,0.5,0.5,0,0.5,0] has mean 0.25 and post-hoc symmetric-null p=0.25; the 50\% contrast is baseline-driven because both faulty laws have zero survivors. The conditional 25\% percentile interval [0.0833,0.4167] does not override the sparse support.')
    table('Preserved v8 counts independently reconstructed from its 72 records.',['Law','Fault','-30','+30','Total'],[
        [esc(r['mode']),esc(r['fault'] or 'healthy'),r['by_bearing']['-30'],r['by_bearing']['30'],f"{r['success']}/{r['n']}"] for r in baseline['counts']])
    para(f"The source-qualified old-flag audit covers {flags['qualified']} unique records; {len(flags['mismatches'])} have an incorrect exact-horizon label. Reused copies are deduplicated. Another {len(flags['unverified'])} old records lack sufficient exact generation-source/timing metadata for this audit; current code is not substituted for that missing provenance. Raw files remain unchanged.")
    table('Corrected derived v8 flags: all listed intervals end exactly at the 1-s horizon. Their last-frame state is true but exact-horizon state is false.',
        ['Law','Fault','Seed','Bearing','Recorded','Exact'],[[esc(r['mode']),esc(r['fault'] or 'healthy'),r['seed'],f"{r['phi_deg']:g}",int(r['recorded']),int(r['at_exact_horizon'])] for r in flags['mismatches']])
    para(r'Old nominal 250/450-ms actuation is realized as 260-ms delay and 440-ms completed bursts on 20-ms frame starts. Original/gated healthy survivors active at the exact horizon number two/two, versus four/three during the last frame. These metadata corrections do not change recorded survival. New v9 exact-event runs are separately executed and replay-checked; they do not retroactively validate old trajectories.')
    table('Read-only 600-ms archive recomputation. f is row deletion; p=1-f is survival. No universal power law or recruitment mechanism follows.',
        ['f','p','Output retention','Retention/p'],[[number(r['deleted'],2),number(r['surviving'],2),number(r['retention'],4),number(r['retention_over_survival'],4)] for r in dropout])
    para(r'Historical transmission-only/joint scoring gives 276/288 versus 262/288 on the SAME records, not runs of SpikeFI or SpikingJET. The 14 differences are 12 inhibitory-hub and two random expected-contact-mass trials (zero-based trials 3 and 9: 327246 and 271058 spikes). Expected contact-mass matching does not equate row fractions (about 8.63\% versus 5.57\%). Their median does not remove the tail risk. HUB\_inh median/mean are 847476.5/847857 spikes. At 75-Hz drive, 50\% deletion passes the historical 51.4-Hz criterion in only 10/12 cases; the 150-Hz main result does not extend to all drives.')
    rows=[]
    for name in ['v4/F4_1pct','v4/F2_25','v4/F2_50','v4c/HUB_inh']:
        r=legacy[name];rows.append([esc(name),f"{r['escaped']}/{r['n']}",r['bursts'],r['activity_exceedances'],number(r['median_pair_ratio'],4)])
    table('Preserved legacy closed-loop records. Bursts mean any logged burst interval, not exact-horizon activity. Geometry/calibration are compromised; this is a descriptive audit.',
        ['Cohort','Survival','Bursts','Above 2x','Median pair ratio'],rows)
    para(r'F4 has 12/12 survival but 6/12 twofold activity exceedances; its pooled ratio near 1.7 is not a per-condition pass. Legacy 50\% deletion changes median ratio from 0.381701 to 0.729443 under common-duration matching. Original F4 node manifests remain unavailable; current reconstructed/protected-FlyID selectors cannot recover those identities or validate the original dynamics. Corrected hub causal experiments are not claimed. The v9 main test uses only row deletion and does not depend on those hub selections.')
    para(r'\section{Compute, audit scope and exact artifact access}')
    table('Measured episode wall times. Overlapping worker sums are NOT CPU seconds or campaign elapsed time.',
        ['Cohort','Episodes','Median episode (s)','Episode sum (s)'],[[label,d['records'],number(d['compute']['episode_wall_seconds_median'],2),number(d['compute']['episode_wall_seconds_sum'],2)] for label,d in [('Core',core),('Stress',stress),('Action ablation',causal)]])
    para(r'The exercised runtime is CPython 3.12.14, Brian2 2.10.1, NumPy 2.5.4 and Cython 3.1.3, using NumPy code generation on an Intel Xeon W-2223 at 3.60 GHz, 8 logical CPUs, 31.59 GiB physical RAM. V10 uses at most four workers, two per map. Memory is the measured lifetime peak working set of each persistent worker, not isolated per-episode memory or GPU allocation. Original V9 workers did not record this peak, so new values are not retroactively assigned to V9. Full phase elapsed times and exit codes accompany the campaign. Overlapping episode sums are not CPU time.')
    compute_rows=[]
    for q in transfer['maps']:
        summary=read(args.transfer/('map-'+q['map_id'])/'analysis/summary.json');rr=records(summary)
        compute_rows.append([q['map_id'],len(rr),number(statistics.median(r['wall_seconds'] for r in rr),2),
            number(max(r['worker_resources']['worker_peak_working_set_bytes'] for r in rr)/2**30,3)])
    table('Measured V10 test episode wall times and persistent-worker lifetime peak working sets. Same CPU host; no hardware cost model.',
        ['Map','Episodes','Median wall (s)','Worker peak (GiB)'],compute_rows)
    para(r'Independent replay checks trace/input consistency from recorded readout outputs. It does not verify neural states, authenticate execution or replace full simulation. Saved-data analysis/replay was repeated from a fresh public checkout and a new isolated dependency installation on the SAME host, without the old cache: all core, angle-stress and action-diagnostic numerical fields match, and all 448 saved input/plant traces pass replay. It uses only NumPy/setuptools, not Brian2 or external matrices. This is not a second-host neural replication or a simulation-speedup benchmark. No energy, area, physical upset rate or real-time execution benefit is inferred.')
    para(r'The immutable public V9 source/data baseline is \url{https://github.com/Scophield/drosophila-fault-injection/tree/43bcd4d6a99b2d9b258cf8a198a4545d237b5c39}. All 3992 source-archive members and the named main/SI PDF bytes were independently checked against the protected baseline. Observed public archive SHA256 is \path{7c05f24560a0a47001a054b09b09f4d7c06dc4c1400b9517b0674f9214708976}; GitHub can repack ZIPs, so commit/tree/member identity is the content binding. This is not the unpublished local review ZIP or a claimed Release. V10 additions remain local until a separately verified authorized snapshot is published. See \path{docs/REPRODUCE_V10.md}.')
    para(r'External model code is MIT (Philip Shiu and Nico Spiller); underlying FlyWire v783 connectivity metadata declares CC-BY 4.0. These do not automatically license all transformed tables or annotations. The local annotation table matches upstream commit \path{a83b2776d60d5764cef36b927f5f9679c16c47a2} after CRLF-to-LF normalization only; generating bytes remain unchanged. Annotation-specific redistribution terms and transformed-table terms remain unresolved, documented in \path{docs/THIRD_PARTY_INPUTS_V10.md}. Hash-matched external connectivity/completeness tables and installed dependencies are still required for new neural runs. The source snapshot is not a complete installed experimental environment.')
    origin=read(ROOT/'audit/v10/upstream-access/model-input-origin-resolved.json')
    if not origin['passed']:raise ValueError('external input byte origin unresolved')
    para(r'The external Parquet exactly matches its upstream Git blob at model commit 91bdd1e7. The exercised model code and completeness CSV are CRLF checkout representations; CRLF-to-LF-only comparisons reproduce upstream Git blobs. No generating input file was rewritten. Exact-byte/runtime preflight is provided before expensive work; semantic newline equivalence does not override frozen hash checks. This provenance resolution supplies no additional dataset licence grant.')
    attribution=[]
    for name in ['flywire','annotations','visual-system','male-cns','gustatory']:
        m=read(ROOT/('audit/v10/upstream-access/crossref-'+name+'.json'))['message']
        attribution.append([esc(m['author'][0]['family']+' et al.'),esc(m['title'][0]),r'\url{https://doi.org/'+m['DOI']+'}'])
    table('Upstream annotation/connectome attribution requested by the pinned resource. Exact title/DOI metadata were checked separately from claim support and dataset licensing; article license metadata do not automatically license a later combined annotation dump.',
        ['Creator','Work','DOI'],attribution,spec='lp{3.3in}p{2.1in}')
    body='\n'.join(parts)
    # A SHA has no natural word boundary. Explicitly display two concatenated
    # lines instead of shrinking fonts or allowing a provenance hash to overflow.
    archive_sha='7c05f24560a0a47001a054b09b09f4d7c06dc4c1400b9517b0674f9214708976'
    body=body.replace('Observed public archive SHA256 is '+r'\path{'+archive_sha+'};',
        'Observed public archive SHA256 (concatenate the following two lines):'+
        r'\begin{quote}\ttfamily '+archive_sha[:32]+r'\\ '+archive_sha[32:]+r'\end{quote}')
    hist=body.index(r'\section{Historical audit and preserved exploratory evidence}')
    compute=body.index(r'\section{Compute, audit scope and exact artifact access}')
    body=body[:hist]+body[compute:]+r'\clearpage\appendix'+body[hist:compute]+r'\end{document}'
    tex=args.out/'supplement.tex';tex.write_text(body,encoding='utf-8')
    for i in [1,2]:
        with (args.out/f'pass{i}.txt').open('w') as f:
            result=subprocess.run(['pdflatex','--disable-installer','-interaction=nonstopmode','-halt-on-error','-file-line-error','supplement.tex'],cwd=args.out,stdout=f,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'LaTeX failed; inspect {args.out}/pass{i}.txt')
    log=(args.out/'supplement.log').read_text(errors='replace')
    problems=re.findall(r'[^\n]*(?:undefined|Overfull \\[hv]box|Float too large|Missing character:|ignored error:|^!)[^\n]*',log)
    manifest=dict(generator_sha256=sha(Path(__file__)),source_sha256=sources,tex_sha256=sha(tex),
        pdf_sha256=sha(args.out/'supplement.pdf'),latex_problems=problems)
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='source_sha256'},indent=2))
    if problems:raise RuntimeError('LaTeX overflow/reference/glyph problem; PDF not promoted')


if __name__=='__main__':main()
