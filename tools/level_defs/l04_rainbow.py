# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 4: Rainbow. OR (and the "= 'a' OR 'b'" trap). Placeholder painting."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q, circle

FILE = "level04_rainbow.geojson"
GRID = "level04_rainbow.grid.json"
KEY = {"S": {"name": "sky", "color": "#bde4f4"}, "G": {"name": "ground", "color": "#7cb342"},
       "C": {"name": "cloud", "color": "#ffffff"}, "R": {"name": "red", "color": "#e53935"},
       "O": {"name": "orange", "color": "#fb8c00"}, "Y": {"name": "yellow", "color": "#fdd835"},
       "E": {"name": "green", "color": "#43a047"}, "B": {"name": "blue", "color": "#1e88e5"},
       "V": {"name": "violet", "color": "#8e24aa"}}
BANDS = ["red", "orange", "yellow", "green", "blue", "violet"]          # outside to inside
ZONES = {"red": ("R-1", "R-2"), "orange": ("R-3", "R-4"), "yellow": ("C-1", "C-2"),
         "green": ("C-3", "MU"), "blue": ("I-1", "I-2"), "violet": ("I-3", "PUD"),
         "sky": ("OS", "PARK"), "ground": ("AG", "RR")}
HEIGHT = {"R": (28, 45), "C": (40, 120), "M": (50, 90), "I": (35, 80), "P": (30, 60), "O": (0, 25), "A": (25, 40)}
CLOUDS = [(4.5, 24, 2.4), (7.5, 23, 2.8), (10.5, 24.3, 2.2), (29.5, 24.3, 2.2), (32.5, 23, 2.8), (35.5, 24, 2.4)]


def painting(px, py, col=0, row=0):
    if any(circle(px, py, *c) for c in CLOUDS):
        return "cloud"
    d = math.hypot(px - 20, py - 25)
    if py <= 25 and 8.5 <= d < 17.5:
        return BANDS[min(5, int((17.5 - d) / 1.5))]
    return "ground" if py > 25.3 else "sky"


def build():
    rnd = random.Random(4)
    grid = Grid(40, 32, gem=200)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        if region == "cloud":
            if rnd.random() < 0.5:
                zone, height = "INST", rnd.randint(40, 75)
            else:
                zone, height = "C-2", rnd.randint(150, 300)      # downtown high-rise district
        else:
            zone = rnd.choice(ZONES[region])
            lo, hi = HEIGHT[zone[0]]
            height = rnd.randint(lo, hi)
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "zone_id": f"Z-{fid:04d}",
            "zone_code": zone,
            "max_height_ft": height,
            "min_lot_sqft": rnd.choice([5000, 7500, 10000, 20000]) if zone.startswith("R") else 0,
            "adopted_yr": rnd.randint(1962, 2023),
        })
    write_layer(FILE, grid, records)

    return {
        "number": 4, "title": "Rainbow", "skill": "OR (and the “= 'a' OR 'b'” trap)",
        "dataset": "City zoning districts", "table": "zoning",
        "about": "Zoning districts from a city’s zoning map, one polygon per district.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "<b>OR</b> joins two conditions, and a feature is selected if <b>either one</b> (or both) is true. OR usually selects <i>more</i> features; AND selects fewer.",
            "<code>county = 'Kent' OR county = 'Sussex'</code> selects features in either county.",
            "The classic mistake is <code>county = 'Kent' OR 'Sussex'</code>. It reads fine in English, but SQL sees <code>'Sussex'</code> as a condition on its own, and it doesn’t mean what you want. Each side of OR needs the field name, the operator and the value.",
            "OR works across different fields too: <code>zone_code = 'INST' OR max_height_ft &gt; 120</code>.",
        ],
        "questions": [
            q("Which query selects districts zoned <code>R-1</code> or <code>R-2</code>?",
              ["<code>zone_code = 'R-1' OR 'R-2'</code>", "<code>zone_code = 'R-1' OR zone_code = 'R-2'</code>",
               "<code>zone_code = 'R-1' AND zone_code = 'R-2'</code>", "<code>zone_code = 'R-1, R-2'</code>"],
              1, "Each side of OR is a complete condition.",
              ["This is the classic trap: the right side is missing <code>zone_code =</code>.", None,
               "A district can’t have two zone codes at once, so AND selects nothing.",
               "That looks for one district whose code is literally the text “R-1, R-2”."]),
            q("Compared with <code>a AND b</code>, does <code>a OR b</code> select more features or fewer?",
              ["More (or the same)", "Fewer (or the same)"], 0,
              "OR only needs one condition to be true, so it can only add features.",
              [None, "AND is the strict one: it needs both conditions to be true."]),
        ],
        "fields": [
            FID,
            {"name": "zone_id", "type": "TEXT", "about": "District ID"},
            {"name": "zone_code", "type": "TEXT", "about": "Zoning district code (R = residential, C = commercial, I = industrial…)"},
            {"name": "max_height_ft", "type": "INTEGER", "about": "Tallest building allowed, in feet"},
            {"name": "min_lot_sqft", "type": "INTEGER", "about": "Smallest lot allowed for a new house, in square feet (0 = no minimum)"},
            {"name": "adopted_yr", "type": "INTEGER", "about": "Year the district was adopted"},
        ],
        "requests": [
            req("Sky Blue", "#bde4f4", "Districts zoned <b>OS</b> or <b>PARK</b>", attr("zone_code = 'OS' OR zone_code = 'PARK'")),
            req("Olive", "#7cb342", "Districts zoned <b>AG</b> or <b>RR</b>", attr("zone_code = 'AG' OR zone_code = 'RR'")),
            req("Red", "#e53935", "Districts zoned <b>R-1</b> or <b>R-2</b>", attr("zone_code = 'R-1' OR zone_code = 'R-2'")),
            req("Orange", "#fb8c00", "Districts zoned <b>R-3</b> or <b>R-4</b>", attr("zone_code = 'R-3' OR zone_code = 'R-4'")),
            req("Yellow", "#fdd835", "Districts zoned <b>C-1</b> or <b>C-2</b>", attr("zone_code = 'C-1' OR zone_code = 'C-2'")),
            req("Green", "#43a047", "Districts zoned <b>C-3</b> or <b>MU</b>", attr("zone_code = 'C-3' OR zone_code = 'MU'")),
            req("Blue", "#1e88e5", "Districts zoned <b>I-1</b> or <b>I-2</b>", attr("zone_code = 'I-1' OR zone_code = 'I-2'")),
            req("Violet", "#8e24aa", "Districts zoned <b>I-3</b> or <b>PUD</b>", attr("zone_code = 'I-3' OR zone_code = 'PUD'")),
            req("White", "#ffffff", "Districts zoned <b>INST</b>, <b>or</b> any district that allows buildings <b>taller than 120 ft</b>",
                attr("zone_code = 'INST' OR max_height_ft > 120")),
        ],
    }
