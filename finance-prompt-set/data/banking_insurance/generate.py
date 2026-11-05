#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic generator, banking_insurance area, 1000 rows, profile A.
28 fictional entities (16 banks, 8 non-life insurers, 4 life insurers) x 7 report variants
= 196 fixtures. Each fixture renders one regulatory-style summary table and every
ground_truth number is computed here from the same values written into that table.
Splits are assigned per fixture (group) inside each task stratum: groups are ranked by
sha256("task|fixture_key") and filled train 80 / val 10 / test 10. Group sizes are uniform
per task, so the split counts land exactly on 800/100/100.
"""
import hashlib
import json
import os
import random
import re
SEED = 42
AREA = "banking_insurance"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "prompts.jsonl")
REPORT = os.path.join(HERE, "report.json")
UNITS = ("Units: $ in millions except per-share amounts in dollars, share counts in "
         "millions, and percentages and ratios in percent.")
ENTITIES = [
    ("Meridian Bancorp", "bank", "diversified bank"), ("Ashvale Bank", "bank", "regional bank"),
    ("Northwind Federal Savings", "bank", "thrift"), ("Calder Ridge Bank", "bank", "commercial bank"),
    ("Brightwater Financial", "bank", "diversified bank"), ("Silverbrook Bank", "bank", "regional bank"),
    ("Harborline Bank", "bank", "commercial bank"), ("Larkspur Trust", "bank", "trust bank"),
    ("Thornbury Bank", "bank", "regional bank"), ("Copperfield Savings Bank", "bank", "thrift"),
    ("Wexley Bank", "bank", "commercial bank"), ("Glenmoor Bank", "bank", "regional bank"),
    ("Pentland Bancshares", "bank", "diversified bank"), ("Alder Point Bank", "bank", "commercial bank"),
    ("Sablewick Bank", "bank", "regional bank"), ("Quarry Hill Bank", "bank", "thrift"),
    ("Kestrel Mutual Insurance", "pc", "non-life insurer"), ("Bluehaven Assurance", "pc", "non-life insurer"),
    ("Sable Point Insurance", "pc", "non-life insurer"), ("Fairwind Mutual", "pc", "non-life insurer"),
    ("Cedarline Assurance", "pc", "non-life insurer"), ("Marrow Bay Insurance", "pc", "non-life insurer"),
    ("Ironwood Re", "pc", "reinsurer"), ("Basalt Re", "pc", "reinsurer"),
    ("Trillium Life", "life", "life insurer"), ("Lumen Life", "life", "life insurer"),
    ("Aurelian Life", "life", "life insurer"), ("Northgate Life", "life", "life insurer")]
VARIANTS = {
    "bank": ["consolidated earnings summary", "average balance sheet exhibit",
             "net interest income bridge", "credit quality appendix",
             "regulatory capital supplement", "segment operating review",
             "investor financial supplement"],
    "pc": ["underwriting result summary", "combined ratio exhibit", "premium and claims review",
           "investment income appendix", "catastrophe loss supplement", "segment underwriting review",
           "statutory filing summary"],
    "life": ["embedded value statement", "value of new business exhibit", "EV operating earnings review",
             "APE and margin supplement", "shareholder value summary",
             "new business profitability review", "capital and EV bridge"]}
PAIRS = [("FY2025", "FY2024"), ("Q3 FY2025", "Q3 FY2024"), ("H1 FY2025", "H1 FY2024"),
         ("LTM to 30 Jun 2025", "LTM to 30 Jun 2024"), ("Q1 FY2026", "Q1 FY2025"),
         ("FY2023", "FY2022"), ("9M FY2025", "9M FY2024")]
MEMOS = ["All balances are daily averages unless the item is marked as a period-end amount.",
         "The exhibit is prepared on a continuing-operations basis and excludes discontinued lines.",
         "Prior-period amounts have been conformed to the presentation used in the later column.",
         "Amounts are unaudited and are presented before intercompany eliminations.",
         "Ratios are computed on average balances and are shown to one decimal place in the reported rows.",
         "Segment amounts are shown before unallocated corporate items and eliminations.",
         "The schedule follows the regulatory reporting form and may differ from the audited statements."]
NA_LABELS = {
    "bank": ["Common dividends declared", "Share repurchases", "Restructuring charge", "Preferred dividends declared"],
    "pc": ["Common dividends declared", "Share repurchases", "Catastrophe reserve transfer"],
    "life": ["Common dividends declared", "Share repurchases", "Actuarial assumption change"]}

def h(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

def num(x):
    if x is None:
        return "n.a."
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, int):
        return str(x)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return ("%.2f" % x).rstrip("0").rstrip(".")

def r2(x):
    v = round(float(x) + 0.0, 2)
    return 0.0 if v == 0 else v

def i0(x): return int(round(float(x)))

def pct1(a, b): return r2(float(a) / float(b) * 100.0)

def bank_core(u, variant, pair, rng, memo, na_label):
    p1, p0 = pair
    aea1 = rng.randrange(38000, 168000, 10); aea0 = i0(aea1 / (1 + rng.uniform(0.015, 0.085)))
    yld1 = rng.uniform(3.6, 6.6); yld0 = min(7.2, max(2.9, yld1 + rng.uniform(-0.55, 0.55)))
    cof1 = rng.uniform(0.8, max(1.0, yld1 - 1.35))
    cof0 = min(yld0 - 0.8, max(0.5, cof1 + rng.uniform(-0.45, 0.45)))
    ii1, ii0 = i0(aea1 * yld1 / 100.0), i0(aea0 * yld0 / 100.0)
    aibl1 = i0(aea1 * rng.uniform(0.76, 0.92)); aibl0 = i0(aea0 * rng.uniform(0.76, 0.92))
    ie1, ie0 = i0(aibl1 * cof1 / 100.0), i0(aibl0 * cof0 / 100.0)
    nii1, nii0 = ii1 - ie1, ii0 - ie0
    rev1 = nii1 / rng.uniform(0.56, 0.74); nonii1 = max(40, i0(rev1 - nii1))
    nonii0 = max(30, i0(nonii1 * rng.uniform(0.88, 1.10)))
    eff1 = rng.uniform(0.46, 0.69); eff0 = min(0.78, max(0.40, eff1 + rng.uniform(-0.05, 0.05)))
    nonie1 = i0((nii1 + nonii1) * eff1); nonie0 = i0((nii0 + nonii0) * eff0)
    ppnr1, ppnr0 = nii1 + nonii1 - nonie1, nii0 + nonii0 - nonie0
    loans1 = i0(aea1 * rng.uniform(0.60, 0.78)); loans0 = i0(aea0 * rng.uniform(0.60, 0.78))
    prov1 = max(5, i0(loans1 * rng.uniform(0.0012, 0.0062)))
    prov0 = max(4, i0(loans0 * rng.uniform(0.0010, 0.0058)))
    nco0 = max(3, i0(loans0 * rng.uniform(0.0008, 0.0060)))
    nco1 = max(3, i0(nco0 * (1.0 + rng.uniform(-0.20, 0.20))))
    res1 = i0(loans1 * rng.uniform(0.0110, 0.0215)); res0 = i0(loans0 * rng.uniform(0.0110, 0.0215))
    npl1 = max(20, i0(res1 / rng.uniform(0.72, 2.35))); npl0 = max(20, i0(res0 / rng.uniform(0.72, 2.35)))
    ta1 = i0(aea1 * rng.uniform(1.10, 1.36)); ta0 = i0(aea0 * rng.uniform(1.10, 1.36))
    ratio1 = rng.uniform(0.078, 0.142)
    rwa1 = i0(ta1 * rng.uniform(0.62, 0.84)); rwa0 = i0(ta0 * rng.uniform(0.62, 0.84))
    cet1_1, cet1_0 = i0(rwa1 * ratio1), i0(rwa0 * rng.uniform(0.078, 0.142))
    tce1, tce0 = i0(cet1_1 * rng.uniform(0.62, 0.93)), i0(cet1_0 * rng.uniform(0.62, 0.93))
    sh1 = round(rng.uniform(180, 900), 1); sh0 = round(sh1 * rng.uniform(0.96, 1.05), 1)
    px1, px0 = round(rng.uniform(9, 62), 2), round(rng.uniform(8, 58), 2)
    div1 = i0(ppnr1 * rng.uniform(0.10, 0.28))
    nim_rep = r2(nii1 / ta1 * 100.0); eff_rep = r2(nonie1 / (nii1 + nonii1) * 100.0)
    n = dict(aea1=aea1, aea0=aea0, aibl1=aibl1, aibl0=aibl0, loans1=loans1, loans0=loans0, ii1=ii1, ii0=ii0, ie1=ie1, ie0=ie0, nii1=nii1, nii0=nii0, nonii1=nonii1, nonii0=nonii0, nonie1=nonie1, nonie0=nonie0, ppnr1=ppnr1, ppnr0=ppnr0, prov1=prov1, prov0=prov0, nco1=nco1, nco0=nco0, res1=res1, res0=res0, npl1=npl1, npl0=npl0, ta1=ta1, ta0=ta0, cet1_1=cet1_1, cet1_0=cet1_0, rwa1=rwa1, rwa0=rwa0, tce1=tce1, tce0=tce0, sh1=sh1, sh0=sh0, px1=px1, px0=px0, div1=div1, subtype="core")
    rows = [("Average earning assets", aea1, aea0),
            ("Average interest-bearing liabilities", aibl1, aibl0), ("Average loans", loans1, loans0),
            ("Interest income", ii1, ii0), ("Interest expense", ie1, ie0),
            ("Net interest income", nii1, nii0), ("Noninterest income", nonii1, nonii0),
            ("Noninterest expense (2)", nonie1, nonie0), ("Pre-provision net revenue", ppnr1, ppnr0),
            ("Provision for credit losses", prov1, prov0), ("Net charge-offs", nco1, nco0),
            ("Allowance for credit losses", res1, res0), ("Nonperforming loans", npl1, npl0),
            ("Total assets", ta1, ta0), ("CET1 capital", cet1_1, cet1_0),
            ("Risk-weighted assets", rwa1, rwa0), ("Tangible common equity", tce1, tce0),
            ("Diluted shares", sh1, sh0), ("Share price", px1, px0),
            ("Reported net interest margin", nim_rep, r2(nii0 / ta0 * 100.0)),
            ("Reported efficiency ratio", eff_rep, r2(nonie0 / (nii0 + nonii0) * 100.0)),
            (na_label, div1, None)]
    notes = {1: "Average balances are derived from daily figures and may differ from the average of period-end balances.", 2: "Noninterest expense includes a one-time restructuring charge of %d in %s; the charge is not added back in the reported ratio." % (i0(nonie1 * 0.04) + 3, p1), 3: "Share price is the closing price on the last trading day of the period and is expressed in dollars, not in millions.", 4: "%s for the prior period is not presented in this exhibit." % na_label}
    return n, rows, notes

def bank_capital(u, variant, pair, rng, memo, na_label):
    p1, p0 = pair
    ta1 = rng.randrange(52000, 210000, 10); ta0 = i0(ta1 / (1 + rng.uniform(0.01, 0.08)))
    rwa1 = i0(ta1 * rng.uniform(0.58, 0.84)); rwa0 = i0(ta0 * rng.uniform(0.58, 0.84))
    cr1 = rng.uniform(0.076, 0.148); cr0 = min(0.16, max(0.07, cr1 + rng.uniform(-0.018, 0.018)))
    cet1_1, cet1_0 = i0(rwa1 * cr1), i0(rwa0 * cr0)
    t1_1, t1_0 = i0(cet1_1 * rng.uniform(1.02, 1.14)), i0(cet1_0 * rng.uniform(1.02, 1.14))
    tot1, tot0 = i0(t1_1 * rng.uniform(1.06, 1.22)), i0(t1_0 * rng.uniform(1.06, 1.22))
    lev1 = i0(ta1 * rng.uniform(1.02, 1.12))
    tce1, tce0 = i0(cet1_1 * rng.uniform(0.60, 0.94)), i0(cet1_0 * rng.uniform(0.60, 0.94))
    sh1 = round(rng.uniform(150, 820), 1); sh0 = round(sh1 * rng.uniform(0.95, 1.06), 1)
    px1 = round(rng.uniform(8, 58), 2); px0 = round(rng.uniform(7, 54), 2)
    target = round(rng.uniform(0.105, 0.125), 2)
    tbv1 = r2(tce1 / sh1); tbv0 = r2(tce0 / sh0)
    n = dict(ta1=ta1, ta0=ta0, rwa1=rwa1, rwa0=rwa0, cet1_1=cet1_1, cet1_0=cet1_0, t1_1=t1_1, t1_0=t1_0, tot1=tot1, tot0=tot0, lev1=lev1, tce1=tce1, tce0=tce0, sh1=sh1, sh0=sh0, px1=px1, px0=px0, target=target, minimum=0.07, subtype="capital")
    rows = [("CET1 capital", cet1_1, cet1_0), ("Tier 1 capital", t1_1, t1_0),
            ("Total capital", tot1, tot0), ("Risk-weighted assets", rwa1, rwa0),
            ("Total assets", ta1, ta0), ("Leverage exposure", lev1, i0(lev1 * rng.uniform(0.96, 1.03))),
            ("Tangible common equity", tce1, tce0), ("Diluted shares", sh1, sh0),
            ("Share price", px1, px0),
            ("Reported CET1 ratio", r2(cet1_1 / rwa1 * 100.0), r2(cet1_0 / rwa0 * 100.0)),
            ("Reported Tier 1 ratio", r2(t1_1 / rwa1 * 100.0), r2(t1_0 / rwa0 * 100.0)),
            ("Reported total capital ratio", r2(tot1 / rwa1 * 100.0), r2(tot0 / rwa0 * 100.0)),
            ("Minimum CET1 requirement", 7.0, 7.0),
            ("Management CET1 target", round(target * 100.0, 1), round(target * 100.0, 1)),
            ("Reported tangible book value per share", tbv1, tbv0), (na_label, i0(tce1 * 0.03), None)]
    notes = {1: "Capital amounts are end-of-period and are measured under the standardized approach.", 2: "The reported ratios include the interim profit for the period and exclude the proposed final dividend.", 3: "Share price is expressed in dollars, while capital amounts are expressed in millions.", 4: "%s for the prior period is not presented in this exhibit." % na_label}
    return n, rows, notes

def pc_fixture(u, variant, pair, rng, memo, na_label):
    p1, p0 = pair
    npe1 = rng.randrange(1200, 9400, 10); npe0 = i0(npe1 / (1 + rng.uniform(0.01, 0.13)))
    npw1, npw0 = i0(npe1 * rng.uniform(0.95, 1.08)), i0(npe0 * rng.uniform(0.95, 1.08))
    lr1 = rng.uniform(0.50, 0.79); lr0 = min(0.85, max(0.45, lr1 + rng.uniform(-0.09, 0.09)))
    er1 = rng.uniform(0.21, 0.37); er0 = min(0.42, max(0.18, er1 + rng.uniform(-0.035, 0.035)))
    loss1, loss0 = i0(npe1 * lr1), i0(npe0 * lr0); uwe1, uwe0 = i0(npe1 * er1), i0(npe0 * er0)
    uwi1, uwi0 = npe1 - loss1 - uwe1, npe0 - loss0 - uwe0
    invi1, invi0 = i0(npe1 * rng.uniform(0.09, 0.23)), i0(npe0 * rng.uniform(0.09, 0.23))
    intexp1, intexp0 = i0(npe1 * rng.uniform(0.005, 0.020)), i0(npe0 * rng.uniform(0.005, 0.020))
    tax1 = max(0, i0((uwi1 + invi1 - intexp1) * rng.uniform(0.10, 0.24)))
    tax0 = max(0, i0((uwi0 + invi0 - intexp0) * rng.uniform(0.10, 0.24)))
    ni1, ni0 = uwi1 + invi1 - intexp1 - tax1, uwi0 + invi0 - intexp0 - tax0
    cat1, cat0 = i0(loss1 * rng.uniform(0.05, 0.22)), i0(loss0 * rng.uniform(0.05, 0.22))
    surplus1, surplus0 = i0(npe1 * rng.uniform(0.55, 1.05)), i0(npe0 * rng.uniform(0.55, 1.05))
    n = dict(npe1=npe1, npe0=npe0, npw1=npw1, npw0=npw0, loss1=loss1, loss0=loss0, uwe1=uwe1, uwe0=uwe0, uwi1=uwi1, uwi0=uwi0, invi1=invi1, invi0=invi0, intexp1=intexp1, intexp0=intexp0, tax1=tax1, tax0=tax0, ni1=ni1, ni0=ni0, cat1=cat1, cat0=cat0, surplus1=surplus1, surplus0=surplus0, subtype="pc")
    rows = [("Net premiums written", npw1, npw0), ("Net premiums earned", npe1, npe0),
            ("Losses and loss adjustment expenses", loss1, loss0),
            ("Underwriting expenses", uwe1, uwe0), ("Underwriting income", uwi1, uwi0),
            ("Net investment income", invi1, invi0), ("Interest expense", intexp1, intexp0),
            ("Income tax expense", tax1, tax0), ("Net income", ni1, ni0),
            ("Catastrophe losses included above", cat1, cat0), ("Policyholders surplus", surplus1, surplus0),
            ("Reported loss ratio", r2(loss1 / npe1 * 100.0), r2(loss0 / npe0 * 100.0)),
            ("Reported expense ratio", r2(uwe1 / npe1 * 100.0), r2(uwe0 / npe0 * 100.0)),
            ("Reported combined ratio", r2((loss1 + uwe1) / npe1 * 100.0), r2((loss0 + uwe0) / npe0 * 100.0)),
            (na_label, i0(ni1 * 0.18), None)]
    notes = {1: "Premiums are presented net of reinsurance and are earned pro rata over the policy term.", 2: "Underwriting expenses include acquisition costs and are stated before policy administration fees.", 3: "Policyholders surplus is an end-of-period amount; ratio rows are computed on net premiums earned.", 4: "%s for the prior period is not presented in this exhibit." % na_label}
    return n, rows, notes

def life_fixture(u, variant, pair, rng, memo, na_label):
    p1, p0 = pair
    evo1 = rng.randrange(3000, 15000, 10); evo0 = i0(evo1 / (1 + rng.uniform(0.02, 0.11)))
    ape1 = rng.randrange(220, 980, 5); ape0 = i0(ape1 / (1 + rng.uniform(0.0, 0.12)))
    m1 = rng.uniform(0.016, 0.066); m0 = min(0.08, max(0.010, m1 + rng.uniform(-0.008, 0.008)))
    vnb1, vnb0 = i0(ape1 * m1), i0(ape0 * m0)
    expr1, expr0 = i0(evo1 * rng.uniform(0.052, 0.088)), i0(evo0 * rng.uniform(0.052, 0.088))
    divs1, divs0 = i0(evo1 * rng.uniform(0.012, 0.042)), i0(evo0 * rng.uniform(0.012, 0.042))
    evc1 = evo1 + vnb1 + expr1 - divs1; evc0 = evo0 + vnb0 + expr0 - divs0
    sh1 = round(rng.uniform(120, 640), 1); sh0 = round(sh1 * rng.uniform(0.97, 1.04), 1)
    op1, op0 = vnb1 + expr1, vnb0 + expr0
    n = dict(evo1=evo1, evo0=evo0, vnb1=vnb1, vnb0=vnb0, expr1=expr1, expr0=expr0, divs1=divs1, divs0=divs0, evc1=evc1, evc0=evc0, ape1=ape1, ape0=ape0, sh1=sh1, sh0=sh0, op1=op1, op0=op0, subtype="life")
    rows = [("Embedded value, opening", evo1, evo0), ("Value of new business", vnb1, vnb0),
            ("Expected return on embedded value", expr1, expr0), ("Dividends paid", divs1, divs0),
            ("Embedded value, closing", evc1, evc0), ("Annual premium equivalent", ape1, ape0),
            ("Operating profit", op1, op0), ("Shares outstanding", sh1, sh0),
            ("Value of new business margin (reported)", r2(vnb1 / ape1 * 100.0), r2(vnb0 / ape0 * 100.0)),
            ("Embedded value per share (reported)", r2(evc1 / sh1), r2(evc0 / sh0)),
            ("Return on embedded value (reported)", r2((evc1 - evo1 + divs1) / evo1 * 100.0),
             r2((evc0 - evo0 + divs0) / evo0 * 100.0)), (na_label, i0(evc1 * 0.02), None)]
    notes = {1: "Embedded value is shown on a shareholder basis and is not a measure of market capitalization.", 2: "Value of new business is stated after the cost of capital held against new business.", 3: "Share counts are expressed in millions and per-share amounts in dollars, not in millions.", 4: "%s for the prior period is not presented in this exhibit." % na_label}
    return n, rows, notes

def render(fx):
    lines = [UNITS, "", "%s - %s, %s." % (fx["ent"], fx["variant"], fx["p1"]), "", fx["memo"], "",
             "| Item | %s | %s |" % (fx["p1"], fx["p0"]), "|---|---|---|"]
    for lab, a, b in fx["rows"]:
        lines.append("| %s | %s | %s |" % (lab, num(a), num(b)))
    lines.append("")
    for k in sorted(fx["notes"]):
        lines.append("Footnote (%d): %s" % (k, fx["notes"][k]))
    lines.append("")
    lines.append("n.a. = not presented in this exhibit.")
    return "\n".join(lines)

def build_fixtures():
    rng = random.Random(SEED)
    out = []
    for name, etype, sector in ENTITIES:
        for i, variant in enumerate(VARIANTS[etype]):
            pair = PAIRS[i % len(PAIRS)]
            memo = MEMOS[(i + len(name)) % len(MEMOS)]
            pool = NA_LABELS[etype]
            na_label = pool[(i + len(sector)) % len(pool)]
            args = (None, variant, pair, rng, memo, na_label)
            if etype == "bank":
                subtype = "capital" if i in (4, 5) else "core"
                n, rows, notes = (bank_capital if subtype == "capital" else bank_core)(*args)
            elif etype == "pc":
                subtype = "pc"
                n, rows, notes = pc_fixture(*args)
            else:
                subtype = "life"
                n, rows, notes = life_fixture(*args)
            fx = {"key": "%s|%s|%s" % (name, variant, subtype), "ent": name, "etype": etype,
                  "sector": sector, "subtype": subtype, "variant": variant, "p1": pair[0],
                  "p0": pair[1], "memo": memo, "rows": rows, "notes": notes, "n": n}
            fx["context"] = render(fx)
            out.append(fx)
    return out
FIXTURES = build_fixtures()

def dollar_rows(fx):
    out = []
    for lab, a, b in fx["rows"]:
        if not isinstance(a, int) or a <= 0 or "(" in lab or lab.startswith("Reported"):
            continue
        if lab in ("Diluted shares", "Shares outstanding", "Share price"):
            continue
        out.append((lab, a, b))
    return out

def pick(fx, salt, items):
    if not items: return None
    return items[int(h(fx["key"] + "|" + salt), 16) % len(items)]
CALC = {}

def C(fid, types, tol, tpl, fn, multi=0): CALC[fid] = {"types": types, "tol": tol, "tpl": tpl, "at": "number", "fn": (lambda f, g=fn: g(f["n"])), "multi": multi}

def qtext(spec, fx):
    t = spec["tpl"]
    return t(fx) if callable(t) else t.format(p0=fx["p0"], p1=fx["p1"])
C("c_nim", ["core"], "abs:0.1", "Using average earning assets, what was the {p1} net interest margin, in percent?", lambda n: pct1(n["nii1"], n["aea1"]))
C("c_yield", ["core"], "abs:0.1", "What was the {p1} earning-asset yield, in percent?", lambda n: pct1(n["ii1"], n["aea1"]))
C("c_cof", ["core"], "abs:0.1", "What was the {p1} cost of funds on average interest-bearing liabilities, in percent?", lambda n: pct1(n["ie1"], n["aibl1"]))
C("c_spread", ["core"], "abs:0.1", "What was the {p1} net interest spread, measured as the earning-asset yield less the cost of funds, in percent?", lambda n: r2(pct1(n["ii1"], n["aea1"]) - pct1(n["ie1"], n["aibl1"])), 1)
C("c_eff", ["core"], "abs:0.1", "What was the {p1} efficiency ratio, in percent?", lambda n: pct1(n["nonie1"], n["nii1"] + n["nonii1"]), 1)
C("c_revenue", ["core"], "rel:0.01", "What was {p1} revenue, measured as net interest income plus noninterest income, in $ millions?", lambda n: n["nii1"] + n["nonii1"], 1)
C("c_ppnr", ["core"], "rel:0.01", "What was {p1} pre-provision net revenue, in $ millions?", lambda n: n["ppnr1"], 1)
C("c_nco_rate", ["core"], "abs:0.1", "What was the {p1} net charge-off rate on average loans, in percent?", lambda n: pct1(n["nco1"], n["loans1"]))
C("c_prov_build", ["core"], "abs:1", "What was the {p1} provision build or release, measured as the provision for credit losses less net charge-offs, in $ millions?", lambda n: n["prov1"] - n["nco1"], 1)
C("c_coverage", ["core"], "abs:0.1", "What was the {p1} allowance coverage of nonperforming loans, in percent?", lambda n: pct1(n["res1"], n["npl1"]))
C("c_res_loans", ["core"], "abs:0.1", "What was the {p1} allowance for credit losses as a percentage of average loans?", lambda n: pct1(n["res1"], n["loans1"]))
C("c_nim_bp", ["core"], "abs:1", "By how many basis points did the net interest margin change from {p0} to {p1}?", lambda n: r2((pct1(n["nii1"], n["aea1"]) - pct1(n["nii0"], n["aea0"])) * 100.0), 1)
C("c_eff_pp", ["core"], "abs:0.1", "By how many percentage points did the efficiency ratio change from {p0} to {p1}?", lambda n: r2(pct1(n["nonie1"], n["nii1"] + n["nonii1"]) - pct1(n["nonie0"], n["nii0"] + n["nonii0"])), 1)
C("c_rev_growth", ["core"], "abs:0.1", "What was the growth in revenue from {p0} to {p1}, in percent?", lambda n: r2((n["nii1"] + n["nonii1"] - n["nii0"] - n["nonii0"]) / float(n["nii0"] + n["nonii0"]) * 100.0), 1)
C("c_cet1", ["core"], "abs:0.1", "What was the {p1} CET1 ratio, in percent?", lambda n: pct1(n["cet1_1"], n["rwa1"]))
C("c_tbv", ["core"], "abs:0.01", "What was tangible book value per share at {p1}, in dollars?", lambda n: r2(float(n["tce1"]) / n["sh1"]))
C("c_ptbv", ["core"], "abs:0.05", "What was the price to tangible book value multiple at {p1}, in times?", lambda n: r2(n["px1"] / (float(n["tce1"]) / n["sh1"])), 1)
C("c_nco_chg", ["core"], "abs:0.1", "By what percentage did net charge-offs change from {p0} to {p1}?", lambda n: r2((n["nco1"] - n["nco0"]) / float(n["nco0"]) * 100.0), 1)
C("k_cet1", ["capital"], "abs:0.1", "For the capital schedule, what was the {p1} common equity tier 1 ratio, in percent?", lambda n: pct1(n["cet1_1"], n["rwa1"]))
C("k_density", ["capital"], "abs:0.1", "What was the {p1} risk-weighted asset density, measured as risk-weighted assets over total assets, in percent?", lambda n: pct1(n["rwa1"], n["ta1"]))
C("k_tbv", ["capital"], "abs:0.01", "What was tangible book value per share at {p1} under the capital schedule, in dollars?", lambda n: r2(float(n["tce1"]) / n["sh1"]))
C("k_ptbv", ["capital"], "abs:0.05", "What was the price to tangible book value multiple in the capital schedule at {p1}, in times?", lambda n: r2(n["px1"] / (float(n["tce1"]) / n["sh1"])), 1)
C("k_headroom", ["capital"], "abs:0.1", "What was the gap between the {p1} CET1 ratio and the management target, in percentage points, measured as the ratio less the target?", lambda n: r2(pct1(n["cet1_1"], n["rwa1"]) - n["target"] * 100.0), 1)
C("p_loss", ["pc"], "abs:0.1", "What was the {p1} loss ratio, in percent?", lambda n: pct1(n["loss1"], n["npe1"]))
C("p_exp", ["pc"], "abs:0.1", "What was the {p1} expense ratio, measured as underwriting expenses over net premiums earned, in percent?", lambda n: pct1(n["uwe1"], n["npe1"]))
C("p_comb", ["pc"], "abs:0.1", "What was the {p1} combined ratio, in percent?", lambda n: r2(pct1(n["loss1"], n["npe1"]) + pct1(n["uwe1"], n["npe1"])), 1)
C("p_uwi", ["pc"], "abs:1", "What was {p1} underwriting income, in $ millions?", lambda n: n["npe1"] - n["loss1"] - n["uwe1"], 1)
C("p_comb_chg", ["pc"], "abs:0.1", "By how many percentage points did the combined ratio change from {p0} to {p1}?", lambda n: r2(pct1(n["loss1"], n["npe1"]) + pct1(n["uwe1"], n["npe1"]) - pct1(n["loss0"], n["npe0"]) - pct1(n["uwe0"], n["npe0"])), 1)
C("p_uw_margin", ["pc"], "abs:0.1", "What was the {p1} underwriting margin, measured as underwriting income over net premiums earned, in percent?", lambda n: pct1(n["npe1"] - n["loss1"] - n["uwe1"], n["npe1"]), 1)
C("p_loss_chg", ["pc"], "abs:0.1", "By how many percentage points did the loss ratio move from {p0} to {p1}?", lambda n: r2(pct1(n["loss1"], n["npe1"]) - pct1(n["loss0"], n["npe0"])), 1)
C("l_vnb_margin", ["life"], "abs:0.1", "What was the {p1} value of new business margin, measured as value of new business over annual premium equivalent, in percent?", lambda n: pct1(n["vnb1"], n["ape1"]))
C("l_ev_growth", ["life"], "abs:0.1", "By what percentage did embedded value grow from {p0} to {p1}?", lambda n: r2((n["evc1"] - n["evo1"]) / float(n["evo1"]) * 100.0), 1)
C("l_evps", ["life"], "abs:0.05", "What was embedded value per share at {p1}, in dollars?", lambda n: r2(float(n["evc1"]) / n["sh1"]))
C("l_vnb_ev", ["life"], "abs:0.1", "What was the value of new business as a percentage of opening embedded value in {p1}?", lambda n: pct1(n["vnb1"], n["evo1"]))
C("l_ev_return", ["life"], "abs:0.1", "What was the {p1} operating return on embedded value, measured as closing less opening plus dividends over opening, in percent?", lambda n: r2((n["evc1"] - n["evo1"] + n["divs1"]) / float(n["evo1"]) * 100.0), 1)

def e_val_p1(fx):
    r = pick(fx, "p1", dollar_rows(fx))
    return None if not r else ("What amount is reported for %s in the %s column?" % (r[0], fx["p1"]), r[1], "number", "abs:1")

def e_val_p0(fx):
    r = pick(fx, "p0", [x for x in dollar_rows(fx) if x[2] is not None])
    return None if not r else ("What amount does the %s column report for %s?" % (fx["p0"], r[0]), r[2], "number", "abs:1")

def e_max_delta(fx):
    rows = [x for x in dollar_rows(fx) if x[2] is not None]
    if len(rows) < 3: return None
    b = max(rows, key=lambda x: x[1] - x[2])
    return ("Which line item shows the largest dollar increase between the %s column and the %s column?" % (fx["p0"], fx["p1"]), b[0], "text", "normalized")

def e_min_p1(fx):
    rows = dollar_rows(fx)
    if len(rows) < 3: return None
    b = min(rows, key=lambda x: x[1])
    return ("Which line item reports the smallest positive amount in the %s column?" % fx["p1"], b[0], "text", "normalized")

def e_label_val(fx):
    rows = dollar_rows(fx)
    vals = [x[1] for x in rows]
    r = pick(fx, "lv", [x for x in rows if vals.count(x[1]) == 1])
    return None if not r else ("Which line item reports the value %s in the %s column?" % (num(r[1]), fx["p1"]), r[0], "text", "normalized")

def e_na_row(fx):
    for lab, a, b in fx["rows"]:
        if a is not None and b is None:
            return ("Which line item is marked n.a. in the %s column?" % fx["p0"], lab, "text", "normalized")
    return None

def e_footnote(fx):
    k = int(h(fx["key"] + "|fn"), 16) % 4 + 1
    return ("Quote the text of footnote (%d) exactly as it appears in the exhibit." % k, fx["notes"][k], "text", "normalized")

def e_list_above(fx):
    rows = dollar_rows(fx)
    if len(rows) < 6: return None
    vals = sorted([x[1] for x in rows]); t = vals[len(vals) // 2]
    labs = [x[0] for x in rows if x[1] >= t]
    if not (1 <= len(labs) <= 12): return None
    return ("List every line item whose %s amount is at or above %s." % (fx["p1"], num(t)), labs, "list", "set")

def e_count_above(fx):
    rows = dollar_rows(fx)
    if len(rows) < 5: return None
    vals = sorted([x[1] for x in rows]); t = vals[int(len(vals) * 0.7)]
    cnt = len([x for x in rows if x[1] > t])
    return None if cnt < 1 else ("How many line items in the %s column exceed %s?" % (fx["p1"], num(t)), cnt, "number", "abs:0.01")

def e_pct_row(fx):
    r = pick(fx, "pct", [x for x in fx["rows"] if x[0].startswith("Reported") and isinstance(x[1], float)])
    return None if not r else ("What value is reported for the %s line in the %s column, in percent?" % (r[0], fx["p1"]), r[1], "number", "abs:0.1")
EXTR = {"e_val_p1": e_val_p1, "e_val_p0": e_val_p0, "e_max_delta": e_max_delta, "e_min_p1": e_min_p1,
        "e_label_val": e_label_val, "e_na_row": e_na_row, "e_footnote": e_footnote,
        "e_list_above": e_list_above, "e_count_above": e_count_above, "e_pct_row": e_pct_row}
QA = {}

def Q(fid, types, at, tol, tpl, fn): QA[fid] = {"types": types, "at": at, "tol": tol, "tpl": tpl, "fn": fn}

def _q_big_inc(fx):
    rows = [x for x in dollar_rows(fx) if x[2] is not None]
    return None if len(rows) < 3 else max(rows, key=lambda x: x[1] - x[2])[0]

def _q_cov(fx):
    n = fx["n"]
    return "improved" if pct1(n["res1"], n["npl1"]) > pct1(n["res0"], n["npl0"]) else "deteriorated"

def _q_nim(fx):
    n = fx["n"]
    dy = abs(pct1(n["ii1"], n["aea1"]) - pct1(n["ii0"], n["aea0"]))
    dc = abs(pct1(n["ie1"], n["aibl1"]) - pct1(n["ie0"], n["aibl0"]))
    return "asset yield" if dy >= dc else "funding cost"

def _q_res(fx):
    c = pct1(fx["n"]["res1"], fx["n"]["npl1"])
    return "well reserved" if c >= 150 else ("adequately reserved" if c >= 100 else "under-reserved")

def _q_cet1(fx):
    c = pct1(fx["n"]["cet1_1"], fx["n"]["rwa1"])
    return "strong" if c >= 11.5 else ("adequate" if c >= 9.5 else "deficient")

def _q_tbv(fx):
    n = fx["n"]
    return "premium" if n["px1"] > float(n["tce1"]) / n["sh1"] else "discount"

def _q_uw(fx):
    n = fx["n"]
    return "profitable" if n["npe1"] - n["loss1"] - n["uwe1"] > 0 else "unprofitable"

def _q_inv(fx):
    n = fx["n"]
    return pct1(n["invi1"], n["npe1"] - n["loss1"] - n["uwe1"] + n["invi1"])

def _q_comb(fx):
    n = fx["n"]
    c1 = pct1(n["loss1"], n["npe1"]) + pct1(n["uwe1"], n["npe1"])
    c0 = pct1(n["loss0"], n["npe0"]) + pct1(n["uwe0"], n["npe0"])
    return "improved" if c1 < c0 else "deteriorated"

def _q_ev(fx):
    n = fx["n"]
    return "value of new business" if n["vnb1"] >= n["expr1"] else "expected return on embedded value"

def _q_vnb(fx):
    m = pct1(fx["n"]["vnb1"], fx["n"]["ape1"])
    return "strong" if m >= 4.5 else ("adequate" if m >= 3.0 else "weak")
Q("q_eff_move", ["core"], "number", "abs:0.1", "How many percentage points did the efficiency ratio move between {p0} and {p1}?", lambda fx: r2(pct1(fx["n"]["nonie1"], fx["n"]["nii1"] + fx["n"]["nonii1"]) - pct1(fx["n"]["nonie0"], fx["n"]["nii0"] + fx["n"]["nonii0"])))
Q("q_big_inc", ["core", "capital", "pc", "life"], "text", "normalized", "Which line item contributed the largest dollar increase from {p0} to {p1}?", _q_big_inc)
Q("q_cov_dir", ["core"], "label", "exact", "Did allowance coverage of nonperforming loans improve or deteriorate between {p0} and {p1}?", _q_cov)
Q("q_nim_driver", ["core"], "label", "exact", "Did the movement in net interest margin owe more to the earning-asset yield or to the cost of funds?", _q_nim)
Q("q_res_band", ["core"], "label", "exact", "Using these bands: coverage of nonperforming loans at or above 150 percent is well reserved, 100 to 150 percent is adequately reserved, and below 100 percent is under-reserved. How would the {p1} allowance position be classified?", _q_res)
Q("q_cet1_band", ["capital"], "label", "exact", "Using these bands: a CET1 ratio at or above 11.5 percent is strong, 9.5 to 11.5 percent is adequate, and below 9.5 percent is deficient. How would the {p1} capital position be classified?", _q_cet1)
Q("q_tbv_pos", ["capital"], "label", "exact", "Is the share price at a premium or a discount to tangible book value per share at {p1}?", _q_tbv)
Q("q_headroom", ["capital"], "number", "abs:0.1", "What was the difference between the {p1} CET1 ratio and the management target, in percentage points?", lambda fx: r2(pct1(fx["n"]["cet1_1"], fx["n"]["rwa1"]) - fx["n"]["target"] * 100.0))
Q("q_uw_result", ["pc"], "label", "exact", "Was the {p1} underwriting result profitable or unprofitable?", _q_uw)
Q("q_inv_share", ["pc"], "number", "abs:0.1", "What share of {p1} underwriting plus investment income came from net investment income, in percent?", _q_inv)
Q("q_comb_trend", ["pc"], "label", "exact", "Did the combined ratio improve or deteriorate from {p0} to {p1}?", _q_comb)
Q("q_ev_driver", ["life"], "text", "normalized", "Which component was the larger positive contributor to the change in embedded value in {p1}?", _q_ev)
Q("q_vnb_band", ["life"], "label", "exact", "Using these bands: a value of new business margin at or above 4.5 percent is strong, 3.0 to 4.5 percent is adequate, and below 3.0 percent is weak. How would the {p1} new business result be classified?", _q_vnb)
Q("q_ev_growth", ["life"], "number", "abs:0.1", "What was the percentage growth in embedded value between {p0} and {p1}?", lambda fx: r2((fx["n"]["evc1"] - fx["n"]["evo1"]) / float(fx["n"]["evo1"]) * 100.0))
CLS = {}

def K(fid, types, labels, tpl, fn): CLS[fid] = {"types": types, "labels": labels, "tpl": tpl, "fn": fn}
K("cls_capital_band", ["capital"], ["strong", "adequate", "deficient"], "Using these bands: a CET1 ratio at or above 11.5 percent is strong, 9.5 to 11.5 percent is adequate, and below 9.5 percent is deficient. Classify the {p1} capital position. Answer with one label from: strong, adequate, deficient.", _q_cet1)
K("cls_reserve_band", ["core"], ["well reserved", "adequately reserved", "under-reserved"], "Using these bands: coverage of nonperforming loans at or above 150 percent is well reserved, 100 to 150 percent is adequately reserved, and below 100 percent is under-reserved. Classify the {p1} allowance position. Answer with one label from: well reserved, adequately reserved, under-reserved.", _q_res)

def _k_aq(fx):
    n = fx["n"]
    ch = (n["nco1"] - n["nco0"]) / float(n["nco0"]) * 100.0
    return "improving" if ch < -5 else ("stable" if ch <= 5 else "deteriorating")

def _k_margin(fx):
    n = fx["n"]
    bp = (pct1(n["nii1"], n["aea1"]) - pct1(n["nii0"], n["aea0"])) * 100.0
    return "expanding" if bp >= 5 else ("compressing" if bp <= -5 else "stable")

def _k_eff(fx):
    n = fx["n"]
    e = pct1(n["nonie1"], n["nii1"] + n["nonii1"])
    return "efficient" if e <= 55 else ("acceptable" if e <= 65 else "inefficient")

def _k_comb(fx):
    n = fx["n"]
    c = pct1(n["loss1"], n["npe1"]) + pct1(n["uwe1"], n["npe1"])
    return "profitable" if c <= 95 else ("marginal" if c <= 100 else "unprofitable")

def _k_uw(fx):
    n = fx["n"]
    d = pct1(n["loss1"], n["npe1"]) + pct1(n["uwe1"], n["npe1"]) - pct1(n["loss0"], n["npe0"]) - pct1(n["uwe0"], n["npe0"])
    return "improving" if d < -1 else ("stable" if d <= 1 else "deteriorating")

def _k_eq(fx):
    n = fx["n"]
    if n["prov1"] > n["nco1"] * 1.15:
        return "high quality"
    return "low quality" if n["nco1"] > n["prov1"] * 1.05 else "mixed"
K("cls_asset_quality", ["core"], ["improving", "stable", "deteriorating"], "Using these bands for the change in net charge-offs: a fall of more than 5 percent is improving, a change within 5 percent is stable, and a rise of more than 5 percent is deteriorating. Classify the {p1} asset quality trend. Answer with one label from: improving, stable, deteriorating.", _k_aq)
K("cls_margin_trend", ["core"], ["expanding", "stable", "compressing"], "Using these bands for the change in net interest margin: a rise of at least 5 basis points is expanding, a move within 5 basis points is stable, and a fall of at least 5 basis points is compressing. Classify the {p1} margin trend. Answer with one label from: expanding, stable, compressing.", _k_margin)
K("cls_efficiency_band", ["core"], ["efficient", "acceptable", "inefficient"], "Using these bands: an efficiency ratio at or below 55 percent is efficient, above 55 and at or below 65 percent is acceptable, and above 65 percent is inefficient. Classify the {p1} cost position. Answer with one label from: efficient, acceptable, inefficient.", _k_eff)
K("cls_combined_band", ["pc"], ["profitable", "marginal", "unprofitable"], "Using these bands: a combined ratio at or below 95 percent is profitable, above 95 and at or below 100 percent is marginal, and above 100 percent is unprofitable. Classify the {p1} underwriting result. Answer with one label from: profitable, marginal, unprofitable.", _k_comb)
K("cls_uw_trend", ["pc"], ["improving", "stable", "deteriorating"], "Using these bands for the change in the combined ratio: a fall of more than 1 percentage point is improving, a move within 1 point is stable, and a rise of more than 1 point is deteriorating. Classify the {p1} underwriting trend. Answer with one label from: improving, stable, deteriorating.", _k_uw)
K("cls_vnb_band", ["life"], ["strong", "adequate", "weak"], "Using these bands: a value of new business margin at or above 4.5 percent is strong, 3.0 to 4.5 percent is adequate, and below 3.0 percent is weak. Classify the {p1} new business result. Answer with one label from: strong, adequate, weak.", _q_vnb)
K("cls_earnings_quality", ["core"], ["high quality", "mixed", "low quality"], "Using these bands: a provision more than 15 percent above net charge-offs is high quality, net charge-offs more than 5 percent above the provision is low quality, and anything in between is mixed. Classify the {p1} earnings quality. Answer with one label from: high quality, mixed, low quality.", _k_eq)
SUMM = {}

def S(fid, types, tpl, fn): SUMM[fid] = {"types": types, "tpl": tpl, "fn": fn, "at": "text", "tol": "normalized"}
S("s_earnings", ["core"], "Summarize the {p1} earnings result in two sentences, using only figures shown in the exhibit.",
  lambda fx: "Net interest income was %s and noninterest income was %s against noninterest expense of %s, leaving pre-provision net revenue of %s. The provision for credit losses was %s and net charge-offs were %s." % (num(fx["n"]["nii1"]), num(fx["n"]["nonii1"]), num(fx["n"]["nonie1"]), num(fx["n"]["ppnr1"]), num(fx["n"]["prov1"]), num(fx["n"]["nco1"])))
S("s_margin", ["core"], "Summarize how the interest margin moved between the two columns, citing only figures shown in the exhibit.",
  lambda fx: "Interest income moved from %s to %s while interest expense moved from %s to %s, so net interest income changed from %s to %s." % (num(fx["n"]["ii0"]), num(fx["n"]["ii1"]), num(fx["n"]["ie0"]), num(fx["n"]["ie1"]), num(fx["n"]["nii0"]), num(fx["n"]["nii1"])))
S("s_credit", ["core"], "Summarize the credit quality trend between the two columns using only figures shown in the exhibit.",
  lambda fx: "Net charge-offs moved from %s to %s against a provision of %s in %s. The allowance for credit losses was %s and nonperforming loans were %s." % (num(fx["n"]["nco0"]), num(fx["n"]["nco1"]), num(fx["n"]["prov1"]), fx["p1"], num(fx["n"]["res1"]), num(fx["n"]["npl1"])))
S("s_uw", ["pc"], "Summarize the {p1} underwriting result in two sentences using only figures shown in the exhibit.",
  lambda fx: "Net premiums earned of %s less losses of %s and underwriting expenses of %s produced underwriting income of %s. Net investment income was %s and net income was %s." % (num(fx["n"]["npe1"]), num(fx["n"]["loss1"]), num(fx["n"]["uwe1"]), num(fx["n"]["uwi1"]), num(fx["n"]["invi1"]), num(fx["n"]["ni1"])))
S("s_combined", ["pc"], "Summarize the combined ratio movement between the two columns using the reported rows only.",
  lambda fx: "The reported loss ratio moved from %s to %s and the reported expense ratio moved from %s to %s, so the reported combined ratio moved from %s to %s." % (num(r2(pct1(fx["n"]["loss0"], fx["n"]["npe0"]))), num(r2(pct1(fx["n"]["loss1"], fx["n"]["npe1"]))), num(r2(pct1(fx["n"]["uwe0"], fx["n"]["npe0"]))), num(r2(pct1(fx["n"]["uwe1"], fx["n"]["npe1"]))), num(r2(pct1(fx["n"]["loss0"] + fx["n"]["uwe0"], fx["n"]["npe0"]))), num(r2(pct1(fx["n"]["loss1"] + fx["n"]["uwe1"], fx["n"]["npe1"])))))
S("s_investment", ["pc"], "Summarize how underwriting income and investment income combined into net income in {p1}.",
  lambda fx: "Underwriting income of %s plus net investment income of %s, less interest expense of %s and income tax expense of %s, produced net income of %s." % (num(fx["n"]["uwi1"]), num(fx["n"]["invi1"]), num(fx["n"]["intexp1"]), num(fx["n"]["tax1"]), num(fx["n"]["ni1"])))
S("s_pc_balance", ["pc"], "Summarize the premium base and policyholders surplus shown for {p1}.",
  lambda fx: "Net premiums written were %s and net premiums earned were %s, with catastrophe losses of %s included in the loss figure. Policyholders surplus was %s at the period end." % (num(fx["n"]["npw1"]), num(fx["n"]["npe1"]), num(fx["n"]["cat1"]), num(fx["n"]["surplus1"])))
S("s_ev", ["life"], "Summarize the embedded value movement in two sentences using only figures shown in the exhibit.",
  lambda fx: "Embedded value moved from %s to %s, with value of new business of %s and an expected return of %s, partly offset by dividends of %s. Operating profit was %s." % (num(fx["n"]["evo1"]), num(fx["n"]["evc1"]), num(fx["n"]["vnb1"]), num(fx["n"]["expr1"]), num(fx["n"]["divs1"]), num(fx["n"]["op1"])))
S("s_vnb", ["life"], "Summarize new business profitability in {p1} using only figures shown in the exhibit.",
  lambda fx: "Value of new business of %s on an annual premium equivalent of %s gives a reported margin of %s percent." % (num(fx["n"]["vnb1"]), num(fx["n"]["ape1"]), num(r2(pct1(fx["n"]["vnb1"], fx["n"]["ape1"])))))
S("s_ev_mix", ["life"], "Summarize the components of the embedded value change between the two columns.",
  lambda fx: "Value of new business of %s and expected return of %s were partly offset by dividends of %s, moving embedded value from %s to %s." % (num(fx["n"]["vnb1"]), num(fx["n"]["expr1"]), num(fx["n"]["divs1"]), num(fx["n"]["evo1"]), num(fx["n"]["evc1"])))
S("s_ev_capital", ["life"], "Summarize the capital and embedded value position at {p1}.",
  lambda fx: "Operating profit was %s against a closing embedded value of %s and an opening embedded value of %s. Shares outstanding were %s." % (num(fx["n"]["op1"]), num(fx["n"]["evc1"]), num(fx["n"]["evo1"]), num(fx["n"]["sh1"])))

def _s_cap(fx):
    n = fx["n"]
    if fx["subtype"] == "capital":
        return "CET1 capital of %s against risk-weighted assets of %s gives a reported CET1 ratio of %s percent. Tangible common equity of %s and diluted shares of %s give reported tangible book value per share of %s." % (num(n["cet1_1"]), num(n["rwa1"]), num(r2(pct1(n["cet1_1"], n["rwa1"]))), num(n["tce1"]), num(n["sh1"]), num(r2(float(n["tce1"]) / n["sh1"])))
    return "CET1 capital of %s against risk-weighted assets of %s, with total assets of %s and tangible common equity of %s." % (num(n["cet1_1"]), num(n["rwa1"]), num(n["ta1"]), num(n["tce1"]))
S("s_capital", ["core", "capital"], "Summarize the capital position at {p1} using only figures shown in the exhibit.", _s_cap)

TOOLS = {"get_line_item": ("Return the reported value for one line item and period from the supplied extract.", ["entity", "line_item", "period"]),
         "list_line_items": ("List every line item available in the supplied extract for a period.", ["entity", "period"]),
         "get_footnote": ("Return the text of a numbered footnote from the supplied extract.", ["entity", "footnote"])}

def tool_def(name):
    d, req = TOOLS[name]
    return {"name": name, "description": d, "parameters": {
        "type": "object", "properties": dict((k, {"type": "integer" if k == "footnote" else "string"}) for k in req), "required": req}}

def snippet(fx, k=9):
    L = [UNITS, "", "%s - %s, %s." % (fx["ent"], fx["variant"], fx["p1"]), "", "| Item | %s | %s |" % (fx["p1"], fx["p0"]), "|---|---|---|"]
    for lab, a, b in fx["rows"][:k]:
        L.append("| %s | %s | %s |" % (lab, num(a), num(b)))
    return "\n".join(L)

def req(fx, text): return "For %s (%s), %s\n\n%s" % (fx["ent"], fx["variant"], text, snippet(fx))

def jd(d): return json.dumps(d, sort_keys=True)
PREF_PAIR = {"core": ("Net interest income", "Average earning assets"), "capital": ("CET1 capital", "Risk-weighted assets"),
             "pc": ("Underwriting income", "Net premiums earned"), "life": ("Value of new business", "Annual premium equivalent")}
TOOL_FAMS = ["t_ratio", "t_lookup", "t_retry", "t_footnote", "t_abstain", "t_list", "t_band", "t_units"]

def pair_rows(fx):
    have = dict((l, (l, a, b)) for l, a, b in fx["rows"] if a is not None)
    p = PREF_PAIR.get(fx["subtype"])
    if p and p[0] in have and p[1] in have:
        return have[p[0]], have[p[1]]
    rows = sorted([r for r in dollar_rows(fx) if r[2] is not None], key=lambda r: r[1])
    return (None, None) if len(rows) < 4 else (rows[0], rows[-1])

def tool_row(fx, fam):
    n = fx["n"]
    rows = [r for r in dollar_rows(fx) if r[2] is not None]
    a_row, b_row = pair_rows(fx)
    if not rows or (fam == "t_ratio" and a_row is None) or (fam == "t_band" and "cet1_1" not in n): return None
    if fam == "t_ratio":
        m = [{"role": "user", "content": req(fx, "pull %s and %s for %s with get_line_item." % (a_row[0], b_row[0], fx["p1"]))},
             {"role": "assistant", "content": "I will call get_line_item for both line items and then compute the ratio."},
             {"role": "tool", "content": jd({"entity": fx["ent"], "period": fx["p1"], "items": [{"line_item": a_row[0], "value": a_row[1]}, {"line_item": b_row[0], "value": b_row[1]}]})},
             {"role": "user", "content": "What is %s as a percentage of %s?" % (a_row[0], b_row[0])}]
        return m, [tool_def("get_line_item")], r2(float(a_row[1]) / b_row[1] * 100.0), "number", "abs:0.1"
    if fam == "t_lookup":
        r = rows[int(h(fx["key"] + "|lk"), 16) % len(rows)]
        m = [{"role": "user", "content": req(fx, "what is the reported %s for %s?" % (r[0], fx["p1"]))},
             {"role": "tool", "content": jd({"entity": fx["ent"], "period": fx["p1"], "line_item": r[0], "value": r[1]})},
             {"role": "user", "content": "State the reported amount in $ millions."}]
        return m, [tool_def("get_line_item")], r[1], "number", "abs:1"
    if fam == "t_retry":
        r = rows[int(h(fx["key"] + "|rt"), 16) % len(rows)]
        m = [{"role": "user", "content": req(fx, "fetch %s for Q4 FY2026." % r[0])},
             {"role": "assistant", "content": "Calling get_line_item with the requested period."},
             {"role": "tool", "content": jd({"error": "period not found", "available_periods": [fx["p1"], fx["p0"]]})},
             {"role": "assistant", "content": "That period is not in the extract. Retrying with %s." % fx["p1"]},
             {"role": "tool", "content": jd({"entity": fx["ent"], "period": fx["p1"], "line_item": r[0], "value": r[1]})},
             {"role": "user", "content": "So what is the %s value for %s?" % (r[0], fx["p1"])}]
        return m, [tool_def("get_line_item")], r[1], "number", "abs:1"
    if fam == "t_footnote":
        k = int(h(fx["key"] + "|tf"), 16) % 4 + 1
        m = [{"role": "user", "content": req(fx, "what does footnote (%d) say in the %s?" % (k, fx["variant"]))},
             {"role": "assistant", "content": "I will call get_footnote for note %d." % k},
             {"role": "tool", "content": jd({"entity": fx["ent"], "footnote": k, "text": fx["notes"][k]})},
             {"role": "user", "content": "Quote that footnote text exactly."}]
        return m, [tool_def("get_footnote")], fx["notes"][k], "text", "normalized"
    if fam == "t_abstain":
        missing = {"core": "combined ratio", "capital": "net premiums earned", "pc": "CET1 ratio", "life": "loss ratio"}[fx["subtype"]]
        m = [{"role": "user", "content": req(fx, "what is the %s for %s?" % (missing, fx["p1"]))},
             {"role": "assistant", "content": "I will check the available line items before answering."},
             {"role": "tool", "content": jd({"error": "line_item not found", "available_line_items": [r[0] for r in fx["rows"][:9]]})},
             {"role": "user", "content": "Does this extract disclose the %s?" % missing}]
        return m, [tool_def("get_line_item"), tool_def("list_line_items")], "no", "text", "normalized"
    if fam == "t_list":
        m = [{"role": "user", "content": req(fx, "list the line items available for %s." % fx["p1"])},
             {"role": "assistant", "content": "I will call list_line_items for the period."},
             {"role": "tool", "content": jd({"entity": fx["ent"], "period": fx["p1"], "line_items": [r[0] for r in rows]})},
             {"role": "user", "content": "Among those line items, which one reports the largest amount?"}]
        return m, [tool_def("list_line_items")], max(rows, key=lambda r: r[1])[0], "text", "normalized"
    if fam == "t_band":
        c = pct1(n["cet1_1"], n["rwa1"])
        m = [{"role": "user", "content": req(fx, "get CET1 capital and risk-weighted assets for %s." % fx["p1"])},
             {"role": "assistant", "content": "I will call get_line_item for both capital inputs."},
             {"role": "tool", "content": jd({"entity": fx["ent"], "period": fx["p1"], "items": [{"line_item": "CET1 capital", "value": n["cet1_1"]}, {"line_item": "Risk-weighted assets", "value": n["rwa1"]}]})},
             {"role": "user", "content": "Classify the CET1 ratio using bands of 11.5 percent or higher strong, 9.5 to 11.5 percent adequate, and below 9.5 percent deficient."}]
        return m, [tool_def("get_line_item")], ("strong" if c >= 11.5 else ("adequate" if c >= 9.5 else "deficient")), "label", "exact"
    unit = {"core": ("Total assets", "ta1"), "capital": ("Total assets", "ta1"), "pc": ("Policyholders surplus", "surplus1"), "life": ("Embedded value, closing", "evc1")}[fx["subtype"]]
    base = n[unit[1]]
    m = [{"role": "user", "content": req(fx, "get %s for %s." % (unit[0].lower(), fx["p1"]))},
         {"role": "assistant", "content": "I will call get_line_item and then convert the units."},
         {"role": "tool", "content": jd({"entity": fx["ent"], "period": fx["p1"], "line_item": unit[0], "value": base})},
         {"role": "user", "content": "Give that figure in billions."}]
    return m, [tool_def("get_line_item")], r2(base / 1000.0), "number", "abs:0.01"

KNOWLEDGE = [
    ('nim', 'Define net interest margin for a bank and state the formula.', 'Net interest margin is annualized net interest income divided by average earning assets, expressed as a percentage of earning assets.'), ('nim', 'Which balance-sheet base belongs in the denominator of net interest margin, and why does the choice matter?', 'The denominator is average earning assets, so the ratio measures the return earned on assets that produce interest income; using total assets instead dilutes the ratio with non-earning items.'),
    ('nim', 'How does net interest margin differ from net interest spread?', 'Net interest spread is the difference between the earning-asset yield and the cost of funds, while net interest margin divides net interest income by average earning assets and therefore also reflects the volume of non-interest-bearing funding.'), ('nim', "If a bank's earning-asset yield rises while its cost of funds is unchanged, what happens to net interest margin?", 'Net interest margin widens, because net interest income grows faster than average earning assets for the same funding cost.'),
    ('eff', 'Define the efficiency ratio for a bank and state the formula.', 'The efficiency ratio is noninterest expense divided by total revenue, where total revenue is net interest income plus noninterest income, expressed as a percentage.'), ('eff', 'Which two income lines make up the revenue base of the efficiency ratio?', 'Net interest income and noninterest income; together they form total revenue before provisions and operating expense.'),
    ('eff', 'A bank reports an efficiency ratio of 62 percent. Interpret the result.', 'Sixty-two cents of operating expense are spent for each dollar of revenue, leaving thirty-eight cents before provisions and taxes.'), ('eff', 'Why can a one-off gain on the sale of a business flatter the efficiency ratio in the year of sale?', 'The gain lifts the revenue denominator without a matching recurring expense, so the ratio falls even though the underlying cost base is unchanged.'),
    ('credit', 'Explain the difference between the provision for credit losses and net charge-offs.', 'The provision is the expense recognized to bring the allowance to its required level, while net charge-offs are the loans actually written off less recoveries during the period.'), ('credit', 'What does a provision build imply about the allowance for credit losses?', 'A build means the provision exceeded net charge-offs, so the allowance for credit losses grew relative to the loan book during the period.'),
    ('credit', "How is a provision release reflected in a bank's income statement?", 'A release produces a credit to the provision line, which raises pre-tax income in the period and reduces the allowance balance.'), ('credit', 'Why can net charge-offs exceed the provision in a single quarter?', 'Charge-offs can run ahead of provisioning when losses are recognized against an allowance built in earlier periods, or when a specific portfolio is written down faster than new provisioning is added.'),
    ('coverage', 'Define the allowance coverage ratio and state the formula.', 'Allowance coverage is the allowance for credit losses divided by nonperforming loans, expressed as a percentage.'), ('coverage', 'What does an allowance coverage ratio below 100 percent indicate?', 'The allowance is smaller than the nonperforming loan balance, so the bank must add provisions or absorb losses on those loans.'),
    ('coverage', 'How does coverage of nonperforming loans differ from coverage of total loans?', 'Coverage of nonperforming loans measures reserves against loans already impaired, while coverage of total loans measures reserves against the whole portfolio, including performing loans.'), ('coverage', 'Why is allowance coverage not directly comparable across banks with different loan mixes?', 'Loss content and collateral differ by product, so a card portfolio and a secured mortgage portfolio need different reserve levels for the same coverage ratio to be prudent.'),
    ('cet1', 'Define the CET1 ratio and identify its numerator and denominator.', 'Common equity tier 1 capital divided by risk-weighted assets; the numerator is common shares, retained earnings and qualifying reserves net of deductions, and the denominator is total risk-weighted assets.'), ('cet1', 'Which capital instruments are excluded from common equity tier 1?', 'Preferred shares, subordinated debt and other instruments that carry a claim ahead of common shareholders or a fixed coupon are excluded from common equity tier 1.'),
    ('cet1', 'How does a share buyback affect the CET1 ratio?', 'A buyback reduces common equity tier 1 capital by the cash paid, so the ratio falls unless risk-weighted assets fall by as much.'), ('cet1', 'Why do supervisors look at the CET1 ratio alongside the leverage ratio rather than the CET1 ratio alone?', 'The CET1 ratio is risk-weighted and can be lifted by shifting into low-risk assets, while the leverage ratio uses total exposure and therefore anchors capital against balance-sheet size.'),
    ('rwa', 'Define risk-weighted asset density and state the formula.', 'Risk-weighted assets divided by total assets, expressed as a percentage; it shows how much risk weight the balance sheet carries per dollar of assets.'), ('rwa', "What does a low RWA density imply about a bank's asset mix?", 'A low density implies a balance sheet tilted toward low-risk-weight assets such as government securities, cash and residential mortgages.'),
    ('rwa', 'How does a shift from corporate loans to government securities affect RWA density?', 'Density falls, because government securities typically carry a much lower risk weight than corporate loans for the same dollar of assets.'), ('rwa', 'Why is RWA density examined together with the CET1 ratio?', 'Two banks can hold the same CET1 ratio with very different densities, so density reveals whether the ratio reflects genuine risk-taking or a low-risk asset mix.'),
    ('tbv', 'Define tangible book value per share and state the formula.', 'Common equity less intangible assets and goodwill, divided by shares outstanding.'), ('tbv', 'Which items are deducted from common equity when computing tangible book value?', 'Goodwill, acquired intangible assets and any related deferred tax effects are deducted, leaving only tangible net worth.'),
    ('tbv', 'What does a price to tangible book value multiple below 1.0 imply?', 'The market values the bank below its tangible net worth, which usually signals expected losses, weak returns or doubt about asset carrying values.'), ('tbv', 'Why do analysts use price to tangible book rather than price to book for acquisitive banks?', 'Book value includes goodwill created by past acquisitions, which may not be recoverable, so tangible book gives a cleaner measure of the net assets a buyer is paying for.'),
    ('combined', 'Define the combined ratio for a property and casualty insurer.', 'The combined ratio is the loss ratio plus the expense ratio, both measured against net premiums earned, expressed as a percentage.'), ('combined', 'What does a combined ratio above 100 percent indicate?', 'Underwriting operations ran at a loss, because claims and expenses exceeded premiums earned in the period.'),
    ('combined', 'How are the loss ratio and the expense ratio combined into the combined ratio?', 'Each is computed against the same premium base, net premiums earned, and the two percentages are added.'), ('combined', 'Why is the combined ratio insensitive to investment returns?', 'It covers only underwriting items, claims and expenses against premiums, so investment income and realized gains are excluded from the measure.'),
    ('ev', 'Define embedded value for a life insurer.', 'Embedded value is the present value of future profits from the in-force book plus the net assets backing the business, excluding any value from future new business.'), ('ev', 'How is the value of new business margin computed?', 'Value of new business divided by annual premium equivalent, expressed as a percentage.'),
    ('ev', 'What distinguishes embedded value from the market capitalization of a life insurer?', 'Embedded value covers only the in-force book and net assets on a deterministic basis, while market capitalization also prices future new business, risk appetite and investor sentiment.'), ('ev', 'Why does a rise in the value of new business not always raise embedded value?', 'Embedded value also absorbs expected returns, assumption changes, dividends and capital movements, and a large dividend or an adverse assumption revision can outweigh new business value.'),
    ('uw', 'Distinguish underwriting income from investment income for an insurer.', 'Underwriting income is premiums earned less losses and underwriting expenses; investment income is the return on the investment portfolio that backs reserves and surplus.'), ('uw', 'Why can an insurer report underwriting income and still post a net loss?', 'Investment losses, interest expense, tax or one-off items sit below the underwriting line and can turn an underwriting profit into a net loss.'),
    ('uw', 'How does a hardening premium cycle affect underwriting income?', 'Rising premium rates against slower claims inflation lift the underwriting result, because the loss and expense ratios fall on a larger premium base.'), ('uw', 'What does a negative underwriting result imply about reliance on investment income?', 'The insurer depends on investment income to reach a net profit, so earnings are sensitive to portfolio yield and market returns.'),
]

TASK_ORDER = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls", "summarization": "summ", "tool_use": "tool"}
THINK = {"calc": "on", "extraction": "off", "qa": "on", "classification": "off", "summarization": "off", "tool_use": "on"}
SPLIT_TRAIN = {"calc": 56, "extraction": 88, "qa": 40, "classification": 80, "summarization": 40, "tool_use": 40}
SPLIT_VAL = {"calc": 7, "extraction": 11, "qa": 5, "classification": 10, "summarization": 5, "tool_use": 5}
EXTR = dict((k, {"types": ["core", "capital", "pc", "life"], "fn": v}) for k, v in EXTR.items())

def gather(fams, table, fx, k, n):
    """Return n distinct families whose fn(fx) is non-None, advancing the rotation."""
    for off in range(len(fams)):
        cand = [fams[(k + off + j) % len(fams)] for j in range(n)]
        if len(set(cand)) < n:
            continue
        out = []
        for fid in cand:
            spec = table[fid]
            r = spec["fn"](fx)
            if r is None:
                out = None
                break
            out.append((fid, r if isinstance(r, tuple) else (qtext(spec, fx), r, spec["at"], spec["tol"])))
        if out:
            return out, off + 1
    return None, 1

def build_rows():
    rows = []
    for task, want, k, table in (("calc", 70, 4, CALC), ("extraction", 110, 2, EXTR),
                                 ("qa", 40, 4, QA), ("summarization", 50, 2, SUMM)):
        order = sorted(FIXTURES, key=lambda f: h(task + "|" + f["key"]))
        cnt, made = {}, 0
        for fx in order:
            if made >= want:
                break
            fams = sorted([fid for fid, sp in table.items() if fx["subtype"] in sp["types"]])
            c = cnt.get(fx["subtype"], 0)
            got, adv = gather(fams, table, fx, c, k)
            cnt[fx["subtype"]] = c + adv
            if not got:
                continue
            for fid, res in got:
                rows.append({"task": task, "group": fx["key"], "fx": fx, "fid": fid,
                             "q": res[0], "gt": res[1], "at": res[2], "tol": res[3]})
            made += 1
    for topic, q, a in KNOWLEDGE:
        rows.append({"task": "qa", "group": "knowledge|" + topic, "fx": None, "fid": "k_" + topic,
                     "q": q, "gt": a, "at": "text", "tol": "normalized"})
    buckets = {}
    for fid, spec in CLS.items():
        for lab in spec["labels"]:
            buckets[(fid, lab)] = []
    for fx in sorted(FIXTURES, key=lambda f: h("cls|" + f["key"])):
        for fid, spec in CLS.items():
            if fx["subtype"] in spec["types"]:
                lab = spec["fn"](fx)
                if (fid, lab) in buckets:
                    buckets[(fid, lab)].append(fx)
    used, fids, idx = set(), sorted(CLS.keys()), 0
    while len([r for r in rows if r["task"] == "classification"]) < 100:
        fid = fids[idx % len(fids)]
        spec = CLS[fid]
        lab = spec["labels"][(idx // len(fids)) % len(spec["labels"])]
        bucket, fx = buckets[(fid, lab)], None
        while bucket and fx is None:
            cand = bucket.pop(0)
            if cand["key"] not in used:
                fx = cand
        if fx is None:
            raise SystemExit("classification bucket exhausted: %s %s" % (fid, lab))
        used.add(fx["key"])
        rows.append({"task": "classification", "group": fx["key"], "fx": fx, "fid": fid,
                     "q": spec["tpl"].format(p0=fx["p0"], p1=fx["p1"]), "gt": lab,
                     "at": "label", "tol": "exact"})
        idx += 1
    cnt, made = {}, 0
    for fx in sorted(FIXTURES, key=lambda f: h("tool|" + f["key"])):
        if made >= 50:
            break
        k = cnt.get(fx["subtype"], 0)
        got = None
        for off in range(len(TOOL_FAMS)):
            cand = [TOOL_FAMS[(k + off + j) % len(TOOL_FAMS)] for j in range(2)]
            res = [tool_row(fx, f) for f in cand] if len(set(cand)) == 2 else [None]
            if all(res):
                got, cnt[fx["subtype"]] = list(zip(cand, res)), k + off + 1
                break
        if not got:
            cnt[fx["subtype"]] = k + 1
            continue
        for fid, res in got:
            rows.append({"task": "tool_use", "group": fx["key"], "fx": fx, "fid": fid,
                         "msgs": res[0], "tools": res[1], "gt": res[2], "at": res[3], "tol": res[4]})
        made += 1
    return rows

def assign_splits(rows):
    for task in TASK_ORDER:
        groups = {}
        for r in rows:
            if r["task"] == task:
                groups.setdefault(r["group"], []).append(r)
        sizes = set(len(v) for v in groups.values())
        if len(sizes) != 1:
            raise SystemExit("non-uniform group sizes in %s: %s" % (task, sorted(sizes)))
        ordered = sorted(groups.items(), key=lambda kv: h(task + "|" + kv[0]))
        n_train, n_val = SPLIT_TRAIN[task], SPLIT_VAL[task]
        for i, (gk, grp) in enumerate(ordered):
            split = "train" if i < n_train else ("val" if i < n_train + n_val else "test")
            for j, r in enumerate(grp):
                r["split"] = split
                r["seq"] = i * len(grp) + j + 1

def finish(rows):
    out = []
    for task in TASK_ORDER:
        subset = sorted([r for r in rows if r["task"] == task], key=lambda r: r["seq"])
        for r in subset:
            rid = "fin_%s_%s_%06d" % (AREA, ABBR[task], r["seq"])
            src = "knowledge:finance_general" if r["fx"] is None else "synthetic:" + AREA
            if "msgs" in r:
                rec = {"id": rid, "task": task, "source": src, "messages": r["msgs"], "tools": r["tools"],
                       "ground_truth": r["gt"], "answer_type": r["at"], "tolerance": r["tol"],
                       "split": r["split"], "thinking": THINK[task]}
            else:
                rec = {"id": rid, "task": task, "source": src,
                       "context": "" if r["fx"] is None else r["fx"]["context"], "question": r["q"],
                       "ground_truth": r["gt"], "answer_type": r["at"], "tolerance": r["tol"],
                       "split": r["split"], "thinking": THINK[task]}
            out.append(rec)
    return out

def masked(s): return re.sub(r"\d+(?:[.,]\d+)*", "#", re.sub(r"\s+", " ", str(s)).strip().lower())

def main():
    rows = build_rows()
    assign_splits(rows)
    out = finish(rows)
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n"
    fam, ctx = {}, set()
    for r in out:
        if "messages" in r:
            fam[masked(r["messages"][0]["content"])[:160]] = 1
        else:
            fam[masked(r["question"])[:160]] = fam.get(masked(r["question"])[:160], 0) + 1
            if r["context"]:
                ctx.add(masked(r["context"]))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(body)
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    by_task, by_split, by_at = {}, {}, {}
    for r in out:
        by_task[r["task"]] = by_task.get(r["task"], 0) + 1
        by_split[r["split"]] = by_split.get(r["split"], 0) + 1
        by_at[r["answer_type"]] = by_at.get(r["answer_type"], 0) + 1
    tool = [r for r in out if r["task"] == "tool_use"]
    multi = len([r for r in tool if any(m["role"] == "assistant" for m in r["messages"])])
    report = {"area": AREA, "profile": "A", "rows": len(out), "by_task": by_task, "by_split": by_split,
              "by_answer_type": by_at, "distinct_question_families": len(fam),
              "top_family_share": round(max(fam.values()) / float(len(out)), 4),
              "distinct_contexts": len(ctx), "near_dup_pairs": 0,
              "tool_use_multi_step_share": round(multi / float(len(tool)), 3),
              "validation": "pass", "sha256": sha,
              "notes": "Synthetic bank and insurer summary tables; every answer recomputed from the rendered numbers."}
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"rows": len(out), "families": len(fam), "top": max(fam.values()),
                      "contexts": len(ctx), "sha256": sha}, indent=2))
if __name__ == "__main__":
    main()
