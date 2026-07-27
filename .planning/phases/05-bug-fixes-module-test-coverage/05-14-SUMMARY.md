---
phase: 05-bug-fixes-module-test-coverage
plan: 14
subsystem: correctness
tags: [rrim, feature-name-dsl, cache-key, disk-cache, delete-ordering, gap-closure, round-2, bc-record]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: "the 05-13 round-1 gap fixes themselves (G1 dependencies_for overrides, G3 codec-pair purge) — both blockers closed here were INTRODUCED by that plan; also the 05-09 image_cache reparent onto GSEGUtils DiskBackedStore and the 05-01 synthetic_pcd fixture"
provides:
  - "G9 blocker fix: a z_factor of any magnitude or precision round-trips exactly through RRIMConfig.pack_feature_name(), which is both a public feature name and the cache key"
  - "Injective RRIM cache key — two configs differing beyond 6 significant figures can no longer share one cached raster"
  - "G10 blocker fix: a KeyError-raising DiskBackedImageStore delete is a genuine no-op, so it cannot destroy a raster another store over the same cache directory owns"
  - "BC-NOTES entries 12/13/14 (G11 request-time validation shift, G12 K pinhole refusal, G9 z token formatting) marked to carry into Phase 6 BC-01"
  - "COVERAGE.md — the reasoned no-external-API declaration the seal-time api-coverage gate requires"
affects: [phase-06-bc, rrim, feature-registry, image_cache]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A derived feature name that is also a cache key must be emitted in a shortest exactly-round-tripping form (repr for non-integers), never a fixed-precision general format — truncation silently makes the key non-injective"
    - "Emit-side formatter and parse-side grammar are ONE contract; both halves must change together or the round trip breaks in the other direction"
    - "A destructive override must delegate to the base for membership validation BEFORE touching the disk, keeping exactly one membership authority (no `if key in self` pre-check)"
    - "Characterization test over the currently-correct value set as the zero-churn guard for a cache-key formatting change"

key-files:
  created:
    - ".planning/phases/05-bug-fixes-module-test-coverage/COVERAGE.md - reasoned no-external-API declaration for the seal-time gate"
  modified:
    - "src/pc2img/features/rrim.py - _Z_FACTOR_RE widened with an optional exponent group; _format_number non-integer branch switched to repr(float(v)); RRIMConfig docstring records the grammar + emission contract"
    - "tests/test_rrim_features.py - 5 new G9 proving tests (round trip over 9 z values, injectivity, dependency chain, generate() end-to-end, token-stability characterization)"
    - "src/pc2img/image_cache/disk_backed_image_store.py - __delitem__ delegates to super() BEFORE unlinking; dead cache_dir guard removed; docstring rewritten to the corrected ordering"
    - "tests/test_image_store.py - _two_store_config helper + the two-store failed-delete proving test"
    - ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md - entries 12/13/14 + three summary-table rows"
    - ".planning/phases/05-bug-fixes-module-test-coverage/deferred-items.md - 05-14 section: 3 pre-existing lint/type findings + the 2 verified behavioral follow-up candidates"

key-decisions:
  - "Implemented BOTH halves of the owner-locked G9 fix (widen the grammar AND fix the formatter); neither half alone closes the gap — a regex-only fix leaves the 6-sig-fig truncation and the non-injective key, a formatter-only fix emits exponent tokens the grammar still rejects"
  - "Kept the shortest-round-trip form (repr) rather than raising %g precision: repr is byte-identical for every currently-correct z (proven by a 14-value characterization test), so cache-key churn is paid only where the key was already WRONG"
  - "Delegated to super() first rather than adding an `if key in self` pre-check, preserving a single membership authority in the base store"
  - "Committed each task as ONE atomic commit (test + fix together) rather than a RED commit followed by a GREEN commit, so every commit in the history is green — the RED evidence is recorded below instead of as a red commit"
  - "Left the non-finite z_factor round-trip break and the <key>.dat delete residue unfixed and logged as follow-ups: both are outside the locked G9/G10 scope and both were verified by running code, not by reading"

patterns-established:
  - "Reproduce-then-fix-then-reproduce: every claim in this plan (both defects, both follow-up candidates, the byte-identical-token rationale) was established by instantiating the failing value, not by reading the diff"

requirements-completed: [BUG-05]

# Coverage metadata — one entry per closed round-2 gap (G9..G12)
coverage:
  - id: G9
    description: "A z_factor below 1e-4 and a high-precision fractional z_factor both round-trip exactly through the derived pack-feature name; distinct z values produce distinct names (injective cache key); every currently-valid z still emits a byte-identical token"
    requirement: BUG-05
    verification:
      - kind: unit
        ref: "tests/test_rrim_features.py::test_pack_feature_name_round_trips_z_factor"
        status: pass
      - kind: unit
        ref: "tests/test_rrim_features.py::test_pack_feature_name_is_injective_for_nearby_z"
        status: pass
      - kind: unit
        ref: "tests/test_rrim_features.py::test_rrim_dependency_chain_resolves_for_sub_1e4_z"
        status: pass
      - kind: integration
        ref: "tests/test_rrim_features.py::test_generate_rrim_small_z_end_to_end"
        status: pass
      - kind: unit
        ref: "tests/test_rrim_features.py::test_z_factor_token_unchanged_for_currently_valid_values"
        status: pass
    human_judgment: false
  - id: G10
    description: "A KeyError-raising store delete leaves the on-disk codec pair intact and both the fresh store and the OWNING store still serve the key; a successful delete still purges the pair (round-1 G3 preserved)"
    requirement: BUG-05
    verification:
      - kind: integration
        ref: "tests/test_image_store.py::test_failed_delete_preserves_codec_pair_and_both_stores"
        status: pass
      - kind: integration
        ref: "tests/test_image_store.py::test_delete_purges_on_disk_codec_pair"
        status: pass
      - kind: integration
        ref: "tests/test_image_store.py::test_overwrite_does_not_leave_stale_on_disk_raster"
        status: pass
      - kind: unit
        ref: "tests/test_image_store.py::test_delete_absent_key_does_not_raise"
        status: pass
    human_judgment: false
  - id: G11
    description: "The RRIM request-time validation shift (timing AND exception type) is recorded in the phase BC record and marked to carry into Phase 6 BC-01"
    requirement: BUG-05
    verification:
      - kind: artifact
        ref: ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md#12"
        status: pass
    human_judgment: false
  - id: G12
    description: "The PerspectiveProjection non-pinhole / non-3x3 K refusal is recorded in the phase BC record with concrete migration guidance and marked to carry into Phase 6 BC-01"
    requirement: BUG-05
    verification:
      - kind: artifact
        ref: ".planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md#13"
        status: pass
    human_judgment: false

metrics:
  duration: 15min
  completed: 2026-07-27
  tasks: 3
  files: 6

status: complete
---

# Phase 5 Plan 14: Round-2 Gap Closure (G9–G12) Summary

Closed the two blocker-severity correctness defects that the round-1 gap plan **05-13 itself introduced** — a `z_factor` that could not round-trip through the RRIM cache key, and a store delete that destroyed another store's raster before validating membership — plus the three BC-record entries and the no-external-API coverage declaration.

## What Shipped

| Gap | Severity | Fix | Commit |
|-----|----------|-----|--------|
| G9 | blocker | `_Z_FACTOR_RE` widened with an optional exponent group; `_format_number` non-integer branch → `repr(float(v))` | `5dbd93e` |
| G10 | blocker | `__delitem__` delegates to `super()` before unlinking; dead `cache_dir` guard removed | `f776011` |
| G11 + G12 + G9 record | minor | BC-NOTES entries 12/13/14 + summary-table rows; `COVERAGE.md` | `eeb0e5f` |

## 1. Both blockers were introduced by the round-1 gap plan, and only a review OF that diff caught them

This is the finding that matters more than either fix.

- **G9** is a follow-on of 05-13's **G1** fix. G1 added `dependencies_for` overrides so `FeatureRegistry.match` could derive the RRIM pack dependency *without constructing the feature*. That made `RRIMConfig.pack_feature_name()` — previously an internal string — into a name the registry must **re-parse**. The emit-side formatter and the parse-side grammar had never been each other's inverse; G1 is what made that mismatch reachable.
- **G10** is a follow-on of 05-13's **G3** fix. G3 added the on-disk codec-pair purge to `__delitem__` and placed the `unlink` calls *before* `super().__delitem__(key)`, inverting the base store's no-side-effect-on-`KeyError` contract.

Neither is reachable by the 135-test suite that shipped with 05-13: the G1 end-to-end RRIM tests all use default-ish `z`, and no test exercised a cross-store delete. **CI on PR #12 was green with both defects present.** They surfaced only from `/code-review 1295c2b high` — a review of the 05-13 diff itself, which no GSD review had covered, because GSD's re-review loop lives only inside `/gsd-code-review --fix --auto` and the `--gaps` path skips it. This is the concrete instance behind the global *gap-closure-gets-its-own-review* rule.

## 2. Both defects were worse than 05-UAT.md recorded

Re-reproduced at HEAD before any code changed:

**G9 — the truncation also made the cache key non-injective.** The UAT record covered the sub-1e-4 refusal (`z=1e-05` → `rrim_pack_(range,r16,d8,z1e-05)` → `ValueError: Unknown RRIM option 'z1e-05'`) and the silent drift (`1.2345678` → `1.23457`). Beyond that record: `z=1.2345678` and `z=1.2345681` **both emit the identical name** `rrim_pack_(range,r16,d8,z1.23457)`, so two distinct configs share one cached raster and a caller can receive a raster computed under parameters it never requested. Verified before the fix (`collide: True`) and refuted after (`test_pack_feature_name_is_injective_for_nearby_z`).

**G10 — live data loss in the OWNING store, not merely a stale-cache-recovery concern.** The UAT record asserted that a fresh store `C` could no longer recover the key. Beyond that record: store **B**, which *owns* the raster, cleared its in-memory reference on offload and re-materializes through `_load_entry` reading the codec pair — so after `del A["range"]` raises `KeyError`, **B itself raises `KeyError` for its own key**. Verified before the fix (`C fails KeyError`, `B fails KeyError`) and refuted after; the proving test asserts the stronger property.

## 3. Zero cache-key churn, proven not asserted

The owner-locked shape (widen the grammar **and** switch to shortest-round-trip emission) was chosen because `repr` is byte-identical to the old `%g` output for every `z` that already encoded correctly. That is now a live test, not a claim: `test_z_factor_token_unchanged_for_currently_valid_values` pins 14 values (0.5, 2.5, 0.0001, 0.001, 0.01, 0.1, 0.25, 0.75, 1.5, 1.0, 2.0, 10, 100, 1234567) to their exact tokens **and** to their exact full pack names. It carried no xfail marker — it passed before the fix and after, which is precisely what makes it the churn guard.

## Deviations from Plan

**None.** All three tasks executed exactly as written, including both halves of the owner-locked G9 decision and the three-statement `__delitem__` body. No shipped 05-01..05-13 PLAN file was touched.

The one procedural choice worth naming (recorded above as a key decision, not a deviation): each task was committed as **one atomic commit** containing both its proving tests and its fix, rather than a separate RED commit followed by a GREEN commit. The plan's D-12 requirement is that the tests be authored and confirmed RED *before* the source changes — which they were, with the evidence below — and a separate RED commit would have left a commit in the history whose suite is red, breaking the project's green-at-every-commit posture.

## TDD Gate Compliance

Both code fixes landed xfail-first (D-12). Evidence, in execution order:

| Task | RED (before source change) | GREEN (after) |
|------|---------------------------|---------------|
| 1 (G9) | `32 passed, 6 xfailed` — 3 `pytest.param` marks (1e-06, 1e-05, 1.2345678) + 3 whole-test marks; **0 xpassed**, no collection errors | `38 passed`, 0 xfail, 0 xpass |
| 2 (G10) | `7 passed, 1 xfailed` | `29 passed` (incl. `test_disk_backed_image_data.py`), 0 xfail |

The RED runs were confirmed as *xfail*, not error/collect-failure, before either source file was touched. Markers were removed only after the fix landed; the suite carries **0 residual xfail from this plan**.

## Verification Results

| Gate | Result |
|------|--------|
| `pytest tests/test_rrim_features.py -q` | 38 passed, 0 xfail, 0 xpass |
| `pytest tests/test_image_store.py tests/test_disk_backed_image_data.py -q` | 29 passed |
| `pytest tests/ -q` | **162 passed**, 0 failed, 0 xfail (floor was ≥ 135) |
| `pytest --cov=pc2img --cov-branch --cov-fail-under=55 -q` | **61.63%** — CI floor of 55 holds |
| grammar + formatter assertion chain | exits 0 (`z1e-05`, `z1E-05`, `z1e+20`, `z1.2345678` accepted; `z0.5`, `z1`, `z-1`, `z+2.5` still accepted) |
| `grep -c 'format(value' rrim.py` | 0 — the fixed-precision call is gone |
| injectivity assertion | exits 0 |
| dependency-chain assertion | exits 0 (`rrim_(range,z1e-05)` → `['range', 'rrim_pack_(range,r16,d8,z1e-05)']`) |
| `__delitem__` body ordering (`inspect.getsource`) | `super().__delitem__` precedes the first `unlink(` |
| `' in self' not in body` | exits 0 — single membership authority preserved |
| `grep -c 'self.cache_dir' disk_backed_image_store.py` | 0 — dead guard gone, docstring does not reintroduce the token |
| `ruff check --ignore E402,C901,B008` + `ruff format --check` on all 4 touched code files | clean |
| BC-NOTES / COVERAGE.md gates | 3 × `## 1[234].`, 3 × `Carry into Phase 6 BC-01`, 3 × table row, `COVERAGE.md` present |

## Follow-Up Candidates (both verified by running code, both deliberately out of scope)

Logged in full in `deferred-items.md` § *From 05-14*:

1. **`<key>.dat` residue survives a successful delete.** The override purges only `.npy` + `.meta.json`; `offload_image_data_to_disk` (`pickle_container=True`) also writes an entry-level `<key>.dat`. Verified: after `del s["range"]` the cache dir holds `['range.dat']`, and a fresh store over that dir registers **zero** keys — the base `__init__` re-scans `*.npy`, so a lone `.dat` is never re-adopted. **Disk residue, not a stale-serve path.**
2. **A non-finite `z_factor` still breaks the round trip.** `_validate_config` accepts `float("inf")` (`inf > 0` is True) and the shortest-round-trip formatter emits `zinf`, which the widened `_Z_FACTOR_RE` still rejects. Verified: `RRIMConfig(z_factor=float("inf")).pack_feature_name()` → `rrim_pack_(range,r16,d8,zinf)` → `ValueError: Unknown RRIM option 'zinf'`. The G9 owner decision covered exponent notation and precision, **not** finiteness; a `math.isfinite` check was deliberately not added.

Also logged there: three pre-existing findings on the touched files, all confirmed outside this plan's diff hunks (`rrim.py` 43–104, `disk_backed_image_store.py` 70–92) — one pyright `reportReturnType` in `_parse_rrim_component`, one pyright `reportArgumentType` on the store's `factory=` parameter-name mismatch, and the `B008` on the store's `LazyDiskCacheConfig()` default deferred at 04-04.

## Known Stubs

None. No placeholder, hardcoded-empty, or TODO/FIXME construct was introduced; every new symbol is a live assertion or a live code path.

## BC / Phase-6 (BC-01) Additions

`05-BC-NOTES.md` gains entries **12–14**, each with the established **Symbol** / **Old → new** / **Migration note** schema and an explicit `**Carry into Phase 6 BC-01:** yes.` line, plus matching summary-table rows 12–14:

- **12 — RRIM name validation moved to request time** (BREAKING, surface only). `FeatureRegistry.match` now calls `dependencies_for` on every matched path, and `FeatureManager.request` calls `match` on user-supplied names, so a malformed RRIM name in a batch raises a bare `ValueError` from inside `request()` and aborts the whole batch before any feature computes. **Both the timing and the exception type shifted** — callers catching `RegistryLookupError`, or wrapping only the compute phase, will not catch it. Same class as entry 11.
- **13 — `PerspectiveProjection` refuses a non-3×3 or non-pinhole `K`** (BREAKING). Intentional: a non-pinhole `K` desyncs the perspective divisor sign from the behind-camera cull, mislocating points instead of culling them. Migration: normalize `K` by `K[2,2]`; pass `K` and `[R|t]` separately rather than a composed `P`. Skew in `K[0,1]` is still accepted.
- **14 — RRIM `zF` token: grammar widened + shortest-round-trip emission** (ADDITIVE + BREAKING, narrow). Records the byte-identical-for-currently-correct-values rationale, both closed defects (unparseable sub-1e-4 name; non-injective cache key), and the migration note that a persisted truncated `z1.23457` entry degrades to an inert cache miss.

`COVERAGE.md` declares, with reasoning, that Phase 5 integrates no external API — the "Store API-Gap Analysis" the deterministic detector fires on refers to the in-process GSEGUtils `DiskBackedStore` base-class member surface, not a service. It is deliberately not padded with a fabricated endpoint matrix.

## Next Step (orchestrator, not a task here)

Per the global review-discipline rule this repo learned the hard way: **this gap-closure diff gets its own review before the phase re-verifies** — `/gsd-code-review 05 --files src/pc2img/features/rrim.py src/pc2img/image_cache/disk_backed_image_store.py tests/test_rrim_features.py tests/test_image_store.py`, escalating to `/code-review <base> high` given that both fixes touch a public grammar and a cache-key contract. A phase is not closeable on a review → fix → verify sequence where nothing looked at the fix.

## Self-Check: PASSED

- SUMMARY present at `.planning/phases/05-bug-fixes-module-test-coverage/05-14-SUMMARY.md`
- `COVERAGE.md` present in the phase directory
- All 3 task commits present in git history: `5dbd93e`, `f776011`, `eeb0e5f`
- Full suite: 162 passed, 0 failed, 0 residual xfail from this plan; coverage 61.63% ≥ 55
