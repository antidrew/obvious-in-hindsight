# E20: the blind sandbox (prereg 2026-11-02, before any E20 agent run)

## Observation
The official starter evaluates with `sandbox='subprocess'`; no docker binary exists in a Kaggle notebook (probe 11-02). In that mode swegemma skips the editable install and test-dep
setup (`container_setup.py:528`), so the agent imports from `PYTHONPATH=/workspace` + the host's packages. All our local evaluations use Docker with per-task wheels. Forum 752672 and
752490 report the same; the hosts have not said which backend scores (754586). rb64 has 13 src-layout repos of 64, OOD-45 6 of 45 (their packages will not import from /workspace at all
unless also on the host). The hidden set scores ~15% vs rb64 ~35%. Candidate-010 (test-first, 5-min cap) got 0.06 against local +4/+2.5.

## Hypothesis
If the scorer's agent phase is like the starter, the agent's checks mostly fail on imports or test the host's copy of a package, so it works blind. That lowers solves relative to Docker
and hits test-first designs hardest, because a FAIL from an import error looks like a real FAIL. This would explain part of the local-to-Kaggle gap and the ordering e10t5 < idris24.

## Assumptions
1. The host environment is approximated by `.kaggle-site-packages` (Kaggle freeze without GPU/ML stacks) + the harness venv; agent python 3.12 like the starter log (the current notebook image is 3.13).
2. Verification in Docker with per-task wheels stands in for the scorer's phase 2, which validates gold at 100%. 3. Same tasks, same model server, one pass.
E20 tests an unconfirmed premise: a null means blindness is not costly even if it exists, and a large effect does not prove the scorer works this way; a Kaggle draw has to confirm.

## Arms
rb64 × 1 (then OOD-45 × 1 if informative): agent phase `SANDBOX=subprocess EXTRA_SITE=.kaggle-site-packages`, patches scored by `scripts/run_e20_verify.sh`.
agent_idris24, agent_e10, agent_e19. Comparators: the same agents in Docker (E18/E19 control pass, E10 passes).

## Predictions
| Counter | Docker | Subprocess |
|---|---|---|
| commands ending in ImportError/ModuleNotFoundError per attempt | ~1 | ≥ 3 |
| idris24 rb64 solved | ~21.5 | ≤ 18 (−15% or more) |
| e10 − idris24 (rb64) | ~+1 | ≤ −2 |
| empty patches | 8/128 × | up |
Local Kaggle-level check: subprocess rb64 for idris24 ≥ 12 (the hidden set is harder, so no absolute match is expected).

## Decision
- idris24 falls ≥ 15% and imports fail ≥ 3/attempt: T2 supported. Run every later arm in both sandboxes; subprocess becomes the time and prompt-robustness instrument; design an environment bootstrap
  step (locate the package, set PYTHONPATH=src, shim only by import path, never in the diff) and test it on Kaggle with draws.
- Otherwise T2 rejected as a main cause; keep Docker as the instrument and record it.
