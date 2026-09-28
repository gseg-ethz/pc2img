---
phase: 05-bug-fixes-module-test-coverage
plan: 09
subsystem: infra
tags: [image_cache, GSEGUtils, DiskBackedNDArray, DiskBackedStore, lazy_disk_cache, uv, tool.uv.sources, security, DSN-09, BUG-02, D-04, D-05]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: "05-01 Wave-0 sensors + xfail conventions; 05-08 GSEGUtils public register_lazy_disk_cache_class hook (reload allow-list extension point) + the pushed git-rev bridge SHA"
  - phase: 04-code-quality-algorithmic-soundness-review
    provides: "04-FINDINGS BUG-02/DSN-02 (dead __array_ufunc__) + DSN-09 (arbitrary-object deserialization sink) that motivate the image_cache reparent onto GSEGUtils primitives"
provides:
  - "DiskBackedImageData reparented onto GSEGUtils DiskBackedNDArray — inherits the working __array_ufunc__ (BUG-02/DSN-02 fixed: arithmetic returns a plain ndarray)"
  - "DiskBackedImageStore as a thin WRAPPER over DiskBackedStore[DiskBackedImageData] — the arbitrary-object deserialization sink is eliminated by construction (DSN-09), reload uses the .npy + .meta.json allow_pickle=False codec, legacy .pkl degrades to a cache miss"
  - "image_cache import-time registration of DiskBackedImageData via the GSEGUtils reload allow-list hook, so offloaded rasters round-trip through the codec"
  - "pc2img consumes the hook-bearing GSEGUtils via a [tool.uv.sources] git-rev bridge + re-locked uv.lock (CI's uv sync --frozen now installs the hook build)"
affects: [05-10, 05-11, 05-12, phase-6-BC-01, phase-6-D-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Finish-the-migration reparent: a hand-rolled array-like/store is replaced by subclassing the sibling GSEGUtils primitive it duplicated (interpolation.py already did this; image_cache was the last holdout)"
    - "Security-by-construction: removing the deserialization sink entirely (adopt the .npy+JSON allow_pickle=False codec) rather than sandboxing pickle"
    - "Thin WRAPPER preserves a legacy public method surface (add_image_to_store / image_data / offload(features=) / offload_image_data_to_disk) over a renamed base API, keeping call sites stable"

key-files:
  created:
    - "tests/test_image_store.py — BUG-02 arithmetic + DSN-09 security + legacy-.pkl-refusal + offload->reload round-trip sensors"
  modified:
    - "src/pc2img/image_cache/disk_backed_image_data.py — reparented onto DiskBackedNDArray (thin subclass: ndim guard + to_uint8)"
    - "src/pc2img/image_cache/disk_backed_image_store.py — WRAPPER over DiskBackedStore[DiskBackedImageData]; pickle sink + .pkl paths deleted"
    - "src/pc2img/image_cache/__init__.py — import-time register_lazy_disk_cache_class(DiskBackedImageData)"
    - "tests/test_disk_backed_image_data.py — private-state tests rewritten to the inherited DiskBackedNDArray/LazyDiskCache contract (_data, offload/load, pickle, finalizer, purge); no residual _image_data"
    - "pyproject.toml — [tool.uv.sources] gsegutils git-rev bridge @ 2cf80835 (GSEGUtils ~= 0.5 gate unchanged)"
    - "uv.lock — re-locked to the git build (0.5.2.post4)"

key-decisions:
  - "D-04 + D-05 landed together in one plan to avoid a broken intermediate (reparented data over an old pickle store)"
  - "WRAPPER (not REPLACE): DiskBackedImageStore subclasses DiskBackedStore and re-aliases legacy names, PRESERVING overwrite semantics (pre-del existing key before add_data_to_store) so generator reuse does not start raising"
  - "Dropped __array_priority__ = 1000 (Assumption A1) — no mixed-operand test depends on dispatch precedence; the inherited __array_ufunc__ handles binary ops"
  - "Delivered the 05-08 hook to CI via the owner-approved [tool.uv.sources] git-rev bridge + re-locked uv.lock (NOT a PyPI version bump); GSEGUtils ~= 0.5 kept (git build 0.5.2.post4 satisfies it), so pc2img published metadata stays free of PEP 508 direct-reference URLs"

patterns-established:
  - "Downstream LazyDiskCache subclass registers itself into the GSEGUtils reload allow-list at package import time (image_cache/__init__.py)"
  - "Security test negative-greps the store SOURCE for the deserialization sink using a hoisted-flag MULTILINE regex (Pitfall 6)"

requirements-completed: [BUG-02]  # BUG-05 is multi-plan (05-02..05-07, 05-09..05-11) — contributes only; final closure at phase verification

coverage:
  - id: D1
    description: "BUG-02 / DSN-02: DiskBackedImageData arithmetic dispatches through the inherited __array_ufunc__ and returns a plain np.ndarray (dbid + dbid == arr + arr)"
    requirement: "BUG-02"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py::test_arithmetic_returns_plain_ndarray"
        status: pass
    human_judgment: false
  - id: D2
    description: "DSN-09 (security): the store carries no arbitrary-object deserialization sink; reload goes through the allow_pickle=False .npy+JSON codec; a legacy .pkl degrades to a cache miss"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py::test_store_source_has_no_arbitrary_deserialization_sink"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py::test_legacy_pkl_refused_as_cache_miss"
        status: pass
    human_judgment: false
  - id: D3
    description: "Offload -> reload round-trip through the store returns the correct array (the reparent blocker sensor; class registration resolved via the 05-08 hook)"
    requirement: "BUG-05"
    verification:
      - kind: integration
        ref: "tests/test_image_store.py::test_offload_reload_round_trip"
        status: pass
    human_judgment: false
  - id: D4
    description: "The hook-bearing GSEGUtils is delivered to the pc2img environment via the [tool.uv.sources] git-rev bridge + re-locked uv.lock; register_lazy_disk_cache_class is importable after uv sync --frozen"
    requirement: "BUG-05"
    verification:
      - kind: integration
        ref: "uv lock && uv sync --frozen && python -c 'from GSEGUtils.lazy_disk_cache import register_lazy_disk_cache_class'"
        status: pass
    human_judgment: false
  - id: D5
    description: "Reparented private-state tests preserve the named behaviors (offload/load, pickle with/without cache, finalizer cancel/re-register/cleanup, purge enable/disable) against the inherited contract; no residual _image_data assertion"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_disk_backed_image_data.py (21 passed) + grep -n _image_data returns nothing"
        status: pass
    human_judgment: false

# Metrics
duration: 13min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 09: image_cache Reparent onto GSEGUtils Primitives (D-04 + D-05) Summary

**Finished the unfinished migration: `DiskBackedImageData` now subclasses `DiskBackedNDArray` (BUG-02/DSN-02 fixed — arithmetic returns a plain ndarray) and `DiskBackedImageStore` wraps `DiskBackedStore` with the `.npy`+JSON `allow_pickle=False` codec, eliminating the DSN-09 arbitrary-object deserialization sink by construction; the 05-08 hook is delivered to CI via the `[tool.uv.sources]` git-rev bridge + re-locked `uv.lock`.**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-07-11T04:42:45Z
- **Completed:** 2026-07-11T04:55:30Z
- **Tasks:** 4 (1 TDD + 3 auto)
- **Files modified:** 7

## Accomplishments

- **BUG-02 / DSN-02 fixed by construction.** `DiskBackedImageData` is now a ~10-line subclass of `GSEGUtils.lazy_disk_cache.DiskBackedNDArray`, keeping only the `ndim in (2,3)` (single- or 3-channel) shape guard and `to_uint8` (migrated to read `self._data`). It inherits the working `__array_ufunc__` (unwrap → delegate → plain ndarray), `__array__`, `__getitem__`, the `data` property, and all four buffer hooks. The broken `__array_ufunc__` override (`raise NotImplementedError`), `__array_priority__`, the `_image_data` buffer, and the duplicated hooks are gone.
- **DSN-09 sink eliminated (the phase's material security deliverable, ASVS V5).** `DiskBackedImageStore` is a thin WRAPPER over `DiskBackedStore[DiskBackedImageData]`. The arbitrary-object deserialization sink and the `.pkl` scan/dump paths are deleted entirely; reload goes through the base store's `<key>.npy` + `<key>.meta.json` (`allow_pickle=False`) codec, and a legacy `.pkl` degrades to a logged cache miss. A source-level negative-grep sensor guards against regression.
- **Reload class resolution wired.** `image_cache/__init__.py` registers `DiskBackedImageData` into the GSEGUtils reload allow-list via the 05-08 `register_lazy_disk_cache_class` hook at import time — explicit allow-list, no importlib fallback (D-02 posture preserved) — so offload→reload resolves the class.
- **Hook delivered to CI (review concern #2).** Added the `[tool.uv.sources]` git-rev bridge for GSEGUtils pinned to the pushed 05-08 branch SHA `2cf80835aa724f64a83853c8e35c91cb7640a919` and re-locked `uv.lock` (git build `0.5.2.post4`, satisfies the unchanged `GSEGUtils ~= 0.5` gate). `uv sync --frozen` now installs the hook-exporting build; `from GSEGUtils.lazy_disk_cache import register_lazy_disk_cache_class` exits 0.
- **BC surface + call sites preserved.** Legacy names `add_image_to_store` (overwrite-preserving via pre-`del`), `image_data`→`store`, `offload(features=)`→`offload(keys=)`, and `offload_image_data_to_disk`→`offload(pickle_container=True)` re-aliased. FeatureManager integration and `cache_store.cache_dir` unchanged. Suite: **93 passed, 1 xfailed** (the lone xfail is DSN-06 constructor coercion, owned by another 05 plan). Ruff gate + `ruff format --check` clean.

## Task Commits

1. **Task 1: proving sensors (TDD RED)** — `454fe2c` (test)
2. **Task 2: reparent DiskBackedImageData onto DiskBackedNDArray** — `4e82f41` (fix)
3. **Task 3: git-rev bridge + re-lock (hook delivery)** — `82990f2` (build)
4. **Task 4: DiskBackedStore WRAPPER + register class + drop sink** — `0c71966` (fix)

**Plan metadata:** committed with this SUMMARY + STATE/ROADMAP/REQUIREMENTS updates (`docs`).

## Files Created/Modified

- `tests/test_image_store.py` (new) — arithmetic (BUG-02) + security (DSN-09) + legacy-.pkl refusal + offload→reload round-trip sensors.
- `src/pc2img/image_cache/disk_backed_image_data.py` — reparented onto `DiskBackedNDArray`.
- `src/pc2img/image_cache/disk_backed_image_store.py` — WRAPPER over `DiskBackedStore[DiskBackedImageData]`; sink + `.pkl` paths removed.
- `src/pc2img/image_cache/__init__.py` — import-time `register_lazy_disk_cache_class(DiskBackedImageData)`.
- `tests/test_disk_backed_image_data.py` — private-state tests rewritten to the inherited contract (no `_image_data`).
- `pyproject.toml` — `[tool.uv.sources]` gsegutils git-rev bridge.
- `uv.lock` — re-locked to the git build.

## Decisions Made

- **D-04 + D-05 together** to avoid a broken intermediate. **WRAPPER over REPLACE** to keep the public barrel and FeatureManager call sites stable, explicitly preserving overwrite semantics (pre-`del`) so generator reuse does not begin raising against the base `add_data_to_store`. **Dropped `__array_priority__`** — no mixed-operand test depends on it. **Delivery via git-rev bridge**, not a PyPI bump (owner-approved at 05-08), keeping pc2img published metadata free of PEP 508 direct-reference URLs.

## Deviations from Plan

**None — plan executed exactly as written.** (Two mechanical hygiene adjustments were made while satisfying the plan's own ruff gate, not scope deviations: the WRAPPER used `X | None` instead of `Optional[X]` to clear UP045, and `test_image_store.py` was `ruff format`-normalized. The B008 finding on the `LazyDiskCacheConfig()` default is a deferred Phase-5 breadcrumb — `test_hygiene` runs `ruff check --ignore E402,C901,B008` — matching the prior store, so it was left as-is.)

## Issues Encountered

- The pc2img venv started on the stale PyPI `GSEGUtils 0.5.2` (no hook), contrary to the note that it already carried the hook build. Task 3's `uv lock && uv sync --frozen` is exactly the step that delivers the `0.5.2.post4` git build, so this resolved cleanly in-flow (hook importable, round-trip green) with no plan change.

## User Setup Required

None — the GSEGUtils hook was owner-approved at the 05-08 checkpoint; this plan edits only pc2img's `pyproject.toml`/`uv.lock`, not GSEGUtils code, so the dependency-approval gate is not re-tripped.

## BC Deltas (D-17 — for Phase 6 / 05-12)

- **Cache on-disk format:** `<key>.pkl` → `<key>.npy` + `<key>.meta.json` (`allow_pickle=False`). Old `.pkl` cache files are refused (treated as a cache miss and re-materialized), not loaded.
- **Arithmetic surface now live:** `DiskBackedImageData` arithmetic previously raised (`NotImplementedError`); it now dispatches and returns a plain `np.ndarray`.
- **Store construction/format** is inherited from `DiskBackedStore`; legacy method names are preserved as aliases.

## Phase-6 Conversion Action (D-17 / BC-01 — tracked, do NOT do now)

The GSEGUtils dependency is on a **time-boxed `[tool.uv.sources]` git-rev bridge** pinned to SHA `2cf80835aa724f64a83853c8e35c91cb7640a919`. **At Phase 6:** merge the GSEGUtils branch `gsd/register-lazy-disk-cache-class` to `main` via PR so release-please cuts the real `0.6.0` to PyPI, then in pc2img bump `GSEGUtils ~= 0.6`, **DROP** the `[tool.uv.sources]` gsegutils git entry, and re-lock. (Consolidated in 05-12.)

## Next Phase Readiness

- image_cache migration onto the GSEGUtils primitives is complete; BUG-02 proven and DSN-09 eliminated. No blockers for downstream Phase-5 plans (05-10/05-11).
- The only outstanding action from this plan is the Phase-6 pin conversion above.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*

## Self-Check: PASSED
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-09-SUMMARY.md
- FOUND: tests/test_image_store.py, tests/test_disk_backed_image_data.py
- FOUND: src/pc2img/image_cache/{disk_backed_image_data,disk_backed_image_store,__init__}.py
- FOUND: pyproject.toml, uv.lock
- FOUND commit 454fe2c (Task 1 test), 4e82f41 (Task 2 reparent), 82990f2 (Task 3 bridge), 0c71966 (Task 4 store)
