---
phase: 04-code-quality-algorithmic-soundness-review
plan: 01
subsystem: testing
tags: [ruff, uv, pytest, pyproject, tooling, hygiene, pep735]

# Dependency graph
requires:
  - phase: 03-testing
    provides: "pytest ~= 9.1 + coverage config, testpaths=[tests], --strict-markers, xfail_strict=false baseline (15 passed / 11 xfailed)"
provides:
  - "ruff ~= 0.15 declared in [dependency-groups].dev (black removed); uv.lock regenerated"
  - "tests/test_hygiene.py — Wave 0 import-smoke + metadata + ruff-clean gate (the QUAL-01 target)"
affects: [04-02, 04-04, code-quality, hygiene-sweep]

# Tech tracking
tech-stack:
  added: [ruff ~= 0.15]
  patterns:
    - "Wave 0 target tests authored before the FIX work — xfail(strict=False) markers track the target state and stay green under --strict-markers until the sweep lands"
  removed: [black ~= 23.10]

key-files:
  created:
    - tests/test_hygiene.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "Chose ruff to replace black (D-11 default: lower-churn, ruff format is black-equivalent) rather than keeping both"
  - "Split the metadata target into two distinct xfail tests (keywords, viz extra) plus a separate ruff-clean xfail so 04-02 and 04-04 executors can flip each marker independently — matches the plan's documented 1 pass + 3 xfail contract"
  - "No [tool.ruff] config block added here — deferred to plan 04-02 per plan instruction"

patterns-established:
  - "Wave 0 hygiene gate: LIVE import-smoke (must stay green) + xfail(strict=False) target checks that xpass as later plans land"

requirements-completed: [QUAL-01]

coverage:
  - id: D1
    description: "ruff ~= 0.15 declared in the dev dependency-group, black removed, uv.lock regenerated"
    requirement: "QUAL-01"
    verification:
      - kind: unit
        ref: "python -c \"import tomllib; g=tomllib.load(open('pyproject.toml','rb'))['dependency-groups']['dev']; assert any(x.startswith('ruff') for x in g) and not any(x.startswith('black') for x in g)\""
        status: pass
      - kind: other
        ref: "uv sync (exit 0; black/mypy-extensions/pathspec/platformdirs uninstalled, ruff==0.15.21 installed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "tests/test_hygiene.py Wave 0 gate exists: import-smoke LIVE, metadata/viz/ruff-clean checks xfail until 04-02/04-04"
    requirement: "QUAL-01"
    verification:
      - kind: unit
        ref: "tests/test_hygiene.py (1 passed / 3 xfailed; full suite 16 passed / 14 xfailed)"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-10
status: complete
---

# Phase 04 Plan 01: Wave 0 Hygiene Scaffolding Summary

**Swapped black→ruff ~= 0.15 in the PEP 735 dev group (uv.lock relocked) and authored tests/test_hygiene.py — the Wave 0 import-smoke + metadata + ruff-clean gate the QUAL-01 sweep must satisfy.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-10T15:00:56Z
- **Completed:** 2026-07-10T15:03:27Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments
- Replaced `black ~= 23.10` with `ruff ~= 0.15` in `[dependency-groups].dev` (D-09/D-11); left pytest/memory_profiler/pytest-cov/coverage and the `doc` group untouched
- Regenerated `uv.lock` via `uv sync` (exit 0): black, mypy-extensions, pathspec, platformdirs uninstalled; `ruff==0.15.21` installed
- Authored `tests/test_hygiene.py`: a LIVE import-smoke gate over `pc2img` + 5 submodules plus three `xfail(strict=False)` target checks (keywords-not-placeholder, viz-extra-exists, `ruff check src/` clean)
- Verified the Wave 0 contract exactly: hygiene file 1 passed / 3 xfailed; full suite 16 passed / 14 xfailed (Phase-3 baseline 15/11 + 1 pass + 3 xfail), no unexpected passes under `--strict-markers`

## Task Commits

Each task was committed atomically:

1. **Task 1: Swap black → ruff in the dev dependency-group and relock** - `b8c34f7` (chore)
2. **Task 2: Author tests/test_hygiene.py smoke + metadata + lint gate** - `3564c9d` (test)

## Files Created/Modified
- `pyproject.toml` - `[dependency-groups].dev` now lists `ruff ~= 0.15`, no `black`
- `uv.lock` - regenerated for the black→ruff swap
- `tests/test_hygiene.py` - Wave 0 import-smoke (LIVE) + metadata/viz/ruff-clean checks (xfail until 04-02/04-04)

## Decisions Made
- **ruff replaces black (not additive):** D-11's default; ruff format is black-equivalent, lower toolchain churn.
- **Three distinct xfail tests, not one:** split the metadata target into `keywords` + `viz-extra` checks plus a separate `ruff-clean` check so the 04-02 and 04-04 executors can flip each marker off independently as their work xpasses. This yields the plan's documented `1 pass + 3 xfail` shape.
- **No `[tool.ruff]` block here:** deferred to 04-02 per the plan; adding config now would let the ruff-clean check surface findings prematurely.

## Deviations from Plan

None - plan executed exactly as written.

_(One implementation refinement, not a deviation: I initially parametrized the import-smoke into 6 separate tests, which produced 6 pass / 2 xfail. I restructured to a single import-smoke test plus three distinct xfail tests to match the plan's explicit `1 pass + 3 xfail` acceptance criterion and to give downstream executors independent marker granularity. Final state matches the plan.)_

## Issues Encountered
- `uv sync` emitted a benign hardlink warning ("Failed to hardlink files; falling back to full copy") because the cache and target are on different filesystems. Non-fatal, exit 0, resolution reflected in uv.lock. No action needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The Wave 0 target exists: 04-02 (pyproject metadata cleanup + `[tool.ruff]` config + `viz` extra) will make `test_pyproject_keywords_not_placeholder` and `test_pyproject_viz_extra_exists` xpass — that executor must remove those two `xfail` markers.
- 04-04 (ruff sweep) will make `test_ruff_check_src_is_clean` xpass — remove that `xfail` marker then.
- The LIVE `test_all_submodules_import` is the green gate every hygiene edit (ruff sweep, `__all__` sync, `_TransformArray` guard) must keep passing.

## Self-Check: PASSED

- Files verified: `tests/test_hygiene.py`, `pyproject.toml`, `uv.lock`, `04-01-SUMMARY.md` all present
- Commits verified: `b8c34f7`, `3564c9d` present in git log

---
*Phase: 04-code-quality-algorithmic-soundness-review*
*Completed: 2026-07-10*
