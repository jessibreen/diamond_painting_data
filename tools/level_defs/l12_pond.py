# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, requests, questions): CC BY-NC-SA 4.0
"""Level 12: Pond and trail. Select by Location against other layers:
intersect, completely within, contain. The picture comes from the
reference layers' shapes. Placeholder painting."""
import random
from levelkit import Grid, FID, write_layer, write_reference, attr, loc, req, q, ellipse, ellipse_ring

FILE = "level12_pond.geojson"
POND = (25, 17, 9, 5.5)
TRAIL = [(0.6, 6), (5, 4.5), (9, 6.5), (13, 8.5), (17, 7), (21, 5), (25, 6), (29, 8.5), (33, 8), (37, 6.5), (39.8, 6)]
SPRINGS = [(5, 7.2, "Birch Spring"), (13, 11, "Fern Spring"), (21, 7.6, "Cold Spring"), (29, 11.2, "Hollow Spring"), (36, 4.0, "Ledge Spring")]


def hex_center(px, py):
    """Snap a point to the center of the hex it falls in, so it isn't on a boundary."""
    row = round((py - 0.5) / 0.8660254)
    col = round(px - 0.5 - (0.5 if row % 2 else 0))
    return (col + 0.5 + (0.5 if row % 2 else 0), row * 0.8660254 + 0.5)


def build():
    rnd = random.Random(12)
    grid = Grid(40, 32, gem=100)
    records = []
    for fid, col, row, px, py in grid.cells():
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "parcel_id": f"HP-{fid:04d}",
            "cover": "water" if ellipse(px, py, *POND) else "grassland",
            "acres": round(rnd.uniform(1.5, 3.5), 2),
            "owner_type": rnd.choice(["town", "private", "private", "land trust"]),
        })
    write_layer(FILE, grid, records)
    write_reference("level12_ponds.geojson", grid, [({"name": "Heron Pond"}, ("Polygon", ellipse_ring(*POND)))])
    write_reference("level12_trails.geojson", grid, [({"name": "Ridge Trail"}, ("LineString", TRAIL))])
    write_reference("level12_springs.geojson", grid, [({"name": n}, ("Point", hex_center(x, y))) for x, y, n in SPRINGS])

    return {
        "number": 12, "title": "Pond and trail", "skill": "Location vs. other layers: within, contains, crossed by",
        "dataset": "Parcels around Heron Pond", "table": "parcels",
        "about": "Small parcels around a pond, one polygon per parcel. Three other layers sit on top: the pond, a trail and some springs.",
        "file": FILE, "location": True, "gem_size": grid.gem, "units": "m",
        "references": [
            {"table": "ponds", "file": "level12_ponds.geojson", "kind": "polygon", "about": "Pond outline"},
            {"table": "trails", "file": "level12_trails.geojson", "kind": "line", "about": "Hiking trail"},
            {"table": "springs", "file": "level12_springs.geojson", "kind": "point", "about": "Mapped springs"},
        ],
        "lesson": [
            "So far you’ve compared parcels with other parcels. Select by Location can also compare them with <b>a different layer</b>. This level has three: a pond (polygon), a trail (line) and springs (points). They’re drawn on top of the painting.",
            "<b>Intersect</b> selects parcels that share <i>any</i> space with the other layer: a parcel half in the pond intersects it, and so does a parcel the trail passes through.",
            "<b>Are completely within</b> selects parcels that lie entirely inside the other layer’s shape, with no part sticking out.",
            "<b>Completely contain</b> is the reverse: parcels that have a whole feature of the other layer inside them, like a spring.",
            "Choose the other layer in the <b>Selecting features</b> menu.",
        ],
        "questions": [
            q("A parcel is half in the pond and half on land. Which is true?",
              ["It intersects the pond and is completely within it", "It intersects the pond but is not completely within it",
               "It is completely within the pond but doesn’t intersect it", "Neither"],
              1, "It shares space with the pond, so it intersects, but part of it sticks out, so it isn’t completely within.",
              ["Part of the parcel is on land, so it isn’t <i>completely</i> within.", None,
               "Anything completely within the pond also intersects it.",
               "It does share space with the pond."]),
            q("Which relationship finds the parcels that have a spring inside them?",
              ["Are completely within", "Completely contain", "Boundary touches"],
              1, "The parcel contains the spring.",
              ["A parcel can’t be within a point; it’s the other way around.", None,
               "A spring point inside a parcel isn’t on its boundary."]),
        ],
        "fields": [
            FID,
            {"name": "parcel_id", "type": "TEXT", "about": "Parcel ID"},
            {"name": "cover", "type": "TEXT", "about": "Main land cover (from an older survey)"},
            {"name": "acres", "type": "REAL", "about": "Parcel area, in acres"},
            {"name": "owner_type", "type": "TEXT", "about": "What kind of owner holds the parcel"},
        ],
        "requests": [
            req("Meadow", "#9ccc65", "Every <b>grassland</b> parcel", attr("cover = 'grassland'")),
            req("Shore Blue", "#81d4fa", "Parcels that touch <b>any part</b> of Heron Pond", loc("intersects", source="ponds")),
            req("Deep Blue", "#1976d2", "Parcels that are <b>completely within</b> Heron Pond", loc("within", source="ponds")),
            req("Fern", "#2e7d32", "Parcels the <b>Ridge Trail passes through</b>", loc("intersects", source="trails")),
            req("Pink", "#ec407a", "Parcels that <b>contain</b> a spring", loc("contains", source="springs")),
        ],
    }
