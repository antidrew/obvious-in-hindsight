#!/usr/bin/env python3
"""Foresight recall by requirement class (paper Table 2).
Inputs (research/reqclass/): rater_claude.json (ground-truth requirements with class I/R/C/A),
judge.json (per requirement n, verdict yes/partial/no for lists X and Y), judge_key.json (which writer is X / Y).
Recall: yes = 1, partial = 0.5. A task for which a writer produced no list is excluded for that writer.  CPU only, standard library.
    python3 scripts/foresight_recall.py [dir]"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/research/reqclass"
gt = json.load(open(f"{D}/rater_claude.json"))
judge = json.load(open(f"{D}/judge.json"))
key = json.load(open(f"{D}/judge_key.json"))
lists = {w: json.load(open(f"{D}/foresight_{w}.json")) for w in ("claude", "gemma")}
SCORE = {"yes": 1.0, "partial": 0.5, "no": 0.0}
NAMES = {"I": "Stated in the issue", "R": "Inferable, in hindsight", "C": "Defensible choice", "A": "Arbitrary"}

tot = {w: {} for w in ("claude", "gemma")}
for task, marks in judge.items():
    reqs = gt[task]
    for m in marks:
        cls = reqs[m["n"] - 1]["class"]
        for lab in ("X", "Y"):
            w = key[task][lab]
            if not lists[w].get(task):  # writer produced no list (Gemma: toqito_1538): task excluded for that writer
                continue
            s, n = tot[w].get(cls, (0.0, 0))
            tot[w][cls] = (s + SCORE[m[lab]], n + 1)

print(f"tasks judged: {len(judge)}; requirements: {sum(len(v) for v in judge.values())}")
print(f"{'Requirement kind':26s} {'n':>4s} {'Claude':>7s} {'Gemma':>7s}")
for cls in "IRCA":
    n = tot["claude"].get(cls, (0, 0))[1]
    r = [100 * tot[w][cls][0] / tot[w][cls][1] for w in ("claude", "gemma")]
    print(f"{NAMES[cls]:26s} {n:4d} {r[0]:6.0f}% {r[1]:6.0f}%")
allr = [100 * sum(s for s, _ in tot[w].values()) / sum(n for _, n in tot[w].values()) for w in ("claude", "gemma")]
print(f"{'All':26s} {'':4s} {allr[0]:6.0f}% {allr[1]:6.0f}%")
