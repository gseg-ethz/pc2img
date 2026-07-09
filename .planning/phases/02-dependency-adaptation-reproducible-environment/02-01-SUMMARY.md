---
phase: 02-dependency-adaptation-reproducible-environment
plan: 01
subsystem: packaging
tags: [dependencies, pyproject, uv, pep735, rapids]
requires: []
provides:
  - "pyproject.toml with real pchandler/GSEGUtils pins"
  - "PEP 735 dependency-groups for dev/doc"
  - "explicit nvidia index + [tool.uv.sources] RAPIDS pins"
affects:
  - pyproject.toml
tech-stack:
  added: []
  patterns:
    - "compatible-release (~=) pins for sibling deps"
    - "PEP 735 [dependency-groups] for tooling deps"
    - "explicit uv index binding for supply-chain containment"
key-files:
  created: []
  modified:
    - pyproject.toml
decisions:
  - "Kept numpy ~= 2.0 loose, relying on pchandler's transitive <2.4 cap (D-03)"
  - "Routed cuda11/cuda12 extras through pchandler[cudaXX] rather than a bare RAPIDS list (D-04)"
  - "Moved dev/doc to PEP 735 groups; intentional divergence from pchandler (D-08)"
  - "Pinned all ten RAPIDS -cu11/-cu12 names to nvidia index with explicit=true (D-06)"
metrics:
  duration: 1min
  completed: 2026-07-09
status: complete
---

# Phase 2 Plan 1: Dependency Declaration Surface Summary

Re-enabled the two sibling deps (`pchandler ~= 2.1`, `GSEGUtils ~= 0.5`) as real
runtime requirements, routed the GPU extras through `pchandler[cudaXX]`, and
restructured tooling + index config so `pyproject.toml` presents a clean, lockable
TOML shape for the uv lock in Plan 02.

## What Was Built

- **Task 1** — In `[project.dependencies]`, removed the three commented-out stale
  lines (`pchandler[cuda12] ~= 1.0`, the `git+ssh` pchandler line, `GSEGUtils ~= 0.2`)
  and added real compatible-release pins `pchandler ~= 2.1` and `GSEGUtils ~= 0.5`
  (capitalized, D-02). Left `numpy ~= 2.0` untouched (D-03) and the duplicate joblib
  pins in place (QUAL-01/Phase 4 scope). Rewired the `cuda12`/`cuda11` extras from
  their old partial/asymmetric RAPIDS lists to `pchandler[cuda12]` / `pchandler[cuda11]`
  (D-04), inheriting pchandler's maintained GPU set.
- **Task 2** — Relocated `dev` (black/pytest/memory_profiler) and `doc` (sphinx) out
  of `[project.optional-dependencies]` into a new PEP 735 `[dependency-groups]` table
  (D-08) so tooling never lands in wheel metadata. Added `[[tool.uv.index]]` for
  `nvidia` (`https://pypi.nvidia.com`, `explicit = true`) plus `[tool.uv.sources]`
  binding all ten RAPIDS `-cu11`/`-cu12` names to that index (D-06). `explicit = true`
  contains the nvidia index to only the named RAPIDS packages (dependency-confusion
  mitigation, T-02-02); no source points at a local `/scratch` or `third_party/` path
  (D-12, T-02-03).

## Verification

- `python -c "import tomllib; tomllib.load(...)"` — TOML parses cleanly.
- Task 1 automated check: `pchandler ~= 2.1`, `GSEGUtils ~= 0.5`, `numpy ~= 2.0`
  present; `cuda12`/`cuda11` extras equal `['pchandler[cudaXX]']` — passed.
- Task 2 automated check: `[dependency-groups]` has dev/doc, extras no longer expose
  dev/doc, nvidia index declared explicit, all ten RAPIDS names pinned, no local-source
  leak — passed.
- `grep -n 'pchandler ~= 2.1\|GSEGUtils ~= 0.5' pyproject.toml` shows both uncommented.

## Deviations from Plan

None — plan executed exactly as written.

## Scope Note

This plan asserts **declaration shape** only (real requirement strings, extras,
groups, and index/source tables present and parseable). It does NOT prove resolver
behavior. Whether the transitive RAPIDS `[tool.uv.sources]` pins actually bind at
lock time (assumption A2) is proven in **Plan 02**, the real lockability gate.

## Commits

- 7f0b894: build(deps): re-enable sibling deps and route cuda extras through pchandler
- 7c0e740: build(deps): move dev/doc to PEP 735 groups and add explicit nvidia index

## Self-Check: PASSED

- FOUND: pyproject.toml
- FOUND: commit 7f0b894
- FOUND: commit 7c0e740
