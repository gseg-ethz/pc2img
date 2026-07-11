---
phase: 05-bug-fixes-module-test-coverage
plan: 13
subsystem: testing
tags: [rrim, feature-registry, projection, disk-cache, pinhole, dependency-resolution, gap-closure]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: "DSN-05 dependencies_for refactor (05-07), image_cache reparent onto GSEGUtils DiskBackedStore (05-09), synthetic_pcd/fetch_stub/fake_projection fixtures (05-01)"
provides:
  - "G1 blocker fix: RRIM feature family (rrim / rrim_pack_ / rrim_component_) resolves its base+pack deps via dependencies_for so generate([...]) works end-to-end again"
  - "Full-pipeline generate() proving tests that guard the RRIM regression class (not just __doc__/E402)"
  - "PerspectiveProjection K-matrix validation (3x3 + pinhole bottom row) and a float64 rotation orthonormality/det check"
  - "DiskBackedImageStore.__delitem__ on-disk codec-pair purge (no stale raster after overwrite/delete)"
  - "Single-sourced dependency grammar, dead-code-free FeatureSpec, and a shared percentile-bounds validator"
affects: [phase-06-bc, rrim, feature-registry, projection, image_cache]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "dependencies_for override mirrors __init__ derivation for regex families whose group name is not base_feature (RRIM args-group)"
    - "Full-pipeline generate() proving test as the regression guard for dependency-resolution refactors"
    - "np.ix_(mask, cols) single-pass two-axis gather (replaces two-step boolean-then-column index)"
    - "Store subclass overrides __delitem__ to keep the on-disk codec pair the single source of truth"

key-files:
  created: []
  modified:
    - "src/pc2img/features/rrim.py - dependencies_for overrides on the 3 RRIM classes; _validate_clip delegates to shared percentile validator"
    - "src/pc2img/strategies/projection.py - K validation + float64 rotation check + np.ix_ orthographic gather"
    - "src/pc2img/image_cache/disk_backed_image_store.py - __delitem__ purges .npy + .meta.json codec pair"
    - "src/pc2img/features/core.py - _default_dependencies_for shared helper; both ABCs delegate"
    - "src/pc2img/features/registry.py - FeatureSpec no longer self-derives dependencies"
    - "src/pc2img/features/derivative_features.py - _validate_percentile_bounds shared validator"
    - "tests/test_rrim_features.py, tests/test_projection.py, tests/test_image_store.py, tests/test_feature_registry.py, tests/test_derivative_features.py - proving/characterization tests"

key-decisions:
  - "Fix G1 at the dependencies_for layer (mirror each class's own __init__ derivation) so match() and construction always agree — not by reverting the DSN-05 instance-free dependency resolution"
  - "G1 proving tests exercise the full generate() pipeline end-to-end, closing the regression class that let 05-06's __doc__/E402-only tests miss the break"
  - "G4 rotation check moved to float64 as a correctness/robustness improvement even though the float32 check does not currently false-reject random scipy rotations (max deviation ~1.2e-7 < atol 1e-6)"
  - "G8 centralizes the numeric percentile contract (bounds + strict/non-strict); the exact per-site message wording is unified (no test asserted message text and no accept/reject outcome changes)"

patterns-established:
  - "RRIM-family dependencies_for: parse params['args'] through the same _parse_rrim_config/_parse_rrim_component the __init__ uses"
  - "Shared _default_dependencies_for and _validate_percentile_bounds single-source cross-class rules"

requirements-completed: [BUG-05, TEST-03, TEST-04]

# Coverage metadata — one entry per closed gap (G1..G8)
coverage:
  - id: G1
    description: "RRIM feature family resolves base+pack deps via dependencies_for so generate(['rrim' | 'rrim_pack_(range)' | 'rrim_component_(slope,range)']) returns a finite raster end-to-end (blocker)"
    requirement: BUG-05
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py::test_rrim_dependencies_for_derives_deps_without_construction"
        status: pass
      - kind: integration
        ref: "tests/test_rrim_features.py::test_generate_rrim_end_to_end_returns_finite_rgb"
        status: pass
      - kind: integration
        ref: "tests/test_rrim_features.py::test_generate_rrim_pack_end_to_end_returns_finite_pack"
        status: pass
      - kind: integration
        ref: "tests/test_rrim_features.py::test_generate_rrim_component_slope_end_to_end_returns_finite_raster"
        status: pass
    human_judgment: false
  - id: G2
    description: "PerspectiveProjection refuses a non-3x3 K and a non-pinhole K (bottom row != [0,0,1]) at construction"
    requirement: BUG-05
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_rejects_wrong_shape_intrinsics"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_rejects_non_pinhole_intrinsics"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_accepts_valid_pinhole_intrinsics"
        status: pass
    human_judgment: false
  - id: G3
    description: "Overwriting/deleting an offloaded key purges its on-disk .npy + .meta.json so a fresh store never serves the stale raster"
    requirement: BUG-05
    verification:
      - kind: integration
        ref: "tests/test_image_store.py::test_overwrite_does_not_leave_stale_on_disk_raster"
        status: pass
      - kind: integration
        ref: "tests/test_image_store.py::test_delete_purges_on_disk_codec_pair"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py::test_delete_absent_key_does_not_raise"
        status: pass
    human_judgment: false
  - id: G4
    description: "A float64 proper rotation is accepted by PerspectiveProjection (orthonormality/det check runs in float64)"
    requirement: BUG-05
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_perspective_accepts_float64_proper_rotation"
        status: pass
    human_judgment: false
  - id: G5
    description: "The default single-base dependency grammar lives in one shared helper both feature ABCs delegate to, still overridable"
    requirement: TEST-04
    verification:
      - kind: unit
        ref: "tests/test_feature_registry.py::test_both_feature_abcs_share_one_default_dependency_helper"
        status: pass
      - kind: unit
        ref: "tests/test_feature_registry.py::test_dependencies_for_stays_overridable_after_unification"
        status: pass
    human_judgment: false
  - id: G6
    description: "FeatureSpec.__init__ no longer derives dependencies; FeatureRegistry.match is the single writer"
    requirement: TEST-04
    verification:
      - kind: unit
        ref: "tests/test_feature_registry.py::test_feature_spec_does_not_self_derive_dependencies"
        status: pass
      - kind: unit
        ref: "tests/test_feature_registry.py::test_match_is_single_writer_of_dependencies"
        status: pass
    human_judgment: false
  - id: G7
    description: "OrthographicProjection.project_raw gathers the two plane columns in one pass (np.ix_), byte-identical to the prior two-step index"
    requirement: TEST-03
    verification:
      - kind: unit
        ref: "tests/test_projection.py::test_orthographic_project_raw_ix_equivalence"
        status: pass
    human_judgment: false
  - id: G8
    description: "Percentile-bounds validation is single-sourced with the strict (NormalizedFeature) / non-strict (ClipPercentile, rrim) contract preserved"
    requirement: TEST-04
    verification:
      - kind: unit
        ref: "tests/test_derivative_features.py::test_shared_percentile_validator_strict_and_non_strict_contract"
        status: pass
      - kind: unit
        ref: "tests/test_derivative_features.py::test_normalized_rejects_equal_percentiles_strict"
        status: pass
      - kind: unit
        ref: "tests/test_derivative_features.py::test_clip_percentile_accepts_equal_percentiles_non_strict"
        status: pass
      - kind: unit
        ref: "tests/test_derivative_features.py::test_rrim_validate_clip_accepts_equal_percentiles_non_strict"
        status: pass
    human_judgment: false

# Metrics
duration: 33min
completed: 2026-07-11
status: complete
---

# Phase 5 Plan 13: Post-UAT Gap Closure Summary

**Closed all 8 post-UAT review gaps against the shipped Phase-5 work — including the G1 release blocker where the DSN-05 registry refactor silently broke the entire RRIM feature family — each fixed test-first with the full test suite green at 135 passed.**

## Performance

- **Duration:** ~33 min
- **Started:** 2026-07-11T15:56:00Z
- **Completed:** 2026-07-11T16:28:59Z
- **Tasks:** 4 of 4
- **Files modified:** 11 (6 source + 5 test)
- **Full suite:** 135 passed (baseline 111 + 24 new proving/characterization tests), 0 residual xfails introduced by this plan

## Accomplishments
- **G1 (blocker) fixed:** added `dependencies_for` overrides to `RRIMPackFeature`, `RRIMFeature`, and `RRIMComponentFeature`, each parsing `params["args"]` through the same `_parse_rrim_config`/`_parse_rrim_component` its `__init__` uses. `generate(["rrim"])`, `generate(["rrim_pack_(range)"])`, and `generate(["rrim_component_(slope,range)"])` all produce finite rasters end-to-end again, guarded by full-pipeline proving tests.
- **G2/G4/G7:** `PerspectiveProjection.__init__` now validates K (3x3 + pinhole bottom row `~[0,0,1]`) with the same fail-fast posture as the rotation, runs the orthonormality/det check in float64, and `OrthographicProjection.project_raw` gathers columns in one pass via `np.ix_`.
- **G3:** `DiskBackedImageStore.__delitem__` purges the on-disk `.npy` + `.meta.json` codec pair, so an overwrite (which routes through `del`) or explicit delete no longer leaves a stale raster for a re-scanned store to serve.
- **G5/G6/G8:** single-sourced the default dependency grammar (`_default_dependencies_for`), removed the dead `FeatureSpec.__init__` dependency derivation (match() is the single writer), and centralized percentile bounds in `_validate_percentile_bounds(low, high, *, strict)` with the strict/non-strict contract preserved and documented.

## Task Commits

TDD tasks: RED test commit → GREEN fix commit.

1. **Task 1 (G1) — RED tests** - `f799ada` (test)
2. **Task 1 (G1) — fix** - `f2e5b12` (fix)
3. **Task 2 (G2/G4/G7) — RED tests** - `eca7499` (test)
4. **Task 2 (G2/G4/G7) — fix** - `80cb108` (fix)
5. **Task 3 (G3) — RED tests** - `002e59d` (test)
6. **Task 3 (G3) — fix** - `9148197` (fix)
7. **Task 4 (G5/G6/G8) — tests** - `aedabcf` (test)
8. **Task 4 (G5/G6/G8) — refactor** - `46d679e` (refactor)

## Files Created/Modified
- `src/pc2img/features/rrim.py` - three `dependencies_for` overrides; `_validate_clip` delegates to the shared percentile validator
- `src/pc2img/strategies/projection.py` - K shape+pinhole validation, float64 rotation check, `np.ix_` orthographic gather
- `src/pc2img/image_cache/disk_backed_image_store.py` - `__delitem__` codec-pair purge
- `src/pc2img/features/core.py` - `_default_dependencies_for` shared helper
- `src/pc2img/features/registry.py` - `FeatureSpec` no longer self-derives dependencies
- `src/pc2img/features/derivative_features.py` - `_validate_percentile_bounds` shared validator
- 5 test files extended with proving + characterization tests (no committed binaries; fixtures from the seeded `conftest.py` factory)

## Decisions Made
- Fixed G1 at the `dependencies_for` layer (mirroring each class's own `__init__` derivation) rather than reverting the DSN-05 instance-free resolution, so `match()` and construction stay in agreement.
- G1 proving tests drive the full `generate()` pipeline (base → interpolate → derivative), the exact path 05-06's `__doc__`/E402-only tests could not exercise.

## Deviations from Plan

### 1. [Plan-intent adjustment] G4 rotation test is a passing characterization test, not a RED xfail
- **Found during:** Task 2 (G2/G4/G7)
- **Issue:** The plan directed marking the float64-rotation test `xfail` (RED→green). Empirically the current float32 orthonormality/det check does NOT false-reject random scipy rotations: across 20,000 seeds the max deviation of `rot @ rot.T` from identity in float32 is ~1.2e-7, comfortably inside `atol=1e-6`. A legitimate rotation therefore cannot be made to fail today, so a genuine RED test is not constructible with a valid rotation.
- **Fix:** Wrote the G4 test as a passing characterization test pinning the accept side (a float64 proper rotation constructs without a false `ValueError`), and still landed the float64-check refactor as a correctness/robustness improvement that removes the float32 round-trip brittleness at the accept/reject boundary. This mirrors the plan's own treatment of G7 as a passing characterization test.
- **Files modified:** `tests/test_projection.py`, `src/pc2img/strategies/projection.py`
- **Verification:** `test_perspective_accepts_float64_proper_rotation` passes; the pre-existing 4x4→TypeError and non-orthonormal-3x3→ValueError tests still pass.
- **Committed in:** `eca7499` / `80cb108`

### 2. [Plan-intent adjustment] G8 percentile error-message wording is unified rather than preserved verbatim
- **Found during:** Task 4 (G5/G6/G8)
- **Issue:** The plan asked to keep "the same ValueError wording each site uses today" while centralizing into one `_validate_percentile_bounds(low, high, *, strict)` helper — but the three sites (NormalizedFeature, ClipPercentileFeature, rrim `_validate_clip`) used three different message strings, which a single fixed-signature helper cannot reproduce simultaneously.
- **Fix:** Centralized the numeric contract (bounds + strict/non-strict ordering) with one clear unified message set. No test asserted the exact message text (all use bare `pytest.raises(ValueError)`), and no accept/reject OUTCOME changes — the hard must-have ("no observable validation outcome changes") is preserved. The strict/non-strict split is documented in the helper docstring as a deliberate contract (a zero-width percentile range divides by zero in `NormalizedFeature`).
- **Files modified:** `src/pc2img/features/derivative_features.py`, `src/pc2img/features/rrim.py`
- **Verification:** All percentile characterization tests + full suite green.
- **Committed in:** `aedabcf` / `46d679e`

---

**Total deviations:** 2 (both plan-intent adjustments where the plan's RED/message directives conflicted with reproducible reality; neither changes any shipped behavior contract). No scope creep; no shipped 05-01..05-12 PLAN file touched.

## Issues Encountered
- `ruff format --check` (enforced by `tests/test_hygiene.py`) flagged `projection.py` after the K-validation edit; resolved by running `ruff format` on the file. No logic change.
- A standalone `ruff check` flags a pre-existing `B008` on the store's `LazyDiskCacheConfig()` default and pyright reports pre-existing pchandler `.xyz`/`BaseArray`/`_smooth_with_nan` attribute-access errors on the touched files; both are out of scope (present before this plan, unchanged after — verified by stash/compare) and not enforced by the project's ruff/hygiene gate.

## TDD Gate Compliance
Tasks 1–3 followed RED (`test(...)`) → GREEN (`fix(...)`) commit pairs; Task 4 is a behavior-preserving refactor committed as `test(...)` (characterization + RED-for-new-helper) → `refactor(...)`. All gates present in git history.

## BC / Phase-6 (BC-01) note
- **RRIM regression root cause:** the DSN-05 refactor made `FeatureRegistry.match` derive dependencies via `cls.dependencies_for(params)` WITHOUT constructing the feature. The three RRIM classes use a regex group named `args` (not `base_feature`) and had no `dependencies_for` override, so the inherited base returned `[]`, the base raster was never scheduled, and `generate(["rrim"])` aborted with `ValueError: Scalar field 'rrim' not found`. It slipped past 05-06 because those tests only checked `rrim.__doc__`/E402, never a feature computation.
- **New guard:** RRIM is now covered by full-pipeline `generate([...])` proving tests (`tests/test_rrim_features.py`) that resolve the dependency graph end-to-end — any future dependency-resolution refactor that drops a family's deps will fail these, not silently ship.
- **New/changed error surface (for BC consumers):** `PerspectiveProjection.__init__` now raises `ValueError` on a non-3x3 K and on a non-pinhole K (previously stored unchecked → opaque matmul crash or phantom mislocation). Percentile validation `ValueError` message wording changed (numeric contract and accept/reject outcomes unchanged).

## Self-Check: PASSED
- SUMMARY file present at `.planning/phases/05-bug-fixes-module-test-coverage/05-13-SUMMARY.md`
- All 8 task commits present in git history (f799ada, f2e5b12, eca7499, 80cb108, 002e59d, 9148197, aedabcf, 46d679e)
- Full suite: 135 passed, 0 residual xfails from this plan
