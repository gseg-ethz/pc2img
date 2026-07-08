# External Integrations

**Analysis Date:** 2026-07-08

> **Summary:** `pc2img` is a self-contained, offline scientific library that converts point clouds into raster images. It makes **no network calls**, uses **no database**, has **no authentication**, and exposes **no webhooks**. Its "integrations" are (a) file formats it reads/writes, (b) two sibling first-party libraries it depends on, and (c) the GitHub Actions release pipeline. No `os.environ`/`getenv`, `requests`, `urllib`, `socket`, `boto3`, or DB-client usage exists in `src/pc2img/` (verified by grep).

## APIs & External Services

**None.** No outbound HTTP/RPC/SDK calls of any kind. The only URL in the source is a documentation reference in a docstring (`src/pc2img/util.py:324`, a Middlebury flow-eval PDF link), not a live call.

## Data Storage

**Databases:**
- None. No SQL/NoSQL client, ORM, or connection string anywhere.

**File I/O - Point cloud inputs (read):**
- pc2img itself operates on in-memory `PointCloudData` objects (from `pchandler`); it does not read raw files directly in library code.
- File loading is delegated to `pchandler.data_io`, used in example scripts:
  - `load_ply(...)` - PLY format (`scripts/04_generate_overview.py`, `scripts/06_test_orthometric.py`, `scripts/08_generating_different_rasterization.py`). Backed by `plyfile`.
  - `load_e57(...)` - E57 format (`scripts/05_test_tiled_image_generator.py`, `scripts/06_test_orthometric.py`). Backed by `pye57`.
  - LAS/LAZ - available via pchandler's `laspy[laszip,lazrs]` dependency.

**File I/O - Image outputs (write):**
- Rasterized features are converted to `uint8` arrays in `src/pc2img/util.py` (`convert_to_image`) and written as images via the declared imaging stack: `imageio ~=2.31`, `Pillow ~=10.0`, `tifffile[all] ~=2024.1` (PNG/TIFF, including multi-page scientific TIFF), and `opencv-python ~=4.0`.
- Example: `TiledContinuousImageGenerator.save_all_images(...)` in `src/pc2img/tiled_generator.py` (used in `scripts/05_test_tiled_image_generator.py`).

**Disk cache (local filesystem):**
- The heavy integration point is `GSEGUtils.lazy_disk_cache`, a local disk-backed cache for large ndarrays/images.
  - `LazyDiskCache`, `LazyDiskCacheConfig`, `LazyDiskCacheKw`, `DiskBackedNDArray`, `DiskBackedStore` used in `src/pc2img/core.py`, `strategies/interpolation.py`, `image_cache/disk_backed_image_data.py`, `image_cache/disk_backed_image_store.py`, `features/manager.py`, `tiled_generator.py`.
  - Cache location is set by `LazyDiskCacheConfig.cache_path`; when unset, offloading is disabled (`src/pc2img/image_cache/disk_backed_image_store.py` logs a warning and skips).
  - Serialization is via Python `pickle` (`disk_backed_image_store.py` `pickle.dump`/`pickle.load`). Note: pickle-based cache files are a trust/portability consideration - see CONCERNS.

**Caching (in-memory / other):**
- Local disk cache only (above). No Redis/Memcached or external cache service.

## Authentication & Identity

**None.** No auth provider, token handling, or identity code. The library has no notion of users or sessions.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Rollbar/etc.).

**Logs:**
- Standard-library `logging` only. Module loggers via `logging.getLogger(__name__)` (`src/pc2img/tiled_generator.py`) and a package-root logger `logging.getLogger(__name__.split(".")[0])` (`src/pc2img/image_cache/disk_backed_image_store.py`). No handler/format configuration is imposed by the library (left to the host application).

## Compute / Parallelism

- joblib process-based parallelism is the one "infrastructure" integration. `src/pc2img/tiled_generator.py` uses `Parallel`, `delayed`, and `parallel_config(backend="loky", n_jobs=..., prefer="processes")`. Scripts pass `n_jobs=-1`/`-5` to fan out tile processing across CPU cores.
- Optional GPU acceleration is available transitively through pchandler's RAPIDS (`cudf`/`cuml`/`cuspatial`/`cuproj`/`dask-cudf` `25.4.*`) via pc2img's `cuda11`/`cuda12` extras; requires NVIDIA's package index (`https://pypi.nvidia.com`).

## CI/CD & Deployment

**Hosting:**
- Not applicable - published as an importable package, not deployed as a service.

**CI Pipeline:**
- GitHub Actions: `.github/workflows/release-please.yml`. Single workflow, triggered on push to `main`.
  - Uses `googleapis/release-please-action@v4` with `release-please-config.json` to open/maintain release PRs and generate `CHANGELOG.md` from Conventional Commits.
  - On release, creates/moves rolling major (`vX`) and minor (`vX.Y`) tags.
  - Runner: `ubuntu-latest`. Permissions: `contents: write`, `pull-requests: write`, `issues: write`.
- No test/lint/build CI workflow exists - tests and type checks are run locally only. See CONCERNS.

**Release versioning:**
- `setuptools_scm` derives package version from git tags at build time (`src/pc2img/_version.py`, generated). Current release per manifest: `0.10.4`.

## Environment Configuration

**Required env vars:**
- None for the library at runtime.

**CI secrets:**
- `GITHUB_TOKEN` (GitHub-provided) - consumed by the release-please workflow for checkout, PR, and tag operations (`.github/workflows/release-please.yml`).

**Secrets location:**
- No application secrets. No `.env` file is present or read by the code. (No `os.environ` access anywhere in `src/pc2img/`.)

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

## First-Party Dependency Linkage (integration note)

- `pchandler` and `GSEGUtils` are the project's own upstream libraries and the primary integration surface. In `pyproject.toml` their dependency declarations are **commented out**; locally they are provided through symlinks under `third_party/` (`third_party/pchandler -> /scratch/41_pchandler`, `third_party/gsegutils -> /scratch/30_GSEGUtils`), and `third_party/` is gitignored. The installed versions are `pchandler 2.1.0.post2` and `GSEGUtils 0.5.2.post2`. A clean `pip install .` will not resolve these automatically - this is a deliberate local-development arrangement (see MEMORY: pc2img-dependency-rework) and a packaging gap flagged in CONCERNS.

---

*Integration audit: 2026-07-08*
