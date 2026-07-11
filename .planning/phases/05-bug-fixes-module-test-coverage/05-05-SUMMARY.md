---
phase: 05-bug-fixes-module-test-coverage
plan: 05
subsystem: testing
tags: [delaunay, interpolation, barycentric, scipy, numpy, characterization-test, kept-behavior]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: shared tests/conftest.py synthetic-fixture factory (05-01)
provides:
  - "tests/test_interpolation.py — TEST-03 interpolation sensors (M-06 characterization + scipy oracle + barycentric pin)"
  - "Opt-in Delaunay culling-threshold kwargs (interior_culling / area_scale / aspect_ratio_mad_factor / aspect_ratio_fallback_scale) with byte-identical defaults"
affects: [05-06, 05-07, 05-09, 05-10, 05-11, 05-12, verify-work, D-17-running-note]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Held-out oracle testing: scipy.LinearNDInterpolator (NaN iff outside convex hull) as ground truth for the culling-disabled path"
    - "Characterization test pins DELIBERATE behavior (M-06) rather than 'fixing' it — Pitfall 5"
    - "Opt-in kwargs whose defaults reproduce prior hardcoded constants byte-for-byte (PERF-03 / D-06)"

key-files:
  created:
    - tests/test_interpolation.py
  modified:
    - src/pc2img/strategies/interpolation.py

key-decisions:
  - "M-06 kept as default (D-06): interior culling is intentional, downstream-validated; only surfaced as tunable knobs, no behavior change"
  - "Culling constants (median-area x10, aspect median+6*MAD, x10 fallback) become area_scale=10.0 / aspect_ratio_mad_factor=6.0 / aspect_ratio_fallback_scale=10.0 defaults"
  - "interior_culling=False admits every in-hull triangle, reproducing scipy.LinearNDInterpolator NaN placement (oracle path)"
  - "Dead max_edge_thresh=None branch dropped (never culled); max_edge still computed but unused (kept minimal diff)"

patterns-established:
  - "Pattern 1: scipy interpolator as held-out NaN-placement oracle for the culling-disabled interpolation path"
  - "Pattern 2: byte-identity regression guard — default vs explicit-default construction compared with assert_array_equal (NaN-aware)"

requirements-completed: [BUG-05, TEST-03]

coverage:
  - id: D1
    description: "M-06 interior-culling kept-behavior pinned: default Delaunay stamps extra interior NaNs over a data-gap hole that scipy fills"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_interior_culling_stamps_extra_nans_inside_hull"
        status: pass
    human_judgment: false
  - id: D2
    description: "Delaunay barycentric weights (CONFIRMED-CORRECT) reproduce a linear field to ~1e-13"
    requirement: "TEST-03"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_barycentric_reproduces_linear_field_within_tolerance"
        status: pass
    human_judgment: false
  - id: D3
    description: "Culling-disabled Delaunay NaN placement matches scipy.LinearNDInterpolator oracle (NaN iff outside hull)"
    requirement: "TEST-03"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_culling_disabled_matches_scipy_oracle_over_hole"
        status: pass
      - kind: unit
        ref: "tests/test_interpolation.py#test_uniform_grid_matches_scipy_oracle_nan_placement"
        status: pass
    human_judgment: false
  - id: D4
    description: "Opt-in culling thresholds: explicit defaults are byte-identical to the default constructor (PERF-03 / D-06)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_interpolation.py#test_explicit_default_thresholds_reproduce_default_output"
        status: pass
      - kind: unit
        ref: "tests/test_interpolation.py#test_invalid_threshold_params_raise"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 05: Delaunay Interpolation Coverage + M-06 Threshold Parameterization Summary

**M-06 interior-culling pinned as kept-behavior with a scipy.LinearNDInterpolator held-out oracle, and the culling thresholds surfaced as opt-in kwargs whose defaults reproduce today's output byte-for-byte.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-11T04:27:00Z
- **Completed:** 2026-07-11T04:33:18Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- New `tests/test_interpolation.py` (pure-array, deterministic) covering interpolation math: M-06 characterization, scipy oracle NaN-placement on both congruent and holed grids, and the CONFIRMED-CORRECT barycentric linear-field reproduction (~1e-13).
- `DelaunayInterpolation` now exposes `interior_culling`, `area_scale`, `aspect_ratio_mad_factor`, and `aspect_ratio_fallback_scale` kwargs (opt-in; PERF-03 / D-06) with eager `ValueError` validation.
- Defaults verified byte-identical against a faithful reproduction of the original hardcoded culling logic — zero behavior change.
- `interior_culling=False` wired as the oracle path: admits every in-hull triangle, matching `scipy.LinearNDInterpolator` NaN placement exactly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author M-06 characterization + barycentric oracle tests** - `d793331` (test)
2. **Task 2: Expose Delaunay culling thresholds as opt-in params** - `67315f4` (feat)

**Plan metadata:** _(this commit)_ (docs: complete plan)

## Files Created/Modified
- `tests/test_interpolation.py` - TEST-03 sensors: characterization (holed grid), scipy oracle (uniform + culling-disabled), barycentric pin, param validation.
- `src/pc2img/strategies/interpolation.py` - Added opt-in culling-threshold kwargs + validation; wrapped the culling block in `interior_culling`; replaced hardcoded `10` / `6` / `10` constants with the new params (defaults unchanged).

## Decisions Made
- Kept M-06 as the default (D-06): the interior-culling heuristic is deliberate and downstream-validated; this plan only makes it tunable and pins it with a characterization test — it does **not** change default output.
- Dropped the dead `max_edge_thresh = None` branch (it never culled). `max_edge` is still computed inside `compute_metrics` (now bound to `_max_edge`) to keep the metric routine and diff minimal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ruff format/lint on the new test file**
- **Found during:** Task 1 (test authoring)
- **Issue:** `tests/test_hygiene.py::test_ruff_check_src_is_clean` fails the whole suite if any file under `tests/` is not ruff-formatted; the freshly authored `test_interpolation.py` needed reformatting and had one unused `pytest` import (Task 1 had no parametrization).
- **Fix:** Ran `ruff format`; removed the unused import in Task 1 (re-added at top level in Task 2 once `test_invalid_threshold_params_raise` used `pytest.raises`).
- **Files modified:** tests/test_interpolation.py
- **Verification:** `ruff check` + `ruff format --check` clean; full suite green.
- **Committed in:** d793331 / 67315f4 (part of task commits)

---

**Total deviations:** 1 auto-fixed (1 blocking hygiene/format)
**Impact on plan:** Formatting only; no scope creep. Source behavior unchanged.

## Issues Encountered
None — both tasks were green against their intended baselines. Byte-identity of the default culling path was confirmed out-of-band against a reproduction of the pre-change hardcoded logic (`np.array_equal(..., equal_nan=True) == True`), and pyright reports 0 errors on the modified module.

## Future Improvement (deferred — M-06 over-culling)
The interior-culling heuristic can over-cull on strongly-anisotropic scans (long, thin
but *legitimate* triangles get dropped along a scan gradient). This is logged as a
deferred refinement: the new `area_scale` / `aspect_ratio_mad_factor` knobs give callers
an immediate escape hatch (raise the thresholds, or `interior_culling=False`), so no code
fix is forced now. A future plan could replace the global median/MAD thresholds with a
direction-aware or per-region criterion. Tracked for the **D-17 running note**: new M-06
threshold params landed here.

## Next Phase Readiness
- TEST-03 interpolation coverage complete; BUG-05 M-06 disposition (KEPT-BEHAVIOR) pinned and now tunable.
- No blockers. The opt-in kwargs are additive and backward-compatible for downstream generators/tiled orchestration.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*

## Self-Check: PASSED

All created files exist on disk and both task commits (d793331, 67315f4) are present in git history.
