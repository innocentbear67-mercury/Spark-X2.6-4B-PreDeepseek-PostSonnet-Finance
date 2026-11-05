# risk_sentiment (profile B)

Authored seed families (40+ question templates across six tasks):
- risk-factor sentence sentiment negative/neutral/positive, 16 each; headline sector sentiment bearish/bullish/neutral, 12 each
- guidance direction raised/lowered/reaffirmed/withdrawn, 8 each; hedging bands from a stated lexicon, 8 per band
- escalation severity under a stated impact policy, 5 per level; tone shift between periods, 6 per shift
- most-material-risk selection from five named exposures, 4 each; multi-label events over eight types
- calc: composite scores, weighted loss, hedge density, coverage ratios
- extraction: verbatim spans, table cells, footnotes; qa: 40 knowledge plus 160 grounded
- tool_use: register lookups, wrong-argument recovery, abstain and clarify paths

Weaknesses: all issuers synthetic; summarisation references are template-shaped; tool
payloads are small. Gaps: no merged cells, no non-English text.
