# CHECK.md — validation runs for the GTA VI trophy-rarity forecaster

All runs 19 Nov 2026, Python 3.13, entry at
`~/workspace/makefun/bounties/gta6-trophy-rarity-forecast-01/entry/main.py`.
The kit ships no practice answers, so the scored checks are a real held-out
read, simulated refresh answers, and synthetic launches (see below). The
practice cases are checked for shape, determinism and runtime only.

## 1. Real held-out read: the live Exophase page

Method: the case is `p00.in`'s history (7 flat launch-night reads, 638 players
tracked) with the checkpoint moved to 2026-11-19T12:44:00Z (horizon 584 min);
the answer is the 55 rates of the live page
`https://www.exophase.com/game/grand-theft-auto-vi-psn/trophies/` fetched at
that time (platinum 0.10%, chapter 1 0.49%, most 0.10–0.39%, one trophy 100%).
The program never saw the page. Scored with an independent Python
implementation of the rules' pinball loss; the house baselines are the kit
starter (flat) and the rules' trend baseline re-implemented from the text.
The starter was also run on the same case to cross-check the re-implementation
(it matches exactly: 1.370656).

| forecaster | loss | typical miss | 90% coverage |
| --- | --- | --- | --- |
| entry (`main.py`) | **1.036938** | 0.6791 pp | 0.073 |
| flat baseline (starter) | 1.370656 | 0.6775 pp | 0.000 |
| trend baseline | 1.370656 | 0.6775 pp | 0.000 |

The entry beats both baselines by 0.334 (24%). The medians are the same (the
flat history fits nothing, so all three sit at the last rate); the win is the
spread: the refresh-risk and count-noise terms widen the band where the
baselines' 0.5·sqrt(days) band puts every trophy outside it.

## 2. Simulated refresh answers (practice cases p00/p01)

Method: the practice answer is the refreshed page, which the kit does not
ship. The rules say the 04:30 UTC refresh took N 638 -> 3,868 and every rate
but the 100% one down; earners grew meanwhile, so the answer is simulated as
last rate x factor, factor 0.16 (earners unchanged), 0.25 (earners x1.5) and
0.40 (earners x2.4), 100% staying 100%. p00 and p01 give identical forecasts
(flat history, same horizon), so one row each.

| answer factor | entry loss | flat loss | trend loss |
| --- | --- | --- | --- |
| 0.16 | 1.272954 | 1.717590 | 1.717590 |
| 0.25 | 0.833998 | 1.278634 | 1.278634 |
| 0.40 | 0.507952 | 0.815869 | 0.815869 |

The entry beats both baselines at every simulated refresh size.

## 3. Synthetic final-like cases

Method: launches generated with the structure the kit documents (N stepwise
with refresh jumps every 6 h from 4.5 h, 638 -> 3,868 at the first refresh;
per-trophy earners growing logistically; the page frozen between refreshes),
cut at checkpoints 30 h and 54 h after launch with a 108 h horizon (the
final's 6,510 min), 3 seeds, 6 cases. Entry, flat and trend baselines scored
with the same pinball implementation; neither program ever sees its target.

| | entry | flat | trend |
| --- | --- | --- | --- |
| mean loss over 6 cases | **0.276441** | 0.326463 | 0.317749 |

The entry wins on all 6 cases individually (0.259–0.373 vs flat 0.313–0.342,
trend 0.289–0.329) and on the mean. An earlier spread (fixed 0.5/sqrt-day
random walk plus the other terms) lost to flat here (0.358 vs 0.326): the fix
was making the trend volatility the case's own fit residual (see DESIGN.md),
which narrows the band on smooth histories.

## 4. Shape, determinism, runtime

- p00/p01 outputs: 55 rows, one per trophy, five quantiles each, monotone
  non-decreasing, all in [0, 100], file 3,068 bytes (< 65,536 cap).
- Two runs byte-identical (`diff -r` clean) on p00, p01 and the live case.
- Runtime ~20 ms per case (three cases in 42 ms) against the 8 s cap.
- The kit starter run on the same live case reproduces the flat baseline's
  loss exactly (1.370656), validating the independent scorer.
