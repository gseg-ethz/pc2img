---
phase: 03-test-ci-foundation
plan: 02
subsystem: testing
tags: [pytest, xfail, triage, green-baseline, test-suite, version-control]

# Dependency graph
requires:
  - phase: 03-test-ci-foundation
    plan: 01
    provides: "[tool.pytest.ini_options] scoping collection to tests/ (testpaths, importlib, xfail_strict=false) + pinned pytest 9.1 / pytest-cov 5.0 / coverage 7.0"
provides:
  - "green scoped tests/ suite (0 failed, 0 collection errors) reached by triage only — the SC1 anchor Plan 03's coverage baseline + CI gate sit on"
  - "tracked test baseline: the three surviving pc2img test modules are now in git (were working-tree-only) so a fresh CI checkout has a suite to run"
  - "src/pc2img/features/rrim.py brought under version control unchanged (test_rrim_features.py's filesystem-loaded dependency)"
  - "11 @pytest.mark.xfail(strict=False) markers parking the current failures as tracked Phase-5 debt (flip to XPASS when fixed)"
affects: [03-03-baseline-ci, phase-05-bugfix-coverage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "green-by-triage (D-01): delete import-broken pre-refactor modules + xfail(strict=False) the current failures — never fix bugs to reach green (that is Phase 5)"
    - "mixed-class marker discipline: per-method xfail on classes with a pass/fail mix, class-level xfail only on all-failing classes (confirmed against a live run)"
    - "xfail reason strings name the observable failure AND point at Phase 5 so an XPASS reads as a re-classify signal"

key-files:
  created:
    - src/pc2img/features/rrim.py
    - tests/test_disk_backed_image_data.py
    - tests/test_point_cloud_image_generator.py
    - tests/test_rrim_features.py
  modified: []
  deleted:
    - tests/test_disk_backed_image_store.py
    - tests/test_lazy_disk_cache.py

key-decisions:
  - "D-02 applied: deleted the two import-broken pre-refactor modules outright (rely on git history)"
  - "D-03 applied: parked the 11 live-verified failures as xfail(strict=False) with distinct Phase-5-pointing reasons"
  - "Rule-3 deviation: committed the previously-untracked surviving test baseline + rrim.py so the phase's green + CI premise holds on a fresh checkout"

patterns-established:
  - "The committed suite must be green on a fresh checkout — only test modules + their filesystem-loaded dependency (rrim.py) enter git; editor/IDE/config cruft stays untracked"
  - "Live-run-driven triage: the xfail set is built from an actual `uv run pytest` FAILED list, not a static count"

requirements-completed: [TEST-01]

# Metrics
duration: 2min
completed: 2026-07-09
status: complete
---

# Phase 3 Plan 2: Green-by-Triage Test Baseline Summary

**Reached a green scoped `tests/` suite by triage only — deleted the two import-broken pre-refactor modules, parked the 11 live-verified current failures as `xfail(strict=False)` with distinct Phase-5-pointing reasons, and (deviation) brought the previously-untracked surviving test baseline + `rrim.py` under version control so the green + CI premise holds on a fresh checkout.**

## Performance

- **Duration:** ~2 min
- **Tasks:** 2
- **Files committed:** 4 paths (3 surviving test modules + `rrim.py`); 2 broken modules removed

## Accomplishments

- **Triaged to green (D-01/D-02/D-03).** Deleted `tests/test_disk_backed_image_store.py` (imports the removed `pc2img.image_generation.ImageGeneratorFromPCD`) and `tests/test_lazy_disk_cache.py` (imports the deleted `_old.v1` package) — exactly the two remaining collection errors. Parked the current failures as `@pytest.mark.xfail(strict=False)`. Result: `uv run python -m pytest tests/` reports **15 passed, 11 xfailed, 0 failed, 0 errors**, and `uv run pytest --collect-only -q` exits 0.
- **Live-verified the failure set.** Ran `uv run pytest tests/ -v` and confirmed the FAILED list matches the RESEARCH-enumerated 11 exactly — **no delta**: the 10 in `test_disk_backed_image_data.py` + `test_point_cloud_image_generator.py::test_constructor_normalizes_omitted_lazy_disk_cache_config`. The `explicit_none` variant passes and is left unmarked (asserted via `ast` parse → `EXPLICIT_NONE_UNMARKED_OK`).
- **Marker discipline preserved passing tests.** Per-method marks on `TestOffloadingAndLoading` and `TestArrayInterfaceAndPickling` (mixed pass/fail classes) so their passing methods stay live; class-level marks only on `TestCacheFileFinalization` (4/4 fail) and `TestPurgeToggle` (3/3 fail) after confirming every method fails.
- **Made the phase actually work on a fresh checkout (deviation, see below).** The `tests/` directory was entirely untracked; committed the three surviving modules + `rrim.py` so Plan 03's CI has a suite to run.

## xfail Markers Applied (11 total, all `strict=False`, each names the failure + points at Phase 5)

| Node | Placement |
|------|-----------|
| `test_disk_backed_image_data.py::TestOffloadingAndLoading::test_offload_without_cache_path_logs_warning` | per-method |
| `test_disk_backed_image_data.py::TestArrayInterfaceAndPickling::test_getstate_with_cache_path_unloads_data` | per-method |
| `test_disk_backed_image_data.py::TestArrayInterfaceAndPickling::test_pickle_roundtrip_with_cache` | per-method |
| `test_disk_backed_image_data.py::TestCacheFileFinalization` (4 methods) | class-level |
| `test_disk_backed_image_data.py::TestPurgeToggle` (3 methods) | class-level |
| `test_point_cloud_image_generator.py::test_constructor_normalizes_omitted_lazy_disk_cache_config` | per-method |

`import pytest` was added to `test_point_cloud_image_generator.py` (it lacked it); `test_disk_backed_image_data.py` already imported pytest.

## Task Commits

1. **Task 1: Establish the tracked suite baseline** — `019e9ed` (`test:`) — removed the two import-broken modules and brought the three surviving test modules + `rrim.py` under version control (collection clean, exit 0).
2. **Task 2: Park current failures as xfail** — `1829f70` (`test(triage):`) — added the 11 `xfail(strict=False)` markers (suite green).

## Files Created / Modified / Deleted

- **Created (brought under version control):** `tests/test_disk_backed_image_data.py` (+ xfail markers), `tests/test_point_cloud_image_generator.py` (+ `import pytest` + xfail), `tests/test_rrim_features.py`, `src/pc2img/features/rrim.py` (unchanged).
- **Deleted:** `tests/test_disk_backed_image_store.py`, `tests/test_lazy_disk_cache.py` (were untracked → removed from the working tree; never entered git).

## Deviations from Plan

### Auto-fixed / Auto-handled Issues

**1. [Rule 3 - Blocking] `tests/` was entirely untracked — the plan's `git rm` assumption was false.**
- **Found during:** Task 1 setup. `git ls-files tests/` was empty and `git log --all -- tests/` had zero history — the whole `tests/` directory lived only in the working tree, on no branch. The plan's instruction to "Use `git rm` so the deletion is staged" could not execute (you cannot `git rm` an untracked file), and a literal triage would have committed nothing meaningful while Plan 03's CI (a fresh `actions/checkout`) would collect zero tests and fail the `--cov-fail-under` floor.
- **Resolution:** Surfaced as a decision checkpoint; owner selected Option A. Removed the two broken modules with plain `rm` (untracked, so they never enter git) and committed the surviving baseline so the green + CI premise holds on a clean checkout.
- **Files:** `tests/test_disk_backed_image_data.py`, `tests/test_point_cloud_image_generator.py`, `tests/test_rrim_features.py`.
- **Commit:** `019e9ed`.

**2. [Rule 3 - Blocking] Committed the pre-existing untracked production module `src/pc2img/features/rrim.py` unchanged.**
- **Reason:** `rrim.py` was an untracked production module that `test_rrim_features.py` loads by filesystem path; without it a fresh CI checkout could not run that test (suite red → CI red). Brought under version control **unchanged — no behavior change** — required for the phase's green-baseline + CI premise to hold on a clean checkout. This is a version-control action, not a `src/` edit / bug fix (Phase 5 owns behavior changes).
- **File:** `src/pc2img/features/rrim.py`.
- **Commit:** `019e9ed`.

**3. [Note] Coordinator commit-path list contained a typo.**
- The Option-A instruction listed `tests/test_lazy_disk_cache.py` among the paths to commit — but that is one of the two modules being **deleted**. Resolved by the stated governing principle ("the committed suite must be green on a fresh checkout; only test modules + `rrim.py` enter git"): committed the three **surviving** modules (`test_disk_backed_image_data.py`, `test_point_cloud_image_generator.py`, `test_rrim_features.py`) + `rrim.py`, and did not commit either deleted module.

## Scope Boundary Honored

Every `git add` was scoped to explicit paths. Left untracked/unstaged as instructed: `scripts/v1.0/`, `scripts/v2.0/`, the numbered `scripts/0X_*.py`, `_tests/`, `.vscode/`, `.codex`, `pyrightconfig.json`, `.editorconfig`, and the modified `.planning/config.json`. No `git add tests/` (would have swept in `__pycache__` and the deleted modules). No `src/` production code was edited (only `rrim.py` tracked unchanged).

## Issues Encountered

- The plan's Task-2 verify snippet uses `status=$?`, but `status` is a **read-only variable in zsh** (this environment's shell), so the snippet's own `[ "$status" -eq 0 ]` gate reported a false Exit-1 while pytest itself reported `15 passed, 11 xfailed`. Re-ran the exit-code capture with a non-reserved variable (`rc=$?`) → `pytest_exit=0`, `SUITE_GREEN`. The suite is genuinely green; only the verify snippet's variable name collided with zsh. (Bash-run CI in Plan 03 is unaffected.)

## Verification Results

- `uv run python -m pytest tests/` → **15 passed, 11 xfailed, 0 failed, 0 errors** (`pytest_exit=0`, `SUITE_GREEN`).
- `uv run pytest --collect-only -q` → exit 0 (`collect_exit=0`); only the three surviving modules collect.
- `XFAIL_PRESENT` (grep `[0-9]+ xfailed`); `EXPLICIT_NONE_UNMARKED_OK` (`ast` parse asserts the explicit-None test carries no xfail decorator).
- Both deleted modules absent from the tree and from git (`BOTH_GONE`); `git ls-files tests/` lists exactly the three surviving modules.

## Next Phase Readiness

- Plan 03 (baseline + CI) can now measure coverage on the green suite and wire the CLI-only `--cov`/`--cov-fail-under` gate; the suite is committed so a fresh `actions/checkout` has tests to run.
- The 11 xfails are tracked Phase-5 (BUG-05 candidate) inputs; each XPASS in Phase 5 is a re-classify signal (not classified here per D-04).
- No blockers.

## Self-Check: PASSED

- FOUND: src/pc2img/features/rrim.py
- FOUND: tests/test_disk_backed_image_data.py
- FOUND: tests/test_point_cloud_image_generator.py
- FOUND: tests/test_rrim_features.py
- CONFIRMED GONE: tests/test_disk_backed_image_store.py, tests/test_lazy_disk_cache.py
- FOUND: commit 019e9ed (Task 1)
- FOUND: commit 1829f70 (Task 2)

---
*Phase: 03-test-ci-foundation*
*Completed: 2026-07-09*
