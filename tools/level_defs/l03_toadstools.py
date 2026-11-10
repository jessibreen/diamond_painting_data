# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, requests, questions): CC BY-NC-SA 4.0
"""Level 3: Toadstools. AND. Painting from art/level03_toadstools.svg (CC0)."""
import random
from levelkit import Grid, FID, write_layer, load_art_grid, region_grid, attr, req, q

FILE = "level03_toadstools.geojson"
GRID = "level03_toadstools.grid.json"      # made from art/level03_toadstools.svg
KEY = {"S": {"name": "sky", "color": "#a8dcf0"}, "R": {"name": "red cap", "color": "#d62828"},
       "W": {"name": "white spot", "color": "#ffffff"}, "T": {"name": "stem", "color": "#c69c6c"},
       "G": {"name": "grass", "color": "#d9e021"}}


def build():
    rnd = random.Random(3)
    art = load_art_grid(GRID)
    grid = Grid(art["cols"], art["rows"], gem=30)
    regions = region_grid(GRID, grid, KEY)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = {v["name"]: k for k, v in KEY.items()}[regions(col, row)]   # back to the letter
        r = {"fid": fid, "_col": col, "_row": row,
             "plot_id": f"VS-{rnd.randint(100, 999)}-{fid:04d}",
             "survey_yr": rnd.randint(2016, 2024),
             "elev_m": rnd.randint(180, 420)}
        if region == "S":
            r.update(habitat="upland", invasive=rnd.choice("NNNY"), canopy_pct=rnd.randint(0, 95))
        elif region == "R":
            r.update(habitat="forest", invasive="N", canopy_pct=rnd.randint(40, 95))
        elif region == "W":
            r.update(habitat="forest", invasive="Y", canopy_pct=rnd.randint(40, 95))
        elif region == "T":
            r.update(habitat="meadow", invasive=rnd.choice("NY"), canopy_pct=rnd.randint(60, 95))
        else:  # grass
            r.update(habitat="meadow", invasive=rnd.choice("NY"), canopy_pct=rnd.randint(0, 59))
        records.append(r)
    write_layer(FILE, grid, records)

    return {
        "number": 3, "title": "Toadstools", "skill": "AND",
        "dataset": "Vegetation survey plots", "table": "plots",
        "about": "Field survey plots from a vegetation study, one polygon per plot.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "art": {"file": "art/level03_toadstools.svg", "license": "CC0"},
        "lesson": [
            "Sometimes one condition isn’t enough. <b>AND</b> joins two conditions, and a feature is selected only if <b>both</b> are true.",
            "<code>land_use = 'farm' AND acres &gt; 10</code> selects farms bigger than 10 acres. A small farm fails, and so does a big parking lot.",
            "Each condition needs its own field name: write <code>acres &gt; 10 AND acres &lt; 20</code>, not <code>acres &gt; 10 AND &lt; 20</code>.",
            "Requests rarely say “AND.” Listen for two facts about the same feature: “forest plots <i>where</i> invasive species were found.”",
        ],
        "questions": [
            q("Which plots does <code>habitat = 'forest' AND invasive = 'Y'</code> select?",
              ["Every forest plot, plus every plot with invasive species", "Only forest plots that have invasive species",
               "Forest plots without invasive species", "Nothing, because a plot can’t have two values"],
              1, "AND needs both conditions to be true for the same plot.",
              ["That’s what OR would do. AND is stricter.", None,
               "<code>invasive = 'Y'</code> means invasive species <i>were</i> found.",
               "Each condition checks a different field, so one plot can pass both."]),
            q("Which condition finds plots with between 20 and 40 percent canopy (both included)?",
              ["<code>canopy_pct &gt;= 20 AND &lt;= 40</code>", "<code>canopy_pct &gt;= 20 AND canopy_pct &lt;= 40</code>",
               "<code>canopy_pct &gt;= 20 OR canopy_pct &lt;= 40</code>", "<code>canopy_pct = 20 AND canopy_pct = 40</code>"],
              1, "Each side of AND is a complete condition with its own field name.",
              ["The second condition is missing its field name.", None,
               "With OR, every plot passes: every number is either at least 20 or at most 40.",
               "No plot can equal 20 and 40 at the same time."]),
        ],
        "fields": [
            FID,
            {"name": "plot_id", "type": "TEXT", "about": "Survey plot code"},
            {"name": "habitat", "type": "TEXT", "about": "Habitat type of the plot"},
            {"name": "invasive", "type": "TEXT", "about": "Were invasive species found? Y or N"},
            {"name": "canopy_pct", "type": "INTEGER", "about": "Percent of the plot shaded by tree canopy"},
            {"name": "elev_m", "type": "INTEGER", "about": "Elevation of the plot, in meters"},
            {"name": "survey_yr", "type": "INTEGER", "about": "Year the plot was last surveyed"},
        ],
        "requests": [
            req("Powder Blue", "#a8dcf0", "Every <b>upland</b> plot", attr("habitat = 'upland'")),
            req("Scarlet", "#d62828", "<b>Forest</b> plots with <b>no</b> invasive species",
                attr("habitat = 'forest' AND invasive = 'N'")),
            req("White", "#ffffff", "<b>Forest</b> plots where invasive species <b>were found</b>",
                attr("habitat = 'forest' AND invasive = 'Y'")),
            req("Tan", "#c69c6c", "<b>Meadow</b> plots with <b>at least 60%</b> canopy cover",
                attr("habitat = 'meadow' AND canopy_pct >= 60")),
            req("Lime", "#d9e021", "<b>Meadow</b> plots with <b>less than 60%</b> canopy cover",
                attr("habitat = 'meadow' AND canopy_pct < 60")),
        ],
    }
