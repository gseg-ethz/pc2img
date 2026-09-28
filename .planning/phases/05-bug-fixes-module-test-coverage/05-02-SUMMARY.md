---
phase: 05-bug-fixes-module-test-coverage
plan: 02
subsystem: strategies
tags: [projection, perspective, orthographic, spherical, pchandler, pinhole-camera, numpy, pytest]

# Dependency graph
requires:
  - phase: 05-01
    provides: tests/conftest.py synthetic_pcd / fake_projection fixture factory
  - phase: 04
    provides: 04-FINDINGS.md canonical M-01..M-05 findings; TYPE_CHECKING-guarded _TransformArray annotation
provides:
  - OrthographicProjection.project_raw correct 4-tuple arity + rows-then-columns column indexing (BUG-01)
  - OrthographicProjection.inverse_projection documented refusal (class was previously abstract/uninstantiable)
  - _reject_wrapping_fov module-level seam guard shared by both SphericalProjection methods (D-15)
  - PerspectiveProjection full pinhole K·(R·X+t) with camera translation, behind-camera depth cull, and eager rotation validation
  - tests/test_projection.py — TEST-03 projection sensors (15 tests)
affects: [projection, tiled_generator, core, downstream-BC]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Extrinsic-first perspective projection: build Transform.generate([R|t]) and apply via the pchandler `Transform @ pcd` matmul contract, then apply K + manual perspective divide (never (K@extrinsic)@pcd)"
    - "Shared module-level guard helper (_reject_wrapping_fov) keeping a forward/inverse method pair in sync behind a single message source"
    - "Documented NotImplementedError refusal to satisfy an ABC where the two-phase contract does not apply, instead of deleting an abstractmethod override"

key-files:
  created:
    - tests/test_projection.py
  modified:
    - src/pc2img/strategies/projection.py

key-decisions:
  - "M-04 'delete the dead project_raw override' adapted to a documented NotImplementedError refusal — deleting it would leave project_raw abstract on the base and make PerspectiveProjection uninstantiable (04-FINDINGS M-04 sanctions this alternative)"
  - "OrthographicProjection gained an inverse_projection documented refusal: it was missing the abstract method entirely and could never be instantiated (pre-existing latent blocker surfaced by M-01 tests)"
  - "Orthographic mins/maxs derived from the ROI box when supplied, else the kept-point extent (per plan)"

patterns-established:
  - "Extrinsic-first pinhole projection via pchandler Transform @ pcd"
  - "xfail-first proving tests flipped to passing asserts per finding (D-12)"

requirements-completed: [BUG-01, BUG-05, TEST-03]

coverage:
  - id: D1
    description: "OrthographicProjection returns (pts2d (M,2), mask (N,)) with in-range pixel coords equal to normalized xyz[mask][:, cols] for xy/yz/xz — not a diagonal (BUG-01 / ROADMAP SC1)"
    requirement: "BUG-01"
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_orthographic_project_columns_and_arity"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_orthographic_project_raw_returns_4_tuple"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_orthographic_roi_box_masks_and_normalizes"
        status: pass
    human_judgment: false
  - id: D2
    description: "SphericalProjection refuses a wrapping (crosses_pi) FoV in both project_raw and inverse_projection with NotImplementedError (M-05/D-15)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_spherical_project_raw_rejects_wrapping_fov"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_spherical_inverse_rejects_wrapping_fov"
        status: pass
    human_judgment: false
  - id: D3
    description: "PerspectiveProjection masks behind-camera (Z_c<=0) points and applies K·(R·X+t) via translation=; a 4×4 rotation_matrix raises TypeError, a non-orthonormal 3×3 raises ValueError (M-02/M-03/M-03b)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_masks_behind_camera"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_applies_translation"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_rejects_4x4_rotation"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_rejects_non_orthonormal_rotation"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_translation_survives_registry_coercion"
        status: pass
    human_judgment: false
  - id: D4
    description: "TEST-03 projection sensors: orthographic + spherical happy-path breadth coverage; perspective project() via documented @pcd matmul contract with documented project_raw refusal (M-04)"
    requirement: "TEST-03"
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_spherical_project_happy_path"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_spherical_inverse_roundtrip_shapes"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_project_raw_is_documented_refusal"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-11
status: complete
---

# Phase 5 Plan 02: strategies/projection.py correctness fixes Summary

**Fixed all five projection.py findings — orthographic 4-tuple arity + column indexing (BUG-01), a shared wrapping-FoV seam guard on both spherical methods (D-15), and the perspective cluster upgraded to the full pinhole `K·(R·X+t)` with a behind-camera depth cull and eager 3×3-rotation validation — with a new 15-test TEST-03 projection sensor file.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-11T04:04:33Z
- **Completed:** 2026-07-11T04:10:21Z
- **Tasks:** 3
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- OrthographicProjection now returns the 4-tuple `(coords, mask, mins, maxs)` the base `project()` unpacks and selects plane columns rows-then-columns (`xyz[mask][:, cols]`), ending the silent-diagonal bug; ROI/extent-based `mins`/`maxs` make span normalization correct (BUG-01 / ROADMAP SC1).
- Added `_reject_wrapping_fov` — a module-level helper raising `NotImplementedError` on `crosses_pi` FoVs — called from both `SphericalProjection.project_raw` (guards user FoV and `pcd.fov`) and `inverse_projection`, converting silent reversed-columns into an explicit refusal (M-05/D-15).
- Rebuilt `PerspectiveProjection` to the pinned `<perspective_api_contract>`: keyword-only `translation`, extrinsic-first `Transform.generate([R|t]) @ pcd` application, behind-camera `Z_c ≤ 0` depth cull (M-02), full `K·(R·X+t)` model (M-03), eager rotation validation (4×4 → TypeError, non-orthonormal → ValueError; M-03b), and a documented `project_raw` refusal replacing the undocumented `@pcd`/`.arr` dead path (M-04).
- New `tests/test_projection.py` (15 tests) authored xfail-first (D-12) then flipped to passing asserts per finding; full suite 40 passed / 11 xfailed (the xfails belong to other plans).

## Task Commits

Each task was committed atomically:

1. **Task 1: Author failing proving tests (xfail-first)** - `6e48f0f` (test)
2. **Task 2: Fix M-01 (orthographic arity + indexing) and M-05 (spherical seam guard)** - `de53903` (fix)
3. **Task 3: Fix perspective cluster M-02 + M-03 + M-04** - `b148ad6` (fix)

_Note: Task 1 is the TDD RED commit; Tasks 2 and 3 are the GREEN commits that flip the xfail markers._

## Files Created/Modified
- `tests/test_projection.py` - TEST-03 projection sensors: orthographic arity/indexing/ROI, spherical happy-path + seam guard, perspective depth-cull/translation/validation/registry-coercion, and M-04 documented-refusal.
- `src/pc2img/strategies/projection.py` - `_reject_wrapping_fov` helper; orthographic 4-tuple + column-slice fix + inverse refusal; perspective rewrite (translation, extrinsic-first, depth cull, validation, docstring).

## Decisions Made
- **M-04 documented-refusal instead of deletion.** The plan/patterns said "delete the dead `project_raw` override," but `project_raw` is an `@abstractmethod` on `ProjectionStrategy`; removing the override leaves it abstract and makes `PerspectiveProjection` uninstantiable (verified: `TypeError: Can't instantiate abstract class`). 04-FINDINGS M-04 explicitly sanctions the alternative ("either remove `project_raw` OR make it a clear `NotImplementedError` with rationale"), so it is now a documented refusal explaining the class projects in one shot via `project()`.
- **Orthographic `inverse_projection` added.** `OrthographicProjection` never implemented the abstract `inverse_projection`, so it was uninstantiable — a latent pre-existing blocker that M-01's proving tests surfaced. Added a documented `NotImplementedError` (orthographic drops the out-of-plane axis, so a raster cannot be lifted back to 3D).
- **Camera-frame convention `t = −R·C`** documented in the class docstring, matching pchandler `Transform.generate` (`x0 = (R·s + t) @ x1`); no `R·(X−C)` convention invented.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted M-04 from "delete project_raw" to a documented refusal**
- **Found during:** Task 3 (perspective cluster)
- **Issue:** Deleting the `project_raw` override — as the plan text literally directed — leaves `project_raw` abstract on the base `ProjectionStrategy`, so `PerspectiveProjection()` raises `TypeError: Can't instantiate abstract class` and every perspective test errors.
- **Fix:** Kept `project_raw` as a clear, documented `NotImplementedError` (the finding-sanctioned alternative) explaining the one-shot `project()` path; replaced the undocumented `@pcd`/`.arr` dead body with the rationale.
- **Files modified:** src/pc2img/strategies/projection.py
- **Verification:** `test_perspective_project_raw_is_documented_refusal` + all perspective tests pass.
- **Committed in:** b148ad6 (Task 3 commit)

**2. [Rule 3 - Blocking] Added OrthographicProjection.inverse_projection (class was uninstantiable)**
- **Found during:** Task 2 (M-01 fix)
- **Issue:** `OrthographicProjection` never implemented the abstract `inverse_projection`, so instantiating it raised `TypeError: Can't instantiate abstract class ... 'inverse_projection'` — a pre-existing latent bug that blocked every orthographic proving test.
- **Fix:** Added a documented `NotImplementedError` (orthographic projection is non-invertible — it discards the out-of-plane coordinate).
- **Files modified:** src/pc2img/strategies/projection.py
- **Verification:** All orthographic tests instantiate and pass.
- **Committed in:** de53903 (Task 2 commit)

**3. [Rule 3 - Blocking] Formatted test file to satisfy the ruff-format hygiene gate**
- **Found during:** Task 2 (post-fix full-suite run)
- **Issue:** `tests/test_hygiene.py::test_ruff_check_src_is_clean` runs `ruff format --check src/ tests/`; the new `test_projection.py` was not yet ruff-formatted, failing the gate.
- **Fix:** `ruff format tests/test_projection.py` (+ ran on the source file); `ruff check` clean.
- **Files modified:** tests/test_projection.py
- **Verification:** `ruff format --check` reports "already formatted"; hygiene gate passes.
- **Committed in:** de53903 / b148ad6 (task commits)

---

**Total deviations:** 3 auto-fixed (all Rule 3 - blocking)
**Impact on plan:** All three were necessary to make the code instantiable, correct, and land on green; no scope creep beyond the plan's five findings.

## Issues Encountered
- The plan's `test_spherical_inverse_roundtrip_shapes` breadth test initially used an invalid vertical FoV range (`bottom=-0.5`); pchandler enforces V ∈ [0, π], so it was corrected to a valid `top=0.5, bottom=1.5` before Task 1's commit.

## Breaking-Change Note (D-17 running note)
- **(a)** An untiled cloud whose resolved FoV wraps (`left > right`, `crosses_pi=True`) now RAISES `NotImplementedError` from `SphericalProjection.project_raw` / `inverse_projection` instead of silently producing reversed columns (D-15, accepted).
- **(b)** A 4×4 `rotation_matrix` passed to `PerspectiveProjection` now raises `TypeError` (was silently accepted as an affine extrinsic) — pass the camera translation via `translation=` instead. Batched into this already-breaking release with no runtime `DeprecationWarning` (the 4×4 path was never a documented contract).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `strategies/projection.py` correctness findings (M-01..M-05) are closed with proving tests; projection sensors (TEST-03) are green.
- Note for Phase 6: the Phase-4 pending todo to guard the module-level `_TransformArray` annotation remains open; this plan added a runtime `from pchandler.geometry.transforms import Transform` import (public class), so a future pchandler rename of `Transform` would now also affect the projection module — worth folding into that guard todo.

## Self-Check: PASSED

- Files verified on disk: `tests/test_projection.py`, `src/pc2img/strategies/projection.py`, `.planning/phases/05-bug-fixes-module-test-coverage/05-02-SUMMARY.md`
- Commits verified in git log: `6e48f0f`, `de53903`, `b148ad6`
- Full suite: 40 passed / 11 xfailed / 0 failed; ruff check + format-check clean.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*
