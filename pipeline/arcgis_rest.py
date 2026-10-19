"""Download every feature from an ArcGIS feature layer, with paging

Saves one GeoJSON snapshot per layer in a dated folder and records
provenance in data/manifest.jsonl, the same way download.py does.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from download import MANIFEST, PROJECT_ROOT, RAW_DIR, USER_AGENT, last_recorded

PRIVATE_DIR = PROJECT_ROOT / "data" / "private"
PAGE_SIZE = 2000  # the service's MaxRecordCount
RETRIES = 3


def _get(url: str, params: dict) -> dict:
    """GET with retries. ArcGIS can report errors inside a 200 response"""
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(
                url, params=params, timeout=60, headers={"User-Agent": USER_AGENT}
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"ArcGIS error: {data['error']}")
            return data
        except (requests.RequestException, RuntimeError) as exc:
            if attempt == RETRIES:
                raise
            wait = 2**attempt
            print(f"  attempt {attempt} failed ({exc}); retrying in {wait}s")
            time.sleep(wait)
    raise AssertionError("unreachable")


def download_feature_layer(
    source: str, layer_url: str, name: str, private: bool
) -> Path:
    """Download all features of a layer as GeoJSON (EPSG:4326)"""
    now = datetime.now(timezone.utc)
    base = PRIVATE_DIR if private else RAW_DIR
    dest = base / source / now.strftime("%Y-%m-%d") / f"{name}.geojson"
    if dest.exists():
        print(f"Already downloaded today: {dest.relative_to(PROJECT_ROOT)}")
        return dest

    info = _get(layer_url, {"f": "json"})
    last_edit_ms = info.get("editingInfo", {}).get("dataLastEditDate")
    query_url = f"{layer_url}/query"
    count_params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    expected = _get(query_url, count_params)["count"]
    print(f"{name}: server reports {expected} features")

    features: list[dict] = []
    while len(features) < expected:
        page = _get(
            query_url,
            {
                "where": "1=1",
                "outFields": "*",
                "orderByFields": "OBJECTID",  # stable order across pages
                "resultOffset": len(features),
                "resultRecordCount": PAGE_SIZE,
                "outSR": 4326,
                "f": "geojson",
            },
        )
        batch = page.get("features", [])
        if not batch:
            break
        features.extend(batch)
        print(f"  fetched {len(features)} / {expected}")

    # Truncation/duplicates
    ids = [f["properties"].get("OBJECTID", f.get("id")) for f in features]
    if len(features) != expected:
        raise RuntimeError(f"Expected {expected} features, got {len(features)}")
    if len(set(ids)) != len(ids):
        raise RuntimeError("Duplicate OBJECTIDs: paging returned overlapping pages")

    # Deterministic output, so identical data always gives an identical checksum
    text = json.dumps(
        {"type": "FeatureCollection", "features": features}, sort_keys=True
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    partial.write_text(text)
    partial.rename(dest)

    checksum = hashlib.sha256(text.encode()).hexdigest()
    previous = last_recorded(source, dest.name)
    entry = {
        "source": source,
        "filename": dest.name,
        "url": layer_url,
        "path": str(dest.relative_to(PROJECT_ROOT)),
        "private": private,
        "downloaded_at": now.isoformat(timespec="seconds"),
        "bytes": len(text.encode()),
        "sha256": checksum,
        "feature_count": len(features),
        "server_last_edit": (
            datetime.fromtimestamp(last_edit_ms / 1000, timezone.utc).isoformat()
            if last_edit_ms
            else None
        ),
        "changed_since_previous": (
            None if previous is None else previous["sha256"] != checksum
        ),
    }
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Saved {entry['path']} ({len(features)} features)")
    return dest
