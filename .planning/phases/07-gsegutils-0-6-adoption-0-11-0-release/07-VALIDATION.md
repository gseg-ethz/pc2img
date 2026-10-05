---
phase: "7"
slug: "gsegutils-0-6-adoption-0-11-0-release"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-01"
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `07-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ~= 9.1 (`--import-mode=importlib --strict-markers`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run --frozen pytest tests/test_image_store.py -q` |
| **Full suite command** | `uv run --frozen pytest -m "not benchmark" --cov=pc2img --cov-branch --cov-fail-under=55` |
| **Estimated runtime** | ~120 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `uv run --frozen pytest tests/test_image_store.py -q` (plus `uv run --frozen pytest .github/scripts/ -q` for CI-script tasks)
- **After every plan wave:** Run the full suite command and the inline migration verifier
- **Before `/gsd-verify-work`:** Full suite green, D-03 unlocked-wheel run green, verifier green, phase-diff review artifact present
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

To be filled by the planner / executor from the PLAN.md task IDs. Requirement → command seed:

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| DEP-05 / SC1 pin | GSEGUtils 0.6.x locked, not a cached 0.5.x | provenance | `uv lock --check` + in-process `GSEGUtils.__version__` / fingerprint assert | ❌ W0 | ⬜ pending |
| DEP-05 / SC1 delete | withdrawn names gone | grep gate | `git grep -nE '_get_npy_path\|_get_meta_path\|_assert_within_cache_dir' -- src tests` (expect exit 1) | ✅ | ⬜ pending |
| DEP-05 / SC1 re-pin | no file outside cache dir on every route | unit | `uv run --frozen pytest tests/test_image_store.py -k "escaping or refused" -q` | ❌ W0 | ⬜ pending |
| SC2 | containment exception is `ValueError`-compatible, recorded as BC | unit + verifier | escape tests + inline verifier `[ok]` | ✅ | ⬜ pending |
| SC3 | no leaked `tmp*` entries; absent-key test folded | suite + shell | `TMPDIR=$(mktemp -d) uv run --frozen pytest -q; ls $TMPDIR \| grep -v '^pytest-of' \| wc -l` = 0 | ❌ W0 | ⬜ pending |
| SC4 / BC-01 | record finalised, `target_ref: "v0.11.0"`, verifier green | verifier | inline verifier extraction + run | ✅ | ⬜ pending |
| D-03 | built wheel passes suite in unlocked env | one-shot | recipe in RESEARCH § Code Examples | ❌ W0 | ⬜ pending |
| D-13/D-14/D-15 | RTD + publish gate + preflight shapes | unit / simulation | `uv run --frozen pytest .github/scripts/ -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Rewrite/rename the 12 failing tests in `tests/test_image_store.py` (5 renames, 7 semantic)
- [ ] Autouse `tempfile.tempdir -> tmp_path` fixture in `tests/conftest.py`
- [ ] `n_jobs>=2` tiled regenerate test (depends on the owner's tiled-race decision)
- [ ] AR-07/AR-08 shape tests in `.github/scripts/`
- [ ] D-03 and RTD simulation scripts (plan verification steps, outside `tests/`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Filtered promotion, release PR publish with attestations, merge-commit back-merge, nightly ancestry green | SC5 | Owner-only GitHub/PyPI account actions | RELEASE.md steps; `git merge-base --is-ancestor origin/main origin/develop-gsd`; `curl -s https://pypi.org/pypi/pc2img/0.11.0/json` |
| Phase diff reviewed | SC3 | Review process | `/gsd-code-review 7`, then `/gsd-consolidate-findings` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
