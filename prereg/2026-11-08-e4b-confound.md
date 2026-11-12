# E4B scale point: inability or early stopping? (2026-11-08, before any run)

**Instrument; adopts nothing.** Removes the confound in the paper's scale claim (`kb/experiments.jsonl` E4Bround1).

## Observation
E4B with agent_e18 on F51: control 1.0, O3 3.0 (+2.0), D3s 1.5 on N32, median 6-7 calls, 9-14 empties of 51. 31B: O3 +11.5. Two readings: (a) E4B cannot turn a contract into a fix (ability wall); (b) E4B stops before it reads or uses the contract (delivery confound).

## Arms (E4B served under the 31B name, F51, interleaved)
- O6 with agent_e18 (gold fix in the issue) x1: can E4B apply a known fix inside the harness at all? (31B: 51 of 51.)
- agent_e10 control x2 and agent_e10 + O3 x2: our test-first agent, whose procedure is to write and run a check before editing; on 31B it gained +12.0 from O3. It runs longer on E4B (median 9-10 calls on rb64).
About 3 h.

## Predictions
O6 N32 20-32 (E4B can copy a diff); e10 control N32 0-2; e10 + O3 N32 2-8.

## Rules
1. **Ability wall:** O6 N32 ≥ 20 and e10 O3 − control ≤ +3: E4B applies a given fix but cannot use tests, even with a test-first procedure. The paper states the scale boundary without the delivery caveat.
2. **Delivery confound:** e10 O3 − control ≥ +6 (p ≤ 0.05): with a procedure that engages the tests, E4B uses the contract; the scale claim is withdrawn or reworded as procedure-dependent.
3. **Cannot apply fixes:** O6 N32 < 15: E4B fails even with the answer, so the harness delivery itself is the limit at 4B; the paper reports E4B as delivery-bound.
4. Otherwise: numbers only.
