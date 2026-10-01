# Phase 7: GSEGUtils 0.6 Adoption & 0.11.0 Release - Research

**Researched:** 2026-10-01
**Domain:** Python library dependency migration (GSEGUtils 0.5.3 -> 0.6.0 store contract), test re-pinning, migration-record finalisation, protected PyPI release flow
**Confidence:** HIGH for everything measured by running code against the released 0.6.0 wheel (spikes 001/004); MEDIUM for release-path edit points (read, existing tests run, live GitHub/PyPI state not exercised); the tiled re-generation race (section "Surprise") is HIGH on cause and reproduction, but the fix decision is the owner's.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Folded Todos (in scope)

- **`2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md`** — the core of the
  phase. Superseded in part: pin (→ D-01/D-02), step 3 `__delitem__` retention (→ D-08),
  per-finding fixes (→ D-11 triage). Close when Phase 7 completes.
- **`2026-09-25-phase-6-round-5-comment-and-test-hygiene.md`** — Phase-7 half (D-12). Close
  when Phase 7 completes.
- **`2026-09-30-phase-7-rtd-and-ruleset-hardening-round-4.md`** — all items (D-13, D-15).

### Claude's Discretion

- Escape-test assertion style (directory snapshot vs sentinel), within D-11 step 3: the
  simplest test per route (insert/offload/load/delete/purge) that would fail if upstream
  containment regressed.
- Exception assertions: keep `ValueError` as pc2img's public contract in tests; whether one
  test additionally pins the GSEGUtils subtype is the planner's call.
- Plan/wave decomposition, provided: spikes are in research (D-04); the code review of the
  phase's own diff precedes the promotion (SC3, global Review Discipline); D-13 lands before
  the promotion; D-03 runs before the release PR merges.

### Deferred Ideas (OUT OF SCOPE)

- Permanent CI job that tests an unlocked/fresh dependency resolve (D-03 is one-shot only).
- Any pc2img-owned hardening that D-11 step 4 defers (recorded per finding in the plan's triage table).

### Reviewed Todos (not folded)
- **`2026-07-27-rrim-float32-scaling-invariant-guard.md`** — deferred past 0.11.0 (owner); it
  becomes a 0.12 BC entry. Retarget `resolves_phase` to the next milestone.
- **`2026-07-09-document-cuda11-vs-cuda12-selection-guidance.md`** — deferred; docs-only,
  unrelated to the release path.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEP-05 | pc2img runs against GSEGUtils >= 0.6 with its `DiskBackedImageStore` containment override removed (containment enforced upstream), every escape route re-pinned by a test (REQUIREMENTS.md line 16) | Spike 001/004 (override is orphaned, removal blast radius = 12 tests in one file), Migration Checklist (re-derived line numbers), Measured Behaviour tables (escape corpus x 9 routes, all refused with `StoreKeyError`), "Escape-route re-pin pattern", D-03 unlocked-wheel recipe, lock re-resolve evidence |
| BC-01 (finalise) | Structured, GSD-consumable breaking-change / migration record of pc2img's own public API/behaviour changes (REQUIREMENTS.md line 54) | "Migration record (BC-01) - material for the Phase-7 entries" (measured exception types, key verdicts, `del`/`purge` semantics, `.store` read-only), verifier run results (25 entries OK on locked env; fails on unmodified tree + 0.6.0), stale-text list for BC-P2I-002/012/017 |
</phase_requirements>

## Summary

**The phase is a working-path break, and the migration itself is small, mechanical and fully validated.** On the released GSEGUtils 0.6.0 wheel the tree as shipped fails 30 of 286 tests (reproduced: 26 with `AttributeError: 'super' object has no attribute '_get_npy_path'` at `disk_backed_image_store.py:120`, 4 with `StoreKeyError` raised by the mapping setter). With the three path-builder overrides and the `__delitem__` override deleted and `add_image_to_store`'s overwrite switched to `purge`, **12 tests fail, all in `tests/test_image_store.py`: 5 are pure renames to the public free functions `get_npy_path`/`get_meta_path`, 7 are semantic rewrites** (`del` no longer unlinks; the mapping setter refuses an escaping key at set time, so a Phase-5 test can no longer seed one). Every other test passes (274 of 286), including the five RRIM end-to-end tests and all realistic-feature-name round trips. Nothing in `src/` other than the store needs to change. [VERIFIED: spike 004 runs, this session; see `.planning/spikes/004-blast-radius-gsegutils-0.6.0/README.md`]

**Spike verdicts (both written to `.planning/spikes/MANIFEST.md`):** 001 orphaned-override-hunt **VALIDATED** — `_get_npy_path`, `_get_meta_path` and the `_assert_within_cache_dir` helper are orphans (the `super()` calls are dangling), `__delitem__` is the one override upstream still reaches (via `pop`/`clear`) and is superseded by `purge`; `DiskBackedImageData` overrides no `LazyDiskCache` buffer hooks and its reload registration still works; the five `extend_cache_path` sites are unchanged in position and only refuse hostile folder names. 004 blast-radius **VALIDATED** — as above. Delta vs spike 000 (phase-14 dev tree): the `.dat` symlink-follow hole spike 000 found is **closed** on the released wheel; planted `.npy.tmp`/`.meta.json.tmp` symlinks are **still followed** (documented non-adversarial residual); an entry carrying its own out-of-cache `cache_path` still offloads there.

**Three findings the discuss step did not have, each needing a plan-level decision:**

1. **Surprise (release-relevant): a second `TiledPointCloudImageGenerator.generate()` on the same instance (>= 2 tiles, `n_jobs >= 2`) fails on 0.6.0** with `BrokenProcessPool`/`TerminatedWorkerError`, and passes on 0.5.3. Root cause is upstream (0.6.0 writes every `.dat` through one fixed `<key>.dat.tmp` name; each loky worker unpickles *every* tile's store because `self._process_tile` is a bound method, so N processes race one temp name), reproduced with GSEGUtils alone (11/12 rounds fail on 0.6.0, 0/12 on 0.5.3) and confirmed by intervention (shipping only the tile's own generator to each worker makes it pass 3/3). The existing suite is blind to it (no `n_jobs >= 2` tiled test). Not caused by the migration. See "Surprise" and Open Question 1.
2. **`pchandler >= 2.1.1` and `GSEGUtils 0.6.0` both require `numpy >= 2.2, < 2.4`**, so the re-lock moves numpy 2.0.2 -> 2.2.6 (plus numba/llvmlite) and — because pchandler 2.1.1 trimmed its `cuda11`/`cuda12` extras to `cudf`+`cuspatial`+`geopandas` — **shrinks `uv.lock` from 193 to 137 packages** (the cuml/cuproj/dask-cudf RAPIDS stack disappears). pc2img's own `numpy ~= 2.0` floor then misstates the effective range. [VERIFIED: PyPI metadata + `uv lock` in a scratch copy] See Open Question 2 and the BC material.
3. **`BC-P2I-017` in the shipped-in-draft migration record is now false** ("nesting under the cache directory is still allowed"): nested keys are refused upstream. Scalar-field names containing `/`, `\`, `:` or ending in `.` worked on 0.5.3 (measured) and now raise `StoreKeyError` at `generate()`.

**Primary recommendation:** Implement the migration exactly as D-07..D-10 prescribe (delete 3 overrides + `__delitem__`, `add_image_to_store` -> keep one containment-first `get_npy_path(self.cache_dir, key)` line, shape check, `purge` on overwrite), re-pin escape routes with whole-tree directory-snapshot tests, rewrite the 7 semantic tests, finalise the BC record from the measured values below, and put the loky tiled race in front of the owner **before** the plan is locked — it is the only item that can make "pc2img runs on GSEGUtils >= 0.6" false for a supported flow.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Store-key validation + path containment (lexical, resolved) | GSEGUtils (`paths.py`, `DiskBackedStore`) | pc2img `DiskBackedImageStore` (propagates `StoreKeyError`) | D-09/D-10: containment is upstream; pc2img adds no pre-validation code |
| Delete verb (`purge`: drop key + unlink six key-derived artefacts, detach finalizer) | GSEGUtils `DiskBackedStore.purge` | pc2img `add_image_to_store` overwrite path | D-08: delete semantics belong upstream; pc2img only calls it |
| Overwrite-preserving legacy alias `add_image_to_store` | pc2img store wrapper | — | Legacy API the `FeatureManager` depends on; shape check (`_assert_image_shape`) is pc2img's rule |
| `.dat` memmap write / reload (`LazyDiskCache`) | GSEGUtils | — | pc2img overrides no buffer hook (spike 001 §A); the tmp-name race (§E) lives here |
| Per-tile fan-out, worker pickling | pc2img `TiledPointCloudImageGenerator` + joblib/loky | GSEGUtils `__getstate__/__setstate__` | The race is the *interaction* of both tiers |
| Migration record, verifier | `.planning/MIGRATION-v0.11.md` (planning tier) | — | Read by downstream from the branch, stripped from `main` |
| Release gating (publish gate, ruleset preflight, RTD) | CI / release infrastructure (`.github/`, `.readthedocs.yaml`) | owner account actions (D-17) | D-13..D-17 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GSEGUtils | `~= 0.6.0` (0.6.0, uploaded 2026-08-17) | store contract, `purge`, free path builders | D-01; `pchandler 2.1.1` pins the same `GSEGUtils~=0.6.0` [VERIFIED: pypi.org/pypi/pchandler/2.1.1/json `requires_dist`] |
| pchandler | `>= 2.1.1, ~= 2.1` (2.1.1, uploaded 2026-08-25) | `PointCloudData`, filters, geometry | D-02 |
| numpy | resolves to 2.2.6 under the new lock (GSEGUtils 0.6.0 and pchandler 2.1.1 both require `>=2.2,<2.4`) | arrays | transitive floor [VERIFIED: PyPI `requires_dist`, `uv lock` diff] |
| pytest | `~= 9.1` (locked) | tests | existing |
| uv | 0.11.26 (local) | lock/build/run | existing project tool |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psutil | `~= 7.0` (new transitive requirement of GSEGUtils 0.6.0; already present in the old lock — the re-lock added no package) | GSEGUtils internals | none directly |
| ruff | `~= 0.15` (dev group) | lint/format (`tests/test_hygiene.py` shells it) | every plan's lint step |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `GSEGUtils ~= 0.6.0` | `>= 0.6, < 1.0` (the todo's text) | rejected by D-01 (a pre-1.0 minor can remove surface); one-way once published |
| deleting `__delitem__` + `purge` (D-08) | keep `__delitem__` unlink | rejected by D-08; also would make upstream `clear()`/`pop` delete files (spike 001 §A) |

**Installation (the change set, not run in the tree):**
```bash
# pyproject.toml [project].dependencies
#   "pchandler >= 2.1.1, ~= 2.1",
#   "GSEGUtils ~= 0.6.0",
uv lock && uv lock --check
```

**Version verification:** `GSEGUtils` 0.6.0 (wheel + sdist, 2026-08-17, not yanked), `pchandler` 2.1.1 (2026-08-25); latest on PyPI for GSEGUtils is 0.6.0 — there is no 0.6.1. [VERIFIED: pypi.org JSON, this session]

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| GSEGUtils | PyPI | 0.6.0 published 2026-08-17 (0.5.2 on 2026-06-24) | unknown to the seam | github.com/gseg-ethz/GSEGUtils (PyPI `project_urls`; seam saw none) | SUS (`unknown-downloads`, `no-repository`) | Already installed and hash-locked in `uv.lock` (0.5.3); first-party ETH GSEG library named in the project constraints. Not a new package — only a version bump. Flagged per protocol; owner confirms at plan review whether the bump needs a `checkpoint:human-verify` (recommended: no, covered by D-17-style owner approval of the pin change). |
| pchandler | PyPI | 2.1.1 published 2026-08-25 | unknown to the seam | github.com/gseg-ethz/PCHandler (PyPI `project_urls`) | SUS (same reasons) | Same as above. |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** GSEGUtils, pchandler — both are the owner's own sibling libraries (CLAUDE.md "Dependencies"), already in the lock; the seam's SUS comes from missing download/repo signals, not from a registry anomaly. No new package enters the lock (diff: added = none).

*Both names are `[ASSUMED]`-free: they come from the project's own CLAUDE.md and pyproject, and PyPI JSON confirms the `gseg-ethz` project URLs.*

## Architecture Patterns

### System Architecture Diagram (data flow through the store, post-migration)

```
FeatureManager.submit(name, raster)
        |
        v
DiskBackedImageStore.add_image_to_store(name, raster)           [pc2img]
        |-- get_npy_path(cache_dir, name) --StoreKeyError/StoreContainmentError--> caller (ValueError family)
        |-- _assert_image_shape(raster) ----AssertionError (type pinned)---------> caller
        |-- name in self ? --yes--> self.purge(name) --------------------------> [GSEGUtils]
        |                              validate key -> PID guard -> existence -> detach finalizer(s)
        |                              -> refuse foreign/aliased symlink targets -> unlink 6 artefacts
        |                              raises: KeyError / StorePurgeRefusedError(RuntimeError) /
        |                                      StorePurgeIncompleteError(OSError) / StoreKeyError
        '-- add_data_to_store(name, raster) --> validate key (again) -> factory(DiskBackedImageData,
                 cache_path=get_npy_path(...)) -> LazyDiskCache._convert_to_memmap
                 writes <key>.dat.tmp -> chmod -> os.replace -> <key>.dat      [GSEGUtils]
                                                   ^
   loky worker unpickle: DiskBackedStore.__setstate__ -> _load_entry -> same <key>.dat.tmp  (RACE, see Surprise)
```

### Recommended end state of the store module (target of D-08/D-09)

Keep: `__init__` (None-sentinel config), `add_image_to_store`, `image_data` (annotation -> `Mapping[...]`), `offload`, `offload_image_data_to_disk`. Delete: `_assert_within_cache_dir`, `_get_npy_path`, `_get_meta_path`, `__delitem__`, the `pathlib.Path` import. Restate the class docstring's threat model once (D-09). The simulated end state is `.planning/spikes/001-orphaned-override-hunt/target_store.py`; a runnable prototype overlay of the whole `src/` tree (outside the repo) produced the 12/274 result and a green `uv build` + unlocked-wheel run.

### Pattern 1: containment-first, then shape, then purge-on-overwrite
**What:** keep exactly one containment statement via the public free function so key refusal still precedes the shape check; let upstream raise.
**When to use:** `add_image_to_store`. **Alternative (D-10 literal, no pre-check):** drop that line; the only behavioural difference is a double-fault input (escaping key *and* bad shape) raising `AssertionError` instead of `StoreKeyError` (measured, spike 001 §S9) — see Open Question 3.
```python
# Source: measured prototype, .planning/spikes/001-orphaned-override-hunt/target_store.py
from GSEGUtils.lazy_disk_cache import DiskBackedStore, LazyDiskCacheConfig, get_npy_path

def add_image_to_store(self, img_name, img_data, *, enable_caching_override=None,
                       automatic_offloading_override=None, purge_disk_on_gc_override=None) -> None:
    get_npy_path(self.cache_dir, img_name)   # key / containment refusal FIRST (StoreKeyError, a ValueError)
    _assert_image_shape(img_data)            # AssertionError, type unchanged
    if img_name in self:
        self.purge(img_name)                 # validates before mutating; detaches finalizer
    self.add_data_to_store(img_name, img_data, enable_caching_override=...,
                           automatic_offloading_override=..., purge_disk_on_gc_override=...)
```

### Pattern 2: escape-route re-pin by whole-tree snapshot (Claude's discretion, D-11 step 3)
**What:** assert that the *entire* `tmp_path` tree (cache dir **and** everything outside it) is unchanged after each refused route; this fails for any file written anywhere, not one sentinel name (the weakness of review-r3 WR-01).
```python
import pytest
from GSEGUtils.lazy_disk_cache import StoreKeyError   # `except ValueError` stays the public contract

def _tree(root):  # name -> bytes, for every file and dir under root
    return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else None) for p in root.rglob("*")}

@pytest.mark.parametrize("spelling", ["parent_segment", "absolute", "embedded_traversal"])
@pytest.mark.parametrize("route", ["add", "setitem", "add_then_offload", "purge", "getitem", "add_data"])
def test_escaping_key_refused_and_nothing_written_anywhere(tmp_path, spelling, route): ...
    # build store on tmp_path/"cache", create tmp_path/"victim.npy" AND (cache/"a").mkdir() (review-r3 IN-02),
    # snapshot = _tree(tmp_path); with pytest.raises(ValueError): <route>(key); assert _tree(tmp_path) == snapshot
```
All 27 cells (3 spellings x 9 routes) refused with `StoreKeyError`, tree unchanged — [VERIFIED: spike 001 §S1, run output]. Whether one test additionally pins `StoreKeyError`/`StoreContainmentError` is the planner's call (`StoreKeyError`'s MRO is `StoreKeyError > ValueError > Exception`, `StoreContainmentError > StoreKeyError`).

### Anti-Patterns to Avoid
- **Re-creating the unlink on another dunder** (handoff §2e): `MutableMapping` builds `pop`/`popitem`/`clear` from `__delitem__`; spike 001 §A shows upstream `pop`/`clear` do `del self[key]`.
- **Keeping a pc2img pre-validation layer** around `StoreKeyError` (D-10).
- **Planning vocabulary in shipped text**: `tests/test_hygiene.py` fails the suite on `D-08`, `BC-01`, `SC1`, `phase 7`, `gap-closure`, `review-r3-...`, `.planning/`, `RESEARCH.md` in any git-tracked non-planning file, tests and docstrings included. [VERIFIED: tests/test_hygiene.py:165-195]
- **Writing to the tree during research-style probes**: all spike harness files live under `.planning/spikes/`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Key/path containment | any pc2img path guard | `GSEGUtils.lazy_disk_cache.get_npy_path/get_meta_path`, `is_valid_store_key`, `StoreKeyError` | all 27 corpus cells refused upstream; resolved-layer symlink case covered (`StoreContainmentError`) |
| Deleting a key's files | `unlink()` on a dunder or helper | `DiskBackedStore.purge(key)` | removes six artefacts incl. `.dat`, detaches finalizer (ABA), validates before mutating, refuses foreign symlink targets |
| Test directory snapshots | ad-hoc sentinel names | a `_tree(tmp_path)` dict comparison | catches any stray file |
| Tmp-dir isolation in tests | per-test `tempfile` fiddling | one autouse fixture `monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))` | `review-r4-15a5c4928dc8`; measured 18 leaked `tmp*` entries per run (reproduced) |

**Key insight:** every defect class the 17 Phase-5 gap rounds chased in the override (ordering, symlinks, setter, ABA) now has an upstream owner and an upstream test suite; pc2img's job shrinks to calling the verbs and pinning *its own* contract.

## Runtime State Inventory

(Dependency migration + code deletion; included because deleting the unlink changes what survives on disk.)

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | On-disk cache written by pc2img on **0.5.3** (`.npy` + `.meta.json` codec + `.dat`) is **adopted and served unchanged** by 0.6.0 (round trip measured, `schema_version: 1`, `lazy_disk_cache_class: DiskBackedImageData`). iof3D keeps durable caches (`purge_disk_on_gc=False`, `src/iof3D/v2/tasks/generate_tile_features.py:265,282`). | None (no on-disk-format BC). Cache dirs holding keys the new rule refuses (`a/b`-style nested subdirs, names with `:`/trailing `.`): `__init__` rescan refuses to track them upstream (D-09 in GSEGUtils); not measured here — note in BC |
| Live service config | Release PR #15 `chore(main): release 0.11.0` open (author `app/gseg-release-please`); `main` at `20ef688`; GitHub rulesets 24237564/24244420 (Phase-6 record); PyPI trusted publisher and `pypi` environment **not yet created** (D-17 owner checkpoint) | owner checkpoints just before the release-PR merge |
| OS-registered state | None — verified: no scheduled task/launchd/systemd unit references pc2img (nightly ancestry check is a GitHub workflow) | none |
| Secrets/env vars | None renamed. `RELEASE_APP_*`, `RULESET_APP_*` unchanged (RELEASE.md) | none |
| Build artifacts | `uv.lock` (re-resolved: GSEGUtils 0.5.3->0.6.0, pchandler 2.1.0->2.1.1, numpy 2.0.2->2.2.6, numba 0.60.0->0.61.2, llvmlite 0.43.0->0.44.0, 56 RAPIDS packages dropped); `.venv` (stale 0.5.3 until `uv sync`); `docs/_build/` (gitignored, contains stale HTML naming `_get_npy_path`); `src/pc2img/_version.py` generated | `uv lock` + `uv sync`; re-verify provenance after sync |

## Common Pitfalls

### Pitfall 1: trusting a cached 0.5.x (the lock hides the break)
**What goes wrong:** the locked env stays green (286 passed) while a plain `pip install` of the built wheel resolves 0.6.0 and fails 30 tests.
**How to avoid:** D-02 verification (`GSEGUtils.__version__ == "0.6.0"` **and** `grep -c 'self\._get_npy_path' ... == 0`) after the re-lock, and the D-03 unlocked-wheel run (recipe below, prototyped: wheel in site-packages, numpy 2.3.5 / pydantic 2.13.5 resolved, 12 failures = the not-yet-rewritten tests).
**Warning signs:** `.venv` still shows `gsegutils 0.5.3` after editing `pyproject.toml`.

### Pitfall 2: the mapping setter now refuses at set time
**What goes wrong:** the Phase-5 tests seed an escaping key via `store[key] = DiskBackedImageData(...)`, expecting `del` to refuse; the *setter* now raises `StoreKeyError`, outside any `pytest.raises` (4 of the 30 discuss-time failures).
**How to avoid:** rewrite those four tests as "setter refuses and the key is not tracked" (WR-04 of round 3 is thereby resolved upstream).

### Pitfall 3: `del store[k]` re-adopts on the next read
**What goes wrong:** for an *offloaded* key, `del` then `store[k]` succeeds again (measured: re-adopted from disk; a fresh store tracks it). A test or BC claim of "del removes the key" is false.
**How to avoid:** assert `purge` for removal; assert `del` drops tracking only.

### Pitfall 4: `purge` refusals are a different exception family
**What goes wrong:** `StorePurgeRefusedError` (RuntimeError family: foreign artefact, aliased artefact, wrong process) and `StorePurgeIncompleteError` (**OSError**) are not `ValueError`/`KeyError`. `add_image_to_store`'s overwrite can now raise them: (a) a symlinked adopted entry whose link target is outside the cache dir -> `StorePurgeForeignArtefactError` (measured); (b) overwrite from a process other than the store's constructor -> `StorePurgeRefusedError` (measured via fork and via loky: `_owner_pid` travels in the pickle).
**How to avoid:** test (a); document (b) in the BC entry. The pipeline never overwrites (no base feature uses `fetch`; `FeatureManager.request` skips cached names) so (b) is reachable only through direct callers.

### Pitfall 5: `purge` is not a no-op for a missing key
`purge("never-added")` raises `KeyError` when the key is neither tracked nor on disk (measured). `add_image_to_store` guards with `img_name in self`, so no behaviour change there.

### Pitfall 6: tests that pass for the wrong reason
The three `test_*delete*`/failed-delete tests that survive arm B unchanged (absent-key delete, failed-delete, `[in_memory]` overwrite) now exercise *upstream* `__delitem__` (`del self._store[key]`). They stay true but are no longer testing pc2img code (D-12 first item).

### Pitfall 7: shipped-file vocabulary gate (see Anti-Patterns) and `ruff format --check` at line length 120.

### Pitfall 8: loky tiled re-generation race (see Surprise).

## Code Examples

### Provenance + lock verification (D-02), reuse of the spike pattern
```bash
uv lock && uv lock --check && uv sync
uv run --frozen python - <<'PY'
import importlib.metadata as md, subprocess, GSEGUtils, pchandler
from GSEGUtils.lazy_disk_cache import disk_backed_store as d
assert md.version("GSEGUtils") == "0.6.0" == GSEGUtils.__version__
assert md.version("pchandler") == "2.1.1"
assert subprocess.run(["grep","-c",r"self\._get_npy_path",d.__file__],capture_output=True,text=True).stdout.strip() == "0"
print("provenance ok")
PY
```
(The scratch-copy equivalent printed `GSEGUtils 0.6.0 pchandler 2.1.1 numpy 2.2.6` and fingerprint `0` after `uv sync --frozen`.)

### D-03 one-shot unlocked-wheel release check (recipe prototyped on a scratch tree)
```bash
uv build --wheel                                   # in the release candidate tree
uv venv --python 3.12 /tmp/unl && uv pip install --python /tmp/unl/bin/python dist/pc2img-*.whl pytest pyyaml
cp -r tests /tmp/unl_tests/tests && cp pyproject.toml /tmp/unl_tests/ && cd /tmp/unl_tests   # run OUTSIDE the repo
/tmp/unl/bin/python -c "import pc2img; assert 'site-packages' in pc2img.__file__"   # wheel, not tree
/tmp/unl/bin/python -m pytest -q --ignore=tests/test_hygiene.py --ignore=tests/test_git_archival.py
```
`test_hygiene.py` / `test_git_archival.py` need `git ls-files`/tags and are excluded outside a clone (they ran green in the real tree).

### Rewritten semantic tests (shape)
```python
from GSEGUtils.lazy_disk_cache import get_npy_path, get_meta_path

def test_purge_removes_the_codec_pair_and_the_memmap(tmp_path):
    store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
    store.add_image_to_store("range", _gray((6, 6))); store.offload_image_data_to_disk("range")
    assert get_npy_path(tmp_path, "range").exists() and get_meta_path(tmp_path, "range").exists()
    store.purge("range")
    assert sorted(p.name for p in tmp_path.iterdir()) == []      # .dat, .npy, .meta.json all gone
```
(Note `store.cache_dir` is the resolved property; `get_*_path` take the directory explicitly.)

## Spike Verdicts (D-04..D-06)

Harness: `.planning/spikes/001-orphaned-override-hunt/` and `.planning/spikes/004-blast-radius-gsegutils-0.6.0/` (READMEs hold commands and output). Scratch venv `GSEGUtils==0.6.0` + `pchandler==2.1.1` outside the repo; tracked tree verified unchanged after every run (`git status` diff empty except the new spike dirs and MANIFEST). Provenance asserted in-process: `__version__ == 0.6.0`, metadata 0.6.0/2.1.1, `site-packages` path, no `direct_url.json`, fingerprint `0`, `DiskBackedStore` has no `_get_npy_path`.

### Spike 001 — VALIDATED (with one surfaced upstream defect)

| pc2img name | Verdict |
|---|---|
| `_get_npy_path`, `_get_meta_path` | ORPHAN; `super()._get_npy_path` / `super()._get_meta_path` DANGLING (`AttributeError`) |
| `_assert_within_cache_dir` | pc2img-only; callers are only the two orphans |
| `__delitem__` | LIVE (upstream `pop` `disk_backed_store.py:1300,1304`, `clear` `:1377` do `del self[key]`); superseded by `purge` |
| `offload` | LIVE; param named `features` vs upstream `keys` (upstream calls only `self.offload(pickle_container=True)` at `disk_backed_store.py:2305`) |
| `DiskBackedImageData` | no buffer-hook overrides; `register_lazy_disk_cache_class` registration works; round trip 2-D f32/u8 and (H,W,3) f32 equal; `AssertionError` on 1-D unchanged |
| direct use `DiskBackedStore[DiskBackedNDArray]` (`strategies/interpolation.py:202`) | keys `triangles/simplices/verts/bary` legal; folder = sha256 hex digest legal |

### Spike 004 — VALIDATED

| Arm | Result |
|---|---|
| locked env (0.5.3), as shipped | 286 passed |
| 0.6.0, tree unmodified | 30 failed / 256 passed (26 `AttributeError`, 4 `StoreKeyError` at the setter) |
| A: overrides removed + migrated `add_image_to_store` | **12 failed / 274 passed**, all in `tests/test_image_store.py` |
| B: A + test-only `_get_*_path` shim | **7 failed / 279 passed** |

The 12 (see spike README for the per-test table): renames (5): `test_overwrite_does_not_leave_stale_on_disk_raster`, `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op`, `test_failed_delete_preserves_codec_pair_and_both_stores`, `test_failed_overwrite_..._[codec_offloaded]`, `test_successful_overwrite_serves_the_replacement_after_offload_and_reload`. Semantic (7): `test_delete_purges_on_disk_codec_pair`, `test_adopted_key_delete_purges_shared_pair`, `test_symlinked_cache_entry_is_served_and_unpickles`, `test_escaping_key_delete_refuses_and_leaves_outside_file_intact[x3]`, `test_refused_overwrite_leaves_existing_entry_intact`.

### Surprise (spike 001 §E): concurrent reload races on `<key>.dat.tmp`

```
worker traceback:  DiskBackedStore.__setstate__ -> _load_entry -> LazyDiskCache._convert_to_memmap
                   -> os.chmod(tmp_path, destination_mode)
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmp75lh6z_k/tile_03/range.dat.tmp'
```
- Repro (pc2img, migrated store overlay + 0.6.0): `generate(["range"])`, then `generate(["range","gradient_x_range","hillshade_range_315_45"])`, then `generate(["range"])` with 2 tiles, `n_jobs=2` -> third call `BrokenProcessPool` (3/3), same script on 0.5.3 passes (3/3).
- Repro (GSEGUtils only, `test_concurrent_reload_race.py`): 4 processes unpickling one store: 11/12 rounds with a failing child on 0.6.0 (`FileNotFoundError`, plus children killed by SIGBUS, exit -7), 0/12 on 0.5.3.
- Mechanism: [VERIFIED: `lazy_disk_cache.py` `_convert_to_memmap` writes `get_memmap_tmp_path` = `<key>.dat.tmp`, chmod, `os.replace`]; `TiledPointCloudImageGenerator._process_tile` is a bound method, so each worker unpickles `self.image_generators` (every tile) [VERIFIED: tiled_generator.py:126-176, `delayed(self._process_tile)` at :136].
- Confirmation by intervention (scratch overlay only): dispatching a copy of `self` with `pcd_tiles=[]`, `image_generators={}` plus only that tile's existing generator makes the third call pass 3/3.
- Supported flow? `TiledPointCloudImageGenerator.image_generators` is kept and reused on purpose (`_process_tile` checks `if tile_id in self.image_generators`), iof3D stores them (`tiles.py:145-146`).
- No fix upstream: PyPI latest GSEGUtils is 0.6.0.

## Measured Behaviour (reproduced on the 0.6.0 wheel, evidence = spike 001 `test_store_semantics.py` output)

**Exception types.** `StoreKeyError(ValueError)`; `StoreContainmentError(StoreKeyError)`; `StorePurgeRefusedError(RuntimeError)` > `StorePurgeForeignArtefactError`; `StorePurgeIncompleteError(OSError)`. All pickle round-trip (loky-safe). Printed MRO: `StoreKeyError > ValueError > Exception`; `StoreContainmentError > StoreKeyError > ValueError > Exception`; `StorePurgeRefusedError > RuntimeError > Exception`. A hostile tile id through the real loky path surfaces in the parent as `StoreKeyError`; no directory is created outside the cache. Existing `except ValueError` callers keep working (SC2 exception-type change = none for `ValueError` catchers; new type is a subclass). `get(escaping_key)` returns `None`, no exception. `.store` writes: `st[k]=v` and `del st[k]` raise `TypeError`; `.pop/.clear/.update/.setdefault` raise `AttributeError` (mappingproxy has no such methods).

**Escape corpus** (`../victim`, `<tmp>/victim`, `a/../../victim`) x routes (add_image_to_store, setitem, setitem+del, add+offload(codec), purge, getitem, pop, get, add_data_to_store): 27/27 refused (get -> None), sentinel intact, whole tree unchanged. Not covered by upstream (measured): an entry inserted via the setter carrying its own `cache_path` outside the cache dir **still offloads there** (`victim.dat` created outside); planted `<key>.npy.tmp`/`<key>.meta.json.tmp` symlinks are followed and **overwrite the target** (needs write access to the cache dir). Closed upstream (differs from spike 000): planted `<key>.dat` and `<key>.dat.tmp` symlinks -> `StoreContainmentError`, sentinel intact.

**`is_valid_store_key`** (73-key corpus: every string literal passed to `generate/request/submit/add_image_to_store/extend_cache_paths/PointCloudTile/_get/match/compute` in `tests/` plus hand-added edge cases). Legal: `range`, `aspect`, `slope_deg`, `hillshade_range_315_45`, `grad_range_px0.5`, `norm_(range,2,98)`, `rrim_pack_(range,r16,d8,z1.2345678)`, `rrim_pack_(range,r16,d8,z1e-05)`, `rrim_component_(structure,range,r16,d8)`, `scalar_field_intensity`, `scalar_field_Scalar field`, `scalar_field_é`, `scalar_field_a*b`/`a?b`/`a<b>`/`a|b`/`a"b`, `tile_03`, `tile-3`, `0_0`, `x_-1_-1`, `0`, `1.5`, `tile 03`, the 64-hex sha256 digest, `triangles/simplices/verts/bary`, 255/256/300-char names (no length rule). **Refused:** `''`, `.`, `..`, `CON`, `ZH/01`, `tile_03/range`, `tile_03.`, `scalar_field_a/b`, `scalar_field_a\b`, `scalar_field_GPS:time`, `scalar_field_x.`. **All realistic pipeline keys pass.** On 0.5.3 the three scalar-field shapes `a/b`, `GPS:time`, `x.` add + offload + read fine (`a/b` vanishes on reopen; the others re-adopt) [VERIFIED: `test_053_baseline_key_shapes.py` on the locked env] -> they are newly refused: BC `error-behavior`.

**`extend_cache_path`** (five sites `tiled_generator.py:71,74,162,171`, `strategies/interpolation.py:203`, unchanged positions): legal `tile_03`, `0`, `tile-0`, `tile 03`, sha256 hex; `StoreKeyError`: `../x`, `a/b`, `/tmp/x`, `''`, `.`, `CON`, `t.`; planted directory symlink -> `StoreContainmentError`; non-`str` -> pydantic `ValidationError`; `TIGSettings.extend_cache_paths('../x')` -> `StoreKeyError` unwrapped.

**`purge`.** From an entry that is in memory only, plain-offloaded (`.dat`) or codec-offloaded (`.npy`+`.meta.json`) it removes all of its files (cache dir empty afterwards), also with `purge_disk_on_gc=False` (explicit purge wins); absent key -> `KeyError`; after purge `store[k]` -> `KeyError`. Forked child and a loky worker holding a parent-constructed store -> `StorePurgeRefusedError`; same overwrite in the constructing process OK. Symlinked adopted entry (cache `range.npy`/`range.meta.json` -> `shared/`): link target **outside** the cache dir -> purge and `add_image_to_store` overwrite refused with `StorePurgeForeignArtefactError`, link and target intact; target **inside** the cache dir -> purge removes link and payload, overwrite OK. Pickling a store after a read still **de-links** the symlinks (`is_symlink` True -> False) — upstream behaviour (review-r3 WR-02's open question).

**`del`/`pop`/`clear`.** Files unchanged; offloaded key re-adopted on the next `store[k]`; a fresh store over the dir tracks it; default-config store (`enable_caching=False`) has no files at all.

**Overwrite residuals.** Empty `(0,0)` raster and `V0` dtype are now **accepted** (old failure mode gone on 0.6.0); wrong-type override (`enable_caching_override=2`) -> pydantic `ValidationError` **after** the purge: old entry lost; simulated `OSError(ENOSPC)` during the memmap build -> old entry lost (`'range'` untracked, files gone) — documented residual unchanged. ABA: `del` + re-add + collect old entry deletes the new `.dat` (True -> False); `purge` + re-add + collect old entry keeps it (True -> True).

## Migration Checklist (handoff §3, line numbers re-derived on HEAD `7e5158f`)

The handoff's own grep, run on 2026-10-01: `git --no-optional-locks grep -n -E '_get_npy_path|_get_meta_path|_get_legacy_pickle_path' HEAD -- src tests` -> **37 raw matches** (handoff: 19 at `7893bda`). Zero source use of `_DBNDArrayFileExt|_DBNDArrayMetaExt|_LegacyPickleExt`.

| # | Handoff item | Now |
|---|---|---|
| 1 | delete `__delitem__` override (was :126) | `src/pc2img/image_cache/disk_backed_image_store.py:186-239` (def at 186; `super().__delitem__` :237; unlinks :238-239; call sites of the withdrawn builders :235-236) |
| 2 | delete path-builder overrides + `super()` calls + `_assert_within_cache_dir` | `_assert_within_cache_dir` def :60; `_get_npy_path` def :118 (`super()` :120); `_get_meta_path` def :122 (`super()` :124) |
| 3 | hand-rolled unlink alt. | n/a (D-08 deletes) |
| 4 | docstring naming withdrawn methods (was :54) | `:65` (enumeration inside `_assert_within_cache_dir`, deleted with it), `:77` (`__delitem__` unlink), `:148` and `:174` (`add_image_to_store`: `self._get_npy_path` pre-check and docstring), `:192`, `:260` (`offload` docstring), class docstring containment invariant `:26-37` |
| 5 | 11 test assertions + banner | 26 lines in `tests/test_image_store.py`: 111, 130, 131, 135, 136, 171, 172, 182, 183, 211, 212, 218, 219, 253, 254, 262 (banner comment), 450, 451, 459, 460, 480, 481, 548, 553, 563, 572 (comments) |
| 6 | audit `clear()` call sites | none in `src/`, `tests/`, `scripts/` (non-vendored) or iof3D; pc2img pipeline never calls `del`/`clear`/`pop` |
| 7 | five `extend_cache_path` sites | `tiled_generator.py:71,74,162,171`; `strategies/interpolation.py:203` (unchanged; all realistic values legal, see Measured Behaviour) |
| 8 | re-run corpus + re-grep | `git grep -nE '_get_npy_path|_get_meta_path|_assert_within_cache_dir' -- src tests` must print nothing; `.store` readers: `tests/test_image_store.py:578` (read-only use, fine); `image_data` alias `:242-244` annotated `dict[...]` -> `Mapping[...]` |

Other consequential edits: `add_image_to_store` body :174-177 (pre-check line, `del self[img_name]` -> `self.purge(img_name)`); `from pathlib import Path` becomes unused (ruff F401) once the builders go; the docstring paragraph claiming "the one safe ordering" (review-r4-d8efb7e5d778) is rewritten with the method.

## iof3D read-only grep (D-19, `/scratch/34_iof3d` @ `767ad66`, no edits)

- No `del`, `.clear()`, `.pop()` on any store; no `.image_data` / `.store` access; no call to `add_image_to_store`/`add_data_to_store`.
- `DiskBackedImageStore` is only **imported** (`src/iof3D/v2/services/tiles.py:13`, `src/iof3D/v2/tasks/generate_tile_features.py:14`), never constructed.
- Store-adjacent calls: `pcig.feature_mgr.cache_store.offload()` (`generate_tile_features.py:304`) inside `try/except Exception: pass` — plain `offload()`; works with the pc2img wrapper's signature, and any new refusal there would be swallowed silently.
- `extend_cache_path(path_ext)` / `extend_cache_paths(path_ext)` with `path_ext = pcd_id.stem if isinstance(pcd_id, Path) else pcd_id` (`image_generation.py:156-160`, `v2/services/tiles.py:132-133`): a **filename stem** — legal unless it contains `:`/`\`/`/`, ends in `.` or is a Win32 device name. Tile ids come from the FoV tree leaf ids.
- Cache config: `purge_disk_on_gc=False` everywhere (`generate_tile_features.py:265,282`; `scripts/v2/*`), so the durable-cache path is unaffected by `del` no longer unlinking; iof3D also pickles `DiskBackedImageData` directly (`integrations/disk_backed_image_data.py:11-25`) — entry-level, outside this phase.
- iof3D calls `TiledPointCloudImageGenerator.generate` per pcd with a **fresh** instance each time (`tiles.py:130-146`), so the tiled re-generate race is not triggered by that call pattern; it needs a *reused* instance.
- Effect on BC wording: the store-key rule matters to iof3D via `path_ext`; `del`/`clear`/`pop` semantics and `.store` read-only matter to no known consumer. iof3D has its own handoff (`iof3d-store-key-contract.md`); cross-reference rather than restate.

## D-11 / D-12 triage — raw material (the planner builds the table; step = mechanical result of the rule)

| ID | What it is | Proposed step | Evidence |
|----|-----------|---------------|----------|
| r3 WR-01 `review-r3-ffa2d1c2ca7c` | insertion route unguarded with the suite green; re-pin each route with a no-new-file-anywhere test | **3** (migration: escape-corpus re-pin) | S1: 27 cells refused; Pattern 2 snapshot test |
| r3 WR-02 `review-r3-e40af7956397` | symlinked-entry delete assertion vacuous after pickling de-links; decide on de-link-on-pickle | **3** (test is rewritten for D-08: assert `purge` refusal/outcome per the two target locations) + de-link-on-pickle is upstream (**1**) — measured still de-links | S4/S8 symlink rows; arm B fails this test |
| r3 WR-04 `review-r3-ede9dcc0e91b` | `__setitem__` unguarded, escaping key un-removable | **1/2**: upstream guards the setter (refused at set time); the `__delitem__` override that raised is deleted | S1 R2/R3; `clear()` completes |
| r3 WR-05 `review-r3-dda7a00b69cf` | docstrings overstate the containment invariant; `.tmp`/`.dat` writes follow planted symlinks | **3** (single restatement of the threat model, D-09) ; facts for the restatement: `.dat`/`.dat.tmp` now refused, `.npy.tmp`/`.meta.json.tmp` still followed, entry-owned `cache_path` not contained | S1b, S5, S9 |
| r3 WR-06 `review-r3-2785f15bd78e` | `_assert_within_cache_dir(cache_dir/"..")` admitted | **2** (helper deleted) | orphan hunt |
| r3 IN-02 `review-r3-36e425b15be9` | `embedded_traversal` case can't escape because `cache/a` never exists | **3/4**: one line `(cache/"a").mkdir()` in the layout when re-pinning | one-liner, no new behaviour |
| r2 `review-r2-a7c7f4e498a6` | meta-path guard branch untested | **2** | `_get_meta_path` deleted |
| r4 `review-r4-a97761a4b73d` | overwrite loses old entry on empty raster / V0 dtype / wrong-type override | **1** (needs build-then-adopt upstream); two of three input classes **no longer fail on 0.6.0**; remaining: wrong-type override and mid-build `OSError` still lose the old entry. Pre-validating = new behaviour -> defer (**4**); narrowing the docstring claim while the docstring is being rewritten anyway is a no-behaviour edit | `test_r4_overwrite_residuals.py` |
| r4 `review-r4-da637a8dfe3c` | `_assert_image_shape` is a bare `assert` (vanishes under `-O`) | **4** candidate: `raise AssertionError(...)` is a one-line change, same type, same default behaviour — differs only under `-O`; owner may read that as "new behaviour" and defer | disk_backed_image_data.py:27 |
| r4 `review-r4-ee69c181dfa0` | no test pins containment-before-shape precedence | **3** if the pre-check line is kept (precedence `StoreKeyError` first, measured); **2** (superseded) if D-10's no-pre-validation is read literally and the line is dropped (then double-fault raises `AssertionError`) — Open Question 3 | S9 `TargetImageStore` vs `NoPreCheck` |
| r4 `review-r4-d8efb7e5d778` | docstring "the one safe ordering" overclaims; held-reference ABA | **2**: `purge` detaches the finalizer; text rewritten with the method | S5 ABA True/True |
| r4 `review-r4-84a2b5dff14c` (D-12) | absent-key delete test near-subset of two-store sensor | **2/3**: both tests pass unchanged on arm B after the rename, but they now exercise upstream `__delitem__`; fold/delete is a no-risk test edit | arm B |
| r4 `review-r4-15a5c4928dc8` (D-12) | 18 `tmp*` entries leaked per run | **3** (SC3 test hygiene): autouse `tempfile.tempdir -> tmp_path` fixture in `tests/conftest.py`; verify `ls $TMPDIR \| grep -v '^pytest-of' \| wc -l` = 0 after a run (currently 18, reproduced on both 0.5.3 and 0.6.0) | scratch `TMPDIR` count |
| residual: finalizer ABA | path-bound finalizer unlinks the new `.dat` | **1**: fixed on the `purge` route (measured); persists on `del`+re-add (not used by pc2img) | S5 |
| residual: `.dat` symlink-follow | | **1**: closed upstream in 0.6.0 for `.dat`/`.dat.tmp` (measured); `.npy.tmp`/`.meta.json.tmp` still followed = documented non-adversarial limit | S5, S9 |
| residual: mid-build `OSError` atomicity | old entry lost when the replacement build fails | **1**: unchanged (measured), needs an upstream build-then-adopt primitive | S5 |

New items found by this research that the table should carry (not in D-11's list): the tiled re-generate race (**1** upstream-owned, but release-relevant); entry-owned out-of-cache `cache_path` still offloads (**1**, restate in docstring); `offload(features=...)` vs upstream `keys` parameter name (pre-existing, step **4**: no action).

## Migration record (BC-01) — material for the Phase-7 entries

Current record: `.planning/MIGRATION-v0.11.md` (25 entries, `BC-P2I-001..025`, frontmatter `baseline_ref: "91b4ab6"`, `target_ref: "e9eb3c48..."`, `milestone: v1.0`; sections Summary / Public API stability statement / Breaking & behaviour changes / Additive / Internal & sweep / Verifier (inline)). The verifier's `BC_ENTRIES` list is the Tier-1/Tier-2 index and must be kept in sync with the tables (`_check_ids` demands unique strictly increasing `BC-P2I-NNN`). Verifier status measured: **`[ok] verified 25 entries` on the locked env; `[fail] BC-P2I-017: expected ValueError for an escaping key, got AttributeError` on 0.6.0 + unmodified tree** (so the verifier itself detects the break).

Stale text to amend (cite, don't restate, BC-GSEG-006/007):
- `BC-P2I-002` (pins): states `pchandler ~= 2.1`, `GSEGUtils >= 0.5.3, < 1.0`, numpy "capped `<2.4`" — now `pchandler >= 2.1.1, ~= 2.1`, `GSEGUtils ~= 0.6.0`, effective numpy `>= 2.2, < 2.4`, cuda extras no longer pull cuproj/cuml/dask-cudf.
- `BC-P2I-012`: says depends on `GSEGUtils >= 0.5.3` (historical record; keep, add pointer).
- `BC-P2I-017`: "nesting under the cache directory is still allowed" is **false** now; the refusal type is `StoreKeyError`/`StoreContainmentError` (both `ValueError`).
- Verifier Tier-2 `_tier2_bc_p2i_017` still passes (it only needs `ValueError`).

Proposed new entries (classification is the planner's, Phase-6 D-25 schema; measured facts supplied):
1. `dep-constraint`, should-review — pin change; add `psutil` transitive note not needed (no lock addition).
2. `semantic-change`, should-review — `del`/`pop`/`popitem`/`clear` drop tracking only; `purge(key)` is the delete verb; an offloaded key is re-adopted by the next read and by a fresh store; `add_image_to_store` overwrite now removes `.dat` + codec pair (previously codec pair only) and raises `StorePurgeForeignArtefactError` for a symlinked adopted entry whose target is outside the cache dir and `StorePurgeRefusedError` when called from a process that did not construct the store.
3. `error-behavior`, should-review — key/segment refusals via `StoreKeyError`/`StoreContainmentError` (`ValueError` subclasses): nested keys, `\`, `:`, trailing `.`/space, `''`/`.`/`..`, Win32 device names; applies to scalar-field names via `generate()` and to `extend_cache_path` segments (tile ids, folder names, pcd stems); refusal happens at the setter, `add_data_to_store`, `purge`, `getitem`, `extend_cache_path`; a planted directory symlink -> `StoreContainmentError`.
4. `signature-shape`/`semantic-change`, should-review — `.store` / `image_data` is a read-only `mappingproxy` (`TypeError` on `[]=`/`del`; `AttributeError` on `.pop/.clear/.update/.setdefault`); cross-reference BC-GSEG-007.
5. Re-stamp `target_ref` to `v0.11.0` (deterministic tag name). Known limitation, if the owner chooses option (b) in Open Question 1: tiled re-generation on one instance with n_jobs>1.

Verifier extraction + run (exists and runs today): `awk '/^## Verifier \(inline\)$/,/^```$/' .planning/MIGRATION-v0.11.md | sed -n '/^```python$/,/^```$/p' | sed '1d;$d' > _scrap/pc2img-migration-verifier.py && uv run --frozen python _scrap/pc2img-migration-verifier.py` (`_scrap/` is the repo's scratch dir).

## Release-Path Inventory (edit points; verify commands that run today)

| Decision | File | Current state | Edit point | Verify (exists & runs) |
|---|---|---|---|---|
| D-13 WR-02 | `.readthedocs.yaml:19-20` `post_checkout` | `- git fetch --unshallow \|\| true` then `- git fetch --tags` | `git fetch --tags --force`; reproduced: plain `--tags` against a moved floating tag -> `! [rejected] v0 -> v0 (would clobber existing tag)`; `--force` -> `t [tag update]` (scratch clone) | scratch-clone simulation of the job commands (no CI test exists for this file) |
| D-13 WR-03 | same | `--unshallow \|\| true` unconditional | run only when `git rev-parse --is-shallow-repository` prints `true`, no `\|\| true` (`--unshallow` on a complete clone is fatal) | same |
| D-13 WR-04 | same, add `post_install` job | none | assert installed version does not start with `0.0.` and clone not shallow | `python -c "import importlib.metadata as m; assert not m.version('pc2img').startswith('0.0.')"`; the CI docs job already has the `0.0.` guard |
| D-14 AR-07 | `.github/scripts/check_publish_gate.py:42-45` `PUBLISH_STEP_PATTERNS` (`pypa/gh-action-pypi-publish`, `twine\s+upload`); `is_publish_step` :57-63; `check_job` :66 iterates only `job.steps` | misses `uv publish` and a publish step inside a composite action (local actions: `.github/actions/setup-python-deps`, `.github/actions/classify-changes`) | add `uv\s+publish`; scan `.github/actions/*/action.y*ml` `runs.steps` and flag any job step `uses: ./.github/actions/<x>` whose action contains a publish step; new tests in `test_check_publish_gate.py` (helpers `build_tree`, `ROGUE_WORKFLOW`) | `python .github/scripts/check_publish_gate.py` -> `check_publish_gate: OK` (today, exit 0); `pytest .github/scripts/ -q` -> 93 passed (today) |
| D-14 AR-08 | `.github/scripts/preflight_ruleset_apply.py:145-208` `matchable_job_names`, `cross_reference` :211-242 | name set = every job `name:` of every workflow regardless of trigger | build the set only from workflows whose trigger block (`ruleset_lib.trigger_block`, handles quoted/bare `on:`) includes `pull_request`; the scheduled `Branch ancestry assertion` must then be rejected; new tests in `test_preflight_ruleset_apply.py` | same pytest run; live payloads require `Lint (pre-commit)`, `Tests (pytest)`, (main) `Docs (sphinx -W)` — all `pull_request` jobs in `ci.yml` |
| D-14 retire | `.planning/phases/06-.../06-SECURITY.md` rows T-06-17 / T-06-31 and AR-07 / AR-08 (lines 61, 77, 135-136) + "Follow-ups (Phase 7)" (:142-149) | accepted risks | Phase-7 security verification retires them (`/gsd-secure-phase`) | re-run both checkers against rogue fixtures |
| D-15 WR-01 | `RULESETS.md` ("For maintainers") | no mention | one line naming `allowed_merge_methods`, `dismissal_restriction`, `required_reviewers`, `require_extra_approval_for_unattributed_changes`, `do_not_enforce_on_create` as not governed by the apply | `tests/test_hygiene.py` (shipped-file vocabulary) |
| D-15 IN-01 | `.github/scripts/test_ruleset_lib.py:117,128-129`; also `test_check_ruleset_drift.py:107,117-118` | `"dismissal_restriction": {}`, `integration_id: 15368` everywhere | measured shapes `{"enabled": false, "allowed_actors": []}`, no `integration_id` after an apply; keep one UI-created case with `15368` | pytest .github/scripts |
| D-15 IN-02 | `ruleset_lib.py:266-268` rule (c) docstring ("live returns the integer 15368") | | reword: live omits `integration_id` after an apply | docs only |
| D-15 IN-03 | `test_ruleset_lib.py:281` `test_read_filled_key_survives_when_the_committed_side_sets_it` | one tuple | parametrise over `PULL_REQUEST_READ_FILLED_KEYS` and `STATUS_CHECKS_READ_FILLED_KEYS` | pytest |
| D-15 IN-04 | `ruleset_lib.py:254-280` `normalize` docstring | rule (d) keys unnamed | name the keys / the two tuples (`ruleset_lib.py:41-47`) | docs only |
| D-16 | `RELEASE.md` "Releasing" steps 1-4 | promote from a branch cut from `main` carrying `develop-gsd`'s tree minus `.planning` and `.claude`, squash-merge; back-merge as merge commit; release PR #15 merge publishes; back-merge again | follow as written; `main` is `20ef688`; PR #15 is open and unmerged (`gh pr list`) | `git merge-base --is-ancestor origin/main origin/develop-gsd` (nightly assertion's check); `scheduled-health.yml` run; attestation: `https://pypi.org/integrity/pc2img/0.11.0/<file>/provenance` |
| D-17 | owner checkpoints | PyPI trusted publisher + `pypi` environment not created | immediately before release-PR merge (tuple: owner `gseg-ethz`, repo `pc2img`, `publish-pypi.yml`, env `pypi`; RELEASE.md) | `gh api repos/gseg-ethz/pc2img/environments` shows `pypi` |
| D-18 | `.planning/MIGRATION-v0.11.md` | frontmatter `target_ref` is a sha | `target_ref: "v0.11.0"`; append entries + `BC_ENTRIES` in the verifier | verifier command above |

Existing CI facts relevant to the plan: `ci.yml` jobs `Lint (pre-commit)`, `Tests (pytest)` (`pytest -m "not benchmark" --cov=pc2img ... --cov-fail-under=55`), `Docs (sphinx -W)`; the lint job also runs `check_publish_gate.py` and `pytest .github/scripts/ -q` (its `check_ci_config.py` step is guarded by an existence test and the script is absent, so it reports "config self-check not configured; skipping"). Commit conventions: functional scopes only, no planning IDs; commits squash to `main` where `.planning/` is stripped.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| subclass overrides `_get_npy_path`/`_get_meta_path` to add containment | upstream validates every key and verifies containment in public free functions | GSEGUtils 0.6.0 (2026-08-17) | override deleted, call free functions |
| `del store[k]` unlinks the codec pair | `del` drops tracking only; `purge(k)` drops tracking and unlinks six artefacts | 0.6.0 | BC entry |
| `.store` returns the live dict | read-only `mappingproxy` | 0.6.0 (BC-GSEG-007) | `image_data` annotation |
| `.dat` memmap written in place | written to `<key>.dat.tmp` then renamed | 0.6.0 | atomic, but a fixed tmp name races across processes (Surprise) |

**Deprecated/outdated:** the handoff's "deprecating wrapper" expectation (retracted in the handoff itself); CLAUDE.md's "implement buffer hooks" description of `DiskBackedImageData` (hooks are inherited from `DiskBackedNDArray`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The seam's SUS verdict on GSEGUtils/pchandler is benign (first-party, already locked) and needs no extra `checkpoint:human-verify` | Package Legitimacy | low; owner confirms at plan review |
| A2 | Nested/`:`/trailing-dot cache dirs left by an older pc2img are refused-to-adopt (not crashed) by the 0.6.0 rescan | Runtime State Inventory | low; only stale caches with such keys; not measured here |
| A3 | pyright informational job tolerates the `image_data` annotation change (`dict` -> `Mapping`) | Migration Checklist | very low (informational, `continue-on-error`) |
| A4 | No other consumer than iof3D calls the changed store surface | iof3D grep | low; consumer topology note in memory says 4-repo chain |
| A5 | `pip`-style resolvers pick numpy 2.3.x for end users (unlocked wheel run picked 2.3.5) | Code Examples | none (measured once) |

## Open Questions

1. **The loky tiled re-generation race — what does 0.11.0 do about it?** (blocks the claim "runs on >= 0.6" for a supported flow)
   - Known: reproduced, root cause upstream + pc2img's whole-`self` pickling; no upstream fix released; intervention proves the diagnosis. iof3D's call pattern (fresh instance per pcd) does not trigger it.
   - Options: (a) small pc2img change so each worker receives only its own tile's generator (prototype ~10 lines in `generate`/`_process_tile`; also removes shipping every tile's point cloud to every worker); (b) ship 0.11.0 with the limitation recorded as a BC/known-issue entry and file the upstream issue (owner action in the GSEGUtils repo); (c) wait for a GSEGUtils fix and pin `>=` it. D-11 step 1 says "never fix what belongs upstream" — but (a) is a pc2img-owned dispatch problem too, so the rule does not decide it.
   - Recommendation: (b) + an `n_jobs>=2` regression test marked xfail/strict-off is the lowest-risk reading of D-11; (a) if the owner wants re-generation to work on release day. Either way, owner decision at plan review.
2. **numpy floor and cuda extras in pc2img's own metadata.** Effective numpy range is now `>=2.2,<2.4` but pc2img declares `numpy ~= 2.0`; the cuda extras shrink. Tighten the declared floor (honest metadata, one-way once published) or leave and document in BC-P2I-002? Not covered by D-01/D-02.
3. **Keep the one-line `get_npy_path(self.cache_dir, img_name)` pre-check?** Keeping preserves "containment error before shape error" and is the only pc2img line that calls the free function; dropping fits D-10 literally and supersedes `review-r4-ee69c181dfa0`, at the price of flipping a double-fault precedence.
4. **Symlinked adopted entry test (`test_symlinked_cache_entry_*`)**: with `del` not unlinking, rewrite to assert `purge` outcomes for both target locations (refused outside, removed inside) or drop the delete half? Planner's call within D-11 step 3.
5. **`add_image_to_store` raising `StorePurgeRefusedError`/`StorePurgeIncompleteError`** (RuntimeError/OSError, not ValueError/KeyError) on overwrite: document only, or catch? Recommendation: document (D-10 spirit: let upstream propagate).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | lock, build, run | yes | 0.11.26 | — |
| Python 3.12 | project (`~=3.12,<3.13`) | yes | CPython 3.12.13 (uv-managed) | — |
| PyPI network | lock/install/spike venv | yes | — | — |
| gh CLI (authenticated) | read-only PR/release/env checks | yes | — | owner runs |
| `.venv` (locked) | baseline suite | yes | GSEGUtils 0.5.3 until re-sync | `uv sync` |
| ruff | `tests/test_hygiene.py` | yes (locked dev group; scratch venv needed it installed) | 0.16.9 in scratch | — |
| RTD / PyPI account actions | D-17, RTD build | owner only | — | checkpoints |

**Missing dependencies with no fallback:** none for planning. Owner-only: PyPI trusted publisher, `pypi` environment (D-17).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ~= 9.1 (`--import-mode=importlib --strict-markers`, `testpaths = ["tests"]`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run --frozen pytest tests/test_image_store.py -q` |
| Full suite command | `uv run --frozen pytest -m "not benchmark" --cov=pc2img --cov-branch --cov-fail-under=55` (CI form) |
| Baselines today | locked env: 286 passed; `.github/scripts`: 93 passed; verifier: `[ok] verified 25 entries` |

### Phase Requirements -> Test Map
| Req / SC | Behavior | Test Type | Automated Command | File Exists? |
|----------|----------|-----------|-------------------|-------------|
| DEP-05 / SC1 pin | `GSEGUtils ~= 0.6.0`, `pchandler >= 2.1.1, ~= 2.1` locked; resolved build is 0.6.x not a cached 0.5.x | provenance | `uv lock --check && uv run --frozen python -c "import importlib.metadata as m,GSEGUtils;assert m.version('GSEGUtils')=='0.6.0'==GSEGUtils.__version__"` + fingerprint `grep -c 'self\._get_npy_path' $(python -c 'import GSEGUtils.lazy_disk_cache.disk_backed_store as d;print(d.__file__)')` = 0 | script in Code Examples |
| DEP-05 / SC1 delete | withdrawn names gone | grep gate | `git grep -nE '_get_npy_path\|_get_meta_path\|_assert_within_cache_dir' -- src tests` prints nothing (exit 1) | handoff §3 item 8 |
| DEP-05 / SC1 re-pin | no file written outside the cache dir on insert/offload/load/delete/purge | unit | `uv run --frozen pytest tests/test_image_store.py -k "escaping or refused" -q` (name new tests to match, as the Phase-5 mutation checks did) | modify existing, Wave 0 |
| SC2 | exception type from upstream containment is `ValueError`-compatible, recorded as BC | unit + verifier | `uv run --frozen pytest tests/test_image_store.py -k escaping -q`; verifier `[ok]` | new BC entry |
| SC3 hygiene | no leaked `tmp*`; absent-key test folded | suite + shell | `TMPDIR=$(mktemp -d) uv run --frozen pytest -q; ls $TMPDIR \| grep -v '^pytest-of' \| wc -l` = 0 | conftest fixture, Wave 0 |
| SC3 review | phase diff reviewed | process | `/gsd-code-review 7 --files <changed>`; `/gsd-consolidate-findings` | — |
| SC4 / BC-01 | record finalised, `target_ref: "v0.11.0"`, verifier green | verifier | `grep -n '^target_ref: "v0.11.0"' .planning/MIGRATION-v0.11.md` + verifier command | file exists |
| D-03 | built wheel + unlocked resolve passes the suite | one-shot | recipe in Code Examples (expect 0 failures after the test rewrites) | script to write |
| D-13 | RTD commands behave on moved tag / complete clone / shallow | simulation | scratch-clone script (recipe in Release-Path Inventory) | script to write |
| D-14/D-15 | gate + preflight reject new shapes; fixtures corrected | unit | `uv run --frozen pytest .github/scripts/ -q`; `python .github/scripts/check_publish_gate.py` | extend existing tests |
| SC5 | promotion, publish, attestations, back-merge, nightly | manual-only (owner actions, GitHub/PyPI side) | `git merge-base --is-ancestor origin/main origin/develop-gsd`; `gh pr view 15`; `curl -s https://pypi.org/pypi/pc2img/0.11.0/json`; provenance URL in RELEASE.md | justified: external accounts |
| Tiled race (if (a)/(b)) | `generate()` x3 on one instance, 2 tiles, `n_jobs=2` | integration (slow, loky) | `uv run --frozen pytest tests/test_tiled_generator.py -k regenerate -q` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run --frozen pytest tests/test_image_store.py -q` (+ `.github/scripts/` for CI-script tasks).
- **Per wave merge:** full suite (CI form) and the verifier.
- **Phase gate:** full suite green, D-03 run green, verifier green, review artifact present, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] rewrite/rename the 12 failing tests in `tests/test_image_store.py` (5 renames, 7 semantic)
- [ ] autouse `tempfile.tempdir -> tmp_path` fixture in `tests/conftest.py`
- [ ] `n_jobs>=2` tiled regenerate test (decision-dependent, Open Question 1)
- [ ] tests for AR-07/AR-08 shapes in `.github/scripts/test_check_publish_gate.py` / `test_preflight_ruleset_apply.py`
- [ ] scripts for the D-03 and RTD simulations (outside `tests/`, e.g. the plan's own verification steps)

## Security Domain

### Applicable ASVS Categories (level 1, `security_enforcement` enabled)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (library) | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | upstream `StoreKeyError` rule (`is_valid_store_key`); scalar-field names from PLY/E57 metadata are untrusted input reaching keys via `FeatureRegistry.match`'s unanchored fallback |
| V6 Cryptography | no | — |
| V12 Files & Resources (path traversal, symlinks) | yes | upstream lexical + resolved containment; residuals: planted `.npy.tmp`/`.meta.json.tmp` symlinks and entry-owned `cache_path` (non-adversarial threat model, restate in docstring) |
| V14 Config / supply chain (release) | yes | publish-gate (AR-07), ruleset preflight (AR-08), trusted publishing + attestations |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| path traversal via crafted scalar-field name (`../x`) | Tampering | upstream `StoreKeyError` at setter/insert/purge/getitem; 27/27 corpus cells refused |
| symlink-follow on write to a planted tmp name | Tampering | `.dat`/`.dat.tmp` refused upstream; `.npy.tmp`/`.meta.json.tmp` accepted residual (needs cache-dir write access) |
| destructive delete by wrong process | Tampering/DoS | `purge` PID guard (`StorePurgeRefusedError`) |
| wrong-publisher publish step | Elevation | `check_publish_gate.py` (+ `uv publish`/composite coverage this phase) |
| required context nothing produces under empty bypass list | DoS | preflight (+ `pull_request`-trigger filter this phase) |
| unreviewed gap-closure fixes | Repudiation | own-diff review (global Review Discipline) |

## Project Constraints (from CLAUDE.md)

- Python `~=3.12,<3.13`; numpy 2.x (floor 2.2 effective), pydantic v2, joblib/loky; `uv`-managed venv.
- **Dependency edits (PCHandler / GSEGUtils) need human approval — they are separate GSD-managed repos: no edits there** (honoured: read-only, scratch venv only). The pc2img pin change itself is pc2img's own `pyproject.toml`.
- Branching: work on `develop-gsd` + per-phase branches (`gsd/phase-07-...`); `main` only at milestone ship, stripped of `.planning/` and agent files.
- Commit messages: Conventional Commits with functional scopes (`fix(image_cache):`, `test(image_store):`, `ci(rtd):`), never planning-ID tags; commits squash to `main`.
- Shipped text carries no planning vocabulary (enforced by `tests/test_hygiene.py`).
- Registry/strategy conventions: new code keeps `__all__`, docstring name-grammar rules (no new feature this phase).
- Ruff line length is 120 (pyproject; the CLAUDE.md black-88 text is stale — owner reversed D-11 88->120).
- Review discipline (global): gap-closure/new diffs get their own review; findings land back in GSD via `/gsd-consolidate-findings`; green CI proves little (cite measurements).
- Reproduce, don't read: every exception-type/containment/purge claim here is from running code.
- GSD workflow enforcement: edits only through a GSD command.
- Interactive mode: scope/architecture tradeoffs (Open Questions 1-3) are the owner's decision at plan review; do not auto-resolve.

## Sources

### Primary (HIGH confidence)
- Spike runs this session against the PyPI wheels: `.planning/spikes/001-orphaned-override-hunt/` (`provenance.py`, `test_orphan_hunt.py`, `test_store_semantics.py`, `test_r4_overwrite_residuals.py`, `test_concurrent_reload_race.py`, `test_053_baseline_key_shapes.py`, `target_store.py`), `.planning/spikes/004-blast-radius-gsegutils-0.6.0/` (`spike004_plugin.py`)
- GSEGUtils 0.6.0 installed source (`lazy_disk_cache/__init__.py`, `disk_backed_store.py`, `lazy_disk_cache.py`, `paths.py`) — read this session
- `~/gsd-workspaces/pchandler/.planning/handoffs/pc2img-migration-BC-GSEG-006.md` (§1-§3) — read in full
- pc2img tree at `7e5158f`: `src/pc2img/image_cache/*.py`, `features/manager.py`, `core.py`, `tiled_generator.py`, `strategies/interpolation.py`, `tests/test_image_store.py`, `tests/test_hygiene.py`, `.github/scripts/*`, `.readthedocs.yaml`, `RELEASE.md`, `RULESETS.md`, `.planning/MIGRATION-v0.11.md`
- `https://pypi.org/pypi/GSEGUtils/json`, `/GSEGUtils/0.6.0/json`, `/pchandler/json`, `/pchandler/2.1.1/json`, `/pchandler/2.1.0/json` (release dates, `requires_dist`)
- `uv lock` / `uv sync --frozen` / `uv build` on a scratch copy of the tree (`git archive HEAD`, outside the repo)

### Secondary (MEDIUM confidence)
- iof3D read-only grep (`/scratch/34_iof3d` @ `767ad66`), `gh pr list` / `gh release list` (read-only), 06-SECURITY.md, 06-CONTEXT.md

### Tertiary (LOW confidence)
- none relied on

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions and `requires_dist` from PyPI JSON; lock re-resolve run.
- Architecture / migration: HIGH — simulated end state run through the full suite (two independent mechanisms: in-process plugin and scratch overlay).
- Pitfalls: HIGH for behaviours measured; MEDIUM for A2.
- Release path: MEDIUM — edit points read and existing tests run; the new gate/preflight behaviours and RTD edits are specified, not yet implemented.

**Research date:** 2026-10-01
**Valid until:** 2026-10-31 (stable) — re-check PyPI for a GSEGUtils 0.6.1 before the plan locks; a fix there changes Open Question 1.
