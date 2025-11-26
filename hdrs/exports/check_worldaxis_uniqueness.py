# check_worldaxis_uniqueness_single_model.py
# Checks if WorldAxisCoord (ΘY, ΘX) uniquely determines orientation
# for ONE chosen model across all participants and all CSVs.

# reads all CSVs that match CSV_GLOB,
# filters to one object (MODEL) before doing any grouping,
# checks collisions only for that object (across all participants and CSVs),
# Assumes everyone starts from the same initial orientation for that model (via initial_quat_from_model).
# If WorldAxisCoord columns are missing, they are reconstructed from actionId.

import os, glob, math
import numpy as np
import pandas as pd

# ========= CONFIG =========
CSV_GLOB  = "exports/record_VCURIOSITY_*.csv"   # all 32 CSVs
MODEL     = "Set_11_elong_glossy_3.glb"         # <--- change this per object
STEP_DEG  = 5.0
ANGLE_RND = 6   # rounding decimals for Euler comparison
OUT_REPORT = f"figs/worldaxis_uniqueness_{MODEL}.txt"
# =========================

# ---- quaternion helpers ----
def quat_mul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([
        aw*bx + ax*bw + ay*bz - az*by,
        aw*by - ax*bz + ay*bw + az*bx,
        aw*bz + ax*by - ay*bx + az*bw,
        aw*bw - ax*bx - ay*by - az*bz
    ], float)

def quat_from_axis_angle(axis, ang):
    ax, ay, az = axis
    n = math.sqrt(ax*ax+ay*ay+az*az) or 1.0
    ax/=n; ay/=n; az/=n
    s = math.sin(ang/2); c = math.cos(ang/2)
    return np.array([ax*s, ay*s, az*s, c], float)

def quat_from_euler_xyz(x, y, z):
    cx, sx = math.cos(x/2), math.sin(x/2)
    cy, sy = math.cos(y/2), math.sin(y/2)
    cz, sz = math.cos(z/2), math.sin(z/2)
    qx = np.array([sx,0,0,cx]); qy=np.array([0,sy,0,cy]); qz=np.array([0,0,sz,cz])
    return quat_mul(quat_mul(qx,qy), qz)

def mat3_from_quat(q):
    x,y,z,w = q
    xx=x*x; yy=y*y; zz=z*z; xy=x*y; xz=x*z; yz=y*z; wx=w*x; wy=w*y; wz=w*z
    return np.array([
        [1-2*(yy+zz), 2*(xy-wz),   2*(xz+wy)],
        [2*(xy+wz),   1-2*(xx+zz), 2*(yz-wx)],
        [2*(xz-wy),   2*(yz+wx),   1-2*(xx+yy)]
    ], float)

def euler_yxz_from_mat3(m):
    sy = -m[2,0]
    if sy < 1.0:
        if sy > -1.0:
            x = math.asin(sy)              # pitch (X)
            y = math.atan2(m[2,1], m[2,2]) # yaw   (Y)
            z = math.atan2(m[1,0], m[0,0]) # roll  (Z)
        else:
            x = -math.pi/2; y = -math.atan2(-m[1,2], m[1,1]); z = 0.0
    else:
        x =  math.pi/2;  y =  math.atan2(-m[1,2], m[1,1]);    z = 0.0
    return y, x, z  # (yaw, pitch, roll) in radians

# ---- deterministic initial orientation (matches your main.js hashing) ----
def hash_js_like(s):
    h = 0
    for ch in s:
        h = ((h*31) + ord(ch)) & 0xFFFFFFFF
    return h

def initial_quat_from_model(name):
    hx = hash_js_like('test'+name)
    hy = hash_js_like('test/' + name)
    rx = math.radians((hx % 72)*5)
    ry = math.radians((hy % 72)*5)
    return quat_from_euler_xyz(rx, ry, 0.0)

AX = np.array([1.0,0.0,0.0]); AY=np.array([0.0,1.0,0.0])
STEP = math.radians(STEP_DEG)

def ensure_world_axis(df):
    if {"WorldAxisCoord_X_deg","WorldAxisCoord_Y_deg"}.issubset(df.columns):
        df["WorldAxisCoord_X_deg"] = pd.to_numeric(df["WorldAxisCoord_X_deg"], errors="coerce").fillna(0.0)
        df["WorldAxisCoord_Y_deg"] = pd.to_numeric(df["WorldAxisCoord_Y_deg"], errors="coerce").fillna(0.0)
        return df

    # reconstruct from actionId
    df = df.copy()
    for c in ["actionId","t_start_ms"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["WorldAxisCoord_X_deg"] = 0.0
    df["WorldAxisCoord_Y_deg"] = 0.0
    if not {"sessionId","model","actionId"}.issubset(df.columns):
        return df

    for (sess, mod), gidx in df.groupby(["sessionId","model"]).groups.items():
        idxs = sorted(list(gidx), key=lambda i: (df.loc[i,"t_start_ms"] if "t_start_ms" in df.columns and pd.notna(df.loc[i,"t_start_ms"]) else -1e30))
        x=y=0.0
        for i in idxs:
            aid = df.at[i,"actionId"]
            if pd.isna(aid) or int(aid)==-1:
                pass
            else:
                aid=int(aid)
                if aid==0: x-=STEP_DEG
                elif aid==1: x+=STEP_DEG
                elif aid==2: y-=STEP_DEG
                elif aid==3: y+=STEP_DEG
            df.at[i,"WorldAxisCoord_X_deg"]=x
            df.at[i,"WorldAxisCoord_Y_deg"]=y
    return df

def replay_quat(df_model):
    # return DataFrame of recovered Euler YXZ (deg) per row by replaying exact key sequence
    eY=[]; eX=[]; eZ=[]
    q = initial_quat_from_model(df_model.iloc[0]["model"])  # same q0 for this MODEL
    for _, r in df_model.iterrows():
        aid = r.get("actionId", np.nan)
        if not (pd.isna(aid) or int(aid)==-1):
            aid=int(aid)
            if aid==0: q = quat_mul(quat_from_axis_angle(AX, -STEP), q)
            elif aid==1: q = quat_mul(quat_from_axis_angle(AX,  STEP), q)
            elif aid==2: q = quat_mul(quat_from_axis_angle(AY, -STEP), q)
            elif aid==3: q = quat_mul(quat_from_axis_angle(AY,  STEP), q)
        y,x,z = euler_yxz_from_mat3(mat3_from_quat(q))
        eY.append(math.degrees(y)); eX.append(math.degrees(x)); eZ.append(math.degrees(z))
    return pd.DataFrame({"EulerY_deg_YXZ":eY,"EulerX_deg_YXZ":eX,"EulerZ_deg_YXZ":eZ}, index=df_model.index)

def main():
    paths = sorted(glob.glob(CSV_GLOB))
    if not paths:
        print(f"[WARN] No files matched {CSV_GLOB}")
        return

    all_rows=[]
    for p in paths:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if not {"sessionId","model","actionId"}.issubset(df.columns):
            continue

        # 🔹 keep only the one MODEL we care about
        df = df[df["model"] == MODEL].copy()
        if df.empty:
            continue

        if "t_start_ms" in df.columns:
            df["t_start_ms"] = pd.to_numeric(df["t_start_ms"], errors="coerce")
        df = df.sort_values(["model","sessionId","t_start_ms"], na_position="first")
        df = ensure_world_axis(df)

        # recover exact Euler by replaying sequence (per participant)
        out_chunks=[]
        for (mod, sess), g in df.groupby(["model","sessionId"]):
            g = g.copy()
            g = g.sort_values("t_start_ms", na_position="first")
            eul = replay_quat(g)
            g = pd.concat([g, eul], axis=1)
            out_chunks.append(g)
        if out_chunks:
            all_rows.append(pd.concat(out_chunks, axis=0, ignore_index=False))

    if not all_rows:
        print(f"[WARN] No usable data for MODEL='{MODEL}'.")
        return

    full = pd.concat(all_rows, axis=0, ignore_index=False)

    # round to reduce floating noise
    full["ΘX_r"]  = full["WorldAxisCoord_X_deg"].round(6)
    full["ΘY_r"]  = full["WorldAxisCoord_Y_deg"].round(6)
    full["EulX_r"]= full["EulerX_deg_YXZ"].round(ANGLE_RND)
    full["EulY_r"]= full["EulerY_deg_YXZ"].round(ANGLE_RND)
    full["EulZ_r"]= full["EulerZ_deg_YXZ"].round(ANGLE_RND)

    collisions=[]
    for (ty, tx), g in full.groupby(["ΘY_r","ΘX_r"]):
        uniq = g[["EulX_r","EulY_r","EulZ_r"]].drop_duplicates()
        if len(uniq) > 1:
            sample = g[["sessionId","actionId","WorldAxisCoord_Y_deg","WorldAxisCoord_X_deg",
                        "EulerY_deg_YXZ","EulerX_deg_YXZ","EulerZ_deg_YXZ"]].head(6)
            collisions.append((ty, tx, len(uniq), sample))

    os.makedirs(os.path.dirname(OUT_REPORT) or ".", exist_ok=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        if not collisions:
            f.write(f"MODEL = {MODEL}\n")
            f.write("No collisions: each (ΘY, ΘX) mapped to a single Euler(YXZ) orientation in this dataset.\n")
        else:
            f.write(f"MODEL = {MODEL}\n")
            f.write(f"Found {len(collisions)} collision location(s) where the same (ΘY,ΘX) mapped to multiple Euler(YXZ) orientations.\n\n")
            for ty, tx, nuniq, sample in collisions[:50]:
                f.write(f"(ΘY={ty}, ΘX={tx}) -> {nuniq} unique orientations\n")
                f.write(sample.to_string(index=False))
                f.write("\n---\n")

    print(f"[OK] Wrote report for MODEL='{MODEL}' → {OUT_REPORT}")
    # Optional: also save the augmented table if you like:
    # full.to_csv(f"exports/all_with_worldaxis_euler_{MODEL}.csv", index=False)

if __name__ == "__main__":
    main()
