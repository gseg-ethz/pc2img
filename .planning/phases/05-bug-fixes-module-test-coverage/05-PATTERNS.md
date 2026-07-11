# Phase 5: Bug Fixes & Module Test Coverage - Pattern Map

**Mapped:** 2026-07-10
**Files analyzed:** 13 modified source files + 9 new test files (+ 1 barrel touch)
**Analogs found:** 22 / 22 (every target has an in-repo or sibling-repo precedent — this is a hardening + finish-the-migration phase, not greenfield)

> **How to read this.** Almost every "analog" here is an *in-repo precedent* the RESEARCH
> already anchored with `file:line`. This map's job is to give the planner accurate
> `<read_first>` lists and the exact copy-from excerpt per creation/heavy-modification target.
> It does NOT re-derive the 24-finding work-list — see `04-FINDINGS.md` (canonical) and
> RESEARCH §"Wave Grouping & Collision Map" for finding→file mapping.

---

## File Classification

### Modified source files

| File | Role | Data Flow | Closest Analog | Match |
|------|------|-----------|----------------|-------|
| `src/pc2img/image_cache/disk_backed_image_data.py` | model (array-like) | transform | `GSEGUtils/.../disk_backed_ndarray.py` (`DiskBackedNDArray`) | exact (reparent = subclass) |
| `src/pc2img/image_cache/disk_backed_image_store.py` | store | CRUD / file-I/O | `GSEGUtils/.../disk_backed_store.py` (`DiskBackedStore`) + in-repo use in `interpolation.py:112,162-166` | exact (adopt as base) |
| `src/pc2img/image_cache/__init__.py` | config (barrel) | — | own `__all__`; adds D-05 gate registration | self |
| `src/pc2img/strategies/registry.py` | registry infra | request-response | itself + `features/registry.py` (the two to unify) | self (unify) |
| `src/pc2img/features/registry.py` | registry infra | request-response | itself + `strategies/registry.py` | self (unify) |
| `src/pc2img/features/core.py` | model (ABC) | — | own `DerivativeFeatureStrategy._split_top_level` + `FeatureSpec.__init__` dep derivation | self (add `dependencies_for`) |
| `src/pc2img/strategies/projection.py` | strategy | transform | own `SphericalProjection` / `OrthographicProjection`; pchandler `FoV.tile()` refusal (D-15) | self + sibling-repo |
| `src/pc2img/util.py` | utility | transform | own `nanconv` / `convert_to_image` (in-place fixes) | self |
| `src/pc2img/features/derivative_features.py` | strategy | transform | own `ClipPercentileFeature` copy-before-mutate (`:259`); `GradientFeature`/`HillshadeFeature` (kept-behavior params) | self |
| `src/pc2img/strategies/interpolation.py` | strategy | transform | own `DelaunayInterpolation.__init__` opt-in-param pattern (`:102-120`) | self |
| `src/pc2img/features/manager.py` | orchestration | request-response | own `_get`/`_compute`; `core.py` None-sentinel for DSN-07 | self |
| `src/pc2img/tiled_generator.py` | orchestration | batch | own `extend_cache_paths`; `core.py` None-sentinel for DSN-07 | self |
| `src/pc2img/core.py` | orchestration | request-response | own `coerce_lazy_cfg` / `coerce_img_res` (None-sentinel coercion) | self (DSN-06) |
| `src/pc2img/features/rrim.py` | strategy | transform | module docstring/import ordering of any clean module (`disk_backed_ndarray.py` header) | pattern-match |

### New test files

| File | Role | Data Flow | Closest Analog | Needs real PCD? |
|------|------|-----------|----------------|-----------------|
| `tests/conftest.py` | test infra | — | `test_point_cloud_image_generator.py:13-32` (Dummy stubs + `make_point_cloud`) | factory *provides* it |
| `tests/test_projection.py` | test | property/parametrized | `test_rrim_features.py` structure; conftest PCD | **yes** |
| `tests/test_interpolation.py` | test | property/oracle | `test_rrim_features.py` (pure-array asserts) | no (pure arrays) |
| `tests/test_derivative_features.py` | test | property | `test_rrim_features.py`; dict-`fetch` stub | no (fetch stub) |
| `tests/test_feature_registry.py` | test | simple-assert | `test_rrim_features.py`; `registry as registry_module` import style | no |
| `tests/test_manager.py` | test | simple-assert | `test_point_cloud_image_generator.py`; conftest PCD | yes (minimal) |
| `tests/test_tiled_generator.py` | test | simple-assert | `test_point_cloud_image_generator.py`; conftest PCD | yes (heaviest) |
| `tests/test_util.py` | test | property/parametrized | `test_rrim_features.py` (pure-array) | no |
| `tests/test_image_store.py` | test | simple-assert + round-trip | `test_disk_backed_image_data.py` structure + xfails | no |

---

## Pattern Assignments

### `src/pc2img/image_cache/disk_backed_image_data.py` (D-04 reparent)

**Analog (base to inherit):** `/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_ndarray.py`
**In-repo consumer precedent:** `src/pc2img/strategies/interpolation.py:10-13,112,162-180`

The working `__array_ufunc__` to inherit (unwrap → delegate → return plain ndarray),
`disk_backed_ndarray.py:98-138`:
```python
def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    def _unwrap(x):
        if isinstance(x, DiskBackedNDArray):
            if x.offloaded:
                x.load()
            return x._data
        return x
    inputs_unwrapped = tuple(_unwrap(x) for x in inputs)
    if "out" in kwargs:
        kwargs["out"] = tuple(_unwrap(x) for x in kwargs["out"])
    return getattr(ufunc, method)(*inputs_unwrapped, **kwargs)
```
Base buffer-hook contract to reuse verbatim (`disk_backed_ndarray.py:51-53,152-171`): buffer is
`self._data`, `self._shape`, `self._dtype`; `_describe_buffer`, `_drop_buffer`,
`_describe_shape_dtype`, `_set_buffer`, `data` property, `__array__`, `__getitem__` all inherited.

**What the reparented class KEEPS (delete everything else) — target file today:**
`src/pc2img/image_cache/disk_backed_image_data.py:16-56` currently declares `__array_priority__`,
`self._image_data`, the broken `__array_ufunc__` (`:55-56` `raise NotImplementedError` → DELETE),
and duplicate buffer hooks. Reparented shape (~10 lines):
```python
class DiskBackedImageData(DiskBackedNDArray):          # was (LazyDiskCache, NDArrayOperatorsMixin)
    def __init__(self, image_data, **settings):
        assert image_data.ndim in (2, 3) and (image_data.ndim == 2 or image_data.shape[-1] == 3)
        super().__init__(image_data, **settings)       # buffer becomes self._data, not self._image_data

    @LazyDiskCache.ensure_loaded
    def to_uint8(self, pre_processing_func=None):
        if pre_processing_func is None:
            pre_processing_func = partial(convert_to_image, replace_nan_with="max", normalize=False)
        return pre_processing_func(self._data)          # MIGRATED from self._image_data (Pitfall 2)
```
Keep the `to_uint8` default `partial(convert_to_image, replace_nan_with="max", normalize=False)`
verbatim (current `:42-44`). Drop `__array_priority__ = 1000` (Assumption A1 — verify no
mixed-operand test depends on dispatch precedence).

**Proving test (BUG-02):** `a=DiskBackedImageData(arr2d); b=DiskBackedImageData(arr2d);
assert_array_equal(a+b, arr2d+arr2d)` and `assert type(a+b) is np.ndarray`. Flips the
`test_disk_backed_image_data.py` xfails at :50,:115,:155,:175,:241.

---

### `src/pc2img/image_cache/disk_backed_image_store.py` (D-05 adopt DiskBackedStore)

**Analog (base to wrap):** `/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py`
**In-repo precedent (construction + method names):** `interpolation.py:112,162-180`
**Full member-by-member map:** RESEARCH § "D-05 — Store API-Gap Analysis" (do not reproduce here).

The in-repo precedent proves the exact construction + method surface to mirror
(`interpolation.py:162-180`):
```python
DiskBackedStore[DiskBackedNDArray](
    config=self._lazy_disk_cache_config.extend_cache_path(hash_str),
    factory=DiskBackedNDArray,
    value_type=DiskBackedNDArray,
)
# ... .add_data_to_store("bary", bary) ; store["simplices"] ; .offload(pickle_container=True)
```

**Recommended shape — WRAPPER** (subclass `DiskBackedStore[DiskBackedImageData]`, supply
`factory=DiskBackedImageData, value_type=DiskBackedImageData`, re-alias legacy names). Legacy
surface FeatureManager depends on (must stay stable — see `manager.py:47,59,62,63,65` +
`cache_store.cache_dir`): `add_image_to_store`→`add_data_to_store` (preserve OVERWRITE semantics,
RESEARCH caveat), `image_data`→`store`, `offload(features=)`→`offload(keys=)`,
`offload_image_data_to_disk`→`offload(pickle_container=True)`. Delete the `pickle.load`/`.pkl`
sink at current `:42-54,73-74,137-168` (this is the DSN-09 security deliverable).

**BLOCKER — resolve before Wave B (RESEARCH §D-05 "The blocker"):** `DiskBackedStore._load_entry`
resolves reload class from a **module-private closed dict** `_LAZY_DISK_CACHE_CLASS_REGISTRY =
{"DiskBackedNDArray": ...}` (`disk_backed_store.py:61-79`). A reparented `DiskBackedImageData`
raises `ValueError: Unknown lazy_disk_cache_class 'DiskBackedImageData'` on offload→reload. Planner
MUST pick Option A (gated GSEGUtils public registration hook) or Option B (pc2img import-time
`_LAZY_DISK_CACHE_CLASS_REGISTRY["DiskBackedImageData"]=...` in `image_cache/__init__.py`). This
gates D-04+D-05 planning.

**Proving test (`test_image_store.py`):** assert no `pickle.load` sink; legacy `.pkl` → cache miss
(`disk_backed_store.py:437-443`); **offload→refetch round-trip** returns correct array (this is the
sensor that catches the blocker if unresolved — Pitfall 1).

---

### `src/pc2img/strategies/registry.py` + `src/pc2img/features/registry.py` (D-14 unification)

**Analogs:** the two registries themselves (read both in full — they are short).
**Full API-delta table + `dependencies_for` shapes:** RESEARCH § "D-14 — Registry Unification".

**Miss-exception type — dual inheritance keeps every caller working:**
```python
class RegistryLookupError(KeyError, RuntimeError): ...
```
Callers preserved unchanged: `_StrategyClass._validate` (`strategies/registry.py:125` `except
KeyError`), `get_strategy` (`:61`). Grep confirms ZERO `pytest.raises(KeyError|RuntimeError)` in
`tests/` — no test breaks. Miss sites to unify: `strategies/registry.py:37,62,91` (KeyError),
`features/registry.py:34,39,48,65` (RuntimeError). **Preserve the feature default-fallback**
(`features/registry.py:57-64`) — unknown feature name returns the `default=True` pseudo-spec, does
NOT raise (RESEARCH correction).

**`match()`-without-instantiation sub-fix** — add classmethod to `features/core.py` base so
`FeatureRegistry.match` (`features/registry.py:52-54`) stops constructing the class twice
(again in `manager.py:70`). Generalize the existing edge-derivation in `FeatureSpec.__init__`
(`features/registry.py:19-21`, single `[base_feature]`) plus the split-list families via the
existing `DerivativeFeatureStrategy._split_top_level` (`features/core.py:34-59`):
```python
# features/core.py — new classmethod on the strategy base
@classmethod
def dependencies_for(cls, params: dict) -> list[str]:
    # derive deps from regex groupdict WITHOUT __init__ side effects
    ...  # single [params["base_feature"]] for most; _split_top_level for average/sum/norm
```
Also fold DSN-11 here: `features/registry.py:27` `_default_cls: type[BaseFeatureStrategy] | None = None`.

**Proving tests (`test_feature_registry.py`):** unknown strategy key raises `RegistryLookupError`
AND is caught by `except KeyError`; unknown feature name → default fallback (no raise); ambiguous
feature match raises; `dependencies_for` returns correct deps without constructing the class.

---

### `src/pc2img/strategies/projection.py` (M-01, M-02/03/04, M-05)

**Analogs:** own `SphericalProjection` (`:99-155`) / `OrthographicProjection` (`:158-189`) /
`PerspectiveProjection` (`:192-223`); pchandler `FoV` seam API (RESEARCH §D-15).

**M-01 (BUG-01) Orthographic arity + column indexing** — current `project_raw` (`:176-189`)
returns a 2-tuple and uses fancy-index `pcd.xyz[mask, self._xyz_column_selection]` (wrong shape).
Match the 4-tuple contract that `SphericalProjection.project_raw` already satisfies
(`:112-123` returns `(coords, mask, mins, maxs)`) and `project()` consumes (`:79`):
```python
# fix: return 4-tuple + correct column slice
cols = self._xyz_column_selection
return pcd.xyz[mask][:, cols], mask, mins, maxs   # was: pcd.xyz[mask, cols], mask
```
Proving test: parametrize plane∈{xy,yz,xz}; assert `coords == xyz[mask][:, cols]` normalized.

**M-02/03/04 Perspective (one plan unit — same class):** M-04 delete the dead `project_raw`
override (`:194-195`); M-02 mask `Z_c ≤ 0` behind-camera points in `project` (`:216-223`); M-03
add camera translation → full `K·[R|t]·X`. The `@ pcd` matmul contract is
`_TransformArray.__matmul__` (annotation guarded under `TYPE_CHECKING`, `:22-28`).

**M-05 (D-15) seam guard — shared helper (discretion call, recommended):**
```python
def _reject_wrapping_fov(fov: FoV) -> None:
    if fov.crosses_pi:                              # pchandler FoV.crosses_pi -> left > right (fov.py:286)
        raise NotImplementedError(
            "SphericalProjection does not support wrapping FoVs (left > right, crosses_pi=True). "
            "Split the FoV at the wrap-around boundary before projecting."
        )
```
Mirrors pchandler's own `FoV.tile()` refusal (`/scratch/41_pchandler/.../fov.py:704-708`). Call
after `fov` resolves in `project_raw` (`:119`) AND after the `is not None` check in
`inverse_projection` (`:125-135`, reads `self._field_of_view.left/.right` into `np.linspace`).
Proving test: build wrapping FoV via `FoV.construct_without_bounds_check(left>right)` (fov.py:368);
assert both methods raise `NotImplementedError`.

---

### `src/pc2img/util.py` (M-07, M-08, M-09)

**Analog:** own `nanconv` (`:197,200-203`) and `convert_to_image`.
**M-07+M-08 are ONE edit — same `nanconv` function (Pitfall 3):** copy input before mutate
(`a = a.copy()`) AND accumulate/divide in **float32** (float16 overflows to `inf` on realistic
range magnitudes). M-09 (`convert_to_image` all-NaN + `normalize=True`) is a separate edit.
Proving tests: M-08 parametrized magnitudes {5e3,1.2e4,5e4} × kernels, finite & within float32 tol
of float64 ref; M-07 `array_equal(isnan(a), isnan(snapshot))`; M-09 all-NaN → valid uint8, no raise.

---

### `src/pc2img/features/derivative_features.py` (M-10, M-11, DSN-03, M-12)

**Analog:** own `ClipPercentileFeature` copy-before-mutate at `:259`
(`np.array(..., copy=True)`); `GradientFeature` / `HillshadeFeature` classes for kept-behavior params.
**DSN-03+M-12 are ONE edit — same `NormalizedFeature.compute` (Pitfall 4):** re-enable the
commented percentile validation (`:68`) and copy-before-mutate replacing in-place `out=img`
(`:80-81`), mirroring `ClipPercentileFeature:259`.
**M-10 / M-11 are KEPT-BEHAVIOR (Pitfall 5 — do NOT change output):** add opt-in params whose
defaults reproduce today's values. M-10: expose the `100` gradient spacing as a `pixel_size`-style
param (default `100`). M-11: keep aspect default; add a self-consistency test (NOT ESRI compass).
Characterization tests assert byte-identical output with default params. Param-plumbing analog:
`DelaunayInterpolation.__init__` opt-in kwargs with validation (`interpolation.py:102-120`).

---

### `src/pc2img/strategies/interpolation.py` (M-06 kept-behavior + PERF-03 param)

**Analog:** own `DelaunayInterpolation.__init__` (`:102-120`) — the established opt-in-param +
constructor-validation pattern to copy for exposing area/aspect-ratio culling thresholds
(defaults = today's values, zero behavior change). Characterization test uses
`scipy.LinearNDInterpolator` as the "NaN iff outside hull" oracle (RESEARCH "Don't Hand-Roll").

---

### Orchestration one-liners: `manager.py`, `tiled_generator.py`, `core.py`

**DSN-07 (mutable `LazyDiskCacheConfig()` default) — shared fix template across 3 waves.**
Sites: `manager.py:17`, `tiled_generator.py:96,109`, `image_cache/disk_backed_image_store.py:22`
(store site resolved by D-05). Copy the None-sentinel + `coerce_lazy_cfg` pattern from
`core.py:34-43` (also the DSN-06 fix source). `interpolation.py:111`
(`lazy_disk_cache_config or LazyDiskCacheConfig()`) is the in-file precedent for the sentinel.
**DSN-01 (BUG-03):** `tiled_generator.py:66-68` — build dict then assign (current
`dict.update()`→`None`). **DSN-08:** visited-set cycle guard in `manager.py` `request/visit`
(`:32-44`). **DSN-10:** import from `pc2img.core`, not the package barrel. **DSN-06:** flips the
existing xfail at `test_point_cloud_image_generator.py:35` — the xfail IS the proving test.

---

### `src/pc2img/features/rrim.py` (BUG-04)

**Analog:** any clean module header ordering (e.g. `disk_backed_ndarray.py:14-28` — docstring
first statement, then imports). Reorder so the module docstring is the first statement (populates
`__doc__`) and imports follow, clearing the E402×9. M-13 (ray sampling) is defer/log only — no fix.

---

### `tests/conftest.py` (NEW — Wave 0 fixture factory)

**Analog:** `test_point_cloud_image_generator.py:13-32` — lift `DummyProjection` /
`DummyInterpolation` duck-stubs + `make_point_cloud()` into shared fixtures.
```python
# existing precedent to generalize (test_point_cloud_image_generator.py:13-32)
class DummyProjection(ProjectionStrategy):
    def project_raw(self, pcd):
        return (np.empty((0,2), np.float32), np.zeros((pcd.nbPoints,), bool),
                np.zeros(2, np.float32), np.ones(2, np.float32))
    def inverse_projection(self): return None
class DummyInterpolation(InterpolationStrategy):
    def interpolate(self, values, points2d, grid_x, grid_y):
        return np.zeros_like(grid_x, dtype=np.float32)
def make_point_cloud(): return PointCloudData(np.empty((0,3), np.float32))
```
**Real-PCD factory (pchandler 2.1.0, VERIFIED):** `PointCloudData(np.ndarray Nx3)` constructs
directly; `**PointCloudDataKW` attaches named scalar fields via `scalar_fields=` (a dict). Exposes
`.nbPoints`, `.xyz`, `.spher`, `.fov`. Recommend `synthetic_pcd(n=…, with_scalar_fields=…)` +
lightweight `fetch_stub` (dict-backed lambda) + `fake_projection`. **Only TEST-03 (projection) and
TEST-05 (orchestration) need a real PCD** — TEST-04/TEST-06/interpolation are pure-array/stub.

---

### New per-module test files

**Structure analog:** `tests/test_rrim_features.py` (module-level `test_*` functions, pure-array
asserts, `from pc2img.features import registry as registry_module` import style) and
`tests/test_disk_backed_image_data.py` (class-grouped tests + `@pytest.mark.xfail(..., strict=False)`
with a Phase-5 reason string). **Test-first (D-12):** genuine fixes get `xfail` proving tests that
flip to pass; kept-behavior gets passing characterization tests from the start. See RESEARCH
§ "Wave 0 Gaps" for the per-file finding→sensor assignment and § "Phase Requirements → Test Map"
for sensor sufficiency (oracle vs simple-assert vs property).

---

## Shared Patterns

### None-sentinel config coercion (DSN-06, DSN-07)
**Source:** `src/pc2img/core.py:34-43` (`coerce_lazy_cfg`), in-file echo `interpolation.py:111`.
**Apply to:** `manager.py:17`, `tiled_generator.py:96,109`, and the DSN-06 constructor path.
Keep the fix consistent across all sites even though they land in different waves (one BC note).

### Dual-inheritance miss exception (D-14)
**Source:** new `class RegistryLookupError(KeyError, RuntimeError)`.
**Apply to:** both registries; every existing `except KeyError` / `except RuntimeError` keeps working.

### GSEGUtils primitive adoption (D-04, D-05)
**Source:** `interpolation.py:10-13,112,162-180` — the in-repo proof that `DiskBackedNDArray` +
`DiskBackedStore[T](config=, factory=, value_type=)` + `.add_data_to_store` + `.offload(
pickle_container=True)` work end-to-end today.
**Apply to:** the whole `image_cache/` reparent. **Key insight:** BUG-02 + DSN-09 are an
*unfinished migration*, not bugs to patch — `interpolation.py` already migrated; `image_cache/`
is the last holdout.

### pchandler seam API consumption (D-15)
**Source:** `FoV.crosses_pi` (`fov.py:286`), `FoV.tile()` refusal message (`fov.py:704-708`).
**Apply to:** both `SphericalProjection.project_raw` and `inverse_projection` via one shared helper.

### xfail-first proving test with Phase-5 reason string (D-12)
**Source:** `test_disk_backed_image_data.py:50-57`, `test_point_cloud_image_generator.py:35-43`
(`@pytest.mark.xfail(reason="Phase 5 (BUG-05 candidate): ...", strict=False)`).
**Apply to:** every genuine-fix proving test authored in Wave 0.

---

## No Analog Found

None. Every target has an in-repo or sibling-repo precedent (this is a hardening + coverage +
finish-the-migration phase). The only *novel* construct is `RegistryLookupError` (a two-line
dual-inheritance class) and `dependencies_for` (generalizes existing
`FeatureSpec.__init__` + `_split_top_level` logic) — both derived from in-repo code, not invented.

---

## Metadata

**Analog search scope:** `src/pc2img/{image_cache,strategies,features}/`, `src/pc2img/{core,util,
tiled_generator}.py`, `tests/`, `/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/`,
`/scratch/41_pchandler/src/pchandler/geometry/spherical/fov.py` (via RESEARCH anchors).
**Files read this session:** `disk_backed_image_data.py`, `disk_backed_image_store.py`,
`disk_backed_ndarray.py` (GSEGUtils), `interpolation.py`, `strategies/registry.py`,
`features/registry.py`, `features/core.py`, `features/manager.py`, `projection.py`,
`test_point_cloud_image_generator.py`, `test_disk_backed_image_data.py`, `test_rrim_features.py`.
**Pattern extraction date:** 2026-07-10
</content>
</invoke>
