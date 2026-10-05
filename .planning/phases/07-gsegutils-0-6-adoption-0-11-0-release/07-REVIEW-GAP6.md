---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-05T13:10:00Z
depth: quick
diff_base: 8bb49c5
head: f4fd4d4
files_reviewed: 3
files_reviewed_list:
  - src/pc2img/tiled_generator.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - .planning/MIGRATION-v0.11.md
findings:
  critical: 1
  warning: 0
  info: 1
  total: 2
status: issues_found
---

# Phase 7: Code Review Report (gap round 6, 07-24: scoped final check, docs-only)

**Reviewed:** 2026-10-05T13:10:00Z
**Depth:** quick (scoped by owner decision 2026-10-05; every claim checked below was run, not just read)
**Files Reviewed:** 3. The scope is `git diff 8bb49c5..f4fd4d4` over `tiled_generator.py`, `disk_backed_image_store.py`
and `.planning/MIGRATION-v0.11.md`, and only the added lines.
**Status:** issues_found

## Summary

The scripts are in `scratchpad/gap6/`: `ast_check.py`, `route.py`, `after_success.py`, `dangling.py` and
`armed.py`. The REPL reproduction is `scratchpad/gap5/repl_typo.py`, re-run against f4fd4d4.

**(1) Docs-only: confirmed.** For both `.py` files, the AST with docstrings stripped is identical at 8bb49c5 and
f4fd4d4. The working tree equals f4fd4d4 for this scope. Every hunk sits inside a docstring, and no hunk touches a
`#` comment. No added line is longer than 120 characters. The record has 30 rows, and the inline verifier prints
`[ok] verified 30 entries`. `tests/test_tiled_generator.py` and `tests/test_image_store.py` pass (148 passed).

**(2) All four fixes landed as the 07-24 must_haves describe.**
- **G5-CR-02 (persistence limited to successful calls).** This landed at all four sites:
  - class Disk persistence, `tiled_generator.py:119-131`;
  - `generate()`, `:270-276`;
  - store, `disk_backed_image_store.py:310-312`;
  - BC-P2I-030.

  Each paragraph points to Known limitations or to the non-owner caveat. I measured "after a successful call,
  released results and dropped generators no longer delete their cache files, whatever `n_jobs`" with
  `after_success.py`, using five histories: success, then a failing call at `n_jobs` 1 or 2, then a successful call
  at `n_jobs` 1 or 2. Every kept entry reads `purge_disk_on_gc=False`, and dropping the generators deleted nothing.
  One new sentence still overreaches. See CR-01.
- **G5-CR-01 (retry routes).** "The recommended route is to retry with a fresh `TiledPointCloudImageGenerator` over a
  fresh `cache_path`" now comes first (`tiled_generator.py:192-194`, BC-P2I-030 (2)). The `gc.collect()` route is
  marked for scripts only, and the text says interactive sessions, notebooks and debuggers are excluded.
- **G5-WR-01 (dangling link).** "If a dangling `<key>.dat` link blocks a key, remove the link by hand; `purge` may not
  clear it" appears in all three places:
  - the `_refuse_linked_write_path` docstring (`disk_backed_image_store.py:77-78`);
  - the tiled Link check paragraph (`tiled_generator.py:209-210`);
  - BC-P2I-027, which BC-P2I-030's Link check mirrors.

  I measured it with `dangling.py`:

  | Case | `purge("k")` | Link after `purge` | After removing the link by hand |
  |---|---|---|---|
  | Untracked dangling link, target inside the cache | `KeyError` | still there | add succeeds, raster reads back |
  | Untracked dangling link, target outside the cache | `KeyError` | still there | add succeeds, raster reads back |
  | Tracked key whose `.dat` became dangling | clears the link | gone | add succeeds |

  "May not" is the right word for this.
- **G5-IN-01 / IN-02 (aligned wording).**
  - "Is planned for pc2img 0.11.1" now appears at all four sites: the store, BC-P2I-027, the class docstring and
    BC-P2I-030. No "follows in" is left.
  - "In general, do not hold entries taken from the tile stores … across a regenerate" now matches between the class
    docstring and BC-P2I-030 (3), and the store docstring and BC-P2I-027.
  - "collects nothing" was replaced by "cannot collect the failed call's objects" at both sites, and 0 occurrences
    are left.

**(3) Nothing else changed.** Every other changed line has its words unchanged:
- Store `:78-80` is a re-wrap.
- `tiled_generator.py:198-199` re-wraps the `(``image_generators[...].feature_mgr.cache_store``)` literal across the
  line break. The literal already spanned a line break before this round.
- The record's `generated_at` was re-stamped, as the plan requires.

No content change falls outside the four fixes.

**(4) New sentences.** I checked every added sentence.
- The armed-entry sentence holds. `armed.py` shows that an armed entry dropped after `del` removes its `.dat`, both
  live and after offload.
- The sentence that interactive sessions, notebooks and debuggers keep the exception alive matches `sys.last_exc` /
  `sys.last_traceback`. IPython sets the same attributes. It was not measured here, because IPython is not installed.
- The fresh-`cache_path` route stayed clean in every shape tested in gap 5 (144 script runs and the REPL).

One added sentence is false: see CR-01.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: "The files of successful calls persist until `purge()` is called or the directory is removed" is false after a failed call. The failed-call hazard deletes exactly those files.

**File:**
- `src/pc2img/tiled_generator.py:131-132` (class, Disk persistence)
- `src/pc2img/tiled_generator.py:275-276` (`generate()`: "The tile directory keeps the files of successful calls
  until `purge` is called or the directory is removed")
- `.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 Disk persistence, same sentence)

**Issue:** The G5-CR-02 fix replaced "All of them persist" and "keeps those files" with a version limited to
successful calls. A retry after a failed call is a successful call, and Known limitations (2) says the retry's files
"may be deleted when the failed call's objects are garbage-collected". The new sentence therefore makes an
unconditional durability promise about the exact files the hazard destroys.

The `generate()` docstring contradicts itself in its next sentence ("may make a retry of that call lose files"). In
the class docstring, the nearby pointer ("Entries that a failed call added may still delete their `.dat`") reads as
if the failed call only removes its own files. It never says that the deleted `.dat` is the one the successful retry
rewrote at the same path.

Measured at f4fd4d4. In each run, the retry `generate()` returned results, then the failed call's objects were
released and `gc.collect()` ran.

```
route.py none 1 1 inside sub    LOST 6/10  (t0 gradient_x_range, hillshade_range, store t0 range, … FileNotFoundError)
route.py none 1 1 inside same   LOST 8/14
python -i < gap5/repl_typo.py   retry read back clean; after a later typo: LOST [('t0','gradient_x_range','FileNotFoundError')]
```

The second reproduction is the interactive case that G5-CR-01 is about. A notebook user reads "the files of
successful calls persist" and keeps working against a result that later disappears. This is the same class of defect
as G5-CR-02, an unconditional persistence claim falsified by measurement. This round set out to remove that class,
and this sentence brings it back in the sentence the fix rewrote.

**Fix (wording only, all three sites):** keep the scope limited to successful calls, and make the exception explicit
in the same sentence:

```text
The files persist until ``purge()`` is called or the directory is removed, except that after a
failed call the failed call's entries may still delete them, a retry's files included (see Known
limitations below).
```

In `generate()`: "The tile directory keeps the files until `purge` is called or the directory is removed, except that
the entries a call that raised added to kept stores stay armed …" Merge it with the following sentence, so that the
promise and its exception are not two separate sentences that contradict each other.

## Info

### IN-01: In BC-P2I-027, the "measured" parenthetical now follows the new hand-removal guidance

**File:** `.planning/MIGRATION-v0.11.md:76` (BC-P2I-027)
**Issue:** The added text puts the guidance directly before the existing measurement, as two parentheticals in a row:
`… lies in the cache directory (if a dangling <key>.dat link blocks a key, remove the link by hand; purge may not
clear it) (measured: k.dat -> payload.bin and g.dat -> gone.bin both raised StorePurgeAliasedArtefactError …)`. The
measurement now reads as evidence for the guidance, but it only measured the refusal. The docstrings place the
guidance in its own sentence after the classification text.
**Fix:** Move the guidance after the measurement, or make it its own sentence after "the temporary names are refused
whatever their target", matching `_refuse_linked_write_path`.

---

_Reviewed: 2026-10-05T13:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick (scoped)_
