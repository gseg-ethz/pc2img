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
| 06-01-T1 | 06-01 | 1 | CICD-02 | T-06-01 | planning vocabulary cannot reach shipped files | pytest gate (parametrized) | `uv run --frozen pytest tests/test_hygiene.py -q -k "planning_vocabulary and smoke_pipeline"` | ❌ W0 (gate authored by this task) | ⬜ pending |
| 06-01-T2 | 06-01 | 1 | CICD-02 | T-06-01 | shipped text accurate, no planning ids | pytest gate + full suite | `uv run --frozen pytest tests/test_hygiene.py -q -k planning_vocabulary` ; `uv run --frozen pytest -q` | ✅ (after T1) | ⬜ pending |
| 06-01-T3 | 06-01 | 1 | CICD-02 | T-06-SC | lock consistent with new groups | uv lock check + import probe | `uv lock --check` ; `uv run --frozen python -c "import sphinx, sphinx_rtd_theme, yaml, pre_commit"` | ✅ | ⬜ pending |
| 06-02-T1 | 06-02 | 1 | CICD-02 | T-06-04 | signoff excluded from fixers | pre-commit run (scoped) | `uvx pre-commit run --files .pre-commit-config.yaml setup.py .gitattributes tests/test_tiled_generator.py tests/test_point_cloud_image_generator.py` | ❌ W0 (config authored by this task) | ⬜ pending |
| 06-02-T2 | 06-02 | 1 | CICD-02 | T-06-06 | ruff clean without weakening rules | ruff + pytest | `ruff check $(git ls-files 'src/*.py' 'tests/*.py' 'setup.py') --statistics` | ✅ | ⬜ pending |
| 06-03-T1 | 06-03 | 1 | CICD-02 | T-06-08 | long description renders | build + twine | `rm -rf dist && uv build && uvx twine check dist/*` | ✅ | ⬜ pending |
| 06-03-T2 | 06-03 | 1 | CICD-02 | T-06-07 | single author, valid CFF | yaml assertions | `uv run --no-project --with pyyaml python -c "..."` (see plan) | ❌ W0 (file authored by this task) | ⬜ pending |
| 06-04-T1 | 06-04 | 1 | BC-01 | T-06-10 | verifier has teeth (empty guard) | inline verifier | extraction command + `uv run --frozen python /tmp/pc2img-migration-verifier.py` | ❌ W0 (record authored by this task) | ⬜ pending |
| 06-04-T2 | 06-04 | 1 | BC-01 | T-06-10 | ids unique/monotonic, rows mirrored | inline verifier + grep | same verifier ; row-count/uniqueness grep | ✅ (after T1) | ⬜ pending |
| 06-04-T3 | 06-04 | 1 | BC-01 | T-06-11 | Tier-2 runtime checks, no planning ids | inline verifier + regex | same verifier ; vocabulary regex | ✅ | ⬜ pending |
| 06-05-T1 | 06-05 | 2 | CICD-02 | T-06-13 | dynamic version, doc group install | sphinx -W + check-yaml | `uv sync --frozen --group doc && uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html` | ❌ W0 (docs authored by this task) | ⬜ pending |
| 06-05-T2 | 06-05 | 2 | CICD-02 | T-06-12 | -W green full tree | sphinx -W + pytest + ruff | same sphinx command ; `uv run --frozen pytest -q` | ✅ | ⬜ pending |
| 06-06-T1 | 06-06 | 2 | CICD-02 | T-06-14, T-06-SC | no placeholder, kit tests green | grep + pytest | `! grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json` ; `uv run --frozen pytest .github/scripts/ -q` | ✅ (kit-shipped tests) | ⬜ pending |
| 06-06-T2 | 06-06 | 2 | CICD-02 | T-06-15, T-06-16, T-06-17 | least privilege, sha pins, no pull_request_target, publish containment | pre-commit + grep gates + publish gate | `uv run --frozen pre-commit run --all-files` ; `uv run --frozen python .github/scripts/check_publish_gate.py` | ✅ | ⬜ pending |
| 06-07-T1 | 06-07 | 3 | CICD-02 | T-06-19 | evidence, never checkmarks | pytest gate + grep | `uv run --frozen pytest tests/test_hygiene.py -q -k "planning_vocabulary and RULESETS"` | ✅ | ⬜ pending |
| 06-07-T2 | 06-07 | 3 | CICD-02 | T-06-21 | claim tuples match workflows | gate + diff | env-name diff between RELEASE.md and publish workflows | ✅ | ⬜ pending |
| 06-07-T3 | 06-07 | 3 | CICD-02 | — | whole tree gated before promotion | full gate set | suite+floor ; pre-commit ; sphinx -W ; verifier ; lock ; build+twine | ✅ | ⬜ pending |
| 06-08-T1 | 06-08 | 4 | CICD-02 | T-06-23 | archive tag pushed before delete | git remote reads | `git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' origin/develop-gsd` | n/a (remote state) | ⬜ pending |
| 06-08-T2 | 06-08 | 4 | CICD-02 | T-06-22 | secrets never logged | human-action checkpoint | `gh secret list --repo gseg-ethz/pc2img` | n/a | ⬜ pending |
| 06-08-T3 | 06-08 | 4 | CICD-02 | T-06-25 | merge only on green checks | gh pr checks + git | `gh pr checks <n> --json name,state` ; two-parent assertion | n/a | ⬜ pending |
| 06-09-T1 | 06-09 | 5 | CICD-02 | T-06-27 | separate release App credentials | human-action checkpoint | `gh secret list --repo gseg-ethz/pc2img` | n/a | ⬜ pending |
| 06-09-T2 | 06-09 | 5 | CICD-02 | T-06-26 | strip list applied, footers present | git tree/message assertions | promotion worktree checks (see plan) | n/a | ⬜ pending |
| 06-10-T1 | 06-10 | 6 | CICD-02 | T-06-45 | human go/no-go immediately before the one-way push | decision checkpoint (blocking-human) | — (human) | n/a | ⬜ pending |
| 06-10-T2 | 06-10 | 6 | CICD-02 | T-06-33, T-06-34 | release PR by App, unmerged | gh reads | `gh pr list --base main --state open ...` ; run conclusion | n/a | ⬜ pending |
| 06-10-T3 | 06-10 | 6 | CICD-02 | T-06-30, T-06-31 | bypass_actors empty, preflight before write | jq + drift comparator | `check_ruleset_drift.py "protect-main:..."` | ✅ (kit script) | ⬜ pending |
| 06-11-T1 | 06-11 | 7 | CICD-02 | T-06-46, T-06-47 | develop ruleset + idempotent apply | jq + comparator + 3 run conclusions | `check_ruleset_drift.py "protect-develop-gsd:..."` | ✅ | ⬜ pending |
| 06-11-T2 | 06-11 | 7 | CICD-02 | T-06-35, T-06-36 | true merge, clean merge-tree | git ancestry | `git merge-base --is-ancestor origin/main origin/develop-gsd` | n/a | ⬜ pending |
| 06-11-T3 | 06-11 | 7 | CICD-02 | T-06-37 | nightly observed once | gh run log | dispatched run conclusion + OK line grep (+ human-check for first cron run) | n/a | ⬜ pending |
| 06-12-T1 | 06-12 | 8 | CICD-02 | T-06-40 | RTD import | human-action checkpoint | badge 200 | n/a | ⬜ pending |
| 06-12-T2 | 06-12 | 8 | CICD-02 | T-06-39 | RTD build proves group install | curl badge/site + gh api | badge contains passing ; site 200 ; environment testpypi | n/a | ⬜ pending |
| 06-12-T3 | 06-12 | 8 | CICD-02 | T-06-38 | exact publisher tuple | human-action checkpoint | proven by 06-13-T1 | n/a | ⬜ pending |
| 06-13-T1 | 06-13 | 9 | CICD-02 | T-06-41, T-06-42, T-06-44 | OIDC + PEP 740, production untouched | gh runs + integrity endpoint | two run conclusions ; provenance 200 per file ; pypi.org 404 | n/a | ⬜ pending |
| 06-13-T2 | 06-13 | 9 | CICD-02, BC-01 | T-06-43 | closing state read live | gh/git/jq + verifier on main | rulesets re-read + comparator ; verifier from `origin/main:MIGRATION-v0.11.md` | n/a | ⬜ pending |
| 06-13-T3 | 06-13 | 9 | CICD-02 | — | bookkeeping only (.planning) | file assertions | todo path/grep checks | ✅ | ⬜ pending |

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
