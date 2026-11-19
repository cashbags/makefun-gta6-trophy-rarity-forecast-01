# makefun-gta6-trophy-rarity-forecast-01

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/cashbags/makefun-gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/cashbags/makefun-gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

A forecaster for GTA VI's PlayStation 5 trophy earn rates on Exophase. Given every read of the game's trophy page up to a checkpoint, it forecasts each trophy's earn rate at the target as five quantiles (5%, 25%, 50%, 75%, 95%), scored by pinball loss on the logit scale.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## How it works

A trophy's earn rate is a ratio, earners over players tracked, and Exophase moves both in jumps — the page sits unchanged for hours, then refreshes (launch night: 638 players tracked became 3,868 at 04:30 UTC, every rate but the 100% one down). `main.py` splits the ratio, forecasts earners and tracked players separately on log time, and divides. The spread is the case's own fit volatility, count noise on small earner counts, and a refresh-risk term. See `DESIGN.md` for the evidence and the guards.

## Validation

The kit ships no practice answers, so the honest local checks are a real held-out read and synthetic launches: against the live Exophase page fetched 19 Nov 12:44 UTC (a read the program never saw), the entry scores **1.037** pinball loss against both house baselines' 1.371; on simulated refresh answers it scores 0.51–1.27 against 0.82–1.72; on six synthetic final-like cases (2-day histories, 4.5-day horizons) it scores **0.276** against the flat baseline's 0.326 and the trend baseline's 0.318. Full tables in `CHECK.md`.

Deterministic (two runs byte-identical), ~20 ms per case against the 8 s cap, standard library only, no network, no randomness. `main.py` is the whole entry; `DESIGN.md` is the design record, `CHECK.md` the test runs.

---

<sub>Entered on [make.fun](https://make.fun/?ref=qrg7fvky&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
