---
phase: 06-publication-hardening-downstream-migration-record
plan: 16
subsystem: quality
tags: [docstrings, hygiene-gate, pre-commit, github-actions, ast-identity, yaml-identity]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "06-15's removal of the migration record from the shipped tree, so the extended planning-vocabulary gate's first whole-tree run can be green; 06-REVIEW.md's WR-03/WR-04/IN-04/IN-13 findings and reproduction values"
provides:
  - "src/pc2img/strategies/projection.py: ProjectionStrategy.project_raw ABC docstring corrected to the (M, 2)/mask.sum()/mask-length-N/FoV-or-ROI-else-kept-extent contract every implementation and core.py actually follow"
  - "tests/test_projection.py: three contract-pinning tests proving the corrected contract by executing SphericalProjection with a culling FoV and OrthographicProjection with and without an ROI box"
  - "tests/test_hygiene.py: single-exemption planning-vocabulary gate (the .pre-commit-config.yaml exemption removed and the file itself brought under scan); _PHASE_PLAN_PATTERN extended with two character-class-spelled prose alternatives (this-phase/this-milestone, gap-closure) plus a positive self-check and an extended negative self-check"
  - ".pre-commit-config.yaml: exclude regex's planning-directory alternative re-spelled with a character class, scoring zero hygiene-gate hits while matching the same paths"
  - "Seven .github/ files: a one-line 'not part of this assembly' note at every reference to a declined kit component (check_ci_config.py, integrity.yml, ruleset-drift.yml, assert_no_skip.py), with no executable-logic change"
affects: ["06-17 (records this plan's gate re-run in .planning/CICD-ADOPTION-RECORD.md's placeholder)", "06-18 (flips WR-03/WR-04/IN-04/IN-13 to resolved in 06-UAT.md, contingent on this diff's own review per the global gap-closure review-discipline rule)"]

actuals:
  tokens: 4430
  tasks: 3
  commits: 3
plan_head_before: a2285da8d83b8fd999c8bc0c6a001d7a30684574
plan_head_after: d9e86d3823a06ee742417415eca8638fe71fd897

tech-stack:
  added: []
  patterns:
    - "AST/YAML identity proof against the phase-PR merge commit (6c10ee0), not against the previous plan's HEAD: this gap-closure round's 'no behaviour change' claims are anchored to the tree's last shipped state, so any drift since 06-15 would also surface"
    - "Same self-match-avoidance trick as _PLANNING_DIR (string parts / character classes) applied to newly-added gate patterns: any alternative a gate's own source text could literally satisfy must be spelled so the gate's tracked source never contiguous-matches its own new pattern"
    - "A 'no logic changed, comment-only' proof must be checked against the target format's actual parse model, not assumed uniform: a composite action's run: block is a single YAML string scalar, so a comment added inside it changes that scalar's value under yaml.safe_load equality even though nothing executable changed. The fix is to place the note in genuine YAML-comment territory (between sibling top-level keys, outside any block scalar), not wherever the grep hit landed."

key-files:
  created: []
  modified:
    - src/pc2img/strategies/projection.py
    - tests/test_projection.py
    - tests/test_hygiene.py
    - .pre-commit-config.yaml
    - .github/workflows/ruleset-apply.yml
    - .github/workflows/ci.yml
    - .github/workflows/scheduled-health.yml
    - .github/actions/classify-changes/action.yml
    - .github/scripts/check_ruleset_drift.py
    - .github/scripts/ruleset_lib.py
    - .github/scripts/check_publish_gate.py

key-decisions:
  - "WR-03: rewrote only the ABC docstring's Returns section (coords_raw is (M, 2) with M == mask.sum() for KEPT points; mask is length-N over the full cloud with an explicit note that project() and the generator pair coords_raw's rows positionally with mask-selected values; mins/maxs are the FoV/ROI-else-kept-extent frame). No implementation changed -- AST-identical to 6c10ee0 with docstrings stripped."
  - "WR-04: removed the .pre-commit-config.yaml entry from tests/test_hygiene.py's _EXEMPTIONS (the signed IP-clearance record is now the sole exemption) and re-spelled the exclude regex's planning-directory alternative with a character class (plan[n]ing), matching the same six sample-path decisions before and after."
  - "IN-13: extended _PHASE_PLAN_PATTERN with two character-class-spelled alternatives (this[ ](phase|milestone), gap[- ]closure) so the gate catches the prose the review found without the gate's own source self-matching; reworded the two 'deferred to the bug-fix phase' sentences in test_hygiene.py's module docstring/comments and the ruleset-apply.yml token-mint comment's 'this phase' reference. The whole shipped tree (88 hygiene-gate parametrizations) passes the extended gate."
  - "IN-04: added the identical 'not part of this assembly ... see RULESETS.md' note at the first declined-component reference in each of the seven files. For .github/actions/classify-changes/action.yml the note was placed between the description block and outputs: (genuine top-level YAML comment territory) rather than inside the file's single run: script step where the plan's cited line numbers (64-74) sit -- see Deviations."
  - "Deviation (documented, resolved, logged and closed in .planning/WINDOWS.md entry 1): the plan's Task 3 action described adding the note 'at the FIRST comment or docstring line that names a declined component' and cited action.yml lines 64-74/176-186 as reference sites, both inside that file's sole run: block. A composite action's run: field is one YAML literal-scalar string, so editing any text inside it -- including a bash comment -- changes that scalar's value, and the task's own required YAML-parse-identity proof (yaml.safe_load(HEAD) == yaml.safe_load(working tree)) would fail. Relocated the note to the nearest genuine top-level YAML comment position instead; re-verified identity holds for all four YAML files."

requirements-completed: []  # CICD-02 is shared across most/several phase-06 plans; withheld until every declaring plan's SUMMARY exists (shared-ID gate, #2388) -- 06-17 and 06-18 have not yet run.

coverage:
  - id: D1
    description: "WR-03 closed: ProjectionStrategy.project_raw's docstring documents the (M, 2)/mask.sum()/length-N-mask/positional-pairing/FoV-or-ROI-else-kept-extent contract every implementation and core.py actually follow, pinned by three tests that run SphericalProjection with a culling FoV (mask.sum()=17 of 1000) and OrthographicProjection with (mask.sum()=13 of 32) and without an ROI box"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "tests/test_projection.py#test_project_raw_returns_kept_points_and_fov_frame_spherical"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py#test_project_raw_returns_kept_points_and_roi_frame_orthographic"
        status: pass
      - kind: unit
        ref: "tests/test_projection.py#test_project_pairs_pts2d_rows_with_mask"
        status: pass
      - kind: other
        ref: "AST-identity one-liner (docstrings stripped) against 6c10ee0:src/pc2img/strategies/projection.py -> 'ast-identical'"
        status: pass
      - kind: other
        ref: "uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html -> build succeeded, no WARNING/ERROR lines"
        status: pass
    human_judgment: false
  - id: D2
    description: "WR-04 closed: .pre-commit-config.yaml is scanned by the planning-vocabulary gate (its file-wide exemption removed) and yields zero hits; the compiled exclude regex is decision-identical for the six sample paths before/after the character-class re-spelling; the gate's docstring now correctly states a single exemption"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "manual command: python -c \"... assert len(h._EXEMPTIONS) == 1 ...  h._matches(open('.pre-commit-config.yaml').read()) == [] ...\" -> gate-ok"
        status: pass
      - kind: other
        ref: "manual command: compiled exclude regex against ['.planning/phases/x.md', '.planning/config.json', '.claude/CLAUDE.md', 'CHANGELOG.md', 'docs/ip/rrim-eth-signoff.md', 'src/pc2img/core.py'] -> [True, True, True, True, True, False] both before and after"
        status: pass
      - kind: unit
        ref: "tests/test_hygiene.py -q -> 88 passed (whole shipped tree, including .pre-commit-config.yaml itself)"
        status: pass
    human_judgment: false
  - id: D3
    description: "IN-13 closed: the gate additionally flags 'this phase', 'this milestone', 'gap-closure' and 'gap closure' (character-class spelled in the gate's own source), with a positive self-check proving they are caught and an extended negative self-check proving 'two-phase ... contract', 'phase unwrapping', 'bug-fix pass', BC-P2I/BC-GSEG identifiers and an ISO date are not; the ruleset-apply.yml token-mint comment reworded ('this phase' -> 'these workflows') and the whole shipped tree passes the extended gate"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "tests/test_hygiene.py#test_prose_planning_phrases_are_flagged"
        status: pass
      - kind: unit
        ref: "tests/test_hygiene.py#test_public_identifiers_are_not_flagged"
        status: pass
      - kind: unit
        ref: "tests/test_hygiene.py -q -> 88 passed (parametrized gate over every git-tracked, unexempted path)"
        status: pass
    human_judgment: false
  - id: D4
    description: "IN-04 closed: every shipped non-test file under .github/ naming a declined kit component carries the 'not part of this assembly ... see RULESETS.md' note; no executable logic changed (YAML parses to the same object against 6c10ee0 for all four YAML files, Python ASTs identical with docstrings stripped for all three Python files); the kit's tests stay green"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "manual command: git grep -lE 'check_ci_config|integrity\\.yml|ruleset-drift\\.yml|assert_no_skip' -- .github ':!.github/scripts/test_*.py' | loop grep 'not part of this assembly' -> marked-ok (all 7 files)"
        status: pass
      - kind: other
        ref: "manual command: yaml.safe_load(6c10ee0:<file>) == yaml.safe_load(<file>) for ci.yml, scheduled-health.yml, ruleset-apply.yml, classify-changes/action.yml -> 4x yaml-same"
        status: pass
      - kind: other
        ref: "manual command: AST-identity one-liner (docstrings stripped) for check_ruleset_drift.py, ruleset_lib.py, check_publish_gate.py against 6c10ee0 -> 3x ast-same"
        status: pass
      - kind: unit
        ref: "uv run --frozen pytest .github/scripts -q -> 92 passed"
        status: pass
      - kind: other
        ref: "git diff --name-only 6c10ee0 -- .github/scripts/test_check_publish_gate.py .github/scripts/test_check_ruleset_drift.py .github/scripts/test_classify_changes.py .github/scripts/test_preflight_ruleset_apply.py .github/scripts/test_ruleset_lib.py -> empty (kit test files untouched)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Whole-tree gates stay green after all three tasks: full pytest suite (286 passed, up from 282 in 06-15's baseline: +3 projection tests, +1 hygiene test), pre-commit run --all-files (all hooks Passed), docs build clean"
    verification:
      - kind: unit
        ref: "uv run --frozen pytest -q -> 286 passed"
        status: pass
      - kind: other
        ref: "uv run --frozen pre-commit run --all-files -> all hooks Passed"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-29
status: complete
---

# Phase 6 Plan 16: Projection-Contract Docstring, Vocabulary-Gate Exemption Removal, and Declined-Component Notes Summary

**Corrected `ProjectionStrategy.project_raw`'s ABC docstring to the kept-point `(M, 2)` contract every implementation already follows (pinned by three new tests), removed the false-justified `.pre-commit-config.yaml` hygiene exemption and extended the planning-vocabulary gate's prose patterns, and marked every shipped `.github/` reference to a declined kit component — each claim established by running code, not by reading.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-29T08:18:00Z
- **Completed:** 2026-09-29T08:33:00Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- **WR-03 (project_raw contract):** Reproduced the contract inversion by executing `SphericalProjection` with `FoV(left=-0.1, right=0.2, top=1.4, bottom=1.8)` on a 1000-point synthetic cloud (`mask.sum() == 17`, `coords_raw.shape == (17, 2)`, not `(1000, 2)`) and `OrthographicProjection` with an ROI box on a 32-point cloud (`mask.sum() == 13`). Rewrote only the ABC docstring's `Returns` section — no implementation touched, confirmed by an AST-identity check (docstrings stripped) against the phase-PR merge commit `6c10ee0`. Three new tests in `tests/test_projection.py` pin the corrected contract by running the real strategies, not by asserting against the (previously wrong) docstring. `sphinx-build -W --keep-going` still builds clean.
- **WR-04 (pre-commit exemption):** Removed the `.pre-commit-config.yaml` entry from `tests/test_hygiene.py`'s `_EXEMPTIONS`, leaving the signed IP-clearance record as the sole exemption (the module docstring's count corrected to match). Re-spelled the exclude regex's planning-directory alternative with a character class (`\.plan[n]ing/.*`), which the gate's own matcher confirms yields zero hits on the file while the compiled regex gives identical `match()` decisions for all six review-cited sample paths before and after.
- **IN-13 (prose vocabulary):** Extended `_PHASE_PLAN_PATTERN` with `\bthis[ ](?:phase|milestone)\b` and `\bgap[- ]closure\b`, both character-class spelled (mirroring `_PLANNING_DIR`'s trick) so the gate's own tracked source never self-matches. Added `test_prose_planning_phrases_are_flagged` (built from string parts, same reason) and extended `test_public_identifiers_are_not_flagged` with the six review-listed safe phrases. Reworded the two `test_hygiene.py` "deferred to the bug-fix phase" sentences and `ruleset-apply.yml`'s "THE one place in this phase" token-mint comment. The full 88-parametrization gate over the whole shipped tree is green — this plan runs after 06-15 moved the migration record under `.planning/`, so nothing else in the tree trips the new alternatives.
- **IN-04 (declined-component notes):** Added the identical `(not part of this assembly: the config self-inspection and continuous-enforcement components were declined; see RULESETS.md)` note at the first declined-component reference in `ci.yml`, `scheduled-health.yml`, `ruleset-apply.yml`, `classify-changes/action.yml`, `check_ruleset_drift.py`, `ruleset_lib.py`, and `check_publish_gate.py`. No executable logic changed — verified with `yaml.safe_load` identity (4 YAML files) and AST identity with docstrings stripped (3 Python files) against `6c10ee0`. See Deviations for the one placement adjustment this required.

## Task Commits

Each task was committed atomically:

1. **Task 1 (tracer): Pin the real project_raw contract, then correct the docstring (WR-03)** — `158a569` docs(projection): document the kept-point (M, 2) contract project_raw implementations actually follow
2. **Task 2: Remove the pre-commit exemption and extend the vocabulary gate (WR-04, IN-13)** — `5bb45dd` test(hygiene): scan the pre-commit config and flag prose planning phrases
3. **Task 3: Note the declined kit components at every shipped reference (IN-04)** — `d9e86d3` ci(comments): mark the declined kit components at every reference

**Plan metadata:** (this commit)

_Note: `workflow.tdd_mode` is off and this plan's frontmatter is `type: execute`, so the plan-level RED/GREEN/REFACTOR gate does not apply. Tasks 1 and 2 carry `tdd="true"` in the plan's characterization-testing sense the plan's own action text specifies: the new tests pin *existing, correct* behaviour (the bug was in the docstring/exemption reasoning, not the code) and pass on their first run, so there is no separate RED commit — this matches the plan's explicit instruction to "record their first run as green in the SUMMARY."_

## Files Created/Modified

- `src/pc2img/strategies/projection.py` — `ProjectionStrategy.project_raw` ABC docstring corrected (docstring-only)
- `tests/test_projection.py` — three contract-pinning tests added
- `tests/test_hygiene.py` — single exemption; extended `_PHASE_PLAN_PATTERN`; new positive self-check; extended negative self-check; reworded "bug-fix phase" sentences
- `.pre-commit-config.yaml` — planning-directory exclude alternative re-spelled with a character class
- `.github/workflows/ruleset-apply.yml` — token-mint comment reworded; declined-component note added
- `.github/workflows/ci.yml` — declined-component note added
- `.github/workflows/scheduled-health.yml` — declined-component note added
- `.github/actions/classify-changes/action.yml` — declined-component note added (between description and outputs:)
- `.github/scripts/check_ruleset_drift.py` — declined-component note added to module docstring
- `.github/scripts/ruleset_lib.py` — declined-component note added to module docstring
- `.github/scripts/check_publish_gate.py` — declined-component note added as an inline comment

## Decisions Made

See `key-decisions` in the frontmatter. In short: WR-03/WR-04/IN-13/IN-04 all closed exactly as the review's reproductions specified; the one adjustment was IN-04's `action.yml` note placement, moved out of the file's `run:` block to preserve YAML-parse identity (documented below and in `.planning/WINDOWS.md` entry 1, recorded then immediately marked fixed since the adjustment is complete and re-verified).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `action.yml`'s declined-component note relocated out of its `run:` script block to preserve YAML-parse identity**
- **Found during:** Task 3, running the plan's own required `yaml.safe_load` identity check against `6c10ee0`
- **Issue:** The plan's read_first/action text cited `.github/actions/classify-changes/action.yml` lines 64-74 and 176-186 as the file's declined-component reference sites, and instructed adding the note "at the FIRST comment or docstring line that names a declined component" — line 67, inside the file's single `run: |` step. That step's entire body is one YAML literal-scalar string; `yaml.safe_load` parses it as one opaque value, so *any* text change inside it — including a bash `#` comment with no executable effect — changes that scalar under Python `==` comparison. Adding the note there made the task's own required identity check (`yaml.safe_load(6c10ee0:action.yml) == yaml.safe_load(action.yml)`) fail with an `AssertionError`, even though nothing executable changed.
- **Fix:** Relocated the note to the blank line between the file's `description: >` folded block and the `outputs:` key — genuine top-level YAML comment territory outside any block scalar, where a `#` line is stripped entirely by the parser and never enters the parsed value. Re-ran the identity check: `yaml-same` for all four YAML files (`ci.yml`, `scheduled-health.yml`, `ruleset-apply.yml`, `classify-changes/action.yml`).
- **Files modified:** `.github/actions/classify-changes/action.yml`
- **Verification:** `yaml.safe_load` identity holds against `6c10ee0` for all four files; `grep -q 'not part of this assembly'` still finds the note (the file-level `marked-ok` check does not require line-adjacency to the specific grep hit, only file-level presence); full test suite and `pre-commit run --all-files` green afterward
- **Committed in:** `d9e86d3` (Task 3 commit)
- **Ledger:** recorded as `.planning/WINDOWS.md` entry 1 (`--kind deviation`), then marked `fixed` in the same session since the relocation is complete and re-verified — nothing remains open

---

**Total deviations:** 1 auto-fixed (Rule 3, YAML-identity-preserving relocation).
**Impact on plan:** None on the delivered fixes — WR-03, WR-04, IN-13, and IN-04 are all closed with the plan's own re-run commands passing. The relocation changes only *where inside one file* the required note sits, not its content, its file-level presence, or any of the four required-headings/AST/YAML identity proofs.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `06-UAT.md`'s WR-03, WR-04, IN-04, and IN-13 each have a proving command re-run and commit evidence in-tree, ready to be flipped to `resolved` in plan 06-18 — **contingent on this gap-closure diff having had its own review first** (global review-discipline rule: gap-closure fixes get their own review before the phase re-verifies; this diff has not yet been reviewed).
- `CICD-02` stays unmarked in `REQUIREMENTS.md` until every declaring plan's `SUMMARY.md` exists (shared-ID gate, #2388) — 06-17 and 06-18 have not yet run.
- No push, pull request, workflow dispatch, or index upload happened in this plan — every commit stays on the phase branch.
- `.planning/WINDOWS.md` now exists (previously absent) with one entry, already resolved (`fixed`) in this same plan.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-29*

## Self-Check: PASSED

- All 11 modified files FOUND on disk (`src/pc2img/strategies/projection.py`, `tests/test_projection.py`, `tests/test_hygiene.py`, `.pre-commit-config.yaml`, and the seven `.github/` files)
- This SUMMARY FOUND at `.planning/phases/06-publication-hardening-downstream-migration-record/06-16-SUMMARY.md`
- Commits `158a569`, `5bb45dd`, `d9e86d3` — all FOUND in `git log --oneline --all`
- All plan-level `<verification>`/task `<verify>` commands re-run clean immediately before writing this SUMMARY: `tests/test_projection.py` (27 passed) and `tests/test_hygiene.py` (88 passed) green; AST-identity ('ast-identical'/'ast-same' x4) and YAML-identity ('yaml-same' x4) proofs against `6c10ee0` all printed; `sphinx-build -W --keep-going` build succeeded with no warnings; `uv run --frozen pytest -q` → 286 passed; `uv run --frozen pre-commit run --all-files` → all hooks Passed; `uv run --frozen pytest .github/scripts -q` → 92 passed; kit test files (`git diff --name-only 6c10ee0 -- .github/scripts/test_*.py`) unchanged
