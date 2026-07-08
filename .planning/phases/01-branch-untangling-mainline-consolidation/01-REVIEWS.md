---
phase: 1
reviewers: [codex]
reviewed_at: 2026-07-08T20:48:05Z
plans_reviewed: [01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md]
---

# Cross-AI Plan Review — Phase 1

## Codex Review

**Summary**

The plans are generally well grounded in the actual repo topology: the key hashes exist, `origin/dev/perspective_projection` is 12 commits over `91b4ab6`, local `dev/perspective_projection` is 16 behind and 0 ahead of the remote, `dev/v2` and `feature/update_to_pchandler-1.0.0` are already ancestors of `develop-gsd`, and the perspective fold touches files disjoint from the phase branch's changes. The main gap is procedural: the phase goal says `develop-gsd` becomes the consolidated mainline, but Plan 01 explicitly folds into the phase branch and none of these plans includes the final merge/update of `develop-gsd`.

**Strengths**

- The core topology checks are accurate. `git merge-base HEAD origin/dev/perspective_projection` and `git merge-base develop-gsd origin/dev/perspective_projection` both returned `91b4ab6f99de…`; `git rev-list --count 91b4ab6..origin/dev/perspective_projection` returned `12`.
- The stale-local-branch risk is correctly handled. `git rev-list --count dev/perspective_projection..origin/dev/perspective_projection` returned `16`, and `origin/dev/perspective_projection..dev/perspective_projection` returned `0`, confirming the local branch is a pure ancestor.
- The dev/v2 and pchandler retirement assumptions are correct. `git merge-base --is-ancestor origin/dev/v2 develop-gsd`, `git merge-base --is-ancestor dev/v2 develop-gsd`, and `git merge-base --is-ancestor 54c7100 develop-gsd` all exited `0`.
- The merge-clean claim is strongly supported by file sets. `git diff --name-only 91b4ab6..HEAD` touches planning/docs/config/LICENSE/pyproject files, while `git diff --name-only 91b4ab6..origin/dev/perspective_projection` touches only `src/pc2img/features/manager.py` and `src/pc2img/strategies/projection.py`.
- The destructive-git ordering is sound: archive before prune, fold before deleting local perspective, and use `git branch -d` rather than `-D`.

**Concerns**

- **HIGH:** The plans do not actually make `develop-gsd` contain the perspective fold. Plan 01 states the fold target is the phase branch, not `develop-gsd` (01-01-PLAN.md:35). But the roadmap success criterion says `develop-gsd` contains the richer architecture. Current evidence: `git rev-list --left-right --count develop-gsd...origin/dev/perspective_projection` returned `8 12`, so `develop-gsd` does not contain it yet. This is fine only if there is an explicit phase-close merge gate outside these three plans.
- **MEDIUM:** Plans 02 and 03 mutate docs/branches but do not reassert `HEAD` is the phase branch. Plan 01 verifies HEAD at 01-01-PLAN.md:95, but Plans 02/03 rely on sequencing rather than checking. If run from `develop-gsd`, their local branch deletions may still succeed while docs are committed to the wrong branch.
- **MEDIUM:** The working tree is not clean. `git status --short --branch` showed only untracked files, but several are broad/noisy (`.codex`, `_tests/`, `tests/`, `src/pc2img/features/rrim.py`). The plans say scoped edits, but they should explicitly forbid `git add .` and verify staged files before commits.
- **LOW:** Direct merge simulation could not be run in this read-only review environment. `git merge-tree --write-tree HEAD origin/dev/perspective_projection` failed with `unable to create temporary file: Read-only file system`. The disjoint diff evidence is enough to support a clean merge expectation, but this remains an environment-limited check.
- **LOW:** The perspective branch introduces a whitespace issue. `git diff --check 91b4ab6..origin/dev/perspective_projection -- ...` reports `src/pc2img/strategies/projection.py:212: new blank line at EOF.` The plan intentionally preserves WIP code, but the verify block will not catch this.
- **LOW:** Plan 03 says no `origin/feature/update_to_pchandler-1.0.0` currently exists, which is true in `git show-ref`, but local branch config still has that upstream configured. `git config --get-regexp '^branch\.feature/update_to_pchandler-1\.0\.0\.'` shows `remote origin` and `merge refs/heads/feature/update_to_pchandler-1.0.0`. The inventory should mention this as stale upstream config only if relevant.

**Suggestions**

- Add an explicit fourth phase-close step or gate: merge the completed phase branch into `develop-gsd`, then verify `git rev-list --count develop-gsd..origin/dev/perspective_projection` is `0` or equivalent after updating `develop-gsd`.
- Add `test "$(git rev-parse --abbrev-ref HEAD)" = gsd/phase-01-branch-untangling-mainline-consolidation` to Plans 02 and 03 before any branch deletion or doc edit.
- Add commit hygiene checks before each commit: `git status --short`, `git diff --name-only --cached`, and require staging only the declared `files_modified`.
- Strengthen Plan 01 preflight with `git diff --name-only 91b4ab6..HEAD` and `git diff --name-only 91b4ab6..origin/dev/perspective_projection` checks, since those are the actual mechanism behind the clean-merge claim.
- Decide whether the EOF whitespace issue should be preserved as "arrived from folded branch" or fixed immediately after merge. If preserved, record it as deferred technical debt so it does not surprise later formatting checks.

**Risk Assessment**

Overall risk: **MEDIUM**. The git facts behind the branch fold and local pruning are mostly correct, and the destructive operations are conservatively ordered. The material risk is not the merge itself; it is that the plans can finish successfully while `develop-gsd` still lacks the folded perspective work, leaving the phase success criterion only conditionally satisfied. Add the explicit `develop-gsd` phase-close verification and HEAD checks, and this drops to low.

---

## Consensus Summary

Only one external reviewer (Codex) was invoked, so there is no cross-reviewer consensus to synthesize. Codex ran the read-only git commands the plans depend on and confirmed the topology facts hold on the live DAG (hashes valid, ancestry as claimed, disjoint changed-file sets → clean fold). Its findings are recorded verbatim above.

### Highest-Priority Concern (HIGH)

- **`develop-gsd` never receives the fold within these 3 plans.** Plan 01 folds `origin/dev/perspective_projection` onto the phase branch (HEAD), not `develop-gsd`. Codex verified `develop-gsd` still lacks the perspective work (`develop-gsd...origin/dev/perspective_projection` → `8 12`). The Phase 1 goal and SC2 require `develop-gsd` to be the consolidated mainline. This is only satisfied if a phase-close merge of the phase branch into `develop-gsd` happens — which is the GSD branching model (phase branches merge forward at phase close), but it is **not captured as a verified step in any of the three plans**. Worth an explicit phase-close gate.

### Notable Secondary Concerns (MEDIUM)

- Plans 02/03 don't re-assert `HEAD` is the phase branch before mutating refs/docs — they lean on wave sequencing. A stray checkout of `develop-gsd` would let doc commits and branch deletes land in the wrong place.
- Working tree has broad untracked paths (`.codex`, `_tests/`, `tests/`, `src/pc2img/features/rrim.py`); plans should explicitly forbid `git add .` and verify staged files against `files_modified` before each commit.

### Divergent Views

N/A — single reviewer.
