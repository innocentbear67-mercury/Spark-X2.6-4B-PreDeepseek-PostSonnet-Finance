# sec_filing_compliance - build notes

- 161 synthetic fixtures in 7 pools: 8-K event briefs (22), other-form events (20), EDGAR headers (30), ownership snapshots (26), proxy proposals (24), 10-K excerpts (20), filing calendars (19). Each fixture emits 2 rows per task it serves, so every (task, fixture) group is size 2 and quotas land exactly.
- 92 authored question families: 16 calc, 26 extraction, 19 qa, 13 classification, 4 summarization, 14 tool-use; 175 distinct digits-masked families survive masking, top family 2.6%.
- Scope: form-type ID over 15 labels, 8-K item mapping over 20 items, deadline and period logic (10-K 60/75/90, 10-Q 40/45, 8-K 4 business days, Form 4 2 business days), 13D/13G selection, Form 4 codes P S A M F G, ownership-percentage arithmetic, proxy proposal labels, Form 10-K section labels.
- Every rule needed to answer is printed in the context (filing window, furnished-vs-filed, 13D/13G, ordinary-vs-extraordinary, vote standard), so only the 12 stable-knowledge QA rows rely on outside knowledge.
- Splits are assigned per fixture by sha256("<task>|<fixture key>") inside each task stratum (train 80 / val 10 / test 10); no fixture straddles a split and no near-duplicate escapes (near_dup_pairs 0).
- Verified independently: all 120 calc answers recomputed from a regex re-parse of the emitted context (0 mismatches), every extraction answer is a literal substring of its context, and no reference summary carries a number absent from its context.
- Known weakness: section classification is keyword-driven - the excerpt vocabulary telegraphs the item, so it is easier than reading a real filing.
- Known weakness: 13D/13G is a binary forced by stated intent, and QII status is set equal to passive intent, so the "passive but not qualified institutional investor" branch never appears (18:17 split).
- Known weakness: labels cannot be exactly balanced at this row count - form types run 2-4 rows each over 14 labels, Form 4 codes 4-5 each over 6.
- Coverage gap: no 10-K/10-Q statement arithmetic, Form 144, Section 16(b) short-swing math, 13D amendment deadlines, or tender-offer schedules.
- Coverage gap: no real filings, tickers, CIKs or accession numbers - every identifier is synthetic, and no text is quoted from a real document.
- Python 3.9, standard library only, no network; `python3 generate.py` rewrites prompts.jsonl and report.json deterministically.
