# agent_tool_use — build notes

Seed families (79): 40 tool trajectories over get_quote / get_financials / screen_companies /
search_filings / compute_ratio / get_peer_set, plus 39 single-turn families across calc (11),
extraction (10), qa (13), classification (2) and summarization (3).

Coverage: 25 fictional issuers, six sector buckets, two fiscal years; income, balance sheet,
cash flow, segment, quarterly, filing excerpt, consensus memo, peer, debt and return contexts
(217 distinct masked contexts). Every table carries an explicit period and a units line.

Tool flows exercised: single call, two-call chain, screen-then-drill, argument repair after a
tool error, ambiguous short names, conflicting vendor vs filed revenue, and abstention when a
metric is not carried or a screen returns nothing. All 400 rows carry tool-role JSON and end
on a user question; 100% contain an assistant call.

Known gaps: single-turn calc is formulaic (margin, growth, ratio families); payloads are small
(three filings, four peers); extraction answers are verbatim lookups. There are no context-free
knowledge rows, so `knowledge:finance_general` is unused. generate.py is template-heavy at
1068 lines (40 bespoke flows with full JSON payloads) — above the 800-line guideline, but every
row is produced by loops over 25 fixtures x family tables, never written inline.
