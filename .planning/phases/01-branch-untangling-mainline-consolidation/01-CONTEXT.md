# Phase 1: Branch Untangling & Mainline Consolidation - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish `develop-gsd` as the single forward-development mainline carrying the
richest architecture, and produce a documented inventory that classifies every
other branch as live or dead with an acted-on disposition.

**Verified starting state (2026-07-08):**
- `develop-gsd` already contains all of `dev/v2`'s architecture — its merge-base
  with the perspective branch *is* the `dev/v2` tip, and it is strictly ahead of
  local `dev/v2` (adds the BSD-3-Clause license commit + the GSD planning docs).
  So consolidating `dev/v2` is a **verify-and-document** task, not a merge
  (Success Criterion 2 essentially already met).
- `origin/dev/perspective_projection` is the **only** branch carrying divergent
  development not reflected in `develop-gsd` (Success Criterion 4). Its
  authoritative copy is the **remote** — the local `dev/perspective_projection`
  is 10 commits behind `origin`.
- History shows signs of duplicated/rebased commits across `dev/*` (same subject
  lines, different hashes) — the researcher should expect a tangled DAG, not a
  clean linear delta.

**In scope:** branch inventory, per-branch disposition decisions, the
`perspective_projection` fold, safe local-branch pruning, staging remote
deletions for ship.
**Out of scope:** dependency adaptation (Phase 2), quality/soundness review
(Phase 4), actual GitHub remote-branch deletion (deferred to Phase 6 ship).
</domain>

<decisions>
## Implementation Decisions

### dev/perspective_projection disposition
- **D-01:** **Fold the entire `origin/dev/perspective_projection` branch into
  `develop-gsd`**, including the new `PerspectiveProjection` strategy — not just
  the hardening-flavored improvements (density thinning, `TriangulationData`
  rework, sobel/sqrt/square features). Merge from `origin/dev/perspective_projection`
  (the authoritative remote copy), not the stale local branch. Mechanically a
  clean merge: `develop-gsd`'s merge-base already *is* the `dev/v2` tip.
- **D-02 (scope amendment — flagged intentional, NOT scope creep):** Folding
  `PerspectiveProjection` overrides the currently-locked "New
  projection/interpolation/feature algorithms" Out-of-Scope boundary
  (PROJECT.md §Out of Scope; REQUIREMENTS.md §Out of Scope). The project owner
  has decided this is now **in scope**. PROJECT.md and REQUIREMENTS.md must be
  amended (remove/reword that Out-of-Scope entry) so the mainline no longer
  contradicts the milestone docs. Downstream agents should treat this as an
  intended, owner-approved scope change.
- **D-03 (downstream consequence):** Because `PerspectiveProjection` now lives on
  the mainline, **Phase 4** (algorithmic-soundness review) and **Phase 5** (test
  coverage) now *own* it — its projection math gets audited and it needs test
  coverage like every other strategy. This is added surface those phases must
  account for.

### feature/update_to_pchandler-1.0.0 disposition (BRANCH-03)
- **D-04:** **Diff-review then retire.** Do a commit-level review to salvage any
  still-relevant change into a note (e.g. the "Enforce named arguments approach
  in registry" commit `54c7100`) BEFORE retiring. The branch targets a
  two-majors-stale PCHandler 1.0 and is superseded by the Phase 2 dep adaptation;
  the review is a cheap guard against losing a stray useful fix, not an
  expectation of salvage.

### Branch deletion scope / mechanics
- **D-05:** **Record dispositions now; execute remote deletions at ship.**
  Phase 1 produces the inventory + dispositions and prunes only *safe local*
  branches. Actual remote (GitHub) branch deletions are **staged** and executed
  at milestone ship (Phase 6), alongside the `main` cleanup. Rationale: avoid
  destructive, outward-facing GitHub actions mid-milestone; keep refs available
  in case a later phase needs the history.
- **D-06:** For anything dispositioned dead but potentially salvage-worthy
  (notably `origin/dev/perspective_projection` once folded, and any branch
  flagged during review), create an **archive tag** before pruning so nothing is
  permanently lost.

### Branch-inventory document
- **D-07:** **Home is `.planning/` now; distill publicly-relevant bits later.**
  The full branch inventory + disposition doc lives under
  `.planning/phases/01-branch-untangling-mainline-consolidation/` (internal
  planning record, stripped from public `main`). If any of it matters publicly,
  fold a distilled note into the Phase 6 breaking-change/migration record (BC-01)
  rather than carrying a standalone doc on `main`.
- **D-08:** "Disposition" for BRANCH-01/03 means **decided-and-recorded (+ local
  action taken where safe)** this phase — not full remote execution (see D-05).

### Claude's Discretion
- Exact inventory doc filename/format within the phase dir.
- Which local branches are "safe" to prune vs keep as local convenience.
- How to classify the housekeeping/automation branches (`feature/release-please`,
  `origin/release-please--branches--main`, `origin/release-please/bootstrap/default`):
  treat as bot-managed/automation → document disposition, leave remote alone,
  prune stale local copies where safe. `develop/tomislav` stays untouched
  (owner-excluded); `main` is retained as the public ship target.
- Whether the `perspective_projection` fold is executed in this phase or staged
  as the first plan of it — planner's call.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone planning
- `.planning/ROADMAP.md` §"Phase 1" — goal + 4 success criteria this phase must satisfy.
- `.planning/REQUIREMENTS.md` §"Branch Untangling" — BRANCH-01, BRANCH-02, BRANCH-03.
- `.planning/PROJECT.md` §Context ("Branch chaos") + §Out of Scope — the
  Out-of-Scope entry on "new algorithms" is the one being amended per D-02.

### Codebase maps (context for what "richer architecture" means)
- `.planning/codebase/` (refreshed 2026-07-08) — architecture/structure/concerns
  analyses describing the `features/ image_cache/ strategies/ tiled_generator.py`
  layout that `develop-gsd` carries.

_No external ADRs/specs — branch topology decisions are captured in this file._
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `develop-gsd` mainline src tree (`src/pc2img/…`) already carries the full
  `dev/v2` architecture; the fold layers `PerspectiveProjection` onto it.

### Established Patterns
- `PerspectiveProjection` (on `origin/dev/perspective_projection`) implements the
  same `ProjectionStrategy` ABC + registry-decorator pattern as
  `SphericalProjection`/`OrthographicProjection` — it slots into the existing
  `strategies/projection.py` + `PROJECTIONS` registry without new plumbing.

### Integration Points
- Fold source: `origin/dev/perspective_projection` (NOT local — local is 10
  commits stale). Merge target: `develop-gsd`. Merge-base is the `dev/v2` tip
  (`91b4ab6`).
</code_context>

<specifics>
## Specific Ideas

- Merge from the **remote** `origin/dev/perspective_projection`, archive-tag
  before any prune, and salvage-note the registry named-args commit (`54c7100`)
  from the pchandler-1.0 branch before retiring it.
</specifics>

<deferred>
## Deferred Ideas

- **Actual GitHub remote-branch deletions** — staged this phase, executed at
  milestone ship (Phase 6) with the `main` cleanup.
- **Public distillation of the branch inventory** — fold into the Phase 6 BC-01
  breaking-change/migration record if warranted.
- **`develop/tomislav`** — permanently excluded from consolidation per owner; not
  a deferred item, just untouched.

</deferred>

---

*Phase: 1-Branch Untangling & Mainline Consolidation*
*Context gathered: 2026-07-08*
