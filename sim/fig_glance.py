import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
s = json.loads((ROOT / "results" / "summary.json").read_text())
r = s["real"]
e = s["er"]
healthy = r["healthy"]["rate_med"]

rows = [
    ("F1 weight noise $\\sigma{=}0.5$", r["F1_wvar_50"]["rate_med"] / healthy * 100, "#2e7d32"),
    ("F2 connection loss 50%", r["F2_drop_50"]["rate_med"] / healthy * 100, "#558b2f"),
    ("F3 unit silencing 10%", r["F3_loss_10"]["rate_med"] / healthy * 100, "#2e7d32"),
    ("F5 LC4 silenced", r["F5_in_LC4"]["rate_med"] / healthy * 100, "#1565c0"),
    ("F5 LPLC2 silenced", r["F5_in_LPLC2"]["rate_med"] / healthy * 100, "#1565c0"),
    ("F5 both channels", r["F5_in_both"]["rate_med"] / healthy * 100, "#b03a2e"),
    ("ER null (any condition)", 0.0, "#8a8a8a"),
]

fig, ax = plt.subplots(figsize=(7.0, 2.6), dpi=200)
labels = [x[0] for x in rows][::-1]
vals = [x[1] for x in rows][::-1]
cols = [x[2] for x in rows][::-1]
bars = ax.barh(labels, vals, color=cols, height=0.62, edgecolor="none")
for b, v in zip(bars, vals):
    ax.text(v + 1.5, b.get_y() + b.get_height() / 2, f"{v:.0f}%", va="center", fontsize=9, color="#333333")
ax.axvline(0, color="#444444", lw=0.8)
ax.set_xlim(-4, 124)
ax.set_xlabel("command-rate retention vs. healthy (%)", fontsize=10)
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=9)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)

hub = r["F4_hub_1pct"]
box = ax.text(0.985, 0.06,
              "F4 hub silencing (top 1%): rate 122.3 Hz (+29%),\nglobal activity 2.52$\\times$ — over-activity, not silence",
              transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
              bbox=dict(boxstyle="round,pad=0.45", fc="#fdecea", ec="#b03a2e", lw=0.9))
er_note = ax.text(0.99, 1.02,
                  "ER null preserves weights + out-degree but transmits nothing (0.0 Hz)",
                  transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, color="#555555")

fig.tight_layout()
fig.savefig(ROOT / "figs" / "fig5_glance.pdf", bbox_inches="tight", pad_inches=0.02)
out_png = ROOT.parent / "docs" / "img" / "fig5_glance.png"
if out_png.parent.exists():
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.02)
print("glance saved")
