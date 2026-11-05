# financial_statement_calc — build notes

- 24 fictional issuers (mixed sectors, fiscal year ends, segment pairs); all amounts USD, millions unless a table says thousands.
- calc (280): 40 fixtures x 7 rows across six table shapes — income statement, cash flow, working capital, EBITDA/restructuring, share data, return on capital.
- calc families: gross/operating/net/EBITDA/pretax margins, margin change in points and basis points, revenue/gross-profit/EBIT/net-income/EPS growth, two-year CAGR, FCF and FCF conversion, capex intensity, working-capital delta, DSO/DIO/DPO/CCC, ROE, ROIC, NOPAT, invested capital, P/E, payout, effective tax rate.
- extraction (220): 20 fixtures x 11 cells; blank cells, footnote markers and a thousands-versus-millions unit trap.
- qa (200): 160 multi-hop table rows plus 40 context-free formula and definition rows.
- classification (100): five label sets; labels are constructed to be balanced (7/6/7 or 10/10 per set) and derivable from the table.
- summarization (100): 10 fixtures x 10 prompts; each reference summary cites only numbers printed in the table.
- tool_use (100): 10 fixtures x 10 scripts — 7 single-call, 1 wrong-period retry, 1 insufficient-data abstain, 1 segment call.
- Splits: fixtures ranked by sha256 of the fixture key inside each task stratum, then filled 80/10/10; no fixture straddles splits.
- Traps: restructuring charge in one period only, tax-rate spike, share-count creep, negative free cash flow, working-capital source/use swings.
- Weakness: summarization references are templated and repeat across the ten prompts attached to one fixture.
- Weakness: segment questions appear only in the tool-use task; no segment table is used in calc.
- Gap: fiscal years only — no quarterly or LTM bridging; no multi-currency statements; no discontinued operations.
