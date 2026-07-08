<!-- refreshed: 2026-07-08 -->
# Architecture

**Analysis Date:** 2026-07-08

## System Overview

`pc2img` converts 3D point clouds into 2D raster images. A point cloud is
projected into image space (spherical or orthographic), scattered point values
are interpolated onto a pixel grid, and named "features" (range, scalar fields,
gradients, hillshade, RRIM, etc.) are computed as rasters. Results are held in a
lazy disk-backed image cache. A tiled orchestrator fans the same pipeline across
many point-cloud tiles in parallel.

```text
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                       │
├──────────────────────────────┬──────────────────────────────┤
│  PointCloudImageGenerator     │  TiledPointCloudImageGenerator│
│  `src/pc2img/core.py`         │  `src/pc2img/tiled_generator.py`
│  (single point cloud)         │  (parallel tiles, joblib/loky)│
└───────────────┬──────────────┴───────────────┬──────────────┘
                │                               │
        ┌───────┴────────┐              ┌───────┴────────┐
        ▼                ▼              ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────────────────┐
│ Projection      │ │ Interpolation│ │ Feature subsystem        │
│ strategies      │ │ strategies   │ │ `src/pc2img/features/`   │
│ `strategies/    │ │ `strategies/ │ │ FeatureManager +         │
│  projection.py` │ │ interpolation│ │ FeatureRegistry (regex   │
│ pcd → pts2d,mask│ │ .py` pts→grid│ │ DSL, dependency graph)   │
└────────┬────────┘ └──────┬───────┘ └────────────┬─────────────┘
         │                 │                       │
         └─────────────────┴───────────┬───────────┘
                                        ▼
                    ┌─────────────────────────────────────┐
                    │ Image cache (lazy, disk-backed)      │
                    │ `src/pc2img/image_cache/`            │
                    │ DiskBackedImageStore / …ImageData    │
                    └──────────────────┬──────────────────┘
                                       ▼
                    ┌─────────────────────────────────────┐
                    │ External deps                        │
                    │ pchandler.PointCloudData (input)     │
                    │ GSEGUtils.LazyDiskCache (persistence)│
                    └─────────────────────────────────────┘
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

**Overall:** Strategy + Registry + a small dependency-resolving pipeline.

**Key Characteristics:**
- Two independent registry mechanisms: `StrategyRegistry` (generic, class-based,
  kwarg-filtering) for projection/interpolation, and `FeatureRegistry`
  (regex-pattern based) for features. They are not shared.
- Features are addressed by *string names* parsed via regex into a
  `FeatureSpec` (e.g. `gradient_x_range`, `normalized_range_2_98`,
  `rrim_(r16,d8)`). Names encode both the operation and its parameters.
- Pervasive lazy disk-backing: rasters and triangulation intermediates offload
  to pickled `.pkl` files under a cache directory to bound memory.
- Pydantic `@validate_call` + `BeforeValidator` coercers accept loose inputs
  (strings, tuples, mappings) while presenting strict types to type-checkers.

## Layers

**Orchestration:**
- Purpose: Assemble strategies + feature manager and drive the generate() flow
- Location: `src/pc2img/core.py`, `src/pc2img/tiled_generator.py`, `src/pc2img/registry.py`
- Contains: `PointCloudImageGenerator`, `TiledPointCloudImageGenerator`, `make_generator`
- Depends on: strategies, features, image_cache, `pchandler`, `GSEGUtils`
- Used by: end-user scripts (`scripts/`), tests (`tests/`)

**Strategies:**
- Purpose: Pluggable projection and interpolation algorithms
- Location: `src/pc2img/strategies/`
- Contains: `projection.py`, `interpolation.py`, `triangulation.py`, `registry.py`, `utils.py`
- Depends on: `numpy`, `scipy`, `pchandler` filters/geometry, `GSEGUtils` cache
- Used by: orchestration layer, registered via `PROJECTIONS` / `INTERPOLATIONS`

**Features:**
- Purpose: Compute named per-point and per-raster features with dependency resolution
- Location: `src/pc2img/features/`
- Contains: `manager.py`, `registry.py`, `core.py` (ABCs), `base_features.py`, `derivative_features.py`, `rrim.py`
- Depends on: image_cache, `numpy`/`scipy`, `pchandler`
- Used by: `PointCloudImageGenerator.generate`

**Image cache:**
- Purpose: Store rasters with lazy disk offload / reload
- Location: `src/pc2img/image_cache/`
- Depends on: `GSEGUtils.lazy_disk_cache`, `pc2img.util.convert_to_image`
- Used by: `FeatureManager`, generators

**Utilities:**
- Purpose: Colormap/NaN-aware image conversion, density thinning
- Location: `src/pc2img/util.py`, `src/pc2img/strategies/utils.py`

## Data Flow

### Primary Request Path — `PointCloudImageGenerator.generate(features)`

1. Caller constructs generator with `pcd`, `img_res`, `proj`, `interp`; coercers
   turn strings/tuples into strategy instances (`src/pc2img/core.py:64`).
2. `feature_mgr.request(features)` walks each requested name, matches it to a
   `FeatureSpec`, and collects the transitive base features + targets
   (`src/pc2img/features/manager.py:32`).
3. `get_base_features()` computes per-point (1D) arrays such as `range` or
   `scalar_field_*` directly off the point cloud (`.../manager.py:56`).
4. `self._proj.project(pcd, resolution)` returns `pts2d` pixel coords + `mask`,
   computed once and memoized in `self.projection_results` (`.../core.py:96`).
5. Each base feature is interpolated onto the pixel grid via
   `self._interp.interpolate(...)` and submitted to the raster cache
   (`.../core.py:106`).
6. `feature_mgr.get_targets()` resolves derivative features recursively through
   `_get` → `_compute`, memoizing each raster in the store (`.../manager.py:71`).
7. Returns `dict[str, DiskBackedImageData]` keyed by feature name.

### Tiled Flow — `TiledPointCloudImageGenerator.generate(features, n_jobs)`

1. `pcd_tiles` (list of `PointCloudTile`) are dispatched with
   `joblib.Parallel` under a loky process backend (`src/pc2img/tiled_generator.py:120`).
2. Each worker calls `_process_tile`, which builds a per-tile
   `PointCloudImageGenerator` with a tile-scoped cache path and runs `generate`
   (`.../tiled_generator.py:145`).
3. Results are re-keyed by `ImageKey(tile_id, feature)` and merged.

### Feature-name DSL Flow

1. `FeatureRegistry.match(name)` finds the single regex pattern whose
   `fullmatch` accepts the name; if none match it falls back to the registered
   default (`ScalarFieldFeature`) (`src/pc2img/features/registry.py:44`).
2. Named capture groups become `FeatureSpec.params`, passed as constructor
   kwargs; the strategy instance declares its `dependencies` list.

**State Management:**
- Per-generator raster memoization in `DiskBackedImageStore`.
- Triangulation intermediates memoized by content hash in
  `DelaunayInterpolation._triangulation_precalc` (`.../interpolation.py:176`).
- Global registry singletons `PROJECTIONS`, `INTERPOLATIONS`, `FEATURES`.

## Key Abstractions

**Strategy ABCs:**
- Purpose: Contract for interchangeable algorithms
- Examples: `src/pc2img/strategies/projection.py` (`ProjectionStrategy`), `src/pc2img/strategies/interpolation.py` (`InterpolationStrategy`)
- Pattern: ABC + `@REGISTRY.register("name")` decorator + Pydantic `validate` classmethod for coercion

**Feature strategies:**
- Purpose: Separate per-point (1D) computation from per-raster (2D) derivation
- Examples: `src/pc2img/features/base_features.py`, `src/pc2img/features/derivative_features.py`, `src/pc2img/features/rrim.py`
- Pattern: `regex_pattern` class attribute + `compute(pcd, fetch)` where `fetch` lazily resolves dependencies

**DiskBacked arrays:**
- Purpose: NumPy-array-like objects that transparently offload to disk
- Examples: `src/pc2img/image_cache/disk_backed_image_data.py`
- Pattern: subclass `GSEGUtils.LazyDiskCache` + `NDArrayOperatorsMixin`, implement buffer hooks

## Entry Points

**`PointCloudImageGenerator` (public API):**
- Location: `src/pc2img/core.py`, re-exported from `src/pc2img/__init__.py`
- Triggers: user code / scripts
- Responsibilities: single-cloud image generation

**`TiledPointCloudImageGenerator`:**
- Location: `src/pc2img/tiled_generator.py`
- Triggers: user code needing parallel multi-tile processing
- Responsibilities: parallel orchestration, per-tile cache pathing

**Example usage:** `scripts/v2.0/04_img_gen.py`, `scripts/v2.0/03_tiled_image_gen.py`

## Architectural Constraints

- **Threading:** A single `PointCloudImageGenerator` is single-threaded and
  CPU-bound (SciPy interpolation). Parallelism is process-level via joblib's
  `loky` backend in `TiledPointCloudImageGenerator` (`tiled_generator.py:128`);
  objects crossing the process boundary must pickle cleanly, which is why the
  cache implements `__getstate__`/`__setstate__` offload.
- **Global state:** Module-level singletons `PROJECTIONS` / `INTERPOLATIONS`
  (`strategies/registry.py:86`) and `FEATURES` (`features/registry.py:67`).
  Registration happens at import time via decorators, so importing a feature
  module has the side effect of populating the registry.
- **Import-time registration:** `features/__init__.py` and
  `strategies/__init__.py` must import every strategy module for its
  `@register` decorator to run; a feature that is never imported is invisible to
  `FeatureRegistry.match`.
- **Circular-import sensitivity:** `tiled_generator.py` imports
  `from pc2img import PointCloudImageGenerator` (package root) rather than
  `from pc2img.core`, and `registry.py` imports from `core`. Keep `__init__.py`
  import order intact (`_version` → `core` → subpackages).
- **Cache directory:** When no `cache_path` is configured the store falls back
  to `tempfile.mkdtemp()` (`disk_backed_image_store.py:31`); output persistence
  is not guaranteed unless a path is supplied.

## Anti-Patterns

### Two divergent registry implementations

**What happens:** Projection/interpolation use `StrategyRegistry`
(`strategies/registry.py`), while features use a separate regex-based
`FeatureRegistry` (`features/registry.py`). They share no base class and behave
differently (kwarg filtering vs regex capture groups).
**Why it's wrong:** Duplicated concepts increase cognitive load and mean fixes
(e.g. reverse-lookup, error messages) must be applied twice.
**Do this instead:** When touching registry behavior, change only the relevant
one and preserve the existing contract; do not assume features are registered
the same way strategies are.

### Stale/broken `make_generator` factory

**What happens:** `make_generator` in `src/pc2img/registry.py:7` constructs
`PointCloudImageGenerator(pcd, proj, interp)` with no `img_res`, which the
current `__init__` requires (`core.py:67`).
**Why it's wrong:** The factory does not match the current constructor signature
and will fail if called.
**Do this instead:** Construct `PointCloudImageGenerator` directly with
`pcd`, `img_res`, `proj`, `interp` (see `scripts/v2.0/04_img_gen.py`), or update
the factory before relying on it.

### `project()` / `project_raw()` return-arity mismatch

**What happens:** The shared `ProjectionStrategy.project` unpacks four values
`(coords_raw, mask, mins, maxs)` (`projection.py:70`), but
`OrthographicProjection.project_raw` returns only two (`projection.py:179`,
`# Todo: Update to pass min and max back!`).
**Why it's wrong:** Orthographic projection is inconsistent with the base
contract and will break when routed through `project`.
**Do this instead:** Return the full `(coords_raw, mask, mins, maxs)` tuple from
every `project_raw` override.

### Large commented-out code blocks

**What happens:** `interpolation.py`, `disk_backed_image_store.py`, and
`disk_backed_image_data.py` carry sizeable commented-out alternative
implementations.
**Why it's wrong:** Dead code obscures the live path and invites confusion about
what is actually executed.
**Do this instead:** Rely on the uncommented implementation; remove dead blocks
when editing those files rather than extending them.

## Error Handling

**Strategy:** Fail fast with typed exceptions during construction/validation;
tolerate missing data with NaN fills during rasterization.

**Patterns:**
- Coercion errors raise `TypeError`/`ValueError` from Pydantic validators and
  strategy `validate` classmethods (`core.py`, `projection.py:38`).
- Registry misuse raises `KeyError` (unknown/duplicate strategy) or
  `RuntimeError` (duplicate/ambiguous feature pattern) (`registry.py`).
- Numerical paths use NaN sentinels: outside-hull grid points and thinned
  triangles fill with `np.nan` (`interpolation.py:204`), and NaN-aware helpers
  (`util.nanconv`) propagate them.
- Note: `DiskBackedImageData.__array_ufunc__` currently `raise NotImplemented`
  (a non-exception object) — arithmetic on the wrapper is effectively disabled
  (`disk_backed_image_data.py:74`).

## Cross-Cutting Concerns

**Logging:** Standard library `logging`, module-level `logger =
logging.getLogger(__name__)` (e.g. `interpolation.py:20`, `tiled_generator.py:23`);
some modules use the top-level package name (`disk_backed_image_store.py:17`).
**Validation:** Pydantic v2 — `@validate_call(config=ConfigDict(arbitrary_types_allowed=True))`,
`@pydantic_dataclass`, and `BeforeValidator` coercers in `core.py`.
**Persistence:** `GSEGUtils.lazy_disk_cache` (`LazyDiskCache`,
`LazyDiskCacheConfig`, `DiskBackedNDArray`, `DiskBackedStore`) underpins all
offloading; cache paths are extended per-feature, per-tile, and per-triangulation-hash.

---

*Architecture analysis: 2026-07-08*
