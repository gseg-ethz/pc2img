---
status: diagnosed
phase: 07-gsegutils-0-6-adoption-0-11-0-release
source: [07-REVIEW.md]
started: 2026-10-02T11:45:20Z
updated: 2026-10-05T12:23:42Z
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

<!-- ROUND 2 — imported 2026-10-02T13:15:11Z by /gsd-consolidate-findings from gsd-code-review-deep+code-review-high (file:.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md+conversation), range 271b208..d689b6a.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "G1-CR-01: After a second generate() with n_jobs>=2 on one instance, returned rasters cannot be read: each pickle round-trip yields another entry on the same <tile>/<key>.dat with its own armed GC finalizer, and releasing the previous call's results deletes the file the new results read lazily. The converted regression test only checks dict keys, never reads an array. [disposition: fix now, pc2img side (owner 2026-10-02): disable_purge() on worker-returned entries; regression tests must read arrays; GSEGUtils own-file-only finalizer -> backlog]"
  status: failed
  severity: blocker
  reason: "G1-CR-01: After a second generate() with n_jobs>=2 on one instance, returned rasters cannot be read: each pickle round-trip yields another entry on the same <tile>/<key>.dat with its own armed GC finalizer, and releasing the previous call's results deletes the file the new results read lazily. The converted regression test only checks dict keys, never reads an array. [disposition: fix now, pc2img side (owner 2026-10-02): disable_purge() on worker-returned entries; regression tests must read arrays; GSEGUtils own-file-only finalizer -> backlog]"
  test: review-r2-8c0dc5826b5b
  root_cause: "Per-tile dispatch (07-12) made the second pooled call reachable; worker-returned store entries keep armed purge-on-GC finalizers pointing at shared paths."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G1-CR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "BLOCKER (gsd-code-reviewer, gap round 1); reproduced by orchestrator"

- truth: "G1-WR-01: The 07-13 presence-gated purge also purges untracked keys with leftover non-serving files, so a non-owner process is refused (StorePurgeRefusedError) on regeneration. Triggers: a .dat.tmp from a killed worker; a lone .dat left by a purge_disk_on_gc=False session (iof3D durable warm-restart). Documented n_jobs=1 workaround fails 4/4 after a pooled run. [disposition: fix now (owner 2026-10-02): narrow the presence check to the stale-serving artefacts; regression tests for leftover .dat and .dat.tmp from a non-owner process]"
  status: failed
  severity: major
  reason: "G1-WR-01: The 07-13 presence-gated purge also purges untracked keys with leftover non-serving files, so a non-owner process is refused (StorePurgeRefusedError) on regeneration. Triggers: a .dat.tmp from a killed worker; a lone .dat left by a purge_disk_on_gc=False session (iof3D durable warm-restart). Documented n_jobs=1 workaround fails 4/4 after a pooled run. [disposition: fix now (owner 2026-10-02): narrow the presence check to the stale-serving artefacts; regression tests for leftover .dat and .dat.tmp from a non-owner process]"
  test: review-r2-6d6f4f1c8db3
  root_cause: "_has_on_disk_artefact checks all six derived paths; only .npy/.meta.json can make a fresh store serve a stale raster."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G1-WR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer) + medium (/code-review 271b208 high)"

- truth: "G1-WR-02: Tiled class docstring and MIGRATION BC-P2I-030 misdescribe when tiled stores refuse (the 'later generate() can fail' claim is real via untracked keys with leftovers, so 07-14's correction is wrong), and the n_jobs=1 workaround fails after a pooled run. [disposition: fix now (owner 2026-10-02): docs follow the G1-CR-01/G1-WR-01 fixes; BC-P2I-030 corrected]"
  status: failed
  severity: minor
  reason: "G1-WR-02: Tiled class docstring and MIGRATION BC-P2I-030 misdescribe when tiled stores refuse (the 'later generate() can fail' claim is real via untracked keys with leftovers, so 07-14's correction is wrong), and the n_jobs=1 workaround fails after a pooled run. [disposition: fix now (owner 2026-10-02): docs follow the G1-CR-01/G1-WR-01 fixes; BC-P2I-030 corrected]"
  test: review-r2-ee291c15ade8
  root_cause: "Reader follows the documented n_jobs=1 workaround on an instance that already ran pooled and gets StorePurgeRefusedError 4/4 (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G1-WR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G1-WR-03: At n_jobs=1, verbose=50 makes every task exception after the first surface as joblib AttributeError '_pre_dispatch_amount'; the real StorePurgeRefusedError/StoreKeyError is only in __context__. Predates this phase. [disposition: defer (owner 2026-10-02): pre-existing, minor]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: pre-existing joblib verbose masking -> minor + defer)"
  severity: minor
  reason: "G1-WR-03: At n_jobs=1, verbose=50 makes every task exception after the first surface as joblib AttributeError '_pre_dispatch_amount'; the real StorePurgeRefusedError/StoreKeyError is only in __context__. Predates this phase. [disposition: defer (owner 2026-10-02): pre-existing, minor]"
  test: review-r2-94d57524bf67
  root_cause: "n_jobs=1 tiled run where tile 2 raises -> caller sees AttributeError '_pre_dispatch_amount' (joblib 1.5.3, reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G1-WR-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G1-WR-04: Duplicate tile ids are accepted: later calls hand both tasks one generator, so tile A is computed from tile B's points silently, one tile drops from results, and with a pool the #82 race returns. [disposition: fix now (owner 2026-10-02): ValueError at construction + MIGRATION note]"
  status: failed
  severity: major
  reason: "G1-WR-04: Duplicate tile ids are accepted: later calls hand both tasks one generator, so tile A is computed from tile B's points silently, one tile drops from results, and with a pool the #82 race returns. [disposition: fix now (owner 2026-10-02): ValueError at construction + MIGRATION note]"
  test: review-r2-cca8bfbff4f4
  root_cause: "Two PointCloudTile with id 'tile_00': second generate() computes both from one generator, result has one entry; pooled run fails 6/6 on the .dat.tmp race (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G1-WR-04 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G1-IN-01: _has_on_disk_artefact hand-copies upstream's purge set from builders GSEGUtils marks deliberately unpublished; four of six members untested. [disposition: fix via the G1-WR-01 narrowing (owner 2026-10-02)]"
  status: failed
  severity: cosmetic
  reason: "G1-IN-01: _has_on_disk_artefact hand-copies upstream's purge set from builders GSEGUtils marks deliberately unpublished; four of six members untested. [disposition: fix via the G1-WR-01 narrowing (owner 2026-10-02)]"
  test: review-r2-eb3bbf0dd51c
  root_cause: "Upstream renames/changes an unpublished builder and the presence check silently diverges from purge."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G1-IN-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G1-IN-02: TOCTOU: files vanishing between the presence check and purge's own existence check raise KeyError on overwrite (timing not reproduced). [disposition: defer]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-02: unreproduced TOCTOU -> cosmetic + defer)"
  severity: cosmetic
  reason: "G1-IN-02: TOCTOU: files vanishing between the presence check and purge's own existence check raise KeyError on overwrite (timing not reproduced). [disposition: defer]"
  test: review-r2-83dee60b4a69
  root_cause: "Concurrent deletion between check and purge -> KeyError from add_image_to_store."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G1-IN-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G1-IN-03: Docstring says 'one loky task per tile' and 'n_jobs >= 2'; joblib batches tiles and the default n_jobs=-1 is also affected. [disposition: fix now with G1-WR-02 (owner 2026-10-02)]"
  status: failed
  severity: cosmetic
  reason: "G1-IN-03: Docstring says 'one loky task per tile' and 'n_jobs >= 2'; joblib batches tiles and the default n_jobs=-1 is also affected. [disposition: fix now with G1-WR-02 (owner 2026-10-02)]"
  test: review-r2-69cf81e9576c
  root_cause: "Reader with default n_jobs=-1 assumes the owner limit does not apply."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G1-IN-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G1-IN-04: [tool.uv.sources] NOTE still gives a reason ('which is why only those names keep an index binding') that the new comment above it withdraws. [disposition: fix now (owner 2026-10-02)]"
  status: failed
  severity: cosmetic
  reason: "G1-IN-04: [tool.uv.sources] NOTE still gives a reason ('which is why only those names keep an index binding') that the new comment above it withdraws. [disposition: fix now (owner 2026-10-02)]"
  test: review-r2-a8e198674c03
  root_cause: "Reader gets contradictory explanations of the nvidia bindings."
  artifacts:
    - path: "pyproject.toml"
      issue: "G1-IN-04 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G1-IN-05: Predates this phase: automatic_offloading=True breaks the first pooled tiled generate() with AttributeError '_data' on both the pre-fix and fixed trees. [disposition: defer + todo (owner 2026-10-02)]"
  status: deferred
  deferred_to: "after 0.11.0, tracked as todo 2026-10-02-tiled-automatic-offloading-first-pooled-call (owner disposition 2026-10-02: pre-existing -> defer + todo)"
  severity: minor
  reason: "G1-IN-05: Predates this phase: automatic_offloading=True breaks the first pooled tiled generate() with AttributeError '_data' on both the pre-fix and fixed trees. [disposition: defer + todo (owner 2026-10-02)]"
  test: review-r2-8a34efb9d346
  root_cause: "TiledPointCloudImageGenerator with automatic_offloading=True, generate(n_jobs=2) -> AttributeError '_data' (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G1-IN-05 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP1.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

<!-- ROUND 3 — imported 2026-10-05T08:33:49Z by /gsd-consolidate-findings from gsd-code-review-deep+code-review-high (file:.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md+conversation), range 7094dde..5382353.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "G2-CR-01: Entries created at n_jobs=1 keep their delete-on-GC hook (_release_gc_ownership runs only for n_jobs != 1); a later pooled call rebuilds <key>.dat under another object and releasing the earlier results deletes it, so pooled results are unreadable. Docstrings and MIGRATION 030 promise the opposite. [disposition: fix now (owner 2026-10-05, option A): disarm delete-on-GC on every call; cache files persist after sequential runs too (extends accepted cost); round-4 review follows]"
  status: failed
  severity: blocker
  reason: "G2-CR-01: Entries created at n_jobs=1 keep their delete-on-GC hook (_release_gc_ownership runs only for n_jobs != 1); a later pooled call rebuilds <key>.dat under another object and releasing the earlier results deletes it, so pooled results are unreadable. Docstrings and MIGRATION 030 promise the opposite. [disposition: fix now (owner 2026-10-05, option A): disarm delete-on-GC on every call; cache files persist after sequential runs too (extends accepted cost); round-4 review follows]"
  test: review-r3-ad4b33fc2971
  root_cause: "07-16 disarm scoped to pooled calls; sequential results are the stores' own armed entries."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G2-CR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "BLOCKER (gsd-code-reviewer round 3) + high (/code-review 7094dde high); reproduced by orchestrator"

- truth: "G2-WR-01: In a non-owner process the soft gate's tolerated StorePurgeRefusedError also swallows the aliased/foreign-artefact refusal (upstream checks process id first), so a planted symlinked leftover k.dat -> other.dat redirects the replacement write into key 'other'. Docstring claim that these refusals still surface is false there. [disposition: fix now (owner 2026-10-05): re-raise when a leftover artefact is a symlink]"
  status: failed
  severity: major
  reason: "G2-WR-01: In a non-owner process the soft gate's tolerated StorePurgeRefusedError also swallows the aliased/foreign-artefact refusal (upstream checks process id first), so a planted symlinked leftover k.dat -> other.dat redirects the replacement write into key 'other'. Docstring claim that these refusals still surface is false there. [disposition: fix now (owner 2026-10-05): re-raise when a leftover artefact is a symlink]"
  test: review-r3-d167e3df49b7
  root_cause: "Exact-type tolerance cannot distinguish the pid refusal from a pid refusal that masks an aliased artefact."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G2-WR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (regression vs 7094dde) + low (/code-review)"

- truth: "G2-WR-02: The non-owner caveat (overwrite cannot disarm a retained dropped entry) is reachable through TiledPointCloudImageGenerator.generate(); docstring and MIGRATION 027 say generate() cannot reach it. [disposition: closed by the G2-CR-01 fix; docs and BC-P2I-027 corrected (owner 2026-10-05)]"
  status: failed
  severity: minor
  reason: "G2-WR-02: The non-owner caveat (overwrite cannot disarm a retained dropped entry) is reachable through TiledPointCloudImageGenerator.generate(); docstring and MIGRATION 027 say generate() cannot reach it. [disposition: closed by the G2-CR-01 fix; docs and BC-P2I-027 corrected (owner 2026-10-05)]"
  test: review-r3-8200412f7dcf
  root_cause: "Pooled call, n_jobs=1 add, del, regenerate, then the held result is collected -> replacement .dat deleted (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G2-WR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G2-WR-03: When one tile fails in a pooled call, a retry is refused for every tile that succeeded: their codec pairs are on disk but untracked in the parent's store copies; not covered by the documented triggers or workaround. [disposition: fix now (owner 2026-10-05): reset image_generators when a pooled dispatch raises]"
  status: failed
  severity: major
  reason: "G2-WR-03: When one tile fails in a pooled call, a retry is refused for every tile that succeeded: their codec pairs are on disk but untracked in the parent's store copies; not covered by the documented triggers or workaround. [disposition: fix now (owner 2026-10-05): reset image_generators when a pooled dispatch raises]"
  test: review-r3-34def3522da0
  root_cause: "Pooled generate() where one tile raises; retry generate() -> StorePurgeRefusedError at n_jobs=1 (2/2) and n_jobs=2 (1/1) (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G2-WR-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G2-WR-04: The popitem drop-route case survives the c2 mutation incidentally: popitem() reloads the entry (rewriting range.dat) and the test keeps it bound, sending the key down the lenient branch so the .npy check is never exercised. [disposition: fix the test (owner 2026-10-05)]"
  status: failed
  severity: minor
  reason: "G2-WR-04: The popitem drop-route case survives the c2 mutation incidentally: popitem() reloads the entry (rewriting range.dat) and the test keeps it bound, sending the key down the lenient branch so the .npy check is never exercised. [disposition: fix the test (owner 2026-10-05)]"
  test: review-r3-c8543a96e80d
  root_cause: "c2 mutant (no .npy hard check) with the popped value discarded serves the stale raster, yet the current popitem case passes (reviewer-reproduced)."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "G2-WR-04 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G2-IN-01: Class docstring overstates persistence: with default enable_caching=False no files are written (only empty mkdtemp dirs persist, as on baseline); without cache_path the path is <mkdtemp>/<key>.dat not <tile_id>/<key>.dat. MIGRATION 030 is correct, so they disagree. [disposition: fix (owner 2026-10-05)]"
  status: failed
  severity: minor
  reason: "G2-IN-01: Class docstring overstates persistence: with default enable_caching=False no files are written (only empty mkdtemp dirs persist, as on baseline); without cache_path the path is <mkdtemp>/<key>.dat not <tile_id>/<key>.dat. MIGRATION 030 is correct, so they disagree. [disposition: fix (owner 2026-10-05)]"
  test: review-r3-f18d53318c02
  root_cause: "Default-config user reads the docstring and expects leaked .dat files that are never written."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G2-IN-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G2-IN-02: The lone-memmap re-add verifier probe (BC-P2I-027) passes with the lenient branch deleted and on 7094dde; 07-18's cited mutation flipped the expected value, not the code. [disposition: fix the probe (owner 2026-10-05)]"
  status: failed
  severity: minor
  reason: "G2-IN-02: The lone-memmap re-add verifier probe (BC-P2I-027) passes with the lenient branch deleted and on 7094dde; 07-18's cited mutation flipped the expected value, not the code. [disposition: fix the probe (owner 2026-10-05)]"
  test: review-r3-ef792ab90c65
  root_cause: "Lenient branch removed from the store -> verifier still prints [ok] verified 30 entries (reviewer-reproduced)."
  artifacts:
    - path: ".planning/MIGRATION-v0.11.md"
      issue: "G2-IN-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G2-IN-03: Tile ids compared as exact strings, so 'Tile' and 'tile' would share one directory on case-insensitive filesystems (macOS/NTFS); pcd_tiles is mutable after construction. Not reproduced here. [disposition: defer]"
  status: deferred
  deferred_to: "after 0.11.0 (owner disposition 2026-10-05: unreproduced here -> cosmetic + defer)"
  severity: cosmetic
  reason: "G2-IN-03: Tile ids compared as exact strings, so 'Tile' and 'tile' would share one directory on case-insensitive filesystems (macOS/NTFS); pcd_tiles is mutable after construction. Not reproduced here. [disposition: defer]"
  test: review-r3-5697455e1d3b
  root_cause: "On a case-insensitive filesystem, tiles 'Tile' and 'tile' collide in one cache directory."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G2-IN-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP2.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

<!-- ROUND 4 — imported 2026-10-05T09:56:11Z by /gsd-consolidate-findings from gsd-code-review-deep+code-review-high (file:.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md+conversation), range c1b813d..08c8445.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "G3-WR-05: With caching on, retrying a failed tiled generate() inside the except block loses the retried <tile>/<key>.dat once the exception is released: entries created during the failed call stay armed (pooled: results joblib received; sequential: generators never stored) and the traceback keeps them alive. [disposition: defer + document as known limitation in the docs-only round (owner 2026-10-05)]"
  status: deferred
  deferred_to: "GSEGUtils#83 (GC hook deletes a shared <key>.dat) fix, then pc2img 0.11.1 (owner 2026-10-05: stop downstream fix-on-fix; create-time purge_disk_on_gc=False is the fallback, todo 2026-10-02-tiled-pooled-runs-leave-cache-files)"
  severity: major
  reason: "G3-WR-05: With caching on, retrying a failed tiled generate() inside the except block loses the retried <tile>/<key>.dat once the exception is released: entries created during the failed call stay armed (pooled: results joblib received; sequential: generators never stored) and the traceback keeps them alive. [disposition: defer + document as known limitation in the docs-only round (owner 2026-10-05)]"
  test: review-r4-5bb0fc0848a4
  root_cause: "enable_caching=True, cache_path set; generate() raises for one tile; retry generate() inside the except block; release the exception and gc.collect(); offload + read -> FileNotFoundError .../t0/range.dat (orchestrator reproduced; default config unaffected)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G3-WR-05 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "high (/code-review c1b813d high)"

- truth: "G3-WR-01: _release_gc_ownership runs only on success, so after a failed n_jobs=1 call the kept stores hold armed entries; releasing one held across a pooled call deletes the .dat that call reads; also reaches the non-owner caveat via the tiled generator. Docstring says this cannot happen. [disposition: defer; false docstring sentence fixed in the docs-only round (owner 2026-10-05)]"
  status: deferred
  deferred_to: "GSEGUtils#83 (GC hook deletes a shared <key>.dat) fix, then pc2img 0.11.1 (owner 2026-10-05: stop downstream fix-on-fix; create-time purge_disk_on_gc=False is the fallback, todo 2026-10-02-tiled-pooled-runs-leave-cache-files)"
  severity: major
  reason: "G3-WR-01: _release_gc_ownership runs only on success, so after a failed n_jobs=1 call the kept stores hold armed entries; releasing one held across a pooled call deletes the .dat that call reads; also reaches the non-owner caveat via the tiled generator. Docstring says this cannot happen. [disposition: defer; false docstring sentence fixed in the docs-only round (owner 2026-10-05)]"
  test: review-r4-a6997211a4d8
  root_cause: "Failed n_jobs=1 generate(), caller holds an entry from image_generators across a pooled call, releases it -> offload+read FileNotFoundError 2/2 (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G3-WR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING (gsd-code-reviewer round 4)"

- truth: "G3-WR-02: _refuse_linked_write_path judges aliasing by link location, upstream by target name: an adopted <key>.dat -> payload.bin (upstream-legitimate) and a dangling <key>.dat link are refused; the dangling case cannot be cleared through the API. c1b813d accepted both. [disposition: defer; documented (owner 2026-10-05)]"
  status: deferred
  deferred_to: "GSEGUtils#83 (GC hook deletes a shared <key>.dat) fix, then pc2img 0.11.1 (owner 2026-10-05: stop downstream fix-on-fix; create-time purge_disk_on_gc=False is the fallback, todo 2026-10-02-tiled-pooled-runs-leave-cache-files)"
  severity: minor
  reason: "G3-WR-02: _refuse_linked_write_path judges aliasing by link location, upstream by target name: an adopted <key>.dat -> payload.bin (upstream-legitimate) and a dangling <key>.dat link are refused; the dangling case cannot be cleared through the API. c1b813d accepted both. [disposition: defer; documented (owner 2026-10-05)]"
  test: review-r4-82b83c54e85a
  root_cause: "Adopted entry k.dat -> payload.bin in the cache dir: add_image_to_store('k', ...) raises StorePurgeAliasedArtefactError (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G3-WR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G3-WR-03: Failed-batch claim 'adopts those codec pairs' is false without cache_path: the retry rebuilds every tile store in a new temp dir, recomputes everything and leaves one old directory per tile; with enable_caching=False the reset protects nothing. [disposition: docs fix now (behaviour deferred) (owner 2026-10-05)]"
  status: failed
  severity: minor
  reason: "G3-WR-03: Failed-batch claim 'adopts those codec pairs' is false without cache_path: the retry rebuilds every tile store in a new temp dir, recomputes everything and leaves one old directory per tile; with enable_caching=False the reset protects nothing. [disposition: docs fix now (behaviour deferred) (owner 2026-10-05)]"
  test: review-r4-ec85539fdd58
  root_cause: "enable_caching=True, no cache_path, pooled failure then retry -> all features recomputed, old temp dirs remain (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G3-WR-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G3-WR-04: The disarm is persisted into .meta.json sidecars, so a later DiskBackedImageStore/PointCloudImageGenerator over the same directory inherits purge_disk_on_gc=False (history-dependent; silently overrides a caller's setting, e.g. iof3D). [disposition: docs fix now; behaviour goes away with the upstream fix (owner 2026-10-05)]"
  status: failed
  severity: minor
  reason: "G3-WR-04: The disarm is persisted into .meta.json sidecars, so a later DiskBackedImageStore/PointCloudImageGenerator over the same directory inherits purge_disk_on_gc=False (history-dependent; silently overrides a caller's setting, e.g. iof3D). [disposition: docs fix now; behaviour goes away with the upstream fix (owner 2026-10-05)]"
  test: review-r4-b8a25d8373eb
  root_cause: "Sequential then pooled call with caching on; open a new store over the tile directory -> entries report purge_disk_on_gc False (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G3-WR-04 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "WARNING"

- truth: "G3-IN-01: A symlink loop at a write path raises a bare RuntimeError from Path.resolve(), not the documented StorePurgeRefusedError family (not a regression). [disposition: defer (owner 2026-10-05)]"
  status: deferred
  deferred_to: "GSEGUtils#83 (GC hook deletes a shared <key>.dat) fix, then pc2img 0.11.1 (owner 2026-10-05: stop downstream fix-on-fix; create-time purge_disk_on_gc=False is the fallback, todo 2026-10-02-tiled-pooled-runs-leave-cache-files)"
  severity: cosmetic
  reason: "G3-IN-01: A symlink loop at a write path raises a bare RuntimeError from Path.resolve(), not the documented StorePurgeRefusedError family (not a regression). [disposition: defer (owner 2026-10-05)]"
  test: review-r4-f7b4125c2e42
  root_cause: "a.dat.tmp -> a.dat.tmp; add_image_to_store('a', ...) -> RuntimeError 'Symlink loop' (orchestrator reproduced)."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G3-IN-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO + low/medium (/code-review)"

- truth: "G3-IN-02: Three inaccurate failed-batch/ownership docstring sentences: a failing first n_jobs=1 call keeps no generators; the parent owns stores again after an n_jobs=1 retry following a pooled failure; at n_jobs=1 the rebuild is in the parent, not a worker. [disposition: docs fix now (owner 2026-10-05)]"
  status: failed
  severity: cosmetic
  reason: "G3-IN-02: Three inaccurate failed-batch/ownership docstring sentences: a failing first n_jobs=1 call keeps no generators; the parent owns stores again after an n_jobs=1 retry following a pooled failure; at n_jobs=1 the rebuild is in the parent, not a worker. [disposition: docs fix now (owner 2026-10-05)]"
  test: review-r4-1daadb31791a
  root_cause: "Reader relies on the docstring's failed-batch description and mispredicts ownership (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G3-IN-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

- truth: "G3-IN-03: The non-owner leg of the linked-write-path test passes on any StorePurgeRefusedError, so it cannot confirm the aliased class its docstring names (byte-identity check still guards writes). [disposition: defer (test-only) (owner 2026-10-05)]"
  status: deferred
  deferred_to: "GSEGUtils#83 (GC hook deletes a shared <key>.dat) fix, then pc2img 0.11.1 (owner 2026-10-05: stop downstream fix-on-fix; create-time purge_disk_on_gc=False is the fallback, todo 2026-10-02-tiled-pooled-runs-leave-cache-files)"
  severity: cosmetic
  reason: "G3-IN-03: The non-owner leg of the linked-write-path test passes on any StorePurgeRefusedError, so it cannot confirm the aliased class its docstring names (byte-identity check still guards writes). [disposition: defer (test-only) (owner 2026-10-05)]"
  test: review-r4-b19986674f87
  root_cause: "A different refusal subclass in the child still exits 3 and passes."
  artifacts:
    - path: "tests/test_image_store.py"
      issue: "G3-IN-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP3.md"
  missing: []
  debug_session: ""
  reviewer_severity: "INFO"

<!-- ROUND 5 — imported 2026-10-05T10:51:40Z by /gsd-consolidate-findings from gsd-code-review-standard+code-review-high (file:.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md+conversation), range cb85baa..f3e2787.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "G4-CR-01: Known-limitations retry text understates the hazard: retries inside the except block lose files at any n_jobs, and pooled failures lose files intermittently; 'a pooled failure ... did not lose files' is false. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: blocker
  reason: "G4-CR-01: Known-limitations retry text understates the hazard: retries inside the except block lose files at any n_jobs, and pooled failures lose files intermittently; 'a pooled failure ... did not lose files' is false. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-3a7e4c77dbb1
  root_cause: "Failing pooled call, retry inside except at n_jobs=1 -> lost files 2/12 and 4/8; pooled-pooled-pooled inside except lost 2/10 (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G4-CR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

- truth: "G4-CR-02: Documented mitigation 'run gc.collect() after the failure and before retrying' does nothing inside the except block (the live exception holds the entries); works only after leaving the block. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: blocker
  reason: "G4-CR-02: Documented mitigation 'run gc.collect() after the failure and before retrying' does nothing inside the except block (the live exception holds the entries); works only after leaving the block. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-0d6739aac7c4
  root_cause: "gc.collect() inside except, then retry -> LOST 3/3 (orchestrator) and 3/3 at n_jobs=1 and -1 (reviewer); gc.collect() after the block -> ok 3/3."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G4-CR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

- truth: "G4-WR-01: Hold-an-entry/regenerate/release limitation omits that it needs a prior pooled call; contradicts BC-P2I-027. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: minor
  reason: "G4-WR-01: Hold-an-entry/regenerate/release limitation omits that it needs a prior pooled call; contradicts BC-P2I-027. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-746be45f4769
  root_cause: "All calls at n_jobs=1: file survives 2/2; after a pooled call: deleted 2/2 (reviewer-reproduced)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G4-WR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

- truth: "G4-WR-02: The upstream-root-cause heading (GSEGUtils#83) covers two bullets that are pc2img's own _refuse_linked_write_path behaviour; test docstring calls the armed entries an upstream limitation. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: minor
  reason: "G4-WR-02: The upstream-root-cause heading (GSEGUtils#83) covers two bullets that are pc2img's own _refuse_linked_write_path behaviour; test docstring calls the armed entries an upstream limitation. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-65c5e3e73089
  root_cause: "Reader attributes the link-classification and RuntimeError-on-loop behaviour to GSEGUtils#83 and expects 0.11.1 to change them via upstream."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G4-WR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

- truth: "G4-WR-03: Sidecar rule 'two pooled calls leave it False' holds per key, not per call; offload(pickle_container=True) also writes the sidecar. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: minor
  reason: "G4-WR-03: Sidecar rule 'two pooled calls leave it False' holds per key, not per call; offload(pickle_container=True) also writes the sidecar. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-302838217be9
  root_cause: "A key first computed in a later pooled call is written True (reviewer-reproduced)."
  artifacts:
    - path: ".planning/MIGRATION-v0.11.md"
      issue: "G4-WR-03 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

- truth: "G4-IN-01: 'A dangling <key>.dat link cannot be cleared through purge' is true only when the key is untracked and has no <key>.npy. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: cosmetic
  reason: "G4-IN-01: 'A dangling <key>.dat link cannot be cleared through purge' is true only when the key is untracked and has no <key>.npy. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-8c6a56cd8bb7
  root_cause: "Tracked key or .npy on disk: purge removes the dangling link (reviewer-reproduced)."
  artifacts:
    - path: ".planning/MIGRATION-v0.11.md"
      issue: "G4-IN-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

- truth: "G4-IN-02: 'The disarm runs only after a call returns' should say 'returns successfully'. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  status: failed
  severity: cosmetic
  reason: "G4-IN-02: 'The disarm runs only after a call returns' should say 'returns successfully'. [disposition: fixed by the conservative docs rewrite (owner 2026-10-05): recommendations and 'may' statements only, measured detail stays in SUMMARY files]"
  test: review-r5-28e3f3ba5f32
  root_cause: "Reader assumes a failed call's returned-before-failure entries are disarmed."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G4-IN-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP4.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 5 / /code-review cb85baa high"

<!-- ROUND 6 — imported 2026-10-05T12:23:42Z by /gsd-consolidate-findings from gsd-code-review-standard+code-review-high (file:.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP5.md+conversation), range c43d6f0..69f2264.
     NOTE: entries live under the single `## Gaps` heading on purpose —
     the audit parser matches /^gaps$/i, so a decorated heading such as
     `## Gaps — Round N` would make every entry below invisible. -->

- truth: "G5-CR-02: Persistence sentences (class docstring, generate(), store 'Only purge removes files', BC-P2I-030) say unconditionally that kept-store entries and dropped generators never delete their files, whatever n_jobs; false after a failed call. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  status: failed
  severity: blocker
  reason: "G5-CR-02: Persistence sentences (class docstring, generate(), store 'Only purge removes files', BC-P2I-030) say unconditionally that kept-store entries and dropped generators never delete their files, whatever n_jobs; false after a failed call. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  test: review-r6-f4ed37a717fa
  root_cause: "Successful first call, failing n_jobs=1 call, drop generators -> t0/gradient_x_range.dat and t0/scalar_field_intensity.dat deleted (reviewer-reproduced, sequential and pooled first call)."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G5-CR-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP5.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 6 / /code-review c43d6f0 high"

- truth: "G5-CR-01: Recommended retry route 'let the exception go out of scope, gc.collect(), retry' fails in interactive sessions/debuggers: sys.last_exc/last_value/last_traceback keep the failed call alive; fresh cache_path route works. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  status: failed
  severity: blocker
  reason: "G5-CR-01: Recommended retry route 'let the exception go out of scope, gc.collect(), retry' fails in interactive sessions/debuggers: sys.last_exc/last_value/last_traceback keep the failed call alive; fresh cache_path route works. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  test: review-r6-cead7cdb1c75
  root_cause: "Interactive prompt: n_jobs=1 failure, gc route retry, later typo replaces sys.last_* -> retried raster deleted 3/3; pooled failure 4/6 (reviewer-reproduced); scripts 0/204 lost."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G5-CR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP5.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 6 / /code-review c43d6f0 high"

- truth: "G5-WR-01: 07-23 removed the dangling-link recovery note everywhere; a refused write leaves the user no documented way out (purge raises KeyError on an untracked dangling <key>.dat link; must unlink by hand). [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  status: failed
  severity: minor
  reason: "G5-WR-01: 07-23 removed the dangling-link recovery note everywhere; a refused write leaves the user no documented way out (purge raises KeyError on an untracked dangling <key>.dat link; must unlink by hand). [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  test: review-r6-780173a7f690
  root_cause: "Dangling k.dat link in cache dir: add_image_to_store -> StorePurgeAliasedArtefactError; purge('k') -> KeyError, link remains (/code-review reproduced)."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G5-WR-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP5.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 6 / /code-review c43d6f0 high"

- truth: "G5-IN-01: Store docstring/BC-P2I-027 frame 'do not hold entries' generally and say the fix 'follows in 0.11.1'; class docstring/BC-P2I-030 put it under 'after a failed call' and say 'planned'. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  status: failed
  severity: cosmetic
  reason: "G5-IN-01: Store docstring/BC-P2I-027 frame 'do not hold entries' generally and say the fix 'follows in 0.11.1'; class docstring/BC-P2I-030 put it under 'after a failed call' and say 'planned'. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  test: review-r6-313259be96bf
  root_cause: "Reader sees inconsistent scope and release status for the same limitation."
  artifacts:
    - path: "src/pc2img/image_cache/disk_backed_image_store.py"
      issue: "G5-IN-01 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP5.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 6 / /code-review c43d6f0 high"

- truth: "G5-IN-02: 'gc.collect() there collects nothing' overstates: inside the handler it collects other garbage, just not the failed call's objects. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  status: failed
  severity: cosmetic
  reason: "G5-IN-02: 'gc.collect() there collects nothing' overstates: inside the handler it collects other garbage, just not the failed call's objects. [disposition: wording fix in 07-24 (owner 2026-10-05), final check scoped to that fix]"
  test: review-r6-231bed78613d
  root_cause: "Reader infers gc.collect() is a no-op inside except."
  artifacts:
    - path: "src/pc2img/tiled_generator.py"
      issue: "G5-IN-02 — see .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-REVIEW-GAP5.md"
  missing: []
  debug_session: ""
  reviewer_severity: "gsd-code-reviewer round 6 / /code-review c43d6f0 high"