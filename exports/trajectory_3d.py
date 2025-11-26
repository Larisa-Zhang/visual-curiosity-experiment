# /analyse/plot_3d_trajectory.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

csv_files = [
    "exports/record_VCURIOSITY_1.csv",
    "exports/record_VCURIOSITY_2.csv",
    # ... keep the rest ...
    "exports/record_VCURIOSITY_32.csv",
]
MODEL = "Set_11_elong_glossy_3.glb"
MAX_STEPS = 90  # cap per your task

def wrap180(a):
    return ((a + 180) % 360) - 180

def to_elev90(p):
    q = wrap180(p)
    q = np.where(q > 90, 180 - q, q)
    q = np.where(q < -90, -180 - q, q)
    return q

fig = plt.figure(figsize=(9, 6))
ax = fig.add_subplot(111, projection='3d')

plotted = 0
for path in csv_files:
    df = pd.read_csv(path)

    sub = df[(df["model"] == MODEL) & (df["actionId"] != -1)].copy()
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

    # unwrap to avoid ±180° jumps
    yaw_un = np.rad2deg(np.unwrap(np.deg2rad(yaw)))
    pit_un = np.rad2deg(np.unwrap(np.deg2rad(pitch)))
    steps = np.arange(1, yaw_un.size + 1)

    # same color for all; transparency shows overlap
    ax.plot(steps, yaw_un, pit_un, marker='o', linewidth=1.0, alpha=0.3, color='blue')
    plotted += 1

ax.set_xlabel("Step")
ax.set_ylabel("Yaw (deg, unwrapped)")
ax.set_zlabel("Pitch (deg, unwrapped)")
ax.set_title(f"3D exploration trajectories • {MODEL}\n{plotted} participant(s)")
plt.tight_layout()
plt.show()