# Foresight test: can a writer anticipate the hidden-test requirements from the issue? (2026-11-09, before any run)

Follow-up to `2026-11-08-reqclass.md`, whose task-level classification was unreliable (kappa 0.00; the Gemma rater rated 93% of requirements stated or inferable, with no open tasks). Raters who see the tests judge in hindsight. This study measures foresight directly. Research data only (`research/reqclass/`).

## Design
- **Ground truth:** the Claude rater's requirement list per task (236 requirements, classes I/R/C/A, `rater_claude.json`), derived from the test patches.
- **Foresight writers** (issue text and repository name only, no tests, `research/reqclass/issue_only/`): Gemma 4 31B (local, temperature 0.2) and a Claude subagent. Each lists up to 8 behaviours the hidden tests most likely check.
- **Judge:** a separate Claude subagent sees, per task, the test patch, the ground-truth list, and the two prediction lists labelled X and Y in random order per task. For each ground-truth requirement it marks whether each list anticipated it: yes, partial or no.
- **Measures:** foresight recall per writer (yes = 1, partial = 0.5), overall and by ground-truth class; per task; the correlation of recall with the D3 statement gain.

## Predictions
Overall recall 30-50% per writer; by class I 60-85%, R 20-45%, C 10-30%, A under 10%. Claude ≥ Gemma by 5-15 points.

## Rules
1. **Hindsight gap established:** recall of R-class requirements ≤ half the recall of I-class for both writers: much of what raters call "inferable" is not anticipated. The paper states the gap as "behaviour that looks inferable once the tests are seen, but is not anticipated from the issue".
2. **Anticipated but unused:** overall recall ≥ 60% for a writer: the writer anticipates most requirements, yet its D4/D5 statements did not help. The failure then lies in turning anticipation into a short statement or in the agent's use of it, and the paper says so.
3. Otherwise: report recall by class with both writers, no headline claim.
