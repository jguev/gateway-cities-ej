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

  ---

## CalEnviroScreen 5.0 (OEHHA)

| Item | Detail |
|---|---|
| Publisher | California Office of Environmental Health Hazard Assessment (OEHHA) |
| What it is | Cumulative pollution burden and population vulnerability scores |
| Geography | One row per 2020 census tract (9,106 tracts) |
| Version used | Final 5.0, released 2026-07-01 |
| Update schedule | Irregular (major versions every few years) |
| Original CRS | EPSG:3310 (already the project standard) |
| Format | File geodatabase, layer `CES5_final_results` |
| Acquire script | `pipeline/acquire_calenviroscreen.py` |
| Documentation | Data dictionary (acquired alongside the data), [technical report](https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-50) |
| Terms | No restrictions on public use |

### Key fields

| Field | Meaning |
|---|---|
| `tract` | Census tract ID. **Stored as an integer (10 digits); must be converted to 11-character text with a leading zero** to match other Census data. |
| `CIscore` / `CIscoreP` | Overall CalEnviroScreen score and its statewide percentile |
| `lead` / `Lead_Pctl` | Children's lead risk from housing ("Child's Lead" in the dictionary) |
| `traffic`, `Diesel_PM`, `Haz_Waste`, `cleanups` | Indicators most relevant to the I-710 corridor and Exide |
| `*_Pctl` | Statewide percentile (0–100) for each indicator |

### Files acquired (see `data/manifest.jsonl`)

| File | SHA-256 (prefix) | Raw folder (UTC) |
|---|---|---|
| `calenviroscreen50results_f_070126.gdb.zip` | `5bcb8afe5b01f477` | `2026-10-08` |
| `final-calenviroscreen-5.0-data-dictionary.pdf` | `1c730d0a9a7e7271` | `2026-10-08` |

### Verified against the data (2026-10-07, #4)

- 9,106 tracts, all MultiPolygon, CRS EPSG:3310. Tract IDs are unique.
- No negative or sentinel values; missing data is stored as real NULLs.
- NULL counts match the data dictionary's "# of NAs" table:

| Indicator | Column | Dictionary | Data |
|---|---|---|---|
| Child's Lead | `lead` | 84 | 84 |
| Diesel PM | `Diesel_PM` | 9 | 9 |
| Drinking Water | `Drinking_Water` | 9 | 9 |
| Traffic | `traffic` | 9 | 9 |
| Asthma | `asthma` | 33 | 33 |
| Cardiovascular Disease | `Cardiovascular` | 26 | 26 |
| Diabetes | `diabetes` | 36 | 36 |
| Low-Birth-Weight | `Low_Birth_Weight` | 234 | 234 |
| Education | `Education` | 28 | 28 |
| Housing Burden | `HousBurd` | 64 | 64 |
| Linguistic Isolation | `Linguistic_Isol` | 58 | 58 |
| Poverty | `Poverty` | 50 | 50 |
| Unemployment | `Unemployment` | 45 | 45 |

  All other indicators: 0 NULLs in both. Not covered by the dictionary
  table: overall score (`CIscore`, 73 NULLs), population characteristics
  (`PopChar`, 73), and demographic columns (25 each).

### Huntington Park overlap (2026-10-07, #4)

- **Method:** spatial join with `intersects`, then each tract's share of
  area inside the city = area of (tract ∩ city) / tract area, in EPSG:3310.
- **Rule:** a tract is "in" the city if ≥ 50% of its area is inside.
- **Result:** 33 tracts intersect; 14 are inside (shares 99.7–100%);
  19 only touch the border (share 0.0%: the overlap is a line, not an area).
  Because shares are either ~100% or 0%, any threshold from 1% to 99%
  gives the same 14 tracts.
- All 14 tracts rank in the 89th–99th percentile overall.
- None of the 33 intersecting tracts is unscored.

### Open questions

- **Tract count:** CES has 9,106 tracts. California's full 2020 tract
  count appears to be somewhat higher. To verify by comparing against TIGER
  2020 tracts (likely water-only or unpopulated tracts excluded).
- **Server date:** files report Last-Modified 2026-10-01, after the
  2026-07-01 release. Unknown whether contents changed.

### Limitations

- **Screening tool, not a risk assessment.** Percentiles are relative rankings, not health thresholds.
- **Tract-level only.** It can't describe individual homes.
- **2020 tracts.** Not directly comparable to CalEnviroScreen 4.0, which used 2010 tracts.
- **Zero is not missing.** Zeros are real measurements; NAs are unknown. Never fill NAs with 0.
- **73 tracts have no overall score.** Population in these tracts ranges from 0 to 13,681 (median 38). Most have too few residents to score, but the largest is the UCLA dormitory tract. Students in dorms live in "group quarters," which the Census Bureau excludes from poverty statistics, so CalEnviroScreen can't compute the population side of the score. Missing scores therefore follow a pattern (few residents, or residents in group quarters) rather than being random.
- **Folder dates are UTC.** The raw folder is dated 2026-10-08 because the download happened after 5 pm Pacific.

---

## DTSC Exide Cleanup Layers (ArcGIS feature services)

| Item | Detail |
|---|---|
| Publisher | California Department of Toxic Substances Control (DTSC) |
| Layers | Parcel status (10,642 parcels, **private**), PIA boundary (1), Exide facility (1) |
| Service | `services3.arcgis.com/Oy2JTCD10wkoelxS/.../DTSCCleanupMay26/FeatureServer/2` (parcels); `.../DTSCCleanupMay24English/FeatureServer/2` and `/3` |
| Traced from | App `d8a6b586...` → web map `c7cfedca...` → operational layers |
| Native CRS | EPSG:2229 (State Plane Zone 5, US ft); downloaded as EPSG:4326 (server-side conversion; ~1–2 m datum tolerance) |
| Update schedule | Live layer; data last edited 2026-10-12 at time of download |
| Acquire script | `pipeline/acquire_dtsc_exide.py` |

**Key field:** `RepresentativeSoilLeadConcent`, one value per property in ppm: the 95% UCL of 10–15 individually analyzed yard samples (EPA ProUCL), per DTSC's map app. A conservative upper estimate, not an average.

**Privacy:** `APN`, `Address`, and `FileURL*` identify individual homes. The parcel layer is stored only in `data/private/` and is never published at parcel level.

**Limitations**
- Use the numeric lead field, not `Symbology` labels; label text has changed over time (80–119 vs. 80–154 ppm).
- Prioritization text cites 300 ppm in one place and 400 ppm elsewhere; unresolved.
- Only properties with access agreements were sampled ("Access Not Provided" parcels have no result).