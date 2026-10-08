# Project Log: Gateway Cities

## Project Info

| Field | Value |
|---|---|
| Start date | 2026-10-06 |
| Repo | jguev/gateway-cities-ej |
| Python | 3.12 (exact package versions pinned in `uv.lock`) |
| GDAL | 3.12.4 |
| PROJ | 9.8.1 |
| PostgreSQL | 18.6 |
| PostGIS | 3.6.3 |

## Conventions

- **Dates** use ISO 8601 (`YYYY-MM-DD`).
  - Log entries and decisions use the local date (America/Los_Angeles).
  - Raw data folders and manifest timestamps use UTC, so a download after 5 pm Pacific is filed under the next day's date.
- **CRS:** all PostGIS tables are stored in EPSG:3310 (see Decisions).
- **Census IDs** (GEOIDs, tract IDs) are always stored as text, never numbers.
- **References:** work is cited by pull request number (e.g. #4), which stays stable after squash merges.

## Data Sources

| Dataset | URL | Accessed | Original CRS |
|---|---|---|---|
| U.S. Census TIGER/Line 2025, Places, California | https://www2.census.gov/geo/tiger/TIGER2025/PLACE/tl_2025_06_place.zip | 2026-10-07 (via pipeline; see data/manifest.jsonl) | EPSG:4269 (NAD83) |
| CalEnviroScreen 5.0 (OEHHA), final, released 2026-07-01 | https://data.ca.gov/dataset/calenviroscreen-5-0 | 2026-10-07 (via pipeline; see data/manifest.jsonl) | EPSG:3310 |

## Decisions

- **2026-10-06:** All PostGIS tables are stored in EPSG:3310 (California Albers, meters). Raw files keep their original CRS.
- **2026-10-07:** Raw downloads are saved in dated folders (`data/raw/<source>/<date>/`) and never overwritten. Every download is recorded in `data/manifest.jsonl` with a SHA-256 checksum.
- **2026-10-07:** Code is linted and formatted with ruff before every commit (rules E, F, I; config in `pyproject.toml`).
- **2026-10-07:** CalEnviroScreen acquired as a file geodatabase rather than shapefile or CSV, to keep full field names, column types, and real NULLs (#4).
- **2026-10-07:** A tract counts as inside a boundary if ≥ 50% of its area lies inside (#4).
- **2026-10-08:** Census IDs are always stored as text; integer IDs from sources are zero-padded on load.

## Open Decisions

- **Study area definition.** The Gateway Cities are a political grouping of cities, but the Exide sampling zone is defined by distance and includes Boyle Heights (part of the City of Los Angeles) and East Los Angeles (an unincorporated CDP). A list of cities can't define the study area cleanly. Decide before designing the database.

## Sessions

### 2026-10-06: Session 1: Setup and First Load (#1)

- Set up Homebrew, a private GitHub repo, uv (Python 3.12), Postgres.app with PostGIS, and QGIS.
- Loaded the Huntington Park boundary (GEOID 0636056) from TIGER into PostGIS, reprojected to EPSG:3310.
- Verified: PostGIS area matches Census at 7.798 km².

### 2026-10-07: Session 2: Acquisition Pipeline and Data Inventory (#2,3)

- Built `pipeline/download.py`: streams downloads into dated raw folders, writes to a `.part` file then renames, rejects HTML error pages, and records provenance in a JSONL manifest.
- Re-acquired TIGER Places through the pipeline; confirmed the checksum with `shasum` and that it matched the hand-downloaded copy before deleting it.
- Loader now finds its input through the manifest (`latest_path()`); output unchanged at 7.798 km².
- Added ruff config; fixed import grouping and line length.
- Started `docs/data-inventory.md` with TIGER Places, checked against the data: 483 cities, 1,136 CDPs, 136 MultiPolygons.
- Filtering to cities would drop several census-designated places (CDPs), which are historically some of the most burdened communities with least political power. 

### 2026-10-07: Session 3: CalEnviroScreen 5.0 (#4)

- Chose the file geodatabase over shapefile/CSV: full field names, real types, real NULLs, geometry.
- Acquired the results and data dictionary through the download helper (both in the manifest).
- Checked the data against the dictionary: NULL counts match exactly, no sentinel values (counts in data-inventory.md).
- Found that tract IDs are stored as integers and need zero-padding to 11 characters.
- First spatial join: 33 tracts intersect Huntington Park; 14 are inside under the ≥ 50% rule, all in the 89th–99th percentile.
- Statewide data-quality check: 73 tracts have no overall score. The largest (13,681 people, tract 06037265301) is the UCLA dormitory area, outside the study area. It explained the pattern: students in dorms live in "group quarters," which are excluded from poverty statistics. None of the tracts touching Huntington Park are unscored, but group-quarters tracts elsewhere in the study area could be.
- **Reflection:** A spatial join matches rows when shapes intersect, and "intersects" includes tracts that only share a border with Huntington Park. Those border tracts are more neighbors than actual parts of the city, so I measured each tract's overlap area to keep only the ones truly inside.

### 2026-10-08: Session 4: Reproducibility Cleanup

- Added a Conventions section (dates, CRS, Census IDs, PR references).
- Inventory: added NULL-count table, overlap method/rule/result, file checksums, open questions.
- Log: recorded GDAL, PROJ, PostgreSQL, and PostGIS versions; dated all decisions; added Open Decisions.
- Committed exploration scripts in `notebooks/`; rerunning them reproduced every documented number.
- **Reflection:** My exploration of the data used to live only in my terminal history. Findings I can rerun let me check whether they still hold when the data changes.