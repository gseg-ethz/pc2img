---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-05T11:09:10Z
depth: standard
diff_base: c43d6f0
head: c5f1ed5
files_reviewed: 3
files_reviewed_list:
  - src/pc2img/tiled_generator.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_tiled_generator.py
findings:
  critical: 2
  warning: 0
  info: 2
  total: 4
status: issues_found
---

# Phase 7: Code Review Report (gap round 5, 07-23: final reading check, docs-only)

**Reviewed:** 2026-10-05T11:09:10Z
**Depth:** standard (reading check; every claim below was reproduced by running code)
**Files Reviewed:** 3, plus `.planning/MIGRATION-v0.11.md` BC-P2I-027 and BC-P2I-030 as the record
**Status:** issues_found

## Summary

**Scope.** `git diff c43d6f0..HEAD` over the three files and `.planning/MIGRATION-v0.11.md`. The behaviour defects
(GSEGUtils#83 family, deferred to pc2img 0.11.1) are not findings here. Every finding is about whether the shipped
text is accurate and whether it calls any state safe. All scripts are in
`scratchpad/gap5/`. Each scenario ran in a fresh process with a fresh `cache_path`, using two tiles where `t1` lacks
`intensity`.

**(1) Docs-only: confirmed.** The docstring-stripped AST of each file was compared with `c43d6f0`
(`gap5/ast_ident.py`). All three are identical. The working tree equals HEAD, `git status --porcelain -- src tests`
is empty, and no line over 120 characters was added. The record still has 30 rows, and
`_scrap/pc2img-migration-verifier.py` prints `[ok] verified 30 entries`.

**(3) The recommended route works in a script.** `gap5/route.py` sweeps these dimensions:
- prelude: none, a successful `n_jobs=1` call, or a successful pooled call;
- failing call: `n_jobs=1` or `2`;
- retry: `n_jobs=1` or `2`;
- retry features: the same features after the input is fixed, or a subset without the failing feature;
- route: the gc route, a fresh generator over a fresh `cache_path` after the block, or the same inside the block.

For each run, it drops the failed call's remaining references and calls `gc.collect()`. It then offloads and reads
every returned raster and every store entry:

```
gc route     (leave block, gc.collect(), retry)   fail n_jobs=1: 24 runs, 0 lost   fail pooled: 36 runs, 0 lost
fresh generator + fresh cache_path, after block   fail n_jobs=1: 36 runs, 0 lost   fail pooled: 36 runs, 0 lost
fresh generator + fresh cache_path, inside block  fail n_jobs=1: 36 runs, 0 lost   fail pooled: 36 runs, 0 lost
negative control (retry inside block, same gen)   LOST 6/10 entries, 2 of 2 runs
```

(Four gc/"same features" shapes that keep generators could not be run. The kept `t1` generator holds its original
point cloud, so swapping `pcd_tiles` does not fix the input. The subset variant covers those histories.)

**The gc route is not sound for an interactive user (CR-01).** At the CPython prompt, an uncaught exception stays
referenced through `sys.last_exc`, `sys.last_value` and `sys.last_traceback`. The user cannot "let it go out of
scope", and the retried rasters are deleted later, when the next uncaught error in the session releases it.

**(2) Unconditional safety claims remain (CR-02).** The round converted the Known-limitations text to "may" wording.
Four sentences in the same touched docstrings, and one in BC-P2I-030, still state without condition that kept-store
entries and dropped generators never delete their files, whatever `n_jobs`. Measured: after a failed `n_jobs=1`
call, they do.

**(4) Consistency and readability.** Apart from the items below, the docstrings and BC-P2I-027/030 match sentence for
sentence. The link-check paragraph is now separate from the upstream heading. The test docstring's attribution is
correct.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: "Let the exception go out of scope, call `gc.collect()`, then retry" loses the retried rasters in an interactive session, where an uncaught exception never goes out of scope

**File:** `src/pc2img/tiled_generator.py:189-192`; `.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 Known limitations
(2), same sentence)

**Issue:** The plainest way to retry interactively is this: the failing call raises at the prompt (or in a notebook
cell), then the user runs `gc.collect()` and calls `generate()` again. An outside reader believes the exception is out
of scope by then, because nothing they wrote holds it. CPython's interactive loop does hold it, in
`sys.last_exc` / `sys.last_value` / `sys.last_traceback`, until the next uncaught exception replaces it. At that
moment the failed call's armed entries are collected and unlink the retried `<tile_id>/<key>.dat`. That later error
can be any typo. Measured with `python -i < gap5/repl_typo.py`: a failing `n_jobs=1` call at the prompt, then
`gc.collect()`, then the retry, then a read, then a mistyped `prnt(...)`, then a read again.

```
REPL gc-route result: clean []   NameError: name 'prnt' is not defined   after a later typo: LOST [('t0','gradient_x_range','FileNotFoundError')]   (3 of 3 runs)
same, pooled failure (n_jobs=2), sys.last_* cleared instead of the typo:                       LOST in 4 of 6 runs (gap5/repl_pool.py)
fresh TiledPointCloudImageGenerator over a fresh cache_path, same REPL sequence:               clean, 2 of 2 (gap5/repl_fresh.py)
```

The loss is delayed and silent. The retried result reads correctly at first and fails only after an unrelated
mistake. Debuggers (`pdb.pm()`) and any code that stores the exception keep it alive in the same way. IPython and
Jupyter, which also set `sys.last_*`, were not measured here, because IPython is not installed. The second route, a
fresh `cache_path`, does not depend on the exception's lifetime and stayed clean in every shape tested (144 script
runs and the REPL).

**Fix (wording only), the same in the docstring and BC-P2I-030 (2):**

```text
  Do not retry inside the ``except`` block, and do not rely on ``gc.collect()`` while the exception
  is still referenced. In an interactive session or notebook, and under a debugger, an uncaught
  exception stays referenced (``sys.last_exc``) until a later error replaces it, so there retry with
  a fresh ``TiledPointCloudImageGenerator`` over a fresh ``cache_path``. In a script, either retry
  that way, or let the exception go out of scope (nothing may keep a reference to it or its
  traceback), call ``gc.collect()``, then retry.
```

You could also list the fresh-`cache_path` route first as the recommended route. It is the only one that does not
depend on who holds the exception.

### CR-02: Four sentences still state that kept-store entries and dropped generators never delete their files, "whatever `n_jobs`". After a failed `n_jobs=1` call they do.

**File:**
- `src/pc2img/tiled_generator.py:119-131` (**Disk persistence**: "Entries returned by any `generate()` call
  (`n_jobs=1` included) and the entries of the stores kept in `image_generators` have purge-on-garbage-collection
  disabled … released results and dropped generators no longer delete their cache files at all, whatever `n_jobs` …
  All of them persist until `purge()` is called or the directory is removed")
- `src/pc2img/tiled_generator.py:264-270` (`generate()`: "Entries returned by any call (`n_jobs=1` included), and the
  entries of the stores kept in `image_generators`, never delete their `.dat` memmap on garbage collection … The tile
  directory keeps those files until `purge` is called or the directory is removed")
- `src/pc2img/image_cache/disk_backed_image_store.py:308-309` ("`del` / `pop` / `clear` drop tracking only … Only
  `purge` removes files")
- `.planning/MIGRATION-v0.11.md:79` (BC-P2I-030 Disk persistence: "The consequence is that released results and
  dropped generators no longer delete their cache files at all, whatever `n_jobs` … They persist until `purge()` is
  called or the directory is removed")

**Issue:** This round's acceptance rule is that the shipped text calls no configuration safe from the failed-call
hazard. These sentences do exactly that, with no condition, for kept-store entries and for dropped generators. The
`generate()` paragraph then contradicts itself in its last sentence ("the entries a call that raised added to kept
stores stay armed"). The class docstring contradicts its own Known limitations bullets 1 and 3. Measured with
`gap5/kept.py`: a successful first call, then a failing `n_jobs=1` call, then `gc.collect()`, then the flags of the
kept entries are read, then `image_generators.clear()` and `gc.collect()`.

```
seq  prelude: kept-store flags {'t0': {'range': False, 'scalar_field_intensity': True, 'gradient_x_range': True}, 't1': {'range': False}}
              .dat deleted by dropping the generators: ['t0/gradient_x_range.dat', 't0/scalar_field_intensity.dat']
pool prelude: identical flags; identical deletions
```

Both claims are false here. Kept-store entries are armed, so purge-on-gc is not "disabled". And dropping the
generators deleted two cache files, which means they do not persist until `purge()`. A reader who trusts "never
delete" may hold or drop kept-store entries after a failed call. For a warm-restart user, sequential `.dat` files
that were never offloaded to a codec pair are gone. The text was left from earlier rounds, but it sits in the
docstrings this round edited, and it fails the round's own criterion.

**Fix (wording only):** qualify each sentence with "successful" and point at the limitation. For example:
- Class: "Entries returned by a successful `generate()` call (`n_jobs=1` included), and the entries of the stores in
  `image_generators` after a successful call, have purge-on-garbage-collection disabled … after a successful call,
  released results and dropped generators no longer delete their cache files … Entries a failed call added may still
  delete their `.dat` when collected (see Known limitations)."
- `generate()`: the same qualifier, and "The tile directory keeps the files of successful calls until …".
- Store: "Only `purge` removes files deliberately; an entry that still has delete-on-collection armed removes its
  `.dat` when it is collected (see the non-owner caveat above)."
- BC-P2I-030: "after a successful call, released results and dropped generators no longer delete …; entries a failed
  call added may (see Known limitations)."

## Info

### IN-01: Held-entry advice and the 0.11.1 promise are worded differently in the class docstring, the store docstring and the record

**File:** `src/pc2img/tiled_generator.py:176-195` versus `src/pc2img/image_cache/disk_backed_image_store.py:296-304`;
BC-P2I-027 versus BC-P2I-030.
**Issue:** The store docstring and BC-P2I-027 say "In general, do not hold entries taken from the tile stores across a
regenerate". The class docstring and BC-P2I-030 (3) put the same advice under the heading "Known limitations after a
failed call". A reader of the tiled class alone concludes that holding entries is fine when no call failed, which
the store text does not allow. The class and BC-P2I-030 say fixes "are planned for pc2img 0.11.1". The store and
BC-P2I-027 still say the fix "follows in pc2img 0.11.1", which is a firmer promise than the softened wording.
**Fix:** Move the held-entry bullet out from under the failed-call heading, or prefix it "In general,". Use "planned
for" at all four sites.

### IN-02: "`gc.collect()` there … collects nothing while the exception is still referenced" is overstated

**File:** `src/pc2img/tiled_generator.py:189-190`; BC-P2I-030 (2).
**Issue:** `gc.collect()` inside the handler collects any unrelated garbage. What it cannot collect is the failed
call's objects that the traceback reaches. The sentence is falsifiable as written, and it is the kind of absolute
statement this round set out to remove.
**Fix:** "it cannot collect the failed call's objects while the exception is still referenced" (folded into the CR-01
wording above).

## Checked and accurate

- AST identity (all three files), the verifier is green, and the record has 30 rows.
- The script-run route is sound. The gc route after leaving the block, and a fresh generator over a fresh
  `cache_path` (inside or after the block), lost nothing in 204 runs. The runs covered the n_jobs=1 and pooled
  failures, three call histories, retries at `n_jobs=1` and `2`, and same-feature and subset retries. The negative
  control lost on every run.
- "With the default `enable_caching=False` nothing is written to disk": seq and pooled calls, each including a failing
  call, with `TMPDIR` redirected, created only empty directories (`gap5/nocache.py`). The default is hard-coded
  upstream (`LazyDiskCacheConfig.enable_caching: bool = False`), not environment-dependent.
- The retry bullet's mechanism ("may rewrite … may unlink … may raise `FileNotFoundError`") and the
  "do not retry inside the `except` block" instruction match the negative control.
- The sidecar paragraph is stated as "may", with a check-the-value instruction. It makes no per-call rule, so nothing
  in it can be falsified.
- The link-check paragraph (pc2img's own, both error classes, dangling and adopted links refused, symlink loop as a
  bare `RuntimeError`) matches `_refuse_linked_write_path` at `disk_backed_image_store.py:84-100`. The removed
  "cannot be cleared through `purge`" claim is gone from every site.
- The test docstrings match the test bodies, and the armed-entries attribution in
  `test_a_failing_sequential_call_keeps_the_tile_generators` is now correct.

---

_Reviewed: 2026-10-05T11:09:10Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
