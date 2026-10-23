# assessment-v9 visual revision

Current main and supplement are `fly_connectome_fault_assessment_v9_visual.pdf`
and `fly_connectome_supplement_v9_visual.pdf`, matching main.tex/main.pdf and
supplement.tex/supplement.pdf. The previous named v9 PDFs remain unchanged.
The protocol, experiments, estimates and scientific limitations are identical.
See repository-root VISUAL_REVISION_V9_zh.md for current plots/builds and QA.


Current main source is main.tex with sections/v9_*.tex. The original v8 sections
and named PDFs are retained as history. Current main and supplement are both
assessment-v9; all three new cohorts and all-page QA are complete. Repository
`docs/STATE.md` identifies final builds, source bindings and release receipts.

Use the repository-root REPRODUCE.md, PROTOCOL_v9.md and PROTOCOL_v9_NOTES.md.
The new test uses24 independent core seed clusters, not288 independent trials;
stress and later action ablations remain separate. CSV export repair and
precision-range clarification do not alter any raw experiment or threshold.

Build from the repository root into a fresh staging directory:

```text
powershell -File tools/build_paper.ps1 -BuildDirectory audit/my-main-build
```

The script runs pdflatex/BibTeX/pdflatex/pdflatex and rejects undefined references,
overfull boxes, oversized floats and missing glyphs before copying main.pdf.
A TeX distribution with IEEEtran, cite, AMS, graphicx, booktabs, placeins and url
is required; no connectome or new simulation is needed. New SI uses lmodern,
longtable, geometry and caption. Main uses default IEEE conference typography,
four technical pages maximum and an optional references-only fifth. Clear all
floats and start references on a new page. Review every final page and all font
embedding/Type3 properties; byte/source checks alone are insufficient.

The preceding versioned names ending in _v9.pdf remain historical; the current
visual revision uses _v9_visual.pdf as stated above, with its own validation. No
commit, push, submission or claim of complete historical reconstruction follows
from compiling these files.
