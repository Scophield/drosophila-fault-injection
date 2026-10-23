# Development and validation registration (before validation outcomes)

Development: 20 passive 400 ms episodes, seeds 200--203 and bearings
-60,-30,0,+30,+60 degrees, now complete. All raw observations are retained.
The existing side/identity map is unchanged. The eight ordered command rates
contain bilateral information; development fit accuracy is not test evidence.

The direction decoder is ridge regression (penalty 10, unpenalized intercept)
of bearing/60 on standardized five-frame command rates in 200--400 ms.
It predicts an assumed direction score, not a biological receptive field.
The burst threshold is half the tenth percentile of per-development-episode
mean command rate in 200--300 ms, bounded below at 2.5 Hz. This yields
4.03125 Hz. Both laws use 400 deg/s maximum turn rate and zero steering before
the cue. Proportional steering clips the decoder score to [-1,1]; relay uses
its sign. Physical task constants remain common. Neither law is claimed novel.

Validation: seeds 300--303, bearings -30,+30; proportional/relay crossed with
healthy,F2_25,F2_50. Total 48 complete 1 s episodes, four independent clusters.
The exact frozen calibration is `runs/task-v9-development/calibration-frozen.json`.
The phase is developmental: controller changes remain permitted if bilateral
healthy capability is inadequate, but every attempt and calibration is kept.
No final test seeds are run or inspected during this phase.

Criterion to retain the initial calibration: each law should achieve at least
3/4 healthy successes in EACH bearing. This is a capability screen, not a
precision claim about population success. If unmet, diagnose rather than
selecting favorable test seeds. A smaller or failed capability must be reported.

Before independent tests, freeze metric definitions/thresholds using only these
validation data; publish a JSON registration with exact seed range, hashes,
sample size, estimands and fixed stopping rule. Planned primary inferential
unit is the complete seed cluster. Early metrics use only observations through
400 ms; verify this precedes collision in every included record. The full 1 s
neural activity after latched contact is explicitly counterfactual resource
exposure. Do not reinterpret it as a pre-failure warning.

First validation command:

```text
python tools/run_v9.py tools/launch_task_v9.py --out runs/task-v9-validation --seeds 300,301,302,303 --calibration runs/task-v9-development/calibration-frozen.json --role validation
```

This local registration is not an externally timestamped preregistration.

## Configuration B, before its validation

Configuration A was stopped after six completed records (three healthy, three
25%-deletion, all proportional/-30); healthy successes were 1/3, making the
3/4 requirement impossible. Two of its three fault records survived, which is
retained as developmental evidence, not promoted to a fault-benefit finding. All complete
records and its actual stop reason remain in `runs/task-v9-validation`.

Trajectory inspection shows only 58--65 degree heading at burst onset in the
three healthy cases; two contacts occur at 975 and 998 ms after the burst.
Configuration B increases the COMMON proportional/relay turn limit to 600 deg/s
and sets steering to zero whenever the smoothed mean command rate is below the
trigger threshold. The decoder and trigger threshold are unchanged. This avoids
an intercept-driven turn during silence. Exact actuation and geometry are
unchanged. Protocol identifier is now `task-v9.1-causal-exact-events`.

New validation seeds 400--407 are disjoint from development and initial
validation. Run healthy only: eight clusters x two bearings x two laws = 32
episodes. Require at least 6/8 healthy successes in EACH law/bearing to retain
this configuration. Metric thresholds use only these healthy observations;
fault-label optimization is deliberately unnecessary. This change reduces
development computation while reserving all fault comparisons for the new
independent factorial test. No final seed has been run or inspected.

```text
python tools/run_v9.py tools/launch_task_v9.py --out runs/task-v9-validation-B --seeds 400,401,402,403,404,405,406,407 --calibration runs/task-v9-development/calibration-B-frozen.json --role validation --faults healthy
```

## Informative operating-point check, before independent tests

After the first 24 healthy-B records all survived, add a minimal fault screen
on validation seeds 400 and 401, both bearings/laws and F2_25/F2_50: 16 episodes
in `runs/task-v9-fault-screen`. These are still development/validation, never
independent test evidence. Their purpose is to detect a task ceiling before
spending the 288-episode test budget. Retain all outcomes and document any
operating-point change before final registration. Metric thresholds remain
healthy-validation-only; do not optimize them on these fault labels.

Warnings use a common nominal 5% healthy flag calibration: lower fifth
percentile of command rate or forecast margin; upper 95th percentile of absolute
log normalized activity for the two-sided comparator. This is a healthy flag
rate, not a guaranteed task false-positive rate: all healthy records, including
task failures, remain in calibration. A state/actuator-schedule baseline holds
future steering at zero, while the deadline candidate holds the currently
available neural-derived turn command. Both have the same known geometry and
pending burst schedule. Any gain is an empirical observability result, not new
statistical or control algorithm novelty.

## Prespecified additional-bearing stress test (before core tests)

To address the review's concrete single-bearing-per-side limitation, reserve
seeds 1100--1107 for +/-45 degrees, both frozen laws and all three networks:
96 episodes in a separate test tree. These bearings are absent from controller
calibration and validation (interpolation between development +/-30 and +/-60).
Use the exact same frozen decoder, trigger, physical parameters and metric
thresholds. Activity references transfer from the same-side +/-30 validation
stratum. No threshold or controller fitting on stress outcomes is permitted.
Report this eight-cluster stress test separately from the core 24-cluster test;
do not pool them to improve significance. Run it after the core, with cancellation
allowed only for deadline/resource constraints and explicitly disclosed.
The expected additional elapsed cost is ~1.5 h at three workers, based on actual
validation episode times. This addresses azimuth transfer, not RF-map or
connectome generalization. No independent test seed has yet been run.
