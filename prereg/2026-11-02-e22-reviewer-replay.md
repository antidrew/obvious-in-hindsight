# E22: reviewer replay gate (prereg 2026-11-02, before any request is sent)

From `reports/research-2026-11-02/judge2.md`, experiment 2. No agent runs, no Kaggle time. It asks whether a same-model reviewer can tell a wrong patch from a right one at all, before we pay for a live arm.

## Observation
- A same-model reviewer has not separated wrong from right so far. E3, live AgentTool reviewer: DEFECT on 4/33 reviewed wrong rb64 patches (12%); resolved after ACCEPT 28/57, after DEFECT 2/6; OOD: 5/7 DEFECTs hit correct patches (judge2.md item 3). E3 lost −1.5 OOD, −2.0 RB (`kb/log.md`, 2026-10-23).
- But E3's reviewer did not get the issue: `agent_tool` hands it the root's summary (`kb/harness.md`, "agent_tool context"). `{problem_description}` is the fix. The issue alone did not rescue it, though: v21's `checker` had it and passed 5/7 wrong fixes (dev40, small; `kb/history.md:33`, judge2.md item 4). The open case is only a post-edit judge with the verbatim issue.
- The same wrong patch recurs: identical changed lines in 24 attempts, loguru 16, twine 13, moto 12, actualpy 11 (judge2.md item 2). A same-model reviewer must reject what the model finds most natural to write.
- Break-even at optimistic assumed values (recall 0.5, conversion 0.10, false reject 0.15, damage 0.3) is +0.3 tasks per pass, before ~0.5 h of Kaggle time (judge2.md, "Converting the 16"). So a live arm is worth running only if the reviewer is clearly better than E3.
- Data for this test (`scripts/reviewer_replay.py --dry-run`, 2026-11-02). Pool of 24 pinned passes (e2b ×10, e10 ×10, idris24 ×3, e18 ×1), 1,536 attempts:
  - 32 mixed tasks by the plain definition; 26 have a usable pair. The other 6 have no finished non-empty wrong patch.
  - Labels look stable: no changed-line set got both verdicts in any mixed task. rb gold passes 64/64, empty 0/64 (`results/rb-gold-20261022`, `results/rb-empty-20261022`). `hints_text` is empty for all 64.
  - All 697 context and removed lines of the 52 selected diffs match the base snapshots.
  - 4 of the 26 wrong patches edit no existing source file (they add a stray file such as `repro.py`). No solved patch does this.
  - Only 7/26 pairs come from one agent: solved patches lean e2b (13/26), wrong patches e10 and idris24 (19/26).

## Hypothesis
Given the verbatim issue, the diff and the enclosing code, with no tools and no author's summary, a same-model reviewer's judgement carries real signal about patch correctness. E3's 12% was then mostly due to its context (a summary, no issue).

Judge2's expectation, which I adopt as the prediction, is the opposite: verification gives signal, not new information, and a model that wrote a wrong patch will accept it.

## Assumptions
1. The stored verdict is the true label. Support above. 3 selected wrong patches failed at collection (`test_exit_code` 2), with no assertion reached.
2. Finished patches are what a live reviewer would see. Attempts with a harness `error` (timeout, call or turn budget) are excluded for both classes: the agent never declared them finished, and half-done edits would be cheap rejections.
3. Enclosing code is at least as good as what a live reviewer would read for itself. **Limit:** the replay cannot execute anything and a live reviewer with `run_command` can, so "replay gets better context" holds for reading, not for running code.
4. Mixed tasks stand in for the failures we care about. **Limit:** 11 of 15 matched tasks in the failure class of 16 were never solved (judge2.md item 1), so they are outside this sample. Recall here may not carry over, and rejecting a wrong patch does not produce a right one on those tasks.
5. Two reviews of one patch are not independent. The patch is the unit for the p value (below).
6. The reviewer's sampling and thinking match the agent's. The dry run compares our settings with the logged harness request of agent_idris24 (`results/sft-20261102e18rb-r1-agent_idris24`): they match.

## Arm
One arm, 26 tasks × 2 patches × 2 repeats = **104 tool-less requests**, concurrency 3, in shuffled order.
- **Selection:** per task, one solved and one wrong patch, each uniform over eligible attempts (`random.Random("e22:<task>")`), so a recurring wrong patch keeps its real weight. Eligible: non-empty, `error` is null, changed lines not seen with the opposite verdict in that task. Frozen in `results/e22-replay/manifest.jsonl` (sha256 starts `3219f219f4cb4791`) and `prompts.jsonl` (`623339eb56849c4f`). The real run sends these files as they are.
- **Request:** system line + `<issue>` (verbatim `problem_statement`) + `<patch>` (stored diff) + `<code_before_patch>` (enclosing function of each changed line, from the base snapshot; ±15 lines when outside a function; functions over 200 lines shown ±40 around the change; cap 10,000 tokens, not reached). Prompt template sha256 starts `4ec4953fc217ac30`. Median prompt 1,491 tokens, max 3,732.
- **Sampling, as agent_idris24:** temperature 1.0, top_p 0.95, top_k 64, `max_completion_tokens` 8192, `enable_thinking` true, `thinking_token_budget` 4096. No tools.
- **Nothing the live agent could not see:** gold, tests and labels are not in the prompt path. The leak audit on finished prompts found 0 hidden-test names or test lines outside the issue.
- **Reply:** must end `REASON: ...` then a strict final line, `VERDICT: ACCEPT` or `VERDICT: REJECT`. A reply whose last non-empty line is not exactly that (bold included) counts as not rejected, which is what it would do live.

## Prediction (written before the run)
| Counter | E3 (live, summary only) | Prediction |
|---|---|---|
| P(reject\|wrong) | 12% | 20-35% |
| P(reject\|right) | 5/7 of OOD DEFECTs hit correct patches | 10-25% |
| within-task p | - | > 0.05 more likely than not |
| rejections naming the assertion | - | < 50% |
| reviews with no verdict line | - | < 5% |
| output tokens per review | - | ~2,000 (not measured for this prompt) |

**P(the rule passes) ≈ 15%** (judge2.md).
GPU time: ~23 min at 2,000 output tokens per review; 11 min at 1,000, 50 min if each review uses the whole thinking budget, 92 min if every call hits 8192. Calibrated on 51 output tok/s per stream at concurrency 3 (350 long calls, E18 r1 idris24). Judge2 estimated ~1 h.

## Decision rule
**Go live only if P(reject|wrong) ≥ 40%, P(reject|right) ≤ 15%, within-task p ≤ 0.05, and at least half of rejections name what the failing test asserts, by a blind label.** All four, otherwise no live arm.

How each number is computed (`--analyze`):
- **Rates:** mean over the 26 tasks of each patch's rejection share. A reply with no verdict counts as not rejected.
- **p:** one-sided, within task, 20,000 draws (exact at ≤ 20 non-zero tasks). A permutation swaps the solved/wrong labels of a task's two patches. It does not shuffle repeats as `compare_ood.py` does with attempts, because two reviews of one patch would then pass as independent and p would come out too small.
- **Blind label:** `--analyze` exports `blind_reasons.jsonl` (opaque id, task, reason), covering every rejection of both classes, in hash order, plus `blind_references.jsonl` (issue, FAIL_TO_PASS, `test_patch`), the same for both patches of a task. A reader who has not seen `blind_key.jsonl` or the rates writes `yes` or `no` to `blind_labels.jsonl`. `yes`: the reason states the behaviour (function, input or expected value) that an assertion in the reference tests checks. `no`: generic ("may not handle edge cases"), a different behaviour, or an empty reason. Failing-test logs are not shown, since a solved patch has none and that would reveal the class.
- **Denominator of the fourth gate:** all rejections, as the rule says. So false rejections count against it. The share among wrong-patch rejections is reported too, and does not enter the rule.

Validity: all 104 replies must be in, else INCOMPLETE. More than 10% of replies without a verdict line makes the run VOID: an instrument failure, not a result. Fix the format instruction and re-run with a new prereg addendum.

Reported with the result, outside the rule:
- The gates again on tasks where both patches edit existing source (22 of 26). If this disagrees with the full set, the result is stated as depending on patches that a simple diff check could catch.
- Rejection rates by source agent per class, since the classes differ in agent mix (Observation).
- Agreement between repeats, and patch size with and without rejection.
- 90% bootstrap intervals over tasks.

Resolution of the rule on 26 tasks (simulated with correlated repeats, not a measurement): a reviewer truly at 60/10 passes the three measured gates 82% of the time, 50/10 75%, exactly at 40/15 26%, a null 25/25 0.1%, E3-like 12/15 0%. So the rule rarely passes a useless reviewer, and it would often miss one that only just meets the thresholds. That is accepted: the live arm's value at the thresholds is already marginal.

## If it passes
Live arm, one change: idris24 + AgentTool `reviewer` (`run_command` only, verbatim `{problem_description}`), once before submit at ≤ 22 calls, no cap change. Scored by judge2's rule R: adopt at pooled ≥ +2.0, p ≤ 0.15, OOD ≥ −1, ≤ 11 h; reject at ≤ 0. It needs its own prereg, its own preflight and a runtime prediction (~+0.5 h Kaggle).

## What would falsify the theory
**A failed gate ends post-edit review for this project**, because the replay gives the reviewer better reading context than a live run would (issue, diff and enclosing code, free of budget and compaction). The hypothesis is also dead if rejection rates do not differ between classes. Then a same-model judge adds no information, and E3's context was not the cause.

One thing this cannot rule out (assumption 3): a reviewer that runs code. It would be a different experiment, closer to "variant-input check" (judge2.md experiment 4), not a re-run of this one.

If the rule passes, judge2's view that the model cannot judge its own modal answer is wrong for mixed tasks, and the next question is conversion: does a rejection lead to a right patch? The replay does not measure that; only the live arm does.
