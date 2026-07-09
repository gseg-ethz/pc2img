---
quick_id: 260709-nvp
slug: re-ignore-python-bytecode-caches-under-s
date: 2026-07-09
status: complete
base_branch: develop-gsd
---

# Quick Task 260709-nvp: Re-ignore Python bytecode caches under scripts/ — Summary

## What was done

Added a single targeted rule to `.gitignore` immediately after the Phase 2
`!/scripts/` + `!/scripts/**` re-include block:

```gitignore
# ...but never track Python bytecode caches under scripts/: the broad !/scripts/**
# re-include above would otherwise un-ignore scripts/**/__pycache__/ (generated).
scripts/**/__pycache__/
```

Ordering matters — the re-ignore comes *after* the `!/scripts/**` negation so it
wins for the `__pycache__` subtree while leaving everything else under `scripts/`
re-included.

## Verification

- `git check-ignore -v scripts/__pycache__/` → `.gitignore:128:scripts/**/__pycache__/` (now ignored ✓)
- `git check-ignore -v scripts/smoke_pipeline.py` → not ignored ✓ (intentional source still trackable)
- `git status` no longer lists `scripts/__pycache__/` ✓
- Legacy demo drivers (`scripts/02_…08_*.py`, `scripts/v1.0/`, `scripts/v2.0/`)
  remain untracked-but-trackable — untouched, deferred to Phase 4 as intended ✓

## Notes

- Branched off `develop-gsd` (5efaea8) per instruction; commit scope `chore(gitignore):` (functional, no planning-ID tag).
- Root cause was a side effect of the Phase 2 plan 02-03 gitignore fix; this closes the `__pycache__` half of the "surfaced scripts/" open item. The demo-driver disposition remains open for Phase 4.

## Self-Check: PASSED
