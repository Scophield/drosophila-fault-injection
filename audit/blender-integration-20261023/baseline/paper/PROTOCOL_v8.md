# Assessment-v8: controller-by-fault revision

## Scope fixed before inspecting the new fault outcomes

The October 21 review identifies a gap between healthy controller interventions
and controller-dependent fault assessment. This revision completes the smallest
requested factorial comparison on the existing held-out seeds. It changes no
neural model, retinal map, controller calibration, integration step or actuator.

- Controllers: `brain` (original) and `precue_gated` (zero steering before 100 ms).
- Network conditions: healthy, `F2_25`, `F2_50`.
- Seeds: 12, 13, 14, 15, 16, 17; both -30 and +30 degrees per seed.
- Total: 72 records; 24 byte-identical healthy records from controller-v4a,
  plus 48 newly executed fault records. Healthy outcomes were already known.
- Frozen calibration SHA256:
  `5427eaa0159bbf7ebb7f4208fad13a1f8e18c43c7c695b39a078bcde41f639b3`.
- Brian2 seed: 20000+s; deletion seed: 10000+s. The same row mask is used
  across bearings and controllers within seed/dose. The two doses use nested
  masks from the same uniform draw; they are not independent fault realizations.
- F2 independently zeroes a connection-table row, including all contacts
  represented by that row. It does not delete individual synaptic contacts.
- Integration: 0.1 ms; feedback: 20 ms; horizon: 1000 ms; collision: minimum
  within-frame separation at most 0.05 m. Stop at collision or horizon.
- Backend: NumPy, float64 dynamical state/weights; connectivity indices as
  in the unchanged VisionSim source. Existing local pinned packages are reused.

The runner verifies every healthy source snapshot and installed package version
before launch. Analysis requires identical healthy/fault generating-source maps,
external-input hashes, annotation hash, runtime and geometric settings. Reused
healthy records retain their original generation manifests and measured timings.
No regenerated or relabeled healthy record is counted as a new experiment.

## Estimands and interpretation

Let Y_H and Y_F indicate collision-free survival through 1000 ms in a matched
controller, bearing and seed. Report loss L = I(Y_H=1,Y_F=0), gain
G = I(Y_H=0,Y_F=1), and net loss D = Y_H-Y_F = L-G. Give both unconditional
loss counts out of 12 and the number of healthy survivors at risk; do not hide
fault-associated gains. Positive-bearing baseline floor effects remain visible.

Average D over the two bearings within each seed. The interaction is
D_gated-D_original, computed on the same six seed clusters. Report all six
cluster contrasts and a conditional percentile range from 20,000 complete-cluster
resamples with RNG seed 0. Intervals are exploratory conditional summaries;
they neither add independent samples nor establish population coverage,
equivalence, broad robustness or a mechanism. An interval containing zero does
not establish a controller effect on net fault loss.

For each faulty episode, compare cumulative network spikes with its healthy
reference under the same controller, bearing and seed at 200/300/400/500 ms,
requiring both records to reach the endpoint. Also report the ratio at each
pair's common recorded duration. No activity after collision is imputed.
Common duration is outcome-dependent; it is not interchangeable with a fixed
horizon or whole-episode ratios under unequal stopping times.

For c=1.5,2,3,4, tabulate early-activity flags R(t)>c against collision/survival.
This is a descriptive threshold sensitivity analysis of network spikes only,
distinct from the archived open-loop joint rule. The thresholds are operational
assessment definitions with no validated hardware power or safety interpretation.
No threshold is selected using collision outcomes.

## Evidence hierarchy

1. Prospective geometry-corrected tests: principal evidence for bounded task
   outcomes and controller/fault comparisons; calibration remains frozen.
2. Immutable archive reanalysis: supplementary evidence for cohort composition,
   stopping-time mismatch and late crossings in the recorded scenarios.
3. Historical-selector reconstructions: diagnostics only. Original F4 cell
   manifests and historical integration-step metadata remain unavailable.

The historical 288 records are a mixture of conditions and controls, with shared
reference data, not 288 independent draws from a population of hardware faults.
Exclusions are post-hoc condition-level sensitivity contrasts: remove the
inhibitory subset, then every targeted/composition-matched hub cohort, then all
auxiliary controls. They are not an outcome-based clean-up or estimated fault
incidence. The six late hub crossings concern calibration bearings/seeds only.

## Reproduction and acceptance

Normal CPython environment: install `requirements.txt`, with `pdflatex` and
`bibtex` available for document builds. From the repository root:

```text
python tools/run_controller_fault_v8.py --out runs/my-controller-fault
python tools/analyze_controller_fault_v8.py --root runs/my-controller-fault --out audit/my-controller-fault
```

Use `--resume` with the same run directory after interruption; original episodes
and source/configuration snapshots must match. No overwrite is allowed.
The runner requires the preserved controller-v4a inputs. For a new independent
replication rather than this incremental campaign, run the existing neural CLI
on all three network conditions and retain the six-way matrix.

Review deliverables: six directional success counts, 48 fault/healthy pairs,
paired loss/gain/interaction, threshold confusion counts, full provenance, updated
English manuscript, supplement and a Chinese response map. Required QA includes
strict completeness and source validation, targeted statistical regression checks,
clean LaTeX compilation, five-page main PDF and visual inspection of every page.
No new off-calibration bearings, corrected-hub simulations, hardware mapping or
mechanistic analysis are claimed in this P0 revision.
