# Phase 5: Bug Fixes & Module Test Coverage - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-10
**Phase:** 5-Bug Fixes & Module Test Coverage
**Areas discussed:** Fix-line/disposition scope, Fix shape (behavior-changing), Test strategy & coverage, Execution methodology

---

## Area 1 — Fix-line / disposition scope

### Perspective findings (M-02/M-03/M-04)
| Option | Description | Selected |
|--------|-------------|----------|
| Guards + cleanup, defer t | Fix M-02 + M-04, defer M-03 translation as WIP | |
| Fix all three now | Complete perspective correctness incl. M-03 K·[R\|t]·X | ✓ |
| Log-only, defer to future phase | No perspective fixes this phase | |

**User's choice:** Fix all three now.

### LOW latent/structural/typing/security (DSN-08/09/10/11)
| Option | Description | Selected |
|--------|-------------|----------|
| Fix cheap ones, document pickle | Fix DSN-08/10/11, document DSN-09 contract only | |
| Fix everything including pickle | Also replace pickle with .npy/safetensors | ✓ |
| Defer all LOW-latent to Phase 6 | Phase 5 handles only MED+ | |

**User's choice:** Fix everything.
**Notes:** Owner flagged that a similar pickle fix was already done in GSEGUtils — reuse that approach. (Confirmed: GSEGUtils migrated to `.npy` + `.meta.json` / `allow_pickle=False`.) This later folded into the store consolidation (Area 2, D-05).

### PERF-linked halves (M-06/M-08)
| Option | Description | Selected |
|--------|-------------|----------|
| Fix correctness now, defer perf-knob | Correctness only; PERF-02/03 stay v2 | |
| Fix correctness + land parameterization | Pull PERF-02/03 params forward | ✓ |

**User's choice:** Fix correctness + land parameterization.
**Notes:** Later refined in Area 2 — for M-06 the *default* does not change (kept-behavior); only the parameters are added.

---

## Area 2 — Fix shape (behavior-changing)

### BUG-02 __array_ufunc__ (element half)
| Option | Description | Selected |
|--------|-------------|----------|
| Reparent onto DiskBackedNDArray | Subclass GSEGUtils, inherit working ufunc | ✓ |
| Keep Option 3 (clean-raise stub) | Standalone, raise proper NotImplementedError | |
| Reparent AND re-wrap results | Return DiskBackedImageData from arithmetic | |

**User's choice:** Reparent onto DiskBackedNDArray.
**Notes:** Owner initially chose clean-raise `NotImplementedError` + defer, and raised whether the disk-backing aspect should move to GSEGUtils. Investigation showed GSEGUtils' `DiskBackedNDArray` already implements the working ufunc and `interpolation.py` already consumes it — so reparenting is cheaper than the stub and gives working arithmetic. Owner switched to reparent.

### DSN-09 store (store half)
| Option | Description | Selected |
|--------|-------------|----------|
| Mirror the .npy codec locally now | Fix in pc2img's own store | |
| Adopt GSEGUtils DiskBackedStore now | Full store consolidation | ✓ |
| Document contract now, defer the fix | DSN-09 stays open, documented | |

**User's choice:** Adopt GSEGUtils DiskBackedStore now (full consolidation).

### M-06 / M-10 defaults
**User's choice (free-form):** KEEP current defaults for both — they are intentional.
**Notes:** M-06 culling was implemented deliberately to suppress interpolation artifacts across data gaps/occlusions and measurably reduced noise in a downstream optical-flow task. M-10's `100` was chosen for downstream tasks; `1.0` doesn't "solve" it. Both re-dispositioned as kept-behavior + characterization test + expose params (defaults unchanged) + future-improvement log.

### M-11 hillshade orientation
**User's choice (free-form):** No north-up guarantee → keep default (backward compatible), document, consistency test. "Align north" option considered but deferred (owner worried about regex-DSL ergonomics; Claude added: also lacks a north reference without georeferencing).

---

## Area 3 — Test strategy & coverage

### Coverage target
| Option | Description | Selected |
|--------|-------------|----------|
| Behavioral-sufficiency + ratchet floor | Cover modules, ratchet floor to new baseline | ✓ |
| Fixed % target (e.g. 70%) | Drive to a concrete number | |

**User's choice:** Behavioral-sufficiency + ratchet floor.

### Fixtures
**User's choice (free-form):** Shared synthetic `conftest.py` factory building real `PointCloudData`.
**Notes:** Owner asked whether pchandler's test fixtures could be reused; investigation showed they're loader/IO-focused with committed binaries and no importable conftest — not reusable. Owner agreed a fresh conftest is cheap and better targeted.

### Ordering
**User's choice:** Test-first per finding (`xfail`→`pass`) for genuine fixes; passing characterization tests for kept-behavior findings.

---

## Area 4 — Execution methodology

### Execution shape
| Option | Description | Selected |
|--------|-------------|----------|
| Wave-based plan grouped by file | Standard gsd-plan/execute, file-grouped | ✓ |
| Multi-agent orchestrated fan-out | Phase-4 style Workflow harness | |

**User's choice:** Wave-based plan grouped by file.

### DSN-05 registries
| Option | Description | Selected |
|--------|-------------|----------|
| Keep + document + cheap sub-fix | Don't unify; do match() sub-fix only | |
| Unify the registries now | Single protocol/adapter, one exception type | ✓ |
| Document only, no code change | Just record design debt | |

**User's choice:** Unify the registries now.
**Notes:** Claude flagged the miss-exception contract change (KeyError vs RuntimeError → one type) as a BC-01 item.

### BC-01 accumulation
| Option | Description | Selected |
|--------|-------------|----------|
| Accumulate a running BC note during Phase 5 | Track as fixes land | ✓ |
| Let Phase 6 reconstruct from commits | No tracking now | |

**User's choice:** Accumulate a running BC note during Phase 5.

---

## Residual findings locked (M-05, M-13)

### M-05 spherical seam
**User's choice (free-form):** Consistency guard (mirror pchandler's `FoV.tile()` refusal on `crosses_pi`) in both `project_raw` and `inverse_projection`, defer the system fix.
**Notes:** Owner confirmed seam-straddle happens in real data and recalled a past tiling/uplift bug (tiles reverting to one side; mixed adapted/non-adapted depth images in the uplift). Investigation confirmed pchandler already tracks the seam and pc2img ignores it in both forward and inverse projection. Owner noted the full fix likely needs a combined pchandler + pc2img + downstream workspace.

### M-13 RRIM ray sampling
**User's choice:** Defer/log as future improvement (openness math is correct; LOW fidelity on an opt-in feature).

---

## Claude's Discretion

- Wave grouping / plan-unit boundaries by file (D-13).
- Whether M-06/M-10 params land as constructor kwargs vs feature-name DSL (defaults unchanged).
- Whether M-05's guard is a shared helper vs inlined.
- Whether the store consolidation keeps `DiskBackedImageStore` as a thin wrapper vs replaces it.

## Deferred Ideas

- Spherical-seam system fix (cross-repo: pchandler + pc2img + downstream, combined workspace).
- M-06 over-culling refinement; M-10 principled spacing; M-11 "align north" (needs georeferencing); M-13 ray-sampling fidelity.
- Full `DiskBackedImageStore` → `DiskBackedStore` API convergence (if D-05 lands a thin wrapper).
- v2 PERF-01, PERF-04 not pulled forward.
