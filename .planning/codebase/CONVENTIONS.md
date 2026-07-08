# Coding Conventions

**Analysis Date:** 2026-07-08

This is a Python 3.12 scientific library (`pc2img`) that converts point clouds to raster images. Conventions below are derived from the source under `src/pc2img/`. The codebase is mid-refactor (a `dev/v2` line): production code lives in `src/pc2img/`, while `_old/`, `_scrap/`, and `build/` hold superseded material and should not be treated as normative.

## Naming Patterns

**Files:**
- `snake_case.py` for all modules: `disk_backed_image_data.py`, `tiled_generator.py`, `base_features.py`, `derivative_features.py`.
- Descriptive, domain-oriented names. Registry modules are consistently named `registry.py` inside each subpackage (`strategies/registry.py`, `features/registry.py`).
- Private/legacy scaffolding is prefixed with a leading underscore at the directory level: `_old/`, `_scrap/`, `_tests/`. Do not add new production code there.

**Classes:**
- `PascalCase` for all classes: `PointCloudImageGenerator`, `DiskBackedImageData`, `FeatureManager`, `SphericalProjection`.
- Strategy implementations end with a role suffix matching their base: `*Projection` (`SphericalProjection`, `OrthographicProjection`), `*Interpolation` (`LinearInterpolation`, `DelaunayInterpolation`), `*Feature` (`RangeFeature`, `GradientFeature`, `MultiScaleGradientFeature`).
- Abstract bases end in `Strategy`: `ProjectionStrategy`, `InterpolationStrategy`, `BaseFeatureStrategy`, `DerivativeFeatureStrategy` (see `src/pc2img/strategies/projection.py`, `src/pc2img/features/core.py`).

**Functions / methods:**
- `snake_case`: `make_generator`, `get_base_features`, `project_raw`, `interpolate`, `convert_to_image`.
- Internal helpers are underscore-prefixed: `FeatureManager._get`, `FeatureManager._compute`, `DelaunayInterpolation._hash_settings`, `DerivativeFeatureStrategy._split_top_level`.
- Ignored/placeholder parameters use `_`: feature `compute(self, _, fetch)` uses `_` for the unused `pcd` argument (`src/pc2img/features/derivative_features.py`).

**Variables:**
- `snake_case` for locals and attributes: `base_features_1D`, `grid_x`, `pts2d`, `cache_store`.
- Private instance state is single-underscore prefixed: `self._pcd`, `self._img_res`, `self._proj`, `self._raster_cache`, `self._triangulation_precalc`.
- Module-level constants are `UPPER_SNAKE_CASE`: `DEFAULT`, `FEATURES`, `PROJECTIONS`, `INTERPOLATIONS`, `DEFAULT_MAX_DISTANCE`, `NAN_REPLACEMENT_STR` (`src/pc2img/features/rrim.py`, `src/pc2img/util.py`).

**Types / aliases:**
- `PascalCase` for `TypeAlias`/`NamedTuple`: `ImgRes`, `ProjectionStrategyLike`, `InterpolationName`.
- String-enum-style unions expressed as `Literal[...]`: `ProjectionName = Literal["spherical", "orthographic"]`, `InterpolationName = Literal["linear", "nearest_neighbor", "cubic", "delaunay"]` (`src/pc2img/strategies/*.py`).
- Numpy typing via `numpy.typing.NDArray` / `DTypeLike`, with local shorthands where helpful: `FloatArray = NDArray[np.floating]`, `BoolArray = NDArray[np.bool_]` (`src/pc2img/strategies/utils.py`).

## Code Style

**Formatting:**
- `black` is the declared formatter (`black ~= 23.10` in the `dev` extra of `pyproject.toml`). No explicit `[tool.black]` config, so black defaults apply (88-char line length). Note: much of the current code exceeds 88 chars and is not yet black-clean, so treat black as the target, not the current state.
- Indentation: 4 spaces (PEP 8). `.editorconfig` only overrides `.rst` files (3-space indent) and does not constrain Python.
- No enforced import sorter (`isort`/`ruff` are absent). Imports are hand-grouped (see below).

**Linting / type checking:**
- No runtime linter configured. Type checking is done with Pyright in `basic` mode via `pyrightconfig.json` (`pythonVersion: 3.12`, `reportMissingImports: error`, scope: `src/pc2img`, `scripts`, `tests`).
- Type hints are expected on public function signatures and are used heavily, including generics (`StrategyRegistry(Generic[T])`), `ParamSpec`, `Protocol`, `TypeGuard`, and PEP 695 syntax (`def register[S](...)` in `src/pc2img/strategies/registry.py`).
- Use `cast(...)` and `# type: ignore[...]` sparingly to satisfy Pyright at boundaries where runtime coercion diverges from the static type (pattern established in `src/pc2img/core.py` and `src/pc2img/util.py`).

## Import Organization

Imports are grouped by origin, separated by blank lines, in this order:

1. Standard library: `from pathlib import Path`, `import re`, `import logging`, `from typing import ...`.
2. Third-party scientific stack: `import numpy as np`, `from numpy.typing import NDArray`, `from scipy.interpolate import ...`, `from pydantic import ...`.
3. First-party sibling projects (external deps developed in-house): `from GSEGUtils.lazy_disk_cache import ...`, `from pchandler import PointCloudData`.
4. Intra-package imports, absolute for cross-subpackage (`from pc2img.strategies.projection import ProjectionStrategy`) and relative for same-subpackage (`from .core import BaseFeatureStrategy`, `from .registry import FEATURES`).

**Path aliases:** None. `numpy` is aliased `np` universally; no other aliases.

**`__future__`:** `from __future__ import annotations` is used in newer/rewritten modules (`src/pc2img/strategies/registry.py`, `src/pc2img/features/rrim.py`, `src/pc2img/image_cache/disk_backed_image_data.py`) but is not universal. Prefer adding it to new modules for cheaper forward references.

## Error Handling

- Raise specific built-in exceptions with an explanatory message. `TypeError` for bad coercion inputs (`coerce_img_res`, strategy `validate` methods), `ValueError` for invalid domain values (`convert_to_image` rejecting unknown `replace_nan_with`; feature constructors validating percentiles/sigmas), `KeyError` for missing registry entries, `RuntimeError` for programmer/config errors (duplicate registration, multiple regex matches).
- Chain exceptions with `raise ... from e` to preserve cause: `raise ValueError(f"Scalar field '{self.feature}' not found ...") from e` (`src/pc2img/features/base_features.py`), and similarly in `strategies/registry.py` and `derivative_features.py` token parsing.
- Validate constructor arguments eagerly and fail fast. Feature strategies validate parsed regex parameters in `__init__` (e.g. `ClipPercentileFeature` checks `0 <= low <= high <= 100`; `MultiScaleGradientFeature` rejects non-positive sigmas).
- Guard numeric edge cases explicitly rather than relying on exceptions: `span[span == 0] = 1` before division (`projection.py`), `np.divide(..., out=..., where=...)` and `np.errstate(invalid="ignore", divide="ignore")` blocks around NaN-aware math (`util.py`, `derivative_features.py`).
- `assert` is used for internal invariants that indicate programmer error, not user input (`assert image_data.ndim in (2, 3) ...` in `disk_backed_image_data.py`). Do not rely on asserts for validating external/API inputs.
- Runtime input coercion at API boundaries is done via Pydantic `@validate_call` plus `BeforeValidator` converters (`src/pc2img/core.py`): the constructor accepts loose types (`tuple`, `str`, `Mapping`) and coerces to canonical types, with the `TYPE_CHECKING` branch exposing the loose union to Pyright and the runtime branch using `Annotated[..., BeforeValidator(...)]`.

## Logging

**Framework:** stdlib `logging`. No print-based logging in library code.

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)` at the top of the module (`src/pc2img/strategies/interpolation.py`, `strategies/registry.py`, `image_cache/disk_backed_image_store.py`, `tiled_generator.py`).
- Use `logger.debug(...)` for pipeline progress and diagnostics (triangulation start, valid-point percentages, density-thinning reductions) and `logger.warning(...)` for recoverable misconfiguration (unexpected kwargs ignored in `StrategyRegistry.create`).
- Both f-strings and `%`-style lazy args appear; the `%`-style lazy form (`logger.debug("Density thinning reduced ... %d to %d", ...)` in `interpolation.py`) is preferred for hot-path debug logs to avoid formatting cost when the level is disabled.

## Comments

**When to comment:**
- Comment non-obvious numerical intent and algorithmic steps: e.g. `# avoid division by zero`, `# Hero's formula`, `# (n_query,) holds -1 for "outside"` in `interpolation.py`.
- Large blocks of commented-out code exist (old implementations retained inline in `interpolation.py`, `util.py`, `disk_backed_image_data.py`). This is a legacy habit of the refactor, not a target convention — prefer deleting dead code and relying on git history rather than adding new commented-out blocks.

**Docstrings:**
- Triple-quoted docstrings on public classes and non-trivial functions. Two styles coexist: a terse one-line summary (`BaseFeatureStrategy` — "Produces a 1D array of length N (per point).") and NumPy-style `Parameters`/`Returns` sections (`DelaunayInterpolation`, `thin_points_by_pixel_density`, `replace_nan`).
- Feature strategies document their **name grammar** in the class docstring, since the feature name string is the public API (see `MultiScaleGradientFeature`, `OcclusionAwareMultiScaleGradientFeature`, `rrim.py`). New features MUST document their regex/name syntax and options this way.
- `# pragma: no cover` marks intentionally untested import stubs (see test helpers).

## Function & Class Design

**Strategy + registry pattern (the core architectural convention):**
- Behaviors are pluggable strategies registered into a module-level singleton registry via a decorator. Two registry flavors exist:
  - String-keyed `StrategyRegistry` for projections/interpolations: `@PROJECTIONS.register("spherical")`, `@INTERPOLATIONS.register("linear")` (`src/pc2img/strategies/registry.py`).
  - Regex-pattern `FeatureRegistry` for features, where the feature name string is parsed to select a class and extract params: `@FEATURES.register` / `@FEATURES.register(default=True)`, with each class defining a `regex_pattern` class attribute (`src/pc2img/features/registry.py`).
- To add a new strategy: subclass the relevant ABC, implement the abstract method(s), and decorate with the registry. Constructor kwargs become the strategy's configuration; the registry filters/validates them. Do not wire strategies together by hand outside the registry/factory.

**Abstract base classes:**
- Use `abc.ABC` + `@abstractmethod` to define strategy contracts (`ProjectionStrategy.project_raw`, `InterpolationStrategy.interpolate`, `BaseFeatureStrategy.compute`).
- Pydantic interop for strategies is provided via classmethods `__get_validators__` / `validate` (v1-style validator protocol) so strategies can be passed as `str`, `(name, kwargs)` tuple, or instance to `PointCloudImageGenerator`.

**Parameters:**
- Keyword-only arguments (`*`) are used to force explicit call sites for configuration: `FeatureManager.__init__(self, pcd, *, lazy_disk_cache_config=...)`, `SphericalProjection(*, field_of_view=None)`, `thin_points_by_pixel_density(points2d, *, img_width, ...)`.
- Positional-only (`/`) is used where the first arg is unambiguous: `DelaunayInterpolation.__init__(self, /, lazy_disk_cache_config=None, *, ...)`.
- Mutable defaults are generally avoided via `None` + coercion, but note `FeatureManager` uses `lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig()` (a constructed default) — the safer `None`-sentinel pattern in `core.py`'s `coerce_lazy_cfg` is the preferred approach for new code.

**Return values:**
- Multi-value returns use plain tuples with documented shapes/order (`project_raw -> (coords_raw, mask, mins, maxs)`), or `NamedTuple` when the shape is a stable public value (`ImgRes`, `PointCloudTile`).
- Numpy dtype discipline is explicit: results are cast with `.astype(np.float32, copy=False)` and fill/NaN handling is deliberate throughout `derivative_features.py` and `util.py`.

## Module Design

**Exports:**
- Every package `__init__.py` declares `__all__` explicitly and re-exports the public surface (`src/pc2img/__init__.py`, `features/__init__.py`, `strategies/__init__.py`, `image_cache/__init__.py`).
- Top-level `pc2img` exposes `PointCloudImageGenerator`, `__version__`, and the subpackages themselves.

**Barrel files:**
- Subpackage `__init__.py` files act as curated barrels — importing them also has the side effect of registering strategies/features (the decorators run at import time), which is how the registries get populated. Keep new strategy classes imported in the relevant `__init__.py` so registration happens.

**Versioning:**
- Version is derived from git tags via `setuptools_scm`, written to `src/pc2img/_version.py` (generated — do not edit). Releases are automated through `release-please` (`.github/workflows/release-please.yml`), and commit messages should follow Conventional Commits (`feat(...)`, `chore(...)`) to drive changelog generation.

---

*Convention analysis: 2026-07-08*
