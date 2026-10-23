"""Append measured factorial results without renumbering earlier supplement tables."""
LABELS = {'brain': 'Original', 'precue_gated': 'Pre-cue gate'}


def append_cross(parts, table, page, figure, cross, independent):
    page('Controller-by-fault comparison: frozen calibration')
    parts.append(r'''This incremental campaign adds 48 actual full-connectome fault
episodes and reuses 24 byte-identical healthy episodes from the paired controls.
The six seed clusters (12--17), both bearings, calibration, receptive-field map,
neural sources and package versions are shared across all six conditions.
Healthy outcomes were already known when this extension was specified; the
fault outcomes were not used to retune the controller. Each seed uses Brian2
seed $20000+s$ and deletion seed $10000+s$. F2 deletes weighted connection-table
rows, including all contacts represented by each row. The same row mask is used
across controllers and bearings. The 25/50-percent masks are nested draws,
not independent fault realizations.

Let $Y_H,Y_F$ denote 1000-ms collision-free survival under the same law,
bearing and seed. Loss is $L=I(Y_H=1,Y_F=0)$; gain is
$G=I(Y_H=0,Y_F=1)$; net loss is $D=Y_H-Y_F=L-G$.
Loss counts are out of all 12 scenarios; the healthy survivors at risk are
also reported. Both bearings and all six conditions remain together within each
seed cluster. Thus 72 records do not represent 72 independent observations.
''')
    rows = []
    for mode in cross['modes']:
        for fault in cross['faults']:
            g = cross['groups'][f'{mode}/{fault or "healthy"}']
            rows.append([LABELS[mode], 'Healthy' if fault is None else fault[-2:]+r'\%',
                         f"{g['by_bearing']['-30.0']}/6", f"{g['by_bearing']['30.0']}/6",
                         f"{g['collision_free']}/12", g.get('task_losses', '---'),
                         g.get('task_gains', '---'), g.get('healthy_survivors', '---')])
    table('Complete factorial outcomes. L/G: paired losses/gains; H: healthy survivors at risk. Healthy rows are reused, not new runs.',
          ['Law', 'Deletion', '$-30^\\circ$', '$+30^\\circ$', 'Total', 'L', 'G', 'H'], rows, 'llrrrrrr')
    names = [(mode, fault) for mode in cross['modes'] for fault in cross['faults']]
    labels = [LABELS[m]+' '+('H' if f is None else f[-2:]) for m, f in names]
    def outcome(mode, fault, phi, seed):
        if fault is None:
            return next(p['healthy_survived'] for p in cross['pairs']
                        if (p['mode'], p['phi'], p['seed']) == (mode, phi, seed))
        return next(p['fault_survived'] for p in cross['pairs']
                    if (p['mode'], p['fault'], p['phi'], p['seed']) == (mode, fault, phi, seed))
    table('Every scenario outcome: each cell lists binary survival (-30,+30 degrees). H denotes healthy; 25/50 denote deletion percentages.',
          ['Seed']+labels,
          [[s]+[','.join(str(int(outcome(m,f,p,s))) for p in cross['azimuths'])
                 for m,f in names] for s in cross['test_seed_clusters']], 'lrrrrrr')
    table('Every paired loss/gain count within seed (two bearings). A gain is retained rather than discarded from the net loss.',
          ['Seed', 'Original 25', 'Original 50', 'Gate 25', 'Gate 50'],
          [[s]+[','.join(str(sum(p[field] for p in cross['pairs']
                                 if (p['mode'],p['fault'],p['seed']) == (m,f,s)))
                         for field in ('task_loss','task_gain'))
                 for m in cross['modes'] for f in cross['faults'][1:]]
           for s in cross['test_seed_clusters']])
    page('Paired interaction, activity and threshold sensitivity')
    parts.append(r'''The interaction is $D_{\rm gate}-D_{\rm original}$, after
averaging both bearings within seed. Positive values mean greater net fault
loss under gating. Conditional 95-percent percentile ranges use 20,000 complete
six-cluster bootstrap draws with RNG seed 0. These exploratory ranges are
conditional on the frozen calibration and fixed bearings. They do not establish
population coverage, equivalence or a controller mechanism. The +30-degree
healthy floor limits observable loss in that direction.
''')
    parts.append(r'''After observing the conditional bootstrap ranges, we added a
post-hoc sign-flip sensitivity, applying all $2^6=64$ sign patterns to the
six seed-level interaction contrasts. Under an independent-cluster, symmetric
zero-centered interaction null, the two-sided tail fraction is 0.25 at 25-percent
deletion (three nonzero clusters) and 0.50 at 50-percent deletion (two nonzero
clusters). This diagnostic is not a randomized controller-assignment test or
confirmatory population inference. The positive percentile range at 25 percent
must be interpreted with this sparse support; it is not a claim of established
controller-dependent neural resilience. At 50 percent, both faulty controllers
have zero survivors, so the net-loss contrast reflects healthy baseline success.
''')
    table('Controller interaction, in percentage points (pp). Six seed values are the actual independent cluster contrasts, not six extra experiments.',
          ['Deletion', 'Six seed contrasts (pp)', 'Mean (pp)', 'Range (pp)'],
          [[fault[-2:]+r'\%', ', '.join(f'{100*v:g}' for v in q['seed_values']),
            f"{100*q['mean']:+.1f}", '['+', '.join(f'{100*v:.1f}' for v in q['conditional_cluster_bootstrap95'])+']']
           for fault,q in cross['interactions'].items()], 'llrr')
    table('Median within-scenario fault/healthy network-spike ratios under the same law. Each cell retains all 12 pairs. Common duration is pair-specific and outcome-dependent.',
          ['Law / deletion', '200 ms', '300 ms', '400 ms', '500 ms', 'Common'],
          [[LABELS[m]+' '+f[-2:]+r'\%']+
           [f"{cross['groups'][m+'/'+f]['activity_medians'][str(w)]:.4f}" for w in (200,300,400,500)]+
           [f"{cross['groups'][m+'/'+f]['common_duration_median']:.4f}"]
           for m in cross['modes'] for f in cross['faults'][1:]])
    threshold_rows = []
    fields = ('flagged_collisions','unflagged_collisions','flagged_survivors','unflagged_survivors')
    for mode in cross['modes']:
        for fault in cross['faults'][1:]:
            for window in (400,500):
                group = [q for q in cross['thresholds'] if (q['mode'],q['fault'],q['window_ms']) == (mode,fault,window)]
                reference = next(q for q in group if q['c']==2)
                if any(any(q[k]!=reference[k] for k in fields) for q in group if q['c']>=2):
                    raise ValueError('cannot combine unequal c=2/3/4 counts')
                for c in (1.5,2):
                    q = next(q for q in group if q['c']==c)
                    threshold_rows.append([LABELS[mode]+' '+fault[-2:]+r'\%', window,
                                           '1.5' if c==1.5 else '2/3/4']+[q[k] for k in fields])
    table('Activity-only flags R(t)>c versus collision/survival through 1000 ms. FC/UC: flagged/unflagged collisions; FS/US: flagged/unflagged survivors. Counts for c=2,3,4 are identical and combined. All four 200--500-ms windows appear in thresholds.csv.',
          ['Law / deletion', '$t$ (ms)', '$c$', 'FC', 'UC', 'FS', 'US'], threshold_rows)
    parts.append(r'''These flags use network spikes only; they are distinct from
the archived open-loop joint rule, which also requires command transmission.
The thresholds are operational definitions, with no validated hardware resource,
power or safety interpretation. No threshold was selected to fit task outcomes.
There is no imputation of neural activity after collision. Activity pairs use
the same controller, bearing and seed at completed common frames.
''')
    figure('audit/cross-figures-v8-final/controller_fault_pairs.pdf',
           'Every paired seed/bearing activity ratio at 400 ms. Lines join the same seed and bearing across nested deletion doses within a control law. Color/shape identify direction; thick black bars are medians. Both bearings share six seed clusters.',
           width=r'.85\textwidth', height='2.8in')
    wall = cross['execution']['wall_seconds']
    parts.append(f"The successful resumed invocation took {wall:.1f} s, including "
                 'worker construction and skipping completed records. This excludes the interrupted invocation. '
                 f"The sum of measured episode times across all 48 new fault episodes is {cross['new_episode_seconds_total']:.1f} s; "
                 'overlapping workers mean this is not CPU time or total campaign elapsed time.\n')
    parts.append(r'''All three resumed workers returned zero. Each completed episode
was written before interruption recovery; the runner verified source/configuration
identity and did not overwrite it. The source and calibration hashes are checked
independently by \path{tools/cross_records_v8.py}. Machine-readable per-scenario
loss, gain, four fixed windows and common duration are in
\path{audit/controller-fault-v8/pairs.csv}; complete summaries and manifests are in
\path{audit/controller-fault-v8/cross.json}. Protocol details and commands are in
\path{paper/PROTOCOL_v8.md}. Corrected historical hub experiments and additional
test bearings remain outside this focused revision.
''')
