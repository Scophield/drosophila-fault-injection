# Protocol supplement, version 2 (21 October 2026)

This supplement accompanies the archive reassessment in `main.pdf`. Observations
and executable code are distinguished throughout. No new whole-brain simulation
was performed for this revision. Historical raw records remain unchanged.

## Sources and reproduction

Historical submission commit: `051dcb6a3123841041a34d3b43395e2841975879`.
Main trials: `sim/results/real/*.jsonl`. Controls and episodes:
`sim_vision/results_vision/`. Raw-source SHA256 hashes and Python/NumPy versions
are in `audit/revision-v2/revision_analysis.json`; all doses are also saved in
`audit/revision-v2/fault_families.csv`. The plot manifest records figure sources.

Run from the repository root, with new output directories:

```text
python tools/audit_revision.py --out audit/reproduce-revision
python tools/plot_revision.py --analysis audit/reproduce-revision/revision_analysis.json --out audit/reproduce-figures
python -m unittest discover -s tests -v
```

The audit requires NumPy, plotting additionally requires matplotlib, and protocol
regression tests additionally use pandas. This lightweight environment does not
validate a Brian2 installation. See `../REPRODUCE.md` for simulation environment,
input-table hashes, isolated PDF builds and the prospective calibration/test sequence.

## Definitions and statistical units

Each main trial drives 314 sensory cells at 150 Hz for 600 ms. For eight command
neurons, `r = command_spikes / (8 * 0.6 s)`. Latency is their first spike, not a
completed decision. `S` counts every model spike, including sensory cells.

Transmission passes if `r >= 51.4 Hz`. The joint rule additionally requires
`r <= c * 94.6875 Hz` and `S <= c * 39694`, normally with `c = 2`.
The healthy medians are fixed main-sweep references, not energy measurements or
certified safety limits. For `c = 1.5, 2, 3, 4`, 262/288 fault/control records
pass jointly, versus 276/288 for transmission alone. Additional failures are all
12 HUB_inh trials and INHrand_mass trials 3 and 9 (zero-based).

Rate intervals use 20,000 bootstrap resamples within each condition, NumPy seed 0,
and the 2.5th/97.5th percentiles of the resampled median. Figure 2 bars instead
show observed 10th/90th trial percentiles. F1-F3 fault masks use SHA-256 of phase,
condition and trial. Historical open-loop Poisson streams were not reset per
trial, so variation combines fault and stimulus effects. Intervals condition on
one connectome, selector, calibration and operating point.

## Complete archived F1-F5 summary

Every row contains 12 trials. Values are medians; brackets are rate bootstrap
intervals. F1 denotes lognormal sigma, not percent coefficient of variation.
F3/F4 silence outputs while units can still spike. F5 identifies the sensory
output removed. F4 describes historical selections, not corrected-selector results.

| Condition | Rate [95% CI] (Hz) | First spike (ms) | Network spikes | Transmission |
|---|---:|---:|---:|---:|
| Healthy | 94.69 [94.06, 95.42] | 4.05 | 39,694 | 12/12 |
| F1 sigma 0.05 | 94.38 [93.75, 95.94] | 4.20 | 39,678.5 | 12/12 |
| F1 sigma 0.10 | 95.31 [94.17, 95.52] | 4.20 | 39,723 | 12/12 |
| F1 sigma 0.20 | 94.17 [92.71, 96.67] | 4.20 | 39,988 | 12/12 |
| F1 sigma 0.50 | 94.17 [92.19, 96.46] | 4.35 | 41,638 | 12/12 |
| F2 deletion 5% | 91.88 [91.15, 93.75] | 4.40 | 39,077 | 12/12 |
| F2 deletion 10% | 93.13 [90.63, 96.04] | 4.30 | 38,448 | 12/12 |
| F2 deletion 25% | 84.48 [82.29, 87.81] | 4.65 | 36,598 | 12/12 |
| F2 deletion 50% | 72.40 [71.25, 74.69] | 5.40 | 31,589.5 | 12/12 |
| F3 output silencing 1% | 94.58 [93.85, 95.00] | 4.30 | 39,335 | 12/12 |
| F3 output silencing 2% | 94.27 [93.44, 95.83] | 4.15 | 39,936 | 12/12 |
| F3 output silencing 5% | 94.06 [92.71, 95.73] | 4.10 | 39,373.5 | 12/12 |
| F3 output silencing 10% | 95.10 [93.65, 96.56] | 4.15 | 39,753.5 | 12/12 |
| F4 historical hubs 1% | 119.06 [118.33, 119.90] | 4.20 | 49,272.5 | 12/12 |
| F4 historical hubs 2% | 114.79 [114.69, 115.21] | 4.20 | 38,861 | 12/12 |
| F4 historical hubs 5% | 93.96 [93.75, 94.27] | 4.25 | 34,115.5 | 12/12 |
| F5 LC4 | 75.52 [75.10, 76.15] | 6.10 | 34,543.5 | 12/12 |
| F5 LPLC2 | 64.27 [63.75, 64.90] | 5.00 | 27,686 | 12/12 |
| F5 both | 0.00 [0.00, 0.00] | Undefined | 21,191 | 0/12 |

## Calibration partitions

The threshold sources are negative-azimuth healthy trajectories at -60/-30
degrees, seeds 0-2. Their six logs exactly match six records in `episodes_v4`.

| Healthy partition | Scenarios | Collision-free records |
|---|---|---:|
| Calibration reuse | -60/-30 degrees, seeds 0-2 | 6/6 |
| Non-overlapping negative azimuth | -60/-30 degrees, seeds 3-5 | 6/6 |
| Positive azimuth | +30/+60 degrees, seeds 0-5 | 12/12 |
| Frontal | 0 degrees, seeds 0-2 | 0/3 |

Excluding exact reuse leaves 18/18 non-overlapping nonfrontal records. Positive
azimuths with seeds 0-2 still share calibration seed clusters. This post-hoc
partition is not a new independent test. Each archived fault has four nonfrontal
azimuths and seeds 0-2; six scenarios match calibration. Controls share the same
restriction. The analysis CSV separates scenario overlap from other records.

## Exposure and activity

Each legacy frame's `n_total` includes spikes through the end of that frame,
although `t_ms` labels its start. With 20 ms frames, the 400 ms count comes from
frame 19, labelled 380 ms. Duration equals recorded frame count times 20 ms.
Collisions truncate some episodes early.

For each matching azimuth/seed pair, retain three distinct ratios:

1. Whole episode: fault total divided by healthy total, allowing different durations.
2. Common paired duration: both cumulative counts through the shorter episode.
3. Fixed window: both cumulative counts through 400 ms, available for every pair.

The fixed window is a post-hoc diagnostic, not an episode-wide safety endpoint.
Full-episode spikes-per-second ratios are also saved; different temporal profiles
make them distinct from common-window comparisons.

| Historical condition | Survived | Whole ratio | Common-duration ratio | 400 ms ratio | 400 ms cluster 95% interval |
|---|---:|---:|---:|---:|---:|
| F2 25% | 10/12 | 0.8861 | 0.8861 | 0.8837 | [0.8330, 0.9607] |
| F2 50% | 0/12 | 0.3817 | 0.7294 | 0.7226 | [0.6366, 0.7451] |
| Full hubs | 12/12 | 1.7029 | 1.7029 | 1.3618 | [1.3543, 1.4050] |
| Inhibitory hubs | 6/12 | 71.6931 | 75.2306 | 118.1571 | [117.0610, 124.7201] |

All ratios shown are medians of episode-paired ratios. Intervals resample three
seed clusters 20,000 times, seed 0, keeping all four azimuths of a selected seed
together. They are descriptive and conditional on calibration and historical
configuration. At a twofold threshold, full hubs exceed in 6/12 whole episodes
and 0/12 fixed windows; inhibitory hubs exceed in 12/12 under both criteria.
Individual ratios and sensitivity to thresholds 1.5, 2, 3 and 4 are saved.

## Historical and fresh semantics

| Component | Historical archive | Fresh geometry-v2 code |
|---|---|---|
| Visual azimuth | Heading cancels, effectively world-frame | World bearing minus heading, wrapped to [-180,180) |
| Looming | Elapsed-time envelope | atan(radius / actual separation) and positive angular expansion |
| Retinal elevation | Assumed 40 degrees | Planar reference 0 degrees; RF construction still assumed |
| Collision | Recorded endpoint <= 0.05 m | Minimum frame-segment relative separation <= 0.05 m |
| Horizon | Nominal 1000 ms; attempted extension ineffective | Explicit fixed horizon; active burst flagged |
| Calibration | Controller-dependent chronology unresolved | Passive observe mode without steering or burst |
| Test membership | Reused healthy logs and seed clusters | Frozen calibration; shared calibration seeds rejected |
| Timestamp | Frame start labels post-frame state | Both frame start and end recorded |
| Neural step | Missing from historical manifest | Explicit 0.1 ms in provenance |
| Results | Archived whole-brain observations | Synthetic-input regression checks only |

Stimulus onset remains gated at 100 ms. In degrees/second, expansion determines
`gain = clip(max(0, expansion) / 150 * exp(-half_angle / 60), 0, 1)`.
RF rates multiply this gain by a Gaussian in body-frame azimuth and elevation
with width `max(30 degrees, half_angle)`, capped at 150 Hz per cell. RF centers
and gains remain modeling assumptions.

Calibration requires a complete -60/-30/0 degree grid with at least three seeds.
Within 250-300 ms, negative-azimuth episode maxima determine the median threshold.
Frontal left-right readouts determine median bias; negative-azimuth readouts
determine sign and the 90th-percentile absolute reference. Source hashes, RF seed,
threat speed and frame interval are frozen. The proposed sequence in
`../REPRODUCE.md` uses seeds 0-2 for calibration and 6-11 for testing.

Fresh success means no collision before the requested horizon, not eventual
escape. The pursuing threat, planar agent and delayed single burst are synthetic.
The hand rule replaces steering only; the network still supplies its burst trigger.

## Withdrawn claims and missing experiments

Historical hub runs lack cell manifests and reconstructed old sets include
protected cells. Corrected selection uses FlyWire identity exclusion and identity
ties. Matched healthy/hub/sign/random runs with one backend and controlled input
streams remain necessary. Existing backend and selector differences cannot be
assigned causal effects separately.

The intact null fails transmission, so relative fault-tolerance comparisons
against it are undefined. Walk-mass curves were removed because deletion sampling
must occur before sparse-edge coalescing. Future target-row/source-column
nonnegative adjacency powers count weighted walks, including repeated edges.
Under independent row survival p, a walk with d distinct rows has expectation
proportional to p^d; p^k requires k distinct rows. Unsigned all-DN mass alone
cannot explain signed eight-cell readout dynamics.

Pending work: fresh whole-brain passive calibration and held-out tests, corrected
hub and multi-null comparisons, horizon/threat/RF/actuator sensitivity, a
functioning matched-controller baseline, a validated simulator environment and
an explicit hardware fault mapping. Weight scaling is not quantization; output
silencing is not a failed core; spikes do not measure hardware energy. Conclusions
requiring these experiments were withdrawn, not reported as validated results.
