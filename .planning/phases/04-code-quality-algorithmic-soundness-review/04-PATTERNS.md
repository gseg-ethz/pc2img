# Phase 4: Code Quality & Algorithmic Soundness Review - Pattern Map

**Mapped:** 2026-07-10
**Files analyzed:** 6 (5 mechanical FIX targets + 1 new findings doc)
**Analogs found:** 6 / 6

> Scope note: this is a **review phase**. The broad QUAL-02/03 audit does not create
> files — it produces `04-FINDINGS.md`. This pattern map covers only the concrete,
> mechanical **FIX** files the planner schedules (D-01) plus the findings-doc structure.
> All `file:line` anchors are cross-referenced to `04-RESEARCH.md` §Anchor Drift Report;
> re-grep before writing any line number into FINDINGS (Pitfall 1).

## File Classification

| Modified/New File | Role | Change Type | Closest Analog | Match Quality |
|-------------------|------|-------------|----------------|---------------|
| `pyproject.toml` | config | ruff block + metadata + dep collapse + `viz` extra | `/scratch/41_pchandler/pyproject.toml` | exact (sibling template) |
| `src/pc2img/registry.py` | factory | repair or delete `make_generator` | `src/pc2img/core.py:64-83` (`PointCloudImageGenerator.__init__`) | exact (call-site contract) |
| `src/pc2img/strategies/projection.py` | strategy module | guard `_TransformArray` module import | `src/pc2img/util.py:278-282` (matplotlib lazy-import guard) | role-match (lazy/guarded import) |
| `src/pc2img/features/__init__.py` | barrel | sync `__all__` with registered feature set | `src/pc2img/strategies/__init__.py:1-12` | exact (barrel pattern) |
| `src/pc2img/util.py` | util | delete dead `convert_to_image` (`:58`), keep `:231` | `src/pc2img/util.py:231-294` (the live def itself) | exact (self-analog) |
| `04-FINDINGS.md` | findings-doc | new structured findings log | CONTEXT.md D-06 entry schema | no code analog (schema template) |

---

## Pattern Assignments

### `pyproject.toml` (config — ruff block + metadata correction + dep collapse + `viz` extra)

**Analog:** `/scratch/41_pchandler/pyproject.toml` (sibling template; the good metadata exemplar).

**Current defects (verified this session):**
```toml
keywords = ["one", "two"]                    # :9   placeholder
classifiers = [
	"Programming Language :: Python :: 3"    # :15-17  minimal placeholder
]
dependencies = [
	"joblib ~= 1.5",                          # :21  ← keep this one
	...
	"joblib ~= 1.3",                          # :24  ← DUP, delete
]
documentation = "https://google.com"         # :45  placeholder URL (A2 — owner-gated)
```

**Sibling metadata pattern to mirror** (`/scratch/41_pchandler/pyproject.toml:9,18-22,90-95`):
```toml
keywords = ["LiDAR", "Pointclouds"]          # style anchor — pc2img gets a richer domain set
classifiers = [
	"Programming Language :: Python :: 3.12",
]
[project.urls]
homepage = "https://gseg.igp.ethz.ch/"
documentation = "https://pchandler.readthedocs.io/en/stable/"   # pattern for real docs URL
repository = "https://github.com/gseg-ethz/PCHandler.git"
```

**Sibling `[tool.ruff]` block** (`/scratch/41_pchandler/pyproject.toml:58-86`) — copy the rule
*families* but override per RESEARCH.md §Pillar 1 (D-11 forces **88**, not 120; drop `D`/pydocstyle):
```toml
[tool.ruff]
line-length = 120                            # ← pc2img MUST use 88 (D-11)
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "W", "B", "I", "C90", "D", "NPY"]   # ← pc2img drops "D", adds "UP"
ignore = ["E203"]
[tool.ruff.lint.pydocstyle]
convention = "numpy"                          # ← omit in pc2img (no "D")
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D100", ...]                    # ← pc2img exempts the 4 __init__ barrels for F401
```
Use the exact recommended pc2img config block quoted in **RESEARCH.md §Pillar 1** (lines 147-175) —
it is already tailored (88-col, `select = ["E","F","W","I","B","C90","UP","NPY"]`,
`extend-select = ["ERA001"]`, per-file-ignores for the four `__init__.py` barrels). Do not re-derive it.

**PEP 735 placement** — pc2img puts tooling in `[dependency-groups]`, NOT `[project.optional-dependencies]`
(`pyproject.toml:66-70`). Add ruff there, remove black (D-11 default):
```toml
[dependency-groups]
dev = ["black ~= 23.10", "pytest ~= 9.1", ...]   # ← swap "black ~= 23.10" → "ruff ~= 0.15"
```

**`viz` extra** — matplotlib is undeclared; add alongside the existing `rrim`/`cudaXX` extras
(`pyproject.toml:51-64`), NOT as a hard dependency (the guard at `util.py:278-282` already tolerates absence):
```toml
[project.optional-dependencies]
viz = ["matplotlib ~= 3.9"]
```

**Post-edit:** `uv sync` (RESEARCH.md §Runtime State Inventory — removing black changes the resolved env).
Verify: `python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert d['project']['keywords']!=['one','two']"`.

**Owner-gated [ASSUMED] items — do NOT auto-pick** (RESEARCH.md A2/A3): the real `documentation` URL
and the `License :: OSI Approved` trove classifier ship to PyPI. Gate behind `checkpoint:human-verify`.

---

### `src/pc2img/registry.py` (factory — repair or delete `make_generator`)

**Analog:** `src/pc2img/core.py:64-83` — the real `PointCloudImageGenerator.__init__` signature.

**Current broken state** (`registry.py:7-16`):
```python
def make_generator(pcd, proj_name, proj_cfg, interp_name, interp_cfg):
    proj = PROJECTIONS.create(proj_name, **proj_cfg)
    interp = INTERPOLATIONS.create(interp_name, **interp_cfg)
    return PointCloudImageGenerator(pcd, proj, interp)   # ← 3 positional args
```

**The contract it violates** (`core.py:66-74`):
```python
@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=False)
def __init__(
    self,
    pcd: PointCloudData,
    img_res: ImgResLike,          # ← 2nd positional; make_generator has NO img_res
    proj: ProjectionStrategyLike,
    interp: InterpolationStrategyLike,
    lazy_disk_cache_config: LazyDiskCacheConfigLike = None,
) -> None:
```
`make_generator(pcd, proj, interp)` → `proj` lands in `img_res`, `interp` lands in `proj`,
`interp`/`img_res` missing. The factory cannot produce a valid generator.

**Two mechanical options (planner picks lowest-churn):**
1. **Delete** — no live caller was found in `src/` or `tests/` (RESEARCH.md anchor #1). Also drop the
   `make_generator` re-export if any barrel lists it (grep first).
2. **Repair** — add an `img_res` parameter and call with keywords mirroring the ctor:
   `PointCloudImageGenerator(pcd, img_res=img_res, proj=proj, interp=interp)`.

**Smoke check after either:** `python -c "import pc2img.registry"`.

---

### `src/pc2img/strategies/projection.py` (strategy module — guard `_TransformArray` import)

**Analog:** `src/pc2img/util.py:278-282` — the in-repo lazy-import-with-guard idiom (matplotlib).

**Current fragile state** (`projection.py:12`):
```python
from pchandler.geometry.transforms import _TransformArray   # module-level private import
```
Used **only** as a type annotation at `projection.py:192` (`PerspectiveProjection.__init__`,
`NDArray | _TransformArray`). A pchandler drop/rename breaks importing the *entire* projection module —
including the shipped `SphericalProjection`/`OrthographicProjection` (RESEARCH.md seed A).

**In-repo guard pattern to mirror** (`util.py:278-282`):
```python
if colormap is not None:
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError("Colormap requires matplotlib") from e
```

**Recommended mechanical fix** (mirror the lazy/guarded shape; the symbol is annotation-only, so a
`TYPE_CHECKING` guard is the lowest-churn form and keeps pyright happy):
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pchandler.geometry.transforms import _TransformArray
```
Because the annotation at `:192` is only evaluated statically, this removes the runtime import entirely.
If a runtime reference is later found, fall back to the `try/except ImportError` form (util.py analog) or
import inside `PerspectiveProjection.__init__`. Note projection.py already imports `TYPE_CHECKING`-friendly
typing at `:2`; confirm before adding.

**Smoke check:** `python -c "import pc2img.strategies.projection"`.

---

### `src/pc2img/features/__init__.py` (barrel — sync `__all__` with registered features)

**Analog:** `src/pc2img/strategies/__init__.py:1-12` and `image_cache/__init__.py:1-4` — the curated-barrel
+ import-side-effect-registration pattern (importing the submodule runs the `@FEATURES.register` decorators).

**Current out-of-sync state** (`features/__init__.py:1-9`):
```python
__all__ = [
    "FeatureManager",
    "RangeFeature", "ScalarFieldFeature",
    "GradientFeature", "NormalizedFeature", "LogFeature", "HillshadeFeature", "AverageFeature",
]
from .manager import FeatureManager
from .base_features import RangeFeature, ScalarFieldFeature
from .derivative_features import GradientFeature, NormalizedFeature, LogFeature, HillshadeFeature, AverageFeature
```

**Registered feature classes actually present** (`grep -n "^class" features/*.py`, all decorated
`@FEATURES.register`):
- `base_features.py`: `RangeFeature`, `ScalarFieldFeature`
- `derivative_features.py`: `GradientFeature`, `SobelFeature`, `NormalizedFeature`, `LogFeature`,
  `HillshadeFeature`, `AverageFeature`, `SumFeature`, `SquareFeature`, `RootFeature`, `NormFeature`,
  `ClipPercentileFeature`, `MultiScaleGradientFeature`, `OcclusionAwareMultiScaleGradientFeature`
- **Missing from the barrel:** `SobelFeature`, `SumFeature`, `SquareFeature`, `RootFeature`,
  `NormFeature`, `ClipPercentileFeature`, `MultiScaleGradientFeature`, `OcclusionAwareMultiScaleGradientFeature`.

**Fix:** add the missing derivative-feature imports + `__all__` entries, mirroring the barrel shape in
`strategies/__init__.py` (which lists every registered strategy). This is documentation/hygiene only —
registration already happens via the module import side effect; it does not fix a functional break
(RESEARCH.md seed C).

**Deliberate exclusion — do NOT add RRIM features to this barrel.** `rrim.py`'s `RRIMPackFeature`,
`RRIMFeature`, `RRIMComponentFeature` (`@FEATURES.register` at `rrim.py:470,500,535`) are **opt-in by
design** — they register only on explicit `import pc2img.features.rrim` (documented at
`rrim.py:335-345` and `pyproject.toml:60-63`). Importing them in the barrel would defeat the opt-in
gate and change registration behavior (out of scope for a hygiene fix).

**Smoke check:** `python -c "import pc2img.features; import pc2img.features as f; assert set(f.__all__) <= set(dir(f))"`.

---

### `src/pc2img/util.py` (util — delete dead `convert_to_image` at `:58`)

**Analog:** the live definition itself, `src/pc2img/util.py:231-294` — this is a self-analog (keep the
second def, delete the first).

**Dead def to remove** (`util.py:58-~108`): the first `convert_to_image` (positional-arg signature,
no `*`) is shadowed by the keyword-only def at `:231`. It references `plt` at `:76` with **no `plt`
import in scope** → would `NameError` if ever reached (it is unreachable, so latent).

**Live def to keep** (`util.py:231-294`): keyword-only signature, integer-scaling branch, all-finite
guard, and the **correct** lazy matplotlib guard at `:278-282`. This is the canonical version; the
executor deletes lines `:58` through the end of the first def (verify the exact end line by re-reading
before editing — the first def runs from `:58` to just before `gaussian_kernel`... confirm boundaries).

**Cross-check:** `ruff check --select F811 src/pc2img/util.py` should report the redefinition **before**
the fix and be **clean after** (RESEARCH.md §QUAL-01 sweep — F811 is the mechanical detector for this).

---

### `04-FINDINGS.md` (findings-doc — NEW, no code analog)

**Structural template:** CONTEXT.md **D-06** (lines 65-71) — the required per-entry schema. Every entry MUST carry:

| Field | Source |
|-------|--------|
| stable id | Claude's discretion; most-severe-first ordering (D-06, CONTEXT L101) |
| `file:line` location | RESEARCH.md §Anchor Drift Report (re-grep before writing — Pitfall 1) |
| one-line defect statement | RESEARCH.md §Pillar 2/3 tables |
| why-it's-wrong | reference formula (math) / contract (design) |
| minimal repro (inputs → wrong output) | D-05 numeric probes |
| severity | Claude's discretion taxonomy (D-06) |
| pillar (design / math / hygiene) | RESEARCH.md Responsibility Map |
| proposed proving-test sketch | becomes the Phase-5 BUG-05 test |

**Seed content (do not re-derive):** RESEARCH.md §Pillar 2 (4 anchors + 12 seeds A-L) and §Pillar 3
(math paths 3.1-3.6) already supply defect statements, reference formulas, and probe sketches. The four
named anchors (broken `make_generator`, divergent registries, in-place raster mutation, missing
dependency-cycle guard) MUST appear if still present (D-04).

**Cross-reference seed:** the Phase-3 pytest suite (15 passed / **11 xfailed**) — the xfail *reasons*
already encode several known bugs (BUG-01 ortho arity, BUG-03 `extend_cache_paths`, BUG-04 rrim docstring).
Pull those reasons in rather than re-deriving (CONTEXT L177-178, RESEARCH.md §Pillar 2 seeds G/I).

**Precision note (CONTEXT `<specifics>` L206-209):** the `__array_ufunc__` entry must state the *observed*
`TypeError: exceptions must derive from BaseException` and the *intended* `NotImplementedError` — Phase 5's
proving test asserts the exact type (RESEARCH.md Pitfall 4).

---

## Shared Patterns

### Lazy / guarded import (applies to: `projection.py` fix, and the log-only pchandler-coupling findings)
**Source:** `src/pc2img/util.py:278-282`
```python
try:
    import matplotlib.pyplot as plt
except Exception as e:
    raise RuntimeError("Colormap requires matplotlib") from e
```
For annotation-only symbols (the `_TransformArray` case) prefer the even-lighter `if TYPE_CHECKING:`
guard — no runtime import at all.

### Curated barrel + import-side-effect registration (applies to: `features/__init__.py` fix)
**Source:** `src/pc2img/strategies/__init__.py:1-12`, `image_cache/__init__.py:1-4`
Every barrel declares `__all__` first, then imports submodules; the submodule import *is* the strategy/feature
registration mechanism. F401 would flag these re-exports as unused — the recommended ruff config exempts the
four `__init__.py` barrels (RESEARCH.md §Pillar 1, Pitfall 2). Never blanket-`# noqa` inline.

### None-sentinel coercion (referenced by FINDINGS, not fixed here)
**Source:** `src/pc2img/core.py:34-41` (`coerce_lazy_cfg`) + `:73` (`= None` default)
The `coerce-null-lazy-disk-cache-config` finding is **LOG-only** (D-02, behavioral → Phase 5). FINDINGS
should point at this existing pattern as the eventual fix path — do not apply it in Phase 4.

### F811 / ruff as the mechanical detector (applies to: dup `convert_to_image`)
**Source:** RESEARCH.md §QUAL-01 sweep
`ruff check --select F811,F401,F841 src/` is the ground-truth for the dead-code FIX items; the pyproject
`joblib` TOML-list dup is *not* ruff-detectable — collapse it by hand.

## No Analog Found

None. Every FIX file has a concrete in-repo or sibling-template analog. The one new file
(`04-FINDINGS.md`) has no *code* analog by nature — its structure comes from the CONTEXT.md D-06 schema
and its content from the RESEARCH.md Pillar tables.

## Metadata

**Analog search scope:** `src/pc2img/` (all subpackages), `pyproject.toml`, sibling
`/scratch/41_pchandler/pyproject.toml` + `/scratch/30_GSEGUtils/pyproject.toml`.
**Files scanned:** 11 (registry, core, projection, util, 4 `__init__.py` barrels, features/*, pyproject, sibling pyproject).
**Pattern extraction date:** 2026-07-10
