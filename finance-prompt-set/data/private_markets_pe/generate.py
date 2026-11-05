#!/usr/bin/env python3
"""Deterministic generator for the private_markets_pe area (profile A, 1000 rows).
Every figure is synthetic. Ground truth is always computed in code from the same
fixture values that are rendered into the context, so every answer is reproducible.
"""
import hashlib
import json
import os
import random
import re
from collections import Counter
from datetime import date, timedelta
R = random.Random(42)
AREA = "private_markets_pe"
HERE = os.path.dirname(os.path.abspath(__file__))
ABBR = {"calc": "calc", "extraction": "extr", "summarization": "summ",
        "classification": "cls", "qa": "qa", "tool_use": "tool"}
def num(x, dp=1):
    s = ("%." + str(dp) + "f") % float(x)
    if s.startswith("-") and float(s) == 0.0:
        s = s[1:]
    return s
def addm(d, months):
    y = d.year + (d.month - 1 + months) // 12
    mo = (d.month - 1 + months) % 12 + 1
    leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
    dim = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1]
    return date(y, mo, min(d.day, dim))
def seed_of(key):
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
def xnpv(rate, flows):
    t0 = flows[0][0]
    return sum(a / (1.0 + rate) ** ((d - t0).days / 365.0) for d, a in flows)
def xirr(flows):
    lo, hi = -0.9999, 20.0
    flo = xnpv(lo, flows)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        fm = xnpv(mid, flows)
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return 100.0 * 0.5 * (lo + hi)
def waterfall_eu(inv, proceeds, hurdle, years, carry, catchup):
    profit = proceeds - inv
    pref = inv * ((1.0 + hurdle / 100.0) ** years - 1.0)
    remaining = profit - pref
    if remaining <= 0:
        return dict(pref=pref, catch=0.0, carry=0.0, gp=0.0, lp=inv + max(profit, 0.0), resid=0.0)
    target = pref * carry / (100.0 - carry)
    pool = min(remaining, target / (catchup / 100.0)) if catchup > 0 else 0.0
    gp_catch = pool * catchup / 100.0
    resid = remaining - pool
    gp_carry = resid * carry / 100.0
    return dict(pref=pref, catch=gp_catch, carry=gp_carry, gp=gp_catch + gp_carry,
                lp=inv + pref + (pool - gp_catch) + (resid - gp_carry), resid=resid)
# --------------------------------------------------------------------------- registries
FUNDS = [
    dict(name="Kestrel Ridge Capital III", vintage=2018, commit=820.0, strategy="mid-market buyout", term=10, fee=2.0, carry=20, hurdle=8), dict(name="Halcyon Grid Partners II", vintage=2016, commit=1450.0, strategy="large-cap buyout", term=10, fee=1.75, carry=20, hurdle=8),
    dict(name="Meridian Street Buyout IV", vintage=2019, commit=2400.0, strategy="large-cap buyout", term=10, fee=1.6, carry=20, hurdle=8), dict(name="Alder Point Growth I", vintage=2020, commit=640.0, strategy="growth equity", term=10, fee=2.0, carry=20, hurdle=7),
    dict(name="Vantage Row Capital V", vintage=2015, commit=3100.0, strategy="large-cap buyout", term=10, fee=1.5, carry=20, hurdle=8), dict(name="Sable Harbour PE II", vintage=2017, commit=980.0, strategy="mid-market buyout", term=10, fee=2.0, carry=20, hurdle=8),
    dict(name="Northgate Equity Partners III", vintage=2014, commit=1750.0, strategy="mid-market buyout", term=10, fee=1.85, carry=20, hurdle=8), dict(name="Cobalt Meridian Buyout II", vintage=2019, commit=1320.0, strategy="healthcare buyout", term=10, fee=1.9, carry=20, hurdle=8),
    dict(name="Larkspur Vale Capital IV", vintage=2013, commit=760.0, strategy="small-cap buyout", term=10, fee=2.25, carry=20, hurdle=8), dict(name="Ironbark Holdco Partners I", vintage=2021, commit=540.0, strategy="industrials buyout", term=10, fee=2.0, carry=20, hurdle=8),
    dict(name="Silverbrook Continuation II", vintage=2020, commit=1100.0, strategy="secondaries", term=8, fee=1.75, carry=15, hurdle=7), dict(name="Tarn Ridge Buyout III", vintage=2016, commit=890.0, strategy="mid-market buyout", term=10, fee=2.0, carry=20, hurdle=8),
    dict(name="Quarry Lane Capital II", vintage=2018, commit=470.0, strategy="lower mid-market buyout", term=10, fee=2.25, carry=20, hurdle=8), dict(name="Windrow Peak Partners IV", vintage=2015, commit=2050.0, strategy="growth equity", term=10, fee=1.9, carry=20, hurdle=8),
    dict(name="Amberley Gate Buyout I", vintage=2022, commit=700.0, strategy="mid-market buyout", term=10, fee=2.0, carry=20, hurdle=8), dict(name="Pellham Cross Equity III", vintage=2017, commit=1240.0, strategy="mid-market buyout", term=10, fee=1.9, carry=20, hurdle=8),
    dict(name="Draymoor Capital V", vintage=2012, commit=1600.0, strategy="large-cap buyout", term=10, fee=1.75, carry=20, hurdle=8), dict(name="Foxglove Basin Partners II", vintage=2019, commit=610.0, strategy="renewable infrastructure", term=12, fee=1.5, carry=15, hurdle=7),
    dict(name="Hollowmere Buyout IV", vintage=2014, commit=950.0, strategy="mid-market buyout", term=10, fee=2.0, carry=20, hurdle=8), dict(name="Brackenridge Peak I", vintage=2021, commit=780.0, strategy="resources buyout", term=10, fee=2.0, carry=20, hurdle=8),
]
COMPANIES = [dict(zip(("name", "sector", "fy", "ccy"), t)) for t in [
    ("Alder Point Logistics", "transport and logistics", "31 December", "USD"), ("Bramblewood Foods", "packaged foods", "31 December", "USD"),
    ("Cobalt Meridian Diagnostics", "healthcare diagnostics", "30 September", "USD"), ("Draycott Industrial Coatings", "specialty chemicals", "31 December", "GBP"),
    ("Elmsworth Veterinary Group", "veterinary services", "31 March", "GBP"), ("Foxglove Basin Water", "water utilities", "31 December", "USD"),
    ("Grantham Reed Insurance", "specialty insurance", "31 December", "USD"), ("Hollowmere Care Homes", "elderly care", "31 March", "GBP"),
    ("Ironbark Timber Products", "building products", "30 June", "AUD"), ("Juniper Lane Pharmacies", "retail pharmacy", "31 December", "EUR"),
    ("Larkspur Vale Semiconductor", "semiconductor equipment", "31 December", "USD"), ("Millbrook Row Dental", "dental services", "31 December", "USD"),
    ("Northgate Equity Services", "business services", "31 December", "CAD"), ("Orchard Pike Brewing", "beverages", "31 December", "EUR"),
    ("Pellham Cross Analytics", "data analytics", "31 January", "USD"), ("Quarry Lane Plastics", "packaging", "31 December", "EUR"),
    ("Redfern Hollow Education", "education services", "31 August", "USD"), ("Sable Harbour Marine", "marine services", "31 December", "SGD"),
    ("Tarn Ridge Utilities", "regulated utilities", "31 December", "USD"), ("Vantage Row Payments", "payments processing", "31 December", "USD"),
    ("Windrow Peak Renewables", "renewable energy", "31 December", "EUR"), ("Amberley Gate Clinics", "outpatient clinics", "31 March", "USD"),
    ("Brackenridge Peak Minerals", "industrial minerals", "31 December", "AUD"),
]]
def build_cf(f, i):
    r = random.Random(seed_of("cf:" + f["name"]))
    d0 = date(f["vintage"], 3, 14)
    rows = []
    cw = [0.16, 0.21, 0.20, 0.19, 0.15]
    cm = [0, 7, 13, 19, 26]
    for k in range(5):
        amt = round(f["commit"] * cw[k] * (0.94 + 0.12 * r.random()), 1)
        rows.append((addm(d0, cm[k]), "Capital call", -amt))
    paid = round(-sum(a for _, _, a in rows), 1)
    mult = round(1.55 + 0.62 * r.random(), 3)
    navf = 0.22 + 0.30 * r.random()
    nav = round(paid * navf, 1)
    dist_total = round(paid * mult - nav, 1)
    dw = [0.07, 0.16, 0.24, 0.30, 0.23]
    dm = [30, 39, 48, 57, 66]
    dists = [round(dist_total * x, 1) for x in dw]
    dists[-1] = round(dist_total - sum(dists[:-1]), 1)
    for k in range(5):
        rows.append((addm(d0, dm[k]), "Distribution", dists[k]))
    nav_date = addm(d0, 78 + 6 * (i % 3))
    rows.append((nav_date, "Residual NAV", nav))
    flows = [(d, a) for d, _, a in rows]
    fees = round(f["commit"] * f["fee"] / 100.0 * 7.5, 1)
    delay = [(d + timedelta(days=365) if k == 8 else d, a) for k, (d, a) in enumerate(flows)]
    gross = [(d, nav + fees if k == len(flows) - 1 else a) for k, (d, a) in enumerate(flows)]
    return dict(rows=rows, paid=paid, dist=round(sum(dists), 1), nav=nav, fees=fees, irr=xirr(flows), irr_wo=xirr(flows[:-1]),
                irr_delay=xirr(delay), irr_gross=xirr(gross), nav_date=nav_date, tvpi=(sum(dists) + nav) / paid, moic=(sum(dists) + nav) / paid)


def build_wf(f, i):
    r = random.Random(seed_of("wf:" + f["name"]))
    inv = round(f["commit"] * (0.82 + 0.10 * r.random()), 1)
    proceeds = round(inv * (1.62 + 0.62 * r.random()), 1)
    years = 4 + (f["vintage"] % 4)
    return dict(inv=inv, proceeds=proceeds, years=years, profit=proceeds - inv, **waterfall_eu(inv, proceeds, f["hurdle"], years, f["carry"], 100))


def build_amer(f, i):
    r = random.Random(seed_of("am:" + f["name"]))
    deals = []
    for k in range(3):
        cost = round(f["commit"] * (0.07 + 0.05 * r.random()), 1)
        proceeds = round(cost * (1.15 + 0.95 * r.random()), 1)
        yrs = 2 + k + (f["vintage"] % 2)
        c = max(0.0, proceeds - cost * (1 + f["hurdle"] / 100.0) ** yrs) * f["carry"] / 100.0
        deals.append((cost, proceeds, yrs, round(c, 1)))
    return dict(deals=deals, total=round(sum(x[3] for x in deals), 1))


def build_lbo(co, i):
    r = random.Random(seed_of("lbo:" + co["name"]))
    eb = round(45 + 85 * r.random(), 1)
    mult = round(7.2 + 2.6 * r.random(), 1)
    ev = round(eb * mult, 1)
    senior = round(eb * (2.6 + 0.7 * r.random()), 1)
    uni = round(eb * (0.9 + 0.4 * r.random()), 1)
    mezz = round(eb * (0.25 + 0.3 * r.random()), 1)
    debt = round(senior + uni + mezz, 1)
    fees = round(ev * 0.015, 1)
    eq = round(ev + fees - debt, 1)
    sr = round(7.0 + 0.75 * r.random(), 2)
    ur = round(9.0 + 0.75 * r.random(), 2)
    mr = round(11.0 + 1.0 * r.random(), 2)
    interest = round(senior * sr / 100 + uni * ur / 100 + mezz * mr / 100, 1)
    g = 0.03 + 0.06 * r.random()
    xeb = round(eb * (1 + g) ** 5, 1)
    xmult = round(mult * (0.95 + 0.25 * r.random()), 1)
    xev = round(xeb * xmult, 1)
    paydown = round(debt * (0.10 + 0.15 * r.random()), 1)
    netdebt = round(debt - paydown, 1)
    xeq = round(xev - netdebt, 1)
    return dict(eb=eb, mult=mult, ev=ev, senior=senior, uni=uni, mezz=mezz, debt=debt, fees=fees, eq=eq, sr=sr, ur=ur, mr=mr,
                interest=interest, xeb=xeb, xmult=xmult, xev=xev, paydown=paydown, netdebt=netdebt, xeq=xeq,
                lev=debt / eb, cov=eb / interest, xlev=netdebt / xeb, moic=xeq / eq)


def build_j(f, i):
    r = random.Random(seed_of("jc:" + f["name"]))
    commit = f["commit"]
    cw = [0.18, 0.22, 0.20, 0.14, 0.09, 0.05, 0.02, 0.01]
    dw = [0.0, 0.0, 0.06, 0.13, 0.21, 0.28, 0.32, 0.34]
    nw = [0.16, 0.44, 0.70, 0.86, 0.92, 0.82, 0.66, 0.52]
    s = 0.85 + 0.25 * r.random()
    contrib = [round(commit * w * s, 1) for w in cw]
    dist = [round(commit * w * s, 1) for w in dw]
    nav = [round(commit * w * s, 1) for w in nw]
    fee = [round(commit * (f["fee"] / 100.0) * (1.0 if y <= 5 else 0.75), 1) for y in range(1, 9)]
    return dict(contrib=contrib, dist=dist, nav=nav, fee=fee, years=list(range(1, 9)), drag=sum(fee) / commit * 100.0)


def build_sl(f, i):
    r = random.Random(seed_of("sl:" + f["name"]))
    limit = round(f["commit"] * (0.15 + 0.10 * r.random()), 1)
    drawn = round(limit * (0.55 + 0.35 * r.random()), 1)
    days = 30 + 5 * (i % 9)
    draw = date(2024, 1 + (i % 12), 5 + (i % 20))
    rate = round(5.9 + 1.2 * r.random(), 2)
    cfee = round(0.25 + 0.20 * r.random(), 2)
    base = round(f["commit"] * f["fee"] / 100.0 / 4.0, 1)
    interest = drawn * rate / 100.0 * days / 365.0
    commitment = (limit - drawn) * cfee / 100.0 * days / 365.0
    return dict(limit=limit, drawn=drawn, days=days, draw=draw, repay=draw + timedelta(days=days), rate=rate, cfee=cfee,
                base=base, interest=interest, commit_fee=commitment, cost=interest + commitment, net=base - interest)
CF = [build_cf(f, i) for i, f in enumerate(FUNDS)]
WF = [build_wf(f, i) for i, f in enumerate(FUNDS)]
AM = [build_amer(f, i) for i, f in enumerate(FUNDS)]
LBO = [build_lbo(c, i) for i, c in enumerate(COMPANIES)]
JC = [build_j(f, i) for i, f in enumerate(FUNDS)]
SL = [build_sl(f, i) for i, f in enumerate(FUNDS)]
FIDX = {f["name"]: i for i, f in enumerate(FUNDS)}
# --------------------------------------------------------------------------- context renderers
def ctx_sched(f, cf):
    rows = "\n".join("| %s | %s | %s |" % (d.isoformat(), lab, num(a)) for d, lab, a in cf["rows"])
    return ("Units: $ in millions except percentages in percent.\n\nFund: %s (vintage %d, committed capital %s).\nDated LP cash flow schedule, inception through %s:\n"
            "| Date | Flow | Amount |\n|---|---|---|\n%s\nCumulative paid-in capital %s; cumulative distributions %s; residual net asset value %s; cumulative management fees %s.\n"
            "Note 1: capital calls are shown as negative amounts and distributions as positive amounts. Note 2: the terminal line is the residual net asset value marked by the GP, not a cash distribution."
            % (f["name"], f["vintage"], num(f["commit"]), cf["nav_date"].isoformat(), rows, num(cf["paid"]), num(cf["dist"]), num(cf["nav"]), num(cf["fees"])))


def ctx_sum(f, cf):
    return ("Units: $ in millions except percentages in percent.\n\nFund performance summary: %s, vintage %d, strategy %s.\n| Item | Amount |\n|---|---|\n"
            "| Commitments | %s |\n| Paid-in capital | %s |\n| Cumulative distributions | %s |\n| Remaining net asset value | %s |\n| Unfunded commitment | %s |\n| Cumulative management fees | %s |\n"
            % (f["name"], f["vintage"], f["strategy"], num(f["commit"]), num(cf["paid"]), num(cf["dist"]), num(cf["nav"]), num(f["commit"] - cf["paid"]), num(cf["fees"])))


def ctx_terms(f, wf):
    return ("Units: $ in millions except percentages in percent.\n\nTerm sheet extract: %s, L.P. (vintage %d).\n| Term | Provision |\n|---|---|\n"
            "| Fund size | %s |\n| Investment period | 5 years from first closing |\n| Fund term | %d years, extendable twice by one year with LPAC consent |\n"
            "| Management fee | %s percent of committed capital during the investment period, %s percent thereafter |\n"
            "| Carried interest | %d percent of profits, subject to a compounded preferred return of %d percent |\n"
            "| Preferred return | %d percent compounded annually on invested capital |\n| Catch-up | 100 percent to the GP until the GP holds %d percent of cumulative profit |\n"
            "| Fee offset | 100 percent of transaction fees and 50 percent of monitoring fees offset against the management fee |\n"
            "| Subscription line | 150.0 limit, secured, 6.75 percent per annum, 45 day maximum draw |\n"
            "| LPAC | Five LP members elected annually; consent required for affiliated transactions |\n| Key person | Key person event suspends the investment period for 180 days |\n"
            "| Clawback | Interim clawback at each distribution; final clawback within 90 days of liquidation |\n"
            "| Invested capital at exit | %s |\n| Total proceeds at exit | %s |\n| Holding period (years) | %d |\n"
            "Note 1: fees and carry are stated on committed capital unless a provision says otherwise. Note 2: the subscription line is repaid from the next capital call."
            % (f["name"], f["vintage"], num(f["commit"]), f["term"], num(f["fee"], 2), num(f["fee"] - 0.5, 2), f["carry"], f["hurdle"],
               f["hurdle"], f["carry"], num(wf["inv"]), num(wf["proceeds"]), wf["years"]))


def ctx_lbo(co, l):
    return ("Units: $ in millions except percentages in percent and multiples in turns.\n\nLeveraged buyout model: %s (%s), entry 30 June 2021, exit 30 June 2026.\n| Entry item | Value |\n|---|---|\n"
            "| Entry enterprise value | %s |\n| Entry EBITDA | %s |\n| Senior secured term loan | %s |\n| Unitranche term loan | %s |\n| Mezzanine notes | %s |\n"
            "| Sponsor equity | %s |\n| Transaction fees | %s |\n| Senior margin (percent) | %s |\n| Unitranche margin (percent) | %s |\n| Mezzanine coupon (percent) | %s |\n"
            "| Exit EBITDA | %s |\n| Exit multiple (turns) | %s |\n| Cumulative debt paydown | %s |\n"
            % (co["name"], co["sector"], num(l["ev"]), num(l["eb"]), num(l["senior"]), num(l["uni"]), num(l["mezz"]), num(l["eq"]),
               num(l["fees"]), num(l["sr"], 2), num(l["ur"], 2), num(l["mr"], 2), num(l["xeb"]), num(l["xmult"]), num(l["paydown"])))


def ctx_j(f, j):
    rows = "\n".join("| %d | %s | %s | %s | %s |" % (j["years"][k], num(j["contrib"][k]), num(j["dist"][k]), num(j["nav"][k]), num(j["fee"][k])) for k in range(8))
    return ("Units: $ in millions except percentages in percent.\n\nFund: %s, committed capital %s. Annual cash flow history, fund years 1 through 8.\n"
            "| Year | Contributions | Distributions | Net asset value | Management fee |\n|---|---|---|---|---|\n%s\n"
            "Distributions and net asset value are measured at each year end; no capital remains committed after year eight." % (f["name"], num(f["commit"]), rows))


def ctx_sl(f, s):
    return ("Units: $ in millions except percentages in percent.\n\nSubscription line facility: %s.\n| Item | Value |\n|---|---|\n"
            "| Facility limit | %s |\n| Drawn amount | %s |\n| Draw date | %s |\n| Repayment date | %s |\n| Days outstanding | %d |\n| All-in rate (percent) | %s |\n"
            "| Commitment fee on undrawn (percent) | %s |\n| Management fee for the period before offset | %s |\n| Fee offset ratio (percent) | 100 |\n"
            % (f["name"], num(s["limit"]), num(s["drawn"]), s["draw"].isoformat(), s["repay"].isoformat(), s["days"], num(s["rate"], 2), num(s["cfee"], 2), num(s["base"])))


def ctx_cmp(funds):
    head = "| Item | " + " | ".join(f["name"] for f in funds) + " |"
    sep = "|---" * (len(funds) + 1) + "|"
    rows = ["| Vintage | " + " | ".join(str(f["vintage"]) for f in funds) + " |", "| Commitments | " + " | ".join(num(f["commit"]) for f in funds) + " |"]
    for lab, key in (("Paid-in capital", "paid"), ("Cumulative distributions", "dist"), ("Remaining net asset value", "nav"), ("Cumulative management fees", "fees")):
        rows.append("| %s | " % lab + " | ".join(num(CF[FIDX[f["name"]]][key]) for f in funds) + " |")
    return "Units: $ in millions except percentages in percent.\n\nFund comparison table, %d vehicles managed by the same sponsor.\n%s\n%s\n%s" % (len(funds), head, sep, "\n".join(rows))


def ctx_update(f, cf, q):
    return ("Units: $ in millions except percentages in percent.\n\nQuarterly LP update, %s, quarter ended %s.\n"
            "Net asset value at quarter end was %s, against %s at the prior quarter end. Cumulative distributions since inception were %s against paid-in capital of %s. The fund called %s during the quarter and distributed %s.\n"
            "| Metric | Value |\n|---|---|\n| Commitments | %s |\n| Unfunded commitment | %s |\n| Portfolio companies held | %d |\n| Average entry multiple (turns) | %s |\n| Net debt to EBITDA at fund level (turns) | %s |\n"
            "Portfolio notes: Bramblewood Foods grew trailing EBITDA 6 percent on flat revenue; Draycott Industrial Coatings was marked down 4 percent on raw material pressure. No new capital was committed and the fund holds %s of unfunded commitments.\n"
            % (f["name"], q, num(cf["nav"]), num(cf["nav"] * 0.96), num(cf["dist"]), num(cf["paid"]), num(cf["paid"] * 0.035), num(cf["dist"] * 0.02),
               num(f["commit"]), num(f["commit"] - cf["paid"]), 3 + (f["vintage"] % 6), num(7.4 + 0.3 * (f["vintage"] % 4)), num(4.1 + 0.2 * (f["vintage"] % 5)), num(f["commit"] - cf["paid"])))


def ctx_cov(co, eb, lev):
    return ("Units: $ in millions except percentages in percent and multiples in turns.\n\nCovenant compliance certificate: %s, test date 30 June 2025.\n| Item | Value |\n|---|---|\n"
            "| Consolidated EBITDA | %s |\n| Total net debt | %s |\n| Springing covenant threshold (turns) | 5.0 |\n| Headroom to covenant (turns) | %s |\n" % (co["name"], num(eb), num(eb * lev), num(5.0 - lev, 2)))


def ctx_reg(f, picks):
    return ("Units: $ in millions except percentages in percent.\n\nLP rights register: %s, L.P.\n| Ref | Provision |\n|---|---|\n%s"
            % (f["name"], "\n".join("| R%d | %s |" % (k + 1, picks[k]) for k in range(4))))


CASES = []
def A(task, key, ctx, q, gt, at="number", tol="abs:0.1"):
    CASES.append(dict(task=task, key=key, ctx=ctx, q=q, gt=gt, at=at, tol=tol))
def calc_cases():
    CTX = {"cf": lambda i: ctx_sched(FUNDS[i], CF[i]), "sum": lambda i: ctx_sum(FUNDS[i], CF[i]),
           "wf": lambda i: ctx_terms(FUNDS[i], WF[i]), "lbo": lambda i: ctx_lbo(COMPANIES[i], LBO[i]),
           "jc": lambda i: ctx_j(FUNDS[i], JC[i]), "sl": lambda i: ctx_sl(FUNDS[i], SL[i])}
    NM = {"lbo": lambda i: COMPANIES[i]["name"]}
    specs = [
        ("cf", 20, "What is the net IRR of %s from the dated cash flow schedule, in percent?", lambda i: CF[i]["irr"], 2, "rel:0.01"),
        ("cf", 10, "If the residual net asset value of %s is written off to zero at the terminal date, what is the IRR of the remaining cash flows, in percent?", lambda i: CF[i]["irr_wo"], 2, "rel:0.02"),
        ("cf", 10, "If the cumulative management fees of %s are added back to the terminal net asset value, what is the gross IRR, in percent?", lambda i: CF[i]["irr_gross"], 2, "rel:0.02"),
        ("sum", 16, "What is the multiple on invested capital (MOIC) of %s, in turns?", lambda i: CF[i]["moic"], 3, "abs:0.02"),
        ("sum", 16, "What is the DPI of %s, in turns?", lambda i: CF[i]["dist"] / CF[i]["paid"], 3, "abs:0.02"),
        ("sum", 16, "What is the RVPI of %s, in turns?", lambda i: CF[i]["nav"] / CF[i]["paid"], 3, "abs:0.02"),
        ("sum", 16, "What is the TVPI of %s, in turns?", lambda i: CF[i]["tvpi"], 3, "abs:0.02"),
        ("wf", 12, "Under the European waterfall in the term sheet, how much carried interest does the GP receive on the stated gain for %s, in millions?", lambda i: WF[i]["gp"], 1, "abs:0.2"),
        ("wf", 10, "Under the European waterfall, what are the LP's total proceeds at exit for %s, in millions?", lambda i: WF[i]["lp"], 1, "abs:0.2"),
        ("wf", 10, "How much does the GP receive in the catch-up tier of the %s waterfall, in millions?", lambda i: WF[i]["catch"], 1, "abs:0.2"),
        ("wf", 8, "What share of the total profit of %s goes to the GP after the full waterfall, in percent?", lambda i: WF[i]["gp"] / WF[i]["profit"] * 100.0, 2, "abs:0.1"),
        ("lbo", 10, "What is opening leverage at entry for %s, in turns of entry EBITDA?", lambda i: LBO[i]["lev"], 2, "abs:0.02"),
        ("lbo", 8, "What equity cheque does the sponsor write at entry for %s, in millions?", lambda i: LBO[i]["eq"], 1, "abs:0.2"),
        ("lbo", 8, "What is the annual interest expense at entry for %s, in millions?", lambda i: LBO[i]["interest"], 1, "abs:0.2"),
        ("lbo", 8, "What is EBITDA interest coverage at entry for %s, in turns?", lambda i: LBO[i]["cov"], 2, "abs:0.02"),
        ("lbo", 8, "What exit enterprise value does the exit multiple imply for %s, in millions?", lambda i: LBO[i]["xev"], 1, "abs:0.2"),
        ("lbo", 8, "What is the sponsor's exit equity value for %s, in millions?", lambda i: LBO[i]["xeq"], 1, "abs:0.2"),
        ("lbo", 8, "What is the LBO money multiple on the sponsor equity for %s, in turns?", lambda i: LBO[i]["moic"], 2, "abs:0.02"),
        ("lbo", 6, "What leverage remains at exit for %s, in turns of exit EBITDA?", lambda i: LBO[i]["xlev"], 2, "abs:0.02"),
        ("jc", 8, "What is the cumulative management fee drag for %s over the eight years, in percent of committed capital?", lambda i: JC[i]["drag"], 2, "abs:0.1"),
        ("jc", 8, "What is the net TVPI of %s at the end of year six, in turns?", lambda i: (sum(JC[i]["dist"][:6]) + JC[i]["nav"][5]) / sum(JC[i]["contrib"][:6]), 3, "abs:0.02"),
        ("jc", 8, "What is the change in net asset value of %s from the end of year four to the end of year five, in millions?", lambda i: JC[i]["nav"][4] - JC[i]["nav"][3], 1, "abs:0.2"),
        ("sl", 8, "What is the interest cost of the subscription line for %s over the draw period, in millions?", lambda i: SL[i]["interest"], 3, "abs:0.01"),
        ("sl", 8, "How much management fee is offset by the subscription line interest for %s, in millions?", lambda i: SL[i]["interest"], 3, "abs:0.01"),
        ("sl", 8, "What is the management fee for the period after the fee offset for %s, in millions?", lambda i: SL[i]["net"], 3, "abs:0.02"),
        ("sl", 6, "What is the all-in cost of the subscription line for %s, including the commitment fee on the undrawn amount, in millions?", lambda i: SL[i]["cost"], 3, "abs:0.01")]
    def emit(seq):
        for kind, n, q, fn, dp, tol in seq:
            for i in range(n):
                nm = NM.get(kind, lambda i: FUNDS[i]["name"])(i)
                A("calc", kind + ":" + nm, CTX[kind](i), q % nm, round(fn(i), dp), "number", tol)
    emit(specs[:2])
    for i in range(8):
        f, cf = FUNDS[i], CF[i]
        A("calc", "cf:" + f["name"], ctx_sched(f, cf), "For %s, if the distribution dated %s is received twelve months later than scheduled, what is the IRR, in percent?" % (f["name"], cf["rows"][8][0].isoformat()), round(cf["irr_delay"], 2), "number", "rel:0.02")
    emit(specs[2:11])
    for i in range(10):
        f, am = FUNDS[i], AM[i]
        rows = "\n".join("| Exit %d | %s | %s | %d |" % (k + 1, num(c), num(p), y) for k, (c, p, y, _) in enumerate(am["deals"]))
        ctx = ("Units: $ in millions except percentages in percent.\n\nDeal-by-deal (American) waterfall: %s, carry %d percent, hurdle %d percent compounded annually, no cross-collateralisation between exits.\n"
               "| Exit | Invested cost | Proceeds | Holding period (years) |\n|---|---|---|---|\n%s" % (f["name"], f["carry"], f["hurdle"], rows))
        A("calc", "am:" + f["name"], ctx, "Under the deal-by-deal waterfall, what is the total carried interest paid to the GP across the three exits of %s, in millions?" % f["name"], round(am["total"], 1), "number", "abs:0.2")
    emit(specs[11:])


def extraction_cases():
    for i, f in enumerate(FUNDS):
        cf = CF[i]
        c = ctx_sched(f, cf)
        d, a = cf["rows"][8][0].isoformat(), cf["rows"][8][2]
        A("extraction", "cf:" + f["name"], c, "Extract the distribution amount paid on %s in the %s cash flow schedule, in millions." % (d, f["name"]), round(a, 1), "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        cf = CF[i]
        A("extraction", "cf:" + f["name"], ctx_sched(f, cf), "Extract the signed amount shown for the capital call made on %s in the %s cash flow schedule, in millions." % (cf["rows"][1][0].isoformat(), f["name"]), round(cf["rows"][1][2], 1), "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "cf:" + f["name"], ctx_sched(f, CF[i]), "Extract the residual net asset value shown at the terminal date for %s, in millions." % f["name"], round(CF[i]["nav"], 1), "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "cf:" + f["name"], ctx_sched(f, CF[i]), "Extract the cumulative management fees stated for %s, in millions." % f["name"], round(CF[i]["fees"], 1), "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "wf:" + f["name"], ctx_terms(f, WF[i]), "Extract the management fee rate that applies during the investment period for %s, in percent." % f["name"], f["fee"], "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "wf:" + f["name"], ctx_terms(f, WF[i]), "Extract the preferred return stated in the %s term sheet, in percent." % f["name"], f["hurdle"], "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "wf:" + f["name"], ctx_terms(f, WF[i]), "Extract the carried interest rate stated in the %s term sheet, in percent." % f["name"], f["carry"], "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "wf:" + f["name"], ctx_terms(f, WF[i]), "Extract the fund term in years stated in the %s term sheet." % f["name"], f["term"], "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "wf:" + f["name"], ctx_terms(f, WF[i]), "Quote the fee offset provision for transaction and monitoring fees in the %s term sheet, verbatim." % f["name"], "100 percent of transaction fees and 50 percent of monitoring fees offset against the management fee", "text", "normalized")
    for i, f in enumerate(FUNDS):
        A("extraction", "sl:" + f["name"], ctx_sl(f, SL[i]), "Extract the facility limit of the subscription line for %s, in millions." % f["name"], round(SL[i]["limit"], 1), "number", "abs:0.01")
    for i, f in enumerate(FUNDS):
        A("extraction", "wf:" + f["name"], ctx_terms(f, WF[i]), "Quote the key person provision in the %s term sheet, verbatim." % f["name"], "Key person event suspends the investment period for 180 days", "text", "normalized")
KNOW = [
    ("What does TVPI measure, and how does it differ from MOIC?", "TVPI divides total value, meaning cumulative distributions plus remaining net asset value, by paid-in capital; MOIC compares value with invested cost and is usually quoted for a single deal or a portfolio rather than the whole fund."),
    ("Define DPI and explain what a DPI above one implies.", "DPI is cumulative distributions divided by paid-in capital; a DPI above one means the fund has already returned more cash to LPs than it has called."),
    ("Define RVPI and state why it can be manipulated by valuation marks.", "RVPI is remaining net asset value divided by paid-in capital, so it depends entirely on unrealised carrying values, which the GP marks and which may not be realised."),
    ("How does a European waterfall differ from an American waterfall?", "A European waterfall applies the preferred return and carry to the whole fund after all capital is returned, while an American waterfall calculates carry deal by deal as each investment is realised."),
    ("Explain the mechanics of a GP catch-up in a fund waterfall.", "After LPs receive their preferred return, the catch-up gives the GP a stated share of subsequent distributions until the GP holds its target share of cumulative profit, after which remaining profit is split in the carry ratio."),
    ("What is a preferred return or hurdle rate, and how does it accrue?", "A preferred return is the minimum annual return LPs receive before the GP shares in profit; it usually compounds on invested or unreturned capital until distributions catch up."),
    ("Explain how a clawback protects limited partners.", "A clawback requires the GP to return carried interest that exceeds its contractual share once the whole fund is wound up, typically supported by an escrow of part of each distribution."),
    ("What is a subscription line facility and why can it flatter reported IRR?", "A subscription line is fund-level debt used to delay capital calls; because LP cash sits in the fund for a shorter period while returns are measured over the same distributions, the timing effect raises the calculated IRR without changing profit."),
    ("Explain the J-curve in private equity fund performance.", "The J-curve describes early negative returns while fees and write-downs accumulate, followed by rising value as investments mature, so interim IRR is low and later improves."),
    ("How does a management fee offset work?", "A fee offset reduces the management fee by a stated share of transaction, monitoring or other fees the GP receives from portfolio companies, so LPs pay less in net fees."),
    ("What is the role of a limited partner advisory committee?", "The LPAC reviews conflicts of interest, affiliated transactions, valuation policy and term amendments, and gives advice to the GP without managing the fund."),
    ("Explain a key person clause in a fund agreement.", "A key person clause suspends or terminates the investment period if named professionals leave or become unable to work, giving LPs protection against a change in the investment team."),
    ("What is a no-fault removal right for limited partners?", "A no-fault removal right lets a supermajority of LPs remove the GP without proving cause, usually after the investment period and often with a termination fee."),
    ("Why do GPs commit their own capital to a fund?", "The GP commitment aligns interests with LPs and is typically one to five percent of commitments, sometimes funded through fee waivers."),
    ("How do fund term and extension options affect LP liquidity?", "A fund term sets the expected wind-down date, and extension options let the GP hold assets longer with LP or LPAC consent, delaying distributions to LPs."),
    ("What is a continuation fund and what conflict does it create?", "A continuation fund buys assets from an expiring fund, letting the GP hold them longer; the conflict is that the GP sets the price and chooses which LPs roll over or cash out."),
    ("What are recallable distributions?", "Recallable distributions are proceeds a fund may call back from LPs during the investment period to fund new investments or expenses, which reduces the effective DPI reported early."),
    ("Contrast fund-level carry with deal-by-deal carry.", "Fund-level carry is struck once at the end of the fund against total profit, while deal-by-deal carry is paid as each investment exits, which pays the GP earlier and exposes LPs to clawback risk."),
    ("How does a NAV facility differ from a subscription line?", "A subscription line is secured by unfunded LP commitments and repaid when capital is called, while a NAV facility is secured by the fund's investment portfolio and is used for liquidity rather than to bridge calls."),
    ("Why is IRR alone a weak measure of private equity performance?", "IRR depends on the size and timing of cash flows and assumes reinvestment at the same rate, so a small early distribution can lift IRR without creating value; MOIC or TVPI should be read alongside it."),
]
QV = ["%s", "%s Answer in one or two sentences.", "Briefly: %s"]
def window(size, seed, used=None):
    used = used if used is not None else set()
    for off in range(20):
        idx = tuple((2 * seed + off + k) % 20 for k in range(size))
        if len(set(idx)) != size or idx in used:
            continue
        paid = [CF[i]["paid"] for i in idx]
        dist = [CF[i]["dist"] for i in idx]
        nav = [CF[i]["nav"] for i in idx]
        fees = [CF[i]["fees"] for i in idx]
        com = [FUNDS[i]["commit"] for i in idx]
        vecs = [[round(dist[j] / paid[j], 3) for j in range(size)],
                [round((dist[j] + nav[j]) / paid[j], 3) for j in range(size)],
                [round(nav[j] / paid[j], 3) for j in range(size)],
                [round(com[j] - paid[j], 1) for j in range(size)],
                [round(fees[j], 3) for j in range(size)]]
        if all(len(set(v)) == size for v in vecs):
            used.add(idx)
            return list(idx)
    idx = tuple((2 * seed + k) % 20 for k in range(size))
    used.add(idx)
    return list(idx)
def qa_cases():
    for q, ans in KNOW:
        for v in QV:
            A("qa", "know:" + q[:40], "", v % q, ans, "text", "normalized")
    used5 = set()
    for w in range(10):
        idx = window(5, w, used5)
        funds = [FUNDS[i] for i in idx]
        c, k = ctx_cmp(funds), "cmp5:%d" % w
        nm = ", ".join(f["name"] for f in funds)
        paid = [CF[i]["paid"] for i in idx]
        dist = [CF[i]["dist"] for i in idx]
        nav = [CF[i]["nav"] for i in idx]
        tvpi = [(dist[i] + nav[i]) / paid[i] for i in range(5)]
        best = funds[tvpi.index(max(tvpi))]
        A("qa", k, c, "In the five-fund comparison (%s), which fund has the highest TVPI?" % nm, best["name"], "text", "normalized")
        worst = funds[tvpi.index(min(tvpi))]
        A("qa", k, c, "In the five-fund comparison (%s), which fund has the lowest TVPI?" % nm, worst["name"], "text", "normalized")
        dpi = [dist[i] / paid[i] for i in range(5)]
        A("qa", k, c, "Rank these five funds from highest to lowest DPI: %s." % nm, [funds[i]["name"] for i in sorted(range(5), key=lambda i: -dpi[i])], "list", "ordered")
        A("qa", k, c, "Across the five funds (%s), what is the spread between the highest and lowest DPI, in turns?" % nm, round(max(dpi) - min(dpi), 3), "number", "abs:0.02")
        A("qa", k, c, "For the group %s, what is the aggregate unfunded commitment, in millions?" % nm, round(sum(f["commit"] - CF[FIDX[f["name"]]]["paid"] for f in funds), 1), "number", "abs:0.2")
        A("qa", k, c, "What is the combined TVPI of %s, calculated on aggregate distributions, net asset value and paid-in capital, in turns?" % nm, round((sum(dist) + sum(nav)) / sum(paid), 3), "number", "abs:0.02")
        srt = sorted(dpi)
        A("qa", k, c, "What is the median DPI of the five funds %s, in turns?" % nm, round(srt[2], 3), "number", "abs:0.02")
        A("qa", k, c, "Which of the five funds (%s) has the largest unfunded commitment in absolute terms?" % nm, funds[[f["commit"] - CF[FIDX[f["name"]]]["paid"] for f in funds].index(max(f["commit"] - CF[FIDX[f["name"]]]["paid"] for f in funds))]["name"], "text", "normalized")
    used3 = set()
    for w in range(10):
        idx = window(3, w, used3)
        funds = [FUNDS[i] for i in idx]
        c, k = ctx_cmp(funds), "cmp3:%d" % w
        nm = ", ".join(f["name"] for f in funds)
        paid = [CF[i]["paid"] for i in idx]
        dist = [CF[i]["dist"] for i in idx]
        nav = [CF[i]["nav"] for i in idx]
        fees = [CF[i]["fees"] for i in idx]
        tvpi = [(dist[i] + nav[i]) / paid[i] for i in range(3)]
        A("qa", k, c, "Of %s, which fund has generated the most cash relative to paid-in capital?" % nm, funds[[dist[i] / paid[i] for i in range(3)].index(max(dist[i] / paid[i] for i in range(3)))]["name"], "text", "normalized")
        A("qa", k, c, "Of %s, which fund carries the heaviest fee load relative to commitments?" % nm, funds[fees.index(max(fees))]["name"], "text", "normalized")
        A("qa", k, c, "What is the aggregate net asset value of %s, in millions?" % nm, round(sum(nav), 1), "number", "abs:0.2")
        A("qa", k, c, "Across %s, how much capital has been returned to LPs but not yet called, in millions?" % nm, round(max(0.0, sum(dist) - sum(paid)), 1), "number", "abs:0.2")
        A("qa", k, c, "Rank %s by RVPI from highest to lowest." % nm, [funds[i]["name"] for i in sorted(range(3), key=lambda i: -(nav[i] / paid[i]))], "list", "ordered")
        A("qa", k, c, "For %s, what proportion of combined commitments has been called, in percent?" % nm, round(sum(paid) / sum(f["commit"] for f in funds) * 100.0, 2), "number", "abs:0.1")
CLAUSES = {
    "governance": [
        "LPAC consent is required before the fund may co-invest alongside an affiliate of the GP", "A key person event suspends the investment period until a replacement is approved", "The GP may be removed for cause by a majority of commitments",
        "The LPAC must review any proposed amendment to the partnership agreement", "An annual meeting of limited partners must be held within 120 days of year end", "The GP must obtain LPAC approval before extending the fund term",
        "Any change to the investment mandate requires approval of a majority of commitments", "The GP must present its valuation policy to the LPAC each year", "Related-party transactions require LPAC review before closing",
        "The GP may not amend the fee schedule without LP consent",
    ],
    "economics": [
        "Distributions in kind require LPAC approval and must be made at fair value", "The GP returns 20 percent of carried interest if the fund fails to clear the preferred return", "Management fees step down from 2.0 percent to 1.5 percent after the investment period",
        "Transaction fees received by the GP offset the management fee dollar for dollar", "The preferred return compounds annually at 8 percent on invested capital", "Recallable distributions may be called back during the investment period",
        "The GP bears 100 percent of broken-deal expenses above the agreed cap", "Carried interest is calculated on a whole-of-fund basis at final liquidation", "Organisation expenses are capped at 0.15 percent of commitments",
        "The GP funds its commitment partly through waived management fees",
    ],
    "exit": [
        "A limited partner may transfer its interest only with GP consent and a right of first refusal", "Tag-along rights apply to any GP-led secondary transaction", "LPs holding 25 percent of commitments may request an orderly wind-down",
        "A continuation fund requires approval from a majority of disinterested LPs", "The GP may sell a portfolio company without LP consent after year five", "LPs may elect to roll into a continuation vehicle or receive cash at the stated price",
        "A drag-along right lets the GP sell the fund's stake alongside a majority buyer", "The fund must distribute proceeds within 90 days of a realisation", "LPs may redeem their interest after the investment period subject to a discount",
        "The GP must offer co-investment exit rights to rolling LPs",
    ],
    "information": [
        "Quarterly reports are delivered within 45 days of quarter end", "Audited financial statements are delivered within 120 days of year end", "The GP provides portfolio company EBITDA and net debt in each quarterly report",
        "LPs receive an annual summary of management fees and expenses", "Capital account statements are issued semi-annually", "The GP discloses its co-investment allocation policy in the quarterly letter",
        "LPs receive notice of any portfolio company impairment within 10 business days", "The annual meeting pack includes fund-level and deal-level performance", "The GP reports uncalled commitments and subscription line usage each quarter",
        "LPs may request the valuation memorandum for any portfolio company annually",
    ],
}
def classification_cases():
    cats = ["governance", "economics", "exit", "information"]
    for i, f in enumerate(FUNDS[:10]):
        picks = [CLAUSES[c][i] for c in cats]
        ctx = ctx_reg(f, picks)
        stem = ["Classify the LP right in row R%d using one of {governance, economics, information, exit}.",
                "Which category does the right in row R%d belong to? Choose one of {governance, economics, information, exit}.",
                "Label the right in row R%d as one of {governance, economics, information, exit}.",
                "State the category of the right in row R%d: one of {governance, economics, information, exit}."]
        for k in range(4):
            q = ("In the %s LP rights register, " % f["name"]) + stem[(i + k) % 4] % (k + 1)
            A("classification", "reg:" + f["name"], ctx, q, cats[k], "label", "exact")
    levels = []
    for k in range(8):
        levels.append(("compliant", 3.1 + 0.18 * k))
    for k in range(8):
        levels.append(("watch", 4.80 + 0.025 * k))
    for k in range(8):
        levels.append(("breach", 5.12 + 0.12 * k))
    rule = ("The credit agreement classifies leverage as compliant when headroom is 0.25 turns or more, "
            "watch when headroom is positive but below 0.25 turns, and breach when leverage exceeds the threshold. ")
    for k, (lab, lev) in enumerate(levels):
        co = COMPANIES[k % len(COMPANIES)]
        eb = round(60 + 5 * (k % 7), 1)
        ctx = ctx_cov(co, eb, lev) if k < 23 else ctx_cov(co, eb, lev).replace("Covenant compliance certificate", "Amended covenant compliance certificate")
        A("classification", "cov:" + co["name"], ctx, rule + "Classify the covenant position of %s: leverage is %s turns against a 5.0 turn threshold. Use one of {compliant, watch, breach}." % (co["name"], num(lev, 2)), lab, "label", "exact")
    srule = ("Stage rule: investment while DPI is below 0.25, harvesting while DPI is between 0.25 and 0.85, "
             "mature once DPI is 0.85 or above. ")
    for k in range(24):
        f = FUNDS[k % 20]
        j = JC[k % 20]
        yr = 2 + (k % 7)
        if k < 8:
            dpi = round(0.06 + 0.02 * k, 2)
            lab = "investment"
        elif k < 16:
            dpi = round(0.30 + 0.07 * (k - 8), 2)
            lab = "harvesting"
        else:
            dpi = round(0.88 + 0.06 * (k - 16), 2)
            lab = "mature"
        rvpi = round(max(0.1, 1.5 - dpi), 2)
        paid = j["contrib"][min(yr, 8) - 1] * 3
        ctx = ("Units: $ in millions except percentages in percent and multiples in turns.\n\n"
               "%s: %s, fund year %d.\n"
               "| Metric | Value |\n|---|---|\n| Paid-in capital | %s |\n| Cumulative distributions | %s |\n"
               "| Net asset value | %s |\n| DPI (turns) | %s |\n| RVPI (turns) | %s |\n"
               % ("Fund stage monitor" if k < 20 else "Interim fund stage monitor", f["name"], yr, num(paid), num(dpi * paid), num(rvpi * paid), num(dpi, 2), num(rvpi, 2)))
        A("classification", "stg:" + f["name"] + str(yr), ctx, srule + "Classify the lifecycle stage of %s at fund year %d using one of {investment, harvesting, mature}." % (f["name"], yr), lab, "label", "exact")
    wf_types = [("european", "Carry is calculated once, on total fund profit, after all capital and the preferred return have been returned to LPs."),
                ("american", "Carry is calculated and paid on each realised investment separately as it exits, with no cross-collateralisation."),
                ("hybrid", "Carry is paid deal by deal after a deal-level hurdle, but realised losses may be clawed back against later gains.")]
    for k in range(12):
        lab, desc = wf_types[k % 3]
        f = FUNDS[k]
        ctx = ("Units: $ in millions except percentages in percent.\n\n"
               "Waterfall description provided by the GP of %s.\n%s\n"
               "The fund charges %d percent carry over a %d percent hurdle." % (f["name"], desc, f["carry"], f["hurdle"]))
        A("classification", "wft:" + f["name"], ctx, "Classify the waterfall structure described for %s as one of {european, american, hybrid}." % f["name"], lab, "label", "exact")
def summ_cases():
    qs = ["Summarize the quarterly update of %s for the investment committee in one sentence.",
          "Write a two-sentence summary of the %s LP update suitable for a placement agent.",
          "Summarize the quarter of %s in plain language.",
          "Summarize the movement in net asset value and distributions this quarter at %s.",
          "Summarize the portfolio notes and the capital position of %s in two sentences.",
          "Give a brief summary of the position of %s for a monitoring file.",
          "Summarize what changed at %s this quarter and why it matters.",
          "Draft a one-sentence summary of the liquidity position of %s.",
          "Summarize the quarterly update of %s without adding any figure that is not stated.",
          "Summarize the progress of %s for a prospective LP in two sentences."]
    for i in range(10):
        f, cf = FUNDS[i], CF[i]
        txt = ("Net asset value was %s against %s at the prior quarter end; cumulative distributions of %s compare with paid-in capital of %s, and the fund called %s while distributing %s. Bramblewood Foods grew EBITDA 6 percent and Draycott Industrial Coatings was marked down 4 percent."
               % (num(cf["nav"]), num(cf["nav"] * 0.96), num(cf["dist"]), num(cf["paid"]), num(cf["paid"] * 0.035), num(cf["dist"] * 0.02)))
        A("summarization", "upd:" + f["name"], ctx_update(f, cf, "30 June %d" % (2025 - (i % 2))), qs[i] % f["name"], txt, "text", "normalized")
    for i in range(10, 20):
        f, cf = FUNDS[i], CF[i]
        txt = ("%s has called %s of its %s commitment and returned %s, leaving %s of net asset value still unrealised and %s of management fees charged to date."
               % (f["name"], num(cf["paid"]), num(f["commit"]), num(cf["dist"]), num(cf["nav"]), num(cf["fees"])))
        A("summarization", "sum:" + f["name"], ctx_sum(f, cf), "Summarize the realised and unrealised position of %s in one sentence for a fund monitor." % f["name"], txt, "text", "normalized")
    for i in range(10):
        f, wf = FUNDS[i], WF[i]
        txt = ("The fund invested %s and exited at total proceeds of %s; after the %d percent compounded preferred return and the 100 percent catch-up, carried interest is %d percent of profit and LPs receive the balance."
               % (num(wf["inv"]), num(wf["proceeds"]), f["hurdle"], f["carry"]))
        A("summarization", "wf:" + f["name"], ctx_terms(f, wf), "Summarize the waterfall outcome for LPs of %s in one sentence." % f["name"], txt, "text", "normalized")
    for i in range(10):
        co, l = COMPANIES[i], LBO[i]
        txt = ("The deal is entered at an enterprise value of %s on %s of EBITDA, funded with %s of senior debt, %s of unitranche and %s of mezzanine alongside %s of sponsor equity; the exit multiple of %s turns is applied to %s of exit EBITDA after %s of debt paydown."
               % (num(l["ev"]), num(l["eb"]), num(l["senior"]), num(l["uni"]), num(l["mezz"]), num(l["eq"]), num(l["xmult"]), num(l["xeb"]), num(l["paydown"])))
        A("summarization", "lbo:" + co["name"], ctx_lbo(co, l), "Summarize the entry and exit economics of the %s buyout in one sentence." % co["name"], txt, "text", "normalized")
    for i in range(10):
        f, j = FUNDS[i], JC[i]
        txt = ("By year four the fund had called %s and distributed %s; by year eight it had called %s, distributed %s and held %s of net asset value, with a management fee of %s in the final year."
               % (num(j["contrib"][3]), num(j["dist"][3]), num(j["contrib"][7]), num(j["dist"][7]), num(j["nav"][7]), num(j["fee"][7])))
        A("summarization", "jc:" + f["name"], ctx_j(f, j), "Summarize the J-curve history of %s in one sentence." % f["name"], txt, "text", "normalized")
    for i in range(10):
        f, wf = FUNDS[i], WF[i]
        txt = ("The fund charges %s percent during the investment period and %s percent thereafter, takes %d percent carry over a %d percent compounded preferred return, and offsets transaction and monitoring fees against the management fee."
               % (num(f["fee"], 2), num(f["fee"] - 0.5, 2), f["carry"], f["hurdle"]))
        A("summarization", "trm:" + f["name"], ctx_terms(f, wf), "Summarize the economics of the %s term sheet in one sentence." % f["name"], txt, "text", "normalized")
    for i in range(10):
        f, s = FUNDS[i], SL[i]
        txt = ("The facility is %s with %s drawn for %d days at %s percent, carrying a commitment fee of %s percent on the undrawn balance against a management fee of %s before the offset."
               % (num(s["limit"]), num(s["drawn"]), s["days"], num(s["rate"], 2), num(s["cfee"], 2), num(s["base"])))
        A("summarization", "sl:" + f["name"], ctx_sl(f, s), "Summarize the subscription line usage and cost for %s in one sentence." % f["name"], txt, "text", "normalized")
    for i in range(10):
        co, l = COMPANIES[i + 10], LBO[i + 10]
        txt = ("Net debt of %s on EBITDA of %s leaves headroom of %s turns against the 5.0 turn threshold, so the facility is %s under the credit agreement test."
               % (num(l["eb"] * l["lev"]), num(l["eb"]), num(5.0 - l["lev"], 2), "comfortable" if 5.0 - l["lev"] >= 0.25 else "tight"))
        A("summarization", "cov:" + co["name"], ctx_cov(co, l["eb"], l["lev"]), "Summarize the covenant position of %s for the deal file." % co["name"], txt, "text", "normalized")
    for w in range(10):
        funds = [FUNDS[(2 * w + k) % 20] for k in range(3)]
        paid = [CF[FIDX[f["name"]]]["paid"] for f in funds]
        dist = [CF[FIDX[f["name"]]]["dist"] for f in funds]
        nav = [CF[FIDX[f["name"]]]["nav"] for f in funds]
        pc = [f["commit"] for f in funds]
        txt = ("The three vehicles range from %s to %s in commitments, %s to %s in paid-in capital and %s to %s in distributions, with net asset value of %s to %s."
               % (num(min(pc)), num(max(pc)), num(min(paid)), num(max(paid)), num(min(dist)), num(max(dist)), num(min(nav)), num(max(nav))))
        A("summarization", "cmp:" + funds[0]["name"], ctx_cmp(funds), "Summarize the combined position of %s, %s and %s in one sentence." % (funds[0]["name"], funds[1]["name"], funds[2]["name"]), txt, "text", "normalized")
    for i in range(10):
        f = FUNDS[10 + i]
        ctx = ctx_reg(f, [CLAUSES[c][(i + 3) % 10] for c in ["governance", "economics", "exit", "information"]])
        txt = "The register sets out four LP rights: a governance right, an economics right, an exit right and an information right, each tied to a specific provision in the partnership agreement."
        A("summarization", "reg:" + f["name"], ctx, "Summarize the four LP rights recorded in the register of %s." % f["name"], txt, "text", "normalized")
def T(name, desc, props, req=None):
    return {"name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": req if req is not None else list(props)}}
def M(role, content):
    return {"role": role, "content": content}
def tool_row(key, msgs, tools, gt, at="number", tol="abs:0.01"):
    CASES.append(dict(task="tool_use", key=key, msgs=msgs, tools=tools, gt=gt, at=at, tol=tol, ctx="", q=""))
def TROW(key, tools, payload, u1, a1, u2, gt, at="number", tol="abs:0.01"):
    msgs = [M("user", u1)] + ([M("assistant", a1)] if a1 else []) + [M("tool", payload), M("user", u2)]
    tool_row(key, msgs, tools, gt, at, tol)
def J(o):
    return json.dumps(o, separators=(",", ":"))
def tool_cases():
    ft = T("get_fund_cashflows", "Return the dated LP cash flow schedule for a fund.",
           {"fund": {"type": "string", "description": "Exact legal fund name"},
            "since": {"type": "string", "description": "ISO-8601 start date, omit for inception"}}, ["fund"])
    for i in range(10):
        f, cf = FUNDS[i], CF[i]
        TROW("tcf:" + f["name"], [ft], J({"fund": f["name"], "unit": "USD millions",
                                          "flows": [{"date": d.isoformat(), "flow": lab, "amount": round(a, 1)} for d, lab, a in cf["rows"]]}),
             "Pull the LP cash flows for %s and work out the net IRR." % f["name"],
             "I will call get_fund_cashflows for %s, then solve for the rate that sets the present value of the dated flows to zero." % f["name"],
             "What is the net IRR in percent, to two decimals?", round(cf["irr"], 2), "number", "rel:0.01")
    st = T("get_fund_summary", "Return paid-in capital, cumulative distributions, net asset value and fees for a fund.",
           {"fund": {"type": "string", "description": "Exact legal fund name"}}, ["fund"])
    for i in range(8):
        f, cf = FUNDS[i], CF[i]
        TROW("tsm:" + f["name"], [st], J({"fund": f["name"], "paid_in": cf["paid"], "distributions": cf["dist"], "nav": cf["nav"], "management_fees": cf["fees"]}),
             "Get the performance summary for %s." % f["name"], None,
             "What is the DPI in turns, to three decimals?", round(cf["dist"] / cf["paid"], 3), "number", "abs:0.01")
    wt = T("get_waterfall_terms", "Return the distribution waterfall terms in a fund's limited partnership agreement.",
           {"fund": {"type": "string", "description": "Exact legal fund name"},
            "section": {"type": "string", "description": "Clause reference, optional"}}, ["fund"])
    for i in range(10):
        f, wf = FUNDS[i], WF[i]
        TROW("twf:" + f["name"], [wt], J({"fund": f["name"], "invested_capital": wf["inv"], "total_proceeds": wf["proceeds"],
                                          "hurdle_percent": f["hurdle"], "hurdle_basis": "compounded annually", "holding_years": wf["years"],
                                          "catch_up_percent": 100, "carry_percent": f["carry"]}),
             "Look up the waterfall terms for %s." % f["name"], None,
             "How much carried interest does the GP receive on this gain, in millions?", round(wf["gp"], 1), "number", "abs:0.2")
    lt = T("get_lbo_model", "Return the sources and uses and exit assumptions for a buyout model.",
           {"company": {"type": "string", "description": "Portfolio company name"}}, ["company"])
    for i in range(10):
        co, l = COMPANIES[i], LBO[i]
        TROW("tlbo:" + co["name"], [lt], J({"company": co["name"], "entry_ebitda": l["eb"], "entry_multiple": l["mult"],
                                            "debt": {"senior": l["senior"], "unitranche": l["uni"], "mezzanine": l["mezz"]},
                                            "sponsor_equity": l["eq"], "exit_ebitda": l["xeb"], "exit_multiple": l["xmult"],
                                            "debt_paydown": l["paydown"]}),
             "Open the buyout model for %s and check the exit equity value." % co["name"],
             "I will call get_lbo_model for %s and then apply the exit multiple to exit EBITDA before deducting net debt." % co["name"],
             "What is the sponsor exit equity value in millions?", round(l["xeq"], 1), "number", "abs:0.2")
    jt = T("get_jcurve", "Return annual contributions, distributions, net asset value and fees for a fund.",
           {"fund": {"type": "string", "description": "Exact legal fund name"}}, ["fund"])
    for i in range(8):
        f, j = FUNDS[i], JC[i]
        TROW("tjc:" + f["name"], [jt], J({"fund": f["name"], "unit": "USD millions",
                                          "years": [{"year": y + 1, "contributions": j["contrib"][y], "distributions": j["dist"][y],
                                                     "nav": j["nav"][y], "management_fee": j["fee"][y]} for y in range(8)]}),
             "Get the annual history for %s." % f["name"], None,
             "What is the cumulative management fee drag over the eight years, in percent of committed capital?", round(j["drag"], 2), "number", "abs:0.1")
    rt = T("list_lp_rights", "List the LP rights recorded in a fund's rights register.",
           {"fund": {"type": "string", "description": "Exact legal fund name"}}, ["fund"])
    cats = ["governance", "economics", "exit", "information"]
    for i in range(8):
        f = FUNDS[i]
        picks = [CLAUSES[c][i] for c in cats]
        TROW("trl:" + f["name"], [rt], J({"fund": f["name"], "rights": [{"ref": "R%d" % (k + 1), "provision": picks[k]} for k in range(4)]}),
             "List the LP rights on file for %s." % f["name"],
             "I will call list_lp_rights and then classify each provision against the standard categories.",
             "Which category does R%d fall into? Use one of {governance, economics, exit, information}." % (i % 4 + 1),
             cats[i % 4], "label", "exact")
    slt = T("get_subscription_line", "Return the subscription line facility terms and usage for a fund.",
            {"fund": {"type": "string", "description": "Exact legal fund name"}}, ["fund"])
    for i in range(8):
        f, s = FUNDS[i], SL[i]
        TROW("tsl:" + f["name"], [slt], J({"fund": f["name"], "limit": s["limit"], "drawn": s["drawn"], "days": s["days"],
                                          "rate_percent": s["rate"], "commitment_fee_percent": s["cfee"]}),
             "Get the subscription line details for %s." % f["name"], None,
             "What is the total interest and commitment fee cost in millions, to three decimals?", round(s["cost"], 3), "number", "abs:0.01")
    tt = T("get_fund_terms", "Return the main economic and duration terms from a fund's term sheet.",
           {"fund": {"type": "string", "description": "Exact legal fund name"},
            "field": {"type": "string", "description": "One of term, hurdle, carry, fee"}}, ["fund"])
    for i in range(8):
        f = FUNDS[i]
        TROW("ttm:" + f["name"], [tt], J({"fund": f["name"], "term_years": f["term"], "extension": "two one-year extensions with LPAC consent",
                                          "hurdle_percent": f["hurdle"], "carry_percent": f["carry"], "management_fee_percent": f["fee"]}),
             "Check the term sheet facts for %s." % f["name"],
             "I will call get_fund_terms and read the duration and economics fields.",
             "How many years is the stated fund term?", f["term"], "number", "abs:0.01")
    srch = T("search_funds", "Search the sponsor's fund list by strategy or vintage.",
             {"strategy": {"type": "string", "description": "Strategy filter"},
              "vintage_from": {"type": "integer", "description": "Earliest vintage year"}}, ["strategy"])
    for i in range(8):
        a, b = FUNDS[i], FUNDS[(i + 5) % 20]
        ca, cb = CF[i], CF[(i + 5) % 20]
        win = a["name"] if ca["dist"] / ca["paid"] > cb["dist"] / cb["paid"] else b["name"]
        TROW("tsr:%d" % i, [srch], J({"results": [
            {"fund": a["name"], "paid_in": ca["paid"], "distributions": ca["dist"], "nav": ca["nav"]},
            {"fund": b["name"], "paid_in": cb["paid"], "distributions": cb["dist"], "nav": cb["nav"]}]}),
            "Search the fund list for mid-market buyout vehicles and compare %s with %s." % (a["name"], b["name"]),
            "I will call search_funds with the strategy filter and then compare the distribution ratios.",
            "Of those two, which has the higher DPI?", win, "text", "normalized")
    for i in range(8):
        f, cf = FUNDS[i], CF[i]
        err = J({"error": "unknown fund", "requested": f["name"] + " Offshore", "known": [f["name"]]})
        ok = J({"fund": f["name"], "paid_in": cf["paid"], "distributions": cf["dist"], "nav": cf["nav"]})
        msgs = [M("user", "What is the DPI of %s?" % f["name"]),
                M("assistant", "I will call get_fund_summary for %s." % (f["name"] + " Offshore")), M("tool", err),
                M("assistant", "The tool rejected that name. Retrying with the exact legal name %s." % f["name"]), M("tool", ok),
                M("user", "Thanks. What is the DPI in turns, to three decimals?")]
        tool_row("twr:" + f["name"], msgs, [st], round(cf["dist"] / cf["paid"], 3), "number", "abs:0.01")
    for i in range(8):
        f, cf = FUNDS[i], CF[i]
        part = J({"fund": f["name"], "paid_in": cf["paid"], "distributions": cf["dist"], "nav": None,
                  "note": "net asset value not yet marked for the current quarter"})
        msgs = [M("user", "What is the RVPI of %s?" % f["name"]),
                M("assistant", "I will call get_fund_summary for the valuation data."), M("tool", part),
                M("assistant", "The response has no net asset value, so RVPI cannot be computed. I can give you DPI from paid-in capital and distributions instead."),
                M("user", "Fine, give me the DPI in turns, to three decimals.")]
        tool_row("tin:" + f["name"], msgs, [st], round(cf["dist"] / cf["paid"], 3), "number", "abs:0.01")
    fet = T("get_fee_schedule", "Return the management fee, transaction fees and offset ratio for a fund.",
            {"fund": {"type": "string", "description": "Exact legal fund name"}}, ["fund"])
    for i in range(6):
        f, s = FUNDS[i], SL[i]
        txn = round(s["base"] * 0.22, 2)
        TROW("tfe:" + f["name"], [fet], J({"fund": f["name"], "management_fee": s["base"], "transaction_fees": txn, "offset_ratio_percent": 100}),
             "Check the fee schedule for %s." % f["name"],
             "I will call get_fee_schedule and net the offset against the management fee.",
             "What is the management fee after the fee offset, in millions?", round(s["base"] - txn, 2), "number", "abs:0.02")
def assign_splits():
    groups = {}
    for c in CASES:
        groups.setdefault(c["task"], {}).setdefault(c["key"], []).append(c)
    for task, g in groups.items():
        keys = sorted(g, key=lambda k: hashlib.sha256(k.encode("utf-8")).hexdigest())
        prefix = [0]
        for k in keys:
            prefix.append(prefix[-1] + len(g[k]))
        total = prefix[-1]
        t0, t1, t2 = 0.8 * total, 0.1 * total, 0.1 * total
        best = min(((abs(prefix[i] - t0) + abs(prefix[j] - prefix[i] - t1) + abs(total - prefix[j] - t2), i, j)
                    for i in range(1, len(keys) - 1) for j in range(i + 1, len(keys))))
        for idx, k in enumerate(keys):
            sp = "train" if idx < best[1] else ("val" if idx < best[2] else "test")
            for c in g[k]:
                c["split"] = sp
        cnt = Counter(c["split"] for c in CASES if c["task"] == task)
        for sp in ("train", "val", "test"):
            while cnt[sp] < 3:
                donor = max(("train", "val", "test"), key=lambda s: cnt[s])
                kk = min([k for k in g if g[k][0]["split"] == donor], key=lambda k: (len(g[k]), k))
                for c in g[kk]:
                    c["split"] = sp
                cnt[donor] -= len(g[kk])
                cnt[sp] += len(g[kk])
def nudge_splits():
    idx = {}
    for c in CASES:
        idx.setdefault((c["task"], c["key"]), []).append(c)
    for _ in range(12):
        d = Counter(c["split"] for c in CASES)
        if d["test"] - d["val"] <= 3:
            break
        moved = False
        for k in sorted([k for k, v in idx.items() if v[0]["split"] == "test"], key=lambda k: (len(idx[k]), k)):
            left = sum(1 for c in CASES if c["task"] == k[0] and c["split"] == "test") - len(idx[k])
            if left < 3 or abs(d["val"] + len(idx[k]) - 100) >= abs(d["val"] - 100):
                continue
            for c in idx[k]:
                c["split"] = "val"
            moved = True
            break
        if not moved:
            break
def build_rows():
    assign_splits(); nudge_splits()
    rows, seq = [], {}
    for c in CASES:
        t = c["task"]
        seq[t] = seq.get(t, 0) + 1
        row = {"id": "fin_%s_%s_%06d" % (AREA, ABBR[t], seq[t]), "task": t,
               "source": "knowledge:finance_general" if (t != "tool_use" and c["ctx"] == "") else "synthetic:" + AREA}
        if t == "tool_use":
            row["messages"], row["tools"] = c["msgs"], c["tools"]
        else:
            row["context"], row["question"] = c["ctx"], c["q"]
        row.update({"ground_truth": c["gt"], "answer_type": c["at"], "tolerance": c["tol"],
                    "split": c["split"], "thinking": "on" if t in ("calc", "qa", "tool_use") else "off"})
        rows.append(row)
    return rows
def mask(s):
    return re.sub(r"\d+(?:[.,]\d+)*", "#", " ".join(str(s).split()).lower())
def main():
    for fn in (calc_cases, extraction_cases, qa_cases, classification_cases, summ_cases, tool_cases):
        fn()
    rows = build_rows()
    order = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
    rows.sort(key=lambda r: order.index(r["task"]))
    with open(os.path.join(HERE, "prompts.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    fam = Counter(mask(r.get("question") or next((m["content"] for m in r["messages"] if m["role"] == "user"), ""))[:160] for r in rows)
    print("rows %d  families %d  top %d" % (len(rows), len(fam), max(fam.values())))
if __name__ == "__main__": main()
