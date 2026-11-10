// SPDX-FileCopyrightText: 2026 Jessica Breen
// SPDX-License-Identifier: GPL-3.0-or-later
// Select by Location on plain x/y coordinates (millimetres on the canvas).
// The painting is fictional, so there is no map projection to worry about.

const EPS = 1e-3; // mm; coordinates are stored to 4 decimal places

export function prepare(features) {
  return features.map((f) => {
    const ring = f.geometry.coordinates[0].slice(0, -1);
    let cx = 0, cy = 0;
    for (const [x, y] of ring) { cx += x; cy += y; }
    cx /= ring.length; cy /= ring.length;
    let r = 0;
    for (const [x, y] of ring) r = Math.max(r, Math.hypot(x - cx, y - cy));
    return { ring, cx, cy, r };
  });
}

function segDist(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

export function pointInRing(x, y, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function ringDist(a, b) {
  if (pointInRing(a.cx, a.cy, b.ring) || pointInRing(b.cx, b.cy, a.ring)) return 0;
  let d = Infinity;
  for (const [P, Q] of [[a, b], [b, a]]) {
    for (const [x, y] of P.ring) {
      for (let i = 0; i < Q.ring.length; i++) {
        const [ax, ay] = Q.ring[i], [bx, by] = Q.ring[(i + 1) % Q.ring.length];
        d = Math.min(d, segDist(x, y, ax, ay, bx, by));
      }
    }
  }
  return d;
}

const overlaps = (a, b) => pointInRing(a.cx, a.cy, b.ring) || pointInRing(b.cx, b.cy, a.ring);

/**
 * Select target hexes by their relationship to the source hexes.
 * relation: 'intersects' | 'touches' | 'distance'
 */
export function selectByLocation(geoms, sourceSet, relation, distance = 0) {
  const out = new Set();
  const source = [...sourceSet].map((i) => geoms[i]);
  const reach = relation === 'distance' ? distance : 0;
  for (let t = 0; t < geoms.length; t++) {
    const T = geoms[t];
    for (const S of source) {
      if (Math.hypot(T.cx - S.cx, T.cy - S.cy) > T.r + S.r + reach + EPS) continue;
      const d = T === S ? 0 : ringDist(T, S);
      let hit;
      if (relation === 'intersects') hit = d <= EPS;
      else if (relation === 'touches') hit = d <= EPS && T !== S && !overlaps(T, S);
      else hit = d <= distance + EPS;
      if (hit) { out.add(t); break; }
    }
  }
  return out;
}

export function applyMethod(current, result, method) {
  if (method === 'new') return new Set(result);
  if (method === 'add') return new Set([...current, ...result]);
  if (method === 'remove') return new Set([...current].filter((i) => !result.has(i)));
  if (method === 'subset') return new Set([...current].filter((i) => result.has(i)));
  throw new Error('Unknown selection method ' + method);
}
