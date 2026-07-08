# Codebase Structure

**Analysis Date:** 2026-07-08

## Directory Layout

```
pc2img/
├── src/pc2img/               # The installed package (src-layout)
│   ├── __init__.py           # Public API re-exports (PointCloudImageGenerator, subpackages)
│   ├── _version.py           # setuptools_scm generated version (do not edit)
│   ├── core.py               # PointCloudImageGenerator + input coercers + ImgRes
│   ├── tiled_generator.py    # TiledPointCloudImageGenerator (parallel tiles)
│   ├── registry.py           # make_generator convenience factory (currently stale)
│   ├── util.py               # Colormap / NaN-aware image conversion helpers
│   ├── strategies/           # Projection + interpolation strategy family
│   │   ├── __init__.py       # Re-exports + imports modules for registration
│   │   ├── projection.py     # ProjectionStrategy, Spherical/Orthographic
│   │   ├── interpolation.py  # InterpolationStrategy, Delaunay/Linear/NN/Cubic
│   │   ├── triangulation.py  # TriangulationStrategy (standalone)
│   │   ├── registry.py       # StrategyRegistry, PROJECTIONS, INTERPOLATIONS
│   │   └── utils.py          # thin_points_by_pixel_density
│   ├── features/             # Named-feature computation subsystem
│   │   ├── __init__.py       # Re-exports + imports feature modules for registration
│   │   ├── manager.py        # FeatureManager (request/resolve/compute)
│   │   ├── registry.py       # FeatureRegistry, FeatureSpec, FEATURES singleton
│   │   ├── core.py           # BaseFeatureStrategy / DerivativeFeatureStrategy ABCs
│   │   ├── base_features.py  # RangeFeature, ScalarFieldFeature (per-point 1D)
│   │   ├── derivative_features.py # Gradient, Sobel, Hillshade, Norm, MultiScale... (raster 2D)
│   │   └── rrim.py           # Red Relief Image Map features
│   └── image_cache/          # Lazy disk-backed raster storage
│       ├── __init__.py       # Re-exports DiskBackedImageStore, DiskBackedImageData
│       ├── disk_backed_image_store.py  # MutableMapping store with pickle offload
│       └── disk_backed_image_data.py   # Single raster wrapper (LazyDiskCache)
├── tests/                    # Pytest suite (see TESTING.md)
├── scripts/                  # Manual/dev usage examples (v1.0, v2.0, numbered)
├── third_party/              # Symlinks to local dep sources (gitignored)
├── build/, _old/, _scrap/, _tests/  # Legacy / scratch (not part of package)
├── pyproject.toml            # Build config, deps, setuptools_scm
├── pyrightconfig.json        # Type-checker config
├── release-please-config.json / .release-please-manifest.json  # Release automation
└── .github/workflows/release-please.yml  # CI (release automation only)
```

## Directory Purposes

**`src/pc2img/` (package root):**
- Purpose: The shipped library; only this tree is packaged (`top_level.txt` → `pc2img`)
- Contains: orchestration, strategies, features, image_cache subpackages
- Key files: `core.py`, `tiled_generator.py`

**`src/pc2img/strategies/`:**
- Purpose: Interchangeable projection + interpolation algorithms
- Contains: strategy ABCs, concrete strategies, the `StrategyRegistry`
- Key files: `projection.py`, `interpolation.py`, `registry.py`

**`src/pc2img/features/`:**
- Purpose: Regex-named feature DSL and computation
- Contains: `FeatureManager`, `FeatureRegistry`, base + derivative feature strategies
- Key files: `manager.py`, `registry.py`, `derivative_features.py`

**`src/pc2img/image_cache/`:**
- Purpose: Memory-bounded raster storage backed by pickle files
- Key files: `disk_backed_image_store.py`, `disk_backed_image_data.py`

**`tests/`:**
- Purpose: Pytest suite covering generator, cache, and RRIM features
- Key files: `test_point_cloud_image_generator.py`, `test_rrim_features.py`

**`scripts/`:**
- Purpose: Non-packaged manual/dev entry points and experiments
- Note: `v1.0/` is legacy; `v2.0/` targets the current API

**Legacy / non-package (ignore for new work):** `_old/`, `_scrap/`, `_tests/`,
`build/`. These are not imported by the package and should not be extended.

## Key File Locations

**Entry Points:**
- `src/pc2img/core.py`: `PointCloudImageGenerator` — primary public API
- `src/pc2img/tiled_generator.py`: `TiledPointCloudImageGenerator` — parallel path
- `src/pc2img/__init__.py`: package-level re-exports

**Configuration:**
- `pyproject.toml`: dependencies, build backend, `setuptools_scm` versioning
- `pyrightconfig.json`: type checking
- `release-please-config.json`: release automation

**Core Logic:**
- `src/pc2img/features/manager.py`: dependency resolution + compute loop
- `src/pc2img/strategies/interpolation.py`: Delaunay rasterization (largest hot path)
- `src/pc2img/strategies/projection.py`: 3D→2D mapping

**Testing:**
- `tests/`: co-located test modules (`test_*.py`)

## Naming Conventions

**Files:**
- `snake_case.py` modules (e.g. `disk_backed_image_store.py`)
- One primary class per module, module named after it in snake_case
- Test files: `test_<subject>.py`
- Scripts: `NN_description.py` (numbered ordering), grouped under version dirs

**Directories:**
- `snake_case` subpackage names matching a domain concern (`strategies`, `features`, `image_cache`)
- Leading `_` marks non-package/legacy dirs (`_old`, `_scrap`, `_tests`)

**Symbols:**
- Classes `PascalCase`; functions/variables `snake_case`
- Registry singletons UPPERCASE (`PROJECTIONS`, `INTERPOLATIONS`, `FEATURES`)
- `Name`-suffixed `Literal` type aliases enumerate valid keys (`ProjectionName`, `InterpolationName`)
- Feature *names* are a lowercase DSL parsed by regex (e.g. `gradient_x_range`,
  `normalized_range_2_98`, `rrim_(r16,d8)`)

## Where to Add New Code

**New projection or interpolation strategy:**
- Implementation: add a class in `src/pc2img/strategies/projection.py` or
  `interpolation.py`, subclass the ABC, decorate with `@PROJECTIONS.register("key")`
  / `@INTERPOLATIONS.register("key")`
- Export: add the class + key to `strategies/__init__.py.__all__` and the
  `Literal` name alias, so import-time registration runs
- Tests: `tests/test_point_cloud_image_generator.py` or a new `tests/test_*.py`

**New feature (per-point 1D):**
- Implementation: add to `src/pc2img/features/base_features.py`, subclass
  `BaseFeatureStrategy`, set `regex_pattern`, decorate `@FEATURES.register`
- Export: add to `features/__init__.py`

**New feature (raster 2D / derivative):**
- Implementation: add to `src/pc2img/features/derivative_features.py` (or a new
  module like `rrim.py` for a cohesive family), subclass
  `DerivativeFeatureStrategy`, set `regex_pattern`, list `dependencies`
- Export: import the module in `features/__init__.py` so `@FEATURES.register` runs
- Tests: follow `tests/test_rrim_features.py`

**New utility:**
- Image/array helpers: `src/pc2img/util.py`
- Strategy-local helpers: `src/pc2img/strategies/utils.py`

**New orchestration behavior:**
- Single-cloud: `src/pc2img/core.py`
- Multi-tile/parallel: `src/pc2img/tiled_generator.py`

## Special Directories

**`third_party/`:**
- Purpose: symlinks to local sources of `GSEGUtils` and `pchandler` for editable dev
- Generated: symlinks created manually; Committed: No (gitignored)

**`src/pc2img/_version.py`:**
- Purpose: version string written by `setuptools_scm`
- Generated: Yes; Committed: No (do not hand-edit)

**`src/pc2img.egg-info/`:**
- Purpose: editable-install metadata; Generated: Yes; Committed: No

**`build/`, `_old/`, `_scrap/`, `_tests/`:**
- Purpose: build output and legacy scratch; Generated/legacy; not part of the package

---

*Structure analysis: 2026-07-08*
