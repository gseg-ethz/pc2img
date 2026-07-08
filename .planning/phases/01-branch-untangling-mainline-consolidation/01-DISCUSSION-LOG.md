# Phase 1: Branch Untangling & Mainline Consolidation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-08
**Phase:** 1-Branch Untangling & Mainline Consolidation
**Areas discussed:** perspective_projection fate, pchandler-1.0.0 branch, remote deletion scope, inventory doc home

---

## dev/perspective_projection disposition

| Option | Description | Selected |
|--------|-------------|----------|
| Shelf as tag, audit-flag improvements | Tag + retire; record non-algorithm improvements as Phase 4/5 candidates without folding code | |
| Cherry-pick improvements now | Commit-by-commit audit, fold only non-algorithm improvements now | |
| Retire wholesale, no salvage | Treat entire branch as dead | |
| Fold everything incl. PerspectiveProjection | Merge whole branch into develop-gsd | ✓ |

**User's choice:** Fold everything including PerspectiveProjection.
**Notes:** This overrides the currently-locked "new algorithms" Out-of-Scope
boundary. Surfaced the consequences before confirming; user confirmed
**"Yes, fold + amend scope"** — merge the full branch, update
PROJECT.md/REQUIREMENTS.md to make PerspectiveProjection in-scope, and accept that
Phase 4 (soundness review) and Phase 5 (test coverage) now own it. Recorded as an
intentional, owner-approved scope amendment, not scope creep.

---

## feature/update_to_pchandler-1.0.0 disposition

| Option | Description | Selected |
|--------|-------------|----------|
| Diff-review then retire | Commit-level review to salvage anything relevant, then retire | ✓ |
| Retire outright | Assume nothing salvageable; tag/delete, record superseded | |

**User's choice:** Diff-review then retire.
**Notes:** Cheap guard against losing a stray useful fix (e.g. registry named-args
commit `54c7100`) before retiring the two-majors-stale branch.

---

## Branch deletion scope

| Option | Description | Selected |
|--------|-------------|----------|
| Record now, delete at ship | Inventory + dispositions now, prune safe local branches; remote deletions staged for Phase 6 ship | ✓ |
| Delete remotes this phase | Execute remote deletions now for dead branches | |
| Local prune only, never touch remote | Only clean local; leave all remotes, just document | |

**User's choice:** Record now, delete at ship.
**Notes:** Avoids destructive outward-facing GitHub actions mid-milestone; keeps
history available for later phases. Archive-tag salvage-worthy branches before prune.

---

## Branch-inventory document home

| Option | Description | Selected |
|--------|-------------|----------|
| .planning/ only | Internal planning record, stripped from public main | |
| Repo doc surviving to main | docs/ file shipped to public main permanently | |
| .planning/ now, distill later | Full inventory in .planning/; distill publicly-relevant bits into Phase 6 BC-01 | ✓ |

**User's choice:** .planning/ now, distill later.
**Notes:** Keeps main clean; publicly-relevant consolidation notes fold into the
Phase 6 breaking-change/migration record (BC-01) if warranted.

---

## Claude's Discretion

- Exact inventory doc filename/format within the phase directory.
- Which local branches count as "safe" to prune.
- Classification/handling of housekeeping/automation branches
  (`feature/release-please`, release-please bot branches).
- Whether the perspective_projection fold executes in-phase or as its first plan.

## Deferred Ideas

- Actual GitHub remote-branch deletions → Phase 6 ship.
- Public distillation of the branch inventory → Phase 6 BC-01 record.
- `develop/tomislav` → permanently excluded per owner (untouched, not deferred).
