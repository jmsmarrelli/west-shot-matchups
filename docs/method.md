# Method notes

The leave-one-out split, why the interaction test is the point of the project,
and what a three-game sample can and cannot measure.

## The unit and its size

A pairing is one team's offense against one team's defense in one season. Two
teams meet three or four times, which is about 227 attempts from each side.
17,775 pairings clear the 150-attempt floor.

Everything in this project is shaped by that number. 227 attempts pins a zone
share to within a couple of percentage points and pins a field goal percentage to
within nothing at all, which is why the location work is a result and the
conversion work is a caveat.

## Leave the pairing out

The obvious version of this test regresses a pairing's shot mix on the two teams'
season profiles. It is wrong, and not by a rounding error.

A team's season profile contains the three or four games against this opponent.
Predicting those games from an average that includes them is partly predicting
them from themselves, and at four games in eighty-two the leakage is enough to
inflate:

`output/leakage_check.csv` runs both versions side by side:

| | With the pairing in | With it left out |
|---|---|---|
| Rim, R² | 0.546 | **0.482** |
| Mid-range, R² | 0.680 | **0.636** |
| Above the break, defense coefficient | 1.002 | **0.897** |
| Conversion, offense coefficient | 0.991 | **0.852** |
| Conversion, defense coefficient | 0.980 | **0.810** |

The conversion row is the striking one. With the pairing left in, conversion looks
like it carries in full; with it taken out, about a sixth of it is gone. Every
number in this repository is the leave-one-out version.

`matchup.leave_pairing_out` does the subtraction on counts, zone by zone, before
any share is computed, which is the only way to get it right — subtracting shares
would be wrong by the difference in sample sizes.

## The interaction test

This is what the project is for.

The additive model says a pairing's deviation from league is the offense's usual
deviation plus the defense's usual deviation. A **matchup effect** would be
something on top of that: a rim-heavy offense meeting a rim-denying defense
ending up somewhere other than the sum, because a strength meets a strength.

The test adds one term per zone — the product of the two deviations, scaled by
100 so the coefficient reads next to the others:

    actual deviation = a x (offense) + b x (defense) + c x (offense x defense)

If `c` were meaningfully non-zero, matchups would be more than arithmetic and
every scouting report that adds two profiles would be leaving something out. It
is not. R² gains 0.0006, 0.0007, 0.0015, 0.0054 and 0.0006 across the five zones.

**What a null here does and does not license.** It says that at the level of a
zone share over a whole season of pairings, there is no interaction to find. It
does not say that no coach has ever taken away a specific action, or that a
seven-game series with a shortened rotation behaves like a three-game regular
season sample. Both of those are outside what this data can reach.

## The asymmetry

The offensive coefficients average 0.996 across the five zones and the defensive
ones 0.922. Both blocks are estimated from the same number of attempts, so the
usual attenuation story does not obviously explain a gap in one direction, and it
is consistent in all five zones.

The natural reading is that an offense takes a little more of its identity into a
given game than a defense does, which is what you would expect if the offense
picks the action and the defense responds to it. It is a small effect and this
project does not push on it further; the honest summary is "roughly half each,
with the offense marginally ahead".

## The conversion result

The same test on whether the shots went in returns coefficients of 0.85 and 0.81
and an R² of 0.19. The R² is not the interesting number.

At 227 attempts and a league make rate near 46%, the standard deviation a field
goal percentage acquires from sampling alone is about 0.034. The observed spread
across pairings is 0.037. So **about 84% of the variance in a pairing's
conversion is the sample size** — and that estimate is conservative, because it
treats attempts as independent coin flips with a common rate, which understates
the true variance.

There is no version of this project that measures matchup conversion effects.
Nothing is priced with it, and every number in the atlas uses league conversion
in each zone.

## What the atlas is, given all that

For a pairing, the predicted zone shares are league plus both deviations,
renormalised so the five still sum to one. Priced at the season's league points
per attempt in each zone, that gives the shot quality of the matchup in points
per 100 attempts.

**One consequence is worth stating because it looks like a bug.** Under an
additive model with no interaction, a defense moves every offense's shot quality
by the same amount, so a table of "how much does this defense hurt this offense"
has an identical column for one side of it. That is the additive result restated,
not a coding error, and it is why the headline figure shows the two sides'
*levels* rather than their shifts.

## Where this is weakest

**Regular season, and shot location only.** No conversion, no free throws, no
turnovers, no possessions. The attempt side of a matchup is the subject of the
sibling `okc-defence` repository and is deliberately not combined here, because
combining them needs a possession count neither file has.

**A pairing is not a matchup plan.** Three or four games in October and March
against a healthy roster is not a seven-game series in May against a shortened
one. The additive result is established on the former and the atlas is applied to
a question about the latter, which is a real gap and is the reason the atlas is
presented as a description rather than a projection.

**Zone shares are coarse.** Two teams can have identical five-zone profiles and
completely different offenses. The coarseness is forced — the finer descriptions
in these files are not comparable across the sample — and it means this
instrument cannot see a scheme, only where the ball ended up.

**Home and away are pooled.** A pairing's three or four games are not split
evenly between the two buildings, and nothing here adjusts for it.
