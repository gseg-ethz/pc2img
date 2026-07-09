---
phase: 02-dependency-adaptation-reproducible-environment
reviewed: 2026-07-09T14:28:31Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - scripts/smoke_pipeline.py
  - docs/pchandler-2x-break-audit.md
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-07-09T14:28:31Z
**Depth:** deep
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed the SC1 smoke driver (`scripts/smoke_pipeline.py`) and the DEP-01/DEP-02
attestation (`docs/pchandler-2x-break-audit.md`) at deep depth, tracing the smoke
through the full public pipeline (`core.py` → `strategies/projection.py` →
`strategies/interpolation.py` → `features/manager.py` → `image_cache/…`) and into
the GSEGUtils cache internals it claims to exercise.

**The audit doc's central negative attestation is sound** — I reproduced its grep
(`FoVTree|to_py4dgeo|\bCsv\b|\bLas\b|load_csv|load_las` → exit 1, no matches),
confirmed `FoVTree` lives only in `scripts/v2.0/03_tiled_image_gen.py`, and
confirmed `load_ply`/`load_e57` appear only under `scripts/`, never in `src/`. So
the "not broken because not called" verdict for BC-PCH-006/007/008/012 holds.

**However, the SC2 runtime-proof claim is empirically false.** Both cache configs
in the smoke leave `enable_caching=False` (the default; setting `cache_path` alone
does not flip it), and `LazyDiskCache.offload()` / `DiskBackedStore.offload()`
no-op when caching is disabled. I traced this in the GSEGUtils source and confirmed
it with a full run under `strace`: **zero** `.npy` / `.meta.json` / `.pkl` / `.dat`
files are opened for writing. The smoke exercises the in-memory DiskBackedStore
container abstraction but never the on-disk `.npy`+`.meta.json` codec — which is
exactly the surface BC-GSEG-001 changed. The doc presents that codec as
runtime-proven; it is not. That is the blocker.

The smoke also has several sensitivity gaps that let it pass when it shouldn't:
bare `assert`-based validation (stripped under `python -O`), a square resolution
that hides axis transposition, and loose value/finite thresholds.

## Critical Issues

### CR-01: SC2 "disk-cache path is runtime-exercised" is empirically false — no on-disk cache is ever written

**File:** `docs/pchandler-2x-break-audit.md:62-67,71-77` (and the mirroring claim in `scripts/smoke_pipeline.py:54-59`)

**Issue:**
The audit doc is the DEP-02/SC2 evidence and states, as fact, that the smoke
runtime-proves the GSEGUtils disk cache:

- L62-67: *"BC-GSEG-001 (on-disk format moved from pickle to `.npy` + `.meta.json`…)
  does not affect pc2img: the library creates fresh `DiskBackedStore` caches at
  runtime … which materialize in the new format … The DiskBackedStore/LazyDiskCache
  surface is runtime-exercised by the Delaunay step in the SC1 smoke."*
- L76-77: *"Delaunay exercises the GSEGUtils `DiskBackedStore` cache path (SC2)."*
- Script L58-59: *"Both still exercise the GSEGUtils disk-cache path (SC2)…"*

This is not what actually happens. Trace of the configs:

- Generator raster store: smoke passes `LazyDiskCacheConfig(cache_path=Path(td))`.
  `enable_caching` **defaults to `False`** (verified:
  `LazyDiskCacheConfig() → enable_caching=False, automatic_offloading=False`).
  Setting `cache_path` does not enable caching. In
  `DiskBackedImageStore.add_image_to_store` the raster is wrapped with
  `enable_caching=False`, and `DiskBackedImageStore.offload` explicitly skips
  disabled entries (`disk_backed_image_store.py:163-165`).
- Delaunay triangulation store: `DelaunayInterpolation()` is constructed with **no
  config**, so it uses its own default (`enable_caching=False`, `cache_path=None`;
  `interpolation.py:112`). Its `offload(pickle_container=True)` call
  (`interpolation.py:196`) no-ops because
  `LazyDiskCache.offload()` / `DiskBackedStore.offload()` bail on
  `if not self._enable_caching`.

Empirical confirmation — a full run under
`strace -f -e trace=openat … uv run python scripts/smoke_pipeline.py`:

```
count of O_CREAT/O_WRONLY opens matching .npy/.meta.json/.pkl/.dat = 0
leftover .npy/.meta.json/.pkl/.dat files = (none)
```

So the exact on-disk codec that BC-GSEG-001 changed is **never executed**. The
smoke would not catch a regression in the `.npy`+`.meta.json` reader/writer, and
the attestation that "fresh caches materialize in the new format" is unproven by
the evidence it cites. A reviewer signing off DEP-02/SC2 on this doc would believe
the GSEGUtils disk format was runtime-verified when it was not.

**Fix:**
Make the claim true by actually enabling caching in the smoke so the codec runs,
then keep the doc language as-is:

```python
raster_cfg = LazyDiskCacheConfig(cache_path=Path(td), enable_caching=True)
delaunay_cfg = LazyDiskCacheConfig(
    cache_path=Path(td) / "delaunay", enable_caching=True
)
gen = PointCloudImageGenerator(
    pcd, (200, 160),
    SphericalProjection(field_of_view=pcd.fov),
    DelaunayInterpolation(delaunay_cfg),   # was DelaunayInterpolation()
    lazy_disk_cache_config=raster_cfg,
)
...
# after generate(), assert the codec actually materialized on disk:
npy_written = list(Path(td).rglob("*.npy"))
assert npy_written, "SC2: expected DiskBackedStore to write .npy cache artifacts"
```

Alternatively, if enabling caching is out of scope for Phase 2, **downgrade the
doc and the script comment** to state precisely what is exercised: the in-memory
`DiskBackedStore` / `DiskBackedNDArray` container API — *not* the on-disk
`.npy`+`.meta.json` codec — and remove the "materialize in the new format" claim.

## Warnings

### WR-01: Load-bearing validation uses bare `assert` — silently disabled under `python -O`

**File:** `scripts/smoke_pipeline.py:73-75`

**Issue:**
The entire pass/fail signal of this durable smoke is three `assert` statements. The
module docstring promises *"Exit 0 (and a printed `OK` line) means the pipeline
works."* Under `python -O` / `-OO` (or `PYTHONOPTIMIZE=1`), all `assert`s are
stripped, so the script skips every check, prints `OK`, and exits 0 even on a
completely broken pipeline. For a script explicitly slated for promotion to CI
(D-09), running it under an optimized interpreter turns it into a no-op that always
"passes." The documented invocation (`uv run python`) is unoptimized today, but
nothing enforces that.

**Fix:** Replace load-bearing asserts with explicit raises that survive `-O`:

```python
if img.shape != (200, 160):
    raise SystemExit(f"FAIL: unexpected shape {img.shape}")
if finite_fraction <= 0.85:
    raise SystemExit(f"FAIL: too few finite pixels: {finite_fraction:.3f}")
if not (8.0 < float(np.nanmin(img)) and float(np.nanmax(img)) < 12.0):
    raise SystemExit(f"FAIL: range out of expected band: "
                     f"[{np.nanmin(img):.3f}, {np.nanmax(img):.3f}]")
```

### WR-02: Square resolution (200, 200) makes the shape assertion blind to axis transposition

**File:** `scripts/smoke_pipeline.py:63,73`

**Issue:**
Resolution is `(200, 200)` and the check is `img.shape == (200, 200)`. In
`core.generate`, `grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))` yields
shape `(h, w)`, and the raster shape is `grid_x.shape`. Because `w == h`, a
regression that swaps width/height (or transposes the projection→grid→raster
mapping) still produces a `(200, 200)` array and passes. Axis-orientation is one of
the most likely things to break when adapting the projection to a new pchandler
FoV API, and this smoke cannot detect it.

**Fix:** Use a non-square resolution so orientation is encoded in the shape, and
assert the exact expected `(height, width)`:

```python
gen = PointCloudImageGenerator(pcd, (200, 160), ...)   # (width, height)
...
assert img.shape == (160, 200), f"unexpected shape {img.shape}"  # (h, w)
```

### WR-03: Value sanity check (`nanmin > 0`) is too weak to catch a wrong-quantity raster

**File:** `scripts/smoke_pipeline.py:75`

**Issue:**
The only value assertion is `np.nanmin(img) > 0`. The synthetic range is ~[8.7,
11.3] (observed `min=8.748 max=11.262`). Any positively-valued raster satisfies
`> 0` — e.g. a raster of interpolated **pixel coordinates**, a different scalar
field, or a constant fill would all pass. A pipeline that "runs but returns the
wrong quantity" (a realistic dependency-adaptation failure mode) is not caught.

**Fix:** Bound the magnitude to the known synthetic band:

```python
assert 8.0 < float(np.nanmin(img)), f"range floor too low: {np.nanmin(img)}"
assert float(np.nanmax(img)) < 12.0, f"range ceiling too high: {np.nanmax(img)}"
```

### WR-04: `finite_fraction > 0.5` threshold is far below the realistic floor

**File:** `scripts/smoke_pipeline.py:74`

**Issue:**
Observed finite fraction is 0.959. The threshold `> 0.5` leaves a ~2x margin: a
regression that NaNs out ~45% of the raster (e.g. half the points dropped by a
broken FoV mask, or a triangulation-quality filter regression) would still pass.
For a smoke whose job is to catch pipeline breaks, the threshold should sit just
below the expected value, not at half of it.

**Fix:** Tighten to a realistic floor with headroom, e.g. `finite_fraction > 0.85`.

## Info

### IN-01: Dead module logger; pipeline debug logs are never surfaced

**File:** `scripts/smoke_pipeline.py:17,30`

**Issue:**
`logger = logging.getLogger(__name__.split(".")[0])` is assigned but never used
(when run as `__main__`, the name resolves to `"__main__"` anyway). Logging is
never configured (`no logging.basicConfig`), so the `logger.debug(...)` diagnostics
emitted by the interpolation/projection layers — the ones that would explain a
degraded run in CI — are suppressed. The `import logging` exists solely for this
dead variable.

**Fix:** Either delete the unused `logger` and `import logging`, or wire it up so
the smoke's stated goal of carrying diagnostics into CI logs is met:

```python
logging.basicConfig(level=logging.INFO)
logging.getLogger("pc2img").setLevel(logging.DEBUG)
```

### IN-02: Audit doc undercounts `.load(` sites in `src/` (verdict still holds)

**File:** `docs/pchandler-2x-break-audit.md:37`

**Issue:**
The doc states *"the only `.load(` in `src/pc2img/` is pc2img's own image-store
pickle offload."* There are actually four sites:
`image_cache/disk_backed_image_data.py:36` (`self.load()`) plus three in
`image_cache/disk_backed_image_store.py:53,103,199`. All are pc2img's own cache
machinery (none is a pchandler `Csv`/`Las` loader), so the conclusion is correct,
but the enumeration is imprecise for a doc that markets itself as reproducible
evidence.

**Fix:** Reword to "the only `.load(` calls in `src/pc2img/` are pc2img's own
image-cache pickle offload/reload sites," or cite the grep count directly.

---

## Structural Findings (fallow)

No structural pre-pass (`<structural_findings>`) was provided with this review.

## Narrative Findings (AI reviewer)

All findings above (CR-01, WR-01…WR-04, IN-01…IN-02) are narrative findings from
direct, cross-file code review at deep depth, corroborated where possible with
reproduced greps and an `strace` run of the smoke.

---

_Reviewed: 2026-07-09T14:28:31Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
