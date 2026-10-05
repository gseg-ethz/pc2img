---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-02T12:51:11Z
depth: deep
diff_base: 271b208
files_reviewed: 5
files_reviewed_list:
  - pyproject.toml
  - src/pc2img/image_cache/disk_backed_image_store.py
  - src/pc2img/tiled_generator.py
  - tests/test_image_store.py
  - tests/test_tiled_generator.py
findings:
  critical: 1
  warning: 4
  info: 5
  total: 10
status: issues_found
---

# Phase 7: Code Review Report (gap round 1: 07-12, 07-13, 07-14)

**Reviewed:** 2026-10-02T12:51:11Z
**Depth:** deep
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Scope: `git diff 271b208..HEAD` over the five listed files. I read them together with the upstream
GSEGUtils 0.6.0 sources in `.venv` (`disk_backed_store.py` `purge`, `__getstate__`, `__setstate__` and `__init__`;
`paths.py`; `lazy_disk_cache.py` config defaults) and with the pc2img callers (`features/manager.py`,
`core.py`).

Baseline on HEAD: `pytest` gives 376 passed, and ruff check and format are clean. A green suite only
shows that the existing tests still pass. Every BLOCKER and WARNING below was reproduced by
running code. The scripts are in
`/tmp/claude-1000/-scratch-31-pc2img/8adb4905-a757-44d2-a417-1d0ec8df8e84/scratchpad/gap1/`. Pre-fix
comparisons ran against a scratch copy of `src/` with the two source files reverted to `271b208`, via
`PYTHONPATH`.

**Are the new tests real sensors?** Yes, with one large hole (CR-01).
- `test_overwrite_after_a_drop_route_*` (all 4 routes) and `test_retained_reference_*` fail on the pre-fix
  tree, giving 5 failures.
- `test_adding_a_new_key_from_another_process_is_not_refused` passes on the pre-fix tree. That is by
  design: it guards against the over-broad `suppress(KeyError): purge(...)` that round 1's CR-02 sketch
  proposed, which the upstream pid guard would have turned into a worker failure. Good catch by 07-13.
- `test_tiled_regenerate_on_one_instance_with_two_workers` and
  `test_generate_dispatches_one_tile_per_task_without_pickling_the_generator` fail on the pre-fix tree in 3 out of 3
  runs (`BrokenProcessPool`). The regeneration test passed 8 out of 8 repeat runs on HEAD.

**The known lead (the 07-14 deviation).** The class-docstring sentence "a later `generate()` that has to
overwrite a key in a different worker can fail the same way" **is reproducible** on HEAD. 07-14 could
not reproduce it because it tried tracked keys, which `FeatureManager` skips. The route is the 07-13
presence gate: a requested key that is untracked but has any file on disk (a `del`'d key, or a crash
leftover such as `<key>.dat.tmp`) now reaches `purge` in a non-owner process. See WR-01 and WR-02.
That makes the BC-P2I-030 wording 07-14 wrote ("repeated `generate()` did not trigger it … because
tracked features are not recomputed") wrong in the other direction.

**Main concern:** the round's headline fix (round-1 CR-01) has stopped the crash but does not yet
deliver correct output. The usual way of calling it twice returns rasters that cannot be read
(CR-01 below). The regression test misses this because it never reads an array.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: After a second `generate()` with `n_jobs >= 2`, the results cannot be read once the first call's results are released, and the regression test cannot see it

**File:** `src/pc2img/tiled_generator.py:105-113, 196-205`; `tests/test_tiled_generator.py:92-121`;
`src/pc2img/image_cache/disk_backed_image_store.py:132-140` (docstring claim)

**Issue:** Every pickle round-trip of a tile generator gives an entry for `<cache>/<tile>/<key>.dat`
the same path and its own armed GC finalizer. The round-trips are parent to worker, then worker back
to parent, and they happen on every call. The entries returned by call N
are distinct objects from the ones returned by call N+1 but name the same file. Call N+1's entries read that
file lazily. Suppose call N's results are still referenced while call N+1 runs and are released
afterwards. That is exactly what `result = gen.generate(...)` does when it is rebound. Their finalizers then unlink
`<key>.dat`, and reading call N+1's results raises `FileNotFoundError`. The store entry in
`image_generators[tile]` is broken the same way (`store["range"]` raises). Only the codec pair is
left on disk.

Reproduced. This is the regression test's own scenario with ordinary rebinding, and the array is
actually read (`repro_blocker.py`):

```
result = gen.generate(["range"], n_jobs=n)
result = gen.generate(["range", "gradient_x_range", "hillshade_range_315_45"], n_jobs=n)
np.asarray(result[("tile_00", "range")])

n_jobs=1: read ok, 3 out of 3
n_jobs=2: FileNotFoundError: '<cache>/tile_00/range.dat', 3 out of 3
```

The failure is deterministic and uses the default config (`purge_disk_on_gc=True`,
`automatic_offloading=False`). A 4-call loop (`repro_loop2.py`) fails at the read after call 2 with or without
`gc.collect()`. Isolation (`repro_hold.py`, `repro_drop_only.py`): holding call 1's results, or
dropping them *before* call 2, both read fine. The trigger is "previous results outlive the next call
and are then released". That is the normal lifetime under rebinding.

This was not reachable before the round, because the pre-fix second call died with
`BrokenProcessPool`. The round now advertises the path as working: the class docstring says
"repeated `generate()` calls on one instance with `n_jobs >= 2` are supported". The xfail was turned into
a plain passing test, but that test only asserts `(tile_id, "range") in result`, and its first two
results are never bound. So it can pass while every returned raster is unreadable. The new
`add_image_to_store` step-3 sentence, "so a retained reference to the old entry cannot delete the
replacement's files when it is collected", also does not hold across store copies. A reference retained from
another copy of the store, which is what every tiled result is, does delete them (`repro_finalizer.py` case 2:
an overwrite in `copy.copy(store)`, followed by collecting an entry held from the original, deletes the replacement's
`range.dat`, and the copy's next read raises `FileNotFoundError`).

**Fix:** There are two parts, and the second is upstream.
1. pc2img-local (validated: `repro_mitigation.py` gives 6 out of 6 reads OK at `n_jobs=2`). Parent-side copies that come
   back from workers must not own GC deletion of a path that other copies share. In `generate()`,
   after reassembly, when the work ran in a pool:

   ```python
   for data in result_dict.values():
       data.disable_purge()
   for gen in self.image_generators.values():
       for entry in gen.feature_mgr.cache_store.store.values():
           if entry is not None:
               entry.disable_purge()
   ```

   (The cost is that the `.dat` files in `cache_path` are no longer GC-removed. The codec pair already persists there, and
   `purge`/`rmtree` remain the removal routes. Document this.)
2. Upstream (needs owner approval, separate repo): the `LazyDiskCache` finalizer should unlink only
   the inode it created (record `st_dev`/`st_ino` when it creates the file and compare at finalize time). That
   closes the shared-path ABA hazard for every consumer.
3. Make the regression test a real sensor. Bind each result with rebinding, read every array
   with `np.asarray(...)` after the last call, and add a `del`+`gc.collect()` of the previous result
   before reading. Correct the step-3 sentence to "registered with this store".

## Warnings

### WR-01: The presence-gated purge refuses to regenerate a key that has leftover files when run from a non-owner process; deterministic at `n_jobs=1` after a pooled run and random at `n_jobs=2`

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:17-36, 183`

**Issue:** Upstream `purge` checks the owner pid *before* its existence check. `_has_on_disk_artefact`
sends any untracked key that has any of six files on disk into `purge`. Every tile store
built with `n_jobs >= 2` is owned by a worker pid (WR-01 of round 1, accepted as a documented limit).
So a reused tiled instance now fails whenever a requested feature is untracked but has a file
on disk. Retrying after a worker was killed mid-write, which leaves a `<key>.dat.tmp`, is enough.
Reproduced with `repro_refusal.py` (2 tiles; a pooled first call; then one of the two triggers below and a second call):

| trigger before call 2 | HEAD `n_jobs=1` | HEAD `n_jobs=2` | pre-fix `n_jobs=1` |
|---|---|---|---|
| A: `del store["range"]`, regenerate `range` | `StorePurgeRefusedError` 4/4 | ok 4/4 | ok 4/4 (but CR-02-stale) |
| B: leftover `gradient_x_range.dat.tmp`, request it | `StorePurgeRefusedError` 4/4 | refused 2/4 (whichever worker gets the task) | ok 4/4 |

Row B is a regression the gap fix introduced. Leftover `.npy.tmp`, `.meta.json.tmp`, `.dat.tmp`
or a lone `.meta.json` cannot cause a stale read. The rescan adopts only `*.npy`, and the writers
overwrite the temporary names. Yet including them in the gate turns a harmless leftover into a hard,
random failure. Only two members carry correctness weight: `<key>.npy` (stale adoption, round-1
CR-02) and `<key>.dat` (an armed finalizer of a dropped entry, `test_retained_reference_*`).

**Fix:** Narrow the gate to those two. This was validated on a scratch copy: the image-store and tiled tests still give
121 passed, and row B becomes ok in 8 out of 8 runs at both `n_jobs`:

```python
def _has_on_disk_artefact(cache_dir: Path, key: str) -> bool:
    # Only the artefacts whose survival changes behaviour: a <key>.npy a fresh store adopts, and a
    # <key>.dat an armed finalizer of a dropped entry still points at. Temporary names are overwritten.
    return get_npy_path(cache_dir, key).exists() or get_memmap_path(cache_dir, key).exists()
```

Row A (a `del`'d key with a codec pair) still refuses in a non-owner. That is legitimate, because the stale pair has to
go and this process may not remove it. Document it as such (WR-02).

### WR-02: The new docstrings and the BC-P2I-030 record misdescribe when tiled stores refuse, and one listed workaround fails deterministically

**File:** `src/pc2img/tiled_generator.py:115-125`; `src/pc2img/image_cache/disk_backed_image_store.py:139-140, 153-158`;
`.planning/MIGRATION-v0.11.md` (BC-P2I-030)

**Issue:**
- This is the known lead. The class docstring's "a later `generate()` that has to overwrite a key in a different worker
  can fail the same way" is **true since 07-13**, but the trigger it names is wrong. `FeatureManager`
  never overwrites a tracked key. The real trigger is a requested key that is untracked but has files on disk
  (WR-01 rows A and B). 07-14 removed the clause from the record on the basis of a test that could not reach it.
  BC-P2I-030 now states the opposite of what HEAD does.
- Workaround bullet 1, "run with `n_jobs=1` when the instance will be purged from or overwritten", fails
  in 4 out of 4 runs for an instance that has already run pooled. The parent is not the owner either (WR-01, column 1). The
  bullet holds only for an instance that has never run with `n_jobs != 1`.
- `add_image_to_store`, "A key that is neither tracked nor on disk is never handed to purge, so a
  worker process that did not construct the store can still add new keys", is accurate. But the converse
  is never stated: a worker *cannot* add a key that has leftover files.

**Fix:** Replace the clause with: "a later `generate()` that requests a feature which is untracked but
still has files in the tile directory (dropped with `del`/`pop`/`clear`, or left by a killed worker)
raises `StorePurgeRefusedError` when that tile's task runs in a process other than the store's owner.
With `n_jobs >= 2` this depends on which worker gets the task, and after a pooled run it always happens at
`n_jobs=1`." Change bullet 1 to "use `n_jobs=1` for every call on an instance that will be purged or
overwritten". Re-state BC-P2I-030 to match.

### WR-03: At `n_jobs=1`, `verbose=50` masks every task exception after the first as `AttributeError`

**File:** `src/pc2img/tiled_generator.py:178`

**Issue:** With joblib 1.5.3 and `verbose=50`, the sequential path's `print_progress` raises
`AttributeError: 'Parallel' object has no attribute '_pre_dispatch_amount'` while it handles a task
error. The real exception survives only as `__context__`. Isolated in `repro_joblib.py`: `verbose=0`
gives `ValueError` at both `n_jobs`, while `verbose=50` gives `AttributeError` at `n_jobs=1` only. On the tiled path:
- `repro_mask.py`: a leftover in the *second* tile, then `generate(..., n_jobs=1)`, gives `AttributeError`,
  and `__context__` is `StorePurgeRefusedError`.
- `repro_illegal2.py`: tiles `("ok", "bad/../x")` at `n_jobs=1` give `AttributeError`, not
  `StoreKeyError`. This happens on the pre-fix tree as well.

The line predates this round. But this round's documentation now steers callers to `n_jobs=1` and
promises exception types: "`StorePurgeRefusedError` (a `RuntimeError`)" on the class, and "All of these
surface unwrapped" in `add_image_to_store`. The `PointCloudTile` docstring promises "`StoreKeyError` … unwrapped". In the
recommended mode, none of these can be caught by type unless the failing tile is the first one.

**Fix:** Drop `verbose=50` (use `verbose=0`, and log progress via `logger.debug` if it is wanted), or pin a
joblib version without the defect. Add a test with an illegal id on the *second* tile at `n_jobs=1`
that asserts `StoreKeyError`.

### WR-04: Duplicate tile ids are accepted; they bring back the `#82` race that the new docstring says "this dispatch no longer does" and silently compute one tile with another's generator

**File:** `src/pc2img/tiled_generator.py:110-113, 153, 181, 197-203`

**Issue:** Nothing checks that `tile_id` is unique. With two tiles sharing an id
(`repro_dup_ids.py`):
- The second call hands the **same** generator object to both tasks. Task 0 receives tile A's `tile_pcd` but
  a generator whose `pcd` is tile B's, so tile A's output is computed from tile B's points and the error is silent.
- With a real pool this fails in 6 out of 6 rounds: `FileNotFoundError` on `range.dat.tmp`/`range.npy.tmp`, or
  `BrokenProcessPool`. That is the one-store-unpickled-in-two-processes race the class docstring says this
  dispatch removes.
- `result_dict` and `image_generators` keep only one of the tiles, with no error.

The silent substitution also happened before this round. The claim "this dispatch no longer does that" is new and
holds only when the ids are unique.

**Fix:** Reject duplicates in `__init__`:
```python
ids = [t.tile_id for t in pcd_tiles]
if len(ids) != len(set(ids)):
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    raise ValueError(f"tile ids must be unique; duplicated: {dupes}")
```
Then qualify the docstring with "tile ids are unique (enforced)". Add a test for it.

## Info

### IN-01: `_has_on_disk_artefact` hand-copies upstream's purge set from builders that upstream marks "deliberately unpublished", and four of its six members are untested

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:5-10, 17-36`

**Issue:** `get_memmap_path`, `get_memmap_tmp_path`, `get_npy_tmp_path` and `get_meta_tmp_path` are
described in the `GSEGUtils.lazy_disk_cache` barrel as builders that "stay module-level … and are
deliberately unpublished". `GSEGUtils ~= 0.6.0` allows any 0.6.x patch to move them. The six-name
list duplicates `purge`'s artefact tuple with nothing to keep the two in sync. A mutation that drops
the four temporary and sidecar members still gives 121 passed (scratch copy `narrow/`).
**Fix:** After WR-01's narrowing, one unpublished builder remains (`get_memmap_path`). Add a test that
fails if `paths.STORE_PATH_BUILDERS` changes shape, or ask upstream to publish a presence
predicate (`store.has_artefacts(key)`), which would also remove the hand copy.

### IN-02: TOCTOU between the presence gate and `purge`'s own existence check

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:183-184`

**Issue:** If the files disappear between `_has_on_disk_artefact` and `purge`'s existence check,
`purge` raises `KeyError`. That error escapes `add_image_to_store` and reaches `FeatureManager`, which does not expect
it. CR-01 shows a real deleter: another copy's GC finalizer. I did **not** reproduce the
interleaving itself.
**Fix:** `try: self.purge(img_name) except KeyError: pass`. This is safe because the pid and containment
refusals are not `KeyError`.

### IN-03: The class docstring says "one loky task per tile" and "`n_jobs >= 2`"; joblib batches tiles, and the default is `n_jobs=-1`

**File:** `src/pc2img/tiled_generator.py:107, 115, 169`

**Issue:** joblib's auto-batching was observed during these runs ("Batch computation too fast … Setting
batch_size=2"), so one task can carry several tiles. Each tile's generator is still unpickled once,
so the isolation claim holds, but "one task per tile" is not literally true. The owner limit applies to
any *effective* worker count of 2 or more, which includes the default `-1` on a multi-core machine.
**Fix:** Write "one `_process_tile` call per tile" and "whenever the work runs in a worker pool (any
`n_jobs` other than 1, including the default `-1`)".

### IN-04: In `[tool.uv.sources]`, the NOTE still gives a reason the new comment above it withdraws

**File:** `pyproject.toml:136-140`

**Issue:** The NOTE ends with "…which is why only those names keep an index binding". The 07-14
comment directly above it says the bindings have no effect. Keeping configuration that does nothing is a
deliberate choice (round-1 WR-04 offered "delete or make effective"). The leftover rationale reads as if the
bindings still matter.
**Fix:** Drop the trailing clause, or reword it to "those are the names the (inert) bindings below
would cover".

### IN-05: Found during review, predates this round: `automatic_offloading=True` breaks the tiled path on the first call

**File:** `src/pc2img/tiled_generator.py` (via `DiskBackedImageData`)

**Issue:** `LazyDiskCacheConfig(enable_caching=True, automatic_offloading=True, cache_path=...)` with
`n_jobs=2` fails on the **first** `generate()` with
`AttributeError: 'DiskBackedImageData' object has no attribute '_data'`. The pre-fix tree fails identically
(`repro_loop2.py 1 0 2`), so this round did not introduce it. Recorded so it gets routed to the
backlog rather than lost.
**Fix:** Route it to Phase 7 follow-up or the backlog; it needs its own investigation.

## Checked and clean

- **Results and state reassembly, and bookkeeping.** `image_generators[tile_id]` is replaced by the
  returned copy at `n_jobs >= 2` and is the same object at `n_jobs=1`. `n_jobs=1` and `n_jobs=2` give
  identical rasters (`repro_parity.py`, `equal_nan` compare over three features, delaunay with an
  interpolation cache config).
- **Cache-path extension only when building.** Each tile gets its own `interp/<tile_id>` and
  `img/<tile_id>` at both `n_jobs`. The parent's `interp_kwargs["lazy_disk_cache_config"]` is not mutated,
  thanks to the new `dict(interp_kwargs)` copy. The behaviour matches the pre-fix code (the extended config
  was only ever used when building).
- **Illegal ids with a single tile.** These give an unwrapped `StoreKeyError` at both `n_jobs` and on both trees. The
  multi-tile `n_jobs=1` case is WR-03.
- **Pickling surface.** A task payload carries `_process_tile` by reference, the tile's own generator or
  `None`, classes by reference, plain dicts, a frozen config and an `ImgRes`. The recorder test's
  `other.encode() not in payload` check would catch a leak of the generator dict or another tile.
- **Symlinks in the gate.** `Path.exists()` follows links exactly as `purge`'s own existence check
  does, so a dangling link is "absent" to both. A link that points outside the cache now reaches `purge` and is
  refused with `StorePurgeForeignArtefactError` instead of being left for a fresh store to adopt, which is the correct
  fail-closed direction.
- **The default cache directory.** It is a per-store `mkdtemp`, so the gate cannot reach another store's
  default directory.
- **The fork test.** No warnings about forking a multi-threaded process in a full run (`-W always::DeprecationWarning`).

---

_Reviewed: 2026-10-02T12:51:11Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
