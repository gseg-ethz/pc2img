---
phase: 05-bug-fixes-module-test-coverage
reviewed: 2026-07-27T14:02:28Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - src/pc2img/features/rrim.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_image_store.py
  - tests/test_rrim_features.py
findings:
  critical: 0
  warning: 7
  info: 3
  total: 10
status: issues_found
amended: 2026-07-27T15:10:00Z
amendments:
  - "CR-01 downgraded BLOCKER -> WARNING after owner review: the defect predates 05-14
     (reachable pre-diff via the long-form spelling) and is therefore not a regression;
     the proposed math.isfinite fix was also shown insufficient. See the Correction
     block under CR-01."
---

# Phase 05: Code Review Report (round-2 gap closure, plan 05-14)

**Reviewed:** 2026-07-27T14:02:28Z
**Depth:** deep
**Files Reviewed:** 4
**Diff base:** `c8521f3` (170 insertions, 16 deletions)
**Status:** issues_found

## Summary

Both G9 (RRIM `z_factor` round trip) and G10 (`__delitem__` ordering) are genuinely fixed,
and both proving tests are genuine RED sensors — I verified that by monkeypatching the
pre-fix code back in and re-running:

- Reverting `_Z_FACTOR_RE` + `_format_number` to the 05-13 versions turns 6 rrim tests RED
  (`round_trips[1e-06]`, `[1e-05]`, `[1.2345678]`, `is_injective_for_nearby_z`,
  `dependency_chain_resolves_for_sub_1e4_z`, `generate_rrim_small_z_end_to_end`).
- Reverting `__delitem__` to the unlink-then-`super()` ordering turns
  `test_failed_delete_preserves_codec_pair_and_both_stores` RED with exactly the intended
  message ("failed delete destroyed the .npy").
- The characterization guard `test_z_factor_token_unchanged_for_currently_valid_values`
  passes under BOTH formatters, so it is a real characterization test and not a
  post-hoc-fitted assertion.

I also verified the plan's locked zero-cache-churn requirement rather than trusting it.
Exhaustive sweep of all ≤6-significant-digit decimals across `[1e-4, 1e6)` (9,000,000
values) plus 300k structured/random/bit-pattern floats: **zero** values exist where the old
token was valid-and-correctly-encoded and the new token differs. Byte-identity holds. A
separate 50k-value fuzz of `RRIMConfig → pack_feature_name → FEATURES.match → _parse_rrim_config`
(including subnormals, 2^-53, 2^53±1, 1.797e308, 17-significant-digit values) found zero
round-trip failures and zero double-matches in the registry.

On the store: I read the GSEGUtils source rather than the docstring's claim about it.
`DiskBackedStore.__delitem__` really is `del self._store[key]` and nothing else, `_cache_dir`
really can never be `None` (temp-dir fallback), so the removed guard was genuinely dead, and
nothing inside GSEGUtils evicts via `__delitem__` (so the override cannot be triggered as a
memory-pressure eviction and silently destroy a cache entry). The DSN-09 posture is intact:
no `pickle.load*` sink, no new deserialization surface.

What is **not** sound: the regex widening was treated as "purely additive", and it is not.
It admits decimal-exponent overflow (`z1e400`), which `float()` turns into `inf`,
`_validate_config` accepts (`inf > 0`), and the slope path then renders as a silently
all-NaN raster. That is CR-01 — **downgraded to a warning on 2026-07-27** after the
orchestrator reproduced the same all-NaN result on the *pre-diff* grammar via the
long-form spelling, establishing that 05-14 did not introduce the defect. The claim
below that the token "raised a clear `ValueError` before this diff" is **wrong**; see the
Correction block under CR-01. Seven warnings in total cover an
overclaimed cross-store safety guarantee (with a confirmed data-loss repro through the
*successful*-delete path the new test does not exercise), an unvalidated key → `unlink()`
path escape, a silent base-feature reinterpretation caused by the same widening, and three
test-strength gaps.

Every finding below was reproduced by running code unless marked PLAUSIBLE. Nothing is
marked PLAUSIBLE.

## Narrative Findings (AI reviewer)

## Critical Issues

*None. CR-01 was raised as a blocker and downgraded to a warning on owner review; it is
retained in place below, with its original text intact and a Correction block appended,
rather than rewritten — the reasoning that produced the wrong severity is itself the
useful record.*

### CR-01 (WARNING — downgraded 2026-07-27, originally filed BLOCKER): Widened `z` grammar admits decimal-exponent overflow → `inf` → silent all-NaN raster

**Status:** CONFIRMED as a defect; **REFUTED as a regression** (see Correction below).
**File:** `src/pc2img/features/rrim.py:45` (regex), `src/pc2img/features/rrim.py:122-123` (missing finiteness guard)

**Issue:**
The widened `_Z_FACTOR_RE` now accepts any exponent, including exponents that overflow
`float()` to `inf`. `_validate_config` only checks `z_factor <= 0`, so `inf` passes
validation. The consequence differs per feature, and one branch is silent:

Reproduction (`/scratch/31_pc2img/.venv/bin/python`):

```
old regex accepts z1e400 : False        <- pre-diff: rejected at the user's own token
new regex accepts z1e400 : True
match ok, deps: ['range']
parsed z_factor: inf  (validated OK -> no error)
slope raster all-NaN: True   finite count: 0
NO EXCEPTION RAISED -> silent all-NaN raster
pre-diff behaviour: ValueError -> Unknown RRIM option 'z1e400'. Supported tokens are rN, dN, sclipA-B, oclipA-B, zF and redF.
```

- `generate(["rrim_component_(slope,range,z1e400)"])` — `dependencies_for` returns
  `[base_feature]` for the slope component, so the pack name (and its `zinf` token) is never
  built. `compute_slope` does `raster * inf` → `inf` → `np.gradient` → NaN. The generator
  returns a **fully NaN raster with no error**, and caches it under a distinct key.
- `generate(["rrim_(range,z1e400)"])` / `rrim_pack_` — `pack_feature_name()` emits
  `repr(inf)` = `"inf"`, producing the machine-derived dependency
  `rrim_pack_(range,r16,d8,zinf)`, which then fails with
  `ValueError: Unknown RRIM option 'zinf'` — an error naming a token the user never wrote.
- Same for `z9e999`, `z1E400`, `z1e309`. (`z1e-400` → `0.0` → correctly rejected by the
  existing `z_factor > 0` check.)

Before this diff none of these tokens parsed at all, so the non-finite `z_factor` hazard was
reachable only through the Python API (`compute_rrim(z_factor=float("inf"))`), never through
the public feature-name grammar. This is the deferred "no finiteness check in
`_validate_config`" item, but the diff **materially worsened it on both axes the deferral
assumed fixed**: unreachable → reachable from the public name DSL, and loud rejection →
silent all-NaN output. The in-code comment at line 43-44 ("purely ADDITIVE — every token
accepted before is still accepted") is true about tokens but hid this consequence: the
widening also admits a value class the validator does not cover.

**Fix** — one line, and it also closes the deferred item outright:

```python
import math

def _validate_config(config: RRIMConfig) -> RRIMConfig:
    ...
    if not math.isfinite(config.z_factor) or config.z_factor <= 0:
        raise ValueError(f"z_factor must be a finite value > 0, got {config.z_factor}.")
```

Add a defensive assertion in `_format_number` so a non-finite value can never be emitted
into a cache key even if it arrives by another route:

```python
def _format_number(value: float) -> str:
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"cannot encode non-finite value {v!r} in a feature name.")
    if v.is_integer():
        return str(int(v))
    return repr(v)
```

Proving test to add:

```python
@pytest.mark.parametrize("token", ["z1e400", "z9e999", "z1E400"])
def test_overflowing_z_token_is_rejected_not_silently_infinite(token):
    with pytest.raises(ValueError, match="finite"):
        FEATURES.match(f"rrim_component_(slope,range,{token})")
```

#### Correction (2026-07-27, orchestrator + owner) — severity BLOCKER → WARNING

Three claims above were tested and two do not survive.

**1. "Before this diff none of these tokens parsed at all" — FALSE.** The pre-05-14 regex
was `^z([+-]?\d+(?:\.\d+)?)$`. Its `\d+` is unbounded, so the same magnitude spelled in
long form was always legal and produces the identical failure:

```
token: z1000…0 (41 chars, = 1e39)
OLD (pre-05-14) regex matches it: True
result: finite=0/256  all-NaN=True
```

05-14 made the magnitude expressible in 6 characters instead of 41. That is an ergonomics
change, not a new defect, so this is **not a regression** and does not gate Phase 5.

**2. The proposed `math.isfinite` fix is INSUFFICIENT.** It closes only `z ≥ 1.8e308`. The
entire finite band from ~3.4e38 upward still produces an all-NaN raster:

```
z=1e30  → 256/256 finite      z=1e150 → 0/256 ALL-NaN
z=1e38  → 256/256 finite      z=1e300 → 0/256 ALL-NaN
```

**3. The mechanism is float32 representability, not non-finiteness.** `numpy` names it
directly — `RuntimeWarning: overflow encountered in cast` at `rrim.py:236`. There are two
distinct modes: the *product* leaving float32 range (data-dependent), and the *multiplier
itself* leaving float32 range, which under NEP 50 casts the weak Python scalar to the array
dtype **before** multiplying. The second mode destroys correct answers: `1e-30 * 1e39`
returns `inf` where the true product `1e9` is trivially representable.

**Disposition:** deferred, not fixed. An owner-reviewed audit established the class is not
systemic — `compute_slope` and `compute_openness` are the only sites in the codebase that
multiply a raster by a user scalar and immediately store float32 unbounded. `pixel_size`
carries float64 headroom (finite at `px=1e-201`, peak 5.45e200); `hillshade` and
`red_strength` are bounded by trig/clip; `multigrad` sigmas already fail loudly via scipy.
The fix is a ~20-line invariant guard at 2 call sites, sketched and prototyped in
`.planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md`. Owner
decision: fail-fast (`ValueError`) when implemented, but not inside Phase 5 — this is a
phase reopened twice by landing extra numerical code late, and nothing here is reachable
with an honest input.

## Warnings

### WR-01 (WARNING): `__delitem__` docstring overclaims cross-store safety; a *successful* delete still destroys another live store's raster

**Status:** CONFIRMED (reproduced).
**File:** `src/pc2img/image_cache/disk_backed_image_store.py:72-78`, `tests/test_image_store.py:152-177`

**Issue:**
The docstring states the reorder means a delete "cannot destroy a raster that another store
over the same cache directory still owns (G10)". That holds only for the KeyError path. The
base `__init__` re-scans `*.npy` and adopts every key it finds, so a store constructed
*after* another store offloaded **tracks** that key — the delete then succeeds and unlinks
the shared codec pair:

```
npy exists: True
a tracks range (adopted from disk): True     <- store_a constructed AFTER store_b offloaded
npy after a-delete: False
b LOST DATA -> KeyError 'range'
```

The new test picks the one construction order (store_a built *before* the offload) that
yields the KeyError branch, so it asserts a strictly weaker property than the docstring
claims. Swapping two lines in the test's setup makes the same data loss reappear while the
suite stays green — i.e. the sensor would not catch a regression that reintroduced the
hazard through the adoption route. Mitigating context: `TiledPointCloudImageGenerator`
gives each tile its own `extend_cache_path(tile_id)` subdirectory, so this needs two
generators explicitly configured with the same `cache_path`.

**Fix:** narrow the docstring to the property actually held ("a delete that raises
`KeyError` is a no-op; a delete of a key this store tracks — including one adopted from
disk on construction — does purge the shared codec pair"), and add the second sensor so the
real semantics are pinned:

```python
def test_adopted_key_delete_purges_shared_pair(tmp_path):
    b = DiskBackedImageStore(config=_two_store_config(tmp_path))
    b.add_image_to_store("range", _gray((6, 6)))
    b.offload_image_data_to_disk("range")
    a = DiskBackedImageStore(config=_two_store_config(tmp_path))  # adopts from disk
    assert "range" in a
    del a["range"]
    assert not b._get_npy_path("range").exists()   # documented, intentional (G3)
```

### WR-02 (WARNING): `__delitem__` unlinks a path built from an unvalidated key — `../` escapes the cache directory

**Status:** CONFIRMED (reproduced).
**File:** `src/pc2img/image_cache/disk_backed_image_store.py:92-93`

**Issue:**
`_get_npy_path(key)` is `cache_dir / f"{key}.npy"` with no validation that the result stays
inside `cache_dir`. `DiskBackedImageStore` is exported from the public barrel
(`pc2img.image_cache.__all__`), and the new code path performs an unconditional `unlink`:

```
victim exists before: True
npy path for key: /tmp/tmpXXXX/cache/../victim.npy
victim content after offload: b'\x93NUMPY'      <- pre-existing file overwritten
victim exists after delete: False               <- deleted outside cache_dir
```

I traced reachability from the feature-name DSL and it is **not** currently reachable that
way: every registered `regex_pattern` anchors on a literal prefix (`range`,
`scalar_field_`, `rrim`, `sqrt_`, …), so no store key can begin with `..` or `/`, and an
embedded `a/../..` cannot traverse because the leading component is not an existing
directory. So this is a hardening gap on the public store API, not an exploitable path from
untrusted point-cloud metadata today. It is worth closing because this diff is what made
`__delitem__` a file-deletion primitive, and the module docstring asserts the purge is safe.

**Fix:**

```python
def _resolved_within_cache(self, path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(self._cache_dir.resolve()):
        raise ValueError(f"cache key escapes the cache directory: {path}")
    return resolved

def __delitem__(self, key: str) -> None:
    super().__delitem__(key)
    self._resolved_within_cache(self._get_npy_path(key)).unlink(missing_ok=True)
    self._resolved_within_cache(self._get_meta_path(key)).unlink(missing_ok=True)
```

### WR-03 (WARNING): Regex widening silently reinterprets base-feature names — it is additive for tokens, not for names

**Status:** CONFIRMED (reproduced).
**File:** `src/pc2img/features/rrim.py:43-45`, consumed at `src/pc2img/features/rrim.py:461, 482`

**Issue:**
`_parse_rrim_config` uses `_looks_like_option_token(tokens[0])` to decide whether the first
token is the base feature. Widening `_Z_FACTOR_RE` moved names into the option class:

```
PRE-DIFF  rrim_pack_(z1e5) -> base_feature='z1e5', z=1.0
POST-DIFF rrim_pack_(z1e5) -> base_feature='range', z=100000.0
POST-DIFF rrim_pack_(z1E5) -> base_feature='range', z=100000.0
```

Feature names are both public API and the on-disk cache key, so for any base feature whose
name matches `z\d+(\.\d+)?[eE][+-]?\d+`, the same string now denotes a different
computation while resolving to the same cache key. The comment on line 43-44 ("purely
ADDITIVE — every token accepted before is still accepted") is accurate at the token level
and misleading at the name level; it should not be the sole record of the BC analysis.

Likelihood is low (a scalar field literally named `z1e5`), but this is exactly the class of
BC event CLAUDE.md flags for the feature-name grammar, and it is currently undocumented and
untested.

**Fix:** correct the comment to state the actual scope of the change, and pin the new
precedence so a future edit cannot flip it silently:

```python
# G9: additive at the TOKEN level. Note the side effect at the NAME level: a
# first token matching the widened z grammar (e.g. `z1e5`) is now read as an
# option, not as a base feature. Option tokens take precedence over base names.
def test_exponent_token_takes_precedence_over_base_feature_name():
    assert rrim_module._parse_rrim_config("z1e5").base_feature == "range"
    assert rrim_module._parse_rrim_config("z1e5").z_factor == 100000.0
```

### WR-04 (WARNING): The G9 end-to-end test cannot detect `z_factor` being dropped from the computation

**Status:** CONFIRMED (reproduced).
**File:** `tests/test_rrim_features.py:221-227`

**Issue:**
`test_generate_rrim_small_z_end_to_end` asserts only `raster.shape == (16, 16, 3)` and
`np.isfinite(raster).all()`. Neither depends on `z_factor` reaching the math. I verified
that `z` genuinely changes the output:

```
slope differs: True
rgb differs: True     (compute_rrim(z=1.0) vs compute_rrim(z=1e-5))
```

so a regression that parsed `z` into the cache key but stopped threading it into
`compute_openness` / `compute_slope` would leave the whole suite green — which is precisely
the failure mode this phase exists to prevent. The test proves the *name* survives
`generate()`; it does not prove the *value* does.

**Fix:** make the assertion value-sensitive.

```python
def test_generate_rrim_small_z_differs_from_default_z(synthetic_pcd):
    gen = _rrim_generator(synthetic_pcd)
    images = gen.generate(["rrim", "rrim_(range,z1e-05)"])
    a = np.asarray(images["rrim"])
    b = np.asarray(images["rrim_(range,z1e-05)"])
    assert np.isfinite(b).all()
    assert not np.allclose(a, b, equal_nan=True), "z_factor did not reach the computation"
```

### WR-05 (WARNING): Round-trip coverage omits the upper `%g` exponent boundary, half of the same defect class

**Status:** CONFIRMED (reproduced).
**File:** `tests/test_rrim_features.py:186` (`_ROUND_TRIP_Z_VALUES`)

**Issue:**
`%g` switches to exponent notation at *both* ends: below `1e-4` **and** at or above its
6-digit precision. The tests only cover the lower end (`1e-06`, `1e-05`, `0.0001`); the
largest value in the list is `100.0`. The upper end was broken identically pre-diff and is
fixed by the diff, but nothing guards it:

```
1234567.5           old: 1.23457e+06  old_regex_ok: False  | new: 1234567.5
12345678.25         old: 1.23457e+07  old_regex_ok: False  | new: 12345678.25
999999.5            old: 1e+06        old_regex_ok: False  | new: 999999.5
1000000000000000.5  old: 1e+15        old_regex_ok: False  | new: 1000000000000000.5
```

`999999.5` is the sharpest case: `%g` collapses it to `1e+06`, which is both unparseable
*and* a collision with `z_factor=1000000.0`.

**Fix:** extend the parametrization so both boundaries are pinned.

```python
_ROUND_TRIP_Z_VALUES = [
    1e-06, 1e-05, 0.0001, 0.5, 1.0, 1.2345678, 2.5, 10.0, 100.0,
    999999.5, 1234567.5, 12345678.25, 1e15 + 0.5,   # upper %g exponent boundary
]
```

### WR-06 (WARNING): `test_delete_absent_key_does_not_raise` encodes the contract the fix just inverted

**Status:** CONFIRMED (read + traced; the test body does not do what its name says).
**File:** `tests/test_image_store.py:128-134`

**Issue:**
The test name asserts that deleting an absent key does not raise. After the G10 fix, that is
the **opposite** of the contract: `super().__delitem__(key)` runs first specifically so an
untracked key raises `KeyError` (and the new G10 test asserts exactly that with
`pytest.raises(KeyError)`). The body does not test an absent key at all — it adds `"range"`,
then deletes a key that is present but never offloaded. Two adjacent tests in one file now
state contradictory contracts by name, and a future maintainer reading only the name could
"fix" the code back into the G10 defect.

**Fix:** rename to describe the actual scenario, and let the G10 test own the absent-key
contract.

```python
def test_delete_tracked_but_never_offloaded_key_does_not_raise(tmp_path: Path):
    # Present in memory, no on-disk codec pair: unlink(missing_ok=True) carries the safety.
```

## Info

### IN-01: Dead module-level `logger`, bound to the root package rather than the module

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:9`
**Issue:** `logger` is never used anywhere in the module (verified by grep), and it binds
`logging.getLogger(__name__.split(".")[0])` — the root `pc2img` logger — contrary to the
project convention `logging.getLogger(__name__)` documented in CLAUDE.md. Dead code that
also models the wrong pattern.
**Fix:** delete the `logger` binding and the now-unused `import logging`, or use it (a
`logger.debug("purged codec pair for %s", key)` in `__delitem__` would be genuinely useful
given the destructive semantics) and correct it to `getLogger(__name__)`.

### IN-02: `_validate_clip` ignores its `name` parameter, so the error cannot say which clip failed

**File:** `src/pc2img/features/rrim.py:107-112`
**Issue:** `name` is accepted and never read. `_validate_percentile_bounds` raises
`"percentiles must lie within [0, 100], got low=…, high=…"` with no indication of whether
`sclip` or `oclip` was at fault — the whole point of passing the name.
**Fix:** either drop the parameter, or wrap: `raise ValueError(f"{name}_clip: {e}") from e`.

### IN-03: `ruff check` fails B008 on the store constructor; CI does not run ruff

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:31`
**Issue:** `[tool.ruff.lint] select` includes `B`, and `ruff check` on the reviewed files
reports `B008` for `config: LazyDiskCacheConfig = LazyDiskCacheConfig()`. `.github/workflows/ci.yml`
runs only `uv run --frozen pytest`, so the lint failure is ungated. The runtime risk is nil
(`LazyDiskCacheConfig` is a frozen pydantic dataclass — GSEGUtils carries a `# noqa: B008`
with that justification), but this leaves the repo's own lint config red while CI is green,
which is the pattern CLAUDE.md warns about.
**Fix:** mirror the upstream suppression with the same justification, or add a ruff step to CI.

```python
config: LazyDiskCacheConfig = LazyDiskCacheConfig(),  # noqa: B008  # frozen pydantic dataclass — safe as default
```

## Verified-Sound (no finding — recorded so a re-review need not redo the work)

- **Zero cache-key churn (plan's locked requirement): HOLDS.** 9,000,000 exhaustive
  ≤6-significant-digit decimals across `[1e-4, 1e6)` plus ~300k structured/random/bit-pattern
  floats: no value where the old token was valid-and-correctly-encoded and the new token
  differs. `repr` and `%g` cannot diverge on a correctly-encoded value because `%g`'s
  plain-decimal window is a strict subset of `repr`'s and `repr` is the shortest exact form.
- **Round trip: exact over all finite positive doubles tested.** 50k-value fuzz through
  `RRIMConfig → pack_feature_name → FEATURES.match → _parse_rrim_config`, including `5e-324`,
  `1e-320`, `2**-53`, `2**53`, `2**53+2`, `1.7976931348623157e308`, and 17-digit values —
  zero mismatches, zero registry double-matches, `repr` never emits `+` or uppercase `E` in
  the non-integer branch (positive-exponent floats are all integral and take the `int` branch).
- **Exactly one membership authority in `__delitem__`.** No `if key in self` pre-check was
  reintroduced; `super().__delitem__` is the sole gate.
- **The `super()` claim checks out against GSEGUtils source.** `DiskBackedStore.__delitem__`
  is `del self._store[key]` and nothing more; `_cache_dir` is never `None` (temp-dir
  fallback), so the removed guard was genuinely dead; no GSEGUtils code path evicts via
  `__delitem__`, so the override cannot fire as a memory-pressure eviction.
- **G3 stays closed.** `test_delete_purges_on_disk_codec_pair` and
  `test_overwrite_does_not_leave_stale_on_disk_raster` both still pass with the new ordering;
  a successful delete purges both `.npy` and `.meta.json`.
- **DSN-09 posture intact.** No `pickle.load*` sink; overwrite-then-serve returns the new
  raster (verified: `2.0`, not the stale `1.0`), and a fresh store re-scans only `*.npy`, so
  the residual `<key>.dat` is inert as the deferred note states — the diff did not worsen it.
- **Fixtures are deterministic** (`conftest.py` `_DEFAULT_SEED = 0`), so the new end-to-end
  tests are not flaky.
- **Full suite: 162 passed** on the reviewed tree.

---

_Reviewed: 2026-07-27T14:02:28Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
