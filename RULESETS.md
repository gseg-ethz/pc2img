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
- **Changing a rule:** edit `.github/rulesets/main.json` or `develop.json`, then
  run the `ruleset-apply` workflow from `main`. Never edit rulesets in the web UI.
- **Inspect a live ruleset:** `gh api repos/gseg-ethz/pc2img/rulesets/<id>`
  (the list endpoint omits the bypass list).
