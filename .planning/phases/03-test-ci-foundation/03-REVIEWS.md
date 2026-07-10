---
phase: 3
reviewers: [codex]
reviewed_at: 2026-07-09T18:34:38Z
plans_reviewed: [03-01-PLAN.md, 03-02-PLAN.md, 03-03-PLAN.md]
---

# Cross-AI Plan Review — Phase 3

## Codex Review

## Summary

The three plans are mostly well-scoped and aligned with Phase 3: they add pytest scoping, introduce coverage tooling, triage the existing red suite without production changes, and add a lightweight uv-based CI. The main implementation risk is not the overall approach; it is a few plan-contract inconsistencies and weak verification commands that could let a failed test run look successful. I could not re-run pytest because this session’s filesystem is read-only and `uv` failed creating a cache temp file, so runtime claims are reviewed against the repo files plus the recorded research.

## Plan 03-01 Review

### Strengths

- Correctly targets the missing config surface: `pyproject.toml` currently has no pytest or coverage config, and the dev group is still only `black`, bare `pytest`, and `memory_profiler` at [pyproject.toml](/scratch/31_pc2img/pyproject.toml:57).
- `testpaths = ["tests"]` is the right primary mechanism for TEST-01. `third_party/` is explicitly gitignored at [.gitignore](/scratch/31_pc2img/.gitignore:4), while tests live as top-level `tests/*.py`.
- Keeping `--cov` out of `addopts` is well-designed. The current RRIM test loads modules under a synthetic package name at [tests/test_rrim_features.py](/scratch/31_pc2img/tests/test_rrim_features.py:11), so subset coverage behavior really is likely to be misleading.
- Coverage omitting `_version.py` is justified: setuptools_scm writes it via [pyproject.toml](/scratch/31_pc2img/pyproject.toml:36), and it is gitignored at [.gitignore](/scratch/31_pc2img/.gitignore:2).

### Concerns

- **MEDIUM:** Plan 03-01 pins `pytest ~= 9.1`, but the locked phase decision only names adding `pytest-cov ~= 5.0` and `coverage ~= 7.0` to the existing dev group at [.planning/phases/03-test-ci-foundation/03-CONTEXT.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-CONTEXT.md:83). The research primary recommendation also says to add only those two tools at [.planning/phases/03-test-ci-foundation/03-RESEARCH.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-RESEARCH.md:77). The plan later claims the pytest pin was “resolved by the owner” at [.planning/phases/03-test-ci-foundation/03-01-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-01-PLAN.md:136), but I do not see that decision recorded in `03-CONTEXT.md`.
- **MEDIUM:** The plan-level verification contradicts the wave state. The must-have correctly says collect-only should still have the two D-02 collection errors after Plan 01 at [.planning/phases/03-test-ci-foundation/03-01-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-01-PLAN.md:14), but the final verification says `uv run pytest --collect-only -q` exits 0 at [.planning/phases/03-test-ci-foundation/03-01-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-01-PLAN.md:179). That is not achievable before Plan 02 deletes the broken modules.
- **LOW:** The plan says “three dev pins,” but only two are required by D-07. If pinning pytest is intentional, record it as a decision; otherwise it is avoidable lock churn.

### Suggestions

- Either remove `pytest ~= 9.1` from Plan 03-01 or add an explicit context decision resolving F1.
- Fix Plan 03-01’s final verification to match its task verification: zero non-D-02 errors, not exit-0 collection.
- Add a small TOML parse check for `addopts` and absence of `fail_under`, rather than relying only on prose acceptance.

### Risk Assessment

**MEDIUM.** The technical approach is sound, but the pytest pin decision and the impossible plan-level verification could create execution ambiguity.

## Plan 03-02 Review

### Strengths

- The deletion targets are correctly identified. `tests/test_disk_backed_image_store.py` imports removed/pre-refactor APIs at [tests/test_disk_backed_image_store.py](/scratch/31_pc2img/tests/test_disk_backed_image_store.py:8), and `tests/test_lazy_disk_cache.py` imports `_old.v1.lazy_disk_cache` at [tests/test_lazy_disk_cache.py](/scratch/31_pc2img/tests/test_lazy_disk_cache.py:9).
- The plan avoids blanket-xfail. That matters because `tests/test_disk_backed_image_data.py` has clearly mixed classes, with passing-looking initialization tests at [tests/test_disk_backed_image_data.py](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:20) and targeted failure candidates later at [tests/test_disk_backed_image_data.py](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:116).
- It correctly leaves `test_constructor_normalizes_explicit_none_lazy_disk_cache_config` unmarked; the omitted-config test and explicit-None test are separate at [tests/test_point_cloud_image_generator.py](/scratch/31_pc2img/tests/test_point_cloud_image_generator.py:34) and [tests/test_point_cloud_image_generator.py](/scratch/31_pc2img/tests/test_point_cloud_image_generator.py:46).

### Concerns

- **MEDIUM:** The verification command for Task 2 pipes pytest output to `tail -3` at [.planning/phases/03-test-ci-foundation/03-02-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-02-PLAN.md:139). Without `set -o pipefail`, the command can exit successfully because `tail` succeeds even if pytest fails.
- **LOW:** Task 1’s collect verification greps for the string `error` at [.planning/phases/03-test-ci-foundation/03-02-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-02-PLAN.md:86). That is a brittle proxy for pytest success; pytest’s actual exit code should be checked directly.
- **LOW:** The plan says use `git rm` and commit-scope guidance at [.planning/phases/03-test-ci-foundation/03-02-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-02-PLAN.md:81), but this phase plan does not otherwise discuss commit boundaries. Fine if the executor workflow owns commits, but not necessary for the test outcome.

### Suggestions

- Replace the Task 2 verify with something like `uv run pytest tests/ -q; status=$?; ...; exit $status`, or enable `set -o pipefail`.
- Add an explicit post-edit check that counts xfail marks and ensures `test_constructor_normalizes_explicit_none_lazy_disk_cache_config` has no xfail decorator.
- Keep the “trust live run” instruction; it is the right guard against stale context counts.

### Risk Assessment

**LOW to MEDIUM.** The triage strategy is correct and well bounded. Risk is mainly weak automated verification, not the planned edits.

## Plan 03-03 Review

### Strengths

- It directly satisfies TEST-02 and CICD-01: measure coverage, record the baseline in `CONTRIBUTING.md`, and create `.github/workflows/ci.yml`.
- CI branch triggers match the repo reality: `develop-gsd` exists locally/remotely, while pchandler’s slash form would be wrong. The phase context records the same trigger decision at [.planning/phases/03-test-ci-foundation/03-CONTEXT.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-CONTEXT.md:104).
- `fetch-depth: 0` is justified by setuptools_scm. The package version is dynamic and tag-derived at [pyproject.toml](/scratch/31_pc2img/pyproject.toml:36), and `_version.py` is not source-controlled per [.gitignore](/scratch/31_pc2img/.gitignore:2).
- It correctly avoids lint/pyright/docs/GPU/codecov, matching D-08 and D-12 at [.planning/phases/03-test-ci-foundation/03-CONTEXT.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-CONTEXT.md:89) and [.planning/phases/03-test-ci-foundation/03-CONTEXT.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-CONTEXT.md:111).

### Concerns

- **MEDIUM:** Task 1’s verification also pipes pytest to `grep` at [.planning/phases/03-test-ci-foundation/03-03-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-03-PLAN.md:95). A failing pytest run that still prints a `TOTAL` line could pass the verify unless pipefail is enabled.
- **LOW:** The workflow structural grep checks for `--cov-fail-under` but not that the numeric floor matches `CONTRIBUTING.md`, even though that match is a must-have at [.planning/phases/03-test-ci-foundation/03-03-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-03-PLAN.md:20).
- **LOW:** The CI threat model accepts action tag pinning at [.planning/phases/03-test-ci-foundation/03-03-PLAN.md](/scratch/31_pc2img/.planning/phases/03-test-ci-foundation/03-03-PLAN.md:187). That is acceptable for Phase 3, but adding `permissions: contents: read` would be a cheap hardening improvement for fork PRs.

### Suggestions

- Use `set -o pipefail` or split coverage verification into two commands: run pytest and save output, then grep the saved output.
- Add a YAML parse check, not just grep, if the executor has Python available.
- Add `permissions: contents: read` to the CI workflow.
- Add a simple consistency check that extracts the `--cov-fail-under` value from CI and compares it to the floor recorded in `CONTRIBUTING.md`.

### Risk Assessment

**LOW to MEDIUM.** The CI shape is appropriate and scoped. The remaining risk is verification quality and minor hardening, not phase-goal coverage.

## Overall Risk Assessment

**MEDIUM.** The plans should achieve the Phase 3 goals with modest edits, and the sequencing is logical: config/tooling, green-by-triage, then coverage baseline plus CI. Before execution, I would fix the Plan 03-01 pytest-pin decision ambiguity and replace the pipe-based verification commands so failures cannot be hidden by `grep` or `tail`.

---

## Consensus Summary

Only one external reviewer (Codex, `codex-cli 0.142.2`) was invoked for this
phase, so this section reflects Codex's findings rather than cross-reviewer
consensus. Codex reviewed the plans against the live working tree and grounded
its findings in concrete `file:line` evidence (it could not re-run `pytest`
because the sandbox filesystem was read-only, so runtime claims were checked
against repo files + recorded research rather than execution).

### Agreed Strengths

- Sound overall approach and sequencing: config/tooling (03-01) → green-by-triage
  (03-02) → coverage baseline + CI (03-03).
- Correct, evidence-backed technical choices: `testpaths = ["tests"]` for TEST-01,
  keeping `--cov` out of `addopts`, omitting `_version.py` from coverage,
  `develop-gsd` CI trigger, and `fetch-depth: 0` for setuptools_scm.
- Triage targets in 03-02 are correctly identified (import-broken modules) and the
  plan avoids blanket-xfail on mixed-status test modules.

### Agreed Concerns (highest priority)

1. **HIGH-value / MEDIUM-severity — Pipe-based verification can hide failures.**
   Across 03-02 (Task 2, `... | tail -3`) and 03-03 (Task 1, `... | grep TOTAL`),
   verification commands pipe `pytest` output without `set -o pipefail`, so a
   failing test run can exit 0 because `tail`/`grep` succeed. This is the single
   most repeated concern and undermines the "green suite" success criterion.
2. **MEDIUM — 03-01 `pytest ~= 9.1` pin is undecided.** The locked context (D-07)
   and research recommend adding only `pytest-cov ~= 5.0` and `coverage ~= 7.0`;
   the plan's claim that the pytest pin was "resolved by the owner" is not
   recorded in `03-CONTEXT.md`. Either drop the pin or record the decision.
3. **MEDIUM — 03-01 plan-level verification is impossible at its wave.** The final
   verification asserts `uv run pytest --collect-only -q` exits 0, but the plan's
   own must-have says the two D-02 collection errors still exist until Plan 02
   deletes the broken modules. The verification should assert "zero non-D-02
   errors," not exit-0 collection.

### Divergent Views

Not applicable — a single reviewer was run. To obtain genuine cross-AI consensus,
re-run `/gsd-review --phase 3` with an additional reviewer (e.g. `--gemini`).

### Suggested Hardening (LOW)

- Add `permissions: contents: read` to `.github/workflows/ci.yml` (cheap fork-PR hardening).
- Add a consistency check that the CI `--cov-fail-under` value matches the floor recorded in `CONTRIBUTING.md`.
- Prefer direct exit-code / TOML / YAML parse checks over string greps in verifications.
