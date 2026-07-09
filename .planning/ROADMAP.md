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
- [ ] **Phase 3: Test & CI Foundation** - Scope pytest to tests/, record a coverage baseline, run the suite on PRs as an early safety net
- [ ] **Phase 4: Code Quality & Algorithmic Soundness Review** - Clean hygiene, review software design and projection/interpolation/feature math; log correctness findings
- [ ] **Phase 5: Bug Fixes & Module Test Coverage** - Fix known + review-surfaced bugs with proving tests and cover the untested core modules
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

**Plans**: TBD

### Phase 4: Code Quality & Algorithmic Soundness Review

**Goal**: Code hygiene, software-design flaws, and mathematical/algorithmic soundness reviewed; fixes applied or findings logged, feeding concrete bug items into Phase 5.
**Depends on**: Phase 3
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):

  1. Dead/commented code is removed, the duplicate `joblib` pin is collapsed, placeholder `pyproject` metadata is replaced, the duplicate `convert_to_image` is removed, and matplotlib is moved to an optional extra.
  2. The software-design review is complete with each finding (divergent registries, in-place raster mutation, missing dependency-cycle guard, broken `make_generator` factory) addressed or explicitly logged with rationale.
  3. A mathematical/algorithmic soundness review of projection geometry, Delaunay culling heuristics, NaN-aware smoothing, and feature math is complete.
  4. Correctness issues surfaced by the soundness review are captured as concrete, testable bug items (BUG-05 inputs for Phase 5).

**Plans**: TBD

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

**Plans**: TBD

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
| 2. Dependency Adaptation & Reproducible Environment | 3/3 | Complete   | 2026-07-09 |
| 3. Test & CI Foundation | 0/TBD | Not started | - |
| 4. Code Quality & Algorithmic Soundness Review | 0/TBD | Not started | - |
| 5. Bug Fixes & Module Test Coverage | 0/TBD | Not started | - |
| 6. Publication Hardening & Downstream Migration Record | 0/TBD | Not started | - |
