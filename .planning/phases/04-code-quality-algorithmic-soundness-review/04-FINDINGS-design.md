# Phase 04 — Design-track FINDINGS (refuted, deduped)

**Plan:** 04-05 (QUAL-02 design track) · **Pillar:** design · **Stage:** REFUTE + synthesize (Task 2)
**Generated:** 2026-07-10 · **Tree state:** post-04-04 · **Feeds:** 04-07 synthesis → Phase 5 BUG-05

> This is the design half of the FINDINGS input. Each entry below is a Task-1 candidate handed to
> an **independent refuter** (04-RESEARCH §Vote-threshold: 1 finder + 1 refuter, 2-of-2 confirm).
> The refuter's job was to **disprove** the finding with the cheapest check (D-05); its concrete
> counter-check / reproduction verdict is recorded per entry as **survived / downgraded / FIXED**.
> Raw pre-refutation candidates are retained separately in `04-FINDINGS-design-candidates.md`.
>
> **Schema (D-06):** id · file:line · defect · why-wrong · minimal repro · severity · pillar=design
> · disposition (Fix/Log) · proving-test sketch · refuter verdict. **Ordering:** most-severe first.
> **D-07:** no per-finding `BUG-05.x` IDs are minted; stable `DSN-*` ids only.
>
> **Four required anchors:** #1 make_generator → **DSN-F1 (FIXED)**; #2 divergent registries →
> **DSN-05**; #3 in-place raster mutation → **DSN-03**; #4 dependency-cycle guard → **DSN-08**.
> **Pickle security finding (seed J):** **DSN-09 (surfaced-and-logged)**.

---

## HIGH

### DSN-01 — `extend_cache_paths` nulls `interp_kwargs` via `dict.update()`
- **file:line:** `src/pc2img/tiled_generator.py:66-68`
- **defect:** `updates["interp_kwargs"] = dict(self.interp_kwargs).update({...})` stores the return
  value of `dict.update()`, which is always `None`.
- **why wrong:** when the branch fires (an interp-level `lazy_disk_cache_config` is present), the
  subsequent `replace(self, **updates)` sets `interp_kwargs = None` instead of the extended dict —
  silently discarding all interpolation kwargs on the per-tile settings, the opposite of intent.
- **minimal repro:** `dict({"a": 1}).update({"b": 2})` → `None`. (Verified this session:
  `PROBE-G ... returns: None -> stores None: True`.)
- **severity:** HIGH · **pillar:** design · **disposition:** LOG (named **BUG-03**; source-only —
  no current pytest xfail encodes it, per the Codex MEDIUM correction).
- **proving-test sketch:** build a `TIGSettings` with `interp_kwargs={"lazy_disk_cache_config":
  LazyDiskCacheConfig(...)}`, call `.extend_cache_paths("t0")`, assert the result's `interp_kwargs`
  is a dict containing the extended config (not `None`). Currently fails.
- **refuter verdict:** **SURVIVED.** Refuter attempted to show `.update()` mutates-and-returns the
  dict; probe confirms `None` return → finding reproduces as a bug.

### DSN-02 — `__array_ufunc__` unconditionally raises → all `NDArrayOperatorsMixin` arithmetic dead
- **file:line:** `src/pc2img/image_cache/disk_backed_image_data.py:63-64`
- **defect:** `def __array_ufunc__(...): raise NotImplementedError`. `DiskBackedImageData` inherits
  `NDArrayOperatorsMixin`, which routes every `+ - * / ...` operator through `__array_ufunc__`.
  Because it always raises, no arithmetic on a `DiskBackedImageData` works.
- **why wrong:** the mixin is inert; any downstream code doing `img_a + img_b` on cache objects
  raises `NotImplementedError` at runtime rather than computing (or cleanly delegating).
- **Pitfall-1 / Pitfall-4 CORRECTION (load-bearing for Phase 5):** 04-RESEARCH/CONTEXT documented
  the observed behavior as `raise NotImplemented` (the singleton → `TypeError: exceptions must
  derive from BaseException`). That is **stale**. Commit `b478a34` (04-04 `ruff check --fix`, rule
  **F901** "raise NotImplemented → raise NotImplementedError") already rewrote the line. The
  exception-type half of BUG-02 is therefore **inadvertently fixed**; the design defect remains.
- **minimal repro:** current `raise NotImplementedError` → `NotImplementedError`; old
  `raise NotImplemented` → `TypeError`. (Both verified this session: `PROBE-F`.)
- **severity:** HIGH · **pillar:** design · **disposition:** LOG (named **BUG-02**, redefined).
- **proving-test sketch:** assert `pytest.raises(NotImplementedError)` on `dbid + dbid` **today**;
  the Phase-5 fix either implements the ufunc protocol (return a wrapped result / `NotImplemented`
  singleton to let numpy fall back) or removes the mixin. Do NOT assert `TypeError`.
- **refuter verdict:** **SURVIVED (redefined).** Refuter re-grepped the line, found the F901 drift,
  and confirmed via git (`b478a34`) that the exception type changed — so it corrected the finding
  rather than dropping it. The arithmetic-dead defect is independent of the exception type.

## MEDIUM

### DSN-03 — In-place raster mutation of the fetched array (ANCHOR #3)
- **file:line:** `src/pc2img/features/derivative_features.py:76-81` (`NormalizedFeature.compute`)
- **defect:** `img = fetch(self.base_feature)` then `np.divide(..., out=img)` (`:80`) and
  `np.clip(img, 0, 1.0, out=img)` (`:81`) write into the fetched array in place.
- **why wrong:** it mutates a value owned by the raster cache path. Safe **only** because the fetch
  lambda in `manager._compute` (`manager.py:71`) wraps `np.asarray(self._get(n))` and
  `DiskBackedImageData.__array__` (`disk_backed_image_data.py:47-52`) always returns a copy. If any
  fetch path ever returns a view, this corrupts the cache. `ClipPercentileFeature` copies first —
  the inconsistency is the smell.
- **minimal repro (latent):** stub a `fetch` returning a live array; after `compute`, the input is
  overwritten (divided/clipped) — assert the caller's array is unchanged (it is not).
- **severity:** MEDIUM · **pillar:** design · **disposition:** LOG (D-02, behavioral).
- **proving-test sketch:** patch `fetch` to return a known array `a`; run `NormalizedFeature(...)
  .compute(None, fetch)`; assert `a` is unmodified (copy-on-write contract). Pair with the
  `ClipPercentile`-style `img = np.array(fetch(...), copy=True)` fix.
- **refuter verdict:** **SURVIVED (currently masked).** Refuter's counter-check: "the `__array__`
  copy makes this harmless today." True — but the finding is the latent contract violation +
  Normalized/Clip inconsistency, which the copy only *masks*. Kept MEDIUM (anchor #3 required),
  with the masking noted so Phase 5 fixes the contract, not just the symptom.

### DSN-04 — `FeatureManager._base_features` never reset across `request()` calls (seed B)
- **file:line:** `src/pc2img/features/manager.py:22` (init), `:28` (`request` resets only
  `_targets`), `:32-36` (`visit` appends to `_base_features`)
- **defect:** `request()` sets `self._targets = []` but leaves `self._base_features` intact, so
  successive `request()` calls append and accumulate base-feature specs.
- **why wrong:** `get_base_features()` (`:49-56`) recomputes every accumulated spec on each
  `generate()`, so a reused generator does redundant work and can carry stale specs from a prior
  request. Latent correctness/perf bug on generator reuse.
- **minimal repro:** one `FeatureManager`, call `request("gradient_x_range")` then
  `request("range")` (without the cache guard hitting) → `_base_features` length grows monotonically.
- **severity:** MEDIUM · **pillar:** design · **disposition:** LOG (D-02, behavioral).
- **proving-test sketch:** call `request()` twice on the same manager with overlapping targets;
  assert `len(mgr._base_features)` reflects only the latest request's uncached base features.
- **refuter verdict:** **SURVIVED.** Refuter noted the `if spec.name in self._raster_cache: return`
  guard (`:33`) prevents *duplicate compute of already-cached* features, but it does **not** reset
  the list — the accumulation across distinct/ uncached requests still holds. Confirmed by reading
  `request()`: no `self._base_features = []` anywhere.

### DSN-05 — Divergent registry mechanisms (ANCHOR #2)
- **file:line:** `src/pc2img/strategies/registry.py:29-92` (`StrategyRegistry`) vs
  `src/pc2img/features/registry.py:24-68` (`FeatureRegistry`)
- **defect:** two independent registry contracts coexist. `StrategyRegistry`: string-key map,
  kwarg-filtering `create()`, reverse `key_of()`, misses raise **`KeyError`**
  (`strategies/registry.py:63`). `FeatureRegistry`: regex-pattern DSL, default-fallback class,
  errors raise **`RuntimeError`** (`features/registry.py:34,39,48,65`).
- **why wrong:** the two have different error types, lifecycles, and coercion protocols, so callers
  and tests cannot treat "a registry" uniformly; unifying them carries behavioral risk (hence LOG).
  **Sub-finding:** `FeatureRegistry.match()` instantiates the class **just to read `.dependencies`**
  (`inst = cls(**spec.params)`, `features/registry.py:52`) and the class is instantiated *again* in
  `manager._compute` (`manager.py:70`) — a side-effectful, duplicated construction.
- **minimal repro:** `PROJECTIONS.get_strategy("nope")` → `KeyError`; `FEATURES.match("nope")` with
  no default → `RuntimeError`. Divergent contracts demonstrated.
- **severity:** MEDIUM · **pillar:** design · **disposition:** LOG (structural; D-02).
- **proving-test sketch:** Phase-5 unification target — a single registry protocol (or an adapter)
  with one miss-exception type; test both families raise the same error class and that `match()`
  reads dependencies without instantiating (e.g. a classmethod `dependencies_for(params)`).
- **refuter verdict:** **SURVIVED.** Refuter could not produce a counter-check showing the two are
  actually one mechanism — the differing exception types are directly observable. Anchor #2 confirmed.

### DSN-06 — Omitted `lazy_disk_cache_config` not coerced (coerce-null)
- **file:line:** `src/pc2img/core.py:63` (`@validate_call`), `:70` (param default `= None`)
- **defect:** `BeforeValidator(coerce_lazy_cfg)` (wired via `LazyDiskCacheConfigLike`, `:59`) runs
  when `None` is **passed explicitly**, but pydantic v2 `@validate_call` does not validate **omitted
  defaults**, so an omitted config stays `None` uncoerced.
- **why wrong:** with the arg omitted, `FeatureManager(..., lazy_disk_cache_config=None)` is invoked
  and the store construction fails before `cache_store.cache_dir` exists. Explicit `None` works;
  omission does not — a surprising asymmetry.
- **minimal repro:** `PointCloudImageGenerator(pcd, (1,1), proj, interp)` (omit config) fails;
  passing `lazy_disk_cache_config=None` succeeds.
- **severity:** MEDIUM · **pillar:** design · **disposition:** LOG (D-02, behavioral).
- **cross-ref:** CURRENT xfail `tests/test_point_cloud_image_generator.py:35`
  (`test_constructor_normalizes_omitted_lazy_disk_cache_config`, `strict=False`) encodes exactly this
  — it xpasses once the coercion lands. (The sibling `..._explicit_none_...` test already passes.)
- **proving-test sketch:** the existing xfail *is* the proving test; Phase 5 makes the omitted-arg
  path coerce (e.g. default to a sentinel and run `coerce_lazy_cfg`), flipping xfail→pass.
- **refuter verdict:** **SURVIVED.** Refuter's counter-check ("explicit `None` is coerced, so it's
  fine") actually *sharpens* the finding: the two sibling tests prove the omitted-vs-explicit
  asymmetry. Confirmed against the live xfail reason.

### DSN-07 — Mutable constructed default `LazyDiskCacheConfig()` (seed E)
- **file:line:** `src/pc2img/features/manager.py:17`; `src/pc2img/tiled_generator.py:96` and `:109`;
  `src/pc2img/image_cache/disk_backed_image_store.py:22`
- **defect:** a single `LazyDiskCacheConfig()` instance is constructed once at def-time and shared as
  the default across all calls that omit the arg (ruff **B008** flags all four sites).
- **why wrong:** shared-mutable-default class of bug; `core.py:34-43` already models the correct
  `None`-sentinel + `coerce_lazy_cfg` pattern, so the fix template exists in-repo.
- **minimal repro:** `manager.py:17` default identity is stable across instances; if any code path
  mutates the config in place, it leaks across managers.
- **severity:** MEDIUM · **pillar:** design · **disposition:** LOG (D-02; overlaps the 04-04 B008
  breadcrumbs).
- **proving-test sketch:** assert two default-constructed managers do not share the same config
  object identity after the None-sentinel fix.
- **refuter verdict:** **SURVIVED.** Refuter noted `LazyDiskCacheConfig` may be effectively frozen
  (low live-mutation risk today) → but B008 fires on all four sites and the None-sentinel is the
  established project idiom, so kept at MEDIUM rather than dropped.

## LOW / latent

### DSN-08 — Missing dependency-cycle guard in `request().visit` (ANCHOR #4)
- **file:line:** `src/pc2img/features/manager.py:32-44` (`visit` recurses `spec.dependencies` with no
  visited-set)
- **defect:** `visit()` recurses through `spec.dependencies` unconditionally; there is no
  visited-set, so a self- or transitively-cyclic feature name would recurse unboundedly →
  `RecursionError`.
- **why wrong:** defensive gap. The one guard present (`if spec.name in self._raster_cache: return`,
  `:33`) only short-circuits already-cached names, not cycles.
- **severity:** LOW (latent) · **pillar:** design · **disposition:** LOG (D-02).
- **refuter verdict:** **DOWNGRADED to LOW (empirical confirmation pending in Phase 5).** Refuter's
  counter-check: with the *currently registered* features, dependencies are derived by stripping a
  regex prefix (e.g. `gradient_x_<base>` → `<base>`), so every dependency edge strictly shrinks the
  name — **no current feature graph can form a cycle**, so no live `RecursionError` reproduces
  today. The structural gap is real (no visited-set) but unreachable with today's feature set;
  anchor #4 is retained at LOW with the "add a visited-set" fix noted.
- **proving-test sketch (Phase 5):** register a throwaway feature whose `dependencies` point back at
  itself; assert `request()` raises a clear `ValueError("dependency cycle: ...")` rather than
  `RecursionError`. Then add the visited-set to `visit()`.

### DSN-09 — Pickle load of arbitrary `*.pkl` cache files (seed J / security)
- **file:line:** `src/pc2img/image_cache/disk_backed_image_store.py:49` (`__getitem__`), `:182-183`
  (`__setstate__`); cache-dir scan at `:38`
- **defect:** the store `pickle.load`s any `*.pkl` found in its cache dir on item access and on
  unpickling (`__setstate__` re-loads offloaded features).
- **why wrong:** `pickle.load` executes arbitrary code during deserialization → Tampering/RCE if the
  cache dir is ever attacker-controlled or shared.
- **trust boundary (recorded):** cache dirs default to **process-local `tempfile.mkdtemp()`**
  (`disk_backed_image_store.py:27-28`) when no `cache_path` is configured, so today the boundary is
  a trusted, process-owned temp dir. Risk materializes only if a user supplies/points a shared cache
  dir. **STRIDE T-04-J** (Tampering/RCE, high, disposition = mitigate/log).
- **severity:** LOW *(as a Phase-4 action — surfaced-and-logged only)*; the underlying threat is
  **high** severity, gated by the trust boundary above · **pillar:** design/security ·
  **disposition:** LOG (D-02 — behavioral surface → Phase 5/6, NOT fixed here).
- **proving-test sketch (Phase 5/6):** document the "cache dirs must be trusted" contract; if
  shared/user-supplied dirs are ever supported, add provenance checks or a non-executable array
  format (e.g. `.npy`/`safetensors`) instead of pickle.
- **refuter verdict:** **SURVIVED as surfaced-and-logged.** Refuter confirmed the current
  `tempfile.mkdtemp` mitigation makes this non-exploitable in the default flow (hence not a Phase-4
  fix), but the `pickle.load` sink is real and must be recorded per the security contract
  (ASVS L1 block_on:high is satisfied by logging T-04-J with its mitigation + boundary).

### DSN-10 — Circular-import sensitivity (seed H)
- **file:line:** `src/pc2img/tiled_generator.py:19` (`from pc2img import PointCloudImageGenerator`)
- **defect:** a submodule imports the top-level package barrel rather than the defining module
  (`pc2img.core`), coupling it to package-init import ordering.
- **why wrong:** fragile — a future reorder of `pc2img/__init__.py` (which also triggers strategy
  registration side effects) could produce a partially-initialized-module `ImportError`.
- **severity:** LOW · **pillar:** design · **disposition:** LOG (D-02).
- **proving-test sketch:** import `pc2img.tiled_generator` first in a fresh interpreter; assert it
  succeeds. Fix by importing from `pc2img.core` directly.
- **refuter verdict:** **DOWNGRADED to LOW.** Refuter: the import currently succeeds (ordering
  happens to work), so no live failure. Kept as a LOW design smell (latent fragility), not a bug.

### DSN-11 — `_default_cls` non-optional attribute assigned `None` (seed D, typing)
- **file:line:** `src/pc2img/features/registry.py:27` (`self._default_cls: type[BaseFeatureStrategy]
  = None`)
- **defect:** annotated as a non-optional class object but initialized to `None`.
- **why wrong:** the annotation lies about the runtime value; pyright *basic* tolerates it, but it
  masks the real `Optional` contract and the `if self._default_cls:` fallback at `:57`.
- **severity:** LOW · **pillar:** design (typing) · **disposition:** LOG (annotate
  `type[BaseFeatureStrategy] | None = None`; mechanical, but grouped with the design log).
- **refuter verdict:** **SURVIVED (trivial).** No counter-check needed — the annotation/value
  mismatch is on the line as written.

## FIXED (recorded, not re-logged)

### DSN-F1 — Broken `make_generator` factory (ANCHOR #1) — FIXED in 04-03
- **file:line:** `src/pc2img/registry.py:1-7` (module is now comment-only)
- **status:** the factory called `PointCloudImageGenerator(pcd, proj, interp)` against the
  5-parameter ctor `(pcd, img_res, proj, interp, lazy_disk_cache_config)`, mis-landing `proj`→
  `img_res` and `interp`→`proj`. 04-03 **deleted** it (zero callers in `src/`, `tests/`, `scripts/`)
  rather than repairing, leaving an explanatory comment.
- **disposition:** **FIXED-with-smoke** (anchor #1 requirement satisfied by removal). Do not re-log.
- **smoke:** `python -c "import pc2img.registry"` imports clean; `make_generator` no longer exists.
- **refuter verdict:** **DROPPED as active finding / recorded FIXED.** Refuter's counter-check
  (import the module, look for the factory) confirms the broken factory is gone.

### DSN-F2 — `__array_ufunc__` exception-type half of BUG-02 — FIXED (inadvertently) in 04-04
- **note:** the `raise NotImplemented` → `raise NotImplementedError` correction (F901,
  `b478a34`) is already applied. Tracked inside **DSN-02** so Phase 5 asserts `NotImplementedError`.
  The residual *design* defect (mixin arithmetic dead) is the live half — see DSN-02.

## Hygiene breadcrumbs (D4 — carried, not the design-review focus)

- **Stale comment** `# class StrategyRegistry(Generic[T]):` at `strategies/registry.py:28` — survived
  04-04 ERA001 (not code-shaped enough to flag). Mechanical delete (LOW hygiene).
- **Dead commented validation** `# if not(0 <= float(low) < float(high) <= 100):` at
  `derivative_features.py:68` — `NormalizedFeature` now accepts `low>high` / out-of-`[0,100]`
  silently. Ties to DSN-03; Phase-5 re-enable + test (behavioral, LOG).
- **18 residual ruff findings** (bare `ruff check src/`): `E402×9` (rrim docstring / BUG-04, no
  xfail — source-only), `C901×5` (complexity, mostly math-track), `B008×4` (= DSN-07). These are the
  04-04 deferred breadcrumbs (D-02), re-verified present this session.

---

## Coverage self-check (against 04-05 must-haves)

- ✅ Four anchors present-or-fixed: #1 **DSN-F1 (FIXED)**, #2 **DSN-05**, #3 **DSN-03**,
  #4 **DSN-08 (LOW/latent)**.
- ✅ Broad audit beyond seeds evident: DSN-01/02/04/06 + hygiene breadcrumbs, plus the F901 drift
  discovery (not in the seed list).
- ✅ Every surviving candidate carries an independent refuter's concrete counter-check verdict
  (survived / downgraded / FIXED) — the two-file FIND/REFUTE split is retained on disk.
- ✅ Pickle-load security finding (seed J) recorded as **DSN-09**, surfaced-and-logged with its
  trust boundary (process-local `tempfile.mkdtemp`) — LOG, not fixed (T-04-J, D-02).
- ✅ Every `file:line` re-grepped against the post-04-04 tree (Pitfall 1); drifts corrected
  (esp. DSN-02 F901, DSN-03 `:79-81`, DSN-01 `:66-68`).
