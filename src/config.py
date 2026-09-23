"""Paths, seasons, and the teams the atlas is pointed at."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
OUT = ROOT / "output"

for d in (RAW, PROC, FIG, OUT):
    d.mkdir(parents=True, exist_ok=True)

# Season label is the year the season ends: 2025 == 2024-25, which is where the
# public shot mirror this project reads currently stops.
FIRST_SEASON = 2004
LAST_SEASON = 2025
SEASONS = list(range(FIRST_SEASON, LAST_SEASON + 1))

SUBJECT = "SAS"
SUBJECT_NAME = "San Antonio Spurs"
ATLAS_SEASON = 2025

# The Western teams a rising San Antonio would meet in a seven-game series.
CONTENDERS = ["OKC", "DEN", "HOU", "MIN", "LAL", "GSW"]

FULL_NAME = {
    "SAS": "San Antonio", "OKC": "Oklahoma City", "DEN": "Denver",
    "HOU": "Houston", "MIN": "Minnesota", "LAL": "LA Lakers", "GSW": "Golden State",
}

HEAVE_DIST = 30.0
HEAVE_SECS = 2.0

# A pairing needs this many attempts on a side before it is scored. Two teams
# play each other three or four times a season, which is about 250 attempts -
# enough to measure where the shots came from and nowhere near enough to measure
# whether they went in.
MIN_PAIR_ATT = 150

SEED = 20240117
