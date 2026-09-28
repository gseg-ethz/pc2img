---
phase: 06-publication-hardening-downstream-migration-record
plan: 03
subsystem: packaging
tags: [readme, citation, pypi, twine, metadata, rrim]

# Dependency graph
requires:
  - phase: 06-02
    provides: green lint/pre-commit gate on the whole shipped tree (whole-tree planning-vocabulary hygiene, ruff clean)
provides:
  - Real README.rst (PyPI long description) with install/quickstart/features/RRIM/docs sections
  - CITATION.cff with single-author citation metadata
  - Local proof that the built sdist+wheel pass `twine check`
affects: [06-04, "Phase 6 first promotion to main", "Phase 7 (0.11.0 release PyPI publish)"]

# Actuals (#2632)
actuals:
  tokens: 1756
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: [README.rst as the setuptools dynamic readme long-description, twine-check proof loop for metadata changes]

key-files:
  created:
    - CITATION.cff
  modified:
    - README.rst

key-decisions:
  - "README quickstart uses the actual PointCloudImageGenerator constructor keyword names (img_res, proj, interp, lazy_disk_cache_config) taken from src/pc2img/core.py, not guessed names"
  - "CITATION.cff modelled on PCHandler's shape but with a single author (Nicholas Meyer) per D-14 — authors intentionally unchanged, no Jon Allemand entry"

patterns-established:
  - "Metadata changes (README/CITATION) are proven locally via `uv build && uvx twine check dist/*` before commit, not just eyeballed"

requirements-completed: [CICD-02]

coverage:
  - id: D1
    description: "README.rst replaced with real install/quickstart/features/RRIM/docs content, proven as a working PyPI long description"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "uv build && uvx twine check dist/* (PASSED for sdist and wheel)"
        status: pass
      - kind: other
        ref: "python metadata-extraction check: 'pip install pc2img' present, '##Hello' absent"
        status: pass
      - kind: other
        ref: "planning-vocabulary regex scan on README.rst"
        status: pass
    human_judgment: false
  - id: D2
    description: "CITATION.cff added, modelled on PCHandler's, single author, BSD-3-Clause, placeholder Zenodo DOI"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "PyYAML parse + field assertions (cff-version, title, authors, license, repository-code)"
        status: pass
      - kind: other
        ref: "grep acceptance criteria: family-names: Meyer x2, Allemand x0, zenodo >=1"
        status: pass
    human_judgment: false

# Metrics
duration: 20min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 3: README.rst + CITATION.cff Summary

**Replaced the placeholder `##Hello` PyPI long description with real install/quickstart/feature/RRIM content and added a single-author CITATION.cff, both proven against a locally built sdist+wheel via `twine check`.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2 completed
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- README.rst now carries real sections: title/description, installation (PyPI, `viz`/`cuda11`/`cuda12`/`rrim` extras), a runnable quickstart mirroring `scripts/smoke_pipeline.py`, a feature-name-grammar overview (range, scalar_field, gradient, hillshade, normalized/clip, multigrad, RRIM family), the RRIM patent-expiry notice, and documentation/contributing/changelog/license links.
- `uv build && uvx twine check dist/*` PASSED for both the sdist and wheel, confirming the reStructuredText renders cleanly as the PyPI long description.
- Added `CITATION.cff` modelled on PCHandler's file shape (cff-version 1.2.0, `authors`, `repository-code`, `url`, `license`, `message`, `preferred-citation` with a placeholder Zenodo DOI), with exactly one author (Nicholas Meyer) as required by D-14 — authors intentionally unchanged from `pyproject.toml`.

## Task Commits

Each task was committed atomically:

1. **Task 1: README.rst with install/quickstart/features/RRIM/CUDA, proven through uv build + twine check** - `1556e2c` (docs)
2. **Task 2: CITATION.cff modelled on PCHandler's, single author** - `f7e565c` (docs)

**Plan metadata:** (this commit)

## Files Created/Modified

- `README.rst` - Real PyPI long description: install, quickstart, feature overview, RRIM notice, docs/contributing/license
- `CITATION.cff` - Citation metadata, single author, BSD-3-Clause, placeholder Zenodo DOI

## Decisions Made

- Quickstart constructor keyword names (`img_res`, `proj`, `interp`, `lazy_disk_cache_config`) were taken verbatim from `src/pc2img/core.py`'s `__init__` signature rather than guessed, satisfying the task's acceptance criterion.
- CITATION.cff's `preferred-citation` follows PCHandler's exact shape (type software, same author list, placeholder DOI + notes) but drops the second author, matching D-14's "authors unchanged" constraint.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- README.rst and CITATION.cff are real, planning-vocabulary-clean, and proven against a locally built package. Ready for `06-04` and the eventual first filtered promotion to `main`.
- `dist/*.tar.gz` and `dist/*.whl` were local proof artifacts only, not committed, and were removed after verification.
- Whole-tree gates re-verified clean after these two files landed: `uv run --frozen pytest -q` (254 passed, including the hygiene gate) and `uvx pre-commit run --all-files` (ruff check/format, hygiene hooks all Passed).

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*

## Self-Check: PASSED

- FOUND: README.rst (contains "pip install pc2img", no "##Hello")
- FOUND: CITATION.cff (cff-version 1.2.0, single author Meyer)
- FOUND commit 1556e2c in git log
- FOUND commit f7e565c in git log
- Re-ran plan-level `<verification>`: `uv build && uvx twine check dist/*` PASSED x2; CITATION.cff parses with asserted fields — both pass
- `must_haves.truths` (from plan frontmatter) re-checked: README has real content, renders under twine check (yes); CITATION.cff exists with single author, pc2img repo URL, BSD-3-Clause, placeholder Zenodo DOI (yes); no planning vocabulary in either file (yes, `vocab-clean` printed)
