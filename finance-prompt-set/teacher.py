#!/usr/bin/env python3
"""Get DeepSeek reasoning + answers for the finance prompt set (thinking == "on" rows).

Only rows that need reasoning traces are sent. Rows with thinking == "off" already
have a ground-truth answer and never touch the API (see build_sft.py).

Setup (once):
    export OPENCODE_API_KEY="..."        # do NOT paste the key into chat or into this file

Test with 5 rows first and look at the output:
    python3 teacher.py --data /path/to/finance-prompt-set/out --limit 5

Full run (safe to stop and restart; it skips ids already saved):
    python3 teacher.py --data /path/to/finance-prompt-set/out --workers 4

Output: answers_raw.jsonl, one line per row:
    {"id", "reasoning", "answer", "usage", "model"}
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

# Copied from the repo's assemble.py so this script never imports downloaded code.
SYSTEM = (
    "You are a financial analyst. Use only the information given in the prompt. "
    "Show the calculation when a number is requested. "
    "Answer with a single value when the question asks for one: a number in the units "
    "stated in the source, a label from the label set given, or a list of items. "
    "If the data needed is not present, say what is missing instead of estimating."
)
FORMAT_HINT = {
    "number": "Reply with the number only, no units and no thousands separators.",
    "text": "Reply in one or two sentences.",
    "label": "Reply with one label from the set given in the question.",
    "list": "Reply with the items, one per line.",
}

BASE_URL = "https://opencode.ai/zen/go/v1/chat/completions"


def build_messages(row):
    system = SYSTEM
    at = row.get("answer_type")
    if at in FORMAT_HINT:
        system = system + " " + FORMAT_HINT[at]
    if "messages" in row:
        msgs = []
        for m in row["messages"]:
            if m["role"] == "tool":  # plain chat API: show tool output as text
                msgs.append({"role": "user", "content": "Tool result:\n" + m["content"]})
            else:
                msgs.append({"role": m["role"], "content": m["content"]})
        return [{"role": "system", "content": system}] + msgs
    ctx = row.get("context") or ""
    q = row["question"]
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"{ctx}\n\n{q}" if ctx else q}]


def call_api(key, session, model, messages, max_tokens, timeout, retries):
    body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            BASE_URL, data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}",
                     "User-Agent": "finance-teacher/1.0",
                     "x-opencode-session": session})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504, 529) and attempt < retries:
                wait = e.headers.get("retry-after")
                time.sleep(float(wait) if wait and wait.replace(".", "").isdigit() else min(60, 2 ** attempt * 2))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries:
                time.sleep(min(60, 2 ** attempt * 2))
                continue
            raise
    raise RuntimeError("retries exhausted")


def one(row, key, session, model, max_tokens, timeout, retries):
    resp = call_api(key, session, model, build_messages(row), max_tokens, timeout, retries)
    msg = resp["choices"][0]["message"]
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
    return {"id": row["id"], "reasoning": reasoning, "answer": (msg.get("content") or "").strip(),
            "usage": resp.get("usage"), "model": resp.get("model", model),
            "finish": resp["choices"][0].get("finish_reason")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder with train/val/test.jsonl (finance-prompt-set/out)")
    ap.add_argument("--out", default="answers_raw.jsonl")
    ap.add_argument("--model", default="deepseek-v4.1-flash")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="only first N pending rows (use 5 to test)")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--retries", type=int, default=6)
    ap.add_argument("--splits", default="train,val,test")
    ap.add_argument("--session", default="", help="stable x-opencode-session id (else $OPENCODE_SESSION_ID, else generated)")
    a = ap.parse_args()

    key = os.environ.get("OPENCODE_API_KEY")
    if not key:
        sys.exit("Set OPENCODE_API_KEY first: export OPENCODE_API_KEY=...")
    session = a.session or os.environ.get("OPENCODE_SESSION_ID") or f"finance-teacher-{uuid.uuid4().hex[:12]}"

    rows = []
    for s in a.splits.split(","):
        with open(os.path.join(a.data, f"{s}.jsonl"), encoding="utf-8") as f:
            rows += [json.loads(l) for l in f if l.strip()]
    todo = [r for r in rows if r.get("thinking") == "on" and r.get("ground_truth") is not None]

    done = set()
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as f:
            for l in f:
                if l.strip():
                    done.add(json.loads(l)["id"])
    todo = [r for r in todo if r["id"] not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(done)} already done, {len(todo)} to run, model={a.model}, workers={a.workers}, session={session}")

    ok = fail = no_reason = 0
    t0 = time.time()
    with open(a.out, "a", encoding="utf-8") as out, cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, r, key, session, a.model, a.max_tokens, a.timeout, a.retries): r["id"] for r in todo}
        for fut in cf.as_completed(futs):
            try:
                res = fut.result()
            except Exception as e:  # keep going; failed ids are simply retried next run
                fail += 1
                print(f"FAIL {futs[fut]}: {e}", file=sys.stderr)
                continue
            out.write(json.dumps(res, ensure_ascii=False) + "\n")
            out.flush()
            ok += 1
            no_reason += 0 if res["reasoning"] else 1
            if ok % 50 == 0 or a.limit:
                print(f"{ok} ok, {fail} failed, {no_reason} without reasoning, {time.time() - t0:.0f}s")
    print(f"DONE: {ok} ok, {fail} failed, {no_reason} without reasoning")
    if ok and no_reason == ok:
        print("WARNING: the API returned no reasoning field for any row. Do not run the full job yet.")


if __name__ == "__main__":
    main()
