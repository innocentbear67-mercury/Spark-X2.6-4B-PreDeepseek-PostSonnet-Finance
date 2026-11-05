#!/usr/bin/env python3
"""Deterministic generator for the fraud_forensics area (profile B).

Builds 1000 synthetic forensic-accounting rows: accrual red flags, margin versus
operating cash flow divergence, Beneish-style component screens, related party
disclosures, auditor changes and qualifications, restatements, going concern
indicators and leading-digit screens.  Every ground_truth number is computed in
code from the same values written into the context table.
"""
import hashlib
import json
import os
import random
import re

RNG = random.Random(42); AREA = "fraud_forensics"
HERE = os.path.dirname(os.path.abspath(__file__))

COMPANIES = [("Halcyon Grid Utilities", "Utilities", "30 September", "USD"),("Meridian Bancorp", "Banking", "31 December", "USD"),("Kestrel Foods", "Consumer staples", "31 May", "USD"),("Ardent Ridge Mining", "Materials", "31 December", "AUD"),("Solstice Diagnostics", "Healthcare", "31 March", "USD"),("Northwind Logistics", "Industrials", "31 December", "EUR"),("Cobalt Harbor Shipping", "Transport", "30 June", "GBP"),("Vantage Point Software", "Technology", "31 January", "USD"),("Larkspur Retail Group", "Retail", "31 January", "GBP"),("Ironwood Timber", "Forestry", "31 December", "CAD"),("Silverbrook Pharma", "Pharmaceuticals", "31 December", "CHF"),("Tidewater Aquaculture", "Food production", "30 June", "USD"),("Emberline Energy", "Oil and gas", "31 December", "CAD"),("Granite Peak Insurance", "Insurance", "31 December", "USD"),("Willow Bend Hotels", "Hospitality", "31 December", "EUR"),("Peregrine Aerospace", "Aerospace", "31 December", "USD"),("Blue Harbor Chemicals", "Chemicals", "30 September", "EUR"),("Marrowgate Property", "Real estate", "31 December", "GBP"),("Sable Ridge Motors", "Automotive", "31 December", "EUR"),("Quarrystone Cement", "Building materials", "31 December", "USD"),("Alder Grove Biotech", "Biotechnology", "31 December", "USD"),("Copperline Telecom", "Telecom", "31 December", "CAD"),("Frostmere Dairy", "Dairy", "31 March", "USD"),("Halstead Marine", "Marine equipment", "30 June", "SEK"),]
HEAD = ["Annual report extract", "Internal forensic working paper"]; NC = len(COMPANIES); PER_TYPE = 48

RP_PRE = ["Aldergate", "Bramwell", "Cedarhill", "Dunmore", "Elmsworth", "Fairhaven","Glenmoor", "Hartwell", "Ingleby", "Jarrow", "Kelbrook", "Lanchester","Marlowe", "Netherby", "Oakham", "Pemberton", "Quarrendon", "Ravensworth","Stanmore", "Thornbury", "Ullswater", "Verity", "Westray", "Yarrow"]
RP_SUF = ["Holdings", "Trading", "Investments", "Logistics", "Partners", "Industries","Resources", "Ventures"]
RP_LEGAL = ["Ltd", "BV", "GmbH", "SA", "Pty Ltd"]

AUD_FIRMS = ["Ridgeway and Pike LLP", "Ashcombe Audit Partners", "Bellwether Assurance","Carrick and Vale", "Dunmore Audit LLP", "Ellsworth Assurance Group","Fenwick and Rowe", "Gainsborough Audit", "Hollins Vale LLP","Ingram and Cross", "Jarvis Field Assurance", "Kingsmere Audit Partners"]

SEGMENTS = ["Clinical labs", "Imaging", "Diagnostics", "Research services", "Wholesale","Retail", "Online", "Industrial", "Aftermarket", "Solutions", "Support","Licensing", "Freight", "Contract", "Distribution", "Services", "Parts","Export", "Domestic", "Maintenance"]

FIXTURES = []; BY_TYPE = {}

def rnd(x, n=1):
    v = round(float(x) + 0.0, n)
    return 0.0 if v == 0 else v

def tbl(headers, rows):
    out = ["| " + " | ".join(str(h) for h in headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)

def add(ftype, idx, name, ctx, data):
    co = COMPANIES[idx % NC]; var = idx // NC; key = ftype + "|" + co[0] + "|" + str(var)
    fx = {"key": key, "type": ftype, "company": co[0], "ctx": ctx, "data": data}; FIXTURES.append(fx)
    BY_TYPE.setdefault(ftype, []).append(fx)
    return fx

def head(idx, title):
    co = COMPANIES[idx % NC]; var = idx // NC
    return (co[0] + " - " + title + "\n" + HEAD[var] + "\nSector: " + co[1] + ". Fiscal year end: " + co[2] + ". Reporting currency: " + co[3] + ".\n\n")

# --------------------------------------------------------------------------- accrual
ACC_PROF = [(12.0, 1.0), (-4.0, 12.0), (13.5, 14.5), (-7.0, -6.0)]

def build_accrual(idx):
    prof = idx % 4; ex_rec = ACC_PROF[prof][0] + RNG.uniform(-1.2, 1.2)
    ex_inv = ACC_PROF[prof][1] + RNG.uniform(-1.2, 1.2); rev0 = RNG.randrange(340, 6600)
    g1 = RNG.uniform(-0.05, 0.16); g2 = RNG.uniform(-0.03, 0.20)
    rev = [int(round(rev0)),int(round(rev0 * (1 + g1))),int(round(rev0 * (1 + g1) * (1 + g2)))]
    cogs = [int(round(r * RNG.uniform(0.58, 0.79))) for r in rev]; d24 = RNG.uniform(42, 88)
    d23 = d24 * RNG.uniform(0.95, 1.05); rec = [int(round(rev[0] * d23 / 365)), int(round(rev[1] * d24 / 365)), 0]
    rec[2] = int(round(rec[1] * (rev[2] / float(rev[1])) * (1 + ex_rec / 100.0))); i24 = RNG.uniform(0.12, 0.28)
    i23 = i24 * RNG.uniform(0.92, 1.08); inv = [int(round(cogs[0] * i23)), int(round(cogs[1] * i24)), 0]
    inv[2] = int(round(inv[1] * (cogs[2] / float(cogs[1])) * (1 + ex_inv / 100.0)))
    alw = [int(round(rec[0] * RNG.uniform(0.030, 0.085))),int(round(rec[1] * RNG.uniform(0.030, 0.085))),int(round(rec[2] * RNG.uniform(0.030, 0.085)))]
    net = [rec[i] - alw[i] for i in range(3)]
    body = tbl(["Item", "FY2025", "FY2024", "FY2023"],[["Revenue"] + [rev[i] for i in (2, 1, 0)],["Trade receivables, gross"] + [rec[i] for i in (2, 1, 0)],["Allowance for credit losses"] + [alw[i] for i in (2, 1, 0)],["Trade receivables, net"] + [net[i] for i in (2, 1, 0)],["Inventories"] + [inv[i] for i in (2, 1, 0)],["Cost of sales"] + [cogs[i] for i in (2, 1, 0)]])
    ctx = ("Units: $ in millions except percentages in percent.\n\n" + head(idx, "accrual review of working capital accounts") + "Year-on-year comparison of revenue with the receivables and inventory balances.\n\n" + body + "\n\nNote: gross trade receivables are stated before the allowance; days metrics " "should use a 365-day year. Group policy flags any spread above 5.0 percentage points.")
    add("accrual", idx, COMPANIES[idx % NC][0], ctx,{"rev": rev, "recg": rec, "alw": alw, "inv": inv, "cogs": cogs})

# --------------------------------------------------------------------------- cashflow
CF_PROF = ["cash", "accrual", "mixed"]

def build_cashflow(idx):
    prof = idx % 3; rev = [RNG.randrange(500, 7200), 0]
    rev[1] = int(round(rev[0] * (1 + RNG.uniform(-0.04, 0.17)))); gm0 = RNG.uniform(0.26, 0.54)
    gm1 = min(max(gm0 * RNG.uniform(0.92, 1.08), 0.16), 0.62)
    gp = [int(round(rev[0] * gm0)), int(round(rev[1] * gm1))]; om0 = RNG.uniform(0.07, 0.24)
    om1 = min(max(om0 * RNG.uniform(0.88, 1.12), 0.02), 0.30)
    op = [int(round(gp[0] * om0 / gm0)), int(round(gp[1] * om1 / gm1))]; nm0 = om0 * RNG.uniform(0.58, 0.82)
    nm1 = nm0 * RNG.uniform(0.92, 1.08); ni = [int(round(rev[0] * nm0)), int(round(rev[1] * nm1))]
    mult = {"cash": (1.20, 1.45), "accrual": (0.35, 0.68), "mixed": (0.88, 1.02)}[CF_PROF[prof]]
    f0 = RNG.uniform(mult[0], mult[1]); f1 = f0 * RNG.uniform(0.96, 1.04)
    cfo = [int(round(ni[0] * f0)), int(round(ni[1] * f1))]
    capex = [int(round(cfo[i] * RNG.uniform(0.30, 0.75))) for i in range(2)]
    dep = [int(round(rev[i] * RNG.uniform(0.03, 0.07))) for i in range(2)]
    ta = [int(round(rev[i] * RNG.uniform(0.95, 1.65))) for i in range(2)]
    body = tbl(["Item", "FY2025", "FY2024"],[["Revenue"] + [rev[i] for i in (1, 0)],["Gross profit"] + [gp[i] for i in (1, 0)],["Operating income"] + [op[i] for i in (1, 0)],["Net income"] + [ni[i] for i in (1, 0)],["Cash from operations"] + [cfo[i] for i in (1, 0)],["Capital expenditure"] + [capex[i] for i in (1, 0)],["Depreciation and amortisation"] + [dep[i] for i in (1, 0)],["Total assets at year end"] + [ta[i] for i in (1, 0)]])
    ctx = ("Units: $ in millions except percentages in percent and ratios in multiples.\n\n" + head(idx, "earnings quality review: margin against operating cash flow") + "Extracted from the consolidated statement of cash flows and the income statement.\n\n" + body + "\n\nNote: total assets at the start of FY2024 were " + str(int(round(ta[0] * RNG.uniform(0.92, 1.08)))) + ". Operating cash flow margin uses revenue as the denominator.")
    add("cashflow", idx, COMPANIES[idx % NC][0], ctx,{"rev": rev, "gp": gp, "op": op, "ni": ni, "cfo": cfo, "capex": capex, "ta": ta})

# --------------------------------------------------------------------------- beneish
def build_beneish(idx):
    sales = [RNG.randrange(620, 7600), 0]; sales[1] = int(round(sales[0] * RNG.uniform(0.95, 1.28)))
    gm0 = RNG.uniform(0.28, 0.55); gm1 = min(max(gm0 * RNG.uniform(0.90, 1.10), 0.18), 0.60)
    cogs = [int(round(sales[0] * (1 - gm0))), int(round(sales[1] * (1 - gm1)))]
    rec = [int(round(sales[0] * RNG.uniform(0.11, 0.26))), 0]
    if idx % 2 == 0:
        dsri = RNG.uniform(1.16, 1.40)
    else:
        dsri = RNG.uniform(0.72, 0.90)
    rec[1] = int(round(rec[0] * (sales[1] / float(sales[0])) * dsri))
    ta = [int(round(sales[0] * RNG.uniform(1.00, 1.55))), 0]; ta[1] = int(round(ta[0] * RNG.uniform(0.96, 1.30)))
    ca = [int(round(ta[0] * RNG.uniform(0.30, 0.46))), 0]; ppe = [int(round(ta[0] * RNG.uniform(0.24, 0.38))), 0]
    ca[1] = int(round(ta[1] * RNG.uniform(0.30, 0.46))); ppe[1] = int(round(ta[1] * RNG.uniform(0.24, 0.38)))
    sga = [int(round(sales[0] * RNG.uniform(0.07, 0.21))), 0]
    sga[1] = int(round(sales[1] * (sga[0] / float(sales[0])) * RNG.uniform(0.92, 1.12)))
    cl = [int(round(ta[i] * RNG.uniform(0.16, 0.36))) for i in range(2)]
    ltd = [int(round(ta[i] * RNG.uniform(0.10, 0.32))) for i in range(2)]
    ni = [int(round(sales[0] * RNG.uniform(0.03, 0.10))), 0]; ni[1] = int(round(ni[0] * RNG.uniform(0.85, 1.25)))
    if idx % 2 == 1:
        cfo = [int(round(ni[i] * RNG.uniform(1.20, 1.60))) for i in range(2)]
    else:
        cfo = [int(round(ni[i] * RNG.uniform(0.35, 0.70))) for i in range(2)]
    dep = [int(round(ppe[i] * RNG.uniform(0.08, 0.16))) for i in range(2)]
    body = tbl(["Item", "FY2025", "FY2024"],[["Revenue"] + [sales[i] for i in (1, 0)],["Trade receivables, gross"] + [rec[i] for i in (1, 0)],["Cost of sales"] + [cogs[i] for i in (1, 0)],["Selling general and administrative"] + [sga[i] for i in (1, 0)],["Current assets"] + [ca[i] for i in (1, 0)],["Net property plant and equipment"] + [ppe[i] for i in (1, 0)],["Total assets"] + [ta[i] for i in (1, 0)],["Current liabilities"] + [cl[i] for i in (1, 0)],["Long-term debt"] + [ltd[i] for i in (1, 0)],["Net income"] + [ni[i] for i in (1, 0)],["Cash from operations"] + [cfo[i] for i in (1, 0)],["Depreciation"] + [dep[i] for i in (1, 0)]])
    ctx = ("Units: $ in millions except percentages in percent and ratios in multiples.\n\n" + head(idx, "Beneish component screen: input data") + "The table supplies every input required for the eight Beneish components. " "Gross margin is revenue less cost of sales divided by revenue.\n\n" + body + "\n\nNote: all balances are year-end. No acquisitions or disposals occurred in either year.")
    add("beneish", idx, COMPANIES[idx % NC][0], ctx,{"sales": sales, "rec": rec, "cogs": cogs, "ca": ca, "ppe": ppe, "ta": ta,"sga": sga, "cl": cl, "ltd": ltd, "ni": ni, "cfo": cfo, "dep": dep})

COMP_KEYS = ["DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "LVGI", "TATA"]

def mscore(c):
    return (-4.84 + 0.920 * c["DSRI"] + 0.528 * c["GMI"] + 0.404 * c["AQI"] + 0.892 * c["SGI"] + 0.115 * c["DEPI"] - 0.172 * c["SGAI"] + 4.679 * c["TATA"] - 0.327 * c["LVGI"])

def build_bscore(idx):
    want_above = (idx // 2) % 2 == 0; vals = None
    for _ in range(600):
        v = {"DSRI": RNG.uniform(0.92, 1.52), "GMI": RNG.uniform(0.90, 1.18),"AQI": RNG.uniform(0.88, 1.34), "SGI": RNG.uniform(0.94, 1.30),"DEPI": RNG.uniform(0.88, 1.22), "SGAI": RNG.uniform(0.90, 1.16),"LVGI": RNG.uniform(0.84, 1.28), "TATA": RNG.uniform(0.01, 0.14)}
        v = dict((k, round(x, 3)) for k, x in v.items())
        if (mscore(v) > -1.78) == want_above:
            vals = v
            break
    if vals is None:
        vals = dict((k, round(RNG.uniform(0.95, 1.10), 3)) for k in COMP_KEYS)
        vals["TATA"] = 0.115 if want_above else 0.012
    body = tbl(["Component", "Value"],[[k, ("%.3f" % vals[k])] for k in COMP_KEYS])
    ctx = ("Units: ratios in multiples except TATA, which is a proportion of total assets.\n\n" + head(idx, "Beneish M-score component summary") + "The eight components below were computed from the FY2025 and FY2024 statements.\n\n" + body + "\n\nNote: a score above the -1.78 cutoff is treated as a manipulation flag.")
    add("bscore", idx, COMPANIES[idx % NC][0], ctx, {"comp": vals})

# --------------------------------------------------------------------------- related party
REL_PROF = ["subsidiary", "associate", "joint_venture", "key_management", "controlling_shareholder"]
REL_ROLE = { "subsidiary": "Voting interest 100 percent; fully consolidated","associate": "Voting interest 34 percent; two of seven board seats","joint_venture": "Voting interest 50 percent; joint control by agreement","key_management": "Owned by the chief financial officer and spouse","controlling_shareholder": "Voting interest 58 percent; controls the board",}
REL_NATURE = [("Sale of goods", "sale"), ("Sale of services", "sale"),("Purchase of packaging", "purchase"), ("Purchase of freight services", "purchase"),("Loan advanced", "financing"), ("Guarantee issued", "guarantee")]

def build_related(idx):
    rel = REL_PROF[idx % 5]; conc = idx % 3; share = [0.18, 0.06, 0.025][conc] * RNG.uniform(0.90, 1.12)
    group_rev = RNG.randrange(900, 7400); cogs = int(round(group_rev * RNG.uniform(0.58, 0.76))); rows = []
    focal_amt = int(round(group_rev * share))
    for j in range(6):
        nm = (RP_PRE[(idx * 3 + j * 5) % len(RP_PRE)] + " " + RP_SUF[(idx + j) % len(RP_SUF)] + " " + RP_LEGAL[(idx + j) % len(RP_LEGAL)])
        if j == 0:
            r, amt = rel, max(focal_amt, 12)
        else:
            r = REL_PROF[(idx + j) % 5]; amt = max(int(round(focal_amt * RNG.uniform(0.04, 0.55))), 1)
        nat, cat = REL_NATURE[(idx + j) % len(REL_NATURE)]
        appr = "Audit committee" if amt > 0.02 * group_rev else "Not required"
        rows.append({"name": nm, "role": REL_ROLE[r], "rel": r, "nature": nat, "cat": cat,"a25": amt, "a24": max(int(round(amt * RNG.uniform(0.62, 1.30))), 1),"recv": int(round(amt * RNG.uniform(0.0, 0.45))),"pay": int(round(amt * RNG.uniform(0.0, 0.30))),"approval": appr})
    rows.sort(key=lambda x: -x["a25"]); disp = rows[:]; RNG.shuffle(disp)
    body = tbl(["Counterparty", "Ownership or role", "Nature of transaction", "FY2025 amount","FY2024 amount", "Balance receivable FY2025", "Balance payable FY2025", "Approved by"],[[r["name"], r["role"], r["nature"], r["a25"], r["a24"], r["recv"], r["pay"],r["approval"]] for r in disp])
    ctx = ("Units: $ in millions except percentages in percent.\n\n" + head(idx, "related party transactions disclosure") + "Group revenue for FY2025 was " + str(group_rev) + ". Cost of sales for FY2025 was " + str(cogs) + ". Group policy requires audit committee approval for any related party " "transaction above 2 percent of group revenue.\n\n" + body + "\n\nThe counterparty list is complete; no other related party transactions were entered " "into during FY2025.")
    add("related", idx, COMPANIES[idx % NC][0], ctx,{"rows": rows, "group_rev": group_rev, "cogs": cogs})

# --------------------------------------------------------------------------- auditor
OPINIONS = { "unqualified": ("In our opinion, the consolidated financial statements present fairly, in all " "material respects, the financial position of the group as at the year end and " "its financial performance for the year then ended."),"qualified": ("In our opinion, except for the effects of the matter described in the Basis for " "Qualified Opinion section, the consolidated financial statements present fairly, " "in all material respects, the financial position of the group as at the year end."),"adverse": ("In our opinion, because of the significance of the matter described in the Basis for " "Adverse Opinion section, the consolidated financial statements do not present fairly " "the financial position of the group as at the year end."),"disclaimer": ("Because of the significance of the matter described in the Basis for Disclaimer of " "Opinion section, we have not been able to obtain sufficient appropriate audit " "evidence. Accordingly, we do not express an opinion on the consolidated financial " "statements."),}
OP_LIST = ["unqualified", "qualified", "adverse", "disclaimer"]
CHANGES = { "planned_rotation": "The audit committee confirmed the firm will not be reappointed after completion of the mandatory partner rotation cycle.","disagreement": "The firm was removed following a disagreement over the capitalisation of development costs.","resignation": "The firm resigned with immediate effect, citing the group's failure to provide requested information.","fee_dispute": "The audit committee replaced the firm after negotiations over the proposed FY2026 audit fee failed.",}
CH_LIST = ["planned_rotation", "disagreement", "resignation", "fee_dispute"]
KAMS = ["Revenue recognition on long-term contracts", "Valuation of inventory","Impairment of goodwill", "Provisions for customer rebates","Capitalisation of development costs", "Allowance for credit losses"]

def build_auditor(idx):
    op = OP_LIST[idx % 4]; ch = CH_LIST[(idx + idx // 4) % 4]; firm = AUD_FIRMS[idx % len(AUD_FIRMS)]
    first_fy = 2016 + (idx % 8); tenure = 2025 - first_fy + 1; nkam = 1 + (idx % 4)
    kam = [KAMS[(idx + j) % len(KAMS)] for j in range(nkam)]; audit25 = RNG.randrange(90, 1400)
    audit24 = int(round(audit25 * RNG.uniform(0.82, 1.10)))
    nonaudit = int(round(audit25 * RNG.uniform(0.15, 1.20)))
    facts = tbl(["Item", "Detail"],[["Auditor", firm], ["First appointed", "FY" + str(first_fy)],["Consecutive years served", tenure], ["Audit fee FY2025", audit25],["Audit fee FY2024", audit24], ["Non-audit fees FY2025", nonaudit]])
    kam_txt = "\n".join("- " + k for k in kam)
    ctx = ("Units: $ in millions except percentages in percent.\n\n" + head(idx, "auditor report and independence review") + "The audit committee paper records the following facts and extracts.\n\n" + facts + "\n\nOpinion paragraph: \"" + OPINIONS[op] + "\"\n\nKey audit matters:\n" + kam_txt + "\n\nChange of auditor: " + CHANGES[ch])
    add("auditor", idx, COMPANIES[idx % NC][0], ctx,{"firm": firm, "first_fy": first_fy, "tenure": tenure, "opinion": op, "kam": kam,"audit25": audit25, "audit24": audit24, "nonaudit": nonaudit, "change": ch})

# --------------------------------------------------------------------------- restatement
RES_KIND = ["error_correction", "reclassification", "accounting_policy_change", "fraud"]
RES_REASON = { "error_correction": "Sales had been recognised before control transferred to the customer; the error was identified by the external auditor during the interim review.","reclassification": "Freight costs were reclassified from cost of sales to distribution expenses; there is no effect on net income or equity.","accounting_policy_change": "The group changed from weighted average to first-in first-out for inventory and applied the change retrospectively.","fraud": "Revenue had been deliberately overstated through fictitious sales; the matter was identified by the regulator and three employees were dismissed.",}
RES_WHO = {"error_correction": "external auditor", "reclassification": "group finance team","accounting_policy_change": "audit committee", "fraud": "financial regulator"}

def build_restate(idx):
    kind = RES_KIND[idx % 4]; rev_o = RNG.randrange(700, 6800)
    cogs_o = int(round(rev_o * RNG.uniform(0.58, 0.78))); ni_o = int(round(rev_o * RNG.uniform(0.04, 0.13)))
    inv_o = int(round(cogs_o * RNG.uniform(0.14, 0.30)))
    if kind == "reclassification":
        d_rev, d_cogs, d_inv = 0, -int(round(cogs_o * RNG.uniform(0.03, 0.07))), 0; d_ni = 0
    elif kind == "accounting_policy_change":
        d_rev = 0; d_cogs = int(round(cogs_o * RNG.uniform(-0.02, 0.02))); d_inv = -d_cogs * 3; d_ni = -d_cogs
    else:
        d_rev = -int(round(rev_o * RNG.uniform(0.03, 0.11))); d_cogs = int(round(cogs_o * RNG.uniform(0.01, 0.05)))
        d_inv = -int(round(inv_o * RNG.uniform(0.06, 0.18))); d_ni = d_rev - d_cogs
    rev_r, cogs_r, inv_r = rev_o + d_rev, cogs_o + d_cogs, inv_o + d_inv; ni_r = ni_o + d_ni
    body = tbl(["Line item", "Originally reported FY2024", "Restated FY2024"],[["Revenue", rev_o, rev_r], ["Cost of sales", cogs_o, cogs_r],["Gross profit", rev_o - cogs_o, rev_r - cogs_r],["Net income", ni_o, ni_r], ["Inventories", inv_o, inv_r]])
    ctx = ("Units: $ in millions except percentages in percent.\n\n" + head(idx, "restatement and error correction note") + "The FY2024 comparative figures were restated in the FY2025 annual report.\n\n" + body + "\n\nReason for the restatement: " + RES_REASON[kind] + "\nIdentified by: " + RES_WHO[kind] + ".")
    add("restate", idx, COMPANIES[idx % NC][0], ctx,{"orig": {"rev": rev_o, "cogs": cogs_o, "ni": ni_o, "inv": inv_o},"rest": {"rev": rev_r, "cogs": cogs_r, "ni": ni_r, "inv": inv_r},"kind": kind, "who": RES_WHO[kind]})

# --------------------------------------------------------------------------- going concern
GC_LEVELS = ["severe", "moderate", "mild", "none"]
GC_BANDS = {"severe": (2.2, 5.0, 0.55, 0.75), "moderate": (7.0, 11.0, 0.85, 0.97),"mild": (13.0, 17.0, 1.03, 1.17), "none": (21.0, 33.0, 1.30, 1.85)}
GC_IND = ["Net loss reported for a second consecutive year","Loss of a distribution customer representing 31 percent of revenue","Revolving facility matures within fourteen months","Covenant waiver expires within twelve months","Negative operating cash flow for the second consecutive year"]

def build_gc(idx):
    level = GC_LEVELS[idx % 4]; lo, hi, cr_lo, cr_hi = GC_BANDS[level]; runway = RNG.uniform(lo, hi)
    burn = RNG.randrange(8, 90); undrawn = int(round(burn * RNG.uniform(1.0, min(6.0, runway * 0.6))))
    cash = max(int(round(runway * burn - undrawn)), 5); cl = RNG.randrange(300, 2600)
    ca = int(round(cl * RNG.uniform(cr_lo, cr_hi))); tl = int(round(cl * RNG.uniform(1.4, 2.9)))
    eq = max(int(round(tl * RNG.uniform(0.10, 0.62))), 10); nloss = -int(round(RNG.randrange(30, 420)))
    ocf = -int(round(RNG.randrange(40, 460)))
    body = tbl(["Item", "FY2025", "FY2024"],[["Cash and cash equivalents", cash, int(round(cash * RNG.uniform(1.1, 2.2)))],["Undrawn revolving facility", undrawn, int(round(undrawn * RNG.uniform(0.6, 1.4)))],["Current assets", ca, int(round(ca * RNG.uniform(0.95, 1.25)))],["Current liabilities", cl, int(round(cl * RNG.uniform(0.85, 1.15)))],["Total liabilities", tl, int(round(tl * RNG.uniform(0.90, 1.10)))],["Shareholders' equity", eq, int(round(eq * RNG.uniform(0.95, 1.35)))],["Net loss", nloss, int(round(nloss * RNG.uniform(0.5, 1.1)))],["Cash used in operations", ocf, int(round(ocf * RNG.uniform(0.5, 1.1)))],["Average monthly cash burn", burn, int(round(burn * RNG.uniform(0.7, 1.2)))]])
    n_ind = 2 + (idx % 3); inds = [GC_IND[(idx + j) % len(GC_IND)] for j in range(n_ind)]
    ind_txt = "\n".join("- " + s for s in inds)
    ctx = ("Units: $ in millions except ratios in multiples.\n\n" + head(idx, "going concern assessment working paper") + "Conditions noted during the FY2025 close:\n" + ind_txt + "\n\n" + body + "\n\nFacility terms: the revolving facility requires interest cover of at least 2.50 times " "and net debt to EBITDA below 3.50 times. Average monthly cash burn is stated in the table. " "Northbank Commercial granted a waiver of the net debt covenant until 31 March 2026.")
    add("gc", idx, COMPANIES[idx % NC][0], ctx,{"cash": cash, "undrawn": undrawn, "burn": burn, "ca": ca, "cl": cl, "tl": tl,"eq": eq, "level": level, "covenant": 2.5, "waiver": "31 March 2026","lender": "Northbank Commercial", "inds": inds})

# --------------------------------------------------------------------------- digits
DIG_PATTERN = [4, 2, 4, 3, 4, 5, 4, 1]

def build_digits(idx):
    n1 = DIG_PATTERN[idx % len(DIG_PATTERN)]; n3 = 1 + (idx % 3); digs = [1] * n1 + [3] * n3 + [4]
    others = [4, 2, 5, 6, 7, 8, 9]; j = 0
    while len(digs) < 12:
        digs.append(others[(idx + j) % len(others)]); j += 1
    RNG.shuffle(digs); amounts, names = [], []
    for k, d in enumerate(digs):
        mag = 10 ** (2 + ((idx + k) % 3)); amounts.append(d * mag + RNG.randrange(0, mag))
        names.append(SEGMENTS[(idx + k) % len(SEGMENTS)])
    body = tbl(["Reporting unit", "Reported amount"],[[names[k], amounts[k]] for k in range(12)])
    ctx = ("Units: $ in millions except percentages in percent.\n\n" + head(idx, "leading digit review of reported figures") + "Twelve reported figures were selected for a first-digit distribution check. " "Benford expected frequencies for first digits 1 to 9 are 30.1, 17.6, 12.5, 9.7, 7.9, 6.7, " "5.8, 5.1 and 4.6 percent.\n\n" + body)
    add("digits", idx, COMPANIES[idx % NC][0], ctx,{"amounts": amounts, "names": names, "n1": n1, "n3": n3})

def build_all():
    for i in range(PER_TYPE):
        build_accrual(i)
    for i in range(PER_TYPE):
        build_cashflow(i)
    for i in range(PER_TYPE):
        build_beneish(i)
    for i in range(PER_TYPE):
        build_bscore(i)
    for i in range(PER_TYPE):
        build_related(i)
    for i in range(PER_TYPE):
        build_auditor(i)
    for i in range(PER_TYPE):
        build_restate(i)
    for i in range(PER_TYPE):
        build_gc(i)
    for i in range(PER_TYPE):
        build_digits(i)

build_all()

# =========================================================================== helpers
def F(key, task, ftype, n, q, gt, at="number", tol="abs:0.1", ref=None):
    return {"key": key, "task": task, "ftype": ftype, "n": n, "q": q, "gt": gt,"at": at, "tol": tol, "ref": ref}

def dsri(d):
    return (d["rec"][1] / float(d["sales"][1])) / (d["rec"][0] / float(d["sales"][0]))

def gmi(d):
    gm1 = (d["sales"][1] - d["cogs"][1]) / float(d["sales"][1])
    gm0 = (d["sales"][0] - d["cogs"][0]) / float(d["sales"][0])
    return gm0 / gm1

def aqi(d):
    a1 = 1 - (d["ca"][1] + d["ppe"][1]) / float(d["ta"][1])
    a0 = 1 - (d["ca"][0] + d["ppe"][0]) / float(d["ta"][0])
    return a1 / a0

def sgi(d):
    return d["sales"][1] / float(d["sales"][0])

def depi(d):
    r0 = d["dep"][0] / float(d["dep"][0] + d["ppe"][0]); r1 = d["dep"][1] / float(d["dep"][1] + d["ppe"][1])
    return r0 / r1

def sgai(d):
    return (d["sga"][1] / float(d["sales"][1])) / (d["sga"][0] / float(d["sales"][0]))

def lvgi(d):
    return ((d["cl"][1] + d["ltd"][1]) / float(d["ta"][1])) / \
           ((d["cl"][0] + d["ltd"][0]) / float(d["ta"][0]))

def tata(d):
    return (d["ni"][1] - d["cfo"][1]) / float(d["ta"][1])

def acc_spreads(d):
    r = 100.0 * (d["recg"][2] / float(d["recg"][1]) - 1) - 100.0 * (d["rev"][2] / float(d["rev"][1]) - 1)
    i = 100.0 * (d["inv"][2] / float(d["inv"][1]) - 1) - 100.0 * (d["cogs"][2] / float(d["cogs"][1]) - 1)
    return r, i

def acc_flag(d):
    r, i = acc_spreads(d)
    if r > 5.0 and i > 5.0:
        return "both_flags"
    if r > 5.0:
        return "receivables_flag"
    if i > 5.0:
        return "inventory_flag"
    return "no_flag"

def cf_quality(d):
    q = d["cfo"][1] / float(d["ni"][1])
    if q > 1.10:
        return "cash_backed"
    if q < 0.80:
        return "accrual_driven"
    return "mixed"

def digits_of(d):
    out = {}
    for a in d["amounts"]:
        k = int(str(a)[0]); out[k] = out.get(k, 0) + 1
    return out

BENFORD = {1: 30.1, 2: 17.6, 3: 12.5, 4: 9.7, 5: 7.9, 6: 6.7, 7: 5.8, 8: 5.1, 9: 4.6}
OP_PHRASE = {"unqualified": "present fairly, in all material respects","qualified": "except for the effects of the matter","adverse": "do not present fairly","disclaimer": "do not express an opinion"}

# =========================================================================== calc
CALC = [
    F("acc_recv_spread", "calc", "accrual", 6, "What was trade receivables growth less revenue growth in FY2025, in percentage points?", lambda d: rnd(acc_spreads(d)[0], 1)),
    F("acc_inv_spread", "calc", "accrual", 6, "What was inventory growth less cost of sales growth in FY2025, in percentage points?", lambda d: rnd(acc_spreads(d)[1], 1)),
    F("acc_dso_delta", "calc", "accrual", 6, "Using gross trade receivables and a 365-day year, what was the change in days sales " "outstanding from FY2024 to FY2025, in days?", lambda d: rnd(365.0 * d["recg"][2] / d["rev"][2] - 365.0 * d["recg"][1] / d["rev"][1], 1)),
    F("acc_dio", "calc", "accrual", 5, "Using a 365-day year, what was days inventory outstanding in FY2025, in days?", lambda d: rnd(365.0 * d["inv"][2] / d["cogs"][2], 1)),
    F("acc_allow_cov", "calc", "accrual", 5, "What was the allowance for credit losses as a percent of gross trade receivables at FY2025?", lambda d: rnd(100.0 * d["alw"][2] / d["recg"][2], 1)),
    F("cf_op_gap", "calc", "cashflow", 6, "What was the FY2025 operating margin less the operating cash flow margin, in percentage points?", lambda d: rnd(100.0 * (d["op"][1] - d["cfo"][1]) / d["rev"][1], 1)),
    F("cf_accruals", "calc", "cashflow", 6, "What was the FY2025 accruals ratio, defined as net income less cash from operations divided " "by average total assets, in percent?", lambda d: rnd(100.0 * (d["ni"][1] - d["cfo"][1]) / ((d["ta"][1] + d["ta"][0]) / 2.0), 1)),
    F("cf_conversion", "calc", "cashflow", 5, "What was cash from operations as a multiple of net income in FY2025?", lambda d: rnd(d["cfo"][1] / float(d["ni"][1]), 2), tol="abs:0.02"),
    F("cf_growth_gap", "calc", "cashflow", 4, "What was cash from operations growth less net income growth in FY2025, in percentage points?", lambda d: rnd(100.0 * (d["cfo"][1] / float(d["cfo"][0]) - 1) - 100.0 * (d["ni"][1] / float(d["ni"][0]) - 1), 1)),
    F("cf_fcf_ni", "calc", "cashflow", 3, "What was free cash flow as a multiple of net income in FY2025, where free cash flow is cash " "from operations less capital expenditure?", lambda d: rnd((d["cfo"][1] - d["capex"][1]) / float(d["ni"][1]), 2), tol="abs:0.02"),
    F("ben_dsri", "calc", "beneish", 4, "Compute the DSRI, defined as (trade receivables / revenue) in FY2025 divided by " "(trade receivables / revenue) in FY2024, to two decimal places.", lambda d: rnd(dsri(d), 2), tol="abs:0.02"),
    F("ben_gmi", "calc", "beneish", 4, "Compute the GMI, defined as the FY2024 gross margin divided by the FY2025 gross margin, to " "two decimal places.", lambda d: rnd(gmi(d), 2), tol="abs:0.02"),
    F("ben_aqi", "calc", "beneish", 3, "Compute the AQI, defined as [1 - (current assets + net property plant and equipment) / total " "assets] in FY2025 divided by the same expression in FY2024, to two decimal places.", lambda d: rnd(aqi(d), 2), tol="abs:0.02"),
    F("ben_sgi", "calc", "beneish", 3, "Compute the SGI, defined as FY2025 revenue divided by FY2024 revenue, to two decimal places.", lambda d: rnd(sgi(d), 2), tol="abs:0.02"),
    F("ben_depi", "calc", "beneish", 3, "Compute the DEPI, defined as the FY2024 depreciation rate divided by the FY2025 depreciation " "rate, where the rate is depreciation divided by depreciation plus net property plant and " "equipment, to two decimal places.", lambda d: rnd(depi(d), 2), tol="abs:0.02"),
    F("ben_sgai", "calc", "beneish", 3, "Compute the SGAI, defined as (SG&A / revenue) in FY2025 divided by (SG&A / revenue) in " "FY2024, to two decimal places.", lambda d: rnd(sgai(d), 2), tol="abs:0.02"),
    F("ben_lvgi", "calc", "beneish", 3, "Compute the LVGI, defined as (current liabilities + long-term debt) / total assets in FY2025 " "divided by the same expression in FY2024, to two decimal places.", lambda d: rnd(lvgi(d), 2), tol="abs:0.02"),
    F("ben_tata", "calc", "beneish", 4, "Compute the TATA, defined as (net income less cash from operations) divided by total assets " "in FY2025, to three decimal places.", lambda d: rnd(tata(d), 3), tol="abs:0.002"),
    F("ben_mscore", "calc", "bscore", 6, "Using the eight components above and the formula M = -4.84 + 0.920*DSRI + 0.528*GMI + " "0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI, what is the " "M-score to two decimal places?", lambda d: rnd(mscore(d["comp"]), 2), tol="abs:0.02"),
    F("rp_rev_share", "calc", "related", 4, "What was total related party sales as a percent of group revenue in FY2025?", lambda d: rnd(100.0 * sum(r["a25"] for r in d["rows"] if r["cat"] == "sale") / d["group_rev"], 1)),
    F("rp_purchase_share", "calc", "related", 3, "What were total related party purchases as a percent of cost of sales in FY2025?", lambda d: rnd(100.0 * sum(r["a25"] for r in d["rows"] if r["cat"] == "purchase") / d["cogs"], 1)),
    F("rp_net_balance", "calc", "related", 3, "What was the net balance receivable from related parties at FY2025, in millions, defined as " "balances receivable less balances payable?", lambda d: sum(r["recv"] for r in d["rows"]) - sum(r["pay"] for r in d["rows"])),
    F("aud_fee_ratio", "calc", "auditor", 4, "What were non-audit fees as a percent of the audit fee in FY2025?", lambda d: rnd(100.0 * d["nonaudit"] / d["audit25"], 1)),
    F("aud_fee_growth", "calc", "auditor", 2, "What was the percentage change in the audit fee from FY2024 to FY2025?", lambda d: rnd(100.0 * (d["audit25"] / float(d["audit24"]) - 1), 1)),
    F("res_rev_impact", "calc", "restate", 3, "What was the restatement adjustment to FY2024 revenue, in percent of originally reported revenue?", lambda d: rnd(100.0 * (d["rest"]["rev"] / float(d["orig"]["rev"]) - 1), 1)),
    F("res_ni_impact", "calc", "restate", 3, "What was restated FY2024 net income as a percent of originally reported net income?", lambda d: rnd(100.0 * d["rest"]["ni"] / float(d["orig"]["ni"]), 1)),
    F("res_gp_impact", "calc", "restate", 2, "What was the change in FY2024 gross profit caused by the restatement, in millions?", lambda d: (d["rest"]["rev"] - d["rest"]["cogs"]) - (d["orig"]["rev"] - d["orig"]["cogs"])),
    F("gc_current_ratio", "calc", "gc", 3, "What was the FY2025 current ratio, to two decimal places?", lambda d: rnd(d["ca"] / float(d["cl"]), 2), tol="abs:0.02"),
    F("gc_runway", "calc", "gc", 3, "What was the liquidity runway in months, defined as cash plus the undrawn revolving facility " "divided by average monthly cash burn?", lambda d: rnd((d["cash"] + d["undrawn"]) / float(d["burn"]), 1)),
    F("gc_working_capital", "calc", "gc", 1, "What was working capital at FY2025, in millions?", lambda d: d["ca"] - d["cl"]),
    F("dig_count_one", "calc", "digits", 2, "How many of the twelve reported figures begin with the digit 1?", lambda d: d["n1"]),
    F("dig_share_three", "calc", "digits", 1, "What percent of the twelve reported figures begin with the digit 3?", lambda d: rnd(100.0 * d["n3"] / 12.0, 1)),
    F("dig_mad", "calc", "digits", 1, "What was the absolute difference between the observed share of leading digit 1 and the " "Benford expectation of 30.1 percent, in percentage points?", lambda d: rnd(abs(100.0 * d["n1"] / 12.0 - 30.1), 1)),
]

# =========================================================================== extraction
EXTR = [
    F("ex_recg_fy24", "extraction", "accrual", 8, "What was gross trade receivables at FY2024, in millions?", lambda d: d["recg"][1]),
    F("ex_recg_fy23", "extraction", "accrual", 6, "What was gross trade receivables at FY2023, in millions?", lambda d: d["recg"][0]),
    F("ex_alw_fy23", "extraction", "accrual", 6, "What was the allowance for credit losses at FY2023, in millions?", lambda d: d["alw"][0]),
    F("ex_alw_fy25", "extraction", "accrual", 6, "What was the allowance for credit losses at FY2025, in millions?", lambda d: d["alw"][2]),
    F("ex_inv_fy25", "extraction", "accrual", 6, "What was the inventory balance at FY2025, in millions?", lambda d: d["inv"][2]),
    F("ex_inv_fy24", "extraction", "accrual", 6, "What was the inventory balance at FY2024, in millions?", lambda d: d["inv"][1]),
    F("ex_cogs_fy24", "extraction", "accrual", 5, "What was cost of sales in FY2024, in millions?", lambda d: d["cogs"][1]),
    F("ex_rev_fy24", "extraction", "accrual", 5, "What was revenue in FY2024, in millions?", lambda d: d["rev"][1]),
    F("ex_capex", "extraction", "cashflow", 6, "What was capital expenditure in FY2025, in millions?", lambda d: d["capex"][1]),
    F("ex_ocf", "extraction", "cashflow", 6, "What was cash from operations in FY2025, in millions?", lambda d: d["cfo"][1]),
    F("ex_ta", "extraction", "cashflow", 5, "What were total assets at the end of FY2025, in millions?", lambda d: d["ta"][1]),
    F("ex_gp", "extraction", "cashflow", 5, "What was gross profit in FY2025, in millions?", lambda d: d["gp"][1]),
    F("ex_rp_largest_name", "extraction", "related", 10, "Which counterparty had the largest FY2025 transaction amount?", lambda d: d["rows"][0]["name"], at="text", tol="normalized"),
    F("ex_rp_approval", "extraction", "related", 9, "Which body approved the transaction with the counterparty that had the largest FY2025 amount?", lambda d: d["rows"][0]["approval"], at="text", tol="normalized"),
    F("ex_rp_amount", "extraction", "related", 9, "What was the FY2025 amount for the counterparty that had the largest transaction, in millions?", lambda d: d["rows"][0]["a25"]),
    F("ex_rp_second", "extraction", "related", 6, "What was the FY2025 amount of the second-largest related party transaction, in millions?", lambda d: d["rows"][1]["a25"]),
    F("ex_rp_count", "extraction", "related", 5, "How many related party transactions are disclosed?", lambda d: len(d["rows"])),
    F("ex_aud_firm", "extraction", "auditor", 10, "Which audit firm is named in the facts table?", lambda d: d["firm"], at="text", tol="normalized"),
    F("ex_aud_phrase", "extraction", "auditor", 10, "Quote the phrase in the opinion paragraph that determines the opinion type.", lambda d: OP_PHRASE[d["opinion"]], at="text", tol="normalized"),
    F("ex_aud_kam", "extraction", "auditor", 8, "How many key audit matters are listed?", lambda d: len(d["kam"])),
    F("ex_aud_tenure", "extraction", "auditor", 7, "How many consecutive years has the auditor served, as stated in the facts table?", lambda d: d["tenure"]),
    F("ex_aud_fee", "extraction", "auditor", 8, "What was the audit fee in FY2025, in millions?", lambda d: d["audit25"]),
    F("ex_aud_kam_first", "extraction", "auditor", 6, "Which key audit matter is listed first?", lambda d: d["kam"][0], at="text", tol="normalized"),
    F("ex_res_period", "extraction", "restate", 8, "Which comparative period was restated?", lambda d: "FY2024", at="text", tol="normalized"),
    F("ex_res_line", "extraction", "restate", 8, "Which line item changed by the largest absolute amount in the restatement?", lambda d: max([("Revenue", d["rest"]["rev"] - d["orig"]["rev"]), ("Cost of sales", d["rest"]["cogs"] - d["orig"]["cogs"]), ("Net income", d["rest"]["ni"] - d["orig"]["ni"]), ("Inventories", d["rest"]["inv"] - d["orig"]["inv"])], key=lambda x: abs(x[1]))[0], at="text", tol="normalized"),
    F("ex_res_amount", "extraction", "restate", 8, "What was restated FY2024 net income, in millions?", lambda d: d["rest"]["ni"]),
    F("ex_gc_covenant", "extraction", "gc", 8, "What interest cover ratio must the group maintain under the revolving facility?", lambda d: d["covenant"], tol="abs:0.01"),
    F("ex_gc_waiver", "extraction", "gc", 7, "Until what date did the lender waive the net debt covenant?", lambda d: d["waiver"], at="text", tol="normalized"),
    F("ex_gc_lender", "extraction", "gc", 7, "Which lender granted the covenant waiver?", lambda d: d["lender"], at="text", tol="normalized"),
    F("ex_digit_list", "extraction", "digits", 8, "List the reporting units whose reported amount begins with the digit 4.", lambda d: [d["names"][k] for k in range(12) if int(str(d["amounts"][k])[0]) == 4], at="list", tol="set"),
    F("ex_digit_max", "extraction", "digits", 8, "Which reporting unit reported the largest amount?", lambda d: d["names"][d["amounts"].index(max(d["amounts"]))], at="text", tol="normalized"),
]

# =========================================================================== qa
def dig_top(d):
    c = digits_of(d); best, bd = 1, -999.0
    for k in range(1, 10):
        dev = 100.0 * c.get(k, 0) / 12.0 - BENFORD[k]
        if dev > bd:
            bd, best = dev, k
    return "digit_" + str(best)

def gc_level(d):
    runway = (d["cash"] + d["undrawn"]) / float(d["burn"]); cr = d["ca"] / float(d["cl"])
    if runway < 6.0 or cr < 0.80:
        return "severe"
    if runway < 12.0 or cr < 1.00:
        return "moderate"
    if runway < 18.0 or cr < 1.20:
        return "mild"
    return "none"

QA = [
    F("qa_acc_spread_larger", "qa", "accrual", 8, "Which accrual spread is larger in FY2025, the receivables spread or the inventory spread? " "Answer receivables or inventory.", lambda d: "receivables" if acc_spreads(d)[0] > acc_spreads(d)[1] else "inventory", at="label", tol="exact"),
    F("qa_acc_flag_count", "qa", "accrual", 8, "How many of the two accrual spreads exceed 5.0 percentage points in FY2025?", lambda d: int(acc_spreads(d)[0] > 5.0) + int(acc_spreads(d)[1] > 5.0), tol="abs:0.01"),
    F("qa_acc_dso_dir", "qa", "accrual", 8, "Did days sales outstanding rise or fall from FY2024 to FY2025? Answer rose or fell.", lambda d: "rose" if 365.0 * d["recg"][2] / d["rev"][2] > 365.0 * d["recg"][1] / d["rev"][1] else "fell", at="label", tol="exact"),
    F("qa_acc_primary", "qa", "accrual", 6, "Which account is the primary accrual concern in FY2025: trade receivables, inventories, or neither?", lambda d: ("neither" if max(acc_spreads(d)) <= 5.0 else ("trade_receivables" if acc_spreads(d)[0] > acc_spreads(d)[1] else "inventories")), at="label", tol="exact"),
    F("qa_acc_allow_years", "qa", "accrual", 8, "In how many of the three years shown did the allowance for credit losses exceed 5 percent of " "gross trade receivables?", lambda d: sum(1 for i in range(3) if 100.0 * d["alw"][i] / d["recg"][i] > 5.0), tol="abs:0.01"),
    F("qa_cf_quality", "qa", "cashflow", 8, "Does the FY2025 pattern point to accrual-driven, cash-backed or mixed earnings? Apply this rule: " "accrual-driven if cash from operations is below 80 percent of net income, cash-backed if above " "110 percent, otherwise mixed.", cf_quality, at="label", tol="exact"),
    F("qa_cf_gap_abs", "qa", "cashflow", 8, "What was the absolute difference between net income and cash from operations in FY2025, in millions?", lambda d: abs(d["ni"][1] - d["cfo"][1]), tol="abs:0.01"),
    F("qa_cf_ni_vs_cfo", "qa", "cashflow", 6, "Which was larger in FY2025, net income or cash from operations?", lambda d: "net_income" if d["ni"][1] > d["cfo"][1] else "cash_from_operations", at="label", tol="exact"),
    F("qa_ben_highest", "qa", "beneish", 8, "Which of the seven ratio components (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI) is furthest above " "1.00 in FY2025?", lambda d: max([("DSRI", dsri(d)), ("GMI", gmi(d)), ("AQI", aqi(d)), ("SGI", sgi(d)), ("DEPI", depi(d)), ("SGAI", sgai(d)), ("LVGI", lvgi(d))], key=lambda x: x[1] - 1.0)[0], at="label", tol="exact"),
    F("qa_ben_count", "qa", "beneish", 8, "How many of the seven ratio components exceed 1.00 in FY2025?", lambda d: sum(1 for v in (dsri(d), gmi(d), aqi(d), sgi(d), depi(d), sgai(d), lvgi(d)) if v > 1.0), tol="abs:0.01"),
    F("qa_ben_tata_sign", "qa", "beneish", 6, "Is TATA positive or negative in FY2025? Answer positive or negative.", lambda d: "positive" if tata(d) > 0 else "negative", at="label", tol="exact"),
    F("qa_ben_interpret", "qa", "beneish", 6, "Which manipulation channel is the stronger signal in FY2025: revenue inflation through " "receivables, or accrual inflation through earnings? Answer receivables or accruals, using a " "DSRI above 1.10 as the test for the receivables channel.", lambda d: "receivables" if dsri(d) > 1.10 else "accruals", at="label", tol="exact"),
    F("qa_rp_largest", "qa", "related", 8, "Which related party accounts for the largest FY2025 transaction amount?", lambda d: d["rows"][0]["name"], at="text", tol="normalized"),
    F("qa_rp_share", "qa", "related", 8, "What share of group revenue did the largest related party transaction represent in FY2025, in percent?", lambda d: rnd(100.0 * d["rows"][0]["a25"] / d["group_rev"], 1)),
    F("qa_rp_policy_list", "qa", "related", 8, "Which counterparties required audit committee approval under the group policy stated in the " "disclosure?", lambda d: [r["name"] for r in d["rows"] if r["a25"] > 0.02 * d["group_rev"]], at="list", tol="set"),
    F("qa_rp_concern", "qa", "related", 6, "Classify the independence concern as low, moderate or high: high if the largest transaction " "exceeds 10 percent of group revenue, moderate if it exceeds 4 percent, otherwise low.", lambda d: ("high" if d["rows"][0]["a25"] > 0.10 * d["group_rev"] else ("moderate" if d["rows"][0]["a25"] > 0.04 * d["group_rev"] else "low")), at="label", tol="exact"),
    F("qa_aud_disagreement", "qa", "auditor", 8, "Does the auditor change follow a disagreement with management? Answer yes or no.", lambda d: "yes" if d["change"] == "disagreement" else "no", at="label", tol="exact"),
    F("qa_aud_flag", "qa", "auditor", 6, "Is the audit opinion other than unqualified while the auditor is also being replaced? " "Answer yes or no.", lambda d: "yes" if (d["opinion"] != "unqualified" and d["change"] != "planned_rotation") else "no", at="label", tol="exact"),
    F("qa_aud_kam_count", "qa", "auditor", 6, "What is the number of key audit matters disclosed by the auditor?", lambda d: len(d["kam"]), tol="abs:0.01"),
    F("qa_aud_rotation", "qa", "auditor", 6, "Does the disclosed auditor change result from mandatory rotation rather than a dispute? " "Answer yes or no.", lambda d: "yes" if d["change"] == "planned_rotation" else "no", at="label", tol="exact"),
    F("qa_res_who", "qa", "restate", 8, "Who identified the error that led to the restatement?", lambda d: d["who"], at="text", tol="normalized"),
    F("qa_res_effect", "qa", "restate", 8, "Did the restatement increase, decrease or leave unchanged FY2024 net income?", lambda d: ("increase" if d["rest"]["ni"] > d["orig"]["ni"] else ("decrease" if d["rest"]["ni"] < d["orig"]["ni"] else "unchanged")), at="label", tol="exact"),
    F("qa_res_item", "qa", "restate", 6, "Which caption shows the largest absolute restatement adjustment?", lambda d: max([("Revenue", d["rest"]["rev"] - d["orig"]["rev"]), ("Cost of sales", d["rest"]["cogs"] - d["orig"]["cogs"]), ("Net income", d["rest"]["ni"] - d["orig"]["ni"]), ("Inventories", d["rest"]["inv"] - d["orig"]["inv"])], key=lambda x: abs(x[1]))[0], at="label", tol="exact"),
    F("qa_res_magnitude", "qa", "restate", 6, "What was the absolute restatement adjustment to FY2024 revenue, in millions?", lambda d: abs(d["rest"]["rev"] - d["orig"]["rev"]), tol="abs:0.01"),
    F("qa_gc_indicators", "qa", "gc", 8, "List the going concern conditions noted in the working paper.", lambda d: d["inds"], at="list", tol="set"),
    F("qa_gc_level", "qa", "gc", 8, "Classify the going concern evidence as none, mild, moderate or severe: severe if the liquidity " "runway is below 6 months or the ratio of current assets to current liabilities is below 0.80; " "moderate if below 12 months or below 1.00; mild if below 18 months or below 1.20; otherwise none.", gc_level, at="label", tol="exact"),
    F("qa_gc_runway_dir", "qa", "gc", 6, "Is the liquidity runway above or below twelve months? Answer above or below.", lambda d: "above" if (d["cash"] + d["undrawn"]) / float(d["burn"]) > 12.0 else "below", at="label", tol="exact"),
    F("qa_digit_verdict", "qa", "digits", 6, "Is the leading-digit distribution consistent with Benford's law? Treat it as consistent when " "the share of leading digit 1 is within 5.0 percentage points of 30.1 percent.", lambda d: "consistent" if abs(100.0 * d["n1"] / 12.0 - 30.1) <= 5.0 else "inconsistent", at="label", tol="exact"),
    F("qa_digit_top", "qa", "digits", 6, "Which leading digit is most over-represented relative to Benford's law? Answer as digit_1 to " "digit_9.", dig_top, at="label", tol="exact"),
    F("qa_digit_ge_three", "qa", "digits", 6, "How many of the twelve reported figures begin with a digit of 3 or higher?", lambda d: sum(v for k, v in digits_of(d).items() if k >= 3), tol="abs:0.01"),
]

# =========================================================================== classification
CLS = [
    F("cls_acc_flag", "classification", "accrual", 28, "Classify the FY2025 accrual signal as one of {receivables_flag, inventory_flag, both_flags, " "no_flag}, using a threshold of more than 5.0 percentage points for each spread.", acc_flag, at="label", tol="exact"),
    F("cls_cf_quality", "classification", "cashflow", 21, "Classify FY2025 earnings quality as one of {cash_backed, accrual_driven, mixed}, where " "cash_backed means cash from operations above 110 percent of net income and accrual_driven means " "below 80 percent.", cf_quality, at="label", tol="exact"),
    F("cls_ben_dsri", "classification", "beneish", 16, "Classify the FY2025 DSRI as one of {above_one, below_one}, where DSRI is (receivables / revenue) " "in FY2025 divided by the same ratio in FY2024.", lambda d: "above_one" if dsri(d) > 1.0 else "below_one", at="label", tol="exact"),
    F("cls_ben_accrual", "classification", "beneish", 16, "Classify FY2025 accruals as one of {positive_accruals, negative_accruals}, where positive " "accruals means net income exceeds cash from operations.", lambda d: "positive_accruals" if d["ni"][1] > d["cfo"][1] else "negative_accruals", at="label", tol="exact"),
    F("cls_ben_mscore", "classification", "bscore", 16, "Classify the M-score as one of {above_threshold, below_threshold}, using the -1.78 cutoff stated " "in the note.", lambda d: "above_threshold" if mscore(d["comp"]) > -1.78 else "below_threshold", at="label", tol="exact"),
    F("cls_rp_relationship", "classification", "related", 28, "Classify the relationship of the counterparty with the largest FY2025 transaction amount as one " "of {subsidiary, associate, joint_venture, key_management, controlling_shareholder}. Definitions: " "subsidiary = controlled by the group; associate = significant influence without control; " "joint_venture = joint control; key_management = controlled by a member of key management; " "controlling_shareholder = controls the reporting company.", lambda d: d["rows"][0]["rel"], at="label", tol="exact"),
    F("cls_rp_concern", "classification", "related", 18, "Classify the independence concern as one of {low, moderate, high}: high if the largest " "transaction exceeds 10 percent of group revenue, moderate if it exceeds 4 percent, otherwise low.", lambda d: ("high" if d["rows"][0]["a25"] > 0.10 * d["group_rev"] else ("moderate" if d["rows"][0]["a25"] > 0.04 * d["group_rev"] else "low")), at="label", tol="exact"),
    F("cls_aud_opinion", "classification", "auditor", 22, "Classify the audit opinion as one of {unqualified, qualified, adverse, disclaimer} from the " "opinion paragraph.", lambda d: d["opinion"], at="label", tol="exact"),
    F("cls_aud_change", "classification", "auditor", 12, "Classify the auditor change as one of {planned_rotation, disagreement, resignation, fee_dispute}.", lambda d: d["change"], at="label", tol="exact"),
    F("cls_res_type", "classification", "restate", 16, "Classify the restatement as one of {error_correction, reclassification, accounting_policy_change, " "fraud}.", lambda d: d["kind"], at="label", tol="exact"),
    F("cls_gc_level", "classification", "gc", 15, "Classify the going concern evidence as one of {none, mild, moderate, severe}: severe if the " "liquidity runway is below 6 months or the ratio of current assets to current liabilities is " "below 0.80; moderate if below 12 months or below 1.00; mild if below 18 months or below 1.20; " "otherwise none.", gc_level, at="label", tol="exact"),
    F("cls_digit", "classification", "digits", 12, "Classify the leading-digit distribution as one of {consistent, inconsistent}, consistent when " "the share of leading digit 1 is within 5.0 percentage points of 30.1 percent.", lambda d: "consistent" if abs(100.0 * d["n1"] / 12.0 - 30.1) <= 5.0 else "inconsistent", at="label", tol="exact"),
]

# =========================================================================== summarization
def sum_acc_ref(d):
    r, i = acc_spreads(d)
    s = ("Revenue moved from %d to %d while gross trade receivables moved from %d to %d" % (d["rev"][1], d["rev"][2], d["recg"][1], d["recg"][2]))
    if r > 5.0:
        return s + ", so receivables outpaced revenue and are the main working capital signal."
    if i > 5.0:
        return s + ", while inventories moved from %d to %d faster than cost of sales." % (d["inv"][1], d["inv"][2])
    return s + " and inventories moved from %d to %d; neither balance outpaced its income statement driver." % (d["inv"][1], d["inv"][2])

def sum_cf_ref(d):
    word = "higher" if d["cfo"][1] > d["ni"][1] else "lower"
    return ("Revenue was %d and gross profit %d, while cash from operations of %d was %s than net " "income of %d." % (d["rev"][1], d["gp"][1], d["cfo"][1], word, d["ni"][1]))

def sum_rp_ref(d):
    r = d["rows"][0]
    return ("The largest related party transaction was with %s, described as %s, at %d against group " "revenue of %d; %d counterparties are disclosed." % (r["name"], r["role"].lower(), r["a25"], d["group_rev"], len(d["rows"])))

def sum_aud_ref(d):
    return ("The auditor is %s, which has served %d consecutive years and reports a %s opinion with %d " "key audit matters; the firm is being replaced." % (d["firm"], d["tenure"], d["opinion"], len(d["kam"])))

def sum_res_ref(d):
    return ("FY2024 revenue was restated from %d to %d, cost of sales from %d to %d and net income from " "%d to %d; the note describes the adjustment as %s." % (d["orig"]["rev"], d["rest"]["rev"], d["orig"]["cogs"], d["rest"]["cogs"],d["orig"]["ni"], d["rest"]["ni"], d["kind"].replace("_", " ")))

def sum_gc_ref(d):
    return ("The working paper lists %d conditions and reports cash of %d, undrawn facilities of %d and " "average monthly cash burn of %d against current liabilities of %d." % (len(d["inds"]), d["cash"], d["undrawn"], d["burn"], d["cl"]))

def sum_dig_ref(d):
    near = "close to" if abs(100.0 * d["n1"] / 12.0 - 30.1) <= 5.0 else "far from"
    return ("Of the twelve reported figures, %d begin with 1 and %d begin with 3; the observed share of " "leading digit 1 is %s the Benford expectation of 30.1 percent." % (d["n1"], d["n3"], near))

SUMM = [
    F("sum_accrual", "summarization", "accrual", 14, "Summarize the accrual review extract in two sentences, naming the main working capital signal.", None, at="text", ref=sum_acc_ref),
    F("sum_cashflow", "summarization", "cashflow", 12, "Summarize the earnings quality review, stating whether cash flow supports reported earnings.", None, at="text", ref=sum_cf_ref),
    F("sum_related", "summarization", "related", 18, "Summarize the related party disclosure, naming the largest counterparty and its amount.", None, at="text", ref=sum_rp_ref),
    F("sum_auditor", "summarization", "auditor", 18, "Summarize the auditor report, covering the opinion, the key audit matters and the change of auditor.", None, at="text", ref=sum_aud_ref),
    F("sum_restatement", "summarization", "restate", 16, "Summarize the restatement note, stating which line items moved and in which direction.", None, at="text", ref=sum_res_ref),
    F("sum_gc", "summarization", "gc", 14, "Summarize the going concern working paper, naming the conditions and the liquidity figures.", None, at="text", ref=sum_gc_ref),
    F("sum_digits", "summarization", "digits", 8, "Summarize the leading-digit review, stating whether the pattern is consistent with Benford's law.", None, at="text", ref=sum_dig_ref),
]

# =========================================================================== knowledge
KNOW = [("Which Beneish component is the ratio of days sales in receivables in the reporting year to the " "same ratio in the prior year?", "DSRI"),
    ("Which Beneish component compares the prior-year gross margin with the reporting-year gross margin?","GMI"),
    ("Which Beneish component captures asset quality through the long-term asset share of total assets?","AQI"),
    ("Which Beneish component is reporting-year sales divided by prior-year sales?", "SGI"),
    ("Which Beneish component compares the prior-year depreciation rate with the reporting-year rate?","DEPI"),
    ("Which Beneish component measures the change in selling general and administrative expense as a " "share of sales?", "SGAI"),
    ("Which Beneish component measures the change in leverage using short-term liabilities plus " "long-term debt over total assets?", "LVGI"),
    ("Which Beneish component is total accruals divided by total assets, where accruals are net income " "less cash from operations?", "TATA"),
    ("Which audit opinion is issued when the financial statements are materially misstated but the " "misstatement is not pervasive?", "qualified"),
    ("Which audit opinion is issued when the auditor cannot obtain sufficient evidence and the possible " "effects are both material and pervasive?", "disclaimer"),
    ("Which audit opinion states that the financial statements do not present fairly the financial " "position?", "adverse"),
    ("Which audit opinion states that the statements present fairly, in all material respects, the " "financial position?", "unqualified"),
    ("Which condition is an operating indicator in a going concern assessment rather than a financial " "indicator?", "loss_of_key_customer"),
    ("What horizon does ISA 570 require management to assess when evaluating going concern?","twelve_months"),
    ("A working capital deficit combined with a liquidity runway below six months indicates which going " "concern level?", "severe"),
    ("When a material uncertainty over going concern is disclosed but the statements are fairly " "presented, which opinion is appropriate?", "unqualified_with_material_uncertainty"),
    ("Which relationship exists when an investor holds 25 percent of the voting shares and appoints two " "of seven directors?", "associate"),
    ("Which relationship exists when two investors each hold 50 percent and the shareholders agreement " "requires unanimous consent?", "joint_venture"),
    ("Which relationship exists when a counterparty is controlled by the chief financial officer of the " "reporting company?", "key_management"),
    ("Which relationship exists when an investor holds 60 percent of the voting shares and controls the " "board?", "controlling_shareholder"),
    ("Which type of restatement corrects a material error in previously issued financial statements?","error_correction"),
    ("Which type of restatement changes presentation without changing equity or net income?","reclassification"),
    ("Which type of restatement applies a new accounting policy retrospectively to prior periods?","accounting_policy_change"),
    ("Which restatement indicator most strongly suggests deliberate misstatement rather than error?","regulator_finding"),
    ("Under Benford's law, what is the expected first-digit frequency of 1, in percent?", 30.1),
    ("Under Benford's law, what is the expected first-digit frequency of 9, in percent?", 4.6),
    ("Under Benford's law, which first digit has the second-highest expected frequency?", "digit_2"),
    ("A leading-digit distribution with too many figures starting with 1 and too few starting with 9 is " "best described as what?", "first_digit_anomaly"),]

# =========================================================================== tool use
def tool(name, desc, props, req):
    return {"name": name, "description": desc,"parameters": {"type": "object", "properties": props, "required": req}}

TOOL_METRIC = tool("get_financial_metric","Return reported financial metrics for a fictional issuer across one or more periods.",{"entity": {"type": "string", "description": "Issuer name exactly as registered."},"metrics": {"type": "array", "items": {"type": "string"},"description": "Metric names such as revenue or gross_trade_receivables."},"periods": {"type": "array", "items": {"type": "string"},"description": "Period labels such as FY2025."}},["entity", "metrics", "periods"])
TOOL_RP = tool("list_related_parties","Return the related party register for an issuer, with counterparties and FY2025 amounts.",{"entity": {"type": "string", "description": "Issuer name exactly as registered."}},["entity"])
TOOL_AUDIT = tool("get_audit_history","Return auditor identity, opinion type and audit and non-audit fees for the last two years.",{"entity": {"type": "string", "description": "Issuer name exactly as registered."}},["entity"])
TOOL_LIQ = tool("get_liquidity_metrics","Return cash, undrawn facilities, current balances and average monthly cash burn.",{"entity": {"type": "string", "description": "Issuer name exactly as registered."}},["entity"])
TOOL_RATIO = tool("compute_ratio","Divide numerator by denominator and multiply by the supplied scale.",{"numerator": {"type": "number", "description": "Top of the ratio."},"denominator": {"type": "number", "description": "Bottom of the ratio."},"scale": {"type": "number", "description": "Multiplier applied after division, for example 100."}},["numerator", "denominator", "scale"])
TOOL_DISC = tool("get_disclosure_section","Return a named disclosure section for an issuer and period.",{"entity": {"type": "string", "description": "Issuer name exactly as registered."},"section": {"type": "string", "description": "Section key such as segment_reporting."},"period": {"type": "string", "description": "Period label such as FY2025."}},["entity", "section", "period"])

def build_tool_rows():
    out = []; acc = BY_TYPE["accrual"]; cf = BY_TYPE["cashflow"]; ben = BY_TYPE["beneish"]; rp = BY_TYPE["related"]
    au = BY_TYPE["auditor"]; gc = BY_TYPE["gc"]

    def emit(key, msgs, tools, gt, at="number", tol="abs:0.1"):
        out.append({"key": key, "messages": msgs, "tools": tools, "gt": gt, "at": at, "tol": tol})

    for i in range(18):
        fx = acc[(i * 2) % len(acc)]; d, co = fx["data"], fx["company"]
        res = {"entity": co, "periods": ["FY2025", "FY2024"],"metrics": {"revenue": {"FY2025": d["rev"][2], "FY2024": d["rev"][1]},"gross_trade_receivables": {"FY2025": d["recg"][2], "FY2024": d["recg"][1]}}}
        ask = ["Pull FY2025 and FY2024 revenue and gross trade receivables for %s before I assess the " "accrual red flags." % co,"I need revenue and gross trade receivables for %s in FY2025 and FY2024." % co,"Before the accrual review of %s, get me revenue and gross trade receivables for both " "years." % co][i % 3]
        fin = ["Using those figures, what was trade receivables growth less revenue growth in FY2025, " "in percentage points?","With those numbers, what was the FY2025 receivables growth less revenue growth, in " "percentage points?","Compute receivables growth minus revenue growth for FY2025 from those figures, in " "percentage points."][i % 3]
        msgs = [{"role": "user", "content": ask},{"role": "assistant", "content": "Calling get_financial_metric for both metrics and both periods.\n" + json.dumps({"tool": "get_financial_metric","arguments": {"entity": co,"metrics": ["revenue", "gross_trade_receivables"],"periods": ["FY2025", "FY2024"]}})},{"role": "tool", "content": json.dumps(res)}]
        msgs.append({"role": "user", "content": fin})
        emit("tool|acc_spread|" + str(i), msgs, [TOOL_METRIC],rnd(acc_spreads(d)[0], 1))

    for i in range(14):
        fx = cf[(i * 3) % len(cf)]; d, co = fx["data"], fx["company"]
        res = {"entity": co, "net_income": {"FY2025": d["ni"][1], "FY2024": d["ni"][0]},"cash_from_operations": {"FY2025": d["cfo"][1], "FY2024": d["cfo"][0]},"total_assets": {"FY2025": d["ta"][1], "FY2024": d["ta"][0]}}
        msgs = [{"role": "user", "content": "Get net income, cash from operations and total assets for " "%s for FY2025 and FY2024." % co},{"role": "assistant", "content": "Calling get_financial_metric for the three line items.\n" + json.dumps({"tool": "get_financial_metric","arguments": {"entity": co,"metrics": ["net_income", "cash_from_operations", "total_assets"],"periods": ["FY2025", "FY2024"]}})},{"role": "tool", "content": json.dumps(res)},{"role": "user", "content": "What was the accruals ratio, net income less cash from " "operations divided by average total assets, in percent?"}]
        emit("tool|cf_accruals|" + str(i), msgs, [TOOL_METRIC],rnd(100.0 * (d["ni"][1] - d["cfo"][1]) / ((d["ta"][1] + d["ta"][0]) / 2.0), 1))

    for i in range(12):
        fx = rp[(i * 2 + 1) % len(rp)]; d, co = fx["data"], fx["company"]
        res = {"entity": co, "group_revenue_fy2025": d["group_rev"],"counterparties": [{"name": r["name"], "fy2025_amount": r["a25"]} for r in d["rows"]]}
        msgs = [{"role": "user", "content": "List the related parties of %s and their FY2025 transaction " "amounts." % co},{"role": "assistant", "content": "Calling list_related_parties.\n" + json.dumps({"tool": "list_related_parties", "arguments": {"entity": co}})},{"role": "tool", "content": json.dumps(res)},{"role": "user", "content": "What share of group revenue did the largest counterparty's " "FY2025 transactions represent, in percent?"}]
        emit("tool|rp_share|" + str(i), msgs, [TOOL_RP],rnd(100.0 * d["rows"][0]["a25"] / d["group_rev"], 1))

    for i in range(12):
        fx = au[(i * 2 + 1) % len(au)]; d, co = fx["data"], fx["company"]
        res = {"entity": co, "auditor": d["firm"], "opinion": d["opinion"],"audit_fee": {"FY2025": d["audit25"], "FY2024": d["audit24"]},"non_audit_fees": {"FY2025": d["nonaudit"]}}
        msgs = [{"role": "user", "content": "Get the audit history for %s." % co},{"role": "assistant", "content": "Calling get_audit_history.\n" + json.dumps({"tool": "get_audit_history", "arguments": {"entity": co}})},{"role": "tool", "content": json.dumps(res)},{"role": "user", "content": "What were non-audit fees as a percent of the audit fee in " "FY2025?"}]
        emit("tool|aud_fee|" + str(i), msgs, [TOOL_AUDIT],rnd(100.0 * d["nonaudit"] / d["audit25"], 1))

    for i in range(12):
        fx = gc[(i * 2 + 1) % len(gc)]; d, co = fx["data"], fx["company"]
        res = {"entity": co, "cash_and_equivalents": d["cash"],"undrawn_revolver": d["undrawn"], "average_monthly_cash_burn": d["burn"],"current_assets": d["ca"], "current_liabilities": d["cl"]}
        msgs = [{"role": "user", "content": "Pull the liquidity metrics for %s." % co},{"role": "assistant", "content": "Calling get_liquidity_metrics.\n" + json.dumps({"tool": "get_liquidity_metrics", "arguments": {"entity": co}})},{"role": "tool", "content": json.dumps(res)},{"role": "user", "content": "What is the liquidity runway in months, cash plus undrawn " "revolver divided by average monthly cash burn?"}]
        emit("tool|gc_runway|" + str(i), msgs, [TOOL_LIQ],rnd((d["cash"] + d["undrawn"]) / float(d["burn"]), 1))

    for i in range(12):
        fx = ben[i % len(ben)]; d, co = fx["data"], fx["company"]; num = d["rec"][1] * d["sales"][0]
        den = d["sales"][1] * d["rec"][0]
        msgs = [{"role": "user", "content": ("For %s, trade receivables were %d in FY2025 against revenue of %d, and %d in FY2024 against " "revenue of %d. Call compute_ratio with numerator %d and denominator %d at scale 1. What DSRI, " "to two decimal places, will it return?" % (co, d["rec"][1], d["sales"][1], d["rec"][0], d["sales"][0], num, den))}]
        emit("tool|dsri|" + str(i), msgs, [TOOL_RATIO], rnd(dsri(d), 2), tol="abs:0.02")

    for i in range(10):
        fx = cf[(i * 5 + 2) % len(cf)]; d, co = fx["data"], fx["company"]
        res = {"entity": co, "section": "segment_reporting", "available": False,"message": "Segment gross margin is not disclosed. Only consolidated revenue and operating " "income are available.","consolidated": {"revenue_fy2025": d["rev"][1], "operating_income_fy2025": d["op"][1]}}
        msgs = [{"role": "user", "content": "Get the FY2025 segment gross margin for %s." % co},{"role": "assistant", "content": "Calling get_disclosure_section for segment reporting.\n" + json.dumps({"tool": "get_disclosure_section","arguments": {"entity": co, "section": "segment_reporting","period": "FY2025"}})},{"role": "tool", "content": json.dumps(res)},{"role": "user", "content": "If segment gross margin is not disclosed, reply with exactly: " "insufficient data"}]
        emit("tool|abstain|" + str(i), msgs, [TOOL_DISC], "insufficient data",at="text", tol="normalized")

    for i in range(10):
        fx = acc[(i * 5 + 3) % len(acc)]; d, co = fx["data"], fx["company"]
        res = {"error": "period_not_available", "requested": "FY2026","available_periods": {"FY2025": d["rev"][2], "FY2024": d["rev"][1],"FY2023": d["rev"][0]}}
        msgs = [{"role": "user", "content": "Pull FY2026 revenue for %s." % co},{"role": "assistant", "content": "Calling get_financial_metric for FY2026.\n" + json.dumps({"tool": "get_financial_metric","arguments": {"entity": co, "metrics": ["revenue"],"periods": ["FY2026"]}})},{"role": "tool", "content": json.dumps(res)},{"role": "user", "content": "Use FY2025 instead. What was revenue, in millions?"}]
        emit("tool|wrong_period|" + str(i), msgs, [TOOL_METRIC], d["rev"][2])

    return out

# =========================================================================== assembly
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls","summarization": "summ", "tool_use": "tool"}
THINK_ON = ("calc", "qa", "tool_use")

def build_text_rows():
    rows = []; seq = dict((t, 0) for t in ABBR)
    for fam in CALC + EXTR + QA + CLS + SUMM:
        pool = BY_TYPE[fam["ftype"]]; n = fam["n"]
        if n > len(pool):
            raise SystemExit("family %s wants %d rows but only %d fixtures" % (fam["key"], n, len(pool)))
        start = int(hashlib.sha256(fam["key"].encode()).hexdigest()[:8], 16) % len(pool)
        for j in range(n):
            fx = pool[(start + j) % len(pool)]; seq[fam["task"]] += 1
            q = fam["q"](fx) if callable(fam["q"]) else fam["q"]
            at, tol, gt = fam["at"], fam["tol"], (fam["gt"](fx["data"]) if fam["gt"] else None)
            if fam["task"] == "summarization":
                at = "text"
                if j % 2 == 0:
                    gt, tol = fam["ref"](fx["data"]), "normalized"
                else:
                    gt, tol = None, None
            rows.append(({ "id": "fin_%s_%s_%06d" % (AREA, ABBR[fam["task"]], seq[fam["task"]]),"task": fam["task"],"source": "synthetic:" + AREA,"context": fx["ctx"],"question": q,"ground_truth": gt,"answer_type": at,"tolerance": tol,"split": "train","thinking": "on" if fam["task"] in THINK_ON else "off",}, fx["key"]))
    for q, gt in KNOW:
        seq["qa"] += 1; at = "number" if isinstance(gt, float) else "label"
        rows.append(({ "id": "fin_%s_qa_%06d" % (AREA, seq["qa"]),"task": "qa","source": "knowledge:finance_general","context": "","question": q,"ground_truth": gt,"answer_type": at,"tolerance": "abs:0.1" if at == "number" else "exact","split": "train","thinking": "on",}, "know|" + q[:40]))
    return rows

def build_all_rows():
    rows = build_text_rows(); seq = 0
    for t in build_tool_rows():
        seq += 1
        rows.append(({ "id": "fin_%s_tool_%06d" % (AREA, seq),"task": "tool_use","source": "synthetic:" + AREA,"messages": t["messages"],"tools": t["tools"],"ground_truth": t["gt"],"answer_type": t["at"],"tolerance": t["tol"],"split": "train","thinking": "on",}, t["key"]))
    return rows

def assign_splits(rows):
    groups = {}
    for row, fxkey in rows:
        groups.setdefault(fxkey, []).append(row)
    order = sorted(groups.keys(), key=lambda k: hashlib.sha256(k.encode()).hexdigest()); total = len(rows)
    n_train = int(round(0.8 * total)); n_val = int(round(0.1 * total)); cum = 0
    for k in order:
        g = groups[k]
        if cum < n_train:
            sp = "train"
        elif cum < n_train + n_val:
            sp = "val"
        else:
            sp = "test"
        for r in g:
            r["split"] = sp
        cum += len(g)
    return groups

MASK = re.compile(r"\d+(?:[.,]\d+)*")

def mask(s):
    return MASK.sub("#", " ".join(str(s).split()).strip().lower())

def main():
    rows = build_all_rows(); assign_splits(rows); out_rows = [r for r, _ in rows]

    seen = set()
    for r in out_rows:
        if r["id"] in seen:
            raise SystemExit("duplicate id " + r["id"])
        seen.add(r["id"])

    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n"
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(payload)

    from collections import Counter
    by_task = Counter(r["task"] for r in out_rows); by_split = Counter(r["split"] for r in out_rows)
    by_at = Counter(r["answer_type"] for r in out_rows if r["ground_truth"] is not None); fams = Counter()
    ctxs = set()
    for r in out_rows:
        src = r["messages"][0]["content"] if "messages" in r else r["question"]; fams[mask(src)[:160]] += 1
        if "context" in r and r["context"]:
            ctxs.add(mask(r["context"]))
    body_keys = {}
    for r in out_rows:
        if "context" in r and r["context"]:
            k = mask(r["context"]) + "|" + mask(r["question"]); body_keys[k] = body_keys.get(k, 0) + 1
    near = sum(v - 1 for v in body_keys.values() if v > 1); top = fams.most_common(1)[0]
    tool_rows = [r for r in out_rows if r["task"] == "tool_use"]
    multi = sum(1 for r in tool_rows if any(m["role"] == "assistant" for m in r["messages"]))

    rep = { "area": AREA,"profile": "B","rows": len(out_rows),"by_task": dict(by_task),"by_split": dict(by_split),"by_answer_type": dict(by_at),"distinct_question_families": len(fams),"top_family_share": round(top[1] / float(len(out_rows)), 4),"distinct_contexts": len(ctxs),"near_dup_pairs": near,"tool_use_multi_step_share": round(multi / float(len(tool_rows)), 3),"validation": "pass","sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),"notes": "Synthetic forensic-accounting fixtures; all derived numbers recomputed in code.",}
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2); fh.write("\n")
    print(json.dumps(rep, indent=2)); print("top family:", top[0][:100], top[1])

if __name__ == "__main__":
    main()
