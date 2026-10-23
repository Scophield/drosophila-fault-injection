# Manuscript review: assessment-v3, 21 October 2026

**Assumed venue: IEEE ISCAS 2027, regular paper, Neural Networks and Neuromorphic Engineering. Recommendation: 5/10, weak reject / borderline. Confidence: 4/5.**

This version is materially stronger than the earlier archive reassessment: it contains nine passive calibration episodes and 48 actual whole-connectome tests, separates calibration seeds, propagates healthy-reference uncertainty, and withdraws unsupported hub and hardware conclusions. Those earlier objections should not be repeated as unresolved defects. The remaining acceptance risks are the interpretation of shortened observation windows, the unisolated controller bias, and whether this carefully bounded case study provides enough new insight for a regular ISCAS paper.

Scope: I read main.tex, all five included sections in order, both bibliographies, IEEEtran/build configuration, PROTOCOL_v3, reproduction documentation, relevant implementation and manifests. I inspected all five current PDF pages and three supplementary plots, then independently recomputed the central counts, calibration and effects. No cover/response letter or manuscript appendix was found. Source locations below refer to paper/sections unless prefixed otherwise.

## Phase 1 - Understand the paper

1. **Problem.** Do cohort inclusion, endpoint definitions and observation duration materially change fault assessments of one fly-connectome spiking model?

2. **Claimed contributions and my reading.** Introduction, intro.tex:7:

   - "cohort-specific agreement between transmission and an activity-constrained rule": a descriptive decomposition of disagreement, rather than a new fault injector or validated failure detector.
   - "compare paired activity over common windows": an exposure audit that contains both unequal-duration comparisons and changes to the chosen horizon; these must be distinguished.
   - "New full-connectome tests examine a frozen-calibration controller on disjoint seeds": a genuine new simulation campaign, with limited directional performance and six independent seed clusters.

3. **Method, in four sentences.** A 138,639-neuron Brian2 LIF network uses 15,091,983 signed connection-table rows representing approximately 54.5 million contacts. Input drives 104 LC4 and 210 LPLC2 cells; eight descending neurons supply a rate and steering readout. Five perturbation families alter weights, connections, random outputs, hub outputs or sensory outputs, and archived records are scored for transmission and upper activity limits. A new geometric loop derives retinal input from relative position and heading, calibrates passively, and measures collision-free survival over a fixed horizon.

4. **Experimental setup.** The substrate is one FlyWire v783 connectome; controls include a target-permuted graph, sign/composition/random-inhibitory lesions, readout disabling and a privileged geometric feasibility rule. Main conditions use 12 trials of 600 ms at 150 Hz; selected drive controls use 75/300 Hz. F1 uses lognormal sigma 0.05/0.10/0.20/0.50; F2 deletes 5/10/25/50%; F3 silences 1/2/5/10%; F4 targets 1/2/5%; F5 removes either/both channels. Membrane/synaptic constants are 20/5 ms, threshold/reset -45/-52 mV, delay 1.8 ms and refractory interval 2.2 ms. Fresh integration uses 0.1 ms; historical timestep and per-trial input seeds are unavailable. Fresh passive calibration uses three bearings and seeds 0-2; tests use seeds 6-11, two bearings and four groups, totaling 48 episodes. Thresholds are 51.4 Hz open-loop and 18.125 Hz fresh behavioral calibration. Metrics are command rate, first-spike latency, total/common-window spikes and bounded survival. Bootstrap intervals use 20,000 draws; legacy cluster sensitivity enumerates 27 resamples. No confirmatory significance or equivalence claim is made. Fresh execution uses CPython 3.13.15, Brian2 2.10.1, NumPy 2.5.4 and NumPy code generation. Documentation reports roughly 1.2 GB per process and 12-13 seconds per 100-ms pilot, but not total campaign CPU/wall time.

5. **Headline results**, independently reproduced:

| Measurement | Result | Interpretation |
|---|---:|---|
| Healthy / 50%-deletion command rate | 94.69 / 72.40 Hz | Retention 76.46%; reference-aware interval 75.11-78.96% |
| First-spike latency | 4.05 / 5.40 ms | Ratio 1.333; interval 1.253-1.400 |
| All archived fault/control records | 276/288 transmission; 262/288 joint | Fourteen disagreements |
| Excluding targeted hub cohorts | 192/204 versus 190/204 | Two disagreements; main non-hub sweep has none |
| Legacy F2_50 paired activity | 0.382 whole; 0.723 first 400 ms | Unequal termination affects whole totals |
| Legacy full-hub exceedances | 6/12 whole; 0/12 first 400 ms | A horizon-dependent result; whole durations already match |
| Fresh healthy / F2_25 / F2_50 / readout-off survival | 5/12 / 4/12 / 0/12 / 0/12 | All survivors are at -30 degrees |
| Fresh F2_25 / F2_50 first-400-ms ratio | 0.983 / 0.890 | Neither exceeds twofold despite task collisions |

6. **Stated limitations.** One connectome, selected drives, small conditional samples, a nonfunctional null, missing historical hub identities, assumed receptive fields, legacy calibration reuse, exploratory windows/exclusions, directional calibration, pre-cue steering, unfinished bursts at the horizon and simultaneous protocol changes are explicitly acknowledged (principles.tex:4-10). These are substantially more accurate boundaries than the previous design-principle framing.

## Phase 2 - Recover the standard

Venue inference follows README.md:4, IEEEtran conference mode, author identities, numerical references and the five-page layout.

| Official 2027 document | Sections used | Standard applied |
|---|---|---|
| [Call for Papers](https://2027.ieee-iscas.org/call-for-papers) | "Scope of Contributions"; "Types of Contributions"; "Call for Regular Papers" | Neuromorphic engineering is in scope; regular papers require original research contributing to the state of the art. |
| [Author Information](https://epapers2.org/iscas2027/ESR/authorinfo1.php) | "Paper Specifications"; "Important Deadlines" | Four technical pages plus an optional references-only fifth page; embedded fonts, no encryption, maximum 5 MB; author identities included. |
| [Templates](https://epapers2.org/iscas2027/ESR/samples.php) | "LaTeX Templates"; "Preparation of the bibliography in LaTeX" | IEEEtran conference class and IEEEtran bibliography style. |

Accessed **21 October 2026**; these pages expose no document revision date. The submission portal states **22 October 2026, 23:59 UTC-05:00**. I found no public regular-paper review form or native numeric scale; therefore the following 1-10 rubric is reviewer-defined. The website's tutorial evaluation criteria are not a regular-paper rubric.

The current PDF passes local format checks: five Letter pages, references only on page five, 297,637 bytes, 20 embedded fonts, zero Type 3 fonts and no encryption. This does not establish conference-system validation.

## Phase 3 - Rubric table

Higher is better; confidence uses 1-5. These dimensions are not mechanically averaged.

| Dimension | Score | Rationale | Concrete required fix |
|---|---:|---|---|
| Overall | **5/10** | Honest, reproducible case study with unresolved interpretation/control questions. | Resolve B1-B2 and foreground fresh evidence. |
| Confidence | 4/5 | Core records and calculations reproduce; no new neural campaign was run during review. | Preserve generating-source versions; PROTOCOL_v3:172. |
| Novelty | 5/10 | Empirical sensitivity is useful, but nested scoring and cohort reweighting are familiar. | State the new empirical lesson precisely; intro.tex:7. |
| Soundness | 7/10 | Counts and equations check; causal separation remains incomplete. | Separate horizon truncation from duration matching; IV-D. |
| Theoretical depth | 4/10 | Appropriate descriptive mathematics, without a general estimand analysis. | Define each ratio and stopping rule symbolically; III-D. |
| Empirical strength | 6/10 | Real held-out runs improve evidence; bias and directional floor effects limit interpretation. | Add bias-preserving and pre-cue controls; IV-E. |
| Reproducibility | 8/10 | Raw trajectories, hashes and generators are supplied locally. | Bind source snapshots to batch hashes and provide reviewer access; supplement. |
| Clarity | 8/10 | Operational limits and invalid historical comparisons are explicitly identified. | Replace ambiguous exposure language; principles.tex:2. |
| Significance | 5/10 | Relevant assessment caution, with limited demonstrated transfer. | Explain which evaluation decision the findings change; Sec. V. |
| Ethics/safety | 8/10 | No unsupported safety, energy or biological-resilience claims remain. | Retain these boundaries in abstract and release descriptions. |
| SOTA/related work | 7/10 | Relevant injectors, connectome perturbations and benchmarking are covered. | Discuss Jo and directional biology; Sec. II. |
| Figures/tables | 7/10 | Labels, units and dispersion definitions are readable. | Promote prospective outcomes and late-time crossings; Fig. 3/IV-E. |
| Bibliography | 8/10 | Major prior miscitation/year/type defects are repaired in compiled references. | Add relevant uncited context; avoid maintaining stale duplicate databases. |

## Phase 4 - Detailed findings

### B1. Shortening a matched horizon must not be described as correcting unequal exposure

**Location:** results.tex:77-79; principles.tex:2; Fig. 3b.

> "Equal exposure changes historical full-hub activity classification."

Every full-hub episode and its paired healthy reference already lasts **1000 ms**. Independent reconstruction finds no twofold cumulative-ratio exceedance through 800 ms, then six at 900 and 1000 ms; first crossings occur at **840-900 ms**. All six are the negative-azimuth calibration scenarios. Thus early windows exclude a late event; they do not repair unequal durations for this cohort. F2_50 genuinely involves unequal termination, and its common-duration ratio is 0.729.

**Why acceptance-critical:** The paper's central assessment lesson could be misread as eliminating an activity warning through fairer matching, when the warning is real under the declared one-second criterion.

**Fix:** Separate the two estimands and extend the full-hub time-course through one second, stratified by direction/calibration status. Replace the quoted sentence with: "For full-hub pairs, both records last one second; limiting observation to the first 400 ms excludes late twofold exceedances. For F2_50, matching unequal episode durations changes the spike ratio." No new neural simulation is necessary.

### B2. The fresh controller comparison does not isolate neural steering from the calibration offset

**Location:** methods.tex:38; results.tex:82; principles.tex:8; run_closedloop.py:108-134; PROTOCOL_v3:128-134.

> "The new tests establish executable neural feedback with limited directional performance."

The test split is valid, and these are real whole-connectome records. However, all 12 healthy tests turn **-11.429 degrees before the 100-ms cue while recording zero spikes**, because subtracting bias -20 Hz produces -114.286 degrees/s at zero readout. Readout disabling also removes this offset and the burst trigger. It therefore cannot isolate how much the survival difference depends on stimulus-dependent steering, constant turning, or triggering.

**Why acceptance-critical:** With 5/6 versus 0/6 healthy directional survival, floor effects and controller assumptions can dominate the purported fault comparison. The result remains a valid observation of this controller, but its interpretation needs a controlled counterfactual.

**Fix:** Freeze the existing results. On new paired seed clusters, compare the current law with pre-cue steering gated off and with zeroed steering readout retaining the offset and identical neural burst-trigger logic. Add a steering-disabled/neural-trigger control if needed to separate trigger from steering. Report both bearings and paired seed outcomes. Do not retune the threshold on these tests or present six paired clusters as 12 independent replicates.

**Significance judgment:** A negative controller result can be publishable. Neither excellent healthy performance, a new theorem, corrected hub experiments nor hardware deployment is intrinsically required for this revised scope. Acceptance depends on turning these two ambiguities into a clear, transferable assessment lesson.

### Section-by-section feedback

| Section | Assessment and concrete edit |
|---|---|
| Abstract, main.tex:42 | Accurately reports the hub-exclusion collapse and fresh failures, but packs too many denominators into one paragraph. Replace the opening with: "We study how cohort composition and observation horizon alter fault classifications in one connectome-based spiking model." Explicitly distinguish the unequal-duration F2 result from late full-hub activity. |
| Introduction, intro.tex:3-7 | The structural-prior distinction and narrowly stated question are appropriate. The practical decision remains vague. Add: "We distinguish matching exposure between paired runs from selecting an earlier endpoint; neither operation establishes a valid resource budget." |
| Related Work, related.tex:2-4 | Correctly credits An and avoids claiming a first fly perturbation study. Add: "Our contribution concerns assessment sensitivity within a declared cohort, rather than a new perturbation operator or superior fault tolerance." Discuss Jo's endpoint-dependent damage results. |
| Methods, III-A-E | Equations, perturbation semantics and resampling units are substantially improved. Fresh steering and trigger equations are absent from the main text. Add the bias-subtracted steering law, five-frame smoothing, onset gate and burst trigger; label the 2.2-ms sensory refractory wrapper as a model variant. |
| Experiments, IV-A-E | Table II exposes concentration of disagreements; IV-E reports failures rather than hiding them. The strongest fresh evidence is buried after legacy material. Move prospective directional outcomes into a main table/figure and separate retrospective and prospective estimands. |
| Discussion, principles.tex:2-8 | Correctly declines hardware/safety conclusions and notes unfinished bursts. Replace "Equal exposure changes..." as in B1. Explain that zero disagreements in the main non-hub sweep is evidence limiting the scope of the activity criterion. |
| Conclusion, principles.tex:10 | The conditional conclusion fits the evidence, but "materially change fault assessment" needs its boundary. Write: "In this archive, cohort membership and endpoint horizon alter selected classifications; prospective deletion tests additionally show that low relative activity does not imply collision-free survival." |
| Appendix/supplement | No manuscript appendix exists. PROTOCOL_v3 provides counts, windows, seed effects and release scope. Add an explicit formula/definition index, generating-source snapshots and a compact campaign compute table; make the exact supplement accessible to reviewers. |

### Equations and proofs

**Equation (1)** is dimensionally consistent: v and g are voltages, and both derivatives have voltage/time units. Decay, reset, refractory pause and threshold match the inspected implementation. External events add 68.75 mV to v, whereas recurrent events add signed contact-scaled increments to g; preserve that distinction.

For **F1**, E[exp(sigma Z - sigma squared/2)] = 1 and CV = sqrt(exp(sigma squared)-1), giving 0.53294 at sigma 0.5. F2's expected lost absolute contact mass is f times the original mass under independent row deletion.

**Equation (2)** defines a nested operational rule, so J is necessarily a subset of T. Its disagreement count does not establish diagnostic accuracy. Include Hz explicitly and define the paired activity estimand as cumulative fault spikes through t divided by paired healthy spikes through the same t. A whole-episode ratio with different stopping times is a different estimand.

The reported retention and latency intervals reproduce. Enumerating 27 legacy cluster draws correctly reveals sparse bootstrap support. There are no theorem or appendix proofs requiring further audit.

### Every main figure and table

| Item | Claim, support, missing checks and presentation |
|---|---|
| Fig. 1, III-A | Supports pathway instrumentation, not causal relay importance. Contact-width encoding and mapped identities are readable; selection/generator hashes exist. Identify left/right command labels and label F3/F4 arrows as output silencing. No statistical bars are needed for this schematic. |
| Table I, IV-A | Selected-dose command retention is supported by raw 12-trial records and reproducible medians/CIs. Historical F4 is explicitly labeled; zero-response latency is correctly blank. Add a direct pointer to all doses and realized damage; equality of medians is not an equivalence test. |
| Fig. 2a-b, IV-A | Supports conditional rate decline and first-spike delay. Separate axes, Hz/ms units, healthy references and percentile captions are correct. A functioning-null comparison is unnecessary for this descriptive plot; input-drive and sensory-refractory sensitivity would establish broader transfer. |
| Table II, IV-B | Supports exact cohort dependence; all four rows reproduce. Add disagreement count or percentage to reduce mental arithmetic, without treating arbitrary cohort mixtures as fault incidence. Held-out healthy false-alarm validation is needed only for a predictive-budget claim. |
| Fig. 3a-b, IV-C/D | Illustrates one legacy trajectory and whole-versus-400-ms ratios; logarithmic activity scale is appropriate. Show individual whole-episode values as well as early-window points and add the late full-hub crossings. The +30-degree trajectory does not illustrate the six negative-direction exceedances. |

**Supplementary figures:** assessment_windows correctly displays pooled and three-seed medians, but its 200-500-ms range misses the late full-hub effect; extend that cohort to 1000 ms. revision_activity shows the two random-mass tail trials on a correctly labeled log scale. prospective_outcomes displays all directional counts and 400-ms pairs; promote it into the paper, retain six-seed denominators, and add shape coding so direction does not rely only on color.

**Supplementary tables:** The seven PROTOCOL_v3 tables cover cohorts, windows, legacy seed medians, prior-work positioning, fresh directional counts, fresh seed counts and paired activity windows. Their numeric measurement tables reproduce from the generators/records; the literature table is contextual, not an executed benchmark. Preserve three versus six cluster counts, and do not reinterpret exploratory ranges as calibrated coverage. The referenced complete-dose CSV supplies omitted main-sweep conditions.

### Related work gaps and bibliography

**Must cite for a novelty-dependent first claim:** No additional omission is demonstrated under the current narrow claim. An is already cited; the official abstract verifies overlapping perturbations, tasks, states and over-excitation. Do not reinstate the old broad novelty language. [An, bioRxiv, DOI 10.64898/2026.09.19.752860](https://doi.org/10.64898/2026.09.19.752860).

**Should cite:**

- **Jo, 2026, arXiv:2610.19153:** the abstract describes endpoint-dependent damage in another whole-connectome model. Present in refs.bib but absent from the compiled bibliography; discuss the different substrate and aims. [Official abstract](https://arxiv.org/abs/2610.19153).
- **Jang et al., JEB 2023, DOI 10.1242/jeb.244790:** bilateral integration and azimuthal invariance contextualize why this controller's directional asymmetry is a modeling issue rather than established fly behavior. Also present but uncited. Publisher access was blocked; the publisher-deposited abstract was checked. [DOI](https://doi.org/10.1242/jeb.244790).
- **Nijsink et al., 2026, arXiv:2605.00030:** optional engineering context distinguishing measured upset-rate/long-duration application testing from arbitrary software perturbations. It is not a matched baseline requirement. [Full text](https://arxiv.org/html/2605.00030v1).

Compiled references correctly use Brian2, published NeuroBench and Simpson's 2024 year. Legacy refs-full.bib remains stale but is not compiled; do not call its old errors current manuscript miscitations. This was a targeted literature/content check, not certification of every unused BibTeX entry.

### Additional actionable line edits

- methods.tex:26: Replace "midpoint of ... medians" with the actual calibration medians and formula, or cite their supplement location.
- methods.tex:35: Replace "All fixed windows precede termination" with "The latest selected window, 500 ms, precedes every included termination."
- results.tex:82: Change "misses task failures" to "does not flag these collision outcomes"; the criterion was not trained as a task-failure detector.
- principles.tex:8: State the measured -11.429-degree pre-cue heading, rather than only naming an offset.

## Phase 5 - Prioritized action plan

**BLOCKER - 3 actions**

1. Separate unequal stopping-time comparisons from early-horizon truncation, and show the 840-900-ms full-hub crossings with direction/calibration status.
2. Add frozen, paired pre-cue and bias-preserving steering controls on new seed clusters, without tuning to existing tests.
3. Put fresh directional outcomes and their controller equations into the four-page argument, explaining the assessment decision supported by the case study.

**SHOULD-FIX - 4 actions**

1. Report paired seed-level survival differences and horizon sensitivity, retaining active-burst metadata.
2. Test whether the sensory-refractory variant changes fault retention, beyond the current single 100-ms healthy pilot.
3. Preserve executable source snapshots for distinct generation hashes, and provide total campaign runtime/hardware details.
4. Provide reviewers the exact matching artifact and discuss the verified contextual literature.

**POLISH - 3 actions**

1. Add disagreement counts to Table II and left/right identities to Fig. 1.
2. Reduce numerical crowding in the abstract and distinguish both ratio estimands consistently.
3. Consolidate current-status documentation while retaining clearly labeled historical records.

**Resubmission decision:** This is now a credible, reproducible empirical case study, but I would not yet recommend acceptance as an ISCAS regular paper. B1 is repairable from existing data; B2 requires a focused control campaign; the main text must then expose the new evidence and its modest scope. Estimate **2-3 person-weeks**, plus measured compute time. A new hardware implementation or dynamical theory is not the minimum bar for this revised contribution.

Review evidence is saved in audit/review-assessment-v3/checks.json. The checked PDF SHA256 is 62ceea523fec9531dcb406b4f9eaa3791625cdf1e69ecb130f5d92056225aca7. This review recomputed summaries and inspected saved trajectories; it did not execute new neural simulations or modify the manuscript.

