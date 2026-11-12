# Oracle ladder: K1, then O6, O3, O23, O2, O1 (prereg 2026-11-03, before any K1 or oracle run)

## Amendment (2026-11-03, before any run; from `reports/rethink-2026-11-02/judge-final.md`). This overrides the text below where they differ.
- **Base is agent_e18, not agent_idris24.** Compaction removes the first user message (statement gone before first edit in 42 of 128 idris24 attempts), and e18 pins the statement, so the section survives. Require `lost` = 0. `NO_COMPACTION=1` only for a low O23.
- **K1 and the terse instrument dropped.** On 242 natural tasks short statements cost nothing (0.59 vs 0.57, 0.32 vs 0.27), and the public mix predicts 0.32-0.47, matching public local and not Kaggle. Terse removed all inline code (0%, public 57%) and in 5 of 14 read statements the identifier carrying the ask. Theory K rejected as the main gap explanation; the gap stays unexplained. The instrument candidate is the natural H set (no code, ≥ 3 hunks; 0.178, n 36), level-calibrated only.
- **O1, O4 dropped; M1 deferred.** Order: control, O6, O23 × 2, control r2, O3 × 2, O2.
- **Noise:** N32 SE 0.6 holds only at control's rate; inside an arm SD is 2.2 at true 6, 2.4 at true 8. One pass separates 3 from 10, not 4 from 8, so O23 and O3 get two passes, and thresholds read on the mean. M19 is used only for O6 and the reliability branch.
- **Baseline:** N32 0.67, M19 11.7, "M19 moves" ≥ 15.5. Control is measured live. Also report F51's 18 tasks with ≥ 3 hunks (`compare_ood.py --tasks dev_sets/rb_f51_h3.txt`).
- **O3 is not executable** in this agent (the prompt forbids editing tests and the patch must be transcribed), so a low O3 cannot read as "not information". Conditional O3x: tests already in the snapshot.
- **Prediction (judge):** O6 ≥ 26, O23 8-14, O3 6-10, O2 ≤ 4. A high reading does not imply 0.25: gold cannot ship.

**Instrument. It adopts nothing.** It locates the wall; no arm can be submitted, and no verdict here may promote anything. Oracle information stays in `research/` and `results/*oracle*`; `scripts/preflight.sh`, `train/oracle_guard.py` and `scripts/kb_lint.py` enforce that. Findings transfer as general design only, after their own prereg. O5 and O4 come later (O5 needs a plans file, O4 needs run F); M1, R1, R2 are not covered here.

## Observation
`reports/rethink-2026-11-02/ceilings.md`, rb64 pool (49 passes, 3,136 attempts). Tasks matter and agents barely do: between-task variance 71%, agent main effect 0.17%. N32 (rate under 0.1) holds 32 tasks and 0.4 solves per pass; M19 (0.1-0.9) holds 19 tasks and 10.5; A13 (≥ 0.9) holds 13 tasks and 12.6. Target 0.25 ≈ 37/64, so +13. Perfect M19 gives +8.5, so **at least +4 must come from N32, where nothing has ever moved.**
Kaggle gap: rb64 composite 33.9, spec 25.1, median words 111; public 129 composite 41.5, spec 44.5, words 58. rb64's slope predicts 0.19 linear, 0.26 logit on the public mix, against rb 0.37 and Kaggle 0.15-0.17.

## Hypotheses
- K: the gap is mostly thin statements, not larger fixes.
- Ladder: each arm adds one kind of gold information to the issue text. Where N32 starts to move names what is missing: applying (O6), the hidden contract (O3), the maximum without the fix (O23), exact location (O2), file location (O1).

## Assumptions
1. Statement text is the only change. `agent_idris24` is byte-identical in all arms, checked at job start. `scripts/build_oracle_data.py --verify-only` and `scripts/build_terse.py --verify-only` prove only `problem_statement` (and `oracle_arm`) differ from `data/rebench`.
2. The agent believes the section. It says the information is correct; counter below.
3. Partitions are selected on the same data, so N32 can only regress upward and M19 either way. The interleaved control absorbs this.
4. **The section survives long enough.** Compaction replaces the first user message with a summary. In `results/sft-20261102e18rb-r{1,2}-agent_idris24`, the statement was already gone before the first edit call in 42 of 128 attempts (first edit: median call 6-7). Oracle arms inherit this, and a longer statement may compact sooner. Added to ceilings.md by this prereg, see Decision.
5. Hidden mix ≈ public 129 (unverified). K1 tests the mechanism, not this premise. Agents share ancestry; "agents don't matter" means this family.

## Arms
All `agent_idris24`, graph-free as it stands, SFT logging on, resumes per task. `queue/held/50-oracle-day1.sh`.

| ID | Data | Statement change | Tasks | Passes | GPU h | Results |
|---|---|---|---|---|---|---|
| K1 | `research/instrument/rb64-terse` | Templates, fences, inline code, exception names stripped; word counts from public 129 | rb64 | 2, + control × 1 on `data/rebench` | 3.75 | `results/ood-instr20261103k1-r<N>-agent_idris24-terse`, control without suffix |
| O6 | `research/oracle/o6` | Gold diff | F51 | 1 | 1.05 | `results/ood-oracle20261103-r1-agent_idris24-o6` |
| O3 | `research/oracle/o3` | Test patch + F2P names | F51 | 1 | 1.05 | as above, `-o3` |
| ctrl | `data/rebench` | None | F51 | 1 | 1.05 | as above, no suffix |
| O23 | `research/oracle/o23` | Hunks + tests | F51 | 1 | 1.05 | `-o23` |
| O2 | `research/oracle/o2` | Files, lines, function | F51 | 1 | 1.05 | `-o2` |
| O1 | `research/oracle/o1` | Gold files | F51 | 1 | 1.05 | `-o1` |

Run time about 10 h. A13 is not run on F51: it cannot move. rb64-terse as built: composite 39.0 (public 41.5), spec 45.2 (44.5), words 40 (58), overlap 45% (36%), code 19% (19%). The transform reads no gold.

## Predictions (ceilings.md table; now N32 0.4, M19 10.5)
| ID | Question | Predicted N32 / M19 | High vs low | Surprise |
|---|---|---|---|---|
| K1 | Thin text causes the gap? | 13-20 of 64 (control ~23) | ≤ 19: new primary instrument. ≥ 22: repos, not text | No fall |
| O6 | Applies a known fix? | ≥ 26 / ≥ 17 | Under 24: tools or delivery wall, fix first | Under 20 |
| O3 | Hidden contract | 6-14 / 14-17 | ≥ 8: spec lever. ≤ 3: not information | ≥ 16 |
| O23 | Maximum without the fix | 8-16 / 14-17 | **≤ 4: edit ability is the wall** | ≤ 2 |
| O2 | Exact location | 2-5 / 12-14 | ≤ 3: closes sites finder, graph work | ≥ 8 |
| O1 | File location (cf. GemmaLoc 27 vs 24/65) | 1-3 / 11-13 | Same | ≥ 5 |

Later, same table: O5 10-20 / 15-18 (low: execution wall; surprise: below O3). O4 2-6 / 12-15 (≥ 6: distil planning; surprise: ≥ 10).

## Reading the ladder (ceilings.md)
- O3 and O23 low: edit ability is the wall. LoRA or a different mechanism only; otherwise accept about 0.17-0.20.
- O3 high, O4 low: contract unavailable from the issue. Only a spec generator; first test strong-model tests without gold (O3b, 1.05 h).
- O3 high, O4 high: reasoning. Plan step, teacher-plan distillation.
- M19 moves, N32 does not: reliability. Reviewer retry: 8.5 failing × 0.42 × ~0.5 resample ≈ +1.8, false rejects ≈ −0.3, about +25% time (inference from E22, mixed tasks only).

## Decision
Read `python3 scripts/read_ladder.py` per arm: N32 / M19 / A13 solved, delta against the interleaved control, branch. N32 first. One-pass noise on known rates: N32 SE 0.6, M19 SE 1.9. Second passes only for arms that moved. Pairwise check: `python3 scripts/compare_ood.py oracle20261103 agent_idris24 agent_idris24-o3 --all --tasks dev_sets/rb_f51.txt`; K1: `python3 scripts/compare_ood.py instr20261103k1 agent_idris24 agent_idris24-terse --all --tasks dev_sets/rb64.txt`.

Operational rules that ceilings.md leaves open, added here before any run:
1. The O-arm thresholds apply to N32. K1's apply to the mean of its passes over 64.
2. "M19 moves" means ≥ 14.3 (10.5 + 2 SE). "N32 does not" means ≤ 3.
3. A value between a table's thresholds takes a second pass, no branch.
4. **Assumption 4 guard.** If a low branch comes with `lost` over 30% of the arm's attempts, it is not read. Run one more pass of that arm with `NO_COMPACTION=1` first (1.05 h), a runner change that is fine for an instrument. Control's own rate is 33%, so this may fire.
5. O6 under 24 stops the reading above it: fix the wall first, after its traces say what the wall is.

## Mechanism counters
- Delivery: `sec1`, section present at first call (must be all attempts); `lost`, section gone before first edit call. From the SFT logs.
- Outcome shape: empty and wrong patches, mean tool calls, mean minutes per attempt. Baseline control counters from the same job.
- Location: share of attempts touching all gold hunks at ±5 lines (baseline on never-solved tasks: 29%; weak, only 64% of solved attempts do). O2 and O23 must raise it, or the agent ignored them.
- Traces, for the O6 rows that fail: did the agent try the diff, how did the edit tool answer, where did time go. Read at least five before believing any branch from O6.
- K1: control near 23, within noise (SD 2.08), or the day drifted.

## Bookkeeping
Rows `O6, O3, O23, O2, O1` with `kind: oracle` in `kb/experiments.jsonl`, K1 as a plain instrument row. `scripts/kb_lint.py` exits 1 on any oracle row with an adoption verdict. Tags start with letters on purpose: `reports/rethink-2026-11-02/mine.py` globs `results/ood-2026*`, so these runs stay out of pooled rates.
