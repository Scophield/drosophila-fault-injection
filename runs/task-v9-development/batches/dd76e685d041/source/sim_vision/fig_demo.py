import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
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
    global OUT, FIG
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--tag',default='v4')
    ap.add_argument('--input',type=Path,default=OUT)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    OUT=args.input
    FIG=args.out
    tag=args.tag
    phi, seed = -30.0, 0
    panels = [
        ("brain", "healthy", "healthy"),
        ("brain", "F2_50", "F2 50%"),
        ("brain", "F4_1pct", "F4 hub"),
        ("steer_disabled", "healthy", "steer off"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(3.45, 1.08), sharex=True, sharey=True)
    for ax, (mode, fault, lbl) in zip(axes, panels):
        e = load(tag, mode, fault, phi, seed)
        if e is None:
            raise FileNotFoundError(f'missing panel {tag}/{mode}/{fault}/{phi}/{seed}')
        xs = [q["fly_x"] for q in e["log"]]
        ys = [q["fly_y"] for q in e["log"]]
        tx = [q["target_x"] for q in e["log"]]
        ty = [q["target_y"] for q in e["log"]]
        ax.plot(tx, ty, color="#888888", lw=0.8)
        ax.plot(xs, ys, color="#1f4e79", lw=1.2)
        ax.scatter([tx[-1]], [ty[-1]], s=14, color="#b03a2e", zorder=3)
        ax.scatter([xs[0]], [ys[0]], s=10, color="#1f4e79", zorder=3)
        ax.set_title(f"{lbl}\n{e['min_dist']*100:.0f} cm", fontsize=7.5, pad=1.6)
        ax.set_xlim(-0.06, 0.28)
        ax.set_ylim(-0.10, 0.20)
        ax.set_xticks([0.0, 0.2]); ax.set_yticks([0.0, 0.2])
        ax.tick_params(labelsize=8.0, length=2.0)
        ax.set_aspect("equal")
    fig.text(0.5, 0.035, "x (m)", ha="center", va="center", fontsize=8.0)
    axes[0].set_ylabel("y (m)", fontsize=8.0)
    fig.tight_layout(rect=(0, 0.09, 1, 1), h_pad=0.2, w_pad=0.7)
    FIG.mkdir(parents=True,exist_ok=True)
    if (FIG/'fig5_demo.pdf').exists():
        raise FileExistsError(FIG/'fig5_demo.pdf')
    fig.savefig(FIG / "fig5_demo.pdf", bbox_inches="tight", pad_inches=0.01)
    print("saved", FIG / "fig5_demo.pdf")


if __name__ == "__main__":
    main()
