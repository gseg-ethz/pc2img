---
phase: 05-bug-fixes-module-test-coverage
reviewed: 2026-09-25T10:25:14Z
depth: deep
review_scope: "round 5, gap closure 05-18 / 05-19 — git diff c93e045..dc7783d -- src tests"
files_reviewed: 28
files_reviewed_list:
  - src/pc2img/core.py
  - src/pc2img/errors.py
  - src/pc2img/features/core.py
  - src/pc2img/features/derivative_features.py
  - src/pc2img/features/manager.py
  - src/pc2img/features/registry.py
  - src/pc2img/features/rrim.py
  - src/pc2img/image_cache/__init__.py
  - src/pc2img/image_cache/disk_backed_image_data.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - src/pc2img/registry.py
  - src/pc2img/strategies/interpolation.py
  - src/pc2img/strategies/projection.py
  - src/pc2img/tiled_generator.py
  - src/pc2img/util.py
  - tests/conftest.py
  - tests/test_conftest_smoke.py
  - tests/test_derivative_features.py
  - tests/test_disk_backed_image_data.py
  - tests/test_feature_registry.py
  - tests/test_hygiene.py
  - tests/test_image_store.py
  - tests/test_interpolation.py
  - tests/test_manager.py
  - tests/test_projection.py
  - tests/test_rrim_features.py
  - tests/test_tiled_generator.py
  - tests/test_util.py
findings:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 05: Code Review Report — round 5, gap closure 05-18 / 05-19

**Reviewed:** 2026-09-25T10:25:14Z
**Depth:** deep
**Files Reviewed:** 28
**Status:** issues_found
**Diff under review:** `c93e045..dc7783d -- src tests`. The round-4 report is kept in git at `c93e045`.

## Summary

This is the required review of the round-5 gap-closure diff. It covers:

- **05-18**: the `add_image_to_store` reorder to containment → shape → delete → build, the new `_assert_image_shape` helper, and the rewritten store and RRIM tests.
- **05-19**: the 28-file sweep of planning references out of comments and docstrings.

Every defect claim below was reproduced by running code with `.venv/bin/python`. Mutations were applied through a throwaway pytest plugin in the session scratchpad. `src/` and `tests/` were never modified (`git status --short src tests` is empty).

**What holds (verified by running code, not by reading):**

- **05-19 changed only comments and docstrings.** I blanked the docstrings and compared `ast.dump`. From `a6695fc` (end of 05-18) to HEAD, all 28 files are identical, so no identifier, runtime string, marker reason or parametrize id moved. From `c93e045` to HEAD, only the four 05-18 files differ, which is expected.
- **The 05-18 mutation claims reproduce exactly:**
  - Old delete-then-build ordering: `2 failed, 27 passed`. Both `test_failed_overwrite_…[in_memory|codec_offloaded]` fail.
  - Unlink-first `__delitem__`: `2 failed, 27 passed` (the absent-key test and the two-store sensor).
  - `slope_noz` (z dropped from `compute_slope`): `1 failed, 50 passed`, with the message "slope path is z_factor-insensitive".
- **The shape guard runs before the delete**, so a 1-D replacement no longer destroys the entry.
- **The store test module no longer leaks** `tmp*` directories (0 per run).
- **The full suite passes:** `196 passed`.

**What does not hold:**

- **The overwrite fix does not cover every input-driven failure.** The new docstring says it does, but three input classes still destroy the old entry and its codec pair (WR-01).
- **The shape guard is a bare `assert`**, so the guarantee disappears under `python -O` (WR-02).
- **No test pins the claim that containment is checked before shape** (WR-03).
- **05-19 made one rewrite that changes a technical claim, and the new claim is wrong.** It is in the `__delitem__` history (WR-04).
- **The new docstring calls delete-before-build "the one safe ordering".** It has the same held-reference hazard as build-first, and the shipped docstring does not mention it (WR-05).
- **The planning-reference sweep's regex misses several shipped references**, including a `.planning/todos` file name. The entry for that finding is still marked resolved in the phase UAT file (`05-UAT.md`) (WR-06).

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Validate-before-delete misses input-driven failures; the docstring overclaims and old data is still lost

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:144-146` (claim), `:174-177` (code)

**Issue:** The docstring says *"every failure that is a function of the inputs — containment, then raster shape — is validated BEFORE the existing entry is dropped, so a failed overwrite is a full no-op"*. The code only checks containment and `ndim`/channel count before `del self[img_name]`. Some input-driven failures come only from `add_data_to_store` / `LazyDiskCache.__init__`, which run after the delete:

- **Empty rasters**, for example `(0, 0)` or `(0, W, 3)`. These pass `_assert_image_shape`. Then `np.memmap` raises `ValueError: cannot mmap an empty file`.
- **Zero-itemsize dtypes** (`V0`). Same `ValueError`.
- **Override kwargs of the wrong type**, for example `enable_caching_override=2` or `purge_disk_on_gc_override="maybe"`. `LazyDiskCache.__init__` is `@validate_call` and raises `pydantic.ValidationError`.

**Reproduction.** Store over a temp dir with `enable_caching=True`. Add `range = full((4,4), 7)`, optionally offload it through the codec, then overwrite:

```
empty (0,0) raster     offloaded=True  -> ValueError: cannot mmap an empty file
    tracked=False original_served=read->KeyError before=['range.meta.json','range.npy'] after=['range.dat']
V0 dtype               offloaded=True  -> ValueError: cannot mmap an empty file
    tracked=False original_served=read->KeyError before=['range.meta.json','range.npy'] after=['range.dat']
enable_caching_override=2 offloaded=True -> ValidationError (LazyDiskCache.__init__)
    tracked=False original_served=read->KeyError before=['range.meta.json','range.npy'] after=[]
```

This is the same kind of data loss that the round-4 overwrite finding (WR-07) was meant to close. The old entry, its `.npy` + `.meta.json` pair and its `.dat` are gone. The empty-raster case also leaves an orphan, untracked `range.dat` behind, because the failed replacement created it before its finalizer was registered.

**Reachability:** only direct callers of the public barrel. `FeatureManager.submit` never passes overrides and never re-submits a tracked name. `ImgRes` does not reject a zero dimension, but it is not proven here that the pipeline produces an empty raster.

**Fix:** Validate everything the build depends on before the delete, or narrow the docstring to what is actually checked. Minimal version:

```python
self._get_npy_path(img_name)
_assert_image_shape(img_data)
if img_data.size == 0 or img_data.dtype.itemsize == 0:
    raise ValueError(f"refusing empty raster {img_data.shape} / dtype {img_data.dtype}")
for flag in (enable_caching_override, automatic_offloading_override, purge_disk_on_gc_override):
    if flag is not None and not isinstance(flag, bool):
        raise TypeError(f"cache overrides must be bool or None; got {flag!r}")
if img_name in self:
    del self[img_name]
```

If the owner prefers not to add checks, rewrite the sentence as: "containment and raster-shape failures are validated before the drop; other build failures (empty rasters, invalid override types, OSError) are not recovered". Add those classes to the documented residual.

### WR-02: The overwrite-atomicity guard is a bare `assert`, removed under `python -O`

**File:** `src/pc2img/image_cache/disk_backed_image_data.py:22-29`; `src/pc2img/image_cache/disk_backed_image_store.py:175`

**Issue:** `_assert_image_shape` is an `assert` statement. The project convention in CLAUDE.md says asserts are for internal invariants and "Do not rely on asserts for validating external/API inputs". The helper's own docstring says it is "an internal-invariant signal, not user-input validation". Yet 05-18 made it the guard that stops the public `add_image_to_store` from dropping an entry on bad input. The pinned `AssertionError` contract therefore depends on an interpreter flag.

**Reproduction:**
- `.venv/bin/python -O -m pytest tests/test_image_store.py` → `2 failed, 27 passed`. Both `test_failed_overwrite_…` cases fail because no `AssertionError` is raised.
- Under `-O`, `add_image_to_store("range", np.ones(4))` over a codec-offloaded 2-D entry is **accepted**. The stored raster becomes shape `(4,)`.

**Fix:** Keep the exception type (so there is no breaking-change event) but make the check unconditional:

```python
def _assert_image_shape(image_data: np.ndarray) -> None:
    if not (image_data.ndim in (2, 3) and (image_data.ndim == 2 or image_data.shape[-1] == 3)):
        raise AssertionError(f"image_data must be 2-D or (H, W, 3); got shape {image_data.shape}")
```

Also update the docstring. It now guards a public entry point, so "not user-input validation" is no longer accurate.

### WR-03: No test pins containment-before-shape precedence

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:148-151, 174`; `tests/test_image_store.py` (no test covers it)

**Issue:** The docstring and the 05-18 must-have both claim that the `self._get_npy_path(img_name)` pre-check keeps containment's `ValueError` ahead of the shape `AssertionError`. That line is the only thing that enforces the ordering. For well-shaped data it is redundant, because `__delitem__` and `add_data_to_store` check containment anyway. Only the plan's one-off `python -c` chain checked the precedence. No test does.

**Reproduction (throwaway plugin):**
- Delete the pre-check line: `29 passed`.
- Swap it after `_assert_image_shape`: `29 passed`.
- Direct probe with an escaping key `../victim` and a 1-D array:
  - HEAD: `untracked -> ValueError`, `tracked -> ValueError`.
  - Pre-check removed: `untracked -> AssertionError`, `tracked -> AssertionError`.

**Fix:** Add a proving test whose name matches `-k "escaping or refused"`, so the Phase-6 regression-net selector picks it up:

```python
@pytest.mark.parametrize("tracked", [False, True], ids=["untracked", "tracked"])
def test_escaping_key_refused_before_shape_check(tmp_path, tracked):
    sentinel, cfg = _escape_layout(tmp_path)
    store = DiskBackedImageStore(config=cfg)
    key = _escaping_keys(tmp_path)["parent_segment"]
    if tracked:
        store[key] = DiskBackedImageData(_gray((4, 4)))
    with pytest.raises(ValueError):
        store.add_image_to_store(key, np.ones(4, dtype=np.float32))
```

### WR-04: The 05-19 rewrite of the `__delitem__` history states a false mechanism

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:199-202`

**Issue:** The sweep changed the history clause to: *"building the codec paths after the base delegation made a refused containment delete non-atomic (the unlink could still land before a later-stage ``ValueError`` was raised)"*. The parenthetical is new and wrong.

The historical body (`f776011`) was:

```python
super().__delitem__(key)
self._get_npy_path(key).unlink(...)
self._get_meta_path(key).unlink(...)
```

`_get_npy_path` raises before the first unlink. The `.npy` and `.meta.json` paths share one parent, so the meta check cannot fail after the npy check passes. What the refused delete really lost was **in-memory membership**. The removed test `test_refused_delete_leaves_store_membership_intact` pinned exactly that. This is the defect class the round-4 IN-03 finding covered, and the plan forbade changing technical claims.

**Reproduction.** I ran the `f776011` body against the current guarded builders, with sentinel `victim.npy` and `victim.meta.json` files one level above the cache dir:

```
'../victim'           -> ValueError; still tracked=False; outside files=['victim.meta.json', 'victim.npy']
'sub/../../victim'    -> ValueError; still tracked=False; outside files=['victim.meta.json', 'victim.npy']
'/tmp/.../victim'     -> ValueError; still tracked=False; outside files=['victim.meta.json', 'victim.npy']
```

No unlink ever landed. The entry was silently dropped.

**Fix:**

```
disk. This ordering fixed two distinct historical defects: building the
codec paths after the base delegation made a refused containment delete
drop the in-memory entry before the ``ValueError`` was raised (a refused
delete was not a no-op in memory); separately, the original absent-key
defect unlinked the codec pair before the membership check, so an
untracked key still destroyed a live pair on disk.
```

### WR-05: The docstring calls delete-before-build "the one safe ordering", but it has the same held-reference hazard

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:156-172`

**Issue:** The new docstring rejects build-then-swap because the replacement reopens the shared `<key>.dat` with `r+` (clobbering the old buffer), and the old entry's path-bound finalizer later unlinks the new `.dat`. It then calls delete-before-build "the one safe ordering". But `del self[img_name]` only drops the store's reference. If anything else still holds the old entry, for example a raster returned by `generate()` / `get_targets()` or a `store[key]` a caller kept, the same two failures happen on a successful overwrite at HEAD.

The docstring's "Documented residual" names only the OSError-mid-build case. The held-reference hazard is recorded only in `.planning/` (the Phase-6 todo), and `.planning/` is stripped from `main`.

**Reproduction (HEAD, successful overwrite):**

```
held old entry now reads: 2.0 (was 1)
files after old entry dies: []
new entry after offload/read -> FileNotFoundError [Errno 2] No such file or directory: '.../range.dat'
```

**Fix:** Do not overclaim in shipped text. Replace "is therefore the one safe ordering" with "avoids the clobber only when the store holds the last reference to the old entry". Add a second residual paragraph: "a caller-held reference to the replaced entry keeps its path-bound finalizer alive; the replacement then shares its `.dat`, the held object reads the new data, and its collection unlinks the replacement's memmap — an upstream LazyDiskCache fix (object-/inode-bound finalizer) is required." The code fix itself stays deferred to GSEGUtils, as the owner decided.

### WR-06: The planning-reference sweep is marked resolved, but shipped planning references remain

**File:** `tests/test_rrim_features.py:236-237`, `tests/test_feature_registry.py:60-61`, `tests/test_image_store.py:51`, `tests/test_image_store.py:439`, `src/pc2img/image_cache/disk_backed_image_store.py:34`, `src/pc2img/image_cache/disk_backed_image_store.py:95`

**Issue:** The round-4 planning-reference finding (IN-04, `review-r3-6cf03abfa333`) is marked resolved in `05-UAT.md` on the evidence "gate 0 hits". The owner widened the class to include "planning file names … spike references" in both trees. The gate's regex has no alternation for most of that vocabulary, so these survive:

- `test_rrim_features.py:236-237` — "the deferred Phase-6 item (``2026-07-27-rrim-float32-scaling-invariant-guard.md``)". This is a `.planning/todos/` file name, which dangles on `main`.
- `test_feature_registry.py:60-61` — "correction to the FINDINGS framing captured in the plan objective".
- `test_image_store.py:51` — "Pitfall 6" (a research-note ID).
- `test_image_store.py:439` — "this gap round does not open" (added by 05-18 itself, which was told to write no ledger wording).
- `disk_backed_image_store.py:34` — "a GSEGUtils carry-out".
- `disk_backed_image_store.py:95` — "(measured and verdict VALIDATED)". This is the remnant of a spike citation and has no referent left.

**Reproduction:**

```
grep -rnE -i "phase[- ]?[0-9]|pitfall|gap round|carry-out|verdict|FINDINGS framing|[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+\.md" src/pc2img tests
```

This prints the lines above. The gate in the 05-19 plan exits 0 on the same tree.

**Fix:** Rewrite each line as a property:
- "the float32 overflow at such z is a known, separately tracked limitation"
- "the fallback must not become a raise"
- drop "Pitfall 6:"
- "changing it would be a breaking change"
- "an upstream GSEGUtils concern"
- drop the parenthetical

Then extend the gate regex with `Phase[- ]?[0-9]|Pitfall [0-9]|gap round|carry-out|verdict|\d{4}-\d{2}-\d{2}-[\w-]+\.md`. Reopen the UAT entry until the extended gate is clean. Leave `_SENTINEL_BYTES` ("round-3") alone as the documented runtime-string exception, and list it as a residual.

## Info

### IN-01: The new test's docstring points at the old location of the shape rule

**File:** `tests/test_image_store.py:436-439`

**Issue:** `test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact` says the rule "lives in `DiskBackedImageData.__init__`". After the hoist it lives in `_assert_image_shape`, and the store calls it directly on this path; `__init__` is never reached for the failing call.

**Fix:** Change it to "the rule lives in `_assert_image_shape`, called by the store before the old entry is dropped".

### IN-02: The sweep added two new ruff ERA001 hits

**File:** `tests/test_util.py:123`, `tests/test_util.py:153`

**Issue:** `# Breadth: replace_nan (TEST-06)` became `# Breadth: replace_nan`, which ruff now parses as an annotated assignment ("commented-out code"). The ruff finding count goes from 4 at `c93e045` to 6 at HEAD (`ruff check src/pc2img tests --ignore E402,C901,B008`). The count is not gated, because the hygiene test only lints `src/`.

**Fix:** Use a phrasing that does not parse as code, for example `# Breadth coverage — replace_nan`.

### IN-03: The strengthened absent-key test is now almost a subset of the two-store sensor

**File:** `tests/test_image_store.py:149-179` vs `:198-225`

**Issue:** Both tests use the same setup:
- a store constructed before a peer offloads the key,
- `del` on the non-owning store raises `KeyError`,
- the pair is asserted to survive.

Both fail on exactly the same mutation (unlink-first, 2 failed). The absent-key test adds only a listing-equality check. The IN-06 goal was "no duplicate tests", and this partly undoes it.

**Fix:** Either fold the listing assertion into `test_failed_delete_preserves_codec_pair_and_both_stores` and drop the absent-key test, or make it cover something the two-store test cannot. One option is a `.dat`-only peer entry (a plain `offload()`), which catches a mutation that unlinks `<key>.dat` too.

### IN-04: Temp-file leaks remain elsewhere in the suite

**File:** tests other than `test_image_store.py` (measured per module)

**Issue:** The store module now leaks 0 `tmp*` entries. A full-suite run still leaves 18 top-level `tmp*` directories and `*.dat` files in `/tmp`:

| Module | Leaked `tmp*` entries |
|---|---|
| `test_disk_backed_image_data.py` | 3 |
| `test_interpolation.py` | 6 |
| `test_manager.py` | 2 |
| `test_point_cloud_image_generator.py` | 2 |
| `test_rrim_features.py` | 5 |

The sources are no-config `DiskBackedImageStore` / `LazyDiskCache` `mkstemp` / `mkdtemp`. This is outside IN-06's stated scope (the store module).

**Fix:** Add an autouse fixture in `tests/conftest.py` that runs `monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))`, so every test's temp files land inside pytest's tree.

---

_Reviewed: 2026-09-25T10:25:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
