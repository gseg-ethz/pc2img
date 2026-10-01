---
phase: "06"
slug: "publication-hardening-downstream-migration-record"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-10-01"
---

# Phase 06 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| develop-gsd tree -> public main | every file outside the strip list is published by a promotion | source, docs, planning prose (must not cross) |
| pyproject.toml / uv.lock -> PyPI resolvers | dependency names resolve from the public index | third-party packages (hash-pinned) |
| fork PR -> CI jobs (incl. pre-commit hooks) | contributor-controlled code runs under the read-only token | untrusted code |
| third-party actions / hook repos -> runners | code fetched by sha / release tag | third-party code |
| GitHub Apps -> repo (rulesets, releases) | per-run App tokens; protection and release are separate Apps | write-scoped tokens |
| owner -> repo secrets | App private keys and tokens enter the secret store | credentials (secret) |
| publish jobs -> PyPI / TestPyPI (OIDC) | identity = repo + workflow filename + environment | release artifacts, attestations |
| git archive -> setuptools_scm | archive describe string becomes the package version | version metadata |
| RTD build container -> repo | RTD runs the install commands from .readthedocs.yaml | public build logs |
| main -> develop-gsd (graft / back-merge) | public-branch history enters the integration branch | git history |
| migration record -> downstream consumers | iof3D and others rework against its claims | breaking-change claims |
| shipped docs -> maintainers / collaborators | RULESETS.md / RELEASE.md / CITATION.cff read as truth | procedure and metadata |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-06-01 | Information Disclosure | shipped comments/docstrings/CONTRIBUTING | medium | mitigate | `tests/test_hygiene.py` vocabulary gate over every tracked path outside `.planning`/`.claude` | closed |
| T-06-02 | Tampering | docs/ip/rrim-eth-signoff.md | high | mitigate | `git diff --quiet docs/ip/rrim-eth-signoff.md` clean; untouched since 06-01 | closed |
| T-06-SC@06-01 | Tampering | uv lock (sphinx_rtd_theme, pre-commit, pyyaml) | high | mitigate | hash-pinned uv.lock; `uv lock --check` clean | closed |
| T-06-03 | Repudiation | relocated audit document | low | accept | AR-01 | closed |
| T-06-04 | Tampering | signoff doc via auto-fixing hooks | high | mitigate | `.pre-commit-config.yaml:14` exclude with stated reason | closed |
| T-06-05 | Elevation of Privilege | Lint job executing hooks from a fork PR | medium | transfer | `ci.yml:97-99` lint job `contents: read` + `pull-requests: read` only | closed |
| T-06-SC@06-02 | Tampering | pre-commit hook repos | medium | mitigate | hooks pinned to upstream release tags — but ruff hook `v0.15.12` ≠ locked ruff `0.15.21`; deferred finding IN-07 → Phase 7 | open — below high threshold (non-blocking) |
| T-06-06 | Repudiation | noqa markers hiding complexity | low | accept | AR-02 | closed |
| T-06-07 | Information Disclosure | README/CITATION text | low | mitigate | hygiene gate covers README.rst | closed |
| T-06-08 | Spoofing | install instructions / index | medium | mitigate | README names `pc2img` on PyPI; nvidia index only for cuda extras, matching pyproject | closed |
| T-06-SC@06-03 | Tampering | `uvx twine` ephemeral tool | low | accept | AR-03 | closed |
| T-06-09 | Tampering | inline verifier (code in markdown) | low | accept | AR-04 | closed |
| T-06-10 | Repudiation | unverifiable claims in the migration record | medium | mitigate | verifier runs (`[ok] verified 25 entries`) but checks less than claimed — Tier-1 checks zero symbols, BC-P2I-010 probe cannot fail, 007/013/014 unchecked; deferred finding WR-02 (round 1) → Phase 7 | open — below high threshold (non-blocking) |
| T-06-11 | Information Disclosure | planning ids leaking through origins | low | mitigate | record lives in `.planning/` (absent from main, confirmed live) | closed |
| T-06-12 | Denial of Service | Docs required context red under -W | high | mitigate | `ci.yml` `sphinx-build -W --keep-going`; RTD `fail_on_warning: true` | closed |
| T-06-13 | Tampering | version shown in docs from a tagless checkout | medium | mitigate | CI side closed; RTD side: unforced `--tags` fetch, `\|\| true` on unshallow, no `0.0.` assertion — deferred findings WR-02/03/04 (round 4) → Phase 7, **precondition of the 0.11.0 promotion** | open — below high threshold (non-blocking) |
| T-06-SC@06-05 | Tampering | sphinx / sphinx_rtd_theme from PyPI | medium | mitigate | hash-pinned uv.lock in CI; RTD installs same dependency group | closed |
| T-06-14 | Tampering | third-party actions | high | mitigate | every `uses:` pinned to a 40-hex sha (0 offenders) | closed |
| T-06-15 | Elevation of Privilege | job permissions | high | mitigate | read-only / narrowly scoped `permissions:` in all workflows | closed |
| T-06-16 | Elevation of Privilege | pull_request_target / job-level if | critical | mitigate | no `pull_request_target`; conditionality only at step level via classify-changes | closed |
| T-06-17 | Elevation of Privilege | publish identity / containment gate | high | mitigate → accept | `check_publish_gate.py` matches only `pypa/gh-action-pypi-publish` and `twine upload`; misses `uv publish` and composite-action wrapping (reproduced 2026-10-01); AR-07 | closed (accepted risk) |
| T-06-18 | Information Disclosure | App private keys / Codecov token | high | mitigate | referenced only as `${{ secrets.* }}`; never echoed; distinct secret pairs | closed |
| T-06-SC@06-06 | Tampering | uv build / actions supply chain | high | mitigate | uv from setup-uv sha; hash-pinned uv.lock; no pip on runners | closed |
| T-06-19 | Repudiation | apply-time checklist | high | mitigate | CICD-ADOPTION-RECORD.md: 12 items each with command + real output, no checkmarks | closed |
| T-06-20 | Information Disclosure | records shipped to main | low | mitigate | hygiene gate covers RULESETS.md / RELEASE.md / CONTRIBUTING.md | closed |
| T-06-21 | Spoofing | claim tuples drifting from the workflows | medium | mitigate | RELEASE.md environment names match `publish-pypi.yml` / `publish-testpypi.yml` | closed |
| T-06-22 | Information Disclosure | App key / Codecov token entry | high | mitigate | entered via `gh secret set`; never in a tracked file or log | closed |
| T-06-23 | Tampering | tag namespace | medium | mitigate | `git ls-remote --tags` → only `archive/v2.0.0a5`; old name gone | closed |
| T-06-24 | Elevation of Privilege | ruleset App credentials | high | mitigate | `RULESET_APP_*` used only in ruleset-apply.yml, distinct from `RELEASE_APP_*` | closed |
| T-06-25 | Repudiation | merge without green checks | medium | mitigate | owner-run merges after green checks; two-parent merge confirmed (06-11-SUMMARY) | closed |
| T-06-26 | Information Disclosure | planning artifacts reaching public main | high | mitigate | live `git ls-tree origin/main` → 0 `.planning/` / `.claude/` paths | closed |
| T-06-27 | Information Disclosure | release App private key | high | mitigate | secret store only; separate from ruleset App | closed |
| T-06-28 | Spoofing | release PR opened with the default token | high | mitigate | PR #15 author `app/gseg-release-please`, 3 checks SUCCESS | closed |
| T-06-29 | Repudiation | unattended one-way push | high | mitigate | owner-executed pushes with recorded command + output (06-09 / 06-18 summaries) | closed |
| T-06-45 | Repudiation | unattended one-way push (promotion) | high | mitigate | blocking-human gate before the push; owner-executed | closed |
| T-06-30 | Elevation of Privilege | bypass_actors | critical | mitigate | live rulesets 24237564 / 24244420 → `bypass_actors: []`, `enforcement: active` | closed |
| T-06-31 | Denial of Service | requiring a context nothing produces | high | mitigate → accept | `preflight_ruleset_apply.py` checks job-name existence, not `pull_request` trigger; a schedule-only context (`Branch ancestry assertion`) is accepted (reproduced 2026-10-01); live payload unaffected; AR-08 | closed (accepted risk) |
| T-06-32 | Tampering | hand-created ruleset drifting from committed | medium | mitigate | `check_ruleset_drift.py` + tests; live comparator 0 differences | closed |
| T-06-33 | Spoofing | release PR by default token | high | mitigate | same evidence as T-06-28 | closed |
| T-06-34 | Repudiation | silent release | medium | mitigate | release PR #15 open, unmerged | closed |
| T-06-46 | Elevation of Privilege | bypass_actors (re-apply) | critical | mitigate | same live read-back as T-06-30 | closed |
| T-06-47 | Tampering | ruleset drift (re-apply) | medium | mitigate | same as T-06-32; idempotent re-apply proven | closed |
| T-06-35 | Tampering | graft altering shipped content | medium | mitigate | merge-tree precondition exit 0; `git diff --stat` empty (06-11-SUMMARY) | closed |
| T-06-36 | Denial of Service | collapsed second parent | high | mitigate | graft / phase merge / back-merges on develop-gsd all two-parent | closed |
| T-06-37 | Repudiation | nightly never observed | medium | mitigate | `scheduled-health.yml` latest run success; it caught real ancestry drift (issue #21) | closed |
| T-06-38 | Spoofing | trusted-publisher tuple too wide | high | mitigate | tuple binds repo + workflow filename + environment; PEP 740 cert SAN checked in VERIFICATION | closed |
| T-06-39 | Elevation of Privilege | testpypi environment without protection | low | accept | AR-05 | closed |
| T-06-40 | Information Disclosure | RTD build logs | low | accept | AR-06 | closed |
| T-06-41 | Spoofing | publish identity | high | mitigate | no API-token secrets referenced; trusted publishing only | closed |
| T-06-42 | Tampering | artifact integrity | high | mitigate | `attestations: write` + pypa publish action; integrity endpoint checked | closed |
| T-06-43 | Repudiation | phase closed on stale summaries | medium | mitigate | 06-13 Task 2 re-read every remote truth live | closed |
| T-06-44 | Denial of Service | accidental production upload | high | mitigate | `publish-pypi.yml` fires only on `release: published`; pypi.org 404 | closed |
| T-06-48 | Denial of Service | release source archives (describe glob) | high | mitigate | `.git_archival.txt` glob == `git_describe_command` glob; `tests/test_git_archival.py` green | closed |
| T-06-49 | Information Disclosure | sdist from a non-main ref | high | mitigate | ref guards in both publish workflows; `test_publish_ref_guard.py` green | closed |
| T-06-50 | Spoofing | citation DOI that does not resolve | medium | mitigate | no `doi` key in CITATION.cff | closed |
| T-06-SC@06-14 | Tampering | package/action supply chain | high | mitigate | `uv lock --check` clean; 0 unpinned `uses:` | closed |
| T-06-53 | Information Disclosure | internal content in RULESETS / RELEASE / README | medium | mitigate | hygiene gate; condensed docs clean | closed |
| T-06-54 | Repudiation | adoption-record evidence lost | medium | mitigate | CICD-ADOPTION-RECORD.md retains all sections and gate logs | closed |
| T-06-55 | Denial of Service | migration verifier unrunnable after move | medium | mitigate | extracted and run from `.planning/MIGRATION-v0.11.md` (`[ok] verified 25 entries`) | closed |
| T-06-56 | Tampering | back-merge procedure gap | medium | mitigate | RELEASE.md requires a merge-commit back-merge after every promotion and release-PR merge (procedure now lives in RELEASE.md, not RULESETS.md as the plan cites) | closed |
| T-06-SC@06-15 | Tampering | package/action supply chain | high | mitigate | `uv lock --check` clean | closed |
| T-06-51 | Tampering | projection.py runtime under a docstring-only change | high | mitigate | AST identity asserted; `tests/test_projection.py` green | closed |
| T-06-52 | Information Disclosure | planning references via unscanned files | medium | mitigate | hygiene exemptions reduced to the signed IP doc only | closed |
| T-06-57 | Tampering | ci.yml / action.yml semantics under comment edits | medium | mitigate | `yaml.safe_load` identity re-run against e929894 | closed |
| T-06-SC@06-16 | Tampering | package/action supply chain | high | mitigate | `uv lock --check` clean; pinned-sha grep unchanged | closed |
| T-06-58 | Repudiation | fixes merged without independent review | high | mitigate | `/gsd-code-review 06` over the recorded scope (06-17-SUMMARY) | closed |
| T-06-59 | Tampering | gate recorded from a stale run | medium | mitigate | full gate re-run in one pass, recorded in CICD-ADOPTION-RECORD.md | closed |
| T-06-SC@06-17 | Tampering | package/action supply chain | high | mitigate | `uv lock --check` clean | closed |
| T-06-60 | Repudiation | gap flipped without evidence | medium | mitigate | every 06-UAT.md gap entry carries sha + proving test | closed |
| T-06-61 | Tampering | merge without green checks / collapsing merge | high | mitigate | green checks before merge; two-parent merges confirmed | closed |
| T-06-62 | Denial of Service | promotion from a develop-gsd lacking fixes | high | mitigate | post-merge assertions on origin/develop-gsd re-confirmed live | closed |
| T-06-SC@06-18 | Tampering | package/action supply chain | high | mitigate | `uv lock --check` clean | closed |
| T-06-63 | Tampering | six workflow/action YAML files under comment edits | high | mitigate | `yaml.safe_load` identity re-run against e929894 | closed |
| T-06-64 | Information Disclosure | planning vocab / review ids via the fix | medium | mitigate | review-identifier regex over the shipped tree → empty | closed |
| T-06-65 | Repudiation | shipped docs misstating protection | medium | mitigate | RULESETS.md table matches live payloads and ci.yml job names | closed |
| T-06-66 | Repudiation | doc pass re-merged without review | high | mitigate | round-3 `/gsd-code-review` over the 13-path scope (06-19-SUMMARY) | closed |
| T-06-SC@06-19 | Tampering | package/action supply chain | high | mitigate | `uv lock --check` clean; YAML identity confirms no action change | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-06-03 | `git mv` preserves history; `.planning/` is the intended home of the audit document | owner (plan 06-01) | 2026-09-28 |
| AR-02 | T-06-06 | each noqa marker carries a same-line reason; the rule stays active for new code | owner (plan 06-02) | 2026-09-28 |
| AR-03 | T-06-SC@06-03 | canonical PyPA tool run ephemerally for a read-only metadata check; not added to the project | owner (plan 06-03) | 2026-09-28 |
| AR-04 | T-06-09 | repo-local verifier, runs only when a maintainer extracts it; root guard; no network; temp dirs only | owner (plan 06-04) | 2026-09-28 |
| AR-05 | T-06-39 | dry-run path with no production impact; the production `pypi` environment gets a required reviewer | owner (plan 06-12) | 2026-09-28 |
| AR-06 | T-06-40 | public project; RTD logs contain only public install output | owner (plan 06-12) | 2026-09-28 |
| AR-07 | T-06-17 | Containment gate misses `uv publish` and publish steps wrapped in a composite action. No current workflow uses either form; every workflow change goes through a reviewed PR. Matches deferred review finding WR-06 (round 1) — non-breaking hardening, fixed in Phase 7. | owner | 2026-10-01 |
| AR-08 | T-06-31 | Preflight accepts a required context produced only by a non-`pull_request` workflow, which would make the branch unmergeable under empty `bypass_actors`. The live payloads require only Lint / Tests / Docs, all `pull_request`-triggered; risk applies only to a future payload edit. Matches deferred review finding WR-07 (round 1) — fixed in Phase 7. | owner | 2026-10-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Follow-ups (Phase 7)

- **T-06-17 / T-06-31** — fix per deferred findings WR-06 / WR-07, then re-verify and retire AR-07 / AR-08.
- **T-06-13** — RTD version handling (round-4 WR-02 / WR-03 / WR-04); **must land before the 0.11.0 promotion.**
- **T-06-10** — migration-record verifier coverage (round-1 WR-02).
- **T-06-SC@06-02** — align the ruff pre-commit hook rev with the locked ruff version (round-1 IN-07).
- **Unregistered: `NIME_RELEASE_PLEASE_TOKEN`** — repo secret referenced by no workflow or action (leftover PAT from before the release App). Owner to delete the secret and revoke the underlying token (2026-10-01).
- **T-06-56** — plan cites RULESETS.md for the back-merge procedure; it now lives in RELEASE.md (informational).

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-01 | 77 | 74 (incl. 8 accepted, 1 transferred) | 3 (all below high; 0 blocking) | gsd-security-auditor (sonnet); T-06-17 / T-06-31 reproduced by orchestrator |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-01
