# Assessment-v4 repair report

This repair addresses the latest `REVIEW_2026-10-21_ASSESSMENT_V3.md`.
The current manuscript is `paper/main.pdf`; the complete current definitions are
in `paper/PROTOCOL_v4.md`. Earlier reports and releases are preserved as history.

## Interpretation and presentation fixes

- **B1:** Whole-episode, common-duration and fixed-horizon spike ratios are
  defined separately. Deletion's unequal stopping times change the median ratio
  from 0.381701 to 0.729443. Every full-hub pair already lasts one second;
  six ratios first exceed twofold at 840--900 ms. The new main figure shows all
  twelve traces, direction/calibration status and first crossings through 1000 ms.
  Earlier-window selection is no longer described as correcting unequal exposure.
- **B2:** The runner adds pre-cue gating and zero steering readout with offset
  retained; the existing steering-disabled mode supplies a third intervention.
  All retain the original neural burst-trigger rule. The new six-cluster paired
  campaign uses seeds 12--17, both bearings, unchanged calibration and neural
  parameters. All 48 actual episodes completed successfully and pass strict
  provenance, snapshot and independently reconstructed trigger checks.
  Original, gated, offset-only and steering-disabled survival is 4/12, 6/12,
  0/12 and 0/12, respectively. Every positive-bearing scenario fails. Gate-minus-
  original mean difference is +16.7 percentage points, with an exploratory
  conditional six-cluster interval of 0.0--33.3 points. Offset-only and
  steering-disabled conditions trigger bursts in 11/12 and 12/12 cases,
  so removing the trigger does not explain their universal collisions.
- **B3:** Main text now leads with the real prospective outcomes, includes
  steering/smoothing/trigger equations and reports directional floor effects.
  The original readout-disabled comparison is explicitly insufficient to isolate
  steering. Detailed open-loop dose plots remain in the supplement.
- Table captions identify six paired seed clusters. Cohort scoring adds explicit
  disagreement counts. The pathway diagram identifies left/right cells and
  labels F3/F4 as output silencing. Jo and Jang are discussed using verified
  primary records and existing bibliography entries.

## Additional evidence and reproducibility

Twelve actual 600-ms full-connectome runs test healthy versus 50% deletion under
sensory refractory intervals 2.2 and 0 ms, with three paired seeds. Median paired
retention changes from 0.763158 to 0.791919; healthy median rate changes from
94.7917 to 103.125 Hz. These observations quantify implementation sensitivity
without asserting equivalence. All counts and runtime records are retained.

New batches save 40 exact generating Python source files each, including the
external model source. Individual hashes and the aggregate code hash are checked
against those snapshots. Original calibration and measurement records remain
unchanged. Historical missing generation snapshots are not fabricated or replaced
by a final-release source hash. External table dependencies and their expected
hashes remain explicit; the upstream MIT notice accompanies copied model source.

The controller matrix and compute table are in `audit/controls-v4/results.md`;
machine-readable checks are in `audit/controls-v4/controls.json` and
`audit/refractory-v4/summary.json`. `paper/sections/controller_results.tex` is
generated from the independently reproduced completed summary.

## Verification and delivery

Final validation is recorded in `audit/validation-controls-v4-final/validation.json`.
It checks the regression suite, archived raw hashes, exact staged manuscript
sources, figure inputs/outputs, new experiments, resolved references, fonts and
four technical pages plus a references-only fifth page. Rendered pages and a
separate visual-inspection record accompany it. The local ZIP manifest binds
every included file by SHA256 and size and is checked after writing.

The repair does not establish population reliability, activity-budget prediction,
corrected hub causality, a biological escape model or hardware fault tolerance.
All new controller interventions use healthy networks; they do not measure
deletion tolerance under those changed control laws. No commit, push, submission
or public publication has been performed.
