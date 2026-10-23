import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation

OUT = Path(__file__).resolve().parent / "results_vision"
CMD_TYPES = ["DNp01", "DNa02", "DNp04", "DNb01"]


def load_episode(mode, fault, phi, seed, tag="main"):
    path = OUT / f"episodes_{tag}" / f"{mode}_{fault}_phi{int(phi)}_s{seed}.json"
    return json.loads(path.open().read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    ap.add_argument("--phi", type=int, default=-30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="demo_escape.mp4")
    args = ap.parse_args()
    panels = [("brain", "healthy"), ("brain", "F2_50"), ("brain", "F4_1pct")]
    eps = [load_episode(m, f, args.phi, args.seed, args.tag) for m, f in panels]
    n_frames = max(len(e["log"]) for e in eps)
    fig = plt.figure(figsize=(9.0, 6.6), dpi=110)
    gs = fig.add_gridspec(3, 2, width_ratios=[1.15, 1.0], hspace=0.55, wspace=0.3, left=0.06, right=0.97, top=0.93, bottom=0.06)
    axes_scene, axes_dn, bars, trails, tgt_dots, fly_dots, txt = [], [], [], [], [], [], []
    for r, (mode, fault) in enumerate(panels):
        ax = fig.add_subplot(gs[r, 0])
        axes_scene.append(ax)
        axd = fig.add_subplot(gs[r, 1])
        axes_dn.append(axd)
        x = np.arange(8)
        bars.append(axd.bar(x, np.zeros(8), color=["#4477aa"] * 4 + ["#ee6677"] * 4))
        axd.set_xticks(x)
        axd.set_xticklabels(["p01L", "p01R", "a02L", "a02R", "p04L", "p04R", "b01L", "b01R"], fontsize=6, rotation=45)
        axd.set_ylim(0, 260)
        axd.set_ylabel("DN rate (Hz)", fontsize=7)
        axd.tick_params(labelsize=6)
        e = eps[r]
        lbl = {"healthy": "no fault", "F2_50": "F2: 50% connection loss", "F4_1pct": "F4: hub output silencing (top 1%)"}[fault]
        title = fig.text(0.06, 0.955 - r * 0.315, "", fontsize=9, va="top")
        txt.append(title)
        ax.set_xlim(-0.35, 0.35)
        ax.set_ylim(-0.35, 0.35)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=6)
        ax.axhline(0, color="#dddddd", lw=0.5)
        ax.axvline(0, color="#dddddd", lw=0.5)
        fly_dot, = ax.plot([], [], "o", color="#222222", ms=5)
        tgt_dot, = ax.plot([], [], "o", color="#cc3311", ms=9, alpha=0.75)
        trail, = ax.plot([], [], "-", color="#888888", lw=0.8)
        arr = ax.annotate("", xy=(0, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="#222222", lw=1.2))
        fly_dots.append((fly_dot, arr))
        tgt_dots.append(tgt_dot)
        trails.append(trail)
    fig.suptitle(f"Vision-driven escape from a moving looming target (phi={args.phi} deg, seed {args.seed}; full 138k-neuron connectome LIF brain in the loop)", fontsize=9.5)

    def update(fr):
        for r, e in enumerate(eps):
            log = e["log"]
            k = min(fr, len(log) - 1)
            recs = log[: k + 1]
            fx = [q["fly_x"] for q in recs]
            fy = [q["fly_y"] for q in recs]
            trails[r].set_data(fx, fy)
            fly_dots[r][0].set_data([fx[-1]], [fy[-1]])
            a = fly_dots[r][1]
            hd = np.radians(log[k]["heading_deg"])
            a.xy = (fx[-1] + 0.05 * np.cos(hd), fy[-1] + 0.05 * np.sin(hd))
            a.xytext = (fx[-1], fy[-1])
            tx, ty = log[k]["target_x"], log[k]["target_y"]
            tgt_dots[r].set_data([tx], [ty])
            tgt_dots[r].set_markersize(max(4.0, 9.0 * log[k]["half_angle"] / 40.0))
            if "cmd_rates" in log[k]:
                for i, (ct, side) in enumerate([(c, sd) for c in CMD_TYPES for sd in ("left", "right")]):
                    bars[r][i].set_height(min(log[k]["cmd_rates"].get(f"{ct}_{side}", 0.0), 260.0))
            txt[r].set_text("")
            if k + 1 < len(log):
                txt[r].set_text(f"t={log[k]['t_ms']:.0f} ms  d={log[k]['dist']:.3f} m")
            else:
                res = "ESCAPED" if e["escaped"] else "CONTACT"
                txt[r].set_text(f"t={log[k]['t_ms']:.0f} ms  d={log[k]['dist']:.3f} m  -> {res} (min d {e['min_dist']:.3f} m, total spikes {e['n_total']/1000:.1f}k)")
        return []

    anim = animation.FuncAnimation(fig, update, frames=n_frames, interval=62, blit=False)
    anim.save(OUT / args.out, writer=animation.FFMpegWriter(fps=16, bitrate=2400))
    print(f"saved {OUT / args.out}")


if __name__ == "__main__":
    main()
