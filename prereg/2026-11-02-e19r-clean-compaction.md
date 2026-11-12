# E19r: compaction off, nothing else changed (prereg 2026-11-02, before any E19r run)

## Observation
`reports/research-2026-11-02/t1-postmortem.md`: E19 is confounded. Snapshot (rb r1, 46 of rb r2, OOD r1): e19 − control rb +2 (p 0.37), OOD −4. Mechanism held (compactions 0; amnesia re-reads 1.45 → 0.20), but that frees only ~1.2 calls, and 3.27 same-file re-reads come before compaction. Restarts cost: of 54 pre-submit stops 12 were overflow and 32 leaked tool calls; 28 of 42 restarted attempts had no edit to keep; 11 of 14 empties follow a stop. Against the confound: without a pre-submit restart e19 is 33 vs 32.0 expected (rb), 29 vs 29.0 (OOD).

## Hypothesis
Compaction costs solves by erasing tool history (T1). E19 could not show it because its dispatcher and restarts added their own losses.

## Assumptions
1. Compaction off in the runner changes only compaction. The agent is byte-identical to the control (`agent_e19r` = copy of `agent_idris24`, for run naming only).
2. A root overflow ends the attempt and its tree is still graded (`agent_runner.py:1054`); checked on the first pass, from logs. 3. Instrument only: **this cannot be submitted**, since a submission cannot set the field (harness-capabilities.md). A positive result justifies building a better compaction escape, not this file.

## Arms
agent_idris24 (compaction as on the starter) vs agent_e19r (`NO_COMPACTION=1`). rb64 × 4 + OOD-45 × 2, interleaved, graph mode.

## Predictions
Mechanism: compactions 0; within-session re-reads ≤ 0.3 per attempt; pre-submit stops ≤ 7 per 1,000 calls; overflow ≤ 15%. T1 as registered: rb +3 to +5, OOD 0 to +2. Reviewer's inference: rb +1 to +2, OOD −1 to +1.

## Decision
T1 supported at pooled ≥ +3 per pass, one-sided p ≤ 0.15, mechanism held. **T1 refuted as an outcome theory at pooled ≤ +1, mechanism held.** Between: add passes. If overflow > 30%, the arm fails assumption 2: report, no verdict.
Falsifier for "E19 was confounded": empties stay ≥ 12 per 155, or stops stay near 17 per 1,000 without the solver framing.
