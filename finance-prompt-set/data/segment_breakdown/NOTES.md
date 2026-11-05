# segment_breakdown - build notes

- 20 fictional issuers, 3-5 reportable segments each, 9 context variants per issuer: segment
  P&L, reconciliation with eliminations, capital employed, geographic revenue with FX,
  restated definitions, margin walk, descriptions with footnotes, blank-cell unit trap, capex.
- 181 distinct question families (largest 20 rows, 2.0%), 292 distinct contexts, no
  (context, family) pair repeated; splits 16/2/2 fixtures by sha256 of the fixture key.
- Every ground_truth is computed from the integers rendered into the tables; 360 numeric
  answers and 620 table totals re-derived independently from the JSONL: 0 mismatches.
- Weakness: the 100 summarization rows carry no reference answer (null ground truth).
- Weakness: classification labels come from constructed tables whose label is fixed by design,
  balanced within each family (7/7/6 or 10/10) but not drawn from the fixture population.
- Gap: no quarterly segments, no segment balance sheet beyond capital employed, and FX is a
  disclosed translation effect rather than a rate table the model must apply.
