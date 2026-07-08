# Technology Stack

**Analysis Date:** 2026-07-08

## Languages

**Primary:**
- Python `~=3.12,<3.13` - Entire codebase. Source under `src/pc2img/`, scripts under `scripts/`, tests under `tests/`. Constrained to CPython 3.12 in `pyproject.toml` (`requires-python`) and `pyrightconfig.json` (`pythonVersion: "3.12"`).

**Secondary:**
- Not applicable - single-language project. No compiled extensions authored here; native code is pulled in transitively via wheels (numpy, scipy, opencv, shapely, etc.).

## Runtime

**Environment:**
- CPython 3.12 only. Upper bound `<3.13` is a hard pin (`pyproject.toml`).
- Local dev interpreters observed: a virtualenv at `.venv/` (Python 3.12) and a conda env `pc2img-dev312` referenced by `pyrightconfig.json` (`venvPath: /scratch/miniconda3/envs`).

**Package Manager:**
- pip (working install present in `.venv/lib/python3.12/site-packages/`).
- No lockfile (no `requirements.txt`, `poetry.lock`, `uv.lock`, or `Pipfile.lock`). Dependency versions are floated via `~=` compatible-release specifiers in `pyproject.toml` - Lockfile: missing.

**Build Backend:**
- `setuptools` + `setuptools_scm` (`pyproject.toml` `[build-system]`).
- Version is dynamic, derived from git tags by `setuptools_scm` and written to `src/pc2img/_version.py`. `local_scheme = "no-local-version"`, `version_scheme = "post-release"`. Tags match `v[0-9]*.[0-9]*.[0-9]*`.
- Minimal `setup.py` shim (`setup.py`) delegates entirely to declarative config.

## Frameworks

This is a scientific/geospatial **library** (point cloud → image rasterization), not an application framework. There is no web/UI/CLI framework.

**Core:**
- NumPy `~=2.0` (installed `2.3.5`) - Fundamental array type used throughout. `NDArray` typing is pervasive.
- SciPy `~=1.14` - Spatial and signal ops: `scipy.spatial.Delaunay` (`src/pc2img/strategies/triangulation.py`, `strategies/interpolation.py`), `scipy.interpolate.{LinearNDInterpolator, NearestNDInterpolator, CloughTocher2DInterpolator}` (`strategies/interpolation.py`), `scipy.signal.convolve2d` and `scipy.ndimage` (`src/pc2img/util.py`).
- Pydantic `~=2.11` (installed `2.13.4`) - Runtime validation/coercion of the public API via `@validate_call`, `ConfigDict`, `BeforeValidator` (`src/pc2img/core.py`); pydantic dataclasses used in strategies/features.

**Testing:**
- pytest (declared under `[project.optional-dependencies].dev`; no pinned version). Config-less (no `pytest.ini`/`tox.ini`/`[tool.pytest]`). Tests live in `tests/`. `.pytest_cache/` present.

**Build/Dev:**
- `setuptools_scm` - versioning from git.
- black `~=23.10` - formatter (dev extra).
- memory_profiler - profiling (dev extra).
- sphinx `~=5.1` - docs (doc extra). Note: `release-please-config.json` lists `docs/conf.py` as an extra-file, but no `docs/` directory exists in the tree yet.
- Pyright (basic mode) - type checking, configured by `pyrightconfig.json` (`typeCheckingMode: "basic"`, `reportMissingImports: "error"`, include `src/pc2img`, `scripts`, `tests`).

## Key Dependencies

**Critical (declared in `pyproject.toml` `dependencies`):**
- `numpy ~= 2.0` - core arrays.
- `scipy ~= 1.14` - triangulation/interpolation/convolution.
- `pydantic ~= 2.11` - API validation.
- `joblib ~= 1.5` (and a redundant `joblib ~= 1.3` line - see CONCERNS) - process-based parallelism (`loky` backend) in `src/pc2img/tiled_generator.py`.
- `imageio ~= 2.31` - image read/write.
- `Pillow ~= 10.0` - image backend.
- `tifffile[all] ~= 2024.1` - TIFF I/O (multi-page/scientific).
- `opencv-python ~= 4.0` - image ops.
- `typing-extensions ~= 4.9` (installed `4.16.0`) - backport typing constructs.

**Vendored / sibling first-party dependencies (CRITICAL, but commented out in `pyproject.toml`):**
- `pchandler` (installed `2.1.0.post2`) - supplies `PointCloudData`, `pchandler.filters` (`FoVFilter`, `BoxFilter`), `pchandler.geometry.spherical.FoV`, `pchandler.geometry.coordinates.rhv2xyz`, and `pchandler.data_io` loaders (`load_ply`, `load_e57`). Imported across `core.py`, `features/`, `strategies/projection.py`, `tiled_generator.py`.
- `GSEGUtils` (installed `0.5.2.post2`) - supplies the disk-cache layer: `GSEGUtils.lazy_disk_cache.{LazyDiskCache, LazyDiskCacheConfig, LazyDiskCacheKw, DiskBackedNDArray, DiskBackedStore}` and `GSEGUtils.config.{get_defaults, CacheDefaults}`. Used in `core.py`, `strategies/interpolation.py`, `image_cache/`, `features/manager.py`, `tiled_generator.py`.

These two are the project's own upstream libraries. In `pyproject.toml` their dependency lines are commented (`# "pchandler[cuda12] ~= 1.0"`, `# "GSEGUtils ~= 0.2"`), and they are wired in locally via symlinks in `third_party/` (`third_party/pchandler -> /scratch/41_pchandler`, `third_party/gsegutils -> /scratch/30_GSEGUtils`). `third_party/` is gitignored. This means an out-of-the-box `pip install .` does NOT pull these in - see CONCERNS.

**Optional runtime dependency (undeclared):**
- matplotlib - lazily imported inside `src/pc2img/util.py` `convert_to_image()` only when a colormap is requested; raises `RuntimeError("Colormap requires matplotlib")` if absent. Not listed in `pyproject.toml`.

**Transitive geospatial/point-cloud stack (via pchandler):** `laspy[laszip,lazrs] ~=2.6`, `pye57 ~=0.4`, `plyfile ~=1.1`, `shapely ~=2.1`, `alphashape ~=1.3`, `numpydantic ~=1.10`, `trimesh`, `rtree`, `pyquaternion`. GSEGUtils adds `psutil ~=7.0`.

## Configuration

**Runtime configuration:**
- No environment variables are read anywhere in `src/pc2img/` (no `os.environ`/`getenv` usage). The library is configured purely through Python call arguments and Pydantic-validated config objects.
- Cache behavior is configured through `LazyDiskCacheConfig` (from GSEGUtils), accepted as a mapping or object and coerced in `src/pc2img/core.py` (`coerce_lazy_cfg`). Defaults come from `GSEGUtils.config.get_defaults` / `CacheDefaults`.
- Image resolution is a validated `ImgRes(width, height)` NamedTuple (`src/pc2img/core.py`).

**Optional GPU acceleration:**
- `[project.optional-dependencies]` defines `cuda12` and `cuda11` extras pinning RAPIDS `25.4.*` (`cudf`, `cuspatial`, `cuproj`, `cuml`, `dask-cudf`). These require `--extra-index-url=https://pypi.nvidia.com` (noted inline). GPU code paths are exercised through pchandler, not directly in pc2img source.

**Build config:**
- `pyproject.toml` - single source of build/dependency/tool config.
- `pyrightconfig.json` - type-checker config.
- `.editorconfig` - `.rst` files use 3-space indent.
- `release-please-config.json` + `.release-please-manifest.json` (current release `0.10.4`) - release automation config.

## Platform Requirements

**Development:**
- Python 3.12 (exactly; `<3.13`).
- The two sibling libraries (`pchandler`, `GSEGUtils`) must be installed - locally provided via `third_party/` symlinks to adjacent checkouts (`/scratch/41_pchandler`, `/scratch/30_GSEGUtils`). See MEMORY: dependency-rework tracks keeping local copies aligned with PyPI releases.
- Optional: matplotlib (colormaps), CUDA 11/12 toolchain + RAPIDS 25.4 for GPU extras.

**Production:**
- No deployment target - distributed as an importable Python package (`pc2img`). No server, container, or service. Public entry point `pc2img.PointCloudImageGenerator` (`src/pc2img/__init__.py`).

---

*Stack analysis: 2026-07-08*
