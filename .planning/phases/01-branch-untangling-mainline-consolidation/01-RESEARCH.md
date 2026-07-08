# Phase 1: Branch Untangling & Mainline Consolidation - Research

**Researched:** 2026-07-08
**Domain:** Git DAG topology / branch consolidation (mechanical, not code-feature)
**Confidence:** HIGH (every claim below is grounded in a read-only git command run against the live repo this session)

## Summary

This is a live-DAG verification pass, not an algorithm/library investigation. I re-ran the
git forensics that `01-CONTEXT.md` recorded on 2026-07-08 and the topology is now fully pinned.
**Most of CONTEXT's claims hold, with two material corrections and one refinement.**

The headline facts: `develop-gsd` (9832d90) already contains all of `dev/v2` (both local
`e795ec0` and remote `91b4ab6` are ancestors), so consolidating `dev/v2` is genuinely
**verify-and-document** — Success Criterion 2 is already satisfied on disk. The *only* branch
carrying divergent development not in `develop-gsd` is `origin/dev/perspective_projection`
(8f0fae9). Its merge-base with `develop-gsd` is exactly the `dev/v2` tip `91b4ab6`, and the
two branches' change-sets since that base touch **disjoint files** (develop-gsd changed only
docs/config/LICENSE/pyproject; perspective changed only `strategies/projection.py` +
`features/manager.py`), so the fold is a **guaranteed clean 3-way merge** — no conflict-prone
paths exist.

**Correction 1 (BRANCH-03 / D-04):** `feature/update_to_pchandler-1.0.0` (tip `54c7100`) is
**already a full ancestor of `develop-gsd`** — the branch adds *zero* commits over mainline,
and its named-arguments registry change is present in the current tree
(`create(self, identifier: str, **kwargs)`). The "diff-review then salvage `54c7100`" task is
**moot**: there is nothing to salvage because it is already folded in. Disposition collapses to
"retire the stale label" (a pure convenience-ref deletion), not a review.

**Correction 2:** local `dev/perspective_projection` is **16 commits behind** origin, not 10 as
CONTEXT states. It is a pure ancestor of the remote (0 ahead of origin), so the remote is
authoritative exactly as decided.

**Primary recommendation:** Fold `origin/dev/perspective_projection` into `develop-gsd` with a
normal merge (clean by construction); archive-tag the remote persp ref before pruning locals;
record BRANCH-03 as "already-merged → retire label"; produce the inventory doc; prune only the
locally-fully-merged branches; stage all remote deletions for Phase 6.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Fold the **entire** `origin/dev/perspective_projection` into `develop-gsd` (including
  the new `PerspectiveProjection` strategy). Merge from the **authoritative remote**, not the
  stale local branch. Merge-base already *is* the `dev/v2` tip → clean merge.
- **D-02 (scope amendment, owner-approved, NOT scope creep):** Folding `PerspectiveProjection`
  overrides the "New projection/interpolation/feature algorithms" Out-of-Scope entry. PROJECT.md
  and REQUIREMENTS.md must be amended so the mainline no longer contradicts the milestone docs.
- **D-03 (downstream consequence):** `PerspectiveProjection` now lives on mainline → Phase 4
  (soundness) and Phase 5 (test coverage) now own it.
- **D-04:** `feature/update_to_pchandler-1.0.0` → **diff-review then retire.** Salvage any still-
  relevant change (e.g. `54c7100` named-args) into a note before retiring. *(Research finding
  below shows this is already merged — see Correction 1; the review is effectively a formality.)*
- **D-05:** Record dispositions now; prune only **safe local** branches. **Remote (GitHub)
  deletions are staged for Phase 6 ship** — out of scope this phase.
- **D-06:** Create an **archive tag** before pruning anything dead-but-salvage-worthy (notably the
  folded `origin/dev/perspective_projection`).
- **D-07:** Inventory doc home is `.planning/phases/01-.../` (internal; stripped from public
  `main`). Distill publicly-relevant bits into the Phase 6 BC-01 record if warranted.
- **D-08:** "Disposition" = decided-and-recorded (+ local action where safe) — NOT remote execution.

### Claude's Discretion
- Exact inventory doc filename/format within the phase dir.
- Which local branches are "safe" to prune vs keep as local convenience.
- Classification of housekeeping/automation branches (`feature/release-please`,
  `origin/release-please--branches--main`, `origin/release-please/bootstrap/default`): treat as
  bot-managed → document disposition, leave remote alone, prune stale local copies where safe.
  `develop/tomislav` untouched (owner-excluded); `main` retained as public ship target.
- Whether the perspective fold executes in this phase or is staged as its first plan — planner's call.

### Deferred Ideas (OUT OF SCOPE)
- Actual GitHub remote-branch deletions — staged now, executed at Phase 6 ship with `main` cleanup.
- Public distillation of the branch inventory — fold into Phase 6 BC-01 if warranted.
- `develop/tomislav` — permanently excluded from consolidation per owner; untouched (not deferred).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BRANCH-01 | A branch inventory documents which branches carry live development vs are dead (`develop/tomislav` excluded) | Full inventory with verified ahead/behind + merge status for all 14 refs below (see `## Branch Inventory`) |
| BRANCH-02 | The richer `dev/*` architecture is consolidated into `develop-gsd` as the single forward-development mainline | `dev/v2` (local `e795ec0` + remote `91b4ab6`) already ancestors of `develop-gsd` → verify-and-document. `origin/dev/perspective_projection` fold is a clean 3-way merge (disjoint file sets) — verified below |
| BRANCH-03 | The stale `feature/update_to_pchandler-1.0.0` branch is analyzed and dispositioned (salvage or retire) | Branch tip `54c7100` is a **full ancestor of `develop-gsd`** (adds 0 commits); named-args intent survives in current tree → retire, nothing to salvage (see `## pchandler-1.0 Salvage Analysis`) |
</phase_requirements>

## Ground-Truth Ref Table (verified 2026-07-08)

`git for-each-ref` snapshot, annotated with ahead/behind vs `develop-gsd` and merge status:

| Ref | Tip | Last commit | vs develop-gsd (ahead/behind) | Merged into develop-gsd? |
|-----|-----|-------------|-------------------------------|--------------------------|
| `develop-gsd` | 9832d90 | 2026-07-08 | — | (self / mainline) |
| `gsd/phase-01-…` (HEAD) | eec7c32 | 2026-07-08 | 2 / 0 | contains develop-gsd + 2 planning commits |
| `dev/v2` (local) | e795ec0 | 2026-07-02 | 0 / 7 | **YES (ancestor)** |
| `origin/dev/v2` | 91b4ab6 | 2025-11-06 | 0 / 8 | **YES (ancestor)** |
| `origin/dev/perspective_projection` | 8f0fae9 | 2025-11-26 | 12 / 8 | **NO** — the one divergent live branch |
| `dev/perspective_projection` (local) | ae69343 | 2025-08-15 | 6 / 18 | NO (but pure ancestor of origin persp) |
| `feature/update_to_pchandler-1.0.0` | 54c7100 | 2025-06-11 | 0 / — | **YES (ancestor)** — adds nothing |
| `feature/release-please` (local) | 121eb55 | 2025-04-15 | 0 / — | **YES (ancestor)** |
| `origin/release-please/bootstrap/default` | c7a9623 | 2025-04-15 | 0 / — | **YES (ancestor)** |
| `origin/release-please--branches--main` | 869d5c6 | 2026-07-02 | 3 / 54 | NO (bot PR branch off main) |
| `main` / `origin/main` | ade40f8 | 2026-07-02 | 2 / 54 | NO (old published lineage) |
| `origin/develop/tomislav` | a28f266 | 2026-07-02 | 4 / 50 | NO — **EXCLUDED (owner)** |

## CONTEXT.md Claim Verification

| # | CONTEXT claim (2026-07-08) | Verdict | Evidence |
|---|----------------------------|---------|----------|
| 1 | Merge-base(`develop-gsd`, `origin/dev/perspective_projection`) *is* the `dev/v2` tip `91b4ab6` | **CONFIRMED** | `git merge-base develop-gsd origin/dev/perspective_projection` → `91b4ab6…`; identical to `git rev-parse origin/dev/v2` |
| 2 | `develop-gsd` already contains all of `dev/v2` | **CONFIRMED** | `git merge-base --is-ancestor` → YES for both local `e795ec0` and remote `91b4ab6`; `dev/v2..develop-gsd` = 7 commits, reverse = 0 |
| 3 | `develop-gsd` is strictly ahead of local `dev/v2`, adding "license + GSD docs" | **CONFIRMED, refined** | `develop-gsd` adds 7 commits over **local** `dev/v2` (all docs/config); the BSD-3-Clause commit `e795ec0` is itself the **local `dev/v2` tip**, so it's the license that `develop-gsd` adds over **`origin/dev/v2`** (8 commits), not over local. Essence holds. |
| 4 | Consolidating `dev/v2` is verify-and-document, not a merge (SC2 met) | **CONFIRMED** | Both `dev/v2` refs are ancestors of `develop-gsd`; nothing to merge |
| 5 | `origin/dev/perspective_projection` is the only branch with divergent dev not in `develop-gsd` (SC4) | **CONFIRMED** | Only non-excluded, non-bot ref that is UNMERGED *and* carries source-code deltas |
| 6 | Remote perspective is authoritative; local is 10 commits behind | **CORRECTED** | Local persp is **16 behind** origin (not 10), 0 ahead; `git merge-base --is-ancestor` confirms local tip `ae69343` is a pure ancestor of origin. Remote authoritative — confirmed. |
| 7 | History shows duplicated/rebased commits across `dev/*` (tangled DAG) | **CONFIRMED** | Duplicate subjects with distinct hashes: "feat: added PerspectiveProjection strategy" (`fc15915` & `dc257e4`), "feat: adaptions to enable perspective projection" (`862da83` & `e441db3`), "chore: update import of pointclouddata…" (`4de625a` & `5077b8b`). Also the license switch exists twice: `e795ec0` (dev lineage) vs `ade40f8` (main lineage). |
| 8 | `54c7100` is a salvage candidate on `feature/update_to_pchandler-1.0.0` | **CORRECTED (moot)** | `54c7100` is a **full ancestor of `develop-gsd`**; the branch adds 0 commits over mainline; its named-args change is live in the current tree. Nothing to salvage. See below. |

## The perspective_projection Fold — Merge Safety (BRANCH-02 / D-01)

**Merge-base:** `91b4ab6` (= `dev/v2` tip, = `origin/dev/v2`). Verified identical three ways.

**Commits `origin/dev/perspective_projection` adds over the merge-base** (`git rev-list 91b4ab6..origin/dev/perspective_projection`, 12 commits incl. merges):

```
8f0fae9 Merge remote-tracking branch 'origin/dev/v2' into dev/perspective_projection
3570240 fix: error of missing abstract function implementation
a6ccd1f Merge remote-tracking branch 'origin/dev/perspective_projection' into …
e441db3 feat: adaptions to enable perspective projection      <- dup subject
5077b8b chore: update import of pointclouddata and install location (temp for dev)  <- dup
dc257e4 feat: added PerspectiveProjection strategy            <- dup subject
ae69343 fix: implement all abstract classes for Perspective projection  (= local persp tip)
3d94a54 Merge remote-tracking branch 'origin/dev/v2' into dev/perspective_projection
862da83 feat: adaptions to enable perspective projection      <- dup subject
4de625a chore: update import of pointclouddata and install location (temp for dev)  <- dup
2846bfc chore: update gitignore not to track idea files
fc15915 feat: added PerspectiveProjection strategy            <- dup subject
```

**Why the merge is clean (guaranteed, not merely likely):** the two branches' change-sets since
the shared base `91b4ab6` touch **disjoint file sets**:
- `develop-gsd` changed over base: `LICENSE`, `pyproject.toml`, `.gitignore`, `.claude/CLAUDE.md`,
  and `.planning/**` — **no `src/` files**.
- `origin/dev/perspective_projection` changed over base: only `src/pc2img/strategies/projection.py`
  and `src/pc2img/features/manager.py`.

Because no file is modified on both sides, a 3-way merge has no overlapping hunks → no conflicts.
**Net effect of the fold** (`git diff 91b4ab6 origin/dev/perspective_projection`) is tiny — ~37
inserted / 4 deleted lines across 2 files:
- `projection.py`: adds `perspective` to the `ProjectionName` Literal, imports
  `scipy.spatial.transform.Rotation`, `pchandler.geometry.transforms._TransformArray`, and
  `GSEGUtils.base_types` shape types; registers a new `@PROJECTIONS.register("perspective")
  PerspectiveProjection` class (~32 lines).
- `manager.py`: removes one stray blank line.

**Landmine flagged for Phase 4/5 (D-03), NOT for this phase:** the folded `PerspectiveProjection`
is **work-in-progress / not runnable as-is**: `project_raw()` and `inverse_projection()` just
`raise NotImplementedError`; `project()` does `(self.projection_matrix @ self.rotation_matrix) @ pcd`
(matmul directly against a `PointCloudData`) and reaches into private pchandler API
(`_TransformArray`) and `GSEGUtils.base_types`. This is exactly the "added surface Phase 4/5 must
account for" that D-03 anticipates. Phase 1's job is only to land it on mainline cleanly; do **not**
try to fix or validate the projection math here.

## pchandler-1.0 Salvage Analysis (BRANCH-03 / D-04)

- `git rev-list develop-gsd..feature/update_to_pchandler-1.0.0` → **empty** (branch adds 0 commits).
- `git merge-base develop-gsd feature/update_to_pchandler-1.0.0` → `54c7100` (= the branch tip).
- `git merge-base --is-ancestor 54c7100 develop-gsd` → **YES**.

The entire branch — including the flagged `54c7100` "Enforce named arguments approach in registry"
— is already an ancestor of `develop-gsd`. `54c7100` edited `src/pc2img/v2/strategies/registry.py`
(the old `v2/`-prefixed layout); that layout has since been promoted to top-level
`src/pc2img/strategies/registry.py`, and **its intent survives**: the current tree's registry is
`def register[S](self, identifier: str)` and `def create(self, identifier: str, **kwargs: Any)`
— i.e. the `name → identifier` rename and the kwargs-only `create` from `54c7100` are both present.

**Disposition:** retire. There is nothing to salvage — the branch is a stale label pointing into
`develop-gsd`'s own history. D-04's "salvage-note before retiring" is satisfied by recording *this
finding* (already-merged, intent-preserved). No note-extraction work remains. The local label
`feature/update_to_pchandler-1.0.0` is safe to delete immediately (fully merged); the remote copy
(if any) is staged for Phase 6.

## Branch Inventory (BRANCH-01)

Proposed live/dead classification with disposition. `develop/tomislav` marked EXCLUDED per owner.

| Branch | Live/Dead | Ahead/Behind develop-gsd | Disposition (this phase) | Rationale |
|--------|-----------|--------------------------|--------------------------|-----------|
| `develop-gsd` | **LIVE (mainline)** | — | Keep; becomes single forward mainline | Richest architecture; contains all dev/v2 |
| `gsd/phase-01-…` (HEAD) | **LIVE (working)** | 2 / 0 | Keep; per-phase branch, merges back to develop-gsd | Current phase branch = develop-gsd + 2 planning commits |
| `dev/v2` (local) | DEAD | 0 / 7 | Prune local (safe — ancestor); archive-tag optional | Fully contained in develop-gsd |
| `origin/dev/v2` | DEAD | 0 / 8 | Stage remote deletion for Phase 6 | Fully contained in develop-gsd |
| `origin/dev/perspective_projection` | **LIVE (to fold)** | 12 / 8 | **Fold into develop-gsd**, then archive-tag, stage remote deletion for Phase 6 | Only divergent source-carrying branch |
| `dev/perspective_projection` (local) | DEAD | 6 / 18 | Prune local **after** fold (pure ancestor of origin persp) | Stale; subsumed once origin persp is folded |
| `feature/update_to_pchandler-1.0.0` | DEAD | 0 / — | **Retire** — prune local (safe); stage remote deletion for Phase 6 | Full ancestor of develop-gsd; nothing to salvage |
| `feature/release-please` (local) | DEAD (bot) | 0 / — | Prune local (safe); leave remote to automation | Ancestor of develop-gsd; release-please artifact |
| `origin/release-please/bootstrap/default` | DEAD (bot) | 0 / — | Document; leave remote (bot-managed) | Ancestor of develop-gsd; bootstrap artifact |
| `origin/release-please--branches--main` | LIVE (bot) | 3 / 54 | Document; leave remote (bot-managed, off `main`) | Active release-please PR branch tracking `main` |
| `main` / `origin/main` | **LIVE (ship target)** | 2 / 54 | Keep; cleanup deferred to Phase 6 ship | Old published v0.10.x lineage; retained public target |
| `origin/develop/tomislav` | **EXCLUDED** | 4 / 50 | Untouched (owner-excluded) | Not part of consolidation |

**`main` divergence note:** `main` forks from `develop-gsd` at `f946268` ("docs: Create LICENSE").
Its 2 extra commits are `69224a9` (merge) and `ade40f8` (a *second, differently-hashed* BSD-3-Clause
license switch — the develop lineage has its own as `e795ec0`). Both are semantically already
present on `develop-gsd`; nothing on `main` needs salvaging. `main` stays as the public ship target;
its reconciliation with the v2 lineage is a Phase 6 concern.

## Runtime State Inventory (branch/ref topology — this phase's "state")

For a branch-consolidation phase the "runtime state" is the ref graph itself. Answering the
inventory categories concretely:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stale local refs (fully merged, safe to prune) | `dev/v2`, `feature/update_to_pchandler-1.0.0`, `feature/release-please` (all ancestors of develop-gsd, per `git branch --merged develop-gsd`) | Local `git branch -d` (safe; `-d` refuses if not merged, so it self-guards) |
| Stale local refs (NOT merged, would lose commits until fold) | `dev/perspective_projection` (6 ahead) — but pure ancestor of `origin/dev/perspective_projection` | Prune **after** the origin-persp fold; then it is fully contained |
| Refs needing an archive tag before prune (D-06) | `origin/dev/perspective_projection` (carries the only unique source work) | Create e.g. `archive/dev-perspective_projection-pre-fold` → `8f0fae9` before pruning any persp ref |
| Remote refs (deletion OUT of scope — staged for Phase 6) | `origin/dev/v2`, `origin/dev/perspective_projection`, `origin/main` cleanup, release-please remotes | Record in inventory as "staged for Phase 6 ship"; do NOT `git push --delete` this phase |
| Owner-excluded / retained | `origin/develop/tomislav` (excluded), `main`/`origin/main` (ship target) | Leave untouched |

**Existing tags** (for archive-tag namespace collision check): `v0`, `v0.10`, `v0.10.0..4`,
`v2.0.0a5`. No `archive/*` namespace exists yet — safe to introduce.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Deciding if a local branch is safe to delete | Manual ahead/behind math | `git branch -d <b>` (lowercase `-d`) | `-d` refuses to delete a branch not merged into HEAD/upstream — it self-guards against data loss. Use `-D` only with an archive tag in place. |
| Detecting whether a branch's commits already exist upstream | Eyeballing hashes | `git merge-base --is-ancestor <b> develop-gsd` | Exact boolean answer; already used above |
| Finding cherry-picked/rebased equivalents | Subject-line grep | `git cherry -v develop-gsd <b>` | Detects patch-equivalence by patch-id, not just subject |
| Confirming a fold is conflict-free before running it | Trial merges | `git diff --name-only <base> <each-side>` and check for disjoint file sets | Disjoint change-sets → provably no conflicts, no mutation needed |

## Common Pitfalls

### Pitfall 1: Merging the stale LOCAL perspective branch instead of the remote
**What goes wrong:** merging `dev/perspective_projection` (local) folds an ancestor snapshot that is
16 commits behind origin, silently dropping the latest perspective work.
**How to avoid:** merge `origin/dev/perspective_projection` explicitly (D-01). Fetch first if unsure
the remote-tracking ref is current (`git fetch origin` — read-only, safe).
**Warning sign:** the merge fast-forwards or shows fewer than ~12 commits over the base.

### Pitfall 2: Running the fold on the wrong HEAD
**What goes wrong:** current HEAD is `gsd/phase-01-…`, not `develop-gsd`. A merge lands on the phase
branch, not the mainline.
**How to avoid:** decide the target explicitly. Per the project branching strategy (CLAUDE.md), phase
work happens on the per-phase branch and merges back to `develop-gsd`. Either (a) do the fold on the
phase branch and later merge the phase branch into `develop-gsd`, or (b) check out `develop-gsd` for
the fold. Planner's call (D-discretion), but be explicit — do not assume HEAD is mainline.

### Pitfall 3: Deleting a remote ref this phase
**What goes wrong:** `git push origin --delete …` is destructive and outward-facing; D-05 stages all
remote deletions for Phase 6.
**How to avoid:** this phase touches only **local** refs and **local** archive tags. All remote
deletions are recorded as "staged for Phase 6" in the inventory.

### Pitfall 4: Pruning `dev/perspective_projection` (local) before the fold
**What goes wrong:** before the fold, local persp carries 6 commits not in `develop-gsd`; `git branch -d`
will refuse and `-D` would (briefly) orphan them.
**How to avoid:** archive-tag the origin persp ref, run the fold, *then* prune the local persp label
(now fully contained). Order matters.

### Pitfall 5: Committing planning-ID scopes / touching `.planning` on `main`
**What goes wrong:** violates the two CLAUDE.md conventions (functional commit scopes only; `main`
stripped of `.planning/`).
**How to avoid:** use functional scopes (e.g. `chore(branch):`, `docs(branch):`) — never
`(BRANCH-01)`-style tags. Keep the inventory doc under `.planning/phases/01-…/` (D-07); it never lands
on `main`.

## State of the Art

Not applicable — this is a mechanical git-topology phase, not a tooling/library selection. Git 2.53.0
is installed; all commands used (`merge-base --is-ancestor`, `cherry`, `rev-list --left-right`,
`for-each-ref`) are long-stable core plumbing/porcelain.

## Package Legitimacy Audit

Not applicable — this phase installs **no** external packages. It is pure git ref manipulation plus a
Markdown inventory document.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| git | All branch operations | ✓ | 2.53.0 | — |

No other external tooling required. (No network action required either — all fold/prune operations are
local; an optional `git fetch origin` to refresh remote-tracking refs is read-only.)

## Validation Architecture

`nyquist_validation` is enabled. There are no unit tests to write for a git-topology phase; validation
is **assertion-by-git-command** proving the four Success Criteria. These are the checks a plan's
verification steps should run (all read-only, all deterministic):

### Success-Criteria → Proof Map

| SC | Behavior to prove | Automated check (expected result) |
|----|-------------------|-----------------------------------|
| SC2 (dev/v2 consolidated) | develop-gsd contains all dev/v2 | `git merge-base --is-ancestor origin/dev/v2 develop-gsd` → exit 0; `git rev-list --count origin/dev/v2..develop-gsd` ≥ 8 |
| SC2 (perspective folded) | `PerspectiveProjection` present on mainline after fold | `git grep -l PerspectiveProjection <fold-target> -- 'src/*'` → matches `strategies/projection.py`; `"perspective"` present in the `PROJECTIONS` registry Literal |
| SC2 (fold completeness) | No perspective commit left behind | after fold: `git rev-list --count <fold-target>..origin/dev/perspective_projection` → 0 |
| SC4 (no divergent dev/*) | every `dev/*` is an ancestor of the fold target | `git branch -a --no-merged <fold-target>` lists no `dev/*` ref (excluding excluded/ship/bot refs) |
| SC1 (inventory) | inventory doc exists and classifies every ref | file present under `.planning/phases/01-…/`; row count == ref count from `git for-each-ref` |
| SC3 (pchandler-1.0) | branch dispositioned + acted on | `git merge-base --is-ancestor 54c7100 develop-gsd` → exit 0 (recorded); local label deleted (`git branch --list feature/update_to_pchandler-1.0.0` → empty) |
| D-06 (archive safety) | nothing lost on prune | `git tag --list 'archive/*'` shows the persp archive tag pointing at `8f0fae9` before any persp prune |

### Sampling
- **Per task:** run the specific SC check the task advances (single git command, sub-second).
- **Phase gate:** run the full proof map above; all exit-0 / expected before `/gsd-verify-work`.
- No pytest run is meaningful here (the source doesn't execute differently) — dependency-adaptation
  testing is Phase 2+.

### Wave 0 Gaps
None — no test infrastructure is needed for git-topology assertions.

## Security Domain

Not applicable in the ASVS sense — this phase performs **local git ref manipulation and Markdown
authoring** with no runtime code path, no input handling, no auth/session/crypto surface. The only
"security-adjacent" risk is **destructive git operations**, mitigated procedurally by D-05 (no remote
deletions this phase), D-06 (archive-tag before prune), and using `git branch -d` (self-guarding)
rather than `-D`. No ASVS L1 category applies to the changed surface.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The remote-tracking refs (`origin/*`) are current as of the last fetch; I did not run `git fetch` this session (read-only-but-network avoided) | Fold safety, inventory | Low — if origin moved, a `git fetch` before the fold refreshes; topology facts recompute identically. Planner should add a `git fetch origin` (read-only) as the fold's first step. |
| A2 | `origin/release-please--branches--main` and bootstrap refs are release-please bot artifacts | Inventory | Low — even if mislabeled, disposition ("leave remote, document") is unchanged |

**Everything else in this document is `[VERIFIED: git]`** — grounded in a command run this session.

## Open Questions

1. **Fold target — `develop-gsd` directly, or via the phase branch?**
   - What we know: HEAD is `gsd/phase-01-…` (= develop-gsd + 2 planning commits). Branching strategy
     says phase work merges back to `develop-gsd`.
   - What's unclear: whether the planner wants the fold merge commit authored on `develop-gsd` or on the
     phase branch (then merged forward).
   - Recommendation: fold on the phase branch (keeps develop-gsd advancing only via reviewed phase
     merges), then fast-forward/merge into `develop-gsd` at phase close. Either is clean; be explicit.

2. **Does a remote `feature/update_to_pchandler-1.0.0` exist to stage for deletion?**
   - What we know: only a local label is present in the ref list; no `origin/feature/update_to_pchandler-1.0.0`
     appeared in `for-each-ref`.
   - Recommendation: after `git fetch`, confirm; if no remote copy exists, BRANCH-03 remote-staging is a no-op.

## Sources

### Primary (HIGH confidence)
- Live repo git commands (this session, 2026-07-08): `git for-each-ref`, `git merge-base [--is-ancestor]`,
  `git rev-list [--left-right] [--count]`, `git diff [--stat|--name-only]`, `git show`, `git cherry -v`,
  `git branch --merged/--no-merged`, `git ls-tree`, `git grep`, `git tag -l`.
- `.planning/phases/01-…/01-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`,
  `./.claude/CLAUDE.md` (branching strategy + commit-scope conventions).

## Metadata

**Confidence breakdown:**
- Branch topology / merge-base / ancestry: **HIGH** — direct git verification, deterministic.
- Fold cleanliness: **HIGH** — proven by disjoint changed-file sets, not a trial merge.
- BRANCH-03 already-merged finding: **HIGH** — `--is-ancestor` + empty `rev-list` + current-tree grep.
- Bot-branch classification: **MEDIUM** — inferred from ref names/dates (see A2).

**Research date:** 2026-07-08
**Valid until:** until the next `git fetch`/push changes remote refs, or any branch is created/deleted.
Re-verify the ref table if the repo's refs change before planning executes.
