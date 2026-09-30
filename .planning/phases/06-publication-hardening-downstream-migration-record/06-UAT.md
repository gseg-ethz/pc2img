---
status: diagnosed
phase: 06-publication-hardening-downstream-migration-record
source: [06-REVIEW.md]
started: 2026-09-29T06:58:29Z
updated: 2026-09-29T16:42:42Z
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
  status: resolved
  severity: blocker
  evidence: "Closed by gap plan 06-14, fix e44ac0b 'fix(release): narrow the archival describe glob to X.Y.Z tags so release archives build' (RED at 8651037 'test(release): pin release-archive version derivation against floating tags'): .git_archival.txt's describe glob narrowed to the single v[0-9]*.[0-9]*.[0-9]* match, identical to pyproject.toml's git_describe_command; proven by tests/test_git_archival.py (test_archive_of_floating_tagged_commit_substitutes_release_tag, test_release_tag_regex_parses_release_tag_only, test_archival_glob_matches_checkout_glob) plus a manual setuptools_scm run against a real extracted archive, before and after the fix."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-16, fix 158a569 'docs(projection): document the kept-point (M, 2) contract project_raw implementations actually follow': ProjectionStrategy.project_raw's ABC docstring rewritten to the (M, 2)/mask.sum()/length-N-mask/positional-pairing/FoV-or-ROI-else-kept-extent contract every implementation and core.py actually follow; proven by tests/test_projection.py's test_project_raw_returns_kept_points_and_fov_frame_spherical, test_project_raw_returns_kept_points_and_roi_frame_orthographic and test_project_pairs_pts2d_rows_with_mask, plus an AST-identity check (docstrings stripped) against 6c10ee0 confirming no implementation changed; follow-up tracked as review-r2-d946cd47a6ca."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-16, fix 5bb45dd 'test(hygiene): scan the pre-commit config and flag prose planning phrases': removed the .pre-commit-config.yaml entry from tests/test_hygiene.py's _EXEMPTIONS, leaving the signed IP-clearance record as the sole exemption, and re-spelled the exclude regex's planning-directory alternative with a character class so it still yields zero hygiene-gate hits; proven by the gate-ok hermetic check (len(_EXEMPTIONS) == 1, _matches() == [] on .pre-commit-config.yaml) and tests/test_hygiene.py -q -> 88 passed over the whole shipped tree."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-14, fix b6d9d9f 'feat(release): ref-guard both publish workflows against a mis-dispatch or a non-release tag' (RED at f51d584 'test(release): add failing test for publish workflow ref guards'): publish-testpypi.yml's build job now refuses any dispatch ref but refs/heads/main; publish-pypi.yml's build job refuses a release ref that is not an X.Y.Z tag, then (immediately after checkout) refuses a tagged commit not reachable from origin/main; proven by .github/scripts/test_publish_ref_guard.py's 9 accept/reject cases across both workflows' guards; follow-up tracked as review-r2-4c41e7116b0b."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-14, fix fd1c2d9 'docs(citation): drop the placeholder DOI until a release is archived': CITATION.cff's preferred-citation block (carrying doi: 10.5281/zenodo.XXXXXXX) removed entirely, message rewritten to state only facts true today; proven by the hermetic cff-ok python assertion in the plan's Task 3 verify and by uvx cffconvert --validate -i CITATION.cff."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-15, fix d179850 'docs(rulesets): condense the branch-protection and release docs to maintainer scope; require a back-merge after every promotion': RULESETS.md's Promotion and back-merge section now requires a true-merge back-merge after every promotion to main and after every release-PR merge, states the measured merge-base rationale (f946268 common ancestor; 69224a9/ade40f8 main-only commits) in place of the false no-common-ancestor claim; proven by the plan's size/heading/rationale grep block (sizes-ok 142 100; heading and rationale counts all >=1) and tests/test_hygiene.py -q -k 'planning_vocabulary and (RULESETS or RELEASE or README or index)' -> 9 passed."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-16, fix d9e86d3 'ci(comments): mark the declined kit components at every reference': added an identical 'not part of this assembly ... see RULESETS.md' note at the first declined-component reference in ci.yml, scheduled-health.yml, ruleset-apply.yml, classify-changes/action.yml, check_ruleset_drift.py, ruleset_lib.py and check_publish_gate.py; proven by the marked-ok git-grep loop over all 7 files, yaml.safe_load identity for the 4 YAML files and AST identity (docstrings stripped) for the 3 Python files, all against 6c10ee0; follow-up tracked as review-r2-9de55bd743fc."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-15, fix d179850 'docs(rulesets): condense the branch-protection and release docs to maintainer scope; require a back-merge after every promotion': RULESETS.md's Applying the rulesets section rewritten from a past-tense claim ('was done once') to a procedure describing how a ruleset gets created, never asserting one already exists; proven by the corrected word-check (wording-ok) and tests/test_hygiene.py -q -k 'planning_vocabulary and (RULESETS or RELEASE or README or index)' -> 9 passed; follow-up tracked as review-r2-9628e6ae5e41."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-15, fix 4fc329b 'docs(readme): name the perspective projection' (README.rst now names spherical, orthographic and perspective, matching docs/source/index.rst and the PROJECTIONS registry; proven by grep -c perspective on both files -> 1 each and uvx twine check on the built sdist/wheel -> both PASSED), plus gap plan 06-17, commit 5eae12c 'docs(contributing): refresh the coverage baseline after the review-round fixes' (CONTRIBUTING.md's baseline sentence now states 286 passed / 0 xfailed, 62.27%, dated 2026-09-29, closing the CONTRIBUTING.md half)."
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
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-16, fix 5bb45dd 'test(hygiene): scan the pre-commit config and flag prose planning phrases': _PHASE_PLAN_PATTERN extended with two character-class-spelled alternatives (this-phase/this-milestone, gap-closure); reworded the 'deferred to the bug-fix phase' sentences and ruleset-apply.yml's 'this phase' token-mint comment; proven by tests/test_hygiene.py's test_prose_planning_phrases_are_flagged and the extended test_public_identifiers_are_not_flagged, plus the whole-tree gate run (tests/test_hygiene.py -q -> 88 passed)."
  reason: "FIX NOW before first promotion (owner disposition 2026-09-28). Part of the de-GSD/public-prose pass."
  test: review-r1-bff4e4d25bca
  root_cause: "Phrases such as 'this phase' and 'gap-closure pass' remain in shipped prose (MIGRATION-v0.11.md, ruleset-apply.yml, tests) that the vocabulary gate's patterns do not match."
  artifacts:
    - path: "tests/test_hygiene.py"
      issue: "line 1: IN-13: Planning vocabulary survives in shipped prose the gate's regexes cannot see"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

<!-- ROUND 2 — imported 2026-09-29T12:08:42Z by /gsd-consolidate-findings from gsd-code-review-deep (file:.planning/phases/06-publication-hardening-downstream-migration-record/06-REVIEW.md), range 2ec34fc..5eae12c.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "WR-01: Publish ref guards only protect commits that contain them; docs overclaim"
  status: resolved
  severity: major
  evidence: "Closed by gap plan 06-19, commits 5691315 'docs(release): rewrite the release process for outside readers and scope the ref-guard claims' and f14c97a 'docs(citation): drop the main-branch claim from the citation message': RELEASE.md and both publish workflow header comments narrowed to state the guards protect only a run started from a commit that carries them, with 'only ever create a release whose tag is on main' as the written safeguard; proven by the RELEASE.md heading/phrase greps ('protect only a run started from a commit that carries them'), the workflow-derived facts check, and yaml-identity against e929894 for publish-pypi.yml/publish-testpypi.yml."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification. Option (b): NO code change; owner declined environment deployment rules and sdist content check. Narrow RELEASE.md:66-72 and the publish-pypi.yml / publish-testpypi.yml header comments to state the guards only protect releases from commits containing them, and make 'only create releases whose tag is on main' the written safeguard."
  test: review-r2-4c41e7116b0b
  root_cause: "GitHub runs a release workflow from the tagged commit and a dispatch from the chosen branch; origin/develop-gsd, the pushed phase-06 branch and 18 older commits carry unguarded publish workflows, so a release tagged there uploads an sdist with .planning/ and .claude/ permanently. RELEASE.md and workflow header comments claim more than the in-file guards give."
  artifacts:
    - path: ".github/workflows/publish-pypi.yml"
      issue: "WR-01: Publish ref guards only protect commits that contain them; docs overclaim"
    - path: ".github/workflows/publish-testpypi.yml"
      issue: "WR-01: Publish ref guards only protect commits that contain them; docs overclaim"
    - path: "RELEASE.md"
      issue: "WR-01: Publish ref guards only protect commits that contain them; docs overclaim"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, commits 975a474 'docs(rulesets): rewrite the branch rules for outside readers', 4503b44 'ci(comments): drop the declined-component pointers and the strategy-document references' and 3e01a1c 'ci(scripts): drop the declined-component pointers from the kit scripts': the seven 'see RULESETS.md' pointer comments deleted from ci.yml, scheduled-health.yml, ruleset-apply.yml, classify-changes/action.yml, check_publish_gate.py, check_ruleset_drift.py and ruleset_lib.py; three keep-by-hand clauses added to ci.yml in their place; proven by zero 'see RULESETS.md' / 'strategy document' / pointer-note greps under .github, the three keep-by-hand clauses' presence, yaml-same-except-logline for ci.yml and yaml-same for the other workflow/action files, and AST-identity (docstrings stripped) for the three scripts, all against e929894."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification. Restore a short declined-components record + apply-time checklist in RULESETS.md, or reword the pointers."
  test: review-r2-9de55bd743fc
  root_cause: "Plan 06-15 condensed RULESETS.md (removing the declined-components record and apply-time checklist); plan 06-16 then added 7 pointers to that record, plus a runtime Lint log line at ci.yml:190 — all point at nothing."
  artifacts:
    - path: "RULESETS.md"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/workflows/ci.yml"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/actions/classify-changes/action.yml"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/scripts/check_publish_gate.py"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/scripts/check_ruleset_drift.py"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/scripts/ruleset_lib.py"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/workflows/ruleset-apply.yml"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
    - path: ".github/workflows/scheduled-health.yml"
      issue: "WR-02: Every 'see RULESETS.md' pointer for the declined components dangles"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-03: A gap-closure fix shipped a review-finding ID into tests/test_projection.py"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix e2a3f5a 'test(projection): drop the review identifier from a section header': the '# WR-03:' section header at tests/test_projection.py:309 removed; extending the hygiene gate to the ID family left out of scope, as planned; proven by a review-identifier regex ((CR|WR|IN)-[0-9]{2}) count of 0 over the file and AST-identity (docstrings stripped) against e929894."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification. Remove the ID from the comment (extending the hygiene gate to the ID family is not in scope of this pass)."
  test: review-r2-d946cd47a6ca
  root_cause: "Commit 158a569 added '# WR-03:' section header at tests/test_projection.py:309, which ships to main; the hygiene gate cannot see CR-/WR-/IN- IDs (_matches('WR-03') returns [])."
  artifacts:
    - path: "tests/test_projection.py"
      issue: "WR-03: A gap-closure fix shipped a review-finding ID into tests/test_projection.py"
    - path: "tests/test_hygiene.py"
      issue: "WR-03: A gap-closure fix shipped a review-finding ID into tests/test_projection.py"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-05: RULESETS.md verification recipe expects a field the list endpoint never returns"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix 975a474 'docs(rulesets): rewrite the branch rules for outside readers': RULESETS.md's verification recipe repointed at the per-ruleset endpoint rather than the list endpoint; proven by the payload-derived RULESETS.md table check and the per-id 'Inspect a live ruleset' line grep. Round 3 re-raised gaps in this same recipe as review-r3-10cbe7e3b994 (admin-token requirement) and review-r3-87fdf631a3ae (create path/main-only payload source), both resolved at the 06-19 checkpoint (fix fd52d77)."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification. Point the recipe at the per-ruleset endpoint or drop the bypass_actors expectation."
  test: review-r2-9628e6ae5e41
  root_cause: "The recipe runs gh api repos/gseg-ethz/pc2img/rulesets and expects bypass_actors, which the list endpoint never returns (checked on five public repos), so the check can never pass."
  artifacts:
    - path: "RULESETS.md"
      issue: "WR-05: RULESETS.md verification recipe expects a field the list endpoint never returns"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "IN-04: RELEASE.md says a PyPI release cannot be deleted"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, commits 5691315 'docs(release): rewrite the release process for outside readers and scope the ref-guard claims' and f14c97a 'docs(citation): drop the main-branch claim from the citation message': RELEASE.md's Rollback section corrected to state owners can delete an uploaded version but the filename/version can never be reused; proven by the RELEASE.md Rollback phrase greps."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification."
  test: review-r2-c1587a95ad75
  root_cause: "RELEASE.md:83-87 claims neither index allows deleting an uploaded version; owners can delete, but the filename/version can never be reused."
  artifacts:
    - path: "RELEASE.md"
      issue: "IN-04: RELEASE.md says a PyPI release cannot be deleted"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-05: Reworded ruleset-token comment makes a false global claim"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix 4503b44 'ci(comments): drop the declined-component pointers and the strategy-document references': ruleset-apply.yml:237-238's claim to be THE one place with a write scope corrected to name it as the only Administration-write grant among other write scopes elsewhere; proven by the 'only Administration-write grant' grep and yaml-identity for ruleset-apply.yml against e929894. Round 3 re-raised the write-scope list's incompleteness as review-r3-ddde4a06e5e0, resolved at the 06-19 checkpoint (fix fd52d77)."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification."
  test: review-r2-6a4285da474b
  root_cause: "ruleset-apply.yml:237-238 claims it is THE one place in these workflows where a write scope is correct; other workflows also hold write scopes."
  artifacts:
    - path: ".github/workflows/ruleset-apply.yml"
      issue: "IN-05: Reworded ruleset-token comment makes a false global claim"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-06: CITATION.cff carries no version and claims main reflects the latest release"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix f14c97a 'docs(citation): drop the main-branch claim from the citation message': CITATION.cff:15-19's main-reflects-latest-release claim dropped from the message; proven by the CITATION.cff phrase grep and cffconvert --validate passing. Round 3 re-raised that the message still claimed releases are published on PyPI (none were yet) as review-r3-fe2548de9d69, resolved at the 06-19 checkpoint (fix fd52d77)."
  reason: "FIX NOW in one doc-only pass before promotion (owner disposition 2026-09-29); the fix diff gets its own /gsd-code-review before re-verification."
  test: review-r2-02618891c01a
  root_cause: "CITATION.cff:15-19 has no version and states main reflects the latest release, which is false between a promotion and the release-PR merge."
  artifacts:
    - path: "CITATION.cff"
      issue: "IN-06: CITATION.cff carries no version and claims main reflects the latest release"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "WR-04: Release-artifact fast path ignores previous_filename, so a rename hides a deletion"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)"
  severity: minor
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer). Pair with deferred round-1 WR-01 (classify-changes fast path)."
  test: review-r2-fe60d80dfeb5
  root_cause: "Renaming a source file into an allowlisted name (after a first PR deletes CHANGELOG.md) greens all required checks while deleting code; rename shape confirmed on pypa/pip#14322. Pre-existing, not introduced this round."
  artifacts:
    - path: ".github/actions/classify-changes/action.yml"
      issue: "WR-04: Release-artifact fast path ignores previous_filename, so a rename hides a deletion"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "IN-01: Planning-vocabulary gate still passes two shipped hits and any wrapped phrase"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)."
  test: review-r2-417b6d3fb915
  root_cause: "Gate passes '(Plan 03)' at pyproject.toml:196, 'round-3' at tests/test_image_store.py:272, and any phrase wrapped across lines."
  artifacts:
    - path: "tests/test_hygiene.py"
      issue: "IN-01: Planning-vocabulary gate still passes two shipped hits and any wrapped phrase"
    - path: "pyproject.toml"
      issue: "IN-01: Planning-vocabulary gate still passes two shipped hits and any wrapped phrase"
    - path: "tests/test_image_store.py"
      issue: "IN-01: Planning-vocabulary gate still passes two shipped hits and any wrapped phrase"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-02: Base project() docstring contradicts the corrected project_raw contract"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)."
  test: review-r2-0ae5634051ba
  root_cause: "projection.py:106-114 still says 'Normalize raw coords into [0,1]x[0,1] based on data extents', contradicting the corrected project_raw docstring."
  artifacts:
    - path: "src/pc2img/strategies/projection.py"
      issue: "IN-02: Base project() docstring contradicts the corrected project_raw contract"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-03: Ref-guard tests do not pin 'before anything is built'; git fixtures inherit ambient GIT_* state"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)."
  test: review-r2-b98e26a33f0c
  root_cause: "Tests do not assert the ancestry guard precedes the build step, and tests/test_git_archival.py fixtures pick up ambient GIT_* environment variables."
  artifacts:
    - path: ".github/scripts/test_publish_ref_guard.py"
      issue: "IN-03: Ref-guard tests do not pin 'before anything is built'; git fixtures inherit ambient GIT_* state"
    - path: "tests/test_git_archival.py"
      issue: "IN-03: Ref-guard tests do not pin 'before anything is built'; git fixtures inherit ambient GIT_* state"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

<!-- ROUND 3 — imported 2026-09-29T16:42:42Z by /gsd-consolidate-findings from gsd-code-review-deep (conversation), range 29039d5..f5d9037.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "WR-01: Deleting the declined-component pointers left false present-tense claims about nightly drift detection and a CI self-check"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77 'docs(release): correct the round of claims the doc pass overstated': ruleset-apply.yml, scheduled-health.yml, check_ruleset_drift.py, ruleset_lib.py and check_publish_gate.py no longer claim a nightly ruleset-drift.yml workflow or a check_ci_config.py self-test exist; proven by yaml-same for ruleset-apply.yml and scheduled-health.yml, and ast-same (docstrings stripped) for check_ruleset_drift.py, ruleset_lib.py and check_publish_gate.py, all against e929894; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-9f579aafa132
  root_cause: "ruleset-apply.yml:13-15, scheduled-health.yml:6-7,36-39, check_ruleset_drift.py:11-19, ruleset_lib.py:5-8,16-20 and check_publish_gate.py:124-127 state unconditionally that a nightly ruleset-drift.yml and check_ci_config.py exist; neither ships, so a maintainer believes a web-UI ruleset edit is detected overnight when nothing detects it"
  artifacts:
    - path: ".github/workflows/ruleset-apply.yml"
      issue: "WR-01: lines 13-15 claim a drift workflow detects changes"
    - path: ".github/workflows/scheduled-health.yml"
      issue: "WR-01: lines 6-7, 36-39 drift-workflow sentence"
    - path: ".github/scripts/check_ruleset_drift.py"
      issue: "WR-01: docstring lines 11-19 name a nightly ruleset-drift.yml caller"
    - path: ".github/scripts/ruleset_lib.py"
      issue: "WR-01: lines 5-8,16-20 list check_ci_config.py as importer and a read-only drift job"
    - path: ".github/scripts/check_publish_gate.py"
      issue: "WR-01: lines 124-127 name check_ci_config.load_workflows"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-02: ci.yml keep-by-hand rule points at the wrong YAML location and omits paths-ignore/branches"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77: the keep-by-hand clause now reads 'never add a job-level `if:` to any job here, and never add a `paths:`, `paths-ignore:` or `branches:` key under `on.pull_request`'; proven by yaml-same-except-logline for ci.yml against e929894 (only the Lint self-check log-line string differs); fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-309ffc956126
  root_cause: "ci.yml:20-21 says never put a paths: filter on a required-context job; path filters live under on.pull_request, and paths-ignore:/branches: have the same stranding effect, so a maintainer checking the job never looks at on: where the defect would be; this sentence is the only guard since check_ci_config.py is absent"
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "line 20: WR-02: ci.yml keep-by-hand rule points at the wrong YAML location and omits paths-ignore/branches"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-03: RULESETS.md inspection note omits the admin-token requirement that a ruleset-apply.yml comment says it states"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77: RULESETS.md's 'Inspect a live ruleset' bullet now says a token with repository administration access is required, that without one the bypass-actor list is missing from the response entirely, and that only an explicit empty array confirms no bypass; ruleset-apply.yml's cross-reference to this note is now accurate; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-10cbe7e3b994
  root_cause: "RULESETS.md:27-28 says read a ruleset by id but not that an administration-capable token is needed; without one the response omits bypass_actors and the reader takes the absence as no bypass; ruleset-apply.yml:243-245 claims RULESETS.md states the token requirement"
  artifacts:
    - path: "RULESETS.md"
      issue: "WR-03: lines 27-28 omit admin-token requirement and absent-key warning"
    - path: ".github/workflows/ruleset-apply.yml"
      issue: "WR-03: lines 243-245 cross-reference claims RULESETS.md states it"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-04: ruleset-token comment's write-scope list is incomplete (attestations, release App token)"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77 (prose only; the behaviour half is DEFERRED to Phase 7, see reason): ruleset-apply.yml's token-mint comment now lists `attestations` on the publish jobs and the release App's token (minted with no `permission-*` inputs) alongside `id-token` and `issues` as the other write grants; proven by yaml-same for ruleset-apply.yml against e929894 (the `permission-administration: write` grant line itself is unchanged); fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner. Behaviour half (narrow the release App token mint so the only-Administration-write claim is enforced) DEFERRED to Phase 7."
  test: review-r3-ddde4a06e5e0
  root_cause: "ruleset-apply.yml:235-242 lists only id-token and issues as other write scopes; attestations: write on both publish jobs is omitted, and the release App token in release-please.yml:45-49 is minted without permission-* inputs, so the 'only Administration-write grant' claim cannot be verified from the repo"
  artifacts:
    - path: ".github/workflows/ruleset-apply.yml"
      issue: "line 235: WR-04: ruleset-token comment's write-scope list is incomplete (attestations, release App token)"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-05: RULESETS.md change-a-rule recipe silently re-applies main's old payload and has no create path"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77: RULESETS.md's 'Changing a rule' bullet now says the edit must reach `main` first (the workflow reads payloads from `main` only), that the workflow updates an existing ruleset only, and gives the `gh api --method POST` command for creating one; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-87fdf631a3ae
  root_cause: "RULESETS.md:24-25 says edit the payload then run ruleset-apply from main; PRs land on develop-gsd, the workflow reads payloads from main only, so dispatch after the edit merges re-applies the old payload and verifies clean; the workflow cannot create a ruleset (exits at lines 187-190) and the create-path note was deleted while live rulesets are []"
  artifacts:
    - path: "RULESETS.md"
      issue: "line 24: WR-05: RULESETS.md change-a-rule recipe silently re-applies main's old payload and has no create path"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-06: CITATION.cff tells users to cite installed version metadata, which for non-release installs is a never-released, non-unique version"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77: CITATION.cff's message now tells a git-install user to cite the commit hash instead of the installed package's version metadata, which it now states does not identify unreleased code; proven by `cffconvert --validate` passing; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-58aee162fdd6
  root_cause: "CITATION.cff:16-17 says cite the installed package's version metadata; with version_scheme post-release and no-local-version, a git install reports <tag>.postN with no hash (reproduced: dev venv reports 0.10.4.post407), which exists on no index and does not identify code"
  artifacts:
    - path: "CITATION.cff"
      issue: "line 16: WR-06: CITATION.cff tells users to cite installed version metadata, which for non-release installs is a never-released, non-unique version"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "WR-07: RELEASE.md promotion step names neither the stripped directories nor a mechanism, and nothing checks it"
  status: resolved
  severity: minor
  evidence: "Closed by gap plan 06-19, fix fd52d77 (prose only; the behaviour half is DEFERRED to Phase 7, see reason): RELEASE.md's Releasing step 1 now names the `.planning` and `.claude` directories explicitly and states the mechanism (a pull request from a branch cut from `main`, never from `develop-gsd` itself, squash-merged); the added-lines hygiene/vocabulary scan against e929894 returns no hit for the new wording; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner. Highest-risk round-3 finding: a literal reading ships .planning/ and .claude/ to PyPI irreversibly. Behaviour half (Lint check that .planning/ and .claude/ are absent on PRs based on main) DEFERRED to Phase 7."
  test: review-r3-975048ad0049
  root_cause: "RELEASE.md:30 says promote develop-gsd to main (squashed, internal directories stripped); read literally a squash-merged develop-gsd->main PR lands .planning/ and .claude/ on main, setuptools-scm puts them in the sdist, and the next release uploads them permanently; no check fires (hygiene gate exempts those dirs, RELEASE.md:43 admits no package-content check)"
  artifacts:
    - path: "RELEASE.md"
      issue: "line 30: WR-07: RELEASE.md promotion step names neither the stripped directories nor a mechanism, and nothing checks it"
  missing: []
  debug_session: ""
  reviewer_severity: "warning"

- truth: "IN-01: RELEASE.md says X.Y.Z tag but the guard requires a v prefix and no pre-release suffix"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix fd52d77: RELEASE.md's Ref guards section now says 'PyPI only from a `vX.Y.Z` tag on `main` (no pre-release suffix)', matching publish-pypi.yml's `^v[0-9]+\\.[0-9]+\\.[0-9]+$` guard; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-1ace814feece
  root_cause: "RELEASE.md:39-40 says PyPI only from an X.Y.Z tag; publish-pypi.yml:47 requires ^v[0-9]+.[0-9]+.[0-9]+$, so a hand-made 0.11.1 or v0.12.0rc1 tag is refused at publish time"
  artifacts:
    - path: "RELEASE.md"
      issue: "line 39: IN-01: RELEASE.md says X.Y.Z tag but the guard requires a v prefix and no pre-release suffix"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-02: Release-As: takes an explicit version and must be on the commit that lands on main"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix fd52d77: RELEASE.md's Versions section now says 'Force a specific version with a `Release-As: 0.12.0` footer on the landing commit'; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-713b1d7f6847
  root_cause: "RELEASE.md:26-27 says force a minor bump with a Release-As: footer; release-please reads Release-As: <version> as an exact version and only sees commits on main (the squashed promotion commit)"
  artifacts:
    - path: "RELEASE.md"
      issue: "line 26: IN-02: Release-As: takes an explicit version and must be on the commit that lands on main"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-03: lint-permissions keep-by-hand rule contradicts the block and disables the fast path if followed"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix fd52d77: ci.yml's keep-by-hand clause now says leave the lint job's `permissions:` read-only (`contents: read`, `pull-requests: read`), matching the job's actual block; proven by yaml-same-except-logline for ci.yml against e929894 (only the Lint self-check log-line string differs); fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-bd8b4cae1b22
  root_cause: "ci.yml:41-42 says leave lint permissions at contents: read; the block also holds pull-requests: read (lines 99-100) which classify-changes requires, so following the sentence makes the classifier fail safe and the fast path goes inert"
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "line 41: IN-03: lint-permissions keep-by-hand rule contradicts the block and disables the fast path if followed"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-04: 'recorded deviation' comments point at a RULESETS.md section this diff deleted"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix fd52d77: publish-testpypi.yml's two attestation comments and ci.yml's coverage-floor comment no longer say 'recorded deviation'/'recorded addition'; proven by yaml-same for publish-testpypi.yml and yaml-same-except-logline for ci.yml against e929894; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-118821980292
  root_cause: "publish-testpypi.yml:73,90 and ci.yml:259-262 call the TestPyPI attestation grant and the coverage floor a recorded deviation/addition; the record was RULESETS.md's Recorded deviations section, removed in this pass"
  artifacts:
    - path: ".github/workflows/publish-testpypi.yml"
      issue: "IN-04: lines 73, 90 reference deleted record"
    - path: ".github/workflows/ci.yml"
      issue: "IN-04: lines 259-262 reference deleted record"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-05: CITATION.cff says releases are published on PyPI; none are yet"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix fd52d77: CITATION.cff's message now says 'Releases are tagged on GitHub; from 0.11.0 on, they are also published on PyPI'; proven by `cffconvert --validate` passing; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-fe2548de9d69
  root_cause: "CITATION.cff:16 says releases are tagged on GitHub and published on PyPI; pypi.org/pypi/pc2img/json returns 404 and v0.10.0..v0.10.4 exist only as GitHub tags; raised in round 2 and not addressed by the rewrite"
  artifacts:
    - path: "CITATION.cff"
      issue: "line 16: IN-05: CITATION.cff says releases are published on PyPI; none are yet"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-06: 'Run the same checks locally' points at CONTRIBUTING.md commands that do not match CI"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)."
  test: review-r3-5239cfaa197f
  root_cause: "RULESETS.md:19 points at CONTRIBUTING.md, whose local commands omit check_publish_gate.py, pytest .github/scripts/ and the coverage floor (--cov-fail-under=55), so a contributor green locally can fail a required check"
  artifacts:
    - path: "RULESETS.md"
      issue: "line 19: IN-06: 'Run the same checks locally' points at CONTRIBUTING.md commands that do not match CI"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-07: three edited lines exceed the 120-column limit"
  status: resolved
  severity: cosmetic
  evidence: "Closed by gap plan 06-19, fix fd52d77: ci.yml's keep-by-hand clause, RELEASE.md's Ref-guards/Releasing paragraphs and CITATION.cff's message were rewrapped as part of the WR-02, WR-01(r2)/WR-07 and WR-06/IN-05 fixes; checked with `awk '{print length}'` over each file, the longest line is now 105 (RELEASE.md), well under the 120-column limit; fix review waived by the owner at the round cap."
  reason: "FIX NOW at the 06-19 checkpoint in one prose-only commit (owner disposition 2026-09-29); round cap reached, review of the fix commit waived by the owner."
  test: review-r3-e8240be04c46
  root_cause: "ci.yml:21 (130 cols), RELEASE.md:41 (141) and CITATION.cff:16 (122) exceed the project's 120-column limit and the ~80-column wrap around them; nothing checks YAML/Markdown width"
  artifacts:
    - path: ".github/workflows/ci.yml"
      issue: "IN-07: line 21 is 130 columns"
    - path: "RELEASE.md"
      issue: "IN-07: line 41 is 141 columns"
    - path: "CITATION.cff"
      issue: "IN-07: line 16 is 122 columns"
  missing: []
  debug_session: ""
  reviewer_severity: "info"

- truth: "IN-08: deferred 'apply-time checklist' phrases still point at an unshipped checklist"
  status: deferred
  deferred_to: "Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer)"
  severity: cosmetic
  reason: "DEFERRED to Phase 7 (owner disposition 2026-09-29: non-breaking hardening -> defer). Pairs with the round-2 deferral of the remaining kit-conditional prose."
  test: review-r3-d5f18c5bd824
  root_cause: "scheduled-health.yml:12-13 and classify-changes/action.yml:73-74 still say this is an apply-time checklist item; the checklist was the unshipped strategy document and every other reference to it was removed in this pass"
  artifacts:
    - path: ".github/workflows/scheduled-health.yml"
      issue: "IN-08: lines 12-13"
    - path: ".github/actions/classify-changes/action.yml"
      issue: "IN-08: lines 73-74"
  missing: []
  debug_session: ""
  reviewer_severity: "info"