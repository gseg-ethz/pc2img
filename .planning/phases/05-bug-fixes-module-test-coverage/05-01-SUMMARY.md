---
phase: 05-bug-fixes-module-test-coverage
plan: 01
subsystem: testing
tags: [pytest, conftest, fixtures, pchandler, numpy, synthetic-data]

# Dependency graph
requires:
  - phase: 04-review-hygiene
    provides: "D-11 decision (synthetic runtime fixtures, no committed binaries) and the xfail-first proving-test convention"
provides:
  - "Shared tests/conftest.py fixture factory (synthetic_pcd, fetch_stub, fake_projection)"
  - "Lifted DummyProjection / DummyInterpolation / FakeProjection duck stubs + make_point_cloud / make_synthetic_pcd helpers as one shared source"
  - "Collection smoke test proving every advertised fixture resolves"
affects: [test_projection, test_interpolation, test_derivative_features, test_feature_registry, test_manager, test_tiled_generator, test_util, test_image_store]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Factory-fixture pattern: fixtures return a callable so each test parameterises its own synthetic PCD / fetch table"
    - "Deterministic synthetic PointCloudData(Nx3) from a seeded numpy Generator — no committed binary fixtures (D-11)"

key-files:
  created:
    - "tests/conftest.py"
    - "tests/test_conftest_smoke.py"
  modified: []

key-decisions:
  - "synthetic_pcd and fetch_stub are factory fixtures (return callables) so a single fixture serves every point count / raster-name table without re-parametrising the fixture itself"
  - "Added FakeProjection (all-points-valid, coords from xyz[:, :2]) alongside the lifted all-masked DummyProjection so projection tests get a usable 4-tuple without a heavy real strategy"
  - "Did not migrate test_point_cloud_image_generator.py to consume the lifted stubs — kept per non-interference scope; the shared source now exists for future waves to adopt"

patterns-established:
  - "Factory fixture returning a builder callable (synthetic_pcd, fetch_stub)"
  - "Seeded-numpy deterministic synthetic data in place of committed fixture blobs"

requirements-completed: [TEST-03, TEST-04, TEST-05, TEST-06]

coverage:
  - id: D1
    description: "synthetic_pcd factory builds a deterministic PointCloudData(Nx3) with optional scalar_fields"
    requirement: "TEST-05"
    verification:
      - kind: unit
        ref: "tests/test_conftest_smoke.py#test_synthetic_pcd_builds_requested_point_count"
        status: pass
      - kind: unit
        ref: "tests/test_conftest_smoke.py#test_synthetic_pcd_is_deterministic"
        status: pass
      - kind: unit
        ref: "tests/test_conftest_smoke.py#test_synthetic_pcd_attaches_scalar_fields"
        status: pass
    human_judgment: false
  - id: D2
    description: "fetch_stub returns a dict-backed fetch callable resolving rasters by name for compute(_, fetch)"
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_conftest_smoke.py#test_fetch_stub_returns_supplied_array_by_name"
        status: pass
    human_judgment: false
  - id: D3
    description: "fake_projection duck stub returns the full project_raw 4-tuple contract"
    requirement: "TEST-03"
    verification:
      - kind: unit
        ref: "tests/test_conftest_smoke.py#test_fake_projection_returns_four_tuple"
        status: pass
    human_judgment: false
  - id: D4
    description: "Full test suite still collects with the new conftest present (no name collisions, no import-time side effects)"
    requirement: "TEST-06"
    verification:
      - kind: integration
        ref: "pytest tests/ --collect-only -q (36 collected, 0 errors)"
        status: pass
    human_judgment: false

# Metrics
duration: 12min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 01: conftest Synthetic Fixture Factory Summary

**Shared tests/conftest.py providing seeded synthetic PointCloudData, a dict-backed fetch stub, and a duck-typed projection — the Wave-1 foundation every Phase-5 proving test depends on, with zero committed binary fixtures (D-11).**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-11
- **Completed:** 2026-07-11
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments
- `synthetic_pcd` factory fixture builds a deterministic real `pchandler.PointCloudData(Nx3)` from a seeded numpy Generator, with optional `scalar_fields=` attachment (explicit arrays or seeded synthesis via a `None` value).
- `fetch_stub` factory fixture returns a dict-backed `Callable[[str], NDArray]` mirroring the `compute(_, fetch)` dependency-resolution contract used by derivative / DSL features.
- `fake_projection` fixture returns a duck-typed `ProjectionStrategy` whose `project_raw` yields the full `(coords (M,2), mask (N,), mins (2,), maxs (2,))` 4-tuple.
- Lifted `DummyProjection` / `DummyInterpolation` + `make_point_cloud` from `test_point_cloud_image_generator.py` into shared conftest source, plus a new `FakeProjection` / `make_synthetic_pcd` helper.
- Added `tests/test_conftest_smoke.py` proving every advertised fixture resolves; full suite collects (36 tests, 0 errors) and runs green (25 passed, 11 xfailed) with the pre-existing suite status unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author tests/conftest.py synthetic fixture factory (D-11)** — `d5067fa` (test)
2. **Task 2: Collection smoke — fixtures resolve and suite still collects** — `37ee892` (test)

**Plan metadata:** committed separately (docs: complete plan)

## Files Created/Modified
- `tests/conftest.py` — shared synthetic fixture factory: `synthetic_pcd`, `fetch_stub`, `fake_projection` fixtures + `DummyProjection` / `DummyInterpolation` / `FakeProjection` stubs + `make_point_cloud` / `make_synthetic_pcd` helpers.
- `tests/test_conftest_smoke.py` — collection smoke asserting fixture resolution, PCD point count / determinism / scalar-field attachment, fetch-by-name, and the projection 4-tuple shape.

## Decisions Made
- **Factory fixtures over value fixtures:** `synthetic_pcd` and `fetch_stub` return callables so each test parametrises its own point count / raster table without re-defining the fixture. This matches the D-11 recommendation (`synthetic_pcd(n=…, with_scalar_fields=…)`) and keeps one fixture reusable across all waves.
- **Added `FakeProjection` alongside the lifted `DummyProjection`:** `DummyProjection` masks every point out (irrelevant-output stand-in); `FakeProjection` keeps all points and derives coords from `xyz[:, :2]`, giving projection tests a well-formed, usable 4-tuple where a full projection strategy would be heavy.
- **Did not migrate the existing `test_point_cloud_image_generator.py`** to consume the lifted stubs — Task 2 explicitly scoped this plan to non-interference. The shared source now exists; adoption is left to later waves.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff-format the new conftest.py to keep the tests/ format-hygiene gate green**
- **Found during:** Task 2 (full-suite collection/run check)
- **Issue:** `test_hygiene.py::test_ruff_check_src_is_clean` shells `ruff format --check src/ tests/`, which now covers the newly created `tests/conftest.py`. Two exception-message lines exceeded ruff's format width, tripping the gate (1 pre-existing-green hygiene test flipped to fail — caused directly by this plan's new file).
- **Fix:** Ran `ruff format tests/conftest.py` (collapsed two multi-line `raise` statements to single lines). No logic change.
- **Files modified:** tests/conftest.py
- **Verification:** `ruff format --check src/ tests/` → "27 files already formatted"; full suite → 25 passed, 11 xfailed, 0 failed.
- **Committed in:** `37ee892` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The format fix was required to keep the pre-existing hygiene gate green; the failure was introduced by this plan's own new file. No scope creep.

## Issues Encountered
- The project `pchandler` / `GSEGUtils` are only importable inside `.venv`; used `.venv/bin/python` for all verification and test runs. No code impact.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Wave-1 fixture foundation is in place: `synthetic_pcd`, `fetch_stub`, `fake_projection` are consumable by Wave-2/3 test authoring (TEST-03..06) and every proving-test flip.
- No committed binary fixtures; deterministic construction confirmed (D-11 satisfied).
- No blockers for downstream Phase-5 plans.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*

## Self-Check: PASSED
- FOUND: tests/conftest.py
- FOUND: tests/test_conftest_smoke.py
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-01-SUMMARY.md
- FOUND commit d5067fa (Task 1)
- FOUND commit 37ee892 (Task 2)
