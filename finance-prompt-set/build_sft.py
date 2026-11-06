#!/usr/bin/env python3
"""Join prompts + DeepSeek answers, keep only rows whose answer matches ground truth,
and write messages-format JSONL ready for fine-tuning.

    python3 build_sft.py --data /path/to/finance-prompt-set/out --answers answers_raw.jsonl --out sft_out

Rules
- thinking == "off" rows: the ground truth IS the answer. No API call was needed.
- thinking == "on"  rows: keep only if DeepSeek's answer matches ground truth within
  the row's tolerance AND it returned reasoning. Training text = <think>reasoning</think> + ground-truth answer.
- ground_truth == null rows (751): skipped. They need a judge, not an exact check.

Outputs in --out: train.jsonl, val.jsonl, test.jsonl, dataset_info.json, report.json, rejected.jsonl
"""
import argparse
import json
import os
import re
from collections import Counter, defaultdict

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

NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def format_target(row):
    gt = row.get("ground_truth")
    if gt is None:
        return None
    if isinstance(gt, list):
        return "\n".join(str(x) for x in gt)
    if isinstance(gt, float) and gt.is_integer():
        return str(int(gt))
    return str(gt)


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().strip("\"'`*. ").lower()


def last_line(s):
    lines = [l for l in str(s).strip().splitlines() if l.strip()]
    return lines[-1] if lines else ""


def to_num(s):
    m = NUM.findall(s)
    if not m:
        return None
    try:
        return float(m[-1].replace(",", "").rstrip("."))
    except ValueError:
        return None


def items(s):
    parts = str(s).splitlines()
    if len(parts) == 1 and "," in parts[0]:
        parts = parts[0].split(",")
    out = []
    for p in parts:
        p = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", p)
        if p.strip():
            out.append(norm(p))
    return out


def matches(row, answer):
    gt, tol = row.get("ground_truth"), row.get("tolerance") or ""
    at = row.get("answer_type")
    if gt is None or not answer:
        return False
    if at == "number":
        got = to_num(last_line(answer)) if to_num(last_line(answer)) is not None else to_num(answer)
        if got is None:
            return False
        kind, _, val = tol.partition(":")
        gt = float(gt)
        if kind == "rel":
            return abs(got - gt) <= float(val) * max(abs(gt), 1e-12)
        return abs(got - gt) <= float(val or 0.0) + 1e-9
    if at == "label":
        return norm(last_line(answer)) == norm(gt)
    if at == "list":
        a, g = items(answer), items("\n".join(str(x) for x in gt))
        return a == g if tol == "ordered" else sorted(a) == sorted(g)
    return norm(answer) == norm(gt)  # text / normalized


def messages_for(row, assistant, thinking_on, system_override=None):
    system = SYSTEM_ON if thinking_on else SYSTEM_OFF
    if row.get("answer_type") in FORMAT_HINT:
        system += " " + FORMAT_HINT[row["answer_type"]]
    if "messages" in row:
        msgs = []
        for m in row["messages"]:  # tool role flattened to plain text (see README note in report)
            if m["role"] == "tool":
                msgs.append({"role": "user", "content": "Tool result:\n" + m["content"]})
            else:
                msgs.append({"role": m["role"], "content": m["content"]})
    else:
        ctx = row.get("context") or ""
        msgs = [{"role": "user", "content": f"{ctx}\n\n{row['question']}" if ctx else row["question"]}]
    return [{"role": "system", "content": system_override or system}] + msgs + [
        {"role": "assistant", "content": assistant}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--answers", default="answers_raw.jsonl")
    ap.add_argument("--out", default="sft_out")
    ap.add_argument("--think-style", choices=["tags", "none"], default="tags",
                    help="tags = <think>..</think> inside the assistant text. Check Spark's chat_template.jinja first.")
    ap.add_argument("--empty-think-for-off", action="store_true",
                    help="prefix off-rows with an empty <think></think> block (Qwen3-style). Default: no prefix.")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    teacher = {}
    if os.path.exists(a.answers):
        with open(a.answers, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    r = json.loads(l)
                    teacher[r["id"]] = r

    stats = defaultdict(Counter)
    rejected = []
    files = {s: open(os.path.join(a.out, f"{s}.jsonl"), "w", encoding="utf-8") for s in ("train", "val", "test")}
    for split in ("train", "val", "test"):
        with open(os.path.join(a.data, f"{split}.jsonl"), encoding="utf-8") as f:
            for l in f:
                row = json.loads(l)
                key = f"{row['task']}|{row['thinking']}"
                target = format_target(row)
                if target is None:
                    stats[key]["skipped_no_ground_truth"] += 1
                    continue
                if row["thinking"] == "off":
                    text = ("<think>\n\n</think>\n\n" if a.empty_think_for_off else "") + target
                    msgs = messages_for(row, text, False)
                else:
                    t = teacher.get(row["id"])
                    if not t:
                        stats[key]["no_teacher_answer"] += 1
                        continue
                    if not t.get("reasoning"):
                        stats[key]["rejected_no_reasoning"] += 1
                        rejected.append({"id": row["id"], "why": "no reasoning"})
                        continue
                    if t.get("finish") == "length":
                        stats[key]["rejected_truncated"] += 1
                        rejected.append({"id": row["id"], "why": "truncated"})
                        continue
                    if not matches(row, t["answer"]):
                        stats[key]["rejected_wrong_answer"] += 1
                        rejected.append({"id": row["id"], "why": "wrong answer",
                                         "got": t["answer"][:200], "want": target[:200]})
                        continue
                    body = f"<think>\n{t['reasoning'].strip()}\n</think>\n\n{target}" if a.think_style == "tags" else target
                    msgs = messages_for(row, body, True)
                stats[key]["kept"] += 1
                files[split].write(json.dumps({"id": row["id"], "messages": msgs}, ensure_ascii=False) + "\n")
    for f in files.values():
        f.close()
    with open(os.path.join(a.out, "rejected.jsonl"), "w", encoding="utf-8") as f:
        for r in rejected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    info = {f"finance_{s}": {"file_name": f"{s}.jsonl", "formatting": "sharegpt",
                              "columns": {"messages": "messages"},
                              "tags": {"role_tag": "role", "content_tag": "content", "user_tag": "user",
                                       "assistant_tag": "assistant", "system_tag": "system"}}
            for s in ("train", "val", "test")}
    with open(os.path.join(a.out, "dataset_info.json"), "w") as f:
        json.dump(info, f, indent=2)

    report = {k: dict(v) for k, v in sorted(stats.items())}
    report["_note"] = ("tool_use rows are flattened to plain text (tool role -> user 'Tool result:'). "
                       "Real tool-call training needs Spark's chat template format. Unverified.")
    with open(os.path.join(a.out, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
