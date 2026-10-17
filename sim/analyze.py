import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
FIGS = SIM / "figs"
FIGS.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 3,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

THETA = 51.4


def agg(phase, cond):
    p = SIM / "results" / phase / f"{cond}.jsonl"
    if not p.exists():
        return None
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    rates = np.array([r["pop_rate"] for r in rows])
    lat = np.array([r["latency_ms"] if r["latency_ms"] is not None else np.nan for r in rows])
    tot = np.array([r["n_total_spikes"] for r in rows])
    dn2 = np.array([r["dn2_n"] for r in rows])
    return dict(rates=rates, lat=lat, tot=tot, dn2=dn2, n=len(rows))


def med(a):
    return float(np.nanmedian(a))


summary = {}
for phase in ["real", "er"]:
    summary[phase] = {}
    for p in sorted((SIM / "results" / phase).glob("*.jsonl")):
        a = agg(phase, p.stem)
        if a:
            summary[phase][p.stem] = {
                "rate_med": med(a["rates"]), "rate_p10": float(np.nanpercentile(a["rates"], 10)),
                "rate_p90": float(np.nanpercentile(a["rates"], 90)),
                "lat_med": med(a["lat"]), "tot_med": med(a["tot"]),
                "dn2_med": med(a["dn2"]), "succ": float(np.mean(a["rates"] >= THETA)),
                "n": a["n"],
            }
with open(SIM / "results" / "summary.json", "w") as f:
    json.dump(summary, f, indent=2)

C_REAL = "#1f77b4"
C_ER = "#d62728"
C_HL = "#2ca02c"

fig2, axs = plt.subplots(1, 1, figsize=(3.5, 1.55))
cal = json.loads((SIM / "results" / "calib" / "calibration.json").read_text())

ax = axs
for name, c in [("healthy", C_REAL), ("background", "#7f7f7f")]:
    rates = cal["conds"][name]["pop_rates"]
    ax.scatter(np.full(len(rates), 0 if name == "healthy" else 1) + np.random.default_rng(1).uniform(-0.08, 0.08, len(rates)),
               rates, s=6, color=c, alpha=0.8, label=name)
ax.axhline(cal["threshold"], color="k", ls="--", lw=0.8)
ax.text(0.5, cal["threshold"] + 4, r"$\theta$", fontsize=8)
ax.set_xticks([0, 1])
ax.set_xticklabels(["escape\n(LC4+LPLC2)", "background\n(314 rand)"], fontsize=7)
ax.set_ylabel("command-pop. rate (Hz)")
ax.legend(frameon=False, loc="center right", fontsize=7)
ax.spines[["top", "right"]].set_visible(False)
fig2.savefig(FIGS / "fig2_baseline.pdf")
plt.close(fig2)

fig3, axs = plt.subplots(1, 2, figsize=(7.0, 1.6), gridspec_kw={"wspace": 0.5})
ax = axs[0]
fs = [0.05, 0.10, 0.25, 0.50]
r = [med(agg("real", f"F2_drop_{int(f*100):02d}")["rates"]) for f in fs]
lat = [med(agg("real", f"F2_drop_{int(f*100):02d}")["lat"]) for f in fs]
ax.plot([0] + fs, [summary["real"]["healthy"]["rate_med"]] + r, "o-", color=C_REAL, label="command rate")
ax.set_xlabel("synapse dropout fraction")
ax.set_ylabel("command rate (Hz)")
ax2 = ax.twinx()
ax2.plot([0] + fs, [summary["real"]["healthy"]["lat_med"]] + lat, "s--", color="#ff7f0e", ms=3)
ax2.set_ylim(3.5, 6.5)
ax2.set_ylabel("latency (ms)", color="#ff7f0e")
ax2.tick_params(axis="y", colors="#ff7f0e")
ax.set_title("(a) F2 synapse dropout")
ax.set_ylim(60, 130)
ax.spines[["top"]].set_visible(False)
ax2.spines[["top"]].set_visible(False)

ax = axs[1]
hs = [0.01, 0.02, 0.05]
r = [med(agg("real", f"F4_hub_{h}") ["rates"]) for h in ["1pct", "2pct", "5pct"]]
tot = [med(agg("real", f"F4_hub_{h}")["tot"]) for h in ["1pct", "2pct", "5pct"]]
ax.plot([0] + hs, [summary["real"]["healthy"]["rate_med"]] + r, "o-", color=C_REAL, label="command rate")
ax.set_xlabel("hub-lesion fraction (top synapse count)")
ax.set_ylabel("command rate (Hz)")
ax4 = ax.twinx()
ax4.plot([0] + hs, [summary["real"]["healthy"]["tot_med"] / 1000] + [t / 1000 for t in tot], "s--", color="#ff7f0e", ms=3)
ax4.set_ylabel("total spikes (k)", color="#ff7f0e")
ax4.tick_params(axis="y", colors="#ff7f0e")
ax.set_title("(b) F4 hub lesion: dysregulation")
ax.set_ylim(60, 130)
ax.spines[["top"]].set_visible(False)
ax4.spines[["top"]].set_visible(False)
fig3.savefig(FIGS / "fig3_curves.pdf")
plt.close(fig3)

fig4, axs = plt.subplots(1, 2, figsize=(7.0, 1.25))
ax = axs[0]
pm = json.loads((SIM / "results" / "graph" / "pathway_mass.json").read_text())
ks = np.arange(1, 9)
for f, c in [(0.10, "#9467bd"), (0.25, "#ff7f0e"), (0.50, "#d62728")]:
    br = np.array(pm[f"real_{f}"]) / np.array(pm["real_0.0"])
    be = np.array(pm[f"er_{f}"]) / np.array(pm["er_0.0"])
    ax.plot(ks, br, "o-", color=c, ms=3, label=f"f={f}")
    ax.plot(ks, be, "x--", color=c, ms=3, alpha=0.6)
ax.set_xlabel("hops")
ax.set_ylabel("rel. pathway mass")
ax.set_title("(a) Pathway decay: real $\\approx$ ER")
ax.legend(frameon=False, fontsize=6, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)

ax = axs[1]
labs = ["healthy", "hub 1%", "hub 2%", "hub 5%"]
tr = [summary["real"][k]["tot_med"] / 1000 for k in ["healthy", "F4_hub_1pct", "F4_hub_2pct", "F4_hub_5pct"]]
te = [summary["er"][k]["tot_med"] / 1000 for k in ["healthy", "F4_hub_1pct", "F4_hub_2pct", "F4_hub_5pct"]]
xs = np.arange(4)
ax.bar(xs - 0.2, tr, 0.38, color=C_REAL, label="connectome")
ax.bar(xs + 0.2, te, 0.38, color=C_ER, label="ER null")
ax.set_xticks(xs)
ax.set_xticklabels(labs, fontsize=6.5)
ax.set_ylabel("total spikes (k)")
ax.set_title("(b) Hub-lesion runaway")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig4.savefig(FIGS / "fig4_topology.pdf")
plt.close(fig4)

print("figures written to", FIGS)
for k in ["healthy", "F2_drop_50", "F4_hub_1pct", "F5_in_both"]:
    print(k, json.dumps(summary["real"][k], default=float))
