# Additional engineering evidence

Scientific baseline: `22999d28d8fe22f863fc8f62eaa45a57256083d0`.
The exact plan, raw-record fixtures and expected labels were committed at
`246352cff3d0ca9f7e3e9d7ac5158fd4cd734482` before comparative scoring.
Frozen checker source files were not changed. This author-designed additional
evaluation is separate from the old 14-type development challenges, the 72 actual
V8 historical records and the 576 current neural test episodes.

## Four-arm comparison

The header-registry baseline A checks schema, declared matrix identities and
trusted input/mask/configuration headers. B adds the complete unchanged common
audit. C adds native input/plant and per-seed mask replay. D combines them.
No arm uses whole-JSON SHA256 to reject every mutation, and no arm stops after
a baseline finding. The registry is a trusted-input prerequisite, not an
execution certificate.

The catalogue has 111 case IDs, but only 107 distinct adapter/spec/raw inputs:
87 distinct known corruptions plus 24 valid-control IDs representing 20 inputs.
Three source repetitions per family are designed software cases, not independent
neural samples or a random sample of production faults.

| Arm | Detected invalid / 87 | Missed invalid | Rejected valid / 24 |
|---|---:|---:|---:|
| A: headers | 36 | 51 | 0 |
| B: A + common | 54 | 33 | 0 |
| C: A + native | 75 | 12 | 0 |
| D: full | 81 | 6 | 0 |

Full adds 45 findings above A: six common-only, 27 native-only and 12 detected
by both added layers. The six common-only findings are tank outcome-label and
truncated-exposure cases; fly C and D both detect 39/45. Tank C detects 36/42,
and D detects 42/42. This is measured complementarity in two specified adapters,
not general detection coverage or evidence of superiority to unexecuted systems.

All six Full misses remain in the denominator: three fly cases add a consistent
offset to global cumulative spikes, and three alter top-level burst declarations
without changing the fixed-protocol execution trace. Replay cannot authenticate
unobserved neural dynamics; the earlier zero-neural-logger witness remains a
separate development counterexample. No detector was repaired after scoring.

Median wall times per valid campaign fixture for A/B/C/D are 1.7/6.6/1328.9/1321.9
ms in fly and 1.8/6.2/13.2/16.8 ms in tank. Each plant has nine 12-row and three
24-row valid fixtures. Costs exclude input/registry initialization (2.24 s in the
evaluation run). Maximum sampled process RSS is 445.8 MiB, including retained
fixtures; it is not extra per-case memory or a neural simulation footprint.
Three additional technical runs on six preselected cases describe timing
variation without enlarging efficacy denominators. CPU clock granularity can
yield zero for millisecond-scale checks. No energy/area claims follow.

[Full per-plant, unique-input, family, cost, miss and false-positive tables](../experiments/checker-ablation-v10_1/summary-01/REPORT.md)
are accompanied by JSON/CSV and all 516 execution rows. The fixed fixture set
was not blind: its authors knew the checker and prior failure modes.

## Actual historical reporting impact

The 72 V8 records are a different stopped-at-contact protocol and are not pooled
with the 576 V9/V10 neural episodes. Independent source/geometry audit identifies
17 unique affected records in the overlapping old 17/4/6 timing categories.
Every observed burst starts at trigger+260 ms rather than +250 ms. Ten bursts
complete within observation at 440 ms rather than 450 ms: four have a following
off-frame and six end exactly at H. The old count of four used the first
definition only.

Among the 17 records reaching H, exact terminal burst activity is 7/17 rather
than the saved 13/17; the stale flags reuse the final frame's starting state.
Declared burst intervals intersect recorded exposure for 7,480 ms, versus
7,300 ms of observed high-speed motion: 180 ms is overallocated, including a
10-ms interval in one trace that stops before burst onset. Original data are
unchanged; these are separate re-scores.

There are 1,349 spikes in observed burst-marked frames. Only 20-ms cumulative
bins are available, so spikes additionally assigned by the nominal windows
are bounded by 0–647; no exact 10-ms allocation is identifiable. The 55 stopped
records cover 600–700 ms, and total observation is 54.240 s rather than 72 s.
Dividing their saved spikes by a nominal second would understate their observed
mean rates by 30–40%. This does not infer unseen post-stop activity or energy.

All 72 task labels agree with their logged historical geometry. Whether corrected
execution would change collision outcomes is unknown; no neural or plant
counterfactual is reported. Six original generating manifests and their source
code are provided without third-party matrices or annotation tables.

## Original generation budget

The 576 current test episode elapsed fields sum to 29.54593 h, median 167.149 s,
range 125.507–792.702 s. This sum is neither CPU-hours nor actual campaign elapsed
time. Seven manifests record Windows 11 and eight logical CPUs; transfer worker
metadata identify Xeon W-2223 and 31.593 GiB visible RAM. Four worker-lifetime
peak working sets range 1.1974–1.2085 GiB. RF-0 has no recorded process-memory
measurement. Repeated per-episode worker-build values must not be summed.

## Reproduce

Use the documented saved-record Python environment. From this repository:

```text
python tools/ablation/experiment.py prepare --out output/fresh-ablation-plan-01
python tools/ablation/experiment.py run --plan output/fresh-ablation-plan-01 --out output/fresh-ablation-run-01
python tools/ablation/summarize.py --plan output/fresh-ablation-plan-01 --results output/fresh-ablation-run-01 --out output/fresh-ablation-summary-01
```

Fresh preparation can change timestamps/costs while preserving seeded fixture
bytes. To score the delivered frozen plan, pass
`experiments/checker-ablation-v10_1/frozen-02` to `--plan`. Existing output
directories are rejected. A fresh run measures its own costs; the distributed
measurements remain unchanged.

For the historical audit, obtain a separate clean 22999d2 checkout and use:

```text
python tools/ablation/audit_historical.py --root ../science-v10.1 --legacy-bundle experiments/checker-ablation-v10_1/historical-source --out output/fresh-historical-01
python -m unittest discover -s tests -p "test_*v10*.py" -v
```

No new neural simulation, controller calibration, warning threshold or
confirmatory test is introduced. Source/input hashes, plan, labels, mutations,
all misses, all negative controls and original scientific limitations are retained.
