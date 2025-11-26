# /analyse/plot_3d_elong_glossy_all.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# --- Inputs ---
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
REQUIRE_SUBSTR = ("_elong_", "_glossy_")  # must contain BOTH

# --- Helpers ---
def wrap180(a):  # 0..360 -> (-180,180]
    return ((a + 180) % 360) - 180

def to_elev90(p):  # 0..360 -> (-90,90]
    q = wrap180(p)
    q = np.where(q > 90, 180 - q, q)
    q = np.where(q < -90, -180 - q, q)
    return q

# --- Find all models that match BOTH substrings across files ---
models = set()
for path in csv_files:
    df_names = pd.read_csv(path, usecols=["model"], dtype=str, on_bad_lines="skip")
    for m in df_names["model"].dropna().unique():
        if all(s in m for s in REQUIRE_SUBSTR):
            models.add(m)

if not models:
    raise SystemExit("No models matched both '_elong_' and '_glossy_' in the provided CSVs.")

# --- One combined 3D plot for ALL matching models & ALL participants ---
fig = plt.figure(figsize=(10.5, 7))
ax = fig.add_subplot(111, projection='3d')

num_lines = 0
for path in csv_files:
    df = pd.read_csv(path, on_bad_lines="skip")

    # Keep only rows for elongated + glossy models and real actions
    mask = df["model"].isin(models) & (df["actionId"] != -1)
    sub_all = df[mask].copy()
    if sub_all.empty:
        continue

    # Split by model so each participant may contribute multiple lines
    for model_name, sub in sub_all.groupby("model"):
        # sort by time if available
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

        # unwrap to avoid discontinuities across ±180°
        yaw_un = np.rad2deg(np.unwrap(np.deg2rad(yaw)))
        pit_un = np.rad2deg(np.unwrap(np.deg2rad(pitch)))
        steps = np.arange(1, yaw_un.size + 1)

        # same color for everything; alpha shows density via overlap
        ax.plot(steps, yaw_un, pit_un, marker='o', linewidth=0.9, alpha=0.007, color='blue')
        num_lines += 1

ax.set_xlabel("Step")
ax.set_ylabel("Yaw (deg, unwrapped)")
ax.set_zlabel("Pitch (deg, unwrapped)")
ax.set_xlim(1, MAX_STEPS)
ax.set_title(f"3D exploration paths • ALL elongated + glossy objects\n"
             f"{len(models)} objects • {num_lines} trajectories (all participants)")
plt.tight_layout()
plt.show()
