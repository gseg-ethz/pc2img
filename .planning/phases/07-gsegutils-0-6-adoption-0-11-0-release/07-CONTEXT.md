# Phase 7: GSEGUtils 0.6 Adoption & 0.11.0 Release - Context

**Gathered:** 2026-10-01
**Status:** Ready for planning

<domain>
## Phase Boundary

pc2img runs on the released GSEGUtils 0.6.0 (PyPI, 2026-08-17) with its home-grown store
overrides removed and containment/deletion delegated upstream; the Phase-6 review items that
gate the release are fixed; `MIGRATION-v0.11.md` is finalised; and 0.11.0 is published to PyPI
through the protected flow (one filtered promotion → release PR merge → back-merge).

Requirements: DEP-05, BC-01 (finalise). Success criteria: ROADMAP.md § Phase 7 (SC1–SC5).

**Measured at discuss time (2026-10-01) — this is a working-path break, not hardening:**
GSEGUtils 0.6.0 *deleted* `DiskBackedStore._get_npy_path` / `_get_meta_path` (no deprecation
shim). pc2img's override calls `super()._get_npy_path(...)`
(`src/pc2img/image_cache/disk_backed_image_store.py:120`) → `AttributeError`. pchandler 2.1.1
(PyPI) requires `GSEGUtils ~= 0.6.0`, and pc2img's current pins (`pchandler ~= 2.1`,
`GSEGUtils >= 0.5.3, < 1.0`) admit both. A fresh unlocked resolve (pchandler 2.1.1 +
GSEGUtils 0.6.0, scratch venv) gives **30 failed / 256 passed** — every store add/delete/
overwrite plus two RRIM end-to-end `generate()` tests. The locked env (0.5.3) and CI stay
green because the lock hides it. Shipping 0.11.0 on today's pins would publish a package that
breaks on a plain `pip install`.

Also measured from the 0.6.0 wheel: `StoreKeyError(ValueError)`,
`StoreContainmentError(StoreKeyError)` — existing `except ValueError` callers keep working.

</domain>

<decisions>
## Implementation Decisions

### Dependency pins
- **D-01:** Pin `GSEGUtils ~= 0.6.0` (i.e. `>= 0.6.0, < 0.7`), matching pchandler 2.1.1's own
  pin. Owner rationale: 0.6.0 just proved a pre-1.0 GSEGUtils *minor* can remove surface pc2img
  uses; an open `< 1.0` cap would ship the next such break silently. Cost accepted: each
  GSEGUtils minor needs a pc2img pin bump + release. Supersedes the todo's `>= 0.6, < 1.0`.
  — **Reversibility:** one-way — published in 0.11.0 metadata on PyPI; loosening later is a new release.
- **D-02:** Raise the pchandler floor: `pchandler >= 2.1.1, ~= 2.1`, so pchandler and pc2img
  always agree on GSEGUtils 0.6 (drops the untested pchandler 2.1.0 + GSEGUtils 0.6 pairing).
  Re-lock `uv.lock`; verify the resolved builds (GSEGUtils `__version__` == 0.6.x and the
  `self._get_npy_path` fingerprint == 0), never trust a cached 0.5.x wheel.
  — **Reversibility:** one-way — published in 0.11.0 metadata.
- **D-03:** Guard against lock-hidden breaks with a **one-shot release check**: before the
  release PR merges, a plan step installs the built wheel into a fresh **unlocked** env (no
  `uv.lock`) and runs the full suite. A permanent CI "unlocked resolve" job is deferred.

### Spikes 001 / 004
- **D-04:** The pending spikes run **inside the research step** (`gsd-phase-researcher`), not
  as separate `/gsd-spike` runs and not as plan tasks. They keep the spike rules from
  `.planning/spikes/MANIFEST.md` (investigation-only, no tree edits — override removal
  simulated by a local subclass; import provenance asserted inside the test process). Verdicts
  are written to RESEARCH.md **and** recorded in `.planning/spikes/MANIFEST.md` (001/004 rows
  move from PENDING to a verdict). This satisfies SC1's "after the pending spikes have run".
- **D-05:** Spike target is the **PyPI 0.6.0 wheel** (what users install). Note any delta vs the
  phase-14 dev tree spike 000 measured.
- **D-06:** Spike 001 covers **every GSEGUtils subclass in pc2img**, not just the store:
  `DiskBackedImageStore`, `DiskBackedImageData`'s `LazyDiskCache` buffer hooks, and the
  `extend_cache_path` drift (BC-GSEG-006) re-derivation. Spike 004 = full suite against 0.6.0
  with the overrides removed; the discuss-time 30-failure run is a first data point only —
  each failure's cause is to be traced, not assumed.

### Store migration (follows the pc2img handoff)
- **D-07:** The migration follows
  `~/gsd-workspaces/pchandler/.planning/handoffs/pc2img-migration-BC-GSEG-006.md` (§3
  checklist). Its line numbers were measured at an older ref (`7893bda`) — re-derive them with
  the handoff's own grep before acting. Where the handoff and the 2026-09-24 todo disagree, the
  **handoff wins** (it was written against released 0.6.0; the todo predates adoption of it).
- **D-08:** **Delete the `__delitem__` override and use upstream `purge(key)`** wherever files
  must be removed (incl. `add_image_to_store`'s overwrite path). This supersedes the todo's
  step 3 ("keep `__delitem__`'s build-both-paths-before-delete ordering"). Owner rationale:
  delete semantics belong upstream — `purge` validates before any mutation, removes all six
  key-derived artefacts (incl. the `.dat` memmap pc2img's pipeline actually writes, which the
  override never removed), and detaches the finalizer (fixes the held-reference/ABA hazard).
  Consequence: `del store[k]` (and `pop`/`clear` built on it) now drops tracking only and no
  longer unlinks files → BC entry. Do not re-create the unlink on another dunder (handoff §2e).
  Note `purge`'s refusal family: `StorePurgeRefusedError` (RuntimeError) and
  `StorePurgeIncompleteError` (**OSError**, outside that family).
  — **Reversibility:** costly — changes public `del` semantics recorded in the 0.11 migration record.
- **D-09:** Delete `_get_npy_path`, `_get_meta_path` and `_assert_within_cache_dir`
  (containment is upstream in 0.6.0, incl. `.dat` containment — handoff §1, §2d). Tests that
  call the removed methods move to the public free functions
  `GSEGUtils.lazy_disk_cache.get_npy_path(cache_dir, key)` / `get_meta_path(...)`. Restate the
  class docstring's threat model once: containment is upstream, construction-time and
  non-adversarial (concurrent writers / racing symlinks / hardlinks are out of scope upstream
  and were never covered by the override either).
- **D-10:** Invalid keys / `extend_cache_path` segments (tile ids, folder names, the
  interpolation hash, scalar-field names): **let upstream `StoreKeyError` propagate** — no
  pc2img pre-validation code. Check the five `extend_cache_path` sites and the realistic
  feature names with `is_valid_store_key` (handoff §2c) and document the rule in the BC entry
  and relevant docstrings. Also audit `clear()` / `.store` (now read-only `Mapping`,
  BC-GSEG-007) usage, incl. the `image_data` legacy alias's `dict[...]` annotation.

### Finding triage rule (fix decisions deferred to the plan)
- **D-11:** Per-finding fix/defer decisions for the parked store and test findings are made **in
  the plan**, not here, by applying this rule. The plan MUST contain a per-finding triage table
  (ID · what it is · rule step · disposition) for owner approval at plan review:
  1. **Upstream-owned → never fixed in pc2img.** Point at the 0.6 fix or the upstream tracking
     item. (Owner guideline: don't fix here what belongs in GSEGUtils.)
  2. **Disappears with deleted code → close as superseded.** No work.
  3. **Part of the migration itself → do it** (handoff checklist, escape-corpus re-run, tests
     that call removed methods, re-pinned escape routes).
  4. **Any other pc2img-owned hardening → only if it is a one-line change with no new
     behaviour; otherwise defer on the record.** No new hardening loops.
  Owner rationale: past iterative fix loops (here and in GSEGUtils) introduced defect after
  defect; the goal is the migration, not chasing hardening that isn't needed.
  Findings in scope of the table: round-3 `review-r3-*` (WR-01, WR-02, WR-04, WR-05, WR-06,
  IN-02), round-2 `review-r2-a7c7f4e498a6`, round-4 `review-r4-a97761a4b73d`,
  `-da637a8dfe3c`, `-ee69c181dfa0`, `-d8efb7e5d778`, and the upstream residuals (finalizer
  ABA, `.dat` symlink-follow, mid-build `OSError` atomicity) — all listed in the 2026-09-24 todo.
- **D-12:** Test-hygiene items `review-r4-84a2b5dff14c` (absent-key delete test: fold or
  differentiate) and `review-r4-15a5c4928dc8` (autouse `tempfile.tempdir → tmp_path` fixture
  for leaked `tmp*` entries) are in scope per SC3; they also go through the D-11 table
  (the first may be superseded by D-08).

### Backlog folded in / release gate
- **D-13:** Release gate (already decided in Phase 6, restated): RTD WR-02
  (`git fetch --tags --force`), WR-03 (unshallow only when shallow, no `|| true`), WR-04
  (`post_install` version/shallow sanity check) land before the 0.11.0 promotion.
- **D-14:** Fix **AR-07 / AR-08** in Phase 7 as the Phase-6 security record states:
  publish-gate check also matches `uv publish` and composite-action-wrapped publish steps
  (WR-06 r1); ruleset preflight rejects required contexts not produced by a
  `pull_request`-triggered workflow (WR-07 r1). Retire AR-07/AR-08 in a Phase-7 security
  verification.
- **D-15:** Fold the ruleset polish: WR-01 (RULESETS.md line naming the five ungoverned
  fields), IN-01..IN-04 (fixture shapes, rule (c) wording, parametrise read-filled test,
  name rule (d) keys).
- **D-16:** **One** filtered promotion `develop-gsd → main` carrying all Phase-7 work (code +
  CI/RTD fixes) after its own review; one back-merge as a merge commit (RELEASE.md step 2);
  nightly ancestry assertion stays green. Matches Phase-6 D-19.
- **D-17:** PyPI trusted publisher + `pypi` environment are owner checkpoints placed
  immediately before the release PR merge (Phase-6 D-30 deferral).

### Migration record (BC-01 finalise)
- **D-18:** Finalise `.planning/MIGRATION-v0.11.md` **before** the release: append the Phase-7
  entries, re-stamp `target_ref` to `v0.11.0` (deterministic tag name), inline verifier green
  before the release PR merges. Expected Phase-7 entries (classification is the planner's,
  per Phase-6 D-25 schema): GSEGUtils/pchandler pin change (`dep-constraint`); `del`/`pop`/
  `clear` no longer delete files, `purge` is the delete verb (`semantic-change`); store-key
  validation refusals via `StoreKeyError` ⊂ `ValueError` (`error-behavior`); `.store` /
  `image_data` read-only mapping. Cross-reference BC-GSEG-006/007 rather than restating them.
- **D-19:** Research does a **read-only grep of iof3D** (`/scratch/34_iof3d`) for usage the
  Phase-7 changes affect (`del`/`clear`/`pop` on the store, direct `DiskBackedImageStore` use,
  tile-id / key shapes, `.image_data` mutation). Findings shape BC-entry wording only; no
  iof3D edits (separate repo).

### Claude's Discretion
- Escape-test assertion style (directory snapshot vs sentinel), within D-11 step 3: the
  simplest test per route (insert/offload/load/delete/purge) that would fail if upstream
  containment regressed.
- Exception assertions: keep `ValueError` as pc2img's public contract in tests; whether one
  test additionally pins the GSEGUtils subtype is the planner's call.
- Plan/wave decomposition, provided: spikes are in research (D-04); the code review of the
  phase's own diff precedes the promotion (SC3, global Review Discipline); D-13 lands before
  the promotion; D-03 runs before the release PR merges.

### Folded Todos
- **`2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md`** — the core of the
  phase. Superseded in part: pin (→ D-01/D-02), step 3 `__delitem__` retention (→ D-08),
  per-finding fixes (→ D-11 triage). Close when Phase 7 completes.
- **`2026-09-25-phase-6-round-5-comment-and-test-hygiene.md`** — Phase-7 half (D-12). Close
  when Phase 7 completes.
- **`2026-09-30-phase-7-rtd-and-ruleset-hardening-round-4.md`** — all items (D-13, D-15).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### GSEGUtils 0.6 migration (upstream-authored)
- `~/gsd-workspaces/pchandler/.planning/handoffs/pc2img-migration-BC-GSEG-006.md` — **the
  pc2img-specific migration handoff**: withdrawn names, `purge`, `clear()` change, key rules,
  `.dat` containment, §3 checklist. Primary input for D-07..D-10. Re-derive its line numbers.
- `~/gsd-workspaces/pchandler/30_GSEGUtils/MIGRATION-v1.2.md` — canonical BC-GSEG-006/007
  write-up for 0.6.0 (with inline verifier).
- `~/gsd-workspaces/pchandler/.planning/MIGRATION-v1.2.md` — workspace index (which release
  carries which entry; names the BC-GSEG-006 parts that still live in MIGRATION-v1.0.md).
- `~/gsd-workspaces/pchandler/.planning/MIGRATION-v1.0.md` — prior-release BC-GSEG-006 parts.
- `~/gsd-workspaces/pchandler/.planning/handoffs/iof3d-store-key-contract.md` — iof3D's own
  handoff; context for D-19.

### Phase scope & prior decisions
- `.planning/ROADMAP.md` § Phase 7 — goal + SC1–SC5.
- `.planning/REQUIREMENTS.md` — DEP-05, BC-01.
- `.planning/phases/06-publication-hardening-downstream-migration-record/06-CONTEXT.md` —
  D-19 (second promotion), D-24 (Phase-7 split), D-25..D-29 (migration-record schema/timing),
  D-30 (owner checkpoints).
- `.planning/phases/06-publication-hardening-downstream-migration-record/06-SECURITY.md` —
  AR-07 / AR-08 (D-14).
- `.planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md`
  — finding list for the D-11 triage table, upstream residuals.
- `.planning/todos/pending/2026-09-25-phase-6-round-5-comment-and-test-hygiene.md` — D-12.
- `.planning/todos/pending/2026-09-30-phase-7-rtd-and-ruleset-hardening-round-4.md` — D-13, D-15.

### Spikes
- `.planning/spikes/MANIFEST.md` — spike rules + 001/004 definitions (D-04..D-06).
- `.planning/spikes/000-absorption-test/README.md` — absorption verdict, provenance-gate pattern,
  escape corpus.

### Migration record & release flow
- `.planning/MIGRATION-v0.11.md` — the record to finalise (D-18).
- `RELEASE.md` — promotion + back-merge procedure (D-16).
- `RULESETS.md`, `.github/scripts/ruleset_lib.py`, `.github/scripts/test_ruleset_lib.py` — D-15.
- `.readthedocs.yaml` — D-13.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- GSEGUtils 0.6.0 public API: `purge(key)`, `get_npy_path` / `get_meta_path` free functions,
  `is_valid_store_key`, `StoreKeyError` / `StoreContainmentError`.
- Spike 000's provenance gate (assert `GSEGUtils.__version__` + `self._get_npy_path`
  fingerprint == 0 inside the test process) — reuse for spikes and the re-lock check.
- Phase-5 escape corpus in `tests/test_image_store.py` (3 key spellings × 4 routes).

### Established Patterns
- pc2img's own pipeline only calls `add_image_to_store` on the store (`features/manager.py:73`);
  it never calls `del`/`clear`/`pop` — the D-08 semantic change hits external callers only.
- `extend_cache_path` sites: `tiled_generator.py:71,74,162,171`, `strategies/interpolation.py:203`.
- `DiskBackedImageStore.image_data` (legacy alias) returns `self.store`, annotated `dict[...]` —
  now a read-only `MappingProxyType` upstream.

### Integration Points
- `src/pc2img/image_cache/disk_backed_image_store.py` (override deletion, `purge` adoption).
- `src/pc2img/image_cache/disk_backed_image_data.py` (`LazyDiskCache` subclass — spike 001).
- `pyproject.toml` + `uv.lock` (D-01/D-02).
- `.github/scripts/check_publish_gate.py`, `preflight_ruleset_apply.py` (D-14).

</code_context>

<specifics>
## Specific Ideas

- Owner guideline (not a standing rule): don't fix in pc2img anything that should be fixed in
  GSEGUtils. Avoid hunting down difficult, unnecessary hardenings — the history of iterative
  fix loops is the reason for D-11.
- "Reproduce, don't read": the discuss-time 30-failure finding came from instantiating the
  fresh resolve, not from reading pins — research and verification should do the same.

</specifics>

<deferred>
## Deferred Ideas

- Permanent CI job that tests an unlocked/fresh dependency resolve (D-03 is one-shot only).
- Any pc2img-owned hardening that D-11 step 4 defers (recorded per finding in the plan's triage table).

### Reviewed Todos (not folded)
- **`2026-07-27-rrim-float32-scaling-invariant-guard.md`** — deferred past 0.11.0 (owner); it
  becomes a 0.12 BC entry. Retarget `resolves_phase` to the next milestone.
- **`2026-07-09-document-cuda11-vs-cuda12-selection-guidance.md`** — deferred; docs-only,
  unrelated to the release path.

</deferred>

---

*Phase: 07-gsegutils-0-6-adoption-0-11-0-release*
*Context gathered: 2026-10-01*
