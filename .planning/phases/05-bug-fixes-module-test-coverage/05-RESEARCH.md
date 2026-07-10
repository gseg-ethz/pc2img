# Phase 5: Bug Fixes & Module Test Coverage - Research

**Researched:** 2026-07-10
**Domain:** Python scientific library hardening — correctness bug fixes with proving tests, GSEGUtils primitive consolidation, registry unification, and pytest module coverage
**Confidence:** HIGH (entirely codebase-grounded; every claim verified against live source in `/scratch/31_pc2img`, `/scratch/30_GSEGUtils`, `/scratch/41_pchandler` and the installed pchandler 2.1.0)

> This phase installs **no new external packages**. All findings are verified via direct
> source reads and the installed dependency surface — not web search (all search providers
> are disabled in `.planning/config.json`). Provenance tags: `[VERIFIED: <file:line>]` =
> confirmed in live source this session; `[ASSUMED]` = judgment not mechanically proven.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Two-bucket work-list.** Every finding not re-dispositioned below is a **genuine fix**
(apply per its `04-FINDINGS.md` proving-test sketch, test-first `xfail`→`pass`). Three
findings are **kept-behavior** (M-06, M-10, M-11): default behavior is intentional and
stays — they get a *characterization test* + owner rationale + future-improvement log, NOT
a fix. Downstream agents must not "correct" kept-behavior findings.

- **D-01: PerspectiveProjection — fix all three findings now.** M-02 (mask `Z_c ≤ 0`), M-03
  (add camera-translation term → full `K·[R|t]·X`), M-04 (remove dead `project_raw`
  override), each with a proving test. M-03 is feature-completion (upholds Phase-4 D-08).
- **D-02: LOW latent/structural/typing — fix everything.** DSN-08 (visited-set cycle guard),
  DSN-10 (import from `pc2img.core`, not the barrel), DSN-11 (`type[...] | None`). DSN-09
  (pickle) resolved by construction via the store consolidation (D-05).
- **D-03: PERF-linked halves — fix correctness AND land parameterization.** M-08 float32 fix;
  PERF-02 (reduced-precision opt-in) and PERF-03 (Delaunay thresholds) pulled forward from v2
  as opt-in parameters. For M-06 superseded by D-07 — the *default* never changes; only params
  are added.
- **D-04: BUG-02 / DSN-02 → reparent, don't patch.** Make `DiskBackedImageData` a thin
  subclass of `GSEGUtils.DiskBackedNDArray` (keep only `to_uint8()` + the `ndim∈(2,3)`
  assertion), **delete** the broken `__array_ufunc__` → inherit GSEGUtils' working one.
  Arithmetic works, returning plain ndarrays. Proving test asserts a *correct arithmetic
  result* (supersedes the earlier "clean-raise" instinct).
- **D-05: DSN-09 / store → adopt `GSEGUtils.DiskBackedStore`.** Replace
  `DiskBackedImageStore`'s pickle sink with `DiskBackedStore[DiskBackedImageData]` (hardened
  `.npy` + `.meta.json`, `allow_pickle=False`). DSN-09 eliminated by construction. Cache
  format `.pkl`→`.npy` (BC-01). **Research flag:** map the store's public surface onto
  `DiskBackedStore`; if a GSEGUtils change is required, that trips the dependency-approval gate.
- **D-06: M-06 (Delaunay culling) → KEPT-BEHAVIOR.** Intentional interior-culling heuristic
  (reduced artifact noise in a downstream optical-flow task). Keep as default; expose
  area/aspect-ratio thresholds as opt-in params whose **defaults equal today's values** (zero
  behavior change; satisfies PERF-03). Characterization test. Log over-culling-on-anisotropic
  as future improvement.
- **D-07: M-10 (GradientFeature spacing `100`) → KEPT-BEHAVIOR.** Keep `100` as default; expose
  as a `pixel_size`-style parameter (default `100`, no output change). Characterization test.
  Log "principled gradient spacing" as future investigation.
- **D-08: M-11 (Hillshade aspect handedness) → KEPT-BEHAVIOR.** pc2img rasters carry NO
  north-up guarantee, so "fix to ESRI compass" is ill-defined. Keep current aspect default;
  document the non-north-up convention; add a **self-consistency** test (not ESRI-compass
  truth). Defer an "align north" option.
- **D-09: M-08 (nanconv float16 overflow) → genuine fix.** Accumulate/divide in float32.
  PERF-02's reduced-precision opt-in may ride along as a parameter.
- **D-10: Behavioral-sufficiency + ratchet the floor.** Meaningful behavioral coverage of
  TEST-03..06 plus every proving/characterization test; then re-measure and ratchet CI
  `--cov-fail-under` up to the new baseline. No fixed-% chase. (Current floor 35%, baseline 37%.)
- **D-11: Shared synthetic fixture factory in a new `tests/conftest.py`.** Real minimal
  `PointCloudData` from synthetic arrays (`PointCloudData(xyz)`; `**PointCloudDataKW` attaches
  scalar fields). Deterministic, fast, NO committed binaries. Lightweight duck-type stubs
  (`.xyz`/`.nbPoints`, `FakeProjection`) only where a full PCD is genuinely heavy. pchandler's
  own fixtures are NOT reusable.
- **D-12: Test-first per finding.** Genuine fixes: write proving test as `xfail` first, then
  fix to flip to `pass`. Kept-behavior findings: passing characterization tests from the
  start. Also flip existing xfails (`test_point_cloud_image_generator.py:35`; the
  `test_disk_backed_image_data.py` xfails at :50,:115,:155,:175,:241).
- **D-13: Wave-based plan grouped by source file.** Standard `gsd-plan-phase` →
  `gsd-execute-phase`. Group findings by source file; fixes run sequentially within a file
  (no worktree collisions), waves parallelize across non-overlapping files. TEST-03..06
  authoring parallelizes by module.
- **D-14: DSN-05 registries → unify now.** Single registry protocol/adapter across
  `StrategyRegistry` and `FeatureRegistry` with one miss-exception type. Fold in the
  `match()`-without-instantiation sub-fix (`dependencies_for(params)` classmethod). Proving
  tests both families. Miss-exception contract change → BC-01 entry.
- **D-15: M-05 (spherical seam) → consistency guard + defer the system fix.** Add `crosses_pi`
  detection to BOTH `project_raw` and `inverse_projection` that raises a clear error mirroring
  pchandler's `FoV.tile()` split-first message. Test asserts it raises on a wrapping FoV. Real
  seam handling DEFERRED. Behavior-change: a single untiled wrapping-FoV cloud now raises
  instead of silently producing reversed columns (accepted).
- **D-16: M-13 (RRIM ray sampling) → defer/log.** Document + log as future improvement; no fix.
- **D-17: BC-01 → accumulate a running breaking-change note during Phase 5.** Append an entry
  as each behavior/format/error-type change lands, for Phase 6's BC-01 to consume.

### Claude's Discretion
- Exact wave grouping and plan-unit boundaries by file (D-13).
- Whether M-06/M-10 threshold/spacing params land as constructor kwargs or via the DSL,
  provided defaults are unchanged.
- Whether M-05's guard is a shared helper vs inlined in both methods.
- Whether the store-consolidation mapping (D-05) keeps `DiskBackedImageStore`'s class/API as a
  thin wrapper over `DiskBackedStore` or replaces it — planner's call after the API-gap analysis.

### Deferred Ideas (OUT OF SCOPE)
- Spherical-seam system fix (cross-repo; likely its own milestone, combined workspace).
- M-06 over-culling refinement; M-10 principled gradient spacing; M-11 "align north" option;
  M-13 near-axis ray-sampling fidelity.
- Full `DiskBackedImageStore` → `DiskBackedStore` API convergence (if D-05 lands a thin wrapper).
- v2 PERF-01 (triangulation keying), PERF-04 (`_triangulation_precalc` growth bound).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUG-01 | `OrthographicProjection.project_raw` correct arity + column indexing | §M-01 anchor: `projection.py:176-189`. Fix = return 4-tuple `(coords, mask, mins, maxs)` + `pcd.xyz[mask][:, cols]`. Proving test: parametrize plane∈{xy,yz,xz}, assert coords == `xyz[mask][:, cols]` normalized. |
| BUG-02 | `DiskBackedImageData.__array_ufunc__` correct (arithmetic or proper `NotImplementedError`) | D-04 reparent onto `DiskBackedNDArray` (`disk_backed_ndarray.py:98-138` ships the working ufunc). Proving test asserts a *correct arithmetic result*. |
| BUG-03 | `TIGSettings.extend_cache_paths` preserves `interp_kwargs` | §DSN-01: `tiled_generator.py:66-68` stores `dict.update()`→`None`. Fix = build dict then assign. |
| BUG-04 | `rrim.py` module `__doc__` populated (+E402×9 cleanup) | §BUG-04: module-level imports after docstring/`__all__` trigger E402; reorder so the docstring is first statement and `__doc__` is set. |
| BUG-05 | Every QUAL-03 correctness bug fixed with a proving test | The 24 findings in `04-FINDINGS.md`. See §Wave Grouping & Collision Map + §Common Pitfalls. |
| TEST-03 | Projection & interpolation math covered | §Fixture Needs: projection needs real PCD; interpolation math needs **zero PCD** (pure arrays). |
| TEST-04 | Derivative features + feature-name DSL covered | §Fixture Needs: `compute(_, fetch)` ignores pcd — dict-backed `fetch` lambda suffices; DSL needs no PCD. |
| TEST-05 | Orchestration (`FeatureManager`, `TiledPointCloudImageGenerator`) covered | §Fixture Needs: needs real minimal PCD (base-feature compute reads `pcd.spher`/scalar fields); tiled path is heaviest. |
| TEST-06 | `util.py` (`convert_to_image`, `replace_nan`, `to_gray`, `nanconv`) covered | §Fixture Needs: pure array functions — **zero PCD**. |
</phase_requirements>

## Summary

Phase 5 is a **hardening + coverage** phase with almost no external-research surface: the WHAT
is fully specified by `04-FINDINGS.md` (24 findings) and the HOW is locked by CONTEXT.md
D-01..D-17. The research value is in **de-risking the four behavior-changing consolidations**
(D-04 reparent, D-05 store adoption, D-14 registry unification, D-15 seam guard) and **sizing
the test-authoring work** by distinguishing findings that need real point clouds from those
that are pure-array/duck-stub testable.

The single most consequential discovery: **the D-05 store consolidation hits a hard blocker in
GSEGUtils that trips the dependency-approval gate.** `DiskBackedStore._load_entry` reconstructs
offloaded entries through a **private, closed allow-list** (`_LAZY_DISK_CACHE_CLASS_REGISTRY`,
`disk_backed_store.py:61-79`) that contains only `"DiskBackedNDArray"`. A reparented
`DiskBackedImageData` offloaded to disk and reloaded raises `ValueError: Unknown
lazy_disk_cache_class 'DiskBackedImageData'`. This is exactly why the in-repo precedent
(`interpolation.py`, which stores `DiskBackedNDArray`) works but the image store will not, "for
free." The planner MUST choose between a GSEGUtils change (clean, gated) and a pc2img-side
import-time registration (zero-approval, private-coupling). See §D-05.

Everything else is well-scoped and low-risk. The registry unification (D-14) breaks **no
existing tests** (grep confirms zero `pytest.raises(KeyError/RuntimeError)` in `tests/`) and a
dual-inheritance miss-exception `class RegistryLookupError(KeyError, RuntimeError)` keeps every
existing `except KeyError` caller working. The seam guard (D-15) has a clean pchandler API to
consume (`FoV.crosses_pi`). Coverage authoring is smaller than it looks: only TEST-03
(projection) and TEST-05 (orchestration) genuinely need the conftest PCD factory.

**Primary recommendation:** Sequence the phase as (Wave 0) conftest factory + failing proving
tests; (Wave A, parallel by file) the pure-math file fixes — `util.py`, `derivative_features.py`,
`interpolation.py`, orthographic/spherical/perspective in `projection.py`; (Wave B) the two
consolidation clusters — `image_cache/` reparent+store (D-04/D-05) and registry unification
(D-14); (Wave C) orchestration fixes + coverage authoring + xfail flips + floor ratchet. Resolve
the D-05 GSEGUtils gate decision **before** planning Wave B.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Bug fixes to projection/interpolation math | Strategies layer (`strategies/`) | — | Pure algorithm layer; no orchestration/cache coupling |
| Derivative-feature + DSL fixes | Features layer (`features/`) | — | Feature math + regex name grammar are self-contained |
| Disk-cache format + arithmetic surface (D-04/D-05) | Storage layer (`image_cache/`) | GSEGUtils primitives | Reparent onto GSEGUtils; the on-disk codec is owned by GSEGUtils |
| Registry unification (D-14) | Registry infra (`strategies/registry.py`, `features/registry.py`) | Orchestration (callers) | Cross-cutting; validators + FeatureManager consume both registries |
| Seam guard (D-15) | Strategies layer (`projection.py`) | pchandler `FoV` | pc2img consumes pchandler's existing seam-tracking API |
| Test coverage (TEST-03..06) | Test layer (`tests/`) | conftest factory | Behavioral sensors over each module; fixture factory is shared infra |
| Config coercion fix (DSN-06) | Orchestration (`core.py`) | — | API-boundary pydantic coercion |

## Standard Stack

### Core (all already installed — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | 2.3.5 (`~=2.0`) | Array math under every finding | Project-wide; forced by pchandler 2.x |
| scipy | 1.18.0 (`~=1.14`) | `Delaunay`, `LinearNDInterpolator`, `convolve2d`, `ndimage` | Interpolation + smoothing math |
| pytest | `~=9.1` | Test runner | Locked in Phase 3 (D-14) |
| pytest-cov | `~=5.0` | Coverage measurement | Phase 3 TEST-02 baseline |
| coverage | `~=7.0` | Branch coverage backend | Phase 3 config |
| pchandler | 2.1.0.post2 | `PointCloudData`, `FoV`, filters | Input layer; provides seam API + PCD factory |
| GSEGUtils | 0.5.2.post2 | `DiskBackedNDArray`, `DiskBackedStore` | D-04/D-05 consolidation targets |

**Verified versions** `[VERIFIED: .venv import]`: pchandler `2.1.0`, `PointCloudData.__init__`
signature `(self, /, xyz: Array_Nx3_Float_T | None = None, **kwargs: Unpack[PointCloudDataKW])`.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Deterministic parametrized numpy tests | `hypothesis` (property-based) | hypothesis adds a new dev dependency and contradicts D-11's determinism mandate; the legitimacy seam flagged it `SUS` this session (see audit). Parametrized seeded numpy tests give equivalent property coverage at zero dependency cost. **Recommend against adding hypothesis.** |
| scipy `LinearNDInterpolator` as test oracle | Hand-rolled reference | scipy is already a dep and is the authoritative "NaN iff outside hull" oracle for the M-06 characterization test — use it. |

## Package Legitimacy Audit

> This phase installs **no new external packages.** All fixes and tests use the existing
> installed stack. The only candidate considered — `hypothesis` for property-based tests — is
> **not recommended** (see Alternatives). Recorded here for completeness only:

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| hypothesis | PyPI | `SUS` (seam returned `too-new`/`no-repository`/`unknown-downloads` — a probe/metadata artifact; hypothesis is a mature 10+yr library, but the signal is recorded per protocol) | **NOT ADDED** — deterministic parametrized tests used instead |

**Packages removed due to [SLOP]:** none. **Packages flagged [SUS] and adopted:** none.
If the planner or owner later opts into hypothesis, gate the install behind a
`checkpoint:human-verify` task (it also requires owner approval as a dependency edit).

## D-05 — Store API-Gap Analysis (HIGHEST VALUE)

`DiskBackedImageStore` (`image_cache/disk_backed_image_store.py`) vs
`GSEGUtils.DiskBackedStore` (`disk_backed_store.py`). Member-by-member mapping:

| pc2img member | line | DiskBackedStore equivalent | Gap class |
|---------------|------|---------------------------|-----------|
| `__init__(*, config)` | :18-40 | `__init__(*, config, factory, value_type=None, validator=None)` | **EXTEND** — must supply `factory=DiskBackedImageData`, `value_type=DiskBackedImageData` |
| `__getitem__` (`pickle.load`) | :42-54 | `__getitem__` → `_load_entry` (codec) | **SEMANTIC + BLOCKER** — codec load, but class-registry gap (below) |
| `__setitem__` (isinstance check) | :56-59 | `__setitem__` → `_check_T` | 1:1 via `value_type` |
| `__delitem__` / `__iter__` / `__len__` / `__repr__` | :61-71 | present | 1:1 (repr text differs) |
| `__contains__` | (inherited) | explicit `__contains__` (:220) | 1:1 (both check tracked keys incl. offloaded) |
| `add_image_to_store(name, data, *overrides)` | :76-96 | `add_data_to_store(key, data, *overrides)` | **RENAME + SEMANTIC** — `add_data_to_store` raises `KeyError` if key exists (:273-274); `add_image_to_store` **overwrites silently** |
| `image_data` property | :98-100 | `store` property (:296) | **RENAME** |
| `cache_dir` property (`Path \| None`) | :102-104 | `cache_dir` property (`Path`) | 1:1 (return type narrows to non-None) |
| `keys` / `values` / `items` | :106-116 | present (:305-315) | near-1:1 (`values`/`items` yield `Optional[T]`) |
| `offload(features=None)` | :118-135 | `offload(keys=None, pickle_container=False)` | **RENAME param** `features`→`keys`; per-entry `obj.offload()` path matches |
| `offload_image_data_to_disk(features)` | :137-153 | `offload(keys, pickle_container=True)` | **SEMANTIC MAP** — the `.pkl`-dump-then-clear becomes codec-write-then-clear |
| `_get_pickle_path` | :73-74 | (internal, `_get_npy_path` / `_get_meta_path`) | removed from public surface |
| `__getstate__` / `__setstate__` | :155-168 | present (:468-501) | 1:1 semantics; format `.pkl`→`.npy`+`.meta.json` |

### The blocker: closed class allow-list (trips the dependency gate)

`DiskBackedStore._store_entry` writes `type(entry).__name__` into `meta["lazy_disk_cache_class"]`
`[VERIFIED: disk_backed_store.py:386]`. On reload, `_load_entry` calls
`_resolve_lazy_disk_cache_class(meta["lazy_disk_cache_class"])` `[VERIFIED: :455]`, which looks
the name up in a **module-private, closed dict**:

```python
_LAZY_DISK_CACHE_CLASS_REGISTRY: dict[str, type[LazyDiskCache]] = {"DiskBackedNDArray": DiskBackedNDArray}
```
`[VERIFIED: disk_backed_store.py:61-79]` — no `importlib` fallback, no public registration hook
(grep confirmed: only `DiskBackedNDArray` is exported; no `register_*` function exists).

**Consequence:** offloading a reparented `DiskBackedImageData` and reloading it raises
`ValueError: Unknown lazy_disk_cache_class 'DiskBackedImageData'`. This is a **hard failure on
the shipped offload→reload path** — the exact path FeatureManager exercises when a raster is
offloaded and re-fetched. The in-repo precedent (`interpolation.py:162-165`) never hits this
because it stores `DiskBackedNDArray`, which **is** in the allow-list.

### Resolution options (planner MUST pick one before Wave B)

| Option | What | Dependency gate? | Assessment |
|--------|------|------------------|------------|
| **A — GSEGUtils change** | Add a public registration hook (e.g. `register_lazy_disk_cache_class(cls)` or a `class_registry=` param on `DiskBackedStore.__init__`) so pc2img registers `DiskBackedImageData` | **YES — trips the approval gate** (owner is the GSEGUtils author, so approval is lightweight but must be **explicit** per project constraint) | Cleanest/long-term correct; makes the allow-list an extension point instead of a closed set |
| **B — pc2img import-time registration** | In `image_cache/__init__.py`, do `GSEGUtils.lazy_disk_cache.disk_backed_store._LAZY_DISK_CACHE_CLASS_REGISTRY["DiskBackedImageData"] = DiskBackedImageData` | No (no GSEGUtils *source* edit) | Zero-approval, one line; but couples to a **private** underscore global that could change without notice. Reconstruct path `cls(arr, **kwargs)` works for `DiskBackedImageData` (ndim assertion runs on the reloaded raster) |
| **C — subclass + override `_load_entry`** | pc2img `DiskBackedImageStore` overrides `_load_entry` to resolve its own class | No | Requires copying ~40 lines of hardened codec logic — fragile, defeats the "adopt the hardened codec" goal |
| **D — store `DiskBackedNDArray`, not `DiskBackedImageData`** | Keep raw arrays in the store; move `to_uint8` to a store/free helper | No | Contradicts D-04 (which wants `DiskBackedImageData` kept with `to_uint8`); loses the value-typed entry |

**Recommendation:** Present **A as the principled fix** and **B as the zero-approval fallback**
to the owner. Because the project constraint says GSEGUtils changes need explicit approval and
the owner authored GSEGUtils, the cheapest correct path is **Option A** — a tiny, well-scoped
GSEGUtils enhancement (public class-registration) that the owner approves in the same session.
Option B ships without a gate but leaves private-API coupling that a future GSEGUtils release
could break silently. **This decision gates D-04+D-05 planning and must be surfaced at plan
time, not discovered mid-execution.** `[VERIFIED: disk_backed_store.py:61-79,386,455]`

### WRAPPER vs REPLACE (Claude's discretion per CONTEXT.md)

**Recommend WRAPPER.** Keep `pc2img.image_cache.DiskBackedImageStore` as a thin subclass of
`DiskBackedStore[DiskBackedImageData]` that: (1) in `__init__` supplies
`factory=DiskBackedImageData, value_type=DiskBackedImageData`; (2) re-aliases the legacy method
names FeatureManager and the public barrel depend on — `add_image_to_store`→`add_data_to_store`,
`image_data`→`store`, `offload_image_data_to_disk`→`offload(pickle_container=True)`,
`offload(features=...)`→`offload(keys=...)`; (3) registers `DiskBackedImageData` per the D-05
gate decision.

Rationale: FeatureManager calls only `add_image_to_store` (`manager.py:59`), `keys`
(`:47`), `in`/`__contains__` (`:62`), `__getitem__` (`:63,65`), and `cache_store.cache_dir`
(via the xfail test). Keeping these names stable = minimal BC surface and preserves
`image_cache/__init__.py __all__ = ["DiskBackedImageData", "DiskBackedImageStore"]`. REPLACE
(delete the class, repoint FeatureManager at `DiskBackedStore` directly) is viable but edits
more call sites and mutates the public barrel — larger BC-01 delta for no functional gain.

**Overwrite-vs-raise semantic caveat:** `add_data_to_store` raises `KeyError` on an existing key
`[VERIFIED: disk_backed_store.py:273-274]`; `add_image_to_store` overwrites `[VERIFIED:
disk_backed_image_store.py:86]`. FeatureManager's normal flow guards with `if name in cache`
before submit (`manager.py:62`), so overwrite is not exercised on the happy path — but the
wrapper's `add_image_to_store` alias should either preserve overwrite semantics (pre-`del` then
add) or the planner must accept raise-on-resubmit as a (minor) BC change. Recommend preserving
overwrite to avoid a behavior change on generator reuse.

## D-04 — DiskBackedImageData Reparent

`GSEGUtils.DiskBackedNDArray(data: NDArray, **settings: Unpack[LazyDiskCacheKw])`
`[VERIFIED: disk_backed_ndarray.py:49]`. Buffer stored as `self._data`; `_shape`/`_dtype`
cached. It ships the **working** `__array_ufunc__` (unwrap `DiskBackedNDArray` inputs → delegate
to the ufunc → return a plain ndarray) `[VERIFIED: disk_backed_ndarray.py:98-138]`.

**A reparented `DiskBackedImageData` is ~10 lines.** Override only:
- `__init__` — run the `ndim∈(2,3)` assertion (`image_data.ndim in (2,3) and (ndim==2 or
  shape[-1]==3)`, `[VERIFIED: disk_backed_image_data.py:24]`) then `super().__init__(image_data,
  **settings)`.
- `to_uint8(pre_processing_func=None)` — the only unique method; keep the
  `@LazyDiskCache.ensure_loaded` decorator and the `partial(convert_to_image,
  replace_nan_with="max", normalize=False)` default. **Naming migration:** it currently reads
  `self._image_data` (`:44`); after reparenting the buffer is `self._data` — reference
  `self._data` (or the inherited `.data` property).

**Inherit (delete the pc2img overrides):** `__array__`, `__array_ufunc__` (the broken
`raise NotImplementedError` at `:55-56` — DELETE), `__getitem__`, `data` property,
`_describe_buffer`, `_drop_buffer`, `_describe_shape_dtype`, `_set_buffer`. Do **not** re-declare
`self._image_data` (the inherited buffer-hooks use `_data`/`_shape`/`_dtype`).

**`__array_priority__ = 1000`** (`disk_backed_image_data.py:17`) is not set on `DiskBackedNDArray`
— recommend dropping it for parity unless a test asserts operator-dispatch precedence against a
bare ndarray. `[ASSUMED]` (no test currently references it; verify at fix time).

**Proving test (BUG-02):** `a = DiskBackedImageData(arr2d); b = DiskBackedImageData(arr2d);
np.testing.assert_array_equal(a + b, arr2d + arr2d)` and assert the result is a plain
`np.ndarray` (not a `DiskBackedImageData`). This is the D-04 "correct arithmetic result"
assertion. It also lets the `test_disk_backed_image_data.py` xfails (:50,:115,:155,:175,:241)
flip as the reparent lands.

**In-repo precedent CONFIRMED** `[VERIFIED: interpolation.py:10-13,112,162-174,176-180]`:
pc2img already uses `DiskBackedStore[DiskBackedNDArray](config=..., factory=DiskBackedNDArray,
value_type=DiskBackedNDArray)`, `.add_data_to_store(name, arr)`, `store["key"]` getitem wrapped
in `np.asarray(...)`, and `.offload(pickle_container=True)`. The primitives work end-to-end today.

## D-14 — Registry Unification

### API deltas

| Aspect | `StrategyRegistry` (`strategies/registry.py`) | `FeatureRegistry` (`features/registry.py`) |
|--------|----------------------------------------------|-------------------------------------------|
| Key model | exact string key (`_map: dict[str, type]`) | regex-pattern (`_map: dict[re.Pattern, type]`) |
| Lookup | `get_strategy(id)` / `create(id, **kw)` (kwarg-filtering) / `key_of(obj)` reverse | `match(name) -> FeatureSpec` |
| Miss exception | **`KeyError`** (`:37,62,91,126`) | **`RuntimeError`** (`:34,39,48,65`) — but see note |
| Duplicate register | `KeyError` (`:37`) | `RuntimeError` (`:34,39`) |
| Default fallback | none | `_default_cls` (a `default=True` feature) |

**Important correction to the FINDINGS framing:** `FEATURES.match` on an *unknown* name does
**not** raise — there **is** a default feature (`base_features.py:19` `@FEATURES.register(default=True)`),
so an unmatched name returns the default pseudo-spec (`registry.py:57-64`). `RuntimeError` fires
only on *ambiguous* (multiple pattern) matches (`:48`) or duplicate registration. So the
"unknown key" contract differs by design (Strategy raises, Feature falls back) — the unification
must preserve the feature default-fallback semantics, not force a raise. `[VERIFIED: features/registry.py:45-65, base_features.py:19]`

### The `match()`-without-instantiation sub-fix

`FeatureRegistry.match` constructs the class solely to read dependencies:
`inst = cls(**spec.params); spec.dependencies = inst.dependencies` `[VERIFIED: registry.py:52-54]`,
and `manager._compute` constructs it **again** (`manager.py:70`) — duplicated, side-effectful
construction. Fix: add a classmethod `dependencies_for(cls, params: dict) -> list[str]` on the
feature-strategy base so `match()` derives dependencies from the regex `groupdict` without a full
`__init__`. Note the dependency shapes to replicate: single `[base_feature]` for most
(`derivative_features.py` passim), and split lists for `average`/`sum`/`norm`
(`_split_top_level(params[...])`). `FeatureSpec.__init__` already derives the `base_feature` edge
(`:19-21`); `dependencies_for` generalizes that for the split-list families.

### One miss-exception type — what breaks

**Grep result: nothing in `tests/` asserts `KeyError`/`RuntimeError` from a registry** (zero
`pytest.raises(KeyError|RuntimeError)` matches). Callers that catch a registry miss:
`_StrategyClass._validate` (`except KeyError`, `registry.py:125`), `get_strategy` internal
(`:61`). Projection/interpolation validators call `.create()` uncaught (`projection.py:47,50`,
`interpolation.py:44,47`).

**Recommendation:** define a shared miss type via **dual inheritance**:
```python
class RegistryLookupError(KeyError, RuntimeError): ...
```
Because it subclasses both, every existing `except KeyError` **and** any `except RuntimeError`
continues to catch it — the unification breaks **zero** callers or tests. This is the lowest-risk
way to satisfy "one miss-exception type" (D-14) while honoring the BC-01 note (the *type* changed,
even though catch-behavior is preserved). `[VERIFIED: grep of src/ + tests/]`

**Blast radius:** touches `strategies/registry.py`, `features/registry.py`, and (for
`dependencies_for`) the feature base + a few feature classes. It does **not** need edits to
`projection.py`/`interpolation.py` validators (the dual-inheritance type keeps their `except
KeyError` intact). Also fold DSN-11 here (`_default_cls: type[...] | None = None`,
`features/registry.py:27`).

## D-15 — M-05 Spherical Seam Guard

**pchandler API confirmed** `[VERIFIED: pchandler/geometry/spherical/fov.py]`:
- `FoV.crosses_pi` property → `return self.left > self.right` (`:286-294`).
- `FoV.width()` already unwraps across the seam (`:296-306`).
- `FoV.tile()` fail-fasts on wrapping FoVs with this exact message (`:704-708`):
  `"FoV.tile() does not support wrapping FoVs (left > right, i.e. crosses_pi=True). Split the
  FoV at the wrap-around boundary before tiling."`

**pc2img anchors** `[VERIFIED: strategies/projection.py]`:
- `SphericalProjection.project_raw` resolves `fov = self._field_of_view if not None else pcd.fov`
  (`:119`) then reads `fov.left/top/right/bottom` (`:120-121`). Insert the guard **after** `fov`
  is resolved (guards user-supplied AND `pcd.fov`).
- `SphericalProjection.inverse_projection` reads `self._field_of_view.left/.right` directly into
  `np.linspace(left, right, ...)` (`:129-135`). Insert the guard after confirming
  `self._field_of_view is not None`.

**Recommended guard (shared helper — the discretion call):**
```python
def _reject_wrapping_fov(fov: FoV) -> None:
    if fov.crosses_pi:
        raise NotImplementedError(
            "SphericalProjection does not support wrapping FoVs (left > right, crosses_pi=True). "
            "Split the FoV at the wrap-around boundary before projecting."
        )
```
A shared helper (module-level function or static method) is preferable to inlining so the message
has a single source and forward/inverse stay in sync (the CONTEXT's stated intent). Call it from
both methods.

**Proving test:** construct a wrapping FoV (`left > right`; use
`FoV.construct_without_bounds_check(left=..., right=..., top=..., bottom=...)` — the regular
constructor may bounds-check, but `crosses_pi` explicitly supports `left>right`). Assert both
`project_raw` and `inverse_projection` raise `NotImplementedError`. `[VERIFIED: fov.py:286,368-373]`

**BC-01 entry:** a single untiled cloud with a wrapping FoV now raises instead of silently
producing reversed columns (accepted per D-15).

## D-11 — conftest Fixture Factory & Fixture Needs

`PointCloudData(xyz)` **confirmed against the installed pchandler 2.1.0** `[VERIFIED: .venv
inspect]`: `PointCloudData(np.ndarray Nx3)` constructs directly; the instance exposes `.nbPoints`,
`.xyz`, `.spher`, `.fov`. `PointCloudDataKW` keys (for `**kwargs`): `rgb, normals, intensity,
reflectance, scalar_fields, socs_origin, project_transformation, numerical_optimization_shift,
unshifted_bbox, _shift_applied_by, arr`. Named scalar fields attach via `scalar_fields=` (a dict).

**Existing precedent to lift into `conftest.py`** `[VERIFIED: test_point_cloud_image_generator.py:13-32]`:
`DummyProjection`/`DummyInterpolation` duck-stubs + `make_point_cloud()` returning
`PointCloudData(np.empty((0,3)))`.

### Which TEST targets need a real PCD vs a stub

| Target | Needs real PCD? | Why |
|--------|-----------------|-----|
| Interpolation math (Linear/Nearest/Cubic/Delaunay) | **No** | `interpolate(values, points2d, grid_x, grid_y)` is pure arrays — zero pcd |
| Orthographic/Spherical `project_raw` | **Yes** | Uses `pcd.xyz`/`pcd.spher`/`pcd.nbPoints`/`pcd.fov` + real `BoxFilter`/`FoVFilter(pcd)` |
| Perspective `project` | Yes (or matmul stub) | Uses `@ pcd` (pchandler `_TransformArray.__matmul__`) — needs real PCD or a matmul-supporting duck |
| Derivative features (`compute(_, fetch)`) | **No** | `pcd` arg is ignored (`_`); a dict-backed `fetch` lambda supplies inputs |
| Feature-name DSL (`FeatureRegistry.match`) | **No** | Pure regex/parse — no pcd |
| `FeatureManager` orchestration | **Yes** (minimal) | Base-feature `compute` reads `pcd.spher`/scalar fields; a small real PCD or a `.xyz`/`.nbPoints`/`.spher` duck |
| `TiledPointCloudImageGenerator` | **Yes** (heaviest) | Needs tiles (`PointCloudTile`) + `FoV.tile`; the largest fixture cost |
| `util.py` (`convert_to_image`/`replace_nan`/`to_gray`/`nanconv`) | **No** | Pure array functions |

**Sizing insight:** the conftest PCD factory is genuinely needed only for **TEST-03 projection**
and **TEST-05 orchestration**. TEST-04 (derivative/DSL), TEST-06 (util), and interpolation math
need **no PCD** — plain arrays and dict-`fetch` stubs. This meaningfully shrinks the Wave-0
fixture surface. Recommend a `synthetic_pcd(n=…, with_scalar_fields=…)` factory fixture plus a
lightweight `fake_projection`/`fetch_stub` helper.

## Wave Grouping & Collision Map (D-13 groups by source file)

Findings mapped to source files, with **must-serialize** (same-function/class) collisions
flagged. `[VERIFIED: 04-FINDINGS.md + live source line anchors]`

| File | Findings | Same-unit collisions (do together) |
|------|----------|-------------------------------------|
| `strategies/projection.py` | M-01(BUG-01), M-02, M-03, M-04, M-05 | **M-02+M-03+M-04** = same `PerspectiveProjection` class → one plan unit. M-01 (Orthographic) + M-05 (Spherical) are independent classes but same file → sequential edits |
| `util.py` | M-07, M-08, M-09 | **M-07+M-08** = same `nanconv` function (lines 197 + 200-203) → one edit (copy input + float32). M-09 (`convert_to_image`) separate |
| `features/derivative_features.py` | M-10, M-11, DSN-03, M-12 | **DSN-03+M-12** = same `NormalizedFeature.compute` (lines 68 + 80-81) → one edit (uncomment validation + copy-before-mutate). M-10 (Gradient, kept-behavior param) + M-11 (Hillshade, kept-behavior) separate classes |
| `strategies/interpolation.py` | M-06 (kept-behavior; PERF-03 param) | single |
| `tiled_generator.py` | DSN-01(BUG-03), DSN-07(site), DSN-10 | independent one-liners |
| `features/manager.py` | DSN-04, DSN-07(site), DSN-08 | independent |
| `core.py` | DSN-06 (flips existing xfail) | single |
| `strategies/registry.py` + `features/registry.py` | DSN-05/D-14, DSN-11 | **registry unification wave** — widest blast radius; own wave |
| `image_cache/*` | DSN-02(BUG-02), DSN-09, DSN-07(store site) | **D-04+D-05 reparent+store wave** — resolves all three by construction |
| `features/rrim.py` | BUG-04 (E402/docstring), M-13 (defer/log) | single |

### Cross-wave finding: DSN-07 (mutable `LazyDiskCacheConfig()` default, B008×4)

DSN-07 spans **four files across three waves** `[VERIFIED: 04-FINDINGS.md DSN-07]`:
`manager.py:17`, `tiled_generator.py:96,109`, `image_cache/disk_backed_image_store.py:22`. The
store site is **resolved by construction** in the D-05 wave (the wrapper inherits
`DiskBackedStore`'s frozen-dataclass default, which is `noqa: B008`-safe, or applies the
None-sentinel). The `manager.py` and `tiled_generator.py` sites are independent one-liners folded
into their own file-waves. Share the fix template: `core.py:34-43`'s `None`-sentinel +
`coerce_lazy_cfg` pattern. Flag to planner: keep the fix **consistent** across sites even though
they land in different waves (one BC/consistency note).

### Sequencing recommendation

- **Wave 0:** `tests/conftest.py` factory (synthetic PCD + fetch stub) + author failing proving
  tests (`xfail`) for every genuine-fix finding (D-12).
- **Wave A (parallel by file, pure-math):** `util.py`, `derivative_features.py`,
  `interpolation.py`, `projection.py` (orthographic + spherical-guard + perspective). No shared
  files → clean worktree parallelism.
- **Wave B (consolidations, coordinate carefully):** (B1) `image_cache/` reparent + store
  (D-04/D-05) — **blocked on the D-05 gate decision**; (B2) registry unification (D-14). B2's
  dual-inheritance exception avoids editing the projection validators, so B1/B2 don't collide.
- **Wave C:** orchestration fixes (`manager.py`, `tiled_generator.py`, `core.py`) + coverage
  authoring (TEST-03..06) + flip all xfails + re-measure and ratchet `--cov-fail-under`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Disk-cache codec / arithmetic surface | A patched pickle store or custom ufunc | `GSEGUtils.DiskBackedStore` + `DiskBackedNDArray` (D-04/D-05) | Hardened `.npy`+JSON codec, `allow_pickle=False`, atomic writes, working ufunc — already shipped and consumed in `interpolation.py` |
| Seam detection | A custom `left>right` check | `pchandler FoV.crosses_pi` | pchandler owns the seam-tracking API; mirror its `FoV.tile()` refusal for consistency |
| Interpolation "outside hull" oracle | Hand-rolled NaN comparison | `scipy.LinearNDInterpolator` (NaN iff `find_simplex==-1`) | Authoritative reference for the M-06 characterization test |
| Synthetic point clouds | Committed E57/PLY binaries | `PointCloudData(xyz)` from synthetic numpy arrays | Deterministic, fast, no binary fixtures (D-11) |
| Miss-exception unification | A single new type that forces call-site edits | `class RegistryLookupError(KeyError, RuntimeError)` | Dual inheritance keeps every existing `except` working |

**Key insight:** BUG-02 and DSN-09 are not "bugs to patch" — they are an **unfinished
migration**. `interpolation.py` already moved onto GSEGUtils primitives; only `image_cache/`
still rolls its own broken ufunc + pickle store. Reparenting finishes the migration and resolves
both by construction.

## Runtime State Inventory

> This is a reparent + on-disk-format-migration phase (`.pkl` → `.npy`+`.meta.json`).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | On-disk cache files change format `.pkl` → `.npy` + `.meta.json`. Existing `.pkl` caches in user temp/`cache_path` dirs become unreadable. | **None (graceful by construction):** `DiskBackedStore._load_entry` refuses legacy `.pkl` with an INFO log and treats it as a **cache miss** → re-materialized via the factory `[VERIFIED: disk_backed_store.py:437-443]`. No migration script needed. Record as BC-01 (cache format change). |
| Committed binary fixtures | **None** — `tests/` holds only `.py` files (verified: no `.pkl`/`.npy`/`.e57`/`.ply`). | None. |
| Live service config | **None** — pc2img is an importable library with no external service state. | None. |
| OS-registered state | **None** — no scheduler/daemon/process registration. | None. |
| Secrets / env vars | **None** — no `os.environ`/`getenv` usage anywhere in `src/pc2img/` (per CLAUDE.md + grep). | None. |
| Build artifacts | Version is `setuptools_scm`-derived; no stale name-embedding artifacts relevant to this phase. | None. |

**The canonical question — after every file is updated, what runtime state still holds the old
form?** Only pre-existing `.pkl` cache files on disk, and those degrade to a re-computable cache
miss automatically. No data-migration task required.

## Common Pitfalls

### Pitfall 1: Assuming the store reparent "just works" like interpolation.py
**What goes wrong:** The precedent stores `DiskBackedNDArray` (allow-listed); `DiskBackedImageData`
is not, so offload→reload raises `ValueError`. **How to avoid:** resolve the D-05 class-registry
gate (Option A or B) as part of the reparent. **Warning sign:** a green in-memory test but a
crash on the first offload+refetch cycle. Add a proving test that **offloads then refetches**.

### Pitfall 2: Referencing `self._image_data` after reparenting
**What goes wrong:** `DiskBackedNDArray` stores the buffer as `self._data`; leftover
`self._image_data` references (esp. in `to_uint8`) raise `AttributeError`. **How to avoid:**
migrate `to_uint8` to `self._data`/`.data`; don't re-declare `_image_data`.

### Pitfall 3: Editing M-07 and M-08 separately
**What goes wrong:** Both live in `nanconv` (`util.py:197` and `:200-203`); two separate edits
collide. **How to avoid:** one edit — copy the input array (`a = a.copy()` / write to a fresh
buffer) AND accumulate/divide in float32.

### Pitfall 4: DSN-03 and M-12 as separate tasks
**What goes wrong:** Both touch `NormalizedFeature.compute` lines 68/80-81. **How to avoid:** one
edit — re-enable the commented percentile validation (`:68`) and copy-before-mutate (mirror
`ClipPercentileFeature`'s `np.array(..., copy=True)` at `:259`), replacing the in-place `out=img`.

### Pitfall 5: Treating M-06/M-10/M-11 as bugs to fix
**What goes wrong:** A downstream agent "corrects" a kept-behavior finding, changing shipped
output. **How to avoid:** these get *characterization* tests that PIN current behavior + a
future-improvement log; the only code change is **adding opt-in params whose defaults reproduce
today's values**. Assert output is byte-identical with default params.

### Pitfall 6: Linter regex with mid-pattern inline flags
**What goes wrong:** Phase-4 hit `re.error` on a mid-pattern `(?im)` under Python ≥3.11. **How to
avoid:** use hoisted-flag form (per STATE.md Phase-04 P07 Rule-1). Applies to any verifier/linter
regex this phase adds.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `~=9.1` + pytest-cov `~=5.0` + coverage `~=7.0` `[VERIFIED: pyproject.toml:84]` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths=["tests"]`, `addopts="--import-mode=importlib --strict-markers"` `[VERIFIED: pyproject.toml:158-163]` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ --cov=pc2img --cov-branch --cov-report=term-missing` |
| Coverage floor | `--cov-fail-under=35` (CI CLI only, not in TOML); baseline 37%; **ratchet up in Phase 5** (D-10) `[VERIFIED: CONTRIBUTING.md:58-81]` |

### Phase Requirements → Test Map (proving/characterization sensors)
| Finding | Behavior | Test type | Sensor sufficiency |
|---------|----------|-----------|--------------------|
| M-01 (BUG-01) | Orthographic returns `(pts2d, mask)` = `xyz[mask][:,cols]` normalized | property (parametrized xy/yz/xz) | Deterministic oracle: assert equality to hand-computed normalized cols, not a diagonal |
| M-06 | Delaunay interior points finite (culling off) / NaN-iff-outside-hull | **held-out oracle** | Use `scipy.LinearNDInterpolator` as the reference (NaN iff `find_simplex==-1`); anisotropic grid triggers the culling |
| DSN-01 (BUG-03) | `extend_cache_paths` keeps `interp_kwargs` | simple assertion | Assert result `interp_kwargs` is a dict (not `None`) after the branch fires |
| DSN-02 (BUG-02) | `dbid + dbid` == `arr + arr`, returns ndarray | simple assertion | Correct-arithmetic-result (D-04) |
| M-08 | `nanconv` finite & within float32 tol of float64 ref | property (parametrized magnitudes {5e3,1.2e4,5e4} × kernels) | Overflow is magnitude-dependent; sample across realistic range values |
| M-07 | `nanconv` does not mutate input | simple assertion | `assert array_equal(isnan(a), isnan(snapshot))` |
| M-09 | all-NaN + `normalize=True` → valid uint8 (no raise) | simple assertion | Single degenerate input |
| M-10 (kept) | Gradient default output unchanged; new `pixel_size` param | characterization | Assert default == today's `1/100`-scaled result; param default reproduces it |
| M-11 (kept) | Hillshade internal self-consistency (NOT ESRI compass) | characterization | Azimuth-sweep self-consistency per D-08; do not assert compass truth |
| Barycentric weights | linear field reproduced exactly | held-out oracle | scipy/analytic reference, err ~1e-15 (CONFIRMED-CORRECT — do not re-open) |
| M-02/M-03/M-04 | Perspective: `Z_c≤0` masked; `t` applied; dead override gone | property + simple | Behind-camera mirror point masked; pixel == `K·[R|t]·X` |
| M-05 (D-15) | wrapping FoV raises in project_raw + inverse | simple assertion | Construct `crosses_pi` FoV; assert raises |
| DSN-06 | omitted config coerced | **existing xfail flips** (`test_...:35`) | The xfail IS the proving test |
| DSN-04/07/08/10/11 | reset/default-identity/cycle-guard/import/typing | simple assertions | Deterministic single-path checks |
| DSN-09 (security) | store no longer calls `pickle.load`; refuses legacy `.pkl` | simple assertion | Assert no pickle sink + legacy `.pkl` → cache miss |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q` (fast subset for the touched module).
- **Per wave merge:** `pytest tests/ --cov=pc2img --cov-branch`.
- **Phase gate:** full suite green + coverage re-measured and floor ratcheted before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/conftest.py` — synthetic `PointCloudData` factory + `fetch` stub + `fake_projection` (D-11). **Does not exist yet** (verified).
- [ ] `tests/test_projection.py` — TEST-03 (real PCD): M-01, M-02/03/04, M-05.
- [ ] `tests/test_interpolation.py` — TEST-03 (pure arrays): M-06, barycentric oracle.
- [ ] `tests/test_derivative_features.py` — TEST-04 (fetch stub): M-10, M-11, DSN-03, M-12.
- [ ] `tests/test_feature_registry.py` — TEST-04: DSL match, `dependencies_for`, unified miss type.
- [ ] `tests/test_manager.py` — TEST-05 (minimal PCD): DSN-04, DSN-06, DSN-08.
- [ ] `tests/test_tiled_generator.py` — TEST-05: DSN-01 (BUG-03), DSN-10.
- [ ] `tests/test_util.py` — TEST-06 (pure arrays): M-07, M-08, M-09, `replace_nan`, `to_gray`.
- [ ] `tests/test_image_store.py` — D-05: pickle-sink removed, legacy `.pkl` refused, offload→reload round-trip.
- [ ] Flip existing xfails: `test_point_cloud_image_generator.py:35`; `test_disk_backed_image_data.py` :50,:115,:155,:175,:241.

*Existing test infra present:* `test_disk_backed_image_data.py`, `test_hygiene.py`,
`test_point_cloud_image_generator.py`, `test_rrim_features.py`. No `conftest.py` yet.

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: "high"`
`[VERIFIED: config.json]`.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Library — no auth surface |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | No access-control surface |
| V5 Input Validation & Deserialization | **yes** | **Resolved by D-05:** `DiskBackedStore` uses `np.save/np.load(allow_pickle=False)` + an explicit class allow-list (no `importlib`), eliminating the `pickle.load` arbitrary-code sink (DSN-09 / STRIDE T-04-J). Also: re-enable percentile bounds validation (M-12); DSL regex already validates. |
| V6 Cryptography | no | No crypto; never hand-roll (n/a) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `pickle.load` of arbitrary `*.pkl` cache files (DSN-09) | Tampering / RCE | **Eliminated by construction** via the D-05 store consolidation (`allow_pickle=False` `.npy` codec + allow-list class resolution). This is the security deliverable — a proving/characterization test asserts the pickle sink is gone and legacy `.pkl` is refused. |
| Unvalidated percentile bounds (M-12) | — (correctness/robustness) | Re-enable the commented `0 ≤ low ≤ high ≤ 100` check (mirror `ClipPercentileFeature`). |

The DSN-09 `block_on:high` gate is satisfied not by a separate fix but by the D-05 consolidation
that the phase already performs — surface this linkage so the planner sequences D-05 before the
security sign-off.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Dropping `__array_priority__ = 1000` on the reparented `DiskBackedImageData` is safe (no test/behavior depends on operator-dispatch precedence vs bare ndarray) | D-04 | Low — a `dbid <op> ndarray` mixed expression could dispatch differently; verify with a mixed-operand test at fix time |
| A2 | The reparented class's inherited `__array_ufunc__` returning a plain ndarray is acceptable to all `DiskBackedImageData` consumers (they don't rely on getting a `DiskBackedImageData` back from arithmetic) | D-04 | Low — matches GSEGUtils' documented contract and `interpolation.py` usage; but grep consumers before finalizing |
| A3 | `hypothesis` is a mature library and the `SUS` verdict is a registry-probe artifact, not a real risk | Package Audit | None for this phase (not added); only relevant if owner later opts in |
| A4 | pchandler `FoV.construct_without_bounds_check` allows building a `crosses_pi` (left>right) FoV for the M-05 proving test | D-15 | Low — `crosses_pi` explicitly supports `left>right`; if the regular ctor bounds-checks, use `construct_without_bounds_check` (verified present at fov.py:368) |
| A5 | Owner will approve Option A (GSEGUtils public class-registration) as a lightweight in-session change, OR accept Option B's private-global coupling | D-05 | **Medium — this is the gating decision.** Must be resolved at plan time; wrong assumption blocks Wave B |

## Open Questions

1. **D-05 gate: Option A (GSEGUtils change) vs Option B (import-time private registration)?**
   - What we know: the closed allow-list is a hard blocker; both options work technically.
   - What's unclear: owner's tolerance for a GSEGUtils edit (gated) vs private-API coupling.
   - Recommendation: raise at plan time as an explicit owner decision; default to Option A
     (principled, owner authors GSEGUtils) unless the owner wants zero cross-repo churn.

2. **WRAPPER vs REPLACE for `DiskBackedImageStore`** (Claude's discretion).
   - Recommendation: WRAPPER (minimal BC surface, preserves the public barrel). See D-05.

3. **Perspective M-02/M-03 empirical resolution** (FINDINGS escalation).
   - What we know: the missing `Z_c>0` guard and absent `t` term are unambiguous from source.
   - What's unclear: whether callers pre-bake `t` into the matrices (undocumented `@ pcd` contract).
   - Recommendation: the proving test constructs an explicit non-origin camera + behind-camera
     mirror point; document the `_TransformArray.__matmul__` contract while fixing M-04.

## Sources

### Primary (HIGH confidence — direct source reads this session)
- `04-FINDINGS.md` — the 24-finding BUG-05 work-list (all line anchors re-verified).
- `/scratch/30_GSEGUtils/.../disk_backed_store.py` — store surface + the class-registry blocker (:61-79,273-274,386,437-466,468-501).
- `/scratch/30_GSEGUtils/.../disk_backed_ndarray.py` — reparent target + working ufunc (:49,98-138,152-172).
- `/scratch/31_pc2img/src/pc2img/image_cache/*` — pickle store + broken ufunc (image_store, image_data).
- `/scratch/31_pc2img/src/pc2img/strategies/{projection,interpolation,registry}.py` — M-01/M-05/perspective anchors, precedent, registry deltas.
- `/scratch/31_pc2img/src/pc2img/features/{manager,registry,derivative_features}.py` — orchestration + DSL + feature math.
- `/scratch/41_pchandler/.../geometry/spherical/fov.py` — `crosses_pi` (:286), `tile()` message (:704-708).
- Installed pchandler 2.1.0 — `PointCloudData` signature + attributes (`.venv` inspect).
- `.planning/config.json`, `CONTRIBUTING.md`, `pyproject.toml` — validation + security config.

### Secondary / Tertiary
- None — no web search used (all providers disabled; task is fully codebase-grounded).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all deps installed and version-verified; no new packages.
- Store/reparent analysis (D-04/D-05): HIGH — the blocker and mapping are read directly from source.
- Registry unification (D-14): HIGH — deltas + zero-test-breakage confirmed by grep.
- Seam guard (D-15): HIGH — pchandler API + message verified in source.
- Fixture needs (D-11): HIGH — PCD signature confirmed against installed package.
- Wave collisions: HIGH — line anchors re-verified against live source.

**Research date:** 2026-07-10
**Valid until:** 2026-08-09 (30 days; stable internal codebase, but re-verify the GSEGUtils
`_LAZY_DISK_CACHE_CLASS_REGISTRY` state if GSEGUtils is upgraded before execution).
