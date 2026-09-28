---
phase: 06-publication-hardening-downstream-migration-record
plan: 07
subsystem: infra
tags: [github-actions, ci-cd, release-please, pypi, oidc, branch-protection, documentation]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "Assembled .github/ tree (3 required-context CI jobs, ruleset-apply, scheduled-health, release-please, publish-pypi, publish-testpypi), .github/rulesets/*.json payloads, uv-based setup composite (plan 06)"
provides:
  - "RULESETS.md — the CI/CD adoption record: interview answers, taken/declined components with the cost of declining, every deviation from the shared template, the superseded floor-only decision, the twelve-item apply-time checklist with recorded command evidence, a live-state verification recipe, deferred items, and the pre-promotion gate record"
  - "RELEASE.md — the release process record: two trusted-publisher claim tables, what must never be renamed, the two-App credential model, 0.x version policy and Release-As mechanics, the dry-run procedure, rollback, and how to verify a release's attestation"
  - "CONTRIBUTING.md additions — the local lint and docs-build commands, linked to RULESETS.md/RELEASE.md"
affects: ["06-08+ (first promotion to main depends on this record and its recorded pre-promotion gate)"]

# Actuals (#2632)
actuals:
  tokens: 8005
  tasks: 3
  commits: 3
  plan_head_before: 5f296b27007e2833ba8ce192a85034bc97dc9cc7
  plan_head_after: c6a4cc345ca5dd1ae0956de888afb8bf8fff8760

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Recorded-evidence checklist: every apply-time item states the exact command run and its real output (or a file:line), never a bare checkmark, so a reader can tell 'checked' from 'checked nothing'"
    - "Two-App credential separation for CI write paths: release automation and branch-protection application authenticate as two distinct GitHub Apps with distinct secrets, so a compromise of one path cannot rewrite the other's surface"

key-files:
  created:
    - RULESETS.md
    - RELEASE.md
  modified:
    - CONTRIBUTING.md

key-decisions:
  - "RULESETS.md's twelve-item checklist evidence was produced by actually running each command against the assembled tree (not paraphrased from the template's example shape) — every item shows real grep/command output captured during this plan's own execution."
  - "The pre-promotion gate (full suite with the coverage floor, whole-tree pre-commit, the documentation build, both hygiene gates, the migration verifier, lockfile freshness, and a package build/check) was run once, in one pass, against the tree as it stood at the end of this plan, and its real summary lines are pasted into RULESETS.md rather than re-described."

patterns-established:
  - "Every new prose file shipped to the public branch is written free of decision/requirement/phase identifiers from the first draft, then re-checked against the planning-vocabulary test before committing — cheaper than discovering a hit after the fact."

requirements-completed: [CICD-02]

coverage:
  - id: D1
    description: "RULESETS.md records the interview answers, taken/declined components with the cost of declining, every template deviation, the superseded floor-only decision, and the twelve-item apply-time checklist with real recorded evidence"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "uv run --frozen pytest tests/test_hygiene.py -q -k \"planning_vocabulary and RULESETS\""
        status: pass
      - kind: unit
        ref: "grep-based record-shape checks (required-checks table rows, bypass_actors, not-applicable item, two quoted evidence-grep commands) — plan 06-07 Task 1 <verify>/<acceptance_criteria>"
        status: pass
    human_judgment: false
  - id: D2
    description: "RELEASE.md carries both trusted-publisher claim tables (production and dry-run) with values that match the workflow files byte-for-byte, plus the version policy, credential model, dry-run procedure, rollback and verification sections; CONTRIBUTING.md links both new records and documents the two new local commands"
    requirement: CICD-02
    verification:
      - kind: unit
        ref: "uv run --frozen pytest tests/test_hygiene.py -q -k \"planning_vocabulary and (RELEASE or CONTRIBUTING)\""
        status: pass
      - kind: unit
        ref: "diff of environment names in publish-pypi.yml/publish-testpypi.yml against RELEASE.md's claim tables — plan 06-07 Task 2 <verify>"
        status: pass
    human_judgment: false
  - id: D3
    description: "The complete local gate set (test suite with the coverage floor, whole-tree pre-commit, the sphinx -W documentation build, the placeholder and planning-vocabulary gates, the migration verifier, lockfile freshness, and a package build plus twine check) ran green in one pass against the merged tree, and every command's real summary output is recorded in RULESETS.md"
    requirement: CICD-02
    verification:
      - kind: integration
        ref: "uv run --frozen pytest --cov=pc2img --cov-branch --cov-fail-under=55 -q (278 passed, 62.27% coverage)"
        status: pass
      - kind: integration
        ref: "uv run --frozen pre-commit run --all-files (all 7 hooks Passed)"
        status: pass
      - kind: integration
        ref: "uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html (build succeeded, no WARNING/ERROR)"
        status: pass
      - kind: unit
        ref: "uv lock --check; uv build; uvx twine check dist/* (both artifacts PASSED)"
        status: pass
    human_judgment: false

# Metrics
duration: 38min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 7: CI/CD adoption record and pre-promotion gate Summary

**Wrote `RULESETS.md` and `RELEASE.md` at the repository root with the twelve-item apply-time checklist evidenced by real command runs against the assembled tree, then ran the complete local gate set once against the merged tree and recorded every command's real summary output.**

## Performance

- **Duration:** 38 min
- **Started:** 2026-09-28T16:40:00Z
- **Completed:** 2026-09-28T17:18:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `RULESETS.md`: interview answers, taken (core + release-to-PyPI) vs. declined (config
  self-inspection, continuous enforcement, GPU self-hosted) components with the cost of declining
  stated plainly, every recorded deviation from the shared template (the `uv`-based setup
  composite, the documentation group install, pre-commit sourced from the locked dev group, full
  checkout depth for version derivation, the carried-forward coverage floor, the pyright venv
  target, `uv build` in both publish workflows, attestations enabled on the dry-run publish, two
  kit test-fixture reformats, the release manifest kept unchanged, and the first-time ruleset
  creation by direct API post), the superseded floor-only decision, and the twelve-item apply-time
  checklist — each item run against the live tree with its real command output pasted in, not a
  checkmark.
- `RELEASE.md`: two trusted-publisher claim tables (production: `publish-pypi.yml` / `pypi`; dry
  run: `publish-testpypi.yml` / `testpypi` / the test-index upload endpoint), what must never be
  renamed, the two-App credential model (`gseg-release-please` for release automation,
  `gseg-ruleset-admin` for branch protection, never the same pair), the 0.x version policy and
  `Release-As` mechanics for the first release, the dry-run dispatch procedure, the rollback
  procedure, and how to verify a release's attestation via the integrity endpoint.
- `CONTRIBUTING.md`: added the local lint (`pre-commit run --all-files`) and documentation-build
  commands that mirror what CI runs, and linked both new records.
- Ran the complete pre-promotion gate once against the merged tree and recorded every command's
  real summary line in `RULESETS.md`: 278 tests passed at 62.27% coverage (floor 55%); all 7
  pre-commit hooks passed on the whole tree; the documentation built clean with warnings promoted
  to errors; the placeholder grep and the planning-vocabulary gate both came back clean; the
  migration record's inline verifier confirmed all 25 entries; the lockfile is up to date; and the
  built wheel and sdist both passed `twine check`.

## Task Commits

Each task was committed atomically:

1. **Task 1: RULESETS.md with the twelve apply-time items evidenced by running their commands** — `5ff2035` (docs)
2. **Task 2: RELEASE.md and CONTRIBUTING.md command additions** — `bf95af2` (docs)
3. **Task 3: Pre-promotion tree gate recorded into RULESETS.md** — `c6a4cc3` (docs)

_Note: this is a `type: execute` plan (Task 1 carries `type="tracer"` but ran and committed exactly
like `type="auto"` — no expansion tasks followed it in this plan), not TDD — no test→feat→refactor
commit triplet._

## Files Created/Modified

- `RULESETS.md` — CI/CD adoption record: interview answers, components, bypass list, approval
  policy, required checks, deviations, superseded decision, apply-time checklist with evidence,
  verification recipe, deferred items, pre-promotion gate record
- `RELEASE.md` — release process record: trusted-publisher claim tables, what not to rename,
  credentials, version policy, dry run, rollback, verifying a release
- `CONTRIBUTING.md` — added `pre-commit run --all-files` and the docs-build command; linked
  `RULESETS.md` and `RELEASE.md`

## Decisions Made

- Evidence in the apply-time checklist is the real output of commands run during this plan's own
  execution, not paraphrased from the template's worked example — every grep/command line in
  `RULESETS.md`'s checklist section reflects the assembled tree as it actually stands.
- The pre-promotion gate is recorded exactly once, in one pass, with real summary lines pasted in;
  it is not re-run or re-described per task.

## Deviations from Plan

None - plan executed exactly as written. Small formatting adjustments were made during authoring
(quoting a second `grep -rn` evidence command, keeping "not applicable" on one line) purely to
satisfy the plan's own literal grep-based acceptance criteria — not fixes to a defect in the
implementation, so none is logged as a Rule 1-4 deviation.

## Issues Encountered

None. `uv build` derives the current version as `2.0.0a5.post363` because the pre-existing
`v2.0.0a5` tag still sorts above the `0.x` release line on this branch — a known, already-recorded
situation (this plan's task list did not include retiring that tag) that does not affect anything
this plan's `<verify>` commands check: the build and `twine check` both succeeded regardless of the
exact version string produced.

## User Setup Required

None — no external service configuration required by this plan. The owner-account-action
checkpoints for this phase (App installs, secrets, environments, trusted-publisher registration)
are separate later plans in this phase, at the point they are actually needed.

## Next Phase Readiness

- `RULESETS.md` and `RELEASE.md` are in place at the repository root, planning-vocabulary-clean,
  and carry a recorded green pre-promotion gate — ready for the plans in this phase that perform
  the first filtered promotion to `main` and apply the committed ruleset payloads live.
- Not yet done (by design, later plans in this phase): the ruleset payloads are not yet applied to
  live branch protection, no promotion to `main` has happened, and the owner-account-action
  checkpoints (App installs, secrets, environments) have not yet been prompted.

## Self-Check: PASSED

All 3 key created/modified files verified present on disk (`RULESETS.md`, `RELEASE.md`,
`CONTRIBUTING.md`); all 3 task commits (`5ff2035`, `bf95af2`, `c6a4cc3`) confirmed in
`git log --oneline --all`.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*
