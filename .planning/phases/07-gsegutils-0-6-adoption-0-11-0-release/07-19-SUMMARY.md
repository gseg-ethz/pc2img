---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 19
subsystem: tiled-orchestration
tags: [gap-closure, round-3, gc-ownership, retry, docs, sensor-test]
status: complete

requires:
  - phase: 07-16
    provides: "GC-ownership release of pooled results (321d68c), twelve-round array-reading instrument"
  - phase: 07-18
    provides: "round-2 docstring and BC-P2I-030 record this plan corrects"
provides:
  - "generate() disarms delete-on-GC on every call, n_jobs=1 included (fix 4b4add3)"
  - "a pooled dispatch that raises clears image_generators and re-raises, so a retry is not refused (fix d00cfdb)"
  - "TiledPointCloudImageGenerator docstring: Disk persistence as measured, failed-batch route, no sequential exemption (16c7ab9)"
  - "sensors: mixed-n_jobs sequences (3 cases), flag test with both halves False, failing-tile retry, sequential failure keeps generators"
affects: [07-21 cites the two fix commits (4b4add3, d00cfdb) and the twelve-round blocks below in BC-P2I-030; round-4 review of this diff precedes the 07-07 resume]

actuals:
  tokens: 4775
  tasks: 3
  commits: 5
plan_head_before: 0ea1ca6b4bb5c92e83c43ade1c6c1a80c40ddbf8
plan_head_after: 16c7ab92b71c76879b96ae967793b7c0d3b3348f

tech-stack:
  added: []
  patterns:
    - "sensors read arrays and store entries (np.asarray, then store.offload() and read again) after rebinding and gc.collect(); a returned key list proves nothing"
    - "a mutation of the fix (dropping the n_jobs != 1 guard) was run to show the sequential-keep sensor can fail"

key-files:
  created: []
  modified:
    - src/pc2img/tiled_generator.py
    - tests/test_tiled_generator.py

key-decisions:
  - "Disarm on every call (owner decision, option A): cache files persist after sequential runs too; documented rather than avoided"
  - "Reset only when n_jobs != 1: a sequential failure updated the stores in place, so the parent's generators stay the owners"
  - "Reset drops all tile generators, not just the failed tile's: Parallel raises without partial results, so the parent cannot tell which tiles finished"

requirements-completed: []

coverage:
  - id: D1
    description: "Mixed n_jobs sequences on one instance leave every returned raster and store entry readable"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_mixed_n_jobs_sequences_keep_every_raster_readable (3 cases), test_tiled_results_never_own_gc_deletion"
        status: pass
      - kind: command
        ref: "_scrap/tiled_mixed_rounds.py (post-fix): failures: 0 / 12"
        status: pass
    human_judgment: false
  - id: D2
    description: "A retry after a pooled call with one failing tile succeeds at n_jobs=1 and n_jobs=2"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_retry_after_a_pooled_call_with_one_failing_tile_succeeds, test_a_failing_sequential_call_keeps_the_tile_generators"
        status: pass
    human_judgment: false
  - id: D3
    description: "Class docstring states persistence as measured and the failed-batch route"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "AST identity vs d00cfdb (docstrings only): identical; tests/test_hygiene.py"
        status: pass
    human_judgment: true
    rationale: "Whether the prose is accurate and readable for outsiders is a reading judgment; the four measurements below back each factual clause"
---

# Phase 7 Plan 19: Always-disarm, pooled-failure reset, persistence docs Summary

`generate()` now disarms delete-on-GC on every call (the `n_jobs=1` exemption is gone), a failing pooled call drops the parent's stale tile generators so a retry is not refused, and the class docstring states persistence as measured.

Completed 2026-10-05. 3 tasks, 5 commits, 2 files.

## What changed

**Task 1 (tracer): disarm on every call.** The round-2 guard `if n_jobs != 1:` around `_release_gc_ownership` is removed. An entry created at `n_jobs=1` stayed armed; the next pooled call pickled the store and rebuilt `<key>.dat` under new objects; releasing the `n_jobs=1` results then unlinked files the pooled results and the stores read.

**Task 2: pooled failure reset.** The dispatch is wrapped in `try/except BaseException:`; when `n_jobs != 1` the handler runs `self.image_generators.clear()` and re-raises. Finished tiles had written codec pairs the parent's pre-call store copies did not track, so the retry reached the hard gate in a non-owner process (`StorePurgeRefusedError`).

**Task 3: docstrings only** (AST identity vs `d00cfdb`: `identical`). **Disk persistence** paragraph rewritten to the measured facts below; failed-batch route added; the "single-object behaviour" and "behave as before" sentences are gone; test module docstring names the new sensors.

## Commits

| Commit | Message |
|--------|---------|
| bc768c5 | test(tiled): mixed n_jobs sequences must keep every raster readable; results never own gc deletion |
| 4b4add3 | fix(tiled): disarm delete-on-gc on every generate call, n_jobs=1 included |
| 61f584e | test(tiled): retry after a pooled call with one failing tile |
| d00cfdb | fix(tiled): drop stale tile generators when a pooled dispatch fails |
| 16c7ab9 | docs(tiled): persistence as measured, failed-batch route, no sequential exemption |

The two fix commits 07-21 cites in BC-P2I-030: **4b4add3** (disarm every call) and **d00cfdb** (pooled-failure reset).

## RED then GREEN records

### Task 1

RED, on `0ea1ca6` (source untouched), `uv run --no-sync pytest tests/test_tiled_generator.py -q -p no:cacheprovider -k "mixed or own_gc"`:

```
FAILED tests/test_tiled_generator.py::test_tiled_results_never_own_gc_deletion
FAILED tests/test_tiled_generator.py::test_mixed_n_jobs_sequences_keep_every_raster_readable[1-then-2]
FAILED tests/test_tiled_generator.py::test_mixed_n_jobs_sequences_keep_every_raster_readable[1-then-neg1]
FAILED tests/test_tiled_generator.py::test_mixed_n_jobs_sequences_keep_every_raster_readable[2-then-1-adding-then-2]
4 failed, 9 deselected, 24 warnings
```

- flag test (deterministic): `AssertionError: seq (n_jobs=1): expected purge_disk_on_gc is False everywhere: [True, True, True, True]`
- `[1-then-2]`: `FileNotFoundError: ... test_mixed_n_jobs_sequences_ke0/tile_00/range.dat`
- `[1-then-neg1]`: `FileNotFoundError: ... test_mixed_n_jobs_sequences_ke1/tile_00/range.dat`
- `[2-then-1-adding-then-2]`: `FileNotFoundError: ... test_mixed_n_jobs_sequences_ke2/tile_00/gradient_x_range.dat`

All three mixed cases failed on the first run; no re-runs were needed.

GREEN after `4b4add3`: `tests/test_tiled_generator.py`: `13 passed`; full suite `390 passed, 84 warnings`; `ruff check src tests`: all checks passed; `ruff format --check src tests`: 37 files already formatted.

### Task 2

RED on `4b4add3` (before the fix), `-k failing_tile`: first assertion failed, `AssertionError: seq-retry: the parent kept stale tile generators` (`image_generators` held four entries). A separate probe (`_scrap/wr03_probe.py`, gitignored) confirmed the retry itself on the unfixed tree:

```
call2 IndexError
retry 1 StorePurgeRefusedError
call2 IndexError
retry 2 StorePurgeRefusedError
```

GREEN after `d00cfdb`: `1 passed` for the retry test. Added `test_a_failing_sequential_call_keeps_the_tile_generators`; mutation check: replacing `if n_jobs != 1:` with `if True:` turned it red (`1 failed, 1 passed`), source restored before commit. Full suite `392 passed, 94 warnings`; ruff clean.

Test-authoring note: the failing-tile tests use `pytest.raises(Exception)` with `# noqa: B017` and a reason, because the exception type belongs to the point cloud (observed: `IndexError`) and the plan says not to pin it.

## Twelve-round measurement (mixed n_jobs, arrays read)

Instrument: `_scrap/tiled_mixed_rounds.py` (gitignored; extended from `tiled_regenerate_rounds.py`). Per round: `2:["range"]` then `1:` all three features then `2:` all three features, rebinding and `gc.collect()` between calls, every raster read with `np.asarray` after each call, every store entry read after `store.offload()` at the end. Two tiles, `cache_path` set.

### pre-fix (tree `0ea1ca6`; source identical to `bc768c5`; RED tests present)

```
round 0 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_00/tile_00/gradient_x_range.dat'"
round 1 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_01/tile_00/gradient_x_range.dat'"
round 2 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_02/tile_00/gradient_x_range.dat'"
round 3 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_03/tile_00/gradient_x_range.dat'"
round 4 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_04/tile_00/gradient_x_range.dat'"
round 5 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_05/tile_00/gradient_x_range.dat'"
round 6 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_06/tile_00/gradient_x_range.dat'"
round 7 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_07/tile_00/gradient_x_range.dat'"
round 8 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_08/tile_00/gradient_x_range.dat'"
round 9 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_09/tile_00/gradient_x_range.dat'"
round 10 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_10/tile_00/gradient_x_range.dat'"
round 11 FileNotFoundError "[Errno 2] No such file or directory: '/scratch/31_pc2img/_scrap/rounds_cache/round_11/tile_00/gradient_x_range.dat'"
failures: 12 / 12
```

(The run was repeated once to capture the output to a file; the second run printed the same `failures: 12 / 12`.)

### post-fix (tree `4b4add3`, measured on the identical uncommitted working tree immediately before that commit)

```
failures: 0 / 12
```

## Persistence measurements (fixed tree, `TMPDIR` fresh per run, two `generate()` calls, generator and results dropped, `gc.collect()`)

Probe: `_scrap/persist_probe.py` (gitignored). The `uv-*.lock` file in each listing is uv's own and is not a library artefact.

```
== default n_jobs=1: dirs=2 files=1   (uv lock only; two empty mkdtemp directories)
== default n_jobs=2: dirs=2 files=1   (uv lock only; two empty mkdtemp directories)
== cache n_jobs=1: dirs=2 files=5     (4 library files: <store dir>/{range,gradient_x_range}.dat per tile)
== cache n_jobs=2: dirs=2 files=13    (12 library files per tile: {range,gradient_x_range}.dat, .npy, .meta.json)
```

So: the default config writes no files at either `n_jobs`; caching without `cache_path` leaves `<store dir>/<key>.dat`, plus the `.npy` and `.meta.json` codec pair after a pooled run; with this round's change the `.dat` files now also persist after a sequential run.

## Verification

- `uv run --no-sync pytest -q -p no:cacheprovider`: `392 passed, 94 warnings` (final tree `16c7ab9`)
- `tests/test_tiled_generator.py tests/test_hygiene.py -k "not benchmark"`: `103 passed`
- `ruff check src tests`: all checks passed; `ruff format --check src tests`: 37 files already formatted
- Docstring-only AST identity (Task 3 vs `d00cfdb`): `identical`
- Acceptance greps: `_release_gc_ownership` unconditional count 1; `purge_disk_on_gc is True` outside comments 0; `enable_caching=False` 1; `<store dir>/<key>.dat` 1; `drops its tile generators` 1; `single-object` 0; `behave as before` 0; `self.image_generators.clear()` 1; `except BaseException:` 1

A green suite proves only that the tests that exist still pass; the evidence for the fixes is the sensors that were red on `0ea1ca6`/`4b4add3` and read arrays, and the 12/12 to 0/12 measurement.

## Deviations from Plan

**1. [Rule 2 - Missing coverage] Added a sequential-failure sensor.** The plan states "`n_jobs=1` failures drop nothing" as a truth but lists no test for it. Added `test_a_failing_sequential_call_keeps_the_tile_generators` and mutation-checked it. Commit d00cfdb.

**2. [Process] A malformed commit was amended.** My own helper edit damaged the retry test body in commit `269c0a3` (the file did not parse); I repaired the file and amended that unpushed local commit as `61f584e` before any further work. No broken commit remains in history. The tracked content of `61f584e` is the intended test.

**3. [Process] The plan commit ledger was written after the first test commit.** `gsd-plan-head-before-07-19` was created with the value `0ea1ca6...` (the HEAD before any commit of this plan) after the first commit rather than before it; the value is the correct pre-plan HEAD, and `git rev-list --count` gives 5 commits.

**Total deviations:** 1 auto-added coverage item, 2 process notes. **Impact:** none on behaviour or scope.

## Issues Encountered

None open. Cleared `PINNED_ROOT` guard before the first write and before every commit.

## Known Stubs

None.

## Threat Flags

None. No new network, auth, file-access or schema surface; the change reduces deletion of cache files, the documented cost of the owner decision.

## Notes for the next steps (orchestrator/owner)

- This diff needs its own review before 07-07 resumes: `/gsd-code-review 7 --files src/pc2img/tiled_generator.py tests/test_tiled_generator.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_image_store.py` and `/code-review c1b813d high`, findings landed with `/gsd-consolidate-findings`. Not executed here.
- 07-21 owns the BC-P2I-030 row update; it should cite `4b4add3`, `d00cfdb` and the `failures: 12 / 12` to `failures: 0 / 12` lines above.
- No `07-UAT.md` gap `status:` field was changed; no requirement was marked complete (gap-closure plan). 07-07 and 07-15 untouched.

## Self-Check: PASSED

- FOUND: src/pc2img/tiled_generator.py, tests/test_tiled_generator.py
- FOUND commits: bc768c5, 4b4add3, 61f584e, d00cfdb, 16c7ab9
