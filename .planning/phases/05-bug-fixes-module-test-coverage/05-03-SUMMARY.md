---
phase: 05-bug-fixes-module-test-coverage
plan: 03
subsystem: testing
tags: [numpy, scipy, convolution, nan-handling, float32, util, pytest]

# Dependency graph
requires:
  - phase: 05-01
    provides: tests/conftest.py shared synthetic-fixture factory (pure-array helpers used indirectly)
provides:
  - "nanconv no longer mutates the caller's input array (M-07)"
  - "nanconv accumulates/divides in float32, finite on realistic range magnitudes (M-08/D-09)"
  - "nanconv compute_dtype reduced-precision opt-in parameter (PERF-02/D-03), default float32"
  - "convert_to_image degrades all-NaN + normalize=True to a constant image instead of raising (M-09)"
  - "tests/test_util.py — TEST-06 coverage for nanconv, convert_to_image, replace_nan, to_gray"
affects: [05-12]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PERF-02 opt-in kwarg whose default reproduces the corrected output byte-for-byte (D-03)"
    - "float64 reference oracle for the normalized-convolution math as the M-08 test sensor"
    - "xfail-first proving test (D-12) flipped to passing once the fix lands"

key-files:
  created:
    - tests/test_util.py
  modified:
    - src/pc2img/util.py

key-decisions:
  - "PERF-02 opt-in landed as nanconv `compute_dtype: DTypeLike = np.float32` — selects accumulation/division dtype; default is the float32 correctness path, reduced precision engages only when the caller passes e.g. np.float16"
  - "M-07 fixed via np.where(mask, 0.0, a) into a fresh buffer (no in-place a[n]=0), mirroring _smooth_with_nan"
  - "M-09 fixed by guarding the empty-finite reduction (not finite.any() -> zeros) inside the normalize branch"

patterns-established:
  - "Opt-in reduced-precision parameter with a correctness-preserving default (PERF-02/D-03)"
  - "float64 reference oracle for NaN-aware convolution correctness tests"

requirements-completed: [BUG-05, TEST-06, PERF-02]

coverage:
  - id: D1
    description: "nanconv does not mutate the caller's input array (M-07)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_util.py#test_nanconv_does_not_mutate_input_nan_mask"
        status: pass
    human_judgment: false
  - id: D2
    description: "nanconv is finite and within float32 tolerance of the float64 reference on realistic range magnitudes (M-08/D-09)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_util.py#test_nanconv_finite_and_within_float32_tolerance"
        status: pass
    human_judgment: false
  - id: D3
    description: "convert_to_image on all-NaN + normalize=True returns a valid constant uint8 image, not a ValueError (M-09)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_util.py#test_convert_to_image_all_nan_normalize_returns_constant_image"
        status: pass
    human_judgment: false
  - id: D4
    description: "nanconv exposes the PERF-02 reduced-precision opt-in (compute_dtype); default reproduces the corrected float32 output byte-for-byte, reduced precision engages only when requested"
    requirement: "PERF-02"
    verification:
      - kind: unit
        ref: "tests/test_util.py#test_nanconv_default_reproduces_float32_output_byte_for_byte"
        status: pass
      - kind: unit
        ref: "tests/test_util.py#test_nanconv_reduced_precision_engages_only_when_requested"
        status: pass
    human_judgment: false
  - id: D5
    description: "util.py breadth coverage for replace_nan and to_gray (TEST-06)"
    requirement: "TEST-06"
    verification:
      - kind: unit
        ref: "tests/test_util.py (replace_nan/to_gray breadth tests)"
        status: pass
    human_judgment: false

# Metrics
duration: 8min
completed: 2026-07-11
status: complete
---

# Phase 5 Plan 03: util.py Findings + Module Coverage Summary

**Fixed nanconv input mutation and float16 overflow (float32 default + PERF-02 `compute_dtype` opt-in), guarded convert_to_image all-NaN normalize, and added TEST-06 coverage for util.py.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-11T04:09:00Z (approx)
- **Completed:** 2026-07-11T04:17:16Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- M-07: `nanconv` fills NaNs on a fresh buffer (`np.where(mask, 0.0, a)`) so the caller's array is never mutated.
- M-08/D-09: `nanconv` accumulates and divides in float32 by default — previously float16 (max ≈65504) overflowed to `inf` on realistic summed range magnitudes.
- PERF-02/D-03: landed the reduced-precision opt-in as `nanconv(..., *, compute_dtype: DTypeLike = np.float32)`; the default reproduces the corrected float32 output byte-for-byte, and reduced precision (e.g. `np.float16`) engages only when the caller explicitly opts in.
- M-09: `convert_to_image` degrades an all-NaN raster under `normalize=True` to a constant/zero image instead of crashing on the empty min/max reduction.
- TEST-06: new `tests/test_util.py` covers all three findings plus breadth for `replace_nan` and `to_gray`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author failing proving tests (D-12)** - `80f6c8d` (test)
2. **Task 2: Fix nanconv (M-07+M-08) and convert_to_image (M-09) + PERF-02 opt-in** - `614a6f1` (fix)

_Task 1 authored M-07/M-08/M-09 as xfail; Task 2 landed the fixes and flipped them to passing._

## Files Created/Modified
- `tests/test_util.py` - TEST-06 sensors (M-07/M-08/M-09) + replace_nan/to_gray breadth + PERF-02 opt-in tests (20 tests).
- `src/pc2img/util.py` - nanconv rewrite (copy-input, float32 accumulation, `compute_dtype` opt-in) + convert_to_image all-NaN normalize guard; added `DTypeLike` import.

## Decisions Made
- **PERF-02 symbol (for D-17 running note):** `nanconv(a, k, replace_nan=None, *, compute_dtype: DTypeLike = np.float32)`. Default `np.float32` is the correctness path; pass a reduced-precision dtype (e.g. `np.float16`) to opt into memory-for-accuracy trade. This is the same landed param 05-12's BC-NOTES lists.
- Chose a `compute_dtype` (dtype-selecting) parameter over a boolean flag: the plan's wording ("selects the accumulation/division dtype") plus the general-purpose value of allowing any accumulation precision.
- M-09 guarded with an explicit `not finite.any()` branch rather than sprinkling `initial=` on the reductions — clearer intent and mirrors the existing `hi>lo` constant-image else-branch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ran ruff format on the new test file**
- **Found during:** Task 1 (after authoring tests/test_util.py)
- **Issue:** The repo hygiene test (`test_hygiene.py::test_ruff_check_src_is_clean`) failed because the freshly authored `tests/test_util.py` was not ruff-formatted, blocking a clean `pytest tests/` run.
- **Fix:** `ruff format tests/test_util.py` (and again after Task 2 edits); no logic change.
- **Files modified:** tests/test_util.py (formatting only)
- **Verification:** `test_hygiene.py::test_ruff_check_src_is_clean` passes; `ruff check` clean.
- **Committed in:** 80f6c8d / 614a6f1 (part of the respective task commits)

---

**Total deviations:** 1 auto-fixed (1 blocking — formatting of a self-authored file)
**Impact on plan:** Formatting only, no behavior change. No scope creep.

## Issues Encountered
- The M-09 test path emits a benign `RuntimeWarning: All-NaN slice encountered` from `replace_nan`'s `np.nanmax` on all-NaN input. This is pre-existing `replace_nan` behavior and out of scope for this plan (M-09 concerns only the `convert_to_image` normalize crash, which is fixed). Logged, not fixed.

## Known Stubs
None.

## Threat Flags
None — the two mitigations in the plan's threat register (T-05-03a in-place mutation, T-05-03b float16 DoS) are both fixed; no new surface introduced.

## Next Phase Readiness
- util.py findings closed; TEST-06 partial (util.py covered). Other Phase-5 waves cover remaining modules.
- PERF-02 `compute_dtype` param recorded for the D-17 running note and 05-12 BC-NOTES.

## Self-Check: PASSED

- FOUND: tests/test_util.py
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-03-SUMMARY.md
- FOUND: commit 80f6c8d (Task 1)
- FOUND: commit 614a6f1 (Task 2)

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*
