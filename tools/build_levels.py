# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
#
# The code in this script is licensed GPL-3.0-or-later. The level designs,
# datasets, lesson text, questions and requests in tools/level_defs/ are
# teaching content, licensed CC BY-NC-SA 4.0 (see LICENSE-CONTENT).
"""
Build the level data for Diamond Painting with Data.

Run from the repository root:
    python3 tools/build_levels.py

Writes each level's GeoJSON into levels/ and the level catalogue
levels/levels.json. No third-party packages needed.

Where things live
-----------------
tools/levelkit.py        shared helpers: the hex grid, shapes, writing GeoJSON
tools/level_defs/lNN_*.py one file per level: the painting, the fictional
                          dataset, the lesson, questions and color key
art/                     illustrations and the gem grids made from them

How a level works
-----------------
Each painting is a grid of pointy-top hexagons ("gems"). Each level dresses
the grid up as a fictional dataset (parcels, watersheds, survey plots...),
so every hex is a feature with realistic attributes. The picture only
appears because the attributes were chosen so that the right queries
select the right hexes.

Each level lists its `requests` in order: the gem color, the plain-English
request students read, and the *solution* steps (the queries that select
those hexes). Several requests can share a color. The web app runs the
solutions when a level loads to work out the finished picture (the box
art), so the attributes and the solutions must agree. If you change one,
change the other, then open the level and check the box art.

Every level has an `fid` field (feature ID) as its first field. The app
relies on it.
"""

import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from levelkit import OUT, catalogue_entry  # noqa: E402

# Levels in order. Each entry is a module in tools/level_defs/, or a
# placeholder for a level that isn't built yet.
LEVELS = [
    "l01_heart",
    "l02_sunset",
    "l03_toadstools",
    "l04_rainbow",
    "l05_butterfly",
    "l06_cactus",
    "l07_fish",
    "l08_skyline",
    "l09_flower",
    "l10_cat",
    "l11_moon",
    "l12_pond",
    "l13_balloon",
]


def main():
    os.makedirs(OUT, exist_ok=True)
    entries = []
    for item in LEVELS:
        if isinstance(item, dict):          # placeholder: {"number": .., "title": .., "skill": ..}
            entries.append(catalogue_entry(item))
            continue
        level = importlib.import_module(f"level_defs.{item}").build()
        entries.append(catalogue_entry(level))
        print(f"  level {level['number']:>2}: {level['title']}")
    with open(os.path.join(OUT, "levels.json"), "w") as f:
        json.dump({"levels": entries}, f, indent=1, ensure_ascii=False)
    print(f"Wrote {sum(1 for e in entries if e['available'])} playable levels to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
