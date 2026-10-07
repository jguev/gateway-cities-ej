"""
Load the Huntington Park city boundary from TIGER/Line Place into PostGIS

Source: U.S. Census TIGER/Line 2025, Places, California (tl_2025_06_place.zip)
Run:    uv run python pipeline/load_hp_boundary.py
"""

import geopandas as gpd
from sqlalchemy import create_engine, text

from download import latest_path

SOURCE = "tiger_places"
FILENAME = "tl_2025_06_place.zip"
HP_GEOID = "0636056"  # state 06 (California) + place 36056 (Huntington Park)
TARGET_EPSG = 3310  # California Albers, meters: the project standard
TABLE = "city_boundary"
DB_URL = "postgresql+psycopg://jo@localhost:5432/gateway_cities"


def main() -> None:
    # 1. Read the raw file exactly as Census published it
    raw_file = latest_path(SOURCE, FILENAME)
    print(f"Reading {raw_file.name} from {raw_file.parent.name}")
    places = gpd.read_file(raw_file)

    # 2. Filter by permanent ID, and fail loudly if the result is unexpected
    hp = places[places["GEOID"] == HP_GEOID]
    if len(hp) != 1:
        raise ValueError(f"Expected 1 row for GEOID {HP_GEOID}, found {len(hp)}")

    # 3. Keep only the columns we need; lowercase names are PostgresSQL-friendly
    hp = hp[["GEOID", "NAME", "NAMELSAD", "ALAND", "AWATER", "geometry"]]
    hp = hp.rename(columns=str.lower)

    # 4. Reproject from NAD83 (EPSG:4269) to California Albers (EPSG:3310)
    hp = hp.to_crs(epsg=TARGET_EPSG)

    # 5. Write to PostGIS. "replace" makes the script safe to run repeatedly.
    engine = create_engine(DB_URL)
    hp.to_postgis(TABLE, engine, if_exists="replace", index=False)

    # 6. Verify: the database's area should match Census's published area.
    census_km2 = (hp["aland"].iloc[0] + hp["awater"].iloc[0]) / 1e6
    with engine.connect() as conn:
        db_km2 = conn.execute(
            text(f"SELECT ST_Area(geometry) / 1e6 FROM {TABLE}")
        ).scalar_one()

    print(f"Loaded {len(hp)} row into '{TABLE}' (EPSG:{TARGET_EPSG})")
    print(f"Census area:   {census_km2:.3f} km²")
    print(f"PostGIS area:  {db_km2:.3f} km²")


if __name__ == "__main__":
    main()
