# Phase 4: Code Quality & Algorithmic Soundness Review - Research

**Researched:** 2026-07-10
**Domain:** Static hygiene tooling (ruff), software-design review, and mathematical/algorithmic soundness review of a numpy/scipy/pydantic-v2 scientific raster pipeline
**Confidence:** HIGH (code anchors verified file:line this session; external refs cited)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (FIX in Phase 4):** QUAL-01 hygiene in full **plus** low-risk, purely-mechanical design fixes that carry no behavioral risk (guard the `_TransformArray` import; delete/repair the broken `make_generator` factory).
- **D-02 (LOG for Phase 5):** anything behavioral or correctness-affecting (in-place raster mutation semantics, `__array_ufunc__` returning bare `NotImplemented`, all math findings). Each becomes a FINDINGS.md entry, fixed-with-a-proving-test in Phase 5.
- **D-03:** The whole QUAL-02 + QUAL-03 review runs as **ONE orchestrated multi-agent workflow** (find → adversarially refute → verify survivors → synthesize FINDINGS.md). Owner opted into the token scale. Planner decides fan-out shape, agent counts, verification vote thresholds. Executed via the Workflow orchestration harness.
- **D-04:** Design audit is **BROAD**, not limited to the four named flaws. The four are required anchors that MUST appear in FINDINGS.md if still present; the audit additionally sweeps the codebase.
- **D-05:** Math review is **adversarial with empirical checks** — ground claims in reference formulas and, where cheap, back findings with minimal numeric probes (project known points, verify hull culling, NaN propagation).
- **D-06:** Findings logged to a single structured `FINDINGS.md` at `.planning/phases/04-.../04-FINDINGS.md`. Every entry: stable id, `file:line`, one-line defect, why-wrong, minimal repro (inputs → wrong output), severity, pillar (design/math/hygiene), proposed proving-test sketch.
- **D-07:** FINDINGS.md is the canonical BUG-05 feeder. Do **not** mint per-finding `BUG-05.x` requirement IDs; do **not** scatter findings across GSD todos.
- **D-08:** `PerspectiveProjection` (WIP folded code) reviewed at the **same correctness bar** as shipped projections. Unsound math → BUG-05 item.
- **D-09:** Adopt **ruff (Astral)** as lint/format tool; use it to power the QUAL-01 hygiene sweep. Land ruff config + apply fixes here.
- **D-10:** Defer CI **enforcement** of ruff to Phase 6. Phase 4 lands config + fixes only; no blocking lint gate in CI.
- **D-11:** black→ruff-format is the **lower-churn option at planner discretion** (default: replace black with `ruff format`; keeping black is acceptable if lower-churn). Either way, formatting stays black-equivalent (**88-col**).

### Claude's Discretion
- Exact workflow fan-out shape, reviewer counts, adversarial vote thresholds.
- Whether to replace black with `ruff format` or keep black (D-11), chosen for lowest churn.
- FINDINGS.md entry ordering and severity taxonomy (most-severe first).

### Deferred Ideas (OUT OF SCOPE)
- CI enforcement of ruff / lint gate → Phase 6.
- Actually fixing the correctness bugs (BUG-01..05, coerce-null, in-place mutation, `__array_ufunc__`) → Phase 5, each with a proving test.
- cuda11/cuda12 docs may relocate to Phase 6 (planner's call; folded here for now).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QUAL-01 | Code-hygiene cleanup — dead/commented code removed, duplicate `joblib` pin collapsed, placeholder `pyproject` metadata replaced, duplicate `convert_to_image` removed, matplotlib moved to an optional extra | §Pillar 1 (ruff config powers dead-code/unused-import detection); §pyproject Metadata Correction; §Anchor Drift Report confirms every hygiene target's live location |
| QUAL-02 | Software-design review completed; findings addressed or logged (divergent registries, in-place raster mutation, missing dependency-cycle guard, broken `make_generator`) | §Pillar 2 (design audit inventory + 4 anchors + 12 additional seed findings); §Review Harness Shape |
| QUAL-03 | Mathematical/algorithmic soundness review of projection geometry, Delaunay culling, NaN-aware smoothing, feature math; findings addressed or logged | §Pillar 3 (reference formulas + correctness criteria per math path); §Review Harness Shape (math track) |
</phase_requirements>

## Summary

Phase 4 is a **review phase**, not a build phase. The value this research adds is fivefold: (1) a concrete, template-grounded ruff configuration for the QUAL-01 hygiene sweep; (2) reference formulas and correctness criteria the QUAL-03 math reviewers can adversarially check against; (3) a practical find→refute→verify→synthesize workflow shape mapped to the actual module list; (4) exact placeholder-metadata corrections grounded in the sibling PCHandler/GSEGUtils templates; and (5) a short cuda11-vs-cuda12 selection note. All code anchors in CONTEXT.md were re-opened and verified file:line this session — see the **Anchor Drift Report** for the few that shifted.

Two facts materially shape planning. First, the sibling libraries (PCHandler, GSEGUtils) **already ship a `[tool.ruff]` template** — `line-length = 120`, `select = ["E","F","W","B","I","C90","D","NPY"]`, numpy pydocstyle, `tests/**` per-file-ignores. The project's publication standard is to "match the PCHandler template," but **D-11 locks pc2img to 88 columns** — a direct divergence the planner must resolve (recommendation below: honor D-11's 88, adopt the rest of the template minus the high-churn `D`/pydocstyle rules, which are not hygiene). Second, the broad design audit (D-04) will find **well more than the four named anchors**: this research already surfaces ~12 additional seed findings (e.g. `FeatureManager._base_features` is never reset across `request()` calls; `features/__init__.__all__` is out of sync with the registered feature set), so the workflow should be scoped to *discover*, not merely confirm.

**Primary recommendation:** Land an 88-col ruff config mirroring the sibling template's rule families (E/F/W/B/I/C90/NPY) but **excluding `D` (pydocstyle)** to keep Phase 4 focused on hygiene not docstring churn; run `ruff check --fix` + `ruff format` for QUAL-01; structure QUAL-02/03 as a two-track (design + math) find→refute→verify workflow producing a single `04-FINDINGS.md`; fix only the D-01 mechanical items (`make_generator`, `_TransformArray` guard) inline, log everything else.

## Architectural Responsibility Map

For this library, "tiers" are the three review pillars mapped onto the module inventory. This is what the workflow fans out across.

| Capability / Module | Pillar owner | Fix-vs-Log (D-01/D-02) | Rationale |
|---------------------|--------------|------------------------|-----------|
| `pyproject.toml` metadata + dep pins | Hygiene (QUAL-01) | **FIX** | Pure metadata; no behavior |
| Dead/commented code across `util.py`, `interpolation.py`, `projection.py`, `disk_backed_image_data.py` | Hygiene (QUAL-01) | **FIX** (ruff-driven) | Deletion; git preserves history |
| `registry.py` `make_generator` | Design (QUAL-02) | **FIX** (D-01) | Broken factory; mechanical repair/delete |
| `strategies/projection.py:12` `_TransformArray` import | Design (QUAL-02) | **FIX** (D-01) | Guard private import; mechanical |
| `strategies/registry.py` vs `features/registry.py` (divergent registries) | Design (QUAL-02) | **LOG** | Structural; behavioral risk to unify |
| `features/manager.py` dependency resolution (cycle guard, `_base_features` reset) | Design (QUAL-02) | **LOG** | Behavioral; needs proving test |
| `image_cache/disk_backed_image_data.py` `__array_ufunc__` | Design (QUAL-02) / BUG-02 | **LOG** | Behavioral; exception-type contract |
| `features/derivative_features.py` in-place mutation + feature math | Design + Math | **LOG** | Behavioral / numeric |
| `strategies/projection.py` spherical/ortho/perspective geometry | Math (QUAL-03) | **LOG** (ortho arity = BUG-01) | Correctness |
| `strategies/interpolation.py` + `triangulation.py` Delaunay culling | Math (QUAL-03) | **LOG** | Heuristic soundness |
| `util.py` `nanconv` / `convert_to_image` / `replace_nan` | Math (QUAL-03) | **LOG** (dup `convert_to_image` = FIX) | NaN-aware smoothing |
| `features/rrim.py` RRIM math | Math (QUAL-03) | **LOG** | Openness/slope/RGB math |

## Anchor Drift Report

> The planner must not plan against stale line numbers. Every CONTEXT.md `<canonical_refs>` anchor was re-opened this session. Verdicts:

| Anchor (as stated in CONTEXT) | Verified location (2026-07-10) | Verdict |
|-------------------------------|-------------------------------|---------|
| `registry.py:7` `make_generator` broken factory | `def make_generator` at **:7**; broken call `PointCloudImageGenerator(pcd, proj, interp)` at **:16** | ✅ LIVE. Confirmed broken: `PointCloudImageGenerator.__init__` signature is `(pcd, img_res, proj, interp, ...)` (`core.py:67-74`) — positional `proj` lands in `img_res`, `interp` lands in `proj`, and `interp`/`img_res` are missing. Factory cannot produce a valid generator. |
| `projection.py:12,192` `_TransformArray` import + use | import at **:12**; used in type annotation `NDArray|_TransformArray` at **:192** (`PerspectiveProjection.__init__`) | ✅ LIVE. Note the *only* use is a type annotation on the perspective ctor; the runtime matmul at `:204` operates on the passed matrices, not `_TransformArray` directly. |
| `disk_backed_image_data.py:73` `__array_ufunc__` raises bare `NotImplemented` | decorator `@LazyDiskCache.ensure_loaded` at **:72**, `def __array_ufunc__` at **:73**, `raise NotImplemented` at **:74** | ⚠️ ±1 DRIFT. The offending `raise NotImplemented` is at **:74**, not `:73`. Confirmed: `NotImplemented` is the singleton constant, so `raise NotImplemented` throws `TypeError: exceptions must derive from BaseException`, not the intended `NotImplementedError`. |
| `util.py:58 and :231` duplicate `convert_to_image` | first (dead) def at **:58**, second (live) def at **:231** | ✅ LIVE. First def references `plt` at **:76** with no `plt` import in scope → `NameError` if ever reached (it is shadowed by the second def, so unreachable). |
| `pyproject.toml:21 and :24` duplicate `joblib` pins | `joblib ~= 1.5` at **:21**, `joblib ~= 1.3` at **:24** | ✅ LIVE. (Note: `.planning/codebase/CONCERNS.md` says lines 22/25 — that doc is **stale**; CONTEXT's 21/24 is correct.) |
| Math paths (`projection.py`, `interpolation.py`, `triangulation.py`, `util.py`, `derivative_features.py`, `rrim.py`) | all present | ✅ LIVE — see §Pillar 3 for per-file anchors. |

**Stale planning-doc references to correct as you go:**
- `.planning/codebase/CONCERNS.md` "Core dependencies commented out of package metadata" (its #1 Tech Debt item) is **RESOLVED** — `pchandler ~= 2.1` and `GSEGUtils ~= 0.5` are now live at `pyproject.toml:19-20` (fixed in Phase 2, DEP-03). Do **not** re-log it.
- `CONCERNS.md` joblib lines (22/25) and metadata lines (9/46/15-17) are off-by-a-line/two from the current tree; use the verified numbers in this report.
- `CONCERNS.md` `pyproject.toml` line refs generally predate the Phase-2/3 rewrite of that file (which added `[dependency-groups]`, `[tool.uv]`, `[tool.pytest.ini_options]`, `[tool.coverage.*]`). Re-grep before citing any pyproject line in FINDINGS.

## Standard Stack

This is a review phase; the "stack" is the tooling to be adopted plus the runtime the reviewers reason about. Versions verified this session against the project `.venv` and the installed tools.

### Core (tooling adopted in this phase)
| Tool | Version (verified) | Purpose | Why Standard |
|------|--------------------|---------|--------------|
| ruff | **0.15.12** (installed on PATH) | Lint (dead code, unused imports, bugbear, import sort, numpy rules) + format | D-09; supersedes flake8+isort+pyupgrade; the sibling PCHandler/GSEGUtils already standardized on it `[VERIFIED: sibling pyproject.toml]` |
| ruff format | 0.15.12 | Black-compatible formatter | >99.9% line-identical to Black on Black-formatted code `[CITED: docs.astral.sh/ruff/formatter/]`; D-11 |

### Runtime the reviewers reason about (project `.venv`, verified)
| Library | Installed | pyproject pin | Notes for math review |
|---------|-----------|---------------|-----------------------|
| numpy | **2.0.2** | `~= 2.0` | Note: root `CLAUDE.md` says "installed 2.3.5"; the actual `.venv` has **2.0.2**. Reviewers should probe against 2.0.2 behavior (e.g. `np.gradient`, `np.nanpercentile`). |
| scipy | **1.18.0** | `~= 1.14` | `Delaunay`, `LinearNDInterpolator`, `CloughTocher2DInterpolator`, `NearestNDInterpolator`, `scipy.ndimage.{sobel,gaussian_filter,binary_dilation}`, `scipy.signal.convolve2d` |
| pydantic | **2.13.4** | `~= 2.11` | `@validate_call`, `BeforeValidator`, pydantic dataclasses |
| joblib | **1.5.3** | `~= 1.5` **and** `~= 1.3` (dup) | loky backend in `tiled_generator.py` |
| black | 23.12.1 (dev group) | `~= 23.10` | To be replaced by `ruff format` (D-11 default) or kept |
| matplotlib | **absent** | undeclared | Only `convert_to_image(colormap=...)` needs it; move to a `viz` extra (QUAL-01) |

**Installation (ruff into the dev dependency-group):**
```bash
uv add --group dev "ruff ~= 0.15"
```
(pc2img uses PEP 735 `[dependency-groups]`, not `[project.optional-dependencies]`, for tooling — see `pyproject.toml:68-70`. Add ruff alongside `black`/`pytest`/`coverage` there.)

## Package Legitimacy Audit

Only one external package is introduced this phase (`ruff`). It is already installed on the machine (0.15.12) and is the tool the two sibling GSEG libraries already depend on.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| ruff | PyPI | ~4 yrs | tens of M/mo | github.com/astral-sh/ruff | OK | Approved (Astral, first-party; already in sibling pyproject) |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.
*(Legitimacy seam/`npm view` not applicable — PyPI package, already vendored in siblings and installed locally. matplotlib, the only other package touched, is an existing well-known dependency being moved to an extra, not newly introduced.)*

## Pillar 1 — ruff adoption (QUAL-01 engine)

### Recommended `[tool.ruff]` config (88-col, honoring D-11)

The sibling template (`/scratch/41_pchandler/pyproject.toml`, `/scratch/30_GSEGUtils/pyproject.toml`) is:
```toml
[tool.ruff]
line-length = 120
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "W", "B", "I", "C90", "D", "NPY"]
ignore = ["E203"]
[tool.ruff.lint.pydocstyle]
convention = "numpy"
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D100","D101","D102","D103","D106","D200","D400","D414","E712","B024","F841"]
```
`[VERIFIED: sibling pyproject.toml, this session]`

**Recommended pc2img config** — mirrors the template's rule *families* but drops `line-length=120→88` (D-11) and drops `D`/pydocstyle from the initial sweep (rationale below):
```toml
[tool.ruff]
line-length = 88            # D-11: black-equivalent, NOT the sibling 120
target-version = "py312"
src = ["src"]

[tool.ruff.lint]
# Hygiene-focused families (QUAL-01). E/F/W = pycodestyle+pyflakes,
# I = isort, B = bugbear, C90 = mccabe, UP = pyupgrade, NPY = numpy.
# F401 (unused import) + F841 (unused local) + ERA001 (commented-out code)
# are the rules that power the dead-code / unused-import sweep D-09 asks for.
select = ["E", "F", "W", "I", "B", "C90", "UP", "NPY"]
extend-select = ["ERA001"]   # flag commented-out code blocks (CONCERNS §"Large volume of commented-out dead code")
ignore = ["E203"]            # match sibling; slice-colon spacing, black-compatible

[tool.ruff.lint.per-file-ignores]
# Barrel __init__.py re-export the public surface AND trigger import-time
# strategy/feature registration as a side effect. F401 would flag the
# re-exports as unused; E402 can appear where a module docstring must move.
"src/pc2img/__init__.py" = ["F401"]
"src/pc2img/features/__init__.py" = ["F401"]
"src/pc2img/strategies/__init__.py" = ["F401"]
"src/pc2img/image_cache/__init__.py" = ["F401"]
"tests/**" = ["E712", "F841", "B024"]

[tool.ruff.format]
# Drop-in for black; 88-col already set above. quote-style/skip-magic-trailing
# left at defaults = black-equivalent.
```
`[CITED: docs.astral.sh/ruff/configuration/, docs.astral.sh/ruff/settings/]`

**Notes for the planner:**
- **`D` (pydocstyle) deliberately omitted.** Adopting the sibling's `D` + `convention="numpy"` would flag every undocumented function/class/module — that is *docstring churn*, not *hygiene*, and would balloon Phase 4 far past the QUAL-01 scope. Recommendation: leave `D` out now; a later docstring-sweep plan (analogous to what the siblings did) can add it under publication hardening (Phase 6). If the owner wants template-parity now, add `D` with a broad `per-file-ignores` and treat the resulting fixes as a separate task — flag as an **[ASSUMED]** scope call for the owner (A1).
- **The registry import-time-side-effect pattern** (decorators run when `__init__.py` imports a submodule — see `features/__init__.py:1-9`, `strategies/registry.py`) means barrel re-exports look "unused" to F401. The `per-file-ignores` above exempt exactly those barrels. Do **not** blanket-`# noqa` inline; scope it to the `__init__.py` files.
- **ERA001** (commented-out code) directly targets the `CONCERNS.md` "large volume of commented-out dead code" list. It is noisy, so run it as an assisted pass: `ruff check --select ERA001 src/` to enumerate, then delete blocks deliberately (git preserves history) rather than blind `--fix`.
- **`C90` (mccabe)** needs a threshold to fire: add `[tool.ruff.lint.mccabe] max-complexity = 15` if you want it active, else it is inert. Optional; the siblings enable it without a threshold (inert there too).

### The QUAL-01 hygiene sweep, mechanically
```bash
ruff check --select F401,F811,F841 src/          # unused imports, redefinitions (catches dup convert_to_image!), unused locals
ruff check --select ERA001 src/                  # enumerate commented-out dead code
ruff check --fix src/                            # auto-fix the safe lot (imports, sorting)
ruff format src/ tests/                          # black-equivalent formatting
```
- **`F811` (redefinition of unused name) will flag the duplicate `convert_to_image`** (`util.py:58` shadowed by `:231`) and any duplicate `joblib`-like issues at the Python level — a nice cross-check that the QUAL-01 targets are real. (The pyproject `joblib` duplicate is a TOML-list dup, not caught by ruff; fix it by hand.)

### black→ruff-format migration (D-11)
- `ruff format` is an explicit **drop-in, Black-compatible** replacement; on Black-formatted code >99.9% of lines are byte-identical `[CITED: docs.astral.sh/ruff/formatter/, astral.sh/blog/the-ruff-formatter]`.
- **Caveat:** the codebase is *not currently black-clean* (root `CLAUDE.md` §Code Style: "much of the current code exceeds 88 chars and is not yet black-clean"). So the first `ruff format` pass will produce a **large diff regardless** of black-vs-ruff — that churn is intrinsic to formatting-for-the-first-time, not to the tool choice. Land it as its own commit so review is legible.
- **Tradeoff (D-11):** Replacing black with `ruff format` collapses two tools into one (ruff already does lint), matches the siblings, and is faster. Keeping black adds no value once ruff is present. **Recommendation: replace black** (remove `black ~= 23.10` from the `dev` group, add `ruff`). Lower churn *long-term*; the one-time format diff is identical either way.

## Pillar 2 — software-design review (QUAL-02, BROAD per D-04)

### The four required anchors (MUST appear in FINDINGS.md if still present — all confirmed LIVE)

| # | Anchor | Location | Fix/Log | Precise defect |
|---|--------|----------|---------|----------------|
| 1 | Broken `make_generator` factory | `registry.py:7-16` | **FIX** (D-01) | Calls `PointCloudImageGenerator(pcd, proj, interp)` but ctor is `(pcd, img_res, proj, interp, ...)` — args land in wrong params, `img_res` missing. Repair to pass `img_res` + keywords, or delete (no live caller found). |
| 2 | Divergent registries | `strategies/registry.py` (generic `StrategyRegistry`, kwarg-filtering, `key_of`) vs `features/registry.py` (regex-DSL `FeatureRegistry`, default fallback) | **LOG** | Two independent registry mechanisms with different contracts, error types (`KeyError` vs `RuntimeError`), and lifecycles. Extra sub-finding: `FeatureRegistry.match()` **instantiates** the class (`registry.py:51 inst = cls(**spec.params)`) merely to read `.dependencies` — side-effectful, and re-instantiated again in `manager._compute`. |
| 3 | In-place raster mutation | `derivative_features.py:83-84` (`NormalizedFeature.compute`: `np.divide(..., out=img)`, `np.clip(..., out=img)` where `img = fetch(...)`) | **LOG** | Writes into the array returned by `fetch`. Safe *only* because `DiskBackedImageData.__array__` returns a copy (`disk_backed_image_data.py:53-58`); becomes cache corruption if `fetch` ever returns a view. `ClipPercentileFeature.compute` (`:264`) already copies — inconsistent. |
| 4 | Missing dependency-cycle guard | `features/manager.py:39-51` (`request.visit`) + `:70-83` (`_get`/`_compute`) | **LOG** | `visit` recurses through `spec.dependencies` with no visited-set; a self/transitively-cyclic feature name → unbounded recursion / `RecursionError`. |

### Additional design seeds surfaced this session (D-04 broad audit — NOT exhaustive; the workflow must find more)

| # | Defect | Location | Fix/Log | Note |
|---|--------|----------|---------|------|
| A | `_TransformArray` private import at module scope | `projection.py:12` | **FIX** (D-01) | A pchandler drop/rename breaks importing the *entire* projection module. Guard with a `try/except ImportError` + lazy fallback, or import inside `PerspectiveProjection`. |
| B | `FeatureManager._base_features` **never reset** in `request()` | `manager.py:29` (init only) vs `:43` (append) | **LOG** | `_targets` is reset at `:35` but `_base_features` is not — repeated `request()` calls **accumulate** base-feature specs. Latent correctness bug on generator reuse. |
| C | `features/__init__.__all__` out of sync with registered features | `features/__init__.py:1-9` | **FIX** (hygiene) | `__all__` lists only 5 derivative features; Sobel/Sum/Square/Root/Norm/Clip/MultiScaleGradient/OcclusionAware/RRIM* are registered (import side effect) but absent from the barrel's public surface. Not a functional break (registration still happens) but a documentation/hygiene defect. |
| D | Non-optional attr assigned `None` | `features/registry.py:27` (`_default_cls: Type[...] = None`) | **LOG** (typing) | pyright basic mode flags/suppresses; annotate `Optional[...]`. |
| E | Mutable constructed default | `manager.py:24` (`lazy_disk_cache_config: LazyDiskCacheConfig = LazyDiskCacheConfig()`); also `tiled_generator.py:93,108` | **LOG** | Shared-instance default; prefer the `None`-sentinel + `coerce_lazy_cfg` pattern from `core.py:34-41`. |
| F | `__array_ufunc__` raises the `NotImplemented` singleton | `disk_backed_image_data.py:74` | **LOG** (BUG-02) | `raise NotImplemented` → `TypeError`, not `NotImplementedError`. The `NDArrayOperatorsMixin` mix-in's entire purpose (`+ - * /`) is dead. FINDINGS must specify the **intended exception type** so Phase 5's proving test asserts correctly (per CONTEXT `<specifics>`). |
| G | `extend_cache_paths` drops interp kwargs | `tiled_generator.py:60-63` | **LOG** (BUG-03) | `updates["interp_kwargs"] = dict(...).update({...})` → `dict.update` returns `None`. Already a named BUG-03; cross-reference, don't duplicate. |
| H | Circular-import sensitivity | `tiled_generator.py:17` (`from pc2img import PointCloudImageGenerator`) | **LOG** | Submodule importing the top-level package barrel; fragile ordering. |
| I | `rrim.py` module docstring inert | `rrim.py:1-11` | **LOG** (BUG-04) | `from __future__ import annotations` precedes the triple-quoted string → `__doc__ is None`. Already BUG-04; cross-reference. |
| J | Pickle load of arbitrary cache files | `image_cache/disk_backed_image_store.py` (scan+`pickle.load`) | **LOG** (security) | See §Security Domain. |
| K | Duplicate `joblib` pin | `pyproject.toml:21,24` | **FIX** (QUAL-01) | Collapse to one `joblib ~= 1.5` (matches sibling PCHandler pin). |
| L | Undeclared matplotlib | `util.py:280` import; `pyproject.toml` no entry | **FIX** (QUAL-01) | Add a `viz = ["matplotlib ~= 3.9"]` optional-extra; guard already exists at `util.py:279-282`. |

## Pillar 3 — mathematical / algorithmic soundness (QUAL-03)

For each math path: the reference formula, the correctness criteria the adversarial reviewer checks against, and a cheap empirical probe (D-05). Reviewers should *try to refute* soundness with a numeric counter-example.

### 3.1 Spherical projection — `projection.py:95-142`
**Code:** `project_raw` returns `pcd.spher[mask, 1:]` (columns = azimuth `h`, elevation `v`; column 0 is range `r`), with `mins=(fov.left, fov.top)`, `maxs=(fov.right, fov.bottom)`. Base `project()` (`:60-87`) normalizes `(coords-mins)/span`, maps `x_px=u*(w-1)`, `y_px=v*(h-1)`.
**Reference:** equirectangular / panoramic range-image mapping: pixel column ∝ azimuth, pixel row ∝ elevation, linear within the FoV bounds.
**Correctness criteria / refutation targets:**
- **Azimuth wrap-around:** linear `(h-left)/(right-left)` is wrong if the FoV straddles the ±180°/0–360° discontinuity (e.g. `left=170°, right=-170°` → negative span). Probe: construct a FoV crossing the seam; check monotonic pixel mapping.
- **top/bottom sign convention:** if `fov.top > fov.bottom` in the elevation metric, `span` is negative → `span[span==0]=1` guard doesn't help; normalization inverts. Probe: known elevation → expected row.
- **Half-pixel / endpoint:** `*(w-1)` maps the extent onto `[0, w-1]` inclusive (pixel *centers* at the edges) rather than `*w` with a 0.5 offset. Reviewer decides if this is the intended convention vs a systematic half-pixel shift. Probe: project the four FoV corners, assert they land on `{0, w-1}×{0, h-1}`.
- Consistency with `inverse_projection` (`:118-142`), which uses `np.linspace(left,right,num=px,endpoint=True)` — endpoint=True agrees with `*(w-1)`. Good cross-check anchor.

### 3.2 Orthographic projection — `projection.py:148-181`  (also BUG-01)
**Code:** `project_raw` returns `pcd.xyz[mask, self._xyz_column_selection], mask` — a **2-tuple**, but base `project()` unpacks a **4-tuple** (`:73`).
**Defect (confirmed):** (a) arity mismatch → `ValueError: not enough values to unpack (expected 4, got 2)`; (b) `pcd.xyz[mask, [0,1]]` mixes a boolean row mask with a fancy column list — numpy broadcasts `nonzero(mask)` (length M) against `[0,1]` (length 2) → error unless M==2. In-source `# Todo: Update to pass min and max back!` at `:180` acknowledges (a).
**Correct approach for FINDINGS proving-test sketch:** return `(coords, mask, mins, maxs)` where `coords = pcd.xyz[mask][:, cols]` (index rows then columns), and `mins/maxs` come from `roi_box` when present else the per-column data extent. This is a named BUG-01 anchor; QUAL-03 confirms the *math* (extent normalization) not just the arity.

### 3.3 Perspective projection (WIP, D-08 — same bar) — `projection.py:184-211`
**Code:** `project()` computes `uv = (projection_matrix @ rotation_matrix) @ pcd; uv = uv.arr[:, :2] / uv.arr[:, 2].reshape(-1,1)`; mask = in-bounds `[0, resolution)`.
**Reference (pinhole):** `x_img = K · [R | t] · X_world`; then perspective divide by depth `Z_c`; cull points with `Z_c ≤ 0` (behind camera). See Hartley & Zisserman, *Multiple View Geometry*, ch. 6 `[ASSUMED: standard pinhole model]`.
**Refutation targets:**
- **`@ pcd` directly:** matmul against a `PointCloudData` object relies on an undocumented `_TransformArray.__matmul__` accepting `pcd` and yielding `.arr`. Verify this contract exists in pchandler 2.x; if not, the method throws before any math. (Probe: minimal `PerspectiveProjection(...).project(pcd, res)`.)
- **No behind-camera guard:** points with `Z_c < 0` still pass the divide and can land in-bounds with flipped sign — classic pinhole bug. Add `mask &= uv_z > 0`.
- **Extrinsics:** `projection_matrix @ rotation_matrix` conflates intrinsics `K` with a rotation but has **no translation `t`** / camera center. Verify whether the caller pre-bakes `t`; if not, the model only works for a camera at the origin.
- `project_raw` raises `NotImplementedError` (`:187`) but is never called (base `project` is overridden) — dead abstract override; note for hygiene.

### 3.4 Delaunay scattered interpolation + hull culling — `interpolation.py:83-289`, `triangulation.py`
**Reference (scipy):** `LinearNDInterpolator`/barycentric — triangulate with Qhull, linear barycentric per triangle; **points outside the convex hull get `fill_value`, default `np.nan`**, corresponding to `Delaunay.find_simplex(...) == -1` `[CITED: docs.scipy.org LinearNDInterpolator]`. The hand-rolled `DelaunayInterpolation` reimplements this: `find_simplex` (`:280`), `tri.transform` barycentric (`:281-286`), `result[~mask]=fill_value=nan` (`:204,258`).
**Refutation targets (the culling heuristics are the suspect part):**
- **Magic culling thresholds** (`:235` `area_thresh = np.median(area)*10`; `:240` MAD-based `aspect_ratio_thresh`; `:237` `max_edge_thresh = None`): triangles exceeding these are dropped (`:243-251`), turning interior query pixels into NaN "holes." On sparse/anisotropic tiles this **over-culls** and punches holes into valid interior regions — a correctness (not just perf) concern. No parameterization (PERF-03 tracks exposing them; QUAL-03 assesses whether the *default* silently corrupts output). Probe: a uniform grid of points with one deliberately large-but-valid triangle; assert it isn't culled.
- **Hull boundary behavior:** confirm interior-but-near-hull pixels get real values, exterior get NaN (matches scipy semantics). Probe: query points just inside vs just outside a known triangle.
- **Barycentric correctness:** `bary[:,-1] = 1 - bary_partial.sum(axis=1)` (`:286`) — verify weights sum to 1 and reproduce a known linear field exactly (interpolate `f(x,y)=ax+by+c` → should be exact to float error). Strong, cheap adversarial probe.
- Full-array SHA-256 keying (`:133-139`) is a *perf* concern (PERF-01), not correctness — note but keep in the perf bucket.

### 3.5 NaN-aware smoothing — `util.py` `nanconv` (`:33-46`), `convert_to_image` (`:231-294`), `replace_nan` (`:110-173`)
**Reference (normalized convolution):** for data `a` with validity mask `m`, `smoothed = conv(a·m, k) / conv(m, k)` where `conv(m,k)==0` → NaN/undefined. This is Knutsson–Westin normalized convolution; `MultiScaleGradientFeature._smooth_with_nan` (`derivative_features.py:354-375`) implements exactly this correctly (fill→convolve→divide by convolved mask→renormalize→NaN where weight≤eps). `nanconv` implements the same idea via `convolve2d`.
**Refutation targets for `nanconv`:**
- **In-place mutation of the input** (`:37 a[n] = 0`) — corrupts the caller's array as a side effect. Design+math defect. Probe: pass an array with NaNs, assert it's unchanged after the call (it won't be).
- **float16 precision/perf** (`:40-43` cast to `np.float16`, divide in float16) — precision loss and slower on most CPUs (PERF-02 tracks the perf half; QUAL-03 flags the numeric half: float16 division of convolution sums can lose significant bits for large kernels/values).
- **`on = np.ones(a.shape, dtype=a.dtype)`** (`:34`) — if `a` is integer dtype, the mask/normalization degrade; and `a[n]=0` on an int array can't hold the NaN sentinel. Probe: int input.
- **Kernel not required to be normalized:** because of the renormalize-by-valid-weight, un-normalized `k` is tolerated — verify that's intended vs. a latent scale bug when callers pass an unnormalized kernel.
**`convert_to_image` (live, `:231`):** min-max normalize on finite values (`:269-276`), NaN filled first via `replace_nan`. Refutation target: `x[finite].min()` at `:271` errors if the array is all-NaN (empty `finite`); the `.min(initial=...)` guard at `:270` covers the branch condition but `:271-272` re-index without the guard. Probe: all-NaN 2D input.

### 3.6 Feature math — `derivative_features.py`, `rrim.py`
- **`GradientFeature`** (`:27-31`): `np.gradient(img, 100, axis=ax)` — the spacing `100` is a hardcoded magic number dividing the gradient by 100. Unless pixel spacing is genuinely 100 units, this mis-scales every gradient. Contrast `MultiScaleGradientFeature`/`rrim` which use unit or `pixel_size` spacing. Probe: gradient of a known linear ramp → expected slope.
- **`HillshadeFeature`** (`:132-144`): implements ESRI hillshade. Reference: `Hillshade = cos(Zenith)·cos(Slope) + sin(Zenith)·sin(Slope)·cos(Azimuth − Aspect)`, `Zenith = 90° − Altitude` `[CITED: standard ESRI hillshade]`. **Algebraic check (done this session): the code is equivalent** — it uses `slope_var = π/2 − arctan|∇|` so `sin(slope_var)=cos(Slope)`, `cos(slope_var)=sin(Slope)`, and `sin(altitude)=cos(Zenith)`, `cos(altitude)=sin(Zenith)`. So the illumination formula is **correct**. The reviewer's remaining refutation target is the **aspect convention**: `aspect = arctan2(-x, y)` where `x,y = np.gradient(values)` → `x = ∂/∂row` (vertical), `y = ∂/∂col` (horizontal). ESRI aspect is `arctan2(dz/dy, -dz/dx)`; verify the axis assignment/handedness isn't transposed (would rotate the light direction 90°). Probe: a synthetic east-facing ramp under a known azimuth → expected bright/dark side.
- **`NormalizedFeature`** (`:57-85`): percentile bounds validation is **commented out** (`:68-71`) — now accepts `low>high` or out-of-`[0,100]` silently. Plus in-place `out=img` mutation (anchor #3). Hygiene (dead validation) + behavior.
- **RRIM** (`rrim.py`): reviewed like any other feature math (RRIM IP gate CLEARED — do not touch IP posture).
  - **Slope** (`compute_slope :207-219`): `|∇(z·z_factor)|` via `np.gradient` with `pixel_size` spacing; NaN-adjacent invalidation. Standard. Probe: planar tilt → constant slope.
  - **Openness** (`compute_openness :222-292`): per direction, along a ray to `max_distance`, `elevation = degrees(arctan2(Δz, distance))`; `positive = 90 − max_upward`, `negative = 90 − max_downward`; then mean across directions. **Reference: Yokoyama et al. (2002)** topographic openness — positive openness = mean over azimuths of `(90° − max elevation angle to horizon)`; large on convexities/ridges, small in pits `[CITED: Yokoyama et al. 2002, Visualizing Topography by Openness]`. Code matches (ridge → neighbors lower → small `max_upward` → large positive). Refutation targets: (i) rays built by integer `rint` of `cos/sin·step` with dedup (`_build_ray_offsets :180-204`) — near-horizontal/vertical rays may under-sample directions; (ii) `pixel_size` anisotropy in the distance term.
  - **Structure / differential openness** (`:373,496`): `structure = 0.5·(positive − negative)`. **Reference: differential openness = (Openness⁺ − Openness⁻) / 2** `[CITED: Yokoyama 2002 / Chiba et al. 2008 RRIM]` — **code is correct.**
  - **RGB compose** (`compose_rrim_rgb :295-313`): red channel = `clip(structure_norm + red_strength·slope_norm·(1−structure_norm), 0, 1)`, green=blue=`structure_norm`. Reference: Chiba et al. (2008) Red Relief Image Map layers slope (red) over openness `[CITED: Chiba et al. 2008]`. Reviewer checks the specific blend against the paper's intent; the *structure/openness/slope* primitives are sound.

## Review Harness Shape (D-03) — find → refute → verify → synthesize

The executor runs this via the Workflow orchestration tool. Concrete, grounded shape for the planner to express as PLAN.md tasks:

### Module inventory to fan out across (13 source modules)
```
Design track (QUAL-02):
  D1 registries+factory   → registry.py, strategies/registry.py, features/registry.py
  D2 orchestration        → core.py, features/manager.py, tiled_generator.py
  D3 image cache          → image_cache/disk_backed_image_data.py, image_cache/disk_backed_image_store.py
  D4 cross-cutting hygiene/typing → sweep all + pyproject.toml (ruff output as evidence)
Math track (QUAL-03):
  M1 projection geometry  → strategies/projection.py (spherical, orthographic, perspective)
  M2 interpolation/culling→ strategies/interpolation.py, strategies/triangulation.py, strategies/utils.py
  M3 smoothing/util math  → util.py (nanconv, convert_to_image, replace_nan, to_gray)
  M4 derivative features  → features/derivative_features.py
  M5 rrim math            → features/rrim.py
```

### Pipeline
1. **FIND (fan-out, ~9 reviewers = D1-D4 + M1-M5):** each reviewer produces *candidate* findings in the D-06 entry schema against its module set, seeded by this research's tables (§Pillar 2, §Pillar 3) + `.planning/codebase/CONCERNS.md` + the Phase-3 pytest `xfail` reasons (they already encode known bugs — cross-reference). Reviewers are told to *discover beyond* the seed list (D-04).
2. **REFUTE (adversarial):** each candidate is handed to an **independent** verifier whose job is to *disprove* it — write the cheapest numeric probe (D-05) that would show the code is actually correct. Math findings especially: project a known point, verify hull culling, force NaN propagation. A candidate that the refuter reproduces-as-a-bug **survives**; one the refuter turns into a passing counter-probe is **dropped** (or downgraded to LOW "needs empirical confirmation").
3. **VERIFY survivors:** dedupe across reviewers (many will independently hit anchors #1-4), assign stable ids, severity, pillar, and attach the minimal repro + proving-test sketch.
4. **SYNTHESIZE:** merge into a single `04-FINDINGS.md`, most-severe first (Claude's discretion on taxonomy).

### Vote threshold recommendation (small codebase — keep it lean)
- **1 finder + 1 independent refuter per module set** (not per finding — per module, refuter re-examines all that module's candidates). This is the 2-of-2 pattern: a finding is *confirmed* only if the finder asserts it AND the refuter fails to produce a counter-probe. Ties/uncertain → keep as a LOW-confidence entry flagged "empirical confirmation pending in Phase 5."
- Escalate to a **3rd tiebreaker reviewer** only for HIGH-severity math findings where finder and refuter disagree (e.g. the perspective `Z<0` guard, the Delaunay over-culling). ~13 modules × 2 passes + a few tiebreakers is the owner-accepted token scale (D-03).
- **Empirical probes are cheap and decisive** (D-05): prefer a 5-line numpy probe over prose. The barycentric exact-linear-field probe (§3.4) and the hillshade ramp probe (§3.6) are the highest-value adversarial tests.

### Expressing as PLAN.md tasks
- One task per FIND reviewer (or batch design/math tracks into two waves) → each emits a candidate-findings fragment.
- One REFUTE task per module set consuming the matching FIND fragment.
- One SYNTHESIZE task consuming all survivors → writes `04-FINDINGS.md`.
- Separate mechanical FIX tasks (D-01): `make_generator` repair/delete, `_TransformArray` guard, `__all__` sync — each with a smoke check that the module still imports.
- Separate QUAL-01 tasks: ruff config land → `ruff check --fix` → `ruff format` → dup-joblib collapse → matplotlib extra → metadata correction (below).

## pyproject.toml Metadata Correction (QUAL-01)

Grounded in the sibling PCHandler template (the good exemplar; note GSEGUtils *also* still has placeholder `keywords = ["ONE","TWO"]`, so mirror **PCHandler**, not GSEGUtils, for keywords).

| Field | Current (placeholder) | Location | Corrected value (recommended) |
|-------|----------------------|----------|-------------------------------|
| `keywords` | `["one", "two"]` | `:9` | e.g. `["LiDAR", "point cloud", "range image", "raster", "geospatial", "remote sensing", "DEM", "RRIM"]` (PCHandler uses `["LiDAR","Pointclouds"]` as the style anchor) |
| `documentation` url | `"https://google.com"` | `:45` | No docs site exists yet. Either **remove** the line, or point to the repo (`https://github.com/gseg-ethz/pc2img` — verify org/name) or the GSEG readthedocs pattern GSEGUtils uses (`https://…readthedocs.io`). Flag as **[ASSUMED]** (A2) — needs owner confirmation of the real docs URL. |
| `classifiers` | `["Programming Language :: Python :: 3"]` | `:15-17` | Mirror GSEGUtils' richer set: `Development Status :: 3 - Alpha`, `Intended Audience :: Science/Research`, `Programming Language :: Python :: 3.12`, `Typing :: Typed`, `Topic :: Scientific/Engineering :: Image Processing`, `Topic :: Scientific/Engineering :: GIS`, and a `License :: OSI Approved :: …` line matching the actual `LICENSE`. Flag license classifier as **[ASSUMED]** (A3) — must match the real LICENSE file. |
| `authors` | `Nicholas Meyer <meyernic@ethz.ch>` | `:11-13` | **Already correct** — matches sibling convention. Not a placeholder. |
| `description` | present, sensible | `:7` | Fine as-is. |
| `joblib` dup | `~= 1.5` and `~= 1.3` | `:21, :24` | Collapse to one `joblib ~= 1.5` (PCHandler pins `~= 1.5`). |
| matplotlib | undeclared | add to `[project.optional-dependencies]` | Add `viz = ["matplotlib ~= 3.9"]` (verify a current 3.x pin); `util.py:279-282` already guards its absence. |

## cuda11 vs cuda12 Selection Note (minor docs deliverable)

Short, driver-based guidance (folded per CONTEXT; planner may relocate to Phase 6 publication docs). Grounded in the existing `pyproject.toml:51-53,72-109` comments, which already document that the two extras are mutually exclusive (uv `conflicts`) and resolve RAPIDS 25.4 via the nvidia index.

**Recommended note content:**
- pc2img exposes `pc2img[cuda11]` and `pc2img[cuda12]` (both pull `pchandler[cudaXX]` → RAPIDS `cudf/cuspatial/cuproj/cuml/dask-cudf`).
- **The pick is driven by your installed NVIDIA driver, not your CUDA toolkit.** RAPIDS cu12 wheels need a driver satisfying the CUDA 12.x minimum; cu11 wheels the CUDA 11.x minimum. Check with `nvidia-smi` (top-right "CUDA Version" = the *maximum* CUDA runtime the driver supports).
  - Driver supports CUDA ≥ 12.0 → install `pc2img[cuda12]` (preferred; RAPIDS 25.4 is primarily a cu12 line).
  - Older driver capped at CUDA 11.x → install `pc2img[cuda11]`.
- The two are **mutually exclusive** — `cudf-cu12` requires `cuda-python>=12.6.2,<13` while `cudf-cu11` requires `>=11.8.5,<12`; a single environment cannot satisfy both (`pyproject.toml:72-77`).
- Install-time selection: `pip install pc2img[cuda12]` vs `pip install pc2img[cuda11]`; requires `--extra-index-url=https://pypi.nvidia.com` (or the configured uv nvidia index).
- Keep it to ~8-10 lines; link the RAPIDS install matrix rather than duplicating version tables. `[ASSUMED]` — exact RAPIDS/driver minimums should be confirmed against the RAPIDS install selector at doc-write time (A4).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Lint/format/dead-code/unused-import detection | custom AST scanner | ruff (`F401/F811/F841/ERA001` + `ruff format`) | D-09; the sibling standard; catches the dup `convert_to_image` via F811 |
| Scattered-point → grid interpolation | the hand-rolled `DelaunayInterpolation` barycentric+culling | scipy `LinearNDInterpolator`/`CloughTocher2DInterpolator` (already wrapped as `linear`/`cubic`) | scipy handles hull/fill correctly; the custom culling heuristics are the main soundness risk (§3.4) |
| NaN-aware smoothing | ad-hoc float16 `nanconv` | normalized-convolution done right (like `_smooth_with_nan`, float32, no input mutation) | §3.5 flaws are in the hand-roll, not the concept |

**Key insight:** the review's job is to decide *which* hand-rolled numerics are load-bearing (the custom Delaunay path is used by the `delaunay` strategy and can't just be deleted) vs. accidental (float16, magic `100` spacing). Log the latter as BUG-05 with a scipy-or-float32 proving path.

## Common Pitfalls

### Pitfall 1: Planning against stale line numbers
**What goes wrong:** `.planning/codebase/CONCERNS.md` predates the Phase-2/3 `pyproject.toml` rewrite and the util/interpolation edits; its line refs are off by 1-3 and one item ("deps commented out") is already fixed.
**How to avoid:** use the §Anchor Drift Report table (verified this session) and re-grep before writing any `file:line` into FINDINGS.

### Pitfall 2: Treating registration barrels as unused imports
**What goes wrong:** `ruff --fix` with F401 unqualified would delete the `__init__.py` re-exports that *are the registration mechanism* (import side effect populates `FEATURES`/`PROJECTIONS`).
**How to avoid:** the `per-file-ignores` in the recommended config exempt the four `__init__.py` barrels. Verify `import pc2img; import pc2img.features; import pc2img.strategies` still register all strategies after the sweep.

### Pitfall 3: Over-culling in Delaunay = silent NaN holes (mistaken for "outside hull")
**What goes wrong:** a reviewer sees NaNs and assumes correct hull behavior; they can actually be interior pixels killed by `area_thresh = median·10`.
**How to avoid:** the §3.4 probe (uniform grid + one large-but-valid triangle) distinguishes hull-NaN from culling-NaN.

### Pitfall 4: Asserting the wrong exception in the `__array_ufunc__` finding
**What goes wrong:** logging "raises NotImplementedError" when it actually raises `TypeError` (the `NotImplemented` singleton isn't an exception). Phase 5's proving test would then assert the wrong type.
**How to avoid:** FINDINGS entry states the *observed* `TypeError: exceptions must derive from BaseException` and the *intended* `NotImplementedError` (per CONTEXT `<specifics>`).

## Runtime State Inventory

> Greenfield-style review phase; no rename/migration. Included for completeness — nothing to migrate.

- **Stored data:** None — this phase edits source + `pyproject.toml` + writes `04-FINDINGS.md`. No datastore keys change.
- **Live service config:** None.
- **OS-registered state:** None.
- **Secrets/env vars:** None — the library reads no env vars (root `CLAUDE.md` §Configuration confirms no `os.environ` usage).
- **Build artifacts:** `src/pc2img/_version.py` is setuptools_scm-generated (do not hand-edit; ruff-exempt via `[tool.coverage.run] omit`). Removing `black` from the dev group changes the resolved env — run `uv sync` after the pyproject edit so the lockfile/venv reflect the ruff swap.

## Validation Architecture

> nyquist_validation is enabled (config.json `workflow.nyquist_validation: true`). This is a review phase: the *primary* validation artifact is `04-FINDINGS.md` proving-test sketches (which become Phase 5 tests), plus automated gates for the mechanical FIX items.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `~= 9.1` (dev dependency-group) + coverage `~= 7.0`, pytest-cov `~= 5.0` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `--import-mode=importlib --strict-markers`) + `[tool.coverage.run] branch=true, source=["pc2img"]` |
| Quick run command | `.venv/bin/pytest -x -q` |
| Full suite command | `.venv/bin/pytest --cov=pc2img --cov-branch` |
| Lint gate (new, non-blocking this phase) | `ruff check src/` and `ruff format --check src/` |

### Phase Requirements → Test/Verification Map
| Req | Behavior | Verification type | Automated command | Exists? |
|-----|----------|-------------------|-------------------|---------|
| QUAL-01 | ruff clean; no dup defs; no placeholder metadata; matplotlib extra | lint + smoke | `ruff check src/` ; `python -c "import pc2img"` ; `python -c "import tomllib,sys; d=tomllib.load(open('pyproject.toml','rb')); assert d['project']['keywords']!=['one','two']"` | ❌ Wave 0 (add) |
| QUAL-01 | dup `convert_to_image` removed | smoke | `ruff check --select F811 src/pc2img/util.py` (expect clean) | ❌ Wave 0 |
| QUAL-02 (D-01 fixes) | `make_generator` repaired/removed; projection module imports without pchandler private symbol | smoke | `python -c "import pc2img.strategies.projection"` ; `python -c "import pc2img.registry"` | ❌ Wave 0 |
| QUAL-02/03 | design+math findings captured | artifact check | `test -s .planning/phases/04-*/04-FINDINGS.md` + schema lint (each entry has id/file:line/severity/pillar/proving-test) | ❌ Wave 0 |
| QUAL-03 | proving-test sketches are executable | (deferred) | Phase 5 authors the actual tests from FINDINGS | — Phase 5 |

### Sampling Rate
- **Per FIX task commit:** `ruff check <touched files>` + `python -c "import <touched module>"`.
- **Per wave merge:** full `ruff check src/` + `.venv/bin/pytest -q` (the Phase-3 green suite, 15 passed / 11 xfailed, must stay green; xfails must not flip to unexpected pass).
- **Phase gate:** `04-FINDINGS.md` exists, schema-valid, and every named anchor (#1-4) is either FIXED (with smoke proof) or logged with a repro.

### Wave 0 Gaps
- [ ] `tests/test_hygiene.py` — smoke: `import pc2img` and each submodule imports; `pyproject.toml` metadata non-placeholder; ruff clean on `src/`.
- [ ] Framework install: `uv add --group dev "ruff ~= 0.15"` (ruff not yet in pyproject, though present on PATH).
- [ ] No new fixtures required; the FINDINGS proving-tests are authored in Phase 5, not here.

## Security Domain

> security_enforcement enabled (ASVS L1, block_on high). This is a review phase editing internal library code with no network/auth surface; the relevant security work is *surfacing* one pre-catalogued issue in the audit.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard control |
|---------------|---------|------------------|
| V5 Input Validation | partial | The library validates API inputs via pydantic `@validate_call` + `BeforeValidator` (`core.py`); feature-name DSL is regex-parsed. No untrusted-network input. |
| V6 Cryptography | no | SHA-256 in `interpolation.py` is a cache key, not a security control. |
| V1/V2/V3/V4 (auth/session/access) | no | Library, no auth surface. |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Mitigation / finding |
|---------|--------|----------------------|
| **Pickle deserialization of arbitrary `*.pkl` cache files** (`image_cache/disk_backed_image_store.py` scans cache dir + `pickle.load`s on access and in `__setstate__`) | Tampering / RCE | Log as a **design/security FINDINGS entry** (seed J). Current mitigation: cache dirs are process-local `tempfile.mkdtemp()`. Recommendation to record: document that cache dirs must be trusted; if ever user-supplied/shared, add provenance checks or a non-executable array format. This is *logged*, not fixed, in Phase 4 (behavioral surface → Phase 5/6). |
| Pickle side-effect writes disk on `__getstate__` | (info) | Note interaction with loky worker serialization in `tiled_generator.py`; verify workers reload from shared cache rather than re-serializing (also a scaling concern). |

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Omitting `D`/pydocstyle from the initial ruff config is acceptable scope for Phase 4 (vs. matching the sibling template's `D` now) | Pillar 1 | If owner wants full template parity now, add a (large) docstring-sweep task; otherwise deferred to Phase 6 |
| A2 | The real documentation URL is unknown (no docs site); recommend removing the `https://google.com` placeholder or pointing to the repo | Metadata / cuda | Wrong URL ships to PyPI again; owner must supply the canonical docs/repo URL |
| A3 | License trove classifier must match the actual `LICENSE` file (not yet read this session) | Metadata | Mislabeled license classifier on PyPI |
| A4 | Exact RAPIDS 25.4 / NVIDIA driver minimums for the cuda11/12 note should be confirmed against the RAPIDS install selector at write time | cuda note | Note could state a stale driver floor |
| A5 | Perspective pinhole reference model (K·[R\|t]·X, cull Z≤0) is the intended model for `PerspectiveProjection`; the code's `@ pcd` + `.arr` contract depends on pchandler `_TransformArray.__matmul__` semantics not fully traced here | Pillar 3.3 | Reviewer's refutation probes resolve this empirically (D-05) |

**If any assumption is load-bearing for a plan decision, gate it behind a `checkpoint:human-verify` (A2, A3 especially — they ship to PyPI).**

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| ruff | QUAL-01 sweep | ✓ | 0.15.12 (PATH) | add to dev group via `uv add` |
| black | current formatter (to be replaced) | ✓ | 23.12.1 (venv) | — |
| pytest/coverage | validation | ✓ | pytest in venv | — |
| numpy/scipy/pydantic/joblib | math reviewers' probes | ✓ | 2.0.2 / 1.18.0 / 2.13.4 / 1.5.3 | — |
| matplotlib | `convert_to_image(colormap=)` path | ✗ | — | already guarded; move to `viz` extra (do not require) |
| pchandler / GSEGUtils | importing pc2img at all | ✓ | 2.1.x / 0.5.x (third_party symlinks) | — |

**Missing with no fallback:** none blocking. **Missing with fallback:** matplotlib (guarded; becomes an optional extra — that's the QUAL-01 fix, not a blocker).

## State of the Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| flake8 + isort + pyupgrade + black (4 tools) | ruff (lint+format, one tool) | 2023→ (ruff format GA) | D-09/D-11; siblings already migrated |
| black formatter | `ruff format` (black-compatible, 30× faster) | ruff 0.1+ | D-11 default: replace black |

**Deprecated/outdated in-repo:** `black ~= 23.10` (dev group) — supersede with ruff. The large commented-out code blocks (CONCERNS) are legacy refactor habit — delete (git preserves history).

## Sources

### Primary (HIGH confidence — verified this session)
- Codebase, all anchors re-opened file:line: `registry.py`, `strategies/projection.py`, `strategies/interpolation.py`, `strategies/triangulation.py`, `strategies/utils.py`, `strategies/registry.py`, `image_cache/disk_backed_image_data.py`, `util.py`, `features/{manager,registry,core,base_features,derivative_features,rrim}.py`, `core.py`, `tiled_generator.py`, `pyproject.toml`, `features/__init__.py`.
- Sibling templates: `/scratch/41_pchandler/pyproject.toml`, `/scratch/30_GSEGUtils/pyproject.toml` (`[tool.ruff]` config + metadata exemplars).
- Installed tool/lib versions probed from `.venv` and PATH (ruff 0.15.12; numpy 2.0.2; scipy 1.18.0; pydantic 2.13.4; joblib 1.5.3; black 23.12.1).

### Secondary (MEDIUM — official docs)
- ruff formatter (black-compatible, >99.9% line-identical): https://docs.astral.sh/ruff/formatter/ ; https://astral.sh/blog/the-ruff-formatter
- ruff configuration/settings: https://docs.astral.sh/ruff/configuration/ ; https://docs.astral.sh/ruff/settings/
- scipy `LinearNDInterpolator` (outside-hull → NaN fill via `find_simplex==-1`): https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.LinearNDInterpolator.html
- Topographic openness / differential openness = (pos−neg)/2: Yokoyama et al. (2002), "Visualizing Topography by Openness"; RRIM layering: Chiba et al. (2008), "Red relief image map."

### Tertiary (LOW — training knowledge, flagged)
- ESRI hillshade formula (`cos Z cos S + sin Z sin S cos(Az−Asp)`) — standard, cross-checked algebraically against the code.
- Pinhole perspective model (Hartley & Zisserman) — standard.

## Metadata

**Confidence breakdown:**
- ruff config / metadata correction: HIGH — grounded in installed ruff 0.15.12 + sibling templates verified this session.
- Design findings (anchors + seeds): HIGH — every anchor re-verified file:line; seeds observed directly in source.
- Math correctness criteria: HIGH for the reference formulas and the confirmed items (RRIM structure, hillshade equivalence, hull-NaN semantics); MEDIUM for the "needs empirical probe" items (perspective `@pcd` contract, azimuth wrap, aspect handedness) — deliberately handed to the adversarial workflow (D-05).
- cuda note: MEDIUM — driver-based logic sound; exact RAPIDS/driver floors flagged [ASSUMED] (A4).

**Research date:** 2026-07-10
**Valid until:** ~2026-08-10 for the code anchors (stable); ruff config valid until a major ruff release changes rule codes.
