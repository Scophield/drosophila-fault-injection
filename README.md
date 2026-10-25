# From Connection Loss to Collision — V10 submission candidate

Limited final polish from fixed revision `126e265`: archived timing-error evidence,
all-map 900/1000-ms counts, separate generating/assessment citations and panel-specific
Fig.2 legends. See [final change and verification report](docs/V10_SUBMISSION_FINAL_zh.md).
No experimental data, preregistration or scientific conclusion changed.

Current paper: [paper/main.pdf](paper/main.pdf). Active source:
[paper/main_v10_horizon.tex](paper/main_v10_horizon.tex) (also `paper/main.tex`).
The title is *From Connection Loss to Collision: Closed-Loop Fault Assessment
of a Fly-Connectome SNN*. Four technical pages plus a reference-only fifth page;
the four main figures and approved Blender imagery are retained.

This revision adds descriptive 900/1000-ms rescoring of the SAME RF-0 trajectories,
concrete quantitative contributions, scoped frozen-warning claims, and guards for
three reproduced malformed core-input crashes. It adds no neural experiments,
threshold fitting, independent samples or new hypothesis tests. Frozen records,
preregistrations and calibrations are byte-identical to the prior public snapshot.

| 50% deletion; contact-free tasks (P, R) | 900 ms | 1000 ms |
|---|---|---|
| RF-0 | 46/48, 48/48 | 37/48, 48/48 |
| RF-A | 23/24, 23/24 | 22/24, 23/24 |
| RF-B | 24/24, 24/24 | 23/24, 24/24 |

Both horizons reuse the same 24/12/12 paired seed clusters, with two bearings per law. Healthy
clearance differs; RF redraws, recalibration and test cohorts change together.
Small uncertain RF-A/B contrasts are neither equivalence nor RF causal effects.
Warning conclusions concern only the tested frozen scalar criteria. Selected
checker challenges are not general detection coverage or execution attestation.

## Obtain and reproduce

```text
git clone --single-branch --branch artifact/iscas2027-v10-submission-polish https://github.com/Scophield/drosophila-fault-injection.git v10-horizon
cd v10-horizon
git rev-parse HEAD
```

[Reproduction entry](docs/PUBLIC_REPRODUCE_V10_HORIZON.md) distinguishes saved-data
analysis, checker tests and LaTeX compilation from fresh neural simulation.
[Contribution before/after](audit/v10-horizon/CONTRIBUTIONS_BEFORE_AFTER.md),
[descriptive records](audit/v10-horizon/descriptive/first-contacts.csv),
[revision report](docs/V10_HORIZON_REVISION.md) and
[publication identities](PUBLICATION.md) document the exact scope.

## Version and distribution boundary

The original generating code/data commit remains
[986ff54193fee6a1b95815499a4a3477b15ea49a](https://github.com/Scophield/drosophila-fault-injection/tree/986ff54193fee6a1b95815499a4a3477b15ea49a).
The preceding fixed assessment revision is
[126e265ef1a0bb49d2a3103ff47b0c9077acdcc0](https://github.com/Scophield/drosophila-fault-injection/tree/126e265ef1a0bb49d2a3103ff47b0c9077acdcc0).
The earlier fixed paper is
[48c16c0852bcc3f6b061ab8edc97b0f16ebc1016](https://github.com/Scophield/drosophila-fault-injection/tree/48c16c0852bcc3f6b061ab8edc97b0f16ebc1016).
Neither identifies this revised PDF/checker. The enclosing Git commit identifies
this revision, while `PUBLIC_SCOPE.json` binds its distributed file bytes.
Historical prepublication reports retain their original unpublished/no-push
status; this publication entry supersedes that delivery status, not their data.
The legacy named `paper/fly_connectome_fault_assessment_v10_final.pdf` and
`main_v10_final*.tex` are prior candidates; use `paper/main.pdf` for this revision.

The full V9 scientific baseline is 43bcd4d6a99b2d9b258cf8a198a4545d237b5c39.
This branch descends from the curated V10 distribution history, avoiding inherited
unresolved-license input tables. Private Blender projects, external matrices,
annotation dumps and caches are omitted; approved rendered figure PDFs remain.
See `PUBLIC_SCOPE.json`, `THIRD_PARTY_LICENSES` and `docs/THIRD_PARTY_INPUTS_V10.md`.
No main/V9/previous-final branch update, GitHub Release or submission is performed.
Research archives are not formal supplementary submission attachments.
