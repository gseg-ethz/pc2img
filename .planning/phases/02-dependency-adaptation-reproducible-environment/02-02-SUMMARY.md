---
phase: 02-dependency-adaptation-reproducible-environment
plan: 02
subsystem: packaging
tags: [dependencies, uv, lockfile, reproducibility, rapids, contributing]
requires:
  - "pyproject.toml with real pchandler/GSEGUtils pins (Plan 01)"
  - "explicit nvidia index + [tool.uv.sources] RAPIDS pins (Plan 01)"
provides:
  - "committed universal uv.lock (hash-pinned, 181 packages)"
  - "[tool.uv] conflicts declaring cuda11/cuda12 mutually exclusive"
  - "CONTRIBUTING.md documenting the uv dev bootstrap workflow"
  - "SC3 clean-room install proof (no third_party symlinks)"
affects:
  - uv.lock
  - pyproject.toml
  - CONTRIBUTING.md
tech-stack:
  added: []
  patterns:
    - "universal uv.lock via native uv project workflow (D-05)"
    - "[tool.uv] conflicts for mutually exclusive GPU extras"
    - "isolated clean-room (temp copy, third_party excluded) as SC3 proof"
key-files:
  created:
    - uv.lock
    - CONTRIBUTING.md
  modified:
    - pyproject.toml
decisions:
  - "Added [tool.uv] conflicts for cuda11/cuda12 (owner-approved option a) — keeps both GPU stacks hash-pinned; the cuXX pick defers to install time"
metrics:
  duration: 10min
  completed: 2026-07-09
status: complete
---

# Phase 2 Plan 2: Reproducible Environment (uv.lock + CONTRIBUTING) Summary

Turned Plan 01's lockable pyproject surface into an actually reproducible
environment: generated and committed a universal, hash-pinned `uv.lock` (181
packages, both GPU variants), proved a genuinely isolated clean-room install
resolves pc2img from PyPI without any `third_party/` symlinks (SC3), and documented
the uv dev bootstrap in a new `CONTRIBUTING.md` (SC4/DEP-04).

## What Was Built

- **Task 1** — Generated the universal `uv.lock` via `uv lock`, then `uv sync` to
  install pc2img editable plus runtime + `dev` group. Confirmed the resolution:
  `pchandler 2.1.0`, `gsegutils 0.5.2`, `numpy 2.0.2` (within `>=2.0,<2.4`),
  `pc2img 2.0.0a5.post59`. Exact installed versions are **asserted** via
  `importlib.metadata.version(...)`, not just grepped. `uv lock --check` reports the
  lock up to date with `pyproject.toml`.
- **Task 2** — Proved SC3 in a **genuinely isolated** clean-room: rsync'd the repo
  into a temp dir excluding `third_party/` and `.venv` (keeping `.git` for
  setuptools_scm), asserted `test ! -e third_party`, ran `uv sync --frozen
  --no-editable` (passed first try, no fallback), and imported `pc2img`,
  `pchandler`, `GSEGUtils` with versions asserted from PyPI. The committed `uv.lock`
  passed the negative-source check (no `/scratch`/`third_party` strings, no non-self
  local/editable source). The developer's real `third_party/` symlinks were left
  untouched (only a temp copy was used). No file changes — this task is a proof
  against the committed lock.
- **Task 3** — Authored a new `CONTRIBUTING.md` documenting `uv sync`,
  `uv sync --group doc`, `uv run` (smoke + pytest), and `uv lock` /
  `uv lock --check` after dependency edits. Notes the `gsegutils`/`GSEGUtils` casing
  gotcha, the gitignored-`third_party/` role (D-12), and the install-time cuda11 vs
  cuda12 selection. Kept strictly dev-workflow-scoped (user-facing docs stay in
  `README.rst`).

## Verification

- Task 1: `uv lock --check` up to date; `pchandler`/`gsegutils` entries present;
  `uv run python -c "import pc2img"` succeeds; versions asserted (pchandler `2.1.*`,
  gsegutils `0.5.*`, numpy `>=2.0,<2.4`) — **passed**.
- Task 2: negative-source check PASS; `third_party` absent in clean-room PASS;
  `uv sync --frozen --no-editable` PASS (no fallback); clean-room import of all three
  packages with PyPI versions asserted (2.1.0 / 0.5.2 / 2.0.2) — **passed**.
- Task 3: `CONTRIBUTING.md` contains `uv sync`, `uv lock`, `uv run`,
  `scripts/smoke_pipeline.py`, plus casing + third_party notes — **passed**.

## Deviations from Plan

### Owner-decision checkpoint (GPU-extra resolution — plan's documented STOP path)

**1. [Rule 4 - Architectural/config] `uv lock` failed on mutually exclusive cuda extras**
- **Found during:** Task 1 (initial `uv lock`).
- **Issue:** The universal lock could not co-satisfy `pc2img[cuda11]` and
  `pc2img[cuda12]`: `cudf-cu12` requires `cuda-python>=12.6.2,<13` while `cudf-cu11`
  requires `cuda-python>=11.8.5,<12` (pulled transitively via `pchandler[cudaXX]`),
  so a single resolution environment is unsatisfiable. This is **not** either
  failure mode the plan's fallback anticipated: the nvidia index **was reachable**
  (all RAPIDS `25.4.*` wheels built) and the `[tool.uv.sources]` transitive pins
  **did bind** (assumption A2 held). Per the plan's explicit "STOP and surface to the
  owner" instruction, I paused and presented three options.
- **Resolution:** Owner chose **option (a)** — add a `[tool.uv] conflicts` table
  declaring `cuda11`/`cuda12` mutually exclusive. uv then resolves each GPU stack in
  a separate fork, keeping **both** variants fully hash-pinned in the universal lock
  (satisfies D-06). The cuda11-vs-cuda12 pick correctly defers to install time
  (`pip install pc2img[cuda12]` vs `[cuda11]`), driven by the user's NVIDIA driver.
- **Files modified:** `pyproject.toml` (added `[tool.uv] conflicts`), committed
  together with `uv.lock`.
- **Commit:** d09ba42

The broader "how should users choose cuda11 vs cuda12" guidance is tracked as a
pending todo (`.planning/todos/pending/2026-07-09-document-cuda11-vs-cuda12-selection-guidance.md`)
and intentionally **not** expanded into this plan.

## Notes

- **A2 (transitive RAPIDS source binding) is confirmed GREEN** — the real
  lockability gate this plan existed to prove. The `[tool.uv.sources]` nvidia pins on
  transitive-from-pchandler names bound without needing the fallback (naming RAPIDS
  packages directly in pc2img's extras).
- **A1 confirmed** — clean PyPI resolution lands `pchandler 2.1.0` / `gsegutils
  0.5.2` where the local editable installs were `.post2`; equivalent, exact versions
  now recorded in the lock.
- A `[tool.uv]` table now sits in `pyproject.toml` on top of Plan 01's surface;
  Plan 01's index/source tables are unchanged.

## Commits

- d09ba42: build(deps): generate universal uv.lock with conflicting cuda extras
- 4046a47: docs(contributing): document uv dev bootstrap workflow

(Task 2 produced no commit — it is a clean-room proof against the committed lock,
with no file changes.)

## Self-Check: PASSED

- FOUND: uv.lock
- FOUND: CONTRIBUTING.md
- FOUND: pyproject.toml
- FOUND: 02-02-SUMMARY.md
- FOUND: commit d09ba42
- FOUND: commit 4046a47
