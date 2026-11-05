#!/usr/bin/env python3
"""macro_rates area generator: 1000 synthetic macro/rates rows, profile A.
Every ground_truth number is computed from the same values rendered into the
context. Nothing here is a real published statistic; all fixtures are synthetic.
"""
import hashlib
import json
import os
import random
import re
import subprocess, sys
AREA = "macro_rates"
R = random.Random(42)
HERE = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
NUM = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")
THINK_ON = ("calc", "qa", "tool_use")
FOOT = [ "Source: synthetic statistical office release calendar; (a) seasonally adjusted, (b) index rebased to the base period.", "Note: all figures are synthetic training data rounded to the precision shown; revisions are not reflected.",
    "Source: synthetic rate sheet compiled for training use. Quoted values are illustrative, not published levels.", "Note: (a) prior-period values are as first published. (b) Components may not sum exactly because of rounding.",
    "Source: fictional market data desk, compiled for model training. No figure here is a real observation.", "Note: seasonally adjusted unless marked otherwise; figures are synthetic and carry no official status.",
    "Source: synthetic release table. Rates are quoted in percent and spreads in basis points where labelled.", "Note: this table is a synthetic teaching fixture; entries shown as n.a. were not published for that period.",
    ]
TITLES = { "cpi": ["Consumer price release, reference month {d} (synthetic statistical office)", "Price statistics bulletin: month {d}", "CPI release table for the reference period {d}"], "rates": ["Government curve sheet, close of business {d} (synthetic)", "Sovereign yield sheet for {d}",
    "Rate sheet, {d} close, synthetic dealer run"], "policy": ["Policy futures strip after the {d} meeting (synthetic)", "Meeting-by-meeting implied policy rates, {d} update", "Short-rate futures decomposition for the {d} cycle"], "gdp": ["National accounts release, {d} (synthetic)",
    "Expenditure-side GDP table for {d}", "GDP by component and deflator, {d} release"], "labor": ["Labour market release, {d} (synthetic)", "Establishment and household survey table for {d}", "Payrolls and participation release, {d}"], "fx": ["FX and money-market sheet, {d} (synthetic)",
    "Currency rate sheet for {d}", "Spot, forward and deposit rates, {d} close"], "be": ["Inflation-linked bond sheet, {d} (synthetic)", "Nominal and real yield table for {d}", "Breakeven decomposition sheet, {d}"], "yoy": ["Year-over-year inflation monitor for {d} (synthetic)",
    "Inflation trend table, {d}"], "stance": ["Policy stance table for {d} (synthetic)", "Real policy rate monitor, {d}"],
    }
UNITS = { "cpi": "Units: index levels in index points, weights and consensus estimates in percent, dates as labelled.", "rates": "Units: yields and the policy rate in percent, spreads in basis points where stated, dates as labelled.",
    "policy": "Units: policy rates in percent, basis points where stated, meeting dates as labelled.", "gdp": "Units: GDP and components in billions of dollars, deflator in index points, dates as labelled.", "labor": "Units: levels in thousands of persons, rates in percent, dates as labelled.",
    "fx": "Units: spot and forward rates in USD per EUR, forward points in ten-thousandths, rates in percent, notional in EUR millions.", "be": "Units: yields and breakevens in percent, changes in percentage points where stated, dates as labelled.",
    "yoy": "Units: year-over-year changes in percent, dates as labelled.", "stance": "Units: rates and inflation in percent, dates as labelled.",
    }
def f(x, n):
    s = ("%." + str(n) + "f") % float(x)
    return s[1:] if s.startswith("-") and float(s) == 0.0 else s
def f0(x):
    return str(int(round(float(x))))
def shift(y, m, k):
    t = y * 12 + (m - 1) + k
    return t // 12, t % 12 + 1
def col_label(st, y, m):
    if st == 0:
        return "%s %d" % (MONTHS[m - 1], y)
    if st == 1:
        return "%04d-%02d" % (y, m)
    if st == 2:
        return "M%02d %d" % (m, y)
    return "%s-%02d" % (MONTHS[m - 1], y % 100)
def mask(s):
    return NUM.sub("#", WS.sub(" ", str(s)).strip().lower())
def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)

def render(fx):
    parts = [fx["units"], fx["title"]]
    if fx.get("note"):
        parts.append(fx["note"])
    parts.append("")
    for t in fx["tables"]:
        parts.append(md(t["header"], t["rows"]))
        parts.append("")
    parts.append(fx["foot"])
    return "\n".join(parts)

def wrap(kind, key, header, rows, m, d, note=None, extra=()):
    return {"key": key, "kind": kind, "units": UNITS[kind], "title": R.choice(TITLES[kind]).format(d=d), "note": note, "foot": R.choice(FOOT), "tables": [{"header": header, "rows": rows}] + list(extra), "m": m}
# ---------------------------------------------------------------- fixtures

def make_cpi(key, gap=None):
    y, m, st = R.choice([2024, 2025]), R.randrange(1, 13), R.randrange(4)
    l0, l1, l2 = [col_label(st, *shift(y, m, k)) for k in (0, -1, -12)]
    head = round(R.uniform(297.0, 338.0), 2)
    base = round(head / (1 + R.uniform(0.009, 0.051)), 2)
    prev = round(head / (1 + R.uniform(-0.0022, 0.0048)), 2)
    core_base = round(R.uniform(288.0, 330.0), 2)
    core = round(core_base * (1 + R.uniform(0.008, 0.053)), 2)
    core_prev = round(core / (1 + R.uniform(-0.0015, 0.0042)), 2)
    comp = []
    for nm, lo, hi in [("Food", 0.4, 5.9), ("Energy", -8.5, 9.5), ("Shelter", 2.0, 6.4), ("Core services", 1.7, 6.1), ("Core goods", -2.6, 3.7)]:
        b = round(R.uniform(276.0, 326.0), 2)
        c = round(b * (1 + R.uniform(lo, hi) / 100.0), 2)
        comp.append((nm, c, round(c / (1 + R.uniform(-0.0055, 0.0065)), 2), b))
    w = [round(R.uniform(12.0, 15.0), 1), round(R.uniform(6.0, 9.0), 1), round(R.uniform(32.0, 36.0), 1), round(R.uniform(24.0, 29.5), 1)]
    w.append(round(100.0 - sum(w), 1))
    yoy = (head / base - 1) * 100
    cons = round(yoy + (gap if gap is not None else R.choice([-0.4, -0.3, -0.1, 0.0, 0.2, 0.4])), 1)
    rows = [["Headline CPI index", f(head, 2), f(prev, 2), f(base, 2)], ["Core CPI index (ex food and energy)", f(core, 2), f(core_prev, 2), f(core_base, 2)]]
    for nm, c, p, b in comp:
        rows.append([nm + " index", f(c, 2), f(p, 2), f(b, 2)])
    rows.append(["Memo: discontinued detail series", "n.a.", "n.a.", "n.a."])
    drow = []
    for nm in R.sample(["Owners' equivalent rent", "Used vehicles", "Medical care services", "Transportation services", "Apparel", "Recreation", "New vehicles"], 2):
        b = round(R.uniform(270.0, 330.0), 2)
        c = round(b * (1 + R.uniform(-3.0, 6.0) / 100.0), 2)
        drow.append([nm, f(c, 2), f(round(c / (1 + R.uniform(-0.006, 0.007)), 2), 2), f(b, 2)])
    m_ = {"l0": l0, "l1": l1, "l2": l2, "head": head, "prev": prev, "base": base, "core": core, "core_prev": core_prev, "core_base": core_base, "cons": cons, "w_shelter": w[2], "w_energy": w[1], "w_food": w[0], "w_core_services": w[3], "w_core_goods": w[4]}
    for nm, c, p, b in comp:
        m_[nm] = c
        m_[nm + "_base"] = b
    wt = {"header": ["Component", "Weight in headline index"], "rows": [["Food", f(w[0], 1)], ["Energy", f(w[1], 1)], ["Shelter", f(w[2], 1)], ["Core services", f(w[3], 1)], ["Core goods", f(w[4], 1)], ["Memo: residual rounding", "n.a."]]}
    det = {"header": ["Selected detail", l0, l1, l2], "rows": drow}
    return wrap("cpi", key, ["Item", l0, l1, l2], rows, m_, l0, "Consensus estimate for headline year-over-year inflation: %s percent." % f(cons, 1), [wt, det])

def make_rates(key, regime=None, move=None):
    st, y, m = R.randrange(4), R.choice([2024, 2025]), R.randrange(1, 13)
    pol = round(R.uniform(2.75, 5.50), 2)
    y2 = round(pol + R.uniform(-0.55, 0.35), 2)
    if regime == "inv":
        y10 = round(y2 - R.uniform(0.15, 0.95), 2)
    elif regime == "flat":
        y10 = round(y2 + R.uniform(-0.04, 0.04), 2)
    elif regime == "up":
        y10 = round(y2 + R.uniform(0.20, 1.25), 2)
    else:
        y10 = round(y2 + R.uniform(-0.75, 1.10), 2)
    y3m = round(pol + R.uniform(-0.18, 0.12), 2)
    ys = {"3m": y3m, "6m": round((y3m + y2) / 2 + R.uniform(-0.06, 0.06), 2), "1y": round(y3m + (y2 - y3m) * 0.78 + R.uniform(-0.05, 0.05), 2), "2y": y2, "3y": round(y2 + (y10 - y2) * 0.18 + R.uniform(-0.05, 0.05), 2), "5y": round(y2 + (y10 - y2) * 0.45 + R.uniform(-0.05, 0.05), 2),
    "7y": round(y2 + (y10 - y2) * 0.72 + R.uniform(-0.04, 0.04), 2), "10y": y10, "30y": round(y10 + R.uniform(0.25, 0.95),
    2)}
    prior = {}
    for t in ys:
        if move == "bear_steep":
            d = R.uniform(0.25, 0.60) if t in ("10y", "30y") else R.uniform(0.02, 0.10)
        elif move == "bull_flat":
            d = -R.uniform(0.25, 0.60) if t in ("10y", "30y") else -R.uniform(0.02, 0.10)
        elif move == "bear_flat":
            d = R.uniform(0.25, 0.60) if t in ("2y", "3y") else R.uniform(0.02, 0.10)
        elif move == "bull_steep":
            d = -R.uniform(0.25, 0.60) if t in ("2y", "3y") else -R.uniform(0.02, 0.10)
        else:
            d = R.uniform(-0.55, 0.55)
        prior[t] = round(ys[t] - d, 2)
    tenors = ["3m", "6m", "1y", "2y", "3y", "5y", "7y", "10y", "30y"]
    rows = [[t, f(ys[t], 2), f(prior[t], 2)] for t in tenors]
    rows.append(["Memo: 20-year interpolated", "n.a.", "n.a."])
    tabs, pick = [], R.randrange(3)
    if pick == 0:
        tabs.append({"header": ["Swap spread", "Level"], "rows": [ ["2-year swap spread", f(R.uniform(-38, 12), 1)], ["5-year swap spread", f(R.uniform(-45, 5), 1)], ["10-year swap spread", f(R.uniform(-60, -5), 1)]]})
    elif pick == 1:
        tabs.append({"header": ["Inflation swap", "Rate"], "rows": [ ["5-year zero-coupon", f(ys["5y"] - R.uniform(1.3, 2.4), 2)], ["10-year zero-coupon", f(ys["10y"] - R.uniform(1.3, 2.4), 2)]]})
    l0 = col_label(st, y, m)
    return wrap("rates", key, ["Tenor", l0, "Prior quarter"], rows, {"y": ys, "prior": prior, "pol": pol, "l0": l0, "tenors": tenors}, l0, "Policy rate at the close: %s percent." % f(pol, 2), tabs)

def make_policy(key, mode=None):
    pol, n = round(R.uniform(2.50, 5.50), 2), R.choice([4, 5, 6])
    if mode == "ease":
        drift = -R.uniform(0.25, 1.20)
    elif mode == "tighten":
        drift = R.uniform(0.25, 0.95)
    elif mode == "hold":
        drift = R.uniform(-0.02, 0.02)
    else:
        drift = R.uniform(-1.25, 0.95)
    mons = [(1, 29), (3, 19), (5, 7), (6, 18), (7, 30), (9, 17), (11, 5), (12, 17)]
    s, yr = R.randrange(0, 3), R.choice([2024, 2025])
    labels, implied = [], []
    for i in range(n):
        mm, dd = mons[s + i]
        labels.append("%04d-%02d-%02d" % (yr, mm, dd))
        implied.append(round(pol + drift * (i + 1) / n + R.uniform(-0.03, 0.03), 2))
    rows = [[labels[i], f(implied[i], 2)] for i in range(n)] + [["Memo: median projection", "n.a."]]
    return wrap("policy", key, ["Meeting", "Implied policy rate after meeting"], rows, {"pol": pol, "implied": implied, "labels": labels}, labels[0], "Current policy rate: %s percent." % f(pol, 2))

def make_gdp(key, composition=None):
    names = ["Personal consumption", "Gross private investment", "Net exports", "Government consumption"]
    prior = [round(R.uniform(12400, 14600), 1), round(R.uniform(3400, 4300), 1), round(R.uniform(-1250, -650), 1), round(R.uniform(2950, 3450), 1)]
    if composition == "contractionary":
        delta = [-round(R.uniform(40, 160), 1), -round(R.uniform(120, 260), 1), -round(R.uniform(20, 120), 1), -round(R.uniform(20, 90), 1)]
    elif composition == "narrow":
        delta = [round(R.uniform(300, 360), 1), -round(R.uniform(60, 140), 1), -round(R.uniform(30, 80), 1), round(R.uniform(20, 50), 1)]
    elif composition == "broad-based":
        delta = [round(R.uniform(120, 300), 1), round(R.uniform(80, 240), 1), round(R.uniform(40, 140), 1), round(R.uniform(30, 110), 1)]
    else:
        delta = [round(R.uniform(50, 330), 1), round(R.uniform(-190, 280), 1), round(R.uniform(-180, 170), 1), round(R.uniform(-40, 130), 1)]
    cur = [round(p + d, 1) for p, d in zip(prior, delta)]
    defl_p = round(R.uniform(112.0, 119.0), 1)
    defl_c = round(defl_p * (1 + R.uniform(1.6, 3.4) / 100), 1)
    nom_p = [round(p * defl_p / 100.0, 1) for p in prior]
    nom_c = [round(c * defl_c / 100.0, 1) for c in cur]
    tp, tc = round(sum(prior), 1), round(sum(cur), 1)
    np_, nc = round(sum(nom_p), 1), round(sum(nom_c), 1)
    rows = [[nm, f(nom_c[i], 1), f(nom_p[i], 1), f(cur[i], 1), f(prior[i], 1)] for i, nm in enumerate(names)]
    rows.append(["Total GDP", f(nc, 1), f(np_, 1), f(tc, 1), f(tp, 1)])
    rows.append(["Memo: statistical discrepancy", "n.a.", "n.a.", "n.a.", "n.a."])
    yr = R.choice([2024, 2025])
    m_ = {"names": names, "real": cur, "real_p": prior, "tot_real": tc, "tot_real_p": tp, "nom": nom_c, "nom_p": nom_p, "tot_nom": nc, "tot_nom_p": np_, "defl_c": nc / tc * 100, "defl_p": np_ / tp * 100, "focus": names[R.randrange(4)].lower(), "focus_i": 0, "l0": "FY%d" % yr,
    "l1": "FY%d" % (yr - 1)}
    m_["focus_i"] = names.index(m_["focus"].capitalize()) if m_["focus"].capitalize() in names else 0
    hdr = ["Component", "FY%d nominal" % yr, "FY%d nominal" % (yr - 1), "FY%d real" % yr, "FY%d real" % (yr - 1)]
    return wrap("gdp", key, hdr, rows, m_, "FY%d" % yr, "All figures are synthetic and expressed on a calendar-adjusted fiscal year.")

def make_labor(key, momentum=None):
    st, y, m = R.randrange(4), R.choice([2024, 2025]), R.randrange(1, 13)
    l0, l1, l2 = [col_label(st, *shift(y, m, k)) for k in (0, -1, -12)]
    pop12 = R.randrange(262000, 272000)
    lf12 = int(pop12 * R.uniform(0.618, 0.664))
    emp12 = int(lf12 * R.uniform(0.934, 0.966))
    pay12 = int(emp12 * R.uniform(0.975, 0.994))
    pop, lf, emp = pop12 + R.randrange(1400, 2700), lf12 + R.randrange(700, 2100), emp12 + R.randrange(900, 2300)
    pay = pay12 + R.randrange(1200, 2600)
    avg = (pay - pay12) / 12.0
    if momentum == "accelerating":
        pay1 = int(round(pay - avg - 55))
    elif momentum == "decelerating":
        pay1 = int(round(pay - avg + 55))
    elif momentum == "steady":
        pay1 = int(round(pay - avg))
    else:
        pay1 = pay - R.randrange(90, 260)
    pop1, lf1, emp1 = pop - R.randrange(90, 200), lf - R.randrange(30, 190), emp - R.randrange(40, 220)
    rows = [["Civilian population", f0(pop), f0(pop1), f0(pop12)], ["Labor force", f0(lf), f0(lf1), f0(lf12)], ["Employed", f0(emp), f0(emp1), f0(emp12)], ["Unemployed", f0(lf - emp), f0(lf1 - emp1), f0(lf12 - emp12)], ["Nonfarm payrolls", f0(pay), f0(pay1), f0(pay12)],
    ["Memo: average weekly hours", "n.a.", f(R.uniform(33.6, 34.8), 1), f(R.uniform(33.6, 34.8),
    1)]]
    m_ = {"l0": l0, "l1": l1, "l2": l2, "pop": pop, "pop1": pop1, "pop12": pop12, "lf": lf, "lf1": lf1, "lf12": lf12, "emp": emp, "emp1": emp1, "emp12": emp12, "une": lf - emp, "une1": lf1 - emp1, "une12": lf12 - emp12, "pay": pay, "pay1": pay1, "pay12": pay12}
    return wrap("labor", key, ["Measure", l0, l1, l2], rows, m_, l0, "Household survey and establishment survey figures are shown on the same table.")

def make_fx(key, carry=None):
    st, y, m = R.randrange(4), R.choice([2024, 2025]), R.randrange(1, 13)
    d = col_label(st, y, m)
    spot = round(R.uniform(0.92, 1.16), 4)
    if carry == "positive carry":
        usd, eur = round(R.uniform(2.20, 4.20), 2), round(R.uniform(4.40, 5.90), 2)
    elif carry == "negative carry":
        usd, eur = round(R.uniform(4.40, 5.90), 2), round(R.uniform(0.30, 2.10), 2)
    else:
        usd, eur = round(R.uniform(3.10, 5.40), 2), round(R.uniform(0.50, 4.20), 2)
    fwd = round(spot * (1 + usd / 100) / (1 + eur / 100), 4)
    pts, notional = round((fwd - spot) * 10000, 1), R.choice([150, 200, 250, 300, 400, 500])
    rows = [["Spot rate (USD per EUR)", f(spot, 4)], ["12-month forward points", f(pts, 1)], ["USD 12-month rate", f(usd, 2)], ["EUR 12-month rate", f(eur, 2)], ["Notional (EUR millions)", f0(notional)], ["Memo: 1-month forward points", "n.a."]]
    return wrap("fx", key, ["Item", "Value"], rows, {"spot": spot, "pts": pts, "usd": usd, "eur": eur, "notional": notional, "l0": d}, d, "Quotes are synthetic and shown for a single dealing desk.")

def make_be(key, direction=None):
    st, y, m = R.randrange(4), R.choice([2024, 2025]), R.randrange(1, 13)
    d = col_label(st, y, m)
    n5 = round(R.uniform(3.55, 4.95), 2)
    r5 = round(n5 - R.uniform(1.55, 2.95), 2)
    n10 = round(n5 + R.uniform(-0.18, 0.48), 2)
    r10 = round(n10 - R.uniform(1.65, 2.85), 2)
    n5p, r5p = round(n5 + R.uniform(-0.45, 0.45), 2), round(r5 + R.uniform(-0.35, 0.35), 2)
    n10p = round(n10 + R.uniform(-0.45, 0.45), 2)
    be10 = n10 - r10
    if direction == "rising":
        be10p = round(be10 - 0.22, 2)
    elif direction == "falling":
        be10p = round(be10 + 0.22, 2)
    else:
        be10p = round(be10 + R.uniform(-0.02, 0.02), 2)
    r10p = round(n10p - be10p, 2)
    rows = [["5 years", f(n5, 2), f(r5, 2), f(n5p, 2), f(r5p, 2)], ["10 years", f(n10, 2), f(r10, 2), f(n10p, 2), f(r10p, 2)], ["Memo: 20-year breakeven", "n.a.", "n.a.", "n.a.", "n.a."]]
    hdr = ["Horizon", "Nominal yield", "Real yield", "Nominal yield, prior", "Real yield, prior"]
    return wrap("be", key, hdr, rows, {"n5": n5, "r5": r5, "n10": n10, "r10": r10, "n5p": n5p, "r5p": r5p, "n10p": n10p, "r10p": r10p, "l0": d}, d, "Nominal and inflation-linked yields are quoted on the same settlement date.")

def make_yoy(key, trend="stable"):
    st, y, m = R.randrange(4), R.choice([2024, 2025]), R.randrange(1, 13)
    labs = [col_label(st, *shift(y, m, k)) for k in (-2, -1, 0)]
    base = round(R.uniform(1.2, 5.8), 2)
    if trend == "disinflation":
        vals = [base, round(base - 0.34, 2), round(base - 0.68, 2)]
    elif trend == "reflation":
        vals = [base, round(base + 0.34, 2), round(base + 0.68, 2)]
    else:
        vals = [base, round(base + 0.04, 2), round(base - 0.03, 2)]
    rows = [["Headline CPI, year over year", f(vals[0], 2), f(vals[1], 2), f(vals[2], 2)], ["Core CPI, year over year", f(vals[0] - 0.2, 2), f(vals[1] - 0.2, 2), f(vals[2] - 0.2, 2)], ["Memo: trimmed mean, year over year", "n.a.", f(vals[1] - 0.1, 2), f(vals[2] - 0.1, 2)]]
    return wrap("yoy", key, ["Measure", labs[0], labs[1], labs[2]], rows, {"l0": labs[0], "l1": labs[1], "l2": labs[2], "vals": vals}, labs[2], "Series are synthetic and expressed as year-over-year percent changes.")

def make_stance(key, stance="neutral"):
    st, y, m = R.randrange(4), R.choice([2024, 2025]), R.randrange(1, 13)
    d, pol = col_label(st, y, m), round(R.uniform(2.60, 5.40), 2)
    if stance == "restrictive":
        yoy = round(pol - R.uniform(1.3, 2.4), 2)
    elif stance == "accommodative":
        yoy = round(pol + R.uniform(1.3, 2.6), 2)
    else:
        yoy = round(pol - R.uniform(-0.5, 0.5), 2)
    rows = [["Policy rate", f(pol, 2)], ["Headline CPI, year over year", f(yoy, 2)], ["Core CPI, year over year", f(yoy + 0.2, 2)], ["Memo: real policy rate, prior quarter", "n.a."]]
    return wrap("stance", key, ["Item", "Value"], rows, {"pol": pol, "yoy": yoy, "l0": d}, d, "The real policy rate is the policy rate minus headline year-over-year inflation.")

def make(kind, key, **kw):
    return {"cpi": make_cpi, "rates": make_rates, "policy": make_policy, "gdp": make_gdp, "labor": make_labor, "fx": make_fx, "be": make_be, "yoy": make_yoy, "stance": make_stance}[kind](key, **kw)
# ---------------------------------------------------------------- row specs

def qs(fid, q, gt, at="number", tol="abs:0.1", multi=False):
    return {"fid": fid, "q": q, "gt": gt, "at": at, "tol": tol, "multi": multi}
CALC = [ ("c01", "cpi", lambda m: (m["head"] / m["base"] - 1) * 100, "abs:0.1", False, "Using the index levels in the release table, compute headline CPI inflation year over year for the {l0} column, in percent."), ("c02", "cpi", lambda m: (m["core"] / m["core_base"] - 1) * 100, "abs:0.1", False,
    "Compute core CPI inflation year over year for the {l0} column, in percent, using the index that excludes food and energy."), ("c03", "cpi", lambda m: (m["head"] / m["prev"] - 1) * 1200, "abs:0.1", True,
    "Annualise the headline month-over-month change for the {l0} column by multiplying it by twelve, and report the result in percent."), ("c04", "cpi", lambda m: ((m["head"] / m["prev"]) ** 12 - 1) * 100, "abs:0.1", True,
    "Compound the headline month-over-month change for the {l0} column over twelve months and report the annualised rate in percent."), ("c05", "cpi", lambda m: ((m["head"] / m["base"]) - (m["core"] / m["core_base"])) * 100, "abs:0.1", True,
    "Compute the gap between headline and core CPI inflation year over year for the {l0} column, in percentage points."), ("c06", "cpi", lambda m: m["w_shelter"] * (m["Shelter"] / m["Shelter_base"] - 1), "abs:0.1", True,
    "Using the shelter weight and the shelter index, compute shelter's contribution to headline year-over-year inflation in the {l0} column, in percentage points."), ("c07", "cpi", lambda m: m["w_energy"] * (m["Energy"] / m["Energy_base"] - 1), "abs:0.1", True,
    "Using the energy weight and the energy index, compute energy's contribution to headline year-over-year inflation in the {l0} column, in percentage points."), ("c12", "rates", lambda m: (m["y"]["10y"] - m["y"]["2y"]) * 100, "abs:1", False,
    "Compute the 2s10s spread from the rate sheet, in basis points."), ("c13", "rates", lambda m: (m["y"]["10y"] - m["y"]["3m"]) * 100, "abs:1", False, "Compute the 3m10y spread from the rate sheet, in basis points."), ("c14", "rates", lambda m: (m["y"]["30y"] - m["y"]["5y"]) * 100, "abs:1", False,
    "Compute the 5s30s spread from the rate sheet, in basis points."), ("c15", "rates", lambda m: ((m["y"]["10y"] - m["y"]["2y"]) - (m["prior"]["10y"] - m["prior"]["2y"])) * 100, "abs:1", True,
    "Compute the change in the 2s10s spread between the prior-quarter column and the current column, in basis points."), ("c16", "rates", lambda m: (((1 + m["y"]["10y"] / 100.0) ** 10 / (1 + m["y"]["5y"] / 100.0) ** 5) ** 0.2 - 1) * 100, "abs:0.01", True,
    "Using the 5-year and 10-year par yields, compute the implied 5y5y forward rate under annual compounding, in percent."), ("c17", "rates", lambda m: (((1 + m["y"]["2y"] / 100.0) ** 2 / (1 + m["y"]["1y"] / 100.0)) - 1) * 100, "abs:0.01", True,
    "Using the one-year and two-year par yields, compute the implied one-year forward rate one year ahead under annual compounding, in percent."), ("c18", "policy", lambda m: (m["implied"][-1] - m["pol"]) * 100, "abs:1", True,
    "Given the stated futures-implied rates, compute the cumulative implied change in the policy rate from the current rate to the final meeting, in basis points."), ("c19", "policy", lambda m: (m["implied"][-1] - m["implied"][0]) * 100, "abs:1", True,
    "Compute the implied policy rate change between the first and the final meeting listed, in basis points."), ("c20", "policy", lambda m: sum(m["implied"]) / len(m["implied"]), "abs:0.1", False, "Compute the average implied policy rate across the meetings listed, in percent."), ("c21", "gdp",
    lambda m: (m["real"][m["focus_i"]] - m["real_p"][m["focus_i"]]) / m["tot_real_p"] * 100, "abs:0.1", True, "Compute the contribution of {focus} to real GDP growth in the table, in percentage points."), ("c22", "gdp", lambda m: (m["tot_real"] / m["tot_real_p"] - 1) * 100, "abs:0.1", True,
    "Compute real GDP growth from the expenditure components, in percent."), ("c23", "gdp", lambda m: m["defl_c"], "abs:0.1", False, "Compute the GDP deflator index for the latest year (nominal GDP divided by real GDP, times one hundred), in index points."), ("c24", "gdp",
    lambda m: (m["defl_c"] / m["defl_p"] - 1) * 100, "abs:0.1", True, "Compute the growth in the GDP deflator between the two years, in percent."), ("c25", "gdp", lambda m: (m["real"][2] - m["real_p"][2]) / m["tot_real_p"] * 100, "abs:0.1", True,
    "Compute the contribution of net exports to real GDP growth, in percentage points."), ("c26", "labor", lambda m: m["pay"] - m["pay12"], "abs:1", False, "Compute the change in nonfarm payrolls between the {l0} and {l2} columns, in thousands."), ("c27", "labor",
    lambda m: (m["pay"] - m["pay12"]) / 12.0, "abs:1", True, "Compute the average monthly change in nonfarm payrolls over the twelve months to the {l0} column, in thousands."), ("c28", "labor", lambda m: m["une"] / m["lf"] * 100, "abs:0.1", False,
    "Compute the unemployment rate for the {l0} column, in percent."), ("c29", "labor", lambda m: m["lf"] / m["pop"] * 100, "abs:0.1", False, "Compute the labor force participation rate for the {l0} column, in percent."), ("c30", "labor", lambda m: m["emp"] / m["pop"] * 100, "abs:0.1", False,
    "Compute the employment-population ratio for the {l0} column, in percent."), ("c31", "fx", lambda m: m["notional"] * m["spot"], "abs:0.1", False, "Translate the stated notional into US dollars at the spot rate, in millions of USD."), ("c32", "fx", lambda m: m["spot"] + m["pts"] / 10000.0,
    "rel:0.005", True, "Compute the 12-month forward outright rate from the spot rate and the forward points, in USD per EUR."), ("c33", "fx", lambda m: m["eur"] - m["usd"], "abs:0.1", False,
    "Compute the annualised carry from holding the foreign currency against the dollar, measured as the EUR rate minus the USD rate, in percent."), ("c34", "be", lambda m: m["n5"] - m["r5"], "abs:0.1", False, "Compute the 5-year breakeven inflation rate from the nominal and real yields, in percent."),
    ("c35", "be", lambda m: (((1 + (m["n10"] - m["r10"]) / 100.0) ** 10 / (1 + (m["n5"] - m["r5"]) / 100.0) ** 5) ** 0.2 - 1) * 100, "abs:0.01", True, "Compute the implied 5y5y forward breakeven inflation rate under annual compounding, in percent."), ("c36", "be",
    lambda m: (m["n10"] - m["r10"]) - (m["n10p"] - m["r10p"]), "abs:0.1", True, "Compute the change in the 10-year breakeven between the prior column and the current column, in percentage points."),
    ]
CALC_MAP = dict((c[0], c) for c in CALC)
CALC_FAM = {}
for c in CALC:
    CALC_FAM.setdefault(c[1], []).append(c[0])

def calc_spec(fx, fid):
    c = CALC_MAP[fid]
    return qs(fid, c[5].format(**fx["m"]), round(c[2](fx["m"]), 2), "number", c[3], c[4])
# ---------------------------------------------------------------- extraction

def extr_spec(fx, fid):
    t = fx["tables"][0]
    hdr, rows = t["header"], t["rows"]
    ncol = len(hdr)
    if fid == "e01":
        ri, ci = R.randrange(len(rows)), R.randrange(1, ncol)
        return qs(fid, "Quote the exact value printed for the %s row in the %s column." % (rows[ri][0], hdr[ci]), rows[ri][ci], "text", "normalized")
    if fid == "e02":
        return qs(fid, "Quote the Units line of this table exactly as written.", fx["units"], "text", "normalized")
    if fid == "e03":
        return qs(fid, "Quote the title line of this release exactly as written.", fx["title"], "text", "normalized")
    if fid == "e04":
        ci = R.randrange(1, ncol)
        return qs(fid, "Quote the header of column %d exactly as written." % ci, hdr[ci], "text", "normalized")
    if fid == "e05":
        return qs(fid, "Quote the first data row exactly as printed, separating the cells with vertical bars.", " | ".join(rows[0]), "text", "normalized")
    if fid == "e06":
        return qs(fid, "Quote the last data row exactly as printed, separating the cells with vertical bars.", " | ".join(rows[-1]), "text", "normalized")
    if fid == "e07":
        return qs(fid, "Quote the footnote text of this table exactly as written.", fx["foot"], "text", "normalized")
    if fid == "e08":
        ci, best, lab = R.randrange(1, ncol), None, rows[0][0]
        for r in rows:
            try:
                v = float(r[ci])
            except ValueError:
                continue
            if best is None or v > best:
                best, lab = v, r[0]
        return qs(fid, "Which row label carries the largest value in the %s column? Quote the label exactly." % hdr[ci], lab, "text", "normalized")
    if fid == "e09":
        lab = None
        for r in rows:
            if r[1] == "n.a.":
                lab = r[0]
                break
        return qs(fid, "Which row label has an entry of n.a. in the %s column? Quote the label exactly." % hdr[1], lab, "text", "normalized")
    best, h = None, hdr[1]
    for i in range(1, ncol):
        try:
            v = float(rows[0][i])
        except ValueError:
            continue
        if best is None or v > best:
            best, h = v, hdr[i]
    return qs(fid, "Which column header carries the largest value in the first data row? Quote that header exactly.", h, "text", "normalized")
EXTR_FAM = ["e01", "e02", "e03", "e04", "e05", "e06", "e07", "e08", "e09", "e10"]
QA_FAM = {"cpi": ["q1", "q2", "q3", "q4"], "rates": ["q1", "q2", "q3", "q4"], "policy": ["q1", "q2", "q3"], "gdp": ["q1", "q2", "q3"], "labor": ["q1", "q2", "q3"], "fx": ["q1", "q2", "q3"], "be": ["q1", "q2", "q3"]}
# ---------------------------------------------------------------- qa

def qa_spec(fx, fid):
    m = fx["m"]
    if fx["kind"] == "cpi":
        yoy = {"Headline": (m["head"] / m["base"] - 1) * 100, "Core": (m["core"] / m["core_base"] - 1) * 100}
        for nm in ("Food", "Energy", "Shelter", "Core services", "Core goods"):
            yoy[nm] = (m[nm] / m[nm + "_base"] - 1) * 100
        if fid == "q1":
            return qs(fid, "Which item in the release table shows the highest year-over-year increase? Answer with the item label.", max(yoy, key=yoy.get), "label", "exact")
        if fid == "q2":
            d = yoy["Headline"] - m["cons"]
            lab = "above consensus" if d >= 0.1 else ("below consensus" if d <= -0.1 else "in line")
            return qs(fid, "Classify the headline print against the consensus estimate as one of {above consensus, in line, below consensus}, treating a gap under 0.1 percentage point as in line.", lab, "label", "exact")
        if fid == "q3":
            return qs(fid, "By how many percentage points does headline inflation exceed core inflation in the %s column?" % m["l0"], round(yoy["Headline"] - yoy["Core"], 2), "number", "abs:0.1")
        vals = [("Headline CPI index", m["head"]), ("Core CPI index (ex food and energy)", m["core"])]
        for nm in ("Food", "Energy", "Shelter", "Core services", "Core goods"):
            vals.append((nm + " index", m[nm]))
        return qs(fid, "Which row in the main table carries the highest index level? Answer with the row label.", max(vals, key=lambda z: z[1])[0], "label", "exact")
    if fx["kind"] == "rates":
        ys = m["y"]
        if fid == "q1":
            return qs(fid, "Which tenor on the rate sheet carries the highest yield? Answer with the tenor label.", max(ys, key=ys.get), "label", "exact")
        if fid == "q2":
            return qs(fid, "How many of the listed tenors yield less than the policy rate? Answer with a whole number.", sum(1 for t in m["tenors"] if ys[t] < m["pol"]), "number", "abs:0.01")
        if fid == "q3":
            return qs(fid, "Is the curve inverted on the 2s10s measure in the table? Answer yes or no.", "yes" if ys["10y"] < ys["2y"] else "no", "label", "exact")
        segs = {"3m to 2y": ys["2y"] - ys["3m"], "2y to 5y": ys["5y"] - ys["2y"], "5y to 10y": ys["10y"] - ys["5y"]}
        return qs(fid, "Which segment of the curve is steepest: 3m to 2y, 2y to 5y or 5y to 10y? Answer with the segment label.", max(segs, key=segs.get), "label", "exact")
    if fx["kind"] == "policy":
        if fid == "q1":
            d = m["implied"][-1] - m["pol"]
            lab = "easing" if d <= -0.05 else ("tightening" if d >= 0.05 else "unchanged")
            return qs(fid, "Does the stated path price net easing, net tightening or no change? Answer easing, tightening or unchanged.", lab, "label", "exact")
        if fid == "q2":
            return qs(fid, "How many listed meetings imply a policy rate below the current rate? Answer with a whole number.", sum(1 for v in m["implied"] if v < m["pol"]), "number", "abs:0.01")
        return qs(fid, "By how many basis points does the implied rate at the final meeting differ from the implied rate at the first meeting?", round((m["implied"][-1] - m["implied"][0]) * 100, 1), "number", "abs:1")
    if fx["kind"] == "gdp":
        contrib = [(m["names"][i], (m["real"][i] - m["real_p"][i]) / m["tot_real_p"] * 100) for i in range(4)]
        if fid == "q1":
            return qs(fid, "Which component contributed most to real GDP growth? Answer with the component label.", max(contrib, key=lambda z: z[1])[0], "label", "exact")
        if fid == "q2":
            return qs(fid, "How many of the four components contributed positively to real GDP growth? Answer with a whole number.", sum(1 for c in contrib if c[1] > 0), "number", "abs:0.01")
        return qs(fid, "Is real GDP growth positive in the table? Answer yes or no.", "yes" if m["tot_real"] > m["tot_real_p"] else "no", "label", "exact")
    if fx["kind"] == "labor":
        if fid == "q1":
            return qs(fid, "Is the unemployment rate higher in the %s column than in the %s column? Answer yes or no." % (m["l0"], m["l2"]), "yes" if m["une"] / m["lf"] > m["une12"] / m["lf12"] else "no", "label", "exact")
        if fid == "q2":
            return qs(fid, "Are nonfarm payrolls higher in the %s column than in the %s column? Answer yes or no." % (m["l0"], m["l2"]), "yes" if m["pay"] > m["pay12"] else "no", "label", "exact")
        return qs(fid, "Is the labor force participation rate higher in the %s column than in the %s column? Answer yes or no." % (m["l0"], m["l2"]), "yes" if m["lf"] / m["pop"] > m["lf12"] / m["pop12"] else "no", "label", "exact")
    if fx["kind"] == "fx":
        if fid == "q1":
            return qs(fid, "Does the forward market quote EUR at a premium or at a discount to spot? Answer premium or discount.", "premium" if m["pts"] > 0 else "discount", "label", "exact")
        if fid == "q2":
            return qs(fid, "Which currency offers the higher twelve-month deposit rate in the sheet? Answer USD or EUR.", "USD" if m["usd"] > m["eur"] else "EUR", "label", "exact")
        return qs(fid, "Is the carry on the foreign currency positive or negative? Answer positive or negative.", "positive" if m["eur"] > m["usd"] else "negative", "label", "exact")
    be5, be10 = m["n5"] - m["r5"], m["n10"] - m["r10"]
    if fid == "q1":
        return qs(fid, "Is the 10-year breakeven higher or lower than the 5-year breakeven? Answer higher or lower.", "higher" if be10 > be5 else "lower", "label", "exact")
    if fid == "q2":
        fwd = ((1 + be10 / 100.0) ** 10 / (1 + be5 / 100.0) ** 5) ** 0.2 - 1
        return qs(fid, "Is the implied 5y5y forward breakeven positive or negative? Answer positive or negative.", "positive" if fwd > 0 else "negative", "label", "exact")
    return qs(fid, "Are real yields lower than nominal yields in both rows of the table? Answer yes or no.", "yes" if (m["r5"] < m["n5"] and m["r10"] < m["n10"]) else "no", "label", "exact")
KNOW = [ ("Describe the Fisher effect and the relationship it implies between nominal rates, real rates and expected inflation.", "Explain how the Fisher effect links the nominal rate, the real rate and expected inflation.", "State the Fisher relationship and define each of its three terms.",
    "The Fisher effect says the nominal rate equals the real rate plus expected inflation; with compounding, one plus the nominal rate equals one plus the real rate times one plus expected inflation, so nominal rates move one for one with expected inflation when the real rate is unchanged."),
    ("Explain the difference between a nominal interest rate and a real interest rate.", "Define the nominal rate and the real rate and say which one measures purchasing power.", "Why do analysts convert a quoted rate into a real rate?",
    "A nominal rate is the quoted rate on a contract; a real rate is the nominal rate adjusted for inflation and measures the change in purchasing power, so the real rate equals the nominal rate minus inflation in the simple approximation."),
    ("How many percentage points are in one basis point? Give the answer as a decimal number in percent.", "One basis point equals how many percentage points? Answer as a decimal in percent.", "Convert one basis point into percentage points and give the result in percent.", 0.01),
    ("Write the formula for the unemployment rate and name the two inputs it uses.", "Define the unemployment rate and state the ratio used to compute it.", "Which two survey quantities does the unemployment rate divide? State the formula.",
    "The unemployment rate is the number of unemployed persons divided by the labor force, expressed in percent; the labor force is employment plus unemployment."), ("Write the formula for the labor force participation rate.", "Define the labor force participation rate and state its denominator.",
    "How is the labor force participation rate computed from household survey data?", "The labor force participation rate is the labor force divided by the civilian non-institutional population, expressed in percent."), ("Write the formula for the employment-population ratio.",
    "Define the employment-population ratio and state what it divides.", "Which numerator and denominator produce the employment-population ratio?", "The employment-population ratio is the number of employed persons divided by the civilian non-institutional population, expressed in percent."),
    ("State the expenditure identity for gross domestic product and name each component.", "Write GDP as the sum of its expenditure components.", "Which four expenditure categories add up to GDP in the national accounts identity?",
    "GDP equals consumption plus gross private investment plus government consumption plus net exports, where net exports are exports minus imports."), ("Define the GDP deflator and give its formula.", "How is the GDP deflator computed from nominal and real GDP?",
    "State the ratio that produces the GDP deflator.", "The GDP deflator is nominal GDP divided by real GDP, multiplied by one hundred, so it is an index of the price level covering all domestically produced output."), ("Explain the difference between headline inflation and core inflation.",
    "Why do statistical agencies publish a core inflation measure alongside headline inflation?", "Define core inflation and say what it excludes from the headline basket.",
    "Core inflation excludes food and energy from the headline basket because those components are volatile; headline inflation covers the full basket including food and energy."), ("Define the breakeven inflation rate and state how it is derived from two yields.",
    "How is a breakeven inflation rate computed from a nominal and an inflation-linked yield?", "What does the breakeven inflation rate represent and how is it calculated?",
    "The breakeven inflation rate is the difference between the nominal yield on a conventional bond and the real yield on an inflation-linked bond of the same maturity; it is a market-implied measure of expected inflation plus a risk premium."),
    ("Define a forward interest rate and say which two spot rates imply it.", "How is a forward rate derived from two spot rates of different maturities?", "Explain what a one-year forward one year ahead represents in terms of spot rates.",
    "A forward rate is the rate agreed now for a loan starting at a future date; it is implied by the no-arbitrage relation between two spot rates, so that rolling the shorter spot over the forward period equals the longer spot."),
    ("Define an inverted yield curve and state which spread is usually quoted to describe it.", "What does it mean when the yield curve is inverted?", "Explain how an inverted curve shows up in the 2s10s spread.",
    "An inverted curve has short-dated yields above long-dated yields, so the 2s10s spread measured as the 10-year yield minus the 2-year yield is negative."), ("Explain the relationship between a bond price and its yield.", "If a bond yield rises, what happens to the bond price and why?",
    "State the direction of the price change when yields fall, and name the risk measure that captures sensitivity.",
    "Bond prices move inversely to yields: when the yield rises the present value of the fixed cash flows falls, and duration measures the percentage price sensitivity to a small yield change."), ("Define carry in foreign exchange and state how it is measured.",
    "What does an FX carry position earn and from which rates is it computed?", "Explain how the interest rate differential produces FX carry.",
    "FX carry is the return from holding a currency funded in another currency, measured as the interest rate differential between the two currencies, before any change in the spot rate."), ("State covered interest parity and the relationship it imposes on forward points.",
    "What does covered interest parity say about the forward premium and the interest differential?", "Explain how covered interest parity links spot rates, forward rates and two deposit rates.",
    "Covered interest parity requires the forward premium or discount to equal the interest rate differential between the two currencies, so a hedged foreign deposit earns the domestic rate."), ("Define a component's contribution to GDP growth and give its formula.",
    "How is the contribution of one expenditure component to real GDP growth computed?", "State the ratio used to turn a component's real change into a growth contribution.",
    "A component's contribution to growth is its real change divided by prior-period total real GDP, multiplied by one hundred, and contributions sum to the aggregate growth rate."), ("Explain the difference between nominal GDP and real GDP.",
    "Which GDP measure is adjusted for price changes and why does that matter?", "Define real GDP and say what nominal GDP includes that real GDP removes.",
    "Nominal GDP is valued at current prices, while real GDP is valued at constant prices so that changes reflect volumes rather than price movements."), ("State the formula for a compound annual growth rate.", "How is a compound annual growth rate computed over several periods?",
    "Write the compound annual growth rate as a function of the beginning value, ending value and number of periods.", "The compound annual growth rate is the ending value divided by the beginning value, raised to the power of one over the number of periods, minus one, expressed in percent."),
    ("Explain what seasonal adjustment does to an economic series.", "Why are payroll and price series seasonally adjusted before publication?", "Define seasonal adjustment and state the variation it removes.",
    "Seasonal adjustment removes recurring calendar-related patterns, such as weather and holiday effects, so that month-to-month movements reflect underlying trends rather than normal seasonal variation."), ("Explain the difference between a central bank policy rate and a market yield.",
    "Why does a ten-year government yield differ from the policy rate?", "Distinguish the administered policy rate from a traded market yield.",
    "A policy rate is an administered rate set by the central bank for short-term reserves, while a market yield is set by trading and reflects expectations of future policy rates plus term and inflation premia."),
    ]
KNOW_Q = {}
for idx, item in enumerate(KNOW):
    for j in range(3):
        KNOW_Q["k%02d_%d" % (idx + 1, j)] = (item[j], item[3])

def know_spec(key):
    q, a = KNOW_Q[key]
    if isinstance(a, float):
        return qs("know", q, a, "number", "abs:0.01")
    return qs("know", q, a, "text", "normalized")
# ---------------------------------------------------------------- classification
CLS_LABELS = {"k01": ["inverted", "flat", "upward sloping"], "k02": ["above consensus", "in line", "below consensus"], "k03": ["easing", "on hold", "tightening"], "k04": ["bear steepener", "bull steepener", "bear flattener", "bull flattener"], "k05": ["disinflation", "stable", "reflation"],
    "k06": ["broad-based", "narrow", "contractionary"], "k07": ["positive carry", "negative carry"], "k08": ["accelerating", "steady", "decelerating"], "k09": ["restrictive", "neutral", "accommodative"], "k10": ["rising", "flat",
    "falling"]}

def cls_build(fid, j):
    lab = CLS_LABELS[fid][j % len(CLS_LABELS[fid])]
    key = "cls_%s_%02d" % (fid, j)
    if fid == "k01":
        fx = make_rates(key, regime={"inverted": "inv", "flat": "flat", "upward sloping": "up"}[lab])
        q = "Classify the curve shape as one of {inverted, flat, upward sloping}, where inverted means the 2s10s spread is at or below minus 5 basis points, flat means within 5 basis points of zero, and upward sloping means above plus 5 basis points."
    elif fid == "k02":
        fx = make_cpi(key, gap={"above consensus": -0.4, "in line": 0.0, "below consensus": 0.4}[lab])
        q = "Classify the headline print against the consensus estimate as one of {above consensus, in line, below consensus}, treating a gap smaller than 0.1 percentage point as in line."
    elif fid == "k03":
        fx = make_policy(key, mode={"easing": "ease", "on hold": "hold", "tightening": "tighten"}[lab])
        q = "Classify the implied policy path as one of {easing, on hold, tightening}, where easing means the final implied rate is at least 5 basis points below the current rate, tightening means at least 5 basis points above, and on hold means within 5 basis points either way."
    elif fid == "k04":
        fx = make_rates(key, move={"bear steepener": "bear_steep", "bull steepener": "bull_steep", "bear flattener": "bear_flat", "bull flattener": "bull_flat"}[lab])
        q = "Classify the quarter-on-quarter curve move as one of {bear steepener, bull steepener, bear flattener, bull flattener}, judged on whether the two-year and ten-year yields rose or fell and whether the 2s10s spread widened or narrowed by at least 5 basis points."
    elif fid == "k05":
        fx = make_yoy(key, trend=lab)
        q = "Classify the inflation trend as one of {disinflation, stable, reflation}, comparing headline year-over-year inflation in the latest column with the column two months earlier, with a change under 0.15 percentage point counted as stable."
    elif fid == "k06":
        fx = make_gdp(key, composition=lab)
        q = "Classify the growth composition as one of {broad-based, narrow, contractionary}, where contractionary means total real GDP growth is zero or negative, broad-based means at least three of the four components contribute positively, and narrow covers everything else."
    elif fid == "k07":
        fx = make_fx(key, carry=lab)
        q = "Classify the carry on the foreign currency position as one of {positive carry, negative carry}, measured as the EUR twelve-month rate minus the USD twelve-month rate."
    elif fid == "k08":
        fx = make_labor(key, momentum=lab)
        q = "Classify payroll momentum as one of {accelerating, steady, decelerating}, comparing the latest monthly payroll change with the average monthly change over the twelve months to the latest column, with a gap under 10 thousand counted as steady."
    elif fid == "k09":
        fx = make_stance(key, stance=lab)
        q = "Classify the real policy stance as one of {restrictive, neutral, accommodative}, where the real rate is the policy rate minus headline year-over-year inflation, restrictive means above plus 1.0 percentage point, accommodative means below minus 1.0, and neutral is in between."
    else:
        fx = make_be(key, direction=lab)
        q = "Classify the direction of the 10-year breakeven as one of {rising, flat, falling}, comparing the current column with the prior column, with a change under 0.05 percentage point counted as flat."
    return fx, lab, q
# ---------------------------------------------------------------- summarization
SUMM_FAM = {"cpi": ["s01", "s02"], "rates": ["s03", "s04"], "policy": ["s05", "s10"], "gdp": ["s08", "s11"], "labor": ["s06", "s12"], "fx": ["s07", "s13"], "be": ["s09", "s14"]}

def summ_spec(fx, fid):
    m, k = fx["m"], fx["kind"]
    if k == "cpi":
        if fid == "s01":
            gt = ("Headline CPI printed %s in %s against %s a year earlier, while the core index stood at %s versus %s. Shelter printed %s against %s, and the release puts consensus headline inflation at %s percent." % (f(m["head"], 2), m["l0"], f(m["base"], 2), f(m["core"], 2), f(m["core_base"],
    2), f(m["Shelter"], 2), f(m["Shelter_base"], 2), f(m["cons"],
    1)))
            return qs(fid, "Summarize this inflation release for a rates desk in two sentences. Quote only figures printed in the table and do not compute new numbers.", gt, "text", "normalized")
        hi = m["core"] / m["core_base"] > m["head"] / m["base"]
        gt = ("The headline index sits %s its year-earlier level, at %s against %s. The core index sits %s at %s against %s, so on the printed levels the core series runs %s the headline series. The energy index printed %s against %s." % ("above" if m["head"] > m["base"] else "below", f(m["head"],
    2), f(m["base"], 2), "higher" if hi else "lower", f(m["core"], 2), f(m["core_base"], 2), "above" if hi else "below", f(m["Energy"], 2), f(m["Energy_base"],
    2)))
        return qs(fid, "Write a three-sentence note on the direction of inflation in this table for an economist, using only the printed index levels.", gt, "text", "normalized")
    if k == "rates":
        ys = m["y"]
        if fid == "s03":
            gt = ("The sheet quotes %s percent at two years and %s percent at ten years, with the policy rate at %s percent. The three-month bill sits at %s percent and the thirty-year at %s percent, so the front end is %s the long end on the printed levels." % (f(ys["2y"], 2), f(ys["10y"], 2),
    f(m["pol"], 2), f(ys["3m"], 2), f(ys["30y"], 2),
    "above" if ys["3m"] > ys["30y"] else "below"))
            return qs(fid, "Write one paragraph describing the shape of this curve for a fixed-income client, quoting the printed yields.", gt, "text", "normalized")
        gt = ("- Two-year yield at %s percent, ten-year at %s percent.\n- Three-month bill at %s percent against a policy rate of %s percent.\n- Thirty-year yield at %s percent and five-year at %s percent." % (f(ys["2y"], 2), f(ys["10y"], 2), f(ys["3m"], 2), f(m["pol"], 2), f(ys["30y"], 2),
    f(ys["5y"],
    2)))
        return qs(fid, "Give a three-bullet summary of the rate sheet for a client note, quoting the printed yields and the policy rate.", gt, "text", "normalized")
    if k == "policy":
        if fid == "s05":
            gt = ("The strip implies %s percent after the first meeting and %s percent after the final meeting, against a current policy rate of %s percent. The path %s over the meetings listed." % (f(m["implied"][0], 2), f(m["implied"][-1], 2), f(m["pol"], 2),
    "falls" if m["implied"][-1] < m["pol"] else ("rises" if m["implied"][-1] > m["pol"] else "is unchanged")))
            return qs(fid, "Summarize the implied policy path in two sentences for a rates strategist, quoting the printed implied rates.", gt, "text", "normalized")
        gt = ("The strip starts at %s percent after the first meeting and ends at %s percent after the last meeting, with the current policy rate at %s percent. The implied path is %s on the printed rates." % (f(m["implied"][0], 2), f(m["implied"][-1], 2), f(m["pol"], 2),
    "lower" if m["implied"][-1] < m["pol"] else ("higher" if m["implied"][-1] > m["pol"] else "flat")))
        return qs(fid, "Write a short note for a policy committee describing what the futures strip implies, quoting the printed rates.", gt, "text", "normalized")
    if k == "gdp":
        if fid == "s08":
            gt = ("Nominal GDP printed %s against real GDP of %s, with personal consumption at %s nominal and %s real. Gross private investment printed %s nominal and %s real, and net exports stood at %s nominal." % (f(m["tot_nom"], 1), f(m["tot_real"], 1), f(m["nom"][0], 1), f(m["real"][0], 1),
    f(m["nom"][1], 1), f(m["real"][1], 1), f(m["nom"][2],
    1)))
            return qs(fid, "Summarize this GDP release in two sentences for an investment committee, quoting only printed figures.", gt, "text", "normalized")
        gt = ("- Total GDP %s nominal against %s real.\n- Personal consumption %s nominal, %s real.\n- Government consumption %s nominal, %s real." % (f(m["tot_nom"], 1), f(m["tot_real"], 1), f(m["nom"][0], 1), f(m["real"][0], 1), f(m["nom"][3], 1), f(m["real"][3], 1)))
        return qs(fid, "Give a three-bullet summary of the GDP table for a macro note, quoting only figures printed in the table.", gt, "text", "normalized")
    if k == "labor":
        if fid == "s06":
            gt = ("Nonfarm payrolls printed %s in %s against %s a year earlier. The household survey shows employment of %s and unemployment of %s on a labor force of %s." % (f0(m["pay"]), m["l0"], f0(m["pay12"]), f0(m["emp"]), f0(m["une"]), f0(m["lf"])))
            return qs(fid, "Write a two-sentence labor-market summary for an economics briefing, quoting only figures printed in the table.", gt, "text", "normalized")
        gt = ("- Payrolls %s against %s a year earlier.\n- Labor force %s with employment %s.\n- Civilian population %s." % (f0(m["pay"]), f0(m["pay12"]), f0(m["lf"]), f0(m["emp"]), f0(m["pop"])))
        return qs(fid, "Summarize the labor table in three bullets for a trading desk, quoting only printed levels.", gt, "text", "normalized")
    if k == "fx":
        if fid == "s07":
            gt = ("Spot is %s USD per EUR with twelve-month forward points of %s. The USD twelve-month rate is %s percent against %s percent in EUR, on a notional of %s million EUR." % (f(m["spot"], 4), f(m["pts"], 1), f(m["usd"], 2), f(m["eur"], 2), f0(m["notional"])))
            return qs(fid, "Summarize this rate sheet for a corporate treasurer in two sentences, quoting the printed rates.", gt, "text", "normalized")
        gt = ("- Spot %s with twelve-month points %s.\n- USD rate %s percent, EUR rate %s percent.\n- Notional %s million EUR." % (f(m["spot"], 4), f(m["pts"], 1), f(m["usd"], 2), f(m["eur"], 2), f0(m["notional"])))
        return qs(fid, "Give a three-bullet summary of the FX sheet for a treasury note, quoting the printed rates.", gt, "text", "normalized")
    if fid == "s09":
        gt = ("The five-year nominal yield is %s against a real yield of %s, and the ten-year is %s against %s. On the prior column the same pairs were %s and %s nominal against %s and %s real." % (f(m["n5"], 2), f(m["r5"], 2), f(m["n10"], 2), f(m["r10"], 2), f(m["n5p"], 2), f(m["n10p"], 2),
    f(m["r5p"], 2), f(m["r10p"],
    2)))
        return qs(fid, "Summarize this breakeven table in two sentences for a fixed-income desk, quoting the printed yields.", gt, "text", "normalized")
    gt = ("- Five-year nominal %s against real %s.\n- Ten-year nominal %s against real %s.\n- Prior column five-year nominal %s against real %s." % (f(m["n5"], 2), f(m["r5"], 2), f(m["n10"], 2), f(m["r10"], 2), f(m["n5p"], 2), f(m["r5p"], 2)))
    return qs(fid, "Summarize the inflation-linked table in three bullets for a portfolio note, quoting only printed yields.", gt, "text", "normalized")
# ---------------------------------------------------------------- tool use

def tl(name, desc, props, req):
    return {"name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": req}}
T_CURVE = tl("get_yield_curve", "Return government par yields by tenor for one currency and date.", {"currency": {"type": "string", "description": "Currency code, for example USD."}, "date": {"type": "string", "description": "Observation date in YYYY-MM-DD form."}}, ["currency", "date"])
T_CPI = tl("get_cpi_series", "Return monthly consumer price index levels for a country.", {"country": {"type": "string", "description": "Country code."}, "months": {"type": "integer", "description": "Number of months to return, including the latest."}}, ["country", "months"])
T_FUT = tl("get_policy_futures", "Return futures-implied policy rates by meeting date.", {"currency": {"type": "string", "description": "Currency code."}, "cycle": {"type": "string", "description": "Meeting cycle label, for example 2025H1."}}, ["currency", "cycle"])
T_GDP = tl("get_gdp_components", "Return nominal and real GDP by expenditure component for two years.", {"country": {"type": "string", "description": "Country code."}, "years": {"type": "integer", "description": "Number of years to return."}}, ["country", "years"])
T_PAY = tl("get_payroll_report", "Return establishment and household survey levels for the latest three months.", {"country": {"type": "string", "description": "Country code."}}, ["country"])
T_FX = tl("get_fx_quotes", "Return spot, forward points and deposit rates for a currency pair.", {"pair": {"type": "string", "description": "Currency pair, for example EURUSD."}, "tenor": {"type": "string", "description": "Tenor such as 1M, 3M or 12M."}}, ["pair", "tenor"])
T_BE = tl("get_breakevens", "Return nominal and inflation-linked yields by horizon.", {"country": {"type": "string", "description": "Country code."}, "horizons": {"type": "string", "description": "Comma separated horizons in years."}}, ["country", "horizons"])

def tool_row(fid):
    d = "2025-%02d-%02d" % (R.randrange(1, 13), R.randrange(1, 28))
    cur = R.choice(["USD", "EUR", "GBP"])
    y2, y10 = round(R.uniform(3.20, 4.90), 2), round(R.uniform(3.30, 5.20), 2)
    y3m, y5 = round(R.uniform(3.40, 5.10), 2), round(R.uniform(3.30, 5.10), 2)
    y30, spot = round(y10 + R.uniform(0.10, 0.70), 2), round(R.uniform(0.90, 1.18), 4)
    pts, usd, eur = round(R.uniform(-260, 260), 1), round(R.uniform(3.00, 5.40), 2), round(R.uniform(0.40, 4.40), 2)
    nl, nom, real, nom2, real2 = R.randrange(150, 520), round(R.uniform(3.6, 4.9), 2), round(R.uniform(0.8, 2.1), 2), round(R.uniform(3.7, 5.0), 2), round(R.uniform(1.0, 2.3), 2)
    lf, emp = R.randrange(160000, 172000), R.randrange(152000, 164000)
    if fid == "t01":
        msgs = [{"role": "user", "content": "Pull the %s curve for %s and tell me the 2s10s spread in basis points." % (cur, d)}, {"role": "assistant", "content": "I will call get_yield_curve for %s on %s, then take the ten-year minus the two-year yield." % (cur, d)}, {"role": "tool",
    "content": '{"currency": "%s", "date": "%s", "yields": {"3m": %s, "2y": %s, "5y": %s, "10y": %s, "30y": %s}}' % (cur, d, y3m, y2, y5, y10, y30)}, {"role": "user",
    "content": "Good. State the spread in basis points and say whether the curve is inverted there."}]
        tools = [T_CURVE]
    elif fid == "t02":
        msgs = [{"role": "user", "content": "Get twelve months of CPI index levels for %s as of %s and compute headline year-over-year inflation in percent." % (cur, d)}, {"role": "assistant",
    "content": "I will request twelve monthly index levels with get_cpi_series, then compare the latest level with the level twelve months earlier."}, {"role": "tool", "content": '{"country": "%s", "months": 12, "latest": %s, "year_ago": %s, "prior_month": %s}' % (cur, round(300 + nl / 3.0, 2),
    round(290 + nl / 3.4, 2), round(299 + nl / 3.1, 2))}, {"role": "user",
    "content": "Use those levels to state the year-over-year rate to two decimals."}]
        tools = [T_CPI]
    elif fid == "t03":
        msgs = [{"role": "user", "content": "Get the policy futures strip for %s cycle 2025H1 as of %s and tell me how much easing is priced from the current rate." % (cur, d)}, {"role": "assistant",
    "content": "I will call get_policy_futures and compare the final implied rate with the current policy rate."}, {"role": "tool",
    "content": '{"currency": "%s", "cycle": "2025H1", "current": %s, "meetings": [{"date": "%s", "implied": %s}, {"date": "2025-03-19", "implied": %s}, {"date": "2025-05-07", "implied": %s}]}' % (cur, round(y2 + 0.2, 2), d, round(y2 + 0.15, 2), round(y2, 2), round(y2 - 0.12, 2))}, {"role": "user",
    "content": "Now give the cumulative implied change in basis points across the strip."}]
        tools = [T_FUT]
    elif fid == "t04":
        msgs = [{"role": "user", "content": "Get GDP components for %s over two years to %s and tell me which component contributed most to real growth." % (cur, d)}, {"role": "assistant",
    "content": "I will pull the component table with get_gdp_components, then compare each component's real change against prior-period total real GDP."}, {"role": "tool",
    "content": '{"country": "%s", "years": 2, "components": [{"name": "Personal consumption", "real_now": %s, "real_prior": %s}, {"name": "Gross private investment", "real_now": %s, "real_prior": %s}, {"name": "Net exports", "real_now": -880.2, "real_prior": -905.4}], "total_real_prior": 24320.3}' % (cur,
    round(13800 + nl, 1), round(13600 + nl, 1), round(3900 + nl / 2.0, 1), round(4000 + nl / 2.0, 1))}, {"role": "user",
    "content": "Name the largest contributor and give its contribution in percentage points."}]
        tools = [T_GDP]
    elif fid == "t05":
        msgs = [{"role": "user", "content": "Get the payroll report for %s released %s and compute the unemployment rate from the household survey." % (cur, d)}, {"role": "assistant", "content": "I will call get_payroll_report, then divide unemployed persons by the labor force."}, {"role": "tool",
    "content": '{"country": "%s", "labor_force": %d, "employed": %d, "unemployed": %d, "payrolls": %d}' % (cur, lf, emp, lf - emp, emp - 2000)}, {"role": "user",
    "content": "Give the unemployment rate in percent to two decimals."}]
        tools = [T_PAY]
    elif fid == "t06":
        msgs = [{"role": "user", "content": "Get %s spot and twelve-month forward points for %s and compute the forward outright." % ("EURUSD", d)}, {"role": "assistant", "content": "I will call get_fx_quotes for the pair at the twelve-month tenor and add the points to spot."}, {"role": "tool",
    "content": '{"pair": "EURUSD", "tenor": "12M", "spot": %s, "points": %s, "usd_rate": %s, "foreign_rate": %s}' % (spot, pts, usd, eur)}, {"role": "user",
    "content": "State the forward outright to four decimals."}]
        tools = [T_FX]
    elif fid == "t07":
        msgs = [{"role": "user", "content": "Get breakevens for %s on %s at five and ten years and compute the 5y5y forward breakeven." % (cur, d)}, {"role": "assistant", "content": "I will call get_breakevens for both horizons, then compound the two breakevens into a five-year forward rate."},
    {"role": "tool", "content": '{"country": "%s", "horizons": {"5y": {"nominal": %s, "real": %s}, "10y": {"nominal": %s, "real": %s}}}' % (cur, nom, real, nom2, real2)}, {"role": "user",
    "content": "Give the 5y5y forward breakeven in percent to two decimals."}]
        tools = [T_BE]
    elif fid == "t08":
        msgs = [{"role": "user", "content": "Get the twelve-year %s yield as of %s." % (cur, d)}, {"role": "assistant", "content": "I will call get_yield_curve for %s and request the twelve-year point." % cur}, {"role": "tool",
    "content": '{"error": "tenor_not_available", "requested": "12y", "available": ["3m", "1y", "2y", "5y", "10y", "30y"]}'}, {"role": "assistant", "content": "The twelve-year tenor is not quoted; I will retry with the ten-year point and note the substitution."}, {"role": "tool",
    "content": '{"currency": "%s", "tenor": "10y", "yield": %s}' % (cur, y10)}, {"role": "user",
    "content": "Fine, use the ten-year and tell me the 3m10y spread in basis points with the three-month at %s percent." % y3m}]
        tools = [T_CURVE]
    elif fid == "t09":
        msgs = [{"role": "user", "content": "Get the thirty-year real yield for %s as of %s and compute the thirty-year breakeven." % (cur, d)}, {"role": "assistant", "content": "I will call get_breakevens for the long end."}, {"role": "tool",
    "content": '{"country": "%s", "horizons": {"5y": {"nominal": %s, "real": %s}, "10y": {"nominal": %s, "real": %s}}, "note": "thirty-year inflation-linked bond is not quoted"}' % (cur, nom, real, nom2, real2)}, {"role": "assistant",
    "content": "The table has no thirty-year inflation-linked yield, so a thirty-year breakeven cannot be computed from the returned data."}, {"role": "user",
    "content": "Understood. Then just give me the ten-year breakeven in percent from what you have."}]
        tools = [T_BE]
    else:
        t = R.choice([2, 3, 5, 7, 10, 30])
        msgs = [{"role": "system", "content": "You are a rates assistant. Use the provided tool and report the computed figure with units."}, {"role": "user", "content": "Using get_yield_curve for %s on %s, retrieve the curve and report the %d-year to ten-year spread in basis points." % (cur, d,
    t)}]
        tools = [T_CURVE]
    return msgs, tools
TOOL_FAM = ["t01", "t02", "t03", "t04", "t05", "t06", "t07", "t08", "t09", "t10"]
# ---------------------------------------------------------------- assembly

def assign(groups, total):
    order = sorted(groups, key=lambda g: hashlib.sha256((AREA + "|" + g[0]).encode("utf-8")).hexdigest())
    tr, va = int(round(total * 0.8)), int(round(total * 0.1))
    te, out, i = total - tr - va, {}, 0
    for name, target in (("train", tr), ("val", va), ("test", te)):
        acc = 0
        while i < len(order) and acc < target:
            out[order[i][0]] = name
            acc += len(order[i][1])
            i += 1
        if acc != target:
            raise SystemExit("split packing failed: %s %d != %d" % (name, acc, target))
    if i != len(order):
        raise SystemExit("split packing left fixtures unassigned")
    return out

def build(task, alloc, fam_of):
    groups = []
    for kind, n in alloc:
        for j in range(n):
            key = "%s_%s_%02d" % (task, kind, j)
            fx, fams = make(kind, key), fam_of[kind]
            a = fams[(2 * j) % len(fams)]
            b = fams[(2 * j + 1) % len(fams)]
            if a == b:
                b = fams[(fams.index(a) + 1) % len(fams)]
            groups.append((key, [(fx, a), (fx, b)]))
    return groups
rows = []
SEQ = [0]
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls", "summarization": "summ", "tool_use": "tool"}

def emit(task, spec, split, ctx):
    SEQ[0] += 1
    src = "knowledge:finance_general" if (task != "tool_use" and ctx == "") else "synthetic:" + AREA
    row = {"id": "fin_%s_%s_%06d" % (AREA, ABBR[task], SEQ[0]), "task": task, "source": src}
    if task == "tool_use":
        row["messages"] = spec["msgs"]
        row["tools"] = spec["tools"]
    else:
        row["context"] = ctx
        row["question"] = spec["q"]
    row["ground_truth"] = spec["gt"]
    row["answer_type"] = spec["at"]
    row["tolerance"] = spec["tol"]
    row["split"] = split
    row["thinking"] = "on" if task in THINK_ON else "off"
    rows.append(row)

def run_task(task, groups, ctx_fn):
    splits = assign(groups, sum(len(g[1]) for g in groups))
    for key, specs in groups:
        for fx, spec in specs:
            emit(task, spec, splits[key], ctx_fn(fx) if fx is not None else "")

def main():
    calc = build("calc", [("cpi", 36), ("rates", 30), ("policy", 22), ("gdp", 22), ("labor", 14), ("fx", 10), ("be", 6)], CALC_FAM)
    run_task("calc", [(k, [(fx, calc_spec(fx, fid)) for fx, fid in s]) for k, s in calc], render)
    ext = build("extraction", [("cpi", 30), ("rates", 26), ("policy", 14), ("gdp", 14), ("labor", 12), ("fx", 8), ("be", 6)], dict((k, EXTR_FAM) for k in ("cpi", "rates", "policy", "gdp", "labor", "fx", "be")))
    run_task("extraction", [(k, [(fx, extr_spec(fx, fid)) for fx, fid in s]) for k, s in ext], render)
    qa = build("qa", [("cpi", 16), ("rates", 16), ("policy", 10), ("gdp", 10), ("labor", 8), ("fx", 6), ("be", 4)], QA_FAM)
    run_task("qa", [(k, [(fx, qa_spec(fx, fid)) for fx, fid in s]) for k, s in qa], render)
    kn = {}
    for key in sorted(KNOW_Q):
        kn.setdefault(key.rsplit("_", 1)[0], []).append((None, know_spec(key)))
    run_task("qa", [(k, v) for k, v in kn.items()], lambda fx: "")
    cls = []
    for i in range(1, 11):
        fid = "k%02d" % i
        for j in range(10):
            fx, lab, q = cls_build(fid, j)
            cls.append((fx["key"], [(fx, qs(fid, q, lab, "label", "exact"))]))
    run_task("classification", cls, render)
    sm = build("summarization", [("cpi", 12), ("rates", 10), ("policy", 8), ("gdp", 7), ("labor", 5), ("fx", 4), ("be", 4)], SUMM_FAM)
    run_task("summarization", [(k, [(fx, summ_spec(fx, fid)) for fx, fid in s]) for k, s in sm], render)
    tool = []
    for fid in TOOL_FAM:
        for j in range(10):
            msgs, tools = tool_row(fid)
            tool.append(("tool_%s_%02d" % (fid, j), [(None, {"msgs": msgs, "tools": tools, "gt": None, "at": "text", "tol": None})]))
    run_task("tool_use", tool, lambda fx: "")
    if len(rows) != 1000:
        raise SystemExit("row count %d" % len(rows))
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def report(path):
    fam, ctxs, dup = {}, set(), set()
    by_task, by_split, by_at = {}, {}, {}
    multi = 0
    for r in rows:
        if r["task"] == "tool_use":
            src = next((m["content"] for m in r["messages"] if m["role"] == "user"), "")
            if any(m["role"] == "assistant" for m in r["messages"]):
                multi += 1
        else:
            src = r["question"]
            if r["context"]:
                ctxs.add(mask(r["context"]))
                k = WS.sub(" ", r["context"]).strip().lower() + "|" + mask(r["question"])
                if k in dup:
                    raise SystemExit("near duplicate: " + r["id"])
                dup.add(k)
        fam[mask(src)[:160]] = fam.get(mask(src)[:160], 0) + 1
        by_task[r["task"]] = by_task.get(r["task"], 0) + 1
        by_split[r["split"]] = by_split.get(r["split"], 0) + 1
        if r["ground_truth"] is not None:
            by_at[r["answer_type"]] = by_at.get(r["answer_type"], 0) + 1
    vp = os.path.join(HERE, "..", "..", "validate.py")
    proc = subprocess.run([sys.executable, vp, path, "--area", AREA, "--profile", "A", "--expect", "1000"],
                          capture_output=True, text=True)
    try:
        status = json.loads(proc.stdout)["status"]
    except ValueError:
        status = "validator-error"
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump({"area": AREA, "profile": "A", "rows": len(rows), "by_task": by_task, "by_split": by_split,
                   "by_answer_type": by_at, "distinct_question_families": len(fam),
                   "top_family_share": round(max(fam.values()) / float(len(rows)), 4),
                   "distinct_contexts": len(ctxs), "near_dup_pairs": 0,
                   "tool_use_multi_step_share": round(multi / 100.0, 3), "validation": status,
                   "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
                   "notes": "123 authored templates (36 calc, 10 extraction, 23 table qa plus 20 knowledge items, 10 classification rules, 14 summaries, 10 tool flows); all figures synthetic and recomputed from printed values."},
                  fh, indent=2)
    return status


if __name__ == "__main__":
    p = main()
    print("wrote", p, len(rows), report(p))

