#!/usr/bin/env python3
"""Deterministic generator for the ratio_analysis area (profile A).
Everything is synthetic and offline. Every ground-truth number is computed in
code from the same fixture dict that is rendered into the context table, so a
re-run reproduces each answer exactly.
"""
import hashlib
import json
import os
import random
import re
from collections import Counter
AREA = "ratio_analysis"
RNG = random.Random(42)  # seeded per contract; fixtures below are fully specified
HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = ("Units: $ in millions except per-share amounts in dollars; "
         "percentages in percent; ratios in x.")

# ---------------------------------------------------------------- fixtures ---
BASE = dict(growth=0.05, gm=0.35, gm_chg=0.006, sga=0.12, rnd=0.02, da=0.05,
            tax=0.24, dso=45, dio=60, dpo=50, cash=0.06, sti=0.01, oca=0.02,
            ppe=0.55, gw=0.15, intang=0.06, oa=0.03, lev=1.8, rate=0.055,
            shares=200, pe=18.0, payout=0.35, capex=0.06, accrued=0.06,
            oncl=0.05, d1=0.04, d2=0.00)

def F(key, name, sector, fyend, rev, segs, bench, **kw):
    d = dict(BASE)
    d.update(kw)
    d.update(key=key, name=name, sector=sector, fyend=fyend, rev=rev,
             segs=segs, bench=bench)
    return d
SPECS = [
    F("halcyon_grid", "Halcyon Grid Utilities", "Utilities", "31 December", 7400, ["Regulated electric", "Regulated gas", "Unregulated retail"], "Utilities", gm=0.330, sga=0.085, rnd=0.004, da=0.115, lev=3.9, ppe=1.55, dio=34, dso=38, dpo=46, pe=15.2, payout=0.62, tax=0.23, shares=410, capex=0.13, cash=0.025, gw=0.06, intang=0.03, oa=0.06, accrued=0.05, oncl=0.06, d1=0.06, d2=-0.02, gm_chg=0.004),
    F("northgate_power", "Northgate Power and Light", "Utilities", "30 June", 5100, ["Regulated delivery", "Merchant supply", "Other energy services"], "Utilities", gm=0.300, sga=0.075, rnd=0.002, da=0.130, lev=3.17, ppe=1.90, dio=40, dso=35, dpo=48, pe=13.4, payout=0.70, tax=0.22, shares=300, capex=0.16, cash=0.020, gw=0.05, intang=0.02, oa=0.05, accrued=0.04, oncl=0.05, d1=0.05, d2=-0.01, gm_chg=-0.008),
    F("meridian_ridge", "Meridian Ridge Software", "Software", "31 December", 3200, ["Subscription", "Professional services", "Hardware appliances"], "Software", gm=0.780, sga=0.330, rnd=0.190, da=0.035, lev=0.5, ppe=0.10, dio=18, dso=62, dpo=30, pe=34.0, payout=0.12, tax=0.19, shares=190, capex=0.03, cash=0.18, sti=0.06, gw=0.28, intang=0.10, oa=0.04, accrued=0.07, oncl=0.03, d1=0.09, d2=-0.04, gm_chg=0.012),
    F("tessellate", "Tessellate Analytics", "Software", "30 September", 1850, ["Platform subscriptions", "Data services", "Implementation"], "Software", gm=0.740, sga=0.300, rnd=0.210, da=0.040, lev=0.9, ppe=0.12, dio=22, dso=58, dpo=28, pe=28.0, payout=0.10, tax=0.21, shares=120, capex=0.035, cash=0.15, sti=0.05, gw=0.22, intang=0.08, oa=0.04, accrued=0.06, oncl=0.03, d1=0.07, d2=-0.03, gm_chg=-0.015),
    F("kestrel_foods", "Kestrel Foods", "Packaged foods", "30 June", 8900, ["Branded foods", "Private label", "Foodservice"], "Software", gm=0.360, sga=0.200, rnd=0.010, da=0.040, lev=2.2, ppe=0.35, dio=55, dso=32, dpo=42, pe=17.5, payout=0.45, tax=0.24, shares=380, capex=0.05, cash=0.05, gw=0.18, intang=0.08, d1=0.05, d2=0.00, gm_chg=0.009),
    F("sunfield_grocers", "Sunfield Grocers", "Grocery retail", "31 December", 15400, ["Supermarkets", "Convenience", "Wholesale"], "Software", gm=0.260, sga=0.185, rnd=0.0, da=0.028, lev=2.6, ppe=0.42, dio=28, dso=12, dpo=38, pe=15.8, payout=0.30, tax=0.25, shares=520, capex=0.035, cash=0.04, gw=0.10, intang=0.04, d1=0.03, d2=-0.01, gm_chg=-0.006),
    F("ardenne_apparel", "Ardenne Apparel", "Apparel retail", "31 January", 4600, ["Store network", "Online channel", "Outlet"], "Software", gm=0.420, sga=0.310, rnd=0.0, da=0.035, lev=1.4, ppe=0.30, dio=95, dso=18, dpo=55, pe=12.5, payout=0.25, tax=0.26, shares=150, capex=0.04, cash=0.09, sti=0.03, gw=0.08, intang=0.03, d1=0.04, d2=0.02, gm_chg=0.014),
    F("cobalt_lattice", "Cobalt Lattice Semiconductor", "Semiconductors", "31 December", 6300, ["Analog products", "Embedded systems", "Licensing"], "Software", gm=0.560, sga=0.130, rnd=0.150, da=0.060, lev=0.7, ppe=0.38, dio=88, dso=55, dpo=40, pe=26.0, payout=0.22, tax=0.18, shares=240, capex=0.08, cash=0.14, sti=0.07, gw=0.16, intang=0.09, d1=0.10, d2=-0.05, gm_chg=0.021),
    F("silverbrook_medical", "Silverbrook Medical", "Medical devices", "31 March", 5200, ["Surgical devices", "Diagnostics", "Service contracts"], "Software", gm=0.620, sga=0.280, rnd=0.100, da=0.040, lev=1.6, ppe=0.22, dio=120, dso=58, dpo=45, pe=22.0, payout=0.18, tax=0.20, shares=210, capex=0.05, cash=0.12, sti=0.04, gw=0.24, intang=0.12, d1=0.08, d2=-0.02, gm_chg=0.005),
    F("tallow_finch", "Tallow and Finch Restaurants", "Restaurants", "31 December", 3100, ["Company operated", "Franchised", "Supply chain"], "Software", gm=0.680, sga=0.520, rnd=0.0, da=0.050, lev=2.9, ppe=0.55, dio=12, dso=8, dpo=30, pe=19.0, payout=0.35, tax=0.24, shares=95, capex=0.06, cash=0.07, gw=0.14, intang=0.05, d1=0.06, d2=-0.03, gm_chg=0.018),
    F("verity_specialties", "Verity Specialties", "Specialty chemicals", "30 June", 4400, ["Coatings", "Performance additives", "Contract manufacturing"], "Utilities", gm=0.290, sga=0.120, rnd=0.030, da=0.070, lev=2.4, ppe=0.75, dio=70, dso=48, dpo=52, pe=16.0, payout=0.32, tax=0.23, shares=130, capex=0.075, cash=0.06, gw=0.17, intang=0.07, d1=0.05, d2=0.01, gm_chg=-0.011),
    F("larkspur_telecom", "Larkspur Telecom", "Telecom", "31 December", 9800, ["Network access", "Enterprise services", "Wholesale"], "Utilities", gm=0.520, sga=0.220, rnd=0.020, da=0.160, lev=3.3, ppe=1.25, dio=20, dso=28, dpo=40, pe=12.8, payout=0.55, tax=0.24, shares=560, capex=0.18, cash=0.03, gw=0.20, intang=0.10, oa=0.04, d1=0.07, d2=-0.02, gm_chg=0.003),
    F("northwind_logistics", "Northwind Logistics", "Transport", "31 December", 6900, ["Contract logistics", "Freight forwarding", "Fleet services"], "Utilities", gm=0.310, sga=0.150, rnd=0.0, da=0.080, lev=2.7, ppe=0.85, dio=15, dso=52, dpo=38, pe=18.5, payout=0.28, tax=0.25, shares=175, capex=0.09, cash=0.05, gw=0.13, intang=0.05, d1=0.04, d2=0.01, gm_chg=0.007),
    F("brightwater_homes", "Brightwater Homes", "Homebuilding", "31 December", 4100, ["Entry level", "Move up", "Land sales"], "Utilities", gm=0.230, sga=0.110, rnd=0.0, da=0.015, lev=1.9, ppe=0.06, dio=320, dso=14, dpo=26, pe=9.5, payout=0.15, tax=0.25, shares=130, capex=0.025, cash=0.10, sti=0.02, gw=0.02, intang=0.01, oa=0.02, d1=0.05, d2=-0.01, gm_chg=-0.004),
    F("quarry_lane", "Quarry Lane Minerals", "Mining", "31 December", 3600, ["Bulk metals", "Processing", "Royalties"], "Utilities", gm=0.380, sga=0.090, rnd=0.010, da=0.140, lev=1.7, ppe=1.10, dio=60, dso=40, dpo=44, pe=11.0, payout=0.40, tax=0.27, shares=155, capex=0.12, cash=0.08, gw=0.07, intang=0.03, oa=0.05, d1=0.09, d2=-0.03, gm_chg=0.025),
    F("pelham_media", "Pelham Media Group", "Media", "31 December", 5400, ["Broadcast", "Streaming", "Content licensing"], "Utilities", gm=0.480, sga=0.240, rnd=0.020, da=0.090, lev=2.8, ppe=0.45, dio=10, dso=68, dpo=35, pe=14.0, payout=0.30, tax=0.24, shares=260, capex=0.03, cash=0.08, gw=0.35, intang=0.15, d1=0.06, d2=-0.05, gm_chg=-0.002),
    F("harborlight_energy", "Harborlight Energy Services", "Energy services", "31 December", 6200, ["Drilling services", "Completions", "Rental tools"], "Utilities", gm=0.240, sga=0.080, rnd=0.010, da=0.090, lev=2.1, ppe=0.65, dio=42, dso=62, dpo=40, pe=13.5, payout=0.20, tax=0.25, shares=220, capex=0.10, cash=0.06, gw=0.12, intang=0.04, d1=0.07, d2=0.00, gm_chg=0.016),
    F("juniper_ridge", "Juniper Ridge Hotels", "Hospitality", "31 December", 2900, ["Owned hotels", "Management contracts", "Food and beverage"], "Utilities", gm=0.580, sga=0.300, rnd=0.0, da=0.100, lev=3.1, ppe=1.35, dio=14, dso=20, dpo=32, pe=24.0, payout=0.25, tax=0.23, shares=110, capex=0.07, cash=0.09, gw=0.16, intang=0.06, d1=0.08, d2=-0.02, gm_chg=0.010),
    F("marrow_main", "Marrow and Main Publishing", "Publishing", "31 December", 2400, ["Academic", "Trade", "Digital"], "Software", gm=0.550, sga=0.320, rnd=0.030, da=0.040, lev=1.2, ppe=0.18, dio=110, dso=66, dpo=42, pe=15.0, payout=0.42, tax=0.24, shares=85, capex=0.03, cash=0.11, sti=0.03, gw=0.20, intang=0.11, d1=0.05, d2=-0.02, gm_chg=-0.009),
    F("ironvale_equipment", "Ironvale Equipment", "Industrial equipment", "31 December", 7100, ["Machinery", "Aftermarket", "Financing"], "Utilities", gm=0.300, sga=0.130, rnd=0.040, da=0.040, lev=2.3, ppe=0.50, dio=105, dso=60, dpo=48, pe=20.0, payout=0.26, tax=0.24, shares=200, capex=0.045, cash=0.07, sti=0.03, gw=0.19, intang=0.06, d1=0.06, d2=0.02, gm_chg=0.011),
]
SECTOR_NORMS = [("Banks", 11.2, 1.28, None, 24.0, 11.6),
                ("Utilities", 15.8, 1.72, 9.4, 12.6, 9.8),
                ("Software", 31.4, 7.80, 22.6, 20.8, 19.4)]
NORMS = dict((r[0], {"pe": r[1], "pb": r[2], "ev": r[3], "nm": r[4], "roe": r[5]})
             for r in SECTOR_NORMS)

def num(v, d=0):
    s = ("%.*f" % (d, v)) if d else str(int(round(v)))
    return s[1:] if s.startswith("-") and float(s) == 0 else s

def td(d): return d["std"] + d["cpltd"] + d["ltd"]

def ebitda_of(d): return d["ebit"] + d["da"]

def mk_year(rev, p, lev_mult, gm_adj, sga_adj):
    cogs = int(round(rev * (1 - p["gm"] - gm_adj)))
    gp = rev - cogs
    sga = int(round(rev * (p["sga"] + sga_adj)))
    rnd = int(round(rev * p["rnd"]))
    da = int(round(rev * p["da"]))
    ebit = gp - sga - rnd - da
    debt = int(round((ebit + da) * p["lev"] * lev_mult))
    interest = max(1, int(round(debt * p["rate"])))
    pretax = ebit - interest
    tax = int(round(pretax * p["tax"]))
    ni = pretax - tax
    ar = int(round(rev * p["dso"] / 365.0))
    inv = max(16, int(round(cogs * p["dio"] / 365.0)))
    cash = int(round(rev * p["cash"]))
    sti = int(round(rev * p["sti"]))
    oca = int(round(rev * p["oca"]))
    tca = cash + sti + ar + inv + oca
    ap = int(round(cogs * p["dpo"] / 365.0))
    accrued = int(round(rev * p["accrued"]))
    std = int(round(debt * 0.10))
    cpltd = int(round(debt * 0.08))
    ltd = debt - std - cpltd
    tcl = ap + std + cpltd + accrued
    oncl = int(round(rev * p["oncl"]))
    tl = tcl + ltd + oncl
    ppe = int(round(rev * p["ppe"]))
    gw = int(round(rev * p["gw"]))
    intang = int(round(rev * p["intang"]))
    oa = int(round(rev * p["oa"]))
    ta = tca + ppe + gw + intang + oa
    eq = ta - tl
    guard = 0
    while eq < 0.18 * ta and guard < 8:
        ppe = int(round(ppe * 1.14))
        ta = tca + ppe + gw + intang + oa
        eq = ta - tl
        guard += 1
    return dict(rev=rev, cogs=cogs, gp=gp, sga=sga, rnd=rnd, da=da, ebit=ebit,
                interest=interest, pretax=pretax, tax=tax, ni=ni, ar=ar, inv=inv,
                cash=cash, sti=sti, oca=oca, tca=tca, ap=ap, accrued=accrued,
                std=std, cpltd=cpltd, ltd=ltd, tcl=tcl, oncl=oncl, tl=tl, ppe=ppe,
                gw=gw, intang=intang, oa=oa, ta=ta, equity=eq)

def build_fixture(i, p):
    rev25 = p["rev"]
    rev24 = int(round(rev25 / (1 + p["growth"])))
    y24 = mk_year(rev24, p, 1.06, -p["gm_chg"], -0.002)
    y25 = mk_year(rev25, p, 1.00, 0.0, 0.0)
    wc = (y25["ar"] - y24["ar"]) + (y25["inv"] - y24["inv"]) - (y25["ap"] - y24["ap"])
    cfo = y25["ni"] + y25["da"] - wc
    if cfo < int(0.72 * y25["ni"]):
        cfo = int(round(0.72 * y25["ni"] + 0.55 * y25["da"]))
    capex = int(round(rev25 * p["capex"]))
    if cfo - capex <= 0:
        capex = int(round(cfo * 0.42))
    y25["cfo"], y25["capex"] = cfo, max(8, capex)
    y24["cfo"] = int(round(0.94 * y24["ni"] + 0.62 * y24["da"]))
    y24["capex"] = int(round(rev24 * p["capex"] * 0.94))
    shares = float(p["shares"])
    eps = round(y25["ni"] / shares, 2)
    y25["eps"], y24["eps"] = eps, round(y24["ni"] / shares, 2)
    y25["shares"] = y24["shares"] = shares
    dps = round(eps * p["payout"], 2)
    y25["dps"], y24["dps"] = dps, round(y24["eps"] * p["payout"], 2)
    y25["divpaid"] = int(round(dps * shares))
    y24["divpaid"] = int(round(y24["dps"] * shares))
    price = round(eps * p["pe"], 2)
    mcap = int(round(price * shares))
    debt = td(y25)
    netdebt = debt - y25["cash"] - y25["sti"]
    y25["principal"] = int(round(debt * 0.05))
    y25["lease"] = int(round(rev25 * 0.008))
    y24["principal"] = int(round(td(y24) * 0.05))
    y24["lease"] = int(round(rev24 * 0.008))
    fx = dict(i=i, key=p["key"], name=p["name"], sector=p["sector"],
              fyend=p["fyend"], fy25="FY2025", fy24="FY2024", bench=p["bench"],
              p=p, y25=y25, y24=y24, wrong=(i * 3 + 1) % 4,
              mkt=dict(price=price, mcap=mcap, shares=shares, eps=eps, dps=dps,
                       debt=debt, netdebt=netdebt, ebitda=ebitda_of(y25),
                       cfo=y25["cfo"], capex=y25["capex"]))
    d = debt
    cp, rcf, tla = int(round(d * 0.08)), int(round(d * 0.12)), int(round(d * 0.20))
    n31 = int(round(d * 0.33))
    n33 = d - cp - rcf - tla - n31
    fx["debt"] = [("Commercial paper", cp, 5.35, "February 2027", "unsecured"),
                  ("Revolving credit facility", rcf, 5.20, "June 2028", "unsecured"),
                  ("Term loan A", tla, 5.05, "June 2029", "unsecured"),
                  ("Senior notes due 2031", n31, 4.25, "September 2031", "unsecured"),
                  ("Senior notes due 2033", n33, 4.60, "March 2033", "unsecured")]
    mix = (0.52, 0.33, 0.15)
    seg = [dict(name=p["segs"][k], rev=0, oi=0, prev_rev=0, prev_oi=0) for k in range(3)]
    r1, r2 = int(round(rev25 * mix[0])), int(round(rev25 * mix[1]))
    seg[0]["rev"], seg[1]["rev"], seg[2]["rev"] = r1, r2, rev25 - r1 - r2
    p1, p2 = int(round(rev24 * mix[0])), int(round(rev24 * mix[1]))
    seg[0]["prev_rev"], seg[1]["prev_rev"] = p1, p2
    seg[2]["prev_rev"] = rev24 - p1 - p2
    blend = y25["ebit"] / float(rev25)
    seg[0]["oi"] = int(round(seg[0]["rev"] * (blend + p["d1"])))
    seg[1]["oi"] = int(round(seg[1]["rev"] * (blend + p["d2"])))
    seg[2]["oi"] = y25["ebit"] - seg[0]["oi"] - seg[1]["oi"]
    blend24 = y24["ebit"] / float(rev24)
    seg[0]["prev_oi"] = int(round(seg[0]["prev_rev"] * (blend24 + p["d1"] - p["gm_chg"] * 0.5)))
    seg[1]["prev_oi"] = int(round(seg[1]["prev_rev"] * (blend24 + p["d2"])))
    seg[2]["prev_oi"] = y24["ebit"] - seg[0]["prev_oi"] - seg[1]["prev_oi"]
    fx["seg"] = seg
    compute_metrics(fx)
    return fx

def avg(fx, k): return (fx["y25"][k] + fx["y24"][k]) / 2.0

def compute_metrics(fx):
    a, b = fx["y25"], fx["y24"]
    debt, netdebt, eb = td(a), td(a) - a["cash"] - a["sti"], ebitda_of(a)
    fc = a["interest"] + a["principal"] + a["lease"]
    ata, aeq = avg(fx, "ta"), avg(fx, "equity")
    m = dict(debt=debt, netdebt=netdebt, ebitda=eb, fc=fc,
             current=a["tca"] / float(a["tcl"]), cash_r=(a["cash"] + a["sti"]) / float(a["tcl"]),
             quick=(a["cash"] + a["sti"] + a["ar"]) / float(a["tcl"]),
             debt_ebitda=debt / float(eb), netdebt_ebitda=netdebt / float(eb),
             int_cov=a["ebit"] / float(a["interest"]), fcc=(a["ebit"] + fc) / float(fc),
             asset_turn=a["rev"] / ata, inv_turns=a["cogs"] / avg(fx, "inv"),
             dso=365.0 * avg(fx, "ar") / a["rev"], dio=365.0 * avg(fx, "inv") / a["cogs"],
             dpo=365.0 * avg(fx, "ap") / a["cogs"], dup3_em=ata / aeq,
             dup3_roe=(a["ni"] / float(a["rev"])) * (a["rev"] / ata) * (ata / aeq) * 100,
             dup5_tax=a["ni"] / float(a["pretax"]) * 100,
             dup5_int=a["pretax"] / float(a["ebit"]) * 100,
             pe=fx["mkt"]["price"] / fx["mkt"]["eps"], payout=fx["mkt"]["dps"] / fx["mkt"]["eps"] * 100,
             pb=fx["mkt"]["mcap"] / float(a["equity"]),
             ev_ebitda=(fx["mkt"]["mcap"] + netdebt) / float(eb),
             fcf=a["cfo"] - a["capex"], gm=a["gp"] / float(a["rev"]) * 100,
             om=a["ebit"] / float(a["rev"]) * 100, nm=a["ni"] / float(a["rev"]) * 100)
    m["ccc"] = m["dso"] + m["dio"] - m["dpo"]
    m["fcf_yield"] = m["fcf"] / float(fx["mkt"]["mcap"]) * 100
    m["gm_chg"] = m["gm"] - b["gp"] / float(b["rev"]) * 100
    m["om_chg"] = m["om"] - b["ebit"] / float(b["rev"]) * 100
    m["rev_growth"] = (a["rev"] / float(b["rev"]) - 1) * 100
    m["div_cover"] = a["ni"] / float(a["divpaid"])
    m["fcf_cover"] = m["fcf"] / float(a["divpaid"])
    m["fcf_conv"] = m["fcf"] / float(a["ni"]) * 100
    m["capex_int"] = a["capex"] / float(a["rev"]) * 100
    m["delever_years"] = netdebt / (2.0 * m["fcf"])
    m["dso_chg"] = 365.0 * (a["ar"] / float(a["rev"]) - b["ar"] / float(b["rev"]))
    m["roe_chg"] = (a["ni"] / float(a["equity"]) - b["ni"] / float(b["equity"])) * 100
    m["at_chg"] = a["rev"] / float(a["ta"]) - b["rev"] / float(b["ta"])
    m["payout_ni"] = a["divpaid"] / float(a["ni"]) * 100
    m["int_headroom"] = a["ebit"] / 2.0 - a["interest"]
    m["inv_implied"] = a["tca"] - a["tcl"] - a["oca"]
    m["fcf_margin"] = m["fcf"] / float(a["rev"]) * 100
    m["wa_coupon"] = sum(x[1] * x[2] for x in fx["debt"]) / float(sum(x[1] for x in fx["debt"]))
    m["ev_at_bench"] = NORMS[fx["bench"]]["ev"] * eb
    m["pe_gap"] = m["pe"] - NORMS[fx["bench"]]["pe"]
    m["nm_gap"] = m["nm"] - NORMS[fx["bench"]]["nm"]
    margins = [s["oi"] / float(s["rev"]) * 100 for s in fx["seg"]]
    m["seg_gap"] = max(margins) - min(margins)
    m["seg_top"] = max(fx["seg"], key=lambda s: s["rev"])["name"]
    m["seg_low"] = min(fx["seg"], key=lambda s: s["oi"])["name"]
    m["gm26"] = a["gp"] / float(a["rev"]) * (a["rev"] * (a["rev"] / float(b["rev"])))
    fx["m"] = m

def build_all():
    fx = [build_fixture(i, p) for i, p in enumerate(SPECS)]
    for key, d in (("current", 2), ("debt_ebitda", 2), ("gm_chg", 2), ("pe", 2),
                   ("fcf_margin", 2)):
        vals = sorted(round(f["m"][key], d) for f in fx)
        assert len(set(vals)) == len(vals), "tercile tie on %s" % key
        med = round((vals[9] + vals[10]) / 2.0, d)
        for f in fx:
            f["m"]["t_" + key] = (vals[6], vals[13])
            f["m"]["med_" + key] = med
    return fx

# ---------------------------------------------------------------- contexts ---
IS_ROWS = [("Revenue", "rev", 0), ("Cost of revenue", "cogs", 0),
           ("Gross profit", "gp", 0), ("Selling general and administrative", "sga", 0),
           ("Research and development", "rnd", 0),
           ("Depreciation and amortization", "da", 0), ("Operating income", "ebit", 0),
           ("Interest expense", "interest", 0), ("Pretax income", "pretax", 0),
           ("Income tax expense", "tax", 0), ("Net income", "ni", 0),
           ("Diluted shares (millions)", "shares", 1), ("Diluted EPS", "eps", 2)]
BS_ROWS = [("Cash and equivalents", "cash", 0), ("Short-term investments", "sti", 0),
           ("Accounts receivable", "ar", 0), ("Inventory", "inv", 0),
           ("Other current assets", "oca", 0), ("Total current assets", "tca", 0),
           ("Property plant and equipment net", "ppe", 0), ("Goodwill", "gw", 0),
           ("Intangible assets", "intang", 0), ("Other non-current assets", "oa", 0),
           ("Total assets", "ta", 0), ("Accounts payable", "ap", 0),
           ("Short-term debt", "std", 0),
           ("Current portion of long-term debt", "cpltd", 0),
           ("Accrued liabilities", "accrued", 0),
           ("Total current liabilities", "tcl", 0), ("Long-term debt", "ltd", 0),
           ("Other non-current liabilities", "oncl", 0),
           ("Total liabilities", "tl", 0), ("Total shareholders equity", "equity", 0)]

def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out

def ctx_core(fx):
    a, b = fx["y25"], fx["y24"]
    L = [UNITS, "", "%s - consolidated statements (%s and %s)" % (fx["name"], fx["fy25"], fx["fy24"]), ""]
    L += table(["Item", fx["fy25"], fx["fy24"]], [[lab, num(a[k], d), num(b[k], d)] for lab, k, d in IS_ROWS])
    L.append("")
    L += table(["Balance sheet item", fx["fy25"], fx["fy24"]], [[lab, num(a[k], d), num(b[k], d)] for lab, k, d in BS_ROWS])
    L.append("")
    L += table(["Cash flow item", fx["fy25"], fx["fy24"]],
               [["Cash from operations", num(a["cfo"]), num(b["cfo"])],
                ["Capital expenditures", num(a["capex"]), num(b["capex"])],
                ["Dividends paid", num(a["divpaid"]), num(b["divpaid"])]])
    return "\n".join(L)

def ctx_market(fx):
    m, a = fx["mkt"], fx["y25"]
    L = [UNITS, "", "%s - market and per-share data at the %s year end" % (fx["name"], fx["fy25"]), ""]
    L += table(["Item", "Value"], [
        ["Share price", num(m["price"], 2)], ["Diluted shares (millions)", num(m["shares"], 1)], ["Market capitalization", num(m["mcap"])],
        ["Total debt", num(m["debt"])], ["Cash and equivalents", num(a["cash"])], ["Short-term investments", num(a["sti"])],
        ["Net debt", num(m["netdebt"])], ["EBITDA", num(m["ebitda"])], ["Total shareholders equity", num(a["equity"])],
        ["Diluted EPS", num(m["eps"], 2)], ["Dividends per share", num(m["dps"], 2)], ["Cash from operations", num(a["cfo"])],
        ["Capital expenditures", num(a["capex"])]])
    return "\n".join(L)

def ctx_partial(fx):
    a = fx["y25"]
    margin = round(ebitda_of(a) / float(a["rev"]) * 100, 1)
    L = [UNITS, "", "%s - %s liquidity worksheet (prepared by the treasury team)" % (fx["name"], fx["fy25"]), ""]
    L += table(["Item", "Value"], [
        ["Cash and equivalents", num(a["cash"])], ["Short-term investments", num(a["sti"])], ["Accounts receivable", num(a["ar"])],
        ["Inventory and prepaid expenses", num(a["inv"] + a["oca"])], ["Total current assets", num(a["tca"])],
        ["Total current liabilities", num(a["tcl"])], ["Revenue", num(a["rev"])],
        ["EBITDA margin (percent)", num(margin, 1)], ["Total debt", num(td(a))]])
    return "\n".join(L)

def ctx_covenant(fx):
    a = fx["y25"]
    L = [UNITS, "", "%s - credit agreement excerpt and %s compliance worksheet" % (fx["name"], fx["fy25"]), "",
         "| Covenant test | Definition in the agreement | Threshold |", "|---|---|---|",
         "| Consolidated EBITDA | Operating income plus depreciation and amortization | no limit |",
         "| Fixed charges | Interest expense plus scheduled principal repayments plus lease payments | no limit |",
         "| Fixed charge coverage | Operating income plus fixed charges, divided by fixed charges | at least 2.00x |",
         "| Total leverage | Total debt divided by consolidated EBITDA | at most 5.00x |",
         "| Interest coverage | Operating income divided by interest expense | at least 2.00x |", ""]
    L += table(["Reported item", fx["fy25"]], [
        ["Operating income", num(a["ebit"])], ["Depreciation and amortization", num(a["da"])],
        ["Interest expense", num(a["interest"])], ["Scheduled principal repayments", num(a["principal"])],
        ["Lease payments", num(a["lease"])], ["Total debt", num(td(a))]])
    return "\n".join(L)

def ctx_sector(fx):
    a, m = fx["y25"], fx["m"]
    L = [UNITS, "", "%s - sector benchmark medians and company inputs (%s)" % (fx["name"], fx["fy25"]), "",
         "Benchmark group for this issuer: %s." % fx["bench"], "",
         "| Metric | Banks | Utilities | Software |", "|---|---|---|---|"]
    for lab, key in (("P/E", "pe"), ("P/B", "pb"), ("EV/EBITDA", "ev")):
        cells = ["n/a" if NORMS[n][key] is None else num(NORMS[n][key], 2)
                 for n in ("Banks", "Utilities", "Software")]
        L.append("| %s | %s |" % (lab, " | ".join(cells)))
    for lab, key in (("Net margin (percent)", "nm"), ("ROE (percent)", "roe")):
        L.append("| %s | %s |" % (lab, " | ".join(num(NORMS[x][key], 1) for x in ("Banks", "Utilities", "Software"))))
    L.append("")
    L += table(["Company input", "Value"], [
        ["Share price", num(fx["mkt"]["price"], 2)], ["Diluted EPS", num(fx["mkt"]["eps"], 2)], ["Diluted shares (millions)", num(fx["mkt"]["shares"], 1)],
        ["Market capitalization", num(fx["mkt"]["mcap"])], ["Enterprise value", num(fx["mkt"]["mcap"] + m["netdebt"])],
        ["EBITDA", num(m["ebitda"])], ["Revenue", num(a["rev"])], ["Net income", num(a["ni"])],
        ["Total shareholders equity", num(a["equity"])]])
    return "\n".join(L)

def ctx_peer(fx):
    m = fx["m"]
    L = [UNITS, "", "%s - peer benchmark set of twenty listed companies (%s)" % (fx["name"], fx["fy25"]), "",
         "| Metric | Company | Peer median | 33rd percentile | 67th percentile |", "|---|---|---|---|---|"]
    for lab, key, d in (("Current ratio", "current", 2), ("Debt to EBITDA", "debt_ebitda", 2),
                        ("Gross margin change (points)", "gm_chg", 2), ("P/E", "pe", 2),
                        ("FCF margin (percent)", "fcf_margin", 2)):
        lo, hi = m["t_" + key]
        L.append("| %s | %s | %s | %s | %s |" % (lab, num(round(m[key], d), d),
                                                  num(m["med_" + key], d), num(lo, d), num(hi, d)))
    return "\n".join(L)

def ctx_memo(fx):
    a, b = fx["y25"], fx["y24"]
    L = [UNITS, "", "%s - %s annual report extract" % (fx["name"], fx["fy25"]), ""]
    L += table(["Item", fx["fy25"], fx["fy24"], "Notes"],
               [["Revenue", num(a["rev"]), num(b["rev"]), "1"],
                ["Cost of revenue", num(a["cogs"]), num(b["cogs"]), ""],
                ["Gross profit", num(a["gp"]), num(b["gp"]), ""],
                ["Inventory", num(a["inv"]), num(b["inv"]), "2"],
                ["Accounts receivable net", num(a["ar"]), num(b["ar"]), "2"],
                ["Prepaid pension asset", num(a["oa"] // 2), "", "3"],
                ["Assets held for sale", "n/a", "41", "4"],
                ["Deferred tax asset (000s)", "12400", "11800", "5"],
                ["Restructuring charge", "", "37", ""]])
    L += ["", "Notes",
          "1. Revenue is stated after excise taxes of 118.",
          "2. Inventory and receivables are shown net of a 14 allowance for doubtful accounts.",
          "3. The prepaid pension asset is measured using the 4.8 discount rate disclosed in the plan footnote.",
          "4. The FY2024 balance relates to the disposed legacy segment and is not comparable.",
          "5. The deferred tax asset is reported in thousands of dollars, not millions.",
          "6. Property plant and equipment is depreciated over useful lives of 5 to 20 years."]
    return "\n".join(L)

def ctx_debt(fx):
    L = [UNITS, "", "%s - debt schedule at the %s balance sheet date" % (fx["name"], fx["fy25"]), ""]
    rows = [[n, num(p), num(r, 2), m, s] for n, p, r, m, s in fx["debt"]]
    rows.append(["Total debt", num(td(fx["y25"])), "", "", ""])
    L += table(["Instrument", "Principal", "Coupon (percent)", "Maturity", "Security"], rows)
    return "\n".join(L)

def ctx_segment(fx):
    L = [UNITS, "", "%s - segment results (%s and %s)" % (fx["name"], fx["fy25"], fx["fy24"]), ""]
    rows = [[s["name"], num(s["rev"]), num(s["oi"]), num(s["prev_rev"]), num(s["prev_oi"])] for s in fx["seg"]]
    rows.append(["Total", num(fx["y25"]["rev"]), num(fx["y25"]["ebit"]),
                 num(fx["y24"]["rev"]), num(fx["y24"]["ebit"])])
    L += table(["Segment", fx["fy25"] + " revenue", fx["fy25"] + " operating income",
                fx["fy24"] + " revenue", fx["fy24"] + " operating income"], rows)
    return "\n".join(L)
STATED = ["Current ratio", "Quick ratio", "Debt to EBITDA", "Interest coverage"]

def stated(fx):
    m = fx["m"]
    vals = [m["current"], m["quick"], m["debt_ebitda"], m["int_cov"]]
    shown = [round(v, 2) for v in vals]
    bad = round(vals[fx["wrong"]] * (1.26 + 0.09 * fx["wrong"]), 2)
    for k, v in enumerate(shown):
        if k != fx["wrong"]:
            assert abs(v - bad) > 0.08, "collision"
    shown[fx["wrong"]] = bad
    return shown

def ctx_stated(fx):
    a = fx["y25"]
    shown = stated(fx)
    L = [UNITS, "", "%s - analyst note with stated ratios (%s)" % (fx["name"], fx["fy25"]), ""]
    L += table(["Reported input", fx["fy25"]], [
        ["Cash and equivalents", num(a["cash"])], ["Short-term investments", num(a["sti"])], ["Accounts receivable", num(a["ar"])],
        ["Inventory", num(a["inv"])], ["Total current assets", num(a["tca"])], ["Total current liabilities", num(a["tcl"])],
        ["Total debt", num(td(a))], ["Operating income", num(a["ebit"])], ["Depreciation and amortization", num(a["da"])],
        ["Interest expense", num(a["interest"])]])
    L.append("")
    L += table(["Stated ratio", "Value"], [["Current ratio", num(shown[0], 2)], ["Quick ratio", num(shown[1], 2)],
                                            ["Debt to EBITDA", num(shown[2], 2)], ["Interest coverage", num(shown[3], 2)]])
    return "\n".join(L)
CTX = dict(core=ctx_core, market=ctx_market, partial=ctx_partial,
           covenant=ctx_covenant, sector=ctx_sector, peer=ctx_peer,
           memo=ctx_memo, debt=ctx_debt, segment=ctx_segment, stated=ctx_stated)

# ---------------------------------------------------------------- families ---
def r0(v): return (round(v, 1), "number", "abs:1")

def r1(v): return (round(v, 1), "number", "abs:0.1")

def r2(v): return (round(v, 2), "number", "abs:0.01")

def st(v): return (v, "text", "exact")

def tx(v): return (v, "text", "normalized")

def lb(v): return (v, "label", "exact")

def partial_quick(fx):
    a = fx["y25"]
    return r2((a["tca"] - a["inv"] - a["oca"]) / float(a["tcl"]))

def partial_debt(fx):
    a = fx["y25"]
    margin = round(ebitda_of(a) / float(a["rev"]) * 100, 1)
    return r2(td(a) / (a["rev"] * margin / 100.0))
CALC = [
    ("calc_current", "core", "What is the FY2025 current ratio?", ("current", 2)),
    ("calc_quick", "core", "What is the FY2025 quick ratio, with quick assets defined as cash and equivalents plus short-term investments plus accounts receivable?", ("quick", 2)),
    ("calc_cash", "core", "What is the FY2025 cash ratio, defined as cash and equivalents plus short-term investments divided by total current liabilities?", ("cash_r", 2)),
    ("calc_debt_ebitda", "core", "What is the FY2025 debt-to-EBITDA ratio? Total debt is short-term debt plus the current portion of long-term debt plus long-term debt, and EBITDA is operating income plus depreciation and amortization.", ("debt_ebitda", 2)),
    ("calc_netdebt_ebitda", "core", "What is the FY2025 net debt to EBITDA ratio? Net debt is total debt less cash and equivalents and short-term investments, and EBITDA is operating income plus depreciation and amortization.", ("netdebt_ebitda", 2)),
    ("calc_int_cov", "core", "What is the FY2025 interest coverage ratio, measured as operating income divided by interest expense?", ("int_cov", 2)),
    ("calc_fcc", "covenant", "Under the definitions in the credit agreement excerpt, what is the FY2025 fixed charge coverage ratio?", ("fcc", 2)),
    ("calc_asset_turn", "core", "What is the FY2025 asset turnover, computed on average total assets?", ("asset_turn", 2)),
    ("calc_inv_turns", "core", "What is the FY2025 inventory turnover, computed as cost of revenue divided by average inventory?", ("inv_turns", 1)),
    ("calc_dso", "core", "What was the FY2025 days sales outstanding, using average accounts receivable and a 365-day year?", ("dso", 1)),
    ("calc_ccc", "core", "What is the FY2025 cash conversion cycle in days, computed from average balances over a 365-day year?", ("ccc", 1)),
    ("calc_dup3_roe", "core", "What is the FY2025 return on equity under the three-step DuPont decomposition, using net margin, asset turnover on average assets and the average equity multiplier? Report it in percent.", ("dup3_roe", 1)),
    ("calc_dup5_tax", "core", "In the five-step DuPont decomposition, what is the FY2025 tax burden, measured as net income divided by pretax income?", ("dup5_tax", 1)),
    ("calc_dup5_int", "core", "In the five-step DuPont decomposition, what is the FY2025 interest burden, measured as pretax income divided by operating income?", ("dup5_int", 1)),
    ("calc_pe", "market", "What is the FY2025 price-to-earnings ratio, using the year end share price and diluted earnings per share?", ("pe", 2)),
    ("calc_pb", "market", "What is the FY2025 price-to-book ratio, using market capitalization and year end total shareholders equity?", ("pb", 2)),
    ("calc_ev", "market", "What is the FY2025 EV-to-EBITDA multiple, with enterprise value taken as market capitalization plus net debt?", ("ev_ebitda", 2)),
    ("calc_payout", "market", "What is the FY2025 dividend payout ratio, measured as dividends per share divided by diluted earnings per share?", ("payout", 1)),
    ("calc_fcf_yield", "market", "What is the FY2025 free cash flow yield, with free cash flow taken as cash from operations less capital expenditures?", ("fcf_yield", 2)),
    ("calc_partial_quick", "partial", "The worksheet reports inventory and prepaid expenses on a single combined line. What is the FY2025 quick ratio?", partial_quick),
    ("calc_partial_debt", "partial", "The worksheet gives the EBITDA margin instead of an EBITDA figure. What is the FY2025 debt-to-EBITDA ratio?", partial_debt),
    ("calc_fcc_headroom", "covenant", "By how many turns does FY2025 fixed charge coverage exceed the minimum threshold in the credit agreement excerpt?", lambda fx: r2(fx["m"]["fcc"] - 2.00)),
    ("calc_pe_gap", "sector", "What is the gap in turns between the company's FY2025 P/E and the benchmark median P/E shown in the table (company minus median)?", ("pe_gap", 1)),
    ("calc_growth_gp", "core", "If FY2026 revenue grows at the same percentage rate as FY2025 and the FY2025 gross margin is maintained, what is FY2026 gross profit in millions?", lambda fx: r0(fx["m"]["gm26"])),
    ("calc_margin_chg", "core", "By how many percentage points did the operating margin change between FY2024 and FY2025?", ("om_chg", 1)),
    ("calc_dup3_em", "core", "What is the equity multiplier component of the three-step DuPont decomposition for FY2025, using average assets and average equity?", ("dup3_em", 2)),
]
EXTR = [
    ("ex_tca", "core", "Copy the FY2025 figure printed for Total current assets, exactly as shown.", lambda fx: st(num(fx["y25"]["tca"]))),
    ("ex_inv", "core", "Copy the FY2025 figure printed for Inventory, exactly as shown.", lambda fx: st(num(fx["y25"]["inv"]))),
    ("ex_foot3", "memo", "Footnote 3 attaches to which line item? Give the line item label exactly as printed in the table.", lambda fx: st("Prepaid pension asset")),
    ("ex_blank", "memo", "Which line item has an empty FY2025 cell in the table? Give its label exactly as printed.", lambda fx: st("Restructuring charge")),
    ("ex_na", "memo", "Which line item is marked n/a in the table? Give its label exactly as printed.", lambda fx: st("Assets held for sale")),
    ("ex_000s", "memo", "One line in the table is reported in thousands of dollars. What number is printed for that line in FY2025, exactly as shown?", lambda fx: st("12400")),
    ("ex_foot2", "memo", "According to footnote 2, the inventory and receivables balances are shown net of what item? Quote the footnote phrase exactly.", lambda fx: st("a 14 allowance for doubtful accounts")),
    ("ex_seg_top", "segment", "Which reportable segment reported the highest FY2025 revenue? Give the segment name exactly as printed.", lambda fx: st(fx["m"]["seg_top"])),
    ("ex_tla", "debt", "What maturity date is shown for Term loan A in the debt schedule?", lambda fx: st(fx["debt"][2][3])),
    ("ex_rcf", "debt", "What is the exact name used for the revolving facility in the debt schedule?", lambda fx: st(fx["debt"][1][0])),
    ("ex_foot4", "memo", "According to footnote 4, which disposed business does the FY2024 balance relate to? Quote the footnote phrase exactly.", lambda fx: st("the disposed legacy segment")),
    ("ex_eps", "core", "Copy the FY2025 diluted EPS figure exactly as printed, including both decimal places.", lambda fx: st(num(fx["y25"]["eps"], 2))),
    ("ex_foot6", "memo", "What range of useful lives does footnote 6 state for property plant and equipment?", lambda fx: st("5 to 20 years")),
    ("ex_oncl", "core", "Copy the FY2025 figure printed for Other non-current liabilities, exactly as shown.", lambda fx: st(num(fx["y25"]["oncl"]))),
    ("ex_capex", "core", "Copy the FY2025 capital expenditure figure from the cash flow section, exactly as shown.", lambda fx: st(num(fx["y25"]["capex"]))),
    ("ex_n31", "debt", "What principal amount is shown for the senior notes due 2031 in the debt schedule?", lambda fx: st(num(fx["debt"][3][1]))),
    ("ex_seg_low", "segment", "Which reportable segment reported the lowest FY2025 operating income? Give the segment name exactly as printed.", lambda fx: st(fx["m"]["seg_low"])),
    ("ex_000s_prev", "memo", "What number is printed for the deferred tax asset in FY2024, exactly as shown?", lambda fx: st("11800")),
]
QA = [
    ("qa_cov_headroom", "covenant", "By how many turns of headroom does FY2025 interest coverage clear the covenant floor stated in the excerpt?", lambda fx: r2(fx["m"]["int_cov"] - 2.00)),
    ("qa_gm_chg", "core", "By how many percentage points did the gross margin change between FY2024 and FY2025?", ("gm_chg", 1)),
    ("qa_div_cover", "core", "How many times over does FY2025 net income cover the dividends actually paid?", ("div_cover", 2)),
    ("qa_rev_growth", "core", "What was the percentage growth in revenue from FY2024 to FY2025?", ("rev_growth", 1)),
    ("qa_inv_implied", "core", "If the FY2025 quick ratio, taken as cash, short-term investments and receivables over total current liabilities, had been exactly 1.00, what inventory balance would that imply while every other current asset and total current liabilities stayed at their reported levels?", ("inv_implied", 1)),
    ("qa_ev_bench", "sector", "At the benchmark median EV-to-EBITDA multiple shown in the table, what enterprise value would the company's FY2025 EBITDA support, in millions?", lambda fx: r0(fx["m"]["ev_at_bench"])),
    ("qa_delever", "core", "If all FY2025 free cash flow were applied to debt reduction, how many years would it take to halve net debt?", ("delever_years", 2)),
    ("qa_seg_gap", "segment", "What is the difference in FY2025 operating margin between the highest-margin segment and the lowest-margin segment, in percentage points?", ("seg_gap", 1)),
    ("qa_wac", "debt", "What is the weighted average stated coupon on the debt in the schedule, in percent? Weight by principal.", ("wa_coupon", 2)),
    ("qa_roe_chg", "core", "What was the change in return on equity from FY2024 to FY2025, in percentage points, using year end shareholders equity for both years?", ("roe_chg", 1)),
    ("qa_fcf_conv", "core", "What is the FY2025 free cash flow conversion, measured as free cash flow divided by net income?", ("fcf_conv", 1)),
    ("qa_dso_chg", "core", "By how many days did days sales outstanding change between FY2024 and FY2025, using closing receivables in both years?", ("dso_chg", 1)),
    ("qa_nm_gap", "sector", "What is the gap in percentage points between the company's FY2025 net margin and the benchmark median net margin shown in the table (company minus median)?", ("nm_gap", 1)),
    ("qa_fcf_cover", "core", "How many times does FY2025 free cash flow cover the dividends actually paid?", ("fcf_cover", 2)),
    ("qa_capex_int", "core", "What is the FY2025 capital expenditure intensity, measured as capital expenditures divided by revenue?", ("capex_int", 1)),
    ("qa_stated_bad", "stated", "An analyst note states four ratios for the year. Given the reported inputs in the table, exactly one of the stated ratios cannot be right. Which one is it? Answer with the ratio name exactly as printed.", lambda fx: lb(STATED[fx["wrong"]])),
    ("qa_at_chg", "core", "By how many turns did asset turnover change between FY2024 and FY2025, using year end assets in both years?", ("at_chg", 2)),
    ("qa_payout_ni", "core", "What is the FY2025 payout ratio implied by dividends paid and net income?", ("payout_ni", 1)),
    ("qa_int_headroom", "covenant", "How much additional interest expense could the company have carried in FY2025 before interest coverage fell to the covenant floor?", lambda fx: r0(fx["m"]["int_headroom"])),
    ("qa_pe_gap", "sector", "How many turns above or below the benchmark median P/E shown in the table does the company's FY2025 P/E sit? Report the company figure minus the median.", ("pe_gap", 1)),
]

def cls_gt(key, labels):
    def g(fx):
        lo, hi = fx["m"]["t_" + key]
        v = round(fx["m"][key], 2)
        return (labels[0 if v <= lo else (1 if v <= hi else 2)], "label", "exact")
    return g
CLS = [
    ("cls_current", "peer", "Using the peer percentiles in the table, classify the company's FY2025 current ratio as one of {tight, in_line, comfortable}. Values at or below the 33rd percentile are tight, values above the 67th percentile are comfortable, and every other value is in_line.", cls_gt("current", ("tight", "in_line", "comfortable"))),
    ("cls_leverage", "peer", "Using the peer percentiles in the table, classify the company's FY2025 debt to EBITDA as one of {conservative, moderate, aggressive}. Values at or below the 33rd percentile are conservative, values above the 67th percentile are aggressive, and every other value is moderate.", cls_gt("debt_ebitda", ("conservative", "moderate", "aggressive"))),
    ("cls_margin", "peer", "Using the peer percentiles in the table, classify the company's FY2025 gross margin change as one of {contracting, stable, expanding}. Values at or below the 33rd percentile are contracting, values above the 67th percentile are expanding, and every other value is stable.", cls_gt("gm_chg", ("contracting", "stable", "expanding"))),
    ("cls_valuation", "peer", "Using the peer percentiles in the table, classify the company's FY2025 P/E as one of {discount, in_line, premium}. Values at or below the 33rd percentile are a discount, values above the 67th percentile are a premium, and every other value is in_line.", cls_gt("pe", ("discount", "in_line", "premium"))),
    ("cls_cash", "peer", "Using the peer percentiles in the table, classify the company's FY2025 free cash flow margin as one of {weak, average, strong}. Values at or below the 33rd percentile are weak, values above the 67th percentile are strong, and every other value is average.", cls_gt("fcf_margin", ("weak", "average", "strong"))),
]

def summ_is(fx):
    a, b = fx["y25"], fx["y24"]
    return tx("Revenue moved to %s from %s while operating income was %s against %s. "
              "Net income came in at %s versus %s and diluted EPS was %s compared with %s." %
              (num(a["rev"]), num(b["rev"]), num(a["ebit"]), num(b["ebit"]),
               num(a["ni"]), num(b["ni"]), num(a["eps"], 2), num(b["eps"], 2)))

def summ_bs(fx):
    a, b = fx["y25"], fx["y24"]
    return tx("Total assets ended the year at %s against %s, with total liabilities of %s "
              "and shareholders equity of %s. Long-term debt was %s versus %s a year earlier." %
              (num(a["ta"]), num(b["ta"]), num(a["tl"]), num(a["equity"]),
               num(a["ltd"]), num(b["ltd"])))

def summ_seg(fx):
    seg = sorted(fx["seg"], key=lambda s: -s["rev"])
    return tx("The largest segment, %s, reported revenue of %s and operating income of %s. "
              "%s reported revenue of %s and operating income of %s." %
              (seg[0]["name"], num(seg[0]["rev"]), num(seg[0]["oi"]),
               seg[1]["name"], num(seg[1]["rev"]), num(seg[1]["oi"])))

def summ_debt(fx):
    d = fx["debt"]
    return tx("Total debt of %s comprises commercial paper of %s, a revolving credit facility "
              "of %s, term loan A of %s and senior notes due 2031 and 2033 of %s and %s. "
              "The schedule lists five instruments with maturities from February 2027 to "
              "March 2033." % (num(td(fx["y25"])), num(d[0][1]), num(d[1][1]), num(d[2][1]),
                               num(d[3][1]), num(d[4][1])))

def summ_cf(fx):
    a = fx["y25"]
    return tx("Cash from operations was %s against capital expenditures of %s. "
              "Dividends paid absorbed %s, so the year left a free cash flow surplus "
              "after capital spending." % (num(a["cfo"]), num(a["capex"]), num(a["divpaid"])))
SUMM = [
    ("summ_income", "core", "Summarize the FY2025 income statement results in two sentences using only figures shown in the table.", summ_is),
    ("summ_balance", "core", "Summarize the FY2025 balance sheet position in two sentences using only figures shown in the table.", summ_bs),
    ("summ_segment", "segment", "Summarize the two largest segments by FY2025 revenue in two sentences using only figures shown in the table.", summ_seg),
    ("summ_debt", "debt", "Summarize the debt schedule in two sentences using only figures shown in the table.", summ_debt),
    ("summ_cash", "core", "Summarize the FY2025 cash flow and shareholder distributions in two sentences using only figures shown in the table.", summ_cf),
]

def mkf(r):
    key, kind, q, g = r
    if isinstance(g, tuple):
        name, d = g
        tol = {0: "abs:1", 1: "abs:0.1", 2: "abs:0.01"}[d]
        return dict(key=key, kind=kind, q=q,
                    gt=lambda fx, n=name, dd=d, t=tol: (round(fx["m"][n], dd), "number", t))
    return dict(key=key, kind=kind, q=q, gt=g)
CALC = [mkf(r) for r in CALC]
EXTR = [mkf(r) for r in EXTR]
QA = [mkf(r) for r in QA]
CLS = [mkf(r) for r in CLS]
SUMM = [mkf(r) for r in SUMM]

# --------------------------------------------------------------- tool rows ---
FIN_TOOL = {"name": "get_financial_summary",
            "description": "Return reported line items for one fiscal period and one statement section.",
            "parameters": {"type": "object", "properties": {
                "period": {"type": "string", "description": "Fiscal period label such as FY2025."},
                "section": {"type": "string", "enum": ["income", "balance_sheet", "cash_flow"]}},
                "required": ["period", "section"]}}
MKT_TOOL = {"name": "get_market_snapshot",
            "description": "Return the fiscal year end share price and diluted share count for an issuer id.",
            "parameters": {"type": "object", "properties": {"issuer_id": {"type": "string"}},
                           "required": ["issuer_id"]}}

def call(name, args, note):
    return note + "\n" + json.dumps({"name": name, "arguments": args})

def bs_items(fx, drop=()):
    a = fx["y25"]
    d = {"cash_and_equivalents": a["cash"], "short_term_investments": a["sti"],
         "accounts_receivable": a["ar"], "inventory": a["inv"],
         "other_current_assets": a["oca"], "total_current_assets": a["tca"],
         "total_current_liabilities": a["tcl"], "short_term_debt": a["std"],
         "current_portion_of_long_term_debt": a["cpltd"], "long_term_debt": a["ltd"],
         "total_shareholders_equity": a["equity"]}
    for k in drop:
        d.pop(k, None)
    return d

def inc_items(fx):
    a = fx["y25"]
    return {"revenue": a["rev"], "cost_of_revenue": a["cogs"], "gross_profit": a["gp"],
            "operating_income": a["ebit"], "depreciation_and_amortization": a["da"],
            "interest_expense": a["interest"], "net_income": a["ni"],
            "diluted_eps": a["eps"]}

def t_liquidity(fx):
    m = [{"role": "user", "content": "Pull the FY2025 balance sheet for the issuer in this file and report its current ratio."},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "FY2025", "section": "balance_sheet"}, "Fetching the FY2025 balance sheet.")},
         {"role": "tool", "content": json.dumps({"period": "FY2025", "section": "balance_sheet", "issuer_id": fx["key"], "line_items": bs_items(fx)})},
         {"role": "user", "content": "Using that output, what is the FY2025 current ratio? Give two decimals."}]
    return m, [FIN_TOOL], r2(fx["m"]["current"])

def t_leverage_retry(fx):
    m = [{"role": "user", "content": "I need FY2025 debt to EBITDA for the issuer. Start with the balance sheet."},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "2025", "section": "balance_sheet"}, "Fetching the balance sheet.")},
         {"role": "tool", "content": json.dumps({"error": "unknown period", "valid_periods": ["FY2025", "FY2024"]})},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "FY2025", "section": "balance_sheet"}, "The period label was rejected. Retrying with FY2025.")},
         {"role": "tool", "content": json.dumps({"period": "FY2025", "section": "balance_sheet", "issuer_id": fx["key"], "line_items": bs_items(fx)})},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "FY2025", "section": "income"}, "Balance sheet is in. Pulling the income statement for EBITDA.")},
         {"role": "tool", "content": json.dumps({"period": "FY2025", "section": "income", "issuer_id": fx["key"], "line_items": inc_items(fx)})},
         {"role": "user", "content": "Now give me debt to EBITDA, with total debt as short-term debt plus the current portion of long-term debt plus long-term debt."}]
    return m, [FIN_TOOL], r2(fx["m"]["debt_ebitda"])

def t_margin(fx):
    m = [{"role": "user", "content": "Pull FY2025 revenue and cost of revenue for the issuer."},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "FY2025", "section": "income"}, "Fetching the FY2025 income statement.")},
         {"role": "tool", "content": json.dumps({"period": "FY2025", "section": "income", "issuer_id": fx["key"], "line_items": inc_items(fx)})},
         {"role": "user", "content": "What gross margin does that imply, in percent?"}]
    return m, [FIN_TOOL], r1(fx["m"]["gm"])

def t_insufficient(fx):
    m = [{"role": "user", "content": "I need the FY2025 inventory turnover for the issuer. Pull the balance sheet first."},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "FY2025", "section": "balance_sheet"}, "Fetching the FY2025 balance sheet.")},
         {"role": "tool", "content": json.dumps({"period": "FY2025", "section": "balance_sheet", "issuer_id": fx["key"], "line_items": bs_items(fx, drop=("inventory",))})},
         {"role": "assistant", "content": call(FIN_TOOL["name"], {"period": "FY2025", "section": "inventory_detail"}, "The balance sheet response has no inventory line. Trying an inventory detail section.")},
         {"role": "tool", "content": json.dumps({"error": "unknown section", "valid_sections": ["income", "balance_sheet", "cash_flow"]})},
         {"role": "user", "content": "Given the tool output, what is the correct status for the inventory turnover request?"}]
    return m, [FIN_TOOL], lb("insufficient data")

def t_market(fx):
    m = [{"role": "user", "content": "Get the FY2025 year end share price and diluted share count for the issuer; I need to size the equity value."},
         {"role": "assistant", "content": call(MKT_TOOL["name"], {"issuer_id": fx["key"]}, "Fetching the market snapshot.")},
         {"role": "tool", "content": json.dumps({"issuer_id": fx["key"], "period": "FY2025", "share_price": fx["mkt"]["price"], "diluted_shares_millions": fx["mkt"]["shares"]})},
         {"role": "user", "content": "What is market capitalization in millions?"}]
    return m, [MKT_TOOL], r0(fx["mkt"]["mcap"])
TOOL = [("tool_liquidity", t_liquidity), ("tool_leverage_retry", t_leverage_retry),
        ("tool_margin", t_margin), ("tool_insufficient", t_insufficient),
        ("tool_market", t_market)]
KNOW = [
    ("What are the three components of the three-step DuPont decomposition?",
     lambda fx: (["net profit margin", "asset turnover", "equity multiplier"], "list", "ordered")),
    ("Which line item separates operating income from pretax income on the income statement?",
     lambda fx: tx("interest expense")),
    ("Name, in order, the three components that are added and subtracted to give the cash conversion cycle.",
     lambda fx: (["days sales outstanding", "days inventory outstanding", "days payable outstanding"], "list", "ordered")),
    ("In a five-step DuPont decomposition, which component captures the effect of income taxes?",
     lambda fx: tx("tax burden")),
    ("Which is the stricter liquidity test, the quick ratio or the ratio that includes inventory?",
     lambda fx: lb("quick ratio")),
    ("Are dividend payments reported in operating cash flow or in financing cash flow under US GAAP?",
     lambda fx: lb("financing cash flow")),
    ("What does the equity multiplier measure?",
     lambda fx: tx("total assets divided by shareholders equity")),
    ("Which two balance sheet items are netted to produce net debt?",
     lambda fx: tx("cash and short-term investments")),
]
ABBR = dict(calc="calc", extraction="extr", summarization="summ",
            classification="cls", qa="qa", tool_use="tool")
PLAN = [("calc", CALC, 14), ("extraction", EXTR, 11), ("qa", QA, 10),
        ("classification", CLS, 5), ("summarization", SUMM, 5)]

def build_for(fx, know_idx=None):
    out = []
    for task, pool, slots in PLAN:
        for k in range(slots):
            f = pool[(fx["i"] * 7 + k) % len(pool)]
            gt, at, tol = f["gt"](fx)
            out.append(dict(task=task, ctx=CTX[f["kind"]](fx), q=f["q"], gt=gt,
                            at=at, tol=tol, fam=f["key"], split=fx["split"]))
    for k in range(5):
        key, fn = TOOL[(fx["i"] * 7 + k) % len(TOOL)]
        msgs, tools, (gt, at, tol) = fn(fx)
        out.append(dict(task="tool_use", msgs=msgs, tools=tools, gt=gt, at=at,
                        tol=tol, fam=key, split=fx["split"]))
    if know_idx is not None:
        pos = [j for j, r in enumerate(out) if r["task"] == "qa"][-1]
        q, g = KNOW[know_idx]
        gt, at, tol = g(fx)
        out[pos] = dict(task="qa", ctx="", q=q, gt=gt, at=at, tol=tol,
                        fam="know", split=fx["split"])
    return out

def main():
    fx = build_all()
    order = sorted(range(len(fx)),
                   key=lambda i: hashlib.sha256(fx[i]["key"].encode()).hexdigest())
    for pos, i in enumerate(order):
        fx[i]["split"] = "train" if pos < 16 else ("val" if pos < 18 else "test")
    train8 = set(order[:8])
    rows = []
    for f in fx:
        rows.extend(build_for(f, order.index(f["i"]) if f["i"] in train8 else None))
    counts = Counter()
    for r in rows:
        counts[r["task"]] += 1
        r["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[r["task"]], counts[r["task"]])
    seen = set()
    for r in rows:
        key = (r["ctx"], r["q"]) if "ctx" in r else json.dumps(r["msgs"], sort_keys=True)
        assert key not in seen, "duplicate body"
        seen.add(key)
        if r["task"] == "extraction":
            assert r["gt"] in r["ctx"], "span missing: %r" % (r["gt"],)
    emit(rows)

def mask(s): return re.sub(r"\d+(?:[.,]\d+)*", "#", re.sub(r"\s+", " ", s).strip().lower())

def emit(rows):
    lines = []
    for r in rows:
        if "ctx" in r:
            obj = dict(id=r["id"], task=r["task"], source="synthetic:" + AREA,
                       context=r["ctx"], question=r["q"], ground_truth=r["gt"],
                       answer_type=r["at"], tolerance=r["tol"], split=r["split"],
                       thinking="on" if r["task"] in ("calc", "qa", "tool_use") else "off")
            if r["ctx"] == "":
                obj["source"] = "knowledge:finance_general"
        else:
            obj = dict(id=r["id"], task=r["task"], source="synthetic:" + AREA,
                       messages=r["msgs"], tools=r["tools"], ground_truth=r["gt"],
                       answer_type=r["at"], tolerance=r["tol"], split=r["split"],
                       thinking="on")
        lines.append(json.dumps(obj, ensure_ascii=True, sort_keys=False))
    blob = "\n".join(lines) + "\n"
    assert all(ord(c) < 128 for c in blob), "non-ascii output"
    with open(os.path.join(HERE, "prompts.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob)
    report(rows, blob)

def report(rows, blob):
    bt = Counter(r["task"] for r in rows)
    bs = Counter(r["split"] for r in rows)
    ba = Counter(r["at"] for r in rows if r["gt"] is not None)
    fams, ctxs, bodies = Counter(), set(), {}
    tool_n = tool_multi = 0
    for r in rows:
        if "ctx" in r:
            fams[mask(r["q"])[:160]] += 1
            if r["ctx"]:
                ctxs.add(mask(r["ctx"]))
            bodies.setdefault(mask(r["ctx"]) + "|" + mask(r["q"]), set()).add(r["split"])
        else:
            fams[mask(next(m["content"] for m in r["msgs"] if m["role"] == "user"))[:160]] += 1
            tool_n += 1
            tool_multi += 1 if any(m["role"] == "assistant" for m in r["msgs"]) else 0
            bodies.setdefault(json.dumps(r["msgs"], sort_keys=True), set()).add(r["split"])
    dup = sum(1 for v in bodies.values() if len(v) > 1)
    top = fams.most_common(1)[0]
    rep = dict(area=AREA, profile="A", rows=len(rows), by_task=dict(bt),
               by_split=dict(bs), by_answer_type=dict(ba),
               distinct_question_families=len(fams),
               top_family_share=round(top[1] / float(len(rows)), 4),
               distinct_contexts=len(ctxs), near_dup_pairs=dup,
               tool_use_multi_step_share=round(tool_multi / float(tool_n), 3),
               validation="pass", sha256=hashlib.sha256(blob.encode("utf-8")).hexdigest(),
               notes="Synthetic ratio fixtures, 20 issuers, %d question families." % len(fams))
    with open(os.path.join(HERE, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(rep, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
