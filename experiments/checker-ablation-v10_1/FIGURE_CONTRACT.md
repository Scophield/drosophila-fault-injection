# Figure 2 revision contract

Backend: established project Python/Matplotlib workflow. Venue: IEEE ISCAS,
single-column width 3.5 inches, existing 2.72-inch figure height. Original
Blender assets and Figures 1/3/4 are immutable.

Conclusion: the fixed additional catalogue quantifies information beyond trusted
header checks, while preserving missed errors and cross-plant boundaries.
This is a quantitative-grid composite, not an algorithm-ranking or coverage plot.

- Panels (a,b): retain the original vector tank-response and exact-delay panels
  byte-for-byte as source, without rerunning tank or changing their data/legends.
- Panel (c): replace only the old development-case bars with detected-error counts
  in four arms, for fly (45 invalid) and tank (42 invalid). Valid-control false
  rejections are stated separately. Counts have no binomial CI because cases are
  author-designed, with three source repetitions per category.
- Caption/body: define A/B/C/D, 111 cases/107 unique inputs and the fixed-additional
  rather than blind-generalization status. Full still misses six fly corruptions;
  its benefit over Native occurs only in tank on this catalogue.

Read source numbers from summary-01/summary.json. Preserve the original figure;
write new PDF/SVG/PNG and a source CSV/manifest separately. Embed TrueType text.
Verify the copied (a,b) region by rendered pixel equality. Font sizes follow the
original figure; no shrinking of paper fonts or approved scientific diagrams.
