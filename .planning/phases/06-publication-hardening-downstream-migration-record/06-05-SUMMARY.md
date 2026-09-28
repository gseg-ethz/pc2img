---
phase: 06-publication-hardening-downstream-migration-record
plan: 05
subsystem: docs
tags: [sphinx, sphinx-rtd-theme, readthedocs, autodoc, napoleon, docstrings]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "sphinx ~= 8.2.3 + sphinx_rtd_theme locked in the doc dependency group (plan 06-01)"
provides:
  - "Minimal Sphinx site (docs/source/conf.py, index.rst, api.rst) building warning-free under -W on Sphinx 8.2.3"
  - "Dynamic version display (importlib.metadata) with no release-please marker to reconcile"
  - ".readthedocs.yaml installing the PEP 735 doc group via pip>=25.1 --group, not an extras-based install"
  - "Full public API surface (18 modules) documented via automodule, including the opt-in rrim module"
affects: ["06-06 (release-please-config.json extra-files kit copy, drops the stale docs/conf.py pointer)"]

actuals:
  tokens: 2058
  tasks: 2
  commits: 2
  plan_head_before: dfbc4dec08d8e96b3622d2ec8ca966c2efcb0f70
  plan_head_after: 8571aa34733cb87a00762ee386d5d6bfb93bd265

tech-stack:
  added: []
  patterns:
    - "Sphinx conf.py version via importlib.metadata.version() instead of a release-please x-release-please-version marker"
    - "RTD doc-group install via build.jobs.install override (pip>=25.1 --group doc .) instead of python.install extra_requirements"

key-files:
  created:
    - docs/source/conf.py
    - docs/source/index.rst
    - docs/source/api.rst
    - .readthedocs.yaml
  modified:
    - src/pc2img/features/derivative_features.py
    - src/pc2img/strategies/projection.py

key-decisions:
  - "conf.py and .readthedocs.yaml comments reworded to plain prose (no D-NN tokens) so the phase 06-01 planning-vocabulary hygiene gate stays green on these newly shipped files, matching the gate's existing scope over the whole shipped tree."
  - "ProjectionStrategy.project_raw's Returns docstring was rewritten to document all four actual return values (coords_raw, mask, mins, maxs) instead of the original two (coords_raw, mask) — a content improvement made while fixing the RST formatting, since the function's true return shape was already a 4-tuple."

requirements-completed: [CICD-02]

coverage:
  - id: D1
    description: "Minimal Sphinx site (conf.py/index.rst/api.rst) builds warning-free under -W on Sphinx 8.2.3, using importlib.metadata for the version"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html"
        status: pass
    human_judgment: false
  - id: D2
    description: ".readthedocs.yaml installs the PEP 735 doc group via pip>=25.1 --group, not extras; fail_on_warning true"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "uv run --frozen pre-commit run check-yaml --files .readthedocs.yaml"
        status: pass
    human_judgment: true
    rationale: "The install command's correctness (pip --group doc . resolving the PEP 735 group on RTD's build container) cannot be exercised locally — no pip binary in this uv-managed venv, and no RTD build was triggered this session (RTD project import is an owner account action per 06-CONTEXT D-13). YAML syntax and the presence/absence of the required keys are proven; the first real RTD build is the actual proof, as the plan itself states."
  - id: D3
    description: "Full public API (18 modules, including features.rrim) documented via automodule, zero -W warnings on the full tree"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html (18 automodule directives, 0 warnings, exit 0)"
        status: pass
      - kind: unit
        ref: "uv run --frozen pytest -q (259 passed)"
        status: pass
      - kind: other
        ref: "ruff check src && ruff format --check src"
        status: pass
      - kind: other
        ref: "uv run --frozen pytest tests/test_hygiene.py -q -k planning_vocabulary (62 passed, 5 deselected)"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 05: Sphinx docs site + RTD config Summary

**Minimal Sphinx 8.2.3 site with dynamic versioning and full 18-module autodoc API reference, building warning-free under `-W`; `.readthedocs.yaml` installs the PEP 735 `doc` group via `pip>=25.1 --group` instead of an extras-based install.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2
- **Files created:** 4 (docs/source/{conf.py,index.rst,api.rst}, .readthedocs.yaml)
- **Files modified:** 2 (docstring-only fixes)

## Accomplishments

- Stood up `docs/source/conf.py` with `autodoc`/`napoleon`/`viewcode`, dynamic `release`/`version` via `importlib.metadata.version("pc2img")` (no literal version string, no release-please marker), and `sphinx_rtd_theme`.
- Wrote `.readthedocs.yaml` mirroring PCHandler's structural shape (`build.os: ubuntu-24.04`, `build.tools.python: "3.12"`, `sphinx.configuration: docs/source/conf.py`) but with an install override (`pip>=25.1 --group doc .`) instead of PCHandler's `extra_requirements: [doc]`, since `doc` is a PEP 735 dependency-group entry that the extras-based mechanism cannot see. `post_checkout` unshallows the repo so `setuptools_scm` can find tags. `sphinx.fail_on_warning: true` mirrors the CI `-W` gate.
- Task 1 proved the toolchain on a single module (`pc2img.core`) — zero warnings, immediately.
- Task 2 extended `api.rst` to all 18 public modules (grouped Core / Strategies / Features / Image cache, `features.rrim` included per its opt-in import-contract documentation role) and re-measured the full-tree `-W` build under Sphinx 8.2.3: **13 warnings**, same count as the 7-module sample measured under 5.3.0 in 06-RESEARCH.md but a different composition (D-32's re-measure rule).
- Fixed all 13 warnings as docstring-only content bugs in two files (see Deviations) — zero warnings, exit 0, on the full public API.

## Task Commits

1. **Task 1: conf.py + index + ONE autodoc page + .readthedocs.yaml, built green under -W** - `be04628` (docs)
2. **Task 2: Full API pages, re-measure -W under 8.2.x, fix the docstrings until green** - `8571aa3` (docs)

## Files Created/Modified

- `docs/source/conf.py` - Sphinx config: autodoc/napoleon/viewcode, dynamic version, sphinx_rtd_theme
- `docs/source/index.rst` - Landing page with one-paragraph description + toctree to api
- `docs/source/api.rst` - 18 automodule directives grouped Core/Strategies/Features/Image cache
- `.readthedocs.yaml` - RTD v2 build definition, PEP 735 doc-group install override
- `src/pc2img/strategies/projection.py` - `ProjectionStrategy.project_raw` docstring rewritten as a NumPy-style Returns section documenting all four return values (was missing a blank line before "Returns:" and used an unrecognized bullet shape, causing 4x2=8 of the 13 warnings via inheritance into Spherical/Orthographic/PerspectiveProjection)
- `src/pc2img/features/derivative_features.py` - `MultiScaleGradientFeature` and `OcclusionAwareMultiScaleGradientFeature` docstrings reworked with literal blocks (`::`) and blank-line separation; `MultiScaleGradientFeature`'s pipe-delimited `|∇|` (parsed by RST as an undefined substitution reference) replaced with the words "gradient magnitude"

## Decisions Made

- Reworded the D-13/D-31/D-32 references in the new `conf.py`/`.readthedocs.yaml` comments to plain prose — the phase 06-01 planning-vocabulary hygiene gate (`tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary`) is parametrized over every git-tracked file outside `.planning/`/`.claude/`, so it caught these two new files on first run and had to be satisfied like any other shipped source.
- Rewrote `ProjectionStrategy.project_raw`'s docstring to document all four of its actual return values (`coords_raw, mask, mins, maxs`) rather than just the two the original malformed docstring listed — a content improvement bundled into the same edit that fixed the RST formatting, since the function's real return shape was already a 4-tuple and the fix touched that exact text anyway.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reworded new-file planning-vocabulary hits to keep the hygiene gate green**
- **Found during:** Task 2 (full-suite verify step)
- **Issue:** The comments added in Task 1 for `docs/source/conf.py` and `.readthedocs.yaml` cited `D-13`/`D-31`/`D-32` decision IDs, which `tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary` flags on any git-tracked file outside `.planning/`/`.claude/` — including files first added in this very plan.
- **Fix:** Reworded both comment blocks to plain technical prose carrying the same reasoning (why the version is dynamic, why the doc group needs a `--group` install override) with no planning-ID tokens.
- **Files modified:** docs/source/conf.py, .readthedocs.yaml
- **Verification:** `uv run --frozen pytest tests/test_hygiene.py -q -k planning_vocabulary` — 62 passed, 5 deselected
- **Committed in:** 8571aa3 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — hygiene-gate compliance on new files)
**Impact on plan:** No scope creep; the fix only reworded comment text on the exact files this plan created.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. RTD project import is a separate owner account action tracked elsewhere in the phase (06-CONTEXT.md D-30), not part of this plan's scope; this plan only proves the local build and writes the RTD build definition it will read.

## Next Phase Readiness

- `docs/source/` and `.readthedocs.yaml` are ready for the `Docs (sphinx -W)` CI job (a later plan in this phase wires the workflow) and for RTD project import.
- `release-please-config.json`'s stale `extra-files: ["docs/conf.py"]` entry still needs reconciling — flagged for plan 06-06's kit copy (per 06-CONTEXT.md D-13/06-RESEARCH.md), not touched here.
- No blockers.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*
