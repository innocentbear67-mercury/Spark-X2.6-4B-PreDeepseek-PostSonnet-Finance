"""Deterministic generator for area sec_filing_compliance (profile B, 1000 rows).

Layout: registries -> rules -> archetypes -> helpers -> fixtures -> contexts ->
question families (calc, extraction, qa, classification, summarization, tool) ->
fixture-level split assignment -> emit.

Everything is synthetic. Fixtures are authored here; every numeric ground
truth is computed in code from the same values written into the context.
Python 3.9, standard library only, no network.
"""
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date, timedelta
AREA = 'sec_filing_compliance'
HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ['calc', 'extraction', 'summarization', 'classification', 'qa', 'tool_use']
ABBR = {'calc': 'calc', 'extraction': 'extr', 'summarization': 'summ', 'classification': 'cls', 'qa': 'qa', 'tool_use': 'tool'}
QUOTA = {'calc': 120, 'extraction': 220, 'qa': 240, 'classification': 220, 'summarization': 100, 'tool_use': 100}
THINK = {'calc': 'on', 'qa': 'on', 'tool_use': 'on', 'extraction': 'off', 'classification': 'off', 'summarization': 'off'}
# --- fictional issuer registry ---
COMPANIES = [{'name': 'Halcyon Grid Utilities', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Delaware', 'status': 'large accelerated filer'}, {'name': 'Meridian Bancorp', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Ohio', 'status': 'large accelerated filer'}, {'name': 'Kestrel Foods', 'kind': 'domestic', 'fy': (6, 30), 'state': 'Illinois', 'status': 'accelerated filer'}, {'name': 'Northwind Logistics', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Georgia', 'status': 'accelerated filer'}, {'name': 'Ardent Semiconductor', 'kind': 'domestic', 'fy': (12, 31), 'state': 'California', 'status': 'large accelerated filer'}, {'name': 'Bluehaven Water Works', 'kind': 'domestic', 'fy': (9, 30), 'state': 'Texas', 'status': 'non-accelerated filer'}, {'name': 'Corvid Analytics', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Massachusetts', 'status': 'accelerated filer'}, {'name': 'Dunlin Marine Services', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Louisiana', 'status': 'smaller reporting company'}, {'name': 'Emberline Insurance', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Connecticut', 'status': 'large accelerated filer'}, {'name': 'Falconridge Mining', 'kind': 'domestic', 'fy': (12, 31), 'state': 'British Columbia', 'status': 'accelerated filer'}, {'name': 'Glimmerlight Media', 'kind': 'domestic', 'fy': (12, 31), 'state': 'New York', 'status': 'accelerated filer'}, {'name': 'Harborview Property Trust', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Maryland', 'status': 'large accelerated filer'}, {'name': 'Ironbell Fabrication', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Michigan', 'status': 'non-accelerated filer'}, {'name': 'Juniper Peak Brewing', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Colorado', 'status': 'smaller reporting company'}, {'name': 'Lanternfish Diagnostics', 'kind': 'domestic', 'fy': (12, 31), 'state': 'New Jersey', 'status': 'accelerated filer'}, {'name': 'Mossbank Timber', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Oregon', 'status': 'non-accelerated filer'}, {'name': 'Nimbus Peak Airlines', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Arizona', 'status': 'accelerated filer'}, {'name': 'Orchard Gate Pharmacy', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Pennsylvania', 'status': 'large accelerated filer'}, {'name': 'Palladium Works', 'kind': 'domestic', 'fy': (9, 30), 'state': 'Wisconsin', 'status': 'non-accelerated filer'}, {'name': 'Quillon Robotics', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Ohio', 'status': 'accelerated filer'}, {'name': 'Redfern Energy Partners', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Oklahoma', 'status': 'non-accelerated filer'}, {'name': 'Sablewood Hotels', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Florida', 'status': 'accelerated filer'}, {'name': 'Tallow Creek Dairy', 'kind': 'domestic', 'fy': (12, 31), 'state': 'Vermont', 'status': 'smaller reporting company'}, {'name': 'Verdant Hollow Farms', 'kind': 'domestic', 'fy': (12, 31), 'state': 'California', 'status': 'smaller reporting company'}, {'name': 'Lysholm Maritime ASA', 'kind': 'fpi', 'fy': (12, 31), 'state': 'Norway', 'status': 'foreign private issuer'}, {'name': 'Tarnholt Systems AB', 'kind': 'fpi', 'fy': (12, 31), 'state': 'Sweden', 'status': 'foreign private issuer'}, {'name': 'Maple Ridge Resources', 'kind': 'mjds', 'fy': (12, 31), 'state': 'Alberta', 'status': 'accelerated filer'}]
DOMESTIC = [c for c in COMPANIES if c['kind'] == 'domestic']
FPI = [c for c in COMPANIES if c['kind'] == 'fpi']
MJDS = [c for c in COMPANIES if c['kind'] == 'mjds']
# --- people and holder names ---
CONTACTS = ['Dana Whitfield, Vice President, Investor Relations', 'Marcus Oyelaran, Corporate Secretary', 'Priya Raghunathan, Chief Compliance Officer', 'Elena Vasquez, Director of Financial Reporting', 'Tobias Lindqvist, General Counsel', 'Ruth Amanpour, Treasurer', 'Kenji Nakamura, Controller', 'Clara Boateng, Head of Regulatory Affairs']
HOLDERS = ['Anselm Ridge Capital', 'Pinewood Value Partners', 'Corvus Asset Management', 'Third Harbor Advisors', 'Stonepine Partners LP', 'Ellsworth Family Trust', 'Nadia Bellweather', 'Dara Whitlock', 'Larkspur Index Funds', 'Bramblewick Partners', 'Tessellate Advisors', 'Orrin Halloway']
# --- fixed label sets used by every classifier question ---
FORM_LABELS = ['10-K', '10-Q', '8-K', '20-F', '40-F', 'S-1', 'S-3', 'DEF 14A', 'SC 13D', 'SC 13G', 'Form 4', 'Form 3', 'Form 5', '6-K', '11-K']
FORM_SET = '{' + ', '.join(FORM_LABELS) + '}'
ITEM_LABELS = ['1.01', '1.02', '1.05', '2.01', '2.02', '2.03', '2.05', '2.06', '3.01', '3.02', '3.03', '4.01', '4.02', '5.01', '5.02', '5.03', '5.07', '7.01', '8.01', '9.01']
ITEM_SET = '{' + ', '.join(ITEM_LABELS) + '}'
PROP_LABELS = ['director_election', 'auditor_ratification', 'say_on_pay', 'say_on_frequency', 'equity_plan', 'merger_approval', 'charter_amendment', 'shareholder_proposal', 'other_business']
PROP_SET = '{' + ', '.join(PROP_LABELS) + '}'
SECTION_LABELS = ['business', 'risk_factors', 'md_a', 'financial_statements', 'controls_and_procedures', 'legal_proceedings', 'exhibit_index', 'cover_page']
SECTION_SET = '{' + ', '.join(SECTION_LABELS) + '}'
SCHED_SET = '{Schedule 13D, Schedule 13G}'
INTENT_SET = '{passive, activist}'
TX_SET = '{P, S, A, M, F, G}'
CODE_ACT = {'P': 'bought shares in the open market at the reported price', 'S': 'sold shares in the open market at the reported price', 'A': 'received a grant of restricted stock from the issuer', 'M': 'exercised an in-the-money employee stock option and received shares', 'F': 'surrendered shares to the issuer to satisfy the tax withholding obligation on a vesting award', 'G': 'made a bona fide gift of shares to a family trust'}
# --- rules quoted inside contexts so every row is self-contained ---
RULE_8K = 'Rule: a current report on Form 8-K is due within 4 business days after the triggering event. Reports under Items 2.02 and 7.01 are furnished to the Commission; reports under every other item are filed.'
RULE_13 = 'Rule: a holder that passes 5.0 percent of a registered class reports on Schedule 13D unless it is a passive qualified institutional investor with no intent to influence control, which may use Schedule 13G.'
RULE_ANNUAL = 'Rule: an annual report is due 60 calendar days after fiscal year end for a large accelerated filer, 75 days for an accelerated filer, and 90 days for any other filer.'
RULE_PROP = 'Rule: routine matters (director elections, auditor ratification, advisory say-on-pay and say-on-frequency votes) are ordinary business; charter amendments, equity plan approvals, merger approvals and shareholder proposals are extraordinary business.'
RULE_PASS = 'Rule: a proposal passes when the votes cast for it exceed the votes cast against it.'
# --- authored fixture archetypes ---
EV8K_ARCH = [('1.01', 'The registrant entered into a new ten-year supply agreement that is material to its operations; no prior agreement was terminated and no borrowing was created by the arrangement.'), ('1.02', 'The registrant terminated its principal distribution agreement before its stated end date, ending a relationship that was material to the registrant.'), ('1.05', 'The registrant determined that unauthorized access to a production network caused a material disruption to its order fulfilment systems.'), ('2.01', 'The registrant completed its previously announced acquisition of a privately held competitor for cash and assumed debt.'), ('2.02', 'The registrant furnished a press release announcing results of operations for the quarter just ended and for the year to date.'), ('2.03', 'The registrant drew 250 million USD under an existing committed facility; no new agreement was executed and the draw created a direct financial obligation.'), ('2.05', 'The registrant committed to a plan to close two plants and expects to record severance and contract termination costs.'), ('2.06', 'The registrant concluded that the carrying amount of a reporting unit exceeded its fair value and recorded a non-cash impairment charge.'), ('3.01', 'The registrant received a written notice from its listing exchange that it no longer satisfies a continued listing standard.'), ('3.02', 'The registrant sold unregistered shares to accredited investors in a private placement without registration.'), ('3.03', 'The registrant amended the certificate of designation for its preferred stock, changing the conversion price and altering the rights of holders.'), ('4.01', 'The registrant dismissed its independent registered public accounting firm and engaged a successor firm for the current fiscal year.'), ('4.02', 'The audit committee concluded that previously issued financial statements should no longer be relied upon.'), ('5.01', 'A shareholder group acquired voting power sufficient to elect a majority of the board, effecting a change in control of the registrant.'), ('5.02', "The registrant's chief financial officer resigned effective immediately and no interim successor was named."), ('5.03', "The board approved an amendment to the bylaws and changed the registrant's fiscal year end."), ('5.07', 'The registrant held its annual meeting and shareholders voted on the election of directors and on ratification of the auditor.'), ('7.01', 'The registrant disclosed material non-public information to a select group of analysts in a private meeting.'), ('8.01', 'The registrant announced a voluntary product recall that does not fall within any other item of the form.'), ('9.01', 'The registrant furnished the audited financial statements of an acquired business as an exhibit to the report.')]
EVFM_ARCH = [('10-K', 'The registrant will file its annual report for the fiscal year ended {period}, containing audited financial statements, the management discussion and the report on internal control. The registrant is a domestic issuer.'), ('10-Q', 'The registrant will file its quarterly report for the three and nine months ended {period}. No annual report is due for this period.'), ('20-F', 'The registrant is a foreign private issuer and will file its annual report for the fiscal year ended {period} on the form reserved for foreign private issuers.'), ('40-F', 'The registrant is a Canadian issuer eligible under the multijurisdictional disclosure system and will file its annual report for the year ended {period} on the MJDS annual form.'), ('S-1', 'The registrant intends to sell common stock to the public for the first time, is not yet a reporting company, and will file a registration statement covering the initial offering.'), ('S-3', 'The registrant is current in its Exchange Act reporting and will register a shelf offering of debt securities on the short-form registration statement available to seasoned issuers.'), ('DEF 14A', 'The registrant will solicit proxies for its annual meeting of shareholders and will file the definitive proxy statement for that meeting.'), ('SC 13D', "An investor acquired 8.4 percent of the registrant's common stock and states an intent to seek board representation and influence the issuer's strategy."), ('SC 13G', "An index fund manager acquired 6.1 percent of the registrant's common stock solely as a passive investment and holds no intent to influence control."), ('Form 4', 'An executive officer sold shares in the open market on the stated date and must report the change in beneficial ownership within two business days.'), ('Form 3', 'A newly appointed director must file an initial statement of beneficial ownership within ten days of taking office.'), ('Form 5', 'An insider must file the annual statement reporting previously exempt small acquisitions and transactions not reported during the year.'), ('6-K', 'A foreign private issuer will furnish an interim report containing its half-year results and a press release to the Commission.'), ('11-K', "The registrant's employee stock purchase plan will file its annual report covering the plan's fiscal year.")]
# --- proxy proposal archetypes ---
PROPOSALS = [('director_election', 'To elect the nine nominees named in the proxy statement to the board of directors, each to serve until the next annual meeting.'), ('auditor_ratification', 'To ratify the appointment of Vantage Audit LLP as the independent registered public accounting firm for the fiscal year.'), ('say_on_pay', 'To approve, on an advisory basis, the compensation of the named executive officers as disclosed in the compensation discussion and analysis.'), ('say_on_frequency', 'To recommend, on an advisory basis, whether the advisory vote on executive compensation should occur every one, two or three years.'), ('equity_plan', 'To approve the 2026 Omnibus Equity Incentive Plan, including the reserve of additional shares authorised for issuance under the plan.'), ('merger_approval', 'To approve the agreement and plan of merger under which the registrant would become a wholly owned subsidiary of the acquirer.'), ('charter_amendment', 'To amend the restated certificate of incorporation to increase the number of authorised shares of common stock.'), ('shareholder_proposal', 'A shareholder asks the company to publish an annual report on its political spending and lobbying expenditures, submitted for action at the meeting.'), ('other_business', 'To transact any other business that may properly come before the meeting or any adjournment of the meeting.')]
# --- Form 10-K section archetypes ---
SECTIONS = [('business', 'Item 1. Business', 'The registrant operates in three reportable segments and sells into 14 countries. It employed 4820 people at the fiscal year end and leases its principal facilities under operating leases.', 0), ('risk_factors', 'Item 1A. Risk Factors', 'A prolonged decline in industrial demand could reduce revenue by an amount the registrant cannot estimate. Supply arrangements depend on a small number of qualified vendors. These factors are not exhaustive.', 0), ('md_a', "Item 7. Management's Discussion and Analysis", 'Revenue increased 8.4 percent to 4210 million USD. Liquidity was 780 million USD at the year end and management believes operating cash flow is sufficient for the next twelve months.', 4210), ('financial_statements', 'Item 8. Financial Statements and Supplementary Data', 'The consolidated statements of operations present revenue of 4210 million USD and net income of 318 million USD. The accompanying notes describe the basis of presentation and the significant accounting policies.', 4210), ('controls_and_procedures', 'Item 9A. Controls and Procedures', 'Management assessed the effectiveness of internal control over financial reporting and concluded that it was effective at the fiscal year end. The auditor issued an unqualified opinion on that assessment.', 0), ('legal_proceedings', 'Item 3. Legal Proceedings', 'The registrant is a defendant in a product liability action filed in state court. Management believes the outcome will not have a material effect on the financial statements.', 0), ('exhibit_index', 'Item 15. Exhibits and Financial Statement Schedules', 'Exhibit 10.1 Credit Agreement dated 14 March 2026. Exhibit 31.1 Certification of the Chief Executive Officer. Exhibit 32.1 Certification of the Chief Financial Officer.', 0), ('cover_page', 'Cover Page', 'The cover page states the registrant name, the commission file number, the number of shares outstanding and the aggregate market value of shares held by non-affiliates.', 0)]
# --- context-free stable knowledge ---
KNOWLEDGE = [('What does Item 2.02 of Form 8-K require a registrant to disclose?', 'results of operations and financial condition', 'text'), ('Within how many business days must an amendment to a Schedule 13D be filed after a material change?', 2, 'number'), ('Which form does a foreign private issuer use to furnish interim results to the Commission?', 'Form 6-K', 'text'), ('Within how many business days must a Form 4 be filed after the reported transaction?', 2, 'number'), ('How many calendar days after fiscal year end must an accelerated filer file its annual report?', 75, 'number'), ('Within how many days after the end of a calendar quarter must a qualified institutional investor file its initial Schedule 13G?', 45, 'number'), ("Which item of Form 8-K covers a change in the registrant's certifying accountant?", 'Item 4.01', 'text'), ('What ownership percentage of a registered class triggers a Schedule 13D filing?', 5, 'number'), ('Which form does a registrant use to furnish a press release rather than file it?', 'Form 8-K', 'text'), ('How many business days after the triggering event is a Form 8-K due?', 4, 'number'), ("Which statement reports a new insider's initial holdings?", 'Form 3', 'text'), ('Within how many calendar days after becoming an insider must a Form 3 be filed?', 10, 'number')]
# --- tool schemas for the tool_use rows ---
TOOL_HEADER = {'name': 'get_filing_header', 'description': 'Return the EDGAR cover-page fields for one filing.', 'parameters': {'type': 'object', 'required': ['issuer', 'accession'], 'properties': {'issuer': {'type': 'string'}, 'accession': {'type': 'string'}}}}
TOOL_RULE = {'name': 'get_deadline_rule', 'description': 'Return the statutory filing window for a form type and filer status.', 'parameters': {'type': 'object', 'required': ['form_type', 'filer_status'], 'properties': {'form_type': {'type': 'string'}, 'filer_status': {'type': 'string'}}}}
TOOL_BD = {'name': 'count_business_days', 'description': 'Count business days between two ISO dates, excluding US federal holidays.', 'parameters': {'type': 'object', 'required': ['start_date', 'end_date'], 'properties': {'start_date': {'type': 'string'}, 'end_date': {'type': 'string'}}}}
TOOL_OWN = {'name': 'get_ownership_snapshot', 'description': 'Return reported and outstanding share counts for one holder and issuer.', 'parameters': {'type': 'object', 'required': ['issuer', 'holder'], 'properties': {'issuer': {'type': 'string'}, 'holder': {'type': 'string'}}}}
TOOL_TX = {'name': 'list_form4_transactions', 'description': 'List Form 4 lines for an insider over a date range.', 'parameters': {'type': 'object', 'required': ['issuer', 'insider', 'start_date', 'end_date'], 'properties': {'issuer': {'type': 'string'}, 'insider': {'type': 'string'}, 'start_date': {'type': 'string'}, 'end_date': {'type': 'string'}}}}
TOOL_ITEMS = {'name': 'get_8k_items', 'description': 'Return the Form 8-K item numbers disclosed on a filing cover page.', 'parameters': {'type': 'object', 'required': ['issuer', 'accession'], 'properties': {'issuer': {'type': 'string'}, 'accession': {'type': 'string'}}}}

# --- small helpers ---
def iso(d):
    return d.strftime('%Y-%m-%d')

def add_bd(start, n):
    cur = start
    k = 0
    while k < n:
        cur += timedelta(days=1)
        if cur.weekday() < 5:
            k += 1
    return cur

def bd_signed(a, b):
    if a == b:
        return 0
    step = 1 if b > a else -1
    cur = a
    n = 0
    while cur != b:
        cur += timedelta(days=step)
        if cur.weekday() < 5:
            n += step
    return n

def fy_date(co, year):
    return date(year, co['fy'][0], co['fy'][1])

def cik_for(i):
    return '000%07d' % (1842217 + 137 * i)

def accession_for(i):
    return '%s-26-%06d' % (cik_for(i), 1000 + 37 * i)

def words(s):
    return len(s.split())

def first_sentence(s):
    i = s.find('. ')
    return s[:i + 1] if i > 0 else s

# --- fixture builders ---
def build_ev8k():
    out = []
    for i in range(22):
        (item, text) = EV8K_ARCH[i % len(EV8K_ARCH)]
        co = DOMESTIC[(5 * i + 1) % 24]
        ev = date(2025, 1, 8) + timedelta(days=15 * i)
        items = [item]
        if i % 3 == 0 and item != '9.01':
            items = sorted([item, '9.01'])
        out.append({'key': 'EV8K-%02d' % (i + 1), 'company': co, 'event_date': ev, 'text': text, 'items': items, 'primary': item, 'exhibit': ['99.1', '10.1', '10.2', '99.2'][i % 4], 'contact': CONTACTS[i % len(CONTACTS)], 'filed': ev + timedelta(days=3 + 5 * i % 11), 'shares': 12000 + 3700 * (i + 1), 'price': round(18.5 + 4.25 * i, 2), 'pre_shares': 24000000 + 1500000 * i, 'new_shares': 900000 + 210000 * i})
    return out

def build_evfm():
    out = []
    for i in range(20):
        (form, text) = EVFM_ARCH[i % len(EVFM_ARCH)]
        if form in ('20-F', '6-K'):
            co = FPI[i % len(FPI)]
        elif form == '40-F':
            co = MJDS[i % len(MJDS)]
        else:
            co = DOMESTIC[(7 * i + 3) % 24]
        p_end = fy_date(co, 2025)
        if form == '10-Q':
            p_end = p_end - timedelta(days=92)
        days = {'10-K': 60, '20-F': 90, '40-F': 90, '10-Q': 40}.get(form, 45)
        out.append({'key': 'EVFM-%02d' % (i + 1), 'company': co, 'form': form, 'text': text.format(period=iso(p_end)), 'period_end': p_end, 'days': days, 'plan_date': p_end + timedelta(days=days - 3 + i % 7), 'contact': CONTACTS[(i + 3) % len(CONTACTS)], 'shares_out': 31000000 + 1900000 * i})
    return out

def build_headers():
    out = []
    forms = ['10-K', '10-Q', '8-K', 'DEF 14A', 'S-1', '20-F', '40-F', '11-K', '10-K', '10-Q', 'S-3', '10-K']
    for i in range(30):
        co = COMPANIES[3 * i % len(COMPANIES)]
        form = forms[i % len(forms)]
        p_end = fy_date(co, 2025)
        if form == '10-Q':
            p_end = p_end - timedelta(days=92)
        shares = 24000000 + 2600000 * i
        out.append({'key': 'HDR-%02d' % (i + 1), 'company': co, 'form': form, 'period_end': p_end, 'status': co['status'], 'cik': cik_for(i), 'accession': accession_for(i), 'filed': p_end + timedelta(days=45 + 4 * (i % 9)), 'state': co['state'], 'shares_out': shares, 'officers': int(shares * (0.045 + 0.004 * (i % 6))), 'float_shares': int(shares * (0.62 + 0.03 * (i % 5))), 'class_b': 0 if i % 4 else int(shares * 0.18)})
    return out

def build_holdings():
    out = []
    for i in range(26):
        out_sh = 22000000 + 2400000 * i
        held = int(out_sh * (0.056 + 0.001 * i))
        sign = 1 if i % 4 else -1
        delta = sign * int(out_sh * (0.002 + 0.0008 * (i % 4)))
        out.append({'key': 'HLD-%02d' % (i + 1), 'company': COMPANIES[5 * i % len(COMPANIES)], 'holder': HOLDERS[i % len(HOLDERS)], 'shares_out': out_sh, 'held': held, 'delta': delta, 'price': round(11.4 + 3.15 * (i % 17), 2), 'options': int(out_sh * (0.002 + 0.0007 * (i % 9))), 'code': ['P', 'S', 'A', 'M', 'F', 'G'][i % 6], 'intent': 'activist' if i % 2 == 0 else 'passive', 'qii': i % 2 == 1, 'ownership_nature': 'direct' if i % 2 == 0 else 'indirect'})
    return out

def build_proposals():
    out = []
    for i in range(24):
        (label, text) = PROPOSALS[i % len(PROPOSALS)]
        vf = 12000000 + 900000 * i
        va = 1500000 + 400000 * (i % 7)
        if i % 5 == 3:
            (vf, va) = (va, vf)
        out.append({'key': 'PRP-%02d' % (i + 1), 'company': COMPANIES[(4 * i + 1) % len(COMPANIES)], 'number': str(1 + i % 7), 'proposal': text, 'label': label, 'meeting': date(2026, 4, 14) + timedelta(days=9 * i), 'standard': ['majority of votes cast', 'majority of shares outstanding', 'two-thirds of votes cast'][i % 3], 'votes_for': vf, 'votes_against': va})
    return out

def build_excerpts():
    out = []
    for i in range(20):
        (sec, caption, body, amount) = SECTIONS[i % len(SECTIONS)]
        out.append({'key': 'EXC-%02d' % (i + 1), 'company': COMPANIES[(6 * i + 2) % len(COMPANIES)], 'section': sec, 'caption': caption, 'body': body, 'amount': amount, 'year': 2025, 'paragraphs': 3 + i % 4})
    return out

def build_calendars():
    out = []
    for i in range(19):
        co = COMPANIES[7 * i % len(COMPANIES)]
        form = ['10-K', '10-Q', '20-F', '10-K', '10-Q'][i % 5]
        p_end = fy_date(co, 2025)
        if form == '10-Q':
            p_end = p_end - timedelta(days=92)
        days = {'10-K': 60, '10-Q': 40, '20-F': 90}[form]
        if form == '10-K' and co['status'] == 'accelerated filer':
            days = 75
        elif form == '10-K' and co['status'] in ('non-accelerated filer', 'smaller reporting company'):
            days = 90
        elif form == '10-Q' and co['status'] in ('non-accelerated filer', 'smaller reporting company'):
            days = 45
        deadline = p_end + timedelta(days=days)
        out.append({'key': 'CAL-%02d' % (i + 1), 'company': co, 'form': form, 'period_end': p_end, 'days': days, 'deadline': deadline, 'review': p_end + timedelta(days=days - 12 - 3 * (i % 5)), 'actual': deadline + timedelta(days=-4 + 2 * (i % 9))})
    return out
UNITS_HOLD = 'Units: share counts in whole shares, prices in USD per share, and percentages in percent.'
UNITS_HEAD = 'Units: share counts in whole shares and percentages in percent.'
UNITS_CAL = 'Units: day counts in calendar days.'
UNITS_EV = 'Units: share counts in whole shares and amounts in USD.'
UNITS_GEN = 'Units: counts are whole numbers.'

# --- context renderers ---
def ctx_ev8k(fx, purpose, extras=(), units=None):
    lines = ['Memo - corporate event brief', 'Prepared for: ' + purpose, 'Issuer: ' + fx['company']['name'], 'Event date: ' + iso(fx['event_date']), 'Brief: ' + fx['text']]
    if 'items' in extras:
        lines.append('Item numbers stated on the cover of the report: ' + ', '.join(fx['items']))
    if 'exhibit' in extras:
        lines.append('Exhibit furnished: Exhibit ' + fx['exhibit'])
    if 'contact' in extras:
        lines.append('Filing contact: ' + fx['contact'])
    if 'filed' in extras:
        lines.append('Actual filing date: ' + iso(fx['filed']))
    if 'trade' in extras:
        lines.append('Shares covered by the concurrent Form 4: ' + str(fx['shares']))
        lines.append('Price per share on the Form 4: ' + str(fx['price']))
        lines.append('Shares outstanding before the new issuance: ' + str(fx['pre_shares']))
        lines.append('New shares issued in the private placement: ' + str(fx['new_shares']))
    lines.append(RULE_8K)
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

def ctx_evfm(fx, purpose, extras=('plan',), units=None, hide_form=False):
    lines = ['Memo - corporate event brief', 'Prepared for: ' + purpose, 'Issuer: ' + fx['company']['name']]
    if not hide_form:
        lines.append('Planned filing: ' + fx['form'])
    lines.extend(['Period end: ' + iso(fx['period_end']), 'Brief: ' + fx['text']])
    if 'plan' in extras:
        lines.append('Planned filing date: ' + iso(fx['plan_date']))
        lines.append('Statutory window stated by the rule: %d calendar days after the period end.' % fx['days'])
    if 'contact' in extras:
        lines.append('Filing contact: ' + fx['contact'])
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

def ctx_header(fx, purpose, extras=('shares',), units=None):
    lines = ['Excerpt from the EDGAR filing header', 'Prepared for: ' + purpose, 'Issuer: ' + fx['company']['name'], 'Form type: ' + fx['form'], 'Period of report: ' + iso(fx['period_end']), 'Filer status: ' + fx['status'], 'CIK: ' + fx['cik'], 'Accession number: ' + fx['accession'], 'Filed: ' + iso(fx['filed']), 'State of incorporation: ' + fx['state']]
    if 'shares' in extras:
        if 'thousands' in extras:
            lines.extend(['| Field | Value (thousands) |', '|---|---|', '| Shares outstanding | %d |' % (fx['shares_out'] // 1000), '| Public float | %d |' % (fx['float_shares'] // 1000), '| Class B shares |  |', 'Footnote 1: share counts on this cover page are stated in thousands of shares.', 'Footnote 2: a dash in any cell means the field was left blank on the cover page.'])
        else:
            lines.extend(['| Field | Value |', '|---|---|', '| Shares outstanding | %d |' % fx['shares_out'], '| Public float | %d |' % fx['float_shares'], '| Shares held by officers and directors | %d |' % fx['officers'], '| Class B shares | %d |' % fx['class_b'], 'Footnote 1: share counts are whole shares stated as of the cover date.'])
    lines.append(RULE_ANNUAL)
    lines.append('Rule: Forms 20-F, 40-F and 6-K are used by foreign private issuers; every other form listed here is used by a domestic issuer.')
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

def ctx_holding(fx, purpose, extras=('price',), units=None):
    lines = ['Holding - beneficial ownership report', 'Prepared for: ' + purpose, 'Issuer: ' + fx['company']['name'], 'Class: common stock', 'Shares outstanding: ' + str(fx['shares_out']), 'Reporting person: ' + fx['holder'], 'Shares held before the reported transaction: ' + str(fx['held']), 'Shares acquired or disposed of in the reported transaction: ' + str(fx['delta']), 'Shares underlying options exercisable within 60 days: ' + str(fx['options'])]
    if 'price' in extras:
        lines.append('Price per share in the reported transaction: ' + str(fx['price']))
    if 'intent' in extras:
        lines.append('Stated intent of the reporting person: ' + fx['intent'])
        lines.append('Registered investment adviser with 340 million USD in assets under management: ' + ('yes' if fx['qii'] else 'no'))
    if 'code' in extras:
        lines.append('Reported insider activity: ' + CODE_ACT[fx['code']])
        lines.append('Form 4 code legend: P purchase, S sale, A award, M option exercise, F tax withholding, G gift.')
    lines.append('Nature of ownership: ' + fx['ownership_nature'])
    lines.append('Rounding: report percentages to one decimal place.')
    lines.append(RULE_13)
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

def ctx_proposal(fx, purpose, extras=('votes',), units=None):
    lines = ['# Proxy extract - shareholder proposal', 'Prepared for: ' + purpose, 'Issuer: ' + fx['company']['name'], 'Meeting date: ' + iso(fx['meeting']), 'Proposal number: ' + fx['number'], 'Proposal text: ' + fx['proposal'], 'Vote standard stated for this proposal: ' + fx['standard']]
    if 'votes' in extras:
        lines.extend(['| Ballot | Shares |', '|---|---|', '| For | %d |' % fx['votes_for'], '| Against | %d |' % fx['votes_against'], '| Abstain | %d |' % (fx['votes_against'] // 9), 'Footnote: shares voted are whole shares and exclude broker non-votes.'])
    lines.append(RULE_PROP)
    lines.append(RULE_PASS)
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

def ctx_excerpt(fx, purpose, with_caption=True, units=None):
    lines = ['Excerpt from the annual report of ' + fx['company']['name'], 'Prepared for: ' + purpose]
    if with_caption:
        lines.append('Caption printed above the excerpt: ' + fx['caption'])
    lines.extend(['Text: ' + fx['body'], 'Footnote: the excerpt is reproduced without the surrounding cross-references.'])
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

def ctx_calendar(fx, purpose, units=None):
    lines = ['Note - filing calendar extract', 'Prepared for: ' + purpose, 'Registrant: ' + fx['company']['name'], 'Form type: ' + fx['form'], 'Fiscal period ended: ' + iso(fx['period_end']), 'Filer status: ' + fx['company']['status'], 'Deadline rule: this form is due %d calendar days after the period end for a registrant with this filer status.' % fx['days'], 'Filing deadline produced by the rule: ' + iso(fx['deadline']), 'Calendar review date: ' + iso(fx['review']), 'Actual filing date: ' + iso(fx['actual'])]
    if units:
        lines.insert(0, units)
    return '\n'.join(lines)

# --- row constructor ---
def rw(task, fx, ctx, q, gt, at, tol):
    return {'task': task, 'fixture': fx['key'], 'context': ctx, 'question': q, 'ground_truth': gt, 'answer_type': at, 'tolerance': tol}

# --- calc families ---
def calc_h1(fx, v=0):
    return rw('calc', fx, ctx_holding(fx, 'ownership percentage check', units=UNITS_HOLD), "Immediately after the reported transaction, what percentage of the issuer's outstanding class does the reporting person beneficially own, in percent?", round((fx['held'] + fx['delta']) / float(fx['shares_out']) * 100.0, 1), 'number', 'abs:0.1')

def calc_h2(fx, v=0):
    return rw('calc', fx, ctx_holding(fx, 'ownership change review', units=UNITS_HOLD), "By how many percentage points did the reported transaction change the reporting person's ownership of the outstanding class? Report a positive number for an increase and a negative number for a decrease.", round(fx['delta'] / float(fx['shares_out']) * 100.0, 1), 'number', 'abs:0.1')

def calc_h3(fx, v=0):
    return rw('calc', fx, ctx_holding(fx, 'position valuation', units=UNITS_HOLD), "What is the market value of the reporting person's post-transaction holding at the reported transaction price, in millions of USD?", round((fx['held'] + fx['delta']) * fx['price'] / 1000000.0, 2), 'number', 'abs:0.01')

def calc_h4(fx, v=0):
    return rw('calc', fx, ctx_holding(fx, 'diluted ownership check', units=UNITS_HOLD), 'What percentage of the outstanding class would the reporting person own if every option exercisable within 60 days were exercised, in percent?', round((fx['held'] + fx['delta'] + fx['options']) / float(fx['shares_out']) * 100.0, 1), 'number', 'abs:0.1')

def calc_h5(fx, v=0):
    return rw('calc', fx, ctx_holding(fx, 'threshold test', units=UNITS_HOLD), 'By how many shares does the post-transaction holding exceed the 5.0 percent threshold of the outstanding class?', fx['held'] + fx['delta'] - fx['shares_out'] // 20, 'number', 'abs:1')

def calc_c1(fx, v=0):
    return rw('calc', fx, ctx_calendar(fx, 'filing calendar review', units=UNITS_CAL), 'How many calendar days remain between the calendar review date and the filing deadline stated in the extract?', (fx['deadline'] - fx['review']).days, 'number', 'abs:1')

def calc_c2(fx, v=0):
    return rw('calc', fx, ctx_calendar(fx, 'late filing assessment', units=UNITS_CAL), 'By how many calendar days did the actual filing date differ from the filing deadline? Report a positive number if the filing was late and a negative number if it was early.', (fx['actual'] - fx['deadline']).days, 'number', 'abs:1')

def calc_c3(fx, v=0):
    return rw('calc', fx, ctx_calendar(fx, 'business day count', units=UNITS_CAL), 'How many business days elapsed between the period end and the actual filing date? Assume no public holidays fall in the window.', bd_signed(fx['period_end'], fx['actual']), 'number', 'abs:1')

def calc_e1(fx, v=0):
    return rw('calc', fx, ctx_ev8k(fx, 'filing window check', units=UNITS_GEN), 'Assuming no public holidays fall in the window, how many calendar days after the event date does the Form 8-K filing window close?', (add_bd(fx['event_date'], 4) - fx['event_date']).days, 'number', 'abs:1')

def calc_e2(fx, v=0):
    return rw('calc', fx, ctx_ev8k(fx, 'insider transaction value', extras=('trade',), units=UNITS_EV), 'What is the aggregate value of the shares covered by the concurrent Form 4 at the stated price, in thousands of USD?', round(fx['shares'] * fx['price'] / 1000.0, 1), 'number', 'abs:1')

def calc_e3(fx, v=0):
    return rw('calc', fx, ctx_ev8k(fx, 'dilution check', extras=('trade',), units=UNITS_EV), 'Immediately after the private placement, what percentage of the outstanding shares does the newly issued block represent, in percent?', round(fx['new_shares'] / float(fx['pre_shares'] + fx['new_shares']) * 100.0, 2), 'number', 'abs:0.01')

def calc_e4(fx, v=0):
    return rw('calc', fx, ctx_ev8k(fx, 'filing timeliness', extras=('filed',), units=UNITS_GEN), 'How many business days elapsed between the event date and the actual filing date? Assume no public holidays fall in the window.', bd_signed(fx['event_date'], fx['filed']), 'number', 'abs:1')

def calc_d1(fx, v=0):
    return rw('calc', fx, ctx_header(fx, 'insider concentration check', units=UNITS_HEAD), 'What percentage of shares outstanding is held by officers and directors, in percent?', round(fx['officers'] / float(fx['shares_out']) * 100.0, 2), 'number', 'abs:0.01')

def calc_d2(fx, v=0):
    return rw('calc', fx, ctx_header(fx, 'float review', units=UNITS_HEAD), 'What percentage of shares outstanding is included in the public float, in percent?', round(fx['float_shares'] / float(fx['shares_out']) * 100.0, 2), 'number', 'abs:0.01')

def calc_d3(fx, v=0):
    return rw('calc', fx, ctx_header(fx, 'free float estimate', units=UNITS_HEAD), 'How many shares are held by persons other than officers and directors, in whole shares?', fx['shares_out'] - fx['officers'], 'number', 'abs:1')

def calc_d4(fx, v=0):
    return rw('calc', fx, ctx_header(fx, 'affiliate overlap check', units=UNITS_HEAD), 'What percentage of the public float is held by officers and directors, in percent?', round(fx['officers'] / float(fx['float_shares']) * 100.0, 2), 'number', 'abs:0.01')

# --- extraction families ---
def ext_h1(fx, v=0):
    return rw('extraction', fx, ctx_header(fx, 'form identification', extras=()), 'What form type is stated in the filing header? Return the label exactly as printed.', fx['form'], 'label', 'exact')

def ext_h2(fx, v=0):
    return rw('extraction', fx, ctx_header(fx, 'accession capture', extras=()), 'What accession number appears in the filing header? Return the full number exactly as printed.', fx['accession'], 'text', 'exact')

def ext_h3(fx, v=0):
    return rw('extraction', fx, ctx_header(fx, 'period capture', extras=()), 'What period of report is stated in the header? Answer in YYYY-MM-DD form.', iso(fx['period_end']), 'text', 'exact')

def ext_h4(fx, v=0):
    return rw('extraction', fx, ctx_header(fx, 'status capture', extras=()), 'Which filer status is stated in the header? Return the phrase exactly as printed.', fx['status'], 'text', 'exact')

def ext_h5(fx, v=0):
    return rw('extraction', fx, ctx_header(fx, 'jurisdiction capture', extras=()), 'In which state or province is the registrant incorporated, according to the header? Return the name exactly as printed.', fx['state'], 'text', 'exact')

def ext_h6(fx, v=0):
    return rw('extraction', fx, ctx_header(fx, 'cover page capture', extras=('shares', 'thousands'), units=UNITS_HEAD), 'The cover page states share counts in thousands. How many shares are outstanding, in whole shares?', fx['shares_out'], 'number', 'abs:1')


def ext_e1(fx, v=0):
    return rw('extraction', fx, ctx_ev8k(fx, 'item capture', extras=('items',)), 'List every Form 8-K item number disclosed on the cover of this report, in ascending order.', list(fx['items']), 'list', 'ordered')

def ext_e2(fx, v=0):
    return rw('extraction', fx, ctx_ev8k(fx, 'exhibit capture', extras=('exhibit',)), 'Which exhibit number is furnished with this report? Return it exactly as printed.', fx['exhibit'], 'text', 'exact')

def ext_e3(fx, v=0):
    return rw('extraction', fx, ctx_ev8k(fx, 'event date capture'), 'What is the date of the earliest event reported? Answer in YYYY-MM-DD form.', iso(fx['event_date']), 'text', 'exact')

def ext_e4(fx, v=0):
    return rw('extraction', fx, ctx_ev8k(fx, 'contact capture', extras=('contact',)), 'Who is the filing contact named in the brief? Return the name and title exactly as printed.', fx['contact'], 'text', 'exact')

def ext_e5(fx, v=0):
    return rw('extraction', fx, ctx_ev8k(fx, 'item count', extras=('items',), units=UNITS_GEN), 'How many Form 8-K item numbers are disclosed on the cover of this report? Answer with a whole number.', len(fx['items']), 'number', 'abs:1')

def ext_f1(fx, v=0):
    return rw('extraction', fx, ctx_evfm(fx, 'form capture', extras=()), 'Which form type does the filing plan state? Return the label exactly as printed.', fx['form'], 'label', 'exact')

def ext_f2(fx, v=0):
    return rw('extraction', fx, ctx_evfm(fx, 'period capture', extras=()), 'What period end is stated in the brief? Answer in YYYY-MM-DD form.', iso(fx['period_end']), 'text', 'exact')

def ext_f3(fx, v=0):
    return rw('extraction', fx, ctx_evfm(fx, 'filing date capture', extras=('plan',)), 'What is the planned filing date stated in the brief? Answer in YYYY-MM-DD form.', iso(fx['plan_date']), 'text', 'exact')

def ext_o1(fx, v=0):
    return rw('extraction', fx, ctx_holding(fx, 'position capture', units=UNITS_HOLD), 'How many shares does the reporting person hold immediately after the reported transaction, in whole shares?', fx['held'] + fx['delta'], 'number', 'abs:1')

def ext_o2(fx, v=0):
    return rw('extraction', fx, ctx_holding(fx, 'price capture', units=UNITS_HOLD), 'What price per share is reported for the transaction, in USD?', fx['price'], 'number', 'abs:0.01')

def ext_o3(fx, v=0):
    return rw('extraction', fx, ctx_holding(fx, 'ownership type capture'), 'Is the reported nature of ownership direct or indirect? Answer with one word.', fx['ownership_nature'], 'label', 'exact')

def ext_x1(fx, v=0):
    return rw('extraction', fx, ctx_excerpt(fx, 'caption capture'), 'Which item caption is printed above this excerpt? Return it exactly as printed.', fx['caption'], 'text', 'exact')

def ext_x2(fx, v=0):
    return rw('extraction', fx, ctx_excerpt(fx, 'issuer capture', with_caption=False), "Which company's annual report is this excerpt taken from? Return the name exactly as printed.", fx['company']['name'], 'text', 'exact')

def ext_x3(fx, v=0):
    return rw('extraction', fx, ctx_excerpt(fx, 'sentence capture', with_caption=False), 'Return the first sentence of the excerpt verbatim.', first_sentence(fx['body']), 'text', 'exact')

def ext_x4(fx, v=0):
    return rw('extraction', fx, ctx_excerpt(fx, 'length check', with_caption=False, units=UNITS_GEN), 'How many words are in the excerpt body? Answer with a whole number.', words(fx['body']), 'number', 'abs:1')

def ext_p1(fx, v=0):
    return rw('extraction', fx, ctx_proposal(fx, 'vote standard capture', extras=()), 'What vote standard is stated for this proposal? Return the phrase exactly as printed.', fx['standard'], 'text', 'exact')

def ext_p2(fx, v=0):
    return rw('extraction', fx, ctx_proposal(fx, 'ballot capture', units=UNITS_GEN), 'How many shares were cast in favour of the proposal, in whole shares?', fx['votes_for'], 'number', 'abs:1')

def ext_p3(fx, v=0):
    return rw('extraction', fx, ctx_proposal(fx, 'proposal number capture', extras=()), 'Which proposal number is printed in the extract? Return it exactly as printed.', fx['number'], 'text', 'exact')

def ext_c1(fx, v=0):
    return rw('extraction', fx, ctx_calendar(fx, 'deadline capture', units=UNITS_CAL), 'What filing deadline date is stated in the calendar extract? Answer in YYYY-MM-DD form.', iso(fx['deadline']), 'text', 'exact')

def ext_c2(fx, v=0):
    return rw('extraction', fx, ctx_calendar(fx, 'window capture', units=UNITS_CAL), 'How many calendar days does the stated rule allow between the period end and the filing deadline? Answer with a whole number.', fx['days'], 'number', 'abs:1')

# --- qa families ---
def qa_e1(fx, v=0):
    item = fx['primary']
    return rw('qa', fx, ctx_ev8k(fx, 'item routing review'), "Which Form 8-K item governs this event, and is that item furnished or filed? Answer as '<item>: furnished' or '<item>: filed'.", item + ': ' + ('furnished' if item in ('2.02', '7.01') else 'filed'), 'text', 'normalized')

def qa_e2(fx, v=0):
    return rw('qa', fx, ctx_ev8k(fx, 'timeliness review', extras=('filed',)), "Given the dates in the brief, is the report timely? Answer 'timely' or 'late'.", 'timely' if fx['filed'] <= add_bd(fx['event_date'], 4) else 'late', 'label', 'exact')

def qa_e3(fx, v=0):
    return rw('qa', fx, ctx_ev8k(fx, 'deadline confirmation'), 'What is the final permissible filing date for the report described? Answer in YYYY-MM-DD form.', iso(add_bd(fx['event_date'], 4)), 'text', 'exact')

def qa_e4(fx, v=0):
    return rw('qa', fx, ctx_ev8k(fx, 'filing lag review', extras=('filed',), units=UNITS_GEN), 'How many business days after the event date did the registrant actually file? Answer with a whole number; report a negative number if the filing came before the event.', bd_signed(fx['event_date'], fx['filed']), 'number', 'abs:1')

def qa_f1(fx, v=0):
    return rw('qa', fx, ctx_evfm(fx, 'deadline computation', extras=('plan',)), 'What is the statutory filing deadline date for the planned report? Answer in YYYY-MM-DD form.', iso(fx['period_end'] + timedelta(days=fx['days'])), 'text', 'exact')

def qa_f2(fx, v=0):
    return rw('qa', fx, ctx_evfm(fx, 'window test', extras=('plan',)), "Is the planned filing date on or before the statutory deadline? Answer 'inside' or 'outside'.", 'inside' if fx['plan_date'] <= fx['period_end'] + timedelta(days=fx['days']) else 'outside', 'label', 'exact')

def qa_d1(fx, v=0):
    return rw('qa', fx, ctx_header(fx, 'annual deadline lookup', extras=(), units=UNITS_HEAD), 'Given the filer status in the header, how many calendar days does the registrant have to file its annual report? Answer with a whole number.', {'large accelerated filer': 60, 'accelerated filer': 75}.get(fx['status'], 90), 'number', 'abs:1')

def qa_d2(fx, v=0):
    return rw('qa', fx, ctx_header(fx, 'period logic review', extras=(), units=UNITS_HEAD), 'How many calendar days after the period end was the filing made? Answer with a whole number.', (fx['filed'] - fx['period_end']).days, 'number', 'abs:1')

def qa_o1(fx, v=0):
    if fx['intent'] == 'passive' and fx['qii']:
        gt = 'Schedule 13G'
    else:
        gt = 'Schedule 13D'
    return rw('qa', fx, ctx_holding(fx, 'schedule selection', extras=('price', 'intent')), 'Does this position require a Schedule 13D or a Schedule 13G? Answer with the schedule name only.', gt, 'label', 'exact')

def qa_o2(fx, v=0):
    after = fx['held'] + fx['delta']
    return rw('qa', fx, ctx_holding(fx, 'threshold narrative', units=UNITS_HOLD), "What ownership percentage must be reported, to one decimal place, and does the position cross the 5.0 percent threshold? Answer as '<pct> percent: yes' or '<pct> percent: no'.", '%.1f percent: %s' % (round(after / float(fx['shares_out']) * 100.0, 1), 'yes' if after > fx['shares_out'] // 20 else 'no'), 'text', 'normalized')

def qa_p1(fx, v=0):
    return rw('qa', fx, ctx_proposal(fx, 'proposal routing'), "Is this proposal ordinary business or extraordinary business? Answer 'ordinary' or 'extraordinary'.", 'ordinary' if fx['label'] in ('director_election', 'auditor_ratification', 'say_on_pay', 'say_on_frequency') else 'extraordinary', 'label', 'exact')

def qa_p2(fx, v=0):
    return rw('qa', fx, ctx_proposal(fx, 'vote outcome review'), "Did the proposal pass? Answer 'passed' or 'failed'.", 'passed' if fx['votes_for'] > fx['votes_against'] else 'failed', 'label', 'exact')

def qa_x1(fx, v=0):
    return rw('qa', fx, ctx_excerpt(fx, 'section identification', with_caption=False), 'Which part of the annual report does the excerpt belong to? Answer with the item caption.', fx['caption'], 'text', 'exact')

def qa_x2(fx, v=0):
    return rw('qa', fx, ctx_excerpt(fx, 'structure check', with_caption=False, units=UNITS_GEN), 'How many sentences does the excerpt contain? Answer with a whole number.', len([s for s in fx['body'].split('. ') if s.strip()]), 'number', 'abs:1')

def qa_c1(fx, v=0):
    return rw('qa', fx, ctx_calendar(fx, 'late filing review', units=UNITS_CAL), 'How many business days late was the filing? Answer with a whole number and report a negative number if the filing was early. Assume no public holidays.', bd_signed(fx['deadline'], fx['actual']), 'number', 'abs:1')

def qa_c2(fx, v=0):
    return rw('qa', fx, ctx_calendar(fx, 'elapsed time review', units=UNITS_CAL), 'How many calendar days elapsed between the period end and the actual filing date? Answer with a whole number.', (fx['actual'] - fx['period_end']).days, 'number', 'abs:1')

def qa_o3(fx, v=0):
    return rw('qa', fx, ctx_holding(fx, 'intent review', extras=('price', 'intent')), "Classify the reporting person's stated intent. Answer 'passive' or 'activist'.", fx['intent'], 'label', 'exact')


def qa_k1(fx, v=0):
    (q, gt, at) = fx['topic']
    return rw('qa', fx, '', q, gt, at, 'abs:1' if at == 'number' else 'normalized')

def qa_k2(fx, v=0):
    (q, gt, at) = fx['topic2']
    return rw('qa', fx, '', q, gt, at, 'abs:1' if at == 'number' else 'normalized')

# --- classification families ---
def cls_f1(fx, v=0):
    return rw('classification', fx, ctx_evfm(fx, 'form classification', extras=(), hide_form=True), 'Classify the required filing into exactly one form type. Label set: ' + FORM_SET, fx['form'], 'label', 'exact')

def cls_f2(fx, v=0):
    return rw('classification', fx, ctx_evfm(fx, 'filing selection', extras=(), hide_form=True), 'Which form type must the registrant file for this event? Label set: ' + FORM_SET, fx['form'], 'label', 'exact')

def cls_f3(fx, v=0):
    return rw('classification', fx, ctx_evfm(fx, 'form identification', extras=(), hide_form=True), 'Identify the applicable form type from the label set. Label set: ' + FORM_SET, fx['form'], 'label', 'exact')

def cls_f4(fx, v=0):
    return rw('classification', fx, ctx_evfm(fx, 'registrant filing plan', extras=(), hide_form=True), 'Select the correct form type for the described filing. Label set: ' + FORM_SET, fx['form'], 'label', 'exact')

def cls_i1(fx, v=0):
    return rw('classification', fx, ctx_ev8k(fx, 'item classification'), 'Classify the triggering event into one Item of Form 8-K. Label set: ' + ITEM_SET, fx['primary'], 'label', 'exact')

def cls_i2(fx, v=0):
    return rw('classification', fx, ctx_ev8k(fx, 'event routing'), 'Which Form 8-K Item must be reported for this event? Label set: ' + ITEM_SET, fx['primary'], 'label', 'exact')

def cls_i3(fx, v=0):
    return rw('classification', fx, ctx_ev8k(fx, 'disclosure routing'), 'Map the event to a single Form 8-K Item number. Label set: ' + ITEM_SET, fx['primary'], 'label', 'exact')

def cls_p1(fx, v=0):
    return rw('classification', fx, ctx_proposal(fx, 'proposal classification', extras=()), 'Classify the shareholder proposal into one label. Label set: ' + PROP_SET, fx['label'], 'label', 'exact')

def cls_p2(fx, v=0):
    return rw('classification', fx, ctx_proposal(fx, 'business classification', extras=()), 'Classify the proposal as ordinary business or extraordinary business. Label set: {ordinary, extraordinary}', 'ordinary' if fx['label'] in ('director_election', 'auditor_ratification', 'say_on_pay', 'say_on_frequency') else 'extraordinary', 'label', 'exact')

def cls_x1(fx, v=0):
    return rw('classification', fx, ctx_excerpt(fx, 'section classification', with_caption=False), 'Classify the excerpt by the part of the annual report it belongs to. Label set: ' + SECTION_SET, fx['section'], 'label', 'exact')

def cls_x2(fx, v=0):
    return rw('classification', fx, ctx_excerpt(fx, 'passage placement', with_caption=False), 'Which section of a Form 10-K contains this passage? Label set: ' + SECTION_SET, fx['section'], 'label', 'exact')

def cls_o1(fx, v=0):
    if fx['intent'] == 'passive' and fx['qii']:
        gt = 'Schedule 13G'
    else:
        gt = 'Schedule 13D'
    return rw('classification', fx, ctx_holding(fx, 'schedule classification', extras=('price', 'intent')), 'Which schedule does this position require? Label set: ' + SCHED_SET, gt, 'label', 'exact')

def cls_t1(fx, v=0):
    return rw('classification', fx, ctx_holding(fx, 'transaction code classification', extras=('code',)), 'Classify the reported insider activity into one Form 4 code. Label set: ' + TX_SET, fx['code'], 'label', 'exact')

# --- summarization families ---
def sum_ev8k(fx, v=0):
    return rw('summarization', fx, ctx_ev8k(fx, 'filing summary', extras=('items', 'filed')), SUM_Q[v % len(SUM_Q)], '%s reported the event of %s under Item %s and filed the report on %s.' % (fx['company']['name'], iso(fx['event_date']), fx['primary'], iso(fx['filed'])), 'text', 'normalized')

def sum_evfm(fx, v=0):
    return rw('summarization', fx, ctx_evfm(fx, 'filing summary', extras=('plan',)), SUM_Q[v % len(SUM_Q)], '%s plans to file a %s for the period ended %s on %s.' % (fx['company']['name'], fx['form'], iso(fx['period_end']), iso(fx['plan_date'])), 'text', 'normalized')

def sum_exc(fx, v=0):
    return rw('summarization', fx, ctx_excerpt(fx, 'filing summary', with_caption=True), SUM_Q[v % len(SUM_Q)], 'The excerpt from %s covers %s and is reproduced without surrounding cross-references.' % (fx['company']['name'], fx['caption']), 'text', 'normalized')

def sum_hdr(fx, v=0):
    return rw('summarization', fx, ctx_header(fx, 'filing summary', extras=('shares',)), SUM_Q[v % len(SUM_Q)], '%s filed a %s for the period ended %s and its filer status is %s.' % (fx['company']['name'], fx['form'], iso(fx['period_end']), fx['status']), 'text', 'normalized')
SUM_Q = ['Summarize the disclosure above in two sentences for a filing calendar log.', 'Write a three-sentence summary of this brief for the compliance desk.', 'Condense the filing brief into one sentence suitable for a board portal.', 'Summarize the event for the disclosure committee in no more than forty words.', 'Provide a short summary of the disclosure, keeping every date and figure that appears above.', 'Reduce the brief to a two-sentence internal memorandum summary.']

# --- tool-use families ---
def tool_t1(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Filing header lookup for %s, accession %s. Which form type is on the cover?' % (fx['company']['name'], fx['accession'])}, {'role': 'tool', 'content': json.dumps({'issuer': fx['company']['name'], 'accession': fx['accession'], 'form_type': fx['form'], 'period': iso(fx['period_end']), 'filer_status': fx['status']})}, {'role': 'user', 'content': 'Answer with the form type only.'}], 'tools': [TOOL_HEADER], 'ground_truth': fx['form'], 'answer_type': 'label', 'tolerance': 'exact'}

def tool_t2(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'I need the Form 8-K due date for an event on %s.' % iso(fx['event_date'])}, {'role': 'assistant', 'content': 'I will look up the Form 8-K filing window first. Calling get_deadline_rule with form_type 8-K.'}, {'role': 'tool', 'content': json.dumps({'form_type': '8-K', 'business_days': 4, 'note': 'due 4 business days after the event'})}, {'role': 'user', 'content': 'Now give me the calendar date the window closes, assuming no holidays.'}], 'tools': [TOOL_RULE, TOOL_BD], 'ground_truth': iso(add_bd(fx['event_date'], 4)), 'answer_type': 'text', 'tolerance': 'exact'}

def tool_t3(fx, v=0):
    after = fx['held'] + fx['delta']
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Ownership snapshot for %s in %s. What percentage of the class does the holder report after the transaction?' % (fx['holder'], fx['company']['name'])}, {'role': 'tool', 'content': json.dumps({'issuer': fx['company']['name'], 'holder': fx['holder'], 'shares_outstanding': fx['shares_out'], 'shares_held_after': after})}, {'role': 'user', 'content': 'Give the percentage to one decimal place.'}], 'tools': [TOOL_OWN], 'ground_truth': round(after / float(fx['shares_out']) * 100.0, 1), 'answer_type': 'number', 'tolerance': 'abs:0.1'}

def tool_t5(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Get the filing header for %s and tell me the form type.' % ' '.join(fx['company']['name'].split()[:-1])}, {'role': 'assistant', 'content': 'Looking up the header by short name.'}, {'role': 'tool', 'content': json.dumps({'error': 'issuer_not_found', 'hint': 'use the full legal name'})}, {'role': 'assistant', 'content': 'The lookup failed on the partial name; retrying with the full legal name %s.' % fx['company']['name']}, {'role': 'tool', 'content': json.dumps({'issuer': fx['company']['name'], 'accession': fx['accession'], 'form_type': fx['form']})}, {'role': 'user', 'content': 'So which form type is reported?'}], 'tools': [TOOL_HEADER], 'ground_truth': fx['form'], 'answer_type': 'label', 'tolerance': 'exact'}

def tool_t6(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'What was the closing price of %s on the filing date of accession %s?' % (fx['company']['name'], fx['accession'])}, {'role': 'assistant', 'content': 'Checking which fields the header tool exposes.'}, {'role': 'tool', 'content': json.dumps({'error': 'field_not_covered', 'available': ['form_type', 'period', 'filer_status', 'issuer']})}, {'role': 'user', 'content': 'Then state whether the data is available and stop.'}], 'tools': [TOOL_HEADER], 'ground_truth': None, 'answer_type': 'text', 'tolerance': None}

def tool_t9(fx, v=0):
    days = {'large accelerated filer': 60, 'accelerated filer': 75}.get(fx['status'], 90)
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Look up the annual report deadline for %s, a registrant with filer status %s and accession %s.' % (fx['company']['name'], fx['status'], fx['accession'])}, {'role': 'tool', 'content': json.dumps({'issuer': fx['company']['name'], 'accession': fx['accession'], 'form_type': '10-K', 'filer_status': fx['status'], 'period_end': iso(fx['period_end']), 'calendar_days': days})}, {'role': 'user', 'content': 'How many calendar days is that?'}], 'tools': [TOOL_RULE], 'ground_truth': days, 'answer_type': 'number', 'tolerance': 'abs:1'}

def tool_t10(fx, v=0):
    other = DOMESTIC[(COMPANIES.index(fx['company']) + 5) % 24]
    d1 = {'large accelerated filer': 60, 'accelerated filer': 75}.get(fx['company']['status'], 90)
    d2 = {'large accelerated filer': 60, 'accelerated filer': 75}.get(other['status'], 90)
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Compare the annual report deadlines for %s (accession %s) and %s.' % (fx['company']['name'], fx['accession'], other['name'])}, {'role': 'assistant', 'content': 'Calling get_deadline_rule for each registrant.'}, {'role': 'tool', 'content': json.dumps({'issuer': fx['company']['name'], 'filer_status': fx['company']['status'], 'calendar_days': d1})}, {'role': 'tool', 'content': json.dumps({'issuer': other['name'], 'filer_status': other['status'], 'calendar_days': d2})}, {'role': 'user', 'content': 'Which registrant has the shorter window, and how many days is it?'}], 'tools': [TOOL_RULE], 'ground_truth': '%s: %d days' % (fx['company']['name'] if d1 <= d2 else other['name'], min(d1, d2)), 'answer_type': 'text', 'tolerance': 'normalized'}

def tool_o1(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Ownership snapshot for the position of %s in %s. How many shares remain after the transaction?' % (fx['holder'], fx['company']['name'])}, {'role': 'assistant', 'content': 'Calling get_ownership_snapshot for that holder.'}, {'role': 'tool', 'content': json.dumps({'issuer': fx['company']['name'], 'holder': fx['holder'], 'shares_outstanding': fx['shares_out'], 'shares_before': fx['held'], 'shares_delta': fx['delta']})}, {'role': 'user', 'content': 'Give the post-transaction count in whole shares.'}], 'tools': [TOOL_OWN], 'ground_truth': fx['held'] + fx['delta'], 'answer_type': 'number', 'tolerance': 'abs:1'}

def tool_o2(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Check the stated intent behind the %s stake held by %s.' % (fx['company']['name'], fx['holder'])}, {'role': 'assistant', 'content': 'Calling get_ownership_snapshot to read the intent fields.'}, {'role': 'tool', 'content': json.dumps({'holder': fx['holder'], 'intent': fx['intent'], 'registered_investment_adviser': fx['qii'], 'percent_of_class': round((fx['held'] + fx['delta']) / float(fx['shares_out']) * 100.0, 1)})}, {'role': 'user', 'content': 'Which schedule must the holder file?'}], 'tools': [TOOL_OWN], 'ground_truth': 'Schedule 13G' if fx['intent'] == 'passive' and fx['qii'] else 'Schedule 13D', 'answer_type': 'label', 'tolerance': 'exact'}

def tool_c1(fx, v=0):
    n = bd_signed(fx['period_end'], fx['actual'])
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Count business days from the period end to the actual filing date for the %s filing of %s.' % (fx['form'], fx['company']['name'])}, {'role': 'assistant', 'content': 'Calling count_business_days over that window.'}, {'role': 'tool', 'content': json.dumps({'start_date': iso(fx['period_end']), 'end_date': iso(fx['actual']), 'business_days': n})}, {'role': 'user', 'content': 'Confirm the count as a single number.'}], 'tools': [TOOL_BD], 'ground_truth': n, 'answer_type': 'number', 'tolerance': 'abs:1'}

def tool_c2(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Compare the deadline and the actual filing date for the %s filing of %s.' % (fx['form'], fx['company']['name'])}, {'role': 'assistant', 'content': 'Calling count_business_days and reading the calendar extract.'}, {'role': 'tool', 'content': json.dumps({'deadline': iso(fx['deadline']), 'actual': iso(fx['actual'])})}, {'role': 'user', 'content': 'How many calendar days separate them? Report a positive number if the filing was late.'}], 'tools': [TOOL_BD], 'ground_truth': (fx['actual'] - fx['deadline']).days, 'answer_type': 'number', 'tolerance': 'abs:1'}

def tool_c3(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'For the %s filing of %s, how many calendar days does the rule allow after the period end?' % (fx['form'], fx['company']['name'])}, {'role': 'tool', 'content': json.dumps({'form_type': fx['form'], 'period_end': iso(fx['period_end']), 'calendar_days': fx['days']})}, {'role': 'user', 'content': 'Answer with a single whole number.'}], 'tools': [TOOL_RULE], 'ground_truth': fx['days'], 'answer_type': 'number', 'tolerance': 'abs:1'}

def tool_e1(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'Which 8-K items are on the cover of the %s report for the event of %s?' % (fx['company']['name'], iso(fx['event_date']))}, {'role': 'assistant', 'content': 'Calling get_8k_items for that filing.'}, {'role': 'tool', 'content': json.dumps({'items': fx['items']})}, {'role': 'user', 'content': 'Return them in ascending order.'}], 'tools': [TOOL_ITEMS], 'ground_truth': list(fx['items']), 'answer_type': 'list', 'tolerance': 'ordered'}

def tool_e2(fx, v=0):
    return {'task': 'tool_use', 'fixture': fx['key'], 'messages': [{'role': 'user', 'content': 'How many 8-K items does the %s report carry?' % fx['company']['name']}, {'role': 'tool', 'content': json.dumps({'items': fx['items']})}, {'role': 'user', 'content': 'Answer with a single whole number.'}], 'tools': [TOOL_ITEMS], 'ground_truth': len(fx['items']), 'answer_type': 'number', 'tolerance': 'abs:1'}

# --- assembly ---
def knowledge_fixtures():
    out = []
    for i in range(6):
        out.append({'key': 'KNW-%02d' % (i + 1), 'topic': KNOWLEDGE[i], 'topic2': KNOWLEDGE[i + 6]})
    return out

def rot(pool, fams):
    out = []
    for (i, fx) in enumerate(pool):
        for j in (0, 1):
            out.append(fams[(i + j) % len(fams)](fx, i + j))
    return out

def build_all():
    ev8k = build_ev8k()
    evfm = build_evfm()
    hdr = build_headers()
    hld = build_holdings()
    prp = build_proposals()
    exc = build_excerpts()
    cal = build_calendars()
    knw = knowledge_fixtures()
    rows = []
    rows += rot(hld[:15], [calc_h1, calc_h2, calc_h3, calc_h4, calc_h5])
    rows += rot(cal[:13], [calc_c1, calc_c2, calc_c3])
    rows += rot(ev8k[:16], [calc_e1, calc_e2, calc_e3, calc_e4])
    rows += rot(hdr[:16], [calc_d1, calc_d2, calc_d3, calc_d4])
    rows += rot(hdr[:30], [ext_h1, ext_h2, ext_h3, ext_h4, ext_h5, ext_h6])
    rows += rot(ev8k[:20], [ext_e1, ext_e2, ext_e3, ext_e4, ext_e5])
    rows += rot(evfm[:10], [ext_f1, ext_f2, ext_f3])
    rows += rot(hld[:15], [ext_o1, ext_o2, ext_o3])
    rows += rot(exc[:16], [ext_x1, ext_x2, ext_x3, ext_x4])
    rows += rot(prp[:10], [ext_p1, ext_p2, ext_p3])
    rows += rot(cal[:9], [ext_c1, ext_c2])
    rows += rot(ev8k[:18], [qa_e1, qa_e2, qa_e3, qa_e4])
    rows += rot(evfm[:12], [qa_f1, qa_f2])
    rows += rot(hdr[:24], [qa_d1, qa_d2])
    rows += rot(hld[:14], [qa_o1, qa_o2, qa_o3])
    rows += rot(prp[:11], [qa_p1, qa_p2])
    rows += rot(exc[:16], [qa_x1, qa_x2])
    rows += rot(cal[:19], [qa_c1, qa_c2])
    rows += rot(knw[:6], [qa_k1, qa_k2])
    rows += rot(evfm[:20], [cls_f1, cls_f2, cls_f3, cls_f4])
    rows += rot(ev8k[:20], [cls_i1, cls_i2, cls_i3])
    rows += rot(prp[:24], [cls_p1, cls_p2])
    rows += rot(exc[:20], [cls_x1, cls_x2])
    rows += rot(hld[:26], [cls_o1, cls_t1])
    rows += rot(ev8k[:18], [sum_ev8k])
    rows += rot(evfm[:12], [sum_evfm])
    rows += rot(exc[:10], [sum_exc])
    rows += rot(hdr[:10], [sum_hdr])
    rows += rot(hdr[:20], [tool_t1, tool_t5, tool_t9, tool_t6, tool_t10])
    rows += rot(hld[:10], [tool_t3, tool_o1, tool_o2])
    rows += rot(cal[:12], [tool_c1, tool_c2, tool_c3])
    rows += rot(ev8k[:8], [tool_e1, tool_e2, tool_t2])
    return rows

def assign_splits(rows):
    groups = {}
    for r in rows:
        groups.setdefault((r['task'], r['fixture']), []).append(r)
    out = {}
    for task in TASKS:
        keys = [k for (t, k) in groups if t == task]
        keys.sort(key=lambda k: hashlib.sha256((task + '|' + k).encode('utf-8')).hexdigest())
        n = len(keys)
        n_train = int(round(n * 0.8))
        n_val = int(round(n * 0.1))
        for (i, k) in enumerate(keys):
            if i < n_train:
                s = 'train'
            elif i < n_train + n_val:
                s = 'val'
            else:
                s = 'test'
            out[task, k] = s
    return out

def body_key(r):
    if 'question' in r:
        return r['question']
    return r['messages'][0]['content']

def finalize(rows):
    split_of = assign_splits(rows)
    order = {t: i for (i, t) in enumerate(TASKS)}
    rows.sort(key=lambda r: (order[r['task']], r['fixture'], body_key(r)))
    seq = {t: 0 for t in TASKS}
    out = []
    for r in rows:
        task = r['task']
        seq[task] += 1
        rid = 'fin_%s_%s_%06d' % (AREA, ABBR[task], seq[task])
        src = 'synthetic:' + AREA
        if 'messages' in r:
            row = {'id': rid, 'task': task, 'source': src, 'messages': r['messages'], 'tools': r['tools'], 'ground_truth': r['ground_truth'], 'answer_type': r['answer_type'], 'tolerance': r['tolerance'], 'split': split_of[task, r['fixture']], 'thinking': THINK[task]}
        else:
            if not r['context']:
                src = 'knowledge:finance_general'
            row = {'id': rid, 'task': task, 'source': src, 'context': r['context'], 'question': r['question'], 'ground_truth': r['ground_truth'], 'answer_type': r['answer_type'], 'tolerance': r['tolerance'], 'split': split_of[task, r['fixture']], 'thinking': THINK[task]}
        out.append(row)
    return out
MASK = re.compile('\\d+(?:[.,]\\d+)*')
WS = re.compile('\\s+')

def norm(s):
    return WS.sub(' ', str(s)).strip().lower()

def mask(s):
    return MASK.sub('#', norm(s))

def summarise(rows):
    fam = Counter()
    ctxs = set()
    by_task = Counter()
    by_split = Counter()
    by_at = Counter()
    bodies = set()
    dups = 0
    tool_rows = 0
    tool_multi = 0
    for r in rows:
        by_task[r['task']] += 1
        by_split[r['split']] += 1
        if r['ground_truth'] is not None:
            by_at[r['answer_type']] += 1
        if 'messages' in r:
            tool_rows += 1
            if any((m['role'] == 'assistant' for m in r['messages'])):
                tool_multi += 1
            fam_src = next((m['content'] for m in r['messages'] if m['role'] == 'user'), '')
            key = norm(json.dumps(r['messages'], sort_keys=True))
        else:
            fam_src = r['question']
            key = norm(r['context']) + '|' + norm(r['question'])
            if r['context']:
                ctxs.add(mask(r['context']))
        fam[mask(fam_src)[:160]] += 1
        if key in bodies:
            dups += 1
        bodies.add(key)
    top = fam.most_common(1)[0][1] if fam else 0
    return {'rows': len(rows), 'by_task': {t: by_task[t] for t in TASKS}, 'by_split': {s: by_split[s] for s in ('train', 'val', 'test')}, 'by_answer_type': {a: by_at[a] for a in ('number', 'text', 'label', 'list')}, 'distinct_question_families': len(fam), 'top_family_share': round(top / float(len(rows)), 4), 'distinct_contexts': len(ctxs), 'near_dup_pairs': dups, 'tool_use_multi_step_share': round(tool_multi / float(tool_rows), 3) if tool_rows else 0.0, 'family_max': top}

# --- emit ---
def main():
    rows = finalize(build_all())
    assert len(rows) == 1000, len(rows)
    path = os.path.join(HERE, 'prompts.jsonl')
    with open(path, 'w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    raw = open(path, 'rb').read()
    st = summarise(rows)
    checks = [st['rows'] == 1000, all(st['by_task'][t] == QUOTA[t] for t in TASKS),
              st['by_split'] == {'train': 800, 'val': 100, 'test': 100},
              st['near_dup_pairs'] == 0, st['distinct_question_families'] >= 25,
              st['top_family_share'] <= 0.04, st['distinct_contexts'] >= 120,
              st['tool_use_multi_step_share'] >= 0.40]
    report = {'area': AREA, 'profile': 'B', 'rows': st['rows'], 'by_task': st['by_task'],
              'by_split': st['by_split'], 'by_answer_type': st['by_answer_type'],
              'distinct_question_families': st['distinct_question_families'],
              'top_family_share': st['top_family_share'],
              'distinct_contexts': st['distinct_contexts'],
              'near_dup_pairs': st['near_dup_pairs'],
              'tool_use_multi_step_share': st['tool_use_multi_step_share'],
              'validation': 'pass' if all(checks) else 'fail',
              'sha256': hashlib.sha256(raw).hexdigest(),
              'notes': 'Sec-filing compliance fixtures; fixture-level splits; every answer recomputed in code.'}
    with open(os.path.join(HERE, 'report.json'), 'w', encoding='utf-8') as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write('\n')
    print(json.dumps(st, indent=2, sort_keys=True))
if __name__ == '__main__':
    main()