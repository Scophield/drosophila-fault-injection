# assessment-v8: current review materials

This index identifies the complete local package for review. It does not claim
submission, remote publication, or that the conference accepts ZIP supplements.

| File | Purpose | Reviewer needs |
|---|---|---|
| `paper/fly_connectome_fault_assessment_v8.pdf` | Five-page IEEE paper | Primary manuscript; references share the five-page limit |
| `paper/fly_connectome_supplement_v8.pdf` | Consolidated Supplementary Information | 22 tables, nine figures, per-seed matrix and protocol |
| `REVISION_V8_REPORT_zh.md` | Chinese response map | Changes, actual findings and remaining boundaries |
| `releases/assessment-v8-review.zip` | Matched source and evidence artifact | Local audit/reproduction package |
| `releases/assessment-v8-review.manifest.json` | SHA256 and size per bundled file | Verify exact revision and PDF identity |
| `audit/overview-v8/assessment_overview.pdf` | Standalone main Figure 1 | Current source binding; vector PDF, editable SVG and 600-dpi PNG |
| `OVERVIEW_FIGURE_REPORT.md` | Overview design, scope and verification | Conceptual diagram; no additional experimental results |
| `ARTIFACT_README.md` | Opening and reproduction entry | Dependencies and Git/archive-check requirements |
| `SUBMISSION_FIX_REPORT.md` | Previous PDF repair and remaining delivery condition | Local preparation versus verified remote access |

Use the current main PDF as the paper upload. If the submission system provides
a supporting-materials field, supply the current supplement there. Supply the
matching ZIP only if that mechanism permits it, or through an authorized stable
repository/release. The public repository branch alone predates this revision.
Do not state that reviewers can access these local files until the selected
submission or publication action is actually completed and verified.

The supplement is standalone; earlier protocol and repair documents are retained
in the artifact as historical provenance. Their old status statements are
superseded. The current manuscript and supplement do not require new experiments
to reconstruct the reported numbers.

## Current evidence map

| Evidence | Supplement | Machine-readable source |
|---|---|---|
| Campaigns, constants, endpoints and trigger | Table S1, Section 2 | Frozen calibration and run manifests |
| Every main F1--F5 dose | Table S2 | `audit/assessment-v3-base/revision_analysis.json` |
| Cohorts and recorded control damage | Tables S3--S4 | `audit/assessment-v3/assessment.json`, archived JSONL |
| Post-hoc selector reconstructions | Main Sec. IV-D; supplement Sec. 4 | `audit/verified-hubs/*.json`; these are not recovered run manifests |
| Legacy calibration partitions and ratios | Tables S5--S8, Figure S3 | `audit/horizons-v4/horizons.json` and archived episodes |
| First held-out directional and seed outcomes | Tables S9--S11, Figure S1 | `audit/prospective-v3.json` |
| Paired new-seed controls and uncertainty | Tables S12--S14, Figure S2 | `audit/controls-v4/controls.json` |
| Refractory variant and compute | Tables S15--S16 | `audit/refractory-v4/summary.json` |
| Archived diagnostic figures | Figures S4--S7 | Figure manifests and archived measurements |
| Conceptual model and assessment overview | Main Figure 1 | `audit/overview-v8/overview_manifest.json` |
| Mapped pathway retained from v6 | Figure S8 | `audit/pathway-v4/pathway_manifest.json` |
| Frozen controller-by-fault matrix, every seed and paired loss/gain | Tables S17--S20 | `audit/controller-fault-v8/cross.json`, `pairs.csv` |
| Same-law activity and threshold/collision counts | Tables S21--S22, Figure S9 | `thresholds.csv`, `audit/cross-figures-v8-final/` |
| Independent raw-outcome and exact-bootstrap verification | Validation | `audit/cross-audit-v8/audit.json` |

The earlier healthy gate contrast consists of two improving, zero worsening and
four unchanged seed clusters, with a conditional range containing zero. The v8
matrix directly compares fault losses under each law; all losses and gains are
retained, with bearings and conditions kept together within six seed clusters.
The response map reports whether the actual interaction ranges resolve a difference.
No population reliability, predictive safety budget or hardware tolerance is inferred.

The main PDF contains printable URLs without interactive links or bookmarks.
The standalone supplement also omits interactive features but retains page numbers
for navigation. It is supporting material. Venue permission for that format and
the ZIP must be confirmed before either is supplied. No remote URL for this exact
revision or successful reviewer download has been established.
