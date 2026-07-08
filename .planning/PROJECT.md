# pc2img

## What This Is

`pc2img` is a scientific Python library (ETH Zurich, GSEG group) that converts 3D
point clouds into 2D raster images: it projects points into image space
(spherical or orthographic), interpolates scattered values onto a pixel grid, and
computes named "features" (range, scalar fields, gradients, hillshade, RRIM,
multiscale gradient, …) as rasters, held in a lazy disk-backed cache. A tiled
orchestrator fans the same pipeline across many point-cloud tiles in parallel. It
depends on two sibling GSEG libraries — **PCHandler** (point-cloud data/geometry)
and **GSEGUtils** (lazy disk caching) — and is itself consumed by downstream
geospatial / deformation-analysis tooling.

## Core Value

Reliably turn 3D point clouds into **correct, reproducible 2D feature rasters** —
the projection → interpolation → feature pipeline must be sound (in code and in
math) and must run against the current PCHandler 2.x + GSEGUtils releases.

## Business Context

<!-- Research library heading toward publication; not monetized. -->

- **Customer**: GSEG research group + downstream GSEG libraries that consume pc2img rasters
- **Revenue model**: n/a — academic / open research library
- **Success metric**: Publishable, installable-from-PyPI package that imports cleanly against reworked deps, with a trustworthy test suite and CI/CD matching the PCHandler standard
- **Strategy notes**: Milestone 1 is a hardening + adaptation pass, not new feature development

## Requirements

### Validated

<!-- Capabilities that exist in the codebase and are relied upon (brownfield-inferred). -->

- ✓ Single-cloud pipeline: spherical projection → Delaunay interpolation → feature rasters — existing
- ✓ Named-feature DSL with regex matching + dependency resolution (`FeatureManager` / `FeatureRegistry`) — existing
- ✓ Lazy disk-backed image cache built on `GSEGUtils.LazyDiskCache` — existing
- ✓ Parallel tiled generation over many tiles (joblib/loky) — existing
- ✓ RRIM and multiscale-gradient feature families — existing
- ✓ Branch untangling & mainline consolidation: `develop-gsd` established as the single forward mainline (richer `dev/*` architecture folded in, incl. the WIP `PerspectiveProjection`); every branch inventoried/dispositioned (`develop/tomislav` excluded); stale `feature/update_to_pchandler-1.0.0` retired — Validated in Phase 1 (BRANCH-01/02/03)

### Active

<!-- Milestone-1 scope. Hypotheses until shipped and validated. -->

**Dependency adaptation**
- [ ] Adapt pc2img to reworked PCHandler 2.x + GSEGUtils (semantic/runtime breaks, not just imports)
- [ ] Resolve the `numpy` pin conflict and re-enable/pin `pchandler` + `GSEGUtils` in `pyproject.toml`
- [ ] Standardize the dev environment on `uv`

**Code Quality & Algorithmic Soundness**
- [ ] Review for code hygiene / tech debt (dead code, duplicate `joblib` pin, placeholder metadata, duplicate `convert_to_image`, matplotlib extra, `make_generator` factory)
- [ ] Review for software design flaws (e.g. two divergent registries, in-place raster mutation, missing dependency-cycle guard)
- [ ] Review implementations for mathematical / algorithmic soundness (projection geometry, Delaunay culling heuristics, NaN-aware smoothing, feature math)

**Bug fixes (explicit, each with a proving test)**
- [ ] `OrthographicProjection.project_raw` return-arity + column-indexing bug
- [ ] `DiskBackedImageData.__array_ufunc__` raising the `NotImplemented` singleton
- [ ] `TIGSettings.extend_cache_paths` storing `None` for `interp_kwargs`
- [ ] `rrim.py` inert module docstring
- [ ] Any additional correctness bugs surfaced by the algorithmic-soundness review

**Test & coverage strengthening**
- [ ] Add pytest configuration scoping discovery to `tests/` (stop collecting `third_party/`)
- [ ] Establish coverage analysis / reporting
- [ ] Add tests across untested modules: projection/interpolation math, derivative features, feature-name DSL, orchestration (`FeatureManager`, tiled generator), `util`

**CI/CD (split)**
- [ ] Early: lightweight CI that runs the test suite on PRs
- [ ] Pre-ship: branch protection + publication hardening matching PCHandler's template

**Downstream-facing breaking-change tracking**
- [ ] Emit a structured, GSD-consumable breaking-change / migration record for the changes pc2img makes to its own public API/behavior this milestone, so downstream consumers can rework against it

### Out of Scope

- `develop/tomislav` branch — explicitly excluded from consolidation per project owner
- New projection/interpolation/feature algorithms — this milestone hardens and adapts existing capability, not new features. **Exception (owner-approved, D-02):** the `PerspectiveProjection` strategy folded onto the mainline in Phase 1 is explicitly **in scope** — it rode in with the `dev/perspective_projection` fold and is WIP; its projection math is owned by Phase 4 (algorithmic-soundness) and its test coverage by Phase 5 (D-03). No *other* new algorithms are in scope.
- Unapproved edits to PCHandler / GSEGUtils — changes to those repos require explicit human approval first
- UI / frontend surface — backend/library only
- Monetization — academic research library

## Context

- **Brownfield, mid-rework.** The package currently comments its two core deps out of `pyproject.toml` and cannot `pip install` cleanly; deps are wired locally via `third_party/` symlinks to `/scratch/30_GSEGUtils` and `/scratch/41_pchandler` (both match current PyPI releases). `third_party/` and `.venv/` are gitignored and never reach `main`.
- **Dependency reality (verified 2026-07-08):** `develop-gsd`'s `dev/v2` base is already import-clean against `pchandler==2.1.0.post2` and `gsegutils==0.5.2.post2`; the remaining work is semantic/runtime breaks (BC-PCH-008 FoVTree 2D identifiers, BC-PCH-007 world-frame `to_py4dgeo`, Csv/Las load behavior) plus the `numpy ~=1.24` vs `>=2.0,<2.4` pin conflict and `pyproject` pin updates (currently `pchandler ~= 0.4`). Package-name casing gotcha: distribution is `gsegutils` (lowercase) but the importable package is `GSEGUtils`.
- **Branch chaos:** `main` (flatter, older) vs `dev/v2` / `dev/perspective_projection` (richer `features/` `image_cache/` `strategies/` `tiled_generator.py`); `feature/update_to_pchandler-1.0.0` targets a two-majors-stale PCHandler 1.0.
- **Codebase map:** `.planning/codebase/` (refreshed 2026-07-08) holds the architecture, concerns, conventions, integrations, stack, structure, and testing analyses that seed this milestone.
- **Publication goal:** the library is being prepared for public release; CI/CD and branch protection should match the PCHandler project's template.

## Constraints

- **Tech stack**: Python `~=3.12`, numpy 2.x, scipy, pydantic v2, joblib/loky — Established scientific stack; numpy 2.x forced by PCHandler 2.x
- **Dependencies**: PCHandler 2.x + GSEGUtils 0.5.x — Core input/persistence layers; on-disk sources match PyPI
- **Environment**: `uv`-managed venv; deps via `third_party/` symlinks (gitignored) — Offline/local dep resolution; install GSEGUtils before PCHandler
- **Dependency edits**: changes to PCHandler / GSEGUtils require human approval — They are separate GSD-managed repos
- **Branching**: work on `develop-gsd` + per-phase branches; `main` only at milestone ship, stripped of `.planning/` and agent-specific files — Keep the public branch clean of planning artifacts
- **Publication standard**: branch protection + CI/CD match the PCHandler template — Consistency across GSEG libraries
- **Commit messages**: conventional-commit scopes use traditional/functional scopes (e.g. `fix(projection):`, `test(features):`), never GSD planning-ID tags (no `(BUGS-05)`-style IDs in the parentheses) — Commits squash to `main` where `.planning/` is stripped, so planning-ID references in scopes would dangle

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Milestone 1 is a hardening + adaptation pass (dep adaptation, branch untangling, quality/algorithmic review, bugs, tests, CI/CD, downstream BC tracking) | Package must become correct, installable, and publishable against reworked deps before new work | — Pending |
| CI/CD split: lightweight test-CI early, branch-protection/publication hardening pre-ship | Early safety net for the heavy adaptation/refactor work without paying full publication-polish cost upfront | — Pending |
| Known bugs tracked as explicit v1 requirements, each with a proving test | Maximum traceability; couples bug closure to the test-coverage pillar | — Pending |
| Test suite + coverage analysis is a first-class pillar, not incidental cleanup | Most core modules are untested; publication needs a trustworthy suite | — Pending |
| Deepen the quality pillar to include mathematical/algorithmic soundness, not just code hygiene | Design and math flaws can hide correctness bugs beyond the four already known | — Pending |
| pc2img emits its own structured, GSD-consumable breaking-change record for downstream consumers | Mirrors PCHandler's migration-doc approach so downstream libraries can rework via GSD | — Pending |
| Work on `develop-gsd` + phase branches; ship stripped to `main` | Keep the public history free of agent/planning files | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-09 — Phase 1 (Branch Untangling & Mainline Consolidation) complete: develop-gsd is the consolidated mainline.*
