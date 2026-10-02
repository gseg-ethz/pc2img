---
status: diagnosed
phase: 07-gsegutils-0-6-adoption-0-11-0-release
source: [07-REVIEW.md]
started: 2026-10-02T11:45:20Z
updated: 2026-10-02T11:45:57Z
gaps_source: "/gsd-code-review 7 (deep, gsd-code-reviewer/opus) over 9bb6b51..5ee3c80, 16 shipped files, plus /code-review origin/develop-gsd high over the same range, run as plan 07-07 Task 3. CR-01 (shipped 12/12 vs per-tile dispatch 0/12), CR-02 (fresh store reads stale 1.0 after clear+re-add of 7.0) and WR-01 (n_jobs=2 then submit -> StorePurgeRefusedError; n_jobs=1 OK) independently reproduced by the orchestrator. Owner dispositions 2026-10-02."
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



<!-- ROUND 1 — imported 2026-10-02T11:45:57Z by /gsd-consolidate-findings from gsd-code-review-deep+code-review-high (file:.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md+conversation), range 9bb6b51..5ee3c80.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "CR-01: Tiled re-generation race is triggered by pc2img's own fan-out: delayed(self._process_tile) pickles the whole generator (every tile's store) into every task, so every loky worker unpickles every store concurrently; shipped as an upstream-only xfail (GSEGUtils#82 / pc2img#24). [disposition: fix now (owner 2026-10-02): per-tile module-level dispatch; xfail -> passing regression test; revise MIGRATION BC-P2I-030; GitHub notes on #24/#82 only with owner-approved wording]"
  status: failed
  severity: blocker
  reason: "CR-01: Tiled re-generation race is triggered by pc2img's own fan-out: delayed(self._process_tile) pickles the whole generator (every tile's store) into every task, so every loky worker unpickles every store concurrently; shipped as an upstream-only xfail (GSEGUtils#82 / pc2img#24). [disposition: fix now (owner 2026-10-02): per-tile module-level dispatch; xfail -> passing regression test; revise MIGRATION BC-P2I-030; GitHub notes on #24/#82 only with owner-approved wording]"
  test: review-r1-b81fd6108587
  root_cause: "Bound-method dispatch broadcasts all tile stores to all workers; GSEGUtils 0.6.0 rebuilds .dat via fixed <key>.dat.tmp on unpickle, so concurrent unpickles of one store race."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "CR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "BLOCKER (gsd-code-reviewer); reproduced by orchestrator"

- truth: "CR-02: add_image_to_store purges only tracked keys; after del/pop/clear (which now leave <key>.npy/.meta.json on disk) a re-add skips the purge and a fresh store serves the pre-overwrite raster. Variant (/code-review): a retained old-entry reference, on GC, can delete the new entry's <key>.dat. [disposition: fix now (owner 2026-10-02): purge whenever the key's files exist, tracked or not; cover the GC-deletes-new-.dat variant]"
  status: failed
  severity: blocker
  reason: "CR-02: add_image_to_store purges only tracked keys; after del/pop/clear (which now leave <key>.npy/.meta.json on disk) a re-add skips the purge and a fresh store serves the pre-overwrite raster. Variant (/code-review): a retained old-entry reference, on GC, can delete the new entry's <key>.dat. [disposition: fix now (owner 2026-10-02): purge whenever the key's files exist, tracked or not; cover the GC-deletes-new-.dat variant]"
  test: review-r1-bb9da775d04c
  root_cause: "__delitem__ override removed (D-07: del drops tracking only) while the overwrite path keys purge on 'img_name in self' rather than on-disk presence."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "CR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "BLOCKER (gsd-code-reviewer) / high silent wrong output (/code-review); reproduced by orchestrator"

- truth: "WR-01: Tile stores built in loky workers record a worker as owner; GSEGUtils 0.6 purge refuses cross-process, so after a tiled n_jobs>=2 run the parent (or a later worker) cannot purge or overwrite them. The tiled xfail raises=(RuntimeError, OSError) would also mask this StorePurgeRefusedError. [disposition: defer + document (owner 2026-10-02): accurate docstring + MIGRATION entry now; fix after 0.11.0]"
  status: failed
  severity: major
  reason: "WR-01: Tile stores built in loky workers record a worker as owner; GSEGUtils 0.6 purge refuses cross-process, so after a tiled n_jobs>=2 run the parent (or a later worker) cannot purge or overwrite them. The tiled xfail raises=(RuntimeError, OSError) would also mask this StorePurgeRefusedError. [disposition: defer + document (owner 2026-10-02): accurate docstring + MIGRATION entry now; fix after 0.11.0]"
  test: review-r1-ba90a0c6b404
  root_cause: "Overwrite moved from del (no pid check) to upstream purge (owner-pid check); store ownership is fixed at worker construction."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "WR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer) / medium (/code-review); reproduced by orchestrator"

- truth: "WR-02: Publish gate misses local actions outside ./.github/actions/<name>/: nested dirs, actions elsewhere in the repo, and unnormalised ../ paths; test_check_publish_gate.py:649 pins the outside-actions case as intended. [disposition: defer (owner 2026-10-02, D-11 no new hardening loops)]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: non-breaking hardening -> minor + defer, D-11)"
  severity: minor
  reason: "WR-02: Publish gate misses local actions outside ./.github/actions/<name>/: nested dirs, actions elsewhere in the repo, and unnormalised ../ paths; test_check_publish_gate.py:649 pins the outside-actions case as intended. [disposition: defer (owner 2026-10-02, D-11 no new hardening loops)]"
  test: review-r1-d5a892eedf9c
  root_cause: "uv publish inside ./.github/actions/group/pub, ./tools/pub2, or ./.github/actions/../../tools/pub2 referenced from a workflow: gate exits 0 (reviewer-reproduced)."
  artifacts:
    - path: ".github/scripts/check_publish_gate.py"
      issue: "WR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer)"

- truth: "WR-03: Ruleset preflight counts pull_request workflows whose branches:/paths: filters mean they never run for the gated branch. [disposition: defer (owner 2026-10-02)]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: non-breaking hardening -> minor + defer, D-11)"
  severity: minor
  reason: "WR-03: Ruleset preflight counts pull_request workflows whose branches:/paths: filters mean they never run for the gated branch. [disposition: defer (owner 2026-10-02)]"
  test: review-r1-ced2d60dcc8b
  root_cause: "A pull_request workflow filtered to branches: [main] contributes a job name counted as matchable for the develop-gsd ruleset (reviewer-reproduced)."
  artifacts:
    - path: ".github/scripts/preflight_ruleset_apply.py"
      issue: "WR-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer)"

- truth: "WR-04: The [tool.uv.sources] nvidia index bindings are inert (uv.lock resolves cudf-cu12 and all RAPIDS packages from pypi.org; 0 pypi.nvidia.com entries, same at base); the comment claiming dependency-confusion protection is false. [disposition: fix the comment now (owner 2026-10-02)]"
  status: failed
  severity: minor
  reason: "WR-04: The [tool.uv.sources] nvidia index bindings are inert (uv.lock resolves cudf-cu12 and all RAPIDS packages from pypi.org; 0 pypi.nvidia.com entries, same at base); the comment claiming dependency-confusion protection is false. [disposition: fix the comment now (owner 2026-10-02)]"
  test: review-r1-a34794af62b1
  root_cause: "grep -c pypi.nvidia.com uv.lock -> 0; a reader trusts the comment's protection claim that the lock does not deliver."
  artifacts:
    - path: "pyproject.toml"
      issue: "WR-04 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer)"

- truth: "WR-05: Overwrite docstring states purge-refusal conditions with 'and' (they are independent, 'or'), omits StorePurgeAliasedArtefactError, and omits that a setter-inserted entry with a cache_path outside the cache dir can no longer be overwritten (worked in 0.10.x). [disposition: fix now (owner 2026-10-02), same file as CR-02]"
  status: failed
  severity: minor
  reason: "WR-05: Overwrite docstring states purge-refusal conditions with 'and' (they are independent, 'or'), omits StorePurgeAliasedArtefactError, and omits that a setter-inserted entry with a cache_path outside the cache dir can no longer be overwritten (worked in 0.10.x). [disposition: fix now (owner 2026-10-02), same file as CR-02]"
  test: review-r1-e176d03694af
  root_cause: "store[k] = entry with outside cache_path, then add_image_to_store(k, ...) raises (reviewer-reproduced) though the docstring implies only symlinked + wrong-process cases refuse."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "WR-05 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer)"

- truth: "IN-01: Drift check drops integration_id unconditionally, unlike every other read-filled key (blind spot). [disposition: defer]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: info -> cosmetic + defer)"
  severity: cosmetic
  reason: "IN-01: Drift check drops integration_id unconditionally, unlike every other read-filled key (blind spot). [disposition: defer]"
  test: review-r1-d667022ab54f
  root_cause: "A committed payload pinning integration_id would never be compared against live."
  artifacts:
    - path: ".github/scripts/ruleset_lib.py"
      issue: "IN-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "IN-02: PointCloudTile docstring's list of illegal tile ids omits control characters. [disposition: defer]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: info -> cosmetic + defer)"
  severity: cosmetic
  reason: "IN-02: PointCloudTile docstring's list of illegal tile ids omits control characters. [disposition: defer]"
  test: review-r1-14b72db4ee6b
  root_cause: "A reader follows the docstring and picks an id with a control character, which upstream refuses."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "IN-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "IN-03: Owner side item (b): the five-fields bullet is consistent with the code but gives no route to change those fields (only via the payload); 'not governed by the apply' rests on GitHub PUT behaviour for omitted fields that the repo's own comment calls undocumented. [disposition: defer]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: info -> cosmetic + defer)"
  severity: cosmetic
  reason: "IN-03: Owner side item (b): the five-fields bullet is consistent with the code but gives no route to change those fields (only via the payload); 'not governed by the apply' rests on GitHub PUT behaviour for omitted fields that the repo's own comment calls undocumented. [disposition: defer]"
  test: review-r1-f93633ce4ed9
  root_cause: "A maintainer needing to change one of the five fields finds no instruction and the web UI is banned."
  artifacts:
    - path: "RULESETS.md"
      issue: "IN-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "IN-04: Owner side item (a): committed lock is not stale — fresh re-lock's extra cloudpickle comes from joblib 1.6.0 (index drift). CI never tests numpy 2.3.x / joblib 1.6.x that a plain pip install resolves (cuda extras cap numpy <2.3 in the lock); D-03 covers this once per release. [disposition: defer]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: info -> cosmetic + defer; D-03 covers unlocked resolve per release)"
  severity: cosmetic
  reason: "IN-04: Owner side item (a): committed lock is not stale — fresh re-lock's extra cloudpickle comes from joblib 1.6.0 (index drift). CI never tests numpy 2.3.x / joblib 1.6.x that a plain pip install resolves (cuda extras cap numpy <2.3 in the lock); D-03 covers this once per release. [disposition: defer]"
  test: review-r1-dbd107420a29
  root_cause: "A regression specific to numpy 2.3 or joblib 1.6 reaches pip users without CI signal."
  artifacts:
    - path: "uv.lock"
      issue: "IN-04 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "IN-05: Owner side item (c): .claude/CLAUDE.md:68 and .planning/codebase/STACK.md:50 still state numpy ~= 2.0 (pyproject now numpy >= 2.2, < 2.4). [disposition: owner edit (not shipped)]"
  status: deferred
  deferred_to: "owner edit of agent/planning docs, not shipped (owner disposition 2026-10-02)"
  severity: cosmetic
  reason: "IN-05: Owner side item (c): .claude/CLAUDE.md:68 and .planning/codebase/STACK.md:50 still state numpy ~= 2.0 (pyproject now numpy >= 2.2, < 2.4). [disposition: owner edit (not shipped)]"
  test: review-r1-87a074a43666
  root_cause: "Agents reading project instructions assume the old numpy floor."
  artifacts:
    - path: ".claude/CLAUDE.md"
      issue: "IN-05 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"