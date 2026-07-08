# Codebase Concerns

**Analysis Date:** 2026-07-08

## Tech Debt

**Core dependencies commented out of package metadata:**
- Issue: `pchandler` and `GSEGUtils` are imported across nearly every module but are commented out in the `dependencies` list. The package therefore declares an install profile that cannot import its own top-level modules.
- Files: `pyproject.toml` (lines 18-21), consumed by `src/pc2img/core.py`, `src/pc2img/features/manager.py`, `src/pc2img/features/core.py`, `src/pc2img/features/base_features.py`, `src/pc2img/strategies/projection.py`, `src/pc2img/strategies/interpolation.py`, `src/pc2img/image_cache/disk_backed_image_data.py`, `src/pc2img/image_cache/disk_backed_image_store.py`, `src/pc2img/tiled_generator.py`
- Impact: `pip install pc2img` produces an unimportable package. A fresh `.venv` in this repo cannot import `pc2img` (both deps and even `matplotlib` are absent). Dependency-resolution/versioning is mid-rework.
- Fix approach: Re-enable the `pchandler`/`GSEGUtils` requirement lines against the reworked upstream releases, pinning to the intended version ranges, before any release-please cut.

**Duplicate and conflicting `joblib` pin:**
- Issue: `joblib` is listed twice with different specifiers (`~= 1.5` and `~= 1.3`).
- Files: `pyproject.toml` (lines 22 and 25)
- Impact: Confusing/contradictory constraint; whichever the resolver honors is nondeterministic to a reader and the two ranges disagree on the floor.
- Fix approach: Collapse to a single `joblib` entry with the intended lower bound.

**Placeholder project metadata:**
- Issue: `keywords = ["one", "two"]`, `documentation = "https://google.com"`, and a near-empty `classifiers` list remain as scaffolding defaults.
- Files: `pyproject.toml` (lines 9, 46, 15-17)
- Impact: Ships meaningless metadata to PyPI; hurts discoverability and looks unfinished.
- Fix approach: Populate real keywords, docs URL, and trove classifiers (License, OS, Python versions, Topic :: Scientific/Engineering).

**Large volume of commented-out dead code:**
- Issue: Substantial blocks of superseded implementations are retained as comments rather than removed (git history already preserves them).
- Files: `src/pc2img/strategies/interpolation.py` (lines 122-130, 207-213, 233-234, 291-351), `src/pc2img/image_cache/disk_backed_image_data.py` (lines 60-99), `src/pc2img/image_cache/disk_backed_image_store.py` (lines 99-135), `src/pc2img/util.py` (lines 85-108), `src/pc2img/strategies/projection.py` (lines 73-74, 161-162), `src/pc2img/core.py` (line 16)
- Impact: Obscures the live code path, inflates files, and makes the intended behavior ambiguous (e.g. the commented `__array_ufunc__` body hints the current stub is unfinished).
- Fix approach: Delete dead blocks; rely on VCS for history.

**Duplicate function definitions in `util.py`:**
- Issue: `convert_to_image` is defined twice (lines 58 and 231) and `replace_nan` once as a comment plus once live. The first `convert_to_image` is shadowed dead code that references an unimported `plt` (line 76) and would `NameError` if ever reached.
- Files: `src/pc2img/util.py` (lines 58-83 vs 231-294)
- Impact: Reader confusion; a latent broken code path hiding behind name shadowing.
- Fix approach: Remove the first definition; keep the second (which lazily imports matplotlib).

## Known Bugs

**`OrthographicProjection.project_raw` returns the wrong arity and indexes incorrectly:**
- Symptoms: Calling `.project()` on an orthographic projection raises `ValueError: not enough values to unpack (expected 4, got 2)`.
- Files: `src/pc2img/strategies/projection.py` (lines 166-179 vs the base `project()` unpack at line 70)
- Trigger: `ProjectionStrategy.project()` unpacks `coords_raw, mask, mins, maxs`, but `OrthographicProjection.project_raw` returns only `(coords, mask)`. There is an in-source `# Todo: Update to pass min and max back!` on line 178 acknowledging this. Additionally `pcd.xyz[mask, self._xyz_column_selection]` mixes a boolean row mask with a fancy column list, which broadcasts to an error unless the mask happens to select exactly `len(columns)` rows.
- Workaround: Only `SphericalProjection` (the 4-tuple return) is currently usable; orthographic projection is non-functional.

**`DiskBackedImageData.__array_ufunc__` raises a non-exception:**
- Symptoms: Any numpy ufunc / arithmetic operator on a `DiskBackedImageData` raises `TypeError: exceptions must derive from BaseException` instead of a clean `NotImplementedError`.
- Files: `src/pc2img/image_cache/disk_backed_image_data.py` (line 74, `raise NotImplemented`)
- Trigger: The class mixes in `NDArrayOperatorsMixin` specifically to support `+ - * /` etc., but the ufunc hook is an unfinished stub that raises the `NotImplemented` singleton (a constant, not an exception). So the mixin's entire purpose is currently dead/broken.
- Workaround: Convert to a plain array via `np.asarray(img)` before doing arithmetic.

**`TIGSettings.extend_cache_paths` stores `None` for `interp_kwargs`:**
- Symptoms: When an interpolation `lazy_disk_cache_config` is present, the extended-path settings object silently drops all interp kwargs.
- Files: `src/pc2img/tiled_generator.py` (lines 60-63)
- Trigger: `updates["interp_kwargs"] = dict(self.interp_kwargs).update({...})` — `dict.update()` returns `None`, so the assignment is always `None`.
- Workaround: None in-code; the method must be rewritten to build the dict then assign it.

**Module docstring in `rrim.py` is inert:**
- Symptoms: `pc2img.features.rrim.__doc__` is `None`; the intended module documentation is a no-op string expression.
- Files: `src/pc2img/features/rrim.py` (lines 1-11)
- Trigger: `from __future__ import annotations` precedes the triple-quoted string, so the string is not the first statement and is not treated as the module docstring.
- Workaround: Move the docstring above the future import.

## Security Considerations

**Unpickling of arbitrary cache files:**
- Risk: `DiskBackedImageStore` scans its cache directory for `*.pkl` files at construction and `pickle.load`s any of them on access; `__setstate__` also loads pickles. Pickle deserialization executes arbitrary code.
- Files: `src/pc2img/image_cache/disk_backed_image_store.py` (lines 41-58, 192-199)
- Current mitigation: Cache dirs are normally process-local temp dirs (`tempfile.mkdtemp()`), limiting exposure.
- Recommendations: Document that cache directories must be trusted; if caches are ever shared or user-supplied, add provenance checks or move to a non-executable serialization format for the payload arrays.

**Pickle side effect during serialization:**
- Risk: `DiskBackedImageStore.__getstate__` writes image data to disk as a side effect of being pickled.
- Files: `src/pc2img/image_cache/disk_backed_image_store.py` (lines 186-190)
- Current mitigation: Intentional offloading design.
- Recommendations: Surprising for anything that pickles the object for reasons other than persistence (e.g. joblib/loky shipping it to a worker). Verify this interacts correctly with the `TiledPointCloudImageGenerator` loky workers, which pickle the whole generator graph.

## Performance Bottlenecks

**Full-array SHA-256 hashing per interpolate call:**
- Problem: `DelaunayInterpolation.interpolate` hashes `points2d`, `grid_x`, and `grid_y` via `.tobytes()` + SHA-256 on every call to key the triangulation cache.
- Files: `src/pc2img/strategies/interpolation.py` (lines 133-139, 176)
- Cause: `tobytes()` materializes and hashes the entire coordinate/grid arrays (grids are H×W); for large tiles this is a real per-feature overhead.
- Improvement path: Cache the grid hash on the strategy (grids are constant per generator), or key on shape+extent metadata rather than full-array bytes.

**float16 convolution in `nanconv`:**
- Problem: `nanconv` casts convolution results to `np.float16` and divides in float16.
- Files: `src/pc2img/util.py` (lines 40-43)
- Cause: float16 both loses precision and is slower/emulated on most CPUs than float32.
- Improvement path: Use float32; reserve reduced precision for an explicit opt-in.

**Delaunay triangle-quality heuristics use magic thresholds:**
- Problem: Triangle culling uses hardcoded `area_thresh = median(area)*10` and MAD-based aspect thresholds with `max_edge_thresh` hardwired to `None`.
- Files: `src/pc2img/strategies/interpolation.py` (lines 233-248)
- Cause: Tuning constants baked into the hot path rather than exposed as strategy parameters.
- Improvement path: Promote thresholds to constructor arguments so tiles with unusual density can be tuned without editing source.

## Fragile Areas

**Regex-driven feature-name DSL:**
- Files: `src/pc2img/features/registry.py` (lines 44-64), `src/pc2img/features/derivative_features.py` (many `regex_pattern` definitions), `src/pc2img/features/rrim.py` (lines 37-42, 460-519)
- Why fragile: Features are addressed by string names parsed with overlapping regexes (`normalized_...`, `clip_..._lo_hi`, `multigrad_...`, `rrim_...`). `FeatureRegistry.match` raises `RuntimeError("Multiple patterns match")` when two patterns overlap and silently falls back to the default base-feature class when none match. New feature patterns can accidentally shadow or collide with existing ones, and lazy/greedy quantifiers (e.g. `NormalizedFeature` optional low/high groups) make boundaries subtle.
- Safe modification: When adding a feature, add a unit test asserting `FEATURES.match(name)` resolves to the intended class for representative names and that neighboring feature names still resolve correctly.
- Test coverage: Only RRIM names are covered (`tests/test_rrim_features.py`); the rest of the DSL is untested.

**No cycle detection in feature dependency resolution:**
- Files: `src/pc2img/features/manager.py` (lines 39-51, `visit`), `src/pc2img/features/manager.py` (lines 71-83, `_get`/`_compute`)
- Why fragile: Dependency graph traversal recurses through `spec.dependencies` with no visited-set guard. A feature whose name resolves (directly or transitively) to a dependency on itself causes unbounded recursion / `RecursionError`.
- Safe modification: Add a visiting/visited set to `visit` and `_get`; raise a clear error on cycles.
- Test coverage: None.

**In-place mutation of fetched rasters:**
- Files: `src/pc2img/features/derivative_features.py` (`NormalizedFeature.compute`, lines 78-85 — `np.divide(..., out=img)`, `np.clip(..., out=img)`)
- Why fragile: Writes in place into the array returned by `fetch`. This is currently safe only because `DiskBackedImageData.__array__` returns a copy; if `fetch` ever returns a view/live buffer, cached data would be corrupted for other consumers.
- Safe modification: Copy before in-place ops (as `ClipPercentileFeature.compute` already does at line 264) or drop the `out=` reuse.
- Test coverage: None for derivative features.

**Typed-as-non-optional attributes assigned `None`:**
- Files: `src/pc2img/features/registry.py` (line 27, `_default_cls: Type[...] = None`)
- Why fragile: Annotation claims a non-optional type but holds `None`; static checkers (pyright is configured, see `pyrightconfig.json`) will flag or be suppressed, and downstream code must remember the `None` case.
- Safe modification: Annotate as `Optional[...]`.

## Scaling Limits

**Whole triangulation held per unique grid/points hash:**
- Current capacity: `DelaunayInterpolation._triangulation_precalc` accumulates a `DiskBackedStore` per distinct input hash for the lifetime of the strategy instance.
- Limit: A long-running generator that sees many distinct point sets (e.g. many tiles reusing one strategy instance) grows this dict unbounded in memory metadata.
- Scaling path: Add eviction / max-size, or scope the cache to a single tile. Density thinning (`thin_points_by_pixel_density`) exists to bound Delaunay input size and should be enabled for dense tiles.

**Tiled generation ships full generator state to loky workers:**
- Current capacity: `TiledPointCloudImageGenerator.generate` uses `joblib.Parallel(backend="loky", prefer="processes")` and pickles each task (including the store, whose `__getstate__` offloads to disk).
- Files: `src/pc2img/tiled_generator.py` (lines 120-168)
- Limit: Per-tile pickling cost plus the disk-offload side effect on every serialization; memory scales with tile point counts held simultaneously across `n_jobs` processes.
- Scaling path: Confirm workers reload from the shared cache dir rather than re-serializing large arrays; consider chunking tiles.

## Dependencies at Risk

**Undeclared matplotlib dependency:**
- Risk: `convert_to_image(..., colormap=...)` imports `matplotlib.pyplot` but matplotlib is not declared in `dependencies` or any optional-extra.
- Files: `src/pc2img/util.py` (lines 278-288); `pyproject.toml` (no matplotlib entry); not present in the local `.venv`.
- Impact: Any colormap path raises `RuntimeError("Colormap requires matplotlib")` on a default install; the shadowed first `convert_to_image` (line 76) would `NameError` outright.
- Migration plan: Add `matplotlib` to an optional extra (e.g. `viz`) and guard/document the colormap feature accordingly.

**Local symlinked dependency sources:**
- Risk: `third_party/pchandler` and `third_party/gsegutils` are symlinks to sibling checkouts (`/scratch/41_pchandler`, `/scratch/30_GSEGUtils`).
- Files: `third_party/` (gitignored), Memory note "Dependency rework".
- Impact: Builds/tests depend on machine-local paths; another contributor without those checkouts cannot resolve the deps until the pyproject requirements are re-enabled against published releases.
- Migration plan: Pin to the reworked GSEGUtils/PCHandler releases in `pyproject.toml` once they are published.

## Missing Critical Features

**No pytest configuration scoping test discovery:**
- Problem: There is no `[tool.pytest.ini_options]` (no `testpaths`, no `conftest`, no `pytest.ini`). Running `pytest` walks into the gitignored `third_party/` symlinks and fails collection.
- Blocks: `python -m pytest` from the repo root reports 39 collection errors (from `third_party/pchandler/tests/...`) despite 42 project tests collecting; CI/local runs need a manual path argument to be usable.
- Fix approach: Add `[tool.pytest.ini_options] testpaths = ["tests"]` (and optionally `norecursedirs`) to `pyproject.toml`.

## Test Coverage Gaps

**Projection and interpolation math untested:**
- What's not tested: `SphericalProjection`/`OrthographicProjection` geometry and the Delaunay barycentric interpolation (the orthographic arity bug above would have been caught by a single test).
- Files: `src/pc2img/strategies/projection.py`, `src/pc2img/strategies/interpolation.py`
- Risk: Silent geometric errors and the known-broken orthographic path ship undetected.
- Priority: High.

**Derivative feature library untested:**
- What's not tested: The 650-line `derivative_features.py` (gradient, sobel, normalized, clip, hillshade, average/sum/norm, multigrad, occlusion-aware multigrad) has no unit tests.
- Files: `src/pc2img/features/derivative_features.py`
- Risk: Regex parsing, option handling, and NaN-aware smoothing math can regress unnoticed; only RRIM features are covered.
- Priority: High.

**Orchestration layers untested:**
- What's not tested: `FeatureManager` dependency resolution/caching and `TiledPointCloudImageGenerator` parallel tiling (including the `extend_cache_paths` `None` bug above).
- Files: `src/pc2img/features/manager.py`, `src/pc2img/tiled_generator.py`
- Risk: Cache-key extension, cycle handling, and multi-process aggregation errors surface only at runtime.
- Priority: Medium.

**Image conversion utilities untested:**
- What's not tested: `convert_to_image`, `replace_nan`, `to_gray`, `nanconv` in `util.py`.
- Files: `src/pc2img/util.py`
- Risk: NaN handling, normalization, and colormap branches (including the undeclared-matplotlib path) are unverified.
- Priority: Medium.

---

*Concerns audit: 2026-07-08*
