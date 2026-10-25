# V10.1 publication identities

Current candidate: `paper/iscas2027-v10.1-count-candidate.pdf`

PDF SHA256: `97a936f912e904472fd119b4d53941319fee48a09848cbf658ce1c658ea173b6`

Active source: `paper/main_v10_1_timing.tex = paper/main.tex = paper/main_v10_horizon.tex`.

The timing-candidate filename and `paper/main.pdf` are byte-identical PDF aliases.

## Engineering candidate

Branch: `research/v10.1-engineering-ablation`.

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

Only Fig.2(c) is replaced. Fig.2(a,b), original Fig.1/3/4 assets and all frozen
scientific records/calibrations/registrations remain unchanged. The original
44 regressions are retained and ten new tests added. The PDF has four technical
pages and a reference-only fifth page. See `docs/ENGINEERING_EVALUATION_V10_1.md`,
`ENGINEERING_SCOPE.json` and `audit/v10_1-engineering/`.

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
