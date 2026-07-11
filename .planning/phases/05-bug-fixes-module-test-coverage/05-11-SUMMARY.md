---
phase: 05-bug-fixes-module-test-coverage
plan: 11
subsystem: testing
tags: [feature-manager, orchestration, pydantic, lazy-disk-cache, dependency-graph, pytest]

# Dependency graph
requires:
  - phase: 05-01
    provides: shared tests/conftest.py synthetic_pcd factory + duck-typed strategy stubs
  - phase: 05-09
    provides: image_cache→GSEGUtils DiskBackedImageStore consolidation the manager caches into
provides:
  - "FeatureManager.request() resets _base_features per call (no stale-spec accumulation on generator reuse)"
  - "Visited-set dependency-cycle guard raising ValueError('dependency cycle: ...') instead of RecursionError"
  - "None-sentinel default for FeatureManager.lazy_disk_cache_config (no shared mutable config)"
  - "PointCloudImageGenerator coerces an OMITTED lazy_disk_cache_config so store construction succeeds"
  - "tests/test_manager.py — TEST-05 orchestration sensors for DSN-04/DSN-07/DSN-08"
affects: [orchestration, feature-manager, tiled-generator, verify-work]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "None-sentinel + `or LazyDiskCacheConfig()` default at the manager site (matches core.py / tiled_generator sites)"
    - "DFS recursion-stack (visited-set with backtracking) cycle guard: only active-path re-entry is a cycle, sibling diamonds are not"
    - "Body-level idempotent coerce for pydantic @validate_call defaults that the BeforeValidator never sees (omitted args)"
    - "Teardown-scoped throwaway feature registration in a fixture (register → yield → FEATURES._map.pop) so cycle tests never pollute the global registry"

key-files:
  created:
    - tests/test_manager.py
  modified:
    - src/pc2img/features/manager.py
    - src/pc2img/core.py
    - tests/test_point_cloud_image_generator.py
    - .planning/phases/05-bug-fixes-module-test-coverage/deferred-items.md

key-decisions:
  - "DSN-07 sensor asserts the __init__ signature default IS the None sentinel (config is decomposed by DiskBackedStore and never retained, so post-construction object identity is not observable; the frozen-dataclass config also makes stores get independent temp dirs regardless — the signature default is the only robust, discriminating proof)"
  - "DSN-07 uses `or LazyDiskCacheConfig()` (not coerce_lazy_cfg) to match the tiled_generator site and avoid a circular import: coerce_lazy_cfg lives in top-level core.py, which imports FeatureManager"
  - "DSN-06 fixed in core.py body via idempotent coerce_lazy_cfg(lazy_disk_cache_config): a provided value is already coerced by the BeforeValidator, an omitted default reaches the body as None and is coerced there"
  - "Cycle guard discards each node on exit (backtracking) so it flags only recursion-stack back-edges, not diamond dependencies reached via independent sibling paths"

patterns-established:
  - "Pattern: None-sentinel config default at every generator/manager construction site (consistency note D-02/D-17)"
  - "Pattern: DFS recursion-stack cycle guard for the feature dependency graph"

requirements-completed: [BUG-05, TEST-05]

coverage:
  - id: D1
    description: "FeatureManager.request() resets _base_features so successive requests do not accumulate stale specs (DSN-04)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_manager.py#test_request_twice_does_not_accumulate_base_features"
        status: pass
    human_judgment: false
  - id: D2
    description: "A cyclic feature dependency graph raises a clear ValueError('dependency cycle: ...') instead of RecursionError (DSN-08)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_manager.py#test_dependency_cycle_raises_valueerror_not_recursionerror"
        status: pass
    human_judgment: false
  - id: D3
    description: "FeatureManager.lazy_disk_cache_config uses the None-sentinel default (no shared mutable LazyDiskCacheConfig()) (DSN-07)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_manager.py#test_default_config_uses_none_sentinel"
        status: pass
    human_judgment: false
  - id: D4
    description: "An omitted lazy_disk_cache_config is coerced so PointCloudImageGenerator constructs a usable cache store (DSN-06 — flips the existing xfail)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_point_cloud_image_generator.py#test_constructor_normalizes_omitted_lazy_disk_cache_config"
        status: pass
    human_judgment: false
  - id: D5
    description: "FeatureManager orchestration path covered by tests/test_manager.py (TEST-05)"
    requirement: "TEST-05"
    verification:
      - kind: unit
        ref: "pytest tests/test_manager.py -q (3 passed)"
        status: pass
    human_judgment: false

# Metrics
duration: 4min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 11: FeatureManager Orchestration Fixes + Coverage Summary

**Fixed four FeatureManager/core orchestration findings (stale base-feature accumulation, unbounded dependency-cycle recursion, mutable-default config, omitted-config coercion) and added the TEST-05 manager sensor suite — full suite 109 passed / 0 xfailed.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-11T05:26:45Z
- **Completed:** 2026-07-11T05:31:14Z
- **Tasks:** 2
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments
- DSN-04: `FeatureManager.request()` now resets `_base_features` per call, so a reused generator no longer recomputes stale accumulated base specs.
- DSN-08: added a DFS recursion-stack visited-set guard that raises `ValueError("dependency cycle: <name>")` on a cyclic feature graph instead of recursing into a `RecursionError`.
- DSN-07: replaced the shared mutable `LazyDiskCacheConfig()` default at the manager site with the `None`-sentinel pattern, consistent with the `core.py` / `tiled_generator` sites.
- DSN-06: `PointCloudImageGenerator` now coerces an omitted `lazy_disk_cache_config` in the constructor body, flipping the pre-existing generator xfail to a passing test (omitted and explicit-`None` paths now behave identically).
- TEST-05: new `tests/test_manager.py` covers the manager orchestration path with three sensors; DSN-08's self-cyclic feature is registered in a teardown-scoped fixture so the global registry is never polluted.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author DSN-04/DSN-08/DSN-07 proving tests (xfail); confirm DSN-06 xfail sensor** - `804bf65` (test)
2. **Task 2: Fix DSN-04/DSN-08/DSN-07 (manager.py) and DSN-06 (core.py); flip sensors** - `0658181` (fix)

_Note: Task 1 authored the sensors xfail-first per D-12; Task 2 landed the fixes and flipped them to passing._

## Files Created/Modified
- `tests/test_manager.py` - TEST-05 manager sensors (DSN-04 accumulation, DSN-08 cycle guard, DSN-07 None-sentinel identity) + teardown-scoped self-cyclic feature fixture.
- `src/pc2img/features/manager.py` - `_base_features` reset per `request()`; visited-set cycle guard in `visit()`; None-sentinel `lazy_disk_cache_config` default.
- `src/pc2img/core.py` - `PointCloudImageGenerator.__init__` coerces the (possibly omitted) `lazy_disk_cache_config` via idempotent `coerce_lazy_cfg`.
- `tests/test_point_cloud_image_generator.py` - dropped the DSN-06 xfail marker (now passing) and the now-unused `pytest` import.
- `.planning/phases/05-bug-fixes-module-test-coverage/deferred-items.md` - logged the pre-existing `spec.cls`-Optional pyright items in manager.py.

## Decisions Made
- **DSN-07 sensor via signature introspection.** `DiskBackedStore` decomposes the config into scalar fields and never retains the object, and `LazyDiskCacheConfig` is a frozen dataclass (so each store gets an independent temp cache_dir regardless of sharing). Post-construction config identity is therefore unobservable, so the sensor asserts the `__init__` signature default IS the `None` sentinel — the only robust, discriminating proof of the fix.
- **DSN-07 uses `or LazyDiskCacheConfig()`, not `coerce_lazy_cfg`.** `coerce_lazy_cfg` lives in top-level `core.py`, which imports `FeatureManager`; importing it into `manager.py` would create a circular import. The `or`-sentinel form matches the tiled_generator site exactly.
- **DSN-06 fixed in the constructor body.** Pydantic's `@validate_call` never runs the `BeforeValidator` on a default value, so an omitted arg reaches the body as `None`. A body-level idempotent `coerce_lazy_cfg` handles the omitted case while leaving provided (already-coerced) values untouched.

## Deviations from Plan

None - plan executed exactly as written. Both tasks and all four findings (DSN-04/06/07/08) landed as specified, sensors authored xfail-first then flipped.

## Issues Encountered
- **Pre-existing pyright errors in manager.py (out of scope).** Three `spec.cls`-Optional errors (`reportArgumentType` on `issubclass`, two `reportOptionalCall` on `spec.cls(**...)`) exist at HEAD before this plan — confirmed by running pyright on the pre-edit file (same 3 errors, only line numbers shifted). Not introduced or touched by the DSN fixes; logged to `deferred-items.md` as a candidate for a `FeatureSpec.cls` typing-narrow pass. Not fixed here per the scope boundary.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Manager/orchestration findings for Phase 5 are resolved and covered; contributes to ROADMAP SC5 (orchestration covered).
- Full suite green: **109 passed, 0 xfailed** (was 105 passed / 1 xfailed — the DSN-06 xfail flipped and three manager sensors added).
- 05-12 is the remaining phase plan.

## Self-Check: PASSED

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*
