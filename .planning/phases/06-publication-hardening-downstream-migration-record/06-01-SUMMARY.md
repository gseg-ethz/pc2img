---
phase: 06-publication-hardening-downstream-migration-record
plan: 01
subsystem: testing
tags: [hygiene, ruff, sphinx, uv, pytest, publication, packaging]

# Dependency graph
requires: []
provides:
  - "Parametrized planning-vocabulary gate (tests/test_hygiene.py) scanning every git-tracked path outside .planning/ and .claude/"
  - "Whole shipped tree green against that gate (pyproject.toml, CONTRIBUTING.md, .github/workflows/ci.yml, the two swept test modules, the image store module)"
  - "docs/pchandler-2x-break-audit.md relocated under .planning/phases/02-.../ "
  - "scripts/01_tiled_image_generation_from_pointcloud.py (broken import) deleted"
  - "pyproject.toml doc group on Sphinx 8.2.3/<8.3 + sphinx_rtd_theme; dev group + pre-commit/pyyaml; full [project.urls] (Homepage/Documentation/Repository/Issues/Changelog); uv.lock re-locked"
affects: [06-publication-hardening-downstream-migration-record later plans (CI/CD kit adoption, first promotion to main, migration record)]

# Actuals (#2632)
actuals:
  tokens: 13148
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: [sphinx_rtd_theme, pre-commit, pyyaml (dev/doc dependency-groups), "sphinx bumped 5.1 -> 8.2.3,<8.3"]
  patterns:
    - "Planning-vocabulary gate: parametrize one pytest case per `git ls-files` path (minus stripped prefixes), scanning for internal ID-family/phase/plan-reference regexes, with an explicit path->reason exemption dict and a word-boundary self-check proving public hyphenated identifiers are never clipped"
    - "A gate whose own source must contain the literal it scans for builds that literal from concatenated string parts, so the gate's own file never contains the contiguous match it produces at runtime (self-referential-scan problem)"

key-files:
  created: []
  modified:
    - tests/test_hygiene.py
    - scripts/smoke_pipeline.py
    - CONTRIBUTING.md
    - tests/test_image_store.py
    - tests/test_rrim_features.py
    - src/pc2img/image_cache/disk_backed_image_store.py
    - pyproject.toml
    - uv.lock
    - .github/workflows/ci.yml

key-decisions:
  - "Widened Task 2's actual scope to also fix .github/workflows/ci.yml's 2 vocabulary hits, do pyproject.toml's comment-only vocabulary sweep, and relocate docs/pchandler-2x-break-audit.md, all ahead of their nominal Task 3 placement -- Task 2's own <verify> runs the full `pytest -q` suite (which includes the whole-tree gate), so it could not pass while those files stayed red. Rule 3 (auto-fix blocking issue), no architectural change."
  - "Built the gate's `.planning/` literal and its regex fragment from concatenated string parts (`\".\" + \"planning\" + \"/\"`) rather than a literal `.planning/` substring, because tests/test_hygiene.py is itself a git-tracked, non-exempted scan target and the literal-in-source form always self-matched"
  - "CONTRIBUTING.md's measured coverage baseline refreshed twice in sequence (253 passed after Task 2's file count, then 252 after Task 3 deleted the broken script) to keep the documented number honest at each state, rather than guessing the final total up front"

requirements-completed: [CICD-02]

coverage:
  - id: D1
    description: "Planning-vocabulary gate exists, is parametrized over the whole shipped tree with a stated exemption, and is red before the sweep (has teeth)"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary"
        status: pass
      - kind: unit
        ref: "tests/test_hygiene.py::test_public_identifiers_are_not_flagged"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every shipped file (pyproject.toml, CONTRIBUTING.md, ci.yml, the two test modules, the store module) passes the gate; the IP signoff record stays byte-identical"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary (full parametrized run, -k planning_vocabulary)"
        status: pass
      - kind: other
        ref: "git diff --quiet 52fdb00 -- docs/ip/rrim-eth-signoff.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "docs/pchandler-2x-break-audit.md relocated under .planning/phases/02-.../; scripts/01_tiled_image_generation_from_pointcloud.py (broken import) deleted"
    requirement: CICD-02
    verification:
      - kind: other
        ref: "test -f .planning/phases/02-.../pchandler-2x-break-audit.md && test ! -e docs/... && test ! -e scripts/01_..."
        status: pass
    human_judgment: false
  - id: D4
    description: "pyproject.toml doc group on Sphinx 8.2.3,<8.3 + sphinx_rtd_theme; dev group + pre-commit/pyyaml; full [project.urls]; uv.lock consistent"
    requirement: CICD-02
    verification:
      - kind: other
        ref: "uv lock --check"
        status: pass
      - kind: unit
        ref: "python -c 'import sphinx, sphinx_rtd_theme, yaml, pre_commit; assert sphinx.__version__.startswith(\"8.2.\")'"
        status: pass
    human_judgment: false
  - id: D5
    description: "No runtime behaviour changed: full suite green, smoke script still prints OK"
    requirement: CICD-02
    verification:
      - kind: integration
        ref: "uv run --frozen pytest -q (252 passed)"
        status: pass
      - kind: integration
        ref: "uv run --frozen python scripts/smoke_pipeline.py"
        status: pass
    human_judgment: false

duration: 32min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 1: Publication-Hardening Public-Tree Hygiene Summary

**Parametrized planning-vocabulary gate scanning the whole shipped tree, driven green across every tracked file, with the phase-2 audit relocated, the broken tiled script deleted, and pyproject.toml's doc toolchain moved to Sphinx 8.2.3 + sphinx_rtd_theme.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-09-28T13:10:00Z
- **Completed:** 2026-09-28T13:41:36Z
- **Tasks:** 3 completed
- **Files modified:** 9 (plus 1 relocated, 1 deleted)

## Accomplishments

- Added `tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary`, a parametrized gate over every `git ls-files` path outside `.planning/`/`.claude/`, scanning for internal decision/requirement/review-ledger/artifact-name codes (case-sensitive) and phase/plan references (case-insensitive), with a single stated exemption for `docs/ip/rrim-eth-signoff.md` and a word-boundary self-check proving public identifiers like `BC-P2I-001`/`BC-GSEG-006` are never clipped.
- Swept `scripts/smoke_pipeline.py`'s docstring/comments to plain technical prose (no behaviour change beyond a ruff import-order fix).
- Swept `CONTRIBUTING.md`, `tests/test_image_store.py`, `tests/test_rrim_features.py` and `src/pc2img/image_cache/disk_backed_image_store.py` to plain technical prose, and fixed two shipped-text accuracy items: the `__delitem__` history clause (now states the WR-04-corrected mechanism — a refused delete dropped in-memory membership before the ValueError, not a non-atomic unlink) and the shape-rule docstring pointer (now names `_assert_image_shape`, the actual enforcement point, instead of only `DiskBackedImageData.__init__`).
- Relocated `docs/pchandler-2x-break-audit.md` to `.planning/phases/02-dependency-adaptation-reproducible-environment/` (`git mv`, content unchanged) and deleted `scripts/01_tiled_image_generation_from_pointcloud.py` (imports a module, `pc2img.tiled_image_generation`, that no longer exists).
- Updated `pyproject.toml`: `[dependency-groups].doc` moved from `sphinx ~= 5.1` to `sphinx ~= 8.2.3, <8.3` + `sphinx_rtd_theme`; `[dependency-groups].dev` gained `pre-commit` and `pyyaml`; `[project.urls]` gained `Repository`/`Issues`/`Changelog` and `Documentation` now points at the future Read the Docs site. Re-locked `uv.lock` and verified `uv sync --frozen --group doc`.
- Refreshed CONTRIBUTING.md's measured coverage baseline (62% branch coverage, 252 passed / 0 xfailed, measured 2026-09-28).

## Task Commits

Each task was committed atomically (Task 2 and Task 3 each split across two commits — see Deviations):

1. **Task 1: Planning-vocabulary gate + smoke_pipeline.py swept** — `8d9e7c6` (test)
2. **Task 2: Sweep CONTRIBUTING.md/tests/store + required ci.yml/pyproject.toml/docs-relocation deviation** — `879b13a` (docs)
3. **Task 3a: Delete the broken tiled script** — `773f537` (build)
4. **Task 3b: pyproject.toml dependency-groups/urls + uv.lock re-lock** — `ed11421` (build)

_Note: `773f537` and `ed11421` are both Task 3 — a `git add` invocation with one already-deleted pathspec failed atomically partway through staging, so the deletion landed in its own commit before the remaining files could be staged and committed separately. Both commits are real, atomic, and individually correct; together they are Task 3's full diff._

## Files Created/Modified

- `tests/test_hygiene.py` — planning-vocabulary gate + public-identifier self-check
- `scripts/smoke_pipeline.py` — docstring/comment sweep, ruff import-order fix
- `CONTRIBUTING.md` — vocabulary sweep, refreshed coverage baseline
- `tests/test_image_store.py` — vocabulary sweep, `_assert_image_shape` pointer fix
- `tests/test_rrim_features.py` — vocabulary sweep
- `src/pc2img/image_cache/disk_backed_image_store.py` — vocabulary sweep, `__delitem__` history clause fix (WR-04)
- `.github/workflows/ci.yml` — 2 vocabulary hits removed (comment-only; file is wholly replaced by a later Phase 6 plan's CI/CD kit adoption)
- `pyproject.toml` — doc/dev dependency-groups, `[project.urls]`, comment sweep
- `uv.lock` — regenerated
- `docs/pchandler-2x-break-audit.md` → `.planning/phases/02-dependency-adaptation-reproducible-environment/pchandler-2x-break-audit.md` (moved, content unchanged)
- `scripts/01_tiled_image_generation_from_pointcloud.py` (deleted)

## Decisions Made

- Widened Task 2's actual scope to include `.github/workflows/ci.yml`'s 2 vocabulary hits, pyproject.toml's comment-only vocabulary sweep, and the docs relocation, ahead of their nominal Task 3 placement — see Deviations.
- Built the gate's `.planning/` literal from concatenated string parts rather than writing it directly, so the gate's own source file (itself a scanned, non-exempted target) never contains the contiguous substring its own regex searches for.
- Kept `.github/workflows/ci.yml`'s substantive content untouched (trigger, jobs, steps) — only its 2 comments were reworded. The file is wholly replaced by a later Phase 6 plan's git-strategy kit adoption, so this sweep is a temporary, low-cost fix, not wasted effort if the later plan lands cleanly on top of it.
- `[project.urls]` keys recapitalized (`homepage`/`documentation` → `Homepage`/`Documentation`) for consistency with the three newly-added Title Case keys (`Repository`/`Issues`/`Changelog`) rather than mixing conventions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 2's own full-suite verify required files nominally scoped to Task 3**

- **Found during:** Task 2, running its own `<verify>` block (`uv run --frozen pytest -q`, which must show zero failed/error)
- **Issue:** The planning-vocabulary gate parametrizes over the *whole* shipped tree, so `pytest -q` exercises every file's gate test regardless of which task's `<files>` list mentions it. `.github/workflows/ci.yml` (not listed in any task's `<files>`), `pyproject.toml`'s comments, and `docs/pchandler-2x-break-audit.md`'s relocation are all nominally Task 3 work, but Task 2's own hard-gated verify could not reach zero-failed while those stayed red.
- **Fix:** Removed `.github/workflows/ci.yml`'s 2 vocabulary hits (comment rewording only, no behaviour change — this workflow file is superseded wholesale by a later Phase 6 plan's CI/CD kit adoption). Did the pyproject.toml comment-only vocabulary sweep (matching the same 10 comments Task 3's own action item separately enumerates, so Task 3 did not re-do this work — it only added the dependency-group/URL content). Relocated `docs/pchandler-2x-break-audit.md` via `git mv` (Task 3's action item 1, done one task early, content unchanged).
- **Files modified:** `.github/workflows/ci.yml`, `pyproject.toml` (comments only, in the Task 2 commit), `docs/pchandler-2x-break-audit.md` → relocated path
- **Verification:** `uv run --frozen pytest tests/test_hygiene.py -q -k planning_vocabulary` — 0 failed at Task 2's completion; Task 3 then added only its substantive dependency-group/URL/uv.lock changes on top.
- **Committed in:** `879b13a` (Task 2 commit)

**2. [Rule 1 - Bug] The gate's own source self-flagged on its first run**

- **Found during:** Task 1, first full run of the new gate (`tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary[tests/test_hygiene.py]`)
- **Issue:** The gate's regex source and its `_STRIPPED_PREFIXES` tuple both needed to contain the literal string `.planning/` to detect it in *other* files, but `tests/test_hygiene.py` is itself a git-tracked, non-exempted scan target — so the file always flagged its own definition.
- **Fix:** Built the literal from concatenated string parts (`"." + "planning" + "/"`) and fed it through `re.escape()` when composing the regex, so the file's raw source text never contains the contiguous 10-character sequence its own pattern searches for, while the compiled regex still functions correctly against other files' content.
- **Files modified:** `tests/test_hygiene.py`
- **Verification:** `tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary[tests/test_hygiene.py]` passes; full gate run unaffected.
- **Committed in:** `8d9e7c6` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking cross-task dependency, 1 self-referential-scan bug).
**Impact on plan:** Both were necessary to satisfy the plan's own explicit hard-gated verify commands. No scope creep beyond what Tasks 2/3 already specified as their eventual content — work was reordered, not invented. Task 3's own commit ended up containing only its remaining, genuinely-Task-3 content (dependency-group/URL additions, uv.lock re-lock, script deletion).

## Issues Encountered

- A `git add pyproject.toml uv.lock CONTRIBUTING.md scripts/01_tiled_image_generation_from_pointcloud.py` invocation included one already-deleted path (staged earlier via `git rm`), which made the whole `git add` call fail atomically with `fatal: pathspec ... did not match any files` — none of the four paths were staged, not just the bad one. Discovered via `git show --stat HEAD` immediately after the resulting commit showed only the deletion. Recovered by re-staging the three remaining files correctly and creating a second, accurately-scoped commit (`ed11421`) — no history was rewritten or lost.

## User Setup Required

None — no external service configuration required in this plan (account actions for the CI/CD kit adoption, Read the Docs import, etc. are D-30 checkpoints in later Phase 6 plans).

## Next Phase Readiness

- The whole shipped tree (minus `.planning/`/`.claude/`) now passes the planning-vocabulary gate, satisfying the D-18 precondition ("all public-tree hygiene lands on develop-gsd before the first promotion") for this plan's share of the work.
- `pyproject.toml`'s doc toolchain (Sphinx 8.2.3 + sphinx_rtd_theme) is ready for the minimal Sphinx site a later Phase 6 plan builds (D-13).
- `[project.urls]` carries the Repository/Issues/Changelog entries D-14 calls for; `Documentation` points at the Read the Docs URL ahead of the actual RTD project import (a D-30 checkpoint in a later plan).
- `.github/workflows/ci.yml` still needs its wholesale replacement by the git-strategy kit (a separate, larger later plan) — this plan only kept it gate-clean in the interim.
- No blockers for the next plan in this phase.

## Self-Check: PASSED

- All 10 key files verified present on disk (`tests/test_hygiene.py`, `scripts/smoke_pipeline.py`, `CONTRIBUTING.md`, `tests/test_image_store.py`, `tests/test_rrim_features.py`, `src/pc2img/image_cache/disk_backed_image_store.py`, `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`, the relocated `.planning/phases/02-.../pchandler-2x-break-audit.md`).
- Confirmed absent: `docs/pchandler-2x-break-audit.md`, `scripts/01_tiled_image_generation_from_pointcloud.py`.
- All 4 commit hashes (`8d9e7c6`, `879b13a`, `773f537`, `ed11421`) verified present in `git log --oneline --all`.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*
