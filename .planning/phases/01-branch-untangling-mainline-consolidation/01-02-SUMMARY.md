---
phase: 01-branch-untangling-mainline-consolidation
plan: 02
subsystem: infra
tags: [git, branch-consolidation, planning-docs, scope]

# Dependency graph
requires:
  - phase: 01-branch-untangling-mainline-consolidation (Plan 01)
    provides: PerspectiveProjection folded onto develop-gsd/phase branch; dev/perspective_projection pruned
provides:
  - "Asserted (no merge) that origin/dev/v2 is fully contained in develop-gsd (SC2 dev/v2 half)"
  - "Fully-merged local convenience branches dev/v2 and feature/release-please pruned"
  - "PROJECT.md + REQUIREMENTS.md Out-of-Scope reconciled with the folded PerspectiveProjection (D-02)"
affects: [Phase 4 (algorithmic-soundness owns PerspectiveProjection math), Phase 5 (test coverage owns it), Phase 6 (remote branch deletions staged per D-05)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Assert-don't-merge: confirm containment with git merge-base --is-ancestor + rev-list count, never a merge, when the ref is already an ancestor"
    - "Self-guarding prune: git branch -d (never -D); when -d refuses due to a divergent-from-upstream local branch that IS contained in the mainline, --unset-upstream to re-point the -d guard at HEAD"

key-files:
  created:
    - .planning/phases/01-branch-untangling-mainline-consolidation/01-02-SUMMARY.md
  modified:
    - .planning/PROJECT.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "dev/v2 consolidation was verified-and-recorded, not merged: origin/dev/v2 is already an ancestor of develop-gsd (8 commits ahead)"
  - "Local dev/v2 deleted via --unset-upstream then self-guarding -d (never -D) after proving 0 commits ahead of develop-gsd"
  - "PerspectiveProjection carved out as an owner-approved in-scope exception in both milestone docs (D-02); no other new algorithms in scope"

patterns-established:
  - "Assert-don't-merge for already-consolidated refs"
  - "Explicit-path staging only (git add <path>), staged-set verified against an exact expected list before commit"

requirements-completed: [BRANCH-02]

coverage:
  - id: D1
    description: "origin/dev/v2 is confirmed fully contained in develop-gsd (SC2 dev/v2 half), asserted not merged"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "git merge-base --is-ancestor origin/dev/v2 develop-gsd && test $(git rev-list --count origin/dev/v2..develop-gsd) -ge 8"
        status: pass
    human_judgment: false
  - id: D2
    description: "Local branches dev/v2 and feature/release-please pruned; no remote ref deleted"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "test -z \"$(git branch --list dev/v2)\" && test -z \"$(git branch --list feature/release-please)\" && git rev-parse origin/dev/v2"
        status: pass
    human_judgment: false
  - id: D3
    description: "PROJECT.md + REQUIREMENTS.md Out-of-Scope reconciled with the folded PerspectiveProjection (D-02), tomislav exclusion untouched"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "grep -qi perspective .planning/PROJECT.md && grep -qi perspective .planning/REQUIREMENTS.md && grep -q tomislav .planning/PROJECT.md"
        status: pass
    human_judgment: true
    rationale: "The D-02 wording is an owner-approved scope-boundary change; a reviewer should confirm the reconciliation reads as intended (VALIDATION manual-review row)."

# Metrics
duration: 12min
completed: 2026-07-09
status: complete
---

# Phase 01 Plan 02: dev/v2 consolidation confirmed + PerspectiveProjection scope reconciliation Summary

**Confirmed (by assertion, not merge) that origin/dev/v2 is fully folded into develop-gsd, pruned the two fully-merged local convenience branches, and amended both milestone docs so the Out-of-Scope "new algorithms" boundary carves out the now-in-scope PerspectiveProjection (D-02).**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-09
- **Tasks:** 2
- **Files modified:** 2 (PROJECT.md, REQUIREMENTS.md) + STATE/ROADMAP metadata

## Accomplishments
- Re-asserted HEAD is the phase branch BEFORE any ref mutation, then proved `origin/dev/v2` is an ancestor of `develop-gsd` with `develop-gsd` 8 commits ahead (SC2 dev/v2 half met on disk — nothing to merge).
- Pruned the fully-merged local convenience branches `dev/v2` and `feature/release-please` with the self-guarding `-d` (never `-D`); no remote ref touched (`origin/dev/v2` still at `91b4ab6`).
- Reconciled `PROJECT.md` and `REQUIREMENTS.md` Out-of-Scope entries with the folded `PerspectiveProjection` via scoped `Edit` replacements — carved it out as an owner-approved in-scope exception (WIP; math owned by Phase 4, coverage by Phase 5 per D-03), leaving the `develop/tomislav` exclusion untouched.

## Task Commits

1. **Task 1: Verify dev/v2 consolidation and prune fully-merged local branches** — no commit (read-only assertions + local ref deletions; branch deletes are not committable working-tree changes). Verification: `CONSOLIDATION_OK`.
2. **Task 2: Amend Out-of-Scope "new algorithms" entry (D-02)** — `ac51432` (docs). Verification: `AMEND_OK`.

**Plan metadata:** committed with SUMMARY/STATE/ROADMAP (docs: complete plan).

## Files Created/Modified
- `.planning/PROJECT.md` — §Out of Scope "new algorithms" bullet reworded to carve out PerspectiveProjection as an owner-approved in-scope exception (D-02).
- `.planning/REQUIREMENTS.md` — §Out of Scope "new algorithms" table row reconciled the same way.
- `.planning/phases/.../01-02-SUMMARY.md` — this file.

## Decisions Made
- Treated dev/v2 consolidation as verify-and-document, not a merge, per RESEARCH (both refs already ancestors of develop-gsd).
- Left `origin/dev/v2` and all remote refs untouched (remote deletions staged for Phase 6 per D-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Local `dev/v2` could not be pruned by the plan's exact `git branch -d dev/v2`**
- **Found during:** Task 1 (prune step)
- **Issue:** The plan assumed `git branch -d dev/v2` would succeed because dev/v2 is an ancestor of `develop-gsd`. But `-d` compares against the branch's *configured upstream* (`origin/dev/v2`), not `develop-gsd`. The local `dev/v2` tip (`e795ec0 chore(license): switch from MIT to BSD-3-Clause`) is 1 commit ahead of `origin/dev/v2`, so `-d` refused — even though git itself reported the branch "is merged to HEAD". Investigation confirmed the branch is 0 commits ahead of `develop-gsd` and is an ancestor of both `develop-gsd` and HEAD, so deletion is genuinely lossless (the license commit is preserved in develop-gsd/HEAD).
- **Fix:** Ran `git branch --unset-upstream dev/v2` (a local `.git/config`-only operation that does NOT touch `origin/dev/v2`), which re-points the `-d` guard at HEAD; `git branch -d dev/v2` then succeeded via the HEAD-containment check. Honored the "never `-D`" safety rule — the self-guarding `-d` would still have refused had the branch not been merged to HEAD.
- **Files modified:** none (local ref/config only)
- **Verification:** `test -z "$(git branch --list dev/v2)"` (deleted); `git rev-parse origin/dev/v2` → `91b4ab6…` (remote untouched); `CONSOLIDATION_OK`.
- **Committed in:** n/a (ref deletion, not a working-tree commit)

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** Fix stayed within the plan's safety envelope — no `-D`, no remote deletion, no history loss. No scope creep.

## Issues Encountered
- Two `gsd-tools` state handlers (`state.record-metric`, `state.add-decision`) rejected positional args and required flag-style args (`--phase/--plan/--duration/--tasks/--files`, `--summary`); re-invoked with flags. A stray "test" decision added while probing the signature was removed from STATE.md.
- The working tree carried a pre-existing unrelated `.planning/config.json` change (`_auto_chain_active: false`) plus broad untracked paths (`.codex`, `_tests/`, `tests/`, `src/pc2img/features/rrim.py`); none were staged — explicit-path staging + staged-set verification (`git diff --name-only --cached` == exactly the two declared files) kept the commit clean.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SC2 (dev/v2 consolidated) satisfied; milestone docs no longer contradict the mainline's PerspectiveProjection.
- Remote branch deletions (`origin/dev/v2` and others) remain staged for Phase 6 (D-05).
- `feature/update_to_pchandler-1.0.0` remains for BRANCH-03 disposition (D-04, diff-review then retire).

## Self-Check: PASSED

- FOUND: `.planning/phases/01-branch-untangling-mainline-consolidation/01-02-SUMMARY.md`
- FOUND: commit `ac51432` (docs(scope) Out-of-Scope amendment)
- CONFIRMED: local `dev/v2` and `feature/release-please` no longer exist; `origin/dev/v2` untouched (`91b4ab6`)

---
*Phase: 01-branch-untangling-mainline-consolidation*
*Completed: 2026-07-09*
