# Data

One CSV per season at `data/raw/NBA_<season>_Shots.csv`, where `<season>` is the
year the season ended: `NBA_2025_Shots.csv` is 2024-25.

## Getting the files

```bash
git clone --depth 1 https://github.com/DomSamangy/NBA_Shots_04_24.git /tmp/nba_shots
mkdir -p data/raw
for z in /tmp/nba_shots/NBA_*_Shots.csv.zip; do unzip -o -q "$z" -d data/raw/; done
```

About 850 MB unzipped, twenty-two seasons. `data/raw/` and `data/processed/` are
gitignored; everything the analysis cites is written to `output/` and committed.

The mirror currently ends with 2024-25 and carries the regular season only.
Nothing here is about a playoff series, which is worth stating twice in a project
whose subject is matchups.

## The unit

A **pairing** is one team's offense against one team's defense in one season —
the three or four games they played, from one side. Two teams produce two
pairings. Twenty-two seasons produce 17,775 of them with at least 150 attempts,
at a median of 227 attempts each.

That number is the constraint the whole project works inside. 227 attempts is
enough to say where the shots came from and nowhere near enough to say whether
they went in.

## Why the five coarse zones

Two defects in these files make anything finer unusable across the sample. The
action-type vocabulary was rewritten between 2007 and 2009 — "pull-up jump shot"
does not exist in the 2003-04 file — and shot coordinates were recorded
differently before 2010-11, with three season files published on a different
scale entirely. Both are documented at length in the sibling `nba-shot-value`
repository.

The five `BASIC_ZONE` labels have meant the same thing throughout. They are all
this project reads, and it reads neither `ACTION_TYPE` nor `LOC_X`.

## Filters applied in stage 1

Heaves — 30 feet or more with two seconds or less on the clock — and backcourt
attempts, 18,735 rows across the sample. Neither is a shot anybody chose, and
neither belongs in a description of what a defense did.

## Columns used

| Column | Used for |
|---|---|
| `SEASON_1` | the season, labeled by ending year |
| `GAME_ID` | counting games in a pairing |
| `TEAM_NAME`, `HOME_TEAM`, `AWAY_TEAM` | who shot, and therefore who defended |
| `BASIC_ZONE` | the five zones |
| `SHOT_TYPE`, `SHOT_MADE` | points, and conversion |
| `SHOT_DISTANCE`, `QUARTER`, `MINS_LEFT`, `SECS_LEFT` | the heave filter |
