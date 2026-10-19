---
description: Run the full Django test suite with the project venv, plus a project check, and summarize results.
agent: build
---

Run the project's verification commands (Windows, venv required):

1. `& .\.venv\Scripts\python.exe manage.py test --verbosity 1` — full suite.
2. If any test fails, capture the failing test names and the one-line assertion errors.
3. `& .\.venv\Scripts\python.exe manage.py check`.

Then summarize: pass/fail count, list of failing tests with their strongest one-line cause, and whether each failure is pre-existing (matches the baseline in `REFACTOR_PLAN.md`) or newly introduced by pending changes. Do not fix anything in this command; just report.

$ARGUMENTS
