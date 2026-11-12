#!/usr/bin/env python3
"""Paper statistics: every pre-registered contrast in one table, with task-bootstrap 95% CIs, one-sided within-task sign-flip p,
and Holm-adjusted p across the family. CPU only. Reads results/ood-<tag>-r<N>-<agent><suffix>/<task>/task_results.jsonl.
    python3 scripts/paper_stats.py [--md out.md]"""
import argparse, glob, json, os, random, re, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = lambda n: set(open(f"{ROOT}/dev_sets/{n}").read().split())
SETS = {"N32": S("rb_n32.txt"), "F51": S("rb_f51.txt"), "H35": S("rb_h36.txt") - {"airbrakesv2_118"}, "rb64": S("rb64.txt"), "OOD45": S("ood45.txt")}
SETS["H30"] = SETS["H35"] - S("rb_h36_e7train.txt")


def runs(tag, agent):
    out = {}
    for d in glob.glob(f"{ROOT}/results/ood-{tag}-r*-{agent}"):
        if not re.fullmatch(rf"ood-{re.escape(tag)}-r\d+-{re.escape(agent)}", os.path.basename(d)):
            continue
        for f in glob.glob(f"{d}/*/task_results.jsonl"):
            x = json.loads(open(f).readline())
            out.setdefault(x["instance_id"], []).append(int(bool(x["resolved"])))
    return out


def passes(tag, agent):
    return len([d for d in glob.glob(f"{ROOT}/results/ood-{tag}-r*-{agent}") if not d.endswith(".progress") and re.fullmatch(rf"ood-{re.escape(tag)}-r\d+-{re.escape(agent)}", os.path.basename(d))])


# (family, label, tag, treatment agent, control agent, set, prereg) ; family "oracle" = instruments, "lever" = score levers
TESTS = [
    ("claim1", "O3 tests vs control", "oracle20261103", "agent_e18-o3", "agent_e18", "N32", "2026-11-03-oracle-ladder"),
    ("claim1", "O2 location vs control", "oracle20261103", "agent_e18-o2", "agent_e18", "N32", "2026-11-03-oracle-ladder"),
    ("claim1", "O23 both vs control", "oracle20261103", "agent_e18-o23", "agent_e18", "N32", "2026-11-03-oracle-ladder"),
    ("claim1", "O6 gold fix vs control", "oracle20261103", "agent_e18-o6", "agent_e18", "N32", "2026-11-03-oracle-ladder"),
    ("claim1", "H36: O3 vs control", "h3620261105", "agent_e18-o3", "agent_e18", "H35", "2026-11-05-h36"),
    ("claim1", "H36: O2 vs control", "h3620261105", "agent_e18-o2", "agent_e18", "H35", "2026-11-05-h36"),
    ("claim1", "H36: O23 vs control", "h3620261105", "agent_e18-o23", "agent_e18", "H35", "2026-11-05-h36"),
    ("claim1", "H36: O6 vs control", "h3620261105", "agent_e18-o6", "agent_e18", "H35", "2026-11-05-h36"),
    ("claim2", "D1 names vs control", "dose20261105", "agent_e18-d1", "agent_e18", "N32", "2026-11-05-spec-dose"),
    ("claim2", "D2 one hunk vs control", "dose20261105", "agent_e18-d2", "agent_e18", "N32", "2026-11-05-spec-dose"),
    ("claim2", "D3 statement vs control", "dose20261105", "agent_e18-d3", "agent_e18", "N32", "2026-11-05-spec-dose"),
    ("claim2", "D3 vs D2", "dose20261105", "agent_e18-d3", "agent_e18-d2", "N32", "2026-11-05-spec-dose"),
    ("claim2", "D3s no names vs control", "dose20261106", "agent_e18-d3s", "agent_e18", "N32", "2026-11-06-d3s"),
    ("claim2", "D3 vs D3s", "dose20261106", "agent_e18-d3", "agent_e18-d3s", "N32", "2026-11-06-d3s"),
    ("claim2", "H36: D3 vs control", "h36dose20261106", "agent_e18-d3", "agent_e18", "H35", "2026-11-06-h36-dose"),
    ("claim2", "H36: D3s vs control", "h36dose20261106", "agent_e18-d3s", "agent_e18", "H35", "2026-11-06-h36-dose"),
    ("claim2", "H36: D3 vs D3s", "h36dose20261106", "agent_e18-d3", "agent_e18-d3s", "H35", "2026-11-06-h36-dose"),
    ("claim3", "D4 Claude issue-only vs control", "d4520261106", "agent_e18-d4", "agent_e18", "N32", "2026-11-06-d45"),
    ("claim3", "D5 Gemma issue-only vs control", "d4520261106", "agent_e18-d5", "agent_e18", "N32", "2026-11-06-d45"),
    ("claim3", "H36: D4 vs control", "h36d4520261106", "agent_e18-d4", "agent_e18", "H35", "2026-11-06-h36-d45"),
    ("claim3", "H36: D5 vs control", "h36d4520261106", "agent_e18-d5", "agent_e18", "H35", "2026-11-06-h36-d45"),
    ("claim3", "D3g Gemma with tests vs control", "d3g20261107", "agent_e18-d3g", "agent_e18", "N32", "2026-11-07-d3g"),
    ("claim3", "H36: D3g Gemma with tests vs control", "h36d3g20261108", "agent_e18-d3g", "agent_e18", "H35", "2026-11-08-h36-d3g"),
    ("claim3", "F1 Claude foresight list vs control", "f120261109", "agent_e18-f1", "agent_e18", "N32", "2026-11-09-f1-foresight-list"),
    ("claim3", "H36: F1 foresight list vs control", "f1h3620261109", "agent_e18-f1", "agent_e18", "H35", "2026-11-09-f1-foresight-list"),
    ("claim3", "F1g Gemma foresight list vs control", "f1g20261109", "agent_e18-f1g", "agent_e18", "N32", "2026-11-09-f1g"),
    ("claim3", "H36: F1g Gemma foresight list vs control", "f1gh3620261109", "agent_e18-f1g", "agent_e18", "H35", "2026-11-09-f1g"),
    ("claim3", "O3b Claude blind tests vs control (14 flips)", "oracle20261104o3b", "agent_e18-o3b", "agent_e18", None, "2026-11-04-spec-lora"),
    ("claim4", "E23 40 calls/10 min vs e18 (rb64)", "20261104e23rb", "agent_e23", "agent_e18", "rb64", "2026-11-04-e23-cap40"),
    ("claim4", "E23 vs e18 (OOD-45)", "20261104e23", "agent_e23", "agent_e18", "OOD45", "2026-11-04-e23-cap40"),
    ("claim4", "E7 RFT adapter vs e2b (H30 unseen)", "e7solve20261106", "agent_e7", "agent_e2b", "H30", "2026-11-06-e7-solve"),
    ("claim4", "E24 completeness vs e18 (H36)", "e24h3620261107", "agent_e24", "agent_e18", "H35", "2026-11-07-e24-complete"),
    ("claim4", "E24 vs e18 (rb64)", "e24rb20261107", "agent_e24", "agent_e18", "rb64", "2026-11-07-e24-complete"),
    ("family", "agent_e10: O3 tests vs control", "fam220261108", "agent_e10-o3", "agent_e10", "N32", "2026-11-08-family2"),
    ("family", "agent_e10: D3s statement vs control", "fam220261108", "agent_e10-d3s", "agent_e10", "N32", "2026-11-08-family2"),
    ("claim4", "E26 predict-the-tests vs e18 (N32)", "e26n20261110", "agent_e26", "agent_e18", "N32", "2026-11-10-e26-predict-tests"),
    ("claim4", "E26 vs e18 (H36)", "e26h20261110", "agent_e26", "agent_e18", "H35", "2026-11-10-e26-predict-tests"),
    ("claim4", "E26 vs e18 (rb64)", "e26rb20261110", "agent_e26", "agent_e18", "rb64", "2026-11-10-e26-predict-tests"),
    ("family", "Qwen3-Coder: O3 tests vs control", "qwen20261111", "agent_e18q-o3", "agent_e18q", "N32", "2026-11-11-family-qwen"),
    ("family", "Qwen3-Coder: D3 statement vs control", "qwen20261111", "agent_e18q-d3", "agent_e18q", "N32", "2026-11-11-family-qwen"),
    ("family", "Qwen3-Coder: D4 issue-only vs control", "qwen20261111", "agent_e18q-d4", "agent_e18q", "N32", "2026-11-11-family-qwen"),
    ("scale", "E4B: O3 tests vs control", "e4bladder20261107", "agent_e18-o3", "agent_e18", "N32", "2026-11-07-e4b-round1"),
    ("scale", "E4B: D3s statement vs control", "e4bladder20261107", "agent_e18-d3s", "agent_e18", "N32", "2026-11-07-e4b-round1"),
    ("scale", "E4B: e10 + O3 vs e10 control", "e4bconf20261108", "agent_e10-o3", "agent_e10", "N32", "2026-11-08-e4b-confound"),
    ("scale", "E4B: 50 calls/12 min vs 28/8 (rb64)", "e4bbudrb20261107", "agent_e10x", "agent_e10", "rb64", "2026-11-07-e4b-round1"),
    ("scale", "E4B: 50 calls/12 min vs 28/8 (OOD-45)", "e4bbud20261107", "agent_e10x", "agent_e10", "OOD45", "2026-11-07-e4b-round1"),
]


def flip(A, B, ts, n=20000, rng=random.Random(1)):
    d = [st.mean(A[t]) - st.mean(B[t]) for t in ts]
    obs = sum(d)
    return obs, (1 + sum(sum(x if rng.random() < .5 else -x for x in d) >= obs - 1e-12 for _ in range(n))) / (n + 1), d


def boot(d, n=5000, rng=random.Random(2)):
    s = sorted(sum(rng.choice(d) for _ in d) for _ in range(n))
    return s[int(.025 * n)], s[int(.975 * n)]


def main():
    a = argparse.ArgumentParser(); a.add_argument("--md"); a = a.parse_args()
    rows = []
    for fam, lab, tag, tr, ct, sname, pre in TESTS:
        A, B = runs(tag, tr), runs(tag, ct)
        ts = sorted(t for t in (SETS[sname] if sname else set(A) | set(B)) if A.get(t) and B.get(t))
        if not ts:
            rows.append((fam, lab, sname or "flips", None)); continue
        obs, p, d = flip(A, B, ts)
        lo, hi = boot(d)
        rows.append((fam, lab, sname or "flips", dict(n=len(ts), pa=passes(tag, tr), pb=passes(tag, ct), a=sum(st.mean(A[t]) for t in ts), b=sum(st.mean(B[t]) for t in ts), d=obs, lo=lo, hi=hi, p=p, pre=pre)))
    done = [r for r in rows if r[3]]
    order = sorted(range(len(done)), key=lambda i: done[i][3]["p"])
    m = len(done); run_max = 0
    for k, i in enumerate(order):  # Holm step-down, monotone
        run_max = max(run_max, min(1, (m - k) * done[i][3]["p"])); done[i][3]["holm"] = run_max
    out = ["| Claim | Contrast | Set (n) | Passes T/C | Treatment | Control | Δ per pass [95% CI] | p (one-sided) | Holm p | MDE |", "|---|---|---|---|---|---|---|---|---|---|"]
    for fam, lab, sname, r in rows:
        if not r:
            out.append(f"| {fam} | {lab} | {sname} | – | not run | | | | | |"); continue
        out.append(f"| {fam} | {lab} | {sname} ({r['n']}) | {r['pa']}/{r['pb']} | {r['a']:.1f} | {r['b']:.1f} | {r['d']:+.1f} [{r['lo']:+.1f}, {r['hi']:+.1f}] | {r['p']:.4f} | {r['holm']:.4f} | {1.27 * (r['hi'] - r['lo']) / 2:.1f} |")
    out.append(f"\nFamily of {m} contrasts; Holm controls family-wise error at 0.05. CIs: task bootstrap of per-task mean differences (5,000). p: within-task sign-flip (20,000). MDE: smallest true difference detected with 80% power at one-sided 0.05, from the CI width (1.27 × half-width).")
    txt = "\n".join(out)
    print(txt)
    if a.md:
        open(a.md, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
