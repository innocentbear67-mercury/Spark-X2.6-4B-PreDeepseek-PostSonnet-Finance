# reits_real_estate — author notes

Seed families (40+ templates over 24 fictional REITs and 11 context views): NOI build-up from a
rent roll, NOI margin, same-store NOI and growth, cap rate / implied value / cap sensitivity,
FFO and AFFO bridges with per-share and payout maths, GLA-weighted occupancy, cash leasing
spreads, rent-weighted WALT and expiry shares, development yield on cost, stabilised value, NAV
sum-of-parts and NAV per share, DSCR / debt yield / net debt to EBITDA, lease escalation,
straight-line rent, mark-to-market; plus extraction (footnotes, blank FY2024 cell), rule-based
classification, summarisation and 9 tool flows (wrong argument, wrong period, insufficient data).
Splits: per fixture by sha256 of the fixture key inside each task stratum; no (context, question
family) pair straddles splits (verified 0). Weakness: 798/96/106 rather than 800/100/100 because
whole fixtures move as ~12-row blocks; figures are synthetic, not market-calibrated. Gaps: no
ground-lease/UPREIT structuring, no FX, no promote waterfalls; the abstain tool family has a null
ground_truth by design.
