---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 02
subsystem: image-cache
tags: [gsegutils-0.6, containment, whole-tree-snapshot, tempfile-isolation, store-key-rule]

requires:
  - phase: 07-01
    provides: "DiskBackedImageStore as a thin wrapper over GSEGUtils 0.6.0 (upstream containment, purge as the delete verb) and the 0.6-contract store tests this plan extends"
provides:
  - "tests/test_image_store.py: seven key spellings x six routes (42 cells) asserting ValueError and a bit-identical temp tree, via a symlink-safe whole-tree snapshot"
  - "containment-before-shape precedence pin (the one test that pins the StoreKeyError subtype)"
  - "del drops tracking only / store mapping read-only / empty-raster overwrite sensors"
  - "characterization of the upstream key rule over the names the pipeline and extend_cache_path produce"
  - "tests/conftest.py autouse fixture redirecting tempfile.tempdir under tmp_path/_tmp (zero leaked tmp* entries)"
  - "the store-key rule stated in PointCloudTile and TIGSettings.extend_cache_paths docstrings"
affects: [07-03 tiled re-generate race, 07-06 migration record, 07-07]

actuals:
  tokens: 3417
  tasks: 2
  commits: 2
plan_head_before: 3a4adcd143a55cdcb923cb3d6f42843519855d9b
plan_head_after: b7b38c61068cc830924e131345769a2afbb67ac2

tech-stack:
  added: []
  patterns:
    - "regression net by whole-tree snapshot: take a symlink-safe snapshot of the entire per-test tmp_path, run the refused call, assert the snapshot is unchanged"
    - "autouse tempfile.tempdir redirect to a subdirectory of tmp_path that snapshot helpers exclude"

key-files:
  created: []
  modified:
    - tests/test_image_store.py
    - tests/conftest.py
    - src/pc2img/tiled_generator.py

key-decisions:
  - "Leak verification counts tmp* entries, not every non-pytest-of entry: uv run itself leaves a uv-*.lock file in TMPDIR, so the plan's literal 'ls | grep -v pytest-of | wc -l' cannot reach 0 under uv run"
  - "Two tests that enumerated tmp_path directly (purge test, snapshot-helper test) were adjusted to tolerate the _tmp redirect directory rather than moving the redirect outside tmp_path"

patterns-established:
  - "Shipped text carries no planning vocabulary (hygiene gate stays green)"

requirements-completed: [DEP-05]

coverage:
  - id: D1
    description: "Every escape route re-pinned: 7 spellings (parent segment, absolute, embedded traversal, nested, empty, dot, dotdot) x 6 routes each raise ValueError and leave the whole temp tree bit-identical"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py::test_escaping_key_refused_on_every_route_and_nothing_written_anywhere (42 cells); -k 'escaping or refused' -> 60 passed"
        status: pass
      - kind: other
        ref: "mutation: with upstream validate_store_key / is_valid_store_key / _assert_contained / _assert_write_contained / _build neutralised, all 42 cells FAIL"
        status: pass
    human_judgment: false
  - id: D2
    description: "Containment precedes the shape check; del drops tracking only; mapping read-only; key rule characterized; empty raster accepted"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py (109 passed); precedence test fails (AssertionError) when the key check is neutralised"
        status: pass
    human_judgment: false
  - id: D3
    description: "A full test run leaves zero tmp* entries in the system temp directory outside pytest's own tree"
    verification:
      - kind: other
        ref: "TMPDIR=$(mktemp -d); pytest full run; tmp* count 18 before (19 incl. uv lock), 0 after"
        status: pass
    human_judgment: false

duration: ~10min
completed: 2026-10-02
status: complete
---

# Phase 7 Plan 02: Re-pin the escape routes and stop the temp leak Summary

**Whole-tree snapshot corpus (7 key spellings x 6 routes = 42 cells) re-pins upstream containment on the migrated store, plus the containment-before-shape pin, 0.6 delete/read-only sensors, the upstream key-rule characterization, an autouse tempfile redirect that takes the per-run leak from 18 `tmp*` entries to 0, and the key rule stated in the tiled generator's docstrings**

## Performance

- **Duration:** ~10 min (approximate; start time not captured)
- **Completed:** 2026-10-02
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `_tree(root)` snapshots the whole per-test `tmp_path` without following links (symlink checked first, recorded by `os.readlink`; `_tmp` excluded). `_escape_layout` now also creates `cache/a` so the embedded-traversal spelling can really escape. A small sensor test pins that a dangling link does not crash the snapshot.
- 42 cells (`parent_segment`, `absolute`, `embedded_traversal`, `nested`, `empty`, `dot`, `dotdot` x `add`, `setitem`, `add_then_offload`, `purge`, `getitem`, `add_data`) each raise `ValueError` and leave `_tree(tmp_path)` unchanged, the key untracked and the sentinel intact. The `nested` (`sub/nested`) cells pin that nesting under the cache directory is no longer a legal key on any route.
- **Reproduced by running code, not by reading:** a probe over the same 42 combinations before writing the tests printed `StoreKeyError` (a `ValueError`) for every cell. A mutation run with the upstream validator, both containment asserts and the path builder neutralised makes all 42 cells FAIL (the net is sensitive to a stray write anywhere in the tree), and the precedence test then fails with `AssertionError` (the shape check wins when the key check is gone). With only the validator neutralised, the 42 cells still pass because upstream's containment and write-containment layers back it up; that defence in depth is why the mutation had to neutralise all of them.
- The precedence test is the one place the upstream subtype (`StoreKeyError`) is asserted; everywhere else the contract is `ValueError`.
- `del store[k]` drops tracking only (codec pair and memmap remain; re-adopted on the next read and by a fresh store); `store.store` is a read-only `MappingProxyType` (`TypeError` on assignment and deletion).
- Key-rule characterization: 23 realistic pipeline keys and `extend_cache_path` segments (feature names incl. `z1e-05`, scalar-field names with spaces, tile ids, hex digests, triangulation intermediates) are legal under `is_valid_store_key`; 10 hostile names are refused. Run against `TIGSettings.extend_cache_paths`: `tile_03`, `tile 03`, `0_0` extend cleanly, `../x`, `a/b`, `..` raise `StoreKeyError` unwrapped (a `ValueError`).
- Empty-raster edge: overwriting with an empty `(0, 0)` float32 raster is accepted on GSEGUtils 0.6.0 and the store serves shape `(0, 0)` (matches the research measurement; no deviation).
- Temp leak: **18 `tmp*` entries per full run before, 0 after** (`TMPDIR=$(mktemp -d)`, full suite; 366 passed both times). With the redirect, the five modules that call `tempfile` without `dir=` land under pytest's own tree.
- `PointCloudTile` (new class docstring) and `TIGSettings.extend_cache_paths` (new docstring) now state that the id/segment is validated upstream and an illegal one raises `StoreKeyError` unwrapped.

## Docstring-only proof for `tiled_generator.py`

Task 2 commit `b7b38c6`. `git diff b7b38c6^..b7b38c6 -- src/pc2img/tiled_generator.py` shows only added docstring lines (15 insertions, 0 deletions, all inside the two docstrings). An AST comparison with docstring nodes removed, on `git show b7b38c6^:src/pc2img/tiled_generator.py` vs `git show b7b38c6:src/pc2img/tiled_generator.py`, printed `identical`.

## Task Commits

1. **Task 1: whole-tree snapshot escape corpus, precedence pin, del/purge/read-only sensors, key-rule characterization, empty-raster edge** - `8e6b0a5` `test(image_store)`
2. **Task 2: autouse tempfile isolation and the key rule stated in the tiled generator** - `b7b38c6` `test(conftest)` / `docs(tiled)`

**Plan metadata:** committed separately (docs: complete plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Leak-check command counts uv's own lock file**
- **Found during:** Task 2 verification
- **Issue:** The plan's `ls "$TMPDIR" | grep -v '^pytest-of' | wc -l` cannot reach 0 when pytest is launched through `uv run`: uv leaves `uv-<hash>.lock` in `TMPDIR`. The baseline count was 19, of which 18 are `tmp*` entries and 1 is uv's lock file.
- **Fix:** Counted `tmp*` entries (the D-12 wording: "zero `tmp*` entries other than pytest's own tree"). Cross-checked by running `.venv/bin/python -m pytest` directly (no uv): every non-`pytest-of` entry count is 0. Result: 18 -> 0.
- **Files modified:** none (verification only)

**2. [Rule 3 - Blocking] Two tests broke under the `tmp_path/_tmp` redirect**
- **Found during:** Task 2 full-suite run (2 failed, 364 passed)
- **Issue:** `test_purge_removes_the_codec_pair_and_the_memmap` lists `tmp_path` (used as the cache directory) and asserts it is empty; the new `_tmp` directory made it non-empty. My own `test_tree_snapshot_records_links_...` called `mkdir()` on a `_tmp` that the fixture had already created.
- **Fix:** The purge test now ignores the `_tmp` redirect directory when asserting emptiness; the snapshot-helper test uses `mkdir(exist_ok=True)`. The redirect stays at `tmp_path/_tmp` as specified (the snapshot helper excludes it).
- **Files modified:** `tests/test_image_store.py`
- **Commit:** `b7b38c6`

**3. Test-count note (not a defect)**
- The plan's fails_when floor for `-k "escaping or refused"` is 46; the run selects 60 passed (42 cells + 10 hostile-key refusals + the precedence test + 7 pre-existing setter, add and purge-refusal tests). Passed.

**Total deviations:** 2 auto-fixed, 0 architectural. Impact: none on the plan's outputs.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. No new network, auth, file-access or schema surface; the plan adds tests, a test fixture and docstrings.

## Notes for the owner

- Row r4-da637a8dfe3c (bare `assert` in `_assert_image_shape`) stays deferred per O-2; `disk_backed_image_data.py` untouched.
- The snapshot corpus is a regression net over upstream's layered containment: neutralising only the key validator does not fail it, because the containment and write-containment asserts still refuse. Only removing all layers (as the mutation run did) turns it red. That is the correct behaviour for a net, but it means a single-layer regression upstream would not be visible here.

## Self-Check: PASSED

- `8e6b0a5` and `b7b38c6` present in `git log`.
- `tests/test_image_store.py`, `tests/conftest.py`, `src/pc2img/tiled_generator.py` contain the specified symbols (`def _tree(`, `isinstance(excinfo.value, StoreKeyError)`, `autouse=True`, `is_valid_store_key`).
- Full suite 366 passed; hygiene gate (`planning_vocabulary`) 82 passed; `ruff check` and `ruff format --check` clean.
