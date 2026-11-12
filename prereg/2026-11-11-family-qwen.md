# Second model family: Qwen3-Coder-30B-A3B on the information arms (2026-11-11, before any run)

**Instrument; adopts nothing; never a submission** (competition models are Gemma only). Answers the limitation "one model family" (`paper/review-2026-11-08.md`).

## Setup
Qwen3-Coder-30B-A3B (AWQ 4-bit, Apache-2.0, `teacher/qwen3-coder-30b-a3b-awq`), served under the Gemma name with the `qwen3_coder` tool parser (`scripts/serve_teacher.sh`). Agent `agent_e18q` = agent_e18 with Qwen's recommended sampling (temperature 0.7, top_p 0.8, top_k 20) and no thinking config (the model has no thinking mode); prompt, tools and budget unchanged. Earlier probe (10-19): dev40 16/40, 0/60 empty patches.

## Arms (N32, interleaved, 2 passes each)
control; O3 full test patch; D3 statement from the tests (≤ 50 words); D4 statement from the issue alone. Same data sets as the Gemma arms (`research/oracle/{o3,d3,d4}`). About 4-5 h.

## Predictions (N32 per pass)
control 0-3; O3 6-16; D3 5-14; D4 0-4.

## Rules
1. **Generalises across model families:** O3 − control ≥ +4 and D3 − control ≥ +4 (p ≤ 0.05 each), and D4 − control ≤ +2: the paper states the information result for two model families.
2. **Family-specific:** O3 or D3 gain ≤ +2: the paper restricts the claim to Gemma and reports Qwen's numbers.
3. Otherwise: numbers only.

## Amendment (2026-11-11 10:15 PM PST, before any valid data)
Job 104 produced no data: every model call was rejected because the harness sends a thinking budget by default and the Qwen server has no reasoning config. agent_e18q now sets `thinking_config: {thinking_budget: 0}`, as the October Qwen agent did. Results of 104 deleted; job 105 reruns the same design unchanged.
