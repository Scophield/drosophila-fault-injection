# Reproduce V10.1

Use an existing Python 3.12 environment with the versions in requirements-saved-v10.txt. Saved-record analysis uses NumPy; plotting also uses Matplotlib and PyMuPDF. The commands below execute data processing and software tests, without rerunning neural dynamics.

## Verify the snapshot and regenerate timing tables

```text
python tools/verify_v10_1.py
python tools/analyze_trigger_timing.py --out output/reproduced-timing-01
python -m unittest discover -s tests -p "test_evidence*v10.py" -v
```

The timing entry reads all 576 original records and the distributed exact-landmark table in output/burst-end-20261025-01/all-records.csv. It verifies the raw hashes, calibrations, paired masks, prefixes and event schedules; exports all 384 healthy/fault pairs and 288 P/R pairs; and regenerates delay distributions and stage tables. Use a new output directory for each run.

## Count-domain warnings and post-burst stage analysis

```text
python tools/rescore_warnings_v10_1.py --out output/reproduced-warning-counts-01 --draws 20000
python tools/plot_warning_counts_v10_1.py --input output/reproduced-warning-counts-01/results.json --out output/reproduced-warning-figure-01
python tools/analyze_postburst_stage_v10_1.py --out output/reproduced-postburst-stage-01
python -m unittest discover -s tests -p "test_*v10*.py" -v
python tools/check_calibration_v10.py --root runs/task-v10-transfer --design runs/task-v10-design/design.json --out output/reproduced-count-calibration-01
```

Delivered re-scores are in `output/warning-counts-v10_1-02/`, Fig.4 exports in `output/warning-figure-v10_1-02/`, and the independent stage check in `output/postburst-stage-recheck-03/`. The warning entry derives exact rational cutoffs only from the original healthy validation records, retaining the registered strict `<` comparison and non-alerting ties. See `docs/WARNING_COUNT_PROTOCOL_V10_1.md` for the 19 boundary records and the distinction between saved rate bins and spike timestamps. All 44 tests pass in the saved Python environment: 20 evidence tests, 18 count-warning tests and six encoder tests. The encoder tests compare the degree-domain manuscript formula with the implementation and all 28,800 saved visual frames, including initialization and the first enabled input; they do not run neural dynamics.

Frozen registrations and historical analysis outputs remain unchanged. Historical full-matrix `analyze_task_v9.py`/`analyze_task_v10.py` entries retain their registered source-hash guards; run those analyses from their original fixed snapshots. The revised `flags` API requires an explicit validation-derived count cutoff and does not silently reuse rounded Hz thresholds. The new entry binds that cutoff without test-outcome fitting or changing neural triggers. These commands do not execute neural dynamics.

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

The distributed count-candidate PDF, timing-candidate filename and paper/main.pdf have identical bytes. Recompilation can vary PDF metadata; sources, numerical content and rendered pages provide the scientific comparison. The paper has four technical pages and a reference-only fifth page. Approved figure PDFs are already supplied, including unchanged Blender imagery. Rebuilding panel-label parentheses is optional: tools/parenthesize_panel_labels.py accepts an existing licensed Arial Bold TTF through --font-file; no system font files are distributed.

Fresh neural simulation uses the separately acquired, pinned inputs described in docs/THIRD_PARTY_INPUTS_V10.md and the frozen run configurations. Original registrations, seeds, calibrations and raw records remain unchanged.
