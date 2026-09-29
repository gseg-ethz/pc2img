---
status: diagnosed
phase: 06-publication-hardening-downstream-migration-record
source: [06-REVIEW.md]
started: 2026-09-29T06:58:29Z
updated: 2026-09-29T06:58:35Z
gaps_source: "/gsd-code-review 06 (deep, gsd-code-reviewer/opus) over e9eb3c4..HEAD, 48 files, run mid-phase as plan 06-09 Task 2's precondition, before the first promotion to main. CR-01 independently reproduced by the orchestrator (floating v0 tag -> setuptools_scm \"Can't parse version from tag 'v0'\" on a git-archive build). Owner dispositions 2026-09-28."
scaffold_note: "No conversational UAT has run yet; ## Tests is empty. This file currently carries only review findings."
---

## Current Test

(none — UAT not started)

## Tests

## Summary

total: 0
passed: 0
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps


<!-- ROUND 1 — imported 2026-09-29T06:58:35Z by /gsd-consolidate-findings from gsd-code-review-deep (file:.planning/phases/06-publication-hardening-downstream-migration-record/06-REVIEW.md), range e9eb3c4..2ec34fc.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "CR-01: Floating vX/vX.Y release tags make every GitHub release source archive unbuildable"
  status: failed
  severity: blocker
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Narrow describe match to v[0-9]*.[0-9]*.[0-9]* and add a git-archive regression test with a floating tag present."
  test: review-r1-a7fbf52f5b95
  root_cause: "release-please.yml tags v0/v0.11 on each release; .git_archival.txt describe matches v*, so git-archive describe resolves to v0 and setuptools_scm raises \"Can't parse version from tag 'v0'\" (reproduced: v0.11.0 alone builds; plus v0/v0.11 fails). Origin already carries v0/v0.10 on v0.10.4."
  artifacts:
    - path: ".git_archival.txt"
      issue: "line 3: CR-01: Floating vX/vX.Y release tags make every GitHub release source archive unbuildable"
  missing: []
  debug_session: ""
  reviewer_severity: "critical"

- truth: "WR-01: Release-artifact fast path green-lights a path containing a newline"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: minor
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-0aad496fe6ca
  root_cause: "A changed filename containing an embedded newline splits into lines that each match the release-artifact allowlist, so the fast path returns true and full checks are skipped."
  artifacts:
    - path: ".github/actions/classify-changes/action.yml"
      issue: "line 123: WR-01: Release-artifact fast path green-lights a path containing a newline"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-02: Migration record's inline verifier verifies far less than it claims"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: minor
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-f55745a6ed77
  root_cause: "Tier 1 checks zero symbols (all affected_symbols dotted and skipped); the BC-P2I-010 probe cannot fail; BC-P2I-007/013/014 are never checked; 'referenced by origin commit sha' is false for 007-025."
  artifacts:
    - path: "MIGRATION-v0.11.md"
      issue: "line 35: WR-02: Migration record's inline verifier verifies far less than it claims"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-03: New project_raw docstring documents a contract no implementation follows"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28)."
  test: review-r1-41b9f56f31b8
  root_cause: "Docstring says coords_raw is (N,2) and mins/maxs are kept-point extents; implementations return already-masked (M,2) coords and FoV/ROI bounds (reproduced). Ships in the public API docs."
  artifacts:
    - path: "src/pc2img/strategies/projection.py"
      issue: "line 81: WR-03: New project_raw docstring documents a contract no implementation follows"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-04: File-wide hygiene exemption for .pre-commit-config.yaml is unnecessary and falsely justified"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28)."
  test: review-r1-b41fa832e634
  root_cause: "The planning-vocabulary gate exempts the whole .pre-commit-config.yaml claiming YAML cannot avoid the literal; \\.plan[n]ing/ gives zero gate hits and identical excludes, so the exemption only weakens the gate. Docstring also says 'One exemption' when there are two."
  artifacts:
    - path: "tests/test_hygiene.py"
      issue: "line 155: WR-04: File-wide hygiene exemption for .pre-commit-config.yaml is unnecessary and falsely justified"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-05: Publish workflows can run from any ref and would ship .planning/ and .claude/ in the sdist"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Owner elevated to fix-now: add a ref guard to both publish workflows."
  test: review-r1-084c307292dd
  root_cause: "Neither publish workflow asserts its ref and no GitHub environments exist; a mis-dispatch from develop-gsd builds an sdist containing .planning/ and .claude/CLAUDE.md and uploads it permanently to (Test)PyPI."
  artifacts:
    - path: ".github/workflows/publish-pypi.yml"
      issue: "line 21: WR-05: Publish workflows can run from any ref and would ship .planning/ and .claude/ in the sdist"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-06: check_publish_gate.py misses uv publish and publish steps inside composite actions"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: minor
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-fc364d22729e
  root_cause: "A rogue workflow using 'uv publish', or a composite action wrapping gh-action-pypi-publish, passes the containment gate with exit 0 (reproduced)."
  artifacts:
    - path: ".github/scripts/check_publish_gate.py"
      issue: "line 42: WR-06: check_publish_gate.py misses uv publish and publish steps inside composite actions"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-07: Ruleset preflight accepts required contexts no pull request can produce"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: minor
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-bbf74045e95b
  root_cause: "Preflight accepts contexts from workflows that never run on pull_request (e.g. 'Branch ancestry assertion', 'Publish to PyPI'); applying such a payload would leave main requiring checks that never report. Current payload is not affected."
  artifacts:
    - path: ".github/scripts/preflight_ruleset_apply.py"
      issue: "line 145: WR-07: Ruleset preflight accepts required contexts no pull request can produce"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-08: CITATION.cff publishes a placeholder DOI"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28)."
  test: review-r1-f80cbd71c53b
  root_cause: "CITATION.cff carries doi 10.5281/zenodo.XXXXXXX, which would publish a fake identifier on public main."
  artifacts:
    - path: "CITATION.cff"
      issue: "line 24: WR-08: CITATION.cff publishes a placeholder DOI"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-09: Unpinned build backend plus deprecated license metadata puts the publish build on a clock"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: minor
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-0d8e74bbb4a8
  root_cause: "setuptools is unpinned in build-system.requires and warns the license metadata form is deprecated, unsupported after 2027-02-18."
  artifacts:
    - path: "pyproject.toml"
      issue: "line 1: WR-09: Unpinned build backend plus deprecated license metadata puts the publish build on a clock"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-10: Ancestry alarm fires after every promotion but the documented procedure only back-merges after releases"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Require a true-merge back-merge after every promotion and release-PR merge; correct the rationale."
  test: review-r1-c03c3cef77e6
  root_cause: "Every squash promotion creates a main commit absent from develop-gsd, so the nightly ancestry assertion fails until a back-merge; RULESETS.md prescribes back-merge only after releases and falsely claims the branches share no common ancestor (merge-base f946268)."
  artifacts:
    - path: "RULESETS.md"
      issue: "line 34: WR-10: Ancestry alarm fires after every promotion but the documented procedure only back-merges after releases"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "IN-01: Two actions pinned to annotated tag-object SHAs, not commit SHAs"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-3efe3bcc5c4e
  root_cause: "scheduled-health.yml:118 and ci.yml:272 pin actions to tag-object SHAs rather than the commit SHAs they point at."
  artifacts:
    - path: ".github/workflows/scheduled-health.yml"
      issue: "line 118: IN-01: Two actions pinned to annotated tag-object SHAs, not commit SHAs"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-02: Upload type-check report step can never upload anything"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-8b013676ed3b
  root_cause: "The type-check report upload step references a file no job produces, so it can never find a file."
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "line 249: IN-02: Upload type-check report step can never upload anything"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-03: attestations: write is an unneeded grant and its comment is wrong"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-ccb601f985b2
  root_cause: "Publish workflows grant attestations: write, which trusted-publishing attestations do not need; the accompanying comment misstates why."
  artifacts:
    - path: ".github/workflows/publish-testpypi.yml"
      issue: "line 59: IN-03: attestations: write is an unneeded grant and its comment is wrong"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-04: Comments reference kit components this assembly declined"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Part of the de-GSD/public-prose pass."
  test: review-r1-b073bad065c6
  root_cause: "Comments/docstrings mention check_ci_config.py, integrity.yml and ruleset-drift.yml, which were declined and do not exist in this repository."
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "line 19: IN-04: Comments reference kit components this assembly declined"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-05: RULESETS.md states the rulesets exist, but the live list is empty"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Part of the RULESETS.md rework."
  test: review-r1-0d3282d443c8
  root_cause: "RULESETS.md describes the rulesets as present; the live ruleset list is empty until plans 06-10/06-11 apply them."
  artifacts:
    - path: "RULESETS.md"
      issue: "line 176: IN-05: RULESETS.md states the rulesets exist, but the live list is empty"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-06: ci.yml header contradicts its own trigger block"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-78d3cc39add6
  root_cause: "The ci.yml header comment says one thing about push triggers while the trigger block does another."
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "line 34: IN-06: ci.yml header contradicts its own trigger block"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-07: Two different ruff versions gate formatting of the same tree"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-f4009f16b426
  root_cause: "Pre-commit pins ruff 0.15.12 while uv.lock carries ruff 0.15.21; the two can disagree on formatting."
  artifacts:
    - path: ".pre-commit-config.yaml"
      issue: "line 17: IN-07: Two different ruff versions gate formatting of the same tree"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-08: Twenty non-executable files committed with mode 100755"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-79775a983a47
  root_cause: "All 19 .github files and release-please-config.json are committed executable though none are scripts run directly."
  artifacts:
    - path: "release-please-config.json"
      issue: "line 1: IN-08: Twenty non-executable files committed with mode 100755"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-09: Migration-record summary arithmetic is wrong"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer). Moves with the record to .planning/; Phase 7 finalises it."
  test: review-r1-814a756db964
  root_cause: "The migration summary says sixteen should-review entries; there are fifteen."
  artifacts:
    - path: "MIGRATION-v0.11.md"
      issue: "line 20: IN-09: Migration-record summary arithmetic is wrong"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-10: Stale or inconsistent public docs"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Part of the public-doc rework."
  test: review-r1-8dbae7bf741e
  root_cause: "CONTRIBUTING.md, README.rst and docs/source/index.rst carry stale or mutually inconsistent statements about the new tooling."
  artifacts:
    - path: "CONTRIBUTING.md"
      issue: "line 74: IN-10: Stale or inconsistent public docs"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-11: RTD build silently tolerates a tagless checkout"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-9feb164ca67d
  root_cause: "The RTD pre-build swallows a failed tag fetch, so a tagless checkout builds docs with a wrong version instead of failing."
  artifacts:
    - path: ".readthedocs.yaml"
      issue: "line 15: IN-11: RTD build silently tolerates a tagless checkout"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-12: Protection-rewriting jobs rely on the runner image's unpinned PyYAML"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> minor + defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-28: non-breaking hardening -> defer)."
  test: review-r1-eb1ffecfa788
  root_cause: "ruleset-apply imports PyYAML from the runner image rather than a pinned install."
  artifacts:
    - path: ".github/workflows/ruleset-apply.yml"
      issue: "line 226: IN-12: Protection-rewriting jobs rely on the runner image's unpinned PyYAML"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-13: Planning vocabulary survives in shipped prose the gate's regexes cannot see"
  status: failed
  severity: major
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Part of the de-GSD/public-prose pass."
  test: review-r1-bff4e4d25bca
  root_cause: "Phrases such as 'this phase' and 'gap-closure pass' remain in shipped prose (MIGRATION-v0.11.md, ruleset-apply.yml, tests) that the vocabulary gate's patterns do not match."
  artifacts:
    - path: "tests/test_hygiene.py"
      issue: "line 1: IN-13: Planning vocabulary survives in shipped prose the gate's regexes cannot see"
  missing: []
  debug_session: ""
  reviewer_severity: "info"