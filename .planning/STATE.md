---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 6
current_phase_name: Publication Hardening & Downstream Migration Record
status: verifying
stopped_at: Completed 05-10-PLAN.md
last_updated: "2026-07-11T06:01:48.954Z"
last_activity: 2026-07-11
last_activity_desc: Phase 05 complete, transitioned to Phase 6
progress:
  total_phases: 7
  completed_phases: 6
  total_plans: 32
  completed_plans: 32
  percent: 86
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-08)

**Core value:** Reliably turn 3D point clouds into correct, reproducible 2D feature rasters — sound in code and math, running against current PCHandler 2.x + GSEGUtils releases.
**Current focus:** Phase 05 — bug-fixes-module-test-coverage

## Current Position

Phase: 6 — Publication Hardening & Downstream Migration Record
Plan: Not started
Status: Phase complete — ready for verification
Last activity: 2026-07-11 — Phase 05 complete, transitioned to Phase 6

Progress: [███████░░░] 69%

## Performance Metrics

**Velocity:**

- Total plans completed: 25
- Average duration: - min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |
| 02 | 3 | - | - |
| 03 | 3 | - | - |
| 03.1 | 3 | - | - |
| 05 | 12 | - | - |

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
| Phase 05 P01 | 12min | 2 tasks | 2 files |
| Phase 05 P02 | 6min | 3 tasks | 2 files |
| Phase 05 P03 | 8min | 2 tasks | 2 files |
| Phase 05 P04 | 3min | 2 tasks | 2 files |
| Phase 05 P05 | 6min | 2 tasks | 2 files |
| Phase 05 P06 | 8min | 2 tasks | 2 files |
| Phase 05 P09 | 13min | 4 tasks | 7 files |
| Phase 05 P07 | 11min | 2 tasks | 6 files |
| Phase 05 P10 | 16min | 2 tasks | 2 files |
| Phase 05 P11 | 4min | 2 tasks | 5 files |
| Phase 05 P12 | 12min | 2 tasks | 4 files |

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
- [Phase 05]: [Phase 05 P08] Landed owner-approved D-05 Option A — GSEGUtils public `register_lazy_disk_cache_class` hook (function + decorator) turning the closed reload allow-list into an extension point; D-02 posture preserved (explicit allow-list, no importlib, idempotent, TypeError on non-subclass, ValueError on name collision); 4 hook tests (incl. decorator form), full file 24 passed; landed on GSEGUtils branch `gsd/register-lazy-disk-cache-class` off main (commits aad300c + 2cf8083), pushed to origin
- [Phase 05]: [Phase 05 P08] Delivery route changed at the approved checkpoint from version tag to git-rev bridge — hand-rolled v0.6.0 tag REMOVED (release-please collision + open 0.5.3 PR); setuptools_scm build reports 0.5.2.post4, satisfying existing `GSEGUtils ~= 0.5`; pc2img consumes the hook via [tool.uv.sources] git-rev @ 2cf80835aa724f64a83853c8e35c91cb7640a919 + re-lock (05-09); PyPI `~= 0.6` conversion + drop-git-entry DEFERRED to Phase 6 (D-17/BC-01)
- [Phase ?]: [Phase 05 P02] M-04 adapted from 'delete project_raw' to a documented NotImplementedError refusal — deletion leaves the abstractmethod unimplemented and makes PerspectiveProjection uninstantiable (04-FINDINGS M-04 sanctions this); added OrthographicProjection.inverse_projection refusal (class was previously uninstantiable)
- [Phase ?]: [Phase 05 P02] Perspective rebuilt to pinned contract: keyword-only translation, extrinsic-first Transform.generate([R|t]) @ pcd, Z_c<=0 depth cull (M-02), K·(R·X+t) (M-03), eager 4×4→TypeError / non-orthonormal→ValueError validation (M-03b); D-15 seam guard raises on wrapping FoVs; BC: 4×4 rotation_matrix now raises (D-17)
- [Phase ?]: PERF-02 opt-in landed as nanconv compute_dtype (default np.float32); reduced precision engages only on explicit opt-in (D-03)
- [Phase ?]: 05-04: NormalizedFeature strict validation 0<=low<high<=100 + copy-before-mutate (DSN-03/M-12); GradientFeature opt-in pixel_size default 100 with DSL _px suffix, byte-identical (M-10); Hillshade aspect kept + documented (M-11)
- [Phase ?]: M-06 Delaunay interior-culling kept as default (D-06); thresholds surfaced as opt-in kwargs with byte-identical defaults
- [Phase ?]: interior_culling=False admits all in-hull triangles, matching scipy.LinearNDInterpolator NaN placement (oracle path for TEST-03)
- [Phase ?]: 05-06: rrim.py header reordered (docstring first, __future__ second) to populate __doc__ and clear E402x9 (BUG-04); M-13 deferred/logged per D-16, RRIM math untouched
- [Phase ?]: [Phase 05 P09] Finished the image_cache migration: DiskBackedImageData reparented onto GSEGUtils DiskBackedNDArray (BUG-02/DSN-02 fixed — arithmetic returns a plain ndarray via inherited __array_ufunc__; dropped __array_priority__ A1)
- [Phase ?]: [Phase 05 P09] DiskBackedImageStore is a thin WRAPPER over DiskBackedStore[DiskBackedImageData]; DSN-09 deserialization sink + .pkl paths deleted (security-by-construction, .npy+JSON allow_pickle=False codec); legacy names re-aliased, overwrite semantics preserved (pre-del)
- [Phase ?]: [Phase 05 P09] Delivered the 05-08 hook to CI via [tool.uv.sources] git-rev bridge @ 2cf80835 + re-locked uv.lock (git build 0.5.2.post4 satisfies GSEGUtils ~= 0.5); PyPI ~=0.6 conversion + drop-git-entry DEFERRED to Phase 6 (D-17/BC-01)
- [Phase ?]: [Phase 05 P09] BC (D-17): cache format .pkl -> .npy+.meta.json (legacy .pkl refused as cache miss); DiskBackedImageData arithmetic surface now live (returns ndarray, previously raised)
- [Phase ?]: 05-07: unified StrategyRegistry+FeatureRegistry on RegistryLookupError(KeyError,RuntimeError); dual inheritance preserves all except-clause catch behavior (BC-01/D-17)
- [Phase ?]: 05-07: FeatureRegistry.match() reads deps via overridable dependencies_for classmethod (no double __init__); Hillshade needed its own override None->range beyond the plan's Average/Sum/Norm list
- [Phase ?]: 05-10: tiled DSN-07 uses lightweight 'or LazyDiskCacheConfig()' sentinel; DSN-07 now consistent across all sites (D-17)
- [Phase ?]: 05-10: BUG-03 manifested as ValidationError (frozen pydantic dataclass re-validates replace(None)); fixed via build-dict-then-assign
- [Phase ?]: 05-11: DSN-07 sensor asserts the FeatureManager __init__ signature default IS the None sentinel — config is decomposed by DiskBackedStore and never retained, so post-construction object identity is unobservable
- [Phase ?]: 05-11: DSN-07 manager default uses 'or LazyDiskCacheConfig()' not coerce_lazy_cfg, to avoid a circular import (coerce_lazy_cfg lives in core.py which imports FeatureManager)
- [Phase ?]: 05-11: DSN-06 fixed via body-level idempotent coerce_lazy_cfg — pydantic @validate_call never runs the BeforeValidator on an omitted default

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

Last session: 2026-07-11T05:42:28.045Z
Stopped at: Completed 05-10-PLAN.md
Resume file: None
