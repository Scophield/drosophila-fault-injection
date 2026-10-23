# assessment-v9 Blender integration — current local state

Current main: paper/fly_connectome_fault_assessment_v9_blender.pdf (5 pages,
page 5 references only). Current SI: paper/fly_connectome_supplement_v9_blender.pdf
(13 pages). Both match the active TeX/PDF files. Original named v8/v9/visual
PDFs and preceding source/data ZIPs remain unchanged historical releases.

Figure 1 is now a wide Blender/model/task overview on page 2, with vector labels.
Its 410 nodes/1050 selected edges and registered v9 input/readout identities were
independently read-checked against the external model and annotation hashes.
It is not a full graph, measured neurite reconstruction or anatomically registered
fly. Quantitative figures 2/3 are byte-identical. Shorter repeated prose and a
moved figure-2 float preserve four technical pages without shrinking body fonts.

No new simulation, statistical reanalysis, threshold fitting or raw-data edits.
24 core clusters / 8 separate stress / 8 separate action clusters stay separate.
SI TeX/tables and all 13 page pixels remain identical to the previous visual SI.
All scientific qualifications and remaining Reject risks continue to apply.

Audit root: audit/blender-integration-20261023/.
Backup: baseline/; copied untouched Blender inputs: source/.
Graph check: graph-audit.json; renders: renders-01/render-manifest.json.
Figure sources/inputs: figures-03/manifest.json; editable scenes: renders-01/paper_scenes.blend.
Main build/QA: main-build-04/ and main-qa-04/.
SI build/QA: supplement-build-01/ and supplement-qa-01/.
Integrity: presentation-integrity.json; all-page visual receipt: visual-final.json.
Tests: tests-final/check.json; full validation: final-validation/validation.json.
Archive: releases/assessment-v9-blender-review.zip; manifest/receipt alongside.
Standalone ZIP byte verification: artifact-byte-check.json under the audit root.
Full sources, current commands and changes: BLENDER_INTEGRATION_V9_zh.md.

Main SHA256: 9cad0840e2a553e8dfd9d00afc646c062ca1b225afb0738879959854e43f2082
SI SHA256: 52d74fadd9b65affbbc29b42225acfb70be1cee84537bd9992662b800989d4db
The original build/audit above predates GitHub publication. The user-authorized
GitHub snapshot uses research/iscas2027-20261022; see GITHUB_SNAPSHOT.md for its
scope and byte-preservation rules. No conference submission is performed.
REPRODUCE.md continues to record the preceding full scientific release; use the
Blender-integration report for the current presentation. External model tables,
dependency caches and local ZIP archives remain separate. Source consistency
does not establish scientific generality, hardware benefits or acceptance.
