# Art

Each level's picture lives here as a gem grid, plus any source illustrations.

| File | What it is | License |
|---|---|---|
| `level03_toadstools.svg` | Toadstools illustration for Level 3 | CC0 |
| `level03_toadstools.grid.json` | That illustration converted to a 56 × 39 grid of gems | CC0 |
| `levelNN_*.grid.json` (others) | Placeholder paintings, first drawn in code | CC BY-NC-SA 4.0 |

## Grid files

A `.grid.json` file has the grid size (`cols`, `rows`), a `key` naming each
region letter with a preview color, and `grid`: one string per row of gems,
one letter per gem. Odd rows sit half a gem to the right.

Edit them with the painting editor (`tools/editor.html`; see the main
README). The key is owned by the level's file in `tools/level_defs/`: the
build rewrites it there, so change region names and colors in that file,
not here.

## Turning an illustration into a grid

The illustration is laid over the hex grid, and each gem takes the color
that covers most of it, snapped to the illustration's main colors.
Illustrations convert best with flat colors, bold shapes and about 5–10
colors; gradients, thin outlines and fine details get lost at gem size.
Pick the smallest grid that keeps the picture recognizable (the toadstools
need about 56 gems across). After converting, touch up the result in the
editor.

Only add illustrations that are yours or are licensed compatibly with
CC BY-NC-SA 4.0 (CC0 and CC BY are fine), and list them in the table above.
