# plot_2d_facets.py
# -----------------
# Builds three 2D subplots (facets) from the same data:
# (1) Step vs Yaw, (2) Step vs Pitch, (3) Yaw vs Pitch (colored by step, with start/end).

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
from matplotlib.colors import BoundaryNorm, Normalize
from matplotlib.cm import ScalarMappable

# ===== user settings =====
csv_files = [
    "exports/record_VCURIOSITY_1.csv",
    "exports/record_VCURIOSITY_2.csv",
    "exports/record_VCURIOSITY_3.csv",
    "exports/record_VCURIOSITY_4.csv",
    "exports/record_VCURIOSITY_5.csv",
    "exports/record_VCURIOSITY_6.csv",
    "exports/record_VCURIOSITY_7.csv",
    "exports/record_VCURIOSITY_8.csv",
    "exports/record_VCURIOSITY_9.csv",
    "exports/record_VCURIOSITY_10.csv",
    "exports/record_VCURIOSITY_11.csv",
    "exports/record_VCURIOSITY_12.csv",
    "exports/record_VCURIOSITY_13.csv",
    "exports/record_VCURIOSITY_14.csv",
    "exports/record_VCURIOSITY_15.csv",
    "exports/record_VCURIOSITY_16.csv",
    "exports/record_VCURIOSITY_17.csv",
    "exports/record_VCURIOSITY_18.csv",
    "exports/record_VCURIOSITY_19.csv",
    "exports/record_VCURIOSITY_20.csv",
    "exports/record_VCURIOSITY_21.csv",
    "exports/record_VCURIOSITY_22.csv",
    "exports/record_VCURIOSITY_23.csv",
    "exports/record_VCURIOSITY_24.csv",
    "exports/record_VCURIOSITY_25.csv",
    "exports/record_VCURIOSITY_26.csv",
    "exports/record_VCURIOSITY_27.csv",
    "exports/record_VCURIOSITY_28.csv",
    "exports/record_VCURIOSITY_29.csv",
    "exports/record_VCURIOSITY_30.csv",
    "exports/record_VCURIOSITY_31.csv",
    "exports/record_VCURIOSITY_32.csv",
]
MODEL = "Set_11_elong_glossy_3.glb"
MAX_STEPS = 90
OUTDIR = "figs"
os.makedirs(OUTDIR, exist_ok=True)

# ===== helpers =====
def wrap180(a):
    return ((a + 180) % 360) - 180

def to_elev90(p):
    q = wrap180(p)
    q = np.where(q > 90, 180 - q, q)
    q = np.where(q < -90, -180 - q, q)
    return q

# ===== collect all series =====
all_steps, all_yaw, all_pitch = [], [], []
plotted = 0

for path in csv_files:
    if not os.path.exists(path):
        continue

    df = pd.read_csv(path)
    sub = df[(df.get("model") == MODEL) & (df.get("actionId") != -1)].copy()
    if sub.empty:
        continue

    if "t_start_ms" in sub.columns:
        sub = sub.sort_values("t_start_ms")

    sub = sub.head(MAX_STEPS).reset_index(drop=True)

    yaw = pd.to_numeric(sub["after_yaw"], errors="coerce").to_numpy()
    pitch = pd.to_numeric(sub["after_pitch"], errors="coerce").to_numpy()
    m = np.isfinite(yaw) & np.isfinite(pitch)
    yaw, pitch = yaw[m], pitch[m]
    if yaw.size == 0:
        continue

    yaw = wrap180(yaw)
    pitch = to_elev90(pitch)

    # unwrap to make the path continuous
    yaw_un = np.rad2deg(np.unwrap(np.deg2rad(yaw)))
    pit_un = np.rad2deg(np.unwrap(np.deg2rad(pitch)))
    steps = np.arange(1, yaw_un.size + 1)

    all_steps.append(steps)
    all_yaw.append(yaw_un)
    all_pitch.append(pit_un)
    plotted += 1

# ===== early exit / safe no-data handling =====
if plotted == 0:
    print(f"[WARN] No usable rows for MODEL='{MODEL}' in provided CSVs.")
    # still produce an empty figure with titles so batch runs don't crash
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.2), sharex=False)
    for ax, t in zip(axs, ["Step vs Yaw", "Step vs Pitch", "Yaw vs Pitch (colored by step)"]):
        ax.set_title(t); ax.grid(True, alpha=0.25)
    fig.suptitle(f"Exploration Projections • {MODEL} • 0 participant(s)", y=1.05)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, "traj_facets_2d.png"), dpi=240, bbox_inches="tight")
    plt.close(fig)
    raise SystemExit(0)

# ===== make facets =====
fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.2), sharex=False)
titles = ["Step vs Yaw", "Step vs Pitch", "Yaw vs Pitch (colored by step)"]

# 1) Step–Yaw
for s, y in zip(all_steps, all_yaw):
    axs[0].plot(s, y, alpha=0.35, linewidth=1.0, color="blue")
axs[0].set_xlabel("Step")
axs[0].set_ylabel("Yaw (deg, unwrapped)")
axs[0].grid(True, alpha=0.25)

# 2) Step–Pitch
for s, p in zip(all_steps, all_pitch):
    axs[1].plot(s, p, alpha=0.35, linewidth=1.0, color="blue")
axs[1].set_xlabel("Step")
axs[1].set_ylabel("Pitch (deg, unwrapped)")
axs[1].grid(True, alpha=0.25)

# 3) Yaw–Pitch with step colouring + start/end markers + arrows
axs[2].set_title("Yaw vs Pitch (colored by step)")
cmap = get_cmap("viridis")

# Arrows to indicate direction every N points
N = 6
for y, p in zip(all_yaw, all_pitch):
    if len(y) < 2:
        continue
    dy = np.diff(y); dp = np.diff(p)
    idx = np.arange(0, len(dy), N)
    if idx.size:
        axs[2].quiver(y[idx], p[idx], dy[idx], dp[idx], angles='xy', scale_units='xy',
                      scale=1, width=0.002, alpha=0.6, color='gray')

# Discrete step coloring (so the bar ticks line up with steps)
bounds = np.arange(1, MAX_STEPS + 2)          # 1..MAX_STEPS+1
norm = BoundaryNorm(bounds, ncolors=256)

last_scatter = None
for y, p, s in zip(all_yaw, all_pitch, all_steps):
    if len(y) == 0:
        continue

    # light path for shape
    axs[2].plot(y, p, color="lightgray", alpha=0.5, linewidth=0.9, zorder=1)

    # points colored by step index
    last_scatter = axs[2].scatter(
        y, p,
        c=s,
        s=12,
        cmap=cmap,
        norm=norm,
        alpha=0.9, linewidths=0, zorder=2
    )

    # START marker (big hollow star)
    axs[2].scatter(
        y[0], p[0],
        marker="*",
        s=160,
        facecolor="none",
        edgecolor="black",
        linewidths=1.6,
        zorder=3
    )

    # END marker (big 'X')
    axs[2].scatter(
        y[-1], p[-1],
        marker="X",
        s=90,
        facecolor="black",
        edgecolor="white",
        linewidths=0.8,
        zorder=3
    )

axs[2].set_xlabel("Yaw (deg, unwrapped)")
axs[2].set_ylabel("Pitch (deg, unwrapped)")
axs[2].grid(True, alpha=0.25)

# Legend (proxy handles)
legend_elems = [
    Line2D([0], [0], marker="*", markersize=12, markerfacecolor="none",
           markeredgecolor="black", linewidth=0, label="Start"),
    Line2D([0], [0], marker="X", markersize=9, markerfacecolor="black",
           markeredgecolor="white", linewidth=0, label="End"),
]
axs[2].legend(handles=legend_elems, loc="best", frameon=False)

# Colorbar (robust if we somehow didn't scatter)
if last_scatter is None:
    # fallback dummy mappable to avoid NameError
    mappable = ScalarMappable(norm=Normalize(1, MAX_STEPS), cmap=cmap)
else:
    mappable = last_scatter

cbar = fig.colorbar(mappable, ax=axs[2], pad=0.02)
cbar.set_label("Step")
cbar.set_ticks(np.arange(10, MAX_STEPS + 1, 10))  # tick every 10 steps

# Titles
for ax, t in zip(axs, titles):
    ax.set_title(t)

fig.suptitle(f"Exploration Projections • {MODEL} • {plotted} participant(s)", y=1.05)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "traj_facets_2d.png"), dpi=240, bbox_inches="tight")
plt.show()
