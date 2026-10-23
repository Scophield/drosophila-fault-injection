# assessment-v8 local review artifact

Open `paper/fly_connectome_fault_assessment_v8.pdf` and
`paper/fly_connectome_supplement_v8.pdf` for the matched manuscript and
standalone current supplement. `REVIEW_MATERIALS.md` indexes the upload-ready files
and evidence; `REVISION_V8_REPORT_zh.md` maps the major-revision responses.
`SUBMISSION_FIX_REPORT.md` records the previous PDF repair.
`EDITORIAL_FIX_REPORT.md` records the previous editorial stage.
`CONTROL_FIX_REPORT.md` and `PROTOCOL_v2.md` through `PROTOCOL_v4.md` are historical
revision records. `paper/PROTOCOL_v8.md` is the current factorial protocol.
The supplement supplies all 22 current tables and nine
supplementary figures without requiring a reader to navigate old status text.

The ZIP contains manuscript sources, included figures, historical raw records,
new whole-brain trajectories, analysis, tests and validation evidence. Its
`MANIFEST.json` lists each included file's SHA256. It does not include Git
metadata, dependency caches or the external connectome tables.

## Reproduce the measurements

Use CPython 3.13 (3.13.15 was exercised) with `requirements.txt`. The archive
analysis and plotting do not require Brian2 execution or the external connectome.
Run the commands at the top of `REPRODUCE.md` into new output directories.
The saved prospective summary can be recomputed directly from the included
calibration and 48 original test episode JSON files. The additional 48 paired
controller episodes and 12 refractory sensitivity runs are included separately;
their summaries can also be reconstructed without new neural execution.
The v8 matrix adds 48 fault episodes and reuses 24 of the paired healthy-control
episodes; it does not add 72 independent simulations. All 72 records, exact neural
source snapshots, calibration, per-pair CSV and threshold tables are included.

The simulation provenance and Git archive-integrity checks require a Git
checkout. Clone `https://github.com/Scophield/drosophila-fault-injection`, select
the historical base commit `051dcb6a3123841041a34d3b43395e2841975879` in a fresh
checkout, then extract this ZIP over that checkout. Preserve its `.git` directory.
The included files supply the current revision; the public branch alone does
not. Use a fresh checkout to avoid overwriting unrelated local edits.

Fresh whole-brain runs additionally require the external inputs described in
`REPRODUCE.md`, with their expected hashes. The bundle is not a redistributable
copy of those tables. NumPy code generation is exercised; a Cython compiler
environment is not validated. New batches include their exact generating Python
source snapshots. Older geometry-v3 aggregate source hashes do not imply that
every generation version was preserved; that limitation is disclosed.

Post-hoc hub selector files are included at `audit/verified-hubs/`, with their
original provenance manifest and caveat. They reconstruct selectors using known
code/data and do not recover missing historical run identities or add simulations.

For PDF preflight, run the following with a new output directory:

```text
python tools/qa_pdf.py --pdf paper/main.pdf --out audit/my-pdf-qa --submission
```

Printable
URLs are retained; clickable links, bookmarks, widgets and encryption are rejected.
See `audit/revision-v8-release-check/validation.json` for the saved release check.

## Interpret the evidence

In the first prospective campaign (seeds 6--11), healthy, 25%-deletion,
50%-deletion and readout-disabled collision-free counts
are 5/12, 4/12, 0/12 and 0/12 at one second. These are six seed clusters at two
bearings, with strong directional asymmetry. They do not establish a broadly
reliable escape controller or a predictive safety budget. Historical hub
identities remain uncertain; corrected hub and hardware claims are excluded.
The v8 six-condition matrix uses seeds 12--17. Its primary fault comparison is
same-law paired loss and gain, with gated-minus-original net-loss interactions;
healthy controller success differences alone do not measure fault tolerance.

This is a matching local artifact, not a remote release or conference submission.
The material index identifies what must be supplied to reviewers through a
permitted mechanism; file preparation does not establish external accessibility.
