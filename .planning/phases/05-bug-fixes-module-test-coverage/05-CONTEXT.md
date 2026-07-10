# Phase 5: Bug Fixes & Module Test Coverage - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the correctness bugs surfaced by the Phase-4 review (BUG-01..05) — the 24
adversarially-refuted findings in `04-FINDINGS.md` are the canonical work-list —
each with a proving test, and cover the four previously-untested module areas
(TEST-03..06: projection/interpolation math, derivative features + the
feature-name DSL, orchestration `FeatureManager`/`TiledPointCloudImageGenerator`,
and `util.py`).

**Scope shape (owner chose the thorough path throughout):** this is a *larger*
Phase 5 than the base roadmap implied. Beyond the logged findings it deliberately
pulls in: completion of the WIP PerspectiveProjection math, a full
`image_cache/` → GSEGUtils consolidation, unification of the two registries, and
PERF-02/PERF-03 parameterization pulled forward from v2. The planner should size
for multiple waves and reflect the PERF-02/PERF-03 pull-forward as a
REQUIREMENTS traceability update.

**Fixed by the roadmap (not up for discussion):** WHAT gets fixed (the FINDINGS
list) and the "every correctness fix has a proving test" guarantee (Phase-4 D-02).
Discussion decided HOW: the fix line, the shape of behavior-changing fixes, the
test approach, and the execution methodology.

**Explicitly NOT this phase:** publication CI/CD + branch protection (Phase 6),
the BC-01 migration record itself (Phase 6 — but Phase 5 *accumulates* its raw
material), and the cross-repo spherical-seam system fix (deferred — see Deferred
Ideas).

</domain>

<decisions>
## Implementation Decisions

> **Two-bucket work-list.** Every finding not explicitly re-dispositioned below is
> a **genuine fix** — apply the fix per its `04-FINDINGS.md` proving-test sketch,
> test-first (`xfail`→`pass`). Three findings are re-dispositioned as
> **kept-behavior** (M-06, M-10, M-11): current default behavior is intentional
> and stays; they get a *characterization test* (pins current behavior) +
> documented owner rationale + a future-improvement log — NOT a fix. Downstream
> agents must not "correct" the kept-behavior findings.

### Fix-line / disposition scope (Area 1)
- **D-01: PerspectiveProjection — fix all three findings now.** M-02 (mask out
  `Z_c ≤ 0` behind-camera points), M-03 (add the camera-translation term → full
  `K·[R|t]·X`), M-04 (remove the dead `project_raw` override), each with a proving
  test. Owner accepts that M-03 is feature-completion, not just a bug patch (upholds
  Phase-4 D-08: perspective reviewed/fixed at the shipped bar).
- **D-02: LOW latent/structural/typing — fix everything.** DSN-08 (add a
  visited-set dependency-cycle guard), DSN-10 (import from `pc2img.core`, not the
  package barrel), DSN-11 (annotate `type[...] | None`). DSN-09 (pickle) is
  resolved by construction via the store consolidation (D-05).
- **D-03: PERF-linked halves — fix correctness AND land parameterization.**
  M-08 gets the float32 fix (see below); PERF-02 (explicit reduced-precision
  opt-in) and PERF-03 (Delaunay thresholds) are pulled forward from v2 as opt-in
  parameters. NOTE: for M-06 this was superseded by D-07 — the *default* does not
  change; only the parameters are added.

### Fix shape — behavior-changing (Area 2)
- **D-04: BUG-02 / DSN-02 → reparent, don't patch.** Make `DiskBackedImageData`
  a thin subclass of `GSEGUtils.DiskBackedNDArray` (keep only `to_uint8()` + the
  `ndim∈(2,3)` shape assertion), **delete** the broken `__array_ufunc__` override
  → inherit GSEGUtils' working one. Result: arithmetic works, returning plain
  ndarrays. Proving test asserts a *correct arithmetic result* (supersedes the
  earlier "clean-raise `NotImplementedError`" instinct, which the owner had
  chosen before learning GSEGUtils already ships the working fix and that
  `interpolation.py` already consumes these primitives).
- **D-05: DSN-09 / store → adopt `GSEGUtils.DiskBackedStore`.** Replace
  `DiskBackedImageStore`'s internals (the `pickle.load`/`.pkl` sink) with
  `DiskBackedStore[DiskBackedImageData]` (the hardened `.npy` + `.meta.json`,
  `allow_pickle=False` codec). DSN-09 is then eliminated by construction.
  Cache on-disk format changes `.pkl` → `.npy` (a BC-01 entry). **Research flag:**
  planner must map the store's public surface (`add_image_to_store`, `offload` /
  `offload_image_data_to_disk`, `enable_caching` / `purge_disk_on_gc` semantics,
  `__getstate__`/`__setstate__`) onto `DiskBackedStore`; if a *GSEGUtils* change
  is required, that trips the dependency-approval gate.
- **D-06: M-06 (Delaunay culling) → KEPT-BEHAVIOR.** The interior-culling
  heuristic is intentional — the owner added it to suppress large interpolation
  artifacts across data gaps/occlusions, and it measurably reduced artifact noise
  in a downstream optical-flow task. Keep it as the default. Expose the area /
  aspect-ratio thresholds as opt-in parameters whose **defaults equal today's
  values** (zero behavior change; satisfies PERF-03). Characterization test pins
  current behavior. Log the over-culling-on-anisotropic-scans as a future
  improvement.
- **D-07: M-10 (GradientFeature spacing `100`) → KEPT-BEHAVIOR.** The `100` was
  chosen for downstream tasks; `1.0` would not "solve" it, only reshuffle an
  arbitrary scale, and a principled value needs a real investigation. Keep `100`
  as the default. Expose it as a `pixel_size`-style parameter (default `100`,
  no output change). Characterization test. Log "principled gradient spacing" as
  a future investigation.
- **D-08: M-11 (Hillshade aspect handedness) → KEPT-BEHAVIOR.** pc2img rasters
  carry NO north-up guarantee (spherical → elevation/azimuth bins; orthographic →
  an arbitrary xy/xz/yz plane), so "fix to ESRI compass" is ill-defined. Keep the
  current aspect default. Document the non-north-up internal convention. Add a
  self-consistency test (not ESRI-compass truth). Defer an "align north" option —
  it needs an external north azimuth pc2img does not carry (georeferencing), and
  would strain the regex feature-name DSL.
- **D-09: M-08 (nanconv float16 overflow) → genuine fix.** Accumulate/divide in
  float32 (float16 overflows to `inf` on realistic range magnitudes). PERF-02's
  explicit reduced-precision opt-in may ride along as a parameter.

### Test strategy & coverage (Area 3)
- **D-10: Behavioral-sufficiency + ratchet the floor.** Primary goal is meaningful
  behavioral coverage of TEST-03..06 plus every proving/characterization test;
  then re-measure and ratchet the CI `--cov-fail-under` floor up to the new
  measured baseline. No fixed-% chase (fits the existing floor-as-ratchet design;
  current floor 35%, baseline 37%).
- **D-11: Shared synthetic fixture factory in a new `tests/conftest.py`.** Build
  real minimal `PointCloudData` from synthetic arrays (pchandler 2.x
  `PointCloudData(xyz)` takes a raw `Nx3` array directly; `**PointCloudDataKW`
  attaches named scalar fields). Deterministic, fast, NO committed binary
  fixtures. Lightweight duck-type stubs (`.xyz`/`.nbPoints`, `FakeProjection`)
  only where constructing a full PCD is genuinely heavy. pchandler's own test
  fixtures are NOT reusable (loader/IO-focused, committed E57/PLY binaries, no
  importable `conftest`) — verified.
- **D-12: Test-first per finding.** Genuine fixes: write the proving test as
  `xfail` first, then apply the fix to flip it to `pass` (self-evident audit
  trail; coverage ratchets as xfails flip). Kept-behavior findings: passing
  characterization tests from the start. Also flip the existing xfails as their
  bugs are fixed (DSN-06 `test_point_cloud_image_generator.py:35`; the
  `test_disk_backed_image_data.py` xfails).

### Execution methodology (Area 4)
- **D-13: Wave-based plan grouped by source file.** Standard `gsd-plan-phase` →
  `gsd-execute-phase` (NOT the Phase-4 bespoke Workflow harness). Group findings
  by source file into plan units — fixes run sequentially within a file (shared
  context, no worktree collisions: `projection.py` hosts 5 findings, `util.py` 3,
  `derivative_features.py` 4), waves parallelize across non-overlapping files.
  TEST-03..06 authoring can parallelize by module.
- **D-14: DSN-05 registries → unify now.** Build a single registry
  protocol/adapter across `StrategyRegistry` and `FeatureRegistry` with one
  miss-exception type. Fold in the `match()`-without-instantiation sub-fix
  (a `dependencies_for(params)` classmethod so `match()` stops constructing the
  class just to read `.dependencies`). Proving tests for both families. NOTE: the
  miss-exception contract changes (`KeyError` for strategies vs `RuntimeError` for
  features → one type) — a public-behavior change → a BC-01 entry.
- **D-15: M-05 (spherical seam) → consistency guard + defer the system fix.**
  pchandler already owns seam tracking (`FoV.crosses_pi`, `horizontal_extent`,
  `_non_wrapping_segments`, and `FoV.tile()` already fail-fasts on wrapping FoVs).
  pc2img ignores it: `SphericalProjection.project_raw` AND `inverse_projection`
  both read raw `fov.left`/`fov.right` and assume `left < right`. Phase-5 action:
  add a `crosses_pi` detection to BOTH `project_raw` and `inverse_projection`
  that raises a clear error mirroring pchandler's `FoV.tile()` split-first
  message — converts silent reversed-columns into an explicit refusal, invents no
  mapping, keeps forward/inverse in sync. Test asserts it raises on a wrapping
  FoV. The real seam handling (split-first tiling → segment projection →
  inverse/uplift reconciliation) is DEFERRED — see Deferred Ideas. Behavior-change
  caveat: a single (untiled) cloud with a wrapping FoV passed directly to
  projection now raises instead of silently producing reversed columns (accepted).
- **D-16: M-13 (RRIM ray sampling) → defer/log.** The openness/slope math is
  confirmed correct; this is LOW sampling fidelity (int-rounded ray steps + dedup
  drop near-axis samples; direction geometry ignores `pixel_size` anisotropy) on
  an opt-in feature. Document + log as a future improvement; no fix this phase.
- **D-17: BC-01 → accumulate a running breaking-change note during Phase 5.** As
  each behavior/output/format/error-type-changing fix lands, append an entry
  (public-API delta, cache-format change `.pkl`→`.npy`, arithmetic surface now
  live, registry miss-exception type change, the new M-06/M-10 params) to a
  running scratch that Phase 6's BC-01 consumes directly rather than
  reconstructing from git diffs.

### Claude's Discretion
- Exact wave grouping and plan-unit boundaries by file (D-13).
- Whether M-06/M-10 threshold/spacing parameters land as constructor kwargs or via
  the feature-name DSL, provided defaults are unchanged.
- Whether M-05's guard is a shared helper vs inlined in both methods.
- Whether the store-consolidation mapping (D-05) keeps `DiskBackedImageStore`'s
  class/API as a thin wrapper over `DiskBackedStore` or replaces it — planner's
  call after the API-gap analysis.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & the BUG-05 work-list
- `.planning/ROADMAP.md` §"Phase 5" — goal + the 5 success criteria.
- `.planning/REQUIREMENTS.md` — BUG-01..05, TEST-03..06 (this phase). NOTE:
  PERF-02 + PERF-03 are pulled forward from v2 into this phase (D-03/D-06/D-07/
  D-09) — traceability update for planning.
- `.planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS.md` —
  **THE canonical BUG-05 work-list**: 24 adversarially-refuted findings,
  most-severe-first, each with `file:line`, repro, and a proving-test sketch.
  Read in full before planning.
- `.planning/phases/04-code-quality-algorithmic-soundness-review/04-CONTEXT.md` —
  governing Phase-4 decisions D-02 (log→fix-in-Phase-5 with proving test), D-06
  (findings schema), D-08 (perspective at shipped bar).

### GSEGUtils consolidation targets (D-04, D-05)
- `/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_ndarray.py` —
  `DiskBackedNDArray` with the WORKING `__array_ufunc__` (unwrap→delegate→plain
  ndarray); the BUG-02 reference implementation to inherit from.
- `/scratch/30_GSEGUtils/src/GSEGUtils/lazy_disk_cache/disk_backed_store.py` —
  `DiskBackedStore`: the hardened `.npy` + `.meta.json`, `allow_pickle=False`
  codec (`_write_entry` ~L361-381, `_load_entry` ~L417-456, legacy-pickle
  handling ~L240/436); the DSN-09 replacement.
- `src/pc2img/strategies/interpolation.py:10-11,112,162-165` — pc2img ALREADY
  uses `DiskBackedStore[DiskBackedNDArray]` with a `factory=`; the in-repo
  precedent the consolidation follows.

### pchandler spherical-seam tracking (D-15, deferred investigation)
- `/scratch/41_pchandler/src/pchandler/geometry/spherical/fov.py` —
  `FoV.crosses_pi` (L292), `horizontal_extent` (L302), `_non_wrapping_segments`
  (L376), and `FoV.tile()` (L706, already fail-fasts on wrapping FoVs). The seam
  tracking lives here; pc2img must consume it.
- `src/pc2img/strategies/projection.py:120-121` (`project_raw` raw left/right) and
  `:127+` (`inverse_projection`/uplift, same assumption) — the M-05 anchors.

### Test baseline & existing xfails to flip (D-10, D-12)
- `CONTRIBUTING.md` §"Coverage baseline" — floor 35%, baseline 37%, ratchet design.
- `tests/test_point_cloud_image_generator.py:35` (DSN-06 xfail) and
  `tests/test_disk_backed_image_data.py` (xfails at :50,:115,:155,:175,:241) —
  flip as fixes land.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GSEGUtils.DiskBackedNDArray` / `DiskBackedStore` — the consolidation targets;
  already installed (GSEGUtils 0.5.2) and already consumed in `interpolation.py`.
- pchandler `FoV.crosses_pi` / `horizontal_extent` / `_non_wrapping_segments` —
  the seam-tracking API the M-05 guard consumes (no reinvention).
- `coerce_lazy_cfg` / `coerce_img_res` (`core.py`) — the None-sentinel coercion
  pattern for DSN-06 (omitted-config coercion) and DSN-07 (mutable default).
- `PointCloudData(xyz)` (pchandler 2.x) — raw `Nx3` array constructor, the basis
  for the synthetic `conftest.py` fixture factory.
- `FakeProjection` pattern in `tests/test_point_cloud_image_generator.py` — the
  lightweight duck-type stub for isolating strategy contracts.

### Established Patterns
- Strategy/feature registries with import-time decorator registration — DSN-05
  unifies the two (`strategies/registry.py` KeyError vs `features/registry.py`
  RuntimeError).
- `DiskBackedStore[T]` with `factory=` — the generic disk-backed store pattern
  already used for triangulation precalc; the store consolidation follows it.
- Test-first `xfail`→`pass` + the coverage-floor ratchet from Phase 3.

### Integration Points
- `image_cache/` (both `DiskBackedImageData` and `DiskBackedImageStore`) reparents
  onto GSEGUtils — public `image_cache/__init__.py __all__` surface + on-disk cache
  format both change (BC-01).
- pc2img consumes pchandler/GSEGUtils *existing* API only — no dependency edits, so
  no approval gate — UNLESS the store-API-gap analysis (D-05) or the deferred seam
  investigation needs a GSEGUtils/pchandler change (then the gate applies).
- FINDINGS.md → this phase's plan units, grouped by source file (D-13).

</code_context>

<specifics>
## Specific Ideas

- The BUG-02 and DSN-09 fixes are really "finish an in-progress migration":
  `interpolation.py` already moved onto GSEGUtils primitives; only `image_cache/`
  still rolls its own (broken ufunc + pickle store). Reparenting resolves both by
  construction rather than patching.
- M-05's silence — not the reversal itself — is what made a real past bug hard to
  trace (seam-straddling clouds tiled into smaller tiles, some reverting to one
  side; the uplift step then couldn't reconcile mixed adapted/non-adapted depth
  images). The guard's job is to end the silence, consistent with pchandler's
  own `FoV.tile()` refusal.
- The three kept-behavior findings (M-06/M-10/M-11) are a deliberate signal that a
  code review's "silent wrong output" can be an owner's intentional, downstream-
  validated design choice — recorded so no downstream agent "fixes" them.

</specifics>

<deferred>
## Deferred Ideas

- **Spherical-seam system fix (cross-repo).** The coherent seam strategy —
  split-first tiling → per-segment projection → inverse_projection/uplift
  reconciliation of adapted vs non-adapted depth images — is deferred to a
  dedicated future investigation, likely its own milestone. Owner note: it will
  probably require a **combined workspace holding pchandler + pc2img + the
  downstream consumer library** to solve consistently across the pipeline, and may
  cross the dependency-approval boundary. Anchored on pchandler's
  `crosses_pi`/`horizontal_extent`/`_non_wrapping_segments`/`tile()`-guard and
  pc2img's `project_raw` + `inverse_projection`.
- **M-06 over-culling refinement** — a better gap/occlusion heuristic that doesn't
  drop valid interior triangles on anisotropic scans (kept-behavior default stands
  meanwhile; thresholds now tunable).
- **M-10 principled gradient spacing** — replace the tuned `100` with a
  physically-meaningful spacing after investigation (param default stays `100`).
- **M-11 "align north" hillshade option** — gated on pc2img carrying
  georeferencing / a north-azimuth reference it does not have today.
- **M-13 RRIM near-axis ray-sampling fidelity** — dedup-aware ray stepping +
  `pixel_size` anisotropy in the direction geometry.
- **Full `DiskBackedImageStore` → `DiskBackedStore` API convergence** — if D-05
  lands only a thin-wrapper mapping, a later pass may collapse the wrapper.
- **v2 PERF items not pulled forward** — PERF-01 (triangulation keying), PERF-04
  (`_triangulation_precalc` growth bound) remain v2.

</deferred>

---

*Phase: 5-Bug Fixes & Module Test Coverage*
*Context gathered: 2026-07-10*
