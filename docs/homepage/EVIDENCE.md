# Homepage evidence index

Current scientific snapshot: [22999d28d8fe22f863fc8f62eaa45a57256083d0](https://github.com/Scophield/drosophila-fault-injection/tree/22999d28d8fe22f863fc8f62eaa45a57256083d0). The media retain their original 75313d7 generation metadata; their source records and displayed quantities are unchanged in the current snapshot. [Current verification](current-verification.json) binds both identities without relabelling the media as new experiments.

## Full-cohort results

- 576 test episodes: RF-0 has 24 independent seed clusters and 288 episodes; RF-A/B each have 12 clusters and 144 episodes. Each seed contributes two bearings, two laws and three network conditions.
- Mean healthy-to-50% trigger delays are 80.0/57.5/57.5 ms, with SD 42.88/46.56/29.67 ms over 48/24/24 bearing pairs. P/R timing duplicates are counted once. These are retrospective descriptive measurements, not neural-conduction latency estimates or causal effects.
- All 288 P/R pairs share trigger/burst schedules; 15 differ in contact outcome. This compares complete feedback configurations and does not isolate healthy reserve.
- At 50% deletion, 900/1000-ms P counts are 46/48→37/48, 23/24→22/24 and 24/24→23/24 in RF-0/A/B. R counts are 48/48→48/48, 23/24→23/24 and 24/24→24/24. Both endpoints reuse the same trajectories and seed clusters.
- The prespecified secondary 1-s R-minus-P net-loss contrasts are −22.9 pp [−33.3, −12.5] in RF-0 and −4.2 pp [−12.5, 0] in each new RF. Intervals are pointwise 95% whole-seed bootstrap intervals, conditional on saved mappings/calibrations. RF redraws, recalibration and cohorts change together; nonsignificance is not equivalence.

All scientific paths below are inside the fixed snapshot:

| Result | File |
|---|---|
| Timing, original source paths and hashes | `output/trigger-timing-20261025-03/all-records.csv` |
| Healthy/fault pairs | `output/trigger-timing-20261025-03/all-healthy-fault-pairs.csv` |
| P/R pairs | `output/trigger-timing-20261025-03/all-P-R-pairs.csv` |
| First contacts | `output/trigger-timing-20261025-03/all-contact-pairs.csv` |
| RF-0 registered analysis | `audit/acceptance-v9/core-v2/summary.json` |
| RF-A/B registered analysis | `audit/v10/transfer-01/map-{A,B}/analysis/summary.json` |

[Full data index](https://github.com/Scophield/drosophila-fault-injection/blob/22999d28d8fe22f863fc8f62eaa45a57256083d0/docs/V10_DATA_INDEX.md) supplies the development, validation, test and diagnostic cohort boundaries. Estimates use whole seed clusters within each RF, keeping both bearings and all paired conditions together.

## Selected examples

| Demo | Fixed identity | Trigger → actual onset → burst end (ms) | First contact |
|---|---|---|---|
| A | RF-0 / seed 1012 / −30° / P / healthy | 140 → 390 → 840 | None through 1000 ms |
| A | Same context / 25% deletion | 160 → 410 → 860 | None through 1000 ms |
| A | Same context / 50% deletion | 220 → 470 → 920 | 961.483236 ms |
| B, C | RF-0 / seed 1010 / −30° / P / 50% | 200 → 450 → 900 | 964.119568 ms |
| B | Same context / R / 50% | 200 → 450 → 900 | None through 1000 ms |

[Original example manifest](../homepage-animation/examples.json) records full raw paths, SHA256, masks, maps, calibration identities, input variates and all selection candidates. A minimizes distance to the all-context mean two-dose delay vector without outcome filtering. B selects the median P-contact time among 11 RF-0/50% discordant pairs; C reuses B/P. All examples are selected retrospectively for explanation, not incidence or mechanism tests.

## Warnings and executable checks

The current integer-count command rule sums eight neurons over the fifteen 20-ms bins in 100–400 ms. Its strict `<` cutoff is derived from healthy validation only; equality does not alert. Canonical TP/FP/TN/FN are 2/51/224/11, 2/42/99/1 and 0/24/119/1 in RF-0/A/B. See [count-domain protocol](https://github.com/Scophield/drosophila-fault-injection/blob/22999d28d8fe22f863fc8f62eaa45a57256083d0/docs/WARNING_COUNT_PROTOCOL_V10_1.md) and `output/warning-counts-v10_1-02/`. Sparse failures limit cross-RF warning estimates; the claim concerns these frozen criteria, not every possible neural predictor.

The common checker validates record identities, pairing, clocks, exposure and labels. Native replay checks inputs and plant transitions independently. Eleven common and three native-only predefined challenge types are detected per adapter, with a delayed-tank second adapter; these selected challenges are not a general detection coverage estimate. Trace consistency cannot authenticate neural execution. Sources: `audit/v10/evidence-05/check.json` and `audit/v10/legacy-timing-01/check.json`.

## Geometry and interpretation

Positions interpolate only within original verified straight-motion segments. Heading is held at the original segment-start value until its recorded boundary. Readout curves use recorded post-step values, without fabricated spikes or an approximate replacement plant. At first contact the displayed pose freezes and the label latches; the declared clock can continue to 1000 ms. The 50-mm ring denotes center separation, not icon size.

A single burst followed by slower motion makes success finite-horizon preservation. The model does not establish biological fault tolerance, sustained avoidance, an RF-isolated effect or an intrinsic P/R robustness advantage after healthy-reserve matching.
