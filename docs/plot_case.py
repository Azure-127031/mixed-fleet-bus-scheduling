"""Redraw the README figure from the model coordinates and archived allocation."""
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "original"))
import goal

plt.rcdefaults()
navy, teal, orange = "#18344a", "#087c80", "#c45122"
fig, (network, flows) = plt.subplots(1, 2, figsize=(11, 4.55), gridspec_kw={"width_ratios": [1.14, 1]})
fig.subplots_adjust(left=.073, right=.965, top=.84, bottom=.19, wspace=.28)
case = json.loads((ROOT / "results/case.json").read_text(encoding="utf-8-sig"))
coords = np.array(goal.coords)
route = [goal.fixed_route1[0][0]] + [end for _, end in goal.fixed_route1]
network.plot(*coords[route].T, color=teal, linewidth=2.2, zorder=1)
for i, (x, y) in enumerate(coords):
    on_loop = i in route
    hub = i == route[0]
    network.scatter(x, y, marker="s" if hub else "o", s=77 if hub else 55,
                    color=orange if hub else (teal if on_loop else "white"),
                    edgecolor=orange if hub else (teal if on_loop else navy), linewidth=1.5, zorder=2)
    network.annotate(str(i + 1), (x, y), xytext=(4, 6), textcoords="offset points",
                     fontsize=10, color=navy, weight="bold")
network.set(xlabel="East–west coordinate (km)", ylabel="North–south coordinate (km)", xlim=(.5, 16.8), ylim=(1.8, 13.8))
network.set_aspect("equal", adjustable="box")
network.grid(color="#e1e7e8", linewidth=.65)
network.set_axisbelow(True)
network.spines[["top", "right"]].set_visible(False)
network.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))
network.set_title("Stops and fixed-route loop", color=navy, loc="left", fontsize=15, pad=13, weight="bold")
network.legend(handles=[
    Line2D([], [], marker="s", color=orange, ls="", label="Hub"),
    Line2D([], [], color=teal, marker="o", label="Fixed route"),
    Line2D([], [], marker="o", markerfacecolor="white", color=navy, ls="", label="Other stop")],
    loc="upper center", bbox_to_anchor=(.5, -.20), ncol=3, frameon=False, fontsize=9,
    handlelength=1.35, columnspacing=1.45)

matrix = np.zeros((len(coords), len(coords)), dtype=int)
for pair, count in case["minibus_by_od"].items():
    origin, destination = map(int, pair.split("-"))
    matrix[origin - 1, destination - 1] = count
colors = ["#f2f4f4", "#d8ece8", "#aed6d0", "#7cbab4", "#479c99", "#197e80", "#0b616b", "#144452"]
maximum = int(matrix.max())
cmap = LinearSegmentedColormap.from_list("vehicles", colors, N=maximum + 1)
norm = BoundaryNorm(np.arange(-.5, maximum + 1.5), cmap.N)
im = flows.imshow(matrix, cmap=cmap, norm=norm, interpolation="nearest")
flows.set_xticks(np.arange(len(coords)), np.arange(1, len(coords) + 1))
flows.set_yticks(np.arange(len(coords)), np.arange(1, len(coords) + 1))
flows.tick_params(length=0, labelsize=8)
flows.set(xlabel="Destination stop", ylabel="Origin stop")
flows.set_title("Direct minibus allocation", color=navy, loc="left", fontsize=15, pad=13, weight="bold")
flows.spines[:].set_visible(False)
bar = fig.colorbar(im, ax=flows, ticks=np.arange(maximum + 1), fraction=.044, pad=.045)
bar.ax.tick_params(labelsize=8, length=0)
bar.outline.set_visible(False)
bar.set_label("Vehicles per pair", fontsize=9)
fig.savefig(ROOT / "docs/case-overview.png", dpi=160, facecolor="white", bbox_inches="tight", pad_inches=.2)
