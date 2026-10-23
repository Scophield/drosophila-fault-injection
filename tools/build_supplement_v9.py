"""Build a source-bound supplement only from completed, verified measurements."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

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
    for name in ['task_v9_overview','task_v9_outcomes','task_v9_assessment']:
        p=args.figures/f'{name}.pdf'
        if figure_manifest['outputs'][p.name]!=sha(p):raise ValueError('figure bytes changed after generation')
        remember(p);shutil.copyfile(p,figdir/p.name)
    remember(args.development_figure)
    shutil.copyfile(args.development_figure,figdir/'development_v9.pdf')
    remember(ROOT/'paper/main.tex')
    title=re.search(r'\\title\{([^}]+)\}',(ROOT/'paper/main.tex').read_text(),re.S).group(1).replace('\\\\',' ')
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
        h=' & '.join(headers)+r'\\'
        body='\n'.join(' & '.join(str(v) for v in row)+r'\\' for row in rows)
        if long:
            parts.append('{\\small\n\\begin{longtable}{'+spec+'}\n\\caption{'+caption+r'}\\'+'\n\\toprule\n'+h+
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
        table(caption,['Seed',r'$\phi$','P H','P 25','P 50','R H','R 25','R 50'],values,long=True)
    def counts(d,caption):
        table(caption,['Law','Network',r'$\phi$','Success','L','G','H at risk'],[
            [esc(r['mode']),esc(r['fault']),f"{r['phi_deg']:+g}",f"{r['success']}/{r['n']}",r['losses'],r['gains'],r['healthy_at_risk']]
            for r in d['counts']])
    def effects(d,caption):
        rows=[]
        for name,r in d['cluster_effects'].items():
            rows.append([esc(name),number(100*r['estimate'],1),f"[{100*r['low']:.1f}, {100*r['high']:.1f}]"])
        table(caption,['Seed-level estimand','Mean (pp)',r'95\% interval (pp)'],rows)
    def metric_table(d,caption):
        labels={'transmission':'Command low','stop_count_upper':'Own-stop upper',
            'equal_duration_upper':'400-ms upper','equal_duration_two_sided':'Two-sided activity',
            'schedule_only':'Actuator schedule','deadline':'Held-command candidate'}
        rows=[]
        for name,label in labels.items():
            for subset in ['all','faulty','healthy']:
                r=d['warning_scores'][name][subset]
                rows.append([label,subset]+[r[k] for k in ['tp','fp','tn','fn']]+[
                    number(r[k]) for k in ['sensitivity','specificity','false_positive_rate','false_negative_rate']])
        table(caption,['Criterion','Subset','TP','FP','TN','FN','Sens','Spec','FPR','FNR'],rows,long=True)
    table('Fixed physical settings. No hardware power or area is inferred.',['Parameter','Value'],[
        ['Neural / feedback step','0.1 / 20 ms'],['Cue / task horizon','100 / 1000 ms'],
        ['Pursuer speed / initial separation','0.3 m/s / 0.25 m'],['Contact / looming radius','0.05 / 0.05 m'],
        ['Walk / burst speed','0.05 / 0.35 m/s'],['Burst delay / duration','250 / 450 ms'],
        ['Common turn limit / heading cap',r'600 deg/s / $\pm100$ deg'],['RF seed / inactive pool seed','20260201 / 0']])
    para(r'Independent input streams use SeedSequence [20261022, seed, frame, 1]; deletion uses [20261022, seed, 2]. The former supplies float32 cell/time uniforms and the latter float64 row uniforms. Both doses reuse the same row variates. Actual realized contact mass and sign composition are saved, not forced to equal their expectations. The input map saves pool/sensory/command identities and RF parameters. Exact source and table hashes are bound by the JSON registrations.')
    table('Fitted direction decoder coefficients, raw five-frame Hz features. Intercept is '+number(cal['direction_intercept'],9)+'.',
        ['FlyWire ID','Type','Side',r'$\beta_i$'],[[esc(c['flyid']),esc(c['cell_type']),esc(c['side']),number(b,9)]
            for c,b in zip(input_map['commands'],cal['direction_weights'])])
    para(r'Development fits bearing/$60^\circ$ with standardized inputs, ridge penalty 10 and an unpenalized intercept over 200--400 ms. The burst threshold is half the tenth percentile of per-episode 200--300 ms mean command rate, floor 2.5 Hz; here it is 4.03125 Hz. Development fit quality is not held-out prediction accuracy. The published B gain/silence gate followed a failed developmental attempt; all attempts remain available.')
    table('Unique newly executed records by role; no reused healthy test records.',['Role','Seeds','Episodes','Horizon','Outcome use'],[
        ['Passive development','200--203',20,'400 ms','Fit only'],['Stopped A configuration','300--302',6,'1000 ms','Development'],
        ['Healthy B validation','400--407',32,'1000 ms','32/32 survived'],['B fault screen','400,401',16,'1000 ms','15/16 survived'],
        ['Independent core','1000--1023',288,'1000 ms','24 clusters'],['Angle stress','1100--1107',96,'1000 ms','8 separate clusters'],
        ['Action ablations','1200--1207',64,'1000 ms','8 separate clusters']])
    para(r'The initial A configuration stopped after healthy success was 1/3, making its predeclared 3/4-per-stratum screen impossible. Its three F2\_25 records included two survivors. B changes the common gain to 600 deg/s and gates steering during silence, preserving the fitted decoder/trigger. All 32 B healthy validations survived (8/8 in every law/bearing stratum). The two-seed fault screen retained a proportional/-30/F2\_50 collision at 977.0661 ms. These are developmental observations, not independent confirmation.')
    para(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figs/development_v9.pdf}\caption{Development and validation diagnostics, not independent-test evidence. (a) DNp04 mean smoothed rates in 200--400 ms; all four developmental seeds per bearing, slight horizontal jitter for visibility, black median. (b) All eight validation seeds per law/bearing; P/R denote proportional/relay, black median. The same seed is shared across conditions. (c) Observed old completed bursts (four v8 records) and all 32 complete B-validation bursts, relative to decision time. This timing comparison does not isolate the cause of old-versus-new task outcomes; other controller/protocol components also changed.}\end{figure}')
    para(r'\section{Independent core outcomes and seed clusters}')
    counts(core,'Core outcomes. Each direction/law/dose has 24 seed clusters. L/G: healthy-to-fault losses/gains; H: healthy survivors at risk. Healthy rows compare to themselves.')
    outcomes(raw,'Every core task outcome, 1=collision-free through 1000 ms. P/R: proportional/relay. H/25/50: healthy and row deletion percentages. No direction or failed seed is omitted.')
    effects(core,'Complete-seed effects in percentage points; 20,000 percentile bootstrap resamples, seed 20261022, conditional on this model/map/task.')
    with (args.core/'clusters.csv').open(newline='') as f:clusters=list(csv.DictReader(f))
    remember(args.core/'clusters.csv')
    table('Every actual independent cluster contrast. P/R and 25/50 match the preceding table; interaction is R minus P net loss.',
        ['Seed','P25','R25',r'$\Delta25$','P50','R50',r'$\Delta50$'],[
            [r['seed']]+[number(float(r[k]),2) for k in ['proportional_F2_25_net_loss','relay_F2_25_net_loss','F2_25_interaction',
                'proportional_F2_50_net_loss','relay_F2_50_net_loss','F2_50_interaction']] for r in clusters],long=True)
    table('Prespecified symmetric-null sign-flip sensitivity; not a randomized-controller assignment test.',['Dose','Raw p','Holm p'],[
        [esc(f),number(core['interaction_raw_p'][f],6),number(core['interaction_holm_p'][f],6)] for f in ['F2_25','F2_50']])
    para(r'The originally frozen analyzer passed the complete input/source/timing checks but then failed on duplicate numeric-margin/Boolean-warning CSV keys, before reporting statistics. The original script, failure log and output directory are retained. The documented exportfix analyzer renames only numeric CSV fields, preserving all numerical definitions, thresholds, source guards and raw records; canonical analyses are core-v2 and stress-v2. This is a post-registration analytical export correction, not a new hypothesis or neural rerun. See \path{paper/PROTOCOL_v9_NOTES.md}.')
    para(f"A post-hoc control diagnostic verifies identical first trigger times and pre-decision traces in all {diagnostic['paired_law_scenarios']} paired law/scenario cells. Both laws gate steering below the trigger threshold, so their first action divergence follows that same decision. Table entries at 400 ms precede every contact. Equal maximum turn rate does not match executed turning effort; these diagnostics are not causal mediation estimates or energy measurements.")
    table('Descriptive precontact control diagnostics on all core records; medians pool the two paired directions, without adding independent samples.',
        ['Law','Network','Median trigger (ms)',r'Median $|\theta(400)|$ (deg)'],[[esc(r['mode']),esc(r['fault']),number(r['median_trigger_ms'],1),number(r['median_abs_heading_400_deg'],2)] for r in diagnostic['groups']])
    table('Healthy baseline safety reserve over the full 1-s episode. No healthy record collided, so these values contain no post-contact continuation. Matching binary success does not match clearance or executed effort.',
        ['Law','Episodes','Median clearance (mm)','Minimum (mm)','Maximum (mm)'],[[esc(r['mode']),r['n'],number(r['median_min_clearance_mm'],2),number(r['minimum_min_clearance_mm'],2),number(r['maximum_min_clearance_mm'],2)] for r in diagnostic['healthy_margins']])
    para(r'\section{Frozen warnings, information and error denominators}')
    table('Thresholds learned only from all 32 healthy validation records.',['Criterion','Threshold'],[
        ['Command mean, 100--400 ms',number(cr['thresholds']['command_lower_hz'],9)+' Hz'],
        ['Two-sided activity log score',number(cr['thresholds']['activity_abs_log_upper'],9)],
        ['Held-command clearance',number(cr['thresholds']['deadline_lower_m'],9)+' m'],
        ['Schedule-only clearance',number(cr['thresholds']['schedule_lower_m'],9)+' m'],['Upper resource excursion',r'$2\times$ reference']])
    para(r'All prospective warnings use data through 400 ms, verified before first contact in every record. The two-sided activity score is the absolute log count ratio to the law/side-specific validation median. Its cutoff is the healthy 95th percentile; command and forecast cutoffs are fifth percentiles. The same nominal 5\% healthy flag calibration is not a guarantee of task FPR. Held-command and schedule forecasts share exact simulated geometry and the pending actuator schedule; the candidate holds the current neural-derived turn command, the baseline sets future turn to zero. If no trigger exists, both assume the earliest next-frame decision. This is an optimistic extrapolation, not a neural-only detector or reachability proof.')
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
            stratum.append([esc(name),esc(label)]+[r[k] for k in ['tp','fp','tn','fn']]+[number(r[k]) for k in ['sensitivity','specificity']])
    table('Direction/law disaggregation of the same core warning records.',['Criterion','Stratum','TP','FP','TN','FN','Sens','Spec'],stratum,long=True)
    para(r'Full conditional cluster intervals for sensitivity, specificity, FPR and FNR are in the source summary JSON. Resampling keeps every law/bearing/dose within seed together. Zero observed errors may produce a degenerate bootstrap interval; the one-sided 95\% bound for the probability of at least one error in an otherwise identically defined seed cluster is $1-0.05^{1/n}$. This is a cluster-any-error bound, not a conditional FPR/FNR guarantee. No population or hardware zero-risk claim follows.')
    para(r'The original registration gives an approximate 0.20 planning half-width without stating its range explicitly. This normal maximum-variance approximation applies only to $[0,1]$ success/loss/gain cluster means. Signed net loss spans $[-1,1]$, and its between-law contrast can span $[-2,2]$, yielding range-based planning approximations about 0.40 and 0.80, respectively. These are not finite-sample coverage guarantees. The clarification in \path{paper/PROTOCOL_v9_NOTES.md} preserves the registration bytes, sample size and analysis. Actual intervals are reported; small interactions and equivalence are not established by the sample size.')
    para(r'\section{Exposure and observation horizon}')
    rows=[]
    for group,values in core['activity_ratios'].items():
        for name,r in values.items():rows.append([esc(group),esc(name),number(r['median'],4),f"[{r['cluster_interval'][0]:.4f}, {r['cluster_interval'][1]:.4f}]"])
    table('Paired network-spike estimands. Own-stop and common-duration use recorded first-contact frame ends. Fixed 1-s activity includes explicitly simulated post-contact continuation.',
        ['Law/dose','Estimand','Median',r'95\% cluster interval'],rows,long=True)
    horizons=[]
    for m in ['proportional','relay']:
        for f in ['healthy','F2_25','F2_50']:
            rr=[next(r for r in core['horizon_sensitivity'] if (r['mode'],r['fault'],r['horizon_ms'])==(m,f,t)) for t in [800,900,1000]]
            horizons.append([esc(m),esc(f)]+[f"{r['success']}/{r['n']}" for r in rr])
    table('Repeated fixed task horizons; these do not add independent samples. No endpoint was selected for significance.',['Law','Network','800 ms','900 ms','1000 ms'],horizons)
    para(r'Common duration is outcome-dependent and does not hold closed-loop sensory histories fixed. Full-horizon activity after first contact is a specified counterfactual resource measure, not a prospective predictor or a claim about physical contact dynamics. Activity profiles at 200/400/600/800/1000 ms, including counts of prior contacts at each window, are provided in activity-profiles.csv.')
    para(r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{figs/task_v9_assessment.pdf}\caption{Core exposure estimands and frozen warning performance. Every line in the left panel is a matched scenario; black markers are medians. Right-panel intervals use complete seed-cluster resampling. The upper resource criterion and all subgroup errors remain tabulated even if they are not emphasized in the main figure.}\end{figure}')
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
    effects(causal,'Descriptive normal-minus-ablated success differences (positive means normal succeeds more often), averaging bearings within each of eight clusters. Identical observed contrasts yield degenerate bootstrap intervals, not population certainty.')
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
    para(r'The exercised runtime is CPython 3.12.14, Brian2 2.10.1, NumPy 2.5.4, Cython 3.1.3 (NumPy code generation), on a Windows CPU host with 31.59 GiB physical memory. Full pins, source/input hashes and actual launcher elapsed/exit-code records accompany the artifact. No hardware mapping, energy, area, physical upset rate or real-time neural execution is inferred. The independent audit checks trace/input consistency using recorded readout outputs; it does not verify every neural state or replace full simulation.')
    para(r'The versioned source/data archive binds the main and supplementary PDFs to TeX, figures, CSV/JSON analysis, every independent raw episode, maps, registrations and exact generating snapshots. External connectivity/completeness tables and dependency caches are excluded; expected input hashes and the upstream release are specified. Reanalysis and input/geometry replay need no external table or new neural execution. Fresh simulation needs the external model and a Git checkout. The public repository may contain an earlier revision; a local archive is not public availability or evidence of submission. See \path{docs/REPRODUCE_v9.md} and the final material index. Historical source/timestep gaps remain explicit.')
    parts.append(r'\end{document}')
    tex=args.out/'supplement.tex';tex.write_text('\n'.join(parts),encoding='utf-8')
    for i in [1,2]:
        with (args.out/f'pass{i}.txt').open('w') as f:
            result=subprocess.run(['pdflatex','--disable-installer','-interaction=nonstopmode','-halt-on-error','-file-line-error','supplement.tex'],cwd=args.out,stdout=f,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError(f'LaTeX failed; inspect {args.out}/pass{i}.txt')
    log=(args.out/'supplement.log').read_text(errors='replace')
    problems=re.findall(r'[^\n]*(?:undefined|Overfull \\[hv]box|Float too large|Missing character:)[^\n]*',log)
    manifest=dict(generator_sha256=sha(Path(__file__)),source_sha256=sources,tex_sha256=sha(tex),
        pdf_sha256=sha(args.out/'supplement.pdf'),latex_problems=problems)
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='source_sha256'},indent=2))
    if problems:raise RuntimeError('LaTeX overflow/reference/glyph problem; PDF not promoted')


if __name__=='__main__':main()
