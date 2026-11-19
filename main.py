#!/usr/bin/env python3
# gta6-trophy-rarity-forecast-01: forecast each GTA VI PS5 trophy's Exophase earn
# rate at the case's target, five quantiles each, scored by pinball loss on the
# logit scale. Python 3.13, standard library only, offline, deterministic.
# MODEL: a rate is a ratio r = E / N, and Exophase moves both in jumps (launch
# night: N 638 -> 3,868 at 04:30 UTC, every rate but the 100% one down). Split
# them: log N and log E_i each regressed on log(1 + hours since the first read)
# over the last 24 h of reads, slopes damped 0.7x (N [0, 1.2], E [0, 2]), E's
# slope shrunk halfway to the cross-trophy median slope. N(T) capped at 4x the
# last read; E_i(T) at 99% of N(T), floored at its last value. Median rate =
# 100 * E_i(T) / N(T). Flat history fits nothing: median stays at the last rate.
# SPREAD (logit sigma, in quadrature): trend volatility x sqrt(days) — the case's
# own median log-E fit residual (and the N fit's), floored 0.10, capped at the
# house baseline's 0.50 (0.50 with no fit); per-trophy fit residual; count noise
# 1/sqrt(E(T)) capped at 0.6; refresh risk 0.35x the median trophy's largest
# |logit jump| between reads (0.20..0.70), or 0.55 when history is flat. The
# trophy at 100% survived a 6x jump in N at 100%: forecast near 100%.

import json
import math
import os
from datetime import datetime

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]
SIGMA_RW = 0.5
VOL_FLOOR = 0.10
VOL_CAP = 0.5
DAMP = 0.7
N_GROWTH_CAP = 4.0
S_REFRESH_FLAT = 0.55
S_FIT_DEFAULT = 0.3


def clamp(x, lo, hi):
    return min(hi, max(lo, x))


def logit(pct):
    p = clamp(pct, 0.01, 99.99) / 100.0
    return math.log(p / (1 - p))


def logistic(l):
    return 100.0 / (1.0 + math.exp(-l))


def round4(x):
    return math.floor(x * 10000 + 0.5) / 10000


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def linreg(xs, ys):
    """OLS of y on x; None below 3 points, on a degenerate x, or on a constant y
    (a series that never moved fits perfectly but says nothing about the future)."""
    if len(xs) < 3:
        return None
    if max(ys) - min(ys) < 1e-12:
        return None
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        return None
    b = sxy / sxx
    a = my - b * mx
    sd = math.sqrt(sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys)) / n)
    return (a, b, sd)


def forecast_case(c):
    if c["levels"] != LEVELS:
        raise ValueError("case asks for levels %r, not %r" % (c["levels"], LEVELS))
    reads = c["history"]
    if not reads:
        raise ValueError("case has no history")
    last = reads[-1]
    d = c["horizon_minutes"] / 1440
    t0 = parse_time(reads[0]["at"])
    tau = lambda r: max(0.0, (parse_time(r["at"]) - t0).total_seconds() / 3600)
    x = lambda r: math.log(1 + tau(r))
    x_t = math.log(1 + max(0.0, (parse_time(c["target"]) - t0).total_seconds() / 3600))
    x_last = x(last)
    win = [r for r in reads if tau(r) >= tau(last) - 24]
    fit_reads = win if len(win) >= 3 else reads

    n_pts = [(x(r), math.log(r["players_tracked"])) for r in fit_reads if r["players_tracked"] > 0]
    n_fit = linreg([p[0] for p in n_pts], [p[1] for p in n_pts])
    n_last = last["players_tracked"]
    n_t = n_last
    if n_fit is not None:
        beta_n = clamp(DAMP * n_fit[1], 0, 1.2)
        n_t = clamp(n_last * math.exp(beta_n * (x_t - x_last)), n_last, N_GROWTH_CAP * n_last)

    jumps = []
    for i in range(len(c["trophies"])):
        mj = 0.0
        for j in range(1, len(reads)):
            a, b = reads[j - 1]["rates"][i], reads[j]["rates"][i]
            if a is not None and b is not None:
                mj = max(mj, abs(logit(b) - logit(a)))
        if mj > 0:
            jumps.append(mj)
    j_med = median(jumps) if jumps else 0.0
    s_refresh = clamp(0.35 * j_med, 0.2, 0.7) if j_med > 0.05 else S_REFRESH_FLAT

    e_fits = []
    for i in range(len(c["trophies"])):
        xs, ys = [], []
        for r in fit_reads:
            rate = r["rates"][i]
            if rate is not None and rate > 0 and r["players_tracked"] > 0:
                xs.append(x(r))
                ys.append(math.log(rate / 100 * r["players_tracked"]))
        f = linreg(xs, ys)
        e_fits.append(None if f is None else (clamp(DAMP * f[1], 0, 2), f[2]))
    betas = [f[0] for f in e_fits if f is not None]
    beta_med = median(betas) if betas else 0.0
    resids = [f[1] for f in e_fits if f is not None]
    if n_fit is not None:
        resids.append(n_fit[2])
    sigma_vol = clamp(median(resids), VOL_FLOOR, VOL_CAP) if resids else SIGMA_RW

    rows = []
    for i, t in enumerate(c["trophies"]):
        last_rate = None
        for r in reversed(reads):
            if r["rates"][i] is not None:
                last_rate = r["rates"][i]
                break
        if last_rate is None:
            rows.append({"id": t["id"], "q": [0.01, 0.01, 0.01, 0.01, 0.01]})
            continue
        if last_rate >= 99.99:
            rows.append({"id": t["id"], "q": [98.5, 99.5, 99.9, 99.99, 99.99]})
            continue
        e_last = last_rate / 100 * n_last
        f = e_fits[i]
        e_t, s_fit = e_last, S_FIT_DEFAULT
        if f is not None and e_last > 0:
            beta = (f[0] + beta_med) / 2
            e_t = clamp(e_last * math.exp(beta * (x_t - x_last)), e_last, 0.99 * n_t)
            s_fit = clamp(f[1], 0.15, 0.8)
        elif e_last == 0:
            e_t = 0.5  # half an earner
        m = clamp(100 * e_t / n_t, 0.01, 99.99)
        s_count = min(0.6, 1 / math.sqrt(max(e_t, 1)))
        s = math.sqrt(sigma_vol ** 2 * d + s_fit ** 2 + s_count ** 2 + s_refresh ** 2)
        l = logit(m)
        q, prev = [], 0.0
        for z in Z:
            v = max(prev, clamp(round4(logistic(l + z * s)), 0.01, 99.99))
            q.append(v)
            prev = v
        rows.append({"id": t["id"], "q": q})
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name in sorted(os.listdir(INPUT_DIR)):
        if not name.endswith(".in"):
            continue
        with open(os.path.join(INPUT_DIR, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        rows = forecast_case(case)
        out = os.path.join(OUTPUT_DIR, name[:-3] + ".out")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"trophies": rows}) + "\n")


if __name__ == "__main__":
    main()
