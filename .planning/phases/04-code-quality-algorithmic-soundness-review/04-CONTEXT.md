# Phase 4: Code Quality & Algorithmic Soundness Review - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 is a **review phase** across three pillars, with a deliberately narrow
fix budget and a structured handoff to Phase 5:

1. **QUAL-01 — mechanical hygiene (FIX here):** remove dead/commented code,
   collapse the duplicate `joblib` pin, replace placeholder `pyproject`
   metadata, remove the duplicate `convert_to_image`, move matplotlib to an
   optional extra.
2. **QUAL-02 — software-design review (broad audit; fix only the safe,
   mechanical ones):** the four named flaws (divergent registries, in-place
   raster mutation, missing dependency-cycle guard, broken `make_generator`)
   are required anchors, but the audit is intentionally **broad** across the
   codebase.
3. **QUAL-03 — mathematical/algorithmic soundness (review + log):** projection
   geometry (spherical, orthographic, **and** the WIP `PerspectiveProjection`),
   Delaunay culling heuristics, NaN-aware smoothing (`nanconv`/`convert_to_image`),
   and feature math.

**Output:** a structured `FINDINGS.md` whose entries are the concrete, testable
BUG-05 inputs for Phase 5. Correctness bugs are **surfaced and specified here,
fixed-with-a-proving-test in Phase 5** — they are not fixed in Phase 4.

**Explicitly NOT this phase:** fixing behavioral/correctness bugs (Phase 5),
adding tests (Phase 5), CI enforcement / branch protection (Phase 6), new
projection/interpolation/feature algorithms.

</domain>

<decisions>
## Implementation Decisions

### Fix-vs-log boundary
- **D-01:** **Fix in Phase 4** = QUAL-01 hygiene in full **plus** low-risk,
  purely-mechanical design fixes that carry no behavioral risk (e.g. guard the
  `_TransformArray` import; delete/repair the broken `make_generator` factory).
- **D-02:** **Log for Phase 5** = anything behavioral or correctness-affecting
  (in-place raster mutation semantics, `__array_ufunc__` returning bare
  `NotImplemented`, all math findings). Each becomes a FINDINGS.md entry and is
  fixed-with-a-proving-test in Phase 5. This preserves the "every bug fix has a
  proving test" guarantee.

### Review methodology (QUAL-02 + QUAL-03)
- **D-03:** **The whole review runs as ONE orchestrated multi-agent workflow.**
  Fan out independent reviewers across design dimensions and math paths, have
  each adversarially try to *refute* correctness, verify survivors, then
  synthesize into FINDINGS.md. The owner explicitly opted into this token
  scale. (Concretely: this is a `/gsd-plan-phase`-driven review executed via the
  Workflow orchestration harness — planner decides fan-out shape, agent counts,
  and verification vote thresholds.)
- **D-04:** **Design audit is BROAD**, not limited to the four named flaws. The
  four named flaws are required anchors that MUST appear in FINDINGS.md if still
  present; the audit additionally sweeps the codebase for other design issues.
- **D-05:** **Math review is adversarial with empirical checks** — reviewers
  should ground claims in the reference formulas and, where cheap, back findings
  with minimal numeric probes (project known points, verify hull culling, NaN
  propagation), not read-only assertion.

### Findings handoff format
- **D-06:** Findings are logged to a single **structured `FINDINGS.md`**
  (`.planning/phases/04-.../04-FINDINGS.md`). Every entry carries: a stable id,
  `file:line` location, a one-line defect statement, why-it's-wrong, a minimal
  repro (inputs → wrong output), severity, pillar (design/math/hygiene), and a
  **proposed proving-test sketch**. Phase 5 consumes these directly as BUG-05
  inputs without re-deriving them.
- **D-07:** FINDINGS.md is the canonical BUG-05 feeder. Do **not** promote each
  finding to its own `BUG-05.x` requirement ID (keeps REQUIREMENTS.md stable);
  do **not** scatter findings across GSD todos.

### PerspectiveProjection (WIP folded code)
- **D-08:** Reviewed at the **same correctness bar** as the shipped
  spherical/orthographic projections (owner override of the softer "WIP-gaps"
  option). Any unsound math becomes a BUG-05 item in FINDINGS.md. This upholds
  D-02/D-03 from Phase 1 (PerspectiveProjection math is owned by Phase 4).

### Tooling — ruff
- **D-09:** **Adopt ruff (Astral)** as the lint/format tool in Phase 4 and use it
  to power the QUAL-01 hygiene sweep (dead code, unused imports, etc.). Land the
  `ruff` config + apply its fixes here. Ruff is the current ecosystem norm
  (supersedes flake8 + isort; `ruff format` is black-compatible).
- **D-10:** **Defer CI *enforcement* of ruff to Phase 6** (where branch-protection
  / CI hardening lives). Phase 4 lands config + fixes only; it does not wire a
  blocking lint gate into CI.
- **D-11:** Black→ruff-format handling is the **lower-churn option at planner
  discretion**: default is to replace black with `ruff format` (drop-in,
  black-compatible, collapses two tools into one); keeping black is acceptable if
  that proves lower-churn given existing config. Either way the formatting style
  stays black-equivalent (88-col).

### Claude's Discretion
- Exact workflow fan-out shape, reviewer counts, and adversarial vote thresholds
  (planner/executor decide per module count + complexity).
- Whether to replace black with `ruff format` or keep black (D-11), chosen for
  lowest churn.
- FINDINGS.md entry ordering and severity taxonomy (most-severe first).

### Folded Todos
All four phase-matched todos were folded into Phase 4 scope:

- **`guard-transformarray-module-import`** (`projection.py:12`) — private
  `pchandler._TransformArray` imported at module level; a future pchandler
  drop/rename breaks importing the whole projection module. **Disposition: FIX
  in Phase 4** (safe design fix, QUAL-02). Confirmed live: import at
  `projection.py:12`, used at `projection.py:192`.
- **`coerce-null-lazy-disk-cache-config`** — `None`-default
  `lazy_disk_cache_config` on `PointCloudImageGenerator` isn't coerced.
  **Disposition: LOG as a Phase-5 BUG** (behavioral; gets a proving test in
  Phase 5, consistent with D-02). A safe coercion pattern already exists
  (`coerce_lazy_cfg` in `core.py`).
- **`move-to-ruff-lint-ci`** — **Disposition: PARTIALLY folded** per D-09/D-10:
  adopt ruff + apply fixes in Phase 4; defer the CI enforcement half to Phase 6.
- **`document-cuda11-vs-cuda12-selection-guidance`** — driver-based cuda11/cuda12
  selection guidance. **Disposition: folded as a minor docs deliverable** in
  Phase 4. Tangential to the review pillars; keep it small (a short selection
  note). Planner may relocate to Phase 6 (publication) if it fits better there.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & success criteria
- `.planning/ROADMAP.md` §"Phase 4" — goal + the 4 success criteria (SC1 hygiene,
  SC2 design addressed/logged, SC3 math review complete, SC4 correctness → BUG-05).
- `.planning/REQUIREMENTS.md` — QUAL-01, QUAL-02, QUAL-03 (this phase); BUG-05 and
  TEST-03..06 (Phase 5 consumers of this phase's output).

### Codebase maps (read to scope the broad audit)
- `.planning/codebase/CONCERNS.md` — pre-catalogued design/quality concerns;
  primary seed list for the QUAL-02 audit.
- `.planning/codebase/ARCHITECTURE.md` — anti-patterns section (divergent
  registries, broken `make_generator`, `__array_ufunc__` `NotImplemented`,
  in-place mutation, import-time registration, circular-import sensitivity).
- `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/STACK.md`,
  `.planning/codebase/STRUCTURE.md`, `.planning/codebase/TESTING.md` — grounding.

### Known-flaw source anchors (verified 2026-07-10)
- `src/pc2img/registry.py:7` — `make_generator` (broken factory) [QUAL-02].
- `src/pc2img/strategies/projection.py:12,192` — module-level private
  `_TransformArray` import + use [QUAL-02, folded todo].
- `src/pc2img/image_cache/disk_backed_image_data.py:73` — `__array_ufunc__`
  raises bare `NotImplemented` (a name, not an exception) [BUG-02, log for P5].
- `src/pc2img/util.py:58` **and** `:231` — duplicate `convert_to_image`
  definitions [QUAL-01, fix].
- `pyproject.toml:21` **and** `:24` — duplicate `joblib` pins (`~=1.5` / `~=1.3`)
  [QUAL-01, fix].
- Math paths for QUAL-03: `src/pc2img/strategies/projection.py` (spherical /
  orthographic / PerspectiveProjection), `src/pc2img/strategies/triangulation.py`
  + `strategies/interpolation.py` (Delaunay culling), `src/pc2img/util.py`
  (`nanconv`, `convert_to_image`, `replace_nan`), `src/pc2img/features/derivative_features.py`
  + `features/rrim.py` (feature math).

### RRIM (context only — do not reopen)
- `.planning/phases/03.1-.../03.1-ADR-rrim-ip-disposition.md` + top-level
  `NOTICE` — RRIM IP gate is CLEARED; treat `rrim.py` math like any other feature
  math, but do not touch its IP posture.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `coerce_lazy_cfg` / `coerce_img_res` (`core.py`) — the None-sentinel coercion
  pattern to reference when logging the `coerce-null-lazy-disk-cache-config`
  finding (and eventually fixing it in Phase 5).
- `.planning/codebase/CONCERNS.md` + `ARCHITECTURE.md` anti-patterns — a
  pre-built seed list so the broad audit isn't cold-started.
- Green pytest suite (Phase 3) with 15 passed / 11 xfailed — the xfail reasons
  already encode several known bugs; cross-reference them when building FINDINGS.

### Established Patterns
- Strategy-registry + decorator registration; import-time side-effect registration
  (`features/__init__.py`, `strategies/__init__.py`) — the "divergent registries"
  finding lives in the split between `strategies/registry.py` (generic) and
  `features/registry.py` (regex DSL).
- Pydantic `@validate_call` + `BeforeValidator` coercion at API boundaries
  (`core.py`) — the idiom the coerce-null finding should follow.
- NaN-sentinel numeric discipline (`np.errstate`, `np.divide(where=...)`,
  `.astype(np.float32, copy=False)`) — the correctness contract the math review
  checks against.

### Integration Points
- FINDINGS.md → Phase 5 `BUG-05` + `TEST-03..06`: the review output IS the Phase 5
  work-list. Handoff quality (D-06) directly determines Phase 5 planability.
- ruff config lands in `pyproject.toml` alongside the existing black/pytest/coverage
  config; CI enforcement wiring is deferred to `ci.yml` work in Phase 6.

</code_context>

<specifics>
## Specific Ideas

- The review is executed as a **multi-agent orchestration workflow**, not a
  single-reader pass — this is a locked methodology choice (D-03), not merely an
  option for the planner. The planner should structure Phase 4 around a
  find → adversarially-verify → synthesize pipeline producing FINDINGS.md.
- `__array_ufunc__` raising bare `NotImplemented` is itself a latent bug (returns
  the builtin `NotImplemented` name via `raise`, which is a `TypeError` at
  runtime, not the intended `NotImplementedError`) — call this out precisely in
  FINDINGS so Phase 5's BUG-02 test asserts the right exception type.

</specifics>

<deferred>
## Deferred Ideas

- **CI enforcement of ruff / lint gate** → Phase 6 (publication hardening),
  per D-10.
- **Actually fixing the correctness bugs** (BUG-01..05, coerce-null, in-place
  mutation, `__array_ufunc__`) → Phase 5, each with a proving test.
- **cuda11/cuda12 docs** may relocate to Phase 6 if it fits publication docs
  better than a soundness-review phase (planner's call; folded here for now).

### Reviewed Todos (not folded)
None — all four phase-matched todos were folded (with per-todo dispositions in
the Folded Todos section above).

</deferred>

---

*Phase: 4-Code Quality & Algorithmic Soundness Review*
*Context gathered: 2026-07-10*
