# dwell_heatmap_with_single_start.py
import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========
# CONFIG
# ==========
CSV_GLOB = "exports/*.csv"        # folder or list of paths
MODEL_NAME = "Set_11_elong_glossy_3.glb"
MAX_STEPS = 90
AZ_BIN_DEG = 15                   # azimuth bins (−180..180)
EL_BIN_DEG = 15                   # elevation bins (−90..90)
USE_DURATION_WEIGHTS = False      # weight by duration_ms if available
OUTFILE = "figs/dwell_map_with_single_start.png"

# ==========
# HELPERS
# ==========
def wrap180(a):
    """Map degrees to (−180, 180]."""
    return ((a + 180) % 360) - 180

def to_elev_90(p):
    """Map pitch 0..360 → (−90..90]."""
    q = wrap180(p)                     # now −180..180
    q = np.where(q > 90,  180 - q, q)  # fold  90..180  down to 90..0
    q = np.where(q < -90, -180 - q, q) # fold −90..−180 up   to −90..0
    return q

def bin_mode_and_center(vals, edges):
    """
    Digitize `vals` into `edges`; return (center_of_modal_bin, modal_index, count_in_modal_bin).
    """
    idx = np.digitize(vals, edges) - 1
    idx = np.clip(idx, 0, len(edges) - 2)  # keep in range
    if idx.size == 0:
        return None, None, 0
    mode_idx = np.bincount(idx).argmax()
    center = 0.5 * (edges[mode_idx] + edges[mode_idx + 1])
    count = int((idx == mode_idx).sum())
    return center, mode_idx, count

# ==========
# LOAD
# ==========
paths = glob.glob(CSV_GLOB) if isinstance(CSV_GLOB, str) else CSV_GLOB
if not paths:
    raise SystemExit("No CSV files found. Update CSV_GLOB to your folder or list of files.")

rows = []
start_az_list, start_el_list = [], []   # raw starts per participant (wrapped)

for p in paths:
    try:
        df = pd.read_csv(p)
    except Exception as e:
        print(f"[WARN] Failed to read {p}: {e}")
        continue

    # keep this object, drop init row
    if "model" not in df.columns or "actionId" not in df.columns:
        continue
    sub = df[(df["model"] == MODEL_NAME) & (df["actionId"] != -1)].copy()
    if sub.empty:
        continue

    # Ensure order by time if available
    if "t_start_ms" in sub.columns:
        sub = sub.sort_values("t_start_ms")

    # Cap to first MAX_STEPS actions
    sub = sub.head(MAX_STEPS)

    # Collect angles + optional weights
    yaw_after  = pd.to_numeric(sub.get("after_yaw"),  errors="coerce").to_numpy()
    pitch_after = pd.to_numeric(sub.get("after_pitch"), errors="coerce").to_numpy()

    if USE_DURATION_WEIGHTS and "duration_ms" in sub.columns:
        w = pd.to_numeric(sub["duration_ms"], errors="coerce").fillna(0).to_numpy()
    else:
        w = np.ones_like(yaw_after, dtype=float)

    # Drop NaNs
    m = np.isfinite(yaw_after) & np.isfinite(pitch_after) & np.isfinite(w)
    yaw_after, pitch_after, w = yaw_after[m], pitch_after[m], w[m]
    if yaw_after.size == 0:
        continue

    # ---- collect a participant's START from BEFORE_* if available; else first AFTER_* ----
    if {"before_yaw", "before_pitch"}.issubset(sub.columns):
        yaw_before  = pd.to_numeric(sub.get("before_yaw"),  errors="coerce").to_numpy()
        pitch_before = pd.to_numeric(sub.get("before_pitch"), errors="coerce").to_numpy()
        m0 = np.isfinite(yaw_before) & np.isfinite(pitch_before)
        if np.any(m0):
            start_az_list.append(wrap180(yaw_before[m0][0]))
            start_el_list.append(to_elev_90(pitch_before[m0][0]))
        else:
            start_az_list.append(wrap180(yaw_after[0]))
            start_el_list.append(to_elev_90(pitch_after[0]))
    else:
        start_az_list.append(wrap180(yaw_after[0]))
        start_el_list.append(to_elev_90(pitch_after[0]))

    # store full sequences (we'll wrap below for the histogram)
    rows.append((yaw_after, pitch_after, w))

if not rows:
    raise SystemExit(f"No usable rows for MODEL='{MODEL_NAME}' in provided CSVs.")

# ==========
# ANGLE NORMALIZATION for histogram (paper-like ranges)
# ==========
all_az, all_el, all_w = [], [], []
for yaw, pitch, w in rows:
    all_az.append(wrap180(yaw))
    all_el.append(to_elev_90(pitch))
    all_w.append(w)

az = np.concatenate(all_az)
el = np.concatenate(all_el)
weights = np.concatenate(all_w)

# ==========
# BINNING → dwell proportion per bin
# ==========
az_edges = np.arange(-180, 180 + AZ_BIN_DEG, AZ_BIN_DEG)  # −180, −165, ..., 180
el_edges = np.arange( -90,  90 + EL_BIN_DEG, EL_BIN_DEG)  #  −90,  −75, ...,  90

H, az_edges, el_edges = np.histogram2d(az, el, bins=[az_edges, el_edges], weights=weights)

total = H.sum()
if total > 0:
    H = H / total

# Transpose for imshow (rows = elevation, cols = azimuth)
H = H.T

# ==========
# Compute ONE canonical start: modal azimuth bin + modal elevation bin
# ==========
one_star = None
n_in_mode = 0
if len(start_az_list) > 0:
    start_az_arr = np.array(start_az_list)
    start_el_arr = np.array(start_el_list)
    az_center, az_mode_idx, n_az = bin_mode_and_center(start_az_arr, az_edges)
    el_center, el_mode_idx, n_el = bin_mode_and_center(start_el_arr, el_edges)
    if az_center is not None and el_center is not None:
        one_star = (az_center, el_center)
        n_in_mode = min(n_az, n_el)  # conservative count overlapping in both modal bins

# ==========
# PLOT heatmap + contours + SINGLE start star
# ==========
plt.figure(figsize=(8.6, 5.2))
extent = [az_edges[0], az_edges[-1], el_edges[0], el_edges[-1]]

# Heatmap (white = higher dwell; paper-like)
plt.imshow(
    H, origin="lower", extent=extent, aspect="auto",
    cmap="Greys", interpolation="bilinear"
)

# Contours using bin centers
if np.any(H > 0):
    az_centers = 0.5 * (az_edges[:-1] + az_edges[1:])
    el_centers = 0.5 * (el_edges[:-1] + el_edges[1:])
    AZ, EL = np.meshgrid(az_centers, el_centers)
    pos = H[H > 0]
    levels = np.quantile(pos, [0.50, 0.70, 0.85, 0.93])
    plt.contour(AZ, EL, H, levels=levels, colors="k", linewidths=0.8)

# Single START marker at the modal cell center
if one_star is not None:
    label = f"Start (n={n_in_mode})" if n_in_mode > 0 else "Start"
    plt.scatter(
        [one_star[0]], [one_star[1]],
        marker="*", s=200, facecolors="none", edgecolors="black",
        linewidths=1.8, zorder=5, label=label
    )
    plt.legend(frameon=False, loc="upper left")

plt.colorbar(label="Dwell proportion")
plt.xlabel("Azimuth (°)")
plt.ylabel("Elevation (°)")
plt.title(f"Dwell-step map • {MODEL_NAME}")
plt.tight_layout()

os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
plt.savefig(OUTFILE, dpi=240, bbox_inches="tight")
plt.show()
