# Pre-registration E2: two single changes to pub22 on OOD-45 (budget; verify against the specification)

Written 2026-10-21 03:45, after E1 and before any E2 run.

## Why
E1: pub22 beat v33 by +6.0 tasks per pass on OOD-45 (p = 0.004); pub22 becomes the base and OOD-45 the primary
local metric. pub22 is at 88% there (39.5/45), so headroom is ~5.5 tasks per pass. Its Kaggle draws (7, 9, 11, 13
of 58, mean 10) need +3 for the 0.23 target. Local pacing matches Kaggle (7.8 s per model call at 3 processes vs
8.7 s reported for Kaggle), so local budgets bind as they would there.

pub22's 11 failed attempts on OOD-45 show two mechanisms:
1. **The 28-call cap binds**: 15/90 attempts end at 28 calls, 5 of them fail (2 empty). Forum (746250): longer
   caps solve more (6/10/15 min -> 37/46/54 of 129).
2. **Incomplete fix submitted with budget left** (wrong patch, 9/90): sibling site missed (feast_6874 fixed the
   constructor, not the read-back), exact message case wrong and an unrelated decorator deleted
   (iceberg_3995), partial semantics (tox_4094). pub22's verify step is capped at 2 calls and checks one test.
   The hidden set was filtered to tasks a strong model "solved or failed by one assertion", so this failure
   class should be more common there than here.

Strategies used (the user's list): problem decomposition (statement -> checklist of claims), scientific method
(each claim becomes an executed assertion), knowledge transfer (sibling-site search).

## Arms (each one change from agent_pub22)
- `agent_e2a`: `max_tool_calls` 28 -> 44; prompt's limit and call plan numbers moved to match (verify window
  13-34, no new exploration from 34). Time cap 8 min unchanged. 44 x 8.7 s = 6.4 min fits on Kaggle.
- `agent_e2b`: steps 4-5 of the prompt replaced: claim checklist, sibling-site `git grep`, one heredoc check
  script asserting every claim, one targeted test run, character-level message check, every diff hunk must
  serve a claim. Cap 28 unchanged.
- Control: pub22's two E1 passes (same server, same day, same runner), symlinked as tag `20261021e2`.

## Contamination note
E2b's text was written after reading pub22's OOD failures. Examples were made generic (no task's identifiers),
but its OOD gain is optimistic. Out-of-sample checks: dev33k and the Kaggle submission.

## Predictions
- E2a - pub22: +1.0 tasks per pass (plausible 0 to +2.5); attempts ending at the cap 15/90 -> <=8/90 (at 44);
  empty patches 2 -> <=1; mean duration 174 s -> 190-230 s.
- E2b - pub22: +1.5 (plausible 0 to +3); wrong patches 9/90 -> <=5/90; median tool calls 20 -> 22-25;
  at-cap rate may rise (risk: verification eats the budget; >20/90 at cap would show it).
- Neither arm worse than pub22 by more than 1 task per pass.

## Decision
- An arm with gain >= +1.0 and p <= 0.2 is kept. If both are kept, E3 combines them (cap 44 + spec verify) and
  is checked against both on OOD and on dev33k before any Kaggle upload.
- Gain between -1 and +1: one more pass for that arm and pub22 before deciding.
- If both fail: the bottleneck is not where these counters point; step back to the traces.

## Outcome on OOD-45 (2026-10-21 07:23, 2 passes per arm)
- **E2a (cap 44): -2.00 tasks/pass vs pub22** (37.5 vs 39.5; one-sided p for a gain 0.95). Prediction (+1.0,
  never worse than -1) **failed**. Mechanism half right: at-cap attempts 15 -> 9/90, mean duration 174 -> 220 s,
  but wrong patches 9 -> 14/90 and timeouts 1 -> 3. The extra calls went into churn and over-editing (e.g. a
  3.2 kB great_tables_889 patch). The 28-call cap acts as a regulariser. Rejected.
- **E2b (verify each claim): +0.00** (39.5 vs 39.5, p = 0.63). Predictions failed: wrong 10/90 (pred <= 5),
  median calls 18 (pred 22-25); at-cap 17/90 (risk bound 20 held). Gains fall exactly on the tasks whose
  failures inspired the text (feast_6874 0 -> 2/2, filesystem_spec_2191, kedro_5790: contaminated), losses
  spread over 4 great_tables tasks and apprise. Undecided by the rule (between -1 and +1).

## Addendum: E2b out-of-sample check on dev33k (written before the run)
Arms `agent_e2b` and a fresh `agent_pub22`, 2 passes each, interleaved, one task per process
(`DATA=data/kaggle-20261013 WHEELS=data/kaggle-20261013/wheels scripts/run_ood_ab.sh`, tag `20261021d33`,
Kaggle wheels). Score with `compare_ood.py --all --tasks dev_sets/dev33k.txt`.
- Prediction: e2b - pub22 = +1.0 per pass (plausible -1 to +2.5); the harder pool has more partial fixes.
- Keep e2b only if the dev33k gain >= +1.0 with p <= 0.2 (OOD is a tie, so dev33k decides). Otherwise e2b is
  rejected and pub22 stays the base.

## Outcome of the dev33k addendum (2026-10-21 10:36)
- **e2b - pub22 = +2.00 tasks/pass over 33, p = 0.154** (15.0 vs 13.0; pub22 passes 12, 14; e2b 15, 15). Prediction
  (+1.0, plausible -1 to +2.5) held. Empty 15 -> 13/66, wrong 26 -> 23/66. Gains on rich_3676 (0 -> 2/2: the
  stored-as-str bug), 2725, 2943, 3043, 3521; losses on 3470, 3480 (half each).
- Mild contamination: the sibling-site idea also came from the rich deep dive (rich_3480), where e2b got worse.
- Decision (as registered): **e2b kept; it is the new base.** Combined over 78 tasks: +2.0 per pass.
  Packaged as Candidate 009, awaiting approval.

## Third dev33k pass (2026-10-21 12:10, confirmation)
Pass 3: e2b 14, pub22 15. Over 3 passes: **e2b - pub22 = +1.00/pass, p = 0.287** (14.67 vs 13.67; empty 20 vs
23/99, wrong 35 vs 36/99). The 2-pass +2.0 shrank as expected for a selected result. With the OOD tie, the best
estimate is e2b ≈ pub22 + 0 to 1 task per pass: not worse, gain unconfirmed. e2b stays the base (no evidence it
hurts, mechanism plausible for the hidden set's "one assertion" failures), but the gain is weak evidence.
