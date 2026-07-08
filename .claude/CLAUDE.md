<!-- GSD:project-start source:PROJECT.md -->

## Project

**pc2img**

`pc2img` is a scientific Python library (ETH Zurich, GSEG group) that converts 3D
point clouds into 2D raster images: it projects points into image space
(spherical or orthographic), interpolates scattered values onto a pixel grid, and
computes named "features" (range, scalar fields, gradients, hillshade, RRIM,
multiscale gradient, …) as rasters, held in a lazy disk-backed cache. A tiled
orchestrator fans the same pipeline across many point-cloud tiles in parallel. It
depends on two sibling GSEG libraries — **PCHandler** (point-cloud data/geometry)
and **GSEGUtils** (lazy disk caching) — and is itself consumed by downstream
geospatial / deformation-analysis tooling.

**Core Value:** Reliably turn 3D point clouds into **correct, reproducible 2D feature rasters** —
the projection → interpolation → feature pipeline must be sound (in code and in
math) and must run against the current PCHandler 2.x + GSEGUtils releases.

### Constraints

- **Tech stack**: Python `~=3.12`, numpy 2.x, scipy, pydantic v2, joblib/loky — Established scientific stack; numpy 2.x forced by PCHandler 2.x
- **Dependencies**: PCHandler 2.x + GSEGUtils 0.5.x — Core input/persistence layers; on-disk sources match PyPI
- **Environment**: `uv`-managed venv; deps via `third_party/` symlinks (gitignored) — Offline/local dep resolution; install GSEGUtils before PCHandler
- **Dependency edits**: changes to PCHandler / GSEGUtils require human approval — They are separate GSD-managed repos
- **Branching**: work on `develop-gsd` + per-phase branches; `main` only at milestone ship, stripped of `.planning/` and agent-specific files — Keep the public branch clean of planning artifacts
- **Publication standard**: branch protection + CI/CD match the PCHandler template — Consistency across GSEG libraries
- **Commit messages**: conventional-commit scopes use traditional/functional scopes (e.g. `fix(projection):`, `test(features):`), never GSD planning-ID tags (no `(BUGS-05)`-style IDs in the parentheses) — Commits squash to `main` where `.planning/` is stripped, so planning-ID references in scopes would dangle

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python `~=3.12,<3.13` - Entire codebase. Source under `src/pc2img/`, scripts under `scripts/`, tests under `tests/`. Constrained to CPython 3.12 in `pyproject.toml` (`requires-python`) and `pyrightconfig.json` (`pythonVersion: "3.12"`).
- Not applicable - single-language project. No compiled extensions authored here; native code is pulled in transitively via wheels (numpy, scipy, opencv, shapely, etc.).

## Runtime

- CPython 3.12 only. Upper bound `<3.13` is a hard pin (`pyproject.toml`).
- Local dev interpreters observed: a virtualenv at `.venv/` (Python 3.12) and a conda env `pc2img-dev312` referenced by `pyrightconfig.json` (`venvPath: /scratch/miniconda3/envs`).
- pip (working install present in `.venv/lib/python3.12/site-packages/`).
- No lockfile (no `requirements.txt`, `poetry.lock`, `uv.lock`, or `Pipfile.lock`). Dependency versions are floated via `~=` compatible-release specifiers in `pyproject.toml` - Lockfile: missing.
- `setuptools` + `setuptools_scm` (`pyproject.toml` `[build-system]`).
- Version is dynamic, derived from git tags by `setuptools_scm` and written to `src/pc2img/_version.py`. `local_scheme = "no-local-version"`, `version_scheme = "post-release"`. Tags match `v[0-9]*.[0-9]*.[0-9]*`.
- Minimal `setup.py` shim (`setup.py`) delegates entirely to declarative config.

## Frameworks

- NumPy `~=2.0` (installed `2.3.5`) - Fundamental array type used throughout. `NDArray` typing is pervasive.
- SciPy `~=1.14` - Spatial and signal ops: `scipy.spatial.Delaunay` (`src/pc2img/strategies/triangulation.py`, `strategies/interpolation.py`), `scipy.interpolate.{LinearNDInterpolator, NearestNDInterpolator, CloughTocher2DInterpolator}` (`strategies/interpolation.py`), `scipy.signal.convolve2d` and `scipy.ndimage` (`src/pc2img/util.py`).
- Pydantic `~=2.11` (installed `2.13.4`) - Runtime validation/coercion of the public API via `@validate_call`, `ConfigDict`, `BeforeValidator` (`src/pc2img/core.py`); pydantic dataclasses used in strategies/features.
- pytest (declared under `[project.optional-dependencies].dev`; no pinned version). Config-less (no `pytest.ini`/`tox.ini`/`[tool.pytest]`). Tests live in `tests/`. `.pytest_cache/` present.
- `setuptools_scm` - versioning from git.
- black `~=23.10` - formatter (dev extra).
- memory_profiler - profiling (dev extra).
- sphinx `~=5.1` - docs (doc extra). Note: `release-please-config.json` lists `docs/conf.py` as an extra-file, but no `docs/` directory exists in the tree yet.
- Pyright (basic mode) - type checking, configured by `pyrightconfig.json` (`typeCheckingMode: "basic"`, `reportMissingImports: "error"`, include `src/pc2img`, `scripts`, `tests`).

## Key Dependencies

- `numpy ~= 2.0` - core arrays.
- `scipy ~= 1.14` - triangulation/interpolation/convolution.
- `pydantic ~= 2.11` - API validation.
- `joblib ~= 1.5` (and a redundant `joblib ~= 1.3` line - see CONCERNS) - process-based parallelism (`loky` backend) in `src/pc2img/tiled_generator.py`.
- `imageio ~= 2.31` - image read/write.
- `Pillow ~= 10.0` - image backend.
- `tifffile[all] ~= 2024.1` - TIFF I/O (multi-page/scientific).
- `opencv-python ~= 4.0` - image ops.
- `typing-extensions ~= 4.9` (installed `4.16.0`) - backport typing constructs.
- `pchandler` (installed `2.1.0.post2`) - supplies `PointCloudData`, `pchandler.filters` (`FoVFilter`, `BoxFilter`), `pchandler.geometry.spherical.FoV`, `pchandler.geometry.coordinates.rhv2xyz`, and `pchandler.data_io` loaders (`load_ply`, `load_e57`). Imported across `core.py`, `features/`, `strategies/projection.py`, `tiled_generator.py`.
- `GSEGUtils` (installed `0.5.2.post2`) - supplies the disk-cache layer: `GSEGUtils.lazy_disk_cache.{LazyDiskCache, LazyDiskCacheConfig, LazyDiskCacheKw, DiskBackedNDArray, DiskBackedStore}` and `GSEGUtils.config.{get_defaults, CacheDefaults}`. Used in `core.py`, `strategies/interpolation.py`, `image_cache/`, `features/manager.py`, `tiled_generator.py`.
- matplotlib - lazily imported inside `src/pc2img/util.py` `convert_to_image()` only when a colormap is requested; raises `RuntimeError("Colormap requires matplotlib")` if absent. Not listed in `pyproject.toml`.

## Configuration

- No environment variables are read anywhere in `src/pc2img/` (no `os.environ`/`getenv` usage). The library is configured purely through Python call arguments and Pydantic-validated config objects.
- Cache behavior is configured through `LazyDiskCacheConfig` (from GSEGUtils), accepted as a mapping or object and coerced in `src/pc2img/core.py` (`coerce_lazy_cfg`). Defaults come from `GSEGUtils.config.get_defaults` / `CacheDefaults`.
- Image resolution is a validated `ImgRes(width, height)` NamedTuple (`src/pc2img/core.py`).
- `[project.optional-dependencies]` defines `cuda12` and `cuda11` extras pinning RAPIDS `25.4.*` (`cudf`, `cuspatial`, `cuproj`, `cuml`, `dask-cudf`). These require `--extra-index-url=https://pypi.nvidia.com` (noted inline). GPU code paths are exercised through pchandler, not directly in pc2img source.
- `pyproject.toml` - single source of build/dependency/tool config.
- `pyrightconfig.json` - type-checker config.
- `.editorconfig` - `.rst` files use 3-space indent.
- `release-please-config.json` + `.release-please-manifest.json` (current release `0.10.4`) - release automation config.

## Platform Requirements

- Python 3.12 (exactly; `<3.13`).
- The two sibling libraries (`pchandler`, `GSEGUtils`) must be installed - locally provided via `third_party/` symlinks to adjacent checkouts (`/scratch/41_pchandler`, `/scratch/30_GSEGUtils`). See MEMORY: dependency-rework tracks keeping local copies aligned with PyPI releases.
- Optional: matplotlib (colormaps), CUDA 11/12 toolchain + RAPIDS 25.4 for GPU extras.
- No deployment target - distributed as an importable Python package (`pc2img`). No server, container, or service. Public entry point `pc2img.PointCloudImageGenerator` (`src/pc2img/__init__.py`).

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- `snake_case.py` for all modules: `disk_backed_image_data.py`, `tiled_generator.py`, `base_features.py`, `derivative_features.py`.
- Descriptive, domain-oriented names. Registry modules are consistently named `registry.py` inside each subpackage (`strategies/registry.py`, `features/registry.py`).
- Private/legacy scaffolding is prefixed with a leading underscore at the directory level: `_old/`, `_scrap/`, `_tests/`. Do not add new production code there.
- `PascalCase` for all classes: `PointCloudImageGenerator`, `DiskBackedImageData`, `FeatureManager`, `SphericalProjection`.
- Strategy implementations end with a role suffix matching their base: `*Projection` (`SphericalProjection`, `OrthographicProjection`), `*Interpolation` (`LinearInterpolation`, `DelaunayInterpolation`), `*Feature` (`RangeFeature`, `GradientFeature`, `MultiScaleGradientFeature`).
- Abstract bases end in `Strategy`: `ProjectionStrategy`, `InterpolationStrategy`, `BaseFeatureStrategy`, `DerivativeFeatureStrategy` (see `src/pc2img/strategies/projection.py`, `src/pc2img/features/core.py`).
- `snake_case`: `make_generator`, `get_base_features`, `project_raw`, `interpolate`, `convert_to_image`.
- Internal helpers are underscore-prefixed: `FeatureManager._get`, `FeatureManager._compute`, `DelaunayInterpolation._hash_settings`, `DerivativeFeatureStrategy._split_top_level`.
- Ignored/placeholder parameters use `_`: feature `compute(self, _, fetch)` uses `_` for the unused `pcd` argument (`src/pc2img/features/derivative_features.py`).
- `snake_case` for locals and attributes: `base_features_1D`, `grid_x`, `pts2d`, `cache_store`.
- Private instance state is single-underscore prefixed: `self._pcd`, `self._img_res`, `self._proj`, `self._raster_cache`, `self._triangulation_precalc`.
- Module-level constants are `UPPER_SNAKE_CASE`: `DEFAULT`, `FEATURES`, `PROJECTIONS`, `INTERPOLATIONS`, `DEFAULT_MAX_DISTANCE`, `NAN_REPLACEMENT_STR` (`src/pc2img/features/rrim.py`, `src/pc2img/util.py`).
- `PascalCase` for `TypeAlias`/`NamedTuple`: `ImgRes`, `ProjectionStrategyLike`, `InterpolationName`.
- String-enum-style unions expressed as `Literal[...]`: `ProjectionName = Literal["spherical", "orthographic"]`, `InterpolationName = Literal["linear", "nearest_neighbor", "cubic", "delaunay"]` (`src/pc2img/strategies/*.py`).
- Numpy typing via `numpy.typing.NDArray` / `DTypeLike`, with local shorthands where helpful: `FloatArray = NDArray[np.floating]`, `BoolArray = NDArray[np.bool_]` (`src/pc2img/strategies/utils.py`).

## Code Style

- `black` is the declared formatter (`black ~= 23.10` in the `dev` extra of `pyproject.toml`). No explicit `[tool.black]` config, so black defaults apply (88-char line length). Note: much of the current code exceeds 88 chars and is not yet black-clean, so treat black as the target, not the current state.
- Indentation: 4 spaces (PEP 8). `.editorconfig` only overrides `.rst` files (3-space indent) and does not constrain Python.
- No enforced import sorter (`isort`/`ruff` are absent). Imports are hand-grouped (see below).
- No runtime linter configured. Type checking is done with Pyright in `basic` mode via `pyrightconfig.json` (`pythonVersion: 3.12`, `reportMissingImports: error`, scope: `src/pc2img`, `scripts`, `tests`).
- Type hints are expected on public function signatures and are used heavily, including generics (`StrategyRegistry(Generic[T])`), `ParamSpec`, `Protocol`, `TypeGuard`, and PEP 695 syntax (`def register[S](...)` in `src/pc2img/strategies/registry.py`).
- Use `cast(...)` and `# type: ignore[...]` sparingly to satisfy Pyright at boundaries where runtime coercion diverges from the static type (pattern established in `src/pc2img/core.py` and `src/pc2img/util.py`).

## Import Organization

## Error Handling

- Raise specific built-in exceptions with an explanatory message. `TypeError` for bad coercion inputs (`coerce_img_res`, strategy `validate` methods), `ValueError` for invalid domain values (`convert_to_image` rejecting unknown `replace_nan_with`; feature constructors validating percentiles/sigmas), `KeyError` for missing registry entries, `RuntimeError` for programmer/config errors (duplicate registration, multiple regex matches).
- Chain exceptions with `raise ... from e` to preserve cause: `raise ValueError(f"Scalar field '{self.feature}' not found ...") from e` (`src/pc2img/features/base_features.py`), and similarly in `strategies/registry.py` and `derivative_features.py` token parsing.
- Validate constructor arguments eagerly and fail fast. Feature strategies validate parsed regex parameters in `__init__` (e.g. `ClipPercentileFeature` checks `0 <= low <= high <= 100`; `MultiScaleGradientFeature` rejects non-positive sigmas).
- Guard numeric edge cases explicitly rather than relying on exceptions: `span[span == 0] = 1` before division (`projection.py`), `np.divide(..., out=..., where=...)` and `np.errstate(invalid="ignore", divide="ignore")` blocks around NaN-aware math (`util.py`, `derivative_features.py`).
- `assert` is used for internal invariants that indicate programmer error, not user input (`assert image_data.ndim in (2, 3) ...` in `disk_backed_image_data.py`). Do not rely on asserts for validating external/API inputs.
- Runtime input coercion at API boundaries is done via Pydantic `@validate_call` plus `BeforeValidator` converters (`src/pc2img/core.py`): the constructor accepts loose types (`tuple`, `str`, `Mapping`) and coerces to canonical types, with the `TYPE_CHECKING` branch exposing the loose union to Pyright and the runtime branch using `Annotated[..., BeforeValidator(...)]`.

## Logging

- Module-level logger: `logger = logging.getLogger(__name__)` at the top of the module (`src/pc2img/strategies/interpolation.py`, `strategies/registry.py`, `image_cache/disk_backed_image_store.py`, `tiled_generator.py`).
- Use `logger.debug(...)` for pipeline progress and diagnostics (triangulation start, valid-point percentages, density-thinning reductions) and `logger.warning(...)` for recoverable misconfiguration (unexpected kwargs ignored in `StrategyRegistry.create`).
- Both f-strings and `%`-style lazy args appear; the `%`-style lazy form (`logger.debug("Density thinning reduced ... %d to %d", ...)` in `interpolation.py`) is preferred for hot-path debug logs to avoid formatting cost when the level is disabled.

## Comments

- Comment non-obvious numerical intent and algorithmic steps: e.g. `# avoid division by zero`, `# Hero's formula`, `# (n_query,) holds -1 for "outside"` in `interpolation.py`.
- Large blocks of commented-out code exist (old implementations retained inline in `interpolation.py`, `util.py`, `disk_backed_image_data.py`). This is a legacy habit of the refactor, not a target convention — prefer deleting dead code and relying on git history rather than adding new commented-out blocks.
- Triple-quoted docstrings on public classes and non-trivial functions. Two styles coexist: a terse one-line summary (`BaseFeatureStrategy` — "Produces a 1D array of length N (per point).") and NumPy-style `Parameters`/`Returns` sections (`DelaunayInterpolation`, `thin_points_by_pixel_density`, `replace_nan`).
- Feature strategies document their **name grammar** in the class docstring, since the feature name string is the public API (see `MultiScaleGradientFeature`, `OcclusionAwareMultiScaleGradientFeature`, `rrim.py`). New features MUST document their regex/name syntax and options this way.
- `# pragma: no cover` marks intentionally untested import stubs (see test helpers).

## Function & Class Design

- Behaviors are pluggable strategies registered into a module-level singleton registry via a decorator. Two registry flavors exist:
- To add a new strategy: subclass the relevant ABC, implement the abstract method(s), and decorate with the registry. Constructor kwargs become the strategy's configuration; the registry filters/validates them. Do not wire strategies together by hand outside the registry/factory.
- Use `abc.ABC` + `@abstractmethod` to define strategy contracts (`ProjectionStrategy.project_raw`, `InterpolationStrategy.interpolate`, `BaseFeatureStrategy.compute`).
- Pydantic interop for strategies is provided via classmethods `__get_validators__` / `validate` (v1-style validator protocol) so strategies can be passed as `str`, `(name, kwargs)` tuple, or instance to `PointCloudImageGenerator`.
- Keyword-only arguments (`*`) are used to force explicit call sites for configuration: `FeatureManager.__init__(self, pcd, *, lazy_disk_cache_config=...)`, `SphericalProjection(*, field_of_view=None)`, `thin_points_by_pixel_density(points2d, *, img_width, ...)`.
- Positional-only (`/`) is used where the first arg is unambiguous: `DelaunayInterpolation.__init__(self, /, lazy_disk_cache_config=None, *, ...)`.
- Mutable defaults are generally avoided via `None` + coercion, but note `FeatureManager` uses `lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig()` (a constructed default) — the safer `None`-sentinel pattern in `core.py`'s `coerce_lazy_cfg` is the preferred approach for new code.
- Multi-value returns use plain tuples with documented shapes/order (`project_raw -> (coords_raw, mask, mins, maxs)`), or `NamedTuple` when the shape is a stable public value (`ImgRes`, `PointCloudTile`).
- Numpy dtype discipline is explicit: results are cast with `.astype(np.float32, copy=False)` and fill/NaN handling is deliberate throughout `derivative_features.py` and `util.py`.

## Module Design

- Every package `__init__.py` declares `__all__` explicitly and re-exports the public surface (`src/pc2img/__init__.py`, `features/__init__.py`, `strategies/__init__.py`, `image_cache/__init__.py`).
- Top-level `pc2img` exposes `PointCloudImageGenerator`, `__version__`, and the subpackages themselves.
- Subpackage `__init__.py` files act as curated barrels — importing them also has the side effect of registering strategies/features (the decorators run at import time), which is how the registries get populated. Keep new strategy classes imported in the relevant `__init__.py` so registration happens.
- Version is derived from git tags via `setuptools_scm`, written to `src/pc2img/_version.py` (generated — do not edit). Releases are automated through `release-please` (`.github/workflows/release-please.yml`), and commit messages should follow Conventional Commits (`feat(...)`, `chore(...)`) to drive changelog generation.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `PointCloudImageGenerator` | Orchestrates project → interpolate → feature pipeline for one point cloud | `src/pc2img/core.py` |
| `TiledPointCloudImageGenerator` | Runs the generator over many tiles in parallel (joblib loky) | `src/pc2img/tiled_generator.py` |
| `make_generator` | Convenience factory building a generator from string keys | `src/pc2img/registry.py` |
| `ProjectionStrategy` (+ subclasses) | Map 3D points to normalized 2D pixel coords + validity mask | `src/pc2img/strategies/projection.py` |
| `InterpolationStrategy` (+ subclasses) | Rasterize scattered point values onto a grid | `src/pc2img/strategies/interpolation.py` |
| `StrategyRegistry` | Name→class registry for projection/interpolation strategies | `src/pc2img/strategies/registry.py` |
| `FeatureManager` | Resolve requested feature names, compute base + derivative rasters, memoize | `src/pc2img/features/manager.py` |
| `FeatureRegistry` / `FeatureSpec` | Regex-based feature-name DSL and dependency parsing | `src/pc2img/features/registry.py` |
| `BaseFeatureStrategy` / `DerivativeFeatureStrategy` | ABCs for per-point (1D) vs per-raster (2D) features | `src/pc2img/features/core.py` |
| `DiskBackedImageStore` | `MutableMapping[str, DiskBackedImageData]` with pickle offload | `src/pc2img/image_cache/disk_backed_image_store.py` |
| `DiskBackedImageData` | Single lazily-offloaded raster (NumPy-array-like) | `src/pc2img/image_cache/disk_backed_image_data.py` |

## Pattern Overview

- Two independent registry mechanisms: `StrategyRegistry` (generic, class-based,
- Features are addressed by *string names* parsed via regex into a
- Pervasive lazy disk-backing: rasters and triangulation intermediates offload
- Pydantic `@validate_call` + `BeforeValidator` coercers accept loose inputs

## Layers

- Purpose: Assemble strategies + feature manager and drive the generate() flow
- Location: `src/pc2img/core.py`, `src/pc2img/tiled_generator.py`, `src/pc2img/registry.py`
- Contains: `PointCloudImageGenerator`, `TiledPointCloudImageGenerator`, `make_generator`
- Depends on: strategies, features, image_cache, `pchandler`, `GSEGUtils`
- Used by: end-user scripts (`scripts/`), tests (`tests/`)
- Purpose: Pluggable projection and interpolation algorithms
- Location: `src/pc2img/strategies/`
- Contains: `projection.py`, `interpolation.py`, `triangulation.py`, `registry.py`, `utils.py`
- Depends on: `numpy`, `scipy`, `pchandler` filters/geometry, `GSEGUtils` cache
- Used by: orchestration layer, registered via `PROJECTIONS` / `INTERPOLATIONS`
- Purpose: Compute named per-point and per-raster features with dependency resolution
- Location: `src/pc2img/features/`
- Contains: `manager.py`, `registry.py`, `core.py` (ABCs), `base_features.py`, `derivative_features.py`, `rrim.py`
- Depends on: image_cache, `numpy`/`scipy`, `pchandler`
- Used by: `PointCloudImageGenerator.generate`
- Purpose: Store rasters with lazy disk offload / reload
- Location: `src/pc2img/image_cache/`
- Depends on: `GSEGUtils.lazy_disk_cache`, `pc2img.util.convert_to_image`
- Used by: `FeatureManager`, generators
- Purpose: Colormap/NaN-aware image conversion, density thinning
- Location: `src/pc2img/util.py`, `src/pc2img/strategies/utils.py`

## Data Flow

### Primary Request Path — `PointCloudImageGenerator.generate(features)`

### Tiled Flow — `TiledPointCloudImageGenerator.generate(features, n_jobs)`

### Feature-name DSL Flow

- Per-generator raster memoization in `DiskBackedImageStore`.
- Triangulation intermediates memoized by content hash in
- Global registry singletons `PROJECTIONS`, `INTERPOLATIONS`, `FEATURES`.

## Key Abstractions

- Purpose: Contract for interchangeable algorithms
- Examples: `src/pc2img/strategies/projection.py` (`ProjectionStrategy`), `src/pc2img/strategies/interpolation.py` (`InterpolationStrategy`)
- Pattern: ABC + `@REGISTRY.register("name")` decorator + Pydantic `validate` classmethod for coercion
- Purpose: Separate per-point (1D) computation from per-raster (2D) derivation
- Examples: `src/pc2img/features/base_features.py`, `src/pc2img/features/derivative_features.py`, `src/pc2img/features/rrim.py`
- Pattern: `regex_pattern` class attribute + `compute(pcd, fetch)` where `fetch` lazily resolves dependencies
- Purpose: NumPy-array-like objects that transparently offload to disk
- Examples: `src/pc2img/image_cache/disk_backed_image_data.py`
- Pattern: subclass `GSEGUtils.LazyDiskCache` + `NDArrayOperatorsMixin`, implement buffer hooks

## Entry Points

- Location: `src/pc2img/core.py`, re-exported from `src/pc2img/__init__.py`
- Triggers: user code / scripts
- Responsibilities: single-cloud image generation
- Location: `src/pc2img/tiled_generator.py`
- Triggers: user code needing parallel multi-tile processing
- Responsibilities: parallel orchestration, per-tile cache pathing

## Architectural Constraints

- **Threading:** A single `PointCloudImageGenerator` is single-threaded and
- **Global state:** Module-level singletons `PROJECTIONS` / `INTERPOLATIONS`
- **Import-time registration:** `features/__init__.py` and
- **Circular-import sensitivity:** `tiled_generator.py` imports
- **Cache directory:** When no `cache_path` is configured the store falls back

## Anti-Patterns

### Two divergent registry implementations

### Stale/broken `make_generator` factory

### `project()` / `project_raw()` return-arity mismatch

### Large commented-out code blocks

## Error Handling

- Coercion errors raise `TypeError`/`ValueError` from Pydantic validators and
- Registry misuse raises `KeyError` (unknown/duplicate strategy) or
- Numerical paths use NaN sentinels: outside-hull grid points and thinned
- Note: `DiskBackedImageData.__array_ufunc__` currently `raise NotImplemented`

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
