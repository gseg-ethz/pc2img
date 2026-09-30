---
phase: 06-publication-hardening-downstream-migration-record
plan: 09
subsystem: infra
tags: [release-please, github-apps, promotion-commit, worktree, breaking-change-footer]

# Dependency graph
requires:
  - phase: 06-publication-hardening-downstream-migration-record (plan 18)
    provides: "origin/develop-gsd tip (d4aa911) carrying every fix from both review rounds — the tree this plan's promotion commit is built from"
provides:
  - "Repo secrets RELEASE_APP_ID / RELEASE_APP_PRIVATE_KEY on gseg-ethz/pc2img (Task 1, owner action)"
  - "Local promotion commit 0819b2b in the gitignored worktree _scrap/pc2img-promotion: parent origin/main (ade40f8), tree identical to origin/develop-gsd minus .planning/ and .claude/, subject feat!:, BREAKING CHANGE: footer (self-contained, no file pointer), Release-As: 0.11.0 footer — verified mechanically, not pushed"
affects: ["06-10 (consumes the worktree to push and open the go/no-go gate)"]

# Actuals (#2632)
actuals:
  tokens: 500
  tasks: 2
  commits: 1
  plan_head_before: 070a52f268a5eaa572cadf0c20f6e66ab73629f3
  plan_head_after: 0df3305f568568d21d36d479e30d182b4ed860f5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Filtered-promotion worktree pattern: git worktree add off origin/main, git rm -r . + checkout origin/develop-gsd -- ., then git rm --cached the strip list (.planning/, .claude/) and rm -rf the working-tree copies, so the index and working tree agree before commit"

key-files:
  created: []
  modified: []

key-decisions:
  - "Task 2's fifth automated <verify> check (git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' HEAD | grep -E '^v0\\.10\\.4-1-g') fails literally: origin/main sits FOUR commits ahead of the v0.10.4 tag (cd9c37d, f946268, 69224a9, ade40f8 — pre-existing LICENSE/merge housekeeping on main, documented in Phase 1's 01-BRANCH-INVENTORY.md 'main divergence note' and explicitly deferred to Phase 6 reconciliation, not new information). The promotion commit is exactly one commit past origin/main's actual tip — already proven by check 1's `HEAD^ == origin/main` assertion — so the check's assumption that main sits exactly at the tag (0 commits ahead) was wrong at authoring time, not the artifact. Treated as a Rule 1 (auto-fixed bug) in the plan's own verification script: substituted the equivalent, correct assertion `git rev-list --count origin/main..HEAD` == 1 (see Deviations) rather than rewriting git history to force the literal string to match."

requirements-completed: []  # CICD-02 not ready: gsd_run query requirements.ready-ids reports 0/1 — sibling plans 06-10..06-13 in this phase also declare CICD-02 and have no SUMMARY yet (shared-ID gate, #2388)

coverage:
  - id: D1
    description: "Release App granted access to pc2img and RELEASE_APP_ID/RELEASE_APP_PRIVATE_KEY secrets stored (Task 1, owner action)"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "gh secret list --repo gseg-ethz/pc2img --json name --jq '.[].name' lists RELEASE_APP_ID and RELEASE_APP_PRIVATE_KEY alongside CODECOV_TOKEN, NIME_RELEASE_PLEASE_TOKEN, RULESET_APP_ID, RULESET_APP_PRIVATE_KEY (6 total)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Filtered promotion commit built locally in _scrap/pc2img-promotion: parent origin/main, tree == develop-gsd minus .planning/+.claude/, zero planning-vocabulary hits, feat!/BREAKING CHANGE/Release-As footers present exactly once each, migration record absent from the tree, RULESETS.md/RELEASE.md present"
    requirement: "CICD-02"
    verification:
      - kind: other
        ref: "cd _scrap/pc2img-promotion && test \"$(git rev-parse HEAD^)\" = \"$(git rev-parse origin/main)\" && ... && echo promotion-tree-ok"
        status: pass
      - kind: other
        ref: "cd _scrap/pc2img-promotion && git log -1 --format=%B HEAD | grep -c '^Release-As: 0.11.0$' / '^BREAKING CHANGE: ' ; git log -1 --format=%s HEAD | grep -c '^feat!: '"
        status: pass
      - kind: other
        ref: "cd _scrap/pc2img-promotion && test ! -e MIGRATION-v0.11.md && test -f RULESETS.md && test -f RELEASE.md && echo footer-and-docs-ok"
        status: pass
      - kind: other
        ref: "cd _scrap/pc2img-promotion && git ls-files | grep -v rrim-eth-signoff.md | xargs grep -lE <planning-vocabulary regex> | wc -l == 0"
        status: pass
      - kind: other
        ref: "cd _scrap/pc2img-promotion && git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' HEAD (literal check fails per key-decisions; substitute git rev-list --count origin/main..HEAD == 1 passes)"
        status: pass
    human_judgment: false

# Metrics
duration: ~20min (this continuation: Task 2 build + verification; Task 1 owner action completed and evidence-verified in the prior session)
completed: 2026-09-30
status: complete
---

# Phase 6 Plan 09: Filtered Promotion Commit + Release App Grant Summary

**Built and mechanically verified the first `develop-gsd` → `main` promotion commit (0819b2b) in a throwaway worktree — planning paths stripped, `feat!`/`BREAKING CHANGE`/`Release-As: 0.11.0` footers attached — without pushing anything; the release App grant (Task 1, owner action) that release-please needs on `main` is already in place.**

## Performance

- **Duration:** ~20 min (this continuation covered Task 2 build + full verification; Task 1 was completed and its evidence independently re-verified by the orchestrator in the prior session, per this plan's `<continuation>` block)
- **Completed:** 2026-09-30T09:05:02Z
- **Tasks:** 2 (both complete)
- **Files modified:** 0 in the main checkout (Task 2's output is a commit inside the gitignored worktree `_scrap/pc2img-promotion`, not a change to the tracked repository)

## Accomplishments

- **Task 1 (owner action, completed and re-verified prior session):** pc2img added to the `gseg-release-please` App's repository selection; `RELEASE_APP_ID` and `RELEASE_APP_PRIVATE_KEY` stored as repo secrets — confirmed present via `gh secret list` (6 secrets total).
- **Task 2:** Built the filtered promotion commit. `git fetch origin` confirmed `origin/develop-gsd` at `d4aa911` (06-18's merge tip) and `origin/main` at `ade40f8`. Asserted the strip list is real (`.planning/`/`.claude/` non-empty on develop-gsd) and that no other agent-specific dot-directory is tracked besides `.github`. Created the worktree idempotently at `_scrap/pc2img-promotion` off `origin/main`, replaced its tree with `origin/develop-gsd`'s, and stripped `.planning/` and `.claude/` from both the index and the working tree. Committed (author = owner's git identity, `Nicholas Meyer <nixton.meyer@gmail.com>`) as `0819b2b`: subject `feat!: publish the 2.x architecture as the 0.11 release line`, a plain-words body, and a trailing footer block with a self-contained `BREAKING CHANGE:` summary (every clause traced to a `BC-P2I` row in `.planning/MIGRATION-v0.11.md`, per the plan's tracing requirement — see Verification below) and `Release-As: 0.11.0`. Left the worktree in place, unpushed, for plan 06-10.

## Task Commits

1. **Task 1: Owner action — release App grant + secrets** — no local commit (remote-only: GitHub App installation config + `gh secret set`; verified in the prior session)
2. **Task 2: Build and verify the filtered promotion commit** — no commit in the main checkout; the commit it produced is `0819b2b` inside the separate worktree `_scrap/pc2img-promotion` (parent `ade40f8` = `origin/main`), per the plan's explicit exception to normal per-task commit protocol

**Plan metadata:** (this SUMMARY's own commit, made in the main checkout)

## Files Created/Modified

- None in the main checkout (`/scratch/31_pc2img`).
- `_scrap/pc2img-promotion/` (gitignored worktree, outside the tracked tree) — holds commit `0819b2b`, left in place for plan 06-10 to push from and read main's workflow files from.

## PROMOTION_SHA and commit detail

```
PROMOTION_SHA=0819b2b754672829f45ac7e169de4e4707821266
parent (HEAD^) = ade40f85a18729290d50e05ce5da0c2d98f45c20 (origin/main)
```

Full commit message:

```
feat!: publish the 2.x architecture as the 0.11 release line

Consolidates the point-cloud-to-raster pipeline onto a single mainline built
around pluggable projection, interpolation, and feature strategies, replacing
the prior 0.10 module layout wholesale. Adopts branch protection and a full
publication CI/CD pipeline (lint, tests, docs, PyPI publish with attestations)
matching the sibling GSEG library template. Refreshes project metadata,
README, and citation information for a real PyPI release. Migration notes for
downstream users are summarised in the BREAKING CHANGE footer below.

BREAKING CHANGE: the 0.10 module layout is replaced wholesale by the 2.x architecture (strategies, features and image_cache packages). Registry misses raise RegistryLookupError; the never-functional make_generator factory and a dead duplicate convert_to_image are removed; matplotlib moves to the optional viz extra; the disk cache codec changes from pickle to .npy plus a JSON sidecar, so a cache directory persisted by an earlier build must be regenerated; a wrapping field of view, a 4x4 rotation_matrix and a non-pinhole intrinsics matrix are now rejected; nanconv accumulates in float32 and no longer mutates its input; DiskBackedImageData arithmetic returns a plain ndarray instead of raising; RRIM feature-name validation moves to request time and the z-factor token uses shortest round-trip formatting; numpy 2.x, pchandler 2.1 and GSEGUtils 0.5.3 or newer are required; the v2.0.0a5 tag is retired, so git-based pins on the 2.0.0a line must move to pc2img ~= 0.11 from PyPI.
Release-As: 0.11.0
```

`git diff --stat origin/main HEAD | tail -1` (in the worktree):

```
 86 files changed, 16317 insertions(+), 2811 deletions(-)
```

**Footer clause traceability (every clause traced to a `BC-P2I` row in `.planning/MIGRATION-v0.11.md`; none dropped):**

| Footer clause | Traces to |
|---|---|
| "the 0.10 module layout is replaced wholesale by the 2.x architecture" | `01-BRANCH-INVENTORY.md` "main divergence note" (old `main` is the pre-2.x lineage; the promotion replaces its tree wholesale) |
| "Registry misses raise RegistryLookupError" | BC-P2I-001 |
| "the never-functional make_generator factory and a dead duplicate convert_to_image are removed" | BC-P2I-004, BC-P2I-005 |
| "matplotlib moves to the optional viz extra" | BC-P2I-006 |
| "the disk cache codec changes from pickle to .npy plus a JSON sidecar...must be regenerated" | BC-P2I-010 |
| "a wrapping field of view, a 4x4 rotation_matrix and a non-pinhole intrinsics matrix are now rejected" | BC-P2I-007, BC-P2I-008, BC-P2I-015 |
| "nanconv accumulates in float32 and no longer mutates its input" | BC-P2I-009 |
| "DiskBackedImageData arithmetic returns a plain ndarray instead of raising" | BC-P2I-011 |
| "RRIM feature-name validation moves to request time and the z-factor token uses shortest round-trip formatting" | BC-P2I-014, BC-P2I-016 |
| "numpy 2.x, pchandler 2.1 and GSEGUtils 0.5.3 or newer are required" | BC-P2I-002, BC-P2I-012 |
| "the v2.0.0a5 tag is retired...move to pc2img ~= 0.11 from PyPI" | BC-P2I-019, BC-P2I-020 |

No clause was dropped — every clause in the footer traced to a row.

## Decisions Made

See `key-decisions` in the frontmatter above. Summary: the plan's fifth automated `<verify>` check for Task 2 (`git describe ... | grep -E '^v0\.10\.4-1-g'`) embeds an incorrect assumption that `origin/main` sits exactly at the `v0.10.4` tag. It doesn't — `origin/main` is four commits ahead of that tag (`cd9c37d`, `f946268`, `69224a9`, `ade40f8`), a pre-existing state fully documented in Phase 1's `01-BRANCH-INVENTORY.md` "`main` divergence note" (one of this task's own `<read_first>` files) and explicitly deferred to Phase 6. This is a Rule 1 (auto-fixed bug) in the verification script itself, not in the promotion artifact: the artifact's correctness — that its parent is exactly `origin/main`'s current tip — is independently and completely proven by check 1 (`test "$(git rev-parse HEAD^)" = "$(git rev-parse origin/main)"`, which passed). The substitute assertion below proves the same intent the literal check was reaching for:

```
$ cd _scrap/pc2img-promotion && git rev-list --count origin/main..HEAD
1
```

## Verification

All five of Task 2's automated `<verify>` checks were run. Four pass exactly as written; the fifth's literal string assertion fails for the documented reason above, with an equivalent substitute check passing.

```
--- verify 1: promotion-tree-ok ---
promotion-tree-ok
--- verify 2: footer counts (Release-As / BREAKING CHANGE / feat!) ---
1
1
1
--- verify 3: footer-and-docs-ok ---
footer-and-docs-ok
--- verify 4: planning-vocabulary hit count ---
0
--- verify 5 (literal, FAILS — see Decisions): git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' HEAD ---
v0.10.4-5-g0819b2b   (expected pattern assumed 0 pre-existing commits past v0.10.4; there are 4)
--- verify 5 (substitute, PASSES): git rev-list --count origin/main..HEAD ---
1
```

Must-haves and acceptance criteria from the plan frontmatter/tasks:
- pc2img in the release App's repository selection + secrets present: verified (Task 1).
- Promotion commit exists, parent `origin/main`, tree == `develop-gsd` minus strip list, `feat!`/`BREAKING CHANGE`/`Release-As` footers present once each, zero planning-vocabulary hits: verified.
- Nothing pushed: confirmed — no `git push` was run at any point in this plan; `origin/main` remains `ade40f8`.
- Worktree at deterministic gitignored path `_scrap/pc2img-promotion`, created idempotently (stale-attempt removal + prune run before `git worktree add`): done and confirmed via `git worktree list`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected Task 2's fifth `<verify>` check's tag-distance assumption**
- **Found during:** Task 2, running the plan's five automated `<verify>` commands
- **Issue:** `git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*' HEAD | grep -E '^v0\.10\.4-1-g'` assumes `origin/main` sits exactly at the `v0.10.4` tag (0 commits ahead), so the promotion commit would land at `-1-g`. `origin/main` is actually 4 commits ahead of that tag (pre-existing LICENSE/merge housekeeping, documented in Phase 1's `01-BRANCH-INVENTORY.md`), so the real output is `v0.10.4-5-g0819b2b`.
- **Fix:** Did not alter git history or the tag to force the literal string to match (that would corrupt release history). Instead verified the check's actual intent — that the promotion commit sits exactly one commit past `origin/main`'s current tip — via `git rev-list --count origin/main..HEAD` (`1`), which is also implied by check 1's already-passing `HEAD^ == origin/main` assertion.
- **Files modified:** None (verification-only; no source or plan file changed)
- **Verification:** `git rev-list --count origin/main..HEAD` → `1`; check 1's `promotion-tree-ok` output
- **Committed in:** N/A (no code change — a verification substitution, documented here for the record)

---

**Total deviations:** 1 auto-fixed (1 Rule-1 bug in a plan verification script's assumption).
**Impact on plan:** None on the promotion artifact's correctness — every invariant the plan actually cares about (parent = `origin/main`, tree = `develop-gsd` minus strip list, footers, zero vocabulary hits, nothing pushed) is proven. The one literal string check that failed was checking a stale assumption about pre-existing repository state that Phase 1 had already documented and deferred.

## Issues Encountered

None beyond the documented verification-script deviation above.

## User Setup Required

None — Task 1's user-setup (release App grant + secrets) was completed and independently re-verified in the prior session (see `<continuation>` evidence in this plan's dispatch).

## Next Phase Readiness

- The exact commit (`0819b2b`) that will become public `main` exists locally in `_scrap/pc2img-promotion`, verified, and unpushed. Plan 06-10's first task is the blocking go/no-go decision on this SHA, immediately before the push it gates.
- `origin/main` remains at `ade40f8`, unchanged. `origin/develop-gsd` remains at `d4aa911`, unchanged.
- The worktree `_scrap/pc2img-promotion` was left in place (not removed) per the plan's explicit instruction — plan 06-10 consumes it (pushes from it, reads main's workflow files from it, then removes it).
- No blockers carried forward.

## Self-Check

- [x] `_scrap/pc2img-promotion` exists as a registered worktree: confirmed via `git worktree list`
- [x] Commit `0819b2b754672829f45ac7e169de4e4707821266` exists: confirmed via `git rev-parse HEAD` inside the worktree
- [x] `git rev-parse HEAD^` inside the worktree equals `git rev-parse origin/main` (`ade40f8`): confirmed
- [x] `git diff --name-only origin/develop-gsd HEAD` inside the worktree, filtered to exclude `.planning/`/`.claude/`, is empty: confirmed
- [x] `RELEASE_APP_ID` / `RELEASE_APP_PRIVATE_KEY` present via `gh secret list --repo gseg-ethz/pc2img`: confirmed (6 secrets total)
- [x] Nothing pushed: `origin/main` still `ade40f8`, `origin/develop-gsd` still `d4aa911`, no `git push` invoked at any point

## Self-Check: PASSED

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-30*

## Post-execution amendment (owner decision at the 06-10 go/no-go, 2026-09-30)

The executor's original commit was `7e53d892f568746c59c4ea32069b3904005120a1`. At the go/no-go the owner chose
"reword first": the body's last sentence pointed outside readers at internal planning history on
develop-gsd, which is permanent public history on `main` once pushed. The orchestrator amended only the
body in `_scrap/pc2img-promotion` (subject, footers, tree, parent and author unchanged) to end with
"Migration notes for downstream users are summarised in the BREAKING CHANGE footer below." The new
PROMOTION_SHA is `0819b2b754672829f45ac7e169de4e4707821266`. All five plan checks were re-run against it: tree-ok,
footer counts 1/1/1, footer-and-docs-ok, 0 vocabulary hits (plus 0 planning terms in the message), and
`git describe` = `v0.10.4-5-g0819b2b` (same known deviation as above). The diff stat is unchanged.
