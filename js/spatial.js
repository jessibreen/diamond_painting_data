// SPDX-FileCopyrightText: 2026 Jessica Breen
// SPDX-License-Identifier: GPL-3.0-or-later
// Select by Location on plain x/y coordinates (meters on a flat map).
// The paintings are fictional, so there is no map projection to worry about.
//
// Every shape is prepared into { kind, rings | pts, cx, cy, r }:
//   kind 'polygon' -> rings: [[x, y], ...] (outer ring, not closed)
//   kind 'line'    -> pts:   [[x, y], ...]
//   kind 'point'   -> pts:   [[x, y]]
// cx, cy, r give a bounding circle used to skip far-away pairs quickly.

let EPS = 1e-3;

function finish(g, pts) {
  let cx = 0, cy = 0;
  for (const [x, y] of pts) { cx += x; cy += y; }
  cx /= pts.length; cy /= pts.length;
  let r = 0;
  for (const [x, y] of pts) r = Math.max(r, Math.hypot(x - cx, y - cy));
  return Object.assign(g, { cx, cy, r });
}

export function prepareGeometry(geom) {
  if (geom.type === 'Polygon') {
    const ring = geom.coordinates[0].slice(0, -1);
    return finish({ kind: 'polygon', ring }, ring);
  }
  if (geom.type === 'LineString') return finish({ kind: 'line', pts: geom.coordinates }, geom.coordinates);
  if (geom.type === 'Point') return finish({ kind: 'point', pts: [geom.coordinates] }, [geom.coordinates]);
  throw new Error(`Unsupported geometry type ${geom.type}`);
}

/** Prepare the main (hex) layer. Also sets the tolerance from the hex size. */
export function prepare(features) {
  const geoms = features.map((f) => prepareGeometry(f.geometry));
  if (geoms.length) EPS = geoms[0].r * 1e-3;
  return geoms;
}

export function pointInRing(x, y, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function segDist(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const len = dx * dx + dy * dy;
  const t = len ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len)) : 0;
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function segsCross(a, b, c, d) {
  const o = (p, q, r) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
  const d1 = o(c, d, a), d2 = o(c, d, b), d3 = o(a, b, c), d4 = o(a, b, d);
  return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
}

function segSegDist(a, b, c, d) {
  if (segsCross(a, b, c, d)) return 0;
  return Math.min(segDist(a[0], a[1], c[0], c[1], d[0], d[1]), segDist(b[0], b[1], c[0], c[1], d[0], d[1]),
    segDist(c[0], c[1], a[0], a[1], b[0], b[1]), segDist(d[0], d[1], a[0], a[1], b[0], b[1]));
}

function segments(g) {
  if (g.kind === 'polygon') return g.ring.map((p, i) => [p, g.ring[(i + 1) % g.ring.length]]);
  if (g.kind === 'line') return g.pts.slice(0, -1).map((p, i) => [p, g.pts[i + 1]]);
  return [[g.pts[0], g.pts[0]]];
}

function vertices(g) { return g.kind === 'polygon' ? g.ring : g.pts; }

/** Shortest distance between two shapes (0 if they touch or overlap). */
function distance(a, b) {
  if (a === b) return 0;
  if (a.kind === 'polygon' && vertices(b).some(([x, y]) => pointInRing(x, y, a.ring))) return 0;
  if (b.kind === 'polygon' && vertices(a).some(([x, y]) => pointInRing(x, y, b.ring))) return 0;
  let d = Infinity;
  for (const [p, q] of segments(a)) for (const [r, s] of segments(b)) {
    d = Math.min(d, segSegDist(p, q, r, s));
    if (d === 0) return 0;
  }
  return d;
}

/** Do the insides of two shapes overlap (not just their boundaries)? */
function interiorsOverlap(a, b) {
  if (a === b) return true;
  if (a.kind !== 'polygon' || b.kind !== 'polygon') return false;
  return pointInRing(a.cx, a.cy, b.ring) || pointInRing(b.cx, b.cy, a.ring);
}

/** Is shape t completely inside polygon s? */
function within(t, s) {
  if (s.kind !== 'polygon') return t === s;
  // a point on the boundary is not inside (as in ArcGIS and QGIS)
  if (t.kind === 'point') {
    const [x, y] = t.pts[0];
    return pointInRing(x, y, s.ring) && !segments(s).some(([p, q]) => segDist(x, y, p[0], p[1], q[0], q[1]) <= EPS);
  }
  if (!vertices(t).every(([x, y]) => pointInRing(x, y, s.ring) || segments(s).some(([p, q]) => segDist(x, y, p[0], p[1], q[0], q[1]) <= EPS))) return false;
  // no edge of t may cross out of s
  for (const [p, q] of segments(t)) for (const [r, u] of segments(s)) if (segsCross(p, q, r, u)) return false;
  return true;
}

/**
 * Select target features by their relationship to source shapes.
 * targets, sources: prepared geometries. sourceIdx: which sources to use (a Set of indexes, or null for all).
 * relation: 'intersects' | 'touches' | 'distance' | 'within' | 'contains' | 'center_in'
 */
export function selectByLocation(targets, sources, sourceIdx, relation, dist = 0) {
  const out = new Set();
  const src = sourceIdx ? [...sourceIdx].map((i) => sources[i]) : sources;
  const reach = relation === 'distance' ? dist : 0;
  for (let t = 0; t < targets.length; t++) {
    const T = targets[t];
    for (const S of src) {
      if (Math.hypot(T.cx - S.cx, T.cy - S.cy) > T.r + S.r + reach + EPS) continue;
      let hit;
      if (relation === 'intersects') hit = distance(T, S) <= EPS;
      else if (relation === 'touches') hit = T !== S && distance(T, S) <= EPS && !interiorsOverlap(T, S);
      else if (relation === 'distance') hit = distance(T, S) <= dist + EPS;
      else if (relation === 'within') hit = within(T, S);
      else if (relation === 'contains') hit = within(S, T);
      else if (relation === 'center_in') hit = S.kind === 'polygon' ? pointInRing(T.cx, T.cy, S.ring) : T === S;
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
