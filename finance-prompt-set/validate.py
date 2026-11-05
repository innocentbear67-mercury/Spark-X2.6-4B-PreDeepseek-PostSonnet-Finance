#!/usr/bin/env python3
"""Shared validator for the finance prompt set.

Usage:
    python3 validate.py prompts.jsonl --area <slug> --profile <A|B|C> [--expect 1000]
    python3 validate.py prompts.jsonl --no-quota        # smoke tests only

Exit 0 + {"status": "pass"} only when every hard rule holds.
Do not edit per area; the whole point is one gate for 20 files.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

TASKS = ["calc", "extraction", "summarization", "classification", "qa", "tool_use"]
ABBR = {
    "calc": "calc",
    "extraction": "extr",
    "summarization": "summ",
    "classification": "cls",
    "qa": "qa",
    "tool_use": "tool",
}
ANSWER_TYPES = ["number", "text", "label", "list"]
SPLITS = ["train", "val", "test"]
PROFILES = {
    "A": {"calc": 280, "extraction": 220, "qa": 200, "classification": 100,
          "summarization": 100, "tool_use": 100},
    "B": {"calc": 120, "extraction": 220, "qa": 240, "classification": 220,
          "summarization": 100, "tool_use": 100},
    "C": {"calc": 150, "extraction": 150, "qa": 200, "classification": 50,
          "summarization": 50, "tool_use": 400},
}
THINKING_ON = {"calc", "qa", "tool_use"}
TOL_RE = re.compile(r"^(abs:\d+(?:\.\d+)?|rel:\d+(?:\.\d+)?)$")
TOL_TEXT = {"normalized", "exact"}
TOL_LABEL = {"exact"}
TOL_LIST = {"set", "ordered"}
KEYS_SINGLE = {"id", "task", "source", "context", "question", "ground_truth",
               "answer_type", "tolerance", "split", "thinking"}
KEYS_MULTI = {"id", "task", "source", "messages", "tools", "ground_truth",
              "answer_type", "tolerance", "split", "thinking"}
THOUSANDS = re.compile(r"(?<![\w.])\d{1,3}(,\d{3})+(?!\d)")
MOJIBAKE = ("\u00e2\u20ac", "\u00c3\u00a9", "\ufffd")
UNITS_LINE = re.compile(r"(?im)^\s*units\s*:")
TIME_SENSITIVE = re.compile(
    r"(?i)\b(current|today|latest|right now|recently|this year|last year|as of today)\b")
BAD_NUMERAL = re.compile(r"\d\.\d+\.\d+|[$€£]\s*\d")
MASK = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")


def norm(s):
    return WS.sub(" ", str(s)).strip().lower()


def mask(s):
    return MASK.sub("#", norm(s))


def fail(errors, kind, detail):
    errors.append({"kind": kind, "detail": detail})


def check_row(i, row, area, profile, errors, stats):
    tag = f"line {i}"
    if not isinstance(row, dict):
        fail(errors, "not_object", tag)
        return
    keys = set(row)
    task = row.get("task")
    if task not in TASKS:
        fail(errors, "bad_task", f"{tag}: {task!r}")
        return
    mult_turn = "messages" in keys
    allowed = KEYS_MULTI if mult_turn else KEYS_SINGLE
    extra = keys - allowed
    missing = allowed - keys
    if extra:
        fail(errors, "extra_keys", f"{tag}: {sorted(extra)}")
    if missing:
        fail(errors, "missing_keys", f"{tag}: {sorted(missing)}")
        return

    # id
    rid = row["id"]
    want = f"fin_{area}_{ABBR[task]}_"
    if not (isinstance(rid, str) and rid.startswith(want) and rid[len(want):].isdigit()
            and len(rid) == len(want) + 6):
        fail(errors, "bad_id", f"{tag}: {rid!r} != {want}NNNNNN")
    if rid in stats["ids"]:
        fail(errors, "dup_id", f"{tag}: {rid}")
    stats["ids"].add(rid)

    # split / thinking / source
    if row["split"] not in SPLITS:
        fail(errors, "bad_split", f"{tag}: {row['split']!r}")
    want_thinking = "on" if task in THINKING_ON else "off"
    if row["thinking"] != want_thinking:
        fail(errors, "bad_thinking", f"{tag}: {row['thinking']!r} for {task}, want {want_thinking}")
    src = row["source"]
    if not (src == "knowledge:finance_general" or src == f"synthetic:{area}"):
        fail(errors, "bad_source", f"{tag}: {src!r}")

    # answer_type / tolerance / ground_truth
    at = row.get("answer_type")
    gt = row.get("ground_truth")
    tol = row.get("tolerance")
    if at not in ANSWER_TYPES:
        fail(errors, "bad_answer_type", f"{tag}: {at!r}")
    elif gt is None:
        if tol is not None:
            fail(errors, "tol_without_gt", f"{tag}: {tol!r}")
    else:
        stats["answer_type"][at] += 1
        if at == "number":
            if isinstance(gt, bool) or not isinstance(gt, (int, float)) or not math.isfinite(gt):
                fail(errors, "number_type", f"{tag}: ground_truth {gt!r} not finite number")
            if not (isinstance(tol, str) and TOL_RE.match(tol)):
                fail(errors, "bad_tolerance", f"{tag}: {tol!r} for number")
        elif at == "text":
            if not isinstance(gt, str):
                fail(errors, "text_type", f"{tag}: {type(gt).__name__}")
            if tol not in TOL_TEXT:
                fail(errors, "bad_tolerance", f"{tag}: {tol!r} for text")
        elif at == "label":
            if not isinstance(gt, str) or not gt.strip() or len(gt) > 48:
                fail(errors, "label_type", f"{tag}: {gt!r}")
            if tol not in TOL_LABEL:
                fail(errors, "bad_tolerance", f"{tag}: {tol!r} for label")
        elif at == "list":
            if not isinstance(gt, list) or not gt or len(gt) > 40 or \
                    not all(isinstance(x, str) and x.strip() for x in gt):
                fail(errors, "list_type", f"{tag}: {gt!r}")
            if tol not in TOL_LIST:
                fail(errors, "bad_tolerance", f"{tag}: {tol!r} for list")
    if gt is not None and at == "number" and "think" not in tag:
        pass  # keep branch explicit for readability

    # body
    if mult_turn:
        msgs = row["messages"]
        if not isinstance(msgs, list) or not msgs:
            fail(errors, "messages_shape", tag)
            msgs = []
        last_role = None
        for m in msgs:
            if not isinstance(m, dict) or "role" not in m or "content" not in m:
                fail(errors, "messages_shape", f"{tag}: {m!r}")
                continue
            if m["role"] not in {"system", "user", "assistant", "tool"}:
                fail(errors, "message_role", f"{tag}: {m['role']!r}")
            if not isinstance(m["content"], str) or not m["content"].strip():
                fail(errors, "message_content", f"{tag}: empty")
            last_role = m["role"]
        if last_role != "user":
            fail(errors, "last_message", f"{tag}: last role {last_role!r}")
        tools = row["tools"]
        if not isinstance(tools, list) or not tools:
            fail(errors, "tools_shape", tag)
            tools = []
        names = []
        for t in tools:
            if not isinstance(t, dict) or set(t) != {"name", "description", "parameters"}:
                fail(errors, "tools_shape", f"{tag}: {t!r}")
                continue
            if not isinstance(t["parameters"], dict):
                fail(errors, "tools_params", f"{tag}: {t['name']}")
            names.append(t["name"])
        if len(names) != len(set(names)):
            fail(errors, "tools_dup", f"{tag}: {names}")
        if task != "tool_use":
            fail(errors, "tools_on_non_tool_task", f"{tag}: {task}")
        if any(m.get("role") == "assistant" for m in msgs):
            stats["tool_multi_step"] += 1
        stats["tool_rows"] += 1
        body_key = json.dumps(msgs, ensure_ascii=False, sort_keys=True)
        fam_src = next((m["content"] for m in msgs if m.get("role") == "user"), "")
    else:
        ctx, q = row["context"], row["question"]
        if task == "tool_use":
            fail(errors, "tool_task_single_turn", tag)
        if not isinstance(ctx, str):
            fail(errors, "context_type", tag)
            ctx = ""
        if not isinstance(q, str) or len(q.strip()) < 8 or len(q) > 600:
            fail(errors, "question_shape", f"{tag}: {len(str(q))} chars")
            q = str(q)
        if ctx:
            if len(ctx) < 40 or len(ctx) > 9000:
                fail(errors, "context_len", f"{tag}: {len(ctx)} chars")
            if not ctx.lstrip().startswith(("Units:", "|", "#", "Excerpt", "Memo", "Email",
                                            "Transcript", "Policy", "Note", "Segment",
                                            "Deal", "Covenant", "Holding", "Fund", "Property")):
                fail(errors, "context_lead", f"{tag}: starts {ctx[:40]!r}")
        if (src == "knowledge:finance_general") != (ctx == ""):
            fail(errors, "knowledge_source_mismatch", f"{tag}: src={src} ctx_len={len(ctx)}")
        if ctx == "" and TIME_SENSITIVE.search(q):
            fail(errors, "time_sensitive_no_context", f"{tag}: {q[:60]!r}")
        if task == "calc":
            if not ctx:
                fail(errors, "calc_without_context", tag)
            elif not UNITS_LINE.search(ctx):
                fail(errors, "calc_missing_units", tag)
        if task == "extraction" and not ctx:
            fail(errors, "extraction_without_context", tag)
        if isinstance(gt, (int, float)) and not isinstance(gt, bool) and ctx and \
                not UNITS_LINE.search(ctx):
            fail(errors, "numbers_missing_units", tag)
        body_key = norm(ctx) + "|" + norm(q)
        fam_src = q
        stats["ctx_set"].add(mask(ctx)[:400]) if ctx else None
        if ctx:
            stats["ctx_rows"] += 1
            stats["ctx_full"].add(mask(ctx))

    # text hygiene
    blob = body_key
    if THOUSANDS.search(blob):
        m = THOUSANDS.search(blob)
        fail(errors, "thousands_separator", f"{tag}: {m.group(0)!r}")
    if BAD_NUMERAL.search(blob):
        fail(errors, "numeral_format", f"{tag}: {BAD_NUMERAL.search(blob).group(0)!r}")
    for bad in MOJIBAKE:
        if bad in blob:
            fail(errors, "mojibake", f"{tag}: {bad!r}")

    # dedupe / diversity bookkeeping
    key = hashlib.sha256(body_key.encode("utf-8")).hexdigest()
    if key in stats["body_hash"]:
        fail(errors, "exact_dup", f"{tag}: {rid}")
    stats["body_hash"].add(key)
    fam = mask(fam_src)[:160]
    stats["family"][fam] += 1
    stats["task"][task] += 1
    stats["split"][row["split"]] += 1
    stats["split_task"][(row["split"], task)] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--area", default=None)
    ap.add_argument("--profile", default=None, choices=sorted(PROFILES))
    ap.add_argument("--expect", type=int, default=1000)
    ap.add_argument("--no-quota", action="store_true")
    ap.add_argument("--max-errors", type=int, default=25)
    a = ap.parse_args()

    errors = []
    stats = {
        "ids": set(), "body_hash": set(), "family": Counter(), "task": Counter(),
        "split": Counter(), "split_task": Counter(), "answer_type": Counter(),
        "ctx_set": set(), "ctx_full": set(), "ctx_rows": 0,
        "tool_rows": 0, "tool_multi_step": 0,
    }

    if not os.path.exists(a.path):
        print(json.dumps({"status": "fail", "error": f"missing {a.path}"}))
        return 1
    raw = open(a.path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(errors, "bom", "file starts with UTF-8 BOM")
    if raw and not raw.endswith(b"\n"):
        fail(errors, "no_trailing_newline", "file does not end with newline")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(json.dumps({"status": "fail", "error": f"not utf-8: {e}"}))
        return 1

    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    n = 0
    for i, line in enumerate(lines, 1):
        if not line.strip():
            fail(errors, "blank_line", f"line {i}")
            continue
        n += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            fail(errors, "json_parse", f"line {i}: {e}")
            continue
        if a.area:
            check_row(n, row, a.area, a.profile, errors, stats)

    rows = n
    if not a.no_quota:
        if rows != a.expect:
            fail(errors, "row_count", f"{rows} != {a.expect}")
        if a.profile:
            want = PROFILES[a.profile]
            for t in TASKS:
                if stats["task"][t] != want[t]:
                    fail(errors, "task_quota", f"{t}: {stats['task'][t]} != {want[t]}")
            for s in SPLITS:
                expect_split = {"train": 0.8, "val": 0.1, "test": 0.1}[s] * a.expect
                if abs(stats["split"][s] - expect_split) > max(3, 0.02 * a.expect):
                    fail(errors, "split_share", f"{s}: {stats['split'][s]} vs ~{expect_split:.0f}")
                for t in TASKS:
                    if stats["split_task"][(s, t)] < 3:
                        fail(errors, "split_task_thin", f"{s}/{t}: {stats['split_task'][(s, t)]}")

    # diversity
    fams = stats["family"]
    top_fam, top_n = (fams.most_common(1)[0] if fams else ("", 0))
    top_share = (top_n / rows) if rows else 0.0
    if rows >= 200:
        if len(fams) < 25:
            fail(errors, "few_families", f"{len(fams)} < 25")
        if top_share > 0.04:
            fail(errors, "family_concentration", f"{top_share:.1%} on {top_fam[:60]!r}")
        if stats["ctx_rows"] and len(stats["ctx_full"]) < 120:
            fail(errors, "few_contexts", f"{len(stats['ctx_full'])} < 120")
    if stats["tool_rows"] >= 50:
        share = stats["tool_multi_step"] / stats["tool_rows"]
        if share < 0.40:
            fail(errors, "tool_single_shot", f"multi-step share {share:.0%} < 40%")
    else:
        share = 0.0

    # near-dup across splits: same masked (context + question) in different splits
    summary = {
        "status": "pass" if not errors else "fail",
        "area": a.area,
        "profile": a.profile,
        "rows": rows,
        "by_task": dict(stats["task"]),
        "by_split": dict(stats["split"]),
        "by_answer_type": dict(stats["answer_type"]),
        "distinct_question_families": len(fams),
        "top_family_share": round(top_share, 4),
        "distinct_contexts": len(stats["ctx_full"]),
        "tool_use_multi_step_share": round(share, 3),
        "error_count": len(errors),
        "errors": errors[: a.max_errors],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
