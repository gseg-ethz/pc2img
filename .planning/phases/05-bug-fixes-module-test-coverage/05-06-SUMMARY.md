---
phase: 05-bug-fixes-module-test-coverage
plan: 06
subsystem: testing
tags: [rrim, ruff, e402, module-docstring, features, hygiene]

# Dependency graph
requires:
  - phase: 05-01
    provides: shared tests/conftest.py synthetic fixtures + Phase-5 test scaffold
provides:
  - "Populated pc2img.features.rrim.__doc__ (module docstring is the first statement)"
  - "E402-clean rrim.py header (imports follow the docstring + __future__ import)"
  - "Proving tests asserting __doc__ non-empty and ruff --select E402 clean on rrim.py"
affects: [05-12, rrim, hygiene, ruff-gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Header ordering for __future__-using modules: docstring first, then 'from __future__ import annotations', then remaining imports"
    - "In-test ruff invocation via subprocess (--select E402) mirroring tests/test_hygiene.py"

key-files:
  created: []
  modified:
    - src/pc2img/features/rrim.py
    - tests/test_rrim_features.py

key-decisions:
  - "M-13 (RRIM near-axis ray-sampling fidelity) deferred/logged only per D-16 — no code change; openness/slope math is CONFIRMED-CORRECT (04-FINDINGS)"
  - "No __all__ added to rrim.py — none existed and enumerating the public surface is out of scope for a mechanical header reorder; the plan's __all__ mention is descriptive of the generic pattern"

patterns-established:
  - "docstring-first / __future__-second header ordering to populate __doc__ without tripping Python's __future__-placement SyntaxError"

requirements-completed: [BUG-04]

coverage:
  - id: D1
    description: "rrim.py module docstring is the first statement, so pc2img.features.rrim.__doc__ is a non-empty string (BUG-04)"
    requirement: BUG-04
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_rrim_module_docstring_is_populated"
        status: pass
    human_judgment: false
  - id: D2
    description: "rrim.py module-level imports no longer trigger ruff E402 (imports follow the docstring)"
    requirement: BUG-04
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_rrim_module_docstring_clears_e402"
        status: pass
      - kind: other
        ref: "ruff check --select E402 src/pc2img/features/rrim.py"
        status: pass
    human_judgment: false

# Metrics
duration: 8min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 06: RRIM Header Reorder (BUG-04) Summary

**Reordered `rrim.py` so the module docstring is the first statement — populating `__doc__` and clearing the E402×9 ruff findings — with two proving tests locking the behavior.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-11T04:30:00Z
- **Completed:** 2026-07-11T04:37:45Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `pc2img.features.rrim.__doc__` is now a non-empty string (the triple-quoted docstring is the first statement).
- The E402×9 ruff findings on `rrim.py` are cleared — `ruff check --select E402 src/pc2img/features/rrim.py` reports zero findings.
- Added two proving tests (`test_rrim_module_docstring_is_populated`, `test_rrim_module_docstring_clears_e402`) to `tests/test_rrim_features.py`, authored xfail then flipped to passing asserts once the fix landed.
- RRIM openness/slope math left completely untouched (CONFIRMED-CORRECT per 04-FINDINGS).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author failing __doc__/E402 proving test for rrim.py** - `7aa60d1` (test)
2. **Task 2: Reorder rrim.py header so __doc__ populates + E402 clears** - `75f541d` (fix)

## Files Created/Modified
- `src/pc2img/features/rrim.py` - Moved the module docstring to be the first statement; relocated `from __future__ import annotations` to sit directly after the docstring and before all other imports. No math/logic changes.
- `tests/test_rrim_features.py` - Added two BUG-04 proving tests (docstring populated + E402 clean via in-test `ruff --select E402` subprocess), plus the supporting `subprocess`/`sys`/`pathlib`/`pytest` imports and `_REPO_ROOT`/`_RRIM_SRC` module constants.

## Decisions Made
- **M-13 deferred/logged (D-16):** RRIM near-axis ray-sampling fidelity is low only on an opt-in feature and the openness math is CONFIRMED-CORRECT, so no code change was made — see the M-13 future-improvement log below.
- **No `__all__` introduced:** `rrim.py` had no `__all__` and adding one would require enumerating the public surface, which is outside a mechanical header reorder. The plan's `__all__` mention describes the generic docstring→`__future__`→`__all__`→imports pattern; the load-bearing requirement (docstring first to populate `__doc__`, imports after to clear E402) is fully satisfied without it.

## M-13 Future-Improvement Log (deferred, D-16)

**Finding M-13 — RRIM near-axis ray-sampling fidelity.** The image-space RRIM openness computation
uses NaN-padded directional shifts that step in whole-pixel increments per direction. Near the
sampling axes this under-samples the ray, and it treats pixel spacing as isotropic. Two future
improvements (no owner sign-off needed to log, but out of scope this phase per D-16):
1. **Dedup-aware ray stepping** — avoid re-visiting the same pixel across near-axis directions so the
   directional openness estimate is not biased by duplicate samples.
2. **`pixel_size` anisotropy** — honor the configured `DEFAULT_PIXEL_SIZE` (x, y) spacing when
   computing slope/openness so non-square rasters (e.g. spherical range images with angular spacing)
   are handled correctly rather than assumed square.

These are fidelity refinements on an opt-in feature; the current openness/slope math is correct.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Bare `python -c` runs outside the venv (`ModuleNotFoundError: pc2img`); re-ran the verification through `uv run --frozen python -c ...` per the environment note. Not a code issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BUG-04 fully resolved; the rrim.py E402 breadcrumb is cleared, which 05-12 (final xfail-reason sweep) expects. Only deferred M-13 remains as a documented future improvement.

## Self-Check: PASSED

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*
