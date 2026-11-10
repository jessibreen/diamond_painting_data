# Diamond Painting with Data

> **🚧 Work in progress.** This tool is still being built and tested. Levels,
> datasets and features will change, some levels are not written yet, and
> things may break. It's shared here to collect feedback, so please open an
> issue with anything you notice.

**Paintings:** Level 3 uses a CC0 illustration (see `art/`). The other
paintings are simple placeholders drawn in code, to be replaced with nicer
illustrations.

**Devices:** designed for laptops, desktops and tablets (portrait or
landscape). It runs on phones, but the screen is small for this kind of work,
so phones are best-effort.

A web tool for teaching GIS queries with diamond painting. Every hex in the
painting is a polygon feature with attributes. Students read a plain-English
color key, write the query that selects those hexes, and fill the selection
with that color. When every query is right, the picture appears.

It runs entirely in the browser (no server, no build step), so it can be
hosted on GitHub Pages as-is.

## Try it on your computer

Browsers block the database engine when a page is opened straight from a
file, so start a small local web server from this folder:

```
python3 tools/serve.py
```

Then open <http://localhost:8000>. This server also rebuilds the levels
automatically whenever a painting or level file changes, so edits show up
when you reload. (`python3 -m http.server 8000` works too, but then you have
to run `python3 tools/build_levels.py` yourself after every change.) Add `#3` to the address to jump to a level
(for example `http://localhost:8000/#10`).

## Put it on GitHub Pages

1. Create a repository and push the contents of this folder to it.
2. In the repository go to **Settings → Pages**, choose **Deploy from a branch**,
   pick `main` and `/ (root)`, and save.
3. After a minute the site is live at `https://<your-username>.github.io/<repo-name>/`.

## What's in the folder

| Path | What it does |
|---|---|
| `index.html` | The page layout |
| `css/style.css` | All the styling |
| `js/app.js` | Main app: levels, color key, history, fill, undo, check my work |
| `js/engine.js` | Select by Attributes: runs WHERE clauses in SQLite and turns errors into plain-English messages |
| `js/spatial.js` | Select by Location (intersect, boundary touches, within a distance, completely within, completely contain, center in) and the four selection types |
| `js/render.js` | Draws the painting on a canvas |
| `js/table.js` | The attribute table under the painting (sorting, all/selected, resizing) |
| `vendor/` | [sql.js](https://github.com/sql-js/sql.js) 1.16 (SQLite compiled for the browser), MIT licensed |
| `levels/levels.json` | The level list: lessons, questions, fields, color key requests and solutions (generated) |
| `levels/*.geojson` | One file per painting: hex polygons and their attributes, plus extra layers for Level 12 (generated) |
| `tools/build_levels.py` | Builds everything in `levels/`. Run this after changing a level |
| `tools/levelkit.py` | Shared helpers: the hex grid, shapes, writing GeoJSON |
| `tools/level_defs/` | One Python file per level: its painting, fictional dataset, lesson, questions and color key |
| `art/` | Each level's picture as an editable gem grid (`*.grid.json`), plus source illustrations |
| `tools/editor.html` | Painting editor: repaint a level's gems by region |
| `tools/serve.py` | Local web server that rebuilds the levels automatically when paintings change |

## How a level works

Each level dresses the hex grid up as a different fictional vector dataset
(parcels, sub-watersheds, survey plots...). In `levels.json` a level has a
`dataset` name, a `table` name (what students see in `SELECT * FROM ... WHERE`),
a one-line `about`, and its `fields`. Every level keeps an `fid` field
(feature ID), which the app uses to match query results to hexes.

Each level has a list of `colors` and an ordered list of `requests`. A
request has:

- `color`: which gem color it is filled with (several requests can share one)
- `rule`: the plain-English request students see
- `solution`: the steps that select the right hexes, for example
  `{"type": "attribute", "where": "habitat = 'forest' AND invasive = 'Y'", "method": "new"}`
  or `{"type": "location", "relation": "touches", "method": "new"}`

In `tools/build_levels.py` you just write each request with its color name
and hex code, and the script builds the color list for you.

### Lessons and comprehension questions

Each level opens on its lesson screen (the `lesson` paragraphs plus a short
description of the dataset). Students click **Start the painting** to get to
the color key and query tools, and can go back with **← Lesson**.

A level can also have `questions`, multiple-choice checks shown under the
lesson. Each has `question`, `options`, `answer` (the index of the right
option), `explain` (shown when they get it right) and `hints` (one per option,
shown when they pick that wrong answer). Students must answer every question correctly
before the Start button unlocks, unless the level sets
`"questions_required": false`. Level 2 has examples.

When a level loads, the app runs every request's solution in order to work out the
finished picture (the box art). So the solutions are the answer key, and if
the box art looks right, the level is solvable. Later colors cover earlier
ones, the same way they do when students paint.

To change a level, edit its file in `tools/level_defs/`. To add one, copy an
existing level file, give it a new number and add it to the `LEVELS` list in
`tools/build_levels.py`. Then run this from the repo folder:

```
python3 tools/build_levels.py
```

If a solution selects nothing, or some hexes are never painted, a warning
appears in the browser's developer console.

### Editing a painting

Each level's picture is stored in `art/` as a grid of region letters
(for example `sky`, `cactus`, `flower`). The level's file in
`tools/level_defs/` gives each region attribute values that the color key's
queries pick out, so you can reshape the picture freely without touching
the data code.

1. Start the local server from the repo folder (`python3 tools/serve.py`)
   and open <http://localhost:8000/tools/editor.html>.
2. Pick a level, click a region, and paint with the brush, fill or pick
   tools. The **Check** box warns if a region has no gems left.
3. Click **Save**. In Chrome or Edge you can save straight over the file in
   `art/`; other browsers download it, and you move it into `art/`.
4. Reload the game. `tools/serve.py` rebuilds the levels for you; with any
   other server, run `python3 tools/build_levels.py` first. The game reads
   the built files in `levels/`, not the paintings in `art/`.

The editor changes which gems belong to which region. It doesn't add new
regions or change the grid size; those need a change to the level's file.

Note: the solutions sit in `levels.json`, so a student who opens the browser's
developer tools can find them. That's fine for practice but worth knowing if
you ever use it for grades.

## Things to know about the SQL

- It's SQLite. Text goes in single quotes (`'sky'`). Double quotes are only
  for field names. SQLite normally lets `"sky"` slide as text when no field has
  that name. The tool blocks that and explains why, so students learn the rule
  that holds everywhere.
- In SQLite, `LIKE` ignores capital letters. Many other databases don't.
- The tool catches common beginner mistakes before running the query:
  curly quotes, `= 'a' OR 'b'`, `AND < 9` with no field name, `= NULL`,
  quotes around numbers, `==`, unbalanced quotes and parentheses, and
  misspelled field names.

## Units

Coordinates are in millimetres on a flat canvas (one gem is 2.5 mm across),
so there's no map projection. Distances are measured edge to edge, as in
ArcGIS and QGIS.

## License

Copyright © 2026 Jessica Breen.

This project uses two licenses: one for the code and one for the teaching
materials.

**Code: [GNU General Public License v3.0 or later](LICENSE) (GPL-3.0-or-later).**
The app itself: `index.html`, `css/`, `js/`, and the code in `tools/`. It's
open source: you're free to use, study, change and share it. If you
distribute a modified version, you must share its source code under the same
license.

**Teaching materials: [CC BY-NC-SA 4.0](LICENSE-CONTENT)**
([Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/)).
The levels and datasets in `levels/`, and the lesson text, comprehension
questions, color-key requests and painting designs (including where they're
written inside `tools/build_levels.py`). You can share and adapt them for
non-commercial purposes if you give credit and share your version under the
same license. Please credit them as:

> *Diamond Painting with Data* by Jessica Breen, licensed under
> [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Bundled third-party code keeps its own license:
[sql.js](https://github.com/sql-js/sql.js) in `vendor/` is MIT licensed
(`vendor/sql.js-LICENSE`), which is compatible with the GPL.
