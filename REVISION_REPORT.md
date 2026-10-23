# Latest review repair (21 October 2026)

Historical repair stage: superseded by `ASSESSMENT_FIX_REPORT.md` and
`paper/PROTOCOL_v3.md`. Statements below about no fresh whole-brain execution
describe this earlier stage, not the current validation work.

The repaired paper is [paper/main.pdf](paper/main.pdf), with editable sources in
[paper/main.tex](paper/main.tex). This report supersedes the status of the earlier
repair in `REPAIR_REPORT.md`; previous work and historical raw records are preserved.

## Changes applied

- Fixed fresh closed-loop input to use body-frame bearing and angular expansion
  from actual separation; added within-frame collision detection and a fixed
  horizon with explicit termination/burst metadata. Neural timestep is pinned
  to 0.1 ms in both engines and provenance.
- Replaced controller-dependent recalibration with passive observe episodes,
  frozen source-traceable calibration, and a test guard rejecting shared
  calibration seed clusters. Old calibration cannot be used for geometry-v2.
- Added calibration partitions, complete F1-F5 dose summaries, matched-duration
  and first-400-ms activity diagnostics, seed-cluster bootstrap intervals,
  threshold sensitivity and raw-source hashes.
- Rewrote the paper around archive-supported observations. Removed mechanism
  attribution, hardware fault equivalence and inhibitory-hub protection advice.
  Removed unreliable pathway-mass curves; kept historical hub records explicitly
  separate from corrected-selector outcomes.
- Rebuilt figures with separated rate/latency axes, individual activity records,
  collision distance, bounded separation traces and exposure-sensitive ratios.
  Added a main F1-F5 table and `paper/PROTOCOL_v2.md` with all doses and definitions.
- Updated Brian 2, LPLC2 biology, Lin and NeuroBench references using registry
  metadata; removed the misplaced Drummond citation and narrowed related-work
  claims. Added verified scientific-computing and embodied-benchmark context.
- Fixed isolated LaTeX builds so an old `paper/main.bbl` cannot shadow the new
  bibliography. Preserved IEEE conference format and Shuchao Gao/Waseda authorship.

## Corrected interpretation

The original 24/24 nonfrontal healthy total includes six calibration episodes.
The remaining 18/18 records do not overlap exact calibration scenarios, but this
post-hoc partition does not establish independent evaluation. Fault scenarios
still include calibration conditions and shared seeds.

For F2 50%, the median paired spike ratio is 0.382 for whole episodes, 0.729 at
each pair's common duration and 0.723 within the first 400 ms. Whole-episode totals
confound firing with collision-truncated exposure. Full-hub twofold exceedances
are 6/12 for episode totals and 0/12 within 400 ms; neither is a general safety
claim. Historical hub-selection inconsistencies remain explicit.

The main archived result remains 76.46% median command-rate retention at 50%
random connection deletion and 150 Hz input, with first-spike latency increasing
from 4.05 to 5.40 ms. The same 288 records give 276 transmission and 262 joint
passes. These results do not identify a mechanism or certify hardware reliability.

## Reproduction and verification

[REPRODUCE.md](REPRODUCE.md) supplies current environment, input, execution and build
instructions. The lightweight path requires no Brian2 simulation or new connectome:

```text
python -m unittest discover -s tests -v
python tools/audit_revision.py --out audit/my-revision
python tools/plot_revision.py --analysis audit/my-revision/revision_analysis.json --out audit/my-figures
powershell -File tools/build_paper.ps1 -BuildDirectory audit/my-paper-build
python tools/qa_pdf.py --pdf paper/main.pdf --out audit/my-paper-qa
```

Choose unused output paths. Publication figures are saved in `paper/figs/`;
regenerating plots into an audit directory does not silently replace them.
Final test output, source hashes, archive-integrity checks and PDF checks are
recorded in `audit/revision-final-validation/`. Saved results in
`audit/revision-v2/` are archive reanalysis, not fresh simulation trials.

## Remaining empirical work

The revised code was exercised on synthetic inputs and the archive reanalyzed.
No new whole-brain experiment or hardware run was executed. The complete pinned
Brian2 environment and compiler toolchain remain unvalidated. Fresh whole-brain
calibration/test outcomes, corrected-selector contrasts, regenerated multi-null
controls, horizon/RF/threat/actuator sensitivity, a functioning matched controller
and a physical hardware fault mapping remain unmeasured. The paper withdraws
conclusions depending on them; experimental validation is still required before
restoring those claims.

No commit, push, submission or publication was performed.
