# How much of a matchup shot profile is additive?

Can a team's offensive shot mix and its opponent's defensive shot mix describe where attempts occur when they meet? This study uses five consistent zones over the 2003–04 through 2024–25 regular seasons.

For each team pairing, each side's profile is calculated from its other opponents. The revised implementation explicitly includes all five zones for every pairing, even when a zone has zero attempts. Otherwise, subtracting the pairing can accidentally remove real attempts against other opponents.

## What the fitted comparison says

| Zone | Offense coefficient | Defense coefficient | R² | Interaction coefficient | R² with interaction | Change in R² |
|---|---|---|---|---|---|---|
| Rim | 1.005 | 0.966 | 0.4815 | 0.018 | 0.4821 | 0.00059 |
| Paint | 0.971 | 0.917 | 0.4266 | 0.025 | 0.4272 | 0.00066 |
| Mid-range | 1.017 | 0.922 | 0.6355 | 0.025 | 0.6370 | 0.0015 |
| Corner 3 | 0.988 | 0.924 | 0.4639 | 0.094 | 0.4676 | 0.0037 |
| Above the break | 1.009 | 0.897 | 0.5545 | 0.023 | 0.5551 | 0.00064 |

Source: [who_chooses.csv](output/who_chooses.csv).

Offense and defense both enter the pooled zone regressions. Adding one product interaction contributes little additional fitted R² in this specification. That is a narrow result about this model and these coarse zones; it does not establish that basketball matchups have no interaction effects.

The coefficients and R² are fitted retrospectively across the sample. Leaving the focal pairing out of its input profiles reduces direct contamination, but the profiles still contain other games later in the same season. This is not a pregame forecast. Future-matchup claims require a chronological test with every input frozen before tipoff.

## Prediction errors and limits

| Zone | League | Offence only | Additive | R additive |
|---|---|---|---|---|
| Rim | 4.349 | 3.599 | 3.110 | 0.694 |
| Paint | 3.253 | 2.746 | 2.440 | 0.653 |
| Mid-range | 4.437 | 2.992 | 2.660 | 0.797 |
| Corner 3 | 2.161 | 1.755 | 1.568 | 0.681 |
| Above the break | 3.733 | 2.688 | 2.467 | 0.744 |

Source: [prediction_error.csv](output/prediction_error.csv).

Errors are mean absolute differences in shot-zone share, in percentage points. Coefficients are unitless.

The residuals identify pairings for closer review. Coaching scheme, personnel availability, action type and shot-clock pressure are not fully represented by five zones. Teams also meet in different schedule and rotation contexts.

## Basketball use

Use the additive comparison as a baseline for a scouting question: where does the matchup deviate from each team's usual distribution? Inspect the relevant possessions and explain any recommendation with that evidence. A model's weak interaction term is not a reason to ignore personnel or coverage.

The historical atlas is a descriptive illustration for the teams and season named in the output. It should not be presented as a current scouting report.


## Reproduce

The historical analysis used Python 3.12 with the pinned dependencies below. From this repository:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make fetch-data PY=python
make all PY=python
make report site PY=python
```

`make all` verifies source hashes before running the analyses in order. A missing or changed input stops the build. Data downloads need network access; article rendering uses the included result tables. See [the source manifest](data/source_manifest.json), [method notes](docs/method.md) and [current validation record](VALIDATION_CURRENT.md) for the distinction between a source rebuild and checks of delivered outputs.

Season keys in CSV files use the **ending year**: `2025` means 2024–25. Display tables use full season labels. The MIT license covers code; third-party data retain their providers' rights and terms.

[Portfolio](https://github.com/jmsmarrelli/basketball-analytics) · [AI assistance and provenance](PROVENANCE.md)
