# Release process — pc2img

## Trusted publishing

Both publish workflows use OIDC trusted publishing; no API token is stored.
Owner `gseg-ethz`, repository `pc2img`:

| Index    | Workflow file          | Environment |
|----------|------------------------|-------------|
| PyPI     | `publish-pypi.yml`     | `pypi`      |
| TestPyPI | `publish-testpypi.yml` | `testpypi`  |

**Do not rename** the repository, either workflow file or either environment —
each is part of the publisher claim on the index. The PyPI project name is
permanent once published.

## Credentials

- Release automation: GitHub App `gseg-release-please`
  (`RELEASE_APP_ID`, `RELEASE_APP_PRIVATE_KEY`).
- Ruleset changes: GitHub App `gseg-ruleset-admin`
  (`RULESET_APP_ID`, `RULESET_APP_PRIVATE_KEY`).

## Versions

On `0.x`: a breaking change bumps the minor version, a feature the patch.
Force a minor bump with a `Release-As:` footer.

## Releasing

1. Promote `develop-gsd` to `main` (squashed, internal directories stripped).
2. Merge `main` back into `develop-gsd` with "Create a merge commit" — never
   squash or rebase. A nightly check opens an issue if this is missed.
3. release-please opens a release pull request on `main`.
   **Merging it publishes to PyPI.**
4. Back-merge again (step 2) after the release pull request merges.

## Ref guards

The publish workflows refuse the wrong ref: TestPyPI only from `main`, PyPI only
from an `X.Y.Z` tag on `main`. These guards protect only a run started from a commit that carries them — older commits hold unguarded copies.
**Only ever create a release whose tag is on `main`.**
No environment rule or package-content check backs this up.

## Dry run

Actions → dispatch "Publish to TestPyPI" from `main`, then check
<https://test.pypi.org/project/pc2img/>.

## Rollback

An uploaded file cannot be replaced, and its filename and version can never be
reused — not even after deletion. Prefer **Yank release** on the PyPI project
page: hidden from normal installs, still installable by exact pin, reversible.

## Verifying a release

Every wheel and sdist carries a provenance attestation:
`https://pypi.org/integrity/pc2img/<version>/<filename>/provenance`
