"""Blind packets for the requirement-classification study (paper review objection 1, `paper/review-2026-11-08.md`).

    .venv-harness/bin/python scripts/build_req_packets.py OUT_DIR

One file per task in N32 and H35: the issue text and the test patch (what the hidden tests check), nothing about
agent outcomes, arms or the gold fix. Raters list each behavioural requirement the new tests impose and classify it.
Research data: never used for training or submissions (oracle firewall: path contains research/).
"""
import json, os, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rows = {}
for f in ("data/rebench_full/tasks.jsonl", "data/rebench/tasks.jsonl"):
    for l in open(f):
        r = json.loads(l)
        rows[r["instance_id"]] = r
ids = []
for s in ("dev_sets/rb_n32.txt", "dev_sets/rb_h35.txt"):
    ids += [l.strip() for l in open(s) if l.strip() and l.strip() not in ids]
for t in ids:
    r = rows[t]
    tp = r["test_patch"]
    if len(tp) > 24000:
        tp = tp[:24000] + "\n[... test patch cut at 24k characters ...]"
    open(f"{OUT}/{t}.md", "w").write(
        f"# Task {t} ({r['repo']})\n\n## Issue text (all the agent is given)\n\n{r['problem_statement']}\n\n"
        f"## Test patch (what the hidden tests check)\n\n```diff\n{tp}\n```\n")
json.dump(ids, open(f"{OUT}/ids.json", "w"))
print(len(ids), "packets")
