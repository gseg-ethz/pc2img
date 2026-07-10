---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 04
status: "Phase 04 shipped — PR #11"
stopped_at: Phase 5 context gathered
last_updated: "2026-07-10T20:01:22.759Z"
last_activity: 2026-07-10
progress:
  total_phases: 7
  completed_phases: 5
  total_plans: 20
  completed_plans: 20
  percent: 71
current_phase_name: code-quality-algorithmic-soundness-review
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-08)

**Core value:** Reliably turn 3D point clouds into correct, reproducible 2D feature rasters — sound in code and math, running against current PCHandler 2.x + GSEGUtils releases.
**Current focus:** Phase 04 — code-quality-algorithmic-soundness-review

## Current Position

Phase: 04 — COMPLETE
Plan: 7 of 7
Status: Phase 04 shipped — PR #11
Last activity: 2026-07-10

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 10
- Average duration: - min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |
| 02 | 3 | - | - |
| 03 | 3 | - | - |
| 03.1 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 3 | 3 tasks | 2 files |
| Phase 01 P02 | 12 | 2 tasks | 2 files |
| Phase 01 P03 | 8min | 2 tasks | 1 files |
| Phase 01 P04 | 2 | 2 tasks | 1 files |
| Phase 02 P01 | 1min | 2 tasks | 1 files |
| Phase 02 P02 | 10min | 3 tasks | 3 files |
| Phase 02 P03 | 5min | 2 tasks | 4 files |
| Phase 03 P01 | 2 | 2 tasks | 2 files |
| Phase 03 P02 | 2min | 2 tasks | 4 files |
| Phase 03 P03 | 2min | 2 tasks | 2 files |
| Phase 03.1 P01 | 20min | 2 tasks | 2 files |
| Phase 03.1 P02 | 2min | 2 tasks | 4 files |
| Phase 03.1 P03 | 5min | 2 tasks | 2 files |
| Phase 04 P01 | 3min | 2 tasks | 3 files |
| Phase 04 P03 | 6min | 3 tasks | 4 files |
| Phase 04 P02 | 3min | 4 tasks | 3 files |
| Phase 04 P04 | 24min | 2 tasks | 23 files |
| Phase 04 P05 | 10min | 2 tasks | 2 files |
| Phase 04 P06 | 12min | 2 tasks | 2 files |
| Phase 04 P07 | 9min | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Milestone 1 is a hardening + adaptation pass (deps, branches, quality/math, bugs, tests, CI/CD, downstream BC).
- CI/CD split: lightweight test-CI early (Phase 3), branch-protection/publication hardening pre-ship (Phase 6).
- Known bugs tracked as explicit requirements, each with a proving test (Phase 5).
- Quality pillar deepened to include mathematical/algorithmic soundness (Phase 4); QUAL-03 findings feed BUG-05.
- [Phase 01]: Folded origin/dev/perspective_projection (authoritative remote) onto phase branch via --no-ff merge; archive tag preserves pre-fold tip 8f0fae9; local dev/perspective_projection pruned with self-guarding -d
- [Phase 01 P02]: Asserted (no merge) origin/dev/v2 is fully contained in develop-gsd (8 commits ahead); pruned fully-merged local dev/v2 (via --unset-upstream then self-guarding -d, never -D) and feature/release-please; amended PROJECT.md + REQUIREMENTS.md Out-of-Scope to carve out folded PerspectiveProjection (D-02)
- [Phase 01 P03]: Retired local feature/update_to_pchandler-1.0.0 via self-guarding git branch -d (54c7100 is a full ancestor of develop-gsd; named-args registry intent already in-tree, nothing to salvage); no remote touched
- [Phase 01 P03]: Authored 01-BRANCH-INVENTORY.md classifying all 13 phase-start refs; develop/tomislav EXCLUDED, all remote deletions staged for Phase 6 (D-05), archive tag recorded as D-06 safety net
- [Phase 01 P04]: Merged the completed phase branch forward into develop-gsd via --no-ff (9b42cfb, two parents); SC2/SC4 re-proven on develop-gsd (develop-gsd..origin/dev/perspective_projection now 0, was 8 12); WIP math untouched (D-03), no remote touched (D-05)
- [Phase 02]: Kept numpy ~= 2.0 loose, relying on pchandler transitive <2.4 cap (D-03); routed cuda extras through pchandler[cudaXX] (D-04); dev/doc to PEP 735 groups (D-08); pinned all ten RAPIDS names to explicit nvidia index (D-06)
- [Phase ?]: [Phase 02 P02]: Added [tool.uv] conflicts for cuda11/cuda12 (owner option a) so the universal uv.lock hash-pins both GPU stacks in separate forks; cuXX pick defers to install time. A2 transitive RAPIDS source binding confirmed green.
- [Phase ?]: DEP-01/DEP-02 delivered as audit attestation + runtime smoke, not code fixes: all three named pchandler 2.x breaks (FoVTree, to_py4dgeo, Csv/Las) have zero call sites in src/pc2img/
- [Phase ?]: Smoke passes an explicit LazyDiskCacheConfig; the uncoerced None-default cache-config bug is deferred to Phase 4/5 (pending todo)
- [Phase 03 P01]: Pinned pytest to ~= 9.1 (D-14) alongside pytest-cov ~= 5.0 + coverage ~= 7.0 (D-07); did NOT downgrade to pchandler's stale pytest ~= 8.4
- [Phase 03 P01]: Added branch-coverage [tool.coverage.*] config (D-05) but omitted fail_under from TOML and kept --cov out of addopts so subset runs never trip a floor; coverage gate lives on the CI CLI only (Plan 03)
- [Phase ?]: [Phase 03 P02] Green-by-triage: deleted the two import-broken pre-refactor modules (D-02); parked the 11 live-verified failures as xfail(strict=False) with Phase-5 reasons (D-03); suite now 15 passed / 11 xfailed / 0 failed
- [Phase ?]: [Phase 03 P02] tests/ was entirely untracked (planning git-rm assumption false); committed the 3 surviving test modules + unchanged src/pc2img/features/rrim.py so the green + CI premise holds on a fresh checkout (Rule-3 deviation)
- [Phase ?]: [Phase 03.1 P01] RRIM disposition locked: keep rrim.py on patent-expiry basis; core AAS patent family expired all jurisdictions (US 7,764,282 B2 et al.), no license required; verbatim claim-1 walk of active patents JP 5281518 + US 11,836,856 shows flat-RGB rrim.py reads on neither
- [Phase ?]: [Phase 03.1 P02] Shipped top-level NOTICE as the RRIM distribution-safety artifact (patent-expiry basis + AAS/Chiba/Yokoyama attribution + trademark disclaimer); added opt-in rrim=[] signposting extra (registers nothing — only import pc2img.features.rrim registers) and re-locked uv.lock; docstrings reconciled to opt-in contract; wheel .dist-info legal-file inclusion deferred to Phase 6 (D-09/D-11/D-12)
- [Phase 03.1 P03]: Owner signed off on keep-on-patent-expiry RRIM disposition (D-10); IP gate CLEARED, branch publication-safe (D-07 resolve-then-push); blocking patent-review todo moved pending->completed via git mv (audit trail) only after the human sign-off gate passed
- [Phase 04]: [Phase 04 P01] Swapped black->ruff ~= 0.15 in PEP 735 dev group (D-11 default; ruff format is black-equivalent), relocked uv.lock; authored tests/test_hygiene.py as the Wave 0 QUAL-01 gate (1 LIVE import-smoke pass + 3 xfail: keywords/viz/ruff-clean, split so 04-02/04-04 flip markers independently); no [tool.ruff] block yet (deferred to 04-02)
- [Phase ?]: [Phase 04 P03] Deleted broken make_generator (zero callers) rather than repairing; guarded pchandler private _TransformArray under TYPE_CHECKING + __future__ annotations (resolves Phase-1 IN-03 / T-04-D1); synced features barrel __all__ to registered non-rrim set; deleted dead plt-referencing convert_to_image duplicate (QUAL-01/02)
- [Phase 04]: [Phase 04 P02] Landed 88-col [tool.ruff] config (D-11; families E/F/W/I/B/C90/UP/NPY+ERA001, not sibling 120); barrel per-file-ignores exempt the four __init__.py from F401 so 04-04 ruff --fix keeps registration re-exports; collapsed joblib to one ~=1.5 pin; matplotlib->optional viz extra; de-placeholdered metadata; owner-confirmed BSD license classifier + github docs URL (T-04-M1)
- [Phase ?]: [Phase 04 P04] Owner reversed D-11: ruff line-length 88->120 (dense numerical code; cleared 25 E501 with zero edits, matches sibling template); applied PEP695 (UP040/UP046); Option A - kept [tool.ruff] STRICT and retargeted the hygiene gate test to the fixable subset (--ignore E402,C901,B008) not global-ignore; 18 residual findings (E402x9->BUG-04, C901x5, B008x4->seed E) deferred to Phase 5 as visible breadcrumbs (D-02); CI enforcement still deferred to Phase 6 (D-10)
- [Phase 04]: [Phase 04 P07] Synthesized canonical 04-FINDINGS.md: 24 active findings (M-01..M-13 + DSN-01..DSN-11) merged most-severe-first, per-entry schema-linted (8 D-06 fields + file:line anchor); BUG-01=M-01 recorded once cross-referenced; DSN-02/BUG-02 states TypeError->NotImplementedError; no per-finding BUG-05 ids (D-07)
- [Phase 04]: [Phase 04 P07] Rule-1: plan Task-2 linter regex (mid-pattern (?im)) fails to compile on Python >=3.11 incl project .venv 3.12.13; validated with semantically-identical hoisted-flag form -> 24/24 schema-valid; Phase 5/verifier must use hoisted-flag linter
- [Phase 04 gap-closure]: Closed SC1 partial gap from 04-VERIFICATION.md — deleted the ~37 lines of commented-out dead code ERA001's heuristic could not flag (orphaned class/def/decorator headers left by 04-04's ERA001-only sweep) across 6 src files + stale DeSpAn pyproject leftovers (commit 4192da5); explanatory prose preserved; suite still 19 passed / 11 xfailed / 0 xpassed, ruff format + hygiene gate clean; appended forward-only correction to 04-04-SUMMARY (18cf7e7 did NOT fully remove TriangulationData/BarycentricInterpolation)

### Pending Todos

- [Phase 4] Guard module-level private pchandler `_TransformArray` import in `projection.py:12` — a future pchandler drop/rename would break importing the whole projection module (spherical/orthographic included), not just perspective. Source: Phase 1 review IN-03. (`.planning/todos/pending/2026-07-09-guard-transformarray-module-import.md`, `resolves_phase: 4`)

### Blockers/Concerns

- Requirement-count discrepancy: REQUIREMENTS.md coverage note said "23 total" but there are 24 distinct requirement IDs. Traceability corrected to 24; confirm at next review.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260709-nvp | Re-ignore Python bytecode caches under scripts/ (fix over-broad `!/scripts/**` negation) | 2026-07-09 | bec9950 | [260709-nvp-re-ignore-python-bytecode-caches-under-s](./quick/260709-nvp-re-ignore-python-bytecode-caches-under-s/) |

### Roadmap Evolution

- Phase 03.1 inserted after Phase 3: RRIM (Red Relief Image) IP status clarification (URGENT)

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-10T20:01:22.740Z
Stopped at: Phase 5 context gathered
Resume file: .planning/phases/05-bug-fixes-module-test-coverage/05-CONTEXT.md
