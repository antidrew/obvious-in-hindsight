# Pre-registration: is SWE-rebench (RB) a better instrument than OOD-45?

Written 2026-10-22 (UTC) while the tasks were being built, before any agent run on them.

## Why
OOD-45 orders agents in the Kaggle direction (E1, confirmed by Candidate 008 = 0.13), but the public single
agent pub22 solves 88% of it, against ~17% of the hidden set. Near the ceiling only ~6 tasks per pass can move,
so a +1-2 task change (what 0.23 needs) is unmeasurable there. dev33k is harder but 30/33 rich, 14 title-only.

RB: tasks from `nebius/SWE-rebench-leaderboard` (CC-BY-4.0), months 2025-09 to 2026-03, original issue text,
repos outside the public 129, Python-only fixes touching <= 3 files, pytest tests, at most 2 per repo
(`scripts/build_rebench.py`). Environment = our sandbox image + per-task wheels resolved in that image from the
task's recorded install commands ("same sandbox but different wheels", as the host describes the hidden set).

## Acceptance (all must hold before RB is used for decisions)
1. **Validity**: >= 50 tasks where gold resolves and empty does not (`run_ood.sh GOLD|EMPTY`).
2. **Difficulty**: pub22 solves 15-50% per pass (hidden-like, not near a ceiling).
3. **Ordering**: pub22 - v33 > 0 over 2 passes each (Kaggle: +2.6/58 ≈ 4.5 points). Prediction: +1 to +5 tasks.
4. **Resolution**: >= 15 tasks with mixed outcomes across the 4 attempts (these carry the signal).
If 1-3 hold, RB becomes the primary metric for E3 onward (OOD-45 stays as a guard against regressions).
If 2 fails high (> 50%), RB is only a bigger OOD; if 3 fails, RB does not track Kaggle and is dropped.

## Known risks
- Contamination: the tasks predate the Gemma 4 release, so the model may have seen the fixes. The memory probe
  (2026-10-21) found Gemma does not recall linked issues; rank order is what matters here.
- Our wheel resolution differs from the hosts' (they use their own pins); tasks that need services, network,
  compiled extensions without cp313 wheels, or a missing build tool fail gold and are excluded, as the hosts did.
- Selection is not filtered by "a strong model solves it", unlike the hidden set, so some tasks may be
  unsolvable from the statement; criterion 2 checks the overall level.

## Build outcome and validation plan (2026-10-22 06:55 UTC, before any agent run)
- Pool: all 2025-01..2026-03 leaderboard months, <= 2 tasks per repo, 316 selected, 303 built. Wheels resolved in
  our sandbox image: recorded install commands with `--uploaded-prior-to` (task date + 2 days) plus build-system
  requirements; tasks that still failed gold were rebuilt from the exact pins of their own SWE-rebench image.
  Excluded by construction: tests needing network, missing system libraries, or the pytest plugins the harness
  never installs (pytest_asyncio, pytest_xdist, pytest_httpbin) - the hidden set cannot contain those either.
- **Criterion 1 holds: 146 scorable tasks** (gold resolves, empty does not) from 120 repos (`dev_sets/rb.txt`).
- Criteria 2-4 are tested on a seeded random subset of 64 (`dev_sets/rb64.txt`, seed 20261022) to fit ~4 h of
  GPU: pub22 and v33, 2 passes each, interleaved, 3 processes. Tag `20261022rb`.

## Outcome (2026-10-22 11:58 UTC; rb64, 2 passes each)
- Criterion 2 (difficulty) **holds**: pub22 23.0/64 = 36%, v33 24.0/64 = 38%.
- Criterion 4 (resolution) **holds, barely**: 16 tasks with mixed outcomes; 33 never solved, 15 always.
- **Criterion 3 (ordering) fails: pub22 - v33 = -1.00/pass** (one-sided p for pub22 better 0.76). Of the 31
  tasks solved at least once, pub22 is better on 5, v33 on 8.
- Mechanism: **pub22 ends at its 28-call cap in 53/128 attempts (41%)** vs 17% on OOD-45; empty 18 vs 5/128;
  v33 (80 calls) hits its cap 4 times. RB tasks (unfiltered, larger repos) need more steps than the hidden
  set does; the hidden set was filtered to tasks "a strong model with a simple config" solves, which makes it
  more OOD-like. SWE-rebench publishes no per-task model results, so that filter cannot be reproduced.
- **Decision (as registered): RB is not the primary metric.** It stays a secondary hard-task set that is
  informative about budget-bound behaviour. Primary: OOD-45 (ranks like Kaggle) plus the daily Kaggle draw.
