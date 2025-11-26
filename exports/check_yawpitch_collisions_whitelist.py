# check_yawpitch_collisions_whitelist.py
#
# For EACH object in MODEL_WHITELIST, across all participants / files:
#   find (after_yaw, after_pitch) locations that map to multiple
#   recovered_after_eulerZ_deg values.
#
# For each model, writes:
#   figs/yawpitch_collisions_{model-name-clean}.txt

import os
import glob
import numpy as np
import pandas as pd
import re

# =========================
# CONFIG – EDIT THESE
# =========================
CSV_GLOB   = "exports/record_VCURIOSITY_*_with_eulerZ.csv"
ANGLE_RND  = 2     # rounding decimals for yaw/pitch/roll
OUT_DIR    = "figs"

MODEL_WHITELIST = [
  'Set_10_elong_glossy_3.glb',
  'Set_10_elong_matte_2.glb',
  'Set_10_orig_glossy_1.glb',
  'Set_10_orig_matte_0.glb',
  'Set_11_elong_glossy_3.glb',
  'Set_11_elong_matte_2.glb',
  'Set_11_orig_glossy_1.glb',
  'Set_11_orig_matte_0.glb',
  'Set_12_elong_glossy_3.glb',
  'Set_12_elong_matte_2.glb',
  'Set_12_orig_glossy_1.glb',
  'Set_12_orig_matte_0.glb',
  'Set_13_elong_glossy_3.glb',
  'Set_13_elong_matte_2.glb',
  'Set_13_orig_glossy_1.glb',
  'Set_13_orig_matte_0.glb',
  'Set_14_elong_glossy_3.glb',
  'Set_14_elong_matte_2.glb',
  'Set_14_orig_glossy_1.glb',
  'Set_14_orig_matte_0.glb',
  'Set_15_elong_glossy_3.glb',
  'Set_15_elong_matte_2.glb',
  'Set_15_orig_glossy_1.glb',
  'Set_15_orig_matte_0.glb',
  'Set_16_elong_glossy_3.glb',
  'Set_16_elong_matte_2.glb',
  'Set_16_orig_glossy_1.glb',
  'Set_16_orig_matte_0.glb',
  'Set_18_elong_glossy_3.glb',
  'Set_18_elong_matte_2.glb',
  'Set_18_orig_glossy_1.glb',
  'Set_18_orig_matte_0.glb',
  'Set_19_elong_glossy_3.glb',
  'Set_19_elong_matte_2.glb',
  'Set_19_orig_glossy_1.glb',
  'Set_19_orig_matte_0.glb',
  'Set_1_elong_glossy_3.glb',
  'Set_1_elong_matte_2.glb',
  'Set_1_orig_glossy_1.glb',
  'Set_1_orig_matte_0.glb',
  'Set_20_elong_glossy_3.glb',
  'Set_20_elong_matte_2.glb',
  'Set_20_orig_glossy_1.glb',
  'Set_20_orig_matte_0.glb',
  'Set_2_elong_glossy_3.glb',
  'Set_2_elong_matte_2.glb',
  'Set_2_orig_glossy_1.glb',
  'Set_2_orig_matte_0.glb',
  'Set_3_elong_glossy_3.glb',
  'Set_3_elong_matte_2.glb',
  'Set_3_orig_glossy_1.glb',
  'Set_3_orig_matte_0.glb',
  'Set_4_elong_glossy_3.glb',
  'Set_4_elong_matte_2.glb',
  'Set_4_orig_glossy_1.glb',
  'Set_4_orig_matte_0.glb',
  'Set_5_elong_glossy_3.glb',
  'Set_5_elong_matte_2.glb',
  'Set_5_orig_glossy_1.glb',
  'Set_5_orig_matte_0.glb',
  'Set_6_elong_glossy_3.glb',
  'Set_6_elong_matte_2.glb',
  'Set_6_orig_glossy_1.glb',
  'Set_6_orig_matte_0.glb',
  'Set_7_elong_glossy_3.glb',
  'Set_7_elong_matte_2.glb',
  'Set_7_orig_glossy_1.glb',
  'Set_7_orig_matte_0.glb',
  'Set_8_elong_glossy_3.glb',
  'Set_8_elong_matte_2.glb',
  'Set_8_orig_glossy_1.glb',
  'Set_8_orig_matte_0.glb',
  'Set_9_elong_glossy_3.glb',
  'Set_9_elong_matte_2.glb',
  'Set_9_orig_glossy_1.glb',
  'Set_9_orig_matte_0.glb',
]
# =========================

YAW_COL   = "after_yaw"
PITCH_COL = "after_pitch"
ROLL_COL  = "recovered_after_eulerZ_deg"


def sanitise_model_name(model: str) -> str:
    """Make a model name safe to use in filenames."""
    return re.sub(r'[^A-Za-z0-9_-]+', '_', model)


def load_all(csv_glob: str) -> pd.DataFrame:
    """Load all CSVs and return a combined DataFrame with source_file column."""
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
            print(f"[WARN] File {p} has no 'model' column; skipping.")
            continue

        df["source_file"] = os.path.basename(p)
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def check_collisions_for_model(df: pd.DataFrame, model: str, angle_rnd: int, out_dir: str):
    """Given DF already filtered to one model, check for yaw–pitch–Z collisions."""
    # Coerce to numeric and drop rows with missing angles
    df[YAW_COL]   = pd.to_numeric(df[YAW_COL], errors="coerce")
    df[PITCH_COL] = pd.to_numeric(df[PITCH_COL], errors="coerce")
    df[ROLL_COL]  = pd.to_numeric(df[ROLL_COL], errors="coerce")

    m = np.isfinite(df[YAW_COL]) & np.isfinite(df[PITCH_COL]) & np.isfinite(df[ROLL_COL])
    df = df[m].copy()
    if df.empty:
        print(f"[WARN] No usable yaw/pitch/roll rows for model '{model}' after filtering.")
        return

    # Round to avoid tiny floating differences
    df["Yaw_r"]   = df[YAW_COL].round(angle_rnd)
    df["Pitch_r"] = df[PITCH_COL].round(angle_rnd)
    df["Roll_r"]  = df[ROLL_COL].round(angle_rnd)

    collisions = []
    for (yaw, pitch), g in df.groupby(["Yaw_r", "Pitch_r"]):
        uniq_roll = g["Roll_r"].drop_duplicates()
        if len(uniq_roll) > 1:
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

    os.makedirs(out_dir, exist_ok=True)
    safe_model = sanitise_model_name(model)
    report_path = os.path.join(out_dir, f"yawpitch_collisions_{safe_model}.txt")

    total_points = df[["Yaw_r", "Pitch_r"]].drop_duplicates().shape[0]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"MODEL = {model}\n")
        f.write(f"Total unique (yaw,pitch) points: {total_points}\n")

        if not collisions:
            f.write("No collisions: each (yaw, pitch) mapped to a single roll in this dataset.\n")
        else:
            f.write(
                f"Found {len(collisions)} collision location(s) where the same (yaw, pitch) mapped to multiple roll values.\n\n"
            )
            for yaw, pitch, nuniq, sample in collisions[:50]:
                f.write(f"(yaw={yaw}, pitch={pitch}) -> {nuniq} unique roll values\n")
                f.write(sample.to_string(index=False))
                f.write("\n---\n")

    print(f"[OK] Wrote yaw/pitch collision report for {model} → {report_path}")


def main():
    df_all = load_all(CSV_GLOB)
    if df_all.empty:
        print(f"[WARN] No rows found in any files matching {CSV_GLOB}")
        return

    print(f"Loaded {len(df_all)} total rows.")

    for model in MODEL_WHITELIST:
        df_model = df_all[df_all["model"] == model].copy()
        if df_model.empty:
            print(f"[WARN] No rows found for model '{model}' – skipping.")
            continue

        print(f"\n=== Checking model: {model} (rows: {len(df_model)}) ===")
        check_collisions_for_model(df_model, model, ANGLE_RND, OUT_DIR)


if __name__ == "__main__":
    main()
