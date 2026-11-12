# Obvious in Hindsight

Code, pre-registrations and per-attempt results for the Kaggle Gemma 4 Developer Agent paper-track Writeup
**"Obvious in Hindsight: What a Small Quantized Coding Agent Is Missing on Hard Repair Tasks"**
(`paper/writeup.md`).

**The short version.** On hard SWE-bench-style repair tasks, Gemma 4 31B (4-bit) lacks the intended *behaviour*, not the
*location* of the fix: the failing tests add +11.5 of 32 tasks and a 50-word statement written from them +13.5, while
the exact location adds +1.0. That behaviour is not recoverable from the issue, and an issue-only foresight test shows
why: most hidden-test requirements look inferable in hindsight, but writers anticipate only 46% (Claude) and 24%
(Gemma) of them.

## What is here

| Path | Contents |
|---|---|
| `paper/` | The Writeup, Figure 1, and the statistics table (`stats-table.md`) |
| `prereg/` | All 53 pre-registrations, committed before each run, including the ones whose predictions failed |
| `results/` | 5,775 per-attempt result rows (`task_results.jsonl`: task, resolved, patch size, duration, tool calls). No patches or traces. |
| `data/experiments.jsonl` | One row per experiment: arms, means, delta, p, prediction, verdict, pre-registration |
| `data/foresight/` | The foresight test's answer key and results for 62 hard tasks: 236 hidden-test requirements with their class (`rater_claude.json`; a second rater, `rater_gemma.json`), the issue-only prediction lists of two writers (`foresight_claude.json`, `foresight_gemma.json`), and the blind judge's verdicts (`judge.json`, writer order in `judge_key.json`) |
| `dev_sets/` | Task-id lists for rb64, N32, F51, H36 and OOD-45 |
| `agents/` | Agent configurations (declarative ADK YAML + prompts): `agent_e18` (main agent), `agent_e10` (test-first), `agent_e26` (predicts the tests first), `agent_e23` (40 calls), `agent_e24` (completeness prompt) |
| `scripts/` | Statistics, figure, task conversion and foresight-test scripts (below) |

## Reproduce the numbers

```bash
python3 scripts/paper_stats.py --md /tmp/stats.md   # every contrast: Δ, 95% task-bootstrap CI, one-sided sign-flip p, Holm p, MDE
diff paper/stats-table.md /tmp/stats.md             # identical except for the not-run Qwen rows
python3 scripts/make_figures.py                     # Figure 1 (needs matplotlib)
```

The statistics are CPU-only and use the Python standard library.

## A cheap foresight test for any benchmark

The test asks how much of a benchmark grades behaviour its issues leave out:

1. List the requirements each task's hidden tests impose, and classify each as stated in the issue, inferable from the
   issue and repository, a defensible choice, or arbitrary (`scripts/build_req_packets.py`, `scripts/rate_reqs_gemma.py`).
2. Have writers who see **only the issue** predict up to 8 behaviours the tests will check (`scripts/foresight_gemma.py`
   for a local OpenAI-compatible server).
3. Have a blind judge mark which requirements each prediction list anticipated, and report recall by requirement kind
   (`python3 scripts/foresight_recall.py data/foresight` reproduces the paper's Table 2 from our data).

To score a new writer against our answer key, have it predict behaviours for the 62 tasks (ids in `data/foresight/judge_key.json`;
issues come from SWE-rebench) and judge its list against `rater_claude.json`.

Design, predictions and decision rules: `prereg/2026-11-09-reqclass2-foresight.md`.

## Rebuilding the tasks

`scripts/build_rebench.py` converts SWE-rebench tasks (CC-BY-4.0) into the competition's task format with
date-pinned wheels and checks that the gold patch passes and the empty patch fails. Running the agents needs the
competition harness (`swegemma`, not redistributed here) and the model `gemma-4-31b-it-qat-w4a16-ct`.

## Not included, and why

- The competition harness code (not ours to redistribute).
- SWE-rebench issues, patches and tests (rebuild them with the script above).
- The test-derived statements given to the agent in the information arms; these are available from the authors on request.

## Licence

Apache 2.0 (`LICENSE`); third-party notes in `NOTICE`.
