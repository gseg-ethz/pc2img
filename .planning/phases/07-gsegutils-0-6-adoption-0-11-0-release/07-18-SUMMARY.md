---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 18
subsystem: tiled-orchestration-docs
tags: [gap-closure, docs, migration-record, pyproject, sensor-test]
status: complete

requires:
  - phase: 07-16
    provides: "GC-ownership release of pooled results (321d68c), duplicate tile ids rejected (3d0b43d), twelve-round array-reading measurement"
  - phase: 07-17
    provides: "hard/soft overwrite gate (b2a3baa)"
provides:
  - "pyproject.toml [tool.uv.sources] NOTE without the clause that gave the inert bindings a purpose"
  - "TiledPointCloudImageGenerator docstring: refusal trigger (untracked key with its codec pair on disk), pool-random vs n_jobs=1-deterministic, tolerated leftovers, corrected workaround bullets"
  - "tests/test_tiled_generator.py::test_regenerate_at_n_jobs_1_after_a_pooled_run_tolerates_a_leftover_temporary_but_refuses_a_dropped_codec_pair"
  - "MIGRATION-v0.11.md: BC-P2I-027/028/030 at the round-2 behaviour, verifier with two new probes, thirty entries, [ok] verified 30 entries"
affects: [07-07 resumes after the round-2 review; its D03_SHA line is stale because shipped files changed]

actuals:
  tokens: 6300
  tasks: 3
  commits: 4
plan_head_before: becfe30e57730af3220a95bd0838cd2e9f083ae3
plan_head_after: 1fa8bb7e59dd0d88367474e05c224e7cd879f44f

tech-stack:
  added: []
  patterns:
    - "every behavioural sentence in a docstring or record is reproduced by running code on the final tree first; the tiled-level sensor pins the two sentences that describe the remaining limit"

key-files:
  created: []
  modified:
    - pyproject.toml
    - src/pc2img/tiled_generator.py
    - tests/test_tiled_generator.py
    - .planning/MIGRATION-v0.11.md

key-decisions:
  - "The record states the default-directory persistence precisely: with enable_caching=True and no cache_path the mkdtemp directory keeps its files; with the default enable_caching=False a pooled run writes no files and only empty per-tile directories remain (measured)"
  - "Duplicate-id rule added to BC-P2I-028 and cross-referenced from BC-P2I-030; the tiled class symbol added to 028's affected_symbols (dotted, so Tier 1 ignores it)"

requirements-completed: []

coverage:
  - id: D1
    description: "The sources NOTE no longer gives the inert bindings a purpose; bindings and uv.lock unchanged"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "uv lock --check; grep -c pypi.nvidia.com uv.lock (0); binding count 4; note-fixed"
        status: pass
    human_judgment: false
  - id: D2
    description: "A leftover temporary is tolerated and a dropped codec pair is refused at n_jobs=1 after a pooled run"
    requirement: BC-01
    verification:
      - kind: unit
        ref: "tests/test_tiled_generator.py#test_regenerate_at_n_jobs_1_after_a_pooled_run_tolerates_a_leftover_temporary_but_refuses_a_dropped_codec_pair"
        status: pass
    human_judgment: false
  - id: D3
    description: "The tiled docstring paragraph and bullets describe the reproduced behaviour; only docstrings changed"
    requirement: BC-01
    verification:
      - kind: command
        ref: "AST with docstrings stripped, step-2 test commit vs working file: identical"
        status: pass
    human_judgment: true
    rationale: "The AST check proves nothing but docstrings changed and the sensor pins two sentences; whether the prose is clear to a downstream reader is a reader judgment"
  - id: D4
    description: "BC-P2I-027/028/030 describe the round-2 behaviour; the inline verifier proves the two new mechanical claims"
    requirement: BC-01
    verification:
      - kind: command
        ref: "extracted verifier: [ok] verified 30 entries; both mutations flip it red"
        status: pass
    human_judgment: true
    rationale: "The verifier proves the duplicate-id ValueError and the owner-process durable re-add; the remaining prose (gate description, persistence, trigger, caveat) is reproduced by scratch scripts but not asserted by the verifier"
---

# Phase 07 Plan 18: Round-2 documentation and record (G1-IN-04, tiled half of G1-WR-02, MIGRATION 027/028/030) Summary

**The sources NOTE no longer contradicts the comment above it, the tiled docstring now names the refusal trigger that reproduces (an untracked key whose codec pair is on disk, pool-random and deterministic at `n_jobs=1` after a pooled run) with the one workaround that holds, and BC-P2I-027/028/030 describe the round-2 behaviour with the verifier green at thirty entries and two new probes.**

Duration: about 7 minutes (2026-10-02T14:15:30Z to 14:22Z), 3 tasks, 4 files, 4 task commits.

## Task 1: NOTE in `[tool.uv.sources]` (commit `e3900b0`)

Precondition and acceptance, as run:

```
uv lock --check            -> Resolved 137 packages in 1ms   (before and after, exit 0)
grep -c 'pypi.nvidia.com' uv.lock -> 0                       (before and after)
binding count (cudf|cuspatial)-cu1[12] = { index = "nvidia" } -> 4
stale clause 'keep an index binding' in the sources block -> 0
note-fixed
tests/test_hygiene.py -k planning_vocabulary -> 82 passed, 6 deselected
git status --short uv.lock -> clean (lock untouched, no re-lock needed)
```

The last sentence of the NOTE now keeps the two pin facts and ends: "The cudf and cuspatial names are the two RAPIDS names the four bindings below would cover; as stated above, they have no effect today."

## Task 2: Tiled refusal paragraph, bullets and sensor (commits `615e236`, `1aadb27`)

### Step 1 - reproduction on the final tree (scratch `_scrap/tiled_refusal_repro.py`, gitignored; each scenario a fresh process, fresh cache directory, `n_jobs=2` pooled first call)

```
A  leftover gradient_x_range.dat.tmp in tile_00, then n_jobs=1:     ok  ok  ok  ok            (4 of 4 succeed, every raster read)
B  del store["range"] on tile_00, then n_jobs=1:                    StorePurgeRefusedError x4  (4 of 4 refused)
B  del store["range"] on tile_00, then n_jobs=2:                    ok ok StorePurgeRefusedError StorePurgeRefusedError  (2 of 4 refused)
C  same drop on an instance that never ran pooled, n_jobs=1:        ok  ok  ok  ok            (4 of 4 succeed)
D  lone range.dat only, then n_jobs=1:                              ok x4
D  lone range.meta.json only, then n_jobs=1:                        ok x4
W  fresh generator for the call (workaround 2), n_jobs=1:           ok x3
W  drop the tile's generator + shutil.rmtree(<cache_path>/tile_00), then n_jobs=1: ok x3
drop routes del / pop / popitem / clear, then n_jobs=1:             StorePurgeRefusedError for all four
```

The `n_jobs=1` refusal after a pooled run is deterministic (4 of 4); at `n_jobs=2` it is random (2 of 4 in this run); `n_jobs=1` on an instance that never ran pooled works (4 of 4). The trigger sits in `tile_00` because of the deferred `verbose=50` masking.

### Step 2 - sensor (commit `615e236`, `test(tiled)`)

`test_regenerate_at_n_jobs_1_after_a_pooled_run_tolerates_a_leftover_temporary_but_refuses_a_dropped_codec_pair`: (a) pooled `generate(["range"])`, a 64-byte `gradient_x_range.dat.tmp` planted with `get_memmap_tmp_path(...)` in `tile_00`, `generate(["gradient_x_range"], n_jobs=1)` succeeds and every raster reads after `gc.collect()`; (b) a second instance, pooled run, `del store["range"]` on `tile_00` (codec pair confirmed on disk), `generate(["range"], n_jobs=1)` raises `StorePurgeRefusedError`. Passes on the final tree (`10 passed` for the file).

Mutation proof for (a): the store module replaced by `git show 7094dde:src/pc2img/image_cache/disk_backed_image_store.py` (six-member gate) and the test run:

```
E   GSEGUtils.lazy_disk_cache.disk_backed_store.StorePurgeRefusedError: Refusing to purge 'gradient_x_range': this store was constructed by process ... and purge was called from process ...
FAILED tests/test_tiled_generator.py::test_regenerate_at_n_jobs_1_after_a_pooled_run_tolerates_a_leftover_temporary_but_refuses_a_dropped_codec_pair
1 failed, 9 deselected
```

File restored with `git checkout --`, `git diff --stat` empty. Part (b) under the same restored six-member gate: the scratch scenario B at `n_jobs=1` printed `StorePurgeRefusedError` twice, so (b) is unchanged by the gate (it pins the documented limit).

### Step 3 - docstring (commit `1aadb27`, `docs(tiled)`)

The ownership/refusal paragraph now says: whenever the work runs in a worker pool each tile store is constructed in a worker and owned by it for good; `purge` is refused from any other process; `add_image_to_store` purges first when the key is tracked or its `<key>.npy` is on disk; a later `generate()` requesting an untracked feature whose codec pair is still in the tile directory (dropped with `del`, `pop`, `popitem` or `clear` while offloaded) raises `StorePurgeRefusedError` when `_process_tile` runs in a non-owner process, pool-random, always at `n_jobs=1` after a pooled run; leftover temporary files, a lone `.meta.json` or a lone `.dat` do not trigger it. Bullet 1 is now "use `n_jobs=1` for every call on an instance that will be purged from or overwritten; an instance that has run in a pool once is owned by its workers for good". The old trigger wording (`has to overwrite a key`) is gone.

```
grep -c 'for every call on an instance' -> 1 ; grep -ci 'do not trigger it' -> 1 ; refusal-paragraph-ok
AST, docstrings stripped, HEAD (615e236, the step-2 commit) vs working file: identical
tests/test_hygiene.py -k planning_vocabulary -> 82 passed; ruff check clean; ruff format --check clean (37 files)
```

## Task 3: MIGRATION-v0.11.md (commit `1fa8bb7`, `docs(migration)`)

- **BC-P2I-030**: origin cell gains `321d68c`; the round counts are quoted from `07-16-SUMMARY.md` `## Twelve-round measurement (arrays read)` ("0 of 12 rounds failing after the change (`failures: 0 / 12`) against 12 of 12 before (`failures: 12 / 12`), with every raster read after each call"); a bold **Disk persistence after a pooled run** group states the GC-ownership rule and the persistence it causes with its two routes and the `mkdtemp` clause; the sentence that repeated `generate()` never triggered the refusal is replaced by the reproduced trigger (pool-random 2 of 4 at `n_jobs=2`, 4 of 4 at `n_jobs=1`, leftovers tolerated per BC-P2I-027); corrected first route; "one `_process_tile` call per tile"; "whenever the work runs in a worker pool"; cross-reference to BC-P2I-028.
- **BC-P2I-027**: origin gains `b2a3baa`; the six-member description is replaced by the hard (tracked or `<key>.npy` on disk) / soft (`.meta.json` or `.dat`, only the exact process-identity refusal tolerated) gate, temporary names not consulted, the converse (a non-owner can add over leftovers but cannot replace a key whose codec pair is on disk), registrations qualified to "registered with this store", and the non-owner caveat (cannot disarm a retained dropped entry; unreachable from the pipeline, which never drops entries).
- **BC-P2I-028**: origin gains `3d0b43d`; the duplicate-id `ValueError` is added; `TiledPointCloudImageGenerator` added to `affected_symbols` in both the table and `BC_ENTRIES`.
- **Verifier**: two new probes (duplicate ids expect `ValueError`; owner-process durable re-add over a lone memmap with `purge_disk_on_gc=False` serves `1.0`); the 030 comments updated.

```
extracted verifier (uv run --frozen): [ok] verified 30 entries   (also re-run after the generated_at re-stamp)
ruff check --select E,F,W --ignore E501 on the extracted file: All checks passed!
'duplicate tile ids were accepted' in extracted file: 1 ; 'lone memmap': 3
mutation 1 (duplicate-id probe flipped to expect no exception): [fail] ... BC-P2I-028: duplicate tile ids were accepted at construction   (exit 1)
mutation 2 (lone-memmap probe flipped to expect 0.0):           [fail] ... BC-P2I-027: a re-add over a lone memmap did not serve the replacement   (exit 1)
Summary tally re-derived (awk): severity should-review 20, informational 5, must-edit 1, additive 4 (= 30);
  category dep-constraint 7, error-behavior 6, semantic-change 6, additive-or-fixed 5, signature-shape 3, surface-removed 2, on-disk-format 1 -> unchanged, matches the Summary text
generated_at re-stamped 2026-10-02T14:21:07Z; target_ref "v0.11.0" unchanged; 30 BC rows; 030 header is one row
row-030-ok ; rows-027-028-ok (all required wording greps >= 1; 'did not trigger it' and 'six derived files' are gone)
```

Claims in the record that the verifier does not assert were each reproduced by a scratch script on the final tree before being written (all in gitignored `_scrap/`):

- Persistence: with `enable_caching=True` and a configured `cache_path`, after releasing the results and then the generator all six files (`range.dat`, `.meta.json`, `.npy` for both tiles) remain. With `enable_caching=True` and no `cache_path`, the `mkdtemp` directory keeps `range.dat`, `range.meta.json`, `range.npy` after the generator is dropped.
- Non-owner caveat (forked child, store built in the parent, entry retained, then `del store["k"]`): the overwrite is accepted and the replacement reads `1.0`; after the retained reference is collected the `.dat` is gone while the open memmap still reads `1.0`.
- Gate: `tests/test_image_store.py -k "leftover or codec_pair_is_still or durable_lone or upstream_builders"` -> `7 passed, 115 deselected`.

## Deviations from Plan

### Auto-fixed Issues

None.

### Observations (not deviations)

1. **Default-directory persistence is narrower than the 07-16 docstring sentence reads.** With the default `LazyDiskCacheConfig` (`enable_caching=False`), a pooled run writes no files; each tile gets an empty `mkdtemp` directory that is never removed. Files persist only when caching is enabled (measured above). The record says so precisely. The class docstring sentence added by 07-16 ("That includes the default temporary directory a store creates with `tempfile.mkdtemp` when no `cache_path` is configured") is true for the directory and for the files when caching is enabled; this plan's scope was the refusal paragraph and bullets only, so I left it untouched. Worth a line in the round-3 review if the owner wants the docstring to carry the same qualification.
2. `uv run --frozen` rebuilt and reinstalled the editable `pc2img` on each verifier run (no lock change; `uv.lock` unmodified, `uv lock --check` clean at the end).
3. A scratch script of mine globbed `/tmp` for one run (a path mistake); read-only, no files changed.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or trust-boundary file access; the plan's T-07-59 (documentation describing behaviour that is not what ships) is mitigated by the reproductions above, the tiled-level sensor and the two verifier probes; T-07-60 by the hygiene gate (88 passed for the whole file at the final tree).

## Final tree checks

```
uv run --no-sync pytest -q -p no:cacheprovider -> 387 passed, 78 warnings in 8.37s
uv lock --check -> Resolved 137 packages; grep -c pypi.nvidia.com uv.lock -> 0
ruff check src tests -> All checks passed; ruff format --check src tests -> 37 files already formatted
tests/test_hygiene.py (whole file) -> 88 passed
```

`commits: 4` is measured with `git rev-list --count becfe30..HEAD` at SUMMARY time (before the SUMMARY commit).

## Commits

- `e3900b0` build(deps): the sources note no longer gives the inert bindings a purpose
- `615e236` test(tiled): leftover temporary tolerated, dropped codec pair refused after a pooled run
- `1aadb27` docs(tiled): when tile stores refuse, and which workaround holds after a pooled run
- `1fa8bb7` docs(migration): pooled results do not own gc deletion, the adoptable-artefact gate, duplicate tile ids rejected

## Review still owed (orchestrator/owner, not executor)

Per the plan's verification block and the global gap-closure rule, this round's diff gets its own review before 07-07 resumes (review round 3 of a maximum of 3 if it finds anything): `/gsd-code-review 7 --files src/pc2img/tiled_generator.py tests/test_tiled_generator.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_image_store.py pyproject.toml` and `/code-review 7094dde high`, findings landed with `/gsd-consolidate-findings`; then 07-07 Tasks 1-2 re-run on the new tip with a new `D03_SHA:` line. No `07-UAT.md` gap `status:` field was changed, no requirement was marked complete, and 07-07..07-11 and 07-15 were not touched. The record stays at thirty entries.

## Self-Check: PASSED

- Files exist and carry the changes: `pyproject.toml`, `src/pc2img/tiled_generator.py`, `tests/test_tiled_generator.py`, `.planning/MIGRATION-v0.11.md`.
- Commits `e3900b0`, `615e236`, `1aadb27`, `1fa8bb7` present on `gsd/phase-07-gsegutils-0-6-adoption-0-11-0-release`.
- All task acceptance criteria and the plan-level verification commands re-run and passing; verifier `[ok] verified 30 entries`.
