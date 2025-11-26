# check_yawpitch_collisions_from_enriched.py
#
# Uses your *enriched* CSVs (…_with_worldaxiscoord.csv) to check:
#   For ONE chosen object (MODEL), across all participants,
#   do any two rows share the same (after_yaw, after_pitch)
#   but have different recovered_after_eulerZ_deg (roll)?
# If YES → yaw + pitch by themselves do not uniquely specify the view.
# If NO → yaw + pitch fully determine the view (in your dataset).
# No key replay needed – we just compare recorded columns.

import os
import glob
import math
import numpy as np
import pandas as pd

# =========================
# CONFIG – EDIT THESE
# =========================
CSV_GLOB   = "exports/record_VCURIOSITY_*_with_eulerZ.csv"
MODEL      = "Set_10_elong_glossy_3.glb"   # <--- change this to the object you want to test
ANGLE_RND  = 3                             # rounding decimals for yaw/pitch/roll
OUT_REPORT = f"figs/yawpitch_collisions_{MODEL}.txt"
# =========================

# Which columns to use as yaw/pitch/roll?
# You already have:
#   after_yaw, after_pitch
#   recovered_after_eulerZ_deg
YAW_COL   = "after_yaw"
PITCH_COL = "after_pitch"
ROLL_COL  = "recovered_after_eulerZ_deg"   # roll from recovered Euler(YXZ)


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


def check_collisions(df: pd.DataFrame, report_path: str):
    """
    Given a DataFrame with after_yaw, after_pitch, recovered_after_eulerZ_deg,
    check for collisions: same (yaw,pitch) but multiple roll values.
    """
    # Coerce to numeric and drop rows with missing angles
    df[YAW_COL]   = pd.to_numeric(df[YAW_COL], errors="coerce")
    df[PITCH_COL] = pd.to_numeric(df[PITCH_COL], errors="coerce")
    df[ROLL_COL]  = pd.to_numeric(df[ROLL_COL], errors="coerce")

    m = np.isfinite(df[YAW_COL]) & np.isfinite(df[PITCH_COL]) & np.isfinite(df[ROLL_COL])
    df = df[m].copy()
    if df.empty:
        print("[WARN] No usable yaw/pitch/roll rows after filtering.")
        return

    # Round to avoid tiny floating differences
    df["Yaw_r"]   = df[YAW_COL].round(ANGLE_RND)
    df["Pitch_r"] = df[PITCH_COL].round(ANGLE_RND)
    df["Roll_r"]  = df[ROLL_COL].round(ANGLE_RND)

    # Group by (yaw,pitch) and check how many distinct roll values we see
    collisions = []
    for (yaw, pitch), g in df.groupby(["Yaw_r", "Pitch_r"]):
        uniq_roll = g["Roll_r"].drop_duplicates()
        if len(uniq_roll) > 1:
            # same yaw,pitch but multiple roll values
            sample = g[
                [
                    "sessionId",
                    "source_file",
                    "actionId",
                    YAW_COL,
                    PITCH_COL,
                    ROLL_COL,
                ]
            ].head(8)
            collisions.append((yaw, pitch, len(uniq_roll), sample))

    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        total_points = df[["Yaw_r", "Pitch_r"]].drop_duplicates().shape[0]

        f.write(f"MODEL = {df['model'].iloc[0] if 'model' in df.columns else 'UNKNOWN'}\n")
        f.write(f"Total unique (yaw,pitch) points: {total_points}\n")

        if not collisions:
            f.write("No collisions: each (yaw, pitch) mapped to a single roll in this dataset.\n")
        else:
            f.write(
                f"Found {len(collisions)} collision location(s) where the same (yaw, pitch) mapped to multiple roll values.\n\n"
            )
            # Show up to 50 collision locations with a few example rows each
            for yaw, pitch, nuniq, sample in collisions[:50]:
                f.write(f"(yaw={yaw}, pitch={pitch}) -> {nuniq} unique roll values\n")
                f.write(sample.to_string(index=False))
                f.write("\n---\n")

    print(f"[OK] Wrote yaw/pitch collision report → {report_path}")


def main():
    df = load_all_for_model(CSV_GLOB, MODEL)
    if df.empty:
        print(f"[WARN] No rows found for MODEL='{MODEL}' in {CSV_GLOB}")
        return
    check_collisions(df, OUT_REPORT)


if __name__ == "__main__":
    main()
