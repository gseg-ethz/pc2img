---
phase: 06-publication-hardening-downstream-migration-record
verified: 2026-09-30T15:53:26Z
status: passed
score: 4/4 roadmap success criteria verified; 19/19 plan must-haves supported by live evidence
covered_files: [".git_archival.txt", ".gitattributes", ".github/actions/classify-changes/action.yml", ".github/actions/setup-python-deps/action.yml", ".github/rulesets/develop.json", ".github/rulesets/main.json", ".github/scripts/check_publish_gate.py", ".github/scripts/check_ruleset_drift.py", ".github/scripts/preflight_ruleset_apply.py", ".github/scripts/ruleset_lib.py", ".github/scripts/test_check_publish_gate.py", ".github/scripts/test_check_ruleset_drift.py", ".github/scripts/test_classify_changes.py", ".github/scripts/test_preflight_ruleset_apply.py", ".github/scripts/test_publish_ref_guard.py", ".github/scripts/test_ruleset_lib.py", ".github/workflows/ci.yml", ".github/workflows/publish-pypi.yml", ".github/workflows/publish-testpypi.yml", ".github/workflows/release-please.yml", ".github/workflows/ruleset-apply.yml", ".github/workflows/scheduled-health.yml", ".gitignore", ".planning/CICD-ADOPTION-RECORD.md", ".planning/MIGRATION-v0.11.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-01-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-01-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-02-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-02-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-03-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-03-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-04-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-04-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-05-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-05-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-06-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-06-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-07-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-07-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-08-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-08-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-09-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-09-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-10-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-10-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-11-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-11-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-12-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-12-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-13-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-13-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-14-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-14-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-15-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-15-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-16-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-16-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-17-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-17-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-18-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-18-SUMMARY.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-19-PLAN.md", ".planning/phases/06-publication-hardening-downstream-migration-record/06-19-SUMMARY.md", ".pre-commit-config.yaml", ".readthedocs.yaml", "CITATION.cff", "CONTRIBUTING.md", "README.rst", "RELEASE.md", "RULESETS.md", "docs/source/api.rst", "docs/source/conf.py", "docs/source/index.rst", "pyproject.toml", "release-please-config.json", "scripts/smoke_pipeline.py", "setup.py", "src/pc2img/features/derivative_features.py", "src/pc2img/image_cache/disk_backed_image_store.py", "src/pc2img/strategies/projection.py", "src/pc2img/util.py", "tests/test_disk_backed_image_data.py", "tests/test_git_archival.py", "tests/test_hygiene.py", "tests/test_image_store.py", "tests/test_point_cloud_image_generator.py", "tests/test_projection.py", "tests/test_rrim_features.py", "tests/test_tiled_generator.py", "tests/test_util.py", "uv.lock"]
covered_digest: "v2:sha256:98fe70ac9010055f0498fce0b2a7877067bad2398b1df34894b0dc3cdc4815ae"
re_verification:
  previous_status: gaps_found
  previous_score: "scaffold only — no goal-backward verification had run; round-4 gaps_open: 8"
  gaps_closed:
    - "All round-1 through round-4 review findings (58 total) are dispositioned in 06-UAT.md: 30 resolved with cited fix commits/tests, 28 explicitly deferred to Phase 7 with owner disposition. None remain open."
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 6: Publication Hardening & Downstream Migration Record Verification Report

**Phase Goal:** pc2img adopts the GSEG git-strategy template (branch protection + publication
CI/CD), is publishable with real metadata, is promoted to `main` for the first time behind active
rulesets, and carries a draft structured breaking-change record for downstream consumers.

**Verified:** 2026-09-30T15:53:26Z
**Status:** passed
**Re-verification:** Yes — the existing `06-VERIFICATION.md` was a pre-verification scaffold that
held only consolidated review-round findings (see "Round-N findings" below, preserved verbatim).
This is the first goal-backward verification run for the phase.

This verification does not trust SUMMARY.md or the round-N narrative text. Every truth below was
checked against live state: `git`/`gh` against the real GitHub repository (rulesets, branches, PRs,
workflow runs), `curl` against TestPyPI, PyPI and Read the Docs, and local command execution
(pytest, the migration record's own inline verifier, `uv build` + `twine check`, `cffconvert`).

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth (ROADMAP.md Success Criteria) | Status | Evidence |
|---|---|---|---|
| 1 | GSEG git-strategy template (core + `release-pypi`) assembled per Procedure B; rulesets active on `main` and `develop-gsd` with `bypass_actors: []`; apply-time checklist recorded with evidence; every template deviation recorded in-repo | ✓ VERIFIED | `gh api repos/gseg-ethz/pc2img/rulesets` returns two rulesets, `protect-main` (id 24237564) and `protect-develop-gsd` (id 24244420), both `enforcement: active`, both `bypass_actors: []` (fetched live, not read from a file). `main`'s ruleset carries `pull_request` (0 approvals), `required_status_checks` = [`Lint (pre-commit)`, `Tests (pytest)`, `Docs (sphinx -W)`] with `strict_required_status_checks_policy: true`, `non_fast_forward`, `deletion`, `required_linear_history`. `develop-gsd`'s carries the same `pull_request`/`non_fast_forward`/`deletion` rules plus `required_status_checks` = [`Lint (pre-commit)`, `Tests (pytest)`] with `strict: false`, and no linear-history rule — matching D-08 Q5/Q7 exactly. `.planning/CICD-ADOPTION-RECORD.md`'s 12-item apply-time checklist was spot-checked, not trusted: item 1's `grep -n 'name:' .github/workflows/ci.yml` reproduces byte-for-byte (`Lint (pre-commit)` / `Tests (pytest)` / `Docs (sphinx -W)` at the stated lines); item 4's `grep -rn pull_request_target .github/workflows/` reproduces empty; item 9's SHA-pin check (`grep -rhoE 'uses: [^ ]+@[^ ]+' .github/ | grep -v 'uses: \./' | grep -vcE '@[0-9a-f]{40}$'`) reproduces `0`. The "Deviations from the template" section (11 named deviations: uv-based setup composite, doc-group install, pre-commit tool source, full-depth checkouts, the coverage floor, the pinned type-check interpreter, `uv build`, dry-run attestations, kit test reformatting, the untouched release manifest, initial-ruleset-creation-by-POST) is present and each deviation names its file. |
| 2 | Package builds with real, non-placeholder metadata (README, `CITATION.cff`, project URLs, RTD site); TestPyPI dry run publishes via OIDC trusted publishing with PEP 740 attestations | ✓ VERIFIED | `uv build` + `uvx twine check` on the current tree: both wheel and sdist **PASSED**. `README.rst` (114 lines) has install/quickstart/feature-overview/RRIM/CUDA content, not the prior `##Hello` placeholder. `CITATION.cff` validates under CFF 1.2.0 (`cffconvert --validate` → "Citation metadata are valid"), single author, no placeholder DOI. `pyproject.toml [project.urls]` carries `Homepage`, `Documentation` (→ RTD), `Repository`, `Issues`, `Changelog`. `curl https://pc2img.readthedocs.io/en/latest/` → HTTP 200; RTD API confirms the 5 most recent builds (including `latest`) all `Finished`/`success: true`. TestPyPI: `curl https://test.pypi.org/pypi/pc2img/json` shows release `0.10.4.post7` present (the dry-run upload; `pypi.org` for the same package still returns 404, confirming no production publish happened). Downloaded the **actual uploaded sdist** from `test-files.pythonhosted.org` and inspected its member list directly — it contains no `.planning` or `.claude` path (the guard worked because the dry run was dispatched from `main`, which itself carries neither directory). Fetched the PEP 740 integrity/provenance endpoint for the uploaded wheel — a real Sigstore-signed attestation bundle is returned, `subject` naming the exact filename+sha256, certificate SAN naming `.github/workflows/publish-testpypi.yml@refs/heads/main`, issuer `token.actions.githubusercontent.com`. |
| 3 | `develop-gsd` promoted to `main` (planning paths stripped; no planning vocabulary); ancestry graft done; nightly ancestry assertion observed passing; release-please opened the 0.11.0 release PR (left unmerged) | ✓ VERIFIED | `git rev-parse origin/main` = `20ef688c...`. `git merge-base --is-ancestor 0819b2b origin/main` succeeds (the promotion commit `feat!: publish the 2.x architecture as the 0.11 release line` is on `main`), and the only two commits after it on `main` are PR #17 (`ci(rulesets): normalise...`) and PR #20 (`fix(docs): fetch tags on Read the Docs...`), both confirmed as `gh pr list --base main --state merged` rebase-merges (RELEASE.md step 1 says squash; for a single-commit PR onto linear-history `main` the result is identical — noted in 06-13-SUMMARY) with green `Lint (pre-commit)`/`Tests (pytest)`/`Docs (sphinx -W)` checks. `git ls-tree -r --name-only origin/main \| grep -cE '^\.planning/\|^\.claude/'` = `0`. The promotion commit's own message: subject `feat!:`, a self-contained `BREAKING CHANGE:` paragraph (no file pointer, matching D-33a since `.planning/MIGRATION-v0.11.md` is stripped from `main`), and a `Release-As: 0.11.0` footer. Ancestry graft: `git merge-base --is-ancestor origin/main origin/develop-gsd` succeeds; `git log --graph` on `develop-gsd` shows the graft merge (PR #18, `chore/ancestry-graft`) followed by two further true-merge back-merges (PR #19 landing the phase branch, PR #22 back-merging main's docs fix) — never squash/rebase. Nightly assertion: `gh run list --workflow scheduled-health.yml` shows the latest dispatch (id `36737255378`, 2026-09-30T15:30) `conclusion: success`; `scheduled-health.yml`'s `on:` block carries a `schedule:` cron trigger, so it is registered on the default branch as required. (The plan's own truth for this item — 06-11 — requires only "dispatched from main and observed passing once" plus the schedule trigger being registered; both hold. The very first *cron-fired* run is scheduled for 2026-10-01 06:00 UTC and had not yet occurred at verification time — noted below, not treated as a gap since it is outside what the phase's own must-have requires.) Release PR: `gh pr view 15` → title `chore(main): release 0.11.0`, `state: OPEN`, author `app/gseg-release-please`, `isDraft: false`, all three required checks green (via the release-artifact classify-changes fast path). |
| 4 | Draft `.planning/MIGRATION-v0.11.md` (migration-spec format, baseline `91b4ab6`; internal, stripped from `main`) documents Phase 1–6 changes; inline verifier passes | ✓ VERIFIED | `git show origin/develop-gsd:.planning/MIGRATION-v0.11.md` exists and its frontmatter reads `type: migration-spec`, `spec_version: "1.0"`, `repo: pc2img`, `baseline_ref: "91b4ab6"`, `target_ref` = the `develop-gsd` HEAD at draft time, `bc_id_prefix: BC-P2I`, `milestone: v1.0` — exactly D-25/D-26/D-28/D-33. 25 unique `BC-P2I-NNN` entries (001–025), monotonic. `git ls-tree --name-only origin/main \| grep -i migration` → empty (not shipped on `main`, per D-33). Extracted the record's own inline verifier with the extraction command its docstring states and ran it standalone: `uv run --frozen python <extracted>.py` → `[ok] verified 25 entries`, exit 0. |

**Score:** 4/4 roadmap Success Criteria verified with live evidence. 0 behavior-unverified, 0 overrides applied.

### Plan-Level Must-Haves (spot-check across all 19 plans)

All 19 plans' `must_haves.truths` were read and cross-referenced against live/local state. Representative
spot-checks beyond the four SC rows above:

| Must-have (plan) | Status | Evidence |
|---|---|---|
| Planning-vocabulary gate green on the whole shipped tree (06-01) | ✓ VERIFIED | `uv run --frozen python -m pytest tests/test_hygiene.py -q` → `88 passed`. |
| `docs/pchandler-2x-break-audit.md` moved; `scripts/01_tiled_image_generation_from_pointcloud.py` deleted (06-01, D-21/D-22) | ✓ VERIFIED | Neither path exists in the working tree; both are absent from the `e9eb3c4..HEAD` diff's surviving files; the audit content lives at `.planning/phases/02-.../pchandler-2x-break-audit.md`. |
| CR-01 (floating-tag archive break) closed with a regression test (06-14) | ✓ VERIFIED | `.git_archival.txt`'s `match=` glob and `pyproject.toml`'s `git_describe_command --match` glob are both the identical string `v[0-9]*.[0-9]*.[0-9]*`. `uv run --frozen python -m pytest tests/test_git_archival.py -q` → `3 passed`. |
| Publish workflows ref-guarded (06-14/06-19, WR-05) | ✓ VERIFIED | `uv run --frozen python -m pytest .github/scripts/test_publish_ref_guard.py -q` → `9 passed`. Guard code present and matches the recorded scope (protects only commits that carry it; RELEASE.md states the rule explicitly). |
| CITATION.cff carries no placeholder DOI (06-14, WR-08) | ✓ VERIFIED | File inspected directly: no `preferred-citation`/`doi:` block; message states no archive exists yet. `cffconvert --validate` passes. |
| `.planning/CICD-ADOPTION-RECORD.md` preserves the full adoption record after `RULESETS.md`/`RELEASE.md` were condensed (06-15/06-19, D-34) | ✓ VERIFIED | 949-line record read directly: interview answers, taken/declined components, 12-item checklist with reproduced evidence, deviations, superseded decision, deferred items and two full gate-re-run logs (`## Gate re-runs`) are present. |
| `RULESETS.md`/`RELEASE.md` read as plain repo docs, sized per D-34, tables match live rulesets (06-19) | ✓ VERIFIED | 36 and 60 lines respectively (within/near the round-2 target after the owner's further condensation); the rules table's every cell (`Lint`/`Tests`/`Docs`/up-to-date/linear-history/approvals, per branch) matches the live ruleset payloads fetched via `gh api` above. |
| Kit script tests, publish containment gate, hygiene gate all green after every gap round (06-16..06-19) | ✓ VERIFIED | `uv run --frozen python -m pytest .github/scripts/ -q` → `93 passed`. |
| 06-UAT.md gaps fully dispositioned, no round left open (06-18) | ✓ VERIFIED | `grep -c 'status: resolved'` = 30, `grep -c 'status: deferred'` = 28, sum = 58 with zero other status values in the file. |
| Actual TestPyPI upload contains none of `.planning`/`.claude` (06-13) | ✓ VERIFIED | Downloaded real artifact from `test-files.pythonhosted.org` (not rebuilt locally) and listed its members directly — confirmed clean. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `RULESETS.md`, `RELEASE.md` | Public repo docs, root, ship on `main` | ✓ VERIFIED | Present on `main` (confirmed via `git ls-tree origin/main`), no planning vocabulary, hygiene gate green. |
| `.planning/CICD-ADOPTION-RECORD.md` | Full internal adoption record | ✓ VERIFIED | 949 lines, present only on `develop-gsd` (internal), all sections present. |
| `.planning/MIGRATION-v0.11.md` | Draft migration-spec record | ✓ VERIFIED | Present on `develop-gsd`, absent from `main`; inline verifier runs and passes. |
| `README.rst`, `CITATION.cff` | Real metadata | ✓ VERIFIED | Both pass their respective validators (`twine check`, `cffconvert`). |
| `docs/source/{conf.py,index.rst,api.rst}`, `.readthedocs.yaml` | Minimal Sphinx site, RTD build | ✓ VERIFIED | RTD project live, `latest` build `Finished`/success, site returns HTTP 200. |
| `.github/rulesets/{main,develop}.json` + live rulesets | Committed payload matches live state | ✓ VERIFIED | Live `gh api` read matches the committed payload's rule shapes (spot-checked; see SC1 row). |
| `.github/workflows/{ci,publish-pypi,publish-testpypi,release-please,ruleset-apply,scheduled-health}.yml` | Assembled kit, active | ✓ VERIFIED | `gh api .../actions/workflows` lists all six as `state: active`. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Promotion commit tree | `origin/develop-gsd` tree | identical outside `.planning/`/`.claude/` | ✓ WIRED | `git diff --stat 91b4ab6..origin/develop-gsd -- . ':!.planning' ':!.claude'` shows real diffs (implementation + doc files), confirming the promotion carries the reviewed Phase 1–6 code; main itself carries zero planning paths. |
| PROMOTION_SHA on `main` | `release-please.yml` | push-to-main trigger → App token → release PR | ✓ WIRED | Release PR #15 exists, `app/gseg-release-please`-authored, `OPEN`. |
| `.github/rulesets/main.json`/`develop.json` | live rulesets `protect-main`/`protect-develop-gsd` | apply workflow PUT + drift read-back | ✓ WIRED | Live `gh api` reads match committed rule shapes; both `bypass_actors: []`. |
| `publish-testpypi.yml` (main) | `test.pypi.org/project/pc2img/` | OIDC trusted publisher | ✓ WIRED / FLOWING | Real uploaded artifact fetched and inspected; real PEP 740 attestation fetched and inspected — not a static claim. |
| `MIGRATION-v0.11.md` `## Verifier (inline)` | the four `__init__.py __all__` lists | AST walk | ✓ WIRED / FLOWING | Extracted and executed standalone; printed `[ok] verified 25 entries`, exit 0 (not merely "script exists"). |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| CICD-02 | 06-01, 06-02, 06-05, 06-06, 06-07, 06-08, 06-09..06-19 (all) | Branch protection + publication hardening matching the PCHandler template | ✓ SATISFIED | SC1–SC3 above; REQUIREMENTS.md traceability already reads "Complete" for CICD-02, and this run confirms the underlying live/remote state actually backs that claim (rulesets, workflows, promotion, dry run all independently reproduced). |
| BC-01 (draft) | 06-04, 06-13, 06-15, 06-17, 06-19 | Structured breaking-change/migration record — Phase 6 scope is the **draft** | ✓ SATISFIED | SC4 above. REQUIREMENTS.md correctly still shows BC-01 as "Pending" overall (finalisation is Phase 7's job — re-stamp to `v0.11.0`, append GSEGUtils 0.6 entries); Phase 6's draft obligation is fully met. |

No orphaned requirements: REQUIREMENTS.md's Traceability table maps only CICD-02 and BC-01 (draft) to Phase 6, and both are claimed by at least one plan's `requirements:` frontmatter field.

### Anti-Patterns Found

Scanned every file in the `e9eb3c4..origin/develop-gsd` diff (53 non-planning files) for debt markers,
placeholders, and empty-implementation patterns.

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD`/`FIXME`/`XXX` | — | **None found** — debt-marker gate is clean across the whole shipped tree (`git grep`). |
| `tests/test_hygiene.py`, `.github/workflows/ci.yml`, `.github/actions/classify-changes/action.yml` | multiple | `placeholder` string matches | ℹ️ Info | All are either a test asserting the **absence** of a placeholder value, or prose discussing a hypothetical placeholder version string — not stub code. Not a finding. |

No blocker or warning anti-patterns found in the phase's own diff. (The phase's own code-review process — rounds 1–4, `06-REVIEW.md`/`06-UAT.md` — already found and dispositioned 58 findings well beyond what a mechanical grep pass would catch; see below.)

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Planning-vocabulary hygiene gate | `pytest tests/test_hygiene.py -q` | 88 passed | ✓ PASS |
| Git-archival / CR-01 regression | `pytest tests/test_git_archival.py -q` | 3 passed | ✓ PASS |
| Publish ref guards | `pytest .github/scripts/test_publish_ref_guard.py -q` | 9 passed | ✓ PASS |
| Kit scripts (ruleset_lib, check_publish_gate, drift, preflight, classify-changes) | `pytest .github/scripts/ -q` | 93 passed | ✓ PASS |
| CITATION.cff schema validity | `uvx cffconvert --validate -i CITATION.cff` | "valid according to schema version 1.2.0" | ✓ PASS |
| Package builds and passes PyPI metadata checks | `uv build && uvx twine check dist/*` | both PASSED | ✓ PASS |
| Migration record inline verifier | extracted + `uv run --frozen python <script>.py` | `[ok] verified 25 entries` | ✓ PASS |
| Live rulesets match committed payload shape | `gh api repos/gseg-ethz/pc2img/rulesets/{id}` ×2 | both active, `bypass_actors: []`, rule sets match D-08 | ✓ PASS |
| `main` carries zero planning paths | `git ls-tree -r --name-only origin/main \| grep -cE '^\.planning/\|^\.claude/'` | `0` | ✓ PASS |
| Ancestry graft holds both directions | `git merge-base --is-ancestor` ×2 | both hold | ✓ PASS |
| Nightly ancestry workflow last run | `gh run list --workflow scheduled-health.yml` | latest `conclusion: success` | ✓ PASS |
| TestPyPI upload is clean of `.planning`/`.claude` | downloaded real sdist, `tar -tzf \| grep` | no match | ✓ PASS |
| TestPyPI PEP 740 attestation retrievable | `curl .../integrity/.../provenance` | real Sigstore bundle returned | ✓ PASS |
| RTD site live | `curl -o /dev/null -w '%{http_code}' https://pc2img.readthedocs.io/en/latest/` | `200` | ✓ PASS |
| Release PR #15 open, unmerged, App-authored, checks green | `gh pr view 15` | confirmed | ✓ PASS |

No spot-check failed or was skipped.

## Round-N review findings (preserved from the pre-verification scaffold)

The sections below are carried forward verbatim from the scaffold this file replaces. They are how
`/gsd-consolidate-findings` routed the four code-review rounds' findings into the phase's
verification surface; the findings themselves live in `06-UAT.md`'s `## Gaps` (all 58 entries now
`resolved` or `deferred`, none open — reconfirmed by this run, see "Plan-Level Must-Haves" above).

---

## Round-1 findings (consolidated 2026-09-29T06:58:35Z)

24 finding(s) imported from `gsd-code-review-deep` over `e9eb3c4..2ec34fc`.

The prior verdict above is preserved, not deleted: it was correct for what it examined. What it did not examine is this range.

Full detail, root causes and required fixes are in the phase UAT file, section `## Gaps`.


---

## Round-2 findings (consolidated 2026-09-29T12:08:42Z)

11 finding(s) imported from `gsd-code-review-deep` over `2ec34fc..5eae12c`.

The prior verdict above is preserved, not deleted: it was correct for what it examined. What it did not examine is this range.

Full detail, root causes and required fixes are in the phase UAT file, section `## Gaps`.


---

## Round-3 findings (consolidated 2026-09-29T16:42:42Z)

15 finding(s) imported from `gsd-code-review-deep` over `29039d5..f5d9037`.

The prior verdict above is preserved, not deleted: it was correct for what it examined. What it did not examine is this range.

Full detail, root causes and required fixes are in the phase UAT file, section `## Gaps`.


---

## Round-4 findings (consolidated 2026-09-30T15:42:34Z)

8 finding(s) imported from `gsd-code-review-deep` over `4da8c6c..2a094ed`.

The prior verdict above is preserved, not deleted: it was correct for what it examined. What it did not examine is this range.

Full detail, root causes and required fixes are in the phase UAT file, section `## Gaps`.

## Human Verification Required

None required to reach `passed`. One forward-looking item is noted for awareness, not as a gate:

**Informational — first cron-fired `scheduled-health` run.** The nightly ancestry assertion has
only been observed passing via `workflow_dispatch` so far (latest: run `36737255378`,
2026-09-30T15:30 UTC, `success`); the workflow's `schedule:` trigger is registered on `main` but its
first actual cron-fired run is expected 2026-10-01 06:00 UTC, after this verification. The phase's
own must-have (06-11) only requires "dispatched from `main` and observed passing once" plus the
trigger being registered — both hold today — so this does not block `passed`. If the owner wants
extra assurance, check `gh run list --repo gseg-ethz/pc2img --workflow scheduled-health.yml --json
event,conclusion,createdAt` after 2026-10-01 06:00 UTC and confirm an `event: schedule` entry with
`conclusion: success`.

## Gaps Summary

No gaps. All four ROADMAP.md Success Criteria for Phase 6 are independently verified against live
GitHub/PyPI/RTD state, not merely against SUMMARY.md narrative or local file presence. All 58
code-review findings across four rounds are dispositioned in `06-UAT.md` (30 resolved with cited
fix commits and reproducible proving tests/commands, 28 explicitly deferred to Phase 7 with an
owner disposition) — none left open. The phase's own review-discipline requirement (gap-closure
fixes get their own review) was itself followed: 06-17 and the round-3/round-4 reviews each
reviewed the diff of the gap-closure plan that preceded them before further gaps were closed or
waived.

Two items worth the next reader's attention (neither is a Phase 6 gap):
- Round-4 findings WR-02/WR-03/WR-04 (`.readthedocs.yaml` `git fetch --tags`/`--unshallow`
  robustness) are explicitly deferred to Phase 7 **as a precondition of the 0.11.0 promotion**,
  not of Phase 6's already-completed first promotion. Phase 7 must not skip them.
- `RULESETS.md`'s "For maintainers" section notes that inspecting `bypass_actors` requires an
  admin-scoped token — the list endpoint never returns it at all, and this verifier's read used the
  per-ruleset endpoint with an admin-capable `gh` session, consistent with that documented caveat.

---

*Verified: 2026-09-30T15:53:26Z*
*Verifier: Claude (gsd-verifier)*
