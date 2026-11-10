# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, requests, questions): CC BY-NC-SA 4.0
"""Level 10: Outlined cat. Select by Location: boundary touches and intersect."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, loc, req, q, ellipse, near_line

FILE = "level10_cat.geojson"
GRID = "level10_cat.grid.json"
KEY = {"B": {"name": "background", "color": "#d9cdf0"}, "C": {"name": "cat", "color": "#f28c28"},
       "E": {"name": "eye", "color": "#2e9e5b"}, "N": {"name": "nose", "color": "#ff8fab"}}
TAIL = [(21.5, 21.5), (25.0, 20.8), (27.2, 18.5), (27.8, 15.5), (27.0, 12.8)]


def painting(px, py, col=0, row=0):
    def ear(cx):
        return 1.6 <= py <= 6.0 and abs(px - cx) <= (py - 1.6) * 0.7
    if math.hypot(px - 11.0, py - 8.3) <= 1.0 or math.hypot(px - 16.0, py - 8.3) <= 1.0:
        return "eye"
    if abs(px - 13.5) <= 0.6 and abs(py - 10.9) <= 0.5:
        return "nose"
    if (ellipse(px, py, 13.5, 9.0, 6.3, 5.4) or ear(9.6) or ear(17.4)
            or ellipse(px, py, 15.0, 18.6, 8.0, 6.2) or near_line(px, py, TAIL, 0.95)):
        return "cat"
    return "background"


def build():
    rnd = random.Random(10)
    grid = Grid(32, 30, gem=100)
    regions = region_grid(GRID, grid, KEY, painting)
    owner = {"eye": "water district", "nose": "land trust", "cat": "state forest", "background": "private"}
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        o = owner[region]
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "parcel_id": f"{rnd.randint(10, 48):03d}-{fid:04d}",
            "owner_type": o,
            "acres": round(rnd.uniform(2, 160), 1),
            "zoning": rnd.choice(["RR", "RR", "AG", "CON"]) if o != "private" or rnd.random() < 0.8 else "R1",
            "deed_yr": rnd.randint(1948, 2024),
        })
    write_layer(FILE, grid, records)

    return {
        "number": 10, "title": "Outlined cat", "skill": "Select by Location: touches & intersects",
        "dataset": "Land ownership around Pine Ridge State Forest", "table": "ownership",
        "about": "Land parcels in and around a state forest, one polygon per parcel.",
        "file": FILE, "grid": f"art/{GRID}", "location": True, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "Attribute queries ask about a feature’s <b>values</b>. <b>Select by Location</b> asks where a feature is <b>in relation to other features</b>.",
            "Here the parcels are compared with the parcels you’ve <b>already selected</b>. <b>Boundary touches</b> picks parcels whose boundaries touch a selected parcel. <b>Intersect</b> picks parcels that share any area or boundary, so it also picks the selected parcels themselves.",
            "Combine tools with the <b>selection type</b>: <i>new</i> replaces the selection, <i>add to</i> adds, <i>remove from</i> takes away, and <i>select subset</i> keeps only the parcels that pass the new test too.",
            "Nothing in the attribute table says which parcels are next to the forest. Some questions can only be answered by location!",
        ],
        "questions": [
            q("You select one parcel, then run <b>Intersect</b> against it. Which parcels end up selected?",
              ["Only its neighbors", "The parcel itself and its neighbors", "Only the parcel itself", "Every parcel in the layer"],
              1, "Intersect includes anything that shares space <i>or</i> a boundary, and a parcel shares space with itself.",
              ["That’s Boundary touches. Does a parcel intersect itself?", None,
               "Its neighbors share a boundary with it, and a shared boundary counts as intersecting.",
               "Only parcels that share space or a boundary with the selected one."]),
            q("You have the forest selected and want only the <b>private</b> parcels that touch it. After running Boundary touches, what’s the next step?",
              ["Run <code>owner_type = 'private'</code> as a <b>new selection</b>",
               "Run <code>owner_type = 'private'</code> with <b>select subset from the current selection</b>",
               "Run <code>owner_type = 'private'</code> with <b>add to the current selection</b>",
               "Nothing; Boundary touches already removed the forest"],
              1, "Subset keeps only the touching parcels that are also private.",
              ["A new selection throws away the location result and selects every private parcel.", None,
               "Adding would pile every private parcel onto the selection.",
               "Forest parcels touch other forest parcels too, so they’re still in the selection."]),
        ],
        "fields": [
            FID,
            {"name": "parcel_id", "type": "TEXT", "about": "Assessor's parcel number (map-lot)"},
            {"name": "owner_type", "type": "TEXT", "about": "What kind of owner holds the parcel"},
            {"name": "acres", "type": "REAL", "about": "Parcel area, in acres"},
            {"name": "zoning", "type": "TEXT", "about": "Zoning district code"},
            {"name": "deed_yr", "type": "INTEGER", "about": "Year of the most recent deed"},
        ],
        "requests": [
            req("Lavender", "#d9cdf0", "Every <b>privately owned</b> parcel", attr("owner_type = 'private'")),
            req("Orange", "#f28c28", "Every parcel in the <b>state forest</b>", attr("owner_type = 'state forest'")),
            req("Emerald", "#2e9e5b", "Parcels owned by the <b>water district</b>", attr("owner_type = 'water district'")),
            req("Pink", "#ff8fab", "The <b>land trust</b> parcel", attr("owner_type = 'land trust'")),
            req("Black", "#1b1b2f",
                "A timber harvest is planned. Every <b>private</b> parcel that <b>shares a boundary</b> with the <b>state forest</b> must be notified. (No field says who borders the forest. Select the forest first, then use Select by Location.)",
                attr("owner_type = 'state forest'"), loc("touches"), attr("owner_type = 'private'", "subset")),
        ],
    }
