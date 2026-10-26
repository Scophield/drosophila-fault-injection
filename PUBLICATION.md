# V10.1 publication identities

Current candidate: `paper/iscas2027-v10.1-count-candidate.pdf`

PDF SHA256: `35eb9d3e96a2f45317a3f6c5205d5a78683be4e067d6cf155532175cb44be622`

Active source: `paper/main_v10_1_timing.tex = paper/main.tex = paper/main_v10_horizon.tex`.

The timing-candidate filename and `paper/main.pdf` are byte-identical PDF aliases.

## Engineering candidate

Repository branch: `research/v10.1-abstract-context`.

The current abstract follows the author-provided collision-first wording, with
fact-preserving compression for four technical pages. Its source/PDF bytes are
bound by PUBLIC_SCOPE.json and the enclosing commit. Publication to this
independent branch is authorized; formal submission has not been performed.
See [the current abstract note](docs/ABSTRACT_FINAL_V10_1.md).

Preserved manuscript stages: abstract background parent
`37becae465a563679bf6db2d668fe01b1779adce`, clarification parent
`9efb38678373acaaf9427e7aad5331ed73734606`, and engineering baseline
`0966a17d035c191891b3ea54c3ee2c9b68723319`. Their stage-specific local notes
remain archived; the current publication status is stated here.

- Preserved scientific/manuscript baseline: `22999d28d8fe22f863fc8f62eaa45a57256083d0`.
- Pre-scoring plan/labels/fixtures commit: `246352cff3d0ca9f7e3e9d7ac5158fd4cd734482`.
- Executed code/data, costs, historical impact and figure exports: `b29f08970f7749c916a472e835517547d832e6cc`.
- The manuscript is a child of the executed code/data commit and cites that fixed
  snapshot. Its own checkout commit and `PUBLIC_SCOPE.json` bind the final
  source/PDF bytes; no self-referential future commit is inserted into the paper.

The author-designed additional evaluation has 111 case IDs / 107 distinct inputs,
87 corruptions and 24 valid controls (20 distinct). It is not blind testing.
The complete unchanged common/native checkers detect 81/87 in combination,
versus 36/87 for trusted-header checks, with zero valid-control rejects and six
retained misses. Separate re-scoring of 72 V8 records quantifies actual reporting
impact; those records are not pooled with 576 current neural episodes.

The engineering baseline replaced only Fig.2(c). The clarification parent
changed no figure asset; Fig.1's caption distinguishes its earlier development
challenges from the additional catalogue. All frozen scientific records,
calibrations and registrations remain unchanged. The engineering baseline
retained the original 44 regressions and added ten; the clarification parent reran the same
54 tests. The abstract-only child preserves their source hashes. The PDF has four technical pages and a reference-only fifth page.
Current document checks are in `audit/v10_1-abstract-final/`; the background-only
checks in `audit/v10_1-abstract-context/` and prior clarification
checks in `audit/v10_1-final-clarifications/` and engineering checks in
`audit/v10_1-engineering/` remain archived unchanged. Numerical code is unchanged;
this round reruns document/integrity checks, retaining the parent's 54-test result. See also
`docs/ENGINEERING_EVALUATION_V10_1.md` and `ENGINEERING_SCOPE.json`.

## Scientific provenance retained

- Exact-count/stage implementation: `d55bb27ae0f8e04ff425a76f47f86d90bd93f835`.
- Count-warning manuscript baseline: `f78942d12fe9978353b3390f649b07a5ddb413b3`.
- Published timing baseline: `75313d7740491e7f7830e2fc554c21e1aaefe655`.
- Frozen V10: `69dfd2ed9e8fe597ae293398fe58a5d36fef2b7e`, also in `paper/frozen-v10-69dfd2e/`.
- Generating data/source snapshot: `986ff54193fee6a1b95815499a4a3477b15ea49a`.
- Earlier schema/horizon snapshot: `126e265ef1a0bb49d2a3103ff47b0c9077acdcc0`.
- Full research scientific baseline: `43bcd4d6a99b2d9b258cf8a198a4545d237b5c39`.

Original neural records, registrations, calibrations and historical analysis files
are unchanged. Integer-warning labels and intervals remain unchanged. New
engineering outputs are separate and include source/input hashes and execution
metadata. No neural rerun, calibration, threshold fit or new confirmatory test
was performed. Existing fixed versions and main remain separate.
