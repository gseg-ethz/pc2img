---
phase: 06-publication-hardening-downstream-migration-record
reviewed: 2026-09-29T11:01:17Z
depth: deep
files_reviewed: 21
files_reviewed_list:
  - .git_archival.txt
  - .github/actions/classify-changes/action.yml
  - .github/scripts/check_publish_gate.py
  - .github/scripts/check_ruleset_drift.py
  - .github/scripts/ruleset_lib.py
  - .github/scripts/test_publish_ref_guard.py
  - .github/workflows/ci.yml
  - .github/workflows/publish-pypi.yml
  - .github/workflows/publish-testpypi.yml
  - .github/workflows/ruleset-apply.yml
  - .github/workflows/scheduled-health.yml
  - .pre-commit-config.yaml
  - CITATION.cff
  - CONTRIBUTING.md
  - README.rst
  - RELEASE.md
  - RULESETS.md
  - src/pc2img/strategies/projection.py
  - tests/test_git_archival.py
  - tests/test_hygiene.py
  - tests/test_projection.py
findings:
  critical: 0
  warning: 5
  info: 6
  total: 11
status: issues_found
---

# Phase 6: Code Review Report (round 2: gap-closure fixes 06-14..06-17)

**Reviewed:** 2026-09-29T11:01:17Z
**Depth:** deep
**Files Reviewed:** 21
**Status:** issues_found

## Summary

Scope: the 21 shipped files changed by the round-1 gap-closure plans (`2ec34fc..HEAD`),
reviewed as whole files. The round-1 findings the owner deferred to Phase 7 (WR-01/02/06/07/09,
IN-01/02/03/06/07/08/09/11/12) are not raised again here. Each fix-now closure was checked by
running code.

**Verified sound (reproduced, not read):**
- **CR-01 is fixed end to end.** I cloned the repo, put `v0.11.0`, `v0.11` and `v0` on HEAD,
  ran `git archive`, and ran `setuptools_scm` over the extracted tree. It gives `0.11.0`. One
  commit later it gives `describe-name: v0.11.0-1-g…`, which resolves to `0.11.0.post1`. The
  archival glob is byte-identical to `git_describe_command`'s glob. No `release-*` tags exist,
  so dropping that match loses nothing.
- **WR-03 is fixed.** `SphericalProjection` (with and without a FoV) and `OrthographicProjection`
  (with and without an ROI) return what the new `project_raw` docstring says: `(M, 2)` coords,
  a bool mask of length N, and a FoV/ROI frame otherwise the kept extent. `pcd.fov` is
  `FoV.from_angles` over the data, so "kept-point extent" holds for spherical too. The module
  AST, with docstrings stripped, is identical to the base.
- **WR-04 is fixed.** The compiled pre-commit `exclude` regex makes identical decisions under
  the `\.plan[n]ing` and literal spellings, across 10 probe paths including near-misses.
- **The other changes are inert.** The comment-only edits to `ci.yml`, `ruleset-apply.yml`,
  `scheduled-health.yml` and `classify-changes/action.yml` leave each YAML object identical to
  the base, and the three kit `.py` files are AST-identical with docstrings stripped.
- **Tooling is green, but that only shows the existing checks pass:**
  - `actionlint` 1.7.12 with shellcheck is clean on all workflows.
  - `check_publish_gate.py` passes.
  - `cffconvert --validate` passes.
  - `readme_renderer` renders `README.rst`.
  - ruff check and format are clean.
  - The suite gives 286 passed at 62% branch coverage, which matches `CONTRIBUTING.md`.
- **WR-10's rationale is now correct.** The merge base is `f946268`, and `main` carries only
  `69224a9` and `ade40f8`. No commit reachable from `origin/main` has ever carried the internal
  directories, so the ancestry guard's premise holds today.

**Key concerns:**
1. **The WR-05 ref guards only protect commits that contain them.** `origin/develop-gsd`, the
   pushed phase branch and 18 historical commits still carry unguarded publish workflows. No
   ref-independent control, such as environment deployment policies, was added. RELEASE.md and
   the workflow headers overstate the guarantee.
2. **Two parallel gap plans undid each other's work (IN-04).** Plan 06-15 condensed
   `RULESETS.md` and removed the declined-components record. Seventeen minutes later, plan 06-16
   added seven "see RULESETS.md" pointers to that record.
3. **A gap-closure fix put a review-finding ID (`WR-03`) into a shipped test file.** The
   hygiene gate, which was extended in the same round, cannot see the `CR-`/`WR-`/`IN-`
   family at all.
4. **One new gate-bypass finding in a file in scope.** The release-artifact fast path ignores
   `previous_filename`, so a rename *into* an allowlisted name hides a deletion. This is the
   same class as the deferred WR-01.
5. **The RULESETS.md verification recipe can never succeed as written.** The list endpoint
   never returns `bypass_actors`.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Publish ref guards live inside the workflow they guard, so every existing unguarded copy stays exploitable, and nothing ref-independent was added

**File:** `.github/workflows/publish-pypi.yml:21-25, 37-66`, `.github/workflows/publish-testpypi.yml:14-16, 28-39`, `RELEASE.md:66-72`
**Issue:** GitHub runs a `release` workflow from the file at the tagged commit (`GITHUB_SHA`),
and a `workflow_dispatch` workflow from the file on the dispatched ref. Both new guards are
steps inside those files, so they protect only commits that already contain them. Measured:
- `git show origin/develop-gsd:.github/workflows/publish-testpypi.yml | grep -c "Refuse a dispatch"`
  gives `0`, and the same is true of `publish-pypi.yml`.
- The pushed `origin/gsd/phase-06-…` branch is also unguarded.
- 18 commits between `e13ca59` (the workflows added) and `b6d9d9f` (the guards added) carry
  `publish-pypi.yml` with no guard.

Two consequences follow:
- **PyPI.** A GitHub release whose tag points at any of those commits runs the old workflow,
  builds an sdist containing `.planning/` and `.claude/` (confirmed in round 1), and uploads it
  permanently. The trigger can be a hand-made release with the wrong target, or a mis-pointed
  tag. The PyPI trusted publisher matches repository + workflow filename + environment, not a
  ref.
- **TestPyPI.** Once `main` carries the workflow (so dispatch is enabled), `gh workflow run
  publish-testpypi.yml --ref <stale-branch>` runs that branch's unguarded copy.

Tag protection is explicitly deferred (`RULESETS.md:147`), so nothing restricts who creates
`v*` tags or where. Round 1's fix recommendation #2 (environment deployment policies) and #3
(sdist content pruning) were neither implemented nor recorded as declined. The prose also
claims more than the mechanism gives:
- "a rehearsal can never build an sdist from a ref that still carries the internal planning
  directories" (`publish-testpypi.yml:14-16`).
- "Both fail before anything is built, since any other ref could still carry internal-only
  content" (`RELEASE.md:71-72`).

**Fix:** Add controls that do not depend on which copy of the file runs, and scope the prose to
what the in-file guards actually cover:
1. In repository settings, restrict the `testpypi` environment's deployment branches to
   `main`, and restrict `pypi` to tags matching `v[0-9]*.[0-9]*.[0-9]*` **plus** a required
   reviewer (self-review is permitted for environments, so a solo owner is fine). A tag-name
   policy alone would not stop a correctly-named tag on a `develop-gsd` commit. Record both in
   `RELEASE.md` under "Ref guards".
2. Assert on the sdist's content, which is the property that actually matters, before upload
   in both build jobs:
```yaml
      - name: Refuse an sdist carrying internal-only directories
        run: |
          if tar -tzf dist/*.tar.gz | grep -Eq '^[^/]+/\.(planning|claude)/'; then
            echo "::error::sdist contains internal-only directories"; exit 1
          fi
```
3. Reword `publish-testpypi.yml:14-16` and `RELEASE.md:71-72` to "refuses … on any commit
   that carries this guard". Delete or rebase the stale remote phase branch after merge.

### WR-02: Every "see RULESETS.md" pointer added for the declined components dangles; the condensation removed what they point to

**File:** `.github/actions/classify-changes/action.yml:23-24`, `.github/scripts/check_publish_gate.py:128-129`, `.github/scripts/check_ruleset_drift.py:22-23`, `.github/scripts/ruleset_lib.py:11-12`, `.github/workflows/ci.yml:23-24, 190`, `.github/workflows/ruleset-apply.yml:22-23, 237-243`, `.github/workflows/scheduled-health.yml:17-18`, `RULESETS.md` (whole file)
**Issue:** Commit `d9e86d3` (IN-04, 10:31) added "(not part of this assembly: the config
self-inspection and continuous-enforcement components were declined; see RULESETS.md)" in
seven files. Commit `d179850` (plan 06-15, 10:14) had already condensed `RULESETS.md` and moved
the "Components: taken and declined" section and the "Apply-time checklist" into
`.planning/CICD-ADOPTION-RECORD.md`, which is stripped from `main`.

`grep -niE "declin|self-inspection|continuous|check_ci_config|integrity|assert_no_skip|ruleset-drift" RULESETS.md`
returns nothing. On the public branch, every pointer therefore leads to a document that
never mentions the components.

The same applies to other references:
- `ci.yml:22, 30, 43-44` still cite "an apply-time checklist item in the strategy document".
- The Lint job's runtime log line (`ci.yml:190`) tells readers "the apply-time checklist in
  the strategy document governs this repository". Neither document ships.
- `ruleset-apply.yml:241-243` still describes "The nightly drift job", which does not exist.

The IN-04 closure, "a one-line note … see RULESETS.md", is therefore not true on the tree that
gets promoted.
**Fix:** Add a short "Declined components" section to `RULESETS.md` (3–4 lines naming
`check_ci_config.py` / `assert_no_skip.py` / `integrity.yml` / `ruleset-drift.yml` and the
one-sentence cost of declining). Otherwise, point the notes at a shipped location. Reword
`ci.yml:190` and the "strategy document" / "apply-time checklist" comments to reference a
shipped document, or drop them. Delete the "nightly drift job" sentence in `ruleset-apply.yml`.

### WR-03: A gap-closure fix shipped a review-finding ID, and the extended hygiene gate cannot see that ID family

**File:** `tests/test_projection.py:309`, `tests/test_hygiene.py:167-180`
**Issue:** Commit `158a569` (the WR-03 fix) added the section header `# WR-03: project_raw
contract pinning …` to a shipped test file. The gate's `_CODE_PATTERN` covers
`BUG|DSN|QUAL|TEST|DEP|CICD|BC|PERF|BRANCH-N`, `M-/D-NN`, `T-NN-NN`, `SCn` and review-ledger ids.
It has no alternative for code-review finding IDs.

Reproduced with the gate's own matcher:
- `_matches('# WR-03: project_raw contract pinning')` gives `[]`.
- `_matches('CR-01')` gives `[]`.
- `_matches('IN-13')` gives `[]`.

This is exactly the vocabulary that review → gap-closure rounds generate. Round 2 of this
same workflow extended the gate (IN-13) and still missed it. The gate is green on a tree that
carries the leak.
**Fix:** Delete the ID from `tests/test_projection.py:309`, for example "project_raw contract
pinning -- kept-point (M, 2) shape …". Add a review-finding family to `_CODE_PATTERN`, spelled
so the gate's own source does not self-match. Extend the positive self-check with
`"WR" + "-03"`, `"CR" + "-01"` and `"IN" + "-13"`:
```python
r"\b(?:CR|WR|IN|BL)-[0-9]{2}\b",  # code-review finding ids
```

### WR-04: Release-artifact fast path ignores `previous_filename`, so a rename into an allowlisted name hides the deletion of its source

**File:** `.github/actions/classify-changes/action.yml:123-125, 195-211`
**Issue:** The pull-request files API reports a rename as one entry whose `filename` is the
**new** path, with the old path only in `previous_filename`. I confirmed this against a live
PR: `pypa/pip#14322` returns `{"filename":"SECURITY.md …","previous_filename":"SECURITY.md","status":"renamed"}`.
The step extracts only `.[].filename`.

A PR whose only entry is a rename of, say, `src/pc2img/core.py` → `CHANGELOG.md` therefore
yields `release-artifacts-only=true`. That greens all three required contexts having executed
nothing, while deleting source code. `required_approving_review_count` is 0.

The rename target must not exist at the base, so the path takes two PRs. The first deletes
`CHANGELOG.md`, and that PR itself fast-paths, because a removal is listed under `filename`
too. This is the same required-gate-bypass class the in-file comment calls "A REAL
REQUIRED-GATE BYPASS". It is not introduced by this round and was not raised in round 1.
**Fix:** Emit both names per entry, and treat any rename, copy or removal as not
release-artifact-only:
```bash
--jq '.[] | if (.status == "renamed" or .status == "copied" or .status == "removed")
             then "\u0000NONARTIFACT" else .filename end'
```
Or at minimum use `.[] | .filename, (.previous_filename // empty)`. Add a renamed-entry case to
`test_classify_changes.py`. This fits naturally with the deferred WR-01 (newline) fix in
Phase 7.

### WR-05: RULESETS.md verification recipe expects a field the list endpoint never returns

**File:** `RULESETS.md:112-120`
**Issue:** The recipe says to run `gh api repos/gseg-ethz/pc2img/rulesets` and expect both
objects "with an empty `"bypass_actors"` array present (not absent — an absent key tells you
nothing …)". The list endpoint returns summary objects only:
`id, name, target, source_type, source, enforcement, node_id, _links, created_at, updated_at`.

I confirmed this live on `python/cpython`, `pypa/pip`, `astral-sh/uv`, `cli/cli` and
`actions/checkout`: none carries `bypass_actors`. So, by the document's own rule, the check it
prescribes can never succeed. A maintainer following it either concludes the protection is
broken or learns to ignore the check.

`ruleset-apply.yml:241-243` notes that even a per-id read needs an admin-capable token to see
`bypass_actors`. This text was carried through the 06-15 rewrite.
**Fix:**
```bash
for id in $(gh api repos/gseg-ethz/pc2img/rulesets --jq '.[].id'); do
  gh api "repos/gseg-ethz/pc2img/rulesets/${id}?includes_parents=false" \
    --jq '{name, enforcement, bypass_actors}'
done
```
State that this requires a token with repository administration access. Quote the `?` URL
(the owner's shell is zsh, where an unquoted `?` is a glob and the drift command at
`RULESETS.md:125-127` fails with "no matches found").

## Info

### IN-01: The planning-vocabulary gate still passes two shipped hits and any wrapped phrase

**File:** `tests/test_hygiene.py:188-195, 226-233` (hits at `pyproject.toml:196`, `tests/test_image_store.py:272`)
**Issue:** The IN-13 extension matches exactly the four phrases round 1 listed, on one line,
with a single space. The following still pass, reproduced with `_matches`:
- `# CI command line only (Plan 03)` in `pyproject.toml:196`.
- `b"pc2img round-3 containment sentinel …"` in `tests/test_image_store.py:272`.
- `"this\nphase"` (a line-wrapped comment), `"this  phase"`, "review round 2" and
  "milestone v1.0".
**Fix:** Reword the two shipped hits. Optionally, add `\bplan\s+[0-9]{1,2}\b` and
`\b(?:review[- ])?round[- ][0-9]\b`. Run the prose alternatives over the whole text with `\s+`
as well as per line (character classes keep the source from self-matching).

### IN-02: The base `project()` docstring contradicts the corrected `project_raw` contract

**File:** `src/pc2img/strategies/projection.py:106-114`
**Issue:** It still says "Normalize raw coords into [0,1]×[0,1] based on data extents". The
`project_raw` docstring just above now correctly says the frame is the FoV/ROI bounds when one
is configured.
**Fix:** "…relative to the normalization frame (`mins`, `maxs`) returned by
:meth:`project_raw`".

### IN-03: The ref-guard tests do not pin "before anything is built", and the git fixtures inherit ambient `GIT_*` state

**File:** `.github/scripts/test_publish_ref_guard.py:117-137, 184-185, 188-224`; `tests/test_git_archival.py:49-57, 68-75`
**Issue:**
- `_guard_script` finds the ancestry step by name anywhere in the job. Moving it after
  `uv build` or the artifact upload keeps every test green, which contradicts
  `RELEASE.md:71` ("Both fail before anything is built").
- `_git` and `_run_git` (for `init`, `add` and `commit`) inherit the full environment. Run from
  a git hook (`GIT_DIR` / `GIT_INDEX_FILE` set), they would act on the real repository's index.
  A global `tag.gpgSign` / `commit.gpgSign` also makes the fixtures fail.
**Fix:** Assert that the ancestry step's index is less than the index of the first step
containing `uv build`. Pass
`env={**os.environ_minus_GIT_vars, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}`
to every fixture git call.

### IN-04: RELEASE.md says a PyPI release cannot be deleted

**File:** `RELEASE.md:83-87`
**Issue:** "Neither index allows deleting or replacing an already-uploaded version … deleting
outright is not possible." PyPI project owners *can* delete a release or file. What is
impossible is re-uploading the same filename or version. A maintainer who believes deletion is
impossible also misses that it is irreversible in the other direction, since the version
number is burned.
**Fix:** "A published file can be deleted, but its filename and version can never be reused;
prefer yanking, which is reversible."

### IN-05: The reworded ruleset-token comment now makes a false global claim

**File:** `.github/workflows/ruleset-apply.yml:237-238`
**Issue:** "THE one place in these workflows where a write scope is the correct answer." The
same workflow set grants these write scopes deliberately and correctly:
- `id-token: write` (`publish-pypi.yml:93`, `publish-testpypi.yml:70`).
- `issues: write` (`scheduled-health.yml:54`).

The IN-13 rewording replaced "in this phase" with a broader, untrue scope.
**Fix:** "The one place in this workflow…", or "the only Administration-write grant in this
repository".

### IN-06: CITATION.cff carries no version and makes a claim that is false between promotion and release

**File:** `CITATION.cff:15-19`
**Issue:**
- The message says "Please cite the version you used", but the file has no `version` /
  `date-released`, so GitHub's "Cite this repository" renders an unversioned citation.
- "The main branch reflects the latest released version" is false by design between a
  promotion and the release-PR merge, because `RELEASE.md:62-63` keeps the release PR open
  "until the publish is wanted".
- "Releases are published on PyPI" is untrue until 0.11.0 is uploaded.
**Fix:** Add `version` / `date-released`, which release-please can maintain via
`extra-files`. Reword the message to "Tagged releases are published on PyPI…" without the
main-branch claim.

---

_Reviewed: 2026-09-29T11:01:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
