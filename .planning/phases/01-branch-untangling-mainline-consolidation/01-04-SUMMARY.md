---
phase: 01-branch-untangling-mainline-consolidation
plan: 04
subsystem: infra
tags: [git, branch-consolidation, forward-merge, mainline, phase-close]

# Dependency graph
requires:
  - phase: 01-branch-untangling-mainline-consolidation (Plan 01)
    provides: PerspectiveProjection folded onto phase branch; archive tag; local dev/perspective_projection pruned
  - phase: 01-branch-untangling-mainline-consolidation (Plan 02)
    provides: dev/v2 consolidation confirmed; PROJECT/REQUIREMENTS Out-of-Scope amended
  - phase: 01-branch-untangling-mainline-consolidation (Plan 03)
    provides: 01-BRANCH-INVENTORY.md; pchandler-1.0 label retired
provides:
  - "develop-gsd carries the phase-01 consolidation work via a --no-ff forward-merge commit (9b42cfb) — BRANCH-02 satisfied on the named mainline"
  - "SC2 (perspective folded + fold-complete + dev/v2 ancestry) and SC4 (no divergent dev/*) proven on develop-gsd, not merely the phase branch — closes the review HIGH concern"
affects: [Phase 4 (owns PerspectiveProjection math, arriving as-is on develop-gsd), Phase 5 (owns PerspectiveProjection coverage), Phase 6 (all remote branch deletions + remote push staged per D-05)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Clean-by-construction forward-merge: preflight-assert develop-gsd is a STRICT ANCESTOR of the phase branch (merge is purely additive — no divergent commits, no conflict resolution, no history rewrite) before merging"
    - "--no-ff for an auditable two-parent merge commit; STOP on any conflict rather than hand-resolving (T-01-07 mitigation)"
    - "No git add ./-A across the merge: known untracked working-tree paths (.codex, _tests/, tests/, src/pc2img/features/rrim.py) verified STILL untracked after the merge"
    - "Restore HEAD to the phase branch after the merge so metadata/tracking commits land on the phase branch, not the mainline"

key-files:
  created:
    - .planning/phases/01-branch-untangling-mainline-consolidation/01-04-SUMMARY.md
  modified:
    - src/pc2img/strategies/projection.py (arrived on develop-gsd via merge — WIP math untouched per D-03)
    - src/pc2img/features/manager.py (arrived on develop-gsd via merge)
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The forward-merge is the phase-close step the GSD branching model requires (per-phase branches merge forward into the mainline at phase close); Plans 01-03 landed work on the phase branch only, so this plan transfers it onto develop-gsd in one auditable merge commit"
  - "SC2/SC4 re-proven against develop-gsd (the <fold-target> the phase goal names), not the phase branch — the exact gap Codex flagged (develop-gsd..origin/dev/perspective_projection was 8 12, now 0)"
  - "No remote push and no remote/branch deletions this phase (D-05); WIP PerspectiveProjection math left untouched (D-03) — it simply arrives on develop-gsd as-is"

patterns-established:
  - "Preflight ancestry guard (strict-ancestor + ahead-count > 0) before any forward-merge to guarantee purely-additive, conflict-free merges"
  - "Post-merge untracked-path audit + HEAD restoration to keep the working tree and subsequent workflow state unsurprising"

requirements-completed: [BRANCH-02]

coverage:
  - id: D1
    description: "Phase branch merged forward into develop-gsd via a real two-parent --no-ff merge commit; phase-branch tip is now an ancestor of develop-gsd"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "git merge-base --is-ancestor gsd/phase-01-... develop-gsd && git rev-parse develop-gsd^2 (=3faa8e5, phase tip) — MERGE_OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "SC2 — PerspectiveProjection + 'perspective' registry key present on develop-gsd:src/pc2img/strategies/projection.py"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "git grep -l PerspectiveProjection develop-gsd -- 'src/*' matches strategies/projection.py; Literal[... 'perspective'] + @PROJECTIONS.register('perspective') present"
        status: pass
    human_judgment: false
  - id: D3
    description: "SC2 — fold completeness on the mainline: develop-gsd..origin/dev/perspective_projection is 0 (was 8 12 per Codex before this plan)"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "git rev-list --count develop-gsd..origin/dev/perspective_projection = 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "SC2 — origin/dev/v2 remains a full ancestor of develop-gsd (dev/v2 half preserved by the merge)"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "git merge-base --is-ancestor origin/dev/v2 develop-gsd exit 0; develop-gsd..origin/dev/v2 = 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "SC4 — no divergent dev/* ref remains unmerged relative to develop-gsd (tomislav/bot/ship excluded)"
    requirement: "BRANCH-02"
    verification:
      - kind: automated
        ref: "git branch -a --no-merged develop-gsd | grep dev/ (excl tomislav/ship) is empty — remaining --no-merged refs are only main/tomislav/release-please"
        status: pass
    human_judgment: false

# Metrics
duration: 2min
completed: 2026-07-09
status: complete
---

# Phase 01 Plan 04: Phase-close forward-merge into develop-gsd Summary

**Merged the completed phase branch `gsd/phase-01-branch-untangling-mainline-consolidation` forward into `develop-gsd` via a clean, auditable `--no-ff` two-parent merge commit (9b42cfb), transferring the whole phase-01 consolidation (perspective fold + dev/v2 consolidation + branch inventory + pchandler-1.0 retire) onto the named consolidated mainline, then re-proved SC2 and SC4 against `develop-gsd` itself — closing the review HIGH concern that the prior plans proved them only on the phase branch.**

## Performance

- **Duration:** ~2 min
- **Completed:** 2026-07-09
- **Tasks:** 2 (1 git-mutating merge, 1 read-only assertion set)

## Accomplishments

- **Task 1 (BRANCH-02, the merge):** Ran the clean-by-construction PREFLIGHT — `develop-gsd` is a STRICT ANCESTOR of the phase branch (`git merge-base --is-ancestor develop-gsd <phase>` → exit 0) and the phase branch is ahead by **28** commits (`develop-gsd..<phase>` = 28, reverse = 0; left-right `0 28`), guaranteeing a purely-additive merge. Checked out `develop-gsd` (was 9832d90), ran `git merge --no-ff <phase>` with a **functional** commit scope (`chore(branch): merge phase-01 consolidation into develop-gsd`, never a planning-ID scope per CLAUDE.md). Merge completed by the `ort` strategy with **zero conflicts** and produced a real two-parent commit **9b42cfb** (parents: 9832d90 old develop-gsd + 3faa8e5 phase tip). Confirmed the four known untracked paths (`.codex`, `_tests/`, `tests/`, `src/pc2img/features/rrim.py`) are **STILL untracked** after the merge (no `git add .`/`-A` used). Restored HEAD to the phase branch. WIP PerspectiveProjection math untouched (D-03); no remote pushed or deleted (D-05).
- **Task 2 (SC2/SC4 on develop-gsd, read-only):** Re-ran the VALIDATION proof-map with `develop-gsd` as the `<fold-target>`:
  - **SC2 perspective present:** `develop-gsd:src/pc2img/strategies/projection.py` contains `PerspectiveProjection`, `ProjectionName = Literal["spherical", "orthographic", "perspective"]` (line 18), and `@PROJECTIONS.register("perspective")` (line 184).
  - **SC2 fold completeness:** `git rev-list --count develop-gsd..origin/dev/perspective_projection` → **0** — the exact check Codex reported as `8 12` before this plan is now resolved on the mainline.
  - **SC2 dev/v2 half:** `git merge-base --is-ancestor origin/dev/v2 develop-gsd` → exit 0 (0 commits ahead) — dev/v2 ancestry preserved.
  - **SC4 no divergent dev/*:** `git branch -a --no-merged develop-gsd` filtered for `dev/*` (excl tomislav/ship) is **empty** — remaining unmerged refs are only `main`, `origin/develop/tomislav` (owner-excluded), and `release-please--branches--main`.

## Task Commits

1. **Task 1: Merge the completed phase branch forward into develop-gsd** — merge commit **9b42cfb** on `develop-gsd` (`chore(branch): merge phase-01 consolidation into develop-gsd`), two parents 9832d90 + 3faa8e5. Verification: `MERGE_OK`.
2. **Task 2: Prove SC2 and SC4 on develop-gsd** — no commit (read-only git assertions). Verification: `SC24_ON_DEVELOP_OK`.

**Plan metadata:** committed on the phase branch with SUMMARY/STATE/ROADMAP/REQUIREMENTS (docs: complete plan) — landed on the phase branch because HEAD was restored there before this commit (the merge commit itself remains on `develop-gsd`).

## Files Created/Modified

- `.planning/phases/.../01-04-SUMMARY.md` — this file (on the phase branch).
- On `develop-gsd` via the merge: `src/pc2img/strategies/projection.py` (perspective fold, +40/-… ; WIP math untouched), `src/pc2img/features/manager.py`, and the full `.planning/` phase-01 doc set.
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` — position/decisions/progress + BRANCH-02 marked complete (on the phase branch).

## Decisions Made

- The forward-merge is the phase-close step the GSD branching model mandates; the prior three plans deliberately landed work on the phase branch, so this plan folds it onto `develop-gsd` in one auditable merge.
- SC2/SC4 are asserted against `develop-gsd` — the mainline the phase goal names — resolving the review HIGH concern (Codex measured `develop-gsd..origin/dev/perspective_projection` = `8 12`; now 0).
- No remote push, no remote/branch deletions (D-05, staged for Phase 6); WIP perspective math left as-is (D-03, owned by Phase 4/5).

## Deviations from Plan

None — the plan executed exactly as written. Preflight confirmed the strict-ancestor invariant, the merge was conflict-free and purely additive, no `git add .`/`-A` was used, the four untracked paths stayed untracked, HEAD was restored to the phase branch, and all SC2/SC4 checks passed on the first run.

## Issues Encountered

- The working tree carries a pre-existing ephemeral `.planning/config.json` edit (only the `_auto_chain_active: false` state key, identical committed blob on both branches) — it carried across the checkout cleanly and was not staged into either the merge or the metadata commit.

## Known Deferred Items

- **WIP PerspectiveProjection math** now present on `develop-gsd` as-is (D-03) — completion/validation owned by Phase 4/5.
- **All remote branch deletions and the remote push of `develop-gsd`** staged for Phase 6 ship (D-05). The perspective work is additionally preserved by the `archive/dev-perspective_projection-pre-fold` tag (D-06).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- BRANCH-01/02/03 all complete; SC1-SC4 satisfied on `develop-gsd`. Phase 01 is functionally closed on the mainline.
- `develop-gsd` now carries the consolidated architecture; subsequent phases branch from it.
- Phase 6 owns the remaining outward-facing actions: remote branch deletions and pushing `develop-gsd`/mainline updates.

## Self-Check: PASSED

- FOUND: `.planning/phases/01-branch-untangling-mainline-consolidation/01-04-SUMMARY.md`
- FOUND: merge commit `9b42cfb` on `develop-gsd` (two parents 9832d90 + 3faa8e5)
- CONFIRMED: `MERGE_OK` and `SC24_ON_DEVELOP_OK` both returned; HEAD restored to the phase branch
- CONFIRMED: four known untracked paths remain untracked; no remote ref pushed or deleted

---
*Phase: 01-branch-untangling-mainline-consolidation*
*Completed: 2026-07-09*
