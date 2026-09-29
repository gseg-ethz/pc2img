---
phase: 06-publication-hardening-downstream-migration-record
plan: 15
subsystem: infra
tags: [migration-record, ci-cd-docs, github-rulesets, release-process, readme]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "MIGRATION-v0.11.md draft (06-04), RULESETS.md/RELEASE.md apply-time checklist and pre-promotion gate (06-07), 06-13's extraction command pointed at .planning/MIGRATION-v0.11.md, mid-phase code review (06-09 precondition) surfacing WR-10/IN-05/IN-10, owner review-round decisions D-33/D-34 (06-CONTEXT.md)"
provides:
  - ".planning/MIGRATION-v0.11.md: the draft migration record, git-renamed from the repository root, with a self-consistent extraction command and a one-sentence internal-location note"
  - ".planning/CICD-ADOPTION-RECORD.md: the full CI/CD adoption record (copied from pre-condensation RULESETS.md), corrected for WR-10/IN-05/D-33, plus four appended sections (release-process full record, review-round changes, cross-repository notes, gate re-runs)"
  - "RULESETS.md condensed to 142 lines: WR-10 (every-promotion-and-release-PR-merge back-merge, correct f946268/69224a9/ade40f8 rationale) and IN-05 (procedural ruleset-creation wording) closed"
  - "RELEASE.md condensed to 100 lines, both claim tables and headings later plans read intact"
  - "README.rst: IN-10 README/index half closed (three projections named, matching docs/source/index.rst)"
affects: ["06-16 (WR-03/WR-04/IN-04/IN-13 closure — reads the same public docs)", "06-17 (records the gate re-run this record's '## Gate re-runs' section points at)", "06-18 (flips WR-10/IN-05/IN-10 to resolved in 06-UAT.md)", "Phase 7 (D-29 finalization of .planning/MIGRATION-v0.11.md; the IN-07 pre-commit/lock ruff-version drift this plan's own whole-tree verify surfaced)"]

actuals:
  tokens: 18800
  tasks: 3
  commits: 4
plan_head_before: e1dfbdafe43ea188d94e0b637e309b35a9a89b86
plan_head_after: 4fc329b33cd5ff33b3d8cf65532c2d23f90e3b0b

tech-stack:
  added: []
  patterns:
    - "Copy-then-correct-in-place preservation: .planning/CICD-ADOPTION-RECORD.md is a straight `cp` of the pre-condensation RULESETS.md with three targeted corrections and four appended sections, not a re-authored summary -- every checklist item and the recorded gate output survive byte-for-byte where unrelated to a correction"
    - "Whole-tree verify widens scope under Rule 3: a plan whose own <verify> block runs pre-commit/hygiene gates over the entire tree must accept and commit any auto-fix those gates produce on files outside the plan's own <files> list, or the verify never goes green"

key-files:
  created:
    - .planning/CICD-ADOPTION-RECORD.md
  modified:
    - MIGRATION-v0.11.md (renamed to .planning/MIGRATION-v0.11.md)
    - .planning/phases/06-publication-hardening-downstream-migration-record/06-VALIDATION.md
    - RULESETS.md
    - RELEASE.md
    - README.rst
    - .github/scripts/test_publish_ref_guard.py (incidental ruff-format reformat, Rule 3)

key-decisions:
  - "D-33/D-34 executed exactly as the owner decided: the draft migration record moved under .planning/ via git rename (history preserved, verifier re-pointed and re-run green); RULESETS.md and RELEASE.md stay at the root but condensed to maintainer scope (142 and 100 lines); the full adoption record D-15 required is preserved, not deleted, in .planning/CICD-ADOPTION-RECORD.md"
  - "WR-10 fix: replaced the false 'no common ancestor' rationale with the measured merge-base f946268 plus the two main-only commits (69224a9, ade40f8); the back-merge rule now fires after every promotion AND every release-PR merge, not only after releases"
  - "IN-05 fix: RULESETS.md's ruleset-creation wording rewritten from a past-tense claim ('was done once') to a procedure, so the public doc never asserts a ruleset exists before the apply workflow creates it"
  - "IN-10 (README/index half) fix: README.rst now names the same three projections (spherical, orthographic, perspective) as docs/source/index.rst and the strategy registry"
  - "Rule 3 deviation: the whole-tree `pre-commit run --all-files` this task's own <verify> requires triggered a ruff-format reformat of .github/scripts/test_publish_ref_guard.py (a 06-14 file, unrelated to this plan's <files>) -- accepted the mechanical line-join-only reformat rather than leaving the required verify command red; no semantic change, confirmed by re-running the full test suite (282 passed) afterward"
  - "The plan's own word-check verify command (`words = ['gsd', ...]`) has a false positive on the literal, required branch name `develop-gsd` in RULESETS.md -- confirmed by testing the regex directly against the isolated string. Ran a corrected version of the same check (excluding the legitimate branch-name substring) to prove the actual no-agent-workflow-vocabulary requirement is met; documented rather than silently worked around, per the deviation-documentation contract"

requirements-completed: []  # CICD-02 and BC-01 both shared across most/several phase-06 plans (06-01..06-18); withheld until every declaring plan's SUMMARY exists (shared-ID gate, #2388) -- 06-16/06-17/06-18 have not yet run

coverage:
  - id: D1
    description: "D-33 executed: the draft migration record moved from the repository root to .planning/MIGRATION-v0.11.md as a tracked git rename; the extraction command in its own docstring is the one actually run, and the verifier prints [ok] verified 25 entries from the repository root; the diff against the pre-move file touches only the docstring's extraction command lines and one added location sentence; 06-VALIDATION.md repointed"
    requirement: "BC-01"
    verification:
      - kind: unit
        ref: "manual command: mkdir -p _scrap && awk extraction + uv run --frozen python _scrap/pc2img-migration-verifier.py -> '[ok] verified 25 entries'"
        status: pass
      - kind: other
        ref: "git log -1 -M --name-status on the move commit: exactly one R100-class rename line MIGRATION-v0.11.md -> .planning/MIGRATION-v0.11.md"
        status: pass
      - kind: other
        ref: "git diff 6c10ee0:MIGRATION-v0.11.md HEAD:.planning/MIGRATION-v0.11.md filtered to BC-P2I- table rows: empty (entries-untouched)"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-34/D-15 executed: the full CI/CD adoption record is preserved at .planning/CICD-ADOPTION-RECORD.md (copy of pre-condensation RULESETS.md, all 12 apply-time checklist items and the recorded 278-passed pre-promotion gate intact), with the WR-10 rationale/rule and the IN-05 ruleset-creation wording corrected in place, plus four appended sections"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "manual command: grep -cE '^\\*\\*[0-9]{1,2}\\. ' .planning/CICD-ADOPTION-RECORD.md -> 12; grep -c '278 passed' -> 1; per-heading presence loop over all 12 required headings -> sections-ok"
        status: pass
      - kind: unit
        ref: "manual command: grep -c 'not currently share a common ancestor' -> 0; grep -c 'was done once' -> 0; grep -c 'f946268'/'69224a9'/'after every promotion' -> all >=1"
        status: pass
    human_judgment: false
  - id: D3
    description: "WR-10 and IN-05 closed in the condensed public RULESETS.md (142 lines): the '## Promotion and back-merge' section requires a true-merge back-merge after every promotion and every release-PR merge with the correct f946268/69224a9/ade40f8 rationale; '## Applying the rulesets' is procedural, asserting no ruleset exists yet"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "manual command: size/heading/rationale grep block in the plan's Task 3 <verify> (sizes-ok 142 100; heading and rationale counts all >=1)"
        status: pass
      - kind: other
        ref: "uv run --frozen pytest tests/test_hygiene.py -q -k 'planning_vocabulary and (RULESETS or RELEASE or README or index)' -> 9 passed"
        status: pass
      - kind: other
        ref: "corrected word-check (develop-gsd branch name excluded) -> wording-ok"
        status: pass
    human_judgment: false
  - id: D4
    description: "IN-10 (README/index half) closed: README.rst names spherical, orthographic and perspective, matching docs/source/index.rst and the PROJECTIONS registry; README.rst still passes twine check as the PyPI long description"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "manual command: grep -c perspective on both files -> 1 each; rm -rf dist && uv build && uvx twine check dist/* | grep -c PASSED -> 2"
        status: pass
    human_judgment: false
  - id: D5
    description: "Whole-tree gates stay green after the condensation: full pytest suite (282 passed), pre-commit run --all-files (all hooks Passed), uv lock --check clean"
    verification:
      - kind: unit
        ref: "uv run --frozen pytest -q -> 282 passed"
        status: pass
      - kind: other
        ref: "uv run --frozen pre-commit run --all-files -> all hooks Passed"
        status: pass
    human_judgment: false

duration: 55min
completed: 2026-09-29
status: complete
---

# Phase 6 Plan 15: Migration-Record Relocation and Public-Doc Condensation Summary

**Moved the draft migration record under `.planning/` (D-33), preserved the full CI/CD adoption record internally while condensing `RULESETS.md`/`RELEASE.md` to maintainer scope (D-34), and closed WR-10, IN-05, and the README/index half of IN-10 — each with re-run, passing verification.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-09-29T10:35:00Z
- **Completed:** 2026-09-29T11:30:00Z
- **Tasks:** 3
- **Files modified:** 7 (1 created, 5 modified, 1 renamed)

## Accomplishments

- **D-33 (migration record relocation):** `MIGRATION-v0.11.md` is now `.planning/MIGRATION-v0.11.md`, a tracked git rename. Its inline verifier's own extraction command was repointed to the new path and to write its scratch script under the gitignored `_scrap/` directory instead of a bare `/tmp` path; re-run, it still prints `[ok] verified 25 entries`. `06-VALIDATION.md`'s migration-record bullet was repointed to match. The diff against the pre-move file touches only those extraction-command lines and one added location sentence — no `BC-P2I-*` table row changed.
- **D-34/D-15 (adoption record preservation):** `.planning/CICD-ADOPTION-RECORD.md` is a full copy of the pre-condensation `RULESETS.md` (all 12 apply-time checklist items and the recorded 2026-09-28 pre-promotion gate output — `278 passed`, `62.27%` coverage — intact verbatim), corrected in place for WR-10 and IN-05, with the migration-verifier line in its pre-promotion-gate section repointed to Task 1's new command. Four sections were appended: the full release-process record (the paragraphs the condensed `RELEASE.md` drops), a review-round changes log naming every fix-now finding and the gap plan that closed it, cross-repository notes on the floating-tag and placeholder-DOI issues shared with PCHandler/GSEGUtils, and a placeholder for plan 06-17's gate re-run.
- **WR-10 closed:** `RULESETS.md`'s "Promotion and back-merge" section now requires a true-merge back-merge after **every** promotion to `main` and after **every** release-PR merge (never squash/rebase), states the measured merge-base rationale (`f946268` common ancestor; `69224a9`/`ade40f8` main-only commits), and names the first back-merge as the ancestry graft.
- **IN-05 closed:** the same doc's "Applying the rulesets" section is now procedural — it describes how a ruleset gets created (a single direct post of the preflight-produced payload, then the dispatch-only workflow) rather than asserting one already exists.
- **IN-10 (README/index half) closed:** `README.rst` now names all three projections (spherical, orthographic, perspective), matching `docs/source/index.rst` and the `PROJECTIONS` registry. `twine check` still passes on both the sdist and wheel long descriptions.
- **Condensation:** `RULESETS.md` shrank from 478 to 142 lines; `RELEASE.md` from 142 to 100 lines — both within their planned bounds (120-160 and 85-110), both free of agent-workflow/planning vocabulary (confirmed by the hygiene gate and a corrected word-check), both retaining every heading and claim-table row later plans (06-10, 06-12, 06-13) read back verbatim.

## Task Commits

1. **Task 1 (tracer): Move the migration record under `.planning/` (D-33)** — `90ae66d` docs(migration): move the draft migration record under the internal planning directory
2. **Task 2: Preserve the full adoption record (D-34, D-15)** — `b6b5223` docs(ci): preserve the full CI/CD adoption record internally
3. **Task 3: Condense `RULESETS.md`/`RELEASE.md`; fix README (WR-10, IN-05, D-33a, IN-10)** — `d179850` docs(rulesets): condense the branch-protection and release docs to maintainer scope; require a back-merge after every promotion, and `4fc329b` docs(readme): name the perspective projection

**Plan metadata:** (this commit)

## Files Created/Modified

- `.planning/MIGRATION-v0.11.md` — renamed from the repository root; extraction command repointed to the new path and to `_scrap/`; one location sentence added
- `.planning/CICD-ADOPTION-RECORD.md` — new: full pre-condensation `RULESETS.md` content, corrected (WR-10, IN-05, D-33) plus four appended sections
- `.planning/phases/06-publication-hardening-downstream-migration-record/06-VALIDATION.md` — migration-record extraction bullet repointed to `.planning/MIGRATION-v0.11.md`
- `RULESETS.md` — condensed to 142 lines; WR-10 and IN-05 closed
- `RELEASE.md` — condensed to 100 lines; both claim tables and required headings intact
- `README.rst` — names the perspective projection
- `.github/scripts/test_publish_ref_guard.py` — incidental ruff-format reformat (Rule 3 deviation, see below)

## Decisions Made

See `key-decisions` in the frontmatter. In short: D-33/D-34 executed exactly as the owner decided in the mid-phase review round; WR-10's back-merge rule and rationale corrected; IN-05's ruleset-creation wording made procedural; IN-10's README/index half closed; one Rule 3 scope-widening (an incidental ruff-format fix) and one verification-script false-positive documented rather than silently patched around.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Whole-tree `pre-commit run --all-files` reformatted an unrelated pre-existing file**
- **Found during:** Task 3, running the plan's own required whole-tree pre-commit verify command
- **Issue:** `ruff-format` reformatted `.github/scripts/test_publish_ref_guard.py` (a file this plan's `<files>` list does not include, created in plan 06-14) — a line-join-only change with no semantic effect. This is very likely the ruff-version drift IN-06/IN-07 already records (deferred to Phase 7): the pre-commit hook's pinned `ruff-pre-commit` revision formats slightly differently than the locked `ruff` version the test suite runs.
- **Fix:** Accepted the mechanical reformat rather than reverting it — reverting would leave the plan's own required `pre-commit run --all-files` verify command red, and the change is purely cosmetic (verified with `git diff`: parenthesized multi-line calls joined to one line, nothing else). Did not attempt to fix the underlying IN-07 version-drift itself — that stays deferred to Phase 7 as recorded.
- **Files modified:** `.github/scripts/test_publish_ref_guard.py`
- **Verification:** re-ran `uv run --frozen pytest -q` afterward — 282 passed, unchanged from before the reformat
- **Committed in:** `d179850` (Task 3 commit)

### Noted, not auto-fixed

**1. [Verification-script false positive, not a doc defect] The plan's own word-check flags the literal, required branch name `develop-gsd`**
- **Found during:** Task 3, running the plan's literal word-check `<verify>` command
- **Issue:** The check's regex (`(?i)(?<![a-z])` + word, for `word='gsd'`) matches "gsd" whenever the preceding character is not a letter — which includes the hyphen in the real, required branch name `develop-gsd`. `RULESETS.md` must name that branch (header block, required-checks table, "Other rules" table) per this task's own action text, so the literal check as written cannot pass on any correct condensed file.
- **Handling:** Confirmed the false positive is isolated to `develop-gsd` by grepping every `gsd` occurrence in the file (all 21 hits are `-gsd`, none a bare "GSD"/workflow-vocabulary reference) and by running a corrected version of the same check with `develop-gsd` substituted out before scanning — that version reports `wording-ok` for all four files. No stray agent-workflow vocabulary survives; the literal command's one non-zero result is the branch name, not a defect.
- **Not filed to WINDOWS.md:** this is a one-off `<verify>` command's own regex, not a stub/skipped-test/deviation in this plan's deliverables, and the underlying requirement (no agent-workflow vocabulary in the shipped docs) is independently verified and met.
- **Files:** none (verification-only)

---

**Total deviations:** 1 auto-fixed (Rule 3, cosmetic reformat), 1 noted verification-script false positive (no code/doc change).
**Impact on plan:** None on the delivered fixes — WR-10, IN-05, D-33, D-34, and the IN-10 README/index half are all closed and independently re-verified with the plan's own commands (corrected where one command had a false positive).

## Issues Encountered

None beyond the two notes above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `06-UAT.md`'s WR-10, IN-05, and the README/index half of IN-10 each have a proving command re-run and commit evidence, ready to be flipped to `resolved` in plan 06-18 once this gap diff has had its own review (global review-discipline rule: gap-closure fixes get their own review before the phase re-verifies).
- `.planning/CICD-ADOPTION-RECORD.md`'s "## Review-round changes" section names 06-16 as the plan that still owes WR-03, WR-04, IN-04, and IN-13; those remain open in `06-UAT.md` and are not this plan's scope.
- `CICD-02` and `BC-01` both stay unmarked in `REQUIREMENTS.md` until every declaring plan's `SUMMARY.md` exists (shared-ID gate, #2388) — 06-16, 06-17, and 06-18 have not yet run.
- No push, pull request, workflow dispatch, or index upload happened in this plan — every commit stays on the phase branch, as the plan's prohibitions require.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-29*

## Self-Check: PASSED

- `.planning/MIGRATION-v0.11.md` — FOUND (git-tracked, rename-detected)
- `.planning/CICD-ADOPTION-RECORD.md` — FOUND
- `RULESETS.md` (142 lines), `RELEASE.md` (100 lines) — FOUND, within bounds
- Commits `90ae66d`, `b6b5223`, `d179850`, `4fc329b` — all FOUND in `git log --oneline --all`
- All plan-level `<verification>` items re-run clean: migration verifier `[ok] verified 25 entries`; `git grep -l 'MIGRATION-v0.11' -- ':!.planning'` empty; `uv run --frozen pytest -q` → 282 passed; `uv run --frozen pre-commit run --all-files` → all hooks Passed
