# Paired Fault Assessment of a Fly-Connectome Spiking Controller

**Current presentation: assessment-v9 Blender integration (2026-10-23).**
The scientific data, protocol and statistics are unchanged. A wide model/task
overview uses the audited Blender assets: representative anchors, a selected
410-cell/1,050-connection graph and an illustrative fly, with vector labels and
explicit task/clocks. Quantitative figures 2/3 retain their previous bytes.
See [Blender integration](BLENDER_INTEGRATION_V9_zh.md) for sources and commands;
[the earlier visual revision](VISUAL_REVISION_V9_zh.md) remains historical.
The local matched archive is `assessment-v9-blender-review.zip`; its source/data
contents are included in this research branch. The ZIP itself is not a Git file.
Previous named PDFs and source/data ZIPs remain immutable.

Shuchao Gao, Waseda University. ISCAS 2027 research revision **assessment-v9**.
Branch `research/iscas2027-20261022`, base HEAD
`051dcb6a3123841041a34d3b43395e2841975879`. This research branch contains the
updated manuscript and its matching source/data snapshot. The older main and
submission branches do not reproduce this revision. See [GitHub snapshot](GITHUB_SNAPSHOT.md).

The independent core, separate angle stress and secondary action diagnostic
are complete: **288 + 96 + 64 new episodes**, with independent input/geometry
replay. Development and validation remain separate. All 59 lightweight tests
passed without skips. The matching main (5 pages, fifth references only) and
supplement (13 pages) use embedded fonts and no Type 3; every page was reviewed.
[Release state](docs/STATE.md) identifies final source/PDF checks and ZIP receipts.
The GitHub source snapshot is distinct from a conference submission or acceptance.

## Independent core evidence

The core crosses 24 new seed clusters, two bearings, two frozen laws and three
network conditions. A seed contains all 12 conditions, not 12 independent repeats.

| Law | Healthy | 25% row deletion | 50% row deletion |
|---|---:|---:|---:|
| Proportional | 48/48 | 46/48 | 37/48 |
| Relay | 48/48 | 48/48 | 48/48 |

Success means collision-free through one second, not eventual escape. At 50%,
relay-minus-proportional net loss is -22.9 pp, 95% cluster interval [-33.3,-12.5],
Holm-adjusted symmetric-null sign-flip p=0.001953125. At 25%, p=0.50.
Both healthy directions work and every failure is retained. Healthy clearance
medians (33.1/41.4 mm) and executed turning effort differ: this is whole-system
context dependence, not isolated fault-specific superiority at matched reserve.

Frozen 400-ms command-rate and two-sided activity criteria detect 2/13 and 3/13
later collisions. A held-command forecast detects 13/13 but flags 57/275
successful tasks, versus 84/275 for its same-state actuator-schedule baseline.
Exact simulated geometry, sparse positives and false alarms limit deployment
claims. Zero observed misses do not establish zero FNR. These are scores of our
records, not executed benchmarks of SpikeFI or SpikingJET.

Stopped/common activity medians are identical in the new cohort; the large
historical exposure shift is not a current finding. Only two collisions occur
by 800/900 ms, versus 13 by 1000 ms: the declared task horizon matters.

## Separate tests and limitations

The prespecified +/-45-degree stress uses eight new clusters/96 episodes:
healthy and 25% deletion each 32/32, 50% proportional/relay 14/16 versus 16/16.
Its contrast interval [-31.3,0] pp is wide; it is not pooled with core inference.
Forecasts detect 2/2 collisions, with held-command/schedule false alarms 11/94
and 21/94. The two-sided activity rule flags 22/32 healthy stress episodes.

The 64-episode action diagnostic uses eight other clusters and was registered
after core launch. Normal laws each succeed 16/16; turn-disabled (burst retained)
and both-neural-actions-disabled each 0/16. Baseline walking remains active.
Burst necessity partly follows from the toy plant's speed/distance construction;
these controls do not establish connectome-specific superiority or biological escape.

One graph, one assumed RF map, a synthetic task, unmatched nominal reserve and
no hardware mapping remain material limits. No energy, area or physical upset
rate benefit is inferred. The original six-cluster 25% p=.25 remains historical.

## Evidence and reproduction

- [Main PDF](paper/fly_connectome_fault_assessment_v9_blender.pdf), [TeX](paper/main.tex), [supplement PDF](paper/fly_connectome_supplement_v9_blender.pdf), [supplement TeX](paper/supplement.tex).
- [Chinese research/change report](RESEARCH_V9_REPORT_zh.md), [final simulated review and Reject risks](FINAL_REVIEW_V9_zh.md).
- [Core raw records](runs/task-v9-test/episodes/), [summary](audit/acceptance-v9/core-v2/summary.json), [index](audit/acceptance-v9/core-v2/raw-index.csv).
- [Stress](audit/acceptance-v9/stress-v2/summary.json), [action diagnostic](audit/acceptance-v9/causal/summary.json).
- [Protocol](paper/PROTOCOL_v9.md), [development](paper/PROTOCOL_v9_DEVELOPMENT.md), [clarifications](paper/PROTOCOL_v9_NOTES.md).
- [Reproduction commands](REPRODUCE.md), [evidence interface](docs/ASSESSMENT_v9_INTERFACE.md), [material index](REVIEW_MATERIALS.md), [artifact scope](ARTIFACT_README.md).

```text
python tools/run_v9.py tools/analyze_task_v9_exportfix.py --root runs/task-v9-test --registration runs/task-v9-frozen/registration-core.json --out audit/my-core
python tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v9-test --calibration runs/task-v9-frozen/calibration.json --out audit/my-replay
```

Saved-data analysis/replay needs no external matrices or neural rerun. A logged
CSV export-key correction leaves the original frozen script and raw data intact;
only numeric export column names change. Registrations are local, not externally timestamped.

Fresh simulation requires Git, Python 3.12, requirements-v9.txt and separate
Drosophila_brain_model inputs: model.py, Completeness_783.csv and
Connectivity_783.parquet. Default location is a sibling, or set FLY_MODEL_DIR.
Exact hashes/layout are documented. A source/data ZIP excludes matrices and
dependency caches; it is not the complete experimental environment. Original
F4 manifests and some old generation metadata remain unavailable. Old source
entry documents are preserved in docs/history/assessment-v8/.
