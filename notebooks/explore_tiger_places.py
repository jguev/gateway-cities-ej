"""Exploration: TIGER/Line 2025 Places (California)

Questions answered here (results recorded in docs/data-inventory.md, #3):
1. What columns, CRS, and geometry types does the file have?
2. Do the classification fields (MTFCC, CLASSFP, FUNCSTAT) agree?

Run: PYTHONPATH=pipeline uv run python notebooks/explore_tiger_places.py
"""

import geopandas as gpd
import pandas as pd

from download import latest_path

places = gpd.read_file(latest_path("tiger_places", "tl_2025_06_place.zip"))

# 1. Shape of the data
print(len(places), "places | CRS:", places.crs)
print(places.geom_type.value_counts().to_string(), "\n")
print(places[["GEOID", "ALAND", "INTPTLAT"]].dtypes.to_string(), "\n")

# 2. Classification fields should tell the same story
print(places["CLASSFP"].value_counts().to_string(), "\n")
print(pd.crosstab(places["MTFCC"], places["FUNCSTAT"]))
