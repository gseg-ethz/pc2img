---
phase: 06-publication-hardening-downstream-migration-record
plan: 06
subsystem: infra
tags: [github-actions, ci-cd, release-please, pypi, oidc, uv, ruleset, branch-protection]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: ".pre-commit-config.yaml, uv.lock dev-group pre-commit/pyyaml (plans 06-01, 06-02)"
provides:
  - "Assembled .github/ tree (3 required-context CI jobs, ruleset-apply, scheduled-health, release-please, publish-pypi, publish-testpypi) with pc2img's tokens substituted"
  - "release-please-config.json with the stale extra-files key removed; .release-please-manifest.json kept at 0.10.4"
  - "uv-based setup-python-deps composite (D-10 deviation) installing from uv.lock instead of the template's pip-extras install"
affects: ["06-07 (RULESETS.md/RELEASE.md CI/CD adoption record — transcribes these deviations)", "06-08+ (first promotion to main, ruleset apply)"]

# Actuals (#2632)
actuals:
  tokens: 54996
  tasks: 2
  commits: 2
  plan_head_before: 9f992ac6348dd62733c3787c422752768b5dde72
  plan_head_after: 5e35816847884b9f6ce54280c0832e59692c1b67

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "GSEG git-strategy kit assembly: root-to-root component copy (core + release-pypi), token substitution, then repo-specific adaptation at named in-place edit sites"
    - "uv-locked CI environment: setup-python-deps composite runs `uv sync --frozen` and prepends the venv to PATH so every subsequent bare-name tool invocation (pytest, pre-commit, sphinx-build, pyright) resolves into the locked env"

key-files:
  created:
    - .github/workflows/ruleset-apply.yml
    - .github/workflows/scheduled-health.yml
    - .github/workflows/publish-pypi.yml
    - .github/workflows/publish-testpypi.yml
    - .github/rulesets/main.json
    - .github/rulesets/develop.json
    - .github/scripts/ruleset_lib.py
    - .github/scripts/preflight_ruleset_apply.py
    - .github/scripts/check_ruleset_drift.py
    - .github/scripts/check_publish_gate.py
    - .github/scripts/test_ruleset_lib.py
    - .github/scripts/test_preflight_ruleset_apply.py
    - .github/scripts/test_check_ruleset_drift.py
    - .github/scripts/test_classify_changes.py
    - .github/scripts/test_check_publish_gate.py
    - .github/actions/classify-changes/action.yml
  modified:
    - .github/workflows/ci.yml
    - .github/workflows/release-please.yml
    - .github/actions/setup-python-deps/action.yml
    - release-please-config.json
    - .gitignore

key-decisions:
  - "setup-python-deps composite installs with `uv sync --frozen` against the committed uv.lock instead of the kit's `pip install .[dev]` (D-10) — pc2img's dev tooling is a PEP 735 dependency-group, not an extra."
  - "TestPyPI dry run requests attestations (attestations: true, attestations: write) — a recorded deviation from the template's test-index default, so the dry run exercises the full PEP 740 attestation path before the real PyPI publish (D-05)."
  - "release-please-config.json drops the stale extra-files key (pointed at a docs/conf.py that never existed); .release-please-manifest.json is kept unchanged at 0.10.4 rather than overwritten with the kit's fresh-project 0.0.0 placeholder."

requirements-completed: [CICD-02]

coverage:
  - id: D1
    description: "Kit's core tier + release-pypi component assembled root-to-root with every interview token substituted (D-07/D-08/D-09)"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json (verification command (1))"
        status: pass
      - kind: unit
        ref: "uv run --frozen pytest .github/scripts/ -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "setup-python-deps composite installs from the committed uv.lock and puts the venv on PATH (D-10)"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "grep -c 'uv sync --frozen' / 'GITHUB_PATH' / setup-uv sha in .github/actions/setup-python-deps/action.yml"
        status: pass
    human_judgment: false
  - id: D3
    description: "Three in-place edit sites plus the uv-forced edits applied to ci.yml, publish-pypi.yml, publish-testpypi.yml"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "grep-based edits-present / no-pip-paths / triggers-ok / all-sha-pinned checks (plan 06-06 Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Whole shipped tree passes pre-commit run --all-files and the publish containment gate from the locked environment"
    requirement: CICD-02
    verification:
      - kind: integration
        ref: "uv run --frozen pre-commit run --all-files"
        status: pass
      - kind: unit
        ref: "uv run --frozen python .github/scripts/check_publish_gate.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "release-please-config.json has no extra-files key; .release-please-manifest.json still reads 0.10.4"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "jq -e '.packages[\".\"] | has(\"extra-files\") | not' release-please-config.json; git diff --quiet .release-please-manifest.json"
        status: pass
    human_judgment: false

# Metrics
duration: ~11min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 6: GSEG git-strategy kit assembly Summary

**Assembled the GSEG git-strategy kit's core tier + release-pypi component into pc2img's `.github/` tree (3 required-context CI jobs, ruleset-apply, scheduled-health, release automation, TestPyPI/PyPI publish) — placeholder-free, uv-locked, and green on the whole shipped tree.**

## Performance

- **Duration:** ~11 min
- **Completed:** 2026-09-28T14:57Z
- **Tasks:** 2
- **Files modified:** 21 (16 created, 5 modified)

## Accomplishments

- Copied the kit's 14 `core/` files + 6 `optional/release-pypi/` files root-to-root into pc2img (19 files under `.github/` + `release-please-config.json` at repo root), substituting all 14 interview tokens (`<MAIN_BRANCH>` → `main`, `<DEV_BRANCH>` → `develop-gsd`, `<LINT_CONTEXT>` → `Lint (pre-commit)`, `<TEST_CONTEXT>` → `Tests (pytest)`, `<DOCS_CONTEXT>` → `Docs (sphinx -W)`, etc.).
- Kept `.release-please-manifest.json` unchanged at `0.10.4` (did not overwrite with the kit's fresh-project `0.0.0` placeholder); dropped the stale `extra-files: ["docs/conf.py"]` key from `release-please-config.json`.
- Rewrote `.github/actions/setup-python-deps/action.yml` to install from the committed `uv.lock` via `uv sync --frozen` and prepend the venv to `PATH`, instead of the kit's `pip install .[dev]` (pc2img's dev tooling is a PEP 735 dependency-group).
- Applied the three in-place edit sites in `ci.yml`: docs job installs the `doc` group with `uv sync --frozen --group doc`; tests job checks out with `fetch-depth: 0`, points pyright at the locked venv via `python-path`, and carries the `--cov-branch --cov-fail-under=55` coverage floor; lint job's pre-commit step drops the pip-install line (no pip in the uv venv).
- Applied the uv-forced edit to `publish-pypi.yml`/`publish-testpypi.yml`: `uv build` replaces `pip install build && python -m build`.
- Enabled attestations on the TestPyPI dry run (`attestations: true`, `attestations: write`) so the rehearsal exercises the full PEP 740 path before the real PyPI publish — a recorded deviation from the template's test-index default.
- Verified the whole assembled tree: placeholder grep clean, kit's own 83 unit tests green, whole-tree `pre-commit run --all-files` green, publish containment gate clean, full pytest suite green (276 passed, 62.27% coverage, floor 55%).

## Task Commits

Each task was committed atomically:

1. **Task 1: Root-to-root copy of core + release-pypi, token substitution, uv composite** — `e13ca59` (ci)
2. **Task 2: In-place edit sites + uv-forced edits; whole-tree lint and apply-time checks** — `5e35816` (ci)

_Note: this is a `type: execute` plan, not TDD — no test→feat→refactor commit triplet._

## Files Created/Modified

- `.github/workflows/ci.yml` — 3 required-context jobs (`Lint (pre-commit)`, `Tests (pytest)`, `Docs (sphinx -W)`), release-artifact fast path, all 3 in-place edit sites applied
- `.github/workflows/ruleset-apply.yml` — dispatch-only ruleset apply (preflight → mint App token → apply → verify)
- `.github/workflows/scheduled-health.yml` — nightly branch-ancestry assertion
- `.github/workflows/release-please.yml` — replaced wholesale; App-token-authenticated, SHA-pinned, direct push-to-main trigger
- `.github/workflows/publish-pypi.yml` / `publish-testpypi.yml` — OIDC + PEP 740 trusted publishing, `uv build`
- `.github/rulesets/main.json` / `develop.json` — `protect-main` / `protect-develop-gsd` payloads
- `.github/scripts/{ruleset_lib,preflight_ruleset_apply,check_ruleset_drift,check_publish_gate}.py` + 5 test files
- `.github/actions/classify-changes/action.yml` — release-artifact fast-path classifier (copied verbatim)
- `.github/actions/setup-python-deps/action.yml` — rewritten for `uv sync --frozen` (D-10)
- `release-please-config.json` — `extra-files` key removed
- `.gitignore` — re-include `.github/scripts/` (was silently caught by the `[Ss]cripts` virtualenv-template rule); ignore `coverage-unit.xml`

## Decisions Made

- Kept the kit's exact token values per D-08 (already answered at context-gathering; no new decisions needed here).
- `setup-python-deps` composite: `uv sync --frozen` + PATH prepend, not `pip install .[dev]` (D-10, already locked, implemented here).
- TestPyPI dry run: attestations enabled (D-05, already locked, implemented here).
- `.release-please-manifest.json`: kept `0.10.4`, did not copy the kit's `0.0.0` placeholder.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `.gitignore`'s virtualenv-template rule silently shadowed `.github/scripts/`**
- **Found during:** Task 1, staging the copied files for commit
- **Issue:** The repo's `.gitignore` carries a bare `[Ss]cripts` line (a VirtualEnv-template rule meant for nested `venv/Scripts/` bin dirs) with only `!/scripts/` + `!/scripts/**` re-including the top-level `scripts/` source directory. `.github/scripts/` matched the same broad pattern and was silently gitignored — `git status`/`git add` showed nothing under it.
- **Fix:** Added the same re-include/negation pair (`!/.github/scripts/`, `!/.github/scripts/**`) plus a `__pycache__` ignore, mirroring the existing top-level `scripts/` block, with a comment explaining why.
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore -v .github/scripts/ruleset_lib.py` returns nothing after the fix; the 8 files under `.github/scripts/` staged and committed correctly.
- **Committed in:** `e13ca59` (Task 1 commit)

**2. [Rule 1 - Bug] Kit-shipped test fixture's unresolved `<INTEGRITY_CONTEXT>` token defeated the placeholder-grep verification command**
- **Found during:** Task 1, running verification command (1) after token substitution
- **Issue:** `.github/scripts/test_preflight_ruleset_apply.py` (shipped with `core/`) uses the literal token `<INTEGRITY_CONTEXT>` in two test fixtures (`test_the_real_committed_main_payload_resolves_the_anti_skip_context_from_the_target_tip` and its refusal-case sibling) to exercise the preflight's anti-skip logic generically. That token is defined only by the `continuous-enforcement` optional component (declined per D-09), so it has no substitution value in this assembly and is not a real config placeholder — it is deliberately arbitrary fixture data. Left as-is, it made verification command (1)'s blanket `grep -rn '<[A-Z_][A-Z_]*>'` fail on a file no D-08 token table entry covers.
- **Fix:** Substituted the literal `<INTEGRITY_CONTEXT>` (6 occurrences) with the Parameters table's own documented example value, `Integrity (base-ref)` — arbitrary fixture data either way, so this preserves the tests' behavior while satisfying the whole-tree placeholder scan.
- **Files modified:** `.github/scripts/test_preflight_ruleset_apply.py`
- **Verification:** `! grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json` prints `no-placeholders`; `uv run --frozen pytest .github/scripts/test_preflight_ruleset_apply.py -q` still passes (all cases, including the two anti-skip tests).
- **Committed in:** `e13ca59` (Task 1 commit)

**3. [Rule 1 - Bug] Kit-shipped test fixture's tag-pinned action ref defeated the whole-tree sha-pinning check**
- **Found during:** Task 2, running the `all-sha-pinned` apply-time-checklist check
- **Issue:** `.github/scripts/test_check_publish_gate.py`'s `ALLOWED_WORKFLOW` fixture (kit-shipped, unmodified from Task 1) uses `pypa/gh-action-pypi-publish@release/v1` — a tag ref, not a 40-char sha — as test data for the publish-containment gate's "allowed shape" case. The plan's `all-sha-pinned` check scans the whole `.github/` tree for any `uses:` line not pinned to a sha, with no exemption for `.py` test fixtures embedding YAML-as-string.
- **Fix:** Retargeted the fixture's ref to the sha this plan already pins elsewhere (`cef221092ed1bacb1cc03d23a2d87d1d172e277b`, v1.14.0) — the sha value is not asserted by any test in this file, so this is a no-op for test semantics.
- **Files modified:** `.github/scripts/test_check_publish_gate.py`
- **Verification:** `test "$(grep -rhoE 'uses: [^ ]+@[^ ]+' .github/ | grep -v 'uses: \./' | grep -vcE '@[0-9a-f]{40}$')" -eq 0` prints `all-sha-pinned`; `uv run --frozen pytest .github/scripts/test_check_publish_gate.py -q` still passes (17 passed).
- **Committed in:** `5e35816` (Task 2 commit)

**4. [Rule 1 - Bug] New in-place-edit comments introduced planning-vocabulary hits, tripping the whole-tree hygiene gate**
- **Found during:** Task 2, running the full pytest suite (`tests/test_hygiene.py::test_shipped_file_has_no_planning_vocabulary`, a whole-tree gate added by plan 06-01)
- **Issue:** Comments I added documenting the D-10/D-31/D-05/D-16 deviations (and one `.gitignore` comment mentioning "Phase 6") used those planning-ID / phase-reference forms directly, which the hygiene gate rejects on every git-tracked file outside `.planning/`/`.claude/`.
- **Fix:** Reworded every new comment into plain prose ("a recorded deviation from the upstream template" / "the template's own composite" instead of citing `D-10`; dropped the `(D-05)`/`(D-16)`/`(D-10/D-31)` parentheticals; removed "Phase 6" from the `.gitignore` comment) — same treatment plan 06-05 already applied to its own new docs/RTD comments.
- **Files modified:** `.github/actions/setup-python-deps/action.yml`, `.github/workflows/ci.yml`, `.github/workflows/publish-testpypi.yml`, `.gitignore`
- **Verification:** `uv run --frozen pytest tests/test_hygiene.py -q` → 84 passed; full suite re-run green (276 passed).
- **Committed in:** `5e35816` (Task 2 commit)

**5. [Rule 2 - Missing critical] `coverage-unit.xml` (the Tests job's own coverage-report filename) was not gitignored**
- **Found during:** Task 2, running the full-suite verify command
- **Issue:** The kit's Tests job writes coverage to `coverage-unit.xml`, a filename distinct from the `coverage.xml` pc2img's `.gitignore` already covers; running the verify command locally left an untracked generated file.
- **Fix:** Added `coverage-unit.xml` to `.gitignore` next to the existing `coverage.xml` entry; deleted the generated file before committing.
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore -v coverage-unit.xml` confirms it is now ignored; `git status --short` shows no untracked generated files after the verify run.
- **Committed in:** `5e35816` (Task 2 commit)

---

**Total deviations:** 5 auto-fixed (1 Rule 3 blocking, 3 Rule 1 bugs, 1 Rule 2 missing-critical)
**Impact on plan:** All five were necessary to make the plan's own literal `<verify>`/acceptance-criteria commands pass without weakening any actual check — three are known-false-positive shapes in kit-shipped content the plan's grep-based checks did not anticipate (an optional-component-only test token, a test-fixture tag ref, and a generated-artifact filename); one is a hygiene-gate interaction from plan 06-01 that any new shipped-file comment must satisfy; one is a pre-existing `.gitignore` gap that would have silently dropped the new `.github/scripts/` files from every future commit. No scope creep.

## One documented plan-verify discrepancy (not auto-fixed — recorded, not a bug)

Task 2's acceptance criterion `test "$(grep -o 'fetch-depth: 0' .github/workflows/ci.yml | wc -l)" -eq 3` expects exactly 3 occurrences (lint/tests/docs checkout steps). The file actually carries 4: the three real `fetch-depth: 0` configs, plus one pre-existing, kit-shipped prose mention inside the docs job's own version-assertion comment ("The `fetch-depth: 0` above is the fix..."), which the plan's own Task 2 action text explicitly instructs to leave untouched ("leave the version-assertion heredoc and the sphinx-build line untouched"). Editing that comment to force the count to 3 would contradict a more specific instruction in the same task, so this was left as-is and is recorded here rather than silently satisfied. All three real checkout-step configs are present and correct (confirmed by `grep -n`).

## Issues Encountered

None beyond the deviations documented above.

## User Setup Required

None — no external service configuration required by this plan. (Owner account actions — GitHub App installs, secrets, environments — are D-30 checkpoint tasks in later plans of this phase, at the point they are needed.)

## Next Phase Readiness

- The assembled `.github/` tree is placeholder-free, uv-locked, and green (pre-commit, publish gate, kit's own tests, full suite with coverage floor met) on `develop-gsd`'s working tree — ready for plan 06-07 to transcribe these deviations into the `RULESETS.md`/`RELEASE.md` CI/CD adoption record.
- Not yet done (by design, later plans in this phase per D-17/D-18): the ruleset payloads are not yet applied live, no first promotion to `main` has happened, and the D-30 owner-account-action checkpoints (App installs, secrets, environments) have not yet been prompted.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*
