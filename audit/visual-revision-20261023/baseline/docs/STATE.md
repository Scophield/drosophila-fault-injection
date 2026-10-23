# assessment-v9 final local release

Completed independent evidence: core 288/288 (24 seed clusters), angle stress
96/96 (eight separate clusters), action diagnostic 64/64 (eight other clusters).
All nine neural workers exited zero. Each full cohort passed independent input/
geometry replay; core/stress also passed separate arithmetic checks. Development
and validation (74 records) are not pooled into test inference.

Core wall time 14393.307 s; stress 4725.465 s; action diagnostic 3142.772 s.
Final lightweight suite: 59 passed, zero failures/errors/skips, at
`audit/acceptance-v9/tests-final-02/check.json`. Original export failure and
minimal exportfix are documented, with frozen sources unchanged.

Final main build: `audit/acceptance-v9/main-build-04/`.
Final SI build: `audit/acceptance-v9/supplement-build-02/`.
QA: `main-qa-04/`, `supplement-qa-02/`; actual visual receipt: `visual-final.json`.
Main has five US-letter pages, page5 references only; SI has13 pages.
All fonts embedded, no Type3, undefined citations, overfull boxes, clipping or
interactive annotations found. This is local review, not portal certification.

Main SHA256: `fa8f358a284577b088b4d76a683f74413318b01f1986743a7d50ee1db8f90eac`.
Supplement SHA256: `ecd0f80581515d6ae48179a61680864c579722d64e1e816a564df23f4bda238a`.
Named v9 PDFs match `paper/main.pdf` and `paper/supplement.pdf` exactly.

Final consistency report: `audit/acceptance-v9/final-validation/validation.json`.
ZIP: `releases/assessment-v9-review.zip`, with `.manifest.json` and `.receipt.json`.
Standalone byte check: `audit/acceptance-v9/artifact-byte-check.json`.
These receipts establish actual packaging/check status, not a public release.

No commit, push or submission. Public main alone may be older. Novelty, single
model/RF/task scope, unmatched healthy reserve, sparse failures and no hardware
validation remain material Reject risks; read `FINAL_REVIEW_V9_zh.md`.
Historical hub reruns and missing source metadata remain unresolved.
