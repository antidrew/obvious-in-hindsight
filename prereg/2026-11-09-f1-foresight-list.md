# F1: does anticipating the hidden requirements from the issue help the agent? (2026-11-09, before any run)

**Instrument; adopts nothing** (the predictions come from a stronger model). Follows `2026-11-09-reqclass2-foresight.md`.

## Observation
The Claude foresight writer anticipates 57% of hidden-test requirements from the issue alone (stated 92%, inferable 46%, choice 31%, arbitrary 10%). Yet a ≤ 50-word statement from the issue alone (D4) gave +1.0 (N32) and −0.5 (H35). F1 supplies the full prediction list (up to 8 concrete behaviours, not capped at 50 words) instead of a short statement.

## Arms (agent_e18 unchanged; built by `scripts/build_f1_data.py` from the D4 data sets, only the appended section differs; 0 gold-line leaks)
N32: control x1, F1 x2. H35: control x1, F1 x2. The section keeps the firewall header ("Verified information for this task"); its text says the items are predictions that may be wrong. About 5 h.

## Predictions
F1 − control: N32 0 to +3; H35 −1 to +3. Well below D3 (+13.5, +12.0).

## Rules
1. **Anticipation is not enough:** F1 − control ≤ +2 on both sets: knowing half the requirements, including a third to a half of the inferable ones, does not move solves; the decisive part is the requirements writers miss. Paper: the gap is in the unanticipated requirements.
2. **Anticipation helps:** F1 − control ≥ +4 on either set with p ≤ 0.05: issue-only prediction lists are a usable lever (a stronger model's list; a same-model version would be the next test).
3. Otherwise: numbers only.

## Addendum (2026-11-10, after F1 and F1g, before these passes)
F1 read +4.5 (N32) and +4.0 (H35) with one control pass per set. Job 102 adds a second control pass and a third F1 pass on both sets, interleaved (control, then F1). The pooled reading (3 F1 passes, 2 control passes) replaces the first reading in the paper whatever it shows; rule thresholds unchanged.
