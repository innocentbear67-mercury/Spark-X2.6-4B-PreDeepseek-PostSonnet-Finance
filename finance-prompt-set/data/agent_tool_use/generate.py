#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic generator for the agent_tool_use area of the finance prompt set.

1000 rows: 400 tool_use trajectories over six JSON-schema tools (tool-role JSON payloads,
wrong-argument repair, ambiguous names, conflicting outputs, abstention) plus 600
single-turn rows across calc / extraction / qa / classification / summarization.
Every derived number is computed from the fixture dict rendered into the context or the
tool payload; nothing is typed twice.
"""
import hashlib
import json
import os
import random
import re
from collections import Counter

AREA = "agent_tool_use"
SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
TASK_ORDER = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls",
        "summarization": "summ", "tool_use": "tool"}
THINK = {"calc": "on", "extraction": "off", "qa": "on", "classification": "off",
         "summarization": "off", "tool_use": "on"}
SPECS = [
    ("halcyon", "Halcyon Grid Utilities", "utilities", "31 December", "USD", "Regulated Grid|Retail Supply|Renewables"),
    ("meridian", "Meridian Bancorp", "financials", "31 December", "USD", "Commercial Banking|Wealth Management|Treasury Services"),
    ("kestrel", "Kestrel Foods", "consumer", "30 June", "USD", "Packaged Foods|Fresh Produce|Foodservice"),
    ("ardent", "Ardent Semiconductor", "technology", "31 December", "USD", "Compute Products|Analog Devices|Licensing"),
    ("blueharbor", "Blue Harbor Shipping", "industrials", "31 December", "USD", "Container Shipping|Port Services|Freight Forwarding"),
    ("cobalt", "Cobalt Ridge Mining", "industrials", "31 December", "AUD", "Iron Ore|Copper Concentrate|Logistics"),
    ("vantage", "Vantage Point Health", "healthcare", "31 December", "USD", "Hospitals|Outpatient Clinics|Diagnostics"),
    ("larkspur", "Larkspur Energy", "utilities", "31 December", "CAD", "Upstream Oil|Gas Storage|Power Trading"),
    ("northwind", "Northwind Logistics", "industrials", "31 March", "EUR", "Contract Logistics|Last Mile|Warehousing"),
    ("silverbrook", "Silverbrook Pharmaceuticals", "healthcare", "31 December", "USD", "Branded Drugs|Generics|Contract Manufacturing"),
    ("tidewater", "Tidewater Realty Trust", "financials", "31 December", "USD", "Office Properties|Industrial Properties|Mixed Use"),
    ("juniper", "Juniper Lane Retail", "consumer", "31 January", "USD", "Apparel|Home Goods|E-Commerce"),
    ("ironvale", "Ironvale Steel", "industrials", "31 December", "EUR", "Flat Products|Long Products|Scrap Recycling"),
    ("pinecrest", "Pinecrest Insurance", "financials", "31 December", "USD", "Property Casualty|Life|Reinsurance"),
    ("quarry", "Quarry Lane Software", "technology", "31 December", "GBP", "Subscription Software|Services|Support"),
    ("verdant", "Verdant Agriculture", "consumer", "30 September", "USD", "Grain Trading|Fertilizer|Livestock"),
    ("summit", "Summit Peaks Airlines", "industrials", "31 December", "USD", "Domestic Routes|International Routes|Cargo"),
    ("ferrous", "Ferrous Bay Chemicals", "industrials", "31 December", "EUR", "Specialty Chemicals|Polymers|Agrochemicals"),
    ("alder", "Alder Grove Telecom", "technology", "31 December", "CAD", "Mobile|Fixed Broadband|Enterprise Data"),
    ("willow", "Willow Bend Hotels", "consumer", "31 December", "USD", "Rooms|Food and Beverage|Management Fees"),
    ("granite", "Granite Hill Capital", "financials", "31 December", "USD", "Asset Management|Private Credit|Advisory"),
    ("solstice", "Solstice Solar Group", "utilities", "31 December", "EUR", "Solar Generation|Storage|Development"),
    ("marlowe", "Marlowe Diagnostics", "healthcare", "31 December", "CHF", "Reagents|Instruments|Lab Services"),
    ("copperline", "Copperline Rail", "industrials", "31 December", "CAD", "Freight Rail|Intermodal|Real Estate"),
    ("basalt", "Basalt Water Works", "utilities", "31 December", "USD", "Water Utility|Wastewater|Infrastructure Services"),
]
COMPANIES = [{"idx": i, "key": s[0], "name": s[1], "sector": s[2], "fy_end": s[3],
              "ccy": s[4], "segs": s[5].split("|")} for i, s in enumerate(SPECS)]
PEERS = dict((c["key"], [COMPANIES[(c["idx"] + d) % 25] for d in (1, 3, 7, 11)]) for c in COMPANIES)
AUDITORS = ["Verrill & Hask LLP", "Pemberton Ross LLP", "Aldrich Wynn & Co",
            "Calloway Fiske LLP", "Draven & Poole LLP"]
GM_RANGE = {"utilities": (0.28, 0.45), "financials": (0.40, 0.62), "consumer": (0.30, 0.46),
            "technology": (0.52, 0.72), "industrials": (0.20, 0.36), "healthcare": (0.46, 0.66)}

def r1(x):
    return round(float(x) + 0.0, 1)

def r2(x):
    return round(float(x) + 0.0, 2)

def f1(x):
    return "%.1f" % x

def f2(x):
    return "%.2f" % x

def units_line(ccy):
    return ("Units: %s in millions except per-share amounts in %s and percentages "
            "in percent." % (ccy, ccy))

def tbl(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)

def median(vals):
    v = sorted(vals)
    n = len(v)
    return v[n // 2] if n % 2 else r2((v[n // 2 - 1] + v[n // 2]) / 2.0)

def terciles(vals):
    v = sorted(vals)
    return (v[len(v) // 3], v[(2 * len(v)) // 3])

# ------------------------------------------------------------------ fixtures
def fin_year(rev, shares, p):
    cogs = r1(rev * (1.0 - p["gm"]))
    gp = r1(rev - cogs)
    opex = r1(gp * p["opex"])
    opinc = r1(gp - opex)
    interest = r1(opinc * p["int"])
    pretax = r1(opinc - interest)
    tax = r1(pretax * p["tax"])
    ni = r1(pretax - tax)
    return {"rev": rev, "cogs": cogs, "gp": gp, "opex": opex, "opinc": opinc,
            "interest": interest, "pretax": pretax, "tax": tax, "ni": ni,
            "eps": r2(ni / shares), "shares": shares,
            "cfo": r1(ni * p["cfo"]), "capex": r1(rev * p["capex"]), "da": r1(rev * p["da"]),
            "divs": r1(ni * p["div"]), "assets": r1(rev * p["assets"]),
            "equity": r1(rev * p["eq"]), "debt": r1(rev * p["debt"]),
            "ca": r1(rev * p["ca"]), "cl": r1(rev * p["cl"]), "cash": r1(rev * p["cash"])}

def build_fixtures():
    out = {}
    for c in COMPANIES:
        rng = random.Random(SEED + c["idx"] * 17)
        rev24 = r1(rng.uniform(1400.0, 8800.0))
        rev25 = r1(rev24 * (1.0 + rng.uniform(-0.06, 0.18)))
        shares25 = r1(r1(rev25 * rng.uniform(0.05, 0.14)) / rng.uniform(1.2, 6.5))
        p = {"gm": rng.uniform(*GM_RANGE[c["sector"]]), "opex": rng.uniform(0.34, 0.70),
             "int": rng.uniform(0.06, 0.22), "tax": rng.uniform(0.18, 0.30),
             "cfo": rng.uniform(1.05, 1.85), "capex": rng.uniform(0.035, 0.10),
             "da": rng.uniform(0.03, 0.07), "div": rng.uniform(0.10, 0.45),
             "assets": rng.uniform(1.0, 2.1), "eq": rng.uniform(0.35, 0.95),
             "debt": rng.uniform(0.25, 0.85), "ca": rng.uniform(0.30, 0.75),
             "cl": rng.uniform(0.16, 0.40), "cash": rng.uniform(0.08, 0.28)}
        p24 = dict(p)
        p24["gm"] = min(0.70, max(0.18, p["gm"] + rng.uniform(-0.025, 0.025)))
        p24["opex"] = p["opex"] * rng.uniform(0.97, 1.03)
        p24["tax"] = p["tax"] * rng.uniform(0.95, 1.05)
        p24["int"] = p["int"] * rng.uniform(0.90, 1.10)
        for k in ("assets", "eq", "debt", "ca", "cl", "cash", "capex", "da", "cfo", "div"):
            p24[k] = p[k] * rng.uniform(0.95, 1.05)
        y25 = fin_year(rev25, shares25, p)
        y24 = fin_year(rev24, r1(shares25 * rng.uniform(0.97, 1.04)), p24)
        f = {"ccy": c["ccy"], "auditor": AUDITORS[c["idx"] % len(AUDITORS)]}
        for tag, y in (("25", y25), ("24", y24)):
            for k, v in y.items():
                f[k + tag] = v
        f["price"] = r2(y25["eps"] * rng.uniform(9.0, 24.0))
        f["pe"] = r2(f["price"] / y25["eps"])
        f["mcap"] = r1(f["price"] * shares25)
        f["dps"] = r2(y25["divs"] / shares25)
        f["dy"] = r2(f["dps"] / f["price"] * 100.0)
        f["hi"] = r2(f["price"] * rng.uniform(1.05, 1.30))
        f["lo"] = r2(f["price"] * rng.uniform(0.62, 0.95))
        f["vol"] = int(rng.uniform(400, 9000)) * 1000
        for k, num, den in (("gm", "gp", "rev"), ("nm", "ni", "rev"), ("om", "opinc", "rev")):
            f[k + "25"] = r2(y25[num] / y25[den] * 100.0)
            f[k + "24"] = r2(y24[num] / y24[den] * 100.0)
        f["roe25"] = r2(y25["ni"] / y25["equity"] * 100.0)
        f["cr25"] = r2(y25["ca"] / y25["cl"])
        f["de25"] = r2(y25["debt"] / y25["equity"])
        f["ic25"] = r2(y25["opinc"] / y25["interest"])
        f["at25"] = r2(y25["rev"] / y25["assets"])
        f["fcf25"] = r1(y25["cfo"] - y25["capex"])
        f["fcf24"] = r1(y24["cfo"] - y24["capex"])
        f["ebitda25"] = r1(y25["opinc"] + y25["da"])
        f["nd_ebitda"] = r2((y25["debt"] - y25["cash"]) / f["ebitda25"])
        f["growth25"] = r1((y25["rev"] / y24["rev"] - 1.0) * 100.0)
        f["bps_gm"] = r1((f["gm25"] - f["gm24"]) * 100.0)
        f["bps_om"] = r1((f["om25"] - f["om24"]) * 100.0)
        f["cover"] = r2(f["fcf25"] / y25["divs"])
        f["buyback"] = r1(y24["shares"] * rng.uniform(0.005, 0.025))
        w = [rng.uniform(0.20, 0.50), rng.uniform(0.15, 0.40)]
        w.append(max(0.12, 1.0 - w[0] - w[1]))
        w = [x / sum(w) for x in w]
        f["segs"] = []
        for j, nm in enumerate(c["segs"]):
            sr = r1(rev25 * w[j]) if j < 2 else r1(rev25 - sum(x["rev"] for x in f["segs"]))
            f["segs"].append({"name": nm, "rev": sr, "cost": r1(sr * rng.uniform(0.55, 0.85)),
                              "rev24": r1(sr / (1.0 + rng.uniform(-0.05, 0.22)))})
        qw = [rng.uniform(0.82, 1.18) for _ in range(4)]
        qrev = [r1(rev25 * x / sum(qw)) for x in qw[:3]]
        qrev.append(r1(rev25 - sum(qrev)))
        f["q"] = [{"label": "Q%d FY2025" % (j + 1), "rev": qrev[j],
                   "gp": r1(qrev[j] * f["gm25"] / 100.0),
                   "ni": r1(qrev[j] * f["nm25"] / 100.0)} for j in range(4)]
        adj = [0.018, 0.0, -0.022][c["idx"] % 3]
        f["cons_rev"] = r1(rev25 / (1.0 + adj))
        f["cons_eps"] = r2(y25["eps"] * (1.0 - adj * 0.7))
        f["fac"] = [("Term loan A", r1(y25["debt"] * 0.30), 5.4, 2029),
                    ("Senior notes", r1(y25["debt"] * 0.50), 4.8, 2031),
                    ("Revolver (undrawn)", r1(y25["debt"] * 0.20), 5.1, 2028)]
        out[c["key"]] = f
    return out

FIX = build_fixtures()
BY_NAME = dict((c["name"], c) for c in COMPANIES)
MAX_REV = max(FIX[c["key"]]["rev25"] for c in COMPANIES)

def V(c, key):
    if callable(key):
        return key(FIX[c["key"]])
    return FIX[c["key"]][key] if isinstance(key, str) else key

# ------------------------------------------------------------------ tool schemas
TOOLS = [
    {"name": "get_quote", "parameters": {"type": "object", "properties": {
        "company": {"type": "string", "description": "Legal or short name of the issuer"},
        "fields": {"type": "array", "description": "Subset of fields to return; omit for all",
                   "items": {"type": "string", "enum": ["price", "volume", "market_cap",
                                                        "pe_ratio", "dividend_yield", "week52"]}}},
        "required": ["company"]},
     "description": ("Return an equity quote for a covered issuer. Delayed unless the response "
                     "says real_time. Raises ambiguous_company if the name maps to two issuers.")},
    {"name": "get_financials", "parameters": {"type": "object", "properties": {
        "company": {"type": "string"},
        "fiscal_year": {"type": "integer", "description": "Four digit fiscal year"},
        "statement": {"type": "string", "enum": ["income", "balance", "cashflow", "all"]}},
        "required": ["company", "fiscal_year"]},
     "description": ("Return filed income statement, balance sheet and cash flow line items for "
                     "one issuer and one fiscal year.")},
    {"name": "screen_companies", "parameters": {"type": "object", "properties": {
        "sector": {"type": "string", "enum": ["utilities", "financials", "consumer", "technology",
                                              "industrials", "healthcare"]},
        "min_revenue": {"type": "number", "description": "FY2025 revenue floor in millions"},
        "max_pe": {"type": "number", "description": "P/E ceiling"},
        "min_roe": {"type": "number", "description": "ROE floor in percent"},
        "sort_by": {"type": "string", "enum": ["revenue", "net_margin", "pe", "roe"]},
        "benchmark_company": {"type": "string", "description": "Issuer echoed as the screen benchmark"},
        "limit": {"type": "integer", "description": "Maximum rows to return"}}, "required": []},
     "description": ("Filter the coverage universe on sector, revenue, P/E and ROE. Returns a "
                     "ranked list plus the total match count.")},
    {"name": "search_filings", "parameters": {"type": "object", "properties": {
        "company": {"type": "string"},
        "form_type": {"type": "string", "enum": ["10-K", "10-Q", "8-K", "DEF 14A"]},
        "year": {"type": "integer", "description": "Fiscal year of the filing"},
        "keyword": {"type": "string", "description": "Free text search across sections"}},
        "required": ["company"]},
     "description": ("Search the filing index for an issuer. Returns filing metadata (form type, "
                     "period, filed date, accession number) and section hits.")},
    {"name": "compute_ratio", "parameters": {"type": "object", "properties": {
        "numerator": {"type": "number"}, "denominator": {"type": "number"},
        "ratio": {"type": "string", "enum": ["gross_margin", "net_margin", "roe",
                                             "current_ratio", "debt_to_equity", "asset_turnover"]},
        "scale": {"type": "string", "enum": ["percent", "x"]}},
        "required": ["numerator", "denominator", "ratio"]},
     "description": ("Compute a named ratio from two numeric inputs. Percentage ratios require "
                     "scale percent; turnover and leverage ratios use scale x.")},
    {"name": "get_peer_set", "parameters": {"type": "object", "properties": {
        "company": {"type": "string"},
        "metric": {"type": "string", "enum": ["pe_ratio", "roe", "revenue_growth", "ev_ebitda"]},
        "max_peers": {"type": "integer"}}, "required": ["company", "metric"]},
     "description": ("Return the curated peer group for an issuer with one comparison metric, the "
                     "subject row and the subject's rank (1 = highest).")},
]

# ------------------------------------------------------------------ payloads
def q_payload(c, fields=None):
    f = FIX[c["key"]]
    fs = fields or ["price", "volume", "market_cap", "pe_ratio", "dividend_yield", "week52"]
    d = {"company": c["name"], "currency": f["ccy"], "as_of": "2025-09-30",
         "data_quality": "real_time", "returned_fields": fs}
    for name, key, label in (("price", "price", "price"), ("volume", "vol", "volume"),
                             ("market_cap", "mcap", "market_cap_millions"), ("pe_ratio", "pe", "pe_ratio"),
                             ("dividend_yield", "dy", "dividend_yield_pct")):
        if name in fs:
            d[label] = f[key]
    if "week52" in fs:
        d["week52_high"], d["week52_low"] = f["hi"], f["lo"]
    return d

def fin_payload(c, year):
    f, y = FIX[c["key"]], "25" if year == 2025 else "24"
    return {"company": c["name"], "fiscal_year": year, "fiscal_year_end": c["fy_end"],
            "currency": f["ccy"], "units": "millions except per-share amounts",
            "source": "annual_report_filed",
            "income_statement": {"revenue": f["rev" + y], "cost_of_revenue": f["cogs" + y],
                                 "gross_profit": f["gp" + y], "operating_expenses": f["opex" + y],
                                 "operating_income": f["opinc" + y], "interest_expense": f["interest" + y],
                                 "pretax_income": f["pretax" + y], "tax_expense": f["tax" + y],
                                 "net_income": f["ni" + y]},
            "balance_sheet": {"total_assets": f["assets" + y], "current_assets": f["ca" + y],
                              "cash": f["cash" + y], "total_debt": f["debt" + y],
                              "current_liabilities": f["cl" + y], "total_equity": f["equity" + y]},
            "cash_flow": {"operating_cash_flow": f["cfo" + y], "capital_expenditure": f["capex" + y],
                          "depreciation_amortization": f["da" + y], "dividends_paid": f["divs" + y]},
            "per_share": {"diluted_shares_millions": f["shares" + y], "diluted_eps": f["eps" + y]}}

def screen_payload(sector=None, min_revenue=None, max_pe=None, min_roe=None,
                   sort_by="revenue", limit=5, skew=None, benchmark=None):
    rows = []
    for c in COMPANIES:
        f = FIX[c["key"]]
        if sector and c["sector"] != sector:
            continue
        if min_revenue is not None and f["rev25"] < min_revenue:
            continue
        if max_pe is not None and f["pe"] > max_pe:
            continue
        if min_roe is not None and f["roe25"] < min_roe:
            continue
        rows.append({"company": c["name"], "sector": c["sector"], "revenue_fy2025": f["rev25"],
                     "net_margin_pct": f["nm25"], "pe_ratio": f["pe"], "roe_pct": f["roe25"],
                     "net_debt_to_ebitda": f["nd_ebitda"]})
    k = {"revenue": "revenue_fy2025", "net_margin": "net_margin_pct",
         "pe": "pe_ratio", "roe": "roe_pct"}[sort_by]
    rows.sort(key=lambda r: r[k], reverse=(k != "pe_ratio"))
    if skew:
        for r in rows:
            if r["company"] == skew[0]:
                r["revenue_fy2025"] = r1(r["revenue_fy2025"] * skew[1])
    return {"query": {"sector": sector, "min_revenue": min_revenue, "max_pe": max_pe,
                      "min_roe": min_roe, "sort_by": sort_by, "limit": limit,
                      "benchmark_company": benchmark}, "benchmark_company": benchmark,
            "source": "vendor_snapshot", "as_of": "2024-11-02",
            "note": "vendor snapshot; not restated after the FY2025 annual report",
            "count": len(rows), "results": rows[:limit]}

def run_screen(q, skew=None):
    return screen_payload(q.get("sector"), q.get("min_revenue"), q.get("max_pe"), q.get("min_roe"),
                          q.get("sort_by", "revenue"), q.get("limit", 5), skew,
                          q.get("benchmark_company"))

def filing_head(c):
    i = c["idx"]
    return ("0001%03d-25-%06d" % (400 + i * 7, 1100 + i * 13), "2026-02-%02d" % (10 + i % 9))

def filings_payload(c):
    acc, filed = filing_head(c)
    i = c["idx"]
    return {"company": c["name"], "count": 3,
            "coverage": "annual and quarterly reports indexed from 2021",
            "filings": [
                {"form_type": "10-K", "period": "FY2025", "filed": filed, "accession": acc,
                 "sections": ["Business", "Risk Factors", "MD&A", "Financial Statements"]},
                {"form_type": "10-Q", "period": "Q3 FY2025", "filed": "2025-11-%02d" % (2 + i % 8),
                 "accession": "0001%03d-25-%06d" % (400 + i * 7, 2400 + i * 5),
                 "sections": ["MD&A", "Financial Statements"]},
                {"form_type": "8-K", "period": "Q2 FY2025", "filed": "2025-08-%02d" % (11 + i % 9),
                 "accession": "0001%03d-25-%06d" % (400 + i * 7, 3600 + i * 3),
                 "sections": ["Results of operations"]}]}

def peer_payload(c, metric):
    if metric == "ev_ebitda":
        return {"company": c["name"], "metric": metric, "error": "metric_unavailable",
                "detail": "ev_ebitda is not carried for this coverage set",
                "available_metrics": ["pe_ratio", "roe", "revenue_growth"]}
    rows = [{"company": p["name"], "pe_ratio": FIX[p["key"]]["pe"], "roe_pct": FIX[p["key"]]["roe25"],
             "revenue_growth_pct": FIX[p["key"]]["growth25"]} for p in [c] + PEERS[c["key"]]]
    field = {"pe_ratio": "pe_ratio", "roe": "roe_pct", "revenue_growth": "revenue_growth_pct"}[metric]
    rows.sort(key=lambda r: r[field], reverse=(metric != "pe_ratio"))
    subj = [r for r in rows if r["company"] == c["name"]][0]
    return {"company": c["name"], "metric": metric, "peer_count": len(rows) - 1,
            "rank": 1 + len([r for r in rows if r[field] > subj[field]]), "subject": subj,
            "peers": [r for r in rows if r["company"] != c["name"]]}

def ratio_payload(num, den, ratio, scale):
    if ratio in ("gross_margin", "net_margin", "roe"):
        if scale != "percent":
            return {"error": "invalid_scale", "ratio": ratio, "allowed": ["percent"],
                    "detail": "%s is a percentage ratio; use scale percent" % ratio}
        return {"ratio": ratio, "value": r2(num / den * 100.0), "scale": "percent",
                "inputs": {"numerator": num, "denominator": den}}
    if scale != "x":
        return {"error": "invalid_scale", "ratio": ratio, "allowed": ["x"],
                "detail": "%s is a multiple; use scale x" % ratio}
    return {"ratio": ratio, "value": r2(num / den), "scale": "x",
            "inputs": {"numerator": num, "denominator": den}}

# ------------------------------------------------------------------ messages
def U(text):
    return {"role": "user", "content": text}

def A_(tool, args):
    return {"role": "assistant", "content": json.dumps({"tool": tool, "arguments": args})}

def R_(payload):
    return {"role": "tool", "content": json.dumps(payload)}

SYS = {"role": "system", "content": ("You are a research assistant. Every number must come from a "
                                     "tool result; if a tool cannot supply a figure, say so rather "
                                     "than estimating.")}

def flow(opening, tail, gt, at="number", tol="abs:0.1"):
    return {"msgs": [SYS, U(opening)] + tail, "gt": gt, "at": at, "tol": tol}

def one(tool, args, payload, opening, question, gt, tol="abs:0.1", at="number"):
    return flow(opening, [A_(tool, args), R_(payload), U(question)], gt, at, tol)

def two(steps, opening, question, gt, tol="abs:0.1", at="number"):
    tail = []
    for tool, args, payload in steps:
        tail += [A_(tool, args), R_(payload)]
    return flow(opening, tail + [U(question)], gt, at, tol)

def fin_step(c, year):
    return ("get_financials", {"company": c["name"], "fiscal_year": year}, fin_payload(c, year))

# ------------------------------------------------------------------ tool flows
def q_pe(c):
    return one("get_quote", {"company": c["name"]}, q_payload(c),
               "Pull a market quote for this issuer and confirm the last traded price.",
               "What P/E ratio does that quote carry? Give one decimal.", FIX[c["key"]]["pe"])

def q_mcap(c):
    return one("get_quote", {"company": c["name"]}, q_payload(c),
               "I need the equity market snapshot for the name in the file.",
               "What market capitalisation, in millions, does the snapshot show?",
               FIX[c["key"]]["mcap"], "abs:1")

def q_div(c):
    f = FIX[c["key"]]
    return one("get_quote", {"company": c["name"]}, q_payload(c),
               "Get me the quote for the issuer and tell me what the dividend looks like.",
               "What annual dividend per share does the quoted yield imply at that price? Give two "
               "decimals.", r2(f["price"] * f["dy"] / 100.0), "abs:0.01")

def q_range(c):
    f = FIX[c["key"]]
    return one("get_quote", {"company": c["name"]}, q_payload(c),
               "How has the share price behaved against its own fifty-two week range?",
               "How far below the fifty-two week high is the quoted price, in percent? Give two "
               "decimals.", r2((f["hi"] - f["price"]) / f["hi"] * 100.0), "abs:0.01")

def q_fields(c):
    f = FIX[c["key"]]
    return flow("Start with the price only, then widen the field list if you need to.",
                [A_("get_quote", {"company": c["name"], "fields": ["price"]}),
                 R_(q_payload(c, ["price"])),
                 A_("get_quote", {"company": c["name"], "fields": ["price", "pe_ratio", "dividend_yield"]}),
                 R_(q_payload(c, ["price", "pe_ratio", "dividend_yield"])),
                 U("What dividend yield, in percent, does the widened quote show?")], f["dy"],
                "number", "abs:0.01")

def q_miss(c):
    bad = c["name"].split()[0] + " Holdings"
    return flow("Check whether the data tool covers the holding company before we screen.",
                [A_("get_quote", {"company": bad}),
                 R_({"error": "not_found", "query": bad, "suggestions": [c["name"]],
                     "coverage": "25 issuers; no entity matches that legal name"}),
                 U("What price should I use for %s in the screen?" % bad)],
                "no price is available: the tool returned not_found and the entity is outside "
                "coverage", "text", "normalized")

def fin_growth(c):
    return two([fin_step(c, 2025), fin_step(c, 2024)],
               "I need the two year revenue trend for this issuer.",
               "What was FY2025 revenue growth over FY2024, in percent? One decimal.",
               FIX[c["key"]]["growth25"])

def fin_badyear(c):
    return two([("get_financials", {"company": c["name"], "fiscal_year": 2026},
                 {"error": "fiscal_year_out_of_range", "requested": 2026, "company": c["name"],
                  "available_years": [2022, 2023, 2024, 2025]}), fin_step(c, 2025)],
               "Pull FY2026 for this issuer so we can compare with the prior year.",
               "Using the latest available year, what was FY2025 revenue, in millions?",
               FIX[c["key"]]["rev25"])

def scr_top(c):
    q = {"sector": c["sector"], "min_revenue": r1(FIX[c["key"]]["rev25"] * 0.45),
         "sort_by": "revenue", "limit": 5, "benchmark_company": c["name"]}
    rows = run_screen(q)
    return one("screen_companies", q, rows,
               "Screen the coverage universe for the largest names in this sector.",
               "Which company in that screen has the highest FY2025 revenue? Give the name exactly "
               "as shown.", rows["results"][0]["company"], "normalized", "text")

def scr_drill(c):
    q = {"sector": c["sector"], "min_roe": r2(FIX[c["key"]]["roe25"] * 0.85),
         "sort_by": "net_margin", "limit": 3, "benchmark_company": c["name"]}
    rows = run_screen(q)
    top = BY_NAME[rows["results"][0]["company"]]
    return two([("screen_companies", q, rows), fin_step(top, 2025)],
               "Find the most profitable name in this sector, then pull its financials.",
               "What gross margin, in percent, did that company report for FY2025? One decimal.",
               FIX[top["key"]]["gm25"])

def scr_empty(c):
    q = {"min_revenue": r1(MAX_REV + FIX[c["key"]]["rev25"] * 0.1), "sort_by": "revenue",
         "limit": 5, "benchmark_company": c["name"]}
    return one("screen_companies", q, run_screen(q),
               "Screen for issuers larger than anything in the coverage set.",
               "Can the peer comparison be built from that screen? Reply with one label from "
               "{usable, abstain}.", "abstain", "exact", "label")

def scr_median(c):
    q = {"max_pe": r2(FIX[c["key"]]["pe"] * 1.45), "sort_by": "pe", "limit": 5,
         "benchmark_company": c["name"]}
    rows = run_screen(q)
    return one("screen_companies", q, rows,
               "I want the typical P/E of a small screen, not the average.",
               "What is the median P/E across the companies returned? Two decimals.",
               median([r["pe_ratio"] for r in rows["results"]]), "abs:0.01")

def scr_badarg(c):
    thr = r1(FIX[c["key"]]["rev25"] * 0.55)
    bad = "%s millions" % f1(thr)
    q = {"sector": c["sector"], "min_revenue": thr, "limit": 10, "benchmark_company": c["name"]}
    rows = run_screen(q)
    return two([("screen_companies", {"sector": c["sector"], "min_revenue": bad},
                 {"error": "invalid_argument", "argument": "min_revenue", "example": thr,
                  "detail": "expected a number in millions, received string '%s'" % bad}),
                ("screen_companies", q, rows)],
               "Run a revenue screen but I only have the threshold in text form.",
               "How many companies matched the corrected screen?", rows["count"])

def fil_acc(c):
    p = filings_payload(c)
    return one("search_filings", {"company": c["name"], "form_type": "10-K"}, p,
               "Find the most recent annual report on file for this issuer.",
               "What is the accession number of the most recent 10-K? Quote it exactly.",
               p["filings"][0]["accession"], "exact", "text")

def fil_kw(c):
    return one("search_filings", {"company": c["name"], "keyword": "impairment"},
               {"company": c["name"], "keyword": "impairment", "count": 1, "matches": [
                   {"form_type": "10-K", "period": "FY2025", "section": "Critical accounting estimates",
                    "snippet": "impairment of goodwill is tested annually"}]},
               "Search the filings for impairment language.",
               "Which section carries the impairment discussion? Give the section name exactly as "
               "shown.", "Critical accounting estimates", "normalized", "text")

def fil_badform(c):
    p = filings_payload(c)
    return two([("search_filings", {"company": c["name"], "form_type": "10K"},
                 {"error": "invalid_enum", "argument": "form_type", "received": "10K",
                  "allowed": ["10-K", "10-Q", "8-K", "DEF 14A"]}),
                ("search_filings", {"company": c["name"], "form_type": "10-K", "year": 2025}, p)],
               "Search for a 10K filing in the archive.",
               "On what date was the FY2025 10-K filed? Reply YYYY-MM-DD.",
               p["filings"][0]["filed"], "exact", "text")

def fil_none(c):
    return one("search_filings", {"company": c["name"], "form_type": "DEF 14A", "year": 2019},
               {"company": c["name"], "count": 0, "matches": [],
                "coverage": "proxy filings are indexed from 2021 onward"},
               "Look for the proxy statement covering FY2019.",
               "What proxy filing date should be cited for FY2019? Reply with one label from "
               "{found, abstain}.", "abstain", "exact", "label")

def ratio_gm(c):
    f = FIX[c["key"]]
    return two([fin_step(c, 2025),
                ("compute_ratio", {"numerator": f["gp25"], "denominator": f["rev25"],
                                   "ratio": "gross_margin", "scale": "percent"},
                 ratio_payload(f["gp25"], f["rev25"], "gross_margin", "percent"))],
               "Pull the FY2025 statement and run the gross margin through the ratio tool.",
               "What gross margin, in percent, did the ratio tool return? Two decimals.",
               f["gm25"], "abs:0.01")

def ratio_scale(c):
    f = FIX[c["key"]]
    return two([fin_step(c, 2025),
                ("compute_ratio", {"numerator": f["gp25"], "denominator": f["rev25"],
                                   "ratio": "gross_margin", "scale": "x"},
                 ratio_payload(f["gp25"], f["rev25"], "gross_margin", "x")),
                ("compute_ratio", {"numerator": f["gp25"], "denominator": f["rev25"],
                                   "ratio": "gross_margin", "scale": "percent"},
                 ratio_payload(f["gp25"], f["rev25"], "gross_margin", "percent"))],
               "Run gross margin through the ratio tool with the multiplier convention.",
               "What value did the corrected call return, in percent? Two decimals.",
               f["gm25"], "abs:0.01")

def ratio_at(c):
    f = FIX[c["key"]]
    return two([fin_step(c, 2025),
                ("compute_ratio", {"numerator": f["rev25"], "denominator": f["assets25"],
                                   "ratio": "asset_turnover", "scale": "x"},
                 ratio_payload(f["rev25"], f["assets25"], "asset_turnover", "x"))],
               "How efficiently is the asset base being used?",
               "What asset turnover, in times, did the tool return? Two decimals.",
               f["at25"], "abs:0.01")

def peer_prem(c):
    p = peer_payload(c, "pe_ratio")
    q = q_payload(c, ["price", "pe_ratio"])
    m = median([r["pe_ratio"] for r in p["peers"]])
    return two([("get_peer_set", {"company": c["name"], "metric": "pe_ratio"}, p),
                ("get_quote", {"company": c["name"], "fields": ["price", "pe_ratio"]}, q)],
               "Compare this issuer's earnings multiple with its peer group.",
               "Is the subject at a premium or discount to the peer median P/E, in percent? Give "
               "the signed number to one decimal.", r1((q["pe_ratio"] / m - 1.0) * 100.0))

def peer_rank(c):
    p = peer_payload(c, "roe")
    return one("get_peer_set", {"company": c["name"], "metric": "roe"}, p,
               "Where does this issuer rank on returns within its peer set?",
               "What rank does the subject hold on ROE, where 1 is the highest of the five names?",
               p["rank"], "abs:0.01")

def peer_unavail(c):
    return one("get_peer_set", {"company": c["name"], "metric": "ev_ebitda"},
               peer_payload(c, "ev_ebitda"),
               "Get the peer set on EV/EBITDA so we can compare leverage adjusted multiples.",
               "Can the EV/EBITDA comparison be produced from that result? Reply with one label "
               "from {usable, abstain}.", "abstain", "exact", "label")

def peer_list(c):
    p = peer_payload(c, "pe_ratio")
    return one("get_peer_set", {"company": c["name"], "metric": "pe_ratio"}, p,
               "List the peer set for this issuer and count them.",
               "List the peer company names, excluding the subject.",
               [r["company"] for r in p["peers"]], "set", "list")

def conflict_rev(c):
    q = {"sector": c["sector"], "min_revenue": r1(FIX[c["key"]]["rev25"] * 0.40), "limit": 25,
         "benchmark_company": c["name"]}
    return two([("screen_companies", q, run_screen(q, skew=(c["name"], 0.985))), fin_step(c, 2025)],
               "The screen and the filed accounts disagree on revenue - check both.",
               "Which revenue figure belongs in the model? Reply with one label from "
               "{filed_statement, vendor_snapshot}.", "filed_statement", "exact", "label")

def conflict_eps(c):
    q = q_payload(c, ["price", "pe_ratio"])
    return two([("get_quote", {"company": c["name"], "fields": ["price", "pe_ratio"]}, q),
                fin_step(c, 2025)],
               "The quoted multiple implies an EPS that looks different from the filed one.",
               "What EPS is embedded in the quoted P/E? Two decimals.",
               r2(q["price"] / q["pe_ratio"]), "abs:0.01")

def conflict_price(c):
    f = FIX[c["key"]]
    delayed = r2(f["price"] * 0.988)
    return two([("get_quote", {"company": c["name"], "fields": ["price", "volume"]},
                 q_payload(c, ["price", "volume"])),
                ("get_quote", {"company": c["name"], "fields": ["price"], "as_of": "2025-09-29"},
                 {"company": c["name"], "currency": f["ccy"], "as_of": "2025-09-29",
                  "data_quality": "delayed", "returned_fields": ["price"], "price": delayed,
                  "note": "consolidated close, delayed by one session"})],
               "I have two quotes with different timestamps - one is delayed.",
               "What close does the delayed quote show? Two decimals.", delayed, "abs:0.01")

def ambig_quote(c):
    tok = c["name"].split()[0]
    return two([("get_quote", {"company": tok},
                 {"error": "ambiguous_company", "query": tok, "candidates": [
                     {"company": c["name"], "sector": c["sector"]},
                     {"company": tok + " Holdings", "sector": "unlisted"}]}),
                ("get_quote", {"company": c["name"]}, q_payload(c))],
               "Pull the quote under the short name - the listed parent, not the holding company.",
               "What P/E did the resolved quote show? One decimal.", FIX[c["key"]]["pe"])

def ambig_year(c):
    return two([("get_financials", {"company": c["name"]},
                 {"error": "missing_argument", "argument": "fiscal_year",
                  "detail": "fiscal_year is required; confirm the latest filed period with "
                            "search_filings first"}),
                ("search_filings", {"company": c["name"], "form_type": "10-K"}, filings_payload(c)),
                fin_step(c, 2025)],
               "Get me the last reported full year for this issuer.",
               "What revenue, in millions, did the latest full year report?",
               FIX[c["key"]]["rev25"])

def ambig_segment(c):
    return one("search_filings", {"company": c["name"], "keyword": "grid"},
               {"company": c["name"], "keyword": "grid", "count": 2, "matches": [
                   {"form_type": "10-K", "period": "FY2025", "section": "Business",
                    "snippet": "the grid segment operates regulated networks"},
                   {"form_type": "10-K", "period": "FY2025", "section": "MD&A",
                    "snippet": "grid segment revenue increased on higher tariffs"}]},
               "Search the annual report for the grid segment discussion.",
               "How many sections of the annual report mention the grid segment?", 2, "abs:0.01")

def chain_screen_peer(c):
    q = {"sector": c["sector"], "min_revenue": r1(FIX[c["key"]]["rev25"] * 0.50),
         "sort_by": "revenue", "limit": 1, "benchmark_company": c["name"]}
    scr = run_screen(q)
    top = BY_NAME[scr["results"][0]["company"]]
    p = peer_payload(top, "pe_ratio")
    return two([("screen_companies", q, scr),
                ("get_peer_set", {"company": top["name"], "metric": "pe_ratio"}, p)],
               "Screen the sector, take the largest name, then pull its peer multiples.",
               "What is the median P/E of that peer set, including the subject? Two decimals.",
               median([r["pe_ratio"] for r in p["peers"]] + [p["subject"]["pe_ratio"]]), "abs:0.01")

def chain_quote_fin(c):
    q = q_payload(c, ["price", "pe_ratio"])
    return two([("get_quote", {"company": c["name"], "fields": ["price", "pe_ratio"]}, q),
                fin_step(c, 2025)],
               "Pull the quote and the FY2025 statement, then cross-check the multiple.",
               "What P/E do you get from the quoted price and the FY2025 diluted EPS? One decimal.",
               r1(q["price"] / FIX[c["key"]]["eps25"]))

def chain_bps(c):
    f = FIX[c["key"]]
    return two([fin_step(c, 2024), fin_step(c, 2025),
                ("compute_ratio", {"numerator": f["gp25"], "denominator": f["rev25"],
                                   "ratio": "gross_margin", "scale": "percent"},
                 ratio_payload(f["gp25"], f["rev25"], "gross_margin", "percent"))],
               "Compare the gross margin of the last two years in basis points.",
               "How many basis points did gross margin change versus FY2024? Give the signed "
               "number.", f["bps_gm"], "abs:1")

TOOL_FLOWS = [
    q_pe, q_mcap, q_div, q_range, q_fields, q_miss, fin_growth,
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "Pull the FY2025 income statement and tell me how profitable the top line is.",
                  "What gross margin, in percent, did FY2025 produce? One decimal.",
                  FIX[c["key"]]["gm25"]),
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "What is left for shareholders after everything except financing?",
                  "What net margin, in percent, did FY2025 produce? One decimal.",
                  FIX[c["key"]]["nm25"]),
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "How much of the profit reaches each share?",
                  "What was FY2025 diluted EPS, in the reporting currency? Two decimals.",
                  FIX[c["key"]]["eps25"], "abs:0.01"),
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "I care about cash generation, not accrual earnings.",
                  "What was FY2025 free cash flow, in millions? Use operating cash flow less "
                  "capital expenditure.", FIX[c["key"]]["fcf25"]),
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "Can this issuer pay its near term bills?",
                  "What was the FY2025 current ratio, in times? Two decimals.",
                  FIX[c["key"]]["cr25"], "abs:0.01"),
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "How levered is the balance sheet at the fiscal year end?",
                  "What was total debt to total equity at FY2025 year end, in times? Two decimals.",
                  FIX[c["key"]]["de25"], "abs:0.01"),
    lambda c: one("get_financials", {"company": c["name"], "fiscal_year": 2025}, fin_payload(c, 2025),
                  "Strip out the financing line and tell me how the core business is running.",
                  "What operating margin, in percent, did FY2025 produce? One decimal.",
                  FIX[c["key"]]["om25"]),
    fin_badyear, scr_top, scr_drill, scr_empty, scr_median, scr_badarg,
    fil_acc, fil_kw, fil_badform, fil_none, ratio_gm, ratio_scale, ratio_at,
    peer_prem, peer_rank, peer_unavail, peer_list, conflict_rev, conflict_eps,
    conflict_price, ambig_quote, ambig_year, ambig_segment,
    chain_screen_peer, chain_quote_fin, chain_bps,
]
assert len(TOOL_FLOWS) == 40

# ------------------------------------------------------------------ contexts
def head(c, title, tail=""):
    s = units_line(FIX[c["key"]]["ccy"]) + "\n\n" + c["name"] + " - " + title
    return s + (("\n\n" + tail) if tail else "")

def ctx_income(c):
    f = FIX[c["key"]]
    body = [(lab, f1(f[k + "25"]), f1(f[k + "24"])) for lab, k in (
        ("Revenue", "rev"), ("Cost of revenue", "cogs"), ("Gross profit", "gp"),
        ("Operating expenses", "opex"), ("Operating income", "opinc"),
        ("Interest expense", "interest"), ("Pretax income", "pretax"),
        ("Tax expense", "tax"), ("Net income", "ni"))]
    body.append(("Diluted shares (millions)", f1(f["shares25"]), f1(f["shares24"])))
    body.append(("Diluted EPS (USD)", f2(f["eps25"]), f2(f["eps24"])))
    tail = "Share price at the fiscal year end: %s %s." % (f2(f["price"]), f["ccy"])
    return head(c, "consolidated income statement for the fiscal years ended " + c["fy_end"] + ".", tail) \
        + "\n\n" + tbl(["Item", "FY2025", "FY2024"], body)

def ctx_balance(c):
    f = FIX[c["key"]]
    body = [(lab, f1(f[k + "25"]), f1(f[k + "24"])) for lab, k in (
        ("Total assets", "assets"), ("Current assets", "ca"), ("Cash and equivalents", "cash"),
        ("Current liabilities", "cl"), ("Total debt", "debt"), ("Total equity", "equity"))]
    tail = ("Fiscal year end: %s. Reporting currency: %s. Diluted shares outstanding at the year "
            "end: %s millions. FY2025 revenue: %s millions. FY2025 net income: %s millions."
            % (c["fy_end"], f["ccy"], f1(f["shares25"]), f1(f["rev25"]), f1(f["ni25"])))
    return head(c, "consolidated balance sheet at the fiscal year end.", tail) + "\n\n" + \
        tbl(["Item", "FY2025", "FY2024"], body)

def ctx_cash(c):
    f = FIX[c["key"]]
    rep = r1(f["buyback"] * f["price"])
    body = [("Net cash from operating activities", f1(f["cfo25"]), f1(f["cfo24"])),
            ("Capital expenditure", f1(f["capex25"]), f1(f["capex24"])),
            ("Depreciation and amortization", f1(f["da25"]), f1(f["da24"])),
            ("Dividends paid", f1(f["divs25"]), f1(f["divs24"])),
            ("Share repurchases", f1(rep), f1(r1(rep * 0.8))),
            ("Net change in cash", f1(f["cfo25"] - f["capex25"] - f["divs25"]),
             f1(f["cfo24"] - f["capex24"] - f["divs24"]))]
    return head(c, "consolidated cash flow statement for the fiscal years ended " + c["fy_end"] + ".") \
        + "\n\n" + tbl(["Item", "FY2025", "FY2024"], body)

def ctx_segment(c):
    f = FIX[c["key"]]
    body = [(s["name"], f1(s["rev"]), f1(s["cost"]), f1(s["rev24"])) for s in f["segs"]]
    body.append(("Total", f1(f["rev25"]), "", f1(f["rev24"])))
    return head(c, "segment information for FY2025 with FY2024 comparatives.") + "\n\n" + \
        tbl(["Segment", "FY2025 revenue", "FY2025 segment cost", "FY2024 revenue"], body)

def ctx_quarter(c):
    f = FIX[c["key"]]
    body = [("Revenue",) + tuple(f1(q["rev"]) for q in f["q"]),
            ("Gross profit",) + tuple(f1(q["gp"]) for q in f["q"]),
            ("Net income",) + tuple(f1(q["ni"]) for q in f["q"])]
    return head(c, "quarterly results for FY2025 (unaudited).") + "\n\n" + \
        tbl(["Metric", "Q1 FY2025", "Q2 FY2025", "Q3 FY2025", "Q4 FY2025"], body)

def ctx_filing(c):
    f = FIX[c["key"]]
    acc, filed = filing_head(c)
    body = ("Revenue (a) for FY2025 was %s, compared with %s in FY2024. Gross profit was %s and "
            "operating income was %s. The effective tax rate was %s percent. (a) Revenue is "
            "presented net of excise duties. The FY2024 comparative for \"Other operating income\" "
            "has been restated to conform with the current presentation. The consolidated financial "
            "statements were audited by %s." % (f1(f["rev25"]), f1(f["rev24"]), f1(f["gp25"]),
                                                f1(f["opinc25"]), f1(r1(f["tax25"] / f["pretax25"] * 100.0)),
                                                f["auditor"]))
    return head(c, "annual report excerpt for the fiscal year ended %s (Form 10-K, accession %s, "
                   "filed %s)." % (c["fy_end"], acc, filed), body)

def ctx_memo(c):
    f = FIX[c["key"]]
    body = [("Revenue", f1(f["rev25"]), f1(f["cons_rev"])),
            ("Diluted EPS", f2(f["eps25"]), f2(f["cons_eps"])),
            ("Gross margin (percent)", f2(f["gm25"]), f2(r2(f["gm25"] - 1.1)))]
    tail = ("The consensus column is a broker mean and is not restated for subsequent filing "
            "adjustments. Revenue is stated in %s millions." % f["ccy"])
    return head(c, "results memo against the internal consensus compiled before the fourth quarter "
                   "close.", tail) + "\n\n" + tbl(["Metric", "FY2025 actual", "Consensus"], body)

def ctx_peer(c):
    body = [(p["name"], f1(FIX[p["key"]]["rev25"]), f2(FIX[p["key"]]["nm25"]),
             f2(FIX[p["key"]]["pe"]), f2(FIX[p["key"]]["roe25"])) for p in [c] + PEERS[c["key"]]]
    return head(c, "trading comparables for FY2025 (peers selected by the coverage desk).") + \
        "\n\n" + tbl(["Company", "FY2025 revenue", "Net margin (percent)", "P/E (times)",
                      "ROE (percent)"], body)

def ctx_debt(c):
    f = FIX[c["key"]]
    body = [(nm, f1(p), f1(rt), str(mat)) for nm, p, rt, mat in f["fac"]]
    tail = ("Covenant: total debt must not exceed 3.50 times EBITDA. FY2025 EBITDA was %s millions. "
            "The revolver was undrawn at the year end." % f1(f["ebitda25"]))
    return head(c, "debt facilities outstanding at the FY2025 year end.", tail) + "\n\n" + \
        tbl(["Facility", "Principal", "Rate (percent)", "Maturity"], body)

def ctx_returns(c):
    f = FIX[c["key"]]
    rep = r1(f["buyback"] * f["price"])
    body = [("Dividends paid", f1(f["divs25"]), f1(f["divs24"])),
            ("Share repurchases", f1(rep), f1(r1(rep * 0.8))),
            ("Shares repurchased (millions)", f1(f["buyback"]), f1(r1(f["buyback"] * 0.8))),
            ("Diluted shares (millions)", f1(f["shares25"]), f1(f["shares24"])),
            ("Free cash flow", f1(f["fcf25"]), f1(f["fcf24"]))]
    return head(c, "shareholder returns and cash generation.") + "\n\n" + \
        tbl(["Item", "FY2025", "FY2024"], body)

# ------------------------------------------------------------------ single-turn families
def simple(ctx_fn, question, fn, tol="abs:0.1", at="number"):
    def fam(c):
        return (ctx_fn(c), question, fn(FIX[c["key"]]), at, tol)
    return fam

def fam_q4_gm(c):
    f = FIX[c["key"]]
    q4 = f["q"][3]
    return (ctx_quarter(c), "What was the gross margin in Q4 FY2025, in percent? Give one decimal.",
            r2(q4["gp"] / q4["rev"] * 100.0), "number", "abs:0.1")

def fam_capex_intensity(c):
    f = FIX[c["key"]]
    return (ctx_cash(c), "What percentage of FY2025 operating cash flow was spent on capital "
                         "expenditure? Give one decimal.",
            r2(f["capex25"] / f["cfo25"] * 100.0), "number", "abs:0.1")

def seg_max(f):
    return max(f["segs"], key=lambda s: s["rev"])

CALC_FAMS = [
    simple(ctx_income, "What was the FY2025 gross margin, in percent? Give one decimal.",
           lambda f: f["gm25"]),
    simple(ctx_income, "What was the FY2025 revenue growth over FY2024, in percent? Give one "
                       "decimal.", lambda f: f["growth25"]),
    simple(ctx_income, "What was the FY2025 net margin, in percent? Give one decimal.",
           lambda f: f["nm25"]),
    simple(ctx_income, "What was FY2025 diluted EPS, in USD? Give two decimals.",
           lambda f: f["eps25"], "abs:0.01"),
    simple(ctx_cash, "What was FY2025 free cash flow, in millions? Free cash flow is operating cash "
                     "flow less capital expenditure.", lambda f: f["fcf25"]),
    simple(ctx_balance, "What was FY2025 return on equity, in percent? Use net income over the "
                        "year-end total equity.", lambda f: f["roe25"]),
    simple(ctx_balance, "What was the FY2025 current ratio, in times? Give two decimals.",
           lambda f: f["cr25"], "abs:0.01"),
    simple(ctx_income, "What was the FY2025 interest coverage ratio, in times? Use operating income "
                       "over interest expense.", lambda f: f["ic25"], "abs:0.01"),
    simple(ctx_income, "By how many basis points did the gross margin change from FY2024 to FY2025? "
                       "Give the signed number.", lambda f: f["bps_gm"], "abs:1"),
    simple(ctx_income, "At the fiscal year-end share price, what was the FY2025 P/E ratio? Give one "
                       "decimal.", lambda f: r1(f["price"] / f["eps25"])),
    simple(ctx_segment, "For the largest segment by FY2025 revenue, what was its segment margin, in "
                        "percent? Give one decimal.",
           lambda f: r2((seg_max(f)["rev"] - seg_max(f)["cost"]) / seg_max(f)["rev"] * 100.0)),
]

def fam_accession(c):
    return (ctx_filing(c), "What accession number appears in the excerpt? Quote it exactly.",
            filing_head(c)[0], "text", "exact")

def fam_lowpe(c):
    low = min([c] + PEERS[c["key"]], key=lambda p: FIX[p["key"]]["pe"])
    return (ctx_peer(c), "Which company in the peer table trades at the lowest P/E? Give the name "
                         "exactly as shown.", low["name"], "text", "normalized")

EXTR_FAMS = [
    simple(ctx_income, "What revenue figure is reported for FY2025, in millions? Quote the number "
                       "exactly as shown.", lambda f: f["rev25"]),
    simple(ctx_segment, "Which reportable segment reported the highest FY2025 revenue? Give the "
                        "segment name exactly as shown.", lambda f: seg_max(f)["name"],
           "normalized", "text"),
    simple(ctx_filing, "Which form type is identified in the excerpt?", lambda f: "10-K",
           "normalized", "text"),
    fam_accession,
    simple(ctx_filing, "What effective tax rate is stated in the excerpt, in percent? Give one "
                       "decimal.", lambda f: r1(f["tax25"] / f["pretax25"] * 100.0)),
    simple(ctx_filing, "Which line item is described in the excerpt as restated? Give the name "
                       "exactly as shown.", lambda f: "Other operating income", "normalized", "text"),
    simple(ctx_filing, "Which audit firm signed the financial statements?",
           lambda f: f["auditor"], "normalized", "text"),
    simple(ctx_returns, "How many shares were repurchased in FY2025, in millions?",
           lambda f: f["buyback"]),
    simple(ctx_filing, "Which footnote marker is attached to the revenue figure in the excerpt?",
           lambda f: "(a)", "normalized", "text"),
    simple(ctx_balance, "What fiscal year end does the issuer use?", lambda f: None,
           "normalized", "text"),
]
EXTR_FAMS[-1] = lambda c: (ctx_balance(c), "What fiscal year end does the issuer use?", c["fy_end"],
                           "text", "normalized")

def fam_covenant(c):
    f = FIX[c["key"]]
    lab = "breach" if f["debt25"] / f["ebitda25"] > 3.50 else "compliant"
    return (ctx_debt(c), "Does total debt to EBITDA breach the 3.50 times covenant? Reply with one "
                         "label from {breach, compliant}.", lab, "label", "exact")


QA_FAMS = [
    simple(ctx_segment, "What was the FY2025 revenue growth of the fastest-growing segment, in "
                        "percent? Give one decimal.",
           lambda f: r1(max((s["rev"] / s["rev24"] - 1.0) * 100.0 for s in f["segs"]))),
    simple(ctx_income, "By how many basis points did the operating margin change from FY2024 to "
                       "FY2025? Give the signed number.", lambda f: f["bps_om"], "abs:1"),
    simple(ctx_income, "If operating expenses had grown at the same rate as revenue, what would "
                       "FY2025 operating income have been, in millions? Give one decimal.",
           lambda f: r1(f["gp25"] - f["opex24"] * (f["rev25"] / f["rev24"]))),
    simple(ctx_balance, "The issuer targets asset turnover of 0.90 times. By how much did FY2025 "
                        "asset turnover miss or exceed that target, in times? Give the signed number "
                        "to two decimals.", lambda f: r2(f["at25"] - 0.90), "abs:0.01"),
    fam_lowpe,
    simple(ctx_segment, "What share of FY2025 revenue came from the largest segment, in percent? "
                        "Give one decimal.",
           lambda f: r1(seg_max(f)["rev"] / f["rev25"] * 100.0)),
    simple(ctx_returns, "How many times was the FY2025 dividend covered by free cash flow? Give two "
                        "decimals.", lambda f: f["cover"], "abs:0.01"),
    simple(ctx_returns, "By what percent did the diluted share count change from FY2024 to FY2025? "
                        "Give one decimal.",
           lambda f: r1((f["shares25"] / f["shares24"] - 1.0) * 100.0)),
    simple(ctx_memo, "By how much, in millions, did FY2025 revenue beat or miss the consensus figure? "
                     "Give the signed number.", lambda f: r1(f["rev25"] - f["cons_rev"])),
    simple(ctx_quarter, "Which quarter of FY2025 produced the highest revenue? Reply Q1, Q2, Q3 or "
                        "Q4.", lambda f: max(f["q"], key=lambda q: q["rev"])["label"].split()[0],
           "exact", "label"),
    fam_q4_gm,
    fam_capex_intensity,
    fam_covenant,
]

SUMM_FAMS = [
    simple(ctx_income, "Summarise the FY2025 income statement in two sentences: state revenue, net "
                       "income and the change in gross margin in basis points.",
           lambda f: "FY2025 revenue was %s against %s in FY2024, with net income of %s; gross margin "
                     "moved %.0f basis points to %s percent."
                     % (f1(f["rev25"]), f1(f["rev24"]), f1(f["ni25"]), f["bps_gm"], f2(f["gm25"])),
           "normalized", "text"),
    simple(ctx_balance, "Write one sentence on the balance sheet: state the current ratio in times "
                        "and total debt to equity in times.",
           lambda f: "The balance sheet carries a current ratio of %s times and total debt to equity "
                     "of %s times at the FY2025 year end." % (f2(f["cr25"]), f2(f["de25"])),
           "normalized", "text"),
    simple(ctx_segment, "Summarise the segment mix in one sentence: name the largest and smallest "
                        "segments and give their FY2025 revenue shares in percent.",
           lambda f: "%s is the largest segment at %s percent of revenue while %s is the smallest at "
                     "%s percent." % (seg_max(f)["name"], f1(seg_max(f)["rev"] / f["rev25"] * 100.0),
                                      min(f["segs"], key=lambda s: s["rev"])["name"],
                                      f1(min(s["rev"] for s in f["segs"]) / f["rev25"] * 100.0)),
           "normalized", "text"),
]

DE_T = terciles([FIX[c["key"]]["de25"] for c in COMPANIES])

def fam_leverage(c):
    f = FIX[c["key"]]
    t1, t2 = DE_T
    lab = "low" if f["de25"] <= t1 else ("high" if f["de25"] > t2 else "moderate")
    q = ("Classify the balance sheet with this rule: total debt to equity at or below %s times is "
         "low, above %s times is high, otherwise moderate. Reply with one label from "
         "{low, moderate, high}." % (f2(t1), f2(t2)))
    return (ctx_balance(c), q, lab, "label", "exact")

def fam_beat(c):
    f = FIX[c["key"]]
    gap = (f["rev25"] / f["cons_rev"] - 1.0) * 100.0
    lab = "beat" if gap > 1.0 else ("miss" if gap < -1.0 else "inline")
    q = ("Classify the FY2025 revenue outcome against consensus: beat if revenue exceeds consensus "
         "by more than one percent, miss if it falls short by more than one percent, otherwise "
         "inline. Reply with one label from {beat, inline, miss}.")
    return (ctx_memo(c), q, lab, "label", "exact")

CLS_FAMS = [fam_leverage, fam_beat]

# ------------------------------------------------------------------ assembly
def build_items():
    items = {}
    for task in TASK_ORDER:
        items[task] = []
        for c in COMPANIES:
            if task == "calc":
                got = [f(c) for f in [CALC_FAMS[(c["idx"] + k) % len(CALC_FAMS)] for k in range(6)]]
            elif task == "extraction":
                got = [f(c) for f in [EXTR_FAMS[(c["idx"] + k) % len(EXTR_FAMS)] for k in range(6)]]
            elif task == "qa":
                got = [f(c) for f in [QA_FAMS[(c["idx"] + k) % len(QA_FAMS)] for k in range(8)]]
            elif task == "classification":
                got = [CLS_FAMS[0](c), CLS_FAMS[1](c)]
            elif task == "summarization":
                got = [SUMM_FAMS[(c["idx"] + k) % len(SUMM_FAMS)](c) for k in range(2)]
            else:
                got = [TOOL_FLOWS[(c["idx"] * 16 + k) % len(TOOL_FLOWS)](c) for k in range(16)]
            items[task].append((c, got))
    return items

def make_row(task, item):
    if task == "tool_use":
        return {"task": task, "source": "synthetic:%s" % AREA, "messages": item["msgs"],
                "tools": TOOLS, "ground_truth": item["gt"], "answer_type": item["at"],
                "tolerance": item["tol"], "thinking": THINK[task]}
    ctx, q, gt, at, tol = item
    return {"task": task, "source": "synthetic:%s" % AREA if ctx else "knowledge:finance_general",
            "context": ctx, "question": q, "ground_truth": gt, "answer_type": at,
            "tolerance": tol, "thinking": THINK[task]}

def assign_splits(fixtures):
    total = sum(len(f["rows"]) for f in fixtures)
    targets = {"train": 0.8 * total, "val": 0.1 * total, "test": 0.1 * total}
    got = {"train": 0, "val": 0, "test": 0}
    for fx in sorted(fixtures, key=lambda f: hashlib.sha256(f["key"].encode("utf-8")).hexdigest()):
        best = None
        for s in ("train", "val", "test"):
            deficit = targets[s] - got[s]
            if best is None or deficit > best[0] + 1e-9:
                best = (deficit, s)
        got[best[1]] += len(fx["rows"])
        for row in fx["rows"]:
            row["split"] = best[1]

def build():
    items = build_items()
    final = []
    for task in TASK_ORDER:
        fixtures = []
        for c, got in items[task]:
            rows = [make_row(task, it) for it in got]
            size = {"tool_use": 4, "calc": 3, "extraction": 3, "qa": 4}.get(task, len(rows))
            for bi in range(0, len(rows), size):
                fixtures.append({"key": "%s:%s:%d" % (task, c["key"], bi // size),
                                 "rows": rows[bi:bi + size]})
        assign_splits(fixtures)
        seq = 0
        for fx in fixtures:
            for row in fx["rows"]:
                seq += 1
                row["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[task], seq)
                final.append(row)
    return final

def main():
    rows = build()
    with open(os.path.join(HERE, "prompts.jsonl"), "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    fams = Counter()
    for r in rows:
        src = r["messages"][1]["content"] if r["task"] == "tool_use" else r["question"]
        fams[re.sub(r"\d+(?:[.,]\d+)*", "#", src.lower())[:160]] += 1
    print("rows", len(rows), "| tasks", dict(Counter(r["task"] for r in rows)))
    print("splits", dict(Counter(r["split"] for r in rows)))
    print("answers", dict(Counter(r["answer_type"] for r in rows)))
    print("families", len(fams), "top", fams.most_common(2))
    print("contexts", len(set(r["context"] for r in rows if r.get("context"))))

if __name__ == "__main__":
    main()
