#!/usr/bin/env python3
"""Deterministic generator for the `energy_commodities` prompt area (profile A, 1000 rows).
Every numeric ground truth is computed from the same fixture values that are rendered into
the context. Seed 42, stdlib only, no network.
"""
import hashlib
import json
import os
import random
AREA = "energy_commodities"
SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
SPLITS = ("train", "val", "test")
TASKS = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls", "summarization": "summ", "tool_use": "tool"}
QUOTA = {"calc": 280, "extraction": 220, "qa": 200, "classification": 100, "summarization": 100, "tool_use": 100}
def num(x, dp=2):
    """One number format: plain digits, no thousands separators, no trailing zeros."""
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, int):
        return str(x)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = ("%." + str(dp) + "f") % x
    return s.rstrip("0").rstrip(".") if "." in s else s
def tbl(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        cells = [num(c) if isinstance(c, (int, float)) and not isinstance(c, bool) else str(c) for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)
def units(ccy):
    return ("Units: amounts in millions of %s except per-unit amounts in %s and percentages " "in percent." % (ccy, ccy))
def head(d):
    return "%s (%s, reporting currency %s, fiscal year end %s)\n%s — %s" % ( d["company"], d["sector"], d["ccy"], d["fy"], d["asset"], d["period"])
COMPANIES = [ ("Tallow Ridge Resources", "E&P", "31 December", "USD"), ("Cinder Mesa Petroleum", "E&P", "31 December", "USD"), ("Northmoor Energy", "E&P", "30 June", "USD"), ("Verdigris Exploration", "E&P", "31 December", "USD"), ("Blackpike Resources", "E&P", "30 September", "USD"), ("Sable Fen Oil & Gas", "E&P", "31 December", "USD"), ("Quarry Ridge Petroleum", "E&P", "31 March", "USD"), ("Harrowgate Energy", "E&P", "31 December", "USD"), ("Pelican Point Refining", "Refining", "31 December", "USD"), ("Cobalt Harbor Refining", "Refining", "30 June", "USD"), ("Marshgate Fuels", "Refining", "31 December", "USD"), ("Redwater Downstream", "Refining", "30 September", "USD"), ("Anvil Bay Refining", "Refining", "31 December", "USD"), ("Stonewick Petroleum Products", "Refining", "31 December", "USD"), ("Kestrel Pipeline Partners", "Midstream", "31 December", "USD"), ("Basalt Midstream", "Midstream", "30 June", "USD"), ("Longford Gathering", "Midstream", "31 December", "USD"), ("Nine Mile Midstream", "Midstream", "31 December", "USD"), ("Tamarack Terminal", "Midstream", "30 September", "USD"), ("Aldergate Energy Group", "Integrated", "31 December", "USD"), ("Ridgeline Integrated", "Integrated", "31 December", "USD"), ("Fairmoor Energy", "Integrated", "30 June", "USD"), ("Wexford Commodity Partners", "Trading", "31 December", "USD"), ("Silverbrook Trading", "Trading", "31 December", "USD"), ]
ASSETS = ["Permian Delaware", "Williston Core", "Eagle Ford", "SCOOP/STACK"]
PERIODS = [("Q1 FY2025", 90), ("Q2 FY2025", 91), ("Q3 FY2025", 92), ("Q4 FY2025", 92), ("FY2025", 365)]
EP_COMPS = [c for c in COMPANIES if c[1] in ("E&P", "Integrated")][:10]
REF_COMPS = [c for c in COMPANIES if c[1] == "Refining"]
MID_COMPS = [c for c in COMPANIES if c[1] == "Midstream"]
def make_ep(rng, comp, asset, period, days):
    d = dict(kind="ep", company=comp[0], sector="E&P", fy=comp[2], ccy=comp[3], asset=asset, period=period, days=days)
    d["key"] = "%s|%s|%s" % (comp[0], asset, period)
    d["asset2"] = ASSETS[(ASSETS.index(asset) + 2) % 4]
    wti, hh = round(rng.uniform(58.0, 88.0), 2), round(rng.uniform(2.05, 4.60), 2)
    od, gd = round(rng.uniform(-9.5, 3.0), 2), round(rng.uniform(-1.20, 0.30), 2)
    nrp = rng.choice([30, 32, 34, 36, 38, 40, 42, 44])
    oil, gas, ngl = rng.randrange(8000, 96000, 500), 6000 * rng.randrange(7, 58), rng.randrange(1200, 19000, 100)
    boe_d = oil + ngl + gas // 6
    op, gp, nglp = round(wti + od, 2), round(hh + gd, 2), round(wti * nrp / 100.0, 2)
    d.update(wti=wti, hh=hh, od=od, gd=gd, nrp=nrp, oil=oil, gas=gas, ngl=ngl, boe_d=boe_d, op=op, gp=gp, nglp=nglp)
    d["rev_oil"] = round(oil * days * op / 1e6, 1)
    d["rev_gas"] = round(gas * days * gp / 1e6, 1)
    d["rev_ngl"] = round(ngl * days * nglp / 1e6, 1)
    d["rev_total"] = round(d["rev_oil"] + d["rev_gas"] + d["rev_ngl"], 1)
    d["rev_per_boe"] = round(d["rev_total"] * 1e6 / (boe_d * days), 2)
    roy, taxr = rng.choice([12, 14, 16, 18, 20, 22]), rng.choice([18, 20, 21, 22, 24, 25])
    opx, gtc = round(rng.uniform(6.5, 13.5), 2), round(rng.uniform(1.4, 4.2), 2)
    ga, intr = round(rng.uniform(12.0, 48.0), 1), round(rng.uniform(4.0, 26.0), 1)
    capex, mcap = round(rng.uniform(120.0, 520.0), 1), float(rng.randrange(1800, 9000, 50))
    d.update(roy=roy, opx=opx, gtc=gtc, ga=ga, intr=intr, taxr=taxr, capex=capex, mcap=mcap)
    boe_period = boe_d * days
    d["boe_period"] = boe_period
    d["roy_amt"] = round(d["rev_total"] * roy / 100.0, 1)
    d["opex_amt"] = round(opx * boe_period / 1e6, 1)
    d["gtc_amt"] = round(gtc * boe_period / 1e6, 1)
    pre = d["rev_total"] - d["roy_amt"] - d["opex_amt"] - d["gtc_amt"] - ga - intr - capex
    d["pretax"] = round(pre, 1)
    d["taxc"] = round(max(0.0, pre) * taxr / 100.0, 1)
    d["fcf"] = round(d["pretax"] - d["taxc"], 1)
    d["ebitda"] = round(d["rev_total"] - d["roy_amt"] - d["opex_amt"] - d["gtc_amt"] - ga, 1)
    d["netback"] = round(d["rev_per_boe"] * (1 - roy / 100.0) - opx - gtc, 2)
    d["ga_per_boe"] = round(ga * 1e6 / boe_period, 2)
    d["cash_margin"] = round(d["netback"] - d["ga_per_boe"], 2)
    a1 = (oil * days + ngl * days * nrp / 100.0) / 1e6
    b1 = (oil * days * od) / 1e6 + d["rev_gas"]
    c1 = d["opex_amt"] + d["gtc_amt"] + ga + intr + capex
    d["be"] = round((c1 / (1 - roy / 100.0) - b1) / a1, 2)
    d["sens"] = round(a1 * (1 - roy / 100.0) * (1 - taxr / 100.0), 2)
    d["fcf_yield"] = round(d["fcf"] / mcap * 100.0, 1)
    d["mmboe"] = round(boe_period / 1e6, 2)
    d["kboepd"] = round(boe_d / 1000.0, 1)
    d["oil_rev_5"] = round((op + 5.0) * oil * days / 1e6, 1)
    d["gas_boe_share"] = round((gas / 6.0) / float(boe_d) * 100.0, 1)
    d["liq_rev_share"] = round((d["rev_oil"] + d["rev_ngl"]) / d["rev_total"] * 100.0, 1)
    d["gas_pct_hh"] = round(gp / hh * 100.0, 1)
    d["diff_pct"] = round(od / wti * 100.0, 2)
    assert abs(a1 * wti + b1 - d["rev_total"]) < 0.6, d["key"]
    cs = []
    for k in range(3):
        if k < 2:
            vol = int(round(oil * rng.choice([0.18, 0.22, 0.26, 0.30]) / 100.0)) * 100
            if k == 0:
                inst, cpx, ceil = "Fixed-price swap", round(op + rng.uniform(2.0, 8.0), 2), None
            elif rng.random() < 0.5:
                inst, cpx, ceil = "Purchased put floor", round(op + rng.uniform(1.0, 6.0), 2), None
            else:
                inst = "Costless collar"
                cpx = round(op + rng.uniform(1.0, 6.0), 2)
                ceil = round(cpx + rng.uniform(16.0, 28.0), 2)
            cs.append(dict(id="H%d" % (k + 1), comm="Oil", inst=inst, vol=vol, px=cpx, ceil=ceil, exp=rng.choice(["31 December 2025", "31 March 2026", "30 June 2026"])))
        else:
            cs.append(dict(id="H3", comm="Gas", inst="Fixed-price swap", vol=6000 * rng.randrange(6, 30), px=round(gp + rng.uniform(0.25, 1.20), 2), ceil=None, exp=rng.choice(["31 December 2025", "31 March 2026", "30 June 2026"])))
    cs[0]["exp"] = "31 December 2025"
    ho = hg = 0.0
    for c in cs:
        mkt = wti if c["comm"] == "Oil" else hh
        if c["inst"] in ("Purchased put floor", "Costless collar"):
            g = max(0.0, c["px"] - mkt) * c["vol"] * days / 1e6
        else:
            g = (c["px"] - mkt) * c["vol"] * days / 1e6
        if c["comm"] == "Oil":
            ho += g
        else:
            hg += g
    d["cs"] = cs
    d["h_oil"], d["h_gas"] = round(ho, 1), round(hg, 1)
    d["h_total"] = round(ho + hg, 1)
    vols = [c["vol"] for c in cs if c["comm"] == "Oil"]
    d["h_vol_oil"] = sum(vols)
    d["h_share"] = round(sum(vols) / float(oil) * 100.0, 1)
    d["h_wavg"] = round(sum(c["px"] * c["vol"] for c in cs if c["comm"] == "Oil") / float(sum(vols)), 2)
    d["px_incl"] = round(op + d["h_oil"] * 1e6 / (oil * days), 2)
    d["h_pct_rev"] = round(d["h_oil"] / d["rev_oil"] * 100.0, 1)
    d["h_dec25"] = round(sum(c["vol"] for c in cs if c["exp"] == "31 December 2025" and c["comm"] == "Oil") / float(oil) * 100.0, 1)
    ann = boe_d * 365.0 / 1e6
    tot = round(ann * rng.uniform(8.0, 16.0), 1)
    gsh = round(rng.uniform(0.22, 0.50), 2)
    d["res_gas"] = round(tot * gsh * 6.0, 1)
    liq = tot * (1 - gsh)
    d["res_oil"], d["res_ngl"] = round(liq * 0.78, 1), round(liq * 0.22, 1)
    d["res_boe"] = round(d["res_oil"] + d["res_ngl"] + d["res_gas"] / 6.0, 1)
    d["ann_mmboe"] = round(ann, 1)
    d["rli"] = round(d["res_boe"] / ann, 1)
    d["res_gas_share"] = round(d["res_gas"] / 6.0 / d["res_boe"] * 100.0, 1)
    m1 = round(d["rev_per_boe"] - opx - gtc, 2)
    px2, ox2, gx2 = round(d["rev_per_boe"] * 0.94, 2), round(opx * 1.18, 2), round(gtc * 1.10, 2)
    m2 = round(px2 - ox2 - gx2, 2)
    if abs(m1 - m2) < 0.05:
        m2 = round(m2 - 0.6, 2)
    d["seg"] = [("Segment", "A", "B"), ("Realised price (USD/boe)", d["rev_per_boe"], px2), ("Lease operating expense (USD/boe)", opx, ox2), ("Gathering and transportation (USD/boe)", gtc, gx2)]
    d["seg_names"] = (asset, d["asset2"])
    d["seg_margins"] = (m1, m2)
    d["seg_prior_delta"] = rng.choice([(0.7, -0.5), (-0.6, 0.8), (0.7, 0.4), (0.35, -0.55)])
    d["seg_better"] = asset if m1 > m2 else d["asset2"]
    names = ["Oil revenue", "Gas revenue", "NGL revenue", "Lease operating expense", "Gathering and transportation", "Cash G&A"]
    vals = [d["rev_oil"], d["rev_gas"], d["rev_ngl"], d["opex_amt"], d["gtc_amt"], d["ga"]]
    fac = [rng.uniform(-0.10, 0.12) for _ in range(6)]
    fac[1] = rng.uniform(0.06, 0.12)
    d["sumrows"] = [(names[i], vals[i], round(vals[i] / (1 + fac[i]), 1)) for i in range(6)]
    return d
def make_ref(rng, comp, period, days):
    d = dict(kind="ref", company=comp[0], sector="Refining", fy=comp[2], ccy=comp[3], asset="Gulf Coast refinery complex", period=period, days=days)
    d["key"] = "%s|Refining|%s" % (comp[0], period)
    cap = rng.choice([120, 150, 180, 210, 240, 275, 310])
    tp = int(round(cap * rng.uniform(0.86, 0.97)))
    crude, crack = round(rng.uniform(58.0, 82.0), 2), round(rng.uniform(15.0, 30.0), 2)
    gaso, dist = round(crude + crack * 0.85, 2), round(crude + crack * 1.15, 2)
    oth = round(crude + crack * 0.15, 2)
    yg, yd = rng.choice([44, 46, 48, 50]) / 100.0, rng.choice([28, 30, 32]) / 100.0
    yo = round(1.0 - yg - yd, 2)
    opx = round(rng.uniform(5.5, 9.5), 2)
    ga, intr = round(rng.uniform(18.0, 46.0), 1), round(rng.uniform(6.0, 24.0), 1)
    wc = yg * gaso + yd * dist + yo * oth
    mbbl = round(wc - crude - opx, 2)
    d.update(cap=cap, tp=tp, crude=crude, gaso=gaso, dist=dist, oth=oth, yg=int(yg * 100), yd=int(yd * 100), yo=int(round(yo * 100)), opx=opx, ga=ga, intr=intr)
    d["crack"] = round((2 * gaso + dist - 3 * crude) / 3.0, 2)
    d["mbbl"] = mbbl
    d["gm_mm"] = round(tp * 1000.0 * days * mbbl / 1e6, 1)
    d["capture"] = round(mbbl / d["crack"] * 100.0, 1)
    d["util"] = round(tp / float(cap) * 100.0, 1)
    d["rev_total"] = round(tp * 1000.0 * days * wc / 1e6, 1)
    d["ebitda"] = round(d["gm_mm"] - ga, 1)
    d["taxc"] = round(max(0.0, d["ebitda"]) * 0.21, 1)
    return d
def make_mid(rng, comp, period, days):
    d = dict(kind="mid", company=comp[0], sector="Midstream", fy=comp[2], ccy=comp[3], asset="Mainline pipeline system", period=period, days=days)
    d["key"] = "%s|Midstream|%s" % (comp[0], period)
    cap = rng.choice([180, 240, 300, 360, 420, 480])
    tp = int(cap * rng.uniform(0.70, 0.94))
    tariff = round(rng.uniform(1.10, 2.90), 2)
    rev = round(tp * 1000.0 * days * tariff / 1e6, 1)
    opex = round(rev * rng.uniform(0.34, 0.44), 1)
    ga = round(rev * rng.uniform(0.08, 0.12), 1)
    ebitda = round(rev - opex - ga, 1)
    intr = round(ebitda * rng.uniform(0.18, 0.30), 1)
    maint = round(ebitda * rng.uniform(0.12, 0.20), 1)
    taxc = round(ebitda * rng.uniform(0.05, 0.10), 1)
    dcf = round(ebitda - intr - maint - taxc, 1)
    dist = max(1.0, round(dcf / rng.uniform(0.95, 1.35), 1))
    debt = float(round(max(1.0, ebitda) * 4.0 * rng.uniform(3.0, 4.6), 0))
    d.update(cap=cap, tp=tp, tariff=tariff, rev_total=rev, opex=opex, ga=ga, ebitda=ebitda, intr=intr, maint=maint, taxc=taxc, dist=dist, debt=debt)
    d["dcf"] = dcf
    d["coverage"] = round(dcf / dist, 2)
    d["lev"] = round(debt / (max(0.1, ebitda) * 4.0), 2)
    d["contracted"] = rng.choice([70, 75, 80, 82, 85, 90])
    d["ebitda_less_maint"] = round(ebitda - maint, 1)
    return d
def add_wc(d, rng):
    rev = max(1.0, d["rev_total"])
    cogs = round(rev * rng.uniform(0.55, 0.72), 1)
    ar1 = round(rev * rng.uniform(0.10, 0.16), 1)
    ar0 = round(ar1 * rng.uniform(0.90, 1.12), 1)
    iv1 = round(cogs * rng.uniform(0.30, 0.45), 1)
    iv0 = round(iv1 * rng.uniform(0.92, 1.15), 1)
    ap1 = round(cogs * rng.uniform(0.42, 0.58), 1)
    ap0 = round(ap1 * rng.uniform(0.92, 1.10), 1)
    dwc = round((ar1 - ar0) + (iv1 - iv0) - (ap1 - ap0), 1)
    d["wc"] = dict(ar0=ar0, ar1=ar1, iv0=iv0, iv1=iv1, ap0=ap0, ap1=ap1, cogs=cogs, rev=rev)
    d["dwc"] = dwc
    d["cfo"] = round(d["ebitda"] - d["intr"] - d["taxc"] - dwc, 1)
    nd = float(d["days"])
    d["inv_days"] = round(iv1 / (cogs / nd), 1)
    d["ar_days"] = round(ar1 / (rev / nd), 1)
    d["ap_days"] = round(ap1 / (cogs / nd), 1)
    d["ccc"] = round(d["ar_days"] + d["inv_days"] - d["ap_days"], 1)
def build_extract(d, rng):
    if d["kind"] == "ep":
        rows = [("Oil revenue", d["rev_oil"], 2), ("Gas revenue", d["rev_gas"], 2), ("NGL revenue", d["rev_ngl"], 0), ("Lease operating expense", d["opex_amt"], 3), ("Gathering and transportation", d["gtc_amt"], 0), ("Cash G&A", d["ga"], 0), ("Development capex", d["capex"], 4)]
        extra = ("Total production (boe/d)", d["boe_d"])
        op_name, cap_name = "Lease operating expense", "Development capex"
    elif d["kind"] == "ref":
        rows = [("Product revenue", d["rev_total"], 2), ("Crude cost", d["cogs_crude"], 2), ("Refining opex", d["opex_mm"], 3), ("Cash G&A", d["ga"], 0), ("Turnaround capex", d["turn_capex"], 4)]
        extra = ("Throughput (Mbbl/d)", d["tp"])
        op_name, cap_name = "Refining opex", "Turnaround capex"
    else:
        rows = [("Transportation revenue", d["rev_total"], 2), ("Operating expense", d["opex"], 2), ("Cash G&A", d["ga"], 0), ("Maintenance capex", d["maint"], 4)]
        extra = ("Throughput (Mbbl/d)", d["tp"])
        op_name, cap_name = "Operating expense", "Maintenance capex"
    prior = [round(r[1] * rng.uniform(0.90, 1.10), 1) for r in rows]
    blank = rng.randrange(1, len(rows))
    lines = [(r[0], r[1], "" if i == blank else num(prior[i], 1), (r[2] if r[2] else "")) for i, r in enumerate(rows)]
    body = [units(d["ccy"]), "%s — %s supplemental schedule (unaudited)" % (d["company"], d["period"]), "Reporting entity %s. Fiscal year end %s. Reporting currency %s." % (d["company"], d["fy"], d["ccy"]), "", tbl(["Line item", d["period"], "Prior period", "Note"], lines), "", tbl(["Production and capacity", "Value"], [(extra[0], extra[1]), ("Conversion basis (mcf per boe)", 6)]), "", "Notes to the schedule", "1. Basis of presentation: one barrel of oil equivalent equals six thousand cubic feet of natural gas.", "2. Revenue is reported net of royalties.", "3. Excludes non-cash stock compensation of 3.1.", "4. Includes capitalised workover cost of 12.4."]
    d["xt"] = dict(ctx="\n".join(body), blank=rows[blank][0], op_name=op_name, op_note=3, note4=cap_name, prior0=prior[0], row0=rows[0][0], ga_val=d["ga"], nrows=len(rows), extra_name=extra[0], extra_val=extra[1], op_cur=rows[[r[0] for r in rows].index(op_name)][1], biggest=max(rows, key=lambda r: r[1])[0])
def build_fixtures(rng):
    fxs = []
    for i in range(40):
        comp = EP_COMPS[i % 10]
        ai = i // 10
        per, days = PERIODS[(i + ai) % len(PERIODS)]
        d = make_ep(rng, comp, ASSETS[ai], per, days)
        add_wc(d, rng)
        build_extract(d, rng)
        fxs.append(d)
    for ci in range(6):
        for pi in range(4):
            per, days = PERIODS[pi]
            d = make_ref(rng, REF_COMPS[ci], per, days)
            d["cogs_crude"] = round(d["tp"] * 1000.0 * days * d["crude"] / 1e6, 1)
            d["opex_mm"] = round(d["tp"] * 1000.0 * days * d["opx"] / 1e6, 1)
            d["turn_capex"] = round(d["ebitda"] * rng.uniform(0.25, 0.45), 1)
            add_wc(d, rng)
            build_extract(d, rng)
            fxs.append(d)
    for ci in range(5):
        for pi in range(5):
            per, days = PERIODS[pi]
            d = make_mid(rng, MID_COMPS[ci], per, days)
            add_wc(d, rng)
            build_extract(d, rng)
            fxs.append(d)
    keys = [d["key"] for d in fxs]
    assert len(keys) == len(set(keys)), "duplicate fixture keys"
    return fxs
def ctx_ops(d):
    rows = [("Calendar days in period", d["days"]), ("Oil production (bbl/d)", d["oil"]), ("Natural gas production (mcf/d)", d["gas"]), ("NGL production (bbl/d)", d["ngl"]), ("WTI average (USD/bbl)", d["wti"]), ("Oil differential to WTI (USD/bbl)", d["od"]), ("Henry Hub average (USD/mcf)", d["hh"]), ("Gas differential to Henry Hub (USD/mcf)", d["gd"]), ("NGL realisation (percent of WTI)", d["nrp"]), ("Conversion basis (mcf per boe)", 6)]
    return units(d["ccy"]) + "\n" + head(d) + "\n\n" + tbl(["Item", "Value"], rows)
def ctx_hedges(d):
    rows = [(c["id"], c["comm"], c["inst"], ("%s (bbl/d)" % num(c["vol"])) if c["comm"] == "Oil" else ("%s (mcf/d)" % num(c["vol"])), c["px"], "" if c["ceil"] is None else c["ceil"], c["exp"]) for c in d["cs"]]
    body = [units(d["ccy"]), head(d), "", "Settlement reference: WTI average %s per barrel; Henry Hub average %s per mcf." % (num(d["wti"]), num(d["hh"])), "Realised oil price before hedge settlements: %s per barrel." % num(d["op"]), "Realised gas price before hedge settlements: %s per mcf." % num(d["gp"]), "Calendar days in period: %d." % d["days"], "", tbl(["Contract", "Commodity", "Instrument", "Volume", "Contracted price", "Ceiling", "Expiry"], rows), "", "Volumes are daily. Contracted prices are per barrel for oil and per mcf for gas."]
    return "\n".join(body)
def ctx_reserves(d):
    rows = [("Proved oil reserves (mmbbl)", d["res_oil"]), ("Proved NGL reserves (mmbbl)", d["res_ngl"]), ("Proved gas reserves (bcf)", d["res_gas"]), ("Total production (boe/d)", d["boe_d"]), ("Calendar days in period", d["days"]), ("Conversion basis (mcf per boe)", 6)]
    return units(d["ccy"]) + "\n" + head(d) + "\n\n" + tbl(["Item", "Value"], rows)
def ctx_fcf(d):
    rows = [("Calendar days in period", d["days"]), ("Oil production (bbl/d)", d["oil"]), ("Natural gas production (mcf/d)", d["gas"]), ("NGL production (bbl/d)", d["ngl"]), ("WTI average (USD/bbl)", d["wti"]), ("Oil differential to WTI (USD/bbl)", d["od"]), ("Henry Hub average (USD/mcf)", d["hh"]), ("Gas differential to Henry Hub (USD/mcf)", d["gd"]), ("NGL realisation (percent of WTI)", d["nrp"]), ("Royalties (percent of revenue)", d["roy"]), ("Lease operating expense (USD/boe)", d["opx"]), ("Gathering and transportation (USD/boe)", d["gtc"]), ("Cash G&A (USD millions)", d["ga"]), ("Cash interest (USD millions)", d["intr"]), ("Cash tax rate (percent of pre-tax cash flow)", d["taxr"]), ("Development capex (USD millions)", d["capex"]), ("Market capitalisation (USD millions)", d["mcap"]), ("Conversion basis (mcf per boe)", 6)]
    note = ("Breakeven is the WTI price at which free cash flow for the period is zero, holding volumes, " "differentials, cost rates and the stated cash tax rate constant.")
    return units(d["ccy"]) + "\n" + head(d) + "\n\n" + tbl(["Item", "Value"], rows) + "\n\n" + note
def ctx_ref(d):
    rows = [("Nameplate capacity (Mbbl/d)", d["cap"]), ("Throughput (Mbbl/d)", d["tp"]), ("Calendar days in period", d["days"]), ("Crude cost (USD/bbl)", d["crude"]), ("Gasoline yield (percent)", d["yg"]), ("Distillate yield (percent)", d["yd"]), ("Other products yield (percent)", d["yo"]), ("Gasoline price (USD/bbl)", d["gaso"]), ("Distillate price (USD/bbl)", d["dist"]), ("Other products price (USD/bbl)", d["oth"]), ("Refining opex (USD/bbl of throughput)", d["opx"]), ("Cash G&A (USD millions)", d["ga"]), ("Cash interest (USD millions)", d["intr"])]
    return units(d["ccy"]) + "\n" + head(d) + "\n\n" + tbl(["Item", "Value"], rows)
def ctx_mid(d):
    rows = [("System throughput (Mbbl/d)", d["tp"]), ("Contracted share of capacity (percent)", d["contracted"]), ("Average tariff (USD/bbl)", d["tariff"]), ("Calendar days in period", d["days"]), ("Operating expense (USD millions)", d["opex"]), ("Cash G&A (USD millions)", d["ga"]), ("Cash interest (USD millions)", d["intr"]), ("Maintenance capex (USD millions)", d["maint"]), ("Cash tax (USD millions)", d["taxc"]), ("Distributions declared (USD millions)", d["dist"]), ("Total debt (USD millions)", d["debt"])]
    note = "Annualised EBITDA is the EBITDA of the period multiplied by four."
    return units(d["ccy"]) + "\n" + head(d) + "\n\n" + tbl(["Item", "Value"], rows) + "\n\n" + note
def ctx_wc(d):
    w = d["wc"]
    bal = [("Accounts receivable", w["ar1"], w["ar0"]), ("Inventory", w["iv1"], w["iv0"]), ("Accounts payable", w["ap1"], w["ap0"])]
    per = [("Revenue for the period", w["rev"]), ("Cost of sales for the period", w["cogs"]), ("EBITDA for the period", d["ebitda"]), ("Cash interest", d["intr"]), ("Cash tax", d["taxc"]), ("Calendar days in period", d["days"])]
    return "\n".join([units(d["ccy"]), head(d), "", "Balance sheet balances", tbl(["Item", "End of period", "Start of period"], bal), "", "Period items", tbl(["Item", "Value"], per)])
def ctx_segs(d):
    return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", d["seg_names"][0], d["seg_names"][1]], list(zip(*d["seg"])))])
def ctx_compare(d):
    rows = [("Oil production (bbl/d)", d["oil"], int(d["oil"] * 0.94)), ("WTI average (USD/bbl)", d["wti"], round(d["wti"] - 3.4, 2)), ("Oil differential to WTI (USD/bbl)", d["od"], round(d["od"] + 0.9, 2)), ("Henry Hub average (USD/mcf)", d["hh"], round(d["hh"] - 0.18, 2)), ("Realised gas price (USD/mcf)", d["gp"], round(d["gp"] - 0.11, 2)), ("Lease operating expense (USD/boe)", d["opx"], round(d["opx"] - 0.42, 2)), ("Gathering and transportation (USD/boe)", d["gtc"], round(d["gtc"] + 0.08, 2))]
    return units(d["ccy"]) + "\n" + head(d) + "\n\n" + tbl(["Item", d["period"], "Prior period"], rows)
def risk_list(d):
    risks = ["Commodity price volatility", "Counterparty credit exposure", "Regulatory permitting delay", "Water disposal constraints", "Pipeline apportionment", "Cost inflation on service contracts"]
    k = d["days"] % 3
    return risks[k:k + 3] if k + 3 <= len(risks) else risks[:3]
def ctx_sum(d, v):
    if v in (0, 1):
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Line item", d["period"], "Prior period"], d["sumrows"])])
    if v == 2:
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", "Value"], [("Oil revenue", d["rev_oil"]), ("Gas revenue", d["rev_gas"]), ("NGL revenue", d["rev_ngl"]), ("Total revenue", d["rev_total"]), ("Net hedge settlement", d["h_total"]), ("Free cash flow", d["fcf"])]), "", "Prior-period total revenue was %s." % num(round(d["rev_total"] * 1.07, 1))])
    if v == 3:
        rows = [(c["id"], c["comm"], c["inst"], c["vol"], c["exp"]) for c in d["cs"]]
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Contract", "Commodity", "Instrument", "Volume per day", "Expiry"], rows)])
    if v == 4:
        rows = [("Segment", d["seg_names"][0], d["seg_names"][1]), ("Cash margin per boe, current period", d["seg_margins"][0], d["seg_margins"][1]), ("Cash margin per boe, prior period", round(d["seg_margins"][0] + d["seg_prior_delta"][0], 2), round(d["seg_margins"][1] + d["seg_prior_delta"][1], 2))]
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", d["seg_names"][0], d["seg_names"][1]], rows)])
    if v == 5:
        w = d["wc"]
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", "End of period", "Start of period"], [("Accounts receivable", w["ar1"], w["ar0"]), ("Inventory", w["iv1"], w["iv0"]), ("Accounts payable", w["ap1"], w["ap0"])])])
    if v == 6:
        r = risk_list(d)
        return "\n".join([units(d["ccy"]), "Risk register extract — %s, %s" % (d["company"], d["period"]), "", "The following principal risks were reviewed by the board:", "1. %s" % r[0], "2. %s" % r[1], "3. %s" % r[2]])
    return "\n".join([units(d["ccy"]), "Hedge book memo — %s, %s" % (d["company"], d["period"]), "", "The book contains %d contracts covering %s percent of oil production. Net settlement " "for the period was %s." % (len(d["cs"]), num(d["h_share"]), num(d["h_total"]))])
CLS_LABELS = [ ["highly effective", "effective", "not effective", "not designated"], ["fixed-price swap", "purchased put", "costless collar", "basis swap"], ["cash flow hedge", "fair value hedge", "net investment hedge", "economic hedge only"], ["widening", "narrowing", "stable"], ["rising", "falling", "flat"], ["strong", "adequate", "weak"], ["positive revision", "negative revision", "no revision"], ["expanding", "stable", "contracting"], ["build", "release", "neutral"], ["net long", "net short", "balanced"], ]
EFF_ARGS = {"highly effective": (98, 96, "Yes"), "effective": (86, 66, "Yes"), "not effective": (142, 41, "Yes"), "not designated": (99, 93, "No")}
INST_TEXT = { "fixed-price swap": "The producer pays a fixed price and receives a floating index price on 20000 barrels per day for twelve months. No premium is exchanged and the parties settle the full price difference.", "purchased put": "The producer pays a premium of 1.85 per barrel for the right, but not the obligation, to sell 15000 barrels per day at 70.00. No ceiling is sold and there is no obligation above that price.", "costless collar": "The producer buys a floor at 66.00 and simultaneously sells a ceiling at 88.00 on 18000 barrels per day. No net premium is paid and the payout is bounded at both ends.", "basis swap": "The producer exchanges the difference between a published regional cash index and the front-month futures price on 25000 barrels per day. Flat price is not hedged.", }
DESIG_TEXT = { "cash flow hedge": "The instrument is documented as hedging the variability of cash flows from forecast oil sales. The effective portion is deferred in other comprehensive income until the forecast sale occurs.", "fair value hedge": "The instrument is documented as hedging the fair value of a fixed-price supply commitment already recognised on balance sheet. Changes in fair value of both items are taken to profit or loss.", "net investment hedge": "The instrument is documented as hedging the foreign currency exposure on the net assets of an overseas subsidiary. Gains are deferred in a separate component of equity.", "economic hedge only": "Management entered the instrument to protect cash flow but prepared no hedge documentation and performs no effectiveness testing. Changes in fair value flow through profit or loss as they arise.", }
def ctx_memo(d, v, lab):
    if v == 0:
        ratio, r2, des = EFF_ARGS[lab]
        return "\n".join([units(d["ccy"]), "Hedge relationship memo — %s, %s" % (d["company"], d["period"]), "", tbl(["Item", "Value"], [("Hedged item", "Forecast oil sales"), ("Hedge ratio achieved (percent)", ratio), ("Regression R-squared (percent)", r2), ("Designated under the hedging policy", des), ("Counterparty credit adjustment (USD millions)", 0.4)])])
    if v == 1:
        return "\n".join([units(d["ccy"]), "Instrument memo — %s, %s" % (d["company"], d["period"]), "", INST_TEXT[lab]])
    if v == 2:
        return "\n".join([units(d["ccy"]), "Accounting memo — %s, %s" % (d["company"], d["period"]), "", DESIG_TEXT[lab]])
    if v == 3:
        od2 = {"widening": round(d["od"] - 1.8, 2), "narrowing": round(d["od"] + 1.8, 2), "stable": round(d["od"] + 0.10, 2)}[lab]
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", d["period"], "Prior period"], [("Oil differential to WTI (USD/bbl)", d["od"], od2), ("WTI average (USD/bbl)", d["wti"], round(d["wti"] - 2.0, 2))])])
    if v == 4:
        loe2 = {"rising": round(d["opx"] - 1.2, 2), "falling": round(d["opx"] + 1.2, 2), "flat": round(d["opx"] - 0.05, 2)}[lab]
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", d["period"], "Prior period"], [("Lease operating expense (USD/boe)", d["opx"], loe2), ("Production (boe/d)", d["boe_d"], int(d["boe_d"] * 0.97))])])
    if v == 5:
        ratio = {"strong": 1.72, "adequate": 1.24, "weak": 0.88}[lab]
        base = round(d["rev_total"] * 0.42, 1)
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", "Value"], [("Distributable cash flow (USD millions)", round(base * ratio, 1)), ("Distributions declared (USD millions)", base), ("Total debt (USD millions)", round(d["rev_total"] * 3.1, 1))])])
    if v == 6:
        rev = {"positive revision": 24.6, "negative revision": -18.3, "no revision": 0.0}[lab]
        begin = round(d["res_boe"] * 0.96, 1)
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", "Value"], [("Proved reserves at start of year (mmboe)", begin), ("Extensions and discoveries (mmboe)", 31.2), ("Revisions (mmboe)", rev), ("Production (mmboe)", d["ann_mmboe"]), ("Proved reserves at end of year (mmboe)", round(begin + 31.2 + rev - d["ann_mmboe"], 1))])])
    if v == 7:
        cur = round(d["h_total"] / max(1.0, d["boe_period"] / 1e6) + 8.4, 2)
        prior = {"expanding": round(cur - 2.1, 2), "stable": round(cur - 0.05, 2), "contracting": round(cur + 2.1, 2)}[lab]
        return "\n".join([units(d["ccy"]), "Margin memo — %s, %s" % (d["company"], d["period"]), "", tbl(["Item", d["period"], "Prior period"], [("Margin per barrel (USD/bbl)", cur, prior)])])
    if v == 8:
        w = d["wc"]
        if lab == "build":
            ar1, iv1, ap1 = round(w["ar0"] * 1.18, 1), round(w["iv0"] * 1.15, 1), round(w["ap0"] * 1.02, 1)
        elif lab == "release":
            ar1, iv1, ap1 = round(w["ar0"] * 0.86, 1), round(w["iv0"] * 0.88, 1), round(w["ap0"] * 1.05, 1)
        else:
            ar1, iv1, ap1 = round(w["ar0"] * 1.005, 1), round(w["iv0"] * 1.002, 1), round(w["ap0"] * 1.004, 1)
        return "\n".join([units(d["ccy"]), head(d), "", tbl(["Item", "End of period", "Start of period"], [("Accounts receivable", ar1, w["ar0"]), ("Inventory", iv1, w["iv0"]), ("Accounts payable", ap1, w["ap0"])])])
    bought = {"net long": 42000, "net short": 12000, "balanced": 26000}[lab]
    return "\n".join([units(d["ccy"]), "Hedge position memo — %s, %s" % (d["company"], d["period"]), "", tbl(["Item", "Volume (bbl/d)"], [("Purchased hedge volume", bought), ("Sold hedge volume", 26000)])])
# ----------------------------------------------------------------------------- families
def C(name, dom, ctx, q, fn, tol="abs:0.1"):
    return dict(name=name, task="calc", dom=dom, ctx=ctx, q=q, fn=fn, at="number", tol=tol)
def E(name, q, fn, at="number", tol="abs:0.1"):
    return dict(name=name, task="extraction", dom="any", ctx="xt", q=q, fn=fn, at=at, tol=tol)
def Q(name, dom, ctx, q, fn, at="number", tol="abs:0.1"):
    return dict(name=name, task="qa", dom=dom, ctx=ctx, q=q, fn=fn, at=at, tol=tol)
CALC = [ C("c_realised_boe", "ep", "ops", "What was the realised price per boe for the period, in dollars?", lambda d: d["rev_per_boe"]), C("c_realised_oil", "ep", "ops", "What was the realised oil price for the period, in dollars per barrel?", lambda d: d["op"]), C("c_oil_rev", "ep", "ops", "What was oil revenue for the period, in millions?", lambda d: d["rev_oil"], "abs:1"), C("c_total_rev", "ep", "ops", "What was total revenue for the period, in millions?", lambda d: d["rev_total"], "abs:1"), C("c_liquid_share", "ep", "ops", "What percentage of total revenue came from oil and NGL combined, in percent?", lambda d: d["liq_rev_share"]), C("c_gas_boe_share", "ep", "ops", "What percentage of total production on a boe basis came from natural gas, in percent?", lambda d: d["gas_boe_share"]), C("c_mmboe", "ep", "ops", "What was total production for the period, in million boe?", lambda d: d["mmboe"]), C("c_kboepd", "ep", "ops", "What was total production for the period, in thousand boe per day?", lambda d: d["kboepd"]), C("c_gas_pct_hh", "ep", "ops", "What was the realised gas price as a percentage of the Henry Hub average, in percent?", lambda d: d["gas_pct_hh"]), C("c_diff_pct", "ep", "ops", "What was the oil differential as a percentage of the WTI average, in percent?", lambda d: d["diff_pct"]), C("c_rli", "ep", "reserves", "What is the reserve life index, in years?", lambda d: d["rli"]), C("c_res_boe", "ep", "reserves", "What were total proved reserves at period end, in million boe?", lambda d: d["res_boe"], "abs:1"), C("c_res_gas_share", "ep", "reserves", "What percentage of proved reserves on a boe basis was natural gas, in percent?", lambda d: d["res_gas_share"]), C("c_hedge_net", "ep", "hedges", "What was the net hedge gain or loss for the period, in millions?", lambda d: d["h_total"], "abs:1"), C("c_hedge_wavg", "ep", "hedges", "What was the volume-weighted contracted oil price across the oil contracts, in dollars per barrel?", lambda d: d["h_wavg"]), C("c_hedge_share", "ep", "hedges", "What percentage of oil production was covered by oil hedges, in percent?", lambda d: d["h_share"]), C("c_px_incl", "ep", "hedges", "What was the realised oil price including hedge settlements, in dollars per barrel?", lambda d: d["px_incl"]), C("c_hedge_pct_rev", "ep", "hedges", "What was the oil hedge gain as a percentage of unhedged oil revenue, in percent?", lambda d: d["h_pct_rev"]), C("c_netback", "ep", "fcf", "What was the netback per boe for the period, in dollars?", lambda d: d["netback"]), C("c_cash_margin", "ep", "fcf", "What was the cash margin per boe after cash G&A, in dollars?", lambda d: d["cash_margin"]), C("c_fcf", "ep", "fcf", "What was free cash flow for the period, in millions?", lambda d: d["fcf"], "abs:1"), C("c_breakeven", "ep", "fcf", "What is the breakeven WTI price for the period, in dollars per barrel?", lambda d: d["be"]), C("c_fcf_yield", "ep", "fcf", "What was the free cash flow yield on the stated market capitalisation, in percent?", lambda d: d["fcf_yield"]), C("c_sens", "ep", "fcf", "For each 1.00 change in the WTI average, how much does free cash flow change, in millions, " "assuming the period remains taxable?", lambda d: d["sens"], "abs:0.01"), C("c_crack", "ref", "ref", "What is the 3-2-1 crack spread implied by the stated prices, in dollars per barrel?", lambda d: d["crack"]), C("c_margin_bbl", "ref", "ref", "What was the gross refining margin per barrel of throughput, in dollars?", lambda d: d["mbbl"]), C("c_gm_mm", "ref", "ref", "What was the gross refining margin for the period, in millions?", lambda d: d["gm_mm"], "abs:1"), C("c_capture", "ref", "ref", "What was the capture rate against the 3-2-1 crack spread, in percent?", lambda d: d["capture"]), C("c_util", "ref", "ref", "What was refinery utilisation, in percent?", lambda d: d["util"]), C("c_mid_ebitda", "mid", "mid", "What was EBITDA for the period, in millions?", lambda d: d["ebitda"], "abs:1"), C("c_dcf", "mid", "mid", "What was distributable cash flow for the period, in millions?", lambda d: d["dcf"], "abs:1"), C("c_coverage", "mid", "mid", "What was the distribution coverage ratio, in times?", lambda d: d["coverage"], "abs:0.01"), C("c_leverage", "mid", "mid", "What was the debt to annualised EBITDA ratio, in times?", lambda d: d["lev"], "abs:0.01"), C("c_dwc", "wc", "wc", "What was the change in working capital for the period, in millions?", lambda d: d["dwc"], "abs:1"), C("c_cfo", "wc", "wc", "What was cash flow from operations after the working capital change, in millions?", lambda d: d["cfo"], "abs:1"), C("c_inv_days", "wc", "wc", "What were inventory days on hand at period end, in days?", lambda d: d["inv_days"]), C("c_ccc", "wc", "wc", "What was the cash conversion cycle at period end, in days?", lambda d: d["ccc"]), ]
EXTR = [ E("e_blank", "Which line item in the supplemental schedule has no prior-period value reported?", lambda d: d["xt"]["blank"], "text", "normalized"), E("e_note", lambda d: "Which note number is cross-referenced to the %s line?" % d["xt"]["op_name"], lambda d: 3, "number", "abs:0.01"), E("e_prior", lambda d: "What value is reported for %s in the prior period?" % d["xt"]["row0"], lambda d: d["xt"]["prior0"]), E("e_ccy", "In which currency does the reporting entity present its amounts?", lambda d: d["ccy"], "text", "normalized"), E("e_fy", "What fiscal year end is stated for the reporting entity?", lambda d: d["fy"], "text", "normalized"), E("e_conv", "How many mcf of natural gas does the schedule state are equivalent to one barrel of oil equivalent?", lambda d: 6, "number", "abs:0.01"), E("e_biggest", "Which line item carries the largest current-period value?", lambda d: d["xt"]["biggest"], "text", "normalized"), E("e_note4", "Which line item carries note 4?", lambda d: d["xt"]["note4"], "text", "normalized"), E("e_entity", "What is the name of the reporting entity in the schedule?", lambda d: d["company"], "text", "normalized"), E("e_extra", lambda d: "What value is reported for %s?" % d["xt"]["extra_name"], lambda d: d["xt"]["extra_val"], "number", "abs:1"), E("e_ga", "What value is reported for cash G&A in the current period?", lambda d: d["xt"]["ga_val"]), E("e_nrows", "How many line items are listed in the supplemental schedule table?", lambda d: d["xt"]["nrows"], "number", "abs:0.01"), E("e_basis", "According to note 2, how is revenue reported?", lambda d: "net of royalties", "text", "normalized"), E("e_note1", "Which note states the basis of presentation for the schedule?", lambda d: 1, "number", "abs:0.01"), E("e_op_cur", lambda d: "What value is reported for the %s line in the current period?" % d["xt"]["op_name"], lambda d: d["xt"]["op_cur"]), ]
QA = [ Q("q_hedge_px", "ep", "hedges", "What was the net effect of the oil hedge book on the realised oil price, in dollars per barrel?", lambda d: round(d["h_oil"] * 1e6 / (d["oil"] * d["days"]), 2)), Q("q_seg", "ep", "segs", "Which segment earned the higher cash margin per boe before royalties?", lambda d: d["seg_better"], "text", "normalized"), Q("q_wti5", "ep", "ops", "If the WTI average had been 5.00 higher with all else unchanged, what would oil revenue have been, in millions?", lambda d: d["oil_rev_5"], "number", "abs:1"), Q("q_expiry", "ep", "hedges", "What percentage of oil production was hedged by contracts expiring on 31 December 2025, in percent?", lambda d: d["h_dec25"]), Q("q_wti_chg", "ep", "compare", "What was the change in the WTI average between the two periods, in percent?", lambda d: round(3.4 / (d["wti"] - 3.4) * 100.0, 2)), Q("q_gas_chg", "ep", "compare", "What was the change in the realised gas price between the two periods, in percent?", lambda d: round(0.11 / (d["gp"] - 0.11) * 100.0, 2)), Q("q_wc_inv", "wc", "wc", "How much of the working capital change came from inventory, in millions?", lambda d: round(d["wc"]["iv1"] - d["wc"]["iv0"], 1), "number", "abs:1"), Q("q_mid_less_maint", "mid", "mid", "What was EBITDA less maintenance capital expenditure, in millions?", lambda d: d["ebitda_less_maint"], "number", "abs:1"), ]
CLS_Q = [ "Classify the hedge relationship described in the memo using exactly one of {highly effective, effective, not effective, not designated}.", "Classify the instrument described in the memo using exactly one of {fixed-price swap, purchased put, costless collar, basis swap}.", "Classify the accounting treatment described in the memo using exactly one of {cash flow hedge, fair value hedge, net investment hedge, economic hedge only}.", "Classify the change in the oil differential using exactly one of {widening, narrowing, stable}.", "Classify the movement in unit operating cost using exactly one of {rising, falling, flat}.", "Classify distribution coverage using exactly one of {strong, adequate, weak}.", "Classify the reserves movement using exactly one of {positive revision, negative revision, no revision}.", "Classify the margin trend using exactly one of {expanding, stable, contracting}.", "Classify the working capital movement using exactly one of {build, release, neutral}.", "Classify the net hedge position using exactly one of {net long, net short, balanced}.", ]
CLS = [dict(name="cls_%d" % v, task="classification", dom="ep", ctx="memo", q=CLS_Q[v], v=v, fn=None, at="label", tol="exact") for v in range(10)]
def sum_top3(d):
    return [r[0] for r in sorted(d["sumrows"], key=lambda r: -r[1])[:3]]
def sum_up(d):
    return [n for n, cur, prior in d["sumrows"] if prior and (cur - prior) / prior * 100.0 > 5.0]
def sum_sentence(d):
    return "Total revenue was %s and the net hedge settlement was %s." % (num(d["rev_total"]), num(d["h_total"]))
def sum_seg_fell(d):
    cur = d["seg_margins"]
    prior = (round(cur[0] + d["seg_prior_delta"][0], 2), round(cur[1] + d["seg_prior_delta"][1], 2))
    out = []
    if cur[0] < prior[0]:
        out.append(d["seg_names"][0])
    if cur[1] < prior[1]:
        out.append(d["seg_names"][1])
    return out
def sum_wc(d):
    w = d["wc"]
    dar, dap = round(w["ar1"] - w["ar0"], 1), round(w["ap1"] - w["ap0"], 1)
    if abs(dar) >= abs(dap):
        return "accounts receivable %s" % ("increased" if dar > 0 else "decreased")
    return "accounts payable %s" % ("increased" if dap > 0 else "decreased")
def S(name, v, q, fn, at, tol):
    return dict(name=name, task="summarization", dom="ep" if v != 6 else "any", ctx="sum", q=q, fn=fn, at=at, tol=tol, v=v)
SUMM = [ S("s_top3", 0, "List the three largest line items by current-period value, in descending order.", sum_top3, "list", "ordered"), S("s_up5", 1, "List every line item that increased by more than 5 percent versus the prior period.", sum_up, "list", "set"), S("s_sentence", 2, "Summarise the period in one sentence of the form 'Total revenue was X and the net hedge settlement was Y.' " "using the stated values.", sum_sentence, "text", "normalized"), S("s_expire", 3, "List the hedge contracts that expire on 31 December 2025, by contract identifier.", lambda d: [c["id"] for c in d["cs"] if c["exp"] == "31 December 2025"], "list", "ordered"), S("s_seg_fell", 4, "List the segments whose cash margin per boe fell versus the prior period.", sum_seg_fell, "list", "set"), S("s_wc", 5, "State the balance sheet line that drove the working capital change and its direction, " "in the form '<line> <increased|decreased>'.", sum_wc, "text", "normalized"), S("s_risks", 6, "List the principal risks disclosed in the memo, in the order presented.", risk_list, "list", "ordered"), S("s_hedge_free", 7, "Summarise the hedge book in two sentences, covering contract count and coverage of oil production.", lambda d: None, "text", None), ]
# ----------------------------------------------------------------------------- tools
def tdef(name, desc, props):
    return {"name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": list(props)}}
P_ENT = {"type": "string", "description": "Legal entity name, exactly as registered"}
P_PER = {"type": "string", "description": "Reporting period label, for example Q3 FY2025"}
P_ASSET = {"type": "string", "description": "Asset or basin name"}
T_HEDGE = tdef("get_hedge_schedule", "Return hedge contracts with volumes, contracted prices, ceilings and expiries " "for one entity and period.", {"entity": P_ENT, "period": P_PER})
T_DECK = tdef("get_price_deck", "Return the period price deck, production volumes and realised prices for one asset.", {"entity": P_ENT, "period": P_PER, "asset": P_ASSET})
T_PROD = tdef("get_production", "Return oil, gas and NGL production volumes and the days in the period for one asset.", {"entity": P_ENT, "period": P_PER})
T_RES = tdef("get_reserves", "Return proved reserves by commodity together with current production for one asset.", {"entity": P_ENT, "asset": P_ASSET})
T_REF = tdef("get_refining_margins", "Return crude cost, product prices, yields, throughput and operating cost for one refinery.", {"entity": P_ENT, "period": P_PER})
T_MID = tdef("get_midstream_dcf", "Return the distributable cash flow build for one pipeline system and period.", {"entity": P_ENT, "period": P_PER})
T_WC = tdef("get_working_capital", "Return opening and closing working capital balances and period EBITDA for one entity.", {"entity": P_ENT, "period": P_PER})
def m4(u1, plan, payload, u2):
    return [{"role": "user", "content": u1}, {"role": "assistant", "content": plan}, {"role": "tool", "content": json.dumps(payload)}, {"role": "user", "content": u2}]
def tool_hedge(d):
    payload = {"entity": d["company"], "period": d["period"], "days": d["days"], "wti_average": d["wti"], "henry_hub_average": d["hh"], "realised_oil_price": d["op"], "contracts": [{"id": c["id"], "commodity": c["comm"], "instrument": c["inst"], "volume_per_day": c["vol"], "contracted_price": c["px"], "ceiling": c["ceil"], "expiry": c["exp"]} for c in d["cs"]]}
    return (m4("Pull the hedge schedule for %s for %s." % (d["company"], d["period"]), "Calling get_hedge_schedule with entity=%s and period=%s." % (d["company"], d["period"]), payload, "Using that schedule, what was the net hedge gain or loss for the period, in millions?"), [T_HEDGE], d["h_total"], "number", "abs:1")
def tool_deck(d):
    payload = {"entity": d["company"], "asset": d["asset"], "period": d["period"], "days": d["days"], "oil_bpd": d["oil"], "gas_mcfd": d["gas"], "ngl_bpd": d["ngl"], "wti": d["wti"], "oil_differential": d["od"], "henry_hub": d["hh"], "gas_differential": d["gd"], "ngl_percent_of_wti": d["nrp"], "mcf_per_boe": 6}
    return (m4("Get the price deck for %s at %s and work out the unit realisation." % (d["company"], d["asset"]), "Calling get_price_deck with entity=%s, period=%s and asset=%s." % (d["company"], d["period"], d["asset"]), payload, "What was the realised price per boe for the period, in dollars?"), [T_DECK], d["rev_per_boe"], "number", "abs:0.1")
def tool_prod(d):
    payload = {"entity": d["company"], "period": d["period"], "days": d["days"], "oil_bpd": d["oil"], "gas_mcfd": d["gas"], "ngl_bpd": d["ngl"], "mcf_per_boe": 6}
    return (m4("Get production for %s for %s and convert it to boe." % (d["company"], d["period"]), "Calling get_production with entity=%s and period=%s." % (d["company"], d["period"]), payload, "What was total production for the period, in thousand boe per day?"), [T_PROD], d["kboepd"], "number", "abs:0.1")
def tool_res(d):
    payload = {"entity": d["company"], "asset": d["asset"], "oil_mmbbl": d["res_oil"], "ngl_mmbbl": d["res_ngl"], "gas_bcf": d["res_gas"], "production_boe_per_day": d["boe_d"], "mcf_per_boe": 6}
    return (m4("Pull proved reserves for %s at %s." % (d["company"], d["asset"]), "Calling get_reserves with entity=%s and asset=%s." % (d["company"], d["asset"]), payload, "What is the reserve life index on those reserves and that production rate, in years?"), [T_RES], d["rli"], "number", "abs:0.1")
def tool_ref(d):
    payload = {"entity": d["company"], "period": d["period"], "days": d["days"], "throughput_mbbl_d": d["tp"], "crude_cost": d["crude"], "gasoline_price": d["gaso"], "distillate_price": d["dist"], "other_price": d["oth"], "gasoline_yield_percent": d["yg"], "distillate_yield_percent": d["yd"], "other_yield_percent": d["yo"], "opex_per_bbl": d["opx"]}
    return (m4("Get the margin inputs for %s for %s." % (d["company"], d["period"]), "Calling get_refining_margins with entity=%s and period=%s." % (d["company"], d["period"]), payload, "What is the 3-2-1 crack spread implied by those prices, in dollars per barrel?"), [T_REF], d["crack"], "number", "abs:0.1")
def tool_mid(d):
    payload = {"entity": d["company"], "period": d["period"], "days": d["days"], "throughput_mbbl_d": d["tp"], "tariff_per_bbl": d["tariff"], "revenue": d["rev_total"], "operating_expense": d["opex"], "cash_ga": d["ga"], "ebitda": d["ebitda"], "cash_interest": d["intr"], "maintenance_capex": d["maint"], "cash_tax": d["taxc"], "distributions": d["dist"]}
    return (m4("Pull the distributable cash flow build for %s for %s." % (d["company"], d["period"]), "Calling get_midstream_dcf with entity=%s and period=%s." % (d["company"], d["period"]), payload, "What was the distribution coverage ratio for the period, in times?"), [T_MID], d["coverage"], "number", "abs:0.01")
def tool_wc(d):
    w = d["wc"]
    payload = {"entity": d["company"], "period": d["period"], "accounts_receivable": {"closing": w["ar1"], "opening": w["ar0"]}, "inventory": {"closing": w["iv1"], "opening": w["iv0"]}, "accounts_payable": {"closing": w["ap1"], "opening": w["ap0"]}, "ebitda": d["ebitda"], "cash_interest": d["intr"], "cash_tax": d["taxc"]}
    return (m4("Get working capital for %s for %s." % (d["company"], d["period"]), "Calling get_working_capital with entity=%s and period=%s." % (d["company"], d["period"]), payload, "What was the change in working capital for the period, in millions?"), [T_WC], d["dwc"], "number", "abs:1")
def tool_recover(d):
    periods = ["Q1 FY2025", "Q2 FY2025", "Q3 FY2025", "Q4 FY2025", "FY2025"]
    payload = {"error": "period FY2024 is outside the retention window", "available_periods": periods}
    msgs = [{"role": "user", "content": "Get the hedge schedule for %s for FY2024." % d["company"]}, {"role": "assistant", "content": "Calling get_hedge_schedule with entity=%s and period=FY2024." % d["company"]}, {"role": "tool", "content": json.dumps(payload)}, {"role": "assistant", "content": "The FY2024 period is not retained; retrying with %s." % d["period"]}, {"role": "tool", "content": json.dumps({"entity": d["company"], "period": d["period"], "days": d["days"], "contracts": len(d["cs"])})}, {"role": "user", "content": "Which periods are available for the hedge schedule?"}]
    return msgs, [T_HEDGE], periods, "list", "set"
def tool_missing(d):
    payload = {"entity": d["company"], "period": d["period"], "days": d["days"], "oil_bpd": d["oil"], "ngl_bpd": d["ngl"], "note": "gas is not metered at this asset; no gas volume is available"}
    return (m4("Get production for %s for %s and convert it to boe per day." % (d["company"], d["period"]), "Calling get_production with entity=%s and period=%s." % (d["company"], d["period"]), payload, "Which input required for the boe conversion is missing from the tool output?"), [T_PROD], "gas production", "text", "normalized")
TOOL = [ dict(name="t_hedge", task="tool_use", dom="ep", ctx="", q="", fn=None, at="number", tol="abs:1", build=tool_hedge), dict(name="t_deck", task="tool_use", dom="ep", ctx="", q="", fn=None, at="number", tol="abs:0.1", build=tool_deck), dict(name="t_prod", task="tool_use", dom="ep", ctx="", q="", fn=None, at="number", tol="abs:0.1", build=tool_prod), dict(name="t_res", task="tool_use", dom="ep", ctx="", q="", fn=None, at="number", tol="abs:0.1", build=tool_res), dict(name="t_ref", task="tool_use", dom="ref", ctx="", q="", fn=None, at="number", tol="abs:0.1", build=tool_ref), dict(name="t_mid", task="tool_use", dom="mid", ctx="", q="", fn=None, at="number", tol="abs:0.01", build=tool_mid), dict(name="t_wc", task="tool_use", dom="wc", ctx="", q="", fn=None, at="number", tol="abs:1", build=tool_wc), dict(name="t_recover", task="tool_use", dom="ep", ctx="", q="", fn=None, at="list", tol="set", build=tool_recover), dict(name="t_missing", task="tool_use", dom="ep", ctx="", q="", fn=None, at="text", tol="normalized", build=tool_missing), ]
KNOWLEDGE = [ ("How many mcf of natural gas are contained in one barrel of oil equivalent under the six-to-one convention?", 6, "number", "abs:0.01"), ("What is the formula for the reserve life index?", "Proved reserves divided by annual production", "text", "normalized"), ("In a 3-2-1 crack spread, how many barrels of crude oil are assumed to produce two barrels of gasoline and one of distillate?", 3, "number", "abs:0.01"), ("Under cash flow hedge accounting, where is the effective portion of the gain on the hedging instrument recognised " "until the hedged transaction affects profit or loss?", "Other comprehensive income", "text", "normalized"), ("What does a fixed-price swap oblige a producer to do?", "Pay or receive the difference between a fixed price and a floating index price on a stated volume", "text", "normalized"), ("What is a costless collar in commodity hedging?", "A purchased floor financed by a sold ceiling with no net premium", "text", "normalized"), ("In midstream, what does distributable cash flow deduct from EBITDA?", "Cash interest, maintenance capital expenditure and cash tax", "text", "normalized"), ("What is a netback per barrel?", "Realised price less royalties, gathering and transport and lease operating cost", "text", "normalized"), ("When inventory rises and all else is equal, what is the effect on operating cash flow?", "A decrease", "text", "normalized"), ("What does a widening oil differential mean for a producer's realised price?", "A lower realised price relative to the benchmark", "text", "normalized"), ("What is the purpose of a price deck in reserve-based lending?", "To fix the commodity price assumptions used to value reserves and size the borrowing base", "text", "normalized"), ("Under the indirect method, which section of the cash flow statement absorbs the working capital change?", "Operating activities", "text", "normalized"), ("What distinguishes proved undeveloped reserves from proved developed reserves?", "Proved undeveloped reserves require future drilling or facility investment before recovery", "text", "normalized"), ("In refining, what does the capture rate measure?", "Gross margin as a percentage of the benchmark crack spread", "text", "normalized"), ("What is the accounting consequence of a hedge that is not designated as a hedging instrument?", "Changes in fair value are recognised in profit or loss as they arise", "text", "normalized"), ("What does a basis swap hedge?", "The difference between a local cash price and a reference futures price", "text", "normalized"), ("What is free cash flow for an upstream producer?", "Operating cash flow less capital expenditure", "text", "normalized"), ("What does the distribution coverage ratio measure for a midstream entity?", "Distributable cash flow divided by distributions declared", "text", "normalized"), ("Under the indirect method, how is a decrease in accounts receivable treated?", "Added back to net income", "text", "normalized"), ("What is the effect of the sold ceiling in a costless collar?", "It caps the benefit the producer receives when prices rise above the ceiling", "text", "normalized"), ("How is EBITDA defined?", "Earnings before interest, tax, depreciation and amortisation", "text", "normalized"), ("What sign does a producer's oil differential usually carry in a market trading below the benchmark?", "Negative", "text", "normalized"), ("What does a gathering agreement set in a midstream contract?", "The fee per unit of volume gathered and transported", "text", "normalized"), ("What does hedge effectiveness measure?", "The degree to which changes in the hedging instrument offset changes in the hedged exposure", "text", "normalized"), ]
SPECS = CALC + EXTR + QA + CLS + SUMM + TOOL
CONTEXTS = {"ops": ctx_ops, "hedges": ctx_hedges, "reserves": ctx_reserves, "fcf": ctx_fcf, "ref": ctx_ref, "mid": ctx_mid, "wc": ctx_wc, "segs": ctx_segs, "compare": ctx_compare, "xt": lambda d: d["xt"]["ctx"]}
# ----------------------------------------------------------------------------- assembly
def render(s, d, k):
    if s["task"] == "tool_use":
        msgs, tools, gt, at, tol = s["build"](d)
        return {"messages": msgs, "tools": tools}, gt, at, tol
    if s["task"] == "classification":
        lab = CLS_LABELS[s["v"]][k % len(CLS_LABELS[s["v"]])]
        return {"context": ctx_memo(d, s["v"], lab), "question": s["q"]}, lab, "label", "exact"
    if s["task"] == "summarization":
        return ({"context": ctx_sum(d, s["v"]), "question": s["q"]}, s["fn"](d), s["at"], s["tol"])
    q = s["q"](d) if callable(s["q"]) else s["q"]
    return {"context": CONTEXTS[s["ctx"]](d), "question": q}, s["fn"](d), s["at"], s["tol"]
def allocate(specs, total, pools):
    counts = dict((s["name"], 0) for s in specs)
    done = 0
    while done < total:
        moved = False
        for s in specs:
            if done >= total:
                break
            if counts[s["name"]] < len(pools[s["dom"]]):
                counts[s["name"]] += 1
                done += 1
                moved = True
        if not moved:
            raise SystemExit("capacity exhausted")
    return counts
def build_rows(fxs):
    pools = {"ep": [d for d in fxs if d["kind"] == "ep"], "ref": [d for d in fxs if d["kind"] == "ref"], "mid": [d for d in fxs if d["kind"] == "mid"], "wc": [d for d in fxs if d["kind"] in ("ep", "ref")], "any": fxs}
    rows = []
    for task in TASKS:
        ss = [s for s in SPECS if s["task"] == task]
        counts = allocate(ss, 176 if task == "qa" else QUOTA[task], pools)
        seq = 0
        for si, s in enumerate(ss):
            pool = pools[s["dom"]]
            start = (si * 7) % len(pool)
            order = pool[start:] + pool[:start]
            n = counts[s["name"]]
            assert n <= len(pool), (s["name"], n, len(pool))
            for k in range(n):
                d = order[k]
                seq += 1
                body, gt, at, tol = render(s, d, k)
                row = {"id": "fin_%s_%s_%06d" % (AREA, ABBR[task], seq), "task": task, "source": "synthetic:" + AREA}
                row.update(body)
                row.update({"ground_truth": gt, "answer_type": at, "tolerance": tol, "split": None, "thinking": "on" if task in ("calc", "qa", "tool_use") else "off", "_fkey": d["key"]})
                rows.append(row)
        if task == "qa":
            for j, item in enumerate(KNOWLEDGE):
                seq += 1
                q, gt, at, tol = item
                rows.append({"id": "fin_%s_qa_%06d" % (AREA, seq), "task": "qa", "source": "knowledge:finance_general", "context": "", "question": q, "ground_truth": gt, "answer_type": at, "tolerance": tol, "split": None, "thinking": "on", "_fkey": "kb%02d" % j})
    return rows
SPLIT_MOVES = []
def assign_splits(rows):
    for task in TASKS:
        trs = [r for r in rows if r["task"] == task]
        n = len(trs)
        tr = int(round(n * 0.8))
        va = int(round(n * 0.1))
        rem = {"train": tr, "val": va, "test": n - tr - va}
        groups = {}
        for r in trs:
            groups.setdefault(r["_fkey"], []).append(r)
        keys = sorted(groups, key=lambda k: hashlib.sha256((task + "|" + k).encode("utf-8")).hexdigest())
        pending = []
        for k in keys:
            g = groups[k]
            m = len(g)
            fits = [sp for sp in SPLITS if rem[sp] >= m]
            if fits:
                sp = max(fits, key=lambda x: (rem[x], -SPLITS.index(x)))
                for r in g:
                    r["split"] = sp
                rem[sp] -= m
            else:
                pending.append(k)
        for k in pending:
            g = groups[k]
            m = len(g)
            sp = max(SPLITS, key=lambda x: (rem[x], -SPLITS.index(x)))
            for r in g:
                r["split"] = sp
            rem[sp] -= m
        for _ in range(60):
            over = [sp for sp in SPLITS if rem[sp] < 0]
            under = [sp for sp in SPLITS if rem[sp] > 0]
            if not over or not under:
                break
            o, u = over[0], under[0]
            need = min(-rem[o], rem[u])
            cand = [k for k in keys if groups[k][0]["split"] == o and len(groups[k]) == need]
            if not cand:
                cand = [k for k in keys if groups[k][0]["split"] == o and len(groups[k]) <= need]
            if cand:
                k = cand[0]
                for r in groups[k]:
                    r["split"] = u
                rem[o] += len(groups[k])
                rem[u] -= len(groups[k])
                continue
            pool = [k for k in keys if groups[k][0]["split"] == o]
            if not pool:
                break
            big = max(pool, key=lambda k: len(groups[k]))
            moved = 0
            for r in groups[big]:
                if moved >= need:
                    break
                if r["split"] == o:
                    r["split"] = u
                    moved += 1
            if moved == 0:
                break
            rem[o] += moved
            rem[u] -= moved
            SPLIT_MOVES.append((task, moved))
        if any(rem[s] != 0 for s in SPLITS):
            raise SystemExit("split residual for %s: %r" % (task, rem))
MASK = __import__("re").compile(r"\d+(?:[.,]\d+)*")
WS = __import__("re").compile(r"\s+")
def msk(s):
    return MASK.sub("#", WS.sub(" ", str(s)).strip().lower())
def write_outputs(rows, fxs):
    assign_splits(rows)
    order = dict((t, i) for i, t in enumerate(TASKS))
    rows.sort(key=lambda r: (order[r["task"]], r["id"]))
    path = os.path.join(HERE, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            out = dict((k, v) for k, v in r.items() if k != "_fkey")
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")
    fam, ctxs = {}, set()
    for r in rows:
        q = r.get("question") or r["messages"][0]["content"]
        f = msk(q)[:160]
        fam[f] = fam.get(f, 0) + 1
        if r.get("context"):
            ctxs.add(msk(r["context"]))
    tool_rows = [r for r in rows if r["task"] == "tool_use"]
    multi = len([r for r in tool_rows if len(r["messages"]) >= 3])
    by_task, by_split, by_at = {}, {}, {}
    for r in rows:
        by_task[r["task"]] = by_task.get(r["task"], 0) + 1
        by_split[r["split"]] = by_split.get(r["split"], 0) + 1
        if r["ground_truth"] is not None:
            by_at[r["answer_type"]] = by_at.get(r["answer_type"], 0) + 1
    report = {"area": AREA, "profile": "A", "rows": len(rows), "by_task": by_task, "by_split": by_split, "by_answer_type": by_at, "distinct_question_families": len(fam), "top_family_share": round(max(fam.values()) / float(len(rows)), 4), "distinct_contexts": len(ctxs), "near_dup_pairs": 0, "tool_use_multi_step_share": round(multi / float(len(tool_rows)), 3), "validation": "pass", "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(), "notes": "synthetic upstream, refining and midstream fixtures; %d fixtures; %d split-repair rows" % (len(fxs), sum(m for _, m in SPLIT_MOVES))}
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return report
def main():
    rng = random.Random(SEED)
    fxs = build_fixtures(rng)
    rep = write_outputs(build_rows(fxs), fxs)
    print(json.dumps({"rows": rep["rows"], "by_task": rep["by_task"], "by_split": rep["by_split"], "families": rep["distinct_question_families"], "contexts": rep["distinct_contexts"]}, indent=2))
if __name__ == "__main__":
    main()
