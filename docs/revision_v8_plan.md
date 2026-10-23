# Revision v8 argument and evidence plan

Paper type: empirical research case study. Sections: results, methods,
introduction, related work, conclusion and abstract. Language: English manuscript
from Chinese review. Venue style: existing five-page IEEE conference manuscript.

One-sentence argument: In a whole-connectome spiking model, interpretation of
software fault effects depends on assessment cohorts, observation exposure and
closed-loop control; prospective paired tests supply the task evidence, while
archive reanalysis quantifies recorded scoring/exposure changes under explicitly
weaker provenance.

The new controller-by-fault interaction is an open empirical question. A null
or imprecise interaction must remain a null or imprecise result; it cannot be
recast as demonstrated controller-dependent robustness. Healthy success
differences alone do not answer that question.

## Locked terminology

| Term | Definition |
|---|---|
| connection-table row | A weighted connection aggregating multiple contacts |
| transmission | Archived eight-cell rate at least 51.4 Hz |
| joint rule | Transmission plus rate/spike operational upper limits |
| activity ratio | Fault/healthy cumulative spikes at an explicit shared endpoint |
| collision-free survival | No collision through the declared horizon |
| paired task loss | Healthy survival and fault collision in one matched scenario |
| paired task gain | Healthy collision and fault survival in one matched scenario |
| net task loss | Healthy minus fault binary survival, including gains |
| controller interaction | Gated minus original net loss, paired by seed/bearing |
| seed cluster | Both fixed bearings and all controller/fault conditions for a seed |

## Evidence-to-claim map

- Main inference: prospective 72-record frozen matrix; no independence claim for
  its 72 records and no retuning on test outcomes.
- Cohort sensitivity: raw archive count reconstruction, supplementary evidence.
- Stopping-time effect: pair-specific common duration versus unequal whole
  episodes, distinct from truncating equal-duration hub records.
- Late crossings: recorded -60/-30 calibration scenarios only.
- Hardware/safety/resource budget: unsupported; operational thresholds only.

Use a challenge-first introduction: state the risk of interpreting a measurement
choice as intrinsic tolerance, identify what the case study measures, and state
its empirical contribution without claiming a new injector or architecture.
Move detailed per-seed records and numerical implementation settings to the
supplement; retain enough method detail to interpret the main results.

## Main review risks and discriminating checks

1. Controller effect might disappear under paired fault loss: report interaction
   intervals and every loss/gain, accepting an inconclusive result.
2. Reused healthy records might have incompatible generating conditions:
   require exact neural-source, runtime, calibration and input hashes.
3. Exposure mismatch might masquerade as activity change: fixed early windows
   plus common-duration ratios with no post-collision imputation.
4. Small directional samples and an already failing +30 baseline: retain
   directions, six seed clusters and limits in the abstract/conclusion.
