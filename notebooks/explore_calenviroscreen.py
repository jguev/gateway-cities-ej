"""Exploration: CalEnviroScreen 5.0 results

Questions answered here (results recorded in docs/data-inventory.md, #4):
1. What layers, CRS, and geometry types does the geodatabase have?
2. How is missing data stored, and do NULL counts match the dictionary?
3. Are tract IDs unique, and how many digits are they?
4. Why do some tracts have no overall score?
5. Which tracts are inside Huntington Park (>= 50% of area)?

Run: PYTHONPATH=pipeline uv run python notebooks/explore_calenviroscreen.py
Requires: the city_boundary table (pipeline/load_hp_boundary.py).
"""

import geopandas as gpd
import pyogrio
from sqlalchemy import create_engine

from download import latest_path

DB_URL = "postgresql+psycopg://jo@localhost:5432/gateway_cities"
INSIDE_THRESHOLD = 50  # percent of tract area; see Decisions in project log

path = latest_path("calenviroscreen", "calenviroscreen50results_f_070126.gdb.zip")
print("Layers:", pyogrio.list_layers(path), "\n")
ces = gpd.read_file(path, layer="CES5_final_results")

# 1. Shape of the data
print(len(ces), "tracts | CRS:", ces.crs)
print(ces.geom_type.value_counts().to_string(), "\n")

# 2. Missing data: sentinel values vs. real NULLs
numeric = ces.select_dtypes("number")
print("Columns with negative values:", list(numeric.columns[numeric.lt(0).any()]))
nulls = ces.isna().sum()
print("NULL counts:")
print(nulls[nulls > 0].to_string(), "\n")

# 3. Tract IDs
print("ID lengths:", ces["tract"].astype(str).str.len().value_counts().to_dict())
print("Unique:", ces["tract"].is_unique, "\n")
ces["geoid"] = ces["tract"].astype(str).str.zfill(11)

# 4. Unscored tracts
unscored = ces[ces["CIscore"].isna()]
print(len(unscored), "unscored tracts; population:")
print(unscored["Population"].describe()[["min", "50%", "max"]].to_string())
largest = unscored.sort_values("Population").iloc[-1]
print("Largest unscored:", largest["geoid"], "\n")

# 5. Huntington Park overlap
engine = create_engine(DB_URL)
hp = gpd.read_postgis(
    "SELECT geometry FROM city_boundary", engine, geom_col="geometry"
).geometry.iloc[0]
hits = ces[ces.intersects(hp)].copy()
hits["pct_inside"] = hits.intersection(hp).area / hits.area * 100
inside = hits[hits["pct_inside"] >= INSIDE_THRESHOLD]
rest = hits.drop(inside.index)
print(f"{len(hits)} intersect, {len(inside)} inside (>= {INSIDE_THRESHOLD}%)")
print("Share inside, inside tracts: min", round(inside["pct_inside"].min(), 1))
print("Share inside, other tracts:  max", round(rest["pct_inside"].max(), 1))
lo, hi = inside["CIscoreP"].min(), inside["CIscoreP"].max()
print(f"Percentile range inside: {lo:.1f} - {hi:.1f}")
print("Unscored among intersecting:", int(hits["CIscore"].isna().sum()))
