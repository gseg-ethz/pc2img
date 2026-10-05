---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 22
subsystem: tiled-generator-and-image-store-docs
tags: [gap-closure, round-4, docs-only, migration-record, known-limitations, GSEGUtils-83]
status: complete

requires:
  - phase: 07-19
    provides: "always-disarm, failed-batch reset"
  - phase: 07-20
    provides: "pre-write linked-path refusal"
  - phase: 07-21
    provides: "round-3 docstrings and BC-P2I-027/030 that this round corrects"
provides:
  - "tiled_generator.py: failed-batch, ownership, sidecar-inheritance and Known limitations docstrings as measured (docstring/comment-only, AST-identical)"
  - "disk_backed_image_store.py: link refusal by location, dangling/adopted links, symlink loop, caveat reachability (docstring-only, AST-identical)"
  - "tests/test_tiled_generator.py: two docstring sentences that repeated a false claim corrected (docstring-only, AST-identical)"
  - "MIGRATION-v0.11.md BC-P2I-030 and BC-P2I-027 amended to the measured behaviour; thirty entries; verifier green"
affects: [07-07 resume needs a new D03_SHA line (shipped files changed); reading-check review of this docs-only diff is an orchestrator/owner step]

actuals:
  tokens: 13378
  tasks: 3
  commits: 3
plan_head_before: e9a6ae4eea33d5a5c7e04205945fd85f9c2ede86
plan_head_after: b57c97b92e249717002a5c9be1f2f7af99c9bc97

tech-stack:
  added: []
  patterns:
    - "docs-only round: every touched .py file proven identical to the base with docstrings stripped from its AST"

key-files:
  created: []
  modified:
    - src/pc2img/tiled_generator.py
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_tiled_generator.py
    - .planning/MIGRATION-v0.11.md

key-decisions:
  - "The inside-except hazard REPRODUCED with the orchestrator's recipe (failed n_jobs=1 call, retry at n_jobs=1), so it is written, but worded by its measured mechanism: it is not specific to the except block (the retry after the block loses the files too); the failed call's armed entries stay alive until the garbage collector runs"
  - "The planner's pooled variants did not reproduce and are recorded as such; the known-limitations sentence names only the shape that reproduces and says the pooled failure and the default config lost nothing"
  - "Claims the executor did not re-measure (the reviewer's 'accepted before the check existed' on c1b813d) were left out of the shipped text"

requirements-completed: []

coverage:
  - id: D1
    description: "Tiled docstrings and BC-P2I-030 describe the failed-batch path, ownership, sidecar inheritance and known limitations as measured, naming GSEGUtils#83 and 0.11.1"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "Measurements (a)-(e), (c2); AST identity tiled_generator.py and tests/test_tiled_generator.py: identical; tests/test_tiled_generator.py + tests/test_hygiene.py: 103 passed"
        status: pass
    human_judgment: true
    rationale: "Whether the prose reads accurately to an outsider is a reading judgment; each factual clause is backed by a measurement below"
  - id: D2
    description: "Store docstrings and BC-P2I-027 state link refusal by location, dangling/adopted links, the loop RuntimeError and the caveat's failed-call route"
    requirement: BC-01
    verification:
      - kind: command
        ref: "Measurements (f)-(i); AST identity disk_backed_image_store.py: identical; tests/test_image_store.py + tests/test_hygiene.py: 221 passed"
        status: pass
    human_judgment: true
    rationale: "Prose accuracy for downstream readers is a reading judgment"
  - id: D3
    description: "The record stays at thirty entries; the verifier is green"
    requirement: BC-01
    verification:
      - kind: command
        ref: "extracted verifier (uv run --frozen): [ok] verified 30 entries; awk tally re-derived, no category change"
        status: pass
    human_judgment: false
---

# Phase 07 Plan 22: Docs-only gap round 4 Summary

The tiled and store docstrings and BC-P2I-027/030 now describe the failed-batch, ownership, sidecar-inheritance, link-refusal and caveat behaviour as measured, with a Known limitations paragraph that names GSEGUtils#83 and pc2img 0.11.1 as where the behaviour fixes go; zero behaviour change, proven by docstring-stripped AST identity for all three touched `.py` files.

Duration: about 25 minutes (started 2026-10-05T09:50Z, finished 10:16Z). Tasks 3, files 4, commits 3 (plus this SUMMARY commit).

## Commits

| Task | Commit | Message |
| ---- | ------ | ------- |
| 1 | `a507165` | docs(tiled): failed-batch path, ownership and sidecar inheritance as measured; known limitations |
| 2 | `626683e` | docs(image_store): link refusal by location, the loop case, and where the caveat is reached |
| 3 | `b57c97b` | docs(migration): failed-batch path, sidecar inheritance, link refusal by location, known limitations and their upstream root cause |

## What changed

- `tiled_generator.py` (class docstring, `generate()` docstring, except-handler comment, `_release_gc_ownership` docstring): the failed-batch paragraph is rewritten (generators that existed before the call; with a `cache_path` the retry adopts the finished tiles' codec pairs; without one it rebuilds every tile store in a new temporary directory, recomputes everything and leaves the old directories; `enable_caching=False` means the reset protects nothing on disk; a failing first `n_jobs=1` call keeps no generators; entries a failed call added to kept stores stay armed). The ownership sentence now reads "the calling process owns a tile's store if that store was built by an `n_jobs=1` call". New paragraph on the disarm being recorded in each key's `.meta.json` sidecar and inherited by any later store, history-dependent. New **Known limitations** paragraph (GSEGUtils#83, 0.11.1).
- `disk_backed_image_store.py`: `_refuse_linked_write_path`, the class docstring's "Two limits", `add_image_to_store` step 3 and the aliased bullet state that the refusal classifies by where the link resolves (adopted-payload and dangling in-cache links refused as aliased, dangling not clearable via `purge`, symlink loop raises a bare `RuntimeError`). The non-owner caveat no longer says `generate()` results cannot reach it: results of a successful call do not, entries a failed `n_jobs=1` call added do (measured).
- `tests/test_tiled_generator.py`: the module docstring sentence and `test_a_failing_sequential_call_keeps_the_tile_generators` docstring corrected; no test body touched.
- `MIGRATION-v0.11.md`: BC-P2I-030 (ownership, sidecar inheritance, Failed batch, Known limitations block replacing "A fix ... is planned after 0.11.0") and BC-P2I-027 (link refusal by location, loop, caveat) amended; `generated_at` re-stamped to 2026-10-05T10:14:57Z, `target_ref` unchanged.

## Measurements

All run on the committed round-3 tree (`e9a6ae4`, `git status --porcelain -- src tests` empty, `cb85baa` an ancestor), each a fresh process and fresh directory, scratch scripts in the session scratchpad (not in the repo). Two tiles: `tile_00` carries an `intensity` field, `tile_01` does not (so a request for `scalar_field_intensity` fails on `tile_01`). The failing call raised `AttributeError` at `n_jobs=1` and `IndexError` when pooled; the plan said only "raises". Verbatim output follows.

### (a) G3-WR-01 kept store after a failing `n_jobs=1` call

```
failed: AttributeError
{'range': False, 'scalar_field_intensity': True, 'gradient_x_range': True}
['tile_00', 'tile_01']
```
(sequence: `generate(["range"], n_jobs=1)`, then `generate(["gradient_x_range", "scalar_field_intensity"], n_jobs=1)` raises; the dict is `{key: entry.purge_disk_on_gc}` for `tile_00`'s kept store.) Planner's expectation held; the two keys the failing call added are `True`.

### (b) G3-IN-02 ownership and kept generators

(i) failing FIRST `n_jobs=1` call:
```
failed: AttributeError
image_generators after failing first n_jobs=1 call: {}
```
(ii) pooled call, pooled failing call, `n_jobs=1` retry, `purge` from the parent:
```
pooled failed: IndexError
gens after pooled failure: []
owner pid == getpid: 407077 407077
purge from parent: succeeded
```
(iii) a sequential build, owner pid against the calling pid:
```
os.getpid(): 407179
[('_owner_pid', 407179)]
purge from calling process: succeeded
```

### (c) G3-WR-03 retry without a `cache_path` (`TMPDIR` on a fresh directory)

```
TMPDIR: /tmp/tmp08jdfp7a
before: {'tile_00': '/tmp/tmp08jdfp7a/tmpaj_mf85d', 'tile_01': '/tmp/tmp08jdfp7a/tmp13urllpe'}
pooled failed: IndexError
after: {'tile_00': '/tmp/tmp08jdfp7a/tmp8rz9xq86', 'tile_01': '/tmp/tmp08jdfp7a/tmp1rj7743j'}
all changed: True
old dir /tmp/tmp08jdfp7a/tmpaj_mf85d files: ['range.dat', 'range.meta.json', 'range.meta.json.tmp', 'range.npy', 'range.npy.tmp', 'scalar_field_intensity.dat']
old dir /tmp/tmp08jdfp7a/tmp13urllpe files: ['range.dat', 'range.meta.json', 'range.npy']
new dir /tmp/tmp08jdfp7a/tmp8rz9xq86 files: ['range.dat', 'range.meta.json', 'range.npy']
new dir /tmp/tmp08jdfp7a/tmp1rj7743j files: ['range.dat', 'range.meta.json', 'range.npy']
```
(c2) the same sequence WITH a `cache_path` (adoption; added by the executor to back the "adopts" sentence):
```
pooled failed: IndexError
cache_dir unchanged: True {'tile_00': '/tmp/tmpf5i_lbnw/tile_00', 'tile_01': '/tmp/tmpf5i_lbnw/tile_01'}
tile_01 range.npy/range.meta.json mtimes unchanged: False | range.dat unchanged: False
a fresh store over tile_00 tracks (startup scan): ['range', 'scalar_field_intensity']
rebuilt generator's store tracks: ['range', 'scalar_field_intensity']
```
File mtimes change on a retry (pickling rewrites the pair), so "adopts" is stated through the startup scan and the unchanged directory, not through untouched files. The shipped text does not claim untouched files.

### (d) G3-WR-04 sidecar inheritance (fresh `DiskBackedImageStore` over `<cache_path>/tile_00` asking `purge_disk_on_gc=True`)

```
sequence of n_jobs: (2,)
meta.json purge_disk_on_gc: True | keys: ['automatic_offloading', 'dtype', 'enable_caching', 'lazy_disk_cache_class', 'purge_disk_on_gc', 'schema_version', 'shape']
fresh store asking purge_disk_on_gc=True -> range.purge_disk_on_gc: True
sequence of n_jobs: (1, 2)
meta.json purge_disk_on_gc: False | keys: [same]
fresh store asking purge_disk_on_gc=True -> range.purge_disk_on_gc: False
sequence of n_jobs: (2, 2)
meta.json purge_disk_on_gc: False | keys: [same]
fresh store asking purge_disk_on_gc=True -> range.purge_disk_on_gc: False
```
Extra: sequences `(1,)` and `(1, 1)` write no `range.meta.json` at all (`FileNotFoundError` on the read; only pickling in a pooled run writes the codec pair). The shipped text says "when the codec pair is written (by the pickling of a pooled run)".

### (e) G3-WR-05 the retry hazard

Orchestrator's recipe (exact script; first call `n_jobs=1`, retry inside the `except` at `n_jobs=1`), 3 runs:
```
### run 1
failed: AttributeError
dat after retry: True
dat after exc released: False
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmpcqcauqxk/t0/range.dat'
### run 2
failed: AttributeError
dat after retry: True
dat after exc released: False
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmpdmmhoppe/t0/range.dat'
### run 3
failed: AttributeError
dat after retry: True
dat after exc released: False
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmpa9rn83zl/t0/range.dat'
```
**Verdict: REPRODUCED 3 of 3 with the orchestrator's recipe.** The loss is NOT specific to the `except` block. Control, same recipe with the retry AFTER the block, 3 runs: `dat after retry (after block): True`, `dat after exc released: False`, `FileNotFoundError .../t0/range.dat`, 3 of 3. Mechanism (executor probe): after a failing `n_jobs=1` call with no retry, the failed call's files are still on disk after the `except` block and are gone after `gc.collect()`:
```
failed: AttributeError | generators kept: []
t0 files after block, before gc.collect(): no t0 ['range.dat', 'scalar_field_intensity.dat']
tile_00 files after gc.collect(): []
```
(the failed call's armed entries stay alive until the garbage collector runs; collecting them unlinks the `.dat` files the retry rewrote). The plan's variants (pooled first call at `n_jobs=-1`, pooled failing call, retry at `n_jobs=-1`), 3 runs each, did NOT reproduce:
```
pooled_inside  runs 1-3: failed: IndexError / retried inside block / tile_00 range read: (8, 8) / tile_01 range read: (8, 8) / OUTCOME: all readable
pooled_after   runs 1-3: failed: IndexError / tile_00 range read: (8, 8) / tile_01 range read: (8, 8) / OUTCOME: all readable
```
Other controls, 3 runs each unless noted:
```
collect_then_retry (failing n_jobs=1, gc.collect() before the retry): OUTCOME: all readable (3/3)
default_config (enable_caching=False, retry inside the block at n_jobs=1): OUTCOME: all readable (3/3)
fresh generator over a fresh cache_path, retry inside the block (1 run): OUTCOME: all readable
```
The planner's non-reproduction came from pooled/default `n_jobs` first calls; the hazard needs a failing `n_jobs=1` call (the pooled failure's generators live in workers, not in the parent's traceback). The shipped sentence is therefore worded: a failing `n_jobs=1` call retried at `n_jobs=1` with a `cache_path`, whether inside or after the block, until the garbage collector has run; mitigations measured above; pooled failure and `enable_caching=False` lost nothing.

### (f) link to a regular in-cache payload

```
(f) k.dat -> /tmp/tmpat9ikazp/payload.bin (regular in-cache file)
(f) add: StorePurgeAliasedArtefactError | StorePurgeRefusedError subclass: True
(f) payload.bin size after: 256
```

### (g) dangling link

```
(g) g.dat -> /tmp/tmpat9ikazp/gone.bin exists: False
(g) add: StorePurgeAliasedArtefactError
(g) purge: KeyError | 'g'
(g) g.dat still a symlink: True
```

### (h) symlink loop at a temporary name

```
(h) add: RuntimeError | Symlink loop from '/tmp/tmpat9ikazp/loop.dat.tmp' | StorePurgeRefusedError subclass: False | RuntimeError subclass: True
```

### (i) the caveat via a failed sequential call (pooled call, failing `n_jobs=1` call, hold, `del`, regenerate at `n_jobs=1`, release)

```
failing n_jobs=1 call: AttributeError
held purge_disk_on_gc before release: True
replacement .dat exists before release: True
replacement .dat exists after release: False
offload+read: FileNotFoundError /tmp/tmpqef81hlx/tile_00/gradient_x_range.dat
```

## Verification

- AST identity (docstrings stripped, working file against the base, run before each commit and again over the whole round against `e9a6ae4`): `src/pc2img/tiled_generator.py` identical; `src/pc2img/image_cache/disk_backed_image_store.py` identical; `tests/test_tiled_generator.py` identical. Comments are not in the AST and one handler comment was reworded (comment-only).
- Task 1 gates: `tiled-docs-ok`; `tests/test_tiled_generator.py` + `tests/test_hygiene.py`: 103 passed; `ruff check` and `ruff format --check` clean (two E501 in the test module docstring were rewrapped, docstring-only).
- Task 2 gates: `store-docs-ok`; `tests/test_image_store.py` + `tests/test_hygiene.py`: 221 passed; ruff clean.
- Task 3 gates: `thirty-rows`, `row-030-ok`, `row-027-ok`; verifier `uv run --frozen python _scrap/pc2img-migration-verifier.py` printed `[ok] verified 30 entries`; `ruff check --select E,F,W --ignore E501` on it clean.
- Tally re-derived with awk: 20 `should-review`, 1 `must-edit`, 5 `informational`, 4 `additive` (30 rows); `dep-constraint` 7; no category changed, the Summary section is unchanged.
- Full suite: `uv run --no-sync pytest -q -p no:cacheprovider`: 403 passed.
- Acceptance criteria re-run: all pass (see Verification gates above); the inside-except sentence is written because (e) reproduced, and it names GSEGUtils#83 and 0.11.1.

## Deviations from Plan

None in code. Two scope notes, neither a deviation from the plan's constraints.

1. The plan's recipe for (e) differed from the orchestrator's (the orchestrator's override was used, and the plan's pooled variants were run and recorded as non-reproducing). The shipped wording follows what reproduces and says the hazard is not specific to the `except` block, which differs from the owner's G3-WR-05 statement ("retry INSIDE the except block"); the owner's recipe is the one that reproduces, the "inside the block" part is not required.
2. Added measurement (c2) and the `(1,)`/`(1, 1)` no-sidecar observation, to avoid writing "adopts the codec pairs" and "the sidecar is inherited" unmeasured. The reviewer's claim that the refusal was "accepted before the check existed" (on `c1b813d`) was not re-measured, so it is not in the shipped text.

## Known Stubs

None. Docs only.

## Threat Flags

None. No new network, auth, file-access or schema surface; no code changed.

## Next Phase Readiness

- The paused 07-07 must re-run its Tasks 1-2 on the new tip with a new `D03_SHA:` line (shipped files changed, docstrings included). Orchestrator/owner step.
- Before 07-07 resumes: `/gsd-code-review 7 --files src/pc2img/tiled_generator.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_tiled_generator.py` and `/code-review cb85baa high`, findings landed with `/gsd-consolidate-findings` (the global review-discipline rule for gap-closure plans). Not run here.
- No `07-UAT.md` `status:` field changed, no requirement marked complete, 07-07..07-11 and 07-15 untouched, no GitHub interaction (GSEGUtils#83 referenced in text only).

## Self-Check: PASSED

- `src/pc2img/tiled_generator.py`, `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_tiled_generator.py`, `.planning/MIGRATION-v0.11.md` exist and carry the edits (commits `a507165`, `626683e`, `b57c97b` present in `git log`).
- `git rev-list --count e9a6ae4..HEAD` was 3 before this SUMMARY commit, matching `actuals.commits`.
