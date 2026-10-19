---
name: refactor-tile
description: Execute one behavior-preserving refactor tile in the learn-vocabulary Django project. Use LITERALLY when the user says "refactor tile", "start a tile", "next tile", "continue the refactor", or references REFACTOR_PLAN.md. Not for feature work or bug fixing.
---

# Refactor Tile Workflow

Perform exactly one refactor tile from `REFACTOR_PLAN.md`, behavior-preserving, then stop for review.

## Steps

1. **Load the plan.** Read `REFACTOR_PLAN.md` and pick the first unchecked tile. If a tile is ambiguous, ask the user which tile to run instead of guessing.
2. **Baseline.** Run the full suite (`& .\.venv\Scripts\python.exe manage.py test`). It must be green (0 failures using the current baseline expectations). If red, stop and report — never refactor on top of red.
3. **Implement one concern.**
   - Behavior-preserving: URLs, responses, model behavior, and rendered pages must not change.
   - Create an isolated branch/worktree, or work on the current refactor branch — ask the user which if unclear.
   - Do NOT quietly expand scope: if you discover new work, add a new tile to `REFACTOR_PLAN.md` instead of doing it now.
4. **Verify.**
   - `& .\.venv\Scripts\python.exe manage.py test` → same pass/fail set as baseline.
   - `& .\.venv\Scripts\python.exe manage.py check` → no issues.
   - For template/static moves, also smoke-check affected pages server-side (status 200, key strings present) with Django test client or a quick shell render.
5. **Log and close.**
   - Append one line to `REFACTOR_LOG.md`: date, tile name, one-sentence outcome.
   - Check the tile off in `REFACTOR_PLAN.md`.
   - Propose a short imperative commit message; only commit if the user asked.

## Anti-patterns to refuse

- Mixing a behavior change (new feature, new field, changed response shape) into a structural move.
- Deleting legacy code (e.g., `Flashcard.ease_factor` / `interval`) without a plan tile.
- Reformatting large files inside a logic-move tile.
