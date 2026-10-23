# ISCAS research optimization: decision log (started before new outcomes)

## Baseline and preservation

Local v8 main SHA256: `011e40516af3a791899a3de4fc934adf095e20c05a0c9d515f3c39b64dff002d`.
Local supplement SHA256: `72c763a8b061a626a80005234e3d056265b0d2114ab60228dc621266284138b8`.
Base HEAD `051dcb6a3123841041a34d3b43395e2841975879`, with substantial pre-existing local revisions.
Working branch `research/iscas2027-20261022`. A 21,069-file, hash-verified baseline
ZIP, full manifest, status and binary tracked patch are preserved at
`../drosophila-research-backups/20261022-acceptance-baseline/`.
No original results are edited. No push, submission or commit is authorized.

## Independent initial diagnosis

Read the full v8 review, its arithmetic/timing audits and current sources.
The v8 review is a useful diagnostic, not independent experimental evidence.

* B1: current five-page main includes technical content on page five. The
  official ISCAS rule is four technical pages plus an optional reference-only
  fifth page. Final validation must enforce this, rather than merely log it.
* B2: source independently confirms frame-start burst checks, nominal 250 ms
  delay / 450 ms duration, and a last-frame flag presented as a horizon flag.
  Archive-derived corrections must preserve raw records. Exact-event handling
  changes trajectories and requires fresh experiments. A further causal-order
  concern is that end-of-frame neural decisions drive that same frame's motion.
* B3: six clusters are the inferential sample size, not 72 episodes. The +30
  degree floor and the zero-success 50% conditions limit controller-interaction
  claims. Preserve the exploratory 25% p=0.25 and loss/gain counts. Do not call
  the conditional percentile interval confirmatory evidence.
* B4: endpoint dependence alone is insufficient novelty. An (2026) already
  varies task, network state and sparsification; Jo (2026) compares neural and
  virtual-arena responses. Prospective shared-record exposure contrasts and a
  reusable auditable paired protocol are plausible contributions, pending data.

Reviewer 1 (systems/novelty): Reject risk remains high without an engineering
artifact and prospective result beyond general reporting advice. Reviewer 2
(validity): correct event timing, input coupling and bilateral healthy ability
before testing fault claims. Reviewer 3 (inference/reproducibility): avoid
pseudoreplication, frozen known healthy reuse as prospective evidence, and
unverifiable historical manifests. All three see merit in explicit estimands,
provided claims remain bounded to this model and synthetic task.

## Contribution decisions before new data

A (endpoint mismatch): retain as a testable empirical question, not algorithm
novelty. B (exposure/horizon bias): retain and prospectively evaluate using the
same complete records. C (feedback dependence): retain only if independent
tests show a useful contrast away from healthy floor. D (deadline-aware metric):
exploratory candidate; do not promise discrimination. Thresholds must be fixed
on separate validation data. No hardware power, area, protection, biological
fault tolerance or physical bit-error claims are supported by functional row
deletions.

## Development protocol, registered before development simulations

Use a distinct `task-v9-causal-exact-events` protocol. Preserve geometry-v2
code and all v8 data. Decisions at the end of a 20 ms neural frame affect the
following motion frame. Split motion at exact trigger+250 and trigger+700 ms;
evaluate horizon burst state on [start,end), not the last frame. Collision is
first contact along the defined piecewise-linear motion segments. Threat
velocity is aimed at the agent at each segment's beginning. Continue the
defined counterfactual trajectory after first contact, latching task failure,
to record equal 1 s neural exposure. Full post-contact activity is a resource
estimand, not a prospective failure predictor. Early windows precede contact
and are evaluated separately.

Replace global Poisson RNG consumption with Bernoulli time-step inputs using
independent uniform arrays indexed by (20261022, seed, frame, stream=1).
Each cell/time probability is rate*0.1 ms, as in the discrete PoissonGroup
implementation. Uniforms are common across faults, bearings and laws, while
actual spikes can differ through closed-loop rates. Store both hashes.
Faults use a separate seed sequence (20261022,seed,2), nested 25/50% row masks;
store mask hash and realized row count. Selected command monitoring changes
recording only; validate neural/input correctness before campaign use.

Development seeds 200--203, passive healthy observations at -60,-30,0,+30,+60
degrees, 400 ms. The principal diagnosis is whether eight command rates carry
bilateral information that the original one-sided calibration discarded.
Fit an explicitly descriptive linear direction decoder from these development
records. Assess two simple neural-feedback laws (proportional and sign relay)
with onset gating, shared trigger, and identical physical actuator parameters.
Choose controller calibration only on development and separate validation
seeds; do not use old tests 6--17 or final new seeds for tuning. All development
attempts, failed configurations and raw data remain archived.

Provisional final matrix: 24 new clusters, two bearings, two frozen laws,
healthy/F2_25/F2_50 = 288 episodes. Select exact validation/test seed ranges,
analysis, thresholds, precision rationale and stopping rule in a second frozen
registration before starting final tests. No optional stopping on significance.
An additional RF-map replication is desirable but secondary to a complete,
checked main package before the deadline.

## Environment note

The previous environment recorded CPython 3.13.15 and a Brian2/Cython version
combination that pip rejects. Available managed Python is 3.12.14. v9 uses a
new isolated `tmp/v9-deps` with Brian2 2.10.1 and supported Cython 3.1.3;
exact installed versions and source/input hashes accompany new runs. This is
a new protocol/environment; never claim bit-identical replay of v8.

## Sources checked

* ISCAS author instructions: https://epapers2.org/iscas2027/ESR/authorinfo1.php
* Scope: https://2027.ieee-iscas.org/call-for-papers
* An author repository: https://github.com/aikian/flylite
* Jo preprint identifier: https://arxiv.org/abs/2610.19153
* Nijsink et al. physical radiation study: https://arxiv.org/html/2605.00030v1

Final conclusions, figures, manuscript text and final risk assessment will be
written from completed data, not from this provisional route.

## Eight-axis baseline assessment

| Axis | Material rejection risk in v8 | Research response and evidence standard |
|---|---|---|
| Novelty | Endpoint dependence and context-dependent connectome damage already appear in close work; standard statistics are not an invention. | Center the executable paired protocol and whatever independent task/exposure finding survives. Treat deadline forecasting as a candidate with a same-state actuator-schedule baseline. |
| Technical correctness | Confirmed 20 ms actuation quantization, six incorrect horizon flags, and end-of-frame neural output driving same-frame motion. | Exact-event causal protocol plus pure geometry, mock-loop and actual Brian2 input-schedule tests. Preserve old recorded outcomes as old-protocol data. |
| Experimental validity | One-sided calibration and +30-degree healthy floor obscure functional fault effects. | Symmetric development; configuration A failed its declared screen and was stopped; B uses new validation seeds. Final tests must retain every healthy failure. |
| Statistical strength | Six clusters, only three nonzero 25% interactions; conditional percentile exclusion differs from p=0.25. | Preserve this result without relabeling. Reserve 24 wholly new core clusters, fixed sample size and complete-cluster resampling; separate eight-cluster angle stress test. |
| Comparison fairness | Upper activity excursions naturally miss hypofunction; a geometry-aware predictor has more information than neural counts. | Add a healthy-calibrated two-sided activity comparator and identical-geometry actuator-schedule ablation. Report actual false alarms/misses and information differences. |
| Reproducibility | Public branches differ from local v8; original environment pin conflict, missing historical hub identities, and source/data tiers. | Verified baseline backup, independent branch, recreated supported environment, source/input snapshots, canonical relative paths, exact masks/maps and independent new outputs. Old missing manifests remain missing. |
| ISCAS relevance | No physical hardware mapping, physical upset model, power or area evidence. | Present sampled-data/actuator-aware SNN assessment with measured software cost. Physical radiation work is context, not a hardware-validation claim for this model. |
| Contribution clarity | Main mixes historical transmission, hub archive, geometry campaigns and small controller contrast. | Main will focus on one prospective protocol and one or two supported findings; historical evidence moves to a clearly labeled supporting audit. |

### Independent positioning against closest sources

An's author repository specifies FlyWire v630, task/state/operator contrasts and
neural population/readout metrics. Jo uses MaleCNS and includes paired circuit
and virtual-arena readouts, so neural/task endpoint separation is already a
substantive prior observation. The present FlyWire v783 experiment must earn
its distinction through explicit sampled-data timing, shared-noise/mask
counterfactual pairing and same-record exposure estimands. This is a difference
in the question tested, not a claim that the earlier papers mishandled exposure.
See https://github.com/aikian/flylite and https://arxiv.org/pdf/2610.19153.

SpikeFI and SpikingJET implement injection campaigns with application outputs;
this work neither executes nor benchmarks those frameworks. Nijsink et al.
report physical neutron testing; our high-severity functional row deletions have
no calibrated physical-error interpretation. Primary metadata checked at
https://arxiv.org/abs/2412.06795,
https://ieeexplore.ieee.org/abstract/document/10616060/ and
https://arxiv.org/html/2605.00030v1.

## Completed baseline reanalysis

`tools/audit_archive.py --out audit/acceptance-v9/archive-recomputed` reproduced
the four deletion/survival ratios, 276/288 transmission-only versus 262/288 joint
scores, HUB_inh median 847476.5 / mean 847857 spikes, six of twelve full-hub
closed-loop activity exceedances despite twelve survivors, and six of twelve
HUB_inh survivors with twelve bursts/exceedances. These remain historical
measurements with their original geometry/provenance caveats. No historical raw
record was edited and no corrected hub rerun is implied.

GitHub read-only heads at inspection: main `8463020054538e8b9989c0ee8848047d833c4a0c`,
submission `051dcb6a3123841041a34d3b43395e2841975879`.
External model HEAD `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`.
The current local revision therefore requires its own source/data artifact;
linking to public main alone would not reproduce this manuscript.

## Decisions from the complete independent core and angle test

The 288-record core and 96-record angle test completed, with no replaced seeds
or added efficacy stopping. All records passed independent input/geometry replay
and separate arithmetic checks. Main title is now *Paired Fault Assessment of a
Fly-Connectome Spiking Controller*. The strongest result is the conditional
50%-deletion system contrast: proportional 37/48 versus relay 48/48, against
healthy 48/48 under each law. Registered relay-minus-proportional net loss is
-22.9 pp, cluster interval [-33.3,-12.5], Holm p=.001953125. The 25% contrast
is -4.2 pp [-10.4,0], p=.50; it remains uncertain. The old six-cluster p=.25
belongs to a different original/gated comparison and remains unchanged.

Healthy capability is bilateral in the core, but minimum-clearance medians
33.1/41.4 mm and different turning effort show unequal nominal reserves.
Therefore C supports whole-system feedback dependence, not a fault-specific
superiority claim with healthy quality held constant. A reserve-matched new
control comparison was not executed; test observations are not reused for gain
retuning. The exact-state warning candidate remains secondary: 13/13 collisions
detected with 57/275 false alarms, versus 84/275 for its same-state schedule
baseline. The specificity increment is descriptive, not a newly registered
confirmatory claim or algorithm invention.

A is retained as a measured calibration-dependent mismatch: command/two-sided
activity detect only 2/13 and 3/13 collisions. B is split: task horizon changes
collision count 2/2/13 at 800/900/1000 ms, but stopped/common activity group
medians are identical, with maximum pair difference <.00325. The old large
exposure shift is withdrawn as a current main finding. Honest negative findings
take precedence over keeping the earlier title or story.

The prespecified eight-cluster +/-45-degree test is separate: healthy/25% all
success, proportional/relay 50% 14/16 versus 16/16, interval [-31.3,0] pp.
Only two collisions and poor two-sided healthy flag transfer (22/32) prevent
strong generalization. The secondary eight-cluster action diagnostic has its
own registration and does not enlarge the 24-cluster primary inference.

Original frozen analysis code is preserved. Its duplicate numeric-margin and
Boolean-flag CSV keys failed during export before statistics were written.
The minimal exportfix only renames numeric columns; metrics, thresholds,
sample size and raw data do not change. Exact diff and source SHA evidence are
in PROTOCOL_v9_NOTES and audit/acceptance-v9/analysis-export-correction.json.
Final simulated reviews deliberately retain novelty, single-model scope,
unmatched healthy reserve, sparse positives and absent hardware as material
rejection risks; implementation effort does not itself justify acceptance.
