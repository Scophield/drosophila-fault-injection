# Count-canonical warning figure contract

## Scientific role

Core conclusion: the tested frozen command, activity and exact-state forecast operating points produce different missed-contact and false-alarm rates, with sparse contact support and whole-seed uncertainty. The command decision uses the validation-derived exact count threshold with the original strict comparison; the figure does not select a threshold, claim a neural monitoring algorithm, compare matched-information ROC curves, or infer a causal mechanism.

Panel (a) shows subsequent-contact miss rates, panel (b) false alarms among contact-free tasks. Each has RF-0/A/B rows and the same three criterion encodings. Counts, denominators and intervals come only from the freshly executed canonical analysis. All 576 frozen test records remain included; independent seed-cluster counts are 24/12/12. Resampling retains both bearings, both laws and all three conditions within a seed. Zero-width/class-conditional empirical intervals do not establish zero population error; positive-class support remains 12/2/1 independent clusters.

## Visual and export contract

- Archetype: paired quantitative grid at the existing single-column footprint, 3.5 × 2.55 inches.
- Backend: the project's existing Python/Matplotlib workflow, used for plotting, previews, exports and visual QA.
- Existing semantic palette: blue circle = Command; orange triangle = two-sided Activity; purple square = Forecast. Markers supplement color. The forecast uses exact simulated state and pending actuation, and is explicitly labelled as not neural-only.
- Preserve the existing axes: misses 0–100% with edge padding; false alarms 0–40% with edge padding. Reject data that would be clipped rather than hiding it.
- White background; Arial; all nonempty labels at least 7.5 pt; embedded TrueType PDF fonts (`pdf.fonttype=42`); editable SVG text. Panel labels directly contain parentheses: `(a)`, `(b)`.
- Deliver one PDF, one editable SVG, one 600-dpi PNG, a nine-row source CSV and a figure manifest with source/script/output hashes. New output directories are mandatory.
- No change to Fig. 1–3, Blender assets, original records, registrations or calibrations. The script reads the new analysis product and writes only its fresh output directory.

The canonical figure is `v10_1_warning_count`. Its source table preserves counts and unrounded proportions/intervals; percentages are only a display transformation. Pointwise 95% whole-seed bootstrap intervals and the registered random seeds remain analysis obligations, not graphical estimates.
