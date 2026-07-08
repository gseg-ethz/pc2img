---
phase: 01-branch-untangling-mainline-consolidation
reviewed: 2026-07-08T22:45:40Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - src/pc2img/strategies/projection.py
  - src/pc2img/features/manager.py
findings:
  critical: 0
  warning: 4
  info: 6
  total: 10
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-08T22:45:40Z
**Depth:** deep
**Files Reviewed:** 2
**Status:** issues_found

## Summary

This phase folded a work-in-progress `PerspectiveProjection` strategy onto the mainline
via a clean merge. Per project decision **D-03**, the perspective math, its
`NotImplementedError` stubs, its use of pchandler private API, and the EOF whitespace
nit are deliberately deferred to Phase 4 (math) and Phase 5 (tests). Those items are
recorded below as **INFO / D-03-deferred**, not as defects of this phase.

Verification performed this review:
- All module-level imports the fold introduced (`pchandler.geometry.transforms._TransformArray`,
  `GSEGUtils.base_types.*`, `pc2img.strategies.registry.StrategyFactory`) **resolve against
  the currently installed dependencies** — the projection module imports cleanly, so the fold
  did not break the pipeline's importability today.
- Traced `ProjectionStrategy.project()` from `core.py:96` through `interpolate()` at
  `core.py:107` to confirm the `(pts2d, mask)` contract. The base `project()` and the
  perspective override are internally consistent (both return `pts2d` of length M and `mask`
  of length N), so no coordinate/value length mismatch exists on the spherical or perspective
  paths.

The findings that carry Warning severity are **not** regressions introduced by the perspective
fold. They are pre-existing correctness bugs (orthographic path) and a documented anti-pattern
(mutable default) that this deep pass surfaced while tracing the module. They are called out so
they get a dedicated fix ticket rather than being masked by the phase's "landing WIP" framing.

No structural-findings substrate was supplied with this review, so this report is entirely
narrative.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `FeatureManager.request()` never resets or de-duplicates `self._base_features`

**File:** `src/pc2img/features/manager.py:32-51` (state at `:29`, `:35`)
**Issue:** `__init__` initializes `self._base_features = []`, but `request()` only resets
`self._targets` (line 35) — it never clears `self._base_features`. Two failure modes follow:
1. **State leak across calls.** Calling `request()` a second time on the same manager appends
   a fresh set of base-feature specs on top of the stale ones. `get_base_features()` (line 59)
   then re-instantiates and recomputes every accumulated base feature, including those from
   prior requests that the new targets do not need.
2. **Duplicates within one call.** `visit()` appends a base spec whenever it is not already in
   `self._raster_cache`, but base features are not in the raster cache during `request()`. If two
   requested targets share the same base-feature dependency, that base feature is appended twice
   and later computed and interpolated twice (`core.py:106-108`).

The `visit()` guard `if spec.name in self._raster_cache` only dedupes already-rasterized
features, not pending base features.
**Fix:**
```python
def request(self, targets: str | list[str]) -> None:
    self._targets = []
    self._base_features = []          # reset alongside _targets
    if isinstance(targets, str):
        targets = [targets]

    seen_base: set[str] = set()
    def visit(spec: FeatureSpec):
        if spec.name in self._raster_cache:
            return
        if issubclass(spec.cls, BaseFeatureStrategy) and spec.name not in seen_base:
            seen_base.add(spec.name)
            self._base_features.append(spec)
        for dep in spec.dependencies:
            visit(self.registry.match(dep))
    ...
```

### WR-02: `OrthographicProjection.project_raw` crashes on mixed boolean+integer-list indexing

**File:** `src/pc2img/strategies/projection.py:181`
**Issue:** `return pcd.xyz[mask, self._xyz_column_selection], mask` indexes with a boolean row
mask (length N) *and* an integer column list (`[0,1]`, `[1,2]`, or `[0,2]`) in the same
subscript. NumPy treats the boolean mask as an integer index of length M (number of `True`
entries) and tries to broadcast it against the length-2 column list. Verified empirically:
```
>>> xyz[mask, [0,1]]
IndexError: shape mismatch: indexing arrays could not be broadcast together
            with shapes (6,) (2,)
```
This raises `IndexError` for every case except the degenerate M == 2. Any use of the
`"orthographic"` projection through `generate()` therefore crashes.
This is **pre-existing** (orthographic predates the perspective fold) and does not appear to be
covered by the documented anti-patterns in CLAUDE.md, so it is likely an unnoticed hard crash.
Recommend a dedicated fix ticket; not a regression from this phase.
**Fix:**
```python
return pcd.xyz[mask][:, self._xyz_column_selection], mask
```

### WR-03: `OrthographicProjection.project_raw` returns a 2-tuple but base `project()` unpacks 4

**File:** `src/pc2img/strategies/projection.py:168`, `:181`; consumer at `:73`
**Issue:** The `project_raw` contract (abstract signature, line 44-55) and the base `project()`
implementation both expect `(coords_raw, mask, mins, maxs)`:
```python
coords_raw, mask, mins, maxs = self.project_raw(pcd)   # projection.py:73
```
`OrthographicProjection.project_raw` returns only `(pcd.xyz[...], mask)` and is even annotated
`-> NDArray`. Calling `project()` on an orthographic instance raises
`ValueError: not enough values to unpack (expected 4, got 2)`. The inline `# Todo: Update to
pass min and max back!` (line 180) confirms it is knowingly incomplete. This is the
"`project()` / `project_raw()` return-arity mismatch" anti-pattern already documented in
CLAUDE.md — pre-existing and not introduced by this phase, but a genuine crash on the
orthographic path.
**Fix:** Compute and return real extents so the tuple matches the contract:
```python
coords = pcd.xyz[mask][:, self._xyz_column_selection]
mins = coords.min(axis=0)
maxs = coords.max(axis=0)
return coords, mask, mins, maxs
```
and correct the annotation to `-> tuple[NDArray, NDArray, NDArray, NDArray]`.

### WR-04: `FeatureManager` uses a constructed mutable default shared across instances

**File:** `src/pc2img/features/manager.py:24`
**Issue:** `lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig()` evaluates the
default **once** at function-definition time. Every `FeatureManager` created without an explicit
config shares the *same* `LazyDiskCacheConfig` object, which is then handed to
`DiskBackedImageStore(config=...)` (line 28). If the store (or anything downstream) mutates that
config — e.g. sets a per-generator cache path — the mutation bleeds into all other
default-constructed managers, a classic shared-mutable-default hazard. CLAUDE.md explicitly flags
this exact line as an anti-pattern and points to the `None`-sentinel pattern used in
`core.py`'s `coerce_lazy_cfg` as the preferred approach. Pre-existing and documented; included
so it is not lost.
**Fix:**
```python
lazy_disk_cache_config: LazyDiskCacheConfig | None = None,
...
self._raster_cache = DiskBackedImageStore(
    config=lazy_disk_cache_config or LazyDiskCacheConfig()
)
```

## Info

### IN-01: Unused imports introduced by the perspective fold (projection.py)

**File:** `src/pc2img/strategies/projection.py:2,6,13,15`
**Issue:** The fold pulled in symbols that are never referenced in the module:
`Self` and `cast` (line 2, `typing`), `Rotation` (line 6, `scipy.spatial.transform`),
`StrategyFactory` (line 15, `.registry`), and `Array_3x3_T`, `Array_4x4_T`, `Array_Nx3_T`
(line 13, `GSEGUtils.base_types`). Only `Vector_Bool_T` and `Array_Nx2_Float_T` from the
`base_types` import are actually used (in the WIP perspective signature).
**Fix:** Drop the unused names. Note these `base_types` imports are candidates to move into the
Phase 4/5 perspective completion if they are intended for the deferred math.

### IN-02: Unused imports in manager.py

**File:** `src/pc2img/features/manager.py:1,2`
**Issue:** `from pathlib import Path` (line 1) and `from typing import Optional` (line 2) are
never used in the module.
**Fix:** Remove both imports.

### IN-03: `PerspectiveProjection` is WIP — stubs, module-level private pchandler API, and unconstructable string form (D-03 deferred to Phase 4/5)

**File:** `src/pc2img/strategies/projection.py:12,18,184-211`
**Issue:** Recorded as **known / D-03-deferred**, not as a phase defect:
- `project_raw` and `inverse_projection` raise `NotImplementedError` by design (lines 186-190).
- `project()` reaches into pchandler private API (`uv.arr`, `@ pcd`) and depends on
  `_TransformArray` (line 12), an underscore-prefixed private symbol. It resolves against the
  current pchandler, but note the import is **module-level**, so if a future pchandler release
  drops or renames `_TransformArray`, importing `pc2img.strategies.projection` fails outright —
  taking the working `spherical`/`orthographic` strategies down with it. Phase 4/5 should either
  move this import method-local, guard it, or switch to a public pchandler API.
- `ProjectionName` now advertises `"perspective"` publicly (line 18), but `__init__` requires two
  positional matrix arguments (line 192), so `PROJECTIONS.create("perspective")` — the string
  form accepted by `validate()` at line 30-31 — raises `TypeError` for missing args, and even
  the `(name, kwargs)` form would then hit the `NotImplementedError` stubs. Phase 4/5 should gate
  or document that `"perspective"` is not yet usable via the standard pipeline.

### IN-04: Trailing blank lines / EOF whitespace (D-03 deferred)

**File:** `src/pc2img/strategies/projection.py:212-213`
**Issue:** File ends with two trailing blank lines after the perspective `project()` return. This
is the known EOF-whitespace nit explicitly deferred to Phase 4/5 under D-03.
**Fix:** Trim to a single trailing newline when the perspective work is completed.

### IN-05: Inconsistent `fetch` contract passed to `compute()`

**File:** `src/pc2img/features/manager.py:61` vs `:80`
**Issue:** `get_base_features()` passes `self._get` as the `fetch` callable, which returns a
`DiskBackedImageData` (line 61). `_compute()` passes `lambda n: np.asarray(self._get(n))`, which
returns a plain `ndarray` (line 80). The same `fetch` parameter therefore has two different
return types depending on whether the caller is a base or derivative feature. Base features do
not currently call `fetch`, so this is latent, but a base feature that ever resolves a dependency
would receive a `DiskBackedImageData` where a derivative feature receives an `ndarray` — a subtle
source of future bugs.
**Fix:** Standardize on one form, e.g. always pass `lambda n: np.asarray(self._get(n))`, so
`fetch(name)` uniformly returns an `ndarray`.

### IN-06: `OrthographicProjection.project_raw` return annotation is wrong

**File:** `src/pc2img/strategies/projection.py:168`
**Issue:** Annotated `-> NDArray` while it actually returns a tuple (and, per WR-03, should return
a 4-tuple). Misleads Pyright and readers. Fold this fix in with WR-03.
**Fix:** `def project_raw(self, pcd: PointCloudData) -> tuple[NDArray, NDArray, NDArray, NDArray]:`

---

_Reviewed: 2026-07-08T22:45:40Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
