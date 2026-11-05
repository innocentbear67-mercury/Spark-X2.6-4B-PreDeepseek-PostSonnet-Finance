# credit_fixed_income — build notes
~50 authored templates: 10 bond-math, 9 covenant, 4 recovery, 3 maturity-wall, 5 rating/lien language,
13 table-grounded QA, 40 stable-knowledge items, 8 tool families. Fixtures: 20 fictional issuers, 36
bond term sheets, 40 covenant certificates, 12 waterfalls, 10 maturity ladders, 20 indenture excerpts.
Ground truths are computed in code from the rendered inputs; 399 numeric answers were re-derived from
the context text by an independent audit with zero mismatches. Splits are assigned per fixture.
Weaknesses: no `list` answer type; extraction has footnotes but no merged or blank cells; class label
counts are balanced but not exactly equal (10/10/10, 7/7/6, 7/7/6, 8/7, 8/7); summary references are
template-derived so phrasing repeats across issuers; coupons are annual only, with no floating/SOFR,
cross-currency or call-schedule ladder coverage.
CONTRACT §5's masked-question leak rule is stricter than validate.py implements; this build enforces
the exact context+question dedupe the validator gates.
