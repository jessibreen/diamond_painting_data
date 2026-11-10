# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, requests, questions): CC BY-NC-SA 4.0
"""Level 2: Sunset. Comparison operators."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q

FILE = "level02_sunset.geojson"
GRID = "level02_sunset.grid.json"
KEY = {"P": {"name": "plum", "color": "#5b2a6e"}, "R": {"name": "rose", "color": "#e0457b"},
       "T": {"name": "tangerine", "color": "#f6872b"}, "S": {"name": "sun", "color": "#ffd23f"},
       "N": {"name": "navy", "color": "#1d2f5e"}, "G": {"name": "glint", "color": "#f8a65a"}}

# The first version of the picture: elevation bands by row, a sun on the horizon
# and fog glints on the water. After the grid file exists, edit that instead.
SKY_ELEV = [99, 95, 92, 88, 85, 84, 80, 77, 73, 70, 66, 62, 59, 55, 52, 48, 45, 41]


def painting(px, py, col, row):
    horizon = len(SKY_ELEV)
    if row < horizon:
        if math.hypot(px - 16.0, py - (horizon - 0.2) * 0.866) <= 6.2:
            return "sun"
        band = SKY_ELEV[row]
        return "plum" if band >= 85 else "rose" if band > 62 else "tangerine"
    rnd = random.Random(row * 1000 + col)
    width = 4.5 - (row - horizon) * 0.25
    if abs(px - 16.0) <= width and (row + col) % 2 == 0 and rnd.random() < 0.75:
        return "glint"
    return "navy"


def edge_or(rnd, edge, lo, hi):
    """Usually a random value in lo..hi, sometimes exactly the edge value."""
    return edge if rnd.random() < 0.15 else rnd.randint(lo, hi)


def build():
    rnd = random.Random(2)
    grid = Grid(32, 30, gem=5000)
    regions = region_grid(GRID, grid, KEY, painting)
    # Each region's values are chosen so the requests below pick out exactly that region.
    # The edge values (850, 620, 400, 1900, 1899) are what make > and >= give different answers.
    elev = {"plum": lambda: edge_or(rnd, 850, 850, 999), "rose": lambda: rnd.randint(621, 849),
            "tangerine": lambda: edge_or(rnd, 620, 401, 620), "sun": lambda: rnd.randint(401, 999),
            "navy": lambda: edge_or(rnd, 400, 0, 400), "glint": lambda: rnd.randint(0, 400)}
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "huc12": f"0105000{row:02d}{col:03d}",
            "mean_elev_m": elev[region](),
            "solar_kwh": edge_or(rnd, 1900, 1900, 2000) if region == "sun" else edge_or(rnd, 1899, 1100, 1899),
            "fog_days": rnd.randint(4, 40) if region == "glint" else 0,
            "precip_mm": rnd.randint(600, 1800),
            "area_km2": round(rnd.uniform(18, 95), 1),
        })
    write_layer(FILE, grid, records)

    return {
        "number": 2, "title": "Sunset", "skill": "Comparisons ( >, <, >=, <=, <> )",
        "dataset": "Mountain sub-watersheds", "table": "watersheds",
        "about": "Small watersheds across a mountain range, one polygon per watershed.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "Not every question is “equals.” Numbers can be compared: <code>&gt;</code> greater than, <code>&lt;</code> less than, <code>&gt;=</code> greater than or equal to, <code>&lt;=</code> less than or equal to, and <code>&lt;&gt;</code> not equal to.",
            "Watch the edges! <code>pop &gt; 5000</code> leaves out a town of exactly 5000. <code>pop &gt;= 5000</code> includes it. Requests say this in words: “more than,” “at least,” “or higher,” “or less.”",
            "Leave commas out of numbers: write <code>1900</code>, not <code>1,900</code>.",
            "This table has more fields than you need. Part of the job is figuring out which field answers each request.",
            "Filling a hex replaces any color already there, like pressing a new gem on top. Work down the color key in order. Some colors are used for more than one request.",
        ],
        # Students must answer every question correctly before they can start;
        # add "questions_required": False to a level to make them optional.
        "questions": [
            q("A request asks for watersheds with a mean elevation of <b>at least</b> 850 m. Which condition matches?",
              ["<code>mean_elev_m &gt; 850</code>", "<code>mean_elev_m &gt;= 850</code>",
               "<code>mean_elev_m &lt;= 850</code>", "<code>mean_elev_m = 850</code>"],
              1, "“At least” includes 850 itself, so use <code>&gt;=</code>.",
              ["<code>&gt;</code> leaves out a watershed at exactly 850 m.", None,
               "<code>&lt;=</code> picks 850 and everything <i>below</i> it.",
               "<code>=</code> only picks watersheds at exactly 850 m."]),
            q("Which condition is written correctly?",
              ["<code>pop =&gt; 5000</code>", "<code>pop &gt;= 5,000</code>",
               "<code>pop &gt;= 5000</code>", "<code>pop &gt;= '5000'</code>"],
              2, "The <code>&gt;</code> comes before the <code>=</code>, and the number has no comma or quotes.",
              ["SQL writes it <code>&gt;=</code>, with the <code>&gt;</code> first.",
               "Leave the comma out of numbers.", None,
               "<code>pop</code> is a number, so its values don’t get quotes."]),
            q("Which watersheds does <code>mean_elev_m &lt;&gt; 400</code> select?",
              ["Only watersheds at exactly 400 m", "Every watershed except those at exactly 400 m",
               "Watersheds below 400 m", "Watersheds above 400 m"],
              1, "<code>&lt;&gt;</code> means “not equal to,” so it keeps everything above <i>and</i> below 400 m.",
              ["That would be <code>= 400</code>.", None,
               "<code>&lt;&gt;</code> isn’t “less than”: it means “not equal to.” What about watersheds above 400 m?",
               "<code>&lt;&gt;</code> isn’t “greater than”: it means “not equal to.” What about watersheds below 400 m?"]),
        ],
        "fields": [
            FID,
            {"name": "huc12", "type": "TEXT", "about": "12-digit hydrologic unit code that identifies the watershed"},
            {"name": "mean_elev_m", "type": "INTEGER", "about": "Average elevation of the watershed, in meters"},
            {"name": "solar_kwh", "type": "INTEGER", "about": "Average sunlight received per year, in kWh per square meter"},
            {"name": "fog_days", "type": "INTEGER", "about": "Days with fog recorded last year"},
            {"name": "precip_mm", "type": "INTEGER", "about": "Precipitation last year, in millimeters"},
            {"name": "area_km2", "type": "REAL", "about": "Area of the watershed, in square kilometers"},
        ],
        "requests": [
            req("Tangerine", "#f6872b", "Watersheds with a mean elevation <b>above 400 m</b>", attr("mean_elev_m > 400")),
            req("Rose", "#e0457b", "Watersheds with a mean elevation <b>above 620 m</b>", attr("mean_elev_m > 620")),
            req("Plum", "#5b2a6e", "Watersheds with a mean elevation of <b>850 m or higher</b>", attr("mean_elev_m >= 850")),
            req("Gold", "#ffd23f", "Watersheds that receive <b>at least 1,900 kWh/m²</b> of sunlight a year", attr("solar_kwh >= 1900")),
            req("Navy", "#1d2f5e", "Watersheds with a mean elevation of <b>400 m or lower</b>", attr("mean_elev_m <= 400")),
            req("Tangerine", "#f6872b", "Watersheds that recorded <b>any</b> fog days last year", attr("fog_days <> 0")),
        ],
    }
