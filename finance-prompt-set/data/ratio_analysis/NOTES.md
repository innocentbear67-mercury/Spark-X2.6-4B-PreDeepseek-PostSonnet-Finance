# ratio_analysis - build notes

- 20 fictional issuers (sector, fiscal year end, currency USD) x 10 context shapes (core statements, market block, partial worksheet, covenant excerpt, sector norms, peer percentiles, annual-report extract, debt schedule, segment table, analyst note).
- 82 single-turn question families plus 5 tool families. Every ground-truth number is computed in code from the same dict rendered into the table; an independent re-parse of 662 contexts reproduces every answer inside its tolerance.
- Scope: liquidity (current, quick, cash), leverage (debt/EBITDA, net debt/EBITDA, interest coverage, fixed charge coverage), efficiency (asset turnover, inventory turns, DSO, DIO, DPO, CCC), DuPont 3-step and 5-step, market ratios (P/E, P/B, EV/EBITDA, payout, FCF yield), 2 partial-data families that force a derivation, 1 consistency family answered as a label.
- Sector norms for banks (P/E 11.2, P/B 1.28, ROE 11.6), utilities (15.8, 1.72, 9.8) and software (31.4, 7.80, 19.4) sit inside every sector context; each issuer carries a named benchmark group.
- Splits are assigned at fixture level, fixtures ranked by sha256(fixture key): 16 train / 2 val / 2 test, so no context or masked question straddles a split. All 20 issuers appear in train.
- Classification labels are tercile-derived from the peer table and land 7/7/6 per family; the consistency rows always have exactly one perturbed ratio.
- Known weakness: no bank-format statements. Bank norms appear only as a benchmark column, so bank-specific ratios (NIM, efficiency ratio, equity/assets) are outside this file.
- Known weakness: benchmark group is assigned by capital intensity, not by a true peer set; the peer percentiles are computed over the 20 synthetic issuers and are stable, not sampled.
- Known weakness: turnover, CCC and DuPont use average balances while the change families in question state closing balances; each question carries its own basis, but a careless reader can mix them.
- Coverage gaps: no quarterly periods, no restatement or multi-currency tables, no negative-equity or covenant-breach cases, no single-shot tool rows (100 percent multi-step).
- Report `validation: pass` was produced by the shared validate.py (profile A, 1000 rows); report.json sha256 is the hash of prompts.jsonl.
