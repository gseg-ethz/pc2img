# Roadmap: pc2img

## Overview

Milestone 1 is a hardening + adaptation pass, not new feature development. The journey
runs concern-first: establish a single clean mainline, make the package import and run
against reworked PCHandler 2.x + GSEGUtils in a reproducible `uv` environment, stand up a
test/CI safety net, then review code and math soundness, fix the bugs that surfaces (with
proving tests) while filling the coverage gaps, and finally harden for publication and emit
a structured breaking-change record for downstream consumers. Each phase leaves the library
more correct, more installable, and closer to publishable.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Branch Untangling & Mainline Consolidation** - Establish develop-gsd as the single forward mainline; inventory and disposition all other branches (completed 2026-07-08)
- [x] **Phase 2: Dependency Adaptation & Reproducible Environment** - Make pc2img import and run against PCHandler 2.x + GSEGUtils with pinned deps and a committed uv lockfile (completed 2026-07-09)
- [x] **Phase 3: Test & CI Foundation** - Scope pytest to tests/, record a coverage baseline, run the suite on PRs as an early safety net (completed 2026-07-09)
- [x] **Phase 4: Code Quality & Algorithmic Soundness Review** - Clean hygiene, review software design and projection/interpolation/feature math; log correctness findings (completed 2026-07-10)
- [ ] **Phase 5: Bug Fixes & Module Test Coverage** - Fix known + review-surfaced bugs with proving tests and cover the untested core modules (REOPENED 2026-07-27 — round-2 review gaps G9-G12; the 2026-07-11 completion is superseded)
- [ ] **Phase 6: Publication Hardening & Downstream Migration Record** - Branch protection + publication CI/CD matching PCHandler; emit a structured breaking-change record

## Phase Details

### Phase 1: Branch Untangling & Mainline Consolidation

**Goal**: Establish `develop-gsd` as the single forward-development mainline carrying the richest architecture, with every other branch inventoried and dispositioned.
**Depends on**: Nothing (first phase)
**Requirements**: BRANCH-01, BRANCH-02, BRANCH-03
**Success Criteria** (what must be TRUE):

  1. A branch-inventory document classifies every branch as live or dead with a disposition (`develop/tomislav` explicitly excluded).
  2. `develop-gsd` contains the richer `dev/*` architecture (`features/`, `image_cache/`, `strategies/`, `tiled_generator.py`) as the consolidated mainline.
  3. The stale `feature/update_to_pchandler-1.0.0` branch has a recorded salvage-or-retire decision and has been acted on.
  4. No divergent `dev/*` branch carries development work that is not reflected in `develop-gsd`.

**Plans**: 4/4 plans complete
**Wave 1**

- [x] 01-01-PLAN.md — Fold origin/dev/perspective_projection onto the phase-branch mainline (archive-tag, clean merge, prune local persp) [BRANCH-02]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Verify dev/v2 consolidation, prune fully-merged locals, amend PROJECT/REQUIREMENTS Out-of-Scope (D-02) [BRANCH-02]

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Retire pchandler-1.0 local label + author the branch-inventory doc [BRANCH-01, BRANCH-03]

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-04-PLAN.md — Merge the completed phase branch forward into develop-gsd; prove SC2/SC4 on the mainline itself [BRANCH-02]

### Phase 2: Dependency Adaptation & Reproducible Environment

**Goal**: pc2img imports and runs correctly against PCHandler 2.x + the current GSEGUtils release, with a correctly pinned, reproducible `uv` environment.
**Depends on**: Phase 1
**Requirements**: DEP-01, DEP-02, DEP-03, DEP-04
**Success Criteria** (what must be TRUE):

  1. Importing pc2img and running the single-cloud pipeline succeeds against `pchandler` 2.x with the semantic/runtime breaks resolved (FoVTree 2D `"<r>-<c>"` identifiers, world-frame `to_py4dgeo`, Csv/Las load behavior).
  2. pc2img uses the current GSEGUtils release correctly (`lazy_disk_cache`, `config`, `base_types`), respecting the `gsegutils`/`GSEGUtils` casing gotcha.
  3. `pyproject.toml` declares and pins `pchandler` + `GSEGUtils` and resolves the numpy 2.x pin conflict; a clean install imports the package without local `third_party/` symlinks.
  4. A documented `uv` workflow reproduces the dev environment from a committed lockfile.

**Plans**: 3/3 plans complete

**Wave 1**

- [x] 02-01-PLAN.md — Re-enable + pin pchandler/GSEGUtils, rewire cuda extras to pchandler[cudaXX], PEP 735 groups + nvidia index [DEP-03, DEP-04]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Generate/commit universal uv.lock, clean-room install proof (SC3), CONTRIBUTING.md uv workflow [DEP-03, DEP-04]

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — Commit synthetic SC1 smoke script + fix scripts gitignore trap + pchandler-2x break-audit attestation [DEP-01, DEP-02]

### Phase 3: Test & CI Foundation

**Goal**: A project-scoped test harness, a recorded coverage baseline, and CI that runs the suite on pull requests as a safety net for the heavy work that follows.
**Depends on**: Phase 2
**Requirements**: TEST-01, TEST-02, CICD-01
**Success Criteria** (what must be TRUE):

  1. `pytest` run from the repo root collects only `tests/` and produces no `third_party/` collection errors.
  2. Coverage measurement runs and a baseline percentage is recorded and reported.
  3. A CI workflow runs the test suite automatically on every pull request and reports pass/fail.

**Plans**: 3/3 plans complete

**Wave 1**

- [x] 03-01-PLAN.md — Add pytest/coverage config tables + three dev-group test-tooling pins, regenerate uv.lock [TEST-01, TEST-02]

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md — Reach a green scoped suite by triage: delete 2 import-broken modules, xfail the current failures [TEST-01]

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-03-PLAN.md — Measure + record the coverage baseline (CONTRIBUTING) and add the lightweight PR CI workflow [TEST-02, CICD-01]

### Phase 03.1: RRIM (Red Relief Image) IP status clarification (INSERTED)

**Goal:** Clear the blocking RRIM IP/publication gate by executing the locked keep-on-patent-expiry disposition (D-09..D-12) in-tree — shipped IP findings doc + NOTICE (expiry basis + AAS/Chiba/Yokoyama attribution + RRIM® trademark disclaimer), an ADR, an opt-in `rrim` extra with a reconciled docstring, an internal good-faith ETH/owner sign-off, and the blocking todo resolved — leaving the branch provably publication-safe so Phase 3's live-CI push can proceed.
**Requirements**: none mapped (driven by CONTEXT decisions D-09..D-12)
**Depends on:** Phase 3
**Plans:** 3/3 plans complete

Plans:
**Wave 1**

- [x] 03.1-01-PLAN.md — IP findings doc (shipped) + ADR recording the locked disposition (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03.1-02-PLAN.md — top-level NOTICE + opt-in `rrim` extra + reconciled rrim.py docstring (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03.1-03-PLAN.md — verify suite green + coverage floor unchanged, ETH/owner sign-off, resolve blocking todo (Wave 3)

### Phase 4: Code Quality & Algorithmic Soundness Review

**Goal**: Code hygiene, software-design flaws, and mathematical/algorithmic soundness reviewed; fixes applied or findings logged, feeding concrete bug items into Phase 5.
**Depends on**: Phase 3
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):

  1. Dead/commented code is removed, the duplicate `joblib` pin is collapsed, placeholder `pyproject` metadata is replaced, the duplicate `convert_to_image` is removed, and matplotlib is moved to an optional extra.
  2. The software-design review is complete with each finding (divergent registries, in-place raster mutation, missing dependency-cycle guard, broken `make_generator` factory) addressed or explicitly logged with rationale.
  3. A mathematical/algorithmic soundness review of projection geometry, Delaunay culling heuristics, NaN-aware smoothing, and feature math is complete.
  4. Correctness issues surfaced by the soundness review are captured as concrete, testable bug items (BUG-05 inputs for Phase 5).

**Plans**: 7/7 plans complete

**Wave 0**

- [x] 04-01-PLAN.md — Swap black→ruff in the dev group + author tests/test_hygiene.py smoke/metadata/lint gate [QUAL-01]

**Wave 1** *(blocked on Wave 0)*

- [x] 04-02-PLAN.md — pyproject full pass: [tool.ruff] config, joblib collapse, viz extra, metadata + human-verify gate for PyPI-facing URL/license, cuda note [QUAL-01]
- [x] 04-03-PLAN.md — Mechanical source FIX: repair/delete make_generator, guard _TransformArray, sync features __all__, delete dup convert_to_image [QUAL-01, QUAL-02]

**Wave 2** *(blocked on Wave 1)*

- [x] 04-04-PLAN.md — ruff sweep: check --fix + deliberate ERA001 deletion + ruff format; keep registration + suite green [QUAL-01]

**Wave 3** *(blocked on Wave 2)*

- [x] 04-05-PLAN.md — Design-track review (D1–D4) find→refute → 04-FINDINGS-design.md (4 anchors + pickle finding) [QUAL-02]
- [x] 04-06-PLAN.md — Math-track review (M1–M5) find→refute with numeric probes → 04-FINDINGS-math.md [QUAL-03]

**Wave 4** *(blocked on Wave 3)*

- [x] 04-07-PLAN.md — Synthesis + phase gate: merge/dedupe/re-anchor into canonical 04-FINDINGS.md [QUAL-02, QUAL-03]

### Phase 5: Bug Fixes & Module Test Coverage

**Goal**: All known and review-surfaced correctness bugs fixed, each with a proving test, and the previously untested core modules covered.
**Depends on**: Phase 4
**Requirements**: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05, TEST-03, TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):

  1. Orthographic projection returns the correct arity and column indexing and produces correct output (BUG-01), proven by a test.
  2. `DiskBackedImageData.__array_ufunc__` supports arithmetic or raises a proper `NotImplementedError` (BUG-02), proven by a test.
  3. `TIGSettings.extend_cache_paths` preserves `interp_kwargs` (BUG-03) and `rrim.py.__doc__` is populated (BUG-04), each proven by a test.
  4. Every correctness bug surfaced by the QUAL-03 review is fixed with a proving test (BUG-05).
  5. Projection/interpolation math, derivative features + the feature-name DSL, orchestration (`FeatureManager`, `TiledPointCloudImageGenerator`), and `util.py` all have passing test coverage (TEST-03..06).

**Plans**: 17/17 plans executed (05-16, 05-17 — round-4 gap closure, planned 2026-09-24, pending)

**Wave 1**

- [x] 05-01-PLAN.md — Shared synthetic fixture factory in tests/conftest.py (D-11) [TEST-03..06]
- [x] 05-08-PLAN.md — GSEGUtils Option A public class-registration hook + owner-approval checkpoint (D-05) [BUG-05]

**Wave 2** *(blocked on Wave 1)*

- [x] 05-02-PLAN.md — projection.py: M-01/BUG-01 orthographic + M-05/D-15 seam guard + M-02/03/04 perspective (D-01) [BUG-01, BUG-05, TEST-03]
- [x] 05-03-PLAN.md — util.py: nanconv copy-input + float32 (M-07/M-08/D-09) + convert_to_image all-NaN (M-09) [BUG-05, TEST-06]
- [x] 05-04-PLAN.md — derivative_features.py: DSN-03+M-12 fix + M-10/M-11 kept-behavior params (D-07/D-08) [BUG-05, TEST-04]
- [x] 05-05-PLAN.md — interpolation.py: M-06 kept-behavior culling thresholds (D-06/PERF-03) + oracle [BUG-05, TEST-03]
- [x] 05-06-PLAN.md — rrim.py: BUG-04 docstring/E402 reorder; M-13 defer/log (D-16) [BUG-04, BUG-05]
- [x] 05-07-PLAN.md — registry unification: RegistryLookupError + dependencies_for + DSN-11 (D-14) [BUG-05, TEST-04]
- [x] 05-09-PLAN.md — image_cache reparent (D-04/BUG-02) + DiskBackedStore WRAPPER + pickle-sink removal (D-05/DSN-09) [BUG-02, BUG-05]

**Wave 3** *(blocked on Wave 2)*

- [x] 05-10-PLAN.md — tiled_generator.py: BUG-03 interp_kwargs + DSN-10 + DSN-07 [BUG-03, BUG-05, TEST-05]
- [x] 05-11-PLAN.md — manager.py + core.py: DSN-04/07/08 + DSN-06 omitted-config coercion [BUG-05, TEST-05]

**Wave 4** *(blocked on Wave 3)*

- [x] 05-12-PLAN.md — Re-measure coverage + ratchet CI floor (D-10) + consolidate BC-01 note (D-17) [BUG-05, TEST-03..06]

**Gap closure** *(post-UAT code-review gaps; additive — no shipped plan modified)*

- [x] 05-13-PLAN.md — Round 1: 8 review gaps G1-G8 (RRIM dependencies_for blocker, K validation, store purge, float64 rotation, single-sourcing) [BUG-05, TEST-03, TEST-04]
- [x] 05-14-PLAN.md — Round 2: G9-G12 — RRIM z_factor round-trip blocker + store delete no-side-effect-on-KeyError blocker (both introduced by 05-13) + G11/G12 BC-record entries [BUG-05]
- [x] 05-15-PLAN.md — Round 3: WR-02 store-key path containment (unlink/write escape from the cache dir) + WR-03 base-feature-vs-option precedence BC record & pin + gap-status reconciliation [BUG-05]
- [x] 05-16-PLAN.md — Round 4 (wave 1, store): refused-delete atomicity BLOCKER (introduced by 05-15) fixed RED-first with G10 intact; symlinked-entry and value-supplied-cache_path claims reproduced→branched; threat posture corrected to load-bearing on GSEGUtils 0.5.x (registry default fallback); guard-sensitive tests + mutation check; IN-01 (actual location: store module), IN-03 None-sentinel + BC entry 17, WR-06 [BUG-05]
- [x] 05-17-PLAN.md — Round 4 (wave 2, RRIM + bookkeeping): precedence pinned at FEATURES.match surface, z-sensitivity end-to-end, upper z boundary (name-level), _validate_clip names its clip; Phase-6 todo for the absorption-superseded containment findings; UAT/VERIFICATION evidence-cited reconciliation [BUG-05, TEST-04]

### Phase 6: Publication Hardening & Downstream Migration Record

**Goal**: The repository meets the PCHandler publication standard and emits a structured breaking-change record for downstream consumers.
**Depends on**: Phase 5
**Requirements**: CICD-02, BC-01
**Success Criteria** (what must be TRUE):

  1. Branch protection and publication CI/CD matching the PCHandler template are in place on the mainline.
  2. The package builds and is publishable to PyPI with correct, non-placeholder metadata.
  3. A structured, GSD-consumable breaking-change / migration record documents pc2img's own public API/behavior changes this milestone, ready for downstream consumers to rework against.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Branch Untangling & Mainline Consolidation | 4/4 | Complete    | 2026-07-08 |
| 2. Dependency Adaptation & Reproducible Environment | 3/3 | Complete    | 2026-07-09 |
| 3. Test & CI Foundation | 3/3 | Complete    | 2026-07-09 |
| 4. Code Quality & Algorithmic Soundness Review | 7/7 | Complete   | 2026-07-10 |
| 5. Bug Fixes & Module Test Coverage | 17/17 | In Progress|  |
| 6. Publication Hardening & Downstream Migration Record | 0/TBD | Not started | - |
