---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 13
subsystem: image-store
tags: [gsegutils-0.6, gap-closure, overwrite-purge, finalizer, regression-test]
status: complete

requires:
  - phase: 07-01
    provides: "DiskBackedImageStore reparented onto GSEGUtils 0.6.0 (purge-on-overwrite, drop-tracking-only del/pop/clear)"
  - phase: 07-02
    provides: "docstring-only proof recipe and the store's documented limits"
provides:
  - "add_image_to_store purges whenever the key is tracked OR any of its six upstream-built artefact paths exists (_has_on_disk_artefact)"
  - "tests: overwrite after del/pop/popitem/clear, retained-reference GC, foreign-process new-key pin"
  - "corrected add_image_to_store and class docstrings (three independent refusal triggers, aliased artefact, setter-inserted outside cache_path, worker-owned tile stores)"
affects: [07-14 migration record (cites the fix commit in the BC-P2I-027 amendment), 07-15]

actuals:
  tokens: 2751
  tasks: 2
  commits: 3
plan_head_before: 96b6d333034d8abc90923ce772100b6da844ea2c
plan_head_after: 5ed76a2d0fa725b56526641d25f8243952099251

tech-stack:
  added: []
  patterns:
    - "gate an upstream destructive verb on a presence predicate computed in pc2img, because the verb's owner-pid guard runs before its existence check"

key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_image_store.py

key-decisions:
  - "Purge is gated in pc2img (tracked or on-disk) rather than called unconditionally with suppress(KeyError): upstream's purge runs its owner-pid guard first, so the unconditional form would refuse every brand-new key added from a loky worker (mutation 2 below shows the pin catches that)"
  - "del/pop/popitem/clear stay drop-tracking-only (D-07/D-08); only purge and the overwrite remove files"

requirements-completed: []

coverage:
  - id: D1
    description: "After del/pop/popitem/clear of an offloaded key, add_image_to_store removes the stale codec pair and a fresh store never serves the pre-overwrite raster"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store"
        status: pass
    human_judgment: false
  - id: D2
    description: "A retained reference to a dropped-then-replaced entry does not delete the replacement's <key>.dat on garbage collection"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_retained_reference_to_a_dropped_entry_does_not_delete_the_replacement_memmap_on_gc"
        status: pass
    human_judgment: false
  - id: D3
    description: "A process that did not construct the store can add a brand-new key (exit 0) and is refused on an existing key (exit 3)"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_adding_a_new_key_from_another_process_is_not_refused"
        status: pass
    human_judgment: false
---

# Phase 07 Plan 13: Presence-gated purge on overwrite (CR-02, WR-05, WR-01 store half) Summary

**`add_image_to_store` now purges whenever the key is tracked or any of its six upstream-built artefact paths exists, so an overwrite after `del`/`pop`/`popitem`/`clear` removes the stale codec pair (a fresh store no longer serves the pre-overwrite raster) and disarms the dropped entry's finalizer; docstrings corrected for WR-05 and the store half of WR-01.**

## Commits

| Commit | Message |
| ------ | ------- |
| 9e9af0d | `test(image_store): overwrite after a drop route, retained-reference gc, foreign-process new key` (RED) |
| e3f7f5c | `fix(image_store): purge on overwrite whenever the key is tracked or still has files on disk` (GREEN; **fix commit, cited by 07-14 in the BC-P2I-027 amendment**) |
| 5ed76a2 | `docs(image_store): overwrite refusal conditions, aliased artefact, setter-inserted entries, worker-owned tile stores` |

`commits: 3` is measured with `git rev-list --count 96b6d33..HEAD` from the persisted ledger.

## What changed

Before: `add_image_to_store` purged only `if img_name in self`, and upstream `__contains__` reports tracking only. Since 0.11, `del`/`pop`/`popitem`/`clear` drop tracking and leave `<key>.npy` + `<key>.meta.json`, so a re-add skipped the purge: the old pair survived and a fresh store adopted it, serving the pre-overwrite raster as a cache hit. The skipped purge also left the dropped entry's finalizer armed, so collecting a retained reference deleted the replacement's `<key>.dat`.

After: module-level `_has_on_disk_artefact(cache_dir, key)` tests the six upstream builder paths (`get_npy_path`, `get_meta_path`, `get_npy_tmp_path`, `get_meta_tmp_path`, `get_memmap_path`, `get_memmap_tmp_path`), and the gate is `if img_name in self or _has_on_disk_artefact(self.cache_dir, img_name): self.purge(img_name)`. Statements 1 and 2 (containment-first `get_npy_path(self.cache_dir, img_name)`, `_assert_image_shape`) are untouched. `purge` detaches every registered finalizer for the key and removes the files.

## RED record (before the fix, commit 9e9af0d, unfixed source)

Command: `uv run --no-sync pytest tests/test_image_store.py -q -p no:cacheprovider -k "drop_route or retained_reference or another_process" -rA`

```
PASSED tests/test_image_store.py::test_adding_a_new_key_from_another_process_is_not_refused
FAILED tests/test_image_store.py::test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store[del]
FAILED tests/test_image_store.py::test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store[pop]
FAILED tests/test_image_store.py::test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store[popitem]
FAILED tests/test_image_store.py::test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store[clear]
FAILED tests/test_image_store.py::test_retained_reference_to_a_dropped_entry_does_not_delete_the_replacement_memmap_on_gc
5 failed, 1 passed, 109 deselected, 12 warnings in 0.45s
```

Failing assertions: all four routes `AssertionError: stale .npy survived the overwrite` (`popitem` behaves exactly like `del`/`pop`/`clear`: it drops tracking only and the pair stays); GC test `AssertionError: collecting the dropped entry deleted the replacement's memmap` (`assert False` on `dat.exists()`). The foreign-process pin passes on the old code, as planned.

## GREEN record (fix commit e3f7f5c)

- Same command: all six `PASSED`, `6 passed, 109 deselected, 12 warnings in 0.35s`.
- `tests/test_image_store.py`: `115 passed, 12 warnings in 1.27s`.
- Full suite: `376 passed, 61 warnings in 6.95s` (0 failed).
- `ruff check src tests`: `All checks passed!`; `ruff format --check src tests`: `37 files already formatted`.
- Greps: `def _has_on_disk_artefact(` = 1; `if img_name in self or _has_on_disk_artefact(self.cache_dir, img_name):` = 1; `get_npy_path(self.cache_dir, img_name)` = 1.

## Mutation checks (by running code, working file restored from a saved copy after each)

1. Tracking-only gate restored (`if img_name in self:`): `5 failed, 1 passed, 109 deselected, 12 warnings in 0.38s` (the four drop-route cases and the GC test fail again; the foreign-process pin passes).
2. Unconditional `purge` under `contextlib.suppress(KeyError)` (the review's sketch): `1 failed, 5 passed` with `FAILED ...test_adding_a_new_key_from_another_process_is_not_refused` and `AssertionError: a brand-new key was refused in a non-owner process`. This is the reason the presence test lives in pc2img, and it confirms the pin has teeth.
3. After restoring: `grep -c contextlib` = 0, `git diff` clean for the file, `115 passed`.

## WR-05 re-measurement (setter-inserted entry with an outside `cache_path`)

Scratch script (outside the repo): `store["range"] = DiskBackedImageData(arr, cache_path=<outside cache dir>/range.dat)` then `store.add_image_to_store("range", arr * 2)`:

```
StorePurgeForeignArtefactError ['StorePurgeForeignArtefactError', 'StorePurgeRefusedError', 'RuntimeError', 'Exception', 'BaseException', 'object'] Refusing to purge 'range': a live entry's own cache_path, '.../outside/range.dat', resolves to '...
```

Exception class: `StorePurgeForeignArtefactError` (a `StorePurgeRefusedError`, a `RuntimeError`), matching the review.

## Docstring-only proof (Task 2, source file)

`ast.dump` with docstring nodes stripped, `git show HEAD:...` (HEAD was the Task-1 fix commit e3f7f5c) versus the working file: `identical`. Task 2's test-file edit is comments only. Docstring checks: `StorePurgeAliasedArtefactError` = 1, `TiledPointCloudImageGenerator` = 1, `mapping setter` = 3 (case-insensitive), `conditions-are-alternatives` printed. `tests/test_image_store.py` + `tests/test_hygiene.py` (`-k "not benchmark"`): `203 passed`; full suite after Task 2: `376 passed, 61 warnings in 6.86s`; ruff check and format clean.

## Deviations from Plan

None - plan executed exactly as written. (Two incidental points: ruff's isort rule required the new `GSEGUtils.lazy_disk_cache.paths` test import to be placed in the third-party block, applied with `ruff check --fix` before the RED commit; and the GC test's reference-holding line carries an `assert old is not None` for the type checker.)

## Known Stubs

None.

## Threat Flags

None. The change tightens the overwrite path; no new endpoints, auth paths or file-access patterns. T-07-46, T-07-47 and T-07-48 are mitigated by the tests above.

## Gap-round bookkeeping

Per the dispatch instruction, no `07-UAT.md` gap `status:` field was changed and no requirement was marked complete. Per the global review-discipline rule, this round's diff (07-12 and 07-13) still needs its own review (`/gsd-code-review 7 --files ...`, `/code-review 271b208 high`, then `/gsd-consolidate-findings`) before 07-07 resumes; those are orchestrator/owner steps listed in the plan's `<verification>`.

## Self-Check: PASSED

- Files: `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_image_store.py` modified and committed.
- Commits found: 9e9af0d, e3f7f5c, 5ed76a2.
