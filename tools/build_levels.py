# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
#
# The code in this script is licensed GPL-3.0-or-later. The level designs, datasets,
# lesson text, questions and requests it contains are teaching content,
# licensed CC BY-NC-SA 4.0 (see LICENSE-CONTENT).
"""
Build the level data for Diamond Painting with Data.

Run from the repository root:
    python3 tools/build_levels.py

Writes one GeoJSON file per painting into levels/ and the level catalogue
levels/levels.json. No third-party packages needed.

How a painting is defined
-------------------------
Each painting is a grid of pointy-top hexagons ("gems"). Each level dresses
the grid up as a different fictional dataset (parcels, weather stations,
survey plots...), so every hex is a feature with realistic attributes.
The picture only appears because the attributes were chosen so that the
right queries select the right hexes.

In this file each level lists its `requests` in order: the gem color, the
plain-English request students read, and the *solution* steps (the
queries that select those hexes). Several requests can share a color.
build turns this into a `colors` list plus `requests` that point at it. The web app runs the solutions when a level loads to work
out the finished picture, so the attributes and the solutions must agree.
If you change one, change the other, then open the level and check the
box art.

Every level also has an `fid` field (feature ID). The app relies on it,
so keep it as the first field.
"""

import json
import math
import os
import random

COLS = 32
ROWS = 30
GEM = 2.5                     # flat-to-flat width of a hex, in mm
R = GEM / math.sqrt(3)        # hex radius (center to corner)
ROW_STEP = 1.5 * R            # vertical distance between row centers

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "levels")

FID = {"name": "fid", "type": "INTEGER", "about": "Feature ID: a unique number the GIS assigns to each feature"}


# ---------------------------------------------------------------- geometry
def hex_center(col, row):
    """Map position in mm. Row 0 is the top row; y grows upward (as in GIS)."""
    x = GEM / 2 + col * GEM + (GEM / 2 if row % 2 else 0)
    y = R + (ROWS - 1 - row) * ROW_STEP
    return x, y


def hex_ring(cx, cy):
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 30)          # pointy-top
        pts.append([round(cx + R * math.cos(a), 4), round(cy + R * math.sin(a), 4)])
    pts.append(pts[0])
    return [pts]


def cells():
    """Yield (fid, col, row, px, py). px/py are 'picture units':
    px = 0..32 left to right, py = 0..~26 top to bottom (1 unit = 1 gem)."""
    for row in range(ROWS):
        for col in range(COLS):
            px = col + 0.5 + (0.5 if row % 2 else 0)
            py = row * 0.866 + 0.5
            yield row * COLS + col + 1, col, row, px, py


def write_geojson(filename, rows):
    feats = []
    for r in rows:
        cx, cy = hex_center(r.pop("_col"), r.pop("_row"))
        feats.append({
            "type": "Feature",
            "properties": r,
            "geometry": {"type": "Polygon", "coordinates": hex_ring(cx, cy)},
        })
    fc = {"type": "FeatureCollection", "name": filename.replace(".geojson", ""),
          "features": feats}
    with open(os.path.join(OUT, filename), "w") as f:
        json.dump(fc, f, separators=(",", ":"))


def base(fid, col, row):
    return {"fid": fid, "_col": col, "_row": row}


def seg_dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
    return math.hypot(px - (ax + t * (bx - ax)), py - (ay + t * (by - ay)))


# ---------------------------------------------------------------- level 1: city parcels
def level_heart():
    rnd = random.Random(1)
    rows = []
    for fid, col, row, px, py in cells():
        x = (px - 16) / 9.5
        y = -(py - 13.2) / 9.5 + 0.15
        inside = (x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0
        shine = ((px - 11.3) / 2.2) ** 2 + ((py - 8.6) / 1.4) ** 2 <= 1
        r = base(fid, col, row)
        if inside and shine:
            r.update(land_use="commercial", zip="02139", floors=rnd.choice([4, 5]))
        elif inside:
            r.update(land_use="commercial", zip=rnd.choice(["02134", "02135"]), floors=1)
        else:
            r.update(land_use="residential", zip=rnd.choice(["02134", "02135"]), floors=rnd.choice([2, 3]))
        rows.append(r)
    write_geojson("level01_heart.geojson", rows)


# ---------------------------------------------------------------- level 2: sub-watersheds
# Elevation (m) by row. The rows that sit exactly on a threshold (850, 620,
# 400) are what make > and >= give different answers.
SKY_ELEV = [99, 95, 92, 88, 85, 84, 80, 77, 73, 70, 66, 62, 59, 55, 52, 48, 45, 41]
SEA_ELEV = [40, 37, 33, 30, 26, 22, 19, 15, 11, 8, 4, 0]
EXACT = {85, 62, 40}


def level_sunset():
    rnd = random.Random(2)
    rows = []
    horizon = len(SKY_ELEV)              # first "valley" row
    sun_x, sun_y, sun_r = 16.0, (horizon - 0.2) * 0.866, 6.2
    for fid, col, row, px, py in cells():
        r = base(fid, col, row)
        d = math.hypot(px - sun_x, py - sun_y)
        fog = 0
        if row < horizon:
            band = SKY_ELEV[row]
            if d <= sun_r - 0.9:
                bright = min(100, 91 + int((sun_r - d) * 1.5))
            elif d <= sun_r:
                bright = 90                     # rim: catches > vs >=
            elif d <= sun_r + 1.0:
                bright = 89
            else:
                bright = max(35, int(88 - (d - sun_r) * 4))
        else:
            band = SEA_ELEV[row - horizon]
            bright = rnd.randint(10, 45)
            width = 4.5 - (row - horizon) * 0.25
            if abs(px - sun_x) <= width and (row + col) % 2 == 0 and rnd.random() < 0.75:
                fog = rnd.randint(4, 40)
        elev = band * 10 + (0 if band in EXACT else rnd.randint(0, 9))
        solar = 1000 + bright * 10 + (0 if bright in (89, 90) else rnd.randint(0, 9))
        r.update(
            huc12=f"0105000{row:02d}{col:03d}",
            mean_elev_m=elev,
            solar_kwh=solar,
            fog_days=fog,
            precip_mm=rnd.randint(600, 1800),
            area_km2=round(rnd.uniform(18, 95), 1),
        )
        rows.append(r)
    write_geojson("level02_sunset.geojson", rows)


# ---------------------------------------------------------------- level 3: vegetation survey plots
def level_mushroom():
    rnd = random.Random(3)
    rows = []
    ground_row = 24
    spots = [(10.5, 7.4, 1.6), (16.5, 4.6, 1.8), (22.0, 8.2, 1.5), (13.0, 10.6, 1.2), (19.8, 11.0, 1.1)]
    flowers = [(3, 26), (7, 28), (10, 25), (24, 26), (27, 28), (29, 25), (5, 25), (21, 28)]
    for fid, col, row, px, py in cells():
        r = base(fid, col, row)
        height = ROWS - 1 - row                 # 0 at the bottom row
        cap = ((px - 16) / 12.5) ** 2 + ((py - 13.3) / 10.5) ** 2 <= 1 and row <= 15
        stem = abs(px - 16) <= 3.6 and 15 < row < ground_row + 1
        invasive = "N"
        if cap:
            habitat = "forest"
            if any(math.hypot(px - sx, py - sy) <= sr for sx, sy, sr in spots) and row <= 13:
                invasive = "Y"
        elif stem:
            habitat = "wetland"
        elif row >= ground_row:
            habitat = "meadow"
            if (col, row) in flowers:
                invasive = "Y"
        else:
            habitat = "upland"
        r.update(
            plot_id=f"VS-{rnd.randint(100, 999)}-{fid:03d}",
            habitat=habitat,
            invasive=invasive,
            elev_m=100 + height * 5,
            canopy_pct=rnd.randint(0, 95),
            survey_yr=rnd.randint(2016, 2024),
        )
        rows.append(r)
    write_geojson("level03_mushroom.geojson", rows)


# ---------------------------------------------------------------- level 10: land ownership
def level_cat():
    rnd = random.Random(10)
    rows = []
    tail_pts = [(21.5, 21.5), (25.0, 20.8), (27.2, 18.5), (27.8, 15.5), (27.0, 12.8)]
    for fid, col, row, px, py in cells():
        r = base(fid, col, row)
        head = ((px - 13.5) / 6.3) ** 2 + ((py - 9.0) / 5.4) ** 2 <= 1

        def ear(cx):
            top = 1.6
            return top <= py <= 6.0 and abs(px - cx) <= (py - top) * 0.7
        ears = ear(9.6) or ear(17.4)
        body = ((px - 15.0) / 8.0) ** 2 + ((py - 18.6) / 6.2) ** 2 <= 1
        tail = min(seg_dist(px, py, tail_pts[i], tail_pts[i + 1]) for i in range(len(tail_pts) - 1)) <= 0.95
        eye = (math.hypot(px - 11.0, py - 8.3) <= 1.0) or (math.hypot(px - 16.0, py - 8.3) <= 1.0)
        nose = abs(px - 13.5) <= 0.6 and abs(py - 10.9) <= 0.5
        if eye:
            owner = "water district"
        elif nose:
            owner = "land trust"
        elif head or body or ears or tail:
            owner = "state forest"
        else:
            owner = "private"
        r.update(
            parcel_id=f"{rnd.randint(10, 48):03d}-{fid:04d}",
            owner_type=owner,
            acres=round(rnd.uniform(2, 160), 1),
            zoning=rnd.choice(["RR", "RR", "AG", "CON"]) if owner != "private" or rnd.random() < 0.8 else "R1",
            deed_yr=rnd.randint(1948, 2024),
        )
        rows.append(r)
    write_geojson("level10_cat.geojson", rows)


# ---------------------------------------------------------------- catalogue
def attr(where, method="new"):
    return {"type": "attribute", "where": where, "method": method}


def loc(relation, method="new", distance=None):
    s = {"type": "location", "relation": relation, "method": method}
    if distance is not None:
        s["distance"] = distance
    return s


LEVELS = [
    {
        "number": 1, "title": "Heart", "skill": "Equals ( = ), text vs. numbers",
        "dataset": "City parcels", "table": "parcels",
        "about": "Property parcels in a small city, one row per parcel.",
        "file": "level01_heart.geojson", "location": False,
        # Level 1 doubles as the tour of the site. Each step ticks itself off
        # when the student does the matching action (event); target is the
        # part of the page that glows while the step is current.
        "tutorial": [
            {"event": "identify", "target": "#painting",
             "text": "<b>Click any hex</b> in the painting. Each hex represents a <b>feature</b>, here a property parcel. Its row lights up in the <b>attribute table</b> under the painting, which lists every feature and its fields. Drag the bar above the table to make it bigger or smaller."},
            {"event": "values", "target": ".field[data-field='land_use'] .fvals",
             "text": "Click <b>values</b> next to the <code>land_use</code> field to list every value stored in it. Click a value to drop it into the query box. (Number fields show their range instead.)"},
            {"event": "run", "target": "#run",
             "text": "Read the first request in the color key, <b>Cream</b>. Build <code>land_use = 'residential'</code> by clicking the field name, the <code>=</code> button and the value, or type it. Click <b>Run</b>. The parcels that match turn <b style='color:#00a3b0'>cyan</b>: that’s your selection."},
            {"event": "fill", "target": "#fill-color",
             "text": "In step 2, choose <b>Cream</b> from the gem color menu and click <b>Fill</b>. When every gem for that request is in place, a ✓ appears next to it in the color key."},
            {"event": "complete", "target": None,
             "text": "Now finish <b>Ruby</b> and <b>Blush</b> on your own. Check each field’s type first: <code>floors</code> is a NUMBER, so no quotes. <code>zip</code> looks like a number but is TEXT, so it needs quotes."},
        ],
        "lesson": [
            "Every hex in the painting is a <b>feature</b>, and every feature has <b>attributes</b>: values stored in <b>fields</b>. Together they make the layer’s <b>attribute table</b>.",
            "A query is a yes/no question asked of every feature. The ones that answer <i>yes</i> get <b>selected</b>.",
            "To ask “is this field equal to this value?” write <code>field = value</code>. Numbers are written plain: <code>acres = 12</code>. Text goes inside <b>single quotes</b>: <code>county = 'Kent'</code>.",
            "Look at each field’s <b>type</b>. Codes that look like numbers, like ZIP codes or phone numbers, are stored as <b>TEXT</b> because you never do math with them. A number field would also drop the leading zero in <code>'02134'</code>.",
        ],
        "fields": [
            FID,
            {"name": "land_use", "type": "TEXT", "about": "What the parcel is used for"},
            {"name": "zip", "type": "TEXT", "about": "Five-digit ZIP code"},
            {"name": "floors", "type": "INTEGER", "about": "Number of stories in the building on the parcel"},
        ],
        "requests": [
            {"name": "Cream", "color": "#f4e4c1",
             "rule": "Every <b>residential</b> parcel",
             "solution": [attr("land_use = 'residential'")]},
            {"name": "Ruby", "color": "#c8102e",
             "rule": "Every parcel with a <b>one-story</b> building",
             "solution": [attr("floors = 1")]},
            {"name": "Blush", "color": "#f7a1b5",
             "rule": "Every parcel in ZIP code <b>02139</b>",
             "solution": [attr("zip = '02139'")]},
        ],
    },
    {
        "number": 2, "title": "Sunset", "skill": "Comparisons ( >, <, >=, <=, <> )",
        # Optional comprehension questions shown under the lesson. "answer" is the
        # index of the right option; "hints" (one per option, None for the right
        # one) explain each wrong answer. Students must answer every question
        # correctly before they can start; add "questions_required": False to
        # the level to make them optional.
        "questions": [
            {"question": "A request asks for watersheds with a mean elevation of <b>at least</b> 850 m. Which condition matches?",
             "options": ["<code>mean_elev_m &gt; 850</code>", "<code>mean_elev_m &gt;= 850</code>",
                         "<code>mean_elev_m &lt;= 850</code>", "<code>mean_elev_m = 850</code>"],
             "answer": 1,
             "explain": "“At least” includes 850 itself, so use <code>&gt;=</code>.",
             "hints": ["<code>&gt;</code> leaves out a watershed at exactly 850 m.", None,
                       "<code>&lt;=</code> picks 850 and everything <i>below</i> it.",
                       "<code>=</code> only picks watersheds at exactly 850 m."]},
            {"question": "Which condition is written correctly?",
             "options": ["<code>pop =&gt; 5000</code>", "<code>pop &gt;= 5,000</code>",
                         "<code>pop &gt;= 5000</code>", "<code>pop &gt;= '5000'</code>"],
             "answer": 2,
             "explain": "The <code>&gt;</code> comes before the <code>=</code>, and the number has no comma or quotes.",
             "hints": ["SQL writes it <code>&gt;=</code>, with the <code>&gt;</code> first.",
                       "Leave the comma out of numbers.", None,
                       "<code>pop</code> is a number, so its values don’t get quotes."]},
            {"question": "Which watersheds does <code>mean_elev_m &lt;&gt; 400</code> select?",
             "options": ["Only watersheds at exactly 400 m", "Every watershed except those at exactly 400 m",
                         "Watersheds below 400 m", "Watersheds above 400 m"],
             "answer": 1,
             "explain": "<code>&lt;&gt;</code> means “not equal to,” so it keeps everything above <i>and</i> below 400 m.",
             "hints": ["That would be <code>= 400</code>.", None,
                       "<code>&lt;&gt;</code> isn’t “less than”: it means “not equal to.” What about watersheds above 400 m?",
                       "<code>&lt;&gt;</code> isn’t “greater than”: it means “not equal to.” What about watersheds below 400 m?"]},
        ],
        "dataset": "Mountain sub-watersheds", "table": "watersheds",
        "about": "Small watersheds across a mountain range, one polygon per watershed.",
        "file": "level02_sunset.geojson", "location": False,
        "lesson": [
            "Not every question is “equals.” Numbers can be compared: <code>&gt;</code> greater than, <code>&lt;</code> less than, <code>&gt;=</code> greater than or equal to, <code>&lt;=</code> less than or equal to, and <code>&lt;&gt;</code> not equal to.",
            "Watch the edges! <code>pop &gt; 5000</code> leaves out a town of exactly 5000. <code>pop &gt;= 5000</code> includes it. Requests say this in words: “more than,” “at least,” “or higher,” “or less.”",
            "Leave commas out of numbers: write <code>1900</code>, not <code>1,900</code>.",
            "This table has more fields than you need. Part of the job is figuring out which field answers each request.",
            "Filling a hex replaces any color already there, like pressing a new gem on top. Work down the color key in order. Some colors are used for more than one request.",
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
            {"name": "Tangerine", "color": "#f6872b",
             "rule": "Watersheds with a mean elevation <b>above 400 m</b>",
             "solution": [attr("mean_elev_m > 400")]},
            {"name": "Rose", "color": "#e0457b",
             "rule": "Watersheds with a mean elevation <b>above 620 m</b>",
             "solution": [attr("mean_elev_m > 620")]},
            {"name": "Plum", "color": "#5b2a6e",
             "rule": "Watersheds with a mean elevation of <b>850 m or higher</b>",
             "solution": [attr("mean_elev_m >= 850")]},
            {"name": "Gold", "color": "#ffd23f",
             "rule": "Watersheds that receive <b>at least 1,900 kWh/m²</b> of sunlight a year",
             "solution": [attr("solar_kwh >= 1900")]},
            {"name": "Navy", "color": "#1d2f5e",
             "rule": "Watersheds with a mean elevation of <b>400 m or lower</b>",
             "solution": [attr("mean_elev_m <= 400")]},
            {"name": "Tangerine", "color": "#f6872b",
             "rule": "Watersheds that recorded <b>any</b> fog days last year",
             "solution": [attr("fog_days <> 0")]},
        ],
    },
    {
        "number": 3, "title": "Mushroom", "skill": "AND",
        "dataset": "Vegetation survey plots", "table": "plots",
        "about": "Field survey plots from a vegetation study, one row per plot.",
        "file": "level03_mushroom.geojson", "location": False,
        "lesson": [
            "Sometimes one condition isn’t enough. <b>AND</b> joins two conditions, and a feature is selected only if <b>both</b> are true.",
            "<code>land_use = 'farm' AND acres &gt; 10</code> selects farms bigger than 10 acres. A small farm fails, and so does a big parking lot.",
            "Each condition needs its own field name: write <code>acres &gt; 10 AND acres &lt; 20</code>, not <code>acres &gt; 10 AND &lt; 20</code>.",
            "Requests rarely say “AND.” Listen for two facts about the same feature: “forest plots <i>where</i> invasive species were found.”",
        ],
        "fields": [
            FID,
            {"name": "plot_id", "type": "TEXT", "about": "Survey plot code"},
            {"name": "habitat", "type": "TEXT", "about": "Habitat type of the plot"},
            {"name": "invasive", "type": "TEXT", "about": "Were invasive species found? Y or N"},
            {"name": "elev_m", "type": "INTEGER", "about": "Elevation of the plot, in meters"},
            {"name": "canopy_pct", "type": "INTEGER", "about": "Percent of the plot shaded by tree canopy"},
            {"name": "survey_yr", "type": "INTEGER", "about": "Year the plot was last surveyed"},
        ],
        "requests": [
            {"name": "Powder Blue", "color": "#a8dcf0",
             "rule": "Every <b>upland</b> plot",
             "solution": [attr("habitat = 'upland'")]},
            {"name": "Moss Green", "color": "#4f9a3a",
             "rule": "<b>Meadow</b> plots with <b>no</b> invasive species",
             "solution": [attr("habitat = 'meadow' AND invasive = 'N'")]},
            {"name": "White", "color": "#ffffff",
             "rule": "<b>Meadow</b> plots where invasive species <b>were found</b>",
             "solution": [attr("habitat = 'meadow' AND invasive = 'Y'")]},
            {"name": "Ivory", "color": "#f3ead3",
             "rule": "Every <b>wetland</b> plot",
             "solution": [attr("habitat = 'wetland'")]},
            {"name": "Scarlet", "color": "#d62828",
             "rule": "<b>Forest</b> plots with <b>no</b> invasive species",
             "solution": [attr("habitat = 'forest' AND invasive = 'N'")]},
            {"name": "White", "color": "#ffffff",
             "rule": "<b>Forest</b> plots where invasive species <b>were found</b>",
             "solution": [attr("habitat = 'forest' AND invasive = 'Y'")]},
            {"name": "Tan", "color": "#c9a27e",
             "rule": "<b>Forest</b> plots at <b>170 m elevation or lower</b>",
             "solution": [attr("habitat = 'forest' AND elev_m <= 170")]},
        ],
    },
    {"number": 4, "title": "Rainbow", "skill": "OR (and the “= 'a' OR 'b'” trap)"},
    {"number": 5, "title": "Butterfly", "skill": "Parentheses: mixing AND and OR"},
    {"number": 6, "title": "Cactus", "skill": "NOT, IN, BETWEEN"},
    {"number": 7, "title": "Fish", "skill": "LIKE and wildcards"},
    {"number": 8, "title": "Night sky", "skill": "NULL (the “= NULL” trap)"},
    {"number": 9, "title": "Hollow flower", "skill": "Selection methods"},
    {
        "number": 10, "title": "Outlined cat", "skill": "Select by Location: touches & intersects",
        "dataset": "Land ownership around Pine Ridge State Forest", "table": "ownership",
        "about": "Land parcels in and around a state forest, one polygon per parcel.",
        "file": "level10_cat.geojson", "location": True,
        "lesson": [
            "Attribute queries ask about a feature’s <b>values</b>. <b>Select by Location</b> asks where a feature is <b>in relation to other features</b>.",
            "Here the parcels are compared with the parcels you’ve <b>already selected</b>. <b>Boundary touches</b> picks parcels whose boundaries touch a selected parcel. <b>Intersect</b> picks parcels that share any area or boundary, so it also picks the selected parcels themselves.",
            "Combine tools with the <b>selection type</b>: <i>new</i> replaces the selection, <i>add to</i> adds, <i>remove from</i> takes away, and <i>select subset</i> keeps only the parcels that pass the new test too.",
            "Nothing in the attribute table says which parcels are next to the forest. Some questions can only be answered by location!",
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
            {"name": "Lavender", "color": "#d9cdf0",
             "rule": "Every <b>privately owned</b> parcel",
             "solution": [attr("owner_type = 'private'")]},
            {"name": "Orange", "color": "#f28c28",
             "rule": "Every parcel in the <b>state forest</b>",
             "solution": [attr("owner_type = 'state forest'")]},
            {"name": "Emerald", "color": "#2e9e5b",
             "rule": "Parcels owned by the <b>water district</b>",
             "solution": [attr("owner_type = 'water district'")]},
            {"name": "Pink", "color": "#ff8fab",
             "rule": "The <b>land trust</b> parcel",
             "solution": [attr("owner_type = 'land trust'")]},
            {"name": "Black", "color": "#1b1b2f",
             "rule": "A timber harvest is planned. Every <b>private</b> parcel that <b>shares a boundary</b> with the <b>state forest</b> must be notified. (No field says who borders the forest. Select the forest first, then use Select by Location.)",
             "solution": [attr("owner_type = 'state forest'"), loc("touches"), attr("owner_type = 'private'", "subset")]},
        ],
    },
    {"number": 11, "title": "Glowing moon", "skill": "Within a distance"},
    {"number": 12, "title": "Pond and vine", "skill": "Reference layers: within, contains, crossed by"},
    {"number": 13, "title": "Capstone", "skill": "Everything"},
]


def catalogue_entry(lv):
    """Split the requests into a color list and requests that point at it."""
    out = dict(lv, available="file" in lv)
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


def main():
    os.makedirs(OUT, exist_ok=True)
    level_heart()
    level_sunset()
    level_mushroom()
    level_cat()
    catalogue = {
        "units": "mm",
        "gem_size": GEM,
        "levels": [catalogue_entry(lv) for lv in LEVELS],
    }
    with open(os.path.join(OUT, "levels.json"), "w") as f:
        json.dump(catalogue, f, indent=1, ensure_ascii=False)
    print("Wrote", len([l for l in LEVELS if "file" in l]), "playable levels to", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
