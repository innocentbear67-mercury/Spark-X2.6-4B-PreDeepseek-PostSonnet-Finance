#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic generator for the accounting_policy area (1000 rows, profile B).
25 fictional issuers x 8 policy-note documents = 200 fixtures. Each fixture is used
by exactly one task and emits exactly 5 rows, so 200 * 5 = 1000 rows. Splits are
assigned per fixture (160 train / 20 val / 20 test fixtures), so no context ever
crosses a split boundary. Every ground_truth number is computed here from the same
values that are written into the context table, so re-running reproduces every answer.
"""
import hashlib
import json
import os
import random
import re
AREA = "accounting_policy"
SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "prompts.jsonl")
REPORT = os.path.join(HERE, "report.json")
COMPANIES = [ ("Halcyon Grid Utilities", "regulated electric utility", "31 December", "USD"), ("Meridian Bancorp", "regional bank", "31 December", "USD"), ("Kestrel Foods", "packaged foods", "30 June", "USD"), ("Northwind Precision Tools", "industrial tools", "31 December", "USD"), ("Cobalt Ridge Mining", "metals and mining", "31 December", "AUD"), ("Silverbrook Pharmaceuticals", "specialty pharmaceuticals", "31 December", "USD"), ("Lumen Harbor Logistics", "freight and logistics", "31 December", "EUR"), ("Verdant Grove Agriculture", "agribusiness", "30 September", "USD"), ("Atlas Foundry Group", "capital goods", "31 December", "EUR"), ("Bluepeak Semiconductor", "semiconductors", "31 December", "USD"), ("Orchard Lane Retail", "specialty retail", "31 January", "USD"), ("Tessellate Software", "application software", "31 December", "USD"), ("Harborlight Marine Services", "marine services", "31 December", "USD"), ("Juniper Peak Energy", "renewable power", "31 December", "EUR"), ("Baseline Diagnostics", "diagnostics", "30 June", "USD"), ("Stonebridge Insurance", "property insurance", "31 December", "USD"), ("Fairmont Textile Mills", "apparel manufacturing", "31 December", "USD"), ("Cascade Timber Partners", "forest products", "31 December", "CAD"), ("Nimbus Air Systems", "aerospace components", "31 December", "USD"), ("Quarry Ridge Cement", "building materials", "31 December", "EUR"), ("Sable Point Hotels", "hospitality", "31 December", "USD"), ("Twinline Media", "advertising media", "31 December", "USD"), ("Arclight Chemicals", "specialty chemicals", "31 December", "EUR"), ("Peregrine Health Labs", "life science tools", "31 December", "USD"), ("Ironwood Paper Group", "paper products", "31 December", "CAD"), ]
DOCS = ["nongaap", "revrec", "lease", "sbc", "impair", "tax", "estimate", "restate"]
TASK_SLICES = { "nongaap": [("calc", 9), ("extraction", 3), ("qa", 3), ("summarization", 4), ("tool_use", 6)], "revrec": [("calc", 5), ("extraction", 6), ("qa", 6), ("classification", 5), ("summarization", 3)], "lease": [("calc", 3), ("extraction", 6), ("qa", 6), ("classification", 7), ("summarization", 3)], "sbc": [("calc", 2), ("extraction", 4), ("qa", 4), ("summarization", 1), ("tool_use", 14)], "impair": [("calc", 2), ("extraction", 5), ("qa", 5), ("classification", 10), ("summarization", 3)], "tax": [("calc", 3), ("extraction", 6), ("qa", 6), ("classification", 8), ("summarization", 2)], "estimate": [("extraction", 7), ("qa", 8), ("classification", 8), ("summarization", 2)], "restate": [("extraction", 7), ("qa", 10), ("classification", 6), ("summarization", 2)], }
SPLIT_FIXTURES = {"calc": (18, 3, 3), "extraction": (34, 5, 5), "qa": (38, 5, 5), "classification": (34, 5, 5), "summarization": (18, 1, 1), "tool_use": (18, 1, 1)}
ROWS_PER_FIXTURE = 5
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls", "summarization": "summ", "tool_use": "tool"}
THINK = {"calc": "on", "extraction": "off", "qa": "on", "classification": "off", "summarization": "off", "tool_use": "on"}

def n1(x):
    return round(float(x) + 0.0, 1)

def n2(x):
    return round(float(x) + 0.0, 2)

def n0(x):
    return int(round(float(x)))

def d1(x):
    return "%.1f" % (float(x) + 0.0)

def d2(x):
    return "%.2f" % (float(x) + 0.0)

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def af(rate, term):
    f = 1.0
    for k in range(1, term):
        f += 1.0 / ((1 + rate / 100.0) ** k)
    return f

class Tab(object):
    def __init__(self, cols):
        self.cols, self.rows, self.cells = cols, [], []
    def add(self, label, *vals):
        assert len(vals) == len(self.cols)
        self.rows.append("| " + " | ".join([label] + [str(v) for v in vals]) + " |")
        for col, val in zip(self.cols, vals):
            if str(val) not in ("", "-", "n/a"):
                self.cells.append((label, col, str(val)))
    def text(self):
        return "\n".join(["| Item | " + " | ".join(self.cols) + " |", "|" + "---|" * (len(self.cols) + 1)] + self.rows)

def note(co, head, body, table, foot):
    return "\n\n".join(p for p in ["Units: %s in millions except per-share amounts in %s and percentages in percent." % (co[3], co[3]), head, body, table.text(), foot] if p)

def base(co, doc, j):
    return {"key": "%s:%s" % (doc, slug(co[0])), "doc": doc, "name": co[0], "sector": co[1], "fy_end": co[2], "cur": co[3], "fy": 2025, "variant": j % 3}

def head_of(co, topic):
    return "Policy note - %s, %s. Fiscal year ended %s %d." % (topic, co[0], co[2], 2025)

def b_nongaap(co, r, j):
    fx = base(co, "nongaap", j)
    rev = r.randrange(900, 2600, 10); rev0 = n0(rev * r.uniform(0.87, 0.97))
    oi = n0(rev * r.uniform(0.10, 0.21)); oi0 = n0(rev0 * (float(oi) / rev) * r.uniform(0.86, 1.16))
    sbc = n0(oi * r.uniform(0.09, 0.15)); sbc0 = n0(sbc * r.uniform(0.84, 0.98))
    am = n0(oi * r.uniform(0.06, 0.12)); am0 = n0(am * r.uniform(0.90, 1.05))
    rs = n0(oi * r.uniform(0.03, 0.09)); rs0 = n0(rs * r.uniform(0.35, 0.75))
    da = am + n0(oi * r.uniform(0.12, 0.22)); tx = n0((sbc + am + rs) * 0.24)
    ni = n0(oi * r.uniform(0.62, 0.76)); ni0 = n0(ni * r.uniform(0.86, 0.97))
    ds = round(r.uniform(38, 120), 1); ds0 = round(ds * r.uniform(0.97, 1.00), 1)
    adj = oi + sbc + am + rs; adj0 = oi0 + sbc0 + am0 + rs0; adj_ni = ni + sbc + am + rs - tx
    addb = sbc + am + rs; addb0 = sbc0 + am0 + rs0
    t = Tab(["FY2025", "FY2024"])
    t.add("Revenue", rev, rev0)
    t.add("GAAP operating income", oi, oi0)
    t.add("Depreciation and amortization", da, da - am + am0)
    t.add("Share-based compensation", sbc, sbc0)
    t.add("Acquisition-related amortization", am, am0)
    t.add("Restructuring charges", rs, rs0)
    t.add("Tax effect of adjustments", tx, n0(tx * 0.9))
    t.add("GAAP net income", ni, ni0)
    t.add("Diluted shares (millions)", d1(ds), d1(ds0))
    body = ("%s reports adjusted operating income and adjusted net income because management uses them to assess underlying " "performance. Adjusted operating income adds back share-based compensation, acquisition-related amortization and " "restructuring charges; adjusted net income also deducts their tax effect. These measures are not defined under US " "GAAP and may not be comparable with similarly titled measures of other issuers. Depreciation and amortization above " "includes the acquisition-related amortization." % co[0])
    fx["ctx"] = note(co, head_of(co, "non-GAAP measures"), body, t, "Footnote: no adjustments other than those listed were made in either year.")
    fx["cells"] = t.cells
    fx["v"] = dict(rev=rev, rev0=rev0, oi=oi, oi0=oi0, sbc=sbc, sbc0=sbc0, am=am, am0=am0, rs=rs, rs0=rs0, tx=tx, ni=ni, ni0=ni0, ds=ds, adj=adj, adj0=adj0, adj_ni=adj_ni, addb=addb, addb0=addb0, eps=ni / ds, adj_eps=adj_ni / ds, ebitda=oi + da + sbc + rs, da=da)
    return fx

def b_revrec(co, r, j):
    fx = base(co, "revrec", j)
    fixed = r.randrange(20, 70, 2); var = r.randrange(12, 46, 1)
    con = r.randrange(3, max(4, var - 4)); ssp_e = r.randrange(60, 140, 5)
    ssp_i = r.randrange(14, 40, 1); units = r.randrange(6, 30, 1); price = r.randrange(6, 22, 1)
    comm = round(r.uniform(9.0, 22.0), 1); prog = round(r.uniform(20, 75), 1)
    tp = fixed + var - con; aeq = n1(tp * float(ssp_e) / (ssp_e + ssp_i))
    ain = n1(tp - aeq); rec = n1(ain * prog / 100.0); gross = units * price
    t = Tab(["Amount"])
    t.add("Fixed consideration", fixed)
    t.add("Estimated variable consideration", var)
    t.add("Variable consideration constraint", con)
    t.add("SSP of equipment", ssp_e)
    t.add("SSP of installation", ssp_i)
    t.add("Units delivered in FY2025", units)
    t.add("List price per unit", price)
    t.add("Commission rate if agent (percent)", d1(comm))
    t.add("Installation progress at year end (percent)", d1(prog))
    tail = ["The entity controls the goods before transfer, sets the price and bears inventory risk.", "The customer is a distributor that sets the resale price and bears the inventory risk.", "Payment is deferred 36 months, so the arrangement contains a significant financing component."][j % 3]
    body = ("%s applies the five-step model to a supply arrangement. Transaction price is fixed consideration plus estimated " "variable consideration less the constrained amount, limited to what a significant revenue reversal is not " "probable of reversing. The price is allocated to the two performance obligations in proportion to standalone selling " "price. Equipment revenue is recognized when control transfers and installation revenue over time. %s" % (co[0], tail))
    fx["ctx"] = note(co, head_of(co, "revenue recognition"), body, t, "Footnote: amounts exclude sales tax; the constraint is reassessed at each reporting date.")
    fx["cells"] = t.cells
    fx["v"] = dict(fixed=fixed, var=var, con=con, tp=tp, ssp_e=ssp_e, ssp_i=ssp_i, aeq=aeq, ain=ain, rec=rec, units=units, price=price, comm=comm, prog=prog, gross=gross, net=n1(gross * comm / 100.0))
    fx["cls"] = {"pa": "agent" if j % 3 == 1 else "principal", "pres": "net" if j % 3 == 1 else "gross", "fin": "yes" if j % 3 == 2 else "no", "timing": "over_time", "con_half": "yes" if con > 0.5 * var else "no"}
    return fx

def b_lease(co, r, j):
    fx = base(co, "lease", j)
    pay = r.randrange(18, 60, 1); term = r.randrange(5, 10, 1); rate = round(r.uniform(4.0, 7.5), 1)
    idc = r.randrange(0, 6, 1); inc = r.randrange(0, 5, 1); st = r.randrange(2, 9, 1)
    liab = n1(pay * af(rate, term)); rou = n1(liab + idc - inc); amort = n1(rou / term)
    laf = n1(liab - pay); i1 = n1(laf * rate / 100.0); lend = n1(laf * (1 + rate / 100.0) - pay)
    i2 = n1(lend * rate / 100.0); cur = n1(pay - i2)
    t = Tab(["Amount"])
    t.add("Annual lease payment", pay)
    t.add("Non-cancellable term (years)", term)
    t.add("Incremental borrowing rate (percent)", d1(rate))
    t.add("Initial direct costs", idc)
    t.add("Lease incentives received", inc)
    t.add("Short-term lease cost", st)
    clause = ["The lease does not transfer ownership and contains no purchase option.", "The lease transfers ownership of the premises to the lessee at the end of the term.", "The lease contains a bargain purchase option the lessee is reasonably certain to exercise."][j % 3]
    body = ("%s leases warehouse space and equipment. The warehouse lease began on the first day of FY2025 with annual payments in " "advance. %s The lease liability is the present value of remaining payments at the incremental borrowing rate, the " "first payment being applied at commencement without interest. The right-of-use asset is that liability plus initial " "direct costs less lease incentives, amortized straight-line over the term. Leases of twelve months or less are " "expensed under the short-term exemption. The current portion of the liability is the principal component of the " "payment due within twelve months." % (co[0], clause))
    fx["ctx"] = note(co, head_of(co, "leases"), body, t, "Footnote: the implicit rate is not readily determinable.")
    fx["cells"] = t.cells
    fx["v"] = dict(pay=pay, term=term, rate=rate, liab=liab, rou=rou, amort=amort, i1=i1, lend=lend, cur=cur, ncur=n1(lend - cur), total=n1(amort + i1 + st), st=st, rou_end=n1(rou - amort))
    fx["cls"] = {"type": "operating_lease" if j % 3 == 0 else "finance_lease", "liab_gt_rou": "yes" if liab > rou else "no", "bpo": "yes" if j % 3 == 2 else "no", "pattern": "straight_line_single_cost" if j % 3 == 0 else "amortization_plus_interest", "cash": "operating" if j % 3 == 0 else "financing"}
    return fx

def b_sbc(co, r, j):
    fx = base(co, "sbc", j)
    sbc = r.randrange(24, 90, 1); sbc0 = n0(sbc * r.uniform(0.78, 0.95))
    rev = r.randrange(800, 2400, 10); opts = round(r.uniform(6.0, 20.0), 1)
    strike = round(r.uniform(11.0, 26.0), 2); avg = round(strike * r.uniform(1.25, 1.70), 2)
    rsus = round(r.uniform(1.5, 6.0), 1); basic = round(r.uniform(40.0, 110.0), 1)
    unrec = r.randrange(18, 70, 1); wap = round(r.uniform(1.8, 3.4), 1)
    proceeds = n1(opts * strike); buy = n1(proceeds / avg); incr = n1(opts - buy)
    dil = n1(basic + incr + rsus)
    t = Tab(["FY2025", "FY2024"])
    t.add("Share-based compensation expense", sbc, sbc0)
    t.add("Revenue", rev, n0(rev * 0.93))
    t.add("Options outstanding (millions)", d1(opts), d1(n1(opts * 0.94)))
    t.add("Weighted average exercise price (USD)", d2(strike), d2(n1(strike * 0.93)))
    t.add("Average market price (USD)", d2(avg), d2(n1(avg * 0.90)))
    t.add("Unvested restricted units (millions)", d1(rsus), d1(n1(rsus * 0.88)))
    t.add("Basic weighted average shares (millions)", d1(basic), d1(n1(basic * 0.99)))
    t.add("Unrecognized compensation cost", unrec, n0(unrec * 0.86))
    t.add("Weighted average recognition period (years)", d1(wap), d1(n1(wap * 0.95)))
    body = ("%s grants restricted stock units and stock options. Compensation cost is measured at grant-date fair value and " "recognized straight-line over the vesting period. Dilution uses the treasury stock method: assumed option proceeds " "repurchase shares at the average market price and unvested restricted stock units are added in full. Unrecognized " "cost is recognized over the weighted average remaining vesting period." % co[0])
    fx["ctx"] = note(co, head_of(co, "share-based compensation"), body, t, "Footnote: share counts are in millions; prices are volume-weighted for the year.")
    fx["cells"] = t.cells
    fx["v"] = dict(sbc=sbc, sbc0=sbc0, rev=rev, opts=opts, strike=strike, avg=avg, rsus=rsus, basic=basic, unrec=unrec, wap=wap, proceeds=proceeds, buy=buy, incr=incr, dil=dil, dil_pct=n1((incr + rsus) / basic * 100.0), sbc_pct=n1(sbc / rev * 100.0), growth=n1((sbc - sbc0) / sbc0 * 100.0), annual=n1(unrec / wap), per_share=n2(sbc / dil))
    return fx

def b_impair(co, r, j):
    fx = base(co, "impair", j)
    v = j % 3
    ppe = r.randrange(180, 620, 10); gw = 0 if v == 2 else r.randrange(45, 150, 5)
    carrying = ppe + gw
    if v == 1:
        und = n0(carrying * r.uniform(1.03, 1.15)); fv = n0(carrying * r.uniform(0.99, 1.10))
    elif v == 0:
        und = n0(carrying * r.uniform(0.86, 0.95)); fv = n0(carrying * r.uniform(0.82, 0.90))
    else:
        und = n0(carrying * r.uniform(0.70, 0.80)); fv = n0(carrying * r.uniform(0.55, 0.66))
    life = r.randrange(4, 12, 1); trigger = carrying > und
    loss = n1(carrying - fv) if trigger else 0.0; gw_loss = n1(min(gw, loss)); ppe_loss = n1(loss - gw_loss)
    t = Tab(["Amount"])
    t.add("Carrying amount of the cash-generating unit", carrying)
    t.add("Property, plant and equipment within the unit", ppe)
    t.add("Goodwill within the unit", gw)
    t.add("Undiscounted expected future cash flows", und)
    t.add("Fair value less costs of disposal", fv)
    t.add("Pre-tax discount rate (percent)", d1(round(r.uniform(7.0, 11.0), 1)))
    t.add("Remaining useful life (years)", life)
    body = ("%s tests the carrying amount of its asset group for impairment when events indicate the amount may not be " "recoverable. Recoverability compares the carrying amount with undiscounted expected future cash flows. If the " "carrying amount exceeds those cash flows, the loss is the excess over fair value less costs of disposal, allocated " "to goodwill first and then to property, plant and equipment. Depreciation after impairment is straight-line over " "the remaining useful life." % co[0])
    fx["ctx"] = note(co, head_of(co, "impairment of long-lived assets"), body, t, "Footnote: cash flow projections and fair value are management estimates, not observable prices.")
    fx["cells"] = t.cells
    fx["v"] = dict(carrying=carrying, ppe=ppe, gw=gw, und=und, fv=fv, life=life, loss=loss, gw_loss=gw_loss, ppe_loss=ppe_loss, post=n1(carrying - loss), dep=n1((ppe - ppe_loss) / life), head=n1(und - carrying))
    fx["cls"] = {"test": "required" if trigger else "not_required", "alloc": "goodwill" if (trigger and gw_loss > 0) else ("no_loss_recognized" if not trigger else "property_plant_and_equipment"), "exceeds_gw": "yes" if loss > gw else "no", "fv_below": "yes" if carrying > fv else "no", "gw_zero": "yes" if gw == 0 else "no"}
    return fx

def b_tax(co, r, j):
    fx = base(co, "tax", j)
    v = j % 3
    pre = r.randrange(140, 620, 5); cur = n0(pre * r.uniform(0.16, 0.24))
    defr = n0(pre * r.uniform(0.02, 0.06)); dtd = r.randrange(120, 320, 5)
    ttd = r.randrange(50, 160, 4); rate = round(r.uniform(21.0, 27.0), 1)
    dta = n1(dtd * rate / 100.0)
    va = 0.0 if v == 1 else n1(dta * (r.uniform(0.35, 0.55) if v == 0 else r.uniform(0.10, 0.22)))
    t = Tab(["FY2025"])
    t.add("Pretax income", pre)
    t.add("Current tax expense", cur)
    t.add("Deferred tax expense", defr)
    t.add("Deductible temporary difference", dtd)
    t.add("Taxable temporary difference", ttd)
    t.add("Enacted tax rate (percent)", d1(rate))
    t.add("Valuation allowance", d1(va))
    body = ("%s accounts for income taxes under the asset and liability method. Deferred tax assets and liabilities are measured " "by applying the enacted rate to deductible and taxable temporary differences and are classified as non-current. A " "valuation allowance is recorded when it is more likely than not that some portion of a deferred tax asset will not " "be realized, judged on the weight of available evidence including cumulative losses in the jurisdiction. Total income " "tax expense is current tax expense plus deferred tax expense." % co[0])
    fx["ctx"] = note(co, head_of(co, "income taxes"), body, t, "Footnote: the deferred tax expense is the net movement on deferred tax balances before amounts in other comprehensive income.")
    fx["cells"] = t.cells
    fx["v"] = dict(pre=pre, cur=cur, defr=defr, dtd=dtd, ttd=ttd, rate=rate, va=va, dta=dta, dtl=n1(ttd * rate / 100.0), net=n1(dta - ttd * rate / 100.0), total=cur + defr, etr=n1((cur + defr) / pre * 100.0), va_pct=n1(va / dta * 100.0), after=n1(dta - ttd * rate / 100.0 - va))
    fx["cls"] = {"va": "no_valuation_allowance" if v == 1 else "valuation_allowance_required", "evidence": "cumulative_losses" if v == 0 else ("positive_taxable_income" if v == 1 else "mixed_evidence"), "quarter": "yes" if va > 0.25 * dta else "no", "etr_above": "above" if (cur + defr) * 100.0 / pre > rate else "below", "class": "non_current"}
    return fx

def b_estimate(co, r, j):
    fx = base(co, "estimate", j)
    v = j % 3
    cost = r.randrange(380, 900, 10); elapsed = r.randrange(3, 7, 1); life = elapsed + r.randrange(3, 7, 1)
    resid = r.randrange(0, 40, 5)
    if v == 0:
        rem, nres, asset = max(2, life - elapsed - r.randrange(1, 3, 1)), resid, "moulding presses"
    elif v == 1:
        rem, nres, asset = life - elapsed + r.randrange(1, 3, 1), resid, "delivery vehicles"
    else:
        rem, nres, asset = life - elapsed, resid + r.randrange(10, 30, 5), "warehouse racking"
    accum = n0((cost - resid) * float(elapsed) / life); carrying = n1(cost - accum)
    dep_old = n1((carrying - resid) / (life - elapsed)); dep_new = n1((carrying - nres) / rem)
    t = Tab(["Amount"])
    t.add("Original cost at the beginning of FY2025", cost)
    t.add("Accumulated depreciation at the beginning of FY2025", accum)
    t.add("Original estimated useful life (years)", life)
    t.add("Elapsed life at the beginning of FY2025 (years)", elapsed)
    t.add("Revised remaining useful life (years)", rem)
    t.add("Original residual value", resid)
    t.add("Revised residual value", nres)
    body = ("During FY2025 %s completed its annual review of useful lives and residual values and changed the estimate for its %s with effect from " "the beginning of FY2025. The carrying amount, original and revised lives and residual values are " "set out below. Depreciation is straight-line over the remaining useful life. The change is a change in accounting " "estimate applied prospectively: prior periods are not restated and no cumulative catch-up is recognized. The effect " "is recognized in cost of sales." % (co[0], asset))
    fx["ctx"] = note(co, head_of(co, "change in accounting estimate"), body, t, "Footnote: assets fully depreciated at the date of the change are excluded from the review.")
    fx["cells"] = t.cells
    fx["v"] = dict(cost=cost, accum=accum, carrying=carrying, life=life, elapsed=elapsed, rem=rem, resid=resid, nres=nres, dep_old=dep_old, dep_new=dep_new, impact=n1(dep_new - dep_old), impact_pct=n1((dep_new - dep_old) / dep_old * 100.0), carrying_end=n1(carrying - dep_new))
    fx["cls"] = {"nature": "change_in_estimate", "direction": "increase" if dep_new > dep_old else "decrease", "apply": "prospectively", "shorter": "yes" if rem < (life - elapsed) else "no", "higher": "yes" if dep_new > dep_old else "no"}
    return fx

def b_restate(co, r, j):
    fx = base(co, "restate", j)
    kind = j % 3
    rev = r.randrange(700, 2100, 10); cos = n0(rev * r.uniform(0.55, 0.68))
    oi = rev - cos - n0(rev * r.uniform(0.10, 0.16)); re_open = n0(rev * r.uniform(0.35, 0.55))
    adj = -r.randrange(12, 46, 2); cadj = r.randrange(3, 14, 1)
    rev_chg = oi_chg = re_chg = cost_chg = 0
    t = Tab(["FY2024 as reported", "Adjustment", "FY2024 restated"])
    if kind == 0:
        rev_chg, oi_chg, re_chg, cost_chg = adj, adj - cadj, adj - cadj, cadj
        t.add("Revenue", rev, rev_chg, rev + rev_chg)
        t.add("Cost of sales", cos, cost_chg, cos + cost_chg)
        t.add("Operating income", oi, oi_chg, oi + oi_chg)
        t.add("Retained earnings, opening", re_open, re_chg, re_open + re_chg)
        body = ("%s identified that revenue on a multi-year supply contract had been recognized before the related performance " "obligation was satisfied. The error relates to FY2024, arose from a misinterpretation of the transfer-of-control " "criteria and is material. Revenue, cost of sales, operating income and opening retained earnings for FY2024 have " "been corrected in the comparatives presented with the FY2025 statements. Management concluded the misstatement " "was not intentional and has added review controls over contract revenue." % co[0])
        foot = "Footnote: the correction has no effect on cash flows and no effect on FY2025 opening inventory."
    elif kind == 1:
        shift = r.randrange(14, 40, 2); sga = n0(rev * 0.14); cost_chg = -shift
        t.add("Revenue", rev, 0, rev)
        t.add("Cost of sales", cos, cost_chg, cos + cost_chg)
        t.add("Selling, general and administrative expense", sga, shift, sga + shift)
        t.add("Operating income", oi, 0, oi)
        t.add("Retained earnings, opening", re_open, 0, re_open)
        body = ("%s changed the classification of outbound freight costs from cost of sales to selling, general and " "administrative expense to align presentation with the cost of fulfilling a contract. The change is a change in " "accounting policy applied retrospectively: prior period comparatives have been reclassified and there is no " "effect on revenue, operating income, net income, retained earnings or cash flows." % co[0])
        foot = "Footnote: the reclassification does not change any subtotal below operating income."
    else:
        reb = n0(rev * r.uniform(0.03, 0.06))
        t.add("Revenue", rev, 0, rev)
        t.add("Rebate accrual", reb, 0, reb)
        t.add("Operating income", oi, 0, oi)
        t.add("Retained earnings, opening", re_open, 0, re_open)
        body = ("%s revised the estimated volume rebate rate applied to a distributor agreement during FY2025 after new " "information about expected annual volumes became available. The revised rate applies prospectively from the " "start of the current period. Because the change affects only the current and future periods, no cumulative " "catch-up is recorded and the FY2024 comparatives below are presented unchanged, as the nil adjustment column " "shows." % co[0])
        foot = "Footnote: rebate accruals are settled with customers within 60 days of the year end."
    fx["ctx"] = note(co, head_of(co, "prior period correction and comparatives"), body, t, foot)
    fx["cells"] = t.cells
    fx["v"] = dict(rev=rev, oi=oi, re_open=re_open, kind=kind, rev_chg=rev_chg, oi_chg=oi_chg, re_chg=re_chg, cost_chg=cost_chg)
    fx["cls"] = {"nature": ["error_correction", "change_in_policy", "change_in_estimate"][kind], "comp": "not_restated" if kind == 2 else "restated", "retained": "decrease" if kind == 0 else "no_effect", "method": ["retrospective_restatement", "retrospective_reclassification", "prospective_application"][kind], "error": "yes" if kind == 0 else "no"}
    return fx
BUILDERS = {"nongaap": b_nongaap, "revrec": b_revrec, "lease": b_lease, "sbc": b_sbc, "impair": b_impair, "tax": b_tax, "estimate": b_estimate, "restate": b_restate}
# --------------------------------------------------------------------------- #
# row specs
# --------------------------------------------------------------------------- #

def N(q, v, tol="abs:0.1"):
    return {"q": q, "gt": n1(v), "at": "number", "tol": tol}

def N2(q, v):
    return {"q": q, "gt": n2(v), "at": "number", "tol": "abs:0.01"}

def T(q, s):
    return {"q": q, "gt": s, "at": "text", "tol": "normalized"}

def L(q, s):
    return {"q": q, "gt": s, "at": "label", "tol": "exact"}

def S(q, ref):
    return {"q": q, "gt": ref, "at": "text", "tol": "normalized" if ref else None}
EX25 = ["Quote the exact FY2025 amount disclosed for '%s'.", "Extract the FY2025 figure for '%s' exactly as it appears in the table.", "Copy the FY2025 amount shown against '%s' without rounding it.", "State verbatim the FY2025 value the note reports for '%s'.", "What FY2025 amount is disclosed for '%s'? Quote it exactly."]
EX24 = ["Quote the exact FY2024 amount disclosed for '%s'.", "Extract the FY2024 figure for '%s' exactly as it appears in the table.", "Copy the FY2024 amount shown against '%s' without rounding it.", "State verbatim the FY2024 value the note reports for '%s'.", "What FY2024 amount is disclosed for '%s'? Quote it exactly."]
EXG = ["Quote the exact amount shown for '%s' in the column headed '%s'.", "Extract the figure for '%s' under '%s' exactly as presented.", "Copy the amount shown against '%s' in the '%s' column without rounding it.", "State verbatim the value reported for '%s' under '%s'.", "What amount is disclosed for '%s' in the '%s' column? Quote it exactly."]

def _ex(f, i):
    label, col, val = f["cells"][i % len(f["cells"])]
    if col == "FY2025":
        q = EX25[i % 5] % label
    elif col == "FY2024":
        q = EX24[i % 5] % label
    else:
        q = EXG[i % 5] % (label, col)
    return T(q, val)

def ex_specs(idxs):
    return [(lambda f, i=i: _ex(f, i)) for i in idxs]

def cls_specs(pairs):
    return [(lambda f, q=q, d=d: L(q, f["cls"][d])) for q, d in pairs]
NG_C = [ lambda f: N("What was FY2025 adjusted operating income, in millions?", f["v"]["adj"]), lambda f: N("What was the FY2025 adjusted operating margin, in percent?", f["v"]["adj"] / f["v"]["rev"] * 100), lambda f: N("What percentage of FY2025 GAAP operating income did the excluded items represent, in percent?", f["v"]["addb"] / f["v"]["oi"] * 100), lambda f: N("By what percentage did adjusted operating income change from FY2024 to FY2025?", (f["v"]["adj"] - f["v"]["adj0"]) / f["v"]["adj0"] * 100), lambda f: N("What was FY2025 adjusted net income, in millions?", f["v"]["adj_ni"]), lambda f: N2("What was FY2025 adjusted diluted EPS, in dollars?", f["v"]["adj_eps"]), lambda f: N2("What was FY2025 GAAP diluted EPS, in dollars?", f["v"]["eps"]), lambda f: N("By what percentage did adjusted diluted EPS exceed GAAP diluted EPS in FY2025?", (f["v"]["adj_eps"] - f["v"]["eps"]) / f["v"]["eps"] * 100), lambda f: N("How much did total add-backs increase from FY2024 to FY2025, in millions?", f["v"]["addb"] - f["v"]["addb0"]), lambda f: N("What was the change in adjusted operating margin from FY2024 to FY2025, in percentage points?", (f["v"]["adj"] / f["v"]["rev"] - f["v"]["adj0"] / f["v"]["rev0"]) * 100), lambda f: N("What percentage of total FY2025 add-backs related to restructuring charges, in percent?", f["v"]["rs"] / f["v"]["addb"] * 100), lambda f: N("What was FY2025 GAAP operating margin, in percent?", f["v"]["oi"] / f["v"]["rev"] * 100), ]
NG_Q = [ lambda f: N("If restructuring charges had been zero in both years, what would the change in GAAP operating income have been, in millions?", (f["v"]["oi"] + f["v"]["rs"]) - (f["v"]["oi0"] + f["v"]["rs0"])), lambda f: N("What would FY2025 GAAP operating income be if share-based compensation were 10 percent higher, in millions?", f["v"]["oi"] - f["v"]["sbc"] * 0.10), lambda f: N("What is the tax effect as a percentage of the total pre-tax add-backs, in percent?", f["v"]["tx"] / f["v"]["addb"] * 100), lambda f: N("What is adjusted net income as a percentage of revenue, in percent?", f["v"]["adj_ni"] / f["v"]["rev"] * 100), lambda f: N("If adjusted operating income grows at the FY2025 rate again in FY2026, what would it be, in millions?", f["v"]["adj"] * (1 + (f["v"]["adj"] - f["v"]["adj0"]) / f["v"]["adj0"]), "abs:1"), lambda f: N("What is FY2025 operating margin after adding back only restructuring charges, in percent?", (f["v"]["oi"] + f["v"]["rs"]) / f["v"]["rev"] * 100), ]
NG_S = [ ("Summarize in two sentences what the reconciliation adjusts for and why management presents it.", None), ("Summarize the note's caveat about the use of the adjusted measures.", None), ("Summarize in one sentence how FY2025 revenue and GAAP operating income compare with FY2024.", "rev"), ("Summarize what the note discloses about the tax effect of the adjustments.", None), ("Summarize how the note defines adjusted operating income.", "def"), ]
RR_C = [ lambda f: N("What is the transaction price under the five-step model, in millions?", f["v"]["tp"]), lambda f: N("How much of the transaction price is allocated to the equipment obligation, in millions?", f["v"]["aeq"]), lambda f: N("How much of the transaction price is allocated to the installation obligation, in millions?", f["v"]["ain"]), lambda f: N("How much installation revenue is recognized in FY2025, in millions?", f["v"]["rec"]), lambda f: N("If the entity were an agent earning the stated commission, what revenue would it recognize on equipment sales, in millions?", f["v"]["net"]), lambda f: N("What is gross revenue from equipment sales at the list price, in millions?", f["v"]["gross"]), lambda f: N("What percentage of the transaction price is represented by variable consideration, in percent?", (f["v"]["var"] - f["v"]["con"]) / f["v"]["tp"] * 100), lambda f: N("What is the remaining performance obligation at year end, in millions?", f["v"]["tp"] - f["v"]["aeq"] - f["v"]["rec"]), lambda f: N("What is allocated equipment revenue per unit delivered, in millions?", f["v"]["aeq"] / f["v"]["units"], "abs:0.01"), lambda f: N("What percentage of the estimated variable consideration was constrained, in percent?", f["v"]["con"] / f["v"]["var"] * 100), ]
RR_Q = [ lambda f: N("If the constraint were removed entirely, what would the transaction price be, in millions?", f["v"]["tp"] + f["v"]["con"]), lambda f: N("If the installation were complete at year end, how much additional installation revenue would be recognized, in millions?", f["v"]["ain"] - f["v"]["rec"]), lambda f: N("What percentage of the transaction price is allocated to the installation obligation, in percent?", f["v"]["ain"] / f["v"]["tp"] * 100), lambda f: N("What is the transaction price expressed as a multiple of fixed consideration?", f["v"]["tp"] / f["v"]["fixed"], "abs:0.01"), lambda f: N("What percentage of the standalone selling price of equipment is covered by the allocated consideration, in percent?", f["v"]["aeq"] / f["v"]["ssp_e"] * 100), lambda f: N("How much of the transaction price remains unrecognized at year end if only equipment revenue has been recognized, in millions?", f["v"]["tp"] - f["v"]["aeq"]), ]
RR_K = [ ("Does the entity act as principal or agent in the arrangement described? Answer one of {principal, agent}.", "pa"), ("Is revenue presented gross of the customer payment or net of it? Answer one of {gross, net}.", "pres"), ("Does the arrangement contain a significant financing component? Answer one of {yes, no}.", "fin"), ("Is installation revenue recognized at a point in time or over time? Answer one of {point_in_time, over_time}.", "timing"), ("Is the constrained variable consideration greater than half of the estimated amount? Answer one of {yes, no}.", "con_half"), ]
RR_S = [ ("Summarize the note's allocation of the transaction price between the two performance obligations.", None), ("Summarize how the note treats variable consideration and the constraint.", None), ("Summarize in one sentence the revenue recognition pattern for equipment and for installation.", "pat"), ("Summarize what the note says about the customer's payment terms.", None), ("Summarize how the note decides whether the entity is principal or agent.", None), ]
LS_C = [ lambda f: N("What is the lease liability at commencement, in millions?", f["v"]["liab"], "abs:1"), lambda f: N("What is the right-of-use asset at commencement, in millions?", f["v"]["rou"], "abs:1"), lambda f: N("What is the annual amortization of the right-of-use asset, in millions?", f["v"]["amort"]), lambda f: N("What is the FY2025 interest expense on the lease liability, in millions?", f["v"]["i1"], "abs:1"), lambda f: N("What is the lease liability at the end of FY2025, in millions?", f["v"]["lend"], "abs:1"), lambda f: N("What is the current portion of the lease liability at the end of FY2025, in millions?", f["v"]["cur"], "abs:1"), lambda f: N("What is the non-current portion of the lease liability at the end of FY2025, in millions?", f["v"]["ncur"], "abs:1"), lambda f: N("What is total lease cost recognized in FY2025, in millions?", f["v"]["total"]), lambda f: N("What percentage of total FY2025 lease cost is short-term lease cost, in percent?", f["v"]["st"] / f["v"]["total"] * 100), lambda f: N("What is the carrying amount of the right-of-use asset at the end of FY2025, in millions?", f["v"]["rou_end"]), lambda f: N("What are total undiscounted payments over the lease term, in millions?", f["v"]["pay"] * f["v"]["term"]), lambda f: N("What percentage of total FY2025 lease cost is interest expense, in percent?", f["v"]["i1"] / f["v"]["total"] * 100), ]
LS_Q = [ lambda f: N("What is the right-of-use asset at commencement as a multiple of the annual lease payment?", f["v"]["rou"] / f["v"]["pay"], "abs:0.01"), lambda f: N("What is total interest expense over the lease term, in millions?", f["v"]["pay"] * f["v"]["term"] - f["v"]["liab"], "abs:1"), lambda f: N("What percentage of the right-of-use asset has been amortized at the end of FY2025, in percent?", (f["v"]["rou"] - f["v"]["rou_end"]) / f["v"]["rou"] * 100), lambda f: N("What principal amount is repaid by the payment made at the end of FY2025, in millions?", f["v"]["pay"] - f["v"]["i1"], "abs:1"), lambda f: N("What is total FY2025 lease cost as a percentage of the annual lease payment, in percent?", f["v"]["total"] / f["v"]["pay"] * 100), lambda f: N("If the term were one year longer with the same payment and rate, by how much would the liability increase, in millions?", f["v"]["pay"] * af(f["v"]["rate"], f["v"]["term"] + 1) - f["v"]["liab"], "abs:1"), ]
LS_K = [ ("Is the warehouse lease classified as an operating lease or a finance lease? Answer one of {operating_lease, finance_lease}.", "type"), ("Is the lease liability greater than the right-of-use asset? Answer one of {yes, no}.", "liab_gt_rou"), ("Does the lease contain a bargain purchase option the lessee is reasonably certain to exercise? Answer one of {yes, no}.", "bpo"), ("How is the total lease cost presented in the income statement? Answer one of {straight_line_single_cost, amortization_plus_interest}.", "pattern"), ("In which cash flow category is the principal element of the lease payment presented? Answer one of {operating, financing}.", "cash"), ]
LS_S = [ ("Summarize how the note measures the lease liability and the right-of-use asset.", None), ("Summarize the note's treatment of short-term leases.", None), ("Summarize in one sentence how the lease liability is split between current and non-current.", "cur"), ("Summarize what the note says about the discount rate used.", None), ("Summarize how the right-of-use asset is subsequently measured.", None), ]
SB_C = [ lambda f: N("What is the incremental share count from options under the treasury stock method, in millions?", f["v"]["incr"], "abs:0.1"), lambda f: N("What is the diluted share count for FY2025, in millions?", f["v"]["dil"], "abs:0.1"), lambda f: N("What is the dilution percentage against basic shares, in percent?", f["v"]["dil_pct"]), lambda f: N("What is share-based compensation as a percentage of revenue, in percent?", f["v"]["sbc_pct"]), lambda f: N("By what percentage did share-based compensation expense grow year over year, in percent?", f["v"]["growth"]), lambda f: N("At the stated recognition period, how much unrecognized compensation cost is expensed each year, in millions?", f["v"]["annual"]), lambda f: N("What are the assumed proceeds from option exercise, in millions?", f["v"]["proceeds"], "abs:1"), lambda f: N("How many shares would be repurchased with option proceeds at the average market price, in millions?", f["v"]["buy"], "abs:0.1"), lambda f: N2("What is share-based compensation expense per diluted share, in dollars?", f["v"]["per_share"]), ]
SB_Q = [ lambda f: N("If all options were excluded as out of the money, what would diluted shares be, in millions?", f["v"]["basic"] + f["v"]["rsus"], "abs:0.1"), lambda f: N("If the average market price were 10 percent higher, by how many million shares would the diluted count change?", (f["v"]["opts"] - f["v"]["proceeds"] / (f["v"]["avg"] * 1.1)) - f["v"]["incr"], "abs:0.1"), lambda f: N("What is unrecognized compensation cost as a multiple of the FY2025 expense?", f["v"]["unrec"] / f["v"]["sbc"], "abs:0.01"), lambda f: N("What is the intrinsic value of outstanding options, in millions?", f["v"]["opts"] * (f["v"]["avg"] - f["v"]["strike"]), "abs:1"), lambda f: N("What percentage of options outstanding is represented by the shares repurchased, in percent?", f["v"]["proceeds"] / f["v"]["avg"] / f["v"]["opts"] * 100), lambda f: N("If the same growth rate repeats, what would FY2026 share-based compensation be, in millions?", f["v"]["sbc"] * (1 + f["v"]["growth"] / 100), "abs:1"), ]
SB_S = [ ("Summarize how the note measures and recognizes share-based compensation.", None), ("Summarize the method used to compute dilution from options.", None), ("Summarize in one sentence how the option count and the average market price compare with the prior year.", None), ("Summarize what the note discloses about unrecognized compensation cost.", "unrec"), ("Summarize the note's presentation of share-based compensation within the income statement.", None), ]
IM_C = [ lambda f: N("What impairment loss is recognized in FY2025, in millions?", f["v"]["loss"]), lambda f: N("How much of the impairment loss is allocated to goodwill, in millions?", f["v"]["gw_loss"]), lambda f: N("How much of the impairment loss is allocated to property, plant and equipment, in millions?", f["v"]["ppe_loss"]), lambda f: N("What is the carrying amount of the asset group after the impairment, in millions?", f["v"]["post"]), lambda f: N("What is revised annual depreciation after the impairment, in millions?", f["v"]["dep"]), lambda f: N("By how much do undiscounted cash flows exceed the carrying amount, in millions?", f["v"]["head"]), lambda f: N("What percentage of the carrying amount was written off, in percent?", f["v"]["loss"] / f["v"]["carrying"] * 100), lambda f: N("What percentage of undiscounted cash flows is the carrying amount, in percent?", f["v"]["carrying"] / f["v"]["und"] * 100), lambda f: N("What is the ratio of fair value less costs of disposal to the carrying amount?", f["v"]["fv"] / f["v"]["carrying"], "abs:0.01"), ]
IM_Q = [ lambda f: N("If fair value less costs of disposal were 10 percent lower, what impairment loss would be recognized, in millions?", max(0.0, f["v"]["carrying"] - f["v"]["fv"] * 0.9), "abs:1"), lambda f: N("What goodwill remains on the balance sheet after the impairment, in millions?", f["v"]["gw"] - f["v"]["gw_loss"]), lambda f: N("If the remaining life were one year longer, what would revised annual depreciation be, in millions?", (f["v"]["ppe"] - f["v"]["ppe_loss"]) / (f["v"]["life"] + 1), "abs:1"), lambda f: N("What percentage of the carrying amount is represented by goodwill, in percent?", f["v"]["gw"] / f["v"]["carrying"] * 100), lambda f: N("What is the ratio of undiscounted cash flows to fair value less costs of disposal?", f["v"]["und"] / f["v"]["fv"], "abs:0.01"), lambda f: N("What is the post-impairment carrying amount as a percentage of the pre-impairment carrying amount, in percent?", f["v"]["post"] / f["v"]["carrying"] * 100), ]
IM_K = [ ("Is an impairment test required at the reporting date? Answer one of {required, not_required}.", "test"), ("Which asset absorbs the impairment loss first? Answer one of {goodwill, property_plant_and_equipment, no_loss_recognized}.", "alloc"), ("Does the impairment loss exceed the goodwill balance? Answer one of {yes, no}.", "exceeds_gw"), ("Is the goodwill balance nil at the reporting date? Answer one of {yes, no}.", "gw_zero"), ("Is the carrying amount greater than fair value less costs of disposal? Answer one of {yes, no}.", "fv_below"), ]
IM_S = [ ("Summarize the note's impairment test and how the loss is measured.", None), ("Summarize how the impairment loss is allocated within the asset group.", None), ("Summarize in one sentence how depreciation changes after the impairment.", None), ("Summarize what the note says about the cash flow projections used.", None), ("Summarize the note's treatment of reversals of impairment.", None), ]
TX_C = [ lambda f: N("What is total income tax expense for FY2025, in millions?", f["v"]["total"]), lambda f: N("What is the FY2025 effective tax rate, in percent?", f["v"]["etr"]), lambda f: N("How many percentage points does the effective tax rate differ from the enacted rate?", f["v"]["etr"] - f["v"]["rate"]), lambda f: N("What is the gross deferred tax asset, in millions?", f["v"]["dta"]), lambda f: N("What is the deferred tax liability, in millions?", f["v"]["dtl"]), lambda f: N("What is net deferred tax before the valuation allowance, in millions?", f["v"]["net"]), lambda f: N("What is net deferred tax after the valuation allowance, in millions?", f["v"]["after"]), lambda f: N("What percentage of the gross deferred tax asset is covered by the valuation allowance, in percent?", f["v"]["va_pct"]), ]
TX_Q = [ lambda f: N("If the valuation allowance were released in full, what would net deferred tax be, in millions?", f["v"]["net"]), lambda f: N("What percentage of total tax expense is deferred tax expense, in percent?", f["v"]["defr"] / f["v"]["total"] * 100), lambda f: N("If the enacted rate were 2 percentage points higher, what would the gross deferred tax asset be, in millions?", f["v"]["dtd"] * (f["v"]["rate"] + 2) / 100, "abs:1"), lambda f: N("What percentage of pretax income is current tax expense, in percent?", f["v"]["cur"] / f["v"]["pre"] * 100), lambda f: N("What is net deferred tax after the allowance as a percentage of pretax income, in percent?", f["v"]["after"] / f["v"]["pre"] * 100), lambda f: N("What would the effective tax rate be if deferred tax expense were zero, in percent?", f["v"]["cur"] / f["v"]["pre"] * 100), ]
TX_K = [ ("Is a valuation allowance required against the deferred tax asset? Answer one of {valuation_allowance_required, no_valuation_allowance}.", "va"), ("Which evidence is decisive for the valuation allowance conclusion? Answer one of {cumulative_losses, positive_taxable_income, mixed_evidence}.", "evidence"), ("Does the valuation allowance exceed a quarter of the gross deferred tax asset? Answer one of {yes, no}.", "quarter"), ("Is the effective tax rate above or below the enacted rate? Answer one of {above, below}.", "etr_above"), ("How are deferred tax balances classified on the balance sheet? Answer one of {non_current, current}.", "class"), ]
TX_S = [ ("Summarize how the note measures deferred tax assets and liabilities.", None), ("Summarize the note's policy for the valuation allowance.", None), ("Summarize in one sentence how total tax expense relates to current and deferred tax.", "tt"), ("Summarize what the note says about the enacted rate.", None), ("Summarize how the valuation allowance is reassessed.", None), ]
ES_Q = [ lambda f: N("What is the revised annual depreciation charge, in millions?", f["v"]["dep_new"]), lambda f: N("By what percentage did annual depreciation change, in percent?", f["v"]["impact_pct"]), lambda f: N("What is the carrying amount at the end of FY2025 after the revised charge, in millions?", f["v"]["carrying_end"]), lambda f: N("What would FY2026 depreciation have been without the change, in millions?", f["v"]["dep_old"]), lambda f: N("How many years of useful life remained at the date of change before the revision?", f["v"]["life"] - f["v"]["elapsed"]), lambda f: N("What is the revised annual charge as a percentage of original cost, in percent?", f["v"]["dep_new"] / f["v"]["cost"] * 100), ]
ES_K = [ ("Is the change an error correction, a change in accounting estimate or a change in accounting policy? Answer one of {error_correction, change_in_estimate, change_in_policy}.", "nature"), ("Does the change increase or decrease FY2026 depreciation expense? Answer one of {increase, decrease}.", "direction"), ("How is the change applied? Answer one of {prospectively, retrospectively}.", "apply"), ("Is the revised remaining useful life shorter than the remaining life at the date of change? Answer one of {yes, no}.", "shorter"), ("Is the revised annual charge higher than the charge that would have applied without the change? Answer one of {yes, no}.", "higher"), ]
ES_S = [ ("Summarize the note's explanation of why the estimate changed and how it is applied.", None), ("Summarize in one sentence the effect of the change on the current period charge.", None), ("Summarize what the note says about prior period comparatives.", None), ("Summarize how the revised residual value affects the depreciation charge.", None), ("Summarize the note's description of the review performed during FY2025.", None), ]
RS_Q = [ lambda f: N("What is FY2024 revenue as restated, in millions?", f["v"]["rev"] + f["v"]["rev_chg"]), lambda f: N("What is FY2024 operating income as restated, in millions?", f["v"]["oi"] + f["v"]["oi_chg"]), lambda f: N("What is the change in FY2024 revenue versus the amount as originally reported, in millions?", f["v"]["rev_chg"]), lambda f: N("What is the change in FY2024 operating income versus the amount as originally reported, in millions?", f["v"]["oi_chg"]), lambda f: N("What is the change in opening retained earnings, in millions?", f["v"]["re_chg"]), lambda f: N("What is the change in FY2024 cost of sales, in millions?", f["v"]["cost_chg"]), ]
RS_K = [ ("Is the item an error correction, a change in accounting policy or a change in accounting estimate? Answer one of {error_correction, change_in_policy, change_in_estimate}.", "nature"), ("Are prior period comparatives restated? Answer one of {restated, not_restated}.", "comp"), ("What is the effect on opening retained earnings? Answer one of {decrease, no_effect}.", "retained"), ("Which transition method applies? Answer one of {retrospective_restatement, retrospective_reclassification, prospective_application}.", "method"), ("Does the adjustment correct a prior period error? Answer one of {yes, no}.", "error"), ]
RS_S = [ ("Summarize what the note says was corrected or changed and why.", None), ("Summarize in one sentence how the adjustment affects the comparative figures.", None), ("Summarize what the note says about the entity's controls after the matter was identified.", None), ("Summarize whether the adjustment affects cash flows.", None), ("Summarize how the note presents the restated columns.", None), ]
REFS = { "rev": lambda f: "Revenue of %d compares with %d in FY2024, while GAAP operating income of %d compares with %d." % (f["v"]["rev"], f["v"]["rev0"], f["v"]["oi"], f["v"]["oi0"]), "def": lambda f: "Adjusted operating income adds back share-based compensation, acquisition-related amortization and restructuring charges to GAAP operating income.", "pat": lambda f: "Equipment revenue is recognized when control transfers, while installation revenue is recognized over time.", "cur": lambda f: "The current portion is the principal component of the payment due within twelve months, with the remainder non-current.", "unrec": lambda f: "Unrecognized compensation cost of %d will be recognized over a weighted average period of %s years." % (f["v"]["unrec"], d1(f["v"]["wap"])), "tt": lambda f: "Total income tax expense is current tax expense plus deferred tax expense.", }

def summ_specs(items):
    out = []
    for q, ref in items:
        if ref is None:
            out.append(lambda f, q=q: S(q, None))
        else:
            fn = REFS[ref]
            out.append(lambda f, q=q, fn=fn: S(q, fn(f)))
    return out
SPECS = { ("nongaap", "calc"): NG_C, ("nongaap", "extraction"): ex_specs([0, 3, 6, 9, 12]), ("nongaap", "qa"): NG_Q, ("nongaap", "summarization"): summ_specs(NG_S), ("revrec", "calc"): RR_C, ("revrec", "extraction"): ex_specs([0, 2, 4, 6, 8]), ("revrec", "qa"): RR_Q, ("revrec", "classification"): cls_specs(RR_K), ("revrec", "summarization"): summ_specs(RR_S), ("lease", "calc"): LS_C, ("lease", "extraction"): ex_specs([0, 2, 4, 1, 5]), ("lease", "qa"): LS_Q, ("lease", "classification"): cls_specs(LS_K), ("lease", "summarization"): summ_specs(LS_S), ("sbc", "calc"): SB_C, ("sbc", "extraction"): ex_specs([0, 3, 6, 9, 12]), ("sbc", "qa"): SB_Q, ("sbc", "summarization"): summ_specs(SB_S), ("impair", "calc"): IM_C, ("impair", "extraction"): ex_specs([0, 2, 4, 6, 1]), ("impair", "qa"): IM_Q, ("impair", "classification"): cls_specs(IM_K), ("impair", "summarization"): summ_specs(IM_S), ("tax", "calc"): TX_C, ("tax", "extraction"): ex_specs([0, 2, 4, 6, 1]), ("tax", "qa"): TX_Q, ("tax", "classification"): cls_specs(TX_K), ("tax", "summarization"): summ_specs(TX_S), ("estimate", "extraction"): ex_specs([0, 2, 4, 6, 1]), ("estimate", "qa"): ES_Q, ("estimate", "classification"): cls_specs(ES_K), ("estimate", "summarization"): summ_specs(ES_S), ("restate", "extraction"): ex_specs([0, 3, 6, 9, 2]), ("restate", "qa"): RS_Q, ("restate", "classification"): cls_specs(RS_K), ("restate", "summarization"): summ_specs(RS_S), }
# --------------------------------------------------------------------------- #
# tool use rows
# --------------------------------------------------------------------------- #
ISSUER = {"issuer": {"type": "string", "description": "legal name of the fictitious issuer"}, "fiscal_year": {"type": "integer", "description": "fiscal year, e.g. 2025"}}

def _tool(name, desc):
    return {"name": name, "description": desc, "parameters": {"type": "object", "properties": dict(ISSUER), "required": ["issuer", "fiscal_year"]}}
TOOL_DEFS = { "get_nongaap_bridge": _tool("get_nongaap_bridge", "Return the GAAP to non-GAAP reconciliation for one issuer and fiscal year."), "get_adjustment_detail": _tool("get_adjustment_detail", "Return the individual non-GAAP adjustment lines and the related tax effect."), "get_sbc_detail": _tool("get_sbc_detail", "Return share-based compensation expense, unrecognized cost and revenue for one issuer and fiscal year."), "get_award_summary": _tool("get_award_summary", "Return option and restricted stock unit balances together with basic shares."), "get_price_detail": _tool("get_price_detail", "Return the weighted average exercise price and the average market price for the year."), }

def p_bridge(f):
    v = f["v"]
    return {"issuer": f["name"], "fiscal_year": 2025, "revenue": v["rev"], "gaap_operating_income": v["oi"], "share_based_compensation": v["sbc"], "acquisition_amortization": v["am"], "restructuring": v["rs"], "tax_effect": v["tx"], "gaap_net_income": v["ni"], "diluted_shares_m": v["ds"]}

def p_bridge_prior(f):
    v = f["v"]
    return {"issuer": f["name"], "fiscal_year": 2024, "revenue": v["rev0"], "gaap_operating_income": v["oi0"], "share_based_compensation": v["sbc0"], "acquisition_amortization": v["am0"], "restructuring": v["rs0"], "gaap_net_income": v["ni0"]}

def p_adj(f):
    v = f["v"]
    return {"issuer": f["name"], "fiscal_year": 2025, "lines": [{"label": "share_based_compensation", "amount": v["sbc"]}, {"label": "acquisition_amortization", "amount": v["am"]}, {"label": "restructuring", "amount": v["rs"]}], "tax_effect": v["tx"], "gaap_net_income": v["ni"], "diluted_shares_m": v["ds"]}

def p_sbc(f):
    v = f["v"]
    return {"issuer": f["name"], "fiscal_year": 2025, "sbc_expense": v["sbc"], "revenue": v["rev"], "unrecognized_cost": v["unrec"], "recognition_period_years": v["wap"]}

def p_award(f):
    v = f["v"]
    return {"issuer": f["name"], "fiscal_year": 2025, "options_outstanding_m": v["opts"], "unvested_rsus_m": v["rsus"], "basic_shares_m": v["basic"], "weighted_average_exercise_price": v["strike"], "average_market_price": v["avg"]}

def p_price(f):
    v = f["v"]
    return {"issuer": f["name"], "fiscal_year": 2025, "weighted_average_exercise_price": v["strike"], "average_market_price": v["avg"], "options_outstanding_m": v["opts"], "unvested_rsus_m": v["rsus"]}

def p_missing(f):
    return {"issuer": f["name"], "fiscal_year": 2025, "error": "detail_not_available", "message": "This issuer does not disclose the requested breakdown at that level."}
TOOL_NG = [ {"tool": "get_nongaap_bridge", "payload": p_bridge, "ask": "Pull the non-GAAP reconciliation for this issuer for FY2025.", "final": "Using that bridge, what is adjusted operating income for the year, in millions?"}, {"tool": "get_nongaap_bridge", "payload": p_bridge_prior, "ask": "I need the prior year GAAP to adjusted bridge for the same issuer.", "final": "Using the prior year figures returned, what was adjusted operating income for that year, in millions?"}, {"tool": "get_adjustment_detail", "payload": p_adj, "ask": "Get the individual adjustment lines behind the non-GAAP reconciliation.", "final": "What share of the total add-backs is share-based compensation, in percent?"}, {"tool": "get_adjustment_detail", "payload": p_adj, "ask": "Show me the adjustment detail and the diluted share count for the issuer.", "final": "Using the tax effect returned, what is adjusted diluted EPS, in dollars?"}, {"tool": "get_nongaap_bridge", "payload": p_bridge, "ask": "Retrieve the reconciliation table for the issuer's fiscal 2025 results.", "final": "What is the adjusted operating margin, in percent?"}, {"tool": "get_adjustment_detail", "payload": p_adj, "ask": "Pull the adjustment lines and the tax effect for FY2025.", "final": "What is adjusted net income after the tax effect, in millions?"}, {"tool": "get_nongaap_bridge", "payload": p_bridge_prior, "ask": "Get the prior year bridge so I can compare the two years.", "final": "Using the prior year figures returned, what were total add-backs for that year, in millions?"}, {"tool": "get_adjustment_detail", "payload": p_missing, "ask": "Get the segment-level non-GAAP bridge for this issuer.", "final": "Using the segment bridge, what is the adjusted operating margin of the largest segment, in percent?"}, ]
TOOL_SB = [ {"tool": "get_award_summary", "payload": p_award, "ask": "Pull the share-based compensation detail for this issuer for FY2025.", "final": "Using that detail, what is the incremental share count from options under the treasury stock method, in millions?"}, {"tool": "get_award_summary", "payload": p_award, "ask": "I need the equity award balances at the fiscal year end.", "final": "What is the diluted share count including unvested restricted units, in millions?"}, {"tool": "get_sbc_detail", "payload": p_sbc, "ask": "Get the unrecognized compensation cost balance for the issuer.", "final": "At the stated recognition period, how much will be expensed each year, in millions?"}, {"tool": "get_price_detail", "payload": p_price, "ask": "What were the weighted average exercise price and the average market price for the year?", "final": "What are the assumed proceeds from option exercise, in millions?"}, {"tool": "get_sbc_detail", "payload": p_sbc, "ask": "Show me share-based compensation expense for the current year.", "final": "What is share-based compensation as a percentage of revenue, in percent?"}, {"tool": "get_award_summary", "payload": p_award, "ask": "Pull the award summary and the basic share count for the issuer.", "final": "What is the dilution percentage against basic shares, in percent?"}, {"tool": "get_price_detail", "payload": p_price, "ask": "Retrieve the price inputs used in the dilution calculation.", "final": "How many shares would be repurchased with option proceeds at the average market price, in millions?"}, {"tool": "get_sbc_detail", "payload": p_missing, "ask": "Get the grant-date fair value by award tranche for this issuer.", "final": "What was the weighted average grant-date fair value of options vested in the year, in dollars?"}, ]
TOOL_SPECS = {"nongaap": TOOL_NG, "sbc": TOOL_SB}

def tool_row(fx, spec):
    msgs = [ {"role": "system", "content": "You are supporting an accounting policy review for %s. Fiscal year ended %s %d. Retrieve note data with the tools and never invent a figure." % (fx["name"], fx["fy_end"], fx["fy"])}, {"role": "user", "content": spec["ask"]}, {"role": "assistant", "content": "I will call %s for %s for fiscal year 2025." % (spec["tool"], fx["name"])}, {"role": "tool", "content": json.dumps(spec["payload"](fx), ensure_ascii=False)}, {"role": "user", "content": spec["final"]}, ]
    return {"id": "", "task": "", "source": "synthetic:" + AREA, "messages": msgs, "tools": [TOOL_DEFS[spec["tool"]]], "ground_truth": None, "answer_type": "text", "tolerance": None, "split": "", "thinking": ""}

def single_row(fx, r):
    return {"id": "", "task": "", "source": "synthetic:" + AREA, "context": fx["ctx"], "question": r["q"], "ground_truth": r["gt"], "answer_type": r["at"], "tolerance": r["tol"], "split": "", "thinking": ""}

def make_fixture(doc, co, m):
    seed = int(hashlib.sha256(("%s|%s" % (doc, co[0])).encode()).hexdigest()[:16], 16)
    return BUILDERS[doc](co, random.Random(seed), m)

def build_rows():
    pending = []
    for doc in DOCS:
        pos = 0
        for task, cnt in TASK_SLICES[doc]:
            specs = SPECS.get((doc, task))
            for m in range(cnt):
                fx = make_fixture(doc, COMPANIES[pos + m], m)
                for k in range(ROWS_PER_FIXTURE):
                    if task == "tool_use":
                        ts = TOOL_SPECS[doc][(m + k) % len(TOOL_SPECS[doc])]
                        pending.append((task, fx["key"], k, tool_row(fx, ts)))
                    else:
                        sp = specs[(m + k) % len(specs)]
                        pending.append((task, fx["key"], k, single_row(fx, sp(fx))))
            pos += cnt
    return pending

def mask(s):
    return re.sub(r"\d+(?:[.,]\d+)*", "#", re.sub(r"\s+", " ", s).strip().lower())

def assemble():
    pending = build_rows()
    rows = []
    for task in ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]:
        sub = [p for p in pending if p[0] == task]
        keys = sorted({p[1] for p in sub}, key=lambda k: hashlib.sha256((task + "|" + k).encode()).hexdigest())
        a, b, c = SPLIT_FIXTURES[task]
        assert a + b + c == len(keys), (task, len(keys))
        smap = {}
        for i, key in enumerate(keys):
            smap[key] = "train" if i < a else ("val" if i < a + b else "test")
        sub.sort(key=lambda p: (p[1], p[2]))
        for i, item in enumerate(sub, 1):
            row = item[3]
            row["id"] = "fin_%s_%s_%06d" % (AREA, ABBR[task], i)
            row["task"] = task
            row["split"] = smap[item[1]]
            row["thinking"] = THINK[task]
            rows.append(row)
    return rows

def selfcheck(rows):
    fams, ctxs, bodies = {}, set(), set()
    for r in rows:
        if "context" in r:
            ctxs.add(mask(r["context"]))
            body = mask(r["context"]) + "|" + mask(r["question"])
            fam = mask(r["question"])[:160]
            if r["task"] == "extraction":
                assert r["ground_truth"] in r["context"], (r["id"], r["ground_truth"])
        else:
            body = mask(json.dumps(r["messages"], ensure_ascii=False, sort_keys=True))
            fam = mask(r["messages"][1]["content"])[:160]
        assert body not in bodies, r["id"]
        bodies.add(body)
        fams[fam] = fams.get(fam, 0) + 1
    assert len(rows) == 1000, len(rows)
    assert len(fams) >= 25 and max(fams.values()) <= 40, (len(fams), max(fams.values()))
    assert len(ctxs) >= 120, len(ctxs)
    return fams

def report(rows, fams):
    from collections import Counter
    by_task = Counter(r["task"] for r in rows)
    by_split = Counter(r["split"] for r in rows)
    by_at = Counter(r["answer_type"] for r in rows if r["ground_truth"] is not None)
    ctx = {mask(r["context"]) for r in rows if "context" in r}
    tool = [r for r in rows if r["task"] == "tool_use"]
    multi = sum(1 for r in tool if any(m["role"] == "assistant" for m in r["messages"]))
    rep = {"area": AREA, "profile": "B", "rows": len(rows), "by_task": {k: by_task.get(k, 0) for k in ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]}, "by_split": {k: by_split.get(k, 0) for k in ["train", "val", "test"]}, "by_answer_type": {k: by_at.get(k, 0) for k in ["number", "text", "label", "list"]}, "distinct_question_families": len(fams), "top_family_share": round(max(fams.values()) / float(len(rows)), 4), "distinct_contexts": len(ctx), "near_dup_pairs": 0, "tool_use_multi_step_share": round(multi / float(len(tool)), 3), "validation": "pass", "sha256": hashlib.sha256(open(OUT, "rb").read()).hexdigest(), "notes": "25 fictitious issuers x 8 policy notes; fixture-level splits; all answers recomputed in code."}
    with open(REPORT, "w") as fh:
        json.dump(rep, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return rep

def main():
    rows = assemble()
    fams = selfcheck(rows)
    with open(OUT, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(report(rows, fams), indent=2))
if __name__ == "__main__":
    main()
