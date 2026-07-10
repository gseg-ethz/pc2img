---
phase: 04-code-quality-algorithmic-soundness-review
plan: 02
subsystem: infra
tags: [ruff, pyproject, pypi-metadata, uv, matplotlib, cuda, packaging]

# Dependency graph
requires:
  - phase: 04-01
    provides: "black->ruff swap in the PEP 735 dev group; tests/test_hygiene.py Wave 0 gate (xfail keywords/viz/ruff-clean)"
provides:
  - "Tailored 88-col [tool.ruff] config (E/F/W/I/B/C90/UP/NPY + ERA001, ignore E203) that ruff check runs against"
  - "per-file-ignores exempting the four __init__.py barrels from F401 (protects registration re-exports from 04-04 ruff --fix)"
  - "Collapsed single joblib ~= 1.5 pin (removed duplicate ~= 1.3)"
  - "Optional viz = [matplotlib ~= 3.9] extra; matplotlib no longer a hard dependency"
  - "De-placeholdered pyproject metadata (keywords domain set, enriched classifiers, BSD license classifier, real docs URL)"
  - "CONTRIBUTING.md cuda11/cuda12 selection note + dev-group wording synced black->ruff"
affects: [04-04, 06-publication-hardening]

# Tech tracking
tech-stack:
  added: [matplotlib (optional viz extra)]
  patterns:
    - "ruff config lives in [tool.ruff]; CI enforcement deferred to Phase 6 (D-10 scope fence)"
    - "PyPI-facing metadata (docs URL, license classifier) gated behind owner human-verify checkpoint (T-04-M1)"

key-files:
  created: []
  modified:
    - pyproject.toml
    - CONTRIBUTING.md
    - uv.lock

key-decisions:
  - "Adopted 88-col ruff config (D-11) mirroring sibling rule families minus D/pydocstyle; NOT the sibling 120-col line-length"
  - "matplotlib kept optional (viz extra) because util.py colormap path already guards its absence"
  - "License classifier = BSD License (matches top-level BSD 3-Clause LICENSE / ETH Zurich); docs URL = https://github.com/gseg-ethz/pc2img — both owner-confirmed via orchestrator checkpoint"
  - "CONTRIBUTING.md:74 .github/workflows/ci.yml reference left unchanged — CI/workflow files are deferred to Phase 6 per D-10"

patterns-established:
  - "Single-pass pyproject edit per plan to avoid same-file wave conflicts"
  - "Barrel-exempt per-file-ignores so mechanical ruff --fix (04-04) cannot strip import-time strategy/feature registration re-exports"

requirements-completed: [QUAL-01]

coverage:
  - id: D1
    description: "[tool.ruff] config present (88-col, py312) and ruff check runs against it"
    requirement: "QUAL-01"
    verification:
      - kind: automated
        ref: "python -c tomllib assert 'ruff' in tool + line-length==88 + target-version==py312"
        status: pass
      - kind: automated
        ref: "ruff check src/ (executes against config; exit 1 = findings deferred to 04-04)"
        status: pass
    human_judgment: false
  - id: D2
    description: "joblib pinned once (~= 1.5); viz optional extra declares matplotlib"
    requirement: "QUAL-01"
    verification:
      - kind: automated
        ref: "python -c tomllib assert sum(joblib)==1 and 'viz' in optional-dependencies"
        status: pass
    human_judgment: false
  - id: D3
    description: "Non-placeholder keywords + enriched classifiers (Science/Research, Python 3.12, Typing, Image Processing, GIS)"
    requirement: "QUAL-01"
    verification:
      - kind: automated
        ref: "python -c tomllib assert keywords!=placeholder and any(Science/Research in classifiers)"
        status: pass
    human_judgment: false
  - id: D4
    description: "CONTRIBUTING.md cuda11/cuda12 selection note (names nvidia-smi + mutual exclusivity); dev wording black->ruff"
    requirement: "QUAL-01"
    verification:
      - kind: automated
        ref: "grep nvidia-smi + 'mutually exclusive' present; ! grep dev-group-black passes"
        status: pass
    human_judgment: false
  - id: D5
    description: "Owner-confirmed PyPI-facing metadata: BSD License classifier + real docs URL, no google.com placeholder"
    requirement: "QUAL-01"
    verification:
      - kind: automated
        ref: "python -c tomllib assert License::OSI Approved present and 'google.com' not in docs url; import pc2img OK"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-10
status: complete
---

# Phase 4 Plan 02: pyproject ruff config + QUAL-01 metadata cleanup Summary

**Landed a tailored 88-col `[tool.ruff]` config with barrel-exempt per-file-ignores, collapsed the duplicate joblib pin, moved matplotlib to an optional `viz` extra, de-placeholdered the PyPI metadata (keywords/classifiers/BSD license/docs URL), and added a cuda11-vs-cuda12 selection note to CONTRIBUTING.md.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-10T15:14:32Z
- **Completed:** 2026-07-10T15:17:22Z
- **Tasks:** 3 auto + 1 checkpoint (owner pre-confirmed)
- **Files modified:** 3 (pyproject.toml, CONTRIBUTING.md, uv.lock)

## Accomplishments
- `[tool.ruff]` / `[tool.ruff.lint]` / per-file-ignores / `[tool.ruff.format]` block landed verbatim from 04-RESEARCH.md §Pillar 1 (88-col per D-11, families E/F/W/I/B/C90/UP/NPY, extend-select ERA001, ignore E203). `ruff check src/` now runs against a real config (reports 437 findings, deferred to 04-04 per scope).
- per-file-ignores exempt all four `__init__.py` barrels from F401 so the 04-04 `ruff --fix` sweep cannot strip the import-time registration re-exports.
- Duplicate `joblib ~= 1.3` entry deleted; joblib now pinned once at `~= 1.5` (matches PCHandler).
- `viz = ["matplotlib ~= 3.9"]` optional extra added; matplotlib is no longer a hard dependency (the `util.py` colormap path already guards its absence). `uv sync` re-synced `uv.lock`.
- Placeholder `keywords = ["one","two"]` replaced with the LiDAR/point-cloud/raster/geospatial/DEM/RRIM domain set; classifiers enriched (Development Status, Intended Audience :: Science/Research, Python :: 3.12, Typing :: Typed, Image Processing + GIS topics).
- CONTRIBUTING.md: ~15-line cuda11/cuda12 selection note (nvidia-smi driver check, mutual exclusivity, RAPIDS install-selector link) and dev-group tooling wording synced from `black` to `ruff`.
- Owner-confirmed PyPI-facing fields written: `License :: OSI Approved :: BSD License` (matches top-level BSD 3-Clause LICENSE) and `[project.urls].documentation = "https://github.com/gseg-ethz/pc2img"`, replacing the `google.com` placeholder.

## Task Commits

Each task was committed atomically:

1. **Task 1: ruff config + joblib collapse + viz extra** - `4ecf824` (chore)
2. **Task 2: de-placeholder metadata + cuda note + dev wording** - `a055913` (docs)
3. **Task 3: owner-confirm checkpoint** - pre-confirmed via orchestrator (no separate commit; values written in Task 4)
4. **Task 4: owner-confirmed license classifier + docs URL** - `90fb5c3` (docs)

**Plan metadata:** _(this SUMMARY + STATE/ROADMAP)_ committed separately.

## Files Created/Modified
- `pyproject.toml` - `[tool.ruff]` config block; collapsed joblib pin; `viz` extra; keywords/classifiers de-placeholdered; BSD license classifier + real docs URL
- `CONTRIBUTING.md` - cuda11/cuda12 selection note; dev-group wording black->ruff
- `uv.lock` - re-synced after the viz extra change

## Decisions Made
- Adopted the 88-col ruff config (D-11) with the sibling rule families minus `D`/pydocstyle (that would be docstring churn, out of QUAL-01 hygiene scope; deferred to Phase 6).
- matplotlib kept optional via a `viz` extra rather than promoted to a hard dependency.
- License classifier resolved to `BSD License` and docs URL to the GitHub repo — both owner-confirmed via the orchestrator checkpoint (Task 3), so no autonomous guessing of PyPI-facing values.
- CONTRIBUTING.md:74 `.github/workflows/ci.yml` reference deliberately left unchanged — CI/workflow files are Phase 6 (publication hardening) work per D-10, not an oversight.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. `ruff check src/` exits nonzero (437 findings) as expected — those are the QUAL-01 findings fixed in plan 04-04, not a failure of this plan (which only lands the config).

## User Setup Required
None - the PyPI-facing metadata that required owner input (docs URL A2, license classifier A3) was confirmed through the orchestrator checkpoint and is already written. No further external configuration is needed.

## Threat Model
- **T-04-M1 (Spoofing/Info — PyPI-facing metadata):** mitigated as planned. The docs URL + license classifier were gated behind the owner human-verify checkpoint, and the Task 4 assertion verify rejects the `google.com` placeholder. Owner-confirmed values written.
- **T-04-SC (Tampering — matplotlib viz extra):** accepted per plan. matplotlib is an existing, well-known dependency merely moved to an optional extra, not newly introduced.
- No new security-relevant surface introduced (pc2img remains a no-network, import-only library). No threat flags.

## Next Phase Readiness
- The `[tool.ruff]` config is in place, so plan **04-04** can run `ruff check --fix` + `ruff format` against it; the barrel per-file-ignores protect registration re-exports during that sweep.
- CI enforcement of ruff remains OUT OF SCOPE (D-10) and is carried to Phase 6 along with the `ci.yml` workflow file.

## Self-Check: PASSED

- Files verified present: pyproject.toml, CONTRIBUTING.md, uv.lock, 04-02-SUMMARY.md
- Commits verified in history: 4ecf824, a055913, 90fb5c3

---
*Phase: 04-code-quality-algorithmic-soundness-review*
*Completed: 2026-07-10*
