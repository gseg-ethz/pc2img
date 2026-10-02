---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 17
subsystem: image-store
tags: [gsegutils-0.6, gap-closure, purge, process-identity, leftover-artefacts, regression-test]
status: complete

requires:
  - phase: 07-13
    provides: "the overwrite route that purges a tracked or on-disk key (whose six-member presence gate this plan narrows)"
provides:
  - "add_image_to_store: a tracked key or an on-disk <key>.npy purges unconditionally (every refusal propagates); a lone <key>.meta.json or <key>.dat attempts purge and tolerates exactly StorePurgeRefusedError (type(exc) is StorePurgeRefusedError), subclasses propagate; temporary names are not consulted"
  - "module predicates _adoptable_artefact_exists (get_npy_path) and _leftover_artefact_exists (get_meta_path, get_memmap_path); the six-member helper and the three temporary-name builder imports are gone"
  - "test_non_owner_add_over_a_leftover_is_not_refused[raw_dat|raw_dat_tmp|durable_lone_dat|lone_meta] (forked non-owner), test_non_owner_add_over_a_dropped_codec_pair_is_still_refused, test_owner_add_over_a_durable_lone_memmap_replaces_it, test_presence_gate_uses_only_upstream_builders_of_known_shape"
  - "store docstrings: hard/soft gate, the converse, registrations are per store, non-owner caveat (docstring-only, AST-identical)"
affects: [07-18 migration record (cites the fix commit b2a3baa42838fff3777acb2aba831fd01b7ec4eb in BC-P2I-027)]

actuals:
  tokens: 3354
  tasks: 2
  commits: 3
plan_head_before: 85b491c68171e7d088576a198363ffcb15f22f74
plan_head_after: 70d0730afe0cb4af226c35725967153ba0ebf5f4

tech-stack:
  added: []
  patterns:
    - "gate on what the base store's startup scan adopts (<key>.npy), not on every file purge would remove"
    - "tolerate an upstream refusal by exact type, so a new subclass fails closed"

key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_image_store.py

key-decisions:
  - "Hard/soft overwrite gate (owner-approved soft gate): tracked or on-disk <key>.npy -> unconditional purge; lone .meta.json/.dat -> purge with only the exact process-identity refusal tolerated"
  - "Temporary names (.dat.tmp, .npy.tmp, .meta.json.tmp) are not consulted: writers overwrite them, so they carry no correctness weight"
  - "Accepted, documented limit: in a non-owner process an overwrite cannot disarm a still-retained reference to a dropped entry; unreachable from the pipeline, which never drops entries"

requirements-completed: []

coverage:
  - id: D1
    description: "A process that did not construct the store can add a key over a raw .dat, a .dat.tmp, a durable lone .dat or a lone .meta.json and reads the new raster back"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_non_owner_add_over_a_leftover_is_not_refused"
        status: pass
    human_judgment: false
  - id: D2
    description: "A non-owner is still refused for a key whose <key>.npy is on disk; an owner replaces a durable lone memmap"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_non_owner_add_over_a_dropped_codec_pair_is_still_refused"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py#test_owner_add_over_a_durable_lone_memmap_replaces_it"
        status: pass
    human_judgment: false
  - id: D3
    description: "The presence gate names exactly three upstream builders of pinned shape; no temporary-name builder remains in the module"
    requirement: DEP-05
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_presence_gate_uses_only_upstream_builders_of_known_shape"
        status: pass
    human_judgment: false
  - id: D4
    description: "Docstrings state the hard/soft gate, the converse, the per-store registration qualification and the non-owner caveat; only docstrings changed"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "AST with docstrings stripped, Task-1 fix commit vs working file: identical"
        status: pass
    human_judgment: true
    rationale: "The AST check proves nothing but docstrings changed; whether the prose is accurate and clear is a reader judgment, and 07-18 records the behaviour in the migration notes"
---

# Phase 07 Plan 17: Narrowed overwrite gate for non-owner processes (G1-WR-01, G1-IN-01, store half of G1-WR-02) Summary

**`add_image_to_store` now refuses a non-owner process only for a key that is tracked or whose `<key>.npy` is on disk; a lone `.dat`, `.dat.tmp` or `.meta.json` no longer makes a forked non-owner child fail (4 of 4 leftover kinds exit 3 before, exit 0 after), and the hand copy of upstream's artefact set shrank from six builders to three, pinned against `paths.STORE_PATH_BUILDERS`.**

Duration: about 5 minutes (commits 2026-10-02T14:11Z to 14:13Z), 2 tasks, 2 files.

## Step 0: measured adoption rule of the base store's startup scan

Fresh `DiskBackedImageStore` over a directory holding exactly the files shown (scratch script, GSEGUtils 0.6.0):

```
lone_npy: adopted=True  read=KeyError  files=['k.npy']
lone_meta: adopted=False  read=KeyError  files=['k.meta.json']
lone_dat: adopted=False  read=KeyError  files=['k.dat']
pair: adopted=True  read=array([1., 1.], dtype=float32)  files=['k.dat', 'k.meta.json', 'k.npy']
```

Only `<key>.npy` is adopted, and only the pair is served. The hard set is therefore the `.npy` alone; the `.meta.json` and `.dat` are the soft set because a `.dat` can still be the recorded path of a dropped entry whose cleanup hook is armed in this process, and `purge` is the only route that detaches it.

## What was done

### Task 1 (tracer): narrow the gate, red on HEAD then green

RED commit `589f5c2` (`test(image_store)`), run on the unfixed source (HEAD `85b491c`), selection `-k "leftover or codec_pair_is_still or durable_lone or upstream_builders"`:

```
E       AssertionError: a raw_dat leftover made a non-owner add fail
E       assert 3 == 0
E       AssertionError: a raw_dat_tmp leftover made a non-owner add fail
E       assert 3 == 0
E       AssertionError: a durable_lone_dat leftover made a non-owner add fail
E       assert 3 == 0
E       AssertionError: a lone_meta leftover made a non-owner add fail
E       assert 3 == 0
E           AssertionError: the store module still names get_npy_tmp_path
FAILED tests/test_image_store.py::test_non_owner_add_over_a_leftover_is_not_refused[raw_dat]
FAILED tests/test_image_store.py::test_non_owner_add_over_a_leftover_is_not_refused[raw_dat_tmp]
FAILED tests/test_image_store.py::test_non_owner_add_over_a_leftover_is_not_refused[durable_lone_dat]
FAILED tests/test_image_store.py::test_non_owner_add_over_a_leftover_is_not_refused[lone_meta]
FAILED tests/test_image_store.py::test_presence_gate_uses_only_upstream_builders_of_known_shape
5 failed, 2 passed, 115 deselected, 12 warnings in 0.64s
```

The two passes are the pins that are green before and after: the non-owner codec-pair refusal and the owner durable-memmap replacement. Exit code 3 is `StorePurgeRefusedError` in the forked non-owner child.

GREEN commit `b2a3baa42838fff3777acb2aba831fd01b7ec4eb` (`fix(image_store)`):

```
13 passed, 109 deselected, 12 warnings in 0.76s     (the 13 named tests: 4 leftover kinds, codec-pair pin, durable owner, shape pin, 4 drop routes, GC variant, new-key pin)
122 passed, 12 warnings in 1.65s                     (tests/test_image_store.py)
386 passed, 74 warnings in 7.85s                     (full suite)
ruff check: All checks passed!   ruff format --check: 37 files already formatted
```

The plan's verify greps all held: one `_adoptable_artefact_exists` def, one `_leftover_artefact_exists` def, one `if type(exc) is not StorePurgeRefusedError:`, one containment-first `get_npy_path(self.cache_dir, img_name)`, and `gate-shape-ok` (no `_has_on_disk_artefact` or temporary-name builder outside comments).

#### Mutation checks (by running code, file restored after each; `-k` selection of the 13 tests)

- (a) six-member gate restored: 5 failed, 8 passed. Failures: the four `leftover_is_not_refused` cases and the builder-shape test.
- (b) soft `elif` branch deleted: 1 failed, 12 passed. Failure: `test_retained_reference_to_a_dropped_entry_does_not_delete_the_replacement_memmap_on_gc`.
- (c) `.npy` removed from the hard predicate (as the plan specified): 1 failed, 12 passed. Failure: `test_non_owner_add_over_a_dropped_codec_pair_is_still_refused` only. **This differs from the plan's prediction** that the four drop-route tests would fail: in the owner process the soft branch still reaches the codec pair through its `.meta.json`, so the owner-side drop routes stay green. What guards the hard `.npy` member is the non-owner pin, and it did fail.
- (c2) additional mutation, `.npy` removed from the hard predicate AND `.meta.json` removed from the soft predicate: 4 failed, 9 passed. Failures: `test_overwrite_after_a_drop_route_never_leaves_a_stale_raster_for_a_fresh_store[del|pop|clear]` and the non-owner codec-pair pin. `[popitem]` stayed green under (c2), so that drop route is covered by the soft branch's `.dat` leg or by the entry state after `popitem` rather than by the `.npy` check; not investigated further.

### Task 2: docstrings (docstring-only)

Commit `70d0730` (`docs(image_store)`): "Ordering" step 3 now states the hard gate (tracked or on-disk `<key>.npy`, refusals surface, a non-owner cannot replace a key whose codec pair is on disk), the soft gate (lone `.meta.json`/`.dat`, only a process-identity refusal tolerated, foreign/aliased refusals surface, temporary names not consulted), and qualifies the retained-reference claim to hooks registered with this store (pickled copies hold their own registrations; the tiled generator disarms the copies it returns from a pooled run). The first "Overwrite failures" bullet says a non-owner is refused only for a tracked key or an on-disk `<key>.npy`. A "Non-owner caveat" paragraph states that in a non-owner process an overwrite cannot disarm a still-retained reference to a dropped entry, and that the pc2img pipeline never drops entries. The class "Removal" paragraph and the test-file section comments were updated.

AST with docstrings stripped, Task-1 fix commit versus the working file, run before committing: `identical`. Docstring phrase greps: converse 1, registered with this store 1, temporary name 2, cannot disarm 1, never drops entries 1. `tests/test_image_store.py` plus `tests/test_hygiene.py -k "not benchmark"`: `210 passed, 12 warnings in 2.05s`. Full suite after the last commit: `386 passed, 74 warnings in 7.45s`.

## Deviations from Plan

None in code or tests. Two observations, neither a deviation:

- Mutation (c) did not fail the four drop-route tests as the plan predicted (see above); the extra mutation (c2) and the non-owner pin are what guard the hard member. Recorded verbatim rather than adjusted.
- The `_scrap/` scratch location named in the plan was not used; the adoption-measurement script lived in the session scratchpad and is not committed.

## Auth gates

None.

## Known Stubs

None.

## Threat Flags

None. The tolerated-refusal branch is the surface the plan's T-07-57 already covers: it tolerates `type(exc) is StorePurgeRefusedError` only, so a foreign or aliased-artefact refusal (subclasses) still propagates.

## Follow-ups (not executed here)

Per the plan's verification section, orchestrator/owner steps, no GitHub interaction: this round's diff gets its own review (`/gsd-code-review 7 --files src/pc2img/tiled_generator.py tests/test_tiled_generator.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_image_store.py pyproject.toml` and `/code-review 7094dde high`), findings landed with `/gsd-consolidate-findings`, then 07-07 Tasks 1-2 re-run on the new tip. No `07-UAT.md` gap `status:` field was changed and no requirement was marked complete.

## Self-Check: PASSED

- Files: `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_image_store.py` exist and are committed.
- Commits: `589f5c2`, `b2a3baa`, `70d0730` present on `gsd/phase-07-gsegutils-0-6-adoption-0-11-0-release`; `git rev-list --count 85b491c..HEAD` was 3 before this SUMMARY commit.
- All task acceptance criteria and the plan-level verification commands re-run and passing.
