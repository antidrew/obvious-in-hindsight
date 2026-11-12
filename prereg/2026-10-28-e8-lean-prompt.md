# E8: lean system prompt (1,175 → ~190 words), same tools and config as agent_e2b

Written 2026-10-28, before any run. Motivation: harness studies (arXiv 2610.04433, "harness tax": Claude Code vs
OpenCode vs mini-swe-agent; a 7-harness Terminal-Bench comparison where the 64-character-prompt bash agent did
best) find long system prompts and tool schemas raise cost without raising accuracy, and that harness changes
flip outcomes no more than reruns do. Our own record agrees for structure (E1 chain −6, E3, E5 null) but we never
shortened the prompt itself. Under Kaggle's 12 h and our 28-call cap, per-call cost is a real resource.

One change: `prompts/system.md` replaced by a ~190-word version keeping the hard limits (budget, edit by call 12,
no test edits, no full suite), the search/edit/claim-check/submit steps, and nothing else. Tools, sampling,
thinking and budgets unchanged.

H: the long prompt's extra rules are weakly followed (kb fact 4) and buy nothing.
Predictions: (1) e8 − e2b ≥ −1.0/pass pooled over OOD-45 + rb64 (non-inferior); (2) mean time per task lower
than e2b; (3) prompt tokens of the first call fall by ≥ 1,200.
Adopt (as the new simpler base) if 1 and 2 hold; a gain ≥ +1.5 (p ≤ 0.15) would be a positive result.
Reject if pooled ≤ −1.5.
Design: interleaved e2b / e8, OOD-45 × 2 and rb64 × 1 (`queue/pending/20-e8.sh`).

## Outcome (2026-10-28, written after the runs)
OOD −0.5/pass (38.0 → 37.5, 2 passes); rb64 −6.0 (24 → 18, 1 pass; wrong 28 → 37 of 64). Pooled far below −1.5 →
**reject**. Faster (OOD 189 → 178 s, RB 260 → 221 s; prediction 2 ✓) but prediction 1 ✗. Unlike the strong-model
harness studies, the long procedural prompt earns its tokens on hard tasks for this model.
