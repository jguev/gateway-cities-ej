# Project Log: Gateway Cities

## Project Info

| Field | Value |
|---|---|
| Start date | 2026-10-06 |
| Repo | jguev/gateway-cities-ej |

## Data Sources

| Dataset | URL | Accessed | Original CRS |
|---|---|---|---|
| U.S. Census TIGER/Line 2025, Places, California | https://www2.census.gov/geo/tiger/TIGER2025/PLACE/tl_2025_06_place.zip | 2026-10-07 (via pipeline; see data/manifest.jsonl) | EPSG:4269 (NAD83) |

## Decisions

- **2026-10-06:** All PostGIS tables are stored in EPSG:3310 (California Albers, meters). Raw files keep their original CRS.
- **2026-10-07:** Raw downloads are saved in dated folders (`data/raw/<source>/<date>/`) and never overwritten. Every download is recorded in `data/manifest.jsonl` with a SHA-256 checksum.
- **2026-10-07:** Code is linted and formatted with ruff before every commit (rules E, F, I; config in `pyproject.toml`).

## Sessions

### 2026-10-06: Session 1: Setup and First Load

- Set up Homebrew, a private GitHub repo, uv (Python 3.12), Postgres.app with PostGIS, and QGIS.
- Loaded the Huntington Park boundary (GEOID 0636056) from TIGER into PostGIS, reprojected to EPSG:3310.
- Verified: PostGIS area matches Census at 7.798 km².

### 2026-10-07: Session 2: Acquisition Pipeline and Data Inventory

- Built `pipeline/download.py`: streams downloads into dated raw folders, writes to a `.part` file then renames, rejects HTML error pages, and records provenance in a JSONL manifest.
- Re-acquired TIGER Places through the pipeline; confirmed the checksum with `shasum` and that it matched the hand-downloaded copy before deleting it.
- Loader now finds its input through the manifest (`latest_path()`); output unchanged at 7.798 km².
- Added ruff config; fixed import grouping and line length.
- Started `docs/data-inventory.md` with TIGER Places, checked against the data: 483 cities, 1,136 CDPs, 136 MultiPolygons.
- Filtering to cities would drop several census-designated places (CDPs), which are historically some of the most burdened communities with least political power. 

### 2026-10-07: Session 3: CalEnviroScreen 5.0

- Chose the file geodatabase over shapefile/CSV: full field names, real types, real NULLs, geometry.
- Acquired the results and data dictionary through the download helper (both in the manifest).
- Checked the data against the dictionary: NULL counts match exactly; no sentinel values.
- Found that tract IDs are stored as integers and need zero-padding to 11 characters.
- First spatial join: 14 tracts lie in Huntington Park, all in the 89th–99th percentile.
- A spatial join matches rows when shapes intersect, and "intersects" includes tracts that only share a border with Huntington Park. Those border tracts are more neighbors than actual parts of the city, so I measured each tract's overlap area to keep only the ones truly inside.
- The largest unscored tract (13,681 people) turned out to be the UCLA dorms. Students in dorms live in "group quarters," which are left out of poverty statistics, so missing data can follow a pattern instead of being random.