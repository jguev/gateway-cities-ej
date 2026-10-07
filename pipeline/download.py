"""
Download a source file into data/raw/ and record its provenance

Each download is saved untouched ina dated folder:
data/raw/<source>/<YYYY-MM-DD>/<filename>
and described by one line appended to data/manifest.jsonl
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

# Paths are built from this file's location, so scripts run from any folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST = PROJECT_ROOT / "data" / "manifest.jsonl"

USER_AGENT = "gateway-cities-ej/0.1 (portfolio data pipeline)"
CHUNK_SIZE = 1024 * 1024  # read 1 MB at a time


def last_recorded(source: str, filename: str) -> dict | None:
    """Return the most recent manifest entry for this source and file, if any."""
    if not MANIFEST.exists():
        return None
    latest = None
    with MANIFEST.open() as f:
        for line in f:
            entry = json.loads(line)
            if entry["source"] == source and entry["filename"] == filename:
                latest = entry
    return latest


def latest_path(source: str, filename: str) -> Path:
    """Return the path of the most recent download of a file, per the manifest."""
    entry = last_recorded(source, filename)
    if entry is None:
        raise FileNotFoundError(
            f"No download recorded for {source}/{filename}. "
            f"Run pipeline/acquire_{source}.py first."
        )
    return PROJECT_ROOT / entry["path"]


def download(source: str, url: str) -> Path:
    """Download url into a dated raw folder, record provenance, return the path."""
    filename = Path(urlparse(url).path).name
    now = datetime.now(timezone.utc)
    dest_dir = RAW_DIR / source / now.strftime("%Y-%m-%d")
    dest = dest_dir / filename

    # Running twice on the same day does nothing the second time.
    if dest.exists():
        print(f"Already downloaded today: {dest.relative_to(PROJECT_ROOT)}")
        return dest

    dest_dir.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    hasher = hashlib.sha256()
    size = 0

    try:
        with requests.get(
            url, stream=True, timeout=60, headers={"User-Agent": USER_AGENT}
        ) as resp:
            resp.raise_for_status()  # stop on 404, 500, etc.

            # Catch the "got an error page instead of data" failure.
            if "text/html" in resp.headers.get("Content-Type", ""):
                raise ValueError(f"Expected a data file but got an HTML page: {url}")

            with partial.open("wb") as f:
                for chunk in resp.iter_content(CHUNK_SIZE):
                    f.write(chunk)
                    hasher.update(chunk)
                    size += len(chunk)
            last_modified = resp.headers.get("Last-Modified")
    except Exception:
        partial.unlink(missing_ok=True)  # never leave a half-downloaded file
        raise

    # Rename only after the download fully succeeds.
    partial.rename(dest)

    checksum = hasher.hexdigest()
    previous = last_recorded(source, filename)
    entry = {
        "source": source,
        "filename": filename,
        "url": url,
        "path": str(dest.relative_to(PROJECT_ROOT)),
        "downloaded_at": now.isoformat(timespec="seconds"),
        "bytes": size,
        "sha256": checksum,
        "server_last_modified": last_modified,
        "changed_since_previous": (
            None if previous is None else previous["sha256"] != checksum
        ),
    }
    with MANIFEST.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"Saved {entry['path']} ({size / 1e6:.1f} MB)")
    changed = entry["changed_since_previous"]
    print(f"sha256 {checksum[:16]}...  changed since previous: {changed}")
    return dest
