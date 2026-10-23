import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "docs" / "img" / "hero.png"
ASSETS = Path("/tmp")

BG = "#050810"
CYAN = "#22d3ee"
VIOLET = "#7c6cf0"
ORANGE = "#f59e0b"
RED = "#ef4444"
GHOST = "#8a93a6"

W, H = 2400, 1160
fig = plt.figure(figsize=(W / 200, H / 200), dpi=200)
fig.patch.set_facecolor(BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

PANEL_W, PANEL_H, GAP = 420, 620, 60
X0, PANEL_Y = 35, 340
slots = [X0 + i * (PANEL_W + GAP) for i in range(5)]


def fit(path, w, h):
    im = Image.open(path).convert("RGB")
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s)))), s


def place(path, x, card=False, crop=None):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    s = min(PANEL_W / im.width, PANEL_H / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)))
    pw, ph = im.size
    px, py = x + (PANEL_W - pw) / 2, PANEL_Y + (PANEL_H - ph) / 2
    if card:
        ax.add_patch(FancyBboxPatch((px - 10, py - 10), pw + 20, ph + 20,
                                    boxstyle="round,pad=2,rounding_size=14",
                                    fc="#ffffff", ec=CYAN, lw=1.6, alpha=0.96, zorder=2))
    ax.imshow(np.asarray(im), extent=[px, px + pw, py, py + ph], zorder=3, interpolation="lanczos")


def label(x, txt, y=304, size=16, color="#e8edf5"):
    ax.text(x + PANEL_W / 2, y, txt, ha="center", va="top", fontsize=size, color=color)


place(ASSETS / "fly.jpg", slots[0], card=True)
label(slots[0], "The animal")

place(ASSETS / "brain.png", slots[1], card=True)
label(slots[1], "Neuron census")

place(ASSETS / "fig1_pathway.png", slots[2], card=True)
label(slots[2], "Digital twin")

fx, fy = slots[3], PANEL_Y
ax.add_patch(FancyBboxPatch((fx + 6, fy + 6), PANEL_W - 12, PANEL_H - 12,
                            boxstyle="round,pad=2,rounding_size=14",
                            fc="#0b1322", ec="#1f3550", lw=1.4, zorder=2))
rng = np.random.default_rng(7)
gx, gy = fx + 40, fy + 150
cols, rows = 9, 6
for i in range(cols):
    for j in range(rows):
        dead = (i, j) in {(2, 1), (5, 4), (6, 0), (3, 3)}
        ax.add_patch(Circle((gx + i * 38, gy + j * 42), 7,
                            fc="#374657" if dead else CYAN, ec="none", alpha=0.55 if dead else 0.95, zorder=4))
for k, ((ci, cj), tag) in enumerate({(1, 4): "F1", (3, 2): "F2", (5, 5): "F3", (7, 3): "F4", (4, 0): "F5"}.items()):
    tx, ty = gx + ci * 38, gy + cj * 42
    ax.plot([tx + 24, tx + 4, tx + 16, tx - 2, tx + 10, tx],
            [fy + PANEL_H - 24, ty + 118, ty + 96, ty + 70, ty + 52, ty + 12],
            color=RED, lw=2.6, alpha=0.95, zorder=5, solid_capstyle="round")
    ax.text(tx + 30, ty + 74, tag, ha="center", fontsize=11, color="#ffffff",
            bbox=dict(boxstyle="round,pad=0.25", fc=RED, ec="none"), zorder=6)
trace_x = np.linspace(0, 1, 240)
trace = 94 + 2.0 * rng.normal(0, 1, 240) * 0.3 + 1.2 * np.sin(np.linspace(0, 9, 240))
ax.plot(fx + PANEL_W - 165 + trace_x * 130, fy + 52 + (trace - trace.min()) / (trace.max() - trace.min()) * 44,
        color=CYAN, lw=2.4, zorder=6)
ax.text(fx + PANEL_W - 100, fy + 128, "behavior survives", ha="center", fontsize=11, color=CYAN)
label(slots[3], "Fault injection F1\u2013F5")

place(ASSETS / "fig5_glance.png", slots[4], card=True)
label(slots[4], "Verdict")

for i in range(4):
    ax.text(slots[i] + PANEL_W + GAP / 2, PANEL_Y + PANEL_H / 2, "\u2192",
            ha="center", va="center", fontsize=34, color=CYAN, alpha=0.9)

ax.plot([30, W - 30], [262, 262], color="#1f2937", lw=1.0)

nodes = [("fly", "1.4\u00d710\u2075 neurons", 138_639),
         ("mouse", "~10\u2078 neurons", 70_000_000),
         ("human", "~10\u00b9\u00b9 neurons", 86_000_000_000),
         ("silicon", "no ceiling", None)]
xs = np.linspace(300, 2100, 4)
ax.annotate("", xy=(2280, 150), xytext=(140, 150),
            arrowprops=dict(arrowstyle="-|>", color=VIOLET, lw=2.4))
for (name, sub, n), x in zip(nodes, xs):
    if n is None:
        ax.add_patch(Polygon([(x, 150 + 34), (x + 30, 150), (x, 150 - 34), (x - 30, 150)],
                             closed=True, fc="none", ec=CYAN, lw=2.2))
    else:
        r = 16 + 30 * (np.log10(n) - 5) / 6
        ax.add_patch(Circle((x, 150), r, fc="none", ec=ORANGE, lw=2.2))
        ax.add_patch(Circle((x, 150), r * 0.45, fc=ORANGE, ec="none", alpha=0.35))
    ax.text(x, 150 - 62, name, ha="center", fontsize=17, color="#e8edf5", fontweight="bold")
    ax.text(x, 150 - 92, sub, ha="center", fontsize=12, color=GHOST)
ax.text(1200, 212, "One route, any substrate:  connectome \u2192 digital twin \u2192 fault injection \u2192 certified robustness",
        ha="center", fontsize=15, color=GHOST)

fig.savefig(OUT, facecolor=BG)
print("hero saved", OUT)
