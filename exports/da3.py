# /analyse/plot_3d_all_elong_glossy.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- 1) Inputs ---
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
    "exports/record_VCURIOSITY_22.csv"
]
MAX_STEPS = 90
MODEL_SUBSTR = "_elong_glossy_"  # <- filter for elong_glossy only
OUTDIR = "outputs/3d_elong_glossy"

os.makedirs(OUTDIR, exist_ok=True)

# --- 2) Helpers ---
def wrap180(a):  # 0..360 -> (-180,180]
    return ((a + 180) % 360) - 180

def to_elev90(p):  # 0..360 -> (-90,90]
    q = wrap180(p)
    q = np.where(q > 90, 180 - q, q)
    q = np.where(q < -90, -180 - q, q)
    return q

# --- 3) Discover which models (across all CSVs) match the filter ---
models = set()
for path in csv_files:
    df = pd.read_csv(path, usecols=["model"], dtype=str, on_bad_lines="skip")
    models.update(m for m in df["model"].dropna().unique() if MODEL_SUBSTR in m)

target_models = sorted(models)
if not target_models:
    raise SystemExit(f"No models containing '{MODEL_SUBSTR}' found in the CSVs.")

# --- 4) Plot one 3D overlay per model across all participants ---
for model in target_models:
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    plotted = 0
    for path in csv_files:
        df = pd.read_csv(path, on_bad_lines="skip")

        sub = df[(df.get("model") == model) & (df.get("actionId") != -1)].copy()
        if sub.empty:
            continue

        if "t_start_ms" in sub.columns:
            sub = sub.sort_values("t_start_ms")

        sub = sub.head(MAX_STEPS).reset_index(drop=True)

        yaw = pd.to_numeric(sub["after_yaw"], errors="coerce").to_numpy()
        pitch = pd.to_numeric(sub["after_pitch"], errors="coerce").to_numpy()
        m = np.isfinite(yaw) & np.isfinite(pitch)
        if not m.any():
            continue

        yaw = wrap180(yaw[m])
        pitch = to_elev90(pitch[m])

        # unwrap to make the line continuous across ±180°
        yaw_un = np.rad2deg(np.unwrap(np.deg2rad(yaw)))
        pit_un = np.rad2deg(np.unwrap(np.deg2rad(pitch)))
        steps = np.arange(1, yaw_un.size + 1)

        ax.plot(steps, yaw_un, pit_un, marker='o', linewidth=1.0, alpha=0.03, color='blue')
        plotted += 1

    if plotted == 0:
        plt.close(fig)
        continue

    ax.set_xlabel("Step")
    ax.set_ylabel("Yaw (deg, unwrapped)")
    ax.set_zlabel("Pitch (deg, unwrapped)")
    ax.set_title(f"3D exploration trajectories • {model}\n{plotted} participant(s)")
    ax.set_xlim(1, MAX_STEPS)  # keep x consistent
    plt.tight_layout()

    safe_name = model.replace("/", "_").replace("\\", "_")
    out_path = os.path.join(OUTDIR, f"3d_{safe_name}.png")
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

print(f"✅ Saved {len(target_models)} figures to {OUTDIR}")
