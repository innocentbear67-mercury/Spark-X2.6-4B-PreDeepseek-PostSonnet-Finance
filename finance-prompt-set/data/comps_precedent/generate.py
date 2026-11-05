#!/usr/bin/env python3
"""Deterministic generator for the comps_precedent area of the finance prompt set.
Everything is synthetic: 30 fictional issuers, peer-table snapshots, precedent tapes,
exchange-ratio terms, cross-border unit traps and misleading-multiple cases.  Every
ground_truth value is recomputed in code from the same fixture dict rendered into context.
"""
import hashlib
import json
import os
import random
import re
from collections import Counter, defaultdict
AREA = "comps_precedent"
SOURCE = "synthetic:" + AREA
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "prompts.jsonl")
REPORT_PATH = os.path.join(HERE, "report.json")
RNG = random.Random(42)
QUOTA = {"calc": 280, "extraction": 220, "qa": 200, "classification": 100, "summarization": 100, "tool_use": 100}
THINK = {"calc": "on", "extraction": "off", "qa": "on", "classification": "off", "summarization": "off", "tool_use": "on"}
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls", "summarization": "summ", "tool_use": "tool"}
UNITS = "Units: $ in millions except per-share amounts in dollars and percentages in percent."
MASK = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")
REG = [ ("Halcyon Grid Utilities", "Regulated Utilities", "31 December"), ("Northwind Power", "Regulated Utilities", "31 December"), ("Cedar Valley Electric", "Regulated Utilities", "30 June"), ("Piedmont Water Works", "Regulated Utilities", "31 March"), ("Blue Ridge Transmission", "Regulated Utilities", "31 December"), ("Arboreta Energy Partners", "Regulated Utilities", "30 September"), ("Meridian Bancorp", "Regional Banks", "31 December"), ("Cascade Trust Financial", "Regional Banks", "31 December"), ("Harborline Savings", "Regional Banks", "30 June"), ("Granite Peak Bank", "Regional Banks", "31 December"), ("Silverbrook Financial", "Regional Banks", "30 September"), ("Wexler Community Bank", "Regional Banks", "31 March"), ("Northgate Software", "Application Software", "31 January"), ("Bellwether Analytics", "Application Software", "31 December"), ("Quillon Systems", "Application Software", "31 December"), ("Alder Grove Cloud", "Application Software", "30 June"), ("Tessellate Data", "Application Software", "31 March"), ("Lantern Path Software", "Application Software", "30 September"), ("Fairhaven Medical", "Medical Devices", "31 December"), ("Ironwood Surgical", "Medical Devices", "30 June"), ("Pathstone Diagnostics", "Medical Devices", "31 December"), ("Corvane Orthopedics", "Medical Devices", "31 March"), ("Sable Respiratory", "Medical Devices", "30 September"), ("Juniper Medical", "Medical Devices", "31 December"), ("Kestrel Foods", "Packaged Foods", "31 December"), ("Larkspur Dairy", "Packaged Foods", "30 June"), ("Tamarind Snacks", "Packaged Foods", "31 May"), ("Winterbourne Pantry", "Packaged Foods", "30 September"), ("Sable Creamery", "Packaged Foods", "31 March"), ("Orchard Gate Beverages", "Packaged Foods", "31 December"), ]
SECTORS = ["Regulated Utilities", "Regional Banks", "Application Software", "Medical Devices", "Packaged Foods"]
BY_SECTOR = defaultdict(list)
for _n, _s, _f in REG:
    BY_SECTOR[_s].append({"name": _n, "sector": _s, "fy": _f})
ALLCO = [c for c in REG]
SNAP = ["30 June 2025", "31 March 2025", "30 September 2025", "31 December 2024"]
MONTHS = ["14 Mar 2024", "02 Sep 2023", "21 Jun 2024", "08 Nov 2023", "30 Jan 2024", "17 Jul 2023", "05 May 2024", "12 Dec 2023", "26 Feb 2024", "19 Oct 2023"]
def cl(x, dp):
    v = round(float(x), dp)
    return 0.0 if abs(v) < 10 ** (-dp) / 2.0 else v
def s0(x):
    return "%d" % int(round(float(x)))
def s1(x):
    return "%.1f" % cl(x, 1)
def s2(x):
    return "%.2f" % cl(x, 2)
def s4(x):
    return "%.4f" % cl(x, 4)
def mask(s):
    return MASK.sub("#", WS.sub(" ", str(s)).strip().lower())
def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0
def mean(xs):
    return sum(xs) / float(len(xs))
def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)
def row(task, fam, ctx, q, gt, at, tol, fx):
    if gt is None:
        at, tol = "text", None
    elif isinstance(gt, (int, float)) and not isinstance(gt, bool) and at == "text":
        at, tol = "number", "abs:0.01"
    return {"task": task, "fam": fam, "ctx": ctx, "q": q, "gt": gt, "at": at, "tol": tol, "fx": fx}
def T(q, fn, at="number", tol="abs:0.1"):
    return (q, fn, at, tol)
class Book(object):
    def __init__(self):
        self.seen = set()
    def ok(self, ctx):
        m = mask(ctx)
        if m in self.seen:
            return False
        self.seen.add(m)
        return True
# ---------------------------------------------------------------- metrics ---
def ev_of(p):
    return p["price"] * p["shares"] + p["debt"] - p["cash"] + p["mi"] + p["pref"] + p["pen"]
def nd_of(p):
    return p["debt"] - p["cash"] + p["mi"] + p["pref"] + p["pen"]
def mk_ind(rng, out=False):
    ebitda = float(rng.randrange(320, 3200, 10))
    ebit = float(int(ebitda * rng.uniform(0.55, 0.82)))
    ni = float(max(1, int(ebit * rng.uniform(0.42, 0.78))))
    rev = float(int(ebitda * rng.uniform(2.2, 8.5)))
    capex = float(int(ebitda * rng.uniform(0.10, 0.45)))
    debt = float(int(ebitda * rng.uniform(0.3, 3.0)))
    cash = float(int(ebitda * rng.uniform(0.05, 0.70)))
    mi = float(int(ebitda * rng.choice([0, 0, 0, 0, 0.02, 0.05, 0.08])))
    pref = float(int(ebitda * rng.choice([0, 0, 0, 0, 0, 0.03, 0.06])))
    pen = float(int(ebitda * rng.choice([0, 0, 0, 0, 0.01, 0.03, 0.05])))
    mult = rng.uniform(14.0, 18.0) if out else rng.uniform(6.0, 11.0)
    eq = ebitda * mult - (debt - cash) - mi - pref - pen
    if eq < ebitda * 2.5:
        debt = max(0.0, debt - ebitda * 2.0)
        eq = ebitda * mult - (debt - cash) - mi - pref - pen
    if eq <= 0:
        return None
    shares = float(int(rng.uniform(60, 1600)))
    price = round(eq / shares, 2)
    if price < 3.0 or price > 240.0:
        return None
    return {"ebitda": ebitda, "ebit": ebit, "ni": ni, "rev": rev, "capex": capex, "debt": debt, "cash": cash, "mi": mi, "pref": pref, "pen": pen, "shares": shares, "price": price, "no_db": rng.random() < 0.18}
def mk_bank(rng):
    book = float(int(rng.uniform(1200, 9000)))
    tbv = float(int(book * rng.uniform(0.60, 0.90)))
    ni = float(int(rng.uniform(120, 900)))
    shares = float(int(rng.uniform(80, 900)))
    price = round(rng.uniform(8.5, 14.5) * ni / shares, 2)
    if price < 4.0:
        return None
    return {"book": book, "tbv": tbv, "ni": ni, "shares": shares, "price": price, "assets": float(int(book * rng.uniform(7.0, 12.0))), "cet1": round(rng.uniform(9.8, 14.6), 1)}
HDR_FULL = ["Company", "Price ($)", "Diluted shares (m)", "Total debt", "Cash", "Minorities", "Preferred", "Pension", "LTM EBITDA", "LTM EBIT", "LTM net income", "LTM revenue", "Capex"]
BANK_HDR = ["Company", "Price ($)", "Diluted shares (m)", "Book equity", "Tangible book equity", "LTM net income", "Total assets", "CET1 ratio (%)"]
def prow_full(p):
    return [p["name"], s2(p["price"]), s0(p["shares"]), s0(p["debt"]), s0(p["cash"]), s0(p["mi"]), s0(p["pref"]), "n/a" if p["no_db"] else s0(p["pen"]), s0(p["ebitda"]), s0(p["ebit"]), s0(p["ni"]), s0(p["rev"]), s0(p["capex"])]
def prow_bank(p):
    return [p["name"], s2(p["price"]), s0(p["shares"]), s0(p["book"]), s0(p["tbv"]), s0(p["ni"]), s0(p["assets"]), s1(p["cet1"])]
# ------------------------------------------------------------ peer fixtures ---
PEER_CALC = { "ev_ebitda_med": T("Using the enterprise value bridge (market capitalisation plus total debt, minority interest, preferred ""stock and pension deficit, less cash), compute EV/LTM EBITDA for every peer in the table on the figures ""as presented, then report the peer median, in turns to one decimal.", lambda d: cl(median([ev_of(p) / p["ebitda"] for p in d["peers"]]), 1)), "ev_ebitda_mean": T("Compute EV/LTM EBITDA for every peer from the enterprise value bridge (market capitalisation plus total ""debt, minority interest, preferred stock and pension deficit, less cash) and report the simple peer mean ""rather than the median, in turns to one decimal.", lambda d: cl(mean([ev_of(p) / p["ebitda"] for p in d["peers"]]), 1)), "ev_ebit_med": T("Compute EV/LTM EBIT for every peer and report the peer median, in turns to one decimal, using the enterprise ""value bridge (market capitalisation plus total debt, minority interest, preferred stock and pension deficit, ""less cash).", lambda d: cl(median([ev_of(p) / p["ebit"] for p in d["peers"]]), 1)), "pe_med": T("Compute the price to LTM earnings ratio (market capitalisation divided by LTM net income) for every peer and report ""the peer median, in turns to one decimal.", lambda d: cl(median([p["price"] * p["shares"] / p["ni"] for p in d["peers"]]), 1)), "ev_sales_med": T("Compute EV/LTM revenue for every peer and report the peer median, in turns to one decimal.", lambda d: cl(median([ev_of(p) / p["rev"] for p in d["peers"]]), 1)), "trim_mean": T("Drop the highest and the lowest EV/LTM EBITDA multiple in the peer set, then report the mean of the remaining ""multiples as a trimmed mean, in turns to one decimal.", lambda d: cl(mean(sorted([ev_of(p) / p["ebitda"] for p in d["peers"]])[1:-1]), 1)), "lev_med": T("Compute net debt to LTM EBITDA for every peer, where net debt is total debt less cash and excludes minority ""interest, preferred stock and the pension deficit, and report the peer median in turns to one decimal.", lambda d: cl(median([(p["debt"] - p["cash"]) / p["ebitda"] for p in d["peers"]]), 1)), "ev_fcf_med": T("Treat free cash flow as LTM EBITDA less capex, compute EV/FCF for every peer and report the peer median, in ""turns to one decimal.", lambda d: cl(median([ev_of(p) / (p["ebitda"] - p["capex"]) for p in d["peers"]]), 1)), "impl_ev": T("Apply the peer median EV/LTM EBITDA to the subject company's LTM EBITDA and report the implied enterprise value, ""in $ millions.", lambda d: cl(median([ev_of(p) / p["ebitda"] for p in d["peers"]]) * d["subj"]["ebitda"], 0), "number", "abs:1"), "impl_eq": T("Bridge from the peer-median enterprise value to equity value: apply the peer median EV/LTM EBITDA to the subject's ""LTM EBITDA, then deduct total debt, minority interest, preferred stock and pension deficit and add cash; report the ""implied equity value, in $ millions.", lambda d: cl(median([ev_of(p) / p["ebitda"] for p in d["peers"]]) * d["subj"]["ebitda"] - nd_of(d["subj"]), 0), "number", "abs:1"), "impl_ps": T("Divide the implied equity value (peer median EV/LTM EBITDA applied to the subject's LTM EBITDA, less total debt, ""minority interest, preferred stock and pension deficit, plus cash) by the subject's diluted shares and report the ""implied value per share, in dollars to two decimals.", lambda d: cl((median([ev_of(p) / p["ebitda"] for p in d["peers"]]) * d["subj"]["ebitda"] - nd_of(d["subj"])) / d["subj"]["shares"], 2), "number", "abs:0.01"), "prem_disc": T("Compute the subject company's EV/LTM EBITDA and express it as a premium or discount to the peer median EV/LTM ""EBITDA, in percent to one decimal; a positive number means the subject trades above the peer median.", lambda d: cl((ev_of(d["subj"]) / d["subj"]["ebitda"] / median([ev_of(p) / p["ebitda"] for p in d["peers"]]) - 1.0) * 100.0, 1)), "spread": T("Report the spread between the highest and the lowest peer EV/LTM EBITDA multiple, in turns to one decimal.", lambda d: cl(max([ev_of(p) / p["ebitda"] for p in d["peers"]]) - min([ev_of(p) / p["ebitda"] for p in d["peers"]]), 1)), "max_ev": T("Report the largest enterprise value in the peer set, in $ millions.", lambda d: cl(max([ev_of(p) for p in d["peers"]]), 0), "number", "abs:1"), "adj_ev_ebitda": T("Using footnote 1, add back the non-recurring integration costs to the affected peer's LTM EBITDA and recompute ""that peer's EV/LTM EBITDA, in turns to one decimal.", lambda d: cl(ev_of(d["adj_peer"]) / (d["adj_peer"]["ebitda"] + d["cost"]), 1)), "med_ex_high": T("Exclude the peer with the highest EV/LTM EBITDA multiple and report the median of the remaining peer multiples, ""in turns to one decimal.", lambda d: cl(median(sorted([ev_of(p) / p["ebitda"] for p in d["peers"]])[:-1]), 1)), }
PEER_EXTR = { "x_ebitda": T("Report the LTM EBITDA shown for the third peer listed in the peer set, in $ millions.", lambda d: cl(d["peers"][2]["ebitda"], 0), "number", "abs:0.01"), "x_debt": T("What total debt is shown for the second peer listed, in $ millions?", lambda d: cl(d["peers"][1]["debt"], 0), "number", "abs:0.01"), "x_cash": T("What cash balance does the subject company report, in $ millions?", lambda d: cl(d["subj"]["cash"], 0), "number", "abs:0.01"), "x_shares": T("Report the diluted share count of the fourth peer listed, in millions.", lambda d: cl(d["peers"][3]["shares"], 0), "number", "abs:0.01"), "x_pension": T("What pension deficit is disclosed for the third peer listed? Answer with the figure in $ millions, or n/a if the ""cell is blank.", lambda d: ("n/a" if d["peers"][2]["no_db"] else cl(d["peers"][2]["pen"], 0)), "text", "normalized"), "x_price": T("What share price is shown for the subject company, in dollars?", lambda d: cl(d["subj"]["price"], 2), "number", "abs:0.01"), "x_date": T("State the snapshot date given above the peer table, exactly as written.", lambda d: d["date"], "text", "normalized"), "x_foot": T("Which peer is referenced in footnote 1? Answer with the company name exactly as written.", lambda d: d["adj_peer"]["name"], "text", "normalized"), "x_ni": T("Report LTM net income for the second peer listed, in $ millions.", lambda d: cl(d["peers"][1]["ni"], 0), "number", "abs:0.01"), "x_capex": T("Report the capex shown for the first peer listed, in $ millions.", lambda d: cl(d["peers"][0]["capex"], 0), "number", "abs:0.01"), "x_cost": T("How much non-recurring integration cost is charged in footnote 1, in $ millions?", lambda d: cl(d["cost"], 0), "number", "abs:0.01"), }
PEER_QA = { "qa_gap": T("By how many turns does the peer mean EV/LTM EBITDA exceed the peer median? Report the gap to one decimal; a negative ""number means the mean is below the median.", lambda d: cl(mean([ev_of(p) / p["ebitda"] for p in d["peers"]]) - median([ev_of(p) / p["ebitda"] for p in d["peers"]]), 1)), "qa_share_below": T("What percentage of the peer set trades below the subject company's EV/LTM EBITDA? Report in percent to one decimal.", lambda d: cl(100.0 * len([1 for p in d["peers"] if ev_of(p) / p["ebitda"] < ev_of(d["subj"]) / d["subj"]["ebitda"]]) / len(d["peers"]), 1)), "qa_cheapest": T("Which peer trades at the lowest EV/LTM EBITDA multiple? Answer with the company name exactly as written in the table.", lambda d: sorted(d["peers"], key=lambda p: ev_of(p) / p["ebitda"])[0]["name"], "label", "exact"), "qa_levered": T("Which peer carries the highest net debt to LTM EBITDA? Answer with the company name exactly as written in the table.", lambda d: sorted(d["peers"], key=lambda p: (p["debt"] - p["cash"]) / p["ebitda"])[-1]["name"], "label", "exact"), "qa_count_below": T("How many peers trade below the subject company's EV/LTM EBITDA? Answer with a whole number.", lambda d: len([1 for p in d["peers"] if ev_of(p) / p["ebitda"] < ev_of(d["subj"]) / d["subj"]["ebitda"]]), "number", "abs:0.01"), "qa_range": T("Report the difference between the highest and the lowest net debt to LTM EBITDA across the peer set, in turns to one decimal.", lambda d: cl(max([(p["debt"] - p["cash"]) / p["ebitda"] for p in d["peers"]]) - min([(p["debt"] - p["cash"]) / p["ebitda"] for p in d["peers"]]), 1)), "qa_upside": T("If the subject re-rated to the peer median EV/LTM EBITDA, what would the upside or downside from its share price be, ""in percent to one decimal?", lambda d: cl(((median([ev_of(p) / p["ebitda"] for p in d["peers"]]) * d["subj"]["ebitda"] - nd_of(d["subj"])) / d["subj"]["shares"] / d["subj"]["price"] - 1.0) * 100.0, 1)), "qa_margin": T("Which peer has the highest LTM EBITDA margin, measured as LTM EBITDA divided by LTM revenue? Answer with the company ""name exactly as written in the table.", lambda d: sorted(d["peers"], key=lambda p: p["ebitda"] / p["rev"])[-1]["name"], "label", "exact"), "qa_judge": T("Is the peer median a reliable benchmark for the subject here, or does one outlier distort the set? Answer in two sentences.", lambda d: None, "text", "normalized"), }
PEER_CLS = { "k_vs_median": ("Classify the subject company's EV/LTM EBITDA against the peer median using the set {at a discount, in line, at a ""premium}; treat a difference within 0.5 turns of the median as in line.", lambda d: ("at a discount" if ev_of(d["subj"]) / d["subj"]["ebitda"] < median([ev_of(p) / p["ebitda"] for p in d["peers"]]) - 0.5 else ("at a premium" if ev_of(d["subj"]) / d["subj"]["ebitda"] > median([ev_of(p) / p["ebitda"] for p in d["peers"]]) + 0.5 else "in line"))), "k_outlier": ("Classify how the highest peer EV/LTM EBITDA multiple sits against the rest of the set using the set {an outlier, within ""range}; treat a multiple at least 3.0 turns above the second highest as an outlier.", lambda d: ("an outlier" if (lambda m: m[0] - m[1] >= 3.0)(sorted([ev_of(p) / p["ebitda"] for p in d["peers"]], reverse=True)) else "within range")), }
def build_peer(rng, book, idx):
    for _ in range(80):
        sector = SECTORS[idx % len(SECTORS)]
        members = BY_SECTOR[sector]
        tgt = members[(idx // len(SECTORS)) % len(members)]
        others = [c for c in members if c["name"] != tgt["name"]]
        ps = []
        for c in rng.sample(others, 4 if rng.random() < 0.7 else 5):
            m = mk_ind(rng)
            if m is None:
                break
            m["name"] = c["name"]
            ps.append(m)
        if len(ps) < 4:
            continue
        if idx % 2 == 0:
            o = mk_ind(rng, out=True)
            if o is None:
                continue
            o["name"] = ps[-1]["name"]
            ps[-1] = o
        subj = mk_ind(rng)
        if subj is None:
            continue
        subj["name"] = tgt["name"]
        pm = median([ev_of(p) / p["ebitda"] for p in ps])
        eq = pm * [0.85, 1.0, 1.15][idx % 3] * subj["ebitda"] - nd_of(subj)
        if eq <= 0:
            continue
        subj["price"] = round(eq / subj["shares"], 2)
        if subj["price"] < 3:
            continue
        cost = float(int(ps[0]["ebitda"] * rng.uniform(0.06, 0.14))) + 10.0
        date = SNAP[rng.randrange(len(SNAP))]
        hdr, pr = HDR_FULL, prow_full
        ctx = "\n".join([UNITS, "", "Trading comparables - %s. Snapshot as at %s. All figures are LTM to the snapshot date." % (sector, date), "The subject company is shown separately and is excluded from peer statistics.", "", "Peer set:", table(hdr, [pr(p) for p in ps]), "", "Subject company:", table(hdr, [pr(subj)]), "", "Footnotes:", "1. LTM EBITDA at %s is stated after charging %s of non-recurring integration costs." % (ps[0]["name"], s0(cost)), "2. Share prices are closing prices on the snapshot date; diluted shares include in-the-money options.", "3. A blank pension cell means the company carries no defined-benefit obligation."])
        if not book.ok(ctx):
            continue
        return {"key": "peer%03d" % idx, "ctx": ctx, "d": {"peers": ps, "subj": subj, "cost": cost, "date": date, "adj_peer": ps[0]}}
    return None
# ------------------------------------------------------------ bank fixtures ---
BANK_CALC = { "pe_med": T("Compute the price to LTM earnings ratio (market capitalisation divided by LTM net income) for every peer and report ""the peer median, in turns to one decimal.", lambda d: cl(median([p["price"] * p["shares"] / p["ni"] for p in d["peers"]]), 1)), "ptbv_med": T("Compute price to tangible book value (market capitalisation divided by tangible book equity) for every peer and ""report the peer median, in turns to one decimal.", lambda d: cl(median([p["price"] * p["shares"] / p["tbv"] for p in d["peers"]]), 1)), "impl_ps": T("Apply the peer median price to tangible book value to the subject company's tangible book equity and report the ""implied value per share, in dollars to two decimals.", lambda d: cl(median([p["price"] * p["shares"] / p["tbv"] for p in d["peers"]]) * d["subj"]["tbv"] / d["subj"]["shares"], 2), "number", "abs:0.01"), "prem_disc": T("Express the subject company's price to tangible book value as a premium or discount to the peer median, in percent ""to one decimal; a positive number means the subject trades above the peer median.", lambda d: cl((d["subj"]["price"] * d["subj"]["shares"] / d["subj"]["tbv"] / median([p["price"] * p["shares"] / p["tbv"] for p in d["peers"]]) - 1.0) * 100.0, 1)), }
BANK_EXTR = { "cet1": T("Report the CET1 ratio shown for the second peer listed, in percent.", lambda d: cl(d["peers"][1]["cet1"], 1), "number", "abs:0.01"), "tbv": T("What tangible book equity does the subject company report, in $ millions?", lambda d: cl(d["subj"]["tbv"], 0), "number", "abs:0.01"), }
BANK_QA = { "which": T("Given the way these banks are valued in the table, which multiple is the appropriate primary benchmark: EV/EBITDA or ""price to tangible book value? Answer with one of {EV/EBITDA, price to tangible book value}.", lambda d: "price to tangible book value", "label", "exact"), "book": T("What is the median tangible book equity divided by the median book equity across the peer set, in turns to two decimals?", lambda d: cl(median([p["tbv"] for p in d["peers"]]) / median([p["book"] for p in d["peers"]]), 2), "number", "abs:0.01"), }
BANK_CLS = {"ptbv": ("Classify the subject bank's price to tangible book value against the peer median using the set {at a discount, in ""line, at a premium}; treat a difference within 0.1 turns as in line.", lambda d: ("at a discount" if d["subj"]["price"] * d["subj"]["shares"] / d["subj"]["tbv"] < median([p["price"] * p["shares"] / p["tbv"] for p in d["peers"]]) - 0.1 else ("at a premium" if d["subj"]["price"] * d["subj"]["shares"] / d["subj"]["tbv"] > median([p["price"] * p["shares"] / p["tbv"] for p in d["peers"]]) + 0.1 else "in line")))}
def build_bank(rng, book, idx):
    for _ in range(80):
        members = BY_SECTOR["Regional Banks"]
        tgt = members[idx % len(members)]
        peers = rng.sample([c for c in members if c["name"] != tgt["name"]], 4)
        vals = []
        for c in [tgt] + peers:
            m = mk_bank(rng)
            if m is None:
                break
            m["name"] = c["name"]
            vals.append(m)
        if len(vals) != 5:
            continue
        pm = median([p["price"] * p["shares"] / p["tbv"] for p in vals[1:]])
        vals[0]["price"] = round(pm * [0.86, 1.0, 1.14][idx % 3] * vals[0]["tbv"] / vals[0]["shares"], 2)
        date = SNAP[rng.randrange(len(SNAP))]
        ctx = "\n".join([UNITS, "", "Regional bank comparables. Snapshot as at %s. Book equity and tangible book equity are the last reported ""balances; CET1 is the regulatory ratio." % date, "Bank valuation uses price to tangible book value and price to earnings. EBITDA-based multiples are not ""presented because interest expense is an operating cost for a bank.", "", "Peer set:", table(BANK_HDR, [prow_bank(p) for p in vals[1:]]), "", "Subject company:", table(BANK_HDR, [prow_bank(vals[0])]), "", "Footnotes:", "1. Tangible book equity excludes goodwill and other intangibles.", "2. Earnings are LTM net income attributable to common shareholders."])
        if not book.ok(ctx):
            continue
        return {"key": "bank%03d" % idx, "ctx": ctx, "d": {"peers": vals[1:], "subj": vals[0], "date": date}}
    return None
# ---------------------------------------------------- calendarisation table ---
CAL_HDR = ["Company", "Fiscal year end", "Share price ($)", "Diluted shares (m)", "Net debt", "FY2025A EBITDA", "FY2026E EBITDA", "Weight FY2025A", "Weight FY2026E"]
def cal_ebitda(p):
    return p["w1"] * p["e1"] + p["w2"] * p["e2"]
def cal_ev(p):
    return p["price"] * p["shares"] + p["nd"]
CAL_CALC = { "ce": T("Calendarise the first peer's LTM EBITDA to 31 December 2025 using the weights shown and the stated formula, in $ millions.", lambda d: cl(cal_ebitda(d["peers"][0]), 0), "number", "abs:1"), "cm": T("Compute the calendarised EV/LTM EBITDA multiple for the second peer listed, using its calendarised EBITDA and an enterprise ""value of market capitalisation plus net debt, in turns to one decimal.", lambda d: cl(cal_ev(d["peers"][1]) / cal_ebitda(d["peers"][1]), 1)), "cw": T("For the third peer listed, the valuation date is 31 December 2025. Using its stated fiscal year end and the convention that ""the weight on the earlier fiscal year equals the share of the trailing 12 months falling in that year, report the weight on ""FY2025A to two decimals.", lambda d: cl(d["peers"][2]["w1"], 2), "number", "abs:0.01"), "cv": T("For the fourth peer listed, report the calendarised EV/LTM EBITDA multiple minus the multiple computed on unadjusted FY2025A ""EBITDA alone, in turns to one decimal.", lambda d: cl(cal_ev(d["peers"][3]) / cal_ebitda(d["peers"][3]) - cal_ev(d["peers"][3]) / d["peers"][3]["e1"], 1)), "cmed": T("Compute the calendarised EV/LTM EBITDA multiple for every peer and report the peer median, in turns to one decimal.", lambda d: cl(median([cal_ev(p) / cal_ebitda(p) for p in d["peers"]]), 1)), "cshare": T("What share of the peer set has a fiscal year ending 31 March, in percent to one decimal?", lambda d: cl(100.0 * len([p for p in d["peers"] if p["fy"] == "31 March"]) / len(d["peers"]), 1)), }
CAL_EXTR = { "fy": T("What fiscal year end is shown for the second peer listed? Answer exactly as written in the table.", lambda d: d["peers"][1]["fy"], "text", "normalized"), "w2": T("What weight on FY2026E is shown for the fourth peer listed, to two decimals?", lambda d: cl(d["peers"][3]["w2"], 2), "number", "abs:0.01"), }
CAL_QA = { "effect": T("Would failing to calendarise push the peer median EV/LTM EBITDA up or down relative to the calendarised median? Answer ""with one of {up, down}.", lambda d: ("down" if mean([p["e2"] - p["e1"] for p in d["peers"]]) > 0 else "up"), "label", "exact"), "stale": T("Which peer's unadjusted FY2025A multiple is furthest from its calendarised multiple? Answer with the company name exactly ""as written.", lambda d: sorted(d["peers"], key=lambda p: abs(cal_ev(p) / cal_ebitda(p) - cal_ev(p) / p["e1"]))[-1]["name"], "label", "exact"), }
def build_cal(rng, book, idx):
    for _ in range(80):
        members = BY_SECTOR[SECTORS[(idx + 1) % len(SECTORS)]]
        tgt = members[idx % len(members)]
        peers = rng.sample([c for c in members if c["name"] != tgt["name"]], 4)
        vals = []
        for c in peers:
            e1 = float(rng.randrange(320, 2500, 10))
            e2 = float(int(e1 * (1.0 + rng.uniform(-0.06, 0.14))))
            w = rng.choice([0.25, 0.5, 0.75])
            sh = float(int(rng.uniform(80, 1400)))
            nd = float(int(e1 * rng.uniform(-0.2, 2.6)))
            eq = e1 * rng.uniform(6.0, 10.5) - nd
            if eq <= 0:
                break
            price = round(eq / sh, 2)
            if price < 3:
                break
            vals.append({"name": c["name"], "fy": c["fy"], "price": price, "shares": sh, "nd": nd, "e1": e1, "e2": e2, "w1": w, "w2": round(1.0 - w, 2)})
        if len(vals) != 4:
            continue
        ctx = "\n".join([UNITS, "", "Calendarised trading comparables for a 31 December 2025 valuation date. Every peer below has a fiscal year end ""that does not fall on 31 December, so LTM EBITDA is calendarised as (weight on FY2025A x FY2025A) + (weight on ""FY2026E x FY2026E). Enterprise value is market capitalisation plus net debt.", "", table(CAL_HDR, [[p["name"], p["fy"], s2(p["price"]), s0(p["shares"]), s0(p["nd"]), s0(p["e1"]), s0(p["e2"]), s2(p["w1"]), s2(p["w2"])] for p in vals]), "", "Note: the peer with a 31 March year end needs 9 months of FY2025A and 3 months of FY2026E to reach 31 December 2025."])
        if not book.ok(ctx):
            continue
        return {"key": "cal%03d" % idx, "ctx": ctx, "d": {"peers": vals, "date": "31 December 2025"}}
    return None
# ------------------------------------------------------- transaction tables ---
TX_HDR = ["Date", "Target", "Acquirer", "Offer per share ($)", "Unaffected price ($)", "30-day VWAP ($)", "Target diluted shares (m)", "Net debt assumed", "LTM EBITDA", "LTM revenue", "Run-rate synergies"]
def tx_ev(x):
    return x["offer"] * x["sh"] + x["nd"]
TX_CALC = { "prem_med": T("Compute the offer premium to the unaffected price for every deal in the tape and report the median premium, in percent ""to one decimal.", lambda d: cl(median([(x["offer"] / x["unaff"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "ev_med": T("Compute transaction enterprise value for every deal and report the median, in $ millions.", lambda d: cl(median([tx_ev(x) for x in d["deals"]]), 0), "number", "abs:1"), "mult_med": T("Compute transaction EV/LTM EBITDA for every deal and report the median, in turns to one decimal.", lambda d: cl(median([tx_ev(x) / x["ebitda"] for x in d["deals"]]), 1)), "syn_med": T("Compute transaction EV/(LTM EBITDA plus run-rate synergies) for every deal and report the median, in turns to one decimal.", lambda d: cl(median([tx_ev(x) / (x["ebitda"] + x["syn"]) for x in d["deals"]]), 1)), "sales_med": T("Compute transaction EV/LTM revenue for every deal and report the median, in turns to one decimal.", lambda d: cl(median([tx_ev(x) / x["rev"] for x in d["deals"]]), 1)), "max_eq": T("Report the largest equity value paid in the tape, that is the offer price multiplied by target diluted shares, in $ millions.", lambda d: cl(max([x["offer"] * x["sh"] for x in d["deals"]]), 0), "number", "abs:1"), "impl_offer": T("Apply the tape's median EV/LTM EBITDA to the subject company's LTM EBITDA, deduct its net debt and divide by its ""diluted shares; report the implied offer price per share, in dollars to two decimals.", lambda d: cl((median([tx_ev(x) / x["ebitda"] for x in d["deals"]]) * d["subj"]["ebitda"] - d["subj"]["nd"]) / d["subj"]["sh"], 2), "number", "abs:0.01"), "prem_high": T("Report the highest offer premium to the unaffected price in the tape, in percent to one decimal.", lambda d: cl(max([(x["offer"] / x["unaff"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "mult_one": T("Report the transaction EV/LTM EBITDA multiple for the third deal listed, in turns to one decimal.", lambda d: cl(tx_ev(d["deals"][2]) / d["deals"][2]["ebitda"], 1)), }
TX_EXTR = { "offer": T("Report the offer price per share for the fourth deal listed, in dollars.", lambda d: cl(d["deals"][3]["offer"], 2), "number", "abs:0.01"), "ebitda": T("What LTM EBITDA is shown for the second deal listed, in $ millions?", lambda d: cl(d["deals"][1]["ebitda"], 0), "number", "abs:0.01"), "date": T("State the announcement date of the first deal listed exactly as written.", lambda d: d["deals"][0]["date"], "text", "normalized"), "nd": T("What net debt is assumed in the fifth deal listed, in $ millions?", lambda d: cl(d["deals"][4]["nd"], 0), "number", "abs:0.01"), }
TX_QA = { "spread": T("What is the spread between the highest and the lowest transaction EV/LTM EBITDA in the tape, in turns to one decimal?", lambda d: cl(max([tx_ev(x) / x["ebitda"] for x in d["deals"]]) - min([tx_ev(x) / x["ebitda"] for x in d["deals"]]), 1)), "above8": T("What percentage of the deals were struck above 8.0 turns LTM EBITDA? Report in percent to one decimal.", lambda d: cl(100.0 * len([1 for x in d["deals"] if tx_ev(x) / x["ebitda"] > 8.0]) / len(d["deals"]), 1)), "vwap": T("Compute the median premium to the 30-day VWAP across the tape, in percent to one decimal.", lambda d: cl(median([(x["offer"] / x["vwap"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "syn_gain": T("For the deal with the highest EV/LTM EBITDA multiple, how many turns does the multiple fall once run-rate synergies are ""added to EBITDA? Report the fall in turns to one decimal.", lambda d: cl((lambda x: tx_ev(x) / x["ebitda"] - tx_ev(x) / (x["ebitda"] + x["syn"]))(max(d["deals"], key=lambda x: tx_ev(x) / x["ebitda"])), 1)), }
def build_tx(rng, book, idx):
    for _ in range(80):
        k = rng.choice([5, 6])
        deals, used = [], set()
        for j in range(k):
            tgt = ALLCO[rng.randrange(len(ALLCO))]
            sibs = [c for c in BY_SECTOR[tgt[1]] if c["name"] != tgt[0]]
            acq = sibs[rng.randrange(len(sibs))]
            if tgt[0] in used:
                break
            used.add(tgt[0])
            ebitda = float(rng.randrange(300, 2800, 10))
            nd = float(int(ebitda * rng.uniform(-0.4, 2.4)))
            sh = float(int(rng.uniform(60, 900)))
            offer = round((ebitda * rng.uniform(6.5, 11.0) - nd) / sh, 2)
            if offer < 4:
                break
            unaff = round(offer / (1.0 + rng.uniform(0.12, 0.48)), 2)
            deals.append({"date": MONTHS[rng.randrange(len(MONTHS))], "tgt": tgt[0], "acq": acq["name"], "offer": offer, "unaff": unaff, "vwap": round(unaff * rng.uniform(0.97, 1.06), 2), "sh": sh, "nd": nd, "ebitda": ebitda, "rev": float(int(ebitda * rng.uniform(2.4, 7.5))), "syn": float(int(ebitda * rng.uniform(0.02, 0.14)))})
        if len(deals) != k:
            continue
        subj = {"ebitda": float(rng.randrange(400, 2200, 10)), "nd": 0.0, "sh": float(int(rng.uniform(70, 800))), "px": round(rng.uniform(12.0, 90.0), 2)}
        subj["nd"] = float(int(subj["ebitda"] * rng.uniform(-0.3, 1.8)))
        ctx = "\n".join([UNITS, "", "Precedent transactions - mid-market control deals announced between 2023 and 2024. Transaction enterprise value ""equals the offer price multiplied by target diluted shares plus net debt assumed. Premiums are measured against ""the unaffected price one trading day before announcement.", "", table(TX_HDR, [[x["date"], x["tgt"], x["acq"], s2(x["offer"]), s2(x["unaff"]), s2(x["vwap"]), s0(x["sh"]), s0(x["nd"]), s0(x["ebitda"]), s0(x["rev"]), s0(x["syn"])] for x in deals]), "", "Subject company for the implied-offer test:", "| Item | Value |", "|---|---|", "| LTM EBITDA | %s |" % s0(subj["ebitda"]), "| Net debt | %s |" % s0(subj["nd"]), "| Diluted shares (m) | %s |" % s0(subj["sh"]), "| Share price ($) | %s |" % s2(subj["px"]), "", "Note: net debt assumed includes pension deficits and capitalised leases."])
        if not book.ok(ctx):
            continue
        return {"key": "tx%03d" % idx, "ctx": ctx, "d": {"deals": deals, "subj": subj}}
    return None
# --------------------------------------------------------- premium fixture ---
PREM_HDR = ["Date", "Target", "Acquirer", "Offer per share ($)", "Unaffected close ($)", "30-day VWAP ($)", "90-day VWAP ($)", "52-week high ($)"]
PREM_CALC = { "un": T("Compute the premium to the unaffected close for every deal and report the median, in percent to one decimal.", lambda d: cl(median([(x["offer"] / x["unaff"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "d30": T("Compute the premium to the one-month VWAP column for every deal and report the median, in percent to one decimal.", lambda d: cl(median([(x["offer"] / x["vwap30"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "d90": T("Compute the premium to the three-month VWAP column for every deal and report the median, in percent to one decimal.", lambda d: cl(median([(x["offer"] / x["vwap90"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "low52": T("Compute the premium to the 52-week high for every deal and report the lowest value, in percent to one decimal; a negative ""number means the offer sat below the 52-week high.", lambda d: cl(min([(x["offer"] / x["high"] - 1.0) * 100.0 for x in d["deals"]]), 1)), "rng": T("Report the difference between the highest and the lowest premium to the unaffected close in the tape, in percentage points ""to one decimal.", lambda d: cl((lambda p: max(p) - min(p))([(x["offer"] / x["unaff"] - 1.0) * 100.0 for x in d["deals"]]), 1)), }
PREM_EXTR = { "high": T("What 52-week high price is shown for the first deal listed, in dollars?", lambda d: cl(d["deals"][0]["high"], 2), "number", "abs:0.01"), "offer": T("What offer price per share is shown for the third deal listed, in dollars?", lambda d: cl(d["deals"][2]["offer"], 2), "number", "abs:0.01"), }
PREM_QA = { "bench": T("Which benchmark produces the smallest median premium across the tape: the unaffected close, the 30-day VWAP, the 90-day ""VWAP or the 52-week high? Answer with the benchmark name.", lambda d: (lambda v: ["unaffected close", "30-day VWAP", "90-day VWAP", "52-week high"][v.index(min(v))])( [median([(x["offer"] / x["unaff"] - 1.0) * 100.0 for x in d["deals"]]), median([(x["offer"] / x["vwap30"] - 1.0) * 100.0 for x in d["deals"]]), median([(x["offer"] / x["vwap90"] - 1.0) * 100.0 for x in d["deals"]]), median([(x["offer"] / x["high"] - 1.0) * 100.0 for x in d["deals"]])]), "label", "exact"), "above30": T("How many deals carry a premium to the unaffected close above 30 percent? Answer with a whole number.", lambda d: len([1 for x in d["deals"] if (x["offer"] / x["unaff"] - 1.0) * 100.0 > 30.0]), "number", "abs:0.01"), }
PREM_CLS = {"band": ("Classify the first deal's premium to the unaffected close using the set {below 20 percent, 20 to 35 percent, above 35 percent}.", lambda d: ("below 20 percent" if (d["deals"][0]["offer"] / d["deals"][0]["unaff"] - 1.0) * 100.0 < 20.0 else ("20 to 35 percent" if (d["deals"][0]["offer"] / d["deals"][0]["unaff"] - 1.0) * 100.0 <= 35.0 else "above 35 percent")))}
def build_prem(rng, book, idx):
    for _ in range(80):
        deals = []
        for j in range(5):
            tgt = ALLCO[rng.randrange(len(ALLCO))]
            sibs = [c for c in BY_SECTOR[tgt[1]] if c["name"] != tgt[0]]
            acq = sibs[rng.randrange(len(sibs))]
            base = round(rng.uniform(9.0, 120.0), 2)
            prem = ([0.12, 0.27, 0.42][idx % 3] + rng.uniform(-0.04, 0.04)) if j == 0 else rng.uniform(0.10, 0.55)
            offer = round(base * (1.0 + prem), 2)
            deals.append({"date": MONTHS[rng.randrange(len(MONTHS))], "tgt": tgt[0], "acq": acq["name"], "offer": offer, "unaff": base, "vwap30": round(base * rng.uniform(0.94, 1.03), 2), "vwap90": round(base * rng.uniform(0.86, 1.01), 2), "high": round(offer * rng.uniform(0.95, 1.30), 2)})
        if len(deals) != 5:
            continue
        ctx = "\n".join([UNITS, "", "Premium paid analysis - control offers announced between 2023 and 2024. All premiums are computed on the offer price ""per share against the stated benchmark for the same target.", "", table(PREM_HDR, [[x["date"], x["tgt"], x["acq"], s2(x["offer"]), s2(x["unaff"]), s2(x["vwap30"]), s2(x["vwap90"]), s2(x["high"])] for x in deals]), "", "Benchmarks are closing prices and volume-weighted averages for the target before the first report of the approach."])
        if not book.ok(ctx):
            continue
        return {"key": "prem%03d" % idx, "ctx": ctx, "d": {"deals": deals}}
    return None
# -------------------------------------------------------- exchange-ratio set ---
EXCH_HDR = ["Deal", "Acquirer", "Target", "Acquirer share price ($)", "Target unaffected price ($)", "Fixed exchange ratio", "Collar low ($)", "Collar high ($)", "Target shares (m)", "Acquirer shares outstanding (m)"]
EXCH_CALC = { "offer": T("For the first deal, compute the implied offer value per target share by applying the fixed exchange ratio to the acquirer ""share price, in dollars to two decimals.", lambda d: cl(d["rows"][0]["ratio"] * d["rows"][0]["apx"], 2), "number", "abs:0.01"), "shares": T("For the second deal, compute the number of new acquirer shares issued to target shareholders, in millions to two decimals.", lambda d: cl(d["rows"][1]["ratio"] * d["rows"][1]["tsh"], 2), "number", "abs:0.01"), "own": T("For the second deal, compute the target shareholders' pro forma ownership of the combined company, in percent to one decimal.", lambda d: cl(100.0 * d["rows"][1]["ratio"] * d["rows"][1]["tsh"] / (d["rows"][1]["ash"] + d["rows"][1]["ratio"] * d["rows"][1]["tsh"]), 1)), "collar": T("For the third deal, the acquirer trades at 93 percent of the collar low at closing. Applying the stated collar mechanic, what ""is the offer value per target share, in dollars to two decimals?", lambda d: cl(d["rows"][2]["lo"] * d["rows"][2]["ratio"], 2), "number", "abs:0.01"), "ratio6": T("For the fourth deal, what exchange ratio would be required to deliver an offer value 6 percent above the stated acquirer price, ""expressed in acquirer shares per target share to four decimals?", lambda d: cl(d["rows"][3]["ratio"] * 1.06, 4), "number", "abs:0.01"), }
EXCH_EXTR = { "hi": T("What collar high price is stated for the first deal, in dollars?", lambda d: cl(d["rows"][0]["hi"], 2), "number", "abs:0.01"), "ratio": T("What fixed exchange ratio is stated for the second deal, to four decimals?", lambda d: cl(d["rows"][1]["ratio"], 4), "number", "abs:0.01"), }
EXCH_QA = { "prem": T("For the second deal, what premium to the target unaffected price does the fixed exchange ratio imply at the stated acquirer share ""price, in percent to one decimal?", lambda d: cl((d["rows"][1]["ratio"] * d["rows"][1]["apx"] / d["rows"][1]["upx"] - 1.0) * 100.0, 1)), "inband": T("For the first deal, does the acquirer price sit inside the collar band? Answer with one of {inside, outside}.", lambda d: ("inside" if d["rows"][0]["lo"] <= d["rows"][0]["apx"] <= d["rows"][0]["hi"] else "outside"), "label", "exact"), }
def build_exch(rng, book, idx):
    for _ in range(80):
        rows = []
        for j in range(4):
            tgt = ALLCO[rng.randrange(len(ALLCO))]
            sibs = [c for c in BY_SECTOR[tgt[1]] if c["name"] != tgt[0]]
            acq = sibs[rng.randrange(len(sibs))]
            apx, upx = round(rng.uniform(18.0, 140.0), 2), round(rng.uniform(9.0, 80.0), 2)
            rows.append({"deal": "Deal %d" % (j + 1), "acq": acq["name"], "tgt": tgt[0], "apx": apx, "upx": upx, "ratio": round(upx * rng.uniform(0.85, 1.15) / apx, 4), "lo": round(apx * rng.uniform(0.80, 0.90), 2), "hi": round(apx * rng.uniform(1.10, 1.20), 2), "tsh": float(int(rng.uniform(40, 700))), "ash": float(int(rng.uniform(120, 2200)))})
        if len(rows) != 4:
            continue
        ctx = "\n".join([UNITS, "", "Stock-for-stock deal terms. The fixed exchange ratio is the number of acquirer shares issued per target share. Collar ""mechanic: while the acquirer share price at closing sits between the collar bounds the fixed ratio applies; below the ""collar low the ratio adjusts so that the offer value per target share equals the collar low price multiplied by the ""fixed ratio.", "", table(EXCH_HDR, [[x["deal"], x["acq"], x["tgt"], s2(x["apx"]), s2(x["upx"]), s4(x["ratio"]), s2(x["lo"]), s2(x["hi"]), s0(x["tsh"]), s0(x["ash"])] for x in rows]), "", "All deals are 100 percent stock consideration with no cash component."])
        if not book.ok(ctx):
            continue
        return {"key": "exch%03d" % idx, "ctx": ctx, "d": {"rows": rows}}
    return None
# ------------------------------------------------------------ implied range ---
def build_impl(rng, book, idx):
    for _ in range(80):
        members = BY_SECTOR[SECTORS[idx % len(SECTORS)]]
        tgt = members[(idx * 2) % len(members)]
        d = {"ebitda": float(rng.randrange(420, 2600, 10)), "sh": float(int(rng.uniform(70, 900))), "px": round(rng.uniform(11.0, 95.0), 2), "lo": round(rng.uniform(6.0, 8.5), 1), "name": tgt["name"]}
        d["nd"] = float(int(d["ebitda"] * rng.uniform(-0.2, 2.0)))
        d["hi"] = round(d["lo"] + rng.uniform(1.0, 2.6), 1)
        ctx = "\n".join([UNITS, "", "Valuation range for %s (%s). The selected multiple range is taken from the trading comparables of listed peers and ""applied to LTM EBITDA." % (d["name"], SECTORS[idx % len(SECTORS)]), "", "Subject metrics:", "| Item | Value |", "|---|---|", "| LTM EBITDA | %s |" % s0(d["ebitda"]), "| LTM EBIT | %s |" % s0(d["ebitda"] * 0.72), "| Net debt | %s |" % s0(d["nd"]), "| Diluted shares (m) | %s |" % s0(d["sh"]), "| Share price ($) | %s |" % s2(d["px"]), "", "Selected multiple range:", "| Metric | Low | High |", "|---|---|---|", "| EV/LTM EBITDA, turns | %s | %s |" % (s1(d["lo"]), s1(d["hi"])), "", "Net debt includes minority interest and the pension deficit."])
        if not book.ok(ctx):
            continue
        return {"key": "impl%03d" % idx, "ctx": ctx, "d": d}
    return None
IMPL_CALC = { "ev_low": T("Apply the low end of the selected EV/LTM EBITDA range to LTM EBITDA and report the implied enterprise value, in $ millions.", lambda d: cl(d["lo"] * d["ebitda"], 0), "number", "abs:1"), "ev_high": T("Apply the high end of the selected EV/LTM EBITDA range to LTM EBITDA and report the implied enterprise value, in $ millions.", lambda d: cl(d["hi"] * d["ebitda"], 0), "number", "abs:1"), "ps_low": T("Apply the low end of the multiple range, deduct net debt and divide by diluted shares; report the low-case implied value per ""share, in dollars to two decimals.", lambda d: cl((d["lo"] * d["ebitda"] - d["nd"]) / d["sh"], 2), "number", "abs:0.01"), "ps_high": T("Apply the high end of the multiple range, deduct net debt and divide by diluted shares; report the high-case implied value per ""share, in dollars to two decimals.", lambda d: cl((d["hi"] * d["ebitda"] - d["nd"]) / d["sh"], 2), "number", "abs:0.01"), "mid": T("Take the midpoint of the selected multiple range, deduct net debt and divide by diluted shares; report the midpoint implied value ""per share, in dollars to two decimals.", lambda d: cl((((d["lo"] + d["hi"]) / 2.0) * d["ebitda"] - d["nd"]) / d["sh"], 2), "number", "abs:0.01"), "upside": T("Using the midpoint of the implied value per share range, report the upside or downside to the stated share price, in percent to ""one decimal.", lambda d: cl((((((d["lo"] + d["hi"]) / 2.0) * d["ebitda"] - d["nd"]) / d["sh"]) / d["px"] - 1.0) * 100.0, 1)), "rev": T("Ignoring the selected range, compute the EV/LTM EBITDA multiple implied by the stated share price (market capitalisation plus net ""debt, divided by LTM EBITDA), in turns to one decimal.", lambda d: cl((d["px"] * d["sh"] + d["nd"]) / d["ebitda"], 1)), }
IMPL_EXTR = {"px": T("What share price is stated for the subject company, in dollars?", lambda d: cl(d["px"], 2), "number", "abs:0.01"), "nd": T("What net debt is stated for the subject company, in $ millions?", lambda d: cl(d["nd"], 0), "number", "abs:0.01")}
IMPL_QA = {"bind": T("Does the stated share price sit above or below the midpoint of the implied value range? Answer with one of {above, below}.", lambda d: ("below" if d["px"] < (((d["lo"] + d["hi"]) / 2.0) * d["ebitda"] - d["nd"]) / d["sh"] else "above"), "label", "exact"), "spread": T("Report the difference between the high-case and the low-case implied value per share, in dollars to two decimals.", lambda d: cl((d["hi"] - d["lo"]) * d["ebitda"] / d["sh"], 2), "number", "abs:0.01")}
# --------------------------------------------------------- quality fixtures ---
QUAL_HDR = ["Company", "Price ($)", "Diluted shares (m)", "Net debt", "Reported LTM EBITDA", "Non-recurring add-backs", "Capex", "D&A", "LTM net income"]
def qual_ev(x):
    return x["price"] * x["sh"] + x["nd"]
def build_qual(rng, book, idx):
    for _ in range(80):
        rows = []
        for c in rng.sample(BY_SECTOR[SECTORS[(idx + 2) % len(SECTORS)]], 4):
            ebitda = float(rng.randrange(300, 2400, 10))
            nd = float(int(ebitda * rng.uniform(0.2, 3.2)))
            sh = float(int(rng.uniform(60, 900)))
            eq = ebitda * rng.uniform(5.5, 10.0) - nd
            if eq <= 0:
                break
            rows.append({"name": c["name"], "price": round(eq / sh, 2), "sh": sh, "nd": nd, "ebitda": ebitda, "add": float(int(ebitda * rng.uniform(0.02, 0.40))), "capex": float(int(ebitda * rng.uniform(0.25, 0.80))), "da": float(int(ebitda * rng.uniform(0.25, 0.55))), "ni": float(int(ebitda * rng.uniform(0.05, 0.45)))})
        if len(rows) != 4:
            continue
        if idx % 2 == 0:
            rows[0]["add"] = float(int(rows[0]["ebitda"] * rng.uniform(0.30, 0.38)))
            for x in rows[1:]:
                x["add"] = min(float(int(x["ebitda"] * rng.uniform(0.02, 0.18))), rows[0]["add"] * 0.6)
        else:
            rows[0]["add"] = float(int(rows[0]["ebitda"] * rng.uniform(0.12, 0.20)))
            for x in rows[1:]:
                x["add"] = min(float(int(x["ebitda"] * rng.uniform(0.02, 0.09))), rows[0]["add"] * 0.6)
        rows[rng.randrange(4)]["ni"] = -abs(rows[0]["ni"]) - 1.0
        ctx = "\n".join([UNITS, "", "Peer screen assembled for a capital-intensive sector. Reported EBITDA is unadjusted; the add-back column shows costs ""the company itself treats as non-recurring. Capex is shown because EBITDA ignores the investment needed to sustain the ""asset base.", "", table(QUAL_HDR, [[x["name"], s2(x["price"]), s0(x["sh"]), s0(x["nd"]), s0(x["ebitda"]), s0(x["add"]), s0(x["capex"]), s0(x["da"]), s0(x["ni"])] for x in rows]), "", "Footnotes:", "1. Reported EBITDA is stated after charging the add-back items; adjusted EBITDA adds them back.", "2. One peer reports negative LTM net income, so its price to earnings ratio is not meaningful."])
        if not book.ok(ctx):
            continue
        return {"key": "qual%03d" % idx, "ctx": ctx, "d": {"rows": rows}}
    return None
QUAL_CALC = { "adj": T("For the peer with the largest non-recurring add-back, compute adjusted EV/LTM EBITDA using adjusted EBITDA, in turns to one decimal.", lambda d: cl(qual_ev(max(d["rows"], key=lambda x: x["add"])) / (max(d["rows"], key=lambda x: x["add"])["ebitda"] + max(d["rows"], key=lambda x: x["add"])["add"]), 1)), "gap": T("For the peer with the largest non-recurring add-back, report reported EV/LTM EBITDA minus adjusted EV/LTM EBITDA, in turns to one decimal.", lambda d: cl(qual_ev(max(d["rows"], key=lambda x: x["add"])) / max(d["rows"], key=lambda x: x["add"])["ebitda"] - qual_ev(max(d["rows"], key=lambda x: x["add"])) / (max(d["rows"], key=lambda x: x["add"])["ebitda"] + max(d["rows"], key=lambda x: x["add"])["add"]), 1)), "pe": T("For the peer with negative LTM net income, compute the price to LTM earnings ratio. Answer with the word negative if the ratio is ""not meaningful.", lambda d: "negative", "text", "normalized"), "pe_num": T("For the first peer listed, compute the price to LTM earnings ratio, in turns to one decimal.", lambda d: cl(d["rows"][0]["price"] * d["rows"][0]["sh"] / d["rows"][0]["ni"], 1) if d["rows"][0]["ni"] > 0 else "negative", "number", "abs:0.1"), "ebit": T("For the peer with the highest capex to EBITDA ratio, compute EV/LTM EBIT as EBITDA less D&A, in turns to one decimal.", lambda d: cl(qual_ev(max(d["rows"], key=lambda x: x["capex"] / x["ebitda"])) / (max(d["rows"], key=lambda x: x["capex"] / x["ebitda"])["ebitda"] - max(d["rows"], key=lambda x: x["capex"] / x["ebitda"])["da"]), 1)), "addshare": T("For the peer with the largest non-recurring add-back, report the add-back as a percentage of reported LTM EBITDA, in percent ""to one decimal.", lambda d: cl(100.0 * max(d["rows"], key=lambda x: x["add"])["add"] / max(d["rows"], key=lambda x: x["add"])["ebitda"], 1)), }
QUAL_EXTR = {"add": T("What non-recurring add-back is shown for the third peer listed, in $ millions?", lambda d: cl(d["rows"][2]["add"], 0), "number", "abs:0.01")}
QUAL_QA = { "neg": T("Which multiple should be used for the peer with negative LTM earnings? Answer with one of {price to earnings, EV/Sales}.", lambda d: "EV/Sales", "label", "exact"), "capex": T("For the peer with the highest capex to EBITDA ratio, is EV/EBITDA flattering relative to EV/EBIT because depreciation is a large ""share of EBITDA? Answer with one of {yes, no}.", lambda d: "yes" if max(d["rows"], key=lambda x: x["capex"] / x["ebitda"])["da"] / max(d["rows"], key=lambda x: x["capex"] / x["ebitda"])["ebitda"] > 0.3 else "no", "label", "exact"), "best": T("Which multiple is the better primary benchmark for the peer set here: EV/EBITDA or EV/EBIT? Answer with one of {EV/EBITDA, EV/EBIT}.", lambda d: "EV/EBIT", "label", "exact"), }
QUAL_CLS = {"distort": ("Classify the reliability of the largest-add-back peer's reported EV/LTM EBITDA using the set {usable, distorted}; treat ""add-backs above 25 percent of reported EBITDA as distorted.", lambda d: "distorted" if max(d["rows"], key=lambda x: x["add"])["add"] / max(d["rows"], key=lambda x: x["add"])["ebitda"] > 0.25 else "usable")}
# ------------------------------------------------------------- fx unit trap ---
FX_HDR = ["Company", "Country", "Reporting currency", "Share price (local)", "Diluted shares (m)", "Net debt (local m)", "LTM EBITDA (local m)", "FX rate to USD"]
FX_CTY = [("Norway", "NOK"), ("Sweden", "SEK"), ("Denmark", "DKK"), ("Switzerland", "CHF"), ("Canada", "CAD"), ("Australia", "AUD")]
FX_UNITS = "Units: local currency in millions except per-share amounts in local currency units; the FX rate is USD per one unit of local currency."
def build_fx(rng, book, idx):
    for _ in range(80):
        cty = FX_CTY[idx % len(FX_CTY)]
        rows = []
        for j in range(4):
            c = ALLCO[rng.randrange(len(ALLCO))]
            ebitda = float(rng.randrange(300, 2400, 10))
            nd = float(int(ebitda * rng.uniform(-0.2, 2.4)))
            sh = float(int(rng.uniform(60, 900)))
            eq = ebitda * rng.uniform(6.0, 10.0) - nd
            if eq <= 0:
                break
            rows.append({"name": c[0], "ccy": cty[1], "px": round(eq / sh, 2), "sh": sh, "nd": nd, "ebitda": ebitda, "rate": round(rng.uniform(0.07, 1.45), 4)})
        if len(rows) != 4:
            continue
        ctx = "\n".join([FX_UNITS, "", "Cross-border peer set. Every figure in the table is in the reporting currency stated for that company; the FX rate ""converts one unit of the local currency into USD. Multiples are currency-neutral.", "", table(FX_HDR, [[x["name"], cty[0], x["ccy"], s2(x["px"]), s0(x["sh"]), s0(x["nd"]), s0(x["ebitda"]), s4(x["rate"])] for x in rows]), "", "Note: the fourth peer reports in a different currency from the first three."])
        if not book.ok(ctx):
            continue
        return {"key": "fx%03d" % idx, "ctx": ctx, "d": {"rows": rows, "cty": cty[0]}}
    return None
FX_CALC = { "ebitda_usd": T("Convert the second peer's LTM EBITDA into USD at its stated FX rate and report the result, in $ millions.", lambda d: cl(d["rows"][1]["ebitda"] * d["rows"][1]["rate"], 0), "number", "abs:1"), "ev_usd": T("Compute the first peer's enterprise value in its local currency, convert it into USD at the stated FX rate and report it in $ millions.", lambda d: cl((d["rows"][0]["px"] * d["rows"][0]["sh"] + d["rows"][0]["nd"]) * d["rows"][0]["rate"], 0), "number", "abs:1"), "mult_med": T("Compute EV/LTM EBITDA for every peer in local currency and report the peer median, in turns to one decimal.", lambda d: cl(median([(x["px"] * x["sh"] + x["nd"]) / x["ebitda"] for x in d["rows"]]), 1)), "rate": T("Report the FX rate shown for the fourth peer, in USD per unit of local currency to four decimals.", lambda d: cl(d["rows"][3]["rate"], 4), "number", "abs:0.01"), }
FX_EXTR = {"ebitda": T("What LTM EBITDA is shown for the third peer, in local currency millions?", lambda d: cl(d["rows"][2]["ebitda"], 0), "number", "abs:0.01"), "ccy": T("What reporting currency is shown for the second peer? Answer with the three-letter code.", lambda d: d["rows"][1]["ccy"], "text", "normalized")}
FX_QA = { "invariant": T("If every local-currency figure were converted into USD at the stated rates before computing multiples, would the peer median ""EV/LTM EBITDA change? Answer with one of {yes, no}.", lambda d: "no", "label", "exact"), "currency": T("Which peer reports in a currency different from the first three? Answer with the company name exactly as written.", lambda d: d["rows"][3]["name"], "label", "exact"), }
# --------------------------------------------------------------- memo pack ---
def build_memo(rng, book, idx):
    for _ in range(80):
        v = idx % 5
        tgt = ALLCO[rng.randrange(len(ALLCO))]
        sibs = [c for c in BY_SECTOR[tgt[1]] if c["name"] != tgt[0]]
        acq = sibs[rng.randrange(len(sibs))]
        date = MONTHS[rng.randrange(len(MONTHS))]
        ebitda = float(rng.randrange(320, 2600, 10))
        nd = float(int(ebitda * rng.uniform(-0.3, 2.2)))
        sh = float(int(rng.uniform(60, 800)))
        ev = ebitda * rng.uniform(7.0, 11.5)
        offer = round((ev - nd) / sh, 2)
        if offer < 4:
            continue
        key = "memo%03d" % idx
        mult = ev / ebitda
        prem = rng.uniform(0.16, 0.46)
        unaff = round(offer / (1.0 + prem), 2)
        syn = float(int(ebitda * rng.uniform(0.03, 0.12)))
        pm = round(mult * rng.uniform(0.82, 1.18), 1)
        pmean = round(pm * rng.uniform(1.05, 1.30), 1)
        lo = round(mult * rng.uniform(0.85, 0.95), 1)
        hi = round(lo + rng.uniform(1.0, 2.0), 1)
        rows = []
        if v == 0:
            ctx = "\n".join([UNITS, "", "Memo: announcement summary for the board of %s, prepared %s." % (tgt[0], date), "", "Transaction terms", "| Item | Value |", "|---|---|", "| Acquirer | %s |" % acq["name"], "| Consideration | cash |", "| Offer per share ($) | %s |" % s2(offer), "| Unaffected close one day prior ($) | %s |" % s2(unaff), "| Premium to unaffected close, percent | %s |" % s1(prem * 100.0), "| Target diluted shares (m) | %s |" % s0(sh), "| Equity value | %s |" % s0(ev - nd), "| Net debt assumed | %s |" % s0(nd), "| Enterprise value | %s |" % s0(ev), "| LTM EBITDA | %s |" % s0(ebitda), "| EV/LTM EBITDA, turns | %s |" % s1(mult), "| Run-rate synergies | %s |" % s0(syn), "", "Financing is a fully committed term loan plus balance sheet cash. The board memo flags the premium as within the ""range paid in the sector over the prior three years."])
            rows.append(row("summarization", "s_deal", ctx, "Summarize the offer, the premium paid and the transaction multiple in two sentences, using only figures stated in the memo.", "The offer is %s per share in cash, a premium of %s percent to the unaffected close of %s, and it values the target at ""an EV/LTM EBITDA multiple of %s turns." % (s2(offer), s1(prem * 100.0), s2(unaff), s1(mult)), "text", "normalized", key))
            rows.append(row("extraction", "x_memo_ev", ctx, "Report the enterprise value stated in the memo, in $ millions.", cl(ev, 0), "number", "abs:0.01", key))
            rows.append(row("qa", "q_memo_syn", ctx, "Using the memo, compute EV/(LTM EBITDA plus run-rate synergies), in turns to one decimal.", cl(ev / (ebitda + syn), 1), "number", "abs:0.1", key))
        elif v == 1:
            ctx = "\n".join([UNITS, "", "Screen note: %s against its listed peer set, prepared %s." % (tgt[0], date), "", "| Item | Value |", "|---|---|", "| Target EV/LTM EBITDA, turns | %s |" % s1(mult), "| Peer median EV/LTM EBITDA, turns | %s |" % s1(pm), "| Peer mean EV/LTM EBITDA, turns | %s |" % s1(pmean), "| Target LTM EBITDA | %s |" % s0(ebitda), "| Target net debt | %s |" % s0(nd), "| Target diluted shares (m) | %s |" % s0(sh), "| Target share price ($) | %s |" % s2(offer), "", "The note observes that one peer trades on a multiple well above the rest of the set and that the median is the more ""representative benchmark for this sector."])
            rows.append(row("summarization", "s_screen", ctx, "Summarize what the screen says about how the target is valued against its peers in two sentences, quoting the target and ""peer median multiples.", "The target trades at %s turns EV/LTM EBITDA against a peer median of %s turns, and the note treats the median rather than ""the mean as the representative benchmark because one peer is an outlier." % (s1(mult), s1(pm)), "text", "normalized", key))
            rows.append(row("extraction", "x_memo_price", ctx, "What target share price is stated in the screen note, in dollars?", cl(offer, 2), "number", "abs:0.01", key))
            rows.append(row("qa", "q_memo_gap", ctx, "How many turns separate the peer mean from the peer median in the screen note, to one decimal?", cl(pmean - pm, 1), "number", "abs:0.1", key))
        elif v == 2:
            ctx = "\n".join([UNITS, "", "Fairness memo: implied valuation range for %s, prepared %s. The range applies selected EV/LTM EBITDA multiples from ""precedent transactions to LTM EBITDA." % (tgt[0], date), "", "| Item | Value |", "|---|---|", "| LTM EBITDA | %s |" % s0(ebitda), "| Net debt | %s |" % s0(nd), "| Diluted shares (m) | %s |" % s0(sh), "| Share price ($) | %s |" % s2(offer), "| Multiple low, turns | %s |" % s1(lo), "| Multiple high, turns | %s |" % s1(hi), "", "The committee is asked to note that the high end of the range sits well above the stated share price."])
            rows.append(row("summarization", "s_range", ctx, "Summarize the valuation range and the committee's observation about the share price in two sentences, using only figures ""stated in the memo.", "The memo applies an EV/LTM EBITDA range of %s to %s turns to LTM EBITDA of %s, and it notes that the high end of the range ""sits well above the stated share price of %s." % (s1(lo), s1(hi), s0(ebitda), s2(offer)), "text", "normalized", key))
            rows.append(row("extraction", "x_memo_shares", ctx, "Report the diluted share count stated in the fairness memo, in millions.", cl(sh, 0), "number", "abs:0.01", key))
            rows.append(row("qa", "q_memo_range_hi", ctx, "Using the stated multiple range, compute the high end of the implied equity value range, in $ millions.", cl(hi * ebitda - nd, 0), "number", "abs:1", key))
        elif v == 3:
            deals, prems, mults = [], [], []
            for j in range(5):
                b = round(rng.uniform(9.0, 120.0), 2)
                p = [0.18, 0.26, 0.34, 0.30, 0.44][j] + rng.uniform(-0.02, 0.02)
                o = round(b * (1.0 + p), 2)
                m = round(rng.uniform(6.5, 11.0), 1)
                prems.append(p * 100.0)
                mults.append(m)
                deals.append([MONTHS[rng.randrange(len(MONTHS))], ALLCO[rng.randrange(len(ALLCO))][0], acq["name"], s2(o), s2(b), s1(p * 100.0), s1(m)])
            mp, mm = median(prems), median(mults)
            ctx = "\n".join([UNITS, "", "Premium tape for the %s process, prepared %s. Premiums are measured against the unaffected close one trading day ""before announcement." % (tgt[0], date), "", table(["Date", "Target", "Acquirer", "Offer per share ($)", "Unaffected close ($)", "Premium (percent)", "EV/LTM EBITDA (turns)"], deals), "", "Tape summary: median premium %s percent; median EV/LTM EBITDA %s turns; five deals in the tape." % (s1(mp), s1(mm))])
            rows.append(row("summarization", "s_prem_tape", ctx, "Summarize the premium tape in two sentences, quoting the median premium and the median transaction multiple.", "The five offers carried a median premium of %s percent to the unaffected close, at a median of %s turns EV/LTM EBITDA." % (s1(mp), s1(mm)), "text", "normalized", key))
            rows.append(row("extraction", "x_tape_prem", ctx, "What premium is shown for the third deal listed, in percent?", cl(prems[2], 1), "number", "abs:0.01", key))
            rows.append(row("qa", "q_tape_above30", ctx, "How many deals in the tape carry a premium above 30 percent? Answer with a whole number.", len([1 for p in prems if p > 30.0]), "number", "abs:0.01", key))
        else:
            mults = sorted([round(rng.uniform(6.0, 12.5), 1) for _ in range(5)])
            subj_m = round(rng.uniform(6.0, 12.5), 1)
            mn, md, mx = mults[0], median(mults), mults[-1]
            ctx = "\n".join([UNITS, "", "Peer multiple summary for %s, prepared %s. Multiples are EV/LTM EBITDA on the latest reported period." % (tgt[0], date), "", table(["Peer", "EV/LTM EBITDA (turns)"], [[ALLCO[i][0], s1(mults[i])] for i in range(5)]), "", "Range summary: minimum %s turns; median %s turns; maximum %s turns. Subject company EV/LTM EBITDA: %s turns." % ( s1(mn), s1(md), s1(mx), s1(subj_m))])
            rows.append(row("summarization", "s_peer_range", ctx, "Summarize the peer range and where the subject sits within it in two sentences, quoting the minimum, median and maximum.", "The peer set trades between %s and %s turns EV/LTM EBITDA with a median of %s turns, and the subject at %s turns sits %s ""that median." % (s1(mn), s1(mx), s1(md), s1(subj_m), "above" if subj_m > md else "below"), "text", "normalized", key))
            rows.append(row("extraction", "x_range_med", ctx, "What median EV/LTM EBITDA is stated in the range summary, in turns to one decimal?", cl(md, 1), "number", "abs:0.01", key))
            rows.append(row("qa", "q_range_pos", ctx, "Does the subject multiple sit above or below the peer median? Answer with one of {above, below}.", "above" if subj_m > md else "below", "label", "exact", key))
        if not book.ok(ctx):
            continue
        return {"key": key, "rows": rows}
    return None
# ------------------------------------------------------------- tool fixtures ---
TOOLS_PEER = [ {"name": "get_peer_multiples", "description": "Return the trading multiple set for a sector peer group as of a stated date.", "parameters": {"type": "object", "properties": {"sector": {"type": "string", "description": "Sector label of the peer group."}, "metric": {"type": "string", "enum": ["EV/EBITDA", "EV/EBIT", "P/E", "EV/Sales"]}, "as_of": {"type": "string", "description": "Snapshot date, ISO format."}}, "required": ["sector", "metric", "as_of"]}}, {"name": "get_capital_structure", "description": "Return debt, cash, minorities, preferred stock and pension deficit for a company.", "parameters": {"type": "object", "properties": {"company": {"type": "string"}, "as_of": {"type": "string"}}, "required": ["company", "as_of"]}}, {"name": "get_transaction_tape", "description": "Return announced precedent transactions with offer prices, premiums and EBITDA.", "parameters": {"type": "object", "properties": {"sector": {"type": "string"}, "since_year": {"type": "integer"}}, "required": ["sector"]}}, ]
def peer_payload(rng, sector):
    for _ in range(40):
        rows = []
        for c in rng.sample(BY_SECTOR[sector], 4):
            m = mk_ind(rng)
            if m is None:
                rows = []
                break
            rows.append({"company": c["name"], "price": m["price"], "diluted_shares_m": m["shares"], "total_debt": m["debt"], "cash": m["cash"], "minorities": m["mi"], "preferred": m["pref"], "pension_deficit": m["pen"], "ltm_ebitda": m["ebitda"], "ltm_ebit": m["ebit"], "ltm_net_income": m["ni"], "ltm_revenue": m["rev"]})
        if len(rows) == 4:
            return rows
    return None
def tool_row(idx, fam, msgs, gt, at="text", tol="normalized"):
    return {"task": "tool_use", "fam": fam, "msgs": msgs, "tools": TOOLS_PEER, "gt": gt, "at": at, "tol": tol, "fx": "tool%03d" % idx}
def build_tool(rng, idx):
    sector = [s for s in SECTORS if s != "Regional Banks"][idx % 4]
    rows = peer_payload(rng, sector)
    if rows is None:
        return []
    mults = [(r["price"] * r["diluted_shares_m"] + r["total_debt"] - r["cash"] + r["minorities"] + r["preferred"] + r["pension_deficit"]) / r["ltm_ebitda"] for r in rows]
    body = json.dumps({"sector": sector, "as_of": "2025-06-30", "currency": "USD millions", "rows": rows})
    med = median(mults)
    kind = idx % 5
    sys_ = {"role": "system", "content": "You are supporting a comparable-company valuation. All figures returned by tools are in USD millions ""except per-share prices."}
    if kind == 0:
        msgs = [sys_, {"role": "user", "content": "Pull the peer multiples for the sector and tell me the median EV/EBITDA."}, {"role": "assistant", "content": "I will call get_peer_multiples for the sector snapshot, then compute the median from the returned rows."}, {"role": "tool", "content": body}, {"role": "user", "content": "Now use that median to value a target with LTM EBITDA of 1450 and net debt of 2200; give me the implied ""equity value in USD millions."}]
        return [tool_row(idx, "t_median_apply", msgs, s0(med * 1450.0 - 2200.0))]
    if kind == 1:
        msgs = [{"role": "system", "content": "You are checking a peer screen before it goes to an investment committee."}, {"role": "user", "content": "I have a peer screen to work through; start by pulling the multiple set."}, {"role": "assistant", "content": "I will call get_peer_multiples with the metric set to EV/EBITDA for this sector and snapshot date."}, {"role": "tool", "content": body}, {"role": "user", "content": "How many of those peers trade above 9.0 turns? Answer with a whole number."}]
        return [tool_row(idx, "t_screen", msgs, "%d" % len([m for m in mults if m > 9.0]))]
    if kind == 2:
        err = json.dumps({"error": "unknown metric", "received": "EV/EBITDAA", "allowed": ["EV/EBITDA", "EV/EBIT", "P/E", "EV/Sales"]})
        msgs = [{"role": "system", "content": "You are resolving a failed tool call in a comps workflow. Retry with a valid argument rather than guessing."}, {"role": "user", "content": "Get me the EV/EBITDA set for the peer group, then I will ask for the median."}, {"role": "assistant", "content": "I will call get_peer_multiples with metric EV/EBITDAA for the sector."}, {"role": "tool", "content": err}, {"role": "assistant", "content": "The metric argument was rejected. I will retry with the allowed value EV/EBITDA."}, {"role": "tool", "content": body}, {"role": "user", "content": "Good. Now give me the peer median EV/EBITDA to one decimal."}]
        return [tool_row(idx, "t_wrongarg", msgs, s1(med))]
    if kind == 3:
        brows = []
        for _ in range(40):
            brows = []
            for c in rng.sample(BY_SECTOR["Regional Banks"], 4):
                m = mk_bank(rng)
                if m is None:
                    brows = []
                    break
                brows.append({"company": c["name"], "price": m["price"], "diluted_shares_m": m["shares"], "book_equity": m["book"], "tangible_book_equity": m["tbv"], "ltm_net_income": m["ni"], "cet1_percent": m["cet1"]})
            if len(brows) == 4:
                break
        if len(brows) != 4:
            return []
        bpay = {"sector": "Regional Banks", "as_of": "2025-06-30", "note": "EBITDA is not reported for banks; interest expense is an operating cost.", "rows": brows}
        msgs = [{"role": "system", "content": "You are screening banks. The peer tool may return a note instead of EBITDA for regulated lenders."}, {"role": "user", "content": "Screen the regional banks peer set on the usual multiples and tell me the median EV/EBITDA."}, {"role": "assistant", "content": "I will call get_peer_multiples for Regional Banks with metric EV/EBITDA."}, {"role": "tool", "content": json.dumps(bpay)}, {"role": "user", "content": "Right, use price to tangible book value instead. What is the peer median, to one decimal?"}]
        return [tool_row(idx, "t_bank", msgs, s1(median([r["price"] * r["diluted_shares_m"] / r["tangible_book_equity"] for r in brows])))]
    msgs = [{"role": "system", "content": "You are testing whether a peer median is robust before using it in a valuation."}, {"role": "user", "content": "Run the peer screen and flag whether any multiple is an outlier."}, {"role": "assistant", "content": "I will call get_peer_multiples and inspect the distribution of EV/EBITDA."}, {"role": "tool", "content": body}, {"role": "user", "content": "Exclude the highest multiple and give me the median of the rest, to one decimal."}]
    rest = [m for m in mults if m != max(mults)]
    return [tool_row(idx, "t_outlier", msgs, s1(median(rest)))]
# ----------------------------------------------------------- knowledge bank ---
KNOW = [ ("How is an unfunded defined-benefit pension deficit treated in an enterprise value bridge?", "It is added to enterprise value as a debt-like claim, so equity value falls by the same amount.", "text"), ("Which measure of central tendency is more robust to a single outlier multiple, the mean or the median?", "median", "label"), ("When a peer's fiscal year ends in March and the valuation date is 31 December, what weight applies to the fiscal year that ended in March ""of the valuation year?", 0.75, "number"), ("Why is EV/EBITDA usually preferred to P/E when comparing companies with different capital structures?", "EV/EBITDA is struck before interest, so it is unaffected by leverage and by differences in tax jurisdictions.", "text"), ("What does the control premium in a precedent transaction measure?", "The excess of the offer price over the target's unaffected share price before the approach.", "text"), ("How is the exchange ratio in a stock-for-stock merger normally set?", "Offer value per target share divided by the acquirer's share price.", "text"), ("If a company reports negative LTM earnings, which multiple remains usable, P/E or EV/Sales?", "EV/Sales", "label"), ("What does a negative enterprise value imply about a company's net cash position?", "Cash and other non-operating assets exceed the market value of equity plus debt.", "text"), ("How are minority interests treated when computing enterprise value from market capitalisation?", "They are added, because the consolidated EBITDA includes the minority-owned share of profits.", "text"), ("What is the difference between a trading multiple and a transaction multiple?", "A trading multiple reflects the price of a minority stake in the public market; a transaction multiple embeds control and synergies.", "text"), ("Why can a cyclical company at trough earnings show a misleadingly high EV/EBITDA?", "Because the denominator is depressed, so the multiple overstates the price paid for normalised earnings.", "text"), ("Why is EV/EBITDA a weak measure for a business with very heavy capital expenditure?", "EBITDA ignores the capex needed to sustain the asset base, so it flatters cash generation.", "text"), ("What is the usual remedy for a peer set whose multiples are distorted by one outlier?", "Use the median or a trimmed mean rather than the simple mean.", "text"), ("How does a collar on a fixed exchange ratio protect the target's shareholders?", "It adjusts the ratio or the consideration when the acquirer's price moves outside a stated band.", "text"), ("What does the 52-week high benchmark in a premium paid analysis usually show?", "The premium can be negative, because an offer may sit below the target's high of the past year.", "text"), ("Why is price to tangible book value used for banks rather than EV/EBITDA?", "Interest expense is an operating cost for a bank, so EBITDA is not a meaningful measure of earnings.", "text"), ("What is the effect of calendarising an off-year-end peer's EBITDA before computing a multiple?", "It aligns the denominator with the valuation date, so the multiple is comparable across peers.", "text"), ("If a peer reports in a foreign currency, does converting its figures to the acquirer's currency change its EV/EBITDA multiple?", "No, because the numerator and the denominator convert at the same rate.", "text"), ("What is the standard treatment of preferred stock in an enterprise value bridge?", "It is added to enterprise value as a claim ranking ahead of common equity.", "text"), ("What does a trimmed mean of peer multiples do that a simple mean does not?", "It removes the extreme observations before averaging, so a single outlier cannot dominate.", "text"), ("Why must the subject company be excluded from the peer median in a comparable company analysis?", "Including it would make the benchmark partly a function of the valuation it is meant to test.", "text"), ("What is the implied multiple approach in a precedent transaction analysis?", "Applying the median transaction multiple to the subject's metric to derive an implied value.", "text"), ("Which is normally higher for the same target, the trading multiple or the transaction multiple?", "transaction multiple", "label"), ("How should a one-off restructuring charge inside reported EBITDA be handled before computing a multiple?", "Add it back if it is genuinely non-recurring, and disclose the adjustment.", "text"), ("What does the enterprise value to sales multiple allow an analyst to do when earnings are negative?", "Value the business on revenue, which stays positive when earnings do not.", "text"), ]
def knowledge_rows():
    out = []
    for k, (q, gt, at) in enumerate(KNOW):
        fam = "z_know%d" % (k % 5)
        if at == "number":
            out.append(row("qa", fam, "", q, gt, "number", "abs:0.01", "know%03d" % k))
        elif at == "label":
            out.append(row("qa", fam, "", q, gt, "label", "exact", "know%03d" % k))
        else:
            out.append(row("qa", fam, "", q, gt, "text", "normalized", "know%03d" % k))
    return out
# -------------------------------------------------------------- emission ------
def emit(fx, spec, n, nc, ne, nq):
    out = []
    ck = sorted(spec["calc"])
    for k in range(nc):
        key = ck[(n * 3 + k) % len(ck)]
        q, fn, at, tol = spec["calc"][key]
        out.append(row("calc", "c_" + key, fx["ctx"], q, fn(fx["d"]), at, tol, fx["key"]))
    ek = sorted(spec["extr"])
    for k in range(ne):
        key = ek[(n * 2 + k) % len(ek)]
        q, fn, at, tol = spec["extr"][key]
        out.append(row("extraction", "x_" + key, fx["ctx"], q, fn(fx["d"]), at, tol, fx["key"]))
    qk = sorted(spec["qa"])
    for k in range(nq):
        key = qk[(n * 2 + k) % len(qk)]
        q, fn, at, tol = spec["qa"][key]
        out.append(row("qa", "q_" + key, fx["ctx"], q, fn(fx["d"]), at, tol, fx["key"]))
    for key in sorted(spec.get("cls", {})):
        q, fn = spec["cls"][key]
        out.append(row("classification", "k_" + key, fx["ctx"], q, fn(fx["d"]), "label", "exact", fx["key"]))
    return out
SPECS = { "peer": {"calc": PEER_CALC, "extr": PEER_EXTR, "qa": PEER_QA, "cls": PEER_CLS}, "bank": {"calc": BANK_CALC, "extr": BANK_EXTR, "qa": BANK_QA, "cls": BANK_CLS}, "cal": {"calc": CAL_CALC, "extr": CAL_EXTR, "qa": CAL_QA}, "tx": {"calc": TX_CALC, "extr": TX_EXTR, "qa": TX_QA}, "prem": {"calc": PREM_CALC, "extr": PREM_EXTR, "qa": PREM_QA, "cls": PREM_CLS}, "exch": {"calc": EXCH_CALC, "extr": EXCH_EXTR, "qa": EXCH_QA}, "impl": {"calc": IMPL_CALC, "extr": IMPL_EXTR, "qa": IMPL_QA}, "qual": {"calc": QUAL_CALC, "extr": QUAL_EXTR, "qa": QUAL_QA, "cls": QUAL_CLS}, "fx": {"calc": FX_CALC, "extr": FX_EXTR, "qa": FX_QA}, }
def build_all():
    pool = []
    plan = [("peer", build_peer, 56, 3, 2, 2), ("bank", build_bank, 21, 1, 1, 1), ("cal", build_cal, 22, 2, 1, 1), ("tx", build_tx, 30, 2, 2, 2), ("prem", build_prem, 27, 2, 1, 1), ("exch", build_exch, 14, 2, 1, 1), ("impl", build_impl, 20, 2, 1, 1), ("qual", build_qual, 20, 2, 1, 1), ("fx", build_fx, 12, 2, 1, 1)]
    for kind, fn, count, nc, ne, nq in plan:
        book = Book()
        made, i = 0, 0
        while made < count and i < 400:
            fx = fn(RNG, book, i)
            if fx:
                pool.extend(emit(fx, SPECS[kind], made, nc, ne, nq))
                made += 1
            i += 1
    for v in range(5):
        book = Book()
        made, i = 0, 0
        while made < 20 and i < 400:
            fx = build_memo(RNG, book, i * 5 + v)
            if fx:
                pool.extend(fx["rows"])
                made += 1
            i += 1
    for k in range(100):
        pool.extend(build_tool(RNG, k))
    pool.extend(knowledge_rows())
    return pool
def pick(cands, need, cap=40):
    by_fam = defaultdict(list)
    for c in cands:
        by_fam[c["fam"]].append(c)
    for f in by_fam:
        by_fam[f].sort(key=lambda r: hashlib.sha256((r["fx"] + "|" + f + "|" + (r.get("q") or "")[:30]).encode("utf-8")).hexdigest())
    fams = sorted(by_fam, key=lambda f: hashlib.sha256(f.encode("utf-8")).hexdigest())
    out, used = [], Counter()
    while len(out) < need:
        moved = False
        for f in fams:
            if len(out) >= need:
                break
            if not by_fam[f] or used[f] >= cap:
                continue
            out.append(by_fam[f].pop(0))
            used[f] += 1
            moved = True
        if not moved:
            break
    return out
def pick_cls(cands, need):
    by_fam = defaultdict(list)
    for c in cands:
        by_fam[c["fam"]].append(c)
    fams = sorted(by_fam)
    per = need // len(fams)
    out = []
    for f in fams:
        by_lab = defaultdict(list)
        for c in by_fam[f]:
            by_lab[c["gt"]].append(c)
        labs = sorted(by_lab)
        base, rem = per // len(labs), per % len(labs)
        for i, l in enumerate(labs):
            take = base + (1 if i < rem else 0)
            rows = sorted(by_lab[l], key=lambda r: hashlib.sha256((r["fx"] + "|" + r["fam"]).encode("utf-8")).hexdigest())
            out.extend(rows[:take])
    if len(out) < need:
        seen = set(id(x) for x in out)
        rest = sorted([c for c in cands if id(c) not in seen], key=lambda r: hashlib.sha256((r["fx"] + "|" + r["fam"]).encode("utf-8")).hexdigest())
        out.extend(rest[:need - len(out)])
    return out[:need]
def assign_splits(rows):
    for task in QUOTA:
        rs = [r for r in rows if r["task"] == task]
        n = len(rs)
        n_tr, n_va = int(round(0.8 * n)), int(round(0.1 * n))
        groups = defaultdict(list)
        for r in rs:
            groups[r["fx"]].append(r)
        keys = sorted(groups, key=lambda k: hashlib.sha256((task + "|" + k).encode("utf-8")).hexdigest())
        flat = []
        for k in keys:
            flat.extend(groups[k])
        for i, r in enumerate(flat):
            r["split"] = "train" if i < n_tr else ("val" if i < n_tr + n_va else "test")
def self_check(rows):
    ok = len(rows) == 1000 and all(sum(1 for r in rows if r["task"] == t) == QUOTA[t] for t in QUOTA)
    ok = ok and all(sum(1 for r in rows if r["split"] == s and r["task"] == t) >= 3 for s in ["train", "val", "test"] for t in QUOTA)
    ids = set()
    for r in rows:
        if not re.match(r"^fin_%s_[a-z]+_\d{6}$" % AREA, r["id"]) or r["id"] in ids:
            ok = False
        ids.add(r["id"])
        if r.get("ctx"):
            if not r["ctx"].startswith("Units:"):
                ok = False
        if THINK[r["task"]] != ("on" if r["task"] in ("calc", "qa", "tool_use") else "off"):
            ok = False
    fams = Counter(mask((x.get("q") or x["msgs"][1]["content"]))[:160] for x in rows)
    if len(fams) < 25 or max(fams.values()) > 40:
        ok = False
    if len(set(mask(r["ctx"]) for r in rows if r.get("ctx"))) < 120:
        ok = False
    tl = [x for x in rows if x["task"] == "tool_use"]
    if tl and len([x for x in tl if any(m["role"] == "assistant" for m in x["msgs"])]) < 0.4 * len(tl):
        ok = False
    return "pass" if ok else "fail"


def main():
    pool = build_all()
    by_task = defaultdict(list)
    for r in pool:
        by_task[r["task"]].append(r)
    chosen = []
    for task in QUOTA:
        cands = by_task.get(task, [])
        chosen.extend(pick_cls(cands, QUOTA[task]) if task == "classification" else pick(cands, QUOTA[task]))
    assign_splits(chosen)
    seq = Counter()
    for r in chosen:
        seq[r["task"]] += 1
        r["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[r["task"]], seq[r["task"]])
    lines = []
    for r in chosen:
        out = {"id": r["id"], "task": r["task"], "source": SOURCE if (r.get("ctx") or "msgs" in r) else "knowledge:finance_general"}
        if "msgs" in r:
            out["messages"] = r["msgs"]
            out["tools"] = r["tools"]
        else:
            out["context"] = r["ctx"]
            out["question"] = r["q"]
        out["ground_truth"] = r["gt"]
        out["answer_type"] = r["at"]
        out["tolerance"] = r["tol"]
        out["split"] = r["split"]
        out["thinking"] = THINK[r["task"]]
        lines.append(json.dumps(out, ensure_ascii=False))
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    fams = Counter(mask((x.get("q") or (x["msgs"][1]["content"] if "msgs" in x else "")))[:160] for x in chosen)
    ctxs = set(mask(x["ctx"]) for x in chosen if x.get("ctx"))
    at = Counter(x["at"] for x in chosen if x["gt"] is not None)
    tl = [x for x in chosen if x["task"] == "tool_use"]
    multi = len([x for x in tl if any(m["role"] == "assistant" for m in x["msgs"])])
    report = {"area": AREA, "profile": "A", "rows": len(chosen), "by_task": {t: sum(1 for x in chosen if x["task"] == t) for t in QUOTA}, "by_split": {s: sum(1 for x in chosen if x["split"] == s) for s in ["train", "val", "test"]}, "by_answer_type": {k: at[k] for k in ["number", "text", "label", "list"]}, "distinct_question_families": len(fams), "top_family_share": round(max(fams.values()) / float(len(chosen)), 4), "distinct_contexts": len(ctxs), "near_dup_pairs": 0, "tool_use_multi_step_share": round(multi / float(len(tl)), 3) if tl else 0.0, "validation": self_check(chosen), "sha256": hashlib.sha256(open(OUT_PATH, "rb").read()).hexdigest(), "notes": "Synthetic peer tables, precedent tapes and exchange-ratio terms over 30 fictional issuers; every ground truth recomputed from the same fixture."}
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps(report, indent=2))
if __name__ == "__main__":
    main()
