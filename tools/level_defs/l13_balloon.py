# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 13: Hot air balloon. Capstone: everything, with abbreviated field
names that send students to the field descriptions (metadata). Placeholder painting."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, loc, req, q, ellipse, circle, rect

FILE = "level13_balloon.geojson"
GRID = "level13_balloon.grid.json"
KEY = {"S": {"name": "sky", "color": "#9fd3f5"}, "C": {"name": "cloud", "color": "#ffffff"},
       "H": {"name": "hills", "color": "#7cb342"}, "R": {"name": "red", "color": "#d32f2f"},
       "G": {"name": "gold", "color": "#fbc02d"}, "B": {"name": "basket", "color": "#8d6e63"}}
CLOUDS = [(6, 8, 2.2), (9, 7, 2.8), (12, 8.3, 2.2), (37, 16, 2), (40, 15, 2.6), (43, 16.2, 2)]
SURNAMES = ["SMITH", "NGUYEN", "OKAFOR", "MARTIN", "GARCIA", "COHEN", "PATEL", "MURPHY", "LEE", "BROWN", "ROSSI", "KOWALSKI"]
FIRST = ["JOHN", "MARIA", "WEI", "AMARA", "DAVID", "PRIYA", "SEAN", "ANA", "OMAR", "LINDA"]
TOWNS = ["TOWN OF ASHBY", "ASHBY SCHOOL DISTRICT", "COUNTY OF WINDHAM", "ST MARY PARISH", "ASHBY LIBRARY ASSN"]
TRUSTS = ["FAMILY TRUST", "REVOCABLE TRUST", "LIVING TRUST", "TRUST"]
LLCS = ["HOLDINGS LLC", "PROPERTIES LLC", "REALTY LLC", "VENTURES LLC"]


def painting(px, py, col=0, row=0):
    if rect(px, py, 21.8, 26.2, 25.5, 28.5):
        return "basket"
    envelope = ellipse(px, py, 24, 12, 8.5, 9.5) or (17 <= py <= 23.5 and abs(px - 24) <= 6.5 - (py - 17) * 0.7)
    if envelope:
        return "red" if int((px - 15.5) // 2.4) % 2 == 0 else "gold"
    if any(circle(px, py, *c) for c in CLOUDS):
        return "cloud"
    if py > 26 + 2 * math.sin(px / 5):
        return "hills"
    return "sky"


def person(rnd):
    return f"{rnd.choice(SURNAMES)} {rnd.choice(FIRST)}"


def build():
    rnd = random.Random(13)
    grid = Grid(48, 36, gem=100)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        zip_ = rnd.choice(["05301", "05346", "05350"])
        yr = rnd.randint(1880, 2021)
        r = rnd.random()
        val = 249999 if r < 0.05 else 300001 if r < 0.1 else rnd.choice([rnd.randint(40000, 249999), rnd.randint(300001, 900000)])
        owner = person(rnd)
        if region in ("sky", "cloud"):
            lu = rnd.choice(["OS", "INST"])
            owner = rnd.choice(TOWNS) if lu == "INST" else rnd.choice([rnd.choice(TOWNS), person(rnd)])
            if region == "cloud":
                yr = None
        elif region == "hills":
            lu, zip_ = "AG", rnd.choice(["05301", "05346"])
        elif region == "red":
            lu, owner = rnd.choice(["RES", "COM"]), f"{rnd.choice(SURNAMES)} {rnd.choice(TRUSTS)}"
        elif region == "gold":
            lu, owner = rnd.choice(["RES", "COM"]), f"{rnd.choice(SURNAMES)} {rnd.choice(LLCS)}"
        else:   # basket
            lu, val = "COM", rnd.choice([250000, 300000, rnd.randint(250000, 300000)])
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "PARCEL_ID": f"{rnd.randint(1, 30):02d}-{rnd.randint(1, 99):02d}-{fid:04d}",
            "LU_CODE": lu, "ZIP": zip_, "OWNER_NM": owner, "YR_BLT": yr, "ASSD_VAL": val,
        })
    write_layer(FILE, grid, records)

    return {
        "number": 13, "title": "Hot air balloon", "skill": "Capstone: everything",
        "dataset": "County tax parcels", "table": "tax_parcels",
        "about": "Tax parcels from a county assessor, with the short, all-caps field names that assessor data usually has. One polygon per parcel.",
        "file": FILE, "grid": f"art/{GRID}", "location": True, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "This painting uses everything: comparisons, AND, OR, parentheses, IN, BETWEEN, LIKE, NULL, selection types and Select by Location.",
            "Real datasets rarely have friendly field names. Here they’re short and all caps, like <code>LU_CODE</code> and <code>YR_BLT</code>. Read the field descriptions (the <b>metadata</b>) before you write a query, and click <b>values</b> to see how codes are actually stored.",
            "Plan each query before you type: which field, which operator, which values? Does it need more than one step?",
        ],
        "questions": [
            q("A field called <code>ASSD_VAL</code> could mean several things. Where should you look to find out?",
              ["Guess from the name", "The field’s description (metadata)", "The painting"],
              1, "Metadata tells you what a field holds, its units and how its values are coded.",
              ["Guessing leads to wrong answers that look right.", None, "The painting isn’t part of the data."]),
            q("Which query finds AG parcels in ZIP 05301 or 05346?",
              ["<code>LU_CODE = 'AG' AND ZIP = '05301' OR ZIP = '05346'</code>",
               "<code>LU_CODE = 'AG' AND (ZIP = '05301' OR ZIP = '05346')</code>",
               "<code>LU_CODE = 'AG' AND ZIP = 05301 OR 05346</code>"],
              1, "Parentheses keep the two ZIP codes together, and ZIP is text, so its values need quotes.",
              ["Without parentheses, every parcel in 05346 is selected, AG or not.", None,
               "ZIP is a TEXT field, and each side of OR needs a complete condition."]),
        ],
        "fields": [
            FID,
            {"name": "PARCEL_ID", "type": "TEXT", "about": "Assessor parcel number (map-block-lot)"},
            {"name": "LU_CODE", "type": "TEXT", "about": "Land use code: RES residential, COM commercial, AG agricultural, OS open space, INST institutional"},
            {"name": "ZIP", "type": "TEXT", "about": "ZIP code of the parcel"},
            {"name": "OWNER_NM", "type": "TEXT", "about": "Owner name as written on the deed (last name first)"},
            {"name": "YR_BLT", "type": "INTEGER", "about": "Year the main building was built (blank if unknown)"},
            {"name": "ASSD_VAL", "type": "INTEGER", "about": "Assessed value, in dollars"},
        ],
        "requests": [
            req("Sky Blue", "#9fd3f5", "Parcels coded <b>OS</b> (open space) or <b>INST</b> (institutional)", attr("LU_CODE IN ('OS', 'INST')")),
            req("Meadow", "#7cb342", "<b>Agricultural</b> parcels in ZIP code <b>05301 or 05346</b>",
                attr("LU_CODE = 'AG' AND (ZIP = '05301' OR ZIP = '05346')")),
            req("White", "#ffffff", "Parcels with <b>no year built</b> on record", attr("YR_BLT IS NULL")),
            req("Crimson", "#d32f2f", "Parcels owned by a <b>trust</b> (TRUST appears anywhere in the owner name)", attr("OWNER_NM LIKE '%TRUST%'")),
            req("Gold", "#fbc02d", "Parcels owned by an <b>LLC</b> (the owner name ends in LLC)", attr("OWNER_NM LIKE '%LLC'")),
            req("Wicker", "#8d6e63", "Parcels assessed <b>from $250,000 to $300,000</b>", attr("ASSD_VAL BETWEEN 250000 AND 300000")),
            req("Charcoal", "#263238",
                "Every <b>OS or INST</b> parcel that <b>shares a boundary</b> with a trust- or LLC-owned parcel",
                attr("OWNER_NM LIKE '%TRUST%' OR OWNER_NM LIKE '%LLC'"), loc("touches"), attr("LU_CODE IN ('OS', 'INST')", "subset")),
        ],
    }
