# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 9: Flower. Selection types (new, add, remove, subset). Placeholder painting."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q, circle, ellipse, rect

FILE = "level09_flower.geojson"
GRID = "level09_flower.grid.json"
KEY = {"B": {"name": "background", "color": "#cfe9f7"}, "P": {"name": "petal", "color": "#f06292"},
       "C": {"name": "center", "color": "#ffca28"}, "S": {"name": "stem", "color": "#43a047"}}


def painting(px, py, col=0, row=0):
    cx, cy = 20, 10.5
    if circle(px, py, cx, cy, 2.5):
        return "center"
    if any(circle(px, py, cx + 5 * math.cos(math.radians(60 * k + 30)), cy + 5 * math.sin(math.radians(60 * k + 30)), 2.9)
           for k in range(6)):
        return "petal"
    if rect(px, py, 19.4, 20.6, 13, 27.5) or ellipse(px, py, 16.3, 21, 3.3, 1.3) or ellipse(px, py, 23.7, 23.5, 3.3, 1.3):
        return "stem"
    return "background"


def build():
    rnd = random.Random(9)
    grid = Grid(40, 32, gem=300)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        irrigated = rnd.choice("YN")
        if region == "background":
            crop, acres = ("Fallow", round(rnd.uniform(5, 160), 1)) if rnd.random() < 0.7 \
                else ("Hay", rnd.choice([40.0, round(rnd.uniform(5, 40), 1)]))
        elif region == "stem":
            crop, acres = ("Soybeans", round(rnd.uniform(5, 160), 1)) if rnd.random() < 0.7 \
                else ("Hay", round(rnd.uniform(40.1, 160), 1))
        else:
            crop, acres = "Corn", round(rnd.uniform(5, 160), 1)
            irrigated = "Y" if region == "center" else "N"
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "field_id": f"T{rnd.randint(1000, 9999)}-F{fid}",
            "farm_no": f"{rnd.randint(100, 999)}",
            "crop": crop,
            "acres": acres,
            "irrigated": irrigated,
        })
    write_layer(FILE, grid, records)

    return {
        "number": 9, "title": "Flower", "skill": "Selection types",
        "dataset": "Farm fields", "table": "fields",
        "about": "Crop fields reported by farms in one county, one polygon per field.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "So far every query made a <b>new selection</b>. The <b>selection type</b> menu lets a query change the selection you already have instead:",
            "<b>Add to the current selection</b> keeps what’s selected and adds the new matches. <b>Remove from the current selection</b> takes the new matches away. <b>Select subset from the current selection</b> keeps only the selected features that also match.",
            "This is how GIS users build a complicated selection step by step, checking the count after each step. Some of these could be written as a single query with AND, OR and NOT. Try building them in steps instead.",
        ],
        "questions": [
            q("All corn fields are selected. You run <code>irrigated = 'Y'</code> with <b>Remove from the current selection</b>. What’s left?",
              ["Irrigated corn fields", "Corn fields that aren’t irrigated", "Every irrigated field", "Nothing"],
              1, "Remove takes the irrigated fields out of the selection, leaving the rest of the corn.",
              ["That’s what <b>select subset</b> would give you.", None,
               "Remove only works on what’s already selected, and only corn was selected.",
               "Only the irrigated corn is removed."]),
            q("Soybean fields are selected. Which selection type lets you also select the large hay fields?",
              ["New selection", "Add to the current selection", "Remove from the current selection", "Select subset from the current selection"],
              1, "Add keeps the soybeans and puts the hay fields on top.",
              ["A new selection would drop the soybeans.", None,
               "Remove would take hay fields away, and none are selected yet.",
               "Subset keeps only fields that are already selected <i>and</i> match, and no soybean field is a hay field."]),
        ],
        "fields": [
            FID,
            {"name": "field_id", "type": "TEXT", "about": "Tract and field number"},
            {"name": "farm_no", "type": "TEXT", "about": "Farm number"},
            {"name": "crop", "type": "TEXT", "about": "Crop reported this year"},
            {"name": "acres", "type": "REAL", "about": "Field area, in acres"},
            {"name": "irrigated", "type": "TEXT", "about": "Is the field irrigated? Y or N"},
        ],
        "requests": [
            req("Sky Blue", "#cfe9f7", "Every <b>fallow</b> field", attr("crop = 'Fallow'")),
            req("Sky Blue", "#cfe9f7", "<b>Hay</b> fields of <b>40 acres or less</b>",
                attr("crop = 'Hay'"), attr("acres <= 40", "subset")),
            req("Pink", "#f06292", "<b>Corn</b> fields that are <b>not irrigated</b>",
                attr("crop = 'Corn'"), attr("irrigated = 'Y'", "remove")),
            req("Gold", "#ffca28", "<b>Irrigated corn</b> fields",
                attr("crop = 'Corn'"), attr("irrigated = 'Y'", "subset")),
            req("Leaf Green", "#43a047", "Every <b>soybean</b> field, <b>plus</b> hay fields <b>over 40 acres</b>",
                attr("crop = 'Soybeans'"), attr("crop = 'Hay' AND acres > 40", "add")),
        ],
    }
