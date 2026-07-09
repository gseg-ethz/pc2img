# Phase 2: Dependency Adaptation & Reproducible Environment - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 5 (1 code-bearing, 2 config, 2 docs/generated)
**Analogs found:** 3 with in-repo analogs / 5 total

> **Phase nature:** This is a dependency/packaging/reproducibility phase. Most
> deliverables are **config/doc/lockfile** units where the correct unit of work is
> a *config diff* or *doc authoring*, not a source-code excerpt. Only
> `scripts/smoke_pipeline.py` is genuinely code-bearing. Excerpts below are given
> as code only where the exact text is load-bearing; config files get an
> anchor-to-current-structure treatment instead of forced code blocks.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/smoke_pipeline.py` | script (driver) | request-response (drive pipeline → assert) | `scripts/v2.0/01_manual_test_PointCloudImageGenerator.py` + verified snippet in 02-RESEARCH.md §Smoke Path | role-match (best available) |
| `pyproject.toml` | config (build metadata) | declaration/transform | current `pyproject.toml` (edit-in-place) + `/scratch/41_pchandler/pyproject.toml` (layout reference) | exact (self) + reference |
| `uv.lock` | config (generated lockfile) | batch (resolver output) | none — `uv lock` generates it | no analog (tool-generated) |
| `CONTRIBUTING.md` | doc | n/a | none in repo (`README.rst` is a 9-byte stub) | no analog (author from RESEARCH workflow block) |
| Break-audit attestation (D-11) | doc or asserted comment | n/a | none — grep-attest content in 02-RESEARCH.md §Semantic-Break Reality | no analog (author from RESEARCH) |

## Pattern Assignments

### `scripts/smoke_pipeline.py` (script, request-response) — the one code-bearing file

**Primary analog:** the runtime-verified snippet in `02-RESEARCH.md` §Smoke Path
(lines 90-124) — this is the authoritative shape, already executed against
`pchandler==2.1.0.post2` / `GSEGUtils==0.5.2.post2`. **Copy this, do not
re-derive it.**

**Secondary analog (project script conventions):**
`scripts/v2.0/01_manual_test_PointCloudImageGenerator.py` — shows the established
driver shape a repo script follows (module-name logger, `TemporaryDirectory`
cache dir, `SphericalProjection`/`DelaunayInterpolation`, `generate(features=...)`,
`__main__` guard). **Diverge from it in three ways** the research flagged:
synthetic in-code cloud (not `Ply.load` of an external file), no matplotlib/
memory_profiler, and an **explicit** `LazyDiskCacheConfig`.

**Import pattern to copy** (from the verified RESEARCH snippet — canonical import
paths, all resolve today):
```python
import tempfile
from pathlib import Path
import numpy as np
from pchandler import PointCloudData
from pchandler.geometry.coordinates import rhv2xyz
from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig
from pc2img.core import PointCloudImageGenerator
from pc2img.strategies import SphericalProjection, DelaunayInterpolation
```
These match the analog script's imports (`analog lines 12-19`) except the analog
also pulls `matplotlib`, `memory_profiler`, `GSEGUtils.logging_setup`,
`pchandler.data_io.Ply` — **omit all of those** (visualization / file-load / profiling
are not part of a CI-friendly smoke).

**Cache-dir + generator-construction pattern** (from analog lines 60-67, but with
the RESEARCH blocker fix applied — the load-bearing difference):
```python
with tempfile.TemporaryDirectory() as td:
    cfg = LazyDiskCacheConfig(cache_path=Path(td))          # REQUIRED — see blocker
    gen = PointCloudImageGenerator(
        pcd, (200, 200),
        SphericalProjection(field_of_view=pcd.fov),
        DelaunayInterpolation(),
        lazy_disk_cache_config=cfg,                          # analog OMITS this → raises
    )
    out = gen.generate(features=["range"])
```
> **Load-bearing divergence from the analog:** the analog script (line 67) calls
> `PointCloudImageGenerator(pcd, resolution, proj, interp)` with **no**
> `lazy_disk_cache_config`. Per 02-RESEARCH.md §Blocker (lines 132-140), the
> `None` default is **not** coerced by pydantic `@validate_call` and raises
> `ValidationError: config Input should be a dictionary or an instance of
> LazyDiskCacheConfig [input_value=None]`. The smoke MUST pass an explicit
> `LazyDiskCacheConfig(cache_path=<tmpdir>)`. Do **not** copy the analog's
> config-less call. (Source fix is deferred — log as pending todo, per Open
> Question 1.)

**Synthetic-cloud construction** (from RESEARCH snippet lines 101-107 — replaces
the analog's `Ply.load(PCD_PATH)` at line 53; deterministic, no external file per
D-10). Use `rhv2xyz` from spherical angles, **not** a flat xy plane (Pitfall 2 —
degenerate FoV):
```python
rng = np.random.default_rng(42)                 # deterministic seed (D-10)
n = 8000
h = rng.uniform(-0.30, 0.30, n)                 # horizontal angle (rad)
v = rng.uniform(1.20, 1.80, n)                  # vertical/polar angle (rad)
r = 10.0 + 0.5 * np.sin(4 * h) + 0.3 * rng.standard_normal(n)
xyz = rhv2xyz(np.column_stack([r, h, v])).astype(np.float64)
pcd = PointCloudData(xyz=xyz)                    # r / spher / fov derived from xyz
```
`range` is the cheapest correct feature — it is literally `return pcd.r`
(`src/pc2img/features/base_features.py:17-18`, `class RangeFeature`,
`regex_pattern = ^range$`).

**Assertion / exit pattern** (from RESEARCH snippet lines 119-122 — this is the SC1
observable proof; exit 0 = pass):
```python
    img = np.asarray(out["range"])
    assert img.shape == (200, 200)
    assert np.isfinite(img).mean() > 0.5         # ~0.96 finite in the verified run
    assert np.nanmin(img) > 0                    # range is a positive distance
    print("OK", img.shape, float(np.nanmin(img)), float(np.nanmax(img)))
```
Verified output to expect: shape `(200, 200)`, finite-fraction `0.959`, min
`8.748`, max `11.262`.

**Structural convention to copy from the analog** (not the content): module-level
`logger = logging.getLogger(__name__.split(".")[0])` (analog line 26) and the
`def main(): ... if __name__ == "__main__": main()` guard (analog lines 51/93-94).
Keep the smoke a plain `main()` + `__main__` guard; drop the `@profile` decorator.

**Sequencing constraint (Pitfall 3):** `uv run python scripts/smoke_pipeline.py`
only works **after** `uv sync` installs `pc2img` into the env (it is not currently
self-installed in `.venv`). Plan the smoke task **after** the `uv.lock`/`uv sync`
task, or run with `PYTHONPATH=src`.

---

### `pyproject.toml` (config, edit-in-place) — dep re-enable + PEP 735 + uv index

**Analog:** the file itself (current structure, read below) is the edit target;
`/scratch/41_pchandler/pyproject.toml` is the **layout reference** for the cuda
extras and `[dependency-groups]`-vs-extras split. Unit of work = **config diff**,
not code excerpt.

**Current structure to edit** (`/scratch/31_pc2img/pyproject.toml`):
- `[build-system]` lines 1-3 — **keep unchanged** (`setuptools` + `setuptools_scm`;
  D-05 keeps the build backend). Matches pchandler lines 1-3 exactly.
- `[project].dependencies` lines 18-32 — the **commented-out** `pchandler` (19-20)
  and `GSEGUtils` (21) lines are the DEP-03 target. Uncomment/replace with
  `"pchandler ~= 2.1"` and `"GSEGUtils ~= 0.5"` (capitalized, D-02). `numpy ~= 2.0`
  (line 23) stays as-is (D-03). Note the **duplicate `joblib`** (lines 22 + 25:
  `~= 1.5` and `~= 1.3`) — leave for QUAL-01/Phase 4 unless trivially collapsed
  (RESEARCH §Standard Stack).
- `[project.optional-dependencies]` lines 52-68 — **restructure**: move `doc`
  (line 53) and `dev` (54-58) **out** to a new `[dependency-groups]` table (D-08,
  PEP 735); **keep** `cuda12` (59-63) and `cuda11` (64-68) as extras but rewire
  their bodies to `pchandler[cuda12]` / `pchandler[cuda11]` (D-04).

**PEP 735 target** (from 02-RESEARCH.md §Standard Stack lines 180-184 — this is the
new table, NOT an existing analog):
```toml
[dependency-groups]
dev = ["black ~= 23.10", "pytest", "memory_profiler"]
doc = ["sphinx ~= 5.1"]
```

**cuda extras rewire** — reference pchandler's own cuda extras for the inherited
set. `/scratch/41_pchandler/pyproject.toml:119-122`:
```toml
cuda11 = ["geopandas ~= 1.0", "cudf-cu11 == 25.4.*", "cuspatial-cu11 == 25.4.*", "cuproj-cu11 == 25.4.*",
	"cuml-cu11 == 25.4.*", "dask-cudf-cu11 == 25.4.*", ]
cuda12 = ["geopandas ~= 1.0", "cudf-cu12 == 25.4.*", "cuspatial-cu12 == 25.4.*", "cuproj-cu12 == 25.4.*",
	"cuml-cu12 == 25.4.*", "dask-cudf-cu12 == 25.4.*", ]
```
pc2img's extras become `pchandler[cuda12]` / `pchandler[cuda11]` (inherits the
above), per D-04. The old pc2img cuda bodies (lines 59-68) had a partial/asymmetric
set — replacing with the `pchandler[...]` reference fills the gaps.

**uv index + sources tables** (NEW — from 02-RESEARCH.md §uv Reproducibility Tooling
lines 232-246; no in-repo analog, uv docs cited). Add:
```toml
[[tool.uv.index]]
name = "nvidia"
url = "https://pypi.nvidia.com"
explicit = true

[tool.uv.sources]
cudf-cu12      = { index = "nvidia" }
cuspatial-cu12 = { index = "nvidia" }
# … each RAPIDS -cu12 / -cu11 package named individually
```
> **A2 risk (verify at `uv lock`):** these RAPIDS names arrive *transitively* via
> `pchandler[cuda12]`. If `[tool.uv.sources]` pins on transitive-only names don't
> bind, the fallback (RESEARCH line 249) is to also name the RAPIDS packages
> directly in pc2img's `cuda12`/`cuda11` extras. Do **not** add
> `[tool.uv.sources]` pointing at local `/scratch` paths (D-12, forbidden).

**Do NOT touch this phase** (deferred to QUAL-01/Phase 4, RESEARCH line 332):
placeholder `keywords = ["one", "two"]` (line 9), `documentation =
"https://google.com"` (line 46), DeSpAn leftovers (lines 47-50). Scope discipline:
only touch what re-enabling deps forces.

---

### `uv.lock` (generated, committed) — no analog

Produced by `uv lock` (D-05); universal cross-platform, hash-pinned. **Not
gitignored** — confirmed: `.gitignore` contains `third_party/`, `__pycache__/`,
`.venv` but **no** `uv.lock` entry, so it commits cleanly. No hand-authoring; the
"pattern" is the command sequence and the SC3/SC4 round-trip proof
(02-RESEARCH.md §Validation, `uv sync` reproduces the env). Watch Pitfall 4:
`uv lock` must reach `pypi.nvidia.com` for the RAPIDS resolution (D-06); flag owner
if offline.

---

### `CONTRIBUTING.md` (doc, NEW) — no in-repo analog

`README.rst` is a 9-byte stub, so there is no doc template to copy. Author from the
verified workflow block in 02-RESEARCH.md §Standard Stack (lines 187-194):
```bash
uv sync                 # project + runtime deps + `dev` group (default)
uv sync --group doc     # add the doc group for sphinx
uv run python scripts/smoke_pipeline.py   # SC1 evidence
uv run pytest           # once tests exist (Phase 3)
uv lock                 # regenerate lock after any dependency edit
```
Content requirement (D-07): dev bootstrap only — keep user-facing content out of
`CONTRIBUTING.md`. Note the `dev` group installs by default; `doc` is opt-in.

---

### Break-audit attestation (D-11, doc or asserted comment) — no analog

Author from 02-RESEARCH.md §Semantic-Break Reality (lines 69-83). The finding: all
three named breaks (**BC-PCH-008** FoVTree 2D identifiers, **BC-PCH-007**
world-frame `to_py4dgeo`, **BC-PCH-006/012** Csv/Las load) have **zero call sites**
in `src/pc2img/`. The proportionate deliverable is a **grep-attest** ("no call
sites; not affected"), not code edits. Observable proof (RESEARCH §Validation line
384):
```bash
grep -rE 'FoVTree|to_py4dgeo|\bCsv\b|\bLas\b' src/   # returns nothing → attest non-use
```
> **Two accuracy corrections the planner must carry forward (RESEARCH lines 81-83,
> do NOT silently drop):**
> 1. D-11/CONTEXT says "spherical projection exercises `FoV`/`FoVTree`." It
>    exercises **`FoV` only**; pc2img never touches `FoVTree`. The smoke *cannot*
>    runtime-prove BC-PCH-008 — it gets an audit attestation, the `FoV`/spherical
>    surface gets the runtime proof.
> 2. DEP-01's three breaks are **absent from the library**; the honest deliverable
>    is attestation, not "fixes." Consistent with D-11 ("fix if broken") — they
>    aren't broken because they aren't called.

## Shared Patterns

### Canonical import paths (all resolve against pchandler 2.1 / GSEGUtils 0.5)
**Source:** 02-RESEARCH.md §GSEGUtils Reality + §Semantic-Break Reality; verified in
`src/pc2img/`.
**Apply to:** the smoke script and any import touched this phase.
- `from pchandler import PointCloudData`
- `from pchandler.geometry.coordinates import rhv2xyz`
- `from pchandler.geometry.spherical import FoV` (spherical proj; **not** `FoVTree`)
- `from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig, DiskBackedStore, …`
**Casing gotcha:** distribution is `gsegutils` (what uv/pip installs); importable
package is `GSEGUtils` (capitalized). Requirement string stays capitalized
`GSEGUtils` (D-02); imports stay capitalized. Both are already correct in-tree.

### Compatible-release pin convention (`~=`)
**Source:** current `pyproject.toml` (existing deps all use `~=`) +
`/scratch/41_pchandler/pyproject.toml` (`GSEGUtils ~= 0.5`, line 37).
**Apply to:** the two re-enabled sibling deps — `pchandler ~= 2.1`, `GSEGUtils
~= 0.5`. Loose in `pyproject`, exact in `uv.lock` (D-02).

### setuptools_scm build backend (keep as-is)
**Source:** `pyproject.toml` lines 1-3 + 37-42 (identical shape to pchandler lines
1-3 + 51-56).
**Apply to:** unchanged — D-05 keeps the backend; uv infers `package = true` from
`[build-system]` (no explicit flag needed, A3). Version derives from git tag
`v2.0.0a5` at build time; `.git` must be visible to uv's isolated build (it is, from
project root).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `uv.lock` | config (generated) | batch | Tool-generated by `uv lock`; never hand-authored |
| `CONTRIBUTING.md` | doc | n/a | No doc precedent in repo (`README.rst` is a 9-byte stub); author from RESEARCH workflow block |
| Break-audit attestation | doc/comment | n/a | No precedent; grep-attest content lives in RESEARCH §Semantic-Break Reality |

For all three, the "pattern source" is 02-RESEARCH.md (verified command sequences
and findings), not a codebase analog.

## Metadata

**Analog search scope:** `scripts/`, `scripts/v2.0/`, repo root (`pyproject.toml`,
`.gitignore`, `README.rst`), `src/pc2img/features/base_features.py`,
`src/pc2img/strategies/__init__.py`, and reference `/scratch/41_pchandler/pyproject.toml`.
**Files scanned:** ~8 (targeted; early-stopped once the smoke analog + config
references were confirmed).
**Pattern extraction date:** 2026-07-09
</content>
</invoke>
