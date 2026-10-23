# Endpoint and Exposure Sensitivity in Fault Assessment

**A Fly-Connectome Spiking Model**
Shuchao Gao, Waseda University. ISCAS 2027 working paper.

Current revision: `assessment-v8`. Start with [REVIEW_MATERIALS.md](REVIEW_MATERIALS.md),
the [five-page manuscript](paper/fly_connectome_fault_assessment_v8.pdf),
the [supplement](paper/fly_connectome_supplement_v8.pdf), and
[the major-revision response](REVISION_V8_REPORT_zh.md).
The [v8 protocol](paper/PROTOCOL_v8.md) fixes the two-law, three-network-condition
matrix on six shared seed clusters and two bearings: 24 preserved healthy records
plus 48 new fault episodes. Paired losses, gains, net loss and same-law activity
ratios distinguish fault effects from baseline controller success.
Original tests remain in `runs/geometry-v3/`; healthy controls and refractory
checks remain in `runs/controller-v4a/` and `runs/refractory-v4/`. The new matrix
is in `runs/controller-fault-v8/`, with analysis in `audit/controller-fault-v8/`.
The older sections below describe the historical archive, with weaker evidence
for undocumented hub selections and legacy geometry. No corrected-hub or hardware
result is claimed.

The paper re-analyzes the archive from commit
`051dcb6a3123841041a34d3b43395e2841975879`. Corrected hub-selection code has **not**
been simulated; hub-specific design conclusions have been withdrawn. See
[REVISION_REPORT.md](REVISION_REPORT.md), [paper/PROTOCOL_v2.md](paper/PROTOCOL_v2.md)
and [REPRODUCE.md](REPRODUCE.md). The earlier REPAIR_REPORT records a superseded repair stage.

## Verified archive results

The main sweep drives 314 LC4/LPLC2 cells at 150 Hz in a 138,639-neuron Brian2 LIF
model (15,091,983 connections). Nineteen conditions per real/null phase use 12 trials
of 600 ms. Selected controls use 75/150/300 Hz. This limited scan cannot establish
drive invariance, a universal power law or a causal mechanism.

| Archived condition | Median command rate | Activity / interpretation |
|---|---:|---|
| Healthy | 94.6875 Hz | 39,694 spikes |
| 50% connection deletion | 72.4 Hz | 76.46% retention; latency +33% |
| 10% random-unit output silencing | 95.1 Hz | median rate retained |
| Full 1% hub lesion | 119.1 Hz | 49,272.5 spikes, 1.24x healthy |
| Inhibitory hub subset | 168.2 Hz | 847,476.5 spikes median (847,857 mean), 21.4x |
| Excitatory hub subset | 88.6 Hz | 32,265 spikes median |
| Random inhibitory expected-contact-mass control | 102.4 Hz | 1.27x median; **2/12 exceed 2x**, IDs 3 and 9 |
| Both sensory outputs silenced | 0 Hz | no transmission |
| Target-permuted null | 0 Hz median | no main-sweep trial reaches threshold |

For deletion `f=0.05/0.10/0.25/0.50` and survival `p=1-f`, output retention is
0.9703/0.9835/0.8922/0.7646. Retention divided by survival is
1.021/1.093/1.190/1.529. This is descriptive sub-proportional degradation; no causal
mechanism is identified. The invalid historical pathway-mass plot is excluded from the paper.

The random inhibitory control targets **expected outgoing contact mass**, not
identical edge count. Its 8.6% edge removal differs from the inhibitory hubs' 5.6%.
Trials 3 and 9 have 327,246 and 271,058 spikes (8.24x and 6.83x healthy). A low median
cannot establish safety of distributed lesions.

Transmission-only re-scoring of the same 288 archived fault/control records yields
276 passes; the per-trial joint rate/spike envelope yields 262. The additional
failures are 12 HUB_inh and two INHrand_mass trials. **Neither SpikeFI nor SpikingJET
was run as a benchmark.** Threshold invariance applies only to the main 150 Hz
sweep; F2_50 at 75 Hz passes 10/12 at the 51.4 Hz threshold.

The legacy synthetic demo distinguishes recorded survival from activity compliance:

- Healthy: six of the former 24/24 logs duplicate calibration episodes. Excluding
  them leaves 18/18 non-overlapping records (6 negative-azimuth, 12 positive); frontal 0/3.
  The positive subset includes calibration seeds at new azimuths; this is a post-hoc split.
- F2_25: 10/12 escapes; F2_50: 0/12.
- Full F4: 12/12 escapes, but **6/12 exceed 2x paired healthy spikes**. Median
  pair ratio 1.703x; negative azimuths reach 2.06–2.32x, positive azimuths 1.28–1.35x.
- HUB_inh: 6/12 escapes, 12/12 bursts, 12/12 activity exceedances; median pair ratio
  71.7x. These archived observations await corrected-selector reruns.
- Steering-disabled, readout-disabled and sign-flipped controls: 0/12 each;
  scene-reading hand rule: 12/12.

The legacy recording horizon is 1 s, with early collision termination. Eight healthy
episodes end during a burst. At a common first 400 ms, F2_50's median paired spike
ratio is 0.723 rather than 0.382 for whole episodes. Full F4 changes from 1.703 to
1.362, with 0/12 rather than 6/12 exceeding 2x within this window. These different
exposures answer different questions. Fresh geometry-v2 code uses actual distance,
body-frame bearing, an explicit fixed horizon and passive calibration with new test
seeds. Actual corrected-geometry campaigns are now included under `runs/geometry-v3/`,
`runs/controller-v4a/` and `runs/controller-fault-v8/`; the legacy illustrations
above are not substituted for those prospective records.

## Paper and lightweight audit

[Paper PDF](paper/main.pdf), [LaTeX entry](paper/main.tex), [sections](paper/sections/).
The cited figures and bibliography are tracked. Compile with a TeX distribution
including IEEEtran, cite, AMS packages and TikZ; no connectome is needed. Error bars
are 10th–90th trial percentiles, while 95% median CIs use 20,000 trial-record bootstrap
resamples, seed 0. See REPRODUCE for isolated builds and PDF/font QA.

```bash
python -m unittest discover -s tests -v
python tools/audit_archive.py --out audit/my-check
```

Use a new output directory. The audit saves source hashes, package versions, paired
scores and a generated `hub_sign.json`, preserving original records.

## Fresh simulation inputs and status

The external model/connectome is **not bundled**. The common resolver expects sibling
`<parent>/Drosophila_brain_model/`, or an explicit `FLY_MODEL_DIR`. The authorized sparse model checkout now supplies `model.py`,
`Connectivity_783.parquet` and `Completeness_783.csv`. Input-only reconstruction is saved
in `audit/verified-hubs/`; no whole-brain simulation was run. No submodules or LFS pointers were found; the 31.9 MB annotation file is
tracked. This checkout is not a complete experimental environment.

Fresh outputs require a new `FLY_RUN_DIR`. All four hub paths now share integer
contact ranking, FlyID protection and FlyID tie breaking, and save selected IDs/hashes
when executed. Synthetic tests and actual-input reconstruction pass: corrected 1% hubs have
766 inhibitory and 620 excitatory cells, versus 765/621 under the old index check.
The latter includes three protected command neurons. Fresh responses remain unmeasured. Historical real/ER damage counts differ; the ~100k to ~49k
activity change cannot be attributed solely to backend/chunking.

Fault seeds are traceable, but the unseeded main open-loop Poisson stream advances
across trials. Bit-identical replay is not promised. Closed-loop seeding remains
conditional on inputs, software and execution schedule. Full simulations require
separate resource confirmation; package/compiler requirements and commands are in
REPRODUCE. Old Chinese reports and review notes remain historical material rather
than the current specification.

## Credits

- Whole-brain LIF model and connectome tables: [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)
- Connectome: FlyWire Consortium — Dorkenwald et al., *Nature* 634, 124–138 (2024), doi:10.1038/s41586-024-07558-y (CC BY 4.0); cell-type annotations via Schlegel et al. 2023 (codex.flywire.ai).
- Escape-pathway neurobiology: Shuang et al. 2023; Fu & Card 2020 (see paper references).
- Fruit-fly photograph in the hero banner: André Karwath, Wikimedia Commons, CC BY-SA 2.5. The hero banner is a composite schematic (photo + FlyWire rendering + this repo's figures); the fault-injection panel is illustrative.

## License

MIT (see `LICENSE`). The bundled `sim/data/annotations.tsv` derives from the FlyWire annotation release (CC BY 4.0); the upstream connectome files remain under the terms of the original model repository.
