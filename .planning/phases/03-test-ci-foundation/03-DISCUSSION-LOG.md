# Phase 3: Test & CI Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-09
**Phase:** 3-Test & CI Foundation
**Areas discussed:** Green-CI bar / broken-test disposition, Coverage (gate vs record + scope), Ruff swap timing, CI shape & install path, Own runners for GPU tests

---

## Green-CI bar / broken-test disposition

**Phase 3 bar for the test suite**

| Option | Description | Selected |
|--------|-------------|----------|
| Green-by-triage | Delete dead modules, park failing-current tests as tracked debt (xfail/skip → Phase 5); CI goes green now. | ✓ |
| Red baseline | Stand CI up as-is, record failing set, report red. SC3 technically met but every PR red. | |
| Fix everything now | Fix the 11+ failures in Phase 3; pulls Phase 5 forward, needs Phase 4 review. | |

**Park failing-but-current tests how**

| Option | Description | Selected |
|--------|-------------|----------|
| xfail(strict=False) + reason + Phase 5 ref | Tests still run; auto-flip to XPASS when fixed; failures stay visible. | ✓ |
| skip + reason + Phase 5 ref | Cleaner output but tests don't execute; easy to forget. | |
| Triage each first | Investigate stale-vs-real now, delete/rewrite stale, xfail only real bugs. | |

**Disposition of the 2 import-broken pre-refactor modules**

| Option | Description | Selected |
|--------|-------------|----------|
| Delete outright | Both import symbols that no longer exist; cache logic now in GSEGUtils. | ✓ |
| Rewrite against current API now | Port to current API — but that's TEST-05/Phase 5 scope. | |
| Delete store test, rewrite cache test | Mixed; cache logic is now GSEGUtils' job so salvage questionable. | |

**User's choice:** Green-by-triage; xfail(strict=False); delete both dead modules.
**Notes:** xfail'd tests flagged as candidate BUG-05 inputs, but stale-vs-real classification is left to Phase 4/5 — Phase 3 only parks them.

---

## Coverage (gate vs record + scope)

**What coverage measures**

| Option | Description | Selected |
|--------|-------------|----------|
| Whole package --cov=pc2img (+ branch) | Honest floor across all src, Phase 5 growth visible. | ✓ |
| Tested modules only | Higher headline number, hides the gap. | |
| Whole package, line-only | Simpler, slightly weaker floor. | |

**What the baseline does**

| Option | Description | Selected |
|--------|-------------|----------|
| fail-under ratchet at floor | Record % AND set --cov-fail-under; CI fails on regression; no external service. | ✓ |
| Record number only, no gate | Report + doc the %, no CI failure on drop. | |
| Codecov integration now | Upload to codecov (PR comments/trends); needs token/account. | |

**User's choice:** Whole-package + branch; fail-under ratchet.
**Notes:** Set fail-under a hair below measured baseline for headroom; codecov deferred to Phase 6.

---

## Ruff swap timing

| Option | Description | Selected |
|--------|-------------|----------|
| Pull swap forward into Phase 3 | Replace black w/ ruff + config now, wire ruff check into CI. | |
| Keep swap in Phase 4; Phase 3 CI = tests only | Cleanest split; ruff swap + lint wiring both land in Phase 4. | ✓ |
| black --check in Phase 3, swap in Phase 4 | The throwaway the todo warns against. | |

**User's choice:** Keep swap in Phase 4; Phase 3 CI = tests + coverage only, no lint.
**Notes:** Both the swap and the lint-in-CI wiring move to Phase 4 → the `move-to-ruff-lint-ci` todo's `resolves_phase` should be retargeted 3 → 4. The two "if pulled forward" follow-up questions were rendered moot by this choice.

---

## CI shape & install path

**How CI installs deps**

| Option | Description | Selected |
|--------|-------------|----------|
| uv sync --frozen | setup-uv + committed universal uv.lock; exercises lock as safety net. | ✓ |
| pip install .[dev] (pchandler-style) | Mirrors template but ignores uv.lock, diverges from pc2img workflow. | |
| uv sync (non-frozen) | Allows lock to update; loses drift detection. | |

**When the workflow runs**

| Option | Description | Selected |
|--------|-------------|----------|
| PRs + push to develop-gsd/main | Matches pchandler; covers mainline pushes. | ✓ |
| Pull requests only | Strict CICD-01 reading. | |
| PRs + push to all branches | Overkill for lightweight net. | |

**Static analysis in Phase 3 CI**

| Option | Description | Selected |
|--------|-------------|----------|
| Tests-only; defer pyright to Phase 4 | All static analysis (ruff + pyright) bundled into Phase 4. | ✓ |
| Add non-blocking pyright now | Informational type signal from day one. | |

**User's choice:** uv sync --frozen; PRs + push to develop-gsd/main; tests-only.
**Notes:** Must add pytest-cov + coverage to the dev group. Single 3.12 / ubuntu-latest, no matrix, no codecov (optional coverage.xml artifact) treated as discretion.

---

## Own runners for GPU tests

**GPU testing / runner setup in Phase 3**

| Option | Description | Selected |
|--------|-------------|----------|
| None in Phase 3; defer to GPU-01 (v2) | CPU-only; pc2img has no GPU-specific code. | ✓ |
| Scaffold dormant self-hosted GPU job now | Manual-gated skeleton, no real assertions. | |
| Write + run pc2img GPU tests now | Pulls v2 forward; re-tests pchandler GPU code. | |

**Runner strategy when GPU testing lands (deferred direction)**

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse pchandler's self-hosted GPU runner | Shared runner pool/labels + GHCR image; no new maintenance. | ✓ |
| Dedicated pc2img self-hosted runner + image | Full isolation, doubles maintenance. | |
| Decide at GPU-01 (v2) | Don't pre-commit now. | |

**User's choice:** None in Phase 3 (defer to GPU-01 v2); when it lands, reuse pchandler's shared runner.
**Notes:** Boundary confirmed — GPU-path validation was already deferred to v2 in Phase 2; pc2img GPU is transitive via pchandler.

---

## Claude's Discretion

- Exact pytest scoping mechanism (`testpaths`, `--import-mode=importlib`, `collect_ignore`, unique basenames) to satisfy TEST-01 with `third_party/` symlinks present locally.
- `addopts` / `[tool.pytest.ini_options]` / `[tool.coverage.*]` placement, report formats, and the precise fail-under number (set post-measurement).
- Whether to upload `coverage.xml` as a plain build artifact.
- Exact xfail `reason` wording + Phase-5 reference form.
- Workflow filename/layout and composite-vs-inline uv setup.

## Deferred Ideas

- `black → ruff` swap + lint-in-CI + pyright step → Phase 4/QUAL-01.
- Codecov integration → Phase 6.
- Real coverage of core modules (TEST-03..06) → Phase 5.
- Fixing xfail'd failures / known bugs with proving tests → Phase 5.
- GPU tests + self-hosted GPU runner infra → GPU-01 (v2); reuse pchandler's shared runner when it lands.
- Reconcile pc2img (uv) vs pchandler (pip) CI templates → Phase 6.
