# Finance prompt set — v1

20,000 finance training prompts built by 20 isolated subagents, one domain area
each, all passing a single shared validator.

| | |
|---|---|
| rows | 20,000 (20 areas × 1,000) |
| splits | train 15,969 · val 2,029 · test 2,002 |
| tasks | calc 4,510 · extraction 4,330 · qa 4,240 · classification 2,670 · summarization 1,950 · tool_use 2,300 |
| answer types | number 9,805 · text 5,982 · label 3,750 · list 463 |
| thinking traces | on 11,050 · off 8,950 |
| rows with ground truth | 19,249 (96.2%); 751 open-ended by design |
| context length | mean 1,035 chars, median 784, max 3,557 |
| tool rows multi-step | 96.9% have 3+ messages |
| duplicate ids | 0 · duplicate (context, question) pairs 0 · documents straddling splits 0 |

## Files

```
finance-prompt-set/
├── README.md              this file
├── CONTRACT.md            the binding spec all 20 areas were built against
├── areas.json             the 20 areas, profiles, scopes, wave assignment
├── validate.py            schema + quota + diversity + hygiene gate (10 hard rules)
├── aggregate.py           re-validates every area, canonical split pass, audits
├── assemble.py            builds final prompts at load time (no template in the data)
├── data/<area>/           1,000 rows each: generate.py, prompts.jsonl, report.json, NOTES.md
└── out/
    ├── train.jsonl  val.jsonl  test.jsonl  all.jsonl
    ├── summary.json       counts, per-area validator results, problems list
    └── COVERAGE.md        per-area table + rows by task and split
```

## The 20 areas

Quant areas (profile A: 280 calc / 220 extraction / 200 qa / 100 classification /
100 summarization / 100 tool_use): `financial_statement_calc`, `ratio_analysis`,
`valuation_dcf`, `comps_precedent`, `segment_breakdown`, `credit_fixed_income`,
`macro_rates`, `m_and_a_deals`, `banking_insurance`, `reits_real_estate`,
`energy_commodities`, `private_markets_pe`, `personal_finance_calc`.

Text areas (profile B: 120 / 220 / 240 / 220 / 100 / 100): `equity_research_docs`,
`earnings_transcripts`, `accounting_policy`, `sec_filing_compliance`,
`risk_sentiment`, `fraud_forensics`.

Agentic area (profile C: 400 tool_use): `agent_tool_use`.

## Row schema

Ten keys exactly. Multi-turn rows replace `context` + `question` with `messages` + `tools`.

| field | notes |
|---|---|
| `id` | `fin_<area>_<abbr>_<6 digits>`, unique across the set, stable for joining teacher outputs |
| `task` | `calc` `extraction` `summarization` `classification` `qa` `tool_use` |
| `source` | `synthetic:<area>` or `knowledge:finance_general` (context-free rows only) |
| `context` | markdown tables / excerpts, always with a `Units:` first line when any number is involved |
| `question` | the instruction |
| `ground_truth` | number in the context's units, string, label, or array; `null` for open-ended rows |
| `answer_type` | `number` `text` `label` `list` |
| `tolerance` | `abs:x` / `rel:x` for numbers, `normalized` / `exact` for text, `exact` for labels, `set` / `ordered` for lists, `null` when gt is null |
| `split` | `train` `val` `test` |
| `thinking` | `on` for calc / qa / tool_use, `off` for extraction / classification / summarization |

**One deviation from the brief you supplied:** your JSONL template showed `"questions"`, the
field guide described `question`. The set uses `question` (singular) throughout, because the
field guide and every normal checker assume it. Rename in one pass if you meant the plural:

```bash
python3 - <<'EOF'
import json,sys
for line in open("out/all.jsonl"):
    r=json.loads(line); r["questions"]=r.pop("question"); print(json.dumps(r,ensure_ascii=False))
EOF
```

## Provenance and licensing

100% synthetic. No filing text, transcript, price series or third-party dataset was
copied — no network access was used at any point in the build. Entities are fictional
(Halcyon Grid Utilities, Meridian Bancorp, Kestrel Foods and so on), so every number is
internally consistent but must never be presented as a real company's data.

That makes the licensing position simple: nothing here carries a third-party licence.
It also sets the ceiling — these rows teach format, arithmetic and reasoning discipline,
not real-world facts. When you add real sources later, keep `source` honest
(`public:<name>`) and record the licence in the area's `NOTES.md`.

## Using it

Keep the pieces in the file and assemble the prompt at training time:

```python
from assemble import to_example
import json

row = json.loads(open("out/train.jsonl").readline())
ex = to_example(row)          # {"messages": [...], "target": "...", "tools": [...]}
```

`assemble.py` builds the system prompt from `answer_type` and `thinking`, so changing the
instruction template never requires regenerating the data. `python3 assemble.py --stats`
prints split composition; `--show` previews one assembled example.

## How this was verified

Every area was gated by `validate.py`, not by the subagent's own opinion of its work:
`python3 aggregate.py` re-runs the gate on all 20 files (result: **20/20 pass, 0 problems**).

The gate enforces: one JSON object per line, exact key set, id shape and uniqueness, task /
answer_type / split / thinking enums, tolerance vocabulary, ground-truth typing, units line
on every numeric row, no thousands separators, no mojibake, self-containment (knowledge rows
must have no context and no time-sensitive wording), no duplicate row bodies, ≥25 question
families, ≤4% on any one family, ≥120 distinct contexts, per-task quotas, split shares, and
≥40% multi-step tool rows.

Beyond the gate:

- **extraction answers** — 2,473 / 2,473 are literal substrings of their context.
- **IRR** — a private-markets XIRR row rebuilt independently: 21.31% vs 21.31% stated.
- **DCF** — one valuation row recomputed end to end (FCFF, Gordon terminal value, EV→equity
  bridge, per-share): intrinsic value 27.39, stated price for 15% upside 23.82. Exact.
- **Covenant** — net leverage headroom (4,209 − 240) / 980 = 4.05 vs a 4.5 maximum → 0.45. Exact.
- **Margin / growth** — gross margin 41.71%, two-year net income CAGR 14.12%, average net
  income 425.5. Exact.
- **Duplicate families** — 0 question families shared across areas; 17,610 distinct masked
  families across the union.
- **Split purity** — the canonical pass assigns splits per fixture group, so 0 documents
  straddle train / val / test even though the areas sit in separate files.

One defect class was found and fixed after the gates passed: 16 `banking_insurance` rows
computed embedded-value growth opening-to-closing while the question read "from FY2024 to
FY2025", which a reader would compute closing-to-closing. The questions now name the basis.
Row counts and splits are unchanged; the fix is recorded in that area's `NOTES.md`.

## Known gaps

Carry these forward rather than rediscovering them:

- **Derived numbers in summaries.** 232 summarization rows state computed values (margins,
  basis-point changes, per-share value) that do not appear verbatim in the context.
  Spot checks reproduce them, but this is the class to re-verify if you extend the set.
- **Open-ended rows.** 751 rows carry `ground_truth: null` (mostly summaries and some tool
  trajectories) — they need judge-based or consistency-based scoring, not exact match.
- **Tables are regular.** Markdown grids with blank cells and footnotes, but never merged
  cells; cell-span parsing is untested.
- **Small peer sets.** Comps tables run 4–5 names with engineered dispersion, so mean-vs-median
  questions are easier than live data.
- **Classification is rule-telegraphed.** Label sets are stated in the question and the
  wording mirrors the label semantics; these rows test rule application, not judgement.
- **Synthetic homogeneity.** Entities, periods and unit traps repeat within an area
  (transcripts hit their 1,500-char ceiling; several areas report repeated phrasing). Length
  and lexical variety are the first thing to fix if you scale this up.
- **No FX, no quarterly restatements, no real filing quirks** (10-K/A, amended exhibits,
  stale taxonomies).

## Extending

1. Add an entry to `areas.json` with a slug, profile and scope.
2. Write `data/<slug>/generate.py` against `CONTRACT.md` (fixtures in, ground truth computed
   in code, never typed).
3. Run the gate: `python3 validate.py data/<slug>/prompts.jsonl --area <slug> --profile <A|B|C>`.
4. Re-run `python3 aggregate.py` — it re-validates everything and rebuilds the splits and
   `COVERAGE.md`.

Do not hand-edit rows to make the gate pass; fix the generator and regenerate, or the file
stops being reproducible.
