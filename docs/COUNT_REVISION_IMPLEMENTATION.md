# V10.1 exact-count and stage implementation

This implementation snapshot fixes the executable count-domain warning semantics and saved-record stage analysis. It builds on published V10.1 `75313d7740491e7f7830e2fc554c21e1aaefe655`; original experimental records, registrations, calibrations and historical analyses are unchanged. The enclosing Git commit identifies these code and analysis files. A subsequent manuscript revision may cite this implementation commit without embedding its own future hash.

## Executed evidence

- `output/warning-counts-v10_1-02/`: 576 test records and 96 original healthy-validation records, exact thresholds and all five criteria with 20,000 whole-seed bootstrap draws; all 19 floating-boundary cases retain their identities and source hashes.
- `output/warning-figure-v10_1-02/`: source CSV and regenerated Fig.4 exports from that result.
- `output/postburst-stage-recheck-03/`: all-record risk-set accounting, 3,114 effective decisions, per-stratum results and explicit synthetic steering-helper fixtures; no additional neural experiments.
- `output/count-calibration-check-v10_1-02/`: independent development/validation-only RF-A/B calibration and threshold compatibility checks, with zero test episodes read.
- `output/timing-recheck-count-v10_1-01/`: a fresh execution of the V10.1 trigger-timing entry against unchanged observations.

Saved products retain their execution-time base HEAD and exact analysis/source hashes. The content-bound implementation snapshot, rather than a retrospective edit of generation metadata, identifies the executable new sources.

The 18 added warning tests and 20 evidence tests pass. Exact threshold semantics preserve all original warning labels and intervals; the change removes equivalent-formula ambiguity, not task errors. Post-burst zero control features are an observed regime in these records, not a structural guarantee for all configurations. No new neural simulations, threshold tuning on test outcomes or causal interventions were performed.

## Version roles

| Fixed version | Role |
|---|---|
| `986ff54193fee6a1b95815499a4a3477b15ea49a` | Original curated V10 source, observations and frozen generation metadata |
| `126e265ef1a0bb49d2a3103ff47b0c9077acdcc0` | Earlier schema/horizon assessment; no V10.1 trigger-timing entry |
| `75313d7740491e7f7830e2fc554c21e1aaefe655` | Published V10.1 timing analysis, verification entry and paper |
| Enclosing implementation commit | Exact-count warning library, tests, re-scores and stage recheck listed above |
| Later manuscript commit | Revised paper/PDF citing the fixed implementation commit; identified externally by its Git permalink and publication manifest |

Use root `REPRODUCE.md` for portable commands and `docs/WARNING_COUNT_PROTOCOL_V10_1.md` for the count-domain definition. Historical full-matrix workflows retain frozen-source guards and must use their corresponding source snapshots.
