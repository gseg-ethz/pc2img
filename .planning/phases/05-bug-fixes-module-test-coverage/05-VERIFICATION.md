---
phase: 05-bug-fixes-module-test-coverage
verified: 2026-07-11T08:00:00Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 5: Bug Fixes & Module Test Coverage — Verification Report

**Phase Goal:** All known and review-surfaced correctness bugs fixed, each with a proving test, and the previously untested core modules covered.
**Verified:** 2026-07-11
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Truths are the 5 ROADMAP Success Criteria (the roadmap contract) plus 3 phase-level must-haves merged from the 12 PLAN frontmatters (DSN-09 security, CI floor, registry unification).

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Orthographic projection returns correct arity + column indexing, produces correct output (BUG-01), proven by test | ✓ VERIFIED | `projection.py:223` uses `pcd.xyz[mask][:, cols]` (M,2), replacing the diagonal-producing `xyz[mask, cols]`; returns the 4-tuple `project()` unpacks at `:101`. Proving tests `test_orthographic_project_columns_and_arity`, `test_orthographic_project_raw_returns_4_tuple` assert `pts2d.shape == (M,2)` and guard against the diagonal. Pass. |
| 2 | `DiskBackedImageData.__array_ufunc__` supports arithmetic or raises proper `NotImplementedError` (BUG-02), proven by test | ✓ VERIFIED | `disk_backed_image_data.py:16` reparented onto `DiskBackedNDArray` (inherits working unwrap→delegate→plain-ndarray ufunc); old `raise NotImplemented` gone (grep NONE). `test_arithmetic_returns_plain_ndarray`: `a+b == arr+arr` and `type(result) is np.ndarray`. Pass. |
| 3 | `extend_cache_paths` preserves `interp_kwargs` (BUG-03) AND `rrim.__doc__` populated (BUG-04), each proven by test | ✓ VERIFIED | `tiled_generator.py:60-76` builds `extended_interp_kwargs` then `replace(self, **updates)` — no `dict.update()`→None trap. `rrim.__doc__` runtime length = 393; docstring is first statement. Tests `test_extend_cache_paths_preserves_interp_kwargs` (asserts dict preserved), `test_rrim_module_docstring_is_populated`. Pass. |
| 4 | Every correctness bug surfaced by QUAL-03 review fixed with a proving test (BUG-05) | ✓ VERIFIED | Multi-plan (05-02..05-07, 05-09, 05-10, 05-11). Fixes verified in source: M-07/08 nanconv copy+float32, M-09 all-NaN convert_to_image, DSN-03/M-12 NormalizedFeature bounds+no-mutate, M-06 Delaunay culling kwargs, DSN-01 interp_kwargs, DSN-04 reset, DSN-08 cycle guard, DSN-10 import-from-core, DSN-06/07 config coercion. Each has a proving test; test-first (xfail-first, D-12) methodology, all flipped to passing. Suite green (109 passed). |
| 5 | Projection/interpolation math, derivative features + DSL, orchestration (FeatureManager, TiledPointCloudImageGenerator), util.py all have passing test coverage (TEST-03..06) | ✓ VERIFIED | Test files present and passing: test_projection, test_interpolation (TEST-03); test_derivative_features, test_feature_registry (TEST-04); test_manager, test_point_cloud_image_generator, test_tiled_generator (TEST-05); test_util (TEST-06). Total coverage 57.17%. |
| 6 | DSN-09: the arbitrary-object deserialization sink in image_cache is eliminated (05-09) | ✓ VERIFIED | `disk_backed_image_store.py` is now a thin WRAPPER over hardened `DiskBackedStore` (`.npy`+`.meta.json`, `allow_pickle=False`); grep for `pickle.load` in image_cache = NONE. `test_store_source_has_no_arbitrary_deserialization_sink` negative-greps source; `test_legacy_pkl_refused_as_cache_miss` proves legacy `.pkl`→KeyError. Pass. |
| 7 | CI `--cov-fail-under` floor ratcheted to 55 and the suite passes at it (D-10) | ✓ VERIFIED | `ci.yml:47` `--cov-fail-under=55`; CONTRIBUTING.md:81 documents the same floor. `uv run --frozen pytest --cov=pc2img --cov-branch --cov-fail-under=55` → "Required test coverage of 55% reached. Total coverage: 57.17%", 109 passed. |
| 8 | Registries unified: single miss type `RegistryLookupError` + non-constructing `dependencies_for` (D-14/DSN-05/DSN-11) | ✓ VERIFIED | `errors.py:28` `RegistryLookupError(KeyError, RuntimeError)` (dual-inherit keeps existing `except KeyError`/`except RuntimeError` callers working). `dependencies_for` classmethod on base (`core.py:19`) with overrides on split-list families (`core.py:48`, `derivative_features.py:170/202/229/282`). `test_feature_registry` passes. |

**Score:** 8/8 truths verified (0 present, behavior-unverified)

Behavior-dependent invariants (state reset, cycle guard, cache-path preservation, offload→reload cleanup) each have a passing behavioral test in the green suite, so they qualify as VERIFIED rather than PRESENT_BEHAVIOR_UNVERIFIED:
- DSN-04 reset → `test_request_twice_does_not_accumulate_base_features` (asserts `len(_base_features) == 1`)
- DSN-08 cycle guard → `test_dependency_cycle_raises_valueerror_not_recursionerror`
- BUG-03 preservation → `test_extend_cache_paths_preserves_interp_kwargs`
- Offload→reload → `test_offload_reload_round_trip` (blocker sensor)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `tests/conftest.py` | Synthetic fixture factory (05-01) | ✓ VERIFIED | Present; `synthetic_pcd` + `fetch_stub`; smoke test passes |
| `src/pc2img/errors.py` | `RegistryLookupError` shared miss type | ✓ VERIFIED | `class RegistryLookupError(KeyError, RuntimeError)` |
| `src/pc2img/strategies/projection.py` | BUG-01 orthographic + seam guard + perspective | ✓ VERIFIED | Fixes present; `_reject_wrapping_fov` called from both spherical paths |
| `src/pc2img/image_cache/disk_backed_image_data.py` | Reparented onto `DiskBackedNDArray` (BUG-02) | ✓ VERIFIED | Inherits working ufunc; shape guard retained |
| `src/pc2img/image_cache/disk_backed_image_store.py` | WRAPPER, no pickle sink (DSN-09) | ✓ VERIFIED | Delegates to hardened base store; legacy BC aliases preserved |
| `pyproject.toml` `[tool.uv.sources]` GSEGUtils git-rev bridge | Hook delivery to CI | ✓ VERIFIED | rev `2cf80835…`; `GSEGUtils ~= 0.5` kept (INTENTIONAL temporary bridge — Phase-6 converts to `~= 0.6` PyPI pin) |
| 11 module test files | Coverage of previously-untested modules | ✓ VERIFIED | All present under `tests/`, all passing |
| `.github/workflows/ci.yml` + `CONTRIBUTING.md` | Ratcheted floor = 55 | ✓ VERIFIED | Consistent `--cov-fail-under=55` |
| `05-BC-NOTES.md` | Consolidated BC-01 running note (D-17) | ✓ VERIFIED | Present (13KB) |

### Key Link Verification

| From | To | Via | Status |
| --- | --- | --- | --- |
| `OrthographicProjection.project_raw` | `project()` unpack at projection.py:101 | 4-tuple return | ✓ WIRED |
| `image_cache/__init__.py` | GSEGUtils hook | `register_lazy_disk_cache_class` | ✓ WIRED (hook importable from installed dep: `python -c` exits 0) |
| `[tool.uv.sources]` git bridge | CI `uv sync --frozen` | git-rev install of hook-bearing build | ✓ WIRED |
| split-list features `dependencies_for` | `FeatureRegistry.match` | non-constructing dep resolution | ✓ WIRED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full suite green | `uv run --frozen pytest tests/ -q` | 109 passed, 0 failed, 0 xfail | ✓ PASS |
| Coverage at floor | `pytest --cov=pc2img --cov-fail-under=55` | 57.17%, floor reached | ✓ PASS |
| GSEGUtils hook installed | `python -c "from GSEGUtils.lazy_disk_cache import register_lazy_disk_cache_class"` | exit 0 | ✓ PASS |
| rrim docstring | `import pc2img.features.rrim; len(__doc__)` | 393 | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
| --- | --- | --- | --- |
| BUG-01 | 05-02 | ✓ SATISFIED | Orthographic arity/indexing fix + tests |
| BUG-02 | 05-09 | ✓ SATISFIED | Reparent + arithmetic test |
| BUG-03 | 05-10 | ✓ SATISFIED | extend_cache_paths preservation + test |
| BUG-04 | 05-06 | ✓ SATISFIED | rrim docstring (len 393) + test |
| BUG-05 | 05-02..07, 05-09, 05-10, 05-11 | ✓ SATISFIED | Every QUAL-03 bug fixed with proving test; suite green |
| TEST-03 | 05-02, 05-05 | ✓ SATISFIED | test_projection, test_interpolation |
| TEST-04 | 05-04, 05-07 | ✓ SATISFIED | test_derivative_features, test_feature_registry |
| TEST-05 | 05-10, 05-11 | ✓ SATISFIED | test_manager, test_tiled_generator, test_point_cloud_image_generator |
| TEST-06 | 05-03 | ✓ SATISFIED | test_util |
| PERF-02 (pulled fwd, D-03) | 05-03 | ✓ SATISFIED | `nanconv(compute_dtype=...)` opt-in |
| PERF-03 (pulled fwd, D-03) | 05-05 | ✓ SATISFIED | Delaunay culling-threshold kwargs |

No orphaned requirements: every ID declared across the 12 PLAN frontmatters (BUG-01..05, TEST-03..06, PERF-02, PERF-03) is mapped to Phase 5 in REQUIREMENTS.md, and REQUIREMENTS.md maps no additional Phase-5 IDs that a plan failed to claim.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
| --- | --- | --- | --- |
| (none) | TODO/FIXME/XXX/HACK/PLACEHOLDER debt markers | — | Grep over all 12 modified source files returned NONE — completion is auditable |

Note: `OrthographicProjection.inverse_projection` raises `NotImplementedError` — a documented refusal (out-of-plane axis is unrecoverable), not the BUG-02-style bare `raise NotImplemented`. This is correct design.

### Deferred / Out-of-Scope (informational, not gaps)

- Pre-existing pyright typing nits in `tiled_generator.py` (6) and `manager.py` (3) — present at HEAD before this phase, untouched by the BUG/DSN fixes, logged in `deferred-items.md` as candidates for a future typing cleanup. Type-checker nits, not correctness bugs. Not Phase-5 gaps.
- GSEGUtils `[tool.uv.sources]` git-rev bridge → conversion to a `~= 0.6` PyPI pin is an owner-approved, documented, TRACKED Phase-6 action (05-08/05-09 SUMMARY + 05-BC-NOTES.md §10). Intentional; NOT a gap.

### Human Verification Required

None. All truths verified programmatically; every behavior-dependent invariant has a passing behavioral test in the green suite.

### Gaps Summary

No gaps. All 5 ROADMAP Success Criteria are observably true in the codebase, each backed by a proving test that asserts the corrected behavior (test-first xfail methodology, all flipped to passing). Every BUG-0x finding has a source fix and a proving test; all previously-untested core modules now have passing coverage; the DSN-09 arbitrary-object deserialization sink is eliminated by construction; the CI coverage floor is ratcheted to 55 and the suite passes at 57.17% (109 passed, 0 failed, 0 residual xfail). The phase goal is achieved.

---

_Verified: 2026-07-11_
_Verifier: Claude (gsd-verifier)_
