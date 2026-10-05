---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-02T14:38:54Z
depth: deep
diff_base: 7094dde
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
  info: 3
  total: 8
status: issues_found
---

# Phase 7: Code Review Report (gap round 2: 07-16, 07-17, 07-18; review round 3 of 3)

**Reviewed:** 2026-10-02T14:38:54Z
**Depth:** deep
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Scope: `git diff 7094dde..HEAD` over the five listed files. I read them together with the upstream
GSEGUtils 0.6.0 sources in `.venv` (`LazyDiskCache.__getstate__`/`__setstate__`/`disable_purge`/`_init_from_config`;
`DiskBackedStore.__init__`/`purge`/`offload`/`_store_entry`/`_load_entry`/`__getstate__`/`__setstate__`), with
`features/manager.py`, and with BC-P2I-027/028/030 plus the inline verifier in `.planning/MIGRATION-v0.11.md`.

Baseline on HEAD: `pytest` gives 387 passed. That is evidence only that the existing tests still pass.
Every BLOCKER and WARNING below was reproduced by running code, and every one of them reads arrays.
The scripts are in `/tmp/claude-1000/-scratch-31-pc2img/8adb4905-a757-44d2-a417-1d0ec8df8e84/scratchpad/gap2/`.
I made the comparisons with the pre-round tree by extracting `7094dde:src` into `gap2/base/src` and running it via `PYTHONPATH`.
I validated the fixes the same way, on scratch copies (`gap2/fix`, `gap2/fixd`, `gap2/fixf`).

**Main concern:** the round's headline fix (round-2 CR-01) is incomplete. It disarms only the entries that
come back from a pooled call. An entry created by an `n_jobs=1` call stays armed, and the next pooled call
gives the parent a second entry object on the same `<key>.dat` file. Releasing the `n_jobs=1` results then
unlinks the files that the pooled results and the stores read. The suite only ever runs one `n_jobs` value
per instance, so it cannot see this. One of its tests even pins the armed flag that causes it (CR-01).

**The leads:**
- **(a) Persistence claims.** Confirmed. The class docstring overstates what persists in the default
  configuration, and it frames a baseline behaviour as the price of the fix (IN-01). MIGRATION 030
  is accurate on this point. The two documents disagree.
- **(b) Mutation c2 and `drop_route[popitem]`.** Explained and reproduced. `popitem()` reads the key, and
  `_load_entry` rewrites `<key>.dat` while doing so. The test then keeps the popped entry bound to `_`, so
  `range.dat` is on disk and the *soft* gate's `.dat` leg catches the key. The `.npy` gate does not. If the
  popped value is discarded, the c2 mutant serves the stale raster to a fresh store (WR-04).
- **(c) Released or reassembled results deleting newer files.** Found: mixed `n_jobs` sequences (CR-01),
  and a `del` between calls (WR-02). Pooled-only sequences (`2,2,2`) and pooled-then-sequential sequences
  (`2,2,1`) are clean.
- **(d) The soft gate.** It cannot make a stale raster servable. Only `<key>.npy` is adopted, and the
  soft set never includes it. It *does* swallow an aliased-artefact refusal in a non-owner process, and
  the write that follows lands in another key's memmap. This is a regression against `7094dde` (WR-01).
- **(e) Parity and reassembly.** Clean. See "Checked and clean".

Carried and not re-raised (already dispositioned): round-2 WR-03 (`verbose=50` masks the exceptions of
later tiles at `n_jobs=1`) is still on line 213, and the new sensor test works around it by placing its
trigger in `tile_00`. Round-2 IN-02 (TOCTOU, `KeyError` from `purge`) is unchanged.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Any `n_jobs=1` call followed by a pooled call (including the default `n_jobs=-1`) leaves the pooled results unreadable and the tile stores unrecoverable once the earlier results are released

**File:** `src/pc2img/tiled_generator.py:240-241` (the `if n_jobs != 1:` guard), `:119-129` and
`:202-208` (docstrings); `tests/test_tiled_generator.py:159-202` (`test_pooled_results_do_not_own_gc_deletion`
pins the armed `n_jobs=1` flag); `.planning/MIGRATION-v0.11.md` BC-P2I-030 ("every returned raster stays
readable after earlier results are released"; "`n_jobs=1` results are the stores' own entries and are
unchanged").

**Issue:** At `n_jobs=1` the work runs in-process. New entries are created with the default
`purge_disk_on_gc=True`, and `_release_gc_ownership` is skipped, so the caller's results R1 are armed entries
(the stores' own objects). The next pooled call pickles each tile store. `DiskBackedStore.__getstate__` →
`offload(pickle_container=True)` writes the codec pair and sets the mapping value to `None`, but R1's entry
objects stay alive and armed. The worker's `_load_entry` and the parent's `__setstate__` rebuild
`<key>.dat` at the same path. The pooled results R2 are disarmed, but R1 never is. On the ordinary rebinding
`result = gen.generate(...)`, R1 is collected after call 2 returns, and its finalizers unlink the `.dat` files
that R2 and the new stores use. Reproduced with `repro_mixed3.py` and `repro_mixed2.py`. The behaviour is deterministic:

```
1:r 2:r           call 1 (n_jobs=2) read: FileNotFoundError '<cache>/tile_00/range.dat'   3 of 3 runs
1:r -1:r          call 1 (n_jobs=-1, the default) read: FileNotFoundError                 1 of 1
2:r 1:a 2:a       call 2 (n_jobs=2) read: FileNotFoundError                               3 of 3
                  (pooled, then the n_jobs=1 workaround adds features, then pooled again)
1,2 / 1:r 2:r     store.offload() then read every store entry: FileNotFoundError; no .dat left on disk
2,2,2 / 2,2,1 / 1,1,1   all reads ok (the round's own scenarios)
```

The store entries look healthy at first, because their memmaps are already open on the unlinked inode.
The damage shows on the first entry-level `offload()` and reload, which is the default
`pickle_container=False` route, and every `.dat` in the tile directory is gone. The same scenario fails on
`7094dde`, so this is the round-2 CR-01 defect class surviving its fix, not a new mechanism. The round's
text now states the opposite: "releasing one call's results never deletes a `.dat` memmap that a later
call's results read", and "`n_jobs=1` keeps the single-object behaviour". Mixing calls is not exotic. Any debug
call at `n_jobs=1` followed by the default `-1` reaches it, and so does the class docstring's own route of
using `n_jobs=1` to work around refusals after a pooled run.

**Fix:** Disarm on every call, not only pooled ones. Validated on `gap2/fix`: all three failing sequences
read OK, `repro_offloaded_holder.py` reads OK, and the image-store and tiled tests pass apart from the one
test that pins the old flag:

```python
        result_dict.update(tile_dict)

    # Every call, not only pooled ones: an entry created at n_jobs=1 is otherwise still armed
    # when a later pooled call pickles its store and rebuilds the same <key>.dat in another object.
    _release_gc_ownership(result_dict, self.image_generators)
    return result_dict
```

I tested and rejected a narrower variant that disarms the live store entries before dispatch when
`n_jobs != 1` (`gap2/fixb`). It misses an `n_jobs=1` result whose store entry the caller
codec-offloaded, which leaves the mapping slot `None`, and that scenario still fails
(`repro_offloaded_holder.py`: FileNotFoundError). The cost of the fix: `.dat` files also persist after `n_jobs=1`-only runs, so
drop the "`n_jobs=1` keeps the single-object behaviour / purge route" sentences and BC-P2I-030's
"unchanged" clause. Flip the sequential half of `test_pooled_results_do_not_own_gc_deletion` to
`False`. Add a sensor, parametrized over `(1, 2)`, `(1, -1)` and `(2, 1, 2)` with new features on the
`n_jobs=1` call. The sensor rebinds `result`, runs `gc.collect()`, reads every raster, then calls `store.offload()`
and reads every store entry.

## Warnings

### WR-01: In a non-owner process the soft gate swallows an aliased-artefact refusal, and the replacement is written through the link into another key's memmap

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:210-215`; docstring `:151-152` ("Refusals
for a foreign or aliased artefact still surface"); BC-P2I-027 (same sentence)

**Issue:** Upstream `purge` checks process identity before it reconciles artefacts. In a process that did
not construct the store, every soft-gate purge therefore raises the exact `StorePurgeRefusedError`, which
the soft gate tolerates. The foreign and aliased checks never run. `add_data_to_store` then writes `<key>.dat`
through a final-component symlink whose target is inside the cache, because upstream's write containment
only refuses targets outside it. Reproduced with `repro_alias_corrupt.py`: the owner tracks `other`
(zeros), `k.dat -> other.dat` is planted, and a forked child calls `add_image_to_store("k", 7.0)`:

```
HEAD:     owner: StorePurgeAliasedArtefactError | non-owner exit 0 | owner reads 'other': 7.0 (was 0.0)
7094dde:  owner: StorePurgeAliasedArtefactError | non-owner StorePurgeRefusedError | 'other': 0.0
```

`repro_soft_foreign.py` shows that the foreign variants surface in a non-owner only as
`StoreContainmentError` from the write route (lone `.dat`), or not at all (lone `.meta.json`), never as the
documented `StorePurgeForeignArtefactError`. Reaching this needs a link planted in the cache directory,
which is narrower than an ordinary pipeline run. But the sentence is false in exactly the processes where
the tolerance applies, and the consequence is the silent cross-key overwrite that upstream's aliased refusal
exists to prevent.

**Fix:** Do not tolerate the refusal when a soft artefact is a link. Validated on `gap2/fixd`: the child is
refused, `other` stays 0.0, and the image-store and tiled tests give 132 passed:

```python
            except StorePurgeRefusedError as exc:
                if type(exc) is not StorePurgeRefusedError or any(
                    p.is_symlink()
                    for p in (get_meta_path(self.cache_dir, img_name), get_memmap_path(self.cache_dir, img_name))
                ):
                    raise
```

Then change the docstring and 027 to say that in a non-owner process a linked leftover is refused with
`StorePurgeRefusedError`.

### WR-02: The "non-owner caveat" can be reached through `TiledPointCloudImageGenerator.generate()`; "`generate()` cannot reach this" is false

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:195-201`; BC-P2I-027 ("unreachable from
pc2img's own pipeline, which never drops entries")

**Issue:** The tiled class docstring itself names `del` on a tile store as a route, and after a pooled run
the parent is a non-owner. Reproduced with `repro_caveat_tiled.py` on 2 tiles:
1. a pooled call;
2. `held = gen.generate(["gradient_x_range"], n_jobs=1)`, which gives an armed entry with only its `.dat` on disk;
3. `del store["gradient_x_range"]`;
4. a regenerate at `n_jobs=1`, where the soft gate tolerates the refusal;
5. `del held; gc.collect()`.

After step 5 the replacement `.dat` is gone, and `store.offload("gradient_x_range")` followed by a read
raises `FileNotFoundError`. The entry that does the damage is an `n_jobs=1` entry that was never disarmed, which is the CR-01 mechanism.

**Fix:** The CR-01 fix closes it. Validated on `gap2/fix`: the `.dat` survives and the read is OK. Then
remove or re-word the "never drops entries / `generate()` cannot reach this" sentences in the docstring and in 027.

### WR-03: A pooled call in which one tile fails poisons the retry for every tile that succeeded, and the documented `n_jobs=1` route does not help

**File:** `src/pc2img/tiled_generator.py:211-229` (no failure handling), `:136-148` (trigger list and
workarounds); BC-P2I-030

**Issue:** A tile that finished pickles its result in its worker, and that pickling writes the codec pair into the tile
directory. If another tile then fails, `Parallel` raises, and the parent keeps its *previous* store copies,
which do not track the new keys. The next `generate()` that asks for such a key reaches the hard gate (an
untracked key with `<key>.npy` on disk) in a process that is not the owner. Reproduced with
`repro_failed_call4.py`: 4 tiles, the last of which lacks the `intensity` scalar field. The sequence is
`["range"]`, then `["gradient_x_range", "intensity"]`, which fails, then `["gradient_x_range"]`:

```
tile_00/01/02: gradient_x_range tracked False, .npy on disk True
call 3 n_jobs=1: StorePurgeRefusedError   (2 of 2)
call 3 n_jobs=2: StorePurgeRefusedError   (1 of 1)
```

This has been present since the 07-13 gate (the six-member gate refuses the same way). It is reported here
because this round's docstring and 030 list the triggers as "dropped with `del`, `pop`, `popitem` or `clear`"
and offer `n_jobs=1` as the way round. A partially failed batch is the ordinary trigger, and the `n_jobs=1` route fails
on it every time.

**Fix:** On any exception from a pooled dispatch, drop the parent's tile generators. The next call then
rebuilds each store in a worker, and the construction rescan adopts the on-disk codec pairs as tracked keys.
Validated on `gap2/fixf`: call 3 is OK and reads OK at both `n_jobs`.

```python
        try:
            with parallel_config(...):
                results = Parallel()(...)
        except BaseException:
            if n_jobs != 1:
                self.image_generators.clear()
            raise
```

Add the failed-batch route to the docstring and 030, and add a test that injects a failure in one tile.

### WR-04: `test_overwrite_after_a_drop_route_...[popitem]` does not sense the `.npy` gate; it passes because of the popped value it keeps (lead b)

**File:** `tests/test_image_store.py:162-164`

**Issue:** `popped_key, _ = store.popitem()` reads the offloaded key, and `_load_entry` constructs an entry
that rewrites `range.dat`. Binding the value to `_` keeps that entry alive, so a `.dat` is on disk at the
overwrite. The soft gate's `.dat` leg then purges the stale pair even when `.npy` is removed from the hard
predicate. Reproduced with `repro_popitem.py` on the 07-17 c2 mutant (`gap2/c2`):

```
c2 retain  -> files after popitem [range.dat, range.meta.json, range.npy]; fresh store serves None (correct)
c2 discard -> files after popitem [range.meta.json, range.npy];            fresh store serves 1.0 (STALE)
HEAD discard -> fresh store serves None
```

So 07-17's open question is answered. `popitem` is protected by the soft gate's `.dat` leg, and only while the
caller holds the popped entry. With the value discarded, the parametrization would be a real sensor for the hard gate.

**Fix:** Use `store.popitem()` without binding, then `gc.collect()`. Assert that `get_memmap_path(...)` does
not exist before the overwrite, in all four routes, so that every route exercises the `.npy` gate alone.

## Info

### IN-01: The class docstring overstates persistence in the default configuration, and the path it gives is wrong for the default directory (lead a)

**File:** `src/pc2img/tiled_generator.py:122-127`

**Issue:** Measured with `repro_persist.py`, `TMPDIR` set to a fresh directory, and two calls:

| config | HEAD n_jobs=1 | HEAD n_jobs=2 | 7094dde n_jobs=1 | 7094dde n_jobs=2 |
|---|---|---|---|---|
| default (`enable_caching=False`) | 2 empty dirs | 2 empty dirs | 2 empty dirs | 2 empty dirs |
| `enable_caching=True`, no `cache_path` | 2 empty dirs | 2 dirs, 18 files | 2 empty dirs | FileNotFoundError (round-2 CR-01) |

In the default configuration nothing is written, and the empty `mkdtemp` directories persisted before this round and also at
`n_jobs=1`. They are not part of "the price". Without a `cache_path` the files land in
`<mkdtemp>/<key>.dat`, not in `<tile_id>/<key>.dat`. MIGRATION 030 states this correctly, so the
docstring and the record now disagree.
**Fix:** Copy 030's qualifier into the docstring: "when caching is enabled without a `cache_path` … (with the
default `enable_caching=False` a pooled run writes no files)". Name the path as `<store dir>/<key>.dat`.

### IN-02: The new BC-P2I-027 verifier probe "re-add over a lone memmap" does not sense the gate

**File:** `.planning/MIGRATION-v0.11.md:698-713`

**Issue:** The extracted verifier prints `[ok] verified 30 entries` with the soft branch deleted
(`gap2/nosoft`). Its 027 probes also pass on `7094dde`, where only the 028 duplicate-id probe fails.
A replacement served over a lone `.dat` holds without any gate. The "mutation" 07-18 cites flipped the
probe's expected value; it did not change the code.
**Fix:** Either mark the probe as documenting behaviour, or make it observe the detach. To observe the
detach, hold a reference to a dropped entry, re-add, collect the reference, and assert that the replacement
`.dat` still exists. That is the `test_retained_reference_*` shape.

### IN-03: The uniqueness check compares exact strings

**File:** `src/pc2img/tiled_generator.py:176-179`

**Issue:** `"Tile"` and `"tile"` both pass `is_valid_store_key` and the new check. On a case-insensitive
filesystem (the macOS default, NTFS) they name the same cache sub-directory, and the
one-directory-two-stores hazards of round-2 WR-04 return. **Not reproduced**: this environment's scratch
filesystems are case-sensitive, and I did not write outside the scratchpad. Separately, `self.pcd_tiles` is a public
mutable attribute, so a caller can append a duplicate after construction.
**Fix:** Compare `casefold()` and NFC-normalised ids (or document the rule), and store `tuple(pcd_tiles)`.

## Checked and clean

- **Parity and per-tile reassembly (lead e).** `repro_parity.py` covers 4 tiles, 3 features, the linear
  interpolation, and delaunay with an interpolation cache config, over the sequences `2,2,2` and `2,2`. In each case
  `n_jobs=1` equals `n_jobs=2` (`equal_nan`), and every tile equals a standalone
  `PointCloudImageGenerator` on that tile alone. The key sets match. The duplicate-id check runs before
  any attribute is assigned and does not disturb reassembly.
- **The soft gate cannot make a stale raster servable (lead d, first half).** The startup scan adopts only
  `*.npy`. The soft set is `.meta.json`/`.dat`. A torn codec write leaves either `.npy` (hard gate) or only `.tmp` names,
  which nothing adopts. The owner process surfaces foreign and aliased refusals as documented (`repro_soft_foreign.py`).
- **Tolerating by exact type.** `type(exc) is StorePurgeRefusedError` matches only upstream's pid refusal at
  line 1699. The foreign and aliased refusals are subclasses and propagate in the owner process.
- **Pooled-only and pooled-then-sequential sequences** (`2,2,2`, `2,2,1`, `2,1,2` with no new features on the
  `n_jobs=1` call). All rasters and store entries read, including after `store.offload()`.
- **`pyproject.toml`.** Comment-only change. It no longer gives the inert bindings a purpose.

---

_Reviewed: 2026-10-02T14:38:54Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
