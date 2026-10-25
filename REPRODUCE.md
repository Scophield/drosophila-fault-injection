# Reproduce V10.1

Use an existing Python 3.12 environment with the versions in requirements-saved-v10.txt. Saved-record analysis uses NumPy; plotting also uses Matplotlib and PyMuPDF. The commands below execute data processing and software tests, without rerunning neural dynamics.

## Verify the snapshot and regenerate timing tables

```text
python tools/verify_v10_1.py
python tools/analyze_trigger_timing.py --out output/reproduced-timing-01
python -m unittest discover -s tests -p "test_evidence*v10.py" -v
```

The timing entry reads all 576 original records and the distributed exact-landmark table in output/burst-end-20261025-01/all-records.csv. It verifies the raw hashes, calibrations, paired masks, prefixes and event schedules; exports all 384 healthy/fault pairs and 288 P/R pairs; and regenerates delay distributions and stage tables. Use a new output directory for each run.

## Regenerate exact-landmark analysis and validation

```text
python tools/analyze_burst_end.py --out output/reproduced-burst-01 --draws 10000
python tools/validate_burst_end.py --input output/reproduced-burst-01 --out output/reproduced-burst-check-01
```

The recorded outputs are retained unchanged in output/. Current public execution protocols are in docs/V10_1_TIMING_PROTOCOL.md and docs/V10_1_BURST_PROTOCOL.md. Frozen metadata retain the original generation-time source and plan identities. Exact original analysis source copies are in provenance/analysis-source/; public execution entries change only the protocol-document paths. Fresh executions record their current source, protocol, environment and commit identities separately. Statistical units remain whole seed clusters within each RF.

## Compile the paper

With an existing IEEEtran installation, run from paper/:

```text
pdflatex main_v10_1_timing.tex
bibtex main_v10_1_timing
pdflatex main_v10_1_timing.tex
pdflatex main_v10_1_timing.tex
```

The distributed named PDF and paper/main.pdf have identical bytes. Recompilation can vary PDF metadata; sources, numerical content and rendered pages provide the scientific comparison. The paper has four technical pages and a reference-only fifth page. Approved figure PDFs are already supplied, including unchanged Blender imagery. Rebuilding panel-label parentheses is optional: tools/parenthesize_panel_labels.py accepts an existing licensed Arial Bold TTF through --font-file; no system font files are distributed.

Fresh neural simulation uses the separately acquired, pinned inputs described in docs/THIRD_PARTY_INPUTS_V10.md and the frozen run configurations. Original registrations, seeds, calibrations and raw records remain unchanged.
