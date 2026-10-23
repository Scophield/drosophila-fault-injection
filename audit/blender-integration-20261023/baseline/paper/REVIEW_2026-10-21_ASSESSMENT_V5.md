# Manuscript Review: assessment-v5

**Assumed venue: IEEE ISCAS 2027, regular-paper standard, Neural Networks and Neuromorphic Engineering. Recommendation: 6/10, weak accept on scientific merit, conditional on submission preparation. Confidence: 4/5.**

The paper now presents a defensible, bounded assessment case study. The contribution is quantified sensitivity to cohort composition, observation duration and feedback laws, rather than a new fault injector or general fly-brain robustness result. I find no remaining scientific blocker for that claim. Two submission issues remain: interactive PDF features conflict with the portal's help instructions, and reviewers need access to this exact revision. Neither requires another experiment campaign.

## Phase 1 - Understand the Paper

I read main.tex, every included section (including controller_results.tex), both bibliographies, IEEEtran configuration, the complete 11-page supplement and relevant implementation/analysis files. No cover letter, response letter or separate manuscript appendix was found. Locations below use files in paper/sections/ unless otherwise stated.

1. **Problem.** How do cohort membership, stopping-time matching, observation horizons and controller assumptions change fault assessments in a fixed fly-connectome spiking model?

2. **Contributions: author wording and interpretation** (intro.tex:7).

   - "cohort exclusions remove 12 of 14 additional activity rejections": a decomposition of a pooled scoring difference, not evidence of a superior detector.
   - "stopping-time matching changes deletion spike ratios": a reproducible exposure correction for fault/healthy episodes that terminate at different times.
   - "full-horizon analysis retains late hub exceedances": an important distinction between matching duration and discarding later activity.
   - "Paired controller interventions with frozen calibration": new evidence about complete feedback laws, conditional on six seeds, two bearings and one-second survival.

3. **Method.** A signed LIF network uses 138,639 neurons and 15,091,983 connection-table rows representing approximately 54.5 million contacts. Five perturbation families alter weights, connection rows or neuronal outputs; eight descending neurons provide command-rate and first-spike readouts. Archived records are re-scored under transmission and operational activity constraints, then paired under whole-episode, common-duration and fixed-horizon estimands. New geometric simulations use passive calibration, disjoint test seeds and controller interventions that retain the neural burst-trigger rule.

4. **Setup.** The substrate is one FlyWire-v783 connectome, with 104 LC4 and 210 LPLC2 inputs and eight DNp01/DNa02/DNp04/DNb01 readouts. The main archive has 19 conditions including healthy, 12 trials each, 600 ms and principally 150-Hz Poisson drive. Doses are lognormal sigma 0.05/0.10/0.20/0.50; row deletion 5/10/25/50%; random output silencing 1/2/5/10%; hub output silencing 1/2/5%; and either/both sensory channels. Controls include random drive, target permutation, sign/composition lesions and random inhibitory lesions.

   Membrane/synaptic constants are 20/5 ms; threshold/reset -45/-52 mV; recurrent contact gain 0.275 mV; delay 1.8 ms; refractory interval 2.2 ms; external voltage jump 68.75 mV. Fresh integration is 0.1 ms with 20-ms feedback. Nine passive calibration episodes use seeds 0-2 and bearings -60/-30/0 degrees. The first 48 tests use seeds 6-11, +/-30 degrees and four conditions; another 48 healthy-network controls use seeds 12-17 and four laws. Twelve additional 600-ms runs compare sensory refractory settings on three paired seeds.

   Outcomes are transmission, activity ratios, collision-free survival at one second, trigger counts and burst status. Thresholds are 51.4 Hz open-loop and 18.125 Hz for the frozen demo trigger. Median intervals use 20,000 bootstrap resamples; behavioral contrasts preserve seed clusters and are explicitly exploratory. No confirmatory significance/equivalence claim is made. The paired controls took 35.6 minutes with three workers on a Xeon W-2223, approximately 1.1 GB per process; Table S16 distinguishes elapsed and summed episode wall times. Historical total compute and timestep remain unavailable.

5. **Headline results, reconstructed from the records.**

| Assessment | Result | Interpretation |
|---|---|---|
| All 288 fault/control records | 276 transmission; 262 joint passes | Fourteen extra operational rejections |
| Exclude targeted hub cohorts | 192 versus 190 of 204 | Two random-mass tail records remain |
| Main F1/F2/F3/F5 cohort | 168 versus 168 of 180 | No scoring disagreement |
| Legacy 50% deletion | Median whole/common ratio 0.3817/0.7294 | Unequal exposure materially changes the ratio |
| Equal-duration legacy full hubs | Six first twofold crossings at 840-900 ms | Earlier horizons omit genuine late activity |
| First prospective campaign | Healthy 5/12; 25% deletion 4/12; 50% deletion/readout-off 0/12 | Every positive-bearing test collides |
| New-seed original/gated laws | 4/12 versus 6/12 | +16.7 pp; conditional range 0.0-33.3 pp |
| Offset-only/no steering | Both 0/12, despite 11/12 and 12/12 triggers | Triggering alone is insufficient under these settings |

6. **Limitations.** One model, selected drives, assumed receptive fields, asymmetric calibration coverage, small seed samples, positive-direction floor effects and bounded survival. Legacy calibration reuse, missing hub manifests, unseeded historical stimulus streams and incomplete older source snapshots limit interpretation. The paper appropriately excludes hardware protection, biological escape, predictive resource-budget and population-reliability conclusions.

## Phase 2 - Recover the Standard

ISCAS 2027 is supported by the project context, IEEEtran conference template, identified author and four technical pages. The official topic list includes spiking neural networks; a specific special session is not established.

Official documents accessed **21 October 2026**; no page-specific revision dates are displayed:

| Source and sections used | Relevant standard |
|---|---|
| [2027 CFP](https://2027.ieee-iscas.org/call-for-papers): "Scope of Contributions", "Types of Contributions" | Original circuits-and-systems research; neuromorphic engineering is in scope. |
| [Author Information](https://epapers2.org/iscas2027/ESR/authorinfo1.php): "Paper Specifications" | Four technical pages, optional references-only fifth page, named authors, embedded fonts, no Type 3, no encryption, maximum 5 MB. |
| [Templates](https://epapers2.org/iscas2027/ESR/samples.php): "LaTeX Templates", "Preparation of the bibliography in LaTeX" | IEEEtran conference class and bibliography style. |
| [PDF Help](https://epapers2.org/iscas2027/ESR/author_help.php): "Author Help with PDF Files" | No bookmarks, form fields, hyperlinks or page numbering; PDF 1.4 or later. |

No public regular-paper scoring form/native scale was found; tutorial criteria are inapplicable. Scores below use a reviewer-defined 1-10 scale. The portal lists the deadline as **22 October 2026, 23:59 UTC-05:00**.

The main PDF passes pagination, size, font and security checks: five Letter pages, references only on page five, 327,711 bytes, 24 embedded fonts, zero Type 3, PDF 1.5, no forms/encryption. It nevertheless contains **41 link annotations and 17 bookmarks**, contrary to PDF Help. Earlier font/page validation did not test this requirement.

## Phase 3 - Rubric Table

Higher is better; confidence alone uses 1-5. Low theoretical novelty does not imply that this empirical paper needs a theorem.

| Dimension | Score | Rationale | Concrete fix/location |
|---|---:|---|---|
| Overall | 6/10, weak accept | A reproducible, bounded assessment result now survives scrutiny. | Resolve submission items B1-B2. |
| Confidence | 4/5 | Records, equations, PDFs and artifact were inspected; no new neural replay was performed. | Preserve exact campaign provenance; supplement Sec. 11. |
| Novelty/originality | 6/10 | Quantified cohort/horizon dependence is the advance; components are inherited. | Keep this distinction explicit; intro.tex:7. |
| Technical soundness | 8/10 | Estimands and controls support the stated conditional conclusions. | Correct state-restoration wording; methods.tex:9. |
| Theoretical depth | 5/10 | Definitions are sound but supply no general robustness result. | Retain empirical scope; Eqs. (1)-(4). |
| Empirical strength | 6/10 | New frozen-calibration controls help; six clusters and directional failure limit transfer. | Avoid improvement/general-reliability language; Table I. |
| Reproducibility | 8/10 | Matching raw data, snapshots and reconstruction scripts are supplied locally. | Deliver this revision through a permitted route; supplement Sec. 11. |
| Clarity/writing | 8/10 | Exposure correction and horizon selection are now clearly separated. | Tighten minor terminology; Secs. III-A/IV-C. |
| Significance/impact | 6/10 | Useful evaluation lessons for neuromorphic assessors; scope remains one case. | Preserve the concrete reporting procedure; Sec. V. |
| Ethics/broader impact | 9/10 | Attribution and limits prevent unsupported biological/safety advice. | Retain these boundaries; Sec. V. |
| SOTA/related work | 7/10 | Close connectome and assessment work is acknowledged without a false superiority claim. | Retain the explicit distinction from An/Jo; Sec. II. |
| Figures/tables | 8/10 | Units, individual pairs, directions and dispersion are legible. | Improve cross-references and redundant precision; Tables S6/S15. |
| Bibliography | 9/10 | All 17 active identifiers resolve; targeted metadata checks agree. | Keep historical refs-full.bib distinct from compiled refs.bib. |

## Phase 4 - Detailed Findings

### Blocker Issues

**B1. Submission PDF features conflict with official PDF Help.** Location: main.tex:12 and the exported main.pdf. Hidden link styling does not remove clickable annotations or outlines. This can impede compliance even though typography passes. **Fix:** disable PDF hyperlinks/bookmarks in the submission build while retaining printable URLs, rebuild, and verify zero link annotations and outlines. Keep a separate interactive reading copy if desired. The main paper has no page numbers; the numbered supplement is a separate supporting document whose permitted format must be established.

**B2. The exact review package is still local.** Location: intro.tex:7 footnote; REVIEW_MATERIALS.md:14; supplement Sec. 11. The supplement states: "The repository link in the paper alone does not expose this revision." The disclosure is honest, but that URL cannot deliver the current evidence. **Fix:** supply the current supplement and matching artifact through a mechanism actually permitted by the venue, then test retrieval and identity. Do not assume that an arbitrary ZIP or an 11-page technical supplement is accepted. This is a submission-readiness condition, not evidence fabrication or a mandatory public-release policy.

**No additional scientific blocker is established.** The modest contribution and limited generality remain acceptance risks, but current claims acknowledge both. In controller_results.tex:17: "The range includes zero difference, and every positive-bearing test collided." The complete-law comparison does not isolate trigger timing; the paper now says so. More seeds, balanced calibration or hardware execution would strengthen a broader paper, but are not prerequisites for the present descriptive claim.

### Section-by-Section Feedback

| Section | Summary, specific strength, weakness and suggested edit |
|---|---|
| Abstract, main.tex:42 | Quantifies cohort, duration and controller effects and states the zero-inclusive range. Its dense sequence of results can obscure the contribution. Replace the final synthesis with: "This case study shows why cohort composition, paired exposure and full-horizon activity must accompany transmission and task outcomes." Retain the scope caveat. |
| Introduction, intro.tex:3-7 | Connects separate endpoints to assessment decisions and identifies the actual novelty. This resolves the earlier vague contribution. Add no new priority claim; shorten repeated resource-budget caveats if space is needed. |
| Related Work, related.tex:2-4 | Separates An/Jo's functional perturbation studies from assessment-definition changes and credits existing injectors. The comparison is now sufficient; retain the statement that no new perturbation operator is introduced. |
| Method, Sec. III | Specifies units, protected outputs, seeds, estimands and the actual trigger rule. Correct the conflation of integration and state restoration at methods.tex:9: "Linear integration advances the dynamics; stored initial states are restored before each trial." |
| Experiments, Sec. IV | Distinguishes two campaigns and exposes the positive-bearing floor. The phrase "every dose, realized damage" can imply more archived metadata than exist. Write: "The supplement supplies every main dose, recorded control damage and selected-dose intervals." |
| Discussion, principles.tex:2-6 | Preserves late warnings and explains why low activity cannot certify task success. Replace "The one-second warning remains valid" with "The six recorded one-second exceedances remain after duration matching." |
| Conclusion, principles.tex:8 | Gives a usable reporting procedure rather than hardware advice. Retain this endpoint and avoid a concluding generic claim of reliable control. |
| Appendix/supplement | No formal appendix; the consolidated supplement is a readable current entry point, with all seed outcomes. Replace vague references to selector reconstructions in results.tex:26 with their exact artifact location, audit/verified-hubs, rather than implying Table S4 contains reconstructed identities. |

### Equations and Proofs

**Eq. (1)** agrees with the inspected wrappers, including voltage-valued drive and refractory pauses. Outside events/refractoriness, its solution is

\[
g(t)=g_0e^{-t/5},\qquad
v(t)-v_0=(v(0)-v_0)e^{-t/20}
+\frac{g_0}{3}(e^{-t/20}-e^{-t/5}),
\]

with t in milliseconds. Both modes decay; this is not a whole-network stability proof. Sensory refractoriness differs from upstream stimulation, is disclosed and is tested in Table S15.

**Eq. (2)** is dimensionally consistent. Joint passes necessarily form a subset of transmission passes; the manuscript correctly avoids treating disagreement as predictive accuracy. Independent calibration of an energy budget would be required only to make that stronger claim.

**Eq. (3)** correctly separates whole/common/fixed-horizon ratios. Common stopping times can themselves depend on faults, so matching exposure does not identify a causal activity effect; supplement Sec. 2 explicitly states this. Zero-reference ratios require exclusion/reporting, not arbitrary finite replacement.

**Eq. (4)** produces -114.286 degrees/s at zero readout and thus -11.429 degrees over the 100-ms pre-cue period. This matches the logs. The implemented trigger uses current smoothed and preceding raw rate, as now described. F1's coefficient of variation is sqrt(exp(sigma^2)-1), or 53.3% at sigma=0.5. The gate contrast reproduces +16.7 pp with conditional range [0.0,33.3]. No theorem or appendix proof is claimed or missing.

### Every Main Figure and Table

All are legible at the saved page size; captions distinguish sample size, endpoint and uncertainty. Reconstructed counts/ratios agree with the supplied records.

| Item | Intended claim, design support and remaining action |
|---|---|
| Fig. 1 | Shows mapped wiring/injection sites, not a causal computation. The 90/849 relay display rule and contact encoding are stated; no statistical bars are needed. Keep input/generator hashes. |
| Fig. 2a-b | Shows direction-specific first-campaign survival and every 400-ms activity pair. Counts, log ratio axis, Hz-free ratios and six shared seeds are appropriate. This is a conditional counterexample to activity-based certification, not a calibrated detector comparison. |
| Table I | Compares healthy-network feedback laws on new paired seeds. B explicitly marks surviving bursts; text reports triggers separately. Retain the zero-inclusive interval and do not infer deletion tolerance under gated control. |
| Table II | Demonstrates cohort dependence, with explicit denominators and whole-condition exclusions. The two tail records are identified; the mixed cohort cannot estimate a population failure rate. No significance test is required for counting fixed records. |
| Fig. 3 | Supports six late crossings in equal-duration records. All traces, calibration bearings, crossings and units are shown. Fresh matched hub reruns are needed only for renewed hub-causality claims. |

### Every Supplementary Table

Each table is readable, has units or count denominators, and identifies its campaign. The remaining requirements concern interpretation or traceability, not missing generic error bars.

| Item | Evidence and audit |
|---|---|
| S1 | Campaign/sample index; distinguishes neural runs from deterministic feasibility tests. No pooled independence claim. |
| S2 | Every archived dose; rate intervals, latency and spikes. Historical F4 remains descriptive; F1/F3 are not equivalence tests. |
| S3 | Repeats main cohort counts consistently; fixed-record decomposition, not prevalence. |
| S4 | Recorded damage and control medians; missing cell counts are dashes. Contact-mass matching is not realized row equality. |
| S5 | Separates exact calibration reuse from shared seeds; correctly rejects independent-test interpretation of 18/18. |
| S6 | Whole/common/400-ms paired medians reproduce. Add Eq. (3) cross-reference; reduce excessive precision consistently. |
| S7 | Full-hub horizons preserve all pairs; late exceedances are not a duration correction. |
| S8 | Every first crossing is shown; no-crossing scenarios remain explicit. |
| S9 | First prospective counts and burst status agree with raw episodes; positive-direction floor is visible. |
| S10 | Every seed is supplied; paired units are identifiable. |
| S11 | Deletion ratios at four common windows reproduce; no fitted failure detector is implied. |
| S12 | New-seed control/trigger counts reproduce; same rule does not mean identical trigger timing. |
| S13 | All paired binary outcomes supplied, preventing independence inflation. |
| S14 | Exploratory six-cluster ranges and improved/worse/same counts agree; retain coverage caveat. |
| S15 | Paired refractory retention is correctly distinguished from ratios of group medians. Three seeds do not show invariance. |
| S16 | Measured compute separates elapsed and summed episode times; total historical campaign cost remains unknown. |

### Every Supplementary Figure

| Item | Claim and remaining action |
|---|---|
| S1 | Repeats main Fig. 2 consistently, with every activity pair and no unsupported population interval. |
| S2 | Exposes every controller seed and conditional differences; zero is visible in the gate range. Keep pairing. |
| S3 | Visually distinguishes unequal stopping times from earlier horizons; every paired line and median is retained. |
| S4 | Archived rate/latency curves have correct Hz/ms labels and percentile bars; no drive-invariance claim follows. |
| S5 | Logarithmic spike counts in thousands preserve both random-mass tail trials. Twofold line is explicitly operational. |
| S6 | Legacy separation is identified as one illustrative trace; whole/400-ms comparisons do not validate corrected geometry. |
| S7 | All early-window pairs/seed medians are shown; caption correctly points to main Fig. 3 for late crossings. |

More bootstrap draws cannot replace three or six independent seed clusters. The paper now communicates this, supplies individual outcomes and avoids confirmatory significance claims. A larger campaign is optional strengthening, not a repair to a hidden statistical assertion.

### Related Work Gaps and Bibliography

**Must cite:** no omitted work was verified that invalidates the narrowed novelty. An is already cited, DOI [10.64898/2026.09.19.752860](https://api.biorxiv.org/details/biorxiv/10.64898/2026.09.19.752860); its official abstract describes matched sparsification budgets, task/state dependence and over-excitation. Jo is already cited, [arXiv:2610.19153](https://arxiv.org/abs/2610.19153); its abstract includes contact-loss matching and different activity/function sensitivity. These precedents make broad claims about first endpoint-aware robustness untenable; the present text avoids them. My comparison uses their official abstracts, not a purported full-text replication audit.

**Optional context:** Nijsink et al., *Shooting Neutrons at Neurons*, [arXiv:2605.00030](https://arxiv.org/html/2605.00030v1), links measured FPGA radiation faults to application metrics. It would help if hardware framing is expanded, but is not mandatory for this software assessment study. It is not an interchangeable connectome baseline.

All 17 active DOI/arXiv identifiers resolved through registries; title/year/venue spot checks, including Jang, Gleyo and Simpson, agree. No substantive current mis-citation was verified. Preserve preprint labeling and use refs.bib as the authoritative compiled source; stale historical entries in unused refs-full.bib are not current citation errors.

## Phase 5 - Prioritized Action Plan

**BLOCKER - 2 submission items**

1. Generate a submission PDF without link annotations or bookmarks and extend QA to check both explicitly.
2. Supply the exact current supplement/artifact through an allowed mechanism and verify reviewer retrieval and PDF identity.

**SHOULD-FIX - 3 items**

1. Correct integration/state-restoration wording in methods.tex:9.
2. Replace the supplement's implied selector-identity location with the precise artifact path in results.tex:26.
3. Retain the zero-inclusive range, six seed clusters and complete-law scope in every abstract/result summary.

**POLISH - 3 items**

1. Shorten the abstract's synthesis while preserving its quantitative limits.
2. Cross-reference exposure definitions and standardize decimal precision in supplementary tables.
3. Name the observed one-second exceedances explicitly instead of using a generic warning phrase.

**Decision:** Close enough to submit after these focused fixes, with weak-accept scientific support and a real risk of rejection for modest novelty. No new experiment or theorem is required to support the current bounded claims. Balanced calibration, more independent seeds and testing faults under altered control laws would support a future broader contribution. Estimate **0.2-0.5 person-weeks** for preparation/editing, excluding venue response or external publication arrangements.

Verification: independently reconstructed calibration, prospective/control/horizon/refractory summaries and cohort counts; checked 449 raw-input hashes, 92 validated source files and all 898 manifest-listed bundle files; inspected all five main and eleven supplementary pages, whose renders match the current PDFs. The existing 34-test pass concerns unchanged sources and was not rerun. No manuscript edits, new neural simulations, upload or submission were performed. Audit: audit/review-assessment-v5/checks.json.
