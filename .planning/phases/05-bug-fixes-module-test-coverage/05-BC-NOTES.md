# Phase 5 — Consolidated Breaking-Change Notes (BC-01 / D-17)

**Purpose:** This is the single, GSD-consumable running note of every public
API / behavior / on-disk-format / error-type / parameter change that landed in
Phase 5. Phase 6's **BC-01** (`downstream migration record`) consumes this file
directly — it should NOT reconstruct the delta set from git diffs.

Each entry gives: the **symbol** affected, the **old → new** contract, and a
**migration note** for a downstream consumer.

**Source plans:** 05-02 (projection), 05-03 (util/nanconv), 05-04 (derivative
features), 05-05 (interpolation), 05-07 (registries), 05-08 + 05-09 (image_cache
+ GSEGUtils bridge), 05-11 (feature manager). Collated 2026-07-11 in 05-12.

**Severity legend:** `BREAKING` = a caller could observe a changed result/raise;
`ADDITIVE` = new opt-in surface, prior behavior byte-for-byte unchanged.

---

## 1. Spherical projection now raises on a wrapping FoV — BREAKING (D-15, 05-02)

- **Symbol:** `pc2img.strategies.projection.SphericalProjection.project_raw`,
  `SphericalProjection.inverse_projection`
- **Old → new:** An untiled cloud whose resolved field of view *wraps* around
  ±π (`left > right`, `crosses_pi=True`) previously **silently produced reversed
  columns** in the raster. It now **raises `NotImplementedError`** from both the
  forward and inverse methods (shared `_reject_wrapping_fov` seam guard).
- **Migration note:** Callers relying on the (incorrect) wrapped output must
  re-orient the point cloud / FoV so the horizontal extent does not cross the
  ±π seam, or split the cloud. The prior output was mathematically wrong
  (reversed columns), so no correct consumer depended on it.

## 2. PerspectiveProjection rejects a 4×4 rotation matrix — BREAKING (05-02)

- **Symbol:** `pc2img.strategies.projection.PerspectiveProjection(rotation_matrix=...)`
- **Old → new:** A 4×4 `rotation_matrix` was previously **silently accepted** as
  an affine extrinsic. It now **raises `TypeError`** — the contract is a **3×3
  rotation** plus a separate `translation=` vector (full pinhole `K·(R·X + t)`
  with a behind-camera depth cull).
- **Migration note:** Split any 4×4 extrinsic into its 3×3 rotation block and a
  translation vector; pass the translation via `translation=`. No runtime
  `DeprecationWarning` was added — the 4×4 path was never a documented contract,
  and it is batched into this already-breaking milestone.

## 3. `nanconv` accumulates in float32 by default + `compute_dtype` opt-in — BREAKING + ADDITIVE (PERF-02 / M-07 / M-08 / D-03, 05-03)

- **Symbol:** `pc2img.util.nanconv(a, k, replace_nan=None, *, compute_dtype: DTypeLike = np.float32)`
- **Old → new:**
  - **(BREAKING, correctness)** Accumulation/division dtype changed from
    **float16 → float32**. The old float16 path **overflowed to `inf`**
    (max ≈ 65504) on realistic summed range magnitudes; results are now finite
    and within float32 tolerance of the float64 reference.
  - **(BREAKING, correctness)** `nanconv` **no longer mutates the caller's input
    array** — NaNs are filled on a fresh buffer (`np.where(mask, 0.0, a)`).
  - **(ADDITIVE, PERF-02)** New keyword-only `compute_dtype` parameter selects
    the accumulation/division dtype. **Default `np.float32` reproduces the
    corrected output byte-for-byte;** reduced precision (e.g. `np.float16`)
    engages only when the caller explicitly opts in.
- **Migration note:** Callers that (a) relied on float16 rounding, or (b) relied
  on the input array being mutated in place, must adjust. To restore the old
  memory-for-accuracy trade explicitly, pass `compute_dtype=np.float16`.

## 4. `GradientFeature` opt-in `pixel_size` — ADDITIVE (M-10 / PERF-03-adjacent, 05-04)

- **Symbol:** `pc2img.features.derivative_features.GradientFeature(pixel_size=100)`;
  feature-name DSL suffix `_px<value>`
- **Old → new:** The previously hardcoded `np.gradient` spacing of `100` is now
  an opt-in constructor kwarg **and** an optional feature-name DSL suffix
  (`_px<value>`). **Default `pixel_size=100` reproduces the historical
  `1/100`-scaled output byte-for-byte.** The base-feature regex switched greedy
  `.+` → non-greedy `.+?` with an optional trailing `_px` group; because of the
  `$` anchor this is byte-identical for every name that omits `_px`.
- **Migration note:** None required — defaults reproduce prior output. Consumers
  wanting true pixel-spacing gradients can now pass `pixel_size` or append
  `_px<value>` to the feature name.

## 5. `HillshadeFeature` aspect convention documented — NO BEHAVIOR CHANGE (M-11, 05-04)

- **Symbol:** `pc2img.features.derivative_features.HillshadeFeature`
- **Old → new:** No math changed. The deliberate non-north-up (non-ESRI-compass)
  aspect handedness is now **documented** in the class docstring and pinned by a
  self-consistency (azimuth-sweep) characterization test.
- **Migration note:** None. Recorded for completeness so downstream illumination
  consumers know the convention is intentional and self-consistent, not ESRI.

## 6. Delaunay interpolation culling thresholds are now opt-in kwargs — ADDITIVE (M-06 / PERF-03 / D-06, 05-05)

- **Symbol:** `pc2img.strategies.interpolation.DelaunayInterpolation(interior_culling=True,
  area_scale=10.0, aspect_ratio_mad_factor=6.0, aspect_ratio_fallback_scale=10.0)`
- **Old → new:** The previously hardcoded triangle-quality culling constants
  (median-area × 10; aspect median + 6·MAD; × 10 fallback) are surfaced as
  constructor kwargs. **Defaults are byte-identical to the prior hardcoded
  behavior.** New `interior_culling=False` admits every in-hull triangle,
  reproducing `scipy.LinearNDInterpolator` NaN placement (the held-out oracle
  path). The dead `max_edge_thresh=None` branch was dropped (it never culled).
- **Migration note:** None required — defaults reproduce prior output. Interior
  culling remains intentional, downstream-validated default behavior (kept per
  D-06); the knobs only make it tunable.

## 7. Registry miss/duplicate exception unified to `RegistryLookupError` — BREAKING (surface only) (D-14, 05-07)

- **Symbol:** `pc2img.errors.RegistryLookupError(KeyError, RuntimeError)`; raised
  by `StrategyRegistry` (`register`, `get_strategy`, `key_of`) and
  `FeatureRegistry`
- **Old → new:** Registry misses/duplicates previously raised a bare `KeyError`
  (strategies) or `RuntimeError` (features). They now raise a single
  `RegistryLookupError` that **dual-inherits `KeyError` + `RuntimeError`**, so
  every existing `except KeyError` and `except RuntimeError` handler still
  catches it — 100% of observable catch behavior preserved, zero caller edits.
- **Migration note:** Only code matching on the **exact** exception class (e.g.
  `type(e) is KeyError`) would notice; no such call site exists in-repo. Downstream
  consumers can optionally tighten to `except RegistryLookupError`.

## 8. Image-cache on-disk format `.pkl` → `.npy` + `.meta.json` — BREAKING (D-05 / DSN-09, 05-09)

- **Symbol:** `pc2img.image_cache.DiskBackedImageStore` (now a thin wrapper over
  `GSEGUtils.lazy_disk_cache.DiskBackedStore[DiskBackedImageData]`)
- **Old → new:** The on-disk cache codec changed from a pickle `<key>.pkl` to
  `<key>.npy` + `<key>.meta.json` (`allow_pickle=False`). **A legacy `.pkl`
  cache file is refused — it degrades to a logged cache miss** and is
  re-materialized, never deserialized. This **eliminates the DSN-09 arbitrary-
  object deserialization sink by construction** (a crafted `.meta.json` still
  cannot coerce an unregistered class; explicit allow-list, no importlib
  fallback). Legacy method names (`add_image_to_store`, `image_data`,
  `offload(features=)`, `offload_image_data_to_disk`) are preserved as aliases,
  overwrite semantics kept via pre-`del`.
- **Migration note:** Any persisted `.pkl` cache directory from before this
  change is silently ignored (cache miss → recompute). No API call sites change;
  the public method surface is preserved via aliases.

## 9. `DiskBackedImageData` arithmetic now returns a plain `ndarray` — BREAKING (BUG-02 / DSN-02, 05-09)

- **Symbol:** `pc2img.image_cache.DiskBackedImageData` (now subclasses
  `GSEGUtils.lazy_disk_cache.DiskBackedNDArray`)
- **Old → new:** Arithmetic (`__array_ufunc__`) previously **raised
  `NotImplementedError`** (dead override). It now **dispatches through the
  inherited `__array_ufunc__` and returns a plain `np.ndarray`** (e.g.
  `dbid + dbid == arr + arr`). The `__array_priority__`, the `_image_data`
  buffer, and the duplicated buffer hooks were removed; only the `ndim in (2,3)`
  shape guard and `to_uint8` remain.
- **Migration note:** Code that caught `NotImplementedError` from arithmetic on a
  `DiskBackedImageData` will no longer see it — arithmetic now succeeds and
  yields an ndarray. Result type is `np.ndarray`, not `DiskBackedImageData`.

## 10. GSEGUtils gained a public `register_lazy_disk_cache_class` hook; pc2img pins it from PyPI (GSEGUtils 0.5.3) — BREAKING (dependency) (D-05 Option A, 05-08 / 05-09; bridge resolved 2026-07-11)

- **Symbol:** `GSEGUtils.lazy_disk_cache.register_lazy_disk_cache_class(cls)`
  (function + decorator form); consumed at import time in
  `pc2img.image_cache.__init__`
- **Old → new:** GSEGUtils' previously **closed** reload allow-list
  (`_LAZY_DISK_CACHE_CLASS_REGISTRY`) is now a **public extension point**. A
  downstream `LazyDiskCache` subclass registers itself into the reload allow-list
  via this hook (explicit allow-list, no importlib fallback — D-02 tampering
  posture preserved). pc2img registers `DiskBackedImageData` this way so
  offloaded rasters round-trip through the `.npy`+JSON codec.
- **Dependency state (RESOLVED 2026-07-11, in Phase 5):** during Phase-5 execution
  pc2img consumed the hook via a temporary `[tool.uv.sources]` git-rev bridge
  (GSEGUtils branch `gsd/register-lazy-disk-cache-class` @
  `2cf80835aa724f64a83853c8e35c91cb7640a919`, build `0.5.2.post4`). That branch has
  since been **released: the hook shipped in the published GSEGUtils `0.5.3` on
  PyPI.** Note the version: release-please emitted a pre-major **PATCH** bump (NOT
  `0.6.0`) because its config sets `bump-patch-for-minor-pre-major: true`, so a
  pre-1.0 `feat:` bumps patch. pc2img now pins **`GSEGUtils >= 0.5.3, < 1.0`** and
  resolves it straight from PyPI; the git-rev bridge + its `[tool.uv.sources]`
  entry were removed and `uv.lock` re-locked to the registry build. pc2img metadata
  is PyPI-clean (no direct-reference URLs).

### ✅ BC-01 dependency conversion — DONE (2026-07-11, Phase 5, pre-ship)

Originally handed to Phase 6, but completed early during Phase-5 execution (the
phase had not yet shipped, so there was no need to defer):

1. ✅ GSEGUtils released the hook to PyPI as **`0.5.3`** via its own release-please
   flow (owner-driven in the GSEGUtils workspace) — NOT `0.6.0`; pre-major patch bump.
2. ✅ pc2img pin bumped `~= 0.5` → **`>= 0.5.3, < 1.0`** (floor at the hook-bearing
   build; the `< 1.0` ceiling preserves the original pre-1.0 range and avoids a
   `~= 0.5.3` cap that would break the moment GSEGUtils ships `0.6.0`).
3. ✅ **DROPPED** the `[tool.uv.sources]` gsegutils git-rev entry from `pyproject.toml`.
4. ✅ Re-locked (`uv lock`) → `uv.lock` resolves `gsegutils 0.5.3` from PyPI;
   verified via `uv sync --frozen` + hook import + full suite (111 passed).

This BC-01 dependency item is **closed** — no Phase-6 follow-up remains for it. (The
broader BC-01 milestone deliverable still aggregates all Phase-5 BC notes below for
downstream consumers.)

## 11. Feature dependency cycle raises `ValueError`, not `RecursionError` — BREAKING (surface only) (DSN-08, 05-11)

- **Symbol:** `pc2img.features.manager.FeatureManager` dependency resolution
- **Old → new:** A cyclic feature-dependency graph previously recursed into a
  `RecursionError`. It now raises a clear
  `ValueError("dependency cycle: <name>")` via a DFS recursion-stack visited-set
  guard.
- **Migration note:** Callers catching `RecursionError` on a malformed feature
  graph should catch `ValueError` instead. Well-formed graphs are unaffected.

---

## Cross-cutting: mutable-default elimination (D-02 / D-17 consistency, 05-10 / 05-11)

Not a public-contract break, but recorded for completeness: the shared mutable
`LazyDiskCacheConfig()` default was eliminated at every generator/manager
construction site (`core.py`, `manager.py`, image_cache store, `interpolation.py`,
`tiled_generator.py`) in favor of a `None`-sentinel pattern. No observable API
change; prevents cross-instance config aliasing.

---

## Summary table (for Phase-6 BC-01 intake)

| # | Symbol | Kind | Class |
|---|--------|------|-------|
| 1 | `SphericalProjection.project_raw` / `inverse_projection` (wrapping FoV) | now raises `NotImplementedError` | BREAKING |
| 2 | `PerspectiveProjection(rotation_matrix=4×4)` | now raises `TypeError` | BREAKING |
| 3 | `util.nanconv` (float16→float32; no input mutation; `compute_dtype` opt-in) | correctness + additive param | BREAKING + ADDITIVE |
| 4 | `GradientFeature(pixel_size=)` + DSL `_px<v>` | new opt-in param | ADDITIVE |
| 5 | `HillshadeFeature` aspect convention | documented only | NO CHANGE |
| 6 | `DelaunayInterpolation` culling-threshold kwargs | new opt-in params | ADDITIVE |
| 7 | `errors.RegistryLookupError(KeyError, RuntimeError)` | unified miss type | BREAKING (surface) |
| 8 | image-cache format `.pkl` → `.npy`+`.meta.json` | on-disk format + DSN-09 sink removed | BREAKING |
| 9 | `DiskBackedImageData` arithmetic → plain `ndarray` | was `NotImplementedError` | BREAKING |
| 10 | GSEGUtils `register_lazy_disk_cache_class` + git-rev bridge | dependency; **Phase-6 conversion** | BREAKING (dependency) |
| 11 | `FeatureManager` dependency cycle → `ValueError` | was `RecursionError` | BREAKING (surface) |

*Collated 2026-07-11 (plan 05-12) from the D-17 running notes recorded in each
Phase-5 plan SUMMARY.*
