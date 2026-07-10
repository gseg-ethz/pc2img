# Phase 1 — Branch Inventory (BRANCH-01)

**Authored:** 2026-07-09 (final task of Phase 1 execution)
**Scope:** classifies every branch ref that existed at phase start as live/dead with an
acted-on disposition, reporting the **final post-fold / post-prune / post-retire topology**.
**Confidence:** HIGH — every row is backed by a read-only git assertion re-run this session
(`git for-each-ref`, `git merge-base --is-ancestor`, `git rev-list --count`), cross-checked
against `01-RESEARCH.md §"Branch Inventory"`.

> This doc is an **internal planning record** (D-07). It lives under
> `.planning/phases/01-…/` and is stripped from the public `main` branch. Any publicly
> relevant distillation folds into the Phase 6 BC-01 breaking-change record if warranted.

---

## Ground rules applied (from CONTEXT.md decisions)

- **D-05:** dispositions are decided-and-recorded now; only **local** refs and **local**
  tags were touched this phase. **Every remote (GitHub) deletion is staged for Phase 6 ship**
  — no `git push --delete` ran this phase.
- **D-06:** an **archive tag** was created before pruning the salvage-worthy perspective ref.
- **Owner exclusion:** `develop/tomislav` (`origin/develop/tomislav`) is **EXCLUDED** from
  consolidation per the project owner and was left completely untouched.
- **Prune safety:** all local prunes used the self-guarding `git branch -d` (never `-D`).

---

## Classification table — all 13 branch refs (phase-start snapshot)

Ahead/behind is measured against `develop-gsd` (the single forward mainline). "This phase"
records the action actually completed across Plans 01–03.

| # | Branch ref | Live/Dead | Ahead/Behind vs `develop-gsd` | Disposition (this phase) | Rationale |
|---|------------|-----------|-------------------------------|--------------------------|-----------|
| 1 | `develop-gsd` | **LIVE (mainline)** | — | **Kept** — single forward-development mainline | Richest architecture; already contains all of `dev/v2`; the perspective fold lands here (via the phase branch) |
| 2 | `gsd/phase-01-branch-untangling-mainline-consolidation` (HEAD) | **LIVE (working)** | ahead / 0 behind | **Kept** — per-phase branch; merges back to `develop-gsd` at phase close (01-04) | Current phase branch = `develop-gsd` + the Phase 1 fold + planning commits |
| 3 | `main` | **LIVE (ship target)** | 2 / 54 | **Kept**; reconciliation + cleanup **deferred to Phase 6 ship** | Old published `v0.10.x` lineage; retained as the public release target. See "`main` divergence note" below |
| 4 | `dev/v2` (local) | DEAD | 0 / 7 | **Pruned local** in Plan 01-02 (self-guarding `-d` after `--unset-upstream`) | Fully contained in `develop-gsd`; its BSD-3-Clause tip is preserved in `develop-gsd`/HEAD |
| 5 | `dev/perspective_projection` (local) | DEAD | 6 / 18 | **Pruned local** in Plan 01-01 **after** the fold (was a pure ancestor of `origin/dev/perspective_projection`) | Stale snapshot 16 commits behind origin persp; subsumed once origin persp was folded |
| 6 | `feature/update_to_pchandler-1.0.0` (local) | DEAD | 0 / — | **Retired local this plan (01-03, Task 1)** via self-guarding `git branch -d` | Full ancestor of `develop-gsd` (tip `54c7100`); nothing to salvage — see "pchandler-1.0 finding" below |
| 7 | `feature/release-please` (local) | DEAD (bot) | 0 / — | **Pruned local** in Plan 01-02 (self-guarding `-d`) | Ancestor of `develop-gsd`; release-please automation artifact |
| 8 | `origin/dev/perspective_projection` | **LIVE (folded)** | 12 / 8 (pre-fold) | **Folded into the mainline** (Plan 01-01, `--no-ff`); **archive-tagged**; **remote deletion staged for Phase 6** | The only divergent source-carrying branch; carried the `PerspectiveProjection` strategy now on mainline |
| 9 | `origin/dev/v2` | DEAD | 0 / 8 | **Remote deletion staged for Phase 6**; local mirror untouched (`91b4ab6`) | Fully contained in `develop-gsd` (verified-and-recorded, not merged, in Plan 01-02) |
| 10 | `origin/main` | **LIVE (ship target mirror)** | 2 / 54 | **Kept**; cleanup **deferred to Phase 6 ship** | Remote of the public `main` ship target |
| 11 | `origin/release-please--branches--main` | LIVE (bot) | 3 / 54 | **Documented**; left to automation (bot-managed, off `main`) — no remote action | Active release-please PR branch tracking `main` |
| 12 | `origin/release-please/bootstrap/default` | DEAD (bot) | 0 / — | **Documented**; left to automation (bot-managed) — no remote action | Ancestor of `develop-gsd`; release-please bootstrap artifact |
| 13 | `origin/develop/tomislav` | **EXCLUDED (owner)** | 4 / 50 | **Untouched** — permanently excluded from consolidation per owner | Not part of consolidation; `develop/tomislav` is owner-owned |

**Ref-count reconciliation:** 13 rows == the 13 non-symbolic branch/remote refs present at
phase start (excludes annotated tags `v0*` / `v2.0.0a5` / `archive/*`, the `stash` ref if any,
and the symbolic `origin/HEAD`). This matches the 13-name coverage the plan's Task 2 verify
loop asserts.

---

## pchandler-1.0 finding (BRANCH-03 / D-04) — recorded verbatim in intent

`feature/update_to_pchandler-1.0.0` (tip `54c7100`) is a **full ancestor of `develop-gsd`**:

- `git rev-list develop-gsd..feature/update_to_pchandler-1.0.0` → **empty** (the branch adds
  **zero** commits over mainline).
- `git merge-base --is-ancestor 54c7100 develop-gsd` → **exit 0** (re-asserted this plan).

Its "Enforce named arguments approach in registry" intent (`54c7100`) already **survives in
the current tree**: the registry is `def register[S](self, identifier: str)` and
`def create(self, identifier: str, **kwargs)` — the `name → identifier` rename and the
kwargs-only `create` are both present (the old `v2/`-prefixed layout `54c7100` edited has since
been promoted to top-level `src/pc2img/strategies/registry.py`).

**Therefore there is NOTHING to salvage.** D-04's "salvage-note before retiring" is satisfied
by recording *this finding*; no note-extraction work remained. The action was a pure
convenience-label deletion, completed in Task 1 via the self-guarding `git branch -d`
(fully-merged → `-d` succeeded directly). No remote copy exists to stage (see Open Question 2
below), so BRANCH-03 remote-staging is a **no-op** this phase.

---

## Archive safety net (D-06)

Before pruning any perspective ref, Plan 01-01 created the archive tag:

- **`archive/dev-perspective_projection-pre-fold` → `8f0fae9`** (the pre-fold
  `origin/dev/perspective_projection` tip).

This is the D-06 safety net: the folded source is recoverable from the tag even after the
remote persp ref is eventually deleted in Phase 6. No prior `archive/*` namespace existed, so
the tag introduced no collision.

---

## `main` divergence note

`main` forks from `develop-gsd` at `f946268` ("docs: Create LICENSE"). Its 2 extra commits are
`69224a9` (a merge) and `ade40f8` (a *second, differently-hashed* BSD-3-Clause license switch —
the develop lineage carries its own as `e795ec0`). Both are semantically already present on
`develop-gsd`; **nothing on `main` needs salvaging.** `main` stays as the public ship target;
its reconciliation with the v2 lineage is a Phase 6 concern.

---

## Bot / automation refs

`feature/release-please`, `origin/release-please--branches--main`, and
`origin/release-please/bootstrap/default` are **release-please bot-managed** (inferred from ref
names/dates — RESEARCH assumption A2; even if mislabeled, the disposition is unchanged).
Disposition: **document, leave the remotes to the automation, prune only the stale local copy
where safe.** The stale local `feature/release-please` (an ancestor of `develop-gsd`) was pruned
in Plan 01-02; the two `origin/release-please*` remotes are untouched.

---

## Remote deletions staged for Phase 6 ship (D-05)

> **Scope clarification (2026-07-10):** this staged list is **former/legacy branch refs only**
> — the pre-existing non-GSD remotes inventoried at Phase 1 start plus the `main` reconciliation.
> It does **NOT** include GSD per-phase workflow branches (`gsd/phase-*`, `gsd/quick-*`), which
> follow normal GSD ship hygiene and have their remote heads deleted on PR merge (e.g.
> `gsd/phase-03.1-…` was deleted when PR #10 merged on 2026-07-10). D-05 gates only the legacy
> cleanup below, not routine phase-branch teardown.

No remote refs were deleted this phase. The following are **staged for Phase 6 ship** (executed
alongside the `main` cleanup, not now):

- `origin/dev/v2` — fully contained in `develop-gsd`.
- `origin/dev/perspective_projection` — folded; recoverable via the archive tag above.
- `origin/main` cleanup — reconciliation with the v2 lineage.
- release-please remotes (`origin/release-please--branches--main`,
  `origin/release-please/bootstrap/default`) — left to bot automation; revisit at ship if stale.

A **fetch-time re-check governs remote pchandler-1.0 staging** (Open Question 2): if a remote
`origin/feature/update_to_pchandler-1.0.0` ever appears after a `git fetch`, record it as
"staged for Phase 6" rather than deleting it. As of this phase, no such remote ref exists, so
there is nothing to stage.

---

## Known-deferred items

Two nits are intentionally carried forward — recorded here so nothing is silently lost:

1. **Stale upstream config on `feature/update_to_pchandler-1.0.0`** (review finding #5): the
   retired local label carried a configured `remote = origin` and
   `merge = refs/heads/feature/update_to_pchandler-1.0.0` even though **no matching
   `origin/feature/update_to_pchandler-1.0.0` ref exists** (a **stale upstream** pointer). No
   separate action was needed — `git branch -d` in Task 1 cleared the branch's config along with
   the label (verified: `git config --get-regexp '^branch\.feature/update_to_pchandler-1\.0\.0\.'`
   now returns nothing). Recorded for completeness; **resolved**.

2. **EOF-whitespace nit in the folded perspective WIP** (review finding #4):
   `src/pc2img/strategies/projection.py` ends with a **new blank line at EOF** (per
   `git diff --check`, the folded change introduced a trailing blank line after
   `return uv[mask, :], mask`). This arrives with the D-03-fenced `PerspectiveProjection` WIP
   surface and is **intentionally left for the Phase 4/5 cleanup** of the perspective code
   (whose math is owned by Phase 4 and coverage by Phase 5). Not fixed this phase — Phase 1's
   job was only to land the fold cleanly.

---

## Success-criteria coverage advanced by this inventory

- **SC1 (inventory):** this doc exists under `.planning/phases/01-…/` and classifies all 13
  branch refs with live/dead + disposition + rationale; `develop/tomislav` EXCLUDED; every
  remote deletion marked "staged for Phase 6".
- **SC3 (pchandler-1.0):** `git merge-base --is-ancestor 54c7100 develop-gsd` → exit 0
  (recorded above); local label `feature/update_to_pchandler-1.0.0` deleted (Task 1).

---

*Phase: 01-branch-untangling-mainline-consolidation*
*Deliverable: BRANCH-01 (branch inventory) + BRANCH-03 closeout*
