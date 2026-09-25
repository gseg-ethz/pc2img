---
status: diagnosed
gaps_resolved: 8/8 round-1 gaps closed via gap plan 05-13 (commits f799ada..46d679e); re-verified suite 135 passed, RRIM blocker reproduced-fixed end-to-end
gaps_open: 4 round-2 gaps (G9-G12) surfaced 2026-07-12 by a code review OF the 05-13 gap-closure diff; 2 are correctness defects introduced by the round-1 fixes, both reproduced 2026-07-27 and still present at HEAD (27687c6)
phase: 05-bug-fixes-module-test-coverage
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md, 05-05-SUMMARY.md, 05-06-SUMMARY.md, 05-07-SUMMARY.md, 05-08-SUMMARY.md, 05-09-SUMMARY.md, 05-10-SUMMARY.md, 05-11-SUMMARY.md, 05-12-SUMMARY.md]
started: 2026-07-11T15:23:32Z
updated: 2026-09-25T07:41:26Z
gaps_source: post-UAT high-effort code review (develop-gsd...HEAD) on PR #12; UAT itself passed 47/47 — these gaps were surfaced by review, already root-caused and reproduced
gaps_source_round2: "/code-review 1295c2b high (session 32af2599-d24a-4113-af77-85196232cb2a, 2026-07-12) — 8 finder angles over `git diff 1295c2b HEAD`, i.e. the 05-13 gap-closure commits themselves. No GSD review ever covered that diff: 05-REVIEW.md predates it. Findings re-reproduced 2026-07-27 against HEAD before recording."
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
review_gaps: 8 (round 1 — closed by 05-13)
review_gaps_round2: 4 (G9-G12 — OPEN; 2 correctness + 2 BC-record)

## Gaps

<!-- Surfaced by post-UAT high-effort code review of PR #12 (develop-gsd...HEAD).
     All root-caused; the blocker (G1) was reproduced end-to-end. Feeds gap-closure.
     RESOLVED 2026-07-11 by gap plan 05-13 (all 8 fixed with proving/characterization
     tests; suite 135 passed; RRIM blocker independently reproduced-fixed). Gap entries
     below are retained as the historical work-list. -->

- truth: "generate([\"rrim\"]) (and rrim_pack_/rrim_component_) produces a correct RRIM raster"
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): fix f2e5b12 'schedule RRIM base/pack deps via dependencies_for (G1 blocker)' on RED tests f799ada; re-verified end-to-end in 05-VERIFICATION.md - generate(['rrim']) resolves deps ['range','rrim_pack_(range,r16,d8,z1)'] and returns a finite raster."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): fix 80cb108 'validate K, check rotation in float64, single-pass ortho gather (G2/G4/G7)' on RED tests eca7499."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): fix 9148197 'purge on-disk codec pair on delete/overwrite (G3)' on RED tests 002e59d; pinned by test_overwrite_does_not_leave_stale_on_disk_raster and test_delete_purges_on_disk_codec_pair."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): fix 80cb108 (G2/G4/G7). DEVIATION recorded in 05-VERIFICATION.md - the RED was not constructible (the float32 check does not in fact false-reject valid scipy rotations within 1e-6 across 20k seeds), so it landed as a passing characterization test plus the float64-robustness refactor."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): refactor 46d679e 'single-source dep grammar, drop dead FeatureSpec derivation, centralize percentile bounds (G5/G6/G8)' on consistency tests aedabcf."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): refactor 46d679e (G5/G6/G8) dropped the dead FeatureSpec.__init__ dependency derivation; tests aedabcf."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): fix 80cb108 (G2/G4/G7) replaced the double copy with a single np.ix_ gather; tests eca7499."
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
  status: resolved
  evidence: "Closed by gap plan 05-13 (commit range f799ada..46d679e): refactor 46d679e (G5/G6/G8) centralized the percentile-bounds validator; tests aedabcf. DEVIATION recorded in 05-VERIFICATION.md - unifying the validator also unified three divergent message strings; accept/reject outcomes are unchanged and no test asserts message text."
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

<!-- ══════════════ ROUND 2 (OPEN) ══════════════
     NOTE: deliberately NOT under its own `## Gaps — Round 2` heading. The
     audit parser (`uat.cjs` parseGapsItems) matches the section heading with
     /^gaps$/i, so any variant heading makes these entries invisible to
     `gsd-tools query audit-uat`. They must live inside the one `## Gaps`
     section to be counted. -->

<!-- Surfaced 2026-07-12 by `/code-review 1295c2b high` (session
     32af2599-d24a-4113-af77-85196232cb2a): 8 finder angles over `git diff 1295c2b HEAD`
     — the 05-13 gap-closure commits. That diff was never reviewed by GSD: 05-REVIEW.md
     (2026-07-11T00:00:00Z) covers the phase implementation, and the round-1 fixes landed
     after it. G9 and G10 are correctness defects INTRODUCED by the round-1 fixes.
     Both re-reproduced 2026-07-27 against HEAD (27687c6) before being recorded here.
     G11/G12 are release-note items, not code fixes — they belong in 05-BC-NOTES.md and
     feed Phase 6 BC-01. -->

- truth: "A z_factor accepted by the RRIM name grammar round-trips through the derived pack-feature name"
  status: resolved
  evidence: "Closed by plan 05-14, commit 5dbd93e (grammar widened + shortest-round-trip emission). Proving tests: test_pack_feature_name_round_trips_z_factor, test_pack_feature_name_is_injective_for_nearby_z, test_rrim_dependency_chain_resolves_for_sub_1e4_z, test_generate_rrim_small_z_end_to_end; zero-churn characterization guard test_z_factor_token_unchanged_for_currently_valid_values. Recorded as BC-NOTES entry 14."
  reason: "Code review (G1 follow-on): pack_feature_name() formats z_factor with _format_number ('g'), which emits exponential notation that _Z_FACTOR_RE rejects — so the pack dependency name the new dependencies_for derives cannot be re-parsed"
  severity: blocker
  test: review-G9
  root_cause: "_format_number (rrim.py:83) returns format(value,'g') for non-integers; %g switches to exponential below 1e-4 and truncates to 6 significant figures. _Z_FACTOR_RE (rrim.py:43) is ^z([+-]?\\d+(?:\\.\\d+)?)$ — no exponent accepted. The G1 dependencies_for overrides build the pack dep via pack_feature_name(), FeatureManager re-matches that name, and RRIMPackFeature.dependencies_for re-parses it."
  reproduced: "2026-07-27 — z=1e-05 -> token 'z1e-05' -> REJECTED (ValueError: Unknown RRIM option); z=1.2345678 -> token 'z1.23457' -> SILENT DRIFT to 1.23457; z=0.0001 and z=2.5 round-trip fine."
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "_format_number ('g' formatting) at line 83 vs _Z_FACTOR_RE at line 43; pack name built at line 70"
  missing:
    - "Make the derived pack name round-trippable. Two shapes with different blast radius — OWNER DECISION: (a) widen _Z_FACTOR_RE to accept exponent notation (purely additive; no cache-key churn; every name valid today stays valid), or (b) change _format_number to a fixed-point round-trippable form (cleaner, but feature names ARE the public API and the cache key, so previously-cached names change = a new BC event)."
    - "The 6-significant-figure truncation is NOT fixed by (a) alone — decide explicitly whether to accept it as the documented z precision limit or raise %g precision. Domain call: how much z_factor precision is meaningful for RRIM openness."
    - "Proving test: round-trip property over the config space (parse(pack_feature_name(cfg)) == cfg) including z < 1e-4 and a high-precision fractional z. Note the existing G1 end-to-end tests all use default-ish z, which is why they pass."

- truth: "A delete that raises KeyError leaves the on-disk codec pair untouched (base-class no-side-effect-on-KeyError contract)"
  status: resolved
  evidence: "Closed by plan 05-14, commit f776011 (super().__delitem__ delegated BEFORE the unlink, keeping one membership authority). Proving test: test_failed_delete_preserves_codec_pair_and_both_stores, plus test_adopted_key_delete_purges_shared_pair added by ce14b28 to pin the adoption route."
  reason: "Code review (G3 follow-on): __delitem__ performs the destructive unlink BEFORE super() validates key membership, so a KeyError-raising delete still irreversibly purges another store's raster"
  severity: blocker
  test: review-G10
  root_cause: "disk_backed_image_store.py __delitem__ unlinks .npy + .meta.json, then calls super().__delitem__(key), whose entire body is `del self._store[key]` — it raises KeyError for an untracked key with no side effect. The override inverts that ordering. Corroborated independently by three review angles."
  reproduced: "2026-07-27 — store A built over an empty cache_dir; store B add+offloads 'range' (range.npy + range.meta.json on disk). `del A['range']` raises KeyError('range') AND leaves the dir empty; a fresh store C no longer recovers 'range'."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "unlink-before-super() ordering in __delitem__ (~line 85)"
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "dead `if self.cache_dir is not None` guard that contradicts the method's own docstring (cache_dir always resolves to a Path via the base temp-dir fallback)"
  missing:
    - "Call super().__delitem__(key) FIRST and unlink after, so the KeyError path is a genuine no-op (preferred over an `if key in self` pre-check: it keeps one membership authority)."
    - "Drop the dead cache_dir guard — the docstring already argues at length that it should not exist."
    - "Proving test: two stores over one cache_dir; assert KeyError AND that the codec pair survives AND that a fresh store still serves it."

- truth: "The RRIM request-time validation shift is recorded in the phase BC record"
  status: resolved
  evidence: "Closed as a record item: 05-BC-NOTES.md entry 12 'RRIM feature-name validation moved from compute time to request time', added by commit eeb0e5f and marked to carry into Phase 6 BC-01."
  reason: "Code review (G1 follow-on, release-note item — not a code fix): the new dependencies_for fully validates RRIM args during dependency-graph analysis, moving the failure from compute time to request time and changing the exception surface"
  severity: minor
  test: review-G11
  root_cause: "FeatureRegistry.match (registry.py:71) calls cls.dependencies_for on every matched path; FeatureManager.request (manager.py:49/56) calls match on user-supplied names. RRIM's override parses via _parse_rrim_config -> _validate_config, so a malformed name in a batch — e.g. generate(['range','rrim_(r0)']) — now raises a bare ValueError from inside request(), aborting the whole batch before any feature computes. Previously it raised at construction, i.e. compute time. Arguably a fail-fast improvement, but both the timing and the exception type shifted: callers catching RegistryLookupError around request(), or wrapping only the compute phase, will not catch it."
  artifacts:
    - path: ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md"
      issue: "no entry for the request-time validation shift"
  missing:
    - "Add a 05-BC-NOTES.md entry (surface-only breaking change, same class as entry 11 for the DSN-08 cycle ValueError); carry into Phase 6 BC-01."

- truth: "The PerspectiveProjection K-matrix refusal is recorded in the phase BC record"
  status: resolved
  evidence: "Closed as a record item: 05-BC-NOTES.md entry 13 'PerspectiveProjection rejects a non-3x3 or non-pinhole intrinsics matrix K', added by commit eeb0e5f and marked to carry into Phase 6 BC-01."
  reason: "Code review (G2 follow-on, release-note item — not a code fix): the new K validation is a genuine breaking change for downstream callers, not an in-repo no-op"
  severity: minor
  test: review-G12
  root_cause: "PerspectiveProjection is reachable via the 'perspective' string API / PROJECTIONS.create(...), so an external caller passing a full 3x4 projection matrix P = K[R|t] (shape mismatch) or an up-to-scale / unnormalized K with K[2,2] != 1 (common in some calibration exports) now raises where it previously constructed. The refusal is INTENTIONAL — non-pinhole K would desync the perspective divisor sign from the behind-camera cull — so this is a migration/doc concern, not a defect. Skew in K[0,1] is still accepted (only the bottom row is checked), so that is a non-issue."
  artifacts:
    - path: ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md"
      issue: "no entry for the K pinhole-form refusal"
  missing:
    - "Add a 05-BC-NOTES.md entry alongside the D-17 4x4-rotation breaking change; carry into Phase 6 BC-01 with explicit migration guidance (normalize K by K[2,2]; pass K and [R|t] separately rather than a composed P)."


<!-- ROUND 1 — imported 2026-07-28T09:53:00Z by /gsd-consolidate-findings from gsd-code-reviewer-deep (conversation), range e6e5bcc87..9631ad3.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "A z_factor that scales the raster beyond float32 range fails fast instead of returning and caching an all-NaN image"
  status: deferred
  evidence: "DISPOSITIONED, NOT DONE. Owner decision 2026-07-27 recorded in 05-REVIEW.md CR-01 Correction block: severity blocker -> warning, and not a Phase-5 regression (the same all-NaN raster is reachable on the pre-05-14 grammar via the long-form spelling, z + ~40 digits), so 05-14 changed ergonomics only. The fail-fast invariant guard is designed and prototyped in the todo below (resolves_phase: 6). This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat - uat.cjs parseGapsItems skips only status: resolved, so a deferred item still surfaces at the ship gate, which is the intended outcome."
  deferred_to: ".planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md"
  severity: minor
  reason: "DEFERRED, not a Phase 5 regression: the same all-NaN is reachable on the pre-05-14 grammar via the long-form spelling (z + 40 digits), so 05-14 changed ergonomics only. Design decided (fail-fast invariant guard, 2 call sites) and prototyped in .planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md. Audit confirmed the class is not systemic."
  test: review-r1-42a7c0c6f8c7
  root_cause: "compute_slope and compute_openness multiply the raster by z_factor and immediately store float32; the product (or, under NEP 50, the weak scalar itself) overflows to inf and np.gradient turns inf-inf into NaN. RuntimeWarning: overflow encountered in cast at rrim.py:236"
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "line 236: z_factor scaling overflows float32 and returns a silently all-NaN raster"
    - path: ".planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md"
      issue: "line 236: z_factor scaling overflows float32 and returns a silently all-NaN raster"
  missing: []
  debug_session: ""

- truth: "The __delitem__ docstring claims only the property the ordering actually buys: a KeyError delete is a disk no-op"
  status: resolved
  evidence: "Closed by commit ce14b28 'narrow the __delitem__ cross-store claim and pin the adopted-key path': the docstring was narrowed to the property the ordering actually buys (a KeyError delete is a disk no-op), and test_adopted_key_delete_purges_shared_pair was added to pin the adoption route the existing sensor missed."
  severity: minor
  reason: "RESOLVED in ce14b28: docstring narrowed to the held property and test_adopted_key_delete_purges_shared_pair added to pin the adoption route the existing test misses"
  test: review-r1-e7905decdd2c
  root_cause: "The reorder guarantees only that the KeyError path is side-effect-free; the base __init__ re-scans *.npy and adopts keys, which the docstring's own next paragraph describes"
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "line 72: __delitem__ docstring overclaimed cross-store safety"
    - path: "tests/test_image_store.py"
      issue: "line 72: __delitem__ docstring overclaimed cross-store safety"
  missing: []
  debug_session: ""

- truth: "A store key can never cause unlink() to touch a file outside the configured cache directory"
  status: resolved
  evidence: "Closed by Task 1 of plan 05-15, commit 03eb715: one containment authority (_assert_within_cache_dir routed through _get_npy_path / _get_meta_path) covering all four disk-touching routes, with __delitem__ left byte-identical. Proving tests (authored xfail-first, RED confirmed before the fix): test_escaping_key_delete_refuses_and_leaves_outside_file_intact, test_escaping_key_add_refuses_before_writing_outside_cache_dir; false-positive bound: test_containment_guard_accepts_realistic_feature_names. Recorded as 05-BC-NOTES.md entry 15."
  severity: major
  reason: "Reachable via the registry default fallback (FeatureRegistry.match has an unanchored fallback to ScalarFieldFeature, params={'feature': name}, verbatim as the store key; reproduced end-to-end 2026-09-24, plan 05-16); load-bearing on the installed GSEGUtils 0.5.x, and redundant only at the Phase-6 GSEGUtils 0.6 adoption (spike-000, VALIDATED). DiskBackedImageStore is also exported from the public barrel. Fix is an is_relative_to guard, ~6 lines."
  test: review-r1-a239bdbfc017
  root_cause: "_get_npy_path/_get_meta_path build cache_dir / f\"{key}.npy\" with no containment check, and this diff made __delitem__ perform an unconditional unlink"
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "line 92: __delitem__ unlinks a path built from an unvalidated key, escaping cache_dir"
  missing: []
  debug_session: ""

- truth: "The base-feature-vs-option precedence change introduced by the widened z grammar is documented as a BC event and pinned by a test"
  status: resolved
  evidence: "Closed by Task 2 of plan 05-15, commit b9b6a2e: recorded as 05-BC-NOTES.md entry 16 (qualifying entry 14a) and pinned by test_exponent_token_takes_precedence_over_base_feature_name and test_z_like_token_that_misses_the_grammar_is_still_a_base_feature_name, both passing on their first run. The comment above _Z_FACTOR_RE was corrected to state the name-level precedence instead of claiming unqualified additivity. Behaviour unchanged (owner-accepted precedence)."
  severity: major
  reason: "Low likelihood (needs a scalar field literally named like z1e5) but feature names are both public API and cache key, so per CLAUDE.md this is a BC event; currently undocumented and untested. Belongs in 05-BC-NOTES.md under the D-17 running BC record."
  test: review-r1-a9b17bf97d8f
  root_cause: "_parse_rrim_config uses _looks_like_option_token on the first token; widening _Z_FACTOR_RE moved names matching z\\d+(\\.\\d+)?[eE][+-]?\\d+ from the base-feature class into the option class"
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "line 43: Regex widening reinterprets base-feature names - additive for tokens, not for names"
    - path: ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md"
      issue: "line 43: Regex widening reinterprets base-feature names - additive for tokens, not for names"
  missing: []
  debug_session: ""

- truth: "The RRIM end-to-end test asserts that z_factor actually influences the output, not merely that the output has the right shape and is finite"
  status: resolved
  evidence: "Closed by 05-16 Task 1, commit 101c077 (fix): __delitem__ reordered to build both codec paths -- running the containment guard -- BEFORE delegating to super().__delitem__, so a refused delete (ValueError or KeyError) is a genuine no-op in memory and on disk. Proving tests: test_refused_delete_leaves_store_membership_intact, test_refused_overwrite_leaves_existing_entry_intact; G10's prior no-side-effect-on-KeyError contract remains independently pinned by test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op."
  severity: minor
  reason: "Test-strength gap on the proving test for the G9 blocker; z was confirmed to change the output, but nothing in the suite asserts it"
  test: review-r1-a8cd7b4707b0
  root_cause: "The assertion set omits any comparison between rasters produced with different z_factor values"
  artifacts:
    - path: "tests/test_rrim_features.py"
      issue: "G9 end-to-end test cannot detect z_factor being dropped from the computation"
  missing: []
  debug_session: ""

- truth: "The z_factor round-trip tests cover the upper end of the exponent range as well as the sub-1e-4 lower end"
  status: resolved
  evidence: "Closed by 05-17 Task 1, commit 83e69e4 (test): _ROUND_TRIP_Z_VALUES extended with 1e16, 1e17, 1.2345678e20, 1e22, 4503599627370495.5 (test_pack_feature_name_round_trips_z_factor now runs 14 parametrised cases); test_upper_boundary_exponent_spellings_canonicalise_to_one_pack_name pins that all three exponent spellings of 1e16 resolve to one identical dependency list and that each emitted pack name re-parses to the exact double. NAME-level only -- no raster computed at z >= 1e16; the float32 overflow item stays deferred (review-r1-42a7c0c6f8c7)."
  severity: minor
  reason: "Test-strength gap; cheap to close by extending the existing parametrisation"
  test: review-r1-4939108716dd
  root_cause: "The G9 plan scoped its proving cases to the reported sub-1e-4 failure, not to the whole exponent-notation boundary the fix actually changed"
  artifacts:
    - path: "tests/test_rrim_features.py"
      issue: "Round-trip coverage omits the upper exponent boundary"
  missing: []
  debug_session: ""

- truth: "Every store test's body asserts the behaviour its name claims"
  status: resolved
  evidence: "Closed by 05-16 Task 3, commit d48bf37 (test): test_delete_absent_key_does_not_raise renamed to test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op (the ordering fix inverted the contract the old name encoded), plus a new absent-key test pinning the corrected behaviour."
  severity: minor
  reason: "Test-strength / naming-accuracy gap; the stale name misdescribes the current, intended contract"
  test: review-r1-c2b69f0885e7
  root_cause: "The test predates the ordering fix and was not revisited when __delitem__ moved membership validation ahead of the unlink"
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "test_delete_absent_key_does_not_raise encodes the contract the fix inverted"
  missing: []
  debug_session: ""

- truth: "rrim.py declares no unused logger, or declares one bound to __name__"
  status: resolved
  evidence: "Artifact path corrected (see below): rrim.py has never had a logger (`git log -S getLogger -- src/pc2img/features/rrim.py` returns nothing over the whole reviewed range -- the truth held vacuously for the named file). The actual dead module-level logger (logging.getLogger(__name__.split('.')[0]), bound to the root package name, never used in the file) lived in src/pc2img/image_cache/disk_backed_image_store.py and was removed there by 05-16 Task 3, commit 3fad7db. See 05-16-SUMMARY.md 'IN-01 Artifact-Path Correction'."
  severity: cosmetic
  reason: "Cosmetic cleanup"
  test: review-r1-ab91c4469087
  root_cause: "Leftover from an earlier revision"
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "Dead module-level logger bound to the root package rather than the module"
  missing: []
  debug_session: ""

- truth: "A clip validation error names which clip (slope_clip or structure_clip) failed"
  status: resolved
  evidence: "Closed by 05-17 Task 1, commit 01dcff0 (fix): _validate_clip re-raises the shared validator's ValueError naming '<name>_clip', chained via `from`. Proving tests: test_clip_validation_error_names_the_failing_clip (parametrised slope_clip/structure_clip), test_clip_validation_error_reaches_the_registry_surface. Judged NOT a BC-NOTES entry (message-text-only change, same ValueError type, identical accept/reject outcomes, no test asserted the old text) per the G8 unified-message-strings precedent (05-VERIFICATION.md deviation record)."
  severity: minor
  reason: "Small correctness/ergonomics issue in an error path; one-line fix"
  test: review-r1-8fb6b87813d1
  root_cause: "_validate_clip takes a name parameter that is unused in the raise"
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "_validate_clip ignores its name parameter so the error cannot say which clip failed"
  missing: []
  debug_session: ""

- truth: "The store constructor's mutable default is either fixed or explicitly recorded as an accepted deferral"
  status: resolved
  evidence: "Closed by 05-16 Task 3, commits 3fad7db (fix) + b49b4f2 (docs: BC-NOTES entry 17): DiskBackedImageStore.__init__'s config parameter is now a None-sentinel default (DSN-07 pattern), coerced in the constructor body; `ruff check --select B008` is clean. Proving test: test_default_config_is_coerced_from_none_sentinel."
  severity: cosmetic
  reason: "Known, already-deferred breadcrumb; recorded for completeness"
  test: review-r1-8ff7171c6ca4
  root_cause: "One of the four B008 findings deferred at 04-04 as a visible breadcrumb (D-02); the 05-10/05-11 sweep replaced this pattern at the generator/manager sites but not at this store __init__"
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "line 31: ruff B008 on the store constructor default; CI does not run ruff"
  missing: []
  debug_session: ""

<!-- ROUND 2 — imported 2026-07-28T14:09:45Z by /gsd-consolidate-findings from gsd-code-reviewer-deep (conversation), range e6e5bcc87..3897237.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "A delete that raises leaves the store unchanged - a refused __delitem__ is a no-op in memory as well as on disk"
  status: resolved
  evidence: "Closed by 05-16 Task 1, commit 101c077 (fix): __delitem__ reordered so both codec paths (running the containment guard) are built BEFORE super().__delitem__ -- a refused delete is a full no-op in memory and on disk for every escape spelling and the overwrite route. Proving tests: test_refused_delete_leaves_store_membership_intact, test_refused_overwrite_leaves_existing_entry_intact. RED confirmed first (4 xfailed) against pre-fix HEAD."
  severity: blocker
  reason: "Independently reproduced by the orchestrator on 2026-07-28, not only by the reviewer. Introduced by 03eb715."
  test: review-r2-70fb459066a6
  root_cause: "Plan 05-15's scope_boundaries forbade editing __delitem__ in order to protect the round-2 G10 ordering, which forced the new containment guard downstream of super().__delitem__(). An exception raised after a mutation makes the operation non-atomic. The new proving test never asserts store state, so the suite is blind to it."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 126-158: super().__delitem__(key) runs before _get_npy_path(key) can refuse"
    - path: "tests/test_image_store.py"
      issue: "the delete proving test asserts only on-disk state, never store membership after the refusal"
  missing:
    - "build both paths before super().__delitem__() so a ValueError refusal precedes any mutation"
    - "a test asserting the key is still tracked after a refused delete"
  debug_session: ""
  reviewer_severity: "BLOCKER"

- truth: "The threat-posture docstring describes the reachability of escaping store keys accurately"
  status: resolved
  evidence: "Closed by 05-16 Task 2, commits f1a81cb (fix) + d1947b4 (docs: BC-NOTES) + 13f02b0 (docs: UAT): the false threat-posture paragraph corrected in the store docstring, the round-3 test-file comment, BC-NOTES entry 15 (relabelled SUPERSEDED + Correction bullet), and the UAT reason: line for review-r1-a239bdbfc017. Reachability transcript (FeatureRegistry.match's unanchored default fallback reaching the store with a scalar-field name taken verbatim from PLY/E57 metadata) is recorded in 05-16-SUMMARY.md 'Reproduction Transcripts' #4."
  severity: major
  reason: "Confirmed end-to-end by the orchestrator on 2026-07-28, and the false claim has already been copied into records that carry to Phase 6."
  test: review-r2-1a435f413f18
  root_cause: "The threat posture was reasoned about from the anchored feature-name regexes without accounting for the registry's unanchored default fallback. Because the paragraph reads as 'this guard is not really needed', it invites a future reader to remove a load-bearing check."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 62-71: the false threat-posture paragraph"
    - path: ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md"
      issue: "entry 15 duplicates the false paragraph and is marked carry into Phase 6 BC-01"
    - path: ".planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md"
      issue: "gap review-r1-a239bdbfc017 duplicates the same claim"
  missing:
    - "correct the paragraph in all three places, naming the registry default-fallback route"
    - "state that containment is load-bearing rather than defence-in-depth"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "A legitimate cache entry is never newly refused by the containment predicate, and store unpickling still succeeds"
  status: resolved
  evidence: "REPRODUCED by 05-16 before any change (05-16-SUMMARY.md 'Reproduction Transcripts' #2), then fixed: _assert_within_cache_dir rewritten to resolve only the parent directory (path.parent.resolve() / path.name), commit f1a81cb. Proving test: test_symlinked_cache_entry_is_served_and_unpickles (authored xfail-first, confirmed xfail in isolation, then passed unmarked after the rewrite); every escape spelling and nesting remain correctly classified."
  severity: major
  reason: "REVIEWER-ASSERTED, NOT INDEPENDENTLY VERIFIED. Round 4 must reproduce before fixing."
  test: review-r2-9998f2b36d4c
  root_cause: "Reviewer attributes it to resolving the full path including the final component, rather than resolving only the parent directory for the containment comparison."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 81-88: path.resolve() in the containment predicate"
  missing:
    - "reproduce the symlinked-entry read/delete/overwrite refusal before changing anything"
    - "reproduce the pickle.loads failure on the loky path"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "Every containment proving test fails if the guard is removed"
  status: resolved
  evidence: "Closed by 05-16 Task 3, commit d48bf37 (test): offload moved inside the guarded region so the sentinel assertions are guard-sensitive; demonstrated by a throwaway, never-committed no-guard pytest plugin selecting -k 'escaping or refused' -- 10 failed guard-off, 10 passed guard-on (05-16-SUMMARY.md 'Mutation Check')."
  severity: major
  reason: "Reviewer measured it against a guard-removed build: both sentinel assertions pass with and without the guard."
  test: review-r2-af50d770d73d
  root_cause: "The test asserts the absence of damage at a point in the sequence where no damage would have occurred anyway."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 279-290: sentinel assertions that pass with and without the guard"
  missing:
    - "assert the ValueError itself, or offload before asserting the sentinel, so the test is guard-sensitive"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "The containment invariant claimed in the class docstring holds for every public method declared in this file"
  status: resolved
  evidence: "REPRODUCED by 05-16 via a STORE-INSERTED entry (05-16-SUMMARY.md 'Reproduction Transcripts' #3), correcting a prior invalid refutation attempt that used a directly-constructed entry whose offload was a no-op. Branch taken: NARROW the docstring (no enforcement extension), commit f1a81cb. test_store_inserted_entries_carry_a_cache_path_under_the_cache_dir pins the enforced half (passed on first run, no marker); confirmed no __setitem__ override was added (`git diff ... | grep -c 'def __setitem__'` = 0)."
  severity: major
  reason: "REVIEWER-ASSERTED, NOT INDEPENDENTLY VERIFIED. The orchestrator's refutation attempt was invalid (a directly-constructed DiskBackedImageData whose offload was a no-op), so this is neither confirmed nor refuted."
  test: review-r2-3f625b03fb03
  root_cause: "Reviewer attributes it to the entry holding its own _cache_path, set at insertion, which later writes use directly without re-consulting the store's path builders."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 26-33 (class docstring invariant) and 165-171 (offload)"
  missing:
    - "reproduce the outside-cache-dir write via offload(pickle_container=False) before changing anything"
    - "narrow the docstring invariant to what is actually enforced, or extend enforcement to the entry write path"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "The precedence BC event is pinned at the public surface where it actually bites"
  status: resolved
  evidence: "Closed by 05-17 Task 1, commit 83e69e4 (test): test_exponent_token_precedence_is_visible_at_the_registry_surface asserts the WR-03 precedence through FEATURES.match (not the private parser), including the derived pack-name dependency and spec.cls identity for all three RRIM classes."
  severity: minor
  reason: "Coverage-shape issue: the pinned contract is not the one the BC record cites."
  test: review-r2-d1c47843161c
  root_cause: "The test targets the parser that implements the behaviour rather than the public entry point the BC note is written about."
  artifacts:
    - path: "tests/test_rrim_features.py"
      issue: "lines 272-322: precedence assertions go through the private parser only"
  missing:
    - "assert the precedence through FEATURES.match, including the resulting dependencies and store key"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "The containment predicate resolves each path at most once per call"
  status: resolved
  evidence: "FOLDED by 05-16 into the _assert_within_cache_dir predicate rewrite (commit f1a81cb): the resolved cache directory is now bound once per call as part of the parent-only-resolution rewrite that also closed review-r2-9998f2b36d4c. No standalone change was needed."
  severity: cosmetic
  reason: "Efficiency and clarity cleanup on an error path."
  test: review-r2-2b9426a42695
  root_cause: "The resolved value is recomputed inline rather than bound once."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 81-87"
  missing:
    - "bind the resolved path to a local and reuse it"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "Every guarded path builder has a test that exercises its guard"
  status: deferred
  evidence: "DEFERRED, not fixed: the _get_meta_path guard branch is symmetric with _get_npy_path but is not directly exercised by its own test (covered only transitively). Superseded by the Phase-6 GSEGUtils 0.6 adoption (spike-000, VALIDATED), which deletes the whole override this finding is about -- writing a dedicated test for code scheduled for deletion is not worthwhile. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: cosmetic
  reason: "Dead-in-practice branch with no coverage."
  test: review-r2-a7c7f4e498a6
  root_cause: "Both builders were guarded symmetrically without checking whether both are reachable."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 94-96"
  missing:
    - "either cover the meta-path guard directly or document why it is a backstop"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "The docstring's enumeration of disk-touching routes matches the routes that exist"
  status: resolved
  evidence: "FOLDED by 05-16 into the rewritten route-enumeration paragraph (commit f1a81cb): the docstring's disk-touching-route enumeration now names the .dat memmap route and states that it inherits containment via cache_path. No standalone change was needed."
  severity: cosmetic
  reason: "Documentation completeness; the omitted path is covered transitively but not named."
  test: review-r2-6f4507d8c33f
  root_cause: "The enumeration was written from the store's own codec pair without accounting for the entry-level memmap suffix."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 52-61"
  missing:
    - "name the .dat memmap path and state that it inherits containment via cache_path"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "Tests contain no unused bindings that imply an assertion which is not made"
  status: resolved
  evidence: "Closed by 05-16 Task 3, commit d48bf37 (test): the previously-unused sentinel binding is now bound and asserted after the round trip in the relevant test."
  severity: cosmetic
  reason: "Cleanup; an unused binding reads as a forgotten assertion."
  test: review-r2-e3a76c7d3fd0
  root_cause: "Leftover from an earlier draft of the test."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "line 310"
  missing:
    - "either assert on the sentinel or drop the binding"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "The delete route is pinned for every escape spelling the add route is pinned for"
  status: resolved
  evidence: "Closed by 05-16 Task 3, commit d48bf37 (test): the delete proving test is now parametrised over the same three escape spellings the add proving test already covered."
  severity: cosmetic
  reason: "Coverage asymmetry between the add and delete proving tests."
  test: review-r2-7c8e11c81eed
  root_cause: "The delete test was written before the add test was parametrised."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 241-247 and 250-276"
  missing:
    - "parametrise the delete proving test over the same three spellings"
  debug_session: ""
  reviewer_severity: "INFO"

<!-- ROUND 3 — imported 2026-09-25T07:41:26Z by /gsd-consolidate-findings from gsd-code-reviewer-deep (file:.planning/phases/05-bug-fixes-module-test-coverage/05-REVIEW.md), range 443d390..c93e045.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "Every containment route is pinned by its own guard-sensitive test: with only the insertion route unguarded, a test fails and no file is written outside the cache directory."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current scope, and the Phase-6 GSEGUtils 0.6 adoption deletes the containment override this finding is about, so fixing it now is work thrown away. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: minor
  reason: "05-16 moved offload into the pytest.raises block on the false premise that insertion alone never writes; with caching enabled insertion writes <key>.dat, so an unguarded insertion route passes the whole suite."
  test: review-r3-ffa2d1c2ca7c
  root_cause: "Mutation insert_unguarded (add_data_to_store builds its path via the base _get_npy_path, delete/offload/load stay guarded): test_escaping_key_add_refuses_* pass (3 passed) and the full suite passes (196) while victim.dat is written outside the cache dir; the round-3 test at 443d390 fails 3x with DID NOT RAISE. Realistic trigger: GSEGUtils 0.6 (admitted by the >=0.5.3,<1.0 pin) has zero self._get_npy_path call sites."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 307-329 and 500-509: add test relies on offload to raise; companion test uses only benign key 'range'"
  missing:
    - "Separate insertion-only test asserting ValueError and no new file anywhere outside cache dir (not one sentinel name)"
    - "Separate offload-route test with a setter-inserted caching-enabled entry"
    - "Correct the 'insertion alone never writes' sentence in the docstring and the round-3 ledger entry"
  debug_session: ""
  reviewer_severity: "WARNING (round-4 regression of a proving test)"

- truth: "The symlinked-entry delete assertion can fail: a delete that follows the link and removes the target is caught."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current scope, and the Phase-6 GSEGUtils 0.6 adoption deletes the containment override this finding is about, so fixing it now is work thrown away. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: minor
  reason: "pickle.dumps(store) replaces the cache-internal symlinks with regular files before the delete half runs, so the delete assertions are vacuous; pickling also silently de-links served symlinks (undocumented)."
  test: review-r3-e40af7956397
  root_cause: "Before pickle npy/meta is_symlink=True, after pickle False; mutation unlink_follow (path.resolve().unlink()) passes all 29 tests in tests/test_image_store.py."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 454-464: delete half runs on de-linked regular files"
  missing:
    - "Re-create the symlink layout before the delete and assert is_symlink() as a precondition"
    - "Decide and document whether de-linking on pickle is acceptable"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "Dropping z_factor from compute_slope is detected by a test."
  status: failed
  severity: minor
  reason: "test_generate_rrim_z_factor_changes_the_output only observes z through the openness/pack path; robust-percentile normalisation cancels a linear z scale on the rrim slope channel."
  test: review-r3-289e26115f42
  root_cause: "Mutation slope_noz (z_factor dropped from compute_slope): all 51 tests in tests/test_rrim_features.py pass; rrim_component_(slope,range,z1) == z4 under the mutation, only the component surface observes it."
  artifacts:
    - path: "tests/test_rrim_features.py"
      issue: "lines 271-298: no rrim_component_(slope,...) z1/z4 pair; docstring overclaims"
  missing:
    - "Add rrim_component_(slope,range,z1)/(z4) pair asserted not array-equal"
    - "Correct the docstring: the rrim pair pins z through the pack only"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "Any key the store tracks can be removed through the public MutableMapping API; an escaping key can never be tracked in the first place."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current scope, and the Phase-6 GSEGUtils 0.6 adoption deletes the containment override this finding is about, so fixing it now is work thrown away. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: minor
  reason: "Round-4 containment-first delete plus the inherited unguarded __setitem__ means a setter-inserted escaping key can never be removed: clear()/pop()/popitem() raise every time and clear() leaves the store part-cleared; under 05-15 the same sequence healed after one failure."
  test: review-r3-ede9dcc0e91b
  root_cause: "store['range']=..., store['../victim']=... (setter, unguarded); store.clear() raises ValueError on attempts 0,1,2 with keys stuck at ['../victim']; store.pop('../victim') raises ValueError; only escape hatch is the private store.store dict. Same script under 05-15 ordering: clear() succeeds on retry."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 200-204: __delitem__ refuses first; __setitem__ inherited unguarded from DiskBackedStore"
  missing:
    - "Guard __setitem__ via self._get_npy_path(key) before super().__setitem__"
    - "Escaping-delete tests seed through store.store[key] to reach the delete path"
    - "Test that a setter insertion of an escaping key raises and is not tracked"
  debug_session: ""
  reviewer_severity: "WARNING (behaviour change introduced in round 4)"

- truth: "The containment docstrings and error message state the invariant the code actually enforces (parent directory resolves inside the cache dir; the final component is not followed) and the threat model (cache-dir writers out of scope)."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current scope, and the Phase-6 GSEGUtils 0.6 adoption deletes the containment override this finding is about, so fixing it now is work thrown away. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: minor
  reason: "Class docstring still claims no key can make a write, read or unlink touch a file outside the cache dir, but round 4 deliberately serves reads through cache-internal symlinks; writes to *.npy.tmp, *.meta.json.tmp and .dat follow planted symlinks (pre-existing); helper docstring and error message say 'resolves' for a parent-only resolution."
  test: review-r3-dda7a00b69cf
  root_cause: "test_symlinked_cache_entry_is_served_and_unpickles asserts a read through cache/range.npy -> shared/range.npy succeeds (outside the cache dir); planted j.npy.tmp, j.meta.json.tmp and m.dat symlinks receive the offload write (w1/w2/w3 transcripts in 05-REVIEW.md WR-05)."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 24-29, 101-102, 113-114: overstated invariant, stale 'only the check resolves', error text 'it resolves to'"
  missing:
    - "Restate invariant as directory-containment, final component not followed"
    - "State threat model: anyone with write access to the cache dir is out of scope"
    - "Error message: 'its parent resolves to ...'"
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "_assert_within_cache_dir refuses any path whose final component is '', '.' or '..', independent of what the key builders append."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current scope, and the Phase-6 GSEGUtils 0.6 adoption deletes the containment override this finding is about, so fixing it now is work thrown away. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: minor
  reason: "candidate = path.parent.resolve() / path.name is correct only if path.name is never '..'; is_relative_to is lexical, so cache/.. is admitted by the LOAD-BEARING helper; the pre-round-4 full-resolve predicate refused it."
  test: review-r3-2785f15bd78e
  root_cause: "_assert_within_cache_dir(cache_dir / '..') and (cache_dir / 'sub/../..') are ADMITTED (real path = parent of cache dir). Unreachable today because both builders append .npy/.meta.json (15 spellings checked); a future builder passing a directory or separate suffix (e.g. Phase-6 GSEGUtils 0.6 adoption) inherits the hole silently."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 109-111: no final-component check before parent-only resolve"
  missing:
    - "Reject path.name in ('', '.', '..') before the parent-only resolve"
    - "Unit test feeding cache_dir / '..' directly to the helper"
  debug_session: ""
  reviewer_severity: "WARNING (latent; not reachable from current key builders)"

- truth: "An overwrite that fails for any reason leaves the existing entry and its codec pair intact."
  status: failed
  severity: minor
  reason: "add_image_to_store runs del self[img_name] (drops the in-memory entry and unlinks .npy + .meta.json) before add_data_to_store validates or wraps the replacement, so any non-containment failure loses the old raster."
  test: review-r3-a37bd243f37d
  root_cause: "Store has 'range' with range.dat/range.meta.json/range.npy; add_image_to_store('range', <1-D array>) raises AssertionError from the DiskBackedImageData shape check; afterwards 'range' not in store and only range.dat remains. Same for factory/validator errors and OSError (disk full, ENAMETOOLONG per IN-05)."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 145-153: delete-then-build overwrite ordering"
  missing:
    - "Build and validate the replacement before deleting the old entry"
    - "Test for a failed overwrite with 1-D data"
  debug_session: ""
  reviewer_severity: "WARNING (pre-existing, adjacent to round-4 claims)"

- truth: "_validate_config rejects a non-finite or underflowed z_factor with an error naming the value, and the upper-boundary test covers overflow."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: absurd z_factor values (overflow to inf / pack names past NAME_MAX) are a constructed-input class, out of current scope; they fail loudly rather than returning wrong output. Folded into the existing Phase-6 z_factor bounds todo. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md"
  severity: minor
  reason: "z1e309 parses to inf, inf > 0 passes validation, _format_number emits zinf, and the request fails late at dependency re-match with 'Unknown RRIM option zinf'; z1e-400 underflows to 0.0; the new boundary test stops at 1e22."
  test: review-r3-92f6d30153ef
  root_cause: "FEATURES.match('rrim_(range,z1e309)') -> deps ['range', 'rrim_pack_(range,r16,d8,zinf)'] then ValueError: Unknown RRIM option 'zinf'; rrim_pack_(range,z1e999) accepted with z_factor=inf; rrim_(range,z1e-400) -> 'z_factor must be > 0, got 0.0'."
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "lines 144-145 (_validate_config), 119-121 (_format_number)"
    - path: "tests/test_rrim_features.py"
      issue: "lines 228-250: boundary test stops at 1e22"
  missing:
    - "Require np.isfinite(z_factor) in _validate_config"
    - "Add z1e309 / z1e-400 cases to the boundary test"
  debug_session: ""
  reviewer_severity: "WARNING (pre-existing code; new test claims the boundary)"

- truth: "test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op fails under the G10 unlink-before-membership mutation, or claims only the KeyError."
  status: failed
  severity: minor
  reason: "No file exists for 'never-added', so the disk no-op half holds under any ordering; the G10 contract is pinned only by test_failed_delete_preserves_codec_pair_and_both_stores."
  test: review-r3-b008fc7c80a7
  root_cause: "Mutation unlink_first (original G10 defect): pytest -k absent_key -> 1 passed; only test_failed_delete_preserves_codec_pair_and_both_stores fails."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 148-157: no on-disk pair for the absent key"
  missing:
    - "Place a never-added.npy/.meta.json pair on disk before the delete and assert it survives, or rename the test"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "Every escape spelling in the delete tests can actually escape when the guard is removed, so its sentinel assertion decides something."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current scope, and the Phase-6 GSEGUtils 0.6 adoption deletes the containment override this finding is about, so fixing it now is work thrown away. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md"
  severity: minor
  reason: "cache/a never exists on the setter/delete route, so cache/a/../../victim.npy fails with ENOENT and unlink(missing_ok=True) is a no-op; the embedded_traversal sentinel is untouchable."
  test: review-r3-36e425b15be9
  root_cause: "With the guard removed, the embedded_traversal delete case fails only on DID NOT RAISE; its sentinel assertions can never fail because the kernel rejects the non-existent cache/a component."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 271, 275-304, 378-393: _escape_layout does not create cache/a"
  missing:
    - "(cache_dir / 'a').mkdir() in _escape_layout"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "Explanatory comments added in round 4 describe the current code and the actual G10 history."
  status: failed
  severity: cosmetic
  reason: "Section header says in present tense that _assert_within_cache_dir resolves the FULL path (pre-fix behaviour); __delitem__ docstring misstates the G10 history as building paths after delegation."
  test: review-r3-95860076d83b
  root_cause: "tests/test_image_store.py:418 header describes the pre-round-4 predicate; disk_backed_image_store.py:168-171 attributes the historical G10 defect to path-building order rather than unlink-before-membership."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "line 418: stale present-tense header"
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 168-171: garbled G10 history sentence"
  missing:
    - "Past-tense header; split the history sentence into two accurate clauses"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "Shipped source docstrings carry no .planning/ paths or planning/review IDs that dangle on main."
  status: failed
  severity: minor
  reason: "New docstring text cites .planning/spikes/000-absorption-test/README.md, review-r2-/review-r1- IDs and D-R4-01; main is stripped of .planning/ (same rationale as the commit-scope rule); rrim.py:53 and :127 continue the pattern."
  test: review-r3-6cf03abfa333
  root_cause: "After the milestone squash to main with .planning/ stripped, disk_backed_image_store.py lines 24, 45-49, 79, 94-97, 158, 224 and rrim.py:127 reference files and IDs that do not exist on that branch."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "lines 24, 45-49, 79, 94-97, 158, 224"
    - path: "src/pc2img/features/rrim.py"
      issue: "line 127 (and pre-existing line 53)"
  missing:
    - "Keep technical reasoning in docstrings; move provenance IDs to commit bodies or .planning/"
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "Any accepted z_factor yields a cache filename within NAME_MAX."
  status: deferred
  evidence: "DEFERRED, not fixed. Owner decision 2026-09-25: absurd z_factor values (overflow to inf / pack names past NAME_MAX) are a constructed-input class, out of current scope; they fail loudly rather than returning wrong output. Folded into the existing Phase-6 z_factor bounds todo. This entry deliberately REMAINS VISIBLE to gsd-tools query audit-uat: uat.cjs parseGapsItems skips only status: resolved."
  deferred_to: ".planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md"
  severity: minor
  reason: "The integer branch of _format_number writes every digit, so from roughly z >= 1e215 the pack name exceeds 255 bytes and offload/memmap creation raises ENAMETOOLONG; feeds WR-07 because the OSError happens after the overwrite's del."
  test: review-r3-a3a5eb992c66
  root_cause: "Pack name of 226 bytes offloads ok; 257 bytes raises OSError [Errno 36] File name too long on offload / memmap creation."
  artifacts:
    - path: "src/pc2img/features/rrim.py"
      issue: "lines 119-120: unbounded integer formatting"
  missing:
    - "Bound z in _validate_config, or exponent form above 2**53 (cache-key BC event)"
  debug_session: ""
  reviewer_severity: "INFO (pre-existing)"

- truth: "The store test module leaves no temp directories behind and has no duplicate tests."
  status: failed
  severity: minor
  reason: "test_default_config_is_coerced_from_none_sentinel constructs DiskBackedImageStore() without cache_path, which mkdtemp()s and never removes the directory; test_escaping_key_delete_refuses_* and test_refused_delete_leaves_store_membership_intact assert the same thing over the same three spellings."
  test: review-r3-e720fec68c0d
  root_cause: "Each run of tests/test_image_store.py leaves two new directories in /tmp from the default-config test; lines 275-304 and 378-393 duplicate each other."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "lines 517-527 temp leak; 275-304 vs 378-393 duplication"
  missing:
    - "tmp_path-backed config or rmtree teardown; merge the two delete tests"
  debug_session: ""
  reviewer_severity: "INFO"