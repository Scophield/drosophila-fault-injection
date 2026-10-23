# v9 execution / handoff log

Last substantive state: 22 October 2026, approximately 04:14 UTC. This is an
in-progress work log; the current main PDF is still the original v8 baseline.
Do not mistake protocol preparation for completed independent experiments.

## Preserve

Repository: `D:/autoresearch_labtorary/drosophila-fault-injection`.
Branch `research/iscas2027-20261022`, base HEAD
`051dcb6a3123841041a34d3b43395e2841975879`. No commit/push/submission.
Hash-verified 21069-file baseline backup is outside the repo at
`../drosophila-research-backups/20261022-acceptance-baseline/`.
All historical raw data and versioned v8 PDFs remain unchanged.

Deadline is 23 October 2026 04:59 UTC / 13:59 JST, verified on the official
ISCAS author page. Do not let optional experiments displace paper/QA completion.

## FROZEN SOURCE WARNING

The core registration has now been written and independent tests launched.
DO NOT EDIT any file in its `frozen_source_sha256` map: all `sim/*.py`, all
`sim_vision/*.py`, `requirements-v9.txt`, and selected tools including
run_v9/run_task/launch_task/calibrate/freeze/analyze/task_metrics/replay_audit.
No controller/metric/source/seed tuning based on independent test outcomes.
Critical correctness failures require a separately documented new protocol,
not a silent patch to running or completed data. Paper, plotting, documentation,
PDF QA and new release tools are not frozen and may be edited.

Registrations: `runs/task-v9-frozen/registration-core.json` and
`registration-stress.json`. Core SHA256:
`7efa2ad4da4dc72cfd5773c57adc44020f12981fcc30d78e9b3c5d10d395b54f`.
Calibration `runs/task-v9-frozen/calibration.json` SHA256:
`8ba27037d006ba6a8ae581c07170be6ac1ed0563873d4a3dc60af6d35d8e4ddf`.

## Actual completed work

* Full v8 review, review-check/timing-check, current source/PDF identity read.
  Independent audit confirms fifth-page violation, 260/440 ms realized old
  timing, six wrong horizon flags, and exploratory interaction p=0.25.
* Archive reanalysis in `audit/acceptance-v9/archive-recomputed` reproduces all
  earlier mathematical/statistical corrections, including HUB_inh 6/12 survival
  with 12 bursts, F4 six activity exceedances, and 276/288 vs 262/288 scoring.
* New causal exact-event task, shared indexed input uniforms, nested row masks,
  source guards, actual input/RF/command identities, signed damage logging,
  frozen thresholds, cluster analysis and independent trace/input replay added.
* Development: 20 passive records, seeds 200--203, five angles, 400 ms.
* Configuration A stopped for a declared capability failure. Six completed
  records preserved: three healthy (one survivor), three F2_25 (two survivors).
  These are development, not confirmation.
* Configuration B: same decoder/trigger, common 600 deg/s gain, silence gating.
  Fresh validation seeds 400--407: 32/32 healthy survivors, 8/8 in every
  law/bearing stratum. B execution exit codes all zero, elapsed 1934.36 s.
* Fault screen: seeds 400,401, two angles/laws/doses = 16 complete records.
  One collision: seed401/proportional/-30/F2_50 at 977.0661 ms. No task retuning.
  Independent replay of all 16 records passed, including exact realized input
  event and mask hashes, in ~1.77 s. It does not resimulate neural dynamics.
* Full regression suite: 50 tests passed, 18.871 s (exec session 71171).
* Main neutral methods drafted in `paper/sections/v9_methods.tex`, not yet
  included. Final abstract/conclusions await complete independent data.
* Figure overview drafted/rendered/inspected in `audit/acceptance-v9/overview-draft`.
  New figure script supports complete core analysis; all PDFs embed TrueType.

## Running / next execution

Core is RUNNING in unified exec session **46440**:
`runs/task-v9-test`, seeds 1000--1023, +/-30, proportional/relay,
healthy/F2_25/F2_50, 288 episodes. Three workers, source/inputs/runtime guards
passed and network builds completed. Use active.json, worker logs and episode
counts for status; do not change sources. Expected elapsed ~4--4.5 h.

After core finishes, start the PRESPECIFIED stress run (no outcome selection):

```text
python tools/run_v9.py tools/launch_task_v9.py --out runs/task-v9-stress --seeds 1100,1101,1102,1103,1104,1105,1106,1107 --phis=-45,45 --calibration runs/task-v9-frozen/calibration.json --role test --registration runs/task-v9-frozen/registration-stress.json
```

It is 96 episodes / eight separate clusters, ~1.5--1.7 h. Never pool with core
to improve significance. Core paper writing can proceed while stress runs.

For completed core (all 288 required):

```text
python tools/run_v9.py tools/analyze_task_v9.py --root runs/task-v9-test --registration runs/task-v9-frozen/registration-core.json --out audit/acceptance-v9/core
python tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v9-test --calibration runs/task-v9-frozen/calibration.json --out audit/acceptance-v9/replay-core
python tools/run_v9.py tools/plot_task_v9.py --analysis audit/acceptance-v9/core --out audit/acceptance-v9/figures
```

Run corresponding analyze/replay on stress into separate NEW directories.
The quantitative plotter expects core 288; stress needs separate SI tables/plots.

## Runtime / tooling

Managed Python:
`C:/Users/ohsawalab gpu3/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
Always use `tools/run_v9.py`; it supplies isolated CP312 `tmp/v9-deps` and
project paths. Old `tmp/sim-deps` etc contain incompatible CP313 binaries.
`tools/run_v9.py -` supports stdin Python scripts for compact read-only analysis.
Environment is saved in `audit/acceptance-v9/environment.json`, 31.59 GiB RAM.
Brian2 2.10.1, NumPy2.5.4, supported Cython3.1.3; old Cython3.3 requirement
conflicts with Brian2. Full pins in requirements-v9.txt.

MiKTeX pdflatex/bibtex are available. `tools/build_paper.ps1` stages source in a
NEW directory, runs pdflatex/bibtex/pdflatex/pdflatex, rejects undefined refs,
overflow/missing glyphs, then copies main.pdf. Ensure FloatBarrier + clearpage
before references: four technical pages, fifth references ONLY. qa_pdf has a
tested references-only checker; old validator now enforces it instead of just
reporting false. Inspect EVERY final main/SI page, font embedding and Type3.
The PDF skill artifact-start marker was already run ONCE for this task; do not
repeat it. Skills loaded: reviewer, writing, figure(Python), PDF, academic search.
No new subagents are authorized/needed.

MiKTeX access requires `sandbox_permissions=require_escalated` on this host:
its user registry/configuration cache is denied inside the sandbox. An escalated
read-only kpsewhich check confirms longtable.sty is installed. This is not an
approval rejection and does not require asking the user again. Compile with the
same justified escalation. A maintenance-update warning is nonfatal if exit=0.

Additional preparation after launch: docs/REPRODUCE_v9.md, a data-driven
tools/build_supplement_v9.py (requires completed core+stress and replay reports),
and four in-memory actual-trace mutation tests were added. All four passed.
No frozen source changed. The supported root requirements now include
requirements-v9.txt; original v8 pins are preserved as requirements-v8-recorded.txt.

All baseline main pages and all 14 v8 supplement pages were visually/textually
inspected. A wider old-flag audit now covers 153 unique old records: 96 have
qualified exact source/timing, reproducing the six known mismatches; 57 lack
sufficient original source metadata and remain unverified. See
audit/acceptance-v9/legacy-horizon-flags/check.json. Do not claim those old flags
fully validated or copy unqualified first-campaign horizon counts into new SI.

Use git diff with `--no-ext-diff --no-textconv`; default textconv invokes a
broken MSYS helper. Process stop commands need escalation to see actual worker
PIDs; stop ONLY PIDs generated for this task. Configuration A was safely stopped
and its nonzero interruption exit codes are preserved.

## Remaining deliverables

1. Finish core/stress + analyses/replays; independently check key raw counts.
2. Decide A/B/C/D contributions from actual evidence. Deadline candidate has
   a same-state actuator baseline and is NOT presumed effective. All methods,
   thresholding and bootstrap are standard; do not invent algorithm novelty.
3. Rewrite main around strongest 1--2 prospective findings. Current v8 main
   still exists. Keep author and IEEE format. Methods draft may need trimming.
   Move weak legacy material to clearly labeled SI; preserve old p=0.25 and
   historical source/provenance limitations, including missing F4 manifests.
4. Build new supplement generator/source/PDF with complete outcome/cluster,
   threshold, clock, exposure, compute and historical-audit tables. Preserve
   named v8 PDFs unchanged. Latest main.pdf and supplement.pdf must match source.
5. Finish/update root README, REPRODUCE, artifact index and review materials,
   preserving previous versions under history. Distinguish replay from a fresh
   replication (new registration) and never promise cross-platform bit identity.
6. Compile, verify citations/layout/fonts/p5 rule, inspect all pages. Generate
   versioned v9 PDFs, source/raw-data artifact ZIP + hashes, no dependency cache
   or huge external matrices. Verify original raw/archive hashes unchanged.
7. Deliver Chinese change/status report, contribution decisions, final simulated
   three-perspective review and each Reject-risk status. Be candid if novelty,
   rare failures, one assumed RF map/model or missing public artifact still
   limit competitiveness. No commit/push/submission.

## 05:15 UTC continuation

Core remains frozen and running (session 46440); fixed follow-through workflow
PID 41296 started 04:59 UTC, its unified session ID was not retained. Do not
launch stress a second time: workflow verifies core, then starts stress itself.
A read-only resource sampler (session 57811) records 45-second OS process costs
in audit/acceptance-v9/resource-samples.jsonl. It began after core launch; values
are process samples/OS per-process peaks, not whole-campaign simultaneous peaks.

New nonfrozen tools: check_tests_v9.py, check_preservation_v9.py,
validate_release_v9.py, package_task_v9.py; source-bound PDF QA now saves PDF SHA
and fifth-page rule. Actual tiny Brian2 reset test passed (one test, 9.294 s);
full final suite expected at least 55, must run once at final code freeze.
Prior seven root/paper docs preserved in docs/history/assessment-v8/.

New independent-warning comparison tool is SECONDARY and was added after
registration, before complete independent outcomes. It reports paired error
differences and the number of valid bootstrap resamples for sparse classes;
never claim it was part of the original JSON registration. Run separately after
core/stress analyses; no threshold/seed/sample change follows. Primary sign-flip
tests remain only the two registered controller contrasts.

Development figure v3 was visually inspected and is clear. Supplement builder
now uses portable relative source keys and binds title source main.tex. Main
introduction/related-work and Methods drafts exist as sections/v9_*.tex, still
not included in current main.tex; actual current PDFs remain v8 until promotion.

05:18 UTC: registered a separate 64-episode / eight-cluster action-ablation
check (seeds1200--1207) BEFORE complete core analysis, to verify dependence on
steering/burst interface. Details in PROTOCOL_v9.md. It is secondary, not part
of original confirmatory registration. New registration-causal.json freezes
FOUR MORE tools: launch_causal_v9.py, analyze_causal_v9.py, replay_causal_v9.py,
finish_causal_v9.py. DO NOT EDIT THEM. Causal workflow session71999 waits for
core+stress completion, then runs its three workers, analysis and independent
replay, with deadline-only cancellation. Do not launch twice. Expected new
independent/diagnostic episodes448 plus74 development/validation, never pooled
for inference. Main+SI/package validation should bind this separate cohort.

The baseline preservation audit passed:3991 inherited experiment/audit files
and both named v8 PDFs are byte-identical to backup. Current report is in
audit/acceptance-v9/preservation-prewriting/check.json; recheck at finalization.

06:55 UTC checkpoint: core199/288, all three workers active, no aggregate
analysis performed. Metadata-only checks confirmed all three batches exactly
match registered Python/packages, model/table hashes, annotation hash and
generating snapshots; no frozen source changed. Resource monitor57811 continues.
Progress-observer cells153/157 finished; safe to poll resource session again.

Initial Chinese review diagnosis is paper/REVIEW_DIAGNOSIS_V9_zh.md (opened/queued
in Codex). Main Methods draft shortened to666 TeX-split words; exact LIF
equations moved into supplement generator, not dropped. Main still v8 until
independent results are available. All baseline named PDFs remain unchanged.

New nonfrozen change_review_v9.py can produce source-review.patch versus the
inherited DIRTY workspace, using the safe backup ZIP/manifest. It excludes raw
data and history/caches from inline diffs. Run at final source freeze. Package
audit extension allowlist still needs .patch added if including this diff.

Supplement builder now requires completed separate causal data/replay and
binds all74 development/validation records as well as448 new core/stress/causal
records. Final validator checks 55+ tests, all-page visual records, all three
cohort audits and registered validation/calibration raw hashes. Root final
reports and README/REPRODUCE promotion, PDF builds, quantitative plots,
comparisons tool and all final checks are still pending.

08:14 UTC IMPORTANT: core288/288 finished successfully, elapsed14393.307s,
all workers exit0. The ORIGINAL FROZEN analyzer hit a CSV dictionary duplicate
key before any outputs: features deadline/schedule_only numeric margins share
names with Boolean flags. Do NOT edit the frozen file. New
analyze_task_v9_exportfix.py changes ONLY numeric CSV names to
deadline_margin_m/schedule_margin_m; all numerical definitions unchanged.
Original failure log/empty core dir preserved. Corrected workflow is session4421,
finish_measurements_v9_corrected.py, marker measurement-workflow-corrected-start.
It writes canonical analyses core-v2 and stress-v2, original replay-core/stress
and numbers-core/stress, then measurements-complete.json. Causal waiting71999
will still start automatically on that marker. Do not duplicate stress.
Validator and current reproduction docs now use exportfix/core-v2/stress-v2.
Full disclosure in PROTOCOL_v9_NOTES.md. Main/SI numeric work can now begin.

Another correction clarified registration planning precision:0.20 applies to
[0,1] mean only, signed netloss/interaction range-based normal approximations
0.40/0.80. Original registrations retained unchanged; no N or hypothesis change.
Notes also distinguish paired stop normalization from validation-reference
400-ms warnings. Stdlib verify_artifact_v9.py was added; package .patch allowed.

08:29 UTC core RESULTS verified: all96 healthy survive; P25=46/48 R25=48/48;
P50=37/48 (negative14/24 positive23/24),R50=48/48. Registered R-minus-P
contrast50=-22.9167pp,clusterCI[-33.3333,-12.5],11 nonzero seed contrasts,
rawp.0009765625,Holm.001953125. Dose25=-4.1667pp,CI[-10.4167,0],p.5,
2 nonzero. No gains.13 collisions in12 clusters, earliest607.599ms; only2
collisions by800/900ms vs13 at1s. All stop/common group medians identical;
max pair change.00324257. So B median exposure headline withdrawn; C50+A
are main findings, horizon dependence retained. D conditional candidate:13TP
0FN57FP/275successes vs schedule84FP; specificitygain9.818ppCI[6.569,13.406]
from post-registration descriptive compare tool, not novelalgorithm. Command
2TP11FN51FP; two-sided3TP10FN68FP; upper0TP0FP13FN.

Posthoc control diagnostic verifies all144 P/R paired scenarios have identical
trigger and predecision traces. At400ms median absolute headings P50=38.73deg,
R50=96deg; healthyP88.27/R100. Equal maxgain but actual turning differs, not
matched energy or mediation proof. Diagnostic saved under control-diagnostic-core.

Corrected workflow4421 started stress08:15:14UTC, still running. Causal71999
will start only after stress verifies; unchanged. Resource57811 still logs.

Core figures v1 had legend overlap and were preserved; fixed figures-v2 all
three PDFs/PNGs viewed, clear, latest main copies those PDFs. Main rewritten
with new sections/v9_intro,related,methods,results,artifact,discussion. Current
main-build-02 and main-qa-02 passed log/fonts/p5 rule, but final main source has
new artifact section/threshold details not yet recompiled. More importantly
main still needs COMPLETE stress+causal outcomes appended before final delivery.
Versioned named v9 PDFs NOT YET generated; original named v8 unchanged.

Main-build-01 failed on long paired-ratio equation; preserved. Shortened by
moving T* definition into prose, no font reduction. Moved wide outcomes figure
to start of Results to avoid a float-only fourth page. Build02 clean but fourth
page still partly empty; forthcoming stress/causal and artifact section will
fill useful content. Default IEEEtran font/spacing kept. Final main andSI need
all-page visual QA and source-bound final validation,55+tests, ZIP+standalone
verify, finalpreservation and source-review.patch. All rootfinalreports pending.

08:37 UTC: root README/REPRODUCE/STATE now point to v9 core and explicitly
mark stress/causal/finalPDF pending. Prior vision README also copied tohistory,
and its current top now distinguishes v9 from retained historical body.
PowerShell piped nonASCII Python source failed before execution under locale
encoding; use python -X utf8 for stdin scripts/Unicode document work. Do not
modify the frozen run_v9.py. File-based scientific tools work with ASCII JSON
and fixed sources; no experimental data were affected.

08:57 UTC update: stress still running (~51/96); expected completion around
09:40UTC due8 seeds split3/3/2 workers. Causal ~onehour after that. Metadata
checks confirm ALL three registrations' frozen source sets unchanged.
Root README, REPRODUCE, ARTIFACT_README, REVIEW_MATERIALS, paper/README,
vision README top and STATE now point at v9 and mark finalization pending.
Final text replacements MUST remove pending states only when true. Original
root docs and full vision README are preserved under docs/history/assessment-v8.

Main has new v9_artifact section and actual warning cutoffs since last build02.
Needs final stress/causal results before final compile. New SI generator now
binds core warning comparisons/control diagnostic, discloses CSV export fix,
planning precision range, and reference differences. No SI generated yet.
Source-only tests should use python -X utf8 on this cp1252 host. Final actual
suite expected55 (not yet run), no skipped tests allowed.

analysis-export-correction.patch/json prove corrected analyzer differs ONLY
in docstring plus renaming numeric CSV margins. Frozen original SHA40aac59...
and exportfixSHA33ec42c... are bound. Original core failure folder/log preserved.
Validator now uses core-v2/stress-v2, binds exportfix SHA plus descriptive source
results; all actual metrics and statistical code otherwise unchanged.

09:12 UTC FAIRNESS clarification: healthy success is96/96 but safety reserve
is NOT matched. Healthy minclearance medians P33.0839mm vsR41.4255mm
(range13.8804--39.6411 vs39.2441--42.1877). New descriptive
control-diagnostic-core-v2 adds healthy margins and sourceSHA4fcd8f...; v1
retained. Current SI/validator/index point at v2. Main now says identical healthy
SUCCESS COUNTS, not matched overall performance; C is whole-system context,
not fault-specific advantage independent of nominal reserve. No controller
retuning or new gain-matching experiments after observing test. Such matching
is future work, not claimed complete. Current frozen laws/thresholds unchanged.

Main Limitations explicitly states scalar rules aren't optimized classifiers,
2x count isn't a validated budget, geometry predictors have extra information,
false alarms substantial. Active source still needs one finalcompile after
full stress/causal results; do not treat main-build02 as final.

09:36 UTC tests: prelayout55 initiallyhad1error onlyCLIpreflight. Fixed
NONFROZEN tools/check_reproduction.py to unwrap run_v9 target,handle simple
dynamicflag declarations, andacceptunique argparse abbreviations (ambiguous
rejected). Three newtests agree with actualargparse behavior. All58 passed
in23.024s/no skips at tests-prelayout-02. Thenadded a JSONreceipt --out plus
source/doc hashes tochecker andbound it infinalvalidator. This is a newcode
change, so final58 suite must run again (reusepriorpass aloneis stale).
FinalCLIreceipt pathrequired audit/acceptance-v9/reproduction-preflight.json,
generateonlyafter REPRODUCE final. Sourceguardsallthree registrationsunchanged.

Existingcore figure anddiagnostic v1 sourcecode reconstructed from exact
recordedpatches and SHA matched, preservedinside their dirs; currentv2 source
alsocopied. No experimentdataedited. Workflows4421/71999 continue;observer202
waits stress96; resource57811 stopsaftercore+stress flag. Aftercausal starts
needseparate count monitor (no causal RAM sampler needed; walltimes recorded).

09:40 UTC STRESS COMPLETED:96/96,elapsed4725.4648s, all workers0. Workflow
4421 exited0 after stress-v2/replay-stress/numbers-stress checks passed.
measurements-complete.json exists. Resource57811 nowdone;observer202done.
Stresshealthy32/32;25%32/32;P50=14/16(negative6/8 positive8/8),R50=16/16.
R-Pcontrast=-12.5ppCI[-31.25,0],rawp.5,Holm1,doNOTpoolorcallconfirmation.
Only2failures (bothnegative); frozen command1TP1FN40FP, two-sided0TP2FN43FP,
upper0TP2FN0FP, schedule2TP0FN21FP, held2TP0FN11FP among94successes.
Warningcomparison/controldiag-stress generated. Bootstrap sensitivity has
18024valid draws/1976no-positive draws; reportconditionalnature. Healthy
two-sidedactivityflags22/32 (scene transferpoor). Mainstressparagraphadded.

Causal started09:35:42UTC, workflow71999stillrunning. New count monitor
session57522 prints JSONprogress45s; use write_stdin toobserve, expected64.
No causal outcome analysis untilcomplete. Expectedfinish~10:30--10:40UTC.
Finalpaper sourcealreadyhascore+stress+artifact+marginqualifications, notyet
compiled afterbuild02. Causalparagraphmuststillbeaddedfromactualdata.
SIfinalbuilder requirescausal summary/replay; full58tests+CLIreceipt+PDFQA+
finalreports+preservation+validation+ZIP remain. UseUTF8 modeforlocale.

10:34 UTC FINAL EVIDENCE COMPLETE: causal64/64, launcher3142.772s/three exit0,
normal P/R16/16 each, steering-disabled0/16, both-neural-actions-disabled0/16;
all64 independent replay passed. Core288+stress96+causal64 remain separate.
Main-build04 matches paper/main.pdf:5pages, page5referencesonly. SI-build02
matches paper/supplement.tex/pdf:13pages. Both allfonts embedded/noType3/
nooverfull/undefinedrefs. All18pages reviewed; finalSIcaptionclarifies
degeneratebootstrapintervals, onlypage11pixelschangedandreinspected;
other12SIpagesbyte-identicalrenderstoindividuallyreviewedQA01.
Final tests02:59passed/no skips19.790s; codehashesbound. Plotv3fixes
feedbackreturnlinecrossinglabel, noquantitativedatachange. Originalfigures
andfailed/intermediatebuildsretained. README/report/indexcurrent.
Remaining release steps: refreshedCLIreceipt, dirty-baselinechange-review,
finalvalidation, source/dataZIPandindependentbytecheck; do notclaimpublished.
No additionalneuralworkplanned, no commit/push/submission.
