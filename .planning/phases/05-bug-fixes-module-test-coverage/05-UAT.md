---
status: complete
gaps_resolved: 8/8 via gap plan 05-13 (commits f799ada..46d679e); re-verified suite 135 passed, RRIM blocker reproduced-fixed end-to-end
phase: 05-bug-fixes-module-test-coverage
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md, 05-05-SUMMARY.md, 05-06-SUMMARY.md, 05-07-SUMMARY.md, 05-08-SUMMARY.md, 05-09-SUMMARY.md, 05-10-SUMMARY.md, 05-11-SUMMARY.md, 05-12-SUMMARY.md]
started: 2026-07-11T15:23:32Z
updated: 2026-07-11T16:05:00Z
gaps_source: post-UAT high-effort code review (develop-gsd...HEAD) on PR #12; UAT itself passed 47/47 — these gaps were surfaced by review, already root-caused and reproduced
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. [05-08 D1] GSEGUtils public register hook
expected: GSEGUtils exposes a public `register_lazy_disk_cache_class(cls)` hook (function + decorator) that registers a LazyDiskCache subclass into the store reload allow-list; idempotent; rejects non-LazyDiskCache (TypeError) and name collisions with a different class (ValueError); no importlib fallback (D-02 posture preserved)
result: pass
requirement: BUG-05
reason: human_judgment
verified: "Live: hook imports from installed GSEGUtils 0.5.3 (PyPI); pc2img disk-backed suite 25 passed. Git-rev bridge retired -> now PyPI 0.5.3 pin (commits 78b241a/c641bdd)."

### 2. [05-08 D2] Registration hook consumed by pc2img (round-trip)
expected: Owner-approved git-rev delivery route validated in the pc2img venv: hook imports, register→offload→reload round-trip returns the correct array, pc2img imports
result: pass
requirement: BUG-05
reason: human_judgment
verified: "Live: import pc2img OK (2.0.0a5.post233); disk-backed round-trip suite 25 passed, full suite 111 passed. Delivery now PyPI 0.5.3 pin (git-rev bridge retired), capability unchanged."

### 3. [05-01 D1] synthetic_pcd factory builds a deterministic PointCloudData(Nx3) with optional s
expected: synthetic_pcd factory builds a deterministic PointCloudData(Nx3) with optional scalar_fields
result: pass
source: automated
coverage_id: 05-01-D1
requirement: TEST-05

### 4. [05-01 D2] fetch_stub returns a dict-backed fetch callable resolving rasters by name for co
expected: fetch_stub returns a dict-backed fetch callable resolving rasters by name for compute(_, fetch)
result: pass
source: automated
coverage_id: 05-01-D2
requirement: TEST-04

### 5. [05-01 D3] fake_projection duck stub returns the full project_raw 4-tuple contract
expected: fake_projection duck stub returns the full project_raw 4-tuple contract
result: pass
source: automated
coverage_id: 05-01-D3
requirement: TEST-03

### 6. [05-01 D4] Full test suite still collects with the new conftest present (no name collisions
expected: Full test suite still collects with the new conftest present (no name collisions, no import-time side effects)
result: pass
source: automated
coverage_id: 05-01-D4
requirement: TEST-06

### 7. [05-02 D1] OrthographicProjection returns (pts2d (M,2), mask (N,)) with in-range pixel coor
expected: OrthographicProjection returns (pts2d (M,2), mask (N,)) with in-range pixel coords equal to normalized xyz[mask][:, cols] for xy/yz/xz — not a diagonal (BUG-01 / ROADMAP SC1)
result: pass
source: automated
coverage_id: 05-02-D1
requirement: BUG-01

### 8. [05-02 D2] SphericalProjection refuses a wrapping (crosses_pi) FoV in both project_raw and 
expected: SphericalProjection refuses a wrapping (crosses_pi) FoV in both project_raw and inverse_projection with NotImplementedError (M-05/D-15)
result: pass
source: automated
coverage_id: 05-02-D2
requirement: BUG-05

### 9. [05-02 D3] PerspectiveProjection masks behind-camera (Z_c<=0) points and applies K·(R·X+t) 
expected: PerspectiveProjection masks behind-camera (Z_c<=0) points and applies K·(R·X+t) via translation=; a 4×4 rotation_matrix raises TypeError, a non-orthonormal 3×3 raises ValueError (M-02/M-03/M-03b)
result: pass
source: automated
coverage_id: 05-02-D3
requirement: BUG-05

### 10. [05-02 D4] TEST-03 projection sensors: orthographic + spherical happy-path breadth coverage
expected: TEST-03 projection sensors: orthographic + spherical happy-path breadth coverage; perspective project() via documented @pcd matmul contract with documented project_raw refusal (M-04)
result: pass
source: automated
coverage_id: 05-02-D4
requirement: TEST-03

### 11. [05-03 D1] nanconv does not mutate the caller's input array (M-07)
expected: nanconv does not mutate the caller's input array (M-07)
result: pass
source: automated
coverage_id: 05-03-D1
requirement: BUG-05

### 12. [05-03 D2] nanconv is finite and within float32 tolerance of the float64 reference on reali
expected: nanconv is finite and within float32 tolerance of the float64 reference on realistic range magnitudes (M-08/D-09)
result: pass
source: automated
coverage_id: 05-03-D2
requirement: BUG-05

### 13. [05-03 D3] convert_to_image on all-NaN + normalize=True returns a valid constant uint8 imag
expected: convert_to_image on all-NaN + normalize=True returns a valid constant uint8 image, not a ValueError (M-09)
result: pass
source: automated
coverage_id: 05-03-D3
requirement: BUG-05

### 14. [05-03 D4] nanconv exposes the PERF-02 reduced-precision opt-in (compute_dtype); default re
expected: nanconv exposes the PERF-02 reduced-precision opt-in (compute_dtype); default reproduces the corrected float32 output byte-for-byte, reduced precision engages only when requested
result: pass
source: automated
coverage_id: 05-03-D4
requirement: PERF-02

### 15. [05-03 D5] util.py breadth coverage for replace_nan and to_gray (TEST-06)
expected: util.py breadth coverage for replace_nan and to_gray (TEST-06)
result: pass
source: automated
coverage_id: 05-03-D5
requirement: TEST-06

### 16. [05-04 D1] NormalizedFeature rejects inverted/out-of-range percentiles (M-12) — 0<=low<high
expected: NormalizedFeature rejects inverted/out-of-range percentiles (M-12) — 0<=low<high<=100 enforced in __init__
result: pass
source: automated
coverage_id: 05-04-D1
requirement: BUG-05

### 17. [05-04 D2] NormalizedFeature.compute does not mutate the raster returned by fetch (DSN-03 c
expected: NormalizedFeature.compute does not mutate the raster returned by fetch (DSN-03 copy-before-mutate)
result: pass
source: automated
coverage_id: 05-04-D2
requirement: BUG-05

### 18. [05-04 D3] GradientFeature default output byte-identical to historical 1/100-scaled result;
expected: GradientFeature default output byte-identical to historical 1/100-scaled result; pixel_size default 100 reproduces it; DSL _px suffix parses (M-10 kept-behavior)
result: pass
source: automated
coverage_id: 05-04-D3
requirement: TEST-04

### 19. [05-04 D4] HillshadeFeature azimuth-sweep self-consistency (an east-rising ramp is brighter
expected: HillshadeFeature azimuth-sweep self-consistency (an east-rising ramp is brighter under one azimuth than its opposite) — M-11 kept-behavior, not ESRI truth
result: pass
source: automated
coverage_id: 05-04-D4
requirement: TEST-04

### 20. [05-05 D1] M-06 interior-culling kept-behavior pinned: default Delaunay stamps extra interi
expected: M-06 interior-culling kept-behavior pinned: default Delaunay stamps extra interior NaNs over a data-gap hole that scipy fills
result: pass
source: automated
coverage_id: 05-05-D1
requirement: BUG-05

### 21. [05-05 D2] Delaunay barycentric weights (CONFIRMED-CORRECT) reproduce a linear field to ~1e
expected: Delaunay barycentric weights (CONFIRMED-CORRECT) reproduce a linear field to ~1e-13
result: pass
source: automated
coverage_id: 05-05-D2
requirement: TEST-03

### 22. [05-05 D3] Culling-disabled Delaunay NaN placement matches scipy.LinearNDInterpolator oracl
expected: Culling-disabled Delaunay NaN placement matches scipy.LinearNDInterpolator oracle (NaN iff outside hull)
result: pass
source: automated
coverage_id: 05-05-D3
requirement: TEST-03

### 23. [05-05 D4] Opt-in culling thresholds: explicit defaults are byte-identical to the default c
expected: Opt-in culling thresholds: explicit defaults are byte-identical to the default constructor (PERF-03 / D-06)
result: pass
source: automated
coverage_id: 05-05-D4
requirement: BUG-05

### 24. [05-06 D1] rrim.py module docstring is the first statement, so pc2img.features.rrim.__doc__
expected: rrim.py module docstring is the first statement, so pc2img.features.rrim.__doc__ is a non-empty string (BUG-04)
result: pass
source: automated
coverage_id: 05-06-D1
requirement: BUG-04

### 25. [05-06 D2] rrim.py module-level imports no longer trigger ruff E402 (imports follow the doc
expected: rrim.py module-level imports no longer trigger ruff E402 (imports follow the docstring)
result: pass
source: automated
coverage_id: 05-06-D2
requirement: BUG-04

### 26. [05-07 D1] Both registries raise one miss type RegistryLookupError, still caught by existin
expected: Both registries raise one miss type RegistryLookupError, still caught by existing except KeyError and except RuntimeError callers (D-14 / BUG-05)
result: pass
source: automated
coverage_id: 05-07-D1
requirement: BUG-05

### 27. [05-07 D2] FeatureRegistry.match() derives dependencies via dependencies_for WITHOUT constr
expected: FeatureRegistry.match() derives dependencies via dependencies_for WITHOUT constructing the feature; per-class overrides on Average/Sum/Norm/Hillshade mirror their own derivation (DSN-05)
result: pass
source: automated
coverage_id: 05-07-D2
requirement: BUG-05

### 28. [05-07 D3] Feature default-fallback preserved — unknown feature name resolves to the defaul
expected: Feature default-fallback preserved — unknown feature name resolves to the default pseudo-spec, never a raise (correction to the FINDINGS framing)
result: pass
source: automated
coverage_id: 05-07-D3
requirement: BUG-05

### 29. [05-07 D4] DSN-11: _default_cls typed type[BaseFeatureStrategy] | None, confirmed optional 
expected: DSN-11: _default_cls typed type[BaseFeatureStrategy] | None, confirmed optional by the pyright gate
result: pass
source: automated
coverage_id: 05-07-D4
requirement: BUG-05

### 30. [05-07 D5] TEST-04: feature-name DSL / registry sensors (pure, no PCD) added
expected: TEST-04: feature-name DSL / registry sensors (pure, no PCD) added
result: pass
source: automated
coverage_id: 05-07-D5
requirement: TEST-04

### 31. [05-09 D1] BUG-02 / DSN-02: DiskBackedImageData arithmetic dispatches through the inherited
expected: BUG-02 / DSN-02: DiskBackedImageData arithmetic dispatches through the inherited __array_ufunc__ and returns a plain np.ndarray (dbid + dbid == arr + arr)
result: pass
source: automated
coverage_id: 05-09-D1
requirement: BUG-02

### 32. [05-09 D2] DSN-09 (security): the store carries no arbitrary-object deserialization sink; r
expected: DSN-09 (security): the store carries no arbitrary-object deserialization sink; reload goes through the allow_pickle=False .npy+JSON codec; a legacy .pkl degrades to a cache miss
result: pass
source: automated
coverage_id: 05-09-D2
requirement: BUG-05

### 33. [05-09 D3] Offload -> reload round-trip through the store returns the correct array (the re
expected: Offload -> reload round-trip through the store returns the correct array (the reparent blocker sensor; class registration resolved via the 05-08 hook)
result: pass
source: automated
coverage_id: 05-09-D3
requirement: BUG-05

### 34. [05-09 D4] The hook-bearing GSEGUtils is delivered to the pc2img environment via the [tool.
expected: The hook-bearing GSEGUtils is delivered to the pc2img environment via the [tool.uv.sources] git-rev bridge + re-locked uv.lock; register_lazy_disk_cache_class is importable after uv sync --frozen
result: pass
source: automated
coverage_id: 05-09-D4
requirement: BUG-05

### 35. [05-09 D5] Reparented private-state tests preserve the named behaviors (offload/load, pickl
expected: Reparented private-state tests preserve the named behaviors (offload/load, pickle with/without cache, finalizer cancel/re-register/cleanup, purge enable/disable) against the inherited contract; no residual _image_data assertion
result: pass
source: automated
coverage_id: 05-09-D5
requirement: BUG-05

### 36. [05-10 D1] extend_cache_paths preserves interp_kwargs as a dict with a path-extended LazyDi
expected: extend_cache_paths preserves interp_kwargs as a dict with a path-extended LazyDiskCacheConfig (BUG-03/DSN-01)
result: pass
source: automated
coverage_id: 05-10-D1
requirement: BUG-03

### 37. [05-10 D2] tiled_generator imports cleanly when loaded first in a fresh interpreter (DSN-10
expected: tiled_generator imports cleanly when loaded first in a fresh interpreter (DSN-10 barrel-cycle guard)
result: pass
source: automated
coverage_id: 05-10-D2
requirement: BUG-05

### 38. [05-10 D3] DSN-07 None-sentinel default at the tiled_generator constructor sites (no shared
expected: DSN-07 None-sentinel default at the tiled_generator constructor sites (no shared mutable LazyDiskCacheConfig())
result: pass
source: automated
coverage_id: 05-10-D3
requirement: BUG-05

### 39. [05-11 D1] FeatureManager.request() resets _base_features so successive requests do not acc
expected: FeatureManager.request() resets _base_features so successive requests do not accumulate stale specs (DSN-04)
result: pass
source: automated
coverage_id: 05-11-D1
requirement: BUG-05

### 40. [05-11 D2] A cyclic feature dependency graph raises a clear ValueError('dependency cycle: .
expected: A cyclic feature dependency graph raises a clear ValueError('dependency cycle: ...') instead of RecursionError (DSN-08)
result: pass
source: automated
coverage_id: 05-11-D2
requirement: BUG-05

### 41. [05-11 D3] FeatureManager.lazy_disk_cache_config uses the None-sentinel default (no shared 
expected: FeatureManager.lazy_disk_cache_config uses the None-sentinel default (no shared mutable LazyDiskCacheConfig()) (DSN-07)
result: pass
source: automated
coverage_id: 05-11-D3
requirement: BUG-05

### 42. [05-11 D4] An omitted lazy_disk_cache_config is coerced so PointCloudImageGenerator constru
expected: An omitted lazy_disk_cache_config is coerced so PointCloudImageGenerator constructs a usable cache store (DSN-06 — flips the existing xfail)
result: pass
source: automated
coverage_id: 05-11-D4
requirement: BUG-05

### 43. [05-11 D5] FeatureManager orchestration path covered by tests/test_manager.py (TEST-05)
expected: FeatureManager orchestration path covered by tests/test_manager.py (TEST-05)
result: pass
source: automated
coverage_id: 05-11-D5
requirement: TEST-05

### 44. [05-12 D1] Full suite green and coverage re-measured; CI --cov-fail-under ratcheted to a re
expected: Full suite green and coverage re-measured; CI --cov-fail-under ratcheted to a regression floor at/below achieved coverage (D-10)
result: pass
source: automated
coverage_id: 05-12-D1
requirement: TEST-03

### 45. [05-12 D2] No residual xfail cites a finding fixed this phase (BUG-01..05, DSN-02/06/08/09/
expected: No residual xfail cites a finding fixed this phase (BUG-01..05, DSN-02/06/08/09/10/11, M-02/03/04/05/08); suite carries 0 xfails
result: pass
source: automated
coverage_id: 05-12-D2
requirement: BUG-05

### 46. [05-12 D3] 05-BC-NOTES.md consolidates every Phase-5 BC/behavior/format/error-type/param ch
expected: 05-BC-NOTES.md consolidates every Phase-5 BC/behavior/format/error-type/param change for direct Phase-6 BC-01 consumption, incl. the GSEGUtils git-rev bridge + Phase-6 conversion action
result: pass
source: automated
coverage_id: 05-12-D3
requirement: BC-01

### 47. [05-12 D4] REQUIREMENTS.md traceability maps PERF-02 and PERF-03 to Phase 5 (D-03 pull-forw
expected: REQUIREMENTS.md traceability maps PERF-02 and PERF-03 to Phase 5 (D-03 pull-forward), forward-only annotation of the v2 Performance entries
result: pass
source: automated
coverage_id: 05-12-D4
requirement: BC-01

## Summary

total: 47
passed: 47
issues: 0
pending: 0
skipped: 0
blocked: 0
review_gaps: 8

## Gaps

<!-- Surfaced by post-UAT high-effort code review of PR #12 (develop-gsd...HEAD).
     All root-caused; the blocker (G1) was reproduced end-to-end. Feeds gap-closure.
     RESOLVED 2026-07-11 by gap plan 05-13 (all 8 fixed with proving/characterization
     tests; suite 135 passed; RRIM blocker independently reproduced-fixed). Gap entries
     below are retained as the historical work-list. -->

- truth: "generate([\"rrim\"]) (and rrim_pack_/rrim_component_) produces a correct RRIM raster"
  status: failed
  reason: "Code review: DSN-05 registry refactor broke the entire RRIM feature family; reproduced `ValueError: Scalar field 'rrim' not found on PointCloudData.`"
  severity: blocker
  test: review-G1
  root_cause: "FeatureRegistry.match now calls cls.dependencies_for(params) instead of constructing the instance; RRIMPackFeature/RRIMFeature/RRIMComponentFeature use a regex group named `args` (not `base_feature`) and do NOT override dependencies_for, so the inherited base returns [] and the base raster (e.g. range) is never scheduled."
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "three RRIM classes lack a dependencies_for override"
    - path: "src/pc2img/features/registry.py"
      issue: "match() relies on dependencies_for (line 71)"
  missing:
    - "Add dependencies_for override to RRIMPackFeature, RRIMFeature, RRIMComponentFeature mirroring _parse_rrim_config (base_feature + pack_feature_name derivation)"
    - "Proving test that runs generate([\"rrim\"]) end-to-end (not just docstring/E402) so it can never silently regress"

- truth: "PerspectiveProjection validates the intrinsics matrix K like it validates the rotation matrix"
  status: failed
  reason: "Code review: K (projection_matrix) shape/pinhole-form is never validated while rotation is validated strictly"
  severity: major
  test: review-G2
  root_cause: "Constructor validates rotation (3x3, orthonormal, det+1) but stores _intrinsics = asarray(K) unchecked; a wrong-shape K gives an opaque matmul crash, and a non-pinhole K (bottom row != [0,0,1]) makes the perspective divisor uv_h[:,2] diverge in sign from depth=camera_xyz[:,2], defeating the M-02 behind-camera cull (phantom mislocation)."
  artifacts:
    - path: "src/pc2img/strategies/projection.py"
      issue: "K stored without shape/pinhole validation (~line 333); project() divide vs M-02 cull can disagree"
  missing:
    - "Validate K is 3x3 (and ideally pinhole bottom-row ~ [0,0,1]) at construction with a clear error; add proving test"

- truth: "Overwriting an already-offloaded key does not leave a stale on-disk raster that can later be served"
  status: failed
  reason: "Code review: add_image_to_store overwrite deletes only the in-memory key; stale .npy/.meta.json remain and a re-scanned store serves them"
  severity: major
  test: review-G3
  root_cause: "add_image_to_store does `if k in self: del self[k]` then add_data_to_store; base __delitem__ only does `del self._store[k]` (no disk purge); base __init__ re-scans *.npy on construction, so a fresh store over the same cache_dir loads the stale codec pair."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "overwrite path (lines 57-58) leaves stale on-disk codec pair"
  missing:
    - "On delete/overwrite, purge the on-disk .npy + .meta.json for the key (or reuse a base purge API); add proving test with two store instances over one cache_dir"

- truth: "A valid double-precision rotation matrix is accepted by PerspectiveProjection"
  status: failed
  reason: "Code review: orthonormality/det check runs in float32 at atol=1e-6 and can falsely reject valid float64 rotations"
  severity: minor
  test: review-G4
  root_cause: "rot is cast to float32 (eps ~1.2e-7); np.allclose(rot@rot.T, I, atol=1e-6) and np.isclose(det, 1, atol=1e-6) can exceed 1e-6 after the round-trip for legitimate rotations (e.g. scipy Rotation)."
  artifacts:
    - path: "src/pc2img/strategies/projection.py"
      issue: "float32 orthonormality check with atol=1e-6 (~line 314)"
  missing:
    - "Perform the check in float64 or loosen tolerance (e.g. atol=1e-5); add a proving test using a scipy-generated rotation"

- truth: "The default single-base-feature dependency grammar lives in one place"
  status: failed
  reason: "Code review (cleanup): dependencies_for default is byte-identical in both feature ABCs"
  severity: minor
  test: review-G5
  root_cause: "core.py:19 (BaseFeatureStrategy) and core.py:48 (DerivativeFeatureStrategy) duplicate the same body."
  artifacts:
    - path: "src/pc2img/features/core.py"
      issue: "duplicated dependencies_for default (lines 19 and 48)"
  missing:
    - "Extract one shared helper/mixin both ABCs use"

- truth: "FeatureSpec has no dead dependency-derivation code"
  status: failed
  reason: "Code review (cleanup): FeatureSpec.__init__ computes self.dependencies that match() overwrites on every path"
  severity: minor
  test: review-G6
  root_cause: "FeatureRegistry.match is the sole FeatureSpec constructor and overwrites spec.dependencies (line 71 or 79) unconditionally."
  artifacts:
    - path: "src/pc2img/features/registry.py"
      issue: "dead dependency derivation in FeatureSpec.__init__ (lines 26-29)"
  missing:
    - "Drop the derivation; leave self.dependencies = [] (dependencies_for is the single source)"

- truth: "OrthographicProjection.project_raw does not allocate a discarded out-of-plane column"
  status: failed
  reason: "Code review (efficiency): pcd.xyz[mask][:, cols] materializes an (M,3) intermediate then an (M,2) copy"
  severity: minor
  test: review-G7
  root_cause: "Two-step index (correct for the diagonal-index fix) but double-copies; np.ix_(mask, cols) does a single (M,2) gather."
  artifacts:
    - path: "src/pc2img/strategies/projection.py"
      issue: "double array copy in project_raw (~line 232)"
  missing:
    - "Use pcd.xyz[np.ix_(mask, cols)] (keep behavior identical; add/keep the existing indexing proving test)"

- truth: "Percentile-bounds validation is consistent and centralized across features"
  status: failed
  reason: "Code review (cleanup/consistency): NormalizedFeature uses strict low<high while ClipPercentileFeature and rrim allow low<=high; triplicated inline"
  severity: minor
  test: review-G8
  root_cause: "Three separate inline checks; semantics differ (strict vs non-strict) with no shared validator."
  artifacts:
    - path: "src/pc2img/features/derivative_features.py"
      issue: "NormalizedFeature ~line 93 strict; ClipPercentileFeature ~line 313 non-strict"
    - path: "src/pc2img/features/rrim.py"
      issue: "percentile bounds ~line 90 non-strict"
  missing:
    - "Extract _validate_percentile_bounds(low, high, *, strict) and call from all three; document the intended contract (NormalizedFeature strict is correct: zero range divides by zero)"
