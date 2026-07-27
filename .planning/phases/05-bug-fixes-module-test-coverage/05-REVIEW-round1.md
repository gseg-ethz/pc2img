---
phase: 05-bug-fixes-module-test-coverage
reviewed: 2026-07-11T00:00:00Z
depth: deep
files_reviewed: 15
files_reviewed_list:
  - src/pc2img/strategies/projection.py
  - src/pc2img/util.py
  - src/pc2img/features/derivative_features.py
  - src/pc2img/strategies/interpolation.py
  - src/pc2img/features/rrim.py
  - src/pc2img/strategies/registry.py
  - src/pc2img/features/registry.py
  - src/pc2img/features/core.py
  - src/pc2img/errors.py
  - src/pc2img/image_cache/disk_backed_image_data.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - src/pc2img/image_cache/__init__.py
  - src/pc2img/tiled_generator.py
  - src/pc2img/features/manager.py
  - src/pc2img/core.py
findings:
  critical: 0
  warning: 2
  info: 7
  total: 9
status: issues
---

# Phase 5: Code Review Report

**Reviewed:** 2026-07-11
**Depth:** deep (cross-file: import graph, registry/allow-list, call chains)
**Files Reviewed:** 15
**Status:** issues_found

## Summary

I traced every Phase-5 bug fix against its finding, cross-checked the
GSEGUtils primitives the image-cache reparent depends on (read the installed
`DiskBackedNDArray` / `DiskBackedStore` source), and verified the security
posture of the DSN-09 removal empirically.

**The core fixes are correct and the "kept-behavior" claims hold up.** I
independently confirmed against `git show`:

- **Orthographic indexing (M-01):** `pcd.xyz[mask][:, cols]` is the right
  two-step index; the old `xyz[mask, cols]` diagonal broadcast is gone.
- **`nanconv` (M-07/M-08):** input array is no longer mutated (fresh
  `np.where` buffer), float32 accumulation is the default, `compute_dtype`
  is a clean opt-in.
- **GradientFeature `pixel_size` (D-07):** default `100.0` is byte-for-byte
  vs the old hardcoded `np.gradient(img, 100, …)`.
- **Delaunay culling (D-06/PERF-03):** the surfaced kwargs
  (`area_scale=10`, `mad_factor=6`, `fallback=10`) reproduce the previously
  hardcoded constants exactly; only the always-`None` `max_edge_thresh`
  dead branch was dropped.
- **RegistryLookupError dual-inheritance:** empirically verified that both
  `except KeyError` and `except RuntimeError` still catch it — handler
  semantics are preserved.
- **Security (DSN-09):** confirmed there is **no residual deserialization
  sink** in pc2img. Array reload goes through GSEGUtils'
  `np.load(..., allow_pickle=False)` + JSON sidecar, class resolution is an
  explicit allow-list with no `importlib`, and
  `register_lazy_disk_cache_class(DiskBackedImageData)` is a supervised,
  idempotent, subclass-checked registration. `pickle_container=True` writes
  the codec pair (no actual pickle). No blocker here.

**No BLOCKER-severity defects were found.** Two WARNING-level issues remain,
both concrete: a latent crash on `SphericalProjection.inverse_projection`'s
own default argument, and a diagnostics regression from the `KeyError`
`__str__` quoting on the unified registry error. The rest are INFO.

## Warnings

### WR-01: `SphericalProjection.inverse_projection` crashes on its own default `field_of_view=None`

**File:** `src/pc2img/strategies/projection.py:150-172`
**Issue:** The full `inverse_projection` body was newly written in 05-02
(pre-05-02 it was the empty stub `def inverse_projection(self): ...`). The
wrapping-FoV guard is applied **only** when a FoV exists:

```python
if self._field_of_view is not None:
    _reject_wrapping_fov(self._field_of_view)
...
horizontal_range = np.linspace(self._field_of_view.left, self._field_of_view.right, ...)
```

But the constructor default is `field_of_view=None`, and the `linspace`
calls immediately below dereference `self._field_of_view.left/.right/.top/
.bottom` unconditionally. Constructing `SphericalProjection()` (no FoV) and
calling `inverse_projection(range_img)` raises a bare
`AttributeError: 'NoneType' object has no attribute 'left'` instead of a
clear "inverse requires a field_of_view" message. The guard already proves
awareness of the `None` case, so the body is internally inconsistent. This
path is untested — `test_spherical_inverse_roundtrip_shapes` always passes an
explicit `FoV` (line 129-132), and `project_raw`'s None path works only
because it falls back to `pcd.fov`, which `inverse_projection` does not do.
**Fix:** Fail fast with a domain message, mirroring the other refusals in
this file:
```python
if self._field_of_view is None:
    raise ValueError(
        "SphericalProjection.inverse_projection requires an explicit "
        "field_of_view; none was configured."
    )
_reject_wrapping_fov(self._field_of_view)
```

### WR-02: Unified `RegistryLookupError` double-quotes every registry error message (KeyError `__str__` regression)

**File:** `src/pc2img/errors.py:28`; message sites
`src/pc2img/strategies/registry.py:39,64,93`,
`src/pc2img/features/registry.py:45,53,62,82`
**Issue:** Because `RegistryLookupError` subclasses `KeyError`, it inherits
`KeyError.__str__`, which returns `repr(args[0])`. I verified empirically:

```
str(RegistryLookupError("No strategy registered under x")) == "'No strategy registered under x'"
```

Every registry miss/duplicate message is now wrapped in an extra pair of
quotes when rendered (logs, tracebacks, `str(e)`). This is a genuine
diagnostics regression for the **FeatureRegistry** paths, which previously
raised `RuntimeError` with clean, unquoted messages (e.g.
`Multiple patterns match 'x'`, `No pattern for 'x' and no default registered`,
`Pattern … already registered`). Those now render as
`'Multiple patterns match \'x\''`. Handler semantics are fine; only the
human-readable message quality degrades — across all seven message sites.
**Fix:** Give the unified error a stable `__str__` so both registries render
cleanly regardless of the `KeyError` base:
```python
class RegistryLookupError(KeyError, RuntimeError):
    def __str__(self) -> str:
        return self.args[0] if self.args else ""
```

## Info

### IN-01: `RegistryLookupError` docstring states the wrong MRO

**File:** `src/pc2img/errors.py:14-16`
**Issue:** The docstring claims the MRO is
`RegistryLookupError → KeyError → RuntimeError → LookupError → Exception`.
The actual C3 linearization (verified) is
`RegistryLookupError → KeyError → LookupError → RuntimeError → Exception →
BaseException → object` — `LookupError` precedes `RuntimeError`, not the
reverse. The dual-catch guarantee still holds, but the documented ordering is
inaccurate.
**Fix:** Correct the docstring ordering to
`KeyError → LookupError → RuntimeError → Exception`.

### IN-02: Non-greedy base-feature regexes silently reinterpret names ending in a numeric suffix

**File:** `src/pc2img/features/derivative_features.py:32-35` (Gradient),
`77-80` (Normalized)
**Issue:** The regex switched from greedy `(?P<base_feature>.+)` to
non-greedy `.+?` plus an optional trailing group (`_px<n>` / `_<low>_<high>`).
For a base feature whose name legitimately ends in `_px5` or `_10_20`, the
parser now peels that suffix off as `pixel_size`/percentiles rather than
treating it as part of the base name — a silent semantic shift. The `$`
anchor makes this byte-identical for the common case (names without such
suffixes), so risk is low and it is documented as opt-in, but it is a latent
ambiguity for exotic feature names.
**Fix:** None required for current names; if defensive, document that a base
feature name may not end in the reserved `_px<digits>` /
`_<num>_<num>` shapes.

### IN-03: Diamond dependencies double-append base features (redundant compute)

**File:** `src/pc2img/features/manager.py:38-58,63-70`
**Issue:** `visit` appends a `BaseFeatureStrategy` to `self._base_features`
every time it is reached, and the cycle `visiting` set is discarded on
backtrack (correctly, to avoid false cycle flags). But a diamond within a
single request — e.g. `sum_(range,log_range)`, where both arms reach `range`
— appends `range` twice. `get_base_features` then constructs and runs
`inst.compute` on `range` twice; the returned dict dedups by name so the
final raster and interpolation are correct, only the 1-D per-point
computation is wasted. Correctness is preserved; this is efficiency only
(out of v1 scope, noted for completeness).
**Fix:** De-dup while appending: `if spec.name not in seen: self._base_features.append(spec)` guarded by a per-request set.

### IN-04: `TIGSettings` (and `extend_cache_paths`/`as_kwargs`) is dead in the runtime path

**File:** `src/pc2img/tiled_generator.py:49-86`
**Issue:** The BUG-03/DSN-01 fix (build-then-assign instead of
`dict.update()` returning `None`) is correct, but it lands on
`TIGSettings.extend_cache_paths`, which `TiledPointCloudImageGenerator` never
calls — the generator stores fields directly and does its own per-tile
extension in `_process_tile` (lines 161-171), which is independently correct
(fresh `dict(...)` copy, reassigned). `TIGSettings` is instantiated only by
`tests/test_tiled_generator.py`. So the runtime fix is really the
`_process_tile` logic; `TIGSettings` is a parallel, unused settings
abstraction.
**Fix:** Either wire `TIGSettings` into `__init__`/`_process_tile` as the
single source of per-tile settings, or move it out of the production module
if it is test-only scaffolding.

### IN-05: `PerspectiveProjection` is registered but not exported from `strategies.__init__`

**File:** `src/pc2img/strategies/__init__.py:1-32`
**Issue:** `@PROJECTIONS.register("perspective")` runs at import (via the
`from .projection import …` side effect), so the `"perspective"` key works.
But unlike `SphericalProjection`/`OrthographicProjection`, the
`PerspectiveProjection` class is absent from `__all__` and the re-export
list, so `from pc2img.strategies import PerspectiveProjection` fails. This is
an inconsistent public surface for a newly added strategy.
**Fix:** Add `PerspectiveProjection` to the `.projection` import and
`__all__` for parity with the other projections.

### IN-06: `DiskBackedImageData` uses `assert` to validate raster shape (stripped under `-O`; rejects valid non-3-channel features)

**File:** `src/pc2img/image_cache/disk_backed_image_data.py:31`
**Issue:** `assert image_data.ndim in (2, 3) and (image_data.ndim == 2 or
image_data.shape[-1] == 3)` validates externally-shaped data (feature raster
output) with an `assert`, which CLAUDE.md reserves for internal invariants
(and which `python -O` strips). It also rejects legitimate feature outputs
with a channel count other than 3 — notably
`multigradocc_<base>_<sigmas>_mask`, which returns an `(H, W, 2)` stack
(`derivative_features.py:701-703`) and would `AssertionError` when submitted
to the store. The assertion is carried verbatim from the pre-reparent class,
so this is pre-existing rather than a Phase-5 regression, but the reparent
(05-09) touched this file and left it unaddressed.
**Fix:** Convert to an explicit `raise ValueError(...)` and either widen the
channel check to `shape[-1] >= 1` or explicitly enumerate supported channel
counts.

### IN-07: `NormalizedFeature.compute` lacks the all-NaN guard its sibling has

**File:** `src/pc2img/features/derivative_features.py:96-104`
**Issue:** `ClipPercentileFeature.compute` early-returns on
`if not np.isfinite(values).any(): return values` (line 322), but the
sibling `NormalizedFeature.compute` does not. On an all-NaN raster,
`np.nanpercentile` yields `nan` bounds, `high_bound - low_bound` is `nan`
(`!= 0` is `True`), and the divide produces an all-`nan` output silently
rather than short-circuiting. No crash, but the two percentile features
handle the degenerate case inconsistently.
**Fix:** Mirror the guard:
`if not np.isfinite(img).any(): return img`.

---

_Reviewed: 2026-07-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
