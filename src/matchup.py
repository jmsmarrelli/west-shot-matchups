"""Whether a shot chart is something a team brings or something it is given.

Every team has an offensive shot profile and every team has a defensive one, and
the natural way to guess what a particular game will look like is to add them:
start from the league's mix, add what this offense usually does to it, add what
that defense usually does to it, and see what comes out.

That guess is testable, because twenty-two seasons contain about nineteen
thousand team-pairings and each one has its own actual shot chart. The test is
worth running before anyone builds a matchup report on top of the assumption,
and it answers a second question on the way: when an offense that loves the rim
meets a defense that takes the rim away, who wins? The two coefficients in the
same regression say how much of a shot chart each side gets to choose.

The five zones are the same coarse set the sibling projects use, for the same
reason: they are the only description of a shot that means the same thing in
2003-04 and 2024-25.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ZONES = ["Restricted Area", "In The Paint (Non-RA)", "Mid-Range",
         "Corner 3", "Above the Break 3"]
SHARE = [f"share_{z}" for z in ZONES]


def zone5(zone: pd.Series) -> pd.Categorical:
    z = zone.astype(str).replace({"Left Corner 3": "Corner 3",
                                  "Right Corner 3": "Corner 3"})
    return pd.Categorical(z, categories=ZONES, ordered=True)


def wide_shares(long: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Long zone counts -> one row per key with a share column per zone."""
    tot = long.groupby(keys, observed=True)["att"].transform("sum")
    d = long.assign(share=long["att"] / tot)
    out = d.pivot_table(index=keys, columns="zone5", values="share", observed=True)
    out.columns = [f"share_{c}" for c in out.columns]
    # A pairing in which nobody took a corner three leaves a hole, not a zero.
    out = out.reindex(columns=SHARE).fillna(0.0)
    att = long.groupby(keys, observed=True)["att"].sum().rename("att")
    return out.join(att).reset_index()


def league_frame(league_zones: pd.DataFrame) -> pd.DataFrame:
    """The league's own zone shares by season, named so a merge cannot collide."""
    lg = wide_shares(league_zones.assign(team="LEAGUE"), ["season"]).drop(columns="att")
    return lg.rename(columns={z: f"{z}_lg" for z in SHARE})


def deviations(season_profile: pd.DataFrame, league: pd.DataFrame,
               side: str) -> pd.DataFrame:
    """How far a team's own profile sits from the league's, zone by zone."""
    d = season_profile.merge(league, on="season")
    for z in SHARE:
        d[f"{side}_{z}"] = d[z] - d[f"{z}_lg"]
    return d[["season", "team"] + [f"{side}_{z}" for z in SHARE]]


def additive_prediction(pairs: pd.DataFrame, off_dev: pd.DataFrame,
                        def_dev: pd.DataFrame, league: pd.DataFrame) -> pd.DataFrame:
    """League mix, plus what this offense does to it, plus what that defense does.

    Renormalised so the five shares still sum to one. The renormalisation is
    small - the deviations are a couple of percentage points each - but leaving
    it out would let a prediction quietly stop being a distribution.
    """
    d = (pairs.merge(off_dev, left_on=["season", "offense"], right_on=["season", "team"])
         .drop(columns="team")
         .merge(def_dev, left_on=["season", "defense"], right_on=["season", "team"],
                suffixes=("", "_d"))
         .drop(columns="team")
         .merge(league, on="season"))
    raw = np.column_stack([d[f"{z}_lg"] + d[f"off_{z}"] + d[f"def_{z}"] for z in SHARE])
    raw = np.clip(raw, 1e-4, None)
    raw = raw / raw.sum(axis=1, keepdims=True)
    for i, z in enumerate(SHARE):
        d[f"pred_{z}"] = raw[:, i]
    return d


def leave_pairing_out(pairs: pd.DataFrame) -> pd.DataFrame:
    """Each side's season profile with this pairing's own games taken out.

    Without this the test is rigged. A team's season shot mix contains the three
    or four games against this opponent, so predicting those games from it is
    partly predicting them from themselves. Four games in eighty-two is only
    about five per cent of the sample, and it is worth four points of R-squared,
    which is more than the interaction term this project goes on to reject.
    """
    key = ["season", "offense", "defense"]
    off_tot = (pairs.groupby(["season", "offense", "zone5"], observed=True)["att"]
               .sum().rename("off_total").reset_index())
    def_tot = (pairs.groupby(["season", "defense", "zone5"], observed=True)["att"]
               .sum().rename("def_total").reset_index())
    p = (pairs.merge(off_tot, on=["season", "offense", "zone5"])
         .merge(def_tot, on=["season", "defense", "zone5"]))
    p["off_rest"] = p["off_total"] - p["att"]
    p["def_rest"] = p["def_total"] - p["att"]

    out = None
    for col, prefix in (("att", "actual"), ("off_rest", "off"), ("def_rest", "def")):
        w = p.pivot_table(index=key, columns="zone5", values=col, observed=True)
        w = w.reindex(columns=ZONES).fillna(0.0)
        w = w.div(w.sum(axis=1), axis=0)
        w.columns = [f"{prefix}_share_{z}" for z in ZONES]
        out = w if out is None else out.join(w)
    att = pairs.groupby(key, observed=True)["att"].sum().rename("att")
    return out.join(att).reset_index()


def who_chooses(d: pd.DataFrame, league: pd.DataFrame) -> pd.DataFrame:
    """Regress what actually happened on what each side does the rest of the time.

    One regression per zone, pooled over every pairing:

        actual deviation  =  a x (the offense's deviation elsewhere)
                          +  b x (the defense's deviation elsewhere)  +  error

    If shot location were entirely the offense's choice, a would be 1 and b would
    be 0. A third fit adds the product of the two deviations, which is where a
    genuine matchup effect would live: a rim-heavy offense meeting a rim-denying
    defense should, if matchups are more than arithmetic, end up somewhere other
    than the sum of the two.
    """
    d = d.merge(league, on="season")
    rows = []
    for z in SHARE:
        lg = d[f"{z}_lg"].to_numpy()
        y = d[f"actual_{z}"].to_numpy() - lg
        o = d[f"off_{z}"].to_numpy() - lg
        f = d[f"def_{z}"].to_numpy() - lg
        X = np.column_stack([o, f, np.ones(len(d))])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r2 = float(1 - np.var(y - X @ beta) / np.var(y))
        # The interaction is scaled by 100 so its coefficient is readable next to
        # the other two rather than being a number with four leading zeros.
        Xi = np.column_stack([o, f, 100 * o * f, np.ones(len(d))])
        bi, *_ = np.linalg.lstsq(Xi, y, rcond=None)
        r2i = float(1 - np.var(y - Xi @ bi) / np.var(y))
        rows.append({
            "zone": z.replace("share_", ""),
            "offence_coef": beta[0], "defence_coef": beta[1], "r2": r2,
            "interaction_coef": bi[2], "r2_with_interaction": r2i,
            "r2_gain": r2i - r2,
        })
    return pd.DataFrame(rows)


def expected_points(shares: np.ndarray, zone_pps: np.ndarray) -> np.ndarray:
    """Points per attempt implied by a shot mix, at some set of zone values."""
    return shares @ zone_pps
