# equity_research_docs - build notes

- 24 fictional issuers x 14 document fixtures (168 contexts): MD&A revenue-driver, margin-bridge and
  liquidity excerpts; revenue, lease, debt, segment, restatement, tax and goodwill notes; risk
  factors, contingencies, subsequent events and going-concern language.
- Profile B: calc 120, extraction 220, qa 240, classification 220, summarization 100, tool 100.
- Splits assigned per fixture (one split per document) by sha256 rank plus a deterministic hill-climb
  holding per-task shares near 80/10/10: 800 train, 102 val, 98 test.
- Numbers are drawn once, rendered into the excerpt and fed to the same expression as ground_truth;
  23 calc answers were re-derived from the rendered tables (max delta 0.4 bps, inside tolerance).
- 357 question families, top family 2.0%, 167 contexts, 0 duplicate bodies, 0 contexts across splits.
- Weaknesses: 100 summarization rows have null ground_truth; tool_use grades only the final answer;
  the tax and impairment classification pools are thinnest (12 fixtures each, 6 per label).
- Gaps: no bank or insurer formats, no FX translation or constant-currency walk, no proxy or guidance.
