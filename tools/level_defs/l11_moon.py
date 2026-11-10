# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, requests, questions): CC BY-NC-SA 4.0
"""Level 11: Glowing moon. Select by Location: within a distance. Placeholder painting."""
import math
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, loc, req, q, circle

FILE = "level11_moon.geojson"
GRID = "level11_moon.grid.json"
KEY = {"S": {"name": "sky", "color": "#172554"}, "H": {"name": "hills", "color": "#1f5f3a"},
       "M": {"name": "moon", "color": "#fff5d6"}, "T": {"name": "star", "color": "#ffffff"}}
STARS = [(3, 3), (7, 9), (11, 2.5), (5, 15), (34, 3), (37, 9), (31, 15.5), (36.5, 19), (2.5, 20), (9, 18),
         (29, 2), (38, 14), (13, 13.5), (27.5, 19.5)]


def painting(px, py, col=0, row=0):
    if circle(px, py, 20, 10, 3.2):
        return "moon"
    if py > 22 + 1.6 * math.sin(px / 4.5):
        return "hills"
    if any(circle(px, py, sx, sy, 0.55) for sx, sy in STARS):
        return "star"
    return "sky"


def build():
    rnd = random.Random(11)
    grid = Grid(40, 32, gem=100)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        use = {"moon": "observatory", "hills": "farm"}.get(region, "conservation")
        if region == "star":
            sky = rnd.choice([21.5, round(rnd.uniform(21.5, 22.0), 2)])
        else:
            sky = rnd.choice([21.49, round(rnd.uniform(18.0, 21.49), 2)])
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "parcel_id": f"DS-{fid:04d}",
            "land_use": use,
            "sky_qual": sky,
            "outdoor_lights": rnd.randint(2, 30) if use == "farm" else rnd.randint(0, 3),
            "owner_type": rnd.choice(["state", "private", "land trust"]),
        })
    write_layer(FILE, grid, records)

    return {
        "number": 11, "title": "Glowing moon", "skill": "Select by Location: within a distance",
        "dataset": "Dark-sky preserve parcels", "table": "darksky",
        "about": "Parcels in and around a dark-sky preserve with an observatory, one polygon per parcel.",
        "file": FILE, "grid": f"art/{GRID}", "location": True, "gem_size": grid.gem, "units": "m", "default_distance": 100,
        "lesson": [
            "<b>Within a distance</b> selects features that are no farther than a set distance from the selected features, like asking “what’s within 300 m of here?”",
            "Distance is measured <b>edge to edge</b>, from the nearest boundary of one feature to the nearest boundary of the other. Neighbors that share a boundary are 0 m apart.",
            "The selected features are within 0 m of themselves, so they’re always included. If you only want the features around them, take the originals out afterward with <b>Remove from the current selection</b>.",
            "Always check the units. In this layer, distances are in meters.",
        ],
        "questions": [
            q("You select the observatory and run <b>Within a distance</b> of 300 m. Is the observatory itself in the result?",
              ["Yes", "No"], 0, "It’s 0 m from itself, which is within 300 m. Remove it afterward if you only want its surroundings.",
              [None, "Distance is measured edge to edge, and a feature is 0 m from itself."]),
            q("How is the distance between two parcels measured here?",
              ["Center to center", "Edge to edge (nearest boundaries)", "Corner to corner", "Along roads"],
              1, "GIS measures the shortest distance between the two shapes, which is between their nearest edges.",
              ["Center to center would be farther for big parcels.", None,
               "It’s the shortest gap between the two shapes, wherever that is.",
               "That would be a network analysis, a different tool."]),
        ],
        "fields": [
            FID,
            {"name": "parcel_id", "type": "TEXT", "about": "Parcel ID"},
            {"name": "land_use", "type": "TEXT", "about": "Current land use"},
            {"name": "sky_qual", "type": "REAL", "about": "Night sky brightness in magnitudes per square arcsecond (higher = darker sky)"},
            {"name": "outdoor_lights", "type": "INTEGER", "about": "Outdoor light fixtures counted in the last survey"},
            {"name": "owner_type", "type": "TEXT", "about": "What kind of owner holds the parcel"},
        ],
        "requests": [
            req("Navy", "#172554", "Every <b>conservation</b> parcel", attr("land_use = 'conservation'")),
            req("Pine", "#1f5f3a", "Every <b>farm</b> parcel", attr("land_use = 'farm'")),
            req("Cream", "#fff5d6", "The <b>observatory</b> parcels", attr("land_use = 'observatory'")),
            req("Pale Gold", "#f6d77a",
                "A lighting ordinance covers every parcel <b>within 300 m</b> of the observatory, <b>not counting</b> the observatory itself.",
                attr("land_use = 'observatory'"), loc("distance", distance=300), attr("land_use = 'observatory'", "remove")),
            req("White", "#ffffff", "Conservation parcels with a sky quality of <b>21.5 or higher</b> (the darkest skies)",
                attr("land_use = 'conservation' AND sky_qual >= 21.5")),
        ],
    }
