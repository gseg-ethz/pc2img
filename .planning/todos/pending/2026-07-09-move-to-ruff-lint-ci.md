---
created: 2026-07-09T00:00:00.000Z
title: Move lint/format from black to ruff and run it in CI
area: tooling
resolves_phase: 3
files:
  - pyproject.toml
  - .github/workflows/
source: .planning/phases/02-dependency-adaptation-reproducible-environment/02-CONTEXT.md (Deferred; owner-raised during Phase 2 discussion)
---

## Problem

pc2img currently declares `black ~= 23.10` as its formatter (in the dev tooling)
and has **no lint step in CI**. The sibling library **pchandler already uses
`ruff ~= 0.15`** (lint + format) in its dev tooling and runs it in CI, per its
publication template. pc2img should converge on the same toolchain both for
code-hygiene reasons and for cross-library consistency (the stated publication
standard is "match pchandler").

Raised by the project owner during the Phase 2 (dependency adaptation)
discussion; explicitly flagged as **out of scope for Phase 2** (which is
dependency/reproducibility only) and to be handled in the appropriate later
phase.

## Solution

Two coupled pieces spanning two phases:

- **Phase 4 (QUAL-01, code hygiene):** replace `black` with `ruff` as the
  formatter + add ruff lint config. This is a tooling swap alongside the other
  hygiene cleanup (dead code, duplicate `joblib` pin, placeholder metadata,
  matplotlib extra). With the Phase 2 decision to move dev deps to PEP 735
  `[dependency-groups]`, ruff lands in the `dev` group.
- **Phase 3 (CICD-01, CI foundation):** wire `ruff check` (and optionally
  `ruff format --check`) into the PR CI workflow as part of the early safety net.

**Sequencing note:** because the lightweight test-CI is stood up in Phase 3,
consider doing the `black -> ruff` swap **before/at Phase 3** so CI doesn't add a
`black` check only for Phase 4 to replace it with `ruff`. `resolves_phase` is set
to 3 for this reason; revisit during Phase 3 planning whether to pull the swap
itself forward or keep it in Phase 4 and only wire CI here.

Match pchandler's ruff version/config (`ruff ~= 0.15`) where reasonable for
cross-library consistency.
