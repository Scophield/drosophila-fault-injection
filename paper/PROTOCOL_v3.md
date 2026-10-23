# Endpoint and exposure sensitivity: protocol and artifact v3

This supplement supersedes the current-status statements in PROTOCOL_v2.md.
The archived trials remain immutable. The retrospective analyses and new
prospective runs have separate directories, manifests and interpretations.

## Question and assessment boundary

The empirical question is whether cohort inclusion and common observation
duration change classifications of the same records. Adding a constraint is
not itself a new algorithm or evidence of predictive value. No hardware energy,
safety or biological robustness claim follows from the activity limit.

Canonical terms are **transmission pass**, **joint pass**, **recorded
collision-free count** for legacy data, **collision-free at the requested
horizon** for fresh data, and **output silencing** for F3/F4. A spike total is
an activity measurement. It is not a hardware-energy measurement.

## Retrospective cohort analysis

Run `python tools/audit_assessment.py --out audit/my-assessment` with a new output
directory. It writes `assessment.json`, including every condition's counts,
source hashes, all paired window values, seed medians and effect intervals.
The earlier complete-dose and calibration audit remains reproducible with
`tools/audit_revision.py` and PROTOCOL_v2.md.

With c=2, references are the original healthy medians: 94.6875 Hz and 39,694
spikes; transmission additionally requires at least 51.4 Hz. Scores apply to
individual records. Conditions are excluded before aggregation, without
retuning references. Healthy resubstitution is explicitly not held-out specificity.

| Included records | n | Transmission | Joint | Additional rejections |
|---|---:|---:|---:|---:|
| All fault/control cohorts | 288 | 276 | 262 | 14 |
| Exclude HUB_inh | 276 | 264 | 262 | 2 |
| Exclude all F4, HUB and EIm cohorts | 204 | 192 | 190 | 2 |
| Main F1/F2/F3/F5 only | 180 | 168 | 168 | 0 |
| Healthy reference (resubstitution) | 12 | 12 | 12 | 0 |

The 288 records comprise 18 main fault conditions and six controls, each with
12 trials. Removing only HUB_inh removes 12 records. Removing F4 (three), HUB
(two) and EIm (two) removes 84. The remaining two extra rejections are random
inhibitory expected-mass trials 3 and 9. Mixture pass fractions do not estimate
the population incidence of hardware faults.

## Reference-aware effects

Use independent resampling of the 12 fault and 12 healthy records, 20,000
draws, NumPy seed 0. No pairing is assumed for unseeded archived input streams.
The code propagates variation in both groups and saves ratio and difference
intervals for all four F2 doses. For F2_50, median-rate ratio is 0.764576,
percentile interval [0.751101, 0.789648]. First-spike-latency ratio is 1.33333,
interval [1.25301, 1.40000]. These intervals condition on the historical
connectome, calibration, implementation and drive; they do not establish
cross-connectome generality or equivalence.

## Exploratory window and seed sensitivity

All windows below precede the earliest archived collision. Legacy `t_ms` is a
frame-start label for a post-frame cumulative count: 400 ms uses frame 19.
Ratios pair identical azimuth and seed, before taking their median. All pairs
are retained. These windows were chosen after reviewing the archive and are
not prospective safety thresholds.

| Condition | 200 ms | 300 ms | 400 ms | 500 ms | Whole episode |
|---|---:|---:|---:|---:|---:|
| F2_25 | 0.9067 | 0.8974 | 0.8837 | 0.8965 | 0.8861 |
| F2_50 | 0.7446 | 0.7327 | 0.7226 | 0.7244 | 0.3817 |
| Historical full hubs | 1.3021 | 1.3317 | 1.3618 | 1.4024 | 1.7029 |
| Historical inhibitory hubs | 88.9895 | 119.6414 | 118.1571 | 111.9476 | 71.6931 |

Full-hub twofold exceedances are 0/12 in all four common windows and 6/12 for
whole episodes. Inhibitory hubs exceed 12/12 at every exposure. F2 cohorts
exceed 0/12. These observations concern historical selection definitions.

| First-400-ms median within seed | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| F2_25 | 0.8725 | 0.9607 | 0.8330 |
| F2_50 | 0.6366 | 0.7451 | 0.7226 |
| Full hubs | 1.4050 | 1.3930 | 1.3543 |
| Inhibitory hubs | 124.7201 | 121.3247 | 117.0610 |

Exact enumeration uses 27 ordered draws of three seed clusters, retaining all
four azimuths within each selected seed. There are only 4-7 distinct resulting
median values. Percentile ranges are descriptive rather than confirmatory
coverage statements. `assessment_windows.pdf` shows both pooled and seed-level
curves. `revision_activity.pdf` retains the historical individual-trial plot
on an explicitly logarithmic axis.

## Comparison with prior work

| Work | Substrate / goal | Main comparison | Difference addressed here |
|---|---|---|---|
| An, doi:10.64898/2026.09.19.752860 | Fly-connectome sparsification | Operators, edge budgets, states and several circuits (official abstract) | Cohort exclusion and observation-duration sensitivity on this archive |
| SpikeFI, arXiv:2412.06795; SpikingJET, arXiv:2404.00383 | SNN fault injectors | Injection semantics and faulty inference outputs | These tools are not executed or ranked here |
| enpheeph, doi:10.1109/IROS47612.2022.9982181 | Spiking/compressed networks | Configurable concurrent faults | Tool coverage and resource overhead are distinct questions |
| Gleyo and Girau, doi:10.23919/DATE69613.2026.11539446 | Population-coded regression | Output robustness | Application-specific output context; no shared task benchmark claimed |
| NeuroBench, doi:10.1038/s41467-025-56739-4 | Algorithm/system benchmarking | Separate functional and system metrics | Existing motivation, not an invention of this paper |

## Simulator provenance and material model difference

The upstream sensory routine sets driven neurons' refractory interval to zero;
both project wrappers retain 2.2 ms. Neither is silently substituted for the
other. In the new full-connectome diagnostic, the same seed at constant 150 Hz
for 100 ms produced 93.75 Hz / 6,519 network spikes with 2.2 ms and 102.5 Hz /
8,334 spikes with zero. First spikes were 4.6 and 4.3 ms. This is one paired
pilot, not a population estimate. Raw observations, input hashes, runtime and
code hash are in `runs/simulator-v3/validation.json`.

New actual execution uses CPython 3.13.15, Brian2 2.10.1, NumPy 2.5.4, pandas
3.0.6 and pyarrow 26.0.0, with NumPy code generation and a 0.1 ms neural step.
Brian2 2.9.0 failed import with the available NumPy because ndarray.ptp was
removed. `requirements-historical.txt` preserves the prior claimed pins;
`requirements.txt` specifies the new environment. A full Cython/compiler
environment has not been validated. The embedded interpreter requires project
dependency directories to be inserted explicitly; a normal venv processes its
site-package hooks automatically. An optional CPU-flag subprocess could not
import cpuinfo in the embedded path setup; NumPy execution succeeded.

## Fresh whole-brain calibration and evaluation

Nine passive observe episodes cover -60/-30/0 degrees and seeds 0-2, for
400 ms each. No steering, threshold or burst controls those trajectories.
Calibration is frozen at threshold 18.125 Hz, bias -20 Hz, left/right scale
70 Hz and sign +1, using the declared 250-300 ms fitting window. Input source
hashes and keys are frozen in `runs/geometry-v3/vision/calib-geometry-v3.json`.

The steering law subtracts this frontal bias from the smoothed left/right rate,
including before stimulus onset. With zero readout and bias -20 Hz, it produces
-114.286 degrees/s rather than zero; every healthy episode reaches -11.429
degrees at 100 ms. This is an explicit controller assumption, not spontaneous
neural activity. Calibration covers negative/frontal directions, so directional
generalization must be assessed separately. The threshold or steering law is
not changed after inspecting test outcomes.

The test matrix uses disjoint seeds 6-11, two azimuths (-30/+30 degrees), a
fixed 1 s horizon and brain modes healthy/F2_25/F2_50. Readout-disabled controls use the same seeds
and azimuths. This is a focused six-cluster evaluation, not the previous
four-azimuth archive or proof of broad reliability. The summarizer refuses
missing/duplicate scenarios and mixed calibration hashes. All 48 test records are
complete and verified in `audit/prospective-v3.json`, separate from nine calibration
episodes. The threshold was not retuned after observing failures.

| Condition | -30 degrees | +30 degrees | Total collision-free | Still bursting at horizon |
|---|---:|---:|---:|---:|
| Healthy | 5/6 | 0/6 | 5/12 | 3 |
| F2 25% | 4/6 | 0/6 | 4/12 | 2 |
| F2 50% | 0/6 | 0/6 | 0/12 | 0 |
| Readout disabled | 0/6 | 0/6 | 0/12 | 0 |

| Collision-free count across two bearings per seed | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---:|---:|---:|---:|---:|---:|
| Healthy | 0 | 1 | 1 | 1 | 1 | 1 |
| F2 25% | 0 | 1 | 0 | 1 | 1 | 1 |
| F2 50% | 0 | 0 | 0 | 0 | 0 | 0 |
| Readout disabled | 0 | 0 | 0 | 0 | 0 | 0 |

| Median fault / paired healthy spikes | 200 ms | 300 ms | 400 ms | 500 ms |
|---|---:|---:|---:|---:|
| F2 25% | 0.9103 | 0.9357 | 0.9832 | 1.0073 |
| F2 50% | 0.7484 | 0.8451 | 0.8898 | 1.0123 |

Each cell aggregates 12 azimuth/seed pairs. The JSON also provides all pair values,
directional medians and seed medians. Neither fault exceeds twice the paired
healthy activity in any of these windows, despite 8/12 and 12/12 collisions. This
describes a limitation of that activity limit, not predictive safety validation.
The 48 tests comprise six paired seed clusters per condition, with two bearings
sharing a seed. No iid confidence interval or significance claim is made.
`audit/prospective-figures-v3/prospective_outcomes.pdf` displays directional counts
and all first-400-ms pairs. Generate it with `tools/plot_prospective.py`.

Each batch retains its own generating code hash. Figure-generation edits,
provenance fields and the added privileged-reference branch changed the aggregate
source hash during the campaign; the brain steering equation, neural parameters
and frozen calibration were not retuned. The summary checks common model inputs,
package versions, geometry and timestep across test batches. Generating hashes
remain distinct from the release's final file hashes; no bitwise replay of every
record from one aggregate source hash is claimed.

The separate `geometry_rule` reference uses privileged body-frame bearing and
an onset-triggered burst with the same turn/speed/delay/burst constraints. It
contains no neural model and no activity comparison. Both deterministic
azimuths survive 800 and 1000 ms but collide by 1200 ms. This establishes
bounded task feasibility, not a matched neural hardware-fault baseline.

## Release contract and remaining scope

The local `assessment-v3` bundle contains the exact manuscript, figures,
supplement, analysis, explicitly listed raw inputs, code/tests and validation
records. MANIFEST.json binds each included file by SHA256. External connectome
tables remain an explicit dependency with hashes and upstream instructions.
The bundle is not a remote publication: the earlier public submission branch
remains separate until a commit/push is explicitly authorized.

Predictive budget calibration, larger independent cohorts, corrected hub
contrasts and hardware mapping remain distinct research work. A successful
code repair or new negative result does not guarantee conference acceptance.
