---
language:
- en
license: mit
task_categories:
- question-answering
- text-classification
- summarization
tags:
- finance
- synthetic
- financial-reasoning
- tool-use
pretty_name: Finance Prompt Set v1
size_categories:
- 10K<n<100K
---

# Finance Prompt Set v1

20,000 synthetic finance training prompts across 20 domain areas:
statement analysis, ratios, DCF valuation, comps, segment reporting, credit,
macro/rates, M&A, banking/insurance, REITs, energy, private markets, personal
finance, accounting policy, SEC compliance, sentiment, fraud forensics, and
agentic tool use.

All rows passed a single machine gate (`validate.py`: schema, task quotas, number
format, units lines, diversity floors, split shares). Document-level train/val/test
splits: no fixture straddles splits. See `../README.md` for the full verification
log and known gaps. 100% synthetic — no real filing, transcript, or price data.

## Files

| file | rows | notes |
|---|---|---|
| `raw/validation_passed_prompts.jsonl` | 20,000 | original checked rows, exactly what the per-split files contain |
| `hf/unified_prompts.jsonl` | 20,000 | chat-native conversion (this card's schema) |
| `hf/generate_hf.py` | — | converter; re-runnable from `raw/` or from the `out/` splits |
| `hf/stats.json` | — | row count, text-length percentiles, tools/ground-truth coverage |
| `hf/dataset_card.md` | — | this file |

## Schema (`unified_prompts.jsonl`)

Twelve string columns — no mixed types, no nulls in struct fields.

| column | content |
|---|---|
| `id` | `fin_<area>_<abbr>_<6 digits>`, unique, join key back to `raw/` rows |
| `task` | `calc` `extraction` `summarization` `classification` `qa` `tool_use` |
| `source` | `synthetic:<area>` or `knowledge:finance_general` (context-free, stable facts only) |
| `answer_type` | `number` `text` `label` `list` |
| `tolerance` | checker rule: `abs:x` / `rel:x` for numbers, `normalized` / `exact` for text, `exact` for labels, `set` / `ordered` for lists, `""` when no ground truth |
| `split` | `train` 15,969 · `val` 2,029 · `test` 2,002 |
| `thinking` | `on` (calc/qa/tool_use) / `off` (extraction/classification/summarization) |
| `text` | one chatml transcript: system + user (context + question) + assistant with the reference answer, or an open assistant turn when there is none |
| `tools` | compact JSON string of the OpenAI-style tool list for tool_use rows, `""` otherwise |
| `ground_truth` | plain string: numbers render canonically (no thousands separators, integers without decimals), lists one-per-line, `""` when open-ended |
| `ground_truth_normalized` | check-side form: lowercased, whitespace collapsed, quotes stripped |
| `target_hint` | output-format instruction matching `answer_type` |

## Load it

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="hf/unified_prompts.jsonl", split="train")
train = ds.filter(lambda r: r["split"] == "train")
val   = ds.filter(lambda r: r["split"] == "val")
test  = ds.filter(lambda r: r["split"] == "test")
```

Tool trajectories decode from the `tools` string:

```python
import json
row = ds.filter(lambda r: r["task"] == "tool_use")[0]
tool_schemas = json.loads(row["tools"])   # list of {name, description, parameters}
```

The 751 rows with empty `ground_truth` are open-ended by design (summaries, some
trajectories) — score them with a judge or consistency check, not exact match.

## Provenance

Deterministic build: `python3 hf/generate_hf.py --root .` regenerates
`hf/unified_prompts.jsonl` from `raw/validation_passed_prompts.jsonl`
(or from the `out/` splits if `raw/` is absent — same bytes). The chatml assembly
is defined once in `assemble.py` (`build_hf_text` / `to_hf_record`), imported by
both the converter and any inference script, so training and eval prompts are
identical. If you fork the system prompt or format hints, change them in
`assemble.py` and regenerate — never hand-edit the data files.

## Limitations

Same as the base set: synthetic homogeneity of phrasing, regular markdown tables
only, small comps peer sets, classification labels that test rule application rather
than judgement, 3.8% open-ended rows. Details in `../README.md` under "Known gaps".
