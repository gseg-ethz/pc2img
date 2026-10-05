---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-05T12:40:00Z
depth: standard
diff_base: cb85baa
files_reviewed: 3
files_reviewed_list:
  - src/pc2img/tiled_generator.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_tiled_generator.py
findings:
  critical: 2
  warning: 3
  info: 2
  total: 7
status: issues_found
---

# Phase 7: Code Review Report (gap round 4, 07-22: docs-only reading check)

**Reviewed:** 2026-10-05T12:40:00Z
**Depth:** standard (reading check, with claims reproduced by running code)
**Files Reviewed:** 3, plus `.planning/MIGRATION-v0.11.md` BC-P2I-027 and BC-P2I-030 as record
**Status:** issues_found

## Summary

**Scope.** `git diff cb85baa..HEAD` over the three files and `.planning/MIGRATION-v0.11.md`. The deferred behaviour
defects (G3-WR-01..05, IN-01/03; GSEGUtils#83 and 0.11.1) are dispositioned and are not findings here. Every
finding below is about whether the shipped text is accurate.

**(1) Docs-only: confirmed.** I stripped the docstrings from the AST and compared it with `cb85baa`
(`gap4/ast_ident.py`). All three files are identical: `tiled_generator.py`, `disk_backed_image_store.py` and
`tests/test_tiled_generator.py`. The working tree matches HEAD and `git status --porcelain -- src tests` is empty.
The only non-docstring change is the reworded `except`-handler comment at `tiled_generator.py:295-304`. The
record still has 30 rows, and `_scrap/pc2img-migration-verifier.py` prints `[ok] verified 30 entries`.

**(2) Claims checked against behaviour.** All scripts are in `scratchpad/gap4/`. Each scenario ran in a fresh
process and a fresh directory, with two tiles where `tile_01` lacks `intensity`.

These claims reproduced:
- the hold → drop → regenerate → release route, *after a pooled call*;
- the failing-first-call retry at `n_jobs=1`, both inside and after the `except` block;
- `gc.collect()` after leaving the block;
- the link refusal for adopted and dangling targets;
- the loop `RuntimeError` at `k.dat`;
- the sidecar values for `(2,)`, `(1,2)` and `(2,2)` with a single feature;
- `enable_caching=False`, which lost nothing (8 of 8 runs across four shapes).

**The Known-limitations retry paragraph does not survive.** It was the scope the caller asked about. Three of its
assertions are false:
- "a pooled failure ... did not lose files" is false. Pooled failures lose files intermittently.
- The hazard is scoped to a *retry at `n_jobs=1`*, but a pooled retry inside the block loses files every time.
- The headline mitigation `gc.collect()` does nothing when run inside the `except` block.

Because a reader who follows the text as written loses rasters, CR-01 and CR-02 are BLOCKERs, although the fix is
wording only. The other findings:
- A precondition is missing from the "held entry" limitation.
- The upstream root cause is attributed to limitations that are pc2img's own.
- The sidecar rule is stated per call when it applies per key.
- The "purge cannot clear a dangling link" claim is overstated.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: The retry hazard is scoped to "failing `n_jobs=1`, retried at `n_jobs=1`", but pooled retries and pooled failures lose files too, so "a pooled failure ... did not lose files" is false

**File:** `src/pc2img/tiled_generator.py:189-198`; `.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 Known limitations
(2): "a pooled failure retried at `n_jobs=-1`, inside or after the block, lost nothing in 3 of 3 runs each")

**Issue:** The bullet makes three claims:
- the hazard is "a failing `n_jobs=1` call that is retried at `n_jobs=1`";
- it happened "whether the retry ran inside the `except` block or after it";
- "A pooled failure retried at `n_jobs=-1` and the default `enable_caching=False` did not lose files."

An outside reader concludes that a pooled retry is safe, and that a pooled failure is safe. Both conclusions are
wrong. `gap4/retry.py` takes four arguments: prelude, failing `n_jobs`, retry `n_jobs`, and where the retry runs.
It reads every returned raster and every store entry after `offload()`:

```
failing n_jobs=1 first call, retry INSIDE except:
  retry n_jobs=2    LOST 4/4   [('t0','gradient_x_range','FileNotFoundError'), ('store t0','range',...), ...]
  retry n_jobs=-1   LOST 3/3
after a successful n_jobs=1 call, failing n_jobs=1, retry n_jobs=2 inside   LOST 4/4  (no entry held by the caller)
after a successful pooled call,  failing n_jobs=1, retry n_jobs=2 inside    LOST 4/4
failing POOLED first call, retry inside except:
  fail n_jobs=2,  retry n_jobs=1     LOST 2/12
  fail n_jobs=-1, retry n_jobs=1     LOST 4/8
  fail n_jobs=-1, retry n_jobs=-1    LOST 2/16
after a successful pooled call, failing n_jobs=-1, retry n_jobs=-1 inside    LOST 2/10   <- the record's own "3 of 3 clean" shape
for comparison: failing n_jobs=1 first call, retry n_jobs=1 inside/after    LOST (reproduces the record)
                failing n_jobs=1, retry pooled AFTER the block                clean 6/6
```

The pooled-failure losses are intermittent. They depend on whether a finished tile's results reached the parent
before the abort. A 3-run sample cannot support "lost nothing". The 07-22 SUMMARY's reason for excluding pooled
failures ("the pooled failure's generators live in workers, not in the parent's traceback") is refuted by the
`2/12`, `4/8` and `2/10` rows. The record's own pooled_inside shape lost files 2 times in 10.

The accurate scope is narrower and simpler. With caching and a `cache_path`, any retry made while the failed call's
exception is still alive, that is inside the `except` block, can lose files whatever `n_jobs` either call used.
After the block, a retry at `n_jobs=1` that follows a failing `n_jobs=1` call still loses them until the garbage
collector runs.

**Fix (wording only), for both the docstring and BC-P2I-030 (2):**

```text
* With caching enabled and a ``cache_path``, a retry after a failed ``generate()`` call can lose the
  retried rasters' files. The failed call's armed entries stay alive while its exception and traceback
  are referenced (and until the garbage collector runs after that), the retry rewrites the same
  ``<tile_id>/<key>.dat`` files, and collecting the old entries unlinks them; a later read raises
  ``FileNotFoundError``. Measured: a retry inside the ``except`` block lost files whatever ``n_jobs``
  the failed call and the retry used (every run after a failing ``n_jobs=1`` call; intermittently
  after a failing pooled call), and a retry at ``n_jobs=1`` after a failing ``n_jobs=1`` call lost them
  after the block too. ``enable_caching=False`` lost nothing. See below for the mitigation.
```

Drop "A pooled failure retried at `n_jobs=-1` ... did not lose files". In 030, replace "lost nothing in 3 of 3
runs each" with the measured intermittent rate.

### CR-02: The documented mitigation "Run `gc.collect()` after the failure and before retrying" does nothing inside the `except` block, where the same paragraph says the retry may run

**File:** `src/pc2img/tiled_generator.py:194-197`; `.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 (2): "collecting the
garbage before the retry ... kept every file in 3 of 3")

**Issue:** The bullet says the hazard hits "whether the retry ran inside the `except` block or after it", then tells
the reader to run `gc.collect()` after the failure and before retrying. A reader retrying inside the handler puts
`gc.collect()` there. That collects nothing, because the handler still references the exception, and through its
traceback, the failed call's entries. The bullet's own mechanism clause ("its exception and traceback hold them")
implies this, but the mitigation does not draw the conclusion. Measured (`retry.py none 1 {1,-1} path gcinside`:
`try: generate(...) except: gc.collect(); generate(retry)`):

```
['none', '1', '1',  'path', 'gcinside'] LOST 3/3   [('t0','gradient_x_range','FileNotFoundError'), ('store t0','range',...), ...]
['none', '1', '-1', 'path', 'gcinside'] LOST 3/3
['none', '1', '1',  'path', 'gc']       clean 3/3  (gc.collect() after leaving the block, then retry)
['none', '1', '2',  'path', 'gc']       clean 3/3
['seq',  '1', '2',  'path', 'gc']       clean 3/3
['pool', '1', '2',  'path', 'gc']       clean 3/3
['none', '-1','1',  'path', 'gc']       clean 6/6
```

The mitigation works only after the `except` block has been left. As written, it leads a careful reader straight
into the loss it is meant to prevent.

**Fix (wording only):**

```text
  Mitigation: let the ``except`` block finish (do not retry inside it; ``gc.collect()`` inside the
  handler collects nothing while the exception is referenced), then run ``gc.collect()`` and retry;
  or retry with a fresh ``TiledPointCloudImageGenerator`` over a fresh ``cache_path``. Both kept every
  file in the measurement.
```

Mirror the same text in BC-P2I-030 (2) and state where the measured `gc.collect()` ran.

## Warnings

### WR-01: The "held entry" limitation omits its precondition, a prior pooled call, so the tiled docstring and the store docstring contradict BC-P2I-027

**File:** `src/pc2img/tiled_generator.py:185-188`; `src/pc2img/image_cache/disk_backed_image_store.py:303-309`;
`.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 (1)); contrast `:76` (BC-P2I-027: "after a pooled call and a failing
`n_jobs=1` call ...").

**Issue:** The tiled bullet reads: "Measured: after a failing `n_jobs=1` call, hold an entry it added to a kept
store, drop its key, regenerate it at `n_jobs=1`, then release the held entry; the held entry deletes the
replacement's `.dat`". The store sentence and BC-P2I-030 (1) say the same, with no prior pooled call. The loss
needs a store owned by a worker. In the owner process, the regenerate's `purge` detaches the held entry's hook
(store step 4). Measured with `gap4/hold.py`, where the prelude call is the only difference:

```
seq  held armed: True | dat after release: True  | offload+read: ok                 (2 of 2)
pool held armed: True | dat after release: False | offload+read: FileNotFoundError  (2 of 2)
```

So a reader with an all-sequential history is told about a loss that does not happen. The precondition appears only
in 027's measurement parenthesis. The store sentence sits under the "Non-owner caveat" heading but never says the
store must be a non-owner.

**Fix:** Insert the precondition in all three places. Tiled bullet: "Measured: after a pooled call (so the tile
stores are owned by workers) and a failing `n_jobs=1` call, hold an entry …; with every call at `n_jobs=1` the
regenerate's purge detaches the held entry and the file survives." Store: "Entries a FAILED `n_jobs=1` call added to
kept tile stores that an earlier pooled call built …". 030 (1): add "after a pooled call".

### WR-02: The "root cause is upstream (GSEGUtils#83) / fixes follow in 0.11.1" heading covers two limitations that are pc2img's own code and unrelated to the GC hook

**File:** `src/pc2img/tiled_generator.py:178-181` (heading) over bullets `:199-205`; `.planning/MIGRATION-v0.11.md:79`
(BC-P2I-030 "Known limitations. The root cause is upstream … Until then: … (3) … (4) …");
`tests/test_tiled_generator.py:294-295` ("stay armed (an upstream limitation, GSEGUtils#83)").

**Issue:** Both the docstring and the record open the list with "The root cause is upstream: a released entry's
purge-on-garbage-collection deletes a `<key>.dat` that another live copy of the entry uses (#83). Behaviour fixes
follow in pc2img 0.11.1. Until then:". Bullets 3 and 4 are not caused by that:
- the location-based link classification (`disk_backed_image_store.py:86-100`, `target.is_relative_to(resolved_cache_dir)`);
- the bare `RuntimeError` from `link.resolve()` at `:91`.

Both are pc2img's `_refuse_linked_write_path`. Fixing #83 would change neither, and the round-3 review's fix for
them (G3-WR-02, G3-IN-01) is a pc2img-side edit. Likewise, "stay armed" in the test docstring comes from pc2img's
control flow: `_release_gc_ownership` runs only on success (`tiled_generator.py:293-317`). That is not an upstream
limitation, even though the harm it enables comes from #83. An outside reader is told to wait for an upstream
release for behaviour that only pc2img can change.

**Fix:** Split the list. "Caused by GSEGUtils#83 (fixes in 0.11.1): bullets 1-2." Then "pc2img's own pre-write link
check (to be revisited in 0.11.1): bullets 3-4." In the test docstring, write "stay armed (the disarm runs only after
a successful call; the deletion it allows is GSEGUtils#83)".

### WR-03: The sidecar rule "two pooled calls leave it `False`" is false for keys first computed in the later pooled call, and the writer is not only "the pickling of a pooled run"

**File:** `src/pc2img/tiled_generator.py:136-143`; `.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 "the sequence `(2,)`
loads `range` with `True`, `(1, 2)` and `(2, 2)` with `False`").

**Issue:** The docstring states a per-call rule: "one pooled call leaves the flag as configured, while a sequential
call followed by a pooled one, or two pooled calls, leave it `False`". The flag is actually per key. It is `False`
only for keys that existed, already disarmed in the parent, when a later pooled call pickled the store. A key that a
pooled call computes for the first time is written armed by the worker. Measured with `gap4/side.py`, which records
the sidecar and a fresh store asking for `purge_disk_on_gc=True`:

```
[('2','range'), ('2','gradient_x_range')]  {'range': (False, False), 'gradient_x_range': (True, True)}
[('1','range'), ('2','gradient_x_range')]  {'range': (False, False), 'gradient_x_range': (True, True)}
[('2','range'), ('1','gradient_x_range')]  {'range': (True, True),  'gradient_x_range': ('no sidecar', 'untracked')}
```

The record's measurement used one feature for every call, so it could not show this. A warm-restart consumer that
adds features run by run (iof3D) gets a mix of `True` and `False` keys that the stated rule does not predict. The
parenthetical "(by the pickling of a pooled run)" also omits the explicit writers that record the disarmed flag in
the same way: `offload_image_data_to_disk()` and `offload(pickle_container=True)` (`disk_backed_image_store.py:346-366`).

**Fix:** "A key's sidecar records `purge_disk_on_gc` as it is when the key's codec pair is written: by the
pickling of a pooled run, or by `offload(pickle_container=True)`. A key that a pooled call computes for the first
time is recorded as configured. A key that already existed, and was disarmed in the parent, when a later pooled call
or an explicit codec offload wrote it is recorded `False`." Add the multi-feature sequence to 030's measurement.

## Info

### IN-01: "A dangling `<key>.dat` link cannot be cleared through `purge` (`KeyError`) and has to be unlinked by hand" holds only for an untracked key with no `<key>.npy`

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:129-130`, `:213-214`, `:273-274` (and, more precisely,
`:76-78`); `src/pc2img/tiled_generator.py:202-203`; BC-P2I-027 and BC-P2I-030 (3).

**Issue:** Measured with `gap4/links.py`:
- A tracked key whose `k.dat` is replaced by a dangling in-cache link: `add` raises `StorePurgeAliasedArtefactError`, then `purge("k")` succeeds and removes the link, and the re-add succeeds.
- The same holds for an untracked key whose `k.npy` is on disk.
- Only a lone dangling link raises `KeyError`, which was the measured shape.

Most of the sites state the `KeyError` without qualification. Only `_refuse_linked_write_path` says "an untracked key", and it still misses the `.npy` case.
**Fix:** "a dangling `<key>.dat` for a key that is neither tracked nor has a `<key>.npy` cannot be cleared through
`purge` (`KeyError`); otherwise `purge(key)` removes it".

### IN-02: "runs only after a `generate()` call returns" should say "returns successfully"

**File:** `src/pc2img/tiled_generator.py:183` and `:269`.
**Issue:** A call that raises also returns control. Elsewhere the text says "after a successful return" (`:303-304`,
`:328`). The two bare forms read as including failed calls, which is the opposite of the meaning.
**Fix:** "runs only after a `generate()` call returns successfully".

## Checked and accurate

- The AST is identical with docstrings stripped (all three files), and the verifier is green.
- The failed-batch paragraph (`:164-176`) matches the code at `:293-306`: only generators that existed before the call are dropped; a failing first call has nothing to drop or keep; a pooled-failure retry with a `cache_path` adopts; without one, a new temporary directory is used.
- The ownership sentence (`:131-134`) is accurate.
- The link refusal for an adopted payload and for a dangling target (`StorePurgeAliasedArtefactError`) is accurate.
- A loop at `k.dat` raises a bare `RuntimeError`, not `StorePurgeRefusedError`.
- `enable_caching=False` lost no files in any retry shape: `1→1`, `1→-1`, seq-prelude `1→-1`, and `-1→1`, 2 runs each.
- The test docstrings match the test bodies, apart from the attribution in WR-02.

---

_Reviewed: 2026-10-05T12:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
