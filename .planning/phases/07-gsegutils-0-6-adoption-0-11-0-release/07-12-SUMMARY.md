---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 12
subsystem: tiled-orchestration
tags: [loky, joblib, gsegutils-0.6, gap-closure, per-tile-dispatch, regression-test]
status: complete

requires:
  - phase: 07-01
    provides: "pc2img on GSEGUtils 0.6.0 (the locked environment the race fires on)"
  - phase: 07-03
    provides: "the expected-failure test and the upstream/tracking issues this plan converts into a passing test"
provides:
  - "TiledPointCloudImageGenerator.generate() dispatches the module-level _process_tile once per tile; a task carries only that tile's generator (or None) and picklable inputs"
  - "test_tiled_regenerate_on_one_instance_with_two_workers is a plain passing test, shown to fail on the bound-method dispatch first"
  - "test_generate_dispatches_one_tile_per_task_without_pickling_the_generator: deterministic fan-out shape test"
  - "test_tile_stores_built_by_workers_refuse_purge_from_the_parent: pins the documented worker-owned-store limit (WR-01, documented not fixed)"
  - "class docstring on TiledPointCloudImageGenerator: per-tile dispatch, GSEGUtils#82, worker-owned stores and three cleanup routes"
affects: [07-14 migration record (cites fix commit and the twelve-round counts), 07-15 issue notes (cites the twelve-round counts)]

actuals:
  tokens: 3786
  tasks: 2
  commits: 3
plan_head_before: 5382b681841b5237c3e44568f80af7a97187bd98
plan_head_after: c7144268701073c0304410842ff6ecc051662d98

tech-stack:
  added: []
  patterns:
    - "loky fan-out dispatches a module-level function with per-item arguments, never a bound method of the orchestrating object"
    - "fan-out shape checked deterministically by monkeypatching Parallel with a recorder that captures the delayed(...) triples and runs them inline"

key-files:
  created: []
  modified:
    - src/pc2img/tiled_generator.py
    - tests/test_tiled_generator.py

key-decisions:
  - "Docstring-only commit for Task 2 and the regression-test docstring combined into one docs(tiled) commit with the pin test (the plan allowed either)"
  - "The structural test's membership check was corrected (string equality instead of `in`, which calls == on array payloads) after the RED run; the corrected test was re-run against the old source and still fails there"

requirements-completed: [DEP-05]

coverage:
  - id: D1
    description: "Repeated generate() on one TiledPointCloudImageGenerator with two tiles and n_jobs=2 works on GSEGUtils 0.6.0"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_tiled_regenerate_on_one_instance_with_two_workers"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each loky task is a module-level call carrying only its own tile's generator and picklable inputs"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_generate_dispatches_one_tile_per_task_without_pickling_the_generator"
        status: pass
    human_judgment: false
  - id: D3
    description: "Worker-built tile stores refuse purge from the parent (documented limit), clean purge with n_jobs=1"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_tile_stores_built_by_workers_refuse_purge_from_the_parent"
        status: pass
    human_judgment: false
---

# Phase 07 Plan 12: Per-tile loky dispatch (CR-01, WR-01 tiled half) Summary

**Per-tile module-level `_process_tile` dispatch in `TiledPointCloudImageGenerator.generate()`, so repeated generation at `n_jobs >= 2` stops failing on GSEGUtils 0.6.0 (12 of 12 rounds failed before, 0 of 12 after), with the expected-failure marker replaced by a regression test shown red first.**

## Commits

| Commit | Message |
| ------ | ------- |
| baa0f2a | `test(tiled): regression and fan-out shape tests for repeated generate with n_jobs >= 2` (RED) |
| 4fbd966 | `fix(tiled): dispatch one tile per loky task instead of pickling the whole generator` (GREEN; **fix commit, cited by 07-14**) |
| c714426 | `docs(tiled): state per-tile dispatch and worker-owned tile stores` (docstrings plus the WR-01 pin; single commit chosen) |

`commits: 3` is measured with `git rev-list --count 5382b68..HEAD` from the persisted ledger.

## What changed

Before: `generate()` handed `delayed(self._process_tile)(...)` to loky, so cloudpickle serialised the bound method together with `self`: every task carried every tile's generator, store and point cloud, and every worker unpickled every tile's store at once, racing GSEGUtils 0.6.0's fixed `<key>.dat.tmp` rebuild name on the second `generate()`.

After: `_process_tile` is a module-level function (serialised by reference). `generate()` calls `delayed(_process_tile)(self.image_generators.get(tile_id), tile_id, tile_pcd, tile_kwargs, features, proj_cls, interp_cls, dict(proj_kwargs), dict(interp_kwargs), lazy_disk_cache_config, img_res)` once per tile. The nested interpolation cache config is extended by `tile_id` only when a generator has to be built (new dict, caller's never mutated); `parallel_config(...)` arguments and the result/`image_generators` refill are unchanged. The class no longer has a `_process_tile` method.

## RED record (taken before the fix, on baa0f2a with the unfixed source)

Command: `uv run --no-sync pytest tests/test_tiled_generator.py -q -p no:cacheprovider -k "regenerate or dispatches"`

```
FAILED tests/test_tiled_generator.py::test_tiled_regenerate_on_one_instance_with_two_workers
FAILED tests/test_tiled_generator.py::test_generate_dispatches_one_tile_per_task_without_pickling_the_generator
2 failed, 3 deselected, 18 warnings in 2.41s
```

- Regression test: `joblib.externals.loky.process_executor.BrokenProcessPool: A task has failed to un-serialize.` (a `RuntimeError`), with the worker-side cause `FileNotFoundError: [Errno 2] No such file or directory: '.../tile_00/range.dat.tmp'` (an `OSError`). Same family as the one recorded in the earlier migration plan's `OBSERVED_TYPES` (`BrokenProcessPool`).
- Structural test: `AssertionError: bound method dispatched: <bound method TiledPointCloudImageGenerator._process_tile of <pc2img.tiled_generator.TiledPointCloudImageGenerator object at 0x...>>`.
- Precondition before RED: `1 xfailed` (not XPASS), GSEGUtils `0.6.0`.

The structural test needed one correction after RED (see Deviations). After the correction, both tests were re-run against the old source (`git show 5382b68:src/pc2img/tiled_generator.py` swapped in temporarily, restored afterwards): `2 failed, 3 deselected` with the same two errors above, then restored.

## GREEN record

- `tests/test_tiled_generator.py` on the fixed source: `5 passed` (before Task 2's pin test), then `6 passed` with it.
- Regression test, three consecutive runs (`-k regenerate`): `1 passed`, `1 passed`, `1 passed`.
- `-rxX` file run: no `xfailed`, no `xpassed`.
- Full suite: `370 passed, 61 warnings in 6.38s` (0 failed, 0 xfailed).
- `ruff check src tests`: `All checks passed!`; `ruff format --check src tests`: `37 files already formatted`.
- Hygiene gate (`tests/test_hygiene.py`): `88 passed`; `-k planning_vocabulary`: `82 passed, 6 deselected`.
- Dispatch shape greps: `grep -c '^def _process_tile('` = 1, `grep -c 'delayed(_process_tile)'` = 1, `delayed(self.` outside comments = 0.
- Acceptance greps for Task 2: `StorePurgeRefusedError` in source = 1, `issues/82` in source = 1, pin test defined = 1, `xfail` outside comments in the test file = 0.

## Twelve-round measurement

Script: `_scrap/tiled_regenerate_rounds.py` (gitignored via `_scrap/`, referenced by no tracked file). Each of 12 rounds uses a fresh cache directory, two tiles (`make_synthetic_pcd(n=64, seed=1/2)`), `(8, 8)`, spherical, linear, and runs `generate(["range"], n_jobs=2)`, `generate(["range", "gradient_x_range", "hillshade_range_315_45"], n_jobs=2)`, `generate(["range"], n_jobs=2)`, asserting both tiles' `range` keys in the last result. Command: `uv run --no-sync python _scrap/tiled_regenerate_rounds.py 2>&1 | grep -vE 'Parallel|Done|Using backend|elapsed'`. These two blocks are the only round counts 07-14 and 07-15 may cite.

### pre-fix

Tree: `5382b68` (unmodified source at HEAD; the two RED tests were uncommitted in the working tree and do not affect the script).

```
round 0 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 1 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 2 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 3 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 4 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 5 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 6 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 7 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 8 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 9 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 10 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
round 11 BrokenProcessPool 'A task has failed to un-serialize. Please ensure that the arguments of the function are all picklable.'
failures: 12 / 12
```

### post-fix

Run twice, unchanged script. First on `baa0f2a` plus the uncommitted fix (the content committed as `4fbd966`), then again on the committed tip `c714426` (the two trees differ only in docstrings and the pin test). Both:

```
failures: 0 / 12
```

## WR-01 ownership outcome (re-measured, `_scrap/wr01_probe.py`)

```
n_jobs 2 subdir exists True owner attrs {'_owner_pid': 169373} store type DiskBackedImageStore
 purge refused: (StorePurgeRefusedError, RuntimeError, Exception) Refusing to purge 'range': this store was constructed by process 169373 and purge was called from process 169317. ...
 keys after ['range'] files ['range.meta.json', 'range.npy']
n_jobs 1 subdir exists True owner attrs {'_owner_pid': 169317} store type DiskBackedImageStore
 purge OK; keys after []
```

Parent pid was 169317: with `n_jobs=2` the store is owned by the worker (169373) and the parent's `purge` is refused as a no-op (key and both files intact); with `n_jobs=1` the parent owns the store and purges cleanly; the `<cache_path>/<tile_id>` sub-directory exists in both cases. This matches the planner's measurement. No behaviour change was made (owner disposition: document now, fix after 0.11.0).

## Docstring-only proof (Task 2, source file)

`ast.dump` of `git show HEAD:src/pc2img/tiled_generator.py` (4fbd966) versus the working file with docstring nodes removed: `identical`. (The `generate()` docstring went in with the fix commit as part of the dispatch change; Task 2's source edit is the class docstring only.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Structural test membership check called `==` on arrays**
- **Found during:** Task 1 GREEN
- **Issue:** `tile_id in values` evaluates `==` against numpy-backed payload values and raised `ValueError: The truth value of an array ... is ambiguous` once the dispatch was fixed (on the old source the earlier bound-method assertion fired first, so RED never reached this line).
- **Fix:** compare by `isinstance(v, str) and v == tile_id`; the second-call generator check uses `is`.
- **Files modified:** `tests/test_tiled_generator.py`
- **Verification:** the corrected test was re-run against the old source and still fails there (`bound method dispatched`), then passes on the fix. Committed with the fix in 4fbd966 (the RED commit baa0f2a holds the pre-correction version).
- **Commit:** 4fbd966

**2. [Plan wording] Fix and test-docstring commits**
- The plan offered amending the docstring into the fix commit or a separate commit, and a single or two Task 2 commits. Chosen: one `docs(tiled)` commit carrying the class docstring, the regression-test and module docstrings, and the pin test.

**Total deviations:** 1 auto-fixed (Rule 1, test-only), 1 packaging choice. **Impact:** none on scope.

## Behaviour note

The interpolation cache config is now extended by `tile_id` only when a generator is built in the worker; previously the extension (and its `StoreKeyError` for an illegal id) ran on every call, including reuse. An illegal id still raises on the first `generate()`, which is where the generator is built, so the unwrapped-error contract in the `PointCloudTile` docstring holds.

## Known Stubs

None.

## Threat Flags

None. The change removes cross-process sharing of a store (T-07-43); no new endpoints, auth paths or file-access patterns.

## Gap-round bookkeeping

Per the dispatch instruction, no `07-UAT.md` gap `status:` field was changed; the orchestrator handles UAT after the round's own review (required by the global review-discipline rule, listed under the plan's `<verification>`; not an executor task).

## Self-Check: PASSED

- Files: `src/pc2img/tiled_generator.py`, `tests/test_tiled_generator.py` present; `_scrap/tiled_regenerate_rounds.py` present and gitignored.
- Commits found: baa0f2a, 4fbd966, c714426.
