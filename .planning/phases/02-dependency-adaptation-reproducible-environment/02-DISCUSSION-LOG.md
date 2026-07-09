# Phase 2: Dependency Adaptation & Reproducible Environment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-09
**Phase:** 2-Dependency Adaptation & Reproducible Environment
**Areas discussed:** Dep source & index, uv reproducibility model, Break-fix verification, Dev symlink workflow

---

## Dep source & index

### Q1 — Where do pchandler + GSEGUtils resolve from for a clean install?

| Option | Description | Selected |
|--------|-------------|----------|
| Public PyPI | Both published to public PyPI; clean install just works; pin with ~= | ✓ |
| Private / ETH index | Published to a private index; URL via [[tool.uv.index]] | |
| git+ssh tag pins | Resolve from repos at pinned tags via git+ssh | |
| Not sure — help me pick | Walk through trade-offs first | |

**User's choice:** Public PyPI

### Q2 — Pin tightness for the two sibling libs

| Option | Description | Selected |
|--------|-------------|----------|
| Compatible-release ~= | `pchandler ~= 2.1`, `GSEGUtils ~= 0.5`; loose in pyproject, exact in lock | ✓ |
| Floor + major cap | `>=2.1,<3`, `>=0.5,<0.6` | |
| Exact == | `== 2.1.*`, `== 0.5.*` | |

**User's choice:** Compatible-release ~=

### Q3 — GPU extras while re-enabling core deps

| Option | Description | Selected |
|--------|-------------|----------|
| Leave extras untouched | Re-enable core deps only; leave cuda extras as-is | |
| Wire pchandler[cuda12] | pc2img cuda12 extra pulls pchandler[cuda12] (+ cuda11 symmetric) | ✓ |
| Strip GPU extras | Remove cuda11/cuda12 extras entirely for now | |

**User's choice:** Wire pchandler[cuda12] (verified pchandler defines both cuda11 + cuda12; wired symmetrically)
**Notes:** GPU *validation* remains deferred to GPU-01 (v2) — this wires + locks the declaration only.

---

## uv reproducibility model

### Q1 — Lockfile form

| Option | Description | Selected |
|--------|-------------|----------|
| uv.lock (project mode) | `uv lock` -> universal uv.lock; `uv sync` recreates env; keep setuptools_scm | ✓ |
| uv pip compile -> requirements | Flat pinned requirements.txt via pip-tools style | |

**User's choice:** uv.lock (project mode)

### Q2 — Lock scope given GPU extras need pypi.nvidia.com

| Option | Description | Selected |
|--------|-------------|----------|
| Core + dev, GPU excluded | Keep GPU extras out of the resolved lock for now | |
| Everything incl. GPU | Configure explicit nvidia index; lock cuda11/cuda12 too | ✓ |

**User's choice:** Everything incl. GPU

### Q3 — Where to document the uv workflow

| Option | Description | Selected |
|--------|-------------|----------|
| CONTRIBUTING.md | Dev-facing bootstrap steps | ✓ |
| README | In the existing README.rst | |
| Match pchandler | Mirror pchandler's docs layout | |

**User's choice:** CONTRIBUTING.md

### Q4 — Where dev/doc tooling deps are declared

| Option | Description | Selected |
|--------|-------------|----------|
| dev + doc -> groups | Both to PEP 735 [dependency-groups]; cuda stays extras | ✓ |
| dev only -> group | Move only dev; leave doc as an extra | |

**User's choice:** dev + doc -> dependency-groups
**Notes:** User initially paused to understand PEP 735 vs extras, then reasoned docs tooling belongs
in the same "repo tooling" category as dev. Accepted intentional divergence from pchandler (which keeps
dev/doc as extras). Deferred idea logged: consider mirroring the grouping into pchandler for consistency.

---

## Break-fix verification

### Q1 — How to prove the single-cloud pipeline runs

| Option | Description | Selected |
|--------|-------------|----------|
| Committed smoke script | scripts/smoke_pipeline.py; durable SC1 evidence; promotable to pytest in Phase 3 | ✓ |
| Reuse/repair a scripts/0X example | Fix an existing example; loads real files + orthographic path | |
| Manual session verification | Run interactively, paste into notes; no committed artifact | |

**User's choice:** Committed smoke script

### Q2 — Smoke data

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic in-code cloud | Deterministic numpy -> PointCloudData; no file; CI-ready | ✓ |
| Small committed fixture | Commit a tiny .ply/.e57; exercises loaders | |
| Point to an external path | Run against an on-disk /scratch cloud | |

**User's choice:** Synthetic in-code cloud

### Q3 — Depth of chasing the three named breaks

| Option | Description | Selected |
|--------|-------------|----------|
| Fix all 3, prove on-path + audit off-path | Runtime-prove FoVTree; audit + targeted-assert to_py4dgeo/Csv-Las | ✓ |
| Full runtime proof of all 3 | Execute + assert every break this phase (needs fixtures) | |
| Smoke-path only, defer rest | Only FoVTree; defer the other two entirely to Phase 5 | |

**User's choice:** Fix all 3, prove on-path + audit off-path

---

## Dev symlink workflow

### Q1 — Fate of the third_party/ editable symlinks

| Option | Description | Selected |
|--------|-------------|----------|
| PyPI default, local override opt-in | PyPI + uv.lock canonical; local-editable override opt-in/non-committed | ✓ |
| Drop symlinks entirely | Remove third_party/; all dev via PyPI-locked env | |
| Commit [tool.uv.sources] to local paths | Commit local-path sources / workspace | |

**User's choice:** PyPI default, local override opt-in
**Notes:** User clarified the symlinks exist primarily so the agent can **investigate** the sibling-lib
source, not as the dev-install mechanism. Both sibling repos are owner-controlled; edits to them are to
be **discussed first** (human-approval constraint) rather than done unilaterally.

### Q2 — numpy bound

| Option | Description | Selected |
|--------|-------------|----------|
| Match pchandler: >=2.0,<2.4 | Explicit identical window | |
| Keep loose ~= 2.0, let pchandler cap | Rely on pchandler's transitive <2.4 | ✓ |
| Floor only: >=2.0 | No upper cap | |

**User's choice:** Keep loose ~= 2.0, let pchandler cap
**Notes:** Established that the DEP-03 "numpy conflict" (old `~= 1.24`) is already resolved on
develop-gsd (now `~= 2.0`), so this is a bound-clarity choice, not a conflict fix.

---

## Claude's Discretion

- Exact smoke-script filename/location; synthetic cloud size/shape/seed.
- Precise `pyproject.toml` ordering and how the nvidia index + cuda package sources are expressed in `[tool.uv]`.
- Exact form of the off-path `to_py4dgeo` / Csv-Las targeted assertions.
- Scoped fallback if the nvidia index / RAPIDS resolution proves impractical offline (flag to owner).

## Deferred Ideas

- `black -> ruff` + lint-in-CI (Phase 3/4) — filed as pending todo `2026-07-09-move-to-ruff-lint-ci.md`.
- GPU-01 (v2) — actual GPU-path validation of the cuda extras.
- Mirror PEP 735 dev/doc grouping into pchandler for cross-library consistency (owner-controlled repo; needs approval).
