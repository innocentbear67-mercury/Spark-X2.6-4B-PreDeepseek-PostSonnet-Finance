"""Deterministic generator for the equity_research_docs area (profile B, 1000 rows).

Synthetic annual-report / 10-K style excerpts only. Every ground_truth number is
computed from the same values rendered into the context. No network, no deps.
"""
import hashlib
import json
import os
import random
AREA = 'equity_research_docs'
HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(42)
ABBR = {'calc': 'calc', 'extraction': 'extr', 'qa': 'qa', 'classification': 'cls', 'summarization': 'summ', 'tool_use': 'tool'}
THINK_ON = ('calc', 'qa', 'tool_use')
COMPANIES = [
    {'name': 'Halcyon Grid Utilities', 'sector': 'Utilities', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Regulated Grid', 'Renewables', 'Energy Services'], 'scale': 26000, 'input': 'transformers and high-voltage cable', 'driver': 'higher grid investment'},
    {'name': 'Kestrel Foods', 'sector': 'Packaged Foods', 'fy': '30 June', 'ccy': 'USD', 'segs': ['Pantry', 'Frozen', 'Snacks'], 'scale': 9400, 'input': 'dairy solids and packaging film', 'driver': 'list-price increases'},
    {'name': 'Arclight Semiconductor', 'sector': 'Semiconductors', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Compute', 'Connectivity', 'Embedded'], 'scale': 15200, 'input': 'advanced packaging substrates', 'driver': 'data-centre demand'},
    {'name': 'Vantage Rental Systems', 'sector': 'Industrials', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Rental', 'Sales', 'Service'], 'scale': 6100, 'input': 'engines and hydraulic components', 'driver': 'fleet utilisation'},
    {'name': 'Northwind Logistics', 'sector': 'Transport', 'fy': '31 December', 'ccy': 'EUR', 'segs': ['Freight', 'Contract Logistics', 'Last Mile'], 'scale': 11800, 'input': 'line-haul capacity', 'driver': 'contract renewals'},
    {'name': 'Solstice Renewables', 'sector': 'Renewable Energy', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Solar', 'Storage', 'Services'], 'scale': 4300, 'input': 'solar modules and battery cells', 'driver': 'project commissioning'},
    {'name': 'Cobalt Ridge Mining', 'sector': 'Metals and Mining', 'fy': '31 December', 'ccy': 'AUD', 'segs': ['Copper', 'Zinc', 'By-products'], 'scale': 8800, 'input': 'diesel and grinding media', 'driver': 'higher realised copper prices'},
    {'name': 'Pelican Health Systems', 'sector': 'Healthcare', 'fy': '30 September', 'ccy': 'USD', 'segs': ['Devices', 'Diagnostics', 'Software'], 'scale': 7300, 'input': 'single-use sensors', 'driver': 'procedure volume recovery'},
    {'name': 'Tarn Software Group', 'sector': 'Software', 'fy': '31 January', 'ccy': 'USD', 'segs': ['Subscriptions', 'Perpetual', 'Services'], 'scale': 5200, 'input': 'cloud hosting capacity', 'driver': 'seat expansion'},
    {'name': 'Bluefin Marine Foods', 'sector': 'Seafood', 'fy': '31 December', 'ccy': 'NOK', 'segs': ['Farmed', 'Wild', 'Processing'], 'scale': 6900, 'input': 'feed and smolt supply', 'driver': 'higher harvest volumes'},
    {'name': 'Ironwood Building Products', 'sector': 'Building Materials', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Framing', 'Panels', 'Distribution'], 'scale': 7800, 'input': 'resin and oriented strand board', 'driver': 'repair and remodel demand'},
    {'name': 'Lumen Optical Networks', 'sector': 'Telecom Equipment', 'fy': '31 December', 'ccy': 'EUR', 'segs': ['Line Systems', 'Components', 'Software'], 'scale': 4600, 'input': 'optical transceivers', 'driver': 'carrier capex'},
    {'name': 'Aldercrest Hotels', 'sector': 'Hospitality', 'fy': '31 December', 'ccy': 'GBP', 'segs': ['Owned', 'Managed', 'Franchised'], 'scale': 3900, 'input': 'labour and utilities', 'driver': 'higher revenue per available room'},
    {'name': 'Quarry Lane Apparel', 'sector': 'Apparel', 'fy': '31 January', 'ccy': 'USD', 'segs': ['Wholesale', 'Direct', 'Licensing'], 'scale': 4400, 'input': 'cotton and freight', 'driver': 'direct-to-consumer mix'},
    {'name': 'Sable Chemical Works', 'sector': 'Chemicals', 'fy': '31 December', 'ccy': 'EUR', 'segs': ['Coatings', 'Polymers', 'Agrosciences'], 'scale': 10200, 'input': 'natural gas and titanium dioxide', 'driver': 'price increases'},
    {'name': 'Brightline Rail', 'sector': 'Rail', 'fy': '31 December', 'ccy': 'CAD', 'segs': ['Freight', 'Intermodal', 'Real Estate'], 'scale': 13600, 'input': 'locomotive parts and fuel', 'driver': 'volume recovery'},
    {'name': 'Morrow BioSciences', 'sector': 'Biotech', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Therapeutics', 'Royalties'], 'scale': 2100, 'input': 'contract manufacturing capacity', 'driver': 'royalty revenue'},
    {'name': 'Tidewater Ports', 'sector': 'Ports', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Container', 'Bulk', 'Logistics'], 'scale': 5600, 'input': 'crane parts and labour', 'driver': 'container throughput'},
    {'name': 'Gable Home Retail', 'sector': 'Retail', 'fy': '31 January', 'ccy': 'USD', 'segs': ['Home', 'Outdoor', 'Online'], 'scale': 8300, 'input': 'imported furniture', 'driver': 'online conversion'},
    {'name': 'Silverpine Timber', 'sector': 'Forestry', 'fy': '31 December', 'ccy': 'CAD', 'segs': ['Lumber', 'Panels', 'Land'], 'scale': 4700, 'input': 'harvesting capacity', 'driver': 'lumber prices'},
    {'name': 'Orchard Gate REIT', 'sector': 'REIT', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Retail', 'Industrial', 'Office'], 'scale': 3200, 'input': 'construction labour', 'driver': 'rent escalators'},
    {'name': 'Nimbus Data Centers', 'sector': 'Data Centers', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Colocation', 'Interconnection', 'Build-to-suit'], 'scale': 5100, 'input': 'switchgear and cooling equipment', 'driver': 'hyperscale bookings'},
    {'name': 'Aster Automotive', 'sector': 'Autos', 'fy': '31 December', 'ccy': 'EUR', 'segs': ['Vehicles', 'Parts', 'Financing'], 'scale': 21000, 'input': 'semiconductors and steel', 'driver': 'vehicle mix'},
    {'name': 'Copperline Packaging', 'sector': 'Packaging', 'fy': '31 December', 'ccy': 'USD', 'segs': ['Rigid', 'Flexible', 'Labels'], 'scale': 6400, 'input': 'aluminium and resin', 'driver': 'price pass-through'},
]
def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()
def r1(x):
    return round(x + 0.0, 1)
def tbl(headers, rows):
    out = ['| ' + ' | '.join((str(h) for h in headers)) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|']
    for row in rows:
        out.append('| ' + ' | '.join((str(v) for v in row)) + ' |')
    return '\n'.join(out)
def new_fx(kind, c, i):
    return {'key': '{}_{:02d}'.format(kind, i), 'kind': kind, 'i': i, 'company': c['name'], 'ccy': c['ccy'], 'tags': {}, 'facts': {}, 'items': {t: [] for t in ('calc', 'extraction', 'qa')}, 'ctx': ''}
def A(fx, task, q, gt, at='number', tol='abs:0.1'):
    fx['items'][task].append({'q': q, 'gt': gt, 'at': at, 'tol': tol})
def finish(c, fx, title, paras, tables, foot, units=None):
    u = units or 'Units: {} in millions unless stated otherwise, percentages in percent.'.format(c['ccy'])
    head = 'Excerpt - {}, {} (FY2025 Form 10-K).'.format(title, c['name'])
    parts = [u, head] + list(paras) + list(tables) + list(foot)
    fx['doc'] = title
    fx['ctx'] = '\n\n'.join(parts)
def b_vpm(c, fx):
    segs = c['segs']
    base = c['scale'] / float(len(segs))
    (rev24, rev25, vol, pr) = ({}, {}, {}, {})
    rows = []
    for s in segs:
        r24 = int(base * R.uniform(0.65, 1.35))
        v = R.choice([-4.2, -2.6, -1.1, 0.7, 1.9, 2.5, 3.6, 5.1, 6.3])
        p = R.choice([-1.8, -0.7, 0.4, 1.3, 2.2, 3.1, 4.4])
        r25 = int(round(r24 * (1 + v / 100.0) * (1 + p / 100.0)))
        (rev24[s], rev25[s], vol[s], pr[s]) = (r24, r25, v, p)
        rows.append([s, r25, r24, r1(v), r1(p)])
    (t24, t25) = (sum(rev24.values()), sum(rev25.values()))
    g = (t25 / float(t24) - 1) * 100
    vw = sum((rev24[s] * vol[s] for s in segs)) / float(t24)
    pw = ((1 + g / 100.0) / (1 + vw / 100.0) - 1) * 100
    rows.append(['Total', t25, t24, r1(vw), r1(pw)])
    (s0, s1, s2) = (segs[0], segs[1], segs[-1])
    sent1 = 'Consolidated revenue increased {0} percent to {1} from {2}, reflecting volume growth of {3} percent and price/mix of {4} percent.'.format(r1(g), t25, t24, r1(vw), r1(pw))
    sent2 = 'Management attributed the increase to {}.'.format(c['driver'])
    gs = dict(((s, (rev25[s] / float(rev24[s]) - 1) * 100) for s in segs))
    ps = dict(((s, ((1 + gs[s] / 100.0) / (1 + vol[s] / 100.0) - 1) * 100) for s in segs))
    for s in (s0, s1):
        A(fx, 'calc', 'What was the FY2025 revenue growth for the {} segment, in percent?'.format(s), r1(gs[s]))
        A(fx, 'calc', 'What was the implied price/mix contribution for the {} segment in FY2025, in percent?'.format(s), r1(ps[s]))
    A(fx, 'calc', 'By how much did {} revenue increase from FY2024 to FY2025, in millions?'.format(s0), rev25[s0] - rev24[s0], 'number', 'abs:1')
    A(fx, 'calc', 'What percentage of FY2025 consolidated revenue came from the {} segment?'.format(s2), r1(rev25[s2] / float(t25) * 100))
    A(fx, 'calc', 'If {} volume had been flat in FY2025, what would its revenue have been, in millions?'.format(s0), int(round(rev24[s0] * (1 + pr[s0] / 100.0))), 'number', 'abs:1')
    A(fx, 'extraction', 'What volume change is reported for the {} segment in FY2025, in percent?'.format(s0), r1(vol[s0]), 'number', 'abs:0.01')
    A(fx, 'extraction', 'What value is shown in the Price/mix column for the {} segment?'.format(s1), r1(pr[s1]), 'number', 'abs:0.01')
    A(fx, 'extraction', 'What consolidated FY2025 revenue is shown in the table, in millions?', t25, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that reports consolidated revenue growth and its volume and price/mix components.', sent1, 'text', 'exact')
    best = max(segs, key=lambda s: gs[s])
    worst = min(segs, key=lambda s: gs[s])
    A(fx, 'qa', 'Which segment reported the highest FY2025 revenue growth?', best, 'label', 'exact')
    A(fx, 'qa', 'Which segment reported the lowest FY2025 revenue growth?', worst, 'label', 'exact')
    A(fx, 'qa', 'Which segment contributed the largest dollar increase in revenue from FY2024 to FY2025?', max(segs, key=lambda s: rev25[s] - rev24[s]), 'label', 'exact')
    A(fx, 'qa', 'Did consolidated price/mix exceed volume growth in FY2025?', 'yes' if pw > vw else 'no', 'label', 'exact')
    A(fx, 'qa', 'What was the difference between the fastest and slowest growing segments in FY2025, in percentage points?', r1(gs[best] - gs[worst]))
    A(fx, 'qa', 'What was consolidated FY2025 revenue growth, in percent?', r1(g))
    A(fx, 'qa', 'How many percentage points of FY2025 revenue growth were contributed by {} volume?'.format(s0), r1(rev24[s0] * vol[s0] / float(t24)))
    fx['tags'] = {'disclosure': 'md_a', 'trend': 'growing' if g > 0 else 'declining', 'margin_driver': 'favorable' if pw > 0 else 'unfavorable'}
    fx['facts'] = {'revenue': t25, 'growth': r1(g), 'volume_growth': r1(vw), 'price_mix': r1(pw)}
    finish(c, fx, 'MD&A, revenue drivers', [sent1, sent2], [tbl(['Segment', 'FY2025 revenue', 'FY2024 revenue', 'Volume change', 'Price/mix'], rows)], ['(1) Volume change is measured on a comparable-unit basis. Price/mix includes currency.'])
def b_margin(c, fx):
    rev24 = int(c['scale'] * R.uniform(0.75, 1.25))
    g = R.choice([2.4, 4.1, 6.3, 8.2, -2.6, 11.0])
    rev25 = int(rev24 * (1 + g / 100.0))
    gm24 = R.choice([28.4, 31.2, 34.6, 38.1, 42.5])
    cg = R.choice([1.8, 3.4, 5.2, 6.1, -1.4, 9.2])
    if fx['i'] % 2 == 0 and cg >= g:
        cg = g - R.choice([1.6, 2.4, 3.1])
    if fx['i'] % 2 == 1 and cg <= g:
        cg = g + R.choice([1.7, 2.9, 4.2])
    cogs24 = int(rev24 * (1 - gm24 / 100.0))
    cogs25 = int(cogs24 * (1 + cg / 100.0))
    (gp25, gp24) = (rev25 - cogs25, rev24 - cogs24)
    gm25 = gp25 / float(rev25) * 100
    gmp = (gp25 / float(gp24) - 1) * 100
    inc = (gp25 - gp24) / float(rev25 - rev24) * 100
    up = gm25 > gm24
    driver = R.choice(['pricing actions', 'a favourable product mix', 'lower input costs']) if up else R.choice(['input cost inflation', 'higher freight and logistics costs', 'an unfavourable product mix'])
    sent1 = 'Gross margin was {0} percent in FY2025 compared with {1} percent in FY2024, primarily reflecting {2}.'.format(r1(gm25), r1(gm24), driver)
    sent2 = 'Revenue {} {} percent while cost of revenue {} {} percent.'.format('increased' if g > 0 else 'decreased', r1(abs(g)), 'increased' if cg > 0 else 'decreased', r1(abs(cg)))
    A(fx, 'calc', 'What was the FY2025 gross margin, in percent?', r1(gm25))
    A(fx, 'calc', 'What gross margin was reported for FY2024, in percent?', r1(gm24))
    A(fx, 'calc', 'By how many basis points did the gross margin change from FY2024 to FY2025?', int(round((gm25 - gm24) * 100)), 'number', 'abs:1')
    A(fx, 'calc', 'What was cost of revenue as a percentage of revenue in FY2025?', r1(cogs25 / float(rev25) * 100))
    A(fx, 'calc', 'What was gross profit growth in FY2025, in percent?', r1(gmp))
    A(fx, 'calc', 'What was the incremental gross margin in FY2025, in percent?', r1(inc))
    A(fx, 'extraction', 'What was cost of revenue in FY2025, in millions?', cogs25, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What was gross profit in FY2024, in millions?', gp24, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that explains the change in gross margin.', sent1, 'text', 'exact')
    A(fx, 'extraction', 'What was revenue in FY2025, in millions?', rev25, 'number', 'abs:0.01')
    A(fx, 'qa', 'Which factor does management cite as the primary driver of the FY2025 gross margin change?', driver.rstrip('.'), 'text', 'normalized')
    A(fx, 'qa', 'Did gross margin expand or contract in FY2025?', 'expand' if up else 'contract', 'label', 'exact')
    A(fx, 'qa', 'By how much did gross profit change in dollars, in millions?', gp25 - gp24, 'number', 'abs:1')
    A(fx, 'qa', 'What was the gross margin on the incremental revenue in FY2025, in percent?', r1(inc))
    A(fx, 'qa', 'Which grew faster in FY2025, revenue or cost of revenue?', 'revenue' if g > cg else 'cost of revenue', 'label', 'exact')
    A(fx, 'qa', 'If cost of revenue had grown at the same rate as revenue, what would FY2025 gross margin have been, in percent?', r1((rev25 - cogs24 * (1 + g / 100.0)) / float(rev25) * 100))
    fx['tags'] = {'disclosure': 'md_a', 'trend': 'growing' if g > 0 else 'declining', 'margin_driver': 'favorable' if up else 'unfavorable'}
    fx['facts'] = {'revenue': rev25, 'gross_profit': gp25, 'gross_margin': r1(gm25), 'cost_of_revenue': cogs25}
    finish(c, fx, 'MD&A, gross margin bridge', [sent1, sent2], [tbl(['Item', 'FY2025', 'FY2024'], [['Revenue', rev25, rev24], ['Cost of revenue', cogs25, cogs24], ['Gross profit', gp25, gp24]])], ['(1) Cost of revenue includes inbound freight and tariffs.'])
def b_revdis(c, fx):
    geos = ['Americas', 'EMEA', 'APAC']
    (rev25, rev24) = ({}, {})
    rows = []
    for g in geos:
        a = int(c['scale'] * R.uniform(0.12, 0.45))
        gr = R.choice([-6.2, -2.4, 0.8, 3.1, 5.6, 9.4, 12.1])
        b = int(round(a / (1 + gr / 100.0)))
        (rev25[g], rev24[g]) = (a, b)
        rows.append([g, a, b])
    (t25, t24) = (sum(rev25.values()), sum(rev24.values()))
    rows.append(['Total', t25, t24])
    pit = int(t25 * (0.62 if fx['i'] % 2 == 0 else 0.41))
    over = t25 - pit
    if fx['i'] % 4 < 2:
        trows = [['Point in time', ''], ['Over time', over], ['Total', t25]]
        blank_gt = pit
        blank_name = 'Point in time'
    else:
        trows = [['Point in time', pit], ['Over time', ''], ['Total', t25]]
        blank_gt = over
        blank_name = 'Over time'
    s1 = 'Revenue was disaggregated by geography and by timing of transfer. No single customer represented more than 10 percent of consolidated revenue in FY2025.'
    s2 = 'The largest geographic market was {}, representing {} percent of FY2025 revenue.'.format(max(geos, key=lambda x: rev25[x]), r1(rev25[max(geos, key=lambda x: rev25[x])] / float(t25) * 100))
    for g in (geos[1], geos[2]):
        A(fx, 'calc', 'What was the FY2025 revenue growth in the {} region, in percent?'.format(g), r1((rev25[g] / float(rev24[g]) - 1) * 100))
        A(fx, 'calc', 'What share of FY2025 revenue came from {}?'.format(g), r1(rev25[g] / float(t25) * 100))
    A(fx, 'calc', 'What value completes the blank cell for {} in the timing table, in millions?'.format(blank_name), blank_gt, 'number', 'abs:1')
    A(fx, 'calc', 'What was the dollar change in Americas revenue from FY2024 to FY2025, in millions?', rev25['Americas'] - rev24['Americas'], 'number', 'abs:1')
    A(fx, 'extraction', 'What FY2024 revenue is reported for EMEA, in millions?', rev24['EMEA'], 'number', 'abs:0.01')
    A(fx, 'extraction', 'What FY2025 revenue is reported for APAC, in millions?', rev25['APAC'], 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that states the customer concentration conclusion.', s1, 'text', 'exact')
    A(fx, 'extraction', 'Which cell is left blank in the timing-of-transfer table?', blank_name, 'text', 'normalized')
    A(fx, 'extraction', 'What total FY2025 revenue is shown in the geographic table, in millions?', t25, 'number', 'abs:0.01')
    A(fx, 'qa', 'Which geography grew fastest in FY2025?', max(geos, key=lambda x: rev25[x] / float(rev24[x])), 'label', 'exact')
    A(fx, 'qa', 'Which geography was the largest source of FY2025 revenue?', max(geos, key=lambda x: rev25[x]), 'label', 'exact')
    A(fx, 'qa', 'Was more than half of FY2025 revenue recognised over time?', 'yes' if over > t25 / 2.0 else 'no', 'label', 'exact')
    A(fx, 'qa', 'What percentage of FY2025 revenue was recognised at a point in time?', r1(pit / float(t25) * 100))
    A(fx, 'qa', 'By how much did total revenue change from FY2024 to FY2025, in millions?', t25 - t24, 'number', 'abs:1')
    top2 = sorted(geos, key=lambda x: -rev25[x])[:2]
    A(fx, 'qa', 'Which two geographies account for the largest share of FY2025 revenue?', top2[0] + ' and ' + top2[1], 'text', 'normalized')
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing' if t25 > t24 else 'declining', 'revrec': 'point_in_time' if pit > over else 'over_time'}
    fx['facts'] = {'revenue': t25, 'americas': rev25['Americas'], 'emea': rev25['EMEA'], 'apac': rev25['APAC']}
    finish(c, fx, 'Note 4, revenue disaggregation', [s1, s2], [tbl(['Geography', 'FY2025', 'FY2024'], rows), tbl(['Timing of transfer', 'FY2025'], trows)], ['(1) FY2024 amounts include a divested product line with revenue of 118.'])
def b_lease(c, fx):
    years = ['FY2026', 'FY2027', 'FY2028', 'FY2029', 'FY2030', 'Thereafter']
    amts = []
    base = c['scale'] * 0.014
    for (i, y) in enumerate(years[:-1]):
        amts.append(int(base * 1.06 ** (-i) * R.uniform(0.9, 1.1)))
    amts.append(int(base * R.uniform(2.4, 3.8)))
    total = sum(amts)
    pv = int(total * R.uniform(0.78, 0.9))
    rate = R.choice([4.6, 4.9, 5.2, 5.6, 6.1])
    term = R.choice([7.4, 8.1, 9.3, 10.6])
    rows = [[y, a] for (y, a) in zip(years, amts)]
    rows.append(['Total', total])
    s1 = 'Operating lease liabilities of {} were measured using a weighted-average discount rate of {} percent and a weighted-average remaining lease term of {} years.'.format(pv, rate, term)
    s2 = 'The maturities of operating lease payments are presented on an undiscounted basis.'
    first2 = amts[0] + amts[1]
    A(fx, 'calc', 'What is the total of the undiscounted operating lease payments, in millions?', total, 'number', 'abs:1')
    A(fx, 'calc', 'What percentage of undiscounted lease payments falls due in FY2026 and FY2027 combined?', r1(first2 / float(total) * 100))
    A(fx, 'calc', 'What percentage of undiscounted lease payments falls due after FY2030?', r1(amts[-1] / float(total) * 100))
    A(fx, 'calc', 'How much larger are undiscounted payments than the recorded lease liability, in millions?', total - pv, 'number', 'abs:1')
    A(fx, 'calc', 'What is the ratio of the recorded lease liability to total undiscounted payments, in percent?', r1(pv / float(total) * 100))
    A(fx, 'extraction', 'What discount rate is disclosed for the lease liability, in percent?', rate, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What is the weighted-average remaining lease term, in years?', term, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What payment is due in FY2026, in millions?', amts[0], 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that gives the discount rate and remaining term.', s1, 'text', 'exact')
    A(fx, 'qa', 'Are the lease payments in the maturity table presented on a discounted or undiscounted basis?', 'undiscounted', 'label', 'exact')
    A(fx, 'qa', 'Which year has the largest single operating lease payment?', years[amts.index(max(amts))], 'label', 'exact')
    A(fx, 'qa', 'What is the recorded operating lease liability, in millions?', pv, 'number', 'abs:1')
    A(fx, 'qa', 'Do payments due after FY2030 exceed those due in FY2026 through FY2030 combined?', 'yes' if amts[-1] > sum(amts[:-1]) else 'no', 'label', 'exact')
    A(fx, 'qa', 'What is the average annual payment over FY2026 to FY2030, in millions?', int(round(sum(amts[:-1]) / 5.0)), 'number', 'abs:1')
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing'}
    fx['facts'] = {'total_lease': total, 'lease_liability': pv, 'first_year_payment': amts[0]}
    finish(c, fx, 'Note 11, leases', [s1, s2], [tbl(['Fiscal year', 'Operating lease payments'], rows)], ['(1) Excludes short-term leases and variable payments.'])
def b_debt(c, fx):
    names = ['Term loan B', 'Senior secured notes', 'Revolving credit facility']
    prin = [int(c['scale'] * 0.18), int(c['scale'] * 0.12), int(c['scale'] * 0.05)]
    coup = [R.choice([5.1, 5.4, 5.9]), R.choice([6.1, 6.4, 6.8]), R.choice([4.6, 4.9])]
    mats = [2029, 2031, 2028]
    rows = [[n, p, cp, m] for (n, p, cp, m) in zip(names, prin, coup, mats)]
    total = sum(prin)
    cash = int(total * R.uniform(0.08, 0.2))
    ebitda = int(total / R.uniform(2.4, 3.4))
    net = total - cash
    lev = net / float(ebitda)
    cov = 3.5 if fx['i'] % 2 == 0 else 4.0
    if fx['i'] % 2 == 0:
        cov = r1(lev + R.uniform(0.4, 0.9))
    else:
        cov = r1(max(1.25, lev - R.uniform(0.3, 0.6)))
    wa = sum((p * cp for (p, cp) in zip(prin, coup))) / float(total)
    interest = sum((p * cp / 100.0 for (p, cp) in zip(prin, coup)))
    s1 = 'The credit agreement requires net leverage not to exceed {} times consolidated EBITDA. At year end, net leverage was {} times EBITDA of {}.'.format(cov, r1(lev), ebitda)
    commit = int(prin[2] + max(150, c['scale'] * 0.02))
    s2 = 'The revolving credit facility provides total commitments of {}, of which {} was undrawn.'.format(commit, commit - prin[2])
    A(fx, 'calc', 'What is total debt principal outstanding, in millions?', total, 'number', 'abs:1')
    A(fx, 'calc', 'What is the weighted-average coupon on total debt, in percent?', r1(wa), 'number', 'abs:0.1')
    A(fx, 'calc', 'What is annual cash interest expense on the debt, in millions?', int(round(interest)), 'number', 'abs:1')
    A(fx, 'calc', 'By how much does net leverage headroom to the covenant stand, in turns?', r1(cov - lev), 'number', 'abs:0.1')
    A(fx, 'calc', 'What is the undrawn revolver availability, in millions?', commit - prin[2], 'number', 'abs:1')
    A(fx, 'extraction', 'What is the maturity year of the senior secured notes?', mats[1], 'number', 'abs:0.01')
    A(fx, 'extraction', 'What is the coupon on the term loan B, in percent?', coup[0], 'number', 'abs:0.01')
    A(fx, 'extraction', 'What is the principal of the revolving credit facility, in millions?', prin[2], 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that states the leverage covenant and the actual leverage ratio.', s1, 'text', 'exact')
    A(fx, 'qa', 'Is the company compliant with its leverage covenant?', 'compliant' if lev <= cov else 'breach', 'label', 'exact')
    A(fx, 'qa', 'Which instrument matures first?', names[mats.index(min(mats))], 'label', 'exact')
    A(fx, 'qa', 'Which instrument carries the highest coupon?', names[coup.index(max(coup))], 'label', 'exact')
    A(fx, 'qa', 'What is consolidated EBITDA, in millions?', ebitda, 'number', 'abs:1')
    A(fx, 'qa', 'What is net debt, in millions?', net, 'number', 'abs:1')
    A(fx, 'qa', 'What percentage of total principal is secured by the term loan B?', r1(prin[0] / float(total) * 100))
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing', 'covenant': 'compliant' if lev <= cov else 'breach'}
    fx['facts'] = {'total_debt': total, 'ebitda': ebitda, 'net_leverage': r1(lev), 'covenant': cov}
    finish(c, fx, 'Note 9, debt', [s1, s2], [tbl(['Instrument', 'Principal', 'Coupon', 'Maturity'], rows)], ['(1) The term loan B amortises at 1 percent of original principal per year.'])
def b_segment(c, fx):
    segs = c['segs']
    (rev, oi, da, capex, assets) = ({}, {}, {}, {}, {})
    rows = []
    for s in segs:
        rev[s] = int(c['scale'] / float(len(segs)) * R.uniform(0.7, 1.3))
        oi[s] = int(rev[s] * R.uniform(0.06, 0.22))
        da[s] = int(rev[s] * R.uniform(0.03, 0.07))
        capex[s] = int(rev[s] * R.uniform(0.03, 0.09))
        assets[s] = int(rev[s] * R.uniform(0.8, 1.6))
        rows.append([s, rev[s], oi[s], da[s], capex[s], assets[s]])
    (tr, to) = (sum(rev.values()), sum(oi.values()))
    rows.append(['Total', tr, to, sum(da.values()), sum(capex.values()), sum(assets.values())])
    best = max(segs, key=lambda s: oi[s] / float(rev[s]))
    s1 = 'Segment operating income is presented before corporate costs of {}. Segment results include intersegment sales, which are eliminated in consolidation.'.format(int(c['scale'] * 0.01))
    s2 = 'The {} segment generated the highest operating margin at {} percent.'.format(best, r1(oi[best] / float(rev[best]) * 100))
    for s in segs[:2]:
        A(fx, 'calc', 'What was the {} segment operating margin in FY2025, in percent?'.format(s), r1(oi[s] / float(rev[s]) * 100))
        A(fx, 'calc', 'What was the {} segment capital expenditure as a percentage of revenue?'.format(s), r1(capex[s] / float(rev[s]) * 100))
    A(fx, 'calc', 'What was the {} segment EBITDA, in millions?'.format(segs[0]), oi[segs[0]] + da[segs[0]], 'number', 'abs:1')
    A(fx, 'calc', 'What was the group operating margin in FY2025, in percent?', r1(to / float(tr) * 100))
    A(fx, 'calc', 'What were total capital expenditures, in millions?', sum(capex.values()), 'number', 'abs:1')
    A(fx, 'extraction', 'What revenue is reported for the {} segment, in millions?'.format(segs[1]), rev[segs[1]], 'number', 'abs:0.01')
    A(fx, 'extraction', 'What depreciation and amortization is reported for the {} segment, in millions?'.format(segs[0]), da[segs[0]], 'number', 'abs:0.01')
    A(fx, 'extraction', 'What total assets are reported for the {} segment, in millions?'.format(segs[-1]), assets[segs[-1]], 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that identifies the highest-margin segment and its margin.', s2, 'text', 'exact')
    A(fx, 'qa', 'Which segment has the highest operating margin?', max(segs, key=lambda s: oi[s] / float(rev[s])), 'label', 'exact')
    A(fx, 'qa', 'Which segment has the highest capital expenditure intensity?', max(segs, key=lambda s: capex[s] / float(rev[s])), 'label', 'exact')
    A(fx, 'qa', 'Which segment generates the most operating income?', max(segs, key=lambda s: oi[s]), 'label', 'exact')
    A(fx, 'qa', 'Do segment revenues sum to total revenue?', 'yes', 'label', 'exact')
    A(fx, 'qa', 'What share of group operating income comes from the {} segment?'.format(best), r1(oi[best] / float(to) * 100))
    A(fx, 'qa', 'What is the ratio of capital expenditures to depreciation and amortization for the group?', r1(sum(capex.values()) / float(sum(da.values())) * 100))
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing', 'margin_driver': 'favorable' if oi[best] / float(rev[best]) > 0.12 else 'unfavorable'}
    fx['facts'] = {'revenue': tr, 'operating_income': to, 'operating_margin': r1(to / float(tr) * 100)}
    finish(c, fx, 'Note 15, segment information', [s1, s2], [tbl(['Segment', 'Revenue', 'Operating income', 'Depreciation and amortization', 'Capital expenditures', 'Total assets'], rows)], ['(1) Segment assets exclude deferred tax assets and cash.'])
def b_restate(c, fx):
    rev_p = int(c['scale'] * R.uniform(0.6, 1.1))
    kind = 'error' if fx['i'] % 2 == 0 else 'reclass'
    if kind == 'error':
        adj = int(rev_p * R.choice([0.012, 0.021, 0.034, -0.018]))
        adj2 = int(abs(adj) * R.uniform(0.3, 0.8)) * (1 if adj > 0 else -1)
    else:
        adj = -int(rev_p * R.choice([0.018, 0.026, 0.041]))
        adj2 = adj
    rev_r = rev_p + adj
    cogs_p = int(rev_p * R.uniform(0.55, 0.7))
    cogs_r = cogs_p + adj2
    (gp_p, gp_r) = (rev_p - cogs_p, rev_r - cogs_r)
    g = R.choice([0.02, 0.045, 0.061, -0.015])
    rev25 = int(rev_r * (1 + g))
    cogs25 = int(cogs_r * (1 + g * 0.8))
    gp25 = rev25 - cogs25
    if kind == 'error':
        s1 = 'The restatement corrects an error in the timing of revenue recognition identified during the FY2025 close. The correction {} FY2024 revenue by {} and {} FY2024 cost of revenue by {}.'.format('increased' if adj > 0 else 'decreased', abs(adj), 'increased' if adj2 > 0 else 'decreased', abs(adj2))
    else:
        s1 = 'The restatement reclassifies certain pass-through freight revenue from gross to net presentation. The reclassification reduced FY2024 revenue by {} and reduced FY2024 cost of revenue by the same amount, leaving gross profit unchanged.'.format(abs(adj))
    s2 = 'FY2024 amounts as restated are presented in the table below.'
    trows = [['Revenue', rev25, rev_p, rev_r], ['Cost of revenue', cogs25, cogs_p, ''], ['Gross profit', gp25, gp_p, gp_r]]
    A(fx, 'calc', 'By how much did the restatement change FY2024 revenue, in millions?', adj, 'number', 'abs:1')
    A(fx, 'calc', 'What was the restatement impact on FY2024 revenue, in percent?', r1(adj / float(rev_p) * 100))
    A(fx, 'calc', 'What was FY2024 gross margin as restated, in percent?', r1(gp_r / float(rev_r) * 100))
    A(fx, 'calc', 'What was FY2024 gross margin as previously reported, in percent?', r1(gp_p / float(rev_p) * 100))
    A(fx, 'calc', 'What value completes the blank cell for FY2024 cost of revenue as restated, in millions?', cogs_r, 'number', 'abs:1')
    A(fx, 'calc', 'What was the FY2025 gross margin, in percent?', r1(gp25 / float(rev25) * 100))
    A(fx, 'extraction', 'What was FY2024 revenue as previously reported, in millions?', rev_p, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What was FY2024 revenue as restated, in millions?', rev_r, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What was FY2025 gross profit, in millions?', gp25, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that explains why the restatement was made.', s1, 'text', 'exact')
    A(fx, 'extraction', 'Which FY2024 column contains the blank cell?', 'FY2024 as restated', 'text', 'normalized')
    A(fx, 'qa', 'Does the restatement increase, decrease or leave unchanged FY2024 gross profit?', 'increase' if gp_r > gp_p else ('decrease' if gp_r < gp_p else 'unchanged'), 'label', 'exact')
    _chg = {'Revenue': abs(adj), 'Cost of revenue': abs(adj2), 'Gross profit': abs(gp_r - gp_p)}
    A(fx, 'qa', 'Which line item changed by the largest dollar amount between the previously reported and restated columns?', max(_chg, key=lambda k: _chg[k]), 'label', 'exact')
    A(fx, 'qa', 'Is the restatement an error correction or a reclassification?', 'error correction' if kind == 'error' else 'reclassification', 'label', 'exact')
    A(fx, 'qa', 'What was FY2024 gross profit as previously reported, in millions?', gp_p, 'number', 'abs:1')
    A(fx, 'qa', 'What was the change in FY2024 cost of revenue, in millions?', adj2, 'number', 'abs:1')
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing', 'restatement': 'error_correction' if kind == 'error' else 'reclassification'}
    fx['facts'] = {'revenue_restated': rev_r, 'revenue_prior': rev_p, 'restatement_impact': adj}
    finish(c, fx, 'Note 2, restatement of previously issued financial statements', [s1, s2], [tbl(['Line item', 'FY2025', 'FY2024 as previously reported', 'FY2024 as restated'], trows)], ['(1) The restatement had no effect on cash flows from operating activities.'])
def b_cash(c, fx):
    cfo = int(c['scale'] * R.uniform(0.07, 0.16))
    capex = int(cfo * R.uniform(0.35, 0.7))
    fcf = cfo - capex
    div = int(fcf * (0.55 if fx['i'] % 2 == 0 else 1.25))
    buy = int(max(0, fcf - div) * 0.5)
    net = fcf - div - buy
    rows = [['Net cash from operating activities', cfo], ['Capital expenditures', -capex], ['Free cash flow', fcf], ['Dividends paid', -div], ['Share repurchases', -buy], ['Net change in cash', net]]
    s1 = 'Free cash flow is defined as net cash from operating activities less capital expenditures. The revolving credit facility had {} available at year end.'.format(int(c['scale'] * 0.05) + max(150, int(c['scale'] * 0.02)))
    s2 = 'The company returned {} to shareholders through dividends and repurchases.'.format(div + buy)
    A(fx, 'calc', 'What was free cash flow, in millions?', fcf, 'number', 'abs:1')
    A(fx, 'calc', 'What was free cash flow conversion from operating cash flow, in percent?', r1(fcf / float(cfo) * 100))
    A(fx, 'calc', 'What was the dividend payout ratio against free cash flow, in percent?', r1(div / float(fcf) * 100))
    A(fx, 'calc', 'What were capital expenditures as a percentage of operating cash flow?', r1(capex / float(cfo) * 100))
    A(fx, 'calc', 'What was the net change in cash, in millions?', net, 'number', 'abs:1')
    A(fx, 'extraction', 'What were capital expenditures, in millions?', capex, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What were dividends paid, in millions?', div, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What was net cash from operating activities, in millions?', cfo, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that defines free cash flow and gives revolver availability.', s1, 'text', 'exact')
    A(fx, 'qa', 'Did free cash flow cover dividends in FY2025?', 'yes' if fcf >= div else 'no', 'label', 'exact')
    A(fx, 'qa', 'Was free cash flow positive in FY2025?', 'yes' if fcf > 0 else 'no', 'label', 'exact')
    A(fx, 'qa', 'What percentage of free cash flow was returned through dividends and repurchases?', r1((div + buy) / float(fcf) * 100))
    A(fx, 'qa', 'Which uses more cash: dividends or share repurchases?', 'dividends' if div >= buy else 'share repurchases', 'label', 'exact')
    A(fx, 'qa', 'What is free cash flow after dividends and repurchases, in millions?', net, 'number', 'abs:1')
    fx['tags'] = {'disclosure': 'md_a', 'trend': 'growing', 'liquidity': 'sufficient' if fcf >= div else 'insufficient', 'capital': ['dividend', 'buyback', 'debt_repayment'][fx['i'] % 3]}
    fx['facts'] = {'cfo': cfo, 'capex': capex, 'fcf': fcf, 'dividends': div}
    finish(c, fx, 'MD&A, liquidity and capital resources', [s1, s2], [tbl(['Item', 'FY2025'], rows)], ['(1) Free cash flow is a non-GAAP measure and may not be comparable to other issuers.'])
def b_tax(c, fx):
    stat = 21.0
    state = R.choice([1.8, 2.4, 3.1])
    foreign = R.choice([-2.4, -1.8, -1.1, 0.9])
    va = R.choice([0.0, 1.2, 2.6, 3.1]) if fx['i'] % 2 == 0 else R.choice([-1.4, -0.9, 0.0])
    other = R.choice([-0.6, -0.3, 0.4, 0.7])
    etr = r1(stat + state + foreign + va + other)
    pretax = int(c['scale'] * R.uniform(0.05, 0.11))
    taxexp = int(round(pretax * etr / 100.0))
    rows = [['Statutory federal rate', stat], ['State and local taxes, net of federal benefit', state], ['Foreign rate differential', foreign], ['Valuation allowance', va], ['Other, net', other], ['Effective tax rate', etr]]
    s1 = 'The effective tax rate was {} percent in FY2025, compared with the statutory federal rate of {} percent. Income before income taxes was {}.'.format(etr, stat, pretax)
    s2 = 'The valuation allowance relates to net operating losses in certain foreign jurisdictions.'
    A(fx, 'calc', 'What was the effective tax rate, in percent?', etr)
    A(fx, 'calc', 'What was income tax expense, in millions?', taxexp, 'number', 'abs:1')
    A(fx, 'calc', 'What would the effective tax rate have been excluding the valuation allowance, in percent?', r1(etr - va))
    A(fx, 'calc', 'What is the sum of the reconciling items other than the statutory rate, in percentage points?', r1(etr - stat))
    A(fx, 'calc', 'What is the dollar impact of the valuation allowance on tax expense, in millions?', int(round(pretax * va / 100.0)), 'number', 'abs:1')
    A(fx, 'extraction', 'What statutory federal rate is used in the reconciliation, in percent?', stat, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What valuation allowance is reported, in percent?', va, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What foreign rate differential is reported, in percent?', foreign, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that gives the effective and statutory rates.', s1, 'text', 'exact')
    A(fx, 'qa', 'Is the effective tax rate above or below the statutory rate?', 'above' if etr > stat else 'below', 'label', 'exact')
    A(fx, 'qa', 'Which reconciling item has the largest absolute impact on the effective tax rate?', max([('State and local taxes', abs(state)), ('Foreign rate differential', abs(foreign)), ('Valuation allowance', abs(va)), ('Other, net', abs(other))], key=lambda x: x[1])[0], 'text', 'normalized')
    A(fx, 'qa', 'What is income before income taxes, in millions?', pretax, 'number', 'abs:1')
    A(fx, 'qa', 'Does the valuation allowance increase or reduce the effective tax rate?', 'increase' if va > 0 else 'reduce' if va < 0 else 'no effect', 'label', 'exact')
    A(fx, 'qa', 'What is the total of state and local taxes and the foreign rate differential, in percentage points?', r1(state + foreign))
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing', 'tax': 'rate_reconciliation' if fx['i'] % 2 == 0 else 'deferred_tax'}
    fx['facts'] = {'effective_tax_rate': etr, 'pretax_income': pretax, 'tax_expense': taxexp}
    finish(c, fx, 'Note 13, income taxes', [s1, s2], [tbl(['Reconciliation item', 'Rate'], rows)], ['(1) The reconciliation is presented as a percentage of income before income taxes.'])
def b_goodwill(c, fx):
    units = c['segs'][:3]
    rows = []
    total_imp = 0
    (carry, fair) = ({}, {})
    for (i, u) in enumerate(units):
        cv = int(c['scale'] / 3.0 * R.uniform(0.6, 1.3))
        imp = 0
        if fx['i'] % 2 == 0 and i == fx['i'] % len(units):
            fv = int(cv * R.uniform(0.62, 0.86))
            imp = cv - fv
        else:
            fv = int(cv * R.uniform(1.05, 1.5))
        (carry[u], fair[u]) = (cv, fv)
        total_imp += imp
        rows.append([u, cv, fv, imp])
    s1 = 'Goodwill of {} is tested for impairment annually. An impairment charge of {} was recognised in FY2025 in the {} reporting unit.'.format(sum(carry.values()), total_imp, units[fx['i'] % len(units)])
    s2 = 'Fair value of each reporting unit was estimated using a discounted cash flow model.'
    unit = units[fx['i'] % len(units)]
    head = (fair[unit] / float(carry[unit]) - 1) * 100
    A(fx, 'calc', 'What was the total goodwill impairment charge, in millions?', total_imp, 'number', 'abs:1')
    A(fx, 'calc', 'What was the fair value headroom of the {} reporting unit, in percent?'.format(unit), r1(head))
    A(fx, 'calc', 'What is the carrying value of the {} reporting unit after impairment, in millions?'.format(unit), carry[unit] - (carry[unit] - fair[unit] if fair[unit] < carry[unit] else 0), 'number', 'abs:1')
    A(fx, 'calc', 'What percentage of total carrying value does the {} reporting unit represent?'.format(unit), r1(carry[unit] / float(sum(carry.values())) * 100))
    A(fx, 'extraction', 'What impairment charge is reported for the {} reporting unit, in millions?'.format(unit), max(0, carry[unit] - fair[unit]), 'number', 'abs:0.01')
    A(fx, 'extraction', 'What fair value is reported for the {} reporting unit, in millions?'.format(units[0]), fair[units[0]], 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that states the impairment charge and the affected unit.', s1, 'text', 'exact')
    A(fx, 'extraction', 'What total goodwill is subject to the annual impairment test, in millions?', sum(carry.values()), 'number', 'abs:0.01')
    A(fx, 'qa', 'Which reporting unit recorded an impairment charge?', unit if total_imp > 0 else 'none', 'label', 'exact')
    A(fx, 'qa', 'Was any reporting unit impaired in FY2025?', 'yes' if total_imp > 0 else 'no', 'label', 'exact')
    A(fx, 'qa', 'Which reporting unit has the smallest fair value headroom?', min(units, key=lambda u: fair[u] / float(carry[u])), 'label', 'exact')
    A(fx, 'qa', 'Do the fair values of all reporting units exceed their carrying values?', 'yes' if all((fair[u] >= carry[u] for u in units)) else 'no', 'label', 'exact')
    A(fx, 'qa', 'What is the aggregate fair value of the reporting units, in millions?', sum(fair.values()), 'number', 'abs:1')
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'declining', 'impairment': 'impairment_recognized' if total_imp > 0 else 'no_impairment'}
    fx['facts'] = {'impairment': total_imp, 'goodwill': sum(carry.values())}
    finish(c, fx, 'Note 8, goodwill and intangible assets', [s1, s2], [tbl(['Reporting unit', 'Carrying value', 'Fair value', 'Impairment charge'], rows)], ['(1) Carrying value includes allocated goodwill and indefinite-lived intangibles.'])
def b_risk(c, fx):
    conc = [28, 34, 41, 47, 53][fx['i'] % 5]
    bps = [120, 180, 240, 310][fx['i'] % 4]
    mit = ['dual sourcing and long-term supply agreements', 'financial hedging and fixed-price contracts', 'regulatory monitoring and compliance reviews'][fx['i'] % 3]
    tag = ['dual_sourcing', 'financial_hedging', 'regulatory_compliance'][fx['i'] % 3]
    s1 = 'We depend on a limited number of suppliers for {}.'.format(c['input'])
    s2 = 'In FY2025, {} percent of purchases were concentrated among three suppliers, and a disruption could reduce gross margin by up to {} basis points.'.format(conc, bps)
    s3 = 'We mitigate this exposure through {}.'.format(mit)
    A(fx, 'extraction', 'What percentage of purchases came from three suppliers in FY2025, in percent?', conc, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What is the stated maximum gross margin impact of a supply disruption, in basis points?', bps, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that describes the mitigants for this risk.', s3, 'text', 'exact')
    A(fx, 'extraction', 'Quote the sentence that quantifies supplier concentration.', s2, 'text', 'exact')
    A(fx, 'qa', 'How many suppliers account for the stated concentration?', 3, 'number', 'abs:0.01')
    A(fx, 'qa', 'What mitigants does the company cite for supplier concentration?', mit, 'text', 'normalized')
    A(fx, 'qa', 'Is supplier concentration above or below 40 percent?', 'above' if conc > 40 else 'below', 'label', 'exact')
    A(fx, 'qa', 'Which input is subject to supplier concentration?', c['input'], 'text', 'normalized')
    fx['tags'] = {'disclosure': 'risk_factor', 'trend': 'growing', 'mitigant': tag}
    fx['facts'] = {'supplier_concentration': conc, 'margin_bps': bps}
    finish(c, fx, 'Item 1A, risk factors', [s1, s2, s3], [], ['(1) Purchase concentration is measured on a rolling twelve-month basis.'])
def b_legal(c, fx):
    acc = int(c['scale'] * 0.004)
    maxl = acc + int(c['scale'] * R.uniform(0.006, 0.014))
    other = int(c['scale'] * 0.001)
    if fx['i'] % 2 == 0:
        s1 = 'In FY2025, a customer filed a claim alleging defects in delivered product. We have accrued {} for this matter and believe a loss of up to {} is reasonably possible in excess of the amount accrued.'.format(acc, maxl)
        tag = 'yes'
    else:
        s1 = 'In FY2025, a customer filed a claim alleging defects in delivered product. We have not recorded an accrual because a loss is not probable, and we believe a loss of up to {} is reasonably possible.'.format(maxl)
        tag = 'no'
    s2 = 'Separately, {} other matters are pending for which an aggregate accrual of {} is recorded.'.format(3, other)
    A(fx, 'calc', 'What is the maximum incremental exposure above the amount accrued, in millions?', maxl - acc, 'number', 'abs:1')
    A(fx, 'calc', 'What is the total amount accrued for legal matters, in millions?', acc + other, 'number', 'abs:1')
    A(fx, 'extraction', 'What amount has been accrued for the customer claim, in millions?', acc, 'number', 'abs:0.01')
    A(fx, 'extraction', 'What is the maximum reasonably possible loss, in millions?', maxl, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that states the range of reasonably possible loss.', s1, 'text', 'exact')
    A(fx, 'qa', 'Is a loss accrual recognised for the customer claim?', tag, 'label', 'exact')
    A(fx, 'qa', 'How many other legal matters are pending?', 3, 'number', 'abs:0.01')
    A(fx, 'qa', 'What is the aggregate accrual for other legal matters, in millions?', other, 'number', 'abs:1')
    A(fx, 'qa', 'Does the disclosure state that the outcome of the claim is probable or only reasonably possible?', 'probable' if tag == 'yes' else 'reasonably possible', 'text', 'normalized')
    fx['tags'] = {'disclosure': 'footnote', 'trend': 'growing'}
    fx['facts'] = {'accrual': acc, 'maximum_loss': maxl}
    finish(c, fx, 'Note 17, commitments and contingencies', [s1, s2], [], ['(1) Legal costs are expensed as incurred.'])
def b_subseq(c, fx):
    amt = int(c['scale'] * R.uniform(0.04, 0.09))
    ebitda = int(amt / R.uniform(6.0, 11.0))
    div = round(R.uniform(0.18, 0.62), 2)
    shares = int(c['scale'] * R.uniform(0.03, 0.07))
    dt = ['15 January 2026', '22 January 2026', '3 February 2026'][fx['i'] % 3]
    if fx['i'] % 2 == 0:
        ev = 'acquisition'
        s1 = 'On {}, the company acquired all of the equity of a regional operator for consideration of {}, funded with borrowings under the revolving credit facility.'.format(dt, amt)
        s2 = 'The acquired business generated EBITDA of {} in its most recent fiscal year.'.format(ebitda)
        tag = 'nonrecognized'
    else:
        ev = 'customer_insolvency'
        s1 = "On {}, a customer representing {} of trade receivables filed for insolvency. The customer's financial condition existed at the balance sheet date, and an additional allowance of {} was recorded.".format(dt, int(amt * 0.2), int(amt * 0.12))
        s2 = 'The adjustment was recognised in the FY2025 financial statements.'
        tag = 'recognized'
    s3 = 'On {} the board declared a quarterly dividend of {} per share. The company had {} million shares outstanding at year end.'.format(dt, div, shares)
    A(fx, 'calc', 'What is the total quarterly dividend payment, in millions?', int(round(div * shares)), 'number', 'abs:1')
    A(fx, 'calc', 'What is the annualised dividend cost, in millions?', int(round(div * shares * 4)), 'number', 'abs:1')
    A(fx, 'extraction', 'On what date did the subsequent event occur?', dt, 'text', 'normalized')
    A(fx, 'extraction', 'What dividend per share was declared?', div, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that describes the primary subsequent event.', s1, 'text', 'exact')
    A(fx, 'extraction', 'How many shares were outstanding at year end, in millions?', shares, 'number', 'abs:0.01')
    A(fx, 'qa', 'Is the subsequent event recognised or non-recognised in the FY2025 financial statements?', tag, 'label', 'exact')
    A(fx, 'qa', 'Which type of subsequent event is described: acquisition or customer insolvency?', ev, 'label', 'exact')
    if ev == 'acquisition':
        A(fx, 'calc', 'What multiple of EBITDA does the acquisition consideration represent?', r1(amt / float(ebitda)), 'number', 'abs:0.1')
        A(fx, 'qa', 'What is the stated EBITDA of the acquired business, in millions?', ebitda, 'number', 'abs:1')
        A(fx, 'qa', 'Was the acquisition funded with existing cash or borrowings?', 'borrowings', 'label', 'exact')
        A(fx, 'qa', 'What is the total of the acquisition consideration and the quarterly dividend, in millions?', amt + int(round(div * shares)), 'number', 'abs:1')
    else:
        A(fx, 'calc', 'What additional allowance was recorded on the customer receivable, in millions?', int(amt * 0.12), 'number', 'abs:1')
        A(fx, 'qa', 'What amount of trade receivables did the customer represent, in millions?', int(amt * 0.2), 'number', 'abs:1')
        A(fx, 'qa', 'What is the total of the additional allowance and the quarterly dividend, in millions?', int(amt * 0.12) + int(round(div * shares)), 'number', 'abs:1')
    fx['tags'] = {'disclosure': 'subsequent_event', 'trend': 'growing', 'subsequent': tag, 'event': ev}
    fx['facts'] = {'consideration': amt, 'ebitda': ebitda, 'dividend_per_share': div}
    finish(c, fx, 'Note 21, subsequent events', [s1, s2, s3], [], ['(1) Subsequent events were evaluated through the date the financial statements were issued.'])
def b_gc(c, fx):
    cash = int(c['scale'] * 0.03)
    if fx['i'] % 2 == 0:
        burn = int(cash / R.uniform(0.5, 0.9))
        tag = 'substantial_doubt'
        concl = "These conditions raise substantial doubt about the company's ability to continue as a going concern."
    else:
        burn = int(cash / R.uniform(2.2, 3.6))
        tag = 'no_substantial_doubt'
        concl = "Management concluded that these conditions do not raise substantial doubt about the company's ability to continue as a going concern."
    runway = cash / (burn / 12.0)
    plan = R.choice(['an equity raise completed in January 2026', 'a refinancing of the term loan', 'cost reductions of 15 percent of the cost base'])
    s1 = 'At 31 December 2025, cash and cash equivalents were {} and net cash used in operating activities was {} for FY2025.'.format(cash, burn)
    s2 = 'Based on the current burn rate, management expects cash to fund operations for {} months.'.format(int(runway))
    s3 = concl
    s4 = "Management's plans include {}.".format(plan)
    A(fx, 'calc', 'What is the implied cash runway in months?', int(runway), 'number', 'abs:1')
    A(fx, 'calc', 'What is the average monthly cash burn, in millions?', int(round(burn / 12.0)), 'number', 'abs:1')
    A(fx, 'calc', 'If the burn rate fell by 25 percent, what would the cash runway be, in months?', int(runway / 0.75), 'number', 'abs:2')
    A(fx, 'extraction', 'What was net cash used in operating activities, in millions?', burn, 'number', 'abs:0.01')
    A(fx, 'extraction', 'Quote the sentence that states the going concern conclusion.', s3, 'text', 'exact')
    A(fx, 'extraction', 'What action does management plan to take?', plan, 'text', 'normalized')
    A(fx, 'extraction', 'What was cash and cash equivalents at 31 December 2025, in millions?', cash, 'number', 'abs:0.01')
    A(fx, 'qa', 'Does the disclosure conclude that substantial doubt exists?', 'yes' if tag == 'substantial_doubt' else 'no', 'label', 'exact')
    A(fx, 'qa', 'What is the stated cash runway in months?', int(runway), 'number', 'abs:1')
    A(fx, 'qa', 'Does management rely on its stated plans to alleviate the going concern doubt?', 'yes' if tag == 'substantial_doubt' else 'no', 'label', 'exact')
    A(fx, 'qa', 'Is the cash balance sufficient to fund twelve months of operations at the stated burn rate?', 'yes' if runway >= 12 else 'no', 'label', 'exact')
    fx['tags'] = {'disclosure': 'going_concern', 'trend': 'declining', 'gc': tag, 'liquidity': 'insufficient' if tag == 'substantial_doubt' else 'sufficient'}
    fx['facts'] = {'cash': cash, 'burn': burn, 'runway_months': int(runway)}
    finish(c, fx, 'Note 1, going concern', [s1, s2, s3, s4], [], ['(1) The assessment covers twelve months from the date the financial statements are issued.'])
BUILDERS = [('vpm', b_vpm), ('margin', b_margin), ('revdis', b_revdis), ('lease', b_lease), ('debt', b_debt), ('segment', b_segment), ('restate', b_restate), ('cash', b_cash), ('tax', b_tax), ('goodwill', b_goodwill), ('risk', b_risk), ('legal', b_legal), ('subseq', b_subseq), ('gc', b_gc)]
def labelset(labels):
    return '{' + ', '.join(labels) + '}'
CLS_SPECS = [('disclosure', ['md_a', 'risk_factor', 'footnote', 'subsequent_event', 'going_concern'], 20, 'Classify the disclosure type of this excerpt as one of '), ('disclosure', ['md_a', 'risk_factor', 'footnote', 'subsequent_event', 'going_concern'], 20, 'Which disclosure category best describes this excerpt: '), ('margin_driver', ['favorable', 'unfavorable'], 12, 'Classify the direction of the FY2025 margin driver as one of '), ('margin_driver', ['favorable', 'unfavorable'], 12, 'Was the FY2025 margin driver favourable or unfavourable? Answer with one of '), ('liquidity', ['sufficient', 'insufficient'], 12, 'Classify the liquidity position described in the excerpt as one of '), ('liquidity', ['sufficient', 'insufficient'], 12, 'Does the excerpt describe liquidity as sufficient or insufficient? Choose from '), ('subsequent', ['recognized', 'nonrecognized'], 12, 'Classify the subsequent event as one of '), ('gc', ['substantial_doubt', 'no_substantial_doubt'], 12, 'Classify the going concern conclusion as one of '), ('restatement', ['error_correction', 'reclassification'], 12, 'Classify the restatement as one of '), ('covenant', ['compliant', 'breach'], 12, 'Classify the debt covenant position as one of '), ('revrec', ['point_in_time', 'over_time'], 12, 'Classify the predominant revenue recognition pattern as one of '), ('impairment', ['impairment_recognized', 'no_impairment'], 12, 'Classify the goodwill impairment outcome as one of '), ('tax', ['rate_reconciliation', 'deferred_tax'], 12, 'Classify the primary purpose of this tax note as one of '), ('trend', ['growing', 'declining'], 12, 'Classify the FY2025 revenue trend as one of '), ('capital', ['dividend', 'buyback', 'debt_repayment'], 12, 'Classify the primary capital allocation action described as one of '), ('event', ['acquisition', 'customer_insolvency'], 12, 'Classify the subsequent event type as one of '), ('mitigant', ['dual_sourcing', 'financial_hedging', 'regulatory_compliance'], 12, 'Classify the primary risk mitigant as one of ')]
def cls_rows(fixtures):
    pools = {}
    for f in fixtures:
        for (k, v) in f['tags'].items():
            pools.setdefault((k, v), []).append(f)
    rows = []
    for (tag, labels, n, stem) in CLS_SPECS:
        q = stem + labelset(labels) + '.'
        if stem.endswith('one of ') and len(labels) > 2 and stem.startswith('Which'):
            q = stem + ', '.join(labels[:-1]) + ', or ' + labels[-1] + '?'
        for i in range(n):
            lab = labels[i % len(labels)]
            pool = pools.get((tag, lab), [])
            if not pool:
                continue
            fx = pool[i // len(labels) % len(pool)]
            rows.append({'task': 'classification', 'fx': fx['key'], 'q': q, 'gt': lab, 'at': 'label', 'tol': 'exact'})
    return rows
SUMM_Q = ['Summarize this excerpt in three bullets covering the reported metric, the year-over-year change, and the stated driver.', 'Write a two-sentence summary of this disclosure suitable for an equity research note.', 'Summarize the excerpt in no more than 40 words.', 'Provide a three-bullet summary: what changed, by how much, and why.', 'Summarize the key disclosure points for a portfolio manager who has not read the filing.', 'Condense this excerpt into one sentence that preserves the quantified impact.', 'List the three most important takeaways from this excerpt.', 'Summarize the excerpt, distinguishing reported facts from management commentary.', 'Write a short analyst summary that states the disclosure type and its main implication.', 'Summarize this excerpt in bullet form for a morning meeting note.']
def summ_rows(fixtures):
    ordered = sorted(fixtures, key=lambda f: sha('summ|' + f['key']))
    rows = []
    for i in range(100):
        fx = ordered[i % len(ordered)]
        rows.append({'task': 'summarization', 'fx': fx['key'], 'q': SUMM_Q[i % len(SUMM_Q)], 'gt': None, 'at': 'text', 'tol': None})
    return rows
T_METRIC = {'name': 'get_financial_metric', 'description': 'Return a reported financial metric for a company and fiscal period.', 'parameters': {'type': 'object', 'properties': {'company': {'type': 'string'}, 'metric': {'type': 'string'}, 'period': {'type': 'string'}}, 'required': ['company', 'metric', 'period']}}
T_SEG = {'name': 'get_segment_table', 'description': 'Return the reported segment table for a company and fiscal period.', 'parameters': {'type': 'object', 'properties': {'company': {'type': 'string'}, 'period': {'type': 'string'}}, 'required': ['company', 'period']}}
T_TEXT = {'name': 'search_filing_text', 'description': 'Search the filing text for a phrase and return matching sentences.', 'parameters': {'type': 'object', 'properties': {'company': {'type': 'string'}, 'query': {'type': 'string'}}, 'required': ['company', 'query']}}
def valid_k(fx):
    f = fx['facts']
    ks = [0, 2, 3, 8, 9]
    if 'gross_margin' in f:
        ks.append(1)
    if 'operating_margin' in f:
        ks.append(4)
    if 'covenant' in f:
        ks.append(5)
    if 'total_lease' in f:
        ks.append(6)
    if 'restatement_impact' in f:
        ks.append(7)
    return ks

LABELS = {'cfo': 'operating cash flow', 'fcf': 'free cash flow', 'capex': 'capital expenditures', 'total_debt': 'total debt', 'ebitda': 'EBITDA', 'revenue': 'revenue', 'gross_profit': 'gross profit', 'gross_margin': 'gross margin', 'cost_of_revenue': 'cost of revenue', 'total_lease': 'total lease payments', 'lease_liability': 'lease liability', 'first_year_payment': 'first-year lease payment', 'net_leverage': 'net leverage', 'operating_income': 'operating income', 'operating_margin': 'operating margin', 'effective_tax_rate': 'effective tax rate', 'pretax_income': 'pre-tax income', 'tax_expense': 'income tax expense', 'impairment': 'impairment charge', 'goodwill': 'goodwill', 'restatement_impact': 'restatement impact', 'revenue_restated': 'restated revenue', 'revenue_prior': 'previously reported revenue', 'dividends': 'dividends paid', 'cash': 'cash and equivalents', 'burn': 'operating cash burn', 'consideration': 'acquisition consideration', 'volume_growth': 'volume growth', 'price_mix': 'price/mix', 'growth': 'revenue growth', 'margin_bps': 'margin impact in basis points', 'supplier_concentration': 'supplier concentration'}
PCT = ('growth', 'volume_growth', 'price_mix', 'gross_margin', 'operating_margin', 'effective_tax_rate', 'supplier_concentration')

def tool_result(fx, metric, value, period='FY2025'):
    unit = 'percent' if metric in PCT else ('basis points' if metric == 'margin_bps' else ('times' if metric in ('net_leverage', 'covenant') else 'millions unless stated'))
    return json.dumps({'company': fx['company'], 'metric': metric, 'period': period, 'value': value, 'unit': unit}, ensure_ascii=False)
def mk_tool(fx, seq, kind):
    c = fx['company']
    f = fx['facts']
    keys = [k for k in f if isinstance(f[k], (int, float))]
    if not keys or kind not in valid_k(fx):
        return None
    if kind == 0:
        m = 'revenue' if 'revenue' in f else keys[0]
        u = 'What was {} FY2025 revenue, in millions?'.format(c) if m == 'revenue' else 'What was the reported {} for {} in FY2025?'.format(LABELS.get(m, m.replace('_', ' ')), c)
        msgs = [{'role': 'user', 'content': u}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': m, 'period': 'FY2025'}})}, {'role': 'tool', 'content': tool_result(fx, m, f[m])}, {'role': 'user', 'content': 'State the value shown in the tool result.'}]
        gt = str(f[m])
    elif kind == 1 and 'gross_margin' in f:
        msgs = [{'role': 'user', 'content': 'Compute {} FY2025 gross margin from the reported figures.'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': 'gross_profit', 'period': 'FY2025'}})}, {'role': 'tool', 'content': tool_result(fx, 'gross_profit', f['gross_profit'])}, {'role': 'user', 'content': 'The revenue figure is {} and gross profit is {}. State the gross margin in percent.'.format(f['revenue'], f['gross_profit'])}]
        gt = '{:.1f}'.format(round(f['gross_profit'] / float(f['revenue']) * 100, 1))
    elif kind == 2:
        m = 'revenue' if 'revenue' in f else keys[0]
        msgs = [{'role': 'user', 'content': 'Pull {} FY2023 {} so I can compare it with FY2025.'.format(c, LABELS.get(m, m.replace('_', ' ')))}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': m, 'period': 'FY2023'}})}, {'role': 'tool', 'content': json.dumps({'error': 'period not available', 'valid_periods': ['FY2025', 'FY2024']})}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': m, 'period': 'FY2025'}})}, {'role': 'tool', 'content': tool_result(fx, m, f[m])}, {'role': 'user', 'content': 'The requested period was unavailable. Report the FY2025 value that was returned.'}]
        gt = str(f[m])
    elif kind == 3:
        msgs = [{'role': 'user', 'content': 'What was {} FY2025 free cash flow per share?'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': 'fcf_per_share', 'period': 'FY2025'}})}, {'role': 'tool', 'content': json.dumps({'error': 'metric not disclosed', 'available': keys[:4]})}, {'role': 'user', 'content': 'If the metric is not disclosed, reply with insufficient_disclosure.'}]
        gt = 'insufficient_disclosure'
    elif kind == 4 and 'operating_margin' in f:
        msgs = [{'role': 'user', 'content': 'Compare FY2025 revenue and operating income for {} and state the operating margin.'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_segment_table', 'arguments': {'company': c, 'period': 'FY2025'}})}, {'role': 'tool', 'content': json.dumps({'company': c, 'period': 'FY2025', 'revenue': f['revenue'], 'operating_income': f['operating_income']})}, {'role': 'user', 'content': 'State the operating margin in percent.'}]
        gt = '{:.1f}'.format(round(f['operating_income'] / float(f['revenue']) * 100, 1))
    elif kind == 5 and 'covenant' in f:
        msgs = [{'role': 'user', 'content': 'Check {} against its leverage covenant.'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': 'net_leverage', 'period': 'FY2025'}})}, {'role': 'tool', 'content': json.dumps({'company': c, 'metric': 'net_leverage', 'value': f['net_leverage'], 'covenant_max': f['covenant']})}, {'role': 'user', 'content': 'State whether the company is compliant or in breach.'}]
        gt = 'compliant' if f['net_leverage'] <= f['covenant'] else 'breach'
    elif kind == 6 and 'total_lease' in f:
        msgs = [{'role': 'user', 'content': 'Total the undiscounted operating lease payments for {}.'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': 'total_lease', 'period': 'FY2025'}})}, {'role': 'tool', 'content': tool_result(fx, 'total_lease', f['total_lease'])}, {'role': 'user', 'content': 'State the total in millions.'}]
        gt = str(f['total_lease'])
    elif kind == 7 and 'restatement_impact' in f:
        msgs = [{'role': 'user', 'content': 'Quantify the FY2024 restatement impact for {}.'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': 'restatement_impact', 'period': 'FY2024'}})}, {'role': 'tool', 'content': tool_result(fx, 'restatement_impact', f['restatement_impact'], 'FY2024')}, {'role': 'user', 'content': 'State the revenue impact in millions.'}]
        gt = str(f['restatement_impact'])
    elif kind == 8:
        msgs = [{'role': 'user', 'content': 'Summarise the two largest reported metrics for {} in FY2025.'.format(c)}, {'role': 'assistant', 'content': json.dumps({'tool': 'get_financial_metric', 'arguments': {'company': c, 'metric': keys[0], 'period': 'FY2025'}})}, {'role': 'tool', 'content': tool_result(fx, keys[0], f[keys[0]])}, {'role': 'user', 'content': 'Also state the {} figure.'.format(LABELS.get(keys[1], keys[1].replace('_', ' ')))}]
        gt = str(f[keys[1]])
    else:
        paras = [x for x in fx['ctx'].split('\n\n') if x and (not x.startswith('|')) and (not x.startswith('Units')) and (not x.startswith('Excerpt'))]
        snip = paras[0].split('. ')[0] + '.'
        phrase = fx.get('doc', 'significant accounting policy')
        msgs = [{'role': 'user', 'content': 'Search the {} filing for the phrase {}.'.format(c, phrase)}, {'role': 'assistant', 'content': json.dumps({'tool': 'search_filing_text', 'arguments': {'company': c, 'query': phrase}})}, {'role': 'tool', 'content': json.dumps({'company': c, 'matches': 1, 'first_match': snip}, ensure_ascii=False)}, {'role': 'user', 'content': 'Quote the first matching sentence.'}]
        gt = snip
    msgs[0]['content'] = 'Refer to the {} excerpt. '.format(fx.get('doc', 'FY2025')) + msgs[0]['content']
    tools = [T_METRIC, T_SEG, T_TEXT]
    return {'task': 'tool_use', 'fx': fx['key'], 'messages': msgs, 'tools': tools, 'gt': gt, 'at': 'text', 'tol': 'normalized'}
def tool_rows(fixtures):
    pool = [f for f in fixtures if f['facts']]
    rows = []
    for k in range(10):
        cand = sorted([f for f in pool if k in valid_k(f)], key=lambda f: sha('tk%d|' % k + f['key']))
        for fx in cand[:10]:
            r = mk_tool(fx, len(rows) + 1, k)
            if r is not None:
                rows.append(r)
    return rows
def assign_splits(rows):
    fixtures = sorted(set((r['fx'] for r in rows)), key=sha)
    counts, per_task = {}, {}
    for r in rows:
        counts[r['fx']] = counts.get(r['fx'], 0) + 1
        per_task.setdefault(r['task'], {})
        per_task[r['task']][r['fx']] = per_task[r['task']].get(r['fx'], 0) + 1
    total, split, cum = len(rows), {}, 0
    for k in fixtures:
        split[k] = 'train' if cum < 0.8 * total else ('val' if cum < 0.9 * total else 'test')
        cum += counts[k]
    def score(sp):
        s = 0
        for task, fxmap in per_task.items():
            n = sum(fxmap.values())
            for name, frac in (('train', 0.8), ('val', 0.1), ('test', 0.1)):
                c = sum(v for k, v in fxmap.items() if sp[k] == name)
                s += abs(c - frac * n) + (100 if c < 3 else 0)
        return s
    best = score(split)
    for _ in range(6):
        moved = False
        for k in fixtures:
            cur = split[k]
            for cand in ('train', 'val', 'test'):
                if cand != cur:
                    split[k] = cand
                    sc = score(split)
                    if sc < best - 0.001:
                        best, cur, moved = sc, cand, True
                    else:
                        split[k] = cur
        if not moved:
            break
    for r in rows:
        r['split'] = split[r['fx']]
def build(fixtures):
    seen = set()
    for fx in fixtures:
        for task in ('calc', 'extraction', 'qa'):
            for it in fx['items'][task]:
                k = (fx['key'], task, it['q'])
                assert k not in seen, 'dup question in fixture: %s' % (k,)
                seen.add(k)
    rows = []
    used = set()
    quota = {'calc': 120, 'extraction': 220, 'qa': 240, 'summarization': 100, 'tool_use': 100}
    for (task, nfx, per) in [('calc', 30, 4), ('extraction', 44, 5), ('qa', 40, 6), ('summarization', 20, 5), ('tool_use', 20, 5)]:
        if task in ('summarization', 'tool_use'):
            continue
        pool = [f for f in fixtures if f['items'].get(task)]
        order = sorted(pool, key=lambda f: sha(task + '|' + f['key']))
        ordered = [f for f in order if f['key'] not in used] + [f for f in order if f['key'] in used]
        need = quota[task]
        for fx in ordered:
            items = fx['items'][task]
            take = min(per, len(items), need)
            used.add(fx['key'])
            start = int(sha('s|' + task + fx['key'])[:6], 16) % len(items)
            for j in range(take):
                rows.append({'task': task, 'fx': fx['key'], 'item': items[(start + j) % len(items)]})
            need -= take
            if need == 0:
                break
        assert need == 0, (task, need)
    for r in rows:
        it = r.pop('item')
        r.update({'q': it['q'], 'gt': it['gt'], 'at': it['at'], 'tol': it['tol']})
    rows += cls_rows(fixtures) + summ_rows(fixtures) + tool_rows(fixtures)
    assign_splits(rows)
    return rows
def materialize(rows):
    order = ['calc', 'extraction', 'qa', 'classification', 'summarization', 'tool_use']
    rows.sort(key=lambda r: (order.index(r['task']), r.get('q') or r['fx']))
    seq = {}
    out = []
    for r in rows:
        t = r['task']
        seq[t] = seq.get(t, 0) + 1
        row = {'id': 'fin_%s_%s_%06d' % (AREA, ABBR[t], seq[t]), 'task': t, 'source': 'synthetic:' + AREA}
        if 'messages' in r:
            row.update({'messages': r['messages'], 'tools': r['tools']})
        else:
            row.update({'context': CONTEXT[r['fx']], 'question': r['q']})
        row.update({'ground_truth': r['gt'], 'answer_type': r['at'], 'tolerance': r['tol'], 'split': r['split'], 'thinking': 'on' if t in THINK_ON else 'off'})
        out.append(row)
    return out
def checks(rows):
    import re
    thousands = re.compile('(?<![\\w.])\\d{1,3}(,\\d{3})+(?!\\d)')
    bad = []
    seen = set()
    for r in rows:
        ctx = r.get('context', '')
        q = r.get('question', '')
        if ctx:
            if not 300 <= len(ctx) <= 1200:
                bad.append(('ctx_len', r['id'], len(ctx)))
            if not ctx.startswith('Units:'):
                bad.append(('ctx_lead', r['id'], ctx[:20]))
        if r['task'] == 'extraction' and r['answer_type'] == 'text' and (r['ground_truth'] not in ctx):
            bad.append(('gt_not_in_ctx', r['id']))
        if r['answer_type'] == 'number' and (not isinstance(r['ground_truth'], (int, float))):
            bad.append(('gt_type', r['id']))
        blob = ctx + '\n' + q
        if thousands.search(blob):
            bad.append(('thousands', r['id'], thousands.search(blob).group(0)))
        if re.search('[$]\\s*\\d', blob):
            bad.append(('currency_symbol', r['id']))
        if not ctx:
            continue
        key = (ctx.strip().lower(), re.sub('\\d+(?:[.,]\\d+)*', '#', q.strip().lower()))
        if key in seen:
            bad.append(('near_dup', r['id']))
        seen.add(key)
    return bad
def main():
    fixtures = []
    for (kind, fn) in BUILDERS:
        idxs = list(range(len(COMPANIES))); R.shuffle(idxs)
        for (i, ci) in enumerate(idxs[:12]):
            fx = new_fx(kind, COMPANIES[ci], i)
            fn(COMPANIES[ci], fx)
            fixtures.append(fx)
            CONTEXT[fx['key']] = fx['ctx']
    rows = materialize(build(fixtures))
    bad = checks(rows)
    if bad:
        print(json.dumps({'status': 'self_check_failed', 'n': len(bad), 'first': bad[:10]}, indent=2))
        return 1
    path = os.path.join(HERE, 'prompts.jsonl')
    with open(path, 'w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    import collections, re
    fam = collections.Counter((re.sub('\\d+(?:[.,]\\d+)*', '#', (r.get('question') or r['messages'][0]['content']).strip().lower())[:160] for r in rows))
    ctxs = set((re.sub('\\d+(?:[.,]\\d+)*', '#', r['context']) for r in rows if r.get('context')))
    by_task = dict(collections.Counter((r['task'] for r in rows))); by_split = dict(collections.Counter((r['split'] for r in rows)))
    by_type = dict(collections.Counter((r['answer_type'] for r in rows if r['ground_truth'] is not None)))
    multi = sum((1 for r in rows if r['task'] == 'tool_use' and any((m['role'] == 'assistant' for m in r['messages']))))
    rep = {'area': AREA, 'profile': 'B', 'rows': len(rows), 'by_task': by_task, 'by_split': by_split,
           'by_answer_type': by_type, 'distinct_question_families': len(fam), 'top_family_share': round(fam.most_common(1)[0][1] / float(len(rows)), 4),
           'distinct_contexts': len(ctxs), 'near_dup_pairs': 0, 'tool_use_multi_step_share': round(multi / 100.0, 3), 'validation': 'pass',
           'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest(),
           'notes': 'Synthetic 10-K excerpts; 24 companies, 14 document types, fixture-level splits.',
           'weakest_spot': 'Summarisation rows have null ground_truth; tool rows grade only the final short answer.'}
    with open(os.path.join(HERE, 'report.json'), 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(rep, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=2))
    return 0
CONTEXT = {}
if __name__ == '__main__':
    raise SystemExit(main())
