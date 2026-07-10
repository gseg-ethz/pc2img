---
phase: 4
slug: code-quality-algorithmic-soundness-review
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-10
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Phase 4 is a **review phase**: the primary validation artifact is the set of
> proving-test *sketches* inside `04-FINDINGS.md` (which become Phase 5 tests),
> plus automated smoke/lint gates for the mechanical FIX items (QUAL-01 + D-01).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (`~= 9.1`, dev dependency-group) + coverage (`~= 7.0`) + pytest-cov (`~= 5.0`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `--import-mode=importlib --strict-markers`) + `[tool.coverage.run] branch=true, source=["pc2img"]` |
| **Quick run command** | `.venv/bin/pytest -x -q` |
| **Full suite command** | `.venv/bin/pytest --cov=pc2img --cov-branch` |
| **Lint gate (new, non-blocking this phase)** | `ruff check src/` and `ruff format --check src/` |
| **Estimated runtime** | ~10–20 seconds (Phase-3 suite: 15 passed / 11 xfailed) |

---

## Sampling Rate

- **After every FIX task commit:** `ruff check <touched files>` + `python -c "import <touched module>"`
- **After every plan wave:** full `ruff check src/` + `.venv/bin/pytest -q` — the Phase-3 green suite (15 passed / 11 xfailed) must stay green; **xfails must not flip to unexpected pass** (`--strict-markers`).
- **Before `/gsd-verify-work`:** full suite green AND `04-FINDINGS.md` exists + schema-valid.
- **Max feedback latency:** ~20 seconds.

---

## Per-Task Verification Map

> Task IDs are placeholders until the planner finalizes plan/wave numbering; the
> verification *command* per requirement is what matters for Nyquist sampling.

| Requirement | Wave | Verification | Test Type | Automated Command | File Exists | Status |
|-------------|------|--------------|-----------|-------------------|-------------|--------|
| QUAL-01 (ruff config lands) | W1 | ruff runs against config | lint | `ruff check src/` | ❌ W0 | ⬜ pending |
| QUAL-01 (dup `convert_to_image` removed) | W1 | no F811 redefinition | smoke | `ruff check --select F811 src/pc2img/util.py` (expect clean) | ❌ W0 | ⬜ pending |
| QUAL-01 (metadata non-placeholder) | W1 | keywords/urls corrected | assertion | `python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert d['project']['keywords']!=['one','two']"` | ❌ W0 | ⬜ pending |
| QUAL-01 (matplotlib → extra) | W1 | package imports without matplotlib | smoke | `python -c "import pc2img"` | ❌ W0 | ⬜ pending |
| QUAL-02 (`make_generator` repaired/removed) | W1 | registry imports + factory sound | smoke | `python -c "import pc2img.registry"` | ❌ W0 | ⬜ pending |
| QUAL-02 (`_TransformArray` guarded) | W1 | projection module imports w/o private symbol | smoke | `python -c "import pc2img.strategies.projection"` | ❌ W0 | ⬜ pending |
| QUAL-02 (`__all__` sync) | W1 | barrel public surface matches registry | assertion | `python -c "import pc2img.features as f; assert set(f.__all__)"` | ❌ W0 | ⬜ pending |
| QUAL-02 + QUAL-03 (findings captured) | W-final | FINDINGS artifact + schema | artifact | `test -s .planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS.md` + per-entry schema (id / file:line / severity / pillar / proving-test) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_hygiene.py` — smoke: `import pc2img` + each submodule imports; `pyproject.toml` metadata non-placeholder; `ruff check src/` clean.
- [ ] Framework install: `uv add --group dev "ruff ~= 0.15"` (ruff present on PATH 0.15.12 but not yet declared in `pyproject.toml`).
- [ ] No new fixtures required — FINDINGS proving-tests are authored in **Phase 5**, not here.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| FINDINGS.md completeness (all 4 named anchors present-or-fixed; broad audit ran) | QUAL-02/03 | Requires human/agent judgment on review coverage; not a single assertion | Confirm each of the 4 anchors (make_generator, divergent registries, in-place mutation, dependency-cycle guard) is FIXED-with-smoke or logged with a repro; spot-check math findings against §Pillar 3 reference formulas |
| Placeholder docs URL + license classifier | QUAL-01 | `[ASSUMED]` A2/A3 — ship to PyPI; owner must confirm canonical values | `checkpoint:human-verify` before committing metadata that ships to PyPI |

---

## Validation Sign-Off

- [ ] All FIX tasks have an `<automated>` smoke/lint verify or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (review/refute tasks emit findings fragments checked at synthesis)
- [ ] Wave 0 covers all MISSING references (`tests/test_hygiene.py`, ruff install)
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter (planner/checker to flip once map is complete)

**Approval:** pending
