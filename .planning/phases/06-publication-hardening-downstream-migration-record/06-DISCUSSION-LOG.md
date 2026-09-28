# Phase 6: Publication Hardening & Downstream Migration Record - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-28
**Phase:** 06-publication-hardening-downstream-migration-record
**Areas discussed:** Todo folding, Release identity, CI checks & metadata (→ template adoption), Migration record shape, Promotion timing / phase split, Public-tree content

---

## Todo folding

| Option | Description | Selected |
|--------|-------------|----------|
| GSEGUtils 0.6 adoption | Pin bump, spikes 001/004, delete containment override | ✓ (later retargeted to Phase 7) |
| Round-5 hygiene | Planning refs in comments, test hygiene | ✓ (later split 6/7) |
| Ruff lint in CI | Wire ruff into CI | ✓ |
| RRIM float32 guard | Fail fast on float32 overflow | |

**User's choice:** the first three, plus (free text) "the adoption of github CI according to template"
(the 2026-07-27 security-floor todo).
**Notes:** Two matched todos (`_TransformArray` guard, config-less default) were found already resolved.

## Gray-area selection

| Option | Selected |
|--------|----------|
| Protection scope | (not selected — later settled by the template) |
| Release identity | ✓ |
| CI checks & metadata | ✓ |
| Migration record shape | ✓ |

---

## Release identity

**Clarification requested:** "What tags have been used up until now?" → table of all 9 origin tags presented
(v0.10.0–v0.10.4 release-please line on old main; lightweight v2.0.0a5 on dev/v2 only; v2.0.0a1–a4 absent).

| Option | Description | Selected |
|--------|-------------|----------|
| 2.0.0 | Matches v2.0.0a5 tag + iof3D pin | |
| 2.0.0rc1 then 2.0.0 | Real-PyPI pre-release first | |
| Stay on 0.x | Continue manifest 0.10.4 | ✓ (free text) |

**User's choice:** "stay in the 0.X range … official release of 0.11 … more consistent with future development."
Claude agreed and surfaced the ordering consequence of the v2.0.0a5 tag.

| Option (v2 tag) | Selected |
|--------|----------|
| Rename to archive/ | ✓ |
| Delete outright | |
| Keep it | |

**Follow-up question from user:** is release-please set up so pre-major breaking changes bump minor? → verified
against release-please source `determineReleaseType`: yes (`bump-minor-pre-major`), and `feat` bumps patch
(`bump-patch-for-minor-pre-major`).

| Option (publish depth) | Selected |
|--------|----------|
| TestPyPI dry-run | ✓ |
| Publish in Phase 6 | |
| Build + twine check only | |

| Option (bump mechanism) | Selected |
|--------|----------|
| feat! + BREAKING footer + Release-As | ✓ |
| Release-As only | |
| feat! only | |

---

## CI checks & metadata

Initial questions (lint shape, docs, extra checks) answered with: "There should be … a template document that
describes the CI/CD process" / "Check the template first" / "Check the template and propose what makes sense".
Claude located and read `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` + kit.

| Option (template) | Selected |
|--------|----------|
| Adopt in full (Procedure B) — supersedes 07-27 floor-only | ✓ |
| Floor only | |

| Option (interview Q1–Q7) | Selected |
|--------|----------|
| Confirm all as proposed | ✓ |
| Some need changes | |

| Option (components) | Selected |
|--------|----------|
| release-pypi | ✓ |
| config-self-inspection | |
| continuous-enforcement | |
| gpu-self-hosted | |

| Option (adaptations) | Selected |
|--------|----------|
| uv sync --frozen in setup composite | ✓ |
| License-banner pre-commit hook | |

| Option (metadata) | Selected |
|--------|----------|
| CITATION.cff | ✓ |
| Add Jon Allemand as author | |
| Extra project URLs | ✓ |

---

## Migration record shape

| Question | Options | Selected |
|----------|---------|----------|
| Format | PCHandler migration-spec / Promote BC-NOTES | migration-spec |
| Baseline | dev/v2 tip 91b4ab6 / v2.0.0a5 / v0.10.4 | 91b4ab6 |
| Coverage | Phases 1–6 / Phase 5 + 6 only | Phases 1–6 |
| Filename | MIGRATION-v0.11.md / MIGRATION-v1.0.md | MIGRATION-v0.11.md |

---

## Promotion timing / phase split

Claude asked when main first receives code + ruleset; user asked to clarify and proposed: "separate the
promotion of the CI/CD workflow aspects from the migration to GSEGUtils 0.6 … CI/CD can go directly as part of
phase 6, whereas the code rework should be part of a milestone ship." Claude agreed with the refinement that the
split is by time, not content (main is a filtered projection; a CI-only PR against old main would fail its own checks).

| Question | Options | Selected |
|----------|---------|----------|
| Where the code rework lives | New Phase 7 / Inside milestone ship | New Phase 7 |
| Migration record timing | Draft in 6, finalize in 7 / Move wholly to 7 | Draft in 6, finalize in 7 |
| Round-5 hygiene split | Split (refs in 6, tests in 7) / All in 6 / All in 7 | Split |
| Docs hosting | Read the Docs / Build-only | Read the Docs |

---

## Public-tree content

| Question | Options | Selected |
|----------|---------|----------|
| Sweep scope | Whole shipped tree / src+tests only | Whole shipped tree |
| docs/pchandler-2x-break-audit.md | Move into .planning / Rewrite public | Move into .planning |
| Broken scripts/01_… | Delete / Fix / Move out | Delete |
| docs/ip/rrim-eth-signoff.md | Keep verbatim, exempt / Scrub | Keep verbatim |

---

## Claude's Discretion

- Protection scope (not selected by user): settled by the template — both branches, linear history on main only.
- Coverage floor kept as recorded addition; GSEGUtils 0.6 exception-type handling per the todo (reproduce by running).
- Ruff remediation specifics, README/Sphinx layout, wave ordering, verifier implementation.

## Deferred Ideas

- New Phase 7 (GSEGUtils 0.6 adoption, test hygiene, migration finalize, second promotion) — add via `/gsd-phase`.
- Tag-protection ruleset; 1-approval review policy (template's own deferrals).
- RRIM float32 guard; CUDA selection guidance (reviewed, not folded).
