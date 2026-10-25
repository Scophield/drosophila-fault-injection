# Retrospective post-burst stage recheck

Run `python tools/analyze_postburst_stage_v10_1.py --out output/<fresh-directory>`
from the scientific repository root using its saved-record Python environment.
No neural simulation, calibration, threshold fit, warning-performance comparison
or confirmatory test is performed. The script refuses to reuse an output directory.

The output independently rechecks all 576 frozen source hashes, recorded
five-frame command features, trigger/steering decisions and original piecewise
plant geometry. `results.json` records raw/calibration/registration/source hashes,
the execution environment and Git identity. This is record/plant replay, not
authentication or independent reproduction of neural execution.

## Risk set and decision windows

Let B be the scheduled burst end and H=1000 ms. Eligibility requires B<H and no
first contact at or before B. There are 543 eligible records; exclusions are four
prior-contact records, seventeen with burst still ongoing at H, and twelve with
B=H and no follow-up. All 576 records triggered. The prior-contact category takes
priority over an unfinished-burst category; it includes three records with B>H.

Effective post-burst decisions satisfy B <= t_end < min(first-contact,H). The
decision at B controls the first walking interval, while a decision at contact
or H has no remaining observed pre-contact follow-up. All 3,114 such decisions
have zero raw eight-cell rates, zero five-frame features and zero gated turn.

Whole-network spikes are assessed only in complete frames ending after B and at
or before min(first-contact,H), subtracting the cumulative total at B. This avoids
using a frame that straddles first contact. Under this conservative window, 474
eligible records still contain whole-network spikes. Eight zero command features
therefore do not imply a silent whole network.

| RF | Eligible records | Decisions | Records with whole-network spikes | Post-burst contacts |
|---|---:|---:|---:|---:|
| RF-0 | 263 | 1492 | 227 | 11 |
| RF-A | 140 | 808 | 123 | 1 |
| RF-B | 140 | 814 | 124 | 1 |

`groups.csv` retains every RF × law × dose group, including explicit zeros and
all exclusions. `postburst-decisions.csv` exports all 3,114 eight-feature vectors.
`all-records.csv` retains all 576 records, including the noneligible cases.

## Timing and code boundaries

All 288 P/R pairs have matching mask, input variates, map, calibration and burst
schedules; 15 have different contact outcomes. Their sensory/neural/realized
motion prefix through the trigger matches. Before the trigger the requested turn
is zero; at the trigger boundary the newly requested next-frame turn can already
differ across laws.

The independently reconstructed paired healthy–50% trigger shifts are
80.0/57.5/57.5 ms, SD 42.8754/46.5553/29.6721 ms over 48/24/24 bearing contexts
and 24/12/12 seed clusters, counting P/R timing duplicates once. The lower-dose
and earlier-trigger counterexamples remain in `delay-summary.csv` and
`healthy-fault-delays.csv`.

`steering-helper-fixtures.csv` shows that the steering code can request nonzero
turns at 900 ms when features are active, and can request nonzero turns from a
zero vector when silent gating is disabled. These are synthetic function
fixtures, not neural experiments. There is no general post-burst suppression
rule; zero features across all sampled RF/law/dose groups are an observed regime.

The thirteen post-burst contacts occurred during that zero-turn walking regime;
the other four contacts occurred before burst completion and are not assigned to
it. This describes stage-specific finite-horizon outcomes without identifying a
causal role for trigger delay, isolating healthy control reserve or establishing
sustained avoidance. Deterministic reconstruction is not scored as a new
predictor, and is not compared with the earlier 400-ms warning task.
