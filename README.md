# Land vs. people: county cartograms for US elections

Interactive county maps that show election results two ways: by land area, and by the people who live there. A land map of a close statewide race looks lopsided because empty counties are big. These pages put population back in.

**Live gallery:** https://christhchild28.github.io/us-midterms-cartograms-geogia-test/

## Status

- This is **version 1**. It is frozen on the `v1-final` branch. A second, stricter version (typed data model, stable unit IDs, stronger checks) is planned in a separate repository.
- **54 pages** are built, one per race (listed below). One more race, Virginia Senate, has a config and data but **no page**: the layout step stalls on its 133 counties and independent cities.
- All results are **unofficial** unless a page says otherwise. Each page names its source and the date of its numbers in the footer. Two races (Kansas governor, Mississippi Senate) were uncalled when built; those pages say "leads", not "won".
- The scheduled results refresh on Dec 12 can still add commits to `main`.

## What a page shows

| Control | What it does |
|---|---|
| **Land** | Real county shapes. Tap a county to grow or shrink it in place. |
| **Lens** | Every county resized by its residents (a density-equalizing warp). A pale copy of the real state sits behind it. |
| **People** | One hexagon per N residents (N is printed on the page and is listed in the table below). The Land to People morph passes through the Lens warp. |
| **Color by: Winner / Swing** | Winner shades each county by margin. Swing shades the change in two-party share against an earlier race (named on the page). Hatching marks a county that a different party won in the earlier race. All 54 pages have an earlier race configured. |
| **Land outlines** | Shows or hides the pale real-state shape. |
| **County card** | Tap a county. Phones get a bottom sheet; desktop gets a side panel (hover previews). **More** opens the vote table. |
| **Precincts** | NYC pages only. A fourth view of 4,214 election districts as real shapes shaded by margin. |

**Retired: the Magnify lens.** Earlier versions had a Magnify / Whole map switch in the Lens view: Magnify enlarged the counties under the pointer as you dragged. It is retired and hidden. The Lens view now always shows the whole population warp, and dragging does nothing. The code is still in `src/page/warp.template.html` (marked `DORMANT`) so it can come back, but no page shows it. `#lens` still opens the Lens view (the whole warp). The settings `lens.start_county`, `lens.radius` and `lens.spacing` are still read, but only the dormant Magnify code uses them.

Links can open a view directly: add `#lens` or `#pop` (or `#people`) to a page URL. The default view is Land.

Each page also carries a table of all counties (a text equivalent of the map), a **Back / All elections / Next** bar, and a share GIF and MP4 in `media/`.

**Privacy.** Pages load the Archivo and IBM Plex Mono fonts from Google Fonts. 54 pages also load GoatCounter analytics (site `distortmaps`), which counts view changes, color-mode changes, county taps and resets. Analytics are off unless the config sets `analytics.goatcounter`.

## Races

Generated from the `elections/*/config.json` files on 2026-11-11. Candidate A uses the blue slot and B the red slot, except where noted below the table. **Hexagon** is the weight per hexagon: residents, except on the two NYC pages, where it is votes cast.

| State | Race | Candidates (A vs B) | Source | Hexagon | Page |
|---|---|---|---|---|---|
| Alabama | Governor | Jones vs Tuberville | NBC News / AP | 5,000 | [open](elections/al-2026-governor/) |
| Alabama | Senate | Wess vs Moore | NBC News / AP | 5,000 | [open](elections/al-2026-senate/) |
| Arizona | Governor | Hobbs vs Biggs | NBC News / AP | 10,000 | [open](elections/az-2026-governor/) |
| Arkansas | Governor | Love vs Huckabee Sanders | NBC News / AP | 10,000 | [open](elections/ar-2026-governor/) |
| Arkansas | Senate | Shoffner vs Cotton | NBC News / AP | 10,000 | [open](elections/ar-2026-senate/) |
| California | Governor | Becerra vs Hilton | California SoS | 20,000 | [open](elections/ca-2026-governor/) |
| Colorado | Governor | Weiser vs Marx | NBC News / AP | 5,000 | [open](elections/co-2026-governor/) |
| Colorado | Senate | Hickenlooper vs Baisley | NBC News / AP | 5,000 | [open](elections/co-2026-senate/) |
| Florida | Governor | Jolly vs Donalds | NBC News / AP | 10,000 | [open](elections/fl-2026-governor/) |
| Florida | Senate special | Nixon vs Moody | NBC News / AP | 10,000 | [open](elections/fl-2026-senate/) |
| Georgia | Governor | Bottoms vs Jackson | NBC News / AP | 10,000 | [open](elections/ga-2026-governor/) |
| Georgia | Senate | Ossoff vs Collins | Atlanta J-C | 10,000 | [open](elections/ga-2026-senate/) |
| Idaho | Governor | Pickens vs Little | NBC News / AP | 5,000 | [open](elections/id-2026-governor/) |
| Idaho | Senate | Achilles vs Risch | NBC News / AP | 5,000 | [open](elections/id-2026-senate/) |
| Illinois | Governor | Pritzker vs Bailey | NBC News / AP | 10,000 | [open](elections/il-2026-governor/) |
| Illinois | Senate | Stratton vs Tracy | NBC News / AP | 10,000 | [open](elections/il-2026-senate/) |
| Iowa | Governor | Sand vs Lahn | NBC News / AP | 10,000 | [open](elections/ia-2026-governor/) |
| Iowa | Senate | Turek vs Hinson | NBC News / AP | 10,000 | [open](elections/ia-2026-senate/) |
| Kansas | Governor (uncalled) | Holscher vs Masterson | NBC News / AP | 3,000 | [open](elections/ks-2026-governor/) |
| Kentucky | Senate | Booker vs Barr | NBC News / AP | 5,000 | [open](elections/ky-2026-senate/) |
| Louisiana | Senate | Davis vs Letlow | NBC News / AP | 5,000 | [open](elections/la-2026-senate/) |
| Michigan | Governor | Benson vs James | Michigan SoS | 10,000 | [open](elections/mi-2026-governor/) |
| Michigan | Senate | El-Sayed vs Rogers | Michigan SoS | 10,000 | [open](elections/mi-2026-senate/) |
| Minnesota | Governor | Klobuchar vs Demuth | NBC News / AP | 10,000 | [open](elections/mn-2026-governor/) |
| Minnesota | Senate | Flanagan vs Tafoya | NBC News / AP | 10,000 | [open](elections/mn-2026-senate/) |
| Mississippi | Senate (uncalled) | Colom vs Hyde-Smith | NBC News / AP | 3,000 | [open](elections/ms-2026-senate/) |
| Montana | Senate | Bodnar vs Alme | NBC News / AP | 10,000 | [open](elections/mt-2026-senate/) |
| Nebraska | Governor | Walz vs Pillen | NBC News / AP | 10,000 | [open](elections/ne-2026-governor/) |
| Nebraska | Senate | Osborn vs Ricketts | NBC News / AP | 10,000 | [open](elections/ne-2026-senate/) |
| Nevada | Governor | Aaron Ford vs Lombardo | NBC News / AP | 5,000 | [open](elections/nv-2026-governor/) |
| New Jersey | Senate | Booker vs Murphy | NBC News / AP | 10,000 | [open](elections/nj-2026-senate/) |
| New Mexico | Governor | Haaland vs Hull | NBC News / AP | 3,000 | [open](elections/nm-2026-governor/) |
| New Mexico | Senate | Luján vs Marker | NBC News / AP | 3,000 | [open](elections/nm-2026-senate/) |
| New York | Governor | Hochul vs Blakeman | NY State BOE | 20,000 | [open](elections/ny-2026-governor/) |
| New York City | Governor, by Assembly district | Hochul vs Blakeman | NYC BOE | 2,500 votes | [open](elections/nyc-ad-2026-governor/) |
| New York City | Governor, by council district | Hochul vs Blakeman | NYC BOE | 2,500 votes | [open](elections/nyc-council-2026-governor/) |
| North Carolina | Senate | Cooper vs Whatley | NBC News / AP | 10,000 | [open](elections/nc-2026-senate/) |
| North Dakota | House (at-large) | Hammer vs Fedorchak | NBC News / AP | 2,000 | [open](elections/nd-2026-house/) |
| Ohio | Governor | Acton vs Ramaswamy | Ohio SoS | 10,000 | [open](elections/oh-2026-governor/) |
| Oklahoma | Governor | Munson vs Mazzei | NBC News / AP | 5,000 | [open](elections/ok-2026-governor/) |
| Oklahoma | Senate | Thomas vs Hern | NBC News / AP | 5,000 | [open](elections/ok-2026-senate/) |
| Oregon | Governor | Kotek vs Drazan | NBC News / AP | 10,000 | [open](elections/or-2026-governor/) |
| Oregon | Senate | Merkley vs Smith | NBC News / AP | 10,000 | [open](elections/or-2026-senate/) |
| Pennsylvania | Governor | Shapiro vs Garrity | Pennsylvania DoS | 10,000 | [open](elections/pa-2026-governor/) |
| South Carolina | Governor | Johnson vs Wilson | NBC News / AP | 10,000 | [open](elections/sc-2026-governor/) |
| South Carolina | Senate | Andrews vs Graham | NBC News / AP | 10,000 | [open](elections/sc-2026-senate/) |
| South Dakota | Governor | Ahlers vs Rhoden | NBC News / AP | 10,000 | [open](elections/sd-2026-governor/) |
| South Dakota | Senate | Bengs vs Rounds | NBC News / AP | 10,000 | [open](elections/sd-2026-senate/) |
| Tennessee | Governor | Green vs Blackburn | NBC News / AP | 10,000 | [open](elections/tn-2026-governor/) |
| Tennessee | Senate | Bradshaw vs Hagerty | NBC News / AP | 10,000 | [open](elections/tn-2026-senate/) |
| Texas | Senate | Talarico vs Paxton | Texas Tribune | 20,000 | [open](elections/tx-2026-senate/) |
| Wisconsin | Governor | Crowley vs Tiffany | NBC News / AP | 10,000 | [open](elections/wi-2026-governor/) |
| Wyoming | Governor | Casner vs Barlow | NBC News / AP | 10,000 | [open](elections/wy-2026-governor/) |
| Wyoming | Senate | Byrd vs Hageman | NBC News / AP | 10,000 | [open](elections/wy-2026-senate/) |

Notes:
- **Independents.** Bodnar (Montana) and Osborn (Nebraska) are independents. They use a purple ramp and a `(I)` tag so that blue stays Democratic.
- **NYC pages.** Hexagons are sized by votes cast (not residents) because Assembly and Council districts have near-equal population. Results are unofficial election-night numbers.
- **Swing baselines differ by race** (2024 president, 2022 governor, 2022 or 2020 Senate, and so on). The page names the baseline. Swing compares the two-party share between different candidates and offices: it shows how far each party moved, not voters switching.

## Make a page for a new race

Scope: **one US state (or one NYC district set), county level, exactly two candidates.**

1. Copy the folder of a similar race to `elections/<id>/` and delete its generated files (`warp-layout.json`, `warp-rings.json`, `lens-fields.json`, `index.html`, `media/`, `.cache/`).
2. Write three CSV files (formats below): `results.csv`, `prior.csv` (optional, enables Swing) and `population.csv`.
3. Edit `config.json` (reference below).
4. Run `python3 build.py elections/<id>/config.json --gif`. Put a time limit on it (for example `timeout 900`). The six steps are `join, warpack, warprings, lens, warppage, warpverify`. Most states take a few minutes (Wyoming: 111 seconds).
5. The `warpverify` step must pass. If a county breaks into pieces or a step runs far too long, lower `hex.unit` (for example from 10,000 to 5,000) and rebuild. Idaho ran over 19 minutes at 10,000 and finished in about 220 seconds at 5,000.
6. The build also regenerates the root gallery (`src/site_index.py`). Check the page at 390 px width, then commit and push.

### Which step picks up which change

| You changed | Run |
|---|---|
| Vote counts in `results.csv`, or `population.csv` | `python3 build.py <config> --from join --gif`. Votes and hexagon counts are stored in `warp-layout.json` and `warp-rings.json`, so they need the earlier steps. |
| `prior.csv`, colors, party tags, page text, source line, analytics | `python3 build.py <config> --only warppage` (add `--gif` to refresh the share media). These are read when the page is assembled. |

Rebuilding from `join` re-runs `warpack` and rewrites `warp-layout.json`. In a test on Wyoming the rebuilt layout was identical to the committed one, but that is one small race on one machine.

### Data files

**`results.csv`** has one row per county with one vote column per candidate. Two shapes are in use. Set `results.county_col` (county names, 26 pages) or `results.fips_col` (five-digit FIPS, 28 pages), then `results.a_col` and `results.b_col`:

```
county,ossoff,collins          fips,a,b
Appling,1548,4628              13001,1548,4628
```

**`prior.csv`** has `fips` and two vote columns for the earlier race. Name the columns for the candidates and point `prior.a_col` and `prior.b_col` at them. The columns must line up with candidate A and B (A first in the sense of party: the blue-slot party in the earlier race).

**`population.csv`** has `fips,county,population` (any column names, set under `population`). Residents come from Census Bureau July 1, 2025 county estimates (Vintage 2025) on 52 pages; the two NYC pages hold votes cast in the `population` column.

The join stops if any county in the geometry lacks a population or a results row, or if a result row matches no county. Match on FIPS where you can. Codes change: South Dakota's Oglala Lakota County is 46102 in current Census and NBC data but 46113 in `data/raw/us-counties.geojson`, so the South Dakota CSVs use 46113; Virginia's Bedford city (51515) is folded into Bedford County with `geometry.merge`.

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
  "results":    {"file": "results.csv", "county_col": "county", "a_col": "ossoff", "b_col": "collins"},
  "population": {"format": "csv", "file": "population.csv", "fips_col": "fips", "pop_col": "population", "name_col": "county"},
  "prior":      {"file": "prior.csv", "fips_col": "fips", "a_col": "abrams", "b_col": "kemp",
                 "label": "2022 governor", "short": "2022", "a": "Abrams", "b": "Kemp"},
  "projection": {"lon0": -83.4, "lat0": 32.7},
  "hex":  {"unit": 10000},
  "lens": {"start_county": "Fulton", "gif_target": "Chatham", "scale": 1},
  "text": {"source": "Credit line shown at the bottom of the page.", "gif_source": "Short credit for the GIF."},
  "analytics": {"goatcounter": "<site code>"}
}
```

| Key | Meaning |
|---|---|
| `race.uncalled` | `true` makes the headline say "leads" instead of "won". |
| `candidates.*.ramp` | `"blue"` or `"red"` (from `src/common/ramps.json`), or an object `{mid_l, deep_l, mid_d, deep_d}` for a custom color (light-mode mid and deep, dark-mode mid and deep). |
| `candidates.*.party` | Tag shown after the name, for example `"I"`. Defaults to D for the blue ramp and R for the red ramp. **A custom ramp has no default: set `party`.** Do not leave an independent on the blue ramp. |
| `prior` | Optional. Without it the page has no Swing control. |
| `population.format` | `"csv"` (every current config) or `"jhu-uid"` (the JHU CSSE lookup table in `data/raw/`, Census 2019 estimates; legacy default). |
| `projection` | Map center. Default: center of the state. |
| `hex.unit` | Weight per hexagon. Used on the 54 pages: 2,000 (1 race), 2,500 (2), 3,000 (4), 5,000 (11), 10,000 (33), 20,000 (3). Default 10,000. |
| `hex.warp_grid`, `hex.warp_sea`, `hex.polish_pull`, `hex.warp_passes` | Layout tuning (defaults 0.015, 1.0, 0.25, 10). |
| `hex.seed`, `hex.frozen` | Used only by the older outline packer. **The default pipeline ignores `frozen`** and rewrites `warp-layout.json` whenever `warpack` runs. |
| `lens.start_county`, `lens.gif_target` | `start_county` only matters to the retired Magnify lens. `gif_target` is the county the share GIF visits. |
| `lens.scale`, `lens.node`, `lens.spacing`, `lens.state_buffer` | Lens sizes (all scale with the state's extent by default). A larger `state_buffer` keeps detached land such as Staten Island connected. |
| `lens.card` | `"live"` makes the card follow the pointer. Default: the card changes on tap. |
| `text.vocab` | Swaps "county/counties/residents" for other words (`unit`, `units`, `measure`) with exact replacements in `fix`. Used by NYC pages and Louisiana (parishes). |
| `ui.outline_toggle` | `false` hides the Land outlines checkbox. |
| `geometry.file`, `geometry.merge` | Another GeoJSON, and units to fold into a parent (for example `{"51515": "51019"}`). |
| `ed` | Optional election-district layer (the NYC **Precincts** view). The build stops if any district lacks results or the totals do not match the parent districts. See `src/page/ed_layer.py`. |

## How it works

1. **join** (`src/page/join.py`) joins geometry, population and results into one county table.
2. **warpack** (`src/hexpack/warpack.py`) flows each county outline through a density-equalizing diffusion (`src/lens/warpflow.py`) until its area is proportional to its hexagon count, then assigns hexagons to counties with one exact assignment (`scipy.optimize.linear_sum_assignment`), repairs broken counties and runs a local polish. Every county gets its exact hexagon count and the layout does not depend on the vote.
3. **warprings** (`build_warp_rings.py`) makes aligned outlines for each county (real, warped, hexagon, in-place) so the page can morph between them.
4. **lens** (`src/lens/`) writes the warp displacement fields to `lens-fields.json`.
5. **warppage** (`src/page/build_warp_page.py`) fills `warp.template.html` with the data, text and colors and writes `elections/<id>/index.html`.
6. **warpverify** (`src/verify_warp.py`) checks hexagon counts against the layout, no duplicate hexagons, each county in one piece, and that the page exists. It does **not** check vote totals, population totals or the warp's area error.

The older outline-holding build (`python3 build.py <config> --outline`) is kept for reference and was not re-run for this README. `elections/ga-2026-senate/archive/` holds earlier Georgia versions.

Layout: `build.py` (entry point), `src/` (pipeline, page template, gallery themes in `src/gallery_themes/`), `data/raw/` (county geometry and the JHU lookup table), `elections/<id>/` (inputs, generated files and media for each race), `gallery.config.json` (gallery theme).

## Requirements

Python 3 with `numpy`, `scipy`, `shapely` and `Pillow` (last run with Python 3.13, numpy 2.5, scipy 1.18, shapely 2.2, Pillow 12.3; versions are not pinned). `matplotlib` is needed only for the older outline mode and `src/hexpack/preview.py`. `node` with Playwright and `ffmpeg` are needed only for `--gif`.

## Known limits

- **One state, county level, two candidates.** Alaska boroughs, Connecticut planning regions and New England towns are not supported. Third-party votes are left out of the two-candidate share.
- **Hexagon floor.** Every county gets at least one hexagon, so "one hexagon per N residents" is exact only when no county is below N/2. Total hexagons exceed the population estimate by 30.5% in South Dakota, 18.4% in Nebraska, 16.2% in Montana and 5.1% in Texas (91 of 254 counties are at the floor). Most other states are within 1%. The hexagon size also differs between races (2,000 to 20,000), so hexagons are not comparable across pages.
- **Border retention.** The People map keeps only part of the real county borders: from 47% (Arizona) to 100%, median 76% across the 55 layouts. The figure for each layout is in `warp-layout.json` under `stats`.
- **Projection.** Maps use one cosine factor at the state's center latitude, not an equal-area projection. Large north-south states such as Texas are visibly stretched.
- **Checks are structural.** Nothing in the build verifies votes or populations against an official total; that was done by hand when each race was added. There are no automated tests, and package versions are not pinned.
- **Builds are not byte-identical.** The lens file embeds a gzip timestamp, so `lens-fields.json` and `index.html` differ on every rebuild even when the data is the same.
- **Geometry.** `data/raw/us-counties.geojson` has no recorded source or vintage.
- **Devices.** Tested in headless Chromium at phone and desktop sizes. Not tested on a physical phone or with a screen reader. Counties cannot yet be reached with the keyboard; the county table is the text alternative.
- **Size.** The repository is about 490 MB, mostly share GIFs and MP4s.
- **License.** No license has been chosen yet.

## Data and credits

- **Results** are county returns as listed in the table's Source column: NBC News (from the Associated Press) for most states, and state or local offices, the Atlanta Journal-Constitution and the Texas Tribune for the others. Counts are unofficial until certified.
- **Residents:** Census Bureau July 1, 2025 county estimates (Vintage 2025), as supplied in each race's `population.csv`.
- **Earlier races for Swing:** the county results named in each page's footer.

## Corrections

- **2026-11-11:** Alabama governor and Senate `prior.csv` had the two vote columns under each other's names, so Swing showed the wrong sign (about -22 points instead of about +18 for the governor race). The headers now match the certified 2022 canvass. Montana and Nebraska Senate pages showed the independent candidates as "(D)" on a blue ramp; they now show "(I)" on a purple ramp.
