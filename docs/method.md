# Method and revision notes


Can a team's offensive shot mix and its opponent's defensive shot mix describe where attempts occur when they meet? This study uses five consistent zones over the 2003–04 through 2024–25 regular seasons.

For each team pairing, each side's profile is calculated from its other opponents. The revised implementation explicitly includes all five zones for every pairing, even when a zone has zero attempts. Otherwise, subtracting the pairing can accidentally remove real attempts against other opponents.

## What the fitted comparison says

[Result table](../output/who_chooses.csv)

Offense and defense both enter the pooled zone regressions. Adding one product interaction contributes little additional fitted R² in this specification. That is a narrow result about this model and these coarse zones; it does not establish that basketball matchups have no interaction effects.

The coefficients and R² are fitted retrospectively across the sample. Leaving the focal pairing out of its input profiles reduces direct contamination, but the profiles still contain other games later in the same season. This is not a pregame forecast. Future-matchup claims require a chronological test with every input frozen before tipoff.

## Prediction errors and limits

[Result table](../output/prediction_error.csv)

The residuals identify pairings for closer review. Coaching scheme, personnel availability, action type and shot-clock pressure are not fully represented by five zones. Teams also meet in different schedule and rotation contexts.

## Basketball use

Use the additive comparison as a baseline for a scouting question: where does the matchup deviate from each team's usual distribution? Inspect the relevant possessions and explain any recommendation with that evidence. A model's weak interaction term is not a reason to ignore personnel or coverage.

The historical atlas is a descriptive illustration for the teams and season named in the output. It should not be presented as a current scouting report.


The result tables are linked and rendered in the main article. Full algorithms and thresholds are in `src/`; source bytes are recorded in `data/source_manifest.json`.
