# Count-domain definition of the frozen command warning

This document specifies the numerical implementation of the existing 400-ms
command warning. It preserves the original healthy-validation cohort, fifth
percentile and strict lower-tail comparison. It does not select a new operating
point, add samples, change neural simulations or create a new confirmatory test.

## Observation and count provenance

The native generator first forms integer spike-monitor counts for each of eight
descending neurons in each 20-ms bin, then stores `cmd_rates = counts / 0.020` in
the episode JSON. The distributed records retain these rates, not a separate
spike-count field or independent spike timestamps. The revised implementation
therefore **recovers the original integers losslessly from the saved rate
lattice**; it does not claim a new timestamp-level neural reproduction.
Only unsmoothed `cmd_rates` enter this warning; the five-frame `smooth_rates`
used for action triggering are a different statistic.

`command_count` in `tools/task_metrics_v9.py` selects rows satisfying
`100 < t_end_ms <= 400`. The required ends are 120, 140, ..., 400 ms: 15 ordered,
complete bins accounting for the generator's `[100,400)` interval. Each bin must
have eight finite, nonnegative command rates exactly on the 50-Hz lattice. The
implementation rejects missing, duplicated, out-of-order or wrong-duration bins,
wrong channel counts, and off-lattice rates. It does not accept near-integers by
tolerance-based rounding.

For a saved cell/bin rate `r`, the count is exactly `r / 50`. Summing these
integers gives `N` across eight neurons and the 300-ms window. The equivalent
mean rate is

```text
command_hz = N / (8 × 0.300 s) = 5N/12 Hz.
```

Rates remain convenient display values; the alert decision uses integer counts
and an exact rational cutoff, not a comparison between rounded Hz values.

## Validation-only quantile and tie semantics

Each RF has its original 32 healthy validation records: eight seed clusters,
two bearings and two laws. All records are retained. The fifth percentile uses
the original NumPy `linear` convention, also known as Hyndman–Fan type 7. For
sorted integer counts `x[0] <= ... <= x[31]`, exact probability `p = 1/20` gives

```text
h = (32 − 1)p = 31/20
Q.05 = x[1] + (11/20)(x[2] − x[1]).
```

The revised implementation evaluates this interpolation with rational arithmetic.
The following cutoffs are derived from the healthy validation counts, not
hard-coded from test outcomes:

| RF | `x[1]`, `x[2]` | Exact count cutoff | Equivalent Hz cutoff | Integer counts flagged |
|---|---|---|---|---|
| RF-0 | 14, 14 | 14 | 35/6 | `N <= 13` |
| RF-A | 14, 15 | 291/20 | 97/16 | `N <= 14` |
| RF-B | 13, 14 | 271/20 | 271/48 | `N <= 13` |

The existing lower-tail rule is **strict `<`**. Equality does not flag. For
example, RF-0 counts 13, 14 and 15 produce alert, no alert and no alert. In
general, for cutoff `a/b`, classification is `N*b < a`, using integer arithmetic.
This retains the original operation's intended equality semantics without an
epsilon, an outcome-selected tie break or a new percentile choice.

`bind_count_cutoff` derives the count cutoff from the corresponding original
validation records and enriches an in-memory copy of the frozen threshold
object. It preserves the stored Hz field and other thresholds. A four-binary64-
ulp check only confirms compatibility between the stored Hz cutoff and the
validation-derived rational value; that tolerance never enters alert decisions.
Frozen registration and calibration files are not rewritten.

## Historical floating implementations and the verified result

The historical expression accumulates `sum(rate * 0.02) / (8 * 0.3)`. An
algebraically equivalent order, `sum(rate) / (8 * 15)`, can round differently.
For 19 contact-free RF-0 records with `N=14`, the historical expression yields
`5.833333333333334` Hz, equal to its stored cutoff. The alternative yields
`5.833333333333333` Hz, one binary64 step below that cutoff, and incorrectly
changes those strict-comparison labels relative to the exact equality rule.
Their identities, source paths, hashes, count values and float hexadecimal
representations are retained in the regenerated boundary-record CSV.

The canonical implementation agrees with the historical saved labels for **all
576 test records**. The alternative floating order changes 19 RF-0 labels and
none in RF-A/B. The command-warning confusion counts are:

| RF | TP | FP | TN | FN | Legacy-to-canonical changed labels |
|---|---:|---:|---:|---:|---:|
| RF-0 | 2 | 51 | 224 | 11 | 0 |
| RF-A | 2 | 42 | 99 | 1 | 0 |
| RF-B | 0 | 24 | 119 | 1 | 0 |

Under the alternative RF-0 floating order, FP/TN become 70/205 while TP/FN stay
2/11. This difference identifies numerical ambiguity; it is not a second chosen
operating point. The canonical rule was fixed by the original validation-only
quantile and strict `<` semantics, **not by which test-set false-alarm rate is
smaller**. Thus unchanged historical counts are a consequence of the specified
rule, rather than a reason for selecting it.

Re-scoring also recomputes the frozen upper-only activity, two-sided activity,
held-command forecast and schedule-only forecast comparators. For all three RFs,
all five criteria's point estimates and bootstrap intervals match the saved
historical analysis. Fig. 4 is regenerated from the new canonical output rather
than copied on the assumption that the numerical values are unchanged. This
repair fixes a reproducibility boundary; it introduces no improved monitoring
performance claim.

## Statistical units and uncertainty

The 288/144/144 test episodes in RF-0/A/B comprise 24/12/12 independent seed
clusters. Each cluster retains both bearings, both laws and all three connection
conditions. TP/FP/TN/FN are trial counts, with contact through the declared 1-s
endpoint as the positive class. Rates use their corresponding confusion-count
denominators, rather than an average of per-seed rates.

The regenerated intervals use 20,000 whole-seed resamples, RNG 20261022 for RF-0
and 20261023 for RF-A/B. Within each draw, the complete per-seed confusion vectors
are summed and rates recomputed; pointwise percentile limits use `linear/type-7`
2.5th/97.5th percentiles. A draw with no positive class is undefined only for the
positive-class rate. Those draws are omitted from that rate's percentile
calculation, not from the original cohort or other rates. The outputs retain
these undefined-draw counts (0/2217/7099 in RF-0/A/B). Sparse positive support and
zero-width empirical intervals do not establish zero population error.

## Executed products and reproduction

The canonical entry reads the original validation/test records and registrations
without modifying them. Run from the repository root in the saved-analysis
Python environment, using a new output directory:

```text
python tools/rescore_warnings_v10_1.py --out output/warning-counts-v10_1-02 --draws 20000
```

For a repeat, choose `-03` or another fresh directory. The delivered products are:

- `output/warning-counts-v10_1-02/results.json`: thresholds, complete confusion
  counts/intervals, historical comparisons, bootstrap definitions, runtime and
  analysis/input SHA256 provenance manifest.
- `output/warning-counts-v10_1-02/all-records.csv`: all 576 canonical/legacy/
  alternative labels and per-record identities.
- `output/warning-counts-v10_1-02/validation-counts.csv`: the 96 validation
  observations used to derive the three cutoffs, with source hashes.
- `output/warning-counts-v10_1-02/boundary-records.csv`: all 19 differing RF-0
  boundary records, including exact counts and floating representations.
- `output/warning-counts-v10_1-02/warning-summary.csv`: all five warning criteria,
  cohort denominators, confusion counts and rate intervals used by the figure.

The output manifests verify frozen input bytes; new results live in a separate
directory. Historical score products, registrations, calibrations and generating
source snapshots remain intact. Historical full-matrix entry points retain their
registered source-hash guards. Reproduce the historical floating analysis in its
fixed checkout or from its frozen source snapshots; do not substitute the revised
library under the old source registration or silently remove the guard. The
versioned re-scoring entry above is the canonical count-domain workflow.

## Fixed artifact layers

1. [986ff54](https://github.com/Scophield/drosophila-fault-injection/tree/986ff54193fee6a1b95815499a4a3477b15ea49a)
   preserves the original curated V10 source, generated observations and frozen
   experiment metadata. Its reproduction document is
   `docs/PUBLIC_REPRODUCE_V10_FINAL.md`.
2. [126e265](https://github.com/Scophield/drosophila-fault-injection/tree/126e265ef1a0bb49d2a3103ff47b0c9077acdcc0)
   identifies the earlier schema/horizon revision and
   `docs/PUBLIC_REPRODUCE_V10_HORIZON.md`; it does not identify V10.1 timing tools.
3. [75313d7](https://github.com/Scophield/drosophila-fault-injection/tree/75313d7740491e7f7830e2fc554c21e1aaefe655)
   identifies the published V10.1 timing snapshot, including
   `tools/analyze_trigger_timing.py`, `tools/verify_v10_1.py`, its saved timing
   products and root `REPRODUCE.md`.

This count-domain implementation is a subsequent revision. Bind its tested code
and regenerated analysis to a separate immutable code/analysis commit before
citing it as a public artifact; do not use 75313d7 to identify the new warning
implementation. A later manuscript commit can reference that fixed implementation
and expose its own final PDF through the publication manifest and external Git
permalink, without embedding its own future commit hash. Original generation
metadata are retained, not relabelled with a later implementation identity.
