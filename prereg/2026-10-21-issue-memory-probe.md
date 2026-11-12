# Pre-registration: does Gemma remember the linked GitHub issues?

Written 2026-10-21 before the probe.

Question: the agent cannot open "Fixes #NNNN" (network_mode none). Can the model recall the issue
from pretraining well enough to act as a hypothesis?

Method: for every rich task whose PR body links an issue (42 of 48), ask the served model (thinking on,
temperature 0.2) with only the PR title + body: "What did issue #N in Textualize/rich report? Describe
the bug/expected behaviour concretely, or say UNKNOWN." Controls: the same question for 10 issue
numbers shifted by +7 (real numbers, wrong issue) to measure confident confabulation.
Grading (by me, against the gold patch + test only): CORRECT (the described behaviour matches what
the gold/test change), PARTIAL (right area, wrong specifics), WRONG, UNKNOWN.

Predictions: CORRECT ≤ 15% of tasks; confabulation (non-UNKNOWN answers on shifted controls) ≥ 70%.
If CORRECT ≥ 30% with control confabulation ≤ 30%, memory is worth an agent step. Otherwise drop it.
