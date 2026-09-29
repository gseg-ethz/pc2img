# Release Process — pc2img

**Repository:** gseg-ethz/pc2img
**Publish workflow:** `.github/workflows/publish-pypi.yml`
**First PyPI release planned:** `0.11.0`, on the `0.x` line. The project name is currently
unclaimed on both the production index and the test index.

## Trusted Publisher Binding

This package publishes to PyPI (and, for a rehearsal, the test index) via OIDC trusted
publishing — no long-lived API token in either workflow's secrets; the index validates a
short-lived runner-minted token against the registered trusted publisher record.

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

Every field is an exact-match claim, case included; the workflow filename and environment name
keep the two claims from ever being satisfied by each other's runs.

## What NOT to Rename

Renaming any of these breaks its trusted-publisher claim and requires deleting and re-creating
the publisher record on the affected index: the **repository name** (`pc2img`), **either
workflow filename** (`publish-pypi.yml`, `publish-testpypi.yml`), or **either Environment name**
(`pypi`, `testpypi`). The PyPI *project* name (`pc2img`) is also immutable once published.

## Credentials

Two separate GitHub Apps hold the write-capable credentials this repository's automation needs,
limiting the blast radius of either credential being compromised:

- **Release automation** authenticates as `gseg-release-please`, using `RELEASE_APP_ID` /
  `RELEASE_APP_PRIVATE_KEY`.
- **Branch protection** authenticates as `gseg-ruleset-admin`, using `RULESET_APP_ID` /
  `RULESET_APP_PRIVATE_KEY`.

## Version policy

This repository stays on the `0.x` line for its first release: while the version is below
`1.0.0`, a breaking-change commit bumps the **minor** version, an ordinary feature commit bumps
only the **patch** version, and a feature-only release that should bump minor needs an explicit
`Release-As:` footer.

**The first promotion to the release branch** carries a `feat!:` subject, a `BREAKING CHANGE:`
footer holding a short, self-contained summary of the breaking changes (which release-please
copies into `CHANGELOG.md`), and a `Release-As: 0.11.0` backstop footer.

The release pull request stays open until the publish is wanted. **Merging it is the real PyPI
publish** — nothing else in this flow uploads to the production index automatically.

## Ref guards

- The TestPyPI rehearsal refuses any dispatch whose ref is not `main`.
- The PyPI publish refuses any release whose ref is not an `X.Y.Z` version tag reachable from
  `main`.

Both fail before anything is built, since any other ref could still carry internal-only content.

## Dry run

Dispatched by hand, never automatically: from the Actions tab, dispatch `Publish to TestPyPI`
(`publish-testpypi.yml`) from the release branch; once it completes, visit
`https://test.pypi.org/project/pc2img/` and confirm the version is listed; then confirm the
attestation via the integrity endpoint (see "Verifying a release" below — the same URL shape
works against the test index host).

## Rollback

Neither index allows deleting or replacing an already-uploaded version. To deprecate a broken
release: on the project's release management page on PyPI, select the version and click **Yank
release**. A yanked version is hidden from ordinary install resolution but stays downloadable by
anyone who pins the exact version. Yanking is reversible; deleting outright is not possible.

## Verifying a release

Every wheel and sdist this workflow publishes carries a build-provenance attestation, produced
automatically by the publish action during the job. Confirm one exists for a given file at:

```
https://pypi.org/integrity/pc2img/<version>/<filename>/provenance
```

substituting the released version and the exact artifact filename (wheel or sdist) you want to
verify.
