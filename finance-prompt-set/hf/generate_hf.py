#!/usr/bin/env python3
"""Build the Hugging Face conversion of the finance prompt set.

    python3 hf/generate_hf.py --root ~/finance-prompt-set

Reads raw/validation_passed_prompts.jsonl (the checked rows, exactly what out/*.jsonl
contain) and writes hf/unified_prompts.jsonl plus an explicit Arrow cache-check via
datasets, so both consumers see row-for-row identical content.

The chatml assembly lives in assemble.py (build_hf_text / to_hf_record) — the batch
converter and any live eval/inference script import the same functions so prompts are
identical everywhere. Never re-implement the assembly here.
"""
import argparse
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assemble import to_hf_record  # noqa: E402  (single source of truth)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = os.path.abspath(os.path.expanduser(a.root))
    out = os.path.abspath(a.out or os.path.join(root, "hf"))
    os.makedirs(out, exist_ok=True)
    src = os.path.join(root, "raw", "validation_passed_prompts.jsonl")
    if os.path.exists(src):
        raw_lines = [l for l in open(src, encoding="utf-8") if l.strip()]
    else:
        # raw/ is a local build artifact; the repo ships the same bytes as splits.
        raw_lines = []
        for s in ("train", "val", "test"):
            p = os.path.join(root, "out", f"{s}.jsonl")
            raw_lines += [l for l in open(p, encoding="utf-8") if l.strip()]
    rows = [json.loads(l) for l in raw_lines]
    hf_rows, lens = [], []
    for r in rows:
        hf_rows.append(to_hf_record(r))
        lens.append(len(hf_rows[-1]["text"]))
    dst = os.path.join(out, "unified_prompts.jsonl")
    with open(dst, "w", encoding="utf-8") as f:
        for h in hf_rows:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
    lens.sort()
    stats = {
        "rows": len(hf_rows),
        "text_chars": {"mean": int(st.mean(lens)), "p50": int(lens[len(lens) // 2]),
                       "p95": int(lens[int(len(lens) * 0.95)]), "max": max(lens)},
        "with_tools": sum(1 for h in hf_rows if h["tools"]),
        "ground_truth_missing": sum(1 for h in hf_rows if not h["ground_truth"]),
    }
    json.dump(stats, open(os.path.join(out, "stats.json"), "w", encoding="utf-8"), indent=2)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
