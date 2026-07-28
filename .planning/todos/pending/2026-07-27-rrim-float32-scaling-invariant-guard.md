---
created: 2026-07-27T15:10:00Z
title: RRIM z_factor scaling — fail fast when a scaled raster leaves float32 range, instead of returning a silent all-NaN image
area: features
severity: minor
resolves_phase: 6
files:
  - src/pc2img/features/rrim.py
  - tests/test_rrim_features.py
  - .planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md
source: Phase 5 round-2 gap-diff review (05-REVIEW.md CR-01, downgraded BLOCKER -> WARNING 2026-07-27)
---

## Problem

`compute_slope` (`rrim.py:236`) and `compute_openness` (`rrim.py:252`) multiply the raster
by `z_factor` and immediately store the result as `float32`. When the result leaves float32
range the value becomes `inf`, `np.gradient` turns `inf - inf` into `NaN`, and the generator
returns and **caches a fully-NaN raster with no error**.

Confirmed by running code (16x16 synthetic cloud, values ~1):

```
z=1.0    → 256/256 finite     z=1e150 → 0/256 ALL-NaN
z=1e6    → 256/256 finite     z=1e300 → 0/256 ALL-NaN
z=1e30   → 256/256 finite     z=1e400 → 0/256 ALL-NaN  (float("1e400") is inf)
```

numpy names the mechanism directly: `RuntimeWarning: overflow encountered in cast` at
`rrim.py:236`. There are **two distinct modes**, and the second is the more interesting:

| case | mode | today |
|---|---|---|
| raster~1, z=1e36 | — | fine |
| raster~1e3, z=1e36 | **product** exceeds float32 max | `inf` (data-dependent) |
| raster~1, z=1e39 | **scalar** cast to float32 first | `inf` (data-independent) |
| raster~1e-30, z=1e39 | scalar cast | `inf` — **true answer is 1e9** |

The last row is a genuine correctness defect rather than garbage-for-garbage: under NEP 50
a weak Python scalar is cast to the array dtype *before* the multiply, so a perfectly
representable product is destroyed. Reaching it still requires an absurd `z`, which is why
this is filed minor.

**This is not a Phase 5 regression.** The pre-05-14 regex `^z([+-]?\d+(?:\.\d+)?)$` has an
unbounded `\d+`, so the same magnitude spelled long-form (`z` + 40 digits) was always legal
and produces the identical all-NaN. 05-14's exponent widening made it 6 characters instead
of 41.

**Rejected fix:** `math.isfinite` in `_validate_config` (the reviewer's proposal). It closes
only `z >= 1.8e308` and leaves the whole ~3.4e38–1e308 band silently all-NaN. Finiteness is
the wrong boundary; float32 representability is the right one.

## Scope — audited, NOT systemic

Owner asked whether other features share the class. Audited empirically 2026-07-27:

| path | scales raster → stores float32? | reachable failure | how it fails |
|---|---|---|---|
| **RRIM `z_factor`** (`:236`, `:252`) | **yes, unbounded** | `z ≳ 3.4e38 / max\|raster\|` | **silent all-NaN** |
| RRIM `red_strength` (`:329`) | scaled then `np.clip(…, 0, 1)` | only literal `inf` | clip absorbs it |
| gradient `pixel_size` (divisor) | no — float64 headroom | **none found** | finite at `px=1e-201`, peak 5.45e200 |
| hillshade `z_factor` | no — bounded by `arctan`/`cos` | only literal `inf` | all-NaN at `inf` only |
| multigrad `sigmas` | n/a | `>=1e30` | **already loud** (scipy raises) |

So the work is **2 call sites**, not an open-ended sweep. `red_strength` is deliberately
**out of scope** — the downstream `np.clip(…, 0, 1)` already bounds it; that skip is a
decision, not an oversight.

Observation, not a finding: `hillshade_range_315_45_<1e40>` returns a plausible-looking
raster with peak 0.707 from a nonsense `z`. Silent-wrong-output, in the category the owner
has previously dispositioned as intentional design.

## Solution

Owner decision 2026-07-27: **fail fast (`ValueError`)**, matching the repo's
invalid-domain-value convention. Validate the *output invariant* in one helper rather than
capping each input — that is what makes it compose to any multiplier added later, and it
avoids inventing a magic ceiling (the real one is data-dependent: `float32_max / max|raster|`).

Prototyped and run 2026-07-27; behaviour table below is measured, not predicted.

```python
_F32_MAX = float(np.finfo(np.float32).max)   # 3.4028235e+38

def _scale_to_float32(raster, multiplier, *, param):
    """Multiply a raster by a scalar, upholding the float32-representability invariant.

    Catches both overflow modes: the PRODUCT leaving float32 range (data-dependent), and
    the MULTIPLIER leaving it, which under NEP 50 casts the weak Python scalar to the
    array dtype BEFORE multiplying -- so 1e-30 * 1e39 returns inf even though the true
    product (1e9) is trivially representable.

    The check is one scalar comparison in float64, so the common path costs nothing beyond
    the finite mask the callers already compute.
    """
    arr = np.asarray(raster, dtype=np.float32)
    mult = float(multiplier)
    finite = np.isfinite(arr)
    max_abs = float(np.abs(arr[finite]).max()) if finite.any() else 0.0

    if max_abs * abs(mult) > _F32_MAX:
        safe = _F32_MAX / max_abs if max_abs else float("inf")
        raise ValueError(
            f"{param}={mult!r} scales this raster's peak |value| ({max_abs:.3g}) to "
            f"{max_abs * abs(mult):.3g}, outside the float32 range (max {_F32_MAX:.3g}) "
            f"that RRIM rasters are stored in; the output would be silently all-NaN. "
            f"Use {param} <= {safe:.3g} for this data."
        )

    if abs(mult) > _F32_MAX:      # product fits but the scalar does not -- widen, then descend
        return (arr.astype(np.float64) * mult).astype(np.float32, copy=False)

    return (arr * mult).astype(np.float32, copy=False)
```

Measured against the prototype:

```
raster=1     z=2       today: 2      guard: 2
raster=1     z=1e36    today: 1e+36  guard: 1e+36
raster=1e3   z=1e36    today: inf    guard: ValueError
raster=1     z=1e39    today: inf    guard: ValueError
raster=1e-30 z=1e39    today: inf    guard: 1e+09        <- wrong answer becomes right
raster with NaN/inf, z=2 → [2. nan inf 4.]               <- NaN inputs do not trip it
```

**Cost:** the common path adds one scalar comparison. `compute_slope` already computes
`finite = np.isfinite(raster)` on line 235, so the mask is free there; `compute_openness`
gains one `isfinite`/`abs`/`max` pass. The float64 widening runs only in the rare
scalar-overflow case.

**BC:** inputs that today yield a silent all-NaN raster will raise. Record in
`05-BC-NOTES.md` under the same request-time-validation shift as entry G11.

## Why deferred rather than fixed in Phase 5

Not risk — the audit above bounds the work to 2 sites. Scheduling: Phase 5 was reopened
twice by exactly the move of landing extra numerical code late (05-13 fixed 8 findings and
introduced 2 blockers), and nothing in this class is reachable with any honest input
(`z` in 0.1–10 against metre-scale rasters never approaches 3.4e38). Deferring is cheap
here precisely because the design is already decided.

## Breadcrumbs

- Finding + full correction block: `.planning/phases/05-bug-fixes-module-test-coverage/05-REVIEW.md` § CR-01
- Mechanism: `RuntimeWarning: overflow encountered in cast`, `src/pc2img/features/rrim.py:236`
- Call sites to change: `rrim.py:236` (`compute_slope`), `rrim.py:252` (`compute_openness`)
- Related deferred item: successful delete leaves an inert `<key>.dat`
  (`.planning/phases/05-bug-fixes-module-test-coverage/deferred-items.md` § From 05-14).
  The non-finite `z_factor` item recorded there is **superseded** by this todo — finiteness
  turned out to be the wrong boundary.
