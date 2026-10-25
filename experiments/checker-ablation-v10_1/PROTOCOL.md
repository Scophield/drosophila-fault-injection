# Fixed additional checker evaluation

Scientific/checker baseline: `22999d28d8fe22f863fc8f62eaa45a57256083d0`.
This protocol is an additional software evaluation, not a blind generalization
test or a preregistration of the original neural experiments. Designers have read
the checker and known error categories. No neural dynamics, threshold fitting,
hypothesis test or original-data editing is permitted.

## Question and competing explanations

Does replay add useful error information to a strong record-identity baseline,
and does the complete existing common contract add information beyond replay?
The simpler explanation is that schema/seed/input/mask checks suffice, or that
the full combination only duplicates one component at substantial cost.

## Four arms, fixed before scoring

- **A / Baseline:** frozen adapter normalization and schema guards; complete
  declared matrix membership, identities and duplicates; positive finite scalar
  clocks, basic field ranges, numeric frame fields and nonnegative resources;
  trusted header registry for input, mask, deletion counts and generating
  configuration identities. The registry is extracted from source-hash-verified
  original records before corruption. It does not whitelist complete JSON hashes
  or trace/output values. Its construction and trust prerequisite are reported.
- **B / Common:** A plus the **entire unchanged**
  `audit(records, spec, adapter=None)` implementation, including all existing
  pairing, binding, timing, exposure, resource and outcome checks.
- **C / Native:** A plus all existing `adapter.check_native` and per-seed
  `adapter.check_pair` calls, in the same record order as Full. It does not
  secretly run Common. Normalization failures are retained, not dropped.
- **D / Full:** A plus the complete unchanged
  `audit(records, spec, adapter)` implementation. It is the union of available
  checks, not a newly trained detector. No arm stops after an A finding; only
  unnormalizable records share the same safety exclusion.

Whole-file SHA256 establishes fixture provenance, not the error-detection oracle.
Inputs and masks are checked against trusted headers, not presumed equal realized
event hashes. Legal worker subsets use explicit declared subcampaign matrices.
Top-level burst-delay/duration declarations receive basic numeric validity checks
in A; no new semantic check is added to the frozen checkers to repair a possible
blind spot. Consistent fabrication of unobserved neural execution is a separately
reported out-of-scope witness, not a valid-log error-detection success.

## Inputs, challenges and validity

Use all 576 RF-0/A/B records and the 96 saved tank records as a trusted input
inventory, with calibration/registration and frozen checker-source hashes. Unit
of evaluation is a declared seed-block software fixture, not a neural replicate.
The separate challenge specification fixes mutations, labels and generation seed
`2026102501`. Three source repetitions per family are not independent evidence
for a population detection rate. Reconstruct every candidate's native rows after
mutation; do not reuse the older normalized-view-only development corruptions.

Save the complete ordered fixture list, expected labels, original input hashes,
generator hashes and compressed fixture bytes **before any comparative scoring**.
Existing outputs cannot be overwritten. Invalidity follows the declared data/
plant semantics, not whether the checker happens to reject the row. Negative
controls include untouched records, real off-grid actuator events, legal worker
seed partitions and real feedback-dependent event streams. Preserve misses and
false positives. Original 14-type development challenges and actual historical
V8 errors remain separate evidence sets.

Structural inapplicability is retained in the frozen index and logs with its
reason, but excluded from detection denominators. Report intrinsic unique inputs
using `(adapter, spec, raw rows)` digests, since named valid cases may reuse the
same source block. Case counts are not independent-input counts. The observed
actuator-end corruption changes the last recorded on-interval; for ongoing
bursts this does not assert an observed complete 450-ms duration. Worker controls
combine two real seed blocks as specified in the pre-execution amendment.

## Metrics and costs

Report per-arm case counts, detected invalid cases, missed invalid cases, falsely
rejected valid cases and accepted valid cases. Also report each family, source,
first detecting layer, Common/Native overlap, disjoint findings and union.
No binomial CI or p-value is justified for this designed challenge catalogue.

Primary cost is one invocation per arm/case with identical record sorting and
cleared FlyAdapter stream cache. Record wall time, process CPU time, sampled RSS
and starting RSS. Adapter construction and registry preparation are separate.
Three technical repeats on a fixed deterministic subset describe timing variation
only. Memory samples are process RSS, not per-case allocation or hardware energy.
The baseline's trusted-registry cost is explicit; Native includes seeded mask
reconstruction and input-event/plant replay. No result-driven early stopping.

## Historical scientific impact and adoption

Independently rescore the 72 old V8 engineering records, retaining their original
protocol and source identity. Report overlapping timing categories and unique
affected rows, declared/observed burst onset and duration, terminal actuation
flags and only identifiable resource/outcome effects. Do not assume these errors
changed collision labels or compute an unobserved neural counterfactual.
Cross-plant results characterize one fly adapter and one delayed-tank adapter;
neither provides general safety or neural-execution authentication.

## Decision and stopping rule

Strengthen the manuscript only if the fixed catalogue shows a clear nonredundant
increment above A, with identifiable Common/Native boundaries and valid-control
behavior, and the genuine historical records quantify an actual reporting impact.
Keep all residual misses, the trusted-registry assumption and cost visible. If
the result is redundant, uninformative or cannot fit four technical pages legibly,
retain 22999d2 as the recommended submission and publish only this evaluation
plus warranted small clarifications. No score-seeking experiment extension.
