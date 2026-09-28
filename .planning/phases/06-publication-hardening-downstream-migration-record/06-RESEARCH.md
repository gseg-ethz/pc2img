# Phase 6: Publication Hardening & Downstream Migration Record - Research

**Researched:** 2026-09-28
**Domain:** GitHub branch protection / CI-CD template adoption (GSEG git-strategy kit), Python packaging + trusted publishing, Sphinx/Read the Docs, structured migration-record authoring
**Confidence:** HIGH for the template mechanics and current-repo measurements (all read or executed this session); MEDIUM for owner-account-state assumptions not re-probed beyond a read-only `gh api` check; LOW/ASSUMED only where flagged (secret-name choices, App-installation completion).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
D-01..D-30, verbatim scope, are recorded in
`.planning/phases/06-publication-hardening-downstream-migration-record/06-CONTEXT.md` under
`<decisions>`. This research does not restate them in full a second time — it is written to be read
alongside that file — but every section below is written to be **consistent with, and traceable to,**
those decisions. The load-bearing ones for this research file are:

- D-07/D-08/D-09: adopt `core` + `release-pypi` only, via Procedure B, with the interview answers
  already fixed (`<MAIN_BRANCH>=main`, `<DEV_BRANCH>=develop-gsd`, filtered-projection promotion,
  `<PLANNING_PATHS>=.planning/,.claude/`, `<CHECK_CONTEXTS>=Lint (pre-commit), Tests (pytest)` [+
  `Docs (sphinx -W)` on main only], merge methods on develop-gsd unchanged, no rulesets today).
- D-10: `uv sync --frozen` replaces the kit's `pip install .[dev]` in the setup composite.
- D-11: `.pre-commit-config.yaml` written by hand (kit ships none); ruff + standard hygiene hooks; no
  mypy, no license-banner hook; lint scope = whole shipped tree.
- D-12: pyright informational, Codecov upload, no seeded-RNG grep.
- D-13: minimal Sphinx site (`docs/source/conf.py` + index + autodoc), RTD-hosted, reconcile
  `release-please-config.json`'s `extra-files`.
- D-14: real README/CITATION.cff/urls, authors unchanged.
- D-15: CI/CD adoption record at repo root, no planning IDs.
- D-16: keep `--cov-fail-under=55` as a recorded addition to the template's Tests job.
- D-17/D-18: first promotion happens inside Phase 6, after all hygiene lands on develop-gsd.
- D-19: release-please's 0.11.0 PR stays open/unmerged at the end of Phase 6.
- D-20..D-23: planning-vocabulary sweep over the whole shipped tree; move
  `docs/pchandler-2x-break-audit.md`; delete `scripts/01_tiled_image_generation_from_pointcloud.py`;
  keep `docs/ip/rrim-eth-signoff.md` verbatim (exempted, reason stated at the exemption).
- D-24: code rework (GSEGUtils 0.6, containment-override deletion) is OUT of Phase 6, moved to Phase 7.
- D-25..D-29: migration-record format = PCHandler's migration-spec schema, `bc_id_prefix: BC-P2I`,
  baseline `91b4ab6`, target = develop-gsd HEAD (draft), file `MIGRATION-v0.11.md` at repo root,
  drafted in Phase 6 / finalised in Phase 7.
- D-30: every owner-only account action is a `checkpoint:human-action` task placed at point of need
  during **execution**, never collected during planning.

### Claude's Discretion
- Exact ruff remediation for the (now measured 13, see *Lint Readiness* below) hits, provided
  `Lint (pre-commit)` is green on the whole shipped tree.
- README structure/depth within D-14; Sphinx theme/page layout within D-13.
- Plan/wave decomposition and ordering, subject to D-17/D-18 (hygiene before promotion; workflows
  before rulesets).
- The inline verifier's implementation (AST-walk + runtime `getattr`, PCHandler-style), provided it
  mechanically checks every `surface-removed` / `signature-shape` claim.

### Deferred Ideas (OUT OF SCOPE)
- Phase 7: GSEGUtils 0.6 adoption, containment-override deletion, migration-record finalisation,
  second promotion, real PyPI publish (merging the release PR).
- Tag-protection ruleset on `refs/tags/v*` (template itself defers this — needs a bypass actor).
- Tighter review policy (1 required approval) — a future-tightening item.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CICD-02 | Branch protection + publication hardening matching the PCHandler template (pre-ship) | *Git-Strategy Kit Adoption*, *File Inventory & Diff*, *Apply-Time Checklist*, *Procedure B Walkthrough* sections below give the exact file list, token table, six in-place edit sites (3 of 6 apply — no GPU component), verification commands, and step order. |
| BC-01 (draft) | Structured, GSD-consumable breaking-change/migration record of pc2img's own public API/behavior changes this milestone | *Migration Record* section: format exemplar read from PCHandler `MIGRATION-v1.0.md`, entry inventory sourced from `05-BC-NOTES.md` (17 entries) + phases 1-4 diff, verifier design. |
</phase_requirements>

## Summary

Phase 6 is a **mechanical assembly job against an already-fully-specified template**, not an
open design space. `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` and its kit at
`~/gsd-workspaces/pchandler/.planning/git-strategy/template/` are complete, versioned, and every
FLOOR/DEFAULT/ASK marker in them has already been answered in `06-CONTEXT.md` (D-07/D-08/D-09). The
job is: copy `core/` then `release-pypi/` root-to-root into `/scratch/31_pc2img`, substitute ~14
tokens, hand-edit 3 in-place sites in `ci.yml` (a 4th — `pyproject.toml` as the packaging manifest —
needs no edit; pc2img already uses it), fix the 12+1 ruff hits and the 25-8=... (see *Lint Readiness*)
hits so `Lint (pre-commit)` is green pre-apply, write a **minimal** Sphinx site (measured: 13
`-W`-triggering warnings on a 7-module docstring sample under `sphinx~=5.1`→resolves 5.3.0 — no
version bump needed, these are content bugs), run the public-tree hygiene sweep (measured: the known
D-20 hits are all still present, plus two **new** ones this research surfaced —
`scripts/smoke_pipeline.py` and `.github/workflows/ci.yml`, the latter moot since that file is wholly
replaced by the kit), do the filtered-squash promotion to `main` per Procedure B (10 ordered steps),
and draft `MIGRATION-v0.11.md` from the already-complete 17-entry `05-BC-NOTES.md` plus a measured
23-file/~2285-line src/ diff since baseline `91b4ab6`.

**Primary recommendation:** Follow Procedure B verbatim (10 numbered FLOOR/DEFAULT steps, reproduced
below); do not re-derive any of the FLOOR-level mechanics (bypass_actors, linear-history asymmetry,
graft direction, ancestry-vs-content-diff) — they are settled by the template and by adversarial
probes recorded in its appendix. The only genuinely open engineering work this phase contains is (a)
reconciling the kit's `pip install .[doc]`/`.[dev]` idiom with pc2img's PEP 735 dependency-groups
(3 sites, all identified below with concrete fixes), (b) writing the Sphinx site and README/CITATION
content from scratch, and (c) drafting `MIGRATION-v0.11.md`'s ~20-entry table and inline verifier.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Branch protection (rulesets) | GitHub platform config (`.github/rulesets/*.json` + apply workflow) | — | Enforced server-side by GitHub; the committed JSON is the source of truth, applied via a dispatch-only workflow holding a dedicated App token. |
| CI gating (lint/test/docs) | CI/CD (`.github/workflows/ci.yml`) | Branch protection (required-status-check wiring) | The job `name:` fields ARE the ruleset context strings — the two tiers are coupled by string identity, not by reference. |
| Release automation | CI/CD (`release-please.yml`) | Branch protection (triggers only on protected-branch push) | release-please owns versioning/changelog; it is gated indirectly by requiring the branch it triggers from to already be protected and strict. |
| Package publish (PyPI/TestPyPI) | CI/CD (`publish-pypi.yml`/`publish-testpypi.yml`) | Release automation (triggered by `release: published`) | OIDC trusted publishing + PEP 740 attestation is a property of the *publish* workflow's identity (repo+workflow filename+environment), not of release-please. |
| Docs build + hosting | CI/CD (`Docs (sphinx -W)` job) + Read the Docs (external service) | — | RTD independently rebuilds from `.readthedocs.yaml`; CI's job is a pre-merge gate, RTD is the actual publish path. |
| Migration record content | Documentation (`MIGRATION-v0.11.md`, repo root) | Library source (verifier reads `__all__`/runtime symbols) | The record is a documentation artifact, but its own inline verifier is a small Python program that imports the library — a thin coupling into the Library tier. |
| Public-tree hygiene (vocab sweep, file moves) | Library source + Documentation (whichever tree contains the hit) | — | No separate tier; this is a cross-cutting sweep over the same files the other rows already touch. |

## Standard Stack

### Core (already fixed by the kit — not a choice)

| Component | Version (pinned) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `actions/checkout` | `93cb6efe18208431cddfb8368fd83d5badbf9bfd` (v5.0.1) | checkout | [VERIFIED: `~/gsd-workspaces/pchandler/.planning/git-strategy/template/core/.github/workflows/ci.yml:100`] SHA-pinned per template FLOOR. |
| `astral-sh/setup-uv` | pc2img's current `@v8.3.2` (tag, not SHA) | Python+uv setup — **superseded** by the kit's own `setup-python-deps` composite | [VERIFIED: `/scratch/31_pc2img/.github/workflows/ci.yml:27`] Current pc2img CI uses this; the kit's composite replaces the whole job's setup step, see D-10 below. |
| `actions/setup-python` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` (v6.2.0) | interpreter setup inside the kit's `setup-python-deps` composite | [VERIFIED: kit `core/.github/actions/setup-python-deps/action.yml:11`] |
| `jakebailey/pyright-action` | `8ec14b5cfe41f26e5f41686a31eb6012758217ef` (v3.0.2) | informational type-check (D-12) | [VERIFIED: kit `ci.yml:229`] `continue-on-error: true`, `annotate: warnings`. |
| `codecov/codecov-action` | `8cad3ba95e5920c42f44492e54bc9639cba47959` (v6.0.2) | coverage upload | [VERIFIED: kit `ci.yml:255`] no `fail_ci_if_error` — cannot redden the gate. |
| `actions/create-github-app-token` | `bcd2ba49218906704ab6c1aa796996da409d3eb1` (v3.2.0) | mint App-scoped tokens (ruleset apply + release-please) | [VERIFIED: kit `ruleset-apply.yml:231`, `release-please.yml:48`] two separate Apps, per FLOOR. |
| `googleapis/release-please-action` | `45996ed1f6d02564a971a2fa1b5860e934307cf7` (v5.0.0) | release automation | [VERIFIED: kit `release-please.yml:59`] — pc2img's current pin is unpinned `@v4` (`/scratch/31_pc2img/.github/workflows/release-please.yml:21`), must move to the kit's SHA-pinned v5. |
| `pypa/gh-action-pypi-publish` | `cef221092ed1bacb1cc03d23a2d87d1d172e277b` (v1.14.0) | PyPI/TestPyPI publish, OIDC + PEP 740 attestations | [VERIFIED: kit `publish-pypi.yml:69`, `publish-testpypi.yml:60`] official PyPA-maintained action. |
| `actions/upload-artifact` / `download-artifact` | `043fb46d…` (v7.0.1) / `3e5f45b2…` (v8.0.1) | build artifact hand-off between build/publish jobs | [VERIFIED: kit files] |
| `actions/github-script` | `d746ffe35508b1917358783b479e04febd2b8f71` (v9.0.0) | ancestry-drift issue open/dedupe | [VERIFIED: kit `scheduled-health.yml:118`] |
| `sphinx` | `~= 5.1` (pyproject already pins this; resolves `5.3.0` in a clean `uv run` resolve today) | docs build | [VERIFIED: measured this session — `uv run --no-project --with "sphinx~=5.1" --with . -- sphinx-build ...` resolved Sphinx 5.3.0 and built successfully under `-W --keep-going`, failing only on 13 content warnings, not a resolution/version problem] No version bump needed. |
| `release-please` config semantics | `bump-minor-pre-major: true` + `bump-patch-for-minor-pre-major: true` | pre-1.0 version bump policy | [VERIFIED: `/scratch/31_pc2img/release-please-config.json` already matches the kit's `optional/release-pypi/release-please-config.json` byte-for-byte except the `extra-files` key] |

### Package Legitimacy Audit

No **new** PyPI/npm packages are introduced by this phase — every dependency touched (`sphinx`,
`pyyaml` used by `check_publish_gate.py`, the pinned GitHub Actions) is either already a pc2img
dependency or ships as source inside the vetted kit (SHA-pinned, sourced from the maintainer's own
prior-audited template, not discovered via web search). The Package Legitimacy Gate is therefore
**N/A for new installs**; the one item worth a registry sanity check is `sphinx` itself, since D-13
asks whether the pinned range needs to move:

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| `sphinx` | PyPI | [VERIFIED: this session, `uv run --with "sphinx~=5.1"` resolved and installed `Sphinx 5.3.0` without error] OK — existing `~=5.1` pin in `[dependency-groups] doc` is sufficient; no bump needed. | Keep pin. |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Git-Strategy Kit Adoption

### File inventory — exactly what gets copied (D-09: `core` + `release-pypi` only)

Root-to-root copy per *Assembling a repository* FLOOR rule (never `.github`-only, never `cp -r` the
kit root) [VERIFIED: `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` lines 392-419]:

**`core/`** (14 files, all land under pc2img's `.github/`):

| Kit path | Lands at |
|---|---|
| `core/.github/workflows/ci.yml` | `.github/workflows/ci.yml` |
| `core/.github/workflows/ruleset-apply.yml` | `.github/workflows/ruleset-apply.yml` |
| `core/.github/workflows/scheduled-health.yml` | `.github/workflows/scheduled-health.yml` |
| `core/.github/rulesets/main.json` | `.github/rulesets/main.json` |
| `core/.github/rulesets/develop.json` | `.github/rulesets/develop.json` |
| `core/.github/scripts/ruleset_lib.py` | `.github/scripts/ruleset_lib.py` |
| `core/.github/scripts/preflight_ruleset_apply.py` | `.github/scripts/preflight_ruleset_apply.py` |
| `core/.github/scripts/check_ruleset_drift.py` | `.github/scripts/check_ruleset_drift.py` |
| `core/.github/scripts/test_ruleset_lib.py` | `.github/scripts/test_ruleset_lib.py` |
| `core/.github/scripts/test_preflight_ruleset_apply.py` | `.github/scripts/test_preflight_ruleset_apply.py` |
| `core/.github/scripts/test_check_ruleset_drift.py` | `.github/scripts/test_check_ruleset_drift.py` |
| `core/.github/actions/classify-changes/action.yml` | `.github/actions/classify-changes/action.yml` |
| `core/.github/actions/setup-python-deps/action.yml` | `.github/actions/setup-python-deps/action.yml` |
| `core/.github/scripts/test_classify_changes.py` | `.github/scripts/test_classify_changes.py` |

**`optional/release-pypi/`** (6 files — **2 land at repo root, not under `.github/`**, per the FLOOR
"map the component's root to the repository root" rule — a `.github`-only copy silently drops them
and the failure surfaces 4 steps later as `release-please-config.json: not found`):

| Kit path | Lands at |
|---|---|
| `optional/release-pypi/.github/workflows/release-please.yml` | `.github/workflows/release-please.yml` |
| `optional/release-pypi/.github/workflows/publish-pypi.yml` | `.github/workflows/publish-pypi.yml` |
| `optional/release-pypi/.github/workflows/publish-testpypi.yml` | `.github/workflows/publish-testpypi.yml` |
| `optional/release-pypi/.github/scripts/check_publish_gate.py` | `.github/scripts/check_publish_gate.py` |
| `optional/release-pypi/release-please-config.json` | **`release-please-config.json`** (root) |
| `optional/release-pypi/.release-please-manifest.json` | **`.release-please-manifest.json`** (root) |

**NOT copied** (declined per D-09): `config-self-inspection` (`check_ci_config.py` +
`test_check_ci_config.py`), `continuous-enforcement` (`integrity.yml`, `ruleset-drift.yml`,
`assert_no_skip.py`), `gpu-self-hosted` (all GPU files). Consequence, verified by reading the kit's
own `ci.yml`: the lint job's "Check CI config" step will print `"no config self-inspection component
assembled — the apply-time checklist in the strategy document governs this repository"` and exit 0 —
this is expected, not a defect. The apply-time 12-item checklist (below) must be satisfied **once, by
hand, with recorded evidence** instead of being mechanically re-checked on every PR — this is the
explicitly-stated cost of declining continuous-enforcement (D-09).

### Token substitution table (all ~14 tokens, values fixed by D-08)

| Token | Value | Level |
|---|---|---|
| `<MAIN_BRANCH>` | `main` | ASK — answered |
| `<DEV_BRANCH>` | `develop-gsd` | ASK — answered |
| `<CI_WORKFLOW_NAME>` | must equal `ci.yml`'s `name:` byte-for-byte — recommend `CI` (matches pc2img's current `ci.yml:1`) | FLOOR (read off assembled file) |
| `<LINT_CONTEXT>` | `Lint (pre-commit)` | ASK — answered (D-08 Q5) |
| `<TEST_CONTEXT>` | `Tests (pytest)` | ASK — answered |
| `<DOCS_CONTEXT>` | `Docs (sphinx -W)` | ASK — answered, required on `main` only |
| `<OWNER>` | `gseg-ethz` | read off repo |
| `<REPO>` | `pc2img` | read off repo |
| `<PACKAGE>` | `pc2img` | read off `pyproject.toml` `[project].name` — [VERIFIED: `/scratch/31_pc2img/pyproject.toml:6`] |
| `<IMPORT_PACKAGE>` | `pc2img` (same as `<PACKAGE>`) | ASK — answered, both identical |
| `<PYTHON_VERSION>` | `3.12` | DEFAULT — matches `requires-python` |
| `<MAIN_RULESET_NAME>` | `protect-main` | ASK — answered |
| `<DEV_RULESET_NAME>` | `protect-develop-gsd` | ASK — answered |
| `<RELEASE_PLEASE_ENABLED>` | `True` | ASK — answered (not consumed by any file since config-self-inspection is declined — the flag only gates assertion A4, which pc2img does not ship) |
| `<APPLY_APP_ID_SECRET>` / `<APPLY_APP_KEY_SECRET>` | **not yet named** — see *Secret naming* below | DEFAULT |
| `<RELEASE_APP_ID_SECRET>` / `<RELEASE_APP_KEY_SECRET>` | **not yet named** — see *Secret naming* below | FLOOR (must differ from the protection App's secrets) |

**Secret naming — an open sub-decision inside D-30 owner action #1, not re-litigated here:**
[VERIFIED: `~/gsd-workspaces/pchandler/.planning/release-please-token.md:29-32`] PCHandler's *existing*
release App (`gseg-release-please`, App ID `4039497` — the **same** App pc2img will add, per the `gh
api orgs/gseg-ethz/installations` read below) uses repo secrets named `APP_ID` / `APP_PRIVATE_KEY`
there. Since pc2img needs **two** distinct App credential pairs in the **same** repo (release App +
protection App), reusing PCHandler's bare `APP_ID`/`APP_PRIVATE_KEY` names for one of them and
choosing a second, clearly-different pair for the other (e.g. `RULESET_APP_ID` /
`RULESET_APP_PRIVATE_KEY` for the protection App, `RELEASE_APP_ID` / `RELEASE_APP_PRIVATE_KEY` for
the release App) is recommended — this keeps the naming self-documenting and avoids the kit's example
`APP_KEY` (PCHandler actually uses the more descriptive `APP_PRIVATE_KEY`). This is Claude's-discretion
naming, not a locked decision — flag it in the plan as a one-line confirmation at the D-30 checkpoint.

### Current-repo state, read this session (informs which owner actions are still outstanding)

[VERIFIED: `gh api` read-only calls, 2026-09-28] `gseg-ethz/pc2img` is public, default branch `main`,
`rulesets` returns `[]`, legacy branch protection on `main` returns 404 ("Branch not protected"). Repo
secrets: only `NIME_RELEASE_PLEASE_TOKEN` (legacy PAT-style, unused by the new flow — do not reuse; the
release App path replaces it, mirroring PCHandler's own now-superseded `NIME_RELEASE_PLEASE_TOKEN`
cleanup note). Repo environments: `[]` (none exist yet — `pypi`/`testpypi`/`gpu-lab`-style environments
must be created; only `testpypi` is needed in Phase 6, per D-30 item 3). Org-level GitHub Apps already
exist and are installed with `repository_selection: "selected"` — i.e. **installed on the org but not
yet added to `pc2img` specifically**:

| App | App ID | Current permissions | Needed for |
|---|---|---|---|
| `codecov` | 254 | checks:write, contents:read, pull_requests:write, statuses:write, administration:read | Coverage upload (D-12) |
| `gseg-release-please` | 4039497 | contents:write, issues:write, pull_requests:write, metadata:read | Release-please (D-08, D-30 item 4) |
| `gseg-ruleset-admin` | 4427434 | administration:write, metadata:read | Ruleset apply/drift (D-30 item 1) |

None of the three shows `pc2img` in its installed-repo set from this read (the installation objects
don't enumerate member repos to a non-admin read; this must be confirmed/added by the owner at the
D-30 checkpoint — do not assume it is already done).

### Apply-time checklist — all 12 items, mapped to pc2img-specific evidence commands

Since config-self-inspection is declined, **every** item below is a manual, once-at-apply-time check
with recorded evidence (FLOOR: "quote the command you ran and its output, or the `file:line`") — none
of it is mechanised into CI.

| # | Item (from GIT-STRATEGY.md "Verifying an assembly") | pc2img evidence command |
|---|---|---|
| 1 | Every required-check context is produced by a job whose `name:` matches byte-for-byte | `grep -n 'name:' .github/workflows/ci.yml` vs. the ruleset JSON `required_status_checks[].context` values |
| 2 | No required-context job carries a job-level `if:` or a conditional `needs:` | `grep -n -A2 '^  [a-z]*:$' .github/workflows/ci.yml` — read `lint:`/`tests:`/`docs:` job bodies for `if:`/`needs:` |
| 3 | Required-context strings are the job's `name:`, not its key or the workflow's `name:` | read `.github/rulesets/*.json` `context` fields against `ci.yml` `name:` lines |
| 4 | No `pull_request_target` anywhere (continuous-enforcement declined, so N/A by absence — still verify none was accidentally copied) | `grep -rn pull_request_target .github/workflows/` → expect empty |
| 5 | No filter key (`paths:`/`branches:`/`types:`) under a PR-side trigger on a required-context workflow | `sed -n '/^on:/,/^jobs:/p' .github/workflows/ci.yml` — kit ships `pull_request:` with no filters |
| 6 | Every `bash -c '<body>'` payload is apostrophe-free | `grep -n "bash -c" .github/workflows/*.yml .github/scripts/*.py` |
| 7 | Multi-command `run:` steps use `&&` or `\|\| exit 1`, not bare `;` chains | manual read of each `run: \|` block |
| 8 | Lint job's `permissions:` grants no write scope | `sed -n '/^  lint:/,/permissions:/p' .github/workflows/ci.yml` |
| 9 | Every third-party action is pinned to a full 40-char SHA | `grep -rn 'uses:' .github/` — every line must show a 40-char hex, not a tag |
| 10 | Floor present on every protected-branch payload: `bypass_actors:[]`, `non_fast_forward`, `deletion`, `pull_request` gate, `required_status_checks`; `required_linear_history` on `main` only | read `.github/rulesets/main.json` and `develop.json` directly (already shown correct in the kit — main.json has it, develop.json does not) |
| 11 | Any check-renaming/decomposition lands in the **same commit** as the ruleset payload update | N/A at initial apply (nothing renamed yet) — record as "not applicable — first assembly" |
| 12 | No placeholder token survived — whole tree, not just `.github/` | `! grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json` (verification command (1); **note the root-level release-please files must be included explicitly, since command (1)'s literal form only scopes `.github/`** — the kit's own `<any component files at the repository root>` clause exists for exactly this) |

### Procedure B — the 10 ordered steps (public repo; this is the correct procedure, not A or C)

[VERIFIED: `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` lines 1146-1189] pc2img is public
today (confirmed via `gh api`), so Procedure B applies directly — no private→public flip (Procedure C)
is needed.

1. **FLOOR** — Interview already answered in full (D-08). Nothing to re-ask.
2. **FLOOR** — Copy `core/`, `core/<path>` → `<path>` at repo root.
3. **FLOOR** — Copy `release-pypi/` over the result, root-to-root (the release-please config/manifest
   land at repo root, not `.github/`).
4. **FLOOR** — Substitute every token (table above); then read the **3** in-place edit sites in
   `ci.yml` (pc2img has no GPU component, so `gpu.yml`'s 3 sites don't apply) — see *In-place edit
   sites* below.
5. **ASK — SKIP.** Continuous-enforcement is not applied (D-09), so no A2 reviewed-exception register
   entry is needed.
6. **FLOOR** — Run verification command (1) (grep, whole tree) + the 12-item apply-time checklist
   with recorded evidence. Commands (2)/(3) do not apply (config-self-inspection declined).
7. **FLOOR — "merge first, require second."** Land the assembled `.github/` tree (workflows +
   payloads, but with the payloads **not yet applied**) as a commit on `develop-gsd` first, get it
   merged/promoted so the workflows exist on **both** `main` and `develop-gsd` before requiring
   anything — a base-repository-context workflow not yet on the default branch never fires, and under
   `bypass_actors: []` an unmet required context makes the branch unmergeable by **anyone**, including
   the owner. Concretely for pc2img's filtered-projection shape: the workflows must exist on `main`
   (via the very promotion this phase performs) **before** step 8 applies `main.json`.
8. **FLOOR** — Apply payloads via the dispatch-only `ruleset-apply.yml`, `main` first then
   `develop-gsd`. Read each back, confirm `bypass_actors` is present **and** an empty array (an absent
   key is a hard failure, not an empty list).
9. **DEFAULT** — One-time true-merge ancestry graft `main` → `develop-gsd`, on the `develop-gsd` side,
   after checking `git merge-tree --write-tree --name-only develop-gsd main` is clean **and** contains
   no planning path in its output. [VERIFIED: `develop-gsd` does not currently contain old `main` as
   an ancestor — confirmed in 06-CONTEXT.md's Integration Points note, and independently consistent
   with this session's `git log` showing `develop-gsd` forked from `dev/v2`, not from any prior `main`
   commit — so the graft **is** needed, matching D-08's closing note.]
10. **FLOOR** — Enable the nightly ancestry assertion (`scheduled-health.yml`'s `ancestry` job; its
    `schedule:` trigger only registers once the file is on the default branch — use
    `workflow_dispatch` first to prove the logic, then confirm the scheduled run fires post-promotion),
    and confirm it passes once before trusting it.

**Ordering consequence specific to pc2img's filtered-projection shape (D-08 Q3):** because `main` is
a filtered squash of `develop-gsd` rather than a branch anything merges into in the ordinary sense,
step 7's "land on the protected branch before requiring" and the phase's own D-17/D-18 ("all hygiene
on develop-gsd before the first promotion") are the **same constraint** stated twice: the promotion
that carries the assembled `.github/` tree onto `main` **is** the "merge first" step, and the
ruleset-apply dispatch against `main` (step 8) cannot run until after that promotion has happened.
Sequence for pc2img specifically: assemble + verify on `develop-gsd` → do the first promotion (carries
workflows + hygiene to `main`) → apply `main.json` → apply `develop.json` → graft → ancestry check.

### In-place edit sites (3 apply to pc2img; the GPU-related 3 do not)

[VERIFIED: `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` lines 355-361; site line numbers from
`~/gsd-workspaces/pchandler/.planning/git-strategy/template/core/.github/workflows/ci.yml`]

| # | Site | Kit's literal text | pc2img-specific fix |
|---|---|---|---|
| 1 | `ci.yml:305`, docs job "Build docs" step | `pip install .[doc]` | **Must change.** pc2img declares `doc` as a PEP 735 `[dependency-groups]` entry, not a `[project.optional-dependencies]` extra (`/scratch/31_pc2img/pyproject.toml:85`) — `pip install .[doc]` installs **nothing extra** and the build then fails on missing `sphinx`. [VERIFIED: `pip --version` in this environment reports `pip 25.1`, which supports `pip install --group doc` per PEP 735; `uv sync --help` confirms `uv sync --group <GROUP>` too, both checked this session] Recommended: replace with `uv sync --frozen --group doc` (consistent with D-10's uv-based composite, rather than mixing pip and uv in the same job) — or, if the runner's ambient `pip` version can't be guaranteed ≥25.1, keep uv. |
| 2 | `ci.yml:330` | `sphinx-build -W --keep-going -b html docs/source docs/_build/html` | No edit needed — D-13's chosen minimal layout already uses `docs/source/conf.py`; keep the build-output directory `docs/_build/html` (gitignore it). |
| 3 | `ci.yml:~318`, the version-assertion Python snippet | `tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["name"]` | No edit needed — pc2img already uses `pyproject.toml` as its packaging manifest (this is the "packaging manifest filename" site GIT-STRATEGY.md's closing note refers to). |

**GPU sites (3, in `gpu.yml`) do not apply** — the `gpu-self-hosted` component is not part of this
assembly (D-09).

### `release-please-config.json` `extra-files` reconciliation (D-13's open question, resolved)

[VERIFIED: `/scratch/31_pc2img/release-please-config.json:26`] Currently `"extra-files":
["docs/conf.py"]`, pointing at a file that has never existed (`git ls-files docs/` shows only
`docs/ip/*` and `docs/pchandler-2x-break-audit.md` — confirmed this session). [CITED:
`googleapis/release-please` `docs/customizing.md`, via WebSearch this session] release-please's
`extra-files` "generic" updater only rewrites a line carrying an `x-release-please-version` marker
comment; it does nothing to a file with no such marker. pc2img's own `ci.yml` docs-job version
assertion (in-place edit site 3 above) already derives the version **dynamically** at build time via
`importlib.metadata.version("pc2img")` (setuptools_scm-backed), so a Sphinx `conf.py` written the
modern way (`release = importlib.metadata.version("pc2img")`, no literal version string) needs **no**
release-please-driven rewrite at all. **Recommendation:** remove the `extra-files` key from
`release-please-config.json` entirely rather than repointing it to `docs/source/conf.py` — there is no
static version string in a dynamically-versioned `conf.py` for the generic updater to have a marker
on. If the planner instead wants a literal `release = "X.Y.Z"` string (e.g. for reproducible offline
doc builds without an installed distribution), then point `extra-files` at
`{"type": "generic", "path": "docs/source/conf.py"}` and add the `# x-release-please-version` marker
comment on that line — this is Claude's-discretion layout per D-13.

## Diff Against Current pc2img `.github/` and PCHandler Reference

| File | pc2img today | Kit (target) | Delta |
|---|---|---|---|
| `.github/workflows/ci.yml` | Single `tests` job; `astral-sh/setup-uv@v8.3.2` (tag); `--cov-fail-under=55` on the CLI [VERIFIED: `/scratch/31_pc2img/.github/workflows/ci.yml`] | 3 jobs (`Lint (pre-commit)`, `Tests (pytest)`, `Docs (sphinx -W)`), SHA-pinned actions, release-artifact fast path | **Wholesale replacement.** Carry the `--cov-fail-under=55` flag into the kit's `pytest` step per D-16; carry `fetch-depth: 0` (already present in both). |
| `.github/workflows/release-please.yml` | `push: branches: [main]`; unpinned `actions/checkout@v4`, `googleapis/release-please-action@v4`; uses default `GITHUB_TOKEN`; unguarded `git tag -d ... \|\| true` deletes [VERIFIED: `/scratch/31_pc2img/.github/workflows/release-please.yml`] | Same trigger shape but SHA-pinned, App-token-authenticated, and the tag-retag logic replaces silent `\|\| true` with status-checked `if ! ...` guards that name the failure | **Wholesale replacement.** No content is salvaged — even the trigger is identical only in shape. |
| `release-please-config.json` | Matches the kit **byte-for-byte** except the `extra-files` key [VERIFIED: diffed this session] | No `extra-files` key (or a corrected generic-typed one, see above) | Single-key fix. |
| `.release-please-manifest.json` | `{".": "0.10.4"}` | kit ships `{".": "0.0.0"}` (a placeholder for a fresh project) | **Do not overwrite with the kit's placeholder** — pc2img already has release history; keep `0.10.4` (D-01/D-02/D-03 govern how `0.11.0` is then reached). |
| `pyproject.toml` | ruff already configured (line-length 120, families E/F/W/I/B/C90/UP/NPY+ERA001); `[project.urls]` = homepage + documentation only; no `CITATION.cff` reference (file doesn't exist) | N/A — kit ships no `pyproject.toml`; this file is pc2img's own | Add `Repository`/`Issues`/`Changelog` urls (D-14); no ruff-config change needed. |
| PCHandler `RULESETS.md`/`RELEASE.md` reference instance | **Pre-template shape** — e.g. `required_linear_history` stated on **both** rulesets, `strict_required_status_checks_policy` OFF everywhere, single App (`APP_ID`/`APP_PRIVATE_KEY`) for release only, no ruleset-apply/drift workflow files exist yet in PCHandler's own `.github/` [VERIFIED: `find /scratch/41_pchandler/.github -type f` shows no `rulesets/`, `scripts/ruleset_lib.py`, etc.] | Template wins on every conflict (explicitly stated in `06-CONTEXT.md` canonical_refs) | Do not copy PCHandler's *current* `.github/` shape — only its App-provisioning *procedure* (`release-please-token.md`) and its `RULESETS.md`/`RELEASE.md`/`CITATION.cff`/`.readthedocs.yaml` *document structure* are worth reusing as templates for pc2img's own equivalents. |

## Lint Readiness (D-11) — measured this session, whole tree minus `.planning/`/`.claude/`

Ran `ruff check`/`ruff format --check` over **all 57 tracked `.py` files** outside `.planning/`/
`.claude/` (`git ls-files | grep -v -E '^(\.planning/\|\.claude/)'`), not just `src`/`tests` as D-11's
2026-09-28 measurement scoped it. Ruff version: `0.15.12` [VERIFIED: `ruff --version`, this session].

**`ruff format --check`:** 2 files need reformatting — `scripts/01_tiled_image_generation_from_pointcloud.py`
(scheduled for deletion, D-22) and **`setup.py`** (new finding, not previously flagged — trivial,
9-byte-stub file, `ruff format setup.py` fixes it).

**`ruff check`:** 25 hits total, **13 more than D-11's documented 12**, but the extra 13 are **all** in
`scripts/01_tiled_image_generation_from_pointcloud.py` (the file D-22 deletes) except **one**:

| File | Rule(s) | Count | Disposition |
|---|---|---|---|
| `src/pc2img/features/derivative_features.py` | C901 (×4) | 4 | Already known (D-11); pre-existing complexity, out of phase 6 scope — keep as a per-function `noqa` or a raised C901 threshold, planner's discretion. |
| `src/pc2img/util.py` | C901 (×2) | 2 | Same as above. |
| `tests/test_disk_backed_image_data.py` | NPY002 (×2) | 2 | Already known (D-11). |
| `tests/test_util.py` | ERA001 (×2) | 2 | Already known (D-11) — the `# Breadth:` headers. |
| `tests/test_tiled_generator.py:27` | F401 | 1 | Already known (D-11) — unused `pytest` import. |
| `tests/test_point_cloud_image_generator.py:1` | I001 | 1 | Already known (D-11) — import sort. |
| **`scripts/smoke_pipeline.py:23`** | I001 | 1 | **NEW — not in D-11's 12.** Autofixable (`ruff check --fix`). |
| `scripts/01_tiled_image_generation_from_pointcloud.py` | I001, UP045, E714, E501×2, F841, ERA001×6 | 12 | Entire file is deleted per D-22 — this whole row disappears with the delete, not with a fix. |

**Net remediation surface once D-22's delete lands:** the original 12 (C901×6, NPY002×2, ERA001×2,
F401×1, I001×1) **plus 1 new** (`smoke_pipeline.py` I001, trivially autofixable) = **13** hits, none
of them touching `scripts/01_...`. `ruff check --fix` mechanically resolves I001/F401/UP045/E714
(6 fixable per the tool's own count); C901/ERA001/NPY002/E501/F841 need hand judgment or config
(`--fix` explicitly reports "6 fixable... 1 hidden fix").

Pre-commit hooks available offline: [VERIFIED: `which ruff` → `/home/nixton/.local/bin/ruff`, version
`0.15.12` present in this environment] `ruff` itself is available without network access. Standard
hygiene hooks (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`,
`check-added-large-files` — all from `pre-commit/pre-commit-hooks`) are **not yet vendored/cached** in
this environment; `pre-commit` itself is not installed in `.venv` — confirm network access at CI-run
time (`pip install pre-commit` is the kit's own first step in the lint job, so this is a CI-time
concern, not a planning blocker).

## Docs (D-13) — measured this session

Sphinx `~=5.1` resolves `Sphinx 5.3.0` cleanly via `uv run --no-project --with "sphinx~=5.1" --with .`
[VERIFIED: this session — command output shows "Running Sphinx v5.3.0"]. A throwaway
`docs/source/conf.py` (extensions: `autodoc`, `napoleon`, `viewcode`) + `index.rst` with
`automodule::` directives over 7 representative modules (`pc2img`, `pc2img.util`, `pc2img.core`,
`pc2img.features.derivative_features`, `pc2img.strategies.projection`,
`pc2img.strategies.interpolation`, `pc2img.image_cache.disk_backed_image_store`) built with
`sphinx-build -W --keep-going -b html` **exits 1** (confirmed via explicit exit-code capture, not
piped through `tail`) on **13 warnings**:

- `MultiScaleGradientFeature` docstring: "Unexpected indentation" (line 3) + **"Undefined substitution
  referenced: ∇"** (line 7, ×2) — a real content bug: the docstring uses an RST substitution-reference
  syntax (`|∇I|`-shaped) without a `.. |∇I| replace::` definition anywhere in scope.
- `OcclusionAwareMultiScaleGradientFeature`, `AverageFeature`: "Unexpected indentation" /
  "Block quote ends without a blank line" — classic numpydoc-section-under-napoleon formatting gaps
  (a `Notes`/`Examples` block probably lacks a blank line before an indented block).
- `OrthographicProjection` (×1, cascades to 3 duplicate "Block quote" warnings across its methods),
  `PerspectiveProjection.project_raw`, `ProjectionStrategy.project_raw`,
  `SphericalProjection.project_raw`: all "Unexpected indentation" at line 3 of the docstring — the
  **same shape recurring across every `project_raw` override**, suggesting a shared docstring-template
  issue (likely a `Parameters`/`Returns` section whose continuation line isn't indented to the
  napoleon-expected 4 spaces).

This was a **7-module sample**, not the full `src/pc2img/` tree (~15+ modules) — treat 13 as a lower
bound; a full-tree autodoc pass will surface more of the same shapes. No version-compatibility issue
was found; **all 13 are docstring content bugs**, fixable independent of any Sphinx/napoleon version
choice. RTD hosting: `/scratch/41_pchandler/.readthedocs.yaml` is a usable structural model
(`build.os: ubuntu-24.04`, `build.tools.python: "3.12"`, `sphinx.configuration: docs/source/conf.py`,
`python.install` via `pip . + extra_requirements: [doc]`) — **note the last line needs the same PEP
735 reconciliation as in-place edit site 1 above**: `extra_requirements: [doc]` is RTD's own
extras-based install mechanism and will not pick up a PEP 735 dependency-group either; RTD's
`.readthedocs.yaml` v2 schema has no native dependency-group install verb, so the safest fix is an
explicit `python.install` step list: `- method: pip / path: .` then a second entry
`- requirements: docs-requirements.txt` (a small pinned `sphinx==<version>` file), OR keep `doc` as a
real PEP 621 extra in `[project.optional-dependencies]` specifically because RTD cannot consume PEP 735
groups — **this is a genuine constraint the planner should resolve explicitly, not default past**: RTD
needs `pip install .[doc]` (an actual extras group) to work at all, which conflicts with D-08's "PEP
735 for tooling deps" pattern used for `dev`. Recommend keeping `doc` as `[project.optional-dependencies]`
(a real extra, published in wheel metadata but empty of runtime impact — it's a docs-only tool) rather
than folding it into `[dependency-groups]`, since RTD is an external consumer that cannot resolve
`[dependency-groups]` at all. This reverses the "PEP 735 for everything" framing pc2img has used since
Phase 2 for `doc` specifically — flag as a one-line confirmation, not a full CONTEXT re-discussion,
since 06-CONTEXT.md's D-14 already treats `doc`'s group-vs-extra question as unresolved region (D-13
only fixed the layout, not the packaging mechanism).

**`x-release-please-version` marker convention:** see *`release-please-config.json` extra-files
reconciliation* above — recommend omitting the marker/extra-files entry entirely given the dynamic
version derivation already used elsewhere in the kit's own `ci.yml`.

## Metadata / Build (D-14)

[VERIFIED: `/scratch/41_pchandler/CITATION.cff`] Shape to model: `cff-version: 1.2.0`, `authors` list
(name/affiliation/orcid), `repository-code`/`url`, `license: BSD-3-Clause`, a `message:` about the
main-branch-reflects-latest-release convention, and a `preferred-citation` block with a placeholder
Zenodo DOI (`10.5281/zenodo.XXXXXXX`) — pc2img has no archive DOI yet either; carry the same
placeholder-with-a-note pattern rather than inventing one. Per D-14, **authors unchanged** — pc2img's
author list stays just Nicholas Meyer (no Jon Allemand addition), unlike PCHandler's two-author file.

`README.rst` is currently literally `##Hello` [VERIFIED: `cat README.rst`, this session] and is the
PyPI long description (`[tool.setuptools.dynamic] readme = {file = ["README.rst"]}`,
`pyproject.toml:48`). `python -m build --wheel --sdist` + `twine check dist/*` viability: not
independently probed this session (would require building against the real environment, which is
plausible but not yet exercised) — **flag as a build-time check the plan should include**, since an
`.rst` long-description with malformed markup fails `twine check` silently-until-upload otherwise.
PEP 740 attestations: automatic via `pypa/gh-action-pypi-publish@v1.14.0`'s default
(`attestations: true` is the action's default per the kit's own comment,
`publish-pypi.yml:70` — no extra config needed). TestPyPI dry run wiring: **separate dispatch-only
workflow** (`publish-testpypi.yml`), `workflow_dispatch` trigger, environment name `testpypi`,
`repository-url: https://test.pypi.org/legacy/`, `attestations: false` (test index's attestation
support is "inconsistent" per the kit's own comment), `skip-existing: true` to tolerate repeat
dispatches from the same commit.

## Planning-Vocabulary Sweep (D-20) — regex run this session over the whole shipped tree

Gate pattern used: `\b(BUG|DSN|QUAL|TEST|DEP|CICD|BC)-[0-9]+\b|\bM-[0-9]{1,3}\b|\bD-[0-9]{1,3}\b`
plus a separate phase-reference pass (`\bphase[- ]?[0-9]+(\.[0-9]+)?\b`, case-insensitive) and a
literal `.planning` path pass, run over `git ls-files | grep -v -E '^(\.planning/|\.claude/)'` (57
files). [VERIFIED: this session, exact grep commands and output captured]

**Known hits confirmed present** (all match D-20's prediction): `pyproject.toml` (10 D-NN/QUAL/TEST
comment hits), `CONTRIBUTING.md` (6 TEST-03..06/Phase-3/Phase-5 hits), `docs/pchandler-2x-break-audit.md`
(7 hits — DEP-01/02, D-11, D-13, D-02, Phase-2 references; **this file moves per D-21**, so its hits
travel with it and are exempt by relocation), `docs/ip/rrim-eth-signoff.md` (2 hits — D-10, D-07; **exempt
verbatim per D-23**).

**Round-5 leftover items** (`test_rrim_features.py`, `test_feature_registry.py`, `test_image_store.py`,
`disk_backed_image_store.py`) named in D-20 as carrying `review-r4-*`/`review-r5-*` ledger IDs: **a
`grep -rnE 'review-r[0-9]-[0-9a-f]{6,}'` over the whole tree returned zero hits** — these appear to
already be clean, consistent with STATE.md's Phase-05-P19 note that IN-04's sweep was "widened...to
all planning vocabulary...in both src/pc2img and tests/" and executed. **Do not assume D-20's named
line numbers are still accurate** — the files at those approximate line ranges now discuss the
containment-guard threat model and RRIM round-trip semantics in plain prose, with no residual ledger
IDs; treat D-20's line citations as historical, not a live to-do list.

**New hits this research surfaced, not in D-20's known list:**

| File | Hits | Notes |
|---|---|---|
| `scripts/smoke_pipeline.py` | `D-10` (×2, lines 5 and 44), `D-09` (line 6), "Phase 2"/"Phase 4/5" phase refs (lines 6-7, 60, 62) | This script **stays** per D-22 (only `01_...` is deleted) — these hits need cleaning, not deletion. Also carries the new ruff I001 hit noted above. |
| `.github/workflows/ci.yml:41` | "Phase 5" | **Moot** — this file is wholly replaced by the kit's `ci.yml` in this phase; the hit disappears with the replacement, not with an edit. |
| `tests/test_image_store.py:63` | "pre-Phase-2" | Present in a docstring; sweep along with the others — worth confirming this doesn't collide with the "already clean" round-5 claim since it's a distinct location from the ones D-20 named. |

**`.planning` path references:** exactly one hit — `docs/pchandler-2x-break-audit.md:98`, a reference
to a pending todo file path. Travels with the file's D-21 move; not a separate fix.

## Migration Record (BC-01)

### Format — read from PCHandler's exemplar this session

[VERIFIED: `/scratch/41_pchandler/MIGRATION-v1.0.md`] Frontmatter: `type: migration-spec`,
`spec_version`, `repo`, `baseline_ref`, `target_ref`, `generated_at`, `bc_id_prefix`. Body sections in
order: `# {repo} MIGRATION-v{X}` heading with **Baseline**/**Target** restated in prose, `## Summary`
(prose, names the phase count and the dominant category), `## Public API stability invariant` (prose,
states what the verifier proves and cites the one deliberately-downgraded severity with its
rationale), `## Breaking changes & behavior changes` (table: BC-ID / category / severity /
affected_symbols / origin / migration_steps), `## Additive changes` (same table shape, `additive`
severity only), `## Internal & sweep changes` (a flat bullet list, **not** a table — each bullet cites
its origin markers and states "no public-surface change" explicitly), `## Verifier (inline)` (a fenced
` ```python ` block, runnable standalone, with a doc-comment stating the exact extraction command:
`awk '/^## Verifier \(inline\)$/,/^```$/'` piped through `sed`).

**BC-ID aggregation rule** (stated in PCHandler's own file, footnote-style, last bullet of *Internal &
sweep changes*): "one BC entry per **observable downstream effect**, with multi-decision markers
aggregated into a single entry whenever the observable effect is shared." pc2img's `05-BC-NOTES.md`
already follows this convention (e.g. its entry 3 aggregates `nanconv`'s float16→float32 fix **and**
its `compute_dtype` additive param into one numbered note, split correctly into two BC-P2I entries by
severity when transcribed, since one half is `should-review`/`must-edit`-shaped BREAKING and the other
is `additive`).

### Verifier design — adapted, not copied (pc2img has no `.pyi` stub files)

PCHandler's Tier-1 verifier AST-walks 6 `__init__.pyi` stub files and extracts `__all__` +
`from .X import Y as Y` re-exports. **pc2img ships no `.pyi` files** — [VERIFIED:
`/scratch/31_pc2img/CLAUDE.md` "Module Design" section: "Every package `__init__.py` declares
`__all__` explicitly and re-exports the public surface"] pc2img's public surface is declared directly
in `__init__.py` files (`src/pc2img/__init__.py`, `features/__init__.py`, `strategies/__init__.py`,
`image_cache/__init__.py`), not in separate stubs. The adapted Tier-1 pass should AST-walk those **4**
`__init__.py` files' `__all__` assignments directly (same `ast.Assign` extraction logic PCHandler
uses, applied to `.py` instead of `.pyi`) — confirmed structurally viable this session by reading
`src/pc2img/__init__.py`'s literal `__all__` list. Tier-2 runtime `getattr` checks are needed for every
`surface-removed`/`signature-shape`/`error-behavior` entry the same way PCHandler's checks
`OptimizedShiftManager.minimum_decimal_places.fset is None` — pc2img's analogous checks (from
`05-BC-NOTES.md`, all already stated precisely enough to code directly):

- Entry 7: `import pc2img.errors; assert issubclass(pc2img.errors.RegistryLookupError, (KeyError, RuntimeError))`.
- Entry 9: `DiskBackedImageData() + DiskBackedImageData()` returns `type(...) is np.ndarray`, not raises.
- Entry 8: a legacy `.pkl` cache path degrades to a miss (already has a dedicated test,
  `tests/test_image_store.py:63`'s "pre-Phase-2 `.pkl`" case — reuse pattern, don't re-derive).
- Entry 15: `DiskBackedImageStore.__setitem__`/`add_image_to_store` with a `../victim`-shaped key
  raises `ValueError` (already has dedicated tests per the BC-note's own citations — the verifier can
  re-run the same assertion shape, not necessarily re-import the test file).

### Entry inventory sourced this session

**Primary source, already complete:** `05-BC-NOTES.md`'s 17 numbered entries (read in full this
session) map close to 1:1 onto `BC-P2I-NNN` rows — entry 10 (GSEGUtils dependency bridge) is already
**closed** (resolved pre-ship in Phase 5 per the note's own "✅ DONE" marker) and should be transcribed
as `dep-constraint`/`informational` (historical record) rather than as an open action item; entries
5, 6, 17 are explicitly "NO BEHAVIOR CHANGE" / "NO CHANGE" and should land as `additive-or-fixed`/
`informational`, matching PCHandler's own precedent of recording no-op changes for traceability
(`BC-PCH-015`-adjacent entries in the *Internal & sweep changes* bullet list, not the breaking table).

**Phase 1-4 additions not yet in `05-BC-NOTES.md`** (identified via `git diff --stat 91b4ab6..HEAD --
src/ pyproject.toml`, [VERIFIED: this session — 23 files changed, +2285/-940 lines]):

- `make_generator` factory: deleted in Phase 4 (`04-03-PLAN.md`, zero callers found) — `surface-removed`,
  `informational` (dead code, never functional — CONTEXT.md's own Anti-Patterns section calls it
  "Stale/broken `make_generator` factory").
- `PerspectiveProjection`: folded onto mainline in Phase 1 (D-02), WIP math finished in Phase 4/5 —
  `additive-or-fixed`, new public strategy, already covered by BC-notes entries 2 and 13 for its
  *behavior*, but its **existence** (Phase-1 addition to `PROJECTIONS` registry) is a separate,
  earlier-dated additive entry worth its own BC-ID for completeness.
- `convert_to_image` duplicate removed (Phase 4, QUAL-01) — `surface-removed`/`informational` (the
  removed copy was dead, matplotlib-referencing; the surviving one is unchanged).
- `matplotlib` moved to optional `viz` extra (Phase 4) — `dep-constraint`/`should-review`: a caller
  requesting a colormap now needs `pip install pc2img[viz]` or gets the existing lazy
  `RuntimeError("Colormap requires matplotlib")`.
- numpy 2.x pin, `pchandler ~= 2.1` pin, `GSEGUtils >= 0.5.3, < 1.0` pin, `joblib` collapse to one
  `~= 1.5` pin (Phase 2/4) — `dep-constraint` entries, several already implicit in `05-BC-NOTES.md`
  entry 10 but the base numpy/pchandler pins themselves predate Phase 5 and are not yet recorded
  anywhere as BC entries.
- Phase 6's own entries (per D-27): tag retirement / version-line change (D-01/D-02, `dep-constraint`),
  the PyPI move itself (downstream should drop git pins and depend on `pc2img ~= 0.11`,
  `dep-constraint`/`should-review`), and the README/metadata replacement (`additive-or-fixed`,
  `informational`).

### Baseline/target verification

[VERIFIED: this session] `91b4ab6` is a real, reachable commit; `git merge-base --is-ancestor 91b4ab6
origin/develop-gsd` — not independently re-run this session (D-26 already states it is "the exact fork
point of develop-gsd," dated 2025-11-06, and this research did not find any reason to doubt it). Target
for the Phase-6 draft is `develop-gsd` HEAD at whatever commit the phase's first-promotion work lands
on — **not** a fixed SHA yet, since the phase itself will add commits after this research. The plan
should resolve `target_ref` at the point the migration-record-drafting task actually runs, not hardcode
a SHA now.

## Versioning (D-01..D-06) — measured this session

[VERIFIED: this session] `git tag -l` on origin shows: `archive/dev-perspective_projection-pre-fold`,
`v0`, `v0.10`, `v0.10.0`..`v0.10.4`, `v2.0.0a5`. `fetch.pruneTags = true` is set (confirms D-02's stated
risk is real and current). `v2.0.0a5` is a real (non-lightweight — `git cat-file -t v2.0.0a5` → `commit`,
i.e. an **annotated-looking but actually a lightweight commit-pointing** tag object type check returned
`commit` not `tag`, meaning it is in fact a **lightweight** tag) tag at `0b1e94392ba0e436377a3a82b92e03ea2f2e3b5d`
(2025-08-18), and **is** an ancestor of `origin/develop-gsd` (`git merge-base --is-ancestor v2.0.0a5
origin/develop-gsd` → true) — confirming D-02's premise that this tag is reachable from the branch
whose builds it corrupts. `git describe --dirty --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*'` cannot
be run against a non-checked-out ref directly (`--dirty` requires an actual working tree, not a
commit-ish) — the **correct** verification after D-02's rename is to `git checkout develop-gsd` (or
run in CI) and confirm `git describe --tags --long --match 'v[0-9]*.[0-9]*.[0-9]*'` reports
`v0.10.4-N-g<hash>`, not `git describe ... origin/develop-gsd` from a detached read — note this
distinction for the plan's verification step, since the exact command in D-02 (`git describe` with a
commit-ish argument plus `--dirty`) will error as written. Plain `git describe --tags --long
origin/develop-gsd` (no `--match`) returns `archive/dev-perspective_projection-pre-fold-308-ge9eb3c4` —
confirms setuptools_scm's own `--match 'v[0-9]*.[0-9]*.[0-9]*'` filter is load-bearing (an unfiltered
describe picks up the unrelated archive tag first).

## Common Pitfalls

### Pitfall 1: Applying `release-please-config.json`'s placeholder manifest
**What goes wrong:** The kit ships `.release-please-manifest.json` as `{".": "0.0.0"}` — a fresh-project
placeholder. Copying it verbatim over pc2img's real `{".": "0.10.4"}` resets release-please's version
memory and the next release PR would try to bump from `0.0.0`.
**Why it happens:** Step 2/3 of Procedure B says "copy `core/`... copy `release-pypi/`... substitute
tokens" — nothing in the procedure calls out that this one file is **not** a template to substitute
tokens into, it is real project state that happens to sit at the same path the kit also ships a file
at.
**How to avoid:** Treat `.release-please-manifest.json` as a merge conflict, not a copy target — keep
pc2img's `0.10.4`, discard the kit's `0.0.0`.
**Warning signs:** `git diff` after the assembly step shows this file's line changing from `0.10.4` to
`0.0.0` — catch it in review before committing.

### Pitfall 2: `.[doc]`/`.[dev]` extras vs. pc2img's PEP 735 dependency-groups
**What goes wrong:** Both the kit's `setup-python-deps` composite (`pip install .[dev]`) and the docs
job's in-place edit site (`pip install .[doc]`) assume `[project.optional-dependencies]` extras. pc2img
uses `[dependency-groups]` for both `dev` and `doc` (PEP 735) — neither extra exists, so both installs
silently install **nothing** and the subsequent `pytest`/`sphinx-build` invocations fail on missing
modules, or worse, silently run against whatever happened to already be in the runner's base Python
(unlikely on `ubuntu-latest`, but not impossible if a system package shares a name).
**Why it happens:** The kit is written against a generic PyPI-extras convention; pc2img made a
different (also valid) packaging choice in Phase 2 (D-08).
**How to avoid:** D-10 already resolves this for the `setup-python-deps` composite (`uv sync --frozen`).
This research additionally surfaces that the **docs job's own in-place `pip install .[doc]` line
(edit site 1) needs the same treatment** — it is easy to miss because it is not inside the composite
D-10 already covers, it is a separate line inside `ci.yml`'s `docs:` job.
**Warning signs:** `ModuleNotFoundError: No module named 'sphinx'` in the `Docs (sphinx -W)` job despite
`setup-python-deps` having "succeeded."

### Pitfall 3: RTD cannot consume a PEP 735 dependency-group either
**What goes wrong:** `.readthedocs.yaml`'s `python.install.extra_requirements` mechanism is
extras-based (same as pip's `.[doc]`), not dependency-groups-aware. If `doc` stays a
`[dependency-groups]` entry, the RTD build fails to install Sphinx at all, independent of whatever fix
is chosen for CI.
**Why it happens:** RTD's config schema predates PEP 735 and has no native group-install verb.
**How to avoid:** Either keep `doc` as a real `[project.optional-dependencies]` extra (recommended,
since it is docs-tooling-only and the "PEP 735 for everything" rationale in D-08 was really about
`dev` not leaking into the published wheel — a `doc` extra leaking into wheel metadata is harmless),
or give `.readthedocs.yaml` an explicit second `python.install` step listing a small pinned
requirements file.
**Warning signs:** RTD build log shows `sphinx-build: command not found` despite a green local build.

### Pitfall 4: Assuming the D-20 sweep's cited line numbers are still current
**What goes wrong:** D-20 cites specific `file:line` locations for round-5 leftovers
(`test_rrim_features.py:236-237`, etc.) from a session that has since had further commits land
(05-16..05-19). Re-running the exact grep this research ran found **zero** `review-r*-<hex>`-shaped
IDs anywhere in the shipped tree — the citations describe *historical* locations, already cleaned.
**Why it happens:** CONTEXT.md documents were gathered before the final Phase-5 gap-closure rounds
fully landed; STATE.md's own Phase-05-P19 note says the sweep was later "widened... to all planning
vocabulary."
**How to avoid:** Re-run the sweep regex fresh at plan-execution time rather than trusting the cited
line numbers as a checklist; use the regex, not the citations, as the source of truth. (This research's
own regex output, above, is the current ground truth as of 2026-09-28.)
**Warning signs:** A task that reads "fix `test_rrim_features.py:236-237`" and finds nothing to fix
there — that's not a defect in the task, it means the item is already resolved; don't invent a change
to make the line count match.

## Code Examples

### Adapted verifier Tier-1 extraction (pc2img has `.py` `__all__`, not `.pyi`)
```python
# Source: adapted from ~/gsd-workspaces/pchandler/MIGRATION-v1.0.md's _extract_declared_names,
# re-targeted at pc2img's __init__.py __all__ lists (no .pyi stubs exist in this repo).
import ast
import pathlib

PUBLIC_SURFACE_FILES = [
    "src/pc2img/__init__.py",
    "src/pc2img/features/__init__.py",
    "src/pc2img/strategies/__init__.py",
    "src/pc2img/image_cache/__init__.py",
]

def extract_all(py_text: str) -> set[str]:
    tree = ast.parse(py_text)
    declared: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__" and isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            declared.add(elt.value)
    return declared
```

### Docs job's PEP-735-correct in-place edit (site 1)
```yaml
# Source: adapted from ~/gsd-workspaces/pchandler/.planning/git-strategy/template/core/.github/workflows/ci.yml:305
# pc2img's `doc` group is PEP 735 (dependency-groups), not a [project.optional-dependencies] extra —
# see 06-RESEARCH.md "In-place edit sites" #1. Consistent with D-10's uv-based setup composite.
- name: Build docs (warnings as errors)
  if: steps.classify.outputs.release-artifacts-only != 'true'
  working-directory: .
  run: |
    uv sync --frozen --group doc
    # ...version-assertion snippet unchanged...
    uv run sphinx-build -W --keep-going -b html docs/source docs/_build/html
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `workflow_run`-chained release automation | Direct `push: branches: [<MAIN_BRANCH>]` trigger + `strict_required_status_checks_policy: true` | Landed in this kit (supersedes pc2img's 2026-07-27 "adopt the floor, defer the flow" decision per D-07) | Removes a silent-failure mode (a cancelled CI run on `main` used to make the `workflow_run` gate read false and skip the release with nothing red). |
| Legacy branch protection API | Rulesets API (`POST /repos/{owner}/{repo}/rulesets`) | Already GitHub's current recommended mechanism | Both are blocked identically on a private free-plan repo, but pc2img is public, so this is moot for Phase 6 — noted only because Procedure A's blocked-state language could otherwise mislead. |
| `format(v, "g")` RRIM z-token formatting | `repr(float(v))` shortest-round-trip formatting | Phase 5, plan 05-14 (05-BC-NOTES entry 14) | Already landed; relevant to the migration record, not to new work this phase. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Secret names `RULESET_APP_ID`/`RULESET_APP_PRIVATE_KEY` and `RELEASE_APP_ID`/`RELEASE_APP_PRIVATE_KEY` are good choices for the two Apps' credentials | *Secret naming* | Low — these are free-text names substituted into the kit's tokens; any distinct, non-colliding pair works. Owner can rename at the D-30 checkpoint with no downstream effect beyond re-running the token substitution. |
| A2 | The three GitHub Apps read via `gh api orgs/gseg-ethz/installations` are not yet added to `pc2img` specifically | *Current-repo state* | Medium — if the owner already added pc2img to one/all of them between context-gathering and plan execution, the D-30 checkpoint for that item becomes a no-op verify rather than an add-then-verify; re-check with `gh api repos/gseg-ethz/pc2img/installation` (requires the App's own token, not available this session) or ask the owner directly at execution time. |
| A3 | `doc` should become a `[project.optional-dependencies]` extra rather than staying a PEP 735 `[dependency-groups]` entry, because RTD cannot consume dependency-groups | *Docs*, Pitfall 3 | Medium — this reverses part of D-08's Phase-2 PEP-735-for-everything framing for one specific group. If the owner prefers keeping `doc` as a dependency-group, RTD's `.readthedocs.yaml` needs an explicit pinned-requirements-file workaround instead; either is workable, but the choice should be made explicitly, not defaulted past. |
| A4 | The 13 measured Sphinx warnings are representative and a full-tree autodoc pass will not surface qualitatively different failure classes | *Docs* | Low — sampled 7 of ~15+ modules; the shapes seen (indentation, undefined substitution) are docstring-authoring patterns likely to recur elsewhere in the same style, not module-specific. |
| A5 | `docs/ip/rrim-ip-findings.md` can be swept for planning vocabulary without altering its attested findings (per D-23's "planner's judgement, flag if unsure") | *Planning-Vocabulary Sweep* | Medium — this research did not diff that file's content against the planning-vocab regex in detail (deprioritized under the IP-verbatim caution D-23 already raises); the plan should grep it specifically and read any hits in context before editing, per D-23's own instruction. |

## Open Questions

1. **Are the two GitHub Apps (`gseg-ruleset-admin`, `gseg-release-please`) already added to `pc2img`'s
   repo-selection list?**
   - What we know: both Apps exist at the org level (`gh api orgs/gseg-ethz/installations` confirms
     App IDs 4427434 and 4039497), with `repository_selection: "selected"`.
   - What's unclear: whether `pc2img` is already in that selected-repos list — the read-only API call
     available this session cannot enumerate an installation's member repos without the App's own
     token.
   - Recommendation: the D-30 checkpoint task for this item should start with a verification read
     (`gh api repos/gseg-ethz/pc2img/installation` once the App token is available, or simply attempt
     the first ruleset-apply dispatch and read the failure if the App isn't installed) rather than
     assuming either state.

2. **Does `docs/ip/rrim-ip-findings.md` (referenced by `NOTICE`) contain any planning-vocabulary hits
   that D-23 requires judgement on?**
   - What we know: `docs/ip/rrim-eth-signoff.md` (the sibling, verbatim-exempt file) has 2 hits; this
     research did not separately grep `rrim-ip-findings.md`.
   - What's unclear: whether it has similar hits and whether removing them would alter the attested
     findings.
   - Recommendation: run the same regex against this specific file as a dedicated plan step, and read
     any hits in full context before deciding sweep-vs-exempt, per D-23's own instruction.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `ruff` | Lint job / pre-commit | ✓ | 0.15.12 | — |
| `pytest`, `uv` | Tests job | ✓ (confirmed via `uv run --frozen pytest`, 196 passed) | project-pinned | — |
| `sphinx` (ephemeral resolve) | Docs job | ✓ (resolved via `uv run --with "sphinx~=5.1"`) | 5.3.0 resolved | — |
| `pre-commit` (CLI, not the hook definitions) | Lint job's own bootstrap step | ✗ in this session's `.venv` | — | The kit's lint job installs it itself (`python -m pip install pre-commit`) — not a planning blocker, just not pre-cached locally. |
| `gh` CLI with repo-admin scope | Owner checkpoints (App install, secrets, environments) | ✓ for read-only calls this session (repo/org reads succeeded); write-scope calls were not attempted (out of scope for research) | — | — |
| TestPyPI/PyPI trusted-publisher registration | D-30 item 3 | Not probed this session (would require a write action) | — | Owner action at execution time, per D-30. |

**Missing dependencies with no fallback:** none — everything needed for Phase 6 is either already
present or self-installs inside CI per the kit's own design.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (project-pinned `~=9.1`) + pytest-cov `~=5.0` + coverage `~=7.0` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run --frozen pytest -q` |
| Full suite command | `uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing --cov-fail-under=55` |

**Current baseline, measured this session:** 196 passed, 0 failed, coverage **62.27%** (floor 55%,
D-16 keeps this floor as a recorded template addition).

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CICD-02 | Assembled workflows produce the 3 named required-status contexts | integration (CI-run) | Ruleset apply + a real PR's checks page — not unit-testable locally; use the apply-time checklist evidence commands above | N/A — verified by running the actual CI, not a local test file |
| CICD-02 | `.github/scripts/ruleset_lib.py`, `preflight_ruleset_apply.py`, `check_ruleset_drift.py` behave correctly | unit | `pytest .github/scripts/ -q` (kit-shipped tests: `test_ruleset_lib.py`, `test_preflight_ruleset_apply.py`, `test_check_ruleset_drift.py`, `test_classify_changes.py`) | ✅ shipped by the kit itself |
| CICD-02 | No placeholder token survives assembly | mechanical | `! grep -rn '<[A-Z_][A-Z_]*>' .github/ release-please-config.json .release-please-manifest.json` | ✅ — verification command (1), see *Apply-Time Checklist* |
| CICD-02 | Lint job green on whole shipped tree | integration | `ruff check $(git ls-files | grep -vE '^(\.planning/|\.claude/)' | grep '\.py$')` + `ruff format --check` (same fileset) | ❌ Wave 0 — 13 hits remain to fix (post-D-22-delete), see *Lint Readiness* |
| CICD-02 | Docs job builds clean under `-W --keep-going` | integration | `sphinx-build -W --keep-going -b html docs/source docs/_build/html` | ❌ Wave 0 — `docs/source/` doesn't exist yet; 13+ docstring warnings to fix once it does, see *Docs* |
| BC-01 (draft) | Migration-record inline verifier passes | unit (standalone script) | extract + run the `## Verifier (inline)` fenced block per PCHandler's own documented extraction command | ❌ Wave 0 — `MIGRATION-v0.11.md` doesn't exist yet |

### Sampling Rate
- **Per task commit:** `uv run --frozen pytest -q` (quick) + `ruff check`/`ruff format --check` on
  touched files.
- **Per wave merge:** full suite (`--cov-fail-under=55`) + the whole-tree ruff pass + (once assembled)
  `pytest .github/scripts/ -q`.
- **Phase gate:** full suite green, apply-time checklist evidence recorded, Sphinx `-W` build green,
  migration-record verifier green, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `docs/source/conf.py` + `docs/source/index.rst` — does not exist yet (D-13).
- [ ] `.pre-commit-config.yaml` — does not exist yet (D-11).
- [ ] `MIGRATION-v0.11.md` — does not exist yet (BC-01 draft).
- [ ] `CITATION.cff` — does not exist yet (D-14).
- [ ] The kit's own `.github/scripts/test_*.py` files (ship with the assembly — not a gap once
      `core/` is copied, but they must be run at least once post-assembly to confirm they pass
      unmodified against pc2img's specific tokens).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface in this phase — CI/CD and packaging only. |
| V3 Session Management | No | N/A |
| V4 Access Control | Yes | `bypass_actors: []` on both rulesets (FLOOR); two separate GitHub Apps (protection vs. release) so a compromise of one cannot rewrite the other's domain — least-privilege by App scope, not by role within one credential. |
| V5 Input Validation | Yes (narrowly) | `check_publish_gate.py`'s YAML parsing of untrusted workflow files uses `yaml.safe_load` (never `yaml.load`), and treats an unparseable workflow as a **violation**, not a skip — fail-closed. |
| V6 Cryptography | No direct control needed | OIDC token minting (`actions/create-github-app-token`, PyPI trusted publishing) is handled entirely by vetted third-party actions/platform mechanisms; nothing here hand-rolls crypto. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `pull_request_target` combined with a head-ref checkout ("pwn request") | Elevation of Privilege | Never used anywhere in this assembly (continuous-enforcement, the only component that would need it, is declined per D-09) — verify via `grep -rn pull_request_target .github/workflows/` returning empty, item 4 of the apply-time checklist. |
| A required-context job with a job-level `if:` or filtered trigger, silently satisfying the gate | Tampering / Elevation of Privilege (bypasses `bypass_actors: []`) | FLOOR: fast-path conditionality lives on **steps**, never on the job; no `paths:`/`branches:` filter under `pull_request:` on a required-context workflow. Verified structurally present in the kit's shipped `ci.yml` this session. |
| A publish step (PyPI upload) added to a workflow other than the two named ones, or under the wrong environment | Tampering (unauthorized publish identity) | `check_publish_gate.py`'s containment check, run every lint job — fails the build if a `pypa/gh-action-pypi-publish`/`twine upload` step appears anywhere else, or in the right file under the wrong `environment:`. |
| A rolling major/minor tag (`v0`, `v0.10`) force-moved by an untrusted actor | Tampering | Tag pushes in `release-please.yml` are status-checked (`if ! git push origin ":refs/tags/$TAG"`) — a refused deletion (tag protection/ruleset/scope) is a **named** failure, not silently ignored; git identity is the App token, not a PAT. |

## Sources

### Primary (HIGH confidence)
- `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` — read in full this session (1545 lines).
- `~/gsd-workspaces/pchandler/.planning/git-strategy/template/{core,optional/release-pypi}/**` — every
  file read in full this session.
- `~/gsd-workspaces/pchandler/.planning/release-please-token.md` — read in full.
- `~/gsd-workspaces/pchandler/MIGRATION-v1.0.md` — read in full (233 lines).
- `/scratch/41_pchandler/{RULESETS.md,RELEASE.md,.readthedocs.yaml,CITATION.cff}` — read in full.
- `/scratch/31_pc2img/{.github/workflows/*.yml,pyproject.toml,release-please-config.json,.release-please-manifest.json,README.rst,NOTICE,CONTRIBUTING.md,05-BC-NOTES.md}` — read in full this session.
- Measured this session: `ruff check`/`ruff format --check` (whole tree), `pytest` (196 passed,
  62.27% coverage), `sphinx-build -W --keep-going` (13 warnings, exit 1), `git` tag/describe/ancestry
  probes, `gh api` read-only repo/org state.

### Secondary (MEDIUM confidence)
- `googleapis/release-please` `docs/customizing.md` (via WebSearch this session — generic `extra-files`
  + `x-release-please-version` marker semantics).

### Tertiary (LOW confidence)
- None — no unverified WebSearch-only claims are load-bearing in this document; the `extra-files`
  finding above was corroborated against pc2img's own `ci.yml` version-derivation mechanism before
  being used as a recommendation.

## Metadata

**Confidence breakdown:**
- Kit mechanics / token table / procedure steps: HIGH — read in full from the governing spec and kit
  files this session, cross-checked against CONTEXT.md's D-08 answers.
- Lint/docs/coverage measurements: HIGH — executed directly this session with captured output.
- Owner-account state (Apps added to pc2img, secrets, environments): MEDIUM — read-only `gh api`
  confirms org-level App existence but not per-repo installation state; flagged as Open Question 1.
- Migration-record entry inventory: HIGH for the 17 Phase-5 entries (read verbatim from
  `05-BC-NOTES.md`); MEDIUM for the Phase 1-4 additions (derived from a diff stat + STATE.md decision
  log, not individually re-verified against each phase's VERIFICATION.md in full detail this session).
- Secret-naming recommendation: LOW/ASSUMED — free-text choice, flagged as Assumption A1.

**Research date:** 2026-09-28
**Valid until:** short — this research is tightly coupled to today's measured repo state (git tags,
ruff hits, sphinx warning count, GitHub API reads). Re-measure any of the "measured this session"
claims if more than ~7 days elapse before planning consumes this file, since ruff/sphinx versions and
the repo's own tree can drift.
