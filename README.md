# Land vs. people: county cartograms for US elections

Interactive county maps that show election results two ways: by land area, and by the people who live there. A land map of a close statewide race looks lopsided because empty counties are big. These pages put population back in, with three views: **Land**, **People** (one hexagon per 10,000 residents) and **Lens** (a population magnifier you move over the map, or snap to the whole map).

`index.html` is a gallery of every election built so far. Each election is a self-contained page in `elections/<id>/index.html`.

| Election | Page |
|---|---|
| Georgia 2026 U.S. Senate (Ossoff vs. Collins) | `elections/ga-2026-senate/` |

## Make one for a new race

Scope today: **one US state, county level, exactly two candidates.** (Any number of parties and non-US elections are planned, not built.)

1. Copy `elections/ga-2026-senate/` to `elections/<id>/` (for example `pa-2026-senate`), drop the generated files (`layout.json`, `rings.json`, `lens-fields.json`, `index.html`, `media/`, `archive/`).
2. Put county results in `results.csv` (a `county` column of names, or a `fips` column, plus one vote column per candidate).
3. Edit `config.json` (reference below).
4. Run `python3 build.py elections/<id>/config.json`. A mid-size state takes about 3 to 10 minutes. Resume with `--from <step>`; add `--gif` for a 720x900 GIF and MP4 for social media.

Needs Python 3 with numpy, scipy, shapely and matplotlib; `node` with Playwright and `ffmpeg` only for `--gif`.

Population comes from `data/raw/uid-lookup.csv` (JHU CSSE lookup table, Census 2019 estimates) and county shapes from `data/raw/us-counties.geojson`; both cover every state, so only the results need sourcing.

### config.json

```json
{
  "id": "ga-2026-senate",
  "state": {"name": "Georgia", "abbr": "GA", "fips": "13", "people": "Georgians"},
  "race": {"office": "U.S. Senate", "date": "Nov 3, 2026"},
  "candidates": {
    "a": {"name": "Ossoff", "full": "Jon Ossoff", "ramp": "blue"},
    "b": {"name": "Collins", "full": "Mike Collins", "ramp": "red"}
  },
  "results": {"file": "results.csv", "county_col": "county", "a_col": "ossoff", "b_col": "collins"},
  "text": {"source": "Credit line shown at the bottom of the page.", "gif_source": "Short credit for the GIF."}
}
```

Optional keys: `results.fips_col` (join by FIPS instead of names); `population` (`format: "csv"` with `file`, `fips_col`, `pop_col` to use your own numbers); `projection` (`lon0`, `lat0`; default is the centre of the state); `hex.unit` (residents per hexagon, default 10000, so use 5000 for small states and 20000 for big ones), `hex.seed`, `hex.iterations`, `hex.frozen` (keep the committed `layout.json` instead of repacking); `lens.start_county`, `lens.gif_target`, `lens.scale` (default is derived from the state's size); `candidates.*.ramp` (`blue`, `red`, or an object with `mid_l`, `deep_l`, `mid_d`, `deep_d`). Candidate A uses the blue slot and B the red slot in the page styles.

## How it works

`build.py` runs seven steps; each script reads the same config (`src/common/cfg.py`) and writes next to it. Caches live in `elections/<id>/.cache/` (safe to delete).

1. **join** (`src/page/join.py`): geometry + population + results into one county table. Stops if any county is unmatched.
2. **hexpack** (`src/hexpack/hexpack.py`): packs one hexagon per 10,000 residents (at least one per county) into the state's outline so every county is one connected piece and the outline still reads as the state. Counties land on average 0.5 to 0.8 degrees from their real position at a fixed outline; the build prints how many real borders survive.
3. **rings** (`build_rings.py`, `build_rings2.py`): each county gets aligned real-outline, hexagon and in-place rings so the page can morph between them. Hexagon coordinates are snapped to the grid before unioning (rounded coordinates silently dropped county pieces).
4. **lens** (`src/lens/`): a density-equalizing flow (Gastner-Newman diffusion) for about 100 lens positions plus one whole-map field, stored as displacement grids. The flow never folds counties. All lens lengths scale with the state's size.
5. **page** (`src/page/build_page.py`): fills `lens.template.html` with the data, names, text and colors.
6. **verify** (`src/verify.py`): connected counties, hexagon counts, ring areas, no folded warps, page parses. The build fails if any check does.
7. **gallery** (`src/site_index.py`): regenerates the root `index.html`.

## Reproducibility

Georgia's `rings.json` and lens fields rebuild bit-for-bit from the committed layout. Its `layout.json` is **frozen** (`hex.frozen`): repacking from scratch is stochastic and gives an equivalent layout (314 to 321 of 414 real borders kept versus 321 in the published one), not an identical one. A second state (Pennsylvania, synthetic results) built end to end in about 3.5 minutes with all checks passing and 93% of real borders kept.

## Known limits

- Counties only: Alaska boroughs, Connecticut planning regions and New England towns are not supported. Virginia independent cities must be listed separately in the results.
- Two candidates only. Island fragments of coastal counties are left off the map.
- On the People view, labels of counties on the very edge of the map can be clipped.
- Tested in headless Chromium at phone and desktop sizes, not on a physical phone.

## Data

- Georgia results: Atlanta Journal-Constitution, 99% of precincts reporting on Nov 5, 2026, unofficial until certified (`elections/ga-2026-senate/results.csv`).
- Residents: Census Bureau 2019 county estimates via the JHU CSSE lookup table.
- Earlier Georgia versions are kept in `elections/ga-2026-senate/archive/`.
