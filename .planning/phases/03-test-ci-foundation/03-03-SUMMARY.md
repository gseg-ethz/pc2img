---
phase: 03-test-ci-foundation
plan: 03
subsystem: ci-cd
tags: [coverage, ci, github-actions, uv, cov-fail-under, baseline, regression-ratchet]

# Dependency graph
requires:
  - phase: 03-test-ci-foundation
    plan: 01
    provides: "[tool.pytest.ini_options] scoping + branch-coverage [tool.coverage.*] config + pinned pytest-cov 5.0 / coverage 7.0"
  - phase: 03-test-ci-foundation
    plan: 02
    provides: "green scoped tests/ suite (15 passed / 11 xfailed / 0 failed) committed so a fresh CI checkout has a suite to run"
provides:
  - "durable coverage baseline record in CONTRIBUTING.md (measured 23%, enforced floor --cov-fail-under=21, Phase-5 ratchet plan)"
  - ".github/workflows/ci.yml — single-job CPU-only ubuntu-latest Python-3.12 PR CI running the scoped suite with branch coverage + the --cov-fail-under=21 gate"
  - "the CI gate installs from the committed uv.lock via uv sync --frozen (exercises the Phase-2 lock as part of the safety net)"
affects: [phase-05-bugfix-coverage, phase-06-publication-hardening, ci-cd]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "coverage gate on the CI command line only (--cov-fail-under=21), never in addopts/pyproject — subset runs stay fast"
    - "floor recorded as the literal grep-able token --cov-fail-under=<N> in BOTH ci.yml and CONTRIBUTING.md so the two cannot drift"
    - "single immutable-tag-pinned actions (checkout@v5, setup-uv@v8.3.2, upload-artifact@v4); SHA-pinning deferred to Phase 6"
    - "least-privilege top-level permissions: contents: read (fork-PR hardening, T-03-04)"

key-files:
  created:
    - .github/workflows/ci.yml
  modified:
    - CONTRIBUTING.md

key-decisions:
  - "measured baseline is 23% (observed on the green suite; RESEARCH measured 24% on 2026-07-09) — used the observed value, did NOT chase the number upward"
  - "enforced floor set to 21 (2 points below baseline) for headroom against xfail coverage volatility (D-06 regression ratchet)"
  - "push triggers restricted to develop-gsd (HYPHEN) + main; pull_request fires on all PRs (D-10)"
  - "no lint/pre-commit/pyright/docs/GPU/codecov steps (D-08/D-12; codecov is Phase 6) — mirror only pchandler's pytest --cov core"
  - "top-level permissions: contents: read added for least-privilege fork-PR hardening (T-03-04)"

patterns-established:
  - "coverage floor lives as a grep-able --cov-fail-under=<N> token in both ci.yml and CONTRIBUTING.md; a floor-consistency verify fails if they diverge"
  - "CI installs strictly from the committed lock (uv sync --frozen) so lock-drift fails the job rather than resolving fresh (T-03-SC)"

requirements-completed: [TEST-02, CICD-01]

coverage:
  - id: D1
    description: "coverage baseline measured on the green suite and durably recorded with the enforced floor and Phase-5 ratchet plan"
    requirement: "TEST-02"
    verification:
      - kind: automated
        ref: "uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing -> pytest_exit=0, TOTAL ... 23%, COVERAGE_RUN_GREEN"
        status: pass
      - kind: automated
        ref: "grep -in 'coverage baseline' CONTRIBUTING.md -> BASELINE_NOTE_PRESENT; grep --cov-fail-under=21 present"
        status: pass
    human_judgment: false
  - id: D2
    description: "single-job CPU-only ci.yml runs the scoped suite with branch coverage + --cov-fail-under gate on PRs and pushes to develop-gsd/main"
    requirement: "CICD-01"
    verification:
      - kind: automated
        ref: "structural grep (pull_request, develop-gsd, main, runs-on ubuntu-latest, fetch-depth 0, uv sync --frozen, --cov-fail-under) -> CI STRUCTURE OK"
        status: pass
      - kind: automated
        ref: "yaml.safe_load parse (system python3): permissions=={contents: read}, push branches [develop-gsd, main], pull_request in on -> SYS_YAML_PARSE_OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "CI --cov-fail-under value equals the floor recorded in CONTRIBUTING.md"
    requirement: "TEST-02"
    verification:
      - kind: automated
        ref: "floor-consistency extract of --cov-fail-under=<N> from both files -> ci_floor=21 doc_floor=21 FLOOR_CONSISTENT"
        status: pass
    human_judgment: false
  - id: D4
    description: "live-run CI pass/fail confirmation on the first real PR"
    requirement: "CICD-01"
    verification:
      - kind: manual
        ref: "first PR run of .github/workflows/ci.yml on GitHub (per VALIDATION.md Manual-Only table)"
        status: deferred
    human_judgment: true

# Metrics
duration: 2min
completed: 2026-07-09
status: complete
---

# Phase 3 Plan 3: Coverage Baseline + Lightweight PR CI Summary

**Recorded the coverage baseline durably (measured 23% on the green suite, enforced floor `--cov-fail-under=21`) in CONTRIBUTING.md and stood up a single-job CPU-only `ci.yml` that runs the scoped pytest suite with branch coverage + the fail-under gate on every PR and on pushes to `develop-gsd`/`main`, installing strictly from the committed `uv.lock`.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-07-09T19:32:40Z
- **Completed:** 2026-07-09T19:34:20Z
- **Tasks:** 2
- **Files created/modified:** 2 (1 created, 1 modified)

## Accomplishments

- **Measured the baseline on the now-green suite.** `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` reports `TOTAL … 23%` with `15 passed, 11 xfailed, 0 failed` (`pytest_exit=0`, `COVERAGE_RUN_GREEN`). RESEARCH measured 24% on 2026-07-09; the re-measure observed 23%, and per the plan I used the observed value rather than chasing the number upward. `rrim.py` shows 0% because `test_rrim_features.py` loads it under a throwaway module name — expected, a Phase-5 concern that depresses the whole-package baseline.
- **Recorded the baseline durably (D-06).** Added a "Coverage baseline" section to `CONTRIBUTING.md` stating the measured 23%, the measurement date + command, the enforced floor as the grep-able literal `--cov-fail-under=21`, the note that CI (not `pyproject.toml`) enforces it, and the Phase-5 ratchet plan. Also documented the `pytest` / `pytest tests/…` (never `pytest .`) guidance and that `--cov` is deliberately kept out of `addopts` so subset runs stay fast.
- **Set the floor 2 points below baseline.** `21` gives headroom against xfail coverage volatility (xfail'd tests execute up to their failure line, so their contribution can shift). The same `--cov-fail-under=21` token appears in both `CONTRIBUTING.md` and `ci.yml`, so a floor-consistency verify fails if they ever drift — confirmed `ci_floor=21 doc_floor=21 FLOOR_CONSISTENT`.
- **Stood up the lightweight PR CI (`.github/workflows/ci.yml`).** `name: CI`, single `tests` job, `runs-on: ubuntu-latest`, no matrix (requires-python pins `~=3.12,<3.13`). Triggers: `pull_request` (all PRs) + `push` restricted to `develop-gsd` (HYPHEN, not pchandler's `develop/gsd` slash form) and `main`. Steps: `actions/checkout@v5` with `fetch-depth: 0` (setuptools_scm needs tags; `_version.py` is gitignored) → `astral-sh/setup-uv@v8.3.2` (Python 3.12, cache) → `uv sync --frozen` (installs from the committed lock) → `uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=21` → `actions/upload-artifact@v4` (`if: always()`) uploading `coverage.xml` as a plain artifact. No lint/pre-commit/pyright/docs/GPU/codecov steps.
- **Applied least-privilege hardening (T-03-04).** Top-level `permissions: contents: read` narrows `GITHUB_TOKEN` to read-only so a fork PR / compromised action cannot mutate the repo.

## Task Commits

Each task was committed atomically (conventional functional scopes, no GSD planning-ID tags):

1. **Task 1: Measure the coverage baseline, set the floor, record it in CONTRIBUTING.md** — `8ec8cf2` (`docs(contributing):`)
2. **Task 2: Create the lightweight PR CI workflow (.github/workflows/ci.yml)** — `23ed550` (`ci(github):`)

## Files Created / Modified

- **Created:** `.github/workflows/ci.yml` — single-job CPU-only CI (checkout fetch-depth 0 → setup-uv → `uv sync --frozen` → scoped `pytest --cov … --cov-fail-under=21` → upload `coverage.xml`); top-level `permissions: contents: read`.
- **Modified:** `CONTRIBUTING.md` — new "Coverage baseline" section (measured 23%, floor `--cov-fail-under=21`, Phase-5 ratchet) plus the `pytest .` caveat and the `--cov`-not-in-`addopts` note.

## Threat Model Coverage

The plan's `<threat_model>` mitigations were all applied in the delivered `ci.yml`:

- **T-03-02 (Information Disclosure, fork-PR CI):** job uses NO secrets; `coverage.xml` uploaded as a plain artifact, not to a token-gated service. Mitigated.
- **T-03-03 (Tampering, third-party actions):** pinned to current immutable tags (`@v5`, `@v8.3.2`, `@v4`); full SHA-pinning is an explicit Phase-6 concern. Accepted as planned.
- **T-03-04 (Elevation of Privilege, GITHUB_TOKEN):** explicit top-level `permissions: contents: read`. Mitigated (asserted present by the YAML parse: `perms={'contents': 'read'}`).
- **T-03-SC (Tampering, install path):** CI installs strictly from the committed lock via `uv sync --frozen`; lock-drift fails the job. Mitigated.

## Decisions Made

- **Baseline = 23% (observed), floor = 21.** Used the re-measured value rather than RESEARCH's 24%; set the floor 2 points below for xfail headroom (D-05 whole-package branch coverage; D-06 regression ratchet). The floor is a regression guard, not a coverage target — ratcheted in Phase 5.
- **push triggers = `develop-gsd` (hyphen) + `main`; `pull_request` = all PRs (D-10).** Deliberately avoided pchandler's `develop/gsd` slash form, which would silently never fire on the integration branch's direct pushes.
- **No lint/pyright/docs/GPU/codecov (D-08/D-11/D-12).** Mirror only pchandler's `pytest --cov` core; codecov is Phase 6, SHA-pinning + branch-protection are Phase 6.

## Deviations from Plan

None — plan executed exactly as written.

The one nuance worth recording: Task 2's second verify (`yaml.safe_load` inside the project `uv run python`) printed `YAML_LIB_ABSENT_SKIP_PARSE` because PyYAML is not in the project venv — the plan's own acceptance criteria treats this as an acceptable fallback (structural grep covers the same keys). For extra assurance I additionally parsed the file with the system `python3` (which has PyYAML): `permissions={'contents': 'read'}`, `push branches=['develop-gsd', 'main']`, `pull_request in on == True`, `SYS_YAML_PARSE_OK`. So the YAML was verified as well-formed and structurally correct despite the in-venv skip.

## Scope Boundary Honored

Every `git add` was scoped to exactly the two files this plan produces (`CONTRIBUTING.md`, `.github/workflows/ci.yml`) plus the planning/tracking files in the final docs commit. Left untracked as required: `scripts/v1.0/`, `scripts/v2.0/`, the numbered `scripts/0X_*.py`, `_tests/`, `.vscode/`, `.codex`, `pyrightconfig.json`, `.editorconfig`, the modified `.planning/config.json`, and `src/pc2img/features/rrim.py` (already tracked from Plan 02). `.github/workflows/release-please.yml` was not touched.

## Verification Results

- **Task 1:** `pytest_exit=0`, `TOTAL … 23%`, `COVERAGE_RUN_GREEN`; `grep -in 'coverage baseline' CONTRIBUTING.md` → `BASELINE_NOTE_PRESENT`; floor token `--cov-fail-under=21` present.
- **Task 2:** `CI STRUCTURE OK` (structural grep: pull_request, develop-gsd, main, runs-on ubuntu-latest, fetch-depth 0, uv sync --frozen, --cov-fail-under); `SYS_YAML_PARSE_OK` (system python3 parse: permissions contents:read, push branches [develop-gsd, main], pull_request present); `FLOOR_CONSISTENT` (`ci_floor=21 doc_floor=21`); `NO_FORBIDDEN_STEPS_OK` (no lint/pre-commit/pyright/codecov/docs/gpu/cuda/matrix); `release-please.yml` unchanged.

## Next Phase Readiness

- **TEST-02 complete:** coverage is measurable, measured, and durably recorded with an enforced floor.
- **CICD-01 complete:** the lightweight PR CI safety net exists and gates every PR + mainline push.
- **Manual follow-up (D4, deferred):** live confirmation that CI passes on the first real PR (per VALIDATION.md Manual-Only table) — cannot be verified without a GitHub PR.
- **Phase 5 handoff:** ratchet the floor upward as bug-fix tests flip xfail→pass and `rrim.py` gets attributed coverage.
- **Phase 6 handoff:** SHA-pin the actions, add branch protection, wire codecov (all explicitly deferred).
- No blockers.

## Self-Check: PASSED

- FOUND: CONTRIBUTING.md
- FOUND: .github/workflows/ci.yml
- FOUND: commit 8ec8cf2 (Task 1)
- FOUND: commit 23ed550 (Task 2)
- CONFIRMED UNCHANGED: .github/workflows/release-please.yml

---
*Phase: 03-test-ci-foundation*
*Completed: 2026-07-09*
