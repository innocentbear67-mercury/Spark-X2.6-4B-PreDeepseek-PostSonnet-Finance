#!/usr/bin/env python3
"""Build mlx_lm.lora training files (sft_v3) with REAL tool calls in Spark's chat-template format.

What is new versus convert_sft_v2.py
- tool_use rows whose assistant turns hold a JSON call ({"name"|"tool": ..., "arguments": {...}})
  are rebuilt from the prompt set (out/*.jsonl) with:
    * a `tools` list on the row, wrapped as {"type": "function", "function": {...}}
      (Spark's template prints `tool.function`, so the bare schema would render as nothing);
    * structured `tool_calls` on the assistant message, arguments as a JSON object (the template
      raises an error if arguments is a string);
    * tool results kept as role "tool" (template renders <|Tool|><tool_response>...</tool_response>).
- For each such row we write:
    (a) one CALL example per assistant turn that holds a parseable JSON call: the prompt ends just
        before that turn, the target is the tool-call message. No ground truth is used. Reasoning is
        empty (the data has none for these turns), so the template renders "</think>" then the call.
        Any prose before the JSON on the same turn (e.g. "Fetching the balance sheet.") stays as content.
        Prose-only assistant turns are never turned into calls (Option 1: no guessed arguments).
        Call examples whose company / issuer / bond id is not written anywhere in the prompt are
        dropped by default (the source data has prompts like "for the issuer" with ~20 different
        companies as targets). Use --keep-ungrounded-calls to keep them.
    (b) the FINAL-ANSWER example from sft/ (teacher reasoning in reasoning_content, ground-truth
        answer, same numeric fix as convert_sft_v2.py), with its history in structured form.
- Every other row (non-tool rows, prose-only tool rows, tool rows with no assistant call) is passed
  through with exactly the convert_sft_v2.py rules: reasoning -> reasoning_content, val -> valid,
  id removed, numeric answer fix, rows over --max-tokens Spark tokens dropped.

    python3 build_sft_v3.py --sft finance-prompt-set/sft --out data_small_v3 --small 500
    python3 build_sft_v3.py --sft finance-prompt-set/sft --out data_full_v3

--prompts defaults to <sft>/../out (the prompt set with tools and the original JSON calls).
"""
import argparse
import json
import os
import random
import re
from collections import Counter

NUM = re.compile(r"^-?[\d,]*\.?\d+$")
SPLITS = {"train": "train", "val": "valid", "test": "test"}


def to_float(s):
    return float(s.replace(",", "").replace(" ", ""))


def parse_call(text):
    """Return (prose_before, name, arguments_dict) if the turn holds a JSON tool call, else None.
    Accepts the whole text as JSON, or prose then JSON starting on a later line / later brace."""
    t = (text or "").strip()
    starts = [0] + [m.start() for m in re.finditer(r"\{", t)]
    for i in starts:
        try:
            obj = json.loads(t[i:])
        except ValueError:
            continue
        if not isinstance(obj, dict):
            return None
        name = obj.get("name", obj.get("tool"))
        args = obj.get("arguments")
        if isinstance(name, str) and name and isinstance(args, dict) and set(obj) <= {"name", "tool", "arguments"}:
            return t[:i].strip(), name, args
        return None
    return None


ENTITY_ARGS = {"company", "issuer", "issuer_id", "benchmark_company", "bond_id", "ticker", "symbol"}


def _norm(x):
    return re.sub(r"[\s_\-]+", " ", str(x).lower()).strip()


def ungrounded_entities(history, args):
    """Entity arguments (company, issuer, bond id...) whose value is not written anywhere in the prompt.
    Prior call arguments do not count as evidence. Returns a list of arg names."""
    ctx = _norm(" ".join(m.get("content") or "" for m in history))
    bad = []
    for k, v in args.items():
        vals = v if isinstance(v, list) else [v]
        if k in ENTITY_ARGS and any(isinstance(x, str) and _norm(x) not in ctx for x in vals):
            bad.append(k)
    return bad


def wrap_tools(tools):
    out = []
    for t in tools or []:
        if isinstance(t, dict) and t.get("type") == "function" and "function" in t:
            out.append(t)
        else:
            out.append({"type": "function", "function": t})
    return out


def structured(messages):
    """Out-row messages -> template messages. JSON-call assistant turns become tool_calls.
    Returns (msgs, call_positions)."""
    msgs, calls = [], []
    for m in messages:
        if m["role"] == "assistant":
            p = parse_call(m["content"])
            if p:
                prose, name, args = p
                calls.append(len(msgs))
                msgs.append({"role": "assistant", "content": prose, "reasoning_content": "",
                             "tool_calls": [{"type": "function", "function": {"name": name, "arguments": args}}]})
                continue
        msgs.append({"role": m["role"], "content": m["content"]})
    return msgs, calls


def flattened(messages):
    """The way build_sft.py wrote history (used only to check our join is right)."""
    return [{"role": "user", "content": "Tool result:\n" + m["content"]} if m["role"] == "tool"
            else {"role": m["role"], "content": m["content"]} for m in messages]


def final_target(r, teacher, keep_gt, s):
    """convert_sft_v2.py rules for the last message. Returns (message, is_think)."""
    text = r["messages"][-1]["content"]
    if text.startswith("<think>"):
        head, _, target = text.partition("</think>")
        reasoning = head[len("<think>"):].strip()
        target = target.strip()
        t = teacher.get(r["id"], "")
        if (not keep_gt and NUM.match(target) and NUM.match(t.replace(" ", ""))
                and to_float(target) != to_float(t)):
            target = t.replace(" ", "")
            s["answer_fixed"] += 1
        return {"role": "assistant", "content": target, "reasoning_content": reasoning}, True
    return r["messages"][-1], False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sft", required=True, help="repo folder finance-prompt-set/sft")
    ap.add_argument("--prompts", default=None, help="repo folder finance-prompt-set/out (default: <sft>/../out)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-tokens", type=int, default=1000, help="drop examples longer than this many tokens")
    ap.add_argument("--tokenizer", default="XHToken/Spark-X2.6-4B")
    ap.add_argument("--keep-ground-truth", action="store_true", help="skip the numeric answer fix")
    ap.add_argument("--small", type=int, default=0, help="random sample of N train examples (valid gets N/5)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--keep-ungrounded-calls", action="store_true",
                    help="keep call examples whose company/issuer/bond id is not written anywhere in the prompt "
                         "(default: drop them, they teach the model to guess names)")
    a = ap.parse_args()
    prompts = a.prompts or os.path.join(os.path.dirname(os.path.abspath(a.sft.rstrip("/"))), "out")
    os.makedirs(a.out, exist_ok=True)

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.tokenizer, trust_remote_code=False)

    def n_tokens(ex):
        text = tok.apply_chat_template(ex["messages"], tools=ex.get("tools"), tokenize=False)
        return len(tok(text, add_special_tokens=False)["input_ids"])

    teacher = {}
    with open(os.path.join(a.sft, "answers_raw.jsonl"), encoding="utf-8") as f:
        for l in f:
            r = json.loads(l)
            teacher[r["id"]] = (r.get("answer") or "").strip()

    rng = random.Random(a.seed)
    report = {"prompts_dir": prompts, "max_tokens": a.max_tokens, "small": a.small, "splits": {}}
    for src, dst in SPLITS.items():
        s = Counter()
        orig = {}
        with open(os.path.join(prompts, f"{src}.jsonl"), encoding="utf-8") as f:
            for l in f:
                r = json.loads(l)
                orig[r["id"]] = r
        examples = []  # (kind, example)
        json_rows_done = set()

        # 1) sft rows: final-answer examples (structured history for JSON-call rows), pass-through otherwise
        with open(os.path.join(a.sft, f"{src}.jsonl"), encoding="utf-8") as f:
            for l in f:
                r = json.loads(l)
                s["sft_rows_read"] += 1
                last, think = final_target(r, teacher, a.keep_ground_truth, s)
                o = orig.get(r["id"])
                is_json_row = False
                if o is not None and o.get("task") == "tool_use":
                    hist, calls = structured(o["messages"])
                    is_json_row = bool(calls)
                if is_json_row:
                    sys_msg = r["messages"][0]
                    if sys_msg["role"] != "system" or r["messages"][1:-1] != flattened(o["messages"]):
                        s["join_mismatch_passed_through"] += 1
                        is_json_row = False
                if is_json_row:
                    ex = {"messages": [sys_msg] + hist + [last], "tools": wrap_tools(o.get("tools"))}
                    examples.append(("final_tool", ex))
                    json_rows_done.add(r["id"])
                else:
                    ex = {"messages": r["messages"][:-1] + [last]}
                    kind = "prose_tool_passthrough" if (o and o.get("task") == "tool_use") else "other_passthrough"
                    examples.append((kind, ex))
                s["think" if think else "plain"] += 1

        # 2) call examples: every tool_use row in this split with >=1 JSON call turn
        #    (also rows with no final-answer example, since the call target uses no ground truth)
        for rid, o in orig.items():
            if o.get("task") != "tool_use":
                continue
            s["tool_rows_in_prompts"] += 1
            hist, calls = structured(o["messages"])
            n_prose = sum(1 for m in o["messages"] if m["role"] == "assistant") - len(calls)
            if not calls:
                s["tool_rows_prose_or_no_call"] += 1
                continue
            s["tool_rows_json_call"] += 1
            s["prose_turns_skipped_in_json_rows"] += n_prose
            if rid not in json_rows_done:
                s["json_rows_without_final_example"] += 1
            sys_msg = {"role": "system", "content": system_for(o)}
            tools = wrap_tools(o.get("tools"))
            names = {t["function"].get("name") for t in tools}
            for pos in calls:
                tgt = hist[pos]
                fn = tgt["tool_calls"][0]["function"]
                if fn["name"] not in names:
                    s["call_name_not_in_tools"] += 1
                if not a.keep_ungrounded_calls and ungrounded_entities(hist[:pos], fn["arguments"]):
                    s["call_dropped_ungrounded_entity"] += 1
                    continue
                examples.append(("call", {"messages": [sys_msg] + hist[:pos + 1], "tools": tools}))

        rows = []
        for kind, ex in examples:
            if n_tokens(ex) > a.max_tokens:
                s["dropped_long"] += 1
                s["dropped_long_" + kind] += 1
                continue
            rows.append((kind, ex))
        if a.small:
            n = a.small if src == "train" else a.small // 5 if src == "val" else len(rows)
            rng.shuffle(rows)
            rows = rows[:n]
        else:
            rng.shuffle(rows)
        with open(os.path.join(a.out, f"{dst}.jsonl"), "w", encoding="utf-8") as f:
            for _, ex in rows:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        w = Counter(k for k, _ in rows)
        s["written"] = len(rows)
        s["written_call_examples"] = w["call"]
        s["written_final_answer_tool_examples"] = w["final_tool"]
        s["written_prose_tool_passthrough"] = w["prose_tool_passthrough"]
        s["written_other_passthrough"] = w["other_passthrough"]
        report["splits"][dst] = dict(sorted(s.items()))
    with open(os.path.join(a.out, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


# Same system prompt build_sft.py uses for thinking == "on" rows (copied, not imported).
SYSTEM_ON = (
    "You are a financial analyst. Use only the information given in the prompt. "
    "Show the calculation when a number is requested. "
    "Answer with a single value when the question asks for one: a number in the units "
    "stated in the source, a label from the label set given, or a list of items. "
    "If the data needed is not present, say what is missing instead of estimating."
)
SYSTEM_OFF = (
    "You are a financial analyst. Answer directly and briefly. "
    "Give the value, label or span requested, in the units stated in the source."
)
FORMAT_HINT = {
    "number": "Reply with the number only, no units and no thousands separators.",
    "text": "Reply in one or two sentences.",
    "label": "Reply with one label from the set given in the question.",
    "list": "Reply with the items, one per line.",
}


def system_for(row):
    system = SYSTEM_ON if row.get("thinking", "on") == "on" else SYSTEM_OFF
    if row.get("answer_type") in FORMAT_HINT:
        system += " " + FORMAT_HINT[row["answer_type"]]
    return system


if __name__ == "__main__":
    main()
