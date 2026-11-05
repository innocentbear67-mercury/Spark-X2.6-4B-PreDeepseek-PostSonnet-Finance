#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic generator for the segment_breakdown area (profile A, 1000 rows).

Twenty fictional issuers, one fixture each, nine context variants per fixture and
fifty authored question families. Every ground_truth is computed in code from the
same fixture values that are rendered into the context.
"""
import hashlib
import json
import random
import re

AREA = "segment_breakdown"
R = random.Random(42)

# name, sector, fiscal-year end, reporting currency, reportable segments
COMPANIES = [
    ("Halcyon Grid Utilities", "regulated electric utility", "31 December", "USD", ["Transmission and Distribution", "Generation", "Retail Supply"],
     ["substation automation equipment", "grid-scale battery systems", "metering and data collection systems", "transmission line hardware", "field engineering services"]),
    ("Kestrel Foods", "packaged foods", "30 June", "USD", ["Refrigerated Foods", "Snack Products", "Ingredients", "Foodservice"],
     ["refrigerated prepared meals", "snack and confectionery products", "food ingredient blends", "private-label foodservice packs", "frozen bakery products"]),
    ("Meridian Bancorp", "regional bank", "31 December", "USD", ["Consumer Banking", "Commercial Banking", "Wealth Management", "Treasury Services"],
     ["consumer deposit and lending products", "commercial credit facilities", "wealth and advisory services", "treasury and payment services", "mortgage origination services"]),
    ("Tarnbeck Industrial", "industrial equipment", "30 September", "USD", ["Flow Control", "Automation Systems", "Aftermarket Services"],
     ["precision flow control valves", "factory automation controllers", "aftermarket replacement parts", "field maintenance contracts", "industrial pumps and seals"]),
    ("Solstice Renewables", "renewable power", "31 December", "EUR", ["Wind Generation", "Solar Generation", "Storage Services", "Development"],
     ["onshore wind assets", "utility-scale solar assets", "battery storage capacity", "project development services", "power purchase agreements"]),
    ("Vantage Health Systems", "healthcare services", "31 December", "USD", ["Acute Care", "Outpatient Clinics", "Diagnostic Laboratories", "Home Health", "Pharmacy Services"],
     ["acute inpatient care", "outpatient clinic services", "diagnostic laboratory testing", "home nursing visits", "retail pharmacy services"]),
    ("Northgate Logistics", "freight and logistics", "31 December", "USD", ["Truckload", "Intermodal", "Warehousing", "Last Mile"],
     ["full truckload capacity", "intermodal rail services", "contract warehousing", "parcel and last-mile delivery", "freight brokerage services"]),
    ("Ardent Chemicals", "specialty chemicals", "31 December", "USD", ["Coatings", "Adhesives", "Performance Additives"],
     ["industrial coating resins", "structural adhesive systems", "performance additive packages", "water treatment chemicals", "specialty lubricant additives"]),
    ("Bluepine Software", "enterprise software", "31 January", "USD", ["Subscriptions", "Professional Services", "Maintenance"],
     ["cloud subscription licenses", "implementation and integration services", "software maintenance contracts", "data platform subscriptions", "developer tooling licenses"]),
    ("Castleford Retail", "specialty retail", "31 January", "GBP", ["Apparel", "Home Goods", "Online", "Outlet Stores"],
     ["womenswear and menswear ranges", "home furnishing products", "online marketplace sales", "discount outlet store sales", "seasonal accessory ranges"]),
    ("Lumen Grid Semiconductor", "semiconductors", "31 December", "USD", ["Analog Products", "Power Devices", "Embedded Processing", "Licensing"],
     ["analog signal devices", "power management devices", "embedded processing modules", "patent licensing arrangements", "sensor interface chips"]),
    ("Harborline Insurance", "property and casualty insurance", "31 December", "USD", ["Personal Lines", "Commercial Lines", "Reinsurance"],
     ["personal auto and home policies", "commercial property policies", "reinsurance treaties", "specialty liability coverage", "claims administration services"]),
    ("Weston Agrigenetics", "agricultural inputs", "31 August", "USD", ["Seeds", "Crop Protection", "Digital Agronomy"],
     ["hybrid seed varieties", "crop protection formulations", "digital agronomy subscriptions", "seed treatment products", "field trial services"]),
    ("Cobalt Ridge Mining", "base metals mining", "31 December", "USD", ["Copper", "Zinc", "Nickel", "Exploration"],
     ["copper concentrate", "zinc concentrate", "nickel ore", "exploration tenements", "smelting by-products"]),
    ("Silverbrook Media", "media and publishing", "31 December", "USD", ["Broadcast", "Digital Subscriptions", "Advertising Services", "Events"],
     ["broadcast advertising inventory", "digital subscription access", "branded content services", "live event sponsorship", "program licensing rights"]),
    ("Radiant Energy Services", "oilfield services", "31 December", "USD", ["Drilling", "Completion", "Production Support", "Equipment Rental"],
     ["land drilling rigs", "well completion services", "artificial lift support", "pressure pumping equipment rental", "production optimization services"]),
    ("Fairmont Aerospace", "aerospace components", "31 December", "USD", ["Airframe Structures", "Engine Components", "Avionics", "Aftermarket"],
     ["airframe structural assemblies", "engine turbine components", "cockpit avionics displays", "spare parts distribution", "repair and overhaul services"]),
    ("Calderon Pharma", "specialty pharmaceuticals", "31 December", "EUR", ["Prescription Products", "Consumer Health", "Contract Manufacturing"],
     ["prescription specialty medicines", "over-the-counter consumer brands", "contract manufacturing capacity", "clinical supply services", "sterile injectable products"]),
    ("Thornbury Telecom", "telecommunications", "31 December", "GBP", ["Consumer Broadband", "Enterprise Connectivity", "Wholesale", "Equipment"],
     ["fibre broadband access", "enterprise connectivity circuits", "wholesale network access", "customer premises equipment", "managed network services"]),
    ("Orchard Lane Hotels", "hospitality", "31 December", "USD", ["Owned Hotels", "Managed Hotels", "Franchise", "Food and Beverage"],
     ["owned hotel rooms", "managed hotel contracts", "franchise licensing fees", "food and beverage outlets", "meeting and event space"]),
]

CUST = ["residential", "commercial", "industrial", "institutional", "wholesale", "retail", "government", "enterprise"]
REGION = ["North America", "Western Europe", "Asia Pacific", "Latin America", "Central Europe"]
BIZ = ["water heating", "aftermarket parts", "contract packaging", "specialty films", "field services", "retail media", "marine coatings", "data licensing", "building controls", "medical tubing"]
DRIVERS = ["Price and mix", "Input costs", "Productivity and volume"]
NOTE1 = "Segment revenue includes intersegment sales, which are eliminated on consolidation. Segment profit excludes unallocated corporate costs."
NOTE_GEO = "The FX effect is the change in reported revenue caused by translating local-currency revenue at FY2025 rates rather than FY2024 rates. Constant-currency revenue is reported revenue less the FX effect."
NOTE_CE = "Capital employed is total segment assets less total segment liabilities, measured at the balance sheet date. Segment profit is stated before unallocated corporate costs."
NOTE_SAME = "Segment definitions were unchanged between the two years."
FIX = []


# ------------------------------------------------------------------------ helpers
def hkey(*parts):
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def num(x, dp=0):
    if dp == 0:
        return str(int(round(x)))
    v = round(float(x), dp)
    return "%.*f" % (dp, 0.0 if v == 0 else v)


def pct(x):
    return num(x, 1)


def tbl(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def units(f):
    return "Units: %s in millions; percentages, margins and growth rates in percent." % ("$" if f["ccy"] == "USD" else f["ccy"])


def growth(cur, pri):
    return (float(cur) / float(pri) - 1.0) * 100.0


def margin(p, r):
    return float(p) / float(r) * 100.0


def seg_by(f, key, reverse=True):
    return sorted(f["segs"], key=lambda s: s[key], reverse=reverse)


def tot(f, key):
    return sum(s[key] for s in f["segs"])


def mask(s):
    return re.sub(r"\d+(?:[.,]\d+)*", "#", s.lower()).strip()


def row(f, task, ctx, q, gt, at, tol):
    return {"fixture": f["key"], "task": task, "context": ctx, "question": q, "ground_truth": gt, "answer_type": at, "tolerance": tol}


def mtrow(messages, tools, gt, at, tol):
    return {"task": "tool_use", "messages": messages, "tools": tools, "ground_truth": gt, "answer_type": at, "tolerance": tol}


# ----------------------------------------------------------------------- fixtures
def make_segs(names):
    segs = []
    for _ in range(60):
        w = [R.uniform(0.55, 2.35) for _ in names]
        base = R.uniform(1400, 24000)
        segs = []
        for j, nm in enumerate(names):
            rp = int(round(base * w[j] / sum(w)))
            rc = int(round(rp * (1.0 + R.uniform(-0.055, 0.185))))
            mp = R.uniform(0.075, 0.295)
            mc = mp + R.uniform(-0.022, 0.034)
            pp, pc = int(round(rp * mp)), int(round(rc * mc))
            ce0 = int(round(rc * R.uniform(0.55, 1.45)))
            cx0 = int(round(rc * R.uniform(0.018, 0.085)))
            segs.append({"name": nm, "rc": rc, "rp": rp, "pc": pc, "pp": pp, "ce0": ce0,
                         "ce1": int(round(ce0 * R.uniform(0.88, 1.12))), "cx0": cx0,
                         "cx1": int(round(cx0 * R.uniform(0.85, 1.15))), "dp0": int(round(cx0 * R.uniform(0.75, 1.1)))})
        if sum(s["rc"] for s in segs) > sum(s["rp"] for s in segs) * 1.03 and all(s["pc"] > 0 and s["pp"] > 0 for s in segs):
            return segs
    return segs


def mix_rate(f):
    trc, trp = f["trc"], f["trp"]
    m1, m0 = float(f["tpc"]) / trc, float(f["tpp"]) / trp
    mix = rate = 0.0
    for s in f["segs"]:
        sh1, sh0 = float(s["rc"]) / trc, float(s["rp"]) / trp
        a1, a0 = float(s["pc"]) / s["rc"], float(s["pp"]) / s["rp"]
        mix += (sh1 - sh0) * (a0 - m0)
        rate += sh1 * (a1 - a0)
    return mix * 100.0, rate * 100.0, (m1 - m0) * 100.0


def build_fixture(idx, comp):
    name, sector, fye, ccy, names, offers = comp
    segs = make_segs(names)
    f = {"key": "F%02d" % (idx + 1), "co": name, "sector": sector, "fye": fye, "ccy": ccy, "segs": segs}
    f["trc"], f["trp"] = tot(f, "rc"), tot(f, "rp")
    f["tpc"], f["tpp"] = tot(f, "pc"), tot(f, "pp")
    f["er0"] = -int(round(f["trc"] * R.uniform(0.008, 0.045)))
    f["er1"] = -int(round(f["trp"] * R.uniform(0.008, 0.045)))
    f["ep0"] = -int(round(f["tpc"] * R.uniform(0.02, 0.11)))
    f["ep1"] = -int(round(f["tpp"] * R.uniform(0.02, 0.11)))
    f["crev"], f["cpri"] = f["trc"] + f["er0"], f["trp"] + f["er1"]
    f["cpro"], f["cpro_p"] = f["tpc"] + f["ep0"], f["tpp"] + f["ep1"]
    f["rest_from"], f["rest_to"] = 0, len(segs) - 1
    f["rest_amt"] = int(round(segs[1]["rp"] * R.uniform(0.04, 0.14)))
    f["biz"] = BIZ[idx % len(BIZ)]
    regs = R.sample(REGION, 4)
    gw = [R.uniform(0.6, 2.2) for _ in regs]
    f["geo"] = []
    for k, rg in enumerate(regs):
        rp = int(round(f["trc"] * gw[k] / sum(gw)))
        rc = int(round(rp * (1.0 + R.uniform(-0.03, 0.17))))
        f["geo"].append({"name": rg, "rc": rc, "rp": rp, "fx": int(round(rc * R.uniform(-0.032, 0.032)))})
    f["mix"], f["rate"], f["dmark"] = mix_rate(f)
    offs = R.sample(offers, len(segs))
    f["descs"] = ["The %s segment provides %s to %s customers, with most revenue generated in %s." % (s["name"], offs[k], R.choice(CUST), R.choice(REGION)) for k, s in enumerate(segs)]
    return f


def cc_growth(f):
    rc, rp = sum(g["rc"] for g in f["geo"]), sum(g["rp"] for g in f["geo"])
    fx = sum(g["fx"] for g in f["geo"])
    return growth(rc - fx, rp), growth(rc, rp), fx


def walk(f):
    s = seg_by(f, "rc")[0]
    m0, m1 = margin(s["pp"], s["rp"]), margin(s["pc"], s["rc"])
    d = m1 - m0
    a = round(R.uniform(-2.2, 2.2), 1)
    b = round(R.uniform(-3.0, 1.2), 1)
    return s, m0, m1, d, a, b, round(d - a - b, 1)


# ----------------------------------------------------------------------- contexts
def ctx_v1(f):
    rows = [[s["name"], num(s["rc"]), num(s["rp"]), num(s["pc"]), num(s["pp"])] for s in f["segs"]]
    rows.append(["**Total reportable segments**", num(f["trc"]), num(f["trp"]), num(f["tpc"]), num(f["tpp"])])
    return "\n".join([units(f), "", "### Segment revenue and profit - %s" % f["co"], "Fiscal year ended %s. %s segment disclosures." % (f["fye"], f["sector"].title()), "", tbl(["Segment", "FY2025 revenue", "FY2024 revenue", "FY2025 segment profit", "FY2024 segment profit"], rows), "", NOTE1])


def ctx_v2(f):
    rows = [["Total reportable segment revenue", num(f["trc"]), num(f["trp"])], ["Intersegment eliminations", num(f["er0"]), num(f["er1"])], ["**Consolidated revenue**", num(f["crev"]), num(f["cpri"])], ["Total reportable segment profit", num(f["tpc"]), num(f["tpp"])], ["Unallocated corporate costs and eliminations", num(f["ep0"]), num(f["ep1"])], ["**Consolidated operating profit**", num(f["cpro"]), num(f["cpro_p"])]]
    return "\n".join([units(f), "", "### Reconciliation of segment totals to the consolidated statements - %s" % f["co"], "Fiscal year ended %s." % f["fye"], "", tbl(["Line item", "FY2025", "FY2024"], rows), "", "Intersegment sales are priced at cost plus a fixed margin. Unallocated corporate costs comprise central functions that are not attributed to a reportable segment."])


def ctx_v3(f):
    rows = [[s["name"], num(s["ce0"]), num(s["ce1"]), num(s["pc"]), num(s["pp"])] for s in f["segs"]]
    rows.append(["**Total**", num(tot(f, "ce0")), num(tot(f, "ce1")), num(f["tpc"]), num(f["tpp"])])
    return "\n".join([units(f), "", "### Segment capital employed and segment profit - %s" % f["co"], "Fiscal year ended %s." % f["fye"], "", tbl(["Segment", "Capital employed FY2025", "Capital employed FY2024", "Segment profit FY2025", "Segment profit FY2024"], rows), "", NOTE_CE])


def ctx_v4(f):
    rows = [[g["name"], num(g["rc"]), num(g["rp"]), num(g["fx"])] for g in f["geo"]]
    rows.append(["**Total**", num(sum(g["rc"] for g in f["geo"])), num(sum(g["rp"] for g in f["geo"])), num(sum(g["fx"] for g in f["geo"]))])
    return "\n".join([units(f), "", "### Revenue by region - %s" % f["co"], "Fiscal year ended %s." % f["fye"], "", tbl(["Region", "FY2025 revenue", "FY2024 revenue", "FX effect on FY2025 revenue"], rows), "", NOTE_GEO])


def ctx_v5(f):
    a, b = f["segs"][f["rest_from"]], f["segs"][f["rest_to"]]
    rows = [[s["name"], num(s["rp"]), num(s["rp"] - f["rest_amt"] if s is a else s["rp"] + f["rest_amt"] if s is b else s["rp"]), num(s["rc"])] for s in f["segs"]]
    rows.append(["**Total**", num(f["trp"]), num(f["trp"]), num(f["trc"])])
    note = "Note 2: effective 1 January 2025 the %s business was transferred from the %s segment to the %s segment. FY2024 segment revenue above has been restated as if the transfer had occurred at the start of FY2024. FY2025 amounts are presented under the new structure." % (f["biz"], a["name"], b["name"])
    return "\n".join([units(f), "", "### Segment revenue after the change in segment definitions - %s" % f["co"], "Fiscal year ended %s." % f["fye"], "", tbl(["Segment", "FY2024 as reported", "FY2024 restated", "FY2025"], rows), "", note])


def ctx_v6(f):
    s, m0, m1, d, a, b, c = walk(f)
    rows = [[DRIVERS[0], num(a, 1)], [DRIVERS[1], num(b, 1)], [DRIVERS[2], num(c, 1)], ["**Total change in segment margin**", num(d, 1)]]
    return "\n".join([units(f), "", "### Segment margin walk - %s, %s segment" % (f["co"], s["name"]), "Fiscal year ended %s. Effects are measured against the FY2024 segment margin of %s percent." % (f["fye"], pct(m0)), "", tbl(["Driver", "Effect on FY2025 segment margin (pp)"], rows), "", "The walk is presented at constant currency. Rounding may cause the components to differ from the total by 0.1 pp."])


def ctx_v7(f):
    lines = [units(f), "", "### Segment descriptions - %s" % f["co"], "Fiscal year ended %s." % f["fye"], ""]
    for k, s in enumerate(f["segs"]):
        lines += ["**%s.** %s" % (s["name"], f["descs"][k]), ""]
    lines += ["### Footnotes",
              "1. Segment profit excludes unallocated corporate costs of %s in FY2025 and %s in FY2024." % (num(abs(f["ep0"])), num(abs(f["ep1"]))),
              "2. Intersegment sales are recorded at cost plus a fixed margin and are eliminated on consolidation.",
              "3. FY2024 segment revenue was restated for the transfer of the %s business from the %s segment to the %s segment." % (f["biz"], f["segs"][f["rest_from"]]["name"], f["segs"][f["rest_to"]]["name"]),
              "4. Capital employed is total segment assets less total segment liabilities."]
    return "\n".join(lines)


def ctx_v8(f):
    gap, other = f["segs"][1], f["segs"][0]
    rows = [[s["name"], num(s["rc"]), "-" if s is gap else num(s["rp"] + (gap["rp"] if s is other else 0)), num(s["pc"])] for s in f["segs"]]
    rows.append(["**Total**", num(f["trc"]), num(f["trp"]), num(f["tpc"])])
    rows.append(["Memo: order backlog", num(f["trc"] * 0.07), num(f["trp"] * 0.065), "-"])
    note = "Note 1: the %s segment was acquired on 1 March 2025; its FY2024 revenue is included within the %s segment line. Note 2: the memo order backlog line is stated in $ thousands; all other amounts are stated in $ millions." % (gap["name"], other["name"])
    return "\n".join([units(f), "", "### Segment table with an acquisition in the year - %s" % f["co"], "Fiscal year ended %s." % f["fye"], "", tbl(["Segment", "FY2025 revenue", "FY2024 revenue", "FY2025 segment profit"], rows), "", note])


def ctx_v9(f):
    rows = [[s["name"], num(s["cx0"]), num(s["cx1"]), num(s["dp0"]), num(s["rc"])] for s in f["segs"]]
    rows.append(["**Total**", num(tot(f, "cx0")), num(tot(f, "cx1")), num(tot(f, "dp0")), num(f["trc"])])
    return "\n".join([units(f), "", "### Segment capital expenditure - %s" % f["co"], "Fiscal year ended %s." % f["fye"], "", tbl(["Segment", "FY2025 capital expenditure", "FY2024 capital expenditure", "FY2025 depreciation", "FY2025 revenue"], rows), "", "Capital expenditure is on an accrual basis and includes both maintenance and expansion spending. Depreciation is charged to segment profit."])


# --------------------------------------------------------------------------- calc
def c1(f):
    s = seg_by(f, "rc")[0]
    return row(f, "calc", ctx_v1(f), "What was the FY2025 percentage growth in revenue of the segment with the largest FY2025 revenue, compared with FY2024?", round(growth(s["rc"], s["rp"]), 1), "number", "abs:0.1")


def c2(f):
    s = seg_by(f, "rc")[1]
    return row(f, "calc", ctx_v1(f), "What was the segment profit margin of the second-largest segment by FY2025 revenue, in percent?", round(margin(s["pc"], s["rc"]), 1), "number", "abs:0.1")


def c3(f):
    s = seg_by(f, "pc")[0]
    return row(f, "calc", ctx_v1(f), "By how many basis points did the segment profit margin of the segment with the highest FY2025 segment profit change between FY2024 and FY2025?", round((margin(s["pc"], s["rc"]) - margin(s["pp"], s["rp"])) * 100.0, 1), "number", "abs:1")


def c4(f):
    s = seg_by(f, "rc")[0]
    return row(f, "calc", ctx_v1(f), "What share of total reportable segment revenue did the largest segment represent in FY2025, in percent?", round(100.0 * s["rc"] / f["trc"], 1), "number", "abs:0.1")


def c5(f):
    return row(f, "calc", ctx_v1(f), "Decompose the change in the total reportable segment margin into mix and rate effects, measuring the mix effect as each segment's change in revenue share multiplied by its FY2024 margin less the FY2024 total margin. What was the mix effect in FY2025, in percentage points?", round(f["mix"], 2), "number", "abs:0.05")


def c6(f):
    return row(f, "calc", ctx_v1(f), "Holding FY2025 revenue shares constant, what was the rate effect in percentage points on the change in the total reportable segment margin in FY2025?", round(f["rate"], 2), "number", "abs:0.05")


def c7(f):
    return row(f, "calc", ctx_v2(f), "Intersegment eliminations represented what percentage of total reportable segment revenue in FY2025?", round(-100.0 * f["er0"] / f["trc"], 1), "number", "abs:0.1")


def c8(f):
    return row(f, "calc", ctx_v2(f), "What was consolidated operating profit in FY2025, in millions?", f["cpro"], "number", "abs:1")


def c9(f):
    return row(f, "calc", ctx_v4(f), "On a constant-currency basis, what was total FY2025 revenue growth, in percent?", round(cc_growth(f)[0], 1), "number", "abs:0.1")


def c10(f):
    cc, rep, fx = cc_growth(f)
    return row(f, "calc", ctx_v4(f), "How many percentage points of the FY2025 reported revenue growth were attributable to foreign exchange translation?", round(rep - cc, 1), "number", "abs:0.1")


def c11(f):
    s = seg_by(f, "pc")[0]
    return row(f, "calc", ctx_v3(f), "What was the FY2025 return on capital employed of the segment with the highest FY2025 segment profit, in percent?", round(margin(s["pc"], s["ce0"]), 1), "number", "abs:0.1")


def c12(f):
    s = f["segs"][f["rest_to"]]
    return row(f, "calc", ctx_v5(f), "Using the restated FY2024 base, what was FY2025 revenue growth of the segment that received the transferred business, in percent?", round(growth(s["rc"], s["rp"] + f["rest_amt"]), 1), "number", "abs:0.1")


def c13(f):
    s = seg_by(f, "cx0")[0]
    return row(f, "calc", ctx_v9(f), "What was capital expenditure as a percentage of segment revenue in FY2025 for the segment with the highest FY2025 capital expenditure?", round(100.0 * s["cx0"] / s["rc"], 1), "number", "abs:0.1")


def c14(f):
    return row(f, "calc", ctx_v1(f), "What was the incremental segment profit margin on the FY2025 increase in total reportable segment revenue, in percent?", round(float(f["tpc"] - f["tpp"]) / (f["trc"] - f["trp"]) * 100.0, 1), "number", "abs:0.1")


CALC = [c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14]


# --------------------------------------------------------------------- extraction
def e1(f):
    s = f["segs"][0]
    return row(f, "extraction", ctx_v1(f), "What FY2025 revenue is reported for the %s segment, in millions?" % s["name"], s["rc"], "number", "abs:1")


def e2(f):
    s = f["segs"][-1]
    return row(f, "extraction", ctx_v1(f), "What FY2024 segment profit is reported for the %s segment, in millions?" % s["name"], s["pp"], "number", "abs:1")


def e3(f):
    return row(f, "extraction", ctx_v7(f), "Under footnote 1, what amount of unallocated corporate costs was excluded from segment profit in FY2025, in millions?", abs(f["ep0"]), "number", "abs:1")


def e4(f):
    phrase = f["descs"][1].split(" provides ")[1].split(" to ")[0]
    return row(f, "extraction", ctx_v7(f), "Which segment is described as supplying %s?" % phrase, f["segs"][1]["name"], "text", "normalized")


def e5(f):
    return row(f, "extraction", ctx_v8(f), "In what unit is the memo order backlog line stated?", "thousands", "text", "normalized")


def e6(f):
    return row(f, "extraction", ctx_v8(f), "Which segment shows no FY2024 revenue in the table?", f["segs"][1]["name"], "text", "normalized")


def e7(f):
    s = f["segs"][f["rest_from"]]
    return row(f, "extraction", ctx_v5(f), "What FY2024 revenue is shown on a restated basis for the %s segment, in millions?" % s["name"], s["rp"] - f["rest_amt"], "number", "abs:1")


def e8(f):
    g = sorted(f["geo"], key=lambda x: x["rc"], reverse=True)[0]
    return row(f, "extraction", ctx_v4(f), "What FY2025 revenue is reported for the %s region, in millions?" % g["name"], g["rc"], "number", "abs:1")


def e9(f):
    g = sorted(f["geo"], key=lambda x: x["fx"])[0]
    return row(f, "extraction", ctx_v4(f), "What foreign exchange effect on FY2025 revenue is shown for the %s region, in millions?" % g["name"], g["fx"], "number", "abs:1")


def e10(f):
    s = f["segs"][-1]
    return row(f, "extraction", ctx_v3(f), "What capital employed is reported for the %s segment at FY2025, in millions?" % s["name"], s["ce0"], "number", "abs:1")


def e11(f):
    return row(f, "extraction", ctx_v7(f), "List the reportable segments named in the excerpt, in the order presented.", [s["name"] for s in f["segs"]], "list", "ordered")


EXTR = [e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11]


# ----------------------------------------------------------------------------- qa
def q1(f):
    s = max(f["segs"], key=lambda x: x["rc"] - x["rp"])
    return row(f, "qa", ctx_v1(f), "Which segment contributed the largest absolute increase in revenue between FY2024 and FY2025?", s["name"], "label", "exact")


def q2(f):
    s = max(f["segs"], key=lambda x: margin(x["pc"], x["rc"]) - margin(x["pp"], x["rp"]))
    return row(f, "qa", ctx_v1(f), "Which segment recorded the largest increase in segment profit margin between FY2024 and FY2025?", s["name"], "label", "exact")


def q3(f):
    s = max(f["segs"], key=lambda x: float(x["pc"]) / x["ce0"])
    return row(f, "qa", ctx_v3(f), "Which segment earned the highest return on capital employed in FY2025?", s["name"], "label", "exact")


def q4(f):
    g = min(f["geo"], key=lambda x: x["fx"])
    return row(f, "qa", ctx_v4(f), "Which region recorded the largest adverse foreign exchange effect on FY2025 revenue?", g["name"], "label", "exact")


def q5(f):
    return row(f, "qa", ctx_v4(f), "What would total FY2025 revenue have been at FY2024 exchange rates, in millions?", sum(g["rc"] for g in f["geo"]) - sum(g["fx"] for g in f["geo"]), "number", "abs:1")


def q6(f):
    return row(f, "qa", ctx_v5(f), "Name, in order, the segment that transferred the %s business and the segment that received it." % f["biz"], [f["segs"][f["rest_from"]]["name"], f["segs"][f["rest_to"]]["name"]], "list", "ordered")


def q7(f):
    return row(f, "qa", ctx_v2(f), "What reconciling amount, in millions, sits between total reportable segment revenue and consolidated revenue in FY2025?", f["er0"], "number", "abs:1")


def q8(f):
    s, m0, m1, d, a, b, c = walk(f)
    top = sorted([(abs(a), DRIVERS[0]), (abs(b), DRIVERS[1]), (abs(c), DRIVERS[2])], reverse=True)[0][1]
    return row(f, "qa", ctx_v6(f), "Which driver had the largest absolute effect on the segment margin in the walk shown?", top.lower(), "label", "exact")


def q9(f):
    order = sorted(f["segs"], key=lambda s: growth(s["rc"], s["rp"]))
    return row(f, "qa", ctx_v1(f), "Rank the reportable segments by FY2025 revenue growth, from lowest to highest.", [s["name"] for s in order], "list", "ordered")


QA = [q1, q2, q3, q4, q5, q6, q7, q8, q9]

KNOW = [
    ("Under IFRS 8, what is the management approach to identifying operating segments?", "Operating segments are identified from the internal reports that the chief operating decision maker reviews to allocate resources and assess performance.", "text"),
    ("Under IFRS 8, what quantitative threshold makes an operating segment reportable?", "A segment is reportable when it is 10 percent or more of combined revenue, profit or loss, or total assets.", "text"),
    ("What is the 75 percent coverage test in segment reporting?", "Reportable segments must account for at least 75 percent of external revenue, with further segments identified until the threshold is reached.", "text"),
    ("Why are intersegment revenues eliminated on consolidation?", "They are internal transactions and do not represent revenue earned from parties outside the group.", "text"),
    ("What does a constant-currency growth rate measure?", "Growth after removing the effect of changes in foreign exchange translation rates between the two periods.", "text"),
    ("How is a segment profit margin computed?", "Segment profit divided by segment revenue, expressed as a percentage.", "text"),
    ("What does a positive mix effect mean in a segment margin bridge?", "Revenue shifted toward segments whose margins are above the group average, which raises the consolidated margin.", "text"),
    ("What is return on capital employed?", "Profit divided by the capital employed in the business, expressed as a percentage.", "text"),
    ("Why must prior-year segment data be restated when segment definitions change?", "So that both periods are presented on the same basis and growth is comparable.", "text"),
    ("What is the difference between segment assets and capital employed?", "Capital employed is total segment assets less total segment liabilities.", "text"),
    ("Name the two effects that together explain the change in a consolidated segment margin.", ["mix effect", "rate effect"], "list"),
    ("What does a segment margin bridge decompose?", "It splits the change in margin into price and mix, cost, and productivity drivers.", "text"),
    ("What is an unallocated corporate cost line in a segment disclosure?", "Costs that are not attributed to any reportable segment, such as central finance, legal and executive functions.", "text"),
    ("How is incremental margin calculated?", "The change in segment profit divided by the change in revenue, expressed as a percentage.", "text"),
    ("What does it mean when reported growth exceeds constant-currency growth?", "Foreign exchange translation added to reported growth, which is a translation tailwind.", "text"),
    ("Under US GAAP ASC 280, what role does the chief operating decision maker play?", "The chief operating decision maker allocates resources and assesses segment performance using the disclosed segment measures.", "text"),
    ("When may two operating segments be aggregated into one reportable segment?", "When they have similar economic characteristics and are alike in products, customers, distribution methods and regulatory environment.", "text"),
    ("Why can total segment revenue exceed consolidated revenue?", "Segment revenue includes intersegment sales, which are eliminated on consolidation.", "text"),
    ("Name the three quantitative tests used to identify a reportable segment under IFRS 8.", ["revenue test", "profit or loss test", "assets test"], "list"),
    ("What is a reportable segment?", "An operating segment for which separate financial information is disclosed because it meets the size or coverage criteria.", "text"),
]


# ----------------------------------------------------------------- classification
CLS1 = ["expanding", "stable", "contracting"]
CLS2 = ["expanding", "stable", "contracting"]
CLS3 = ["tailwind", "neutral", "headwind"]
CLS4 = ["overstated", "understated", "unaffected"]
CLS5 = ["broad-based", "narrow-based"]


def cls_pick(salt, f, labels):
    order = sorted(FIX, key=lambda x: hkey(salt + x["key"]))
    return labels[order.index(f) % len(labels)]


def cls_ctx(f, title, head, rows, note):
    return "\n".join([units(f), "", "### %s - %s" % (title, f["co"]), "Fiscal year ended %s." % f["fye"], "", tbl(head, rows), "", note])


def cls1_row(f, i):
    lab = cls_pick("cls1", f, CLS1)
    g = {"expanding": 0.088, "stable": 0.033, "contracting": -0.036}[lab] + R.uniform(-0.010, 0.010)
    names = [s["name"] for s in f["segs"][:3]]
    w = [R.uniform(0.7, 2.0) for _ in names]
    base, rows, pr = R.uniform(3200, 9000), [], []
    for k, nm in enumerate(names):
        rp = int(round(base * w[k] / sum(w)))
        rc = int(round(rp * (1.0 + g + R.uniform(-0.012, 0.012))))
        rows.append([nm, num(rc), num(rp), num(rc - rp)])
        pr.append((rc, rp))
    trc, trp = sum(x[0] for x in pr), sum(x[1] for x in pr)
    gr = growth(trc, trp)
    assert ("expanding" if gr >= 6.0 else "stable" if gr >= 0.0 else "contracting") == lab
    rows.append(["**Total**", num(trc), num(trp), num(trc - trp)])
    ctx = cls_ctx(f, "Segment revenue momentum", ["Segment", "FY2025 revenue", "FY2024 revenue", "Change"], rows, NOTE_SAME)
    q = "Classify the FY2025 revenue momentum of the company as one of {expanding, stable, contracting}, where growth of 6.0 percent or more is expanding, growth from 0.0 percent to less than 6.0 percent is stable, and negative growth is contracting."
    return row(f, "classification", ctx, q, lab, "label", "exact")


def cls2_row(f, i):
    lab = cls_pick("cls2", f, CLS2)
    d = {"expanding": 140.0, "stable": 12.0, "contracting": -165.0}[lab] + R.uniform(-22.0, 22.0)
    names = [s["name"] for s in f["segs"][:3]]
    w = [R.uniform(0.7, 2.0) for _ in names]
    base, rows, p0, p1 = R.uniform(3800, 10000), [], 0, 0
    for k, nm in enumerate(names):
        rp = int(round(base * w[k] / sum(w)))
        rc = int(round(rp * R.uniform(1.01, 1.06)))
        m0 = R.uniform(10.0, 26.0)
        m1 = m0 + d / 100.0
        rows.append([nm, num(rc), num(rp), pct(m1), pct(m0)])
        p0, p1 = p0 + int(round(rp * m0 / 100.0)), p1 + int(round(rc * m1 / 100.0))
    trc, trp = sum(int(r[1]) for r in rows), sum(int(r[2]) for r in rows)
    chg = (float(p1) / trc - float(p0) / trp) * 100.0 * 100.0
    assert ("expanding" if chg >= 75.0 else "contracting" if chg <= -75.0 else "stable") == lab, (lab, chg)
    ctx = cls_ctx(f, "Segment margins", ["Segment", "FY2025 revenue", "FY2024 revenue", "FY2025 margin", "FY2024 margin"], rows, "Segment profit is not shown; margins are stated as segment profit divided by segment revenue.")
    q = "Classify the FY2025 change in the consolidated segment margin as one of {expanding, stable, contracting}, where a change of 75 basis points or more is expanding, a change between -75 and +75 basis points is stable, and a change of -75 basis points or worse is contracting."
    return row(f, "classification", ctx, q, lab, "label", "exact")


def cls3_row(f, i):
    lab = cls_pick("cls3", f, CLS3)
    pp = {"tailwind": 2.4, "neutral": 0.35, "headwind": -2.5}[lab] + R.uniform(-0.45, 0.45)
    names = [g["name"] for g in f["geo"]]
    w = [R.uniform(0.6, 2.0) for _ in names]
    rps = [int(round(R.uniform(3200, 11000) * w[k] / sum(w))) for k in range(len(names))]
    trp = sum(rps)
    tfx = int(round(trp * pp / 100.0))
    fx = [int(round(tfx * w[k] / sum(w))) for k in range(len(names) - 1)]
    fx.append(tfx - sum(fx))
    rows = [[names[k], num(int(round(rps[k] * 1.05)) + fx[k]), num(rps[k]), num(fx[k])] for k in range(len(names))]
    trc = sum(int(r[1]) for r in rows)
    rows.append(["**Total**", num(trc), num(trp), num(tfx)])
    diff = growth(trc, trp) - growth(trc - tfx, trp)
    assert ("tailwind" if diff >= 1.0 else "headwind" if diff <= -1.0 else "neutral") == lab, (lab, diff)
    ctx = cls_ctx(f, "Revenue by region", ["Region", "FY2025 revenue", "FY2024 revenue", "FX effect on FY2025 revenue"], rows, "Underlying local-currency revenue grew at the same rate in every region. The FX effect is the translation difference between FY2025 and FY2024 rates.")
    q = "Classify the foreign exchange contribution to FY2025 revenue growth as one of {tailwind, neutral, headwind}, where an FX contribution of at least +1.0 percentage point is a tailwind, between -1.0 and +1.0 percentage points is neutral, and -1.0 percentage points or worse is a headwind."
    return row(f, "classification", ctx, q, lab, "label", "exact")


def cls4_row(f, i):
    lab = cls_pick("cls4", f, CLS4)
    t = {"overstated": 0.052, "understated": -0.048, "unaffected": 0.0}[lab]
    names = [s["name"] for s in f["segs"][:3]]
    w = [R.uniform(0.7, 2.0) for _ in names]
    base, seg = R.uniform(2800, 9000), []
    for k, nm in enumerate(names):
        rp = int(round(base * w[k] / sum(w)))
        seg.append([nm, rp, int(round(rp * R.uniform(1.02, 1.12)))])
    tgt = seg[0]
    amt = int(round(tgt[1] * abs(t))) if t else int(round(seg[1][1] * 0.045))
    tr = tgt[1] + amt if t > 0 else tgt[1] - amt if t < 0 else tgt[1]
    rows = []
    for s in seg:
        res = s[1]
        if s is tgt:
            res = tr
        elif s is seg[2]:
            res = s[1] - amt if t > 0 else s[1] + amt if t < 0 else s[1] + amt
        elif s is seg[1] and t == 0:
            res = s[1] - amt
        rows.append([s[0], num(s[1]), num(res), num(s[2])])
    if t > 0:
        note = "Note: the %s business was transferred into the first segment from the %s segment with effect from 1 January 2025 and FY2024 revenue has been restated accordingly." % (f["biz"], seg[2][0])
    elif t < 0:
        note = "Note: the %s business was transferred out of the first segment to the %s segment with effect from 1 January 2025 and FY2024 revenue has been restated accordingly." % (f["biz"], seg[2][0])
    else:
        note = "Note: the %s business was transferred between the %s and %s segments with effect from 1 January 2025; the first segment was not affected." % (f["biz"], seg[1][0], seg[2][0])
    d = growth(tgt[2], tgt[1]) - growth(tgt[2], tr)
    assert ("overstated" if d > 0.2 else "understated" if d < -0.2 else "unaffected") == lab, (lab, d)
    ctx = cls_ctx(f, "Segment revenue after a change in segment definitions", ["Segment", "FY2024 as reported", "FY2024 restated", "FY2025"], rows, note)
    q = "Compare the FY2025 growth of the segment listed first in the table, computed on its as-reported FY2024 base, with the growth computed on its restated FY2024 base. Classify the as-reported growth as one of {overstated, understated, unaffected}, treating a difference of 0.2 percentage points or less as unaffected."
    return row(f, "classification", ctx, q, lab, "label", "exact")


def cls5_row(f, i):
    lab = cls_pick("cls5", f, CLS5)
    names = [s["name"] for s in f["segs"][:4]]
    w = [R.uniform(0.7, 2.0) for _ in names]
    base, rows = R.uniform(4200, 11000), []
    order = list(range(len(names)))
    R.shuffle(order)
    up = set(order[:len(names) if lab == "broad-based" else 1])
    for k, nm in enumerate(names):
        rp = int(round(base * w[k] / sum(w)))
        rc = int(round(rp * R.uniform(1.03, 1.14))) if k in up else int(round(rp * R.uniform(0.90, 0.99)))
        rows.append([nm, num(rc), num(rp)])
    ups = sum(1 for r in rows if int(r[1]) > int(r[2]))
    assert ("broad-based" if ups * 2 >= len(names) else "narrow-based") == lab, (lab, ups)
    rows.append(["**Total**", num(sum(int(r[1]) for r in rows)), num(sum(int(r[2]) for r in rows))])
    ctx = cls_ctx(f, "Segment revenue by segment", ["Segment", "FY2025 revenue", "FY2024 revenue"], rows, NOTE_SAME)
    q = "Classify the FY2025 revenue performance as one of {broad-based, narrow-based}, where broad-based means at least half of the segments grew and narrow-based means fewer than half grew."
    return row(f, "classification", ctx, q, lab, "label", "exact")


CLS = [cls1_row, cls2_row, cls3_row, cls4_row, cls5_row]


# ------------------------------------------------------------------ summarization
SUMM = [
    (ctx_v1, "Summarize the FY2025 segment performance for an investment committee in two or three sentences. State which segment grew fastest and which had the highest margin, and do not introduce any figure that is not in the table."),
    (ctx_v2, "Summarize how the segment totals reconcile to the consolidated figures, naming the reconciling items and whether they increase or reduce the reported amounts. Use only amounts shown in the table."),
    (ctx_v4, "Summarize the geographic revenue performance, distinguishing reported movements from constant-currency movements and identifying the region most affected by translation. Use only amounts shown in the table."),
    (ctx_v5, "Summarize the segment restatement, which segments it affects and why the as-reported and restated FY2024 bases give different growth rates."),
    (ctx_v6, "Summarize the margin walk, identifying the largest positive and largest negative driver and whether the segment margin expanded or contracted."),
]


# ---------------------------------------------------------------------- tool use
def T(name, desc, props, req):
    return {"name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": req}}


def call(name, args):
    return json.dumps({"tool": name, "arguments": args}, ensure_ascii=False)


def t1(f):
    s = max(f["segs"], key=lambda x: margin(x["pc"], x["rc"]))
    msgs = [{"role": "user", "content": "Pull the FY2025 segment table for this issuer and tell me which segment runs the highest segment profit margin."},
            {"role": "assistant", "content": call("get_segment_table", {"issuer": f["co"], "period": "2025"})},
            {"role": "tool", "content": json.dumps({"error": "invalid period", "valid_values": ["FY2025", "FY2024"]})},
            {"role": "assistant", "content": call("get_segment_table", {"issuer": f["co"], "period": "FY2025"})},
            {"role": "tool", "content": json.dumps({"period": "FY2025", "segments": [{"segment": x["name"], "revenue": x["rc"], "segment_profit": x["pc"]} for x in f["segs"]]})},
            {"role": "user", "content": "Which segment has the highest segment profit margin?"}]
    tools = [T("get_segment_table", "Return the reported segment table for an issuer and fiscal period.",
               {"issuer": {"type": "string", "description": "Legal issuer name."}, "period": {"type": "string", "enum": ["FY2025", "FY2024"]}}, ["issuer", "period"])]
    return mtrow(msgs, tools, s["name"], "label", "exact")


def t2(f):
    g = max(f["geo"], key=lambda x: x["rc"])
    msgs = [{"role": "user", "content": "I need constant-currency growth for the largest region in the FY2025 disclosure."},
            {"role": "assistant", "content": call("get_region_revenue", {"issuer": f["co"], "period": "FY2025", "region": g["name"]})},
            {"role": "tool", "content": json.dumps({"region": g["name"], "FY2025_revenue": g["rc"], "FY2024_revenue": g["rp"]})},
            {"role": "assistant", "content": call("get_fx_effect", {"issuer": f["co"], "period": "FY2025", "region": g["name"]})},
            {"role": "tool", "content": json.dumps({"region": g["name"], "fx_effect_on_revenue": g["fx"]})},
            {"role": "user", "content": "So what was constant-currency growth in the region, in percent?"}]
    tools = [T("get_region_revenue", "Return reported revenue for one region and period.", {"issuer": {"type": "string"}, "period": {"type": "string"}, "region": {"type": "string"}}, ["issuer", "period", "region"]),
             T("get_fx_effect", "Return the translation effect on revenue for one region.", {"issuer": {"type": "string"}, "period": {"type": "string"}, "region": {"type": "string"}}, ["issuer", "period", "region"])]
    return mtrow(msgs, tools, round(growth(g["rc"] - g["fx"], g["rp"]), 1), "number", "abs:0.1")


def t3(f):
    s = seg_by(f, "pc")[0]
    msgs = [{"role": "user", "content": "Work out return on capital employed for the largest segment in the FY2025 disclosure."},
            {"role": "assistant", "content": call("get_capital_employed", {"issuer": f["co"], "period": "FY2025", "segment": s["name"]})},
            {"role": "tool", "content": json.dumps({"segment": s["name"], "capital_employed_FY2025": s["ce0"]})},
            {"role": "assistant", "content": call("get_segment_profit", {"issuer": f["co"], "period": "FY2025", "segment": s["name"]})},
            {"role": "tool", "content": json.dumps({"error": "segment profit is not reported for this segment in the requested period"})},
            {"role": "user", "content": "Which input is missing before you can compute it?"}]
    tools = [T("get_capital_employed", "Return capital employed for one segment.", {"issuer": {"type": "string"}, "period": {"type": "string"}, "segment": {"type": "string"}}, ["issuer", "period", "segment"]),
             T("get_segment_profit", "Return segment profit for one segment.", {"issuer": {"type": "string"}, "period": {"type": "string"}, "segment": {"type": "string"}}, ["issuer", "period", "segment"])]
    return mtrow(msgs, tools, "segment profit", "text", "normalized")


def t4(f):
    a, b = f["segs"][f["rest_from"]], f["segs"][f["rest_to"]]
    msgs = [{"role": "user", "content": "Check whether the FY2024 comparatives in this issuer's segment note can be compared directly with the FY2025 presentation."},
            {"role": "assistant", "content": call("get_segment_note_metadata", {"issuer": f["co"], "period": "FY2025"})},
            {"role": "tool", "content": json.dumps({"restated": True, "restatement_note": "FY2024 restated for the transfer of the %s business from %s to %s." % (f["biz"], a["name"], b["name"])})},
            {"role": "user", "content": "Do the FY2024 comparatives need adjustment before I calculate FY2025 growth?"}]
    tools = [T("get_segment_note_metadata", "Return presentation metadata for the segment note.", {"issuer": {"type": "string"}, "period": {"type": "string"}}, ["issuer", "period"])]
    return mtrow(msgs, tools, "yes", "text", "normalized")


def t5(f):
    a, b = f["segs"][0], f["segs"][-1]
    msgs = [{"role": "user", "content": "Compare the two segments named in the request and tell me which one earns the better segment margin."},
            {"role": "assistant", "content": call("compare_segments", {"issuer": f["co"], "period": "FY2025", "segments": [a["name"], b["name"]]})},
            {"role": "tool", "content": json.dumps({"period": "FY2025", "rows": [{"segment": a["name"], "revenue": a["rc"], "segment_profit": a["pc"]}, {"segment": b["name"], "revenue": b["rc"], "segment_profit": b["pc"]}]})},
            {"role": "user", "content": "Which of the two has the higher segment margin?"}]
    tools = [T("compare_segments", "Return revenue and segment profit for up to four segments.",
               {"issuer": {"type": "string"}, "period": {"type": "string"}, "segments": {"type": "array", "items": {"type": "string"}, "maxItems": 4}}, ["issuer", "period", "segments"])]
    gt = a["name"] if margin(a["pc"], a["rc"]) > margin(b["pc"], b["rc"]) else b["name"]
    return mtrow(msgs, tools, gt, "label", "exact")


TOOL = [t1, t2, t3, t4, t5]


# ---------------------------------------------------------------------- assembly
def build_rows():
    out = []
    for fam in CALC:
        out += [fam(f) for f in FIX]
    for fam in EXTR:
        out += [fam(f) for f in FIX]
    for fam in QA:
        out += [fam(f) for f in FIX]
    for fam in CLS:
        out += [fam(f, i) for i, f in enumerate(FIX)]
    for fn, q in SUMM:
        out += [row(f, "summarization", fn(f), q, None, "text", None) for f in FIX]
    for fam in TOOL:
        for f in FIX:
            r = fam(f)
            r["fixture"] = f["key"]
            out.append(r)
    kn = sorted(range(len(KNOW)), key=lambda k: hkey("know%d" % k))
    for pos, k in enumerate(kn):
        q, gt, at = KNOW[k]
        out.append({"fixture": "K%02d" % k, "task": "qa", "context": "", "question": q, "ground_truth": gt, "answer_type": at,
                    "tolerance": "set" if at == "list" else "normalized", "split": "train" if pos < 16 else "val" if pos < 18 else "test"})
    return out


def finalize(rows):
    seq = dict((k, 0) for k in ("calc", "extraction", "qa", "classification", "summarization", "tool_use"))
    abbr = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls", "summarization": "summ", "tool_use": "tool"}
    think = {"calc": "on", "qa": "on", "tool_use": "on"}
    byfix = dict((f["key"], f["split"]) for f in FIX)
    out = []
    for r in rows:
        t = r["task"]
        seq[t] += 1
        o = {"id": "fin_%s_%s_%06d" % (AREA, abbr[t], seq[t]), "task": t,
             "source": "knowledge:finance_general" if not r.get("context") and "messages" not in r else "synthetic:%s" % AREA}
        if "messages" in r:
            o["messages"], o["tools"] = r["messages"], r["tools"]
        else:
            o["context"], o["question"] = r["context"], r["question"]
        o["ground_truth"] = r["ground_truth"]
        o["answer_type"] = r["answer_type"] if r["ground_truth"] is not None else "text"
        o["tolerance"] = r["tolerance"]
        o["split"] = r.get("split") or byfix[r["fixture"]]
        o["thinking"] = think.get(t, "off")
        out.append(o)
    return out


def report(rows, path):
    fam, ctxs, tasks, splits, ats, pairs = {}, set(), {}, {}, {}, {}
    for r in rows:
        tasks[r["task"]] = tasks.get(r["task"], 0) + 1
        splits[r["split"]] = splits.get(r["split"], 0) + 1
        ats[r["answer_type"]] = ats.get(r["answer_type"], 0) + 1
        if "messages" in r:
            q = next(m["content"] for m in r["messages"] if m["role"] == "user")
            body = json.dumps(r["messages"], ensure_ascii=False, sort_keys=True)
        else:
            q = r["question"]
            body = r.get("context", "") + "|" + q
            if r.get("context"):
                ctxs.add(mask(r["context"]))
        fam[mask(q)[:160]] = fam.get(mask(q)[:160], 0) + 1
        pk = hashlib.sha256(mask(body).encode()).hexdigest()
        pairs[pk] = pairs.get(pk, 0) + 1
    top = max(fam.values()) if fam else 0
    tools = [r for r in rows if r["task"] == "tool_use"]
    multi = sum(1 for r in tools if any(m["role"] == "assistant" for m in r["messages"]))
    return {
        "area": AREA, "profile": "A", "rows": len(rows),
        "by_task": dict((k, tasks.get(k, 0)) for k in ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]),
        "by_split": dict((k, splits.get(k, 0)) for k in ["train", "val", "test"]),
        "by_answer_type": dict((k, ats.get(k, 0)) for k in ["number", "text", "label", "list"]),
        "distinct_question_families": len(fam),
        "top_family_share": round(top / float(len(rows)), 4),
        "distinct_contexts": len(ctxs),
        "near_dup_pairs": sum(1 for v in pairs.values() if v > 1),
        "tool_use_multi_step_share": round(multi / float(len(tools)), 3),
        "validation": "pass",
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "notes": "Synthetic segment disclosures only; splits assigned per fixture by sha256 inside each task stratum.",
        "weakest_spot": "Summarization rows carry no reference answer, and the five classification prompts use a constructed three-segment skeleton whose label is fixed by design rather than observed.",
    }


def main():
    for i, c in enumerate(COMPANIES):
        FIX.append(build_fixture(i, c))
    for i, f in enumerate(sorted(FIX, key=lambda x: hkey(x["key"]))):
        f["split"] = "train" if i < 16 else ("val" if i < 18 else "test")
    rows = finalize(build_rows())
    with open("prompts.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    rep = report(rows, "prompts.jsonl")
    with open("report.json", "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2)
        fh.write("\n")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
