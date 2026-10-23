"""Stage 2 - test the additive matchup model, then use it on the Western tier.

    python src/run_02_matchups.py

Writes output/who_chooses.csv, output/prediction_error.csv,
output/conversion_check.csv, output/leakage_check.csv, output/profiles.csv,
output/atlas.csv,
output/matchup_edge.csv and figures 01-05.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (ATLAS_SEASON, CONTENDERS, FIG, FULL_NAME, MIN_PAIR_ATT,  # noqa: E402
                    OUT, PROC, SEASONS, SUBJECT)
import matchup as M  # noqa: E402
import style as S  # noqa: E402

S.apply()

SHORT = {"share_Restricted Area": "Rim", "share_In The Paint (Non-RA)": "Paint",
         "share_Mid-Range": "Mid-range", "share_Corner 3": "Corner 3",
         "share_Above the Break 3": "Above the break"}


def season_label(season: int) -> str:
    return f"{season - 1}-{str(season)[2:]}"


def leakage_check(pairs: pd.DataFrame, loo: pd.DataFrame, league: pd.DataFrame,
                  od: pd.DataFrame, dd: pd.DataFrame) -> pd.DataFrame:
    """The same regressions run both ways, so the cost of leakage is a number.

    Version A uses each team's whole-season profile, which contains the games
    being predicted. Version B leaves them out. The gap between them is what a
    four-per-cent overlap is worth, and it is larger than anything else this
    project measures.
    """
    full = (M.wide_shares(pairs, ["season", "offence", "defence"])
            .rename(columns={z: f"actual_{z}" for z in M.SHARE}))
    full = full[full["att"] >= MIN_PAIR_ATT]
    full = (full.merge(od, left_on=["season", "offence"], right_on=["season", "team"])
            .drop(columns="team")
            .merge(dd, left_on=["season", "defence"], right_on=["season", "team"],
                   suffixes=("", "_d")).drop(columns="team")
            .merge(league, on="season"))

    rows = []
    for z in M.SHARE:
        lg = full[f"{z}_lg"].to_numpy()
        y = full[f"actual_{z}"].to_numpy() - lg
        X = np.column_stack([full[f"off_{z}"], full[f"def_{z}"], np.ones(len(full))])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        rows.append({"quantity": SHORT[z], "leakage": "season profile includes the pairing",
                     "offence_coef": beta[0], "defence_coef": beta[1],
                     "r2": float(1 - np.var(y - X @ beta) / np.var(y))})
    clean = M.who_chooses(loo, league)
    for _, r in clean.iterrows():
        rows.append({"quantity": SHORT[f"share_{r['zone']}"],
                     "leakage": "pairing left out",
                     "offence_coef": r["offence_coef"],
                     "defence_coef": r["defence_coef"], "r2": r["r2"]})
    return pd.DataFrame(rows).sort_values(["quantity", "leakage"])


def prediction_error(d: pd.DataFrame, league: pd.DataFrame) -> pd.DataFrame:
    """How far each of three guesses lands from what actually happened.

    League: assume every pairing looks like the league. Offence only: assume the
    offence gets its way. Additive: both sides, added. Mean absolute error in
    percentage points of share, and every guess is built from the rest of the
    season rather than from the games being predicted.
    """
    d = d.merge(league, on="season")
    rows = []
    for z in M.SHARE:
        lg = d[f"{z}_lg"]
        a = d[f"actual_{z}"]
        o = d[f"off_{z}"] - lg
        f = d[f"def_{z}"] - lg
        pred = np.clip(lg + o + f, 1e-4, None)
        rows.append({
            "zone": SHORT[z],
            "league": float(100 * (a - lg).abs().mean()),
            "offence_only": float(100 * (a - lg - o).abs().mean()),
            "additive": float(100 * (a - pred).abs().mean()),
            "r_additive": float(np.corrcoef(a - lg, pred - lg)[0, 1]),
        })
    return pd.DataFrame(rows)


def conversion_leakage(pairs: pd.DataFrame) -> pd.DataFrame:
    """Conversion additivity with and without the pairing in the season average."""
    key = ["season", "offence", "defence"]
    g = (pairs.groupby(key, observed=True)
         .agg(made=("made", "sum"), att=("att", "sum")).reset_index())
    off_tot = (pairs.groupby(["season", "offence"], observed=True)
               .agg(o_made=("made", "sum"), o_att=("att", "sum")).reset_index())
    def_tot = (pairs.groupby(["season", "defence"], observed=True)
               .agg(d_made=("made", "sum"), d_att=("att", "sum")).reset_index())
    lg = (pairs.groupby("season", observed=True)
          .agg(l_made=("made", "sum"), l_att=("att", "sum")).reset_index())
    lg["fg_lg"] = lg["l_made"] / lg["l_att"]
    p = (g.merge(off_tot, on=["season", "offence"]).merge(def_tot, on=["season", "defence"])
         .merge(lg[["season", "fg_lg"]], on="season"))
    p = p[p["att"] >= MIN_PAIR_ATT].copy()
    p["fg"] = p["made"] / p["att"]

    rows = []
    for label, sub in (("season profile includes the pairing", False),
                       ("pairing left out", True)):
        if sub:
            o = (p["o_made"] - p["made"]) / (p["o_att"] - p["att"]) - p["fg_lg"]
            f = (p["d_made"] - p["made"]) / (p["d_att"] - p["att"]) - p["fg_lg"]
        else:
            o = p["o_made"] / p["o_att"] - p["fg_lg"]
            f = p["d_made"] / p["d_att"] - p["fg_lg"]
        y = (p["fg"] - p["fg_lg"]).to_numpy()
        X = np.column_stack([o, f, np.ones(len(p))])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        rows.append({"quantity": "Conversion", "leakage": label,
                     "offence_coef": beta[0], "defence_coef": beta[1],
                     "r2": float(1 - np.var(y - X @ beta) / np.var(y))})
    return pd.DataFrame(rows)


def conversion_check(pairs: pd.DataFrame) -> pd.DataFrame:
    """The same additivity test on whether the shots went in.

    Also leave-the-pairing-out, and it comes back with the same answer and a much
    smaller R-squared. That is not the model failing. Three or four games is two
    hundred-odd attempts, and the sampling noise in a field goal percentage over
    two hundred attempts is twice the size of the entire spread of team ability.
    The coefficients are what to read here; the R-squared is a statement about
    the sample size.
    """
    key = ["season", "offence", "defence"]
    g = (pairs.groupby(key, observed=True)
         .agg(made=("made", "sum"), att=("att", "sum")).reset_index())
    off_tot = (pairs.groupby(["season", "offence"], observed=True)
               .agg(o_made=("made", "sum"), o_att=("att", "sum")).reset_index())
    def_tot = (pairs.groupby(["season", "defence"], observed=True)
               .agg(d_made=("made", "sum"), d_att=("att", "sum")).reset_index())
    lg = (pairs.groupby("season", observed=True)
          .agg(l_made=("made", "sum"), l_att=("att", "sum")).reset_index())
    lg["fg_lg"] = lg["l_made"] / lg["l_att"]

    p = (g.merge(off_tot, on=["season", "offence"])
         .merge(def_tot, on=["season", "defence"])
         .merge(lg[["season", "fg_lg"]], on="season"))
    p = p[p["att"] >= MIN_PAIR_ATT].copy()
    p["fg"] = p["made"] / p["att"]
    p["off_fg"] = (p["o_made"] - p["made"]) / (p["o_att"] - p["att"]) - p["fg_lg"]
    p["def_fg"] = (p["d_made"] - p["made"]) / (p["d_att"] - p["att"]) - p["fg_lg"]

    y = (p["fg"] - p["fg_lg"]).to_numpy()
    X = np.column_stack([p["off_fg"], p["def_fg"], np.ones(len(p))])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r2 = float(1 - np.var(y - X @ beta) / np.var(y))

    # How much of the spread in a pairing's field goal percentage is just the
    # sample size. Treating attempts as independent coin flips understates the
    # true variance a little - a pairing's shots are not identically
    # distributed - so this is a lower bound on the noise and the share below is
    # a conservative one.
    pbar = float(p["made"].sum() / p["att"].sum())
    noise_var = float((pbar * (1 - pbar) / p["att"]).mean())
    observed_var = float(y.var())
    return pd.DataFrame([{
        "pairings": len(p), "median_attempts": int(p["att"].median()),
        "offence_coef": beta[0], "defence_coef": beta[1], "r2": r2,
        "observed_sd": float(np.sqrt(observed_var)),
        "sampling_noise_sd": float(np.sqrt(noise_var)),
        "noise_share_of_variance": float(min(noise_var / observed_var, 1.0)),
    }])


def atlas(od: pd.DataFrame, dd: pd.DataFrame, league: pd.DataFrame,
          zone_pps: pd.Series, season: int, teams: list[str]) -> pd.DataFrame:
    """Every ordered pairing among a set of teams, priced."""
    rows = []
    lg = league[league["season"] == season].iloc[0]
    base = np.array([lg[f"{z}_lg"] for z in M.SHARE])
    pps = np.array([zone_pps[z.replace("share_", "")] for z in M.SHARE])
    for a in teams:
        oa = od[(od["season"] == season) & (od["team"] == a)]
        if oa.empty:
            continue
        o = np.array([oa.iloc[0][f"off_{z}"] for z in M.SHARE])
        for b in teams:
            if a == b:
                continue
            db = dd[(dd["season"] == season) & (dd["team"] == b)]
            if db.empty:
                continue
            f = np.array([db.iloc[0][f"def_{z}"] for z in M.SHARE])
            pred = np.clip(base + o + f, 1e-4, None)
            pred = pred / pred.sum()
            own = np.clip(base + o, 1e-4, None)
            own = own / own.sum()
            row = {"season": season, "offence": a, "defence": b,
                   "xpps_matchup": float(pred @ pps),
                   "xpps_own_season": float(own @ pps),
                   "xpps_league": float(base @ pps)}
            for i, z in enumerate(M.SHARE):
                row[f"pred_{SHORT[z]}"] = pred[i]
                row[f"own_{SHORT[z]}"] = own[i]
            rows.append(row)
    d = pd.DataFrame(rows)
    # Points per 100 attempts, against what this offence usually generates and
    # against the league. Under an additive model the first of these depends only
    # on the defence, which is a result rather than a bug and is discussed in the
    # README.
    d["shift_vs_own"] = 100 * (d["xpps_matchup"] - d["xpps_own_season"])
    d["vs_league"] = 100 * (d["xpps_matchup"] - d["xpps_league"])
    return d


def fig_who_chooses(w: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    x = np.arange(len(w))
    width = 0.36
    ax.bar(x - width / 2, w["offence_coef"], width, color=S.SERIES[0], zorder=3,
           label="what the offence usually does")
    ax.bar(x + width / 2, w["defence_coef"], width, color=S.SERIES[1], zorder=3,
           label="what the defence usually does")
    ax.axhline(1, color=S.INK_3, lw=1.1, ls=(0, (4, 3)), zorder=4)
    ax.annotate("1.00: carried through in full", (len(w) - 0.5, 1.0), xytext=(6, 4),
                textcoords="offset points", fontsize=8.8, color=S.INK_3)
    for xi, v in zip(np.r_[x - width / 2, x + width / 2],
                     np.r_[w["offence_coef"], w["defence_coef"]]):
        ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=8.8, color=S.INK_2)
    ax.set_xticks(x, w["zone"])
    ax.set_ylim(0, 1.28)
    ax.set_ylabel("Coefficient in the fitted zone-share model")
    ax.set_title("Offensive and defensive profiles both contribute", loc="left")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    S.strip(ax)
    ax.grid(axis="x", visible=False)
    S.caption(fig, 'One pooled regression per zone. Inputs use each side’s other opponents in the same season, including zero-attempt zones. Coefficients are descriptive fitted associations, not causal shares of control or a chronological forecast.')
    fig.tight_layout()
    fig.savefig(FIG / "01_who_chooses.png")
    plt.close(fig)


def fig_prediction(e: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    x = np.arange(len(e))
    width = 0.26
    for i, (col, label, colour) in enumerate((
            ("league", "assume league average", S.NEUTRAL),
            ("offence_only", "assume the offence gets its way", S.SERIES[0]),
            ("additive", "add both sides", S.SERIES[1]))):
        ax.bar(x + (i - 1) * width, e[col], width, color=colour, zorder=3, label=label)
    ax.set_xticks(x, e["zone"])
    ax.set_ylabel("Mean error in a pairing's zone share\n(percentage points)")
    ax.set_title("What each assumption costs you", loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    S.strip(ax)
    ax.grid(axis="x", visible=False)
    S.caption(fig, 'Mean absolute errors for historical pairings using same-season profiles. Lower is better. The comparisons are retrospective and do not test a pregame forecast; later-season games can enter the input profiles.')
    fig.tight_layout()
    fig.savefig(FIG / "02_prediction.png")
    plt.close(fig)


def fig_profiles(od: pd.DataFrame, dd: pd.DataFrame, season: int,
                 teams: list[str]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8), sharey=True)
    zones = [SHORT[z] for z in M.SHARE]
    y = np.arange(len(teams))
    for ax, dev, side, title in ((axes[0], od, "off", "On offence"),
                                 (axes[1], dd, "def", "On defence")):
        mat = np.array([[100 * dev[(dev["season"] == season) & (dev["team"] == t)]
                         .iloc[0][f"{side}_{z}"] for z in M.SHARE] for t in teams])
        vmax = np.abs(mat).max()
        im = ax.imshow(mat, cmap=mpl.colors.LinearSegmentedColormap.from_list(
            "d", S.DIVERGING), vmin=-vmax, vmax=vmax, aspect="auto")
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                ax.text(j, i, f"{mat[i, j]:+.1f}", ha="center", va="center",
                        fontsize=8.6,
                        color=S.SURFACE if abs(mat[i, j]) > 0.62 * vmax else S.INK)
        ax.set_xticks(range(len(zones)), zones, fontsize=8.6)
        ax.set_yticks(y, [FULL_NAME.get(t, t) for t in teams], fontsize=9)
        ax.set_title(title, loc="left", fontsize=11)
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)
    S.caption(fig, f"Share of attempts against the league in {season_label(season)}, in "
                   "percentage points. On offence this is where a team likes to shoot from; on "
                   "defence it is where it lets you. Red is more than the league, blue is "
                   "less.")
    fig.tight_layout()
    fig.savefig(FIG / "03_profiles.png")
    plt.close(fig)


def fig_atlas(a: pd.DataFrame, subject: str) -> None:
    d = a[a["offence"] == subject].set_index("defence")
    order = [t for t in CONTENDERS if t in d.index]
    d = d.loc[order]
    zones = [SHORT[z] for z in M.SHARE]
    mat = np.array([[100 * (d.loc[t, f"pred_{z}"] - d.loc[t, f"own_{z}"]) for z in zones]
                    for t in order])
    fig, ax = plt.subplots(figsize=(9.0, 4.2))
    vmax = max(np.abs(mat).max(), 1.0)
    ax.imshow(mat, cmap=mpl.colors.LinearSegmentedColormap.from_list("d", S.DIVERGING),
              vmin=-vmax, vmax=vmax, aspect="auto")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:+.1f}", ha="center", va="center", fontsize=9,
                    color=S.SURFACE if abs(mat[i, j]) > 0.62 * vmax else S.INK)
    ax.set_xticks(range(len(zones)), zones, fontsize=9)
    ax.set_yticks(range(len(order)),
                  [f"{FULL_NAME.get(t, t)}   {d.loc[t, 'shift_vs_own']:+.2f}"
                   for t in order], fontsize=9)
    ax.set_title(f"What each defence does to {FULL_NAME.get(subject, subject)}'s shot chart",
                 loc="left")
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    S.caption(fig, "Percentage points of shot share moved against what this offence generates on "
                   "an average night, with the value of the whole change in points per 100 "
                   "attempts beside each opponent. Priced at league conversion in each zone, so "
                   "it is a statement about where the shots come from and not about who makes "
                   "them.")
    fig.tight_layout()
    fig.savefig(FIG / "04_atlas.png")
    plt.close(fig)


def fig_edge(a: pd.DataFrame, subject: str) -> None:
    """The level each side's shot chart is worth in each matchup, not the shift.

    The shift is the wrong thing to draw once the interaction has been rejected:
    a defence moves every offence by the same amount, so a chart of shifts on the
    defensive side would be six identical bars. The levels are what differ, and
    the gap between them is the matchup.
    """
    ours = a[a["offence"] == subject].set_index("defence")
    theirs = a[a["defence"] == subject].set_index("offence")
    order = [t for t in CONTENDERS if t in ours.index and t in theirs.index]
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    y = np.arange(len(order))
    width = 0.36
    us = np.array([100 * ours.loc[t, "xpps_matchup"] for t in order])
    them = np.array([100 * theirs.loc[t, "xpps_matchup"] for t in order])
    lg = 100 * float(a["xpps_league"].iloc[0])
    ax.barh(y + width / 2, us - lg, width, color=S.SPURS, zorder=3,
            label=f"{FULL_NAME.get(subject, subject)}'s shot chart in the matchup")
    ax.barh(y - width / 2, them - lg, width, color=S.SILVER, zorder=3,
            label="theirs")
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=4)
    for i, t in enumerate(order):
        for val, off in ((us[i] - lg, width / 2), (them[i] - lg, -width / 2)):
            ax.text(val + np.sign(val) * 0.05, i + off, f"{val:+.2f}", va="center",
                    ha="left" if val >= 0 else "right", fontsize=8.8, color=S.INK_2)
    ax.set_yticks(y, [f"{FULL_NAME.get(t, t)}   {us[i] - them[i]:+.2f}"
                      for i, t in enumerate(order)])
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_xlabel("Shot quality against league average, points per 100 attempts")
    ax.set_title("What each shot chart is worth in the matchup", loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    S.strip(ax, keep=("bottom",))
    ax.grid(axis="y", visible=False)
    S.caption(fig, "Both sides of each pairing, priced at league conversion in each zone, with "
                   "the difference between them beside the opponent's name. This is a statement "
                   "about where the shots would come from and not about who makes them: a team "
                   "that generates worse locations and shoots better can win the game and lose "
                   "this chart.")
    fig.tight_layout()
    fig.savefig(FIG / "05_edge.png")
    plt.close(fig)


def main() -> None:
    pairs = pd.read_csv(PROC / "pair_profiles.csv")
    profiles = pd.read_csv(PROC / "season_profiles.csv")
    league_zones = pd.read_csv(OUT / "league_zones.csv")

    league = M.league_frame(league_zones)
    off = M.wide_shares(profiles[profiles["side"] == "off"], ["season", "team"])
    dfn = M.wide_shares(profiles[profiles["side"] == "def"], ["season", "team"])
    od = M.deviations(off, league, "off")
    dd = M.deviations(dfn, league, "def")

    loo = M.leave_pairing_out(pairs)
    loo = loo[loo["att"] >= MIN_PAIR_ATT]

    w = M.who_chooses(loo, league)
    w["zone"] = w["zone"].map(lambda z: SHORT[f"share_{z}"])
    w.round(5).to_csv(OUT / "who_chooses.csv", index=False)

    err = prediction_error(loo, league)
    err.round(4).to_csv(OUT / "prediction_error.csv", index=False)

    conv = conversion_check(pairs)
    conv.round(5).to_csv(OUT / "conversion_check.csv", index=False)

    leak = pd.concat([leakage_check(pairs, loo, league, od, dd),
                      conversion_leakage(pairs)], ignore_index=True)
    leak.round(5).to_csv(OUT / "leakage_check.csv", index=False)

    teams = [SUBJECT] + CONTENDERS
    prof = od.merge(dd, on=["season", "team"])
    prof[prof["season"] == ATLAS_SEASON].round(5).to_csv(OUT / "profiles.csv", index=False)

    zone_pps = (league_zones[league_zones["season"] == ATLAS_SEASON]
                .set_index("zone5")["pps"])
    a = atlas(od, dd, league, zone_pps, ATLAS_SEASON, teams)
    a.round(5).to_csv(OUT / "atlas.csv", index=False)

    edge = a[((a["offence"] == SUBJECT) | (a["defence"] == SUBJECT))].copy()
    edge.round(5).to_csv(OUT / "matchup_edge.csv", index=False)

    fig_who_chooses(w)
    fig_prediction(err)
    fig_profiles(od, dd, ATLAS_SEASON, teams)
    fig_atlas(a, SUBJECT)
    fig_edge(a, SUBJECT)

    print(f"{len(loo):,} team pairings with {MIN_PAIR_ATT}+ attempts, "
          f"median {int(loo['att'].median())}\n")
    print("--- who chooses where the shot comes from ---")
    print(w[["zone", "offence_coef", "defence_coef", "r2", "interaction_coef",
             "r2_with_interaction", "r2_gain"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    print("\n--- mean error in a pairing's zone share, percentage points ---")
    print(err.to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print("\n--- what leaving the pairing in the season average would have bought ---")
    print(leak.pivot_table(index="quantity", columns="leakage",
                           values=["offence_coef", "defence_coef", "r2"])
          .round(3).to_string())

    print("\n--- the same test on conversion ---")
    print(conv.T.to_string(header=False, float_format=lambda v: f"{v:.4f}"))

    print(f"\n--- {season_label(ATLAS_SEASON)}: what each defence does to "
          f"{SUBJECT}'s shot chart ---")
    ours = a[a["offence"] == SUBJECT].set_index("defence")
    cols = [f"pred_{SHORT[z]}" for z in M.SHARE]
    own = ours.iloc[0][[f"own_{SHORT[z]}" for z in M.SHARE]].to_numpy()
    show = ours[cols].copy()
    for i, c in enumerate(cols):
        show[c] = 100 * (show[c] - own[i])
    show["points per 100"] = ours["shift_vs_own"]
    print(show.round(2).to_string())

    print(f"\n--- and what {SUBJECT} does to theirs ---")
    theirs = a[a["defence"] == SUBJECT].set_index("offence")
    print(theirs[["shift_vs_own", "xpps_matchup", "xpps_own_season"]]
          .to_string(float_format=lambda v: f"{v:.4f}"))


if __name__ == "__main__":
    main()
