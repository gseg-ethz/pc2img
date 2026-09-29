# CI/CD adoption record — pc2img (internal)

This is the full record decision D-15 required. On 2026-09-29 the owner decided (D-34) that the
public `RULESETS.md`/`RELEASE.md` keep only what a maintainer needs and that this record lives
under the internal planning directory. Nothing was deleted in that condensation — everything the
public docs no longer carry verbatim is preserved below, corrected where a review round found it
wrong.

---

# Branch Rulesets — pc2img

**Repository:** gseg-ethz/pc2img
**Protected branches:** `main`, `develop-gsd`
**Ruleset names:** `protect-main`, `protect-develop-gsd`
**Ruleset snapshots:** `.github/rulesets/main.json`, `.github/rulesets/develop.json`
**Template followed:** the shared GSEG git-strategy kit — core tier (branch protection + CI
shape) plus the release-to-PyPI component — assembled for a public repository.

This record states the interview answers this repository gave the template, which optional
components were taken and declined, every place this assembly's configuration differs from the
template's own defaults, the twelve-item checklist run against the assembled tree with its
evidence, and how to verify the live protection state against what is committed here.

---

## Interview answers

The template poses a fixed set of questions before assembly. This repository's answers, recorded
so they are not asked again:

| Question | Answer |
|---|---|
| Integration branch | `develop-gsd` |
| Release branch | `main` |
| Is the release branch a true release branch, or a filtered projection of the integration branch? | A **filtered projection**: promotion from `develop-gsd` to `main` is a squash that strips the internal planning paths (the tracked agent-planning directories) rather than a plain merge. Nothing else in the flow changes because of this — the promoted commit still lands on `main` as a normal commit. |
| Required check contexts | `Lint (pre-commit)` and `Tests (pytest)` on both protected branches; `Docs (sphinx -W)` on `main` only. |
| Merge methods on the integration branch | Merge, squash and rebase all stay enabled. The merge-commit method must stay available because the back-merge and the one-time ancestry graft below are both true merges, never squashes or rebases. |
| Rulesets before this assembly | None. The repository's API returned an empty ruleset list and there was no pre-existing branch protection of any kind. |
| Import/package name | `pc2img` (both the distribution name and the importable package). |
| Python version | 3.12. |
| Release automation | Enabled — the release-please bot manages the changelog and version bump. |

Consequences that follow mechanically from these answers, not separate choices: linear-history
enforcement applies to `main` only (see "Required status checks" below); the two rulesets'
strictness policy is intentionally asymmetric (see "Deviations from the template"); and, after
every promotion to `main` and after every merge of a release pull request, `main` is merged back
into `develop-gsd` with the "Create a merge commit" method, never squash or rebase, because either
would silently collapse the second parent and break the ancestry the nightly assertion below
watches. The first such back-merge, immediately after the first promotion, is also the ancestry
graft — the branches share the common ancestor `f946268`, but `main` carries commits (`69224a9`,
`ade40f8`) that `develop-gsd` lacks, and each squash promotion after that adds one more.

---

## Components: taken and declined

**Taken:** the core tier (branch protection payloads, the three-job CI shape, the release-artifact
fast path, the dispatch-only ruleset-apply workflow, the nightly ancestry assertion) plus the
release-to-PyPI component (trusted-publisher OIDC publishing, attestations, the TestPyPI dry-run
workflow).

**Declined:** the self-inspecting CI config checker, the continuous pull-request-side enforcement
workflow, and the self-hosted GPU runner support. This project ships no GPU-dependent tests of its
own — its CUDA extras only pass through to a dependency's own GPU code paths — so there is nothing
for a self-hosted GPU job to exercise here.

**Cost of declining, stated plainly:** every floor and default property in the checklist below is
verified **once**, at assembly time, by a person or agent actually running the evidence commands.
Without the self-inspecting checker or the continuous enforcement workflow, later drift — a
contributor adding a path filter to a required-check workflow, someone editing a ruleset by hand
in the web interface instead of through the committed payload — is not caught automatically. It
would only be discovered when it actually breaks something, for example a pull request stuck
forever on a check that never reports. The owner accepted this trade-off in exchange for a smaller
surface to maintain.

---

## Bypass list

**The bypass list is EMPTY on both rulesets.**

No actor — not the release automation, not repository administrators — appears on either bypass
list. Nobody can merge a change whose required checks are red, and nobody can force-push or delete
a protected branch by routing around the ruleset.

**Why release automation needs no bypass entry:** the release bot only ever pushes to its own
scratch branch when it opens a release pull request, which is not one of the protected refs, and
it moves major/minor tags on release, which branch rulesets do not cover at all (tag refs are a
separate protection surface, deferred below). Neither action needs to bypass anything.

---

## Approval policy

**Pull request required; `required_approving_review_count = 0`.**

Direct pushes to `main` or `develop-gsd` are blocked — every change must arrive through a pull
request with its required checks passing. The approval count is deliberately zero: this repository
is maintained by a single owner working with an agent and CI, and GitHub forbids self-approval, so
any nonzero approval requirement combined with the empty bypass list above would deadlock every
solo-authored pull request — nobody could approve it, and nothing could bypass the block. Zero
approvals keeps the required status checks as the sole hard gate while avoiding that deadlock.

The remaining pull-request flags are explicitly off on both rulesets: `dismiss_stale_reviews_on_push`,
`require_code_owner_review`, `require_last_push_approval`, and `required_review_thread_resolution`.

**Future tightening:** moving to a nonzero approval count, once a second routine reviewer exists,
is recorded below under "Deferred" — it is not a gap in today's protection, it is a known next step.

---

## Required status checks

Check-run context strings are the exact `name:` field of the producing job in
`.github/workflows/ci.yml`. If a job is ever renamed, the ruleset payload requiring its old name
must be updated in the same commit as the rename, or the branch becomes unmergeable by anyone —
the bypass list is empty, so there is no escape hatch.

| Check | Required on | Producing job |
|---|---|---|
| Lint (pre-commit) | main, develop-gsd | `.github/workflows/ci.yml`, job `lint` |
| Tests (pytest) | main, develop-gsd | `.github/workflows/ci.yml`, job `tests` |
| Docs (sphinx -W) | main only | `.github/workflows/ci.yml`, job `docs` |

**Strictness (`strict_required_status_checks_policy`) is `true` on `main` and `false` on
`develop-gsd`** — this asymmetry is a recorded deviation, explained below, not an oversight.

**Linear history (`required_linear_history`) is required on `main` only**, never on
`develop-gsd`. This is the single deliberate asymmetry between the two payloads: the back-merge
from `main` into `develop-gsd` lands as a true merge commit, and a linear-history rule on the
integration branch would refuse that merge outright, which would make the ancestry graft
impossible in the first place.

---

## Deviations from the template

Every place this assembly's configuration differs from what the template ships by default, with
the reason and the file where the deviation lives:

- **Dependency install in the setup composite.** The template's setup composite installs the
  development toolchain as a package extra via `pip install .[dev]`. This project's development
  tooling (lint, test and formatting tools) is declared as a dependency group rather than an
  extra, so an extras-based install would pull in nothing. `.github/actions/setup-python-deps/action.yml`
  instead runs `uv sync --frozen` against the committed lockfile and prepends the resulting
  virtual environment to the runner's `PATH`, so every subsequent bare-name tool invocation
  resolves into the locked environment.
- **Documentation dependency install.** For the same reason, the documentation job installs its
  own dependency group with `uv sync --frozen --group doc` rather than a `pip install .[doc]`
  extras line. The hosted documentation build mirrors this by installing the group directly rather
  than through the extras mechanism the hosting platform defaults to.
- **Lint tool source.** The lint job runs `pre-commit` from the locked development dependency
  group already on `PATH` via the setup composite above, rather than a separate `pip install
  pre-commit` step — there is no `pip` at all in the `uv`-built virtual environment.
  `.github/workflows/ci.yml`, job `lint`.
  See also "Multi-command run steps" in the checklist below.
- **Checkout depth on the test and documentation jobs.** Both checkout with full history
  (`fetch-depth: 0`) rather than the template's shallow default, because the build backend derives
  the package version from git tags at build and import time, and a shallow clone would silently
  fall back to a placeholder version. `.github/workflows/ci.yml`.
- **Coverage floor.** A `--cov-branch --cov-fail-under=55` flag pair rides along on the test
  command. The template's own tests job carries no coverage gate at all; this is an addition
  carried forward from this repository's own prior CI, kept rather than dropped so an existing
  gate is not weakened by the template swap. `.github/workflows/ci.yml`, job `tests`.
  (`--cov-fail-under=55` present: **1**.)
- **Type-check target.** The informational type-check step is pointed explicitly at the locked
  virtual environment's interpreter (`python-path: .venv/bin/python`) rather than whatever ambient
  interpreter the action would otherwise fall back to, so it resolves the same imports the locked
  environment provides. `.github/workflows/ci.yml`, job `tests`.
- **Build tool in both publish workflows.** Both the production and dry-run publish workflows
  build with `uv build` rather than the template's `pip install build && python -m build` — again
  because the setup composite's virtual environment ships no `pip`.
  `.github/workflows/publish-pypi.yml`, `.github/workflows/publish-testpypi.yml`.
- **Attestations on the dry-run publish.** The dry-run workflow requests attestations
  (`attestations: true` on the publish step, `attestations: write` on the job's permission grant)
  even though the template disables attestations on the test index by default. This dry run exists
  specifically to exercise the complete OIDC-and-attestation publish path once before the real
  index is ever touched, so attestations are deliberately turned on here.
  `.github/workflows/publish-testpypi.yml`.
- **Kit-shipped test fixtures.** Two of the template's own bundled test files needed
  reformatting-only edits to keep the whole-tree lint gate green after assembly; no test behavior
  changed. `.github/scripts/test_preflight_ruleset_apply.py`, `.github/scripts/test_check_publish_gate.py`.
- **Release manifest left unchanged.** The template ships a fresh-project placeholder version in
  its release manifest; this assembly kept the manifest at its pre-existing recorded version
  instead of overwriting it, since this repository already has a release history the template's
  placeholder would have discarded. `.release-please-manifest.json`.
- **Initial ruleset creation.** The dispatch-only apply workflow updates an existing ruleset by
  name; it has no create path. Because this repository started with no rulesets at all (see the
  interview answer above), the first creation of each ruleset is a single direct post of the
  preflight-produced payload, performed by plans 06-10 and 06-11 at apply time; every apply from
  that point forward goes exclusively through the dispatch-only workflow.
- **Strictness asymmetry.** Already noted under "Required status checks" above: `main` requires a
  pull request to be up to date with its base before merging; `develop-gsd` does not, because no
  release automation triggers from `develop-gsd` and the property the strict policy buys does not
  arise there.

---

## Superseded decision

An earlier decision on this project adopted only a minimal security floor from the shared
template family and deliberately deferred the rest of the flow mechanics to a later pass. That
deferral no longer holds: the template this repository assembled from has since been redesigned to
remove the exact mechanics the earlier decision was worried about (an indirect release trigger, a
duplicated post-merge test run). With that redesign in hand, the full template is adopted here
in one pass rather than the floor-only subset, and the earlier partial-adoption decision is
superseded by this record.

---

## Apply-time checklist

Twelve items, each run against the assembled tree with its evidence recorded below — not a
checkmark. A checklist that is merely skimmed and reported "all clear" produces the appearance of
having checked without anything actually checked; recording the command and its output is what
makes "checked" and "not checked" distinguishable to the next reader.

**1. Required checks and their producers.** Every context string the ruleset payloads require is
produced by a job whose `name:` matches it byte-for-byte.

```
$ grep -n 'name:' .github/workflows/ci.yml
91:    name: Lint (pre-commit)
197:    name: Tests (pytest)
279:    name: Docs (sphinx -W)
```

All three required-check strings above match these job names exactly.

**2. No job-level condition, no conditioned dependency.** None of the three required-check jobs
(`lint`, `tests`, `docs`) carries a job-level `if:`, and none `needs:` another job.

```
$ grep -n '^  [a-z]*:$\|needs:' .github/workflows/ci.yml
90:  lint:
196:  tests:
278:  docs:
```

No `needs:` line appears anywhere in the file; no job-level `if:` sits on any of the three job
bodies (the only `if:` conditions in the file are on individual steps, gated by the
release-artifact fast path, never on a job itself).

**3. Context strings sourced from the job `name:` field.** All three context strings above were
read from the `name:` key of each job body in `.github/workflows/ci.yml`, not inferred, not read
from a workflow's own top-level `name:`, and not read from any job key. No matrix is present, so
no matrix-value suffix applies.

**4. No `pull_request_target` trigger anywhere.**

```
$ grep -rn pull_request_target .github/workflows/
(no output)
```

Empty, as required — nothing in this assembly runs the base branch's workflow against a fork's
head content with this repository's credentials.

**5. Trigger block of the CI workflow carries no filter key under the pull-request trigger.**

```
on:
  pull_request:
  push:
    branches: [develop-gsd]
  schedule:
    - cron: '0 5 * * *'
```

`pull_request:` carries no `paths:`, `paths-ignore:` or `branches:` filter, so every pull request
produces all three required contexts regardless of which files it touches. `push:` is scoped to
`develop-gsd` only, which is an intentional narrowing of when the workflow runs at all (not a
per-job condition on a required context) and is recorded here as the reason: nightly and
pull-request triggers already cover `main`, and a push-to-`main` trigger is unnecessary alongside
the release automation, which fires from a push to `main` directly.

**6. Every `bash -c` payload is apostrophe-free inside its body.**

```
$ grep -rn "bash -c" .github/
(no output)
```

No `bash -c '<body>'` construction appears anywhere in this assembly's shell steps.

**7. Multi-command `run:` steps use `&&` chains or explicit exit-status checks.** Every workflow
in this assembly runs under the platform's own `bash --noprofile --norc -eo pipefail` shell, so
plain sequential commands already abort the step on the first failure without needing an explicit
`&&` chain — this is recorded rather than assumed, because it is exactly the kind of thing a
future edit could quietly break by wrapping a command in a context that suppresses it. Two
representative shapes, both correct under that contract:
  - `.github/workflows/ci.yml`, job `docs`: three sequential top-level commands (dependency sync,
    a Python version-derivation check, the documentation build) rely on the shell's own default
    exit-on-error; none is wrapped in a construct that would suppress it.
  - `.github/workflows/ruleset-apply.yml`: every command whose result a later step depends on is
    wrapped in an explicit `if ! <command>; then echo "::error::..."; exit 1; fi` — the one shape
    in this assembly where the default exit-on-error is deliberately suppressed (inside the `if`
    condition), and each such wrapping carries its own named failure message rather than falling
    through silently.

**8. The lint job's effective permissions block grants no write scope.**

```
$ grep -n 'permissions:' -A2 .github/workflows/ci.yml | head -4
94:    permissions:
95-      contents: read
96-      pull-requests: read   # the classify step below reads the pull request's file list
```

Both grants are read-only. This job executes hooks defined by the repository's own configuration,
which on a fork-originated pull request is contributor-controlled content, so it holds nothing it
could use to write back to the repository.

**9. Every third-party action is pinned to a full commit SHA.**

```
$ grep -rn 'uses:' .github/
```

(every match shown below, one per third-party action reference, local composite/action references
of the form `uses: ./...` excluded since they name a path in this repository, not a third party):

```
$ grep -rhoE 'uses: [^ ]+@[^ ]+' .github/ | grep -v 'uses: \./' | grep -vcE '@[0-9a-f]{40}$'
0
```

Zero lines fail the forty-character-hex check — every third-party `uses:` reference across this
assembly (checkout, the App-token minter, artifact upload/download, the type checker, the coverage
uploader, the release automation action and the PyPI publish action) is pinned to a commit SHA,
never a mutable tag or branch name.

**10. Protection configuration carries all five floor rules per payload, and linear history on
`main` only.**

`main` (`.github/rulesets/main.json`): `"bypass_actors": []`; `{"type": "pull_request", ...
"required_approving_review_count": 0}`; `{"type": "required_status_checks", ...}`; `{"type":
"non_fast_forward"}`; `{"type": "deletion"}`; and, present on `main` only, `{"type":
"required_linear_history"}`.

`develop-gsd` (`.github/rulesets/develop.json`): the same `"bypass_actors": []` and the same four
rule types (`pull_request`, `required_status_checks`, `non_fast_forward`, `deletion`); no
`required_linear_history` entry.

**11. Same-commit constraint on renaming or decomposing a required check.**
Evidence: not applicable — first assembly. No check has ever been renamed or decomposed on this repository,
because this is the first time any of these checks or any ruleset payload naming them has
existed. The constraint itself — a rename and the ruleset payload update must land in the same
commit — is recorded above under "Required status checks" for the next time a check name
changes.

**12. No placeholder token survived parameterisation, across the whole assembled tree.**

```
$ grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json
(no output)
```

Empty, scoped to the whole `.github/` tree plus the two repository-root release configuration
files the release component ships outside `.github/` — not `.github/` alone, since a
root-shipping component's placeholders would sit outside a narrower scope.

---

## Verification

To confirm the live protection state matches what is committed here:

```bash
gh api repos/gseg-ethz/pc2img/rulesets
```

Expected: an array containing two ruleset objects, `"name": "protect-main"` and `"name":
"protect-develop-gsd"`, both `"enforcement": "active"`, both with an empty `"bypass_actors"`
array present (not absent — an absent key tells you nothing, only an empty array tells you the
list really is empty).

To compare a specific live ruleset against its committed payload directly rather than by eye:

```bash
python .github/scripts/check_ruleset_drift.py \
  "protect-main:<(gh api repos/gseg-ethz/pc2img/rulesets/<id>?includes_parents=false):.github/rulesets/main.json"
```

replacing `<id>` with the ruleset id from the listing above, and the equivalent invocation with
`protect-develop-gsd` / `.github/rulesets/develop.json` for the other branch.

---

## Deferred

- **Tag protection.** No ruleset on the moving version tags the release automation pushes.
  Branch rulesets do not cover tag refs at all; adding one would need a bypass actor so the
  release automation can still move those tags, and that is future work, not a gap in what this
  record claims to protect today.
- **Tighter review policy.** Moving from zero required approvals to one, once a second routine
  reviewer is regularly available, is the clean next step referenced under "Approval policy"
  above.

---

## Pre-promotion gate (recorded once)

Recorded once, run in one pass against the tree that already carries every wave-1 and wave-2
plan's changes, immediately before the first filtered promotion to `main`. Every command below
exited zero.

**Full test suite with the coverage floor:**

```
$ uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing --cov-fail-under=55 -q
...
Required test coverage of 55% reached. Total coverage: 62.27%
278 passed, 17 warnings in 4.67s
```

**Whole-tree pre-commit:**

```
$ uv run --frozen pre-commit run --all-files
ruff check...............................................................Passed
ruff format..............................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check toml...............................................................Passed
check for added large files..............................................Passed
```

**Documentation build, warnings as errors:**

```
$ uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html
...
build succeeded.

The HTML pages are in docs/_build/html.
```

No `WARNING:` or `ERROR:` line appeared anywhere in the build output.

**Placeholder grep, whole tree:**

```
$ grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json
(no output — no placeholder survived parameterisation)
```

**Planning-vocabulary gate:**

```
$ uv run --frozen pytest tests/test_hygiene.py -q -k planning_vocabulary
81 passed, 5 deselected, 12 warnings in 0.13s
```

**Migration record verifier:**

```
$ mkdir -p _scrap && awk '/^## Verifier \(inline\)$/,/^```$/' .planning/MIGRATION-v0.11.md | sed -n '/^```python$/,/^```$/p' | sed '1d;$d' > _scrap/pc2img-migration-verifier.py && uv run --frozen python _scrap/pc2img-migration-verifier.py
[ok] verified 25 entries
```

**Lockfile freshness:**

```
$ uv lock --check
Resolved 193 packages in 5ms
```

**Build and package check:**

```
$ rm -rf dist && uv build
Successfully built dist/pc2img-...tar.gz
Successfully built dist/pc2img-...-py3-none-any.whl

$ uvx twine check dist/*
Checking dist/pc2img-....whl: PASSED
Checking dist/pc2img-....tar.gz: PASSED
```

**Working tree clean apart from the files this task edited:** confirmed with `git status
--porcelain` — the only tracked-repository change from this record's own edits is to this file;
every other entry shown by that command belongs to pre-existing, untracked local state outside
this record's scope.

**Signed IP-clearance record untouched:** `git log --oneline origin/develop-gsd..HEAD --
docs/ip/rrim-eth-signoff.md` printed nothing — no commit in this work touched that file.

---

## Release process — full record

The condensed public `RELEASE.md` keeps only the tables and section headings later plans read
back. The paragraphs it drops are preserved here in full.

**Why a bot-opened pull request needs an App token at all:** an event triggered by the default,
repository-scoped workflow token creates no further workflow runs. A release pull request opened
with that default token would never receive any of its required checks and would sit unmergeable
forever under an empty bypass list. An App-minted installation token does not have this
restriction, which is the entire reason the release automation authenticates as an App rather than
relying on the ambient token every workflow already has.

**Full version-policy paragraph:** This repository stays on the `0.x` line for its first PyPI
release and for the foreseeable releases after it. The release-please configuration carries
`bump-minor-pre-major: true` together with `bump-patch-for-minor-pre-major: true`, which together
mean: while the version is below `1.0.0`, a commit marked as a breaking change bumps the **minor**
version, and an ordinary feature commit bumps only the **patch** version. A feature-only release
that should bump the minor version instead needs an explicit `Release-As:` footer in the commit
that triggers it — without one, a plain feature commit on the `0.x` line never reaches the next
minor number on its own.

**The first promotion to the release branch** carries a `feat!:` subject, a `BREAKING CHANGE:`
footer, and a `Release-As: 0.11.0` footer as a backstop — the breaking-change bump alone would
already land on a `0.x` minor bump, and the explicit `Release-As` pins the exact number rather
than leaving it to be derived. **Per D-33a**, the `BREAKING CHANGE:` footer carries a short,
self-contained public summary of the breaking changes rather than a pointer at
`MIGRATION-v0.11.md` — that file does not exist on `main` (D-33), so a pointer at it would dangle
in the published `CHANGELOG.md`.

The release pull request release-please opens against the promoted tree stays open until the
actual publish is wanted. **Merging that pull request is the real PyPI publish** — nothing else in
this flow uploads to the production index automatically.

**Dry run (test index), three steps:**

1. From the repository's Actions tab, dispatch `Publish to TestPyPI` (`publish-testpypi.yml`) from
   the release branch.
2. Once the run completes, visit `https://test.pypi.org/project/pc2img/` and confirm the version
   just built is listed.
3. Confirm the attestation was produced by checking the integrity endpoint for that exact file (the
   same URL shape works against the test index host as the production "Verifying a release"
   section in `RELEASE.md`).

---

## Review-round changes (2026-09-29)

Fix-now findings from the mid-phase code review (`06-REVIEW.md`, owner disposition D-35), one
bullet per finding naming the file(s) touched and the gap plan that closed it:

- **CR-01** (floating vX/vX.Y release tags break the source archive) — `.git_archival.txt`,
  `tests/test_git_archival.py` — closed in plan **06-14**.
- **WR-05** (publish workflows could run from any ref; owner-elevated to fix-now) —
  `.github/workflows/publish-testpypi.yml`, `.github/workflows/publish-pypi.yml`,
  `.github/scripts/test_publish_ref_guard.py` — closed in plan **06-14**.
- **WR-08** (placeholder DOI in `CITATION.cff`) — `CITATION.cff` — closed in plan **06-14**.
- **WR-10** (ancestry alarm fires after every promotion; documented procedure only back-merged
  after releases, on a false rationale) — `RULESETS.md` (this record's "Interview answers"
  consequences paragraph, corrected above) — closed in plan **06-15**.
- **IN-05** (`RULESETS.md` stated the rulesets already exist) — `RULESETS.md` (this record's
  "Initial ruleset creation" deviation, reworded above) — closed in plan **06-15**.
- **IN-10, README/index half** (`README.rst` named two projections; `docs/source/index.rst` and
  the registry name three) — `README.rst` — closed in plan **06-15**. The `CONTRIBUTING.md`
  baseline-count half of IN-10 is not this plan's scope.
- **WR-03** (new `project_raw` docstring documented a contract no implementation follows) —
  `src/pc2img/strategies/projection.py`, `tests/test_projection.py` — closed in plan **06-16**.
- **WR-04** (file-wide hygiene exemption for `.pre-commit-config.yaml` was unnecessary and falsely
  justified) — `tests/test_hygiene.py` — closed in plan **06-16**.
- **IN-04** (comments/docstrings referenced declined kit components as if they existed) —
  `.github/workflows/ci.yml`, `.github/actions/classify-changes/action.yml`,
  `.github/scripts/check_ruleset_drift.py`, `.github/scripts/ruleset_lib.py` — closed in plan
  **06-16**.
- **IN-13** (planning vocabulary in shipped prose the gate's regexes could not see) —
  `tests/test_hygiene.py`, `.github/workflows/ruleset-apply.yml` — closed in plan **06-16**.

**D-33 and D-34** (this plan, 06-15): the draft migration record moved from the repository root to
`.planning/MIGRATION-v0.11.md` (git rename, history preserved; verifier re-pointed and re-run
green); the full CI/CD adoption record (this file) was created by copying the pre-condensation
`RULESETS.md` and correcting it in place, then `RULESETS.md` and `RELEASE.md` were condensed to
maintainer scope at the public root.

**Deferred to Phase 7** (owner disposition, D-35 — not fix-now): WR-01, WR-02, WR-06, WR-07,
WR-09, and the remaining Info-severity findings (IN-01, IN-02, IN-03, IN-06, IN-07, IN-08, IN-09,
IN-11, IN-12, and the `CONTRIBUTING.md` baseline-count half of IN-10). Each carries its own
`status: deferred` entry in `06-UAT.md`.

---

## Cross-repository notes (owner approval required)

Recorded here, not acted on — editing a sibling repository needs explicit owner approval.

- **Floating release tags (CR-01).** `release-please.yml`'s "Tag major and minor versions" step is
  shared GSEG-kit code. PCHandler and GSEGUtils very likely carry the identical step and therefore
  the same archive-unbuildable defect once either cuts a release with more than one tag on the
  commit. pc2img's own `origin/v0.10.4` already has `v0`/`v0.10` on its commit and that archive
  stays unbuildable — a pushed tag's archive cannot be corrected retroactively. (Source:
  `06-14-SUMMARY.md`, "Cross-Repository Notes".)
- **Placeholder DOI (WR-08).** `/scratch/41_pchandler/CITATION.cff` and
  `/scratch/30_GSEGUtils/CITATION.cff` both still carry the identical
  `doi: 10.5281/zenodo.XXXXXXX` placeholder and `preferred-citation` block this plan's 06-14 gap
  removed from pc2img's own copy. Neither sibling file was edited. (Source: `06-14-SUMMARY.md`,
  "Cross-Repository Notes".)

---

## Gate re-runs

Plan 06-17 records the re-run of the full pre-promotion gate after this review round's fixes
(plans 06-14, 06-15, 06-16) land, ahead of the first promotion to `main`.

### 2026-09-29 — after the round-2 doc pass

Run in one pass from the repository root, against the tree that carries plan 06-19's round-2
fix-now closures (RELEASE.md and RULESETS.md rewritten to the owner's target texts, the seven
pointer comments deleted, ci.yml's header/log-line made self-contained, the ruleset-apply.yml
token-mint comment scoped, the citation message and one test header corrected). HEAD `e2a3f5a`.
Every command below exited zero.

**Publish containment gate:**

```
$ uv run --frozen python .github/scripts/check_publish_gate.py
check_publish_gate: OK — publish steps found only in allowed files + environments
```

**Kit script tests:**

```
$ uv run --frozen pytest .github/scripts -q
92 passed in 1.28s
```

**Hygiene gate:**

```
$ uv run --frozen pytest tests/test_hygiene.py -q
88 passed, 12 warnings in 0.19s
```

**Projection tests:**

```
$ uv run --frozen pytest tests/test_projection.py -q
27 passed, 12 warnings in 0.06s
```

**Whole-tree pre-commit:**

```
$ uv run --frozen pre-commit run --all-files
ruff check...............................................................Passed
ruff format..............................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check toml...............................................................Passed
check for added large files..............................................Passed
```

**CFF validation:**

```
$ uv run --frozen cffconvert --validate
Citation metadata are valid according to schema version 1.2.0.
```

**RULESETS.md table derived from the committed payloads (Task 2):**

```
$ uv run --frozen python - <<'PY'
... (table-cell derivation against .github/rulesets/main.json and develop.json, and the
     check names against .github/workflows/ci.yml's job name: fields)
PY
rulesets-table-matches-payloads
```

**YAML identity against `e929894` (five files, comments the only permitted diff):**

```
yaml-same .github/workflows/publish-pypi.yml
yaml-same .github/workflows/publish-testpypi.yml
yaml-same .github/workflows/ruleset-apply.yml
yaml-same .github/workflows/scheduled-health.yml
yaml-same .github/actions/classify-changes/action.yml
```

**YAML identity against `e929894`, ci.yml (single run-block log-line string excluded):**

```
yaml-same-except-logline .github/workflows/ci.yml
```

**AST identity against `e929894` (docstrings stripped):**

```
ast-same .github/scripts/check_publish_gate.py
ast-same .github/scripts/check_ruleset_drift.py
ast-same .github/scripts/ruleset_lib.py
ast-same tests/test_projection.py
```

**Added-lines vocabulary/review-identifier scan** (every `+` line of `git diff e929894 -- .
':!.planning'` run through `tests/test_hygiene.py`'s own matcher plus a review-identifier regex):

```
vocabulary hits: [] review ids: []
```

**Files changed by the round-2 doc pass (the round-3 review scope):**

`git diff --name-only e929894..HEAD -- . ':!.planning'` — thirteen paths:

```
.github/actions/classify-changes/action.yml
.github/scripts/check_publish_gate.py
.github/scripts/check_ruleset_drift.py
.github/scripts/ruleset_lib.py
.github/workflows/ci.yml
.github/workflows/publish-pypi.yml
.github/workflows/publish-testpypi.yml
.github/workflows/ruleset-apply.yml
.github/workflows/scheduled-health.yml
CITATION.cff
RELEASE.md
RULESETS.md
tests/test_projection.py
```

This list is the scope handed to `/gsd-code-review 06 --files <list>` at plan 06-19's Task 4
checkpoint (round 3 of 3, the round cap) and to plan 06-18 Task 1's precondition.

### 2026-09-29 — after the review-round fixes

Run in one pass from the repository root, against the tree that carries every review-round fix
(plans 06-14, 06-15, 06-16; HEAD `cf2fe47`). Every command below exited zero.

**Full test suite with the coverage floor:**

```
$ uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing --cov-fail-under=55 -q
...
Required test coverage of 55% reached. Total coverage: 62.27%
286 passed, 17 warnings in 6.06s
```

**Whole-tree pre-commit:**

```
$ uv run --frozen pre-commit run --all-files
ruff check...............................................................Passed
ruff format..............................................................Passed
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
check toml...............................................................Passed
check for added large files..............................................Passed
```

**Documentation build, warnings as errors (rebuilt clean, `rm -rf docs/_build` first):**

```
$ uv sync --frozen --group doc && uv run --frozen sphinx-build -W --keep-going -b html docs/source docs/_build/html
...
build succeeded.

The HTML pages are in docs/_build/html.
```

No `WARNING:` or `ERROR:` line appeared anywhere in the build output.

**Placeholder grep, whole tree:**

```
$ grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json
(no output — no placeholder survived parameterisation)
```

**Planning-vocabulary gate (extended, IN-13/IN-04 patterns included):**

```
$ uv run --frozen pytest tests/test_hygiene.py -q -k planning_vocabulary
82 passed, 6 deselected, 12 warnings in 0.26s
```

**Kit script tests:**

```
$ uv run --frozen pytest .github/scripts -q
92 passed in 1.66s
```

**Publish containment gate:**

```
$ uv run --frozen python .github/scripts/check_publish_gate.py
check_publish_gate: OK — publish steps found only in allowed files + environments
```

**Migration record verifier:**

```
$ mkdir -p _scrap && awk '/^## Verifier \(inline\)$/,/^```$/' .planning/MIGRATION-v0.11.md | sed -n '/^```python$/,/^```$/p' | sed '1d;$d' > _scrap/pc2img-migration-verifier.py && uv run --frozen python _scrap/pc2img-migration-verifier.py
[ok] verified 25 entries
```

**Lockfile freshness:**

```
$ uv lock --check
Resolved 193 packages in 2ms
```

**Build and package check:**

```
$ rm -rf dist && uv build
Successfully built dist/pc2img-0.10.4.post429.tar.gz
Successfully built dist/pc2img-0.10.4.post429-py3-none-any.whl

$ uvx twine check dist/*
Checking dist/pc2img-0.10.4.post429-py3-none-any.whl: PASSED
Checking dist/pc2img-0.10.4.post429.tar.gz: PASSED
```

**Files changed since the phase PR merge (the round-2 review scope):**

`git diff --name-only 6c10ee0..HEAD -- . ':!.planning'` — 21 paths:

```
.git_archival.txt
.github/actions/classify-changes/action.yml
.github/scripts/check_publish_gate.py
.github/scripts/check_ruleset_drift.py
.github/scripts/ruleset_lib.py
.github/scripts/test_publish_ref_guard.py
.github/workflows/ci.yml
.github/workflows/publish-pypi.yml
.github/workflows/publish-testpypi.yml
.github/workflows/ruleset-apply.yml
.github/workflows/scheduled-health.yml
.pre-commit-config.yaml
CITATION.cff
MIGRATION-v0.11.md
README.rst
RELEASE.md
RULESETS.md
src/pc2img/strategies/projection.py
tests/test_git_archival.py
tests/test_hygiene.py
tests/test_projection.py
```

`MIGRATION-v0.11.md` appears as a deletion — the 06-15 rename moved the draft under
`.planning/` (D-33), so its removal from the public root is a real change to the shipped tree
even though the pathspec above excludes `.planning/` itself. This list is the scope handed to
both round-2 review commands in Task 2 (`/gsd-code-review 06 --files <list>` and
`/code-review origin/develop-gsd high`).
