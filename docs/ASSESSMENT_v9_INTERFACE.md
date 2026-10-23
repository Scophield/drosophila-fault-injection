# Assessment v9: reusable evidence interface

The reusable component is an executable, auditable assessment protocol. Ridge
decoding, common random numbers, percentile bootstrap and the warning rules are
standard methods. This artifact does not establish a new protection algorithm.

## Evidence tiers

1. `runs/task-v9-frozen/registration-*.json` fixes the source, input-table hashes,
   runtime, calibration, seeds, matrix, thresholds, analysis and stopping rule
   **before** independent generation. Core and angle stress are separate.
2. A campaign contains `active.json`, execution/exit-code records, a saved
   `input-map.json`, per-worker `batches/*/run_manifest.json` and generating
   `batches/*/source/`, and one non-overwritten `episodes/*.json` per cell.
3. An episode stores its seed/bearing/law/fault, realized deletion size and sign
   composition, mask/common-uniform/actual-input hashes, source-manifest hash,
   complete 20-ms frame trace, exact actuator segments, first contact and task
   outcome. One seed shares all twelve core conditions. They are not twelve
   independent statistical replicates.
4. `tools/analyze_task_v9_exportfix.py` rejects missing/duplicate cells, mixed runtime or
   input maps, wrong source snapshots, changed registrations, noncommon uniforms,
   nonnested masks, wrong duration and inconsistent timing flags. It writes
   portable raw indices, all outcome cells, paired effects, cluster contrasts,
   warning denominators, horizons and exposure profiles.
5. `tools/replay_audit_v9.py` independently reconstructs the sampled geometry,
   retinal rates, readout smoothing, causal decisions, exact actuator intervals,
   first contact, fault masks and actual input-event hashes. It imports neither
   the task implementation nor the neural simulator and needs no external table.
   It consumes recorded neural readouts: it cannot establish correctness of every
   neural state or substitute for rerunning the neural model.
6. `tools/check_task_numbers_v9.py` independently checks outcome/risk-set counts,
   cluster effects/intervals, polynomial sign-flip tails, saved warning confusion
   counts and zero pre-cue activity. It does not reuse the main analyzer.
7. Final PDF validation binds the complete evidence, tests, source-built PDFs,
   figure inputs, fonts, page rule and actual all-page visual review. The local
   ZIP includes a per-file SHA256 manifest and is read back for verification.
   Packaging does not make the revision public or submit it to a conference.

These checks can expose clock, mapping, duration, input-coupling or arithmetic
errors while avoiding another full neural execution. They do not validate the
biological assumptions or generalize the empirical result to another plant.

The scientific ZIP includes the matched evidence required for saved-data
reanalysis, not the entire pre-existing workspace backup. The one-time baseline
preservation check therefore remains a recorded local editing audit; rerunning
that editing-history check needs the original backup/workspace. Independent ZIP
byte verification needs only the standard library (`verify_artifact_v9.py`),
and scientific analysis/replay needs the packaged files and pinned libraries.

## Field semantics that matter

- `escaped` means **no first contact through 1000 ms**, not eventual escape.
- `collision_ms` is a latched first-passage time within a linear motion segment.
- `t_end_ms` is when the logged neural decision becomes available. Its
  `next_omega` applies to the following motion interval.
- `segments` partitions a feedback frame at any scheduled burst boundary.
  The burst interval is half-open; the state at exactly 1000 ms is evaluated
  independently of the last frame's state.
- `n_total` is cumulative network spike count. After first contact, continued
  neural activity is a specified counterfactual resource observation, not a
  physical collision simulation or a prospective warning.
- Common input uniforms do not imply identical realized sensory events: feedback
  changes rates. The artifact saves both digests rather than equating them.
- Deletion fractions concern **weighted connection-table rows**, not independent
  contacts, cell deletion or mapped physical bit upsets. Doses have nested masks.
- FlyWire IDs exceed IEEE-754 exact integer precision. `input-map.json` stores
  them as strings; older calibration/episode fields contain JSON integer tokens.
  Parse those with Python/arbitrary-precision integers. Do not round-trip them
  through ordinary JavaScript `Number` values.
- A healthy reference median, a trial percentile range and a bootstrap confidence
  interval are different quantities. New intervals resample whole seed clusters;
  historical trial-level intervals are not used as new independent evidence.
- Retrospective `stop_count_upper` uses its paired healthy stopped count as
  denominator. The prospective 400-ms activity flags use frozen law/side healthy
  validation medians. Their classification difference changes both exposure and
  reference. Only the paired `stop_ratio` versus `common_ratio` comparison
  isolates the observation-duration change within those same records.

## Minimal use without a connectome

Use the supported environment in `REPRODUCE_v9.md`, a new output directory, and:

```text
python tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v9-test --calibration runs/task-v9-frozen/calibration.json --out audit/my-independent-replay
python tools/run_v9.py tools/analyze_task_v9_exportfix.py --root runs/task-v9-test --registration runs/task-v9-frozen/registration-core.json --out audit/my-independent-summary
python tools/run_v9.py tools/check_task_numbers_v9.py --root runs/task-v9-test --analysis audit/my-independent-summary --registration runs/task-v9-frozen/registration-core.json --out audit/my-independent-numbers
```

Analysis checks the frozen generating/analysis sources. If adapting the simulator,
controller, map, task or analysis, retain old outputs and create a newly labeled
registration and campaign. A different plant needs its own replay and calibration;
the present test does not establish portability without that work.
