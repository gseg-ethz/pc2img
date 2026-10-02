---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 01
subsystem: image-cache
tags: [gsegutils-0.6, pchandler-2.1.1, numpy-2.2, uv-lock, disk-backed-store, purge, containment]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "the hardened DiskBackedImageStore wrapper and its containment overrides, which this plan deletes in favour of upstream"
provides:
  - "pyproject.toml pins pchandler >= 2.1.1, ~= 2.1; GSEGUtils ~= 0.6.0; numpy >= 2.2, < 2.4 (one-way, D-01/D-02/D-21)"
  - "uv.lock re-resolved on GSEGUtils 0.6.0 / pchandler 2.1.1 / numpy 2.2.6 (137 packages, was 193), the RAPIDS cuml/cuproj/dask-cudf stack gone"
  - "DiskBackedImageStore reduced to a thin wrapper: no containment helper, no private path-builder overrides, no __delitem__; overwrite goes through upstream purge"
  - "tests/test_image_store.py green on the 0.6 contract (29 tests)"
  - "Per-finding D-11/D-12 triage table (in 07-01-PLAN.md) as the approved disposition record later plans cite"
affects: [07-02 snapshot corpus, 07-03 tiled re-generate race xfail, 07-06 migration record / BC entries, 07-07 D-03 copy, 0.11.0 promotion]

actuals:
  tokens: 12691
  tasks: 3
  commits: 3
plan_head_before: 49507b549dd2f9b134e7a1bf3cf10513c4d242b0
plan_head_after: 07ac22c384d39155cdce8e004b2d7fce806f9b09

tech-stack:
  added: []
  patterns:
    - "thin wrapper over upstream DiskBackedStore: containment via the public get_npy_path free function, delete verb is purge"
    - "in-process provenance assert (metadata version == module __version__, attribute fingerprint of the withdrawn builder absent) instead of trusting the lock"

key-files:
  created: []
  modified:
    - pyproject.toml
    - uv.lock
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_image_store.py

key-decisions:
  - "Task 1 (blocking-human gate) resolved by the owner directly with the orchestrator: 'proceed' - the three pin strings are written exactly as specified and GSEGUtils 0.6.0 / pchandler 2.1.1 from PyPI are accepted as first-party"
  - "add_image_to_store keeps exactly one containment-first statement (public get_npy_path) before the shape check and before purge on overwrite (D-22)"
  - "purge refusal family (StorePurgeRefusedError a RuntimeError; StorePurgeIncompleteError an OSError) is documented in the add_image_to_store docstring and surfaces unwrapped, not caught (D-10 spirit)"
  - "review-r4-da637a8dfe3c (bare assert in _assert_image_shape) stays deferred per O-2; disk_backed_image_data.py not touched"

patterns-established:
  - "Docstring text written into shipped files passes the planning-vocabulary gate (no ids, no phase/plan references)"

requirements-completed: [DEP-05]

coverage:
  - id: D1
    description: "Three one-way dependency pins written and uv.lock re-resolved on GSEGUtils 0.6.0 / pchandler 2.1.1 / numpy 2.2.6; resolved build proven 0.6.x in-process"
    requirement: "DEP-05"
    verification:
      - kind: other
        ref: "uv lock --check && uv run --frozen python -c '...provenance...' -> provenance ok 0.6.0 2.1.1 2.2.6"
        status: pass
    human_judgment: false
  - id: D2
    description: "Six stale RAPIDS [tool.uv.sources] bindings and the 0.5.3 pin comment removed; proven inert by reproduction"
    requirement: "DEP-05"
    verification:
      - kind: other
        ref: "grep gate 'sources-clean'; byte-identical lock with/without the bindings (in-repo re-lock and from-scratch resolve)"
        status: pass
    human_judgment: false
  - id: D3
    description: "DiskBackedImageStore carries no containment helper / private builders / __delitem__; overwrite purges; single-cloud pipeline runs through it"
    requirement: "DEP-05"
    verification:
      - kind: e2e
        ref: "scripts/smoke_pipeline.py -> OK shape=(260, 200) finite_fraction=0.961 min=8.801 max=11.269 artifacts=['range.dat']"
        status: pass
      - kind: integration
        ref: "tests/test_rrim_features.py tests/test_manager.py tests/test_point_cloud_image_generator.py tests/test_disk_backed_image_data.py (77 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "tests/test_image_store.py pins the 0.6 semantics (del drops tracking, purge removes memmap + codec pair, setter refuses an escaping key, symlinked-entry purge outcomes)"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: "tests/test_image_store.py (29 passed); full suite 286 passed"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-02
status: complete
---

# Phase 7 Plan 01: Adopt GSEGUtils 0.6.0 Summary

**Pins moved to GSEGUtils ~= 0.6.0 / pchandler >= 2.1.1 / numpy >= 2.2,<2.4 and re-locked, the orphaned containment and `__delitem__` overrides deleted from `DiskBackedImageStore`, overwrite routed through upstream `purge`, and the store tests rewritten for the 0.6 contract**

## Performance

- **Duration:** 4 min (clock-measured; ~09:26Z to ~09:30Z)
- **Started:** 2026-10-02T09:26:02Z
- **Completed:** 2026-10-02T09:30:17Z (code); SUMMARY and state updates after
- **Tasks:** 3 (Task 1 resolved by the owner before execution; Tasks 2 and 3 executed)
- **Files modified:** 4 (`pyproject.toml`, `uv.lock`, `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_image_store.py`)

## Accomplishments

- On the old pins, a plain install resolved GSEGUtils 0.6.0 and the shipped tree failed 30 tests (the override called a `super()` method 0.6.0 deleted). That is closed: the lock now resolves 0.6.0 and the full suite is 286 passed.
- The store is now a thin wrapper. `add_image_to_store` is exactly four statements: `get_npy_path(self.cache_dir, img_name)` (key + containment, upstream `StoreKeyError`), `_assert_image_shape`, `purge` on an existing key, `add_data_to_store`.
- Provenance is proven in-process, not assumed: metadata version equals `GSEGUtils.__version__`, starts with `0.6.`, and the upstream class no longer has the 0.5.x private npy-path builder.
- Behaviours reproduced by running code (scratch script, not by reading): all three escape spellings (`../victim`, absolute, `a/../../victim`) raise `ValueError` (`StoreKeyError`), an escaping key with a bad-shape raster raises `StoreKeyError` not `AssertionError`, no file is created or changed outside the cache dir, and a fresh store never serves the pre-overwrite raster after an overwrite.

## Task Commits

1. **Task 1: Confirm the pin strings (checkpoint:decision, blocking-human)** - no commit. Owner answered **"proceed"** directly with the orchestrator; the strings `pchandler >= 2.1.1, ~= 2.1`, `GSEGUtils ~= 0.6.0`, `numpy >= 2.2, < 2.4` were written exactly, and GSEGUtils 0.6.0 / pchandler 2.1.1 from PyPI were accepted as first-party.
2. **Task 2: End-to-end on GSEGUtils 0.6.0 (tracer)** - two commits:
   - `a69ca05` `build(deps)`: pins, six RAPIDS bindings deleted, comment rewritten, re-lock
   - `1d1f9f2` `fix(image_cache)`: override deletion, purge-on-overwrite, docstrings, `Mapping` annotation
3. **Task 3: Bring tests/test_image_store.py to green** - `07ac22c` `test(image_store)`

**Plan metadata:** committed separately (docs: complete plan).

## Task 2 evidence

**Precondition:** `curl -s https://pypi.org/pypi/GSEGUtils/json` -> `info.version` = `0.6.0` (no 0.6.1; met).

**Resolved versions (uv.lock):** gsegutils 0.6.0, pchandler 2.1.1, numpy 2.2.6, numba 0.61.2, llvmlite 0.44.0. Before: gsegutils 0.5.3, pchandler 2.1.0, numpy 2.0.2 (installed).

**Lock package count:** before 193, after 137 (`grep -c '^\[\[package\]\]' uv.lock`).

**O-3 reproduction (the six RAPIDS bindings are inert):**

- (a) pins moved, all ten bindings present: `uv lock` -> 137 packages, dropped-RAPIDS entries (`cuml|cuproj|dask-cudf` `-cu11|-cu12`) = 0, `sha256sum uv.lock` = `791397d9bf8f7fc3af9658e668ffe5df26188ccee608966c0618246fdc496d53`
- (c) six bindings deleted, `uv lock` again -> `sha256sum uv.lock` = `791397d9bf8f7fc3af9658e668ffe5df26188ccee608966c0618246fdc496d53` (equal to (a)).
- Honest caveat on (c): the second in-repo `uv lock` printed `Resolved 137 packages in 0.99ms`, i.e. uv judged the existing lock still satisfied rather than re-resolving, so on its own that equality is weak evidence. I therefore also resolved **from scratch** (no existing lock) in two throwaway git repos holding this `pyproject.toml` with and without the six bindings: both `Resolved 138 packages`, 0 RAPIDS entries, identical `sha256` `cfbbb7cbe25ccc1976b2e3dcec5701046109aaea4dd32d7d3834245ad94c1ec8`. The 138 vs 137 difference is one extra package (`cloudpickle`) that a fresh resolve picks up and the incremental re-lock of the committed lock does not; it is the same with and without the bindings. Conclusion: the bindings never influenced resolution.
- Remaining `[tool.uv.sources]` lines (`grep -nE '^(cudf|cuspatial)-cu1[12]' pyproject.toml`):
  - `135:cudf-cu12      = { index = "nvidia" }`
  - `136:cuspatial-cu12 = { index = "nvidia" }`
  - `137:cudf-cu11      = { index = "nvidia" }`
  - `138:cuspatial-cu11 = { index = "nvidia" }`
- `sources-clean` printed; no `0.5.3` anywhere in `pyproject.toml`.

**Provenance (exact command, run after `uv lock --check && uv sync`):**

```
uv run --frozen python -c "import importlib.metadata as m, GSEGUtils; from packaging.version import Version; from GSEGUtils.lazy_disk_cache import DiskBackedStore; v=m.version('GSEGUtils'); assert v.startswith('0.6.') and v == GSEGUtils.__version__, v; p=m.version('pchandler'); assert Version(p) >= Version('2.1.1'), p; assert not hasattr(DiskBackedStore, '_get_npy_path'); print('provenance ok', v, p, m.version('numpy'))"
provenance ok 0.6.0 2.1.1 2.2.6
```

**Tracer gate:** after the two commits, `scripts/smoke_pipeline.py` printed `OK shape=(260, 200) finite_fraction=0.961 min=8.801 max=11.269 artifacts=['range.dat']` and the four end-to-end modules (`test_rrim_features`, `test_manager`, `test_point_cloud_image_generator`, `test_disk_backed_image_data`) gave 77 passed. Logged `Tracer verified end-to-end - expanding`.

**Tests left red for Task 3 at the end of Task 2** (exactly the 12 the blast-radius spike predicted, all in `tests/test_image_store.py`): `test_overwrite_does_not_leave_stale_on_disk_raster`, `test_delete_purges_on_disk_codec_pair`, `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op`, `test_failed_delete_preserves_codec_pair_and_both_stores`, `test_adopted_key_delete_purges_shared_pair`, `test_escaping_key_delete_refuses_and_leaves_outside_file_intact[x3]`, `test_refused_overwrite_leaves_existing_entry_intact`, `test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact[codec_offloaded]`, `test_successful_overwrite_serves_the_replacement_after_offload_and_reload`, `test_symlinked_cache_entry_is_served_and_unpickles`.

## Task 3 evidence

- `tests/test_image_store.py`: 29 passed (`grep -c 'def test_'` = 19; parametrised cases make up the rest). Full suite: 286 passed. Planning-vocabulary gate: 82 passed. `ruff check` and `ruff format --check` on `src tests`: clean.
- `git grep -nE '_get_npy_path|_get_meta_path|_assert_within_cache_dir' -- src tests` prints nothing (exit 1, `no-withdrawn-names`).
- **Pure renames to the public free functions:** `test_overwrite_does_not_leave_stale_on_disk_raster`, `test_failed_delete_preserves_codec_pair_and_both_stores`, `test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact`, `test_successful_overwrite_serves_the_replacement_after_offload_and_reload` (the fifth rename, the absent-key delete test, was folded away instead, D-12).
- **Rewritten on the 0.6 semantics:** `test_delete_purges_on_disk_codec_pair` -> `test_purge_removes_the_codec_pair_and_the_memmap`; `test_adopted_key_delete_purges_shared_pair` -> `test_adopted_key_purge_removes_shared_pair`; `test_escaping_key_delete_refuses_and_leaves_outside_file_intact` -> `test_escaping_key_setter_refuses_and_key_is_never_tracked` (x3 spellings); `test_symlinked_cache_entry_is_served_and_unpickles` keeps the serve/unpickle half, its escape tail now runs through `get_npy_path`; `test_delete_tracked_key_without_on_disk_pair_succeeds` comment reworded.
- **Added:** `test_symlinked_entry_with_outside_target_purge_is_refused`, `test_symlinked_entry_with_inside_target_purge_removes_link_and_payload`.
- **Deleted:** `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op` (folded into the two-store sensor, D-12) and `test_refused_overwrite_leaves_existing_entry_intact` (premise unreachable: upstream refuses the escaping key at set time).
- `grep -n 'sub/nested' tests/test_image_store.py` -> line 472, inside `with pytest.raises(ValueError):`.
- Mutation check by running code: replacing `self.purge(img_name)` with `del self[img_name]` in the store makes `test_overwrite_does_not_leave_stale_on_disk_raster` fail (a fresh store re-adopts the stale raster); the file was restored afterwards (clean `git status`). Removing the containment pre-check statement leaves the suite green because `add_data_to_store` validates the same key upstream; the containment-before-shape precedence (D-22) is pinned by the 07-02 snapshot test, as planned, not here.
- Measured outcome of the two symlink tests on 0.6.0 (scratch script before writing them): outside target -> `StorePurgeForeignArtefactError` (a `StorePurgeRefusedError`, a `RuntimeError`), links and both payload files untouched, entry still served; inside target -> purge succeeds, links and payload (`range.npy`, `range.meta.json`) removed (the shared store's own `range.dat` remains, as it belongs to that store).

## Files Created/Modified

- `pyproject.toml` - three pin strings; six stale RAPIDS source bindings deleted; `NOTE:` comment rewritten in plain words (no planning vocabulary)
- `uv.lock` - re-resolved; 193 -> 137 packages
- `src/pc2img/image_cache/disk_backed_image_store.py` - thin wrapper; `from pathlib import Path` dropped, `Mapping` and `get_npy_path` imported; class docstring states the threat model once; `add_image_to_store` docstring states the four-step ordering, the `StoreKeyError`-before-`AssertionError` precedence, the `purge` refusal family and the two residuals that still lose the old entry
- `tests/test_image_store.py` - rewritten for the 0.6 contract (see Task 3 evidence)

## Decisions Made

- Followed the plan's locked decisions (D-01, D-02, D-07..D-10, D-21, D-22) and the owner's Task 1 `proceed`.
- `review-r4-da637a8dfe3c` (bare `assert` in `_assert_image_shape`) stays deferred per owner disposition O-2; `disk_backed_image_data.py` untouched.
- The `offload(features=...)` vs upstream `keys=` kwarg drift is recorded in the plan's triage table only (no action, D-11 step 4).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Docstring contained the literal the verify gate counts**
- **Found during:** Task 2 verification
- **Issue:** the plan's verify requires `grep -c 'get_npy_path(self.cache_dir, img_name)'` to be exactly 1; my first `add_image_to_store` docstring repeated that exact call text, giving 2.
- **Fix:** reworded the docstring step to "the upstream `get_npy_path` builder validates the key..." so the call statement is the only match.
- **Files modified:** `src/pc2img/image_cache/disk_backed_image_store.py`
- **Verification:** grep count 1; ruff clean; hygiene gate 88 passed
- **Committed in:** `1d1f9f2` (amended into the Task 2 store commit before anything depended on it)

**2. [Rule 1 - Verification weakness] The in-repo second `uv lock` was a no-op, so the byte-identical check was not by itself a reproduction**
- **Found during:** Task 2 step 2(c)
- **Issue:** uv reported `Resolved 137 packages in 0.99ms` (lock considered satisfied), so equal sha256 values between (a) and (c) prove little.
- **Fix:** added a from-scratch resolve with and without the six bindings in scratch repos (identical sha256, 0 RAPIDS entries). Recorded above with the 138 vs 137 explanation.
- **Files modified:** none (scratch work only)
- **Verification:** both sha256 values recorded in the Task 2 evidence

---

**Total deviations:** 2 (1 blocking-gate wording, 1 verification-strength). **Impact:** no scope change; no behaviour differs from the plan.

## Issues Encountered

- `uv sync` removed the `doc` dependency group's packages (sphinx etc.) from `.venv` because `doc` is opt-in; unrelated to this plan, restorable with `uv sync --group doc`.
- The suite has no loky `n_jobs >= 2` tiled test, so it cannot see the tiled re-generate race recorded in the spikes (D-20); that is planned in 07-03 and 07-06, not here.

## Known Stubs

None. No hardcoded-empty values, placeholders or unwired data introduced.

## Threat Flags

None. No new network endpoints, auth paths or trust-boundary file access beyond what the plan's threat model (T-07-01..T-07-04, T-07-SC) already covers. T-07-01 (traversal via crafted scalar-field names) is mitigated by the upstream `StoreKeyError`, reproduced above; T-07-02 (cached 0.5.x wheel) by the in-process provenance assert.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 07-02 (snapshot corpus re-pinning every insertion route and the containment-before-shape precedence) and 07-03 (tiled re-generate race xfail).
- Follow-up for the owner (outside this plan, per D-21): `.claude/CLAUDE.md` still says `numpy ~= 2.0`; not edited here.
- Observation left as is (outside O-3's scope): the four remaining `cudf`/`cuspatial` bindings and the `nvidia` index resolve from `pypi.org/simple` in both the old and new lock, so they are not consulted either.

## Self-Check: PASSED

- `pyproject.toml`, `uv.lock`, `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_image_store.py` exist and are committed.
- Commits `a69ca05`, `1d1f9f2`, `07ac22c` found in `git log`; `git rev-list --count 49507b5..HEAD` = 3 at the time of writing.
- Task acceptance criteria re-run: pin strings (1/1/1), `sources-clean`, provenance line, `store-shape-ok`, smoke OK, 286 passed, no withdrawn names, hygiene and ruff clean.

---
*Phase: 07-gsegutils-0-6-adoption-0-11-0-release*
*Completed: 2026-10-02*
