# PAPERGURU REVIEW — v2.0 (Post-Revision Re-Review)

**Manuscript:** *How Much Fault Tolerance Is in a Fly Brain? Fault-Injection Analysis of a Whole-Connectome Spiking Controller for Physical Intelligence* (Shuchao Gao, Waseda University)
**Reviewed version:** `paper/main.pdf`, 5 pages (technical content pp. 1–4, references-only p. 5), 27 references, post-revision state of 2026-10-15 (real-data Fig. 1 with CC-BY inset, SpikeFI/SpikingJET citations, artifact footnote).
**Review date:** 2026-10-16. **Supersedes** `REVIEW_v1.md`; all three v1 blockers were verified as fixed in this version.
**Inferred venue:** IEEE ISCAS 2027 (Bordeaux, June 6–9, 2027) — regular-track formatting, targeted at Special Session 16.3 *"Intelligent Circuits and Systems for Physical Intelligence"* (special-session papers undergo the same review as regular papers). Submission deadline **Oct 22, 2026 (extended)**.

---

## Phase 1 — Understand the Paper

1. **(a) Problem statement (one sentence).** No one has ever measured how a *complete, evolved* connectome controller behaves when its components fail, although such controllers are now being ported to neuromorphic hardware; this paper performs that measurement on the released 138,639-neuron LIF whole-brain model of *Drosophila*.

2. **(b) Claimed contributions.**
   - Author wording: "(i) a fault-injection framework mapping hardware failure modes onto a biologically exact 138k-neuron controller" — a five-family taxonomy (F1 weight noise, F2 synapse deletion, F3 random unit loss, F4 hub loss, F5 channel deafferentation) applied post state-restoration with deterministic seeds.
   - "(ii) the first behavioral-grade tolerance curves of a complete connectome (50% weight noise absorbed, 50% synapse loss retains 76%, 10% unit loss invisible); top-1% hub loss instead produces a 2.5× *activity runaway*" — the empirical core.
   - "(iii) a decomposition showing that linear graph redundancy explains neither specificity nor graceful degradation, implicating threshold amplification in convergent spiking dynamics" — the mechanistic claim, supported by an ER null plus analytic pathway-mass analysis.
   - "(iv) five design principles for fault-tolerant neuromorphic controllers" — Table I, each principle anchored to a measured number.
   - My reading: (i)+(ii) are an empirical first on this substrate class and survive the v1 novelty audit; (iii) is the intellectual contribution that lifts the paper above a measurement report; (iv) is packaging. The novelty claim is now correctly narrowed ("on such a controller") after v1 flagged SpikeFI/SpikingJET.

3. **(c) Method summary.** The released Brian2 LIF whole-brain model (FlyWire v783 connectome: 138,639 neurons, 15,091,983 signed edges, delta synapses of 0.275 mV, 40% inhibitory) is driven through the visuomotor escape pathway: LC4+LPLC2 (314 cells) stimulated at 150 Hz Poisson, read out as the population rate of 8 command descending neurons (DNp01, DNa02, DNp04, DNb01) over the last 500 ms, thresholded at θ=51.4 Hz. Five hardware-motivated fault families are injected after full state restoration and held fixed across 12 seeded 600 ms trials per condition (36 conditions). Two controls isolate mechanism: an edge-permuted Erdős–Rényi null preserving weight and out-degree statistics, and an analytic synapse-count-weighted pathway mass m_k = ‖A^k‖₁ on the sensory-to-command submatrix.

4. **(d) Experimental setup.** Dataset: published FlyWire connectome tables (no new data collection). Baselines: intact model and ER null. Metrics: command-population rate (primary), first-spike latency, total spikes, broad-readout (1,299 descending neurons) spikes; pass/fail vs θ. Seeds: SHA-256-derived, deterministic; 10-trial calibration set vs 12-trial sweep set explicitly separated (Sec. III-B). Compute: ≈3.5 s per 600 ms trial on one CPU core. Statistics: medians with interdecile ranges reported for key conditions; no formal hypothesis tests (appropriate for deterministic seeded sweeps, but see Empirical Strength in the rubric).

5. **(e) Headline results (reconstructed).**

   | Condition | Command rate | vs. healthy (94.7 Hz) | Note |
   |---|---|---|---|
   | Healthy (12 trials) | 94.7 Hz (94.0–95.6) | — | 4.05 ms latency |
   | Random drive control | 8.2 Hz | 9% | 293k vs 40k total spikes |
   | F1 weight noise σ=0.5 | 94.7 Hz | 100% | flat through dose |
   | F2 synapse loss 50% | 72.4 Hz | 76.5% | latency 4.05→5.4 ms (+33%) |
   | F3 unit loss 10% (~14k neurons) | 94.6 Hz | ~100% | flat through dose |
   | F4 hub loss 1% (1,386 cells, 9.1% synapses) | 122.3 Hz (121.1–123.9) | **+29%, 2.52× global activity** | dysregulation, not silence |
   | F5 both channels silenced | 0.0 Hz every trial | 0% | only catastrophic mode |
   | ER null, any condition | 0.0 Hz | — | transmits nothing |

6. **(f) Stated limitations.** LIF abstraction (single-compartment, delta synapses, no plasticity, Poisson drive); doses bounded to keep the background regime intact; hub analysis descriptive; no correlated damage or plastic recovery modeling (Sec. V-B). Adequate and honest for the venue.

---

## Phase 2 — Recover the Standard

**Official venue rules (live-verified 2026-10-16):**

- **Paper specification** — epapers2 author instructions (https://epapers2.org/iscas2027/ESR/authorinfo1.php), quoted verbatim: *"Paper Length: Maximum 5 pages, of which 4 are for technical content including text, figures and references (if any), and with one additional optional 5th page containing only references"* and *"ISCAS is NOT double-blind review this year. Please include author information on your submission."* → The current manuscript is **compliant**: content ends on p. 4, p. 5 begins with REFERENCES and contains only references. This resolves the v1-era misreading (the rule is 4+1, not 5+1).
- **Deadlines** — official CFP (https://2027.ieee-iscas.org/call-for-papers + https://ieee-cas.org/files/ieeecass/2026-07/iscas2027-cfp.pdf): regular/special-session paper submission **October 22, 2026 (extended from October 13)**; author notification January 11, 2027 (CFP page; the epapers2 dashboard remains authoritative if it differs — verify at submission); final paper January 27, 2027. Papers are submitted to IEEE Xplore.
- **Review process** — ISCAS 2026 actuals (published TPC welcome message): **51.9% regular-paper acceptance, >4.2 reviews per paper**, three-tier track structure (Track Chair / Review Committee Member / Reviewer). IEEE CASS review forms use ten 1–5 criteria (relevance to ISCAS, novelty/originality, technical content, clarity, references, title, abstract, figures/tables, overall recommendation, reviewer confidence). Special-session papers are held to the same bar.
- **Alternative route noted:** the OJCAS special-session option (5–8 pages, initial submission Oct 1, 2026) — its deadline has **passed**; irrelevant here, do not consider.

**Literature verification (paper_search, 2026-10-16).** Two targeted searches (fault injection × SNN × neuromorphic; Drosophila connectome × fault/degradation) confirm: (1) no competing work injects faults into a whole-connectome controller — the v1-narrowed novelty claim holds; (2) the SNN dependability literature has moved since the revision and the paper's related-work paragraph now lags its own field's 2025–2026 wave (details in §Related-Work Gaps below, with DOIs).

---

## Phase 3 — Rubric Table

Scale: 1–5 (IEEE CASS review-form style). "Rec." uses ISCAS's implicit accept/reject decision categories.

| Dimension | Score | Rationale | Required fix |
|---|---|---|---|
| **Overall recommendation** | **Accept (4/5)** | Novel measurement on a unique substrate, mechanism-backed, compliant, honest limitations; one pre-camera-ready artifact action and a citation refresh needed. | Apply Phase 5 list. |
| Reviewer confidence | 5/5 | All numbers re-derived from the released connectome + result files; venue rules verified live. | — |
| Novelty / originality | 4.5/5 | First behavioral fault-injection sweep on a whole-connectome controller; SpikeFI/SpikingJET contrast now explicit (Sec. II). The *concept* of SNN fault injection is not new — the paper no longer pretends otherwise. | Keep the narrowed claim wording exactly as in Intro L4. |
| Technical correctness | 4.5/5 | Every headline number (94.7, 72.4/76.5%, 122.3, 2.52×, 0.0 Hz, 594/849/22,471/1,437, 60% vs 40% inhibitory) re-verified against `sim/results/*` and `sweep.py` logic; θ-robustness interval (9.2–63.1 Hz) is per-trial-verified. | Fix P5 anchor wording (see Blockers). |
| Theoretical depth | 3.5/5 | One formal object (m_k = ‖A^k‖₁) + a six-line convergence/threshold mini-derivation (Sec. IV-D). Correct but not a theory contribution; fine for ISCAS. | None; do not overpromise theory. |
| Empirical strength | 4/5 | 36 conditions × 12 seeds, deterministic; dispersion given as interdeciles for headline conditions only; no external model cross-check (e.g., a second connectome or Brian2-vs-Loihi2 port). | State per-trial minima explicitly for F2 dose curve (already partly done). |
| Reproducibility / release readiness | 3.5/5 | Seed-exact pipeline, artifact footnote added — but "available from the author" has no persistent identifier; environment (Brian2 version, Python) unstated. | **Create public repo + pinned commit/DOI before camera-ready** (see Blocker 1). |
| Clarity & writing | 4.5/5 | Dense but disciplined two-column IEEE prose; compressions left no grammar damage; terminology (fault family/condition/trial) consistent. | Three line-edits in Phase 4 §12. |
| Significance / impact | 4/5 | Directly relevant to SS 16.3's theme (controllers for physical intelligence on imperfect hardware); principles are actionable. | — |
| Ethics / broader impact | N/A (5) | No human/animal data; public connectome; no dual-use concern. | — |
| SOTA & related-work coverage | 4/5 | Core competing lines covered (SpikeFI, SpikingJET, Loihi-2 port, connectome-application wave 2026); **missing the 2025–2026 dependability wave** (IOLTS/DATE/ETS/ICONS). | Add 3–4 citations (see Related-Work Gaps). |
| Figure & table quality | 4/5 | Fig. 1 is now a real-data connectogram with attribution — strong; Figs. 2–4 legible with units; Table I anchors every principle. | Inset is small at print size; keep (acceptable), but see Polish. |
| Bibliography quality | 4.5/5 | 27 entries, newest-first coverage through Oct 2026 (cho2026dorkenwald-wave), all entries verified via paper_search/CrossRef; CC-BY inset attribution correct. | Add the 2026 dependability refs; then 5/5. |

---

## Phase 4 — Detailed Findings

### Blocker Issues

**B1 (borderline blocker — must fix before camera-ready, may submit without it). Artifact persistence.**
- Claim: the reproducibility selling point rests on a footnote ("Code, connectome-derived edge lists, and per-trial records are available from the author.", Sec. III-C) with no persistent identifier; if the reviewer asks "where?", there is no answer at notification time.
- Location: Sec. III-C, footnote 2.
- Why it matters: Reproducibility is claimed three times (Abstract "identical weight and out-degree statistics", III-C seed sentence, V-A "re-runs in minutes"). A single-author "available from the author" is the weakest form of that promise and is the one thing a skeptical reviewer can use to discount all numbers.
- Fix: create a public repository (GitHub + Zenodo DOI, or institutional archive) containing `sim/`, the edge lists, and result JSONs; replace the footnote with "available at [DOI]". If timing is tight for the Oct 22 deadline, an anonymized-but-persistent link is unnecessary (ISCAS is not double-blind) — a plain URL added now suffices; the DOI can be added at camera-ready.

No other blocker-level defects were found: page limit ✓, claim support ✓, citation integrity ✓ (27/27 verified), CC-BY attribution ✓ (caption + ref [27]).

### Section-by-Section Feedback

**Abstract.** Complete quantitative thumbnail; every number matches the body (76%, 2.5×, 0.0 Hz). The ER sentence ("identical weight and out-degree statistics") is now precise. No edit required.

**I. Introduction.** Tight; the four contributions are enumerated without a list environment; the hardware-fault mapping sentence ("weight imprecision, broken interconnect, dead cores, and dead sensors") now anticipates the taxonomy. Minor: "to our knowledge, the first systematic fault-injection study on such a controller" — keep "to our knowledge"; it is doing useful work.
- Edit: consider adding one clause naming the controller's port to hardware to sharpen motivation: "...and a reference point for benchmarking the fault tolerance of engineered designs, several of which now exist on Loihi 2 [wang2025neuromorphic]." (Optional; page budget has ~2 lines of slack.)

**II. Related Work.** Two-paragraph compression is effective; the SpikeFI/SpikingJET contrast sentence ("automate this but score task accuracy on human-designed networks") is exactly the right differentiation. The closing claim — "our taxonomy and scoring transfer, so the resulting curves read as requirements rather than observations" — is the paper's positioning in one line.
- Weakness: the hardware/dependability literature sentence ("Hardware platforms expose complementary constraints: on-chip variability co-design, FPGA precision–capacity trade-offs, and edge energy–robustness envelopes") cites only 2025–2026 *platform* work and misses the 2025–2026 *fault/dependability* work (see Related-Work Gaps). A circuits-audience reviewer may know those venues (IOLTS, DATE, ETS, ICONS are CESS-adjacent) and notice.

**III-A (Substrate).** All constants present (threshold, reset, τ_m, refractory, delay, synapse magnitude, edge count, inhibitory fraction); provenance of background drive stated; trial-restoration design stated; compute cost stated. This is a model reproducibility paragraph of above-average quality.
- Edit: "(Section~I)" is hardcoded; use `\ref{}` or leave — if section order is final it is safe, but a `\-ref` protects against camera-ready reordering.

**III-B (Task).** The looming caveat ("rather than modeling looming kinetics") resolves v1-B3; θ-robustness sentence ("every pass/fail classification below is unchanged for any threshold between the distributions' observed trial extremes, 9.2 and 63.1 Hz") converts a fragility into a strength. Calibration-vs-sweep provenance sentence present.
- Nit: "median first-spike latency 4.4 ms" (calibration) vs "4.05 ms median" (sweep, Sec. IV-A) — both correct for their sets, and the provenance sentence covers it, but a reviewer skimming may flag the mismatch. Add "(10-trial set)" after the 4.4 ms value.

**Fig. 1 (new).** Real-data connectogram: 314 sensory cells → top-90 of 849 two-hop relays → 8 command DNs, line α/width ∝ synapse count, red dashed badges marking where F1–F5 act, inset = FlyWire whole-brain render with attribution. This is the single biggest quality jump since v1: the reader now sees the experiment geographically *and* statistically. Caption carries the true edge counts (594 direct; consistent with the data).
- Nit: caption says "adapted from" nowhere; it says "from Dorkenwald et al. [27] (CC BY 4.0)" — IEEE's preference is the word "Adapted from" when the image is re-rendered/cropped. One-word fix.

**III-C (Taxonomy).** All five families with parameter grids in one paragraph; the hub-definition sentence ("ranked by total outgoing synapse count (again excluding input and readout)") matches the implementation exactly (weighted bincount, protected types excluded). Seed sentence + footnote.
- Nit: "these cells carry 9–22% of all synapses" — this is the 1%/2%/5% hub sets respectively; a parenthetical "(for the 1%, 2% and 5% sets, respectively)" removes any ambiguity.

**III-D (Controls).** The ER description is precise about what is preserved (out-degree, weight, sign) vs destroyed (in-degree structure); the pathway-mass definition now correctly says "synapse-weighted mass of k-hop directed routes" (v1's mischaracterization fixed).

**IV-A.** Specificity paragraph: 94.7 vs 8.2 Hz with the "more total activity (293k vs 40k spikes)" inversion — this is the most persuasive single sentence in the paper for a circuits audience (activity is not the signal). F5-both zero-trial statement is exact.

**IV-B.** Corrected numbers (91.9/93.1 Hz) ✓; per-trial minima in-line ✓; the latency-cost sentence ("4.05 to 5.4 ms at 50% loss (+33%)") is the right behavioral framing; the broad-readout sentence closes the "eight-neuron readout is cherry-picked" objection.
- Nit: "(the weakest per-trial rates, 63.1 Hz under single-channel loss and 68.1 Hz at 50% synapse loss, both remain far above θ)" — this parenthetical mixes F5 and F2 evidence inside the F2 paragraph; a semicolon introducing "across all conditions," would make the scope unambiguous.

**IV-C.** Hub-loss paragraph: numbers + mechanism ("about 60% of removed hub output synapses are inhibitory, versus 40% network-wide") + engineering reading ("violates its output envelope while every per-unit health monitor still reads 'active'") + ER-null dissociation. Complete and well-ordered. No edit.

**IV-D.** The mechanistic centerpiece. The mini-derivation is correct (Np linear vs p^k geometric; 6.25% at k=4, p=0.5; saturating threshold nonlinearity; 76.5% > 50% linear bound). The pathway-mass numbers (5.8×/17.7× absolute advantage; 0.3% vs 0.4% relative decay at f=0.5, k=8) are consistent with `sim/results/graph/pathway_mass.json`. The double-requirement closing sentence ("requires both convergent wiring ... and threshold dynamics") is the right falsifiable statement.

**V-A (Principles + Table I).** Each principle anchored to a measured number; P4's "monitor envelope, not liveness" is quotable.
- Consistency flag (see Blockers B2-lite): P5 anchor says "single-channel loss 68–79%" but Sec. IV-B reports the weakest *single trial* at 63.1 Hz (=66.6% of baseline). Both are true (68–79% is per-channel median; 63.1 Hz is the worst trial), but the table does not say "median". Fix the anchor to "single-channel loss: 68–79% median (min 66.6%)" or similar.

**V-B (Limitations & Conclusion).** Honest scope; the closing aphorism ("robustness is a property of the wiring, not of precision parts") lands. The methodological-message paragraph (certify by fault injection, not topology) justifies the paper's existence beyond the measurement.

### Equations & Proofs

Only two formal objects; both verified:
1. **m_k = ‖A^k‖₁** (Sec. III-D): A defined as the synapse-count submatrix; the text's "synapse-count-weighted mass of k-hop directed routes" is exactly ‖A^k‖₁ restricted to LC4∪LPLC2 rows and DN columns. Implementation (`pathway_analysis.py`) uses |w0| — consistent.
2. **Convergence/threshold mini-derivation** (Sec. IV-D): E[drive] = Np linear; k-hop mass p^k; saturating f ⇒ rate changes slowly near operating point; the 76.5% > 50% inequality is correctly framed as a *bound* comparison, not a proof. No errors.

### Experiments (figure/table audit)

- **Fig. 1** (fig0_pathway.pdf): supports "the instrumented pathway exists, is sparse-to-convergent, and has injectable parts." Verified from real adjacency; α-scaling stated in caption. Missing: nothing material. (Optional: mark the 594 direct edges visually distinct — currently they blend into the green fan.)
- **Fig. 2** (fig2_baseline.pdf, single panel): claim = readout specificity. Supports it. Missing: per-trial dots or interdecile bar for the two conditions (12 trials each) — one line of matplotlib; strengthens "far above θ".
- **Fig. 3** (fig3_curves.pdf, 2 panels): F2 dose–response + F4 hub dose–response. Supports the graceful-degradation and runaway claims. Missing: interdecile shading on the curves (data exists in summary.json); F1/F3 flat curves were cut for space and are delegated to Table I — acceptable, and the text says so explicitly ("flat to within noise (Table I)").
- **Fig. 4** (fig4_topology.pdf, 2 panels): pathway-mass decay + hub-runaway ER contrast. Supports the central decomposition. Caption correctly notes the ER null transmits nothing (0.0 Hz).
- **Table I**: five principles with anchors; anchor wording consistency is the only issue (P5, above).
- **Statistical reporting:** medians + interdeciles for headline conditions; per-trial minima quoted for the two weakest cases; 12 trials per condition; deterministic seeds. For an ISCAS measurement paper this is adequate; adding interdecile shading to Figs. 3–4 would preempt the "error bars?" review question at zero text cost.
- **Reproducibility of numbers:** verified — every number in the text was re-derived in this review from `sim/results/{real,er}/*.jsonl`, `calibration.json`, and `pathway_mass.json`.

### Related-Work Gaps

Must cite (novelty-adjacent — the paper already handles this class):
- ✅ SpikeFI (Spyrou et al., arXiv:2412.06795) and SpikingJET (Göğebakan et al., IOLTS 2024, DOI 10.1109/IOLTS60994.2024.10616060) — already cited and differentiated.

Should cite (2025–2026 dependability wave; strengthens positioning with the circuits audience, zero page cost since references live on p. 5):
1. **Jouni & Stratigopoulos**, "STDP-Trained SNN Reliability Assessment Through Fault Injections," IOLTS 2025, DOI 10.1109/iolts65288.2025.11116934 — fault-injection methodology line continued into 2025.
2. **Gleyo & Girau**, "Population coding to improve fault tolerance of neuromorphic networks in regression tasks," DATE 2026, DOI 10.23919/date69613.2026.11539446 — *redundancy-based* tolerance in engineered SNNs; the direct engineered-side counterpart of P1/P2.
3. **Chessa et al.**, "Cross-Layer Analysis of Permanent Faults in Asynchronous NoCs for Neuromorphic Computing," ICONS 2026, DOI 10.1145/3822454.3822495 — interconnect-permanent-fault hardware anchor for F2.
4. **Kumar et al.**, "Dependable digital spiking neuromorphic hardware," 2026, DOI 10.17918/00011559, and/or **Gracia-Morán et al.**, "Dependability Analysis of a Spiking CNN," LNCS 2026, DOI 10.1007/978-3-032-35506-5_10 — the hardware-dependability framing the paper's principles speak to.

All four fit the existing sentence "Hardware platforms expose complementary constraints: ... Benchmarking efforts omit fault-injection axes [yik2023neurobench]" — one added clause, ~2 lines of prose total, references absorbed by p. 5's spare capacity.

### Writing Quality (line-edits)

1. Sec. III-B: add "(10-trial set)" after "first-spike latency 4.4 ms" to pre-empt the 4.4-vs-4.05 skim error.
2. Sec. III-A: "(Section~I)" → `\hyperref`/`\ref` or accept as-is if ordering frozen.
3. Fig. 1 caption: "from Dorkenwald et al." → "adapted from Dorkenwald et al." (IEEE attribution convention).
4. Sec. III-C: "(for the 1%, 2% and 5% sets, respectively)" after "9–22% of all synapses".
5. Sec. IV-B: change the parenthetical to "across all conditions, the weakest per-trial rates ...".
6. Index Terms: seven terms; IEEE convention is 3–6 — drop "embodied intelligence" or "spiking neural networks" (the title/abstract already carry them).
7. Consistent usage of "vs." vs "versus" — currently consistent; no action.

---

## Phase 5 — Action Plan

### BLOCKER (must fix to be considered) — 1 item
1. **Archive the artifact**: create a public repository containing `sim/` code, connectome-derived edge lists, and per-trial result records; replace footnote 2's "available from the author" with the repository URL (Zenodo DOI can wait for camera-ready). Effort: 1–2 h. (May be completed between submission and camera-ready; the footnote as written is acceptable at submission but must not survive to the final paper.)

### SHOULD-FIX (likely requested by reviewers) — 4 items
2. **Add the 2025–2026 dependability citations**: insert one clause in Sec. II citing Jouni & Stratigopoulos (IOLTS'25), Gleyo & Girau (DATE'26), Chessa et al. (ICONS'26), and Kumar et al. or Gracia-Morán et al. (2026); refs land on p. 5 (capacity verified: ~30 ref-line starts vs ~116 line capacity). Effort: 30 min.
3. **Fix the P5 anchor consistency** (Table I): change "single-channel loss 68–79%" to "single-channel loss: 68–79% median (weakest trial 63.1 Hz)" so the table and Sec. IV-B cannot be read as contradicting each other. Effort: 10 min.
4. **Write "adapted from"** in the Fig. 1 inset attribution (IEEE convention for re-rendered/cropped CC-BY material). Effort: 1 min.
5. **Add "(10-trial set)" after the 4.4 ms calibration latency** in Sec. III-B to pre-empt the 4.4-vs-4.05 misread. Effort: 2 min.

### POLISH (improves quality, not required) — 5 items
6. Add interdecile shading (or per-trial dots) to Figs. 2–4 from the existing `summary.json` dispersion data.
7. Trim Index Terms to five keywords.
8. Add "(for the 1%, 2% and 5% sets, respectively)" after "9–22% of all synapses" in Sec. III-C.
9. Replace hardcoded "(Section~I)" in Sec. III-A with a `\ref`.
10. Optionally mark the 594 direct sensory→DN edges in Fig. 1 with a distinct hue so the direct path is visible at a glance.

### Resubmission Decision

**The paper is submission-ready now.** The manuscript is page-compliant, every quantitative claim is verified against the artifact, the novelty claim is correctly scoped against the SNN fault-injection literature, and the two v1 weaknesses that mattered (missing related work, no artifact statement) are fixed. The remaining items are hardening, not rescuing:

- Exact changes that move it over the line: items 2–4 (citations, P5 wording, attribution word). Everything else is polish.
- Effort estimate: **0.5–1 person-day** for should-fixes + polish, leaving ample margin before the **Oct 22, 2026** deadline.
- Risk register for the review round: (a) a connectome-specialist reviewer asking for the "so what" beyond *Drosophila* — mitigated by the Sec. II closing sentence and P1–P5; (b) a dependability reviewer asking why no fault-injection-on-SNN framework was *used* rather than compared — mitigated by the SpikeFI/SpikingJET sentence; adding the four citations above further defuses it; (c) an artifact request — mitigated by item 1.

**Verdict: Accept (4/5) — submit after items 2–4; complete item 1 before camera-ready.**

---

*Verification trail: all numbers re-derived from `sim/results/` (real/ER jsonl, calibration.json, pathway_mass.json) and `sweep.py`/`pathway_analysis.py` logic; venue rules fetched live from epapers2.org/iscas2027 and 2027.ieee-iscas.org on 2026-10-16; all 27 bibliography entries verified via paper_search/CrossRef (dorkenwald2024neuronal backfilled to Nature 634(8032):124–138).*




---
**STATUS 2026-10-16:** All SHOULD-FIX items 2-5 applied ([23] Jouni IOLTS'25, [24] Gleyo DATE'26, [25] Chessa ICONS'26, [27] Gracia-Morán LNCS'26; P5 anchor wording; 'adapted from'; 10-trial-set note). Polish 7-9 applied (keywords 5, respectively-clause, \ref). Item 6 (interdecile shading) left optional; item 10 moot (direct edges already the distinct green fan). Blocker 1 (artifact repo) remains a USER action before camera-ready. Page compliance maintained via removal of 29 redundant bibliography URL lines (identifiers preserved in .bib: arXiv eprints, journal vol/pages, DOI notes).
