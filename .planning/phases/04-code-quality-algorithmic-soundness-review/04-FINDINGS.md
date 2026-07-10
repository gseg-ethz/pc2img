# Phase 04 — Canonical FINDINGS (code-quality + algorithmic-soundness review)

> The single, canonical, schema-valid, most-severe-first findings log for Phase 4. This file
> merges the design half (`04-FINDINGS-design.md`, QUAL-02, plan 04-05) and the math half
> (`04-FINDINGS-math.md`, QUAL-03, plan 04-06) into one deduped list. It is the **Phase-5
> BUG-05 feeder** (D-06 / D-07): Phase 5 fixes each surviving finding with the sketched
> proving test. This file stands alone — the design/math/candidate fragments are retained
> beside it only as adversarial-pass (FIND → REFUTE) evidence (D-05).
>
> **Per-entry schema (D-06), eight labels on every entry:** an identifier, then a `location`
> (a `file.py:line` anchor), a `defect`, a `why-wrong`, a `repro`, a `severity`, a `pillar`,
> and a `proving-test` sketch.
> **Ordering:** most-severe-first (HIGH → MED-HIGH → MED → LOW-MED → LOW).
> **D-07:** no per-finding BUG-05 sub-numbered requirement ids are minted and no GSD todos are
> created —
> this file itself is the feeder. Stable `M-*` / `DSN-*` ids are carried forward verbatim from
> the two half-files (no collision). Named legacy bugs are cross-referenced inline
> (BUG-01 = M-01, BUG-02 = DSN-02, BUG-03 = DSN-01, BUG-04 = the E402/rrim breadcrumb).
>
> **Tree state:** re-grepped against the live post-04-04 tree (Pitfall 1); numeric probes ran
> against the project `.venv` (numpy 2.0.2 / scipy 1.18.0). Every `file:line` below was
> re-verified in this synthesis pass.
>
> **Four required design anchors (present-or-fixed):** #1 broken `make_generator` →
> **FIXED in 04-03** (recorded below, not re-logged); #2 divergent registries → **DSN-05**;
> #3 in-place raster mutation → **DSN-03**; #4 missing dependency-cycle guard → **DSN-08**.
> **Security (seed J / STRIDE T-04-J):** pickle load → **DSN-09** (surfaced-and-logged).

**Severity legend:** HIGH = silent wrong output or hard failure on a shipped path ·
MED-HIGH / MED = wrong/corrupt output on a reachable path or config · LOW-MED / LOW =
latent, conditional, or WIP-path.

---

## HIGH

### M-01 — Orthographic projection unusable: 2-tuple arity + mixed row/col indexing (BUG-01)

**id:** `M-01` (a.k.a. **BUG-01**; this is the math-track confirmation of the design anti-pattern
"`project()` / `project_raw()` return-arity mismatch" — recorded once here, cross-referenced, not
duplicated).
**location:** `src/pc2img/strategies/projection.py:189` (`return pcd.xyz[mask, self._xyz_column_selection], mask`)
vs `src/pc2img/strategies/projection.py:79` (`coords_raw, mask, mins, maxs = self.project_raw(pcd)`).
**defect:** two compounding defects on the same return line — (a) **arity:** `OrthographicProjection.project_raw`
returns a 2-tuple but the base `project()` unpacks a 4-tuple `(coords_raw, mask, mins, maxs)`;
(b) **indexing:** `pcd.xyz[mask, [c0, c1]]` mixes a length-M boolean-derived row index with a
length-2 column list, which numpy broadcasts elementwise instead of selecting an `(M, 2)` block.
**why-wrong:** the projection contract is `(coords_raw, mask, mins, maxs)`; the in-source
`# Todo: Update to pass min and max back!` (`projection.py:188`) acknowledges (a). The correct
column-select is `pcd.xyz[mask][:, cols]` (rows then columns). With the arity error, extent
normalization (`span = maxs - mins`, `projection.py:82`) can never run.
**repro:** `PROBE-M1b` (arity) `a,b,c,d = (xyz, mask)` → `ValueError: not enough values to unpack
(expected 4, got 2)`. `PROBE-M1a` (indexing) with 3 kept rows `xyz[mask,[0,1]]` →
`IndexError: shape mismatch: indexing arrays could not be broadcast together with shapes (3,) (2,)`;
with exactly 2 kept rows it **silently returns the diagonal** `[xyz[i0,0], xyz[i1,1]]` instead of
the `(2,2)` block — a silent wrong result. Both SURVIVED refutation.
**severity:** HIGH (silent wrong output / hard failure on a shipped projection path).
**pillar:** math.
**proving-test:** parametrize a tiny `PointCloudData` (or `.xyz`/`.nbPoints` stub) through
`OrthographicProjection(plane="xy").project(pcd, (W,H))`; assert it returns `(pts2d (M,2), mask (N,))`
with pixel coords in `[0,W-1]×[0,H-1]`, and that coords equal `xyz[mask][:, [0,1]]` normalized by the
ROI/data extent (not a diagonal). Currently raises before producing output.

### M-06 — Delaunay culling heuristics punch NaN holes into valid interior

**id:** `M-06`
**location:** `src/pc2img/strategies/interpolation.py:221` (`area_thresh = np.median(area) * 10`),
`:225` (MAD-based `aspect_ratio_thresh`), applied `:236` (`mask &= tri_is_good[simplices]`).
**defect:** query pixels whose enclosing triangle exceeds the median-scaled **area** or MAD-scaled
**aspect-ratio** threshold are set to `fill_value=nan` (`:139`). On sparse/anisotropic tiles this
drops *valid interior* triangles, not just hull-exterior ones.
**why-wrong:** scipy `LinearNDInterpolator` puts NaN **only outside the convex hull**
(`find_simplex == -1`). The extra heuristic culling silently corrupts interior output — a
correctness concern, not merely performance. Thresholds are unparameterized defaults (PERF-03 tracks
exposing them; QUAL-03 flags the silent corruption).
**repro:** `PROBE-M2b'` replicates the live culling math on an anisotropic scan-like sampling (dense
along x, sparse rows in y): of 468 triangles, **156 culled, 140 of them interior** (centroids well
inside the outer hull). The refuter's uniform-grid counter-probe (`PROBE-M2b`) culled 0 — confirming
the bug is data-dependent (anisotropy/sparsity triggers it). SURVIVED. **NON-FINDING:** the
barycentric weights themselves are correct (`interpolation.py:262-265`, `PROBE-M2a` err 7.1e-15) —
do NOT log.
**severity:** HIGH (silent interior data corruption on a shipped interpolation path).
**pillar:** math.
**proving-test:** build points on an anisotropic grid with a genuinely valid large interior triangle;
interpolate a known field; assert interior query points inside the hull are finite (not NaN).
Optionally assert parity with `scipy.LinearNDInterpolator` (NaN iff `find_simplex==-1`) when culling
is disabled.

### DSN-01 — `extend_cache_paths` nulls `interp_kwargs` via `dict.update()` (BUG-03)

**id:** `DSN-01` (a.k.a. **BUG-03**; source-only cross-reference — no pytest xfail encodes it).
**location:** `src/pc2img/tiled_generator.py:66-68`
(`updates["interp_kwargs"] = dict(self.interp_kwargs).update({...})`).
**defect:** the assignment stores the return value of `dict.update()`, which is always `None`.
**why-wrong:** when the branch fires (an interp-level `lazy_disk_cache_config` is present), the
subsequent `replace(self, **updates)` sets `interp_kwargs = None` instead of the extended dict —
silently discarding all interpolation kwargs on the per-tile settings, the opposite of intent.
**repro:** `PROBE-G` — `dict({"a": 1}).update({"b": 2})` → `None`; `... -> stores None: True`.
SURVIVED (the refuter's attempt to show `.update()` returns the dict failed).
**severity:** HIGH (silent config loss on the tiled path).
**pillar:** design.
**proving-test:** build a settings object with `interp_kwargs={"lazy_disk_cache_config":
LazyDiskCacheConfig(...)}`, call `.extend_cache_paths("t0")`, assert the result's `interp_kwargs` is a
dict containing the extended config (not `None`). Currently fails.

### DSN-02 — `__array_ufunc__` unconditionally raises → all `NDArrayOperatorsMixin` arithmetic dead (BUG-02)

**id:** `DSN-02` (a.k.a. **BUG-02**, redefined — see the exception-type note below).
**location:** `src/pc2img/image_cache/disk_backed_image_data.py:63-64`
(`def __array_ufunc__(...): raise NotImplementedError`).
**defect:** `DiskBackedImageData` inherits `NDArrayOperatorsMixin`, which routes every `+ - * / ...`
operator through `__array_ufunc__`. Because it always raises, no arithmetic on a
`DiskBackedImageData` works — the entire mixin arithmetic surface is dead.
**why-wrong:** the mixin is inert; any downstream `img_a + img_b` on cache objects raises at runtime
rather than computing (or cleanly delegating to numpy via the `NotImplemented` singleton).
**Exception-type history (load-bearing for the Phase-5 proving test):** the 04-RESEARCH / CONTEXT
anchor tables documented the observed exception as a **`TypeError`** — because the old
`raise NotImplemented` used the `NotImplemented` *singleton*, which is not a `BaseException`
(`TypeError: exceptions must derive from BaseException`). That is now stale: commit `b478a34`
(04-04 `ruff check --fix`, rule **F901** "raise NotImplemented → raise NotImplementedError") already
rewrote the line, so the **currently-observed** exception is **`NotImplementedError`**. The
exception-type half of BUG-02 is therefore inadvertently fixed; the design defect (arithmetic dead)
remains the live half.
**repro:** `PROBE-F` — current `raise NotImplementedError` → `NotImplementedError`; historical
`raise NotImplemented` → `TypeError`. Confirmed via `git show b478a34`. SURVIVED (redefined).
**severity:** HIGH (a whole public arithmetic surface is non-functional).
**pillar:** design.
**proving-test:** assert `pytest.raises(NotImplementedError)` on `dbid + dbid` **today** (assert
`NotImplementedError`, **NOT** `TypeError`). The Phase-5 fix either implements the ufunc protocol
(return a wrapped result / the `NotImplemented` singleton so numpy falls back) or removes the mixin.

---

## MEDIUM-HIGH

### M-02 — Perspective projection has no behind-camera (Z_c ≤ 0) guard

**id:** `M-02` (escalation flag — reserved for a 3rd-tiebreaker / empirical resolution in Phase 5).
**location:** `src/pc2img/strategies/projection.py:217`
(`uv = uv.arr[:, :2] / uv.arr[:, 2].reshape(-1, 1)`), in-bounds mask `:218-221`.
**defect:** points with camera-space depth `Z_c < 0` (behind the camera) are still divided through;
the double sign flip can place them at valid in-bounds pixel coordinates as phantom projections.
**why-wrong:** a correct pinhole projector (`K·[R|t]·X`) culls `Z_c ≤ 0` before/with the perspective
divide — `mask &= uv.arr[:,2] > 0`. No `> 0` depth test exists anywhere in `project`. Reviewed at the
shipped-projection bar (D-08).
**repro:** SURVIVED (reference-grounded, not empirically executed this session): the `@ pcd` contract
needs a real `PointCloudData` + pchandler `_TransformArray.__matmul__`, so no cheap standalone numpy
probe reproduces it. The missing depth test is unambiguous from source + reference. **Escalation:**
resolve empirically in Phase 5 with a real behind-camera point.
**severity:** MED-HIGH (WIP/perspective path, D-08 bar; escalate).
**pillar:** math.
**proving-test:** construct a minimal perspective setup with one point at `Z_c > 0` and one mirror
point at `Z_c < 0` that maps to the same pixel; assert the behind-camera point is masked out
(`mask[i] == False`), not projected in-bounds.

---

## MEDIUM

### M-07 — `nanconv` mutates the caller's input array in place

**id:** `M-07`
**location:** `src/pc2img/util.py:197` (`a[n] = 0`, inside `nanconv`, `:193`).
**defect:** `nanconv(a, k)` zeroes the caller's NaN entries in `a` in place, corrupting the input as a
side effect.
**why-wrong:** normalized convolution must fill a **copy**; the reference impl
`MultiScaleGradientFeature._smooth_with_nan` (`derivative_features.py`, `np.where(mask, image, 0.0)`)
never touches the input.
**repro:** `PROBE-M3b` passed `[[1,nan],[3,4]]`; after the call the NaN was gone
(`input NaN preserved? False`) — caller array corrupted. SURVIVED.
**severity:** MEDIUM (input corruption on a reachable smoothing path).
**pillar:** math.
**proving-test:** `a = array with NaN; snap = a.copy(); nanconv(a,k); assert
np.array_equal(np.isnan(a), np.isnan(snap))`.

### M-08 — `nanconv` float16 divide overflows to inf on realistic magnitudes

**id:** `M-08`
**location:** `src/pc2img/util.py:200-203` (conv sums cast to `np.float16`, divide in float16).
**defect:** the convolution numerator/denominator are cast to float16 (max ≈ 65504). For realistic
range/elevation values with a moderate kernel the summed numerator overflows to `inf`, so the
smoothed output is `inf`/`nan`; even below overflow, float16 loses significant bits.
**why-wrong:** normalized convolution should accumulate/divide in float32 (as `_smooth_with_nan`
does). float16 here buys neither correctness nor speed on CPU.
**repro:** `PROBE-M3d'` used value `12000.0` with a 7×7 ones-kernel → conv-sum ≈ 588000 → float16
`inf`; center result `inf` vs float64 `12000.0`. The smaller counter-probe (`PROBE-M3d`, value 5000 /
3×3, sum 45000 < 65504) gave err 0.0 — bug is magnitude/kernel-dependent but reachable with ordinary
range-image values. SURVIVED.
**severity:** MEDIUM (silent inf/nan output on realistic magnitudes).
**pillar:** math.
**proving-test:** `nanconv(full((16,16),12000.0), ones((7,7)))` → assert all outputs finite and within
float32 tolerance of the float64 reference.

### M-10 — `GradientFeature` hardcoded spacing `100` divides every gradient by 100

**id:** `M-10`
**location:** `src/pc2img/features/derivative_features.py:29`
(`grad = np.gradient(img, 100, axis=ax)`).
**defect:** the second positional arg to `np.gradient` is the sample spacing; `100` scales the
gradient by `1/100` regardless of the raster's true pixel spacing.
**why-wrong:** sibling features use unit or `pixel_size` spacing (`MultiScaleGradientFeature`,
`rrim.compute_slope`); `100` is an unexplained magic constant that mis-scales the reported slope
unless spacing is genuinely 100 units.
**repro:** `PROBE-M4a` on a ramp rising 1/px: `np.gradient(ramp,1)=1.0` (true) vs
`np.gradient(ramp,100)=0.01` — off by exactly 100×. SURVIVED.
**severity:** MEDIUM (wrong gradient magnitude on a shipped feature).
**pillar:** math.
**proving-test:** gradient of a unit-slope ramp → assert result ≈ 1.0 (or a documented, configurable
`pixel_size`), not 0.01.

### M-11 — `HillshadeFeature` aspect axis handedness rotated ~90° vs ESRI north-up

**id:** `M-11` (suspect / escalation — depends on the raster orientation convention Phase 5 pins).
**location:** `src/pc2img/features/derivative_features.py:135` (`x, y = np.gradient(values * self.z_factor)`),
`:137` (`aspect = np.arctan2(-x, y)`).
**defect:** with `x = ∂/∂row`, `y = ∂/∂col`, the computed aspect (and thus the illuminated side) is
consistently rotated ≈90° relative to the standard ESRI north-up aspect convention.
**why-wrong:** the illumination **magnitude** formula (`:141-143`) is confirmed correct (algebraic
equivalence to ESRI, `slope_var = π/2 − arctan|∇|`). The open question is only the axis→compass
mapping, which is well-defined only if the raster is north-up (row=south, col=east) — not guaranteed
for projected range images.
**repro:** `PROBE-M3'` swept azimuth 0–359: an east-rising ramp (`z=col`) is brightest at azimuth 0°
(ESRI expects ~90°); a south-rising ramp (`z=row`) is brightest at 270° (expects ~180°) — a
*consistent* 90° offset (transposed axis assignment, not random error). SURVIVED-with-caveat; suspect,
escalate. **NON-FINDING:** the illumination magnitude formula (`:141-143`) is correct — do NOT log.
**severity:** MEDIUM (suspect; correctness depends on the orientation contract).
**pillar:** math.
**proving-test:** decide the raster orientation contract; for a north-up raster, assert an east-facing
slope is brightest under an east azimuth (and dark under west). If range-image rows/cols are not
north-up, document the convention and assert internal consistency instead.

### M-03 — Perspective projection omits the translation `t` (origin-only camera)

**id:** `M-03` (resolve alongside M-02 in Phase 5).
**location:** `src/pc2img/strategies/projection.py:216`
(`(self.projection_matrix @ self.rotation_matrix) @ pcd`).
**defect:** composes projection/intrinsics with a rotation only; there is no camera-center
translation, so the model is valid only for a camera at the world origin.
**why-wrong:** full pinhole is `K·[R|t]·X`; a non-origin camera needs `t`. Whether the caller
pre-bakes `t` into the matrices is undocumented.
**repro:** SURVIVED (source + reference; escalation-linked to M-02): confirmed by inspection — no
translation term appears.
**severity:** MEDIUM (WIP/perspective path, D-08 bar).
**pillar:** math.
**proving-test:** project a point with a known non-origin camera center; assert the pixel matches
`K·[R|t]·X`, not the `t=0` result.

### DSN-03 — In-place raster mutation of the fetched array (ANCHOR #3)

**id:** `DSN-03` (design anchor #3).
**location:** `src/pc2img/features/derivative_features.py:80` (`np.divide(..., out=img)`) and `:81`
(`np.clip(img, 0, 1.0, out=img)`) in `NormalizedFeature.compute` (`:75`), where `img = fetch(self.base_feature)`.
**defect:** the feature writes into the fetched array in place.
**why-wrong:** it mutates a value owned by the raster-cache path. Safe **only** because the fetch
lambda in `manager._compute` wraps `np.asarray(self._get(n))` and `DiskBackedImageData.__array__`
always returns a copy. If any fetch path ever returns a view, this corrupts the cache.
`ClipPercentileFeature` copies first — the inconsistency is the smell.
**repro:** SURVIVED (currently masked). Stub a `fetch` returning a live array; after `compute`, the
input is overwritten (divided/clipped). The `__array__` copy masks it today; the finding is the latent
contract violation + Normalized/Clip inconsistency. Cross-ref M-12 (same lines, validation half).
**severity:** MEDIUM (latent copy-on-write contract violation).
**pillar:** design.
**proving-test:** patch `fetch` to return a known array `a`; run `NormalizedFeature(...).compute(None,
fetch)`; assert `a` is unmodified. Pair with a `ClipPercentile`-style `img = np.array(fetch(...),
copy=True)` fix.

### DSN-04 — `FeatureManager._base_features` never reset across `request()` calls

**id:** `DSN-04`
**location:** `src/pc2img/features/manager.py:22` (init `self._base_features = []`), `:28`
(`request` resets only `self._targets = []`), `:36` (`visit` appends to `_base_features`).
**defect:** `request()` sets `self._targets = []` but leaves `self._base_features` intact, so
successive `request()` calls append and accumulate base-feature specs.
**why-wrong:** `get_base_features()` (`:49-52`) recomputes every accumulated spec on each `generate()`,
so a reused generator does redundant work and can carry stale specs from a prior request.
**repro:** SURVIVED. One `FeatureManager`, call `request("gradient_x_range")` then `request("range")`
(without the cache guard hitting) → `_base_features` grows monotonically; `request()` contains no
`self._base_features = []` reset.
**severity:** MEDIUM (latent correctness/perf bug on generator reuse).
**pillar:** design.
**proving-test:** call `request()` twice on the same manager with overlapping targets; assert
`len(mgr._base_features)` reflects only the latest request's uncached base features.

### DSN-05 — Divergent registry mechanisms (ANCHOR #2)

**id:** `DSN-05` (design anchor #2).
**location:** `src/pc2img/strategies/registry.py:38,63,92` (`StrategyRegistry`, `KeyError`) vs
`src/pc2img/features/registry.py:33,39,48,65` (`FeatureRegistry`, `RuntimeError`).
**defect:** two independent registry contracts coexist. `StrategyRegistry`: string-key map,
kwarg-filtering `create()`, reverse `key_of()`, misses raise **`KeyError`**. `FeatureRegistry`:
regex-pattern DSL, default-fallback class, errors raise **`RuntimeError`**.
**why-wrong:** different error types, lifecycles, and coercion protocols, so callers and tests cannot
treat "a registry" uniformly. **Sub-finding:** `FeatureRegistry.match()` instantiates the class just to
read `.dependencies` (`inst = cls(**spec.params)`, `features/registry.py:48`) and it is instantiated
again in `manager._compute` — a side-effectful, duplicated construction.
**repro:** SURVIVED. `PROJECTIONS.get_strategy("nope")` → `KeyError`; `FEATURES.match("nope")` with no
default → `RuntimeError`. Divergent contracts directly observable.
**severity:** MEDIUM (structural; unifying carries behavioral risk → LOG).
**pillar:** design.
**proving-test:** a single registry protocol (or adapter) with one miss-exception type; test both
families raise the same error class and that `match()` reads dependencies without instantiating (e.g. a
classmethod `dependencies_for(params)`).

### DSN-06 — Omitted `lazy_disk_cache_config` not coerced (coerce-null asymmetry)

**id:** `DSN-06` (the live xfail `tests/test_point_cloud_image_generator.py:35` encodes exactly this).
**location:** `src/pc2img/core.py:63` (`@validate_call`), `:70` (param default `= None`), coercer wired
via `LazyDiskCacheConfigLike` (`:59`).
**defect:** `BeforeValidator(coerce_lazy_cfg)` runs when `None` is passed **explicitly**, but pydantic
v2 `@validate_call` does not validate **omitted defaults**, so an omitted config stays `None`
uncoerced.
**why-wrong:** with the arg omitted, `FeatureManager(..., lazy_disk_cache_config=None)` is invoked and
store construction fails before `cache_store.cache_dir` exists. Explicit `None` works; omission does
not — a surprising asymmetry.
**repro:** SURVIVED. `PointCloudImageGenerator(pcd, (1,1), proj, interp)` (omit config) fails; passing
`lazy_disk_cache_config=None` succeeds. The two sibling xfail/pass tests prove the asymmetry.
**severity:** MEDIUM (behavioral; a live xfail already encodes it).
**pillar:** design.
**proving-test:** the existing xfail `test_constructor_normalizes_omitted_lazy_disk_cache_config`
(`strict=False`) *is* the proving test; Phase 5 makes the omitted-arg path coerce (default to a
sentinel and run `coerce_lazy_cfg`), flipping xfail → pass.

### DSN-07 — Mutable constructed default `LazyDiskCacheConfig()` (seed E, B008×4)

**id:** `DSN-07` (overlaps the 04-04 deferred B008 breadcrumbs).
**location:** `src/pc2img/features/manager.py:17`; `src/pc2img/tiled_generator.py:96` and `:109`;
`src/pc2img/image_cache/disk_backed_image_store.py:22`.
**defect:** a single `LazyDiskCacheConfig()` instance is constructed once at def-time and shared as the
default across all calls that omit the arg (ruff **B008** flags all four sites).
**why-wrong:** shared-mutable-default class of bug; `core.py:34-43` already models the correct
`None`-sentinel + `coerce_lazy_cfg` pattern, so the fix template exists in-repo.
**repro:** SURVIVED. The default's identity is stable across instances; if any code path mutates the
config in place, it leaks across managers. (`LazyDiskCacheConfig` may be effectively frozen today, so
kept MEDIUM rather than HIGH.)
**severity:** MEDIUM (shared-mutable-default; low live-mutation risk today).
**pillar:** design.
**proving-test:** assert two default-constructed managers do not share the same config object identity
after the `None`-sentinel fix.

---

## LOW-MEDIUM

### M-05 — Spherical projection: linear azimuth mapping breaks at the ±180° seam / inverted span

**id:** `M-05`
**location:** `src/pc2img/strategies/projection.py:120-121` (`mins = [fov.left, fov.top]`,
`maxs = [fov.right, fov.bottom]`) → `:82-84` (`span = maxs - mins; span[span == 0] = 1;
norm = (coords - mins)/span`).
**defect:** linear `(h-left)/(right-left)` mis-maps azimuth when the FoV straddles the ±180°/0–360°
discontinuity (e.g. `left=170, right=-170` → span `−340`), and inverts when `top > bottom` in the
elevation metric. The `span[span==0]=1` guard covers only the zero case, not a negative span.
**why-wrong:** equirectangular mapping must unwrap azimuth across the seam so the mapping stays
monotonic within the FoV.
**repro:** SURVIVED (math, conditional). A `left=170, right=-170` FoV yields `span=-340`, so `norm`
runs backwards → out-of-`[0,1]` / reversed pixel columns; no seam handling exists. Conditional on
seam-crossing FoVs occurring in the data → LOW-MED.
**severity:** LOW-MED (conditional on seam-crossing FoVs).
**pillar:** math.
**proving-test:** build a FoV crossing the ±180° seam; assert the pixel-column mapping is monotonic and
within `[0, W-1]` across the seam.

### M-09 — `convert_to_image` all-NaN + `normalize=True` → empty-reduction ValueError

**id:** `M-09`
**location:** `src/pc2img/util.py:385` (`lo = x[finite].min()`), condition `:384`, `finite` `:383`.
**defect:** for an all-NaN 2D input, `finite = np.isfinite(x)` is empty. The condition at `:384` uses
`.min(initial=…)` and is safe, but when `normalize=True` the body at `:385-386` re-reduces the empty
selection without an `initial` → crash.
**why-wrong:** an all-invalid raster should degrade to a constant/zero image (as the `hi>lo`
else-branch at `:390` already does), not raise.
**repro:** `PROBE-M3e` — all-NaN 4×4, `normalize=True`: finite count 0 → `ValueError: zero-size array
to reduction operation minimum which has no identity`. SURVIVED.
**severity:** LOW-MED (conditional on all-NaN input).
**pillar:** math.
**proving-test:** `convert_to_image(full((4,4),nan), normalize=True)` → assert it returns a valid uint8
image (constant), not a raise.

---

## LOW

### M-04 — Perspective `project_raw` dead override + undocumented `@ pcd` matmul contract

**id:** `M-04`
**location:** `src/pc2img/strategies/projection.py:195` (`project_raw` → `raise NotImplementedError`),
`:216-217` (`@ pcd` then `.arr`).
**defect:** `project_raw` is an unreachable dead override (base `project` is overridden), and the
projection relies on an undocumented pchandler `_TransformArray.__matmul__(pcd) → .arr` contract that
will throw before any math if pchandler changes it.
**why-wrong:** structural dead code + hidden dependency on a private pchandler operator; low blast
radius (WIP path).
**repro:** SURVIVED (LOW, source-grounded); no numeric probe needed.
**severity:** LOW (WIP path).
**pillar:** math.
**proving-test:** assert `PerspectiveProjection.project` works against the documented pchandler
transform type, and either remove `project_raw` or make it a clear `NotImplementedError` with
rationale.

### M-12 — `NormalizedFeature` percentile validation commented out

**id:** `M-12` (cross-refs design anchor #3 / DSN-03 — same lines, in-place mutation half).
**location:** `src/pc2img/features/derivative_features.py:68`
(`# if not(0 <= float(low) < float(high) <= 100):`), compounded by `:80-81` (in-place `out=img`).
**defect:** the low/high percentile bounds check is commented out, so the feature silently accepts
`low > high` or out-of-`[0,100]` values (unlike `ClipPercentileFeature`, which validates).
**why-wrong:** dead-code-by-inspection; the sibling `ClipPercentileFeature` validates identical bounds,
so the omission is an inconsistency that admits nonsense percentiles.
**repro:** SURVIVED. `PROBE-M4b` confirms the in-place `out=img` mutates the fetched array (safe today
only because `DiskBackedImageData.__array__` returns a copy); the missing validation is
dead-code-by-inspection.
**severity:** LOW (math-adjacent; validation gap).
**pillar:** math.
**proving-test:** assert `normalized_range_90_10` (low>high) raises `ValueError`, mirroring
`ClipPercentileFeature`; assert `compute` does not mutate its input (shared with DSN-03).

### M-13 — RRIM openness ray offsets under-sample near-axis directions

**id:** `M-13`
**location:** `src/pc2img/features/rrim.py:196-204` (`dx=int(rint(cos·step))`, `dy=int(rint(sin·step))`,
dedup via `seen` at `:194,199,201`).
**defect:** rounding each ray step to integer pixels then de-duplicating `(dy,dx)` can drop samples
along near-horizontal/vertical rays; direction sampling also ignores `pixel_size` anisotropy (only the
distance term uses it, `:202`).
**why-wrong:** a sampling-fidelity concern — near-axis rays lose steps to integer rounding + dedup;
anisotropic pixels are not reflected in the direction geometry.
**repro:** SURVIVED (LOW, source-grounded). The openness mean / `90−max` math itself is correct (see
CONFIRMED-CORRECT); this is sampling fidelity only, minor.
**severity:** LOW (sampling fidelity).
**pillar:** math.
**proving-test:** assert each direction yields a monotonic, deduped ray whose sampled count is stable
across `max_distance`, and that anisotropic `pixel_size` is reflected in the direction geometry (not
only the distance).

### DSN-08 — Missing dependency-cycle guard in `request().visit` (ANCHOR #4, latent)

**id:** `DSN-08` (design anchor #4; downgraded to LOW/latent — empirical confirmation pending Phase 5).
**location:** `src/pc2img/features/manager.py:32-39` (`visit` recurses `spec.dependencies` with no
visited-set; the only guard `if spec.name in self._raster_cache: return` at `:33` short-circuits only
already-cached names).
**defect:** `visit()` recurses through `spec.dependencies` unconditionally; there is no visited-set, so
a self- or transitively-cyclic feature name would recurse unboundedly → `RecursionError`.
**why-wrong:** defensive gap. The cache-hit guard does not detect cycles.
**repro:** DOWNGRADED to LOW. With the currently-registered features, dependencies are derived by
stripping a regex prefix (`gradient_x_<base>` → `<base>`), so every dependency edge strictly shrinks
the name — no current feature graph can form a cycle, so no live `RecursionError` reproduces today. The
structural gap is real but unreachable with today's feature set.
**severity:** LOW (latent; structurally reachable, not with today's registered features).
**pillar:** design.
**proving-test:** register a throwaway feature whose `dependencies` point back at itself; assert
`request()` raises a clear `ValueError("dependency cycle: ...")` rather than `RecursionError`. Then add
the visited-set to `visit()`.

### DSN-09 — Pickle load of arbitrary `*.pkl` cache files (seed J / security, STRIDE T-04-J)

**id:** `DSN-09` (security; surfaced-and-logged — fix + proving test is Phase 5/6 per D-02).
**location:** `src/pc2img/image_cache/disk_backed_image_store.py:49` (`pickle.load` in `__getitem__`),
`:38` (cache-dir `*.pkl` scan), `:28` (`tempfile.mkdtemp()` default cache dir); offloaded features are
re-loaded via `__setstate__`.
**defect:** the store `pickle.load`s any `*.pkl` found in its cache dir on item access and on
unpickling.
**why-wrong:** `pickle.load` executes arbitrary code during deserialization → Tampering/RCE if the
cache dir is ever attacker-controlled or shared.
**trust boundary (recorded):** cache dirs default to process-local `tempfile.mkdtemp()`
(`disk_backed_image_store.py:28`) when no `cache_path` is configured, so today the boundary is a
trusted, process-owned temp dir. Risk materializes only if a user supplies/points a shared cache dir.
**STRIDE T-04-J** (Tampering/RCE, high, disposition = mitigate/log). Carrying it here satisfies the
ASVS L1 `block_on:high` gate by surfacing-and-logging.
**repro:** SURVIVED as surfaced-and-logged. The `tempfile.mkdtemp` default makes it non-exploitable in
the default flow (hence not a Phase-4 fix), but the `pickle.load` sink is real and must be recorded.
**severity:** LOW *(as a Phase-4 action — surfaced-and-logged only)*; underlying threat is **HIGH**,
gated by the trust boundary above.
**pillar:** design/security.
**proving-test:** document the "cache dirs must be trusted" contract; if shared/user-supplied dirs are
ever supported, add provenance checks or a non-executable array format (e.g. `.npy`/safetensors)
instead of pickle.

### DSN-10 — Circular-import sensitivity (seed H)

**id:** `DSN-10`
**location:** `src/pc2img/tiled_generator.py:19` (`from pc2img import PointCloudImageGenerator`).
**defect:** a submodule imports the top-level package barrel rather than the defining module
(`pc2img.core`), coupling it to package-init import ordering.
**why-wrong:** fragile — a future reorder of `pc2img/__init__.py` (which also triggers strategy
registration side effects) could produce a partially-initialized-module `ImportError`.
**repro:** DOWNGRADED to LOW. The import currently succeeds (ordering happens to work), so no live
failure; kept as a LOW design smell (latent fragility).
**severity:** LOW (latent fragility).
**pillar:** design.
**proving-test:** import `pc2img.tiled_generator` first in a fresh interpreter; assert it succeeds. Fix
by importing from `pc2img.core` directly.

### DSN-11 — `_default_cls` non-optional attribute assigned `None` (seed D, typing)

**id:** `DSN-11`
**location:** `src/pc2img/features/registry.py:27`
(`self._default_cls: type[BaseFeatureStrategy] = None`).
**defect:** annotated as a non-optional class object but initialized to `None`.
**why-wrong:** the annotation lies about the runtime value; pyright *basic* tolerates it, but it masks
the real `Optional` contract and the `if self._default_cls:` fallback at `:57`.
**repro:** SURVIVED (trivial). The annotation/value mismatch is on the line as written; no counter-check
needed.
**severity:** LOW (typing; mechanical).
**pillar:** design (typing).
**proving-test:** annotate `type[BaseFeatureStrategy] | None = None`; assert pyright (or a targeted
reveal_type) treats `_default_cls` as optional and the `:57` truthy fallback is well-typed.

---

## FIXED — recorded, not re-logged

**DSN-F1 — Broken `make_generator` factory (ANCHOR #1) — FIXED in 04-03.**
`src/pc2img/registry.py` is now comment-only. The factory called `PointCloudImageGenerator(pcd, proj,
interp)` against the 5-parameter ctor `(pcd, img_res, proj, interp, lazy_disk_cache_config)`,
mis-landing `proj`→`img_res` and `interp`→`proj`. 04-03 **deleted** it (zero callers in `src/`,
`tests/`, `scripts/`) rather than repairing, leaving an explanatory comment. **Disposition:**
FIXED-with-smoke — anchor #1 satisfied by removal. Smoke: `python -c "import pc2img.registry"` imports
clean; `make_generator` no longer exists.

**BUG-02 exception-type half — FIXED (inadvertently) in 04-04.** The `raise NotImplemented` →
`raise NotImplementedError` correction (ruff F901, commit `b478a34`) is already applied. Tracked inside
**DSN-02** so the Phase-5 proving test asserts `NotImplementedError`. The residual *design* defect
(mixin arithmetic dead) is the live half — see DSN-02.

## Deferred ruff / hygiene breadcrumbs (04-04, D-02 — carried, not the review focus)

- **BUG-04 (E402×9):** `rrim.py` module-level imports after the module docstring/`__all__` trigger
  ruff **E402**; source-only, no xfail. Phase-5 cleanup item.
- **C901×5:** cyclomatic-complexity findings (mostly the math-track projection/interpolation
  functions). Phase-5 refactor candidates; re-verified present this session.
- **B008×4:** the mutable constructed `LazyDiskCacheConfig()` defaults — the same four sites as
  **DSN-07** (seed E). Fixed together in Phase 5.
- **Stale comment** `# class StrategyRegistry(Generic[T]):` at `strategies/registry.py:28` — survived
  04-04 ERA001. Mechanical delete (LOW hygiene).
- **Dead commented validation** `# if not(0 <= float(low) < float(high) <= 100):` at
  `derivative_features.py:68` — same line as **M-12**; Phase-5 re-enable + test.

## CONFIRMED-CORRECT — explicitly NOT logged (recorded so Phase 5 does not re-open)

- **Barycentric weights** (`interpolation.py:262-265`) — reproduce a linear field exactly (`PROBE-M2a`,
  err 7.1e-15).
- **Hillshade illumination magnitude formula** (`derivative_features.py:141-143`) — algebraically
  equivalent to ESRI (only the aspect handedness, M-11, is suspect).
- **RRIM differential-openness** `structure = 0.5·(positive − negative)` (`rrim.py:376` et al.) —
  matches Yokoyama (2002).
- **RRIM positive/negative openness + slope primitives** (`rrim.py:219-220,265-291`) — match the
  reference formulas.
- **`nanconv` integer-dtype** candidate — DROPPED: `np.isnan(int)` returns all-`False` (no raise) under
  numpy 2.0.2; no reproducible numeric bug on the int path.

---

## Summary table (most-severe first)

| id | file:line | severity | pillar | one-line | verdict |
|----|-----------|----------|--------|----------|---------|
| M-01 (BUG-01) | projection.py:189 / :79 | HIGH | math | orthographic 2-tuple arity + mixed row/col index | SURVIVED |
| M-06 | interpolation.py:221/:225/:236 | HIGH | math | Delaunay culling → interior NaN holes | SURVIVED |
| DSN-01 (BUG-03) | tiled_generator.py:66-68 | HIGH | design | extend_cache_paths nulls interp_kwargs (`.update()`→None) | SURVIVED |
| DSN-02 (BUG-02) | disk_backed_image_data.py:63-64 | HIGH | design | `__array_ufunc__` arithmetic dead (now NotImplementedError, was TypeError) | SURVIVED (redefined) |
| M-02 | projection.py:217 | MED-HIGH | math | perspective no Z_c≤0 behind-camera guard | SURVIVED (escalate) |
| M-07 | util.py:197 | MED | math | nanconv mutates caller input in place | SURVIVED |
| M-08 | util.py:200-203 | MED | math | nanconv float16 divide overflows to inf | SURVIVED |
| M-10 | derivative_features.py:29 | MED | math | GradientFeature magic-100 spacing | SURVIVED |
| M-11 | derivative_features.py:135/:137 | MED | math | hillshade aspect handedness ~90° off | SURVIVED (suspect) |
| M-03 | projection.py:216 | MED | math | perspective omits translation t | SURVIVED |
| DSN-03 (anchor #3) | derivative_features.py:80-81 | MED | design | in-place raster mutation of fetched array | SURVIVED (masked) |
| DSN-04 | manager.py:22/:28/:36 | MED | design | `_base_features` never reset across request() | SURVIVED |
| DSN-05 (anchor #2) | strategies/registry.py vs features/registry.py | MED | design | divergent registry contracts (KeyError vs RuntimeError) | SURVIVED |
| DSN-06 | core.py:63/:70 | MED | design | omitted lazy_disk_cache_config not coerced | SURVIVED |
| DSN-07 | manager.py:17; tiled_generator.py:96/:109; disk_backed_image_store.py:22 | MED | design | mutable constructed LazyDiskCacheConfig() default (B008) | SURVIVED |
| M-05 | projection.py:120-121/:82-84 | LOW-MED | math | spherical azimuth seam / inverted span | SURVIVED |
| M-09 | util.py:385 | LOW-MED | math | convert_to_image all-NaN + normalize → ValueError | SURVIVED |
| M-04 | projection.py:195/:216-217 | LOW | math | perspective dead project_raw + @pcd contract | SURVIVED |
| M-12 | derivative_features.py:68/:80-81 | LOW | math | NormalizedFeature validation commented out | SURVIVED |
| M-13 | rrim.py:196-204 | LOW | math | RRIM ray offsets under-sample near-axis | SURVIVED |
| DSN-08 (anchor #4) | manager.py:32-39 | LOW | design | missing dependency-cycle guard (latent) | DOWNGRADED |
| DSN-09 (T-04-J) | disk_backed_image_store.py:49/:38/:28 | LOW (underlying HIGH) | design/security | pickle load of arbitrary cache files | SURVIVED (logged) |
| DSN-10 | tiled_generator.py:19 | LOW | design | circular-import sensitivity | DOWNGRADED |
| DSN-11 | features/registry.py:27 | LOW | design | `_default_cls` typed non-optional but None | SURVIVED |
| — | registry.py (module) | FIXED | design | broken make_generator (anchor #1) — deleted in 04-03 | FIXED |

**Totals:** 24 active findings (4 HIGH · 1 MED-HIGH · 10 MED · 2 LOW-MED · 7 LOW) + 1 FIXED anchor.
Design track: DSN-01..DSN-11 (+ DSN-F1). Math track: M-01..M-13. BUG-01 = M-01 (single entry,
cross-referenced). This is the canonical Phase-5 BUG-05 work-list.
