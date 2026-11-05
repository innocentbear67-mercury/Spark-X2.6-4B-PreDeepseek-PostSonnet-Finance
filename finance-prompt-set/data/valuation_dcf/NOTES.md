# valuation_dcf — build notes

- 200 fixtures = 20 fictional issuers x 10 scenarios, rendered through five context variants: full DCF
  pack, cost-of-capital inputs, sensitivity grid, stub period and single-stage perpetuity.
- 143 distinct masked question families; the largest holds 2.5% and no (context, family) pair repeats.
- Reproducibility checked outside the generator: 411 calc/qa rows re-derived from the markdown tables
  alone and all 100 tool rows from their JSON payloads.
- Scope: FCFF from EBIT with tax shield, D&A, capex and working capital; FCFE valued directly at the
  cost of equity; WACC via CAPM with after-tax debt, target weights and beta relevering; Gordon and
  exit-multiple terminal values with the implied-multiple and implied-growth cross-check; mid-year and
  stub discounting; EV-to-equity bridge (debt, cash, minorities, preferred, pension); per-share value;
  a 5x5 sensitivity grid; implied upside; reverse DCF for implied growth and implied WACC.
- Known weakness: the full context states the WACC, so the cost-of-capital build is asked from a
  variant that omits it; both agree to rounding. Classification labels are balanced by construction,
  so class priors are uniform. Gap: no peer-multiple table and no LBO/returns analysis here.
