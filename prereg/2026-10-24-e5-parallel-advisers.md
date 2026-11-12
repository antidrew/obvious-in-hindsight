# Pre-registration E5: parallel tool-less fix advisers before the first edit

Written 2026-10-24 (UTC) before any scored run of the final design (smoke runs on 4 OOD tasks only checked
the mechanics).

## Why (and what was dropped first)
The planned "best-of-2 attempts selected by the agent's own check script" was dropped before any GPU run,
on two precursor measurements from existing traces (no new runs):
1. **No time for it.** e2b's mean is 207 s per task (p90 355 s, 587 OOD/RB attempts) = 6.9 h of the 12 h
   for 120 tasks before Kaggle slowdown and sandbox setup; a full second attempt does not fit.
2. **The selection signal is uninformative.** Last check-script verdict vs resolved: RB PASS 48% (n 29),
   FAIL 50% (n 10), no check 46% (n 71); OOD PASS 84%, FAIL 67%, no check 79%.

Also measured: empty patches (RB 14%, OOD ~5%) are attempts whose first edit came at call 29, after all 28
calls went to exploration, although the prompt says "edit by call 12" and the harness warns at 7 left.
Fixing them is worth little: v33 (80 calls) cuts RB empties 18 → 5 but resolves only +2/128.

The free resource: Kaggle runs tasks sequentially, so the vLLM server serves one stream; parallel LLM calls
inside a task cost little wall time (local per-call 7.8-8.4 s at 3 streams vs Kaggle 8.7 s sequential).
A first design with two parallel read-only *investigators* (`agent_e5inv`) failed its smoke test:
investigator B ignored "at most 6 calls" and an explicit `Call k of 5` counter (13, 21, 11, 14 calls; never
wrote the counter), so tool-using sub-agents cannot be bounded declaratively with this model.

## Design (`agent_e5` = e2b + one change)
After locating the code and before the first edit, the editor calls `consult` once (an `agent_tool` of a
`ParallelAgent`). Its request carries the verbatim code to change and the planned change. Two **tool-less**
advisers (one LLM call each, thinking 3072, temperature 0.6) answer in parallel: A checks the plan against
every literal in the issue; B predicts what the maintainers' regression test will assert. Their notes reach
the editor through `output_key` state templated into its instruction (`{advice_a?}`, `{advice_b?}`).
Call cap 28 → 29 (the consult call itself); time cap unchanged (8 min). Target: the dominant failure on
hard tasks, a wrong or incomplete fix at the right place.

Smoke (4 OOD tasks): consult called exactly once, right before the first edit, 4/4; costs 13-41 s.
Known risk seen in the smoke: advisers agree with the plan even when it misses a literal (capitalised
message), i.e. sycophancy.

## Runs
Tag `20261024e5` (OOD-45) and `20261024e5rb` (rb64, `DATA=data/rebench`), 2 passes, order per pass:
e2b OOD, e5 OOD, e2b RB, e5 RB (control interleaved). 3 processes. ~9.6 h.

## Predictions and decision
- Primary: pooled per-pass difference e5 − e2b over OOD-45 + rb64 (109 tasks), one-sided within-task
  permutation test. **Prediction: +2 tasks per pass pooled (+0.5 OOD, +1.5 RB).**
- Adopt e5 as the new base if pooled diff >= +1.5/pass with p <= 0.15 and OOD diff >= -1 (no regression on
  the instrument that ranks like Kaggle). Reject if pooled diff <= 0. Otherwise "unresolved": run 2 more
  passes before deciding.
- Secondary: mean duration (Kaggle-time risk; reject regardless if e5 mean > 260 s), share of attempts
  where advisers say DISAGREE or MISSED non-empty, and the solve rate in those vs AGREE attempts.

## Outcome (2026-10-28, written after the runs)
OOD +1.0/pass (37.5 → 38.5, p = 0.40); rb64 −3.0 (24.5 → 21.5, 2 passes); pooled −2.0 → **reject** by the rule.
Mean time OOD 210 → 259 s, RB 258 → 312 s (limit 260). OOD wrong 10 → 4, empty 5 → 9 of 90; RB empty 25 → 31 of 128.
