# Assessment v9: frozen prospective protocol

Status at registration: all development/validation complete, independent core
tests not yet run. Test execution begins only after the two JSON registrations.
The final execution report, not this registration, determines completion.

## Identity and evidence separation

* Neural/task protocol: `task-v9.1-causal-exact-events`.
* Core registration: `runs/task-v9-frozen/registration-core.json`, SHA256
  `7efa2ad4da4dc72cfd5773c57adc44020f12981fcc30d78e9b3c5d10d395b54f`.
* Frozen calibration: `runs/task-v9-frozen/calibration.json`, SHA256
  `8ba27037d006ba6a8ae581c07170be6ac1ed0563873d4a3dc60af6d35d8e4ddf`.
* Stress registration: `runs/task-v9-frozen/registration-stress.json`, binding
  the same implementation, calibration and thresholds to a separate cohort.
* Old v8 uses geometry-v2, different controller laws, input RNG and stopping
  semantics. Its six-cluster p=0.25 is preserved as exploratory history. Do not
  pool its records with v9 or call a new controller contrast a replication of
  that original/gated contrast.

Development was 20 passive 400 ms episodes on seeds 200--203 and five bearings.
The initial 400 deg/s configuration failed the declared capability screen;
its six completed records remain at `runs/task-v9-validation`. The final common
600 deg/s limit and silence gate were selected during development, while keeping
the fitted decoder and trigger threshold. New healthy validation seeds 400--407
gave 8/8 success in each of four law/bearing strata. All 32 records remain in
calibration; no successful-seed filtering is performed. A two-cluster fault
screen retained 16 records, including one failed 50%-deletion episode. It did
not drive metric threshold fitting. See `PROTOCOL_v9_DEVELOPMENT.md` for the
chronological decisions and failed attempt.

## Independent matrices and stopping rule

Core: seeds 1000--1023, bearings -30/+30 degrees, proportional/relay laws,
healthy/F2_25/F2_50 = 288 fresh episodes in 24 seed clusters. Stress: seeds
1100--1107 and -45/+45 degrees, otherwise unchanged = 96 fresh episodes in
eight separate clusters. These angles were absent from calibration/validation.
Do not pool core and stress for significance. Do not replace seeds, stop for
efficacy, tune thresholds or extend sample size after observing outcomes.
Stress cancellation is permitted only for time/resource constraints and must
be disclosed; all produced records remain available.

For [0,1]-valued success/loss/gain means, the maximum-variance normal planning
half-width at 24 clusters is approximately 0.20. This does not apply to signed
net-loss or interaction contrasts (range-based approximations about 0.40/0.80),
and is not a finite-sample coverage guarantee. See `PROTOCOL_v9_NOTES.md` for
the explicit clarification of the frozen registration's shorthand. Actual
conditional intervals are reported; the design does not establish small
interactions or equivalence. Sparse failure clusters remain a limitation.

## Dynamics, clocks and input coupling

The 138639-neuron, 15091983-row signed graph and default LIF parameters use
0.1 ms integration, 2.2 ms sensory refractoriness, 1.8 ms recurrent delay,
0.275 mV/contact, and 68.75 mV external events. Eight command cells and 314
sensory cells are identified by actual FlyWire IDs. The map seed is 20260201;
the inactive background pool uses seed 0. All identities and receptive-field
values are saved in `input-map.json`; digit strings preserve large identifiers.

Input variates have SeedSequence [20261022, seed, frame, 1], shape
(200 time steps, input-pool size), float32 uniform. An event occurs if U is
below rate*0.0001. The complete arrays are common across laws, doses and angles
within seed. Rate-dependent thinning changes realized events under feedback.
Deletion uses an independent SeedSequence [20261022, seed, 2] with one float64
uniform per weighted connection row. Thresholds .25 and .50 give nested masks.
Saved mask digests, counts and realized signed damage are checked; no equality
of contact mass across heterogeneous masks is imposed.

For relative position r and heading theta, body-frame bearing is
wrap(degrees(atan2(r_y,r_x))-theta). Angular half-size is degrees(atan(.05/|r|)).
Finite-difference expansion over 20 ms supplies the looming gain
clip(max(0,expansion)/150 * exp(-half_size/60),0,1). A Gaussian receptive-field
map with minimum angular sigma 30 degrees gives rates capped at 150 Hz.
No visual input precedes the 100 ms cue. The map is assumed, not measured.

At each 20 ms frame, neural outputs are measured; decisions at its END apply
to the NEXT motion interval. The direction score is a ridge-fitted linear
function of five-frame means of the eight command rates. Both laws turn zero
before/equal to the cue or below the 4.03125 Hz eight-cell mean trigger level.
Otherwise proportional clips the score to [-1,1], relay uses its sign, both
multiplied by -600 deg/s. Heading is capped at +/-100 degrees.

The first qualifying frame end t_d schedules one burst on
[t_d+250,t_d+700) ms. Walk/burst speeds are .05/.35 m/s. The pursuer starts
.25 m away and moves at .3 m/s toward the agent at each segment start.
Split motion at scheduled burst events even inside feedback frames. Positions
are linear within each segment at its starting heading; non-burst heading is
updated at the segment END. First contact with radius .05 m is calculated
inside the segment. This specifies a discrete sampled plant, not exact
continuous unicycle dynamics. Horizon burst state is evaluated at exactly
1000 ms, not copied from the last interval flag.

Task failure latches at first contact through 1000 ms. Continue the stated
trajectory and neural loop after contact to retain equal exposure. Post-contact
activity is an explicitly simulated counterfactual resource measure, with no
contact mechanics; it is not pre-failure warning data or eventual escape.

## Estimands, metrics and inference

Report loss, gain and net loss against the same-law/bearing/seed healthy trial.
Average bearings inside seed, then compare relay minus proportional net loss.
Use 20000 complete-seed bootstrap draws, RNG 20261022. Exact cluster sign-flip
sensitivity assumes a symmetric null, with Holm adjustment for two doses; it
does not arise from randomized controller assignment. Report each direction
and healthy risk set. Fixed 800/900/1000 ms task observations are repeated
horizons, not new independent trials.

Spike estimands: counts at each member's own contact-frame/horizon, counts at
the earlier common frame, fixed 400 ms, and complete 1000 ms. Common exposure
is still outcome-dependent. Fixed activity profiles at 200/400/600/800/1000 ms
are reported without choosing a favorable window. All 400 ms assessments must
precede first contact, checked explicitly.

400 ms warnings are frozen from healthy validation only:

* Mean command rate over 100--400 ms below 5.833333333333334 Hz.
* Upper activity excursion above twice the law/side healthy median.
* Two-sided absolute log activity ratio above 0.169456319362701, corresponding
  to [0.8441236255330035,1.1846605991729846] times the reference.
* Held-command kinematic forecast: use 400 ms geometry, current neural-derived
  turn command and pending burst; assume the earliest next-frame trigger if
  absent. Hold this turn command to 1000 ms and warn below 0.018772702392980428 m
  predicted minimum clearance (distance minus collision radius).
* Same-state actuator-schedule baseline: zero future turn, same pending burst;
  threshold 0.018548259924690145 m.

The forecasts have exact simulated geometry and are not neural-only, sensor
implementations or reachability guarantees. The schedule baseline separates
actuator observability from additional neural-turn extrapolation. Both are
candidates, not promised innovations. The nominal healthy flag level is 5%;
actual task sensitivity/specificity/FPR/FNR are evaluated on ALL independent
records and fault/healthy/law/bearing subgroups. Retrospective own-stop resource
flags are not prospective warnings. For zero observed errors, a degenerate
bootstrap interval is accompanied by the cluster-any-error bound; no zero-risk
claim is allowed. Stress activity references transfer from the same-side
30-degree validation stratum; all thresholds stay fixed.

## Reusable audit and execution controls

`tools/replay_audit_v9.py` independently reconstructs geometry, looming,
readout smoothing, trigger decisions, causal steering, exact burst segments,
first contact, masks, shared uniforms and every realized input event hash. It
does not import the task implementation or resimulate neural dynamics. Passing
this audit establishes trace/input consistency, not correctness of all neural
equations. The complete 16-record validation fault screen passed this replay.

New workers snapshot generating sources and reject mixed configurations.
`--resume` requires identical source, environment, input and registration
hashes; changed source demands a separate run or replay from its snapshot.
Historical outputs are never overwritten. Versions and source bindings are
documented in the registrations and per-worker manifests.

Reanalysis and fresh-replication commands are in `../docs/REPRODUCE_v9.md`.
The public main/submission branches do not identify this uncommitted local
revision. A versioned source/data artifact is required; no push or submission
is performed by this workflow.

## Secondary action-ablation registration (after core launch)

At 2026-10-22 05:18:27 UTC, while the core was running and before complete core
analysis, a separate diagnostic matrix was registered in
`runs/task-v9-frozen/registration-causal.json` (SHA256
`020ad97501b7fbde836cfaf032b47679cbab4a3d330692543e1109a6cd015c86`).
It uses eight new seeds 1200--1207, both core bearings, and healthy networks
under proportional, relay, turn-disabled and all-action-disabled interfaces:
64 new episodes. `disabled` sets turning to zero while retaining neural burst
triggering; `observe` prevents turning and burst action. The normal laws,
calibration, task and exogenous input coupling stay unchanged.

This checks whether normal task capability actually depends on the motor
interface. It cannot establish superiority of the connectome over another
controller. It was not part of the original core registration, is not pooled
with the core/stress, and adds no primary significance test. Paired effects
are descriptive eight-cluster intervals. Exactly eight clusters are run,
without tuning, seed replacement or efficacy stopping. Deadline/resource-only
cancellation is permitted and disclosed. All records, including failed normal
controls, remain available. Registration is not evidence of completion.
