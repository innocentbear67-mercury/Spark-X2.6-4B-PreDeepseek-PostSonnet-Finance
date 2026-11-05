# macro_rates — build notes

Authored: 123 templates — 36 calc, 10 extraction, 23 table qa, 20 knowledge items x3 paraphrases, 10
classification rules, 14 summaries, 10 tool flows; 290 masked families after date-style variants.

Scope: CPI headline/core yoy, MoM simple and compounded annualisation, weighted contributions, Fisher
real rates, 2s10s/3m10y/5s30s and their changes, 5y5y and 1y1y forwards, futures-implied policy paths,
GDP contributions and deflators, payrolls/unemployment/participation, FX translation, forward outright,
carry, breakevens and forward breakevens.

Splits: fixture-level, sha256 ordering per task stratum, 80/10/10; rows never straddle splits.

Weaknesses: forwards and breakevens use annual compounding on par yields, not a bootstrapped zero curve;
extraction answers are literal cell quotes; classification rules are stated in-question; tool rows carry
null ground_truth so they train the trajectory only. Gaps: no credit, vol, cross-currency basis, revisions.
