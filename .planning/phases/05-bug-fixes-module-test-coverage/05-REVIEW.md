---
phase: 05-bug-fixes-module-test-coverage
reviewed: 2026-09-24T15:38:56Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - src/pc2img/features/rrim.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_image_store.py
  - tests/test_rrim_features.py
findings:
  critical: 0
  warning: 8
  info: 6
  total: 14
status: issues_found
---

# Phase 5: Code Review Report (round 4, gap closure 05-16 / 05-17)

**Reviewed:** 2026-09-24T15:38:56Z
**Depth:** deep
**Files Reviewed:** 4
**Status:** issues_found
**Diff scope:** `git diff 443d390..HEAD -- src tests`. Full files were read for context, along with the GSEGUtils 0.5.3 `DiskBackedStore` / `LazyDiskCache` source they call into, `FeatureManager`, and `FeatureRegistry.match`.

## Summary

The main round-4 fixes are correct. I confirmed each one by running code:

- **`__delitem__` ordering.** Containment is checked before any in-memory or on-disk change. An escaping key now raises `ValueError` with the store left as it was. An absent ordinary key still raises `KeyError` and does nothing on disk, and the base store is still the only authority on membership. Mutation check: reverting to the 05-15 order makes 7 tests fail.
- **Parent-only resolve.** No key-reachable escape is newly admitted. I tried 15 key spellings, including `..`, `.`, `""`, `sub/..`, `../`, a symlinked parent directory pointing outside, NUL, and `//etc/passwd`. Keys that escape were refused, and keys that stay inside were admitted. A planted symlink at `<key>.npy` / `<key>.meta.json` is never written *through*: `_store_entry` uses `os.replace` and delete uses `unlink`, and both act on the link itself. Mutation check: the full-resolve predicate makes the symlink test fail.
- **Constructor None-sentinel.** Old and new signatures behave the same for omitted, instance, dict, path-dict and bad input. The only difference is that `config=None` is now accepted.
- **`_validate_clip`.** Only the message and the `from` chaining changed; nothing else in `rrim.py` moved. Mutation check: dropping the wrapper makes 3 tests fail.
- **Threat-posture paragraph.** Reproduced end to end. A PCD scalar field named `../victim` passed to `generate(["../victim"])` is refused. With the guard removed, the same call overwrites `<root>/victim.dat` outside the cache directory. The claim that the guard is LOAD-BEARING holds.

The defects are in what surrounds the fix:

1. **Round 4 weakened the insertion-route test** (WR-01). The 05-16 edit rests on a false premise: that inserting alone never writes. It does write `<key>.dat`. A mutation that removes the guard from the insertion route only now passes the **whole suite** (196 passed) while writing `victim.dat` outside the cache directory. The round-3 version of the test caught that mutation.
2. **Tests that can't fail.** The delete half of the symlink test is vacuous (WR-02). The new "z changes the output" test does not pin z on the slope path (WR-03).
3. **A new stuck state** (WR-04). A key inserted through the setter that escapes the cache directory can no longer be removed through the public API: `clear()` and `pop()` raise on it every time.
4. **Docstrings claim more than the code does** (WR-05). They still say no read can touch a file outside the cache directory, but round 4 deliberately serves reads through cache-internal symlinks.
5. **A latent hole in the containment helper** (WR-06). It admits a path whose final component is `..`.
6. **Two pre-existing defects next to the round-4 claims** (WR-07, WR-08).

No BLOCKER-tier defects were found.

All transcripts below come from `.venv/bin/python` / `.venv/bin/pytest` runs against HEAD. Mutations were applied with a scratch pytest plugin (`-p mutplug`), so no repo file was edited.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: The round-4 add test no longer catches an unguarded insertion route, and its docstring's premise is false

**File:** `tests/test_image_store.py:307-329` (also `:500-509`)
**Severity:** WARNING. This weakens the proving test on the route the guard exists to protect.

**Issue:** 05-16 moved `offload_image_data_to_disk(key)` into the `pytest.raises` block. The reason given in the docstring is: "With the guard disabled … insertion alone never writes". That is false. With `enable_caching=True`, `add_data_to_store` calls the factory, and `LazyDiskCache._init_from_config` → `_convert_to_memmap` then creates the `<key>.dat` memmap. The class docstring says so itself at `disk_backed_image_store.py:69-72`. The round-3 finding WR-03 reached its wrong conclusion because it only watched the `victim.npy` sentinel.

This is what the edit costs. Suppose `offload` raises `ValueError` from the still-guarded `_store_entry` while `add_image_to_store` has stopped raising. The test then passes even though insertion has already written outside the cache directory. The sentinel assertions still never decide the outcome: with the guard live nothing is written, and with the guard fully removed the test fails on `DID NOT RAISE` first.

This mutation is realistic. The spike README records that GSEGUtils phase-14 has **zero** `self._get_npy_path` call sites, and the pin `GSEGUtils >= 0.5.3, < 1.0` admits 0.6. An upstream change of this kind is exactly how the override would silently drop off the insertion route.

The companion test at `:500-509` uses only the benign key `"range"`, so it passes under the same mutation too.

Reproduction. The insertion route is unguarded (`add_data_to_store` builds its path via `DiskBackedStore._get_npy_path`), while delete, offload and load stay guarded:
```
$ MUT=insert_unguarded pytest -q -s -p mutplug tests/test_image_store.py -k escaping_key_add
[insert_unguarded] files written OUTSIDE cache dir in test_escaping_key_add_refuses_0: ['victim.dat']
[insert_unguarded] files written OUTSIDE cache dir in test_escaping_key_add_refuses_1: ['victim.dat']
[insert_unguarded] files written OUTSIDE cache dir in test_escaping_key_add_refuses_2: ['victim.dat']
3 passed, 26 deselected
$ MUT=insert_unguarded pytest -q -p mutplug tests/
196 passed
$ MUT=insert_unguarded pytest -q -p mutplug <round-3 test_image_store.py @443d390> -k escaping_key_add
E       Failed: DID NOT RAISE ValueError   (x3)
3 failed
```
Direct check that inserting alone writes outside the cache directory when the guard is removed:
```
'../victim'        after add only -> outside-cache files: ['victim.dat', 'victim.npy']
'a/../../victim'   after add only -> outside-cache files: ['victim.dat', 'victim.npy']
```
**Fix:** Pin each route separately, and check for *any* new file outside the cache directory rather than one sentinel name:
```python
def _outside_files(tmp_path):
    return sorted(p.name for p in tmp_path.iterdir() if p.name != "cache")

before = _outside_files(tmp_path)
with pytest.raises(ValueError):
    store.add_image_to_store(key, _gray((4, 4)))       # insertion alone
assert _outside_files(tmp_path) == before              # catches victim.dat
assert key not in store
```
Keep a separate test for the offload route that uses a setter-inserted, caching-enabled entry. Also correct the "insertion alone never writes" sentence in the docstring and in the round-3 ledger entry.

### WR-02: The delete half of the symlink test is vacuous, because pickling has already replaced the symlinks with regular files

**File:** `tests/test_image_store.py:454-464`
**Issue:** The test says "delete must only remove the LINK". But `pickle.dumps(store)` at `:454` runs `__getstate__` → `offload(pickle_container=True)` → `_store_entry`, and its `os.replace` swaps the regular `range.npy.tmp` in over the `cache/range.npy` **symlink**. So `store2` at `:459` deletes regular files, and the `shared/…` assertions can't fail under any unlink implementation. A mutation that deletes the symlink **target** (`path.resolve().unlink()`) passes the whole file:
```
before pickle: npy is_symlink = True  meta is_symlink = True
after  pickle: npy is_symlink = False  meta is_symlink = False
$ MUT=unlink_follow pytest -q -p mutplug tests/test_image_store.py
29 passed
```
The behaviour the test is named for, deleting a symlinked entry, is therefore not tested. There is also a side effect nobody documented: pickling a store (the joblib/loky tiled path) silently turns served symlinks into independent copies.

**Fix:** Build a fresh layout before the delete assertion, or re-create the links. Assert `(cache/"range.npy").is_symlink()` just before `del store2["range"]`, so the precondition can't quietly disappear again. Decide whether de-linking on pickle is acceptable, and document it either way.

### WR-03: `test_generate_rrim_z_factor_changes_the_output` does not pin z on the slope path

**File:** `tests/test_rrim_features.py:271-298`
**Issue:** The docstring says: "If z were dropped from the computation, both pairs … would be array-equal". That holds only if z is dropped *everywhere*. In the `rrim` composite, the slope term is robust-percentile normalised (`_normalize_robust`), so a linear z scale cancels out of the red channel. `rrim_z1 != rrim_z4` then holds purely because of the openness-derived structure channel from the pack. Dropping `z_factor` from `compute_slope` (the red channel and `rrim_component_(slope,…)`) goes unnoticed:
```
$ MUT=slope_noz pytest -q -p mutplug tests/test_rrim_features.py
51 passed
$ MUT=openness_noz pytest -q -p mutplug tests/test_rrim_features.py
FAILED tests/test_rrim_features.py::test_generate_rrim_z_factor_changes_the_output
MUT= None      | component slope z1==z4: False | rrim z1==z4: False
MUT= slope_noz | component slope z1==z4: True  | rrim z1==z4: False
```
**Fix:** Add the component-slope pair, which is the only place slope's z is observable:
```python
"rrim_component_(slope,range,z1)", "rrim_component_(slope,range,z4)",
...
assert not np.array_equal(slope_z1, slope_z4, equal_nan=True), "slope path is z_factor-insensitive"
```
Also correct the docstring: the rrim pair pins z through the pack only.

### WR-04: Checking containment first makes a setter-inserted escaping key impossible to remove through the public API

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:200-204` (setter inherited unguarded from the base, `DiskBackedStore.__setitem__`)
**Issue:** `store[key] = value` does not check containment, but `del store[key]` now refuses before it drops anything. A key admitted by one route can never be removed by the other. `MutableMapping.clear()` / `popitem()` / `pop()` raise `ValueError` on it every time. `clear()` also leaves the store part-cleared, and it gets stuck on the same key on every retry. Under 05-15 the same sequence healed itself after one failure, so this is a behaviour change round 4 introduced, and neither the docstring nor the tests mention it. The only way out is the private `store.store` dict.
```
keys: ['range', '../victim']
clear attempt 0: ValueError; keys now ['../victim']
clear attempt 1: ValueError; keys now ['../victim']
clear attempt 2: ValueError; keys now ['../victim']
pop: ValueError
only escape hatch is the private dict: True []
# same script under the 05-15 ordering:
clear attempt 0: ValueError; keys now []
clear ok
```
pc2img's own code never uses the setter (`FeatureManager` goes through `add_image_to_store`), so this is limited to the public-barrel API. That is also the surface the docstring says it defends.

**Fix:** Close the asymmetry at insertion, so an escaping key can never be tracked in the first place:
```python
def __setitem__(self, key: str, value: DiskBackedImageData) -> None:
    self._get_npy_path(key)          # containment authority; raises ValueError
    super().__setitem__(key, value)
```
The base store's own loads (`__getitem__`, `__setstate__`) write `self._store[...]` directly, so they are unaffected. The escaping-delete tests would then seed through `store.store[key] = …` to reach the delete path.

### WR-05: The containment docstrings overstate the guarantee now that round 4 serves reads through cache-internal symlinks

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:24-29, 101-102, 113-114`
**Issue:** The class docstring still says every key-built path "resolves *inside*" the cache directory, "so no key can make a write, a read or an unlink touch a file outside that directory". Round 4 deliberately stopped resolving the final component. `test_symlinked_cache_entry_is_served_and_unpickles` asserts that a **read** through `cache/range.npy → shared/range.npy` succeeds, and that read touches a file outside the directory.

Writes to key-derived sibling paths also follow planted symlinks. Neither predicate ever guarded these (pre-existing, but covered by the same sentence):
```
w1 after offload via planted j.npy.tmp:       b"\x93NUMPY\x01\x00v\x00{'desc"
w2 after offload via planted j.meta.json.tmp: b'{"schema_version'
w3 after memmap offload via planted m.dat:    [9. 9. 9.]
```
Two further inaccuracies. The helper docstring says "only the *check* resolves", but it now resolves only the parent. The error message says "it resolves to {candidate}" for a path that is *not* fully resolved.

**Fix:** State the actual invariant: "every key-built path's *directory* resolves inside the cache directory; the final component is not followed, so a symlink placed inside the cache directory is served on read". State the threat model explicitly as well. Anyone with write access to the cache directory is out of scope, since they can plant `*.tmp` / `.dat` symlinks. Reword the error message to "its parent resolves to …".

### WR-06: `_assert_within_cache_dir` admits a path whose final component is `..`, a latent hole the old predicate did not have

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:109-111`
**Issue:** `candidate = path.parent.resolve() / path.name` is correct only if `path.name` is never `..`. Pathlib does not collapse `..`, and `is_relative_to` is purely lexical, so `cache/..` passes:
```
ADMITTED /tmp/tmp7be9z4pd/cache/.. -> real /tmp/tmp7be9z4pd
ADMITTED /tmp/tmp7be9z4pd/cache/sub/../.. -> real /tmp/tmp7be9z4pd
```
No current key can reach this: both builders append `.npy` / `.meta.json`, so the final component is never `..`. I ran 15 spellings to check. But the helper is documented as "the single containment authority" and is LOAD-BEARING. The full-resolve predicate refused this path, and nothing records the unstated precondition. A future builder that passes a directory or a path with a separate suffix, for example during the Phase-6 0.6 adoption, would inherit the hole silently.

**Fix:**
```python
if path.name in ("", ".", ".."):
    raise ValueError(f"Refusing raster key path {str(path)!r}: final component {path.name!r} is not a file name.")
candidate = path.parent.resolve() / path.name
```
Add a unit test that feeds `cache_dir / ".."` straight to the helper.

### WR-07 (pre-existing, adjacent to round-4 claims): an overwrite that fails for any reason other than containment destroys the existing entry and its codec pair

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:145-153`
**Issue:** Round 4 made refusals atomic, but only for containment. `add_image_to_store` still runs `del self[img_name]`, which drops the in-memory entry **and unlinks `.npy` + `.meta.json`**, before `add_data_to_store` validates or wraps the replacement. Any later failure loses the old raster: a `DiskBackedImageData` shape assertion, a factory or validator error, `OSError` (disk full, or ENAMETOOLONG, see IN-05). `test_refused_overwrite_leaves_existing_entry_intact` covers only the containment case.
```
before: True ['range.dat', 'range.meta.json', 'range.npy']
overwrite raised: AssertionError
after:  False ['range.dat']
```
**Fix:** Build the replacement first, then swap it in:
```python
new = self._factory(img_data, enable_caching=..., cache_path=self._get_npy_path(img_name) if self._cache_dir else None, ...)
new = self._check_T(new)
if img_name in self:
    del self[img_name]
self._store[img_name] = new
```
Or route the new container through a temporary key and rename only once construction succeeds. Add a test for a failed overwrite (1-D data).

### WR-08 (pre-existing code, new test claims the boundary): a z_factor that overflows to `inf` passes validation and produces a pack name the grammar rejects

**File:** `src/pc2img/features/rrim.py:144-145, 119-121`; `tests/test_rrim_features.py:228-250`
**Issue:** The widened `_Z_FACTOR_RE` accepts `z1e309`. `float("1e309")` is `inf`, and `inf > 0` passes `_validate_config`. `_format_number(inf)` then emits `zinf`, which the grammar rejects. The request fails late, at dependency re-match, with an error about an option the user never typed. `rrim_pack_(range,z1e999)` is accepted outright with `z_factor=inf`. `z1e-400` underflows to `0.0` and reports "got 0.0" instead of naming the token. The WR-05 test says it extends coverage "to the upper exponent boundary", but it stops at `1e22`.
```
rrim_(range,z1e309)      -> deps ['range', 'rrim_pack_(range,r16,d8,zinf)']
rrim_(range,z1e309)      -> ValueError: Unknown RRIM option 'zinf'. Supported tokens are rN, dN, ...
rrim_pack_(range,z1e999) -> deps ['range']
rrim_(range,z1e-400)     -> ValueError: z_factor must be > 0, got 0.0.
```
**Fix:** Require finiteness in `_validate_config`, and add `z1e309` / `z1e-400` cases to the boundary test:
```python
if not np.isfinite(config.z_factor) or config.z_factor <= 0:
    raise ValueError(f"z_factor must be finite and > 0, got {config.z_factor}.")
```

## Info

### IN-01: `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op` cannot detect a G10 regression

**File:** `tests/test_image_store.py:148-157`
**Issue:** No file exists for `"never-added"`, so the "disk no-op" half holds under any ordering. Under the unlink-before-membership mutation (the original G10 defect), this test passes. Only `test_failed_delete_preserves_codec_pair_and_both_stores` fails:
```
$ MUT=unlink_first pytest -q -p mutplug tests/test_image_store.py      -> 1 failed (test_failed_delete_...), 28 passed
$ MUT=unlink_first pytest -q -p mutplug tests/test_image_store.py -k absent_key -> 1 passed
```
**Fix:** Before the delete, place a `never-added.npy` / `.meta.json` pair on disk (for example, written by a peer store) and assert it survives. Or rename the test so it claims only the `KeyError`.

### IN-02: In the delete tests, the `embedded_traversal` parameter cannot do harm, so its sentinel assertions never decide anything

**File:** `tests/test_image_store.py:271, 275-304, 378-393`
**Issue:** `cache/a` never exists on the setter or delete route, so the kernel fails `cache/a/../../victim.npy` with ENOENT and `unlink(missing_ok=True)` turns that into a no-op. With the guard removed, the only failure is `DID NOT RAISE`. The sentinel is untouchable for this spelling. **Fix:** `(cache_dir / "a").mkdir()` in `_escape_layout`, so the traversal really escapes on every route.

### IN-03: Stale or garbled explanatory comments added this round

**File:** `tests/test_image_store.py:418`; `src/pc2img/image_cache/disk_backed_image_store.py:168-171`
**Issue:** The section header says in the present tense that "`_assert_within_cache_dir` resolves the FULL path". That describes the pre-fix code. The `__delitem__` docstring says "building the paths AFTER the base delegation made a refused delete (… or, historically, a reversed `KeyError` ordering) irreversibly destructive". The G10 history was unlinking *before* the membership check, not building paths after it. **Fix:** Change the header to the past tense ("resolved"). Split the history sentence into two accurate clauses.

### IN-04: Shipped source docstrings cite `.planning/` paths and review IDs that will dangle on `main`

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:24, 45-49, 79, 94-97, 158, 224`; `src/pc2img/features/rrim.py:127`
**Issue:** New text cites `.planning/spikes/000-absorption-test/README.md`, `review-r2-…` / `review-r1-…` IDs, and `D-R4-01`. `main` is stripped of `.planning/`, which is the same reason CLAUDE.md bans planning IDs in commit scopes. This continues an existing pattern (`rrim.py:53` already cites `05-BC-NOTES.md`). **Fix:** Keep the technical reasoning in the docstring and move the provenance IDs to commit bodies or `.planning/`.

### IN-05 (pre-existing): very large z produces a pack name longer than `NAME_MAX`

**File:** `src/pc2img/features/rrim.py:119-120`
**Issue:** The integer branch writes out every digit, so from roughly z ≥ 1e215 the cache filename exceeds 255 bytes, and offload or memmap creation raises `OSError: [Errno 36] File name too long`:
```
226 ok
257 OSError [Errno 36] File name too long
```
This feeds into WR-07, since the `OSError` happens after the overwrite's `del`. **Fix:** Bound z in `_validate_config`, since values anywhere near that are physically meaningless. Or use exponent form above 2**53. That would change the cache key, so treat it as a BC event.

### IN-06: `test_default_config_is_coerced_from_none_sentinel` leaks temp directories and duplicates coverage

**File:** `tests/test_image_store.py:517-527`; `:275-304` vs `:378-393`
**Issue:** Each `DiskBackedImageStore()` with no `cache_path` calls `tempfile.mkdtemp()` and never removes the directory, so every run leaves two directories in `/tmp`. Separately, `test_escaping_key_delete_refuses_…` and `test_refused_delete_leaves_store_membership_intact` now assert the same thing over the same three spellings. **Fix:** Pass a `tmp_path`-backed config where possible, or `shutil.rmtree(store.cache_dir)` in teardown. Merge the two delete tests.

---

_Reviewed: 2026-09-24T15:38:56Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
