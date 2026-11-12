# Pre-registration: v33 = v26b with a 30 s per-command timeout

Written 2026-10-20 before the runs.

## Finding that motivates it
swegemma runs `run_command` synchronously on the shared asyncio event loop: ADK only moves sync
tools to a thread pool when `RunConfig.tool_thread_pool_config` is set, and swegemma builds
`RunConfig(max_llm_calls=...)` without it (`agent_runner.py:801`, `functions.py:973`,
`function_tool.py:231-237`, `tools/execution.py:47`). One command that hangs (an issue about an
infinite loop reproduced without `timeout`, `Prompt.ask` on an exhausted stream) blocks every
concurrent task until `timeout_seconds` expires. v26b inherits the 300 s default, the whole task budget.

Today's 18 dev40 runs: 24 freeze events, 39 task-runs with >90 s of silence before the cap; v26b
8 in 4 runs. Proof case r2-v26b: rich_3480 `python3 -c "...t.append(t)..."` issued at 10.5 s,
returned at 299.9 s; rich_3471 and rich_3521 were silent for the same window. Command durations
(13,725 commands): median 0.04 s, p99.9 56 s, 16 over 30 s, all hangs.

## Change
`agent_v33/eval_config.yaml`: `timeout_seconds: 300 -> 30`. Nothing else. The README confirms
the scorer reads this key (`evaluation.timeout_seconds` -> `command_timeout_seconds`).

## Runs
v33 × 2 on dev40, same server mode and wheels (`data/sandbox-wheels-20261014`) as today's
v26b r1-r4, which are the control. Scored on dev33k (Kaggle-passable).

## Predictions
- Mechanism: task-runs with >90 s silence before the end: v26b 2.0/run -> v33 ≤ 0.5/run.
  At least one `TimeoutExceeded` observation across the two runs.
- rich_3518 resolves 2/2; rich_3480 ≥ 1/2 (v26b today 1/4, three runs lost to its own hang).
- Score on dev33k: v33 − v26b mean +0.5 to +1.0 per run. Too small for two runs to reach p ≤ 0.2.

## Decision rule
Adopt the 30 s timeout as the new base if the mechanism prediction holds and the dev33k mean is
not worse than v26b by more than 1.0 task. It removes a failure mode rather than adding a part.
If the mechanism holds but the score drops by more than 1.0, look for legitimate commands cut at 30 s.

## Prior attempt (found after writing the above, before any v33 result)
v18 (2026-10-17) set `timeout_seconds` 300 -> 60 on v16: hung commands -> 0, resolved 13, 13 vs v16
15, 16; not adopted. `AGENT_VERSIONS.md` later judged that gap to be inside the ±2.5 single-run noise.
The cross-task freeze was unknown then, so v18 was judged only on rescuing the hung task. v33 is a
re-test under rule 2 with the mechanism counted directly. The predictions above stand unchanged.

## Outcome (added after the runs)
- Result: dev40 16, 18 (v26b today 15, 18, 18, 18). dev33k: +0.00 per pass vs v26b, p = 0.63.
  Mechanism ✓: silent stalls 1, 0 (v26b 4, 1, 3, 1); the 30 s timeout fired 7 times, all on hangs
  (fastapi_14258 ×4, rich_3480, rich_3468 ×2). rich_3518 2/2 ✓. rich_3480 0/2 ✗: r1 found the real cause
  (`list(text._spans)` in `append`) but missed the same generator in sibling `append_text`, which the gold
  also fixes; the hidden test still loops. Score prediction (+0.5 to +1) ✗, inside noise.
- **Verdict: adopted as the new base** per the prereg rule (mechanism holds, not worse by > 1). It removes a
  failure mode that would also hit Kaggle if the scorer runs tasks concurrently in one process; no local gain.
