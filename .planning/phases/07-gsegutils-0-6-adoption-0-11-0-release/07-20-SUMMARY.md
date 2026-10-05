---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 20
subsystem: image-store
tags: [gap-closure, round-3, symlink, write-path, sensor-test]
status: complete

requires:
  - phase: 07-17
    provides: "round-2 narrowed purge gate and soft non-owner branch this plan extends"
provides:
  - "add_image_to_store refuses, before any purge or write and in every process, a symlink at <key>.dat, <key>.dat.tmp, <key>.npy.tmp or <key>.meta.json.tmp (fix e738cf4)"
  - "soft non-owner branch re-raises for a linked .dat/.meta.json leftover (second layer)"
  - "drop-route sensor cases exercise the <key>.npy hard check alone (test commit 446606b)"
  - "ordering and class docstrings corrected"
affects: [07-21 cites fix commit e738cf4 in BC-P2I-027; round-4 review of this diff precedes the 07-07 resume]

actuals:
  tokens: 5118
  tasks: 2
  commits: 3
plan_head_before: bbfb89aec0f584c970657f587f1fb7694f35544e
plan_head_after: 446606b881fdcb0d2b67eafc3de4b91a77d7f5a4

tech-stack:
  added: []
  patterns:
    - "sensors assert the aliased target is byte-identical after forcing the write to disk (store.offload()), not only that an exception was raised"
    - "each mutation of the fix was run and restored (git diff clean) to show its sensors can fail"

key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_image_store.py

key-decisions:
  - "The four write paths only (.dat, .dat.tmp, .npy.tmp, .meta.json.tmp); the .npy / .meta.json finals are os.replace targets and stay out of the check"
  - "Aliased vs foreign class by where the link resolves (inside vs outside the cache directory); both are StorePurgeRefusedError so the method's except contract is unchanged"
  - "The soft-branch re-raise for a linked leftover is kept as a second layer; it alone carries the meta_link non-owner case"

requirements-completed: []

coverage:
  - id: D1
    description: "A linked write path for the key being added is refused before any write, by the owner and by a forked non-owner, with the target byte-identical afterwards"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_add_over_a_linked_write_path_is_refused_before_any_write (5 kinds x owner/non_owner), test_add_over_a_write_path_linked_outside_the_cache_is_refused_as_foreign"
        status: pass
    human_judgment: false
  - id: D2
    description: "All four drop-route cases sense the <key>.npy hard check (fail under the c2 mutation)"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store[del|pop|popitem|clear]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ordering and class docstrings state the pre-write refusal and no longer claim that foreign or aliased refusals surface in the tolerated non-owner case"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "awk/grep acceptance checks below; tests/test_image_store.py#test_presence_gate_uses_only_upstream_builders_of_known_shape"
        status: pass
    human_judgment: true
    rationale: "Whether the prose is accurate and readable is a reading judgment; the factual clauses are backed by the RED/GREEN runs below"
---

# Phase 7 Plan 20: Pre-write refusal of linked write paths, drop-route sensors Summary

`add_image_to_store` now refuses, before anything is purged or written and in every process (owner included), a symlink at any of the four paths a write opens for the key, raising `StorePurgeAliasedArtefactError` or `StorePurgeForeignArtefactError` by where the link resolves; the popitem drop-route case (and the other three) now senses the hard `<key>.npy` check.

Completed 2026-10-05. 2 tasks, 3 production/test commits, 2 files.

## What changed

**Task 1 (tracer): `_refuse_linked_write_path`.** A module-level helper builds `<key>.dat`, `<key>.dat.tmp`, `<key>.npy.tmp`, `<key>.meta.json.tmp` through the upstream builders; the first that `is_symlink()` is resolved, and the helper raises `StorePurgeAliasedArtefactError` (target inside the resolved cache directory) or `StorePurgeForeignArtefactError` (outside). It is called in `add_image_to_store` right after `_assert_image_shape` and before the purge gate. The soft non-owner branch additionally re-raises when a leftover `.dat` or `.meta.json` is a symlink (`_leftover_is_linked`). The ordering docstring is now five steps (the refusal is step 3), the non-owner sentence says upstream's foreign and aliased checks never run in a non-owner process (it refuses on process identity first), and the class-docstring limit is narrowed to a link planted under an already tracked key after its add.

**Task 2: drop-route cases.** The `popitem` branch calls `store.popitem()` as a bare statement and then `gc.collect()`; every route asserts `not get_memmap_path(store.cache_dir, "range").exists()` before the overwrite, so the four cases reach the overwrite with the codec pair alone on disk.

## Commits

| Commit | Message |
|--------|---------|
| 4ce1c22 | test(image_store): a linked write path is refused before any write, in every process |
| e738cf4 | fix(image_store): refuse a linked write path before any write, in every process |
| 446606b | test(image_store): drop routes exercise the npy check alone; popitem discards its value |

The fix commit 07-21 cites in BC-P2I-027: **e738cf4**.

## Which write paths upstream opens (read, then run)

Read in GSEGUtils 0.6.x `lazy_disk_cache.py` / `disk_backed_store.py`:

- memmap path (`_convert_to_memmap`, runs at the add): `np.memmap(<key>.dat.tmp, mode="w+")`, then `os.chmod`, then `os.replace` onto `<key>.dat`; entry-level `offload()` writes through `<key>.dat`.
- codec path (`_store_entry`, runs at `offload_image_data_to_disk`): `open(<key>.npy.tmp, "wb")`, `open(<key>.meta.json.tmp, "w")`, then `os.replace` onto the `.npy` and `.meta.json` finals. The finals are replace targets only (the link itself is replaced, its target untouched).
- `paths._assert_write_contained` refuses only a link that resolves outside the cache directory. Run on HEAD it raised `StoreContainmentError` for the outside `k.dat.tmp` link ("its final component is a symlink resolving to ... outside/victim.dat ... the write is refused"); a link to another key's file inside the cache is followed.

The RED run below confirms exactly these names: the three temporary links corrupt their targets; the `.dat` link is held back on HEAD only by upstream reconciliation (owner) or the deferred write (non-owner).

## RED then GREEN records

### Task 1

RED, on `bbfb89a` (source untouched), `uv run --no-sync pytest tests/test_image_store.py -q -p no:cacheprovider -k "linked_write_path or linked_outside" -rA`:

```
PASSED ...test_add_over_a_linked_write_path_is_refused_before_any_write[dat_link-owner]
PASSED ...test_add_over_a_linked_write_path_is_refused_before_any_write[meta_link-owner]
FAILED ...[dat_tmp_link-owner]
FAILED ...[dat_tmp_link-non_owner]
FAILED ...[npy_tmp_link-owner]
FAILED ...[npy_tmp_link-non_owner]
FAILED ...[meta_tmp_link-owner]
FAILED ...[meta_tmp_link-non_owner]
FAILED ...[dat_link-non_owner]
FAILED ...[meta_link-non_owner]
FAILED ...test_add_over_a_write_path_linked_outside_the_cache_is_refused_as_foreign
9 failed, 2 passed, 122 deselected, 12 warnings
```

Failure reasons: owner temp-link kinds `Failed: DID NOT RAISE StorePurgeAliasedArtefactError`; the five non-owner kinds `assert 0 == 3` (the child added `k` and exited 0); the outside case raised upstream's `StoreContainmentError` (a `ValueError`), not the foreign refusal class. `dat_link[owner]` and `meta_link[owner]` pass on HEAD (upstream reconciliation already refuses there), as the plan predicted.

HEAD corruption, scratch step (`repro_link_corrupt.py` in the session scratchpad, not in the repo; owner process, `purge_disk_on_gc=False`, `other` zeros (6, 6), `k` ones (4, 4)):

```
dat_tmp_link: add accepted; other.dat changed at add=True; after offload_image_data_to_disk('k')=True; len 144->64
npy_tmp_link: add accepted; other.npy changed at add=False; after offload_image_data_to_disk('k')=True; len 272->192
meta_tmp_link: add accepted; other.meta.json changed at add=False; after offload_image_data_to_disk('k')=True; len 184->184
```

(`meta_tmp_link`: same length, different bytes; the differing shape makes the write-through byte-visible.)

GREEN after `e738cf4`: the eleven cases `11 passed`; `tests/test_image_store.py` `133 passed`; full suite `403 passed, 94 warnings`; `ruff check src tests` all checks passed; `ruff format --check src tests` 37 files already formatted. Tracer re-verified end-to-end before the expansion task.

### Mutation checks (source restored after each, `git diff` clean)

- M1, remove the `_refuse_linked_write_path(self.cache_dir, img_name)` call: `7 failed, 4 passed` — the three temporary-link kinds fail in both processes (6) and the outside-link case fails; `dat_link` and `meta_link` (both processes) stay green because upstream reconciliation (owner) and the soft-branch re-raise (non-owner) still hold them. Matches the plan's expectation.
- M2, drop `or _leftover_is_linked(...)` from the soft branch: `1 failed, 10 passed` — exactly `[meta_link-non_owner]` fails. This is why the second layer is kept (the `.dat` half is redundant with the pre-write check, the `.meta.json` half is not).

### Task 2

Before the change, with the c2 mutation (`_adoptable_artefact_exists` returns `False`; `.meta.json` removed from `_leftover_artefact_exists`, `.dat` kept), the OLD drop-route test (HEAD `e738cf4`, run from a scratch copy):

```
PASSED ...[popitem]
FAILED ...[del]
FAILED ...[pop]
FAILED ...[clear]
3 failed, 1 passed
```

After the change, same c2 mutation, `tests/test_image_store.py -k drop_route`:

```
FAILED ...[del]
FAILED ...[pop]
FAILED ...[popitem]
FAILED ...[clear]
4 failed
```

Every one fails with `AssertionError: stale .npy survived the overwrite`. Unmutated tree: `4 passed`. Source restored after the mutation (`git diff` clean).

## Verification

- `uv run --no-sync pytest -q -p no:cacheprovider`: `403 passed, 94 warnings` (final tree `446606b`)
- `tests/test_image_store.py`: `133 passed`
- `ruff check src tests`: all checks passed; `ruff format --check src tests`: 37 files already formatted
- Acceptance checks: `def _refuse_linked_write_path(` count 1; call `_refuse_linked_write_path(self.cache_dir, img_name)` count 1; `get_npy_tmp_path` count 2 (import and use); `foreign or aliased artefact still surface` in the method docstring 0 (`pre-write-refusal-ok`); AST ordering check (shape check < write-path check < purge gate; predicates name no temporary builder; the write-path check names the four builders and no final) `ordering-ok`; `routes-tightened`; the eleven-case and four-case pass counts are 11 and 4.

A green suite proves only that the existing tests still pass. The evidence for the fix is the nine cases red on `bbfb89a` that read the target's bytes after forcing the write, the three scratch corruption lines, and the two mutation checks above.

## Deviations from Plan

**1. [Rule 3 - Blocking] Shape-pin predicate check uses word-boundary regexes.** The first draft matched builder names by `name + "("` and missed `get_meta_tmp_path)` at the end of a tuple; changed to `re.search(rf"\b{name}\b", source)`. Test-only; same commit as the fix (`e738cf4`).

**2. [Process] The tests commit and the fix commit are split as the plan specified; the doc-only edits to the method's "Overwrite failures" bullets** (non-owner bullet: "regular-file" leftover; aliased bullet: names the pre-write refusal) were added beyond the three docstring edits the plan lists, because the old wording would otherwise contradict step 3. No behaviour change.

**3. [Process] The plan commit ledger** `gsd-plan-head-before-07-20` was written before the first commit, with `bbfb89a`.

Total deviations: 0 auto-fixed bugs, 1 test-authoring correction, 1 additional docstring edit.

## Known Stubs

None.

## Threat Flags

None. The change closes T-07-64 (pre-write refusal over the four write paths, owner and forked tests), T-07-65 (docstrings corrected) and T-07-66 (drop-route sensors with the c2 proof). One residual remains as documented in the class docstring: a link planted under an already tracked key after its add is still followed by a later offload.

## Self-Check

Created/modified files exist (`disk_backed_image_store.py`, `tests/test_image_store.py`); commits `4ce1c22`, `e738cf4`, `446606b` are present on the branch.

## Self-Check: PASSED
