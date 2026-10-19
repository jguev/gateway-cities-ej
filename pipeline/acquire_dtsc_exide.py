"""Acquire DTSC Exide layers from DTSC's public ArcGIS feature services

Traced from the Exide Cleanup map: app d8a6b586685f46f793e39759c71be3ef
-> web map c7cfedcad8e741cb996f1825137b0a84 -> operational layers.

Parcels contain APNs and addresses, so they are stored as private data.
"""

from arcgis_rest import download_feature_layer

SERVICES = "https://services3.arcgis.com/Oy2JTCD10wkoelxS/arcgis/rest/services"

LAYERS = [
    ("parcels", f"{SERVICES}/DTSCCleanupMay26/FeatureServer/2", True),
    ("pia_boundary", f"{SERVICES}/DTSCCleanupMay24English/FeatureServer/2", False),
    ("facility", f"{SERVICES}/DTSCCleanupMay24English/FeatureServer/3", False),
]

if __name__ == "__main__":
    for name, url, private in LAYERS:
        download_feature_layer("dtsc_exide", url, name, private=private)
