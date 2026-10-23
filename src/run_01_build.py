"""Stage 1 - twenty-two seasons of shots into pairwise and season profiles.

    python src/run_01_build.py

Every attempt gets the team that took it and the team that faced it, so the same
rows produce three tables: what each team did on offence, what it allowed on
defence, and what happened in each specific pairing.

Writes data/processed/season_profiles.csv, data/processed/pair_profiles.csv,
output/league_zones.csv and output/coverage.csv.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import HEAVE_DIST, HEAVE_SECS, OUT, PROC, RAW, SEASONS  # noqa: E402
import matchup as M  # noqa: E402

COLS = ["SEASON_1", "GAME_ID", "TEAM_NAME", "HOME_TEAM", "AWAY_TEAM",
        "SHOT_MADE", "SHOT_TYPE", "BASIC_ZONE", "SHOT_DISTANCE",
        "QUARTER", "MINS_LEFT", "SECS_LEFT"]


def team_abbreviations(df: pd.DataFrame) -> pd.Series:
    """A team's own code is the one present in every game it played."""
    pairs = df[["TEAM_NAME", "HOME_TEAM", "AWAY_TEAM"]].drop_duplicates()
    out = {}
    for team, grp in pairs.groupby("TEAM_NAME", observed=True):
        common = set(grp.iloc[0][["HOME_TEAM", "AWAY_TEAM"]])
        for _, row in grp.iloc[1:].iterrows():
            common &= {row["HOME_TEAM"], row["AWAY_TEAM"]}
            if len(common) == 1:
                break
        if len(common) != 1:
            raise ValueError(f"could not resolve an abbreviation for {team}: {common}")
        out[team] = common.pop()
    return pd.Series(out, name="team_abbrev")


def load_season(season: int) -> tuple[pd.DataFrame, dict]:
    path = RAW / f"NBA_{season}_Shots.csv"
    if not path.exists():
        raise SystemExit(f"missing {path}. See data/README.md.")
    raw = pd.read_csv(path, usecols=COLS, low_memory=False)

    abbrev = team_abbreviations(raw)
    team = raw["TEAM_NAME"].map(abbrev)
    opponent = np.where(team == raw["HOME_TEAM"], raw["AWAY_TEAM"], raw["HOME_TEAM"])

    secs_left = raw["MINS_LEFT"] * 60 + raw["SECS_LEFT"]
    drop = ((raw["SHOT_DISTANCE"] >= HEAVE_DIST) & (secs_left <= HEAVE_SECS)) \
        | raw["BASIC_ZONE"].astype(str).eq("Backcourt")

    d = pd.DataFrame({
        "season": season,
        "game_id": raw["GAME_ID"].to_numpy(),
        "offence": team.to_numpy(),
        "defence": opponent,
        "zone5": M.zone5(raw["BASIC_ZONE"]),
        "made": raw["SHOT_MADE"].to_numpy().astype(int),
        "points": np.where(raw["SHOT_MADE"].to_numpy(),
                           np.where(raw["SHOT_TYPE"].eq("3PT Field Goal"), 3, 2), 0),
    })[~drop.to_numpy()]

    audit = {"season": season, "rows": int(len(raw)), "kept": int(len(d)),
             "dropped": int(drop.sum()), "games": int(d["game_id"].nunique()),
             "pairings": int(d.groupby(["offence", "defence"]).ngroups)}
    return d, audit


def main() -> None:
    frames, audit = [], []
    for season in SEASONS:
        t0 = time.time()
        d, a = load_season(season)
        frames.append(d)
        a["seconds"] = round(time.time() - t0, 1)
        audit.append(a)
        print(f"  {season}: {a['kept']:,} attempts, {a['pairings']} pairings "
              f"({a['seconds']}s)", flush=True)
    shots = pd.concat(frames, ignore_index=True)

    agg = dict(att=("points", "size"), made=("made", "sum"), pts=("points", "sum"))

    league = (shots.groupby(["season", "zone5"], observed=True).agg(**agg).reset_index())
    league["pps"] = league["pts"] / league["att"]
    league["fg"] = league["made"] / league["att"]
    league.round(6).to_csv(OUT / "league_zones.csv", index=False)

    off = (shots.groupby(["season", "offence", "zone5"], observed=True).agg(**agg)
           .reset_index().rename(columns={"offence": "team"}).assign(side="off"))
    dfn = (shots.groupby(["season", "defence", "zone5"], observed=True).agg(**agg)
           .reset_index().rename(columns={"defence": "team"}).assign(side="def"))
    pd.concat([off, dfn], ignore_index=True).to_csv(PROC / "season_profiles.csv",
                                                    index=False)

    pairs = (shots.groupby(["season", "offence", "defence", "zone5"], observed=True)
             .agg(**agg).reset_index())
    games = (shots.groupby(["season", "offence", "defence"], observed=True)["game_id"]
             .nunique().rename("games").reset_index())
    pairs = pairs.merge(games, on=["season", "offence", "defence"])
    pairs.to_csv(PROC / "pair_profiles.csv", index=False)

    cov = pd.DataFrame(audit)
    cov.to_csv(OUT / "coverage.csv", index=False)

    n_pairs = pairs.groupby(["season", "offence", "defence"]).ngroups
    print(f"\n{len(shots):,} attempts, {shots['game_id'].nunique():,} games")
    print(f"{n_pairs:,} team pairings, {games['games'].min()}-{games['games'].max()} "
          f"games each")
    print()
    print(cov.to_string(index=False))


if __name__ == "__main__":
    main()
