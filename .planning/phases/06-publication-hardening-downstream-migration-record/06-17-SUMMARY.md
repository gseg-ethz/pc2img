---
phase: 06-publication-hardening-downstream-migration-record
plan: 17
subsystem: quality
tags: [gate-rerun, fix-diff-review, consolidate-findings, waiver]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "06-14/06-15/06-16 review-round fixes on the phase branch"
provides:
  - ".planning/CICD-ADOPTION-RECORD.md: '### 2026-09-29 — after the review-round fixes' gate block with real output and the recorded round-2 review scope"
  - "CONTRIBUTING.md: coverage baseline refreshed to 286 passed / 62.27%, dated 2026-09-29 (IN-10 CONTRIBUTING half)"
  - "06-REVIEW.md round 2 (deep, 21 files, 0 blocker / 5 warning / 6 info) and its consolidation into 06-UAT.md / 06-VERIFICATION.md as review-r2 entries"
affects: ["06-19 (new round-2 doc-only gap plan, to be created)", "06-18 (re-waved behind 06-19; also resolves the round-2 fix-now entries)"]

actuals:
  tasks: 2
  commits: 3
plan_head_before: cf2fe47
plan_head_after: 28faffb

key-files:
  created: []
  modified:
    - .planning/CICD-ADOPTION-RECORD.md
    - CONTRIBUTING.md

key-decisions:
  - "Task 2 step 2 (the additional /code-review origin/develop-gsd high run) WAIVED by owner 2026-09-29: the deep gsd-code-reviewer pass covered exactly the recorded scope and confirmed its claims by running code (the archive round trip, the rename API shape); the last round under the cap is kept for reviewing the round-2 fix."
  - "Round-2 dispositions (owner, 2026-09-29): 7 fix now in one doc-only pass (WR-01 via doc narrowing only — environment deployment rules and sdist content check declined; WR-02, WR-03, WR-05, IN-04, IN-05, IN-06); 4 deferred to Phase 7 (WR-04, IN-01, IN-02, IN-03). No blocker."
  - "The four round-1 gaps whose fixes round 2 found incomplete (WR-05, IN-04, WR-03, IN-05) are to be resolved in 06-18 with evidence lines naming their round-2 follow-up entries, not held open."
---

# Phase 06 Plan 17: Gate re-run and fix-diff review — Summary

## Task 1 — gate re-run (commit `5eae12c`)

The complete local gate set ran in one pass against HEAD `cf2fe47` (every review-round fix
applied); every command exited zero. Real output is in `.planning/CICD-ADOPTION-RECORD.md`
under `### 2026-09-29 — after the review-round fixes`:

| Gate | Result |
|---|---|
| Full suite + coverage floor | 286 passed, total coverage 62.27% |
| Whole-tree pre-commit | all hooks Passed |
| sphinx -W doc build | build succeeded |
| Placeholder grep | no output |
| Planning-vocabulary gate | 82 passed, 6 deselected |
| Kit script tests | 92 passed |
| Publish containment gate | green |
| Migration record verifier | `[ok] verified 25 entries` |
| `uv lock --check` | Resolved 193 packages |
| `uv build` + `twine check` | both artifacts PASSED |

CONTRIBUTING.md's baseline sentence now states `**286 passed / 0 xfailed**`, 62.27%, dated
2026-09-29. The review scope (`git diff --name-only 6c10ee0..HEAD -- . ':!.planning'`, 22 paths)
is recorded in the same block.

## Task 2 — fix-diff review checkpoint (resumed 2026-09-29)

1. `/gsd-code-review 06 --files <recorded list>` ran at deep depth (diff base `2ec34fc`) over 21
   files — the recorded scope minus `MIGRATION-v0.11.md`, which the fixes moved out of the shipped
   tree. Report: `06-REVIEW.md`, committed `29039d5`. Result: 0 blocker, 5 warning, 6 info.
   The orchestrator spot-checked WR-02 (0 "declined" mentions in RULESETS.md against 7 pointers)
   and WR-03 (`# WR-03:` present at `tests/test_projection.py:309`).
2. `/code-review origin/develop-gsd high` — **waived by owner** (reason under key-decisions).
3. Findings landed with `/gsd-consolidate-findings` as round 2 (commit `28faffb`); parser
   post-condition OK (`audit-uat` sees all 11; `verification.status = gaps_found`).
4. Dispositions: 7 fix-now (`status: failed`: 1 major, 3 minor, 3 cosmetic), 4 deferred to
   Phase 7. No round-2 entry is `status: failed` with `severity: blocker`, so the checkpoint's
   resume condition holds.

**Resume signal:** reviewed — 11 round-2 findings; 7 to be fixed in a new doc-only gap plan
before 06-18, 4 deferred; `/code-review high` waived.

## Deviations from Plan

- **Step 2 waived** (owner decision, recorded above) instead of run.
- **Sequencing change:** round-2 fix-now findings exist, so a new gap plan (06-19) is inserted
  before 06-18; 06-18 is re-waved to depend on it and to resolve the round-2 fix-now entries
  too. The doc-pass diff gets its own review (round 3 of 3) before 06-18 merges anything.

## Next

`/gsd-plan-phase 06 --gaps` → execute 06-19 → `/gsd-code-review 06 --files <06-19 files>` →
consolidate → 06-18.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-29*
