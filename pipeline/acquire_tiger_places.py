"""Acquire U.S. Census TIGER/Line Places (cities and CDPs) for California

Docs: https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/tiger-geo-line.html
"""

from download import download

TIGER_YEAR = 2025
STATE_FIPS = "06"  # California
URL = (
    f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/PLACE/"
    f"tl_{TIGER_YEAR}_{STATE_FIPS}_place.zip"
)

if __name__ == "__main__":
    download(source="tiger_places", url=URL)
