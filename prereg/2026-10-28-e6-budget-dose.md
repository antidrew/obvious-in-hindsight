# E6: tool-call budget dose-response (pub22 at caps 20 / 28 / 44), OOD-45 × 2

Written 2026-10-28, before any E6 run. Purpose: firm up paper claim C3 (more budget → churn) with a
dose-response instead of one two-arm comparison (E2a: cap 44 −2.0/45, wrong 9 → 14/90).

## Arms (one change each: `max_tool_calls` and the matching number in the system prompt)
- `agent_cap20`: pub22, cap 20
- `agent_pub22`: cap 28 (the public bundle)
- `agent_e2a`: pub22, cap 44
Run interleaved on OOD-45, 2 passes, PAR 3, graph-mode vLLM (`scripts/run_e6.sh`). Earlier pub22 / e2a
passes (E1, E2) may be pooled as a secondary analysis only.

## Hypothesis and predictions
H: the cap trades empty patches (budget runs out before the first edit) against wrong patches (churn
after a good first edit); the solve rate peaks near 28.
1. Empty patches fall monotonically with the cap (20 > 28 > 44).
2. Wrong patches rise monotonically with the cap (20 < 28 < 44).
3. Solves: cap20 ≤ pub22 − 1.0/pass and e2a ≤ pub22 − 1.0/pass (inverted U).
H is supported if 1 and 2 hold; 3 is the outcome claim. If wrong patches do not rise from 28 to 44, C3
is weakened to "extra budget does not help".

## Analysis
`compare_ood.py 20261028e6 agent_pub22 agent_cap20` and `... agent_pub22 agent_e2a`; empty/wrong counts
from the same output; mean duration per arm.

## Outcome (2026-10-28, written after the runs)
Solved/pass: cap20 36.5, cap28 40.0, cap44 39.5. Empty per 90: 9, 4, 0 (prediction 1 ✓). Wrong per 90: 8, 6, 11
(prediction 2 ✗ for 20→28, ✓ for 28→44, replicating E2a's 9 → 14). Prediction 3: cap20 −3.5 ✓, cap44 −0.5 ✗ (needed ≤ −1).
Mean time 159 / 180 / 199 s. H partly supported: the budget trades empties for wrong patches above 28; below 28 the
cost is empties. Cap 28 stays.
