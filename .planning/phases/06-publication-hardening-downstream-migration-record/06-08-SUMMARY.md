---
phase: 06-publication-hardening-downstream-migration-record
plan: 08
subsystem: infra
tags: [github-actions, ci-cd, pull-request, codecov, release-please, git-tags, github-apps]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "Assembled .github/ tree (CI, ruleset-apply, publish workflows), RULESETS.md/RELEASE.md records, pre-promotion gate (plans 06-01..06-07)"
provides:
  - "Clean version namespace: v2.0.0a5 retired to archive/v2.0.0a5 (origin), old name gone locally and remotely; setuptools_scm describes develop-gsd against the 0.10.4 line again"
  - "Stale release-please PR #6 closed, its scratch branch deleted"
  - "The two org GitHub Apps (codecov, gseg-ruleset-admin) granted access to pc2img; repo secrets RULESET_APP_ID, RULESET_APP_PRIVATE_KEY, CODECOV_TOKEN present"
  - "The assembled CI/CD workflows (ci.yml, ruleset-apply.yml, publish-*.yml) merged onto develop-gsd via PR #13, a two-parent merge commit (6c10ee0), behind three green required contexts and a real Codecov upload"
affects: ["06-09+ (ruleset-apply, the first live rulesets application, needs the workflows and RULESET_APP_* secrets landed here)"]

# Actuals (#2632)
actuals:
  tokens: 3200
  tasks: 3
  commits: 1
  plan_head_before: a607a3ef7002281c413e46945210608b08fd4358
  plan_head_after: a607a3ef7002281c413e46945210608b08fd4358

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Namespace-rename-before-delete for git tags: push the replacement ref, confirm it landed on origin, only then delete the old ref — the archive tag stayed fetchable throughout, and the old name was never absent from both places at once"
    - "Codecov posts via the GitHub Checks API (an app check-run, e.g. codecov/patch) rather than the legacy Commit Status API on this installation/action version combination — a verify command written against /commits/{sha}/status alone will read 0 results even when the upload succeeded; check both endpoints"

key-files:
  created: []
  modified: []

key-decisions:
  - "Task 3's <verify> automated command for the codecov proof queries the legacy /status (Commit Status API) endpoint, which returned zero entries even though the upload succeeded; the task's own <action> text sanctioned check-runs as an equally valid alternative proof, and repos/.../check-runs showed codecov/patch with conclusion=success on the same head commit — treated as satisfying the acceptance criterion via the plan's own stated alternative, not as a deviation requiring a plan edit."

patterns-established: []

requirements-completed: [CICD-02]

coverage:
  - id: D1
    description: "v2.0.0a5 retired to archive/v2.0.0a5 on origin (old name absent locally and remotely); setuptools_scm describe on origin/develop-gsd resolves against the v0.10.4 line again; release-please PR #6 closed and its branch deleted"
    requirement: CICD-02
    verification:
      - kind: other
        ref: "git ls-remote --tags origin refs/tags/archive/v2.0.0a5 (1 match at 0b1e94392ba0e436377a3a82b92e03ea2f2e3b5d); git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' origin/develop-gsd -> v0.10.4-368-ge9eb3c4; gh pr view 6 --json state -> CLOSED"
        status: pass
    human_judgment: false
  - id: D2
    description: "codecov and gseg-ruleset-admin Apps granted repository access to pc2img; RULESET_APP_ID, RULESET_APP_PRIVATE_KEY, CODECOV_TOKEN present as repo secrets"
    requirement: CICD-02
    verification:
      - kind: other
        ref: "gh secret list --repo gseg-ethz/pc2img --json name --jq '.[].name' -> CODECOV_TOKEN, RULESET_APP_ID, RULESET_APP_PRIVATE_KEY present (re-checked as this plan's Task 3 precondition, in addition to Task 2's own acceptance run)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Phase PR #13 opened gsd/phase-06-publication-hardening-downstream-migration-record -> develop-gsd, all three required contexts (Lint (pre-commit), Tests (pytest), Docs (sphinx -W)) SUCCESS, a real Codecov upload succeeded and posted a codecov/patch check-run on the head commit, and the PR was merged with a two-parent merge commit (6c10ee0) keeping the source branch"
    requirement: CICD-02
    verification:
      - kind: integration
        ref: "gh pr checks 13 --repo gseg-ethz/pc2img --watch (all three SUCCESS); GH Actions run 36445463863, Tests (pytest) job log 'Upload queued for processing complete' with results URL app.codecov.io/github/gseg-ethz/pc2img/commit/a607a3e; gh api repos/.../commits/a607a3e.../check-runs -> codecov/patch conclusion=success"
        status: pass
      - kind: other
        ref: "git log -1 --format=%P origin/develop-gsd -> two parents (e9eb3c4 a607a3e); git merge-base --is-ancestor HEAD origin/develop-gsd; git show origin/develop-gsd:.github/workflows/ruleset-apply.yml present; git branch --list + git ls-remote --heads origin both show the phase branch retained"
        status: pass
    human_judgment: false

# Metrics
duration: 20min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 8: Remote sequence start — tag retirement, Apps/secrets, phase PR merged to develop-gsd Summary

**Retired the v2.0.0a5 tag to archive/v2.0.0a5 and closed stale PR #6, then (after the owner granted the codecov and gseg-ruleset-admin Apps and stored their secrets) opened PR #13 and merged the assembled CI/CD workflows onto develop-gsd behind three green required contexts and a verified Codecov upload.**

## Performance

- **Duration:** 20 min (this continuation session, Task 3 only; Tasks 1-2 completed in a prior session — see Completed Tasks below)
- **Started:** 2026-09-28T15:28:00Z
- **Completed:** 2026-09-28T15:48:45Z
- **Tasks:** 3
- **Files modified:** 0 (this plan touches only remote git/GitHub state — tags, a PR, repo secrets; no tracked files in the working tree changed)

## Accomplishments

- **Task 1 — Namespace cleanup (prior session):** Pushed `archive/v2.0.0a5` at the alpha commit (`0b1e94392ba0e436377a3a82b92e03ea2f2e3b5d`) to origin, confirmed it landed, then deleted the old `v2.0.0a5` name locally and on origin. `git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' origin/develop-gsd` now resolves as `v0.10.4-368-ge9eb3c4` instead of sorting above `0.11.0` under the alpha tag. Closed the stale release-please PR #6 with `gh pr close --delete-branch`; `release-please--branches--main` is gone from origin (confirmed again by this session's `git fetch origin`, which reported `[deleted] origin/release-please--branches--main`). A stale gitignored `_version.py` needed `uv sync --frozen --reinstall-package pc2img` to pick up the new describe result (Rule 1 auto-fix, no tracked file involved).
- **Task 2 — Owner action (prior session):** Owner granted the `codecov` App (installation 131721488) and `gseg-ruleset-admin` App (installation 149904322, App ID 4427434) access to `pc2img`, and stored `CODECOV_TOKEN`, `RULESET_APP_ID`, `RULESET_APP_PRIVATE_KEY` as repo secrets.
- **Task 3 — Phase PR merged (this session):** Pushed the phase branch, opened PR #13 (`gsd/phase-06-publication-hardening-downstream-migration-record` -> `develop-gsd`) titled "ci(release): adopt the git-strategy template, publication metadata, docs site and migration record", body scoped to the tree's actual contents with no planning-ID references. Watched `gh pr checks 13 --watch`: `Lint (pre-commit)`, `Tests (pytest)`, `Docs (sphinx -W)` all reported SUCCESS (GH Actions run 36445463863). Confirmed the Codecov upload actually completed — the `Tests (pytest)` job log shows `Upload queued for processing complete` with a live results URL — and that a `codecov/patch` check-run (app `codecov`, conclusion `success`) is attached to the PR head commit, proving both the App installation and the token. Merged with `gh pr merge --merge` (merge commit, branch kept): `origin/develop-gsd` tip `6c10ee0` has two parents (`e9eb3c4`, the phase head `a607a3e`), is a descendant confirmed via `merge-base --is-ancestor`, and carries `.github/workflows/ruleset-apply.yml`. The local and remote phase branches both still exist.

## Task Commits

This plan produced **no local task commits** — every acceptance-bearing change happened on GitHub/origin (tag refs, a closed PR, repo secrets, a merged PR), not in the working tree. `git status --short` before and after Task 3 is identical modulo the pre-existing, deliberately untouched user files.

**Plan metadata:** this SUMMARY commit (hash recorded in Self-Check below).

## Files Created/Modified

None. This plan's `files_modified: []` frontmatter is accurate for the full three-task run — see Accomplishments for the remote-only actions performed.

## Decisions Made

- Task 3's `<verify>` automated command for proving the Codecov App/token queries `/commits/{sha}/status` (the legacy Commit Status API), which returned zero statuses even after the upload completed and after ~2 minutes of polling. The task's own `<action>` prose explicitly named `check-runs` as an equally valid alternative proof ("also confirm a codecov status/check appears on the PR head ... or the commit statuses"). `repos/gseg-ethz/pc2img/commits/a607a3e.../check-runs` shows `codecov/patch` with `app.slug=codecov` and `conclusion=success` on the exact head commit — the acceptance criterion ("codecov status present on the head commit") is satisfied through the plan's own sanctioned alternative. No plan edit was needed; recorded here as a key decision rather than a Rule 1-4 deviation because the plan text already anticipated this exact case.

## Deviations from Plan

None (Rule 1-4) - plan executed exactly as written. See "Decisions Made" above for the one place a verification query needed its documented alternative instead of its primary form.

## Issues Encountered

None. All three `<verify>` blocks for Task 1 and Task 3 passed; Task 2's acceptance criterion (`gh secret list` naming all three secrets) was re-confirmed as this session's Task 3 precondition before any Task 3 action ran.

## User Setup Required

None further — Task 2's owner action (Apps + secrets) is complete and was the only user-setup item this plan carried.

## Next Phase Readiness

- The assembled CI/CD workflows, `RULESETS.md`/`RELEASE.md` records, and the migration record are now on `develop-gsd` behind green required checks and a verified Codecov upload — "merge first" (D-17) is satisfied.
- `RULESET_APP_ID`/`RULESET_APP_PRIVATE_KEY` are in place, which the next plan (06-09, the first live ruleset-apply run) needs to authenticate its token-mint step.
- Left untouched by design (not decided in this phase, recorded per the plan's own instruction): the `release-please`, `bootstrap`/`default`, and `dev/*` remote branches. `release-please--branches--main` (PR #6's scratch branch) was the one branch this plan does dispose of, and `git fetch origin` in this session independently confirmed it is gone (`[deleted] -> origin/release-please--branches--main`).
- Not yet done: live ruleset application (plan 06-10 per the plan's own read_first pointer — the PLAN.md frontmatter table of contents lists 06-09 through 06-13 as the remaining plans in this phase).

## Self-Check: PASSED

No created/modified files to verify (this plan touches no tracked files). Remote state independently re-verified in this session: `archive/v2.0.0a5` present on origin at the recorded SHA; `v2.0.0a5` absent locally and remotely; PR #6 CLOSED with its branch deleted; the three repo secrets present; PR #13 MERGED with a two-parent merge commit `6c10ee0` on `origin/develop-gsd`; `.github/workflows/ruleset-apply.yml` present on `develop-gsd`; both the local and remote phase branches retained.

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*
