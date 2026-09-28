---
created: 2026-07-09T03:55:38.537Z
title: Guard module-level private pchandler _TransformArray import in projection.py
area: general
resolves_phase: 4
files:
  - src/pc2img/strategies/projection.py:12
source: .planning/phases/01-branch-untangling-mainline-consolidation/01-REVIEW.md (IN-03)
---

## Problem

The `PerspectiveProjection` strategy folded onto the mainline in Phase 1 imports a
**private, underscore-prefixed** pchandler symbol at **module scope**:
`from pchandler.geometry.transforms import _TransformArray` (projection.py:12).

Because the import is module-level, if a future pchandler release drops or renames
`_TransformArray`, `import pc2img.strategies.projection` fails outright — which takes the
working `SphericalProjection` and `OrthographicProjection` strategies down with it, not just
the WIP perspective path. A single private-API change in a sibling dep would break importing
the projection module entirely.

Surfaced as finding IN-03 (Info) in the Phase 1 code review; it was classified Info because
the perspective math itself is D-03-fenced (deferred to Phase 4 soundness / Phase 5 tests).
This todo carries the *import-fragility* concern forward so it is not lost when that WIP is
completed.

## Solution

When the perspective math is worked in Phase 4, make the `_TransformArray` dependency
non-fatal to the rest of the module. Options (TBD — pick during Phase 4):
- Move the import method-local (inside `PerspectiveProjection.project*`) so it only fails
  when the perspective strategy is actually used, not on module import.
- Guard it (`try/except ImportError`) and degrade the perspective strategy gracefully
  (e.g. raise a clear error only on use) while leaving spherical/orthographic importable.
- Coordinate with pchandler (requires human approval per project constraints) to expose a
  public equivalent of `_TransformArray`, removing the private-API reliance entirely.

## Resolved (verified 2026-09-28)

The import is guarded under `TYPE_CHECKING` in `src/pc2img/strategies/projection.py` (Phase 4/5 work). Closed during Phase 6 discuss.
