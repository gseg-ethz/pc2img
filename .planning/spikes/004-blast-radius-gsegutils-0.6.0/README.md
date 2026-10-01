---
spike: 004
name: blast-radius-gsegutils-0.6.0
type: standard
validates: "Given pc2img's full test suite and the PyPI GSEGUtils 0.6.0 wheel, when the DiskBackedImageStore overrides are removed (simulated in-process), then every remaining failure is traced to a cause: rename, semantic change, or something else"
verdict: VALIDATED
related: [000-absorption-test, 001-orphaned-override-hunt]
tags: [gsegutils, regression, blast-radius, 0.6.0]
---

# Spike 004: Blast Radius — full suite vs GSEGUtils 0.6.0 (overrides removed)

Run during Phase 7 research (D-04, D-06). Original name `blast-radius-phase14`; target changed to
the released wheel (D-05). The tracked tree is **not edited**: `spike004_plugin.py` is loaded
with `-p` and mutates the already-imported `DiskBackedImageStore` class in-process at
`pytest_configure`, after asserting provenance inside the test process.

## How to run

```bash
# scratch venv as in spike 001 README (+ ruff~=0.15, pre-commit, pytest-cov so tests/test_hygiene.py runs)
export PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=/scratch/31_pc2img/src:/scratch/31_pc2img/.planning/spikes/004-blast-radius-gsegutils-0.6.0 \
  SPIKE004_ARM=A /tmp/s001/bin/python -m pytest -p spike004_plugin -p no:cacheprovider -q --tb=short -W ignore
# SPIKE004_ARM=B adds a TEST-ONLY shim re-adding _get_npy_path/_get_meta_path over the public free functions
# Baseline (no plugin; tree as shipped, 0.6.0): `python -m pytest -p no:cacheprovider -q`
```

## Results (286 tests)

| arm | what | result |
|---|---|---|
| baseline, locked env (`.venv`, GSEGUtils 0.5.3) | as shipped | 286 passed |
| baseline, 0.6.0 wheel, tree unmodified | the discuss-time data point | **30 failed / 256 passed** (reproduced). 26 fail with `AttributeError: 'super' object has no attribute '_get_npy_path'` at `disk_backed_image_store.py:120`; 4 fail with `StoreKeyError` raised **at the `store[key] = ...` setter** inside the test (outside any `pytest.raises`) |
| **A**: overrides removed, `add_image_to_store` migrated to `purge`, no shim | the migration as D-08/D-09 prescribe | **12 failed / 274 passed**; all 12 are in `tests/test_image_store.py` |
| **B**: A + test-only `_get_*_path` shim | separates renames from semantic breaks | **7 failed / 279 passed** |

The 18 tests that fail only on the unmodified tree and pass in arm A include all five RRIM
end-to-end `generate()` tests, the six `test_containment_guard_accepts_realistic_feature_names`
cases and the three `test_escaping_key_add_refuses_*` cases: they depended on the dangling
`super()` call, not on any behaviour.

### The 12 arm-A failures, traced

| test | cause | class |
|---|---|---|
| `test_overwrite_does_not_leave_stale_on_disk_raster` | calls `store1._get_npy_path` (line 111) | rename |
| `test_delete_absent_key_raises_keyerror_and_is_a_disk_no_op` | `_get_npy_path` at 171/172/182/183 (passes in B unchanged) | rename |
| `test_failed_delete_preserves_codec_pair_and_both_stores` | `_get_npy_path` at 211/212/218/219 (passes in B unchanged) | rename |
| `test_failed_overwrite_leaves_existing_entry_and_codec_pair_intact[codec_offloaded]` | `_get_npy_path` at 450/451/459/460 (passes in B unchanged) | rename |
| `test_successful_overwrite_serves_the_replacement_after_offload_and_reload` | `_get_npy_path` at 480/481 (passes in B unchanged) | rename |
| `test_delete_purges_on_disk_codec_pair` | rename **and** `del store[k]` no longer unlinks (B: `assert not ...exists()` fails) | semantic (D-08) |
| `test_adopted_key_delete_purges_shared_pair` | same | semantic (D-08) |
| `test_symlinked_cache_entry_is_served_and_unpickles` | `del store2[k]` no longer removes the link; also `_get_npy_path` at 548/553 | semantic (D-08) |
| `test_escaping_key_delete_refuses_and_leaves_outside_file_intact[x3]` | `store[key] = DiskBackedImageData(...)` now raises `StoreKeyError` at set time, so the escaping key can never be tracked and the delete is unreachable | semantic (upstream guards the setter) |
| `test_refused_overwrite_leaves_existing_entry_intact` | same setter refusal | semantic (upstream guards the setter) |

Pure renames = 5, semantic = 7 (arm B). No failure outside `tests/test_image_store.py`; no
failure in `src/` logic other than the store; nothing "unexplained".

### Instrumentation

The plugin counted `purge()` calls during the whole suite: **1** in arm A and **2** in arm B
(every one triggered by the `add_image_to_store` overwrite path; arm A reaches fewer because the
other overwrite tests fail earlier on the removed `_get_npy_path`). The
pipeline itself never triggers an overwrite (no `BaseFeatureStrategy` uses `fetch`, and
`FeatureManager.request` skips cached names), so `purge` is reachable only through direct
`add_image_to_store` callers.

### What the suite cannot see

The suite has **no loky/`n_jobs>=2` tiled test** (`tests/test_tiled_generator.py` is
settings-level only), so it is blind to the concurrent-reload race recorded in spike 001 §E.
Migrated store + 0.6.0 + scratch overlay: first `generate()` OK (n_jobs=2), second `generate()`
with more features OK, **third `generate()` on the same tiled generator fails**
(`BrokenProcessPool`, 3/3 runs); the same script on 0.5.3 passes 3/3.

## Verdict

**VALIDATED** — the blast radius of removing the overrides is confined to `tests/test_image_store.py`
(12 tests: 5 renames to the public free functions, 7 semantic rewrites). The weak-confirmation
claim "nothing else was load-bearing" holds for the suite as written; the suite's own blind spot
(loky tiled re-generation) is a separate finding.
