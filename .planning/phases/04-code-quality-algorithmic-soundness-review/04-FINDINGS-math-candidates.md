# Phase 04 — Math-track FIND candidates (QUAL-03, plan 04-06)

> Raw FIND-pass output, **pre-refutation**, grouped by module set M1–M5. This file is
> retained on disk as the D-05 adversarial-pass evidence and stays distinct from the
> refuted `04-FINDINGS-math.md`. Every `file:line` was re-grepped against the live
> post-04-04 tree (Pitfall 1). Runtime the reviewers reason about: numpy 2.0.2,
> scipy 1.18.0 (verified this session).

Reference basis: 04-RESEARCH.md §Pillar 3 (3.1 spherical, 3.2 orthographic/BUG-01,
3.3 perspective/D-08, 3.4 Delaunay culling, 3.5 nanconv/convert_to_image/replace_nan,
3.6 derivative features + rrim). Confirmed-correct items from §3.6 (hillshade
illumination magnitude, RRIM differential-openness) are recorded as NON-candidates so
reviewers do not mis-log them.

BUG-01 is cross-referenced SOURCE-ONLY at `strategies/projection.py`; there is **no**
pytest xfail encoding it (the live xfails only cover the null lazy-cache-config case at
`tests/test_point_cloud_image_generator.py:35` and DiskBackedImageData lifecycle cases at
`tests/test_disk_backed_image_data.py:50`). Repros are derived from the reference
formulas, not from tests.

---

## M1 — projection geometry (`strategies/projection.py`)

### C-M1-a — Orthographic `project_raw` returns a 2-tuple; `project` unpacks 4 (BUG-01, arity)
- **file:line:** `strategies/projection.py:189` (return) vs `:79` (`coords_raw, mask, mins, maxs = self.project_raw(pcd)`)
- **defect:** `OrthographicProjection.project_raw` returns `(coords, mask)`; the base
  `project()` unpacks four values → `ValueError: not enough values to unpack (expected 4, got 2)`.
- **why-wrong:** §3.2 — the contract is `(coords_raw, mask, mins, maxs)`; the in-source
  `# Todo: Update to pass min and max back!` at `:188` acknowledges it. Extent normalization
  in `project()` (`span = maxs - mins`, `:82`) cannot run.
- **repro:** call any `orthographic` generate → unpack error before any raster is produced.
- **severity:** HIGH · **pillar:** math

### C-M1-b — Orthographic mixed boolean-row + fancy-column indexing
- **file:line:** `strategies/projection.py:189` (`pcd.xyz[mask, self._xyz_column_selection]`)
- **defect:** `xyz[mask, [c0, c1]]` broadcasts a length-M boolean-derived row index against a
  length-2 column list → `IndexError` unless M==2, and when M==2 it silently returns the
  **diagonal** `[xyz[i0,c0], xyz[i1,c1]]`, not the intended `(M,2)` block.
- **why-wrong:** §3.2 — must index rows then columns: `pcd.xyz[mask][:, cols]`.
- **repro:** `xyz[mask,[0,1]]` with 3 kept rows → IndexError; with 2 kept rows → wrong diag.
- **severity:** HIGH (same line as C-M1-a) · **pillar:** math

### C-M1-c — Perspective projection: no behind-camera (Z_c ≤ 0) guard
- **file:line:** `strategies/projection.py:217` (`uv = uv.arr[:,:2] / uv.arr[:,2].reshape(-1,1)`)
- **defect:** points with camera-space depth `Z_c < 0` (behind the camera) still pass the
  perspective divide; a sign flip can land them in-bounds (`:218-221`) as phantom points.
- **why-wrong:** §3.3, pinhole model — must cull `Z_c ≤ 0`; add `mask &= uv.arr[:,2] > 0`.
- **repro:** reference-grounded (needs a real PointCloudData to run); classic pinhole bug.
- **severity:** MEDIUM-HIGH (D-08 same bar; escalation candidate) · **pillar:** math

### C-M1-d — Perspective extrinsics: no translation `t` (origin-only camera)
- **file:line:** `strategies/projection.py:216` (`(self.projection_matrix @ self.rotation_matrix) @ pcd`)
- **defect:** composes intrinsics/projection with a rotation only; there is no camera-center
  translation `t`. Model is correct only for a camera at the world origin.
- **why-wrong:** §3.3 — pinhole is `K·[R|t]·X`; missing `t`.
- **severity:** MEDIUM · **pillar:** math

### C-M1-e — Perspective `@ pcd` relies on undocumented `_TransformArray.__matmul__`
- **file:line:** `strategies/projection.py:216-217`
- **defect:** matmul against a `PointCloudData`, then `.arr` — depends on an undocumented
  pchandler 2.x contract; if absent the method throws before any math. Also `project_raw`
  raises `NotImplementedError` (`:195`) but is never called (dead override → hygiene note).
- **severity:** LOW-MEDIUM · **pillar:** math

### C-M1-f — Spherical azimuth wrap / inverted-span normalization
- **file:line:** `strategies/projection.py:120-121` (`mins=(left,top)`, `maxs=(right,bottom)`) → `:82-85`
- **defect:** linear `(h-left)/(right-left)` mis-maps if the FoV straddles the ±180°/0–360°
  seam (`left=170, right=-170` → span `-340`) or if `top>bottom` in the elevation metric →
  negative span. `span[span==0]=1` (`:84`) only guards the zero case, not negative.
- **why-wrong:** §3.1 — equirectangular mapping needs seam-aware unwrapping.
- **severity:** LOW-MEDIUM (conditional on seam-crossing FoV) · **pillar:** math

---

## M2 — interpolation / Delaunay culling (`strategies/interpolation.py`, `triangulation.py`, `utils.py`)

### C-M2-a — Magic culling thresholds punch interior NaN holes (over-culling)
- **file:line:** `strategies/interpolation.py:221` (`area_thresh = np.median(area)*10`),
  `:225` (MAD `aspect_ratio_thresh`), applied `:228-236` (`mask &= tri_is_good[simplices]`)
- **defect:** triangles exceeding the median-scaled area or MAD-scaled aspect thresholds are
  dropped; on sparse/anisotropic tiles this culls **valid interior** triangles, turning
  interior query pixels into NaN "holes" (not hull behavior — Pitfall 3).
- **why-wrong:** §3.4 — scipy semantics put NaN only *outside* the hull (`find_simplex==-1`).
  The heuristic silently corrupts interior output.
- **repro:** anisotropic sampling → assert interior triangles culled.
- **severity:** HIGH · **pillar:** math

### C-M2-b (NON-candidate) — Barycentric weights are CORRECT
- **file:line:** `strategies/interpolation.py:262-265` (`bary[:,-1] = 1 - bary_partial.sum(axis=1)`)
- **note:** weights sum to 1 and reproduce a linear field exactly; confirmed by probe. **Do
  not log.** Recorded so reviewers do not mis-flag it.

---

## M3 — smoothing / util math (`util.py`)

### C-M3-a — `nanconv` mutates the caller's input array in place
- **file:line:** `util.py:197` (`a[n] = 0`)
- **defect:** zeroes the caller's NaNs in place → silent data corruption of the input.
- **why-wrong:** §3.5 — normalized convolution must operate on a filled copy.
- **repro:** pass an array with NaNs → array changed after call.
- **severity:** MEDIUM · **pillar:** math

### C-M3-b — `nanconv` float16 division loses precision / overflows to inf
- **file:line:** `util.py:200-203` (cast conv sums to `np.float16`, divide in float16)
- **defect:** float16 max ≈ 65504; realistic range/elevation magnitudes with a moderate
  kernel overflow the convolution sum to `inf` → the smoothed output is `inf`/`nan`.
- **why-wrong:** §3.5 — do the divide in float32 (like `_smooth_with_nan`).
- **repro:** value 12000, 7×7 ones-kernel → conv sum ≈ 588000 → inf.
- **severity:** MEDIUM · **pillar:** math

### C-M3-c — `convert_to_image` all-NaN + `normalize=True` → empty reduction ValueError
- **file:line:** `util.py:385` (`lo = x[finite].min()`), guarded condition at `:384`
- **defect:** for an all-NaN 2D input, `replace_nan` cannot fill (stats are NaN), so `finite`
  is empty; the guarded branch at `:384` uses `.min(initial=…)`, but `:385-386` re-reduce
  the empty array without an initial → `ValueError: zero-size array to reduction …`.
- **repro:** all-NaN 2×2, `normalize=True`.
- **severity:** LOW-MEDIUM (conditional) · **pillar:** math

### C-M3-d (to-refute) — `nanconv` integer-dtype degradation
- **file:line:** `util.py:194` (`on = np.ones(a.shape, dtype=a.dtype)`), `:196-197`
- **claim:** int input breaks `np.isnan`/the mask math. **Handed to refuter** — numpy 2.0.2
  behavior must be checked before logging.

---

## M4 — derivative features (`features/derivative_features.py`)

### C-M4-a — `GradientFeature` hardcoded spacing 100 mis-scales the gradient
- **file:line:** `features/derivative_features.py:29` (`np.gradient(img, 100, axis=ax)`)
- **defect:** unless pixel spacing is genuinely 100 units, every gradient is divided by 100.
  Contrast `MultiScaleGradientFeature`/rrim which use unit/`pixel_size` spacing.
- **repro:** ramp rising 1/px → reported slope 0.01.
- **severity:** MEDIUM · **pillar:** math

### C-M4-b — `HillshadeFeature` aspect axis handedness (suspect)
- **file:line:** `features/derivative_features.py:135` (`x, y = np.gradient(values*z_factor)`),
  `:137` (`aspect = np.arctan2(-x, y)`)
- **defect:** with `x=∂/∂row`, `y=∂/∂col`, the aspect/illumination appears rotated ~90° vs
  the standard ESRI north-up convention. The **illumination magnitude formula (`:141-143`)
  is confirmed correct** (§3.6 algebraic check); only the aspect axis assignment is suspect.
- **repro:** east/south-rising ramps → argmax-azimuth offset by 90°.
- **severity:** MEDIUM (escalation/suspect — depends on the raster's intended orientation) · **pillar:** math

### C-M4-c — `NormalizedFeature` percentile validation commented out
- **file:line:** `features/derivative_features.py:68` (`# if not(0 <= float(low) < float(high) <= 100):`)
- **defect:** now silently accepts `low>high` and out-of-`[0,100]` percentiles. Plus in-place
  `np.divide(..., out=img)` / `np.clip(..., out=img)` (`:80-81`) — cross-ref design anchor #3.
- **severity:** LOW (math-adjacent hygiene) · **pillar:** math

### C-M4-d (NON-candidate) — Hillshade illumination magnitude formula CORRECT
- **note:** §3.6 — `sin(alt)sin(slope_var)+cos(alt)cos(slope_var)cos(az-aspect)` with
  `slope_var=π/2-arctan|∇|` is algebraically equivalent to ESRI. **Do not log the formula.**

---

## M5 — RRIM math (`features/rrim.py`) — IP posture NOT in scope

### C-M5-a — Openness ray offsets: integer `rint` dedup under-samples near-axis directions
- **file:line:** `features/rrim.py:196-204` (`dx=int(rint(cos·step))`, `dy=int(rint(sin·step))`, dedup)
- **defect:** rounding ray steps to integer pixels then de-duplicating can drop samples along
  near-horizontal/vertical rays and ignores `pixel_size` anisotropy in direction sampling.
- **severity:** LOW · **pillar:** math

### C-M5-b (NON-candidate) — Differential-openness structure CORRECT
- **file:line:** `features/rrim.py:376,498` (`structure = 0.5*(positive - negative)`)
- **note:** matches Yokoyama (2002) differential openness = (O⁺−O⁻)/2. **Do not log.**

### C-M5-c (NON-candidate) — Openness/slope primitives sound
- **note:** §3.6 — `positive = 90 − max_upward` per direction, mean across directions (`:265-291`);
  slope `|∇(z·z_factor)|` (`:219-220`). Match the references. **Do not log.**
