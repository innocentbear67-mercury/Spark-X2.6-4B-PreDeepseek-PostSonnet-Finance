# earnings_transcripts
- 24 fictional issuers x 8 fiscal quarters = 192 fixtures, each rendering its own SPEAKER COLON
  excerpt (1355-1500 chars) with a units line, a segment table and a CFO outlook sentence.
- 66 authored question families: 14 calc, 15 extraction, 15 qa, 6 summarization, 6 classification,
  10 tool-use. Splits are assigned per (task, fixture) by sha256, then rebalanced to 800/100/100.
- Guidance direction is numeric by construction ({raise, cut, withdraw, reiterate}); the hedge family
  states its counting rule (term list and thresholds), so that label is reproducible, not a mood call.
- Certainty, response type, intent and commitment-strength labels are written into the transcript by
  construction and are recoverable, but they stay judgement labels rather than arithmetic.
- Weakness: summarization bullets are template-composed and share phrasing across fixtures; every
  number in them appears verbatim in the context.
- Weakness: no merged or blank table cells, and the $000 unit-trap note fits only 12 fixtures.
- Weakness: transcripts sit near the 1500-character ceiling, so optional notes (FX, facility, export)
  are dropped on most fixtures and those extraction families run at 12-26 rows.
- All figures are rounded once in build_fixture; ground_truth reuses those same rounded values.
