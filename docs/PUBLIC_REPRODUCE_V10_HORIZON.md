# Reproduce the V10 horizon revision

Use a new checkout of `artifact/iscas2027-v10-horizon` and record its full HEAD.
No dependency installation or new neural simulation is performed by the commands
below. An existing Python environment needs NumPy for checker tests; plotting also
needs Matplotlib and PyMuPDF. Original pinned environments and external inputs are
described in the preserved V10 reproduction/input documents.

## Saved-record checks and descriptive plot

```text
python -m unittest discover -s tests -p "test_evidence*v10.py" -v
python tools/plot_horizon_v10.py --out output/new-horizon-01
python tools/check_evidence_v10.py --out output/new-evidence-01
```

Always use new output directories. The plot verifies the original 288 RF-0
record hashes, selects 96 P/R 50%-deletion records and exports cumulative first
contacts plus 900/1000-ms counts. Whole-seed independent support stays 24; no new
CI or p-value is generated. The saved summary uses Windows path separators; this
plot entry was verified on Windows. Original Figure3(a-c) is imported unchanged
from `paper/figs/v10f_rf.pdf`; the current composite is `v10h_rf.pdf`.

The checker command regenerates small tank examples and selected corruptions,
not neural equations. Its repeat is not an independent scientific cohort.
`test_evidence_schema_v10.py` adds core-type regression tests separate from the
original 11 common/3 native challenge types. Arbitrary native objects and neural
execution authentication remain outside the contract.

## Paper

With an existing IEEEtran LaTeX installation, work in `paper`:

```text
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Active named source is `main_v10_horizon.tex`; `main.tex` has identical bytes.
`sections/v10h_*.tex`, unchanged `sections/v10f_methods.tex`, `refs.bib` and the
four referenced figure PDFs are included. `PUBLIC_SCOPE.json` binds the checked
3,393,378-byte PDF (SHA256 7ac89fa92507d6529db773d0320821c4556e32d1c0fe1b8a4ceb4ad40eb319e1).
All five pages were rendered, all 29 font entries embedded, no Type3/overflow or
undefined references found; page5 is references only. This is local QA, not
submission-portal certification.

Saved-record analysis/replay needs no external matrices. Fresh neural runs need
separately acquired hash-matched inputs and substantial resources; they are not
part of this revision. Preserve original generating snapshots and frozen seeds.
