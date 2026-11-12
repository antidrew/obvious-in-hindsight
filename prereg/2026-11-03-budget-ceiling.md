# R1/R2: what would a much larger budget give? (prereg 2026-11-03, before any run)

**Instrument, adopts nothing:** 100 calls and 30 minutes cannot fit 12 h. It bounds the lever.

## Observation
`reports/rethink-2026-11-02/first-principles.md` §4: every cap test ran on OOD-45, which is near its ceiling, or under compaction, so 28 calls is unproven on hard tasks. `reports/rethink-2026-11-02/ceilings.md`: v33 at 80 calls 24 vs pub22 23; attempts at 28+ calls solve 0.239 vs 0.29 expected from their tasks. `o3-contract.md`: of 21 N32 tasks still failing with the gold tests in hand, 7 exhaust the budget and 8 edit late or never, so budget may matter once the contract is known, but that is a different question. `t1-postmortem.md`: E19 is confounded, and R2 replaces E19r.

## Hypotheses
R1: on F51, budget is not the wall. R2: without compaction on top of R1, tool history is still not the wall (T1 as an outcome theory).

## Assumptions
1. Prompt states the new limits; only the numbers and `eval_config.yaml` differ from agent_e18. agent_r2 = agent_r1 byte for byte, with `NO_COMPACTION=1` in the runner.
2. Time caps in local seconds are generous enough that calls bind first. 3. R2 can overflow 32k: prompt + max output above 32,768 is a 400; the tree is still graded. Report the overflow rate; over 30% means no verdict on T1.

## Arms
agent_e18 (control under this tag), agent_r1, agent_r2 on F51, one pass each. About 1, 2.6, 2.6 GPU h. `queue/pending/60-budget.sh`.

## Predictions (ceilings.md)
| Arm | N32 (control ~1) | M19 (control ~12) |
|---|---|---|
| R1 | 0.5-2.5 | 11-14 |
| R2 | R1 + 0-3 | same |

## Decision
R1 ≥ +5 total over control: budget is a lever, so a thrift program and a cap arm near 40 become worth building. Otherwise this closes. Surprise at ≥ +8. Between +3 and +5, one more pass.
R2 − R1 ≥ +3 with overflow ≤ 30%: T1 supported as an outcome theory, so a better compaction escape is worth building. ≤ +1 with mechanism held: T1 refuted as an outcome theory. Otherwise, one more pass.
Falsifier: wrong patches and churn rise with calls and solves fall (as E2a), which would close budget harder than a null.
