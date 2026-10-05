# Branch rules — pc2img

Protected branches: `main` (released code) and `develop-gsd` (integration).
Open pull requests against `develop-gsd`.

## What a pull request needs

| Requirement                          | develop-gsd | main |
|--------------------------------------|:-----------:|:----:|
| Arrives as a pull request            | ✓ | ✓ |
| Lint (pre-commit) passes             | ✓ | ✓ |
| Tests (pytest) passes                | ✓ | ✓ |
| Docs (sphinx -W) passes              | – | ✓ |
| Branch up to date with target        | – | ✓ |
| Linear history (no merge commits)    | – | ✓ |
| Required approvals                   | 0 | 0 |

No force-pushes, no branch deletion, and no bypass for anyone, admins included.
Run the same checks locally: see CONTRIBUTING.md.

## For maintainers

- **Renaming a CI job blocks all merges.** The check names above are the job
  `name:` fields in `.github/workflows/ci.yml`; update `.github/rulesets/*.json`
  in the same commit.
- **Changing a rule:** edit `.github/rulesets/main.json` or `develop.json` and
  get the change onto `main` (the workflow reads payloads from `main` only),
  then run the `ruleset-apply` workflow from `main`. It updates an existing
  ruleset only; creating one is a single `gh api --method POST
  repos/gseg-ethz/pc2img/rulesets --input <payload>`. Never edit rulesets in
  the web UI.
- **Five fields are not governed by the apply:** `allowed_merge_methods`,
  `dismissal_restriction`, `required_reviewers`,
  `require_extra_approval_for_unattributed_changes` and `do_not_enforce_on_create`.
  GitHub fills them on read; the drift check ignores them unless a payload sets one.
- **Inspect a live ruleset:** `gh api repos/gseg-ethz/pc2img/rulesets/<id>`
  with a token that has repository administration access. Without one, the
  bypass-actor list is missing from the response entirely; only an explicit
  empty array (`[]`) confirms there really is no bypass. The list endpoint
  never returns it at all.
