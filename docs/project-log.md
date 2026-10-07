# Project Log: Gateway Cities

## Project Info

| Field | Value |
|---|---|
| Start date | 2026-10-06 |
| Repo | jguev/gateway-cities-ej |

## Data Sources

| Dataset | URL | Accessed | Original CRS |
|---|---|---|---|
| U.S. Census TIGER/Line 2025, Places, California | https://www2.census.gov/geo/tiger/TIGER2025/PLACE/tl_2025_06_place.zip | 2026-10-06 | EPSG:4269 (NAD83) |

## Decisions

- **2026-10-06:** All PostGIS tables are stored in EPSG:3310 (California Albers, meters). Raw files keep their original CRS.

## Sessions

### 2026-10-06: Setup and First Load

- Set up Homebrew, a private GitHub repo, uv (Python 3.12), Postgres.app with PostGIS, and QGIS.
- Loaded the Huntington Park boundary (GEOID 0636056) from TIGER into PostGIS, reprojected to EPSG:3310.
- Verified: PostGIS area matches Census at 7.798 km².