# Branch Rulesets — pc2img

**Repository:** gseg-ethz/pc2img
**Protected branches:** `main`, `develop-gsd`
**Ruleset names:** `protect-main`, `protect-develop-gsd`
**Ruleset snapshots:** `.github/rulesets/main.json`, `.github/rulesets/develop.json`
**Applied via:** `.github/workflows/ruleset-apply.yml`, dispatch-only from `main`.

---

## Bypass list

**The bypass list is empty on both rulesets.**

No actor — not the release automation, not repository administrators — appears on either bypass
list. Nobody can merge a change whose required checks are red, and nobody can force-push or
delete a protected branch by routing around the ruleset.

The release bot needs no bypass entry: it only ever pushes to its own scratch branch when it
opens a release pull request, which is not one of the protected refs, and it moves major/minor
tags on release, which branch rulesets do not cover at all.

---

## Approval policy

**Pull request required; `required_approving_review_count = 0`.**

Direct pushes to `main` or `develop-gsd` are blocked — every change must arrive through a pull
request with its required checks passing. The approval count is deliberately zero: this
repository is maintained by a single owner working with CI, and GitHub forbids self-approval, so
any nonzero approval requirement combined with the empty bypass list above would deadlock every
solo-authored pull request — nobody could approve it, and nothing could bypass the block. Zero
approvals keeps the required status checks as the sole hard gate while avoiding that deadlock.

`dismiss_stale_reviews_on_push`, `require_code_owner_review`, `require_last_push_approval`, and
`required_review_thread_resolution` are all off.

**Future tightening:** moving to a nonzero approval count, once a second routine reviewer
exists, is the clean next step.

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

`strict_required_status_checks_policy` is `true` on `main` and `false` on `develop-gsd` — this
asymmetry is deliberate, not an oversight.

---

## Other rules

| Rule | On | Effect |
|---|---|---|
| `non_fast_forward` | main, develop-gsd | Force-pushes to the protected branch are blocked |
| `deletion` | main, develop-gsd | The protected branch cannot be deleted |
| `required_linear_history` | main only | Merge commits are blocked on `main`; kept OFF on `develop-gsd`, because the back-merge below lands as a true merge commit and a linear-history rule there would refuse it outright |

---

## Promotion and back-merge

`main` is a filtered projection: each promotion squashes `develop-gsd` with its internal-only
directories stripped, so every promotion creates a `main` commit that `develop-gsd` lacks. A
nightly ancestry assertion checks that `main` is an ancestor of `develop-gsd` and opens an issue
when it is not.

**Therefore: after every promotion to `main`, and after every merge of a release pull request,
merge `main` back into `develop-gsd` using "Create a merge commit" — never squash or rebase.**
Either of those would silently collapse the second parent and break the ancestry the nightly
assertion watches. The first such back-merge, immediately after the first promotion, is the
ancestry graft: the branches share the common ancestor `f946268`, but `main` carries commits
(`69224a9`, `ade40f8`) that `develop-gsd` lacks, and each squash promotion after that adds one
more.

---

## Applying the rulesets

Dispatch `ruleset-apply.yml` from `main` with the committed payload. It preflights against the
target branch's workflow files, mints the ruleset App token, updates the named ruleset, and reads
it back through `check_ruleset_drift.py`. It has no create path: when the repository has no
ruleset of that name yet, the first creation posts the preflight-produced payload once directly
through the API, and every later change goes through this workflow exclusively. Never edit a
ruleset in the web interface.

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

## Recorded deviations

- The setup composite installs with `uv sync --frozen` against the committed lockfile, because
  the dev tooling is a dependency group rather than an extra.
- The docs job installs the `doc` dependency group with `uv` the same way.
- The test command keeps `--cov-branch --cov-fail-under=55`.
- The test and docs jobs check out full history, because the build backend derives the package
  version from git tags.
- The dry-run publish requests attestations, to exercise the full attestation path once before
  the real index is ever touched.

---

## Deferred

- **Tag protection.** No ruleset covers the moving version tags the release automation pushes.
- **Tighter review policy.** Moving from zero required approvals to one, once a second routine
  reviewer is regularly available.
