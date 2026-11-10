# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, requests, questions): CC BY-NC-SA 4.0
"""Level 6: Cactus. NOT, IN, BETWEEN. Placeholder painting."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q, circle, rect

FILE = "level06_cactus.geojson"
GRID = "level06_cactus.grid.json"
KEY = {"S": {"name": "sky", "color": "#a9d6f5"}, "D": {"name": "sand", "color": "#e9c98f"},
       "C": {"name": "cactus", "color": "#3c8d3f"}, "F": {"name": "flower", "color": "#ff6fa8"},
       "O": {"name": "sun", "color": "#ffc107"}}
NAMES_A = ["Dry", "Coyote", "Mesa", "Juniper", "Red Rock", "Sage", "Cottonwood", "Antelope", "Badger", "Horse",
           "Lone Pine", "Granite", "Willow", "Rabbit", "Ruby", "Cedar", "Quail", "Wild Horse"]
NAMES_B = ["Wash", "Flat", "Draw", "Canyon", "Springs", "Basin", "Bench", "Ridge", "Valley", "Point", "Butte"]


def painting(px, py, col=0, row=0):
    if circle(px, py, 33.5, 5, 3.2):
        return "sun"
    if circle(px, py, 20, 4.9, 1.2) or circle(px, py, 14.8, 7.8, 0.9) or circle(px, py, 25.2, 10.3, 0.9):
        return "flower"
    cactus = (rect(px, py, 18.3, 21.7, 6.5, 25.5) or circle(px, py, 20, 6.5, 1.7)
              or rect(px, py, 13.8, 18.3, 14, 15.8) or rect(px, py, 13.8, 15.8, 9, 15.8) or circle(px, py, 14.8, 9, 1.0)
              or rect(px, py, 21.7, 26.2, 17, 18.8) or rect(px, py, 24.2, 26.2, 11.5, 18.8) or circle(px, py, 25.2, 11.5, 1.0))
    if cactus:
        return "cactus"
    return "sand" if py > 24.5 + 0.6 * math.sin(px / 3) else "sky"


def outside(rnd, lo, hi, below, above):
    """A value outside lo..hi, sometimes exactly on the edge (lo-1 or hi+1)."""
    r = rnd.random()
    if r < 0.08:
        return lo - 1
    if r < 0.16:
        return hi + 1
    return rnd.randint(*below) if r < 0.58 else rnd.randint(*above)


def build():
    rnd = random.Random(6)
    grid = Grid(40, 32, gem=3000)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        if region in ("sky", "sun"):
            state = rnd.choice(["AZ", "NM", "NV"])
        elif region == "sand":
            state = rnd.choice(["UT", "CO", "ID"])
        else:
            state = rnd.choice(["AZ", "NM", "NV", "UT", "CO", "ID"])
        if region == "cactus":
            status = rnd.choice(["Inactive", "Vacant"])
        elif region == "flower":
            status = rnd.choice(["Active", "Inactive", "Vacant"])
        else:
            status = "Active"
        year = rnd.choice([2015, 2018, rnd.randint(2015, 2018)]) if region == "flower" \
            else outside(rnd, 2015, 2018, (1996, 2014), (2019, 2024))
        aums = rnd.choice([4000, 5000, rnd.randint(4000, 5000)]) if region == "sun" \
            else outside(rnd, 4000, 5000, (40, 3999), (5001, 9800))
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "allot_no": f"{fid:05d}",
            "allot_name": f"{rnd.choice(NAMES_A)} {rnd.choice(NAMES_B)}",
            "state": state,
            "status": status,
            "aums": aums,
            "last_eval_yr": year,
        })
    write_layer(FILE, grid, records)

    return {
        "number": 6, "title": "Cactus", "skill": "NOT, IN, BETWEEN",
        "dataset": "Grazing allotments", "table": "allotments",
        "about": "Public-land grazing allotments across several western states, one polygon per allotment.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "<b>IN</b> is a shortcut for a list of ORs: <code>state IN ('AZ', 'NM', 'NV')</code> means the same as <code>state = 'AZ' OR state = 'NM' OR state = 'NV'</code>.",
            "<b>NOT</b> flips a condition: <code>NOT status = 'Active'</code> selects everything that isn’t Active. You can also write <code>status &lt;&gt; 'Active'</code>. <code>NOT IN</code> works too: <code>state NOT IN ('AZ', 'NM')</code>.",
            "<b>BETWEEN</b> is a shortcut for a range: <code>yr BETWEEN 2015 AND 2018</code> means <code>yr &gt;= 2015 AND yr &lt;= 2018</code>. Both ends are <b>included</b>.",
        ],
        "questions": [
            q("Does <code>last_eval_yr BETWEEN 2015 AND 2018</code> select an allotment evaluated in 2018?",
              ["Yes", "No"], 0, "BETWEEN includes both ends of the range.",
              [None, "BETWEEN is inclusive: it means <code>&gt;= 2015 AND &lt;= 2018</code>."]),
            q("Which query means the same as <code>state IN ('AZ', 'NM')</code>?",
              ["<code>state = 'AZ' AND state = 'NM'</code>", "<code>state = 'AZ' OR state = 'NM'</code>",
               "<code>state = 'AZ, NM'</code>", "<code>state BETWEEN 'AZ' AND 'NM'</code>"],
              1, "IN is a list of ORs.",
              ["An allotment can only be in one state, so AND selects nothing.", None,
               "That looks for the literal text “AZ, NM”.",
               "BETWEEN on text compares alphabetically, so it would also catch states like CO and ID."]),
        ],
        "fields": [
            FID,
            {"name": "allot_no", "type": "TEXT", "about": "Allotment number"},
            {"name": "allot_name", "type": "TEXT", "about": "Allotment name"},
            {"name": "state", "type": "TEXT", "about": "Two-letter state code"},
            {"name": "status", "type": "TEXT", "about": "Permit status"},
            {"name": "aums", "type": "INTEGER", "about": "Animal unit months of grazing permitted per year"},
            {"name": "last_eval_yr", "type": "INTEGER", "about": "Year of the last land health evaluation"},
        ],
        "requests": [
            req("Sky Blue", "#a9d6f5", "Allotments in <b>Arizona, New Mexico or Nevada</b>", attr("state IN ('AZ', 'NM', 'NV')")),
            req("Sand", "#e9c98f", "Allotments in <b>any other state</b>", attr("state NOT IN ('AZ', 'NM', 'NV')")),
            req("Saguaro", "#3c8d3f", "Allotments whose status is <b>anything except Active</b>", attr("NOT status = 'Active'")),
            req("Pink", "#ff6fa8", "Allotments last evaluated <b>from 2015 through 2018</b>", attr("last_eval_yr BETWEEN 2015 AND 2018")),
            req("Gold", "#ffc107", "Allotments permitted for <b>4,000 to 5,000 AUMs</b> (both included)", attr("aums BETWEEN 4000 AND 5000")),
        ],
    }
