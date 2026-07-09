# Phase 2: Dependency Adaptation & Reproducible Environment - Research

**Researched:** 2026-07-09
**Domain:** Python packaging / dependency pinning / `uv` reproducibility + pchandler 2.x semantic-break adaptation
**Confidence:** HIGH (pipeline runtime-proven, PyPI verified, call sites audited, uv syntax cited from official docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `pchandler` and `GSEGUtils` resolve from **public PyPI**. Clean `uv sync` / `pip install pc2img` fetches both from pypi.org — no index config, no git URLs, no `third_party/` symlinks for the default install.
- **D-02:** Pin with **compatible-release** specifiers: `pchandler ~= 2.1`, `GSEGUtils ~= 0.5`. Loose in `pyproject`, exact in the committed lockfile. Keep the requirement name **capitalized** (`GSEGUtils`).
- **D-03:** **numpy stays loose: `numpy ~= 2.0`.** Rely on pchandler's transitive `<2.4` to cap resolution (effective `>=2.0,<2.4`).
- **D-04:** **Wire GPU extras to pchandler.** pc2img `cuda12` → `pchandler[cuda12]`, `cuda11` → `pchandler[cuda11]`. Declaration only; GPU-path validation stays deferred to GPU-01 (v2).
- **D-05:** **Native `uv.lock` project workflow.** `uv lock` → universal `uv.lock` committed; `uv sync` recreates env. **Keep the `setuptools_scm` build backend.**
- **D-06:** **Lock everything, including GPU.** Configure explicit nvidia index (`[[tool.uv.index]] name="nvidia" url="https://pypi.nvidia.com" explicit=true`) so cuda extras resolve into the universal lock.
- **D-07:** **Document the uv workflow in `CONTRIBUTING.md`** (`uv sync`, `uv run pytest`, `uv lock` after dep changes).
- **D-08:** **Move `dev`+`doc` to PEP 735 `[dependency-groups]`; keep `cuda11`/`cuda12` as `[project.optional-dependencies]` extras.** `uv sync` installs `dev` by default; `uv sync --group doc` for docs. Intentional divergence from pchandler.
- **D-09:** **Prove SC1 with a committed smoke script** (e.g. `scripts/smoke_pipeline.py`) running the single-cloud pipeline end-to-end, asserting completion + basic output sanity. Runnable via `uv run`; promotable to a pytest smoke test in Phase 3.
- **D-10:** **Run the smoke on a synthetic, in-code point cloud** (deterministic numpy arrays → `PointCloudData`), no external file. **Spherical** projection + Delaunay interpolation + a simple feature (`range`). Avoids orthographic (BUG-01) and WIP `PerspectiveProjection`.
- **D-11:** **Fix all three named breaks at the code level; verify proportionately.** Runtime-prove the FoVTree 2D identifier behavior on the smoke path; for the two off-path breaks (`to_py4dgeo`, Csv/Las) audit call sites, fix if broken, add a small targeted assertion — no full loader fixtures.
- **D-12:** **PyPI + `uv.lock` is canonical resolution** (satisfies SC3). `third_party/` symlinks stay as gitignored source-investigation aids. Do **not** commit `[tool.uv.sources]` pointing at local paths.
- **D-13:** Both sibling repos are **owner-controlled**. Strongly-advisable changes to `pchandler`/`GSEGUtils` → raise with owner first, don't edit unilaterally.

### Claude's Discretion
- Exact smoke-script filename/location and the synthetic cloud's size/shape/seed.
- Precise `pyproject.toml` layout ordering and how the nvidia index + cuda package sources are expressed in `[tool.uv]` (as long as D-06 holds).
- Exact form of the off-path `to_py4dgeo` / Csv-Las targeted assertions (D-11).
- Whether GPU-extra resolution issues (nvidia index misbehaving offline) warrant a scoped fallback — flag to owner if D-06 proves impractical.

### Deferred Ideas (OUT OF SCOPE)
- **`black -> ruff` + lint-in-CI** — Phase 3/4.
- **GPU-01 (v2)** — actual GPU-path validation.
- **Mirror PEP 735 dev/doc grouping into pchandler** — separate owner-controlled repo.
- `guard-transformarray-module-import` — stays Phase 4.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEP-01 | pc2img runs against PCHandler 2.x with all semantic/runtime breaks resolved (FoVTree 2D identifiers, world-frame `to_py4dgeo`, Csv/Las load behavior) | **All three named breaks have ZERO call sites in `src/pc2img/`** (§Semantic-Break Reality). The actually-exercised pchandler surface is runtime-proven by a full synthetic smoke run (§Smoke Path — Runtime-Proven). DEP-01 is satisfied by: (a) smoke proving the exercised FoV/spherical surface, (b) a documented negative audit for the three named breaks. |
| DEP-02 | pc2img runs against current GSEGUtils release (`lazy_disk_cache`, `config`, `base_types`), respecting the `gsegutils`/`GSEGUtils` casing gotcha | GSEGUtils import surface enumerated + runtime-proven (§GSEGUtils Reality). No GSEGUtils BC requires a pc2img source change. DiskBackedStore/LazyDiskCache path exercised by Delaunay in the smoke run. Casing gotcha confirmed (dist `gsegutils`, import `GSEGUtils`). |
| DEP-03 | `pyproject.toml` re-enables + pins `pchandler` + `GSEGUtils`, resolves the numpy 2.x pin conflict | Both siblings on public PyPI, versions + metadata verified (§Package Legitimacy Audit). numpy intersection `>=2.0,<2.4` confirmed. `pyproject.toml` change spec in §Standard Stack. |
| DEP-04 | Dev env reproducibly set up with `uv` (documented; lockfile committed) | uv 0.11.26 present; `uv.lock`/`CONTRIBUTING.md` absent (to create). Current uv syntax for dependency-groups + explicit index confirmed from official docs (§uv Reproducibility Tooling). |
</phase_requirements>

## Summary

This is a **packaging + reproducibility phase with a thin adaptation layer**, and the adaptation layer is thinner than CONTEXT.md assumed. I audited every call site and ran the single-cloud pipeline end-to-end against the installed `pchandler==2.1.0.post2` / `gsegutils==0.5.2.post2`. **All three named pchandler semantic breaks (BC-PCH-007 world-frame `to_py4dgeo`, BC-PCH-008 FoVTree 2D identifiers, BC-PCH-006/012 Csv/Las load behavior) have zero call sites in `src/pc2img/`.** The library never imports `FoVTree`, never calls `to_py4dgeo`, and never uses the Csv/Las loaders. So DEP-01's "fixes" are, at the code level, **no-ops verified by a documented negative audit** — there is nothing broken to fix. What *is* exercised (and what the smoke script proves) is the `FoV` / spherical / `pcd.r` / `pcd.spher` / `FoVFilter` surface, which works correctly.

The genuinely load-bearing work is: (1) re-enable + pin `pchandler ~= 2.1` and `GSEGUtils ~= 0.5` in `pyproject.toml` (currently commented out — the package cannot `pip install` cleanly), wire GPU extras to pchandler, and restructure dev/doc into PEP 735 groups; (2) stand up `uv.lock` + a `CONTRIBUTING.md` workflow; (3) commit a synthetic smoke script as durable SC1 evidence. Both siblings are on **public PyPI** under the `gseg-ethz` org (owner-controlled), so D-01's clean-install premise is valid. The numpy pin already intersects cleanly (`>=2.0,<2.4`).

**Two things the planner must not miss.** First — a **real on-smoke-path blocker**: the `PointCloudImageGenerator` default `lazy_disk_cache_config=None` is *not* coerced (pydantic `validate_call` doesn't validate default values), so `None` reaches `DiskBackedImageStore` and raises a `ValidationError`. The smoke script must pass an explicit `LazyDiskCacheConfig(cache_path=<tmpdir>)` (it needs a temp cache dir anyway). Second — the CONTEXT/D-11 claim "spherical projection exercises `FoV`/`FoVTree`" is **inaccurate**: it exercises `FoV`, not `FoVTree`. The smoke cannot "runtime-prove the FoVTree break" because pc2img never touches FoVTree; the proportionate verification for BC-PCH-008 is an audit, not a runtime proof.

**Primary recommendation:** Treat DEP-01 as *audit-and-attest* for the three named breaks (they don't apply), spend the effort on the `pyproject.toml`/`uv.lock`/`CONTRIBUTING.md` packaging work and a clean synthetic smoke script that passes an explicit cache config, and flag the two accuracy corrections (None-config coercion gap; FoVTree-not-on-path) to the planner.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dependency declaration / pinning | Build metadata (`pyproject.toml`) | — | `[project.dependencies]` + `[project.optional-dependencies]` own the resolution surface |
| Reproducible env lock | Package manager (`uv`) | Build backend (`setuptools_scm`) | `uv.lock` pins exact versions; setuptools_scm still builds the wheel/editable install |
| Semantic-break adaptation | Library source (`src/pc2img/`) | pchandler/GSEGUtils (dep) | Adaptation lives in pc2img call sites — but audit shows the named breaks have no call sites |
| SC1 runtime proof | Committed script (`scripts/`) | Library entry point (`core.py`) | Smoke drives `PointCloudImageGenerator.generate` on synthetic input |
| Dev-workflow documentation | Repo docs (`CONTRIBUTING.md`) | — | Dev bootstrap separated from user-facing `README.rst` (D-07) |

## Semantic-Break Reality (DEP-01 / D-11) — the core finding

I read `/scratch/41_pchandler/MIGRATION-v1.0.md` (BC-PCH-001..015) and grepped every call site in `src/pc2img/` and `scripts/`.

| Break | What changed in pchandler 2.x | Call sites in `src/pc2img/` | Verdict |
|-------|-------------------------------|-----------------------------|---------|
| **BC-PCH-008** FoVTree 2D `"<r>-<c>"` identifiers | `FoVTree.build_from_tiles` / `__getitem__` / `.identifier` now emit collision-free 2D `"<r>-<c>"` strings; `__getitem__` accepts full identifier strings `[CITED: /scratch/41_pchandler/MIGRATION-v1.0.md BC-PCH-008]` | **NONE.** `grep FoVTree src/` → nothing. `FoVTree` appears only in `scripts/v2.0/03_tiled_image_gen.py` (an example driver, not library code). `tiled_generator.py` takes **pre-built** `PointCloudTile`s; it does not build a FoVTree. `[VERIFIED: grep src/]` | Not affected. Audit-only. |
| **BC-PCH-007** world-frame `to_py4dgeo` | `PointCloudData.to_py4dgeo` now returns world-frame (not shift-frame) coords, preserves normals/scalar fields `[CITED: MIGRATION-v1.0.md BC-PCH-007]` | **NONE.** `grep to_py4dgeo src/ scripts/` → nothing anywhere. `[VERIFIED: grep src/ scripts/]` | Not affected. Audit-only. |
| **BC-PCH-006/012** Csv/Las load behavior | `Las.load` caller-wins `numerical_optimization_shift`; `Csv.load` strict-by-name field selection raising `ValueError` on missing fields `[CITED: MIGRATION-v1.0.md BC-PCH-006, BC-PCH-012]` | **NONE.** No `Csv`/`Las`/`load_csv`/`load_las`/`CsvHandler`/`LasHandler` in `src/`. The only loaders anywhere are `load_ply`/`load_e57`/`Ply.load` in `scripts/` (examples). The only `.load(` / `pickle.load` in `src/` is pc2img's *own* image-store pickle offload. `[VERIFIED: grep src/]` | Not affected. Audit-only. |

**What the spherical projection actually exercises** (`src/pc2img/strategies/projection.py`): `pchandler.geometry.spherical.FoV` (via `pcd.fov`), `pchandler.filters.FoVFilter` + `BoxFilter`, `pchandler.geometry.coordinates.rhv2xyz`, `pchandler.geometry.transforms._TransformArray` (private, module-scope import — Phase 4 fragility todo), and `PointCloudData` properties `pcd.spher`, `pcd.fov`, `pcd.nbPoints`, `pcd.r`, `pcd.scalar_fields`. The `FoV` object exposes `.left/.right/.top/.bottom` (returned as `Angle`) and `.ratio()` — all present and working `[VERIFIED: runtime probe]`. **`FoV` is a different symbol from `FoVTree`; BC-PCH-008 did not change `FoV`.**

### ⚠️ Accuracy corrections for the planner (do NOT silently override — flag)
1. **D-11 says "spherical projection exercises `FoV`/`FoVTree`."** It exercises **`FoV` only**. pc2img's library has no `FoVTree` usage. The smoke path *cannot* runtime-prove BC-PCH-008. Recommended framing: smoke runtime-proves the exercised `FoV`/spherical surface; BC-PCH-008 gets a documented negative audit (grep-attest), optionally noting `scripts/v2.0/03_tiled_image_gen.py` already uses the new `build_from_tiles` API shape.
2. **DEP-01 lists three breaks "to resolve."** At the code level there is nothing to resolve — all three are absent from the library. The proportionate, honest deliverable is an **audit attestation** (a short doc/assertion recording "no call sites; not affected") rather than code edits. This *is* consistent with D-11 ("audit the call sites, fix if broken") — the finding is simply "not broken because not called."

## Smoke Path — Runtime-Proven (SC1 / D-09 / D-10)

I built a synthetic deterministic cloud and ran the full pipeline in the existing `.venv` against the installed deps. **It completes and produces finite output.** `[VERIFIED: runtime execution]`

Minimal correct construction (recommended smoke shape):
```python
# Source: runtime-verified against pchandler 2.1.0.post2 / GSEGUtils 0.5.2.post2
import tempfile
from pathlib import Path
import numpy as np
from pchandler import PointCloudData
from pchandler.geometry.coordinates import rhv2xyz
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from pc2img.core import PointCloudImageGenerator
from pc2img.strategies import SphericalProjection, DelaunayInterpolation

rng = np.random.default_rng(42)                 # deterministic (D-10)
n = 8000
h = rng.uniform(-0.30, 0.30, n)                 # horizontal angle (rad)
v = rng.uniform(1.20, 1.80, n)                  # vertical/polar angle (rad)
r = 10.0 + 0.5 * np.sin(4 * h) + 0.3 * rng.standard_normal(n)   # gentle structured range
xyz = rhv2xyz(np.column_stack([r, h, v])).astype(np.float64)
pcd = PointCloudData(xyz=xyz)                    # r / spher / fov derived automatically

with tempfile.TemporaryDirectory() as td:
    cfg = LazyDiskCacheConfig(cache_path=Path(td))          # ← REQUIRED (see blocker below)
    gen = PointCloudImageGenerator(
        pcd, (200, 200),
        SphericalProjection(field_of_view=pcd.fov),
        DelaunayInterpolation(),
        lazy_disk_cache_config=cfg,
    )
    out = gen.generate(features=["range"])
    img = np.asarray(out["range"])
    assert img.shape == (200, 200)
    assert np.isfinite(img).mean() > 0.5         # ~0.96 finite in the verified run
    assert np.nanmin(img) > 0                    # range is a positive distance
    print("OK", img.shape, float(np.nanmin(img)), float(np.nanmax(img)))
```
Verified output: `shape (200, 200)`, dtype `float64`, finite-fraction `0.959`, min `8.748`, max `11.262` (consistent with the ~10 m synthetic surface). `[VERIFIED: runtime execution]`

Notes for the smoke task:
- **`PointCloudData(xyz=<Nx3 float64>)` is the whole constructor** you need — `r`, `spher`, `fov`, `nbPoints` all derive from `xyz`. Full signature: `PointCloudData(self, /, xyz=None, **kwargs: Unpack[PointCloudDataKW])` `[VERIFIED: inspect.signature]`. Using `rhv2xyz` to synthesize from angles gives a healthy 2D FoV extent (a flat wall in xyz yields a near-degenerate horizontal span — avoid).
- The `range` feature is literally `return pcd.r` (`features/base_features.py:18`) — cheapest correct feature (D-10). `[VERIFIED: read]`
- `DelaunayInterpolation()` exercises the **GSEGUtils `DiskBackedStore`** triangulation cache — so the smoke *also* covers the DEP-02/SC2 GSEGUtils disk-cache path. `[VERIFIED: runtime execution]`
- Run via `uv run python scripts/smoke_pipeline.py` (D-09). Because pc2img isn't currently self-installed in `.venv`, this only works after `uv sync` installs the project (part of DEP-04) — or with `PYTHONPATH=src`. Sequence the smoke task **after** the `uv.lock`/`uv sync` task so `uv run` resolves `pc2img` itself.

### 🔴 Blocker: default `lazy_disk_cache_config=None` is not coerced
`PointCloudImageGenerator.__init__` declares `lazy_disk_cache_config: LazyDiskCacheConfigLike = None`, where the runtime type is `Annotated[LazyDiskCacheConfig, BeforeValidator(coerce_lazy_cfg)]`. But **pydantic `@validate_call` does not validate default argument values**, so the `None` default bypasses `coerce_lazy_cfg` and reaches `FeatureManager` → `DiskBackedImageStore(config=None)`, raising:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for DiskBackedImageStore.__init__
config  Input should be a dictionary or an instance of LazyDiskCacheConfig [input_value=None]
```
`[VERIFIED: runtime execution]`. This is a **latent public-API bug** (any caller relying on the default hits it, including `scripts/v2.0/01_manual_test_PointCloudImageGenerator.py` which passes no config). Options for the planner:
- **Smoke script (this phase):** pass an explicit `LazyDiskCacheConfig(cache_path=<tmpdir>)` — clean, CI-friendly, needs the temp dir anyway. **Recommended.** No source change required to satisfy SC1.
- **Optional source fix (borderline scope):** add `validate_default=True` to the `@validate_call`, or handle `None` in `FeatureManager`/`DiskBackedImageStore`. This is arguably QUAL/BUG territory (Phase 4/5). Recommend logging it as a pending todo rather than folding into Phase 2 unless the owner wants the default path fixed now.

## GSEGUtils Reality (DEP-02 / SC2)

Import surface in `src/pc2img/` `[VERIFIED: grep src/]`:
- `GSEGUtils.lazy_disk_cache` → `LazyDiskCache`, `LazyDiskCacheConfig`, `LazyDiskCacheKw`, `DiskBackedNDArray`, `DiskBackedStore` (core.py, interpolation.py, image_cache, features/manager.py, tiled_generator.py)
- `GSEGUtils.config` → `get_defaults`, `CacheDefaults`
- `GSEGUtils.base_types` → `Vector_Bool_T`, `Array_Nx2_Float_T`, `Array_3x3_T`, `Array_4x4_T`, `Array_Nx3_T` (projection.py)

Against `/scratch/30_GSEGUtils/MIGRATION-v1.0.md` (BC-GSEG-001..005):

| GSEGUtils BC | Change | Affects pc2img? |
|--------------|--------|-----------------|
| BC-GSEG-001 on-disk format | `DiskBackedStore` now `.npy` + `.meta.json` (not pickle); refuses legacy `.pkl` with `KeyError` `[CITED: BC-GSEG-001]` | **No source change.** pc2img creates *fresh* `DiskBackedStore` instances at runtime (triangulation cache); caches materialize in the new format. No legacy `.pkl` to migrate. Runtime-proven by the smoke (Delaunay). |
| BC-GSEG-002 `source_range` kwarg on `normalize_uint8/16`, `linear_map_dtype` `[CITED: BC-GSEG-002]` | **No.** pc2img does not import GSEGUtils validators; its own `convert_to_image`/`to_gray` (`util.py`) do normalization. `[VERIFIED: grep src/]` |
| BC-GSEG-003 public angle helpers | additive | No. |
| BC-GSEG-005 memmap streaming / lock-free singleton | behaviour-preserving | No. (Note: adds `psutil` as a GSEGUtils runtime dep — pulled transitively, appears in the lock.) |

**Casing gotcha confirmed:** distribution name is `gsegutils` (what pip/uv installs), importable package is `GSEGUtils` (capitalized). pc2img imports use the capitalized form correctly; the `pyproject.toml` requirement keeps `GSEGUtils` capitalized (D-02) — pip normalizes case for *resolution* regardless. `[VERIFIED: PyPI returns 200 for both `gsegutils` and `GSEGUtils`; import works capitalized]`

SC2 is runtime-proven for the exercised surface: the successful smoke run imports the entire `pc2img` module graph (core → strategies → features → image_cache → tiled_generator), so every `GSEGUtils.*` import above resolves and the `DiskBackedStore`/`LazyDiskCache` cache path executes.

## Standard Stack

This phase changes **declarations and lockfiles**, not runtime libraries. The "stack" here is the dependency + tooling surface.

### Core dependency changes (`pyproject.toml`)
| Item | Current state | Target | Provenance |
|------|---------------|--------|------------|
| `pchandler` | commented out (`# "pchandler[cuda12] ~= 1.0"` etc.) | `"pchandler ~= 2.1"` in `[project.dependencies]` | `[VERIFIED: npm-equivalent PyPI 2.1.0]` |
| `GSEGUtils` | commented out (`# "GSEGUtils ~= 0.2"`) | `"GSEGUtils ~= 0.5"` (capitalized) | `[VERIFIED: PyPI 0.5.2]` |
| `numpy` | `numpy ~= 2.0` (already correct on develop-gsd) | keep `numpy ~= 2.0` (D-03) | `[VERIFIED: intersects pchandler <2.4]` |
| duplicate `joblib` | `joblib ~= 1.5` AND `joblib ~= 1.3` both present | leave for QUAL-01 (Phase 4) unless trivially collapsed here | `[VERIFIED: read pyproject.toml]` |
| `cuda12` extra | bare `cudf-cu12 == 25.4.*` … | `pchandler[cuda12]` + keep pin set (D-04) | `[CITED: pchandler pyproject cuda12]` |
| `cuda11` extra | partial (`cudf-cu11`, `cuml-cu11` only) | `pchandler[cuda11]` (symmetric, fills gaps) | `[CITED: pchandler pyproject cuda11]` |

pchandler's own cuda extras bring `geopandas ~= 1.0`, `cudf`, `cuspatial`, `cuproj`, `cuml`, `dask-cudf` (all `25.4.*`) `[CITED: /scratch/41_pchandler/pyproject.toml:119-122]` — wiring `pchandler[cuda12]` inherits these.

### Tooling deps → PEP 735 groups (D-08)
Move out of `[project.optional-dependencies]` into `[dependency-groups]`:
```toml
[dependency-groups]
dev = ["black ~= 23.10", "pytest", "memory_profiler"]   # or ruff later (Phase 3/4 deferred)
doc = ["sphinx ~= 5.1"]
```
Keep `cuda11`/`cuda12` as `[project.optional-dependencies]` extras (they are shippable package capabilities). `matplotlib` stays out of scope here (QUAL-01 moves it to an extra in Phase 4).

**Installation / bootstrap (target dev workflow):**
```bash
uv sync                 # installs project + runtime deps + `dev` group (default)
uv sync --group doc     # add the doc group when building sphinx docs
uv run python scripts/smoke_pipeline.py   # SC1 evidence
uv run pytest           # once tests exist (Phase 3)
uv lock                 # regenerate the lock after any dependency edit
```

**Version verification (done this session):**
- `pchandler` → PyPI `2.1.0`, requires-python `<3.13,>=3.12`, `numpy<2.4,>=2.0`, `GSEGUtils~=0.5`. `[VERIFIED: pypi.org/pypi/pchandler/json]`
- `GSEGUtils` → PyPI `0.5.2`, requires-python `<3.13,>=3.12`, `numpy<2.4,>=2.0`. `[VERIFIED: pypi.org/pypi/gsegutils/json]`
- Local editable installs are `.post2` (setuptools_scm post-tag) — clean PyPI resolution lands `2.1.0` / `0.5.2` (one release each). Functionally equivalent (both post-migration v2.x/0.5.x); see Assumptions A1.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `uv.lock` native workflow | `uv pip compile` → `requirements.txt` | Loses universal cross-platform lock + `uv sync` project semantics; D-05 chose native. Don't. |
| PEP 735 groups | keep dev/doc as extras (pchandler style) | Extras leak into wheel metadata as installable capabilities; D-08 chose correct modeling. |
| Locking GPU extras (D-06) | leave cuda unlocked (owner-only extras) | D-06 chose fuller reproducibility; costs a network-bound RAPIDS resolution at lock time (see risk). |

## Package Legitimacy Audit

Both siblings are first-party GSEG (ETH Zurich) packages under the `gseg-ethz` GitHub org — the same owner as this project. Not slopsquat candidates; owner-controlled per D-13.

| Package | Registry | Age / Releases | Source Repo | Verdict | Disposition |
|---------|----------|----------------|-------------|---------|-------------|
| `pchandler` | PyPI `2.1.0` | 1 release (freshly published) | github.com/gseg-ethz/PCHandler | OK (owner-identity verified) | Approved — pin `~= 2.1` |
| `GSEGUtils` (dist `gsegutils`) | PyPI `0.5.2` | 1 release | github.com/gseg-ethz/GSEGUtils | OK (owner-identity verified) | Approved — pin `~= 0.5` (capitalized) |

**Packages removed due to [SLOP]:** none.
**Packages flagged [SUS]:** none. (A naive heuristic might flag "new / single-release / low-downloads", but identity is verified: PyPI `project_urls` point to the `gseg-ethz` org that owns this repo, and the installed on-disk source at `/scratch/41_pchandler` + `/scratch/30_GSEGUtils` matches. No planner checkpoint needed.)
**GPU extras** (`cudf-cu12`, `cuspatial-cu12`, `cuproj-cu12`, `cuml-cu12`, `dask-cudf-cu12`, cuda11 equivalents, `geopandas`): RAPIDS packages from `pypi.nvidia.com`, `== 25.4.*` — inherited via `pchandler[cuda12]`. Not resolved/installed this session (network-heavy); pinned exactly as pchandler declares. `[CITED: pchandler pyproject]`

## Architecture Patterns

### uv Reproducibility Tooling (D-05, D-06, D-08)

**PEP 735 dependency-groups + default behavior** `[CITED: docs.astral.sh/uv/concepts/projects/dependencies, pydevtools.com dependency-groups]`:
- `uv sync` with no flags installs project deps **plus the `dev` group** (dev is special-cased). No other group by default.
- `uv sync --group doc` adds the `doc` group; `--no-default-groups` / `--no-dev` exclude dev; `--all-groups` for everything.
- `default-groups` is configurable via `[tool.uv] default-groups = [...]` if the `dev` default ever needs changing (not needed here — D-08 wants `dev` by default).
- Groups are never published to PyPI and never installed by `pip install pc2img` — correct for repo tooling (D-08 rationale).

**Explicit nvidia index for GPU extras (D-06)** `[CITED: docs.astral.sh/uv/concepts/indexes, docs.astral.sh/uv/guides/integration/pytorch]`:
```toml
[[tool.uv.index]]
name = "nvidia"
url = "https://pypi.nvidia.com"
explicit = true          # index used ONLY for packages that name it in [tool.uv.sources]

[tool.uv.sources]
# each RAPIDS package must be pinned to the nvidia index individually:
cudf-cu12     = { index = "nvidia" }
cuspatial-cu12 = { index = "nvidia" }
cuproj-cu12   = { index = "nvidia" }
cuml-cu12     = { index = "nvidia" }
dask-cudf-cu12 = { index = "nvidia" }
# … and the cuda11 (-cu11) equivalents
```
Key mechanics: `explicit = true` means the nvidia index is consulted **only** for packages that explicitly reference it in `[tool.uv.sources]`; everything else resolves from PyPI. So each cuda package name must appear in `[tool.uv.sources]` with `{ index = "nvidia" }` — otherwise uv won't find them (they're not on PyPI). `[CITED: docs.astral.sh/uv/concepts/indexes]`

**Caveat / discretion note:** the RAPIDS packages come from `pchandler[cuda12]`, so they are transitive to pc2img. `[tool.uv.sources]` pins apply to the *resolving project's* declarations; pinning transitive-from-pchandler packages to the nvidia index in pc2img's `pyproject.toml` should work because uv resolves the whole graph against configured indexes, but this is worth an explicit resolution test in the plan. If it misbehaves, the fallback is to name the RAPIDS packages directly in pc2img's `cuda12`/`cuda11` extras (alongside `pchandler[cuda12]`) so the `[tool.uv.sources]` pins bind to first-party declarations. `[ASSUMED — verify during `uv lock`]`

**setuptools_scm + uv (D-05)** `[CITED: docs.astral.sh/uv + PEP 517 knowledge]`:
- With a `[build-system]` table present, uv treats the project as a **package** and builds it (editable) on `uv sync`. **No `[tool.uv] package = true` needed** — it's inferred from `[build-system]`. Only add `package = false` to opt *out*, which we don't want.
- setuptools_scm derives the version from git at build time; the working tree has tag `v2.0.0a5` (`git describe` → `v2.0.0a5-50-gb1d8e8b`), so builds produce a valid post-release version. `.git` is present and accessible to the isolated build. `[VERIFIED: git describe]`
- Gotcha to watch: uv's build isolation must see `.git`. Building from the project root (the normal `uv sync` path) satisfies this. If a plan ever does `uv build` from a copied/exported tree without `.git`, setuptools_scm falls back to `0.0.0`-style versions — not relevant to `uv sync` here.

### Recommended file layout (discretion)
```
pc2img/
├── pyproject.toml          # deps re-enabled + pinned; [dependency-groups]; [tool.uv.index]/[tool.uv.sources]
├── uv.lock                 # NEW — committed universal lock (D-05); NOT gitignored (confirmed)
├── CONTRIBUTING.md         # NEW — uv bootstrap workflow (D-07)
├── scripts/
│   └── smoke_pipeline.py   # NEW — synthetic single-cloud SC1 evidence (D-09/D-10)
└── third_party/            # gitignored source-investigation symlinks (D-12, unchanged)
```

### Anti-Patterns to Avoid
- **Committing `[tool.uv.sources]` pointing at local `/scratch` paths** — forbidden by D-12. Local editable override stays an opt-in, non-committed `uv pip install -e` step.
- **Trying to "fix" FoVTree/`to_py4dgeo`/Csv-Las in source** — there is nothing to fix; the honest deliverable is an audit attestation.
- **Relying on the `PointCloudImageGenerator` default `None` cache config** — it raises. Always pass an explicit `LazyDiskCacheConfig` in the smoke.
- **Editing pchandler/GSEGUtils** to accommodate pc2img — D-13 requires owner discussion first.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-platform reproducible lock | custom `requirements.txt` per-OS | `uv.lock` via `uv lock` (D-05) | Universal resolution, hash-pinned, `uv sync` restores exactly |
| GPU dep set for pc2img | re-list RAPIDS packages | `pchandler[cuda11/12]` (D-04) | Inherits pchandler's maintained, gap-filled set |
| Synthetic point cloud | hand-rolled arrays that miss `r`/`spher`/`fov` | `PointCloudData(xyz=...)` + `rhv2xyz` | Derives all needed properties; matches real API |
| "Is the break relevant?" guesswork | assume the MIGRATION list applies | grep the actual call sites | 3/3 named breaks turned out to have zero call sites |

**Key insight:** the MIGRATION-v1.0 BC list is pchandler's *whole* public-surface change record; only the subset pc2img actually calls matters. Grepping first turned a "fix three semantic breaks" task into "attest three non-applicable breaks + prove the one surface you do use."

## Runtime State Inventory

> This phase re-declares dependencies and stands up a lock; it does not rename stored keys or migrate datastores. Included for completeness.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | GSEGUtils `DiskBackedStore` caches are runtime-ephemeral (temp dirs). BC-GSEG-001 refuses legacy `.pkl`, but pc2img writes fresh caches only. | None — no persisted legacy caches in the repo. |
| Live service config | None — library, no services. | None. |
| OS-registered state | None. | None. |
| Secrets/env vars | None — `src/pc2img/` reads no env vars (confirmed in STACK.md; no `os.environ`). | None. |
| Build artifacts | `.venv/` has pchandler/GSEGUtils editable-installed from `/scratch`; pc2img itself is **not** installed in `.venv`. After `uv sync` the env is rebuilt from `uv.lock` and pc2img is installed. `third_party/` symlinks stay (gitignored). | `uv sync` rebuilds; smoke via `uv run` works only post-sync. |

## Common Pitfalls

### Pitfall 1: Smoke fails on the default `None` cache config
**What goes wrong:** `PointCloudImageGenerator(pcd, res, proj, interp)` with no `lazy_disk_cache_config` raises `ValidationError` (`config` = `None`).
**Why:** pydantic `@validate_call` skips default-value validation, so `coerce_lazy_cfg(None)` never runs.
**How to avoid:** pass `lazy_disk_cache_config=LazyDiskCacheConfig(cache_path=<tmpdir>)` in the smoke. `[VERIFIED: runtime]`
**Warning signs:** `Input should be a dictionary or an instance of LazyDiskCacheConfig [input_value=None]`.

### Pitfall 2: Degenerate FoV from a flat synthetic cloud
**What goes wrong:** a planar wall in `xyz` yields a near-zero horizontal angular span → skewed/blank raster.
**Why:** spherical projection normalizes by FoV extent; a tiny span collapses the image.
**How to avoid:** synthesize from spherical angles via `rhv2xyz` over a real `(h, v)` range (as in the verified snippet), not a flat xy plane. `[VERIFIED: runtime — first flat-wall attempt gave ratio 0.01]`

### Pitfall 3: `uv run smoke` before `uv sync` installs pc2img
**What goes wrong:** `ModuleNotFoundError: No module named 'pc2img'`.
**Why:** pc2img is not currently installed in `.venv` (only the siblings are).
**How to avoid:** sequence the smoke task after the `uv.lock`/`uv sync` task; `uv sync` installs the project editable. `[VERIFIED: import failed until PYTHONPATH=src set]`

### Pitfall 4: nvidia index offline at lock time (D-06)
**What goes wrong:** `uv lock` needs to reach `pypi.nvidia.com` to resolve RAPIDS `25.4.*`; offline or flaky access stalls the lock.
**Why:** D-06 pulls the full GPU surface into the universal lock.
**How to avoid:** run `uv lock` with network access; if impractical, invoke the D-06 discretion fallback (flag to owner; consider scoping GPU out of the lock). `[CITED: D-06 discretion]`

## Code Examples

The runtime-verified smoke construction is in **§Smoke Path** above. `pyproject.toml` fragments are in **§Standard Stack** and **§uv Reproducibility Tooling**.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| dev/doc as `[project.optional-dependencies]` extras | PEP 735 `[dependency-groups]` | PEP 735 accepted 2024; uv full support | Tooling deps no longer leak into wheel metadata (D-08) |
| `pip install -r requirements.txt` | `uv sync` from committed `uv.lock` | uv project workflow | Universal, hashed, exact reproduction (D-05) |
| `--extra-index-url` for nvidia (old pc2img comment) | `[[tool.uv.index]] explicit=true` + `[tool.uv.sources]` | uv indexes | Deterministic per-package index binding (D-06) |
| pchandler 1.0 (`~= 1.0`, git+ssh pins) | pchandler 2.1 from public PyPI | this milestone | Clean `pip install`, no git/ssh (D-01) |

**Deprecated/outdated in current `pyproject.toml`:** commented `pchandler[cuda12] ~= 1.0` and `git+ssh` line, `GSEGUtils ~= 0.2`, placeholder `keywords = ["one","two"]`, `documentation = "https://google.com"`, DeSpAn leftovers. Metadata cleanup is **QUAL-01 (Phase 4)** except where re-enabling deps forces a touch — don't expand scope here.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Clean PyPI resolution of `pchandler 2.1.0` / `GSEGUtils 0.5.2` is behavior-equivalent to the local `.post2` editable installs the smoke ran against | Standard Stack | LOW — both are post-migration v2.x/0.5.x; `.post2` is git-commit drift past the tag. Planner's `uv sync` in a throwaway env (SC3) re-proves the exact resolved versions. |
| A2 | Pinning RAPIDS packages (transitive from `pchandler[cuda12]`) to the nvidia index via pc2img's `[tool.uv.sources]` resolves correctly | uv Reproducibility Tooling | MEDIUM — `[tool.uv.sources]` on transitive-only names may need the packages named in pc2img's own extras. Verified only by running `uv lock` (D-06). Fallback documented. |
| A3 | No `[tool.uv] package = true` is needed (inferred from `[build-system]`) | uv Reproducibility Tooling | LOW — standard uv behavior; if `uv sync` doesn't build the project, add `package = true`. |

**Everything else in this research was VERIFIED (runtime/PyPI/grep) or CITED (official docs / migration specs).**

## Open Questions (RESOLVED)

1. **Fix the `None`-config coercion now, or defer?**
   - What we know: it's a real public-API bug on the default path, blocking any config-less caller.
   - What's unclear: whether the owner wants it fixed in Phase 2 (packaging) or Phase 4/5 (quality/bugs).
   - Recommendation: smoke passes an explicit config (no fix needed for SC1); log a pending todo for the default-path fix. Do not expand Phase 2 scope without owner sign-off.
   - **RESOLVED:** deferred out of Phase 2. Plan 02-03 drives the smoke with an explicit `LazyDiskCacheConfig(cache_path=<tmpdir>)` (no fix needed for SC1) and records the default-path coercion bug as a Phase 4/5 pending todo. Scope unchanged.

2. **BC-PCH-008 attestation depth** — is a grep-attest doc/assertion enough, or does the owner want the example `scripts/v2.0/03_tiled_image_gen.py` FoVTree usage validated too?
   - Recommendation: attest non-use in `src/`; optionally note the example script already matches the new `build_from_tiles` shape. Full tiled/FoVTree coverage is TEST-05 (Phase 5).
   - **RESOLVED:** grep-attest is sufficient for Phase 2. Plan 02-03 T2 produces `docs/pchandler-2x-break-audit.md` attesting zero `FoVTree`/`to_py4dgeo`/Csv/Las call sites in `src/pc2img/`; exhaustive tiled/FoVTree coverage stays in TEST-05 (Phase 5).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | DEP-04 lock/sync | ✓ | 0.11.26 | — |
| Python 3.12 | whole project | ✓ | 3.12 (`.venv`) | — |
| `pchandler` (PyPI) | DEP-01/03 | ✓ | 2.1.0 | local `third_party/` editable (dev-only, D-12) |
| `GSEGUtils` (PyPI) | DEP-02/03 | ✓ | 0.5.2 | local `third_party/` editable |
| PyPI network | `uv lock`/`uv sync` | ✓ (verified reachable) | — | — |
| `pypi.nvidia.com` | D-06 GPU-extra lock | ✗ (not tested this session) | — | scope GPU out of lock / flag owner (D-06 discretion) |
| git + tag `v2.0.0a5` | setuptools_scm version | ✓ | describe `v2.0.0a5-50-g…` | — |

**Missing with no fallback:** none blocking. **Missing with fallback:** nvidia index reachability at lock time (D-06 fallback documented).

## Validation Architecture

> nyquist_validation is enabled (config.json). This is a dependency/packaging phase; validation is mostly clean-install + smoke, not unit tests. No test framework exists yet (Phase 3 stands up pytest scoping).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | none yet — pytest arrives in Phase 3 (TEST-01). This phase's proof is a runnable **script** (D-09), promotable to a pytest smoke in Phase 3. |
| Config file | none (`[tool.pytest]` absent) |
| Quick run command | `uv run python scripts/smoke_pipeline.py` (exit 0 = pass) |
| Full suite command | n/a this phase |

### Success Criterion → Proof Map
| SC / Req | Observable proof | Type |
|----------|------------------|------|
| **SC1 / DEP-01** | `uv run python scripts/smoke_pipeline.py` exits 0; asserts `range` raster shape `(H,W)`, finite-fraction > threshold, `min > 0`. | **Runtime-provable** (verified this session). |
| DEP-01 named breaks | Documented negative audit: `grep -r 'FoVTree\|to_py4dgeo\|Csv\|Las' src/` returns nothing → attest non-use. Optional inline assertion in the audit doc. | **Audit-only** (breaks are off-path/absent). |
| **SC2 / DEP-02** | Smoke run imports the full `pc2img` graph (all `GSEGUtils.*` resolve) and Delaunay exercises `DiskBackedStore` — completing the run proves it. Casing: `import GSEGUtils` works; dist is `gsegutils`. | **Runtime-provable** (verified). |
| **SC3 / DEP-03** | In a **throwaway env** (`uv venv` in a temp dir, no `third_party/` symlinks), `uv sync` + `uv run python -c "import pc2img"` succeeds; `pyproject.toml` shows `pchandler ~= 2.1` + `GSEGUtils ~= 0.5` uncommented; numpy resolves `>=2.0,<2.4`. | **Runtime-provable** (must run clean-room; not run this session — needs a fresh env to avoid mutating `.venv`). |
| **SC4 / DEP-04** | `uv.lock` committed; `CONTRIBUTING.md` documents `uv sync` / `uv run` / `uv lock`; `uv sync` from the lock reproduces the env. | **Runtime-provable** (lock round-trip) + doc audit. |

### Sampling Rate
- **Per task commit:** `uv run python scripts/smoke_pipeline.py` once it exists + syncs.
- **Phase gate:** clean-room `uv sync` (SC3) green + smoke green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `scripts/smoke_pipeline.py` — SC1 evidence (D-09/D-10). Must pass explicit `LazyDiskCacheConfig`.
- [ ] `uv.lock` — committed universal lock (D-05).
- [ ] `CONTRIBUTING.md` — uv workflow (D-07).
- [ ] Break-audit attestation (doc or asserted script) for BC-PCH-007/008 + Csv/Las non-use (D-11).
- [ ] No pytest framework install this phase (Phase 3 owns it).

## Security Domain

> `security_enforcement` enabled, ASVS L1. This is a packaging/dependency phase; the security-relevant surface is **supply chain**, not app auth/crypto.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture / Supply chain | yes | Pin to public-PyPI, owner-verified packages; commit a hash-locked `uv.lock`; no `git+ssh`/local-path sources committed (D-12) |
| V5 Input Validation | partial | pydantic `@validate_call` at API boundaries (existing); not changed here |
| V6 Cryptography | no | none introduced |
| V2/V3/V4 Auth/Session/Access | no | library, no auth surface |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Dependency confusion / slopsquat on `pchandler`/`gsegutils` | Spoofing/Tampering | Identity-verified against `gseg-ethz` org + on-disk source match; `uv.lock` hash-pins exact artifacts (§Package Legitimacy Audit) |
| Untrusted index for GPU extras | Tampering | `[[tool.uv.index]] explicit=true` binds RAPIDS names to the official `pypi.nvidia.com` only; PyPI stays default for everything else |
| Legacy pickle cache load (GSEGUtils `DiskBackedStore`) | Tampering | BC-GSEG-001 replaced pickle with `.npy`+JSON and refuses `.pkl`; pc2img writes fresh caches only — no untrusted-pickle deserialization path introduced |

## Sources

### Primary (HIGH confidence)
- Runtime execution against `pchandler==2.1.0.post2` / `GSEGUtils==0.5.2.post2` in `.venv` — full `PointCloudImageGenerator.generate` smoke, `PointCloudData` constructor probe, FoV attribute probe, `None`-config repro.
- `grep` audit of `src/pc2img/` + `scripts/` — FoVTree/to_py4dgeo/Csv/Las call sites, GSEGUtils/pchandler import surfaces.
- `/scratch/41_pchandler/MIGRATION-v1.0.md` (BC-PCH-001..015) and `/scratch/30_GSEGUtils/MIGRATION-v1.0.md` (BC-GSEG-001..005).
- `/scratch/41_pchandler/pyproject.toml`, `/scratch/31_pc2img/pyproject.toml`.
- PyPI JSON API — `pchandler` 2.1.0, `gsegutils`/`GSEGUtils` 0.5.2 (version, requires-python, requires-dist, project_urls).

### Secondary (MEDIUM confidence)
- docs.astral.sh/uv/concepts/projects/dependencies — dependency-groups, `uv sync` default `dev`.
- docs.astral.sh/uv/concepts/indexes — `explicit = true`, `[tool.uv.sources]` index pinning.
- docs.astral.sh/uv/guides/integration/pytorch — explicit-index recommendation pattern.
- pydevtools.com dependency-groups / PEP 735 explainer.

### Tertiary (LOW confidence)
- A2 assumption on transitive RAPIDS index pinning — verify at `uv lock`.

## Metadata

**Confidence breakdown:**
- Semantic-break reality: HIGH — every named break grep-audited to zero call sites; exercised surface runtime-proven.
- Smoke path: HIGH — full pipeline executed, finite output captured, blocker reproduced.
- Package/PyPI: HIGH — versions + metadata pulled live from PyPI.
- uv syntax: MEDIUM-HIGH — official docs cited; GPU-index transitive pinning (A2) unverified against a real `uv lock`.
- GPU/D-06 offline resolution: LOW-MEDIUM — not exercised; risk + fallback flagged.

**Research date:** 2026-07-09
**Valid until:** 2026-08-08 (stable — packaging + owner-controlled sibling releases; re-check if pchandler/GSEGUtils publish new PyPI releases or uv changes lock/index syntax).
