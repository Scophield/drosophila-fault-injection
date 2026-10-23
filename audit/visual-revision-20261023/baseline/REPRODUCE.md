# Reproduce assessment v9 without mixing protocol versions

This is the v9 protocol entry point. The execution/release report records which
commands have actually completed. The registered independent matrices are not
called complete until their full expected record sets pass analysis and replay.
Historical v8 and open-loop material remain separate.

## Environment and inputs

The exercised environment is CPython 3.12.14, Brian2 2.10.1, NumPy 2.5.4 and the
other exact pins in `requirements-v9.txt`. Install into an isolated environment:

```text
python -m venv .venv
# Activate the environment using the command for your shell.
python -m pip install -r requirements-v9.txt
```

The project-local launcher adds `sim/` and `sim_vision/` to Python's search path.
On Windows, use `python -X utf8` (or set `PYTHONUTF8=1`) for Unicode document
and piped-stdin work. The exercised host's legacy locale is cp1252; explicit
UTF-8 avoids mojibake. Do not modify the frozen launcher to change this.
It optionally uses a local `tmp/v9-deps` cache; this cache is not required when
packages are installed in the active environment and is not part of the review
artifact. Do not load the old CP313 binary caches under Python 3.12. The old
recorded Cython3.3 pin conflicts with Brian2's declared requirement; v9 uses
supported Cython3.1.3. NumPy code generation is exercised; no C/C++ compiler is
required by this protocol. A separate pdflatex/BibTeX installation builds PDFs.

The original registered analyzer hit duplicate numeric-margin/Boolean-warning
CSV keys after the complete core was generated. Current commands use
`analyze_task_v9_exportfix.py`, which changes only numeric CSV field names;
original sources, failure logs, statistics, thresholds and data are retained.
See `paper/PROTOCOL_v9_NOTES.md` for this correction and the planning-precision
range clarification. Canonical completed-core analysis is `core-v2/`.

Fresh neural runs require the external model repository, model.py,
Completeness_783.csv and Connectivity_783.parquet, plus this repository's
sim/data/annotations.tsv. The portable default is:

```text
parent/
  Drosophila_brain_model/
    model.py
    Completeness_783.csv
    Connectivity_783.parquet
  drosophila-fault-injection/
    sim/data/annotations.tsv
    sim/
    sim_vision/
    tools/
```

Neural-generation provenance also requires a Git checkout. A source/data ZIP
does not include .git; use a fresh checkout plus the matched artifact rather
than extracting over unrelated local edits. Saved-data analysis/replay does
not require Git or the external connectivity tables.

Set `FLY_MODEL_DIR` to the external model directory when using another layout.
All implementations resolve it through `sim/project_paths.py`. For a new
checkout, the source is https://github.com/philshiu/Drosophila_brain_model,
exercised at 91bdd1e7dcf193f3e7ca5a8933497fcef63b7960. Inspect any existing
checkout and preserve its modifications. The registrations contain exact input
file hashes; a commit name alone is insufficient, including CSV line endings.
Do not silently substitute a different table if the hashes differ.

Whole-neural workers use approximately a few GiB each; the current host has
31.59 GiB physical memory. Limit the supplied launcher to at most three workers.
Measured validation episode times, not hardware energy/area, guide planning.
The 288-episode core was budgeted at roughly four hours with three workers;
the 96-episode stress matrix at about 1.5 hours. Actual execution JSON files
supersede these estimates. Do not describe a source/data ZIP without these
external matrices and installed tools as a complete experimental environment.

## Reanalyse the supplied matched evidence

This path does NOT run neural simulations or require the external matrices.
It needs the supplied code snapshots, maps, calibration, registrations and raw
episode JSON files. Choose new output directories; existing nonempty outputs
are not overwritten. Run only after the corresponding matrix is complete:

```text
python tools/run_v9.py tools/analyze_task_v9_exportfix.py --root runs/task-v9-test --registration runs/task-v9-frozen/registration-core.json --out audit/my-v9-core
python tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v9-test --calibration runs/task-v9-frozen/calibration.json --out audit/my-v9-core-replay
python tools/run_v9.py tools/analyze_task_v9_exportfix.py --root runs/task-v9-stress --registration runs/task-v9-frozen/registration-stress.json --out audit/my-v9-stress
python tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v9-stress --calibration runs/task-v9-frozen/calibration.json --out audit/my-v9-stress-replay
python tools/run_v9.py tools/check_task_numbers_v9.py --root runs/task-v9-test --analysis audit/my-v9-core --registration runs/task-v9-frozen/registration-core.json --out audit/my-v9-core-numbers
python tools/run_v9.py tools/check_task_numbers_v9.py --root runs/task-v9-stress --analysis audit/my-v9-stress --registration runs/task-v9-frozen/registration-stress.json --out audit/my-v9-stress-numbers
python tools/run_v9.py tools/plot_task_v9.py --analysis audit/my-v9-core --out audit/my-v9-figures
```

Analysis requires exactly 288 core records or 96 stress records with every
seed/bearing/law/dose present. It checks original generating snapshots, input
and software bindings, common uniform streams, reproducible nested masks,
complete exposure, exact actuator duration and horizon flags. Statistics use
whole seed clusters, never 288 independent replicates. Outputs include raw-index,
pair, cluster, metric, horizon and activity-profile CSVs plus summary JSON.

The independent replay imports neither task implementation nor neural simulator.
It reconstructs motion, body-frame bearing, actual-separation looming, readout
smoothing, decisions, actuator segments, first contact, masks, uniforms and every
realized input-event hash. It verifies trace/input consistency, not every neuron
state. It uses recorded command outputs; it does not invent replacement results.

Additional secondary descriptive diagnostics, explicitly added after the original
registration, use the completed core without tuning any threshold:

```text
python tools/run_v9.py tools/compare_warnings_v9.py --analysis audit/my-v9-core --out audit/my-warning-comparisons
python tools/run_v9.py tools/diagnose_control_v9.py --root runs/task-v9-test --out audit/my-control-diagnostics
```

The first reports paired sensitivity/specificity/error differences and sparse-
class bootstrap denominators. The second checks equal pre-decision traces and
reports precontact headings plus healthy safety reserve. It does not identify
causal mediation or make the controllers margin/effort matched. Current canonical
core diagnostics are `warning-comparisons-core/` and `control-diagnostic-core-v2/`.

The provided frozen registration rejects changed evaluation sources, model
inputs or simulation runtime. This protects a matched run rather than promising
cross-platform bit identity. Reanalysis on a different host checks the saved
generation metadata; fresh simulation on a different environment needs a new
registration and a clearly separate replication.

## Re-execute the frozen independent matrices

Use the original calibrated files and exactly matching registered sources,
inputs and runtime. Choose NEW run directories. Do not copy old healthy records
into these new matrices. Generate all three networks under both laws:

```text
python tools/run_v9.py tools/launch_task_v9.py --out runs/my-v9-test --seeds 1000,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012,1013,1014,1015,1016,1017,1018,1019,1020,1021,1022,1023 --calibration runs/task-v9-frozen/calibration.json --role test --registration runs/task-v9-frozen/registration-core.json
python tools/run_v9.py tools/launch_task_v9.py --out runs/my-v9-stress --seeds 1100,1101,1102,1103,1104,1105,1106,1107 --phis=-45,45 --calibration runs/task-v9-frozen/calibration.json --role test --registration runs/task-v9-frozen/registration-stress.json
```

These are seeded replications of the supplied design, not additional independent
samples to be pooled with the original seeds. `--resume` is permitted only with
the same complete command/configuration and matching sources/environment.
Existing episodes must bind to the identical batch manifest. If code, inputs or
calibration change, use a new run tree and label it as a new protocol/replication.
Never run sweep followed by a supposedly corrective rerun into an old output
tree: completed-trial skipping can otherwise leave the old values in place.

## Fresh calibration / independent replication

For a fresh end-to-end replication, collect development observations in a new
tree, regenerate the decoder and final B calibration, validate, then write NEW
registrations before generating test outcomes. Preserve the published design
constants; do not tune them on those new test outcomes.

```text
python tools/run_v9.py tools/run_task_v9.py --out runs/my-v9-development --seeds 200,201,202,203 --phis=-60,-30,0,30,60 --modes observe --horizon 400 --role development
python tools/run_v9.py tools/calibrate_task_v9.py --root runs/my-v9-development --out runs/my-v9-development/calibration-A.json
python tools/run_v9.py tools/calibrate_task_v9.py --root runs/my-v9-development --out runs/my-v9-development/calibration-B.json --configuration B --parent runs/my-v9-development/calibration-A.json
python tools/run_v9.py tools/launch_task_v9.py --out runs/my-v9-validation --seeds 400,401,402,403,404,405,406,407 --calibration runs/my-v9-development/calibration-B.json --role validation --faults healthy
python tools/run_v9.py tools/freeze_task_v9.py --validation runs/my-v9-validation --calibration runs/my-v9-development/calibration-B.json --out runs/my-v9-registration/core.json --stress-out runs/my-v9-registration/stress.json
```

The A file is an intermediate fitted calibration. The original failed A
configuration is a historical developmental attempt, with its own source
snapshots; it is not rerun under new semantics and counted as independent
evidence. B publishes the final gain/silence-gate choices. The freeze tool
requires the complete prespecified healthy grid and at least 6/8 success in
every stratum. A failure is reported, not hidden by replacing seeds.

Then run the two full factorial commands above with your new calibration,
registrations and run directories. The fixed numeric seed sets reproduce this
design; a new scientific confirmation with different seeds requires its own
prospective registration and must not be tuned after outcomes are seen.

## Tests and PDF preflight

```text
python tools/run_v9.py -m unittest discover -s tests -v
```

This includes geometry, causal-frame behavior, exact burst timing, actual tiny
Brian2 input replay, mask nesting, prefix-only metric handling, archive integrity,
mapping/protection tests and PDF-reference-page checks. Lightweight replay and
analysis run in empty output directories. No result JSON is hand edited.

After all three complete cohorts and their replay reports exist, regenerate
the SI from the canonical saved analyses, then build the main in a NEW directory.
The SI generator requires the complete 64-record separate action diagnostic;
it rejects an incomplete cohort. It stages figures and binds its source inputs.
Run from the repository root; choose unused output paths:

```text
python -X utf8 tools/run_v9.py tools/build_supplement_v9.py --core audit/acceptance-v9/core-v2 --stress audit/acceptance-v9/stress-v2 --causal audit/acceptance-v9/causal --figures audit/acceptance-v9/figures-v3 --out audit/my-si-build
powershell -NoProfile -File tools/build_paper.ps1 -BuildDirectory audit/my-main-build
```

Copy the generated `supplement.tex`, `supplement.pdf` and its `figs/*.pdf` into
`paper/` and `paper/figs/` only after the SI build succeeds. The main build
promotes its PDF only on clean references/overflow/glyph checks. To compile the
portable generated SI directly, use `pdflatex supplement.tex` twice from its
own folder, with its relative `figs/` directory alongside. TeX tools need
IEEEtran, cite, AMS, graphicx, booktabs, placeins, url, lmodern, longtable,
geometry, float, array and caption; no new neural run is needed.

```text
python -X utf8 tools/run_v9.py tools/qa_pdf.py --pdf paper/main.pdf --out audit/my-main-qa --submission
python -X utf8 tools/run_v9.py tools/qa_pdf.py --pdf paper/supplement.pdf --out audit/my-si-qa
python -X utf8 tools/run_v9.py tools/check_tests_v9.py --out audit/my-final-tests
python -X utf8 tools/run_v9.py tools/check_reproduction.py --require-model --out audit/my-cli-preflight.json
```

Review EVERY rendered page, then record actual PDF SHA256 values, complete page
lists, `passed` and concrete visual notes in a new JSON visual receipt. Do not
generate a passing visual receipt without inspection. The final local release
used `main-build-04`, `supplement-build-02`, `main-qa-04`, `supplement-qa-02`
and `tests-final-02` under `audit/acceptance-v9/`; their reports, rather than
this command list, establish actual completion. Later builds must have new names.
The fifth page must contain references only. Default IEEE body font size is
retained; excess content is edited or moved to supporting material. Check
undefined citations/references, overfull boxes, clipping, all embedded fonts and
absence of Type 3, encryption and interactive annotations.

The complete local release consistency check binds final sources, full tests,
all measurements, build/QA reports and the actual visual receipt:

```text
python -X utf8 tools/run_v9.py tools/validate_release_v9.py --main-build audit/acceptance-v9/main-build-04 --supplement-build audit/acceptance-v9/supplement-build-02 --main-qa audit/acceptance-v9/main-qa-04 --supplement-qa audit/acceptance-v9/supplement-qa-02 --tests audit/acceptance-v9/tests-final-02/check.json --preservation audit/acceptance-v9/preservation-final/check.json --visual audit/acceptance-v9/visual-final.json --out audit/acceptance-v9/final-validation
python -X utf8 tools/run_v9.py tools/package_task_v9.py --validation audit/acceptance-v9/final-validation/validation.json --out releases/assessment-v9-review.zip
python -X utf8 tools/verify_artifact_v9.py --zip releases/assessment-v9-review.zip --out audit/acceptance-v9/artifact-byte-check.json
```

These final local output names must not be reused over existing files.
`validate_release_v9.py` also checks preservation against the recorded initial
editing backup; that particular historical editing audit cannot be recreated
from an unrelated fresh checkout alone. The standalone ZIP byte verifier needs
only Python's standard library and the scientific ZIP, no original backup,
connectome or new simulation. It checks every member SHA/CRC, safe paths and
the two final PDF bindings. None of these checks certify acceptance, physical
reliability or submission-portal compatibility.

## Separate action-ablation check

The 64-record diagnostic cohort was registered after the core campaign began;
it is not an extension of its sample size or original confirmatory tests.
Seeds 1200--1207 cross bearings -30/+30 and normal proportional/relay,
turn-disabled (burst triggering retained), and all-action-disabled interfaces.
No controller or threshold is retuned. A fresh output directory is required:

```text
python tools/run_v9.py tools/launch_causal_v9.py --registration runs/task-v9-frozen/registration-causal.json --out runs/my-causal-replay
python tools/run_v9.py tools/analyze_causal_v9.py --root runs/my-causal-replay --registration runs/task-v9-frozen/registration-causal.json --out audit/my-causal-summary
python tools/run_v9.py tools/replay_causal_v9.py --root runs/my-causal-replay --calibration runs/task-v9-frozen/calibration.json --out audit/my-causal-audit
```

The original registration enforces its exact runtime/input/source hashes;
another runtime or changed code requires a newly labeled replication
registration, as for the core. Recorded cohort completion is reported in
`audit/acceptance-v9/causal-complete.json`, not implied by these commands.

## Historical evidence

Old geometry-v2/v8 and 600 ms open-loop data use different clocks, calibration,
drives and input randomness. Their commands and caveats remain in the versioned
protocols; never apply their 51.4 Hz open-loop criterion to the new geometry task.
The new trigger (4.03125 Hz) and 400 ms warning threshold (5.83333 Hz) also serve
different purposes and must not be interchanged.

Fresh read-only historical re-scoring is available with:

```text
python tools/run_v9.py tools/audit_archive.py --out audit/my-historical-audit
```

The original PDF/72-record baseline capture is preserved at
`audit/acceptance-v9/baseline/check.json`; it is not rerun against the revised
paper or written over existing evidence. `audit_archive.py`
generates hub_sign.json directly from raw records. 276/288 and 262/288 are
alternative scores of the same archive, not executed SpikeFI/SpikingJET
benchmarks. Original F4 hub manifests and some old integration metadata remain
unavailable; reconstructed node lists do not validate those original runs.
Current local inputs suffice for v9, but the historical experimental environment
is not claimed complete.
