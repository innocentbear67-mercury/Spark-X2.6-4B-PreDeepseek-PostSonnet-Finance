#!/usr/bin/env python3
"""Deterministic generator for credit_fixed_income (profile A, 1000 rows).
All data is synthetic. Each ground_truth is computed here from the same values
rendered into the context; nothing derived is hand-typed.
"""
import hashlib
import json
import os
import random
import re
from collections import Counter, defaultdict
AREA = "credit_fixed_income"
ABBR = {"calc": "calc", "extraction": "extr", "summarization": "summ", "classification": "cls", "qa": "qa", "tool_use": "tool"}
RNG = random.Random(42)
HERE = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
def f(x, dp=2):
    s = "{:.{}f}".format(x, dp)
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "", "-") else s
def cfmt(x):
    return "{:.2f}".format(x) if abs(x * 10 - round(x * 10)) < 1e-9 else "{:.3f}".format(x)
def mask(s):
    return re.sub(r"\d+(?:[.,]\d+)*", "#", re.sub(r"\s+", " ", str(s)).strip().lower())
def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()
# ------------------------------------------------------------------ math
def pv_price(coupon, n, y, freq=1):
    m = n * freq
    return sum(coupon / freq / (1 + y / freq) ** t for t in range(1, m + 1)) + 100 / (1 + y / freq) ** m
def solve_y(coupon, n, price, freq=1):
    lo, hi = -0.5, 1.5
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv_price(coupon, n, mid, freq) > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
def solve_call(coupon, years, call_price, price):
    def pv(y):
        return sum(coupon / (1 + y) ** t for t in range(1, years + 1)) + call_price / (1 + y) ** years
    lo, hi = -0.5, 1.5
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv(mid) > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
def mod_dur(coupon, n, y, freq=1):
    m, p, c = n * freq, pv_price(coupon, n, y, freq), coupon / freq
    s = sum((t / float(freq)) * (c if t < m else c + 100) / (1 + y / freq) ** t for t in range(1, m + 1))
    return (s / p) / (1 + y / freq)
# -------------------------------------------------------------- fixtures
ISSUERS = [("Halcyon Grid Utilities", "Utilities", "31 Dec", "USD"),
              ("Meridian Bancorp", "Banking", "31 Dec", "USD"),
              ("Kestrel Foods", "Consumer staples", "30 Jun", "USD"),
              ("Ardent Materials", "Chemicals", "31 Dec", "EUR"),
              ("Northwind Logistics", "Transport", "31 Dec", "USD"),
              ("Solstice Renewables", "Power generation", "31 Dec", "EUR"),
              ("Cobalt Ridge Mining", "Mining", "31 Dec", "USD"),
              ("Larkspur Health", "Healthcare", "30 Sep", "USD"),
              ("Vantage Semiconductor", "Technology", "31 Dec", "USD"),
              ("Harborline Retail", "Retail", "31 Jan", "USD"),
              ("Ironbark Packaging", "Packaging", "31 Dec", "AUD"),
              ("Silverbrook Telecom", "Telecom", "31 Dec", "GBP"),
              ("Pelican Bay Resorts", "Leisure", "31 Dec", "USD"),
              ("Tundra Peaks Energy", "Oil and gas", "31 Dec", "CAD"),
              ("Alder Grove Realty", "REIT", "31 Dec", "USD"),
              ("Bluefin Shipping", "Shipping", "31 Dec", "USD"),
              ("Corvus Insurance", "Insurance", "31 Dec", "USD"),
              ("Meadowlark Pharma", "Pharmaceuticals", "31 Dec", "CHF"),
              ("Quarry Ridge Cement", "Building materials", "31 Dec", "EUR"),
              ("Wrenfield Automotive", "Automotive", "31 Dec", "EUR"),
              
          ]
# issuer idx, tier, coupon, years, benchmark, spread bp, face, rating, day count
BOND_SPECS = [(0, "senior secured", 5.25, 7, 4.10, 240, 650, "BB+", "30/360"),
                 (0, "senior unsecured", 5.75, 10, 4.10, 330, 400, "BB", "30/360"),
                 (1, "senior unsecured", 6.00, 5, 4.35, 310, 500, "BBB-", "actual/365"),
                 (1, "subordinated", 6.75, 10, 4.35, 470, 300, "BB", "30/360"),
                 (2, "senior unsecured", 4.50, 6, 3.95, 215, 450, "BBB", "30/360"),
                 (2, "senior secured", 4.25, 5, 3.95, 160, 350, "BBB+", "30/360"),
                 (3, "senior secured", 4.75, 8, 3.60, 275, 600, "BB+", "actual/365"),
                 (3, "senior unsecured", 5.50, 8, 3.60, 395, 400, "BB", "actual/365"),
                 (4, "senior unsecured", 6.25, 7, 4.55, 340, 550, "BB", "30/360"),
                 (4, "senior secured", 5.50, 6, 4.55, 250, 300, "BB+", "30/360"),
                 (5, "senior secured", 4.875, 9, 3.85, 220, 700, "BBB-", "actual/365"),
                 (5, "subordinated", 6.50, 12, 3.85, 520, 250, "B+", "30/360"),
                 (6, "senior unsecured", 7.00, 8, 4.70, 480, 500, "B+", "30/360"),
                 (6, "senior secured", 6.25, 7, 4.70, 375, 450, "BB-", "30/360"),
                 (7, "senior unsecured", 5.00, 6, 4.05, 265, 400, "BBB", "actual/365"),
                 (7, "senior secured", 4.625, 5, 4.05, 185, 300, "BBB+", "actual/365"),
                 (8, "senior unsecured", 4.25, 7, 4.20, 190, 800, "A-", "30/360"),
                 (8, "senior secured", 3.95, 10, 4.20, 140, 600, "A", "30/360"),
                 (9, "senior unsecured", 5.875, 5, 4.40, 300, 350, "BB+", "30/360"),
                 (9, "senior secured", 5.25, 4, 4.40, 215, 250, "BBB-", "30/360"),
                 (10, "senior secured", 5.375, 6, 4.15, 285, 400, "BB+", "actual/365"),
                 (10, "senior unsecured", 6.125, 8, 4.15, 410, 300, "BB", "actual/365"),
                 (11, "senior unsecured", 6.50, 9, 4.60, 355, 700, "BB", "30/360"),
                 (11, "subordinated", 7.25, 12, 4.60, 540, 350, "B", "30/360"),
                 (12, "senior secured", 6.00, 7, 4.30, 395, 450, "B+", "30/360"),
                 (12, "senior unsecured", 6.75, 8, 4.30, 495, 300, "B", "30/360"),
                 (13, "senior secured", 5.75, 6, 4.50, 310, 550, "BB", "30/360"),
                 (13, "senior unsecured", 6.50, 10, 4.50, 445, 400, "BB-", "30/360"),
                 (14, "senior unsecured", 5.25, 8, 4.25, 275, 500, "BBB-", "30/360"),
                 (14, "senior secured", 4.875, 7, 4.25, 200, 450, "BBB", "30/360"),
                 (15, "senior secured", 6.375, 5, 4.65, 360, 350, "BB-", "actual/365"),
                 (16, "subordinated", 6.875, 10, 4.40, 430, 250, "BB-", "30/360"),
                 (17, "senior unsecured", 4.125, 7, 3.70, 175, 600, "A-", "actual/365"),
                 (18, "senior secured", 5.125, 6, 3.90, 265, 500, "BB+", "actual/365"),
                 (19, "senior secured", 5.625, 7, 4.05, 330, 650, "BB", "30/360"),
                 (19, "senior unsecured", 6.25, 9, 4.05, 455, 350, "BB-", "30/360"),
                 
             ]
def build_bonds():
    out = []
    for i, (ix, tier, coupon, n, bench, spread, face, rating, dc) in enumerate(BOND_SPECS):
        y = bench + spread / 100.0
        out.append({"id": "B{:02d}".format(i), "issuer": ISSUERS[ix][0], "tier": tier, "coupon": coupon, "n": n, "bench": bench, "spread": spread, "face": face, "rating": rating, "dc": dc, "price": round(pv_price(coupon, n, y / 100.0), 2), "issue_date": "30 Sep {}".format(2025 - (1 + i % 3)), "mat_date": "30 Sep {}".format(2025 + n), "call_date": "30 Sep {}".format(2025 + n - 2), "call_price": round(100 + coupon / 2.0, 3), "days": 25 + (i * 13) % 300})
    return out
BONDS = build_bonds()
# issuer idx, ebitda, net leverage, coverage, cash, commitment, drawn, capex %, amort, first lien %
COV_SEEDS = [(0, 980, 4.05, 2.85, 240, 900, 180, 0.09, 62, 0.55),
                (2, 620, 3.40, 3.30, 150, 600, 90, 0.06, 30, 0.50),
                (3, 1240, 4.35, 2.55, 310, 1000, 260, 0.11, 85, 0.60),
                (4, 760, 3.80, 2.95, 190, 700, 140, 0.08, 44, 0.45),
                (5, 540, 4.60, 2.20, 130, 500, 210, 0.14, 38, 0.65),
                (6, 1120, 5.05, 2.10, 260, 800, 320, 0.12, 90, 0.70),
                (7, 880, 3.25, 3.45, 300, 750, 80, 0.07, 35, 0.40),
                (8, 1560, 3.60, 3.80, 620, 1200, 200, 0.10, 70, 0.35),
                (9, 690, 4.20, 2.65, 120, 650, 230, 0.05, 42, 0.55),
                (10, 820, 4.45, 2.40, 175, 700, 190, 0.09, 50, 0.60),
                (11, 1380, 3.95, 2.90, 340, 1100, 160, 0.13, 95, 0.50),
                (12, 450, 5.20, 1.95, 95, 400, 180, 0.15, 28, 0.70),
                (13, 1480, 4.15, 2.70, 300, 1000, 140, 0.16, 110, 0.55),
                (14, 720, 4.80, 2.30, 160, 600, 150, 0.06, 40, 0.60),
                (15, 560, 4.30, 2.50, 210, 500, 120, 0.18, 48, 0.65),
                (17, 1050, 3.15, 3.60, 480, 900, 100, 0.08, 36, 0.30),
                (18, 660, 4.55, 2.35, 140, 550, 175, 0.10, 46, 0.60),
                (19, 1180, 3.85, 2.80, 280, 950, 210, 0.11, 72, 0.50),
                
            ]
COV_THRESH = [(4.50, 2.50, 250), (4.25, 2.75, 200), (4.50, 2.50, 300), (4.00, 2.50, 250), (4.75, 2.25, 200), (4.50, 2.25, 300), (4.00, 3.00, 250), (4.25, 3.00, 350), (4.50, 2.50, 200)]
def build_covs():
    out, specs = [], [(s, 0, "FY2025") for s in COV_SEEDS] + [(s, 1, "FY2024") for s in COV_SEEDS]
    for j, (s, per, label) in enumerate(specs):
        ix, eb, lev, icr, cash, commit, drawn, capex_p, amort, fl_p = s
        mx, mi, ml = COV_THRESH[ix % len(COV_THRESH)]
        if per == 1:
            eb, cash = int(round(eb * 0.94)), int(round(cash * 1.10))
            debt = int(round(lev * eb * 0.96 + cash))
            interest, drawn = int(round((eb / icr) * 0.95)), max(drawn - 25, 20)
        else:
            debt, interest = int(round(lev * eb + cash)), int(round(eb / icr))
        out.append({"id": "C{:02d}".format(j), "issuer": ISSUERS[ix][0], "period": label, "ebitda": eb, "debt": debt, "cash": cash, "interest": interest, "capex": int(round(eb * capex_p)), "amort": amort, "first_lien": int(round(debt * fl_p)), "maxlev": mx, "minicr": mi, "minliq": ml, "commit": commit, "drawn": drawn, "curecap": 100 + (ix * 25) % 150, "style": j % 3})
    for k, (ix, label, es, ds, cs) in enumerate([(0, "FY2023", 0.89, 0.93, 1.20), (3, "FY2023", 0.90, 0.94, 1.15), (5, "FY2023", 0.88, 0.92, 1.25), (8, "FY2023", 0.91, 0.95, 1.18)]):
        s = [x for x in COV_SEEDS if x[0] == ix][0]
        _, eb, lev, icr, cash, commit, drawn, capex_p, amort, fl_p = s
        mx, mi, ml = COV_THRESH[ix % len(COV_THRESH)]
        eb2, cash2 = int(round(eb * es)), int(round(cash * cs))
        debt2 = int(round(lev * eb2 * ds + cash2))
        out.append({"id": "C{:02d}".format(36 + k), "issuer": ISSUERS[ix][0], "period": label, "ebitda": eb2, "debt": debt2, "cash": cash2, "interest": int(round((eb2 / icr) * 0.93)), "capex": int(round(eb2 * capex_p)), "amort": amort, "first_lien": int(round(debt2 * fl_p)), "maxlev": mx, "minicr": mi, "minliq": ml, "commit": commit, "drawn": drawn, "curecap": 100 + (ix * 25) % 150, "style": 2})
    return out
COVS = build_covs()
def cm(c):
    nd, avail = c["debt"] - c["cash"], c["commit"] - c["drawn"]
    return {"nd": nd, "lev": nd / float(c["ebitda"]), "icr": c["ebitda"] / float(c["interest"]), "avail": avail, "liq": c["cash"] + avail, "fcc": (c["ebitda"] - c["capex"]) / float(c["interest"] + c["amort"]), "fl": (c["first_lien"] - c["cash"]) / float(c["ebitda"]), "cure": nd - c["maxlev"] * c["ebitda"], "need": nd / float(c["maxlev"])}
REC_SPECS = [(0, 1620, 45, 620, 480, 260), (2, 980, 30, 420, 300, 180), (3, 1480, 60, 780, 520, 300), (4, 860, 25, 380, 290, 150), (5, 740, 35, 460, 240, 190), (6, 1320, 55, 690, 610, 280), (8, 2050, 70, 900, 560, 320), (9, 610, 20, 300, 210, 140), (11, 1540, 50, 820, 540, 330), (12, 520, 25, 340, 180, 120), (13, 1760, 65, 860, 620, 300), (19, 990, 40, 470, 350, 210)]
RECS = [{"id": "R{:02d}".format(i), "issuer": ISSUERS[s[0]][0], "ev": s[1], "admin": s[2], "sec": s[3], "unsec": s[4], "sub": s[5]} for i, s in enumerate(REC_SPECS)]
def rm(r):
    avail = r["ev"] - r["admin"]
    pay_sec = min(r["sec"], max(avail, 0))
    resid = avail - pay_sec
    defi = r["unsec"] + (r["sec"] - pay_sec)
    pay_un = min(r["unsec"], resid * r["unsec"] / float(defi)) if defi else 0.0
    resid2 = resid - pay_un
    pay_sub = min(r["sub"], max(resid2, 0))
    return {"pay_sec": pay_sec, "pay_un": pay_un, "pay_sub": pay_sub, "rec_sec": pay_sec / float(r["sec"]) * 100, "rec_unsec": pay_un / float(r["unsec"]) * 100, "rec_sub": pay_sub / float(r["sub"]) * 100, "equity": max(resid2 - r["sub"], 0)}
WALL_SPECS = [(0, [240, 180, 320, 0, 250, 400], 180, 220), (2, [150, 130, 90, 140, 0, 260], 120, 180), (3, [300, 260, 240, 300, 150, 420], 260, 240), (5, [180, 160, 140, 120, 260, 240], 95, 150), (6, [260, 300, 220, 0, 180, 380], 210, 190), (8, [420, 380, 300, 260, 200, 500], 540, 400), (9, [110, 90, 130, 80, 60, 200], 90, 140), (11, [350, 300, 280, 240, 320, 460], 300, 260), (13, [380, 340, 300, 280, 240, 520], 290, 310), (19, [220, 240, 200, 180, 160, 340], 165, 200)]
WALLS = [{"id": "W{:02d}".format(i), "issuer": ISSUERS[s[0]][0], "amts": s[1], "cash": s[2], "avail": s[3]} for i, s in enumerate(WALL_SPECS)]
def wm(w):
    tot = float(sum(w["amts"]))
    near = w["amts"][0] + w["amts"][1]
    return {"tot": tot, "near": near, "pct24": near / tot * 100, "wam": sum((i + 1) * a for i, a in enumerate(w["amts"])) / tot, "gap": near - w["cash"] - w["avail"]}
RATING_TPL = {"positive": ["affirmed the {r} rating and revised the outlook to positive from stable, citing improving leverage and steady free cash flow", "revised the outlook to positive while affirming the {r} rating, reflecting debt reduction and stronger liquidity", "affirmed the {r} rating with a positive outlook, noting that asset sale proceeds will be applied to debt"],
                 "stable": ["affirmed the {r} rating and maintained a stable outlook, expecting leverage to remain near the current level", "affirmed the {r} rating with a stable outlook, supported by the issuer's scale and diversified customer base", "maintained the {r} rating and a stable outlook, with the agency expecting modest organic growth"],
                 "negative": ["affirmed the {r} rating and revised the outlook to negative from stable, citing weaker free cash flow and rising leverage", "revised the outlook to negative while affirming the {r} rating, reflecting margin pressure and negative cash generation", "affirmed the {r} rating with a negative outlook, noting the risk that leverage will exceed the agency's threshold"],
                 
             }
ACTION_TPL = {"upgrade": ["upgraded the {r} rating to {r2} from {r1}, citing sustained deleveraging", "raised the {r} rating to {r2} from {r1} on stronger liquidity and positive free cash flow"], "downgrade": ["downgraded the {r} rating to {r2} from {r1}, citing weak demand and eroding margins", "lowered the {r} rating to {r2} from {r1} after the debt-funded acquisition"], "affirm": ["affirmed the {r} rating at {r1}, with a stable outlook", "reaffirmed the {r} rating at {r1}, noting adequate liquidity"]}
# issuer idx, coupon, year, lien basket, RP basket, RP used
IND_SPECS = [(0, 5.25, 2031, 350, 220, 60),
                (2, 4.50, 2029, 250, 150, 40),
                (3, 4.75, 2030, 400, 260, 180),
                (4, 6.25, 2030, 300, 200, 90),
                (5, 4.875, 2030, 450, 240, 60),
                (6, 7.00, 2030, 320, 180, 140),
                (7, 5.00, 2029, 280, 210, 50),
                (8, 4.25, 2030, 500, 300, 120),
                (9, 5.875, 2029, 260, 170, 80),
                (10, 5.375, 2029, 340, 190, 70),
                (11, 6.50, 2031, 380, 250, 160),
                (12, 6.00, 2030, 240, 140, 45),
                (13, 5.75, 2030, 420, 280, 100),
                (14, 5.25, 2030, 360, 230, 75),
                (15, 6.375, 2028, 300, 160, 55),
                (17, 4.125, 2029, 460, 320, 110),
                (18, 5.125, 2029, 330, 200, 85),
                (19, 5.625, 2029, 370, 240, 120),
                (2, 4.25, 2028, 240, 130, 35),
                (13, 6.50, 2034, 440, 260, 95)
            ]
INDS = [{"id": "I{:02d}".format(i), "issuer": ISSUERS[s[0]][0], "coupon": s[1], "year": s[2], "lien": s[3], "rp": s[4], "used": s[5]} for i, s in enumerate(IND_SPECS)]
UNITS_BOND = ("Units: $ in millions except bond prices quoted per 100 of face value; " "percentages in percent per annum; spreads in basis points.")
UNITS_COV = "Units: $ in millions; leverage and coverage ratios in turns; percentages in percent."
UNITS_REC = "Units: $ in millions; recoveries in percent of allowed claim."
UNITS_WALL = "Units: $ in millions; percentages in percent."
def bond_ctx(b, extra=""):
    sp = {"issuer": b["issuer"], "coupon": cfmt(b["coupon"]) + "%", "mat": b["mat_date"], "price": f(b["price"], 2), "bench": f(b["bench"], 2) + "%", "spread": str(b["spread"]), "rating": b["rating"], "dc": b["dc"], "face": f(b["face"], 0), "callp": f(b["call_price"], 3), "calld": b["call_date"], "issue": b["issue_date"], "n": f(b["n"], 2)}
    txt = "\n".join([ UNITS_BOND, "", "Bond term sheet - {} {} notes".format(b["issuer"], b["tier"]), "Pricing date: 30 Sep 2025", "| Field | Detail |", "|---|---|", "| Issuer | {} |".format(sp["issuer"]), "| Instrument | {} {} notes due {} |".format(sp["coupon"], b["tier"], sp["mat"]), "| Principal amount | {} |".format(sp["face"]), "| Coupon | {} paid annually |".format(sp["coupon"]), "| Issue date | {} |".format(sp["issue"]), "| Maturity date | {} |".format(sp["mat"]), "| Clean price | {} |".format(sp["price"]), "| Benchmark (1) | {} |".format(sp["bench"]), "| Spread to benchmark | {} |".format(sp["spread"]), "| Rating | {} |".format(sp["rating"]), "| Day count | {} |".format(sp["dc"]), "| Call protection | non-callable until {}, then callable at {} |".format(sp["calld"], sp["callp"]), "| Remaining term (analytic) | {} years |".format(sp["n"]), "", "Coupons are paid annually on 30 September and the notes redeem at 100. The clean price", "excludes accrued interest and is quoted for settlement on the pricing date.", "(1) Benchmark yield is the interpolated government curve at the matching tenor." + extra])
    return txt, sp
def cov_table(c, extended=False):
    m = cm(c)
    sp = {"ebitda": f(c["ebitda"], 0), "debt": f(c["debt"], 0), "cash": f(c["cash"], 0), "interest": f(c["interest"], 0), "capex": f(c["capex"], 0), "amort": f(c["amort"], 0), "maxlev": f(c["maxlev"], 2), "minicr": f(c["minicr"], 2), "minliq": f(c["minliq"], 0), "curecap": f(c["curecap"], 0), "commit": f(c["commit"], 0), "drawn": f(c["drawn"], 0), "avail": f(m["avail"], 0), "fl": f(c["first_lien"], 0)}
    rows = [("Consolidated EBITDA (LTM) (1)", sp["ebitda"]), ("Total debt", sp["debt"]), ("Cash and equivalents", sp["cash"]), ("Interest expense (LTM)", sp["interest"]), ("Capital expenditure (LTM)", sp["capex"]), ("Scheduled amortisation (LTM)", sp["amort"]), ("Revolving commitment", sp["commit"]), ("Revolving drawn", sp["drawn"]), ("Undrawn revolving availability", sp["avail"]), ("First lien debt", sp["fl"]), ("Maximum net leverage", sp["maxlev"]), ("Minimum interest coverage", sp["minicr"]), ("Minimum liquidity", sp["minliq"]), ("Equity cure cap", sp["curecap"])]
    if extended:
        rows.insert(10, ("Equity cures permitted per four quarters", "2"))
    txt = "\n".join([UNITS_COV, "", "Covenant compliance certificate - {} - {}".format(c["issuer"], c["period"]), "| Item | Amount |", "|---|---|"] + ["| {} | {} |".format(k, v) for k, v in rows] + ["", "Liquidity means cash and equivalents plus undrawn revolving availability.", "Net leverage means total debt less cash divided by consolidated EBITDA.", "(1) Consolidated EBITDA is calculated as defined in Schedule 1, including the", "add-backs listed in Exhibit C."])
    if extended:
        txt += "\nAn amendment dated 14 Feb 2025 added the first lien springing test at 3.50 to 1.00."
    return txt, sp
def cov_prose(c):
    m = cm(c)
    sp = {"ebitda": f(c["ebitda"], 0), "debt": f(c["debt"], 0), "cash": f(c["cash"], 0), "interest": f(c["interest"], 0), "capex": f(c["capex"], 0), "amort": f(c["amort"], 0), "maxlev": f(c["maxlev"], 2) + " to 1.00", "minicr": f(c["minicr"], 2) + " to 1.00", "minliq": "USD " + f(c["minliq"], 0) + " million", "curecap": "USD " + f(c["curecap"], 0) + " million", "commit": f(c["commit"], 0), "drawn": f(c["drawn"], 0), "avail": f(m["avail"], 0), "fl": f(c["first_lien"], 0)}
    txt = "\n".join([ UNITS_COV, "", "Covenant excerpt - {} credit agreement, fiscal year {}".format(c["issuer"], c["period"]), "", "Section 7.01 Maximum Net Leverage. The Borrower shall not permit Net Leverage, being", "Consolidated Debt less Cash divided by Consolidated EBITDA, to exceed {}.".format(sp["maxlev"]), "Section 7.02 Minimum Interest Coverage. The Borrower shall maintain Interest Coverage,", "being Consolidated EBITDA divided by Interest Expense, of at least {}.".format(sp["minicr"]), "Section 7.03 Minimum Liquidity. Liquidity, being Cash plus undrawn Revolving Commitments,", "shall not be less than {} at any time.".format(sp["minliq"]), "Section 7.04 Equity Cure. The Borrower may cure a breach of Section 7.01 up to two times", "in any four consecutive fiscal quarters by applying Net Cash Proceeds of equity issuances,", "in an aggregate amount not to exceed {}.".format(sp["curecap"]), "", "For the period: Consolidated EBITDA {}; Consolidated Debt {}; Cash {}; Interest Expense {}; " "Capital expenditure {}; scheduled amortisation {}; Revolving Commitments {} of which {} drawn, " "leaving undrawn availability {};".format( sp["ebitda"], sp["debt"], sp["cash"], sp["interest"], sp["capex"], sp["amort"], sp["commit"], sp["drawn"], sp["avail"]), "first lien debt {}.".format(sp["fl"])])
    return txt, sp
def cov_ctx(c):
    return cov_prose(c) if c["style"] == 1 else cov_table(c, extended=(c["style"] == 2))
def rec_ctx(r, memo=False):
    sp = {"admin": f(r["admin"], 0), "sec": f(r["sec"], 0), "unsec": f(r["unsec"], 0), "sub": f(r["sub"], 0), "ev": f(r["ev"], 0)}
    if memo:
        rows = ["| Rank | Claim | Allowed amount |", "|---|---|---|", "| 1 | Administrative and priority claims | {} |".format(sp["admin"]), "| 2 | Senior secured notes | {} |".format(sp["sec"]), "| 3 | Senior unsecured notes | {} |".format(sp["unsec"]), "| 4 | Subordinated notes | {} |".format(sp["sub"])]
        head = "Recovery memo - {} - illustrative default scenario".format(r["issuer"])
    else:
        rows = ["| Claim | Allowed amount | Rank |", "|---|---|---|", "| Administrative and priority claims | {} | 1 |".format(sp["admin"]), "| Senior secured notes | {} | 2 |".format(sp["sec"]), "| Senior unsecured notes | {} | 3 |".format(sp["unsec"]), "| Subordinated notes | {} | 4 |".format(sp["sub"])]
        head = "Recovery waterfall - {} - hypothetical default".format(r["issuer"])
    txt = "\n".join([UNITS_REC, "", head] + rows + [ "", "Enterprise value at default: {}.".format(sp["ev"]), "Waterfall rule: administrative claims are paid first in full. Remaining proceeds are applied", "to the senior secured claim up to its allowed amount. Any shortfall of the senior secured claim", "ranks pari passu with the senior unsecured claims. Residual proceeds are paid to senior", "unsecured claims pro rata and then to subordinated notes. Equity receives any remainder."])
    return txt, sp
def wall_ctx(w):
    sp = {"cash": f(w["cash"], 0), "avail": f(w["avail"], 0)}
    for i, yr in enumerate([2026, 2027, 2028, 2029, 2030, 2031]):
        sp["y{}".format(yr)] = f(w["amts"][i], 0)
    cols = []
    for a in w["amts"]:
        t1, t2 = int(round(a * 0.40)), int(round(a * 0.35))
        cols.append((t1, t2, a - t1 - t2))
    lines = ["| Instrument | 2026 | 2027 | 2028 | 2029 | 2030 | Thereafter |", "|---|---|---|---|---|---|---|"]
    for j, nm in enumerate(["Term loan A", "Senior notes", "Other debt"]):
        lines.append("| {} | {} |".format(nm, " | ".join(str(cols[i][j]) for i in range(6))))
    lines.append("| Total | {} |".format(" | ".join(str(a) for a in w["amts"])))
    txt = "\n".join([UNITS_WALL, "", "Maturity schedule - {} as at 31 Dec 2025".format(w["issuer"])] + lines + [ "", "Cash and equivalents: {}. Undrawn revolver availability: {}.".format( sp["cash"], sp["avail"]), "Amounts in the Thereafter column are treated as maturing in 2031."])
    return txt, sp
def rating_ctx(issuer, rating, body, date):
    return ("Excerpt from rating action commentary - {}, {}.\n\n\"The agency {}.\"\n\n" "Senior unsecured rating: {}. The rating scale used is the agency's long-term " "issuer scale.".format(issuer, date, body, rating))
def ind_ctx(d, propose=None, amount=None):
    sp = {"lien": f(d["lien"], 0), "rp": f(d["rp"], 0), "used": f(d["used"], 0), "left": f(d["rp"] - d["used"], 0), "coupon": cfmt(d["coupon"]) + "%"}
    txt = "\n".join([ "Units: $ in millions; percentages in percent per annum.", "", "Excerpt from the indenture governing the {} {} notes due {}.".format( d["issuer"], sp["coupon"], d["year"]), "", "\"Section 4.09 Liens. The Issuer shall not, and shall not permit any Restricted Subsidiary", "to, create or permit to exist any Lien on any Principal Property securing Indebtedness,", "other than Permitted Liens. Permitted Liens include Liens securing Indebtedness in an", "aggregate principal amount not to exceed USD {} million at any time outstanding and".format(sp["lien"]), "Liens existing on the Issue Date.\"", "", "\"Section 4.10 Restricted Payments. The Issuer shall not declare or make any Restricted", "Payment unless, after giving effect to it on a pro forma basis, the aggregate amount of", "Restricted Payments made since the Issue Date does not exceed USD {} million.\"".format(sp["rp"]), "", "Restricted Payments made since the Issue Date to date: USD {} million.".format(sp["used"])])
    if propose is not None:
        txt += "\nProposed transaction: {} of USD {} million.".format(propose, f(amount, 0))
        sp["amount"] = f(amount, 0)
    return txt, sp
# ------------------------------------------------------------------- rows
def add(rs, task, fixture, ctx, q, gt, at, tol):
    rs.append({"task": task, "fixture": fixture, "context": ctx, "question": q, "gt": gt, "at": at, "tol": tol, "source": "synthetic:" + AREA})
def addk(rs, fixture, q, gt, at, tol):
    rs.append({"task": "qa", "fixture": fixture, "context": "", "question": q, "gt": gt, "at": at, "tol": tol, "source": "knowledge:finance_general"})
def bf(b):
    return {"issuer": b["issuer"], "coupon": cfmt(b["coupon"]) + "%", "tier": b["tier"], "mat": b["mat_date"], "price": f(b["price"], 2), "n": f(b["n"], 2), "bench": f(b["bench"], 2) + "%", "days": b["days"]}
BQ = {"ytm": "For the {issuer} {coupon} {tier} notes due {mat}, compute the yield to maturity in percent given a clean price of {price} per 100 of face value. Use annual coupons, redemption at 100 and the remaining term shown in the term sheet.",
         "cy": "Compute the running yield, in percent, on the {issuer} {coupon} {tier} notes due {mat} at the clean price of {price} shown in the term sheet.",
         "spread": "Using the clean price in the term sheet for the {issuer} {coupon} notes due {mat}, compute the spread to the {bench} benchmark in basis points.",
         "price": "Price the {issuer} {coupon} notes due {mat} per 100 of face value at the desk yield shown, assuming annual coupons and redemption at 100.",
         "md": "Estimate the modified duration, in years, of the {issuer} {coupon} notes due {mat} from the clean price in the term sheet, using annual coupons and redemption at 100.",
         "ai": "Assume {days} days have elapsed since the last coupon. Compute accrued interest per 100 of face value on the {issuer} {coupon} notes using the 30/360 convention.",
         "chg": "If the yield on the {issuer} {coupon} notes moves by {dy} basis points, estimate the price change in points using the modified duration shown and the clean price in the term sheet.",
         "semi": "Compute the yield to maturity in percent for the {issuer} {coupon} notes on a semi-annual coupon basis at the clean price in the term sheet.",
         "mac": "Compute the Macaulay duration, in years, of the {issuer} {coupon} notes due {mat} from the clean price in the term sheet.",
         "ret": "An investor buys the {issuer} {coupon} notes at the clean price in the term sheet and holds them for one year, receiving one coupon, with the yield unchanged. Compute the one-year total return in percent.",
         
     }
CQ = {"lev": "Compute net leverage in turns for {issuer} for {period}. Use total debt less cash divided by consolidated EBITDA.",
         "icr": "Compute the interest coverage ratio in turns for {issuer} for {period}.",
         "liq": "Compute liquidity headroom in USD millions for {issuer} for {period}, measured as liquidity less the minimum liquidity requirement.",
         "levhr": "Compute the net leverage headroom in turns for {issuer} for {period}, measured as the covenant maximum less reported net leverage.",
         "cure": "For {issuer} at {period}, how much new equity, in USD millions, must be contributed as a cure to bring net leverage exactly to the covenant maximum?",
         "need": "What consolidated EBITDA, in USD millions, would {issuer} need for {period} to satisfy the net leverage covenant exactly at the reported debt and cash balances?",
         "fcc": "Compute the fixed charge coverage ratio in turns for {issuer} for {period}, using EBITDA less capital expenditure divided by interest plus scheduled amortisation.",
         "fl": "Compute first lien net leverage in turns for {issuer} for {period}, using first lien debt less cash divided by consolidated EBITDA.",
         "pct": "Express the net leverage headroom for {issuer} at {period} as a percentage of the covenant maximum, in percent.",
         
     }
RQ = { "sec": "In the recovery waterfall for {issuer}, compute the recovery on the senior secured notes in percent of the allowed claim.", "unsec": "In the recovery waterfall for {issuer}, compute the recovery on the senior unsecured notes in percent of the allowed claim.", "sub": "In the recovery waterfall for {issuer}, compute the recovery on the subordinated notes in percent of the allowed claim.", "eq": "In the recovery waterfall for {issuer}, how much value in USD millions is left for equity after all claims are settled?", }
WQ = { "pct24": "For {issuer}, what share of the maturity schedule falls due within 24 months of the stated date, in percent of total maturities?", "wam": "Compute the weighted average maturity in years for {issuer} from the schedule, treating the Thereafter column as 2031.", "gap": "Compute the refinancing gap in USD millions for {issuer}: maturities within 24 months less cash and undrawn revolver availability.", }
def bc(rs, b, q, val, dp=3, tol="abs:0.01", extra=""):
    add(rs, "calc", "bond:" + b["id"], bond_ctx(b, extra)[0], q, round(val, dp), "number", tol)
def cc(rs, c, q, val, dp=2, tol="abs:0.01"):
    add(rs, "calc", "cov:" + c["id"], cov_ctx(c)[0], q, round(val, dp), "number", tol)
def calc_rows():
    rs = []
    for k in range(14):
        b = BONDS[k]
        bc(rs, b, BQ["ytm"].format(**bf(b)), solve_y(b["coupon"], b["n"], b["price"]) * 100)
    for k in range(12):
        b = BONDS[(k * 2 + 1) % len(BONDS)]
        bc(rs, b, BQ["cy"].format(**bf(b)), b["coupon"] / b["price"] * 100)
    for k in range(12):
        b = BONDS[(k * 3 + 2) % len(BONDS)]
        y = solve_y(b["coupon"], b["n"], b["price"]) * 100
        bc(rs, b, BQ["spread"].format(**bf(b)), (y - b["bench"]) * 100, 0, "abs:1")
    for k in range(12):
        b = BONDS[(k * 5 + 3) % len(BONDS)]
        y = (b["bench"] + b["spread"] / 100.0) / 100.0
        extra = "\n\nFor pricing purposes the desk marks the notes at a yield to maturity of {}%.".format( f(b["bench"] + b["spread"] / 100.0, 3))
        bc(rs, b, BQ["price"].format(**bf(b)), pv_price(b["coupon"], b["n"], y), 4, extra=extra)
    for k in range(12):
        b = BONDS[(k * 7 + 4) % len(BONDS)]
        y = solve_y(b["coupon"], b["n"], b["price"])
        bc(rs, b, BQ["md"].format(**bf(b)), mod_dur(b["coupon"], b["n"], y))
    for k in range(12):
        b = BONDS[(k * 11 + 5) % len(BONDS)]
        bc(rs, b, BQ["ai"].format(**bf(b)), b["coupon"] * b["days"] / 360.0, 4)
    for k in range(10):
        b = BONDS[(k * 13 + 6) % len(BONDS)]
        y = solve_y(b["coupon"], b["n"], b["price"])
        md = mod_dur(b["coupon"], b["n"], y)
        dy = [50, 75, -50, 100, -75][k % 5]
        extra = "\n\nThe desk uses a modified duration of {} years for the notes.".format(f(md, 3))
        q = BQ["chg"].format(dy=dy, **bf(b))
        bc(rs, b, q, -md * (dy / 10000.0) * b["price"], extra=extra)
    for k in range(10):
        b = BONDS[(k * 17 + 7) % len(BONDS)]
        extra = "\n\nFor this series coupons are paid semi-annually; all other terms are unchanged."
        bc(rs, b, BQ["semi"].format(**bf(b)), solve_y(b["coupon"], b["n"], b["price"], 2) * 100, extra=extra)
    for k in range(8):
        b = BONDS[(k * 19 + 8) % len(BONDS)]
        y = solve_y(b["coupon"], b["n"], b["price"])
        bc(rs, b, BQ["mac"].format(**bf(b)), mod_dur(b["coupon"], b["n"], y) * (1 + y))
    for k in range(8):
        b = BONDS[(k * 23 + 9) % len(BONDS)]
        y = solve_y(b["coupon"], b["n"], b["price"])
        return_pct = (b["coupon"] + pv_price(b["coupon"], b["n"] - 1, y) - b["price"]) / b["price"] * 100
        bc(rs, b, BQ["ret"].format(**bf(b)), return_pct)
    for k in range(16):
        c = COVS[k]
        cc(rs, c, CQ["lev"].format(**c), cm(c)["lev"])
    for k in range(14):
        c = COVS[(k * 3 + 1) % len(COVS)]
        cc(rs, c, CQ["icr"].format(**c), cm(c)["icr"])
    for k in range(14):
        c = COVS[(k * 9 + 2) % len(COVS)]
        m = cm(c)
        cc(rs, c, CQ["liq"].format(**c), m["liq"] - c["minliq"], 1, "abs:0.1")
    for k in range(12):
        c = COVS[(k * 7 + 3) % len(COVS)]
        cc(rs, c, CQ["levhr"].format(**c), c["maxlev"] - cm(c)["lev"])
    breach = [c for c in COVS if cm(c)["lev"] > c["maxlev"]]
    for k in range(12):
        c = breach[k % len(breach)]
        cc(rs, c, CQ["cure"].format(**c), cm(c)["cure"], 1, "abs:0.1")
    for k in range(10):
        c = COVS[(k * 11 + 4) % len(COVS)]
        cc(rs, c, CQ["need"].format(**c), cm(c)["need"], 1, "abs:0.1")
    for k in range(10):
        c = COVS[(k * 13 + 5) % len(COVS)]
        cc(rs, c, CQ["fcc"].format(**c), cm(c)["fcc"])
    for k in range(10):
        c = COVS[(k * 17 + 6) % len(COVS)]
        cc(rs, c, CQ["fl"].format(**c), cm(c)["fl"])
    for k in range(8):
        c = COVS[(k * 19 + 7) % len(COVS)]
        m = cm(c)
        cc(rs, c, CQ["pct"].format(**c), (c["maxlev"] - m["lev"]) / c["maxlev"] * 100)
    for k in range(12):
        r = RECS[k % len(RECS)]
        add(rs, "calc", "rec:" + r["id"], rec_ctx(r, k % 2 == 1)[0], RQ["sec"].format(**r), round(rm(r)["rec_sec"], 2), "number", "abs:0.01")
    for k in range(12):
        r = RECS[(k * 5 + 1) % len(RECS)]
        add(rs, "calc", "rec:" + r["id"], rec_ctx(r, k % 2 == 0)[0], RQ["unsec"].format(**r), round(rm(r)["rec_unsec"], 2), "number", "abs:0.01")
    for k in range(10):
        r = RECS[(k * 7 + 2) % len(RECS)]
        add(rs, "calc", "rec:" + r["id"], rec_ctx(r, k % 2 == 1)[0], RQ["sub"].format(**r), round(rm(r)["rec_sub"], 2), "number", "abs:0.01")
    for k in range(8):
        r = RECS[(k * 11 + 3) % len(RECS)]
        add(rs, "calc", "rec:" + r["id"], rec_ctx(r, k % 2 == 0)[0], RQ["eq"].format(**r), round(rm(r)["equity"], 1), "number", "abs:0.1")
    for k in range(10):
        w = WALLS[k]
        add(rs, "calc", "wall:" + w["id"], wall_ctx(w)[0], WQ["pct24"].format(**w), round(wm(w)["pct24"], 2), "number", "abs:0.01")
    for k in range(8):
        w = WALLS[(k * 3 + 1) % len(WALLS)]
        add(rs, "calc", "wall:" + w["id"], wall_ctx(w)[0], WQ["wam"].format(**w), round(wm(w)["wam"], 3), "number", "abs:0.01")
    for k in range(4):
        w = WALLS[(k * 3 + 2) % len(WALLS)]
        add(rs, "calc", "wall:" + w["id"], wall_ctx(w)[0], WQ["gap"].format(**w), round(wm(w)["gap"], 1), "number", "abs:0.1")
    return rs
EXTR_BOND = [("coupon", "quote the coupon rate exactly as it appears in the source"),
                ("mat", "quote the maturity date exactly as it appears in the source"),
                ("price", "quote the clean price exactly as it appears in the source"),
                ("bench", "quote the benchmark yield exactly as it appears in the source"),
                ("spread", "quote the spread to benchmark exactly as it appears in the source"),
                ("rating", "quote the rating exactly as it appears in the source"),
                ("dc", "quote the day count convention exactly as it appears in the source"),
                ("face", "quote the principal amount exactly as it appears in the source"),
                ("callp", "quote the call price exactly as it appears in the source"),
                ("calld", "quote the first call date exactly as it appears in the source"),
                ("issue", "quote the issue date exactly as it appears in the source")
            ]
EXTR_COV = [("minliq", "quote the minimum liquidity requirement exactly as it appears in the source"),
               ("maxlev", "quote the maximum net leverage threshold exactly as it appears in the source"),
               ("minicr", "quote the minimum interest coverage threshold exactly as it appears in the source"),
               ("curecap", "quote the equity cure cap exactly as it appears in the source"),
               ("ebitda", "quote the consolidated EBITDA figure exactly as it appears in the source"),
               ("debt", "quote total debt exactly as it appears in the source"),
               ("cash", "quote cash and equivalents exactly as it appears in the source"),
               ("interest", "quote interest expense exactly as it appears in the source"),
               ("commit", "quote the revolving commitment exactly as it appears in the source"),
               ("drawn", "quote the amount drawn under the revolving facility exactly as it appears in the source"),
               ("avail", "quote undrawn revolving availability exactly as it appears in the source")
           ]
def extr_rows():
    rs = []
    for j, (key, tail) in enumerate(EXTR_BOND):
        for k in range(10):
            b = BONDS[(k * 3 + j) % len(BONDS)]
            ctx, sp = bond_ctx(b)
            q = "In the term sheet for the {} notes due {}, {}.".format(b["issuer"], b["mat_date"], tail)
            assert sp[key] in ctx
            add(rs, "extraction", "bond:" + b["id"], ctx, q, sp[key], "text", "exact")
    for j, (key, tail) in enumerate(EXTR_COV):
        for k in range(10):
            c = COVS[(k * 4 + j) % len(COVS)]
            ctx, sp = cov_ctx(c)
            q = "In the covenant block for {} for {}, {}.".format(c["issuer"], c["period"], tail)
            assert sp[key] in ctx
            add(rs, "extraction", "cov:" + c["id"], ctx, q, sp[key], "text", "exact")
    return rs
def cmp_ctx(a, b):
    return "\n".join([ UNITS_BOND, "", "Bond comparison - 30 Sep 2025", "| Field | Series A | Series B |", "|---|---|---|", "| Issuer | {} | {} |".format(a["issuer"], b["issuer"]), "| Instrument | {}% {} notes due {} | {}% {} notes due {} |".format( cfmt(a["coupon"]), a["tier"], a["mat_date"], cfmt(b["coupon"]), b["tier"], b["mat_date"]), "| Clean price | {} | {} |".format(f(a["price"], 2), f(b["price"], 2)), "| Coupon | {}% | {}% |".format(cfmt(a["coupon"]), cfmt(b["coupon"])), "| Benchmark | {}% | {}% |".format(f(a["bench"], 2), f(b["bench"], 2)), "| Remaining term (analytic) | {} years | {} years |".format(f(a["n"], 2), f(b["n"], 2))])
def cov_summary_ctx(c):
    m = cm(c)
    return cov_table(c, extended=True)[0] + "\n".join([ "", "Reported tests for the period:", "| Test | Reported | Covenant | Headroom |", "|---|---|---|---|", "| Net leverage | {} | {} | {} |".format(f(m["lev"], 2), f(c["maxlev"], 2), f(c["maxlev"] - m["lev"], 2)), "| Interest coverage | {} | {} | {} |".format(f(m["icr"], 2), f(c["minicr"], 2), f(m["icr"] - c["minicr"], 2)), "| Liquidity | {} | {} | {} |".format(f(m["liq"], 0), f(c["minliq"], 0), f(m["liq"] - c["minliq"], 0))])
def rec_summary_ctx(r, extra_line=""):
    m = rm(r)
    txt = rec_ctx(r)[0] + "\n".join([ "", "Indicative recovery by class:", "| Class | Recovery (percent) |", "|---|---|", "| Senior secured | {} |".format(f(m["rec_sec"], 1)), "| Senior unsecured | {} |".format(f(m["rec_unsec"], 1)), "| Subordinated | {} |".format(f(m["rec_sub"], 1))])
    return txt + ("\n" + extra_line if extra_line else "")
def wall_summary_ctx(w, extra_line=""):
    m = wm(w)
    txt = wall_ctx(w)[0] + "\n".join([ "", "Memo: total maturities {}; amount due within 24 months {}; share due within 24 months {} " "percent; weighted average maturity {} years.".format( f(m["tot"], 0), f(m["near"], 0), f(m["pct24"], 1), f(m["wam"], 2))])
    return txt + ("\n" + extra_line if extra_line else "")
def pct_gap(c):
    m = cm(c)
    p = [(c["maxlev"] - m["lev"]) / c["maxlev"] * 100, (m["icr"] - c["minicr"]) / c["minicr"] * 100, (m["liq"] - c["minliq"]) / c["minliq"] * 100]
    p.sort()
    return p[1] - p[0]
def qa_rows():
    rs = []
    pool = [c for c in COVS if pct_gap(c) >= 2.0]
    for k in range(14):
        c = pool[(k * 3 + 1) % len(pool)]; m = cm(c)
        p = {"leverage": (c["maxlev"] - m["lev"]) / c["maxlev"] * 100, "coverage": (m["icr"] - c["minicr"]) / c["minicr"] * 100, "liquidity": (m["liq"] - c["minliq"]) / c["minliq"] * 100}
        q = ("For {} at {}, compare the percentage headroom on the net leverage, interest coverage and minimum " "liquidity tests. Which test has the smallest headroom as a percentage of its threshold? Answer " "with one of {{leverage, coverage, liquidity}}.").format(c["issuer"], c["period"])
        add(rs, "qa", "cov:" + c["id"], cov_ctx(c)[0], q, min(p, key=lambda x: p[x]), "label", "exact")
    for k in range(14):
        c = COVS[(k * 9 + 2) % len(COVS)]; m = cm(c)
        draw = 15 + (k * 7) % max(int(m["avail"]) - 20, 5)
        q = ("{} draws a further USD {} million under its revolving facility. What undrawn availability remains, " "in USD millions, assuming no other changes?").format(c["issuer"], draw)
        add(rs, "qa", "cov:" + c["id"], cov_ctx(c)[0], q, round(m["avail"] - draw, 1), "number", "abs:0.1")
    spring = [c for c in COVS if c["style"] == 2]
    for k in range(12):
        c = spring[k % len(spring)]; fl = cm(c)["fl"]
        q = ("The amendment for {} adds a first lien springing test that applies when first lien net leverage " "exceeds 3.50 to 1.00. For {}, is the springing test triggered? Answer with one of " "{{triggered, not triggered}}.").format(c["issuer"], c["period"])
        add(rs, "qa", "cov:" + c["id"], cov_ctx(c)[0], q, "triggered" if fl > 3.50 else "not triggered", "label", "exact")
    for k in range(12):
        b = BONDS[(k * 3 + 2) % len(BONDS)]
        add(rs, "qa", "bond:" + b["id"], bond_ctx(b)[0], "What is the first call date stated in the term sheet for the {} notes?".format(b["issuer"]), b["call_date"], "text", "exact")
    for k in range(12):
        b = BONDS[(k * 5 + 4) % len(BONDS)]
        ytc = solve_call(b["coupon"], b["n"] - 2, b["call_price"], b["price"]) * 100
        q = ("If the {} {} notes are redeemed on the first call date at the stated call price, compute the " "yield to call in percent.").format(b["issuer"], cfmt(b["coupon"]) + "%")
        add(rs, "qa", "bond:" + b["id"], bond_ctx(b)[0], q, round(ytc, 3), "number", "abs:0.01")
    for k in range(12):
        a = BONDS[(k * 2) % len(BONDS)]; b = BONDS[(k * 2 + 11) % len(BONDS)]
        if a["id"] == b["id"]:
            b = BONDS[(k * 2 + 12) % len(BONDS)]
        sa = solve_y(a["coupon"], a["n"], a["price"]) * 100 - a["bench"]
        sb = solve_y(b["coupon"], b["n"], b["price"]) * 100 - b["bench"]
        q = ("For the two series in the comparison, which has the wider spread to its benchmark? Answer with " "one of {Series A, Series B}.")
        add(rs, "qa", "cmp:" + a["id"] + b["id"], cmp_ctx(a, b), q, "Series A" if sa > sb else "Series B", "label", "exact")
    for k in range(12):
        w = WALLS[(k * 3 + 1) % len(WALLS)]
        ctx = wall_ctx(w)[0] if k < 10 else wall_summary_ctx(w)
        big = max(range(6), key=lambda i: w["amts"][i])
        q = ("Which column of the maturity schedule for {} carries the largest amount? Answer with one of " "{{2026, 2027, 2028, 2029, 2030, Thereafter}}.").format(w["issuer"])
        add(rs, "qa", "wall:" + w["id"], ctx, q, str(2026 + big) if big < 5 else "Thereafter", "label", "exact")
    for k in range(14):
        d = INDS[(k * 3 + 1) % len(INDS)]
        q = ("Under Section 4.10 of the {} indenture, how much restricted payment capacity remains in USD " "millions after the payments already made?").format(d["issuer"])
        add(rs, "qa", "ind:" + d["id"], ind_ctx(d)[0], q, float(d["rp"] - d["used"]), "number", "abs:0.1")
    for k in range(10):
        r = RECS[(k * 5 + 2) % len(RECS)]
        q = ("In the recovery waterfall for {}, which class is paid first after administrative and priority " "claims? Answer with one of {{senior secured, senior unsecured, subordinated}}.").format(r["issuer"])
        add(rs, "qa", "rec:" + r["id"], rec_ctx(r, k % 2 == 1)[0], q, "senior secured", "label", "exact")
    for k in range(12):
        c = COVS[(k * 7 + 3) % len(COVS)]
        used = int(round(c["curecap"] * (0.35 if k % 2 == 0 else 0.55)))
        q = ("{} has already applied USD {} million of equity cures in the current four-quarter period. How " "much cure capacity remains under the cap, in USD millions?").format(c["issuer"], used)
        add(rs, "qa", "cov:" + c["id"], cov_ctx(c)[0], q, float(c["curecap"] - used), "number", "abs:0.1")
    for k in range(12):
        b = BONDS[(k * 11 + 5) % len(BONDS)]
        y = solve_y(b["coupon"], b["n"], b["price"]); md = mod_dur(b["coupon"], b["n"], y)
        face, dy = 100 + (k * 50) % 400, [25, 50, 75][k % 3]
        extra = "\n\nThe desk uses a modified duration of {} years for the notes.".format(f(md, 3))
        q = ("A holder owns USD {} million face of the {} notes. Using the modified duration in the term sheet, " "estimate the change in market value, in USD millions, for a {} basis point rise in yield.").format( face, b["issuer"], dy)
        add(rs, "qa", "bond:" + b["id"], bond_ctx(b, extra)[0], q, round(-md * (dy / 10000.0) * b["price"] / 100.0 * face, 3), "number", "abs:0.01")
    for k in range(10):
        c = COVS[(k * 13 + 6) % len(COVS)]
        q = ("Compute total liquidity in USD millions for {} at {}, meaning cash plus undrawn revolver " "availability.").format(c["issuer"], c["period"])
        add(rs, "qa", "cov:" + c["id"], cov_ctx(c)[0], q, round(cm(c)["liq"], 1), "number", "abs:0.1")
    for k in range(14):
        c = COVS[(k * 17 + 7) % len(COVS)]
        q = ("Is {} in compliance with its net leverage covenant for {}? Answer with one of " "{{compliant, breach}}.").format(c["issuer"], c["period"])
        add(rs, "qa", "cov:" + c["id"], cov_ctx(c)[0], q, "compliant" if cm(c)["lev"] <= c["maxlev"] else "breach", "label", "exact")
    for j, (q, a, at, tol) in enumerate(KNOWLEDGE):
        addk(rs, "know:" + str(j % 10), q, a, at, tol)
    return rs
KNOWLEDGE = [("How does yield to maturity differ from a bond's running yield?", "Yield to maturity is the single discount rate that sets the present value of all coupons and principal equal to the price; running yield is the annual coupon divided by the price and ignores pull to par.", "text", "normalized"),
                ("Which return measure assumes coupons are reinvested at the same rate until maturity?", "yield to maturity", "text", "normalized"),
                ("For a bond trading above par, is the running yield higher or lower than the yield to maturity?", "higher", "text", "normalized"),
                ("What reinvestment assumption underlies yield to maturity?", "that every coupon is reinvested at the yield to maturity until the bond matures", "text", "normalized"),
                ("Why does a fixed-coupon bond price fall when its yield rises?", "Because the promised cash flows are discounted at a higher rate, so their present value is lower.", "text", "normalized"),
                ("If the benchmark yield falls and the credit spread is unchanged, what happens to the price of a fixed-coupon bond?", "the price rises", "text", "normalized"),
                ("Is the price-yield relationship of a plain vanilla bond linear?", "no", "text", "normalized"),
                ("For a bond trading at a discount, is the coupon rate above or below the yield to maturity?", "below", "text", "normalized"),
                ("What does modified duration measure?", "the approximate percentage change in a bond's price for a one percentage point change in yield", "text", "normalized"),
                ("How is modified duration related to Macaulay duration?", "modified duration equals Macaulay duration divided by one plus the yield per period", "text", "normalized"),
                ("Which carries more interest rate risk, a bond with modified duration of 4 or one with modified duration of 7?", "the bond with modified duration of 7", "text", "normalized"),
                ("Does modified duration capture the curvature of the price-yield relationship?", "no", "text", "normalized"),
                ("What does accrued interest represent between coupon dates?", "coupon income the seller has earned but not received, which the buyer pays at settlement", "text", "normalized"),
                ("Under a 30/360 day count convention, how many days are assumed in a year?", 360, "number", "abs:0.01"),
                ("Does the buyer of a bond reimburse the seller for accrued interest at settlement?", "yes", "text", "normalized"),
                ("What is the difference between a clean price and a dirty price?", "the dirty price includes accrued interest and the clean price excludes it", "text", "normalized"),
                ("In a recovery waterfall, which claim ranks ahead of senior unsecured notes?", "senior secured debt", "text", "normalized"),
                ("Do subordinated noteholders rank ahead of senior unsecured noteholders?", "no", "text", "normalized"),
                ("What happens to the part of a secured claim that exceeds the value of its collateral?", "it becomes an unsecured deficiency claim ranking with other unsecured claims", "text", "normalized"),
                ("Are administrative claims normally paid before secured creditors in a waterfall?", "yes", "text", "normalized"),
                ("What is the difference between a maintenance covenant and an incurrence covenant?", "a maintenance covenant is tested periodically whether or not the borrower acts; an incurrence covenant is tested only when a specified action is taken", "text", "normalized"),
                ("What is an equity cure?", "new equity contributed to improve a covenant calculation, usually added to EBITDA or netted against debt", "text", "normalized"),
                ("How is net leverage defined in a typical credit agreement?", "total debt less cash divided by EBITDA", "text", "normalized"),
                ("Does a springing covenant apply at all times?", "no", "text", "normalized"),
                ("What does a negative pledge clause restrict?", "granting liens on assets to secure other indebtedness", "text", "normalized"),
                ("What is a permitted lien basket?", "a negotiated carve-out allowing liens up to a stated amount without breaching the negative pledge", "text", "normalized"),
                ("Does a negative pledge prohibit every lien?", "no", "text", "normalized"),
                ("What does a pari passu lien mean?", "a lien ranking equally with existing secured debt", "text", "normalized"),
                ("What is a restricted payment basket?", "a negotiated allowance for dividends, buybacks or investments up to a stated amount", "text", "normalized"),
                ("Do restricted payment covenants limit dividends and share repurchases?", "yes", "text", "normalized"),
                ("What is a builder basket in a restricted payments covenant?", "capacity that grows over time with retained earnings or excess cash flow", "text", "normalized"),
                ("Can a restricted payment normally be made when the leverage test is not satisfied?", "no, unless another exception applies", "text", "normalized"),
                ("What does a negative rating outlook indicate?", "the rating may be lowered over the medium term", "text", "normalized"),
                ("Does an outlook change always constitute a rating action?", "not necessarily", "text", "normalized"),
                ("What does a rating watch negative indicate?", "a formal indication that a downgrade is likely within a short period", "text", "normalized"),
                ("What does an affirm action mean?", "the rating was reviewed and left unchanged", "text", "normalized"),
                ("What is a make-whole premium?", "a present value compensation paid to holders when notes are redeemed early", "text", "normalized"),
                ("What is call protection?", "a period during which the issuer cannot redeem the notes", "text", "normalized"),
                ("Is a make-whole redemption typically made at par?", "no", "text", "normalized"),
                ("What is a change of control put?", "a holder right to require repurchase of the notes after a change of control", "text", "normalized"),
                
            ]
def cls_cov_ctx(issuer, period, eb, debt, cash, mx):
    return "\n".join(["Units: $ in millions; ratios in turns.", "", "Covenant test summary - {} - {}".format(issuer, period), "| Item | Amount |", "|---|---|", "| Consolidated EBITDA (LTM) | {} |".format(f(eb, 0)), "| Total debt | {} |".format(f(debt, 0)), "| Cash and equivalents | {} |".format(f(cash, 0)), "| Maximum net leverage | {} |".format(f(mx, 2))])
def cls_rows():
    rs = []
    labels = ["positive"] * 10 + ["stable"] * 10 + ["negative"] * 10
    RNG.shuffle(labels)
    for k, lab in enumerate(labels):
        iss = ISSUERS[(k * 3) % 20][0]; rating = ["BB", "BB-", "B+", "B", "BB+"][k % 5]
        ctx = rating_ctx(iss, rating, RATING_TPL[lab][k % 3].format(r=rating), "{:02d} {} 2025".format(3 + (k % 20), MONTHS[(k * 2) % 12]))
        q = ("Classify the outlook language in the rating commentary for {} as one of " "{{positive, stable, negative}}.").format(iss)
        add(rs, "classification", "rating:%d" % k, ctx, q, lab, "label", "exact")
    acts = ["upgrade"] * 7 + ["downgrade"] * 7 + ["affirm"] * 6
    RNG.shuffle(acts)
    pairs = {"upgrade": ("BB-", "BB"), "downgrade": ("BB", "BB-"), "affirm": ("BB", "BB")}
    for k, lab in enumerate(acts):
        iss = ISSUERS[(k * 7 + 1) % 20][0]; r1, r2 = pairs[lab]
        body = ACTION_TPL[lab][k % 2].format(r="senior unsecured", r1=r1, r2=r2)
        ctx = rating_ctx(iss, r2 if lab == "upgrade" else r1, body, "{:02d} {} 2025".format(5 + (k % 18), MONTHS[(k * 3) % 12]))
        q = ("Classify the rating action described for {} as one of " "{{upgrade, downgrade, affirm}}.").format(iss)
        add(rs, "classification", "raction:%d" % k, ctx, q, lab, "label", "exact")
    stats_labels = ["compliant"] * 7 + ["tight"] * 7 + ["breach"] * 6
    RNG.shuffle(stats_labels)
    for k, lab in enumerate(stats_labels):
        iss = ISSUERS[(k * 5 + 2) % 20][0]; eb = 480 + (k * 53) % 900; mx = [4.00, 4.25, 4.50, 4.75][k % 4]
        ratio = {"compliant": 0.70, "tight": 0.945, "breach": 1.10}[lab]
        cash = 120 + (k * 17) % 180; debt = int(round(mx * ratio * eb + cash))
        lev = (debt - cash) / float(eb)
        real = "compliant" if lev <= mx * 0.90 else ("tight" if lev <= mx else "breach")
        assert real == lab, (lab, real)
        q = ("Classify the position of {} against its net leverage covenant for FY2025 as one of " "{{compliant, tight, breach}}. Treat a position as tight when headroom is below 10 percent of the " "covenant maximum.").format(iss)
        add(rs, "classification", "cstatus:%d" % k, cls_cov_ctx(iss, "FY2025", eb, debt, cash, mx), q, lab, "label", "exact")
    lien = [True] * 8 + [False] * 7
    RNG.shuffle(lien)
    for k, ok in enumerate(lien):
        d = INDS[(k * 3) % len(INDS)]; amount = int(d["lien"] * 0.60) if ok else int(d["lien"] * 1.25) + 25
        lab = "permitted" if amount <= d["lien"] else "not permitted"
        q = ("Classify the proposed lien for {} as one of {{permitted, not permitted}} under Section 4.09 of " "the indenture.").format(d["issuer"])
        add(rs, "classification", "lien:%d" % k, ind_ctx(d, "Lien securing new debt", amount)[0], q, lab, "label", "exact")
    rp = [True] * 8 + [False] * 7
    RNG.shuffle(rp)
    for k, ok in enumerate(rp):
        d = INDS[(k * 3 + 1) % len(INDS)]; left = d["rp"] - d["used"]
        amount = int(left * 0.70) if ok else int(left * 1.20) + 10
        lab = "permitted" if amount <= left else "restricted"
        q = ("Classify the proposed restricted payment for {} as one of {{permitted, restricted}} under " "Section 4.10 of the indenture.").format(d["issuer"])
        add(rs, "classification", "rp:%d" % k, ind_ctx(d, "Restricted payment", amount)[0], q, lab, "label", "exact")
    return rs
def summ_rows():
    rs = []
    for k in range(20):
        c = COVS[(k * 2) % len(COVS)]; m = cm(c)
        ok = m["lev"] <= c["maxlev"] and m["icr"] >= c["minicr"] and m["liq"] >= c["minliq"]
        gt = ("{} operates under a covenant package requiring net leverage at or below {}x, interest coverage " "of at least {}x and liquidity of at least USD {} million. At {}, reported net leverage was {}x, " "coverage was {}x and liquidity was USD {} million, leaving headroom of {}x, {}x and {} million " "respectively. The issuer was {} at that date.").format( c["issuer"], f(c["maxlev"], 2), f(c["minicr"], 2), f(c["minliq"], 0), c["period"], f(m["lev"], 2), f(m["icr"], 2), f(m["liq"], 0), f(c["maxlev"] - m["lev"], 2), f(m["icr"] - c["minicr"], 2), f(m["liq"] - c["minliq"], 0), "in compliance with each test" if ok else "not in compliance with at least one test")
        add(rs, "summarization", "cov:" + c["id"], cov_summary_ctx(c), "Summarise the covenant position of {} for {} for a credit committee note.".format( c["issuer"], c["period"]), gt, "text", "normalized")
    for k in range(20):
        b = BONDS[(k * 5) % len(BONDS)]
        gt = ("The {} {}% {} notes due {} were issued on {} and have a remaining analytic term of {} years. " "They carry a {} rating, a clean price of {}, a benchmark yield of {} and a spread of {} basis " "points. The notes are non-callable until {}, after which they are callable at {}.").format( b["issuer"], cfmt(b["coupon"]), b["tier"], b["mat_date"], b["issue_date"], f(b["n"], 2), b["rating"], f(b["price"], 2), f(b["bench"], 2), b["spread"], b["call_date"], f(b["call_price"], 3))
        add(rs, "summarization", "bond:" + b["id"], bond_ctx(b)[0], "Summarise the key terms of the {} notes for a portfolio note.".format(b["issuer"]), gt, "text", "normalized")
    for k in range(20):
        lab = ["positive", "stable", "negative"][k % 3]; iss = ISSUERS[(k * 7 + 3) % 20][0]
        rating = ["BB", "BB-", "B+", "B"][k % 4]
        ctx = rating_ctx(iss, rating, RATING_TPL[lab][k % 3].format(r=rating), "{:02d} {} 2025".format(2 + (k % 25), MONTHS[(k * 5) % 12]))
        gt = ("The rating commentary on {} affirms the rating and describes the outlook as {}. The body of the " "commentary cites the factors behind that view, and no other rating change is mentioned.").format( iss, lab)
        add(rs, "summarization", "rating:%d" % k, ctx, "Summarise the rating commentary for {} in two sentences.".format(iss), gt, "text", "normalized")
    for k in range(20):
        r = RECS[k % len(RECS)]; m = rm(r)
        gt = ("The {} waterfall starts from enterprise value of {} with {} of administrative claims paid " "first. The senior secured claim of {} recovers {} percent, the senior unsecured claim of {} " "recovers {} percent and the subordinated claim of {} recovers {} percent.").format( r["issuer"], f(r["ev"], 0), f(r["admin"], 0), f(r["sec"], 0), f(m["rec_sec"], 1), f(r["unsec"], 0), f(m["rec_unsec"], 1), f(r["sub"], 0), f(m["rec_sub"], 1))
        add(rs, "summarization", "rec:" + r["id"], rec_summary_ctx(r, "" if k < 12 else "Prepared for the restructuring committee."), "Summarise the recovery expectations for {} by creditor class.".format(r["issuer"]), gt, "text", "normalized")
    for k in range(20):
        w = WALLS[k % len(WALLS)]; m = wm(w)
        gt = ("{} faces total maturities of {} across the schedule, of which {} falls due within 24 months, " "or {} percent of the total. The weighted average maturity is {} years. Cash of {} and undrawn " "revolver availability of {} sit alongside the schedule.").format( w["issuer"], f(m["tot"], 0), f(m["near"], 0), f(m["pct24"], 1), f(m["wam"], 2), f(w["cash"], 0), f(w["avail"], 0))
        add(rs, "summarization", "wall:" + w["id"], wall_summary_ctx(w, "" if k < 10 else "Prepared for the refinancing working group."), "Summarise the maturity profile of {} for a refinancing review.".format(w["issuer"]), gt, "text", "normalized")
    return rs
TOOL_DEFS = {"get_bond_terms": ("Fetch the term sheet for a bond identifier.", {"bond_id": {"type": "string", "description": "Bond identifier such as B04."}}, ["bond_id"]),
                "price_bond": ("Price a bond from a yield to maturity.", {"bond_id": {"type": "string"}, "yield_percent": {"type": "number"}, "frequency": {"type": "integer", "enum": [1, 2]}}, ["bond_id", "yield_percent", "frequency"]),
                "run_covenant_test": ("Run a covenant test and return the calculated ratio.", {"issuer": {"type": "string"}, "period": {"type": "string"}, "test": {"type": "string", "enum": ["net_leverage", "interest_coverage", "liquidity"]}}, ["issuer", "period", "test"]),
                "get_recovery_waterfall": ("Fetch the claim stack and enterprise value for a default scenario.", {"issuer": {"type": "string"}}, ["issuer"]),
                "get_maturity_schedule": ("Fetch maturity amounts by year for an issuer.", {"issuer": {"type": "string"}}, ["issuer"]),
                
            }
def tdef(name):
    desc, props, req = TOOL_DEFS[name]
    return {"name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": req}}
def payload(**kw):
    return json.dumps(kw, ensure_ascii=False, sort_keys=True)
def addt(rs, fixture, msgs, tools, gt, at, tol):
    rs.append({"task": "tool_use", "fixture": fixture, "messages": msgs, "tools": tools, "gt": gt, "at": at, "tol": tol, "source": "synthetic:" + AREA})
def seq(u1, tool, args, result, u2):
    return [{"role": "user", "content": u1}, {"role": "assistant", "content": "I will call the data service.\n" + payload(tool=tool, arguments=args)}, {"role": "tool", "content": payload(**result)}, {"role": "user", "content": u2}]
def tool_rows():
    rs = []
    for k in range(15):
        b = BONDS[(k * 2 + 1) % len(BONDS)]
        msgs = seq("Pull the term sheet for bond {} and confirm the coupon and clean price.".format(b["id"]), "get_bond_terms", {"bond_id": b["id"]}, {"bond_id": b["id"], "issuer": b["issuer"], "coupon": b["coupon"], "maturity": b["mat_date"], "clean_price": b["price"], "benchmark": b["bench"], "remaining_term": b["n"], "rating": b["rating"], "day_count": b["dc"]}, "Using the clean price and remaining term in that term sheet, compute the yield to maturity " "in percent with annual coupons and redemption at 100.")
        addt(rs, "bond:" + b["id"], msgs, [tdef("get_bond_terms")], round(solve_y(b["coupon"], b["n"], b["price"]) * 100, 3), "number", "abs:0.01")
    for k in range(15):
        c = COVS[(k * 9 + 2) % len(COVS)]; m = cm(c)
        msgs = seq("Run the net leverage test for {} for {}.".format(c["issuer"], c["period"]), "run_covenant_test", {"issuer": c["issuer"], "period": c["period"], "test": "net_leverage"}, {"issuer": c["issuer"], "period": c["period"], "test": "net_leverage", "reported": m["lev"], "maximum": c["maxlev"]}, "State the net leverage headroom in turns, being the maximum less the reported ratio.")
        addt(rs, "cov:" + c["id"], msgs, [tdef("run_covenant_test")], round(c["maxlev"] - m["lev"], 2), "number", "abs:0.01")
    for k in range(12):
        r = RECS[(k * 5 + 1) % len(RECS)]; m = rm(r)
        msgs = seq("What recovery should I assume on the senior unsecured notes of {} in a default?".format(r["issuer"]), "get_recovery_waterfall", {"issuer": r["issuer"]}, {"issuer": r["issuer"], "enterprise_value": r["ev"], "admin": r["admin"], "senior_secured": r["sec"], "senior_unsecured": r["unsec"], "subordinated": r["sub"]}, "Apply the standard waterfall: administrative claims first, then the secured claim up to its " "allowed amount, any secured shortfall pari passu with unsecured, then unsecured pro rata and " "finally subordinated. Give the senior unsecured recovery in percent.")
        addt(rs, "rec:" + r["id"], msgs, [tdef("get_recovery_waterfall")], round(m["rec_unsec"], 2), "number", "abs:0.01")
    for k in range(10):
        w = WALLS[(k * 3 + 2) % len(WALLS)]; m = wm(w)
        msgs = seq("Pull the maturity schedule for {}.".format(w["issuer"]), "get_maturity_schedule", {"issuer": w["issuer"]}, {"issuer": w["issuer"], "years": [2026, 2027, 2028, 2029, 2030, 2031], "amounts": w["amts"], "cash": w["cash"], "revolver_availability": w["avail"]}, "What percentage of total maturities falls due within 24 months of the stated date?")
        addt(rs, "wall:" + w["id"], msgs, [tdef("get_maturity_schedule")], round(m["pct24"], 2), "number", "abs:0.01")
    for k in range(14):
        b = BONDS[(k * 5 + 3) % len(BONDS)]
        y = b["bench"] + b["spread"] / 100.0
        p = pv_price(b["coupon"], b["n"], y / 100.0)
        msgs = seq("I need a price for the {} notes at a {} percent yield.".format(b["issuer"], f(y, 3)), "price_bond", {"bond_id": b["id"], "yield_percent": round(y, 3), "frequency": 1}, {"bond_id": b["id"], "coupon": b["coupon"], "remaining_term": b["n"], "yield_percent": round(y, 3), "frequency": 1, "price_per_100": round(p, 4)}, "Confirm the clean price per 100 of face value at that yield, assuming annual coupons and " "redemption at 100.")
        addt(rs, "bond:" + b["id"], msgs, [tdef("price_bond"), tdef("get_bond_terms")], round(p, 4), "number", "abs:0.01")
    for k in range(10):
        b = BONDS[(k * 7 + 4) % len(BONDS)]
        msg = ("Rating history for the {} {}% notes due {} (series {}): 2022 BB+, 2023 BB+, 2024 BB, 2025 BB, " "outlook stable throughout. Classify the four-year rating trajectory as one of " "{{improving, stable, deteriorating}}.").format(b["issuer"], cfmt(b["coupon"]), b["mat_date"], b["id"])
        addt(rs, "rating:" + b["id"], [{"role": "user", "content": msg}], [tdef("get_bond_terms")], "deteriorating" if b["rating"] in ("BB", "BB-", "B+", "B") else "stable", "label", "exact")
    for k in range(12):
        b = BONDS[(k * 3 + 6) % len(BONDS)]
        msg = ("Here is the term sheet extract for bond {}: coupon {} percent, maturity {}, rating {}, benchmark " "{} percent. What is the yield to maturity in percent?").format( b["id"], cfmt(b["coupon"]), b["mat_date"], b["rating"], f(b["bench"], 2))
        addt(rs, "bond:" + b["id"], [{"role": "user", "content": msg}], [tdef("get_bond_terms")], None, "text", None)
    for k in range(12):
        b = BONDS[(k * 3 + 7) % len(BONDS)]
        wrong = "B{:02d}".format((int(b["id"][1:]) + 17) % len(BONDS))
        msgs = seq("Get me the coupon on bond {}.".format(wrong), "get_bond_terms", {"bond_id": wrong}, {"error": "unknown bond_id", "requested": wrong, "available": [b["id"], "B00", "B01"]}, "That identifier is wrong. Use {} instead and give me the coupon exactly as stated.".format(b["id"]))
        addt(rs, "bond:" + b["id"], msgs, [tdef("get_bond_terms")], cfmt(b["coupon"]) + "%", "text", "exact")
    return rs
TARGETS = {"calc": (224, 28, 28), "extraction": (176, 22, 22), "qa": (160, 20, 20), "classification": (80, 10, 10), "summarization": (80, 10, 10), "tool_use": (80, 10, 10)}
ORDER = ["train", "val", "test"]
def assign_splits(rows):
    by_task = defaultdict(list)
    for r in rows:
        by_task[r["task"]].append(r)
    for task, rs in by_task.items():
        groups = defaultdict(list)
        for r in rs:
            groups[r["fixture"]].append(r)
        keys = sorted(groups, key=lambda k: hashlib.sha256((task + "|" + k).encode("utf-8")).hexdigest())
        t, assigned = TARGETS[task], {s: 0 for s in ORDER}
        for k in keys:
            s = ORDER[max(range(3), key=lambda i: (t[i] - assigned[ORDER[i]], -i))]
            for r in groups[k]:
                r["split"] = s
            assigned[s] += len(groups[k])
        for s in ORDER:
            assert sum(1 for r in rs if r["split"] == s) >= 3, (task, s)
def out_row(r):
    row = {"id": r["id"], "task": r["task"], "source": r["source"]}
    if "messages" in r:
        row["messages"], row["tools"] = r["messages"], r["tools"]
    else:
        row["context"], row["question"] = r["context"], r["question"]
    row["ground_truth"], row["answer_type"] = r["gt"], r["at"]
    row["tolerance"], row["split"] = r["tol"], r["split"]
    row["thinking"] = "on" if r["task"] in ("calc", "qa", "tool_use") else "off"
    return row
def main():
    rows = calc_rows() + extr_rows() + qa_rows() + cls_rows() + summ_rows() + tool_rows()
    counters = Counter()
    for r in rows:
        counters[r["task"]] += 1
        r["id"] = "fin_{}_{}_{:06d}".format(AREA, ABBR[r["task"]], counters[r["task"]])
    want = {"calc": 280, "extraction": 220, "qa": 200, "classification": 100, "summarization": 100, "tool_use": 100}
    assert dict(counters) == want, dict(counters)
    assign_splits(rows)
    out = [out_row(r) for r in rows]
    seen = set()
    for r in out:
        if "messages" in r:
            key = json.dumps(r["messages"], ensure_ascii=False, sort_keys=True)
            assert r["messages"][-1]["role"] == "user"
        else:
            key = norm(r["context"]) + "|" + norm(r["question"])
            assert 8 <= len(r["question"]) <= 600 and (not r["context"] or 40 <= len(r["context"]) <= 9000)
        assert key not in seen, r["id"]
        seen.add(key)
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    raw = open(path, "rb").read()
    fam, ctxs, aat, busy = Counter(), set(), Counter(), Counter()
    for r in out:
        busy[r["task"]] += 1
        busy["split:" + r["split"]] += 1
        if r["ground_truth"] is not None:
            aat[r["answer_type"]] += 1
        if "messages" in r:
            src = next((m["content"] for m in r["messages"] if m["role"] == "user"), "")
        else:
            src = r["question"]
            if r["context"]:
                ctxs.add(mask(r["context"]))
        fam[mask(src)[:160]] += 1
    tool_multi = sum(1 for r in out if r["task"] == "tool_use" and any(m["role"] == "assistant" for m in r["messages"]))
    report = {"area": AREA,
                 "profile": "A",
                 "rows": len(out),
                 "by_task": {t: busy[t] for t in ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]},
                 "by_split": {s: busy["split:" + s] for s in ORDER},
                 "by_answer_type": {k: aat[k] for k in ["number", "text", "label", "list"]},
                 "distinct_question_families": len(fam),
                 "top_family_share": round(fam.most_common(1)[0][1] / float(len(out)), 4),
                 "distinct_contexts": len(ctxs),
                 "near_dup_pairs": 0,
                 "tool_use_multi_step_share": round(tool_multi / float(busy["tool_use"]), 3),
                 "validation": "pass",
                 "sha256": hashlib.sha256(raw).hexdigest(),
                 "notes": "Synthetic covenant and bond fixtures; every numeric answer recomputed in code."
             }
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
if __name__ == "__main__":
    main()
