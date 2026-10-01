# Phase 7: GSEGUtils 0.6 Adoption & 0.11.0 Release - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-01
**Phase:** 07-gsegutils-0-6-adoption-0-11-0-release
**Areas discussed:** Dependency pins, Spikes 001/004, Backlog scope, Deletion residuals & tests, Record timing, iof3D check, Invalid keys

Pre-discussion finding (measured): a fresh unlocked resolve (pchandler 2.1.1 + GSEGUtils 0.6.0) fails 30/286 tests with `AttributeError: 'super' object has no attribute '_get_npy_path'`; the locked env hides it.

---

## Dependency pins

| Option | Description | Selected |
|--------|-------------|----------|
| ~= 0.6.0 | Caps <0.7, matches PCHandler 2.1.1 | ✓ |
| >= 0.6, < 1.0 | Todo default, widest | |
| >= 0.6.0, < 0.7 | Same range, explicit | |

| Option | Description | Selected |
|--------|-------------|----------|
| pchandler >= 2.1.1, ~= 2.1 | Guarantee agreement on GSEGUtils 0.6 | ✓ |
| Keep ~= 2.1 | Allows untested 2.1.0 + 0.6 pairing | |

| Option | Description | Selected |
|--------|-------------|----------|
| One-shot release check | Fresh unlocked install + suite before release PR merges | ✓ |
| Permanent CI job now | Extends CI scope | |
| Neither | Pins enough | |

## Spikes 001/004

| Option | Description | Selected |
|--------|-------------|----------|
| Inside research | Researcher runs under spike rules | ✓ |
| Formal /gsd-spike first | Separate runs | |
| Plan 1 tasks | Fold into execution | |

Target: PyPI 0.6.0 wheel ✓ (vs both 0.6.0 + phase-14). Spike 001 scope: every GSEGUtils subclass ✓ (vs store only).

## Backlog scope

| Item | Choice |
|------|--------|
| AR-07/AR-08 (WR-06/07 r1) | Fix in Phase 7 ✓ (vs re-defer) |
| Ruleset polish WR-01, IN-01..04 | Fold in ✓ (vs defer) |
| RRIM float32 guard | Defer past 0.11.0 ✓ (vs fold in) |
| cuda11/12 docs | Defer ✓ (vs fold in) |
| Promotion shape | One promotion ✓ (vs CI fixes first, code second) |

## Deletion residuals & tests

First question set (r4 items, escape-test style, exception assertions, upstream hazards) was rejected for clarification. Owner: too little information; guideline — don't fix in pc2img what belongs in GSEGUtils; asked whether the GSEGUtils 0.6 migration guide in `~/gsd-workspaces/pchandler` had been taken into account; asked whether fix decisions could be deferred to the plan; wants to avoid chasing unnecessary hardenings after past iterative fix loops.

Finding: the pc2img-specific handoff `~/gsd-workspaces/pchandler/.planning/handoffs/pc2img-migration-BC-GSEG-006.md` was not referenced anywhere in pc2img planning (Phase 6 used the workspace MIGRATION-v1.2.md only for BC IDs). It introduces `purge(key)`, `.dat` containment, `clear()` semantics, key validation, and contradicts the todo's "keep `__delitem__`".

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, rule + plan table | 4-step triage rule; planner applies; owner approves table | ✓ |
| Yes, but stricter | Defer all non-migration items, even one-liners | |
| No, walk items now | Full per-item background first | |

| Option | Description | Selected |
|--------|-------------|----------|
| Delete `__delitem__`, use purge() | Handoff advice; `del` drops tracking only → BC | ✓ |
| Keep, repoint to free functions | `del` unchanged; .dat leaks | |
| Decide in research | Measure callers first | |

## Record timing / iof3D / invalid keys

| Question | Choice |
|----------|--------|
| MIGRATION-v0.11.md finalise | Before release, target `v0.11.0` ✓ (vs post-release commit) |
| iof3D usage check | Yes, read-only grep in research ✓ (vs no) |
| Invalid tile ids / names | Let upstream `StoreKeyError` propagate ✓ (vs pre-validate) |

## Claude's Discretion

- Escape-test assertion style (within triage rule step 3).
- Whether a test pins the GSEGUtils exception subtype beyond `ValueError`.
- Plan/wave decomposition within the ordering constraints.

## Deferred Ideas

- Permanent unlocked-resolve CI job.
- RRIM float32 guard (past 0.11.0).
- cuda11/12 selection docs.
