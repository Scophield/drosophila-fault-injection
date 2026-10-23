# Assessment-v4 review — 21 October 2026

**Assumed venue: IEEE ISCAS 2027, regular paper, Neural Networks and Neuromorphic Engineering. Recommendation: 6/10, weak accept for a bounded empirical case study; confidence: 4/5.** These are reviewer-defined scores, not a recovered ISCAS review form. The principal numerical and controller-confounding problems identified previously are resolved. Acceptance now depends primarily on establishing the significance of the resulting narrow contribution.

## Phase 1 — Understanding the paper

1. **Problem.** How do cohort composition, observation duration, endpoint choice and controller assumptions change fault-assessment conclusions for the same fly-connectome spiking model?

2. **Claimed contributions, with my interpretation.**
   - “Cohort inclusion, observation horizon and controller assumptions change assessment” (`intro.tex:7`): quantify how classifications depend on selected conditions and evaluation semantics within one archive.
   - “Matching exposure between paired runs and selecting an earlier endpoint are distinct operations” (`intro.tex:7`): demonstrate a stopping-time artifact for deletion and a genuine late threshold crossing for equal-duration hub records. This is an empirical distinction, not a new mathematical estimand.
   - “Prospective tests freeze calibration on disjoint seeds, with controls for pre-cue turning and steering offset” (`intro.tex:7`): execute new whole-connectome tests showing limited directional behavior and dependence on complete feedback laws.

3. **Method, four sentences.** The paper instruments a 138,639-neuron signed leaky integrate-and-fire model with visual input and eight descending-neuron readouts. Five functional perturbation families alter weights, connection rows, random-unit outputs, hub outputs or sensory outputs. Archived records are rescored using transmission and a nested activity-constrained rule, with cohort exclusions and three paired spike-ratio definitions. New geometric closed-loop tests freeze passive calibration and compare deletion, readout removal and steering interventions on separate seed cohorts.

4. **Experimental setup.** One released connectome contains 15,091,983 connection rows representing approximately 54.5 million contacts. Main open-loop conditions use 12 trials, 600 ms and 150 Hz sensory drive; 288 fault/control records enter pooled scoring. Baselines include healthy, random drive, target-permuted anatomy and inhibitory controls; the nonfunctional null is correctly treated as a specificity control. Fresh calibration uses nine 400-ms episodes, seeds 0–2, bearings −60/−30/0°. The original test campaign uses seeds 6–11, ±30°, four conditions and a 1-s horizon; the new campaign uses seeds 12–17 and four healthy-network control laws, totaling 48 episodes each. Twelve additional 600-ms runs compare sensory refractory settings on three paired seeds. Metrics are command rate, first-spike latency, total spikes and bounded collision-free survival. Settings include 0.1-ms neural steps, 20-ms feedback frames, 100-ms cue onset and a 250-ms delayed, 450-ms burst. Bootstrap analyses use 20,000 draws; paired analyses retain bearings within seed clusters. No confirmatory significance test is claimed. The supplement records Xeon W-2223/NumPy execution: about 35.6 minutes elapsed for the new control campaign and 20.4 minutes for the refractory check; summed worker wall times are not CPU time.

5. **Reconstructed headline results.**

| Comparison | Result | Interpretation |
|---|---:|---|
| Pooled transmission / joint passes | 276/288 / 262/288 | Fourteen additional rejections |
| Exclude targeted hub cohorts | 192/204 / 190/204 | Only two disagreements remain |
| Main F1/F2/F3/F5 | 168/180 under either rule | No disagreement in this subset |
| Legacy 50% deletion, whole / common-duration ratio | 0.381701 / 0.729443 | Unequal stopping times matter |
| Legacy full hubs | Six crossings at 840–900 ms | Both records already last 1000 ms |
| Original held-out healthy / 25% / 50% deletion | 5/12 / 4/12 / 0/12 | Every +30° case fails |
| New original / gated / offset-only / no-steering | 4/12 / 6/12 / 0/12 / 0/12 | Six paired seed clusters |
| Gate-minus-original survival | +16.7 percentage points; interval 0–33.3 | Exploratory and conditional |
| Sensory refractory 2.2 / 0 ms | 76.3% / 79.2% paired deletion retention | Three-seed sensitivity, not equivalence |

6. **Stated limitations.** One connectome and selected drives; small conditional samples; missing historical hub manifests; unseeded historical input streams; compromised legacy geometry/calibration; assumed receptive fields; asymmetric calibration coverage; positive-bearing floor effects; active bursts at the horizon; no eventual-escape, hardware-energy, predictive-budget or broad reliability validation. Healthy-only steering controls do not measure fault tolerance under modified laws (`principles.tex:4–8`).

7. **Venue inference.** IEEEtran conference mode, IEEE bibliography, four technical pages plus references, neuromorphic fault-assessment scope and explicit project references to ISCAS 2027 strongly identify that venue. No cover or response letter was located. I read all six included section files, the bibliography and protocol supplements, inspected all five rendered pages, and checked the compiled template/version records.

## Phase 2 — Live venue standard and verification

Official sources accessed **21 October 2026**, with no displayed revision dates:

| Official source | Section names used | Application |
|---|---|---|
| [ISCAS 2027 call](https://2027.ieee-iscas.org/call-for-papers) | “Scope of Contributions”; “Types of Contributions”; “Call for Regular Papers” | Neuromorphic engineering is in scope; regular papers require original research advancing circuits and systems. |
| [Author Information](https://epapers2.org/iscas2027/ESR/authorinfo1.php) | “Important Deadlines”; “Paper Specifications” | Four technical pages plus optional references-only fifth; author information included; embedded fonts; no Type 3; PDF ≤5 MB. |
| [Samples and Templates](https://epapers2.org/iscas2027/ESR/samples.php) | “LaTeX Templates”; “Preparation of the bibliography in LaTeX” | IEEEtran conference mode and IEEEtran bibliography. |

I did not locate a public regular-paper scoring form. The call’s “Evaluation Criteria” applies to tutorials, so I do not misapply it. The rubric below supplements the official scope/author requirements. The submission portal gives October 22, 2026, 23:59 UTC−05:00; notification dates differ between official pages, so use the portal for operational deadlines.

**Verification boundary.** Recorded prospective, control, horizon and refractory summaries recompute exactly, including frozen calibration and generating-source checks. All 887 bundled files pass hash/size verification; the bundled PDF matches the reviewed PDF. All 88 validation-listed current sources remain unchanged. The saved 34-test pass remains applicable to those unchanged sources; I did not rerun neural simulations or reinstall the environment. The PDF is five US-Letter pages, 328,429 bytes, unencrypted, with references only on page five; saved font checks show no unembedded or Type 3 fonts.

## Phase 3 — Rubric table

Scores are out of 10 except confidence; theoretical depth is assessed relative to this empirical scope.

| Dimension | Score | Rationale | Concrete revision |
|---|---:|---|---|
| Overall | 6 | Credible, bounded observations now support the revised claims, but originality is modest. | Make the transferable contribution explicit in I and V. |
| Confidence | 4/5 | Sources, calculations, controls and rendered pages were checked; neural execution was not repeated. | Preserve this verification distinction in artifact documentation. |
| Novelty/originality | 5 | Endpoint/cohort sensitivity adds a specific case study beyond existing connectome perturbation work. | Add the explicit comparison proposed under B1, II. |
| Correctness/soundness | 7 | Equations and reconstructed headline results agree with code and records. | Make the trigger’s mixed smoothed/raw criterion explicit, III-E. |
| Theoretical depth | 5 | Definitions are correct; there is no theoretical contribution or proof requirement here. | State Eq. (3)’s descriptive scope; do not imply a new estimator. |
| Empirical strength | 6 | New paired controls help substantially, but six clusters and a directional floor limit inference. | Add discordant-pair counts and qualify the abstract’s gate comparison. |
| Reproducibility/release | 8 | Local manifest, source snapshots and raw records are unusually traceable. | Provide reviewers the matching release/supplement, I footnote. |
| Clarity/writing | 7 | Duration matching and horizon selection are now distinguished consistently. | Reduce competing numerical messages in the abstract. |
| Significance/audience | 5 | Useful assessment lesson, but its engineering consequence remains understated. | Add a concrete reporting procedure in V. |
| Ethics/safety | 8 | Hardware, biological resilience and safety claims are appropriately bounded. | Keep these boundaries adjacent to any reliability language, V. |
| SOTA/related work | 7 | Close connectome and injector work is acknowledged without unsupported superiority. | Explain the precise additional question beyond An and Jo, II. |
| Figures/tables | 8 | Main panels are readable; Fig. 3 preserves all late crossings. | Label supplementary symbols/units explicitly; see figure audit. |
| Bibliography | 7 | Seventeen compiled citations resolve and recent close work is included. | Normalize identifiers and complete article metadata where available, refs [6–8]. |

## Phase 4 — Detailed findings

### Blocker issues and remaining rejection risks

**No reproduced fatal numerical or implementation error remains in the current claim set.** The following are the two acceptance-critical risks, rather than demands to reopen withdrawn claims.

**B1. The original contribution must be more explicit than “assessment depends on assessment choices.”** Location: I final paragraph (`intro.tex:7`), II first paragraph (`related.tex:2`), V conclusion. The statement “Our contribution concerns assessment sensitivity within one declared model and cohort” is accurate but may sound like bookkeeping. Existing work already varies perturbations, states, tasks and functional endpoints. A reviewer could accept every number yet reject the significance.

**Fix:** replace the generic contribution sentence with: “We quantify three distinct changes in assessment: cohort exclusions remove 12 of 14 additional activity rejections; stopping-time matching changes deletion spike ratios; and fixed-horizon analysis retains late hub exceedances. Paired controller interventions then identify which behavioral interpretations depend on the chosen feedback law.” Close V with an operational instruction: report the cohort denominator, paired exposure rule, full-horizon activity trace and direction-specific task outcome. A new hardware implementation or theorem is unnecessary for this contribution.

**B2. The evidence essential to evaluation is packaged locally but not yet available through the manuscript’s repository link.** Location: I footnote; `PROTOCOL_v4.md`; III-B/IV-C references to complete doses and damage. The footnote honestly says the local revision is unpublished. Nevertheless, remote reviewers cannot inspect a local ZIP unless it is supplied, and much of the experimental detail lives outside the five-page paper.

**Fix:** attach the exact assessment-v4 supplement/release through the submission’s permitted mechanism, or provide a stable accessible version before claiming availability. Give one current index separating archived observations, new controls and reproduction commands. This is an evidence-access risk, not an asserted ISCAS mandate to publish code. If the matching supplement accompanies submission, B2 is resolved.

### Section-by-section feedback and concrete edits

**Abstract (`main.tex:42`).** It reports all three assessment effects and the new controls; the unequal-duration versus late-crossing distinction is particularly effective. However, many numbers compete with the central message, and “gating pre-cue steering changes … 4/12 to 6/12” lacks the uncertainty and directional floor shown later. Replace that sentence with: “Pre-cue gating yielded 6/12 collision-free episodes versus 4/12 for the original law; the six-cluster interval included zero difference, and every positive-bearing test failed.” Retain the final scope statement.

**Introduction (I, `intro.tex:3–7`).** The opening separates transmission, activity and behavior, and correctly treats anatomy as a structural prior. The final paragraph lists evaluation operations without sufficiently stating what another researcher should do differently. Insert B1’s concrete contributions and reporting consequence; shorten the preceding generic model description to make room.

**Related work (II, `related.tex:2–4`).** An, Jo, injector frameworks and benchmarking references cover the nearest motivations. The section appropriately avoids claiming a new injector. Add: “Those studies investigate how damage or sparsification changes function; our comparison additionally holds archived observations fixed while changing the cohort and exposure definitions used to classify them.” Do not characterize prior work as ignoring endpoints without evidence.

**Method (III-A–E, `methods.tex:3–51`).** Units, perturbation semantics, selection defects and explicit steering parameters make the implementation inspectable. The key weakness is dense interleaving of historical and fresh protocols. Add a compact campaign cross-reference, and replace the trigger prose with: “Triggering requires both the current five-frame mean and the preceding unsmoothed frame rate to meet or exceed 18.125 Hz.” Explain that this is not two consecutive smoothed crossings. Add compute requirements to III-E in one sentence, referring to the detailed supplement.

**Experiments/results (IV-A–F).** Leading with prospective failures is appropriate, Table I addresses the old confound, and Fig. 3 restores late activity. The gate contrast changes only two seed clusters, while all +30° cases remain at floor. Add “two improving, zero worsening and four unchanged seed clusters” after the interval (`controller_results.tex:17`). Describe the interval explicitly as a conditional 95% percentile bootstrap range. Separate the seeds 6–11 “original campaign” from the seeds 12–17 “original control law” wherever “original” could refer to either. Keep the statement that altered-law fault tolerance is unmeasured.

**Discussion and conclusion (V, `principles.tex:2–8`).** The discussion now preserves the one-second warning and separates low activity from survival. Its limitations are specific, including active bursts and uncertain historical selection. Replace its last generic sentence with: “These records support reporting transmission, activity and bounded task outcome separately, with explicit cohort membership and exposure, rather than interpreting one pass fraction as reliability.” Avoid extrapolating this reporting lesson into a validated safety procedure.

**Appendix/supplements (`PROTOCOL_v2–v4.md`).** Complete dose, calibration-partition, cohort, window, seed, controller and refractory tables preserve important evidence; there are no hidden proofs. Version supersession statements are present, but readers must navigate three documents. Create a current table/figure index and label older status statements as historical. In the dose tables, distinguish ratio-of-medians from median-of-paired-ratios; in partition tables, distinguish exact log reuse from shared seeds; in three-/six-cluster tables, keep uncertainty explicitly descriptive. These are presentation fixes, not grounds to discard the data.

### Equations and proofs

- **Eq. (1), III-A:** dimensionally consistent voltage equations. Between events outside refractoriness, for initial values v and g, g(t)=g exp(−t/5 ms) and v(t)−v0=(v−v0)exp(−t/20 ms)+(g/3)[exp(−t/20 ms)−exp(−t/5 ms)]. This agrees with linear integration. Threshold, reset, drive jumps and refractory pausing must accompany the equations, as they do here.
- **F1, III-B:** E[exp(σZ−σ²/2)]=1; CV=sqrt(exp(σ²)−1)=0.53294 at σ=0.5. The stated 53.3% is correct.
- **Eq. (2), III-C:** the midpoint is 51.40625 Hz, correctly rounded to 51.4. Joint-pass containment is definitional; Table II measures its empirical consequences, not detector accuracy.
- **Eq. (3), III-D:** all three ratios are correct. Equal durations imply whole=common pairwise, as verified for hubs. Even a common duration can depend on fault-induced stopping; it is a declared estimand, not an unbiased resource-cost estimate.
- **Eq. (4), III-E:** zero readout gives −400(20/70)=−114.286°/s and −11.429° over 100 ms, agreeing with logs. No derivation or appendix proof is missing. Interventions preserve the trigger rule, not trigger times or sensory trajectories.

### Every main figure and table

| Item | Claim and design assessment | Required reporting/visual edit |
|---|---|---|
| Fig. 1, III-A | Supports anatomical instrumentation; 90 selected relays cannot establish a dynamical mechanism. Caption correctly says so. | State explicitly that relay selection is for display; retain source hashes and identity mapping. No significance test is applicable. |
| Fig. 2a–b, IV-A | Directional counts and all 400-ms activity pairs support coexistence of low relative activity and collision. Healthy +30° failure prevents estimating a deletion effect there. | Retain n=6 clusters, direction markers and seed configuration. Simplify log ticks near one; do not fit a detector or add iid error bars. |
| Table I, IV-B | Healthy-only paired interventions establish dependence on complete control laws, not an isolated biological steering mechanism. | Include the two-improved/four-unchanged pairing summary and conditional interval level; preserve burst-active counts. No new fault matrix is required for the stated healthy-only claim. |
| Table II, IV-D | Reconstructed counts are correct; removal of entire conditions changes the denominator by design. | Spell out EIm in the caption/index and identify the two random-mass outliers. Avoid population-failure confidence intervals for this chosen mixture. |
| Fig. 3, IV-F | All 12 equal-duration traces support genuine late crossings; units, calibration labels and crosses are legible. | Explain that markers encode bearing while three same-bearing traces are seeds; retain the complete 1-s horizon. A pooled median below two does not negate six individual exceedances. |

**Supplementary figure audit.** `revision_curves`: rate/latency dose response is readable; supply n=12 and define bars as 10th–90th percentiles. `revision_activity` (the supplied image): log scale and thousands-of-spikes units are correct; label horizontal segments as medians and distinguish the operational threshold from a resource budget. `revision_demo`: the single separation trace is illustrative; rename “Matched-exposure activity” to “Whole-episode versus fixed-window activity” to avoid reviving the corrected duration/horizon conflation. `assessment_windows`: useful pooled/seed views, but label its 500-ms endpoint as an early-window diagnostic and point to Fig. 3. `estimands`: correctly shows whole=common only for equal-duration hubs; add a legend for bearing markers, calibration status and the black pooled median. `paired_controls`: shows every seed and conditional range; emphasize that six, not twelve, is the independent cluster count. Repeated `prospective_outcomes` and `late_hubs` exports inherit the main-figure findings. All are traceable through saved data and plot manifests; none supplies population-level generalization.

### Related-work gaps and bibliography

**Must cite for novelty:** no newly established omission. The closest works are already cited: An, bioRxiv DOI [10.64898/2026.09.19.752860](https://doi.org/10.64898/2026.09.19.752860), and Jo, [arXiv:2610.19153](https://arxiv.org/abs/2610.19153). An’s author repository confirms multi-operator, multi-task and network-state comparisons; Jo’s official abstract confirms endpoint- and damage-dependent responses. Strengthen the distinction, not the citation count. The bioRxiv full-text endpoint was unavailable, so I do not attribute unverified detailed arguments to it; the accessible [author repository](https://github.com/aikian/flylite) supports the comparison above.

**Should cite for optional hardware context:** Nijsink et al., *Shooting Neutrons at Neurons*, [arXiv:2605.00030](https://arxiv.org/abs/2605.00030), 2026, connects neutron measurements to a calibrated fault model and application failure. It would illustrate what additional evidence a hardware claim needs; it is not a mandatory baseline for this software case study.

Selected registry checks confirm Jang DOI 10.1242/jeb.244790, SpikingJET DOI 10.1109/IOLTS60994.2024.10616060, SpikeFI arXiv:2412.06795 and NeuroBench DOI 10.1038/s41467-025-56739-4. Complete article identifiers where available; preserve “SpikeFI” capitalization. NeuroBench correctly renders as 2025 despite its older internal citation key. Seventeen resolved citations do not by themselves constitute a complete claim-level citation audit.

### Additional actionable line edits

- `results.tex:21`: replace “Reference-aware retention … was 75.1–79.0%” with “The 95% bootstrap interval for the ratio of median command rates was 75.1–79.0%.”
- `results.tex:23`: retain “median paired … retention” to distinguish the new statistic from the historical ratio of medians.
- `results.tex:3`: replace “failed behaviorally” in cross-references with “collided before the 1-s horizon.”
- `controller_results.tex:17`: retain “under these settings”; do not shorten it into a universal necessity claim about neural steering.
- `main.tex:46`: consider “fault assessment” instead of “fault tolerance,” matching the actual contribution.

## Phase 5 — Prioritized plan and resubmission decision

**BLOCKER / acceptance-critical: 2 items**

1. **State** the three concrete empirical contributions and their engineering reporting consequence in I, II and V (B1).
2. **Supply** the exact current supplement/artifact to reviewers through an allowed access mechanism (B2; conditional on submission packaging).

**SHOULD-FIX: 5 items**

1. **Qualify** the abstract’s gating result with the zero-inclusive range and directional floor.
2. **Report** the six paired seed outcomes and label conditional bootstrap intervals precisely.
3. **Clarify** the mixed smoothed/raw neural trigger and campaign naming.
4. **Index** all current supplemental tables/figures and distinguish historical from current status statements.
5. **Relabel** supplementary duration/window comparisons and explain their plotting symbols.

**POLISH: 3 items**

1. **Normalize** bibliography capitalization and article identifiers.
2. **Simplify** Fig. 2b ticks and spell out Table II abbreviations.
3. **Align** keywords and conclusion wording with fault assessment rather than established tolerance.

**Decision.** This version is close to a defensible ISCAS submission as a narrow empirical assessment study. The minimum revision is clearer originality, accessible supporting evidence and tighter uncertainty/reporting; a new connectome, theorem, hardware campaign or reliable bilateral controller is not required for the current claims. I estimate **0.3–0.7 person-weeks** for these revisions and final verification. If the authors instead want to claim that gating improves performance generally, or that a joint rule predicts resource failure, they need a separately designed, adequately sized held-out experiment; the current six-cluster contrasts cannot support that stronger paper. Venue acceptance remains uncertain because significance, rather than reproduced correctness, is now the principal judgment call.
