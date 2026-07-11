# Requirements: pc2img

**Defined:** 2026-07-08
**Core Value:** Reliably turn 3D point clouds into correct, reproducible 2D feature rasters — sound in code and math, running against current PCHandler 2.x + GSEGUtils releases.

## v1 Requirements

Milestone-1 scope: hardening + adaptation for publication readiness. Each maps to roadmap phases.

### Dependency Adaptation

- [x] **DEP-01**: pc2img runs against PCHandler 2.x with all semantic/runtime breaks resolved (FoVTree 2D `"<r>-<c>"` identifiers, world-frame `to_py4dgeo`, Csv/Las load behavior)
- [x] **DEP-02**: pc2img runs against the current GSEGUtils release (`lazy_disk_cache`, `config`, `base_types` usage), respecting the `gsegutils`/`GSEGUtils` casing gotcha
- [x] **DEP-03**: `pyproject.toml` re-enables and correctly pins `pchandler` + `GSEGUtils`, and resolves the numpy pin conflict (numpy 2.x)
- [x] **DEP-04**: The dev environment is reproducibly set up with `uv` (documented; lockfile committed)

### Branch Untangling

- [x] **BRANCH-01**: A branch inventory documents which branches carry live development vs are dead (`develop/tomislav` excluded)
- [x] **BRANCH-02**: The richer `dev/*` architecture is consolidated into `develop-gsd` as the single forward-development mainline
- [x] **BRANCH-03**: The stale `feature/update_to_pchandler-1.0.0` branch is analyzed and dispositioned (salvage or retire)

### Code Quality & Algorithmic Soundness

- [x] **QUAL-01**: Code-hygiene cleanup — dead/commented code removed, duplicate `joblib` pin collapsed, placeholder `pyproject` metadata replaced, duplicate `convert_to_image` removed, matplotlib moved to an optional extra
- [x] **QUAL-02**: Software-design review completed; findings addressed or logged (divergent registries, in-place raster mutation, missing dependency-cycle guard, broken `make_generator` factory)
- [x] **QUAL-03**: Mathematical/algorithmic soundness review of projection geometry, Delaunay culling heuristics, NaN-aware smoothing, and feature math; findings addressed or logged

### Bug Fixes (each with a proving test)

- [x] **BUG-01**: `OrthographicProjection.project_raw` returns correct arity and column indexing; orthographic projection produces correct output
- [x] **BUG-02**: `DiskBackedImageData.__array_ufunc__` behaves correctly (supports arithmetic or raises a proper `NotImplementedError`)
- [x] **BUG-03**: `TIGSettings.extend_cache_paths` preserves `interp_kwargs` (no `None` overwrite)
- [x] **BUG-04**: `rrim.py` module docstring is present and accessible (`__doc__` populated)
- [x] **BUG-05**: Correctness bugs surfaced by the QUAL-03 review are fixed, each with a proving test

### Test & Coverage

- [x] **TEST-01**: pytest configuration scopes discovery to `tests/` (stops collecting `third_party/`)
- [x] **TEST-02**: Coverage measurement + reporting established with a recorded baseline
- [x] **TEST-03**: Projection & interpolation math covered by tests
- [x] **TEST-04**: Derivative features + feature-name DSL covered by tests
- [x] **TEST-05**: Orchestration (`FeatureManager`, `TiledPointCloudImageGenerator`) covered by tests
- [x] **TEST-06**: `util.py` (`convert_to_image`, `replace_nan`, `to_gray`, `nanconv`) covered by tests

### CI/CD

- [x] **CICD-01**: Lightweight CI runs the test suite on pull requests (early safety net)
- [ ] **CICD-02**: Branch protection + publication hardening matching the PCHandler template (pre-ship)

### Downstream Migration

- [ ] **BC-01**: A structured, GSD-consumable breaking-change / migration record of pc2img's own public API/behavior changes this milestone, for downstream consumers to rework against

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Performance

- **PERF-01**: Replace full-array SHA-256 triangulation keying with shape/extent metadata or a cached grid hash
- **PERF-02**: Use float32 (not float16) in `nanconv`; reduced precision becomes explicit opt-in — **pulled forward into Phase 5 (D-03)**; landed as the `nanconv(..., *, compute_dtype=np.float32)` opt-in (05-03). See Traceability.
- **PERF-03**: Promote Delaunay triangle-quality thresholds to constructor parameters — **pulled forward into Phase 5 (D-03)**; landed as the `DelaunayInterpolation` culling-threshold kwargs (05-05). See Traceability.
- **PERF-04**: Bound `_triangulation_precalc` growth (eviction / max size / per-tile scoping)

### GPU

- **GPU-01**: Validate and test the `cuda11` / `cuda12` optional extras against current RAPIDS

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| `develop/tomislav` branch consolidation | Explicitly excluded by project owner |
| New projection / interpolation / feature algorithms (except the folded `PerspectiveProjection`) | Milestone hardens & adapts existing capability, not new features. **Owner-approved exception (D-02):** `PerspectiveProjection`, folded onto the mainline in Phase 1, is in scope (WIP; math owned by Phase 4, coverage by Phase 5 per D-03). No other new algorithms are in scope. |
| Unapproved edits to PCHandler / GSEGUtils | Changes to those repos require explicit human approval first |
| UI / frontend surface | Backend/library only |
| Monetization | Academic research library |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEP-01 | Phase 2 | Complete |
| DEP-02 | Phase 2 | Complete |
| DEP-03 | Phase 2 | Complete |
| DEP-04 | Phase 2 | Complete |
| BRANCH-01 | Phase 1 | Complete |
| BRANCH-02 | Phase 1 | Complete |
| BRANCH-03 | Phase 1 | Complete |
| QUAL-01 | Phase 4 | Complete |
| QUAL-02 | Phase 4 | Complete |
| QUAL-03 | Phase 4 | Complete |
| BUG-01 | Phase 5 | Complete |
| BUG-02 | Phase 5 | Complete |
| BUG-03 | Phase 5 | Complete |
| BUG-04 | Phase 5 | Complete |
| BUG-05 | Phase 5 | Complete (multi-plan: 05-02..05-07, 05-09, 05-10, 05-11 fixed each review-surfaced correctness bug with a proving test; 05-08 contributed the GSEGUtils public class-registration hook unblocking the store consolidation — all contributing fixes landed) |
| TEST-01 | Phase 3 | Complete |
| TEST-02 | Phase 3 | Complete |
| TEST-03 | Phase 5 | Complete |
| TEST-04 | Phase 5 | Complete |
| TEST-05 | Phase 5 | Complete |
| TEST-06 | Phase 5 | Complete |
| CICD-01 | Phase 3 | Complete |
| CICD-02 | Phase 6 | Pending |
| BC-01 | Phase 6 | Pending |
| PERF-02 | Phase 5 | Complete (v2 item pulled forward — D-03; `nanconv` float32 default + `compute_dtype` opt-in, 05-03) |
| PERF-03 | Phase 5 | Complete (v2 item pulled forward — D-03; Delaunay culling-threshold kwargs, 05-05) |

**Coverage:**

- v1 requirements: 24 total (note: earlier "23 total" undercounted by one; there are 24 distinct IDs)
- Mapped to phases: 24 ✓
- Unmapped: 0
- v2 requirements pulled forward and traced to Phase 5: 2 (PERF-02, PERF-03; D-03). The remaining v2 items (PERF-01, PERF-04, GPU-01) stay deferred/untraced.

---
*Requirements defined: 2026-07-08*
*Last updated: 2026-07-08 after roadmap creation (traceability mapped)*
