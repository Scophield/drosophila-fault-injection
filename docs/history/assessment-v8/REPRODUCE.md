# Reproducing and auditing the paper

## Current assessment-v8 path

The October 21 major revision completes Original/Pre-cue gate x
Healthy/F2_25/F2_50 on seeds 12--17 at -30/+30 degrees. There are 72 records:
24 byte-identical preserved healthy episodes and 48 new fault episodes. The
conditions share frozen calibration and generating sources. See
`paper/PROTOCOL_v8.md` for seed rules, nested masks, stopping rules and evidence
tiers; `REVISION_V8_REPORT_zh.md` maps the review requests to the changes.

Read-only reconstruction and figure commands, each using a new output directory:

```text
python tools/analyze_controller_fault_v8.py --root runs/controller-fault-v8 --out audit/my-cross
python tools/audit_cross_v8.py --summary audit/my-cross/cross.json --out audit/my-cross-audit
python tools/plot_controller_fault_v8.py --summary audit/my-cross/cross.json --out audit/my-cross-figures
python tools/plot_prospective.py --summary audit/prospective-v3.json --out audit/my-prospective-figure
```

The first command independently checks completion, generation snapshots, runtime,
calibration, trajectory outcomes and trigger/steering laws. The second recomputes
losses/gains and interaction signs from raw outcomes, compares conditional ranges
with all 6^6 exact cluster resamples, and reconstructs archived threshold counts.
`pairs.csv` contains all 48 fault/healthy pairs and fixed/common-duration ratios;
`thresholds.csv` contains the 64 law/dose/window/threshold combinations.

To repeat the incremental neural campaign using the preserved healthy inputs:

```text
python tools/run_controller_fault_v8.py --out runs/my-cross
```

Use `--resume` only after confirming a previous invocation stopped. It verifies
the same configuration and skips completed episodes. Source/package changes are
rejected rather than mixed with preserved healthy records. The successful resume
elapsed time excludes the interrupted invocation; the sum of measured times for
all 48 fault episodes is reported separately. No unmeasured total is estimated.

For a new complete independent replication, create the run directory, set
FLY_RUN_DIR and FLY_CODEGEN_TARGET=numpy, and use the unchanged neural CLI:

```text
python sim_vision/run_closedloop.py --tag controls --modes brain,precue_gated --phis=-30,30 --seeds 12,13,14,15,16,17 --faults none,F2_25,F2_50 --calibration runs/geometry-v3/vision/calib-geometry-v3.json
```

Its new calibration/manifest locations must be retained with the outcomes. The
incremental analyzer deliberately expects the included v8 provenance layout; it
must not be presented as a generic analyzer for a different campaign.

Current PDF builds use `tools/build_paper.ps1` with a new absolute BuildDirectory,
and `python tools/build_supplement_v5.py --out audit/my-supplement-v8`. The latter
retains its filename for continuity and now reads the completed v8 summary at
`audit/controller-fault-v8/cross.json`, plus the saved current figure paths. It
creates 22 tables and nine figures. Main and supplement opening entries are in
`REVIEW_MATERIALS.md`. The descriptive v8 PDFs are exact copies of the current
`paper/main.pdf` and `paper/supplement.pdf`, bound by the release manifest.

## Preserved assessment-v7 path

Start with `REVIEW_MATERIALS.md` and `paper/supplement.pdf`. All measurements are
unchanged from assessment-v4. The current supplement consolidates tables S1--S16
and figures S1--S8, with sample, estimand and uncertainty definitions. Historical
protocol files below remain for chronology, not as current pending-work lists.
`OVERVIEW_FIGURE_REPORT.md` records the current visual revision;
`SUBMISSION_FIX_REPORT.md` records the preceding PDF repair.
The existing supplement generator name is retained for continuity; it now emits
assessment-v7. Scientific measurements and neural generating sources are unchanged.

```text
python tools/build_supplement_v5.py --out audit/my-supplement
```

The conceptual main Figure 1 is generated without simulation or external inputs:

```text
python tools/plot_overview_v7.py --out audit/my-overview
```

Copy its `assessment_overview.pdf` to `paper/figs/assessment_overview.pdf` before
building the paper. The same directory contains editable SVG, a 600-dpi PNG and
the input/output manifest. The former main pathway is Supplementary Figure S8.

The supplement build requires analysis/plot dependencies and the installed `pdflatex`
on PATH. It uses saved measurement JSON and current figure PDFs; it performs no
neural simulation. Compilation checks overflow and references before promoting
`paper/supplement.pdf`. Use a fresh output directory. Figure generators take
explicit new outputs; the current figure source locations are in the manifest.

## Preserved assessment-v4 experiment path

Start with `CONTROL_FIX_REPORT.md` and `paper/PROTOCOL_v4.md`. The original
assessment-v3 commands below remain reproducible. New read-only reconstructions:

```text
python tools/analyze_horizons_v4.py
python tools/analyze_controls_v4.py
python tools/analyze_refractory_v4.py
python tools/plot_horizons_v4.py
python tools/plot_controls_v4.py
```

These campaign-specific audit scripts deliberately refuse to overwrite their
saved output directories. To recompute a packaged summary without writing,
import its `analyze()` function and compare to the included JSON. For example:

```text
python -c "import sys,json; sys.path.insert(0,'tools'); from analyze_controls_v4 import analyze; from pathlib import Path; assert analyze()==json.loads(Path('audit/controls-v4/controls.json').read_text()); print('matched')"
```

To rerun neural controls, choose a new run directory and reuse the frozen
calibration without refitting. Example POSIX commands (PowerShell environment
syntax appears below):

```bash
export FLY_CODEGEN_TARGET=numpy
export FLY_RUN_DIR="$PWD/runs/my-controller-replay"
python sim_vision/run_closedloop.py --tag controls --modes brain,precue_gated,bias_only,steer_disabled --phis=-30,30 --seeds 12,13,14,15,16,17 --faults none --calibration runs/geometry-v3/vision/calib-geometry-v3.json
```

The released campaign used three workers, disjoint seed pairs per worker, with
the same parameters above. `runs/controller-v4a/campaign.json` records the frozen
matrix; each batch retains source snapshots, per-episode times and manifests.
`tools/check_refractory_v4.py` records the separate three-seed/600-ms variant
campaign. Exact outcomes need not be bitwise identical on a different runtime.

Archive matching is not horizon selection. For deletion, common-duration
matching changes the paired ratio; full-hub/healthy records already both last
one second and show six late crossings at 840--900 ms.

## Earlier assessment-v3 path

The historical archive instructions below remain available. Current additions:
For ZIP extraction and Git-check requirements, start with `ARTIFACT_README.md`.

```text
python tools/audit_assessment.py --out audit/my-assessment
python tools/audit_revision.py --out audit/my-revision
python tools/plot_revision.py --analysis audit/my-revision/revision_analysis.json --assessment audit/my-assessment/assessment.json --out audit/my-figures
python -m unittest discover -s tests -v
```

Use a normal CPython 3.12+ virtual environment (3.13.15 was exercised) and
`python -m pip install -r requirements.txt`. The earlier claimed environment is
preserved in `requirements-historical.txt`; it is not advertised as validated.
Brian2 2.9.0 failed against the available NumPy because ndarray.ptp was removed.
The new actual network execution uses Brian2 2.10.1 and NumPy 2.5.4. SciPy is
required for graph analysis; the NumPy backend does not require an MSVC compiler.

Use `FLY_CODEGEN_TARGET=numpy` for the exercised portable backend. Default Cython
execution still requires a separately configured compiler. Example POSIX commands:

```bash
export FLY_CODEGEN_TARGET=numpy
export FLY_RUN_DIR="$PWD/runs/my-geometry"
python sim_vision/run_closedloop.py --tag calibration --modes observe --evaluation-role calibration --seeds 0,1,2 --phis=-60,-30,0 --duration-ms 400
python sim_vision/calibrate_readout.py --input runs/my-geometry/vision/episodes_calibration --out runs/my-geometry/vision/calib.json
python sim_vision/run_closedloop.py --tag evaluation --modes brain --seeds 6,7,8,9,10,11 --phis=-30,30 --faults none,F2_25,F2_50 --calibration runs/my-geometry/vision/calib.json
python sim_vision/run_closedloop.py --tag controls --modes readout_disabled --seeds 6,7,8,9,10,11 --phis=-30,30 --calibration runs/my-geometry/vision/calib.json
python tools/summarize_prospective.py --root runs/my-geometry --calibration runs/my-geometry/vision/calib.json --modes brain,readout_disabled --out audit/my-prospective.json
python tools/task_reference.py --out runs/my-task-reference
```

PowerShell uses `$env:FLY_CODEGEN_TARGET='numpy'` and `$env:FLY_RUN_DIR=...`.
All outputs must be new. Do not copy the frozen threshold from one RF/threat
configuration into another. The test matrix has six independent seed
clusters at two bearings; it does not establish generality over tasks or models.

The actual full-connectome sensory refractory diagnostic can be rerun with:

```bash
python tools/validate_simulator.py --out runs/my-runtime --backend numpy --seeds 0 --duration-ms 100
```

Current measured pilot: 13.2 and 12.0 seconds for 100 ms, excluding network setup.
Frame-wise closed-loop execution is slower. These timings are local observations.

`tools/make_release.py` builds a new ZIP from explicit scientific inputs and
verifies every file against its manifest. The ZIP is local until publication is
explicitly requested. Current results and limitations are documented in
`ASSESSMENT_FIX_REPORT.md` and `paper/PROTOCOL_v3.md`.

The shipped `sim/results/` and `sim_vision/results_vision/` are immutable historical
records from submission commit `051dcb6a3123841041a34d3b43395e2841975879`.
The current paper distinguishes reanalysis of that archive from the fresh
geometry-v2 calibration and evaluation under `runs/geometry-v3/`. Corrected
hub-selection contrasts remain unmeasured. See `ASSESSMENT_FIX_REPORT.md` for
current status; `REVISION_REPORT.md` and `REPAIR_REPORT.md` retain earlier stages.
Never merge fresh JSONL trials into these directories or substitute the lean F4
records for a different backend without an explicit comparison.

## 1. Lightweight archive audit (no connectome or Brian2 required)

Use Python with NumPy; plotting additionally needs matplotlib. The protocol regression
tests additionally use pandas. Run from the repo root.
Choose a **new, empty output directory** on every invocation; the scripts refuse reuse.

```bash
python -m unittest discover -s tests -v
python tools/audit_revision.py --out audit/local-revision
python tools/plot_revision.py --analysis audit/local-revision/revision_analysis.json --out audit/local-revision-figures
python sim_vision/analyze_closedloop.py --tag v4 --out audit/local-legacy-splits.csv
python tools/audit_archive.py --out audit/local-check
python sim_vision/score_protocols.py --out audit/local-protocol.json
python sim/analyze.py --derived audit/local-check --out audit/local-figures
python sim_vision/fig_demo.py --tag v4 --out audit/local-demo
python tools/check_reproduction.py
```

The paper's current deletion and legacy-demo figures are produced by
`plot_revision.py`; `sim/fig_pathway.py` produces the pathway schematic. The older
`sim/analyze.py` and `fig_demo.py` commands produce legacy diagnostic figures, including
the withdrawn pathway-mass comparison; they are not the current publication pipeline.

`audit_revision.py` saves all 19 main-sweep condition summaries in `fault_families.csv`,
calibration-overlap partitions, matched episode-duration and first-400-ms ratios,
seed-cluster bootstrap intervals, envelope sensitivity and raw-input SHA256 hashes in
`revision_analysis.json`. The first 400 ms is a post-hoc common-exposure diagnostic.
The intervals resample only three fault-seed clusters with azimuths kept together;
they do not establish independent test performance. See `paper/PROTOCOL_v2.md` for
endpoint equations, the complete dose table and historical/fresh protocol differences.

`audit_archive.py` generates summary statistics, 20,000-resample percentile bootstrap
CIs for the median (trial-record resampling within each condition, NumPy seed 0),
`hub_sign.json` directly from raw records, protocol scores, deletion/survival ratios,
paired closed-loop activity ratios and an input-SHA256/version manifest. It rejects
incomplete main sweeps, duplicate trial IDs and ambiguous duplicate conditions.
The original `hub_sign.json` has no tracked generator; its plotted medians can be
recovered from the records by this script. This reconstructs values, not its lost
creation history. Plots read the newly derived file explicitly.

The 288-record protocol comparison uses 18 non-healthy main conditions plus six
HUB/EIm/random-inhibitory controls, all at 150 Hz. Transmission-only scoring gives
276 passes, joint scoring gives 262. The 14 extra failures are 12 HUB_inh and two
INHrand_mass trials (IDs 3 and 9). This re-scores records; it does not execute SpikeFI
or SpikingJET. The open-loop joint rule is `rate >= 51.4`, `rate <= 2*94.6875`, and
`spikes <= 2*39694`, per trial. Closed-loop activity instead compares each episode's
total spikes with the healthy episode at the same azimuth and seed; collision-free
survival is a separate endpoint. Ratios of pooled medians cannot replace this test.
The former 24/24 healthy total includes six calibration episodes. Its 18 non-overlapping
records are a post-hoc partition, not a new independent test. For F2_50, the median
episode-total ratio is 0.382; the matched first-400-ms ratio is 0.723.

## 2. External model inputs and historical environment

Expected portable layout:

```text
<parent>/drosophila-fault-injection/
<parent>/Drosophila_brain_model/model.py
<parent>/Drosophila_brain_model/Completeness_783.csv
<parent>/Drosophila_brain_model/Connectivity_783.parquet
```

The external repository is https://github.com/philshiu/Drosophila_brain_model .
Obtain it only when data download is authorized. Its Git commit was not pinned in
the original archive; record the acquired SHA as well as these expected data hashes:

```text
Connectivity_783.parquet  efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347
Completeness_783.csv      bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311
```

During this repair, an authorized sparse input checkout was obtained at upstream SHA
`91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`. Connectivity matches the expected checksum.
Completeness has the expected hash in its Git blob; Windows checkout CRLF produces
worktree SHA256 `52b0ac6094cd32c546f8d4c341e094376f48f4e791f8db9b166de5dff8199ea4`.
The bytes are identical after CRLF-to-LF normalization. No scientific values were edited.
`audit/verified-hubs/` contains the reconstructed lists and input/version hashes.

`sim/project_paths.py` is the common resolver. The default is the sibling directory;
set `FLY_MODEL_DIR` to an explicit alternative, with no machine-specific path in code.
`sim/data/annotations.tsv` is already tracked (about 31.9 MB). No submodules or LFS
pointers were found. Cloning this repository does not supply the experimental environment.

The historical environment reported CPython 3.11 and the pins now retained in
`requirements-historical.txt`. Those claims were not independently validated.
The current requirements and actual NumPy-backend measurements are described at
the start of this document and in `runs/simulator-v3/validation.json`. The upstream
model also imports joblib, whose original version was not recorded. Brian2's
Cython backend still needs a working compiler and remains unvalidated here.

Before any simulation, reconstruct selectors without building a network:

```bash
python tools/check_reproduction.py --require-model
python tools/audit_hubs.py --out audit/hubs-with-inputs
```

The hub audit compares old index-exclusion, old mapped-exclusion and corrected
selection, saving actual reconstructed FlyIDs, sign composition, edge/contact
counts, protected overlaps, differences and hashes. Without the external tables
these values cannot be produced. Reconstructed old-code sets still do not establish
which sets historical runs actually used, because their manifests were not saved.

The corrected definition ranks integer outgoing contacts, breaks ties by ascending
FlyID, and excludes sensory and command-readout **FlyIDs**, not indices. It is shared
by main real/null sweeps, controls, lean recheck and closed loop. Each fresh hub run
saves selected FlyIDs and their SHA256 (sorted numeric IDs, decimal ASCII, newline
per ID). A target-only permutation must leave the selection and outgoing row count
unchanged for the same source table and definition; arbitrary heterogeneous graphs
need not have identical damage counts.

## 3. Unexecuted extended campaigns

The following broader commands remain a **plan**, not a record of execution.
Archived estimates were about 2.4 GB and one hour per main phase, but actual costs
depend on the backend and campaign. The focused assessment-v3 NumPy processes use
about 1.2 GB each; several independent batches can run concurrently when memory
and CPU capacity permit. Validate input checksums and available resources first.

Choose a new run tree (POSIX example; PowerShell uses `$env:FLY_RUN_DIR=...`):

```bash
export FLY_RUN_DIR="$PWD/runs/corrected-v1"
# Optional: export FLY_MODEL_DIR="<parent>/Drosophila_brain_model"
python sim/calibrate.py
python sim/sweep.py --phase real --trials 12 --budget 10800
python sim/sweep.py --phase er --er-seed 17 --trials 12 --budget 10800
python sim_vision/controls_openloop.py --trials 12 --budget 10800
python sim_vision/inhib_controls.py --trials 12 --cond INHrand_cells INHrand_mass
python sim/pathway_analysis.py
```

`controls_openloop.py` accepts `--only` (substring filter), `--trials`, `--budget`,
`--resume`; it does not accept `--cond all`. Do not split filters into the same output
component, because different configurations are intentionally rejected. A stopped
batch may use exactly the same arguments plus `--resume`, only if its code, model,
parameters and package manifest still agree. Unseeded Poisson streams mean that a
resumed open-loop batch is not bit-identical to an uninterrupted one. Use a fresh
run tree when either configuration or implementation changes.

An optional cross-backend F4 diagnostic has its own healthy baseline and output
component `recheck_real`, never the main `core/real` folder:

```bash
python sim_vision/f4_recheck.py --trials 12
```

It therefore cannot silently skip the main sweep's existing trial IDs or overwrite
its results. Compare its hub manifests, baseline and responses separately. The old
~100k versus ~49k activity change cannot be attributed exclusively to backend/chunking:
archived selector counts also changed. A controlled matched rerun is needed.

## 4. Fresh geometric closed loop and independent calibration

The expanded five-bearing matrix below remains a proposed extension; assessment-v3
executes the focused two-bearing matrix at the start of this document. The archive's `calib.json`
is retained for archive analysis and is rejected by the fresh geometry-v2 runner.
The revised runner uses heading-relative bearing, actual-separation angular expansion,
planar retinal elevation zero, collision checks within each frame, a 0.1 ms neural
timestep and a fixed requested horizon. A surviving episode may still be bursting
at the horizon; its metadata states that explicitly. No eventual-escape claim follows.

The fitting bootstrap dependency is removed: `observe` episodes have no steering,
threshold or burst. Collect a complete passive grid, fit once, then use new seed
clusters for all test scenarios. The fitter records source hashes and scenario IDs;
the runner rejects shared calibration seeds even at different azimuths.

```bash
export FLY_RUN_DIR="$PWD/runs/geometry-v2"
python sim_vision/run_closedloop.py --tag calibration --modes observe --evaluation-role calibration --seeds 0,1,2 --phis=-60,-30,0 --duration-ms 400
python sim_vision/calibrate_readout.py --input runs/geometry-v2/vision/episodes_calibration --out runs/geometry-v2/vision/calib-geometry-v2.json
python sim_vision/run_closedloop.py --tag evaluation --modes brain --seeds 6,7,8,9,10,11 --phis=-60,-30,0,30,60 --faults none,F2_25,F2_50,F4_1pct,HUB_inh,HUB_exc --calibration runs/geometry-v2/vision/calib-geometry-v2.json
python sim_vision/run_closedloop.py --tag controls --modes steer_disabled,readout_disabled,flip,handrule --seeds 6,7,8,9,10,11 --phis=-60,-30,0,30,60 --calibration runs/geometry-v2/vision/calib-geometry-v2.json
python sim_vision/analyze_closedloop.py --tag evaluation --input runs/geometry-v2/vision --calibration runs/geometry-v2/vision/calib-geometry-v2.json --out audit/geometry-v2-evaluation.csv
```

This proposed extension contains nine calibration, 180 brain and 120 control episodes;
its complete runtime has not been measured. Each invocation saves a configuration manifest/summary under
`vision/batches/` and unique episodes under `vision/episodes_<tag>/`. Existing episodes
cannot be replaced. Changing code or configuration requires a new run directory;
`--resume` only accepts an identical manifest. Brian2 seeds are `20000+s`, fault
seeds `10000+s`, and the default RF seed is 20260201.

For horizon and actuator-delay sensitivity use `--duration-ms` (whole 20 ms frames)
and `--burst-delay-ms` in separate run trees. Changing `--threat-speed` or `--rf-seed`
requires passive episodes and a calibration with matching settings; do not refit on
test episodes. The hand rule still uses the network trigger and is only a steering
reference, not an independently calibrated fault-tolerance baseline. These sensitivity
experiments and a functioning matched-controller baseline remain unmeasured.

Optional fresh visual-encoding open-loop runs:

```bash
python sim_vision/run_openloop.py
```

These use `vision_openloop/`, with newly explicit `20000+seed` Poisson seeding. The
old script only labeled seeds without re-seeding inside its loop. New records cannot
be advertised as bit-identical replays of those archived visual-encoding runs.
Fresh visual runs also stop after exactly `duration_ms/FRAME_DT_MS` frames; the old
endpoint-inclusive loop would run 620 ms for a nominal 600 ms trajectory. Legacy
records lack duration metadata, so `analyze_openloop.py` requires an explicit
`--legacy-duration-ms` assumption (600 for reproducing old nominal summaries; 620
for the checked old generator). It reports per-cell mean command rate rather than
summed eight-cell rate. Neither assumption establishes missing historical timing.
The main constant-drive sweep and closed-loop episode scoring do not use this visual
open-loop duration assumption.

## 5. Analyze only after the required runs finish

```bash
python tools/audit_archive.py --run-root "$FLY_RUN_DIR" --out audit/corrected-v1-analysis
python sim/analyze.py --results "$FLY_RUN_DIR/core" --pathway "$FLY_RUN_DIR/graph/pathway_mass.json" --derived audit/corrected-v1-analysis --out audit/corrected-v1-figures
python sim_vision/analyze_closedloop.py --tag evaluation --input "$FLY_RUN_DIR/vision" --calibration "$FLY_RUN_DIR/vision/calib-geometry-v2.json" --out audit/corrected-v1-episodes.csv
```

For new plots, supply the graph input separately using `--pathway` if it lives in
`$FLY_RUN_DIR/graph/pathway_mass.json`. No fresh run may use a stale graph result
without declaring it. The corrected pathway generator now samples original table rows
before CSR coalesces repeated null pairs; archived pathway curves have not been rerun.
Analyze summary, bootstrap, protocol scores and sign activity
from the same completed inputs. The figure error bars are trial 10th--90th percentiles;
95% bootstrap CIs in the text estimate median uncertainty. They are different quantities.

The original seed table describes derivation rules, not proof of complete deterministic
state restoration. Fixed fault masks are traceable; unseeded open-loop stimulus streams
advance across trials. Closed-loop seeds improve repeatability within a fixed software
and scheduling configuration but do not guarantee cross-platform bit identity. Validate
counts, input/selection hashes and statistical distributions; preserve raw realizations.

## 6. Paper compilation and QA

Paper-only compilation uses tracked figures and references, without simulation inputs.
Use a TeX distribution with IEEEtran, cite, AMS packages, graphicx, xcolor, booktabs,
placeins, TikZ and url. Preferred command from the repository root (choose a new directory):

```bash
powershell -File tools/build_paper.ps1 -BuildDirectory audit/local-paper-build
python tools/qa_pdf.py --pdf paper/main.pdf --out audit/local-paper-qa --submission
```

The build script stages sources and figures in the new build directory, then runs
pdfLaTeX, BibTeX and pdfLaTeX twice. This prevents a stale `paper/main.bbl` from
shadowing the regenerated bibliography. It preserves historical intermediate files
and copies the PDF to `paper/main.pdf` only after successful passes. Do not delete
archived `.bbl` files or results to force a rebuild. Verify the final log for undefined citations/references,
overfull boxes and missing glyphs, render every page, and inspect fonts (no Type 3,
all text fonts embedded). `fig_demo.py` now sets `pdf.fonttype=42` explicitly.
The official [ISCAS 2027 author instructions](https://epapers2.org/iscas2027/ESR/authorinfo1.php)
(checked 2026-10-21) allow four technical pages plus an optional fifth page containing
only references, require embedded fonts, and instruct authors to avoid Type 3. No font shrinking or
page enlargement is used to meet the limit. Current verification and remaining limits are in
`SUBMISSION_FIX_REPORT.md`.
The official [PDF Help](https://epapers2.org/iscas2027/ESR/author_help.php), checked
2026-10-21, also requires no bookmarks, hyperlinks, form fields or page numbers,
and PDF 1.4 or higher. The main source uses printable `url` without `hyperref`.
QA checks saved PDF feature objects, not link appearance; inspect every rendered
main page for typography and absence of page numbers. The separate supplement
retains page numbering and is not certified as a permitted venue attachment.
