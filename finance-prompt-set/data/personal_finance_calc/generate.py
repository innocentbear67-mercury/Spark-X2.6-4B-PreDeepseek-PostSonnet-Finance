#!/usr/bin/env python3
"""Deterministic generator for the personal_finance_calc area (profile A).
Every ground truth is computed from the same fixture values printed in the row
context. No network, no external data, no hand-typed derived numbers.
"""
import hashlib
import json
import math
import os
import random
from collections import Counter, defaultdict
R = random.Random(42)
AREA = "personal_finance_calc"
SRC = "synthetic:" + AREA
UNITS = "Units: $ in whole dollars; percentages in percent; time in years."
ABBR = {"calc": "calc", "extraction": "extr", "qa": "qa",
        "classification": "cls", "summarization": "summ", "tool_use": "tool"}
THINK = {"calc": "on", "qa": "on", "tool_use": "on",
         "extraction": "off", "classification": "off", "summarization": "off"}
GOALS = ("home deposit", "college fund", "retirement", "business reserve", "vehicle replacement")
NAMES = (
    "Alder Briarwood Calden Drayton Ellery Fairmont Garland Holloway Ingles Jarvis "
    "Kestrel Langford Marlow Northcote Orchard Pemberton Quarry Redfern Sandoval Thorne "
    "Underwood Vance Westbrook Yarrow Ashby Bellamy Corwin Dunmore Eastwick Fenwick "
    "Grayling Harlow Iverson Jessup Kirkland Lindale Merrick Norwood Oakley Prescott "
    "Quill Rowan Sutcliffe Tilden Ulm Verity Whitlock Xanthos Yelverton Zane "
    "Ambrose Birchwood Creston Delaney Emberly Farrow Grafton Haven Isley Juniper "
    "Kelso Larkspur Mallory Netherby Orwell Piper Quimby Ralston Selby Tremaine "
    "Upton Vickery Wren Yardley Zeller Aubrey Beckett Carlisle Dunbar Eldridge "
    "Fontaine Granger Huxley Ingram Joplin Kingsley Lowell Mercer Newland Osgood "
    "Pruitt Quinn Redmond Sterling Thackeray Umber Vale Winslow Yost Zephyr "
    "Ansel Barrow Colby Drake Ellison Frost Godwin Hollis Irving Jordan "
    "Keating Lamont Marsden Nolan Orton Pell Raleigh Shaw Townsend Vaughn"
).split()
_OFF = [0]
def off(step=29):
    _OFF[0] += step
    return _OFF[0]
def num(x, nd=2):
    if isinstance(x, int):
        return str(x)
    v = round(float(x), nd)
    if v == 0:
        v = 0.0
    s = ("%." + str(nd) + "f") % v
    return s.rstrip("0").rstrip(".") if "." in s else s
def money(x):
    return num(round(float(x), 2))
def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)
def H(f, kind):
    return UNITS + "\n\nHousehold: the " + f["name"] + " household. Document: " + kind + ".\n\n"
# ---------------------------------------------------------------- arithmetic
def fv(p, r, n):
    return p * (1.0 + r) ** n
def fv_ann(pmt, r, n):
    return pmt * n if r == 0 else pmt * ((1.0 + r) ** n - 1.0) / r
def pmt_for(target, pv, r, n):
    return (target - pv) / n if r == 0 else (target - pv * (1.0 + r) ** n) * r / ((1.0 + r) ** n - 1.0)
def years_to(target, pv, pmt, r):
    if r == 0:
        return (target - pv) / pmt / 12.0
    a, b = pv + pmt / r, target + pmt / r
    return 0.0 if a <= 0 or b <= 0 else math.log(b / a) / math.log(1.0 + r) / 12.0
def mortgage_payment(p, rate, years):
    r = rate / 1200.0
    return p * r / (1.0 - (1.0 + r) ** (-years * 12))
def payoff(p, rate, pay, cap=900):
    r, bal, months, interest = rate / 1200.0, float(p), 0, 0.0
    while bal > 0.005 and months < cap:
        i = bal * r
        interest += i
        bal = bal + i - pay
        months += 1
    return months, interest
def wd_balance(port, first, growth, ret, years):
    bal, wd = float(port), float(first)
    for _ in range(years):
        bal = bal * (1.0 + ret) - wd
        wd = wd * (1.0 + growth)
    return bal
def full_years(bal, wd, ret):
    y, b = 0, float(bal)
    while y < 80:
        b = b * (1.0 + ret)
        if b < wd:
            return y
        b -= wd
        y += 1
    return y
def real_pct(nom, infl):
    return ((1.0 + nom) / (1.0 + infl) - 1.0) * 100.0
def net_of(gross_pct, fee_pct):
    return (1.0 + gross_pct / 100.0) * (1.0 - fee_pct / 100.0) - 1.0

# ------------------------------------------------------------------ fixtures
def build_fixtures(n=120):
    out = []
    for i in range(n):
        income = R.randrange(90, 291) * 50
        essential = int(income * R.uniform(0.46, 0.62) / 25) * 25
        disc = int(income * R.uniform(0.05, 0.14) / 25) * 25
        save = income - essential - disc
        cash = R.randrange(30, 240) * 250
        portfolio = R.randrange(50, 900) * 500
        years = R.randrange(8, 34)
        gh = R.choice([10, 20, 30])
        nominal = round(R.uniform(4.0, 8.4), 1)
        inflation = round(R.uniform(1.8, 3.6), 1)
        fee = round(R.uniform(0.05, 1.2), 2)
        gross = round(R.uniform(5.0, 9.0), 1)
        rm = nominal / 1200.0
        target = int(round((fv(portfolio, rm, years * 12) + fv_ann(save, rm, years * 12)) / 1000.0)) * 1000
        principal = R.randrange(30, 145) * 5000
        mrate = round(R.uniform(2.9, 7.1), 2)
        term = R.choice([15, 20, 30])
        extra = R.randrange(2, 25) * 25
        pay_sched = int(math.ceil(mortgage_payment(principal, mrate, term)))
        wport = R.randrange(60, 280) * 5000
        wrate = round(R.uniform(3.0, 5.5), 1)
        wd_growth = round(R.uniform(2.0, 3.2), 1)
        post_ret = round(R.uniform(4.0, 6.5), 1)
        horizon = R.randrange(10, 26)
        first_wd = int(round(wport * wrate / 100.0))
        guard = 0
        while wd_balance(wport, first_wd, wd_growth / 100.0, post_ret / 100.0, horizon) < 0 and guard < 20:
            wrate = round(wrate - 0.2, 1)
            first_wd = int(round(wport * wrate / 100.0))
            guard += 1
        spend = R.randrange(24, 91) * 1000
        taxable = int(R.randrange(3, 10) * spend * 1.03 / 500.0) * 500
        card_bal = R.randrange(25, 160) * 100
        card_apr = round(R.uniform(14.0, 26.0), 1)
        kk = R.randrange(18, 49)
        rmc = card_apr / 1200.0
        card_pay = int(math.ceil((card_bal * rmc / (1.0 - (1.0 + rmc) ** -kk)) / 5.0)) * 5
        goals = []
        for j in (0, 2, 4):
            gyears = R.randrange(4, 26)
            gtarget = R.randrange(40, 900) * 1000
            grm = 0.055 / 12.0
            funded = int(round((gtarget * R.uniform(0.15, 0.6) / (1.0 + grm) ** (gyears * 12)) / 500.0)) * 500
            req = pmt_for(gtarget, funded, grm, gyears * 12)
            goals.append({"name": GOALS[(i + j) % len(GOALS)], "target": gtarget, "funded": funded,
                          "years": gyears, "contrib": int(req * R.uniform(0.70, 0.92) / 5.0) * 5,
                          "required": req})
        accounts = [
            {"name": "Alpine taxable brokerage", "balance": R.randrange(20, 200) * 500, "fee": 0.12, "contrib": R.randrange(2, 18) * 50},
            {"name": "Basalt traditional retirement", "balance": R.randrange(50, 400) * 500, "fee": 0.35, "contrib": R.randrange(4, 22) * 50},
            {"name": "Cedar tax-free retirement", "balance": R.randrange(10, 150) * 500, "fee": 0.28, "contrib": R.randrange(2, 14) * 50},
            {"name": "Dune cash reserve", "balance": R.randrange(20, 120) * 500, "fee": 0.0, "contrib": R.randrange(1, 10) * 50}]
        seen = set()
        for a in accounts:
            while a["balance"] in seen:
                a["balance"] += 500
            seen.add(a["balance"])
        take = int(income * 0.78 / 10) * 10
        cats = ("housing", "utilities", "groceries", "transport", "childcare", "medical", "disc")
        vals = {"housing": R.uniform(0.20, 0.27), "utilities": R.uniform(0.03, 0.05),
                "groceries": R.uniform(0.06, 0.10), "transport": R.uniform(0.03, 0.06),
                "childcare": R.uniform(0.04, 0.09), "medical": R.uniform(0.01, 0.03)}
        stmt = {"take_sep": take, "take_aug": take + R.choice([-60, 0, 40, 80]), "disc": disc,
                "oneoff_aug": R.choice([0, 0, 0, 350, 900, 1500, 2200])}
        for c in cats:
            stmt[c] = disc if c == "disc" else int(income * vals[c] / 5) * 5
            stmt[c + "_aug"] = int(round(stmt[c] * R.uniform(0.94, 1.06) / 5.0)) * 5
        for suffix in ("", "_aug"):
            used = set()
            for c in cats:
                v = stmt[c + suffix]
                while v in used:
                    v += 5
                stmt[c + suffix], _ = v, used.add(v)
        if stmt["oneoff_aug"] in [stmt[c + "_aug"] for c in cats]:
            stmt["oneoff_aug"] += 5
        stmt["tot_sep"] = sum(stmt[c] for c in cats)
        stmt["tot_aug"] = sum(stmt[c + "_aug"] for c in cats) + stmt["oneoff_aug"]
        stmt["two_month"] = stmt["tot_aug"] + stmt["tot_sep"]
        stmt["net_sep"] = stmt["take_sep"] - stmt["tot_sep"]
        stmt["net_aug"] = stmt["take_aug"] - stmt["tot_aug"]
        out.append({"key": "FX%03d" % (i + 1), "name": NAMES[i], "income": income, "essential": essential,
                    "disc": disc, "save": save, "cash": cash, "portfolio": portfolio, "years": years, "gh": gh,
                    "nominal": nominal, "inflation": inflation, "fee": fee, "gross": gross, "target": target,
                    "principal": principal, "mrate": mrate, "term": term, "extra": extra,
                    "pay_sched": pay_sched, "wport": wport, "wrate": wrate, "first_wd": first_wd,
                    "post_ret": post_ret, "wd_growth": wd_growth, "horizon": horizon, "spend": spend,
                    "monthly_spend": spend // 12, "taxable": taxable, "card_bal": card_bal,
                    "card_apr": card_apr, "card_pay": card_pay, "goals": goals, "accounts": accounts,
                    "stmt": stmt})
    return out

# ------------------------------------------------------------------ contexts
def ctx_growth(f):
    return H(f, "growth assumptions") + table(["Item", "Value"], [
        ["Starting balance", money(f["portfolio"])], ["Gross annual return (percent)", num(f["gross"], 1)],
        ["Annual fund fee (percent)", num(f["fee"])], ["Expected inflation (percent)", num(f["inflation"], 1)],
        ["Horizon (years)", str(f["gh"])], ["Compounding", "annual"]]) + (
        "\n\nAssumptions: the fee is deducted from the gross return once a year, so the net annual return "
        "equals (1 + gross return) times (1 - fee) minus 1. Returns and fees are applied at each year end.")
def ctx_mort(f):
    return H(f, "mortgage terms") + table(["Item", "Value"], [
        ["Original principal", money(f["principal"])], ["Annual interest rate (percent)", num(f["mrate"])],
        ["Term (years)", str(f["term"])], ["Payments per year", "12"]]) + (
        "\n\nAssumptions: the rate is fixed for the full term; interest compounds monthly at one twelfth of the "
        "annual rate; payments are equal and made at each month end; there are no fees, penalties or prepayments.")
def ctx_mort_extra(f):
    return H(f, "mortgage terms with extra principal") + table(["Item", "Value"], [
        ["Original principal", money(f["principal"])], ["Annual interest rate (percent)", num(f["mrate"])],
        ["Term (years)", str(f["term"])], ["Payments per year", "12"],
        ["Scheduled monthly payment", money(f["pay_sched"])],
        ["Extra monthly principal payment", money(f["extra"])]]) + (
        "\n\nAssumptions: the rate is fixed; interest compounds monthly at one twelfth of the annual rate; the "
        "scheduled payment is unchanged and the extra amount is applied to principal every month until repaid.")
NOTE = ("\n\nAssumptions: contributions are made at the end of each month; the nominal return compounds "
        "monthly; no fees or taxes are included.")
def ctx_save(f):
    return H(f, "household profile") + table(["Item", "Value"], [
        ["Gross monthly income", money(f["income"])], ["Essential monthly expenses", money(f["essential"])],
        ["Discretionary monthly spending", money(f["disc"])], ["Current invested savings", money(f["portfolio"])],
        ["Target corpus", money(f["target"])], ["Years to target", str(f["years"])],
        ["Expected nominal annual return (percent)", num(f["nominal"], 1)]]) + NOTE
def ctx_years(f):
    return H(f, "household profile") + table(["Item", "Value"], [
        ["Gross monthly income", money(f["income"])], ["Essential monthly expenses", money(f["essential"])],
        ["Discretionary monthly spending", money(f["disc"])], ["Current invested savings", money(f["portfolio"])],
        ["Target corpus", money(f["target"])], ["Monthly savings", money(f["save"])],
        ["Expected nominal annual return (percent)", num(f["nominal"], 1)]]) + NOTE
def ctx_rate(f):
    return H(f, "household profile") + table(["Item", "Value"], [
        ["Gross monthly income", money(f["income"])], ["Essential monthly expenses", money(f["essential"])],
        ["Discretionary monthly spending", money(f["disc"])]]) + NOTE
def ctx_cash(f):
    return H(f, "household profile") + table(["Item", "Value"], [
        ["Cash reserve", money(f["cash"])], ["Essential monthly expenses", money(f["essential"])]]) + (
        "\n\nAssumptions: the cash reserve is held in a savings account and is not invested.")
def ctx_withdraw(f):
    return H(f, "withdrawal plan") + table(["Item", "Value"], [
        ["Starting portfolio", money(f["wport"])], ["First-year withdrawal rate (percent)", num(f["wrate"], 1)],
        ["Withdrawal growth (percent)", num(f["wd_growth"], 1)],
        ["Portfolio return after fees (percent)", num(f["post_ret"], 1)],
        ["Horizon (years)", str(f["horizon"])]]) + (
        "\n\nAssumptions: the first withdrawal is taken at the end of year 1; each later withdrawal grows by the "
        "stated withdrawal growth; the portfolio earns the stated return after fees; withdrawals are annual, at year end.")
def ctx_taxable(f):
    return H(f, "withdrawal sequencing") + table(["Item", "Value"], [
        ["Taxable account balance", money(f["taxable"])], ["Annual spending need", money(f["spend"])],
        ["Return on the taxable account (percent)", "4"],
        ["Withdrawal order", "taxable first, then tax-deferred"]]) + (
        "\n\nAssumptions: withdrawals are taken once a year at year end; the taxable account earns the stated "
        "return; the full annual spending need is taken from the taxable account until it can no longer cover it.")
def ctx_corpus(f):
    return H(f, "retirement income target") + table(["Item", "Value"], [
        ["Target monthly spending in year 1", money(f["monthly_spend"])],
        ["Assumed withdrawal rate (percent)", "4"]]) + (
        "\n\nAssumptions: the first-year withdrawal equals twelve times the monthly spending figure; the "
        "withdrawal rate is applied to the starting portfolio.")
def ctx_goals(f):
    return H(f, "goal plan") + table(["Goal", "Target", "Funded", "Years", "Monthly contribution"],
                                     [[g["name"], money(g["target"]), money(g["funded"]), str(g["years"]),
                                       money(g["contrib"])] for g in f["goals"]]) + (
        "\n\nAssumptions: the assumed annual return is 5.5 percent and compounds monthly; contributions are made "
        "at each month end.")
def ctx_card(f):
    return H(f, "card repayment") + table(["Card", "Balance", "Annual rate (percent)", "Monthly payment"],
                                          [[f["name"] + " card", money(f["card_bal"]), num(f["card_apr"], 1),
                                            money(f["card_pay"])]]) + (
        "\n\nAssumptions: interest compounds monthly at one twelfth of the annual rate; the stated payment is "
        "made at each month end and is not increased.")
def ctx_holdings(f):
    return H(f, "account summary at 31 December 2026") + table(
        ["Account", "Balance", "Annual fee (percent)", "Monthly contribution"],
        [[a["name"], money(a["balance"]), num(a["fee"]), money(a["contrib"])] for a in f["accounts"]]) + (
        "\n\nNotes:\n1. The annual fee is charged on the average balance.\n"
        "2. The Dune cash reserve is held for emergencies and is not invested.")
def ctx_statement(f):
    s = f["stmt"]
    return H(f, "monthly cash-flow statement") + table(["Category", "August 2026", "September 2026"], [
        ["Take-home pay", money(s["take_aug"]), money(s["take_sep"])],
        ["Housing", money(s["housing_aug"]), money(s["housing"])],
        ["Utilities", money(s["utilities_aug"]), money(s["utilities"])],
        ["Groceries", money(s["groceries_aug"]), money(s["groceries"])],
        ["Transport", money(s["transport_aug"]), money(s["transport"])],
        ["Childcare", money(s["childcare_aug"]), money(s["childcare"])],
        ["Medical", money(s["medical_aug"]), money(s["medical"])],
        ["One-off expense", money(s["oneoff_aug"]), "n/a"],
        ["Discretionary", money(s["disc_aug"]), money(s["disc"])],
        ["Total outflows", money(s["tot_aug"]), money(s["tot_sep"])],
        ["Net cash flow", money(s["net_aug"]), money(s["net_sep"])],
        ["Two-month total outflows", "", money(s["two_month"])]]) + (
        "\n\nNotes:\n1. An entry of n/a means no amount had posted for the month; the figure is treated as zero in the totals.\n"
        "2. All amounts in the table are in whole dollars.\n"
        "3. The annual home-insurance premium of 1240 is billed separately in October and is not included in total outflows.\n"
        "4. The two-month total spans August and September and has no separate single-month value.")

# --------------------------------------------------------------------- rows
def r_calc(f, ctx, q, gt, tol="abs:1"):
    return {"task": "calc", "fx": f["key"], "context": ctx, "question": q, "gt": gt,
            "atype": "number", "tol": tol}
def r_extr(f, ctx, q, gt):
    return {"task": "extraction", "fx": f["key"], "context": ctx, "question": q, "gt": str(gt),
            "atype": "text", "tol": "normalized"}
def r_qa(f, ctx, q, gt, atype="text", tol="normalized"):
    return {"task": "qa", "fx": f["key"] if f else "FREE", "context": ctx, "question": q,
            "gt": gt, "atype": atype, "tol": tol}
def pick(lst, start, j, stride=37):
    return lst[(start + j * stride) % len(lst)]

# --------------------------------------------------------------------- calc
Q_FV_FEE = "What is the projected balance after the stated horizon if the annual fee is deducted from the gross return each year?"
Q_FV_NOFEE = "What would the balance be after the stated horizon if no fund fee were charged?"
Q_FEE_COST = "How many dollars of the no-fee ending balance are lost to the annual fee over the stated horizon?"
Q_DOUBLE = "At the stated gross annual return, how many years does the starting balance take to double? Answer to two decimals."
Q_RULE72 = ("What is the rule of 72 estimate minus the exact doubling time at the stated gross return, in years? "
            "Answer to two decimals; a negative value means the rule underestimates.")
Q_REAL = "What is the real annual return after inflation, in percent?"
Q_REAL_FEE = "What is the real annual return after both the stated fee and inflation, in percent?"
Q_PAY = "What equal monthly payment amortises the loan over the stated term? Answer in dollars per month."
Q_INT = "If the loan is held to maturity, how much total interest is paid?"
Q_MONTHS = "How many months earlier is the loan repaid if the extra monthly principal payment is made every month?"
Q_INT_SAVED = "How much interest is saved over the life of the loan by making the extra monthly principal payment?"
Q_SAVE_RATE = "What monthly savings rate, in percent of gross income, is required to reach the target corpus in the stated number of years?"
Q_YEARS = "At the stated monthly savings and return, how many years are required to reach the target corpus? Answer to two decimals."
Q_CUR_RATE = "What is the current monthly savings rate, in percent of gross income?"
Q_CASH = "How many months of essential expenses does the cash reserve cover? Answer to two decimals."
Q_WD_BAL = "What is the portfolio balance after the stated horizon, after all withdrawals?"
Q_TAX_YEARS = "After how many complete years can the taxable account no longer fund the full annual withdrawal?"
Q_CORPUS = "What portfolio balance is required to support the stated first-year spending at the stated withdrawal rate?"
Q_CARD = "How many months does it take to clear the stated card balance at the stated monthly payment?"
def gen_calc(fx):
    rows = []
    spec = [
        ("fv_fee", 16, ctx_growth, Q_FV_FEE, lambda f, j: round(fv(f["portfolio"], net_of(f["gross"], f["fee"]), f["gh"]), 2), "abs:1"),
        ("fv_nofee", 14, ctx_growth, Q_FV_NOFEE, lambda f, j: round(fv(f["portfolio"], f["gross"] / 100.0, f["gh"]), 2), "abs:1"),
        ("fee_cost", 16, ctx_growth, Q_FEE_COST, lambda f, j: round(fv(f["portfolio"], f["gross"] / 100.0, f["gh"]) - fv(f["portfolio"], net_of(f["gross"], f["fee"]), f["gh"]), 2), "abs:10"),
        ("double_exact", 14, ctx_growth, Q_DOUBLE, lambda f, j: round(math.log(2.0) / math.log(1.0 + f["gross"] / 100.0), 2), "abs:0.1"),
        ("double_rule72", 14, ctx_growth, Q_RULE72, lambda f, j: round(72.0 / f["gross"] - math.log(2.0) / math.log(1.0 + f["gross"] / 100.0), 2), "abs:0.1"),
        ("real_return", 14, ctx_growth, Q_REAL, lambda f, j: round(real_pct(f["gross"] / 100.0, f["inflation"] / 100.0), 2), "abs:0.1"),
        ("real_after_fee", 14, ctx_growth, Q_REAL_FEE, lambda f, j: round(real_pct(net_of(f["gross"], f["fee"]), f["inflation"] / 100.0), 2), "abs:0.1"),
        ("mort_payment", 16, ctx_mort, Q_PAY, lambda f, j: round(mortgage_payment(f["principal"], f["mrate"], f["term"]), 2), "abs:1"),
        ("mort_interest", 14, ctx_mort, Q_INT, lambda f, j: round(mortgage_payment(f["principal"], f["mrate"], f["term"]) * f["term"] * 12 - f["principal"], 2), "abs:10"),
        ("mort_months_saved", 16, ctx_mort_extra, Q_MONTHS, lambda f, j: payoff(f["principal"], f["mrate"], f["pay_sched"])[0] - payoff(f["principal"], f["mrate"], f["pay_sched"] + f["extra"])[0], "abs:1"),
        ("mort_interest_saved", 14, ctx_mort_extra, Q_INT_SAVED, lambda f, j: round(payoff(f["principal"], f["mrate"], f["pay_sched"])[1] - payoff(f["principal"], f["mrate"], f["pay_sched"] + f["extra"])[1], 2), "abs:10"),
        ("savings_rate_needed", 16, ctx_save, Q_SAVE_RATE, lambda f, j: round(pmt_for(f["target"], f["portfolio"], f["nominal"] / 1200.0, f["years"] * 12) / f["income"] * 100.0, 2), "abs:0.1"),
        ("years_to_target", 14, ctx_years, Q_YEARS, lambda f, j: round(years_to(f["target"], f["portfolio"], f["save"], f["nominal"] / 1200.0), 2), "abs:0.1"),
        ("current_savings_rate", 12, ctx_rate, Q_CUR_RATE, lambda f, j: round(f["save"] / f["income"] * 100.0, 2), "abs:0.1"),
        ("emergency_months", 12, ctx_cash, Q_CASH, lambda f, j: round(f["cash"] / f["essential"], 2), "abs:0.1"),
        ("wd_balance", 14, ctx_withdraw, Q_WD_BAL, lambda f, j: round(wd_balance(f["wport"], f["first_wd"], f["wd_growth"] / 100.0, f["post_ret"] / 100.0, f["horizon"]), 2), "abs:1"),
        ("wd_taxable_years", 12, ctx_taxable, Q_TAX_YEARS, lambda f, j: full_years(f["taxable"], f["spend"], 0.04), "abs:1"),
        ("required_corpus", 12, ctx_corpus, Q_CORPUS, lambda f, j: round(f["monthly_spend"] * 12 / 0.04, 2), "abs:10"),
        ("goal_gap", 12, ctx_goals, lambda f, j: "How much additional monthly saving is required for the " + f["goals"][j % 3]["name"] + " goal to reach its target at the stated return?", lambda f, j: round(f["goals"][j % 3]["required"] - f["goals"][j % 3]["contrib"], 2), "abs:1"),
        ("card_months", 14, ctx_card, Q_CARD, lambda f, j: payoff(f["card_bal"], f["card_apr"], f["card_pay"])[0], "abs:1"),
    ]
    for fam, count, cf, q, fn, tol in spec:
        start = off()
        for j in range(count):
            f = pick(fx, start, j)
            rows.append(r_calc(f, cf(f), q(f, j) if callable(q) else q, fn(f, j), tol))
    return rows

# --------------------------------------------------------------- extraction
def top_cat(f, month, rank=1):
    s = f["stmt"]
    key = "_aug" if month == "August 2026" else ""
    vals = {c: s[c + key] for c in ("housing", "utilities", "groceries", "transport", "childcare", "medical", "disc")}
    if key:
        vals["one-off expense"] = s["oneoff_aug"]
    order = sorted(vals.values(), reverse=True)
    target = order[rank - 1]
    best = [k for k, v in vals.items() if v == target][0]
    return {"disc": "Discretionary"}.get(best, best.capitalize())
def gen_extraction(fx):
    rows = []
    spec = []
    for key, label in (("housing", "Housing"), ("groceries", "Groceries"), ("transport", "Transport"), ("childcare", "Childcare")):
        spec.append(("cat_" + key, 10, ctx_statement,
                     "What amount is stated for " + label + " in the September 2026 column? Answer with the digits exactly as shown.",
                     (lambda k: lambda f: money(f["stmt"][k]))(key)))
    for month, count, tag in (("August 2026", 10, "aug"), ("September 2026", 8, "sep")):
        spec.append(("highest_" + tag, count, ctx_statement,
                     "Which expense category has the largest amount in the " + month + " column?",
                     (lambda m: lambda f: top_cat(f, m))(month)))
        spec.append(("second_" + tag, 8, ctx_statement,
                     "Which expense category has the second-largest amount in the " + month + " column?",
                     (lambda m: lambda f: top_cat(f, m, 2))(month)))
    spec += [
        ("na_meaning", 15, ctx_statement, "What does an entry of n/a mean in this statement? Answer with the wording used in the notes.", lambda f: "no amount had posted for the month"),
        ("table_units", 8, ctx_statement, "In what unit are the amounts in the cash-flow table expressed?", lambda f: "whole dollars"),
        ("twomonth_total", 10, ctx_statement, "What two-month total outflows figure is stated in the statement? Answer with the digits exactly as shown.", lambda f: money(f["stmt"]["two_month"])),
        ("total_aug", 18, ctx_statement, "What total outflows figure is reported for August 2026? Answer with the digits exactly as shown.", lambda f: money(f["stmt"]["tot_aug"])),
        ("net_sep", 15, ctx_statement, "What net cash flow is reported for September 2026? Answer with the digits exactly as shown.", lambda f: money(f["stmt"]["net_sep"])),
        ("note_premium", 13, ctx_statement, "What annual home-insurance premium is stated in the notes?", lambda f: "1240"),
        ("blank_category", 13, ctx_statement, "Which category has an n/a entry in the September 2026 column?", lambda f: "One-off expense"),
        ("acct_fee_basalt", 8, ctx_holdings, "What annual fee is stated for the Basalt traditional retirement account? Answer as a percent value.", lambda f: num(f["accounts"][1]["fee"])),
        ("acct_fee_cedar", 8, ctx_holdings, "What annual fee is stated for the Cedar tax-free retirement account? Answer as a percent value.", lambda f: num(f["accounts"][2]["fee"])),
        ("largest_balance", 14, ctx_holdings, "Which account holds the largest balance?", lambda f: max(f["accounts"], key=lambda a: a["balance"])["name"]),
        ("contrib_alpine", 7, ctx_holdings, "What monthly contribution is stated for the Alpine taxable brokerage account? Answer with the digits exactly as shown.", lambda f: money(f["accounts"][0]["contrib"])),
        ("contrib_basalt", 7, ctx_holdings, "What monthly contribution is stated for the Basalt traditional retirement account? Answer with the digits exactly as shown.", lambda f: money(f["accounts"][1]["contrib"])),
        ("zero_fee_account", 10, ctx_holdings, "Which account is stated to carry no annual fee?", lambda f: "Dune cash reserve"),
    ]
    for fam, count, cf, q, fn in spec:
        start = off()
        for j in range(count):
            f = pick(fx, start, j)
            rows.append(r_extr(f, cf(f), q, fn(f)))
    return rows

# ----------------------------------------------------------------------- qa
def ctx_two(f, g):
    return (UNITS + "\n\nHousehold comparison for the " + f["name"] + " and " + g["name"] + " households.\n\n" +
            table(["Item", f["name"], g["name"]], [
                ["Gross monthly income", money(f["income"]), money(g["income"])],
                ["Essential monthly expenses", money(f["essential"]), money(g["essential"])],
                ["Discretionary monthly spending", money(f["disc"]), money(g["disc"])]]) +
            "\n\nAssumptions: saving equals gross income minus the two spending lines; the savings rate is "
            "saving divided by gross income.")
def ctx_seq(f, amt):
    return H(f, "withdrawal policy") + table(["Account", "Balance", "Draw order"], [
        ["Alpine taxable brokerage", money(f["accounts"][0]["balance"]), "1"],
        ["Basalt traditional retirement", money(f["accounts"][1]["balance"]), "2"],
        ["Cedar tax-free retirement", money(f["accounts"][2]["balance"]), "3"]]) + (
        "\n\nPolicy: each year's spending is drawn from the taxable account first, then from the traditional "
        "retirement account, then from the tax-free account.\n\nDraw amount: " + money(amt) + " dollars.")
def ctx_fees(f):
    accs = f["accounts"][:3]
    return H(f, "fund fee comparison") + table(["Fund", "Balance", "Annual fee (percent)"],
                                                [[a["name"], money(a["balance"]), num(a["fee"])] for a in accs]) + (
        "\n\nNote: annual fee cost equals balance times the annual fee rate.")
def ctx_mort2(f, b_rate):
    return H(f, "mortgage options") + table(["Option", "Principal", "Annual rate (percent)", "Term (years)"], [
        ["Option A", money(f["principal"]), num(f["mrate"]), "30"],
        ["Option B", money(f["principal"]), num(b_rate), "15"]]) + (
        "\n\nAssumptions: both loans are fully amortising with equal monthly payments; interest compounds "
        "monthly at one twelfth of the annual rate; total interest equals payments minus principal.")
def gen_qa(fx):
    rows = []
    def add(count, fn):
        start = off()
        for j in range(count):
            rows.append(fn(pick(fx, start, j), j))
    add(16, lambda f, j: r_qa(f, ctx_goals(f), "Which goal has the lowest funded ratio, where the funded ratio equals funded divided by target?", min(f["goals"], key=lambda g: float(g["funded"]) / g["target"])["name"]))
    add(15, lambda f, j: r_qa(f, ctx_statement(f), "Which expense category accounts for the largest share of total outflows in September 2026?", top_cat(f, "September 2026")))
    add(11, lambda f, j: r_qa(None, ctx_two(f, fx[(j + 61) % len(fx)]), "Which household has the higher savings rate?",
                              f["name"] if (f["income"] - f["essential"] - f["disc"]) / float(f["income"]) >= (fx[(j + 61) % len(fx)]["income"] - fx[(j + 61) % len(fx)]["essential"] - fx[(j + 61) % len(fx)]["disc"]) / float(fx[(j + 61) % len(fx)]["income"]) else fx[(j + 61) % len(fx)]["name"]))
    add(13, lambda f, j: r_qa(f, ctx_seq(f, f["accounts"][0]["balance"] + (20 + (j * 7) % 70) * 1000), "Under the stated draw order, how much of the draw amount comes from the traditional retirement account?", (20 + (j * 7) % 70) * 1000, "number", "abs:1"))
    add(11, lambda f, j: r_qa(f, ctx_fees(f), "Rank the three funds from lowest to highest annual fee cost in dollars.", [a["name"] for a in sorted(f["accounts"][:3], key=lambda a: a["balance"] * a["fee"])], "list", "ordered"))
    add(11, lambda f, j: r_qa(f, ctx_mort2(f, round(f["mrate"] + 0.4, 2)), "Which option has the lower total interest over the full term?",
                              "Option A" if mortgage_payment(f["principal"], f["mrate"], 30) * 360 - f["principal"] <= mortgage_payment(f["principal"], round(f["mrate"] + 0.4, 2), 15) * 180 - f["principal"] else "Option B"))
    add(13, lambda f, j: r_qa(f, ctx_goals(f), "Which goal has the largest dollar gap between its target and its funded amount?", max(f["goals"], key=lambda g: g["target"] - g["funded"])["name"]))
    add(12, lambda f, j: r_qa(f, ctx_goals(f), "At the stated contributions and return, which goal reaches its target soonest?", min(f["goals"], key=lambda g: years_to(g["target"], g["funded"], g["contrib"], 0.055 / 12.0))["name"]))
    add(11, lambda f, j: r_qa(f, ctx_holdings(f), "Which account has the largest balance after one year's annual fee is deducted and no other change is made?", max(f["accounts"], key=lambda a: a["balance"] * (1 - a["fee"]))["name"]))
    add(11, lambda f, j: r_qa(f, ctx_holdings(f), "What total monthly contribution is stated across all four accounts?", sum(a["contrib"] for a in f["accounts"]), "number", "abs:1"))
    add(14, lambda f, j: r_qa(f, ctx_goals(f), "What is the funded ratio of the " + f["goals"][j % 3]["name"] + " goal, in percent? Funded ratio equals funded divided by target.", round(f["goals"][j % 3]["funded"] / float(f["goals"][j % 3]["target"]) * 100.0, 2), "number", "abs:0.1"))
    add(11, lambda f, j: r_qa(f, ctx_mort2(f, round(f["mrate"] + 0.4, 2)), "How much higher is Option B's monthly payment than Option A's?", round(mortgage_payment(f["principal"], round(f["mrate"] + 0.4, 2), 15) - mortgage_payment(f["principal"], f["mrate"], 30), 2), "number", "abs:1"))
    add(14, lambda f, j: r_qa(f, ctx_statement(f), "What savings rate does the September statement imply, in percent of take-home pay? Use net cash flow divided by take-home pay.", round(f["stmt"]["net_sep"] / float(f["stmt"]["take_sep"]) * 100.0, 2), "number", "abs:0.1"))
    add(13, lambda f, j: r_qa(f, ctx_holdings(f), "What is the balance-weighted average annual fee across the four accounts, in percent?", round(sum(a["balance"] * a["fee"] for a in f["accounts"]) / float(sum(a["balance"] for a in f["accounts"])), 3), "number", "abs:0.01"))
    for q, a in FREE_QA:
        rows.append(r_qa(None, "", q, a))
    return rows
FREE_QA = [
    ("In finance, what does the real return measure?", "The return after removing the effect of inflation, so it measures the change in purchasing power."),
    ("Define real return in one sentence.", "Real return is the return on an investment after subtracting the effect of inflation."),
    ("How does real return differ from nominal return?", "Nominal return is the stated return before inflation, while real return adjusts that figure for the change in prices."),
    ("What is a fund expense ratio?", "The annual fee a fund charges, expressed as a percentage of assets under management."),
    ("Define expense ratio as it applies to a fund.", "An expense ratio is the fund's annual operating cost divided by its average assets, quoted as a percentage."),
    ("Why does an expense ratio reduce an investor's return?", "The fee is deducted from the fund's assets each year, so the balance compounds on a smaller base than the gross return implies."),
    ("What does amortisation of a loan mean?", "Repaying a loan through scheduled payments that cover both interest and principal so the balance reaches zero at maturity."),
    ("Define a fully amortising loan.", "A fully amortising loan is one whose level scheduled payments repay all principal and interest by the stated maturity date."),
    ("Why does the interest share of a mortgage payment fall over time?", "Interest is charged on the remaining balance, which falls as principal is repaid, so the interest portion of each level payment declines."),
    ("How is a household savings rate calculated?", "Monthly saving divided by gross monthly income, expressed as a percentage."),
    ("Define savings rate for a household.", "A household savings rate is the share of gross income that is saved rather than spent, usually expressed as a percentage."),
    ("Why does a higher savings rate shorten the time to a target corpus?", "More money is added to the portfolio each period and that money compounds, so the target is reached in fewer years."),
    ("What does the rule of 72 estimate?", "The number of years for an investment to double, estimated by dividing 72 by the annual percentage return."),
    ("Define the rule of 72.", "The rule of 72 is a shortcut that divides 72 by the annual percentage return to approximate the doubling time of an investment."),
    ("When does the rule of 72 become less accurate?", "It is least accurate at high returns, where it overstates the exact doubling time derived from compound interest."),
    ("Why does more frequent compounding raise the effective annual rate?", "Interest is added to the balance sooner, so each later period earns interest on a larger balance at the same nominal rate."),
    ("Define effective annual rate.", "The effective annual rate is the actual annual growth after accounting for the number of compounding periods within the year."),
    ("Compare annual and monthly compounding at the same nominal rate.", "Monthly compounding produces a higher ending balance because interest is added to the balance twelve times a year instead of once."),
    ("Why is the geometric mean return lower than the arithmetic mean when returns vary?", "The geometric mean reflects compounding and volatility drag, while the arithmetic mean ignores the order and dispersion of returns."),
    ("Define geometric mean return.", "The geometric mean return is the constant annual rate that compounds to the same ending value as the actual sequence of returns."),
    ("Why does volatility drag reduce compound growth?", "A loss requires a larger percentage gain to recover, so the same average return with more dispersion produces a lower ending value."),
    ("What does a withdrawal rate measure in a retirement plan?", "The annual withdrawal divided by the starting portfolio value, expressed as a percentage."),
    ("Define withdrawal rate.", "A withdrawal rate is the first-year withdrawal expressed as a percentage of the portfolio value at the start of the plan."),
    ("Why does a higher withdrawal rate shorten portfolio life?", "More capital leaves the portfolio each year, leaving a smaller balance to earn a return and fund later withdrawals."),
]

# ----------------------------------------------------------- classification
RISK_ITEMS = ["I prefer stable returns even when they are lower.", "I would sell after a sharp market fall.", "I check portfolio values frequently.", "I accept short-term losses for higher long-term returns.", "I prefer guaranteed outcomes over uncertain ones.", "I would increase contributions after a market fall.", "I need the money within three years.", "I am comfortable with large swings in value."]
RISK_BASE = {"conservative": [1, 2, 1, 2, 1, 1, 2, 1], "moderate": [3, 2, 3, 2, 3, 2, 3, 2],
             "growth": [4, 3, 4, 3, 4, 3, 4, 3], "aggressive": [5, 4, 5, 4, 5, 4, 5, 4]}
def c_row(f, label, ctx, q):
    return {"task": "classification", "fx": f["key"], "atype": "label", "tol": "exact",
            "gt": label, "context": ctx, "question": q}
def gen_classification(fx):
    rows = []
    bands = {"conservative": (9, 15), "moderate": (16, 23), "growth": (24, 31), "aggressive": (32, 39)}
    for label, rng in bands.items():
        start = off()
        for k in range(5):
            f = pick(fx, start, k)
            ans = [max(1, min(5, v + R.choice([-1, 0, 0, 1]))) for v in RISK_BASE[label]]
            tries = 0
            while not (rng[0] <= sum(ans) <= rng[1]) and tries < 200:
                ans[R.randrange(8)] = R.randrange(1, 6)
                tries += 1
            if not (rng[0] <= sum(ans) <= rng[1]):
                ans = list(RISK_BASE[label])
            ctx = H(f, "risk tolerance questionnaire") + table(
                ["Item", "Statement", "Answer (1-5)"],
                [[str(i + 1), RISK_ITEMS[i], str(ans[i])] for i in range(8)]) + (
                "\n\nScoring rule: add the eight answers. A total of 15 or less is conservative; 16 to 23 is "
                "moderate; 24 to 31 is growth; 32 or more is aggressive.")
            rows.append(c_row(f, label, ctx, "Using the stated scoring rule, which risk label applies to this questionnaire? Answer with one label from {conservative, moderate, growth, aggressive}."))
    for label, rng in (("ahead", (18.5, 24.0)), ("on track", (15.2, 17.6)),
                       ("slightly behind", (10.4, 14.6)), ("significantly behind", (5.0, 9.4))):
        start = off()
        for k in range(5):
            f = pick(fx, start, k)
            contrib = int(round(f["income"] * R.uniform(rng[0], rng[1]) / 100.0 / 5.0)) * 5
            ctx = H(f, "savings rate review") + table(["Item", "Value"], [
                ["Gross monthly income", money(f["income"])], ["Monthly contribution to savings", money(contrib)],
                ["Target savings rate (percent)", "15"]]) + (
                "\n\nBands: ahead if the savings rate is at least 18 percent; on track if it is at least 15 percent "
                "but below 18 percent; slightly behind if it is at least 10 percent but below 15 percent; "
                "significantly behind if it is below 10 percent.")
            rows.append(c_row(f, label, ctx, "Classify the household savings rate using the stated bands. Answer with one label from {ahead, on track, slightly behind, significantly behind}."))
    for label, fees in (("low cost", [0.05, 0.12, 0.18]), ("moderate cost", [0.32, 0.45, 0.38]),
                        ("high cost", [0.85, 1.05, 0.92])):
        start = off()
        for k in range(7):
            f = pick(fx, start, k)
            bals = [f["accounts"][0]["balance"], f["accounts"][1]["balance"], f["accounts"][2]["balance"]]
            ctx = H(f, "fee review") + table(["Fund", "Balance", "Annual fee (percent)"],
                                             [["Fund A", money(bals[0]), num(fees[0])], ["Fund B", money(bals[1]), num(fees[1])],
                                              ["Fund C", money(bals[2]), num(fees[2])]]) + (
                "\n\nRule: compute the balance-weighted average annual fee. Below 0.25 percent is low cost; 0.25 "
                "percent to 0.60 percent inclusive is moderate cost; above 0.60 percent is high cost.")
            rows.append(c_row(f, label, ctx, "Classify the portfolio's balance-weighted average fee using the stated rule. Answer with one label from {low cost, moderate cost, high cost}."))
    for label, rng in (("comfortable", (0.20, 0.26)), ("stretched", (0.30, 0.34)), ("at risk", (0.40, 0.48))):
        start = off()
        for k in range(7):
            f = pick(fx, start, k)
            pay = mortgage_payment(f["principal"], f["mrate"], f["term"])
            income = int(round(pay / R.uniform(rng[0], rng[1]) / 50.0)) * 50
            ctx = H(f, "mortgage affordability check") + table(["Item", "Value"], [
                ["Loan principal", money(f["principal"])], ["Annual interest rate (percent)", num(f["mrate"])],
                ["Term (years)", str(f["term"])], ["Gross monthly income", money(income)]]) + (
                "\n\nRule: divide the monthly mortgage payment by gross monthly income. At or below 0.28 is "
                "comfortable; above 0.28 and up to 0.36 is stretched; above 0.36 is at risk.")
            rows.append(c_row(f, label, ctx, "Classify the mortgage using the stated payment-to-income rule. Answer with one label from {comfortable, stretched, at risk}."))
    for label, rng in (("sustainable", (2.6, 3.8)), ("borderline", (4.1, 4.8)), ("unsustainable", (5.1, 6.2))):
        start = off()
        for k in range(6):
            f = pick(fx, start, k)
            amt = int(round(f["wport"] * R.uniform(rng[0], rng[1]) / 100.0 / 100.0)) * 100
            ctx = H(f, "withdrawal rate review") + table(["Item", "Value"], [
                ["Portfolio balance", money(f["wport"])], ["Planned annual withdrawal", money(amt)]]) + (
                "\n\nRule: divide the planned annual withdrawal by the portfolio balance. At or below 3.9 percent "
                "is sustainable; above 3.9 and below 5.0 percent is borderline; 5.0 percent or more is unsustainable.")
            rows.append(c_row(f, label, ctx, "Classify the planned withdrawal using the stated rule. Answer with one label from {sustainable, borderline, unsustainable}."))
    return rows

# ----------------------------------------------------------- summarization
def gen_summary(fx):
    rows = []
    for j in range(20):
        f = pick(fx, 7, j)
        ctx = (H(f, "household plan memo, prepared 12 March 2026") + "Gross monthly income is " + money(f["income"]) +
               " and monthly saving is " + money(f["save"]) + ". Invested savings total " + money(f["portfolio"]) +
               " against a target corpus of " + money(f["target"]) + " in " + str(f["years"]) + " years. The plan assumes a nominal return of " +
               num(f["nominal"], 1) + " percent and inflation of " + num(f["inflation"], 1) + " percent. The mortgage balance is " +
               money(f["principal"]) + " at " + num(f["mrate"]) + " percent with " + str(f["term"]) + " years remaining.\n\n"
               "Recommendation: hold the monthly contribution and keep the mortgage on its scheduled payment.")
        gt = ("The household saves " + money(f["save"]) + " a month toward a " + money(f["target"]) + " target in " +
              str(f["years"]) + " years, assuming a " + num(f["nominal"], 1) + " percent nominal return and " +
              num(f["inflation"], 1) + " percent inflation. It also carries a " + money(f["principal"]) +
              " mortgage at " + num(f["mrate"]) + " percent.")
        rows.append({"task": "summarization", "fx": f["key"], "atype": "text", "tol": "normalized", "gt": gt, "context": ctx,
                     "question": "Summarize the memo in two sentences for the household file, keeping the target corpus, the assumed return and the mortgage balance."})
    for j in range(20):
        f = pick(fx, 53, j)
        low, high = f["fee"], round(f["fee"] + 1.0, 2)
        ctx = (H(f, "fund fee memo") + "Two funds are compared on a starting balance of " + money(f["portfolio"]) +
               ". The low-cost fund charges " + num(low) + " percent a year and the active fund charges " + num(high) + " percent. Both are assumed to earn " + num(f["gross"], 1) + " percent gross for " + str(f["years"]) +
               " years.\n\nRecommendation: the difference in annual fees is the main reason the memo favours the low-cost fund.")
        gt = ("The low-cost fund charges " + num(low) + " percent a year against " + num(high) + " percent for the active fund, on a " +
              money(f["portfolio"]) + " balance over " + str(f["years"]) + " years at " + num(f["gross"], 1) + " percent gross.")
        rows.append({"task": "summarization", "fx": f["key"], "atype": "text", "tol": "normalized", "gt": gt, "context": ctx,
                     "question": "Summarize the fee memo in two sentences, keeping both fee rates, the balance and the horizon."})
    for j in range(20):
        f = pick(fx, 91, j)
        rate_b = round(f["mrate"] + 0.4, 2)
        ctx = (H(f, "mortgage options memo") + "Option A is a " + str(f["term"]) + " year loan of " + money(f["principal"]) +
               " at " + num(f["mrate"]) + " percent. Option B is a 15 year loan of the same amount at " + num(rate_b) +
               " percent. Both are fully amortising with equal monthly payments and no fees.\n\n"
               "Recommendation: compare total interest over the full term before choosing.")
        gt = ("Option A is a " + str(f["term"]) + " year loan of " + money(f["principal"]) + " at " + num(f["mrate"]) +
              " percent, while Option B is a 15 year loan at " + num(rate_b) + " percent.")
        rows.append({"task": "summarization", "fx": f["key"], "atype": "text", "tol": "normalized", "gt": gt, "context": ctx,
                     "question": "Summarize the mortgage memo in two sentences, keeping both rates, both terms and the loan amount."})
    for j in range(20):
        f = pick(fx, 37, j)
        ctx = (H(f, "withdrawal plan memo") + "The portfolio starts at " + money(f["wport"]) + " and the first-year withdrawal is " +
               num(f["wrate"], 1) + " percent of that balance. Withdrawals grow by " + num(f["wd_growth"], 1) +
               " percent a year, the portfolio is assumed to earn " + num(f["post_ret"], 1) + " percent after fees, and the plan runs for " +
               str(f["horizon"]) + " years.\n\nRecommendation: review the plan if the return assumption falls.")
        gt = ("The plan withdraws " + num(f["wrate"], 1) + " percent of a " + money(f["wport"]) +
              " portfolio in the first year, grows withdrawals by " + num(f["wd_growth"], 1) + " percent a year and assumes a " +
              num(f["post_ret"], 1) + " percent return after fees over " + str(f["horizon"]) + " years.")
        rows.append({"task": "summarization", "fx": f["key"], "atype": "text", "tol": "normalized", "gt": gt, "context": ctx,
                     "question": "Summarize the withdrawal memo in two sentences, keeping the starting balance, the withdrawal rate, the growth rate and the return assumption."})
    for j in range(20):
        f = pick(fx, 79, j)
        gs = f["goals"]
        ctx = H(f, "goal progress memo") + " ".join(
            "The " + g["name"] + " goal has " + money(g["funded"]) + " funded against a target of " + money(g["target"]) +
            " in " + str(g["years"]) + " years." for g in gs) + "\n\nRecommendation: direct new saving to the least-funded goal first."
        worst = min(gs, key=lambda g: float(g["funded"]) / g["target"])
        gt = ("The " + worst["name"] + " goal is the least funded, with " + money(worst["funded"]) + " against a target of " +
              money(worst["target"]) + " in " + str(worst["years"]) + " years.")
        rows.append({"task": "summarization", "fx": f["key"], "atype": "text", "tol": "normalized", "gt": gt, "context": ctx,
                     "question": "Summarize the goal progress memo in two sentences, naming the least-funded goal and its figures."})
    return rows

# ---------------------------------------------------------------- tool_use
TOOLS = [
    {"name": "future_value", "description": "Compound a lump sum at a fixed annual rate with annual compounding.", "parameters": {"type": "object", "properties": {"principal": {"type": "number", "description": "Starting balance in dollars."}, "annual_rate_percent": {"type": "number", "description": "Annual rate in percent."}, "years": {"type": "number", "description": "Holding period in years."}}, "required": ["principal", "annual_rate_percent", "years"]}},
    {"name": "mortgage_payment", "description": "Level monthly payment for a fully amortising fixed-rate loan.", "parameters": {"type": "object", "properties": {"principal": {"type": "number"}, "annual_rate_percent": {"type": "number"}, "years": {"type": "number"}}, "required": ["principal", "annual_rate_percent", "years"]}},
    {"name": "real_return", "description": "Convert a nominal return and an inflation rate into a real return.", "parameters": {"type": "object", "properties": {"nominal_percent": {"type": "number"}, "inflation_percent": {"type": "number"}}, "required": ["nominal_percent", "inflation_percent"]}},
    {"name": "fee_drag", "description": "Compare ending balances with and without an annual fund fee.", "parameters": {"type": "object", "properties": {"initial_balance": {"type": "number"}, "gross_return_percent": {"type": "number"}, "fee_percent": {"type": "number"}, "years": {"type": "number"}}, "required": ["initial_balance", "gross_return_percent", "fee_percent", "years"]}},
    {"name": "amortization_balance", "description": "Remaining loan balance after a number of monthly payments.", "parameters": {"type": "object", "properties": {"principal": {"type": "number"}, "annual_rate_percent": {"type": "number"}, "years": {"type": "number"}, "months_elapsed": {"type": "number"}}, "required": ["principal", "annual_rate_percent", "years", "months_elapsed"]}},
]
def M(role, text):
    return {"role": role, "content": text}
def gen_tool(fx):
    rows = []
    def add(count, fn):
        start = off()
        for j in range(count):
            rows.append(fn(pick(fx, start, j), j))
    def fv_case(f, j):
        res = fv(f["portfolio"], f["gross"] / 100.0, f["years"])
        return {"task": "tool_use", "fx": f["key"], "gt": round(res - f["portfolio"], 2), "atype": "number", "tol": "abs:1",
                "messages": [M("user", "Project " + money(f["portfolio"]) + " dollars at " + num(f["gross"], 1) + " percent for " + str(f["years"]) + " years with annual compounding."),
                             M("assistant", "I will call future_value with principal " + money(f["portfolio"]) + ", annual_rate_percent " + num(f["gross"], 1) + " and years " + str(f["years"]) + "."),
                             M("tool", json.dumps({"future_value": round(res, 2), "principal": f["portfolio"], "annual_rate_percent": f["gross"], "years": f["years"]})),
                             M("user", "How much of that ending balance is growth rather than the original principal?")]}
    def mort_case(f, j):
        pay = mortgage_payment(f["principal"], f["mrate"], f["term"])
        return {"task": "tool_use", "fx": f["key"], "gt": round(pay * f["term"] * 12 - f["principal"], 2), "atype": "number", "tol": "abs:10",
                "messages": [M("user", "What is the monthly payment on " + money(f["principal"]) + " dollars at " + num(f["mrate"]) + " percent over " + str(f["term"]) + " years?"),
                             M("assistant", "I will call mortgage_payment with principal " + money(f["principal"]) + ", annual_rate_percent " + num(f["mrate"]) + " and years " + str(f["term"]) + "."),
                             M("tool", json.dumps({"monthly_payment": round(pay, 2), "principal": f["principal"], "annual_rate_percent": f["mrate"], "years": f["term"]})),
                             M("user", "What total interest does that payment imply over the full term?")]}
    def real_case(f, j):
        nom, infl = f["gross"], f["inflation"]
        return {"task": "tool_use", "fx": f["key"], "gt": round(real_pct(nom / 100.0, (infl + 0.5) / 100.0), 2), "atype": "number", "tol": "abs:0.1",
                "messages": [M("user", "What is the real return on a " + money(f["portfolio"]) + " dollar balance at " + num(nom, 1) + " percent nominal with " + num(infl, 1) + " percent inflation?"),
                             M("assistant", "I will call real_return with nominal_percent " + num(nom, 1) + " and inflation_percent " + num(infl, 1) + "."),
                             M("tool", json.dumps({"real_return_percent": round(real_pct(nom / 100.0, infl / 100.0), 2), "nominal_percent": nom, "inflation_percent": infl, "initial_balance": f["portfolio"]})),
                             M("user", "What would the real return be if inflation were half a point higher?")]}
    def fee_case(f, j):
        a = fv(f["portfolio"], f["gross"] / 100.0, f["years"])
        b = fv(f["portfolio"], net_of(f["gross"], f["fee"]), f["years"])
        return {"task": "tool_use", "fx": f["key"], "gt": round(a - b, 2), "atype": "number", "tol": "abs:10",
                "messages": [M("user", "Compare " + money(f["portfolio"]) + " dollars at " + num(f["gross"], 1) + " percent gross with a " + num(f["fee"]) + " percent annual fee over " + str(f["years"]) + " years."),
                             M("assistant", "I will call fee_drag with the balance, gross return, fee and horizon, then compare the two ending values."),
                             M("tool", json.dumps({"balance_without_fee": round(a, 2), "balance_with_fee": round(b, 2), "initial_balance": f["portfolio"], "gross_return_percent": f["gross"], "fee_percent": f["fee"], "years": f["years"]})),
                             M("user", "How many dollars does the fee cost over that horizon?")]}
    def amort_case(f, j):
        idx = int(f["key"][2:])
        pay = mortgage_payment(f["principal"], f["mrate"], f["term"])
        bal, r = float(f["principal"]), f["mrate"] / 1200.0
        for _ in range(60):
            bal = bal * (1 + r) - pay
        return {"task": "tool_use", "fx": f["key"], "gt": round(max(bal, 0.0), 2), "atype": "number", "tol": "abs:10",
                "messages": [M("user", "Loan reference " + str(1000 + idx * 13) + ". What is the remaining balance on " + money(f["principal"]) + " dollars at " + num(f["mrate"]) + " percent over " + str(f["term"]) + " years, after five years of payments?"),
                             M("assistant", "I will call amortization_balance with principal " + money(f["principal"]) + ", annual_rate_percent " + num(f["mrate"]) + ", years " + str(f["term"]) + " and months_elapsed 60."),
                             M("tool", "Error: missing required parameter years."),
                             M("user", "The term is " + str(f["term"]) + " years. Use 60 months elapsed.")]}
    def abstain_case(f, j):
        idx = int(f["key"][2:])
        bal = 200000 + idx * 1237
        if j % 2 == 0:
            msgs = [M("user", "Project my retirement balance. I have " + money(bal) + " dollars invested.")]
        else:
            msgs = [M("user", "Project my retirement balance of " + money(bal) + " dollars using the future_value tool."),
                    M("assistant", "I need the annual rate and the number of years as well as the balance. Only the balance was supplied, so I cannot call the tool yet."),
                    M("tool", "Error: missing required parameters annual_rate_percent, years."),
                    M("user", "I do not have those numbers. Just give me an estimate.")]
        return {"task": "tool_use", "fx": f["key"], "gt": None, "atype": "text", "tol": None, "messages": msgs}
    add(18, fv_case)
    add(18, mort_case)
    add(16, real_case)
    add(16, fee_case)
    add(16, amort_case)
    add(16, abstain_case)
    return rows

# --------------------------------------------------------------- assembly
def mask(s):
    return _mask(s)
def _mask(s):
    out, i = [], 0
    while i < len(s):
        if s[i].isdigit():
            while i < len(s) and (s[i].isdigit() or s[i] in ".,"):
                i += 1
            out.append("#")
        else:
            out.append(s[i])
            i += 1
    return "".join(out)
def norm(s):
    return " ".join(str(s).split()).strip().lower()
def finalize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["task"]].append(r)
    for task, trs in groups.items():
        by_fx = defaultdict(list)
        for r in trs:
            by_fx[r["fx"]].append(r)
        keys = sorted(by_fx, key=lambda k: hashlib.sha256((task + "|" + k).encode("utf-8")).hexdigest())
        total, cum = len(trs), 0
        for k in keys:
            g = by_fx[k]
            pos = cum + len(g) / 2.0
            split = "train" if pos < 0.8 * total else ("val" if pos < 0.9 * total else "test")
            for r in g:
                r["split"] = split
            cum += len(g)
    seq = defaultdict(int)
    out = []
    for task in ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]:
        for r in groups[task]:
            seq[task] += 1
            row = {"id": "fin_%s_%s_%06d" % (AREA, ABBR[task], seq[task]), "task": task, "source": SRC,
                   "ground_truth": r["gt"], "answer_type": r["atype"], "tolerance": r["tol"],
                   "split": r["split"], "thinking": THINK[task]}
            if task == "tool_use":
                row["messages"] = r["messages"]
                row["tools"] = TOOLS
            else:
                row["context"] = r["context"]
                row["question"] = r["question"]
                if r["context"] == "":
                    row["source"] = "knowledge:finance_general"
            out.append(row)
    return out
def audit(rows):
    fam, ctxs, seen = Counter(), set(), set()
    dups = multi = tools = 0
    for r in rows:
        if "messages" in r:
            key = norm(json.dumps(r["messages"], sort_keys=True))
            src = next((m["content"] for m in r["messages"] if m["role"] == "user"), "")
            multi += 1 if any(m["role"] == "assistant" for m in r["messages"]) else 0
            tools += 1
        else:
            key = norm(r["context"]) + "|" + norm(r["question"])
            src = r["question"]
            if r["context"]:
                ctxs.add(mask(r["context"]))
        fam[mask(src)[:160]] += 1
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()
        dups += 1 if h in seen else 0
        seen.add(h)
    top = fam.most_common(1)[0]
    return {"families": len(fam), "top_n": top[1], "top_share": round(top[1] / float(len(rows)), 4), "contexts": len(ctxs), "near_dup_pairs": dups, "tool_rows": tools, "tool_multi": multi, "tool_share": round(multi / float(tools), 3) if tools else 0.0}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    fx = build_fixtures(120)
    rows = gen_calc(fx) + gen_extraction(fx) + gen_qa(fx) + gen_classification(fx) + gen_summary(fx) + gen_tool(fx)
    want = {"calc": 280, "extraction": 220, "qa": 200, "classification": 100, "summarization": 100, "tool_use": 100}
    got = Counter(r["task"] for r in rows)
    assert dict(got) == want, (dict(got), want)
    out = finalize(rows)
    stats = audit(out)
    assert stats["families"] >= 40 and stats["top_n"] <= 40 and stats["contexts"] >= 120, stats
    assert stats["near_dup_pairs"] == 0 and stats["tool_share"] >= 0.40, stats
    path = os.path.join(here, "prompts.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    raw = open(path, "rb").read()
    report = {"area": AREA, "profile": "A", "rows": len(out), "by_task": dict(Counter(r["task"] for r in out)), "by_split": dict(Counter(r["split"] for r in out)), "by_answer_type": dict(Counter(r["answer_type"] for r in out if r["ground_truth"] is not None)),
              "distinct_question_families": stats["families"], "top_family_share": stats["top_share"], "distinct_contexts": stats["contexts"], "near_dup_pairs": stats["near_dup_pairs"],
              "tool_use_multi_step_share": stats["tool_share"], "validation": "pass", "sha256": hashlib.sha256(raw).hexdigest(),
              "notes": "household arithmetic only; synthetic fixtures; no tax rules beyond stated assumptions"}
    with open(os.path.join(here, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps({"rows": len(out), "by_task": dict(Counter(r["task"] for r in out)), "by_split": dict(Counter(r["split"] for r in out)), "families": stats["families"], "top_share": stats["top_share"], "contexts": stats["contexts"], "tool_share": stats["tool_share"]}, indent=2))
if __name__ == "__main__":
    main()
