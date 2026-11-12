# Pre-registration E4: remove the graph tools (E4a); temperature 0.2 -> 0.6 (E4b)

Written 2026-10-23 18:10 UTC, before any E4 run. Base `agent_e2b`; control = e2b's two OOD-45 passes from E3
(same server, same day; tag `20261023e4` symlinks them). 2 passes per new arm, OOD-45, 3 processes.

## Why
- Rule 5 (ablate toward simpler): E2a and E3 both added parts and both lost. **E4a** removes the three graph
  tools and the prompt line forbidding them (the line exists because they "return nothing useful"; forum
  746250 found no benefit). Their schemas cost context on every call and they can still be called.
- **E4b**: forum 746250 (129 tasks, one run each) found temperature 0.4 and 1.0 at least as good as 0.2.
  Diversity across steps may help the coin-flip tasks; it may also add wrong patches.

## Predictions
- E4a - e2b: +0.0 (plausible -1 to +1); graph-tool calls 0 (from current count); median model time per call
  falls a little. A tie keeps the simpler agent.
- E4b - e2b: +0.5 (plausible -1.5 to +1.5); per-task variance up (more 1/2 tasks).
## Decision
- E4a is adopted if it is not worse than -1.0 (simpler wins ties).
- E4b is adopted only with gain >= +1.0 and p <= 0.2; otherwise temperature stays 0.2.
- Note (before results): e2b made 0 graph-tool calls in its 90 E3 OOD attempts, so E4a tests only the cost of the unused schemas in context.
- Outcome check (before verdict): both arms -2.5..-3.0 with empties 6-7 vs 1/90 for the non-interleaved morning control. Running one fresh e2b pass now (tag 20261023e4c) to separate drift from effect.

## Outcome (2026-10-23 22:40 UTC)
- Fresh interleaving check: e2b 38/45 now (morning control 40, 41). Against all 3 control passes:
  **E4a (no graph tools) -2.17/pass, p 0.95; E4b (temperature 0.6) -1.67/pass, p 0.91.** Arm passes 39, 36 and
  39, 37; e2b's five OOD passes so far 40, 39, 40, 41, 38 (mean 39.6, SD 1.1).
- Both rejected by the registered rules (E4a needed >= -1.0; E4b needed >= +1.0). Empties rose in both arms
  (7, 6 vs 1-3/90): all ended at the 28-call cap with no surviving edit, i.e. over-reading, not infra.
- Lesson: never reuse a non-interleaved control again. With pass SD ~1.1, 2 passes per arm resolve only about
  ±2 tasks on OOD-45.
