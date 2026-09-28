---
phase: "6"
slug: "publication-hardening-downstream-migration-record"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-28"
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ~=9.1 + pytest-cov ~=5.0 (plus the kit-shipped `.github/scripts/test_*.py` once assembled) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run --frozen pytest -q` |
| **Full suite command** | `uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing --cov-fail-under=55` |
| **Estimated runtime** | ~60 seconds (baseline 2026-09-28: 196 passed, coverage 62.27%) |

Non-pytest gates used in this phase (see 06-RESEARCH.md § Validation Architecture):

- Whole-shipped-tree lint: `ruff check` + `ruff format --check` over `git ls-files` minus `.planning/` and `.claude/` (later: `pre-commit run --all-files`)
- Docs: `sphinx-build -W --keep-going -b html docs/source docs/_build/html`
- Token-residue: `! grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json`
- Planning-vocabulary gate: the sweep regex over all tracked paths minus `.planning/`, `.claude/` and the D-23 exemption
- Build: `uv build` + `twine check dist/*`
- Migration record: extract and run the `## Verifier (inline)` block of `MIGRATION-v0.11.md`

---

## Sampling Rate

- **After every task commit:** Run `uv run --frozen pytest -q` plus ruff on touched files
- **After every plan wave:** Run the full suite, the whole-tree ruff pass and (once assembled) `pytest .github/scripts/ -q`
- **Before `/gsd-verify-work`:** Full suite green, Sphinx `-W` green, migration verifier green, apply-time checklist evidence recorded
- **Max feedback latency:** 120 seconds (local); CI-run and GitHub-API evidence is sampled at the checkpoint that produces it

---

## Per-Task Verification Map

*Filled in by the planner/executor once PLAN.md task IDs exist.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 6-TBD | TBD | TBD | CICD-02 / BC-01 | — | — | — | — | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/source/conf.py` + `docs/source/index.rst`: the Sphinx site (D-13)
- [ ] `.pre-commit-config.yaml`: the lint job definition (D-11)
- [ ] `MIGRATION-v0.11.md` with its inline verifier (BC-01 draft)
- [ ] `CITATION.cff` (D-14)
- [ ] Kit `.github/scripts/test_*.py`: run once after assembly against pc2img's tokens

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| App installs + secrets (codecov, gseg-ruleset-admin, gseg-release-please) | CICD-02 | Owner account action (D-30) | Checkpoint prompt with exact values; the next task verifies via a CI run or `gh api` |
| RTD project import | CICD-02 | Owner account action (D-30) | After import, verify the RTD build status via its API/badge |
| TestPyPI trusted publisher + `testpypi` environment | CICD-02 | Owner account action (D-30) | Dispatch the dry run; verify the upload + PEP 740 attestation on TestPyPI |
| Nightly ancestry assertion observed passing once | CICD-02 | Scheduled workflow; needs a real run | `gh run list --workflow <ancestry workflow>` shows a success |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
