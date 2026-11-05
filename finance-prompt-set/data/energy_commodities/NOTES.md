# energy_commodities — build notes
89 fixtures, 24 fictional issuers: 40 upstream asset-periods, 24 refinery-periods, 25 pipeline-periods; seed 42.
111 authored templates: 37 calc, 15 extraction, 8 table QA + 24 knowledge one-offs, 10 classification, 8 summarization, 9 tool-use.
- 6 mcf = 1 boe throughout; Units line first in every context; percentages declared in the units line, never in a % column header.
- Splits are fixture-level inside each task stratum, ranked by sha256(fixture key); one row-level repair landed exactly 800/100/100.
- Breakeven solves revenue(P) = cash costs / (1 - royalty rate) with NGL priced off WTI; the definition is printed in the context.

Known weaknesses:
- All issuers report in USD, so there is no FX or local-currency price deck.
- Hedge families ignore daily fixings, margin calls and counterparty credit.
- Classification scenarios are constructed to be unambiguous, so they are easier than real disclosure judgements.
- Summarization references are short and template-shaped; the free-form family has a null target.
- Tool payloads are flat JSON with one wrong-period recovery and one missing-input case only.
