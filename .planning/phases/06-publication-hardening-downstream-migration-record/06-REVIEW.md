---
phase: 06-publication-hardening-downstream-migration-record
reviewed: 2026-09-29T15:27:30Z
depth: deep
files_reviewed: 13
files_reviewed_list:
  - .github/actions/classify-changes/action.yml
  - .github/scripts/check_publish_gate.py
  - .github/scripts/check_ruleset_drift.py
  - .github/scripts/ruleset_lib.py
  - .github/workflows/ci.yml
  - .github/workflows/publish-pypi.yml
  - .github/workflows/publish-testpypi.yml
  - .github/workflows/ruleset-apply.yml
  - .github/workflows/scheduled-health.yml
  - CITATION.cff
  - RELEASE.md
  - RULESETS.md
  - tests/test_projection.py
findings:
  critical: 0
  warning: 7
  info: 8
  total: 15
status: issues_found
---

# Phase 6: Code Review Report (round 3: round-2 doc pass, 5691315..c3b44d9)

**Reviewed:** 2026-09-29T15:27:30Z
**Depth:** deep
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Scope: `git diff 29039d5..HEAD` over the 13 listed files. This is a prose, comment and docstring pass.

**Behaviour, checked by running code:**
- `yaml.safe_load` of all six workflow/action files plus `CITATION.cff` gives the same objects at `29039d5` and `HEAD`, with two intended exceptions:
  - `jobs.lint.steps[5].run` in `ci.yml` (the one Lint log string);
  - `message` in `CITATION.cff`.
- `ast.dump` is identical for `check_publish_gate.py` and `tests/test_projection.py`.
- `check_ruleset_drift.py` and `ruleset_lib.py` differ only in their module docstrings; with docstrings stripped, their ASTs are identical.
- `cffconvert --validate` passes.
- `tests/test_hygiene.py` plus `.github/scripts/` give 180 passed.
- No planning IDs, planning paths or review-finding identifiers appear in the added lines or in the full files. The only hit is the real branch name `develop-gsd`.

**What matches the source:**
- The RULESETS.md rules table matches `.github/rulesets/main.json` and `develop.json` cell by cell.
- RELEASE.md's secrets and environment names match the workflows, and so do its trigger chain (release-please on push to `main`, then `release: published`, then publish-pypi) and its version-bump rules (`bump-minor-pre-major`, `bump-patch-for-minor-pre-major`).
- The `RELEASE.md "Ref guards"` pointer resolves.

**Defects.** They are all in what the prose now says, or no longer says:
1. Deleting the "declined component" pointers left present-tense claims that a nightly drift workflow and `check_ci_config.py` exist. Neither ships.
2. The new keep-by-hand rule in `ci.yml` is now the only enforcement, and it points at the wrong YAML location.
3. The shortened RULESETS.md drops two things:
   - the admin-token requirement for reading the bypass list, even though a new `ruleset-apply.yml` comment says the doc states it;
   - the fact that an edited payload must reach `main` before the apply workflow can see it.
4. The new CITATION.cff sentence tells users to cite a version string that, for any install that is not a release, was never released. This was reproduced: the dev venv reports `0.10.4.post407`.

**Live state, read-only:**
- `gh api repos/gseg-ethz/pc2img/rulesets` returns `[]`.
- `main` has no branch protection.
- The repository has no environments.
- `pc2img` returns 404 on both PyPI and TestPyPI.

Both docs describe a target state that does not exist yet. That is expected before 06-18, but it makes the ruleset-bootstrap gap in WR-05 current, not hypothetical.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Deleting the "declined" pointers turned disclosed absences into false present-tense claims about drift detection and a CI self-check

**File:**
- `.github/workflows/ruleset-apply.yml:13-15`
- `.github/workflows/scheduled-health.yml:6-7, 36-39`
- `.github/scripts/check_ruleset_drift.py:11-19`
- `.github/scripts/ruleset_lib.py:5-8, 16-20`
- `.github/scripts/check_publish_gate.py:124-127`

**Issue:** At each of these sites the removed two-line comment was the only thing in the file saying the referenced component is not in this repository. The claims it qualified are still there, and they are not conditional:
- **`ruleset-apply.yml:13-15`:** "Detection lives in the continuous-enforcement component's ruleset-drift workflow, which holds no write."
- **`check_ruleset_drift.py:11-17`:** "Called from two workflows in this kit … The nightly job in the continuous-enforcement component's `ruleset-drift.yml` runs it on a schedule … Both callers write…"
- **`ruleset_lib.py:5-8`:** "Importers are `check_ruleset_drift.py` …, `check_ci_config.py` (the CI self-test) and `preflight_ruleset_apply.py` …, all of which live in this same directory." Lines 16-20 also describe a "read-only drift job".
- **`check_publish_gate.py:124-127`:** names a sibling parser `check_ci_config.load_workflows`.

`ls` confirms that `.github/workflows/ruleset-drift.yml`, `.github/workflows/integrity.yml` and `.github/scripts/check_ci_config.py` do not exist.

The practical harm is false assurance on a safety property. A maintainer who reads `ruleset-apply.yml` will believe a ruleset edited in the web UI gets detected overnight. Nothing detects it: the only caller of `check_ruleset_drift.py` is the post-apply read-back. The plan deferred only the conditional "when the … component is applied" phrasing. These sentences are unconditional, so the deferral does not cover them.

**Fix:** Keep the pointers deleted, but make each claim true for this repository. For example:
```yaml
# ruleset-apply.yml:13-15
# Nothing in this repository checks live rulesets against the committed payloads
# on a schedule; the only comparison is this workflow's post-apply read-back.
```
```python
# check_ruleset_drift.py — replace lines 11-19 with:
"""Called from ``ruleset-apply.yml``'s post-apply read-back, which writes the live
read with ``includes_parents=false`` first — a parent organization ruleset is not
drift in a committed file and would be reported as one."""
```
- **`ruleset_lib.py`:** drop `check_ci_config.py` from the importer list.
- **`check_publish_gate.py`:** drop the `check_ci_config.load_workflows` reference.
- **`scheduled-health.yml:6-7`:** drop the drift-workflow sentence.

### WR-02: The new keep-by-hand rule in `ci.yml` points at the wrong YAML location and is narrower than the rule it replaces, and it is now the only enforcement

**File:** `.github/workflows/ci.yml:20-21`
**Issue:** The rule in lines 13-15: no job-level `if:`, and no filter key (`paths:`, `paths-ignore:`, `branches:`, …) under `pull_request:`. The new hand instruction reads: "never put a job-level `if:` or a `paths:` filter on a required-context job."
- **Wrong location:** path filters cannot go on a job. They go on the workflow trigger (`on.pull_request.paths`), where they filter every job in the file. A maintainer checking "the job" against this sentence never looks at `on:`, which is where the defect would actually be.
- **Too narrow:** it names only `paths:`. `paths-ignore:` and `branches:` have the same effect: the run never reports, and the pull request is stranded under `bypass_actors: []`.

`check_ci_config.py` (assertions A1/A5) does not exist, so this sentence is the only guard. Line 21 is also 130 columns, past the project's 120 limit and unlike the ~80-column wrap around it (see IN-07).

**Fix:**
```yaml
#     in `.github/scripts/check_ci_config.py` fail the build if either returns,
#     when the config self-inspection component is applied; otherwise keep this
#     by hand: never add a job-level `if:` to any job here, and never add a
#     `paths:`, `paths-ignore:` or `branches:` key under `on.pull_request`.
```

### WR-03: RULESETS.md's inspection note omits the admin-token requirement, and a new `ruleset-apply.yml` comment says the note includes it

**File:** `RULESETS.md:27-28`, `.github/workflows/ruleset-apply.yml:243-245`
**Issue:**
- **The cross-reference is wrong.** The rewritten token-mint comment says a read-scoped token "does not receive the bypass list at all, which is why RULESETS.md's live-inspection note reads a ruleset by id with an administration-capable token." RULESETS.md says only `gh api repos/gseg-ethz/pc2img/rulesets/<id>` "(the list endpoint omits the bypass list)". It says nothing about the token.
- **The note itself can give a false answer.** By this repository's own premise (the same comment), a reader whose `gh` token lacks administration access gets a response with no `bypass_actors` key. They then read the absence as "no bypass". This is the exact misreading the old doc warned about ("an absent key tells you nothing, only an empty array tells you the list really is empty"), and the rewrite dropped that warning.

**Fix:** In RULESETS.md:
```markdown
- **Inspect a live ruleset:** `gh api repos/gseg-ethz/pc2img/rulesets/<id>` with a
  token that has repository administration access. Without it the response omits
  `bypass_actors` entirely; only an empty array (`[]`) confirms there is no bypass.
  The list endpoint never includes it.
```
Alternatively, drop "which is why RULESETS.md's …" from the workflow comment.

### WR-04: The write-scope list in the ruleset-token comment is incomplete, repeating the defect class of the round-2 fix

**File:** `.github/workflows/ruleset-apply.yml:235-242`
**Issue:** The comment says "The other write scopes in this directory — `id-token` on the publish jobs and `issues` on the health check —". Enumerating every `permissions:` block and every App-token mint gives:
- `attestations: write` on both publish jobs (`publish-pypi.yml:94`, `publish-testpypi.yml:78`). The comment omits it.
- The release App token (`release-please.yml:45-49`). It is minted with **no** `permission-*` inputs, so it carries the full installation grant of `gseg-release-please`.

Because of that second point, the lead claim "The only Administration-write grant in this repository's workflows" cannot be checked from the repository. It holds only if the release App's installation was never granted Administration, and nothing in the repository narrows or asserts that.

**Fix:**
```yaml
# ... (The other write grants here — `id-token` and `attestations` on
# the publish jobs, `issues` on the health check, and the release App's token
# in release-please.yml — are different grants for different reasons.)
permission-administration: write
```
Also narrow the release mint (`permission-contents: write`, `permission-pull-requests: write`) so the "only Administration-write" claim is enforced rather than assumed. That part is a behaviour change: plan it separately, not under this prose-only plan.

### WR-05: RULESETS.md's "change a rule" recipe applies the old payload after a normal edit, and fails outright with no ruleset to update

**File:** `RULESETS.md:24-25`
**Issue:** "edit `.github/rulesets/main.json` or `develop.json`, then run the `ruleset-apply` workflow from `main`."
- **Normal edit: silent no-op.** The same doc says to open PRs against `develop-gsd`, so a payload edit lands there first. `ruleset-apply.yml` refuses every ref except `main` (lines 75-86) and applies the payload from **main's** checkout (lines 88-93, 128-132). Dispatching right after the edit merges re-applies main's old payload. The verify step then compares live against that same old file and passes, so the run reports "applied" and verifies clean while nothing changed. The doc says nothing about the edit having to reach `main` (by promotion) first.
- **No ruleset: hard failure.** The workflow has no create path. It exits with "no ruleset named `protect-main`" when none exists (lines 187-190). Live, `gh api repos/gseg-ethz/pc2img/rulesets` returns `[]` today. The old doc's note ("the first creation posts the preflight-produced payload once directly through the API") was deleted, so after the rewrite the shipped docs contain no working procedure for the current state, or for re-creating a deleted ruleset.

**Fix:**
```markdown
- **Changing a rule:** edit `.github/rulesets/main.json` or `develop.json` and get
  the change onto `main` (the workflow reads payloads from `main` only), then run
  the `ruleset-apply` workflow from `main`. It updates an existing ruleset only;
  creating one is a single `gh api --method POST repos/gseg-ethz/pc2img/rulesets
  --input <payload>`. Never edit rulesets in the web UI.
```
Check that 06-18 covers the initial POST, since live state has none.

### WR-06: CITATION.cff tells users to cite installed version metadata, which for any install that is not a release is a version that was never released and is not unique

**File:** `CITATION.cff:16-17`
**Issue:** New text: "cite the version you used, taken from the release tag or from the installed package's version metadata."
- `pyproject.toml:52-53` sets `version_scheme = "post-release"` and `local_scheme = "no-local-version"`. Any install from a commit that is not a tag therefore reports `<last-tag>.postN`, with no commit hash.
- Reproduced: `importlib.metadata.version('pc2img')` in the dev venv reports `0.10.4.post407`. No such version exists on any index or tag.
- `N` counts commits since the tag. Two different branches with the same distance report the same string, so it does not identify code either.

This is citation guidance for a project whose core value is reproducible output. Following it for a git install produces a citation that points at nothing.

**Fix:**
```yaml
message: >
  Releases are tagged on GitHub. Please cite the release you used (the tag,
  e.g. v0.11.0). If you used an unreleased commit, cite the commit hash instead
  of the installed version string, which does not identify unreleased code.
  A persistent identifier will be added to this file when a release is archived.
```

### WR-07: RELEASE.md's promotion step, the premise every ref guard depends on, names neither the directories nor a mechanism, and nothing checks it

**File:** `RELEASE.md:30`
**Issue:**
- **Why this step matters.** "Promote `develop-gsd` to `main` (squashed, internal directories stripped)." Every ref guard in `publish-pypi.yml` and `publish-testpypi.yml` rests on the premise that `main` is the stripped tree. The TestPyPI guard's own error text says "every other ref still carries the internal planning directories".
- **What the doc leaves out.** It does not say which directories are "internal", and gives no mechanism for stripping them.
- **The literal reading does the damage.** Read literally, "promote `develop-gsd` to `main` (squashed)" means opening a PR from `develop-gsd` to `main` and squash-merging it. That lands `.planning/` and `.claude/` on `main`.
- **Nothing catches it.** setuptools-scm's file finder puts every git-tracked file into the sdist. The next release then uploads them permanently, and no re-upload can undo it (RELEASE.md's own Rollback section). RELEASE.md:43 admits "No environment rule or package-content check backs this up". The hygiene gate exempts exactly those directories (`tests/test_hygiene.py:151-152`), so no CI signal fires either.

**Fix:**
- In the doc, name the stripped paths and the mechanism. For example:
```markdown
1. Promote `develop-gsd` to `main`: open the pull request from a branch cut from
   `main` that carries `develop-gsd`'s tree minus `.planning/` and `.claude/`
   (never a pull request from `develop-gsd` itself), and squash-merge it.
```
- Separately (a behaviour change, so for a later plan): add a Lint step that fails when `.planning/` or `.claude/` is present on a PR whose base is `main`. That gives the premise an automated check instead of only a written one.

## Info

### IN-01: "X.Y.Z tag" does not match the guard, which requires a `v` prefix

**File:** `RELEASE.md:39-40`
**Issue:** "PyPI only from an `X.Y.Z` tag on `main`." `publish-pypi.yml:47` requires `^v[0-9]+\.[0-9]+\.[0-9]+$`. Meanwhile `pyproject.toml:54` (`tag_regex`) accepts an optional `v` and pre-release suffixes, and the guard refuses both. A hand-made `0.11.1` tag or `v0.12.0rc1` release is refused at publish time.
**Fix:** "PyPI only from a `vX.Y.Z` tag on `main` (no pre-release suffix)."

### IN-02: `Release-As:` needs an explicit version and must be on the commit that lands on `main`

**File:** `RELEASE.md:26-27`
**Issue:** "Force a minor bump with a `Release-As:` footer." release-please reads `Release-As: <version>` as an exact version, not as a bump level. It only sees commits on `main`, which here means the squashed promotion commit.
**Fix:** "Force a specific version with a `Release-As: 0.12.0` footer on the promotion commit."

### IN-03: Following the lint-permissions keep-by-hand rule literally disables the fast path

**File:** `.github/workflows/ci.yml:41-42`
**Issue:** "leave the lint job's `permissions:` at `contents: read`". The block actually holds `contents: read` **and** `pull-requests: read` (lines 99-100). The second is needed by `classify-changes` (its description says the caller MUST grant it). Following the sentence literally makes the classifier fail safe: a warning appears and the fast path goes inert.
**Fix:** "leave the lint job's `permissions:` read-only (`contents: read`, `pull-requests: read`) whenever you edit it."

### IN-04: "Recorded deviation" comments now point at a record that was deleted

**File:** `.github/workflows/publish-testpypi.yml:73, 90`; `.github/workflows/ci.yml:259-262`
**Issue:** These comments call the attestation grant on TestPyPI, and the coverage floor, a "recorded deviation" or "recorded addition". The record was RULESETS.md's "Recorded deviations" section, which this diff removed. They now reference nothing.
**Fix:** Drop "recorded" and state the reason inline, which both comments mostly do already.

### IN-05: CITATION.cff says releases are published on PyPI; none are yet

**File:** `CITATION.cff:16`
**Issue:** "Releases are tagged on GitHub and published on PyPI." Right now `https://pypi.org/pypi/pc2img/json` returns 404, and the existing releases `v0.10.0`..`v0.10.4` exist only as GitHub tags. Round 2 raised this point (in the CITATION finding), and this rewrite did not address it. It becomes partly true once 0.11.0 is uploaded, but remains untrue for every earlier tag.
**Fix:** "Releases are tagged on GitHub; from 0.11.0 on, they are also published on PyPI."

### IN-06: "Run the same checks locally" points at commands that do not match CI

**File:** `RULESETS.md:19`
**Issue:**
- **Lint:** CONTRIBUTING.md's local commands do not cover the `Lint (pre-commit)` job's `check_publish_gate.py` and `pytest .github/scripts/` steps.
- **Tests:** the local `uv run pytest` skips the `Tests (pytest)` job's `-m "not benchmark" … --cov-fail-under=55`.

A contributor who is green locally can still fail a required check.
**Fix:** "Run the main checks locally (CONTRIBUTING.md). CI runs extra gate scripts and a coverage floor on top of them." Alternatively, add those commands to CONTRIBUTING.md.

### IN-07: Three edited lines were not rewrapped

**File:** `.github/workflows/ci.yml:21` (130 cols), `RELEASE.md:41` (141), `CITATION.cff:16` (122)
**Issue:** The surrounding text is wrapped at about 80 columns. These three lines exceed even the project's 120-column limit. Nothing checks YAML/Markdown width, so they will stay this way.
**Fix:** Rewrap to match the neighbouring lines.

### IN-08: The deferred "apply-time checklist" phrases point at a checklist that is not shipped

**File:** `.github/workflows/scheduled-health.yml:12-13`, `.github/actions/classify-changes/action.yml:73-74`
**Issue:** Both still say that, without the self-inspection component, this is "an apply-time checklist item". The checklist was the strategy document, which is not shipped, and every other reference to it was removed in this pass. The plan explicitly deferred these two, so this entry only records that they still dangle after the pass.
**Fix:** Use the same wording as the `ci.yml` rewrite: "otherwise keep this by hand: …".

---

_Reviewed: 2026-09-29T15:27:30Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
