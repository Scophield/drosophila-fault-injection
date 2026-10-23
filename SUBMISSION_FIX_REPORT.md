# assessment-v6: response to the assessment-v5 review

This is a local revision of the manuscript and supporting artifact, dated
21 October 2026. No neural experiment, calibration, outcome or historical raw
record is changed. Earlier review packages are preserved.

## Applied changes

| Review item | Change and verification entry |
|---|---|
| B1: PDF links and bookmarks | Replaced `hyperref` with `url` in both sources. Printable addresses remain. `tools/qa_pdf.py` checks saved link objects, outlines, widgets, forms, encryption and PDF version. `tools/validate_revision.py` enforces these checks. |
| Method wording | Linear integration advances the dynamics; restoring stored initial states is a separate operation before each trial. |
| Metadata scope | Main results now promise every main dose, recorded control damage and selected-dose intervals, matching the supplement. |
| Selector provenance | Main Sec. IV-D identifies `audit/verified-hubs/`. All eight original JSON files, including the reconstruction caveat and manifest, are included and hashed. They are not recovered historical manifests. Table S4 reports recorded damage only. |
| Abstract and discussion | Tightened the synthesis and described the six recorded one-second exceedances precisely; retained the resource-budget and reliability limits. |
| Supplement | Table S6 points to main Eq. (3). Table S15 reports rates to two decimals and paired ratios to four; unrounded data remain in the JSON. All 16 tables and seven figures are retained. |
| Regression coverage | Saved/reopened PDF fixtures test a printable URL, an invisible-style link and bookmark, a form widget, encryption with an empty user password and a pre-1.4 PDF. |

The gate contrast retains six clusters and its zero-inclusive conditional range.
Controller comparisons remain complete feedback-law interventions; no isolated
trigger-timing effect, corrected hub effect or hardware claim is added.

## Verification and opening

Open `paper/main.pdf`, `paper/supplement.pdf`, then `REVIEW_MATERIALS.md`.
Main build sources and logs are in `audit/build-submission-v6-final/`; supporting build
sources and input hashes are in `audit/supplement-v6/`. Final regression, raw-data,
PDF feature and source checks are saved in
`audit/submission-v6-final-validation/validation.json`; its `pdf/` and `supplement/`
directories contain the rendered pages used for visual inspection.

The matched local artifact is `releases/assessment-v6-review.zip` with its
`.manifest.json` sidecar. Every included file has a SHA256 and size. External
connectome tables and dependency caches are not bundled. See `REPRODUCE.md` for
the existing build and reconstruction commands, and `ARTIFACT_README.md` for
the Git-base and dependency requirements.

## B2: external delivery remains unverified

The existing public repository does not expose this exact revision. No commit,
push, public release or conference submission is performed by this repair.
The main PDF is prepared for the paper field; the 11-page supplement and ZIP
are optional supporting files whose permitted delivery mechanism must be
established. Local packaging alone does not establish reviewer access.

After an authorized upload through a permitted mechanism, retrieve the actual
files from the reviewer-accessible location and compare their SHA256 values
with the release manifest before claiming this condition resolved. No upload,
successful retrieval or venue acceptance is asserted here.

The official PDF Help was checked on 21 October 2026:
https://epapers2.org/iscas2027/ESR/author_help.php . Its restrictions are checked
locally; portal certification and permission for supporting files remain separate.
