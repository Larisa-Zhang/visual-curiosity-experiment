# plot_world_axis_paths_fixed.py
# Recreate WorldAxisCoord (if needed) and plot rectilinear 2D paths for ONE object.
# WorldAxisCoord_X_deg: cumulative rotation about world X (Up/Down), ±5° per press
# WorldAxisCoord_Y_deg: cumulative rotation about world Y (Left/Right), ±5° per press

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# CONFIG — EDIT THESE
# =========================
CSV_GLOB   = "exports/record_VCURIOSITY_*_with_worldaxiscoord.csv"   # your 32 files
MODEL      = "Set_11_elong_glossy_3.glb"         # object to plot
MAX_STEPS  = 90                                   # per participant cap
OUT_PNG    = "figs/world_axis_paths.png"          # output figure path
# =========================

def ensure_world_axis_coords(df: pd.DataFrame) -> pd.DataFrame:
    """
    If WorldAxisCoord_X/Y exist -> coerce numeric and return.
    Else reconstruct from actionId per (sessionId, model), applying ±5° steps in time order.
    """
    need = {"WorldAxisCoord_X_deg", "WorldAxisCoord_Y_deg"}
    if need.issubset(df.columns):
        df = df.copy()
        df["WorldAxisCoord_X_deg"] = pd.to_numeric(df["WorldAxisCoord_X_deg"], errors="coerce").fillna(0.0)
        df["WorldAxisCoord_Y_deg"] = pd.to_numeric(df["WorldAxisCoord_Y_deg"], errors="coerce").fillna(0.0)
        return df

    df = df.copy()
    for col in ["t_start_ms", "actionId"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["WorldAxisCoord_X_deg"] = 0.0
    df["WorldAxisCoord_Y_deg"] = 0.0

    if not {"sessionId","model","actionId"}.issubset(df.columns):
        # not enough info; return zeros
        return df

    rows = []
    for (_, _), g in df.groupby(["sessionId","model"], sort=False):
        g = g.sort_values("t_start_ms") if "t_start_ms" in g.columns else g.copy()
        x_deg, y_deg = 0.0, 0.0
        for _, r in g.iterrows():
            aid = r.get("actionId", np.nan)
            if not (pd.isna(aid) or int(aid) == -1):
                aid = int(aid)
                if   aid == 0: x_deg -= 5.0   # Up    -> world X −5
                elif aid == 1: x_deg += 5.0   # Down  -> world X +5
                elif aid == 2: y_deg -= 5.0   # Left  -> world Y −5
                elif aid == 3: y_deg += 5.0   # Right -> world Y +5
            r["WorldAxisCoord_X_deg"] = x_deg
            r["WorldAxisCoord_Y_deg"] = y_deg
            rows.append(r)
    return pd.DataFrame(rows, columns=df.columns)

def load_series(csv_glob: str, model: str, max_steps: int):
    """
    Returns list of (sessionId, ThetaY[], ThetaX[]) for the given MODEL.
    """
    paths = sorted(glob.glob(csv_glob))
    series = []
    for p in paths:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "model" not in df.columns or "actionId" not in df.columns:
            continue

        sub = df[(df["model"] == model) & (df["actionId"] != -1)].copy()
        if sub.empty:
            continue

        sub = ensure_world_axis_coords(sub)
        if "t_start_ms" in sub.columns:
            sub["t_start_ms"] = pd.to_numeric(sub["t_start_ms"], errors="coerce")
            sub = sub.sort_values("t_start_ms")

        sub = sub.head(max_steps).reset_index(drop=True)

        if "sessionId" not in sub.columns:
            continue
        for sess, g in sub.groupby("sessionId"):
            x = pd.to_numeric(g["WorldAxisCoord_X_deg"], errors="coerce").to_numpy()
            y = pd.to_numeric(g["WorldAxisCoord_Y_deg"], errors="coerce").to_numpy()
            m = np.isfinite(x) & np.isfinite(y)
            x, y = x[m], y[m]
            if x.size == 0:
                continue
            series.append((str(sess), y, x))  # plot ΘY on x-axis, ΘX on y-axis
    return series

def plot_paths(series, model: str, out_png: str):
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    plt.figure(figsize=(7, 7))
    n = 0
    for sess, tY, tX in series:
        # rectilinear polyline
        plt.plot(tY, tX, linewidth=1.2, alpha=0.9)
        # start (*) and end (X)
        plt.scatter([tY[0]], [tX[0]], marker='*', s=150, zorder=3)
        plt.scatter([tY[-1]], [tX[-1]], marker='X', s=80, zorder=3)
        n += 1
    plt.xlabel("WorldAxisCoord Y (deg) — rotations about world Y (Left/Right)")
    plt.ylabel("WorldAxisCoord X (deg) — rotations about world X (Up/Down)")
    plt.title(f"World-axis 2D paths — {model} — {n} participant(s)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=240, bbox_inches="tight")
    plt.close()
    return n

def main():
    series = load_series(CSV_GLOB, MODEL, MAX_STEPS)
    if not series:
        print(f"[WARN] No usable rows for MODEL='{MODEL}' in {CSV_GLOB}")
        return
    n = plot_paths(series, MODEL, OUT_PNG)
    print(f"[OK] Plotted {n} participant path(s) → {OUT_PNG}")

if __name__ == "__main__":
    main()
