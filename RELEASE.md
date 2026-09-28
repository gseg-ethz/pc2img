# Release Process — pc2img

**Repository:** gseg-ethz/pc2img
**Publish workflow:** `.github/workflows/publish-pypi.yml`
**First PyPI release planned:** `0.11.0`, on the `0.x` line. The project name is currently unclaimed
on both the production index and the test index.

---

## Trusted Publisher Binding

This package publishes to PyPI (and, for a rehearsal, to the test index) via OIDC trusted
publishing — no long-lived API token is stored in either workflow's secrets. The GitHub Actions
runner receives a short-lived OIDC token from GitHub's own token endpoint, and the index validates
that token against the registered trusted publisher record before accepting an upload.

### Production claim

| Field | Value |
|---|---|
| Owner (GitHub) | gseg-ethz |
| Repository | pc2img |
| Workflow filename | publish-pypi.yml |
| Environment name | pypi |

### Dry-run claim (test index)

| Field | Value |
|---|---|
| Owner (GitHub) | gseg-ethz |
| Repository | pc2img |
| Workflow filename | publish-testpypi.yml |
| Environment name | testpypi |
| Upload endpoint | https://test.pypi.org/legacy/ |

Every field in both tables is an exact-match claim — the index rejects an upload if any field
differs by even a single character, case included. The two claims are entirely separate records on
two separate indexes; the workflow filename and environment name are what keep them from ever being
satisfied by each other's runs.

---

## What NOT to Rename

Renaming any of the following breaks its trusted-publisher claim and requires deleting and
re-creating the publisher record on the affected index:

- **Repository name** (`pc2img` on GitHub).
- **Either workflow filename** (`publish-pypi.yml`, `publish-testpypi.yml`).
- **Either GitHub Environment name** (`pypi`, `testpypi`).

The PyPI *project* name (`pc2img`) is also immutable once the first version is published to it.

---

## Credentials

Two entirely separate GitHub Apps hold the write-capable credentials this repository's automation
needs, and they are never the same pair:

- **Release automation** (opening the release pull request, tagging, pushing the changelog and
  version bump) authenticates as the `gseg-release-please` App, using the secrets
  `RELEASE_APP_ID` and `RELEASE_APP_PRIVATE_KEY`.
- **Branch protection** (applying the committed ruleset payloads) authenticates as the
  `gseg-ruleset-admin` App, using the secrets `RULESET_APP_ID` and `RULESET_APP_PRIVATE_KEY`.

Keeping them separate limits the blast radius of either credential being compromised: a leaked
release-automation token can open pull requests and push tags, but it cannot rewrite branch
protection, and the reverse holds for the ruleset-admin token.

**Why a bot-opened pull request needs an App token at all:** an event triggered by the default,
repository-scoped workflow token creates no further workflow runs. A release pull request opened
with that default token would never receive any of its required checks and would sit unmergeable
forever under an empty bypass list. An App-minted installation token does not have this
restriction, which is the entire reason the release automation authenticates as an App rather than
relying on the ambient token every workflow already has.

---

## Version policy

This repository stays on the `0.x` line for its first PyPI release and for the foreseeable
releases after it. The release-please configuration carries `bump-minor-pre-major: true` together
with `bump-patch-for-minor-pre-major: true`, which together mean: while the version is below
`1.0.0`, a commit marked as a breaking change bumps the **minor** version, and an ordinary feature
commit bumps only the **patch** version. A feature-only release that should bump the minor version
instead needs an explicit `Release-As:` footer in the commit that triggers it — without one, a
plain feature commit on the `0.x` line never reaches the next minor number on its own.

**The first promotion to the release branch** carries a `feat!:` subject, a `BREAKING CHANGE:`
footer pointing readers at `MIGRATION-v0.11.md`, and a `Release-As: 0.11.0` footer as a backstop —
the breaking-change bump alone would already land on a `0.x` minor bump, and the explicit
`Release-As` pins the exact number rather than leaving it to be derived.

The release pull request release-please opens against the promoted tree stays open until the
actual publish is wanted. **Merging that pull request is the real PyPI publish** — nothing else in
this flow uploads to the production index automatically.

---

## Dry run (test index)

The test-index dry run is dispatched by hand, deliberately never as an automatic consequence of
anything:

1. From the repository's Actions tab, dispatch `Publish to TestPyPI` (`publish-testpypi.yml`) from
   the release branch.
2. Once the run completes, visit `https://test.pypi.org/project/pc2img/` and confirm the version
   just built is listed.
3. Confirm the attestation was produced by checking the integrity endpoint for that exact file (see
   "Verifying a release" below — the same URL shape works against the test index host).

---

## Rollback

Neither index allows deleting or replacing an already-uploaded version — once a version number is
uploaded, that number is permanently unavailable for the project again on that index.

To deprecate a broken release on the production index:

1. Navigate to the project's release management page on PyPI.
2. Select the broken version.
3. Click **Yank release**.

A yanked version is hidden from ordinary install resolution (a plain `pip install pc2img` skips
yanked versions) but stays downloadable by anyone who pins the exact version number. Yanking is
reversible; deleting a version outright is not possible.

---

## Verifying a release

Every wheel and sdist this workflow publishes carries a build-provenance attestation, produced
automatically by the publish action during the job. Confirm one exists for a given file at:

```
https://pypi.org/integrity/pc2img/<version>/<filename>/provenance
```

substituting the released version and the exact artifact filename (wheel or sdist) you want to
verify.
