# E15: parallel candidate fixes + executable selection (paradigm P1, kb/design-2026-10-30.md)

Written 2026-10-30, before any run. Strategies: parallel exploration + formal verification + iterative prompting
(the OpenAI "First Proof?" loop adapted to a 28-call / 5-8-minute budget).

## Design (agent_e15 = agent_e10 + steps 2b/2c)
2b: the check script is saved to /tmp/check.py and must print FAIL before any edit (as E10, but saved so it can be
rerun cheaply). 2c: one `propose` call (ParallelAgent: 3 tool-less proposers, temperature 1.0 / top_k 64, thinking 2048;
views: literal reading, maintainers' tests + sibling sites, different approach) returns 3 candidate fixes as exact
OLD/NEW blocks; then ONE run_command selector applies the root's own fix R and A, B, C in turn, runs /tmp/check.py with
a fresh bytecode cache, keeps the first all-PASS candidate applied, else restores. Selector unit-tested offline
(no-match, fail, pass-and-apply, none-pass-restore; stale-.pyc bug found and fixed).

## Hypothesis and assumptions
H: per-attempt success is a coin flip on many tasks (22/178 pool tasks mixed; 16/64 RB mixed), and E10's check selects
(RB 55% vs 17%), so trying 4 candidate fixes against the check before committing raises resolution on hard tasks.
Assumptions: (a) proposers given only the root's code excerpt produce applicable, diverse fixes (OLD matches);
(b) the check's PASS is specific enough that a passing candidate is usually right; (c) the extra ~2 calls and one
parallel latency (~30-50 s) fit the budget; (d) the model transcribes 4 candidates into the selector correctly.

## Smoke (queue job 55, 8 RB tasks + 4 OOD tasks, 1 pass) — mechanics only, no score claims
Pass if: `propose` called in ≥ 70% of attempts; selector run in ≥ 60%; ≥ 1 candidate NOMATCH-free in ≥ 70% of
selector runs; mean time ≤ e10 + 60 s. If the smoke fails, fix the mechanics before the full run (job 68 is removed).

## Predictions for the full run (job 68: e10 vs e15, OOD-45 × 2 + rb64 × 2, interleaved)
1. Mechanism: in selector runs, some candidate other than R is APPLIED in ≥ 25%; P(resolved | APPLIED) ≥ 55% on RB.
2. Outcome: e15 − e10 ≥ +2.0/pass on rb64 and pooled ≥ +2.5 (OOD ≥ −1), one-sided p ≤ 0.15.
3. Time: mean ≤ e10 + 40 s (Kaggle risk); if above, E15 needs the 5-min cap variant before any upload.
Adopt if 2 and 3; reject if pooled ≤ 0; otherwise 2 more passes.

## Outcome (2026-10-30): rejected on mechanics; full run (68) not started
Smoke 1 (55) invalid: harness crash (ADK read `{e}` in the selector code as a state variable). Smoke 2 after the fix
(`results/smoke2-20261030e15{,rb}-agent_e15`, `results/e15-gate.json`): 12 attempts, propose called in 7 (58%, rule ≥ 70%),
selector run in 3 (25%, rule ≥ 60%), no crash, 2 solved (both OOD). Of 4 selector runs: 2 Python syntax errors (quotes in
the transcribed OLD/NEW text), 1 all-NOMATCH, 1 applied the root's own fix (R PASS). propose came at 72-371 s into the
task; 9 of 12 attempts ended at the 8-minute cap (~480-506 s).
Which assumption broke: "the root can transcribe 4 candidate edits into one script reliably and in time". It cannot:
exact-text transcription fails, and the extra step comes too late in a call budget already used up by reading.
Combined with the ceiling analysis (kb/analysis-2026-10-30-ceiling.md: best-of-3 with verdict selection ≈ +19% on
rb64 even with whole independent attempts), P1 is parked. Next per-attempt work targets multi-site completeness and
call economy; the k lever is re-tested through speed (E14b, 12B).
