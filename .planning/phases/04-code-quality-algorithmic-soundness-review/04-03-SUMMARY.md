---
phase: 04-code-quality-algorithmic-soundness-review
plan: 03
subsystem: code-quality
tags: [hygiene, ruff-prep, type-checking, registry, features-barrel]

# Dependency graph
requires:
  - phase: 04-01
    provides: tests/test_hygiene.py QUAL-01 gate (import-smoke pass + xfail markers)
provides:
  - make_generator broken factory removed (no 3-positional ctor mismatch)
  - _TransformArray private pchandler import guarded under TYPE_CHECKING with __future__ annotations
  - features barrel __all__ synced to the registered non-rrim feature set
  - single live keyword-only convert_to_image in util.py (dead duplicate deleted)
affects: [04-04-ruff-format-sweep, 04-05-review, 04-06-review]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Private third-party symbols used only in annotations go under `if TYPE_CHECKING:` + `from __future__ import annotations` so runtime import never depends on them"
    - "Package barrels re-export exactly the registered non-opt-in surface; opt-in modules (rrim) stay out of the barrel"

key-files:
  created: []
  modified:
    - src/pc2img/registry.py
    - src/pc2img/strategies/projection.py
    - src/pc2img/features/__init__.py
    - src/pc2img/util.py

key-decisions:
  - "make_generator had zero callers in src/, tests/, scripts/ -> deleted the broken factory rather than repairing it (lower churn per plan's grep-driven choice)"
  - "Chose __future__ annotations (option a) over per-annotation quoting (option b) for projection.py — module-wide, lowest churn, removes the runtime private import entirely"
  - "RRIM features deliberately excluded from features/__init__ __all__ to preserve the opt-in registration gate"

patterns-established:
  - "TYPE_CHECKING-guarded private-dependency imports for annotation-only symbols"
  - "Barrel __all__ == registered non-opt-in feature set"

requirements-completed: [QUAL-01, QUAL-02]

coverage:
  - id: D1
    description: "make_generator broken 3-positional factory removed; pc2img.registry still importable"
    requirement: "QUAL-01"
    verification:
      - kind: unit
        ref: "tests/test_hygiene.py::test_public_modules_import (pc2img.registry smoke import)"
        status: pass
      - kind: other
        ref: "python -c 'import pc2img.registry'; grep -rn make_generator src/ tests/ (no surviving 3-positional call)"
        status: pass
    human_judgment: false
  - id: D2
    description: "_TransformArray import guarded under TYPE_CHECKING with __future__ annotations; projection module imports at runtime without the private symbol"
    requirement: "QUAL-02"
    verification:
      - kind: other
        ref: "python -c 'import pc2img.strategies.projection as p; assert p.PerspectiveProjection and p.SphericalProjection'"
        status: pass
    human_judgment: false
  - id: D3
    description: "features barrel __all__ synced to registered non-rrim features; util.py convert_to_image defined exactly once"
    requirement: "QUAL-01"
    verification:
      - kind: other
        ref: "python -c 'assert set(f.__all__) <= set(dir(f)); assert 1 == count(def convert_to_image)'"
        status: pass
      - kind: integration
        ref: "python -m pytest -q (16 passed / 14 xfailed — no regression)"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-10
status: complete
---

# Phase 04 Plan 03: D-01 Mechanical Source Hygiene Fixes Summary

**Deleted the broken make_generator factory, moved pchandler's private `_TransformArray` import under `TYPE_CHECKING` (with `from __future__ import annotations`), synced the features barrel `__all__` to the registered non-rrim set, and removed the dead `plt`-referencing `convert_to_image` duplicate — all four modules still import.**

## Performance

- **Duration:** ~6 min
- **Completed:** 2026-07-10
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Removed the `make_generator` factory whose 3-positional call mismatched the 5-parameter `PointCloudImageGenerator` constructor (no callers existed anywhere); left a documenting note and kept `pc2img.registry` importable for the hygiene smoke test.
- Guarded the private `pchandler.geometry.transforms._TransformArray` import behind `if TYPE_CHECKING:` and added `from __future__ import annotations`, so a future pchandler drop/rename can no longer break importing the whole projection module (which also ships Spherical/Orthographic). Resolves the pending Phase-1 IN-03 todo (T-04-D1).
- Synced `features/__init__.py` `__all__` to every registered non-rrim feature (added Sobel, Sum, Square, Root, Norm, ClipPercentile, MultiScaleGradient, OcclusionAwareMultiScaleGradient); RRIM features stay out of the barrel to preserve the opt-in gate.
- Deleted the dead first `convert_to_image` definition in `util.py` that referenced an unimported `plt` (NameError if reached), keeping only the live keyword-only version.

## Task Commits

1. **Task 1: Repair or delete the broken make_generator factory** - `6714214` (fix)
2. **Task 2: Guard the private _TransformArray import behind TYPE_CHECKING** - `29d1a38` (fix)
3. **Task 3: Sync features/__init__ __all__ and delete dead convert_to_image** - `9d74e6e` (fix)

## Files Created/Modified
- `src/pc2img/registry.py` - Removed the broken `make_generator` factory and its now-unused imports; module reduced to a documenting comment, still importable.
- `src/pc2img/strategies/projection.py` - Added `from __future__ import annotations`; moved `_TransformArray` import under `if TYPE_CHECKING:`; annotation at `PerspectiveProjection.__init__` now evaluates lazily.
- `src/pc2img/features/__init__.py` - `__all__` and imports synced to the full registered non-rrim feature set.
- `src/pc2img/util.py` - Deleted the dead positional-arg `convert_to_image`; single live keyword-only definition remains.

## Decisions Made
- Deleted `make_generator` rather than repairing it — grep confirmed zero callers in `src/`, `tests/`, `scripts/`, making deletion the lower-churn correct path.
- Chose `from __future__ import annotations` (module-wide lazy annotations) over per-annotation string quoting for projection.py, per the plan's preferred option (a).
- Excluded RRIM features from the barrel deliberately (opt-in registration gate).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. The initial `python -c` verification failed only because the system interpreter lacks the package; re-ran through the project venv (`.venv/bin/python`) and all checks passed.

## Self-Check: PASSED
- FOUND: src/pc2img/registry.py, src/pc2img/strategies/projection.py, src/pc2img/features/__init__.py, src/pc2img/util.py
- FOUND commits: 6714214, 29d1a38, 9d74e6e
- Test suite: 16 passed / 14 xfailed (no regression from the post-04-01 baseline)

## Next Phase Readiness
- Four edited source files are clean and importing, ready for the 04-04 ruff format sweep to reformat them.
- Pending Phase-1 IN-03 todo (guard `_TransformArray`) is now resolved and can be moved to completed.

---
*Phase: 04-code-quality-algorithmic-soundness-review*
*Completed: 2026-07-10*
