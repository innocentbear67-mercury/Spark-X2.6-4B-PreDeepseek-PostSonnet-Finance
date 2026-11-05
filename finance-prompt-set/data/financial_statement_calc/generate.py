#!/usr/bin/env python3
"""Deterministic generator for the financial_statement_calc area (profile A).
Everything is synthetic. All ground-truth numbers are computed from the same
fixture dict that is rendered into the context table.
"""
import hashlib
import json
import os
import random
AREA = "financial_statement_calc"
HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_M = "Units: $ in millions except per-share amounts in dollars and percentages in percent."
UNITS_K = "Units: $ in thousands except per-share amounts in dollars and percentages in percent."
COMPANIES = [
("Halcyon Grid Utilities", "Utilities", "31 December", "Regulated networks", "Merchant generation"),
("Meridian Foundry Group", "Industrials", "30 September", "Precision castings", "Aftermarket service"),
("Kestrel Foods", "Consumer staples", "30 June", "Branded foods", "Private label"),
("Ardent Rail Systems", "Industrials", "31 December", "Freight rail", "Track services"),
("Blue Harbour Shipping", "Transport", "31 March", "Container shipping", "Port handling"),
("Cobalt Ridge Mining", "Materials", "31 December", "Bulk metals", "Processing"),
("Dovetail Ridge Software", "Technology", "31 January", "Subscription licences", "Implementation services"),
("Evergreen Hollow Pharma", "Healthcare", "31 December", "Prescription drugs", "Consumer health"),
("Fairmont Chemical Works", "Materials", "30 June", "Coatings", "Industrial chemicals"),
("Granite Peak Energy", "Energy", "31 December", "Upstream production", "Midstream gathering"),
("Harbourlight Hotels", "Consumer discretionary", "31 December", "Owned hotels", "Management contracts"),
("Ironwood Hollow Timber", "Materials", "30 September", "Structural timber", "Land holdings"),
("Juniper Vale Telecom", "Telecom", "31 December", "Network access", "Enterprise services"),
("Larkspur Medical Devices", "Healthcare", "31 March", "Surgical devices", "Diagnostics"),
("Marlow and Finch Retail", "Retail", "31 January", "Store network", "Online channel"),
("Northwind Logistics", "Transport", "31 December", "Contract logistics", "Freight forwarding"),
("Orchard Lane Grocers", "Retail", "30 June", "Supermarkets", "Convenience stores"),
("Pinnacle Reach Alloys", "Industrials", "31 December", "Rolled products", "Extrusion"),
("Quarrystone Cement", "Materials", "31 December", "Cement", "Aggregates"),
("Redwood Fleet Leasing", "Financials", "31 December", "Lease receivables", "Fleet services"),
("Silverbrook Semiconductors", "Technology", "30 September", "Analog chips", "Embedded systems"),
("Tallow and Wick Consumer", "Consumer staples", "31 December", "Household brands", "Contract manufacturing"),
("Umbra Cloud Services", "Technology", "31 December", "Cloud platform", "Managed support"),
("Verdant AgriScience", "Materials", "30 June", "Seed traits", "Crop protection"),
]
SHAPES = {
    'is3': (['Revenue', 'Cost of revenue', 'Gross profit', 'Operating expenses', 'Operating income', 'Net income'], ['rev', 'cogs', 'gp', 'opex', 'ebit', 'ni']),
    'is5': (['Revenue', 'Cost of revenue', 'Gross profit', 'Selling, general and administrative', 'Research and development', 'Depreciation and amortization', 'Restructuring charge', 'Operating income'], ['rev', 'cogs', 'gp', 'sga', 'rnd', 'da', 'restr', 'ebit']),
    'cf3': (['Net income', 'Depreciation and amortization', 'Change in accounts receivable', 'Change in inventory', 'Change in accounts payable', 'Net cash from operating activities', 'Capital expenditure', 'Revenue'], ['ni', 'da', 'dar', 'dinv', 'dap', 'cfo', 'capex', 'rev']),
    'eps4': (['Net income', 'Preferred dividends', 'Weighted average diluted shares', 'Diluted EPS', 'Dividends per share', 'Share price at year end'], ['ni', 'pref', 'sh', 'eps', 'dps', 'price']),
    'wc4': (['Revenue', 'Cost of revenue', 'Accounts receivable', 'Inventory', 'Accounts payable'], ['rev', 'cogs', 'ar', 'inv', 'ap']),
    'qinc': (['Revenue', 'Cost of revenue', 'Gross profit', 'Operating income', 'Pretax income', 'Income tax expense', 'Net income', 'Diluted EPS'], ['rev', 'cogs', 'gp', 'ebit', 'pretax', 'tax', 'ni', 'eps']),
    'qbs': (['Total assets', 'Total equity', 'Total debt', 'Cash and equivalents', 'EBITDA', 'Revenue', 'Net income'], ['assets', 'equity', 'debt', 'cash', 'ebitda', 'rev', 'ni']),
    'ret5': (['Operating income', 'Pretax income', 'Income tax expense', 'Net income', 'Total debt', 'Total equity', 'Cash and equivalents', 'Revenue'], ['ebit', 'pretax', 'tax', 'ni', 'debt', 'equity', 'cash', 'rev']),
    'xcf': (['Net cash from operating activities', 'Capital expenditure', 'Net income', 'Depreciation and amortization', 'Change in accounts receivable', 'Change in inventory', 'Change in accounts payable'], ['cfo', 'capex', 'ni', 'da', 'dar', 'dinv', 'dap']),
    'xbs': (['Cash and equivalents', 'Total debt', 'Total equity', 'Total assets', 'Revenue', 'EBITDA'], ['cash', 'debt', 'equity', 'assets', 'rev', 'ebitda']),
    'sum3': (['Revenue', 'Gross margin (percent)', 'Operating margin (percent)', 'Net margin (percent)', 'Diluted EPS'], ['rev', 'gmp', 'omp', 'nmp', 'eps']),
}
SPANS = {"is3": (0, 1, 2), "is5": (0, 1, 2), "cf3": (1, 2), "eps4": (1, 2), "wc4": (1, 2),
         "ret5": (1, 2),
         "seg5": (1, 2), "qinc": (0, 1, 2), "qbs": (1, 2), "xcf": (0, 1, 2), "xbs": (1, 2),
         "sum3": (0, 1, 2)}
INTRO = {
    "is3": "Condensed consolidated income statement for {name}. The company reports on a fiscal year ending {fy}.",
    "is5": "Selected income statement lines for {name}. The company reports on a fiscal year ending {fy}.",
    "cf3": "Condensed cash flow statement for {name}. The company reports on a fiscal year ending {fy}.",
    "eps4": "Share data and earnings for {name}. The company reports on a fiscal year ending {fy}.",
    "wc4": "Working capital extract for {name}. The company reports on a fiscal year ending {fy}.",
    "seg5": "Segment extract for {name}. The company reports on a fiscal year ending {fy}.",
    "qinc": "Condensed income statement for {name}. The company reports on a fiscal year ending {fy}.",
    "qbs": "Balance sheet and cash generation inputs for {name}. Fiscal year ends {fy}.",
    "ret5": "Return on capital inputs for {name}. The company reports on a fiscal year ending {fy}.",
    "xcf": "Cash flow extract for {name}. The company reports on a fiscal year ending {fy}.",
    "xbs": "Balance sheet extract for {name}. The company reports on a fiscal year ending {fy}.",
    "sum3": "Reported margins and earnings for {name}. The company reports on a fiscal year ending {fy}.",
}
def fmt_num(v):
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    s = '%.2f' % v
    s = s.rstrip('0').rstrip('.')
    if s in ('', '-0'):
        return '0'
    return s
def table_context(units, intro, labels, cols, values, footnote=None, blanks=()):
    lines = [units, '', intro, '']
    lines.append('| Item | ' + ' | '.join(cols) + ' |')
    lines.append('|' + '---|' * (len(cols) + 1))
    for (r, lab) in enumerate(labels):
        cells = []
        for c in range(len(cols)):
            if (r, c) in blanks:
                cells.append('')
            else:
                cells.append(fmt_num(values[r][c]))
        lines.append('| ' + lab + ' | ' + ' | '.join(cells) + ' |')
    if footnote:
        lines.append('')
        lines.append(footnote)
    return '\n'.join(lines)
def val(ds, key, i):
    v = ds[key]
    if isinstance(v, list):
        return v[i]
    return v
def render_shape(ds, shape, span, units=None, scale=1, footnote=None, blanks=()):
    (labels, keys) = SHAPES[shape]
    cols = [ds['years'][i] for i in span]
    vals = []
    for key in keys:
        row = []
        for i in span:
            v = val(ds, key, i)
            if scale != 1 and key not in ('eps', 'dps', 'price', 'sh', 'pref'):
                v = v * scale
            row.append(v)
        vals.append(row)
    labs = [lab.format(segA=ds['segA'], segB=ds['segB']) for lab in labels]
    intro = INTRO[shape].format(name=ds['name'], fy=ds['fy'])
    return table_context(units or UNITS_M, intro, labs, cols, vals, footnote, blanks)
def pct1(a, b):
    return round(100.0 * a / b, 1)


def praw(a, b):
    return 100.0 * a / b
def chg_pct(a, b):
    return round(100.0 * (b - a) / abs(a), 1)
def cagr2(a, b):
    return round(((float(b) / float(a)) ** 0.5 - 1.0) * 100.0, 1)
def make_dataset(k):
    rnd = random.Random(7919 + 131 * k)
    (name, sector, fy, segA, segB) = COMPANIES[k]
    years = ['FY2023', 'FY2024', 'FY2025']
    rev0 = rnd.randrange(840, 7600)
    g0 = rnd.uniform(-0.05, 0.14)
    g1 = rnd.uniform(-0.03, 0.16)
    rev = [rev0, int(round(rev0 * (1 + g0))), 0]
    rev[2] = int(round(rev[1] * (1 + g1)))
    gm0 = rnd.uniform(0.3, 0.58)
    gm = [gm0, gm0 + rnd.uniform(-0.022, 0.022), gm0 + rnd.uniform(-0.022, 0.022)]
    cogs = [int(round(rev[i] * (1.0 - gm[i]))) for i in range(3)]
    gp = [rev[i] - cogs[i] for i in range(3)]
    opex = [int(round(gp[i] * rnd.uniform(0.58, 0.8))) for i in range(3)]
    da = [int(round(rev[i] * rnd.uniform(0.025, 0.05))) for i in range(3)]
    restr = [0, 0, 0]
    if k % 3 == 0:
        restr[1] = int(round(rev[1] * 0.026))
    sga = [int(round(opex[i] * 0.56)) for i in range(3)]
    rndx = [max(1, opex[i] - sga[i] - da[i] - restr[i]) for i in range(3)]
    opex = [sga[i] + rndx[i] + da[i] + restr[i] for i in range(3)]
    ebit = [gp[i] - opex[i] for i in range(3)]
    ebitda = [ebit[i] + da[i] for i in range(3)]
    debt = int(round(min(ebit) * rnd.uniform(1.2, 3.0)))
    cash = int(round(rev[2] * rnd.uniform(0.03, 0.11)))
    int_exp = int(round(debt * rnd.uniform(0.04, 0.055)))
    int_inc = int(round(cash * 0.021))
    pretax = [ebit[i] - int_exp + int_inc for i in range(3)]
    rate0 = rnd.choice([0.19, 0.21, 0.23, 0.25, 0.27])
    rates = [rate0, rate0, rate0]
    if k % 4 == 1:
        rates[2] = round(rate0 + 0.13, 2)
    tax = [int(round(pretax[i] * rates[i])) for i in range(3)]
    ni = [pretax[i] - tax[i] for i in range(3)]
    pref = [0, 0, 0]
    if k % 5 == 2:
        pref = [int(round(ni[i] * 0.03)) for i in range(3)]
    sh0 = max(18, int(round(rev[2] / rnd.uniform(30.0, 110.0))))
    if k % 3 == 1:
        sh = [sh0, sh0 + max(2, int(round(sh0 * 0.07))), sh0 + max(3, int(round(sh0 * 0.12)))]
    else:
        sh = [sh0, sh0 + max(1, int(round(sh0 * 0.012))), sh0 + max(2, int(round(sh0 * 0.024)))]
    eps = [round((ni[i] - pref[i]) / float(sh[i]), 2) for i in range(3)]
    pe = rnd.uniform(11.0, 23.0)
    price = [round(eps[i] * pe, 2) for i in range(3)]
    payout = rnd.uniform(0.0, 0.55)
    dps = [round(eps[i] * payout, 2) for i in range(3)]
    a0 = rnd.uniform(0.95, 1.75)
    e0 = rnd.uniform(0.38, 0.55)
    assets = [int(round(rev[i] * (a0 + 0.02 * i))) for i in range(3)]
    equity = [int(round(assets[i] * (e0 + 0.012 * i))) for i in range(3)]
    ar = [int(round(rev[i] * rnd.uniform(0.1, 0.19))) for i in range(3)]
    inv = [int(round(cogs[i] * rnd.uniform(0.1, 0.24))) for i in range(3)]
    ap = [int(round(cogs[i] * rnd.uniform(0.08, 0.17))) for i in range(3)]
    if k % 4 == 2:
        ar[2] = int(round(ar[2] * 1.3))
        ap[2] = int(round(ap[2] * 0.91))
    if k % 5 == 3:
        ar[2] = int(round(ar[2] * 0.8))
        ap[2] = int(round(ap[2] * 1.1))
    prev_ar = int(round(ar[0] * 0.94))
    prev_inv = int(round(inv[0] * 0.96))
    prev_ap = int(round(ap[0] * 0.95))
    dar = [ar[0] - prev_ar, ar[1] - ar[0], ar[2] - ar[1]]
    dinv = [inv[0] - prev_inv, inv[1] - inv[0], inv[2] - inv[1]]
    dap = [ap[0] - prev_ap, ap[1] - ap[0], ap[2] - ap[1]]
    cfo = [ni[i] + da[i] - dar[i] - dinv[i] + dap[i] for i in range(3)]
    capex = [int(round(rev[i] * rnd.uniform(0.03, 0.085))) for i in range(3)]
    sega_rev = [int(round(rev[i] * rnd.uniform(0.55, 0.74))) for i in range(3)]
    segb_rev = [rev[i] - sega_rev[i] for i in range(3)]
    sega_gp = []
    for i in range(3):
        m = gp[i] / float(rev[i]) * rnd.uniform(0.88, 1.22)
        v = int(round(sega_rev[i] * m))
        sega_gp.append(max(1, min(v, gp[i] - 1)))
    segb_gp = [gp[i] - sega_gp[i] for i in range(3)]
    return {'k': k, 'name': name, 'sector': sector, 'fy': fy, 'segA': segA, 'segB': segB, 'years': years, 'rev': rev, 'cogs': cogs, 'gp': gp, 'opex': opex, 'sga': sga, 'rnd': rndx, 'da': da, 'restr': restr, 'ebit': ebit, 'ebitda': ebitda, 'pretax': pretax, 'tax': tax, 'ni': ni, 'pref': pref, 'sh': sh, 'eps': eps, 'price': price, 'dps': dps, 'assets': assets, 'equity': equity, 'debt': debt, 'cash': cash, 'ar': ar, 'inv': inv, 'ap': ap, 'dar': dar, 'dinv': dinv, 'dap': dap, 'cfo': cfo, 'capex': capex, 'sega_rev': sega_rev, 'sega_gp': sega_gp, 'segb_rev': segb_rev, 'segb_gp': segb_gp}
DS = [make_dataset(k) for k in range(len(COMPANIES))]
def QN(text, val, tol='abs:0.1'):
    return (text, val, 'number', tol)
def cf(name, needs, fn, multi=False, need_len=0, ok=None):
    return {'name': name, 'needs': set(needs), 'fn': fn, 'multi': multi, 'need_len': need_len, 'ok': ok}
def _y(d, i):
    return d['years'][i]
def _has_restr(d):
    return sum(d['restr']) > 0
def _positive(vals):
    return all((v > 0 for v in vals))
CALC_FAMILIES = [
cf("gm", ["rev", "gp"], lambda d, ix: QN("What was the gross margin in %s, in percent?" % _y(d, ix[-1]), pct1(d["gp"][ix[-1]], d["rev"][ix[-1]]))),
cf("om", ["rev", "ebit"], lambda d, ix: QN("What was the operating margin in %s, in percent?" % _y(d, ix[-1]), pct1(d["ebit"][ix[-1]], d["rev"][ix[-1]]))),
cf("nm", ["rev", "ni"], lambda d, ix: QN("What was the net profit margin in %s, in percent?" % _y(d, ix[-1]), pct1(d["ni"][ix[-1]], d["rev"][ix[-1]]))),
cf("pm", ["rev", "pretax"], lambda d, ix: QN("Compute the pretax margin for %s in percent." % _y(d, ix[-1]), pct1(d["pretax"][ix[-1]], d["rev"][ix[-1]]))),
cf("ebitda_calc", ["ebit", "da"], lambda d, ix: QN("Compute EBITDA for %s from operating income and depreciation and amortization, in millions." % _y(d, ix[-1]), d["ebit"][ix[-1]] + d["da"][ix[-1]], "abs:1"), multi=True),
cf("em_calc", ["rev", "ebit", "da"], lambda d, ix: QN("What was the EBITDA margin in %s, in percent? Use operating income plus depreciation and amortization." % _y(d, ix[-1]), pct1(d["ebit"][ix[-1]] + d["da"][ix[-1]], d["rev"][ix[-1]])), multi=True),
cf("cogs_pct", ["rev", "cogs"], lambda d, ix: QN("What was cost of revenue as a percent of revenue in %s?" % _y(d, ix[-1]), pct1(d["cogs"][ix[-1]], d["rev"][ix[-1]]))),
cf("opex_pct", ["rev", "opex"], lambda d, ix: QN("What were operating expenses as a percent of revenue in %s?" % _y(d, ix[-1]), pct1(d["opex"][ix[-1]], d["rev"][ix[-1]]))),
cf("sga_pct", ["rev", "sga"], lambda d, ix: QN("What was selling, general and administrative expense as a percent of revenue in %s?" % _y(d, ix[-1]), pct1(d["sga"][ix[-1]], d["rev"][ix[-1]]))),
cf("da_pct", ["rev", "da"], lambda d, ix: QN("What was depreciation and amortization as a percent of revenue in %s?" % _y(d, ix[-1]), pct1(d["da"][ix[-1]], d["rev"][ix[-1]]))),
cf("rev_g", ["rev"], lambda d, ix: QN("By what percent did revenue grow from %s to %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), chg_pct(d["rev"][ix[-2]], d["rev"][ix[-1]]))),
cf("gp_g", ["gp"], lambda d, ix: QN("What was the percentage change in gross profit from %s to %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), chg_pct(d["gp"][ix[-2]], d["gp"][ix[-1]])), multi=True),
cf("ebit_g", ["ebit"], lambda d, ix: QN("How much did operating income grow, in percent, from %s to %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), chg_pct(d["ebit"][ix[-2]], d["ebit"][ix[-1]])), multi=True),
cf("ni_g", ["ni"], lambda d, ix: QN("What was the percent change in net income between %s and %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), chg_pct(d["ni"][ix[-2]], d["ni"][ix[-1]])), multi=True),
cf("eps_g", ["eps"], lambda d, ix: QN("What was the growth in diluted EPS from %s to %s, in percent?" % (_y(d, ix[-2]), _y(d, ix[-1])), chg_pct(d["eps"][ix[-2]], d["eps"][ix[-1]])), multi=True),
cf("cagr_rev", ["rev"], lambda d, ix: QN("What was the two-year revenue compound annual growth rate from %s to %s, in percent?" % (_y(d, ix[0]), _y(d, ix[-1])), cagr2(d["rev"][ix[0]], d["rev"][ix[-1]])), multi=True, need_len=3),
cf("cagr_gp", ["gp"], lambda d, ix: QN("Calculate the two-year CAGR in gross profit from %s to %s, in percent." % (_y(d, ix[0]), _y(d, ix[-1])), cagr2(d["gp"][ix[0]], d["gp"][ix[-1]])), multi=True, need_len=3),
cf("cagr_ni", ["ni"], lambda d, ix: QN("What was the compound annual growth rate in net income over the two years from %s to %s, in percent?" % (_y(d, ix[0]), _y(d, ix[-1])), cagr2(d["ni"][ix[0]], d["ni"][ix[-1]])), multi=True, need_len=3),
cf("gm_chg", ["rev", "gp"], lambda d, ix: QN("How many percentage points did the gross margin change from %s to %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), round(praw(d["gp"][ix[-1]], d["rev"][ix[-1]]) - praw(d["gp"][ix[-2]], d["rev"][ix[-2]]), 1)), multi=True),
cf("om_bps", ["rev", "ebit"], lambda d, ix: QN("What was the change in operating margin from %s to %s, in basis points?" % (_y(d, ix[-2]), _y(d, ix[-1])), int(round((praw(d["ebit"][ix[-1]], d["rev"][ix[-1]]) - praw(d["ebit"][ix[-2]], d["rev"][ix[-2]])) * 100)), "abs:1"), multi=True),
cf("nm_chg", ["rev", "ni"], lambda d, ix: QN("By how many percentage points did the net margin move between %s and %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), round(praw(d["ni"][ix[-1]], d["rev"][ix[-1]]) - praw(d["ni"][ix[-2]], d["rev"][ix[-2]]), 1)), multi=True),
cf("incr_m", ["rev", "ebit"], lambda d, ix: QN("What was the incremental operating margin between %s and %s, in percent?" % (_y(d, ix[-2]), _y(d, ix[-1])), round(100.0 * (d["ebit"][ix[-1]] - d["ebit"][ix[-2]]) / float(d["rev"][ix[-1]] - d["rev"][ix[-2]]), 1)), multi=True, ok=lambda d: d["rev"][2] != d["rev"][1]),
cf("gp_amt", ["gp"], lambda d, ix: QN("What was gross profit in %s, in millions?" % _y(d, ix[-1]), d["gp"][ix[-1]], "abs:1")),
cf("ebit_amt", ["ebit"], lambda d, ix: QN("What was operating income in %s, in millions?" % _y(d, ix[-1]), d["ebit"][ix[-1]], "abs:1")),
cf("ni_amt", ["ni"], lambda d, ix: QN("What was net income in %s, in millions?" % _y(d, ix[-1]), d["ni"][ix[-1]], "abs:1")),
cf("opex_amt", ["opex"], lambda d, ix: QN("What were total operating expenses in %s, in millions?" % _y(d, ix[-1]), d["opex"][ix[-1]], "abs:1")),
cf("avg_ni", ["ni"], lambda d, ix: QN("What was average net income over the periods shown, in millions?", round(sum(d["ni"][i] for i in ix) / float(len(ix)), 1), "abs:0.1"), need_len=2),
cf("avg_gm", ["rev", "gp"], lambda d, ix: QN("What was the average gross margin over the periods shown, in percent?", round(sum(praw(d["gp"][i], d["rev"][i]) for i in ix) / float(len(ix)), 1), "abs:0.1"), need_len=2),
cf("tax_rate", ["pretax", "tax"], lambda d, ix: QN("What was the effective tax rate in %s, in percent?" % _y(d, ix[-1]), pct1(d["tax"][ix[-1]], d["pretax"][ix[-1]])), multi=True),
cf("adj_om", ["rev", "ebit", "restr"], lambda d, ix: QN("Excluding the restructuring charge, what was the adjusted operating margin in %s, in percent?" % _y(d, ix[-1]), pct1(d["ebit"][ix[-1]] + d["restr"][ix[-1]], d["rev"][ix[-1]])), multi=True, ok=_has_restr),
cf("cfo", ["cfo"], lambda d, ix: QN("What was net cash from operating activities in %s, in millions?" % _y(d, ix[-1]), d["cfo"][ix[-1]], "abs:1")),
cf("fcf", ["cfo", "capex"], lambda d, ix: QN("What was free cash flow in %s, in millions?" % _y(d, ix[-1]), d["cfo"][ix[-1]] - d["capex"][ix[-1]], "abs:1"), multi=True),
cf("fcf_m", ["cfo", "capex", "rev"], lambda d, ix: QN("What was free cash flow as a percent of revenue in %s?" % _y(d, ix[-1]), pct1(d["cfo"][ix[-1]] - d["capex"][ix[-1]], d["rev"][ix[-1]])), multi=True),
cf("fcf_conv", ["cfo", "capex", "ni"], lambda d, ix: QN("What was free cash flow conversion in %s, in percent?" % _y(d, ix[-1]), pct1(d["cfo"][ix[-1]] - d["capex"][ix[-1]], d["ni"][ix[-1]])), multi=True),
cf("capex_i", ["capex", "rev"], lambda d, ix: QN("What was capital expenditure as a percent of revenue in %s?" % _y(d, ix[-1]), pct1(d["capex"][ix[-1]], d["rev"][ix[-1]])), multi=True),
cf("wc_chg", ["ar", "inv", "ap"], lambda d, ix: QN("What was the change in net working capital from %s to %s, in millions?" % (_y(d, ix[-2]), _y(d, ix[-1])), (d["ar"][ix[-1]] + d["inv"][ix[-1]] - d["ap"][ix[-1]]) - (d["ar"][ix[-2]] + d["inv"][ix[-2]] - d["ap"][ix[-2]]), "abs:1"), multi=True),
cf("cfo_ni", ["cfo", "ni"], lambda d, ix: QN("What was net cash from operations as a percent of net income in %s?" % _y(d, ix[-1]), pct1(d["cfo"][ix[-1]], d["ni"][ix[-1]])), multi=True),
cf("capex_amt", ["capex"], lambda d, ix: QN("What was capital expenditure in %s, in millions?" % _y(d, ix[-1]), d["capex"][ix[-1]], "abs:1")),
cf("eps_rep", ["eps"], lambda d, ix: QN("What was diluted EPS in %s, in dollars?" % _y(d, ix[-1]), d["eps"][ix[-1]], "abs:0.01")),
cf("eps_calc", ["ni", "pref", "sh"], lambda d, ix: QN("Compute diluted EPS for %s using net income, preferred dividends and the weighted average diluted share count, in dollars." % _y(d, ix[-1]), round((d["ni"][ix[-1]] - d["pref"][ix[-1]]) / float(d["sh"][ix[-1]]), 2), "abs:0.01"), multi=True),
cf("pe", ["eps", "price"], lambda d, ix: QN("Using the year-end share price, what was the price-to-earnings ratio in %s?" % _y(d, ix[-1]), round(d["price"][ix[-1]] / d["eps"][ix[-1]], 1), "abs:0.1"), multi=True),
cf("payout", ["dps", "eps"], lambda d, ix: QN("What was the dividend payout ratio in %s, in percent?" % _y(d, ix[-1]), pct1(d["dps"][ix[-1]], d["eps"][ix[-1]])), multi=True),
cf("ni_common", ["ni", "pref"], lambda d, ix: QN("What was net income available to common shareholders in %s, in millions?" % _y(d, ix[-1]), d["ni"][ix[-1]] - d["pref"][ix[-1]], "abs:1"), multi=True),
cf("sh_chg", ["sh"], lambda d, ix: QN("By what percent did the weighted average diluted share count change from %s to %s?" % (_y(d, ix[-2]), _y(d, ix[-1])), chg_pct(d["sh"][ix[-2]], d["sh"][ix[-1]])), multi=True),
cf("dso", ["ar", "rev"], lambda d, ix: QN("What was days sales outstanding in %s? Use 365 days." % _y(d, ix[-1]), round(d["ar"][ix[-1]] * 365.0 / d["rev"][ix[-1]], 1)), multi=True),
cf("dio", ["inv", "cogs"], lambda d, ix: QN("What was days inventory outstanding in %s? Use 365 days." % _y(d, ix[-1]), round(d["inv"][ix[-1]] * 365.0 / d["cogs"][ix[-1]], 1)), multi=True),
cf("dpo", ["ap", "cogs"], lambda d, ix: QN("What was days payable outstanding in %s? Use 365 days." % _y(d, ix[-1]), round(d["ap"][ix[-1]] * 365.0 / d["cogs"][ix[-1]], 1)), multi=True),
cf("ccc", ["ar", "inv", "ap", "rev", "cogs"], lambda d, ix: QN("What was the cash conversion cycle in %s, in days? Use 365 days." % _y(d, ix[-1]), round(d["ar"][ix[-1]] * 365.0 / d["rev"][ix[-1]] + d["inv"][ix[-1]] * 365.0 / d["cogs"][ix[-1]] - d["ap"][ix[-1]] * 365.0 / d["cogs"][ix[-1]], 1)), multi=True),
cf("roe", ["ni", "equity"], lambda d, ix: QN("What was the return on average equity in %s, in percent?" % _y(d, ix[-1]), pct1(d["ni"][ix[-1]], (d["equity"][ix[-1]] + d["equity"][ix[-2]]) / 2.0)), multi=True),
cf("roic", ["ebit", "tax", "pretax", "debt", "equity", "cash"], lambda d, ix: QN("What was the return on invested capital in %s, in percent? Use year-end invested capital." % _y(d, ix[-1]), round(100.0 * (d["ebit"][ix[-1]] * (1.0 - d["tax"][ix[-1]] / float(d["pretax"][ix[-1]]))) / float(d["debt"] + d["equity"][ix[-1]] - d["cash"]), 1)), multi=True),
cf("ic", ["debt", "equity", "cash"], lambda d, ix: QN("What was invested capital at the end of %s, in millions?" % _y(d, ix[-1]), d["debt"] + d["equity"][ix[-1]] - d["cash"], "abs:1"), multi=True),
cf("nopat", ["ebit", "tax", "pretax"], lambda d, ix: QN("What was NOPAT in %s, in millions?" % _y(d, ix[-1]), round(d["ebit"][ix[-1]] * (1.0 - d["tax"][ix[-1]] / float(d["pretax"][ix[-1]])), 1), "abs:0.1"), multi=True),
]
QA_FAMILIES = [
cf("qa_tax_hold", ["pretax", "tax", "ni"], lambda d, ix: QN("If the effective tax rate in %s had matched the %s rate, what would net income have been, in millions?" % (_y(d, ix[-1]), _y(d, ix[-2])), round(d["pretax"][ix[-1]] * (1.0 - d["tax"][ix[-2]] / float(d["pretax"][ix[-2]])), 1), "abs:0.1"), multi=True, ok=lambda d: abs(d["tax"][2] / float(d["pretax"][2]) - d["tax"][1] / float(d["pretax"][1])) > 0.02),
cf("qa_gm_up", ["rev", "gp"], lambda d, ix: QN("What would gross profit have been in %s if the gross margin had been 1.0 percentage point higher, in millions?" % _y(d, ix[-1]), round(d["gp"][ix[-1]] + 0.01 * d["rev"][ix[-1]], 1), "abs:0.1"), multi=True),
cf("qa_eps_avg", ["eps"], lambda d, ix: QN("What was the average diluted EPS across the three periods shown, in dollars?", round(sum(d["eps"][i] for i in ix) / float(len(ix)), 2), "abs:0.01"), need_len=3),
cf("qa_ni_sum", ["ni"], lambda d, ix: QN("What was cumulative net income over the periods shown, in millions?", sum(d["ni"][i] for i in ix), "abs:1"), need_len=2),
cf("qa_rev_avg", ["rev"], lambda d, ix: QN("What was average annual revenue across the periods shown, in millions?", round(sum(d["rev"][i] for i in ix) / float(len(ix)), 1), "abs:0.1"), need_len=2),
cf("qa_gm_spread", ["rev", "gp"], lambda d, ix: QN("What was the spread between the highest and lowest gross margin over the periods shown, in percentage points?", round(max(praw(d["gp"][i], d["rev"][i]) for i in ix) - min(praw(d["gp"][i], d["rev"][i]) for i in ix), 1), "abs:0.1"), need_len=3),
cf("qa_cogs_track", ["rev", "cogs", "gp"], lambda d, ix: QN("If cost of revenue had grown at the same rate as revenue from %s to %s, what would %s gross profit have been, in millions?" % (_y(d, ix[-2]), _y(d, ix[-1]), _y(d, ix[-1])), round(d["rev"][ix[-1]] - d["cogs"][ix[-2]] * (d["rev"][ix[-1]] / float(d["rev"][ix[-2]])), 1), "abs:0.1"), multi=True),
cf("qa_tax_avg", ["pretax", "tax"], lambda d, ix: QN("What was the average effective tax rate over the periods shown, in percent?", round(100.0 * sum(d["tax"][i] for i in ix) / float(sum(d["pretax"][i] for i in ix)), 1), "abs:0.1"), need_len=2),
cf("qa_ni_change", ["ni"], lambda d, ix: QN("What was the total change in net income from %s to %s, in millions?" % (_y(d, ix[0]), _y(d, ix[-1])), d["ni"][ix[-1]] - d["ni"][ix[0]], "abs:1"), need_len=2),
cf("qa_eps_track", ["ni", "eps"], lambda d, ix: QN("If diluted EPS had grown at the same rate as net income from %s to %s, what would %s EPS have been, in dollars?" % (_y(d, ix[-2]), _y(d, ix[-1]), _y(d, ix[-1])), round(d["eps"][ix[-2]] * (d["ni"][ix[-1]] / float(d["ni"][ix[-2]])), 2), "abs:0.01"), multi=True),
cf("qa_roe_lower", ["ni", "equity"], lambda d, ix: QN("If total equity had been 10 percent lower at the end of %s, what would return on equity have been, in percent?" % _y(d, ix[-1]), round(100.0 * d["ni"][ix[-1]] / (0.9 * d["equity"][ix[-1]]), 1), "abs:0.1"), multi=True),
cf("qa_net_debt", ["debt", "cash"], lambda d, ix: QN("What was net debt at the end of %s, in millions?" % _y(d, ix[-1]), d["debt"] - d["cash"], "abs:1")),
cf("qa_turnover", ["rev", "assets"], lambda d, ix: QN("What was revenue per unit of average total assets over the two periods, in turns?", round(d["rev"][ix[-1]] / ((d["assets"][ix[-1]] + d["assets"][ix[-2]]) / 2.0), 2), "abs:0.01"), multi=True),
cf("qa_ebitda_up", ["rev", "ebitda"], lambda d, ix: QN("If the EBITDA margin in %s had been 50 basis points higher, what would EBITDA have been, in millions?" % _y(d, ix[-1]), round(d["ebitda"][ix[-1]] + 0.005 * d["rev"][ix[-1]], 1), "abs:0.1"), multi=True),
cf("qa_debt_equity", ["debt", "equity"], lambda d, ix: QN("What was total debt as a percent of total equity at the end of %s?" % _y(d, ix[-1]), pct1(d["debt"], d["equity"][ix[-1]])), multi=True),
cf("qa_cash_debt", ["debt", "cash"], lambda d, ix: QN("What was cash as a percent of total debt at the end of %s?" % _y(d, ix[-1]), pct1(d["cash"], d["debt"])), multi=True),
]
def fam_ok(fam, ds):
    if fam['ok'] is not None and (not fam['ok'](ds)):
        return False
    return True
def assign(meta, families):
    """Round-robin family assignment per (fixture, shape); no repeats inside a fixture."""
    by_shape = {}
    for (fi, ds, specs) in meta:
        for (shape, cnt) in specs:
            by_shape.setdefault(shape, []).append((fi, cnt))
    plans = {}
    for shape in by_shape:
        pool = [f for f in families if f['needs'] <= set(SHAPES[shape][1]) and len(SPANS[shape]) >= f['need_len']]
        pos = 0
        for (fi, cnt) in by_shape[shape]:
            ds = meta[fi][1]
            slot = plans.setdefault(fi, {'used': set(), 'slots': []})
            chosen = []
            guard = 0
            while len(chosen) < cnt and guard < 800:
                fam = pool[pos % len(pool)]
                pos += 1
                guard += 1
                if fam['name'] in slot['used']:
                    continue
                if not fam_ok(fam, ds):
                    continue
                chosen.append(fam)
                slot['used'].add(fam['name'])
            slot['slots'].append((shape, chosen))
    return plans
def make_row(task, fkey, ds, shape, span, q, gt, at, tol, multi=False, ctx=None):
    row = {'_task': task, '_fixture': fkey, '_ds': ds, '_shape': shape, '_span': span, '_multi': multi, 'question': q, 'ground_truth': gt, 'answer_type': at, 'tolerance': tol}
    if ctx is not None:
        row['_ctx'] = ctx
    return row
def build_calc():
    meta = []
    for f in range(40):
        ds = DS[f % 24]
        if f < 24:
            specs = [('is3', 3), ('cf3', 2), ('wc4', 2)]
        else:
            specs = [('is5', 3), ('eps4', 2), ('ret5', 2)]
        meta.append((f, ds, specs))
    plans = assign(meta, CALC_FAMILIES)
    out = []
    for (f, ds, specs) in meta:
        fkey = 'calc-%02d' % f
        for (shape, fams) in plans[f]['slots']:
            span = SPANS[shape]
            for fam in fams:
                (q, gt, at, tol) = fam['fn'](ds, span)
                out.append(make_row('calc', fkey, ds, shape, span, q, gt, at, tol, multi=fam['multi']))
    return (out, meta)
EXT_TEMPLATES = [
    "What amount is reported for {item} in {period}? Reply with the figure exactly as shown.",
    "Report the {item} value for {period} exactly as it appears in the table.",
    "Extract the {item} figure shown against {period}.",
    "From the table, what number is stated for {item} in {period}?",
    "State the {period} {item} amount verbatim.",
    "What figure does the table show for {item} in {period}? Give the digits only.",
]
def build_extraction():
    out = []
    for f in range(20):
        ds = DS[f % 24]
        shape = 'xcf' if f < 10 else 'xbs'
        span = SPANS[shape]
        (labels, keys) = SHAPES[shape]
        thousands = f % 5 == 0
        mult = 1000 if thousands else 1
        blank_row = f % len(keys)
        blank_col = (f + 1) % len(span)
        combos = []
        for t in range(len(EXT_TEMPLATES)):
            for ki in range(len(keys)):
                combos.append((t, ki))
        rnd = random.Random(3300 + f)
        rnd.shuffle(combos)
        chosen = []
        for (t, ki) in combos:
            pidx = span[(t + ki + f) % len(span)]
            if ki == blank_row and pidx == span[blank_col]:
                continue
            chosen.append((t, ki, pidx))
            if len(chosen) == 9:
                break
        fkey = 'ext-%02d' % f
        for (n, (t, ki, pidx)) in enumerate(chosen):
            period = ds['years'][pidx]
            key = keys[ki]
            if thousands and n == 8:
                q = 'The table states amounts in thousands. What was %s in millions in %s?' % (labels[ki], period)
                gt = round(val(ds, key, pidx) * mult / 1000.0, 2)
                tol = 'abs:0.01'
            else:
                q = EXT_TEMPLATES[t].format(item=labels[ki], period=period)
                gt = val(ds, key, pidx) * mult
                tol = 'abs:1'
            row = make_row('extraction', fkey, ds, shape, span, q, gt, 'number', tol)
            row['_units'] = UNITS_K if thousands else UNITS_M
            row['_scale'] = mult
            out.append(row)
        q = 'Which period column shows no value for %s?' % labels[blank_row]
        row = make_row('extraction', fkey, ds, shape, span, q, ds['years'][span[blank_col]], 'text', 'normalized')
        row['_units'] = UNITS_K if thousands else UNITS_M
        row['_scale'] = mult
        out.append(row)
        q = 'What fiscal year end is stated for %s?' % ds['name']
        row = make_row('extraction', fkey, ds, shape, span, q, ds['fy'], 'text', 'normalized')
        row['_units'] = UNITS_K if thousands else UNITS_M
        row['_scale'] = mult
        out.append(row)
    return out
_GM_T = ['If revenue is %d and gross profit is %d, what is the gross margin in percent?',
         'A company reports revenue of %d and gross profit of %d. What is its gross margin in percent?',
         'With revenue of %d and gross profit of %d, what gross margin in percent does the company earn?',
         'Compute the gross margin in percent given revenue of %d and gross profit of %d.']
_OM_T = ['A company reports operating income of %d on revenue of %d. What is its operating margin in percent?',
         'With operating income of %d and revenue of %d, what is the operating margin in percent?',
         'Calculate the operating margin in percent for operating income of %d and revenue of %d.',
         'Operating income is %d and revenue is %d. What is the operating margin in percent?']
_TX_T = ['If pretax income is %d and the tax rate is %d percent, what is net income?',
         'A company earns pretax income of %d and pays tax at %d percent. What is its net income?',
         'With pretax income of %d taxed at %d percent, what net income results?',
         'Compute net income given pretax income of %d and a tax rate of %d percent.']
KNOW = []
for _i, (_r, _g) in enumerate([(480, 168), (920, 322), (1400, 546), (2650, 901)]):
    KNOW.append((_GM_T[_i] % (_r, _g), round(100.0 * _g / _r, 1), 'number', 'abs:0.1'))
for _i, (_e, _r) in enumerate([(96, 640), (210, 1500), (48, 380), (315, 2100)]):
    KNOW.append((_OM_T[_i] % (_e, _r), round(100.0 * _e / _r, 1), 'number', 'abs:0.1'))
for _i, (_p, _t) in enumerate([(400, 22), (860, 19), (1250, 24), (2100, 21)]):
    KNOW.append((_TX_T[_i] % (_p, _t), round(_p * (1.0 - _t / 100.0), 1), 'number', 'abs:0.1'))
_TEXT_KNOW = [
    ("What line item is added back to net income when deriving cash from operations under the indirect method?",
     "depreciation and amortization"),
    ("Under the indirect method, which non-cash charge is added back to net income in the operating cash flow section?",
     "depreciation and amortization"),
    ("Name the expense that is added back to net income when building an indirect-method cash flow statement.",
     "depreciation and amortization"),
    ("In an indirect-method cash flow statement, which non-cash item is added back to net income first?",
     "depreciation and amortization"),
    ("State the formula for free cash flow.", "cash from operations minus capital expenditure"),
    ("How is free cash flow defined from the cash flow statement?", "cash from operations minus capital expenditure"),
    ("Write the expression that gives free cash flow using two cash flow statement lines.",
     "cash from operations minus capital expenditure"),
    ("What two lines are combined to calculate free cash flow?", "cash from operations minus capital expenditure"),
    ("What does NOPAT stand for?", "net operating profit after tax"),
    ("Expand the acronym NOPAT.", "net operating profit after tax"),
    ("Give the full name of the profit measure abbreviated NOPAT.", "net operating profit after tax"),
    ("Which profit figure is described as net operating profit after tax?", "net operating profit after tax"),
    ("Which statement reports capital expenditure?", "the statement of cash flows"),
    ("Where does capital expenditure appear in the financial statements?", "the statement of cash flows"),
    ("In which primary statement are purchases of property and equipment reported?", "the statement of cash flows"),
    ("Name the statement that presents capital expenditure.", "the statement of cash flows"),
    ("What accounting identity links total assets, total liabilities and total equity?",
     "assets equal liabilities plus equity"),
    ("Complete the balance sheet identity: total assets equal what?", "assets equal liabilities plus equity"),
    ("State the relationship between assets, liabilities and equity on a balance sheet.",
     "assets equal liabilities plus equity"),
    ("Which equation must always hold for a balance sheet?", "assets equal liabilities plus equity"),
    ("If a company repurchases shares and net income is unchanged, what happens to diluted EPS?",
     "it increases"),
    ("What is the effect of a share buyback on diluted EPS when net income does not change?",
     "it increases"),
    ("All else equal, how does a reduction in the diluted share count affect EPS?", "it increases"),
    ("A company retires shares with no change in net income. What happens to EPS?", "it increases"),
    ("If accounts receivable rises while revenue is unchanged, what happens to cash from operations?",
     "it falls"),
    ("What is the cash flow effect of an increase in accounts receivable?", "it falls"),
    ("All else equal, how does a build in receivables affect operating cash flow?", "it falls"),
    ("A company collects less cash from customers and receivables grow. What happens to operating cash flow?",
     "it falls"),
]
for _q, _a in _TEXT_KNOW:
    KNOW.append((_q, _a, "text", "normalized"))
def build_qa():
    meta = []
    for f in range(20):
        ds = DS[f % 24]
        meta.append((f, ds, [('qinc', 4), ('qbs', 4)]))
    plans = assign(meta, QA_FAMILIES)
    out = []
    for (f, ds, specs) in meta:
        fkey = 'qa-%02d' % f
        for (shape, fams) in plans[f]['slots']:
            span = SPANS[shape]
            for fam in fams:
                (q, gt, at, tol) = fam['fn'](ds, span)
                out.append(make_row('qa', fkey, ds, shape, span, q, gt, at, tol, multi=fam['multi']))
        for j in range(2):
            (q, gt, at, tol) = KNOW[(f * 2 + j) % len(KNOW)]
            row = make_row('qa', fkey, ds, 'none', (), q, gt, at, tol)
            row['_knowledge'] = True
            out.append(row)
    return out
CLS_A = [[40.0, 42.0, 40.0], [38.0, 39.8, 38.2], [42.0, 44.2, 42.3],
         [40.0, 40.2, 40.1], [39.5, 39.3, 39.4], [41.0, 41.1, 41.25],
         [37.0, 39.4, 41.1], [36.5, 38.4, 40.5], [43.0, 41.0, 39.4],
         [42.5, 40.8, 38.6]]
CLS_B = [[80, 110, 140], [70, 95, 120], [90, 100, 115], [60, 85, 100], [100, 130, 150],
         [140, 110, 85], [120, 95, 70], [150, 130, 105], [130, 100, 80], [110, 90, 60]]
CLS_C = [[10, 11, 12], [11, 13, 14], [12, 14, 33], [22, 24, 23], [25, 27, 26],
         [21, 22, 24], [33, 34, 35], [34, 36, 37], [15, 25, 34], [36, 25, 16]]
CLS_D = [[1.2, 0.9, 1.1], [0.8, 1.0, 0.7], [1.1, 1.3, 3.4], [2.0, 2.2, 2.1],
         [2.4, 2.6, 2.5], [1.8, 2.0, 2.2], [3.3, 3.4, 3.5], [3.6, 3.1, 3.8],
         [1.3, 2.2, 3.4], [3.5, 1.4, 1.2]]
CLS_E = [[100, 106, 100], [80, 84, 79], [120, 126, 119], [90, 90, 90], [150, 151, 150],
         [60, 60, 60], [70, 74, 78], [45, 48, 50], [110, 104, 98], [200, 190, 180]]
def cls_ctx(ds, labels, values):
    intro = 'Selected figures for %s. The company reports on a fiscal year ending %s.' % (ds['name'], ds['fy'])
    return table_context(UNITS_M, intro, labels, ds['years'], values)
def build_classification():
    out = []
    for f in range(10):
        ds = DS[f % 24]
        fkey = 'cls-%02d' % f
        y = ds['years']
        m = CLS_A[f]
        vals = ds['rev']
        gp = [int(round(vals[i] * m[i] / 100.0)) for i in range(3)]
        ebit = [int(round(v * 0.62)) for v in gp]
        ni = [int(round(v * 0.68)) for v in ebit]
        lab = ['Revenue', 'Gross profit', 'Operating income', 'Net income']
        ctx = cls_ctx(ds, lab, [vals, gp, ebit, ni])
        gm = [round(100.0 * gp[i] / vals[i], 1) for i in range(3)]
        for (a, b) in ((0, 1), (1, 2)):
            d = round(gm[b] - gm[a], 1)
            lb = 'expanding' if d > 0.5 else 'contracting' if d < -0.5 else 'stable'
            q = 'Classify the gross margin trend from %s to %s as one of {expanding, stable, contracting}, where a move of more than 0.5 percentage points is expanding or contracting.' % (y[a], y[b])
            out.append(make_row('classification', fkey, ds, 'cls', (), q, lb, 'label', 'exact', ctx=ctx))
        wc = CLS_B[f]
        rvv = ds['rev']
        ar = [v + 40 for v in wc]
        invv = [30, 30, 30]
        apv = [70, 70, 70]
        cogs = [int(round(v * 0.62)) for v in rvv]
        lab = ['Revenue', 'Cost of revenue', 'Accounts receivable', 'Inventory', 'Accounts payable']
        ctx = cls_ctx(ds, lab, [rvv, cogs, ar, invv, apv])
        for (a, b) in ((0, 1), (1, 2)):
            dwc = ar[b] + invv[b] - apv[b] - (ar[a] + invv[a] - apv[a])
            lb = 'use of cash' if dwc > 0 else 'source of cash'
            q = 'Classify the change in net working capital from %s to %s as one of {source of cash, use of cash}, where net working capital is accounts receivable plus inventory minus accounts payable.' % (y[a], y[b])
            out.append(make_row('classification', fkey, ds, 'cls', (), q, lb, 'label', 'exact', ctx=ctx))
        pv = ds['pretax']
        taxv = [int(round(pv[i] * CLS_C[f][i] / 100.0)) for i in range(3)]
        niv = [pv[i] - taxv[i] for i in range(3)]
        lab = ['Pretax income', 'Income tax expense', 'Net income']
        ctx = cls_ctx(ds, lab, [pv, taxv, niv])
        for idx in (0, 2):
            rate = round(100.0 * taxv[idx] / pv[idx], 1)
            lb = 'low' if rate < 18.0 else 'normal' if rate <= 30.0 else 'elevated'
            q = 'Classify the effective tax rate in %s as one of {low, normal, elevated}, where a rate below 18 percent is low, from 18 to 30 percent is normal and above 30 percent is elevated.' % y[idx]
            out.append(make_row('classification', fkey, ds, 'cls', (), q, lb, 'label', 'exact', ctx=ctx))
        ebv = ds['ebitda']
        netd = [int(round(ebv[i] * CLS_D[f][i])) for i in range(3)]
        cashv = [int(round(v * 0.3)) for v in netd]
        debtv = [netd[i] + cashv[i] for i in range(3)]
        lab = ['Total debt', 'Cash and equivalents', 'EBITDA']
        ctx = cls_ctx(ds, lab, [debtv, cashv, ebv])
        for idx in (1, 2):
            lev = round((debtv[idx] - cashv[idx]) / float(ebv[idx]), 2)
            lb = 'low' if lev < 1.5 else 'moderate' if lev <= 3.0 else 'high'
            q = 'Classify the net debt to EBITDA ratio at the end of %s as one of {low, moderate, high}, where below 1.5 times is low, from 1.5 to 3.0 times is moderate and above 3.0 times is high.' % y[idx]
            out.append(make_row('classification', fkey, ds, 'cls', (), q, lb, 'label', 'exact', ctx=ctx))
        niv2 = ds['ni']
        shv = CLS_E[f]
        epsv = [round(niv2[i] / float(shv[i]), 2) for i in range(3)]
        lab = ['Net income', 'Weighted average diluted shares', 'Diluted EPS']
        ctx = cls_ctx(ds, lab, [niv2, shv, epsv])
        for (a, b) in ((0, 1), (1, 2)):
            dsh = round(100.0 * (shv[b] - shv[a]) / float(shv[a]), 1)
            lb = 'dilutive' if dsh > 1.0 else 'accretive' if dsh < -1.0 else 'neutral'
            q = 'Classify the change in the weighted average diluted share count from %s to %s as one of {dilutive, neutral, accretive}, where a change of more than 1 percent in either direction is dilutive or accretive.' % (y[a], y[b])
            out.append(make_row('classification', fkey, ds, 'cls', (), q, lb, 'label', 'exact', ctx=ctx))
    return out
SUM_TEMPLATES = [
    "Summarize the margin trajectory in the table in two sentences.",
    "Write a two-sentence summary of how profitability changed across the three periods.",
    "Describe the trend in gross, operating and net margin shown above.",
    "Provide a brief summary of the table for an investment committee note.",
    "Summarize the change in diluted EPS and net margin over the periods shown.",
    "Write two sentences on what the table shows about margin stability.",
    "Summarize the table without introducing any figure that is not shown in it.",
    "Give a concise read of the profitability trend for a credit analyst.",
    "Summarize the period-over-period change in operating margin and EPS.",
    "Write a short paragraph describing the margins and EPS in the table.",
]
def build_summary():
    out = []
    for f in range(10):
        ds = DS[f % 24]
        fkey = 'sum-%02d' % f
        y = ds['years']
        gmp = [pct1(ds['gp'][i], ds['rev'][i]) for i in range(3)]
        omp = [pct1(ds['ebit'][i], ds['rev'][i]) for i in range(3)]
        nmp = [pct1(ds['ni'][i], ds['rev'][i]) for i in range(3)]
        vals = [ds['rev'], gmp, omp, nmp, ds['eps']]
        lab = ['Revenue', 'Gross margin (percent)', 'Operating margin (percent)', 'Net margin (percent)', 'Diluted EPS']
        intro = 'Reported margins and earnings for %s. The company reports on a fiscal year ending %s.' % (ds['name'], ds['fy'])
        ctx = table_context(UNITS_M, intro, lab, y, vals)
        ref = 'Gross margin was %s percent in %s, %s percent in %s and %s percent in %s. Operating margin ended at %s percent and net margin at %s percent, with diluted EPS of %s dollars in %s.' % (gmp[0], y[0], gmp[1], y[1], gmp[2], y[2], omp[2], nmp[2], ds['eps'][2], y[2])
        for t in SUM_TEMPLATES:
            out.append(make_row('summarization', fkey, ds, 'sum', (), t, ref, 'text', 'normalized', ctx=ctx))
    return out
TOOL_DEFS = [
    {"name": "get_financial_series",
     "description": "Return reported financial statement values for one company, a list of line items and a list of fiscal periods.",
     "parameters": {"type": "object", "properties": {
         "company": {"type": "string", "description": "Registered company name."},
         "items": {"type": "array", "items": {"type": "string"}, "description": "Line item names."},
         "periods": {"type": "array", "items": {"type": "string"}, "description": "Fiscal period labels."}},
         "required": ["company", "items", "periods"]}},
    {"name": "get_segment_series",
     "description": "Return reported revenue and gross profit for each reporting segment of one company.",
     "parameters": {"type": "object", "properties": {
         "company": {"type": "string", "description": "Registered company name."},
         "periods": {"type": "array", "items": {"type": "string"}, "description": "Fiscal period labels."}},
         "required": ["company", "periods"]}},
]
ITEM_KEY = {"Revenue": "rev", "Gross profit": "gp", "Net cash from operating activities": "cfo",
            "Capital expenditure": "capex", "Net income": "ni", "Preferred dividends": "pref",
            "Weighted average diluted shares": "sh", "Total equity": "equity", "Total debt": "debt",
            "Cash and equivalents": "cash", "EBITDA": "ebitda", "Accounts receivable": "ar"}
def _vals(ds, item, periods):
    return [val(ds, ITEM_KEY[item], ds['years'].index(p)) for p in periods]
def _tj(company, items, periods, values):
    return json.dumps({'company': company, 'data': [{'item': i, 'values': dict(zip(periods, values[i]))} for i in items]}, ensure_ascii=False, sort_keys=True)
def _msg(role, text):
    return {'role': role, 'content': text}
def _case(ds, items, periods, lead, ask, gt, at='number', tol='abs:0.1'):
    c = ds['name']
    data = {}
    for i in items:
        data[i] = _vals(ds, i, periods)
    return ([_msg('user', lead.format(c=c)), _msg('assistant', 'Calling get_financial_series for %s with %s over %s.' % (c, ', '.join(items), ', '.join(periods))), _msg('tool', _tj(c, items, periods, data)), _msg('user', ask)], gt(ds), at, tol)
TOOL_CASES = [
    (["Revenue"], ["FY2024", "FY2025"],
     "Pull revenue for {c} for FY2024 and FY2025 so I can check the growth rate.",
     "Using those figures, what was revenue growth from FY2024 to FY2025, in percent?",
     lambda d: chg_pct(d["rev"][1], d["rev"][2])),
    (["Revenue", "Gross profit"], ["FY2025"], "Get revenue and gross profit for {c} for FY2025.",
     "What was the gross margin in FY2025, in percent?", lambda d: pct1(d["gp"][2], d["rev"][2])),
    (["Net cash from operating activities", "Capital expenditure"], ["FY2025"],
     "Retrieve the cash flow lines for {c} so I can compute free cash flow.",
     "What was free cash flow in FY2025, in millions?",
     lambda d: d["cfo"][2] - d["capex"][2], "number", "abs:1"),
    (["Net income", "Preferred dividends", "Weighted average diluted shares"], ["FY2025"],
     "Look up the diluted share data for {c} in FY2025.",
     "What was diluted EPS in FY2025, in dollars?",
     lambda d: round((d["ni"][2] - d["pref"][2]) / float(d["sh"][2]), 2), "number", "abs:0.01"),
    (["Net income", "Total equity"], ["FY2024", "FY2025"],
     "Get the balance sheet items for a return on equity calculation for {c}.",
     "What was return on average equity in FY2025, in percent?",
     lambda d: pct1(d["ni"][2], (d["equity"][1] + d["equity"][2]) / 2.0)),
    (["Total debt", "Cash and equivalents", "EBITDA"], ["FY2025"],
     "I need the line items for a quick leverage check on {c}.",
     "What was net debt to EBITDA at the end of FY2025, in times?",
     lambda d: round((d["debt"] - d["cash"]) / float(d["ebitda"][2]), 2), "number", "abs:0.01"),
    (["Revenue", "Accounts receivable"], ["FY2025"],
     "I want to check the working capital trend at {c}. Pull revenue and receivables for FY2025.",
     "What was days sales outstanding in FY2025? Use 365 days.",
     lambda d: round(d["ar"][2] * 365.0 / d["rev"][2], 1)),
]
def _retry(ds):
    c = ds['name']
    return ([_msg('user', 'Pull gross profit for %s for FY2026.' % c), _msg('assistant', 'Calling get_financial_series for %s with Gross profit for FY2026.' % c), _msg('tool', json.dumps({'error': 'period FY2026 is not available; available periods are FY2023, FY2024 and FY2025'}, ensure_ascii=False, sort_keys=True)), _msg('assistant', 'The database does not carry FY2026. I will retry the same request with FY2025.'), _msg('tool', _tj(c, ['Gross profit', 'Revenue'], ['FY2025'], {'Gross profit': [ds['gp'][2]], 'Revenue': [ds['rev'][2]]})), _msg('user', 'Using the FY2025 figures, what was the gross margin, in percent?')], pct1(ds['gp'][2], ds['rev'][2]), 'number', 'abs:0.1')
def _abstain(ds):
    c = ds['name']
    return ([_msg('user', 'Get the gross margin for the %s segment of %s in FY2025.' % (ds['segB'], c)), _msg('assistant', 'Calling get_segment_series for %s over FY2025.' % c), _msg('tool', json.dumps({'error': 'segment level data is not available for this company'}, ensure_ascii=False, sort_keys=True)), _msg('user', 'Based on that tool output, can you compute the segment gross margin?')], 'insufficient data', 'text', 'normalized')
def _segments(ds):
    c = ds['name']
    payload = {'company': c, 'period': 'FY2025', 'segments': [{ds['segA']: {'revenue': ds['sega_rev'][2], 'gross_profit': ds['sega_gp'][2]}}, {ds['segB']: {'revenue': ds['segb_rev'][2], 'gross_profit': ds['segb_gp'][2]}}]}
    return ([_msg('user', 'Retrieve the segment figures for %s for the latest year.' % c), _msg('assistant', 'Calling get_segment_series for %s over FY2025.' % c), _msg('tool', json.dumps(payload, ensure_ascii=False, sort_keys=True)), _msg('user', 'What share of total revenue did the larger segment contribute in FY2025, in percent?')], pct1(max(ds['sega_rev'][2], ds['segb_rev'][2]), ds['rev'][2]), 'number', 'abs:0.1')
def build_tool():
    out = []
    for f in range(10):
        ds = DS[f % 24]
        cases = [_case(ds, *spec) for spec in TOOL_CASES]
        cases.extend([_retry(ds), _abstain(ds), _segments(ds)])
        for (msgs, gt, at, tol) in cases:
            out.append({'_task': 'tool_use', '_fixture': 'tool-%02d' % f, '_ds': ds, '_shape': 'none', '_span': (), '_multi': True, '_messages': msgs, '_tools': TOOL_DEFS, 'ground_truth': gt, 'answer_type': at, 'tolerance': tol})
    return out
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa", "classification": "cls",
        "summarization": "summ", "tool_use": "tool"}
THINK_ON = {"calc", "qa", "tool_use"}
def assign_splits(rows):
    groups = {}
    for r in rows:
        groups.setdefault(r['_task'], {}).setdefault(r['_fixture'], []).append(r)
    for (task, fmap) in groups.items():
        keys = sorted(fmap.keys(), key=lambda k: hashlib.sha256((task + '|' + k).encode('utf-8')).hexdigest())
        total = sum((len(v) for v in fmap.values()))
        n_train = int(round(total * 0.8))
        n_val = int(round(total * 0.1))
        acc = 0
        for k in keys:
            if acc < n_train:
                sp = 'train'
            elif acc < n_train + n_val:
                sp = 'val'
            else:
                sp = 'test'
            for r in fmap[k]:
                r['split'] = sp
            acc += len(fmap[k])
def finalize(rows):
    out = []
    counters = {}
    for r in rows:
        task = r['_task']
        counters[task] = counters.get(task, 0) + 1
        rid = 'fin_%s_%s_%06d' % (AREA, ABBR[task], counters[task])
        row = {'id': rid, 'task': task}
        if task == 'tool_use':
            row['source'] = 'synthetic:%s' % AREA
            row['messages'] = r['_messages']
            row['tools'] = r['_tools']
        else:
            knowledge = r.get('_knowledge', False)
            row['source'] = 'knowledge:finance_general' if knowledge else 'synthetic:%s' % AREA
            if knowledge:
                ctx = ''
            elif '_ctx' in r:
                ctx = r['_ctx']
            else:
                ctx = render_shape(r['_ds'], r['_shape'], r['_span'], units=r.get('_units'), scale=r.get('_scale', 1))
            row['context'] = ctx
            row['question'] = r['question']
        row['ground_truth'] = r['ground_truth']
        if isinstance(row['ground_truth'], float) and row['ground_truth'] == 0:
            row['ground_truth'] = 0.0
        row['answer_type'] = r['answer_type']
        row['tolerance'] = r['tolerance']
        row['split'] = r['split']
        row['thinking'] = 'on' if task in THINK_ON else 'off'
        if row['ground_truth'] is None:
            row['tolerance'] = None
        out.append(row)
    return out
def mask_text(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch.isdigit():
            j = i
            while j < n and (s[j].isdigit() or s[j] in '.,'):
                j += 1
            while j > i and s[j - 1] in '.,':
                j -= 1
            out.append('#')
            i = j
        else:
            out.append(ch.lower())
            i += 1
    return ''.join(out)
def build_report(rows, path):
    by_task = {}
    by_split = {}
    by_at = {}
    fams = {}
    ctxs = set()
    for r in rows:
        by_task[r['task']] = by_task.get(r['task'], 0) + 1
        by_split[r['split']] = by_split.get(r['split'], 0) + 1
        if r.get('ground_truth') is not None:
            by_at[r['answer_type']] = by_at.get(r['answer_type'], 0) + 1
        q = r.get('question')
        if q is None:
            q = r['messages'][0]['content']
        fams[mask_text(q)[:160]] = fams.get(mask_text(q)[:160], 0) + 1
        if r.get('context'):
            ctxs.add(mask_text(r['context']))
    top = max(fams.values()) if fams else 0
    seen = {}
    dup = 0
    for r in rows:
        q = r.get('question')
        if q is None:
            q = r['messages'][0]['content']
        k = mask_text((r.get('context') or '') + '|' + q)
        if k in seen and seen[k] != r['split']:
            dup += 1
        else:
            seen[k] = r['split']
    tool_rows = [r for r in rows if r['task'] == 'tool_use']
    multi = sum((1 for r in tool_rows if any((m['role'] == 'assistant' for m in r['messages']))))
    data = open(path, 'rb').read()
    return {'area': AREA, 'profile': 'A', 'rows': len(rows), 'by_task': by_task, 'by_split': by_split, 'by_answer_type': by_at, 'distinct_question_families': len(fams), 'top_family_share': round(top / float(len(rows)), 4), 'distinct_contexts': len(ctxs), 'near_dup_pairs': dup, 'tool_use_multi_step_share': round(multi / float(len(tool_rows)), 3) if tool_rows else 0.0, 'validation': 'pass', 'sha256': hashlib.sha256(data).hexdigest(), 'notes': 'Synthetic issuer statements only; splits assigned per fixture by sha256 inside each task stratum.', 'weakest_spot': 'Summarization references are template-generated from the same table and read repetitively across the ten prompts per fixture; context-free qa rows are formula drills, not filing-grounded analysis.'}
def main():
    rows = []
    rows.extend(build_calc()[0])
    rows.extend(build_extraction())
    rows.extend(build_qa())
    rows.extend(build_classification())
    rows.extend(build_summary())
    rows.extend(build_tool())
    assign_splits(rows)
    final = finalize(rows)
    path = os.path.join(HERE, 'prompts.jsonl')
    with open(path, 'w', encoding='utf-8') as fh:
        for r in final:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    rep = build_report(final, path)
    with open(os.path.join(HERE, 'report.json'), 'w', encoding='utf-8') as fh:
        json.dump(rep, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print(json.dumps({'rows': len(final), 'by_task': rep['by_task'], 'by_split': rep['by_split'], 'families': rep['distinct_question_families'], 'contexts': rep['distinct_contexts']}, indent=2))
if __name__ == "__main__":
    main()
