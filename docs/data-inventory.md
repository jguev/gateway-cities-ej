# Data Inventory

One entry per source. Each entry records what the documentation claims
and what we verified in the data itself. Update an entry whenever a new
vintage is acquired.

---

## U.S. Census TIGER/Line: Places (California)

| Item | Detail |
|---|---|
| Publisher | U.S. Census Bureau |
| What it is | Boundaries of incorporated cities and census-designated places (CDPs) |
| Geography | One polygon per place |
| Vintage used | 2025 (boundaries as of January 1, 2025) |
| Update schedule | Annual |
| Original CRS | EPSG:4269 (NAD83, geographic, degrees) |
| Stored as | EPSG:3310 (California Albers, meters) |
| File | `tl_2025_06_place.zip` (shapefile, ~9.9 MB) |
| Acquire script | `pipeline/acquire_tiger_places.py` |
| Documentation | [TIGER/Line technical documentation](https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/tiger-geo-line.html) |
| Terms | U.S. government work, public domain |

### Key fields

| Field | Type | Meaning |
|---|---|---|
| `GEOID` | text | State FIPS + place code (e.g. `0636056` = Huntington Park). **Primary key. Keep as text** to preserve leading zeros. |
| `NAME` / `NAMELSAD` | text | Name; `NAMELSAD` adds the legal type ("Huntington Park city") |
| `MTFCC` | text | `G4110` incorporated place, `G4210` CDP |
| `CLASSFP` | text | `C1` incorporated; `U1`/`U2` CDP (official / unofficial name); `M2` military CDP |
| `FUNCSTAT` | text | `A` active government, `S` statistical entity only |
| `ALAND` / `AWATER` | integer | Land / water area, square meters |
| `INTPTLAT` / `INTPTLON` | text | Internal point, guaranteed inside the polygon (not a centroid) |

### Verified against the data (2026-10-07)

- 1,619 places: 483 incorporated (`G4110`), 1,136 CDPs (`G4210`).
- `MTFCC`, `CLASSFP`, and `FUNCSTAT` are mutually consistent.
- Geometry: 1,483 `Polygon`, 136 `MultiPolygon`.
- Huntington Park area in EPSG:3310 matches `ALAND + AWATER` (7.798 km²).

### Limitations

- **Not survey-grade.** Fine for city-scale analysis; don't use it to decide
  whether an individual parcel is inside a boundary.
- **Boundaries can lag reality.** They reflect what local governments
  reported for January 1 of the vintage year.
- **CDPs have no legal standing** and can be redrawn each decade.
- **Don't filter to cities only.** Unincorporated communities such as
  Walnut Park and East Los Angeles are CDPs, and dropping them would bias an
  environmental justice analysis.
- **Mixed geometry types.** Convert to MultiPolygon before loading into a
  single table.
- **NAD83 vs WGS 84** differ by about 1–2 m in California. Always
  transform explicitly; never relabel one as the other.