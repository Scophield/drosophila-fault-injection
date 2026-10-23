# Canonical terminology and claim scope

| Term | Definition and decision |
|---|---|
| connection-row deletion | F2 zeroes a weighted table row and every contact represented by that row. Not individual-contact deletion or hardware bit flips. |
| seed cluster | Shared mask/uniform seed across both bearings, both laws and all doses. The independent resampling unit. |
| common uniforms | Same cell/time random variates, not identical realized spike trains. Feedback changes rate-dependent thinning. |
| collision-free survival | No first contact at or before the fixed 1 s horizon. Does not mean eventual escape. |
| stopped-count ratio | Counts at each trajectory's own first-contact frame/horizon, divided within the pair. Unequal exposure is allowed by this definition. |
| common-duration ratio | Both counts evaluated at the earlier recorded stopping frame. Still outcome-dependent; not a fixed-exposure causal effect. |
| fixed-prefix activity | Counts at 400 ms; separately verify it is before first contact. |
| full-horizon activity | Simulated 1 s count with latched failure and continued post-contact trajectories. A specified counterfactual resource estimand. |
| paired loss / gain | Healthy success -> fault failure / healthy failure -> fault success, within law/bearing/seed. Report both, not just net difference. |
| controller interaction | Relay net loss minus proportional net loss, averaging bearings within seed. No mechanistic interpretation solely from a baseline/floor difference. |
| deadline candidate | Held-command kinematic extrapolation from 400 ms state, current neural-derived turn command and actuator schedule. Uses exact simulated geometry; not neural-only or a reachability guarantee. |
| activity envelope | Operational resource excursion rule. Its disagreement with task outcome alone is not a validated detector improvement. |
| independent test | New seeds 1000--1023, only after frozen calibration/threshold registration. Development and validation remain separate. |

Writing axes: methods/evaluation case study; full manuscript; Chinese research
brief to English prose; IEEE ISCAS regular paper (generic venue skill), four
technical pages plus optional reference-only fifth page. Introduction uses a
technical-challenge structure: define the assessment failure, explain what
existing tools/studies already establish, then specify the reusable protocol
and bounded experiment. Abstract and conclusions are written after results.

Provisional one-sentence argument: An auditable paired closed-loop assessment
can separate neural transmission, exposure-dependent activity and task failure
under common input randomness; prospective evidence must determine the size,
direction and limitations of those differences.

No novelty claim is made for ridge regression, relay/proportional control,
bootstrap, common random numbers, or a threshold combination. The engineering
artifact is the executable assessment protocol and its source-bound evidence.
