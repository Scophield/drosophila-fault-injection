# Checked evidence interface: executable contract and boundary

Intended user: an engineer comparing closed-loop fault campaigns whose random
draws, feedback updates, actuation and evaluation clocks must remain auditable.
This complements a fault injector; it is not a replacement simulator or a new
CRN, bootstrap, fault-model or safety-certification algorithm.

## Inputs and outputs

`evidence_v10.contract.Campaign` specifies independent clusters, task conditions,
controller laws, faults, horizon/frame durations in **seconds**, and resource unit.
`Evidence` supplies those identities, source/config/map/calibration bindings,
common-uniform and fault-mask digests, removed count, completed frame observations,
failure time and binary success. Success means no failure through that horizon.
Frames contain start/end, decision-availability time, earliest use time and
cumulative resource. The native trace is retained for domain-specific replay.

`audit(records, campaign, adapter)` returns structured `Issue(code,key,detail)`
records. An empty issue list means the declared checks pass, not that the physical
model or neural solver is correct. `decode_and_audit` also retains native parsing
errors; malformed/missing rows are never silently deleted. `prefix(record,t)`
returns defensive copies of completed observations through t and cannot read
future outcomes. No cross-plant comparison of incompatible resource units occurs.

### Revised core schema boundary

Before generic set, regex and arithmetic checks, normalized records validate the
integer cluster/deletion fields, hashable condition key, string law/fault/digests,
numeric clocks and optional failure time, boolean success, mapping bindings/native
record, and a list of frame mappings. Missing/nonfinite frame fields remain
structured frame issues. `decode_and_audit` reports invalid core rows as
`native-schema` with their original row index; the direct `audit` entry reports
`record-schema`. Valid rows continue, and absent campaign cells remain explicit.
No invalid scalar is silently coerced into a valid seed, digest or success flag.

The reproduced null-uniform, numeric-mask and list-seed failures are regression
probes, tested on both tank and saved fly schemas, with mixed valid/invalid batches.
They are separate from the original fourteen selected challenge types and are
not additional scientific samples or a general error-coverage estimate. This
core-shape guard does not promise a total parser for arbitrary native objects,
validate every plant-specific field, or authenticate neural execution. Native
adapters retain responsibility for their declared semantics and preconditions.
The revised guard is a source revision, not a retroactive change to the immutable
V10 generation-time/public snapshot or frozen experiment records.

## Generic invariants

1. Exactly one record per cluster/condition/law/fault; every declared cell remains.
2. Configuration, source, RF map and calibration bindings are consistent.
3. Within a seed, exogenous uniforms match across paired conditions. Feedback can
   change rates and realized events; matching event hashes is **not** required.
4. Within a seed/dose, mask identity and removed count match across laws/tasks.
5. Seconds-valued frame coverage is contiguous and reaches the declared horizon;
   decision data must exist before they can be used. Nonfinite fields are errors.
6. Cumulative resource is finite and nondecreasing; success/failure-time labels
   agree and failure times are within the horizon.

## Adapter responsibilities and reuse

The core has no fly imports. `FlyAdapter` converts ms to seconds, binds the saved
map/calibration/model, regenerates frame-indexed uniforms and nested masks, and
calls the independent geometry/input replay. That replay does not import the
task simulator and verifies body bearing, input events, five-frame readouts,
next-frame control, within-frame contact, exact delayed bursts and horizon flags.

`TankAdapter` consumes separately generated delayed level-control records. A
leaky tank has 100-ms sampling, a 150-ms actuator delay (not on the frame grid),
two inflow settings and two fixed laws. Faults delete sensor samples rather than
fly connection rows. The adapter independently checks analytical state updates,
held measurements, queued actuation, within-segment boundary crossing and sensor
resource counts. The exact SAME generic audit and campaign matrix are used.
Eight seeds x two inflows x two laws x three doses produce 96 small simulations.
All 96 are safe in this chosen example; it is reuse evidence, not a neural
performance comparison or evidence that one law is more fault tolerant.

To add a new plant: implement `normalize(native)->Evidence`, `check_native(e)`
and `check_pair(cluster_records)`. The first defines schema/units; the others
state which input, mask, actuation and state semantics are independently checked.
Applications must record sufficient native observations for those checks.

## Executed error and blind-spot challenges

Run from a new output directory:

```text
python -X utf8 tools/run_v9.py tools/check_evidence_v10.py --out audit/my-interface-check
python -X utf8 tools/run_v9.py -m unittest discover -s tests -p test_evidence_v10.py -v
```

The source-bound challenge uses the 288 original V9 core records unchanged, plus
96 genuine tank simulations in its own output directory. Fourteen predefined
error types are instantiated for each adapter: missing/duplicate cells, mixed
bindings, broken CRN/masks, ms/s mistakes, truncated exposure, decreasing resource,
early/nonfinite decisions, wrong success labels, missing native fields and two
plant-specific clock/state defects. These are selected regression challenges,
not a random corruption distribution or a universal 100% detection benchmark.

A separate, conspicuously labelled **synthetic audit fixture** substitutes an
all-zero neural readout without solving neural equations and generates a
self-consistent input/geometry trace. It passes the trace audit. It is never
stored in any scientific episode directory, counted as an experiment, or used in
an outcome/statistical analysis. This witness demonstrates the boundary:
trace consistency and matching claimed source hashes do not authenticate actual
execution, validate unlogged neural state or certify an SNN solver. The two
independent adapters also share mathematical assumptions with their generators;
they do not validate real fluid dynamics or biological pursuit.

Checks do not establish physical fault rates, sensor realism, biological escape,
hardware energy/area, operational safety or guaranteed CRN variance reduction.
Source snapshots, test outputs and the challenge's synthetic/real distinction
are part of the audit record. Report failed/incomplete challenge attempts too.

## Standalone adoption entry

`python examples/tank_v10.py --out runs/my-tank` needs only NumPy and the standard
library (the minimal environment also pins setuptools for the V9 saved-data
launcher). It imports no fly data or Brian2 module and was actually run in the
new minimal environment. Its deterministic repeat is not a new independent
cohort. Five additional real-manifest regressions test generating-source and
calibration bindings, including changed worker entrypoints with the same neural
code digest. A legacy probe separately identifies genuine V8 timing defects;
V8 records are not normalized as V9 or pooled with the new experiment.
