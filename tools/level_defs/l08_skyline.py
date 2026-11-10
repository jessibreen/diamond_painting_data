# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 8: Night skyline. NULL. Placeholder painting."""
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q, circle

FILE = "level08_skyline.geojson"
GRID = "level08_skyline.grid.json"
KEY = {"S": {"name": "sky", "color": "#2c3e6b"}, "T": {"name": "star", "color": "#ffffff"},
       "M": {"name": "moon", "color": "#fff3c4"}, "B": {"name": "building", "color": "#121420"},
       "W": {"name": "window", "color": "#ffd166"}}
BUILDINGS = [(0, 4.5, 17), (4.5, 8, 20.5), (8, 12.5, 14), (12.5, 15, 19), (15, 19.5, 11.5), (19.5, 22, 17.5),
             (22, 26.5, 15), (26.5, 29, 20), (29, 33.5, 13.5), (33.5, 36, 18.5), (36, 40.5, 15.5)]
STARS = [(3, 3), (8, 6.5), (12, 2), (17, 5), (22, 3), (25, 8), (36, 10), (6, 11), (14, 8.5), (20, 9),
         (38, 3), (27, 2), (10, 10), (2, 8), (35, 1.5), (18, 1.5)]
USES = ["residential", "office", "retail", "mixed use", "hotel", "parking garage", "warehouse"]
LOT_USES = ["vacant lot", "surface parking", "plaza", "park"]
STREETS = ["Main St", "Elm St", "Water St", "Union Ave", "Bridge St", "Market St", "Canal St", "High St"]


def painting(px, py, col, row):
    rnd = random.Random(row * 1000 + col)
    if circle(px, py, 31, 6, 3.6) and not circle(px, py, 32.6, 5, 3.2):
        return "moon"
    for x0, x1, top in BUILDINGS:
        if x0 <= px < x1 and py >= top:
            lit = col % 3 == 1 and row % 3 == 1 and py >= top + 1.2 and x0 + 0.8 < px < x1 - 0.8
            return "window" if lit and rnd.random() < 0.65 else "building"
    if any(circle(px, py, sx, sy, 0.55) for sx, sy in STARS):
        return "star"
    return "sky"


def build():
    rnd = random.Random(8)
    grid = Grid(40, 32, gem=30)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        addr = f"{rnd.randint(1, 980)} {rnd.choice(STREETS)}"
        r = {"fid": fid, "_col": col, "_row": row, "bldg_id": f"B{fid:05d}"}
        if region in ("building", "window"):
            r.update(bldg_use=rnd.choice(USES), height_ft=rnd.randint(20, 240),
                     year_built=None if region == "window" else rnd.randint(1890, 2022), addr=addr)
        else:   # sky, star, moon: lots without a measured height
            r.update(bldg_use=None if region == "moon" else rnd.choice(LOT_USES), height_ft=None,
                     year_built=rnd.choice([None, rnd.randint(1890, 2022)]),
                     addr=None if region == "star" else addr)
        records.append(r)
    write_layer(FILE, grid, records)

    return {
        "number": 8, "title": "Night skyline", "skill": "NULL (the “= NULL” trap)",
        "dataset": "Downtown building footprints", "table": "footprints",
        "about": "Building and lot footprints from a downtown survey, one polygon per footprint. Some values were never recorded.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "Real data has gaps. When a value was never recorded, the field holds <b>NULL</b>: not zero, not blank text, just “no value.” The attribute table shows it as <code>&lt;Null&gt;</code>.",
            "To find missing values, write <code>field IS NULL</code>. To find values that are there, write <code>field IS NOT NULL</code>.",
            "The trap: <code>field = NULL</code> never selects anything, because nothing is “equal” to an unknown, not even another unknown.",
            "NULLs also drop out of comparisons: <code>height_ft &lt; 50</code> skips every footprint whose height is NULL.",
        ],
        "questions": [
            q("What does <code>height_ft = NULL</code> select?",
              ["Every footprint with no height", "Nothing", "Every footprint with a height of 0", "Every footprint"],
              1, "Nothing is ever equal to NULL. Use <code>IS NULL</code> instead.",
              ["That’s what you want, but you have to write <code>height_ft IS NULL</code>.", None,
               "NULL isn’t 0. Zero is a value; NULL means there’s no value.",
               "It selects nothing, because the comparison is never true."]),
            q("Does <code>height_ft &lt; 50</code> select footprints whose height is NULL?",
              ["Yes", "No"], 1, "A missing height isn’t less than 50, or more than 50. It’s unknown, so it’s skipped.",
              ["An unknown value can’t be compared, so those footprints are left out.", None]),
        ],
        "fields": [
            FID,
            {"name": "bldg_id", "type": "TEXT", "about": "Footprint ID"},
            {"name": "bldg_use", "type": "TEXT", "about": "What the building or lot is used for"},
            {"name": "height_ft", "type": "INTEGER", "about": "Building height, in feet (not measured for open lots)"},
            {"name": "year_built", "type": "INTEGER", "about": "Year built, where known"},
            {"name": "addr", "type": "TEXT", "about": "Street address"},
        ],
        "requests": [
            req("Twilight", "#2c3e6b", "Footprints with <b>no height</b> on record", attr("height_ft IS NULL")),
            req("Ink", "#121420", "Footprints that <b>do</b> have a height on record", attr("height_ft IS NOT NULL")),
            req("Lamplight", "#ffd166", "Footprints with a height on record but <b>no year built</b>",
                attr("height_ft IS NOT NULL AND year_built IS NULL")),
            req("White", "#ffffff", "Footprints missing <b>both</b> a height and an address",
                attr("height_ft IS NULL AND addr IS NULL")),
            req("Moonbeam", "#fff3c4", "Footprints whose <b>use</b> was never recorded", attr("bldg_use IS NULL")),
        ],
    }
