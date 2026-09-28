---
spike: 000
name: absorption-test
type: standard
validates: "Given pc2img's Phase 5 escape corpus (commit 03eb715) and GSEGUtils phase-14 HEAD with pc2img's _get_npy_path/_get_meta_path override REMOVED, when every corpus input is run through every disk-touching route, then every input is still refused upstream — proving the override was absorbed and is deletable"
verdict: VALIDATED
related: [001-orphaned-override-hunt, 004-blast-radius-phase14]
tags: [gsegutils, containment, wr-02, disk-backed-store, absorption, security]
---

# Spike 000: Absorption Test

## What This Validates

**Given** pc2img's Phase 5 escape corpus — every input the `_get_npy_path` /
`_get_meta_path` override was written to stop (commit `03eb715`, WR-02) —
**when** it is run against GSEGUtils phase-14 HEAD with that override removed,
**then** every input must still be refused, by `StoreKeyError` (lexical layer)
or `StoreContainmentError` (resolved layer).

Interpretation fixed before running, so a green could not be misread:

- **ALL REFUSED** → absorption confirmed, the override is provably redundant.
- **ANY SURVIVOR** → a GSEGUtils phase-14 *requirement gap*, not a pc2img patch.

## Import Provenance

The experiment is invalid if the GSEGUtils under test is the installed 0.5.3
wheel — 0.5.3 still routes every disk-touching route through
`self._get_npy_path`, so the override would be live and everything would be
refused for the wrong reason. `provenance.py` refuses to let any assertion run
until four independent checks pass, and every script prints them first:

| check | value |
|---|---|
| `GSEGUtils.__file__` | `/home/nixton/gsd-workspaces/pchandler/30_GSEGUtils/src/GSEGUtils/__init__.py` |
| `GSEGUtils.__version__` | `0.5.0.post28` |
| `disk_backed_store.py` | resolves under the phase-14 workspace |
| `grep -c 'self\._get_npy_path'` | **0** (0.5.x fingerprint would be 4) |
| `pc2img.__file__` | `/scratch/31_pc2img/src/pc2img/__init__.py` |

The override is removed **without editing pc2img source**: `NoGuardImageStore`
rebinds both path builders to the base implementations, and installs a tripwire
on `_assert_within_cache_dir` that raises if pc2img's guard is ever reached — so
a refusal can never be credited to the code under test.

## How to Run

```bash
export PYTHONPATH=~/gsd-workspaces/pchandler/30_GSEGUtils/src
.venv/bin/python .planning/spikes/000-absorption-test/test_absorption.py
.venv/bin/python .planning/spikes/000-absorption-test/test_differential.py
.venv/bin/python .planning/spikes/000-absorption-test/test_symlink_and_groundtruth.py
.venv/bin/python .planning/spikes/000-absorption-test/test_dat_writer.py
```

## Results

### 1. Escape corpus — 12/12 refused, override removed

3 spellings × 4 routes (insert, mapping-setter, setter+delete, insert+offload).
Every cell refused, and an independent sentinel check confirmed no outside file
was created, overwritten, or deleted in any cell.

| key | refused by |
|---|---|
| `../victim` | `StoreKeyError` (lexical) — all 4 routes |
| `<tmp>/victim` (absolute) | `StoreKeyError` (lexical) — all 4 routes |
| `a/../../victim` | `StoreKeyError` (lexical) — all 4 routes |

False-positive bound: all 6 realistic feature names from the Phase 5
characterization test (`range`, `rrim_pack_(range,r16,d8,z1.2345678)`,
`hillshade_range_315_45`, `norm_(range,2,98)`, `scalar_field_intensity`,
`grad_range_px0.5`) still round-trip unchanged. Absorption does not over-refuse.

**→ ABSORPTION CONFIRMED for the corpus.**

### 2. Surprise: the corpus never reaches the resolved layer

Every refusal came from the **lexical** rule (`validate_store_key`, which
rejects any key containing a path separator). `paths._assert_contained` — the
resolved check, and the thing pc2img's override actually was — is never
exercised by the corpus. So "the corpus passes" is weaker evidence than it
looks, which is why the differential probe below was added.

### 3. Differential probe — the one class where the guards diverge

A key that escapes **without a path separator** sails past the lexical rule.
The canonical instance is a symlink inside the cache directory whose name is a
legal store key. Measured, per artefact, per writer:

| artefact | phase-14 alone | pc2img guard live |
|---|---|---|
| `<key>.npy` | ALLOWED — symlink replaced (atomic write), sentinel INTACT | refused (`ValueError`), sentinel INTACT |
| `<key>.meta.json` | ALLOWED — symlink replaced, sentinel INTACT | ALLOWED — symlink replaced, sentinel INTACT |
| `<key>.dat` | **ALLOWED — write FOLLOWED the symlink, sentinel OVERWRITTEN** | **ALLOWED — write FOLLOWED the symlink, sentinel OVERWRITTEN** |

The `.npy` divergence is cosmetic: phase-14 permits-and-contains where pc2img
refused, and the outside file survives either way because the codec writes via
atomic replace, which swaps the symlink inode instead of following it.

The `.dat` row is a real hole — **and pc2img's override never covered it
either.** It is damaged identically with the guard live. So it is not a
regression from removing the override; it is a pre-existing gap in both.

### 4. Ground truth (folded spike 002) — the load-bearing result

A real `PointCloudImageGenerator.generate()` run, cache directory listed
verbatim:

```
sorted(p.name for p in cache_dir.iterdir())
['hillshade_range_315_45.dat', 'range.dat']
```

No `.npy`. No `.meta.json`. Instrumenting the run:

```
files written by generate()   : ['range.dat']
paths._build calls            : 5  [('triangles','.npy'), ('simplices','.npy'),
                                    ('verts','.npy'), ('bary','.npy'), ('range','.npy')]
paths._assert_contained calls : 5
DiskBackedStore._store_entry  : 0
```

`_store_entry` is **never called**. pc2img's real pipeline does not write the
store codec pair at all — the `.npy`/`.meta.json` path builders, and therefore
pc2img's override on them, do not run during `generate()`. Artefacts reach disk
through `LazyDiskCache.offload` (`lazy_disk_cache.py:479`), which writes the
`.dat` memmap via `np.memmap(path, mode="w+")` (`:277-278`) — not through
`paths._build`, not through `_assert_contained`, and not atomically.

The `.dat` *name* is still contained transitively: `add_data_to_store`
(`disk_backed_store.py:875`) builds `paths.get_npy_path(cache_dir, key)` —
containment-checked — and `LazyDiskCache._init_from_config` (`:231`) derives the
memmap path as `cache_path.with_suffix('.dat')`. So a key cannot escape into a
`.dat`; measured, escaping keys are refused at the store door by `StoreKeyError`.
The residual `.dat` exposure is symlink-following only, which requires an
attacker who can already write inside the cache directory.

## Investigation Trail

1. Extracted the corpus from `git show 03eb715 -- tests/` rather than
   paraphrasing it — 3 key spellings, 4 routes, plus the 6-name false-positive
   bound.
2. Built the provenance gate first. The brief flagged 0.5.3 as a false-green
   risk; the installed wheel is indeed 0.5.3, so this was not hypothetical.
   `PYTHONPATH` to the phase-14 worktree, verified by fingerprint.
3. Ran the corpus → 12/12 refused. Nearly stopped here.
4. Noticed every refusal was lexical, so the corpus proves nothing about the
   resolved layer that pc2img's override actually implemented. Added the
   differential probe.
5. Probe found the symlink divergence: pc2img refuses, phase-14 allows —
   sentinel intact. "Allowed but undamaged" is not a finding until you know why,
   so each artefact was probed separately.
6. `.dat` came back DAMAGED — under phase-14 **and** under the live guard. That
   reframed it from "regression" to "pre-existing gap in both".
7. Instrumented a real `generate()` to find out which writer matters. Result:
   only `.dat` is written, `_store_entry` never fires. The containment work on
   both sides guards the artefact family pc2img's pipeline does not write.
8. One probe (constructing `DiskBackedImageData` directly and setting `.name`)
   wrote nothing — wrong lever, inconclusive, discarded rather than reported.
   Reachability was settled instead via the store door, by measurement.

## Verdict

**VALIDATED — absorption confirmed. The override is redundant and deletes
cleanly.** Removing it loses exactly one behaviour: a stricter refusal of a
symlinked `<key>.npy`, which phase-14 already renders harmless via atomic
replace.

**Carry-out finding for GSEGUtils (not a pc2img item):** `LazyDiskCache.offload`
writes the `.dat` memmap non-atomically and follows a symlink at the target
path, outside the phase-14 containment seam. Low severity — it needs pre-existing
write access to the cache directory, and no store key can reach it — but it is
the artefact family that pc2img actually writes, so it is the one worth closing.
