# Phase 4: Code Quality & Algorithmic Soundness Review - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-10
**Phase:** 4-Code Quality & Algorithmic Soundness Review
**Areas discussed:** Fix-vs-log boundary, Math review rigor, Findings handoff format, Design-review depth, Folded todos, Review orchestration, PerspectiveProjection depth, ruff adoption

---

## Gray-area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Fix-vs-log boundary | How aggressive with code changes | ✓ |
| Math review rigor | Method for QUAL-03 soundness | ✓ |
| Findings handoff format | How findings feed Phase 5 | ✓ |
| Design-review depth | How wide the QUAL-02 net | ✓ |

**User's choice:** All four selected for discussion.

---

## Todo folding

| Option | Description | Selected |
|--------|-------------|----------|
| guard _TransformArray import | design hygiene, resolves_phase:4 | ✓ |
| coerce null lazy_disk_cache_config | correctness bug | ✓ |
| move to ruff lint CI | tooling migration | ✓ |
| document cuda11 vs cuda12 | docs | ✓ |

**User's choice:** Fold all four.
**Notes:** Per-todo dispositions worked out in later questions (guard→fix,
coerce-null→log for P5, ruff→adopt+defer-CI, cuda docs→minor deliverable).

---

## Fix-vs-log boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Hygiene + safe design fixes | Fix QUAL-01 + low-risk mechanical design fixes; log correctness/math | ✓ |
| Hygiene only; log everything else | Only QUAL-01 fixed; all design+math logged | |
| Fix all low-risk, log ambiguous | Aggressively fix anything safe incl. simple correctness | |

**User's choice:** Hygiene + safe design fixes.
**Notes:** Preserves the "each bug fix has a proving test in Phase 5" guarantee.

---

## Math review rigor

| Option | Description | Selected |
|--------|-------------|----------|
| Expert read + numeric probes | Manual read grounded in formulas + numeric sanity scripts | |
| Multi-agent adversarial review | Fan-out reviewers per math area, adversarial verify (opt-in orchestration) | ✓ |
| Literature-grounded manual read | Single-pass read against cited references, no execution | |

**User's choice:** Multi-agent adversarial review.
**Notes:** Owner explicitly opted into the orchestration token scale. Combined
with the design-audit choice, this became "whole review orchestrated" (below).

---

## Findings handoff format

| Option | Description | Selected |
|--------|-------------|----------|
| Structured FINDINGS.md | id, file:line, why-wrong, repro, proposed test sketch | ✓ |
| New requirement IDs | Promote each to BUG-05.x in REQUIREMENTS.md | |
| GSD todos | One pending todo per finding | |

**User's choice:** Structured FINDINGS.md.

---

## Design-review depth

| Option | Description | Selected |
|--------|-------------|----------|
| Named four + bounded sweep | Four named flaws required; flag egregious extras only | |
| Named four only | Strictly the four flaws + folded todos | |
| Broad design audit | Full software-design sweep | ✓ |

**User's choice:** Broad design audit.
**Notes:** Claude flagged the scoping implication — broad audit + adversarial
review likely yields a large FINDINGS.md and therefore a bigger Phase 5. Accepted
deliberately; recorded as a scoping risk and reinforces the FINDINGS.md handoff.

---

## Review orchestration (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Whole review orchestrated | Both design + math run as one multi-agent workflow | ✓ |
| Math orchestrated, design manual | Multi-agent for math only | |
| Decide at plan time | Record both, let plan-phase pick | |

**User's choice:** Whole review orchestrated.

---

## coerce-null todo disposition (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Log as Phase-5 bug | Correctness bug → FINDINGS.md → Phase 5 with proving test | ✓ |
| Safe-fix now | Trivial coercion; fix in Phase 4, regression test in Phase 5 | |

**User's choice:** Log as Phase-5 bug.

---

## ruff adoption (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Adopt for the sweep; CI later | ruff config + fixes in Phase 4; CI enforcement Phase 6 | ✓ |
| Surface only, full swap logged | Run ruff read-only; keep black; log the migration | |
| Defer entirely to Phase 6 | No tooling change in Phase 4 | |

**User's choice:** Adopt for the sweep; CI later.
**Notes:** Black→ruff-format left at planner discretion for lowest churn; style
stays black-equivalent.

---

## PerspectiveProjection depth (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Review, flag as WIP-gaps | Softer bar; WIP completeness gaps ≠ correctness bugs | |
| Full adversarial, same bar | Same correctness standard as shipped projections | ✓ |
| Out of scope this phase | Exclude entirely (would contradict D-02/D-03) | |

**User's choice:** Full adversarial, same bar.
**Notes:** Upholds Phase-1 D-02/D-03 (PerspectiveProjection math owned by Phase 4).

---

## Claude's Discretion

- Workflow fan-out shape, reviewer counts, adversarial vote thresholds.
- Replace black with `ruff format` vs. keep black (lowest churn).
- FINDINGS.md entry ordering + severity taxonomy.

## Deferred Ideas

- CI enforcement of ruff / lint gate → Phase 6.
- Fixing correctness bugs (BUG-01..05, coerce-null, in-place mutation,
  `__array_ufunc__`) → Phase 5.
- cuda11/cuda12 docs may relocate to Phase 6 if it fits publication docs better.
