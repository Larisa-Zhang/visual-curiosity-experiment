// recover_eulerZ_from_actions.js
// Reconstruct Euler Z (roll, order YXZ) by replaying action history in world space.
//Logic:
// Start from the same deterministic initial orientation as in main.js (via initialQuatFromModel(model)).
// Sort rows by t_start_ms within each (sessionId, model).
// For each row, use actionId to apply a 5° rotation in world space:
// Up → rotate −5° around world X
// Down → rotate +5° around world X
// Left → rotate −5° around world Y
// Right → rotate +5° around world Y
// Accumulate these as quaternions: q = qAxis * q (world-space rotation).
// At each step, convert q → rotation matrix → Euler(Y,X,Z) and read off Z = roll.
// So it’s literally:
// “Rebuild the same quaternion the object had after each action, then ask: what is the Euler Z if we decompose that quaternion in Y-X-Z order?”
// If:
// initialQuatFromModel truly matches what main.js did, and
// each action really was a perfect ±5° world-space rotation,
// then this is as close as you can get to the real roll that existed in Three.js at the time. Any error is just floating-point / minor implementation details.
// 👉 Verdict: This is the most faithful reconstruction of Euler Z.
// Usage examples:
//   node recover_eulerZ_from_actions.js path/to/record_VCURIOSITY_1.csv
//   node recover_eulerZ_from_actions.js path/to/record_VCURIOSITY_*.csv       (bash/zsh glob)
//   node recover_eulerZ_from_actions.js --dir ./exports --pattern "record_VCURIOSITY_*.csv"
//   node recover_eulerZ_from_actions.js --dir ./exports --pattern "record_VCURIOSITY_*.csv" --inplace

import fs from 'node:fs';
import path from 'node:path';

// ---------------------- CSV helpers (simple) ----------------------
function parseCSV(text) {
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    .split('\n')
    .filter(Boolean);
  const header = lines[0].split(',');
  const rows = lines.slice(1).map((line, i) => {
    const cells = line.split(',');
    const r = {};
    header.forEach((h, idx) => {
      r[h] = (cells[idx] ?? '');
    });
    r.__line = i + 2; // for debugging if needed
    return r;
  });
  return { header, rows };
}

function toCSV(header, rows) {
  const out = [header.join(',')];
  for (const r of rows) {
    out.push(header.map(h => (r[h] ?? '')).join(','));
  }
  return out.join('\n') + '\n';
}

// ---------------------- Math utils: quats + Euler YXZ ----------------------
function d2r(d) { return d * Math.PI / 180; }
function r2d(r) { return r * 180 / Math.PI; }

// quaternion multiplication: a * b
function quatMul(a, b) {
  const [ax, ay, az, aw] = a;
  const [bx, by, bz, bw] = b;
  return [
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
    aw * bw - ax * bx - ay * by - az * bz,
  ];
}

// axis-angle → quaternion
function quatFromAxisAngle(ax, ay, az, ang) {
  const n = Math.hypot(ax, ay, az) || 1;
  ax /= n; ay /= n; az /= n;
  const s = Math.sin(ang / 2), c = Math.cos(ang / 2);
  return [ax * s, ay * s, az * s, c];
}

// Euler XYZ → quaternion (matches three.js .set(x,y,z) in 'XYZ')
function quatFromEulerXYZ(x, y, z) {
  const cx = Math.cos(x / 2), sx = Math.sin(x / 2);
  const cy = Math.cos(y / 2), sy = Math.sin(y / 2);
  const cz = Math.cos(z / 2), sz = Math.sin(z / 2);
  const qx = [sx, 0, 0, cx];
  const qy = [0, sy, 0, cy];
  const qz = [0, 0, sz, cz];
  return quatMul(quatMul(qx, qy), qz); // qx*qy*qz
}

function mat3FromQuat(q) {
  const [x, y, z, w] = q;
  const xx = x * x, yy = y * y, zz = z * z;
  const xy = x * y, xz = x * z, yz = y * z;
  const wx = w * x, wy = w * y, wz = w * z;
  return [
    1 - 2 * (yy + zz), 2 * (xy - wz),       2 * (xz + wy),
    2 * (xy + wz),     1 - 2 * (xx + zz),   2 * (yz - wx),
    2 * (xz - wy),     2 * (yz + wx),       1 - 2 * (xx + yy),
  ];
}

// Euler.fromRotationMatrix with order 'YXZ'
// Returns { yaw (Y), pitch (X), roll (Z) } in radians
function eulerYXZFromMat3(m) {
  // m is flat row-major: [m00,m01,m02, m10,m11,m12, m20,m21,m22]
  const sy = -m[6]; // -m20
  let x, y, z;
  if (sy < 1) {
    if (sy > -1) {
      x = Math.asin(sy);          // pitch X
      y = Math.atan2(m[7], m[8]); // atan2(m21, m22) yaw Y
      z = Math.atan2(m[3], m[0]); // atan2(m10, m00) roll Z
    } else {
      // sy <= -1 : gimbal lock
      x = -Math.PI / 2;
      y = -Math.atan2(-m[5], m[4]);
      z = 0;
    }
  } else {
    // sy >= 1 : gimbal lock
    x =  Math.PI / 2;
    y =  Math.atan2(-m[5], m[4]);
    z = 0;
  }
  return { yaw: y, pitch: x, roll: z };
}

// ---------------------- Deterministic initial orientation ----------------------
// Must match your main.js logic for model initial rotations.
function hashStringJS(s) {
  let h = 0 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h * 31) + s.charCodeAt(i)) >>> 0;
  }
  return h >>> 0;
}

function initialQuatFromModel(modelName) {
  const hx = hashStringJS('test' + modelName);
  const hy = hashStringJS('test/' + modelName);
  const rotationsX = (hx % 72) * 5; // 0..355 in 5° steps
  const rotationsY = (hy % 72) * 5;
  return quatFromEulerXYZ(d2r(rotationsX), d2r(rotationsY), 0);
}

// ---------------------- Core: replay actions to recover Euler Z ----------------------
function addRecoveredEulerZ(rows) {
  // We need these columns to exist
  for (const k of ['sessionId', 'model', 'actionId', 't_start_ms']) {
    if (!(k in rows[0])) {
      throw new Error(`Missing required column: ${k}`);
    }
  }

  // Coerce numeric fields
  for (const r of rows) {
    r.actionId   = (r.actionId === '' ? null : Number(r.actionId));
    r.t_start_ms = (r.t_start_ms === '' ? NaN   : Number(r.t_start_ms));
  }

  // Ensure target column exists in each row
  for (const r of rows) {
    if (!('recovered_after_eulerZ_deg' in r)) {
      r.recovered_after_eulerZ_deg = '';
    }
  }

  // Group by (sessionId, model)
  const groups = new Map();
  for (const r of rows) {
    const key = `${r.sessionId}||${r.model}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }

  const STEP = d2r(5);      // 5° step in radians
  const AX   = [1, 0, 0];   // world X axis (up/down)
  const AY   = [0, 1, 0];   // world Y axis (left/right)

  for (const gRows of groups.values()) {
    // Sort by time so we replay actions in the correct order
    gRows.sort((a, b) => {
      const ta = Number.isNaN(a.t_start_ms) ? -Infinity : a.t_start_ms;
      const tb = Number.isNaN(b.t_start_ms) ? -Infinity : b.t_start_ms;
      return ta - tb;
    });

    // Start at same deterministic initial orientation as main.js
    let q = initialQuatFromModel(gRows[0].model);

    for (const r of gRows) {
      if (r.actionId === null || r.actionId === -1) {
        // No move: orientation stays as-is; just read roll
        const e = eulerYXZFromMat3(mat3FromQuat(q));
        r.recovered_after_eulerZ_deg = r2d(e.roll).toFixed(6);
        continue;
      }

      // Map actionId → world axis + direction
      let axis = null;
      let ang = STEP;

      if (r.actionId === 0) { axis = AX; ang = -STEP; } // Up    → world X -5°
      if (r.actionId === 1) { axis = AX; ang =  STEP; } // Down  → world X +5°
      if (r.actionId === 2) { axis = AY; ang = -STEP; } // Left  → world Y -5°
      if (r.actionId === 3) { axis = AY; ang =  STEP; } // Right → world Y +5°

      if (axis) {
        const qAxis = quatFromAxisAngle(axis[0], axis[1], axis[2], ang);
        // Pre-multiply = world-space rotation
        q = quatMul(qAxis, q);
      }

      const e = eulerYXZFromMat3(mat3FromQuat(q));
      r.recovered_after_eulerZ_deg = r2d(e.roll).toFixed(6);
    }
  }

  return rows;
}

// ---------------------- CLI wrapper ----------------------
async function main() {
  const args = process.argv.slice(2);
  let files = [];
  let inplace = false;

  if (args.includes('--inplace')) {
    inplace = true;
  }

  if (args[0] === '--dir') {
    const dir = args[1] || '.';
    let pattern = 'record_VCURIOSITY_*.csv';

    const patIdx = args.indexOf('--pattern');
    if (patIdx >= 0 && args[patIdx + 1]) {
      pattern = args[patIdx + 1];
    }

    const star = pattern.indexOf('*');
    const prefix = star >= 0 ? pattern.slice(0, star) : pattern;
    const suffix = star >= 0 ? pattern.slice(star + 1) : '';

    for (const name of fs.readdirSync(dir)) {
      const ok = star >= 0
        ? (name.startsWith(prefix) && name.endsWith(suffix))
        : name === pattern;
      if (ok) files.push(path.join(dir, name));
    }

    if (!files.length) {
      console.error(`No files matched ${pattern} in ${dir}`);
      process.exit(1);
    }
  } else {
    // Treat remaining non-flag args as file paths
    files = args.filter(a => !a.startsWith('--'));
    if (!files.length) {
      console.error(
        'Usage:\n' +
        '  node recover_eulerZ_from_actions.js <csv...>\n' +
        '  node recover_eulerZ_from_actions.js --dir <folder> [--pattern "record_VCURIOSITY_*.csv"] [--inplace]'
      );
      process.exit(1);
    }
  }

  for (const file of files) {
    const raw = fs.readFileSync(file, 'utf8');
    const { header, rows } = parseCSV(raw);

    // Add column to header if needed
    const outHeader = [...header];
    if (!outHeader.includes('recovered_after_eulerZ_deg')) {
      outHeader.push('recovered_after_eulerZ_deg');
    }

    const outRows = addRecoveredEulerZ(rows);
    const outCsv  = toCSV(outHeader, outRows);

    let outPath;
    if (inplace) {
      outPath = file; // overwrite
    } else {
      const ext = path.extname(file);
      const base = file.slice(0, -ext.length);
      outPath = `${base}_with_eulerZ${ext || '.csv'}`;
    }

    fs.writeFileSync(outPath, outCsv, 'utf8');
    console.log(`✅ Wrote ${outPath}`);
  }
}

main().catch(err => {
  console.error('Error:', err.stack || err);
  process.exit(1);
});
