# Phase 2: Dependency Adaptation & Reproducible Environment - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Make pc2img import **and run** correctly against **PCHandler 2.x + the current
GSEGUtils release**, re-enable and pin both in `pyproject.toml` (resolving the
numpy pin question), and stand up a **reproducible `uv` workflow** with a
committed lockfile.

**Verified starting state (2026-07-09):**
- `develop-gsd` is already **import-clean** against `pchandler==2.1.0.post2` and
  `gsegutils==0.5.2.post2` — every pchandler/GSEGUtils import in the tree
  resolves on the new paths. So this phase is **not** a from-scratch import
  migration; it is the deeper layer: semantic/runtime break resolution +
  packaging + reproducibility.
- Both sibling libs are currently **editable-installed from local `/scratch`
  paths** (`third_party/pchandler -> /scratch/41_pchandler`,
  `third_party/gsegutils -> /scratch/30_GSEGUtils`); `pyproject.toml` **comments
  out** the two core deps, so a clean `pip/uv install` has **no declared
  resolution path** yet.
- pc2img's numpy pin is already `numpy ~= 2.0` on `develop-gsd` (the stale
  `~= 1.24` in DEP-03's text is gone); pchandler pins `numpy >= 2.0, < 2.4`, so
  they already intersect cleanly.
- Package-name casing gotcha: distribution is `gsegutils` (lowercase, what
  uv/pip installs) but the importable package is `GSEGUtils` (capitalized).
  pc2img imports use the capitalized form correctly.

**In scope:** re-enabling + pinning `pchandler`/`GSEGUtils` in `pyproject.toml`,
GPU-extra wiring, the `uv.lock` reproducible workflow + CONTRIBUTING docs, PEP
735 dev/doc grouping, resolving/verifying the three named semantic breaks, and a
committed single-cloud smoke script.
**Out of scope:** GPU-path *validation* (GPU-01, v2), the `black -> ruff` +
lint-in-CI swap (Phase 3/4 — see Deferred), the algorithmic-soundness review
(Phase 4), exhaustive module test coverage incl. loaders (Phase 5), publication
CI/CD + branch protection (Phase 6). WIP `PerspectiveProjection` and
`OrthographicProjection` (BUG-01) are not exercised by this phase's smoke path.
</domain>

<decisions>
## Implementation Decisions

### Dependency source & pinning (DEP-03)
- **D-01:** `pchandler` and `GSEGUtils` resolve from **public PyPI**. A clean
  `uv sync` / `pip install pc2img` fetches both from pypi.org — no index config,
  no git URLs, no `third_party/` symlinks required for the default install.
- **D-02:** Pin with **compatible-release** specifiers in `pyproject.toml`:
  `pchandler ~= 2.1`, `GSEGUtils ~= 0.5`. Loose in `pyproject`, exact in the
  committed lockfile. Matches pchandler's own `GSEGUtils ~= 0.5` declaration and
  pc2img's existing `~=` convention. Keep the requirement name **capitalized**
  (`GSEGUtils`) as pchandler does (pip normalizes case for resolution regardless).
- **D-03:** **numpy stays loose: `numpy ~= 2.0`.** pc2img declares numpy as a
  direct dep (it uses `NDArray` heavily) but relies on pchandler's transitive
  `< 2.4` to cap the resolution (effective `>=2.0,<2.4`). Rationale: avoids
  having to track pchandler's numpy-ceiling bumps; pchandler is a hard dep so the
  intersection always caps anyway. The DEP-03 "numpy conflict" (old `~= 1.24`) is
  already resolved on `develop-gsd`.
- **D-04:** **Wire the GPU extras to pchandler.** pc2img's `cuda12` extra pulls
  `pchandler[cuda12]` and `cuda11` pulls `pchandler[cuda11]` (symmetric).
  pchandler's cuda extras also bring `geopandas`, `cuspatial`, `cuproj`,
  `dask-cudf` — filling gaps pc2img's current extras had. This wires the
  *declaration* only; actual GPU-path **validation stays deferred to GPU-01
  (v2)**.

### uv reproducibility (DEP-04)
- **D-05:** **Native `uv.lock` project workflow.** `uv lock` produces a
  universal (cross-platform) `uv.lock`, committed to the repo; `uv sync`
  recreates the exact env. **Keep the `setuptools_scm` build backend** — uv
  locks/manages the project without changing how the package builds.
- **D-06:** **Lock everything, including GPU.** Configure an explicit nvidia
  index so the `cuda11`/`cuda12` extras also resolve into the universal lock:
  ```toml
  [[tool.uv.index]]
  name = "nvidia"
  url = "https://pypi.nvidia.com"
  explicit = true
  ```
  Fuller reproducibility posture (the whole declared surface is locked). Note:
  this makes `uv lock` heavier and pulls the RAPIDS 25.4.* resolution + nvidia
  index into Phase 2 — but only *resolution*, not GPU validation (still GPU-01).
- **D-07:** **Document the uv workflow in `CONTRIBUTING.md`** (dev-facing
  bootstrap: `uv sync`, `uv run pytest`, `uv lock` after dep changes). Separates
  dev workflow from the user-facing `README.rst`.
- **D-08:** **Move `dev` + `doc` tooling deps to PEP 735 `[dependency-groups]`;
  keep `cuda11`/`cuda12` as `[project.optional-dependencies]` extras.** The split
  is *repo tooling* (pytest/black/memory_profiler, sphinx — never shipped in wheel
  metadata) vs *package capabilities* (GPU acceleration — a real feature a
  consumer opts into via `pip install pc2img[cuda12]`). `uv sync` installs the
  `dev` group by default; `uv sync --group doc` for docs. **Intentional
  divergence from pchandler** (which keeps dev/doc as extras) — accepted for
  correct modeling; see Deferred re: mirroring it back into pchandler.

### Semantic-break resolution & verification (DEP-01, DEP-02)
- **D-09:** **Prove SC1 with a committed smoke script** (e.g.
  `scripts/smoke_pipeline.py`) that runs the single-cloud
  project → interpolate → feature pipeline end-to-end and asserts completion +
  basic output sanity. It is the durable SC1 evidence, runnable via `uv run`, and
  is **promotable to a pytest smoke test in Phase 3**.
- **D-10:** **Run the smoke on a synthetic, in-code point cloud** (deterministic
  numpy arrays → `PointCloudData`), no external file — fully reproducible and
  CI-ready. Use the **spherical** projection + Delaunay interpolation + a simple
  feature (e.g. `range`); this deliberately avoids the orthographic path
  (BUG-01, Phase 5) and the WIP `PerspectiveProjection` (Phase 4/5).
- **D-11:** **Fix all three named breaks at the code level; verify
  proportionately.** Runtime-prove the **FoVTree 2D `"<r>-<c>"` identifier**
  behavior on the smoke path (spherical projection exercises `FoV`/`FoVTree`).
  For the two breaks **off** the single-cloud happy path — **world-frame
  `to_py4dgeo`** (BC-PCH-007) and **Csv/Las load behavior** — audit the call
  sites, fix if broken, and add a small targeted assertion/check documenting the
  fix, **without** building full loader fixtures. Exhaustive loader/orchestration
  coverage is **Phase 5** (TEST-05/06).

### Dev workflow / third_party symlinks (DEP-01..04 supporting)
- **D-12:** **PyPI + `uv.lock` is the canonical resolution** (satisfies SC3:
  clean install with no symlinks). The `third_party/` editable symlinks stay as
  **gitignored source-investigation aids** — their purpose is to let the agent
  *read* the live pchandler/GSEGUtils source while adapting, not to serve as the
  dev-install mechanism. A local-editable override
  (`uv pip install -e /scratch/41_pchandler ...`) remains an opt-in, non-committed
  dev step. Do **not** commit `[tool.uv.sources]` pointing at local paths.
- **D-13:** Both sibling repos are **owner-controlled**. If adapting pc2img
  surfaces a change that is *strongly advisable* in `pchandler`/`GSEGUtils`,
  **raise and discuss it with the owner first** (standing human-approval
  constraint) rather than editing those repos unilaterally.

### Claude's Discretion
- Exact smoke-script filename/location and the synthetic cloud's size/shape/seed.
- Precise `pyproject.toml` layout ordering and how the nvidia index + cuda
  package sources are expressed in `[tool.uv]` (as long as D-06 holds).
- Exact form of the off-path `to_py4dgeo` / Csv-Las targeted assertions (D-11).
- Whether GPU-extra resolution issues (if the nvidia index misbehaves offline)
  warrant a scoped fallback — flag to the owner if D-06 proves impractical.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone planning
- `.planning/ROADMAP.md` §"Phase 2: Dependency Adaptation & Reproducible
  Environment" — goal + 4 success criteria this phase must satisfy.
- `.planning/REQUIREMENTS.md` §"Dependency Adaptation" — DEP-01, DEP-02, DEP-03,
  DEP-04 (+ the numpy-conflict note).
- `.planning/PROJECT.md` §Context — "Dependency reality (verified 2026-07-08)"
  paragraph (semantic breaks, numpy pin, casing gotcha) and §Constraints.

### Sibling-library migration records (the semantic breaks live here)
- `/scratch/41_pchandler/MIGRATION-v1.0.md` — structured breaking-change IDs
  `BC-PCH-001..013`. Key hits: **BC-PCH-008** (FoVTree 2D `"<r>-<c>"`
  identifiers), **BC-PCH-007** (world-frame `to_py4dgeo`), **BC-PCH-001** (numpy
  `>=2.0,<2.4`), plus Csv/Las load-behavior "should-review" changes.
- `/scratch/30_GSEGUtils/MIGRATION-v1.0.md` — companion GSEGUtils migration
  record.
- `/scratch/41_pchandler/pyproject.toml` — authoritative dep declarations
  (`GSEGUtils ~= 0.5`, `numpy >= 2.0,<2.4`, `cuda11`/`cuda12` extras) that
  pc2img's pins mirror.

### Codebase maps (context for the integration surface)
- `.planning/codebase/INTEGRATIONS.md` §"First-Party Dependency Linkage" — the
  commented-out deps + `third_party/` symlink arrangement, GSEGUtils disk-cache
  usage sites.
- `.planning/codebase/STACK.md` — full dependency inventory + versions.

_No external ADRs beyond the sibling migration docs — dep/env decisions are
captured in this file._
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PointCloudImageGenerator` (`src/pc2img/core.py`) — the single-cloud pipeline
  entry point the smoke script drives.
- `scripts/` already contains example drivers (`04_generate_overview.py`, etc.)
  that show the `load_* -> generate(...)` shape; the new smoke script models the
  synthetic-cloud analogue of these.
- `.venv` (uv, Python 3.12.13) already exists with both deps editable-installed —
  the working baseline to convert into a locked `uv.lock` env.

### Established Patterns
- pchandler import paths in use (all resolve today): `from pchandler import
  PointCloudData`, `from pchandler.geometry.spherical import FoV, FoVTree`,
  `from pchandler.geometry.coordinates import rhv2xyz`, `from pchandler.filters
  import FoVFilter, BoxFilter`; GSEGUtils: `from GSEGUtils.lazy_disk_cache /
  config / base_types import ...`.
- pc2img already floats deps via `~=` compatible-release specifiers — D-02
  extends the same convention to the two sibling libs.

### Integration Points
- FoVTree identifier break (BC-PCH-008) surfaces where the spherical projection /
  tiling uses `FoVTree` + `split_pc_with_fov_tree` — this is the on-smoke-path
  break (D-11).
- `to_py4dgeo` (BC-PCH-007) and Csv/Las loaders are the off-path call sites to
  audit (D-11).
- `src/pc2img/strategies/projection.py:12` imports a **private** pchandler symbol
  (`_TransformArray`) at module scope — fragility already tracked by the Phase 4
  pending todo (`guard-transformarray-module-import`); not this phase's job but
  relevant when touching projection imports.
</code_context>

<specifics>
## Specific Ideas

- Lock/pin exactly to what is on PyPI and matches the on-disk `/scratch` sources
  (`pchandler 2.1.x`, `gsegutils 0.5.x`).
- Smoke script: spherical → Delaunay → `range` on a small deterministic synthetic
  cloud; assert output shape/finite-ness, print `OK`.
- Model the "tooling vs capability" dep split cleanly: PEP 735 groups for
  `dev`/`doc`, extras for `cuda11`/`cuda12`.
</specifics>

<deferred>
## Deferred Ideas

- **`black -> ruff` + lint-in-CI** (owner-raised 2026-07-09) — move
  linting/formatting from `black` to `ruff` and run it in CI. Straddles **Phase 3**
  (CICD-01 — wiring lint into CI) and **Phase 4** (QUAL-01 — the tooling swap).
  Consistent with pchandler (`ruff ~= 0.15`). Sequencing note: doing the swap
  before/at Phase 3 avoids adding `black`-in-CI only to replace it in Phase 4.
  Filed as a pending todo (`2026-07-09-move-to-ruff-lint-ci.md`, `resolves_phase: 3`).
- **GPU-01 (v2)** — actual validation/testing of the `cuda11`/`cuda12` extras
  against current RAPIDS. Phase 2 wires + locks the GPU deps but does not verify
  the GPU code path runs.
- **Mirror PEP 735 dev/doc grouping into pchandler** — for cross-library
  consistency, consider moving pchandler's `dev`/`doc` deps to
  `[dependency-groups]` too. Separate owner-controlled repo → requires human
  approval; not a pc2img-Phase-2 action.

### Reviewed Todos (not folded)
- `guard-transformarray-module-import` (`resolves_phase: 4`) — reviewed; stays in
  Phase 4. It concerns projection-module import fragility, not dependency
  declaration/reproducibility, so it is not folded into Phase 2.

</deferred>

---

*Phase: 2-Dependency Adaptation & Reproducible Environment*
*Context gathered: 2026-07-09*
