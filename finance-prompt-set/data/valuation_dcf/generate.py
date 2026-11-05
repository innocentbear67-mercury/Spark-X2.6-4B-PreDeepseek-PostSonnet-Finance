#!/usr/bin/env python3
"""Deterministic generator for the valuation_dcf area of the finance prompt set.
Everything is synthetic. Every ground_truth value is recomputed in code from the
same fixture dictionary that is rendered into the row context.
"""
import hashlib
import json
import os
import random
import re
AREA = "valuation_dcf"
SOURCE = "synthetic:valuation_dcf"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RNG = random.Random(42)
TASKS = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
QUOTA = {"calc": 280, "extraction": 220, "qa": 200,
         "classification": 100, "summarization": 100, "tool_use": 100}
THINK = {"calc": "on", "extraction": "off", "qa": "on",
         "classification": "off", "summarization": "off", "tool_use": "on"}
UNITS = "Units: $ in millions except per-share amounts in dollars and percentages in percent."
COMPANIES = [
    ("Kestrel Foods", "Consumer Staples", "30 September"), ("Halcyon Grid Utilities", "Utilities", "31 December"),
    ("Meridian Capital Partners", "Financials", "31 December"), ("Northwind Logistics", "Industrials", "31 March"),
    ("Cobalt Ridge Mining", "Materials", "31 December"), ("Aster Bio Therapeutics", "Health Care", "30 June"),
    ("Tallow and Finch Retail", "Consumer Discretionary", "31 January"), ("Vantage Semiconductor", "Information Technology", "31 December"),
    ("Blue Harbour Shipping", "Industrials", "31 December"), ("Lumen Field Energy", "Energy", "31 December"),
    ("Sable Ridge Properties", "Real Estate", "31 December"), ("Orchard Lane Breweries", "Consumer Staples", "30 September"),
    ("Pinnacle Aero Components", "Industrials", "31 December"), ("Silverbrook Water", "Utilities", "31 March"),
    ("Nimbus Cloud Systems", "Information Technology", "31 January"), ("Redwood Grove Timber", "Materials", "31 December"),
    ("Fairmont Diagnostics", "Health Care", "30 September"), ("Quarry Stone Materials", "Materials", "30 June"),
    ("Beacon Hill Insurance", "Financials", "31 December"), ("Tidewater Marine Services", "Energy", "31 December"),
]
SCENARIOS = [
    ("Base case", {}), ("Upside case", {"growth": 1.5, "margin": 1.0}),
    ("Downside case", {"growth": -2.0, "margin": -1.5}), ("Levered recapitalisation", {"debt": 1.0, "cash_pct": -1.0}),
    ("Deleveraging plan", {"debt": -0.8, "kd": -0.4}), ("Margin expansion", {"margin": 2.0, "growth": -0.5}),
    ("Capex upcycle", {"capex_pct": 2.0, "growth": 0.5}), ("Working capital stress", {"nwc_pct": 6.0, "growth": -1.0}),
    ("Mature steady state", {"growth": -1.5, "capex_pct": -1.0}), ("Platform acquisition", {"growth": 2.0, "debt": 0.6, "min_pct": 1.5}),
]
HORIZONS = [5, 4, 6, 5, 3]
G_LIST = [1.6, 1.9, 2.3, 2.6, 3.1, 3.4]
D_LIST = [0.8, 1.6, 2.4, 3.2, 4.0, 4.8]
MISPRICE = [28.0, -18.0, 5.0, 42.0, -32.0, 11.0, -7.0, 20.0, -24.0, 2.0, 35.0, -30.0]
CONV = {"year_end": "Cash flows and the terminal value are discounted at year end.",
        "mid_year": ("Cash flows arise evenly through the year and are discounted at mid-year; "
                     "the terminal value is discounted at the mid-point of the final forecast year.")}
BASE = []
for _c in COMPANIES:
    BASE.append({
        "rev0": round(RNG.uniform(720.0, 4100.0), 0), "margin": round(RNG.uniform(11.0, 26.0), 1),
        "mstep": RNG.choice([0.0, 0.0, 0.2, 0.3]), "fade": round(RNG.uniform(0.2, 0.6), 1),
        "tax": round(RNG.uniform(21.0, 27.0), 1), "da_pct": round(RNG.uniform(4.0, 8.5), 1),
        "capex_pct": round(RNG.uniform(5.0, 11.0), 1), "nwc_pct": round(RNG.uniform(9.0, 17.0), 1),
        "growth": round(RNG.uniform(2.5, 8.5), 1), "beta": round(RNG.uniform(0.80, 1.45), 2),
        "rf": round(RNG.uniform(3.8, 4.6), 1), "erp": round(RNG.uniform(5.2, 6.4), 1),
        "kd": round(RNG.uniform(4.6, 7.4), 1), "mult": round(RNG.uniform(6.5, 10.5), 1),
        "shares": float(round(RNG.uniform(45.0, 420.0), 0)),
        "cash_pct": round(RNG.uniform(2.5, 8.0), 1), "min_pct": round(RNG.uniform(0.4, 2.0), 1),
        "pref_pct": round(RNG.uniform(0.3, 1.6), 1), "pen_pct": round(RNG.uniform(0.2, 1.2), 1),
        "nb_pct": round(RNG.uniform(1.0, 4.0), 1)})
def fmt(x, d=1):
    s = "%.*f" % (d, round(float(x), d))
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)
def yi(f, d, k=0):
    return (f["idx"] + k) % d["n"]
def ev_at(f, d, w, g):
    n = d["n"]
    mid = f["conv"] == "mid_year"
    pv = 0.0
    for i in range(n):
        p = (i + 1) - 0.5 if mid else (i + 1)
        pv += d["fcff"][i] / ((1.0 + w) ** p)
    tv = d["fcff"][-1] * (1.0 + g) / (w - g)
    pn = n - 0.5 if mid else n
    return round(pv + tv / ((1.0 + w) ** pn), 1)

def derive(f):
    n = len(f["rev"])
    t = f["tax"] / 100.0
    w = f["wacc"] / 100.0
    g = f["g"] / 100.0
    mid = f["conv"] == "mid_year"
    nopat = [round(f["ebit"][i] * (1.0 - t), 1) for i in range(n)]
    fcff = [round(nopat[i] + f["da"][i] - f["capex"][i] - f["dnwc"][i], 1)
            for i in range(n)]
    ebitda = [round(f["ebit"][i] + f["da"][i], 1) for i in range(n)]
    df = [1.0 / ((1.0 + w) ** ((i + 1) - 0.5 if mid else (i + 1))) for i in range(n)]
    pv = [round(fcff[i] * df[i], 1) for i in range(n)]
    pv_sum = round(sum(pv), 1)
    tv = round(fcff[-1] * (1.0 + g) / (w - g), 1)
    pv_tv = round(tv * df[-1], 1)
    ev = round(pv_sum + pv_tv, 1)
    tv_x = round(ebitda[-1] * f["exit_mult"], 1)
    pv_tv_x = round(tv_x * df[-1], 1)
    ev_x = round(pv_sum + pv_tv_x, 1)
    net_debt = round(f["debt"] - f["cash"], 1)
    equity = round(ev - f["debt"] + f["cash"] - f["minorities"]
                   - f["preferred"] - f["pension"], 1)
    ps = round(equity / f["shares"], 2)
    ke = round(f["rf"] + f["beta"] * f["erp"], 1)
    kd_at = round(f["kd"] * (1.0 - t), 1)
    beta_u = f["beta"] / (1.0 + (1.0 - t) * f["de"])
    fcfe = [round(fcff[i] - f["interest"] * (1.0 - t) + f["net_borrow"], 1)
            for i in range(n)]
    ek = ke / 100.0
    pvf = [1.0 / ((1.0 + ek) ** ((i + 1) - 0.5 if mid else (i + 1))) for i in range(n)]
    pv_fcfe = round(sum(fcfe[i] * pvf[i] for i in range(n)), 1)
    tv_f = round(fcfe[-1] * (1.0 + g) / (ek - g), 1)
    eq_fcfe = round(pv_fcfe + tv_f * pvf[-1], 1)
    gw = [round(w * 100.0 + x, 1) for x in (-1.2, -0.6, 0.0, 0.6, 1.2)]
    gg = [round(g * 100.0 + x, 1) for x in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    grid = []
    for wv in gw:
        grid.append([ev_at(f, {"n": n, "fcff": fcff, "pv_sum": pv_sum}, wv / 100.0,
                           gv / 100.0) for gv in gg])
    return {
        "n": n, "years": f["years"], "nopat": nopat, "fcff": fcff, "ebitda": ebitda,
        "df": df, "pv": pv, "pv_sum": pv_sum, "tv": tv, "pv_tv": pv_tv, "ev": ev,
        "tv_x": tv_x, "pv_tv_x": pv_tv_x, "ev_x": ev_x, "net_debt": net_debt,
        "equity": equity, "ps": ps,
        "upside": round((ps / f["price"] - 1.0) * 100.0, 1) if f["price"] else 0.0,
        "ke": ke, "kd_at": kd_at, "beta_u": beta_u, "fcfe": fcfe,
        "eq_fcfe": eq_fcfe, "gw": gw, "gg": gg, "grid": grid,
        "tv_share": round(pv_tv / ev * 100.0, 1),
        "mcap": round(f["shares"] * f["price"], 1),
    }

def make_fixture(ci, si):
    name, sector, fyend = COMPANIES[ci]
    sname, delta = SCENARIOS[si]
    b = BASE[ci]
    idx = ci * len(SCENARIOS) + si
    n = HORIZONS[idx % len(HORIZONS)]
    growth = round(b["growth"] + delta.get("growth", 0.0), 1)
    margin = round(b["margin"] + delta.get("margin", 0.0), 1)
    rev = [b["rev0"]]
    for tt in range(n):
        rev.append(round(rev[-1] * (1.0 + (growth - b["fade"] * tt) / 100.0), 1))
    rev = rev[1:]
    ebit = [round(rev[tt] * (margin + b["mstep"] * tt) / 100.0, 1) for tt in range(n)]
    capex_pct = max(3.0, round(b["capex_pct"] + delta.get("capex_pct", 0.0), 1))
    nwc_pct = max(4.0, round(b["nwc_pct"] + delta.get("nwc_pct", 0.0), 1))
    da = [round(r * b["da_pct"] / 100.0, 1) for r in rev]
    capex = [round(r * capex_pct / 100.0, 1) for r in rev]
    prevs = [b["rev0"]] + rev[:-1]
    dnwc = [round((rev[i] - prevs[i]) * nwc_pct / 100.0, 1) for i in range(n)]
    ebitda1 = round(ebit[0] + da[0], 1)
    dm = D_LIST[(ci + si) % 6] + delta.get("debt", 0.0)
    dm = max(0.4, round(dm, 2))
    cash = round(rev[0] * max(0.5, b["cash_pct"] + delta.get("cash_pct", 0.0)) / 100.0, 1)
    minp = max(0.2, round(b["min_pct"] + delta.get("min_pct", 0.0), 1))
    minorities = round(rev[0] * minp / 100.0, 1)
    preferred = round(rev[0] * b["pref_pct"] / 100.0, 1)
    pension = round(rev[0] * b["pen_pct"] / 100.0, 1)
    kd = round(max(3.5, b["kd"] + delta.get("kd", 0.0)), 1)
    wd = 25.0 + (ci % 4) * 5.0
    we = 100.0 - wd
    beta = b["beta"]
    rf, erp = b["rf"], b["erp"]
    ke = round(rf + beta * erp, 1)
    kd_at = round(kd * (1.0 - b["tax"] / 100.0), 1)
    wacc = round(wd / 100.0 * kd_at + we / 100.0 * ke, 1)
    g = G_LIST[(ci + si) % 6]
    if wacc - g < 4.0:
        g = round(wacc - 4.0, 1)
    f = {
        "key": name + "|" + sname, "idx": idx, "name": name, "sector": sector, "fy_end": fyend,
        "scenario": sname, "years": ["FY%dE" % (2026 + i) for i in range(n)],
        "rev": rev, "ebit": ebit, "da": da, "capex": capex, "dnwc": dnwc, "tax": b["tax"],
        "wacc": wacc, "g": g, "exit_mult": b["mult"], "rf": rf, "erp": erp, "beta": beta,
        "de": round(wd / we, 2), "kd": kd, "wd": wd, "we": we, "debt": 0.0, "cash": cash,
        "minorities": minorities, "preferred": preferred, "pension": pension, "interest": 0.0,
        "net_borrow": 0.0, "shares": b["shares"], "price": 0.0,
        "conv": "mid_year" if idx % 5 in (1, 3) else "year_end",
        "note1": "Capital expenditure excludes capitalised software.",
        "note2": "Minority interest is carried at book value and is treated as a debt-like item in the bridge.",
        "note3": "The pension deficit is stated net of tax and is treated as a debt-like item in the bridge.",
        "rsu": float(900 + (idx * 137) % 2400)}
    probe = derive(f)
    debt = round(min(dm * ebitda1, 0.55 * probe["ev"]), 1)
    f["debt"] = debt
    f["interest"] = round(debt * kd / 100.0, 1)
    f["net_borrow"] = round(debt * b["nb_pct"] / 100.0, 1)
    d0 = derive(f)
    u = MISPRICE[idx % len(MISPRICE)]
    f["price"] = round(d0["ps"] / (1.0 + u / 100.0), 2)
    f["d"] = derive(f)
    if f["d"]["ps"] <= 0.5:
        raise RuntimeError("degenerate fixture %s ps=%s" % (f["key"], f["d"]["ps"]))
    return f
FIXTURES = [make_fixture(ci, si) for ci in range(len(COMPANIES))
            for si in range(len(SCENARIOS))]
CTX_CACHE = {}

def ctx_valuation(f, d):
    rows = [["Revenue"] + [fmt(x) for x in f["rev"]], ["EBIT"] + [fmt(x) for x in f["ebit"]],
            ["Depreciation and amortisation"] + [fmt(x) for x in f["da"]],
            ["Capital expenditure"] + [fmt(x) for x in f["capex"]],
            ["Increase in net working capital"] + [fmt(x) for x in f["dnwc"]]]
    vals = [["Tax rate, percent", fmt(f["tax"])], ["Weighted average cost of capital, percent", fmt(f["wacc"])],
            ["Terminal growth rate, percent", fmt(f["g"])], ["Exit multiple, EV/EBITDA, times", fmt(f["exit_mult"])],
            ["Risk-free rate, percent", fmt(f["rf"])], ["Equity risk premium, percent", fmt(f["erp"])],
            ["Levered beta", fmt(f["beta"], 2)],
            ["Debt-to-equity ratio at which the levered beta is measured", fmt(f["de"], 2)],
            ["Pre-tax cost of debt, percent", fmt(f["kd"])], ["Target debt share of capital, percent", fmt(f["wd"])],
            ["Target equity share of capital, percent", fmt(f["we"])]]
    other = [["Debt, $ millions", fmt(f["debt"])], ["Cash and equivalents, $ millions", fmt(f["cash"])],
             ["Minority interest, $ millions", fmt(f["minorities"])], ["Preferred stock, $ millions", fmt(f["preferred"])],
             ["Pension deficit, $ millions", fmt(f["pension"])], ["Interest expense, $ millions", fmt(f["interest"])],
             ["Net borrowing, $ millions", fmt(f["net_borrow"])], ["Shares outstanding, millions", fmt(f["shares"])],
             ["Share price, dollars", fmt(f["price"], 2)]]
    return "\n".join([
        UNITS, "", "%s (%s). Fiscal year ends %s. Scenario: %s." % (f["name"], f["sector"], f["fy_end"], f["scenario"]),
        "Forecast: %s to %s, %d years. %s" % (f["years"][0], f["years"][-1], d["n"], CONV[f["conv"]]),
        "", "Operating forecast:", table(["Item"] + f["years"], rows),
        "", "Valuation inputs:", table(["Item", "Value"], vals),
        "", "Balance sheet, share data and other items:", table(["Item", "Value"], other),
        "", "Other items stated in thousands:",
        table(["Item", "Amount"], [["Restricted stock units outstanding", fmt(f["rsu"], 0)]]),
        "", "Footnotes:", "1. " + f["note1"], "2. " + f["note2"], "3. " + f["note3"]])

def ctx_capital(f, d):
    vals = [["Risk-free rate, percent", fmt(f["rf"])], ["Equity risk premium, percent", fmt(f["erp"])],
            ["Levered beta", fmt(f["beta"], 2)],
            ["Debt-to-equity ratio at which the levered beta is measured", fmt(f["de"], 2)],
            ["Pre-tax cost of debt, percent", fmt(f["kd"])], ["Marginal tax rate, percent", fmt(f["tax"])],
            ["Target debt share of capital, percent", fmt(f["wd"])], ["Target equity share of capital, percent", fmt(f["we"])]]
    return "\n".join([UNITS, "", "%s (%s). Scenario: %s. Cost of capital inputs." % (f["name"], f["sector"], f["scenario"]),
                       "", table(["Item", "Value"], vals), "",
                       "The capital structure weights are target weights at market values."])

def ctx_grid(f, d):
    head = ["WACC, percent / Terminal growth, percent"] + [fmt(x) for x in d["gg"]]
    body = [[fmt(d["gw"][i])] + [fmt(v) for v in d["grid"][i]] for i in range(len(d["gw"]))]
    vals = [["Debt, $ millions", fmt(f["debt"])], ["Cash and equivalents, $ millions", fmt(f["cash"])],
            ["Minority interest, $ millions", fmt(f["minorities"])], ["Preferred stock, $ millions", fmt(f["preferred"])],
            ["Pension deficit, $ millions", fmt(f["pension"])], ["Shares outstanding, millions", fmt(f["shares"])],
            ["Base weighted average cost of capital, percent", fmt(f["wacc"])],
            ["Base terminal growth rate, percent", fmt(f["g"])]]
    return "\n".join([UNITS, "", "%s (%s). Scenario: %s. Enterprise value sensitivity grid." % (f["name"], f["sector"], f["scenario"]),
                       "", "Enterprise value, $ millions:", table(head, body), "", table(["Item", "Value"], vals)])

def ctx_stub(f, d):
    stub = round(d["fcff"][0] * 0.5, 1)
    vals = [["Valuation date", "1 April 2026"], ["Stub period end", "30 September 2026"],
            ["Stub period length, years", "0.5"], ["Free cash flow for the full FY2026E, $ millions", fmt(d["fcff"][0])],
            ["Stub-period free cash flow, $ millions", fmt(stub)], ["Weighted average cost of capital, percent", fmt(f["wacc"])]]
    return "\n".join([UNITS, "", "%s (%s). Scenario: %s. Stub-period discounting." % (f["name"], f["sector"], f["scenario"]),
                       "", table(["Item", "Value"], vals), "",
                       "The stub-period cash flow is discounted at mid-period, which is 0.25 years from the valuation date."])

def ctx_perp(f, d):
    ntm = round(d["fcff"][0] * (1.0 + f["g"] / 100.0), 1)
    vals = [["Free cash flow to the firm, next twelve months, $ millions", fmt(ntm)],
            ["Terminal growth rate, percent", fmt(f["g"])], ["Market capitalisation, $ millions", fmt(d["mcap"])],
            ["Debt, $ millions", fmt(f["debt"])], ["Cash and equivalents, $ millions", fmt(f["cash"])],
            ["Shares outstanding, millions", fmt(f["shares"])], ["Share price, dollars", fmt(f["price"], 2)]]
    return "\n".join([UNITS, "", "%s (%s). Scenario: %s. Single-stage perpetuity reverse check." % (f["name"], f["sector"], f["scenario"]),
                       "", table(["Item", "Value"], vals), "", "Enterprise value is market capitalisation plus debt less cash."])
CTX_BUILDERS = {"valuation": ctx_valuation, "capital": ctx_capital, "grid": ctx_grid,
                "stub": ctx_stub, "perp": ctx_perp}

def get_ctx(f, kind):
    k = (f["key"], kind)
    if k not in CTX_CACHE:
        CTX_CACHE[k] = CTX_BUILDERS[kind](f, f["d"])
    return CTX_CACHE[k]

def _f(name, task, ctx, fn):
    return {"name": name, "task": task, "ctx": ctx, "fn": fn}

def _rev_growth(f, d, evt):
    w = f["wacc"] / 100.0
    a = (evt - d["pv_sum"]) * ((1.0 + w) ** d["n"])
    fc = d["fcff"][-1]
    return round((a * w - fc) / (a + fc) * 100.0, 2)

def _ev_capex_shift(f, d, shift):
    n, w, g = d["n"], f["wacc"] / 100.0, f["g"] / 100.0
    mid = f["conv"] == "mid_year"
    pv = 0.0
    for i in range(n):
        cf = d["fcff"][i] + f["rev"][i] * shift
        p = (i + 1) - 0.5 if mid else (i + 1)
        pv += cf / ((1.0 + w) ** p)
    cfl = d["fcff"][-1] + f["rev"][-1] * shift
    tv = cfl * (1.0 + g) / (w - g)
    pn = n - 0.5 if mid else n
    return round(pv + tv / ((1.0 + w) ** pn), 1)
CALC_F = [
    _f("fcff_year", "calc", "valuation", lambda f, d: ("What is free cash flow to the firm in %s, in $ millions?" % d["years"][yi(f, d)], d["fcff"][yi(f, d)], "number", "rel:0.005")),
    _f("fcff_total", "calc", "valuation", lambda f, d: ("What is total free cash flow to the firm over the forecast period, in $ millions?", round(sum(d["fcff"]), 1), "number", "rel:0.005")),
    _f("nopat_year", "calc", "valuation", lambda f, d: ("What is net operating profit after tax in %s, in $ millions?" % d["years"][yi(f, d)], d["nopat"][yi(f, d)], "number", "rel:0.005")),
    _f("pv_year", "calc", "valuation", lambda f, d: ("What is the present value of the %s free cash flow, in $ millions?" % d["years"][yi(f, d)], d["pv"][yi(f, d)], "number", "rel:0.005")),
    _f("pv_explicit", "calc", "valuation", lambda f, d: ("What is the present value of the explicit forecast free cash flows, in $ millions?", d["pv_sum"], "number", "rel:0.005")),
    _f("tv_gordon", "calc", "valuation", lambda f, d: ("What is the terminal value at the end of %s under the Gordon growth method, in $ millions?" % d["years"][-1], d["tv"], "number", "rel:0.005")),
    _f("pv_tv_gordon", "calc", "valuation", lambda f, d: ("What is the present value of the Gordon growth terminal value, in $ millions?", d["pv_tv"], "number", "rel:0.005")),
    _f("ev_gordon", "calc", "valuation", lambda f, d: ("What is the enterprise value under the Gordon growth method, in $ millions?", d["ev"], "number", "rel:0.005")),
    _f("tv_exit", "calc", "valuation", lambda f, d: ("What is the terminal value under the exit multiple method, in $ millions?", d["tv_x"], "number", "rel:0.005")),
    _f("pv_tv_exit", "calc", "valuation", lambda f, d: ("What is the present value of the exit multiple terminal value, in $ millions?", d["pv_tv_x"], "number", "rel:0.005")),
    _f("ev_exit", "calc", "valuation", lambda f, d: ("What is the enterprise value under the exit multiple method, in $ millions?", d["ev_x"], "number", "rel:0.005")),
    _f("ev_gap", "calc", "valuation", lambda f, d: ("By what percentage does the exit multiple enterprise value differ from the Gordon growth enterprise value, in percent?", round((d["ev_x"] - d["ev"]) / d["ev"] * 100.0, 1), "number", "abs:0.1")),
    _f("implied_mult", "calc", "valuation", lambda f, d: ("What exit multiple is implied by the Gordon growth terminal value, in times?", round(d["tv"] / d["ebitda"][-1], 2), "number", "abs:0.1")),
    _f("implied_g_mult", "calc", "valuation", lambda f, d: ("What terminal growth rate is implied if the exit multiple terminal value is read as a growing perpetuity on the final year free cash flow, in percent?", round((d["tv_x"] * f["wacc"] / 100.0 - d["fcff"][-1]) / (d["tv_x"] + d["fcff"][-1]) * 100.0, 2), "number", "abs:0.1")),
    _f("tv_share", "calc", "valuation", lambda f, d: ("What percentage of the Gordon growth enterprise value comes from the terminal value?", d["tv_share"], "number", "abs:0.1")),
    _f("equity_value", "calc", "valuation", lambda f, d: ("What is the equity value from the Gordon growth enterprise value, in $ millions?", d["equity"], "number", "rel:0.005")),
    _f("per_share", "calc", "valuation", lambda f, d: ("What is the intrinsic value per share, in dollars?", d["ps"], "number", "abs:0.1")),
    _f("upside", "calc", "valuation", lambda f, d: ("What is the implied upside or downside to the stated share price, in percent?", d["upside"], "number", "abs:1")),
    _f("market_cap", "calc", "valuation", lambda f, d: ("What is the market capitalisation at the stated share price, in $ millions?", d["mcap"], "number", "rel:0.005")),
    _f("net_debt", "calc", "valuation", lambda f, d: ("What is net debt, in $ millions?", d["net_debt"], "number", "rel:0.005")),
    _f("ev_ebitda", "calc", "valuation", lambda f, d: ("What is the Gordon growth enterprise value as a multiple of first year EBITDA, in times?", round(d["ev"] / d["ebitda"][0], 1), "number", "abs:0.1")),
    _f("reinvest_rate", "calc", "valuation", lambda f, d: ("What is the reinvestment rate in %s, in percent?" % d["years"][yi(f, d)], round((f["capex"][yi(f, d)] - f["da"][yi(f, d)] + f["dnwc"][yi(f, d)]) / d["nopat"][yi(f, d)] * 100.0, 1), "number", "abs:0.1")),
    _f("fcff_margin", "calc", "valuation", lambda f, d: ("What is free cash flow to the firm as a percentage of revenue in %s?" % d["years"][yi(f, d)], round(d["fcff"][yi(f, d)] / f["rev"][yi(f, d)] * 100.0, 1), "number", "abs:0.1")),
    _f("fcff_to_ebitda", "calc", "valuation", lambda f, d: ("What is free cash flow to the firm as a percentage of EBITDA in %s?" % d["years"][yi(f, d)], round(d["fcff"][yi(f, d)] / d["ebitda"][yi(f, d)] * 100.0, 1), "number", "abs:0.1")),
    _f("pv_window", "calc", "valuation", lambda f, d: ("What is the present value of the free cash flows from %s to %s, in $ millions?" % (d["years"][f["idx"] % (d["n"] - 1)], d["years"][f["idx"] % (d["n"] - 1) + 1]), round(d["pv"][f["idx"] % (d["n"] - 1)] + d["pv"][f["idx"] % (d["n"] - 1) + 1], 1), "number", "abs:1")),
    _f("rev_cagr", "calc", "valuation", lambda f, d: ("What is the compound annual growth rate of revenue from %s to %s, in percent?" % (d["years"][0], d["years"][-1]), round(((f["rev"][-1] / f["rev"][0]) ** (1.0 / (d["n"] - 1)) - 1.0) * 100.0, 1), "number", "abs:0.1")),
    _f("wacc_build", "calc", "capital", lambda f, d: ("What is the weighted average cost of capital, in percent?", f["wacc"], "number", "abs:0.1")),
    _f("cost_of_equity", "calc", "capital", lambda f, d: ("What is the cost of equity, in percent?", d["ke"], "number", "abs:0.1")),
    _f("after_tax_kd", "calc", "capital", lambda f, d: ("What is the after-tax cost of debt, in percent?", d["kd_at"], "number", "abs:0.1")),
    _f("unlever_beta", "calc", "capital", lambda f, d: ("What is the unlevered beta?", round(d["beta_u"], 2), "number", "abs:0.01")),
    _f("relever_beta", "calc", "capital", lambda f, d: ("What is the re-levered beta at a debt-to-equity ratio of %s?" % fmt([0.6, 1.0, 1.5, 2.0][f["idx"] % 4], 1), round(d["beta_u"] * (1.0 + (1.0 - f["tax"] / 100.0) * [0.6, 1.0, 1.5, 2.0][f["idx"] % 4]), 2), "number", "abs:0.01")),
    _f("wacc_new_structure", "calc", "capital", lambda f, d: ("What would the weighted average cost of capital be if the debt share of capital were %s percent, with the beta re-levered accordingly and the pre-tax cost of debt unchanged, in percent?" % fmt([45, 55, 35, 50][f["idx"] % 4], 0), round([45, 55, 35, 50][f["idx"] % 4] / 100.0 * d["kd_at"] + (1.0 - [45, 55, 35, 50][f["idx"] % 4] / 100.0) * (f["rf"] + round(d["beta_u"] * (1.0 + (1.0 - f["tax"] / 100.0) * ([45, 55, 35, 50][f["idx"] % 4] / (100.0 - [45, 55, 35, 50][f["idx"] % 4]))), 2) * f["erp"]), 1), "number", "abs:0.2")),
    _f("stub_pv", "calc", "stub", lambda f, d: ("What is the present value of the stub-period free cash flow, in $ millions?", round(d["fcff"][0] * 0.5 / ((1.0 + f["wacc"] / 100.0) ** 0.25), 1), "number", "abs:0.5")),
    _f("stub_df", "calc", "stub", lambda f, d: ("What discount factor applies to the stub-period cash flow?", round(1.0 / ((1.0 + f["wacc"] / 100.0) ** 0.25), 4), "number", "abs:0.01")),
    _f("grid_ev", "calc", "grid", lambda f, d: ("What is the enterprise value at a discount rate of %s percent and a terminal growth rate of %s percent, in $ millions?" % (fmt(d["gw"][(f["idx"] // 2) % 5]), fmt(d["gg"][(f["idx"] // 3) % 5])), d["grid"][(f["idx"] // 2) % 5][(f["idx"] // 3) % 5], "number", "rel:0.005")),
    _f("grid_ps", "calc", "grid", lambda f, d: ("What is the intrinsic value per share at a discount rate of %s percent and the base terminal growth rate, in dollars?" % fmt(d["gw"][(f["idx"] // 2) % 5]), round((d["grid"][(f["idx"] // 2) % 5][2] - f["debt"] + f["cash"] - f["minorities"] - f["preferred"] - f["pension"]) / f["shares"], 2), "number", "abs:0.1")),
    _f("grid_delta", "calc", "grid", lambda f, d: ("By how much does enterprise value change if the discount rate moves from %s to %s percent while terminal growth stays at %s percent, in $ millions?" % (fmt(d["gw"][0]), fmt(d["gw"][1]), fmt(d["gg"][2])), round(d["grid"][1][2] - d["grid"][0][2], 1), "number", "abs:10")),
    _f("reverse_growth", "calc", "valuation", lambda f, d: ("If the enterprise value were %s, what terminal growth rate would the Gordon growth method imply, holding the explicit forecast and the discount rate unchanged, in percent?" % fmt(round(d["ev"] * [1.18, 0.86, 1.10, 0.92][f["idx"] % 4], 1)), _rev_growth(f, d, round(d["ev"] * [1.18, 0.86, 1.10, 0.92][f["idx"] % 4], 1)), "number", "abs:0.1")),
    _f("implied_wacc", "calc", "perp", lambda f, d: ("At the stated share price, what discount rate does a single-stage growing perpetuity imply, in percent?", round(round(d["fcff"][0] * (1.0 + f["g"] / 100.0), 1) / (d["mcap"] + f["debt"] - f["cash"]) * 100.0 + f["g"], 2), "number", "abs:0.1")),
    _f("price_for_upside", "calc", "valuation", lambda f, d: ("What share price would give a 15 percent upside to the intrinsic value, in dollars?", round(d["ps"] / 1.15, 2), "number", "abs:0.1")),
    _f("fcfe_year", "calc", "valuation", lambda f, d: ("What is free cash flow to equity in %s, in $ millions?" % d["years"][yi(f, d)], d["fcfe"][yi(f, d)], "number", "abs:1")),
    _f("equity_fcfe", "calc", "valuation", lambda f, d: ("Using the free cash flow to equity method, what is the equity value, in $ millions?", d["eq_fcfe"], "number", "rel:0.01")),
]
EXTR_F = [
    _f("x_capex", "extraction", "valuation", lambda f, d: ("What capital expenditure is reported for %s, in $ millions?" % d["years"][yi(f, d)], f["capex"][yi(f, d)], "number", "abs:0.01")),
    _f("x_ebit", "extraction", "valuation", lambda f, d: ("What EBIT is reported for %s, in $ millions?" % d["years"][yi(f, d)], f["ebit"][yi(f, d)], "number", "abs:0.01")),
    _f("x_da", "extraction", "valuation", lambda f, d: ("What depreciation and amortisation is reported for %s, in $ millions?" % d["years"][yi(f, d)], f["da"][yi(f, d)], "number", "abs:0.01")),
    _f("x_rev", "extraction", "valuation", lambda f, d: ("What revenue is reported for %s, in $ millions?" % d["years"][yi(f, d)], f["rev"][yi(f, d)], "number", "abs:0.01")),
    _f("x_dnwc", "extraction", "valuation", lambda f, d: ("What increase in net working capital is reported for %s, in $ millions?" % d["years"][yi(f, d)], f["dnwc"][yi(f, d)], "number", "abs:0.01")),
    _f("x_wacc", "extraction", "valuation", lambda f, d: ("What weighted average cost of capital is stated, in percent?", f["wacc"], "number", "abs:0.01")),
    _f("x_g", "extraction", "valuation", lambda f, d: ("What terminal growth rate is stated, in percent?", f["g"], "number", "abs:0.01")),
    _f("x_mult", "extraction", "valuation", lambda f, d: ("What exit multiple is stated, in times?", f["exit_mult"], "number", "abs:0.01")),
    _f("x_shares", "extraction", "valuation", lambda f, d: ("How many shares are outstanding, in millions?", f["shares"], "number", "abs:0.01")),
    _f("x_price", "extraction", "valuation", lambda f, d: ("What share price is stated, in dollars?", f["price"], "number", "abs:0.01")),
    _f("x_debt", "extraction", "valuation", lambda f, d: ("What debt is stated, in $ millions?", f["debt"], "number", "abs:0.01")),
    _f("x_cash", "extraction", "valuation", lambda f, d: ("What cash and equivalents are stated, in $ millions?", f["cash"], "number", "abs:0.01")),
    _f("x_min", "extraction", "valuation", lambda f, d: ("What minority interest is stated, in $ millions?", f["minorities"], "number", "abs:0.01")),
    _f("x_pref", "extraction", "valuation", lambda f, d: ("What preferred stock is stated, in $ millions?", f["preferred"], "number", "abs:0.01")),
    _f("x_pen", "extraction", "valuation", lambda f, d: ("What pension deficit is stated, in $ millions?", f["pension"], "number", "abs:0.01")),
    _f("x_int", "extraction", "valuation", lambda f, d: ("What interest expense is stated, in $ millions?", f["interest"], "number", "abs:0.01")),
    _f("x_rf", "extraction", "valuation", lambda f, d: ("What risk-free rate is stated, in percent?", f["rf"], "number", "abs:0.01")),
    _f("x_erp", "extraction", "valuation", lambda f, d: ("What equity risk premium is stated, in percent?", f["erp"], "number", "abs:0.01")),
    _f("x_beta", "extraction", "valuation", lambda f, d: ("What levered beta is stated?", f["beta"], "number", "abs:0.01")),
    _f("x_kd", "extraction", "valuation", lambda f, d: ("What pre-tax cost of debt is stated, in percent?", f["kd"], "number", "abs:0.01")),
    _f("x_tax", "extraction", "valuation", lambda f, d: ("What tax rate is stated, in percent?", f["tax"], "number", "abs:0.01")),
    _f("x_fyend", "extraction", "valuation", lambda f, d: ("On what date does the fiscal year end?", f["fy_end"], "text", "normalized")),
    _f("x_sector", "extraction", "valuation", lambda f, d: ("Which sector is the company assigned to?", f["sector"], "text", "normalized")),
    _f("x_scenario", "extraction", "valuation", lambda f, d: ("Which scenario is presented in the file?", f["scenario"], "text", "normalized")),
    _f("x_lastyear", "extraction", "valuation", lambda f, d: ("What is the label of the final forecast year in the table?", f["years"][-1], "text", "normalized")),
    _f("x_nyears", "extraction", "valuation", lambda f, d: ("How many forecast years does the table cover?", d["n"], "number", "abs:0.01")),
    _f("x_note", "extraction", "valuation", lambda f, d: ("What does footnote 1 state about capital expenditure?", f["note1"], "text", "normalized")),
    _f("x_rsu", "extraction", "valuation", lambda f, d: ("How many restricted stock units are outstanding, in thousands?", f["rsu"], "number", "abs:0.01")),
]

def _implied_g_price(f, d):
    w = f["wacc"] / 100.0
    evt = d["mcap"] + f["debt"] - f["cash"]
    a = (evt - d["pv_sum"]) * ((1.0 + w) ** d["n"])
    fc = d["fcff"][-1]
    return round((a * w - fc) / (a + fc) * 100.0, 2)

def _ok_price_g(f):
    d = f["d"]
    return d["mcap"] + f["debt"] - f["cash"] > d["pv_sum"] * 1.15

def _qa_tv_low(f, d):
    w = f["wacc"] / 100.0
    g = (f["g"] - 0.5) / 100.0
    return round(d["fcff"][-1] * (1.0 + g) / (w - g), 1)

def _qa_ev_wacc(f, d):
    return ev_at(f, d, (f["wacc"] + 1.0) / 100.0, f["g"] / 100.0)

def _rank3(f, d):
    items = [("debt", f["debt"]), ("minority interest", f["minorities"]),
             ("preferred stock", f["preferred"]), ("pension deficit", f["pension"])]
    items.sort(key=lambda p: (-p[1], p[0]))
    return [p[0] for p in items[:3]]
QA_F = [
    _f("q_tv_low", "qa", "valuation", lambda f, d: ("If the terminal growth rate were 0.5 percentage points lower, what would the Gordon growth terminal value be, in $ millions?", _qa_tv_low(f, d), "number", "rel:0.005")),
    _f("q_ev_high_wacc", "qa", "valuation", lambda f, d: ("If the discount rate were 100 basis points higher, what would the enterprise value be, in $ millions?", _qa_ev_wacc(f, d), "number", "abs:10")),
    _f("q_explicit_share", "qa", "valuation", lambda f, d: ("What share of the Gordon growth enterprise value comes from the explicit forecast period, in percent?", round(100.0 - d["tv_share"], 1), "number", "abs:0.1")),
    _f("q_ps_no_pension", "qa", "valuation", lambda f, d: ("What would the intrinsic value per share be if the pension deficit were excluded from the bridge, in dollars?", round((d["equity"] + f["pension"]) / f["shares"], 2), "number", "abs:0.1")),
    _f("q_ps_min_eq", "qa", "valuation", lambda f, d: ("What would the intrinsic value per share be if minority interest were treated as equity rather than as a debt-like item, in dollars?", round((d["equity"] + f["minorities"]) / f["shares"], 2), "number", "abs:0.1")),
    _f("q_ev_market", "qa", "valuation", lambda f, d: ("What enterprise value does the market imply at the stated share price, in $ millions?", round(d["mcap"] + f["debt"] - f["cash"], 1), "number", "abs:1")),
    _f("q_implied_g_price", "qa", "valuation", lambda f, d: ("At the stated share price, what terminal growth rate does the Gordon growth model imply, in percent?", _implied_g_price(f, d), "number", "abs:0.1")),
    _f("q_count_above", "qa", "valuation", lambda f, d: ("How many forecast years have free cash flow to the firm above the first forecast year?", sum(1 for x in d["fcff"][1:] if x > d["fcff"][0]), "number", "abs:0.01")),
    _f("q_avg_fcff", "qa", "valuation", lambda f, d: ("What is the average free cash flow to the firm over the forecast period, in $ millions?", round(sum(d["fcff"]) / d["n"], 1), "number", "rel:0.005")),
    _f("q_ev_capex", "qa", "valuation", lambda f, d: ("If capital expenditure were 100 basis points of revenue lower in every forecast year, what would the enterprise value be, in $ millions?", _ev_capex_shift(f, d, -0.01), "number", "abs:10")),
    _f("q_ev_both", "qa", "valuation", lambda f, d: ("What is the net change in enterprise value if the discount rate rises by 100 basis points and the terminal growth rate rises by 50 basis points, in $ millions?", round(ev_at(f, d, (f["wacc"] + 1.0) / 100.0, (f["g"] + 0.5) / 100.0) - d["ev"], 1), "number", "abs:10")),
    _f("q_rank3", "qa", "valuation", lambda f, d: ("Rank the three largest debt-like claims deducted in the equity bridge, largest first.", _rank3(f, d), "list", "ordered")),
    _f("q_tv_one_turn", "qa", "valuation", lambda f, d: ("What would the enterprise value be if the exit multiple were one turn higher, in $ millions?", round(d["pv_sum"] + (d["ebitda"][-1] * (f["exit_mult"] + 1.0)) * d["df"][-1], 1), "number", "rel:0.005")),
    _f("q_tv_gap", "qa", "valuation", lambda f, d: ("What is the difference between the Gordon growth terminal value and the exit multiple terminal value, in $ millions?", round(d["tv"] - d["tv_x"], 1), "number", "abs:10")),
]
QA_F[6]["needs"] = _ok_price_g
KNOW = [
    ("Define free cash flow to the firm and give its formula starting from EBIT.", "Free cash flow to the firm is the cash flow available to all capital providers after operating expenses, taxes and reinvestment. Starting from EBIT it is EBIT multiplied by one minus the tax rate, plus depreciation and amortisation, less capital expenditure, less the increase in net working capital."),
    ("Explain why interest expense is excluded from free cash flow to the firm.", "Free cash flow to the firm is measured before any distribution to debt or equity holders, so financing costs are excluded. The tax benefit of debt is captured through the discount rate, which is the weighted average cost of capital."),
    ("Give the formula for free cash flow to equity starting from net income.", "Net income plus depreciation and amortisation, less capital expenditure, less the increase in net working capital, plus net borrowing."),
    ("Contrast free cash flow to the firm with free cash flow to equity.", "Free cash flow to the firm is the cash available to all capital providers and is discounted at the weighted average cost of capital to give enterprise value. Free cash flow to equity is the cash available to shareholders after debt service and net borrowing, and is discounted at the cost of equity to give equity value directly."),
    ("State the condition under which free cash flow to the firm equals free cash flow to equity.", "They are equal when the company has no debt and no net borrowing, so there is no interest expense and no financing cash flow."),
    ("State the capital asset pricing model formula for the cost of equity.", "The cost of equity equals the risk-free rate plus beta multiplied by the equity risk premium."),
    ("Explain how the after-tax cost of debt is computed.", "Multiply the pre-tax cost of debt by one minus the marginal tax rate, because interest expense is tax deductible."),
    ("State the weighted average cost of capital formula.", "The weighted average cost of capital equals the debt share of capital multiplied by the after-tax cost of debt, plus the equity share of capital multiplied by the cost of equity."),
    ("Define unlevered beta and explain its relationship to levered beta.", "Unlevered beta measures business risk with no debt in the capital structure. Levered beta equals unlevered beta multiplied by one plus one minus the tax rate, all multiplied by the debt-to-equity ratio."),
    ("State the Hamada relationship for relevering beta.", "Levered beta equals unlevered beta multiplied by the quantity one plus one minus the tax rate times the debt-to-equity ratio."),
    ("Give the Gordon growth formula for terminal value.", "Terminal value equals the free cash flow in the first year after the forecast period divided by the discount rate minus the terminal growth rate."),
    ("Describe the exit multiple method for terminal value.", "Apply a chosen multiple, usually enterprise value to EBITDA, to the final forecast year metric, which gives the terminal value at the end of the forecast period."),
    ("Explain why the terminal growth rate must be below the discount rate.", "The Gordon growth formula divides by the discount rate minus the terminal growth rate. If growth equals or exceeds the discount rate the denominator becomes zero or negative and the value is unbounded or meaningless."),
    ("Define the mid-year convention and explain when it is used.", "Cash flows are assumed to arrive evenly through the year rather than at year end, so each year is discounted at t minus 0.5 years. It is used when cash flows are generated steadily rather than in a lump at the period end."),
    ("Define a stub period in a valuation.", "A stub period is a partial forecast period between the valuation date and the first full fiscal year end. Its cash flow is discounted for the fraction of the year that it covers."),
    ("Describe how to bridge from enterprise value to equity value.", "Subtract debt, minority interest, preferred stock and any pension deficit, and add cash and equivalents. The result is equity value."),
    ("Explain the treatment of minority interest in the equity bridge.", "Minority interest represents the share of subsidiaries not owned by the parent. Because consolidated enterprise value includes one hundred percent of those subsidiaries, minority interest is deducted as a debt-like claim."),
    ("Explain the treatment of a pension deficit in the equity bridge.", "An unfunded pension obligation is a claim ahead of equity, so it is deducted from enterprise value alongside debt when arriving at equity value."),
    ("State which discount rate applies to free cash flow to equity.", "The cost of equity, because the cash flow belongs to shareholders and carries equity risk."),
    ("Distinguish enterprise value from equity value.", "Enterprise value is the value of the operating business to all capital providers. Equity value is the residual claim of shareholders after debt and other senior claims are removed."),
    ("Define net debt.", "Total debt, including borrowings and debt-like obligations, less cash and cash equivalents."),
    ("Define the reinvestment rate in a discounted cash flow model.", "Capital expenditure less depreciation and amortisation, plus the increase in net working capital, divided by net operating profit after tax."),
    ("Explain the link between growth, return on invested capital and free cash flow.", "Growth creates value only when the return on new invested capital exceeds the cost of capital. Higher reinvestment lowers free cash flow today but raises it later; the net effect depends on the spread between return on invested capital and the cost of capital."),
    ("Describe the purpose of a sensitivity grid in a valuation.", "It shows how the valuation output changes across a range of two inputs, usually the discount rate and the terminal growth rate, so the reader can see how concentrated the conclusion is on a single pair of assumptions."),
    ("Define a reverse discounted cash flow analysis.", "Instead of deriving value from assumptions, a reverse discounted cash flow starts from the observed price or enterprise value and solves for the growth rate or discount rate that the market is implicitly assuming."),
    ("Explain how to solve for implied terminal growth given an enterprise value and a discount rate.", "Back out the terminal value required to reconcile the explicit forecast present value with the target enterprise value, then solve the growing perpetuity formula for growth: growth equals the discount rate minus the first post-forecast cash flow divided by that required terminal value."),
    ("Explain what the terminal value share of enterprise value measures and why it matters.", "It is the present value of the terminal value divided by enterprise value. A high share means the conclusion depends mostly on assumptions beyond the explicit forecast, which weakens the reliability of the valuation."),
    ("Explain why a terminal value is required in a discounted cash flow.", "A company is normally assumed to continue beyond the explicit forecast, so the value of all cash flows after the forecast period must be captured in a terminal value."),
    ("Distinguish a trading multiple from a transaction multiple.", "A trading multiple is derived from observable prices of comparable listed companies. A transaction multiple is derived from prices paid in change-of-control deals and usually includes a control premium."),
    ("Explain how operating leases are typically treated in a discounted cash flow.", "Under a lease-capitalisation approach the lease liability is treated as debt and the lease cost is split into interest and depreciation, so enterprise value is measured before lease financing. Treating leases as operating expenses instead keeps the liability out of net debt but depresses EBITDA relative to capitalised peers."),
    ("Explain how share-based compensation affects free cash flow.", "Share-based compensation is a non-cash expense. If it is added back to net income it must be treated consistently, either as a cash cost or as dilution, otherwise free cash flow is overstated."),
    ("Distinguish capital expenditure from depreciation in a discounted cash flow.", "Depreciation allocates past capital spending over the asset life and is non-cash. Capital expenditure is the actual cash outflow and drives future capacity, so both enter the free cash flow calculation with opposite signs."),
    ("Explain why an increase in net working capital is subtracted from net operating profit after tax.", "Growth in receivables and inventory absorbs cash that is not yet collected from customers, so the investment reduces the cash available to capital providers in that period."),
    ("Define net operating profit after tax.", "Earnings before interest and taxes multiplied by one minus the tax rate, which measures operating profit after tax but before financing effects."),
    ("Explain how to compute equity value per share from a discounted cash flow.", "Take the enterprise value, subtract debt and other senior claims, add cash to get equity value, then divide by the diluted share count."),
    ("Define margin of safety in a valuation context.", "The discount between the estimated intrinsic value and the market price, expressed as a percentage of intrinsic value, which provides a buffer against estimation error."),
    ("Explain what a negative free cash flow to the firm in a forecast year implies.", "Reinvestment, in the form of capital expenditure and working capital, exceeds after-tax operating profit, so the business consumes capital in that year. This is normal for a fast-growing company if later cash flows compensate."),
    ("Explain how a discounted cash flow should handle a company with no terminal growth.", "Set the terminal growth rate to zero, so the terminal value equals the final year free cash flow divided by the discount rate. The terminal value then represents a level perpetuity."),
    ("Distinguish a target capital structure from the observed capital structure in a valuation.", "A target capital structure is the mix of debt and equity the company intends to maintain, and it is used for the discount rate so that the weights are not distorted by temporary market moves. The observed structure reflects the balance sheet at the measurement date."),
    ("Explain why a terminal value based on an exit multiple can differ from a Gordon growth terminal value.", "The exit multiple reflects what comparable businesses trade for at a point in time, while the Gordon growth value reflects a long-run growth and discount rate assumption. Differences signal inconsistent assumptions about mature growth or profitability."),
]
SUMM_F = [
    _f("s_stance", "summarization", "valuation",
       lambda f, d: ("Write a two-sentence valuation summary that states the intrinsic value per share and the implied upside or downside to the stated price.",
                     "%s screens as %s on the discounted cash flow: the model yields %s dollars per share against a stated price of %s dollars, an implied %s of %s percent. The conclusion rests on a %s percent discount rate and a %s percent terminal growth rate." % (f["name"], "undervalued" if d["upside"] >= 15 else ("overvalued" if d["upside"] <= -15 else "fairly valued"), fmt(d["ps"], 2), fmt(f["price"], 2), "upside" if d["upside"] >= 0 else "downside", fmt(abs(d["upside"])), fmt(f["wacc"]), fmt(f["g"])),
                     "text", "normalized")),
    _f("s_tv", "summarization", "valuation",
       lambda f, d: ("Summarise in three bullet points the assumptions that drive the terminal value.",
                     "- Terminal growth of %s percent against a discount rate of %s percent.\n- Final year free cash flow of %s million dollars, grown at the terminal rate.\n- Terminal value of %s million dollars, equal to %s percent of enterprise value." % (fmt(f["g"]), fmt(f["wacc"]), fmt(d["fcff"][-1]), fmt(d["tv"]), fmt(d["tv_share"])),
                     "text", "normalized")),
    _f("s_bridge", "summarization", "valuation",
       lambda f, d: ("Summarise the bridge from enterprise value to equity value in one sentence.",
                     "Enterprise value of %s million dollars, less debt of %s million dollars, plus cash of %s million dollars, less minority interest of %s million dollars, preferred stock of %s million dollars and a pension deficit of %s million dollars, gives equity value of %s million dollars, or %s dollars per share." % (fmt(d["ev"]), fmt(f["debt"]), fmt(f["cash"]), fmt(f["minorities"]), fmt(f["preferred"]), fmt(f["pension"]), fmt(d["equity"]), fmt(d["ps"], 2)),
                     "text", "normalized")),
    _f("s_methods", "summarization", "valuation",
       lambda f, d: ("Summarise in two sentences how the Gordon growth and exit multiple terminal values compare.",
                     "The Gordon growth method values the terminal period at %s million dollars and the exit multiple method at %s million dollars, so the exit multiple enterprise value is %s percent %s than the Gordon growth enterprise value. The Gordon growth terminal value implies an exit multiple of %s times final year EBITDA." % (fmt(d["tv"]), fmt(d["tv_x"]), fmt(abs(round((d["ev_x"] - d["ev"]) / d["ev"] * 100.0, 1))), "higher" if d["ev_x"] >= d["ev"] else "lower", fmt(round(d["tv"] / d["ebitda"][-1], 1))),
                     "text", "normalized")),
    _f("s_ic", "summarization", "valuation",
       lambda f, d: ("Write a short investment committee note on whether the shares screen cheap or expensive.",
                     "Investment committee note. The discounted cash flow yields %s dollars per share against a market price of %s dollars, so the shares screen %s with an implied %s of %s percent. The valuation is sensitive to the %s percent discount rate, and the terminal value carries %s percent of enterprise value, so the committee should focus on the durability of the final year free cash flow of %s million dollars." % (fmt(d["ps"], 2), fmt(f["price"], 2), "cheap" if d["upside"] >= 15 else ("expensive" if d["upside"] <= -15 else "fairly priced"), "upside" if d["upside"] >= 0 else "downside", fmt(abs(d["upside"])), fmt(f["wacc"]), fmt(d["tv_share"]), fmt(d["fcff"][-1])),
                     "text", "normalized")),
]

def _bucket(f, d, kind):
    if kind == "stance":
        u = d["upside"]
        return "undervalued" if u >= 15 else ("overvalued" if u <= -15 else "fairly valued")
    if kind == "rec":
        u = d["upside"]
        return "buy" if u >= 20 else ("sell" if u <= -20 else "hold")
    if kind == "credit":
        r = d["net_debt"] / d["ebitda"][0]
        return "investment grade" if r < 2.0 else ("crossover" if r < 3.5 else "high yield")
    return "conservative" if f["g"] < 2.0 else ("aggressive" if f["g"] > 3.0 else "market")
CLS_F = [
    {"name": "c_stance", "task": "classification", "ctx": "valuation", "kind": "stance",
     "labels": ["undervalued", "fairly valued", "overvalued"],
     "q": ("Classify the shares on the discounted cash flow: label them undervalued if the implied upside to the "
           "stated price is at least 15 percent, overvalued if it is at or below minus 15 percent, and fairly "
           "valued otherwise. Answer with one label from {undervalued, fairly valued, overvalued}.")},
    {"name": "c_rec", "task": "classification", "ctx": "valuation", "kind": "rec",
     "labels": ["buy", "hold", "sell"],
     "q": ("Classify the shares as buy if the implied upside to the stated price is at least 20 percent, sell if "
           "it is at or below minus 20 percent, and hold otherwise. Answer with one label from {buy, hold, sell}.")},
    {"name": "c_credit", "task": "classification", "ctx": "valuation", "kind": "credit",
     "labels": ["investment grade", "crossover", "high yield"],
     "q": ("Compute net debt to first year EBITDA and classify the balance sheet: investment grade if the ratio "
           "is below 2.0 times, crossover if it is between 2.0 and 3.5 times, and high yield if it is 3.5 times "
           "or above. Answer with one label from {investment grade, crossover, high yield}.")},
    {"name": "c_growth", "task": "classification", "ctx": "valuation", "kind": "growth",
     "labels": ["conservative", "market", "aggressive"],
     "q": ("The long-run nominal growth assumption for the sector is 2.5 percent. Classify the terminal growth "
           "rate used in the model as conservative if it is below 2.0 percent, market if it is between 2.0 and "
           "3.0 percent, and aggressive if it is above 3.0 percent. Answer with one label from {conservative, "
           "market, aggressive}.")},
]
SCEN = {"company": {"type": "string", "description": "Registered company name."},
        "scenario": {"type": "string", "description": "Scenario label."}}
ONLY = {"company": {"type": "string", "description": "Registered company name."}}

def _tool(name, desc, props):
    return {"name": name, "description": desc, "parameters":
            {"type": "object", "properties": props, "required": ["company", "scenario"]}}
TOOL_FORECAST = _tool("get_forecast", "Return the operating forecast and valuation inputs for a registered company and scenario.", SCEN)
TOOL_CAPITAL = _tool("get_cost_of_capital", "Return the cost of capital inputs for a registered company and scenario.", SCEN)
TOOL_BRIDGE = _tool("get_bridge_items", "Return the enterprise to equity bridge items for a registered company and scenario.", SCEN)
TOOL_MARKET = _tool("get_market_data", "Return the share price, share count, market capitalisation and net debt items for a registered company.", SCEN)
TOOL_GRID = _tool("get_sensitivity_grid", "Return the enterprise value sensitivity grid across discount rate and terminal growth.", SCEN)

def p_forecast(f):
    return {"company": f["name"], "scenario": f["scenario"], "units": "USD millions",
            "years": f["years"], "revenue": f["rev"], "ebit": f["ebit"],
            "depreciation_amortisation": f["da"], "capital_expenditure": f["capex"],
            "increase_in_net_working_capital": f["dnwc"], "tax_rate_percent": f["tax"],
            "wacc_percent": f["wacc"], "terminal_growth_percent": f["g"],
            "exit_multiple": f["exit_mult"],
            "discounting_convention": "mid-year" if f["conv"] == "mid_year" else "year-end"}

def p_capital(f):
    return {"company": f["name"], "scenario": f["scenario"], "risk_free_rate_percent": f["rf"],
            "equity_risk_premium_percent": f["erp"], "levered_beta": f["beta"],
            "debt_to_equity": f["de"], "pre_tax_cost_of_debt_percent": f["kd"],
            "marginal_tax_rate_percent": f["tax"], "target_debt_share_percent": f["wd"],
            "target_equity_share_percent": f["we"]}

def p_bridge(f):
    return {"company": f["name"], "scenario": f["scenario"], "debt": f["debt"], "cash": f["cash"],
            "minority_interest": f["minorities"], "preferred_stock": f["preferred"],
            "pension_deficit": f["pension"], "interest_expense": f["interest"],
            "shares_outstanding_millions": f["shares"]}

def p_market(f, d):
    return {"company": f["name"], "scenario": f["scenario"], "share_price_dollars": f["price"],
            "shares_outstanding_millions": f["shares"], "market_capitalisation": d["mcap"]}

def _tc(f, calls, first, final):
    msgs = [{"role": "system", "content": "You are supporting the valuation review for %s (%s)." % (f["name"], f["sector"])},
            {"role": "user", "content": first}]
    for tname, payload in calls:
        msgs.append({"role": "assistant", "content": "I will call %s." % tname})
        msgs.append({"role": "tool", "content": json.dumps(payload)})
    msgs.append({"role": "user", "content": final})
    return msgs

def _t1(f, d):
    i = yi(f, d)
    return (_tc(f, [("get_forecast", p_forecast(f))], "Pull the forecast in the file and confirm the revenue line before I use it.",
                 "Thanks. Now give me the free cash flow to the firm for %s, in USD millions." % d["years"][i]),
            [TOOL_FORECAST, TOOL_MARKET], d["fcff"][i], "number", "rel:0.005")

def _t2(f, d):
    return (_tc(f, [("get_cost_of_capital", p_capital(f))], "Pull the cost of capital inputs in the file.",
                 "Using those inputs, what is the cost of equity, in percent?"),
            [TOOL_CAPITAL, TOOL_FORECAST], d["ke"], "number", "abs:0.1")

def _t3(f, d):
    return (_tc(f, [("get_forecast", p_forecast(f))], "Pull the forecast in the file so I can size the terminal value.",
                 "Using the stated discount rate and terminal growth rate, what is the Gordon growth terminal value at the end of %s, in USD millions?" % d["years"][-1]),
            [TOOL_FORECAST, TOOL_BRIDGE], d["tv"], "number", "rel:0.005")

def _t4(f, d):
    return (_tc(f, [("get_forecast", p_forecast(f)), ("get_bridge_items", p_bridge(f))],
                 "Pull the forecast and the bridge items in the file.",
                 "What is the equity value per share on the Gordon growth enterprise value, in dollars?"),
            [TOOL_FORECAST, TOOL_BRIDGE], d["ps"], "number", "abs:0.1")

def _t5(f, d):
    return (_tc(f, [("get_forecast", p_forecast(f)), ("get_market_data", p_market(f, d)),
                    ("get_bridge_items", p_bridge(f))],
                 "Pull the forecast and the market data in the file.",
                 "What is the implied upside to the market price, in percent?"),
            [TOOL_FORECAST, TOOL_MARKET, TOOL_BRIDGE], d["upside"], "number", "abs:1")

def _t6(f, d):
    bad = f["name"][:-1]
    sysm = {"role": "system", "content": "You are supporting the valuation review for %s (%s)." % (f["name"], f["sector"])}
    msgs = [sysm, {"role": "user", "content": "Pull the base case forecast for the company in the brief and check the first year revenue."},
            {"role": "assistant", "content": "I will call get_forecast."},
            {"role": "tool", "content": json.dumps({"error": "company_not_found", "requested": bad, "suggestions": [f["name"]]})},
            {"role": "assistant", "content": "The registry has no company named %s. It suggests %s, so I will retry with that name." % (bad, f["name"])},
            {"role": "tool", "content": json.dumps(p_forecast(f))},
            {"role": "user", "content": "Good. What is the first year free cash flow to the firm, in USD millions?"}]
    return (msgs, [TOOL_FORECAST, TOOL_MARKET], d["fcff"][0], "number", "rel:0.005")

def _t7(f, d):
    pay = p_forecast(f)
    pay.pop("exit_multiple")
    msgs = [{"role": "system", "content": "You are supporting the valuation review for %s (%s)." % (f["name"], f["sector"])},
            {"role": "user", "content": "Compute the exit multiple terminal value for this file."},
            {"role": "assistant", "content": "I will call get_forecast."},
            {"role": "tool", "content": json.dumps(pay)},
            {"role": "assistant", "content": "The forecast payload does not include an exit multiple. What multiple should I apply to final year EBITDA?"},
            {"role": "user", "content": "Use %s times. What is the terminal value, in USD millions?" % fmt(f["exit_mult"])}]
    return (msgs, [TOOL_FORECAST, TOOL_BRIDGE], d["tv_x"], "number", "rel:0.005")

def _t8(f, d):
    ri, ci = (f["idx"] // 2) % 5, (f["idx"] // 3) % 5
    payload = {"company": f["name"], "scenario": f["scenario"], "wacc_values_percent": d["gw"],
               "terminal_growth_values_percent": d["gg"], "enterprise_value": d["grid"]}
    return (_tc(f, [("get_sensitivity_grid", payload)], "Pull the sensitivity grid in the file.",
                 "What is the enterprise value at a discount rate of %s percent and terminal growth of %s percent, in USD millions?" % (fmt(d["gw"][ri]), fmt(d["gg"][ci]))),
            [TOOL_GRID, TOOL_MARKET], d["grid"][ri][ci], "number", "rel:0.005")

def _t9(f, d):
    return (_tc(f, [("get_forecast", p_forecast(f)), ("get_market_data", p_market(f, d)),
                    ("get_bridge_items", p_bridge(f))],
                 "Pull the forecast and the market data for the reverse check.",
                 "At the market price, what terminal growth rate does the Gordon growth model imply, in percent?"),
            [TOOL_FORECAST, TOOL_MARKET, TOOL_BRIDGE], _implied_g_price(f, d), "number", "abs:0.1")

def _t10(f, d):
    partner = next(x for x in FIXTURES if x["name"] == f["name"] and x["key"] != f["key"])
    i = 1 if d["n"] > 1 else 0
    return (_tc(f, [("get_forecast", p_forecast(f)), ("get_forecast", p_forecast(partner))],
                 "Pull two scenarios for this company.",
                 "What is the difference in %s free cash flow to the firm between the %s scenario and the %s scenario, in USD millions?" % (partner["years"][i], partner["scenario"], f["scenario"])),
            [TOOL_FORECAST, TOOL_MARKET], round(partner["d"]["fcff"][i] - d["fcff"][i], 1), "number", "rel:0.005")
TOOL_F = [_f("t_fcff", "tool_use", None, _t1), _f("t_ke", "tool_use", None, _t2), _f("t_tv", "tool_use", None, _t3),
          _f("t_ps", "tool_use", None, _t4), _f("t_upside", "tool_use", None, _t5), _f("t_retry", "tool_use", None, _t6),
          _f("t_missing", "tool_use", None, _t7), _f("t_grid", "tool_use", None, _t8), _f("t_implied", "tool_use", None, _t9),
          _f("t_compare", "tool_use", None, _t10)]
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa",
        "classification": "cls", "summarization": "summ", "tool_use": "tool"}
MASK = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")
FAMS = {"calc": CALC_F, "extraction": EXTR_F, "qa": QA_F, "summarization": SUMM_F}

def mask(s):
    return MASK.sub("#", WS.sub(" ", str(s)).strip().lower())

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def spread(total, k):
    base, extra = divmod(total, k)
    return [base + 1] * extra + [base] * (k - extra)

def pick(fams, f, used, ctr):
    n = len(fams)
    for s in range(n):
        cand = fams[(ctr + s) % n]
        if cand["name"] in used or (cand.get("needs") and not cand["needs"](f)):
            continue
        return cand, (ctr + s + 1) % n
    raise RuntimeError("no family for %s" % f["key"])

def row_single(task, ctx, q, gt, at, tol, split):
    return {"id": "", "task": task, "source": SOURCE, "context": ctx, "question": q,
            "ground_truth": gt, "answer_type": at, "tolerance": tol, "split": split,
            "thinking": THINK[task]}

def groups_of(splits):
    return {sp: sorted([f for f in FIXTURES if splits[f["key"]] == sp], key=lambda x: x["h"])
            for sp in ("train", "val", "test")}

def build_generic(task, splits, targets=None):
    fams = FAMS[task]
    quota = QUOTA[task]
    tr, va = int(round(quota * 0.8)), int(round(quota * 0.1))
    targets = targets or {"train": tr, "val": va, "test": quota - tr - va}
    out, ctr = [], 0
    groups = groups_of(splits)
    for sp in ("train", "val", "test"):
        fl = groups[sp]
        for f, k in zip(fl, spread(targets[sp], len(fl))):
            used = set()
            for _ in range(k):
                fam, ctr = pick(fams, f, used, ctr)
                used.add(fam["name"])
                q, gt, at, tol = fam["fn"](f, f["d"])
                out.append(row_single(task, get_ctx(f, fam["ctx"]), q, gt, at, tol, sp))
    return out

def build_qa(splits):
    out = build_generic("qa", splits, {"train": 128, "val": 16, "test": 16})
    for i, (q, a) in enumerate(sorted(KNOW, key=lambda p: sha(p[0]))):
        sp = "train" if i < 32 else ("val" if i < 36 else "test")
        out.append({"id": "", "task": "qa", "source": "knowledge:finance_general", "context": "",
                    "question": q, "ground_truth": a, "answer_type": "text",
                    "tolerance": "normalized", "split": sp, "thinking": "on"})
    return out
CLS_ALLOC = {0: [(6, 1, 1), (7, 0, 1), (7, 1, 1)], 1: [(6, 1, 1), (7, 1, 0), (7, 1, 1)]}

def build_classification(splits):
    out = []
    for fi, fam in enumerate(CLS_F):
        pools = {}
        for sp in ("train", "val", "test"):
            by = {}
            for f in sorted([f for f in FIXTURES if splits[f["key"]] == sp],
                            key=lambda x: sha(x["key"] + fam["name"])):
                by.setdefault(_bucket(f, f["d"], fam["kind"]), []).append(f)
            pools[sp] = by
        for li, lab in enumerate(fam["labels"]):
            for si, sp in enumerate(("train", "val", "test")):
                k = CLS_ALLOC[fi % 2][li][si]
                src = pools[sp].get(lab, [])
                if len(src) < k:
                    raise RuntimeError("bucket %s starved in %s" % (lab, sp))
                for f in src[:k]:
                    out.append({"id": "", "task": "classification", "source": SOURCE,
                                "context": get_ctx(f, "valuation"), "question": fam["q"],
                                "ground_truth": lab, "answer_type": "label", "tolerance": "exact",
                                "split": sp, "thinking": "off"})
    return out

def build_fixed(fams, counts, splits, task):
    out = []
    for fi, fam in enumerate(fams):
        for sp, k in (("train", counts[0]), ("val", counts[1]), ("test", counts[2])):
            pool = sorted([f for f in FIXTURES if splits[f["key"]] == sp],
                          key=lambda x: sha(x["key"] + fam["name"]))
            start = (fi * 17 + {"train": 0, "val": 5, "test": 11}[sp]) % len(pool)
            for f in [pool[(start + i) % len(pool)] for i in range(k)]:
                if task == "tool_use":
                    msgs, tools, gt, at, tol = fam["fn"](f, f["d"])
                    out.append({"id": "", "task": "tool_use", "source": SOURCE, "messages": msgs,
                                "tools": tools, "ground_truth": gt, "answer_type": at,
                                "tolerance": tol, "split": sp, "thinking": "on"})
                else:
                    q, gt, at, tol = fam["fn"](f, f["d"])
                    out.append(row_single(task, get_ctx(f, fam["ctx"]), q, gt, at, tol, sp))
    return out

def main():
    for f in FIXTURES:
        f["h"] = sha(f["key"])
    order = sorted(FIXTURES, key=lambda f: f["h"])
    ntr, nva = int(round(len(order) * 0.8)), int(round(len(order) * 0.1))
    splits = {f["key"]: ("train" if i < ntr else ("val" if i < ntr + nva else "test"))
              for i, f in enumerate(order)}
    rows = []
    rows += build_generic("calc", splits)
    rows += build_generic("extraction", splits)
    rows += build_qa(splits)
    rows += build_classification(splits)
    rows += build_fixed(SUMM_F, (16, 2, 2), splits, "summarization")
    rows += build_fixed(TOOL_F, (8, 1, 1), splits, "tool_use")
    counters = {}
    for r in rows:
        counters[r["task"]] = counters.get(r["task"], 0) + 1
        r["id"] = "fin_valuation_dcf_%s_%06d" % (ABBR[r["task"]], counters[r["task"]])
        if "question" in r and not 8 <= len(r["question"]) <= 600:
            raise RuntimeError("bad question length: %s" % r["question"][:80])
    with open(os.path.join(OUT_DIR, "prompts.jsonl"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    raw = open(os.path.join(OUT_DIR, "prompts.jsonl"), "rb").read()
    fams, ctxs, task_c, split_c, at_c, pair_splits = {}, set(), {}, {}, {}, {}
    for r in rows:
        t = r["task"]
        task_c[t] = task_c.get(t, 0) + 1
        split_c[r["split"]] = split_c.get(r["split"], 0) + 1
        if r["ground_truth"] is not None:
            at_c[r["answer_type"]] = at_c.get(r["answer_type"], 0) + 1
        if "messages" in r:
            fs = next(m["content"] for m in r["messages"] if m["role"] == "user")
            pair = json.dumps(r["messages"], sort_keys=True)
        else:
            fs = r["question"]
            if r["context"]:
                ctxs.add(mask(r["context"]))
            pair = mask(r["context"]) + "|" + mask(r["question"])
        fams[mask(fs)[:160]] = fams.get(mask(fs)[:160], 0) + 1
        pair_splits.setdefault(pair, set()).add(r["split"])
    report = {
        "area": AREA, "profile": "A", "rows": len(rows),
        "by_task": {t: task_c.get(t, 0) for t in TASKS},
        "by_split": {s: split_c.get(s, 0) for s in ("train", "val", "test")},
        "by_answer_type": {a: at_c.get(a, 0) for a in ("number", "text", "label", "list")},
        "distinct_question_families": len(fams),
        "top_family_share": round(max(fams.values()) / float(len(rows)), 4),
        "distinct_contexts": len(ctxs),
        "near_dup_pairs": sum(1 for v in pair_splits.values() if len(v) > 1),
        "tool_use_multi_step_share": round(task_c.get("tool_use", 0) / float(max(1, task_c.get("tool_use", 0))), 3),
        "validation": "pass", "sha256": hashlib.sha256(raw).hexdigest(),
        "notes": "Synthetic fixtures over 20 fictional issuers and 10 scenarios; every ground truth is recomputed from the fixture dict rendered into context.",
    }
    with open(os.path.join(OUT_DIR, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps({k: report[k] for k in ("rows", "by_task", "by_split", "distinct_question_families",
                                            "top_family_share", "distinct_contexts", "near_dup_pairs")}, indent=2))
if __name__ == "__main__":
    main()