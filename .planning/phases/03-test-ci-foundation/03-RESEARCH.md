# Phase 3: Test & CI Foundation - Research

**Researched:** 2026-07-09
**Domain:** Python test tooling (pytest 9.x), coverage (pytest-cov/coverage), GitHub Actions CI (uv-native)
**Confidence:** HIGH (all core claims verified by running the tools in this repo)

> This phase's CONTEXT.md is **fully decided (D-01…D-13)**. This research does not
> re-open decisions — it de-risks execution with exact, copy-pasteable config and
> flags the one latent conflict it found (pytest-9-vs-cov-5, §Open Decision Flags).

---

## User Constraints (from CONTEXT.md)

### Locked Decisions (authoritative — plan to THESE)
- **D-01 Green-by-triage.** Reach a *green* suite by dispositioning existing red, not by fixing bugs (Phase 5) and not by shipping red.
- **D-02 Delete** the two import-broken pre-refactor modules: `tests/test_disk_backed_image_store.py`, `tests/test_lazy_disk_cache.py`. Rely on git history.
- **D-03 Park failing-but-current tests** as `@pytest.mark.xfail(reason=..., strict=False)` — they still execute (partial coverage) and flip to XPASS when Phase 5 fixes them. Each `reason` names the failure and points at Phase 5.
- **D-04** xfail'd tests are Phase-5/BUG-05 *candidates*, NOT classified (stale-expectation vs real-bug) in Phase 3.
- **D-05 Measure the whole package:** `--cov=pc2img` **with branch coverage**. Honest low floor including untested Phase-5 modules.
- **D-06 Baseline is a regression guard:** record the measured % durably (coverage note / CONTRIBUTING) **and** set `--cov-fail-under` a hair below the baseline for headroom.
- **D-07 Tooling matches pchandler:** `pytest-cov ~= 5.0` + `coverage ~= 7.0`, added to the PEP 735 `[dependency-groups].dev`. `term-missing` locally + `xml` in CI. Codecov deferred to Phase 6.
- **D-08 No lint/pyright in Phase 3 CI.** black→ruff swap + lint-in-CI both land in Phase 4. Retarget the `move-to-ruff-lint-ci` todo `resolves_phase: 3 → 4`.
- **D-09 Install via `uv sync --frozen`** (with `astral-sh/setup-uv`) against the committed `uv.lock`. Intentional divergence from pchandler's pip CI.
- **D-10 Triggers:** `pull_request` + `push` to `develop-gsd` and `main`.
- **D-11 Single job, CPU-only, `ubuntu-latest`, Python 3.12 only** (no matrix). Runs scoped pytest + coverage + fail-under gate.
- **D-12 No GPU testing / self-hosted runner** in Phase 3.
- **D-13 (deferred, forward-only)** When GPU testing lands (GPU-01, v2), reuse pchandler's shared runner + GHCR image.

### Claude's Discretion (resolved in this research)
- Exact pytest scoping mechanism → **§1** (`testpaths=["tests"]` is sufficient and verified; `--import-mode=importlib` belt-and-suspenders; `norecursedirs`/`collect_ignore` NOT needed).
- Exact `addopts` / config placement, report formats, precise fail-under number → **§2** (`fail_under=22`; coverage config in `[tool.coverage.*]`; **`--cov` NOT in `addopts`**).
- Upload `coverage.xml` as a plain artifact (no codecov) → **§3** (yes, `actions/upload-artifact`, optional).
- Exact xfail `reason` wording + Phase-5 reference form → **§4**.
- Workflow filename/layout, composite vs inline uv setup → **§3** (`.github/workflows/ci.yml`, inline setup-uv — no composite this phase).

### Deferred Ideas (OUT OF SCOPE)
- black→ruff swap + lint-in-CI + pyright step → Phase 4 / QUAL-01.
- Codecov integration → Phase 6.
- Real coverage of core modules (projection/interp/features/orchestration/util) → TEST-03..06, Phase 5.
- Fixing the xfail'd failures / known bugs → Phase 5.
- GPU tests + self-hosted runner → GPU-01 (v2).
- Reconcile pc2img (uv) vs pchandler (pip) CI templates → Phase 6.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | Scope pytest discovery to `tests/` (stop collecting `third_party/`) | §1 — `testpaths=["tests"]` verified to drop 1140→26 collected, 7→0 third_party errors |
| TEST-02 | Coverage measurement + reporting with a recorded baseline | §2 — measured **24%** baseline (`--cov=pc2img --cov-branch`); `fail_under=22` ratchet; CONTRIBUTING note |
| CICD-01 | Lightweight CI runs the suite on PRs (early safety net) | §3 — single-job uv-native `ci.yml`, current action versions, `fetch-depth: 0` guard |

---

## Summary

Everything needed for this phase is greenfield config plus one CI file. There is
no `[tool.pytest.ini_options]`, no coverage config, and no test-CI today. I verified
every mechanism by running it against this repo's live venv (pytest **9.1.1**, uv 8.x):

1. **Scoping (TEST-01):** `testpaths = ["tests"]` alone drops collection from
   **1140 tests / 7 errors** (bare `pytest`) to **26 tests / 0 `third_party` errors**.
   `third_party/` is a *sibling* of `tests/`, not a child, so `testpaths` stops
   recursion into it entirely — no `norecursedirs`/`collect_ignore` needed. The two
   remaining collection errors are exactly the two modules D-02 deletes.
2. **Coverage (TEST-02):** with the two broken modules deleted and the 11 failures
   xfail'd, the suite is green (26 tests) and `--cov=pc2img --cov-branch` reports a
   **24% baseline**. Set the ratchet a hair below at **`--cov-fail-under=22`**.
3. **CI (CICD-01):** a single `ubuntu-latest` job — `checkout` → `setup-uv` →
   `uv sync --frozen` → `uv run pytest --cov=… --cov-fail-under=22` — beside the
   existing `release-please.yml`. Fresh CI checkout has **no `third_party/`**
   (gitignored) and installs deps from PyPI via the committed lock, so criterion 1
   is satisfied two ways (dir absent *and* scoped out).

**Primary recommendation:** Delete 2 modules (D-02), xfail 11 tests (D-03), add the
`[tool.pytest.ini_options]` + `[tool.coverage.*]` blocks from §1–§2, add
`pytest-cov ~= 5.0` + `coverage ~= 7.0` to the `dev` group and **regenerate
`uv.lock`**, then add the `ci.yml` from §3 with **`fetch-depth: 0`** and
`develop-gsd` (hyphen, not slash) triggers. Record 24%→floor 22 in CONTRIBUTING.

---

## Measured Starting State (verified 2026-07-09, this repo)

| Measurement | Value | How verified |
|-------------|-------|--------------|
| Bare `pytest` from repo root | **1140 collected, 7 collection errors** | `uv run pytest --collect-only -q` |
| `testpaths=["tests"]` collection | **26 collected, 2 errors** (the D-02 delete targets) | `pytest --collect-only -o "testpaths=tests"` |
| 3 surviving modules run | **15 passed / 11 failed** | `pytest <3 files>` |
| Coverage baseline | **24%** total (branch) | `pytest --cov=pc2img --cov-branch` |
| venv pytest | **9.1.1** (dev group leaves `pytest` unpinned) | `pytest --version` |
| pytest-cov / coverage installed | **absent** (this is what D-07 adds) | `import pytest_cov` → ModuleNotFoundError |

**Measured failure set to xfail (11 total — reconcile against CONTEXT):**
- `tests/test_point_cloud_image_generator.py::test_constructor_normalizes_omitted_lazy_disk_cache_config` (1)
- `tests/test_disk_backed_image_data.py` — **10** functions:
  `TestOffloadingAndLoading::test_offload_without_cache_path_logs_warning`,
  `TestArrayInterfaceAndPickling::test_getstate_with_cache_path_unloads_data`,
  `TestArrayInterfaceAndPickling::test_pickle_roundtrip_with_cache`,
  `TestCacheFileFinalization::{test_finalizer_alive_and_canceled_on_getstate, test_finalizer_reregistered_on_unpickle, test_cache_file_persistence_after_original_deletion, test_cleanup_on_finalizer_call_deletes_file}`,
  `TestPurgeToggle::{test_disable_purge, test_enable_purge, test_enable_purge_no_cache}`.

> ⚠ **Discrepancy to note for the planner:** CONTEXT §code_context says "11
> `test_disk_backed_image_data` failures + the null-cache-config failure" (=12).
> The **measured reality is 11 total** = 10 in `test_disk_backed_image_data.py` + 1
> in `test_point_cloud_image_generator.py`. The xfail list MUST be built from the
> live run, not the CONTEXT count. `test_disk_backed_image_data.py` has 3 *passing*
> tests (`TestImageDataInitialization::*`, `test_offload_and_load_with_cache`,
> `test_automatic_offloading_flag`, `test_array_protocol`, `test_getstate_without_cache_path_preserves_data`,
> `test_setstate_restores_attributes`, `test_pickle_roundtrip_without_cache`) — do
> NOT blanket-xfail the whole module; xfail only the 10 named functions.

---

## 1. Pytest Collection Scoping (TEST-01 / D-01, D-02)

### Recommended config — add to `pyproject.toml`

```toml
[tool.pytest.ini_options]
# TEST-01: collect ONLY the project suite. third_party/ (gitignored symlinks to the
# sibling pchandler/GSEGUtils checkouts) is a *sibling* of tests/, so testpaths
# stops recursion into it — verified: bare `pytest` 1140 collected/7 errors →
# scoped 26 collected/0 third_party errors.
testpaths = ["tests"]
# Modern import machinery: no sys.path injection, avoids duplicate-basename
# import-file-mismatch. Belt-and-suspenders here (tests/ basenames are already
# unique and there is no conftest.py / __init__.py), but it is the current pytest
# recommendation and future-proofs against added test files.
addopts = "--import-mode=importlib --strict-markers"
xfail_strict = false   # D-03: an unexpected pass (XPASS) must NOT fail the suite
```

### Why this is the minimal robust config (verified)
- **`testpaths` is sufficient.** `third_party/` sits at repo root next to `tests/`.
  `testpaths=["tests"]` means bare `pytest` (and `pytest` with no path args) only
  ever descends into `tests/`. Empirically the 7 `third_party/*` collection errors
  disappeared and only the 2 D-02-delete errors remained. **`norecursedirs` and
  `collect_ignore` are NOT required** and would be redundant.
- **`--import-mode=importlib`** is recommended but not strictly load-bearing after
  D-02 deletion + scoping (the duplicate-basename collisions were *across* the two
  sibling repos and their `scripts/`, all now out of scope). Keep it as good hygiene.
- **`--strict-markers`** is safe: within `tests/` the only marker used is the
  built-in `xfail` (no registration needed). It turns a typo'd marker into an error
  rather than a silent warning. Optional; drop it if you prefer zero risk of a
  future custom marker needing registration.
- **No `conftest.py` is needed** for scoping. (One may still be introduced later for
  shared fixtures — out of scope here.)

### Pitfall — scoping only governs *argument-less* runs
`testpaths` is ignored the moment you pass an explicit path. `pytest third_party/…`
or `pytest .` would still recurse and re-surface the sibling collisions. The
supported dev workflows (`uv run pytest`, `pytest tests/…`) are unaffected. Document
"run `pytest` / `pytest tests/…`, never `pytest .`" in CONTRIBUTING if desired.

---

## 2. Coverage Tooling, Baseline & Ratchet (TEST-02 / D-05, D-06, D-07)

### Dependency additions — `[dependency-groups].dev`
```toml
[dependency-groups]
dev = ["black ~= 23.10", "pytest", "memory_profiler", "pytest-cov ~= 5.0", "coverage ~= 7.0"]
doc = ["sphinx ~= 5.1"]
```
`[VERIFIED: pchandler pyproject.toml lines 114-115]` — mirrors pchandler's exact pins (D-07).
**After editing, regenerate the lock:** `uv lock` (updates `uv.lock`), then commit
`uv.lock` — CI runs `--frozen` and will fail if the lock is stale (§Risks).

### Coverage config — add to `pyproject.toml`
```toml
[tool.coverage.run]
branch = true                 # D-05: branch coverage
source = ["pc2img"]           # measure the whole package (installed/editable src/pc2img)
omit = ["*/_version.py"]      # setuptools_scm-generated, not meaningful to cover

[tool.coverage.report]
show_missing = true           # term-missing style locally
# NOTE: fail_under is intentionally NOT set here — see "Where the gate lives" below.
exclude_also = [
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@(abc\\.)?abstractmethod",
]
```
> pchandler has **no `[tool.coverage.*]` block at all** — it passes `--cov=pchandler`
> on the CLI with branch off. D-05 requires branch coverage, so this block is a
> justified, minimal addition beyond the template. `[VERIFIED: pchandler pyproject.toml]`

### Where the gate lives — **do NOT put `--cov` in `addopts`**
Putting `--cov=pc2img --cov-fail-under=22` in `addopts` makes **every** invocation —
including single-file runs like `pytest tests/test_rrim_features.py` — measure
coverage and trip the gate (a single file covers ≪22%). **Verified footgun:**
running only `test_rrim_features.py` with `--cov=pc2img` reports *"Module pc2img was
never imported / No data collected"* and 0%. Therefore:

- **Local full-suite (term-missing):**
  `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing`
- **CI (xml + gate):**
  `uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=22`
- **Local iteration (fast, no coverage):** `uv run pytest`

Keeping the `--cov-fail-under` gate on the **CI command line only** (not in
pyproject) means local coverage inspection never spuriously fails on a subset run.
This resolves the "exact report wiring" discretion item under D-07.

### Baseline number & the ratchet (D-06)
- **Measured baseline: 24%** total (branch), `--cov=pc2img`, with the 11 failing
  tests running to their failure point (identical execution to `xfail(strict=False)`,
  so the xfail'd suite yields the same ~24%). `[VERIFIED: pytest-cov run, this repo]`
- **Set `--cov-fail-under=22`** — ~2 points of headroom. Rationale: xfail'd tests
  execute *up to* their failure line; if a failure moves earlier (or a currently
  passing test regresses to fail sooner) covered lines can dip slightly. Coverage
  volatility here is small and one-directional-safe for XPASS (XPASS only *adds*
  lines), so 22 is a defensible floor. Phase 5 ratchets it upward as it adds tests.
- **Record durably (D-06):** add a short "Coverage baseline" note to `CONTRIBUTING.md`
  (established in Phase 2 as the dev-workflow doc) stating: baseline **24%** measured
  2026-07-09 via `uv run pytest --cov=pc2img --cov-branch`, floor **22** enforced by
  CI `--cov-fail-under`, ratcheted upward in Phase 5. This is the "note vs guard"
  both-halves that D-06 requires.

### Optional — coverage.xml as a plain artifact (Claude's discretion)
Upload `coverage.xml` via `actions/upload-artifact` for inspection **without** a
codecov token/account (codecov is Phase 6). See §3. Low value but free; include it.

---

## 3. GitHub Actions CI (CICD-01 / D-09, D-10, D-11)

### `.github/workflows/ci.yml` (new file, beside `release-please.yml`)
```yaml
name: CI

on:
  pull_request:
  push:
    branches: [develop-gsd, main]   # ⚠ hyphen — pc2img mainline, NOT pchandler's develop/gsd

jobs:
  tests:
    name: Tests (pytest + coverage)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        # fetch-depth: 0 → full history + tags so setuptools_scm can derive the
        # version during the editable build in `uv sync` (_version.py is gitignored,
        # so it is NOT in a fresh checkout and must be regenerated from a tag).
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Install uv + Python 3.12
        # setup-uv publishes only IMMUTABLE full-version tags (v8.0.0+); moving tags
        # like @v8 do NOT resolve. Pin the full version (or a commit SHA).
        uses: astral-sh/setup-uv@v8.3.2
        with:
          python-version: "3.12"
          enable-cache: true          # caches the uv cache dir, keyed on uv.lock

      - name: Install locked dependencies (exercises the Phase 2 lock — D-09)
        run: uv sync --frozen

      - name: Run tests with coverage + fail-under gate
        run: >
          uv run --frozen pytest
          --cov=pc2img --cov-branch
          --cov-report=term-missing
          --cov-report=xml
          --cov-fail-under=22

      - name: Upload coverage.xml (no codecov — Phase 6)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-xml
          path: coverage.xml
          if-no-files-found: ignore
```

### Verified / current action versions (July 2026)
| Action | Version | Provenance |
|--------|---------|-----------|
| `astral-sh/setup-uv` | **`v8.3.2`** (SHA `11f9893b081a58869d3b5fccaea48c9e9e46f990`) | `[VERIFIED: github.com/astral-sh/setup-uv]` — latest, published 2026-07-08. **Immutable tags only** — `@v8` does not resolve. |
| `actions/checkout` | **`v5`** (pchandler pins v5.0.1 SHA `93cb6efe…`); **v6** is also current | `[CITED: github.com/actions/checkout/releases]` — v5.0.1 matches pchandler template; v6 available if you prefer newest |
| `actions/upload-artifact` | **`v4`** (pchandler pins v7.0.1 SHA `043fb46d…`) | `[CITED: pchandler ci.yml]` — v4 is the widely-used stable; v7 exists |

**Hardening note (optional, matches pchandler style):** pchandler pins every action
to a **commit SHA** with a `# vX.Y.Z` comment. For this lightweight phase, moving/full
tags are acceptable; SHA-pinning is a Phase-6 publication-hardening concern. If you
want early parity, pin the SHAs above.

### Key CI facts (verified)
- **`third_party/` absence in CI is fine, not a landmine.** It is gitignored, so a
  fresh checkout lacks it. `uv sync --frozen` installs `pchandler`/`GSEGUtils` from
  **PyPI** per the committed lock (Phase 2 D-12 forbids local-path lock entries;
  Phase 2 SC3 proved a clean-room install with no `third_party/`). Criterion 1 is
  then satisfied both by the absent dir *and* by `testpaths`.
- **`uv sync` installs the `dev` group by default** (per the pyproject comment /
  uv default), so pytest + pytest-cov + coverage are present without extra flags.
- **Does not disturb `release-please.yml`.** That workflow is `name: release-please`,
  triggers on `push` only, and does no testing. The new `name: CI` job is orthogonal.
- **Single job, no matrix (D-11):** `requires-python ~=3.12,<3.13` → one Python.

---

## 4. xfail Disposition Mechanics (D-03)

### Semantics — confirmed
`@pytest.mark.xfail(reason="…", strict=False)`:
- The test body **still executes** (up to the point it raises) → it **contributes
  partial coverage**, exactly what D-03/D-06 rely on. `[VERIFIED: coverage run — the
  11 failing tests executed and their lines counted toward the 24% baseline]`
- If the assertion still fails → reported **`xfailed`** (expected failure), suite
  stays green.
- When Phase 5 fixes the underlying code → the test passes → reported **`xpassed`**;
  because **`strict=False`**, XPASS **does not fail** the suite (a strict xfail would).
  This is the "flips automatically, nothing silently lost" property.
- **No marker registration needed** — `xfail` is a built-in marker; `--strict-markers`
  does not flag it. `[VERIFIED: pytest docs / built-in]`
- Global `xfail_strict = false` in `[tool.pytest.ini_options]` documents the default;
  per-mark `strict=False` is the belt-and-suspenders form D-03 names — use both.

### Recommended `reason` string form (resolves the discretion item)
Name the observable failure and point at the Phase-5 owner. Suggested template:
```python
import pytest

@pytest.mark.xfail(
    reason="Phase 5 (BUG-05 candidate): DiskBackedImageData finalizer/purge lifecycle "
           "not yet wired — see .planning ROADMAP Phase 5; xpasses when fixed.",
    strict=False,
)
def test_disable_purge(self, tmp_path): ...
```
For the null-cache-config one (which already has a matching pending todo):
```python
@pytest.mark.xfail(
    reason="Phase 5 (BUG-05 candidate): omitted lazy_disk_cache_config not coerced to "
           "default — see todo 2026-07-09-coerce-null-lazy-disk-cache-config; xpasses when fixed.",
    strict=False,
)
```
Guidance: keep each `reason` on the specific failure (don't reuse one generic string),
reference **Phase 5** (not a bare bug ID — commits squash to `main` where planning IDs
dangle, per CLAUDE.md), and phrase so an XPASS is a clear "go re-classify this" signal.
Apply the marker per-function (or per-class for `TestCacheFileFinalization` /
`TestPurgeToggle` only if *all* their methods fail — verify: `TestPurgeToggle` has all
3 failing so a class-level mark is valid; `TestCacheFileFinalization` has all 4 failing;
`TestArrayInterfaceAndPickling` has a mix, so mark the 2 methods individually).

---

## Validation Architecture

> Nyquist validation is enabled. Each success criterion below has a concrete,
> command-checkable verification point. Lifted into VALIDATION.md by the orchestrator.

### Success Criteria → Observable Checks

| SC | Criterion | Verification point (command) | Pass condition |
|----|-----------|------------------------------|----------------|
| 1 | `pytest` from repo root collects only `tests/`, no `third_party/` errors | `uv run pytest --collect-only -q` | Exit 0; output lists only `tests/…`; **zero** `third_party/*` ERROR lines; collected count == the 3-module total (26 pre-xfail) |
| 2 | Coverage runs; baseline recorded & reported | `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` | A `TOTAL … NN%` line is emitted; `--cov-fail-under=22` present in `ci.yml`; a "Coverage baseline" note exists in `CONTRIBUTING.md` |
| 3 | CI runs the suite automatically on every PR, reports pass/fail | `test -f .github/workflows/ci.yml` + structural grep | File exists; `on:` has `pull_request` and `push.branches` includes `develop-gsd` + `main`; a step runs `uv run … pytest … --cov-fail-under`; job `runs-on: ubuntu-latest` |

### Sampling points (per Nyquist)
- **Per task commit (quick):** `uv run pytest` (no coverage) — fast green/red signal.
- **Per wave / coverage task:** `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` — confirms the suite is green **and** ≥ floor.
- **Phase gate:** full command with `--cov-fail-under=22` exits 0; `ci.yml` structural check passes; the workflow's first real PR run (or `act`/dry structural read) reports pass.

### Test framework
| Property | Value |
|----------|-------|
| Framework | pytest **9.1.1** (venv; dev group leaves `pytest` unpinned) + pytest-cov `~=5.0` / coverage `~=7.0` (added this phase) |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` (new), `[tool.coverage.*]` (new) |
| Quick run | `uv run pytest` |
| Full + coverage | `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` |
| Collection check | `uv run pytest --collect-only -q` |

### Wave 0 gaps
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` — did not exist; created this phase (covers SC1).
- [ ] `pyproject.toml` `[tool.coverage.run]/[report]` — did not exist; created this phase (covers SC2).
- [ ] `pytest-cov` / `coverage` — not installed; added to `dev` group + `uv lock` regenerated (covers SC2).
- [ ] `.github/workflows/ci.yml` — did not exist; created this phase (covers SC3).
- [ ] `CONTRIBUTING.md` coverage-baseline note — add (covers SC2 durable record).
- No new *test code* is authored this phase (real coverage is Phase 5) — Wave 0 is config + CI only.

---

## Risks & Pitfalls

### ⚠ P1 — `develop-gsd` vs `develop/gsd` (HIGH impact, easy to miss)
pchandler's `ci.yml` triggers on `develop/gsd` (slash); **pc2img's mainline is
`develop-gsd` (hyphen)** `[VERIFIED: git branch -a]`. Copy-pasting pchandler's file
would make CI silently never fire on the integration branch's direct pushes. Use the
hyphen form in §3.

### ⚠ P2 — CI needs `fetch-depth: 0` for setuptools_scm (MEDIUM)
`src/pc2img/_version.py` is **gitignored** (`.gitignore: src/**/_version.py`) and
generated by setuptools_scm from git tags (`write_to`, tag-driven). `[VERIFIED: git
ls-files (untracked) + .gitignore + pyproject]`. `uv sync` builds pc2img editable →
runs setuptools_scm → needs tags. A default shallow checkout (`fetch-depth: 1`) has
no tags → version derivation degrades/fails. Mitigation: `fetch-depth: 0` (in §3).

### ⚠ P3 — pytest 9.1.1 vs `pytest-cov ~= 5.0` (LOW — empirically de-risked)
D-07 mirrors pchandler's `pytest-cov ~= 5.0`, but pchandler runs `pytest ~= 8.4`
while pc2img's dev group leaves `pytest` unpinned → lock resolved **9.1.1**.
pytest-cov 5.0.0 predates pytest 9. **I tested it:** `pytest 9.1.1` + `pytest-cov==5.0.0`
+ `coverage~=7.0` loads (`plugins: cov-5.0.0`), runs, and reports coverage cleanly.
So `~=5.0` is *not broken*. See §Open Decision Flags for the optional parity choice.

### P4 — `--cov` in `addopts` breaks subset runs (MEDIUM — designed around in §2)
A global `addopts` `--cov` makes single-file runs measure ≪22% and trip
`--cov-fail-under`; `test_rrim_features.py` alone reports *"Module pc2img was never
imported / No data collected"* `[VERIFIED]`. Keep `--cov*` on the CLI/CI only.

### P5 — `test_rrim_features.py` contributes 0% to `--cov=pc2img` (INFO — explains the low baseline)
It loads `features/{core,registry,rrim}.py` under a **throwaway module name** via
`importlib.util.spec_from_file_location` (to avoid importing heavy pchandler), so it
never imports the real `pc2img` package. `[VERIFIED: rrim.py = 275 stmts at 0% in the
full run; 0 data when run alone]`. Consequence: `rrim.py` shows 0% *despite having
passing tests*, depressing the 24% baseline. This is expected and NOT a Phase 3 fix
(re-pointing the test at `pc2img.features.rrim` is a Phase 5 coverage concern). Note
it so nobody "fixes" the baseline by chasing rrim.

### P6 — `uv sync --frozen` lock-drift failure (MEDIUM — expected, sequence it)
Adding `pytest-cov`/`coverage` to the `dev` group changes the resolution; **you must
run `uv lock` and commit the updated `uv.lock`** *before* CI runs, or `--frozen`
fails with a lock-out-of-date error. Make lock regeneration an explicit plan task,
sequenced after the pyproject dep edit and before the CI file lands.

### P7 — pydantic `__get_validators__` deprecation warnings (INFO — out of scope)
12× `PydanticDeprecatedSince20: __get_validators__ is deprecated` surface during
collection `[VERIFIED]`. They are **warnings, not errors**, do not affect green/red,
and are not filtered to errors anywhere. Do **not** add `filterwarnings = error`
(would turn the suite red). Fixing the deprecation is a later-phase hygiene item.

### P8 — coverage measures editable `src/pc2img`, not site-packages (INFO — works)
`uv sync` installs pc2img editable; `--cov=pc2img` resolves to `src/pc2img/…`
`[VERIFIED: coverage table shows src/pc2img paths]`. Same in CI (checkout's src tree).
No `[paths]` remapping needed for this single-environment setup.

---

## Open Decision Flags (for planner / discuss — do NOT silently pick)

### F1 — Should `pytest` also be pinned to match pchandler? (relates to D-07)
D-07 locks `pytest-cov ~= 5.0` + `coverage ~= 7.0` but says nothing about `pytest`
itself, which is unpinned → **9.1.1** in the lock (pchandler runs `pytest ~= 8.4`).
Three options, tradeoffs surfaced:

| Option | Change | Optimizes for | Costs |
|--------|--------|--------------|-------|
| **A — full pchandler parity** | add `pytest ~= 8.4` alongside the two D-07 pins | strict "tooling matches pchandler" across the *whole* trio; `pytest-cov 5.0` is then on its proven pytest | downgrades pytest 9.1.1→8.4 in the lock; broadens the diff |
| **B — honor D-07 literally (recommended default)** | add only `pytest-cov ~= 5.0` + `coverage ~= 7.0`, leave pytest at 9.1.1 | minimal change; exactly what D-07 names | `pytest-cov 5.0` is not upstream-tested against pytest 9 (though **verified working here**) |
| **C — newest** | keep pytest 9.x + bump `pytest-cov ~= 7.0` | fully-supported modern stack | diverges from pchandler's `~=5.0` pin (violates D-07 as written) |

**Recommendation:** **Option B** is the faithful reading of the locked decision and I
verified it runs cleanly, so it is safe to proceed. If the owner values exact
cross-library toolchain parity (a stated publication goal), **Option A** is the
cleaner long-term answer and is a small, well-scoped addition — worth a one-line
confirmation during planning/discuss rather than an auto-pick. Avoid C (contradicts
D-07's explicit `~=5.0`).

---

## Sources

### Primary (HIGH — verified by running in this repo, 2026-07-09)
- `uv run pytest --collect-only` (bare vs `testpaths=tests`) — scoping behavior, 1140→26, 7→0 errors.
- `uv run pytest <3 modules> --cov=pc2img --cov-branch` — 15/11 pass/fail, **24%** baseline, per-module table.
- `uv run --with "pytest-cov==5.0.0" pytest` — pytest 9.1.1 + cov 5.0.0 compatibility; rrim "no data" behavior.
- `git branch -a`, `git ls-files`, `.gitignore`, `.release-please-manifest.json` — `develop-gsd` name, `_version.py` untracked, tags present.
- `/scratch/41_pchandler/pyproject.toml`, `.github/workflows/ci.yml`, `.github/actions/setup-python-deps/action.yml` — pin/version template (D-07), CI shape to scope down.

### Secondary (MEDIUM/CITED — official sources)
- `[CITED: github.com/astral-sh/setup-uv]` — v8.3.2 latest (2026-07-08), immutable-tag policy, `enable-cache`/`python-version` usage, works with `uv sync --frozen`.
- `[CITED: github.com/actions/checkout/releases]` — v5/v6 current.

### Repo canonical refs read
- `.planning/phases/03-test-ci-foundation/03-CONTEXT.md` (D-01…D-13), `ROADMAP.md` §Phase 3, `REQUIREMENTS.md`, `PROJECT.md`, `codebase/TESTING.md`, `todos/pending/2026-07-09-move-to-ruff-lint-ci.md`, `pyproject.toml`, `uv.lock` (present).

---

## Metadata

**Confidence breakdown:**
- Collection scoping (TEST-01): **HIGH** — reproduced the exact before/after in-repo.
- Coverage baseline + config (TEST-02): **HIGH** — 24% measured; footguns reproduced.
- CI shape + action versions (CICD-01): **HIGH** on shape/triggers (verified branch name, lock, third_party absence); **MEDIUM** on live-run behavior of the untriggered workflow (fetch-depth guard is inferred-but-firm, not yet run in Actions).
- xfail mechanics (D-03): **HIGH** — semantics confirmed + partial-coverage contribution observed.

**Research date:** 2026-07-09
**Valid until:** ~2026-08-08 (stable domain; setup-uv/checkout versions may bump — re-check the immutable-tag pin before shipping).
