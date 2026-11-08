# Training types without reasoning traces: exact formats

Builder: `build_training_sets.py` (this folder).
Nothing here edits your existing files. Every command writes only into `--out`.
To see a few rows of any type, add `--limit 3` to its build command.

Counts below are from a build on 2026-11-08 against this repo's `out/` and `sft/` files.

| # | Type | Needs | Trains with | Rows built |
|---|------|-------|-------------|-----------|
| 1 | Domain continued pretraining (CPT) | real text files you add | `mlx_lm.lora` | depends on your text |
| 2 | Answer-only SFT | `out/` | `mlx_lm.lora` | 6,834 train / 854 valid / 863 test |
| 3 | Preference tuning (DPO / KTO) | `out/` + `sft/answers_raw.jsonl` | `mlx-lm-lora` or a cloud GPU (TRL) | 554 train / 67 valid pairs |
| 4 | RL with verifiable rewards (RLVR) | `out/` | `mlx-lm-lora` GRPO or a cloud GPU | 6,115 train / 759 valid |
| 5 | Tool-format SFT without reasoning | `sft_v3/` (from `build_sft_v3.py`) | `mlx_lm.lora` | 824 train / 124 valid / 85 test |
| 6 | Distillation on labels | `out/` + `sft/answers_raw.jsonl` | `mlx_lm.lora` | 5,264 train / 666 valid / 683 test |

Every `valid.jsonl` is named that way on purpose. `mlx_lm.lora` only reads `valid.jsonl`, not `val.jsonl`.

---

## 1. Domain continued pretraining (CPT)

**What it is:** raw text, no questions. Teaches vocabulary and layout of filings and manuals.

**Important:** your prompt set is synthetic (made-up companies and numbers). CPT on it would teach fake facts.
Use REAL text: 10-K / 20-F sections, accounting manuals, central-bank reports, saved as `.txt` or `.md`.
Check the licence of anything you add.

**Format** (`train.jsonl`, `valid.jsonl`): one JSON object per line, one key.

```json
{"text": "Item 7. Liquidity and capital resources.\n\nCash from operations rose 12% to 931 million.\n\nCapital expenditures were 210 million."}
```

- No chat template. No `messages`. No system prompt.
- Chunks are about 2,000 characters, cut on blank lines. Spark text runs near 2.6 characters per token, so that is about 770 tokens. That fits `--max-seq-length 1024`.

**Build:**
```
python3 build_training_sets.py cpt --text-dir my_filings --out data_cpt
```

**Train** (no `--mask-prompt`, there is no prompt):
```
mlx_lm.lora --model xunlinkx/Spark-X2.6-4B-Abliterated-Uncensored-MLX-oQ8e-fp16 --train --data data_cpt --iters 500 --batch-size 1 --num-layers 8 --grad-checkpoint --max-seq-length 1024 --steps-per-eval 100 --save-every 25 --val-batches 10 --adapter-path adapters_cpt
```

**Cautions:**
- LoRA is a weak way to add facts. It nudges style and vocabulary more than it stores knowledge. For facts, use retrieval (RAG).
- Do CPT first, then SFT. SFT after CPT restores the answer format.

---

## 2. Answer-only SFT

**What it is:** question in, final answer out. No reasoning field.
Covers extraction, classification, summarization (the rows where `thinking` is `off`).

**Format** (`train.jsonl`, `valid.jsonl`, `test.jsonl`):

```json
{"messages": [
  {"role": "system", "content": "You are a financial analyst. Answer directly and briefly. Give the value, label or span requested, in the units stated in the source. Reply with one label from the set given in the question."},
  {"role": "user", "content": "<source text>\n\n<question>"},
  {"role": "assistant", "content": "Positive"}
]}
```

- No `reasoning_content`. Spark's chat template then writes an empty think block, so the model learns to close its thinking at once.
- The target is the repo's ground truth, so the answer is already checked.
- Rows with an unknown ground truth are skipped.

**JSON-output rows:** there are none in this data. Answer types here are only number, text, label and list. For JSON formatting you need new rows. Put a `{"messages": [...]}` row with the JSON string as the assistant content and the schema in the system message.

**Build:**
```
python3 build_training_sets.py answer_sft --data finance-prompt-set/out --out data_answer
```
Add `--include-on` to also use calc and QA rows with the working left out. Do this only if you want that. Number answers with no working teach the model to guess a number.

**Train:**
```
mlx_lm.lora --model xunlinkx/Spark-X2.6-4B-Abliterated-Uncensored-MLX-oQ8e-fp16 --train --data data_answer --iters 500 --batch-size 1 --num-layers 8 --grad-checkpoint --mask-prompt --max-seq-length 1024 --steps-per-eval 100 --save-every 25 --val-batches 10 --adapter-path adapters_answer
```
Rows longer than `--max-seq-length` give `nan` loss under `--mask-prompt`. Filter by token count first, as `convert_sft_v2.py` does.

---

## 3. Preference tuning (DPO / KTO)

**What it is:** for the same question, a good answer and a bad answer.

**Source of pairs:**
- chosen = the repo's ground truth
- rejected = DeepSeek's own final answer, where it did not match the ground truth
- Only the train and val splits are used. The test split is never touched.
- Only number, label and list answers are used. Text answers are judged by exact match, so a "wrong" one is often a fair paraphrase. Add `--include-text` to bring them in, at your own risk.
- Truncated teacher answers are skipped.

**Default format (`--format mlxlora`, for `mlx-lm-lora`):** `prompt`, `chosen`, `rejected`, optional `system`.

```json
{"system": "You are a financial analyst. ...", "prompt": "<source text>\n\n<question>", "chosen": "350", "rejected": "340"}
```

**`--format trl` (cloud GPU, TRL DPOTrainer, conversational):**

```json
{"prompt": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
 "chosen": [{"role": "assistant", "content": "350"}],
 "rejected": [{"role": "assistant", "content": "340"}]}
```

**`--format kto` (TRL KTOTrainer):** one line per answer, with a `label`.

```json
{"prompt": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}], "completion": [{"role": "assistant", "content": "350"}], "label": true}
{"prompt": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}], "completion": [{"role": "assistant", "content": "340"}], "label": false}
```

**Build:**
```
python3 build_training_sets.py dpo --data finance-prompt-set/out --sft finance-prompt-set/sft --out data_dpo
```

**Train:** `mlx_lm.lora` cannot do DPO. The separate package `mlx-lm-lora` can (field names above match its README). I have not run it with Spark's chat template. Its README does not mention reasoning or tool fields. Check its README for the exact command flags before you run it.

**Cautions:**
- Chosen answers here have no reasoning, but a thinking-mode model writes reasoning first. The pair then compares a bare answer to a full response. Run DPO after SFT, with a low learning rate, and watch whether the model stops reasoning.
- 554 pairs is small.

---

## 4. RL with verifiable rewards (RLVR)

**What it is:** the model writes its own answer. A checker gives reward 1 if the number is right, else 0. No traces from a teacher.

**Format** (`train.jsonl`, `valid.jsonl`, for GRPO in `mlx-lm-lora`): `prompt` and `answer` required.

```json
{"system": "You are a financial analyst. ...", "prompt": "<source text>\n\n<question>", "answer": "350", "type": "math"}
```

**Checker data** (`train_meta.jsonl`, same line order as `train.jsonl`):

```json
{"id": "fin_risk_sentiment_calc_000022", "ground_truth": 350, "answer_type": "number", "tolerance": "abs:1"}
```

**Reward function:** `reward(completion, meta)` in `build_training_sets.py`.
- Returns 1.0 for a right final answer within the row's tolerance, 0.0 otherwise.
- Text before the last `</think>` is ignored.
- If the model never closes its thinking, the reward is 0.0. This pushes it to finish.
- Tested on the repo's own examples: right answer 1.0, wrong answer 0.0, unclosed thinking 0.0.

**Rows:** thinking-on rows with number or label answers (calc, QA).

**Build:**
```
python3 build_training_sets.py rlvr --data finance-prompt-set/out --out data_rlvr
```

**Train:** not on your Mac for a real run. GRPO samples many answers per question, so it is slow. At about 20 tokens per second on your Air, use a cloud GPU. Unverified: whether `mlx-lm-lora` GRPO accepts this `reward()`. Its built-in rewards may differ.

---

## 5. Tool-format SFT without reasoning

**What it is:** user message, then the tool call, then (in the next example) the tool result and final answer. It teaches valid calls as a pattern.

**Source:** the output of `build_sft_v3.py` (only rows with a real JSON call and its arguments).

**Format:** two example shapes in one file.

Call target (the assistant message is the call):
```json
{"messages": [
  {"role": "system", "content": "..."},
  {"role": "user", "content": "Check Pelican Health Systems against its leverage covenant."},
  {"role": "assistant", "content": "", "reasoning_content": "",
   "tool_calls": [{"type": "function", "function": {"name": "get_financial_metric",
     "arguments": {"company": "Pelican Health Systems", "metric": "net_leverage", "period": "FY2025"}}}]}
 ],
 "tools": [{"type": "function", "function": {"name": "get_financial_metric", "description": "...", "parameters": {"type": "object", "properties": {"company": {"type": "string"}}, "required": ["company"]}}}]}
```

Final answer after the result (reasoning removed):
```json
{"messages": [ ..., {"role": "assistant", "tool_calls": [...]}, {"role": "tool", "content": "{...}"}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "3.2"}], "tools": [...]}
```

Rules (checked against Spark's chat template):
- `tools` entries are wrapped as `{"type":"function","function":{...}}`.
- `arguments` is a JSON object, not a string.
- Tool results use the `tool` role. The template writes them as `<|Tool|><tool_response>...`.
- The template writes calls as `<tool_call>`, `<arg_key>`, `<arg_value>`.

**Build:**
```
python3 build_training_sets.py tool_sft --sft3 sft_v3 --out data_tool
```
Add `--calls-only` for just the call targets (526 train rows now).

**Train:** same command as type 2 with `--data data_tool --adapter-path adapters_tool`. `mlx-lm` 0.32.2 passes `tools`, `tool_calls` and `reasoning_content` to the template (checked by reading its source). A real training run on this data is unverified.

**Cautions:** 824 train rows is small. Prose-only tool rows (no arguments in the source) are left out on purpose, so the model never learns made-up arguments.

---

## 6. Distillation on labels

**What it is:** train on the teacher's final answer. Its reasoning is thrown away.

**Format:** same as type 2.

```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "350"}]}
```

**Rows:** thinking-on rows where DeepSeek's answer matched the ground truth. The target is DeepSeek's own wording, not the stored ground truth.

**Honest note:** here this is close to type 2 with `--include-on`. The teacher answers were only kept when they matched the ground truth, so the text is nearly the same. The only difference is small ones (for example `350.0` against `350`, or a number inside tolerance). It would matter if you had teacher answers for rows with no ground truth. Those rows were never sent to the teacher (751 rows). Pick type 2 or type 6, not both.

**Build:**
```
python3 build_training_sets.py distill --data finance-prompt-set/out --sft finance-prompt-set/sft --out data_distill
```

**Train:** same command as type 2 with `--data data_distill --adapter-path adapters_distill`.

---

## Which to run first

1. Type 5 smoke test (format check, 20 steps).
2. Type 2 (cheap, format and style).
3. Types 1 and 3 and 4 only after you have real text (1), a working SFT (3), and a cloud GPU (4).

Mixing: you can concatenate type 2 and type 5 and your earlier reasoning SFT files into one `train.jsonl`. Shuffle first. Keep `valid.jsonl` from the same mix.
