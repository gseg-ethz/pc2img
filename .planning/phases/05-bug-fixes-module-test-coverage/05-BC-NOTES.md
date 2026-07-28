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

## 12. RRIM feature-name validation moved from compute time to request time — BREAKING (surface only) (G11, 05-14)

- **Symbol:** the `pc2img.features.rrim` name grammar, surfaced through
  `pc2img.features.registry.FeatureRegistry.match` and
  `pc2img.features.manager.FeatureManager.request`
- **Old → new:** RRIM argument validation previously ran when the feature was
  **constructed**, i.e. at **compute time**. `FeatureRegistry.match`
  (`registry.py:71`) now calls `cls.dependencies_for(spec.params)` on **every**
  matched path, and the RRIM overrides parse through `_parse_rrim_config` →
  `_validate_config`. Because `FeatureManager.request` calls `match` on
  user-supplied names, a malformed RRIM name inside a batch — e.g.
  `generate(["range", "rrim_(r0)"])` — now raises a bare **`ValueError` from
  inside `request()`**, aborting the **entire batch** before any feature
  computes. **Both the timing and the exception type shifted.**
- **Migration note:** Arguably a fail-fast improvement — an unusable RRIM name no
  longer costs a full base-raster computation before failing. But callers that
  catch `RegistryLookupError` around `request()`, or that wrap only the compute
  phase, will **not** catch it: catch `ValueError` around the request call
  instead. Same class as entry 11 (the DSN-08 cycle `ValueError`).
- **Carry into Phase 6 BC-01:** yes.

## 13. PerspectiveProjection rejects a non-3×3 or non-pinhole intrinsics matrix K — BREAKING (G12, 05-14)

- **Symbol:** `pc2img.strategies.projection.PerspectiveProjection(projection_matrix=...)`,
  reachable via the `"perspective"` string API and `PROJECTIONS.create(...)`
- **Old → new:** `K` was previously **stored unchecked**. It is now **validated at
  construction**, so an external caller passing a full 3×4 composed projection
  matrix `P = K[R|t]` (shape mismatch) or an up-to-scale / unnormalized `K` with
  `K[2,2] != 1` (common in some calibration exports) now **raises** where it
  previously constructed. The refusal is **INTENTIONAL**, not a defect: a
  non-pinhole `K` desyncs the sign of the perspective divisor from the
  behind-camera depth cull, which would **mislocate** points instead of culling
  them — silently wrong pixels rather than a loud refusal.
- **Migration note:** Two concrete steps — (1) **normalize `K` by `K[2,2]`** so the
  bottom row is `[0, 0, 1]`; (2) **pass `K` and `[R|t]` separately** (`K` as
  `projection_matrix`, the extrinsic via `rotation_matrix=` + `translation=`)
  rather than a composed `P`. Note explicitly that **skew in `K[0,1]` is still
  accepted** — only the bottom row is checked — so skewed intrinsics are a
  non-issue. Sibling of entry 2, the D-17 4×4-rotation breaking change.
- **Carry into Phase 6 BC-01:** yes.

## 14. RRIM `z_factor` token: grammar widened + shortest-round-trip formatting — ADDITIVE + BREAKING (narrow) (G9, 05-14)

- **Symbol:** the `zF` option token of the RRIM feature-name DSL
  (`pc2img.features.rrim._Z_FACTOR_RE`) and the derived cache key
  `RRIMConfig.pack_feature_name()`
- **Old → new**, two halves:
  - **(a) ADDITIVE** — the `zF` token now accepts **exponent notation**
    (`z1e-05`, `z1E-05`, `z1e+20`) in addition to plain decimals. Every feature
    name valid before stays valid, and names like `rrim_(range,z1e-05)` become
    expressible at all. `z_factor` is a plain scale multiplier
    (`raster * z_factor`, validated `> 0`), so sub-1e-4 values are legitimate
    unit conversions (µm → m = 1e-06).
  - **(b) BREAKING but narrow** — the **emitted** `z` token switched from
    6-significant-figure general formatting (`format(v, "g")`) to the **shortest
    exactly round-tripping form** (`repr(float(v))`; integers still emit
    `str(int(v))`).
- **Owner's accepted rationale (verified before the change landed):** the emitted
  token is **byte-identical** for every `z` that works correctly today — 0.5, 2.5,
  0.0001, 0.001, 0.01, 0.1, 0.25, 0.75, 1.5, 1.0, 2.0, 10, 100, 1234567 and every
  integer `z`. The **only** tokens that change are exactly those already
  **mis-encoding their config** (`1.23457` from 1.2345678; `3.33333` from
  3.3333333333). **Cache-key churn is therefore ~zero and is paid only where the
  key was WRONG.** Full precision is fixed, not documented around.
- **Defects this closes (both reproduced at HEAD):**
  1. Below 1e-4 the derived pack name (`rrim_pack_(range,r16,d8,z1e-05)`) was
     **unparseable** — `FEATURES.match` raised
     `ValueError: Unknown RRIM option 'z1e-05'` at **request time**, aborting the
     whole feature batch.
  2. Above 6 significant figures two **distinct** configs collided on **one**
     name — `z=1.2345678` and `z=1.2345681` both emitted
     `rrim_pack_(range,r16,d8,z1.23457)` — making the cache key
     **non-injective**, so a caller could receive a raster computed under
     parameters it never requested.
- **Migration note:** No API call changes. A persisted cache directory holding a
  truncated `rrim_pack_(...,z1.23457)` entry simply **degrades to a cache miss**
  and is recomputed under the now-correct key; the stale entry is inert, never
  mis-served.
- **Carry into Phase 6 BC-01:** yes.

## 15. DiskBackedImageStore refuses a key whose on-disk path escapes the cache directory — BREAKING (surface only) (WR-02, 05-15)

- **Symbol:** `pc2img.image_cache.DiskBackedImageStore` (exported from the public
  barrel `pc2img.image_cache.__all__`) — specifically the on-disk path builders
  `_get_npy_path` / `_get_meta_path`, which every disk-touching route goes
  through: `add_image_to_store` (insertion), the offload write
  (`DiskBackedStore._store_entry`), the load (`DiskBackedStore._load_entry`) and
  `del store[key]` (unlink).
- **Old → new:** A key containing a parent-directory segment (`../victim`), an
  absolute path (`/tmp/x/victim`) or an embedded traversal (`a/../../victim`)
  previously produced a **real path outside the configured cache directory**, and
  the store then used it. Reproduced 2026-07-28 on HEAD: with a sentinel file one
  level above the cache directory, `add_image_to_store("../victim", arr)` +
  `offload_image_data_to_disk("../victim")` **overwrote the sentinel with an NPY
  header**, and `del store["../victim"]` then **deleted it**. Such a key now
  raises **`ValueError` at the first path build** — for insertion, that is before
  any file outside the cache directory is created or truncated.
- **Reachability, stated honestly:** this was **NOT reachable through the
  feature-name DSL**. Every registered `regex_pattern` anchors on a literal prefix
  (`range`, `scalar_field_`, `rrim`, `sqrt_`, …), so no store key derived from a
  feature name can begin with `..` or `/`. It is therefore **hardening of a public
  store API**, not a live exploit path from untrusted point-cloud metadata. It is
  recorded as breaking because the store is publicly exported and because Phase 5
  (entry 14's sibling fix, 05-14 `f776011`) is what turned `__delitem__` into a
  file-deletion primitive in the first place.
- **Scope:** containment is about **escaping, not nesting**. A key that resolves
  *inside* the cache directory is still accepted — `".."` becomes a file literally
  named `...npy` inside it, and `"sub/nested"` stays under it. All six realistic
  feature-name shapes (`range`, `rrim_pack_(range,r16,d8,z1.2345678)`,
  `hillshade_range_315_45`, `norm_(range,2,98)`, `scalar_field_intensity`,
  `grad_range_px0.5`) still complete add → offload → reload unchanged, pinned by
  `test_containment_guard_accepts_realistic_feature_names`. Refusals are pinned by
  `test_escaping_key_delete_refuses_and_leaves_outside_file_intact` and
  `test_escaping_key_add_refuses_before_writing_outside_cache_dir`.
- **Migration note:** Any caller passing a raster key that is not a plain name
  must sanitize it before handing it to the store (strip `..` segments, reject
  absolute paths, or hash the key). Nesting under the cache directory is still
  allowed; only escaping is refused. `__delitem__` itself is unchanged — the
  guard rides inside the path builders, so the 05-14 delegate-then-unlink
  ordering and its single membership authority are preserved by construction.
- **Carry into Phase 6 BC-01:** yes.

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
| 12 | RRIM name validation at request time | now raises `ValueError` from `request()` | BREAKING (surface) |
| 13 | `PerspectiveProjection(projection_matrix=non-pinhole or non-3×3)` | now raises | BREAKING |
| 14 | RRIM `zF` token (exponent accepted; shortest round-trip emission) | grammar widened + key formatting | ADDITIVE + BREAKING (narrow) |
| 15 | `DiskBackedImageStore` key whose path escapes the cache dir | now raises `ValueError` at the first path build | BREAKING (surface) |

*Collated 2026-07-11 (plan 05-12) from the D-17 running notes recorded in each
Phase-5 plan SUMMARY.*

*Entries 12–14 added 2026-07-27 by plan 05-14 from the round-2 review gaps
G9 / G11 / G12.*
