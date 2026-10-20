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

fig2, axs = plt.subplots(1, 1, figsize=(2.78, 0.62))
cal = json.loads((SIM / "results" / "calib" / "calibration.json").read_text())

ax = axs
for name, c in [("healthy", C_REAL), ("background", "#7f7f7f")]:
    rates = cal["conds"][name]["pop_rates"]
    ax.scatter(np.full(len(rates), 0 if name == "healthy" else 1) + np.random.default_rng(1).uniform(-0.08, 0.08, len(rates)),
               rates, s=6, color=c, alpha=0.8, label="escape drive" if name == "healthy" else "random sites")
ax.axhline(cal["threshold"], color="k", ls="--", lw=0.8)
ax.text(0.5, cal["threshold"] + 4, r"$\theta$", fontsize=8)
ax.set_xticks([0, 1])
ax.set_xticklabels(["escape drive\n(LC4+LPLC2)", "random-site\nstimulation (314)"], fontsize=7)
ax.set_ylabel("command-pop. rate (Hz)")
ax.legend(frameon=False, loc="center right", fontsize=7)
ax.spines[["top", "right"]].set_visible(False)
fig2.savefig(FIGS / "fig2_baseline.pdf")
plt.close(fig2)

fig3, axs = plt.subplots(1, 2, figsize=(7.0, 0.60), gridspec_kw={"wspace": 0.5})
jit = np.random.default_rng(3)
ax = axs[0]
fs = [0.05, 0.10, 0.25, 0.50]
conds_f2 = ["healthy"] + [f"F2_drop_{int(f*100):02d}" for f in fs]
xs_f2 = [0.0] + fs
r = [med(agg("real", c)["rates"]) for c in conds_f2]
lat = [med(agg("real", c)["lat"]) for c in conds_f2]
for x, c in zip(xs_f2, conds_f2):
    a = agg("real", c)
    ax.scatter(np.full(a["n"], x) + jit.uniform(-0.012, 0.012, a["n"]), a["rates"], s=4, color=C_REAL, alpha=0.35, lw=0)
lo = [float(np.percentile(agg("real", c)["rates"], 10)) for c in conds_f2]
hi = [float(np.percentile(agg("real", c)["rates"], 90)) for c in conds_f2]
ax.errorbar(xs_f2, r, yerr=[np.array(r) - lo, np.array(hi) - r], color=C_REAL, fmt="o-", lw=1.2, ms=3.5, capsize=2, label="command rate")
ax.set_xlabel("connection dropout fraction")
ax.set_ylabel("command rate (Hz)")
ax2 = ax.twinx()
llo = [float(np.nanpercentile(agg("real", c)["lat"], 10)) for c in conds_f2]
lhi = [float(np.nanpercentile(agg("real", c)["lat"], 90)) for c in conds_f2]
for x, c in zip(xs_f2, conds_f2):
    a = agg("real", c)
    ax2.scatter(np.full(a["n"], x) + jit.uniform(-0.012, 0.012, a["n"]), a["lat"], s=4, color="#ff7f0e", alpha=0.3, lw=0)
ax2.errorbar(xs_f2, lat, yerr=[np.array(lat) - llo, np.array(lhi) - lat], color="#ff7f0e", fmt="s--", lw=1.2, ms=3.5, capsize=2)
ax2.set_ylim(3.5, 6.5)
ax2.set_ylabel("latency (ms)", color="#ff7f0e")
ax2.tick_params(axis="y", colors="#ff7f0e")
ax.set_title("(a) F2 connection dropout")
ax.set_ylim(60, 130)
ax.spines[["top"]].set_visible(False)
ax2.spines[["top"]].set_visible(False)

ax = axs[1]
hs = [0.01, 0.02, 0.05]
conds_f4 = ["healthy"] + [f"F4_hub_{h}" for h in ["1pct", "2pct", "5pct"]]
xs_f4 = [0.0] + hs
r = [med(agg("real", c)["rates"]) for c in conds_f4]
tot = [med(agg("real", c)["tot"]) for c in conds_f4]
for x, c in zip(xs_f4, conds_f4):
    a = agg("real", c)
    ax.scatter(np.full(a["n"], x) + jit.uniform(-0.0016, 0.0016, a["n"]), a["rates"], s=4, color=C_REAL, alpha=0.35, lw=0)
lo = [float(np.percentile(agg("real", c)["rates"], 10)) for c in conds_f4]
hi = [float(np.percentile(agg("real", c)["rates"], 90)) for c in conds_f4]
ax.errorbar(xs_f4, r, yerr=[np.array(r) - lo, np.array(hi) - r], color=C_REAL, fmt="o-", lw=1.2, ms=3.5, capsize=2, label="command rate")
ax.set_xlabel("hub-silencing fraction (top contact count)")
ax.set_ylabel("command rate (Hz)")
ax4 = ax.twinx()
ax4.errorbar(xs_f4, [t / 1000 for t in tot], yerr=[np.zeros(4), np.zeros(4)], color="#ff7f0e", fmt="s--", lw=1.2, ms=3.5, capsize=2)
ax4.set_ylabel("total spikes (k)", color="#ff7f0e")
ax4.tick_params(axis="y", colors="#ff7f0e")
ax.set_title("(b) F4 hub silencing")
h_rate, h_tot = med(agg("real", "healthy")["rates"]), med(agg("real", "healthy")["tot"]) / 1000
ax.axhline(h_rate, color="gray", ls=":", lw=0.7, zorder=0)
ax4.axhline(h_tot, color="gray", ls=":", lw=0.7, zorder=0)
ax.set_ylim(60, 135)
ax4.set_ylim(28, 56)
ax.spines[["top"]].set_visible(False)
ax4.spines[["top"]].set_visible(False)
fig3.savefig(FIGS / "fig3_curves.pdf")
plt.close(fig3)

fig4, axs = plt.subplots(1, 2, figsize=(7.0, 0.50))
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
ax.set_title("(a) Pathway decay: real $\\approx$ null")
ax.legend(frameon=False, fontsize=6, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)

ax = axs[1]
hs = json.loads((SIM / "results" / "graph" / "hub_sign.json").read_text())
order = [("healthy", "healthy"), ("F4_1pct", "hub 1%"), ("HUB_inh", "inh. only"),
         ("HUB_exc", "exc. only"), ("INHrand_mass", "rand. inh.\n8.6%")]
vals = [hs[k]["tot"] / 1000 for k, _ in order]
labs = [v for _, v in order]
xs = np.arange(len(order))
cols = ["#4c72b0", "#4c72b0", "#d62728", "#7f7f7f", "#7f7f7f"]
ax.bar(xs, vals, 0.7, color=cols)
for i, (k, _) in enumerate(order):
    ax.text(xs[i], vals[i] * 1.12, f"{vals[i]:.0f}", ha="center", va="bottom", fontsize=5.6)
ax.axhline(hs["healthy"]["tot"] / 1000 * 2, color="k", ls=":", lw=0.7)
ax.text(-0.45, hs["healthy"]["tot"] / 1000 * 2.25, "2$\\times$ healthy", fontsize=5.4, ha="left", va="bottom")
ax.set_xlim(-0.6, 4.6)
ax.set_yscale("log")
ax.set_ylim(20, 1600)
ax.set_xticks(xs)
ax.set_xticklabels(labs, fontsize=6.2)
ax.set_ylabel("total spikes (k)")
ax.set_title("(b) Hub silencing: activity by sign")
ax.spines[["top", "right"]].set_visible(False)
fig4.savefig(FIGS / "fig4_topology.pdf")
plt.close(fig4)

print("figures written to", FIGS)
for k in ["healthy", "F2_drop_50", "F4_hub_1pct", "F5_in_both"]:
    print(k, json.dumps(summary["real"][k], default=float))
