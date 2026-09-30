---
phase: 06-publication-hardening-downstream-migration-record
plan: 11
subsystem: infra
tags: [rulesets, branch-protection, ancestry-graft, scheduled-health, github-actions]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record (plan 10)
    provides: "origin/main promoted (6e759d3), protect-main ruleset active/reconciled/idempotent, release PR #15 open unmerged"
provides:
  - "Live ruleset protect-develop-gsd (id 24244420) on gseg-ethz/pc2img: active, bypass_actors [], strict false (recorded develop deviation, kept), no required_linear_history, exactly the two contexts (Lint (pre-commit), Tests (pytest)); comparator clean on first read-back AND on an idempotent second apply"
  - "Ancestry graft merge commit 243710a on develop-gsd (parents 2af2257 + 6e759d3 origin/main), landed via PR #18 through the required Lint+Tests contexts, merged --merge (never squash/rebase); origin/main is now an ancestor of origin/develop-gsd; tree unchanged relative to develop-gsd outside .planning/.claude"
  - "scheduled-health.yml dispatched from main (run 36714649924), watched to success, log contains the OK ancestry line; workflow state active with cron '0 6 * * *' registered on main; no open ancestry-drift issue"
  - "Both required branches (main, develop-gsd) now governed by committed, comparator-clean, idempotently-reconciled rulesets; the phase's ancestry/nightly-assertion mechanism is proven end-to-end"
affects: ["06-12+ (any later plan touching main/develop-gsd protection or the nightly health job)", "phase close / ship gate (first cron-triggered run pending human-check 2026-10-01 06:00 UTC)"]

# Actuals (#2632)
actuals:
  tokens: 9000
  tasks: 3
  commits: 1
  plan_head_before: 2999949ecf2397b3ff58019f8842efe915fcac2f
  plan_head_after: 5081bbe15299e36a7a794254b8b733be0552930f

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The main-checkout executor never has permission to push/merge on GitHub directly (auto-mode denies agent pushes and merges); the owner runs the exact dispatched/pushed/merged command the executor hands them, and the executor re-verifies the result independently afterward. This held for the develop-gsd bootstrap POST and both ruleset-apply.yml dispatches in this plan's Task 1 (from the prior session), same as protect-main in 06-10 — but the graft branch push, PR create, and PR merge in Task 2, and the scheduled-health.yml dispatch in Task 3, were NOT denied and ran directly from the executor, showing the auto-mode classifier's denial is keyed to the specific destination (main/develop-gsd push, ruleset POST) rather than all GitHub-mutating calls uniformly."
    - "Ancestry-graft-then-nightly-assertion: a one-time true merge (never squash/rebase) establishes the merge-base a scheduled workflow watches forever after; the workflow's own workflow_dispatch trigger proves its logic before its schedule trigger can be proven (schedule only registers off the default branch, so registration is checked separately, after promotion, by reading the dispatched run's log and the workflow's registered state)."

key-files:
  created: []
  modified: []

key-decisions:
  - "Owner decision (2026-09-30, Task 1): the plan's literal 'push a throwaway commit directly to develop-gsd and record the refusal' verification step was replaced with a read-only proof — reading both branches' live GitHub ruleset rules via `gh api .../rules/branches/<branch>` and confirming pull_request/required_status_checks/non_fast_forward/deletion (plus required_linear_history on main only) are present with the correct ruleset_id, instead of actually attempting and recording a rejected push. Reason recorded in the prior continuation: if the rule were not enforced, the throwaway commit would land and non_fast_forward would then block its own removal, so a live push was judged an unnecessary risk once the rule-set contents were confirmed present via the read-only API."
  - "The graft (Task 2) was built in a separate gitignored worktree (_scrap/ancestry-graft), never switching the main checkout's own branch, exactly mirroring the promotion-worktree pattern from 06-09/06-10 — kept the executor's own working branch untouched throughout a GitHub-mutating task."

requirements-completed: []  # CICD-02: shared across sibling plans 06-11..06-13 (all three carry requirements: [CICD-02]); not marked complete here, consistent with 06-10-SUMMARY.md's same deferral

coverage:
  - id: D1
    description: "protect-develop-gsd created from the committed .github/rulesets/develop.json payload, reconciled via ruleset-apply.yml, read back clean by the drift comparator, and proven idempotent on a second apply"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "gh api repos/gseg-ethz/pc2img/rulesets/24244420?includes_parents=false jq assertion (bypass_actors present+empty, enforcement active, no required_linear_history rule, strict false, contexts exactly Lint (pre-commit)/Tests (pytest)) exit 0; check_ruleset_drift.py 'protect-develop-gsd:...' -> OK, 1 ruleset compared, 0 differences surviving, 15 normalised away; idempotent re-apply run 36713544557 success, re-read + re-compared identical 0-difference result; gh run list --workflow ruleset-apply.yml --limit 3 --json conclusion -> 3/3 success (36713544557, 36712456605, 36697456406); gh api repos/gseg-ethz/pc2img/rulesets --jq 'map(.name)|sort|join(",")' -> protect-develop-gsd,protect-main"
        status: pass
    human_judgment: false
  - id: D2
    description: "One-time ancestry graft: main merged into develop-gsd as a true merge commit via a gated PR, landing origin/main as an ancestor of origin/develop-gsd with no tree drift outside the strip list"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "git merge-tree --write-tree --name-only origin/develop-gsd origin/main exit 0, no .planning/.claude path in output (prior session); worktree merge commit c8c58b3 (parents 2af2257, 6e759d3), git diff --stat origin/develop-gsd HEAD empty (prior session); PR #18 (chore(git): graft main ancestry into develop-gsd) checks green (Lint, Tests, Docs, codecov/patch), merged --merge --delete-branch by owner -> origin/develop-gsd = 243710a, parents 2af2257 + c8c58b3; this continuation: git merge-base --is-ancestor origin/main origin/develop-gsd -> main-is-ancestor; git log -1 --format=%P origin/develop-gsd | awk '{print NF}' -> 2; git diff --stat origin/main origin/develop-gsd -- . ':!.planning' ':!.claude' | wc -l -> 0 -> trees-match-outside-strip"
        status: pass
    human_judgment: false
  - id: D3
    description: "Nightly ancestry assertion (scheduled-health.yml) dispatched from main, observed passing once with the OK ancestry line, schedule registered active with cron '0 6 * * *', no open ancestry-drift issue"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "gh workflow run scheduled-health.yml --repo gseg-ethz/pc2img --ref main -> run 36714649924, dispatched directly (not denied by auto-mode); gh run watch --exit-status -> success; gh run list --limit 1 --json conclusion,event --jq -> workflow_dispatch=success; gh run view --log | grep -c 'OK: refs/remotes/origin/main is an ancestor of refs/remotes/origin/develop-gsd' -> 1 (full line: 'OK: refs/remotes/origin/main is an ancestor of refs/remotes/origin/develop-gsd — the merge-base is intact.'); gh api .../actions/workflows/scheduled-health.yml --jq .state -> active; git show origin/main:.github/workflows/scheduled-health.yml | grep cron -> \"cron: '0 6 * * *'\"; gh issue list --label ancestry-drift --state open --json number,title -> []"
        status: pass
    human_judgment: true
    rationale: "The plan's own <human-check> for this deliverable (first cron-triggered run at 06:00 UTC 2026-10-01) has not yet occurred — the dispatched run proves the workflow's logic and registration, but the scheduled trigger itself has not been observed firing yet. That check is pending and must be confirmed after 2026-10-01 06:00 UTC before the phase can be considered fully closed on this point."

# Metrics
duration: ~20min (this continuation: Task 2 verify + Task 3 + cleanup + SUMMARY)
completed: 2026-09-30
status: complete
---

# Phase 6 Plan 11: protect-develop-gsd Ruleset, Ancestry Graft, and Nightly Health Assertion Summary

**Both branch-protection rulesets (protect-main, protect-develop-gsd) are now active, comparator-clean, and idempotently reconciled; develop-gsd carries main in its ancestry through a true merge commit landed via a gated PR; and the nightly ancestry-assertion workflow has been dispatched from main and observed passing once, with its schedule registered on the default branch.**

## Performance

- **Duration:** ~20 min in this continuation (Task 1 — protect-develop-gsd bootstrap/reconcile/idempotency and Task 2's graft/PR/merge — was completed in prior sessions per the continuation's carried-in evidence)
- **Completed:** 2026-09-30
- **Tasks:** 3 of 3 (all complete)
- **Files modified:** 0 (this plan's work is entirely remote GitHub state: ruleset objects, a merge commit, and a workflow dispatch — no source files changed)

## Accomplishments

- **Task 1 (completed prior session, evidence carried into this continuation):** `protect-develop-gsd` (id `24244420`) created from the committed `.github/rulesets/develop.json` payload via the owner-run bootstrap POST (auto-mode denies agent ruleset creation), then reconciled through `ruleset-apply.yml` dispatched twice by the owner (runs `36712456605`, `36713544557`) — the second dispatch proving idempotency (identical comparator result, 0 differences surviving both times). Independent read-back confirmed `bypass_actors` present and empty, `enforcement: active`, no `required_linear_history` rule (develop's recorded strict-false deviation, kept), `strict_required_status_checks_policy: false`, and exactly the two required contexts. `check_ruleset_drift.py` reported `0 differences surviving, 15 normalised away` on both reads. `gh api repos/gseg-ethz/pc2img/rulesets --jq 'map(.name)|sort|join(",")'` returned `protect-develop-gsd,protect-main`. The plan's literal direct-push-refusal test was replaced (owner decision) by a read-only proof: `gh api .../rules/branches/develop-gsd` and `.../rules/branches/main` both show `[pull_request, required_status_checks, non_fast_forward, deletion]` (plus `required_linear_history` on main only) at the correct `ruleset_id`s, with nothing ever pushed to either branch directly.
- **Task 2 (completed prior session, re-verified this continuation):** The merge-tree precondition (`git merge-tree --write-tree --name-only origin/develop-gsd origin/main`) exited 0 with no `.planning`/`.claude` path in its output. The graft was built in a separate gitignored worktree (`_scrap/ancestry-graft`, main checkout's own branch never switched): merge commit `c8c58b3` (parents `2af2257` develop-gsd + `6e759d3` main), `git diff --stat origin/develop-gsd HEAD` empty. Branch `chore/ancestry-graft` pushed, PR #18 opened into `develop-gsd`, all four checks green (Lint, Tests, Docs, codecov/patch), merge state CLEAN. The executor's own `gh pr merge` was denied by auto-mode ("Merge Without Review"); the owner ran `gh pr merge 18 --merge --delete-branch`, landing `origin/develop-gsd` at `243710a` (parents `2af2257` + `c8c58b3`) — the first PR ever gated by `protect-develop-gsd`. **This continuation re-ran all three of Task 2's `<verify>` checks fresh:** `git merge-base --is-ancestor origin/main origin/develop-gsd` → `main-is-ancestor`; `git log -1 --format=%P origin/develop-gsd | awk '{print NF}'` → `2`; `git diff --stat origin/main origin/develop-gsd -- . ':!.planning' ':!.claude' | wc -l` → `0` → `trees-match-outside-strip`. All pass.
- **Task 3 (this continuation):** `gh workflow run scheduled-health.yml --repo gseg-ethz/pc2img --ref main` dispatched successfully — **not** denied by auto-mode (unlike the Task 1 ruleset POST and Task 2 PR merge), landing run `36714649924`. Watched to completion with `gh run watch --exit-status`: conclusion `success`, all steps green including "Assert the protected branch is an ancestor of the integration branch". Log confirms the OK line verbatim: `OK: refs/remotes/origin/main is an ancestor of refs/remotes/origin/develop-gsd — the merge-base is intact.` (grep count 1). Registration confirmed: `gh api repos/gseg-ethz/pc2img/actions/workflows/scheduled-health.yml --jq .state` → `active`; `git show origin/main:.github/workflows/scheduled-health.yml | grep cron` → `cron: '0 6 * * *'`. No open `ancestry-drift` issue (`gh issue list --label ancestry-drift --state open` → `[]`). The workflow's own dedup step ("Open or update ancestry-drift issue, deduped") correctly skipped since the assertion passed. **Pending human-check:** the first cron-triggered run is expected at **2026-10-01 06:00 UTC** — `gh run list --workflow scheduled-health.yml --event schedule --limit 1 --json conclusion` should show `success` after that time; not yet observable at authoring time (2026-09-30).
- **Cleanup:** `git worktree remove _scrap/ancestry-graft && git worktree prune` — `git worktree list` now shows only the main checkout. `git branch -D chore/ancestry-graft` deleted the local branch (was `c8c58b3`); `git ls-remote origin chore/ancestry-graft` confirmed empty (remote branch already deleted by the `--delete-branch` merge).

## Task Commits

1. **Task 1: Create protect-develop-gsd, reconcile, read back, prove idempotent** — no local commit (remote-only: owner bootstrap POST + two owner-dispatched `ruleset-apply.yml` runs, all re-verified via `gh api`/`gh run list` in this continuation)
2. **Task 2: Ancestry graft main -> develop-gsd via merge-commit PR** — no local commit in the main checkout (built in gitignored worktree `_scrap/ancestry-graft`, landed remotely via PR #18, merged by the owner; worktree/branch removed in this continuation's cleanup)
3. **Task 3: Dispatch and observe the nightly ancestry assertion** — no source-file commit (workflow dispatch only; run `36714649924`)

**Plan metadata:** (this SUMMARY's own commit, made in the main checkout)

## Files Created/Modified

None in the tracked main checkout. This plan's deliverables are entirely GitHub-side state: a second live ruleset, a merge commit on `develop-gsd`, and an observed workflow run.

## Decisions Made

See `key-decisions` in the frontmatter. In short: the direct-push-refusal proof for Task 1 was replaced with a read-only rules-API check (owner decision, carried from the prior continuation), and the Task 2 graft was built in an isolated worktree to keep the executor's own branch untouched during GitHub-mutating operations — both consistent with the pattern established in 06-09/06-10.

## Deviations from Plan

### Auto-fixed Issues

None in this continuation's own scope (Task 2 verify, Task 3, cleanup, SUMMARY). The one substantive deviation for this plan — substituting the direct-push refusal test with a read-only rules-API proof — was an owner decision recorded in Task 1, carried into this SUMMARY from the continuation's evidence rather than newly introduced here.

---

**Total deviations:** 0 auto-fixed in this continuation. 1 owner-decided substitution carried in from Task 1 (documented above, not a Rule 1-4 auto-fix).
**Impact on plan:** No architectural change. The substitution avoided an unnecessary live push once the rule-set contents were confirmed present via a safer read-only check.

## Issues Encountered

None. Both Task 2's re-verification and all of Task 3 completed cleanly on the first attempt. Notably, the Task 3 `gh workflow run` dispatch and the Task 2 (prior session) PR push/create were **not** denied by Claude Code's auto-mode classifier, in contrast to the Task 1 ruleset bootstrap POST and the Task 2 PR merge, which were. This confirms the auto-mode denial is scoped to specific high-risk destinations (ruleset creation, PR merge into a protected branch) rather than blocking all GitHub-mutating `gh` calls uniformly.

## User Setup Required

**One pending human-check remains, per the plan's own `<human-check>` verification item (not a new setup step, but an unresolved plan verification):**

After **2026-10-01 06:00 UTC**, run:
```
gh run list --repo gseg-ethz/pc2img --workflow scheduled-health.yml --event schedule --limit 1 --json conclusion
```
Expected: `success` — confirming the scheduled trigger fired unattended from `main` and the ancestry assertion passed without a manual dispatch. If it shows `failure` or the run is missing, an `ancestry-drift` issue should also be checked for (`gh issue list --repo gseg-ethz/pc2img --label ancestry-drift --state open`).

## Next Phase Readiness

- Both branch-protection rulesets (`protect-main` id `24237564`, `protect-develop-gsd` id `24244420`) are active, comparator-clean, and proven idempotent.
- `develop-gsd` now carries `main` in its ancestry via a true merge commit (`243710a`), landed through the newly-active `protect-develop-gsd` ruleset's own PR gate — the first PR ever merged under that ruleset.
- The nightly ancestry assertion has been dispatched and observed passing once, with its schedule registered active on `main` (`cron: '0 6 * * *'`).
- No blockers carried forward, aside from the pending first-cron-slot human-check noted above (2026-10-01 06:00 UTC), which is an observation task, not a rework risk — the workflow's logic has already been proven via dispatch.
- `_scrap/ancestry-graft` worktree and `chore/ancestry-graft` local/remote branches are fully cleaned up; nothing left over for the next plan.

## Self-Check

- [x] `protect-develop-gsd` (id `24244420`) exists, active, empty bypass, comparator clean: confirmed via fresh `gh api` read in this continuation
- [x] `gh run list --workflow ruleset-apply.yml --limit 5` shows 3 consecutive `success` runs for develop (`36713544557`, `36712456605`, `36697456406` — the third being the shared main-apply re-dispatch from 06-10, all still within the 3-of-3 window the plan's verify requires): confirmed
- [x] `git merge-base --is-ancestor origin/main origin/develop-gsd` holds: confirmed
- [x] `origin/develop-gsd` tip has 2 parents (true merge, not squash/rebase): confirmed
- [x] Trees match outside `.planning`/`.claude` between `origin/main` and `origin/develop-gsd`: confirmed
- [x] `scheduled-health.yml` run `36714649924` concluded `success`, log contains the OK ancestry line: confirmed
- [x] Workflow state `active`, cron `0 6 * * *` registered on `main`, no open `ancestry-drift` issue: confirmed
- [x] `_scrap/ancestry-graft` worktree removed, `chore/ancestry-graft` local branch deleted, remote branch confirmed gone: confirmed

## Self-Check: PASSED

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-30*
