# Revised-Manuscript Review: ISCAS 2027
Date: 21 October 2026

**Assumed venue: IEEE ISCAS 2027, regular-paper standard, Neural Networks and Neuromorphic Engineering. Recommendation: 4/10, reject in the present form. Confidence: 4/5.**

The revision substantially improves evidential discipline: calibration reuse and exposure differences are disclosed, unsupported mechanisms and hardware protection advice are withdrawn, and the figures distinguish their endpoints. The remaining obstacle is research contribution and experimental validation. Correcting the account of an archive does not, by itself, establish a new reliability-assessment method.

I reviewed the current local PDF and all included sources, both bibliographies, IEEEtran configuration, protocol supplement, reproduction instructions and relevant code. No cover letter, response letter or manuscript appendix was found. I independently reproduced the archive analysis and inspected all five rendered pages; pixel comparisons confirm that those renders match the current PDF. Section-file locations below are under `paper/sections/`. The earlier review is preserved separately.

## Phase 1 - Understand the Paper

1. **Problem.** Which conclusions about transmission, network activity and synthetic task survival remain supported when an existing fly-connectome fault archive is reassessed with explicit endpoint and evaluation definitions?

2. **Claimed contributions and my reading.**

   - Author: "a reproducible assessment of which conclusions survive three separate endpoint definitions" (`intro.tex:7`). My reading: a descriptive reassessment of an existing experiment collection, rather than a new fault-injection algorithm.
   - Author: "identify calibration reuse and unequal episode duration" and "report corrected archive summaries." My reading: substantive evaluation corrections, especially the paired equal-exposure analysis.
   - Author: "provide a revised geometric protocol for future experiments." My reading: executable prospective methodology, tested with synthetic inputs but not yet validated using the whole-brain network.

3. **Method, in three sentences.** A 138,639-neuron LIF network uses 15,091,983 signed connection-table rows representing 54.5 million contacts. Independent Poisson input drives 104 LC4 and 210 LPLC2 cells; eight descending neurons supply rate and latency readouts under five perturbation families. Archive re-scoring compares transmission with activity-constrained transmission, while paired synthetic episodes expose calibration overlap and unequal observation duration.

4. **Experimental setup.** One connectome; 19 conditions including healthy per real/null phase; 12 trials of 600 ms per condition. F1 uses lognormal sigma 0.05/0.10/0.20/0.50; F2 deletes 5/10/25/50% of rows; F3 silences 1/2/5/10% of eligible unit outputs; F4 targets 1/2/5% hubs; F5 removes either/both sensory outputs. Principal drive is 150 Hz, with selected 75/300 Hz controls. Parameters are membrane/synaptic constants 20/5 ms, threshold/reset -45/-52 mV, refractory period 2.2 ms, delay 1.8 ms and contact gain 0.275 mV. Transmission threshold is 51.4 Hz; the joint rule also bounds rate and spikes by multiples of healthy medians. Controls include target permutation, inhibitory/composition lesions and random inhibitory lesions. Behavioral faults use four nonfrontal azimuths and three seeds; the original healthy set uses six seeds. Fault seeds are traceable, but historical open-loop stimulus streams were not explicitly reset. Median intervals use 20,000 bootstrap draws; behavioral intervals resample only three seed clusters. There are no formal hypothesis tests or established equivalence margins. Historical timestep, CPU specification and measured campaign compute are missing; approximately 2.4 GB memory and several-hour fresh campaigns are documented estimates, not verified requirements.

5. **Headline results, independently reconstructed.**

| Archived condition | Command median [95% median interval], Hz | Additional observation |
|---|---:|---|
| Healthy | 94.69 [94.06,95.42] | First spike 4.05 ms |
| F1, sigma 0.50 | 94.17 [92.19,96.46] | 99.4% rate retention |
| F2, 50% | 72.40 [71.25,74.69] | 76.5% retention; latency 5.40 ms |
| F3, 10% | 95.10 [93.65,96.56] | 100.4% retention |
| Historical F4, 1% | 119.06 [118.33,119.90] | Selector interpretation remains unresolved |
| F5, both channels | 0.00 [0.00,0.00] | 0/12 transmission passes |

Across the specified 288 fault/control records, transmission/joint passes are 276/262. Removing six reused calibration episodes leaves 18/18 non-overlapping healthy records, without establishing a new independent test. F2_50's median paired spike ratio changes from 0.3817 for whole episodes to 0.7226 within 400 ms. Full-hub twofold exceedances change from 6/12 to 0/12 over those exposures.

6. **Limitations.** One connectome/pathway, limited operating points, small samples, unseeded historical stimulus streams, missing timestep/selection provenance, a nonfunctional null, compromised legacy behavioral evaluation and unexecuted corrected whole-brain experiments. The paper now acknowledges these. It makes no supported biological-resilience, energy-efficiency, hardware-yield or mechanistic claim.

## Phase 2 - Recover the Standard

Venue inference follows `README.md:4`, IEEEtran conference mode, named authorship and four technical pages plus references. A particular special session cannot be established from the current manuscript alone.

Official pages retrieved on **21 October 2026**; none displays a document revision date:

| Source | Exact section headings used | Applicable requirement |
|---|---|---|
| [ISCAS 2027 CFP](https://2027.ieee-iscas.org/call-for-papers) | "Scope of Contributions"; "Types of Contributions" | Neuromorphic engineering is in scope; regular submissions require an original circuits-and-systems contribution. |
| [Author Information](https://epapers2.org/iscas2027/ESR/authorinfo1.php) | "Paper Specifications" | Four technical pages; optional references-only fifth page; identified authors; embedded fonts; avoid Type 3; PDF within 5 MB. |
| [Templates](https://epapers2.org/iscas2027/ESR/samples.php) | "LaTeX Templates"; "Preparation of the bibliography in LaTeX" | IEEEtran conference class and bibliography style. |

The portal lists submission closure at **22 October 2026, 23:59 UTC-05:00**. I found no public regular-paper review form or native numerical scale; the scores below are reviewer-defined, not an official ISCAS form. Tutorial evaluation criteria are not substituted.

The current PDF meets the checked specifications: five Letter pages, references only on page five, 313,346 bytes, no encryption, 21 embedded fonts and zero Type 3 fonts. This is local compliance verification, not conference-system certification.

## Phase 3 - Rubric Table

Higher is better; confidence alone uses 1-5.

| Dimension | Score | Rationale | Concrete required fix |
|---|---:|---|---|
| Overall | **4/10, reject** | Reliable reassessment remains short of a validated original research contribution. | Resolve B1-B3 before submission. |
| Confidence | 4/5 | Sources, pixels and raw statistics were checked; simulator outcomes remain unavailable. | Supply an executable whole-brain validation record; Sec. V. |
| Novelty | 4/10 | Endpoint separation is useful but not yet a demonstrated methodological advance. | Define and validate the added decision enabled by the protocol; Sec. I. |
| Technical soundness | 6/10 | Re-scoring is consistent; model provenance and cohort comparability remain limited. | Document sensory refractory differences and validate affected contrasts; Sec. III-A. |
| Theoretical depth | 4/10 | Equations define dynamics and thresholds without a new derivation or guarantee. | State the intended empirical scope; Eq. (2). |
| Empirical strength | 3/10 | Corrected behavior has no whole-brain measurements; three clusters are insufficient for broad reliability inference. | Run frozen-calibration held-out evaluations; Sec. IV-C/D. |
| Reproducibility/release | 6/10 | Local audit and hashes are strong; the public branch and simulator environment lag. | Release a matching artifact and validate its environment; Sec. I footnote. |
| Clarity | 7/10 | Current caveats distinguish records from claims, but revision history dominates. | Replace withdrawal language with a self-contained contribution; Abstract/Sec. I. |
| Significance | 5/10 | Relevant to reliability practitioners, with limited demonstrated engineering consequence. | Show a changed assessment or design decision; Sec. V. |
| Ethics/broader impact | 8/10 | Biological/hardware extrapolations are appropriately restrained. | Preserve attribution and distinguish activity limits from safety certification; Sec. V. |
| SOTA comparison | 5/10 | Relevant tools are cited without a functioning comparative experiment. | Add a matched controller or validated assay comparison; Sec. IV-C. |
| Figures/tables | 8/10 | Endpoints, units and dispersion are substantially clearer. | State Fig. 3's log scale and enlarge Fig. 1's smallest labels. |
| Bibliography | 8/10 | All 13 active references resolve; earlier major citation problems are removed. | Normalize Ref. [13]'s publication date and Ref. [7]'s preprint label. |

## Phase 4 - Detailed Findings

### Blocker Issues

**B1. The claimed assessment contribution has no demonstrated advantage beyond imposing an extra constraint.**  
Locations: `intro.tex:7`; Eq. (2); `results.tex:52`.

> "Our contribution is a reproducible assessment of which conclusions survive three separate endpoint definitions and an audit of their evaluation conditions."

A stricter acceptance set necessarily rejects at least as many trials. The 276-to-262 difference demonstrates different labels, but not that the new labels predict an independently defined resource failure or improve a controller decision. Stability for c=1.5-4 is useful sensitivity analysis, not validation of the budget.

**Fix:** Prespecify a measurable operating budget or independent reference outcome, freeze the rule using calibration data, and evaluate its added detections and healthy false alarms on new records. Alternatively, demonstrate a reproducible controller-ranking reversal after exposure matching. Frame the advance as an explicit, testable assessment result and compare it with existing benchmarking practice. Physical hardware and a new theorem are not inherently required.

**B2. The behavioral component remains an unvalidated legacy illustration.**  
Locations: `results.tex:55-59`, Fig. 4; `principles.tex:8`.

> "This revised protocol is regression-tested on synthetic inputs, but no new whole-brain outcomes are claimed."

This is accurate reporting. However, the legacy observations retain calibration reuse, scripted looming and a bearing calculation that cancels heading. The 18-record partition does not repair those dynamics. Tests use a ToySim and replace Brian2 seeding with a stub (`tests/test_revision.py:98-100`); they cannot establish neural input-response or closed-loop survival.

**Fix:** Execute the passive calibration and disjoint-seed evaluation already specified in `REPRODUCE.md:178-193`. Include healthy, F2_25/F2_50 and steering/readout controls, with a fixed survival horizon and common-window activity. Prespecify horizon/threat sensitivity and show a functioning baseline. If retaining an archive-only paper, make behavioral material illustrative throughout and replace its evidential role with a sufficiently strong validated analysis.

**B3. The headline joint-score example depends mainly on a cohort with unresolved experimental identity.**  
Locations: `results.tex:41-52`, Fig. 3.

> "The additional failures are 12 inhibitory-hub and two random-mass trials."

Twelve of fourteen extra rejections arise from historical inhibitory-hub records whose selected identities/backend are not consistently established. Numerical re-scoring remains valid, but it does not demonstrate how a controlled hub intervention changes joint reliability. The revised paper properly withdraws that causal conclusion; the remaining headline still needs a trustworthy empirical basis.

**Fix:** Report cohort-specific counts and a sensitivity analysis excluding disputed hub cohorts. Validate the scoring result with consistently generated healthy/random-lesion records. Rerun matched hub/sign controls only if restoring hub conclusions; removing an unsupported claim does not create an obligation to regenerate the removed walk-mass figure.

### Section-by-Section Feedback

| Section | Content and specific strength | Weakness and concrete edit |
|---|---|---|
| Abstract, `main.tex:42` | Quantifies retention, scoring differences and exposure sensitivity; flags overlap. | Reads partly as a response letter. Replace "We withdraw..." with "Hub records are descriptive because historical selection provenance is incomplete." Lead with the tested assessment question. |
| Introduction, `intro.tex:3-7` | Correctly distinguishes a wiring prior from validated reliability. | Contribution lacks an evaluation criterion. Add: "We test whether activity and exposure definitions change the classification of otherwise identical perturbation records." State what would count as useful added information. |
| Related Work, `related.tex:2-4` | Explicitly acknowledges An's overlap and avoids claiming the first fly perturbation study. | Add a compact comparison of substrate, functional endpoint, activity measure and validation split. Explain the experimental distinction rather than relying on a new application label. |
| Methods, Sec. III | Defines fault semantics, seed limitations and Eq. (2)'s references. | State wrapper deviations from upstream, identify the 288-record composition, and put the behavioral protocol before its results. Suggested sentence: "Our wrappers retain a sensory refractory interval, unlike the upstream stimulation routine." |
| Experiments, Sec. IV | Equal-exposure analysis directly corrects the interpretation of F2_50 activity. | Add per-cohort scoring and independent evaluation; report uncertainty for retention/latency contrasts, including healthy-reference uncertainty. |
| Discussion, Sec. V, lines 2-8 | Separates spike counts from energy and hardware mapping. | Specify an actionable assessment consequence. Add: "Comparisons require a declared exposure window and separate functional and activity criteria." Avoid presenting a convention alone as a new validated method. |
| Conclusion, `principles.tex:10` | Ends with conditional observations rather than biological generalization. | Write: "The archive demonstrates endpoint sensitivity at the tested operating point; controlled prospective experiments must establish generality." |
| Appendix/supplement | No manuscript appendix; `PROTOCOL_v2.md` contains all doses, partitions and semantics. | Provide a versioned reviewer-accessible supplement and cite its exact location/version; do not assume reviewers can discover local audit folders. |

### Equations and Implementation

**Eq. (1):** Units and linear subthreshold dynamics are consistent with the inspected wrappers. Without events or refractory periods, its exact solution is
\[
g(t)=g_0e^{-t/5},\quad
v(t)-v_0=(v(0)-v_0)e^{-t/20}+\frac{g_0}{3}(e^{-t/20}-e^{-t/5}),
\]
with t in milliseconds. Both modes decay; this supplies no whole-network robustness theorem.

A material implementation distinction remains: upstream `model.py:92,103` sets stimulated neurons' refractory periods to zero; `sim/engine.py:66` and `sim_vision/vision_core.py:63` retain 2.2 ms. This is not an internal contradiction in Eq. (1), but it limits equivalence to the released model. Disclose it and compare 0 versus 2.2 ms before transferring conclusions across implementations.

**Eq. (2):** Dimensionally valid with rates in Hz. The joint-pass set is a subset of transmission passes by construction; do not treat that inclusion as evidence of predictive validity.

**Other calculations:** F1's factor has expectation one and CV = sqrt(exp(sigma squared)-1), giving 53.3% at sigma=0.5. F2 retention is 0.764576 and latency increases by 33.33%. These checks pass. No theorem or proof appendix remains; no missing proof is alleged.

### Every Figure and Table

| Item | Claim, support and presentation | Required experiment/reporting and reproducibility |
|---|---|---|
| Fig. 1, Sec. III-A | Illustrates anatomical routing/injection sites; cannot validate an escape computation. Smallest annotations/inset are difficult at final size. | Enlarge labels and provide generator/input provenance; no statistical bars are needed for a schematic. |
| Table I, Sec. IV-A | Summarizes selected F1-F5 doses; numbers and median intervals reproduce. "Pass" is ambiguous. | Rename to "Transmission pass"; retain explicit historical F4 labeling. Cite the complete-dose supplement and archive-analysis script. |
| Fig. 2a/b, Sec. IV-A | Supports conditional rate loss and first-spike delay under deletion. Separate Hz/ms axes and percentile caption are correct. | Add the 5% tick and uncertainty on healthy-relative effects; include another operating point or activity state for generality. Reproduced from main JSONL records. |
| Fig. 3, Sec. IV-B | Shows historical activity distributions and random-control tails, rather than a corrected sign-specific contrast. | State logarithmic scaling explicitly; use matched selectors/backend if making hub comparisons. Plot generation and raw values are traceable. |
| Fig. 4a, Sec. IV-C | One selected separation trace illustrates termination; metres, milliseconds and collision boundary are clear. | Add cohort survival/termination summaries; independently test the corrected protocol. One trace cannot estimate reliability. |
| Fig. 4b, Sec. IV-D | Demonstrates exposure-dependent paired ratios; logarithmic axis and calibration markers are appropriate. | Add seed-level summaries, label the twofold line and show several prespecified windows. Generated paired values reproduce. |

The first 400 ms is explicitly post-hoc and avoids early termination; that correction is appropriate. It may miss later hyperactivity, so report it alongside episode outcomes rather than selecting whichever endpoint favors a conclusion.

Three seed clusters permit only **27 ordered cluster-resampling draws** before repetition. Exact enumeration gives only 4-7 distinct median values for these conditions. Drawing 20,000 times does not increase independent information. Keep the descriptive caveat, display cluster values and collect more independent seeds for confirmatory inference. The 288 deliberately mixed records are not a population sample from which to estimate a universal fault-failure rate.

### Related Work and Bibliography

**Must discuss for novelty:** An is already cited as [4], DOI [10.64898/2026.09.19.752860](https://api.biorxiv.org/details/biorxiv/10.64898/2026.09.19.752860). The official API abstract reports matched-budget operators, several circuits, state dependence and over-excitation. Explicitly explain the incremental result relative to that study. I did not obtain its full text and make no claim about an identical three-endpoint protocol.

**Should cite for context:**

- Colucci, Steininger and Shafique, **enpheeph**, IROS 2022, [arXiv:2208.00328](https://arxiv.org/abs/2208.00328), DOI 10.1109/IROS47612.2022.9982181: an omitted SNN fault-injection framework relevant to Sec. II's tool coverage.
- Gleyo and Girau, **Population coding to improve fault tolerance of neuromorphic networks in regression tasks**, DATE 2026, DOI [10.23919/DATE69613.2026.11539446](https://doi.org/10.23919/DATE69613.2026.11539446): useful output-based robustness context; present in the bibliography database but not cited in the paper. Metadata/abstract were available; HAL full text was blocked.

No omitted paper was verified to refute the current narrowly stated contribution. Bibliography expansion alone will not resolve B1.

All 13 active references resolve through CrossRef/arXiv. Ref. [13] combines a 2023 online-publication year with volume 84's **February 2024** issue; normalize to 2024 or explicitly distinguish online-first publication. [PubMed record](https://pubmed.ncbi.nlm.nih.gov/38096757/). Add an explicit arXiv identifier to [7]. The unused `refs-full.bib` still contains obsolete metadata; distinguish it from the compiled bibliography.

### Additional Line Edits and Release Readiness

- `main.tex:42`: Change "18 non-overlapping healthy records" to "18 records without exact calibration-scenario overlap"; shared seeds remain.
- `results.tex:43`: Retain the iid-reference qualifier on the Wilson interval; it does not resolve selector uncertainty.
- `results.tex:59`: Replace "Survival counts" with "Recorded collision-free counts" for legacy episodes.
- `results.tex:71`: Replace "bootstrap intervals" with "descriptive three-seed bootstrap intervals."
- `intro.tex:7`, artifact footnote: identify the reviewed revision. The public `submission` branch still resolves to `051dcb6a3123841041a34d3b43395e2841975879`; its [source](https://raw.githubusercontent.com/Scophield/drosophila-fault-injection/submission/paper/main.tex) contains the earlier abstract. The release mismatch affects reproducibility, not venue-format compliance.

## Phase 5 - Prioritized Action Plan

**BLOCKER - 3 items**

1. Define one original, testable assessment claim and demonstrate its value against an independent outcome or functioning comparative baseline.
2. Execute frozen passive calibration and held-out whole-brain evaluations, or replace the legacy behavioral evidential role with a validated archive-only result.
3. Recompute headline scoring by cohort, isolate disputed hub records, and validate the remaining conclusion using consistently generated interventions.

**SHOULD-FIX - 4 items**

1. Document and test the sensory refractory difference and validate the actual simulator environment.
2. Increase independent seed coverage, propagate reference uncertainty and report cluster-level outcomes.
3. Release a version matching the reviewed PDF, scripts, supplement and source hashes.
4. Expand the closest-work comparison and define operating-point, exposure and horizon sensitivity.

**POLISH - 3 items**

1. Replace revision-history language with a standalone research narrative.
2. Clarify Table I's pass column, Fig. 3's scale and Fig. 4's reference line.
3. Normalize publication dates and preprint identifiers.

**Resubmission decision:** The manuscript is more accurate and readable, but it is not one editing pass from acceptance. The minimum bar is a clear incremental research result plus controlled evidence supporting it. A new mechanism, hardware deployment, multiple biological connectomes and rerunning withdrawn graph curves are not mandatory for the narrowed claim. Estimate **2-4 person-weeks** for environment validation, a focused experiment campaign, analysis and rewriting; broader hardware claims would require additional work.

Verification: all main archive-analysis outputs reproduced; 449 raw-source hashes and the previously validated source hashes are unchanged; all five inspected renders match the current PDF. The existing 23-test pass remains applicable to unchanged code but was not rerun. No whole-brain simulation, manuscript edit, commit, push or submission was performed during this review. Evidence is saved in `audit/rereview-2026-10-21/`.

