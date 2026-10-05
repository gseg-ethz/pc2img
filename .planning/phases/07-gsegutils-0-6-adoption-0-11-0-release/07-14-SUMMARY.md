---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 14
subsystem: migration-record
tags: [gap-closure, migration, uv, dependency-comment, verifier]
status: complete

requires:
  - phase: 07-06
    provides: "the thirty-entry migration record and its inline verifier"
  - phase: 07-12
    provides: "per-tile loky dispatch (fix commit 4fbd966) and the twelve-round measurement"
  - phase: 07-13
    provides: "presence-gated overwrite purge (fix commit e3f7f5c)"
provides:
  - "pyproject.toml comments state the measured truth: the lock resolves every RAPIDS name from pypi.org, the four nvidia bindings have no effect and give no dependency-confusion protection"
  - "BC-P2I-030 rewritten as semantic-change: race fixed pc2img-side (0 of 12 failing after, 12 of 12 before), GSEGUtils#82 still valid, worker-owned tile store limit with three routes"
  - "BC-P2I-027 amended: tracked-or-on-disk purge, GC consequence, three independent refusal conditions, setter-inserted entry"
  - "inline verifier probes the re-add-after-del claim (mutation-checked), still prints [ok] verified 30 entries"
affects: [07-07 (gate literal `[ok] verified 30 entries` still holds; plan not touched), 07-15]

actuals:
  tokens: 4826
  tasks: 2
  commits: 2
plan_head_before: 3cacd4dd5bcf5d51385bd4a5fceff921ea74724e
plan_head_after: 179da9b017ed4f875b6947a72d039143d5fe54d3

tech-stack:
  added: []
  patterns:
    - "a documentation claim about a supply-chain control is re-derived from the lock (grep counts) and a from-scratch resolve, not from the comment it replaces"

key-files:
  created: []
  modified:
    - pyproject.toml
    - .planning/MIGRATION-v0.11.md

key-decisions:
  - "BC-P2I-030 narrows the 'overwrite in a different worker' clause to what was reproduced (see Deviations)"
  - "Record refers to the baseline 91b4ab6 rather than '0.10.x' for the old dispatch and the old setter-entry behaviour: v0.10.4 predates both modules"

requirements-completed: []

coverage:
  - id: D1
    description: "pyproject.toml uv-section comments state that the committed lock resolves RAPIDS from pypi.org and the nvidia bindings have no effect; bindings and lock unchanged"
    requirement: DEP-05
    verification:
      - kind: command
        ref: "uv lock --check; grep -c pypi.nvidia.com uv.lock (0); four bindings counted (4); hygiene suite 88 passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "BC-P2I-030 and BC-P2I-027 reflect the shipped behaviour after 07-12 and 07-13; record stays at thirty entries"
    requirement: BC-01
    verification:
      - kind: command
        ref: ".planning/MIGRATION-v0.11.md inline verifier (extract recipe) prints [ok] verified 30 entries"
        status: pass
    human_judgment: false
---

# Phase 07 Plan 14: nvidia-index comment truth + migration record for the gap fixes (WR-04, CR-01/CR-02/WR-01/WR-05 record) Summary

**The `pyproject.toml` comments now say what is measured (every RAPIDS name resolves from pypi.org, the four nvidia bindings do nothing today), and BC-P2I-030/BC-P2I-027 record the per-tile tiled dispatch, the presence-gated overwrite purge and the worker-owned tile-store limit, with the inline verifier extended and green at thirty entries.**

## Commits

| Commit | Message |
| ------ | ------- |
| 0d8ab0a | `build(deps): state what the nvidia index bindings actually do` |
| 179da9b | `docs(migration): record the per-tile tiled dispatch, the presence-gated overwrite purge and the worker-owned tile stores` |

`commits: 2` is measured with `git rev-list --count 3cacd4d..HEAD` taken at the second task commit (before this SUMMARY commit), from the persisted ledger.

Origin shas cited in the record, read from the SUMMARYs: `4fbd966` (07-12 fix, in the BC-P2I-030 origin cell, next to the earlier `a7d593d`) and `e3f7f5c` (07-13 fix, in the BC-P2I-027 origin cell, next to `1d1f9f2`).

## Task 1 evidence (comment, bindings and lock unchanged)

Precondition before any edit: `uv lock --check` exit 0 (`Resolved 137 packages`), `grep -c 'pypi.nvidia.com' uv.lock` = 0.

| Check | Result |
| ----- | ------ |
| `grep -c 'pypi.nvidia.com' uv.lock` | `0` |
| `grep -n 'pypi.org/simple' uv.lock \| grep -c .` | `144` |
| `uv lock --check` after the edit | exit 0, `Resolved 137 packages`; `git status` shows `uv.lock` unmodified |
| index bindings (`^(cudf\|cuspatial)-cu1[12] = { index = "nvidia" }`) | `4` |
| uv section lines matching `no (effect\|protection)` / `pypi.nvidia.com` | `1` / `3` |
| `comment-truthful` (false claim string absent) | printed |
| `tests/test_hygiene.py -k planning_vocabulary` | `82 passed, 6 deselected`; whole file `88 passed` |

The comment's claim that re-locking with and without the bindings gives byte-identical locks was reproduced rather than copied from 07-01: two throwaway git repos holding the current `pyproject.toml` (one with the four bindings, one with them stripped), each resolved from scratch with `uv lock`: both `Resolved 138 packages`, identical sha256 `cfbbb7cbe25ccc1976b2e3dcec5701046109aaea4dd32d7d3834245ad94c1ec8`, `pypi.nvidia.com` count 0 and `pypi.org/simple` count 145 in each. (138 versus the committed lock's 137 is the root-package entry difference 07-01 already explained; scratch repos live in the scratchpad, outside the repo.)

## Task 2 evidence (migration record)

### Round counts quoted in BC-P2I-030 (07-12-SUMMARY.md, `## Twelve-round measurement`)

```
pre-fix   failures: 12 / 12
post-fix  failures: 0 / 12
```

BC-P2I-030 states: "0 of 12 rounds failing after the change against 12 of 12 before".

### Severity/category tally (`awk` over rows matching `^| BC-P2I-[0-9]{3} |`)

```
rows: 30
additive-or-fixed 5, dep-constraint 7, error-behavior 6, on-disk-format 1,
semantic-change 6, signature-shape 3, surface-removed 2
additive 4, informational 5, must-edit 1, should-review 20
```

Summary paragraph re-derived: `dep-constraint` is now "seven entries" (was eight; 030 moved to `semantic-change`, now six); twenty should-review, one must-edit, five informational, four additive unchanged; the tiled sentence now names "the per-tile tiled fan-out change with its worker-owned tile stores". `generated_at` re-stamped to `2026-10-02T12:33:24Z`; `target_ref` stays `"v0.11.0"`.

### Verifier (extracted with the 07-06 recipe)

```
[ok] verified 30 entries          (exit 0)
ruff check --select E,F,W --ignore E501 _scrap/pc2img-migration-verifier.py: All checks passed!
grep -c 're-add after del' (extracted verifier): 2
```

New probe (appended to `_tier2_bc_p2i_027`): add `range`, offload, `del`, re-add with `np.ones`; the codec pair must be gone (`BC-P2I-027: a re-add after del left the stale codec pair on disk`); after offloading the replacement, a fresh `DiskBackedImageStore` over the directory must serve `1.0` (`BC-P2I-027: a fresh store served the pre-overwrite raster after del and re-add`) or serve nothing.

### Mutation checks (scratch copies in the gitignored `_scrap/`; repo files untouched)

1. Plan's mutation, expectation flipped (`served != 1.0` to `served != 0.0`):
   ```
   [fail] migration-spec verification:
     BC-P2I-027: a fresh store served the pre-overwrite raster after del and re-add
   mut1 rc=1
   ```
2. Source-level mutation, `pc2img.image_cache.disk_backed_image_store._has_on_disk_artefact` forced to `False` (the pre-07-13 tracking-only gate) before running the verifier:
   ```
   [fail] migration-spec verification:
     BC-P2I-027: a re-add after del left the stale codec pair on disk
   mut2 rc=1
   ```
3. Unmutated extraction re-run afterwards: `[ok] verified 30 entries`, rc 0.

### Claims in the new text reproduced by running code

| Claim | Run |
| ----- | --- |
| parent `purge` and parent `add_image_to_store` over an existing key after `n_jobs=2` raise `StorePurgeRefusedError` (a `RuntimeError`) | `_scrap/wr01_routes.py` |
| route `n_jobs=1`: parent overwrite and purge both succeed | same script |
| route fresh generator over the same `cache_path` works; route drop `image_generators["tile_00"]` + `shutil.rmtree(<cache_path>/tile_00)` then regenerate on the same instance works | same script |
| `StorePurgeAliasedArtefactError` for a built artefact symlinked to another key's artefact; `StorePurgeForeignArtefactError` for a setter-inserted entry with an outside `cache_path` (both `StorePurgeRefusedError` / `RuntimeError`) | `_scrap/bc027_refusals.py` |
| 07-13 regression tests (drop routes, retained-reference GC, foreign-process new key) | `tests/test_image_store.py -k "drop_route or retained_reference or another_process"`: `6 passed` |
| `test_tiled_regenerate_on_one_instance_with_two_workers` is a plain passing test | `tests/test_tiled_generator.py`: `6 passed` |
| repeated `generate()` with fresh worker processes does not trigger a refusal | `_scrap/wr01_overwrite_other_worker.py`: `second generate (fresh workers) ok` |
| baseline `91b4ab6` dispatched `delayed(self._process_tile)` (whole tiled generator pickled) and its `add_image_to_store` had no refusal at all | read from `git show 91b4ab6:...` (baseline cannot run on the locked environment) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in record text] The plan's "a later `generate()` that must overwrite a key in a different worker can fail the same way" is not reproducible, so the record narrows it**
- **Found during:** Task 2 (checking each new claim by running code, per the global rule)
- **Issue:** Repeated `generate()` on one instance with fresh worker processes (after `get_reusable_executor().shutdown()`, so the second call's workers differ from the store's owner) succeeded, and the store's `_owner_pid` stayed that of the first-call worker. `FeatureManager.request()` skips features the store already tracks, so no overwrite is attempted; a direct `purge` of the same store from a fresh worker is refused, so the refusal itself is real. 07-12 and 07-13 both shipped the "can fail the same way" clause in the `TiledPointCloudImageGenerator` class docstring (and the 12-round measurement saw no such failure).
- **Fix:** BC-P2I-030 states what was reproduced: parent-side `purge` and overwrite are refused after `n_jobs >= 2`; an overwrite from any other process is refused the same way; repeated `generate()` did not trigger it in the measured runs, including with fresh worker processes, because tracked features are not recomputed.
- **Not done:** the shipped docstring was not edited (out of this plan's `files_modified`). Surfaced for the round's review: `src/pc2img/tiled_generator.py` class docstring, sentence "and a later `generate()` that has to overwrite a key in a different worker can fail the same way", overstates what `generate()` can currently hit.
- **Files modified:** `.planning/MIGRATION-v0.11.md`
- **Commit:** 179da9b

**2. [Plan wording] "0.10.x" anchor replaced by the baseline `91b4ab6`**
- `v0.10.4` predates `image_cache` and `tiled_generator.py` (it has `tiled_image_generation.py`), so "0.10.x pickled the whole tiled generator" and "0.10.x allowed overwriting a setter-inserted entry" cannot be checked against a 0.10 tag. Both statements are anchored to the baseline `91b4ab6` (verified by reading its source).

**Total deviations:** 1 auto-fixed (record text narrowed), 1 wording choice. **Impact:** none on scope; one possible docstring follow-up for the round's review.

## Known Stubs

None.

## Threat Flags

None. A comment edit and a planning-record edit; no new endpoints, auth paths, file-access patterns or schema changes. T-07-49 (claimed control the lock does not deliver) and T-07-50 (record claims without a probe) are mitigated by the greps and the mutation-checked probe above.

## Gap-round bookkeeping

Per the dispatch instruction, no `07-UAT.md` gap `status:` field was changed, no requirement was marked complete, and 07-07 through 07-11 and their artefacts were not touched (07-07's gate literal `[ok] verified 30 entries` still holds). Per the global review-discipline rule, this round's diff (07-12, 07-13, 07-14) still needs its own review before 07-07 resumes: `/gsd-code-review 7 --files src/pc2img/tiled_generator.py tests/test_tiled_generator.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_image_store.py pyproject.toml`, `/code-review 271b208 high`, findings landed with `/gsd-consolidate-findings`, then 07-07 Tasks 1-2 re-run on the new tip with a new `D03_SHA:` line. Orchestrator/owner steps.

## Self-Check: PASSED

- Files: `pyproject.toml`, `.planning/MIGRATION-v0.11.md` modified and committed; `uv.lock` unmodified.
- Commits found: 0d8ab0a, 179da9b.
- `uv lock --check` clean before and after; verifier `[ok] verified 30 entries`.
