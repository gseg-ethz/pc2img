---
created: 2026-09-24T15:30:00Z
title: Adopt GSEGUtils 0.6 and delete the DiskBackedImageStore containment override
area: image_cache
severity: minor
resolves_phase: 6
files:
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_image_store.py
  - pyproject.toml
  - uv.lock
  - .planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md
source: D-R4-01 (round-4 gap closure owner decision, 2026-09-24), spike-000-absorption-test
---

## Why

Spike 000 (`.planning/spikes/000-absorption-test/README.md`, verdict **VALIDATED**) proved
absorption: GSEGUtils phase-14 (the codebase that ships as GSEGUtils 0.6.0 on PyPI) enforces
containment natively at every disk-touching path builder. Every input in pc2img's Phase-5
escape corpus (3 key spellings x 4 routes, commit `03eb715`) is still refused upstream when
`DiskBackedImageStore`'s `_get_npy_path` / `_get_meta_path` / `_assert_within_cache_dir`
override is removed — refused by `StoreKeyError` (lexical rule, the layer the corpus
actually exercises) or `StoreContainmentError` (resolved layer, exercised by the spike's
differential symlink probe). The 6 realistic feature names from the Phase-5 characterization
test round-trip unchanged, so absorption does not over-refuse.

**On the currently-installed GSEGUtils 0.5.x, this override is load-bearing, not
defence-in-depth** — 05-16 corrected that exact false claim everywhere it had propagated
(store docstring, test comment, BC-NOTES entry 15, UAT `review-r1-a239bdbfc017`). The
override is deletable only once pc2img is actually running phase-14 / GSEGUtils >= 0.6, which
is a Phase-6 adoption, not a round-4 gap-closure change. Deleting it now, against the
installed 0.5.3, would remove the only refusal pc2img has for the registry
default-fallback route (`FeatureRegistry.match`'s unanchored fallback to `ScalarFieldFeature`
with a scalar-field name taken verbatim from PLY/E57 metadata).

## Steps

1. **Run the two still-PENDING spikes first** (`.planning/spikes/MANIFEST.md`):
   - **001 orphaned-override-hunt** — every pc2img override of a GSEGUtils `self._*` method
     that upstream stopped calling; each hit must be either absorbed (deletable) or an
     upstream gap. Includes the BC-GSEG-006 `extend_cache_path` drift re-derivation.
   - **004 blast-radius-phase14** — pc2img's full test suite (190+ tests as of this todo's
     filing) run against phase-14 with the override removed, as a weak confirmation that
     nothing else in the suite was silently relying on the override's stricter refusal.
2. **Bump the pin and re-lock**: `GSEGUtils >= 0.5.3, < 1.0` -> `GSEGUtils >= 0.6, < 1.0` in
   `pyproject.toml`; re-run `uv lock` and confirm the resolved GSEGUtils build is actually
   phase-14 / >= 0.6.0, not a cached 0.5.x wheel (spike 000's provenance gate is the pattern
   to reuse — assert `GSEGUtils.__version__` and the `grep -c 'self\._get_npy_path'` == 0
   fingerprint before trusting any test result).
3. **Delete the override**: remove `_get_npy_path`, `_get_meta_path`, and
   `_assert_within_cache_dir` from `src/pc2img/image_cache/disk_backed_image_store.py`. Keep
   `__delitem__`'s build-both-paths-before-delete ordering (05-16, commit `101c077`) —
   with the override gone, the base path builders themselves run upstream containment, so the
   atomicity property still holds, just enforced one layer down.
4. **Run the guard-sensitive tests** — every `escaping` / `refused` test in
   `tests/test_image_store.py` (the set 05-16 made demonstrably guard-sensitive via the
   throwaway no-guard mutation check). They must still pass after deletion, but **check
   the exception type BEFORE changing any `pytest.raises`**: confirm whether
   `GSEGUtils.errors.StoreKeyError` / `StoreContainmentError` subclass `ValueError` (spike 000
   observed both types on phase-14; pc2img's own tests currently assert `ValueError`). If they
   do not subclass `ValueError`, update the assertions to the new types and add a BC-NOTES
   entry recording the exception-type change (same class as entry 11/G11's request-time
   validation shift) — this is a real behavioral difference for any external catcher.
5. **Update the class docstring's threat-posture paragraph** one more time (05-16 already
   corrected it once for the current override's reachability; deletion changes the
   enforcement layer again, so the paragraph needs to say containment is now upstream, not
   downstream).

## Findings deferred here

Three round-4 review findings are superseded by this deletion rather than fixed in place —
fixing them in the override now would be work thrown away the moment this todo executes:

- **review-r2-a7c7f4e498a6** — "Every guarded path builder has a test that exercises its
  guard." The `_get_meta_path` guard branch is symmetric with `_get_npy_path` but has no test
  that reaches it directly (it is covered only transitively). Not worth a dedicated test for
  code this todo deletes.
- **review-r2-2b9426a42695** and **review-r2-6f4507d8c33f** were NOT deferred — 05-16 folded
  both into rewrites it was already doing for other reasons (see 05-16-SUMMARY.md
  "Disposition of Every Finding This Plan Touched"): review-r2-2b9426a42695 (bind the resolved
  path once per call) folded into the `_assert_within_cache_dir` parent-only-resolution
  rewrite (commit `f1a81cb`); review-r2-6f4507d8c33f (name the `.dat` memmap route in the
  docstring enumeration) folded into the rewritten route-enumeration paragraph (same commit).
  Both are `status: resolved` in 05-UAT.md with that evidence, not deferred to this todo.

### Round-4 gap-diff review (05-REVIEW.md, 2026-09-24) — deferred 2026-09-25

Owner decision 2026-09-25: hardening against constructed/escaping key names is out of current
scope. The six findings below all concern the containment override (or its tests) that step 3
deletes, so they become a **checklist for this adoption**, not Phase-5 work. Each is
`status: deferred` in 05-UAT.md, round `review-r3-*`:

- **review-r3-ffa2d1c2ca7c** (WR-01) — the add proving test only fails via offload; an
  unguarded *insertion* route writes `<key>.dat` outside the cache dir with the whole suite
  green. **Directly relevant to step 4**: after deleting the override, re-pin each route
  (insert / offload / load / delete) with its own test that asserts *no new file anywhere*
  outside the cache dir, not one sentinel name.
- **review-r3-e40af7956397** (WR-02) — the symlinked-entry delete assertion runs after pickling
  has de-linked the entries, so it cannot fail; also decide whether de-link-on-pickle is fine.
- **review-r3-ede9dcc0e91b** (WR-04) — `__setitem__` is unguarded while `__delitem__` refuses
  first, so a setter-inserted escaping key cannot be removed via the public API. Re-check
  under 0.6 whether upstream guards the setter.
- **review-r3-dda7a00b69cf** (WR-05) — containment docstrings overstate the invariant
  (parent-only resolve; reads served through cache-internal symlinks; `.tmp`/`.dat` writes
  follow planted symlinks). Moot once the override and its docstrings are deleted; restate the
  threat model wherever the guarantee is documented after adoption.
- **review-r3-2785f15bd78e** (WR-06) — `_assert_within_cache_dir(cache_dir / "..")` is
  admitted (lexical `is_relative_to` after parent-only resolve). Deleted with the helper.
- **review-r3-36e425b15be9** (IN-02) — the `embedded_traversal` delete case cannot escape
  because `cache/a` never exists; `mkdir` it in `_escape_layout` when re-pinning in step 4.

## Not this repo

The spike-000 differential probe found that `LazyDiskCache.offload` writes the `.dat` memmap
via `np.memmap(path, mode="w+")` non-atomically and follows a symlink at the target path —
outside phase-14's containment seam, and outside pc2img's override too (pc2img's override
never covered this route either, so this is not a regression this todo introduces or fixes).
This is a **GSEGUtils carry-out item**, not a pc2img change: `.dat` is the only artifact
family pc2img's real `generate()` pipeline actually writes (spike 000's ground-truth
instrumentation: `_store_entry` is never called; only `LazyDiskCache.offload` writes).
File or reference the corresponding GSEGUtils-side todo when this phase starts; do not attempt
to work around it from pc2img.
