---
phase: 06-publication-hardening-downstream-migration-record
reviewed: 2026-09-28T16:07:18Z
depth: deep
files_reviewed: 48
files_reviewed_list:
  - .gitattributes
  - .github/actions/classify-changes/action.yml
  - .github/actions/setup-python-deps/action.yml
  - .github/rulesets/develop.json
  - .github/rulesets/main.json
  - .github/scripts/check_publish_gate.py
  - .github/scripts/check_ruleset_drift.py
  - .github/scripts/preflight_ruleset_apply.py
  - .github/scripts/ruleset_lib.py
  - .github/scripts/test_check_publish_gate.py
  - .github/scripts/test_check_ruleset_drift.py
  - .github/scripts/test_classify_changes.py
  - .github/scripts/test_preflight_ruleset_apply.py
  - .github/scripts/test_ruleset_lib.py
  - .github/workflows/ci.yml
  - .github/workflows/publish-pypi.yml
  - .github/workflows/publish-testpypi.yml
  - .github/workflows/release-please.yml
  - .github/workflows/ruleset-apply.yml
  - .github/workflows/scheduled-health.yml
  - .gitignore
  - .pre-commit-config.yaml
  - .readthedocs.yaml
  - CITATION.cff
  - CONTRIBUTING.md
  - MIGRATION-v0.11.md
  - README.rst
  - RELEASE.md
  - RULESETS.md
  - docs/source/api.rst
  - docs/source/conf.py
  - docs/source/index.rst
  - pyproject.toml
  - release-please-config.json
  - scripts/smoke_pipeline.py
  - setup.py
  - src/pc2img/features/derivative_features.py
  - src/pc2img/image_cache/disk_backed_image_store.py
  - src/pc2img/strategies/projection.py
  - src/pc2img/util.py
  - tests/test_disk_backed_image_data.py
  - tests/test_hygiene.py
  - tests/test_image_store.py
  - tests/test_point_cloud_image_generator.py
  - tests/test_rrim_features.py
  - tests/test_tiled_generator.py
  - tests/test_util.py
  - uv.lock
findings:
  critical: 1
  warning: 10
  info: 13
  total: 24
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-09-28T16:07:18Z
**Depth:** deep
**Files Reviewed:** 48
**Status:** issues_found

## Summary

Scope: the whole diff `e9eb3c4..HEAD` outside `.planning/`. That is the assembled `.github/`
kit (workflows, composites, rulesets, gate scripts and their tests), the publication metadata
and docs, the migration record, the docstring-only `src/` edits, and the test and lock changes.

Every claimed defect below was reproduced by running code, not just by reading it. Things that
were checked and hold up:
- `pytest .github/scripts` passes (83 tests).
- The main suite passes: 278 passed, 62.27% branch coverage against a floor of 55.
- `sphinx-build -W` is clean.
- `uv lock --check` is clean.
- `ruff check` over the tracked `*.py` files is clean.
- The README quickstart and `scripts/smoke_pipeline.py` both run.
- `uv build` succeeds.
- The four `src/` files are **AST-identical to the base modulo docstrings**, so the docstring
  edits did not change runtime behaviour.
- All pinned action SHAs resolve to the tags their comments name, and the last phase PR's CI run
  green-lit all three required contexts.

Key concerns:

1. **Release chain (blocker).** The release workflow still pushes the floating `vX` / `vX.Y` tags
   onto the release commit. `.git_archival.txt` matches `v*`, so every GitHub source archive of
   a release (Zenodo, tarball installs, conda-forge-style recipes) resolves to `v0` / `v0.11`.
   setuptools_scm then refuses to build from it.
2. **The fast-path whitespace fix is incomplete.** A path with an embedded newline still yields
   `release-artifacts-only=true`.
3. **The migration record's verifier checks less than it claims.** Tier 1 checks zero symbols,
   and the on-disk-format probe cannot tell a pass from a fail.
4. **A new public docstring documents the wrong contract** for the `ProjectionStrategy.project_raw`
   extension point.
5. **The orchestrator's hypothesis about the `.pre-commit-config.yaml` hygiene exemption is
   confirmed.** A character class removes the only hit, so the file-wide exemption is unnecessary.
6. **Several publish, gate and preflight guarantees are narrower than stated.** Publishing can
   start from any branch or tag, the sdist then carries `.planning/` and `.claude/`, the publish
   gate misses `uv publish` and composites, and the preflight accepts contexts that no pull
   request produces.

Live state observed read-only, for context:
- `gh api repos/gseg-ethz/pc2img/rulesets` returns `[]`, so no rulesets exist yet. `RULESETS.md`
  says they were created.
- No GitHub environments exist.
- The repository is public.
- `origin/main` is not an ancestor of `origin/develop-gsd`.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Floating `vX`/`vX.Y` tags make every GitHub release source archive unbuildable

**File:** `.github/workflows/release-please.yml:65-108` (interacts with `.git_archival.txt:3` and `.gitattributes:1`)
**Issue:** On each release the "Tag major and minor versions" step creates annotated `v0` and
`v0.11` tags on the **same commit** as `v0.11.0`. `.git_archival.txt` uses
`describe-name:$Format:%(describe:tags=true,match=v*,match=release-*)$`, and `v*` matches the
floating tags. Git then describes the release commit as `v0` (or `v0.11`), not `v0.11.0`.

Reproduced two ways:
- In a scratch repo with the three tags on one commit, `git log -1 --format='%(describe:tags=true,match=v*,...)'` printed `v0`.
- `python -m setuptools_scm` over an archival file with this repo's `[tool.setuptools_scm]` config:
  - `describe-name: v0` gives `ValueError: Can't parse version from tag 'v0'`.
  - `describe-name: v0.11` gives the same error.
  - Only `v0.11.0` gives `0.11.0`.

So from the first release onward, the GitHub "Source code" tarball of every release fails to
build. That covers anything that archives or builds from it: Zenodo (the archive `CITATION.cff`
points to), `pip install https://github.com/.../archive/refs/tags/v0.11.0.tar.gz`, and distro or
conda recipes. A pushed tag's archive cannot be corrected afterwards.

This is already true of `v0.10.4`: `v0` and `v0.10` point at its commit. The phase rewrote this
step on purpose and carries the behaviour into the first PyPI release. For a Python library the
floating tags are a GitHub-Actions-repository convention with no consumer here, because
`git_describe_command` already excludes them.
**Fix:** Do either of the following. The first is preferred because it also removes the moving
tag refs that `RULESETS.md` leaves unprotected.
1. Delete the "Tag major and minor versions" step.
2. Tighten the archival match to the same X.Y.Z glob `pyproject.toml` already uses. This was
   verified to return `v0.11.0` in the scratch repo:
```text
# .git_archival.txt
describe-name:$Format:%(describe:tags=true,match=v[0-9]*.[0-9]*.[0-9]*)$
```

## Warnings

### WR-01: Release-artifact fast path still green-lights a path containing a newline

**File:** `.github/actions/classify-changes/action.yml:123-125, 195-211`
**Issue:** `gh api ... --jq '.[].filename'` prints string results raw (confirmed: `gh api
repos/actions/checkout --jq .name` prints `checkout` unquoted). A single filename containing
`\n` is therefore split into several lines before the per-line whitespace rejection ever sees
it.

Reproduced by running the shipped step body under `bash --noprofile --norc -eo pipefail`, with
a `gh` stub that emits `jq -r '.[].filename'` over a JSON fixture:
- `"CHANGELOG.md\n.release-please-manifest.json"` gives `release-artifacts-only=true`, logged as
  "all 2 changed path(s)".
- `"CHANGELOG.md\nCHANGELOG.md"` gives `true`.
- `"CHANGELOG.md .release-please-manifest.json"` gives `false` (the space case the comment
  documents).

Git permits LF in path names. This is the same bypass class the comment calls "A REAL
REQUIRED-GATE BYPASS", and it contradicts the test name
`test_no_whitespace_bearing_path_can_satisfy_the_allowlist`. It also inflates `COUNT`. With
`required_approving_review_count: 0`, a pull request consisting solely of such a file greens
all three required contexts on `main` having executed nothing.
**Fix:** Let jq produce an unambiguous, one-record-per-file encoding, and reject control
characters before splitting. For example:
```bash
if ! FILES=$(gh api --paginate "repos/${REPO}/pulls/${PRNUM}/files" \
      --jq '.[].filename | if test("[[:cntrl:][:space:]]") then "\u0000BAD" else . end' 2>"$STDERR_FILE"); then
```
Then treat any line equal to the sentinel as `emit false`. Alternatively emit `@json` per file
and compare against JSON-quoted allowlist entries. Add a newline-bearing path to
`test_no_whitespace_bearing_path_can_satisfy_the_allowlist`, using a stub that emits via
`jq -r`, so the test exercises raw-output splitting.

### WR-02: The migration record's inline verifier verifies far less than the record claims

**File:** `MIGRATION-v0.11.md:35-41, 119-124, 412-457, 494-530`
**Issue:** The prose says "Tier 1 confirms the public-surface `__all__` lists" and "Tier 2
runtime-checks every `signature-shape` claim ... and every `error-behavior`/`on-disk-format`
claim that is cheap to instantiate." Measured against that claim:

1. **Tier 1 is vacuous.** Every `affected_symbols` entry is dotted (`pc2img.x.y`), and `_tier1`
   skips anything containing `.`. After extracting and importing the verifier, the set of
   symbols Tier 1 actually checks is `[]`. The script still prints `[ok] verified 25 entries`.
2. **The BC-P2I-010 probe cannot fail.** It plants `ghost.pkl` and asserts
   `"ghost" not in store`. But `DiskBackedImageStore.__contains__` never consults disk: a fresh
   store over a directory holding a **valid** entry for `ghost` also reports
   `"ghost" in store == False`, and so does a real planted pickle. The check would pass against
   the old pickle-loading codec too. The real guarantee lives in
   `tests/test_image_store.py::test_legacy_pkl_degrades_to_cache_miss`.
3. **These cheap error-behavior claims are not checked at all:**
   - BC-P2I-007 (`NotImplementedError` on a wrapping FoV)
   - BC-P2I-013 (`ValueError("dependency cycle")`)
   - BC-P2I-014 (request-time `ValueError`)
4. **Two checks are weaker than their comments.** The BC-P2I-006 check only asserts
   `callable(convert_to_image)`, although its comment claims it verifies laziness about
   matplotlib. BC-P2I-009 checks only the `compute_dtype` parameter, not the documented "input
   no longer mutated in place".
5. **The provenance claim does not hold.** The prose says the unverified fixes are "referenced by
   origin commit sha", but entries 007–025 cite "bug-fix pass" / "gap-closure pass", not SHAs.
**Fix:** Either narrow the prose to what is actually checked, or make the checks real:
- Tier 1: resolve dotted symbols by importing the module path and `getattr`-walking, or check
  `sym.split(".")[-1]` against the barrels' `__all__` for barrel-exported names.
- BC-P2I-010: call the store's actual legacy-load path (the one the unit test uses) and assert
  `KeyError` with no unpickling.
- Add probes for 007, 013 and 014, plus an in-place-mutation probe for 009.
- Replace "bug-fix pass" / "gap-closure pass" with origin SHAs, or drop the SHA claim.

### WR-03: New `project_raw` docstring documents a contract no implementation follows

**File:** `src/pc2img/strategies/projection.py:81-95`
**Issue:** The rewritten ABC docstring (new in this phase, on a public extension point) says:
- `coords_raw` has shape `(N, 2)`
- `mins` / `maxs` are the "per-dimension minimum/maximum of `coords_raw` over the kept points"

Reproduced with `SphericalProjection(field_of_view=FoV(left=-0.1, right=0.2, top=1.4,
bottom=1.8))` on a 1000-point cloud:
- `coords_raw.shape == (792, 2)`, i.e. already masked (M rows, not N).
- `mins == [-0.1, 1.4]`, the FoV bounds, while the kept-data minimum is
  `[-0.0997, 1.4012]`.
- `OrthographicProjection` likewise returns the ROI box when one is set.

`core.py:103-111` indexes `bf_1D[mask]` against `pts2d`. A third-party strategy that follows
the documented `(N, 2)` contract would therefore produce a value/coordinate length mismatch.
**Fix:**
```python
coords_raw : NDArray
    Raw model-space coordinates of the KEPT points only, shape ``(M, 2)`` with
    ``M == mask.sum()`` (e.g. angles or xy).
mask : NDArray
    Boolean array of length ``N`` (the full cloud) marking the kept points.
mins, maxs : NDArray
    Per-dimension normalization frame used by :meth:`project`: the configured
    FoV / ROI bounds when the strategy has one, otherwise the kept-point extent.
```

### WR-04: File-wide hygiene exemption for `.pre-commit-config.yaml` is unnecessary and justified by a false statement

**File:** `tests/test_hygiene.py:155-160` (and `.pre-commit-config.yaml:6`; module docstring line 25)
**Issue:** The exemption reason says a static YAML regex cannot avoid literally naming the
planning directory. It can.

Checked by running the gate's own `_matches()` and the pre-commit `exclude` regex:
- The as-is file produces exactly one hit, `6: '.planning/'`.
- Replacing `\.planning/.*` with `\.plan[n]ing/.*` produces **zero** hits.
- The compiled `exclude` regex gives identical results before and after the change for
  `.planning/phases/x.md`, `.planning/config.json`, `.claude/CLAUDE.md`, `CHANGELOG.md`,
  `docs/ip/rrim-eth-signoff.md` and `src/pc2img/core.py`.

As shipped, any future planning reference added to this file (for example a `# see D-11`
comment) goes out unscanned. The module docstring also says "One exemption is held in
`_EXEMPTIONS`", but the dict holds two.
**Fix:** In `.pre-commit-config.yaml` write `|\.plan[n]ing/.*` (with a comment explaining the
character class). Delete the `.pre-commit-config.yaml` key from `_EXEMPTIONS` and correct the
docstring count.

### WR-05: Both publish paths can be driven from any ref, and the sdist then ships `.planning/` and `.claude/`

**File:** `.github/workflows/publish-testpypi.yml:14-15`, `.github/workflows/publish-pypi.yml:21-23`, `RELEASE.md:101-111`
**Issue:** `publish-testpypi.yml` is `workflow_dispatch` with no ref guard, unlike
`ruleset-apply.yml`, which refuses anything but `refs/heads/main`. `publish-pypi.yml` fires on
any published release, whatever commit the tag points at. No GitHub environments exist yet
(`gh api .../environments` returns an empty list), so nothing restricts `pypi` / `testpypi`
deployments to `main` or to `v*` tags. `RELEASE.md` only says to dispatch "from the release
branch".

setuptools_scm's file finder puts every tracked file into the sdist. `uv build` on
`develop-gsd` produced a tarball containing `.planning/` (PROJECT, REQUIREMENTS,
REVIEW-LEDGER, every phase directory) and `.claude/CLAUDE.md`. A mis-dispatch, or a release cut
from a non-main tag, uploads that to an index where it can never be deleted. This defeats the
filtered-projection design.
**Fix:**
- Add the same first-step guard `ruleset-apply.yml` uses. For TestPyPI, require
  `github.ref == 'refs/heads/main'`. For PyPI, require
  `github.ref_type == 'tag' && startsWith(github.ref_name, 'v')`, plus
  `git merge-base --is-ancestor "$GITHUB_SHA" origin/main`.
- Configure deployment branch/tag policies on the `pypi` (`v*` tags) and `testpypi` (`main`)
  environments, and record that in `RELEASE.md`.
- As defense in depth, add a `MANIFEST.in` with `prune .planning` and `prune .claude`.

### WR-06: `check_publish_gate.py` misses `uv publish` and publish steps inside composite actions

**File:** `.github/scripts/check_publish_gate.py:42-45, 149-152`
**Issue:** The gate only scans `.github/workflows/*.y*ml`, and it only matches
`pypa/gh-action-pypi-publish` and `twine\s+upload`. Reproduced by copying the real workflows
into a scratch tree and adding a `rogue.yml` job with `permissions: {id-token: write}`, a step
`run: uv publish --trusted-publishing always`, and a step
`uses: ./.github/actions/pub` whose composite contains `pypa/gh-action-pypi-publish@...`.
`main()` printed "OK — publish steps found only in allowed files + environments" and returned 0.

This assembly is explicitly uv-adapted, so `uv publish` is the idiomatic upload command. The
module's docstring promises containment. The PyPI trusted-publisher binding (workflow filename
plus environment) is the real backstop, but the required `Lint` context reports a containment
guarantee it does not provide.
**Fix:** Add `r"\buv\s+publish\b"`, `r"\bpoetry\s+publish\b"`, `r"\bflit\s+publish\b"` and
`r"\bhatch\s+publish\b"` to `PUBLISH_STEP_PATTERNS`. Also scan `.github/actions/**/action.y*ml`
`runs.steps`, treating any publish step there as a violation. Add tests for both cases.

### WR-07: Ruleset-apply preflight accepts required contexts that no pull request can ever produce

**File:** `.github/scripts/preflight_ruleset_apply.py:145-208, 211-242`
**Issue:** `matchable_job_names` unions job names from **every** workflow, whatever its
triggers. Reproduced: a `main.json` payload with `Branch ancestry assertion` (schedule/dispatch
only) and `Publish to PyPI` (release only) added as required contexts passed the preflight:
"OK — 5 required context(s) all matched", with a send payload written. Applying it leaves
`main` requiring checks that never report on a pull request. The preflight's own docstring says
it is "what stands between a dispatch and that state". The fix PR to `main.json` would then be
unmergeable too, leaving only a hand edit of the ruleset in the UI, which is exactly the drift
the kit exists to prevent.
**Fix:** Only count jobs from workflows whose trigger block (via `ruleset_lib.trigger_block`)
includes `pull_request`, with no `branches:` / `paths:` filter that could exclude the target
branch. Report every other name as "produced, but never on a pull request". Add a test using
`scheduled-health.yml`'s job name.

### WR-08: `CITATION.cff` publishes a placeholder DOI

**File:** `CITATION.cff:24`
**Issue:** `doi: 10.5281/zenodo.XXXXXXX` is syntactically valid, so CFF validation and GitHub's
"Cite this repository" accept and render it. On a public `main` this hands readers a citation
with a non-existent DOI. The accompanying message also says "company research data archive",
although the prefix is Zenodo's and ETH is not a company.
**Fix:** Remove `doi:` from `preferred-citation` until the concept DOI exists. Add it, and a
`version` / `date-released`, when the release is archived. Reword the message to name the
actual archive.

### WR-09: Unpinned build backend plus deprecated license metadata puts the publish build on a clock

**File:** `pyproject.toml:1-3, 15, 27`
**Issue:** `requires = ["setuptools", "setuptools_scm"]` is fully unpinned, and `uv build` in
both publish workflows resolves it fresh with no build constraints. The local build emits two
`SetuptoolsDeprecationWarning`s:
- `project.license` as a TOML table: "By 2027-Feb-18 ... your builds will no longer be supported".
- The license classifier: "License classifiers are deprecated".

The PyPI build is therefore not reproducible from the lock, and it will start failing on a
setuptools release after that deadline, at release time. `write_to` is likewise deprecated in
current setuptools_scm.
**Fix:**
```toml
[build-system]
requires = ["setuptools>=77,<81", "setuptools_scm>=8,<10"]
[project]
license = "BSD-3-Clause"
license-files = ["LICENSE", "NOTICE"]
# drop "License :: OSI Approved :: BSD License" from classifiers
[tool.setuptools_scm]
version_file = "src/pc2img/_version.py"
```
Keep `NOTICE` in `license-files` so the RRIM notice stays in the wheel's `dist-info/licenses/`,
where it is today.

### WR-10: The ancestry alarm will fire after every promotion, but the documented procedure only back-merges after releases

**File:** `RULESETS.md:34-41`, `.github/workflows/scheduled-health.yml:76-114`
**Issue:** `scheduled-health.yml` asserts that `main` is an ancestor of `develop-gsd`. Every
filtered promotion is a squash, and it creates a commit on `main` that is not in `develop-gsd`.
The assertion therefore fails, and opens or comments on an issue nightly, from the first
promotion until a back-merge. Today `origin/main` is already not an ancestor
(`merge-base --is-ancestor` fails).

`RULESETS.md` prescribes a one-time graft plus "one back-merge ... follows every release". But
`RELEASE.md` keeps the release PR open "until the actual publish is wanted", so the promotion
and the release are decoupled. The same paragraph's rationale is also false: it says the
branches "do not currently share a common ancestor", yet `git merge-base origin/main
origin/develop-gsd` returns `f946268`, and `v0.10.0`–`v0.10.4` are reachable from both.
**Fix:** In `RULESETS.md`, require a true-merge back-merge after **every promotion and every
release-PR merge**. Correct the rationale to "main carries commits (`69224a9`, `ade40f8`) that
develop-gsd lacks". Optionally schedule the first promotion and the graft back-to-back, before
the first nightly run on `main`.

## Info

### IN-01: Two actions are pinned to annotated tag-object SHAs, not commit SHAs

**File:** `.github/workflows/scheduled-health.yml:118`, `.github/workflows/ci.yml:272`
**Issue:** `git ls-remote` shows the pins resolve like this:
- `actions/github-script@d746ffe…` is the `v9.0.0` **tag object**; its commit is `3a2844b…`.
- `codecov/codecov-action@8cad3ba…` is the `v6.0.2` tag object; its commit is `fb8b358…`.

The runner resolves both (seen in the phase PR's job log), and the checklist's 40-hex grep
passes. But these are the only two pins not on the dereferenced commit, which is the form
pinning tools and auditors expect.
**Fix:** Pin to `3a2844b7e9c422d3c10d287c895573f7108da1b3` and
`fb8b3582c8e4def4969c97caa2f19720cb33a72f`.

### IN-02: "Upload type-check report" can never upload anything

**File:** `.github/workflows/ci.yml:249-255`
**Issue:** `pyright-action` writes no `.pyright-report.json`. The phase PR run logged "No files
were found with the provided path".
**Fix:** Delete the step, or run pyright with `--outputjson > .pyright-report.json`.

### IN-03: `attestations: write` is an unneeded grant, and its comment is wrong

**File:** `.github/workflows/publish-pypi.yml:62`, `.github/workflows/publish-testpypi.yml:59`
**Issue:** PEP 740 attestations from `gh-action-pypi-publish` need only `id-token: write`.
`attestations: write` is for GitHub artifact attestations, which nothing here produces.
**Fix:** Drop the grant and the "required to attach" comment in both files, and update the
`RULESETS.md` deviation bullet.

### IN-04: Comments and docstrings reference components this assembly declined

**File:** `.github/workflows/ci.yml:19-29, 39-42, 55-67`, `.github/actions/classify-changes/action.yml:64-74, 176-186`, `.github/scripts/check_ruleset_drift.py:12-20`, `.github/scripts/ruleset_lib.py:5-9`
**Issue:** These cite `check_ci_config.py` assertions A1–A7, `integrity.yml`, `assert_no_skip.py`
and "the nightly job in ... `ruleset-drift.yml`". `RULESETS.md` records all of these as
declined, and none exist. Readers of the public tree are pointed at enforcement that is not
there.
**Fix:** Prune the conditional passages, or add one line per file: "declined in this assembly;
see RULESETS.md".

### IN-05: `RULESETS.md` states the rulesets exist, but the live list is empty

**File:** `RULESETS.md:176-181, 368-376`
**Issue:** It says "the first creation of both rulesets was done once by posting the committed
payload directly". `gh api repos/gseg-ethz/pc2img/rulesets` currently returns `[]`, and the
creation is still planned for later plans. That is false at promotion time.
**Fix:** Word it as future or conditional until the creation has run.

### IN-06: `ci.yml` header contradicts its own trigger block

**File:** `.github/workflows/ci.yml:34-38, 81-82`
**Issue:** It says "`push:` deliberately does NOT list the protected branch", but it lists
`develop-gsd`, which `develop.json` protects. The template means the release branch.
**Fix:** Say "the release branch (`main`)".

### IN-07: Two different ruff versions gate formatting of the same tree

**File:** `.pre-commit-config.yaml:17`, `tests/test_hygiene.py:109-130`, `uv.lock` (ruff 0.15.21)
**Issue:** The Lint context formats with `ruff-pre-commit v0.15.12`. The Tests context
(`test_ruff_check_src_is_clean`) runs the locked ruff 0.15.21. A formatter-output change between
the two versions makes the two required contexts disagree. The pre-commit `rev`s are also
mutable tags.
**Fix:** Align the `rev` with the lock (or use a `language: system` local hook running the
locked ruff), and pin the `rev`s by SHA.

### IN-08: Twenty non-executable files are committed with mode 100755

**File:** `.github/**` (all 19 files), `release-please-config.json` (its mode changed from 100644 in this diff)
**Issue:** YAML, JSON and library modules carry the executable bit on a public branch.
**Fix:** `git update-index --chmod=-x` on everything except scripts intended to run directly.
Consider enabling `check-executables-have-shebangs`.

### IN-09: Migration-record summary arithmetic is wrong

**File:** `MIGRATION-v0.11.md:20-27`
**Issue:** It says "twenty-five changes: sixteen should-review ... one must-edit ... five
informational ... four additive". That sums to 26. The table has 15 should-review entries
(001, 002, 006–009, 011, 013–020).
**Fix:** Change "sixteen" to "fifteen".

### IN-10: Stale or inconsistent public docs

**File:** `CONTRIBUTING.md:74-75`, `README.rst:8`, `docs/source/index.rst:8`
**Issue:**
- `CONTRIBUTING.md` gives the baseline as "252 passed"; the suite is 278.
- `README.rst` lists "spherical or orthographic", while `index.rst` and the registry include
  `perspective`.
**Fix:** Update the figures and add `perspective` to the README.

### IN-11: The RTD build silently tolerates a tagless checkout

**File:** `.readthedocs.yaml:15-19`
**Issue:** `git fetch --unshallow --tags || true` swallows every failure. On a non-shallow clone,
`--unshallow` errors out, so the tags are never fetched. `fail_on_warning` does not see the
`0.0.` fallback that CI's docs job explicitly asserts against.
**Fix:** Use `git fetch --tags --force && (git rev-parse --is-shallow-repository | grep -q false || git fetch --unshallow)`, and add the same `startswith("0.0.")` assertion as a `pre_build` job.

### IN-12: The protection-rewriting jobs rely on the runner image's unpinned PyYAML

**File:** `.github/workflows/ruleset-apply.yml:226, 342`, `.github/scripts/preflight_ruleset_apply.py:49`
**Issue:** `python3` is the image's system interpreter, and `import yaml` depends on
`ubuntu-latest` happening to ship `python3-yaml`. An image change would break ruleset applies,
with a traceback instead of a named error.
**Fix:** Add `./.github/actions/setup-python-deps` (or `uv run --frozen`) before the preflight,
or guard the import with an explicit `::error::`.

### IN-13: Planning vocabulary survives in shipped prose that the gate's regexes cannot see

**File:** `MIGRATION-v0.11.md:9, 20, 62-80, 93`, `.github/workflows/ruleset-apply.yml:235`, `tests/test_hygiene.py:17, 97`
**Issue:** Phrases that pass the gate:
- `milestone: v1.0` for a 0.11 release.
- "This milestone's first six phases".
- "publication pass, this phase — ... not yet executed as of this draft".
- "gap-closure pass".
- "THE one place in this phase".

`docs/ip/rrim-eth-signoff.md` is exempt by design.
**Fix:** Reword these as release-facing prose. Optionally extend `_PHASE_PLAN_PATTERN` with
`\bthis phase\b` and `\bgap[- ]closure\b`.

---

_Reviewed: 2026-09-28T16:07:18Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
