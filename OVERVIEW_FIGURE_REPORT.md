# assessment-v7: intuitive model and assessment overview

This local visual revision adds a conceptual main Figure 1, retaining every
measured result. No neural experiment is executed. The assessment-v6 ZIP remains
available as the previous matched package; current loose PDFs are assessment-v7.

The figure's conclusion is that transmission, network activity and bounded task
outcome require separate reporting with declared cohorts, exposure and control
laws. The three panels show model flow, distinct endpoints and assessment
conditions. Visual feedback is explicitly confined to geometric tests. The
314 sensory cells, 138,639 model neurons and eight command cells follow the
existing methods. Edges, icons and traces are conceptual; none is a measured
connectivity map, spike train or behavioral trajectory.

The Python script `tools/plot_overview_v7.py` exports a 3.5 x 2.65 inch vector
PDF, text-editable SVG and 600-dpi PNG into `audit/overview-v7-final/`. Its manifest
binds the generator, model descriptions and output files by SHA256. Font sizes
are 6.2-9 pt at the specified figure size. The orange fault label also uses an
arrow, so its meaning does not depend on color alone. No statistical comparison
or new error bar is introduced in this schematic.

The overview replaces the previous pathway in the paper and appears on page one.
The original mapped pathway is byte-preserved as Supplementary Figure S8. Its
selection rule, contact encoding and provenance limits remain in the caption.
The other seven supplementary figures and all 16 tables are retained. Repeated
introductory and concluding prose is shortened to fit the new graphic; fonts,
page geometry, scientific values and the references are unchanged.

Main build sources/logs: `audit/build-overview-v7-final2/`.
Supplement build sources/logs: `audit/supplement-v7-final/`.
Final checks and page renders: `audit/overview-v7-final-validation/`.
Matched artifact: `releases/assessment-v7-review.zip` with a per-file hash/size
manifest. The final validation covers overview input/output identity, historical
data integrity, source matching, PDF fonts and prohibited interactive features.
Visual inspection covers the standalone figure and the rendered main and
supplementary pages. A successful build or hash check alone is not visual QA.

This work prepares local materials only. Publication, submission, venue
permission for supporting files and successful reviewer retrieval remain
unverified, as described in `REVIEW_MATERIALS.md`.
