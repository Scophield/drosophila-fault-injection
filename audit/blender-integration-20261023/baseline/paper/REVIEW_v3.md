# PAPERGURU REVIEW — v3.0 (Submission-Readiness Verdict)

**Review brief:** "能投ISCAS吗" (*Can this be submitted to ISCAS?*)
**Manuscript:** *How Much Fault Tolerance Is in a Fly Brain?* (Shuchao Gao, Waseda University) — `paper/main.pdf`, 5 pages, 31 references, state of 2026-10-16 after v2-review fixes.
**Review date:** 2026-10-16. **Chain:** `REVIEW_v1.md` (6-page version) → `REVIEW.md` v2 (post-revision) → **this document**.

---

## VERDICT (stated up front)

**YES — the manuscript is ready to submit to ISCAS 2027. Deadline: October 22, 2026, 23:59 UTC−5 (extended).** Every hard compliance gate is now verified green; one compliance blocker (Type 3 fonts) was discovered *during this review* and fixed; the only open item (public artifact link) is a camera-ready obligation, not a submission obstacle. Remaining work is a 10-item submission checklist (Phase 5), not manuscript revision.

---

## Phase 1 — Understand the Paper (current state)

1. **(a) Problem.** First behavioral-grade measurement of fault tolerance of a complete evolved connectome controller (138,639-neuron LIF whole-brain *Drosophila* model) under five hardware-motivated fault families.
2. **(b) Contributions.** (i) fault-injection framework mapped onto a biologically exact controller; (ii) first connectome-scale tolerance curves (50% weight noise absorbed; 76% retained at 50% synapse loss; 10% unit loss invisible; top-1% hub loss → 2.5× activity runaway; channel deafferentation the only catastrophic mode); (iii) decomposition showing linear graph redundancy explains neither specificity nor graceful degradation — threshold amplification in convergent spiking dynamics does; (iv) five design principles with quantitative anchors (Table I).
3. **(c) Method.** Brian2 LIF whole-brain model on FlyWire v783 (15,091,983 signed edges, 0.275 mV delta synapses, 40% inhibitory); escape task: 150 Hz Poisson drive to LC4+LPLC2 (314 cells), readout = rate of 8 command DNs vs θ=51.4 Hz; five fault families F1–F5 injected post state-restoration, 12 seeded 600 ms trials × 36 conditions; controls: edge-permuted ER null (weight + out-degree preserved) and analytic pathway mass m_k=‖A^k‖₁.
4. **(d) Setup.** Baselines: intact model, ER null, random-drive control. Metrics: command rate, first-spike latency, total spikes, broad 1,299-DN readout. SHA-256 deterministic seeds; 10-trial calibration vs 12-trial sweep explicitly separated (Sec. III-B); ≈3.5 s/trial/core.
5. **(e) Headline results.** 94.7 Hz healthy (94.0–95.6 interdecile); 8.2 Hz random control (with *more* total spikes, 293k vs 40k — specificity, not arousal); F1 σ=0.5 → 100%; F2 50% → 72.4 Hz (76.5%), latency +33%; F3 10% → 94.6 Hz; F4 1% → 122.3 Hz (121.1–123.9), 2.52× global activity; F5 both → 0.0 Hz every trial; ER null → 0.0 Hz everywhere.
6. **(f) Limitations.** LIF abstraction (single-compartment, delta synapses, no plasticity, Poisson drive); bounded doses; descriptive hub analysis; no correlated damage or plastic recovery (Sec. V-B).

**Assumed venue:** IEEE ISCAS 2027, Bordeaux, June 6–9 2027 — regular-track format; thematically aimed at Special Session 16.3 *"Intelligent Circuits and Systems for Physical Intelligence"* (special-session papers follow the same review process as regular papers per the official CFP).

---

## Phase 2 — Recover the Standard (live-verified this session, 2026-10-16)

**Author instructions, fetched live** from https://epapers2.org/iscas2027/ESR/authorinfo1.php — the submission system's own page, quoted verbatim:

- *"Submission deadline (EXTENDED): Oct 22, 2026 23:59 (UTC -0500)"*
- *"Decision notification: Jan 20, 2027"* — this **resolves** the Jan-11-vs-Jan-20 discrepancy noted in v2: the CFP PDF says Jan 11, but the submission system (authoritative for authors) says **Jan 20, 2027**.
- *"Maximum 5 pages, of which 4 are for technical content including text, figures and references (if any), and with one additional optional 5th page containing only references"* ✓ current PDF compliant.
- *"ISCAS is NOT double-blind review this year. Please include author information on your submission."* ✓ author block present.
- *"Fonts: Embed ALL fonts in your PDF file. Avoid the use of Type 3 fonts."* — **this gate caught a real defect this review** (see Blocker 1: fixed).
- *"Allowed File Size: 5 MB"* ✓ (0.27 MB). *"Do NOT apply security settings"* ✓ none. Page size US Letter ✓ (612×792 pt).
- *"IEEE policy requires you to file a copyright release for each accepted submission."* + *"One author per accepted submission must be registered at the full conference rate AND attend the conference to present."* — author-side obligations, listed in Phase 5.

**Rubric provenance.** IEEE CASS review forms (ten 1–5 criteria incl. novelty, technical content, clarity, references, figures) as reconstructed in v2; ISCAS 2026 actuals: 51.9% regular acceptance, >4.2 reviews/paper. No 2027-specific reviewer form is public yet — 2026 forms are the operative fallback.

**Literature delta-check (paper_search, 2026-10-16).** One fresh sweep for connectome-controller fault-injection competitors: none. The only adjacent new item (Gruel et al., "Line-based Event Preprocessing," *Neuromorphic Computing and Engineering* 6:024002, 2026, DOI 10.1088/2634-4386/ae5128) is event-vision preprocessing — out of scope, no citation needed.

---

## Phase 3 — Rubric Table (submission state)

| Dimension | Score | Rationale | Required fix |
|---|---|---|---|
| **Overall recommendation** | **Submit (4.5/5)** | All compliance gates green; claims verified against artifacts; the one Type-3 defect found and fixed within this review. | Execute Phase 5 checklist. |
| Reviewer confidence | 5/5 | Every number re-derived; venue rules fetched from the submission system itself. | — |
| Novelty | 4.5/5 | First fault-injection sweep on a whole-connectome controller; claim correctly scoped against SpikeFI/SpikingJET and the 2025–26 dependability line (now cited: [23][24][25][27]). | — |
| Technical correctness | 4.5/5 | Headline numbers, θ-interval, hub-inhibitory fraction (60% vs 40%), pathway-mass ratios all artifact-verified. | — |
| Theoretical depth | 3.5/5 | m_k=‖A^k‖₁ + six-line mini-derivation — correct, appropriately modest for the venue. | — |
| Empirical strength | 4/5 | 36×12 deterministic runs; medians + interdeciles; per-trial minima quoted; no formal tests (defensible for seeded sweeps). | Optional: interdecile shading (Polish). |
| Reproducibility | 3.5/5 | Seed-exact pipeline, artifact footnote present; persistent link still pending. | Blocker for **camera-ready**, not submission. |
| Clarity | 4.5/5 | Section I cross-reference now a `\ref`; 4.4 ms tagged "(on the 10-trial set)"; P5 anchor now "68–79% median (weakest trial 63.1 Hz)". | — |
| Significance | 4/5 | Direct fit to SS 16.3's theme; P1–P5 actionable for hardware builders. | — |
| Ethics / impact | N/A (5) | Public connectome data; no dual-use. | — |
| SOTA coverage | 4.5/5 | 31 refs; fault-injection line (SpikeFI, SpikingJET, IOLTS'25, DATE'26), hardware/dependability (ICONS'26, LNCS'26), connectome wave through Oct 2026. | — |
| Figure & table quality | 4/5 | Real-data Fig. 1 with CC-BY inset ("adapted from ... [31]"); Figs. 2–4 legible; **fonts now all Type 1/42, fully embedded**. | — |
| Bibliography quality | 4.5/5 | 31 verified entries; acronym case protected ({STDP}, {NoCs}, {S-CNN}); redundant URL lines removed with locators preserved (arXiv IDs, vol/pages, `note={doi:...}` for the bioRxiv entry). | — |

---

## Phase 4 — Findings

### Blocker Issues

**B1. Type 3 fonts in the submission PDF — FOUND AND FIXED DURING THIS REVIEW.**
- Claim: `pdffonts main.pdf` showed **7 embedded Type 3 font objects** (DejaVuSans / DejaVuSans-Oblique), violating the epapers2 spec *"Avoid the use of Type 3 fonts."*
- Location: all four figure PDFs (`figs/fig0_pathway.pdf`, `fig2_baseline.pdf`, `fig3_curves.pdf`, `fig4_topology.pdf`); root cause: matplotlib's default `pdf.fonttype = 3`.
- Why a blocker: epapers2's PDF validation (and IEEE Xplore downstream) flags Type 3; "Deviations from the above paper specifications could impede the review of your paper and result in rejection" (epapers2, quoted).
- Fix (applied): `matplotlib.rcParams["pdf.fonttype"] = 42` (TrueType) in `sim/analyze.py` and `sim/fig_pathway.py`; all four figures regenerated and copied into `paper/figs/`; recompiled. **Verification: `pdffonts main.pdf` → Type 3 count = 0, all fonts embedded, layout unchanged (still 5 pages, refs-only p. 5, zero unresolved citations).**

No other blocker-level defects remain. Residual items are author-side actions (Phase 5), not manuscript defects.

### Post-fix verification sweep (all green)

- Pages: 5; p. 4 ends with the conclusion; p. 5 = REFERENCES only. ✓
- Unresolved citations "??" = 0. ✓
- All fonts embedded (emb=yes for every row), no non-embedded fonts. ✓
- File size 0.28 MB ≪ 5 MB; US Letter; no security settings. ✓
- Cross-references: "(Section I)" via `\ref{sec:introduction}` renders correctly; Fig. 1 caption cites [31]; related-work additions render as [23] Jouni, [24] Gleyo, [25] Chessa, [27] Gracia-Morán. ✓
- Keywords: 5 Index Terms (within IEEE convention). ✓
- Acronym case: "STDP-trained", "NoCs", "S-CNN" render correctly after brace protection. ✓

### Section-level residual notes (all minor, none required for submission)

1. **Sec. III-C footnote 2** — "available from the author": acceptable at submission; **must** become a public repository/DOI at camera-ready (v2 Blocker 1, unchanged status).
2. **Figs. 2–4** could carry interdecile shading (data exists in `summary.json`); optional, zero-text-cost, improves robustness optics.
3. **Fig. 1** — the 594 direct sensory→DN edges already form the distinct green fan (blue = input→relay, gray = relay→DN); no further color work needed (closes v2 Polish item 10 as moot).
4. **IEEE attribution wording** for the inset is now "adapted from Dorkenwald et al. [31] (CC BY 4.0)" — compliant; remember to also declare third-party CC-BY material on the copyright form (see Phase 5).

---

## Phase 5 — Action Plan

### BLOCKER — 0 items outstanding for submission
(Type-3 fonts found and fixed; artifact repository required before camera-ready, listed below.)

### Submission checklist (author actions, in order) — Oct 22 deadline
1. **Create the code/data repository** (GitHub public; optional Zenodo DOI) with `sim/` code, edge lists, result records; update footnote 2 text to the URL — 1–2 h, strongly recommended *before* submission so reviewers can click it.
2. **Recompile a final PDF** (`latexmk -pdf main.tex`) and run the four self-checks: `pdfinfo` (5 pages), `pdffonts` (0 Type 3, all embedded), size <5 MB, no "??".
3. **Register on epapers2** (one account covers multiple submissions), upload `main.pdf` before **Oct 22, 2026 23:59 UTC−5**; resubmission/edit allowed until the deadline.
4. **Complete submission metadata**: title, abstract (paste from main.tex), keywords, author = Shuchao Gao, Waseda University (not double-blind).
5. **Select the Special Session 16.3 track** ("Intelligent Circuits and Systems for Physical Intelligence") if the submission form asks for a session/special-issue preference.
6. **Flag third-party CC-BY material** in any copyright/permissions field: Fig. 1 inset, adapted from Dorkenwald et al., *Nature* 634:124–138, CC BY 4.0.
7. **Plan IEEE copyright release + full-rate registration + attendance** for the accepted case (decision Jan 20, 2027; final paper Jan 27, 2027 per CFP).

### SHOULD-FIX — 0 items (all v2 items applied and verified)
### POLISH — 2 optional items
1. Add interdecile shading to Figs. 2–4 from `summary.json`.
2. (Camera-ready) upgrade footnote 2 to a Zenodo DOI and consider adding `--dblp`-style DOI display if the template supports it.

### Resubmission Decision
- **Not needed — first submission is go.** The manuscript clears every epapers2 specification gate, every quantitative claim is artifact-verified, the literature is current through October 2026, and the two historical weaknesses (novelty scoping, reproducibility statement) are closed.
- Effort to submission: **2–4 hours** (repo + final checks + upload). Effort to camera-ready (if accepted): **0.5 day** (DOI, copyright form, registration).
- Risk register: (a) connectome-specialist asks "so what beyond *Drosophila*" — mitigated by Sec. II close + P1–P5; (b) dependability reviewer asks why no FI framework was *used* — mitigated by the SpikeFI/SpikingJET/2025–26 contrast sentence; (c) artifact request — footnote + (ideally) live repo link.

**Final verdict: 能投 — submit after Phase 5 items 1–4. Accept-level manuscript (4.5/5 on the v2 rubric, up from 4/5).**

---

*Verification trail (2026-10-16): epapers2 authorinfo1.php fetched live (deadline extended Oct 22, notification Jan 20, 2027; Type-3 rule quoted); `pdffonts`/`pdfinfo`/`pdftotext` checks executed on the final PDF; all numbers previously re-derived from `sim/results/` remain unchanged by this round's figure regeneration (only font embedding changed); literature delta-check via paper_search returned no new competitors.*
