---
phase: 1
slug: branch-untangling-mainline-consolidation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **This is a git-topology phase.** There is no runtime code path to unit-test — the
> only source change (`PerspectiveProjection`) arrives via a clean merge of an existing
> branch and is intentionally WIP (its math is Phase 4/5's concern, per D-03). Validation
> is therefore **assertion-by-git-command**: deterministic, read-only checks that prove the
> four Success Criteria. Lifted from RESEARCH.md §"Validation Architecture".

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none — git plumbing assertions (no pytest run is meaningful here) |
| **Config file** | none |
| **Quick run command** | the single git assertion for the task being advanced (see map below) |
| **Full suite command** | run the full Success-Criteria → Proof Map below |
| **Estimated runtime** | < 2 seconds (all git commands, sub-second each) |

---

## Sampling Rate

- **After every task commit:** Run the specific SC git check the task advances.
- **After every plan wave:** Run the full proof map.
- **Before `/gsd-verify-work`:** All proof-map checks must return their expected result.
- **Max feedback latency:** ~2 seconds.

---

## Success-Criteria → Proof Map (per-task verification)

`<fold-target>` = whichever ref the planner chooses to land the fold on (phase branch or
`develop-gsd`; see Open Question 1). All checks are read-only.

| SC | Requirement | Behavior to prove | Automated check (expected result) |
|----|-------------|-------------------|-----------------------------------|
| SC2 | BRANCH-02 | develop-gsd contains all dev/v2 | `git merge-base --is-ancestor origin/dev/v2 develop-gsd` → exit 0; `git rev-list --count origin/dev/v2..develop-gsd` ≥ 8 |
| SC2 | BRANCH-02 | `PerspectiveProjection` present on mainline after fold | `git grep -l PerspectiveProjection <fold-target> -- 'src/*'` matches `strategies/projection.py`; `"perspective"` present in the `PROJECTIONS` registry `Literal` |
| SC2 | BRANCH-02 | no perspective commit left behind | `git rev-list --count <fold-target>..origin/dev/perspective_projection` → 0 |
| SC4 | BRANCH-02 | every `dev/*` is an ancestor of the fold target | `git branch -a --no-merged <fold-target>` lists no `dev/*` ref (excluding tomislav/ship/bot refs) |
| SC1 | BRANCH-01 | inventory doc exists and classifies every ref | file present under `.planning/phases/01-…/`; one row per non-symbolic branch/remote ref (13) — matching 01-03 Task 2's 13-name grep loop (excludes tags `v0*`/`v2.0.0a5`/`archive/*`, `stash`, and the symbolic `origin/HEAD`) |
| SC3 | BRANCH-03 | branch dispositioned + acted on | `git merge-base --is-ancestor 54c7100 develop-gsd` → exit 0 (recorded); `git branch --list feature/update_to_pchandler-1.0.0` → empty (local label deleted) |
| D-06 | (safety) | nothing lost on prune | `git tag --list 'archive/*'` shows the persp archive tag pointing at `8f0fae9` **before** any persp prune |

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.* No test framework, fixtures, or
stubs are needed — git 2.53.0 (verified available) provides all assertion primitives.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Inventory doc classifies **every** ref correctly (live/dead + disposition rationale) | BRANCH-01 | Classification correctness (esp. bot-branch labeling, A2) is a judgement call git cannot assert | Reviewer compares the doc's rows against `git for-each-ref` output; confirms `develop/tomislav` marked EXCLUDED and every remote deletion marked "staged for Phase 6" |
| PROJECT.md / REQUIREMENTS.md Out-of-Scope amendment (D-02) | BRANCH-02 | Prose edit; correctness is editorial, not mechanical | Reviewer confirms the "new algorithms" Out-of-Scope entry is reworded/removed and no longer contradicts the folded `PerspectiveProjection` |

---

## Validation Sign-Off

- [x] All tasks have an automated git-assertion verify or are covered by a manual review row
- [x] Sampling continuity: every SC has at least one deterministic check
- [x] Wave 0 covers all MISSING references (none required)
- [x] No watch-mode flags
- [x] Feedback latency < 2s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
