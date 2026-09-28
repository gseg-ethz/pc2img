---
created: 2026-07-27T09:38:20.296Z
title: Phase 6 publication CI/CD — adopt the PCHandler branch-protection security floor on the mainline; defer the redundant-CI template mechanics to SEED-001
area: tooling
severity: major
resolves_phase: 6
files:
  - .github/workflows/ci.yml
  - .github/workflows/release-please.yml
  - .github/rulesets/
  - pyproject.toml
source: pchandler workspace seed SEED-001 (~/gsd-workspaces/pchandler/.planning/seeds/SEED-001-streamline-branch-protection-cicd-release-flow.md), surfaced 2026-07-27
---

## Problem

Phase 6's goal is "the repository meets the PCHandler publication standard," and Success
Criterion 1 is "branch protection and publication CI/CD **matching the PCHandler template**
are in place on the mainline." The project constraint says the same.

**But the PCHandler template is itself under review.** On 2026-07-11 the pchandler project
planted **SEED-001** (`status: dormant`) after living through the GSEGUtils 0.5.3 ship
(quick task `260711-lz3` — the release that delivered `register_lazy_disk_cache_class`,
prompted by discoveries in *this* repo). Running that ship end-to-end surfaced two concrete
inefficiencies in the very template Phase 6 would copy:

1. **Redundant CI — lint + pytest ran ~4-5x on functionally identical source before one
   publish.** All on unchanged `src/`:
   - PR #38 (`feat -> main`) — Lint (pre-commit) + Tests
   - push to `main` post-#38 merge — CI re-runs (this is what triggers release-please via `workflow_run`)
   - PR #34 (release-please branch) — Lint + Tests again, though the PR only edits CHANGELOG / manifest / conf.py
   - push to `main` post-#34 merge — CI re-runs again, then tags + publishes
   - PR #39 (`main -> develop/gsd` reconcile) — Lint + Tests yet again

   Plus `publish-pypi.yml` does its own build. The seed calls "4 runs" conservative.

2. **Squash + protected develop branch makes post-release cleanup involved.** The release
   lands on `main` only, and squash merges give `main` and the develop branch permanently
   divergent SHAs, so every release needs a follow-up reconcile PR — which itself re-runs
   CI and needs a human merge.

SEED-001's trigger is "at the start of the next milestone (pchandler v2.0 Maturity &
Cutover), as its **first phase**," and its scope is explicitly **both** repos (pchandler +
GSEGUtils) kept symmetric. So the redesign has not happened yet and is not scheduled before
pc2img Phase 6.

**Risk if ignored:** Phase 6 plans against the current template, pc2img inherits the
redundant-run mechanics, and then becomes a third repo needing the same rework when
SEED-001 is finally worked.

Related but distinct: `2026-07-09-move-to-ruff-lint-ci.md` (pc2img still has no lint step
in CI at all). That todo asks *whether* to add a lint job; this one constrains *how much of
the pchandler CI/CD flow* to adopt while doing it. Both should be on the table in the same
Phase 6 discussion, and the sequencing note in the ruff todo ("don't add a check only to
replace it") argues for deciding this one first.

## Solution

Adopt the **security floor now, defer the flow mechanics** (option 3 of three considered on
2026-07-27; the alternatives were "adopt the whole template now and absorb the rework
later," and "pull SEED-001 forward into Phase 6" — rejected as scope creep into two other
repos, and because SEED-001 explicitly wants to be pchandler v2.0's own first phase).

**Adopt in Phase 6 — the floor SEED-001 itself marks "do NOT regress":**
- OIDC trusted-publisher publish to PyPI (no long-lived API tokens)
- PEP 740 publish attestations
- Branch-protection rulesets on the mainline: 0-approval PR gate, linear history,
  no force-push / no deletion, empty bypass list
- Required status checks on `main`
- The self-merge / merge-without-review guard

Rationale: none of this is what SEED-001 wants to change — the seed's candidate levers are
about *where checks fire and how often*, not *whether the security posture holds*. Adopting
the floor is therefore safe against the redesign.

**Defer to the SEED-001 redesign — do not copy pchandler's current shape verbatim:**
- The `workflow_run`-chained CI -> release-please trigger topology
- Running the full required-check suite on release-please PRs (docs/manifest-only diffs)
- The `feat -> main -> reconcile-PR-back-to-develop` promotion mechanic

For these, pick the **minimum that satisfies Phase 6's success criteria** and record the
choice as an explicit deviation from "match the PCHandler template," so pc2img is a clean
adopter of whatever SEED-001 concludes rather than a third instance of the current shape.
Cheap, redesign-compatible levers worth evaluating in-phase (they are the seed's own
candidate list, so adopting them early does not pre-empt it):
- `paths-ignore` / path filters so docs- and manifest-only PRs skip the full suite
- `concurrency` groups with in-progress cancellation
- reusing a merged commit's existing green status instead of re-running

**Deliverable for the phase:** whichever way it lands, write the divergence down (ADR or
BC/CI note) with a pointer back to SEED-001, so the Phase 6 record states *which* parts of
the PCHandler standard were adopted, which were deliberately deferred, and why. Otherwise a
later reader sees Success Criterion 1 partially met and reads it as an oversight.

**Cross-repo coordination:** SEED-001 wants pchandler + GSEGUtils kept symmetric. If pc2img
lands a leaner flow first, feed the result back so the eventual redesign has three data
points rather than two. Note the standing constraint that dependency-repo edits require
human approval — this todo does not authorize touching pchandler or GSEGUtils.

## Breadcrumbs

- Seed: `~/gsd-workspaces/pchandler/.planning/seeds/SEED-001-streamline-branch-protection-cicd-release-flow.md`
- Evidence: `~/gsd-workspaces/pchandler/.planning/quick/260711-lz3-ship-register-lazy-disk-cache-class-gsegutils-0-5-3/SUMMARY.md`
- Posture being inherited: pchandler v1.1 CI Rework (Phases 8-11)
- Config surfaces to audit: `.github/workflows/{ci,release-please,publish-pypi}.yml`,
  `.github/actions/setup-python-deps`, `release-please-config.json`, `.github/rulesets/*.json`
- Version-bump gotcha from the same ship, relevant to pc2img's own release config:
  GSEGUtils resolved to **0.5.3, not 0.6.0**, because `bump-patch-for-minor-pre-major: true`
  makes a pre-1.0 `feat` bump the patch. pc2img is pre-1.0 too (currently 0.10.4) — confirm
  what `release-please-config.json` does here before assuming a `feat` yields a minor bump.
