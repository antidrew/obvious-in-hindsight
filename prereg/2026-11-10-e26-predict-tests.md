# E26: the agent predicts the hidden tests before editing (2026-11-10, before any run)

**Score lever** (Kaggle candidate if it passes) and a paper data point.

## Observation
F1 (`kb/experiments.jsonl`): a stronger model's issue-only list of up to 8 predicted test behaviours raised agent_e18 by +4.5 on N32 (p 0.017) and +4.0 on H35 (p 0.07); pooled controls give +3.8 / +3.7. A 50-word issue-only statement (D4/D5) did nothing. F1g (Gemma's own list, job 100) is running.

## Change (one)
agent_e26 = agent_e18 plus one paragraph in "1. Contract": before any tool call, write a numbered list of up to 8 concrete behaviours the hidden tests most likely check (input → exact result; implied edge cases, defaults, related call paths), and satisfy every item. No extra tool call. Preflight passed (live task resolved).

## Assumptions
1. Gemma can produce a list like its foresight list (recall 38%, inferable 24%) inside the agent's own thinking/reply, and the agent uses its own list as it used Claude's.
2. The list costs output tokens, not tool calls; time per task rises by under 10%.

## Arms (31B, interleaved)
N32 and H35: agent_e18 x2, agent_e26 x2. rb64: e18 x1, e26 x1 (regression and level). About 9.5 h.

## Predictions
e26 − e18: N32 +0 to +3, H35 −1 to +3, rb64 −2 to +3; minutes per task +0-10%.

## Rules
1. **Kaggle candidate:** pooled (N32 + H35 + rb64) e26 − e18 ≥ +3 per pass with one-sided p ≤ 0.10, rb64 not below −2, and predicted Kaggle time within 10 h: build the zip, preflight, and queue it for draws.
2. **Null:** pooled ≤ +1: Gemma's own anticipation does not help inside the agent; with F1g this closes the self-prediction lever.
3. Mechanism check: fraction of e26 attempts whose first reply contains a numbered prediction list (target ≥ 80%; below 50% means the change did not take, read nothing).
