# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 1: Heart. Equals, text vs. numbers. Doubles as the tour of the site."""
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q

FILE = "level01_heart.geojson"
GRID = "level01_heart.grid.json"
KEY = {"B": {"name": "background", "color": "#f4e4c1"}, "H": {"name": "heart", "color": "#c8102e"},
       "S": {"name": "shine", "color": "#f7a1b5"}}


def painting(px, py, col=0, row=0):
    x = (px - 16) / 9.5
    y = -(py - 13.2) / 9.5 + 0.15
    inside = (x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0
    shine = ((px - 11.3) / 2.2) ** 2 + ((py - 8.6) / 1.4) ** 2 <= 1
    return "shine" if inside and shine else "heart" if inside else "background"


def build():
    rnd = random.Random(1)
    grid = Grid(32, 30, gem=50)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        r = {"fid": fid, "_col": col, "_row": row}
        if region == "shine":
            r.update(land_use="commercial", zip="02139", floors=rnd.choice([4, 5]))
        elif region == "heart":
            r.update(land_use="commercial", zip=rnd.choice(["02134", "02135"]), floors=1)
        else:
            r.update(land_use="residential", zip=rnd.choice(["02134", "02135"]), floors=rnd.choice([2, 3]))
        records.append(r)
    write_layer(FILE, grid, records)

    return {
        "number": 1, "title": "Heart", "skill": "Equals ( = ), text vs. numbers",
        "dataset": "City parcels", "table": "parcels",
        "about": "Property parcels in a small city, one row per parcel.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        # Level 1 doubles as the tour of the site. Each step ticks itself off
        # when the student does the matching action (event); target is the
        # part of the page that glows while the step is current.
        "tutorial": [
            {"event": "identify", "target": "#painting",
             "text": "<b>Click any hex</b> in the painting. Each hex represents a <b>feature</b>, here a property parcel. Its row lights up in the <b>attribute table</b> under the painting, which lists every feature and its fields. Drag the bar above the table to make it bigger or smaller."},
            {"event": "values", "target": ".field[data-field='land_use'] .fvals",
             "text": "Click <b>values</b> next to the <code>land_use</code> field to list every value stored in it. Click a value to drop it into the query box. (Number fields show their range instead.)"},
            {"event": "run", "target": "#run",
             "text": "Read the first query in the color key, <b>Cream</b>. Build <code>land_use = 'residential'</code> by clicking the field name, the <code>=</code> button and the value, or type it. Click <b>Run</b>. The parcels that match turn <b style='color:#00a3b0'>cyan</b>: that’s your selection."},
            {"event": "fill", "target": "#fill-color",
             "text": "In step 2, choose <b>Cream</b> from the gem color menu and click <b>Fill</b>. When every gem for that query is in place, a ✓ appears next to it in the color key."},
            {"event": "complete", "target": None,
             "text": "Now finish <b>Ruby</b> and <b>Blush</b> on your own. Check each field’s type first: <code>floors</code> is a NUMBER, so no quotes. <code>zip</code> looks like a number but is TEXT, so it needs quotes."},
        ],
        "lesson": [
            "Every hex in the painting is a <b>feature</b>, and every feature has <b>attributes</b>: values stored in <b>fields</b>. Together they make the layer’s <b>attribute table</b>.",
            "A query is a yes/no question asked of every feature. The ones that answer <i>yes</i> get <b>selected</b>.",
            "To ask “is this field equal to this value?” write <code>field = value</code>. Numbers are written plain: <code>acres = 12</code>. Text goes inside <b>single quotes</b>: <code>county = 'Kent'</code>.",
            "Look at each field’s <b>type</b>. Codes that look like numbers, like ZIP codes or phone numbers, are stored as <b>TEXT</b> because you never do math with them. A number field would also drop the leading zero in <code>'02134'</code>.",
        ],
        "questions": [
            q("Which query finds parcels where <code>county</code> (a TEXT field) is Kent?",
              ["<code>county = Kent</code>", "<code>county = 'Kent'</code>", "<code>county = \"Kent\"</code>", "<code>'county' = 'Kent'</code>"],
              1, "Text values go in single quotes. The field name doesn’t.",
              ["Without quotes, SQL thinks <code>Kent</code> is the name of a field.", None,
               "Double quotes are for field names, not text values.",
               "Quoting the field name turns it into the text <code>'county'</code>, which never equals <code>'Kent'</code>."]),
            q("A <code>phone</code> field holds values like 6175550142. What type should it be?",
              ["NUMBER", "TEXT"], 1,
              "You never do math with phone numbers, and a number field would drop leading zeros. It’s a code, so it’s text.",
              ["Would you ever add or average phone numbers? And what happens to a leading zero?", None]),
        ],
        "fields": [
            FID,
            {"name": "land_use", "type": "TEXT", "about": "What the parcel is used for"},
            {"name": "zip", "type": "TEXT", "about": "Five-digit ZIP code"},
            {"name": "floors", "type": "INTEGER", "about": "Number of stories in the building on the parcel"},
        ],
        "requests": [
            req("Cream", "#f4e4c1", "Every <b>residential</b> parcel", attr("land_use = 'residential'")),
            req("Ruby", "#c8102e", "Every parcel with a <b>one-story</b> building", attr("floors = 1")),
            req("Blush", "#f7a1b5", "Every parcel in ZIP code <b>02139</b>", attr("zip = '02139'")),
        ],
    }
