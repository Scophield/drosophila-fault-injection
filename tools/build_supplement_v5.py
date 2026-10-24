"""Generate a current, standalone supplement from preserved measurement summaries."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def escape(value):
    replacements = {'\\': r'\textbackslash{}', '_': r'\_', '%': r'\%',
                    '&': r'\&', '#': r'\#', '{': r'\{', '}': r'\}'}
    return ''.join(replacements.get(c, c) for c in str(value))


def generate(out):
    out.mkdir(parents=True, exist_ok=False)
    sources = set()

    def read(name):
        path = ROOT / name
        sources.add(path)
        return json.loads(path.read_text())

    def records(name):
        path = ROOT / name
        sources.add(path)
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    archive = read('audit/assessment-v3-base/revision_analysis.json')
    assessment = read('audit/assessment-v3/assessment.json')
    prospective = read('audit/prospective-v3.json')
    controls = read('audit/controls-v4/controls.json')
    horizons = read('audit/horizons-v4/horizons.json')
    refractory = read('audit/refractory-v4/summary.json')
    cross = read('audit/controller-fault-v8/cross.json')
    independent = read('audit/cross-audit-v8/audit.json')
    calibration = read('runs/geometry-v3/vision/calib-geometry-v3.json')
    if not all(d.get('complete') for d in (prospective, controls, refractory, cross)):
        raise ValueError('supplement requires completed saved campaigns')
    if controls['calibration_sha256'] != sha(ROOT / 'runs/geometry-v3/vision/calib-geometry-v3.json'):
        raise ValueError('calibration mismatch')
    if not independent['passed'] or independent['summary_sha256'] != sha(ROOT/'audit/controller-fault-v8/cross.json'):
        raise ValueError('independent cross audit is incomplete or stale')
    for data in (controls, prospective, cross):
        for name, expected in data['source_sha256'].items():
            if sha(ROOT / name) != expected:
                raise ValueError(f'measurement changed: {name}')

    parts = [r'''\documentclass[10pt,letterpaper]{article}
\usepackage[margin=0.78in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,graphicx,float,array}
\usepackage{url}
\usepackage[font=small,labelfont=bf]{caption}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setlength{\textfloatsep}{9pt}
\raggedbottom
\begin{document}
\begin{center}
{\Large\bfseries Supplementary Information}\\[4pt]
{\large Endpoint and Exposure Sensitivity in Fault Assessment\\of a Fly-Connectome Spiking Model}\\[5pt]
Shuchao Gao, Waseda University\\
Review package assessment-v8, 22 October 2026
\end{center}
This document is the current entry point for all supporting measurements.
It consolidates the evidence retained across protocols v2--v4 and v8; their status
statements describe earlier revisions and are not current experimental claims.
This revision adds 48 fault episodes to 24 preserved healthy episodes, completing
the 72-record controller-by-fault comparison in Sections 12--13.
The matched artifact contains raw records, generating-source snapshots where
recorded, current analysis scripts, figure sources and a SHA256/size manifest.
\section{Campaign and material index}
Tables S1--S22 and Figures S1--S9 distinguish historical observations from new
simulations. Main-paper Table I reports the controller-by-fault matrix; Tables
S12--S14 retain the earlier healthy-only intervention evidence. The +30-degree
healthy direction is at floor in both prospective cohorts. Neural survival endpoints are bounded at
1000 ms; the geometric rule uses the separate horizons in Table S1.
''']
    table_count = 0

    def table(caption, header, rows, spec=None):
        nonlocal table_count
        table_count += 1
        cols = spec or 'l' + 'r' * (len(header) - 1)
        parts.append(r'\begin{table}[H]\centering\small' + '\n'
                     + r'\setlength{\tabcolsep}{4pt}' + '\n'
                     + r'\caption{' + caption + '}\n'
                     + r'\begin{tabular}{' + cols + r'}\toprule' + '\n'
                     + ' & '.join(header) + r'\\\midrule' + '\n'
                     + '\n'.join(' & '.join(str(v) for v in row) + r'\\' for row in rows)
                     + '\n' + r'\bottomrule\end{tabular}\end{table}' + '\n')

    def page(title):
        parts.append(r'\clearpage\section{' + title + '}\n')

    def figure(source, caption, width=r'.94\textwidth', height=None):
        source = ROOT / source
        sources.add(source)
        destination = out / 'figures' / source.name
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, destination)
        options = f'width={width}' + (f',height={height},keepaspectratio' if height else '')
        parts.append(r'\begin{figure}[H]\centering\includegraphics[' + options + ']{figures/'
                     + source.name + r'}\caption{' + caption + r'}\end{figure}' + '\n')

    table('Campaigns and statistical units. Counts refer to neural episodes, except the deterministic rule.',
          ['Campaign', 'Seeds', 'Bearings', 'Runs', 'Duration (ms)'], [
              ['Passive calibration', '0--2', '$-60,-30,0$', 9, 400],
              ['First prospective campaign', '6--11', '$-30,+30$', 48, 1000],
              ['Paired healthy controls', '12--17', '$-30,+30$', 48, 1000],
              ['Controller-by-fault extension', '12--17', '$-30,+30$', '48 new + 24 reused', 1000],
              ['Sensory refractory sensitivity', '12--14', 'Constant drive', 12, 600],
              ['Main historical sweep', 'Fault-seeded', 'Constant drive', r'$19\times12$', 600],
              ['Privileged geometric rule', 'Deterministic', '$-30,+30$', 6, '800/1000/1200'],
          ], 'llllr')
    parts.append(r'''The 288 scored fault/control records comprise 216 main-sweep
fault trials plus 72 targeted/random-inhibitory controls; healthy references are
separate. The target-permuted historical phase is a specificity control, not a
functioning fault-tolerance baseline. Exact current tables derive from saved
summaries; no missing historical manifest or generation version is reconstructed
as if it had been recorded.

\textbf{Reading map.} Section 2 defines model and estimands; Section 3 supplies
every main dose; Section 4 gives cohorts, controls and legacy partitions;
Section 5 separates stopping-time matching from late crossings; Sections 6--7
give the prospective and paired-control results; Section 8 gives model-variant
sensitivity and compute; Sections 9--10 give archived diagnostic figures; Section 11
gives reproduction and provenance boundaries; Sections 12--13 add the paired
factorial experiment. Tables and figures are numbered
continuously and have explicit sample/dispersion definitions.
''')
    page('Model, endpoints and statistical definitions')
    parts.append(r'''The signed FlyWire-v783 substrate contains 138,639 neurons,
15,091,983 connection rows and approximately 54.5 million contacts. Membrane and
synaptic-drive constants are 20 and 5 ms; threshold/reset are -45/-52 mV, delay
1.8 ms, and contact gain 0.275 mV. Both voltage equations pause during the 2.2-ms
refractory period. Project wrappers retain this interval in sensory neurons,
unlike the upstream stimulation routine. Fresh integration uses 0.1 ms;
historical timestep metadata are unavailable. Independent 150-Hz inputs drive
104 LC4 and 210 LPLC2 cells; each external event adds 68.75 mV to voltage.
Eight DNp01/DNa02/DNp04/DNb01 cells provide the readout. No background drive is used.

\textbf{Open-loop endpoints.} For eight command cells and $T=0.6$ s,
$r=N_{\rm cmd}/(8T)$. Latency is the first spike in this group, not a completed
decision. Total $S$ counts all network spikes. Transmission requires
$r\geq51.4$ Hz, rounding $(94.583333+8.229167)/2=51.40625$ Hz from separate
ten-trial sensory/random-drive calibrations. Joint passing additionally requires
$r\leq c\,94.6875$ Hz and $S\leq c\,39694$ with $c=2$; sensitivity uses
$c=1.5,3,4$. This is a nested operational rule, not a validated energy/safety budget.

\textbf{Paired estimands.} With cumulative spikes $S_F,S_H$ and recorded
durations $T_F,T_H$, define
\[R_{\rm whole}=\frac{S_F(T_F)}{S_H(T_H)},\quad
R_{\rm common}=\frac{S_F(T_*)}{S_H(T_*)},\quad
R(t)=\frac{S_F(t)}{S_H(t)},\quad T_*=\min(T_F,T_H),\ t\leq T_* .\]
Matching unequal stopping times and choosing an earlier endpoint are different.
The common duration can itself depend on fault-induced collision. Ratios are
reported per scenario before taking medians. Undefined zero-reference ratios
are not silently assigned finite values. Legacy timestamps mark frame starts
but cumulative counts include the completed 20-ms frame; 400 ms uses frame 19.

\textbf{Frozen controller.} Nine passive episodes at -60/-30/0 degrees and
seeds 0--2 fix threshold 18.125 Hz, bias $b=-20$ Hz, scale $\ell=70$ Hz and sign +1.
The fitted window is 250--300 ms. Steering is
$\omega_k=-400\,\mathrm{deg/s}\,\operatorname{clip}((\bar d_k-b)/\ell,-1,1)$.
$d_k$ sums four left rates minus four right rates; $a_k$ is the eight-cell mean.
Bars average the latest five frames (all available initially). Triggering requires
the current smoothed $\bar a_k$ and preceding unsmoothed $a_{k-1}$ both to reach
18.125 Hz. The first qualifying frame schedules one burst 250 ms after its end.
This is not two consecutive smoothed crossings. Burst speed/duration are
0.35 m/s and 450 ms, with fixed heading; otherwise speed is 0.05 m/s and heading
is limited to $\pm100$ degrees. Cue onset is 100 ms. Geometry uses actual separation,
body-frame bearing and within-frame collision checks at 0.05 m.

\textbf{Uncertainty.} Historical median intervals use 20,000 resamples, seed 0.
Reference-aware ratio-of-median intervals independently resample healthy/fault
trials. Dispersion bars instead show 10th--90th trial percentiles. Legacy seed
diagnostics enumerate $3^3=27$ ordered draws, yielding only 4--7 distinct medians.
New control ranges resample six complete seed clusters, keeping both bearings
together. These conditional percentile ranges are exploratory, with no confirmatory
coverage, significance or equivalence claim. More bootstrap draws do not add
independent observations. Historical open-loop streams were not reset per trial.
''')
    page('Complete archived main sweep')
    rows = []
    for name, q in archive['fault_families'].items():
        lo, hi = q['rate_ci95']
        rows.append([escape(name), f"{q['rate_med']:.2f} [{lo:.2f},{hi:.2f}]",
                     '---' if q['lat_med'] is None else f"{q['lat_med']:.2f}",
                     f"{q['tot_med']:,.1f}", f"{q['transmission_pass']}/12"])
    table(r'All main conditions, 12 trials each. Rate, latency and spikes are medians; brackets give conditional 95\% bootstrap intervals for rate.',
          ['Condition', 'Rate [range] (Hz)', 'Latency (ms)', 'Spikes', 'T'], rows)
    parts.append(r'''F1 multiplies each weight by $\exp(\sigma Z-\sigma^2/2)$,
$Z\sim N(0,1)$; $\sigma=0.5$ has coefficient of variation 53.3\%.
F2 independently deletes connection rows, so expected lost absolute contact mass
is the deletion fraction. F3/F4 silence outgoing connections while affected cells
can still receive input and spike. F5 silences sensory outputs. Historical F4
selections lack contemporaneous cell manifests and may include protected readouts.
These rows are descriptive, not corrected-selector results.

The ratio of F2\_50 and healthy median rates is 0.764576. Resampling both groups
gives a 95\% bootstrap interval [0.751101, 0.789648]. The first-spike-latency ratio
is 1.333333 [1.253012, 1.400000]. These ratios of medians differ from the median of
within-seed ratios in Table S15. A separate control at 75 Hz with 50\% deletion passes
10/12; the 150-Hz sweep does not establish drive invariance or equivalence.
''')
    page('Cohorts, realized controls and legacy partitions')
    exclusion = assessment['cohort_scores']['exclusions']
    labels = ['All fault/control records', 'Exclude inhibitory hubs', 'Exclude F4/HUB/EIm', 'Main F1/F2/F3/F5']
    table('Cohort scoring at $c=2$. T and J denote transmission and joint passes.',
          ['Included records', '$n$', 'T', 'J', 'T$-$J'],
          [[label, q['n'], q['transmission'], q['joint'], q['additional_rejections']]
           for label, q in zip(labels, exclusion.values())])
    rows = []
    for name in ['EIm_1pct','EIm_2pct','HUB_exc','HUB_inh','INHrand_cells','INHrand_mass']:
        q = records(f'sim_vision/results_vision/openloop_controls/{name}.jsonl')
        med = lambda field: float(np.median([r[field] for r in q]))
        rows.append([escape(name), f"{med('n_cells'):,.0f}" if all('n_cells' in r for r in q) else '---',
                     f"{100*med('frac_edges_modified'):.2f}" if all('frac_edges_modified' in r for r in q) else '---',
                     f"{med('pop_rate'):.2f}", f"{med('n_total_spikes'):,.1f}"])
    table('Historical controls, 12 trials each. Medians of recorded damage and responses; cell/edge counts are not contact-mass equality.',
          ['Condition', 'Cells', r'Rows modified (\%)', 'Rate (Hz)', 'Spikes'], rows)
    parts.append(r'''EIm denotes excitatory/inhibitory-composition-matched controls.
The two remaining additional rejections after targeted-hub exclusion are
INHrand\_mass trials 3 and 9 (zero-based), with 327,246 and 271,058 spikes.
Their median cannot summarize this tail. Complete per-trial damage is preserved
in the raw JSONL files; dashes denote absent cell-count metadata, not zero cells.
Post-hoc selector reconstructions are supplied at \path{audit/verified-hubs}
with their original manifest. They cannot establish missing historical hub
identities; expected-mass matching does not imply realized contact equality.
''')
    table('Healthy legacy partitions. Exact reused logs differ from shared seed clusters.',
          ['Partition', 'Scenarios', 'Collision-free'], [
              ['Calibration reuse', '$-60/-30$ degrees, seeds 0--2', '6/6'],
              ['Other negative bearings', '$-60/-30$ degrees, seeds 3--5', '6/6'],
              ['Positive bearings', '$+30/+60$ degrees, seeds 0--5', '12/12'],
              ['Frontal', '0 degrees, seeds 0--2', '0/3'],
          ], 'llr')
    parts.append('All legacy fault records use calibration seed clusters. The remaining 18/18 healthy records lack exact scenario reuse but do not form an independent evaluation.\n')
    page('Stopping times, early windows and late crossings')
    table('Median paired legacy spike ratios, using main-paper Eq.~(3). Ratios are computed within scenario before aggregation.',
          ['Condition', 'Whole', 'Common duration', 'First 400 ms'],
          [[escape(name), f"{q['median_episode_ratio']:.4f}", f"{q['median_common_ratio']:.4f}",
            f"{q['median_fixed400_ratio']:.4f}"] for name,q in archive['conditions'].items()])
    table('Full-hub cumulative horizon sensitivity. Every fault/healthy pair lasts 1000 ms.',
          ['Horizon (ms)', 'Median paired ratio', 'Above twofold'],
          [[t, f"{q['median']:.3f}", f"{q['exceedances']}/12"]
           for t,q in horizons['groups']['F4_1pct']['windows'].items()])
    table('First twofold crossings. All six are negative-bearing calibration scenarios.',
          ['Bearing (degrees)', 'Seed 0 (ms)', 'Seed 1 (ms)', 'Seed 2 (ms)'],
          [[phi] + [next(p['first_twofold_ms'] for p in horizons['pairs']
                         if p['fault']=='F4_1pct' and p['phi']==phi and p['seed']==s) or 'None'
                    for s in range(3)] for phi in (-60,-30,30,60)])
    parts.append(r'''For F2\_50, common-duration matching changes 0.381701 to
0.729443. For full hubs, whole and common ratios are identical within every pair.
Selecting 400 ms excludes late activity, without invalidating the one-second
warning. Inhibitory hubs exceed twofold in all 12 pairs at every selected
200--500-ms window. Late-crossing traces are in main-paper Figure 3; Figure S3
shows individual estimands rather than only pooled medians.
''')
    page('First prospective campaign: directional outcomes')
    groups = prospective['groups']
    names = ['brain/healthy','brain/F2_25','brain/F2_50','readout_disabled/healthy']
    labels = ['Healthy',r'25\% deletion',r'50\% deletion','Readout disabled']
    table('First campaign, seeds 6--11. Six clusters per condition; bearings share seeds.',
          ['Condition', '$-30$ degrees', '$+30$ degrees', 'Total', 'Burst at 1 s'],
          [[label, f"{groups[name]['azimuth_collision_free_counts']['-30.0']}/6",
            f"{groups[name]['azimuth_collision_free_counts']['30.0']}/6",
            f"{groups[name]['collision_free']}/12", groups[name]['burst_active_at_horizon']]
           for name,label in zip(names,labels)])
    table('First-campaign collision-free counts over both bearings within each seed (maximum two).',
          ['Condition'] + [str(s) for s in range(6,12)],
          [[label]+[groups[name]['seed_collision_free_counts'][str(s)] for s in range(6,12)]
           for name,label in zip(names,labels)])
    table('Median paired activity in first-campaign faults. All 12 pairs are retained in each cell.',
          ['Condition', '200 ms', '300 ms', '400 ms', '500 ms'],
          [[label]+[f"{groups[name]['activity_windows'][str(t)]['median']:.4f}" for t in (200,300,400,500)]
           for name,label in zip(names[1:3],labels[1:3])])
    parts.append(r'''Neither deletion condition exceeds twofold matched activity
in these windows despite eight and twelve collisions. This is not a fitted
task-failure detector. The activity ratio is distinct from the open-loop joint
criterion. Every +30-degree healthy record collides, creating a floor for fault
comparisons in that direction. Five healthy survivors are retained at -30 degrees;
25\% deletion loses one and 50\% loses all five on those paired seeds.
''')
    figure('audit/prospective-figures-v8/prospective_outcomes.pdf',
            'First-campaign outcomes and every first-400-ms pair. Lines join the same seed and bearing across doses; directions share six seed clusters. Dashed ratio one is a reference; black segments are medians.',
           width=r'.62\textwidth', height='3.4in')
    page('Paired controller interventions: new seeds')
    labels = ['Original law','Pre-cue gate','Offset only','No steering']
    modes = controls['modes']
    table('Healthy-network controls, seeds 12--17. All retain the same neural trigger rule, not identical trigger times.',
          ['Law', '$-30$ degrees', '$+30$ degrees', 'Total', 'Bursts triggered'],
          [[label, f"{controls['groups'][mode+'/healthy']['azimuth_collision_free_counts']['-30.0']}/6",
            f"{controls['groups'][mode+'/healthy']['azimuth_collision_free_counts']['30.0']}/6",
            f"{controls['groups'][mode+'/healthy']['collision_free']}/12", f"{controls['trigger_counts'][mode]}/12"]
           for mode,label in zip(modes,labels)])
    table('Every paired seed outcome. Each cell lists (-30,+30) binary survival at 1 s.',
          ['Seed'] + labels,
          [[s]+[','.join(str(int(next(p['survived'] for p in controls['pairs']
                                    if (p['mode'],p['seed'],p['phi'])==(m,s,phi))))
                         for phi in (-30.,30.)) for m in modes] for s in controls['test_seed_clusters']])
    table(r'Mean paired difference versus original law, averaging both bearings within seed. Conditional 95\% percentile bootstrap ranges, 20,000 six-cluster draws; exploratory only.',
          ['Law', 'Difference (pp)', 'Range (pp)', 'Improved / worse / same'],
          [[label, f"{100*controls['contrasts'][mode]['mean_difference']:+.1f}",
            '['+', '.join(f'{100*v:.1f}' for v in controls['contrasts'][mode]['conditional_cluster_bootstrap95'])+']',
            ' / '.join(str(sum(test(v) for v in controls['contrasts'][mode]['seed_mean_differences']))
                       for test in (lambda v:v>0,lambda v:v<0,lambda v:v==0))]
           for mode,label in zip(modes[1:],labels[1:])])
    parts.append(r'''The gate comparison has two improving, zero worsening and
four unchanged clusters. Its range includes zero. All positive-bearing tests
collide under every law. Offset-only and no-steering laws trigger bursts in
11/12 and 12/12 cases yet never survive. These complete feedback-law comparisons
do not isolate trigger timing from subsequent sensory trajectories. They do not
estimate deletion tolerance under altered control laws by themselves; Sections
12--13 supply the direct fault comparison. Original/gated survivors
still bursting at 1 s number four/three. Every group's survival count is unchanged
between 800 and 1000 ms; no 1200-ms neural outcome is imputed.
''')
    figure('audit/control-figures-v4b/paired_controls.pdf',
           'Every paired outcome and six-cluster differences. Blue intervals are conditional exploratory percentile ranges; open circles are seed means. Bearings are fixed scenarios sharing each seed.',
           width=r'.98\textwidth', height='2.45in')
    page('Sensory refractory sensitivity and measured compute')
    table('Three-seed model-variant comparison, 12 full-connectome 600-ms runs. Retention is computed within seed before its median; it is not a ratio of group medians.',
          ['Sensory refractory', 'Healthy (Hz)', 'Fault (Hz)', 'Paired median', 'Paired range'],
           [[key+' ms', f"{q['healthy_median_hz']:.2f}", f"{q['fault_median_hz']:.2f}",
             f"{q['paired_median']:.4f}", '['+', '.join(f'{v:.4f}' for v in q['paired_range'])+']']
           for key,q in refractory['groups'].items()])
    parts.append(r'''Seeds 12--14 share deletion masks (10000+s) and reset Poisson
seeds (20000+s) within each pair. All other neurons retain 2.2-ms refractoriness.
Healthy median rates are 94.79 and 103.12 Hz under sensory refractory times
2.2 and 0 ms. This quantifies a conditional implementation difference; three
paired seeds cannot establish variant invariance or replace the historical sweep.
''')
    table('Measured compute on Intel Xeon W-2223, 3.60 GHz, Windows. Sums of worker episode wall times are not CPU time.',
          ['Campaign', 'Episodes', 'Elapsed (s)', 'Episode sum (s)'], [
              ['Paired controls, 3 workers', 48, f"{controls['execution']['wall_seconds']:.1f}", f"{controls['episode_seconds_total']:.1f}"],
              ['Refractory, 1 worker', 12, f"{refractory['wall_seconds']:.1f}", f"{refractory['trial_wall_seconds']:.1f}"],
          ])
    parts.append(f"Refractory construction took {refractory['build_seconds']:.1f} s before its elapsed interval. "
                 'Control timings include state restoration and frame processing; workers overlap.\n')
    parts.append(r'''Fresh neural execution uses CPython 3.13.15, Brian2 2.10.1,
NumPy 2.5.4 and the NumPy backend, with 0.1-ms integration and 20-ms feedback.
Observed per-process working memory is about 1.1 GB, not a profiled peak bound.
Total historical campaign runtime is unavailable. A complete Cython/compiler
environment has not been validated. The original 48-test campaign has generation
hashes but not every complete version-specific source snapshot. New control and
refractory batches save exact generating Python sources with per-file hashes.

\textbf{Assessment boundary.} One connectome, selected drives, asymmetric
calibration coverage, assumed receptive fields and directional floor effects
limit transfer. Fixed-horizon survival is not eventual escape. The privileged
geometric rule survives both bearings at 800/1000 ms but collides by 1200 ms;
it establishes bounded feasibility, not a matched neural resource-cost baseline.
No new hardware mapping, corrected-hub causal contrast, predictive activity
budget, biological escape model or population reliability is established.
''')
    page('Supplementary visual diagnostics')
    figure('audit/editorial-v5-horizons/estimands.pdf',
           'Individual paired whole/common/400-ms estimands. Shape and color identify bearing; negative-bearing pairs reuse calibration scenarios, while positive bearings still share calibration seeds. The black line is the median of all 12 pairs.',
           height='2.8in')
    figure('audit/editorial-v5-figures-final/revision_curves.pdf',
           'Archived deletion doses, 12 trials each. Points are medians; bars show observed 10th--90th percentiles, not confidence intervals. Healthy references and the 51.4-Hz transmission threshold are separate lines.',
           width=r'.57\textwidth', height='2.8in')
    figure('audit/editorial-v5-figures-final/revision_activity.pdf',
           'Historical network spikes in thousands, logarithmic scale. Each dot is a trial; horizontal segments are medians. The dashed twofold limit is operational, not an energy or safety budget. Both random-mass tail trials are retained.',
           width=r'.57\textwidth', height='1.7in')
    page('Legacy diagnostics and reproduction')
    figure('audit/editorial-v5-figures-final/revision_demo.pdf',
           'Legacy illustration, not a test of corrected geometry. The separation trace uses +30 degrees, seed 0. Squares/diamonds are whole/400-ms medians; dots show 400-ms pairs, open for calibration scenarios. Whole records can have unequal durations. Full-hub equal-duration late crossings remain valid in main Figure 3.',
           width=r'.56\textwidth', height='3.2in')
    figure('audit/editorial-v5-figures-final/assessment_windows.pdf',
           'Post-hoc early-window diagnostics, all 12 scenario pairs and three shared seed medians. The 500-ms endpoint does not cover the full-hub late crossings. Refer to main Figure 3 for the complete one-second time course.',
           height='2.6in')
    page('Reproduction and exact artifact access')
    parts.append(r'''The review package contains \texttt{main.pdf}, this
\texttt{supplement.pdf}, a material index and the matching source/data ZIP.
The current revision is prepared locally; it has not been submitted or published.
The repository link in the paper alone does not expose this revision. For review,
the current files must be supplied through a permitted submission mechanism or
an explicitly authorized accessible release. A hash check is evidence of file
identity, not public availability or acceptance.

\textbf{Read-only reconstruction.} From the repository root, install the declared
analysis dependencies in a CPython environment, then use each campaign's
\texttt{analyze()} function to compare against its saved JSON. Entry points are
\begin{itemize}
\item \path{tools/analyze_controls_v4.py}
\item \path{tools/analyze_horizons_v4.py}
\item \path{tools/analyze_refractory_v4.py}
\item \path{tools/summarize_prospective.py}
\end{itemize}
The scripts refuse accidental overwrite of their original output directories.
Raw reconstructions require no new neural simulation. Exact build commands,
versions and expected external-input hashes are in \texttt{REPRODUCE.md}.

\textbf{Source and data identity.} The artifact manifest lists every included
file by SHA256 and size, and binds both PDFs to their sources. External
\texttt{Connectivity\_783.parquet} and \texttt{Completeness\_783.csv} tables remain
separate dependencies from the released Shiu model repository. Expected hashes
and Windows newline normalization are documented; no table values were changed.
The calibration file remains byte-identical across both prospective campaigns.
No final-release source hash is substituted for a missing older generation hash.
The bundled upstream source snapshots retain their license notice.

\textbf{Reporting procedure supported by this case study.} Report the cohort
denominator and condition composition; identify the functional and activity
criteria separately; state the paired stopping rule; inspect full-horizon
activity; and report task outcomes by direction and independent seed cluster.
These reporting choices clarify evidence without establishing a safety predictor.

\textbf{Prior work and inherited components.} The manuscript bibliography supplies
the full verified citations. The neural substrate follows Shiu et al., Nature
2024, DOI 10.1038/s41586-024-07763-9. Close comparisons include An's sparsification
study, DOI 10.64898/2026.09.19.752860, and Jo's endpoint-dependent damage study,
arXiv:2610.19153. NeuroBench, DOI 10.1038/s41467-025-56739-4, already motivates
separate functional/system measures. Our contribution is the quantified case
study of cohort, exposure, horizon and feedback-law dependence; neither adding
a nested constraint nor defining a ratio is claimed as an algorithmic invention.

\textbf{Historical documentation.} Protocols v2--v4 and earlier repair reports are
retained for chronology. Their old pending-work statements are superseded by
this current supplement and its campaign index. Historical raw records remain
immutable; only current summaries, presentation and delivery files are revised.
''')
    figure('audit/pathway-v4/fig0_pathway.pdf',
           'Mapped pathway retained from the previous main Figure 1. For display, 90 of 849 relays are selected by summed sensory-input and command-output contacts. Labels follow mapped identities; line strength encodes contacts and dashed markers locate perturbations. Generator and input hashes accompany the artifact. This display does not establish a dynamical mechanism; the new main Figure 1 is a conceptual overview.',
           width=r'.55\textwidth', height='1.55in')
    from supplement_cross_v8 import append_cross
    sources.add(ROOT / 'tools/supplement_cross_v8.py')
    append_cross(parts, table, page, figure, cross, independent)
    parts.append(r'\end{document}' + '\n')
    tex = out / 'supplement.tex'
    tex.write_text('\n'.join(parts), encoding='ascii')
    manifest = {'version':'assessment-v8', 'tables':table_count,
                'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)},
                'generator_sha256':sha(Path(__file__)), 'simulations_executed':False}
    for pass_number in (1, 2):
        command = ['pdflatex','--disable-installer','-interaction=nonstopmode',
                   '-halt-on-error','-file-line-error','supplement.tex']
        result = subprocess.run(command, cwd=out, capture_output=True)
        (out / f'pass{pass_number}.txt').write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'supplement compilation failed: {out}/pass{pass_number}.txt')
    log = (out / 'supplement.log').read_text(errors='replace')
    problems = re.findall(r'[^\n]*(?:Overfull \\[hv]box|undefined|Missing character:)[^\n]*', log)
    manifest.update(latex_problems=problems, pdf_sha256=sha(out/'supplement.pdf'),
                    tex_sha256=sha(tex))
    (out/'supplement_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if problems:
        raise ValueError(f'supplement layout/citation errors: {problems}')
    shutil.copyfile(out/'supplement.pdf', ROOT/'paper/supplement.pdf')
    print(json.dumps({'tables':table_count,'output':str(out),'pdf_sha256':manifest['pdf_sha256']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    generate(parser.parse_args().out.resolve())
