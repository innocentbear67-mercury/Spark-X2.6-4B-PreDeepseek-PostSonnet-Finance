# m_and_a_deals — build notes

- 160 synthetic deal fixtures (24 fictional issuers, sector-matched pairings), each rendered as a merger term
  sheet: consideration, LTM financials, segments, sources and uses, synergies/financing, PPA, termination terms.
- 113 question families: 35 calc, 22 extraction, 20 qa, 5 classification, 10 summarization, 10 tool_use.
- All ground truths are computed in derive() from the rounded values render() writes; an independent re-parse of
  the context reproduces every calc and numeric qa answer.
- Splits are fixture-level by sha256 of the deal key (128/16/16); all tasks reuse that split, so no context straddles.
- Weakness: split is 801/103/96 rather than exactly 800/100/100, because classification rows are picked for label
  balance rather than quota.
- Weakness: pro forma EPS is a cash-EPS convention excluding intangible amortization (stated in context).
- Weakness: CVR milestone extraction answers "not applicable" on the 75 percent of deals without a CVR.
- Gaps: no tax structuring, cross-border inversion mechanics, REIT/PE fund deals, fairness opinions or tender offers.
