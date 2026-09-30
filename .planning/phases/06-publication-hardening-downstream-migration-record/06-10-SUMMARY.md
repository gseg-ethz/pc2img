---
phase: 06-publication-hardening-downstream-migration-record
plan: 10
subsystem: infra
tags: [main-promotion, release-please, rulesets, branch-protection, worktree, drift-comparator]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record (plan 09)
    provides: "Verified, unpushed promotion commit 0819b2b in the gitignored worktree _scrap/pc2img-promotion, parent origin/main, tree = develop-gsd minus .planning/.claude"
provides:
  - "origin/main promoted to the filtered 2.x tree (first via 0819b2b, then again via 6e759d3 carrying the drift-comparator fix); .planning and .claude both 404 on main"
  - "Release PR #15 'chore(main): release 0.11.0' by app/gseg-release-please, OPEN, checks green, fast path engaged — left unmerged per D-19"
  - "Live ruleset protect-main (id 24237564) on gseg-ethz/pc2img: active, bypass_actors [], required_linear_history present, strict_required_status_checks_policy true, exactly the three required contexts, current_user_can_bypass never"
  - "PULL_REQUEST_READ_FILLED_KEYS in .github/scripts/ruleset_lib.py now includes require_extra_approval_for_unattributed_changes, closing the drift gap found on the first apply attempt (fb44899, PRs #16/#17)"
affects: ["06-11 (develop-gsd ruleset, next)", "06-12+ (any plan touching main/ruleset state)"]

# Actuals (#2632)
actuals:
  tokens: 9000
  tasks: 3
  commits: 2
  plan_head_before: fffa2393787cc7074b3ed35130524979eb597a3a
  plan_head_after: PENDING_AT_WRITE_TIME

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ruleset bootstrap-then-reconcile: a repo with no prior ruleset of a given name must be POSTed once (owner token, admin scope) before the kit's dispatch-only apply workflow can PUT-update it by name; the apply run's own in-run drift check and an independent post-run read-back both re-run the same comparator against a freshly fetched live.json, so a clean apply is proven twice from two different token scopes"
    - "GitHub-read-filled ruleset keys are tracked in an explicit allow-list (PULL_REQUEST_READ_FILLED_KEYS) rather than inferred; a key GitHub silently populates on read that isn't in the list surfaces as false drift, not a real config divergence"

key-files:
  created: []
  modified:
    - ".github/scripts/ruleset_lib.py (already landed on develop-gsd in commit fb44899 before this continuation began; carried into main by the second promotion PR #17)"

key-decisions:
  - "Owner decision (2026-09-30, mid-Task-3): normalise require_extra_approval_for_unattributed_changes in the drift comparator's PULL_REQUEST_READ_FILLED_KEYS rather than add it to the committed payload, and land the fix on main immediately (via a second develop-gsd PR + a second filtered promotion) rather than deferring it to plan 06-11 — because Task 3's own acceptance criteria require a clean drift comparator exit 0 on this plan, not a later one."
  - "Second promotion (commit 4f5de06, PR #17 to main) reused the exact filtered-worktree recipe from 06-09/06-10 Task 2 (parent origin/main 0819b2b, tree = develop-gsd 2af2257 minus .planning/.claude) rather than inventing a lighter-weight direct-to-main patch, keeping the promotion mechanism itself as the only path onto main even for a 2-file infra fix."

requirements-completed: []  # CICD-02: gsd_run query requirements.ready-ids gate applies across sibling plans 06-11..06-13 sharing the same ID; not marked complete here

coverage:
  - id: D1
    description: "Blocking human decision gate on PROMOTION_SHA before any push (Task 1)"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "Owner reviewed PROMOTION_SHA=0819b2b754672829f45ac7e169de4e4707821266, its message, diff stat, describe output; chose 'reword first' then approved proceed (recorded in 06-09-SUMMARY.md 'Post-execution amendment')"
        status: pass
    human_judgment: true
  - id: D2
    description: "origin/main == PROMOTION_SHA; .planning/.claude absent; release-please opened OPEN, App-authored, checks-green PR #15 with the fast path engaged; PR left unmerged"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "git ls-remote origin refs/heads/main (owner-pushed) equalled 0819b2b; gh api repos/gseg-ethz/pc2img/contents/.planning?ref=main and ...contents/.claude?ref=main both 404; gh pr list --base main --state open (title regex release 0.11.0) -> #15, author app/gseg-release-please; gh run list --workflow release-please.yml --branch main -> conclusion success; PR #15 checks green, Tests job log line 'classify-changes: true — all 2 changed path(s) are release artifacts'"
        status: pass
      - kind: other
        ref: "This continuation: gh pr view 15 --json state,title,author -> state OPEN, title 'chore(main): release 0.11.0', author app/gseg-release-please (is_bot); confirmed still unmerged after the second promotion landed 6e759d3 on main"
        status: pass
    human_judgment: false
  - id: D3
    description: "protect-main created from the committed payload, reconciled through ruleset-apply.yml, read back clean by the drift comparator"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "First attempt (owner-run bootstrap POST -> ruleset id 24237564; owner-dispatched run 36696050776): step 9 in-run drift FAILED on require_extra_approval_for_unattributed_changes (live=true, committed=absent) even though the independent jq read-back assertion passed"
        status: fail
      - kind: other
        ref: "Deviation fix (Rule 3, blocking): commit fb44899 adds the key to PULL_REQUEST_READ_FILLED_KEYS + a new pinning test (test_ruleset_lib.py: 3 failures before, 93 passed after); merged develop-gsd via PR #16 (2af2257), promoted to main via PR #17 (commit 4f5de06, merged 6e759d3)"
        status: pass
      - kind: other
        ref: "This continuation: re-dispatched run 36697456406 watched to completion (gh run watch --exit-status, exit 0); its own step log shows 'applied to ruleset protect-main (id 24237564)' then 'check_ruleset_drift: OK — 1 ruleset(s) compared, 0 differences surviving, 16 normalised away' (require_extra_approval_for_unattributed_changes now correctly normalised under rule (d))"
        status: pass
      - kind: other
        ref: "Independent read-back: gh api repos/gseg-ethz/pc2img/rulesets/24237564?includes_parents=false -> jq assertion (has bypass_actors, length==0, enforcement active, required_linear_history present, strict_required_status_checks_policy true) exit 0 = true; uv run --frozen python .github/scripts/check_ruleset_drift.py 'protect-main:<live>:.github/rulesets/main.json' exit 0, '0 differences surviving, 16 normalised away'; required contexts read back as exactly Lint (pre-commit), Tests (pytest), Docs (sphinx -W); current_user_can_bypass = never"
        status: pass
    human_judgment: false
---

# Phase 6 Plan 10: Push to Main, Release PR, and protect-main Ruleset Summary

**Pushed the reviewed 2.x tree to public `main` behind an explicit human go/no-go, confirmed release-please opened an unmerged 0.11.0 release PR with green fast-path checks, then created and reconciled the `protect-main` branch-protection ruleset — surviving one real drift finding mid-task that required a second develop-gsd PR and a second promotion before the comparator went clean.**

## Performance

- **Duration:** ~3 sessions across Tasks 1-3 (Task 1 decision gate + Task 2 push in prior sessions; this continuation covers the tail of Task 3: apply-run watch, independent read-back, cleanup, and this SUMMARY)
- **Completed:** 2026-09-30
- **Tasks:** 3 of 3 (all complete)
- **Files modified:** 0 in this continuation's own diff (the drift-comparator fix, `.github/scripts/ruleset_lib.py` + its test, was authored and committed earlier in this same plan's Task 3 as commit `fb44899`, before this continuation began)

## Accomplishments

- **Task 1 (blocking-human decision, completed prior session):** Owner reviewed `PROMOTION_SHA=0819b2b754672829f45ac7e169de4e4707821266` — full commit message, diff stat (`86 files changed, 16317 insertions(+), 2811 deletions(-)`), `git describe` output, confirmation both review rounds are recorded clean in `06-UAT.md` — and chose "reword first" (the body's closing sentence was rewritten to stop pointing at internal planning history before the tree becomes public), then approved **proceed**.
- **Task 2 (owner-run push, completed prior session):** Because Claude Code's auto-mode classifier denies agent pushes to `main`, the owner ran `git -C _scrap/pc2img-promotion push origin HEAD:refs/heads/main`. Verified: `origin/main` == `0819b2b`; `.planning` and `.claude` both 404 on main (the plan's unquoted `?ref=main` URL glob-fails in zsh — substituted the quoted form); release-please run `36694879352` succeeded; release PR **#15** `chore(main): release 0.11.0` opened by `app/gseg-release-please` (not the default token — proves checks can run); its three checks passed with the fast path engaged (`classify-changes: true — all 2 changed path(s) are release artifacts`, confirmed in the Tests job log, run `36694925067` / job `109820484268`). (`gh run list --workflow X --branch main` combo returned `[]` as a `gh` quirk; cross-confirmed instead via separate run-id and branch checks.)
- **Task 3, first attempt (mixed owner/agent, completed prior session):** Preflight (`preflight_ruleset_apply.py`) exited 0 against `_scrap/pc2img-promotion`'s workflow files (asserted equal to `origin/main` first). Auto-mode denied the agent's bootstrap POST, so the owner ran it directly, creating `protect-main` (id `24237564`, `bypass_actors: []`, `current_user_can_bypass: never`). The owner then dispatched `ruleset-apply.yml` (run `36696050776`): steps 1-8 (including the App-token mint, the running proof of the `RULESET_APP_ID`/`RULESET_APP_PRIVATE_KEY` grant) succeeded, but **step 9's in-run drift verification failed**: `require_extra_approval_for_unattributed_changes` read back `true` live with no corresponding key in the committed payload. The independent jq structural assertion (bypass_actors/enforcement/linear-history/strict) still passed — this was a comparator gap, not a live-state problem. Cross-checked against sibling repos PCHandler/GSEGUtils: both show the same field `=true` live but don't carry the ruleset kit at all (only `check_publish_gate.py`), confirming the comparator gap was pc2img-owned, not inherited.
- **Task 3, deviation fix (Rule 3, blocking — owner decision, this same continuation's predecessor turn):** Normalised the key into `PULL_REQUEST_READ_FILLED_KEYS` in `.github/scripts/ruleset_lib.py` (consistent with the other GitHub-read-filled `pull_request` keys already in that list) rather than adding it to the committed payload. `test_ruleset_lib.py`'s fixture was updated to carry the key, and a new test `test_unattributed_changes_approval_is_a_read_filled_key` was added: **3 failures before the fix, 93 passed after**. A local drift check against the live `protect-main` state exited 0 before this fix was even merged, confirming the fix's shape was correct in isolation. Committed as `fb44899` on the phase branch, merged via PR #16 into `develop-gsd` (two-parent merge `2af2257`, checks green). Promoted to `main` a second time: commit `4f5de06` (parent `origin/main` `0819b2b`, tree = `develop-gsd` `2af2257` minus `.planning`/`.claude`, 2 files changed / +10 lines) built in the same worktree recipe as the first promotion, in branch `promote/ruleset-drift-normalisation`; PR **#17** to `main`, checks green, merge state `CLEAN` — the **first PR ever gated by the new `protect-main` ruleset**. Owner merged it with `--rebase`, landing `main` at `6e759d3`.
- **Task 3, this continuation (final verification + cleanup):**
  1. `gh run watch 36697456406 --repo gseg-ethz/pc2img --exit-status` — the owner's re-dispatch of `ruleset-apply.yml` after the fix landed on main. Already completed with conclusion **success** before the watch call returned (exit 0). Its own step log: `applied to ruleset protect-main (id 24237564) on gseg-ethz/pc2img`, then `check_ruleset_drift: OK — 1 ruleset(s) compared, 0 differences surviving, 16 normalised away` — the previously-surviving key is now among the 16 normalised entries, dropped correctly under rule (d).
  2. Independent read-back (not reusing the in-run artifact): fetched `protect-main`'s id (`24237564`) fresh, re-read it via `gh api .../rulesets/24237564?includes_parents=false` into a new local file. The plan's jq assertion (`has("bypass_actors") and (.bypass_actors|length==0) and .enforcement=="active" and required_linear_history present and strict_required_status_checks_policy==true`) evaluated `true`, exit 0. `check_ruleset_drift.py` on this fresh read-back also exited 0 with the identical `0 differences surviving, 16 normalised away` result. Additional spot checks: required contexts read back as exactly `Lint (pre-commit)`, `Tests (pytest)`, `Docs (sphinx -W)`; `current_user_can_bypass` = `never`.
  3. Confirmed `gh run list --workflow ruleset-apply.yml --limit 1 --json conclusion` = `success`.
  4. Cleanup: `git worktree remove _scrap/pc2img-promotion && git worktree prune` — `git worktree list` afterward shows only the main checkout. `git branch -D promote/ruleset-drift-normalisation` deleted the local promotion branch (`was 4f5de06`); no remote branch was touched (the owner's PR #17 merge already handled the remote side; GitHub's own branch-deletion policy for that PR was left as-is).
  5. Confirmed release PR `#15` is still `OPEN`, unmerged, title unchanged (`chore(main): release 0.11.0`), author `app/gseg-release-please` — `git fetch origin main` shows `origin/main` now at `6e759d3` (carrying the drift-comparator fix), and PR #15 remains based on `main` without having been merged.

## Task Commits

1. **Task 1: Go/no-go decision** — no commit (decision recorded in `06-09-SUMMARY.md` "Post-execution amendment")
2. **Task 2: Push to main; verify release PR** — no local commit in the main checkout (remote-only: owner push, verified via `gh`/`git ls-remote`)
3. **Task 3: Create + reconcile protect-main; deviation fix** — `fb44899` `ci(rulesets): normalise the unattributed-changes approval key GitHub fills on read` (phase branch, in this continuation's predecessor turn); remote side: PR #16 -> `develop-gsd` (`2af2257`), PR #17 -> `main` (`4f5de06`, merged as `6e759d3`) — both owner-merged, neither a local-checkout commit

**Plan metadata:** (this SUMMARY's own commit, made in the main checkout)

## Files Created/Modified

- `.github/scripts/ruleset_lib.py` — added `require_extra_approval_for_unattributed_changes` to `PULL_REQUEST_READ_FILLED_KEYS` (landed via `fb44899` on the phase branch; carried to `develop-gsd` via PR #16 and to `main` via PR #17)
- `tests/test_ruleset_lib.py` (or equivalent — see `fb44899`) — fixture updated to include the key; new test `test_unattributed_changes_approval_is_a_read_filled_key` added
- No files modified in the tracked main checkout during this continuation itself (verification, read-back, and cleanup only)
- `_scrap/pc2img-promotion` (gitignored worktree) — removed at the end of this continuation

## Decisions Made

See `key-decisions` in the frontmatter. In short: the owner chose to fix the drift-comparator gap in the comparator itself (treating the GitHub-read-filled key the same as its siblings) rather than widen the committed ruleset payload, and chose to land that fix on `main` immediately via a second filtered promotion rather than deferring it — because this plan's own Task 3 acceptance criteria require the comparator to exit clean now, not later.

## Verification

All of Task 3's automated `<verify>` checks pass on the independent read-back performed in this continuation:

```
--- jq structural assertion ---
true  (exit 0)

--- check_ruleset_drift.py (fresh read-back) ---
... 16 lines of "normalised away" (envelope keys, GitHub-read-filled pull_request/required_status_checks params, integration_id) ...
check_ruleset_drift: OK — 1 ruleset(s) compared, 0 differences surviving, 16 normalised away
(exit 0)

--- gh run list --workflow ruleset-apply.yml --limit 1 --json conclusion ---
success

--- worktree removal ---
git worktree list -> only /scratch/31_pc2img (worktree-removed)

--- PR #15 ---
{"author":{"is_bot":true,"login":"app/gseg-release-please"},"baseRefName":"main","headRefName":"release-please--branches--main","isDraft":false,"number":15,"state":"OPEN","title":"chore(main): release 0.11.0"}

--- origin/main tip ---
6e759d3af5e0fe2862c7ffc7ef8606f716e4b575
```

Must-haves from the plan frontmatter:
- Owner saw PROMOTION_SHA/message/diff-stat at a blocking gate and answered proceed before any push: verified (06-09-SUMMARY.md amendment).
- `origin/main` == PROMOTION_SHA (then, after the fix, `6e759d3`); no `.planning`/`.claude` on main; release-please ran with the release App, opened the 0.11.0 PR, stays open: verified.
- Release PR checks green through the release-artifact fast path: verified.
- `protect-main` active, created from the committed payload, reconciled through the dispatch-only apply workflow, `bypass_actors` present and empty, strict checks and linear history, drift comparator reports no difference: verified (after the fix landed).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Drift comparator false-positive on `require_extra_approval_for_unattributed_changes`**
- **Found during:** Task 3, first `ruleset-apply.yml` dispatch's in-run verification step (run `36696050776`)
- **Issue:** GitHub fills `require_extra_approval_for_unattributed_changes: true` on read for this `pull_request` ruleset rule, but the committed payload (`.github/rulesets/main.json`) is silent about it (same as its sibling read-filled keys `allowed_merge_methods`, `dismissal_restriction`, `required_reviewers`, `do_not_enforce_on_create`). Because this one key wasn't yet in `PULL_REQUEST_READ_FILLED_KEYS`, `check_ruleset_drift.py` reported it as real drift and the apply run's own verification step failed the plan's acceptance criteria (comparator exit 0), even though the live ruleset state itself was correct.
- **Fix:** Added the key to `PULL_REQUEST_READ_FILLED_KEYS` in `.github/scripts/ruleset_lib.py`, matching the treatment of its sibling read-filled keys. Added fixture coverage + a dedicated pinning test.
- **Files modified:** `.github/scripts/ruleset_lib.py`, its test file
- **Verification:** Test suite 3 failures -> 93 passed; local drift check against live `protect-main` state exit 0 before merge; the re-dispatched apply run's in-run comparator and this continuation's independent read-back both confirm 0 surviving differences (16 normalised away, including this key)
- **Committed in:** `fb44899` (phase branch) -> PR #16 -> `develop-gsd` (`2af2257`) -> PR #17 -> `main` (`4f5de06`, merged `6e759d3`)

---

**Total deviations:** 1 auto-fixed (1 Rule-3 blocking fix, requiring a second develop-gsd PR and a second filtered promotion to land on `main` before Task 3's acceptance criteria could be met).
**Impact on plan:** The plan's Task 3 could not close on the first apply attempt as written; closing it required two additional PRs (#16, #17) and a second promotion cycle beyond the plan's literal step list. No architectural change — the fix reuses the exact promotion-commit recipe from Task 2/06-09, and the ruleset kit's own dispatch-only apply mechanism was exercised twice, which is itself evidence the mechanism works under real drift, not just a clean first pass.

## Issues Encountered

None beyond the documented drift-comparator deviation above, which is fully resolved.

## Command quirks (recorded per the continuation's instructions, not deviations from correctness)

1. `gh api repos/gseg-ethz/pc2img/contents/.planning?ref=main` — the unquoted URL with `?ref=main` glob-fails under zsh; quoted form used instead (`"...?ref=main"`).
2. `gh run list --workflow release-please.yml --branch main` combined with other filters intermittently returned `[]` even for a run that existed; cross-confirmed by querying the run id and the branch separately rather than trusting the combined filter.

## User Setup Required

None remaining. All owner-only actions for this plan (the go/no-go decision, the push to `main`, the bootstrap ruleset POST, both `ruleset-apply.yml` dispatches, and both PR merges — #16 and #17) were completed in prior sessions or this continuation's predecessor turn, and are independently re-verified here.

## Next Phase Readiness

- `main` is promoted (now at `6e759d3`, carrying both the original filtered tree and the drift-comparator fix), release PR #15 open and unmerged, `protect-main` active with an empty bypass list and a comparator-clean state proven by two independent evaluations (in-run and this continuation's fresh read-back).
- The promotion worktree `_scrap/pc2img-promotion` and its local branch are both gone; nothing is left over for plan 06-11 to clean up.
- Plan 06-11 (the `develop-gsd` ruleset) can proceed — it was not blocked by this plan's deviation, since the deviation's fix landed as ordinary PRs through the existing branches, not as a change to the ruleset-apply mechanism itself.
- No blockers carried forward.

## Self-Check

- [x] Ruleset `protect-main` (id `24237564`) exists and is `active`: confirmed via fresh `gh api` read-back in this continuation
- [x] `gh run list --workflow ruleset-apply.yml --limit 1` conclusion is `success` for the re-dispatched run: confirmed
- [x] `check_ruleset_drift.py` exits 0 on a freshly fetched read-back (not the in-run artifact): confirmed, `0 differences surviving, 16 normalised away`
- [x] `_scrap/pc2img-promotion` worktree is gone: confirmed via `git worktree list`
- [x] Local branch `promote/ruleset-drift-normalisation` is deleted: confirmed via `git branch --list`
- [x] Release PR #15 still `OPEN`, title `chore(main): release 0.11.0`, unmerged: confirmed via `gh pr view`
- [x] `origin/main` at `6e759d3` (post-fix promotion tip): confirmed via `git fetch` + `git rev-parse`

## Self-Check: PASSED

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-30*
