# Assessment-v4: horizons and controller interventions

This supplement supersedes assessment-v3 interpretations of shortened windows.
Historical raw records and geometry-v3 calibration/test records remain unchanged.
The earlier [PROTOCOL_v3.md](PROTOCOL_v3.md) retains complete archive tables,
perturbation definitions, dose results and explicitly labeled earlier limitations.

## Definitions and terminology

| Symbol / term | Definition |
|---|---|
| Transmission | Eight-command-cell mean rate at least 51.4 Hz in the 600-ms archive |
| Joint rule | Transmission plus rate and total spikes no more than twice healthy medians |
| S_F(t), S_H(t) | Cumulative fault / paired healthy network spikes through completed frame t |
| T_F, T_H | Actual recorded fault / healthy durations |
| Whole-episode ratio | S_F(T_F) / S_H(T_H) |
| Common-duration ratio | S_F(T*) / S_H(T*), T* = min(T_F,T_H) |
| Fixed-horizon ratio | S_F(t) / S_H(t), requiring both records to reach t |
| Collision-free survival | No within-frame separation at or below 0.05 m through requested horizon |
| Seed cluster | Both bearings sharing one Brian2 seed and, where applicable, a fault seed |
| Pre-cue gating | Steering zero before the 100-ms stimulus onset; unchanged law thereafter |
| Bias-only steering | Set steering readout to zero while retaining bias and neural burst trigger |
| Steering disabled | Steering zero, with the neural burst trigger retained |
| Readout disabled | Both steering and the neural burst trigger disabled |

The joint rule is nested in transmission by definition. Its disagreement count
is neither diagnostic accuracy nor a population fault incidence estimate.
The historical transmission threshold rounds (94.583333 + 8.229167)/2 =
51.40625 Hz from separate ten-trial calibration medians. Healthy medians used
for the joint rule are 94.6875 Hz and 39,694 spikes, not those calibration values.

## B1: stopping-time matching differs from horizon selection

`tools/analyze_horizons_v4.py` reconstructs these quantities directly from saved
episodes, retaining every pair. Output: `audit/horizons-v4/horizons.json` and
`pairs.csv`; every raw input and the generating analysis script are hashed.

For 50% deletion, median whole-episode ratio is 0.381701, versus 0.729443
at each pair's common duration. First-400-ms ratio is 0.722628. Unequal
termination therefore changes the estimand and numerical result.

Every full-hub pair already lasts 1000 ms on both sides. Whole and common-duration
ratios are identical within each pair. Limiting observation to 400 ms excludes
late twofold exceedances; it does not correct unequal exposure.

| Full-hub horizon (ms) | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 1000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Median paired ratio | 1.302 | 1.332 | 1.362 | 1.402 | 1.415 | 1.435 | 1.472 | 1.682 | 1.703 |
| Pairs above twofold | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 6 |

| Bearing / seed | First twofold crossing (ms) | Calibration scenario |
|---|---:|---|
| -30 / 0 | 840 | yes |
| -30 / 1 | 840 | yes |
| -30 / 2 | 860 | yes |
| -60 / 0 | 900 | yes |
| -60 / 1 | 880 | yes |
| -60 / 2 | 880 | yes |
| +30 and +60 / all three seeds | none through 1000 | no, but shared seed clusters |

The main figure shows all twelve cumulative traces, with direction coded by
shape/color. The supplementary `estimands` figure shows individual whole,
common-duration and 400-ms values, not just pooled medians. The one-second
activity warning remains a true observation under its stated criterion.

## B2: frozen-calibration paired interventions

Original geometry-v3 tests used seeds 6--11 at -30/+30 degrees, following nine
passive calibration episodes on seeds 0--2. Calibration remains byte-identical:
threshold 18.125 Hz, frontal bias -20 Hz, left/right scale 70 Hz, positive sign;
SHA256 `5427eaa0159bbf7ebb7f4208fad13a1f8e18c43c7c695b39a078bcde41f639b3`.

The original law is omega = -400 * clip((d_bar - b)/ell, -1, 1) deg/s.
Here d is the sum of four left command rates minus four right command rates.
The command mean a is the sum of all eight rates divided by eight. Bars average
the latest five frames, using all available frames initially. The first frame
with a_bar >= 18.125 Hz AND the preceding **unsmoothed** frame a >= 18.125 Hz
schedules a burst 250 ms after that frame ends. This is not a requirement for
two consecutive smoothed threshold crossings. There is only one scheduled burst.

Burst speed is 0.35 m/s for 450 ms, with fixed heading; baseline speed is 0.05 m/s.
Steering saturates at 400 deg/s and heading at +/-100 degrees. At zero readout,
the offset yields -114.285714 deg/s. All original healthy records reach
-11.428571 degrees at cue onset with zero preceding network spikes.

The new campaign uses seeds 12--17, excluding every calibration and prior test
seed, at both -30/+30 bearings. Four healthy conditions form 48 actual neural
episodes: original law, pre-cue gating, bias-only steering and steering disabled.
All three interventions retain the same neural trigger law. Feedback changes
subsequent sensory input, so trigger times need not be identical between laws.
No threshold, receptive-field map, neural parameter or fault dose is retuned.

The runner verifies source/configuration hashes and refuses episode overwrites.
`tools/analyze_controls_v4.py` rejects missing/extra scenarios, mixed runtime or
calibration, failed workers and corrupt source snapshots. It independently
reconstructs each trigger from raw command rates and verifies pre-cue motion.
Its final outputs contain every paired survival difference, six seed-level
contrasts, directional counts, trigger times and active-burst metadata.

Outcomes and contrasts are in `audit/controls-v4/controls.json`; the generated
`results.md` provides compact tables. Differences are averaged within seed over
both bearings. Conditional bootstrap intervals resample the six complete seed
clusters 20,000 times (seed 0). They are exploratory summaries, not calibrated
population coverage or evidence of equivalence. Horizon sensitivity at 800 and
1000 ms comes from the same records; no unexecuted 1200-ms outcome is imputed.

| Healthy control law | -30 degrees | +30 degrees | Total | Active burst at 1000 ms | Neural trigger occurred |
|---|---:|---:|---:|---:|---:|
| Original | 4/6 | 0/6 | 4/12 | 4 | 4/12 |
| Pre-cue gated | 6/6 | 0/6 | 6/12 | 3 | 6/12 |
| Offset only | 0/6 | 0/6 | 0/12 | 0 | 11/12 |
| No steering | 0/6 | 0/6 | 0/12 | 0 | 12/12 |

Gating-minus-original seed differences are [0,0,0.5,0,0.5,0], with mean 0.166667
and a conditional cluster interval [0,0.333333]. Offset-only and no-steering
differences are both [-0.5,-0.5,0,-0.5,0,-0.5], mean -0.333333, interval
[-0.5,-0.166667]. All positive-bearing cases remain at floor. Every group's
survival count is unchanged between the retrospectively scored 800-ms horizon
and the full 1000 ms. This does not establish survival after that horizon.

## Sensory refractory sensitivity

`tools/check_refractory_v4.py` performs 12 additional actual full-connectome runs:
three seeds (12--14), healthy versus 50% connection deletion, and sensory refractory
settings 2.2 versus 0 ms. Each run lasts 600 ms under 150-Hz input. Other neurons
retain the 2.2-ms interval. Deletion masks use seed 10000+s and Poisson streams
use 20000+s. Network state is restored and the same input seed reset for each pair.

`runs/refractory-v4/paired/results.json` saves counts, rates, latency, full-network
size and measured runtimes. Three paired retentions per variant describe model
sensitivity; they do not establish equivalence or replace the historical archive.

| Sensory refractory (ms) | Healthy median (Hz) | Deletion median (Hz) | Paired retentions (seeds 12,13,14) | Median paired retention |
|---|---:|---:|---|---:|
| 2.2 | 94.7917 | 72.5000 | 0.8285, 0.7451, 0.7632 | 0.7632 |
| 0 | 103.1250 | 81.6667 | 0.8525, 0.7619, 0.7919 | 0.7919 |

Paired retention is the ratio within a seed. It is distinct from a ratio of
group medians. `audit/refractory-v4/summary.json` is independently reconstructed
from the 12 saved count/rate records and source-snapshot hashes.

## Provenance, compute and release boundaries

New batch manifests contain exact generating `sim` and `sim_vision` Python source
snapshots plus the external model source, each individually hashed. Aggregate
source hashes are independently reconstructed from snapshots. The two external
connectome tables remain separate, pinned dependencies. Do not represent final
release code as an exact snapshot of every older geometry-v3 generation version:
those old aggregate hashes are retained, but their complete version-specific
snapshots were not recorded. The pre-repair working-source snapshot is preserved
for audit and is not relabeled as an older generating version.

Compute uses an Intel Xeon W-2223 CPU at 3.60 GHz, Windows, NumPy backend,
Brian2 2.10.1, NumPy 2.5.4 and a 0.1-ms neural step. Three control workers run in
parallel; their summed episode wall times differ from campaign elapsed time.
Each process uses about 1.1 GB working memory in observed execution, not a
profiled peak-memory guarantee. `results.md` records the measured campaign
times. Complete historical campaign runtime is unavailable and is not estimated.

The local assessment-v4 release contains the exact PDF, current source,
supplements, explicit raw inputs, new source snapshots, analyses and validation.
Every ZIP entry is checked against a SHA256/size manifest. This is a local
review artifact; no commit, push, paper submission or public publication is
implied. Corrected hub simulations, mapped hardware experiments, broader
calibration and population-level reliability remain outside this repair.
