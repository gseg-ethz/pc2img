# Phase 3: Test & CI Foundation - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up the **test & CI foundation**: scope pytest collection to `tests/`,
establish **coverage measurement with a recorded baseline**, and add a
**lightweight CI workflow** that runs the suite on pull requests as an early
safety net — *before* the heavy quality/soundness (Phase 4) and bug-fix/coverage
(Phase 5) work that follows.

**Requirements:** TEST-01 (scope pytest to `tests/`), TEST-02 (coverage +
recorded baseline), CICD-01 (lightweight PR CI).

**Verified starting state (2026-07-09, measured by running it):**
- `pytest` from the repo root collects **1140 tests** across
  `third_party/pchandler` + `third_party/gsegutils` with **7 collection errors**
  (duplicate module basenames like `test_util.py` / `test_lazy_disk_cache.py`
  colliding across the two sibling repos, plus their `scripts/`). This is exactly
  the TEST-01 target. `third_party/` is a **gitignored symlink** to the sibling
  checkouts, so it is absent on a fresh CI checkout — but present for local dev.
- Scoped to `tests/`, the pc2img suite is **substantially red**: two modules do
  not even import — `tests/test_disk_backed_image_store.py` (imports the
  pre-refactor `pc2img.image_generation.ImageGeneratorFromPCD`) and
  `tests/test_lazy_disk_cache.py` (imports the deleted `_old.v1` package) — and of
  the 26 tests that do collect, **11 fail / 15 pass**. One failure,
  `test_point_cloud_image_generator.py::test_constructor_normalizes_omitted_lazy_disk_cache_config`,
  is the already-known deferred null-cache-config coercion bug.

**In scope:** pytest collection scoping (`testpaths`/config), disposition of the
broken/failing existing tests to reach a **green** baseline, coverage tooling +
recorded baseline + a `--cov-fail-under` regression ratchet, and a single-job
GitHub Actions CI workflow (uv-based) running on PRs + mainline pushes.

**Out of scope (deferred):** the `black → ruff` swap and lint/pyright-in-CI
(Phase 4/QUAL-01); authoring real coverage for the untested core modules —
projection/interp/features/orchestration/util (TEST-03..06, Phase 5); actually
*fixing* the failing tests / known bugs (Phase 5, with proving tests, informed by
the Phase 4 soundness review); GPU tests + self-hosted GPU runner infra
(GPU-01, v2); codecov + branch protection + publication CI/CD (Phase 6).
</domain>

<decisions>
## Implementation Decisions

### Green-CI bar & broken-test disposition (TEST-01 support)
- **D-01:** **Green-by-triage.** Phase 3's bar is a **green** suite so that
  "green" durably means "no new regressions." We reach green by dispositioning
  the existing red — *not* by fixing bugs (that is Phase 5) and *not* by shipping
  a red baseline (a red-from-day-one net hides regressions).
- **D-02:** **Delete the two import-broken pre-refactor modules outright** —
  `tests/test_disk_backed_image_store.py` and `tests/test_lazy_disk_cache.py`.
  Both import symbols that no longer exist and test the pre-refactor architecture;
  `lazy_disk_cache` now lives in GSEGUtils (with its own tests). Rely on git
  history. Real store/cache coverage, if wanted, is Phase 5.
- **D-03:** **Park the failing-but-current tests as tracked debt via
  `@pytest.mark.xfail(reason=..., strict=False)`** (the 11 `test_disk_backed_image_data`
  failures + the null-cache-config failure). Rationale for xfail over skip: the
  tests still **execute** (so they contribute partial coverage) and flip to
  **XPASS automatically** once Phase 5 fixes the underlying code — nothing is
  silently lost. Each xfail `reason` MUST name the failure and point at Phase 5.
- **D-04:** **The xfail'd tests are candidate BUG-05 / Phase-5 inputs but are NOT
  classified in Phase 3.** Whether each is a *stale test expectation* vs a *real
  bug* is decided in Phase 4 (soundness review) / Phase 5 (bug fixes). Phase 3
  only parks them with a tracking reason; the null-cache-config one already has a
  matching pending todo (see Reviewed Todos).

### Coverage measurement & baseline (TEST-02)
- **D-05:** **Measure the whole package: `--cov=pc2img` with branch coverage.**
  An honest, low floor that includes every untested Phase 5 module, so Phase 5's
  coverage growth is visible and the baseline is a meaningful milestone signal.
  (Scoping coverage to only tested modules would flatter the number and hide the
  gap — rejected.)
- **D-06:** **The baseline is a regression guard, not just a note:** record the
  measured percentage durably (coverage note / CONTRIBUTING) **and** set
  `--cov-fail-under` at the floor so CI fails on a coverage drop. Set the
  threshold a **hair below** the measured baseline for headroom against coverage
  volatility (xfail'd tests execute up to their failure point, contributing
  partial/variable coverage). Phase 5 ratchets the floor upward as it adds tests.
- **D-07:** **Tooling matches pchandler:** `pytest-cov` (`~=5.0`) + `coverage`
  (`~=7.0`), added to the PEP 735 `dev` dependency-group (which currently holds
  only `black`, `pytest`, `memory_profiler`). Report `term-missing` locally + an
  `xml` report in CI (Claude's discretion on exact report wiring). **Codecov is
  deferred to Phase 6** (needs a token/account; publication-hardening scope).

### Ruff / lint timing
- **D-08:** **Keep the `black → ruff` swap in Phase 4.** Phase 3 CI is
  **tests + coverage only — no lint step, no pyright step.** Both the swap
  (QUAL-01) *and* the lint-in-CI wiring land together in Phase 4, so CI never
  gains a `black --check` step only to have Phase 4 rip it out. Consequence: the
  `move-to-ruff-lint-ci` pending todo (`resolves_phase: 3`) should be
  **retargeted to Phase 4** — its CI half moved with its swap half.

### CI shape & install path (CICD-01)
- **D-09:** **Install via `uv sync --frozen`** (using `astral-sh/setup-uv`)
  against the committed universal `uv.lock`. This exercises the Phase 2 lockfile
  as part of the safety net (a lock-drift regression fails CI), is fast with the
  uv cache, and is consistent with pc2img's uv-native workflow (D-05/D-12 of
  Phase 2). **Intentional divergence** from pchandler's `pip install .[dev]` CI;
  reconciling the two CI templates is a Phase 6 concern.
- **D-10:** **Triggers: `pull_request` + `push` to `develop-gsd` and `main`.**
  Matches pchandler's `ci.yml`; covers direct pushes to the integration mainline,
  not just PRs. Cheap for a single CPU job.
- **D-11:** **Single job, CPU-only, GitHub-hosted `ubuntu-latest`, Python 3.12
  only** (no matrix — `requires-python` pins `~=3.12,<3.13`). The job runs the
  scoped pytest with coverage + the fail-under gate and reports pass/fail.

### GPU testing / runners
- **D-12:** **No GPU testing or self-hosted runner setup in Phase 3.** pc2img has
  no GPU-specific code of its own (GPU paths are exercised transitively through
  pchandler; the `cuda11/cuda12` extras just pull `pchandler[cudaXX]`), and Phase 2
  already deferred GPU-path validation to **GPU-01 (v2)**. Phase 3 CI is CPU-only.
- **D-13 (forward direction, deferred):** **When GPU testing does land (GPU-01,
  v2), reuse pchandler's existing shared self-hosted GPU runner pool + labels +
  digest-pinned GHCR RAPIDS image** rather than standing up a dedicated pc2img
  runner/image. Captured now to steer v2; no action this phase.

### Claude's Discretion
- Exact pytest scoping mechanism to satisfy TEST-01: `testpaths = ["tests"]` in
  `[tool.pytest.ini_options]`, plus whatever is needed for a clean local run with
  the `third_party/` symlinks present (e.g. `--import-mode=importlib`,
  `norecursedirs`/`collect_ignore`, unique test basenames). Register any custom
  markers used (`xfail` is built-in; no marker registration needed for it).
- Exact `addopts` / config placement (`pyproject.toml [tool.pytest.ini_options]`
  and `[tool.coverage.*]`), report formats, and the precise fail-under number
  (set after measuring).
- Whether to upload `coverage.xml` as a plain build artifact (no token, no
  codecov) for inspection.
- Exact wording of each xfail `reason` string and the Phase-5 reference form.
- Workflow filename/layout (e.g. `.github/workflows/ci.yml`) and whether to use a
  composite `setup` action now or inline the uv setup (pchandler uses a composite;
  inline is acceptable for this lightweight phase).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone planning
- `.planning/ROADMAP.md` §"Phase 3: Test & CI Foundation" — goal + 3 success
  criteria this phase must satisfy.
- `.planning/REQUIREMENTS.md` — **TEST-01**, **TEST-02**, **CICD-01** (lines
  ~39–49, 103–110). Note TEST-03..06 and CICD-02 are explicitly later phases.
- `.planning/PROJECT.md` §Constraints — "Publication standard: branch protection
  + CI/CD match the PCHandler template"; §Key Decisions — "CI/CD split:
  lightweight test-CI early (Phase 3), branch-protection/publication hardening
  pre-ship (Phase 6)."

### Publication template (the standard to match — scoped down here, full in Phase 6)
- `/scratch/41_pchandler/.github/workflows/ci.yml` — the elaborate target
  (pre-commit lint, informational pyright, `pytest --cov`, codecov upload, docs
  build, self-hosted GPU job). Phase 3 mirrors **only** the `pytest --cov` core.
- `/scratch/41_pchandler/.github/actions/setup-python-deps/action.yml` — pchandler's
  composite install action (pip-based; pc2img diverges to uv per D-09).
- `/scratch/41_pchandler/pyproject.toml` §`[project.optional-dependencies].dev`,
  `[tool.ruff]`, `[tool.pytest.ini_options]` — the `pytest-cov~=5.0` /
  `coverage~=7.0` pins to mirror (D-07) and the ruff config Phase 4 will adopt.
- `/scratch/41_pchandler/.pre-commit-config.yaml` — ruff/mypy hook setup that
  Phase 4 (not Phase 3) will bring over.

### Phase-local carryover
- `.planning/phases/02-dependency-adaptation-reproducible-environment/02-CONTEXT.md`
  — uv-canonical decisions (D-05 native `uv.lock` workflow, D-08 PEP 735 dev/doc
  groups, D-12 third_party symlinks are gitignored source-aids only) that D-07/D-09
  build on; also names GPU-01 (v2) as the GPU-validation deferral.
- `.planning/todos/pending/2026-07-09-move-to-ruff-lint-ci.md` — the ruff/lint-CI
  todo deferred to Phase 4 by D-08.

### Codebase maps (integration surface)
- `.planning/codebase/TESTING.md` — current test layout / gaps.
- `.planning/codebase/STACK.md` — dependency inventory + versions.

_No external ADRs beyond the sibling publication template — Phase 3's decisions
are captured in this file._
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/` already holds 5 modules:
  `test_point_cloud_image_generator.py`, `test_disk_backed_image_data.py`,
  `test_disk_backed_image_store.py` (DELETE — D-02),
  `test_lazy_disk_cache.py` (DELETE — D-02), `test_rrim_features.py`. The three
  surviving modules are the collection scope Phase 3 makes green.
- The committed universal `uv.lock` + `[tool.uv]` config in `pyproject.toml`
  (Phase 2) — CI installs from it via `uv sync --frozen` (D-09).
- The PEP 735 `[dependency-groups].dev` group — where `pytest-cov`/`coverage`
  are added (D-07).
- `.github/workflows/release-please.yml` already exists — the new `ci.yml` sits
  beside it; don't disturb release-please.

### Established Patterns
- pc2img has **no** `[tool.pytest.ini_options]`, `pytest.ini`, `tox.ini`,
  `setup.cfg`, or `conftest.py` today — pytest config is greenfield (goes in
  `pyproject.toml`).
- Phase 2 established uv-native dev flow (`uv sync`, `uv run pytest`) in
  CONTRIBUTING; CI (D-09) follows the same tool, not pip.
- `~=` compatible-release pin convention throughout `pyproject.toml`.

### Integration Points
- **TEST-01 root cause:** collection reaches `third_party/pchandler` +
  `third_party/gsegutils` (each a full sibling repo with its own `tests/` +
  `scripts/`); duplicate basenames trigger import-file-mismatch errors.
  `testpaths = ["tests"]` is the primary fix; the symlinks are gitignored so CI's
  fresh checkout won't have them, but local dev must collect cleanly too.
- **Failing tests to xfail (D-03):** all of
  `tests/test_disk_backed_image_data.py` (11: `TestOffloading*`, `TestArrayInterfaceAndPickling*`,
  `TestCacheFileFinalization*`, `TestPurgeToggle*`) +
  `tests/test_point_cloud_image_generator.py::test_constructor_normalizes_omitted_lazy_disk_cache_config`.
- `pydantic` `__get_validators__` deprecation warnings surface during collection
  (12×) — noise, not in scope to fix here.
</code_context>

<specifics>
## Specific Ideas

- "Green means clean" is the guiding principle for D-01: a safety net is only
  useful if a green run guarantees no *new* regressions.
- Mirror pchandler's coverage tooling versions (`pytest-cov~=5.0`,
  `coverage~=7.0`) for cross-library consistency, but keep pc2img's CI **uv-based**
  (not pchandler's pip) — an intentional, already-established divergence.
- Phase 3 CI is deliberately the *lightweight* slice of pchandler's `ci.yml` —
  just the `pytest --cov` core; lint/pyright/docs/GPU/codecov are later phases.
</specifics>

<deferred>
## Deferred Ideas

- **`black → ruff` swap + lint-in-CI + pyright step** — Phase 4/QUAL-01 (D-08).
  The `move-to-ruff-lint-ci` todo's CI half moved to Phase 4 with its swap half;
  its `resolves_phase` should be retargeted `3 → 4`.
- **Codecov integration** (upload `coverage.xml`, PR comments, trend tracking) —
  Phase 6 publication hardening.
- **Real coverage of the core modules** (projection/interp, derivative features +
  feature-name DSL, `FeatureManager`/`TiledPointCloudImageGenerator`, `util.py`)
  — TEST-03..06, Phase 5.
- **Fixing the xfail'd failures / known bugs** with proving tests — Phase 5
  (BUG-05 inputs), informed by the Phase 4 soundness review.
- **GPU tests + self-hosted GPU runner infrastructure** — GPU-01 (v2); when it
  lands, reuse pchandler's shared self-hosted runner + GHCR image (D-12/D-13).
- **Reconcile pc2img (uv-native) vs pchandler (pip) CI templates** — Phase 6.

### Reviewed Todos (not folded)
- `2026-07-09-move-to-ruff-lint-ci.md` (`resolves_phase: 3`) — **reviewed,
  deferred to Phase 4** (D-08). Both the swap and the lint-CI wiring belong with
  the Phase 4 hygiene work; wiring lint into Phase 3 CI would be throwaway.
  Recommend updating its `resolves_phase` to 4.
- `2026-07-09-coerce-null-lazy-disk-cache-config.md` — **reviewed**; the
  corresponding test (`test_constructor_normalizes_omitted_lazy_disk_cache_config`)
  is xfail'd in Phase 3 (D-03) and the fix stays in its target phase (4/5).
- `2026-07-09-guard-transformarray-module-import.md` (`resolves_phase: 4`) and
  `2026-07-09-document-cuda11-vs-cuda12-selection-guidance.md` — reviewed;
  unrelated to test/CI, remain in their own phases.

</deferred>

---

*Phase: 3-Test & CI Foundation*
*Context gathered: 2026-07-09*
