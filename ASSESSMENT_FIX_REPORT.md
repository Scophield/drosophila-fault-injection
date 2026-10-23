# Revised-review repair: assessment-v3

This work follows `paper/REVIEW_2026-10-21_REVISED.md` and preserves both earlier
reviews, the earlier repair report, and all historical raw trials.

## Applied changes

- Defined the empirical question as cohort/exposure sensitivity, with a clear
  distinction between numerical disagreement and predictive validity.
- Added per-condition scores and exclusions. After F4/HUB/EIm removal, counts
  are 192 transmission and 190 joint passes among 204 records. Main F1/F2/F3/F5
  counts agree at 168/180; healthy resubstitution is labelled as such.
- Added independent healthy/fault resampling for relative effects, exact
  three-seed resampling support, 200/300/400/500-ms comparisons and seed medians.
- Disclosed the sensory refractory difference from upstream. Actual whole-brain
  diagnostic execution confirms the two settings give different responses.
- Installed an isolated actual simulator environment. Brian2 2.9.0 failed with
  the available NumPy; Brian2 2.10.1 executes successfully. Historical pins are
  retained separately and new requirements specify the exercised runtime.
- Executed nine real passive calibration episodes and froze their threshold.
  Completed 48 whole-brain tests on disjoint seeds, without test-based refitting.
- Added a deterministic privileged geometry reference using the same action
  constraints. It establishes 1-s task feasibility and fails at 1.2 s; it is
  explicitly not a neural fault-tolerance comparison.
- Reworked the manuscript into a standalone account, added cohort counts and
  model differences, normalized citations, and expanded the closest-work comparison.
- Improved figure labels and scale descriptions. Corrected the pathway figure's
  command labels to follow actual cell types instead of a hardcoded ordering.
- Fixed PowerShell TeX handling so nonfatal MiKTeX maintenance stderr does not
  abort a successful compile; exit codes and final reference/overflow checks remain.
- Prepared an explicit local release builder that verifies packaged bytes and
  excludes private memory, Git metadata, dependency caches and unrelated files.

## Evidence locations

| Evidence | Location |
|---|---|
| Cohorts, exclusions, effects, windows, source hashes | audit/assessment-v3/assessment.json |
| Complete original archive reanalysis | audit/assessment-v3-base/revision_analysis.json |
| Actual full-network refractory pilot | runs/simulator-v3/validation.json |
| Passive calibration and frozen threshold | runs/geometry-v3/vision/ |
| Verified 48-test matrix, seed/direction counts and activity pairs | audit/prospective-v3.json |
| Deterministic task-feasibility reference | runs/task-reference-v3/reference.json |
| Current protocol and methodological boundaries | paper/PROTOCOL_v3.md |

## Scope and status

With a one-second horizon, healthy survival is 5/12 (5/6 at -30 degrees and 0/6
at +30 degrees). At 25% and 50% deletion it is 4/12 and 0/12; readout-disabled
controls are 0/12. All 48 tests, nine calibration episodes and the full-connectome
refractory diagnostic executed successfully. Successful execution does not mean
the controller succeeds: its directional limitation and pre-cue steering bias
are reported explicitly. No threshold was changed to improve test performance.

The fresh faults never exceed twice matched healthy activity in the common
200/300/400/500-ms windows, despite 8/12 and 12/12 collisions. This limits the
activity criterion's interpretation; it does not validate it as a safety predictor.

The local deliverables are `paper/main.pdf`, `paper/PROTOCOL_v3.md` and
`releases/assessment-v3-review.zip`. The bundle includes the precise raw/derived records,
scripts, source and validation evidence with per-file SHA256 hashes. The final
validation is saved in `audit/assessment-final-validation-v4/`; 32 regression checks
cover protocol behavior, cohort/exposure arithmetic and provenance rejection.

The work repairs analysis, implementation documentation and the empirical
validation gap with a focused new experiment. It does not certify acceptance,
a biological escape controller, a calibrated safety budget, or hardware reliability.
Historical hub identities cannot be recovered by editing code. They remain
isolated and excluded from claims requiring a controlled sign-specific contrast.

The prospective summarizer requires every declared test scenario, rejects
calibration overlap, and checks source/manifest consistency before reporting a
completed matrix. Partial results are not a final cohort. New outcomes are
never merged into the archive.

The matching local release is a reviewable artifact. No commit, push or conference
submission is authorized by a manuscript-edit request or performed automatically.
The public-branch mismatch therefore remains until the author explicitly requests
publishing the prepared revision.
