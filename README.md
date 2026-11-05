# Georgia 2026 U.S. Senate: land vs. people

Interactive county cartograms of the Georgia Senate race (Ossoff vs. Collins). The point: a county-by-county map shows a lot of red because land votes don't count; people do.

Open any file in `pages/` in a browser. They are self-contained HTML.

| File | What it is |
|---|---|
| `pages/georgia-population-lens.html` | Current version. Land map with three views: **Land**, **People** (one hexagon per 10,000 residents), and **Lens** (a population magnifier you roll over the map, or snap to the whole map). Tooltips can be turned off. |
| `pages/georgia-land-vs-people.html` | Earlier version: land-to-hexagon morph, with tap-a-county grow/shrink in place. |
| `pages/georgia-senate-hexmap.html` | First version: static hex tile map. |
| `media/georgia-land-to-people.gif`, `.mp4` | 10 s loop (720x900) of land, lens, whole map, hexagons. |

## How it works

- **Hexpack** (`src/hexpack/`): packs 1,072 hexagons (one per 10,000 residents, at least one per county) into Georgia's outline. Each county is one connected piece and the outline still reads as Georgia. 321 of the 414 real county borders are kept as shared borders (78%); the misses are mostly one- or two-hexagon rural counties. Counties land on average about 0.8 degrees from their real position, which is unavoidable at a fixed outline: Atlanta's counties need about 37% of the hexagon area but cover about 8% of the land.
- **Rings** (`build_rings*.py`): each county gets an aligned real-outline ring and hexagon ring so the page can morph them. Hexagon coordinates are snapped to the exact grid before unioning (rounded coordinates silently dropped pieces of counties).
- **Lens** (`src/lens/`): a density-equalizing flow (Gastner-Newman diffusion) computed for 103 lens positions, plus one whole-map field, stored as displacement grids in `data/lens-fields.json`. The page blends nearby fields as the lens moves. The flow never folds or overlaps counties. Whole map overlaps the real outline about 74%, so it reads as "Georgia, stretched", not Georgia's outline.
- **Page** (`src/page/`): `lens.template.html` has `/*DATA*/` and `/*LENS*/` placeholders; `build_lens_template.py` patches `morph.template.html` into it. Fill the placeholders with `data/rings.json` and `data/lens-fields.json`.
- **GIF** (`src/media/capture-gif.js`): renders the page on a virtual clock with Playwright and encodes frames with ffmpeg.

The scripts were written in a scratch workspace and still use absolute `/tmp/ga/...` paths for inputs and outputs. Point them at `data/` before re-running.

## Data

- County results: Atlanta Journal-Constitution, 99% of precincts reporting on Nov 5, 2026. Unofficial until certified. See `data/senate.csv`.
- Residents: Census Bureau 2019 county estimates (joined in `data/counties-joined.json`).
- Geometry: US county GeoJSON in `data/raw/us-counties.geojson`. Island fragments of coastal counties are left off the map.
