#!/usr/bin/env python3
"""Aggregate the 20 area files into train/val/test splits and audit the union.

Usage: python3 aggregate.py [--root ~/finance-prompt-set] [--keep-splits]

- re-runs validate.py on every area file (authoritative gate)
- assigns the CANONICAL split pass: one fixture group never straddles splits
- exact duplicate audit across areas, family coverage audit
- writes out/{train,val,test,all}.jsonl + out/summary.json + out/COVERAGE.md
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

MASK = re.compile(r"\d+(?:[.,]\d+)*")
WS = re.compile(r"\s+")
TARGET = {"train": 0.8, "val": 0.1, "test": 0.1}
SPLITS = ["train", "val", "test"]
TASKS = ["calc", "extraction", "qa", "classification", "summarization", "tool_use"]


def norm(s):
    return WS.sub(" ", str(s)).strip().lower()


def masked(s):
    return MASK.sub("#", norm(s))


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def area_of(r):
    return r["id"].split("_")[1]


def row_body(r):
    if "messages" in r:
        return norm(json.dumps(r["messages"], ensure_ascii=False, sort_keys=True))
    return norm(r.get("context", "")) + " | " + norm(r.get("question", ""))


def fam_key(r):
    src = r.get("question")
    if src is None and "messages" in r:
        src = next((m["content"] for m in r["messages"] if m.get("role") == "user"), "")
    return masked(src or "")[:160]


def fixture_key(r):
    """Rows sharing a key are the same document/scenario and must share a split."""
    if r.get("context"):
        return "ctx:" + sha(masked(r["context"]))
    if "messages" in r:
        first = next((m["content"] for m in r["messages"] if m.get("role") == "user"), "")
        return "msg:" + sha(area_of(r) + "|" + masked(first))
    return "qa:" + sha(area_of(r) + "|" + masked(r.get("question", "")))


def canonical_split(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[fixture_key(r)].append(r)
    totals = Counter(r["task"] for r in rows)
    target = {s: Counter({t: TARGET[s] * n for t, n in totals.items()}) for s in SPLITS}
    done = {s: Counter() for s in SPLITS}
    for key in sorted(groups, key=sha):
        mix = Counter(r["task"] for r in groups[key])
        best, best_score = None, None
        for s in SPLITS:
            score = 0.0
            for t, c in mix.items():
                if target[s][t] <= 0:
                    continue
                score += c * max(0.0, target[s][t] - done[s][t]) / target[s][t]
            if best_score is None or score > best_score:
                best, best_score = s, score
        done[best].update(mix)
        for r in groups[key]:
            r["split"] = best
    return len(groups)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/finance-prompt-set"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-splits", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    out = os.path.abspath(a.out or os.path.join(root, "out"))
    os.makedirs(out, exist_ok=True)
    areas = json.load(open(os.path.join(root, "areas.json")))["areas"]
    validator = os.path.join(root, "validate.py")

    rows_all, per_area, problems = [], [], []
    seen_hash, seen_fam = {}, defaultdict(list)

    for meta in areas:
        slug, prof = meta["slug"], meta["profile"]
        p = os.path.join(root, "data", slug, "prompts.jsonl")
        if not os.path.exists(p):
            problems.append({"area": slug, "issue": "missing prompts.jsonl"})
            per_area.append({"area": slug, "profile": prof, "status": "MISSING"})
            continue
        rr = subprocess.run([sys.executable, validator, p, "--area", slug, "--profile", prof,
                             "--expect", "1000"], capture_output=True, text=True)
        try:
            v = json.loads(rr.stdout)
        except json.JSONDecodeError:
            v = {"status": "fail", "errors": [rr.stdout[:300] + rr.stderr[:300]]}
        status = "pass" if rr.returncode == 0 and v.get("status") == "pass" else "FAIL"
        if status != "pass":
            problems.append({"area": slug, "issue": "validator", "detail": v.get("errors", [])[:6]})
        n = dups = 0
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            row = json.loads(line)
            n += 1
            bh = sha(row_body(row))
            if bh in seen_hash:
                dups += 1
                problems.append({"area": slug, "issue": "cross_area_exact_dup",
                                 "id": row["id"], "other": seen_hash[bh]})
            else:
                seen_hash[bh] = row["id"]
            seen_fam[(masked(row.get("context", ""))[:200], fam_key(row))].append(
                (slug, row["id"]))
            rows_all.append(row)
        per_area.append({"area": slug, "profile": prof, "status": status, "rows": n,
                         "dups": dups, "families": v.get("distinct_question_families"),
                         "top_share": v.get("top_family_share")})

    groups = len(set(fixture_key(r) for r in rows_all)) if a.keep_splits else canonical_split(rows_all)

    fk = defaultdict(set)
    for r in rows_all:
        fk[fixture_key(r)].add(r["split"])
    doc_straddles = sum(1 for v in fk.values() if len(v) > 1)
    cross_area_fam = sum(1 for v in seen_fam.values() if len({x[0] for x in v}) > 1)
    dup_fams_same_area = sum(1 for v in seen_fam.values()
                             if len(v) > 1 and len({x[0] for x in v}) == 1)

    by_task = Counter(r["task"] for r in rows_all)
    by_split = Counter(r["split"] for r in rows_all)
    by_at = Counter(r["answer_type"] for r in rows_all)
    by_think = Counter(r["thinking"] for r in rows_all)
    by_area = Counter(area_of(r) for r in rows_all)
    split_task = defaultdict(Counter)
    split_area = defaultdict(Counter)
    for r in rows_all:
        split_task[r["split"]][r["task"]] += 1
        split_area[r["split"]][area_of(r)] += 1

    for s in SPLITS:
        with open(os.path.join(out, f"{s}.jsonl"), "w", encoding="utf-8") as f:
            for r in rows_all:
                if r["split"] == s:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out, "all.jsonl"), "w", encoding="utf-8") as f:
        for r in rows_all:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "rows_total": len(rows_all),
        "areas_passing": len([x for x in per_area if x.get("status") == "pass"]),
        "areas_total": len(areas),
        "fixture_groups": groups,
        "documents_straddling_splits": doc_straddles,
        "by_task": dict(by_task),
        "by_split": dict(by_split),
        "split_task": {s: {t: split_task[s][t] for t in TASKS} for s in SPLITS},
        "split_areas": {s: len([k for k, c in split_area[s].items() if c > 0]) for s in SPLITS},
        "by_answer_type": dict(by_at),
        "by_thinking": dict(by_think),
        "by_area": dict(by_area),
        "distinct_question_families": len(seen_fam),
        "cross_area_duplicate_families": cross_area_fam,
        "same_area_duplicate_families": dup_fams_same_area,
        "problems": problems[:60],
        "per_area": per_area,
    }
    json.dump(summary, open(os.path.join(out, "summary.json"), "w", encoding="utf-8"), indent=2)

    lines = [f"# Coverage — {len(rows_all)} rows, {len(areas)} areas", "",
             "| area | profile | validator | rows | families | top family share |",
             "|---|---|---|---|---|---|"]
    for x in per_area:
        lines.append(f"| {x['area']} | {x.get('profile')} | {x.get('status')} | {x.get('rows','-')} "
                     f"| {x.get('families','-')} | {x.get('top_share','-')} |")
    lines += ["", "## Rows by task and split", "", "| task | train | val | test | total |",
              "|---|---|---|---|---|"]
    for t in TASKS:
        lines.append(f"| {t} | {split_task['train'][t]} | {split_task['val'][t]} | "
                     f"{split_task['test'][t]} | {by_task[t]} |")
    open(os.path.join(out, "COVERAGE.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print(json.dumps({k: summary[k] for k in ("rows_total", "areas_passing", "areas_total",
                                              "fixture_groups", "documents_straddling_splits",
                                              "by_split", "by_task", "by_answer_type",
                                              "by_thinking", "distinct_question_families",
                                              "cross_area_duplicate_families")}, indent=2))
    print("problems:", len(problems))
    for p in problems[:8]:
        print(" -", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
