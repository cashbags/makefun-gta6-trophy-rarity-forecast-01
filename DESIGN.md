# DESIGN.md — forecasting GTA VI's trophy earn rates a week after launch

## The problem in one paragraph

Grand Theft Auto VI released 19 November 2026 on PS5 and Xbox, and no console
maker publishes how far players get. The contest counts each PS5 trophy's earn
rate on Exophase's trophy page: the percent of the players Exophase tracks who
have earned it. The program sees every read of that page up to the checkpoint
and must forecast all 55 trophies' rates at the target as five quantiles each,
scored by mean pinball loss on the logit scale. A forecast whose five quantiles
are equal scores exactly its mean absolute logit error, so the median has to be
right *and* the spread honest: too narrow pays for every trophy outside it, too
wide pays at every trophy.

## What the launch-night reads show

The kit's practice cases carry 7–8 reads, all identical: 638 players tracked,
rates 0.63–2.04% (one trophy at 100%). The rules record what happened next:
the page sat unchanged from 23:48 UTC to 04:00 UTC, then refreshed at 04:30
UTC — 3,868 players tracked, every rate but the 100% one lower. A live fetch
of the page on 19 Nov 12:44 UTC (the held-out read in CHECK.md) shows rates
of 0.10–1.16%, chapter 1 at 0.49% (was 1.25%), the platinum at 0.10% (was
0.63%). Two regularities drive the design:

1. RATES ARE RATIOS, AND BOTH SIDES JUMP. The refresh moved the denominator
   6x while earners barely moved, so rates fell ~5x in one step. Forecasting
   the ratio directly confuses the two motions. The program splits them:
   earners E_i(t) = rate_i(t) x N(t) / 100, forecasts E_i and N separately on
   log time, and divides. Earners only grow; tracked players only grow; the
   ratio can fall, rise, or both in sequence, which is what launch week does.
2. EARLY RATES ARE SMALL COUNTS. The platinum's 0.63% of 638 players is 4
   earners; the same 4 earners at 3,868 tracked is 0.10%. A trophy with 4
   earners is ±0.5 logit before anything else moves, so the spread carries an
   explicit 1/sqrt(E) count-noise term, capped at 0.6.

## The model

For each trophy, log E_i and log N are each regressed on log(1 + hours since
the first read) over the last 24 h of reads (all reads when shorter), slopes
damped 0.7x toward flat (N clamped to [0, 1.2], E to [0, 2]) and E's slope
shrunk halfway toward the median slope across trophies — small earner counts
are noisy, and the cross-trophy median stabilises them. N(T) is capped at 4x
the last read; E_i(T) at 99% of N(T), floored at its last value. The median
rate is 100 x E_i(T) / N(T). Flat history fits nothing (a constant series is
treated as no fit, not a perfect one), so the median stays at the last rate
and the spread below carries the refresh risk — the honest answer when the
page has not moved yet. The one trophy at 100% stayed 100% through a 6x jump
in N, so it is forecast near 100% with a narrow band instead of through the
ratio machinery. A trophy nobody holds yet gets half an earner, not zero.

## The spread

Four logit-sigma terms, added in quadrature: trend volatility x sqrt(days),
where the volatility is the case's own — the median per-trophy log-E fit
residual (and the N fit's), floored at 0.10 and capped at the house baseline's
0.50, so a smooth history earns a narrow band and a jumpy one a wide one
(0.50 with no fit at all, as on the flat practice histories); the per-trophy
fit's residual sd; count noise 1/sqrt(E(T)); refresh risk 0.35x the median
trophy's largest |logit jump| between consecutive reads (0.20–0.70), or 0.55
when history is flat, because the first refresh is the one the reads cannot
show. Nothing is tuned to a practice score: the only numbers fixed in advance
are the 0.7 damping, the slope and growth caps, the 0.10/0.50 volatility
bounds, and the 0.35/0.55 refresh terms — all chosen from the shape of the
data before scoring, not from a practice result.

## What would change the answer

If the final case's history shows rates still falling at the deadline (tracked
players outgrowing earners), the E/N split forecasts that fall to continue,
damped; if it shows rates climbing, it forecasts the climb. The main risk is a
refresh landing just before the target read: the refresh term widens the band
for exactly that, and the median does not pretend to know which side of a
refresh the target read falls on.
