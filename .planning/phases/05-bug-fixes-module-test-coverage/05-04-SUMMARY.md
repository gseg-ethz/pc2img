---
phase: 05-bug-fixes-module-test-coverage
plan: 04
subsystem: testing
tags: [features, derivative-features, numpy, gradient, hillshade, normalized, pytest, tdd]

# Dependency graph
requires:
  - phase: 05-01
    provides: "tests/conftest.py fetch_stub factory fixture (dict-backed compute(_, fetch) stub)"
provides:
  - "DSN-03 fixed: NormalizedFeature.compute copies before mutate (never writes the fetched raster in place)"
  - "M-12 fixed: NormalizedFeature re-enables percentile bounds validation (0<=low<high<=100) in __init__"
  - "M-10 kept-behavior: GradientFeature opt-in pixel_size param (default 100, DSL suffix _px<v>) — output unchanged"
  - "M-11 kept-behavior: HillshadeFeature non-north-up aspect convention documented (no behavior change)"
  - "tests/test_derivative_features.py — TEST-04 sensors for all four findings"
affects: [05-05, 05-06, 05-07, verify-work, TEST-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Copy-before-mutate at feature compute boundary (np.array(fetch(...), copy=True)) mirroring ClipPercentileFeature"
    - "Opt-in kept-behavior parameterization: new param default reproduces historical output byte-for-byte"
    - "Characterization tests pin deliberate design; proving tests ship xfail→pass for genuine defects (D-12)"

key-files:
  created:
    - tests/test_derivative_features.py
  modified:
    - src/pc2img/features/derivative_features.py

key-decisions:
  - "NormalizedFeature validation uses strict 0<=low<high<=100 (matches the commented-out anchor and must_haves.truths), a superset of ClipPercentileFeature's low<=high"
  - "GradientFeature pixel_size wired into BOTH the constructor kwarg and the DSL via an optional _px<value> suffix; base_feature regex switched greedy .+ → non-greedy .+? (byte-identical for all names without _px)"
  - "M-11 aspect handedness left unchanged; only a docstring convention note added and self-consistency (not ESRI-compass) asserted (D-08)"

patterns-established:
  - "Kept-behavior parameterization: expose a magic constant as an opt-in param whose default is byte-for-byte identical, pinned by a characterization test"

requirements-completed: [BUG-05, TEST-04]

coverage:
  - id: D1
    description: "NormalizedFeature rejects inverted/out-of-range percentiles (M-12) — 0<=low<high<=100 enforced in __init__"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_derivative_features.py#test_normalized_feature_rejects_inverted_percentiles"
        status: pass
      - kind: unit
        ref: "tests/test_derivative_features.py#test_normalized_feature_rejects_out_of_range_percentiles"
        status: pass
    human_judgment: false
  - id: D2
    description: "NormalizedFeature.compute does not mutate the raster returned by fetch (DSN-03 copy-before-mutate)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_derivative_features.py#test_normalized_feature_does_not_mutate_fetched_array"
        status: pass
    human_judgment: false
  - id: D3
    description: "GradientFeature default output byte-identical to historical 1/100-scaled result; pixel_size default 100 reproduces it; DSL _px suffix parses (M-10 kept-behavior)"
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_derivative_features.py#test_gradient_default_matches_hundredth_scaled_reference"
        status: pass
      - kind: unit
        ref: "tests/test_derivative_features.py#test_gradient_pixel_size_default_reproduces_hundred_spacing"
        status: pass
      - kind: unit
        ref: "tests/test_derivative_features.py#test_gradient_dsl_px_suffix_parses_pixel_size"
        status: pass
    human_judgment: false
  - id: D4
    description: "HillshadeFeature azimuth-sweep self-consistency (an east-rising ramp is brighter under one azimuth than its opposite) — M-11 kept-behavior, not ESRI truth"
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_derivative_features.py#test_hillshade_azimuth_sweep_is_self_consistent"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-11
status: complete
---

# Phase 5 Plan 04: Derivative Features Fix + Coverage Summary

**Fixed NormalizedFeature's in-place mutation + commented-out percentile validation (DSN-03/M-12), and pinned GradientFeature's 1/100 spacing (via opt-in `pixel_size`) and HillshadeFeature's aspect handedness as deliberate kept-behavior — all covered by `tests/test_derivative_features.py`.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-07-11T04:22:18Z
- **Completed:** 2026-07-11T04:25:24Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- **DSN-03 + M-12 (genuine, one edit):** `NormalizedFeature.__init__` now rejects `low>high` and out-of-`[0,100]` percentiles (strict `0<=low<high<=100`), and `compute` copies the fetched raster before mutating it — the cache-owned array is never written in place.
- **M-10 (kept-behavior):** `GradientFeature` exposes the previously-hardcoded `np.gradient` spacing `100` as an opt-in `pixel_size` (constructor kwarg + DSL `_px<value>` suffix). Default `100` reproduces the historical `1/100`-scaled output byte-for-byte.
- **M-11 (kept-behavior):** `HillshadeFeature`'s deliberate non-north-up aspect convention is documented in the class docstring; no math changed. A self-consistency (azimuth-sweep) test pins the behavior without asserting ESRI-compass truth.
- **TEST-04:** New `tests/test_derivative_features.py` — 3 proving tests (DSN-03/M-12) shipped xfail→pass per D-12, plus 6 characterization/opt-in tests, all green.

## Task Commits

1. **Task 1: Author proving + characterization tests** - `7062d7e` (test)
2. **Task 2: Fix DSN-03+M-12 and add M-10 pixel_size param** - `d3886b5` (fix)

_Task 1 authored the DSN-03/M-12 proving tests as `xfail` (RED) and the M-10/M-11 characterization tests green from the start; Task 2 landed the source fix and flipped the xfails to passing asserts (GREEN)._

## Files Created/Modified
- `tests/test_derivative_features.py` (new) - Sensors for all four findings: percentile validation, non-mutation, gradient spacing characterization + opt-in `pixel_size`, hillshade azimuth-sweep self-consistency.
- `src/pc2img/features/derivative_features.py` - `NormalizedFeature` validation + copy-before-mutate; `GradientFeature` `pixel_size` param + DSL suffix + docstring; `HillshadeFeature` aspect-convention docstring.

## Decisions Made
- **Strict validation bound:** used `0<=low<high<=100` (matches the commented-out anchor at `:68` and the plan's `must_haves.truths`), which is a superset of `ClipPercentileFeature`'s `low<=high`. Rejects the degenerate `low==high` too.
- **pixel_size wiring:** exposed on both the constructor kwarg and the feature-name DSL (optional `_px<value>` suffix). The `base_feature` regex was switched from greedy `.+` to non-greedy `.+?` with an optional trailing `_px` group; because of the `$` anchor this is byte-identical for every existing name that omits `_px`. Added a `pixel_size > 0` guard.
- **M-11 untouched:** aspect handedness left exactly as-is per D-08; only documented. Test asserts internal consistency, never compass truth.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reformatted new test file to satisfy the ruff-format hygiene gate**
- **Found during:** Task 2 (full-suite verification)
- **Issue:** `tests/test_hygiene.py::test_ruff_check_src_is_clean` also runs `ruff format --check src/ tests/`; the new `tests/test_derivative_features.py` was not format-clean (the repo line length is 120 per D-11, and ruff preferred single-line call expressions).
- **Fix:** Ran `ruff format tests/test_derivative_features.py`. No logic change.
- **Files modified:** tests/test_derivative_features.py
- **Verification:** `ruff format --check src/ tests/` clean; full suite 69 passed, 11 xfailed.
- **Committed in:** d3886b5 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** Formatting-only; keeps the pre-existing hygiene gate green. No scope creep.

The C901 (cyclomatic complexity) findings on the `MultiScaleGradient*` classes are pre-existing, out of scope for this plan, and explicitly deferred to Phase 5's broader ruff work via the hygiene gate's `--ignore E402,C901,B008` (per D-02). Not touched.

## Future Improvements (deferred)
- **M-10 principled gradient spacing:** `pixel_size` now defaults to `100` for byte-for-byte compatibility. A future change could default it to the raster's true pixel spacing (or `1`) once downstream consumers are audited for the `1/100` scale assumption.
- **M-11 align-north option:** an opt-in flag to rotate `HillshadeFeature`'s aspect into the ESRI north-up compass convention, gated on re-validating downstream illumination consumers.

## D-17 running note
`GradientFeature` gained an opt-in `pixel_size` parameter (constructor kwarg + DSL `_px<value>` suffix, default `100`). Record for the D-17 API-surface running note.

## Issues Encountered
None beyond the ruff-format gate noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `derivative_features.py` DSN-03/M-12 closed; M-10/M-11 pinned as kept-behavior. Ready for the remaining Wave-2/3 coverage plans.
- No blockers.

## Self-Check: PASSED

- FOUND: tests/test_derivative_features.py
- FOUND: src/pc2img/features/derivative_features.py
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-04-SUMMARY.md
- FOUND commit: 7062d7e (Task 1, test)
- FOUND commit: d3886b5 (Task 2, fix)

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*
