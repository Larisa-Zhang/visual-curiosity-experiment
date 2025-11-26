import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========
# CONFIG
# ==========
# 1) Where your per-participant CSVs live (change this to your folder)
CSV_GLOB = "exports/*.csv"  
# 2) The object you want to plot
MODEL_NAME = "Set_20_elong_glossy_3.glb"
# 3) Limit each participant to first N steps (your task uses 90)
MAX_STEPS = 90
# 4) Bin sizes (degrees). Paper used +/-15° windows; we’ll use 15°-wide bins too.
AZ_BIN_DEG = 15  # azimuth bins (−180..180)
EL_BIN_DEG = 15  # elevation bins (−90..90)
# 5) Use time weights? (if you want to weight by duration_ms instead of count)
USE_DURATION_WEIGHTS = False

# ==========
# LOAD
# ==========
paths = glob.glob(CSV_GLOB) if isinstance(CSV_GLOB, str) else CSV_GLOB
if not paths:
    raise SystemExit("No CSV files found. Update CSV_GLOB to your folder or list of files.")

rows = []
for p in paths:
    df = pd.read_csv(p)
    # keep this object, drop init row
    df = df[(df["model"] == MODEL_NAME) & (df["actionId"] != -1)].copy()
    if df.empty:
        continue
    # Ensure order by time if available
    if "t_start_ms" in df.columns:
        df = df.sort_values("t_start_ms")
    # Cap to first 90 actions
    df = df.head(MAX_STEPS)

    # Collect angles + optional weights
    yaw = pd.to_numeric(df["after_yaw"], errors="coerce").to_numpy()
    pitch = pd.to_numeric(df["after_pitch"], errors="coerce").to_numpy()
    if USE_DURATION_WEIGHTS and "duration_ms" in df.columns:
        w = pd.to_numeric(df["duration_ms"], errors="coerce").fillna(0).to_numpy()
    else:
        w = np.ones_like(yaw, dtype=float)

    # Drop NaNs
    m = np.isfinite(yaw) & np.isfinite(pitch)
    yaw, pitch, w = yaw[m], pitch[m], w[m]

    rows.append((yaw, pitch, w))

if not rows:
    raise SystemExit(f"No rows for {MODEL_NAME} in provided CSVs.")

# ==========
# ANGLE NORMALIZATION (to paper-like ranges)
# Your CSV angles are 0..360; map to:
#   azimuth:  −180..180
#   elevation:  −90..90  (fold 270..360 and 90..180 back)
# ==========
def wrap180(a):
    """Map degrees to (−180, 180]."""
    return ((a + 180) % 360) - 180

def to_elev_90(p):
    """Map pitch 0..360 → (−90..90]."""
    q = wrap180(p)      # now −180..180
    q = np.where(q > 90, 180 - q, q)    # fold 90..180 down to 90..0
    q = np.where(q < -90, -180 - q, q)  # fold −90..−180 up to −90..0
    return q

all_az = []
all_el = []
all_w  = []
for yaw, pitch, w in rows:
    az = wrap180(yaw)
    el = to_elev_90(pitch)
    all_az.append(az)
    all_el.append(el)
    all_w.append(w)

az = np.concatenate(all_az)
el = np.concatenate(all_el)
weights = np.concatenate(all_w)

# ==========
# BINNING → dwell proportion per bin
# ==========
az_edges = np.arange(-180, 180 + AZ_BIN_DEG, AZ_BIN_DEG)  # e.g., −180, −165, ..., 180
el_edges = np.arange(-90,   90 + EL_BIN_DEG, EL_BIN_DEG)  # e.g., −90, −75, ..., 90

# 2D weighted histogram (azimuth = x, elevation = y)
H, az_edges, el_edges = np.histogram2d(
    az, el, bins=[az_edges, el_edges], weights=weights
)

# Normalize to proportions of total dwell (like paper)
total = H.sum()
if total > 0:
    H = H / total

# Transpose for imshow (rows = elevation, cols = azimuth)
H = H.T  # shape: [len(el_bins)-1, len(az_bins)-1]

# ==========
# PLOT heatmap + contours
# ==========
plt.figure(figsize=(8.5, 5.2))

extent = [az_edges[0], az_edges[-1], el_edges[0], el_edges[-1]]
# Grayscale with white = high dwell (like their figure)
plt.imshow(
    H, origin="lower", extent=extent, aspect="auto",
    cmap="Greys", interpolation="bilinear"  # simple smoothing
)

# Add contours at useful levels (e.g., quantiles)
if np.any(H > 0):
    levels = np.quantile(H[H > 0], [0.5, 0.7, 0.85, 0.93])  # tweak if you like
    plt.contour(
        np.linspace(az_edges[0], az_edges[-1], H.shape[1]),
        np.linspace(el_edges[0], el_edges[-1], H.shape[0]),
        H, levels=levels, colors="k", linewidths=0.8
    )

plt.colorbar(label="Dwell proportion")
plt.xlabel("Azimuth (degrees)")
plt.ylabel("Elevation (degrees)")
plt.title(f"Dwell-step map\n{MODEL_NAME}")
plt.tight_layout()
plt.show()
