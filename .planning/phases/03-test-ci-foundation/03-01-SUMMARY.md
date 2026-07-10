---
phase: 03-test-ci-foundation
plan: 01
subsystem: testing
tags: [pytest, coverage, pytest-cov, uv, pyproject, ci-foundation]

# Dependency graph
requires:
  - phase: 02-dependency-adaptation
    provides: committed universal uv.lock + PEP 735 dev/doc dependency-groups
provides:
  - "[tool.pytest.ini_options] scoping collection to tests/ (testpaths, importlib import mode, strict markers, xfail_strict=false)"
  - "[tool.coverage.run]/[tool.coverage.report] branch-coverage config for pc2img (no fail_under in TOML)"
  - "pinned dev test tooling: pytest ~= 9.1, pytest-cov ~= 5.0, coverage ~= 7.0"
  - "regenerated uv.lock in sync with pyproject.toml"
affects: [03-02-green-triage, 03-03-baseline-ci, test-coverage, ci-cd]

# Tech tracking
tech-stack:
  added: [pytest-cov ~= 5.0, coverage ~= 7.0, pytest ~= 9.1 pin]
  patterns:
    - "pytest scoping via testpaths=[\"tests\"] (sibling third_party/ excluded without norecursedirs)"
    - "coverage gate lives on CLI/CI invocation only — --cov never in addopts"
    - "dep edits followed by uv lock + uv sync + uv lock --check (CONTRIBUTING workflow)"

key-files:
  created: []
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "pytest pinned to ~= 9.1 (D-14) rather than downgrading to pchandler's stale pytest ~= 8.4"
  - "pytest-cov ~= 5.0 + coverage ~= 7.0 mirror pchandler's exact pins (D-07)"
  - "branch coverage config added as a justified minimal addition beyond pchandler's CLI-only approach (D-05)"
  - "fail_under intentionally omitted from TOML — coverage stays opt-in, gate deferred to Plan 03 CI (D-05/D-06)"

patterns-established:
  - "Scoping mechanism: testpaths alone is sufficient; norecursedirs/collect_ignore not needed since third_party/ is a sibling of tests/"
  - "Coverage flags belong on CLI/CI only so subset runs never trip a floor"

requirements-completed: [TEST-01, TEST-02]

coverage:
  - id: D1
    description: "pytest collection scoped to tests/ — zero third_party/* ERROR lines; only the two D-02 modules remain (deleted in Plan 02)"
    requirement: "TEST-01"
    verification:
      - kind: automated
        ref: "uv run pytest --collect-only -q | grep ^ERROR (0 non-D-02 error lines, COLLECTION_SCOPED_OK)"
        status: pass
      - kind: automated
        ref: "tomllib parse asserting testpaths==['tests'], addopts exact, no --cov"
        status: pass
    human_judgment: false
  - id: D2
    description: "branch coverage tooling installed + configured for pc2img; no coverage gate in addopts"
    requirement: "TEST-02"
    verification:
      - kind: automated
        ref: "uv run pytest tests/test_rrim_features.py -q (subset run, no cov-fail-under trip, 5 passed)"
        status: pass
      - kind: automated
        ref: "tomllib parse asserting coverage.run.branch is true, source==['pc2img'], no fail_under key"
        status: pass
    human_judgment: false
  - id: D3
    description: "dev group carries pytest ~= 9.1, pytest-cov ~= 5.0, coverage ~= 7.0; uv.lock regenerated and in sync"
    requirement: "TEST-02"
    verification:
      - kind: automated
        ref: "uv lock --check (exit 0) + uv run python -c 'import pytest_cov, coverage, pytest' -> pytest 9.1.1, coverage 7.15.0"
        status: pass
    human_judgment: false

# Metrics
duration: 2min
completed: 2026-07-09
status: complete
---

# Phase 3 Plan 1: Pytest + Coverage Config Foundation Summary

**Greenfield pytest scoping to tests/ plus branch-coverage config and pinned pytest 9.1 / pytest-cov 5.0 / coverage 7.0 dev tooling, with a regenerated in-sync uv.lock.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-09T19:00:03Z
- **Completed:** 2026-07-09T19:01:43Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `[tool.pytest.ini_options]` scoping collection to `tests/` — bare pytest's 1140 collected / 7 errors (recursing into gitignored `third_party/` sibling checkouts) is now scoped to the project suite with zero `third_party/*` ERROR lines. The only remaining collection errors are the two D-02 modules that Plan 02 deletes.
- Added `[tool.coverage.run]`/`[tool.coverage.report]` for branch coverage of the whole `pc2img` package (D-05), with `_version.py` omitted and `exclude_also` guards for `TYPE_CHECKING`, `raise NotImplementedError`, and abstractmethod decorators. Deliberately no `fail_under` in TOML so coverage stays opt-in.
- Kept `--cov` out of `addopts` so subset/single-file runs never measure coverage and trip a floor — verified via a clean `tests/test_rrim_features.py` run.
- Pinned the previously-bare `pytest` to `pytest ~= 9.1` (D-14) and added `pytest-cov ~= 5.0` + `coverage ~= 7.0` (mirroring pchandler's pins, D-07); regenerated `uv.lock` and confirmed `uv lock --check` passes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pytest + coverage config tables to pyproject.toml** - `3944928` (test)
2. **Task 2: Add dev-group test-tooling pins and regenerate uv.lock** - `2d8218e` (chore)

## Files Created/Modified
- `pyproject.toml` - new `[tool.pytest.ini_options]`, `[tool.coverage.run]`, `[tool.coverage.report]` tables; `[dependency-groups].dev` gains `pytest ~= 9.1`, `pytest-cov ~= 5.0`, `coverage ~= 7.0` (bare `pytest` replaced)
- `uv.lock` - regenerated to add `coverage 7.15.0` and `pytest-cov 5.0.0`

## Decisions Made
- **pytest ~= 9.1 (D-14):** pinned the test runner alongside the D-07 additions so local + CI baselines resolve against a known pytest major, consistent with D-09's `uv sync --frozen` posture. pc2img stays on its current pytest 9.1.x (next major gated by `~=`) and deliberately does NOT downgrade to pchandler's stale `pytest ~= 8.4`. This resolves the Codex F1 finding that the pin was previously unrecorded — it is now D-14.
- **pytest-cov ~= 5.0 + coverage ~= 7.0 (D-07):** mirror pchandler's exact pins for cross-library consistency.
- **Branch coverage config (D-05):** added a minimal `[tool.coverage.*]` block (pchandler has none, using CLI-only `--cov` with branch off); D-05 requires branch coverage so this is a justified addition.
- **No `fail_under` in TOML (D-05/D-06):** the coverage gate lives on the CI command line only (Plan 03); coverage stays opt-in locally.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None. `uv sync` emitted a benign hardlink-fallback warning (cache and target on different filesystems); packages installed successfully.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Config half of TEST-01 (scoping) and tooling half of TEST-02 (coverage measurable) are in place.
- Plan 02 (green-triage) can now delete the two D-02 modules (`test_disk_backed_image_store.py`, `test_lazy_disk_cache.py`) so `--collect-only` reaches exit 0.
- Plan 03 (baseline + CI) can wire the CLI-only `--cov`/`--cov-fail-under` gate on top of this config.
- No blockers.

## Self-Check: PASSED

- FOUND: pyproject.toml
- FOUND: uv.lock
- FOUND: 03-01-SUMMARY.md
- FOUND: commit 3944928 (Task 1)
- FOUND: commit 2d8218e (Task 2)

---
*Phase: 03-test-ci-foundation*
*Completed: 2026-07-09*
