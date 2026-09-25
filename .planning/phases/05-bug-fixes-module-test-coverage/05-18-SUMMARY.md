---
phase: 05-bug-fixes-module-test-coverage
plan: 18
subsystem: testing
tags: [image-cache, rrim, disk-backed-store, mutation-testing, gap-closure]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage (plans 14-17)
    provides: the round-2/3/4 gap-closure fixes (G9/G10, WR-02, review-r2-70fb459066a6) this plan's
      overwrite reorder builds on, and the owner triage (D-R5-01, commit a64c73e) that scoped this
      plan to the four code-level round-4 findings
provides:
  - "WR-07 fixed: add_image_to_store validates containment then raster shape BEFORE dropping the
    existing entry, so a failed overwrite (bad shape or containment) is a full no-op in memory and
    on disk; the raster-shape rule now has one source (_assert_image_shape)"
  - "IN-01 fixed: test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op now plants a
    never-added codec pair on disk so the sensor is mutation-sensitive, not vacuous"
  - "IN-06 fixed: test_default_config_is_coerced_from_none_sentinel no longer leaks tmp* directories
    outside pytest's tree; the two delete-refusal tests are merged into one carrying the union of
    both contracts"
  - "WR-03 fixed: test_generate_rrim_z_factor_changes_the_output now pins z_factor on compute_slope
    itself via the component-slope pair, which neither the rrim nor the pack pair could detect"
affects: [05-19 (round-5 wave 2: provenance sweep, UAT/VERIFICATION bookkeeping, cites this plan's commits)]

# Actuals (#2632)
actuals:
  tokens: 5115
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level private helper as the single source of a cross-file invariant, imported
      cross-module (precedent: derivative_features._validate_percentile_bounds) -- applied here to
      _assert_image_shape, shared by DiskBackedImageData.__init__ and the store's overwrite path"
    - "validate -> delete -> build ordering for an overwrite-preserving mutation on a shared on-disk
      path, rather than build-then-swap, when the replacement and the original derive the same
      backing file path from the same key"
    - "Mutation-sensitivity proof via a throwaway pytest plugin (pytest_configure rebinding the
      target method/function to its pre-fix behaviour), run once to record the RED signature, never
      committed"

key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - src/pc2img/image_cache/disk_backed_image_data.py
    - tests/test_image_store.py
    - tests/test_rrim_features.py

key-decisions:
  - "WR-07 ordering: validate (containment, then raster shape) -> delete -> build. The reviewer's
    suggested build-then-swap ordering was measured and rejected: constructing the replacement on
    the old entry's shared <key>.dat path while the old entry is still tracked clobbers the old
    entry's live buffer at construction, and the old entry's path-bound weakref.finalize then
    unlinks the just-built replacement's .dat when the old object is collected."
  - "The raster-shape rule's exception type stays AssertionError (unchanged, single-sourced via the
    new _assert_image_shape helper) -- no BC-NOTES entry opens for this plan."
  - "The documented residual (an OSError raised while the replacement's memmap is created, after the
    old entry has already been dropped) and the pre-existing held-reference hazard (a caller keeping
    an entry alive across a re-generate) are NOT fixed here -- both need a build-to-temporary-then-
    adopt primitive that can only live in the GSEGUtils cache layer that derives <key>.dat from the
    key; routed to the Phase-6 GSEGUtils carry-out list for 05-19 to record."

requirements-completed: [BUG-05, TEST-04]

coverage:
  - id: D1
    description: "WR-07: a failed overwrite (containment or raster shape) is a full no-op, in memory
      and on disk, for an in-memory and a codec-offloaded original; a successful overwrite still
      round-trips after offload/reload from the same store and a fresh store; the shape rule has one
      source; the reorder is mutation-sensitive under a revert-ordering plugin."
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py#test_successful_overwrite_serves_the_replacement_after_offload_and_reload"
        status: pass
    human_judgment: false
  - id: D2
    description: "IN-01: the absent-key delete test is no longer vacuous -- a peer-planted codec pair
      on disk makes it fail under the unlink-first mutation."
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op"
        status: pass
    human_judgment: false
  - id: D3
    description: "IN-06: the store test module leaves no temp directories outside pytest's tree, and
      the two delete-refusal tests are merged into one carrying the union of both contracts."
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_default_config_is_coerced_from_none_sentinel"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py#test_escaping_key_delete_refuses_and_leaves_outside_file_intact"
        status: pass
    human_judgment: false
  - id: D4
    description: "WR-03: dropping z_factor from compute_slope is now detected via the
      rrim_component_(slope,...) pair, which the rrim and pack pairs alone could not catch."
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py#test_generate_rrim_z_factor_changes_the_output"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-09-25
status: complete
---

# Phase 5 Plan 18: Round-5 Wave-1 Gap Closure (WR-07, IN-01, IN-06, WR-03) Summary

**Store overwrite reordered to validate-before-delete (closing a pre-existing data-loss defect), two proving tests made mutation-sensitive, one duplicate test merged, and z_factor pinned on the RRIM slope path via a component-surface assertion the prior test lacked.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-09-25T09:50:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- **WR-07 (Task 1):** `DiskBackedImageStore.add_image_to_store` now validates containment and raster
  shape BEFORE dropping the existing entry, so a failed overwrite is a full no-op in memory and on
  disk (both an in-memory and a codec-offloaded original). The raster-shape rule was hoisted into a
  module-level `_assert_image_shape` helper — the single source, shared by
  `DiskBackedImageData.__init__` and the store's overwrite path.
- **IN-01 (Task 2):** `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op` now plants a
  `never-added` codec pair on disk (via a peer store constructed after the store under test, so it
  is never adopted) — the sensor now fails under an unlink-first delete-ordering mutation instead of
  holding vacuously on an empty cache directory.
- **IN-06 (Task 2):** `test_default_config_is_coerced_from_none_sentinel` redirects
  `tempfile.tempdir` to `tmp_path` before either None-config store is constructed and asserts
  `cache_dir.parent == tmp_path`, so the module no longer leaves `tmp*` directories under the system
  temp directory. `test_refused_delete_leaves_store_membership_intact` was removed and its one extra
  assertion (array equality of the surviving entry) folded into
  `test_escaping_key_delete_refuses_and_leaves_outside_file_intact`.
- **WR-03 (Task 3):** `test_generate_rrim_z_factor_changes_the_output` now also asserts the
  `rrim_component_(slope,range,z1)` vs `(z4)` pair, the only surface on which `compute_slope`'s own
  `z_factor` is directly observable (the rrim composite's slope channel is robust-percentile
  normalised, so a linear z scale cancels there; the pack pair only observes z through the openness
  path). The docstring's prior overclaim — that dropping z would make every asserted pair equal —
  was corrected.

## Task Commits

Each task was committed atomically:

1. **Task 1: WR-07 — validate-before-delete overwrite ordering**
   - `20ef1c6` `test(image-cache): pin failed-overwrite atomicity and the successful-overwrite round trip`
   - `816a7cc` `fix(image-cache): validate the replacement before dropping the old entry on overwrite`
2. **Task 2: IN-01 / IN-06 — absent-key sensor, temp-dir leak, duplicate merge**
   - `1ac37b0` `test(image-cache): plant the absent-key codec pair, keep temp dirs under tmp_path, merge the delete-refusal tests`
3. **Task 3: WR-03 — component-slope z_factor pin**
   - `d6a25ef` `test(rrim): pin z_factor on the slope path via the component surface`

**Plan metadata:** committed separately after this SUMMARY.

_Note: Task 1 is `type="tracer"` per the plan (production-quality, no throwaway); the two commits
above are its test-then-fix pair, not a RED/GREEN/REFACTOR TDD triple — `workflow.tdd_mode` is
`false` in this project's config, so the plan's own task-level test-first sequence (not the
tdd.md gate machinery) governs commit shape here._

## Files Created/Modified

- `src/pc2img/image_cache/disk_backed_image_store.py` — `add_image_to_store` reordered
  (containment -> shape -> delete -> build); docstring states the ordering, why build-first is
  unsafe, and the documented residual.
- `src/pc2img/image_cache/disk_backed_image_data.py` — inline shape assertion hoisted into the
  module-level `_assert_image_shape` helper; `__init__` delegates to it.
- `tests/test_image_store.py` — two new tests (WR-07), one strengthened test (IN-01), one
  redirected + strengthened test and one removed duplicate (IN-06).
- `tests/test_rrim_features.py` — one extended test, docstring corrected (WR-03).

## Decisions Made

See `key-decisions` in the frontmatter — WR-07 ordering choice, exception-type pin (no BC-NOTES
entry), and the two residuals explicitly left unfixed and routed to 05-19 / the Phase-6 GSEGUtils
carry-out list.

## Deviations from Plan

None - plan executed exactly as written. The single wording adjustment beyond the plan's literal
text was removing the duplicated `ndim in (2, 3)` substring from `DiskBackedImageData`'s class
docstring (it appeared once in the docstring and once in the assertion before this plan; the
class-docstring wording was reworded to keep the required single-source count at 1 for the
`<verify>` chain's exact-match check) — a same-scope wording fix inside the task's own diff, not a
Rule 1-4 deviation.

## Reproduction Transcripts

### WR-07 — HEAD state (measured before the source edit, HEAD `816a7cc`'s parent)

```
before: 'range' in store -> True
before listing: ['range.meta.json', 'range.npy']
AssertionError raised:
after: 'range' in store -> False
after listing: []
KeyError raised on store['range']: 'range'
```

### WR-07 — reviewer-ordering hazard (build-then-swap, rejected)

```
old entry data before construct-new: [2. 2. 2.]
old entry data AFTER construct-new (clobbered if == 99): [99. 99. 99.]
new_entry.cache_path: /tmp/tmp7m_iuz_t/range.dat exists: True
new_entry.cache_path exists after old entry dropped+GC'd: False
new_entry data readable after old entry GC: [99. 99. 99.]
```
The old entry's data is clobbered at construction time (shared `.dat` path, `r+` reopen), and the
new entry's `.dat` is deleted once the old entry is collected (its finalizer fires on the shared
path) — the file the just-built replacement depends on. This is the measured basis for rejecting
build-then-swap and choosing validate -> delete -> build instead.

### IN-01 — LIVE vs unlink-first mutant (via the plan's Task 2 mutation plugin)

Plugin off: `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op` passes — the peer-planted
`never-added.npy` + `.meta.json` pair survives the absent-key `KeyError`. Plugin on (unlink both
codec paths before delegating to the base `__delitem__`): the same test fails with
`assert ['never-added.dat'] == ['never-added.meta.json', 'never-added.npy']` — the pair is gone,
only the base store's KeyError contract held.

### IN-06 — leak (measured before the fix)

`DiskBackedImageStore()` / `DiskBackedImageStore(config=None)` each created a `tmp*` directory under
the system temp dir that survived `del` + `gc.collect()`, because the base store's None-`cache_path`
branch calls `tempfile.mkdtemp()` unconditionally. Fixed by redirecting `tempfile.tempdir` to
`tmp_path` before construction; `leaked tmp dirs: 0` recorded by the plan's `<verify>` chain (see
below).

## Mutation-Check Summary Lines

- **Task 1 (WR-07), revert-ordering plugin** (old body: `del self[img_name]` before
  `add_data_to_store`): `2 failed, 30 passed` — exactly
  `test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact[in_memory]` and
  `[codec_offloaded]` fail; plugin off: `32 passed`.
- **Task 2 (IN-01), unlink-first plugin** (`__delitem__` unlinks both codec paths before delegating
  to the base store): `-k absent_key` -> `1 failed`;
  whole file -> `2 failed, 27 passed` — exactly
  `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op` and
  `test_failed_delete_preserves_codec_pair_and_both_stores` fail; plugin off: `29 passed`.
- **Task 3 (WR-03), slope_noz plugin** (`compute_slope` forced to `z_factor=1.0` regardless of the
  argument): `-k z_factor_changes` -> `1 failed` with message `slope path is z_factor-insensitive`;
  whole file -> `1 failed, 50 passed`, same single failure; plugin off: `51 passed`.

All plugins are throwaway modules that lived only in the session scratchpad
(`/tmp/claude-1000/-scratch-31-pc2img/.../scratchpad/mutation_*.py`) and were never committed.

## Leaked-tmp-dirs Verify Line

```
leaked tmp dirs: 0
```

## Suite / Coverage / Hygiene

- `.venv/bin/pytest tests/test_image_store.py -q` -> `32 passed` (0 xfail/xpass).
- `.venv/bin/pytest tests/test_rrim_features.py -q` -> `51 passed` (0 xfail/xpass; extended test
  passed on its FIRST run).
- `.venv/bin/pytest -q` (full suite) -> `196 passed, 0 failed`.
- `.venv/bin/pytest --cov=pc2img --cov-branch --cov-fail-under=55 -q` -> `62.27%` total coverage,
  floor 55% held.
- `.venv/bin/pytest tests/test_hygiene.py -q` -> `4 passed`.
- `.venv/bin/ruff check` / `ruff format --check` on
  `src/pc2img/image_cache/ tests/test_image_store.py tests/test_rrim_features.py` -> all clean.
- `test_store_source_has_no_arbitrary_deserialization_sink` (DSN-09 sensor) still passes — part of
  the 196.

## Not-a-BC-Entry Judgement (WR-07)

No `BC-NOTES.md` entry opens for this plan: the raster-shape rule's exception type stays
`AssertionError` (unchanged, now single-sourced), the error precedence (containment before shape) is
unchanged and verified, and `_assert_image_shape` is a private module-level helper, not a new public
symbol on `DiskBackedImageData` or the store. This follows the precedent set by the G10 data-loss fix
(05-14), which was likewise not a BC entry for the same reasons.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave-1 (this plan) of round-5 closure is done: all four assigned code-level findings (WR-07,
  IN-01, IN-06, WR-03) are fixed, tested, and proven mutation-sensitive where applicable.
- **05-19 (wave 2) is next**, and owns: the two comment-text findings (IN-03, IN-04 provenance
  sweep) this plan deliberately left untouched in its own added text; the UAT/VERIFICATION
  bookkeeping (per-gap status flips, `## Gaps — Round 5` entry) this plan explicitly did not touch;
  and citing this plan's four commit hashes plus the reproduction transcripts above into the
  Round-5 closure record and the Phase-6 GSEGUtils carry-out list (the OSError-mid-build residual
  and the held-reference hazard).
- **Blocker still open, unrelated to this plan's scope:** per the global Review Discipline rule
  (`~/.claude/CLAUDE.md` § Review Discipline) and this plan's own `<verification>` §"Post-execution
  gate", the round-5 diff (this plan + 05-19) needs its OWN code review —
  `/gsd-code-review 05 --files src/pc2img/image_cache/disk_backed_image_store.py
  src/pc2img/image_cache/disk_backed_image_data.py tests/test_image_store.py
  tests/test_rrim_features.py`, escalating to `/code-review <base> high` because Task 1 reorders a
  data-loss path in a base-class wrapper — BEFORE Phase 5 re-verifies. This plan alone does not make
  the phase closeable.

## Self-Check: PASSED

- `src/pc2img/image_cache/disk_backed_image_store.py`, `disk_backed_image_data.py` exist on disk.
- Commits `20ef1c6`, `816a7cc`, `1ac37b0`, `d6a25ef` found in `git log --oneline --all`.
- All task-level `<acceptance_criteria>` re-verified (see reproduction transcripts and
  mutation-check summary lines above).
- Plan-level `<verification>`: `tests/test_image_store.py` 32 passed; `tests/test_rrim_features.py`
  51 passed; full suite 196 passed, 0 failed; coverage 62.27% (floor 55); hygiene 4 passed; ruff
  check + format clean on all touched paths.

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-09-25*
