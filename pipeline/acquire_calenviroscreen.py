"""Acquire CalEnviroScreen 5.0 results (file geodatabase) and data dictionary

Publisher:   California Office of Environmental Health Hazard Assessment (OEHHA)
Released:    2026-07-01 (final version)
Dataset:     https://data.ca.gov/dataset/calenviroscreen-5-0
Methodology: https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-50
"""

from download import download

DATASET = "https://data.ca.gov/dataset/72b28c84-ceac-4886-9f71-d422470d2223"

RESULTS_GDB = (
    f"{DATASET}/resource/64a0fdd4-ccb1-4bfb-ba41-22c4ee2f3e14"
    "/download/calenviroscreen50results_f_070126.gdb.zip"
)
DATA_DICTIONARY = (
    f"{DATASET}/resource/31ddb21a-44bb-4cb0-81d8-6e2f80ee359d"
    "/download/final-calenviroscreen-5.0-data-dictionary.pdf"
)

if __name__ == "__main__":
    download(source="calenviroscreen", url=RESULTS_GDB)
    download(source="calenviroscreen", url=DATA_DICTIONARY)
