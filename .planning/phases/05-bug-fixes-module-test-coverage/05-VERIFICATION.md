---
phase: 05-bug-fixes-module-test-coverage
verified: 2026-07-11T08:00:00Z
reverified: 2026-07-11T16:40:00Z
status: gaps_found
status_history: passed (2026-07-11T16:40:00Z) → gaps_found (2026-07-27T10:05:00Z)
score: 8/8 must-haves verified as of 2026-07-11; superseded — see Round-2 Gaps below
behavior_unverified: 0
overrides_applied: 0
gap_closure: 05-13 (8 post-UAT code-review gaps closed; suite 111→135 passed)
gaps_open: "10 (round 1)"
next_action: "/gsd-plan-phase --gaps — then execute, re-review the fix diff, and re-verify before /gsd-ship"
---

# Phase 5: Bug Fixes & Module Test Coverage — Verification Report

**Phase Goal:** All known and review-surfaced correctness bugs fixed, each with a proving test, and the previously untested core modules covered.
**Verified:** 2026-07-11
**Status:** gaps_found — the `passed` verdict below is superseded; see "Round-2 Gaps" at the end of this report
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

## Re-verification — Post-UAT Code-Review Gap Closure (05-13)

**Trigger:** UAT passed 47/47, but a post-UAT high-effort code review of PR #12 surfaced **8 defects** the phase's own tests missed — including a **release-blocker**: the DSN-05 registry refactor (05-07) broke the entire RRIM feature family. `FeatureRegistry.match()` was changed to derive dependencies via `dependencies_for()` instead of constructing the instance, but the three RRIM classes (`args` regex group, no override) resolved to `[]` deps, so the base raster was never scheduled — `generate(["rrim"])` raised `ValueError`. It slipped through because 05-06 only tested `rrim.__doc__`/E402, never RRIM computation.

**Closure:** gap plan `05-13` (test-first, 4 tasks) closed all 8 (G1 RRIM blocker; G2 PerspectiveProjection K-validation; G3 store on-disk codec purge on overwrite; G4 float64 rotation check; G5/G6 dependency-grammar single-sourcing + dead `FeatureSpec` removal; G7 `np.ix_` orthographic gather; G8 shared percentile-bounds validator). Commits `f799ada`→`46d679e`.

**Independent re-verification (orchestrator, not just executor report):**
- RRIM family reproduced END-TO-END on the fixed code: `generate(["rrim"])` → deps `['range','rrim_pack_(range,r16,d8,z1)']`, `(48,48,3)` raster, 100% finite; `rrim_pack_(range)` and `rrim_component_(slope,range)` likewise finite. The pre-fix `ValueError` is gone.
- New proving tests exercise the full `generate()` path with the opt-in `import pc2img.features.rrim` registration (`tests/test_rrim_features.py`), so this regression class is now guarded.
- **Full suite: 135 passed** (baseline 111 + 24 new proving/characterization tests), 0 residual xfail from this plan.

**Deviations (executor, non-behavioral):** G4's RED wasn't constructible (the float32 check doesn't actually false-reject valid scipy rotations within 1e-6 across 20k seeds) → landed as a passing characterization test plus the float64-robustness refactor. G8 unified three divergent message strings (no test asserts message text; accept/reject outcomes unchanged).

**Status after closure: PASSED.** No shipped 05-01..05-12 plan was modified; the fixes are additive.

---

_Verified: 2026-07-11 · Re-verified after 05-13 gap closure: 2026-07-11_
_Verifier: Claude (gsd-verifier + orchestrator independent end-to-end re-check)_

---

## Round-2 Gaps (recorded 2026-07-27) — supersedes the `passed` verdict above

The 8/8 verdict above was correct for what it examined: the phase implementation plus the
05-13 gap-closure work, judged against the ROADMAP success criteria. It did not examine the
05-13 diff *as code*. Nothing did — `05-REVIEW.md` is stamped `2026-07-11T00:00:00Z` and the
gap-closure commits (`f799ada`..`46d679e`) landed after it. GSD's re-review loop exists only
inside `/gsd-code-review --fix --auto`; fixes routed through `plan-phase --gaps` skip it.

`/code-review 1295c2b high` (2026-07-12, session `32af2599-d24a-4113-af77-85196232cb2a`)
reviewed exactly that diff across 8 finder angles and found two correctness defects the
round-1 fixes introduced. Both were re-reproduced on 2026-07-27 against HEAD (`27687c6`)
before being recorded:

| Gap | Severity | Defect | Reproduced |
| --- | --- | --- | --- |
| G9 | blocker | RRIM `z_factor` cannot round-trip through the derived pack-feature name — `%g` emits exponent notation `_Z_FACTOR_RE` rejects | `z=1e-05` → `ValueError`; `z=1.2345678` → silent drift to `1.23457` |
| G10 | blocker | `DiskBackedImageStore.__delitem__` unlinks the codec pair *before* `super()` validates membership, breaking the base no-side-effect-on-`KeyError` contract | `del A['range']` raises `KeyError` **and** destroys store B's persisted raster; a fresh store no longer recovers it |
| G11 | minor | RRIM validation moved from compute time to request time with a bare `ValueError` — unrecorded in the BC notes | n/a (release-note item) |
| G12 | minor | The `K` pinhole-form refusal is a real downstream breaking change (3×4 `P`, up-to-scale `K`) — unrecorded in the BC notes | n/a (release-note item) |

Neither correctness defect is caught by the current suite: the G1 end-to-end tests all use
default-ish `z` values, and no test exercises a cross-store delete. CI on PR #12 is green
and remains green with both defects present — a reminder that a green gate bounds only what
the tests reach.

**Phase 5 is therefore not shippable as it stands.** Full detail, root causes, reproduction
transcripts, and the owner decision required on the G9 fix shape are in `05-UAT.md`
§"Gaps — Round 2".


---

## Round-1 findings (consolidated 2026-07-28T09:53:00Z)

10 finding(s) imported from `gsd-code-reviewer-deep` over `e6e5bcc87..9631ad3`.

The prior verdict above is preserved, not deleted: it was correct for what it examined. What it did not examine is this range.

Full detail, root causes and required fixes are in the phase UAT file, section `## Gaps`.

---

## Round-3 closure record (2026-07-28)

Written by plan `05-15` (gap round 3). **Body-only append — the YAML frontmatter
`status:` / `gaps_open:` fields are deliberately NOT updated here.** Re-verification
owns those; this section records what changed underneath them so the next verifier
does not have to reconstruct it.

**Two `major` round-1 findings closed with code + record:**

| Finding | Closed by | Evidence |
| --- | --- | --- |
| WR-02 — a store key could make `unlink()` (and, as reproduced, the offload *write*) touch a file outside the cache directory | `05-15` Task 1, commit `03eb715` | `DiskBackedImageStore._assert_within_cache_dir` routed through `_get_npy_path` / `_get_meta_path` — one authority over all four disk-touching routes, with `__delitem__` byte-identical to `ce14b28`. Proving tests authored xfail-first (RED confirmed): `test_escaping_key_delete_refuses_and_leaves_outside_file_intact`, `test_escaping_key_add_refuses_before_writing_outside_cache_dir`; false-positive bound by `test_containment_guard_accepts_realistic_feature_names`. BC-NOTES entry 15. |
| WR-03 — the base-feature-vs-option precedence introduced by the widened `z` grammar was an unrecorded BC event | `05-15` Task 2, commit `b9b6a2e` | Owner-accepted as correct: **no behaviour change**. Recorded as BC-NOTES entry 16 (qualifying entry 14a by forward-only cross-reference) and pinned by `test_exponent_token_takes_precedence_over_base_feature_name` + `test_z_like_token_that_misses_the_grammar_is_still_a_base_feature_name`, both passing on their first run. The comment above `_Z_FACTOR_RE` no longer claims unqualified additivity. |

**Stale bookkeeping reconciled (no code):** `gsd-tools query audit-uat` reported **22
open items** for `05-UAT.md` before this plan and reports **7** after. Sixteen per-gap
`status:` fields were flipped in place (the parser takes the FIRST occurrence of a key,
so each existing line was edited, never duplicated), each gaining an `evidence:` line
naming a commit SHA, a test function or a BC-NOTES entry number:

- `review-G1`..`review-G8` (2026-07-11, round 1) → `resolved`, cited to the 05-13 range
  `f799ada..46d679e` and the specific fix commit per gap (`f2e5b12` G1; `80cb108`
  G2/G4/G7; `9148197` G3; `46d679e` G5/G6/G8). Every one tied to a commit — none was
  left `failed` for lack of evidence. The G4 and G8 deviations already documented above
  (G4's RED was not constructible; G8 unified three message strings) are carried into
  their evidence lines rather than glossed.
- `review-G9`..`review-G12` (round 2) → `resolved`, cited to `5dbd93e`, `f776011` +
  `ce14b28`, and BC-NOTES entries 12 / 13 (`eeb0e5f`).
- `review-r1-e7905decdd2c` (the `__delitem__` docstring overclaim) → `resolved`, cited
  to `ce14b28`.

**Deferred, not closed:** `review-r1-42a7c0c6f8c7` (the RRIM float32 scaling overflow)
reads `status: deferred`, not `resolved`, with a `deferred_to:` pointing at
`.planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md`
(`resolves_phase: 6`). `uat.cjs parseGapsItems` skips only `resolved`, so this item
**stays visible to the audit query by design** — the work is dispositioned, not done,
and the ship gate should keep showing it.

**Deliberately still open (6):** `review-r1-a8cd7b4707b0` (WR-04, z-insensitive
end-to-end assertion), `review-r1-4939108716dd` (WR-05, upper exponent-boundary
coverage), `review-r1-c2b69f0885e7` (WR-06, misnamed store test),
`review-r1-ab91c4469087` (IN-01, dead logger), `review-r1-8fb6b87813d1` (IN-02,
`_validate_clip` ignores its name parameter), `review-r1-8ff7171c6ca4` (IN-03, ruff
B008 on the store constructor default). These were untouched by this plan and are not
regressions — a future reviewer should not re-report them as new.

All gap entries remain inside the single `## Gaps` heading: `uat.cjs parseGapsItems`
matches it with `/^gaps$/i`, so a decorated `## Gaps — Round N` variant would make
every entry below it invisible to the audit.

Suite at the end of this plan: **175 passed, 0 failed, 0 residual xfail.**
