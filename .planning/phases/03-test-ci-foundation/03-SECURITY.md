---
phase: 03
slug: test-ci-foundation
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-10
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register origin: authored at plan time (all three PLAN.md files carried a `<threat_model>` block). Verification depth: ASVS L1 (grep-level mitigation confirmation against the implementation). Block threshold: `high` — the highest severity in this register is `medium`, so no threat is at or above the blocking threshold.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI → local lock | New dev tooling (pytest, pytest-cov, coverage) enters the hash-pinned `uv.lock` | dev dependency wheels + hashes |
| untrusted PR → CI runner | A `pull_request` (incl. from a fork) runs workflow code on GitHub-hosted infra | PR source tree, `GITHUB_TOKEN` |
| pinned action → CI runner | Third-party GitHub Actions execute inside the job | action code (checkout, setup-uv, upload-artifact) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-03-SC-dep | Tampering | `uv` dev-group installs (pytest, pytest-cov, coverage) | medium | mitigate | `~=` bounds + hash-pinned `uv.lock`; `uv lock --check` in sync (183 pkgs, no drift); canonical PyPI tooling mirroring pchandler pins | closed |
| T-03-10 | Tampering | xfail markers hiding a regression | low | mitigate | `strict=False` xfail markers (6 present in tests/) with Phase-5 reasons — a fixed test surfaces as XPASS, never silently; passing tests left unmarked so new regressions fail the suite | closed |
| T-03-02 | Information Disclosure | CI job on `pull_request` from forks | medium | mitigate | Job references **no** secrets (`grep secrets\. ci.yml` → 0); default `GITHUB_TOKEN` read-only on fork PRs; `coverage.xml` is a plain artifact, not a token-gated upload | closed |
| T-03-03 | Tampering | third-party GitHub Actions (checkout, setup-uv, upload-artifact) | low | accept | Pinned to immutable version tags (`actions/checkout@v5`, `astral-sh/setup-uv@v8.3.2`, `actions/upload-artifact@v4`); full SHA-pinning deferred to Phase 6 publication hardening | closed (accepted) |
| T-03-04 | Elevation of Privilege | default `GITHUB_TOKEN` scope on fork PRs | low | mitigate | Explicit top-level `permissions: contents: read` (ci.yml:13-14) narrows the workflow token to read-only — a compromised action or fork PR cannot write to the repo | closed |
| T-03-SC-ci | Tampering | `uv sync --frozen` install in CI | medium | mitigate | CI installs strictly from the committed hash-pinned `uv.lock` (`uv sync --frozen` ci.yml:36; `uv run --frozen pytest` ci.yml:43) — lock drift/substitution fails the job rather than resolving fresh | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `high` count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-03 | Third-party Actions are pinned to immutable version tags, not full commit SHAs. Full SHA-pinning (pchandler-style) is an explicit Phase 6 publication-hardening concern (D-09 reconciliation); acceptable to defer for this lightweight test-CI phase. | Nicholas Meyer (owner) | 2026-07-10 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-10 | 6 | 6 | 0 | Claude (gsd-secure-phase, ASVS L1 grep verification) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-10
