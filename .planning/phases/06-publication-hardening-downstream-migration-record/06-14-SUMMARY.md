---
phase: 06-publication-hardening-downstream-migration-record
plan: 14
subsystem: infra
tags: [setuptools-scm, git-archive, github-actions, publish-workflow, citation, ref-guard]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "publish-testpypi.yml / publish-pypi.yml (06-06), release-please.yml floating-tag step and .git_archival.txt (06-08), mid-phase code review (06-09 precondition) surfacing CR-01/WR-05/WR-08"
provides:
  - "Narrowed .git_archival.txt describe glob (single v[0-9]*.[0-9]*.[0-9]* match), matching pyproject's checkout-time glob, plus tests/test_git_archival.py pinning the regression"
  - "First-step ref guards on both publish workflows (release-branch-only dispatch for TestPyPI; X.Y.Z-tag-reachable-from-main for PyPI) plus .github/scripts/test_publish_ref_guard.py executing the extracted guard scripts"
  - "CITATION.cff with the placeholder-DOI preferred-citation block removed and a factual message"
affects: ["06-15 (adoption record cross-repository notes)", "06-17/06-18 (this gap diff's own review and re-merge)", "Phase 7 (GSEGUtils/PCHandler floating-tag + placeholder-DOI cross-repository follow-up; environment deployment policies; MANIFEST.in)"]

actuals:
  tokens: 5650
  tasks: 3
  commits: 5
plan_head_before: 1c01674c830081932e94cdc4a6ed914dc8647ce4
plan_head_after: fd1c2d93c421133960d46bf9a79eb79e82ae4986

tech-stack:
  added: []
  patterns:
    - "Guard-script extraction test pattern: yaml.safe_load a real workflow file, pull one step's run: script by name, execute it under bash with only the env vars CI would set — proves the shipped script, not a paraphrase of it"
    - "Reproduce-then-pin: every fix here was reproduced with a real git archive / real setuptools_scm invocation / a real subprocess-executed guard script before the corresponding test was written"

key-files:
  created:
    - tests/test_git_archival.py
    - .github/scripts/test_publish_ref_guard.py
  modified:
    - .git_archival.txt
    - .github/workflows/publish-testpypi.yml
    - .github/workflows/publish-pypi.yml
    - CITATION.cff

key-decisions:
  - "CR-01 fixed by narrowing .git_archival.txt's match= glob to the same v[0-9]*.[0-9]*.[0-9]* string pyproject.toml's git_describe_command already uses, rather than deleting release-please.yml's floating-tag step (owner disposition: minimal fix, floating tags stay as shipped)"
  - "WR-05 fixed with plain-bash first-build-step guards mirroring ruleset-apply.yml's existing shape, rather than relying solely on GitHub environment deployment-branch policies (those are recorded as follow-ups, not a substitute)"
  - "WR-08 fixed by deleting preferred-citation entirely rather than inventing a placeholder-free DOI; message rewritten to state only facts that are true today"

requirements-completed: []  # CICD-02 shared across most phase-06 plans (06-01..06-18); withheld until every declaring plan's SUMMARY exists (shared-ID gate, #2388) — see Next Phase Readiness

coverage:
  - id: D1
    description: "CR-01 closed: release archive of a commit carrying floating vX/vX.Y tags now substitutes the X.Y.Z release tag, which the repository's own tag_regex parses; pinned by a test that builds a real archive and was observed failing first"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "tests/test_git_archival.py#test_archive_of_floating_tagged_commit_substitutes_release_tag"
        status: pass
      - kind: unit
        ref: "tests/test_git_archival.py#test_release_tag_regex_parses_release_tag_only"
        status: pass
      - kind: unit
        ref: "tests/test_git_archival.py#test_archival_glob_matches_checkout_glob"
        status: pass
      - kind: other
        ref: "manual: uv run --no-project --with setuptools-scm python -m setuptools_scm against a real extracted archive, before and after the fix"
        status: pass
    human_judgment: false
  - id: D2
    description: "WR-05 closed: a TestPyPI dispatch from any ref but main, and a PyPI release from any ref that is not an X.Y.Z tag reachable from main, are refused in the first build-job step(s) before anything is built"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: ".github/scripts/test_publish_ref_guard.py (9 cases: 3 TestPyPI dispatch-ref, 4 PyPI tag, 2 PyPI ancestry)"
        status: pass
      - kind: unit
        ref: ".github/scripts/test_check_publish_gate.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "WR-08 closed: CITATION.cff ships no placeholder DOI and no preferred-citation block; top-level metadata unchanged"
    requirement: "CICD-02"
    verification:
      - kind: unit
        ref: "hermetic python -c assertion (cff-ok) in the plan's Task 3 <verify>"
        status: pass
      - kind: other
        ref: "uvx cffconvert --validate -i CITATION.cff"
        status: pass
    human_judgment: false

duration: 45min
completed: 2026-09-29
status: complete
---

# Phase 6 Plan 14: Release-Archive, Publish-Ref-Guard, and Citation Gap Closure Summary

**Narrowed the release-archive describe glob to X.Y.Z tags, added first-step ref guards to both publish workflows, and removed CITATION.cff's placeholder DOI — each fix reproduced with real git/setuptools_scm/subprocess runs and pinned by a test that failed first.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-09-29T09:44:00Z
- **Completed:** 2026-09-29T10:29:00Z
- **Tasks:** 3
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments

- CR-01: `.git_archival.txt` now carries exactly one describe-match glob, `v[0-9]*.[0-9]*.[0-9]*`, identical to `pyproject.toml`'s `git_describe_command`. A release commit that also carries the `v0`/`v0.11` rolling tags now archives with `v0.11.0` substituted, which `setuptools_scm`'s `tag_regex` parses to `0.11.0`.
- WR-05: `publish-testpypi.yml`'s build job now opens with a guard refusing any dispatch ref but `refs/heads/main`. `publish-pypi.yml`'s build job opens with a guard refusing any release ref that is not an `X.Y.Z` tag, followed (immediately after checkout) by a guard refusing a tagged commit not reachable from `origin/main`.
- WR-08: `CITATION.cff`'s `preferred-citation` block (carrying `doi: 10.5281/zenodo.XXXXXXX`) is gone; `message` now states only facts that are true today.

## Task Commits

Each task followed RED → GREEN (Task 1 and Task 2 are `tdd="true"`):

1. **Task 1 (tracer): release-archive version derivation (CR-01)**
   - `8651037` test(release): pin release-archive version derivation against floating tags — RED
   - `e44ac0b` fix(release): narrow the archival describe glob to X.Y.Z tags so release archives build — GREEN
2. **Task 2: publish workflow ref guards (WR-05)**
   - `f51d584` test(release): add failing test for publish workflow ref guards — RED
   - `b6d9d9f` feat(release): ref-guard both publish workflows against a mis-dispatch or a non-release tag — GREEN
3. **Task 3: CITATION.cff placeholder DOI (WR-08)**
   - `fd1c2d9` docs(citation): drop the placeholder DOI until a release is archived

No `refactor(...)` commits were needed — neither GREEN implementation required cleanup.

## Files Created/Modified

- `tests/test_git_archival.py` — builds a real scratch git repository carrying the release tag plus both rolling tags in release-automation order, runs a real `git archive`, and asserts the substituted tag both matches expectation and satisfies the project's `tag_regex`; also asserts the archival and checkout globs are the same literal string
- `.git_archival.txt` — describe format narrowed to the single glob `v[0-9]*.[0-9]*.[0-9]*`
- `.github/scripts/test_publish_ref_guard.py` — extracts each guard's `run:` script from the real workflow YAML and executes it under `bash` with only the environment variables CI would set; 9 accept/reject cases across both workflows' guards
- `.github/workflows/publish-testpypi.yml` — new first build step refusing a dispatch from any ref but `refs/heads/main`
- `.github/workflows/publish-pypi.yml` — new first build step refusing a release ref that is not an `X.Y.Z` tag; new step immediately after checkout refusing a tagged commit not reachable from `origin/main`
- `CITATION.cff` — `preferred-citation` block removed; `message` rewritten to state only current facts

## Decisions Made

- CR-01: chose the narrow-glob fix over deleting `release-please.yml`'s "Tag major and minor versions" step — that step is kit-shipped and shared with PCHandler/GSEGUtils, and the plan's prohibitions forbid editing it without owner approval. The narrow glob is a pc2img-local, fully sufficient fix.
- WR-05: guard shape mirrors `ruleset-apply.yml`'s existing first-step pattern exactly (`env:` reads only, `set -uo pipefail`, `::error::` + `exit 1` on refusal) rather than inventing a new idiom.
- WR-08: no DOI was invented and no archive service was named — the message states only that a persistent identifier will be added "when a release is archived," which is true regardless of which archive is eventually used.

## Deviations from Plan

### Auto-fixed Issues

None — both fixes matched the plan's prescribed action text exactly (glob string, guard shapes, CITATION.cff rewrite).

### Noted, not auto-fixed

**1. [Tooling limitation, not a code defect] `gsd_run check tdd-red-evidence` misclassifies pytest/JUnit-XML RED evidence as `INVALID_RED`**
- **Found during:** Task 1, persisting the RED-phase evidence record per `tdd.md`'s gate-enforcement step
- **Issue:** The checker's Surefire/JUnit-XML parser extracts `name=` and `classname=` with an unanchored `/name="([^"]*)"/` regex. Because the literal string `classname="..."` itself contains the substring `name="..."` starting at its 6th character, the regex matches inside `classname=` before it ever reaches the real `name=` attribute, so both fields resolve to the classname value. `pytest --junitxml` (the only JUnit-XML pytest can emit without adding a new dependency) always emits `classname` before `name` on `<testcase>`, so this misfires on every pytest-generated record, independent of which test is actually failing.
- **Handling:** Verified RED manually instead — ran `uv run --frozen pytest tests/test_git_archival.py -q` before the fix and confirmed the target test failed with the exact planned assertion (`describe_name == 'v0'`, not an import/fixture/syntax error), matching `tdd.md`'s "intentional failure" bar. `workflow.tdd_mode` is `false` in this project's config and this plan's frontmatter `type` is `execute` (the gate-enforcement section in `tdd.md` scopes the mandatory machine gate to `type: tdd` plans under `tdd_mode: true`), so the machine-verified gate is not the enforced contract here.
- **Not filed to WINDOWS.md:** this is a limitation in the shared `gsd-core` tool, not a stub/skipped-test/unrun-verify/deviation in this plan's own deliverables — every `<verify>` command the plan specified was run to completion.
- **Files:** none in this repository (informational only)

**2. [Verification-environment quirk, not a code defect] One literal plan `<verify>` grep command needs a fixed-string flag on this box's GNU grep**
- **Found during:** Task 1, running `grep -c 'describe-name:$Format:%(describe:tags=true,match=v\[0-9\]\*\.\[0-9\]\*\.\[0-9\]\*)$' .git_archival.txt`
- **Issue:** GNU grep 3.7's BRE treats an unescaped `$` as an end-of-line anchor whenever it is the last character of the pattern — which it is here, since the file's line genuinely ends with a literal `$` character (part of git's `$Format:...$` export-subst syntax). The anchor interpretation requires the *previous* character to be immediately followed by end-of-line, but the actual line has one more literal `$` after that — so the anchor reading can never match, regardless of the file's content. Reproduced identically on both the harness's `ugrep`-backed `grep` shell function and real `/usr/bin/grep` (GNU grep 3.7).
- **Handling:** Confirmed the identical intent with `grep -cF` (fixed-string mode) → `1`, and independently with `grep -o 'match=' .git_archival.txt | wc -l` → `1` plus `git check-attr export-subst` → `set` (the plan's own third verify command, which passed as literally written). All three confirm exactly one match glob with the correct value. Not a defect in `.git_archival.txt`; the literal command's trailing unescaped `$` cannot match a literal trailing `$` in BRE mode on this grep version.
- **Files:** none (verification-only; no plan file was edited)

---

**Total deviations:** 0 auto-fixed. Two tooling/verification notes recorded above, neither changing scope or requiring a code change.
**Impact on plan:** None on the delivered fixes — all three findings are closed and independently reproduced with real tooling (git archive, setuptools_scm, subprocess-executed guard scripts, cffconvert).

## Issues Encountered

None beyond the two tooling notes above.

## Cross-Repository Notes (recorded, not acted on)

- **CR-01 (floating tags):** `release-please.yml`'s "Tag major and minor versions" step is kit-shipped and shared. PCHandler and GSEGUtils very likely carry the same step and therefore the same archive-unbuildable defect once they cut a release with more than one tag on the commit. Origin's existing `v0.10.4` release already has `v0`/`v0.10` on its commit and its archive stays unbuildable — a pushed tag's archive cannot be corrected retroactively. Editing PCHandler/GSEGUtils or the shared kit needs owner approval; this is a note for the plan-06-15 adoption record, not an action taken here.
- **WR-08 (placeholder DOI):** `/scratch/41_pchandler/CITATION.cff` and `/scratch/30_GSEGUtils/CITATION.cff` both carry the identical `doi: 10.5281/zenodo.XXXXXXX` placeholder and `preferred-citation` block this plan removed from pc2img's copy. Neither sibling file was edited (owner approval required for changes to those repositories); this is a note only.

## Follow-ups Recorded (not done here, per plan scope)

- **WR-05 follow-up 1 — GitHub environment deployment policies:** the `testpypi` environment (bound to `main` only) and the `pypi` environment (bound to `v*` tags only) should get deployment branch/tag protection rules once the environments exist. `testpypi`'s environment-creation step lands in plan 06-12; `pypi`'s lands in Phase 7. Recorded so it is not lost, not implemented here — the ref guards added in this plan are the enforced control in the meantime.
- **WR-05 follow-up 2 — `MANIFEST.in` as defence in depth:** a `MANIFEST.in` with `prune .planning` / `prune .claude` was suggested by the reviewer as a second layer beneath the ref guards. Deferred with the other WR-09 packaging items (Phase 7).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `06-UAT.md`'s gaps CR-01, WR-05 and WR-08 now each have a proving test/assertion and commit evidence, ready to be flipped to `resolved` in plan 06-18 once this gap diff has had its own review (global review-discipline rule: gap-closure fixes get their own review before the phase re-verifies — plan 06-17).
- `CICD-02` is declared by nearly every plan in this phase (06-01 through 06-18); it stays unmarked in `REQUIREMENTS.md` until every declaring plan's `SUMMARY.md` exists (shared-ID gate, #2388) — several sibling gap-closure plans (06-15..06-18) have not yet run.
- No push, pull request, workflow dispatch or index upload happened in this plan — every commit stays on the phase branch, as the plan's prohibitions require.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-29*

## Self-Check: PASSED

- `tests/test_git_archival.py` — FOUND
- `.github/scripts/test_publish_ref_guard.py` — FOUND
- `.git_archival.txt` — FOUND
- Commits `8651037`, `e44ac0b`, `f51d584`, `b6d9d9f`, `fd1c2d9` — all FOUND in `git log --oneline --all`
- All plan-level `<verification>` commands re-run clean: `uv run --frozen pytest tests/test_git_archival.py .github/scripts -q` → 95 passed
