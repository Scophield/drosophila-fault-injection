import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent / "results_vision"
FIG = Path(__file__).resolve().parent.parent / "paper" / "figs"


def load(tag, mode, fault, phi, seed):
    f = OUT / f"episodes_{tag}" / f"{mode}_{fault}_phi{int(phi)}_s{seed}.json"
    if not f.exists():
        f = OUT / f"episodes_{tag}" / f"{mode}_{fault}_phi{phi:g}_s{seed}.json"
    return json.load(f.open()) if f.exists() else None


def main():
    import sys
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'v4'
    phi, seed = -30.0, 0
    panels = [
        ("brain", "healthy", "no fault"),
        ("brain", "F2_50", "F2: 50% loss"),
        ("brain", "F4_1pct", "F4: hub silence"),
        ("steer_disabled", "healthy", "steering disabled"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(3.45, 0.95), sharex=True, sharey=True)
    for ax, (mode, fault, lbl) in zip(axes, panels):
        e = load(tag, mode, fault, phi, seed)
        if e is None:
            ax.set_visible(False)
            continue
        xs = [q["fly_x"] for q in e["log"]]
        ys = [q["fly_y"] for q in e["log"]]
        tx = [q["target_x"] for q in e["log"]]
        ty = [q["target_y"] for q in e["log"]]
        ax.plot(tx, ty, color="#888888", lw=0.8)
        ax.plot(xs, ys, color="#1f4e79", lw=1.2)
        ax.scatter([tx[-1]], [ty[-1]], s=14, color="#b03a2e", zorder=3)
        ax.scatter([xs[0]], [ys[0]], s=10, color="#1f4e79", zorder=3)
        hit = e["min_dist"] <= 0.05
        tag_txt = "contact" if hit else f"escaped"
        ax.set_title(f"{lbl}\n{tag_txt} ({e['min_dist']*100:.0f} cm)", fontsize=6.0, pad=1.8)
        ax.set_xlim(-0.06, 0.28)
        ax.set_ylim(-0.10, 0.20)
        ax.tick_params(labelsize=4.8, length=1.2)
        ax.set_aspect("equal")
    fig.text(0.5, 0.0, "x (m)", ha="center", fontsize=5.2)
    axes[0].set_ylabel("y (m)", fontsize=5.2)
    fig.tight_layout(rect=(0, 0.02, 1, 1), h_pad=0.2, w_pad=0.2)
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "fig5_demo.pdf", bbox_inches="tight", pad_inches=0.01)
    print("saved", FIG / "fig5_demo.pdf")


if __name__ == "__main__":
    main()
