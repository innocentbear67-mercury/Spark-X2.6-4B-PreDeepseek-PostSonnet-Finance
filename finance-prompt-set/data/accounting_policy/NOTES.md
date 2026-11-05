# accounting_policy — build notes

- 25 fictional issuers x 8 note types = 200 fixtures; each fixture serves exactly one task and emits exactly 5 rows (200 x 5 = 1000), which keeps task quotas exact.
- Authored note types: GAAP/non-GAAP bridge (add-backs plus tax effect), five-step revenue model (variable consideration, constraint, allocation, principal vs agent), leases (liability, ROU asset, current/non-current split, short-term exemption), share-based compensation (treasury-stock dilution), impairment (trigger, measurement, goodwill-first allocation), deferred tax with valuation allowance, change in estimated useful life, and restatement/policy/estimate language.
- 224 distinct digits-masked question families; largest family is 1.0% of the file. Extraction rows ask for a table line by label and column, so answers are verbatim spans.
- Splits are assigned per fixture by sha256 of the fixture key inside each task stratum (160/20/20 fixtures), so no context appears in two splits and no near-duplicate straddles one.
- Every number is computed in generate.py from the values written into the table; an independent re-parse of all 360 numeric answers from the emitted contexts reproduces each one.
- Tool rows (100): non-GAAP and share-based-comp tools, all plan -> call -> result -> answer, including two deliberate "detail_not_available" abstention cases.
- Known weakness: 4 classification dimensions are single-label by construction (prospective application, non-current deferred tax, estimate-not-policy, over-time installation revenue) because the guidance prescribes one treatment; the other 26 dimensions vary across labels.
- Known weakness: classification labels are policy conclusions rather than genuinely contested judgements; no grey-area fixtures where two treatments are defensible.
- Coverage gap: no context-free knowledge rows — all 1000 rows are grounded in a note, so definition recall is not represented.
- Coverage gap: no pensions, foreign-currency remeasurement, EPS anti-dilution sequencing, business combinations or segment reporting.
- All issuers, amounts and notes are synthetic; the generator has no network access and no dependencies outside the standard library. Python 3.9 compatible.
