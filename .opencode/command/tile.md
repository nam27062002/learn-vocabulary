---
description: Execute the next refactor tile from REFACTOR_PLAN.md (behavior-preserving, baseline-verified).
agent: build
---

Execute exactly one refactor tile using the `refactor-tile` skill protocol: load `REFACTOR_PLAN.md`, pick the first unchecked tile (or the tile the user specified: $ARGUMENTS), run the baseline test suite, implement the single concern on the refactor branch, verify with the full test suite + `manage.py check`, then append one line to `REFACTOR_LOG.md` and check off the tile in `REFACTOR_PLAN.md`. Stop after the one tile and report the outcome — do not start another tile.
