# Checked evidence for paired closed-loop SNN fault assessment — V10

This is the authorized curated publication layer of the full research project.
The frozen V10 **code/data** reference is
[986ff54193fee6a1b95815499a4a3477b15ea49a](https://github.com/Scophield/drosophila-fault-injection/tree/986ff54193fee6a1b95815499a4a3477b15ea49a).
It includes the pre-citation manuscript candidate. This later checkout adds the
final paper with that real code/data citation; `PUBLIC_SCOPE.json` binds its
exact PDF/source bytes, and the enclosing Git commit identifies the complete
final-paper package. Use `git rev-parse HEAD` and pin that full SHA when citing
the final manuscript. A PDF cannot contain the hash of its own enclosing commit.

Scientific baseline:43bcd4d6a99b2d9b258cf8a198a4545d237b5c39. That V9 parent
does NOT identify V10. The curated branch has independent distribution history
to avoid republishing unresolved-license tables in inherited Git history.
Original generation HEADs, frozen registrations, source snapshots, observations
and negative results are retained. No GitHub Release or main/V9 update was made.

The main paper is self-contained within four technical pages. ISCAS2027 does
not accept supplementary materials. The24-page research archive is retained
privately as history; it is not a submission attachment or required reading.

Obtain the final branch in a NEW directory and record the actual full commit:

```text
git clone --single-branch --branch artifact/iscas2027-v10-final https://github.com/Scophield/drosophila-fault-injection.git v10-evidence
cd v10-evidence
git rev-parse HEAD
```

The paper's fixed code/data citation deliberately identifies the earlier frozen
data snapshot. The final-paper delivery receipt provides the enclosing final
manuscript commit. Do not substitute V9 or that earlier candidate for the final PDF.

## Evidence and boundaries

- Two native schemas use one common checker. Each detects11common-checker and
  3native-only predefined challenges; this is not general error coverage.
- An independent delayed tank has96actual episodes, all safe; it demonstrates
  limited reuse, not superior fault tolerance. A synthetic logger that never
  solves neural dynamics can pass replay: consistency is not execution authentication.
- RF-0 uses24test clusters/288episodes; RF-A/B each12clusters/144episodes.
  Each seed contains all directions/laws/faults. RF-A/B are independent draws
  from the SAME prior, with separate development/validation/recalibration.
- New50%law contrasts are both−4.17pp,95%CI[−12.5,0], four-test Holm p=1.
  This is not equivalence or stable replication of the larger baseline contrast.
- Saved-trace replay does not rerun neural dynamics. Same-host clean dependency
  installation has been exercised; second-host neural replication has not.

## Minimal saved-record checks

Use CPython3.12, a NEW virtual environment and NEW output directories. Create it:

```text
python -m venv .venv
```

Activate it before running the remaining commands: PowerShell
`.\.venv\Scripts\Activate.ps1`, or a POSIX shell `. .venv/bin/activate`.
Then install the minimal pinned packages:

```text
python -m pip install -r requirements-saved-v10.txt
python -c "from pathlib import Path; Path('tmp').mkdir(exist_ok=True)"
python -X utf8 tools/run_v9.py tools/analyze_task_v9_exportfix.py --root runs/task-v9-test --registration runs/task-v9-frozen/registration-core.json --out output/core
python -X utf8 tools/run_v9.py tools/analyze_task_v10.py --root runs/task-v10-transfer/map-A/test --registration runs/task-v10-transfer/map-A/registration.json --out output/map-A
python -X utf8 tools/run_v9.py tools/analyze_task_v10.py --root runs/task-v10-transfer/map-B/test --registration runs/task-v10-transfer/map-B/registration.json --out output/map-B
python -X utf8 tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v9-test --calibration runs/task-v9-frozen/calibration.json --out output/core-replay
python -X utf8 tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v10-transfer/map-A/test --calibration runs/task-v10-transfer/map-A/calibration.json --out output/map-A-replay
python -X utf8 tools/run_v9.py tools/replay_audit_v9.py --root runs/task-v10-transfer/map-B/test --calibration runs/task-v10-transfer/map-B/calibration.json --out output/map-B-replay
python examples/tank_v10.py --out output/tank
```

Per-map significance fields are descriptive. The registered FOUR-test family
spans both new maps and both doses; use canonical
`audit/v10/transfer-01/summary.json` and the independent score check, not a
within-map two-test correction, for the reported secondary Holm p values.
Primary loss/gain/exposure, derived net loss, prespecified secondary
interactions/warnings and post-hoc clearance diagnostics remain distinct.

## Interface, figures, tests and paper

The complete scientific environment uses `requirements-v9.txt`; saved-analysis
checks above do not require Brian2 or external connectivity tables.

```text
python -X utf8 tools/run_v9.py tools/check_evidence_v10.py --out output/interface
python -X utf8 tools/run_v9.py tools/plot_v10f.py --out output/figures
python -X utf8 tools/run_v9.py tools/test_v10.py --out output/tests
powershell -File tools/build_v10.ps1 -SourceFile main_v10_final4.tex -BuildDirectory output/paper
```

Interface challenge execution imports pandas through the explicitly synthetic
logger witness; figure rebuilding additionally needs matplotlib/PyMuPDF.
The full test suite includes a tiny actual Brian2 reset test, not a connectome
simulation. Plot source CSVs, saved counts, input hashes and source snapshots
are retained. No simulation, threshold or seed is changed by plotting.
Build from the repository root. MiKTeX/TeXLive with IEEEtran,AMS,cite,graphicx,
booktabs,placeins,url and BibTeX is required. The locked Fig.1 PDF is included
byte-for-byte; rebuilding the paper does not regenerate approved Blender art.
Use a relative output directory for Python commands; the PowerShell build
script resolves the supplied new directory against the repository working directory.

## External inputs deliberately not redistributed

`PUBLIC_SCOPE.json` enumerates exact bytes and explicitly omitted inputs.
The annotation dump, transformed completeness/connectivity tables and original
private Blender projects are not bundled. MIT applies to project code and the
identified upstream model code copies, not all upstream datasets. Full-neural
reruns require the pinned model, separate annotations and hash/runtime checks;
they are not implied by successfully re-scoring saved records.

Obtain model inputs from philshiu/Drosophila_brain_model at
91bdd1e7dcf193f3e7ca5a8933497fcef63b7960. Original text inputs used CRLF
checkout representations; Parquet bytes match upstream exactly. Annotations
originate at flyconnectome/flywire_annotations commit
a83b2776d60d5764cef36b927f5f9679c16c47a2. See
`docs/THIRD_PARTY_INPUTS_V10.md` for source URLs, hashes, attribution and unresolved
annotation/transformed-table terms. New runs need a separate compatible
registration and output directory; do not rewrite frozen records to disguise
changed runtime/input versions. Traceable Poisson seeds do not promise
bit-identical trajectories across platforms.
