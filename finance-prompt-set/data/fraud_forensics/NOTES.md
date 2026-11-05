# fraud_forensics - build notes
- 9 fixture families x 24 fictional issuers x 2 document variants = 432 contexts (362 distinct after digit masking).
- 225 question families: accrual spreads, DSO/DIO, margin-versus-OCF gap, accruals ratio, all eight Beneish
  components plus the M-score, related party relationship and concern screens, auditor opinion and
  change-of-auditor screens, restatement type and magnitude, going concern grading, Benford counts.
- Every numeric ground truth is computed in code from the same integers rendered into the table; loaded rows
  were re-parsed from the rendered markdown and re-derived independently (0 mismatches over all calc rows).
- Splits assigned per fixture by sha256 rank: 800/100/100; no masked (context, question) pair straddles splits.
- Known weakness: extraction tables have no merged or blank cells; unit traps are gross-versus-net and
  period-column only, so merged-cell parsing is untested.
- Known weakness: restatement rows on reclassification fixtures can answer 0.0 percent, and classification
  labels are balanced by construction, so the prior is uniform rather than a real-world base rate.
- No summarization reference cites a number absent from its context; 50 of 100 summarization rows are
  open-ended (null ground truth), so the reference-summary target covers only half the task.
- Tool rows: 88 percent multi-step; 10 wrong-period recovery rows and 10 insufficient-data abstention rows.
