---
phase: 05-bug-fixes-module-test-coverage
plan: 16
subsystem: image-cache
tags: [containment, security, pydantic, disk-backed-store, gsegutils]

requires:
  - phase: 05-bug-fixes-module-test-coverage (plan 05-15)
    provides: the WR-02 containment guard (`_assert_within_cache_dir` routed through `_get_npy_path` / `_get_meta_path`) this plan reorders, rewrites and re-proves
provides:
  - "An atomic __delitem__: a refused delete (ValueError, containment) or a KeyError (membership) is a full no-op, in memory as well as on disk, for every escape spelling and for the overwrite route"
  - "A containment predicate that resolves only the parent directory, so a legitimate symlinked cache entry is served and the store unpickles, while every escape spelling stays refused"
  - "A corrected, measured threat-posture record (store docstring, test comment, BC-NOTES entry 15, UAT reason) stating the containment guard is reachable via the registry default fallback and load-bearing on GSEGUtils 0.5.x"
  - "A narrowed class-docstring containment invariant that claims only what the key builders enforce, plus a pin for the enforced half"
  - "Demonstrated guard-sensitivity: every escaping/refused proving test fails with the guard removed and passes with it live"
  - "DiskBackedImageStore constructor's None-sentinel default (DSN-07), B008 clean; dead root-package logger removed"
affects: [phase-06-gsegutils-adoption, 05-17-rrim-residuals]

actuals:
  tokens: 9191
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - "Containment-check-before-mutation ordering for MutableMapping overrides: build every side-effecting path first, delegate to the base class second, act on disk last"
    - "Parent-directory-only path resolution (path.parent.resolve() / path.name) to distinguish 'escapes the cache directory' from 'is a symlink to something legitimate inside it'"

key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_image_store.py
    - .planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md
    - .planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md

key-decisions:
  - "review-r2-9998f2b36d4c and review-r2-3f625b03fb03 REPRODUCED (both reviewer-asserted findings confirmed by running code before any change), so both took their REPRODUCED branches per D-R4-01 #5"
  - "review-r2-2b9426a42695 folded into the predicate rewrite (resolved cache directory bound once per call); review-r2-6f4507d8c33f folded into the rewritten route-enumeration paragraph (now names the .dat memmap route); review-r2-a7c7f4e498a6 stays deferred to the Phase-6 todo (05-17)"
  - "test_legacy_pkl_refused_as_cache_miss renamed to test_legacy_pkl_degrades_to_cache_miss (out-of-band, no behaviour change): its name collided with the Task 3 mutation-check's -k 'escaping or refused' filter, and it legitimately passes with the containment guard removed (unrelated legacy-.pkl refusal path), which made the literal guard-off assertion false-negative until renamed"

requirements-completed: [BUG-05]

coverage:
  - id: D1
    description: "A refused delete (ValueError) or KeyError leaves the store exactly as it was, in memory and on disk, for every escape spelling and the overwrite route (review-r2-70fb459066a6, BLOCKER)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_refused_delete_leaves_store_membership_intact"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py#test_refused_overwrite_leaves_existing_entry_intact"
        status: pass
    human_judgment: false
  - id: D2
    description: "A legitimate symlinked cache entry is served, not refused, and the store still unpickles, while every escape spelling stays refused (review-r2-9998f2b36d4c)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_symlinked_cache_entry_is_served_and_unpickles"
        status: pass
    human_judgment: false
  - id: D3
    description: "The class docstring's containment invariant is narrowed to what the key builders enforce; an entry inserted through add_image_to_store always carries a cache_path under the cache directory (review-r2-3f625b03fb03)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_store_inserted_entries_carry_a_cache_path_under_the_cache_dir"
        status: pass
    human_judgment: false
  - id: D4
    description: "The threat posture is corrected everywhere it is stated (store docstring, test comment, BC-NOTES entry 15, UAT reason) to state the containment guard is reachable via the registry default fallback and load-bearing on GSEGUtils 0.5.x (review-r2-1a435f413f18)"
    requirement: "BUG-05"
    verification:
      - kind: other
        ref: "grep chain in Task 2 <verify> (false clauses absent, corrected markers present) + registry-fallback reproduction script"
        status: pass
    human_judgment: false
  - id: D5
    description: "Every containment refusal test is demonstrably guard-sensitive (fails with the guard removed, passes with it live), and no test name misdescribes its body"
    requirement: "BUG-05"
    verification:
      - kind: other
        ref: "throwaway no-guard pytest plugin, -k 'escaping or refused' (10 selected, 10 failed guard-off / 10 passed guard-on)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Store constructor uses a None-sentinel default (B008 clean); dead root-package logger removed from the module that actually held it"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py#test_default_config_is_coerced_from_none_sentinel"
        status: pass
      - kind: other
        ref: "ruff check --select B008 src/pc2img/image_cache/disk_backed_image_store.py"
        status: pass
    human_judgment: false

duration: 55min
completed: 2026-09-24
status: complete
---

# Phase 05 Plan 16: Round-4 image-cache gap closure — atomic delete, honest threat posture, guard-sensitive tests

**Closes the round-4 BLOCKER (a refused delete dropped the entry anyway), settles two reviewer-asserted containment claims by running code first, corrects a false threat-posture paragraph that had already propagated into BC-NOTES and UAT, and makes every containment proving test demonstrably guard-sensitive.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-09-24T13:11:00Z (approx.)
- **Completed:** 2026-09-24T14:06:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- `DiskBackedImageStore.__delitem__` now builds both codec paths (running the containment guard) BEFORE delegating to the base store's in-memory delete, so a refused delete — containment `ValueError` or membership `KeyError` — is a genuine no-op, in memory as well as on disk, for all three escape spellings and for the overwrite route through `add_image_to_store`. No membership pre-check was added; the base store remains the single membership authority.
- `_assert_within_cache_dir` now resolves only the parent directory of the candidate path (`path.parent.resolve() / path.name`), not the full path. A cache directory holding a symlinked `<key>.npy` + `<key>.meta.json` pair to a real codec pair elsewhere is now served, deleted (link only — target survives) and pickles/unpickles correctly, while every escape spelling (parent segment, absolute, embedded traversal) is still refused with the exact resolved-candidate message.
- The threat-posture paragraph in the store docstring, the round-3 test-file comment, BC-NOTES entry 15, and the UAT `reason:` line all previously claimed the escaping-key route was unreachable from the feature-name DSL. All four are corrected to state the measured fact: `FeatureRegistry.match`'s unanchored default fallback (`ScalarFieldFeature`, `params={'feature': name}`) reaches the store with a scalar-field name taken verbatim from PLY/E57 metadata, and on the installed GSEGUtils 0.5.3 this guard is load-bearing, not defence-in-depth.
- The class docstring's containment invariant is narrowed to "every on-disk path this store builds FROM A KEY" — an entry inserted through the mapping setter carries its own caller-supplied `cache_path`, which the guard does not see; `offload(pickle_container=False)` writes through it directly (a GSEGUtils carry-out). `add_image_to_store` is pinned to always derive a `cache_path` under the cache directory.
- Every containment refusal test (`escaping`/`refused` in its name) is now demonstrably guard-sensitive: with `_assert_within_cache_dir` monkeypatched to identity in a throwaway, never-committed pytest plugin, all 10 selected tests fail; with the guard live, all 10 pass.
- `DiskBackedImageStore.__init__`'s `config` parameter is now a `None`-sentinel default (DSN-07 pattern), coerced in the constructor body; `ruff check --select B008` is clean. The dead module-level logger — bound to the root package name, misattributed by the UAT finding to `rrim.py`, actually in this store module — is removed.

## Task Commits

Each task was committed atomically (7 commits total):

1. **Task 1: atomic `__delitem__`** — `101c077` (fix)
2. **Task 2: containment predicate + threat-posture corrections** — `f1a81cb` (fix, both reproductions land together), `d1947b4` (docs: BC-NOTES), `13f02b0` (docs: UAT)
3. **Task 3: guard-sensitive tests + constructor default + dead logger** — `d48bf37` (test), `3fad7db` (fix), `b49b4f2` (docs: BC-NOTES entry 17)

## Reproduction Transcripts

All four reproduced by running code, verbatim below (dates: planner 2026-09-24 on `4714b57`; executor re-measured 2026-09-24 on the same HEAD before any change, per the Reproduce-Don't-Read rule).

### 1. review-r2-70fb459066a6 (BLOCKER) — refused delete drops the entry anyway, both routes

```
key in store before delete: True
delete raised ValueError: Refusing raster key path '/tmp/tmp9zqm7md7/cache/../victim.npy': it resolves to '/tmp/tmp9zqm7md7/victim.npy', outside the configured cache directory '/tmp/tmp9zqm7md7/cache'. Raster keys must not escape the cache directory.
key in store AFTER delete attempt: False
len(store): 0
sentinel intact: True
add_image_to_store raised ValueError: Refusing raster key path '/tmp/tmp9zqm7md7/cache2/../victim.npy': it resolves to '/tmp/tmp9zqm7md7/victim.npy', outside the configured cache directory '/tmp/tmp9zqm7md7/cache2'. Raster keys must not escape the cache directory.
key in store2 AFTER overwrite attempt: False
```
**Disposition:** confirmed exactly as claimed. Fixed by reordering `__delitem__` (Task 1). RED confirmed first: 4 xfailed (0 errors, 0 collection failures) against pre-fix HEAD; 0 xfailed/xpassed after the reorder.

### 2. review-r2-9998f2b36d4c — symlinked cache entry, full-path resolution refuses a legitimate link

```
adopted 'range': True
read raised ValueError: Refusing raster key path '/tmp/tmp5rxmuv9f/cache/range.npy': it resolves to '/tmp/tmp5rxmuv9f/shared/range.npy', outside the configured cache directory '/tmp/tmp5rxmuv9f/cache'. Raster keys must not escape the cache directory.
pickle.loads raised ValueError: Refusing raster key path '/tmp/tmp5rxmuv9f/cache/range.npy': it resolves to '/tmp/tmp5rxmuv9f/shared/range.npy', outside the configured cache directory '/tmp/tmp5rxmuv9f/cache'. Raster keys must not escape the cache directory.
delete raised ValueError: Refusing raster key path '/tmp/tmp5rxmuv9f/cache/range.npy': it resolves to '/tmp/tmp5rxmuv9f/shared/range.npy', outside the configured cache directory '/tmp/tmp5rxmuv9f/cache'. Raster keys must not escape the cache directory.
'range' still in store2 after refusal: True   (Task 1's fix already carries into this scenario)
parent_segment -> refused: ... outside the configured cache directory ...
absolute -> refused: ... outside the configured cache directory ...
embedded_traversal -> refused: ... outside the configured cache directory ...
nested -> accepted, path: /tmp/tmp5rxmuv9f/cache/sub/nested.npy
```
**Disposition:** REPRODUCED. Branch taken: rewrite the predicate. `_assert_within_cache_dir` now resolves only `path.parent`, binding the resolved cache directory once per call (folds review-r2-2b9426a42695). `test_symlinked_cache_entry_is_served_and_unpickles` authored xfail-first, confirmed xfail (1 xfailed, isolated `-k symlinked` run), then passed unmarked after the rewrite; all three escape spellings and nesting remain correctly classified.

### 3. review-r2-3f625b03fb03 — value-supplied `cache_path`, store-inserted entry

```
outside exists before offload: True
outside exists after offload: True
outside bytes (first 32): b'\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?\x00\x00\x80?'
cache dir listing: []
store['range'].cache_path: /tmp/tmpy8a17f37/outside.dat
```
(float32 `1.0` little-endian bytes `00 00 80 3F`, repeated — the outside file was overwritten with raster data.)

**Disposition:** REPRODUCED via a STORE-INSERTED entry (`store["range"] = DiskBackedImageData(..., cache_path=<outside>)` then `store.offload("range")`), correcting the prior invalid refutation attempt that used a directly-constructed entry whose offload was a no-op. Branch taken: NARROW the docstring, no enforcement extension. `test_store_inserted_entries_carry_a_cache_path_under_the_cache_dir` pins the enforced half (passed on first run, no marker). Confirmed no `__setitem__` override was added: `git diff "$BASE" -- src/pc2img/image_cache/disk_backed_image_store.py | grep -c "def __setitem__"` = 0.

### 4. review-r2-1a435f413f18 — registry default-fallback reachability, end-to-end

```
match1: ScalarFieldFeature {'feature': '../victim'} []
match2: ScalarFieldFeature {'feature': 'a/../../victim'}
```
End-to-end (`PointCloudData` with scalar field `"../victim"`, `PointCloudImageGenerator(..., "orthographic", "nearest_neighbor", lazy_disk_cache_config=cfg).generate(["../victim"])`):
```
generate raised ValueError: Refusing raster key path '/tmp/tmperbje64_/cache/../victim.npy': it resolves to '/tmp/tmperbje64_/victim.npy', outside the configured cache directory '/tmp/tmperbje64_/cache'. Raster keys must not escape the cache directory.
```
**Disposition:** REPRODUCED exactly as claimed. The threat-posture paragraph is corrected in all four places that carried the false claim: store docstring (`_assert_within_cache_dir`), the round-3 test-file comment block, BC-NOTES entry 15 (relabelled SUPERSEDED + appended Correction bullet), and the UAT `reason:` line for `review-r1-a239bdbfc017` (single-line edit in place, `status:` untouched).

## Mutation Check (Task 3, review-r2-af50d770d73d)

Guard-off run (`-p no_guard_plugin -k "escaping or refused"`, throwaway plugin, never committed):
```
10 failed, 19 deselected in 0.25s
```
Guard-on run of the same selection:
```
10 passed, 19 deselected, 12 warnings in 0.05s
```
Every one of the 10 selected containment refusal tests fails with the guard removed and passes with it live. (One pre-existing test, `test_legacy_pkl_refused_as_cache_miss`, also matched the `-k` filter's `refused` keyword and legitimately passed regardless of the guard — an unrelated legacy-`.pkl` refusal path. Renamed to `test_legacy_pkl_degrades_to_cache_miss`, no behaviour change, to keep the mutation-check selection precise. See Deviations.)

## Disposition of Every Finding This Plan Touched

| Finding | Disposition | Commit |
|---|---|---|
| review-r2-70fb459066a6 (BLOCKER) | Fixed — `__delitem__` reordered, RED-first proven | `101c077` |
| review-r2-1a435f413f18 (major) | Fixed — posture corrected in code, test comment, BC-NOTES, UAT | `f1a81cb`, `d1947b4`, `13f02b0` |
| review-r2-9998f2b36d4c (reviewer-asserted) | REPRODUCED → predicate rewritten (parent-only resolution) | `f1a81cb` |
| review-r2-3f625b03fb03 (reviewer-asserted) | REPRODUCED → docstring narrowed, no enforcement extension | `f1a81cb` |
| review-r2-af50d770d73d (guard-sensitivity) | Fixed — offload moved inside guarded region; mutation check demonstrated | `d48bf37` |
| review-r2-7c8e11c81eed (parametrise delete test) | Fixed — parametrised over the three escape spellings | `d48bf37` |
| review-r2-e3a76c7d3fd0 (unused sentinel binding) | Fixed — sentinel bound and asserted after round trip | `d48bf37` |
| review-r1-c2b69f0885e7 (test-naming truth) | Fixed — renamed + new absent-key test added | `d48bf37` |
| review-r1-8ff7171c6ca4 (IN-03, constructor default) | Fixed — None-sentinel default, BC entry 17 | `3fad7db`, `b49b4f2` |
| review-r1-ab91c4469087 (IN-01, dead logger) | Fixed — artifact path was wrong (rrim.py has no logger); actual dead logger (store module) removed | `3fad7db` |
| review-r2-2b9426a42695 | **Folded** into the predicate rewrite (resolved cache dir bound once per call) | `f1a81cb` |
| review-r2-6f4507d8c33f | **Folded** into the rewritten route-enumeration paragraph (now names `.dat`) | `f1a81cb` |
| review-r2-a7c7f4e498a6 | Deferred to the Phase-6 todo (05-17 owns it) | — |

## IN-01 Artifact-Path Correction

The UAT finding `review-r1-ab91c4469087` named `src/pc2img/features/rrim.py` as the file with a dead logger. `git log --oneline -S getLogger -- src/pc2img/features/rrim.py` returns nothing over the whole reviewed range — rrim.py has never had a logger. The actual dead module-level logger (`logging.getLogger(__name__.split(".")[0])`, bound to the root package name, never used in the file) was line 1/10 of `src/pc2img/image_cache/disk_backed_image_store.py`. This plan removes it there; 05-17 should cite this corrected artifact path in its own evidence line.

## Files Created/Modified

- `src/pc2img/image_cache/disk_backed_image_store.py` — `__delitem__` reordered (containment-before-mutation); `_assert_within_cache_dir` resolves only the parent directory; class docstring and route-enumeration/threat-posture docstrings corrected; constructor default is a `None` sentinel; dead logger + `logging` import removed
- `tests/test_image_store.py` — 2 new proving tests (Task 1), 1 new proving test + 1 new pin test (Task 2), guard-sensitivity fix + parametrisation + sentinel binding + rename + 1 new test + 1 new test + 1 out-of-band rename (Task 3)
- `.planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md` — entry 15 relabelled SUPERSEDED + Correction bullet appended; entry 17 + summary-table row 17 added; one forward-only sentence appended to the Cross-cutting section
- `.planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md` — single-line `reason:` correction on `review-r1-a239bdbfc017`; `status:` untouched

## Decisions Made

- Both reviewer-asserted findings (review-r2-9998f2b36d4c, review-r2-3f625b03fb03) reproduced true; took the REPRODUCED branch per the owner's pre-committed decision (D-R4-01 #5).
- review-r2-2b9426a42695 and review-r2-6f4507d8c33f folded into the predicate/docstring rewrites since both hosts were being rewritten anyway; review-r2-a7c7f4e498a6 stays deferred (05-17).
- `test_legacy_pkl_refused_as_cache_miss` renamed to `test_legacy_pkl_degrades_to_cache_miss` (see Deviations) — out-of-scope-adjacent but necessary to make the plan's own mutation-check verification command discriminate correctly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in the plan's own verification tooling] Task 3's literal mutation-check `<verify>` regex cannot match this project's pytest summary format**
- **Found during:** Task 3, running the exact `<verify>` command for review-r2-af50d770d73d
- **Issue:** The plan's automated check does `grep -qE '^[1-9][0-9]* failed in '` against the `tail -1` summary line. On the installed pytest 9.1.1, any `-k`-filtered run that deselects tests always reports a chained summary (`"N failed, M deselected in Ts"` or, guard-on, `"N passed, M deselected, W warnings in Ts"`), so the literal string `"failed in "` never appears immediately after the count — the check is structurally unsatisfiable in this environment regardless of test correctness.
- **Fix:** Verified the actual property (guard sensitivity) with a format-robust equivalent: extract the `N failed` count via `grep -oE '[0-9]+ failed'` and confirm zero occurrences of `' passed'` in the guard-off summary line, and the symmetric check guard-on. Confirmed 10/10 selected tests fail guard-off and 10/10 pass guard-on — the underlying property the check exists to prove. Both raw summary lines are pasted above (Mutation Check section) for direct inspection.
- **Files modified:** none (verification-only; no source change from this item)
- **Verification:** manual re-run of both the literal and the robust check, transcripts above
- **Committed in:** N/A (verification artifact, not a code change)

**2. [Rule 1 - Bug] Test-name collision defeated the Task 3 mutation-check's own `-k "escaping or refused"` selection**
- **Found during:** Task 3, running the mutation check
- **Issue:** `test_legacy_pkl_refused_as_cache_miss` (pre-existing, unrelated to containment) matched the `-k "escaping or refused"` keyword filter and legitimately passed with the containment guard disabled (its KeyError comes from the legacy-`.pkl` refusal path, not `_assert_within_cache_dir`). This polluted the mutation-check selection with a guard-INsensitive test, producing a false "18/19 deselected + 1 unrelated pass" signal that made even the literal `<verify>` regex's `! grep -q 'passed'` half fail for reasons unrelated to guard-sensitivity.
- **Fix:** Renamed to `test_legacy_pkl_degrades_to_cache_miss` (no behaviour change, docstring updated to explain the rename). tests/test_image_store.py is within Task 3's declared file scope.
- **Files modified:** `tests/test_image_store.py`
- **Verification:** `.venv/bin/pytest tests/test_image_store.py -q` — 33 passed; mutation check now selects exactly the 10 containment-relevant tests
- **Committed in:** `d48bf37`

---

**Total deviations:** 2 auto-fixed (both Rule 1, both in the plan's own verification tooling — no source-code defects found beyond what the plan already anticipated).
**Impact on plan:** No scope creep; both fixes make this plan's own verification gates measure what they claim to measure. No production behaviour changed as a result of either deviation.

## Issues Encountered

- `uv run --frozen pyright src/pc2img/image_cache/disk_backed_image_store.py` (plan-level `<verification>` bullet) could not be run: `pyright` is not installed in this environment and is not a declared dependency in `pyproject.toml`'s `dependency-groups` (only `ruff`, `pytest`, `pytest-cov`, `coverage`, `memory_profiler` under `dev`). 05-15-SUMMARY.md recorded a prior pyright run (2 pre-existing errors, including the `factory` `reportArgumentType` nit this plan's `<verification>` explicitly expects to remain) from a session where the tool was evidently available out-of-band. Per the package-install exclusion in the executor's deviation rules, no attempt was made to install it. The type-relevant changes in this plan (`LazyDiskCacheConfig | None` parameter, `Path.parent.resolve() / path.name` predicate) follow existing typed patterns in the file and introduce no new dynamic-typing surface; this is flagged for 05-17 or a follow-up to confirm with an environment that has `pyright` available.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- The blocker and both reviewer-asserted findings are closed with reproduction evidence; the threat posture is now consistent across code, tests, and planning records.
- 05-17 can cite this plan's disposition table verbatim in its own UAT evidence lines, and should cite the corrected IN-01 artifact path (image_cache store module, not rrim.py).
- Outstanding for 05-17: RRIM residuals (WR-01, WR-04, IN-04, IN-05 not touched here — out of this plan's declared files), the Phase-6 deferral todo (review-r2-a7c7f4e498a6), and all `05-UAT.md` `status:` flips for the findings this plan closed.
- Pending: confirm `uv run --frozen pyright` produces no NEW errors in an environment where the tool is actually available (see Issues Encountered).

## Self-Check: PASSED

- `src/pc2img/image_cache/disk_backed_image_store.py` — FOUND
- `tests/test_image_store.py` — FOUND
- `.planning/phases/05-bug-fixes-module-test-coverage/05-16-SUMMARY.md` — FOUND
- Commits `101c077`, `f1a81cb`, `d1947b4`, `13f02b0`, `d48bf37`, `3fad7db`, `b49b4f2`, `a98a34a` — all FOUND in `git log --oneline --all`
