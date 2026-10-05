---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 21
subsystem: image-store-and-migration-record
tags: [gap-closure, round-3, docs, migration-record, verifier-probe, mutation-proof]
status: complete

requires:
  - phase: 07-19
    provides: "always-disarm (4b4add3), failed-batch reset (d00cfdb), the mixed-n_jobs twelve-round counts"
  - phase: 07-20
    provides: "pre-write linked-path refusal (e738cf4)"
provides:
  - "disk_backed_image_store.py: the non-owner caveat worded strictly from measurement (docstring-only, AST-identical to HEAD)"
  - "MIGRATION-v0.11.md BC-P2I-027: pre-write linked-path refusal, measured caveat, e738cf4"
  - "MIGRATION-v0.11.md BC-P2I-030: always-disarm rule, mixed-sequence counts, failed-batch reset, persistence as measured, 4b4add3 and d00cfdb"
  - "a 027 verifier probe that observes the finalizer detach and fails when the soft branch is removed from the CODE"
affects: [review round 4 of the round-3 diff precedes the 07-07 resume (orchestrator/owner step, not run here)]

actuals:
  tokens: 7870
  tasks: 2
  commits: 2
plan_head_before: 36d1efc89817b1837dc30b285580b5de46025a66
plan_head_after: 5549f7c144ab7f9144ffb5fc641ee83b1c6b75f4

tech-stack:
  added: []
  patterns:
    - "a verifier probe is proven by mutating the CODE under test in a scratch copy of src/, with the mutated tree's import proven before the result is trusted"

key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - .planning/MIGRATION-v0.11.md

key-decisions:
  - "The caveat is kept (route (c) reproduces) but worded with its precondition: it applies only while no <key>.npy exists for the key"
  - "The unpickled-copy route (b) is not named anywhere: it is refused, so it does not reach the caveat"
  - "The earlier pooled-only 0 of 12 / 12 of 12 sentence in BC-P2I-030 is left as it was; the new always-disarm sentence carries the mixed-sequence counts quoted from 07-19-SUMMARY.md"

requirements-completed: []

coverage:
  - id: D1
    description: "The non-owner caveat states what was measured: tiled generate() does not reach it, a key with its codec pair on disk is refused, a fork-inherited live entry with no .npy does reach it"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "_scrap/r3_caveat_a.py, _scrap/r3_caveat_bc.py (b and c); AST identity vs HEAD: identical; tests/test_hygiene.py"
        status: pass
    human_judgment: true
    rationale: "Whether the prose reads accurately to an outsider is a reading judgment; each factual clause is backed by a measurement below"
  - id: D2
    description: "BC-P2I-027 and BC-P2I-030 describe the round-3 tree; the record stays at thirty entries"
    requirement: BC-01
    verification:
      - kind: command
        ref: "extracted verifier (uv run --frozen): [ok] verified 30 entries; awk tally unchanged"
        status: pass
    human_judgment: true
    rationale: "Prose accuracy of the two rows is a reading judgment; behavioural claims were re-run on the final tree"
  - id: D3
    description: "The 027 detach probe fails when the soft branch is deleted from the code"
    requirement: BC-01
    verification:
      - kind: command
        ref: "PYTHONPATH=<scratch>/mut/src uv run --frozen python _scrap/pc2img-migration-verifier.py -> [fail] ... BC-P2I-027: collecting a dropped entry deleted the replacement's memmap (exit 1), import proven first"
        status: pass
    human_judgment: false
---

# Phase 7 Plan 21: Caveat from measurement, detach-observing 027 probe, 027/030 at round 3 Summary

The non-owner caveat now says what was measured (tiled `generate()` cannot reach it; it applies only while no `<key>.npy` exists for the key), BC-P2I-027/030 describe the round-3 tree, and the 027 verifier probe observes the finalizer detach and was shown to fail when the soft branch is deleted from the code.

Completed 2026-10-05. 2 tasks, 2 commits, 2 files.

## Commits

| Commit | Message |
|--------|---------|
| 3e91f7e | docs(image_store): the non-owner caveat worded from measurement after tiled results stopped owning gc deletion |
| 5549f7c | docs(migration): every tiled call disarms gc deletion, failed-batch reset, symlinked leftovers refused, a probe that observes the detach |

## Task 1: the caveat, re-measured on the round-3 tree (HEAD 36d1efc)

Instruments are in the gitignored `_scrap/` (`r3_caveat_a.py`, `r3_caveat_bc.py`).

**(a) The reviewer's five-step tiled route** (two tiles, `cache_path`, pooled `generate(["range"], n_jobs=2)`; `held = generate(["gradient_x_range"], n_jobs=1)`; `del store["gradient_x_range"]` on `tile_00`; `generate(["gradient_x_range"], n_jobs=1)`; `del held; gc.collect()`):

```
tile_00/gradient_x_range.dat exists: True /scratch/31_pc2img/_scrap/tmpccdrsnqp/tile_00/gradient_x_range.dat
offload+read: (8, 8) OK
```

The route is closed.

**(b) Unpickled-copy route** (`pickle.loads(pickle.dumps(store))` in a forked child; hold an entry, `del` it, re-add):

```
[b] parent: dat=True npy=False
[b] child after pickle round trip: dat=True npy=True
[b] child: add REFUSED StorePurgeRefusedError
[b] child exit code 3
```

Pickling wrote `<key>.npy`, so the add took the hard path and the non-owner was refused; nothing was lost. This route does not reach the caveat and is not named in the docstring or in the record.

**(c) Fork-inherited live, never-offloaded entry** (parent adds `k`, forks; child holds `store.store["k"]`, `del store["k"]`, re-adds, `del held; gc.collect()`):

```
[c] parent: dat=True npy=False
[c] child: add accepted; dat=True npy=False served=1.0
[c] child after collecting held: dat=False
[c] child: offload+read raised FileNotFoundError
[c] child exit code 0
```

It reproduces, so the paragraph is kept and describes exactly this shape, with the precondition "applies only while no `<key>.npy` exists for the key" (the case with the codec pair on disk is (b)).

**Docstring changes** (docstring-only): the Non-owner caveat paragraph rewritten from (a)-(c); the sentence claiming `generate()` cannot reach it because the pipeline never drops entries is gone; the step-4 clause "the tiled generator disarms the copies it returns from a pooled run" now reads "the entries it returns on every call" (07-19's always-disarm; the flag test and the 12-round measurement back it).

Gates: AST identity against HEAD `36d1efc` printed `identical`; `caveat-measured` printed (`never drops entries` 0, `unpickled store copy` 0, `no ``<key>.npy``` 1); `tests/test_image_store.py tests/test_hygiene.py -k "not benchmark"`: `221 passed`; `ruff check src tests`: all checks passed; `ruff format --check src tests`: 37 files already formatted.

## Task 2: MIGRATION-v0.11.md (commit 5549f7c)

**BC-P2I-030.** Origin cell gains `4b4add3` and `d00cfdb`. The "Disk persistence after a pooled run" group is replaced by **Disk persistence**: every `generate()` call (`n_jobs=1` included) disarms delete-on-garbage-collection on the entries it returns and on those of the stores in `image_generators`; the clause that exempted sequential results is gone. The mixed-sequence counts are quoted from `07-19-SUMMARY.md` `## Twelve-round measurement (mixed n_jobs, arrays read)`: "0 of 12 rounds failing after the change against 12 of 12 before (`failures: 0 / 12` against `failures: 12 / 12`)" over a pooled, then sequential-adding-features, then pooled sequence with every raster read. Persistence statement: default `enable_caching=False` writes no files at either `n_jobs`; without `cache_path` the files are `<store dir>/<key>.dat` (a pooled run also leaves the codec pair); with it `<cache_path>/<tile_id>/<key>.dat`; two routes. A **Failed batch** group records the failed-pooled-dispatch reset (parent drops its tile generators and re-raises; the retry is not refused; before, `StorePurgeRefusedError` at both `n_jobs`; at `n_jobs=1` nothing is dropped). The ownership limit, its triggers and routes are unchanged. The earlier pooled-only `failures: 0 / 12` / `12 / 12` sentence from 07-16 was left as it was.

**BC-P2I-027.** Origin cell gains `e738cf4`. The sentence that foreign or aliased refusals still surface in the tolerated case is replaced by the pre-write refusal (four write paths, `StorePurgeAliasedArtefactError` / `StorePurgeForeignArtefactError` by where the link resolves, every process, nothing written; a planted `<key>.dat.tmp` link used to redirect the raster in both processes; in a non-owner process a linked `.dat`/`.meta.json` leftover is refused by pc2img as `StorePurgeRefusedError`; a link planted under an already tracked key after its add is still followed, a documented limit). The caveat is the same wording as the docstring. The "unreachable from pc2img's own pipeline, which never drops entries" sentence is gone. The retained-reference clause now says the tiled generator disarms the entries it returns on every call.

**Verifier.** The second block of `_tier2_bc_p2i_027` (owner-process durable re-add over a lone memmap) is replaced by the detach probe: add `k` (zeros), `held = store.store["k"]`, `del store["k"]`, re-add (ones), assert the replacement `.dat` exists, `del held; gc.collect()`, assert the `.dat` still exists and the replacement reads `1.0`. Messages: `BC-P2I-027: collecting a dropped entry deleted the replacement's memmap` and `BC-P2I-027: the replacement over a dropped entry did not read back`.

Extracted (07-06 recipe) and run on the final tree:

```
[ok] verified 30 entries                (uv run --frozen; also after the generated_at re-stamp)
ruff check --select E,F,W --ignore E501 on the extracted file: All checks passed!
'collecting a dropped entry deleted the replacement' in extracted file: 1; 'did not serve the replacement': 0
```

### Code-mutation proof

Scratch copy of `src/` at `<scratchpad>/mut/src` (`<scratchpad>` = `/tmp/claude-1000/-scratch-31-pc2img/8adb4905-a757-44d2-a417-1d0ec8df8e84/scratchpad`), with the soft branch deleted from the copy's `disk_backed_image_store.py` (the whole `elif _leftover_artefact_exists(...): try: self.purge(...) except StorePurgeRefusedError ...` block). Import proof first, which printed the scratch path (no fallback to the real file was needed, and `git status --porcelain -- src` printed nothing throughout):

```
$ PYTHONPATH=<scratchpad>/mut/src uv run --no-sync python -c "import pc2img.image_cache.disk_backed_image_store as m, sys; assert m.__file__.startswith('<scratchpad>/mut/src'), m.__file__; print(m.__file__)"
<scratchpad>/mut/src/pc2img/image_cache/disk_backed_image_store.py
```

Then the extracted verifier against the mutated tree:

```
$ PYTHONPATH=<scratchpad>/mut/src uv run --frozen python _scrap/pc2img-migration-verifier.py
[fail] migration-spec verification:
  BC-P2I-027: collecting a dropped entry deleted the replacement's memmap
exit 1
```

Then against the real tree: `[ok] verified 30 entries`, exit 0.

### Tally and stamp

Summary tally re-derived with awk: severity should-review 20, additive 4, informational 5, must-edit 1 (= 30); category dep-constraint 7, error-behavior 6, semantic-change 6, additive-or-fixed 5, signature-shape 3, surface-removed 2, on-disk-format 1: unchanged, matches the Summary text. 30 `BC-P2I` rows; `target_ref: "v0.11.0"` unchanged; `generated_at` re-stamped `2026-10-02T14:21:07Z` to `2026-10-05T09:20:03Z`.

### Behavioural claims re-run on the final tree before being written

- `_scrap/tiled_mixed_rounds.py` (07-19's instrument): `failures: 0 / 12`.
- `tests/test_tiled_generator.py tests/test_image_store.py -k "mixed or own_gc or failing_tile or failing_sequential or linked_write_path or linked_outside or retained_reference"`: `18 passed`.
- Persistence (`persist_probe.py` per configuration, fresh `TMPDIR`; `uv-*.lock` is uv's own): default `n_jobs=1` and `n_jobs=2`: no library files; caching without `cache_path` `n_jobs=1`: `gradient_x_range.dat` and `range.dat` per tile (4 files); `n_jobs=2`: `.dat`, `.npy`, `.meta.json` per key per tile (12 files). With `cache_path` (`_scrap/r3_cp.py`, one `generate(["range"])`): `n_jobs=1` `['tile_00/range.dat', 'tile_01/range.dat']`; `n_jobs=2` the `.dat`, `.meta.json` and `.npy` per tile.
- The record's statement that the pipeline never calls `del`/`pop`/`popitem`/`clear` on a store: `grep` over `src/pc2img` (excluding `_old/`) finds no such call.

## Verification

- `uv run --no-sync pytest -q -p no:cacheprovider`: `403 passed, 94 warnings` (final tree, before the SUMMARY commit)
- Task 1 and Task 2 `<automated>` greps: `caveat-measured`, `thirty-rows`, row-030 counts all 1 and `are unchanged` 0, row-027 counts all 1 and the three absent strings 0, `probe-reshaped`
- A green suite proves only that the existing tests still pass; the evidence here is the (a)-(c) measurements, the 0 / 12 re-run, and the mutation run that failed with the new 027 message.

## Deviations from Plan

**1. [Rule 2 - Doc accuracy] Step-4 clause in the `add_image_to_store` docstring.** The sentence "the tiled generator disarms the copies it returns from a pooled run" understated 07-19's always-disarm; it now says "the entries it returns on every call". Docstring-only (inside the AST-identity check). Commit 3e91f7e.

**2. [Scope note] The pooled-only twelve-round sentence from 07-16 is retained in BC-P2I-030.** The plan says the only round counts written here come from 07-19's heading; that earlier sentence is pre-existing record text, not written by this plan, so it was neither re-quoted nor removed. The new counts are labelled with their sequence.

**3. [Process] Fork-route (b) unnamed in the record.** Per plan, the disproved unpickled-copy route appears only in this SUMMARY.

Total deviations: 1 docstring-accuracy edit, 2 process notes. No behaviour or scope change.

## Known Stubs

None.

## Threat Flags

None. Docstring and planning-record edits only; no new network, auth, file-access or schema surface. T-07-67 (a caveat whose reachability was disproved; a probe that passes without the code) is closed by the (a)-(c) measurements and the code-mutation proof; T-07-68 by the hygiene gate (`tests/test_hygiene.py` passing).

## Notes for the orchestrator/owner

- Before 07-07 resumes: review round 4 of this diff as stated in the plan's `<verification>` (`/gsd-code-review 7 --files ...`, `/code-review c1b813d high`, `/gsd-consolidate-findings`), then 07-07 Tasks 1-2 re-run on the new tip with a new `D03_SHA:` line. Not executed here.
- No `07-UAT.md` gap `status:` field was changed; no requirement was marked complete (gap-closure plan). 07-07..07-11 and 07-15 untouched; the record stays at thirty entries and prints `[ok] verified 30 entries`. No GitHub interaction.

## Self-Check: PASSED

- FOUND: src/pc2img/image_cache/disk_backed_image_store.py, .planning/MIGRATION-v0.11.md
- FOUND commits: 3e91f7e, 5549f7c
