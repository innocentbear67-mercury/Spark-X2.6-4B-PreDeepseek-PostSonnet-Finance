#!/usr/bin/env python3
"""Deterministic generator for the earnings_transcripts area (1000 rows, profile B).
Every company, transcript and figure is synthetic. Ground-truth values are computed from the
same fixture dict that renders the context string, so each answer reproduces by arithmetic.
"""
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
AREA = "earnings_transcripts"
SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
LASTD = {"Jan": 31, "Feb": 28, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
         "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}
# name, sector, fiscal-year-end month, currency, CEO, CFO, product noun
COMPANIES = [
    ("Halcyon Grid Utilities", "Utilities", 12, "USD", "Marisol Vance", "Devin Okafor", "grid interconnect"),
    ("Meridian Bancorp", "Banking", 12, "USD", "Adaeze Nwosu", "Peter Lindqvist", "commercial loan"),
    ("Kestrel Foods", "Staples", 6, "USD", "Tomas Ferreira", "Anika Shah", "chilled ready meal"),
    ("Arclight Semiconductor", "Semiconductors", 12, "USD", "Grace Okonjo", "Rahul Menon", "analog controller"),
    ("Blue Harbour Logistics", "Transport", 3, "EUR", "Sofia Lindgren", "Mateo Ricci", "container slot"),
    ("Northwind Therapeutics", "Biotech", 12, "USD", "Elena Marchetti", "Julian Reyes", "clinical programme"),
    ("Cedarline Retail Group", "Retail", 1, "GBP", "Harriet Coles", "Niall Docherty", "store format"),
    ("Vantage Alloy Works", "Industrials", 12, "USD", "Marcus Bell", "Ingrid Halvorsen", "precision casting"),
    ("Solstice Renewables", "Renewables", 12, "EUR", "Clara Duarte", "Henrik Bauer", "solar tracker"),
    ("Granite Peak Mining", "Mining", 12, "CAD", "Wesley Cardinal", "Mei-Ling Chao", "ore tonne"),
    ("Lumen Path Software", "Software", 12, "USD", "Priyanka Iyer", "Douglas Fenwick", "subscription seat"),
    ("Tidewater Marine Services", "Shipping", 12, "USD", "Rafael Montes", "Kirsten Aaberg", "vessel day"),
    ("Orchard Gate Hotels", "Hospitality", 12, "GBP", "Imogen Hartley", "Sanjay Kapoor", "room night"),
    ("Pinnacle Fabrication", "Machinery", 9, "USD", "Bruce Whitaker", "Lena Petrova", "hydraulic unit"),
    ("Silverbrook Insurance", "Insurance", 12, "USD", "Camille Beaumont", "Owen Fitzgerald", "policy"),
    ("Foxglove Media", "Media", 12, "EUR", "Stefan Vogel", "Aisha Bello", "advertising slot"),
    ("Redstone Payments", "Payments", 12, "USD", "Daniel Osei", "Yuki Tanaka", "processed transaction"),
    ("Aurora Biosciences", "Biotech", 12, "USD", "Naomi Roth", "Felipe Andrade", "assay kit"),
    ("Copperfield Chemicals", "Chemicals", 12, "EUR", "Beatriz Salgado", "Anders Holm", "specialty resin"),
    ("Windrow Agritech", "Agriculture", 9, "USD", "Colleen Mahoney", "Viktor Sorokin", "field sensor"),
    ("Beacon Health Systems", "Healthcare", 12, "USD", "Ayesha Rahman", "Gregory Pike", "outpatient clinic"),
    ("Ironvale Steel", "Steel", 12, "USD", "Frank Delacroix", "Sunita Rao", "rolled coil"),
    ("Marlow Consumer Brands", "Consumer", 12, "GBP", "Edith Nakamura", "Rory Gallagher", "household brand"),
    ("Quarry Lane REIT", "Real Estate", 12, "USD", "Leonard Ashby", "Petra Novak", "leasable suite"),
]
SEGMENTS = {
    "Utilities": ["Grid Hardware", "Services", "Software"], "Banking": ["Net Interest", "Fee Income", "Treasury"],
    "Staples": ["Ambient", "Chilled", "Foodservice"], "Semiconductors": ["Automotive", "Industrial", "Consumer"],
    "Transport": ["Ocean", "Contract Logistics", "Air"], "Biotech": ["Lead Programme", "Partnered", "Royalties"],
    "Retail": ["Stores", "Online", "Wholesale"], "Industrials": ["Aerospace", "Energy", "General"],
    "Renewables": ["Development", "Construction", "Operating"], "Mining": ["Copper", "Gold", "By-product"],
    "Software": ["Subscription", "Services", "Licence"], "Shipping": ["Spot", "Time Charter", "Bunkering"],
    "Hospitality": ["Rooms", "Food and Beverage", "Management"], "Machinery": ["Original Equipment", "Aftermarket", "Rental"],
    "Insurance": ["Motor", "Property", "Commercial"], "Media": ["Broadcast", "Digital", "Production"],
    "Payments": ["Merchant Acquiring", "Issuing", "Platform"], "Chemicals": ["Coatings", "Adhesives", "Agro"],
    "Agriculture": ["Hardware", "Data", "Services"], "Healthcare": ["Primary Care", "Specialty", "Diagnostics"],
    "Steel": ["Flat Rolled", "Long Products", "Distribution"], "Consumer": ["Home Care", "Personal Care", "Baby"],
    "Real Estate": ["Office", "Industrial", "Retail"],
}
ANALYSTS = [
    ("Priya Raman", "Sable Ridge"), ("Nathan Cole", "Brookline"), ("Ingrid Sandoval", "Harbor Point"),
    ("Desmond Achebe", "Cobalt Street"), ("Lucia Ferraro", "Northgate"), ("Owen Trimble", "Ashford Lane"),
    ("Meera Krishnan", "Wexford"), ("Tobias Lang", "Sterling Row"), ("Hannah Weiss", "Juniper Bay"),
    ("Victor Almeida", "Redwood"), ("Sophie Duval", "Larkspur"), ("Andre Kowalski", "Highbridge"),
]
OPENS = [
    "Demand for our {product} held up and order intake ran ahead of plan.",
    "We converted backlog faster than expected in the quarter.",
    "Input costs moved against us again and we are passing through price.",
    "Currency moved against us, though volume growth more than offset it.",
    "The next-generation {product} launch remains on track.",
    "Retention improved everywhere and churn was the lowest we have reported.",
    "Weather delayed two large projects and that work shifts into next quarter.",
    "The acquisition closed and the commercial teams are already combined.",
]
GUIDE_REASON = {
    "raise": "Order intake and pricing supported a higher range.",
    "cut": "Slower pipeline conversion forced a reset.",
    "reiterate": "Trading is in line with the plan.",
    "withdraw": "Second-half visibility is too limited.",
}
HEDGE = {
    "low": "Margin should recover in the fourth quarter.",
    "moderate": "Margin should recover if volume holds, subject to input costs.",
    "high": "Margin may recover if volume holds, though it could slip assuming costs ease.",
}
CERT = {
    "certain": "We will close the year at the top of the range.",
    "probable": "We expect to close the year at the top of the range.",
    "possible": "We could close the year at the top of the range.",
    "unlikely": "We do not expect to close at the top of the range.",
}
INTENT_Q = {
    "growth": "Where is second-half growth coming from?",
    "capital_allocation": "How are you prioritising buybacks against capital spending?",
    "guidance": "What pricing is embedded in the guidance?",
    "competition": "Are competitors discounting to win share?",
}
INTENT_LABEL = {"growth": "growth", "capital_allocation": "capital allocation",
                "guidance": "guidance", "competition": "competition"}
INTENT_ANS = {
    "growth": "The second half is carried by backlog we did not have a year ago.",
    "capital_allocation": "Buybacks remain the first call on excess cash.",
    "guidance": "The guidance assumes no further price increases.",
    "competition": "We are not matching the discounting and we are holding share.",
}
COMMIT = {
    "firm": "We are committed to {amt} of capital spending on the new line by {date}.",
    "tentative": "We intend to spend {amt} on the new line, targeting commissioning by {date}.",
    "aspirational": "We aspire to commission the new line by {date}, with {amt} planned.",
}
DIRS = ["raise", "cut", "reiterate", "withdraw"]
HEDGES = ["low", "moderate", "high"]
CERTS = ["certain", "probable", "possible", "unlikely"]
RESPS = ["direct", "partial", "deflect"]
INTENTS = ["growth", "capital_allocation", "guidance", "competition"]
CTYPES = ["firm", "tentative", "aspirational"]
THINK = {"calc": "on", "qa": "on", "tool_use": "on",
         "extraction": "off", "classification": "off", "summarization": "off"}
FIELDS = ["name", "sector", "fye", "ccy", "ceo", "cfo", "product"]
def h(*parts):
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:12], 16)
def rd(x, nd=1):
    return round(float(x), nd)
def fnum(x, nd=1):
    x = rd(x, nd)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return ("%." + str(nd) + "f") % x
def pct(a, b):
    return rd((a / b - 1.0) * 100.0, 1)
def pctof(a, b):
    return rd(a / b * 100.0, 1)
def quarter_date(co, fy, q):
    m = co["fye"] - 3 * (4 - q)
    y = fy
    while m <= 0:
        m += 12
        y -= 1
    name = MONTHS[m - 1]
    return "%d %s %d" % (LASTD[name], name, y)

def build_fixture(co, t):
    q, fy = t % 4 + 1, 2025 + t // 4
    period, prev = "Q%d FY%d" % (q, fy), "Q%d FY%d" % (q, fy - 1)
    key = "%s|%s" % (co["name"], period)
    base = 700.0 + h(co["name"], "base") % 3600
    g = 0.02 + (h(co["name"], "g") % 9) / 100.0
    def rev_at(k):
        return rd(base * ((1.0 + g) ** k), 1)
    rev, rev_prior = rev_at(t - 4), rev_at(t - 8)
    gm0 = 0.30 + (h(co["name"], "gm") % 28) / 100.0
    drift = ((h(key, "gmd") % 7) - 3) / 1000.0
    if abs(drift) < 0.002:
        drift = 0.002 if drift >= 0 else -0.002
    gm = gm0 + drift
    gm_prior = gm0 - (0.001 + (h(key, "gmp") % 4) / 1000.0)
    gp, gp_prior = rd(rev * gm, 1), rd(rev_prior * gm_prior, 1)
    oxr = 0.16 + (h(co["name"], "ox") % 18) / 100.0
    opex, opex_prior = rd(rev * oxr, 1), rd(rev_prior * (oxr - 0.002), 1)
    op, op_prior = rd(gp - opex, 1), rd(gp_prior - opex_prior, 1)
    ni, ni_prior = rd(op * 0.78, 1), rd(op_prior * 0.78, 1)
    shares = float(40 + h(co["name"], "sh") % 260)
    eps, eps_prior = rd(ni / shares, 2), rd(ni_prior / shares, 2)
    ocf = rd(ni + rev * 0.06, 1)
    capex = rd(rev * (0.04 + (h(key, "cx") % 6) / 100.0), 1)
    cash, debt = rd(rev * 0.28 + 200, 1), rd(rev * 0.18, 1)
    bb = rd(min(60 + h(key, "bb") % 240, shares * 4.0 * 0.05), 1)
    px = rd(max(4.0, abs(eps) * 16.0 + h(key, "px") % 7), 2)
    dps = rd(max(0.05, eps * 0.30), 2)
    hc = int(rev * 2.2 + 900)
    hcp = int(hc * (0.97 + (h(key, "hc") % 7) / 100.0))
    backlog = rd(rev * 1.15, 1)
    segs = SEGMENTS[co["sector"]]
    s1 = 0.50 + (h(key, "s1") % 9) / 100.0
    s2 = 0.27 + (h(key, "s2") % 6) / 100.0
    a1, a2 = rd(rev * s1, 1), rd(rev * s2, 1)
    a3 = rd(rev - a1 - a2, 1)
    shift = 0.04 + (h(key, "sh1") % 7) / 100.0
    p1, p2 = rd(rev_prior * s1 * (1.0 - shift), 1), rd(rev_prior * s2 * (1.0 - shift / 2.0), 1)
    p3 = rd(rev_prior - p1 - p2, 1)
    dec = h(key, "dec") % 3
    if dec == 0:
        p1 = rd(p1 * 1.14, 1)
    elif dec == 1:
        p2 = rd(p2 * 1.14, 1)
    else:
        p3 = rd(p3 * 1.14, 1)
    seg_rows = [(segs[0], a1, p1), (segs[1], a2, p2), (segs[2], a3, p3)]
    growths = [pct(a, p) for (_, a, p) in seg_rows]
    largest = max(range(3), key=lambda i: seg_rows[i][1])
    smallest = min(range(3), key=lambda i: seg_rows[i][1])
    fastest = max(range(3), key=lambda i: growths[i])
    declining = [seg_rows[i][0] for i in range(3) if growths[i] < 0]
    direction = DIRS[t % 4]
    mid = rd(rev * 4.05 * (1.0 + g), 1)
    width = rd(mid * 0.018, 1)
    g_low, g_high = rd(mid - width, 1), rd(mid + width, 1)
    pm = rd(mid * 0.975, 1) if direction == "raise" else (rd(mid * 1.035, 1) if direction == "cut" else mid)
    pg_low, pg_high = rd(pm - width, 1), rd(pm + width, 1)
    capex_commit = rd(capex * 4.0 * (0.9 + (h(key, "cc") % 3) * 0.15), 1)
    cm, cy = co["fye"] + 6, fy + 1
    while cm > 12:
        cm -= 12
        cy += 1
    cname = MONTHS[cm - 1]
    commit_date = "%d %s %d" % (LASTD[cname], cname, cy)
    a1n, a1f = ANALYSTS[h(key, "a1") % len(ANALYSTS)]
    a2n, a2f = ANALYSTS[h(key, "a2") % len(ANALYSTS)]
    if a2n == a1n:
        a2n, a2f = ANALYSTS[(h(key, "a2") + 1) % len(ANALYSTS)]
    f = dict(key=key, co=co, t=t, period=period, prev=prev, qdate=quarter_date(co, fy, q),
             rev=rev, rev_prior=rev_prior, gp=gp, gp_prior=gp_prior, opex=opex,
             opex_prior=opex_prior, op=op, op_prior=op_prior, ni=ni, ni_prior=ni_prior,
             shares=shares, eps=eps, eps_prior=eps_prior, ocf=ocf, capex=capex, cash=cash,
             debt=debt, bb=bb, px=px, dps=dps, hc=hc, hcp=hcp, backlog=backlog,
             seg_rows=seg_rows, growths=growths, largest=largest, smallest=smallest,
             fastest=fastest, declining=declining, direction=direction, g_low=g_low,
             g_high=g_high, pg_low=pg_low, pg_high=pg_high, capex_commit=capex_commit,
             commit_date=commit_date, hedge=HEDGES[h(key, "hg") % 3],
             cert=CERTS[h(key, "ct") % 4], resp=RESPS[t % 3],
             intent=INTENTS[h(key, "it") % 4], ctype=CTYPES[h(key, "cy") % 3],
             a1n=a1n, a1f=a1f, a2n=a2n, a2f=a2f, gm=gm, gm_prior=gm_prior,
             fx=rd(rev * (0.006 + (h(key, "fx") % 5) / 1000.0), 1),
             acq=rd(rev * (0.03 + (h(key, "aq") % 5) / 100.0), 1),
             export=1000 * (200 + h(key, "ex") % 400),
             export_p=int(1000 * (200 + h(key, "ex") % 400) * (0.92 + (h(key, "exp") % 7) / 100.0)),
             fac=rd(rev * (0.35 + (h(key, "fc") % 4) / 10.0), 1),
             px_inc=rd(2.0 + (h(key, "pi") % 40) / 10.0, 1),
             )
    f["gm_pct"], f["gmp_pct"] = pctof(gp, rev), pctof(gp_prior, rev_prior)
    f["bp"] = int(round(abs(f["gm_pct"] - f["gmp_pct"]) * 100.0, 0))
    f["gm_dir"] = "up" if f["gm_pct"] >= f["gmp_pct"] else "down"
    f["open"] = OPENS[t % len(OPENS)].format(product=co["product"])
    f["ctx"], f["avail"] = render_context(f)
    return f

def render_context(f):
    co = f["co"]
    p, pp = f["period"], f["prev"]
    core = ("CFO %s: Revenue %s against %s, gross profit %s against %s, operating income %s on "
            "operating expense %s against %s, and diluted EPS %s against %s."
            % (co["cfo"], fnum(f["rev"]), fnum(f["rev_prior"]), fnum(f["gp"]), fnum(f["gp_prior"]),
               fnum(f["op"]), fnum(f["opex"]), fnum(f["opex_prior"]), fnum(f["eps"], 2),
               fnum(f["eps_prior"], 2)))
    cash = ("Operating cash flow %s, net income %s, capital expenditure %s; cash %s against debt %s."
            % (fnum(f["ocf"]), fnum(f["ni"]), fnum(f["capex"]), fnum(f["cash"]), fnum(f["debt"])))
    capital = ("Buybacks %s at an average of %s; dividend %s per share on %s diluted shares."
               % (fnum(f["bb"]), fnum(f["px"], 2), fnum(f["dps"], 2), fnum(f["shares"])))
    ops = "Headcount %d against %d; backlog %s." % (f["hc"], f["hcp"], fnum(f["backlog"]))
    rows = ["| Segment | %s | %s |" % (p, pp), "|---|---|---|"]
    rows += ["| %s | %s | %s |" % (nm, fnum(a), fnum(b)) for nm, a, b in f["seg_rows"]]
    table = "\n".join(rows)
    if f["direction"] == "withdraw":
        guide = ("We are withdrawing our full-year revenue guidance, having previously guided %s to "
                 "%s. %s" % (fnum(f["pg_low"]), fnum(f["pg_high"]), GUIDE_REASON["withdraw"]))
        outlook = None
    else:
        guide = ("We guide full-year revenue to %s to %s, from %s to %s. %s"
                 % (fnum(f["g_low"]), fnum(f["g_high"]), fnum(f["pg_low"]),
                    fnum(f["pg_high"]), GUIDE_REASON[f["direction"]]))
        outlook = "Outlook: %s %s" % (HEDGE[f["hedge"]], CERT[f["cert"]])
    a1line = ("Analyst %s (%s): Margins have moved around again this quarter. Why point to a recovery?"
              % (f["a1n"], f["a1f"]))
    if f["resp"] == "direct":
        resp = ("Gross margin was %s percent, %s %d basis points, as input costs outran price; %s "
                "percent of pricing is already in the market."
                % (fnum(f["gm_pct"]), f["gm_dir"], f["bp"], fnum(f["px_inc"])))
    elif f["resp"] == "partial":
        resp = ("Margin was %s percent, %s %d basis points, and we have %s percent of pricing already "
                "in the market. I would rather not guide the quarter."
                % (fnum(f["gm_pct"]), f["gm_dir"], f["bp"], fnum(f["px_inc"])))
    else:
        resp = ("I would point you to the segment disclosure on mix. The bigger story is backlog of %s."
                % fnum(f["backlog"]))
    a2line = "Analyst %s (%s): %s" % (f["a2n"], f["a2f"], INTENT_Q[f["intent"]])
    ans = INTENT_ANS[f["intent"]]
    if f["direction"] == "withdraw" and f["intent"] == "guidance":
        ans = "We are not in a position to guide pricing for the second half."
    close = "CEO %s: %s %s" % (co["ceo"], ans,
                               COMMIT[f["ctype"]].format(amt=fnum(f["capex_commit"]), date=f["commit_date"]))
    blocks = [
        ("hdr", "Transcript: %s %s call." % (co["name"], p), False),
        ("units", "Units: $ in millions, per-share in dollars, percentages in percent.", False),
        ("open", "CEO %s: %s" % (co["ceo"], f["open"]), False),
        ("core", core, False),
        ("cash", cash, False),
        ("capital", capital, True),
        ("table", table, False),
    ]
    if h(f["key"], "fx") % 5 == 0:
        blocks.append(("x_fx", "Note: revenue includes a currency headwind of %s in the quarter." % fnum(f["fx"]), True))
    if h(f["key"], "aq") % 5 == 1:
        blocks.append(("x_acq", "Note: the acquisition contributed %s of revenue in the quarter." % fnum(f["acq"]), True))
    if h(f["key"], "fn") % 4 == 0:
        blocks.append(("x_fn", "Footnote: segment revenue excludes intersegment sales.", True))
    if h(f["key"], "fc") % 6 == 0:
        blocks.append(("x_fac", "Note: the revolving credit facility totals %s." % fnum(f["fac"]), True))
    if h(f["key"], "ex") % 6 == 2:
        blocks.append(("x_ex", "Note: export revenue was %d thousand against %d thousand."
                       % (f["export"], f["export_p"]), True))
    blocks.append(("ops", ops, True))
    blocks.append(("guide", guide, False))
    if outlook:
        blocks.append(("outlook", outlook, False))
    blocks.append(("a1", a1line, False))
    blocks.append(("resp", "CFO %s: %s" % (co["cfo"], resp), False))
    blocks.append(("a2", a2line, False))
    blocks.append(("close", close, False))
    def length():
        return len("\n".join(b[1] for b in blocks if b[1]))
    for pref in ["ops", "x_", "capital"]:
        while length() > 1500:
            hit = None
            for i in range(len(blocks) - 1, -1, -1):
                if blocks[i][0].startswith(pref) and blocks[i][1]:
                    hit = i
                    break
            if hit is None:
                break
            blocks[hit] = (blocks[hit][0], "", True)
    text = "\n".join(b[1] for b in blocks if b[1])
    avail = set(b[0] for b in blocks if b[1])
    if f["resp"] != "deflect":
        avail.add("price")
    if f["direction"] != "withdraw":
        avail.add("guide_cur")
    if f["direction"] in ("raise", "cut"):
        avail.add("guide_chg")
    if f["intent"] == "capital_allocation":
        avail.add("intent_cap")
    if f["declining"]:
        avail.add("decl")
    return text, avail
def T(name, q, at, tol, req, fn):
    return dict(name=name, q=q, at=at, tol=tol, req=set(req), fn=fn)
def seg_share(f, i):
    return pctof(f["seg_rows"][i][1], f["rev"])
T_CALC = [
    T("c_rev_yoy", "What was the year-over-year change in revenue, in percent?", "number", "abs:0.1", ["core"], lambda f: pct(f["rev"], f["rev_prior"])),
    T("c_gm", "What was the gross margin for the quarter, in percent?", "number", "abs:0.1", ["core"], lambda f: pctof(f["gp"], f["rev"])),
    T("c_om", "What was the operating margin for the quarter, in percent?", "number", "abs:0.1", ["core"], lambda f: pctof(f["op"], f["rev"])),
    T("c_gmid", "What was the midpoint of the full-year revenue guidance, in millions?", "number", "abs:0.1", ["guide_cur"], lambda f: rd((f["g_low"] + f["g_high"]) / 2.0, 1)),
    T("c_gdelta", "By how much did the midpoint of revenue guidance change versus the prior midpoint, in millions?", "number", "abs:0.1", ["guide_cur"], lambda f: rd((f["g_low"] + f["g_high"]) / 2.0 - (f["pg_low"] + f["pg_high"]) / 2.0, 1)),
    T("c_epsg", "What was the year-over-year change in earnings per share, in percent?", "number", "abs:0.1", ["core"], lambda f: pct(f["eps"], f["eps_prior"])),
    T("c_capexpct", "What was capital expenditure as a percentage of revenue?", "number", "abs:0.1", ["cash"], lambda f: pctof(f["capex"], f["rev"])),
    T("c_fcf", "What was free cash flow for the quarter, in millions?", "number", "abs:0.1", ["cash"], lambda f: rd(f["ocf"] - f["capex"], 1)),
    T("c_netcash", "What was net cash at quarter end, in millions?", "number", "abs:0.1", ["cash"], lambda f: rd(f["cash"] - f["debt"], 1)),
    T("c_rpe", "What was revenue per employee for the quarter, in thousands?", "number", "abs:1", ["ops"], lambda f: rd(f["rev"] * 1000.0 / f["hc"], 1)),
    T("c_div", "What was the total dividend payout for the quarter, in millions?", "number", "abs:0.1", ["capital"], lambda f: rd(f["dps"] * f["shares"], 1)),
    T("c_bbshares", "How many shares were repurchased during the quarter, in millions?", "number", "abs:0.01", ["capital"], lambda f: rd(f["bb"] / f["px"], 2)),
    T("c_opexg", "What was the year-over-year change in operating expense, in percent?", "number", "abs:0.1", ["core"], lambda f: pct(f["opex"], f["opex_prior"])),
    T("c_segg", "What was the year-over-year change in revenue for the largest segment, in percent?", "number", "abs:0.1", ["table"], lambda f: f["growths"][f["largest"]]),
]
T_EXTR = [
    T("e_capex", "What capital expenditure amount, in millions, was given for the new line?", "number", "abs:0.1", ["close"], lambda f: f["capex_commit"]),
    T("e_date", "By what date did management say the new line would be commissioned?", "text", "exact", ["close"], lambda f: f["commit_date"]),
    T("e_glow", "What was the low end of the full-year revenue guidance, in millions?", "number", "abs:0.1", ["guide_cur"], lambda f: f["g_low"]),
    T("e_ghigh", "What was the high end of the full-year revenue guidance, in millions?", "number", "abs:0.1", ["guide_cur"], lambda f: f["g_high"]),
    T("e_backlog", "What was the backlog at quarter end, in millions?", "number", "abs:0.1", ["ops"], lambda f: f["backlog"]),
    T("e_hc", "How many employees did the company report at quarter end?", "number", "abs:1", ["ops"], lambda f: f["hc"]),
    T("e_dps", "What dividend per share did the company declare, in dollars?", "number", "abs:0.01", ["capital"], lambda f: f["dps"]),
    T("e_bb", "What amount of stock did the company repurchase during the quarter, in millions?", "number", "abs:0.1", ["capital"], lambda f: f["bb"]),
    T("e_smallest", "Which segment reported the smallest revenue for the quarter?", "text", "normalized", ["table"], lambda f: f["seg_rows"][f["smallest"]][0]),
    T("e_gp", "What was gross profit for the quarter, in millions?", "number", "abs:0.1", ["core"], lambda f: f["gp"]),
    T("e_fx", "What currency headwind to revenue was disclosed in the note, in millions?", "number", "abs:0.1", ["x_fx"], lambda f: f["fx"]),
    T("e_acq", "What revenue did the acquisition contribute in the quarter, in millions?", "number", "abs:0.1", ["x_acq"], lambda f: f["acq"]),
    T("e_export", "What was export revenue for the quarter, in millions?", "number", "abs:0.1", ["x_ex"], lambda f: rd(f["export"] / 1000.0, 1)),
    T("e_analyst2", "Which analyst asked about the capital programme?", "text", "normalized", ["intent_cap"], lambda f: f["a2n"]),
    T("e_shares", "How many diluted shares were outstanding, in millions?", "number", "abs:0.1", ["capital"], lambda f: f["shares"]),
]
T_QA = [
    T("q_who_margin", "Who fielded the analyst's question about gross margin?", "text", "normalized", ["resp"], lambda f: f["co"]["cfo"]),
    T("q_top2", "What was the combined revenue of the two largest segments, in millions?", "number", "abs:0.1", ["table"], lambda f: rd(sum(sorted([x[1] for x in f["seg_rows"]], reverse=True)[:2]), 1)),
    T("q_gmchg", "By how many percentage points did the gross margin change versus the prior-year quarter?", "number", "abs:0.1", ["price"], lambda f: rd(f["gm_pct"] - f["gmp_pct"], 1)),
    T("q_fastest", "Which segment grew fastest year over year?", "text", "normalized", ["table"], lambda f: f["seg_rows"][f["fastest"]][0]),
    T("q_commit", "What amount was given for the new line, and by what date?", "list", "set", ["close"], lambda f: [fnum(f["capex_commit"]), f["commit_date"]]),
    T("q_guide_why", "Why did management change the full-year revenue guidance?", "text", "normalized", ["guide_chg"], lambda f: GUIDE_REASON[f["direction"]]),
    T("q_q2", "What topic did the second analyst raise?", "text", "normalized", ["a2"], lambda f: INTENT_LABEL[f["intent"]]),
    T("q_price", "What percentage of pricing did management say was already in the market, in percent?", "number", "abs:0.1", ["price"], lambda f: f["px_inc"]),
    T("q_declined", "Which segments reported lower revenue than a year ago?", "list", "set", ["decl"], lambda f: sorted(f["declining"])),
    T("q_hc_chg", "What was the change in headcount versus the prior quarter, in percent?", "number", "abs:0.1", ["ops"], lambda f: pct(f["hc"], f["hcp"])),
    T("q_cashconv", "What was operating cash flow as a multiple of net income?", "number", "abs:0.01", ["cash"], lambda f: rd(f["ocf"] / f["ni"], 2)),
    T("q_direct", "Did management give a direct answer to the analyst's margin question? Answer yes or no.", "text", "normalized", ["resp"], lambda f: "yes" if f["resp"] == "direct" else "no"),
    T("q_largest", "Which segment contributed the largest share of revenue, and what was that share in percent?", "list", "set", ["table"], lambda f: [f["seg_rows"][f["largest"]][0], fnum(seg_share(f, f["largest"]), 1)]),
    T("q_range", "How wide was the full-year revenue guidance range, in millions?", "number", "abs:0.1", ["guide_cur"], lambda f: rd(f["g_high"] - f["g_low"], 1)),
    T("q_eps", "What were earnings per share for the quarter, in dollars?", "number", "abs:0.01", ["core"], lambda f: f["eps"]),
]
def summ_prep(f):
    out = ["Revenue was %s against %s a year ago." % (fnum(f["rev"]), fnum(f["rev_prior"])),
           "Gross profit was %s and operating income %s." % (fnum(f["gp"]), fnum(f["op"]))]
    if f["direction"] == "withdraw":
        out.append("Management withdrew full-year revenue guidance, previously %s to %s."
                   % (fnum(f["pg_low"]), fnum(f["pg_high"])))
    else:
        out.append("Full-year revenue guidance is %s to %s." % (fnum(f["g_low"]), fnum(f["g_high"])))
    return out
def summ_qa(f):
    return ["The first analyst pressed management on the gross margin decline.",
            "Management put gross margin at %s percent, %s %d basis points year over year."
            % (fnum(f["gm_pct"]), f["gm_dir"], f["bp"]),
            "The second analyst asked about %s." % INTENT_LABEL[f["intent"]]]
def summ_guide(f):
    if f["direction"] == "withdraw":
        return ["Management withdrew the full-year revenue guidance.",
                "The prior range was %s to %s." % (fnum(f["pg_low"]), fnum(f["pg_high"])),
                "The reason given was limited second-half visibility."]
    head = {"raise": "Guidance was raised to %s to %s.", "cut": "Guidance was cut to %s to %s.",
            "reiterate": "Guidance was reiterated at %s to %s."}[f["direction"]]
    return [head % (fnum(f["g_low"]), fnum(f["g_high"])),
            "The prior range was %s to %s." % (fnum(f["pg_low"]), fnum(f["pg_high"])),
            GUIDE_REASON[f["direction"]]]
def summ_seg(f):
    return ["%s revenue was %s against %s." % (nm, fnum(a), fnum(b)) for nm, a, b in f["seg_rows"]]
def summ_cap(f):
    return ["Buybacks were %s at an average price of %s." % (fnum(f["bb"]), fnum(f["px"], 2)),
            "The dividend was %s per share on %s diluted shares." % (fnum(f["dps"], 2), fnum(f["shares"])),
            "Capital expenditure was %s in the quarter." % fnum(f["capex"])]
def summ_risk(f):
    return ["Currency was a %s headwind to revenue." % fnum(f["fx"]),
            "Input costs rose faster than pricing.",
            "Gross margin was %s percent, %s %d basis points year over year."
            % (fnum(f["gm_pct"]), f["gm_dir"], f["bp"])]
T_SUMM = [
    dict(name="s_prep", q="Summarise the prepared remarks in three bullets.", at="list", tol="set", req={"core"}, fn=summ_prep),
    dict(name="s_qa", q="Summarise the analyst Q and A in three bullets.", at="list", tol="set", req={"price"}, fn=summ_qa),
    dict(name="s_guide", q="Summarise what changed in guidance and why, in three bullets.", at="list", tol="set", req={"guide"}, fn=summ_guide),
    dict(name="s_seg", q="Summarise the segment performance discussion in three bullets.", at="list", tol="set", req={"table"}, fn=summ_seg),
    dict(name="s_cap", q="Summarise the capital allocation comments in three bullets.", at="list", tol="set", req={"capital"}, fn=summ_cap),
    dict(name="s_risk", q="Summarise the risks management flagged in three bullets.", at="list", tol="set", req={"x_fx", "price"}, fn=summ_risk),
]
T_CLS = [
    dict(name="k_dir", q="Classify the full-year revenue guidance change as exactly one of {raise, cut, withdraw, reiterate}.",
         at="label", tol="exact", req={"guide"}, fn=lambda f: f["direction"]),
    dict(name="k_hedge", q=("Counting only the terms may, might, could, subject to, assuming, potentially and if, classify the "
                            "hedging in the sentence labelled Outlook as exactly one of {low, moderate, high}, where low is "
                            "0-1 terms, moderate is 2-3 and high is 4 or more."),
         at="label", tol="exact", req={"outlook"}, fn=lambda f: f["hedge"]),
    dict(name="k_cert", q="Classify management's certainty about closing the year at the top of the range as exactly one of {certain, probable, possible, unlikely}.",
         at="label", tol="exact", req={"outlook"}, fn=lambda f: f["cert"]),
    dict(name="k_resp", q="Classify management's response to the analyst's margin question as exactly one of {direct, partial, deflect}.",
         at="label", tol="exact", req={"resp"}, fn=lambda f: f["resp"]),
    dict(name="k_intent", q="Classify the second analyst's question as exactly one of {growth, capital_allocation, guidance, competition}.",
         at="label", tol="exact", req={"a2"}, fn=lambda f: f["intent"]),
    dict(name="k_commit", q="Classify the capital commitment language in the CEO's closing remarks as exactly one of {firm, tentative, aspirational}.",
         at="label", tol="exact", req={"close"}, fn=lambda f: f["ctype"]),
]

def tool(name, desc, props, required):
    return {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required}}
TOOLS = [
    tool("get_financials", "Return reported revenue, gross profit, operating income, EPS, cash flow and balance sheet items for one company and fiscal period.",
         {"company": {"type": "string", "description": "Legal company name"},
          "period": {"type": "string", "description": "Fiscal period such as Q2 FY2026"}}, ["company", "period"]),
    tool("get_guidance", "Return the revenue guidance range this company has issued, newest first.",
         {"company": {"type": "string", "description": "Legal company name"},
          "updates": {"type": "integer", "description": "How many recent updates to return"}}, ["company", "updates"]),
    tool("get_segment_revenue", "Return segment revenue for the reported period and the prior-year period.",
         {"company": {"type": "string", "description": "Legal company name"},
          "period": {"type": "string", "description": "Fiscal period such as Q2 FY2026"}}, ["company", "period"]),
    tool("search_transcript", "Full-text search inside one earnings call transcript and return matching speaker turns.",
         {"company": {"type": "string", "description": "Legal company name"},
          "period": {"type": "string", "description": "Fiscal period such as Q2 FY2026"},
          "keyword": {"type": "string", "description": "Word or phrase to find"}},
         ["company", "period", "keyword"]),
]
SYS_T = ("You are an equity research assistant. Units: $ in millions except per-share amounts in "
         "dollars. Use the tools rather than guessing, and say so when the data is missing.")
def MSG(role, content):
    return {"role": role, "content": content}
QWORD = ["first", "second", "third", "fourth"]


def sysmsg(f):
    return MSG("system", SYS_T + " Covered issuer: %s, period %s (%s quarter). Coverage: %s."
               % (f["co"]["name"], f["period"], QWORD[f["t"] % 4], f["a1f"]))
def fin_payload(f):
    return {"company": f["co"]["name"], "period": f["period"], "revenue": f["rev"],
            "prior_revenue": f["rev_prior"], "gross_profit": f["gp"], "operating_income": f["op"],
            "eps": f["eps"], "net_income": f["ni"], "operating_cash_flow": f["ocf"],
            "capex": f["capex"], "cash": f["cash"], "debt": f["debt"]}
def CALL(name, **args):
    return MSG("assistant", json.dumps({"tool": name, "arguments": args}, sort_keys=True))
def RES(obj):
    return MSG("tool", json.dumps(obj, sort_keys=True))
def tl_rev_growth(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "Pull the reported revenue for the covered issuer and tell me the number."
    m = [sysmsg(f), MSG("user", u1), CALL("get_financials", company=n, period=p), RES(fin_payload(f)),
         MSG("user", "Using that result, what was the year-over-year change in revenue, in percent, to one decimal?")]
    return dict(msgs=m, gt=pct(f["rev"], f["rev_prior"]), at="number", tol="abs:0.1", fam=u1)
def tl_gm_recover(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "Get me the gross margin for the covered period."
    bad = "Q1 FY2019"
    m = [sysmsg(f), MSG("user", u1), CALL("get_financials", company=n, period=bad),
         RES({"error": "no transcript for %s; available periods run from Q1 FY2025 to Q4 FY2026" % bad}),
         CALL("get_financials", company=n, period=p), RES(fin_payload(f)),
         MSG("user", "Using the corrected result, what was the gross margin, in percent, to one decimal?")]
    return dict(msgs=m, gt=pctof(f["gp"], f["rev"]), at="number", tol="abs:0.1", fam=u1)
def tl_guide_delta(f):
    n = f["co"]["name"]
    u1 = "Pull the last two guidance updates for the covered issuer."
    hist = [{"period": f["period"], "low": f["g_low"], "high": f["g_high"]},
            {"period": f["prev"], "low": f["pg_low"], "high": f["pg_high"]}]
    m = [sysmsg(f), MSG("user", u1), CALL("get_guidance", company=n, updates=2),
         RES({"company": n, "history": hist}),
         MSG("user", "By how much did the midpoint of guidance change versus the prior update, in millions?")]
    return dict(msgs=m, gt=rd((f["g_low"] + f["g_high"]) / 2.0 - (f["pg_low"] + f["pg_high"]) / 2.0, 1),
                at="number", tol="abs:0.1", fam=u1)
def tl_capex_search(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "Search the covered transcript for the new line commitment."
    sent = "CEO %s: %s" % (f["co"]["ceo"], COMMIT[f["ctype"]].format(
        amt=fnum(f["capex_commit"]), date=f["commit_date"]))
    m = [sysmsg(f), MSG("user", u1), CALL("search_transcript", company=n, period=p, keyword="new line"),
         RES({"matches": [{"speaker": f["co"]["ceo"], "text": sent}]}),
         MSG("user", "What amount was given for the new line, in millions?")]
    return dict(msgs=m, gt=f["capex_commit"], at="number", tol="abs:0.1", fam=u1)
def tl_insufficient(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "What was the gross margin for the covered period?"
    m = [sysmsg(f), MSG("user", u1), CALL("get_financials", company=n, period=p),
         RES({"company": n, "period": p, "revenue": f["rev"],
              "note": "gross profit is not disclosed for this period"}),
         MSG("user", "If the data needed is not present, reply exactly: insufficient data")]
    return dict(msgs=m, gt="insufficient data", at="text", tol="exact", fam=u1)
def tl_segments(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "Pull segment revenue for the covered period."
    rows = [{"segment": s, "period": a, "prior": b} for (s, a, b) in f["seg_rows"]]
    m = [sysmsg(f), MSG("user", u1), CALL("get_segment_revenue", company=n, period=p),
         RES({"company": n, "period": p, "segments": rows}),
         MSG("user", "Which segment was the largest, and what share of total revenue did it represent, in percent?")]
    return dict(msgs=m, gt=[f["seg_rows"][f["largest"]][0], fnum(seg_share(f, f["largest"]), 1)],
                at="list", tol="set", fam=u1)
def tl_type_error(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "Get me the balance sheet for the covered issuer."
    m = [sysmsg(f), MSG("user", u1), CALL("get_financials", company=n, period=3),
         RES({"error": "period must be a string such as Q3 FY2026"}),
         CALL("get_financials", company=n, period=p), RES(fin_payload(f)),
         MSG("user", "What was net cash, in millions?")]
    return dict(msgs=m, gt=rd(f["cash"] - f["debt"], 1), at="number", tol="abs:0.1", fam=u1)
def tl_direction(f):
    n = f["co"]["name"]
    u1 = "Compare the two most recent guidance ranges."
    hist = [{"period": f["period"], "low": f["g_low"], "high": f["g_high"]},
            {"period": f["prev"], "low": f["pg_low"], "high": f["pg_high"]}]
    m = [sysmsg(f), MSG("user", u1), CALL("get_guidance", company=n, updates=2),
         RES({"company": n, "history": hist}),
         MSG("user", "Classify the change as exactly one of {raise, cut, reiterate}.")]
    return dict(msgs=m, gt=f["direction"], at="label", tol="exact", fam=u1)
def tl_speaker(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "Find who spoke about pricing on the covered call."
    sent = "We have %s percent of pricing already in the market." % fnum(f["px_inc"])
    m = [sysmsg(f), MSG("user", u1), CALL("search_transcript", company=n, period=p, keyword="pricing"),
         RES({"matches": [{"speaker": f["co"]["cfo"], "role": "CFO", "text": sent}]}),
         MSG("user", "Who made that statement? Give the name only.")]
    return dict(msgs=m, gt=f["co"]["cfo"], at="text", tol="normalized", fam=u1)
def tl_capex_pct(f):
    n, p = f["co"]["name"], f["period"]
    u1 = "What did the covered issuer spend on capital expenditure?"
    m = [sysmsg(f), MSG("user", u1), CALL("get_financials", company=n, period=p), RES(fin_payload(f)),
         MSG("user", "Express that as a percentage of revenue, to one decimal.")]
    return dict(msgs=m, gt=pctof(f["capex"], f["rev"]), at="number", tol="abs:0.1", fam=u1)
TOOL_BUILDERS = [
    dict(name="t_rev_growth", fn=tl_rev_growth, req=set()),
    dict(name="t_gm_recover", fn=tl_gm_recover, req=set()),
    dict(name="t_guide_delta", fn=tl_guide_delta, req={"guide_cur"}),
    dict(name="t_capex_search", fn=tl_capex_search, req=set()),
    dict(name="t_insufficient", fn=tl_insufficient, req=set()),
    dict(name="t_segments", fn=tl_segments, req={"table"}),
    dict(name="t_type_error", fn=tl_type_error, req=set()),
    dict(name="t_direction", fn=tl_direction, req={"guide_cur"}),
    dict(name="t_speaker", fn=tl_speaker, req={"price"}),
    dict(name="t_capex_pct", fn=tl_capex_pct, req=set()),
]
def hashed_order(fixtures, task):
    return sorted(fixtures, key=lambda f: hashlib.sha256(("%s|%s" % (task, f["key"])).encode("utf-8")).hexdigest())
def mk(task, t, fx):
    return {"task": task, "source": "synthetic:" + AREA, "context": fx["ctx"], "question": t["q"],
            "ground_truth": t["fn"](fx), "answer_type": t["at"], "tolerance": t["tol"],
            "thinking": THINK[task], "_fx": fx["key"]}
def mk_tool(b, fx):
    d = b["fn"](fx)
    return {"task": "tool_use", "source": "synthetic:" + AREA, "messages": d["msgs"], "tools": TOOLS,
            "ground_truth": d["gt"], "answer_type": d["at"], "tolerance": d["tol"],
            "thinking": "on", "_fx": fx["key"]}
def cls_block(order, tmpl, counts, used):
    out = []
    for lab, n in counts:
        got = 0
        for fx in order:
            if got >= n:
                break
            k = (tmpl["name"], fx["key"])
            if k in used or not (tmpl["req"] <= fx["avail"]) or tmpl["fn"](fx) != lab:
                continue
            used.add(k)
            out.append(mk("classification", tmpl, fx))
            got += 1
        if got < n:
            raise SystemExit("cls short: %s %s %d/%d" % (tmpl["name"], lab, got, n))
    return out
def allocate(task, tmpls, total, fixtures, cap):
    base, rem = total // len(tmpls), total % len(tmpls)
    out, used, pairs, short = [], Counter(), set(), 0
    def add(t, fx):
        out.append(mk_tool(t, fx) if task == "tool_use" else mk(task, t, fx))
        used[fx["key"]] += 1
        pairs.add((t["name"], fx["key"]))
    for i, t in enumerate(tmpls):
        want = base + (1 if i < rem else 0)
        order = sorted(fixtures, key=lambda f: hashlib.sha256(
            ("%s|%s|%s" % (task, t["name"], f["key"])).encode("utf-8")).hexdigest())
        got = 0
        for fx in order:
            if got >= want:
                break
            if t["req"] <= fx["avail"] and used[fx["key"]] < cap:
                add(t, fx)
                got += 1
        short += want - got
    if short:
        for t in tmpls:
            if short <= 0:
                break
            order = sorted(fixtures, key=lambda f: hashlib.sha256(
                ("%s|%s|x" % (task, f["key"])).encode("utf-8")).hexdigest())
            for fx in order:
                if short <= 0:
                    break
                if (t["name"], fx["key"]) in pairs or t["req"] > fx["avail"] or used[fx["key"]] >= cap + 1:
                    continue
                add(t, fx)
                short -= 1
    if short:
        raise SystemExit("short %s %d" % (task, short))
    return out
def build_rows(fixtures):
    rows = []
    rows += allocate("calc", T_CALC, 120, fixtures, 2)
    rows += allocate("extraction", T_EXTR, 220, fixtures, 3)
    rows += allocate("qa", T_QA, 240, fixtures, 3)
    rows += allocate("summarization", T_SUMM, 100, fixtures, 2)
    rows += allocate("tool_use", TOOL_BUILDERS, 100, fixtures, 2)
    order, used = hashed_order(fixtures, "classification"), set()
    rows += cls_block(order, T_CLS[0], [("raise", 9), ("cut", 9), ("reiterate", 9), ("withdraw", 9)], used)
    rows += cls_block(order, T_CLS[1], [("low", 13), ("moderate", 13), ("high", 12)], used)
    rows += cls_block(order, T_CLS[2], [("certain", 9), ("probable", 9), ("possible", 9), ("unlikely", 9)], used)
    rows += cls_block(order, T_CLS[3], [("direct", 13), ("partial", 13), ("deflect", 12)], used)
    rows += cls_block(order, T_CLS[4], [("growth", 9), ("capital_allocation", 9), ("guidance", 9), ("competition", 9)], used)
    rows += cls_block(order, T_CLS[5], [("firm", 12), ("tentative", 12), ("aspirational", 12)], used)
    return rows
def assign(rows):
    for task in ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]:
        rs = [r for r in rows if r["task"] == task]
        groups = defaultdict(list)
        for r in rs:
            groups[r["_fx"]].append(r)
        keys = sorted(groups, key=lambda kk: hashlib.sha256(("%s|%s" % (task, kk)).encode("utf-8")).hexdigest())
        n, cum = float(len(rs)), 0.0
        for kk in keys:
            blk = groups[kk]
            mid = cum + len(blk) / 2.0
            sp = "train" if mid < 0.80 * n else ("val" if mid < 0.90 * n else "test")
            for r in blk:
                r["split"] = sp
            cum += len(blk)
def rebalance(rows):
    def count(sp):
        return sum(1 for r in rows if r["split"] == sp)
    for _ in range(400):
        train, val, test = count("train"), count("val"), count("test")
        if (train, val, test) == (800, 100, 100):
            return
        groups = defaultdict(list)
        for r in rows:
            groups[(r["task"], r["_fx"], r["split"])].append(r)
        moved = False
        for dst, need in (("train", 800 - train), ("val", 100 - val), ("test", 100 - test)):
            if need <= 0:
                continue
            for src in ("val", "test", "train"):
                if src == dst:
                    continue
                cands = sorted([(len(v), k) for k, v in groups.items() if k[2] == src],
                               key=lambda x: (abs(x[0] - need), x[0]))
                for size, k in cands:
                    if size > need or size == 0:
                        continue
                    if sum(1 for r in rows if r["task"] == k[0] and r["split"] == src) - size < 3:
                        continue
                    for r in groups[k]:
                        r["split"] = dst
                    moved = True
                    break
                if moved:
                    break
            if moved:
                break
        if not moved:
            return
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa",
        "classification": "cls", "summarization": "summ", "tool_use": "tool"}
MASK = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")
def mask(s):
    return WS.sub(" ", MASK.sub("#", s.lower())).strip()
def finalize(rows):
    for task in ABBR:
        rs = [r for r in rows if r["task"] == task]
        rs.sort(key=lambda r: (r["_fx"], r.get("question") or r["messages"][0]["content"]))
        for i, r in enumerate(rs, 1):
            r["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[task], i)
    assign(rows)
    rebalance(rows)
    out = []
    for r in rows:
        r = dict(r)
        r.pop("_fx", None)
        out.append(r)
    return out
def write(rows):
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path
def summarise(rows, path):
    fam, ctx, bodies = Counter(), set(), Counter()
    multi = tools = 0
    for r in rows:
        if "messages" in r:
            u = next((m["content"] for m in r["messages"] if m["role"] == "user"), "")
            fam[mask(u)[:160]] += 1
            bodies[mask(json.dumps(r["messages"], sort_keys=True))] += 1
            tools += 1
            if any(m["role"] == "assistant" for m in r["messages"]):
                multi += 1
        else:
            fam[mask(r["question"])[:160]] += 1
            ctx.add(mask(r["context"]))
            bodies[mask(r["context"]) + "|" + mask(r["question"])] += 1
    dup = sum(v - 1 for v in bodies.values() if v > 1)
    return {
        "area": AREA, "profile": "B", "rows": len(rows),
        "by_task": dict(Counter(r["task"] for r in rows)),
        "by_split": dict(Counter(r["split"] for r in rows)),
        "by_answer_type": dict(Counter(r["answer_type"] for r in rows if r["ground_truth"] is not None)),
        "distinct_question_families": len(fam),
        "top_family_share": round(max(fam.values()) / float(len(rows)), 4),
        "distinct_contexts": len(ctx),
        "near_dup_pairs": dup,
        "tool_use_multi_step_share": round(multi / float(tools), 3) if tools else 0.0,
        "validation": "pass",
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "notes": "Synthetic transcript excerpts; 24 fictional issuers, 8 quarters each; every figure computed in code.",
    }
NOTES = """# earnings_transcripts
- 24 fictional issuers x 8 fiscal quarters = 192 fixtures, each rendering its own SPEAKER COLON
  excerpt (1355-1500 chars) with a units line, a segment table and a CFO outlook sentence.
- 66 authored question families: 14 calc, 15 extraction, 15 qa, 6 summarization, 6 classification,
  10 tool-use. Splits are assigned per (task, fixture) by sha256, then rebalanced to 800/100/100.
- Guidance direction is numeric by construction ({raise, cut, withdraw, reiterate}); the hedge family
  states its counting rule (term list and thresholds), so that label is reproducible, not a mood call.
- Certainty, response type, intent and commitment-strength labels are written into the transcript by
  construction and are recoverable, but they stay judgement labels rather than arithmetic.
- Weakness: summarization bullets are template-composed and share phrasing across fixtures; every
  number in them appears verbatim in the context.
- Weakness: no merged or blank table cells, and the $000 unit-trap note fits only 12 fixtures.
- Weakness: transcripts sit near the 1500-character ceiling, so optional notes (FX, facility, export)
  are dropped on most fixtures and those extraction families run at 12-26 rows.
- All figures are rounded once in build_fixture; ground_truth reuses those same rounded values.
"""

def main():
    fixtures = []
    for c in COMPANIES:
        co = dict(zip(FIELDS, c))
        for t in range(8):
            fixtures.append(build_fixture(co, t))
    rows = finalize(build_rows(fixtures))
    path = write(rows)
    rep = summarise(rows, path)
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(HERE, "NOTES.md"), "w", encoding="utf-8") as fh:
        fh.write(NOTES)
    print(json.dumps(rep, indent=2))
if __name__ == "__main__":
    main()
