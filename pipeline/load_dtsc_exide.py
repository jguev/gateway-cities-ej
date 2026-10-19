"""Load DTSC Exide layers into the raw and staging schemas

raw: exactly as downloaded (all fields, EPSG:4326).
staging: only the fields analysis needs, stable status codes, EPSG:3310,
MultiPolygon geometry, and the source file's SHA-256 for lineage.
Addresses and document links are dropped (data minimization).
"""

import geopandas as gpd
from shapely.geometry import MultiPolygon
from sqlalchemy import create_engine, text

from download import last_recorded, latest_path

DB_URL = "postgresql+psycopg://jo@localhost:5432/gateway_cities"
SOURCE = "dtsc_exide"
TARGET_EPSG = 3310

# DTSC label text -> stable code, matched by prefix (labels change over time).
STATUS_PREFIXES = {
    "Cleaned": "cleaned",
    "Prioritized": "prioritized",
    "Residential Parcel with a Representative": "below_priority",
    "No Cleanup Required": "no_cleanup",
    "Access Not Provided": "no_access",
}


def to_multi(geom):
    """Promote Polygon to MultiPolygon so one column type fits every row."""
    if geom is not None and geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    return geom


def status_code(label):
    for prefix, code in STATUS_PREFIXES.items():
        if label and label.startswith(prefix):
            return code
    raise ValueError(f"Unknown parcel status label: {label!r}")


def read_layer(name):
    """Return the latest download of a layer and its SHA-256."""
    filename = f"{name}.geojson"
    gdf = gpd.read_file(latest_path(SOURCE, filename))
    return gdf, last_recorded(SOURCE, filename)["sha256"]


def write(gdf, table, schema, engine):
    gdf.to_postgis(table, engine, schema=schema, if_exists="replace", index=False)


def main() -> None:
    engine = create_engine(DB_URL)

    # Parcels: raw as-is, then a minimal staged version
    parcels, sha = read_layer("parcels")
    write(parcels, "dtsc_parcels", "raw", engine)
    staged = gpd.GeoDataFrame(
        {
            "objectid": parcels["OBJECTID"],
            "apn": parcels["APN"],
            "lead_ppm": parcels["RepresentativeSoilLeadConcent"],
            "category": parcels["CategoryforPrioritization"],
            "status": parcels["Symbology"].map(status_code),
            "source_sha256": sha,
        },
        geometry=parcels.geometry.map(to_multi),
        crs=parcels.crs,
    ).to_crs(epsg=TARGET_EPSG)
    write(staged, "dtsc_parcels", "staging", engine)

    # Boundary and facility: public information, geometry only
    for name in ["pia_boundary", "facility"]:
        gdf, sha = read_layer(name)
        write(gdf, f"dtsc_{name}", "raw", engine)
        clean = gpd.GeoDataFrame(
            {"source_sha256": [sha] * len(gdf)},
            geometry=gdf.geometry.map(to_multi),
            crs=gdf.crs,
        ).to_crs(epsg=TARGET_EPSG)
        write(clean, f"dtsc_{name}", "staging", engine)

    with engine.begin() as conn:
        add_pk = "ALTER TABLE staging.dtsc_parcels ADD PRIMARY KEY (objectid)"
        conn.execute(text(add_pk))
        counts = conn.execute(
            text(
                "SELECT status, count(*) FROM staging.dtsc_parcels "
                "GROUP BY status ORDER BY count(*) DESC"
            )
        ).all()

    print("Staged parcels by status:")
    for status, n in counts:
        print(f"  {status:<15} {n:>6}")


if __name__ == "__main__":
    main()