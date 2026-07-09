---
quick_id: 260709-nvp
slug: re-ignore-python-bytecode-caches-under-s
date: 2026-07-09
status: complete
base_branch: develop-gsd
---

# Quick Task 260709-nvp: Re-ignore Python bytecode caches under scripts/

## Objective

Fix an over-broad `.gitignore` negation introduced by the Phase 2 plan 02-03
`scripts/` gitignore fix. That fix added `!/scripts/` + `!/scripts/**` to undo the
virtualenv-template `[Ss]cripts` trap (so `scripts/smoke_pipeline.py` is
committable), but `!/scripts/**` re-includes **everything** under `scripts/` —
including `scripts/**/__pycache__/` bytecode caches, which should never be tracked.

## Task

- **Files:** `.gitignore`
- **Action:** After the `!/scripts/` + `!/scripts/**` negations, add a targeted
  re-ignore `scripts/**/__pycache__/` with an explanatory comment.
- **Verify:** `git check-ignore -v scripts/__pycache__/` reports the new rule;
  `git check-ignore -v scripts/smoke_pipeline.py` reports NOT ignored;
  `git status` no longer lists `scripts/__pycache__/`.
- **Done:** bytecode caches under `scripts/` ignored; intentional source still tracked.

## Out of scope (deferred)

The legacy demo drivers surfaced by the same 02-03 gitignore fix
(`scripts/02_…08_*.py`, `scripts/v1.0/`, `scripts/v2.0/` — v2.0 is stale against
pchandler 2.x) are deliberately **not** touched here. Their disposition
(commit / narrow-ignore / delete) is deferred to Phase 4 (Code Quality).
