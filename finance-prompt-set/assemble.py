#!/usr/bin/env python3
"""Assemble training examples from the prompt set at load time.

The JSONL stores pieces (context, question, ground_truth) so the instruction
template can change without regenerating 20k rows. This is that template.

    python3 assemble.py --stats
    python3 assemble.py --split val --limit 3 --show

    from assemble import to_example
    ex = to_example(row)         # {"messages": [...], "target": "..."}
"""
import argparse
import json
import os
import re

SYSTEM = (
    "You are a financial analyst. Use only the information given in the prompt. "
    "Show the calculation when a number is requested. "
    "Answer with a single value when the question asks for one: a number in the units "
    "stated in the source, a label from the label set given, or a list of items. "
    "If the data needed is not present, say what is missing instead of estimating."
)

SYSTEM_ANSWER_ONLY = (
    "You are a financial analyst. Answer directly and briefly. "
    "Give the value, label or span requested, in the units stated in the source."
)

FORMAT_HINT = {
    "number": "Reply with the number only, no units and no thousands separators.",
    "text": "Reply in one or two sentences.",
    "label": "Reply with one label from the set given in the question.",
    "list": "Reply with the items, one per line.",
}


def build_messages(row):
    at = row.get("answer_type")
    system = SYSTEM if row.get("thinking") == "on" else SYSTEM_ANSWER_ONLY
    if at in FORMAT_HINT:
        system = system + " " + FORMAT_HINT[at]
    if "messages" in row:
        return [{"role": "system", "content": system}] + row["messages"]
    ctx = row.get("context") or ""
    q = row["question"]
    content = f"{ctx}\n\n{q}" if ctx else q
    return [{"role": "system", "content": system}, {"role": "user", "content": content}]


def format_target(row):
    gt = row.get("ground_truth")
    if gt is None:
        return None
    if isinstance(gt, list):
        return "\n".join(gt)
    if isinstance(gt, float) and gt.is_integer():
        return str(int(gt))
    return str(gt)


def flat_str(x):
    """Check-safe plain-string serialization: numbers render canonically, lists
    serialize to JSON, None becomes "" — never a mixed-type column."""
    if x is None:
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    if isinstance(x, str):
        return x
    return json.dumps(x, ensure_ascii=False)


def to_example(row):
    ex = {"id": row["id"], "task": row["task"], "answer_type": row["answer_type"],
          "tolerance": row.get("tolerance"), "messages": build_messages(row),
          "target": format_target(row), "thinking": row.get("thinking")}
    if "tools" in row:
        ex["tools"] = row["tools"]
    return ex


# ---------------------------------------------------------------------------
# Hugging Face conversion — single source of truth for the chatml assembly.
# Both the batch converter (hf/generate_hf.py) and any live eval/inference
# script must import these functions so prompts are identical everywhere.
# ---------------------------------------------------------------------------

CHATML_SYS = ("You are a financial analyst. Use only the information given. "
              "Show the calculation when a number is requested. If the needed "
              "data is not present, say what is missing instead of estimating. "
              "Follow the output format stated in the user turn.")
CHATML_SYS_SHORT = ("You are a financial analyst. Answer directly and briefly. "
                    "Give the value, label or span requested, in the units stated.")


def chatml(role, content):
    return f"<|im_start|>{role}\n{content}<|im_end|>"


def normalize_ground_truth(gt, answer_type=None):
    """Check-side normalized form of a ground truth: lowercased, whitespace
    collapsed, surrounding quotes stripped. Numbers render canonically so
    leading-digit and all-zero values stay exact as text. None -> ""."""
    if gt is None:
        return ""
    if isinstance(gt, bool):
        return str(gt)
    if isinstance(gt, (int, float)):
        return str(int(gt)) if float(gt).is_integer() else str(gt)
    if isinstance(gt, list):
        items = [re.sub(r"\s+", " ", str(x)).strip().strip("\"'").lower() for x in gt]
        return "\n".join(items)
    s = re.sub(r"\s+", " ", str(gt)).strip().strip("\"'")
    return s.lower()


def build_hf_text(row, include_target=True):
    """One chatml transcript per row. Multi-turn (tool) rows keep their full
    trajectory; single-turn rows become system + user(context + question).
    The assistant turn carries the reference answer when one exists, so the
    text column is SFT-ready; rows without ground truth end on an open
    assistant turn for judge-based or consistency-based training."""
    sys = CHATML_SYS if row.get("thinking") == "on" else CHATML_SYS_SHORT
    at = row.get("answer_type")
    if at in FORMAT_HINT:
        sys = f"{sys} {FORMAT_HINT[at]}"
    msgs = row.get("messages")
    if msgs:
        parts = [] if msgs[0].get("role") == "system" else [chatml("system", sys)]
        parts += [chatml(m["role"], m["content"]) for m in msgs]
    else:
        ctx, q = row.get("context") or "", row["question"]
        parts = [chatml("system", sys),
                 chatml("user", f"{ctx}\n\n{q}" if ctx else q)]
    gt = format_target(row)
    parts.append(chatml("assistant", gt if (include_target and gt is not None) else ""))
    return "\n".join(parts)


HF_COLUMNS = ["id", "task", "source", "answer_type", "tolerance", "split",
              "thinking", "text", "tools", "ground_truth",
              "ground_truth_normalized", "target_hint"]


def to_hf_record(row):
    """Canonical HF record: 12 string columns. Variable-shape values
    (numbers, lists, tool schemas) are serialized to JSON/plain strings so the
    Arrow schema unifies without type conflicts."""
    tools = row.get("tools") or []
    return {
        "id": row["id"],
        "task": row["task"],
        "source": row["source"],
        "answer_type": row["answer_type"],
        "tolerance": row.get("tolerance") or "",
        "split": row["split"],
        "thinking": row["thinking"],
        "text": build_hf_text(row),
        "tools": json.dumps(tools, ensure_ascii=False, separators=(",", ":")) if tools else "",
        "ground_truth": flat_str(row.get("ground_truth")),
        "ground_truth_normalized": normalize_ground_truth(row.get("ground_truth"),
                                                          row.get("answer_type")),
        "target_hint": FORMAT_HINT.get(row.get("answer_type"), ""),
    }


def main():
    ap = argparse.ArgumentParser()
    root = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--split", default="all", choices=["train", "val", "test", "all"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    path = os.path.join(root, "out", f"{a.split}.jsonl")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    if a.limit:
        rows = rows[: a.limit]
    if a.stats:
        from collections import Counter
        print(json.dumps({"split": a.split, "rows": len(rows),
                          "task": dict(Counter(r["task"] for r in rows)),
                          "targets_present": sum(1 for r in rows if r.get("ground_truth") is not None)},
                         indent=2))
        return
    for r in rows:
        ex = to_example(r)
        if a.show:
            print(json.dumps(ex, indent=2, ensure_ascii=False)[:1200])
        else:
            print(json.dumps(ex, ensure_ascii=False))


if __name__ == "__main__":
    main()
