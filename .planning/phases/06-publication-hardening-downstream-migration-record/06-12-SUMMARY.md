---
phase: 06-publication-hardening-downstream-migration-record
plan: 12
subsystem: infra
tags: [readthedocs, sphinx, setuptools_scm, github-environments, testpypi, oidc-trusted-publisher]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record (plan 11)
    provides: "Both branch-protection rulesets active/idempotent; develop-gsd carries main in its ancestry; nightly ancestry assertion dispatched and passing"
provides:
  - "Read the Docs project pc2img imported (owner action, Task 1), building main's .readthedocs.yaml on the `latest` version"
  - "RTD tag-fetch bug (D-31 first real build) found and fixed: post_checkout ran a single `git fetch --unshallow --tags || true`, which is fatal (and silently swallowed) once RTD's own depth-50 fetch already holds full history, so setuptools_scm never saw a tag and rendered `0.0.post41`; split into two fetches, commit e9a3a98, merged to main via PR #19 -> develop-gsd 52c6c7f -> promotion 83964d9 -> PR #20 -> main 20ef688"
  - "https://pc2img.readthedocs.io/en/latest/ live and green: badge passing, site HTTP 200, page contains \"API reference\"; latest successful build 34852247 (commit 20ef688) renders pc2img 0.10.4.post7"
  - "GitHub environment testpypi created via the API (0 protection rules, no branch policy) — the dry run needs no reviewer gate"
  - "TestPyPI pending trusted publisher registered by the owner: pc2img / gseg-ethz / pc2img / publish-testpypi.yml / testpypi (Task 3, confirmed 2026-09-30; running proof deferred to 06-13's dispatch)"
  - "stable RTD version left pointing at the pre-0.11 v0.10.4 tag by owner decision — it will move to v0.11.0 once that tag is cut"
affects: ["06-13 (dispatches publish-testpypi.yml — the trusted-publisher registration is its precondition)", "phase close / ship gate (RTD hosting half of SC2 is now proven by a real build, not just config)"]

# Actuals (#2632)
actuals:
  tokens: 400
  tasks: 3
  commits: 1
  plan_head_before: 7436788991f2d2f8ec0d65a0e85eb048c8cbc362
  plan_head_after: PENDING_AT_COMMIT

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reproduce-don't-read (global Review Discipline rule, applied here rather than to a review finding): rather than reading RTD's post_checkout step and reasoning about whether `--unshallow --tags` would work, the orchestrator reproduced RTD's exact clone sequence (shallow clone, depth-50 fetch, then the post_checkout step) locally and observed the real failure (`fatal: --unshallow on a complete repository does not make sense`, silently hidden by `|| true`, version renders `0.0.post41`) before writing the fix, then reproduced the fixed sequence locally too (`0.10.4.post6`) before opening the PR."

key-files:
  created: []
  modified:
    - ".readthedocs.yaml (post_checkout: split the single `git fetch --unshallow --tags || true` into a separate `--unshallow` and `--tags` fetch, since the combined form is fatal once RTD's own depth-50 fetch already holds full history)"

key-decisions:
  - "Owner decision (2026-09-30, Task 1): leave the auto-created `stable` RTD version pointing at the old-layout v0.10.4 tag (its build fails — no RTD config existed at that tag) rather than deleting or activating it now; it will resolve itself once v0.11.0 is tagged and `stable` re-points."
  - "Owner decision (2026-09-30, Task 2 deviation, Rule 1): fix the RTD tag-fetch bug immediately, before 06-13, rather than deferring — 06-13 dispatches a release workflow and needs an already-correct docs pipeline as its baseline, not a second in-flight fix."
  - "The fix was landed through the full promotion chain already established in 06-09/06-10 (PR into develop-gsd, checks green, owner-merged; promotion commit built in a worktree; PR into main, checks green, owner-merged), not as a direct push to either protected branch — consistent with protect-main/protect-develop-gsd from 06-10/06-11."

patterns-established:
  - "Owner account actions are recorded with their concrete outcome (build numbers, HTTP codes, exact API tuple), not just \"done\" — the plan's <resume-signal> only asks for a word, but the SUMMARY captures what that word confirmed."

requirements-completed: []  # CICD-02: shared across sibling plans 06-11..06-13 (all three carry requirements: [CICD-02]); not marked complete here, consistent with 06-10/06-11-SUMMARY.md's same deferral

coverage:
  - id: D1
    description: "Read the Docs project pc2img imported (owner action) and its `latest` version builds main's .readthedocs.yaml"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "curl -s -o /dev/null -w '%{http_code}' https://readthedocs.org/projects/pc2img/badge/?version=latest -> 200 (project exists, build started); first build 34851945 (commit 6e759d3) completed but rendered a tagless version, diagnosed and fixed in D2 below"
        status: pass
    human_judgment: false
  - id: D2
    description: "RTD tag-fetch bug found and fixed by running the reproduction locally, then verified end-to-end against the real hosted site after the fix promoted to main"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "curl -s 'https://readthedocs.org/projects/pc2img/badge/?version=latest' | grep -c passing -> 1; curl -s -o /tmp/rtd-index.html -w '%{http_code}\\n' https://pc2img.readthedocs.io/en/latest/ -> 200; grep -c 'API reference' /tmp/rtd-index.html -> 4; latest successful build 34852247 (commit 20ef688, 2026-09-30T12:43:54Z) rendered 'pc2img 0.10.4.post7'"
        status: pass
    human_judgment: false
  - id: D3
    description: "GitHub environment testpypi created (no reviewer, no wait timer — a dry-run environment needs neither)"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "gh api --method PUT repos/gseg-ethz/pc2img/environments/testpypi -> id 23112113818, 0 protection_rules, no branch policy; gh api repos/gseg-ethz/pc2img/environments --jq '.environments[].name' -> testpypi listed"
        status: pass
    human_judgment: false
  - id: D4
    description: "TestPyPI pending trusted publisher registered for the exact 4-tuple (owner action)"
    verification: []
    human_judgment: true
    rationale: "TestPyPI's pending-publisher registration has no read API reachable from this session (it requires the owner's own authenticated TestPyPI session to view or verify); the owner confirmed the row was saved with the exact fields (pc2img / gseg-ethz / pc2img / publish-testpypi.yml / testpypi). The running proof is 06-13's dispatch of publish-testpypi.yml — a successful OIDC token exchange there is the only fully automatable verification of this tuple, and it happens in the next plan, not this one."

# Metrics
duration: ~25min (Task 1 owner import + first-build diagnosis; Task 2 reproduce/fix/promote/re-verify; Task 3 owner registration)
completed: 2026-09-30
status: complete
---

# Phase 6 Plan 12: Read the Docs Hosting, Tag-Fetch Fix, and TestPyPI Trusted Publisher Summary

**Read the Docs now serves a correctly-versioned build of main (0.10.4.post7) after finding and fixing a silent tag-fetch bug in `.readthedocs.yaml` by reproducing RTD's clone sequence locally; the testpypi GitHub environment exists and the owner has registered the matching TestPyPI trusted-publisher tuple.**

## Performance

- **Duration:** ~25 min across the three tasks (owner actions plus the reproduce-fix-promote cycle)
- **Completed:** 2026-09-30
- **Tasks:** 3 of 3
- **Files modified:** 1 (`.readthedocs.yaml`)

## Accomplishments

- **Task 1 (owner action):** Owner imported `gseg-ethz/pc2img` on Read the Docs (slug `pc2img`, default branch `main`). The first `latest` build (34851945, commit 6e759d3) succeeded but rendered `pc2img 0.0.post41` — RTD's log showed `git fetch --unshallow --tags || true` failing with `fatal: --unshallow on a complete repository does not make sense`, silently swallowed by `|| true`, because RTD's own `clone --depth 1` + `fetch --depth 50 HEAD` already held all 41 commits and the tags were never fetched as a result. RTD also auto-created a `stable` version pointing at the pre-existing tag `v0.10.4` (0.10 layout, no RTD config there), which failed to build (34851946); **owner decision:** leave `stable` as-is — it resolves once `v0.11.0` is tagged.
- **Task 2 (auto, with a Rule 1 deviation):** Reproduced RTD's exact clone sequence locally to confirm the diagnosis by running it, not by reading the YAML: the unpatched sequence reproduced `0.0.post41`. Split the single fused command into two separate fetches (`git fetch --unshallow || true` then `git fetch --tags`) and reproduced the fix locally too: `0.10.4.post6`. Landed via the established promotion chain — commit `e9a3a98` (`fix(docs): fetch tags on Read the Docs even when the clone is already complete`, `.readthedocs.yaml` +5/−2) → PR #19 into `develop-gsd` (checks green, including an RTD PR-preview build rendering `0.10.4.post460`) → owner-merged (`--merge`) → `develop-gsd` at `52c6c7f` → promotion commit `83964d9` (parent `origin/main` `6e759d3`, tree = develop-gsd minus `.planning`/`.claude`) → PR #20 into `main` (checks green, RTD preview `0.10.4.post7`) → owner-merged (`--rebase`) → `main` at `20ef688`. Promotion worktree and local branch removed afterward. Re-verified end-to-end against the real hosted site: badge `passing`, `https://pc2img.readthedocs.io/en/latest/` → `200` with 4 occurrences of "API reference", latest successful build `34852247` (commit `20ef688`, `2026-09-30T12:43:54Z`) rendering `pc2img 0.10.4.post7`. Created the GitHub environment `testpypi` via `gh api --method PUT repos/gseg-ethz/pc2img/environments/testpypi` (id `23112113818`, 0 protection rules, no branch policy — not denied by auto-mode) and confirmed it lists in `gh api repos/gseg-ethz/pc2img/environments`.
- **Task 3 (owner action):** Owner registered the TestPyPI pending trusted publisher for the exact tuple `pc2img` / `gseg-ethz` / `pc2img` / `publish-testpypi.yml` / `testpypi`, confirmed 2026-09-30. The running proof (a successful OIDC-authenticated upload) is deferred to plan 06-13's dispatch of `publish-testpypi.yml`.

**Version-string reconciliation (not a defect — recorded because it differs from the plan's stated expectation):** the plan's Task 2 anticipated `0.10.4.post1`; the actually-rendered `0.10.4.post7` is correct. `git log v0.10.4..origin/main` counts 7 commits: 4 pre-existing commits already on `main` after the `v0.10.4` tag (`cd9c37d`, `f946268`, `69224a9`, `ade40f8` — LICENSE/merge housekeeping, see 06-09's deviation record) plus 3 promotions (`0819b2b` the first promotion, `6e759d3` the drift-comparator fix from 06-10, `20ef688` this plan's RTD tag-fetch fix).

## Task Commits

1. **Task 1: Owner action — import pc2img on Read the Docs** — no repo commit (remote-only: RTD project creation, first build 34851945/34851946)
2. **Task 2: Reproduce, fix, promote, and re-verify the RTD build; create the testpypi environment** — `e9a3a98` (fix), landed to `main` at `20ef688` via PR #19 → develop-gsd → promotion `83964d9` → PR #20 → main (all merges owner-run; environment creation via `gh api`)
3. **Task 3: Owner action — register the TestPyPI pending trusted publisher** — no repo commit (remote-only: TestPyPI account action)

**Plan metadata:** (this SUMMARY's own commit, made in the main checkout)

## Files Created/Modified

- `.readthedocs.yaml` - split the fused `git fetch --unshallow --tags || true` post_checkout step into a separate unshallow fetch and tag fetch, so tags are always fetched even when RTD's own history is already complete

## Decisions Made

See `key-decisions` in the frontmatter. In short: `stable` stays pointed at the pre-0.11 tag until `v0.11.0` ships; the tag-fetch bug was fixed immediately (Rule 1) rather than deferred to keep 06-13's release-workflow dispatch running against a correct docs baseline; the fix travelled through the same develop-gsd → promotion → main chain established in 06-09/06-10, not a direct push.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] RTD post_checkout tag fetch was fatal-and-hidden once the clone was already complete**
- **Found during:** Task 2 (verifying the first RTD build by running it)
- **Issue:** `.readthedocs.yaml`'s post_checkout step ran `git fetch --unshallow --tags || true` as one command. RTD's own checkout already does a `--depth 50` fetch, which on this 41-commit repo already holds full history — making `--unshallow` fatal (`fatal: --unshallow on a complete repository does not make sense`) and, combined in one command, taking the `--tags` fetch down with it. The `|| true` swallowed the failure silently, so `setuptools_scm` found no tags and the docs rendered `pc2img 0.0.post41` instead of a real version.
- **Fix:** Split into two independent fetches — `git fetch --unshallow || true` (tolerates the already-complete case) followed by an unconditional `git fetch --tags` (always runs, regardless of whether the unshallow step did anything).
- **Files modified:** `.readthedocs.yaml`
- **Verification:** Reproduced RTD's clone sequence locally before and after the fix (`0.0.post41` → `0.10.4.post6`); after promotion to `main`, the real hosted build confirmed `0.10.4.post7`, badge `passing`, site `200` with "API reference" present.
- **Committed in:** `e9a3a98` (landed to `main` at `20ef688` via PR #19 → develop-gsd → promotion → PR #20)

---

**Total deviations:** 1 auto-fixed (Rule 1 bug, owner-approved to fix now rather than defer).
**Impact on plan:** No architectural change — a one-line-split fix to an existing config file, landed through the phase's already-established promotion chain. No scope creep.

## Issues Encountered

None beyond the RTD tag-fetch bug documented above, which was found, fixed, and re-verified within this plan's own scope.

## User Setup Required

None remaining for this plan — both owner account actions (Task 1 RTD import, Task 3 TestPyPI trusted-publisher registration) are complete and confirmed. No further external configuration is needed before 06-13.

## Next Phase Readiness

- Read the Docs hosting half of ROADMAP SC2 is proven by a real, green, correctly-versioned build (`0.10.4.post7`), not just committed config.
- The `testpypi` GitHub environment exists and the matching TestPyPI trusted-publisher tuple is registered — 06-13 can dispatch `publish-testpypi.yml` against a satisfied precondition.
- No blockers carried forward. The only open item is cosmetic and self-resolving: RTD's `stable` version will continue to fail to build until `v0.11.0` is tagged, per the owner's explicit decision to leave it alone.

## Self-Check

- [x] `.readthedocs.yaml` post_checkout step contains two separate fetch lines (not one fused `--unshallow --tags`): confirmed by reading the file on disk
- [x] Commit `e9a3a98` exists in `git log`: confirmed
- [x] `main` at `20ef688` contains the fix (PR #19 → develop-gsd → promotion → PR #20 → main): confirmed by the chain of commits in `git log --oneline -5`
- [x] RTD badge and site checks reported in this SUMMARY reflect the plan's own `<verify>` commands, run against the real hosted project

## Self-Check: PASSED

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-30*
