#!/usr/bin/env python3
"""Build training files for six kinds of training that do not need reasoning traces.

Run from the folder that contains finance-prompt-set/ (or pass the paths).
Nothing here edits your existing files. It only writes into --out.

    python3 build_training_sets.py cpt        --text-dir my_filings        --out data_cpt
    python3 build_training_sets.py answer_sft --data finance-prompt-set/out --out data_answer
    python3 build_training_sets.py dpo        --data finance-prompt-set/out --sft finance-prompt-set/sft --out data_dpo
    python3 build_training_sets.py rlvr       --data finance-prompt-set/out --out data_rlvr
    python3 build_training_sets.py tool_sft   --sft3 sft_v3 --out data_tool
    python3 build_training_sets.py distill    --data finance-prompt-set/out --sft finance-prompt-set/sft --out data_distill

Add --limit 5 to any of them to write only 5 rows per file (for a quick look).
See FORMATS.md for the exact format of every output.
"""
import argparse
import json
import os
import random
import re

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
SPLITS = {"train": "train", "val": "valid", "test": "test"}
NUM = re.compile(r"-?\d[\d,]*\.?\d*")


# ---------- answer checking (same rules as build_sft.py / score.py) ----------
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
    gt, tol, at = row.get("ground_truth"), row.get("tolerance") or "", row.get("answer_type")
    if gt is None or not answer:
        return False
    if at == "number":
        got = to_num(last_line(answer))
        if got is None:
            got = to_num(answer)
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
    return norm(answer) == norm(gt)


def reward(completion, meta, require_think=True):
    """RLVR reward: 1.0 if the final answer is right, else 0.0.
    completion: model text. meta: one line of train_meta.jsonl (needs ground_truth, answer_type, tolerance).
    If the model never closes its thinking (no </think>) the reward is 0.0, same as score.py."""
    if "</think>" not in completion:
        return 0.0 if require_think else (1.0 if matches(meta, completion.strip()) else 0.0)
    return 1.0 if matches(meta, completion.rsplit("</think>", 1)[1].strip()) else 0.0


def format_target(row):
    gt = row.get("ground_truth")
    if gt is None:
        return None
    if isinstance(gt, list):
        return "\n".join(str(x) for x in gt)
    if isinstance(gt, float) and gt.is_integer():
        return str(int(gt))
    return str(gt)


# ---------- helpers ----------
def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def system_for(row, on):
    s = SYSTEM_ON if on else SYSTEM_OFF
    if row.get("answer_type") in FORMAT_HINT:
        s += " " + FORMAT_HINT[row["answer_type"]]
    return s


def user_for(row):
    ctx = row.get("context") or ""
    return f"{ctx}\n\n{row['question']}" if ctx else row["question"]


def write(out_dir, name, rows, limit):
    os.makedirs(out_dir, exist_ok=True)
    if limit:
        rows = rows[:limit]
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def teacher_answers(sft_dir):
    return {r["id"]: r for r in read(os.path.join(sft_dir, "answers_raw.jsonl"))}


def plain_rows(data_dir, split):
    """Rows with a single question (no tool_use) and a checkable ground truth."""
    return [r for r in read(os.path.join(data_dir, f"{split}.jsonl"))
            if r["task"] != "tool_use" and r.get("ground_truth") is not None]


# ---------- the six builders ----------
def build_cpt(a):
    files = []
    for root, _, names in os.walk(a.text_dir):
        files += [os.path.join(root, n) for n in sorted(names) if n.lower().endswith((".txt", ".md"))]
    if not files:
        raise SystemExit(f"No .txt or .md files found in {a.text_dir}. Put real filings or manuals there as text.")
    chunks = []
    for p in files:
        text = open(p, encoding="utf-8", errors="ignore").read()
        paras, cur = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()], ""
        for para in paras:
            while len(para) > a.chunk_chars:  # one huge paragraph: cut it
                chunks.append(para[: a.chunk_chars])
                para = para[a.chunk_chars:]
            if cur and len(cur) + len(para) + 2 > a.chunk_chars:
                chunks.append(cur)
                cur = ""
            cur = (cur + "\n\n" + para).strip()
        if cur:
            chunks.append(cur)
    random.Random(1).shuffle(chunks)
    rows = [{"text": c} for c in chunks]
    nv = max(1, int(len(rows) * a.valid_frac)) if len(rows) > 1 else 0
    train, valid = rows[nv:], (rows[:nv] or rows)  # one chunk only: reuse it for valid
    print({"files": len(files), "chunks": len(chunks),
           "train": write(a.out, "train.jsonl", train, a.limit),
           "valid": write(a.out, "valid.jsonl", valid, a.limit)})


def build_answer_sft(a):
    rep = {}
    for src, dst in SPLITS.items():
        out = []
        for r in plain_rows(a.data, src):
            on = r["thinking"] == "on"
            if on and not a.include_on:
                continue
            out.append({"messages": [{"role": "system", "content": system_for(r, False)},
                                     {"role": "user", "content": user_for(r)},
                                     {"role": "assistant", "content": format_target(r)}]})
        random.Random(1).shuffle(out)
        rep[dst] = write(a.out, f"{dst}.jsonl", out, a.limit)
    print(rep)


def build_dpo(a):
    teacher, rep = teacher_answers(a.sft), {}
    for src, dst in (("train", "train"), ("val", "valid")):  # never the test split
        pairs = []
        for r in plain_rows(a.data, src):
            t = teacher.get(r["id"])
            if r["thinking"] != "on" or not t or t.get("finish") == "length" or not t.get("answer"):
                continue
            if r["answer_type"] == "text" and not a.include_text:
                continue  # text answers are judged by exact match, so a "wrong" one may be a fine paraphrase
            if matches(r, t["answer"]):
                continue
            chosen, rejected = format_target(r), t["answer"].strip()
            system, prompt = system_for(r, True), user_for(r)
            if a.format == "mlxlora":
                pairs.append({"system": system, "prompt": prompt, "chosen": chosen, "rejected": rejected})
            elif a.format == "trl":
                pairs.append({"prompt": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                              "chosen": [{"role": "assistant", "content": chosen}],
                              "rejected": [{"role": "assistant", "content": rejected}]})
            else:  # kto: one good line and one bad line per pair
                p = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
                pairs.append({"prompt": p, "completion": [{"role": "assistant", "content": chosen}], "label": True})
                pairs.append({"prompt": p, "completion": [{"role": "assistant", "content": rejected}], "label": False})
        random.Random(1).shuffle(pairs)
        rep[dst] = write(a.out, f"{dst}.jsonl", pairs, a.limit)
    print(rep)


def build_rlvr(a):
    rep = {}
    for src, dst in (("train", "train"), ("val", "valid")):
        rows = [r for r in plain_rows(a.data, src)
                if r["thinking"] == "on" and r["answer_type"] in ("number", "label")]
        random.Random(1).shuffle(rows)
        main = [{"system": system_for(r, True), "prompt": user_for(r), "answer": format_target(r),
                 "type": "math" if r["answer_type"] == "number" else "label"} for r in rows]
        meta = [{"id": r["id"], "ground_truth": r["ground_truth"], "answer_type": r["answer_type"],
                 "tolerance": r.get("tolerance") or ""} for r in rows]
        rep[dst] = write(a.out, f"{dst}.jsonl", main, a.limit)
        write(a.out, f"{dst}_meta.jsonl", meta, a.limit)
    print(rep)


def build_tool_sft(a):
    rep = {}
    for src, dst in SPLITS.items():
        path = os.path.join(a.sft3, f"{dst}.jsonl")
        if not os.path.exists(path):
            continue
        out = []
        for r in read(path):
            last = r["messages"][-1]
            if "tool_calls" in last:  # a tool-call target: keep as is
                out.append(r)
            elif "tools" in r and not a.calls_only:  # a tool row's final answer: drop the reasoning
                m = {k: v for k, v in last.items() if k != "reasoning_content"}
                out.append({**r, "messages": r["messages"][:-1] + [m]})
        random.Random(1).shuffle(out)
        rep[dst] = write(a.out, f"{dst}.jsonl", out, a.limit)
    print(rep)


def build_distill(a):
    teacher, rep = teacher_answers(a.sft), {}
    for src, dst in SPLITS.items():
        out = []
        for r in plain_rows(a.data, src):
            t = teacher.get(r["id"])
            if r["thinking"] != "on" or not t or t.get("finish") == "length":
                continue
            ans = (t.get("answer") or "").strip()
            if not matches(r, ans):  # keep only teacher answers that are right
                continue
            out.append({"messages": [{"role": "system", "content": system_for(r, False)},
                                     {"role": "user", "content": user_for(r)},
                                     {"role": "assistant", "content": ans}]})
        random.Random(1).shuffle(out)
        rep[dst] = write(a.out, f"{dst}.jsonl", out, a.limit)
    print(rep)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **extra):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--limit", type=int, default=0, help="rows per file (0 = all)")
        for k, v in extra.items():
            p.add_argument(f"--{k.replace('_', '-')}", **v)
        p.set_defaults(fn=fn)

    add("cpt", build_cpt, text_dir=dict(required=True), chunk_chars=dict(type=int, default=2000),
        valid_frac=dict(type=float, default=0.05))
    add("answer_sft", build_answer_sft, data=dict(required=True),
        include_on=dict(action="store_true", help="also use calc/qa rows, answer only (no working shown)"))
    add("dpo", build_dpo, data=dict(required=True), sft=dict(required=True),
        format=dict(choices=["mlxlora", "trl", "kto"], default="mlxlora"),
        include_text=dict(action="store_true", help="also use text answers (noisy: paraphrases count as wrong)"))
    add("rlvr", build_rlvr, data=dict(required=True))
    add("tool_sft", build_tool_sft, sft3=dict(required=True),
        calls_only=dict(action="store_true", help="only the tool-call targets"))
    add("distill", build_distill, data=dict(required=True), sft=dict(required=True))
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
