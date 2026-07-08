---
phase: 01-branch-untangling-mainline-consolidation
plan: 01
subsystem: infra
tags: [git, branch-consolidation, perspective-projection, projection-strategy]

# Dependency graph
requires:
  - phase: 00-roadmap
    provides: Phase 1 branch-untangling scope, D-01/D-03/D-05/D-06 decisions
provides:
  - PerspectiveProjection strategy landed on the phase-branch mainline (WIP; math deferred to Phase 4/5)
  - "'perspective' key registered in the ProjectionName Literal and PROJECTIONS registry"
  - Archive tag archive/dev-perspective_projection-pre-fold preserving pre-fold remote tip 8f0fae9
  - Stale local dev/perspective_projection label pruned (fully contained)
affects: [04-soundness, 05-tests, 06-publication-hardening]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Archive-tag-before-prune safety net (D-06) for all destructive local git ref ops"
    - "Fold divergent work from the authoritative REMOTE ref, never a stale local label (D-01)"
    - "Self-guarding git branch -d (never -D) as proof-of-containment on prune"

key-files:
  created: []
  modified:
    - src/pc2img/strategies/projection.py
    - src/pc2img/features/manager.py

key-decisions:
  - "Merged origin/dev/perspective_projection (authoritative remote tip 8f0fae9), NOT the stale local dev/perspective_projection (16 commits behind), per D-01 / RESEARCH Pitfall 1"
  - "Used --no-ff to preserve the fold as an explicit merge commit; functional commit scope chore(branch) per CLAUDE.md (no planning-ID scopes)"
  - "Left the folded PerspectiveProjection WIP math untouched (project_raw/inverse_projection NotImplementedError, private-pchandler-API project()) — owned by Phase 4/5 per D-03"

patterns-established:
  - "Disjoint-file-set verification as a provably-conflict-free merge precondition (review finding #6)"
  - "Explicit HEAD assertion (phase branch, not develop-gsd) before any ref mutation (RESEARCH Pitfall 2)"

requirements-completed: [BRANCH-02]

coverage:
  - id: D1
    description: "PerspectiveProjection strategy folded onto the phase-branch mainline, registered under the 'perspective' key"
    requirement: "BRANCH-02"
    verification:
      - kind: automated_ui
        ref: "git grep -l PerspectiveProjection HEAD -- 'src/*' matches strategies/projection.py; git grep '\"perspective\"' HEAD -- src/pc2img/strategies/projection.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fold completeness — zero perspective commits remain outside the fold target"
    requirement: "BRANCH-02"
    verification:
      - kind: other
        ref: "git rev-list --count HEAD..origin/dev/perspective_projection => 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pre-fold remote tip preserved by an archive tag before any perspective ref prune (D-06 safety)"
    verification:
      - kind: other
        ref: "git rev-parse archive/dev-perspective_projection-pre-fold^{commit} == 8f0fae9"
        status: pass
    human_judgment: false
  - id: D4
    description: "Stale local dev/perspective_projection label pruned via self-guarding -d; no remote ref touched"
    verification:
      - kind: other
        ref: "git branch --list dev/perspective_projection empty; archive tag intact"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-08
status: complete
---

# Phase 01 Plan 01: Fold perspective_projection onto phase mainline Summary

**Folded `origin/dev/perspective_projection` (tip `8f0fae9`) onto the phase branch via a clean `--no-ff` 3-way merge, landing the WIP `PerspectiveProjection` strategy under the `"perspective"` key, guarded by a pre-fold archive tag and finished by pruning the now-contained local perspective label.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-08T22:15:52Z
- **Completed:** 2026-07-08T22:18:02Z
- **Tasks:** 3
- **Files modified:** 2 (via the fold merge)

## Accomplishments
- Re-verified fold topology against RESEARCH after `git fetch origin`: remote tip `8f0fae9`, merge-base `91b4ab6` (dev/v2 tip), 12 commits over base, HEAD on the phase branch (not `develop-gsd`), and — the actual conflict-free guarantee — DISJOINT changed-file sets (HEAD touches no `src/`; perspective touches only the two declared files).
- Archive-tagged the pre-fold remote tip (`archive/dev-perspective_projection-pre-fold` → `8f0fae9`) BEFORE any destructive op (D-06), then folded via `git merge --no-ff` — clean, +37/-4 across exactly the two declared files.
- Pruned the fully-contained local `dev/perspective_projection` (`ae69343`) with self-guarding `git branch -d`; `-d` succeeding is itself proof of containment. No remote ref touched.

## Task Commits

Tasks 1 and 3 are read-only / local-ref-only (no working-tree files → no source commit). Task 2's fold IS its commit (the merge).

1. **Task 1: Refresh remote-tracking refs and re-verify fold topology** — no commit (read-only git plumbing; `TOPOLOGY_OK`)
2. **Task 2: Archive-tag remote perspective tip, then fold onto phase branch** — `3f3de26` (chore(branch) merge commit) + tag `archive/dev-perspective_projection-pre-fold` (`FOLD_OK`)
3. **Task 3: Prune the now-contained local perspective branch** — no commit (local ref deletion; `PRUNE_OK`)

**Plan metadata:** committed separately with SUMMARY.md + STATE.md + ROADMAP.md + REQUIREMENTS.md.

## Files Created/Modified
- `src/pc2img/strategies/projection.py` — gains the `@PROJECTIONS.register("perspective") PerspectiveProjection` class and the `"perspective"` entry in the `ProjectionName` Literal; imports `scipy.spatial.transform.Rotation`, `pchandler.geometry.transforms._TransformArray`, `GSEGUtils.base_types` shape types. WIP math untouched.
- `src/pc2img/features/manager.py` — one stray blank line removed (arrived with the fold).

## Decisions Made
- Merged the authoritative REMOTE `origin/dev/perspective_projection`, never the stale local label (D-01 / RESEARCH Pitfall 1).
- `--no-ff` to keep the fold as an explicit merge; functional `chore(branch)` scope per CLAUDE.md (planning-ID scopes would dangle when squashed to `main`).
- Left the folded WIP perspective math as-is (D-03) — soundness and tests are owned by Phase 4/5.

## Deviations from Plan
None - plan executed exactly as written. All three tasks' automated verifications passed on first run (`TOPOLOGY_OK`, `FOLD_OK`, `PRUNE_OK`).

## Issues Encountered
None. Two tracked files (`.planning/STATE.md`, `.planning/config.json`) showed as modified at plan start — these were orchestrator setup edits (state normalization + `_auto_chain_active` flag) made before this agent was spawned, not task work; the fold merge commit correctly touched only the two declared source files.

## Known Deferred Items
- `src/pc2img/strategies/projection.py:212: new blank line at EOF` — a whitespace nit that arrived WITH the folded WIP. Intentionally left as-is (fixing it would touch the D-03-fenced perspective surface); staged for the Phase 4/5 cleanup. Confirmed present via `git diff --check 91b4ab6..HEAD`.
- The folded `PerspectiveProjection` is not runnable as-is: `project_raw()`/`inverse_projection()` raise `NotImplementedError` and `project()` reaches into private pchandler API. Deferred to Phase 4 (soundness) and Phase 5 (tests) per D-03.
- Remote refs on GitHub for perspective are NOT deleted this phase (D-05 / T-01-02 accepted) — staged for Phase 6.

## Next Phase Readiness
- Success Criterion 2 (perspective folded) and Success Criterion 4 (no divergent `dev/*` unmerged into HEAD) are advanced: `git branch -a --no-merged HEAD` lists no divergent `dev/*` ref.
- Wave 1 (this plan) mutated shared HEAD/index state alone and is complete; subsequent git-mutating plans (01-02 …) can proceed serialized.

## Self-Check: PASSED
- FOUND: src/pc2img/strategies/projection.py (contains PerspectiveProjection on HEAD)
- FOUND: src/pc2img/features/manager.py
- FOUND commit: 3f3de26 (fold merge on HEAD)
- FOUND tag: archive/dev-perspective_projection-pre-fold → 8f0fae9

---
*Phase: 01-branch-untangling-mainline-consolidation*
*Completed: 2026-07-08*
