# Fault-Injection Analysis of a Whole-Connectome Spiking Controller

Artifact repository for the paper *"How Much Fault Tolerance Is in a Fly Brain? Fault-Injection Analysis of a Whole-Connectome Spiking Controller for Physical Intelligence"* (Shuchao Gao, Waseda University — ISCAS 2027 submission).

The code injects five hardware-motivated fault families into the released leaky integrate-and-fire (LIF) whole-brain model of *Drosophila melanogaster* (138,639 neurons, 15,091,983 signed synapses, FlyWire connectome) and measures behavioral outcome on the visuomotor escape pathway: 150 Hz Poisson drive to the looming-sensitive LC4 + LPLC2 populations (314 cells), scored as the population firing rate of the 8 descending command neurons (DNp01, DNa02, DNp04, DNb01) against a threshold θ = 51.4 Hz.

## Headline results (36 conditions × 12 seeded 600 ms trials each)

| Condition | Command rate (median) | vs. healthy (94.7 Hz) | Note |
|---|---|---|---|
| Healthy | 94.7 Hz (94.0–95.6) | — | 4.05 ms first-spike latency |
| Random-drive control | 8.2 Hz | 9% | total spikes 293k vs 40k — specificity, not arousal |
| F1 weight noise, σ = 0.5 | 94.7 Hz | 100% | flat through the dose |
| F2 synapse loss, 50% | 72.4 Hz | 76.5% | latency 4.05 → 5.4 ms (+33%) |
| F3 unit loss, 10% (~14k neurons) | 94.6 Hz | ~100% | flat through the dose |
| F4 hub loss, top 1% (9.1% of synapses) | 122.3 Hz (121.1–123.9) | **+29%, 2.52× global activity** | dysregulation, not silence |
| F5 both sensory channels silenced | 0.0 Hz (every trial) | 0% | the only catastrophic mode; brain keeps spiking (21.2k spikes) |
| ER null (edge-permuted control) | 0.0 Hz (every condition) | — | transmits nothing |

An edge-permuted Erdős–Rényi null with identical weight and out-degree statistics transmits nothing, while an analytic multi-hop pathway-mass analysis shows that *relative* route-mass decay under edge loss is topology-independent. Conclusion: functional robustness arises from **threshold amplification acting on convergent wiring**, not from graph redundancy alone — and the dangerous failure mode is hub-loss **dysregulation** (over-activity while every per-unit monitor reads "active"), not signal loss. See `REPORT_zh.md` for a detailed Chinese walkthrough of every experiment, and `paper/main.pdf` for the paper itself.

## Repository layout

```
├── paper/                 LaTeX source of the paper + compiled main.pdf + figure PDFs
├── docs/img/              PNG renders of the four paper figures (used by README/REPORT)
├── sim/
│   ├── engine.py          network construction + fault injection + trial runner (Brian2)
│   ├── calibrate.py       background calibration + θ placement (10-trial set)
│   ├── sweep.py           fault sweep over all 36 conditions (writes results/)
│   ├── analyze.py         dose-response figures from results/
│   ├── pathway_analysis.py  analytic multi-hop pathway mass m_k = ||A^k||_1
│   ├── fig_pathway.py     real-data escape-pathway figure (Fig. 1)
│   ├── data/annotations.tsv   FlyWire cell-type annotations (see Credits)
│   ├── results/           per-trial JSONL records, calibration, summary.json, pathway_mass.json
│   └── figs/              generated figure PDFs
```

## Setup

```bash
python3 -m pip install -r requirements.txt
```

The connectome itself is **not** bundled here. Clone the released model and place it next to this repository:

```bash
git clone https://github.com/philshiu/Drosophila_brain_model.git
# directory layout expected by the code:
#   <parent>/Drosophila_brain_model/   (Connectivity_783.parquet, Completeness_783.csv, ...)
#   <parent>/sim/                      (this repository)
```

## Reproduce

All runs are deterministic: fault realizations are derived from SHA-256 seeds, and every trial restores the full network state, so all conditions share identical initial states and background realizations. Every number in the paper is exactly reproducible.

```bash
cd sim
python3 calibrate.py           # ~1 min: background stats + threshold (10-trial set)
python3 sweep.py               # ~1 h single core: 36 conditions x 12 trials (real + ER)
python3 pathway_analysis.py    # ~1 min: multi-hop route-mass analysis
python3 analyze.py             # regenerates figs 2-4 (writes sim/figs/, copy to paper/figs/)
python3 fig_pathway.py         # regenerates Fig. 1 (writes sim/figs/ and paper/figs/)
```

Runtime: ≈3.5 s per 600 ms trial on one CPU core; the full sweep is minutes-to-an-hour on a laptop. Figures are written with embedded TrueType (Type 42) fonts to comply with IEEE PDF specifications (no Type 3 fonts).

## Output format

- `sim/results/real/*.jsonl`, `sim/results/er/*.jsonl` — one JSON record per trial: condition, seed, command rate, broad-readout rate, first-spike latency, total spikes.
- `sim/results/calib/calibration.json` — healthy/random calibration distributions and θ.
- `sim/results/summary.json` — per-condition medians, interdeciles, success fractions.
- `sim/results/graph/pathway_mass.json` — route mass m_k per graph per edge-loss level.

## Credits

- Whole-brain LIF model and connectome tables: [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)
- Connectome: FlyWire Consortium — Dorkenwald et al., *Nature* 634, 124–138 (2024), doi:10.1038/s41586-024-07558-y (CC BY 4.0); cell-type annotations via Schlegel et al. 2023 (codex.flywire.ai).
- Escape-pathway neurobiology: Shuang et al. 2023; Fu & Card 2020 (see paper references).

## License

MIT (see `LICENSE`). The bundled `sim/data/annotations.tsv` derives from the FlyWire annotation release (CC BY 4.0); the upstream connectome files remain under the terms of the original model repository.
