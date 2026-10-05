---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-05T09:35:54Z
depth: deep
diff_base: c1b813d
files_reviewed: 4
files_reviewed_list:
  - src/pc2img/image_cache/disk_backed_image_store.py
  - src/pc2img/tiled_generator.py
  - tests/test_image_store.py
  - tests/test_tiled_generator.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 7: Code Review Report (gap round 3: 07-19, 07-20, 07-21; review round 4, beyond the cap by owner decision)

**Reviewed:** 2026-10-05T09:35:54Z
**Depth:** deep
**Files Reviewed:** 4
**Status:** issues_found

## Summary

**Scope.** `git diff c1b813d..HEAD` over the four listed files. I read it together with:
- the upstream GSEGUtils 0.6 sources in `.venv`: `LazyDiskCache._init_from_config`, `_convert_to_memmap`, `disable_purge`, `__getstate__`/`__setstate__`, and `DiskBackedStore.purge`, `_reconcile_artefact_targets`, `_store_entry`, `_load_entry`, `__getstate__`/`__setstate__`;
- `paths._assert_write_contained`;
- `features/manager.py`, `core.py` and `strategies/interpolation.py`;
- BC-P2I-027/028/030 and the inline verifier in `.planning/MIGRATION-v0.11.md`.

**Baseline.** `pytest` gives 403 passed on HEAD. That only shows the existing tests still pass.

**Method.** Every WARNING below was reproduced by running code, and the scripts are in `/tmp/claude-1000/-scratch-31-pc2img/8adb4905-a757-44d2-a417-1d0ec8df8e84/scratchpad/gap3/`.
- Pre-round comparisons ran against `c1b813d:src`, extracted to `gap3/base/src` and run via `PYTHONPATH`.
- Fixes were validated on scratch copies: `gap3/fix` for WR-01 and `gap3/fixlink` for WR-02. On each, the image-store and tiled tests give 148 passed.
- No tracked file other than this review was modified (`git status --porcelain -- src tests` is empty).

**Headline: no BLOCKER survives.** The round's three mechanisms do what they claim on their main paths:
- **Always-disarm.** Delaunay with its own triangulation cache over the mixed sequences `1,2,1,2` and `2,1,2` reads every raster and every store entry after `store.offload()` (2 of 2 runs).
- **Pooled-failure reset.** Results held from an earlier call stay readable across a failed pooled call and its retry, at `2/2/1`, `2/2/2` and `1/2/1`.
- **Pre-write link refusal.** It closes the round-3 in-cache aliasing. A relative `k.dat.tmp -> other.dat` corrupted `other` on `c1b813d` and is now refused.
- **027 verifier probe.** I re-extracted it. It returns `None` on HEAD and returns `BC-P2I-027: collecting a dropped entry deleted the replacement's memmap` with the soft branch deleted from a scratch copy, so the 07-21 claim reproduces.

**The defects are at the edges of each mechanism.**
- **WR-01.** The failure path skips the disarm. After a failed `n_jobs=1` call, the kept stores hold armed entries, which the docstring says cannot happen. A held store entry then deletes the `.dat` that the next pooled call's results read. The same route reaches the "non-owner caveat" through the tiled generator, which the round's docstring and BC-P2I-027 now say is impossible.
- **WR-02.** The link refusal is classified by *location*, while upstream classifies by *name*. It refuses upstream's documented legitimate adopted `<key>.dat` and a dangling `<key>.dat`. Both were accepted before this round, and for the dangling shape no API call can clear it.
- **WR-03.** The failed-batch claim "adopts those codec pairs" is false without a `cache_path`.
- **WR-04.** Always-disarm is written into the `.meta.json` sidecars, so a later non-tiled store over the same directory inherits it.

**Answers to the specific questions:**
- **Does always-disarm change any non-tiled behaviour?** Not directly, because `_release_gc_ownership` is private to the tiled path. It does leak into later non-tiled stores through the sidecars (WR-04).
- **Can the link refusal fire on legitimate entries?** Yes, on an adopted `.dat` and on a dangling `.dat` (WR-02). It does not fire on a symlinked cache directory (measured: accepted). Relative links are classified correctly (measured).
- **Is a failure in the parent after a successful `Parallel` return handled?** Unpickling the results happens inside `Parallel()`, so the reset covers it. After the return, only the reassembly loop and `disable_purge()` run, and I found no realistic failure there. The unhandled failure path is the sequential one (WR-01).
- **Is anything in the docstrings or MIGRATION not reproduced?** Yes: WR-01, WR-03 and IN-02.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: A failed `n_jobs=1` call leaves armed entries in the kept stores, which re-opens the deleted-`.dat` defect class and the non-owner caveat through the tiled generator

**File:** `src/pc2img/tiled_generator.py:241-250` (the exception path skips `_release_gc_ownership`, which sits at `:261`);
claims at `:119-121` ("the entries of the stores kept in `image_generators` have purge-on-garbage-collection
disabled") and `:212-213`; `src/pc2img/image_cache/disk_backed_image_store.py:274-280` ("Results obtained
through `TiledPointCloudImageGenerator.generate()` do not reach it"); the same sentence in BC-P2I-027 and the
persistence clause of BC-P2I-030.

**Issue:** At `n_jobs=1` the handler keeps the generators, as designed, because the stores were updated in
place. `_release_gc_ownership` runs only after a successful return. So every entry that the failing call added
to a kept store keeps the default `purge_disk_on_gc=True`. Measured in `repro_failed_seq_armed.py` (two tiles,
`tile_01` lacks `intensity`; call 1 is `["range"]` at `n_jobs=1`, call 2 is
`["gradient_x_range", "scalar_field_intensity"]` at `n_jobs=1` and fails):

```
tile_00 store purge_disk_on_gc after the failed call: {'range': False, 'scalar_field_intensity': True, 'gradient_x_range': True}
hold store entry=True,  next n_jobs=2: gradient_x_range.dat exists=False
    unreadable after offload+read: [('tile_00','gradient_x_range','FileNotFoundError'), ('store tile_00','gradient_x_range','FileNotFoundError')]
hold store entry=False, next n_jobs=2: clean
hold store entry=True,  next n_jobs=1: clean
```

It failed in 2 of 2 runs and is deterministic. The mechanism is round-2 CR-01, reached through the failure path:
1. The next pooled call pickles the store, so its mapping slot becomes `None`, while the held entry stays alive and armed.
2. The worker and the parent rebuild `<key>.dat` under new objects.
3. Releasing the held entry unlinks the file that the pooled results and the store read.

The same armed entry also reaches the non-owner caveat through the tiled generator (`repro_caveat_via_failed_seq.py`). The sequence is:
1. a pooled call, after which the parent is a non-owner;
2. a failing `n_jobs=1` call;
3. `held = store["gradient_x_range"]` and `del store["gradient_x_range"]`;
4. a regenerate at `n_jobs=1`, where the soft gate tolerates the refusal;
5. `del held; gc.collect()`.

Output: `held purge_disk_on_gc: True`, `replacement .dat exists after releasing the held entry: False`, then
`offload+read raised FileNotFoundError`. That is the "route that did" from the caveat paragraph, and both
the docstring and 027 now say it is closed.

Triggering it requires holding an entry taken from `image_generators[...].feature_mgr.cache_store`, not a returned result. That narrows it, so it is not a blocker. But the class docstring guarantees exactly that those entries are disarmed, and `test_a_failing_sequential_call_keeps_the_tile_generators` pins the identity of the kept generators without checking the flag.

**Fix:** Disarm the kept stores on the sequential failure path. Validated on `gap3/fix`: both repros come out clean, all three flags read `False`, and 148 tests pass.

```python
        except BaseException:
            if n_jobs != 1:
                self.image_generators.clear()
            else:
                # The stores were updated in place; disarm what the failing call added to them.
                _release_gc_ownership({}, self.image_generators)
            raise
```

Then extend `test_a_failing_sequential_call_keeps_the_tile_generators` to assert that `purge_disk_on_gc is False` on
every non-`None` store entry after the failure.

### WR-02: The pre-write link refusal rejects upstream's legitimate adopted `<key>.dat` and a dangling `<key>.dat` (both accepted on `c1b813d`) with a misleading "aliased" error

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:74-88` (classification by location at `:80`);
docstring `:56-63` and `:65-68`; BC-P2I-027 ("`StorePurgeAliasedArtefactError` (the link resolves inside the cache
directory, i.e. to another key's artefact)").

**Issue:** Upstream treats `<key>.dat` as a symlink to a real payload inside the cache directory. It calls this the
legitimate *adopted entry* (D-17/STORE-03):
- `_convert_to_memmap` deliberately writes through it (`final_path = self._cache_path.resolve()`);
- `purge` removes both the link and its payload (D-15-G2a);
- `purge` classifies "aliased" by the target's *name*: a target that carries another key's store-artefact suffix (D-15-G7).

Upstream's own `StorePurgeAliasedArtefactError` message tells the user to "RENAME THE PAYLOAD TO AN EXTENSION
THIS STORE DOES NOT BUILD — .bin". pc2img raises the same class for *any* in-cache target, `.bin` included, so
following upstream's remedy for this exception does not help. Measured in `repro_link_shapes.py` (owner process):

```
shape                     HEAD                                      c1b813d
k.dat -> payload.bin      StorePurgeAliasedArtefactError            accepted; k reads 1.0 (link and payload purged)
same, k tracked           StorePurgeAliasedArtefactError            accepted; k reads 1.0
k.dat -> gone.bin         StorePurgeAliasedArtefactError            accepted; k reads 1.0
(dangling)
k.dat.tmp -> other.dat    StorePurgeAliasedArtefactError (correct)  accepted, other overwritten (the round-3 defect)
symlinked cache dir       accepted                                  accepted
```

The message claims that "another artefact inside the cache directory" would be overwritten. For the adopted
shape the target is the key's own payload, and for the dangling shape it does not exist. For the adopted shape,
`purge("k")` followed by the add works. For the dangling shape there is no API way out: `purge("k")` raises `KeyError`
(a dangling link does not `exists()`, so an untracked key counts as absent), and the add is then refused again
(`dangling purge raised KeyError 'k'` / `add after purge raised StorePurgeAliasedArtefactError`). Through
`generate()` that feature then fails for the tile on every call until someone runs `unlink` by hand. A dangling `.dat` is
reachable without a hostile plant: upstream's documented "two keys, one payload" limit leaves one when the other key is purged.

The temporary names (`.dat.tmp`, `.npy.tmp`, `.meta.json.tmp`) are correctly refused whatever their target,
because `np.memmap(w+)` and `open(..., "wb")` truncate through them. Only the `<key>.dat` final has adopted-entry semantics.

**Fix:** For `<key>.dat` only, mirror upstream's discrimination by refusing an in-cache target only when its name is
a store artefact name. Validated on `gap3/fixlink`:
- the adopted and dangling shapes behave as on `c1b813d`;
- `k.dat -> other.dat` and every temporary-name link are still refused;
- 148 tests pass.

```python
        target = link.resolve()
        if (
            build is get_memmap_path
            and target.is_relative_to(resolved_cache_dir)
            and not target.name.endswith((".npy", ".meta.json", ".dat", ".tmp", ".pkl"))
        ):
            continue  # upstream's adopted <key>.dat payload (STORE-03); purge reconciles it
```

The suffix tuple hand-copies upstream's private `paths._store_artefact_suffix`. Pin it with a drift test the way
`test_presence_gate_uses_only_upstream_builders_of_known_shape` pins the builders. In a non-owner process the soft
branch's `_leftover_is_linked` re-raise still refuses the adopted shape, which is the intended round-3 behaviour.
Then reword the docstring and 027: "inside the cache directory **and named like a store artefact**".

### WR-03: "The next call … adopts those codec pairs" is false without a `cache_path`; the retry recomputes everything in fresh `mkdtemp` directories and orphans the old ones

**File:** `src/pc2img/tiled_generator.py:153-156` and `:241-250`; BC-P2I-030 "Failed batch" ("adopts the codec pairs the finished tiles wrote").

**Issue:** With `enable_caching=True` and no `cache_path`, each tile store's directory is a `tempfile.mkdtemp()`
created at construction. Dropping the generators makes the next call build new stores in *new* temporary directories.
Nothing is adopted, so every feature is recomputed, including those from earlier successful calls. The old directories
keep their full raster sets and nothing ever removes them. Measured with `repro_nocachepath_retry.py` (TMPDIR isolated):

```
store dirs after call 1: {'tile_00': 'tmp8r7k7ah7', 'tile_01': 'tmphnzsbsri', 'tile_02': 'tmpsf40iha3'}
failing call raised IndexError
store dirs after retry:  {'tile_00': 'tmpzobuedm6', 'tile_01': 'tmpgfjuf02h', 'tile_02': 'tmpcrld0mqz'}
  tile_00: old dir files ['gradient_x_range.meta.json', 'gradient_x_range.npy', 'range.dat', 'range.meta.json', 'range.npy', ...]
```

So every failed pooled batch leaks one directory of rasters per tile. The retry is not refused, so the functional
half of the claim holds, but the adoption half and its "nothing is lost" reading do not. With the default
`enable_caching=False`, the reset has no hazard to address, because nothing is on disk and no gate can fire. It still
discards every tile's in-memory rasters from earlier calls. That point is about cost and is noted only for the wording.

**Fix:** At minimum, qualify the docstring and 030: "with a `cache_path` the next call adopts the codec pairs the
finished tiles wrote; without one the retry rebuilds each store in a new temporary directory, recomputes every
feature, and leaves the previous directories (and their files) behind". Optionally, skip the reset when
`not self._lazy_disk_cache_config.enable_caching`, where it protects nothing.

### WR-04: Always-disarm is persisted into the `.meta.json` sidecars and inherited by later non-tiled stores over the same directory (undocumented; widened by this round)

**File:** `src/pc2img/tiled_generator.py:266-284` (`disable_purge()` flips the entry's persisted intent); BC-P2I-030
"Disk persistence".

**Issue:** `disable_purge()` sets the entry's `_purge_disk_on_gc = False`. The next codec write (`_store_entry`,
run by every pooled pickling) records `"purge_disk_on_gc": false` in `<key>.meta.json`. Upstream's `_load_entry`
reconstructs adopted entries from that sidecar, and the sidecar overrides the opening store's config. So a later
`DiskBackedImageStore` or a plain `PointCloudImageGenerator` opened over `<cache_path>/<tile_id>` inherits the
tiled run's disarm. Measured with `repro_meta_flag.py`:

```
seq      HEAD sidecar / fresh store / fresh PointCloudImageGenerator     c1b813d
(2,)     True / True / True                                              True / True / True
(1, 2)   False / False / False                                           True / True / True
(2, 2)   False / False / False                                           False / False / False
```

For `2,2` this was already true before this round. The round extends it to any sequence with a sequential call
before a pooled one. It also depends on call history: one pooled call leaves `True` and two leave `False`. Nothing is lost, only more
`.dat` files persist. But it is a change of behaviour outside the tiled class, and 030 and the docstring present
the price as confined to that class's returned entries and kept stores. Per the consumer-topology note, iof3D is
where the durable-cache and warm-restart configuration lives, and its `purge_disk_on_gc` setting is silently
overridden for those keys.

**Fix:** Document it in 030 and in the class docstring: "the disarm is recorded in each key's `.meta.json`, so any
later store that adopts the directory, tiled or not, loads those keys with purge-on-gc disabled; the setting depends
on call history". Making it uniform would require restoring the intent before codec writes, which `disable_purge()`
cannot do through the public API alone.

## Info

### IN-01: A symlink loop at a write path raises a bare `RuntimeError`, not the documented refusal family

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:79` (`link.resolve()`); docstring `:65-68`.
**Issue:** `k.dat.tmp -> k.dat.tmp` raises `RuntimeError: Symlink loop from …` (Python 3.12 `Path.resolve`). That is not a
`StorePurgeRefusedError`, but `except RuntimeError` still catches it. `c1b813d` raised the same error from upstream, so this is not a
regression, only a contract that is stated more narrowly than the code behaves.
**Fix:** Wrap `link.resolve()` and re-raise as `StorePurgeForeignArtefactError(...) from exc`, or mention the loop case in the docstring.

### IN-02: Three failed-batch and ownership sentences are inaccurate as written

**File:** `src/pc2img/tiled_generator.py:131-132`, `:153-156`, `:208-210`; BC-P2I-030.
**Issue:** Measured in `repro_doc_claims.py`:
- (a) "At `n_jobs=1` the stores were updated in place and nothing is dropped": a *first* call at `n_jobs=1` that fails keeps nothing (`image_generators kept: []`), because generators built during the call are stored only on success.
- (b) "the calling process owns the stores only if every call used `n_jobs=1`": after a pooled call, a failed pooled call and an `n_jobs=1` retry, the parent owns the rebuilt stores and `purge` succeeds.
- (c) "The next call rebuilds each tile's generator in a worker": at `n_jobs=1` it rebuilds them in the parent.

**Fix:** Change (a) to "generators that existed before the call are kept"; (b) to "owns a tile's store if that store was built by an `n_jobs=1` call"; (c) to "rebuilds each tile's generator (in a worker, or in this process at `n_jobs=1`)".

### IN-03: The non-owner leg of the linked-write-path test accepts any `StorePurgeRefusedError`

**File:** `tests/test_image_store.py:396-417` (`_non_owner_adds_k(store) == 3`).
**Issue:** Exit code 3 means any `StorePurgeRefusedError`, so the non-owner leg cannot tell the pre-write aliased refusal from the soft branch's plain re-raise or from a plain process-identity refusal. The test docstring says "the refusal is the aliased class". The byte-identity check on the targets is what actually senses a write, so the sensor is not hollow, only less specific than its docstring.
**Fix:** Give the child a distinct exit code for `StorePurgeAliasedArtefactError`, and assert it for the four write-path kinds (all except `meta_link`, where the plain re-raise is expected).

## Checked and clean

- **Mixed `n_jobs` with the Delaunay triangulation cache** (`repro_delaunay_mixed.py`, `interp_kwargs` cache config): `1,2,1,2` and `2,1,2` with new features each call read every raster and every store entry after `store.offload()`, in 2 of 2 runs. The triangulation stores are never disarmed, but every entry is codec-offloaded and dropped inside `interpolate`, so no second live object shares their `.dat`.
- **Results held across a failed pooled call** (`repro_failed_pooled_deletes.py`, 4 tiles, the last lacking `intensity`): held results from an earlier successful call (`n_jobs` 2 or 1) read before and after the failure and after `offload()` with a retry at `n_jobs` 1 or 2. The finished tiles' new-key `.dat` files are gone after the failure, but they are rebuilt from the adopted `.npy`.
- **Non-tiled direct use.** `_release_gc_ownership` is called only from `TiledPointCloudImageGenerator.generate`. `PointCloudImageGenerator`, `FeatureManager` and the store keep the default armed behaviour, apart from the sidecar inheritance in WR-04.
- **Symlinked cache directory, relative links.** Accepted, and classified correctly by the link refusal.
- **027 verifier detach probe.** Re-extracted. It passes on HEAD and fails with the documented message when the soft branch is deleted from the code.
- **Not pursued.** joblib's loky backend SIGKILLs sibling workers when a task fails (`abort_everything`, `kill_workers=True`). A kill between `_store_entry`'s two `os.replace` calls could leave a lone `<key>.npy` that the retry adopts and cannot load. I did not reproduce the window, so it is not a finding.

---

_Reviewed: 2026-10-05T09:35:54Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
