# check_worldaxiscoord_vs_afteryawpitch.py
#
# For ONE chosen object (MODEL), across all participants and enriched CSVs:
#   - Take world-axis coordinates: WorldAxisCoord_X_deg, WorldAxisCoord_Y_deg
#   - Ask: whenever these coords are the same, do we always get the same
#          (after_yaw, after_pitch, recovered_after_eulerZ_deg)?
#
# If not, then world-axis coords are not a unique descriptor of view
# even at the level of (after_yaw, after_pitch, recovered roll).

import os
import glob
import numpy as np
import pandas as pd

# =========================
# CONFIG – EDIT THESE
# =========================
CSV_GLOB   = "exports/record_VCURIOSITY_*_with_worldaxiscoord.csv"
MODEL      = "Set_11_elong_glossy_3.glb"   # <--- change to the object you want to test
ANGLE_RND  = 6                             # decimals for rounding
OUT_REPORT = f"figs/worldaxiscoord_vs_afteryawpitch_{MODEL}.txt"
# =========================

# Column names
THETA_X_COL = "WorldAxisCoord_X_deg"
THETA_Y_COL = "WorldAxisCoord_Y_deg"

AFTER_YAW_COL   = "after_yaw"
AFTER_PITCH_COL = "after_pitch"
ROLL_COL        = "recovered_after_eulerZ_deg"   # recovered roll (Euler Z)


def load_all_for_model(csv_glob: str, model: str) -> pd.DataFrame:
    """Load all enriched CSVs and keep only rows for the chosen MODEL."""
    paths = sorted(glob.glob(csv_glob))
    dfs = []
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            df = pd.read_csv(p)
        except Exception as e:
            print(f"[WARN] Could not read {p}: {e}")
            continue
        if "model" not in df.columns:
            continue
        df = df[df["model"] == model].copy()
        if df.empty:
            continue
        df["source_file"] = os.path.basename(p)
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def check_worldaxis_vs_after(df: pd.DataFrame, report_path: str):
    """
    Given a DataFrame with world-axis coords + after_yaw/pitch + recovered Z,
    check whether each (ΘX, ΘY) pair corresponds to exactly one
    (after_yaw, after_pitch, recovered_after_eulerZ_deg) triplet.
    """
    required = {
        THETA_X_COL, THETA_Y_COL,
        AFTER_YAW_COL, AFTER_PITCH_COL, ROLL_COL
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in data: {missing}")

    # Coerce angles to numeric and drop non-finite
    for c in required:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    m = (
        np.isfinite(df[THETA_X_COL]) &
        np.isfinite(df[THETA_Y_COL]) &
        np.isfinite(df[AFTER_YAW_COL]) &
        np.isfinite(df[AFTER_PITCH_COL]) &
        np.isfinite(df[ROLL_COL])
    )
    df = df[m].copy()
    if df.empty:
        print("[WARN] No usable rows after filtering for finite values.")
        return

    # Round to smooth tiny numeric noise
    df["ThetaX_r"] = df[THETA_X_COL].round(ANGLE_RND)
    df["ThetaY_r"] = df[THETA_Y_COL].round(ANGLE_RND)
    df["Yaw_r"]    = df[AFTER_YAW_COL].round(ANGLE_RND)
    df["Pitch_r"]  = df[AFTER_PITCH_COL].round(ANGLE_RND)
    df["Roll_r"]   = df[ROLL_COL].round(ANGLE_RND)

    # Group by world-axis coord and see how many distinct (after_yaw, after_pitch, roll) triplets we get
    collisions = []
    for (ty, tx), g in df.groupby(["ThetaY_r", "ThetaX_r"]):
        uniq_triplets = g[["Yaw_r", "Pitch_r", "Roll_r"]].drop_duplicates()
        if len(uniq_triplets) > 1:
            # same world-axis coord, but multiple (after_yaw, after_pitch, roll) combinations
            sample = g[
                [
                    "sessionId",
                    "source_file",
                    "actionId",
                    THETA_Y_COL,
                    THETA_X_COL,
                    AFTER_YAW_COL,
                    AFTER_PITCH_COL,
                    ROLL_COL,
                ]
            ].head(8)
            collisions.append((ty, tx, len(uniq_triplets), sample))

    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        total_points = df[["ThetaY_r", "ThetaX_r"]].drop_duplicates().shape[0]
        f.write(f"MODEL = {df['model'].iloc[0] if 'model' in df.columns else 'UNKNOWN'}\n")
        f.write(f"Total unique (WorldAxisCoord_Y_deg, WorldAxisCoord_X_deg) points: {total_points}\n")

        if not collisions:
            f.write(
                "No collisions: each world-axis coord (ΘY, ΘX) mapped to a single "
                "(after_yaw, after_pitch, recovered_after_eulerZ_deg) combination in this dataset.\n"
            )
        else:
            f.write(
                f"Found {len(collisions)} collision location(s) where the same world-axis coord (ΘY, ΘX)\n"
                f"mapped to multiple (after_yaw, after_pitch, recovered_after_eulerZ_deg) combinations.\n\n"
            )
            # Show up to 50 collision locations with a few example rows each
            for ty, tx, nuniq, sample in collisions[:50]:
                f.write(
                    f"(ΘY={ty}, ΘX={tx}) -> {nuniq} unique (after_yaw, after_pitch, roll) combinations\n"
                )
                f.write(sample.to_string(index=False))
                f.write("\n---\n")

    print(f"[OK] Wrote world-axis vs after_yaw/pitch report → {report_path}")


def main():
    df = load_all_for_model(CSV_GLOB, MODEL)
    if df.empty:
        print(f"[WARN] No rows found for MODEL='{MODEL}' in {CSV_GLOB}")
        return
    check_worldaxis_vs_after(df, OUT_REPORT)


if __name__ == "__main__":
    main()
