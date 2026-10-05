---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 16
subsystem: tiled-orchestration
tags: [loky, joblib, gsegutils-0.6, gap-closure, disable-purge, duplicate-tile-ids, regression-test]
status: complete

requires:
  - phase: 07-12
    provides: "per-tile module-level _process_tile dispatch (the round-1 fix whose results turned out unreadable)"
provides:
  - "TiledPointCloudImageGenerator.generate() calls the public LazyDiskCache.disable_purge() on every returned entry and every live entry of every reassembled store when n_jobs != 1; n_jobs=1 results keep purge_disk_on_gc True"
  - "TiledPointCloudImageGenerator.__init__ raises ValueError('tile ids must be unique; duplicated: [...]') before assigning any attribute"
  - "test_tiled_regenerate_on_one_instance_with_two_workers[n_jobs=1|n_jobs=2] rebinds the result, collects, and reads every raster and store entry with np.asarray"
  - "test_pooled_results_do_not_own_gc_deletion: deterministic flag test"
  - "test_duplicate_tile_ids_are_rejected_at_construction"
  - "class docstring: one _process_tile call per tile, pooled run = any n_jobs other than 1 including -1, unique tile ids, bold 'Disk persistence after a pooled run' paragraph with the two routes"
affects: [07-18 migration record (cites the two fix commits 321d68c and 3d0b43d in BC-P2I-030 and BC-P2I-028), 07-18 rewrite of the ownership/refusal paragraph and workaround bullets]

actuals:
  tokens: 2649
  tasks: 3
  commits: 5
plan_head_before: b552425d37091a6c25770caf00c843b25d54eb23
plan_head_after: 36db04fc569ba550474deb68a0ebedceb0960b6b

tech-stack:
  added: []
  patterns:
    - "regression tests for lazily-read disk-backed output must read every array (np.asarray) after rebinding and gc.collect(); a keys-only assertion cannot see an unlinked memmap"
    - "pooled parent-side copies of disk-backed entries share one .dat path, so none may own GC deletion"

key-files:
  created: []
  modified:
    - src/pc2img/tiled_generator.py
    - tests/test_tiled_generator.py

key-decisions:
  - "Disarm via the public disable_purge() only (no _finalizer / _purge_disk_on_gc access); applied when n_jobs != 1, so the default -1 is covered and n_jobs=1 keeps single-object semantics"
  - "Accepted cost (owner decision 2026-10-02): after a pooled run .dat files persist until purge() or removal of the cache directory, including the default mkdtemp directory; stated prominently in the class docstring with the two routes"
  - "Duplicate tile ids rejected at construction with ValueError naming the sorted duplicates"

requirements-completed: []

coverage:
  - id: D1
    description: "After repeated pooled generate() with the result rebound and collected, every raster and every tile-store entry can be read"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_tiled_regenerate_on_one_instance_with_two_workers"
        status: pass
    human_judgment: false
  - id: D2
    description: "Pooled results and reassembled store entries have purge_disk_on_gc False; n_jobs=1 entries stay True"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_pooled_results_do_not_own_gc_deletion"
        status: pass
    human_judgment: false
  - id: D3
    description: "A repeated tile id raises ValueError naming it at construction"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_duplicate_tile_ids_are_rejected_at_construction"
        status: pass
    human_judgment: false
  - id: D4
    description: "Docstring wording (one call per tile, pooled-run definition, GC ownership, persistence paragraph, unique ids) is accurate and complete for a reader"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "uv run --no-sync pytest tests/test_hygiene.py -q -k 'not benchmark'"
        status: pass
    human_judgment: true
    rationale: "Hygiene gate proves only the absence of planning vocabulary; whether the prose is clear is a reader judgment, and 07-18 rewrites the neighbouring paragraphs"
---

# Phase 07 Plan 16: Readable pooled results, duplicate tile ids (G1-CR-01, G1-WR-04, G1-IN-03 wording) Summary

**Pooled `generate()` results and reassembled tile stores are disarmed with the public `LazyDiskCache.disable_purge()` (when `n_jobs != 1`), so rasters can be read after earlier results are released (12 of 12 rounds failed at the read before, 0 of 12 after); duplicate tile ids now raise `ValueError` at construction.**

Duration: about 5 minutes (2026-10-02T14:03:45Z to 14:08:28Z), 3 tasks, 2 files.

## What was done

### Task 1 (tracer): pooled results stop owning GC deletion

Round 1 stopped the crash but not the data loss: every pickle round-trip of a tile generator gives the parent another entry object on the same `<tile>/<key>.dat`, each with its own armed GC finalizer, so releasing call N's results unlinks the files call N+1's entries read. The old regression test only checked dict keys and never read an array.

- RED commit `fca6e85` (`test(tiled)`): the regression test rewritten to rebind `result` on every call, `gc.collect()`, read every raster and every store entry with `np.asarray`, parametrised over `n_jobs=1` and `n_jobs=2`; plus `test_pooled_results_do_not_own_gc_deletion`.
- GREEN commit `321d68c` (`fix(tiled)`): `_release_gc_ownership(result_dict, image_generators)` calls `disable_purge()` on every result value and every non-None store entry; `generate()` calls it when `n_jobs != 1`. The `generate()` docstring states the rule.

RED run, taken on the unfixed source (HEAD `b552425`, tests uncommitted at that point):

```
FAILED tests/test_tiled_generator.py::test_tiled_regenerate_on_one_instance_with_two_workers[n_jobs=2]
FAILED tests/test_tiled_generator.py::test_pooled_results_do_not_own_gc_deletion
2 failed, 1 passed, 5 deselected, 20 warnings in 2.68s
```

The flag test failed with `AssertionError: [True, True, True, True]` (deterministic). `[n_jobs=1]` passed (control). `[n_jobs=2]` was then re-run three more times on the same unfixed source, failing every time at the read:

```
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/pytest-of-nixton/pytest-1680/test_tiled_regenerate_on_one_i0/tile_00/range.dat'
1 failed, 16 warnings in 2.75s
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/pytest-of-nixton/pytest-1681/test_tiled_regenerate_on_one_i0/tile_00/range.dat'
1 failed, 16 warnings in 2.55s
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/pytest-of-nixton/pytest-1682/test_tiled_regenerate_on_one_i0/tile_00/range.dat'
1 failed, 16 warnings in 2.35s
```

So on this tree the behavioural sensor failed 4 of 4 (not the roughly 5 of 6 the checker saw), and the deterministic flag test failed every time.

GREEN, with the fix applied:

```
3 passed, 5 deselected, 22 warnings in 2.99s          (-k "regenerate or own_gc")
1 passed, 16 warnings in 2.87s                         (n_jobs=2, run 1)
1 passed, 16 warnings in 2.48s                         (n_jobs=2, run 2)
1 passed, 16 warnings in 2.57s                         (n_jobs=2, run 3)
```

Three further consecutive `[n_jobs=2]` runs on the final committed tip `36db04f`: `1 passed` each (2.61s, 2.42s, 2.59s). Whole file at the fix commit: `8 passed`. Full suite after Task 1: `378 passed, 67 warnings in 8.21s`.

### Task 2: duplicate tile ids rejected at construction

- RED commit `bcccde1` (`test(tiled)`): `test_duplicate_tile_ids_are_rejected_at_construction`. Run before the fix:

```
E       Failed: DID NOT RAISE ValueError
FAILED tests/test_tiled_generator.py::test_duplicate_tile_ids_are_rejected_at_construction
1 failed, 8 deselected, 16 warnings in 0.14s
```

- GREEN commit `3d0b43d` (`fix(tiled)`): `__init__` collects the ids before assigning any attribute and raises `ValueError("tile ids must be unique; duplicated: [...]")` with the repeated ids sorted. `PointCloudTile` docstring states the uniqueness rule.

```
1 passed, 8 deselected, 21 warnings in 0.10s          (-k duplicate)
9 passed, 35 warnings in 5.02s                         (whole file)
379 passed, 74 warnings in 7.52s                       (full suite)
```

### Task 3: docstrings (docstring-only)

Commit `36db04f` (`docs(tiled)`). Class docstring first paragraph now says "one `_process_tile` call per tile" (joblib may batch calls into one worker task), defines a pooled run as any `n_jobs` other than 1 including the default `-1`, and states that tile ids are unique. A new paragraph with the bold lead **Disk persistence after a pooled run** states the GC-ownership rule and its price (released results and dropped generators no longer delete their cache files; `<tile_id>/<key>.dat` and the codec pair persist until `purge()` or removal of the cache directory, including the default `tempfile.mkdtemp` directory used when no `cache_path` is configured) and the two routes (configure `cache_path` and remove it; `n_jobs=1` for every call and purge from the owning process). The ownership/refusal paragraph and the three workaround bullets were left exactly as they were (07-18's). The test module docstring names the tests the file now has.

AST identity, docstrings stripped, `HEAD` (the Task 2 fix commit `3d0b43d`) versus the working file, run before committing Task 3:

```
identical
```

Hygiene gate and the tiled tests: `97 passed, 35 warnings in 5.44s`. ruff check clean; ruff format clean (37 files).

## Twelve-round measurement (arrays read)

Script: `_scrap/tiled_regenerate_rounds.py` (gitignored via `_scrap/`, referenced by no tracked file), extended from the 07-12 version. Each of 12 rounds uses a fresh cache directory, two tiles (`make_synthetic_pcd(n=64, seed=1/2)`), `(8, 8)`, spherical, linear, `n_jobs=2`. Each round rebinds `result` on each of three calls (`["range"]`, then the three features `range`, `gradient_x_range`, `hillshade_range_315_45`, then `["range"]`), calls `gc.collect()` after each rebinding, reads every `np.asarray(result[k])` after each call, and at the end reads every store entry for the three features of both tiles. Command: `uv run --no-sync python _scrap/tiled_regenerate_rounds.py 2>&1 | grep -vE 'Parallel|Done|Using backend|elapsed|Warning|warn'`. These two blocks are the only round counts later plans may cite for the array-reading scenario.

### pre-fix

Tree: `b552425` (unmodified source at HEAD; the RED tests committed afterwards as `fca6e85` do not affect the script).

```
round 0 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_00/tile_00/range.dat'"
round 1 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_01/tile_00/range.dat'"
round 2 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_02/tile_00/range.dat'"
round 3 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_03/tile_00/range.dat'"
round 4 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_04/tile_00/range.dat'"
round 5 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_05/tile_00/range.dat'"
round 6 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_06/tile_00/range.dat'"
round 7 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_07/tile_00/range.dat'"
round 8 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_08/tile_00/range.dat'"
round 9 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_09/tile_00/range.dat'"
round 10 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_10/tile_00/range.dat'"
round 11 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_11/tile_00/range.dat'"
failures: 12 / 12
```

### post-fix

Run twice, unchanged script. First on `fca6e85` plus the uncommitted fix (the content committed as `321d68c`, apart from two assertion messages in the flag test), then again on the committed tip `36db04f`. Both:

```
failures: 0 / 12
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan verify expression `-k "regenerate and n_jobs=2"` is not valid pytest syntax**
- **Found during:** Task 1 (RED re-runs)
- **Issue:** pytest rejects `=` in a `-k` expression: `ERROR: Wrong expression passed to '-k': regenerate and n_jobs=2: at column 22: expected end of input; got =`. The plan's second `<automated>` block for Task 1 therefore cannot run as written.
- **Fix:** used the node id `tests/test_tiled_generator.py::test_tiled_regenerate_on_one_instance_with_two_workers[n_jobs=2]`, which selects the same single test. All "three consecutive runs" above use it.
- **Files modified:** none (command only)
- **Commit:** n/a

**2. [Rule 3 - Blocking] Plan wording greps use single backticks; the file uses RST double backticks**
- **Found during:** Task 3 verify
- **Issue:** `grep -c 'one \`_process_tile\` call per tile'` and `grep -c 'including the default \`-1\`'` print 0 because the docstring spells them with double backticks, the convention throughout this module.
- **Fix:** ran the same greps with double backticks (`2` and `2`); every other wording grep (`garbage` 4, `Disk persistence after a pooled run` 1, `mkdtemp` 1, `wording-ok`) passed as written. The docstring was not changed to suit the grep.
- **Files modified:** none
- **Commit:** n/a

**3. [Rule 1 - Test hygiene] Flag-test assertion messages carry the literal `purge_disk_on_gc is False`**
- **Found during:** Task 1 verify
- **Issue:** the plan's third `<automated>` grep counts `purge_disk_on_gc is False` in the test file; my assertion was phrased `flag is False` and counted 0.
- **Fix:** put the literal into the assertion messages of the flag test (and the `True` counterpart). Behaviour unchanged. Folded into the Task 1 fix commit `321d68c` (the RED commit `fca6e85` was already made). The post-fix suite and measurement were re-run afterwards.
- **Files modified:** tests/test_tiled_generator.py
- **Commit:** 321d68c

**Total deviations:** 3 (2 plan-command defects worked around without changing any shipped text, 1 test-message tweak). **Impact:** none on scope or behaviour.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: disk-persistence | src/pc2img/tiled_generator.py | After a pooled run, `.dat`/codec files persist until `purge()` or directory removal, including the default `mkdtemp` directory. Accepted by the owner 2026-10-02 (tracked by a todo the orchestrator writes); documented in the class docstring. Not a new trust boundary, but a resource-retention change. |

## Threat model dispositions

- T-07-53 (released results' finalizers deleting memmaps): mitigated; regression test reads every array after rebinding and GC, red on HEAD first; twelve-round measurement 12/12 to 0/12.
- T-07-54 (duplicate tile ids): mitigated; construction-time `ValueError`, red-then-green test.
- T-07-55 (evidence that passes without reading output): mitigated; every regression and measurement path calls `np.asarray` on every returned raster and on store entries outside the last request; the flag test pins the mechanism deterministically.

## Acceptance criteria re-run

- Task 1: RED before the fix commit recorded (flag test deterministic failure; `[n_jobs=2]` `FileNotFoundError` on `<tile>/range.dat` 4 of 4; `[n_jobs=1]` passes); GREEN and three consecutive passes recorded; twelve-round blocks recorded (pre 12/12, post 0/12); `disable_purge()` count in the source 3, `np.asarray` count in tests 3, `purge_disk_on_gc is False` count 1 after deviation 3; full suite `379 passed` at the tip; ruff check and format clean. PASS.
- Task 2: RED (DID NOT RAISE) then GREEN recorded; `tile ids must be unique` count 1; distinct ids construct as before; `PointCloudTile` docstring states the rule. PASS.
- Task 3: wording greps pass (two with double backticks, see deviation 2); AST identity `identical`; hygiene gate and ruff clean; ownership/refusal paragraph and workaround bullets untouched. PASS.

## Commits

- `fca6e85` test(tiled): read every raster after rebinding and gc; pooled results must not own gc deletion
- `321d68c` fix(tiled): pooled results no longer delete shared memmaps on garbage collection
- `bcccde1` test(tiled): duplicate tile ids are rejected
- `3d0b43d` fix(tiled): reject duplicate tile ids at construction
- `36db04f` docs(tiled): one call per tile, pooled-run definition, gc ownership of pooled results, unique ids

`commits: 5` is measured with `git rev-list --count b552425..HEAD` at SUMMARY time.

## Review still owed (orchestrator/owner, not executor)

Per the plan's verification block and the global gap-closure rule, this round's diff needs its own review before 07-07 resumes: `/gsd-code-review 7 --files src/pc2img/tiled_generator.py tests/test_tiled_generator.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_image_store.py pyproject.toml` and `/code-review 7094dde high`, findings landed with `/gsd-consolidate-findings`. No `07-UAT.md` gap `status:` was changed and no requirement was marked complete.

## Self-Check: PASSED

- `src/pc2img/tiled_generator.py` and `tests/test_tiled_generator.py` exist and carry the changes.
- Commits `fca6e85`, `321d68c`, `bcccde1`, `3d0b43d`, `36db04f` all present in `git log` on `gsd/phase-07-gsegutils-0-6-adoption-0-11-0-release`.
- Full suite `379 passed` at the committed tip `36db04f`; ruff check and format clean.
