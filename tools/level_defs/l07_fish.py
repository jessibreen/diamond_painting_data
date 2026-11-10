# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 7: Fish. LIKE and wildcards. Placeholder painting."""
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q, ellipse, circle, near_line

FILE = "level07_fish.geojson"
GRID = "level07_fish.grid.json"
KEY = {"W": {"name": "water", "color": "#1565c0"}, "B": {"name": "body", "color": "#f57c00"},
       "S": {"name": "stripe", "color": "#ffffff"}, "F": {"name": "fin", "color": "#bf360c"},
       "K": {"name": "weed", "color": "#2e7d32"}, "U": {"name": "bubble", "color": "#b3e5fc"},
       "E": {"name": "eye", "color": "#1b1b2f"}}
LAKE = ["Round", "Long", "Bass", "Clear", "Echo", "Island", "Mud", "Crystal", "Loon", "Horseshoe", "Silver",
        "Otter", "Pine", "Beaver", "Twin", "Grass", "Sunset", "Pickerel", "Wolf", "Heron"]
POND = ["Duck", "Frog", "Hidden", "Turtle", "Sand", "Cedar", "Fox", "Grassy", "Shadow", "Bear", "Kettle",
        "Black", "Goose", "Hemlock", "Lily", "Moose", "Perch", "Rock"]
MILL = ["Mill Pond", "Millers Pond", "Millstone Pond", "Mill Brook Pond"]
RES = ["North", "South", "Hill", "Quarry", "Town", "Upper", "Lower", "Notch"]
SWAMP = ["Cedar", "Black", "Great", "Alder", "Moose", "Tamarack", "Bog Brook"]
SPRING = ["Spring Lake", "Cold Spring Lake", "Big Spring Lake", "Spring Hill Lake"]
WEEDS = [[(3, 27.5), (2.4, 24), (3.4, 21), (2.6, 18)], [(36, 27.5), (36.8, 24), (35.8, 21), (36.6, 17.5)],
         [(38.5, 27.5), (38, 25), (38.8, 22.5)]]


def painting(px, py, col=0, row=0):
    if circle(px, py, 10.2, 12.8, 0.9):
        return "eye"
    body = ellipse(px, py, 17, 14, 10, 6.3)
    if body and (11.2 <= px <= 12.8 or 18 <= px <= 19.6):
        return "stripe"
    if body:
        return "body"
    if (26 <= px <= 33.5 and abs(py - 14) <= (px - 26) * 0.85) \
            or (ellipse(px, py, 18, 7.6, 4, 1.6) and py < 8.3) or (ellipse(px, py, 16, 20.4, 2.6, 1.2) and py > 19.8):
        return "fin"
    if circle(px, py, 5.5, 8, 1.0) or circle(px, py, 4, 4.5, 0.8) or circle(px, py, 6.5, 1.8, 0.6):
        return "bubble"
    if any(near_line(px, py, w, 0.8) for w in WEEDS):
        return "weed"
    return "water"


def build():
    rnd = random.Random(7)
    grid = Grid(40, 32, gem=500)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        name, ftype = {
            "water": (f"{rnd.choice(LAKE)} Lake", "LakePond"),
            "body": (f"{rnd.choice(POND)} Pond", "LakePond"),
            "eye": (f"{rnd.choice(POND)} Pond", "LakePond"),
            "stripe": (rnd.choice(MILL), "LakePond"),
            "fin": (f"{rnd.choice(RES)} Reservoir", "Reservoir"),
            "weed": (f"{rnd.choice(SWAMP)} Swamp", "SwampMarsh"),
            "bubble": (rnd.choice(SPRING), "LakePond"),
        }[region]
        after_dash = 9 if region == "eye" else rnd.randint(1, 8)
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "permanent_id": f"{rnd.randint(100, 999)}-{after_dash}{rnd.randint(1000, 9999)}",
            "gnis_name": name,
            "ftype": ftype,
            "area_sqkm": round(rnd.uniform(0.02, 6.5), 2),
            "elev_ft": rnd.randint(380, 2100),
        })
    write_layer(FILE, grid, records)

    return {
        "number": 7, "title": "Fish", "skill": "LIKE and wildcards",
        "dataset": "Lakes and ponds", "table": "waterbodies",
        "about": "Named lakes, ponds, reservoirs and swamps, modeled on the National Hydrography Dataset. One polygon per waterbody.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "<code>=</code> only matches text exactly. <b>LIKE</b> matches a <b>pattern</b>, using wildcards.",
            "<code>%</code> stands for <b>any number of characters</b> (even none). <code>gnis_name LIKE '%Pond'</code> finds names that end in “Pond.” <code>LIKE 'Mill%'</code> finds names that start with “Mill.” <code>LIKE '%Spring%'</code> finds “Spring” anywhere.",
            "<code>_</code> (underscore) stands for <b>exactly one</b> character: <code>LIKE '_ake'</code> matches “Lake” and “Make” but not “Snake.”",
            "Heads up: in this tool (SQLite), LIKE ignores capital letters, so <code>'%pond'</code> also matches “Pond.” Many databases are case-sensitive, so match the capitals you see in the data.",
        ],
        "questions": [
            q("Which names does <code>gnis_name LIKE 'Mill%'</code> match?",
              ["“Mill Pond” and “Sawmill Pond”", "“Mill Pond” and “Millers Pond”", "Only “Mill”", "Any name that contains “Mill”"],
              1, "<code>'Mill%'</code> means the name starts with “Mill,” followed by anything.",
              ["“Sawmill Pond” doesn’t <i>start</i> with Mill.", None,
               "The <code>%</code> allows more characters after “Mill.”",
               "That would be <code>'%Mill%'</code>, with a wildcard on both sides."]),
            q("What does <code>_</code> stand for in a LIKE pattern?",
              ["Any number of characters", "Exactly one character", "A space", "Nothing; it’s just an underscore"],
              1, "<code>_</code> is a single-character wildcard; <code>%</code> matches any number.",
              ["That’s <code>%</code>.", None, "It matches any one character, including a space.",
               "Inside LIKE it’s a wildcard."]),
        ],
        "fields": [
            FID,
            {"name": "permanent_id", "type": "TEXT", "about": "Permanent identifier (three digits, a dash, five digits)"},
            {"name": "gnis_name", "type": "TEXT", "about": "Official name from the Geographic Names Information System"},
            {"name": "ftype", "type": "TEXT", "about": "Feature type"},
            {"name": "area_sqkm", "type": "REAL", "about": "Surface area, in square kilometers"},
            {"name": "elev_ft", "type": "INTEGER", "about": "Surface elevation, in feet"},
        ],
        "requests": [
            req("Cobalt", "#1565c0", "Waterbodies whose name <b>ends with “Lake”</b>", attr("gnis_name LIKE '%Lake'")),
            req("Tangerine", "#f57c00", "Waterbodies whose name <b>ends with “Pond”</b>", attr("gnis_name LIKE '%Pond'")),
            req("White", "#ffffff", "Waterbodies whose name <b>starts with “Mill”</b>", attr("gnis_name LIKE 'Mill%'")),
            req("Rust", "#bf360c", "Waterbodies whose name <b>ends with “Reservoir”</b>", attr("gnis_name LIKE '%Reservoir'")),
            req("Kelp", "#2e7d32", "Waterbodies whose name <b>ends with “Swamp”</b>", attr("gnis_name LIKE '%Swamp'")),
            req("Pale Aqua", "#b3e5fc", "Waterbodies whose name contains <b>“Spring” anywhere</b>", attr("gnis_name LIKE '%Spring%'")),
            req("Black", "#1b1b2f", "Waterbodies whose permanent ID has a <b>9 right after the dash</b>", attr("permanent_id LIKE '___-9%'")),
        ],
    }
