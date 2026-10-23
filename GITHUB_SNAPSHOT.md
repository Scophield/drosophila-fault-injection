# GitHub research snapshot

Branch: `research/iscas2027-20261022` in
[Scophield/drosophila-fault-injection](https://github.com/Scophield/drosophila-fault-injection/tree/research/iscas2027-20261022).
Scientific base: `051dcb6a3123841041a34d3b43395e2841975879` on submission.
Use the branch's Git commit as the published version identifier. Main and
submission remain earlier revisions; this update does not merge into them.

## Current paper

- Main: `paper/fly_connectome_fault_assessment_v9_blender.pdf`, identical to
  `paper/main.pdf`, five pages with page 5 references only.
- Main SHA256: `9cad0840e2a553e8dfd9d00afc646c062ca1b225afb0738879959854e43f2082`.
- SI: `paper/fly_connectome_supplement_v9_blender.pdf`, identical to
  `paper/supplement.pdf`, 13 pages.
- SI SHA256: `52d74fadd9b65affbbc29b42225acfb70be1cee84537bd9992662b800989d4db`.
- Source: `paper/main.tex`, `paper/sections/v9_*.tex`, figures and bibliography.

This snapshot includes the complete verified Blender-review source/data contents,
existing tracked historical results, the frozen generating code and registrations,
all 288 core / 96 separate stress / 64 separate diagnostic records, development
history, derived analyses, input/geometry replay and audit results. Cohorts are
not pooled. Selected Blender data and editable scenes are included. The independent
review text added after this validated snapshot remains local and is not represented
as an audit of these published files.

The pre-publication archive's 3,915-member SHA256 manifest is preserved at
`releases/assessment-v9-blender-review.manifest.json`, with its receipt. Publication
updates only entry documentation and Git configuration files beyond that snapshot;
scientific files and both PDFs retain their verified bytes. The exact-byte check
at `audit/blender-integration-20261023/final-validation/validation.json` is the
source/PDF/test binding. It records 59 passing tests, with no skipped tests, and
complete input/geometry checks on all three cohorts. `artifact-byte-check.json`
verifies the local pre-publication ZIP independently.

The local ZIP (185,985,383 bytes, SHA256
`1a023c6b732fc6843c0e01cdb25c4746084403f8b255f14c93386090636a30ce`)
is not uploaded as a Git file or GitHub Release asset. Its contents are available
as ordinary versioned source/data in the branch. External model matrices,
dependency caches, task metadata and temporary runtime directories are excluded.
They remain on the local machine; no files are deleted by publication.

`.gitattributes` disables automatic newline conversion because registrations and
audit manifests bind exact bytes, including existing CRLF/LF choices. This avoids
fresh-clone hash mismatches caused by host Git newline defaults. It does not
change the simulation protocol or create cross-platform bit-identical dynamics.

README and STATE now describe branch distribution. Historical reports and archive
receipts retain their original local/unpublished wording and creation provenance.
The scientific limitations and outstanding historical metadata gaps are unchanged.
Publication does not run new experiments, submit to a conference, or imply acceptance.
