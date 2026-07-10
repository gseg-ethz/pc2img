# Phase 04 — Design-track FIND pass (raw candidates, pre-refutation)

**Plan:** 04-05 (QUAL-02 design track) · **Pillar:** design · **Stage:** FIND (Task 1)
**Generated:** 2026-07-10 · **Tree state:** post-04-04 (ruff sweep landed; line-length 120)

> This is the **retained raw FIND-pass output** (D-05 evidence-retention). It is deliberately
> kept distinct from the refuted `04-FINDINGS-design.md`. Candidates here are pre-dedup and
> pre-refutation: some survive, some are downgraded, some are recorded as already-FIXED. Every
> `file:line` was **re-grepped against the post-04-04 tree** (Pitfall 1) — several drifted from
> the 04-RESEARCH anchor table because the 04-04 `ruff --fix`/format pass moved code.
>
> Fan-out shape (04-RESEARCH §Review Harness Shape): four design reviewers, one per module set.
> D1 registries+factory · D2 orchestration · D3 image cache · D4 cross-cutting hygiene/typing.

---

## D1 — registries + factory (`registry.py`, `strategies/registry.py`, `features/registry.py`)

### C-D1-a — Broken `make_generator` factory (ANCHOR #1) — appears FIXED
- **file:line:** `src/pc2img/registry.py:1-7` (module is now comment-only)
- **defect:** the anchor factory called `PointCloudImageGenerator(pcd, proj, interp)` against a
  5-param ctor `(pcd, img_res, proj, interp, lazy_disk_cache_config)`, mis-landing args.
- **status seen by reviewer:** the whole `def make_generator` body is gone; `registry.py` holds
  only an explanatory comment. Looks resolved by 04-03 (deleted, zero callers). → hand to refuter
  as "record FIXED-with-smoke, do not re-log."

### C-D1-b — Divergent registry mechanisms (ANCHOR #2)
- **file:line:** `src/pc2img/strategies/registry.py:29-92` (`StrategyRegistry`) vs
  `src/pc2img/features/registry.py:24-68` (`FeatureRegistry`)
- **defect:** two independent registry contracts. `StrategyRegistry`: string keys, kwarg-filtering
  `create()`, reverse `key_of()`, raises **`KeyError`** (`strategies/registry.py:63`).
  `FeatureRegistry`: regex-pattern DSL, default-fallback class, raises **`RuntimeError`**
  (`features/registry.py:34,39,48,65`). Different lifecycles, error types, and coercion protocols.
- **sub-finding:** `FeatureRegistry.match()` **instantiates the class just to read
  `.dependencies`** — `inst = cls(**spec.params)` at `features/registry.py:52` — a side-effectful
  read, and the class is instantiated *again* in `manager._compute` (`manager.py:70`).

### C-D1-c — `_default_cls` non-optional attr assigned `None` (seed D)
- **file:line:** `src/pc2img/features/registry.py:27` (`self._default_cls: type[BaseFeatureStrategy] = None`)
- **defect:** annotated non-optional but initialized to `None`; typing lie (pyright basic tolerates).

### C-D1-d — Stale dead comment survived 04-04 ERA001 (hygiene)
- **file:line:** `src/pc2img/strategies/registry.py:28` (`# class StrategyRegistry(Generic[T]):`)
- **defect:** commented-out old class header left in place directly above the PEP-695 `class
  StrategyRegistry[T]:`. ERA001 in 04-04 did not catch it. Pure hygiene.

## D2 — orchestration (`core.py`, `features/manager.py`, `tiled_generator.py`)

### C-D2-a — `extend_cache_paths` stores `None` via `dict.update()` (BUG-03 / seed G)
- **file:line:** `src/pc2img/tiled_generator.py:66-68`
- **defect:** `updates["interp_kwargs"] = dict(self.interp_kwargs).update({...})`. `dict.update()`
  returns `None`, so when the branch fires, `interp_kwargs` is replaced by `None` in the
  `replace(self, **updates)` — nulling the interp kwargs it meant to extend.
- **repro:** `dict({"a":1}).update({"b":2})` → `None`.
- **cross-ref:** named BUG-03. **Source-only** — there is NO current pytest xfail encoding this
  (Codex MEDIUM correction); cite the source, not a non-existent xfail.

### C-D2-b — `FeatureManager._base_features` never reset in `request()` (seed B)
- **file:line:** init `src/pc2img/features/manager.py:22`; append at `:36`; `request()` resets only
  `_targets` at `:28`.
- **defect:** `request()` clears `self._targets = []` but not `self._base_features`. Repeated
  `request()` calls **accumulate** base-feature specs; `get_base_features()` (`:49-56`) then
  recomputes every accumulated spec on each `generate()`. Latent correctness/perf bug on
  generator reuse.

### C-D2-c — In-place raster mutation in `NormalizedFeature.compute` (ANCHOR #3)
- **file:line:** `src/pc2img/features/derivative_features.py:79-81`
- **defect:** `img = fetch(self.base_feature)` (`:76`) then `np.divide(..., out=img)` and
  `np.clip(..., out=img)` write into the fetched array. `ClipPercentileFeature` copies first;
  `NormalizedFeature` does not — inconsistent, and cache-corrupting if `fetch` ever returns a view.

### C-D2-d — Omitted `lazy_disk_cache_config` not coerced (coerce-null)
- **file:line:** `src/pc2img/core.py:70` (default `= None`) + `@validate_call` at `:63`
- **defect:** the `BeforeValidator(coerce_lazy_cfg)` runs on a *passed* `None` but not on an
  *omitted* argument (pydantic v2 does not validate defaults), so an omitted config stays `None`
  uncoerced and the ctor fails before `cache_store.cache_dir` exists.
- **cross-ref:** CURRENT xfail `tests/test_point_cloud_image_generator.py:35`
  (`test_constructor_normalizes_omitted_lazy_disk_cache_config`, strict=False) encodes exactly this.

### C-D2-e — Mutable constructed default `LazyDiskCacheConfig()` (seed E, B008)
- **file:line:** `src/pc2img/features/manager.py:17`; `src/pc2img/tiled_generator.py:96` and `:109`
- **defect:** shared-instance default arg. `core.py:34-43` already models the correct None-sentinel
  + `coerce_lazy_cfg` pattern. (ruff B008 confirms all sites; see D4.)

### C-D2-f — Circular-import sensitivity (seed H)
- **file:line:** `src/pc2img/tiled_generator.py:19` (`from pc2img import PointCloudImageGenerator`)
- **defect:** a submodule imports the top-level package barrel; fragile import ordering.

## D3 — image cache (`disk_backed_image_data.py`, `disk_backed_image_store.py`)

### C-D3-a — `__array_ufunc__` unconditionally raises → mixin arithmetic dead (seed F / BUG-02)
- **file:line:** `src/pc2img/image_cache/disk_backed_image_data.py:63-64`
- **defect (as re-grepped):** current body is `raise NotImplementedError`. The class mixes in
  `NDArrayOperatorsMixin` (whose entire purpose is `+ - * /` via `__array_ufunc__`), so every
  arithmetic op on a `DiskBackedImageData` raises. The mixin is dead.
- **Pitfall-1/4 CORRECTION:** 04-RESEARCH/CONTEXT documented the defect as `raise NotImplemented`
  (the singleton → `TypeError: exceptions must derive from BaseException`). That is **no longer the
  observed behavior**: commit `b478a34` (04-04 `ruff check --fix`, rule **F901**) rewrote it to
  `raise NotImplementedError`. So the *exception-type* half of BUG-02 is inadvertently already
  fixed; the *design* defect (arithmetic non-functional) survives. Refuter must confirm and the
  Phase-5 proving test must assert `NotImplementedError`, not `TypeError`.

### C-D3-b — Pickle load of arbitrary `*.pkl` cache files (seed J / security T-04-J)
- **file:line:** `src/pc2img/image_cache/disk_backed_image_store.py:49` (`__getitem__`) and `:183`
  (`__setstate__`); cache dir scan at `:38`.
- **defect:** the store `pickle.load`s any `*.pkl` in the cache dir on access and on unpickle.
  Tampering/RCE if the cache dir is ever attacker-influenced.
- **current mitigation:** cache dirs default to process-local `tempfile.mkdtemp()`
  (`disk_backed_image_store.py:28`) → currently trusted. LOG only (D-02, Phase 5/6).

## D4 — cross-cutting hygiene / typing (sweep + `pyproject.toml`, ruff as evidence)

### C-D4-a — 18 residual ruff findings (post-04-04, deferred to Phase 5 per D-02)
- **evidence:** bare `ruff check src/` → **18 errors**: `E402×9` (`features/rrim.py`, docstring-
  before-imports / BUG-04), `C901×5` (`derivative_features.py` ×4 + `util.replace_nan:227`),
  `B008×4` (`manager.py:17`, `disk_backed_image_store.py:22`, `tiled_generator.py:96,109`).
- **defect:** these are the 04-04 "breadcrumbs." B008 overlaps seed E (C-D2-e); E402 overlaps
  BUG-04 (rrim docstring). C901 is complexity refactor (largely math-track).

### C-D4-b — Dead commented-out validation in `NormalizedFeature` (hygiene, ties to C-D2-c)
- **file:line:** `src/pc2img/features/derivative_features.py:68` (`# if not(0 <= float(low) < float(high) <= 100):`)
- **defect:** percentile-bound validation is commented out, so `normalized_<f>_<low>_<high>` accepts
  `low > high` or out-of-`[0,100]` silently. Not ERA001-flagged (dangling `if`, no body).

### C-D4-c — BUG-04 `rrim.py` module docstring inert (cross-ref, E402 root cause)
- **file:line:** `src/pc2img/features/rrim.py:1-23` (`from __future__ import annotations` precedes the
  triple-quoted string → `rrim.__doc__ is None`; imports then flagged E402).
- **cross-ref:** named BUG-04. **Source-only** — no current pytest xfail encodes it (Codex MEDIUM).
