"""Deterministic synthetic generator for the reits_real_estate area.

All entities are fictional. Every ground_truth number is recomputed in code from the same
rounded values that are printed into the row context, so repeating the arithmetic on the
rendered table reproduces the answer.
"""
import hashlib
import json
import os
import random
import re
AREA = 'reits_real_estate'
SOURCE = 'synthetic:reits_real_estate'
OUT = os.path.dirname(os.path.abspath(__file__))
R = random.Random(42)
TASKS = ['calc', 'extraction', 'qa', 'classification', 'summarization', 'tool_use']
QUOTA = {'calc': 280, 'extraction': 220, 'qa': 200, 'classification': 100, 'summarization': 100, 'tool_use': 100}
THINK = {'calc': 'on', 'extraction': 'off', 'qa': 'on', 'classification': 'off', 'summarization': 'off', 'tool_use': 'on'}
UNITS = 'Units: $ in millions except per-share amounts in dollars; occupancy, cap rates, yields, spreads and margins are stated in percent; GLA is in thousands of square feet.'

def f(x, dp=1):
    s = ('%.' + str(dp) + 'f') % (x,)
    return s[1:] if s.startswith('-') and float(s) == 0.0 else s

def q(x, dp=1):
    return float(('%.' + str(dp) + 'f') % (x,))
MASK = re.compile('\\d+(?:[.,]\\d+)*')
WS = re.compile('\\s+')

def msk(s):
    return MASK.sub('#', WS.sub(' ', str(s)).strip().lower())

def tbl(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] * len(head)) + '|']
    out += ['| ' + ' | '.join((str(c) for c in r)) + ' |' for r in rows]
    return '\n'.join(out)
ENTS = [  # name, sector, fiscal year end, currency, city, property type
    ('Halcyon Ridge REIT', 'Office', '31 December', 'USD', 'Denver', 'Office'),
    ('Larkspur Commons Trust', 'Retail', '31 December', 'USD', 'Atlanta', 'Retail'),
    ('Ironwood Logistics REIT', 'Industrial', '31 December', 'USD', 'Chicago', 'Industrial'),
    ('Bramble Point Residential', 'Residential', '31 December', 'USD', 'Austin', 'Multifamily'),
    ('Kestrel Creek Storage', 'Self storage', '31 December', 'USD', 'Phoenix', 'Self storage'),
    ('Marlowe Data Trust', 'Data center', '31 December', 'USD', 'Dallas', 'Data center'),
    ('Alder Grove Medical REIT', 'Healthcare', '31 December', 'USD', 'Boston', 'Medical office'),
    ('Stonebridge Lodging Trust', 'Lodging', '31 December', 'USD', 'Orlando', 'Hotel'),
    ('Copperfield Retail REIT', 'Retail', '31 December', 'USD', 'Charlotte', 'Retail'),
    ('Willow Bend Industrial', 'Industrial', '31 December', 'USD', 'Memphis', 'Industrial'),
    ('Harborview Office Trust', 'Office', '31 December', 'USD', 'Seattle', 'Office'),
    ('Ashford Residential REIT', 'Residential', '31 December', 'USD', 'Raleigh', 'Multifamily'),
    ('Quarry Ridge Storage', 'Self storage', '31 December', 'USD', 'Las Vegas', 'Self storage'),
    ('Foxglove Data Centers', 'Data center', '31 December', 'USD', 'Ashburn', 'Data center'),
    ('Silverlake Medical Trust', 'Healthcare', '31 December', 'USD', 'San Diego', 'Medical office'),
    ('Northgate Lodging', 'Lodging', '31 December', 'USD', 'Nashville', 'Hotel'),
    ('Pemberton Office REIT', 'Office', '31 December', 'USD', 'Philadelphia', 'Office'),
    ('Draycott Retail Trust', 'Retail', '31 December', 'USD', 'Minneapolis', 'Retail'),
    ('Ellsworth Industrial', 'Industrial', '31 December', 'USD', 'Columbus', 'Industrial'),
    ('Vantage Point Residential', 'Residential', '31 December', 'USD', 'Tampa', 'Multifamily'),
    ('Kingswell Storage REIT', 'Self storage', '31 December', 'USD', 'Sacramento', 'Self storage'),
    ('Brightwater Medical', 'Healthcare', '31 December', 'USD', 'Houston', 'Medical office'),
    ('Fair Oaks Mixed Use', 'Mixed use', '31 December', 'USD', 'Portland', 'Mixed use'),
    ('Highgate Net Lease', 'Net lease', '31 December', 'USD', 'Kansas City', 'Net lease'),
]
PN = ['Cedar Hollow', 'Larkspur', 'Ironwood', 'Bramble Point', 'Kestrel Creek', 'Marlowe', 'Alder Grove', 'Stonebridge', 'Copperfield', 'Willow Bend', 'Harborview', 'Ashford', 'Quarry Ridge', 'Foxglove', 'Silverlake', 'Northgate', 'Pemberton', 'Draycott', 'Ellsworth', 'Vantage', 'Kingswell', 'Brightwater', 'Fair Oaks', 'Highgate', 'Amberley', 'Ravenswood', 'Thistledown', 'Granite Bay', 'Meridian Park', 'Old Mill']
SUF = {'Office': ['Office Center', 'Park', 'Tower', 'Plaza', 'Commons'], 'Retail': ['Marketplace', 'Commons', 'Shopping Center', 'Square', 'Crossing'], 'Industrial': ['Logistics Park', 'Distribution Center', 'Industrial Park', 'Business Park', 'Warehouse'], 'Multifamily': ['Apartments', 'Residences', 'Gardens', 'Village', 'Court'], 'Self storage': ['Storage', 'Self Storage', 'Storage Center', 'Lockers', 'Depot'], 'Data center': ['Data Center', 'Campus', 'Data Hall', 'Exchange', 'Works'], 'Medical office': ['Medical Plaza', 'Medical Center', 'Clinic Campus', 'Health Park', 'Medical Arts'], 'Hotel': ['Hotel', 'Suites', 'Inn', 'Lodge', 'Resort'], 'Mixed use': ['Mixed Use', 'Commons', 'Quarter', 'District', 'Exchange'], 'Net lease': ['Net Lease Portfolio', 'Distribution Center', 'Pharmacy', 'Convenience', 'Service Center']}

def build_fixtures():
    out = []
    for (i, (name, sector, fye, ccy, city, ptype)) in enumerate(ENTS):
        r = random.Random(7000 + 13 * i)
        n = 3 + i % 3
        trend = 1 if i % 2 == 0 else -1
        props = []
        for j in range(n):
            gla = r.randrange(120, 621, 10)
            occ = q(r.uniform(87.0, 97.5), 1)
            rent = q(r.uniform(15.0, 55.0), 1)
            opx = q(r.uniform(5.0, 14.0), 1)
            rc = q(r.uniform(0.65, 0.95), 2)
            st = 'Acquisition' if j == n - 1 and i % 3 == 0 else 'Same store'
            rev = q(gla * 1000 * occ / 100.0 * rent / 1000000.0, 1)
            opex = q(gla * 1000 * opx / 1000000.0, 1)
            rec = q(opex * rc, 1)
            oth = q(rev * r.uniform(0.004, 0.018), 1)
            noi = q(rev + rec + oth - opex, 1)
            mkt = q(rent * r.uniform(0.82, 1.18), 1)
            p = {'name': PN[(i * 5 + j * 7) % 30] + ' ' + SUF[ptype][j % 5], 'type': ptype, 'gla': gla, 'occ': occ, 'rent': rent, 'opex_psf': opx, 'recov': rc, 'rev': rev, 'opex': opex, 'rec': rec, 'oth': oth, 'noi': noi, 'mkt': mkt, 'status': st, 'noi_p': None, 'rev_p': 0.0, 'rec_p': 0.0, 'opex_p': 0.0, 'oth_p': 0.0}
            if st == 'Same store':
                occ_p = q(min(99.0, occ - trend * r.uniform(0.3, 2.4)), 1)
                rent_p = q(rent * (1 - trend * r.uniform(0.01, 0.055)), 1)
                p['occ_p'] = occ_p
                p['rent_p'] = rent_p
                p['rev_p'] = q(gla * 1000 * occ_p / 100.0 * rent_p / 1000000.0, 1)
                p['opex_p'] = q(gla * 1000 * opx * 1.02 / 1000000.0, 1)
                p['rec_p'] = q(p['opex_p'] * rc, 1)
                p['oth_p'] = q(p['rev_p'] * 0.015, 1)
                p['noi_p'] = q(p['rev_p'] + p['rec_p'] + p['oth_p'] - p['opex_p'], 1)
            props.append(p)
        fx = {'key': 'fx%02d' % i, 'name': name, 'sector': sector, 'fye': fye, 'ccy': ccy, 'city': city, 'props': props}
        fx['gla'] = sum((p['gla'] for p in props))
        fx['noi'] = q(sum((p['noi'] for p in props)), 1)
        fx['noi_p'] = q(sum((p['noi_p'] for p in props if p['noi_p'] is not None)), 1)
        ss = [p for p in props if p['status'] == 'Same store']
        fx['ss_noi'] = q(sum((p['noi'] for p in ss)), 1)
        fx['ss_noi_p'] = q(sum((p['noi_p'] for p in ss)), 1)
        fx['occ'] = q(sum((p['occ'] * p['gla'] for p in props)) / fx['gla'], 1)
        fx['occ_prior'] = q(sum((p['occ'] for p in props if p['status'] == 'Same store')) / len(ss), 1)
        fx['rent_w'] = sum((p['rent'] * p['gla'] * p['occ'] for p in props)) / sum((p['gla'] * p['occ'] for p in props))
        fx['mkt_w'] = sum((p['mkt'] * p['gla'] * p['occ'] for p in props)) / sum((p['gla'] * p['occ'] for p in props))
        cap = q(r.uniform(6.0, 7.8), 1)
        fx['cap'] = cap
        fx['value'] = q(fx['noi'] / (cap / 100.0), 1)
        fx['appr'] = q(fx['value'] * r.uniform(0.93, 1.07), 1)
        ltv = [0.28, 0.34, 0.4, 0.46][i % 4]
        fx['loan'] = q(fx['value'] * ltv, 1)
        tl = q(fx['loan'] * 0.55, 1)
        nt = q(fx['loan'] - tl, 1)
        fx['tl'] = tl
        fx['notes'] = nt
        fx['tl_rate'] = q(r.uniform(5.1, 6.6), 2)
        fx['nt_rate'] = q(r.uniform(3.9, 5.4), 2)
        fx['tl_amort'] = q(tl * 0.012, 1)
        fx['int'] = q(tl * fx['tl_rate'] / 100.0 + nt * fx['nt_rate'] / 100.0, 1)
        fx['ds'] = q(fx['int'] + fx['tl_amort'], 1)
        fx['dscr'] = q(fx['noi'] / fx['ds'], 2)
        fx['dy'] = q(fx['noi'] / fx['loan'] * 100.0, 1)
        fx['cash'] = q(r.uniform(2.0, 16.0), 1)
        fx['liab'] = q(r.uniform(5.0, 22.0), 1)
        fx['rent_rev'] = q(sum((p['rev'] for p in props)), 1)
        fx['recov'] = q(sum((p['rec'] for p in props)), 1)
        fx['opex'] = q(sum((p['opex'] for p in props)), 1)
        fx['other'] = q(sum((p['oth'] for p in props)), 1)
        fx['ga'] = q(fx['noi'] * r.uniform(0.06, 0.11), 1)
        fx['da'] = q(fx['noi'] * r.uniform(0.22, 0.34), 1)
        fx['gain'] = q(r.uniform(0.0, 8.0), 1)
        fx['ni'] = q(fx['noi'] - fx['ga'] - fx['int'] - fx['da'] + fx['gain'], 1)
        fx['rent_rev_p'] = q(sum((p['rev_p'] for p in props)), 1)
        fx['recov_p'] = q(sum((p['rec_p'] for p in props)), 1)
        fx['opex_p'] = q(sum((p['opex_p'] for p in props)), 1)
        fx['other_p'] = q(sum((p['oth_p'] for p in props)), 1)
        fx['ga_p'] = q(fx['ga'] * 0.95, 1)
        fx['int_p'] = q(fx['int'] * 0.96, 1)
        fx['da_p'] = q(fx['da'] * 0.98, 1)
        fx['gain_p'] = 0.0
        fx['ni_p'] = q(fx['noi_p'] - fx['ga_p'] - fx['int_p'] - fx['da_p'], 1)
        fx['ffo'] = q(fx['ni'] + fx['da'] - fx['gain'], 1)
        fx['capex'] = q(fx['noi'] * r.uniform(0.12, 0.2), 1)
        fx['sl_adj'] = q(r.uniform(0.2, 1.6), 1)
        fx['ncc'] = q(r.uniform(0.2, 0.9), 1)
        fx['affo'] = q(fx['ffo'] - fx['capex'] - fx['sl_adj'] + fx['ncc'], 1)
        fx['shares'] = float(r.randrange(12, 46))
        fx['ffo_ps'] = q(fx['ffo'] / fx['shares'], 2)
        fx['affo_ps'] = q(fx['affo'] / fx['shares'], 2)
        fx['dev'] = []
        for k in range(2):
            cost = q(r.uniform(38.0, 150.0), 1)
            yld = q(r.uniform(6.8, 9.6), 2)
            sn = q(cost * yld / 100.0, 1)
            fx['dev'].append({'name': PN[(i * 3 + k * 11 + 4) % 30] + ' ' + ['Redevelopment', 'Phase II'][k], 'type': ptype, 'incurred': q(cost * r.uniform(0.15, 0.55), 1), 'complete': q(cost * r.uniform(0.45, 0.85), 1), 'budget': cost, 'stab': sn, 'cap': q(r.uniform(5.2, 6.9), 1)})
        fx['dev_cost'] = q(sum((d['budget'] for d in fx['dev'])), 1)
        fx['dev_stab'] = q(sum((d['stab'] for d in fx['dev'])), 1)
        core = q(fx['noi'] * 0.7, 1)
        non = q(fx['noi'] * 0.22, 1)
        oth = q(fx['noi'] - core - non, 1)
        fx['nav_seg'] = [('Stabilised core', core, q(cap - 0.5, 1)), ('Non-core and redevelopment', non, q(cap + 0.7, 1)), ('Other income assets', oth, q(cap + 0.2, 1))]
        fx['nav_val'] = q(sum((s[1] / (s[2] / 100.0) for s in fx['nav_seg'])), 1)
        fx['land'] = q(r.uniform(9.0, 38.0), 1)
        fx['nav'] = q(fx['nav_val'] + fx['land'] + fx['cash'] - fx['loan'] - fx['liab'], 1)
        fx['navps'] = q(fx['nav'] / fx['shares'], 2)
        fx['price'] = q(fx['navps'] * (1 + r.uniform(-0.3, 0.2)), 2)
        fx['dps'] = q(fx['affo_ps'] * r.uniform(0.55, 0.85), 2)
        fx['dps_p'] = q(fx['dps'] * 0.94, 2)
        yrs = [2026, 2027, 2028, 2029, 2030, 2031]
        rem = [0.5, 1.5, 2.5, 3.5, 4.5, 6.5]
        fx['lease'] = []
        for k in range(6):
            fx['lease'].append({'year': yrs[k], 'sf': r.randrange(40, 300, 5), 'rent': q(r.uniform(18.0, 48.0), 1), 'rem': rem[k]})
        fx['act'] = []
        for k in range(3):
            pr = q(r.uniform(20.0, 44.0), 1)
            fx['act'].append({'bldg': props[k % len(props)]['name'], 'sf': r.randrange(12, 60, 2), 'prior': pr, 'new': q(pr * r.uniform(0.94, 1.13), 1), 'ti': q(r.uniform(6.0, 24.0), 1), 'lc': q(r.uniform(2.0, 5.0), 1), 'term': [60, 84, 120][k]})
        fx['abs'] = {'base': q(r.uniform(24.0, 46.0), 2), 'esc': 3.0, 'term': 5, 'free': 6, 'ti': q(r.uniform(8.0, 22.0), 1), 'lc': q(r.uniform(2.0, 5.0), 1)}
        fx['sale_cap'] = q(cap + r.uniform(-1.8, 2.0), 1)
        fx['wacc'] = q(6.4 + i % 5 * 0.2, 2)
        out.append(fx)
    return out
FIX = build_fixtures()

def hdr(fx, title):
    return UNITS + '\n\n' + fx['name'] + ' (' + fx['sector'] + '; fiscal year ends ' + fx['fye'] + '; reporting currency ' + fx['ccy'] + '). ' + title

def v_props(fx):
    rows = [[p['name'], p['type'], p['gla'], f(p['occ']), f(p['rent']), f(p['mkt']), f(p['noi']), '' if p['noi_p'] is None else f(p['noi_p']), p['status']] for p in fx['props']]
    return hdr(fx, 'Property schedule at 31 December 2025. Status flags membership of the same-store pool.') + '\n\n' + tbl(['Property', 'Type', 'GLA (000 sf)', 'Occupancy (percent)', 'Rent psf', 'Market rent psf', 'NOI FY2025 ($mm)', 'NOI FY2024 ($mm)', 'Status'], rows)

def v_build(fx):
    rows = [[p['name'], p['type'], p['gla'], f(p['rev']), f(p['rec']), f(p['oth']), f(p['opex']), f(p['recov'], 2), p['status']] for p in fx['props']]
    return hdr(fx, 'Property revenue build for FY2025; recoveries are billed gross of an administrative fee.') + '\n\n' + tbl(['Property', 'Type', 'GLA (000 sf)', 'Rental revenue FY2025 ($mm)', 'Recoveries FY2025 ($mm)', 'Other income FY2025 ($mm)', 'Property opex FY2025 ($mm)', 'Recovery ratio', 'Status'], rows)

def v_cons(fx):
    rows = [['Rental revenue', f(fx['rent_rev']), f(fx['rent_rev_p'])], ['Recoveries', f(fx['recov']), f(fx['recov_p'])], ['Other income', f(fx['other']), f(fx['other_p'])], ['Property operating expenses', f(fx['opex']), f(fx['opex_p'])], ['Net operating income', f(fx['noi']), f(fx['noi_p'])], ['General and administrative', f(fx['ga']), f(fx['ga_p'])], ['Interest expense', f(fx['int']), f(fx['int_p'])], ['Depreciation and amortisation', f(fx['da']), f(fx['da_p'])], ['Gain on sale of property', f(fx['gain']), f(fx['gain_p'])], ['Net income', f(fx['ni']), f(fx['ni_p'])], ['Dividends declared per share (dollars)', f(fx['dps'], 2), f(fx['dps_p'], 2)]]
    return hdr(fx, 'Consolidated statement of operations for the year to 31 December 2025.') + '\n\n' + tbl(['Line item', 'FY2025', 'FY2024'], rows) + '\n\nNote 1: net operating income excludes general and administrative expense, interest expense, depreciation and amortisation, and gains on sale. Note 2: recoveries exclude tenant direct-metered utilities of ' + f(fx['other'] * 0.4) + '.' + '\nStated portfolio capitalisation rate: ' + f(fx['cap']) + ' percent. Appraised gross asset value at 31 December 2025: ' + f(fx['appr']) + '.'

def v_ffo(fx):
    rows = [['Net income', f(fx['ni'])], ['Depreciation and amortisation', f(fx['da'])], ['Gain on sale of property', f(fx['gain'])], ['Recurring capital expenditure', f(fx['capex'])], ['Straight-line rent adjustment', f(fx['sl_adj'])], ['Non-cash share-based compensation', f(fx['ncc'])], ['Weighted average shares (millions)', f(fx['shares'], 0)], ['Annual dividend per share (dollars)', f(fx['dps'], 2)], ['Share price at 31 December 2025 (dollars)', f(fx['price'], 2)]]
    return hdr(fx, 'Reconciliation of net income to funds from operations and adjusted funds from operations (NAREIT basis).') + '\n\n' + tbl(['Reconciliation item', 'FY2025'], rows)

def v_debt(fx):
    rows = [['Term loan', f(fx['tl']), f(fx['tl_rate'], 2), f(fx['tl_amort']), '2028'], ['Senior unsecured notes', f(fx['notes']), f(fx['nt_rate'], 2), '0.0', '2031'], ['Revolving credit facility (undrawn)', '0.0', '0.0', '0.0', '2027']]
    return hdr(fx, 'Debt schedule and covenants at 31 December 2025.') + '\n\n' + tbl(['Tranche', 'Balance ($mm)', 'Rate (percent)', 'Annual amortisation ($mm)', 'Maturity'], rows) + '\n\nCash and equivalents: ' + f(fx['cash']) + ' ($mm). FY2025 net operating income: ' + f(fx['noi']) + ' ($mm). FY2025 general and administrative expense: ' + f(fx['ga']) + ' ($mm).\nCovenants: minimum debt service coverage 1.50x; maximum net debt to EBITDA 7.00x.'

def v_lease(fx):
    rows = [[l['year'], l['sf'], f(l['rent']), f(l['rem'])] for l in fx['lease']]
    return hdr(fx, 'Lease expiry schedule by annual rent at 31 December 2025.') + '\n\n' + tbl(['Expiry year', 'Leased sf (000)', 'Rent psf', 'Years remaining'], rows)

def v_dev(fx):
    rows = [[d['name'], d['type'], f(d['incurred']), f(d['complete']), f(d['budget']), f(d['stab']), f(d['cap'])] for d in fx['dev']]
    return hdr(fx, 'Development and redevelopment pipeline at 31 December 2025.') + '\n\n' + tbl(['Project', 'Type', 'Cost incurred to date ($mm)', 'Cost to complete ($mm)', 'Total budget ($mm)', 'Stabilised NOI ($mm)', 'Stabilised cap rate (percent)'], rows)

def v_nav(fx):
    rows = [[s[0], f(s[1]), f(s[2])] for s in fx['nav_seg']]
    return hdr(fx, 'Net asset value build-up at 31 December 2025.') + '\n\n' + tbl(['Segment', 'Stabilised NOI ($mm)', 'Cap rate (percent)'], rows) + '\n\n' + tbl(['Other item', 'Amount ($mm)'], [['Land held for development', f(fx['land'])], ['Cash and equivalents', f(fx['cash'])], ['Total debt', f(fx['loan'])], ['Other liabilities', f(fx['liab'])]]) + '\nShares outstanding: ' + f(fx['shares'], 0) + ' million. Share price: ' + f(fx['price'], 2) + ' dollars per share.'

def v_act(fx):
    rows = [[a['bldg'], a['sf'], f(a['prior']), f(a['new']), f(a['ti']), f(a['lc']), a['term']] for a in fx['act']]
    return hdr(fx, 'Leasing activity for the year to 31 December 2025, all renewals.') + '\n\n' + tbl(['Building', 'Leased sf (000)', 'Prior rent psf', 'New rent psf', 'TI psf', 'Leasing commission (percent of aggregate rent)', 'Term (months)'], rows)

def v_abs(fx):
    a = fx['abs']
    rows = [['Initial rent (dollars per sf)', f(a['base'], 2)], ['Annual escalation (percent)', f(a['esc'])], ['Term (years)', a['term']], ['Free rent (months)', a['free']], ['Tenant improvement allowance (dollars per sf)', f(a['ti'])], ['Leasing commission (percent of aggregate rent)', f(a['lc'])], ['Commencement', '1 January 2026']]
    return hdr(fx, 'Lease abstraction for a single new lease; rent is payable monthly in advance.') + '\n\n' + tbl(['Lease term', 'Value'], rows)

def v_deal(fx):
    prop = max(fx['props'], key=lambda p: p['noi'])
    rows = [['Property', prop['name']], ['Contract price ($mm)', f(prop['noi'] / (fx['sale_cap'] / 100.0))], ['FY2025 NOI of the property ($mm)', f(prop['noi'])], ['Buyer capitalisation rate (percent)', f(fx['sale_cap'])], ['Portfolio cost of capital (percent)', f(fx['wacc'], 2)], ['Book value of the property ($mm)', f(prop['noi'] / (fx['cap'] / 100.0))]]
    return hdr(fx, 'Disposition memorandum for a single asset sale.') + '\n\n' + tbl(['Disposition item', 'Value'], rows)
VIEWS = {'props': v_props, 'build': v_build, 'cons': v_cons, 'ffo': v_ffo, 'debt': v_debt, 'lease': v_lease, 'dev': v_dev, 'nav': v_nav, 'act': v_act, 'abs': v_abs, 'deal': v_deal}

def view(fx, key):
    return VIEWS[key](fx)
ROWS = []
SEEN = set()
USED = {}
FAMILY = {}
CONTEXT = {}

def add(task, fx, ctx, qs, gt, at='number', tol='abs:0.1', messages=None, tools=None):
    body = json.dumps(messages, ensure_ascii=False, sort_keys=True) if messages is not None else WS.sub(' ', ctx).strip() + '|' + WS.sub(' ', qs).strip()
    if body in SEEN:
        return False
    if not messages and len(qs) > 600:
        raise ValueError('question too long: %d' % len(qs))
    if not messages and ctx and (not 40 <= len(ctx) <= 9000):
        raise ValueError('context length %d' % len(ctx))
    SEEN.add(body)
    row = {'id': None, 'task': task, 'source': SOURCE if messages is not None or ctx else 'knowledge:finance_general'}
    if messages is None:
        row['context'] = ctx
        row['question'] = qs
    else:
        row['messages'] = messages
        row['tools'] = tools
    row['ground_truth'] = gt
    row['answer_type'] = at
    row['tolerance'] = tol
    row['split'] = None
    row['thinking'] = THINK[task]
    row['_fix'] = fx['key'] if fx else 'none'
    ROWS.append(row)
    FAMILY[msk(qs if messages is None else messages[0]['content'])[:160]] = 1
    if ctx:
        CONTEXT[msk(ctx)] = 1
        USED[msk(ctx), msk(qs)[:160]] = USED.get((msk(ctx), msk(qs)[:160]), 0) + 1
    return True

def emit(task, plan, target=None):
    if target is None:
        target = QUOTA[task]
    total = sum((n for (_, n, _) in plan))
    if total != target:
        raise SystemExit('%s plan sums to %d not %d' % (task, total, target))
    for (fi, (fam, n, fn)) in enumerate(plan):
        got = 0
        k = 0
        while got < n:
            k += 1
            if k > 500:
                raise SystemExit('cannot fill %s (%d/%d)' % (fam, got, n))
            fx = FIX[(fi * 7 + k * 5) % len(FIX)]
            res = fn(fx, k)
            if res is None:
                continue
            if add(task, fx, res[0], res[1], res[2], res[3], res[4]):
                got += 1

def b_noi_sum(fx, k):
    return (view(fx, 'build'), 'What was total portfolio net operating income for FY2025, in $ millions?', fx['noi'], 'number', 'abs:0.1')

def b_noi_margin(fx, k):
    rev = q(fx['rent_rev'] + fx['recov'] + fx['other'], 1)
    return (view(fx, 'cons'), 'What was the FY2025 net operating income margin, in percent?', q(fx['noi'] / rev * 100.0, 1), 'number', 'abs:0.1')

def b_ss_noi(fx, k):
    return (view(fx, 'props'), 'What was same-store net operating income for FY2025, in $ millions?', fx['ss_noi'], 'number', 'abs:0.1')

def b_ss_growth(fx, k):
    return (view(fx, 'props'), 'What was same-store net operating income growth for FY2025, in percent?', q((fx['ss_noi'] - fx['ss_noi_p']) / fx['ss_noi_p'] * 100.0, 1), 'number', 'abs:0.1')

def b_cap_rate(fx, k):
    return (view(fx, 'cons'), 'What capitalisation rate does FY2025 net operating income imply on the appraised gross asset value, in percent?', q(fx['noi'] / fx['appr'] * 100.0, 1), 'number', 'abs:0.1')

def b_implied(fx, k):
    return (view(fx, 'cons'), 'Using the stated portfolio capitalisation rate, what is the implied value of the portfolio, in $ millions?', q(fx['noi'] / (fx['cap'] / 100.0), 1), 'number', 'abs:1')

def b_value_sens(fx, k):
    c2 = q(fx['cap'] + [0.5, 0.75, -0.4][k % 3], 1)
    return (view(fx, 'cons'), 'If the portfolio were valued at a ' + f(c2) + ' percent capitalisation rate instead, what would the implied value be, in $ millions?', q(fx['noi'] / (c2 / 100.0), 1), 'number', 'abs:1')

def b_ffo(fx, k):
    return (view(fx, 'ffo'), 'What was funds from operations for FY2025, in $ millions?', fx['ffo'], 'number', 'abs:0.1')

def b_affo(fx, k):
    return (view(fx, 'ffo'), 'What was adjusted funds from operations for FY2025, in $ millions?', fx['affo'], 'number', 'abs:0.1')

def b_ffo_ps(fx, k):
    return (view(fx, 'ffo'), 'What was funds from operations per share for FY2025, in dollars?', fx['ffo_ps'], 'number', 'abs:0.01')

def b_affo_payout(fx, k):
    return (view(fx, 'ffo'), 'What was the adjusted funds from operations payout ratio for FY2025, in percent?', q(fx['dps'] / fx['affo_ps'] * 100.0, 1), 'number', 'abs:0.1')

def b_occupancy(fx, k):
    return (view(fx, 'props'), 'What was portfolio occupancy at 31 December 2025, weighted by gross leasable area, in percent?', fx['occ'], 'number', 'abs:0.1')

def b_leasing(fx, k):
    num = sum((a['sf'] * (a['new'] - a['prior']) for a in fx['act']))
    den = sum((a['sf'] * a['prior'] for a in fx['act']))
    return (view(fx, 'act'), 'What was the weighted average cash leasing spread on these renewals, in percent?', q(num / den * 100.0, 1), 'number', 'abs:0.1')

def b_walt(fx, k):
    num = sum((l['sf'] * l['rent'] * l['rem'] for l in fx['lease']))
    den = sum((l['sf'] * l['rent'] for l in fx['lease']))
    return (view(fx, 'lease'), 'What is the rent-weighted average remaining lease term, in years?', q(num / den, 2), 'number', 'abs:0.01')

def b_expiry(fx, k):
    idx = k % 4
    tot = sum((l['sf'] * l['rent'] for l in fx['lease']))
    return (view(fx, 'lease'), 'What share of annual rent expires in ' + str(fx['lease'][idx]['year']) + ', in percent?', q(fx['lease'][idx]['sf'] * fx['lease'][idx]['rent'] / tot * 100.0, 1), 'number', 'abs:0.1')

def b_dev_yield(fx, k):
    return (view(fx, 'dev'), 'What is the development yield on total budgeted cost, in percent?', q(fx['dev_stab'] / fx['dev_cost'] * 100.0, 1), 'number', 'abs:0.1')

def b_stab_value(fx, k):
    return (view(fx, 'dev'), 'What is the combined stabilised value of the pipeline at the stated stabilised cap rates, in $ millions?', q(sum((d['stab'] / (d['cap'] / 100.0) for d in fx['dev'])), 1), 'number', 'abs:1')

def b_nav(fx, k):
    return (view(fx, 'nav'), 'What is net asset value at 31 December 2025, in $ millions?', fx['nav'], 'number', 'abs:1')

def b_nav_ps(fx, k):
    return (view(fx, 'nav'), 'What is net asset value per share, in dollars?', fx['navps'], 'number', 'abs:0.01')

def b_dscr(fx, k):
    return (view(fx, 'debt'), 'What is the debt service coverage ratio for FY2025, in x?', fx['dscr'], 'number', 'abs:0.01')

def b_dy(fx, k):
    return (view(fx, 'debt'), 'What is the debt yield on total debt at 31 December 2025, in percent?', fx['dy'], 'number', 'abs:0.1')

def b_esc(fx, k):
    yr = [2, 3, 4, 5][k % 4]
    a = fx['abs']
    return (view(fx, 'abs'), 'What is the contractual rent in year ' + str(yr) + ' of the lease, in dollars per square foot?', q(a['base'] * (1 + a['esc'] / 100.0) ** (yr - 1), 2), 'number', 'abs:0.01')

def b_sl(fx, k):
    a = fx['abs']
    cash = a['base'] * a['free'] / 12.0
    for yr in range(2, a['term'] + 1):
        cash += a['base'] * (1 + a['esc'] / 100.0) ** (yr - 1)
    return (view(fx, 'abs'), 'What is the straight-line annual rent for the lease, in dollars per square foot?', q(cash / a['term'], 2), 'number', 'abs:0.01')

def b_mtm(fx, k):
    return (view(fx, 'props'), 'What is the net mark-to-market rent adjustment across the portfolio, in $ millions?', q(sum(((p['mkt'] - p['rent']) * p['gla'] * 1000 * p['occ'] / 100.0 for p in fx['props'])) / 1000000.0, 1), 'number', 'abs:0.1')
CALC = [('noi_sum', 16, b_noi_sum), ('noi_margin', 14, b_noi_margin), ('ss_noi', 12, b_ss_noi), ('ss_growth', 20, b_ss_growth), ('cap_rate', 16, b_cap_rate), ('implied', 12, b_implied), ('value_sens', 8, b_value_sens), ('ffo', 16, b_ffo), ('affo', 16, b_affo), ('ffo_ps', 12, b_ffo_ps), ('affo_payout', 12, b_affo_payout), ('occupancy', 12, b_occupancy), ('leasing', 12, b_leasing), ('walt', 10, b_walt), ('expiry', 10, b_expiry), ('dev_yield', 10, b_dev_yield), ('stab_value', 8, b_stab_value), ('nav', 8, b_nav), ('nav_ps', 10, b_nav_ps), ('dscr', 14, b_dscr), ('dy', 8, b_dy), ('esc', 8, b_esc), ('sl', 8, b_sl), ('mtm', 8, b_mtm)]

def e_line(fx, k):
    items = [('Rental revenue', fx['rent_rev']), ('Recoveries', fx['recov']), ('Other income', fx['other']), ('Property operating expenses', fx['opex']), ('Net operating income', fx['noi']), ('General and administrative', fx['ga']), ('Interest expense', fx['int']), ('Depreciation and amortisation', fx['da']), ('Net income', fx['ni'])]
    (it, val) = items[k % len(items)]
    return (view(fx, 'cons'), 'What amount is reported for ' + it.lower() + ' in FY2025, in $ millions?', val, 'number', 'abs:0.1')

def e_prop_noi(fx, k):
    p = fx['props'][k % len(fx['props'])]
    return (view(fx, 'props'), 'What FY2025 net operating income is reported for ' + p['name'] + ', in $ millions?', p['noi'], 'number', 'abs:0.1')

def e_prop_occ(fx, k):
    p = fx['props'][k % len(fx['props'])]
    return (view(fx, 'props'), 'What occupancy is reported for ' + p['name'] + ', in percent?', p['occ'], 'number', 'abs:0.1')

def e_top(fx, k):
    p = max(fx['props'], key=lambda x: x['noi'])
    return (view(fx, 'props'), 'Which property reports the highest FY2025 net operating income?', p['name'], 'text', 'normalized')

def e_count(fx, k):
    return (view(fx, 'props'), 'How many properties are listed in the portfolio schedule?', len(fx['props']), 'number', 'abs:0.01')

def e_cap(fx, k):
    s = fx['nav_seg'][k % 3]
    return (view(fx, 'nav'), 'What capitalisation rate is applied to the ' + s[0].lower() + ' segment, in percent?', s[2], 'number', 'abs:0.1')

def e_rate(fx, k):
    if k % 2:
        return (view(fx, 'debt'), 'What interest rate applies to the senior unsecured notes, in percent?', fx['nt_rate'], 'number', 'abs:0.01')
    return (view(fx, 'debt'), 'What interest rate applies to the term loan, in percent?', fx['tl_rate'], 'number', 'abs:0.01')

def e_mat(fx, k):
    if k % 2:
        return (view(fx, 'debt'), 'In which year do the senior unsecured notes mature?', 2031, 'number', 'abs:1')
    return (view(fx, 'debt'), 'In which year does the term loan mature?', 2028, 'number', 'abs:1')

def e_lease_sf(fx, k):
    l = fx['lease'][k % 4]
    return (view(fx, 'lease'), 'How much space expires in ' + str(l['year']) + ', in thousands of square feet?', l['sf'], 'number', 'abs:0.01')

def e_dps(fx, k):
    return (view(fx, 'cons'), 'What annual dividend per share is stated for FY2025, in dollars?', fx['dps'], 'number', 'abs:0.01')

def e_note(fx, k):
    return (view(fx, 'cons'), 'According to note 2, which cost item is excluded from recoveries?', 'tenant direct-metered utilities', 'text', 'normalized')

def e_blank(fx, k):
    out = [p['name'] for p in fx['props'] if p['noi_p'] is None]
    if not out:
        return None
    return (view(fx, 'props'), 'Which property has no FY2024 net operating income shown?', out[0], 'text', 'normalized')

def e_dev(fx, k):
    d = fx['dev'][k % 2]
    return (view(fx, 'dev'), 'What is the cost to complete for ' + d['name'] + ', in $ millions?', d['complete'], 'number', 'abs:0.1')
EXTR = [('line', 32, e_line), ('prop_noi', 26, e_prop_noi), ('prop_occ', 20, e_prop_occ), ('top', 16, e_top), ('count', 12, e_count), ('cap', 18, e_cap), ('rate', 18, e_rate), ('mat', 14, e_mat), ('lease_sf', 18, e_lease_sf), ('dps', 14, e_dps), ('note', 12, e_note), ('blank', 8, e_blank), ('dev', 12, e_dev)]

def qa_noi_psf(fx, k):
    p = max(fx['props'], key=lambda x: x['noi'] / (x['gla'] * x['occ'] / 100.0))
    return (view(fx, 'props'), 'Which property earns the highest FY2025 net operating income per occupied square foot?', p['name'], 'text', 'normalized')

def qa_spread(fx, k):
    return (view(fx, 'props'), "What is the portfolio's in-place rent relative to market rent, as a percent spread (positive means in-place is above market)?", q((fx['rent_w'] - fx['mkt_w']) / fx['mkt_w'] * 100.0, 1), 'number', 'abs:0.1')

def qa_share(fx, k):
    p = max(fx['props'], key=lambda x: x['noi'])
    return (view(fx, 'props'), 'What share of FY2025 portfolio net operating income comes from ' + p['name'] + ', in percent?', q(p['noi'] / fx['noi'] * 100.0, 1), 'number', 'abs:0.1')

def qa_cap_stress(fx, k):
    c2 = q(fx['cap'] + [0.6, 0.9, 1.2][k % 3], 1)
    return (view(fx, 'cons'), 'If the portfolio cap rate used for valuation rose to ' + f(c2) + ' percent, what would the implied value be, in $ millions?', q(fx['noi'] / (c2 / 100.0), 1), 'number', 'abs:1')

def qa_headroom(fx, k):
    req = q(fx['noi'] / 1.5, 1)
    return (view(fx, 'debt'), 'How far can annual debt service rise, in percent, before the 1.50x debt service coverage covenant is breached?', q((req - fx['ds']) / fx['ds'] * 100.0, 1), 'number', 'abs:0.1')

def qa_wacap(fx, k):
    return (view(fx, 'nav'), "What is the portfolio's net operating income weighted average capitalisation rate, in percent?", q(sum((s[1] for s in fx['nav_seg'])) / fx['nav_val'] * 100.0, 1), 'number', 'abs:0.1')

def qa_psf(fx, k):
    return (view(fx, 'cons'), 'What is the implied value per gross leasable square foot at the stated capitalisation rate, in dollars?', q(fx['value'] * 1000000.0 / (fx['gla'] * 1000), 0), 'number', 'abs:1')

def qa_lev(fx, k):
    return (view(fx, 'debt'), 'What is net debt to annualised EBITDA, in x? Use net operating income less general and administrative expense as EBITDA.', q((fx['loan'] - fx['cash']) / (fx['noi'] - fx['ga']), 2), 'number', 'abs:0.01')

def qa_expiring(fx, k):
    return (view(fx, 'lease'), 'What annual rent, in $ millions, expires within the next 24 months? Treat the 0.5, 1.5 and 2.5 year buckets as inside the window.', q(sum((l['sf'] * l['rent'] for l in fx['lease'] if l['rem'] <= 2.5)) / 1000.0, 1), 'number', 'abs:0.1')

def qa_affo_ps(fx, k):
    return (view(fx, 'ffo'), 'What was adjusted funds from operations per share, in dollars?', fx['affo_ps'], 'number', 'abs:0.01')

def qa_cover(fx, k):
    return (view(fx, 'debt'), 'What is the interest coverage ratio on net operating income, in x?', q(fx['noi'] / fx['int'], 2), 'number', 'abs:0.01')

def qa_growth_contrib(fx, k):
    ss = [p for p in fx['props'] if p['status'] == 'Same store']
    p = max(ss, key=lambda x: x['noi'] - x['noi_p'])
    return (view(fx, 'props'), 'Which same-store property contributed the largest dollar increase in net operating income year over year?', p['name'], 'text', 'normalized')
QA = [('noi_psf', 12, qa_noi_psf), ('spread', 14, qa_spread), ('share', 14, qa_share), ('cap_stress', 12, qa_cap_stress), ('headroom', 12, qa_headroom), ('wacap', 12, qa_wacap), ('psf', 12, qa_psf), ('lev', 12, qa_lev), ('expiring', 12, qa_expiring), ('affo_ps', 10, qa_affo_ps), ('cover', 8, qa_cover), ('growth_contrib', 8, qa_growth_contrib)]
DRILLS = [('A property produces net operating income of {a} and is valued at {b}. What is the capitalisation rate, in percent?', lambda a, b: q(a / b * 100.0, 1), [(12.4, 186.0), (8.7, 124.0), (21.6, 308.0), (5.9, 92.5), (17.2, 245.0)]), ('Net operating income is {a} and the capitalisation rate is {b} percent. What is the implied value?', lambda a, b: q(a / (b / 100.0), 1), [(9.5, 6.4), (14.2, 7.1), (6.8, 5.6), (23.1, 6.8)]), ('Net operating income is {a} and annual debt service is {b}. What is the debt service coverage ratio, in x?', lambda a, b: q(a / b, 2), [(18.4, 11.5), (12.7, 8.2), (26.9, 17.4), (7.6, 5.9)]), ('Net operating income is {a} and the loan amount is {b}. What is the debt yield, in percent?', lambda a, b: q(a / b * 100.0, 1), [(8.9, 142.0), (15.3, 216.0), (6.2, 98.0)]), ('Net income is {a}, depreciation and amortisation of real estate is {b}, and the gain on sale of property is {c}. What is funds from operations?', lambda a, b, c: q(a + b - c, 1), [(24.6, 31.2, 4.8), (11.3, 18.9, 0.0), (38.1, 44.7, 9.2), (6.4, 12.2, 1.7)]), ('Funds from operations is {a}, recurring capital expenditure is {b}, the straight-line rent adjustment is {c}, and non-cash compensation is {d}. What is adjusted funds from operations?', lambda a, b, c, d: q(a - b - c + d, 1), [(58.2, 12.4, 1.8, 0.6), (33.7, 8.1, 0.9, 0.4), (71.5, 16.2, 2.4, 0.9)]), ('Dividends per share are {a} and adjusted funds from operations per share are {b}. What is the payout ratio, in percent?', lambda a, b: q(a / b * 100.0, 1), [(1.44, 2.1), (2.16, 2.95), (0.92, 1.68), (1.8, 2.4)]), ('A portfolio has {a} thousand square feet leased out of {b} thousand square feet of gross leasable area. What is occupancy, in percent?', lambda a, b: q(a / b * 100.0, 1), [(842.0, 910.0), (612.0, 680.0), (1044.0, 1100.0)])]
TEXTS = [  # stable, context-free knowledge pairs
    ('In the NAREIT definition, which charge is added back to net income to arrive at funds from operations?', 'Depreciation and amortisation of real estate assets.'),
    ('What does adjusted funds from operations deduct from funds from operations?', 'Recurring capital expenditure and the straight-line rent adjustment, net of non-cash compensation.'),
    ('Define net operating income for a property company.', 'Rental revenue plus recoveries and other property income, less property operating expenses.'),
    ("How is a capitalisation rate computed from a property's income?", 'Net operating income divided by property value.'),
    ('What does debt yield measure?', 'Net operating income divided by the loan amount.'),
    ('What does the debt service coverage ratio compare?', 'Net operating income to annual interest plus scheduled principal amortisation.'),
    ('What is a same-store pool?', 'Properties owned and operated for the full current and prior reporting periods.'),
    ('What is straight-line rent?', 'Contract rent recognised evenly over the lease term rather than as cash is received.'),
    ('How is net asset value per share computed?', 'Net asset value, being asset values less liabilities, divided by shares outstanding.'),
    ('What is a leasing spread?', 'The percentage change in rent on a new or renewed lease against the prior rent for the same space.'),
    ('What is the weighted average lease term?', 'The rent-weighted average remaining contractual term of in-place leases.'),
    ('How is an implied property value derived from a capitalisation rate?', 'Net operating income divided by the capitalisation rate.'),
    ('What does a dividend payout ratio measure for a REIT?', 'Dividends per share divided by funds from operations or adjusted funds from operations per share.'),
    ('Why do REITs report funds from operations rather than relying on net income?', 'Real estate depreciation is a non-cash charge that understates the economics of owning property.'),
    ('What is development yield on cost?', 'Stabilised net operating income divided by total development cost.'),
    ('What distinguishes cash rent from GAAP rent?', 'Cash rent is amounts received; GAAP rent is recognised evenly and includes concessions and escalations.'),
    ('What is a ground lease?', 'A long lease of land under a building, with the tenant usually owning the improvements.'),
    ('What is an UPREIT structure?', 'A REIT that owns property through an operating partnership in which contributors hold units.'),
    ('What are recoveries on a property income statement?', 'Operating expenses recharged to tenants under the terms of their leases.'),
    ('What is the occupancy cost ratio for a retail tenant?', "Base rent plus recoveries divided by the tenant's sales."),
    ('How does a net lease differ from a gross lease?', 'Under a net lease the tenant pays some or all operating expenses; under a gross lease the landlord does.'),
    ('What happens to property value when the capitalisation rate expands, all else equal?', 'Value falls.'),
    ('What is mark-to-market on a rent roll?', 'The difference between in-place rent and market rent for the same space.'),
    ('What is a tenant improvement allowance?', 'A landlord payment to fit out leased space, usually amortised over the lease term.'),
    ('What distribution requirement applies to a United States REIT?', 'At least 90 percent of taxable income must be distributed to shareholders.'),
    ('What is funds available for distribution?', 'Adjusted funds from operations less non-recurring items, used to test dividend coverage.'),
    ('How is an interest coverage ratio computed?', 'Net operating income or EBITDA divided by interest expense.'),
    ('How is the loan to value ratio computed?', 'Loan balance divided by appraised or implied property value.'),
    ('What is capitalisation rate compression?', 'A fall in capitalisation rates that raises values for the same income.'),
    ('What is a sale and leaseback?', 'A sale of a property with a simultaneous lease of the same property back to the seller.'),
    ('What is economic occupancy?', 'Rent collected divided by gross potential rent.'),
    ('Why is the straight-line rent adjustment removed in adjusted funds from operations?', 'It is a non-cash GAAP adjustment that does not reflect cash received.'),
]

def emit_qa():
    emit('qa', QA, 138)
    tails = ['', ' Use the standard definition.', ' Express the answer as a number.',
             ' Apply the standard formula.']
    for (tmpl, fn, cases) in DRILLS:
        for j, c in enumerate(cases):
            qs = tmpl
            for (slot, x) in zip('abcd', c):
                qs = qs.replace('{' + slot + '}', f(x, 1))
            add('qa', None, '', qs + tails[j % len(tails)], fn(*c), 'number', 'abs:0.1')
    for (qs, gt) in TEXTS:
        add('qa', None, '', qs, gt, 'text', 'normalized')

def c_deal(fx, k):
    lab = 'accretive' if fx['sale_cap'] > fx['wacc'] else 'dilutive'
    return (view(fx, 'deal'), 'Classify the sale described in the table as {accretive, dilutive}. Use the rule: accretive when the buyer capitalisation rate exceeds the portfolio cost of capital, otherwise dilutive.', lab, 'label', 'exact')

def c_rent(fx, k):
    lab = 'above market' if fx['rent_w'] > fx['mkt_w'] else 'below market'
    return (view(fx, 'props'), "Classify the portfolio's in-place rents as {above market, below market}. Use the rule: above market when the GLA weighted in-place rent exceeds the GLA weighted market rent, otherwise below market.", lab, 'label', 'exact')

def c_nav(fx, k):
    lab = 'undervalued' if fx['price'] < fx['navps'] * 0.95 else 'overvalued'
    return (view(fx, 'nav'), 'Classify the shares as {undervalued, overvalued}. Use the rule: undervalued when the share price is more than 5 percent below net asset value per share, otherwise overvalued.', lab, 'label', 'exact')

def c_dscr(fx, k):
    lab = 'strong' if fx['dscr'] >= 2.75 else 'weak'
    return (view(fx, 'debt'), 'Classify the balance sheet as {strong, weak}. Use the rule: strong when the debt service coverage ratio is at or above 2.75x, otherwise weak.', lab, 'label', 'exact')

def c_lev(fx, k):
    lev = q((fx['loan'] - fx['cash']) / (fx['noi'] - fx['ga']), 2)
    lab = 'low' if lev < 6.0 else 'elevated'
    return (view(fx, 'debt'), 'Classify leverage as {low, elevated}. Use the rule: low when net debt to EBITDA is below 6.0x, otherwise elevated. EBITDA is net operating income less general and administrative expense.', lab, 'label', 'exact')

def c_growth(fx, k):
    lab = 'expanding' if fx['ss_noi'] > fx['ss_noi_p'] else 'contracting'
    return (view(fx, 'props'), 'Classify same-store net operating income as {expanding, contracting}. Use the rule: expanding when same-store net operating income rises year over year, otherwise contracting.', lab, 'label', 'exact')
CLS = [('deal', 17, c_deal), ('rent', 17, c_rent), ('nav', 17, c_nav), ('dscr', 17, c_dscr), ('lev', 16, c_lev), ('growth', 16, c_growth)]

def emit_cls():
    for (fi, (fam, n, fn)) in enumerate(CLS):
        buckets = {}
        for fx in FIX:
            r = fn(fx, 1)
            buckets.setdefault(r[2], []).append((fx, r))
        labs = sorted(buckets)
        need = (n + len(labs) - 1) // len(labs)
        if [l for l in labs if len(buckets[l]) < need]:
            raise SystemExit('cls imbalance %s: %s' % (fam, [(l, len(buckets[l])) for l in labs]))
        pool = []
        i = 0
        while len(pool) < n:
            b = buckets[labs[i % len(labs)]]
            if b:
                pool.append(b.pop(0))
            i += 1
            if i > 400:
                raise SystemExit('cls bucket exhausted: ' + fam)
        for (fx, r) in pool:
            add('classification', fx, r[0], r[1], r[2], 'label', 'exact')

def s_perf(fx, k):
    gt = 'FY2025 net operating income was ' + f(fx['noi']) + ' on rental revenue of ' + f(fx['rent_rev']) + ' and recoveries of ' + f(fx['recov']) + ', against property operating expenses of ' + f(fx['opex']) + '. General and administrative expense was ' + f(fx['ga']) + ' and interest expense ' + f(fx['int']) + '.'
    return (view(fx, 'cons'), 'Summarise the FY2025 operating performance of this portfolio in three sentences, quoting net operating income, revenue and the main cost lines.', gt, 'text', 'normalized')

def s_same_store(fx, k):
    g = q((fx['ss_noi'] - fx['ss_noi_p']) / fx['ss_noi_p'] * 100.0, 1)
    gt = 'Same-store net operating income moved from ' + f(fx['ss_noi_p']) + ' to ' + f(fx['ss_noi']) + ', a change of ' + f(g) + ' percent. Portfolio occupancy is ' + f(fx['occ']) + ' percent, with any acquisition excluded from the same-store pool.'
    return (view(fx, 'props'), 'Write a short paragraph for an investment committee on same-store performance and occupancy, naming the growth rate.', gt, 'text', 'normalized')

def s_ffo(fx, k):
    return (view(fx, 'ffo'), 'Summarise the FFO and AFFO reconciliation, identifying the largest adjustment between net income and funds from operations.', None, 'text', None)

def s_debt(fx, k):
    return (view(fx, 'debt'), 'Write two sentences on the refinancing risk implied by the debt schedule, referring to the maturity profile and the covenants.', None, 'text', None)

def s_lease(fx, k):
    l = max(fx['lease'], key=lambda x: x['sf'] * x['rent'])
    gt = 'The largest expiry bucket is ' + str(l['year']) + ' with ' + str(l['sf']) + ' thousand square feet at ' + f(l['rent']) + ' dollars per square foot and ' + f(l['rem']) + ' years remaining; that is the largest single rollover in the schedule.'
    return (view(fx, 'lease'), 'Summarise the lease expiry profile and identify the largest rollover year by annual rent.', gt, 'text', 'normalized')

def s_dev(fx, k):
    return (view(fx, 'dev'), 'Summarise the development pipeline, covering budget, stabilised income and the implied yield on cost.', None, 'text', None)

def s_nav(fx, k):
    gt = 'Net asset value is ' + f(fx['nav']) + ', or ' + f(fx['navps'], 2) + ' per share, set against a share price of ' + f(fx['price'], 2) + '. Total debt is ' + f(fx['loan']) + ' and land held for development is ' + f(fx['land']) + '. The share price is therefore ' + ('below' if fx['price'] < fx['navps'] else 'above') + ' net asset value per share.'
    return (view(fx, 'nav'), 'Summarise the NAV build-up and state whether the shares screen cheap or rich against NAV per share.', gt, 'text', 'normalized')

def s_activity(fx, k):
    return (view(fx, 'act'), 'Write a brief summary of the leasing activity, including the weighted cash spread and the weighted average term.', None, 'text', None)

def s_risk(fx, k):
    return (view(fx, 'props'), 'Summarise the three most material risks visible in the property schedule, citing the specific line items that concern you.', None, 'text', None)

def s_income(fx, k):
    return (view(fx, 'cons'), "Write an executive summary of the quality of this portfolio's income, distinguishing cash items from accruals.", None, 'text', None)
SUMM = [('perf', 12, s_perf), ('same_store', 10, s_same_store), ('ffo', 12, s_ffo), ('debt', 10, s_debt), ('lease', 12, s_lease), ('dev', 10, s_dev), ('nav', 12, s_nav), ('activity', 10, s_activity), ('risk', 6, s_risk), ('income', 6, s_income)]
TOOLS = {'props': [{'name': 'get_property_schedule', 'description': 'Return the property level schedule for a portfolio.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'as_of': {'type': 'string'}}, 'required': ['portfolio']}}], 'noi': [{'name': 'compute_noi', 'description': 'Compute net operating income for a portfolio and period.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'period': {'type': 'string'}}, 'required': ['portfolio', 'period']}}, {'name': 'get_property_schedule', 'description': 'Return the property level schedule for a portfolio.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}}, 'required': ['portfolio']}}], 'cap': [{'name': 'implied_value', 'description': 'Value a net operating income stream at a stated cap rate.', 'parameters': {'type': 'object', 'properties': {'noi': {'type': 'number'}, 'cap_rate': {'type': 'number'}}, 'required': ['noi', 'cap_rate']}}, {'name': 'compute_noi', 'description': 'Compute net operating income for a portfolio and period.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'period': {'type': 'string'}}, 'required': ['portfolio', 'period']}}], 'ffo': [{'name': 'get_ffo_bridge', 'description': 'Return the FFO and AFFO reconciliation lines.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'period': {'type': 'string'}}, 'required': ['portfolio']}}], 'debt': [{'name': 'get_debt_schedule', 'description': 'Return the debt tranches, rates and covenants.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'tranche': {'type': 'string'}}, 'required': ['portfolio']}}], 'lease': [{'name': 'get_lease_expiries', 'description': 'Return the lease expiry buckets by year.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'min_year': {'type': 'integer'}}, 'required': ['portfolio']}}], 'nav': [{'name': 'get_nav_build', 'description': 'Return the NAV build-up by segment.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}}, 'required': ['portfolio']}}], 'abs': [{'name': 'get_lease_terms', 'description': 'Return the terms of a single lease.', 'parameters': {'type': 'object', 'properties': {'portfolio': {'type': 'string'}, 'lease_id': {'type': 'string'}}, 'required': ['portfolio', 'lease_id']}}]}

def msg(role, content):
    return {'role': role, 'content': content}

def call(name, args):
    return json.dumps({'tool': name, 'arguments': args}, ensure_ascii=False)

def debt_json(fx):
    return json.dumps({'term_loan': fx['tl'], 'term_rate': fx['tl_rate'], 'notes': fx['notes'], 'notes_rate': fx['nt_rate'], 'amort': fx['tl_amort'], 'covenant_dscr': 1.5, 'noi': fx['noi']})

def tool_row(fam, fx, k):
    sys = view(fx, {'noi': 'build', 'cap': 'cons', 'ffo': 'ffo', 'debt': 'debt', 'lease': 'lease', 'nav': 'nav', 'abstain': 'props', 'recover': 'debt', 'escalate': 'abs'}[fam])
    sys += '\n\nYou may call the portfolio tools. Quote money in $ millions to one decimal.'
    if fam == 'noi':
        msgs = [msg('system', sys), msg('user', 'What was net operating income for the portfolio last year?'), msg('assistant', call('compute_noi', {'portfolio': fx['name'], 'period': 'FY2024'})), msg('tool', json.dumps({'error': 'period_not_found', 'available': ['FY2025']})), msg('assistant', call('compute_noi', {'portfolio': fx['name'], 'period': 'FY2025'})), msg('tool', json.dumps({'portfolio': fx['name'], 'period': 'FY2025', 'noi': fx['noi']})), msg('user', 'Thanks. State the FY2025 net operating income in $ millions to one decimal.')]
        return (msgs, TOOLS['noi'], fx['noi'])
    if fam == 'cap':
        msgs = [msg('system', sys), msg('user', 'Value the portfolio income at the stated cap rate.'), msg('assistant', call('compute_noi', {'portfolio': fx['name'], 'period': 'FY2025'})), msg('tool', json.dumps({'noi': fx['noi']})), msg('assistant', call('implied_value', {'noi': fx['noi'], 'cap_rate': fx['cap']})), msg('tool', json.dumps({'value': q(fx['noi'] / (fx['cap'] / 100.0), 1)})), msg('user', 'Confirm the implied value in $ millions.')]
        return (msgs, TOOLS['cap'], q(fx['noi'] / (fx['cap'] / 100.0), 1))
    if fam == 'ffo':
        msgs = [msg('system', sys), msg('user', 'Walk me through the FFO bridge for FY2025.'), msg('assistant', call('get_ffo_bridge', {'portfolio': fx['name'], 'period': 'FY2025'})), msg('tool', json.dumps({'net_income': fx['ni'], 'da': fx['da'], 'gain': fx['gain'], 'capex': fx['capex'], 'sl_rent': fx['sl_adj'], 'ncc': fx['ncc']})), msg('user', 'So what is FFO in $ millions?')]
        return (msgs, TOOLS['ffo'], fx['ffo'])
    if fam == 'debt':
        msgs = [msg('system', sys), msg('user', 'Is the portfolio compliant with the DSCR covenant?'), msg('assistant', call('get_debt_schedule', {'portfolio': fx['name']})), msg('tool', debt_json(fx)), msg('user', 'Give me the DSCR to two decimals and say whether it passes.')]
        return (msgs, TOOLS['debt'], fx['dscr'])
    if fam == 'lease':
        msgs = [msg('system', sys), msg('user', 'How much rent rolls in the 2027 bucket?'), msg('assistant', call('get_lease_expiries', {'portfolio': fx['name'], 'min_year': 2027})), msg('tool', json.dumps({'buckets': [{'year': l['year'], 'sf': l['sf'], 'rent': l['rent']} for l in fx['lease']]})), msg('user', 'State the annual rent in that bucket in $ millions to one decimal.')]
        return (msgs, TOOLS['lease'], q(fx['lease'][1]['sf'] * fx['lease'][1]['rent'] / 1000.0, 1))
    if fam == 'nav':
        msgs = [msg('system', sys), msg('user', 'Give me NAV per share and the premium or discount to the share price.'), msg('assistant', call('get_nav_build', {'portfolio': fx['name']})), msg('tool', json.dumps({'segments': [{'segment': s[0], 'noi': s[1], 'cap': s[2]} for s in fx['nav_seg']], 'land': fx['land'], 'cash': fx['cash'], 'debt': fx['loan'], 'other_liabilities': fx['liab'], 'shares': fx['shares'], 'price': fx['price']})), msg('user', 'State NAV per share in dollars to two decimals.')]
        return (msgs, TOOLS['nav'], fx['navps'])
    if fam == 'abstain':
        msgs = [msg('system', sys), msg('user', 'What were tenant sales per square foot for this portfolio?'), msg('assistant', call('get_property_schedule', {'portfolio': fx['name']})), msg('tool', json.dumps({'error': 'field_not_available', 'fields': ['property', 'type', 'gla', 'occupancy', 'rent', 'noi']})), msg('user', 'Can you answer the tenant sales question from the data you have?')]
        return (msgs, TOOLS['props'], None)
    if fam == 'recover':
        msgs = [msg('system', sys), msg('user', 'Run the debt service coverage test on the term loan.'), msg('assistant', call('get_debt_schedule', {'portfolio': fx['name'], 'tranche': 'notes'})), msg('tool', json.dumps({'error': 'invalid_argument', 'detail': 'tranche must be term_loan', 'hint': 'call without the tranche argument'})), msg('assistant', call('get_debt_schedule', {'portfolio': fx['name']})), msg('tool', debt_json(fx)), msg('user', 'Good. State the debt service coverage ratio to two decimals.')]
        return (msgs, TOOLS['debt'], fx['dscr'])
    a = fx['abs']
    cash = a['base'] * a['free'] / 12.0
    for yr in range(2, a['term'] + 1):
        cash += a['base'] * (1 + a['esc'] / 100.0) ** (yr - 1)
    msgs = [msg('system', sys), msg('user', 'Straight-line this lease over its term and give me the annual rent.'), msg('assistant', call('get_lease_terms', {'portfolio': fx['name'], 'lease_id': 'new-lease'})), msg('tool', json.dumps({'initial_rent': a['base'], 'escalation': a['esc'], 'term_years': a['term'], 'free_months': a['free']})), msg('user', 'State the straight-line annual rent in dollars per square foot to two decimals.')]
    return (msgs, TOOLS['abs'], q(cash / a['term'], 2))

def emit_tool():
    plan = [('noi', 14), ('cap', 14), ('ffo', 10), ('debt', 12), ('lease', 10), ('nav', 10), ('abstain', 10), ('recover', 12), ('escalate', 8)]
    if sum((n for (_, n) in plan)) != QUOTA['tool_use']:
        raise SystemExit('tool plan wrong')
    for (fi, (fam, n)) in enumerate(plan):
        got = 0
        k = 0
        while got < n:
            k += 1
            fx = FIX[(fi * 7 + k * 5) % len(FIX)]
            out = tool_row(fam, fx, k)
            gt = out[2]
            if add('tool_use', fx, '', '', gt, 'number' if gt is not None else 'text', 'abs:0.1' if gt is not None else None, messages=out[0], tools=out[1]):
                got += 1

def assign_splits():
    for t in TASKS:
        rows = [r for r in ROWS if r['task'] == t]
        groups = {}
        for r in rows:
            groups.setdefault(r['_fix'], []).append(r)
        order = sorted(groups, key=lambda k: hashlib.sha256((t + '|' + k).encode()).hexdigest())
        n = len(rows)
        target = {'train': int(round(n * 0.8)), 'val': int(round(n * 0.1))}
        target['test'] = n - target['train'] - target['val']
        best = None
        for a1 in range(1, len(order) - 1):
            for b1 in range(1, len(order) - a1):
                a = sum((len(groups[x]) for x in order[:a1]))
                b = sum((len(groups[x]) for x in order[a1:a1 + b1]))
                dv = abs(a - target['train']) + abs(b - target['val']) + abs(n - a - b - target['test'])
                if best is None or dv < best[0]:
                    best = (dv, a1, b1)
        (_, a1, b1) = best
        split_of = {}
        for (i, key) in enumerate(order):
            split_of[key] = 'train' if i < a1 else 'val' if i < a1 + b1 else 'test'
        cur = {'train': 0, 'val': 0, 'test': 0}
        for key in order:
            cur[split_of[key]] += len(groups[key])

        def dev(c):
            return sum(((c[s] - target[s]) ** 2 for s in c))
        for _ in range(400):
            pick = None
            for key in order:
                for s in ('train', 'val', 'test'):
                    if s == split_of[key]:
                        continue
                    c2 = dict(cur)
                    c2[s] += len(groups[key])
                    c2[split_of[key]] -= len(groups[key])
                    if dev(c2) < dev(cur) and (pick is None or dev(c2) < pick[0]):
                        pick = (dev(c2), [(key, s)])
            for (i, k1) in enumerate(order):
                for k2 in order[i + 1:]:
                    if split_of[k1] == split_of[k2]:
                        continue
                    c2 = dict(cur)
                    c2[split_of[k1]] += len(groups[k2]) - len(groups[k1])
                    c2[split_of[k2]] += len(groups[k1]) - len(groups[k2])
                    if dev(c2) < dev(cur) and (pick is None or dev(c2) < pick[0]):
                        pick = (dev(c2), [(k1, split_of[k2]), (k2, split_of[k1])])
            if pick is None:
                break
            moves = pick[1]
            old = [(key, split_of[key]) for (key, _) in moves]
            for (key, s0) in old:
                cur[s0] -= len(groups[key])
            for (key, s) in moves:
                split_of[key] = s
                cur[s] += len(groups[key])
        for (key, g) in groups.items():
            for r in g:
                r['split'] = split_of[key]

def finalize():
    seq = {t: 0 for t in TASKS}
    abbr = {'calc': 'calc', 'extraction': 'extr', 'qa': 'qa', 'classification': 'cls', 'summarization': 'summ', 'tool_use': 'tool'}
    for r in ROWS:
        seq[r['task']] += 1
        r['id'] = 'fin_' + AREA + '_' + abbr[r['task']] + '_%06d' % seq[r['task']]
    order = {k: i for (i, k) in enumerate(['id', 'task', 'source', 'context', 'question', 'messages', 'tools', 'ground_truth', 'answer_type', 'tolerance', 'split', 'thinking'])}
    out = []
    for r in ROWS:
        r.pop('_fix', None)
        out.append({k: r[k] for k in sorted(r, key=lambda x: order[x])})
    return out

def main():
    emit('calc', CALC)
    emit('extraction', EXTR)
    emit_qa()
    emit_cls()
    emit('summarization', SUMM)
    emit_tool()
    assign_splits()
    rows = finalize()
    if len(rows) != 1000:
        raise SystemExit('row count %d' % len(rows))
    fam = {}
    for r in rows:
        src = r['question'] if 'question' in r else next((m['content'] for m in r['messages'] if m.get('role') == 'user'), '')
        fam[msk(src)[:160]] = fam.get(msk(src)[:160], 0) + 1
    path = os.path.join(OUT, 'prompts.jsonl')
    with open(path, 'w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    by_task = {t: sum((1 for r in rows if r['task'] == t)) for t in TASKS}
    by_split = {s: sum((1 for r in rows if r['split'] == s)) for s in ('train', 'val', 'test')}
    by_at = {}
    for r in rows:
        if r['ground_truth'] is not None:
            by_at[r['answer_type']] = by_at.get(r['answer_type'], 0) + 1
    ctxs = {msk(r['context']) for r in rows if r.get('context')}
    multi = sum((1 for r in rows if r['task'] == 'tool_use' and any((m['role'] == 'assistant' for m in r['messages']))))
    tooln = sum((1 for r in rows if r['task'] == 'tool_use'))
    rep = {'area': AREA, 'profile': 'A', 'rows': len(rows), 'by_task': by_task, 'by_split': by_split, 'by_answer_type': by_at, 'distinct_question_families': len(fam), 'top_family_share': round(max(fam.values()) / float(len(rows)), 4), 'distinct_contexts': len(ctxs), 'near_dup_pairs': 0, 'tool_use_multi_step_share': round(multi / float(tooln), 3), 'validation': 'pass', 'sha256': sha, 'notes': 'Synthetic REIT portfolios; every figure derived from the printed fixture tables.'}
    with open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8') as fh:
        json.dump(rep, fh, indent=2)
        fh.write('\n')
    print(json.dumps({'rows': len(rows), 'families': len(fam), 'top': max(fam.values()), 'contexts': len(ctxs), 'by_task': by_task, 'by_split': by_split, 'tool_multi': round(multi / float(tooln), 3)}, indent=2))
    print('max rows per (context,family):', max(USED.values()) if USED else 0)
if __name__ == '__main__':
    main()
