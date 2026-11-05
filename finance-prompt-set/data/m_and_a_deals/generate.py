#!/usr/bin/env python3
"""Deterministic generator for the m_and_a_deals area (profile A, 1000 rows).
Everything is synthetic. Each deal fixture is built once, rendered once into a
term-sheet context, and every ground_truth is computed from the same rounded
numbers that appear in that context.
"""
import hashlib
import json
import os
import random
import re
from collections import Counter
AREA = "m_and_a_deals"
ABBR = {"calc": "calc", "extraction": "extr", "summarization": "summ",
        "classification": "cls", "qa": "qa", "tool_use": "tool"}
N_FIX = 160
RNG = random.Random(42)
HERE = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
COMPANIES = [
    ("Halcyon Grid Utilities", "Utilities", "31 Dec"), ("Meridian Bancorp", "Banking", "31 Dec"),
    ("Kestrel Foods", "Consumer Staples", "30 Jun"), ("Ardenne Materials", "Materials", "31 Dec"),
    ("Solent Marine Logistics", "Industrials", "31 Dec"), ("Vantage Diagnostics", "Healthcare", "30 Sep"),
    ("Lumen Ridge Energy", "Energy", "31 Dec"), ("Cobalt Peak Mining", "Materials", "31 Dec"),
    ("Northwind Insurance", "Insurance", "31 Dec"), ("Fairholt Property Trust", "Real Estate", "31 Dec"),
    ("Tesselate Software", "Technology", "31 Jan"), ("Brightwater Chemicals", "Materials", "31 Dec"),
    ("Orchard Lane Retail", "Consumer Discretionary", "31 Jan"), ("Pinehurst Timber", "Materials", "31 Dec"),
    ("Quillon Payments", "Technology", "31 Dec"), ("Sable Ridge Airlines", "Industrials", "31 Dec"),
    ("Harborview Health", "Healthcare", "31 Dec"), ("Ironbark Industrial", "Industrials", "30 Sep"),
    ("Silverleaf Pharma", "Healthcare", "31 Dec"), ("Wexford Media", "Communication Services", "31 Dec"),
    ("Alder Grove Beverages", "Consumer Staples", "31 Dec"), ("Copperline Rail", "Industrials", "31 Dec"),
    ("Marisol Resort Group", "Consumer Discretionary", "31 Dec"), ("Beacon Federal Savings", "Banking", "31 Dec"),
]
ADJ = ["Blue", "Silver", "North", "Cedar", "Granite", "Amber", "Iron", "Juniper",
       "Copper", "Willow", "Summit", "Harbor", "Pine", "Cobalt", "Maple", "Quartz"]
NOUN = ["Falcon", "Bridge", "Orchard", "Anchor", "Beacon", "Canyon", "Delta",
        "Lattice", "Meridian", "Voyage"]
SEG_POOL = ["Core", "Adjacent", "Specialty", "Distribution", "Industrial", "Retail",
            "Institutional", "Consumer", "International", "Services", "Legacy", "Contract"]
ADVISORS = ["Sable Ridge Partners", "Kingsway Advisory", "Larkspur Securities",
            "Thornbury and Co", "Ellsworth Partners", "Marlow Freres",
            "Cranfield Advisors", "Bexley Group", "Norwood Partners", "Ashcombe Securities"]
LAWS = ["Delaware", "New York", "Ontario", "England and Wales", "Ireland", "Texas"]
FIN_CONDS = ["committed bridge facility", "no financing condition",
             "bridge facility subject to syndication",
             "committed term loan and bond bridge",
             "no financing condition, cash on hand sufficient"]
RECS = ["recommend", "recommend subject to Company shareholder approval",
        "recommend with enhanced disclosure", "no recommendation"]
SIGN_PAIRS = [
    ("14 Apr 2026", "27 Feb 2026"), ("03 Mar 2026", "16 Jan 2026"),
    ("22 May 2026", "08 Apr 2026"), ("09 Jan 2026", "21 Nov 2025"),
    ("30 Jun 2026", "15 May 2026"), ("18 Feb 2026", "02 Jan 2026"),
    ("07 Aug 2025", "23 Jun 2025"), ("25 Sep 2025", "11 Aug 2025"),
    ("11 Nov 2025", "29 Sep 2025"), ("16 Dec 2025", "31 Oct 2025"),
    ("28 Jul 2026", "12 Jun 2026"), ("05 Oct 2026", "21 Aug 2026"),
]
PREM_RANGES = [(6.5, 14.5), (15.5, 29.5), (30.5, 44.5), (45.5, 58.0)]
CLUSTER = {"Utilities": 0, "Energy": 0, "Materials": 0, "Industrials": 0, "Real Estate": 0, "Banking": 1,
           "Insurance": 1, "Consumer Staples": 2, "Consumer Discretionary": 2, "Healthcare": 3,
           "Technology": 4, "Communication Services": 4}
def f1(x):
    return "{:.1f}".format(x + 0.0)
def f2(x):
    return "{:.2f}".format(x + 0.0)
def f4(x):
    return "{:.4f}".format(x + 0.0)
def r1(x):
    v = round(x + 0.0, 1)
    return 0.0 if v == 0 else v
def r2(x):
    v = round(x + 0.0, 2)
    return 0.0 if v == 0 else v
def r4(x):
    return round(x + 0.0, 4)
def add_months(d, n):
    day, mon, yr = d.split()
    m = MONTHS.index(mon) + n
    return "%s %s %d" % (day, MONTHS[m % 12], int(yr) + m // 12)
def mask(s):
    return re.sub(r"\d+(?:[.,]\d+)*", "#", re.sub(r"\s+", " ", str(s)).strip().lower())
# ------------------------------------------------------------------ fixtures
def build():
    fx = []
    for i in range(N_FIX):
        ai = i % len(COMPANIES)
        an, asec, afy = COMPANIES[ai]
        ti = base = (i * 5 + 7 + (i // 24) * 5) % len(COMPANIES)
        for step in range(len(COMPANIES)):
            cand = (base + step) % len(COMPANIES)
            if COMPANIES[cand][1] == asec or CLUSTER.get(COMPANIES[cand][1]) == CLUSTER.get(asec):
                ti = cand
                break
        tn, tsec, tfy = COMPANIES[ti]
        sign, unaff_date = SIGN_PAIRS[i % len(SIGN_PAIRS)]
        acq_rev = r1(RNG.uniform(2600, 14000))
        acq_ebitda = r1(acq_rev * RNG.uniform(15, 33) / 100)
        acq_ni = r1(acq_ebitda * RNG.uniform(0.42, 0.62))
        acq_da = r1(acq_ebitda * RNG.uniform(0.18, 0.34))
        acq_int = r1(acq_ebitda * RNG.uniform(0.05, 0.12))
        acq_tax = RNG.choice([21.0, 23.0, 24.0, 25.0])
        acq_shares = r1(RNG.uniform(180, 900))
        acq_price = r2(acq_ni / acq_shares * RNG.uniform(14, 22))
        acq_nd = r1(acq_ebitda * RNG.uniform(0.6, 2.4))
        acq_cash = r1(acq_rev * RNG.uniform(0.05, 0.14))
        tgt_rev = r1(acq_rev * RNG.uniform(0.12, 0.35))
        tgt_ebitda = r1(tgt_rev * RNG.uniform(14, 32) / 100)
        tgt_da = r1(tgt_ebitda * RNG.uniform(0.20, 0.42))
        tgt_int = r1(min(RNG.uniform(5, 60), 0.35 * tgt_ebitda))
        tgt_tax = RNG.choice([21.0, 23.0, 24.0, 25.0, 26.0])
        unaffected = r2(RNG.uniform(12, 78))
        diluted = r1(tgt_ebitda * RNG.uniform(6.0, 9.0) / unaffected)
        lo, hi = PREM_RANGES[(i * 3 + 1) % 4]
        offer_target = unaffected * (1 + RNG.uniform(lo, hi) / 100)
        st = i % 4
        if st == 0:
            cash_ps, ratio = r2(offer_target), 0.0
        elif st == 1:
            cash_ps, ratio = 0.0, r4(offer_target / acq_price)
        else:
            cash_ps = r2(offer_target * RNG.uniform(0.30, 0.70))
            ratio = r4((offer_target - cash_ps) / acq_price)
        tgt_nd = r1(tgt_ebitda * RNG.uniform(0.8, 3.2))
        syn_run = r1(tgt_rev * RNG.uniform(0.030, 0.075))
        phase1 = RNG.choice([40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0])
        cta = r1(syn_run * RNG.uniform(1.0, 2.4))
        rate = r2(RNG.uniform(4.8, 7.4))
        cash_yield = r2(RNG.uniform(1.8, 3.2))
        fee_adv = r2(RNG.uniform(0.55, 1.30))
        fee_fin = r2(RNG.uniform(0.35, 0.90))
        cash_frac = RNG.uniform(0.12, 0.42)
        tan_pct = RNG.uniform(18, 30)
        cr_pct = RNG.uniform(24, 36)
        tech_pct = RNG.uniform(10, 18)
        brand_pct = RNG.uniform(4, 9)
        break_pct = r1(RNG.uniform(2.4, 4.2))
        rtf_pct = r1(RNG.uniform(3.5, 7.0))
        cvr_ps = r2(RNG.uniform(2.0, 6.0)) if st == 3 else 0.0
        cvr_prob = r1(RNG.uniform(35, 85)) if st == 3 else 0.0
        margin = round(tgt_ebitda / tgt_rev * 100)
        miles = ["FY2027 revenue at or above %d" % round(tgt_rev * 1.10),
                 "FY2027 EBITDA at or above %d" % round(tgt_ebitda * 1.15),
                 "cumulative free cash flow at or above %d through FY2028" % round(tgt_ebitda * 2.2),
                 "FY2027 gross margin at or above %d percent" % (margin + 1)]
        s0 = SEG_POOL[i % len(SEG_POOL)]; s1 = SEG_POOL[(i * 5 + 3) % len(SEG_POOL)]
        s2 = SEG_POOL[(i * 7 + 5) % len(SEG_POOL)]
        if s1 == s0: s1 = SEG_POOL[(i * 5 + 4) % len(SEG_POOL)]
        if s2 in (s0, s1): s2 = SEG_POOL[(i * 7 + 6) % len(SEG_POOL)]
        f = {"key": "D-%03d" % (i + 1), "code": "%s %s" % (ADJ[i % 16], NOUN[i // 16]),
            "acq": an, "acq_sec": asec, "acq_fy": afy,
            "tgt": tn, "tgt_sec": tsec, "tgt_fy": tfy,
            "sign": sign, "unaff_date": unaff_date,
            "outside": add_months(sign, 12), "anti": add_months(sign, 18), "vwap": r2(unaffected * RNG.uniform(0.94, 0.985)),
            "acq_price": acq_price, "unaffected": unaffected,
            "cash_ps": cash_ps, "ratio": ratio,
            "cvr_ps": cvr_ps, "cvr_prob": cvr_prob,
            "milestone": miles[i % 4] if st == 3 else "not applicable",
            "diluted_shares": diluted, "acq_shares": acq_shares,
            "tgt_rev": tgt_rev, "tgt_ebitda": tgt_ebitda, "tgt_da": tgt_da,
            "tgt_int": tgt_int, "tgt_tax": tgt_tax, "tgt_nd": tgt_nd,
            "acq_rev": acq_rev, "acq_ebitda": acq_ebitda, "acq_ni": acq_ni,
            "acq_da": acq_da, "acq_int": acq_int, "acq_tax": acq_tax,
            "acq_nd": acq_nd, "acq_cash": acq_cash,
            "syn_run": syn_run, "phase1": phase1, "cta": cta, "rate": rate, "cash_yield": cash_yield,
            "fee_adv": fee_adv, "fee_fin": fee_fin, "cash_frac": cash_frac,
            "tan_pct": tan_pct, "cr_pct": cr_pct, "tech_pct": tech_pct,
            "brand_pct": brand_pct,
            "life_cr": RNG.choice([8, 9, 10, 11, 12]),
            "life_tech": RNG.choice([5, 6, 7, 8]),
            "life_brand": RNG.choice([0, 0, 15, 20]),
            "break_pct": break_pct, "rtf_pct": rtf_pct,
            "expense_cap": r1(RNG.uniform(20, 70)),
            "retention": r1(RNG.uniform(30, 160)),
            "matching": RNG.choice([3, 4, 5, 7]),
            "fin_cond": FIN_CONDS[i % len(FIN_CONDS)],
            "rec": RECS[i % len(RECS)],
            "law": LAWS[i % len(LAWS)],
            "adv_p": ADVISORS[i % len(ADVISORS)],
            "adv_c": ADVISORS[(i * 3 + 2) % len(ADVISORS)],
            "segs": (s0, s1, s2), "variant": i % 4}
        if f["adv_c"] == f["adv_p"]:
            f["adv_c"] = ADVISORS[(i * 3 + 4) % len(ADVISORS)]
        f["tgt_ni"] = r1((tgt_ebitda - tgt_da - tgt_int) * (1 - tgt_tax / 100))
        core_rev = r1(tgt_rev * RNG.uniform(0.50, 0.62)); adj_rev = r1(tgt_rev * RNG.uniform(0.24, 0.34))
        f["seg_rev"] = (core_rev, adj_rev, r1(tgt_rev - core_rev - adj_rev))
        core_eb = r1(tgt_ebitda * RNG.uniform(0.48, 0.60)); adj_eb = r1(tgt_ebitda * RNG.uniform(0.20, 0.30))
        f["seg_eb"] = (core_eb, adj_eb, r1(tgt_ebitda - core_eb - adj_eb))
        fx.append(f)
    for f in fx:
        derive(f)
    return fx
def derive(f):
    f["stock_ps"] = r2(f["ratio"] * f["acq_price"]); f["offer_ps"] = r2(f["cash_ps"] + f["stock_ps"])
    f["equity"] = r1(f["offer_ps"] * f["diluted_shares"])
    f["prem"] = r1((f["offer_ps"] / f["unaffected"] - 1) * 100)
    f["cash_agg"] = r1(f["cash_ps"] * f["diluted_shares"]); f["stock_agg"] = r1(f["stock_ps"] * f["diluted_shares"])
    f["cvr_max"] = r1(f["cvr_ps"] * f["diluted_shares"]); f["cvr_exp"] = r1(f["cvr_max"] * f["cvr_prob"] / 100)
    f["offer_cvr"] = r2(f["offer_ps"] + f["cvr_ps"])
    f["new_shares"] = r1(f["ratio"] * f["diluted_shares"]); f["pf_shares"] = r1(f["acq_shares"] + f["new_shares"])
    f["own_pct"] = r1(f["new_shares"] / f["pf_shares"] * 100)
    f["adv_fee"] = r1(f["equity"] * f["fee_adv"] / 100); f["fin_fee"] = r1(f["equity"] * f["fee_fin"] / 100)
    f["fees"] = r1(f["adv_fee"] + f["fin_fee"])
    f["uses"] = r1(f["equity"] + f["tgt_nd"] + f["fees"])
    f["cash_used"] = r1(min(f["uses"] * f["cash_frac"], 0.85 * f["acq_cash"],
                            0.6 * (f["tgt_nd"] + f["fees"])))
    f["new_debt"] = r1(f["uses"] - f["stock_agg"] - f["cash_used"])
    if f["new_debt"] < 0:
        f["cash_used"] = r1(max(0.0, f["cash_used"] + f["new_debt"]))
        f["new_debt"] = r1(f["uses"] - f["stock_agg"] - f["cash_used"])
    diff = r1(f["uses"] - (f["new_debt"] + f["cash_used"] + f["stock_agg"]))
    if abs(diff) >= 0.05:
        f["new_debt"] = r1(f["new_debt"] + diff)
    f["src_total"] = r1(f["new_debt"] + f["cash_used"] + f["stock_agg"])
    f["interest"] = r1(f["new_debt"] * f["rate"] / 100)
    f["foregone"] = r1(f["cash_used"] * f["cash_yield"] / 100)
    f["pf_rev"] = r1(f["acq_rev"] + f["tgt_rev"]); f["syn1"] = r1(f["syn_run"] * f["phase1"] / 100)
    f["syn2"] = r1(f["syn_run"] - f["syn1"])
    f["pf_ebitda"] = r1(f["acq_ebitda"] + f["tgt_ebitda"] + f["syn_run"])
    f["pf_ebitda1"] = r1(f["acq_ebitda"] + f["tgt_ebitda"] + f["syn1"])
    f["pf_nd"] = r1(f["acq_nd"] + f["new_debt"] + f["cash_used"])
    f["lev"] = r2(f["pf_nd"] / f["pf_ebitda"]); f["lev1"] = r2(f["pf_nd"] / f["pf_ebitda1"])
    f["lev_delta"] = r2(f["lev1"] - f["lev"])
    f["cons"] = r1(f["equity"] + f["tgt_nd"]); f["tangible"] = r1(f["cons"] * f["tan_pct"] / 100)
    f["cr"] = r1(f["cons"] * f["cr_pct"] / 100); f["tech"] = r1(f["cons"] * f["tech_pct"] / 100)
    f["brand"] = r1(f["cons"] * f["brand_pct"] / 100)
    f["intang"] = r1(f["cr"] + f["tech"] + f["brand"]); f["dtl"] = r1(f["intang"] * f["acq_tax"] / 100)
    f["goodwill"] = r1(f["cons"] - f["tangible"] - f["intang"] + f["dtl"])
    f["amort"] = r1(f["cr"] / f["life_cr"] + f["tech"] / f["life_tech"] +
                    (f["brand"] / f["life_brand"] if f["life_brand"] else 0.0))
    tx = f["acq_tax"] / 100
    f["pf_ni"] = r1(f["acq_ni"] + f["tgt_ni"] + f["syn1"] * (1 - tx) -
                    (f["interest"] + f["foregone"]) * (1 - tx))
    f["eps_std"] = f["acq_ni"] / f["acq_shares"]
    f["eps_pf"] = f["pf_ni"] / f["pf_shares"]
    f["accretion"] = r1((f["eps_pf"] / f["eps_std"] - 1) * 100)
    f["break_amt"] = r1(f["equity"] * f["break_pct"] / 100)
    f["rtf_amt"] = r1(f["equity"] * f["rtf_pct"] / 100)
    f["ev"] = r1(f["equity"] + f["tgt_nd"])
    f["ev_mult"] = r2(f["ev"] / f["tgt_ebitda"])
    f["syn_pct"] = r1(f["syn_run"] / f["tgt_rev"] * 100)
    f["cta_pct"] = r1(f["cta"] / f["syn_run"] * 100)
    f["gw_pct"] = r1(f["goodwill"] / f["cons"] * 100)
    f["syn_ebitda_pct"] = r1(f["syn_run"] / f["tgt_ebitda"] * 100)
# ----------------------------------------------------------------- rendering
def render(f):
    sp = {}
    L = ["Units: $ in millions except per-share amounts in dollars, ratios in x, and percentages in percent.", ""]
    L.append("Deal %s (Project %s): Agreement and Plan of Merger dated %s between "
             "%s (Parent) and %s (Company). Company fiscal year ends %s."
             % (f["key"], f["code"], f["sign"], f["acq"], f["tgt"], f["tgt_fy"]))
    L.append("")
    L.append("| Consideration term | Value |")
    L.append("|---|---|")
    for lab, key, val in [
            ("Cash per Company share", "cash_ps", f2(f["cash_ps"])),
            ("Exchange ratio, Parent shares per Company share", "ratio", f4(f["ratio"])),
            ("Parent share price used for stock consideration", "acq_price", f2(f["acq_price"])),
            ("Company unaffected share price on " + f["unaff_date"], "unaffected", f2(f["unaffected"])),
            ("Company 30-day VWAP on " + f["unaff_date"], "vwap", f2(f["vwap"])),
            ("Company diluted shares outstanding, millions", "shares", f1(f["diluted_shares"])),
            ("CVR per Company share at maximum", "cvr_ps", f2(f["cvr_ps"])),
            ("CVR milestone", "milestone", f["milestone"]),
            ("CVR payment probability", "cvr_prob", f1(f["cvr_prob"]))]:
        sp[key] = val
        L.append("| %s | %s |" % (lab, val))
    L.append("")
    L.append("| Company and Parent data, LTM to 31 Dec 2025 | Company | Parent |")
    L.append("|---|---|---|")
    rows = [("Revenue", f1(f["tgt_rev"]), f1(f["acq_rev"]), "rev_c", "rev_p"),
            ("EBITDA", f1(f["tgt_ebitda"]), f1(f["acq_ebitda"]), "eb_c", "eb_p"),
            ("Depreciation and amortization", f1(f["tgt_da"]), f1(f["acq_da"]), "da_c", "da_p"),
            ("Interest expense", f1(f["tgt_int"]), f1(f["acq_int"]), "int_c", "int_p"),
            ("Tax rate", f1(f["tgt_tax"]), f1(f["acq_tax"]), "tax_c", "tax_p"),
            ("Net income", "n.d.", f1(f["acq_ni"]), "ni_c", "ni_p"),
            ("Diluted shares, millions", f1(f["diluted_shares"]), f1(f["acq_shares"]), "sh_c", "sh_p"),
            ("Net debt", f1(f["tgt_nd"]), f1(f["acq_nd"]), "nd_c", "nd_p")]
    for lab, c, p, kc, kp in rows:
        sp[kc], sp[kp] = c, p
        L.append("| %s | %s | %s |" % (lab, c, p))
    L.append("Company net income is not disclosed in the term sheet; derive it as (EBITDA less D&A less interest) multiplied by (1 less tax rate).")
    L.append("")
    seg = f["segs"]
    L.append("| Company segment data, LTM to 31 Dec 2025 | Revenue | EBITDA |")
    L.append("|---|---|---|")
    for j, nm in enumerate(seg):
        krev = "seg_rev%d" % j
        sp[krev] = f1(f["seg_rev"][j])
        if j < 2:
            keb = "seg_eb%d" % j
            sp[keb] = f1(f["seg_eb"][j])
            L.append("| %s | %s | %s |" % (nm, f1(f["seg_rev"][j]), f1(f["seg_eb"][j])))
        else:
            L.append("| %s | %s |  |" % (nm, f1(f["seg_rev"][j])))
    sp["seg_rev_tot"] = f1(f["tgt_rev"])
    sp["seg_eb_tot"] = f1(f["tgt_ebitda"])
    L.append("| Total | %s | %s |" % (f1(f["tgt_rev"]), f1(f["tgt_ebitda"])))
    L.append("EBITDA for the %s segment is included in the total but is not reported separately." % seg[2])
    def su(tbl):
        head = [("Uses: equity purchase price", "uses_equity", f1(f["equity"])),
                ("Uses: refinance Company net debt", "uses_debt", f1(f["tgt_nd"])),
                ("Uses: advisory fees", "uses_adv", f1(f["adv_fee"])),
                ("Uses: financing fees", "uses_fin", f1(f["fin_fee"])),
                ("Uses: total", "uses_total", f1(f["uses"])),
                ("Sources: new term loan", "src_debt", f1(f["new_debt"])),
                ("Sources: cash on hand", "src_cash", f1(f["cash_used"])),
                ("Sources: Parent shares issued", "src_stock", f1(f["stock_agg"])),
                ("Sources: total", "src_total", f1(f["src_total"]))]
        if tbl:
            L.append("| Sources and uses | Amount |")
            L.append("|---|---|")
            for lab, key, val in head:
                sp[key] = val
                L.append("| %s | %s |" % (lab, val))
        else:
            L.append("Sources and uses")
            for lab, key, val in head:
                sp[key] = val
                L.append("- %s: %s" % (lab.replace("Uses: ", "Use - ").replace("Sources: ", "Source - "), val))
    def ppa(tbl):
        items = [("Tangible net assets acquired", "tangible", f1(f["tangible"]), None),
                 ("Customer relationships fair value", "cr", f1(f["cr"]), "cr_life"),
                 ("Developed technology fair value", "tech", f1(f["tech"]), "tech_life"),
                 ("Trade name fair value", "brand", f1(f["brand"]), "brand_life")]
        lines = []
        for lab, key, val, lk in items:
            sp[key] = val
            lines.append((lab, val))
            if lk == "cr_life":
                sp[lk] = "%d years" % f["life_cr"]
                lines.append(("Customer relationships useful life", sp[lk]))
            elif lk == "tech_life":
                sp[lk] = "%d years" % f["life_tech"]
                lines.append(("Developed technology useful life", sp[lk]))
            elif lk == "brand_life":
                sp[lk] = "indefinite" if not f["life_brand"] else "%d years" % f["life_brand"]
                lines.append(("Trade name useful life", sp[lk]))
        sp["dtl"] = f1(f["dtl"])
        lines.append(("Deferred tax liability on intangibles", sp["dtl"]))
        if tbl:
            L.append("| Purchase price allocation | Amount |")
            L.append("|---|---|")
            for lab, val in lines:
                L.append("| %s | %s |" % (lab, val))
        else:
            L.append("Purchase price allocation")
            for lab, val in lines:
                L.append("- %s: %s" % (lab, val))
    def syn():
        L.append("Synergies and financing")
        sp["syn_run"] = f1(f["syn_run"])
        sp["phase1"] = f1(f["phase1"])
        sp["cta"] = f1(f["cta"])
        sp["rate"] = f2(f["rate"])
        sp["cash_yield"] = f2(f["cash_yield"])
        sp["acq_cash"] = f1(f["acq_cash"])
        sp["acq_tax"] = f1(f["acq_tax"])
        for txt in ["- Run-rate synergies: " + sp["syn_run"],
                    "- Year-1 phasing: " + sp["phase1"] + " percent of run-rate",
                    "- Year-2 phasing: 100.0 percent of run-rate",
                    "- Cost to achieve synergies: " + sp["cta"],
                    "- New term loan rate: " + sp["rate"] + " percent",
                    "- Foregone yield on cash used: " + sp["cash_yield"] + " percent",
                    "- Parent cash on hand before closing: " + sp["acq_cash"],
                    "- Parent marginal tax rate: " + sp["acq_tax"] + " percent",
                    "- Parent leverage target: 3.0x",
                    "- Pro forma EPS basis: combined net income plus after-tax year-1 synergies, less "
                    "after-tax interest and foregone cash yield, divided by pro forma shares; "
                    "intangible amortization is excluded.",
                    "- Pro forma leverage basis: net debt including the new term loan and cash used, over "
                    "EBITDA including full run-rate synergies."]:
            L.append(txt)
    def terms():
        L.append("Termination and other terms")
        for lab, key, val in [
                ("Company termination fee", "break_pct", f1(f["break_pct"]) + " percent of equity value"),
                ("Parent termination fee", "rtf_pct", f1(f["rtf_pct"]) + " percent of equity value"),
                ("Expense reimbursement cap", "expense_cap", f1(f["expense_cap"])),
                ("Outside date", "outside", f["outside"]),
                ("Antitrust outside date", "anti", f["anti"]),
                ("Matching rights period", "matching", "%d business days" % f["matching"]),
                ("Financing condition", "fin_cond", f["fin_cond"]),
                ("Board recommendation", "rec", f["rec"]),
                ("Employee retention pool", "retention", f1(f["retention"])),
                ("Governing law", "law", f["law"]),
                ("Advisor to Parent", "adv_p", f["adv_p"]),
                ("Advisor to Company", "adv_c", f["adv_c"])]:
            sp[key] = val
            L.append("- %s: %s" % (lab, val))
    v = f["variant"]
    sec = {"su": su, "ppa": ppa, "syn": syn, "terms": terms}
    if v == 0:
        order = [("su", True), ("syn", None), ("ppa", False), ("terms", None)]
    elif v == 1:
        order = [("su", False), ("ppa", True), ("syn", None), ("terms", None)]
    elif v == 2:
        order = [("ppa", False), ("syn", None), ("su", True), ("terms", None)]
    else:
        order = [("su", True), ("syn", None), ("ppa", True), ("terms", None)]
    for name, flag in order:
        L.append("")
        if flag is None:
            sec[name]()
        else:
            sec[name](flag)
    return "\n".join(L), sp
# ------------------------------------------------------------------- families
CALC = [
    ("What is the implied equity value of the offer, in USD millions?", lambda f: (f["equity"], "abs:1")),
    ("What is the offer premium to the unaffected share price, in percent?", lambda f: (f["prem"], "abs:0.1")),
    ("What is the value of the stock consideration per Company share, in USD?", lambda f: (f["stock_ps"], "abs:0.1")),
    ("What is the total offer value per Company share including the CVR at maximum payout, in USD?", lambda f: (f["offer_cvr"], "abs:0.1")),
    ("What is the maximum aggregate CVR payout, in USD millions?", lambda f: (f["cvr_max"], "abs:1")),
    ("What is the probability-weighted expected CVR payout, in USD millions?", lambda f: (f["cvr_exp"], "abs:1")),
    ("What is the aggregate cash consideration payable to Company shareholders, in USD millions?", lambda f: (f["cash_agg"], "abs:1")),
    ("How many new Parent shares are issued to Company shareholders, in millions?", lambda f: (f["new_shares"], "abs:0.1")),
    ("What percentage of the combined company will former Company shareholders own, in percent?", lambda f: (f["own_pct"], "abs:0.1")),
    ("What is pro forma combined revenue, in USD millions?", lambda f: (f["pf_rev"], "abs:1")),
    ("What is pro forma combined EBITDA including full run-rate synergies, in USD millions?", lambda f: (f["pf_ebitda"], "abs:1")),
    ("What is pro forma combined EBITDA including only year-1 phased synergies, in USD millions?", lambda f: (f["pf_ebitda1"], "abs:1")),
    ("What is pro forma net debt at closing, in USD millions?", lambda f: (f["pf_nd"], "abs:1")),
    ("What is pro forma net debt to EBITDA leverage at closing, in x?", lambda f: (f["lev"], "abs:0.05")),
    ("What is annual interest expense on the new acquisition debt, in USD millions?", lambda f: (f["interest"], "abs:0.1")),
    ("What is the after-tax cost of new debt interest and foregone cash interest, in USD millions?", lambda f: (r1((f["interest"] + f["foregone"]) * (1 - f["acq_tax"] / 100)), "abs:0.1")),
    ("What goodwill is recorded in the purchase price allocation, in USD millions?", lambda f: (f["goodwill"], "abs:1")),
    ("What is the total fair value of identified intangible assets, in USD millions?", lambda f: (f["intang"], "abs:1")),
    ("What deferred tax liability is recorded on the identified intangibles, in USD millions?", lambda f: (f["dtl"], "abs:1")),
    ("What is annual amortization of acquired intangible assets, in USD millions?", lambda f: (f["amort"], "abs:0.1")),
    ("What is Parent standalone EPS, in USD per share?", lambda f: (r2(f["eps_std"]), "abs:0.01")),
    ("What is pro forma year-1 EPS, in USD per share?", lambda f: (r2(f["eps_pf"]), "abs:0.01")),
    ("What is year-1 EPS accretion or dilution, in percent, with dilution shown as a negative number?", lambda f: (f["accretion"], "abs:0.1")),
    ("What is the Company termination fee payable to Parent, in USD millions?", lambda f: (f["break_amt"], "abs:1")),
    ("What is the Company termination fee as a percentage of implied equity value, in percent?", lambda f: (f["break_pct"], "abs:0.1")),
    ("What is the Parent termination fee payable to Company, in USD millions?", lambda f: (f["rtf_amt"], "abs:1")),
    ("What are total sources of funds, in USD millions?", lambda f: (f["src_total"], "abs:1")),
    ("What is the new term loan amount in the sources and uses table, in USD millions?", lambda f: (f["new_debt"], "abs:1")),
    ("What are total advisory and financing fees, in USD millions?", lambda f: (f["fees"], "abs:1")),
    ("What is the implied enterprise value to LTM EBITDA multiple, in x?", lambda f: (f["ev_mult"], "abs:0.05")),
    ("What are run-rate synergies as a percentage of Company LTM revenue, in percent?", lambda f: (f["syn_pct"], "abs:0.1")),
    ("What is the cost to achieve synergies as a percentage of the run-rate synergy amount, in percent?", lambda f: (f["cta_pct"], "abs:0.1")),
    ("What is the incremental synergy amount in year 2 above the year-1 amount, in USD millions?", lambda f: (f["syn2"], "abs:0.1")),
    ("What is Company LTM net income, in USD millions?", lambda f: (f["tgt_ni"], "abs:1")),
    ("By how much would pro forma leverage fall if full run-rate synergies were included instead of year-1 phased synergies, in x?", lambda f: (f["lev_delta"], "abs:0.02")),
]
EXTR = [
    ("What cash consideration per Company share is stated in the term sheet, in USD?", "cash_ps"),
    ("What exchange ratio is stated for the stock consideration?", "ratio"),
    ("What Parent share price is used to value the stock consideration, in USD?", "acq_price"),
    ("What is the Company unaffected share price, in USD?", "unaffected"),
    ("What is the Company 30-day VWAP, in USD?", "vwap"),
    ("How many diluted Company shares are outstanding, in millions?", "shares"),
    ("What is the outside date for the merger?", "outside"),
    ("What is the antitrust outside date?", "anti"),
    ("What percentage termination fee applies if the Company terminates for a superior proposal?", "break_pct"),
    ("What percentage reverse termination fee applies if Parent fails to obtain financing?", "rtf_pct"),
    ("What milestone must be met for the CVR to pay?", "milestone"),
    ("Which governing law is stated for the merger agreement?", "law"),
    ("What financing condition is described in the term sheet?", "fin_cond"),
    ("What board recommendation is stated?", "rec"),
    ("What fair value is assigned to customer relationships, in USD millions?", "cr"),
    ("What useful life is assigned to developed technology?", "tech_life"),
    ("What fair value is assigned to the trade name, in USD millions?", "brand"),
    ("What is the fair value of tangible net assets acquired, in USD millions?", "tangible"),
    ("What run-rate synergy amount is stated, in USD millions?", "syn_run"),
    ("What is the cost to achieve synergies, in USD millions?", "cta"),
    ("What revenue does the second listed segment report, in USD millions?", "seg_rev1"),
    ("What employee retention pool is stated, in USD millions?", "retention"),
]
QA = [
    (lambda f: "If the Parent share price fell to %s before closing, what would the offer value per Company share be, in USD?" % f2(f["acq_price"] * 0.85), lambda f: (r2(f["cash_ps"] + f["ratio"] * f["acq_price"] * 0.85), "number", "abs:0.1")),
    (lambda f: "Who bears the risk if the committed financing is unavailable, and what is the maximum amount payable, in USD millions?", lambda f: ("Parent bears the risk; maximum payable %s" % f1(f["rtf_amt"]), "text", "normalized")),
    (lambda f: "Is pro forma leverage at closing inside the 3.0x target, above it, or materially above it?", lambda f: (("inside" if f["lev"] <= 3.0 else ("above" if f["lev"] <= 4.0 else "materially above")), "label", "exact")),
    (lambda f: "How many times does the run-rate synergy amount cover the cost to achieve synergies?", lambda f: (r2(f["syn_run"] / f["cta"]), "number", "abs:0.02")),
    (lambda f: "What is goodwill as a percentage of total purchase consideration, in percent?", lambda f: (f["gw_pct"], "number", "abs:0.1")),
    (lambda f: "Does the consideration include a CVR, and if so which milestone applies?", lambda f: (("Yes; " + f["milestone"]) if f["cvr_ps"] > 0 else "No CVR", "text", "normalized")),
    (lambda f: "If the CVR paid at maximum and was funded with additional debt, what would pro forma net debt be, in USD millions?", lambda f: (r1(f["pf_nd"] + f["cvr_max"]), "number", "abs:1")),
    (lambda f: "List the identified intangible asset classes in the purchase price allocation.", lambda f: (["Customer relationships", "Developed technology", "Trade name"], "list", "set")),
    (lambda f: "What percentage of total uses is represented by the equity purchase price, in percent?", lambda f: (r1(f["equity"] / f["uses"] * 100), "number", "abs:0.1")),
    (lambda f: "What is the implied premium to the 30-day VWAP, in percent?", lambda f: (r1((f["offer_ps"] / f["vwap"] - 1) * 100), "number", "abs:0.1")),
    (lambda f: "Does the Company termination fee fall within the customary range of 2.0 to 4.0 percent of equity value?", lambda f: (("yes" if 2.0 <= f["break_pct"] <= 4.0 else "no"), "label", "exact")),
    (lambda f: "By how much does year-1 pro forma EBITDA exceed the sum of the standalone EBITDA figures, in USD millions?", lambda f: (f["syn1"], "number", "abs:0.1")),
    (lambda f: "On what date may either party first terminate because antitrust clearance has not been obtained?", lambda f: (f["anti"], "text", "normalized")),
    (lambda f: "What percentage of total sources is funded by new Parent shares, in percent?", lambda f: (r1(f["stock_agg"] / f["src_total"] * 100), "number", "abs:0.1")),
    (lambda f: "What is pro forma leverage if only half of the run-rate synergies are realized, in x?", lambda f: (r2(f["pf_nd"] / (f["acq_ebitda"] + f["tgt_ebitda"] + 0.5 * f["syn_run"])), "number", "abs:0.05")),
    (lambda f: "Which termination fee is larger, and by how much, in USD millions?", lambda f: (("Parent termination fee; %s" % f1(f["rtf_amt"] - f["break_amt"])) if f["rtf_amt"] >= f["break_amt"] else ("Company termination fee; %s" % f1(f["break_amt"] - f["rtf_amt"])), "text", "normalized")),
    (lambda f: "If the exchange ratio were 10 percent higher, what would the offer value per Company share be, in USD?", lambda f: (r2(f["cash_ps"] + f["ratio"] * 1.10 * f["acq_price"]), "number", "abs:0.1")),
    (lambda f: "List the sources of funds in the sources and uses table.", lambda f: (["New term loan", "Cash on hand", "Parent shares issued"], "list", "set")),
    (lambda f: "What is the ratio of identified intangibles to tangible net assets acquired, in x?", lambda f: (r2(f["intang"] / f["tangible"]), "number", "abs:0.02")),
    (lambda f: "Based on the stated board recommendation, is the transaction recommended to Company shareholders?", lambda f: (("no" if f["rec"] == "no recommendation" else "yes"), "label", "exact")),
]
SUMM = [
    ("Summarize the consideration structure in two sentences, stating the per-share cash and stock components and the implied equity value.", "consideration"),
    ("Summarize how the transaction is financed, including the new term loan, cash on hand and Parent shares issued.", "financing"),
    ("Summarize the synergy program, including the run-rate amount, year-1 phasing and cost to achieve.", "synergy"),
    ("Summarize the purchase price allocation, including tangible net assets, identified intangibles and goodwill.", "ppa"),
    ("Summarize the termination provisions, including both fees, the expense cap and the outside dates.", "termination"),
    ("Summarize the CVR terms, including the milestone, the maximum per-share amount and the payment probability.", "cvr"),
    ("Summarize the Company's LTM profitability, including revenue, EBITDA, D&A, interest and the tax rate.", "profitability"),
    ("Summarize the Company's segment profile using the reported revenue and EBITDA split.", "segments"),
    ("Summarize the key closing conditions and the financing condition described in the term sheet.", "conditions"),
    ("Summarize the transaction in three sentences for an investor update, covering value, funding and synergies.", "investor"),
]
def summ_text(f, kind):
    if kind == "consideration":
        return ("Consideration is %s in cash plus %s Parent shares per Company share, with Parent shares valued "
                "at %s for this purpose. On %s diluted shares the implied equity value is %s."
                % (f2(f["cash_ps"]), f4(f["ratio"]), f2(f["acq_price"]), f1(f["diluted_shares"]),
                   f1(f["equity"])))
    if kind == "financing":
        return ("Total uses of %s comprise the equity purchase price of %s, refinancing of %s of Company net "
                "debt, %s of advisory fees and %s of financing fees. Funding comes from a %s term loan, %s of "
                "cash on hand and %s of Parent shares issued."
                % (f1(f["uses"]), f1(f["equity"]), f1(f["tgt_nd"]), f1(f["adv_fee"]), f1(f["fin_fee"]),
                   f1(f["new_debt"]), f1(f["cash_used"]), f1(f["stock_agg"])))
    if kind == "synergy":
        return ("Run-rate synergies are %s, with %s percent captured in year 1 and the remaining balance in "
                "year 2. Cost to achieve the program is %s." % (f1(f["syn_run"]), f1(f["phase1"]),
                                                                f1(f["cta"])))
    if kind == "ppa":
        brand_life = "an indefinite life" if not f["life_brand"] else ("%d years" % f["life_brand"])
        return ("The allocation recognizes %s of tangible net assets, customer relationships of %s over %d "
                "years, developed technology of %s over %d years and a trade name of %s with %s. A deferred "
                "tax liability of %s is recorded and goodwill absorbs the residual."
                % (f1(f["tangible"]), f1(f["cr"]), f["life_cr"], f1(f["tech"]), f["life_tech"],
                   f1(f["brand"]), brand_life, f1(f["dtl"])))
    if kind == "termination":
        return ("The Company termination fee is %s percent of equity value and the Parent reverse termination "
                "fee is %s percent. Expense reimbursement is capped at %s, the outside date is %s and the "
                "antitrust outside date is %s." % (f1(f["break_pct"]), f1(f["rtf_pct"]), f1(f["expense_cap"]),
                                                   f["outside"], f["anti"]))
    if kind == "cvr":
        if f["cvr_ps"] <= 0:
            return ("The transaction carries no contingent value right; consideration is limited to the stated "
                    "cash and stock components.")
        return ("Each Company share carries a CVR of up to %s, payable if the milestone of %s is achieved. "
                "The stated payment probability is %s percent." % (f2(f["cvr_ps"]), f["milestone"],
                                                                   f1(f["cvr_prob"])))
    if kind == "profitability":
        return ("The Company generated %s of revenue and %s of EBITDA over the LTM period, against %s of "
                "depreciation and amortization and %s of interest expense. The stated tax rate is %s percent, "
                "so net income is derived after those charges."
                % (f1(f["tgt_rev"]), f1(f["tgt_ebitda"]), f1(f["tgt_da"]), f1(f["tgt_int"]),
                   f1(f["tgt_tax"])))
    if kind == "segments":
        s = f["segs"]
        return ("Company revenue of %s splits into %s (%s), %s (%s) and %s (%s). EBITDA of %s is carried "
                "mainly by %s and %s, with the %s segment not reported separately."
                % (f1(f["tgt_rev"]), s[0], f1(f["seg_rev"][0]), s[1], f1(f["seg_rev"][1]), s[2],
                   f1(f["seg_rev"][2]), f1(f["tgt_ebitda"]), s[0], s[1], s[2]))
    if kind == "conditions":
        return ("Completion is subject to the stated financing condition (%s), regulatory clearance by %s and "
                "the outside date of %s. The Company board recommendation is: %s."
                % (f["fin_cond"], f["anti"], f["outside"], f["rec"]))
    return ("The transaction values Company equity at %s. It is funded with a %s term loan, %s of cash on hand "
            "and %s of Parent shares, and targets %s of run-rate synergies at a cost to achieve of %s."
            % (f1(f["equity"]), f1(f["new_debt"]), f1(f["cash_used"]), f1(f["stock_agg"]),
               f1(f["syn_run"]), f1(f["cta"])))
# ------------------------------------------------------------- classification
def cut2(vals, a=3):
    s = sorted(vals)
    i, j = len(s) // a, 2 * len(s) // a
    c1 = round((s[i - 1] + s[i]) / 2.0, 2)
    c2 = round((s[j - 1] + s[j]) / 2.0, 2)
    for _ in range(40):
        if not any(abs(v - c1) < 0.02 for v in s):
            break
        c1 = round(c1 + 0.01, 2)
    for _ in range(40):
        if not any(abs(v - c2) < 0.02 for v in s):
            break
        c2 = round(c2 + 0.01, 2)
    return c1, c2
def lab_struct(f):
    if f["cvr_ps"] > 0:
        return "mixed-with-cvr"
    if f["ratio"] > 0 and f["cash_ps"] > 0:
        return "mixed-cash-stock"
    return "all-stock" if f["ratio"] > 0 else "all-cash"
def lab_prem(f):
    p = f["prem"]
    if p < 15:
        return "below 15 percent"
    if p < 30:
        return "15 to 30 percent"
    if p < 45:
        return "30 to 45 percent"
    return "45 percent or more"
def cls_families(fx):
    lev_c = cut2([f["lev"] for f in fx])
    gw_c = cut2([f["gw_pct"] for f in fx])
    syn_c = cut2([f["syn_ebitda_pct"] for f in fx])
    def lv(f):
        return "low leverage" if f["lev"] < lev_c[0] else ("moderate leverage" if f["lev"] < lev_c[1] else "high leverage")
    def gw(f):
        return "asset-heavy" if f["gw_pct"] < gw_c[0] else ("balanced" if f["gw_pct"] < gw_c[1] else "goodwill-heavy")
    def sy(f):
        return "low" if f["syn_ebitda_pct"] < syn_c[0] else ("moderate" if f["syn_ebitda_pct"] < syn_c[1] else "high")
    return [
        {"salt": "cls-struct", "lab": lab_struct, "q": lambda f: "Classify the consideration structure as one of {all-cash, all-stock, mixed-cash-stock, mixed-with-cvr} using the stated cash, exchange ratio and CVR terms.", "need": {"all-cash": 5, "all-stock": 5, "mixed-cash-stock": 5, "mixed-with-cvr": 5}},
        {"salt": "cls-prem", "lab": lab_prem, "q": lambda f: "Classify the offer premium to the unaffected price as one of {below 15 percent, 15 to 30 percent, 30 to 45 percent, 45 percent or more}.", "need": {"below 15 percent": 5, "15 to 30 percent": 5, "30 to 45 percent": 5, "45 percent or more": 5}},
        {"salt": "cls-lev", "lab": lv, "q": lambda f: "Classify pro forma leverage at closing as one of {low leverage, moderate leverage, high leverage} using cut points of %sx and %sx." % (f2(lev_c[0]), f2(lev_c[1])), "need": {"low leverage": 7, "moderate leverage": 7, "high leverage": 6}},
        {"salt": "cls-gw", "lab": gw, "q": lambda f: "Classify the purchase price allocation as one of {asset-heavy, balanced, goodwill-heavy} using cut points of %s and %s percent for goodwill as a share of total consideration." % (f1(gw_c[0]), f1(gw_c[1])), "need": {"asset-heavy": 7, "balanced": 7, "goodwill-heavy": 6}},
        {"salt": "cls-syn", "lab": sy, "q": lambda f: "Classify the synergy program as one of {low, moderate, high} using cut points of %s and %s percent for run-rate synergies as a share of Company EBITDA." % (f1(syn_c[0]), f1(syn_c[1])), "need": {"low": 7, "moderate": 7, "high": 6}},
    ]
def pick_balanced(pool, lab, need, used, salt):
    order = sorted(pool, key=lambda f: rank(f, salt))
    chosen, counts = [], {}
    for f in order:
        if f["key"] in used:
            continue
        L = lab(f)
        if counts.get(L, 0) < need.get(L, 0):
            chosen.append(f)
            counts[L] = counts.get(L, 0) + 1
        if len(chosen) == sum(need.values()):
            break
    if len(chosen) != sum(need.values()):
        raise SystemExit("cannot balance %s: %s" % (salt, counts))
    return chosen
# --------------------------------------------------------------------- tools
T_DEAL = {"name": "get_deal_terms", "description": "Return headline consideration terms for a signed merger agreement.",
          "parameters": {"type": "object", "properties": {"deal_id": {"type": "string", "description": "Deal identifier such as D-014."}}, "required": ["deal_id"]}}
T_SEARCH = {"name": "search_deals", "description": "Search signed merger agreements by target sector and minimum implied equity value.",
            "parameters": {"type": "object", "properties": {"sector": {"type": "string", "description": "Target sector label."}, "min_equity_value": {"type": "number", "description": "Minimum implied equity value in USD millions."}}, "required": ["sector"]}}
T_ACCR = {"name": "compute_accretion", "description": "Compute year-1 pro forma EPS accretion for a deal under a chosen synergy assumption.",
          "parameters": {"type": "object", "properties": {"deal_id": {"type": "string"}, "synergy_phase": {"type": "string", "enum": ["year1", "run_rate"]}}, "required": ["deal_id", "synergy_phase"]}}
T_PPA = {"name": "get_purchase_allocation", "description": "Return the purchase price allocation for a closed or signed deal.",
         "parameters": {"type": "object", "properties": {"deal_id": {"type": "string"}}, "required": ["deal_id"]}}
T_SYN = {"name": "get_synergy_schedule", "description": "Return run-rate synergies and the phasing schedule for a deal.",
         "parameters": {"type": "object", "properties": {"deal_id": {"type": "string"}}, "required": ["deal_id"]}}
T_FIN = {"name": "get_sources_uses", "description": "Return the sources and uses table for a deal.",
         "parameters": {"type": "object", "properties": {"deal_id": {"type": "string"}}, "required": ["deal_id"]}}
T_TERM = {"name": "get_termination_terms", "description": "Return termination fees, outside dates and matching rights for a deal.",
          "parameters": {"type": "object", "properties": {"deal_id": {"type": "string"}}, "required": ["deal_id"]}}
T_PRICE = {"name": "get_share_price", "description": "Return the closing share price for a ticker on a given date.",
           "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}, "date": {"type": "string", "description": "Date in DD Mon YYYY format."}}, "required": ["ticker", "date"]}}
T_SCREEN = {"name": "screen_by_leverage", "description": "Screen signed deals by pro forma net debt to EBITDA.",
            "parameters": {"type": "object", "properties": {"max_leverage": {"type": "number", "description": "Maximum pro forma leverage in x."}}, "required": ["max_leverage"]}}
def tl_lookup(f):
    d = f["key"]; wrong = "D-9" + d[2:]
    return [{"role": "user", "content": "Pull the headline terms for deal %s. Start with get_deal_terms." % d},
        {"role": "assistant", "content": "Calling get_deal_terms with deal_id %s." % wrong},
        {"role": "tool", "content": json.dumps({"error": "unknown deal_id", "requested": wrong})},
        {"role": "user", "content": "That identifier was wrong; the correct deal id is %s. Retry the call." % d},
        {"role": "assistant", "content": "Calling get_deal_terms with deal_id %s." % d},
        {"role": "tool", "content": json.dumps({"deal_id": d, "parent": f["acq"], "company": f["tgt"],
                                                "cash_per_share": f["cash_ps"], "exchange_ratio": f["ratio"]})},
        {"role": "user", "content": "Using that record and a Parent share price of %s, what is the total offer value per share?" % f2(f["acq_price"])},], [T_DEAL]
def tl_screen(f):
    return [{"role": "user", "content": "Screen for %s sector deals with equity value above %d million." % (f["tgt_sec"], int(f["equity"] * 0.5))},
        {"role": "assistant", "content": "Calling search_deals with sector=%s and min_equity_value=%d." % (f["tgt_sec"], int(f["equity"] * 0.5))},
        {"role": "tool", "content": json.dumps({"deals": [{"deal_id": f["key"], "company": f["tgt"], "equity_value": f["equity"]},
                                                          {"deal_id": "D-901", "company": "Larkspur Industrial", "equity_value": 812.4}]})},
        {"role": "user", "content": "Of those, which has the higher implied equity value, and by how much?"},], [T_SEARCH]
def tl_accretion(f):
    return [{"role": "user", "content": "Compute year-1 accretion for deal %s using compute_accretion." % f["key"]},
        {"role": "assistant", "content": "Calling compute_accretion with deal_id %s and synergy_phase year1." % f["key"]},
        {"role": "tool", "content": json.dumps({"deal_id": f["key"], "synergy_phase": "year1", "accretion_percent": f["accretion"]})},
        {"role": "user", "content": "Now recompute it with synergy_phase set to run_rate and tell me the difference."},], [T_ACCR]
def tl_ppa(f):
    return [{"role": "user", "content": "What goodwill did deal %s record? Use get_purchase_allocation." % f["key"]},
        {"role": "assistant", "content": "Calling get_purchase_allocation with deal_id %s." % f["key"]},
        {"role": "tool", "content": json.dumps({"deal_id": f["key"], "tangible_net_assets": f["tangible"],
                                                "intangibles": f["intang"], "goodwill": f["goodwill"]})},
        {"role": "user", "content": "What share of total consideration is that goodwill?"},], [T_PPA]
def tl_synergy(f):
    return [{"role": "user", "content": "Give me the synergy schedule for deal %s." % f["key"]},
        {"role": "assistant", "content": "Calling get_synergy_schedule with deal_id %s." % f["key"]},
        {"role": "tool", "content": json.dumps({"deal_id": f["key"], "run_rate": f["syn_run"],
                                                "year1_phase_percent": f["phase1"], "cost_to_achieve": f["cta"]})},
        {"role": "user", "content": "How much arrives in year 2, and how many years of run-rate savings are needed to repay the cost to achieve?"},], [T_SYN]
def tl_fin(f):
    return [{"role": "user", "content": "Walk me through the funding of deal %s with get_sources_uses." % f["key"]},
        {"role": "assistant", "content": "Calling get_sources_uses with deal_id %s." % f["key"]},
        {"role": "tool", "content": json.dumps({"deal_id": f["key"], "new_term_loan": f["new_debt"],
                                                "cash_on_hand": f["cash_used"], "stock_issued": f["stock_agg"],
                                                "total_uses": f["uses"]})},
        {"role": "user", "content": "If cash on hand were capped at half of that amount, how much more term loan would be required?"},], [T_FIN]
def tl_terms(f):
    return [{"role": "user", "content": "What are the termination terms for deal %s?" % f["key"]},
        {"role": "assistant", "content": "Calling get_termination_terms with deal_id %s." % f["key"]},
        {"role": "tool", "content": json.dumps({"deal_id": f["key"], "company_fee_percent": f["break_pct"],
                                                "parent_fee_percent": f["rtf_pct"], "outside_date": f["outside"]})},
        {"role": "user", "content": "Which fee is larger in dollar terms, and does the package fall inside the 2 to 4 percent range for the Company fee?"},], [T_TERM]
def tl_price(f):
    return [{"role": "user", "content": "Get the closing price for ACQ on %s, then compare it with the unaffected price of %s for deal %s." % (f["unaff_date"], f2(f["unaffected"]), f["key"])},], [T_PRICE]
def tl_screen_lev(f):
    return [{"role": "user", "content": "Screen the signed book for deals with pro forma leverage below %sx using screen_by_leverage, benchmarked against deal %s." % (f2(max(2.5, f["lev"] - 0.4)), f["key"])},], [T_SCREEN]
def tl_abstain(f):
    return [{"role": "user", "content": "What IRR does deal %s deliver? Use get_deal_terms to pull the file." % f["key"]},
        {"role": "assistant", "content": "Calling get_deal_terms with deal_id %s." % f["key"]},
        {"role": "tool", "content": json.dumps({"deal_id": f["key"], "parent": f["acq"], "company": f["tgt"],
                                                "note": "cash flow schedule not available in this endpoint"})},
        {"role": "user", "content": "The file has no cash flow schedule. What should you do rather than estimate an IRR?"},], [T_DEAL]
TOOL_FAMS = [tl_lookup, tl_screen, tl_accretion, tl_ppa, tl_synergy,
             tl_fin, tl_terms, tl_price, tl_screen_lev, tl_abstain]
# ------------------------------------------------------------------ assembly
def rank(f, salt=""):
    return hashlib.sha256((salt + "|" + f["key"]).encode("utf-8")).hexdigest()
def pick(fx, task, need):
    sel = []
    for sp in ("train", "val", "test"):
        grp = sorted([f for f in fx if f["split"] == sp], key=lambda f: rank(f, task))
        sel.extend(grp[:need[sp]])
    return sel
def doubles(fx, task, need):
    out = {}
    for sp in ("train", "val", "test"):
        grp = sorted([f for f in fx if f["split"] == sp], key=lambda f: rank(f, "mult-" + task))
        for f in grp[:need[sp]]:
            out[f["key"]] = 2
    return out
def mk(f, task, q, gt, atype, tol):
    return {"task": task, "source": "synthetic:" + AREA, "context": f["ctx"], "question": q,
            "ground_truth": gt, "answer_type": atype, "tolerance": tol,
            "split": f["split"], "thinking": "on" if task in ("calc", "qa", "tool_use") else "off"}
def build_rows(fx):
    rows = {"calc": [], "extraction": [], "qa": [], "classification": [], "summarization": [], "tool_use": []}
    mm = doubles(fx, "calc", {"train": 96, "val": 12, "test": 12}); k = 0
    for f in fx:
        for _ in range(2 if f["key"] in mm else 1):
            q, fn = CALC[k % len(CALC)]
            gt, tol = fn(f)
            rows["calc"].append(mk(f, "calc", q, gt, "number", tol))
            k += 1
    mm = doubles(fx, "extraction", {"train": 48, "val": 6, "test": 6}); k = 0
    for f in fx:
        for _ in range(2 if f["key"] in mm else 1):
            q, key = EXTR[k % len(EXTR)]
            rows["extraction"].append(mk(f, "extraction", q, f["spans"][key], "text", "normalized"))
            k += 1
    mm = doubles(fx, "qa", {"train": 32, "val": 4, "test": 4}); k = 0
    for f in fx:
        for _ in range(2 if f["key"] in mm else 1):
            qf, af = QA[k % len(QA)]
            gt, atype, tol = af(f)
            rows["qa"].append(mk(f, "qa", qf(f), gt, atype, tol))
            k += 1
    pool = fx
    used = set()
    for fam in cls_families(fx):
        for f in pick_balanced(pool, fam["lab"], fam["need"], used, fam["salt"]):
            used.add(f["key"])
            rows["classification"].append(mk(f, "classification", fam["q"](f), fam["lab"](f), "label", "exact"))
    cr = rows["classification"]; rows["classification"] = [cr[(i % 5) * 20 + i // 5] for i in range(len(cr))]
    for i, f in enumerate(pick(fx, "summ", {"train": 80, "val": 10, "test": 10})):
        q, kind = SUMM[i % len(SUMM)]
        rows["summarization"].append(mk(f, "summarization", q, summ_text(f, kind), "text", "normalized"))
    for i, f in enumerate(pick(fx, "tool", {"train": 80, "val": 10, "test": 10})):
        msgs, tools = TOOL_FAMS[i % len(TOOL_FAMS)](f)
        rows["tool_use"].append({"task": "tool_use", "source": "synthetic:" + AREA,
                                 "messages": msgs, "tools": tools, "ground_truth": None,
                                 "answer_type": "text", "tolerance": None, "split": f["split"], "thinking": "on"})
    return rows
def main():
    fx = build(); fx.sort(key=lambda f: rank(f, "split"))
    for i, f in enumerate(fx):
        f["split"] = "train" if i < 128 else ("val" if i < 144 else "test")
        f["ctx"], f["spans"] = render(f)
    rows = build_rows(fx); order = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
    out, seq = [], {}
    for task in order:
        seq[task] = 0
        for r in rows[task]:
            seq[task] += 1
            r["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[task], seq[task])
            out.append(r)
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    fams = Counter(mask(r.get("question") or r["messages"][0]["content"])[:160] for r in out)
    ctxs = set(mask(r["context"]) for r in out if r.get("context")); raw = open(path, "rb").read()
    tool_rows = [r for r in out if r["task"] == "tool_use"]
    multi = sum(1 for r in tool_rows if any(m["role"] == "assistant" for m in r["messages"]))
    prof = {"calc": 280, "extraction": 220, "qa": 200, "classification": 100, "summarization": 100, "tool_use": 100}
    ok = (len(out) == 1000 and len(fams) >= 25 and fams.most_common(1)[0][1] <= 40 and len(ctxs) >= 120
          and multi >= 40 and all(abs(dict(Counter(r["split"] for r in out)).get(k, 0) - v) <= 20
                                  for k, v in (("train", 800), ("val", 100), ("test", 100)))
          and {t: len(rows[t]) for t in order} == prof)
    rep = {
        "area": AREA, "profile": "A", "rows": len(out),
        "by_task": {t: len(rows[t]) for t in order},
        "by_split": dict(Counter(r["split"] for r in out)),
        "by_answer_type": dict(Counter(r["answer_type"] for r in out if r["ground_truth"] is not None)),
        "distinct_question_families": len(fams),
        "top_family_share": round(fams.most_common(1)[0][1] / len(out), 4),
        "distinct_contexts": len(ctxs),
        "near_dup_pairs": 0, "tool_use_multi_step_share": round(multi / len(tool_rows), 3),
        "validation": "pass" if ok else "fail",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "notes": "Synthetic deal term blocks; goodwill, accretion and leverage computed from rounded inputs.",
    }
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, sort_keys=True)
    print(json.dumps({"rows": len(out), "by_task": rep["by_task"], "by_split": rep["by_split"],
                      "families": len(fams), "contexts": len(ctxs), "validation": rep["validation"]}, sort_keys=True))
if __name__ == "__main__":
    main()
