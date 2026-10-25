# From Connection Loss to Collision — V10.1

**Closed-loop fault assessment of a fly-connectome spiking neural network.**

[Read the V10.1 paper](paper/iscas2027-v10.1-count-candidate.pdf) · [Source](paper/main_v10_1_timing.tex) · [Reproduce the results](REPRODUCE.md) · [What's new](docs/V10_1_CHANGELOG.md)

## Research highlights

- **Paired system evidence:** 576 frozen neural trajectories span three sensory realizations, two feedback laws, two bearings and three connection conditions.
- **Action timing resolved:** 50% connection-row deletion shifts average trigger timing by **80.0 / 57.5 / 57.5 ms** in RF-0/A/B. All **288 P/R pairs** share trigger/burst schedules; **15 pairs** have distinct contact outcomes.
- **Explicit task horizons:** first-contact trajectories quantify task preservation at both 900 and 1000 ms on the same paired records.
- **Executable evidence checks:** a common contract and native replay bind pairing, actuation and endpoints; a delayed-tank adapter demonstrates reuse across two plant schemas.
- **Reproducible publication:** complete active LaTeX, four approved figures, paired analysis tables, source hashes, frozen configurations and saved records are included.
- **Exact warning semantics:** validation-derived integer-count cutoffs remove floating-order boundary ambiguity; all 576 historical warning labels and their whole-seed intervals are preserved. [Count-domain protocol](docs/WARNING_COUNT_PROTOCOL_V10_1.md).
- **Stage-resolved evidence:** 543 contact-free burst completions with follow-up expose an observed zero-command walking regime, distinguished from ongoing, prior-contact and zero-follow-up cases.

| 50% deletion: contact-free tasks (P, R) | 900 ms | 1000 ms |
|---|---|---|
| RF-0 | 46/48, 48/48 | 37/48, 48/48 |
| RF-A | 23/24, 23/24 | 22/24, 23/24 |
| RF-B | 24/24, 24/24 | 23/24, 24/24 |

These endpoints use the same 24/12/12 seed clusters. Timing analysis is retrospective and descriptive; frozen registrations and existing inference are preserved.

## Use this version

```text
git clone --single-branch --branch artifact/iscas2027-v10.1-count-warning https://github.com/Scophield/drosophila-fault-injection.git drosophila-v10.1
cd drosophila-v10.1
git rev-parse HEAD
python tools/verify_v10_1.py
```

The count-candidate PDF is the current V10.1 revision; `paper/main.pdf` and the timing-candidate filename are byte-identical build aliases. The original [V10.1 timing snapshot](https://github.com/Scophield/drosophila-fault-injection/tree/75313d7740491e7f7830e2fc554c21e1aaefe655) is preserved. Original V10 is preserved in [the frozen source/PDF folder](paper/frozen-v10-69dfd2e), and at [commit 69dfd2e](https://github.com/Scophield/drosophila-fault-injection/tree/69dfd2ed9e8fe597ae293398fe58a5d36fef2b7e).

The generating data snapshot remains [986ff54](https://github.com/Scophield/drosophila-fault-injection/tree/986ff54193fee6a1b95815499a4a3477b15ea49a). [Publication identities](PUBLICATION.md), [file hashes](PUBLIC_SCOPE.json), [data index](docs/V10_DATA_INDEX.md) and [third-party input information](docs/THIRD_PARTY_INPUTS_V10.md) connect the paper to its scientific sources. Generation-time metadata are retained.
