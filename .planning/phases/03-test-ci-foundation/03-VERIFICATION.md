---
phase: 03-test-ci-foundation
verified: 2026-07-09T19:48:11Z
status: passed
score: 3/3 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:

  - test: "Open a real pull request against develop-gsd (or main) and confirm the CI workflow triggers, runs to completion, and reports a green pass/fail status check on the PR."
    expected: "The `CI / tests` check appears on the PR, installs from the frozen lock, runs the scoped suite (15 passed / 11 xfailed), the --cov-fail-under=21 gate passes (~23% total), and the check reports success."
    why_human: "GitHub's platform triggering + status-check reporting is an external-service behavior that cannot be observed from the codebase. The workflow file is verified correct and its exact test command runs green locally; only the live GitHub run remains. Plan 03 recorded this as deferred manual item D4 (VALIDATION.md Manual-Only table)."
---

# Phase 3: Test & CI Foundation Verification Report

**Phase Goal:** A project-scoped test harness, a recorded coverage baseline, and CI that runs the suite on pull requests as a safety net for the heavy work that follows.
**Verified:** 2026-07-09T19:48:11Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | pytest run from repo root collects only `tests/`, no `third_party/` collection errors (SC1) | ✓ VERIFIED | `uv run pytest --collect-only -q` → `collect_exit=0`, `third_party_lines=0`, `26 tests collected`. `testpaths = ["tests"]` in pyproject.toml; the two D-02 import-broken modules are gone from tree and git. |
| 2 | Coverage measurement runs and a baseline percentage is recorded and reported (SC2) | ✓ VERIFIED | `uv run pytest --cov=pc2img --cov-branch --cov-fail-under=21` → `TOTAL … 23%`, gate live ("Required test coverage of 21% reached. Total coverage: 23.35%"). Baseline 23% + floor `--cov-fail-under=21` recorded in CONTRIBUTING.md §"Coverage baseline". |
| 3 | A CI workflow runs the test suite automatically on every pull request and reports pass/fail (SC3) | ✓ VERIFIED (in-codebase) | `.github/workflows/ci.yml` exists, valid YAML: `on: pull_request` + `push` to `develop-gsd`/`main`, `runs-on: ubuntu-latest`, `fetch-depth: 0`, `uv sync --frozen`, runs `pytest … --cov-fail-under=21`, `permissions: contents: read`. Its exact test command runs green locally. Live GitHub trigger deferred to human check. |

**Score:** 3/3 truths verified (0 present, behavior-unverified). One external-platform confirmation routed to human verification (does not lower the in-codebase score).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `pyproject.toml` `[tool.pytest.ini_options]` | testpaths, addopts, xfail_strict | ✓ VERIFIED | `testpaths=["tests"]`, `addopts="--import-mode=importlib --strict-markers"` (no `--cov`), `xfail_strict=false`. |
| `pyproject.toml` `[tool.coverage.*]` | branch coverage config, no fail_under | ✓ VERIFIED | `branch=true`, `source=["pc2img"]`, `omit=["*/_version.py"]`, `exclude_also` guards; no `fail_under` key. |
| `[dependency-groups].dev` pins | pytest ~= 9.1, pytest-cov ~= 5.0, coverage ~= 7.0 | ✓ VERIFIED | `dev = ["black ~= 23.10", "pytest ~= 9.1", "memory_profiler", "pytest-cov ~= 5.0", "coverage ~= 7.0"]`; bare pytest gone. |
| `uv.lock` regenerated + in sync | in sync with pyproject | ✓ VERIFIED | `uv lock --check` → resolved cleanly, no drift. |
| Deletion of 2 import-broken modules | test_disk_backed_image_store.py, test_lazy_disk_cache.py | ✓ VERIFIED | Both absent from tree and git ls-files. |
| xfail markers on current failures | 11 xfailed via strict=False | ✓ VERIFIED | 6 decorators (3 per-method + 2 class-level in disk_backed + 1 in point_cloud) → 11 xfailed at runtime; all `strict=False`, all reasons reference Phase 5. `explicit_none` variant correctly unmarked. |
| `.github/workflows/ci.yml` | single-job CPU-only ubuntu 3.12 PR CI | ✓ VERIFIED | Present, correct structure; no lint/pyright/docs/GPU/codecov steps. |
| CONTRIBUTING.md coverage baseline note | measured % + floor + ratchet | ✓ VERIFIED | §"Coverage baseline": measured 23% (dated + command), floor `--cov-fail-under=21`, Phase-5 ratchet plan. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| ci.yml floor | CONTRIBUTING.md floor | `--cov-fail-under=<N>` token | ✓ WIRED | ci=21, doc=21 — consistent. |
| `--cov` scope | addopts | must stay off addopts | ✓ WIRED | addopts contains no `--cov`; subset run confirmed not to trip gate (Plan 01/02). |
| CI install | committed uv.lock | `uv sync --frozen` | ✓ WIRED | Present in ci.yml; `uv lock --check` passes so frozen install won't drift. |
| suite tracked in git | fresh CI checkout | 3 test modules + rrim.py committed | ✓ WIRED | `git ls-files tests/` lists the three surviving modules; rrim.py tracked. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Scoped suite green | `uv run python -m pytest tests/ -q` | 15 passed, 11 xfailed, 0 failed, 0 errors | ✓ PASS |
| Collection scoped, exit 0 | `uv run pytest --collect-only -q` | exit 0, 26 collected, 0 third_party | ✓ PASS |
| Coverage gate live at floor | `uv run pytest --cov=pc2img --cov-branch --cov-fail-under=21` | exit 0, TOTAL 23%, "Required test coverage of 21% reached. Total coverage: 23.35%" | ✓ PASS |
| Lock in sync | `uv lock --check` | resolved, no drift | ✓ PASS |
| Live CI run on GitHub PR | (needs real PR) | — | ? SKIP → human |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| TEST-01 | 03-01, 03-02 | pytest configuration scopes discovery to `tests/` (stops collecting `third_party/`) | ✓ SATISFIED | testpaths scoping + collect-only exit 0, 0 third_party lines. |
| TEST-02 | 03-01, 03-03 | Coverage measurement + reporting established with a recorded baseline | ✓ SATISFIED | Branch coverage config + tooling installed; 23% baseline recorded in CONTRIBUTING.md with enforced floor 21. |
| CICD-01 | 03-03 | Lightweight CI runs the test suite on pull requests (early safety net) | ✓ SATISFIED (in-codebase) | ci.yml runs scoped suite + coverage gate on pull_request; live trigger confirmation is the deferred human item. |

All three declared requirement IDs are mapped to Phase 3 in REQUIREMENTS.md and marked Complete. No orphaned requirements for this phase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No TBD/FIXME/XXX debt markers in phase-authored files (tests/, ci.yml, CONTRIBUTING.md) | ℹ️ Info | Clean. xfail reason strings reference "Phase 5" as intentional triage tracking (design decision D-01/D-03), not unreferenced debt. |

### Human Verification Required

**1. Live first-PR CI run**

- **Test:** Open a real pull request against `develop-gsd` (or `main`) and confirm the CI workflow triggers, runs, and reports a status check.
- **Expected:** `CI / tests` check appears, installs from frozen lock, runs the scoped suite (15 passed / 11 xfailed), the `--cov-fail-under=21` gate passes (~23%), check reports success.
- **Why human:** GitHub's platform triggering + status-check reporting is an external-service behavior not observable from the codebase. The workflow is verified structurally correct and its exact test command runs green locally; only the live GitHub run remains. Plan 03 recorded this as deferred manual item D4.

### Gaps Summary

No gaps. The test harness is genuinely project-scoped (testpaths=["tests"], zero third_party/ collection, 26 collected, collect exit 0). The green baseline is real (15 passed / 11 xfailed / 0 failed) and reached by triage only — two import-broken modules deleted, current failures parked as `xfail(strict=False)` with Phase-5-pointing reasons, and the previously-untracked suite + rrim.py committed so a fresh checkout is runnable. The coverage gate actually runs and matches the documented floor (ci=21 == doc=21, live "Required test coverage of 21% reached" at 23.35%). The CI workflow is correct: pull_request + develop-gsd/main triggers, ubuntu-latest, fetch-depth 0, frozen lock install, command-line coverage gate, least-privilege permissions, no forbidden steps, release-please.yml untouched.

The only open item is the intentionally-deferred live confirmation that GitHub actually triggers the workflow on a real PR — a platform behavior requiring an actual PR, which the plan itself scheduled as manual (D4). It is surfaced as a human-verification item, not a gap; the in-codebase deliverables for all three success criteria are fully verified.

---

_Verified: 2026-07-09T19:48:11Z_
_Verifier: Claude (gsd-verifier)_
