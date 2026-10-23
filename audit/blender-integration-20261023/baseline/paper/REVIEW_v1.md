# PAPERGURU PAPER REVIEW

**Manuscript:** *How Much Fault Tolerance Is in a Fly Brain? Fault-Injection Analysis of a Whole-Connectome Spiking Controller for Physical Intelligence* (paper/main.pdf, 6 pages: 5 content + 1 references-only)
**Author:** Shuchao Gao, Waseda University
**Review date:** 2026-10-14. **Live venue lookup:** ENABLED (all URLs verified live on this date).

---

## 1. Phase 1 — Understanding the Paper

### 1.1 Problem and motivation

Complete synaptic wiring diagrams (FlyWire adult *Drosophila*) now exist, and point-neuron models built on them run without training. Several 2025–2026 works drive such models as controllers (visual prediction, cognitive tasks, whole-body locomotion). The paper argues that **none of these works varies the integrity of the controller** — they vary inputs, tasks, or training — so the fault tolerance of a biologically exact spiking controller is unmeasured, while neuromorphic hardware needs exactly this quantity before deployment on degrading substrates.

### 1.2 Claimed contributions

1. A fault-injection framework mapping five hardware fault classes (weight noise, interconnect loss, dead units, dead hubs, dead sensors) onto a 138,639-neuron / 15.1M-synapse LIF whole-brain controller.
2. "First behavioral-grade tolerance curves of a complete connectome" (hedged *to our knowledge*): 36 conditions (18 fault doses × 2 graphs) × 12 seeded trials = 432 trials, scored as command-population firing rate against a calibrated threshold θ = 51.4 Hz.
3. A decomposition (ER null + analytic pathway mass ‖A^k‖₁) showing that linear graph redundancy explains neither specificity nor graceful degradation; threshold amplification on convergent wiring converts exponential topological decay (5.8% 4-hop mass retention at 50% edge loss) into graceful functional decay (76% behavioral retention).
4. Five design principles (Table II, P1–P5) with quantitative anchors, plus the headline anomaly: top-1% hub loss produces a **2.5× activity runaway** rather than silence.

### 1.3 Experimental setup (as stated)

Released Brian2 LIF model re-implemented with state restore per trial (identical initial state and background realizations across conditions); 600 ms trials, ~3.5 s/core; escape pathway LC4 (104) ∪ LPLC2 (210) driven at 150 Hz Poisson; readout = population rate of {DNp01, DNa02, DNp04, DNb01} over last 500 ms; secondary readout all 1,299 descending neurons; SHA-256-derived deterministic seeds. Controls: (a) ER null by postsynaptic-endpoint permutation preserving out-degree, weight, and sign; (b) analytic multi-hop pathway mass on input→command submatrices.

### 1.4 Results table (reconstructed from text)

| Fault | Dose | Command rate (Hz) | Retention | Notes |
|---|---|---|---|---|
| — healthy | — | 94.7 (94.0–95.6) | 100% | latency 4.05 ms; 39.7k spikes |
| F1 weight noise | σ=0.5 | 94.7 | 100% | 41.5k spikes |
| F2 edge deletion | 25% / 50% | 84.7 / 72.4 | 89.5% / 76.5% | latency +33% at 50% |
| F3 unit loss | 10% (~13.9k units) | 94.6 | 100% | dn2 layer tracks (2,941→1,918 spikes) |
| F4 hub loss | 1% / 2% / 5% | 122.3 / 117.5 / 94.1 | 129% / 124% / 99% | spikes 99.9k (2.52×) / 42.4k / 36.4k |
| F5 channel loss | LC4 / LPLC2 / both | 75.1 / 64.4 / 0.0 | 79% / 68% / 0% | both = only catastrophic mode |
| ER null | all conditions | 0.0 | — | also 0 on 1,299-neuron readout |

### 1.5 Limitations acknowledged by authors

LIF abstraction (single-compartment, delta synapses, no plasticity/neuromodulation), Poisson reconstruction of sensory drive, single scalar readout, hub analysis descriptive rather than mechanistic, fault doses bounded to preserve background regime.

---

## 2. Phase 2 — Venue Standard Recovery (LIVE lookup)

**Inferred target venue:** ISCAS 2027 — Regular track (primary) + **Special Session 16.3 "Intelligent Circuits and Systems for Physical Intelligence"** (secondary), Bordeaux, France, June 6–9, 2027.

**Official rubric-relevant facts, retrieved 2026-10-14:**

| Source (accessed 2026-10-14) | What it establishes |
|---|---|
| https://epapers2.org/iscas2027/ESR/authorinfo1.php | Max 5 pages = **4 pages technical content (incl. figures/references) + 1 optional page containing ONLY references**; NOT double-blind; IEEEtran conference template mandatory; submission deadline Oct 22, 2026 23:59 (UTC−5); notification Jan 20, 2027. |
| https://2027.ieee-iscas.org/call-for-papers | Same deadline; accepted papers may be invited to TCAS-I/II, TBioCAS, OJCAS, TCAS-AI, TVLSI. |
| https://ieee-cas.org/files/ieeecass/2026-07/iscas2027-cfp.pdf | Scope list includes "Neural Networks and Neuromorphic Engineering" and "Sensory Circuits and Systems" — this paper fits both. |
| https://epapers2.org/iscas2027/ESR/login.php | IEEE plagiarism screening; in-person presentation requirement. |
| ISCAS Organizing Guide, https://ieee-cas.org/files/ieeecass/2026-04/iscas-organizing-guide-2026.pdf (Best Practice, reviews section) | ≥5 reviews per paper expected; Track Chairs select papers. |
| IEEE conference review form, https://events.ieee.org/wp-content/uploads/paper-review-form.pdf | 10-item 1–5 rubric: relevance; contribution; structure; English; appropriateness of research method; relevance/clarity of figures & tables; abstract quality; keywords; discussion & conclusions; reference list adequate and correctly cited. |

Note the deadline discrepancy between sources (CFP page says notification Jan 11, epapers2 says Jan 20) — epapers2 is the submission system of record; author should trust epapers2. Also: the ISCAS 2027 reviewer-signup page instructs real reviewers not to use AI tools to draft reviews; this document is a pre-submission internal review for the author, not a submission to the conference review system.

**Literature verification for this review (paper_search, this session):** the two fault-injection frameworks recommended below were retrieved with full metadata: SpikeFI — Spyrou, Hamdioui, Stratigopoulos, arXiv:2412.06795 (2024); SpikingJET — Gogebakan et al., IEEE IOLTS 2024, DOI 10.1109/IOLTS60994.2024.10616060. Searches for prior *whole-connectome damage/fault* studies (neuroscience + engineering disciplines, 2023–2026) returned none that damage a connectome controller, supporting the paper's core novelty claim as scoped.

---

## 3. Phase 3 — Rubric Scores

| # | Dimension | Score (1–5) | One-line justification |
|---|---|---|---|
| 1 | Overall recommendation | **Accept with minor revisions** (maps to 4/5) | Novel question, clean controls, reproducible; blockers are all fixable in ≤1 day. |
| 2 | Reviewer confidence | 4/5 | Reviewer works in both neuromorphic reliability and connectomics; did not execute the code. |
| 3 | Novelty | 4/5 | First behavioral fault-injection on a whole-connectome controller; −1 because SNN fault-injection frameworks exist and are neither cited nor differentiated (§4.1, B1). |
| 4 | Technical correctness | 4/5 | All arithmetic verified (§4.7); F3/F4 implementation honestly described; concern: "exactly zero" ER/F5both results are clean but under-explained (§4.2). |
| 5 | Theory / depth of analysis | 3/5 | Pathway-mass argument is linear and simple; "threshold amplification" is asserted, not modeled even minimally (§4.3). |
| 6 | Empirical strength | 3/5 | 18×12×2 design is broad, but 12 trials/condition, medians without dispersion in text, no significance testing, single task, single connectome instantiation (§4.1, S1–S2). |
| 7 | Reproducibility | 4/5 | SHA-256 seeds, restore-per-trial, runtime stated — but no code/data release statement (§4.1, B2). |
| 8 | Clarity / writing | 4/5 | Dense but well-structured; compression occasionally costs precision (§4.6). |
| 9 | Significance to ISCAS audience | 4/5 | P1–P5 are directly actionable for neuromorphic system designers; strong SS 16.3 fit. |
| 10 | Ethics / safety | 5/5 | No issues; no human/animal data; public connectome. |
| 11 | Comparison with state of the art | 2.5/5 | Related work is qualitative; no quantitative contrast with any prior fault-injection framework or with an engineered network on the same task (§4.1, S4; §4.5). |
| 12 | Figure / table quality | 4/5 | Publication-quality panels; minor caption inconsistencies (§4.4). |
| 13 | Bibliography quality | 3/5 | 24 refs, recency-weighted (2024–2026 dominant), all verifiable; but misses the two most relevant works and cites arXiv preprints as primary evidence for load-bearing claims (§4.5). |

---

## 4. Phase 4 — Detailed Findings

### 4.1 Blocker issues (fix before submission)

**B1 — Missing prior art: SNN fault-injection frameworks (novelty exposure).**
`sections/related.tex`, line 4: "Robustness of spiking networks to weight noise has mostly been characterized on small trained architectures [thieu2022effects, yunusoglu2025neuromorphic]." This sentence omits the dedicated fault-injection literature: **SpikeFI** (Spyrou et al., 2024), a fault-injection framework for SNNs that maps injected faults to device-level defects, and **SpikingJET** (Gogebakan et al., IOLTS 2024), which enhances fault injection for fully connected and convolutional SNNs targeting safety-critical deployment. ISCAS draws reviewers from the reliability/IOLTS community; one of them *will* name these papers, and the current text makes the framework sound more unprecedented than it is. The honest and stronger position: those frameworks inject into *trained, task-specific* networks scored by classification accuracy; this paper injects into an *evolved, connectome-specified* controller scored by *behavioral* output, which is precisely what trained-network fault models cannot provide. Fix: add both citations, one contrast sentence in related work, and tighten the "first" claims (intro line 4, abstract) to "first systematic fault-injection study of a *whole-brain connectome controller*" — the hedge "to our knowledge" is present but the scope must carry the weight, not the hedge.

**B2 — No code/data availability statement contradicts the reproducibility claim.**
`sections/methods.tex`, line 9: "fault realizations are driven by deterministic SHA-256–derived seeds, making every number in this paper exactly reproducible." Exact reproducibility requires the artifact. Add one footnote in Section II: "Code, connectome-derived edge lists, and per-trial records will be released at ⟨URL⟩" (or "from the author upon request" as a minimum, though a repository is strongly preferred and cheap). Without it, a reviewer scores reproducibility as claimed-but-unverifiable.

**B3 — "Looming-triggered" task language vs. constant-rate stimulus.**
`sections/methods.tex`, line 6 and `sections/results.tex`, line 2 describe a looming-triggered escape circuit, but the stimulus is a fixed 150 Hz Poisson drive for the whole trial — there is no looming (expanding-object, accelerating-rate) dynamics. A neuroscience-literate reviewer will flag this as task-fidelity overstatement. Fix (cheapest): rename the task "escape-command pathway stimulation" and add one sentence: "A sustained high-rate drive approximates the plateau response of LC4/LPLC2 to looming stimuli [fu2020complementary]; we do not model looming kinetics." Alternatively implement a rate ramp — but that invalidates all current results and costs a re-run; do not attempt before the deadline.

### 4.2 Section-by-section feedback

**Abstract.** Well-compressed, hedged appropriately. Two edits: (i) after "never been measured at the behavioral level", the claim is fine, but "An edge-permuted Erdős–Rényi null network with identical weight statistics" should read "identical weight and out-degree statistics" (in-degree is what got scrambled — precision matters here because the null's *asymmetry* is the point); (ii) consider appending one artifact sentence ("All fault realizations are seeded and released.") — kills B2 and strengthens the close.

**I. Introduction.** Strong opening paragraph; the gap statement ("their tolerance … must be re-measured for every design") is crisp and ISCAS-relevant. Line 4: the four-neuron command set is introduced without saying why these four (DNp01/DNa02/DNb01 are the characterized take-off/command types) — add "(take-off command types identified in [shuang2023opplod/fu2020complementary])" or similar. Contribution (ii) is a long single sentence with five clauses; split after "…10% unit loss is invisible".

**II. Related Work.** Two paragraphs, correctly organized (connectome-executable models; SNN robustness/hardware). Beyond B1: the sentence "None of these works measures what happens when the controller is damaged: published analyses vary inputs, not integrity" is the paper's best positioning sentence — keep it verbatim. One gap: the ER-null/permutation methodology deserves a pointer to damage-analysis traditions in network neuroscience (lesion studies on connectomes) if the authors can find one verifiable reference; if not, the current framing stands on its own.

**III. Methods.**
- III-A: faithful and appropriately modest ("we re-implemented the model faithfully"). Good that runtime is stated. One omission: brian2 dependency and the released model's own calibration of the Poisson background are asserted but the *threshold* θ's sensitivity is never discussed (see S2).
- III-B: calibration numbers (94.6 Hz interdecile 93.6–95.8; 8.2 Hz; latency 4.4 ms) differ slightly from the sweep baseline (94.7; 94.0–95.6; 4.05 ms) — this is presumably calibration-set vs. sweep-set sampling, but nothing says so. A reviewer WILL notice 4.4 vs 4.05 ms and 94.6 vs 94.7 Hz. Add half a sentence: "Sweep-phase baselines (Section IV) are computed over the 12 sweep trials."
- III-C taxonomy: F3/F4 are described as silencing output synapses with the equivalence-to-unit-removal argument — this is correct for delta synapses and admirably precise. Keep.
- Table I: clean; "memristor stuck faults" for F2 is the loosest mapping (stuck-at-fault is a bit-level analogue) — acceptable at ISCAS.
- Controls (III-D): excellent design; this is the paper's methodological spine. One underspecification: pathway mass — state explicitly whether A is the **binarized** signed submatrix. "Total number of k-hop directed paths" is only literally true for a 0/1 matrix; if weights enter the product, the quantity is weighted path mass. One clause fixes it.
- Fig. 1: clear; the feedback arrow "rate vs. θ" from readout to fault layer reads oddly (the fault layer does not consume the readout) — consider an arrow to a small "score" node instead, or drop it.

**IV. Results.**
- IV-A: the specificity argument (random stimulation yields more total spikes, less command rate) is compelling and correctly deployed as the validity anchor. The "exactly zero in every trial" F5both claim deserves one mechanistic clause — zero is a strong number to report from a spiking simulation; say *why* (command DNs receive their effective excitatory drive through the two lesioned channels; surviving afferents alone never cross threshold). Otherwise a skeptical reviewer suspects an implementation artifact.
- IV-B: excellent dose–response narrative; the latency reframing ("budget latency, not accuracy") is the kind of claim ISCAS reviewers like because it converts a neuro observation into an engineering requirement. The dn2 corroboration sentence is important — keep it, and consider moving its numbers (2,941→1,918) into Fig. 3's caption so they are visible, not buried.
- IV-C: the runaway finding is the paper's most original result and currently rests on three dose points with n=12 each. Two cheap strengthenings: (i) report the hub set's inhibitory fraction at each dose (one sentence, data already available); (ii) state whether the 1% runaway is consistent across trials (interdecile of the 99.9k spike counts). The ER contrast sentence is good.
- IV-D: the pathway-mass dissociation is well told. "76% functional retention at f=0.5 versus 5.8% four-hop mass retention" — make sure the reader knows these are different f-quantities compared across different normalizations (behavior vs. mass), because the juxtaposition invites a apples/oranges complaint; one clause ("mass retained 5.8% of intact 4-hop count") suffices.

**V. Principles and VI. Limitations/Conclusion.**
- Table II is the paper's most quotable artifact; anchors verified (§4.7). P4's "monitor envelope, not liveness" is the strongest engineering statement in the paper.
- The methodological paragraph (certification warning + NeuroBench/formal-methods pointers) is exactly the right pitch for SS 16.3.
- Limitations are honest but end abruptly; the conclusion sentence is long (58 words) — split.
- Missing: an explicit statement of what the framework does *not* claim to cover (e.g., structural faults that reroute rather than delete; fault correlations; plastic recovery over longer timescales). One sentence each; preempts the "scope too narrow" review comment.

### 4.3 Equations and formal content

There is exactly one formal object, m_k = ‖A^k‖₁, used correctly as a path-count functional **if A is binary** — verify and state. The paper's central theoretical claim (threshold amplification converts exponential topological decay into graceful functional decay) is supported empirically but not derived. A minimal derivation — e.g., a two-stage integrator with N convergent afferents, threshold θ, and iid synapse survival p: command rate is a smooth function of the *expected* converged input N·p (linear in p), while path mass decays as p^k; hence behavior/mass separation follows from k ≫ 1 and the saturating rate mapping — would take ~8 lines and lift Theory from 3/5 to 4/5. This is the single highest-leverage intellectual addition available at zero compute cost.

### 4.4 Figures and tables, one by one

- **Fig. 1** (TikZ, III): functional but the feedback arrow is conceptually wrong (§4.2). Minor.
- **Fig. 2** (baseline, 3 panels): (a) threshold placement is well shown; (b) per-neuron profile "pooled over 10 calibration trials" — inconsistent with the 12-trial convention everywhere else; either re-pool over the sweep trials or annotate why 10; (c) the "representative faults" selection is fair; caption says "single-channel silencing" plural but only one channel need be shown — fine.
- **Fig. 3** (curves, 2×2): dual-axis convention (blue rate left, orange latency/spikes right) is consistently applied — good. Panel (d) carries the headline finding; its x-axis is hub dose in % — label "top out-degree fraction" once in the caption to prevent misreading as random dose. All interdecile shading present but never referenced in the text — add "(shading: interdecile range over 12 trials)" to the caption so the dispersion *is* reported somewhere visible (this partially answers S1).
- **Fig. 4** (topology, 3 panels): (a) the all-zeros null panel is stark and effective; (b) relative-decay curves nearly identical — the key figure of the dissociation argument; caption should state whether the y-axis is log-scaled (it is) and that absolute separation is 5.8–17.7×; (c) runaway contrast — good. All three panels earn their space.
- **Table I** (taxonomy): accurate; see III note on "memristor stuck faults".
- **Table II** (principles): every anchor cross-checks against the results text (§4.7); this table alone will be the most-cited slide of the talk.

### 4.5 Related-work gaps (must / should)

- **MUST CITE** (both verified via paper_search this session):
  1. T. Spyrou, S. Hamdioui, H.-G. Stratigopoulos, "SpikeFI: A Fault Injection Framework for Spiking Neural Networks," arXiv:2412.06795, 2024.
  2. A. B. Gogebakan, E. Magliano, A. Carpegna, A. Ruospo, A. Savino, S. Di Carlo, "SpikingJET: Enhancing Fault Injection for Fully and Convolutional Spiking Neural Networks," IEEE IOLTS 2024, DOI 10.1109/IOLTS60994.2024.10616060.
  Failure to cite these is the paper's only genuinely dangerous omission: both are SNN fault-injection *frameworks*, i.e., the same artifact class as the paper's contribution (i).
- **SHOULD CITE:** the FlyWire complete-connectome dataset paper (Dorkenwald et al., *Nature* 2024) alongside lin2024network, since the paper uses the wiring itself, not merely its network statistics; and one canonical biological-robustness reference (e.g., Kitano, *Nat. Rev. Genet.* 2004, "Biological robustness") to anchor "evolved robustness" claims — verify metadata before adding; do not cite from memory.
- Correctly *not* needed: NeuroBench and the formal-methods line are already cited (yik2023neurobench, medvedeva2025formalizing).

### 4.6 Writing quality (line edits)

1. Abstract, "An edge-permuted Erdős–Rényi null network with identical weight statistics" → "identical weight and out-degree statistics" (accuracy).
2. Intro, contribution (ii): split the 60+ word sentence.
3. Methods III-B: add the calibration-vs-sweep provenance clause (4.4 vs 4.05 ms issue).
4. Methods III-D: "restricted to the input-to-command submatrix" → "restricted to the binarized input-to-command submatrix" (pending author verification of what was actually computed).
5. Results IV-C: "The same lesion in the ER null produces no such signature" — good; consider "no comparable signature" since the null produces nothing at all.
6. Results IV-D: fix the normalization juxtaposition (see §4.2).
7. Conclusion: split the final 58-word sentence; end on the framework sentence rather than the reframing sentence.
8. Keywords: add "fault injection" and "reliability" — ISCAS reviewers/searchers use these terms.
9. Limitations: add one sentence scoping what is not covered (rerouting faults, correlated failures, plasticity-driven recovery).
10. Throughout: "escape pathway" vs "escape-command pathway" — pick one term and use it exclusively.

### 4.7 Number audit (all recomputed 2026-10-14 from sim/results/summary.json and jsonl records)

Verified correct: 1,386 = 1% of 138,639; 9.1% synapse share at 1% hub dose; 9–22% range across doses (9.05/13.2/22.4); 122.3 Hz = +29% over 94.7; 99.9k = 2.52×39.7k; 76.5% = 72.4/94.7; 89.5% = 84.7/94.7; 5.4/4.05 = +33%; 79% = 75.1/94.7; 68% = 64.4/94.7; 5.8× = 4.176/0.715; 17.7× = 0.635/0.0358; 13,864 ≈ "nearly 14,000"; 2,941 vs 1,918 dn2 spikes; ER null = 0.0 Hz in all recorded conditions; F5both = 0 in all trials. **No numerical errors found.** The single residual risk is interpretive: "exactly zero" and "identical decay" statements should carry their measurement basis (12 trials, thresholded readout) which the text mostly does.

---

## 5. Phase 5 — Prioritized Action Plan and Decision

### 5.1 BLOCKER (fix before submission; ~1 hour total, no compute)

1. **Add SpikeFI + SpikingJET citations and one contrast sentence** in Related Work; re-scope the "first" claims in abstract and intro to "first systematic fault-injection study of a *whole-brain connectome controller*". (30 min; page-cost ~4 lines, recover by trimming one related-work sentence.)
2. **Add an artifact-availability footnote** in Methods III-A/C: code + edge lists + per-trial records at a repository URL. Create the repo (private-to-public at camera-ready is acceptable; even an anonymized zip link helps). (20 min.)
3. **Fix the looming overstatement**: rename task to "escape-command pathway stimulation" in Methods III-B and Results IV-A; add the plateau-approximation clause. (10 min.)

### 5.2 SHOULD-FIX (do if time allows before Oct 22; ~half day)

4. **Report dispersion in text or make it caption-visible**: add "(shading: interdecile over 12 trials)" to Fig. 3 caption and one interdecile range for the F4-1% runaway spike count. (15 min.)
5. **θ-robustness sentence**: state that all qualitative conclusions are unchanged for θ anywhere in [lower-escape-decile, upper-background-decile] or the tighter interval you can defend from the trial distributions. (30 min; no recompute if using existing deciles.)
6. **Hub-set composition**: one sentence giving the inhibitory fraction of the removed hub sets at 1/2/5% (computable from the connectome annotation in seconds). Turns the disinhibition story from speculation into evidence. (30 min.)
7. **Threshold-amplification mini-derivation** (§4.3): 6–10 lines in IV-D, converting the empirical dissociation into a stated mechanism. Highest intellectual ROI per line in the whole revision. (1–2 h.)
8. **Soften or substantiate the benchmark claim** in intro line 2. Cheapest: "provides a reference point against which engineered designs can be benchmarked" (drop the implied comparison actually performed). Substantive option — a tiny trained SNN on the same task — is a 4–6 h job; only if a co-author cycles it. (10 min soft / 5 h hard.)
9. **Harmonize calibration vs. sweep provenance** (4.4/4.05 ms; 94.6/94.7 Hz) with one clause in III-B or IV-A. (5 min.)
10. **Fig. 2(b) caption**: reconcile "10 calibration trials" with the 12-trial convention. (5 min.)
11. **Add Dorkenwald et al. 2024** for the connectome source (verify via paper_search before adding; do not cite from memory). (10 min.)

### 5.3 POLISH (camera-ready or if minutes remain)

12. Keywords: add "fault injection", "reliability". 13. Conclusion final sentence split. 14. Fig. 4(b): state log-scale in caption. 15. Fig. 1 feedback-arrow cleanup. 16. Terminology unification ("escape pathway"). 17. Limitations scope sentence (rerouting/correlated faults/plastic recovery).

### 5.4 Decision

**Accept with minor revisions.** In its current state the paper would most likely receive a weak-accept-to-accept at ISCAS regular review (the organizing guide's ≥5-review average tempers single-reviewer risk), but the SpikeFI/SpikingJET omission is the kind of finding that flips one reviewer to "novelty overstated" — and in a Special Session, where slot counts are small and PC scrutiny of SS papers is higher than the regular track, that is an avoidable risk. With the three blockers fixed (≈1 hour, zero compute) the paper is a strong SS 16.3 submission: novel substrate, clean negative controls, exact reproducibility, and a principles table that speaks the hardware audience's language. The should-fix items 4–7 (≈ half day) would move Theory and Empirical-strength scores from 3/5 to 4/5 and materially raise the TCAS-journal-invitation odds.

**Estimated total effort to camera-ready quality: ~1 day text-only; ~1.5 days with the mini-derivation and hub-composition additions. Deadline margin: 8 days (Oct 22).**

