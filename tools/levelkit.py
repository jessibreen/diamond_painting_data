# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Shared helpers for building levels: the hex grid, writing GeoJSON,
reference layers, illustration grids, and the little request/solution
helpers used in each level file.
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "levels")
ART = os.path.join(ROOT, "art")

FID = {"name": "fid", "type": "INTEGER", "about": "Feature ID: a unique number the GIS assigns to each feature"}
ROW_STEP = math.sqrt(3) / 2      # vertical spacing between hex rows, in gem widths


class Grid:
    """A grid of pointy-top hexes.

    cols, rows  how many gems across and down
    gem         width of one gem in map units (meters), flat side to flat side

    Positions inside the picture are given in "picture units": px runs from
    0 to cols left to right, py from 0 to about rows * 0.866 top to bottom,
    and 1 unit = 1 gem. Each painting function decides what goes where using
    these units, so the same drawing code works at any gem size.
    """

    def __init__(self, cols, rows, gem):
        self.cols, self.rows, self.gem = cols, rows, gem
        self.R = gem / math.sqrt(3)
        self.height = rows * ROW_STEP          # picture height in picture units

    def cells(self):
        """Yield (fid, col, row, px, py) for every hex, top row first."""
        for row in range(self.rows):
            for col in range(self.cols):
                px = col + 0.5 + (0.5 if row % 2 else 0)
                py = row * ROW_STEP + 0.5
                yield row * self.cols + col + 1, col, row, px, py

    def to_map(self, px, py):
        """Picture units -> map coordinates (meters, y up)."""
        return [round(px * self.gem, 3), round((self.height + 0.5 - py) * self.gem, 3)]

    def hex_ring(self, col, row):
        px = col + 0.5 + (0.5 if row % 2 else 0)
        py = row * ROW_STEP + 0.5
        cx, cy = self.to_map(px, py)
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts.append([round(cx + self.R * math.cos(a), 3), round(cy + self.R * math.sin(a), 3)])
        pts.append(pts[0])
        return [pts]


def write_layer(filename, grid, records):
    """records: one dict per hex with the attributes plus _col and _row."""
    feats = []
    for r in records:
        col, row = r.pop("_col"), r.pop("_row")
        feats.append({"type": "Feature", "properties": r,
                      "geometry": {"type": "Polygon", "coordinates": grid.hex_ring(col, row)}})
    with open(os.path.join(OUT, filename), "w") as f:
        json.dump({"type": "FeatureCollection", "name": filename[:-8], "features": feats}, f, separators=(",", ":"))


def write_reference(filename, grid, features):
    """Reference layer (level 12+). features: list of (properties, geometry) where
    geometry is ("Polygon", [(px, py), ...]) or ("LineString", [...]) or ("Point", (px, py))
    in picture units."""
    out = []
    for props, (kind, coords) in features:
        if kind == "Point":
            geom = {"type": "Point", "coordinates": grid.to_map(*coords)}
        elif kind == "LineString":
            geom = {"type": "LineString", "coordinates": [grid.to_map(*p) for p in coords]}
        else:
            ring = [grid.to_map(*p) for p in coords]
            ring.append(ring[0])
            geom = {"type": "Polygon", "coordinates": [ring]}
        out.append({"type": "Feature", "properties": props, "geometry": geom})
    with open(os.path.join(OUT, filename), "w") as f:
        json.dump({"type": "FeatureCollection", "name": filename[:-8], "features": out}, f, separators=(",", ":"))


def load_art_grid(name):
    """Region letters for each hex, made from an illustration (see art/README.md)."""
    with open(os.path.join(ART, name)) as f:
        data = json.load(f)
    return data


def region_grid(filename, grid, key, painting=None):
    """The picture for a level, as an editable grid file in art/.

    key       {letter: {"name": region name, "color": preview color}}
    painting  function(px, py, col, row) -> region name, used only to create
              the grid file the first time. After that the file is the
              picture: edit it with tools/editor.html.

    Returns a function (col, row) -> region name.
    """
    path = os.path.join(ART, filename)
    by_name = {v["name"]: k for k, v in key.items()}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        if data["cols"] != grid.cols or data["rows"] != grid.rows:
            raise ValueError(f"{filename} is {data['cols']} x {data['rows']} but the level expects {grid.cols} x {grid.rows}")
        bad = {c for line in data["grid"] for c in line} - set(key)
        if bad:
            raise ValueError(f"{filename} uses letters the level doesn't know: {sorted(bad)}")
    else:
        if painting is None:
            raise FileNotFoundError(path)
        rows = []
        for row in range(grid.rows):
            line = ""
            for col in range(grid.cols):
                px = col + 0.5 + (0.5 if row % 2 else 0)
                py = row * ROW_STEP + 0.5
                line += by_name[painting(px, py, col, row)]
            rows.append(line)
        data = {"cols": grid.cols, "rows": grid.rows, "grid": rows}
    counts = {k: sum(line.count(k) for line in data["grid"]) for k in key}
    empty = [key[k]["name"] for k, n in counts.items() if n == 0]
    if empty:
        print(f"  WARNING {filename}: no gems are painted as {', '.join(empty)}. "
              "Any query that depends on them will select nothing.")
    # The level file owns the key (names and preview colors); keep the grid file in step.
    data["key"] = key
    os.makedirs(ART, exist_ok=True)
    with open(path, "w") as f:
        meta = {k: v for k, v in data.items() if k != "grid"}
        f.write(json.dumps(meta, indent=1, ensure_ascii=False)[:-2])
        f.write(',\n "grid": [\n  ' + ",\n  ".join(json.dumps(r) for r in data["grid"]) + "\n ]\n}\n")
    return lambda col, row: key[data["grid"][row][col]]["name"]


# ------------------------------------------------------------------ shapes (picture units)
def ellipse(px, py, cx, cy, rx, ry):
    return ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1


def circle(px, py, cx, cy, r):
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def rect(px, py, x0, x1, y0, y1):
    return x0 <= px <= x1 and y0 <= py <= y1


def seg_dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
    return math.hypot(px - (ax + t * (bx - ax)), py - (ay + t * (by - ay)))


def near_line(px, py, pts, width):
    return min(seg_dist(px, py, pts[i], pts[i + 1]) for i in range(len(pts) - 1)) <= width


def ellipse_ring(cx, cy, rx, ry, n=48):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


# ------------------------------------------------------------------ requests and solutions
def attr(where, method="new"):
    """A Select by Attributes step."""
    return {"type": "attribute", "where": where, "method": method}


def loc(relation, method="new", distance=None, source="selected"):
    """A Select by Location step. source is "selected" (the selected hexes)
    or the table name of a reference layer."""
    s = {"type": "location", "relation": relation, "method": method, "source": source}
    if distance is not None:
        s["distance"] = distance
    return s


def req(name, color, rule, *solution):
    """One request in the color key: gem color name, hex code, the request
    students read, and the steps that answer it."""
    return {"name": name, "color": color, "rule": rule, "solution": list(solution)}


def q(question, options, answer, explain, hints):
    """A comprehension question. hints: one per option (None for the right one)."""
    return {"question": question, "options": options, "answer": answer, "explain": explain, "hints": hints}


def catalogue_entry(lv):
    """Split the requests into a color list and requests that point at it."""
    out = {k: v for k, v in lv.items() if k != "requests"}
    out["available"] = "file" in lv
    if "requests" not in lv:
        return out
    colors, index, requests = [], {}, []
    for r in lv["requests"]:
        if r["name"] not in index:
            index[r["name"]] = len(colors)
            colors.append({"name": r["name"], "color": r["color"]})
        elif colors[index[r["name"]]]["color"] != r["color"]:
            raise ValueError(f"Level {lv['number']}: color {r['name']} has two different hex codes")
        requests.append({"color": index[r["name"]], "rule": r["rule"], "solution": r["solution"]})
    out["colors"] = colors
    out["requests"] = requests
    return out
