# Testing Patterns

**Analysis Date:** 2026-07-08

## Test Framework

**Runner:**
- `pytest` (declared in the `dev` optional-dependency group of `pyproject.toml`; no pinned version).
- No `[tool.pytest.ini_options]` section, no `pytest.ini`, no `conftest.py`, and no `testpaths` config. Pytest uses default discovery: `test_*.py` files, `Test*` classes, `test_*` functions. Running `pytest` from the repo root collects `tests/`.

**Assertion Library:**
- Plain `assert` statements (pytest rewrites them). Numpy comparisons use `numpy.testing.assert_array_equal` / `np.allclose` / `np.array_equal` and NaN-aware checks (`equal_nan=True`, `np.nanmax`, `np.isnan`).

**Memory profiling:**
- `memory_profiler` is in the `dev` extra, used for ad-hoc profiling (not part of the automated suite).

**Run Commands:**
```bash
pip install -e ".[dev]"     # install pytest + dev tooling
pytest                       # run all tests (from repo root)
pytest tests/test_rrim_features.py            # run one file
pytest tests/test_rrim_features.py -k ridge   # run by keyword
pytest -q                    # quieter output
```
Note: there is **no CI test job**. The only GitHub workflow (`.github/workflows/release-please.yml`) handles releases, not testing. Tests are run locally/manually.

## Test File Organization

**Location:**
- Separate top-level `tests/` directory (not co-located with source). One test module per source unit under test.

**Naming:**
- `test_<subject>.py`, where the subject mirrors the source module/class: `test_point_cloud_image_generator.py` ↔ `core.PointCloudImageGenerator`, `test_disk_backed_image_data.py` ↔ `image_cache/disk_backed_image_data.py`, `test_rrim_features.py` ↔ `features/rrim.py`.

**Structure:**
```
tests/
├── test_point_cloud_image_generator.py   # generator constructor / pipeline (current API)
├── test_rrim_features.py                  # RRIM feature registry + compute (current API)
├── test_disk_backed_image_data.py         # image cache wrapper (current API)
├── test_disk_backed_image_store.py        # STALE — imports removed modules (see Gaps)
└── test_lazy_disk_cache.py                # STALE — imports _old.v1 (see Gaps)
```
A separate `_tests/` directory holds only a binary data fixture (`_tests/01_test.dat`), not test code.

## Test Structure

Two styles coexist:

**1. Flat module-level functions** (preferred for newer tests — `test_rrim_features.py`, `test_point_cloud_image_generator.py`):
```python
def test_compute_rrim_flat_plane_returns_neutral_gray() -> None:
    raster = np.zeros((9, 9), dtype=np.float32)
    result = rrim_module.compute_rrim(raster, max_distance=4, num_directions=8)

    assert np.nanmax(np.abs(result.slope)) == 0.0
    assert np.nanmax(np.abs(result.structure)) < 1e-6
    assert np.allclose(result.rgb[4, 4], np.array([0.5, 0.5, 0.5], dtype=np.float32))
```
- Descriptive, behavior-oriented test names (`test_compute_rrim_distinguishes_ridge_from_valley`, `test_constructor_normalizes_omitted_lazy_disk_cache_config`).
- `-> None` return annotations on test functions; `from __future__ import annotations` at the top.
- Arrange/act/assert with a blank line separating construction from assertions.

**2. Class-grouped tests** (`test_disk_backed_image_data.py`, `test_lazy_disk_cache.py`):
```python
class TestOffloadingAndLoading:
    def test_offload_and_load_with_cache(self, tmp_path: Path, caplog):
        ...
        data_obj.offload()
        assert data_obj.offloaded
        assert cache_file.exists()
```
- `Test*` classes group related behaviors (`TestInitialization`, `TestOffloadLoad`, `TestGetstateSetstatePickle`, `TestThreadSafety`). No shared class state — grouping is purely organizational.

**Patterns:**
- Setup is inline in each test (build a small numpy array, construct the object).
- No explicit teardown; filesystem isolation is delegated to the `tmp_path` fixture.
- Assertions frequently probe internal/private state directly (`data_obj._image_data is None`, `d._finalizer.alive`, `state["_buffer"]`) — tests are white-box and tightly coupled to implementation details of the cache classes.

## Mocking

**Framework:** No `unittest.mock` / `pytest-mock`. Test doubles are hand-written.

**Patterns:**
- **Dummy strategy subclasses** implementing the ABC contract with trivial bodies, used to exercise the pipeline without real projection/interpolation math:
```python
class DummyProjection(ProjectionStrategy):
    def project_raw(self, pcd):
        return (np.empty((0, 2), np.float32), np.zeros((pcd.nbPoints,), bool),
                np.zeros(2, np.float32), np.ones(2, np.float32))
    def inverse_projection(self):
        return None

class DummyInterpolation(InterpolationStrategy):
    def interpolate(self, values, points2d, grid_x, grid_y):
        return np.zeros_like(grid_x, dtype=np.float32)
```
(`tests/test_point_cloud_image_generator.py`)
- **Lambda fetchers** substitute the `FeatureManager` dependency-resolution callback in feature tests: `rrim_feature.compute(None, lambda name: raster if name == "range" else pack)` (`tests/test_rrim_features.py`). The `pcd` argument is passed as `None` since derivative features ignore it.
- **Module import stubs**: `test_rrim_features.py` builds a fake `pchandler` module and hand-loads `features/core.py`, `features/registry.py`, `features/rrim.py` under a throwaway package name via `importlib.util.spec_from_file_location`, so RRIM can be tested in isolation without importing the heavy `pchandler`/`GSEGUtils` dependency chain. This is the pattern to reuse when a unit under test would otherwise pull in optional/CUDA-heavy dependencies.

**What to mock:**
- External heavy deps (`pchandler`, CUDA-backed libs) via import stubs when they are not the subject under test.
- Strategy collaborators of the pipeline via Dummy* subclasses.

**What NOT to mock:**
- Numpy/scipy numerics — feed real small arrays and assert on real computed values.
- The filesystem — use the real filesystem under `tmp_path` rather than mocking IO (the cache layer's whole point is disk behavior).

## Fixtures and Factories

**Test data:**
- Small deterministic numpy arrays built inline. Helper factory functions live at module top:
```python
def dummy_gray_image(shape=(10, 10), dtype=np.float32):
    return np.random.rand(*shape).astype(dtype)

def dummy_rgb_image(shape=(8, 8, 3), dtype=np.float64):
    return np.random.rand(*shape).astype(dtype)
```
(`tests/test_disk_backed_image_data.py`)
- Structured synthetic inputs are used to make assertions meaningful: ridge/valley profiles via `np.tile`, ramps via `np.where`, NaN injection (`raster[2, 2] = np.nan`) to test edge/NaN handling (`tests/test_rrim_features.py`).
- `pytest.fixture` is used lightly for shared sample arrays: `@pytest.fixture def sample_array(): return np.arange(100, dtype=np.float64)` (`tests/test_lazy_disk_cache.py`).

**Location:**
- No `conftest.py` and no shared fixtures package. Factories/fixtures are defined per-module. Randomness is unseeded (`np.random.rand`) but tests assert on shape/roundtrip equality rather than exact random values, so this is stable.

**Built-in fixtures used:**
- `tmp_path: Path` — per-test temp directory for cache files (heavily used across cache tests).
- `caplog` — assert on emitted log messages: `caplog.set_level("DEBUG"); assert "Caching disabled ==> `offload()` ignored." in caplog.text`.

## Coverage

**Requirements:** None enforced. No `pytest-cov`, no coverage config, no CI gate.

**What is currently covered (current API):**
- `PointCloudImageGenerator` constructor config normalization (`test_point_cloud_image_generator.py`).
- `DiskBackedImageData` init/offload/load, `__array__` protocol, pickle roundtrips, finalizer/purge behavior (`test_disk_backed_image_data.py`).
- RRIM feature: `compute_rrim` numerics (flat/ridge/valley/steepness/NaN) and registry wiring for `rrim` / `rrim_component_(...)` names (`test_rrim_features.py`).

**View coverage (if adding pytest-cov):**
```bash
pip install pytest-cov
pytest --cov=pc2img --cov-report=term-missing
```

## Test Types

**Unit tests:**
- The bulk of the suite. Isolated units (a feature's `compute`, a cache object's lifecycle, a constructor's coercion) with hand-built doubles.

**Integration tests:**
- Light. `test_point_cloud_image_generator.py` exercises the generator + `FeatureManager` + cache store wiring end-to-end (with dummy strategies), verifying the on-disk cache dir is created and feature listing works.

**E2E tests:**
- Not used. There is no test that runs a real point cloud through real projection + interpolation + feature computation to an image on disk.

## Common Patterns

**NaN- and shape-aware assertions:**
```python
assert np.isnan(result.structure[2, 2])
assert np.nanmax(np.abs(result.structure[:, 0])) < 1e-6
assert rrim_rgb.shape == raster.shape + (3,)
assert np.allclose(structure, pack[..., 2], equal_nan=True)
```

**Error testing:**
```python
with pytest.raises(AssertionError):
    DiskBackedImageData(np.zeros((5, 5, 5)))   # invalid dimensionality
```
(`tests/test_disk_backed_image_data.py`). Prefer raising/asserting on specific exception types; feature constructors that raise `ValueError` on bad params (e.g. clip percentiles, sigmas) are good candidates for `pytest.raises(ValueError)` coverage that does not yet exist.

**Log-output testing:**
```python
caplog.set_level("DEBUG")
data_obj.offload()
assert "Caching disabled ==> `offload()` ignored." in caplog.text
```

**Filesystem/lifecycle testing:**
```python
data_obj = DiskBackedImageData(img, cache_file)
serialized = pickle.dumps(data_obj)   # forces offload
assert cache_file.exists()
del data_obj; gc.collect()
assert cache_file.exists()            # finalizer was canceled on getstate
```

**Thread-safety testing:**
- `test_lazy_disk_cache.py::TestThreadSafety` spins up 4 `threading.Thread` workers hammering `offload()`/`load()` to assert the cache's lock keeps the buffer consistent.

## Test Coverage Gaps

- **Stale/broken test modules.** `tests/test_disk_backed_image_store.py` imports `pc2img.image_generation` (module does not exist) and `_old.v1.image_cache`; `tests/test_lazy_disk_cache.py` imports `_old.v1.lazy_disk_cache`. These reference the pre-refactor layout and will fail at collection/import against the current `src/pc2img/`. They should be rewritten against the current `image_cache/` API or removed. Until then, `pytest` over the whole `tests/` dir will error on collection — run targeted files (the three current-API modules) instead.
- **No tests for projection/interpolation strategies.** `SphericalProjection`, `OrthographicProjection`, and the scipy-backed interpolators (`Linear/Nearest/Cubic/Delaunay`) in `src/pc2img/strategies/` have no direct tests, including the `project()` normalization math and Delaunay triangle-quality masking in `interpolation.py`.
- **No tests for most derivative features.** `src/pc2img/features/derivative_features.py` (gradient, sobel, normalized, log, hillshade, average/sum/norm, clip, `MultiScaleGradientFeature`, `OcclusionAwareMultiScaleGradientFeature`) is largely untested despite complex name-grammar parsing and NaN-aware numerics.
- **No tests for `util.py`** (`convert_to_image`, `replace_nan`, `to_gray`, optical-flow visualization) — dtype/normalization/colormap branches are untested.
- **No tests for `tiled_generator.py`** (joblib-parallel tiled generation).
- **No tests for the registries themselves** (`StrategyRegistry` kwarg filtering/`key_of`, `FeatureRegistry.match` default-fallback and multiple-match `RuntimeError`).

---

*Testing analysis: 2026-07-08*
