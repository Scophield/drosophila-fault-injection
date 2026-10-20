# Reproducing the ISCAS 2027 results

Every number in `paper/main.pdf` comes from one of the runs below. The archived
per-trial records in `sim/results/` and `sim_vision/results_vision/` are the
canonical realization; the scripts regenerate them.

## 1. Environment

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Pinned versions (the ones that produced the archived records):

| package | version |
|---|---|
| brian2 | 2.9.0 |
| numpy | 2.4.6 |
| pandas | 3.0.6 |
| scipy | 1.17.1 |
| matplotlib | 3.11.2 |
| pyarrow | 26.0.0 |
| Pillow | 12.3.0 |

Single core, CPython 3.11. The full network occupies ≈2.4 GB of RAM; do not run
two whole-brain trials concurrently on a 4 GB machine.

## 2. Data

The connectome is not redistributed here. Clone the released model next to this
repository:

```bash
git clone https://github.com/philshiu/Drosophila_brain_model.git
```

Expected layout: `<parent>/Drosophila_brain_model/` and `<parent>/drosophila-fault-injection/`.
Verify the two files every number depends on:

```
Connectivity_783.parquet  sha256 efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347
Completeness_783.csv      sha256 bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311
```

## 3. Seeds

`seeds.json` lists the integer seed used for every (condition, trial) pair.

- Open loop: `int(sha256("<phase>|<condition>|<trial>")[:16], 16)`, phase `real`.
- Controls: `int(sha256("ctrl|<condition>|<trial>")[:16], 16)`.
- Closed loop: `brian2.seed(20000 + s)`, `numpy.default_rng(10000 + s)`, `s ∈ {0,1,2}`.

Regenerate and check the table with `python3 sim/seed_table.py`. The stimulus
Poisson stream is deliberately *not* re-seeded per trial, so a rerun is
statistically equivalent to the archive rather than bit-identical; this models
repeated runs on the same hardware and is stated in the paper.

## 4. Runs

```bash
cd sim
python3 calibrate.py            # threshold theta = 51.4 Hz; ~1 min
python3 sweep.py                # 19 conditions x 12 trials, real graph; ~1 h
python3 sweep.py --phase er     # same on the degree-matched graph; ~1 h
python3 pathway_analysis.py     # multi-hop route mass; ~1 min
python3 envelope.py             # two-criterion verdict table; seconds
python3 analyze.py              # Figs. 2-4 of the paper; seconds
python3 fig_pathway.py          # Fig. 1; seconds
```

```bash
cd ../sim_vision
python3 controls_openloop.py --cond all      # drive sweep, EIm, HUB_*, INHrand_*
python3 f4_recheck.py                        # F4 on the lean harness
python3 inhib_controls.py                    # 765-cell and 8,889-cell inhibitory controls
python3 run_closedloop.py --phis=-60,-30,30,60 --seeds 0,1,2 --tag v4c
python3 run_closedloop.py --phis=-60,-30,30,60 --seeds 0,1,2 --tag v4c --fault HUB_inh
python3 score_protocols.py                   # protocol re-scoring (Section IV-C)
```

## 5. Expected outputs

| artefact | content |
|---|---|
| `sim/results/real/*.jsonl` | 19 conditions x 12 trials, open loop |
| `sim/results/er/*.jsonl` | same, degree-matched graph |
| `sim/results/protocol_scores.json` | transmission-only vs envelope pass counts (276/288 vs 262/288) |
| `sim/results/graph/hub_sign.json` | activity by sign, Fig. 3(b) |
| `sim_vision/results_vision/openloop_controls/*.jsonl` | drive sweep and sign-matched controls |
| `sim_vision/results_vision/episodes_v4c/*.json` | 12 closed-loop episodes per condition |

Reference medians (12 trials, 150 Hz drive): healthy 94.7 Hz / 39.7k spikes;
F4 1% 119.1 Hz / 49.3k; inhibitory hubs only 168.2 Hz / 846.9k; excitatory hubs
only 88.6 Hz / 32.3k; 8,889 random inhibitory cells 102.4 Hz / 50.3k; F5 both
0.0 Hz.

## 6. Paper

```bash
cd paper
rm -f main.aux main.bbl main.blg main.fls main.fdb_latexmk main.log
latexmk -pdf main.tex
```

Requires TeX Live with IEEEtran and the `cite` package. Output: 5 pages, the
fifth carrying references only.
