# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
# Level content (lesson, data design, color key queries, questions): CC BY-NC-SA 4.0
"""Level 5: Butterfly. Parentheses: mixing AND and OR. Placeholder painting."""
import random
from levelkit import Grid, FID, write_layer, region_grid, attr, req, q, ellipse, circle, near_line

FILE = "level05_butterfly.geojson"
GRID = "level05_butterfly.grid.json"
KEY = {"M": {"name": "background", "color": "#c8f0d8"}, "K": {"name": "body", "color": "#2b2b3a"},
       "U": {"name": "upper", "color": "#7b4fd6"}, "L": {"name": "lower", "color": "#6ec6f0"},
       "u": {"name": "upper_spot", "color": "#ffc93c"}, "l": {"name": "lower_spot", "color": "#ffdf80"}}
FIPS = {"Ashford": "001", "Birch": "003", "Cedar": "005", "Dale": "007"}
SPOTS = [(12, 9, 1.6), (28, 9, 1.6), (15.5, 12.6, 0.9), (24.5, 12.6, 0.9), (14.5, 18.8, 1.1), (25.5, 18.8, 1.1)]


def painting(px, py, col=0, row=0):
    if (abs(px - 20) <= 0.9 and 4.5 <= py <= 23) or near_line(px, py, [(20, 5), (16.5, 1.2)], 0.5) \
            or near_line(px, py, [(20, 5), (23.5, 1.2)], 0.5):
        return "body"
    upper = ellipse(px, py, 13.5, 10, 6.8, 5.6) or ellipse(px, py, 26.5, 10, 6.8, 5.6)
    lower = ellipse(px, py, 15, 18.5, 5, 4.2) or ellipse(px, py, 25, 18.5, 5, 4.2)
    if upper or lower:
        spot = any(circle(px, py, *s) for s in SPOTS)
        return ("upper" if upper else "lower") + ("_spot" if spot else "")
    return "background"


def build():
    rnd = random.Random(5)
    grid = Grid(40, 32, gem=2000)
    regions = region_grid(GRID, grid, KEY, painting)
    records = []
    for fid, col, row, px, py in grid.cells():
        region = regions(col, row)
        wing = region.startswith(("upper", "lower"))
        county = rnd.choice(["Cedar", "Dale"]) if wing else rnd.choice(["Ashford", "Birch"])
        if region == "background":
            pop = rnd.choice([1999, rnd.randint(300, 1999)])
        elif region == "body":
            pop = rnd.choice([2000, rnd.randint(2000, 6500)])
        else:
            pop = rnd.randint(2000, 8500)
        if region.startswith("upper"):
            income = rnd.randint(75001, 150000)
        elif region.startswith("lower"):
            income = rnd.choice([75000, rnd.randint(30000, 75000)])
        else:
            income = rnd.randint(30000, 150000)
        if region.endswith("_spot"):
            renter = round(rnd.uniform(60.1, 95), 1)
        elif wing:
            renter = rnd.choice([60.0, round(rnd.uniform(5, 60), 1)])
        else:
            renter = round(rnd.uniform(5, 95), 1)
        records.append({
            "fid": fid, "_col": col, "_row": row,
            "geoid": f"39{FIPS[county]}{fid:04d}00",
            "county": county,
            "pop_total": pop,
            "med_income": income,
            "pct_renter": renter,
            "median_age": round(rnd.uniform(22, 58), 1),
        })
    write_layer(FILE, grid, records)

    return {
        "number": 5, "title": "Butterfly", "skill": "Parentheses: mixing AND and OR",
        "dataset": "Census tracts", "table": "tracts",
        "about": "Census tracts with a few American Community Survey estimates, one polygon per tract.",
        "file": FILE, "grid": f"art/{GRID}", "location": False, "gem_size": grid.gem, "units": "m",
        "lesson": [
            "When a query mixes AND and OR, SQL does the <b>AND first</b>, the way math does multiplication before addition.",
            "So <code>county = 'Cedar' OR county = 'Dale' AND med_income &gt; 75000</code> really means <code>county = 'Cedar' OR (county = 'Dale' AND med_income &gt; 75000)</code>: every Cedar tract, plus the wealthier Dale tracts.",
            "<b>Parentheses</b> say what goes together: <code>(county = 'Cedar' OR county = 'Dale') AND med_income &gt; 75000</code> means wealthier tracts in either county.",
            "When a query has both AND and OR, use parentheses every time, even when you think you don’t need them.",
        ],
        "questions": [
            q("SQL does AND before OR. Which query means the same as <code>a OR b AND c</code>?",
              ["<code>(a OR b) AND c</code>", "<code>a OR (b AND c)</code>"], 1,
              "AND binds tighter, so <code>b AND c</code> is grouped first.",
              ["That’s what you usually <i>want</i>, which is why you need to write the parentheses.", None]),
            q("Which query selects tracts in Cedar <b>or</b> Dale County with more than 50% renters?",
              ["<code>county = 'Cedar' OR county = 'Dale' AND pct_renter &gt; 50</code>",
               "<code>(county = 'Cedar' OR county = 'Dale') AND pct_renter &gt; 50</code>",
               "<code>county = 'Cedar' OR (county = 'Dale' AND pct_renter &gt; 50)</code>",
               "<code>(county = 'Cedar' AND county = 'Dale') OR pct_renter &gt; 50</code>"],
              1, "The parentheses keep the two counties together, and the renter test applies to both.",
              ["Without parentheses, every Cedar tract is selected, renters or not.", None,
               "This is how SQL reads the first option: all of Cedar, plus Dale tracts with many renters.",
               "A tract can’t be in two counties at once."]),
        ],
        "fields": [
            FID,
            {"name": "geoid", "type": "TEXT", "about": "11-digit census tract ID (state + county + tract)"},
            {"name": "county", "type": "TEXT", "about": "County name"},
            {"name": "pop_total", "type": "INTEGER", "about": "Total population"},
            {"name": "med_income", "type": "INTEGER", "about": "Median household income, in dollars"},
            {"name": "pct_renter", "type": "REAL", "about": "Percent of occupied homes that are rented"},
            {"name": "median_age", "type": "REAL", "about": "Median age of residents"},
        ],
        "requests": [
            req("Mint", "#c8f0d8", "Tracts with <b>fewer than 2,000</b> residents", attr("pop_total < 2000")),
            req("Violet", "#7b4fd6", "Tracts in <b>Cedar or Dale</b> County with a median household income <b>over $75,000</b>",
                attr("(county = 'Cedar' OR county = 'Dale') AND med_income > 75000")),
            req("Sky", "#6ec6f0", "Tracts in <b>Cedar or Dale</b> County with a median household income of <b>$75,000 or less</b>",
                attr("(county = 'Cedar' OR county = 'Dale') AND med_income <= 75000")),
            req("Gold", "#ffc93c", "Tracts in <b>Cedar or Dale</b> County where <b>more than 60%</b> of homes are rented",
                attr("(county = 'Cedar' OR county = 'Dale') AND pct_renter > 60")),
            req("Charcoal", "#2b2b3a", "Tracts in <b>Ashford or Birch</b> County with <b>2,000 or more</b> residents",
                attr("(county = 'Ashford' OR county = 'Birch') AND pop_total >= 2000")),
        ],
    }
