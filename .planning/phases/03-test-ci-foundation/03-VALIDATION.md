---
phase: 3
slug: test-ci-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `03-RESEARCH.md` §"Validation Architecture". Phase 3 authors **no
> new test code** (real coverage is Phase 5) — Wave 0 is config + CI only.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.x (`~= 9.1`) + pytest-cov `~= 5.0` / coverage `~= 7.0` (added this phase) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` + `[tool.coverage.*]` (both new this phase) |
| **Quick run command** | `uv run pytest` |
| **Full suite command** | `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` |
| **Estimated runtime** | ~10 seconds (26-test scoped suite, pre-xfail) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest` (fast green/red signal, no coverage)
- **After every plan wave:** Run `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` (green **and** ≥ floor)
- **Before `/gsd-verify-work`:** Full suite green + `--cov-fail-under` passes + `ci.yml` structural check passes
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

Phase 3 is config + CI wiring; tasks are authored by the planner. Each success
criterion has a concrete, command-checkable verification point:

| SC | Requirement | Verification point (command) | Pass condition | File Exists | Status |
|----|-------------|------------------------------|----------------|-------------|--------|
| 1 | TEST-01 | `uv run pytest --collect-only -q` (repo root) | Exit 0; only `tests/…` listed; **zero** `third_party/*` ERROR lines; collected count == 3-module total | ❌ W0 (`[tool.pytest.ini_options]`) | ⬜ pending |
| 2 | TEST-02 | `uv run pytest --cov=pc2img --cov-branch --cov-report=term-missing` | `TOTAL … NN%` line emitted; `--cov-fail-under` present; baseline note recorded in `CONTRIBUTING.md` | ❌ W0 (`[tool.coverage.*]`, dev group) | ⬜ pending |
| 3 | CICD-01 | `test -f .github/workflows/ci.yml` + structural grep | File exists; `on:` has `pull_request` + `push.branches` incl. `develop-gsd` + `main`; a step runs `uv run … pytest … --cov-fail-under`; `runs-on: ubuntu-latest` | ❌ W0 (`ci.yml`) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` `[tool.pytest.ini_options]` — did not exist; created this phase (covers SC1).
- [ ] `pyproject.toml` `[tool.coverage.run]` / `[tool.coverage.report]` — did not exist; created this phase (covers SC2).
- [ ] `pytest ~= 9.1` (existing 9.1.1, now pinned) + `pytest-cov ~= 5.0` + `coverage ~= 7.0` — added to `[dependency-groups].dev`; `uv.lock` regenerated (covers SC2 + keeps CI `--frozen` valid).
- [ ] `.github/workflows/ci.yml` — did not exist; created this phase (covers SC3).
- [ ] `CONTRIBUTING.md` coverage-baseline note — durable record of the measured baseline (covers SC2).

*No new test code is authored this phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI actually runs & reports pass/fail on a real PR | CICD-01 | GitHub Actions only fires on a live PR/push event; cannot be triggered from a local checkout | Structural check of `ci.yml` is automated; the live-run observation happens on the first PR opened after merge (or a `workflow_dispatch`/`act` dry run) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
