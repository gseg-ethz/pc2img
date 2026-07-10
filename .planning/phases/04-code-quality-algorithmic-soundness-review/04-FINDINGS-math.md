# Phase 04 — Math-track FINDINGS (QUAL-03, plan 04-06)

> Numerically-probed, deduped math findings in the D-06 schema, **most-severe first**.
> All findings are **LOG** (Phase-5 BUG-05 per D-02) — this phase surfaces, Phase 5 fixes
> each with the sketched proving test. This is the **math half**; 04-07 merges it with the
> design half (`04-FINDINGS-design.md`) into the canonical `04-FINDINGS.md`.
>
> **Evidence retention (D-05):** the raw FIND candidates live in
> `04-FINDINGS-math-candidates.md` (distinct file); each finding below records the
> **independent refuter's concrete numeric-probe verdict** (inputs → output, survived /
> dropped / downgraded). The two-file split + per-entry probe result is the evidence a real
> find → probe → refute pass ran, not a single-reader summary.
>
> Runtime probed against: **numpy 2.0.2, scipy 1.18.0** (verified). Every `file:line`
> re-grepped against the live post-04-04 tree (Pitfall 1). BUG-01 is a **source-only**
> cross-reference — no pytest xfail encodes it (live xfails cover only the null
> lazy-cache-config case at `tests/test_point_cloud_image_generator.py:35` and
> DiskBackedImageData lifecycle cases at `tests/test_disk_backed_image_data.py:50`).

**Severity legend:** HIGH = silent wrong output or hard failure on a shipped path ·
MEDIUM = wrong/corrupt output on a reachable path or config · LOW = latent / conditional.

---

## M-01 — Orthographic projection is unusable: 2-tuple arity + mixed-index rows/cols (BUG-01) · HIGH

- **file:line:** `strategies/projection.py:189` (`return pcd.xyz[mask, self._xyz_column_selection], mask`)
  vs `strategies/projection.py:79` (`coords_raw, mask, mins, maxs = self.project_raw(pcd)`)
- **defect:** two compounding defects on the same return line —
  (a) **arity:** `project_raw` returns a 2-tuple but the base `project()` unpacks 4;
  (b) **indexing:** `pcd.xyz[mask, [c0,c1]]` mixes a length-M boolean-derived row index with a
  length-2 column list.
- **why-wrong (reference §3.2):** the projection contract is `(coords_raw, mask, mins, maxs)` —
  the in-source `# Todo: Update to pass min and max back!` (`:188`) acknowledges (a). numpy
  advanced indexing broadcasts the two index arrays elementwise, so `xyz[mask,[0,1]]` is not
  the intended `(M,2)` block; correct form is `pcd.xyz[mask][:, cols]` (rows then columns).
  Extent normalization (`span = maxs - mins`, `:82`) can never run.
- **numeric repro / REFUTER VERDICT — SURVIVED (2 probes):**
  - `PROBE-M1b` (arity): `a, b, c, d = (xyz, mask)` → `ValueError: not enough values to unpack (expected 4, got 2)`.
  - `PROBE-M1a` (indexing): with 3 kept rows `xyz[mask,[0,1]]` → `IndexError: shape mismatch:
    indexing arrays could not be broadcast together with shapes (3,) (2,)`; with exactly 2 kept
    rows it silently returns the **diagonal** `[xyz[i0,0], xyz[i1,1]]` instead of the `(2,2)`
    block — a *silent wrong result*, the more dangerous branch. In practice the IndexError in
    `project_raw` fires first (M≠2), so the arity error is only reached in the M==2 coincidence.
- **severity:** HIGH · **pillar:** math · **disposition:** LOG (BUG-01)
- **proving-test sketch (Phase 5):** parametrize a tiny `PointCloudData` (or stub with `.xyz`,
  `.nbPoints`) through `OrthographicProjection(plane="xy").project(pcd, (W,H))`; assert it
  returns `(pts2d (M,2), mask (N,))` with pixel coords in `[0,W-1]×[0,H-1]`, and that the
  returned coords equal `xyz[mask][:, [0,1]]` normalized by the ROI/data extent (not a
  diagonal). Currently raises before producing output.

---

## M-06 — Delaunay culling heuristics punch NaN holes into valid interior · HIGH

- **file:line:** `strategies/interpolation.py:221` (`area_thresh = np.median(area) * 10`),
  `:225` (MAD-based `aspect_ratio_thresh`), applied `:233-236` (`mask &= tri_is_good[simplices]`)
- **defect:** query pixels whose enclosing triangle exceeds the median-scaled **area** or
  MAD-scaled **aspect-ratio** threshold are set to `fill_value=nan`. On sparse/anisotropic
  tiles this drops *valid interior* triangles, not just hull-exterior ones.
- **why-wrong (reference §3.4, Pitfall 3):** scipy `LinearNDInterpolator` semantics put NaN
  **only outside the convex hull** (`find_simplex == -1`). The extra heuristic culling silently
  corrupts interior output — a correctness concern, not merely performance. Thresholds are
  unparameterized defaults (PERF-03 tracks exposing them; QUAL-03 flags the silent corruption).
- **numeric repro / REFUTER VERDICT — SURVIVED:** `PROBE-M2b'` replicates the live culling math
  on an anisotropic scan-like sampling (dense along x, sparse rows in y): of 468 triangles,
  **156 culled, 140 of them interior** (centroids well inside the outer hull, e.g. (7.6,1.9),
  (1.1,8.1)). Those interior pixels become NaN despite lying inside the data footprint. The
  refuter's counter-attempt (uniform grid, `PROBE-M2b`) culls 0 — confirming the bug is
  *data-dependent* (anisotropy/sparsity triggers it), which is exactly the silent-hole hazard.
- **severity:** HIGH · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** build points on an anisotropic grid with a genuinely
  valid large interior triangle; interpolate a known field; assert interior query points inside
  the hull are finite (not NaN). Optionally assert parity with `scipy.LinearNDInterpolator`
  (NaN iff `find_simplex==-1`) when culling is disabled.
- **NON-FINDING (recorded so it is not mis-logged):** the **barycentric weights themselves are
  correct** — `PROBE-M2a` interpolated a linear field `f=2x−3y+1.5` and reproduced it with max
  abs error `7.1e-15` (float only). Do not log `interpolation.py:262-265` as a bug.

---

## M-02 — Perspective projection has no behind-camera (Z_c ≤ 0) guard · MEDIUM-HIGH (escalation)

- **file:line:** `strategies/projection.py:217` (`uv = uv.arr[:,:2] / uv.arr[:,2].reshape(-1,1)`),
  in-bounds mask `:218-221`
- **defect:** points with camera-space depth `Z_c < 0` (behind the camera) are still divided
  through; the double sign flip can place them at valid in-bounds pixel coordinates as phantom
  projections.
- **why-wrong (reference §3.3, pinhole `K·[R|t]·X`):** a correct pinhole projector culls
  `Z_c ≤ 0` before/with the perspective divide — `mask &= uv.arr[:,2] > 0`. Reviewed at the
  shipped-projection bar per D-08.
- **REFUTER VERDICT — SURVIVED (reference-grounded, not empirically executed):** the `@ pcd`
  contract requires a real `PointCloudData` + pchandler `_TransformArray.__matmul__`, so no
  cheap standalone numpy probe reproduces it this session. The defect is unambiguous from the
  source + reference (no `> 0` depth test exists anywhere in `project`). **Escalation flag:**
  this is a HIGH-severity math item the plan calls out for a 3rd-tiebreaker — resolve
  empirically in Phase 5 with a real behind-camera point.
- **severity:** MEDIUM-HIGH (WIP path, D-08 bar) · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** construct a minimal perspective setup with one point at
  `Z_c > 0` and one mirror point at `Z_c < 0` that maps to the same pixel; assert the
  behind-camera point is masked out (`mask[i] == False`), not projected in-bounds.

---

## M-07 — `nanconv` mutates the caller's input array in place · MEDIUM

- **file:line:** `util.py:197` (`a[n] = 0`)
- **defect:** `nanconv(a, k)` zeroes the caller's NaN entries in `a` in place, corrupting the
  input as a side effect.
- **why-wrong (reference §3.5, normalized convolution):** must fill a **copy**; the correct
  reference impl `MultiScaleGradientFeature._smooth_with_nan` (`derivative_features.py:361`,
  `np.where(mask, image, 0.0)`) never touches the input.
- **numeric repro / REFUTER VERDICT — SURVIVED:** `PROBE-M3b` passed `[[1,nan],[3,4]]`; after
  the call the NaN was gone (`input NaN preserved? False`) — caller array corrupted.
- **severity:** MEDIUM · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** `a = array with NaN; snap = a.copy(); nanconv(a,k);
  assert np.array_equal(np.isnan(a), np.isnan(snap))`.

---

## M-08 — `nanconv` float16 divide overflows to inf on realistic magnitudes · MEDIUM

- **file:line:** `util.py:200-203` (conv sums cast to `np.float16`, divide in float16)
- **defect:** the convolution numerator/denominator are cast to float16 (max ≈ 65504). For
  realistic range/elevation values with a moderate kernel the summed numerator overflows to
  `inf`, so the smoothed output is `inf`/`nan`; even below overflow, float16 loses significant
  bits.
- **why-wrong (reference §3.5):** normalized convolution should accumulate/divide in float32
  (as `_smooth_with_nan` does). float16 here buys neither correctness nor speed on CPU.
- **numeric repro / REFUTER VERDICT — SURVIVED:** `PROBE-M3d'` used value `12000.0` with a 7×7
  ones-kernel → conv-sum ≈ 588000 → **float16 `inf`**; center result `inf` vs float64 `12000.0`.
  The refuter's smaller counter-probe (`PROBE-M3d`, value 5000 / 3×3, sum 45000 < 65504) gave
  err `0.0` — confirming the bug is magnitude/kernel-dependent, not universal, but reachable
  with ordinary range-image values.
- **severity:** MEDIUM · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** `nanconv(full((16,16),12000.0), ones((7,7)))` → assert all
  outputs finite and within float32 tolerance of the float64 reference.

---

## M-10 — `GradientFeature` hardcoded spacing `100` divides every gradient by 100 · MEDIUM

- **file:line:** `features/derivative_features.py:29` (`grad = np.gradient(img, 100, axis=ax)`)
- **defect:** the second positional arg to `np.gradient` is the sample spacing; `100` scales
  the gradient by `1/100` regardless of the raster's true pixel spacing.
- **why-wrong (reference §3.6):** sibling features use unit or `pixel_size` spacing
  (`MultiScaleGradientFeature`, `rrim.compute_slope`); `100` is an unexplained magic constant
  that mis-scales the reported slope unless spacing is genuinely 100 units.
- **numeric repro / REFUTER VERDICT — SURVIVED:** `PROBE-M4a` on a ramp rising 1/px:
  `np.gradient(ramp,1)=1.0` (true) vs `np.gradient(ramp,100)=0.01` — off by exactly 100×.
- **severity:** MEDIUM · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** gradient of a unit-slope ramp → assert result ≈ 1.0 (or a
  documented, configurable `pixel_size`), not 0.01.

---

## M-11 — `HillshadeFeature` aspect axis handedness rotated ~90° vs ESRI north-up · MEDIUM (suspect / escalation)

- **file:line:** `features/derivative_features.py:135` (`x, y = np.gradient(values*z_factor)`),
  `:137` (`aspect = np.arctan2(-x, y)`)
- **defect:** with `x = ∂/∂row`, `y = ∂/∂col`, the computed aspect (and thus the illuminated
  side) is consistently rotated ≈90° relative to the standard ESRI north-up aspect convention.
- **why-wrong (reference §3.6):** the **illumination magnitude formula (`:141-143`) is
  confirmed correct** (algebraic equivalence to ESRI, `slope_var = π/2 − arctan|∇|`). The open
  question is only the axis→compass mapping, which is well-defined only if the raster is
  north-up (row=south, col=east) — not guaranteed for projected range images.
- **numeric repro / REFUTER VERDICT — SURVIVED-with-caveat:** `PROBE-M3'` swept azimuth 0–359:
  an **east-rising** ramp (`z=col`) is brightest at azimuth **0°** (ESRI north-up expects ~90°);
  a **south-rising** ramp (`z=row`) is brightest at **270°** (expects ~180°) — a *consistent*
  90° offset. Consistency points to a transposed axis assignment rather than random error, but
  correctness depends on the intended raster orientation → **suspect, escalate** for a
  3rd-tiebreaker + orientation-convention decision in Phase 5. Not logged as a definite bug.
- **severity:** MEDIUM (suspect) · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** decide the raster orientation contract; for a north-up
  raster, assert an east-facing slope is brightest under an east azimuth (and dark under west).
  If range-image rows/cols are not north-up, document the convention and assert internal
  consistency instead.
- **NON-FINDING (recorded):** the hillshade **illumination magnitude** formula is correct — do
  not log `:141-143`.

---

## M-03 — Perspective projection omits the translation `t` (origin-only camera) · MEDIUM

- **file:line:** `strategies/projection.py:216` (`(self.projection_matrix @ self.rotation_matrix) @ pcd`)
- **defect:** composes projection/intrinsics with a rotation only; there is no camera-center
  translation, so the model is valid only for a camera at the world origin.
- **why-wrong (reference §3.3):** full pinhole is `K·[R|t]·X`; a non-origin camera needs `t`.
- **REFUTER VERDICT — SURVIVED (source + reference; escalation-linked to M-02):** confirmed by
  inspection — no translation term appears; whether the caller pre-bakes `t` into the matrices
  is undocumented. Resolve alongside M-02 in Phase 5.
- **severity:** MEDIUM (WIP path, D-08 bar) · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** project a point with a known non-origin camera center;
  assert the pixel matches `K·[R|t]·X`, not the `t=0` result.

---

## M-05 — Spherical projection: linear azimuth mapping breaks at the ±180° seam / inverted span · LOW-MEDIUM

- **file:line:** `strategies/projection.py:120-121` (`mins=(left,top)`, `maxs=(right,bottom)`) →
  `:82-85` (`span = maxs-mins; span[span==0]=1; norm=(coords-mins)/span`)
- **defect:** linear `(h-left)/(right-left)` mis-maps azimuth when the FoV straddles the
  ±180°/0–360° discontinuity (e.g. `left=170, right=-170` → span `−340`), and inverts when
  `top > bottom` in the elevation metric. The `span[span==0]=1` guard covers only the zero case,
  not a negative span.
- **why-wrong (reference §3.1):** equirectangular mapping must unwrap azimuth across the seam
  so the mapping stays monotonic within the FoV.
- **REFUTER VERDICT — SURVIVED (math, conditional):** arithmetically a `left=170,right=-170`
  FoV yields `span=-340`, so `norm` runs backwards and produces out-of-`[0,1]` / reversed pixel
  columns; no seam handling exists. Conditional on seam-crossing FoVs actually occurring in the
  data, hence LOW-MEDIUM rather than HIGH.
- **severity:** LOW-MEDIUM · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** build a FoV crossing the ±180° seam; assert the pixel-column
  mapping is monotonic and within `[0, W-1]` across the seam.

---

## M-09 — `convert_to_image` all-NaN + `normalize=True` → empty-reduction ValueError · LOW-MEDIUM

- **file:line:** `util.py:385` (`lo = x[finite].min()`), condition `:384`
- **defect:** for an all-NaN 2D input, `replace_nan` cannot compute a fill (nanmin/nanmax are
  NaN), so `finite = np.isfinite(x)` is empty. The condition at `:384` uses `.min(initial=…)`
  and is safe, but when `normalize=True` the body at `:385-386` re-reduces the empty selection
  without an `initial` → crash.
- **why-wrong (reference §3.5):** an all-invalid raster should degrade to a constant/zero image
  (as the `hi>lo` else-branch at `:390` already does), not raise.
- **numeric repro / REFUTER VERDICT — SURVIVED:** `PROBE-M3e` — all-NaN 4×4, `normalize=True`:
  finite count 0 → `ValueError: zero-size array to reduction operation minimum which has no
  identity`.
- **severity:** LOW-MEDIUM (conditional on all-NaN input) · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** `convert_to_image(full((4,4),nan), normalize=True)` → assert
  it returns a valid uint8 image (constant), not a raise.

---

## M-04 — Perspective `project_raw` dead override + undocumented `@ pcd` matmul contract · LOW

- **file:line:** `strategies/projection.py:195` (`project_raw` → `raise NotImplementedError`),
  `:216-217` (`@ pcd` then `.arr`)
- **defect:** `project_raw` is an unreachable dead override (base `project` is overridden), and
  the projection relies on an undocumented pchandler `_TransformArray.__matmul__(pcd) → .arr`
  contract that will throw before any math if pchandler changes it.
- **REFUTER VERDICT — SURVIVED (LOW, source-grounded):** structural, no numeric probe needed;
  low blast radius (WIP path).
- **severity:** LOW · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** assert `PerspectiveProjection.project` works against the
  documented pchandler transform type, and either remove `project_raw` or make it a clear
  `NotImplementedError` with rationale.

---

## M-12 — `NormalizedFeature` percentile validation commented out · LOW

- **file:line:** `features/derivative_features.py:68` (`# if not(0 <= float(low) < float(high) <= 100):`)
- **defect:** the low/high percentile bounds check is commented out, so the feature silently
  accepts `low > high` or out-of-`[0,100]` values (unlike `ClipPercentileFeature:253-256`,
  which validates). Compounded by in-place `np.divide(..., out=img)` / `np.clip(..., out=img)`
  (`:80-81`) — cross-references design anchor #3 (in-place raster mutation, DSN-03).
- **numeric repro / REFUTER VERDICT — SURVIVED:** `PROBE-M4b` confirms the in-place `out=img`
  mutates the fetched array (safe today only because `DiskBackedImageData.__array__` returns a
  copy). The missing validation is dead-code-by-inspection.
- **severity:** LOW (math-adjacent) · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** assert `normalized_range_90_10` (low>high) raises
  `ValueError`, mirroring `ClipPercentileFeature`; assert `compute` does not mutate its input.

---

## M-13 — RRIM openness ray offsets under-sample near-axis directions · LOW

- **file:line:** `features/rrim.py:196-204` (`dx=int(rint(cos·step))`, `dy=int(rint(sin·step))`, dedup via `seen`)
- **defect:** rounding each ray step to integer pixels then de-duplicating `(dy,dx)` can drop
  samples along near-horizontal/vertical rays; direction sampling also ignores `pixel_size`
  anisotropy (only the distance term uses it, `:202`).
- **REFUTER VERDICT — SURVIVED (LOW, source-grounded):** the openness mean/`90−max` math itself
  is correct (see NON-FINDINGS); this is a sampling-fidelity concern, minor.
- **severity:** LOW · **pillar:** math · **disposition:** LOG
- **proving-test sketch (Phase 5):** assert each direction yields a monotonic, deduped ray whose
  sampled count is stable across `max_distance`, and that anisotropic `pixel_size` is reflected
  in the direction geometry (not only the distance).

---

## Dropped / downgraded candidates (refuter turned into passing counter-probes)

- **C-M3-d — `nanconv` integer-dtype breakage → DROPPED.** Claim: int input breaks `np.isnan`.
  `PROBE-M3c`: `np.isnan(np.array([[1,2],[3,4]], int))` returns an all-`False` array (no raise)
  under numpy 2.0.2. The downstream float16 divide still produces a float result. No reproducible
  numeric bug on the int path → **not logged** (Pitfall-1/honest-refutation).

## Confirmed-CORRECT items — explicitly NOT logged (recorded so 04-07 does not re-open)

- **Barycentric weights** (`interpolation.py:262-265`) — reproduce a linear field exactly
  (`PROBE-M2a`, err 7.1e-15).
- **Hillshade illumination magnitude formula** (`derivative_features.py:141-143`) — algebraically
  equivalent to ESRI (only the aspect handedness, M-11, is suspect).
- **RRIM differential-openness `structure = 0.5·(positive − negative)`** (`rrim.py:376,498`) —
  matches Yokoyama (2002).
- **RRIM positive/negative openness and slope primitives** (`rrim.py:219-220,265-291`) — match
  the reference formulas.

---

## Summary table (most-severe first)

| id | file:line | severity | one-line | verdict |
|----|-----------|----------|----------|---------|
| M-01 | projection.py:189/:79 | HIGH | orthographic 2-tuple arity + mixed row/col index (BUG-01) | SURVIVED |
| M-06 | interpolation.py:221/:225/:233-236 | HIGH | Delaunay culling → interior NaN holes | SURVIVED |
| M-02 | projection.py:217 | MED-HIGH | perspective no Z_c≤0 behind-camera guard | SURVIVED (escalate) |
| M-07 | util.py:197 | MED | nanconv mutates caller input in place | SURVIVED |
| M-08 | util.py:200-203 | MED | nanconv float16 divide overflows to inf | SURVIVED |
| M-10 | derivative_features.py:29 | MED | GradientFeature magic-100 spacing | SURVIVED |
| M-11 | derivative_features.py:135/:137 | MED | hillshade aspect handedness ~90° off | SURVIVED (suspect/escalate) |
| M-03 | projection.py:216 | MED | perspective omits translation t | SURVIVED |
| M-05 | projection.py:120-121/:82-85 | LOW-MED | spherical azimuth seam / inverted span | SURVIVED |
| M-09 | util.py:385 | LOW-MED | convert_to_image all-NaN + normalize → ValueError | SURVIVED |
| M-04 | projection.py:195/:216-217 | LOW | perspective dead project_raw + @pcd contract | SURVIVED |
| M-12 | derivative_features.py:68/:80-81 | LOW | NormalizedFeature validation commented out | SURVIVED |
| M-13 | rrim.py:196-204 | LOW | RRIM ray offsets under-sample near-axis | SURVIVED |
| — | interpolation.py:262-265 | — | barycentric weights | DROPPED (correct) |
| — | util.py:194,196-197 | — | nanconv int-dtype | DROPPED (no repro) |
| — | derivative_features.py:141-143 | — | hillshade illumination magnitude | CORRECT |
| — | rrim.py:376 etc. | — | RRIM structure/openness/slope | CORRECT |
