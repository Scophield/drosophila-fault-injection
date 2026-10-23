# Revision v8 completed

## Final checkpoint (2026-10-22, Japan time)

All 72 matrix records are complete (24 preserved healthy, 48 new faults), with
all three resumed workers returning zero. Do not rerun the campaign. Analysis,
source/calibration verification, paired loss/gain, fixed/common-duration activity,
64 threshold combinations and independent exact-bootstrap audit have passed.

Original healthy/25/50 survival is 4/4/0 of 12; gated is 6/3/0. Net-loss
interaction is +25.0 pp [8.3,41.7] at 25% and +16.7 pp [0,33.3] at 50%.
Only three/two clusters have nonzero contrasts. Post-hoc symmetric-null sign-flip
sensitivities are p=.25/.50; the manuscript does not claim population robustness.
All 41 fault collisions are unflagged across tested early-window thresholds;
two surviving records are flagged at 500 ms and c=1.5.

Delivered PDFs: paper/fly_connectome_fault_assessment_v8.pdf (5 pages) and
paper/fly_connectome_supplement_v8.pdf (14 pages, 22 tables, 9 figures).
Every page was rendered and visually inspected. Final source/PDF/figure checks,
39 passing regressions and 449 unchanged archived inputs are recorded at
audit/revision-v8-release-check/validation.json. The response map is
REVISION_V8_REPORT_zh.md; commands and dependency boundaries are in REPRODUCE.md.
The source-bound current overview is audit/overview-v8; the current paired
activity figure is audit/cross-figures-v8-final.

Local release: releases/assessment-v8-review.zip, 1303 files, 23314153 bytes,
SHA256 0d01d87079a45bb55d5e773ec8c6094bd2ef425510c0cd955377a1e3e85ad522.
Every ZIP entry was verified against its size/hash manifest. No commit, push,
submission or publication occurred. External connectome tables remain pinned
dependencies rather than bundled data. No requested acceptance work remains.

## Superseded execution checkpoint history

Goal: complete the frozen controller-by-fault matrix and evidence-aligned five-page
English manuscript, supplement, Chinese response map and reproduction entry.

Completed before this resume: source/package compatibility checks, 24 preserved
healthy records, six new fault episodes, protocol and analysis/validator scripts;
initial manuscript repairs of evidence tiers, F2 units, thresholds and sign examples.

Current resume: the prior worker PIDs no longer existed. The exact runner was
resumed with --resume; completed records were verified and skipped. Its live
execution is attached to exec session 35053. Do not relaunch while it runs.
New fault outputs are in runs/controller-fault-v8/vision/episodes_controls.
Completion requires execution.json with exit_codes [0,0,0] and all 72 records.

New work: paired plot generated and visually inspected at
audit/prospective-figures-v8; its PDF copied to paper/figs. Initial five-page layout
compiled at audit/manuscript-v8-layoutpilot and rendered. This is a layout pilot,
not the final results manuscript. The old controller table and abstract still
await actual new results; do not deliver this intermediate PDF.

Added separate modules for the cross figure, independent raw-outcome/exact-bootstrap
audit, main result writer and supplement extension. The existing supplement
generator now requires the completed v8 cross summary. Six new tables will retain
earlier S1--S16 numbering, with a new Figure S9.

Regression suite: 39 checks were attempted. The first sandbox execution failed on
temporary-directory ACLs; a managed-runtime replay with project-local temporary
directories passed 38 checks, with one git-on-PATH environment failure. The local
tmp/run_revision.py bootstrap now supplies Git/TeX paths and project-local temp.
The managed-runtime replay with corrected paths then passed all 39 tests. Final
validation will retain its own complete log after artifacts are stable.

Remaining commands (normal environment uses python without the local bootstrap):
1. Analyze completed matrix to audit/controller-fault-v8.
2. Independently audit to audit/cross-audit-v8 and plot to audit/cross-figures-v8.
3. Generate main controller_results.tex from verified cross.json; revise abstract,
   conclusion and response map using actual results, without assuming interaction.
4. Build supplement and main in new directories, inspect every final PDF page.
5. Update material index/reproduction docs, validate, package explicit local release,
   retrieve goal evidence and complete every saved criterion. No commit/push/publish.
