---
phase: 05-bug-fixes-module-test-coverage
plan: 10
subsystem: testing
tags: [tiled-generator, joblib, pydantic-dataclass, lazy-disk-cache, orchestration]

# Dependency graph
requires:
  - phase: 05-01
    provides: shared tests/conftest.py synthetic-fixture factory (D-11)
  - phase: 05-09
    provides: image_cache → GSEGUtils consolidation (stable cache-config surface)
provides:
  - "BUG-03/DSN-01 fix: TIGSettings.extend_cache_paths preserves interp_kwargs (no dict.update()→None trap)"
  - "DSN-10 fix: tiled_generator imports PointCloudImageGenerator from pc2img.core, not the package barrel"
  - "DSN-07 fix: None-sentinel default for lazy_disk_cache_config at the tiled_generator sites"
  - "tests/test_tiled_generator.py — TEST-05 tiled-orchestration sensors (deterministic, no process parallelism)"
affects: [tiled orchestration, 05-11, 05-12, milestone verification SC3/SC5]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "None-sentinel + 'or LazyDiskCacheConfig()' default (core.py / interpolation.py:141) applied consistently across DSN-07 sites"
    - "build-dict-then-assign for pydantic-dataclass replace() updates (never store dict.update()'s None return)"
    - "subprocess fresh-import guard (python -c 'import <submodule>') to prove barrel-cycle safety"

key-files:
  created:
    - tests/test_tiled_generator.py
  modified:
    - src/pc2img/tiled_generator.py

key-decisions:
  - "DSN-07 tiled sites use the lightweight 'or LazyDiskCacheConfig()' sentinel (interpolation.py:141 precedent) rather than a full coerce_lazy_cfg BeforeValidator, since the tiled path takes an already-typed config, not loose input"
  - "BUG-03 sensor written as strict=False xfail in the RED commit, then the marker removed (not inverted) in the GREEN commit"

patterns-established:
  - "Pattern: pydantic frozen-dataclass replace() updates build the child dict first, then assign — dict.update() returns None and nulls the field"
  - "Pattern: prove import-ordering safety with an out-of-process 'import submodule-first' subprocess check"

requirements-completed: [BUG-03, BUG-05, TEST-05]

coverage:
  - id: D1
    description: "extend_cache_paths preserves interp_kwargs as a dict with a path-extended LazyDiskCacheConfig (BUG-03/DSN-01)"
    requirement: BUG-03
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_extend_cache_paths_preserves_interp_kwargs"
        status: pass
    human_judgment: false
  - id: D2
    description: "tiled_generator imports cleanly when loaded first in a fresh interpreter (DSN-10 barrel-cycle guard)"
    requirement: BUG-05
    verification:
      - kind: integration
        ref: "tests/test_tiled_generator.py#test_tiled_generator_imports_first_in_fresh_interpreter"
        status: pass
    human_judgment: false
  - id: D3
    description: "DSN-07 None-sentinel default at the tiled_generator constructor sites (no shared mutable LazyDiskCacheConfig())"
    requirement: BUG-05
    verification:
      - kind: unit
        ref: "pytest tests/ -x -q (full suite green, 105 passed / 1 xfailed)"
        status: pass
    human_judgment: false

# Metrics
duration: 16min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 10: Tiled-generator findings + orchestration coverage Summary

**Fixed the silent per-tile interp_kwargs loss (BUG-03: `dict.update()`→None), removed the barrel-import fragility (DSN-10), applied the DSN-07 None-sentinel default at the tiled sites, and added deterministic TEST-05 tiled-orchestration sensors.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-07-11T05:04:00Z
- **Completed:** 2026-07-11T05:20:32Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- **BUG-03/DSN-01 (HIGH, silent config loss):** `TIGSettings.extend_cache_paths` now builds the extended `interp_kwargs` dict and assigns it, instead of storing `dict.update()` (which returns `None`). Under the bug, the frozen pydantic dataclass re-validated the `None` and raised `ValidationError` — so the per-tile interpolation kwargs were lost outright; now they are preserved with a path-extended nested `LazyDiskCacheConfig`.
- **DSN-10:** `tiled_generator` imports `PointCloudImageGenerator` from `pc2img.core` (the defining module) rather than the `pc2img` package barrel, removing partial-initialization import fragility. A subprocess fresh-import guard proves the submodule loads first without an `ImportError`.
- **DSN-07:** the two constructor default sites (`__init__` overload + impl) now use `lazy_disk_cache_config: ... | None = None` with an `or LazyDiskCacheConfig()` coercion, matching `core.py`, `manager.py`, and `interpolation.py:141` — no shared mutable default instance.
- **TEST-05:** new `tests/test_tiled_generator.py` covers the orchestration path with pure-object, CI-safe tests (no joblib/loky process parallelism). Full suite: **105 passed / 1 xfailed** (was 103 / 1).

## Task Commits

Each task was committed atomically (test-first per D-12):

1. **Task 1: Author failing BUG-03 + DSN-10 sensors (RED)** - `09f2513` (test)
2. **Task 2: Fix BUG-03 / DSN-10 / DSN-07 + flip xfail (GREEN)** - `fe0d8eb` (fix)

Supporting: **`b26bde5`** (docs) - logged pre-existing tiled_generator pyright items as deferred (out of scope).

## Files Created/Modified
- `tests/test_tiled_generator.py` (new) - TEST-05 tiled sensors: `test_extend_cache_paths_preserves_interp_kwargs` (BUG-03), `test_tiled_generator_imports_first_in_fresh_interpreter` (DSN-10).
- `src/pc2img/tiled_generator.py` - build-then-assign fix in `extend_cache_paths`; import from `pc2img.core`; None-sentinel default at the two constructor sites.

## Decisions Made
- **DSN-07 sentinel choice:** used the lightweight `... or LazyDiskCacheConfig()` sentinel (interpolation.py:141 in-file precedent) rather than a full `coerce_lazy_cfg` `BeforeValidator`. The tiled constructor already receives a validated `LazyDiskCacheConfig`, so the mapping-coercion arm of `coerce_lazy_cfg` is unneeded here; the sentinel keeps the site minimal while removing the shared mutable default. **D-17 running note:** DSN-07 is now consistent across `core.py` (BeforeValidator arm), `manager.py`, `image_cache` store, `interpolation.py:141`, and now `tiled_generator.py` — the mutable `LazyDiskCacheConfig()` default is eliminated everywhere.
- **BUG-03 manifested as `ValidationError`, not a silent `None`:** because `TIGSettings` is a frozen pydantic dataclass, `replace(self, interp_kwargs=None)` re-validated and raised rather than storing `None`. Either way the per-tile kwargs were lost; the proving test asserts the post-fix contract (dict with a nested `LazyDiskCacheConfig`) and the `strict=False` xfail captured the raise in the RED phase.

## Deviations from Plan

None - plan executed exactly as written. (One out-of-scope discovery was logged, not fixed — see below.)

## Issues Encountered
- **Pre-existing pyright errors in `tiled_generator.py` (out of scope):** pyright reports 6 errors — one `reportInconsistentOverload` on `__init__` (intentional loose-overload / `@validate_call`-narrowed-impl pydantic pattern) and three `reportOptionalSubscript` in `generate()` (joblib `Parallel()(...)` is typed as possibly `None`). Confirmed present at HEAD before this plan's edits by running pyright on the pre-edit file (identical 6 errors), so my changes introduced **zero** new type errors. Logged to `deferred-items.md`; SCOPE BOUNDARY keeps them for a future typing pass.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Milestone SC3 (BUG-03 proven) and SC5 (tiled orchestration covered) advanced.
- Tiled path is now barrel-cycle-safe and free of shared mutable cache-config defaults; ready for 05-11 / 05-12.
- No blockers. Deferred: tiled_generator typing cleanup (pre-existing pyright items) if the orchestration path is revisited.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*

## Self-Check: PASSED
- FOUND: tests/test_tiled_generator.py
- FOUND: src/pc2img/tiled_generator.py
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-10-SUMMARY.md
- FOUND commits: 09f2513 (test), fe0d8eb (fix), b26bde5 (docs/deferred)
