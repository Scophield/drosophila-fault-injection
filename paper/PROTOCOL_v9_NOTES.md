# Post-registration clarifications (registration bytes retained)

## Planning precision, clarified 2026-10-22 before complete core analysis

The frozen registration's approximate 0.20 worst-case half-width is shorthand
for a **[0,1]-valued seed-cluster success/loss/gain mean**, using the maximal
variance normal planning approximation `1.96 * 0.5 / sqrt(24) = 0.2000`.
It is not a finite-sample coverage guarantee or a precision statement for every
contrast. The original wording did not specify this range clearly enough.

Signed net loss `D=Y_H-Y_F` lies in [-1,1]; the corresponding range-based normal
planning bound is about 0.40. A relay-minus-proportional net-loss interaction
can lie in [-2,2] before assuming any healthy successes; its corresponding bound
is about 0.80. Averaging directions can reduce variance but does not establish
either reduction in advance. Observed all-success healthy strata must not be
used to retrospectively rewrite the planning range.

All actual intervals still use the registered complete-cluster bootstrap. The
fixed 24 clusters, both registered dose contrasts, thresholds and stopping rule
are unchanged. This clarification does not justify extending the sample until
significance. The study is not powered to establish small interactions or
equivalence. Original registrations are retained byte-for-byte, not corrected
silently in place.

## Activity-reference distinction

The retrospective own-stop upper flag uses its paired healthy stopped count.
Prospective 400-ms activity flags use frozen law/side healthy-validation medians.
Their classification difference changes both reference and exposure. The paired
`R_stop` versus `R_common` analysis keeps the healthy/fault pair fixed and is the
comparison that isolates the duration change. This clarifies existing code;
no metric or threshold was changed.

## Analysis CSV export correction (2026-10-22 08:14 UTC)

The original frozen analyzer failed before writing result tables: numeric
`features()['deadline'/'schedule_only']` collided with same-named Boolean warning
fields in `dict(**features, **flags)`. It raised `TypeError` after the complete
288-record matrix passed input/source/timing checks. No statistic had been
reported or selected from this failure. All three neural workers exited zero.

The original frozen file, failed log and empty `audit/acceptance-v9/core/`
directory are retained. `tools/analyze_task_v9_exportfix.py` renames only the
numeric CSV fields to `deadline_margin_m` and `schedule_margin_m`, leaving the
Boolean names, definitions, thresholds, pairing, intervals, tests and original
source guards unchanged. Its own hash is stored in each new summary. Corrected
analyses use new `core-v2/` and `stress-v2/` directories; raw records are unchanged.
This is an explicitly disclosed post-registration analytical export fix, not a
re-registration, hypothesis change or neural rerun.

## Later secondary work

The two action ablations remove steering alone (retaining burst triggering),
or remove both neural steering and burst. Baseline walking remains 0.05 m/s.
They do not separately isolate burst contribution. In the defined sampled plant,
triangle inequality gives `d_next <= d - (0.30-0.05)*delta_t` for walk-only
precontact segments, since `d>=0.05 > 0.30*0.02`. Thus contact occurs by0.8s
without bursting regardless of heading. This analytic feasibility check and its
lightweight property test are not additional neural data or a new warning rule.

The action-ablation cohort was registered after core launch, with eight distinct
seeds and no pooling into original inference. Paired warning-difference and
sparse-bootstrap diagnostics were also added after registration and are labeled
secondary descriptive analyses. They add no confirmatory hypothesis and cannot
be described as part of the original JSON registration.
