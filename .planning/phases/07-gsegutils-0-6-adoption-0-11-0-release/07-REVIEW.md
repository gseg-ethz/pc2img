---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-02T10:12:39Z
depth: deep
files_reviewed: 16
files_reviewed_list:
  - .github/scripts/check_publish_gate.py
  - .github/scripts/preflight_ruleset_apply.py
  - .github/scripts/ruleset_lib.py
  - .github/scripts/test_check_publish_gate.py
  - .github/scripts/test_check_ruleset_drift.py
  - .github/scripts/test_preflight_ruleset_apply.py
  - .github/scripts/test_ruleset_lib.py
  - .readthedocs.yaml
  - RULESETS.md
  - pyproject.toml
  - src/pc2img/image_cache/disk_backed_image_store.py
  - src/pc2img/tiled_generator.py
  - tests/conftest.py
  - tests/test_image_store.py
  - tests/test_tiled_generator.py
  - uv.lock
findings:
  critical: 2
  warning: 5
  info: 5
  total: 12
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-10-02T10:12:39Z
**Depth:** deep
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Scope: `git diff 9bb6b51...HEAD` over the 16 listed files, read together with the upstream
GSEGUtils 0.6.0 sources installed in `.venv` (`disk_backed_store.py`, `paths.py`,
`lazy_disk_cache.py`) and the pc2img callers (`features/manager.py`, `core.py`).

Baseline: `pytest` gives 367 passed and 1 xfailed. `pytest .github/scripts` gives 120 passed.
`ruff check` and `ruff format --check` are clean. A green suite only shows that the existing tests
still pass. Every BLOCKER and most WARNINGs below were **reproduced by running code**. The
reproduction scripts are in the session scratchpad, and each finding states the command and what
it showed.

The main concerns:

1. **The tiled-regeneration "known limitation" is caused by pc2img, and pc2img can fix it.** The
   race is pinned as an upstream-only xfail, but pc2img's own fan-out triggers it: `generate()`
   pickles `self`, and so every tile's store, into every task. With the shipped code the reuse
   scenario fails 6 out of 6 runs. When each task carries only its own tile's generator it fails
   0 out of 12. As things stand, 0.11.0 would ship a tiled generator that breaks on its second
   `generate()` call at the default `n_jobs=-1` with two or more tiles.
2. **The overwrite route can serve a stale raster.** `del`/`pop`/`clear` now leave the codec pair
   on disk. `add_image_to_store` checks only tracking, not the disk. So delete, then recompute,
   then open a fresh store, and the fresh store serves the pre-overwrite raster.
3. **The stores of a tiled run can never be purged or overwritten.** Their owner pid is a loky
   worker that has already exited.
4. **The release-path hardening leaks in the same way it was meant to stop.** The publish gate
   misses local actions outside `.github/actions/<name>`. The ruleset preflight counts
   pull-request workflows whose `branches:`/`paths:` filters mean they never run for the gated
   branch.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: The tiled re-generation race comes from pc2img's own fan-out, has a local fix, and is shipped as an upstream-only xfail

**File:** `src/pc2img/tiled_generator.py:151` (with `tests/test_tiled_generator.py:89-123`)

**Issue:** `delayed(self._process_tile)(...)` pickles the bound method, which means the whole
`TiledPointCloudImageGenerator`. That includes `self.image_generators`: every tile's
`PointCloudImageGenerator` and its `DiskBackedImageStore`, plus every tile's point cloud. It does
this into **every** task. So on the second and later `generate()` calls, each worker unpickles
every tile's store, and each unpickle rebuilds that tile's `.dat` memmaps through the single
`<key>.dat.tmp` name. Several workers then race on the same files. The xfail docstring describes
this mechanism correctly ("every worker unpickles every tile's disk-backed store"). It then frames
the problem as "known limitation on GSEGUtils 0.6.0" and says an XPASS is the signal to "bump the
GSEGUtils pin". That framing leaves out the fact that pc2img decides what each task carries.

Measured with the xfail test's own scenario: two tiles, `n_jobs=2`, three `generate()` calls on one
instance, with `enable_caching=True` and a `cache_path`.

- Shipped code: **6 out of 6 rounds fail** with `BrokenProcessPool: A task has failed to
  un-serialize`. The failure is deterministic, not a rare race.
- The same scenario with `generate` monkeypatched so that each task receives only
  `self.image_generators.get(tile_id)` (plus picklable settings) through a module-level function:
  **0 out of 12 rounds fail**, and every `(tile_id, "range")` result is present.

`n_jobs=-1` is the default and `image_generators` exists precisely to be reused. So the 0.11.0
public tiled path fails on its second call for any run with two or more tiles on a machine with
two or more cores. `strict=False` also means CI stays green if the behaviour changes in either
direction.

**Fix:** Ship only the tile's own state to the worker, and stop pickling `self`:

```python
def _process_tile(image_gen, tile_id, tile_pcd, tile_kwargs, features,
                  proj_cls, interp_cls, proj_kwargs, interp_kwargs, cfg, img_res):
    if image_gen is None:
        if "lazy_disk_cache_config" in interp_kwargs:
            interp_kwargs = {**interp_kwargs,
                             "lazy_disk_cache_config": interp_kwargs["lazy_disk_cache_config"].extend_cache_path(tile_id)}
        image_gen = PointCloudImageGenerator(
            pcd=tile_pcd, proj=proj_cls(**tile_kwargs, **proj_kwargs), interp=interp_cls(**interp_kwargs),
            lazy_disk_cache_config=cfg.extend_cache_path(tile_id), img_res=img_res)
    return tile_id, image_gen, image_gen.generate(features)

# in generate():
delayed(_process_tile)(self.image_generators.get(t.tile_id), t.tile_id, t.tile_pcd, t.tile_kwargs, features,
                       self.proj_cls, self.interp_cls, dict(self._proj_kwargs), dict(self._interp_kwargs),
                       self._lazy_disk_cache_config, self._img_res)
for t in self.pcd_tiles
```

Then turn the xfail into a plain passing regression test, and keep GSEGUtils#82 as the upstream
fix for the fixed `.tmp` name. Note that the existing `_process_tile` extends the interpolation
cache path only for workers, and the sketch above does the same. Keep that behaviour.

### CR-02: The overwrite misses keys that are untracked but still on disk, so a fresh store serves the pre-overwrite raster

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:130-131`

**Issue:** `add_image_to_store` purges only `if img_name in self`, and upstream `__contains__`
reports tracking only. In 0.11, `del store[k]`, `pop` and `clear` drop tracking but leave
`<k>.npy` + `<k>.meta.json` on disk. The class docstring itself says such a key "is re-adopted on
the next read". So for a key that `store[k]` would serve, `add_image_to_store` decides it is *not*
an existing key and skips the purge. The new raster lives in `<k>.dat`. The old codec pair
survives, and any store reopened over the directory (the warm-restart pattern) adopts and serves
the **old** raster as a cache hit. Feature names are the cache key, so nothing downstream can tell
the difference.

Reproduced:

```
s.add_image_to_store("range", zeros); s.offload_image_data_to_disk("range")
del s["range"]                      # 0.10.x: unlinked the pair; 0.11: tracking only
s.add_image_to_store("range", ones) # recompute -> no purge (key untracked)
this store serves: 1.0
files: ['range.dat', 'range.meta.json', 'range.npy']
fresh store serves: 0.0 (expected 1.0 = replacement)
```

In 0.10.x the deleted `__delitem__` override unlinked the pair, so the same sequence gave a cache
miss and a recompute. BC-P2I-027 documents that `del` now only drops tracking. It does not document
that a later overwrite through the store's own overwrite verb leaves stale data behind. Upstream
`purge` deliberately treats "untracked but on disk" as present (its D-02). The pc2img wrapper's
membership test throws that away. pc2img's own pipeline never calls `del`, so the trigger is a
caller of the publicly exported store. That is exactly the caller BC-P2I-027 addresses.

**Fix:** Purge whatever exists, tracked or not. `purge` raises `KeyError` only when the key is
neither tracked nor on disk:

```python
from contextlib import suppress
...
get_npy_path(self.cache_dir, img_name)
_assert_image_shape(img_data)
with suppress(KeyError):
    self.purge(img_name)
self.add_data_to_store(...)
```

Add a regression test for del, then re-add, then a fresh store serving the replacement (or a cache
miss).

## Warnings

### WR-01: Every tile store is permanently un-purgeable and un-overwritable after a tiled run

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:131`, `src/pc2img/tiled_generator.py:178-187`

**Issue:** Tile generators, and therefore their stores, are constructed inside loky workers.
Upstream stamps `_owner_pid` at construction and refuses `purge` from any other pid. Once the run
returns, every store in `tiled.image_generators` belongs to a worker pid that the caller cannot get
back to. Reproduced with two tiles and `n_jobs=2`: parent pid 148559, store owner pid 148607.
`store.purge("range")` raises `StorePurgeRefusedError`, and so does
`store.add_image_to_store("range", ...)` (an overwrite), which worked in 0.10.x. In later
`generate()` calls the outcome depends on whether loky happens to hand the task back to the
original worker pid, so the same call can succeed or fail from run to run. The docstring and
BC-P2I-027 state the generic rule, but neither says that it covers *every* store the tiled
generator produces. As a result `purge`, the only removal verb, has no supported caller for tiled
caches.

**Fix:** Either build each tile's generator in the parent, so the owner is the long-lived process
(this combines naturally with CR-01's per-tile shipping; workers only write, which upstream
permits), or document on `TiledPointCloudImageGenerator` that tile stores cannot be purged or
overwritten and give a cleanup route (for example `shutil.rmtree` of the tile sub-directory).

### WR-02: The publish gate misses local actions outside `./.github/actions/<name>/`

**File:** `.github/scripts/check_publish_gate.py:54-56, 88-104, 149`

**Issue:** The new composite-action coverage reads only `.github/actions/*/action.y{a,}ml`, and it
recognises only `uses:` values that begin with `./.github/actions/`. GitHub runs **any** in-repo
directory with an `action.yml` as a local action. Reproduced on a scratch tree where `ci.yml` has
three jobs whose only step is a local action that runs `uv publish dist/*`:

- `uses: ./.github/actions/group/pub` (a nested directory that the `*/` glob does not reach)
- `uses: ./tools/pub2` (a local action outside `.github/actions`)
- `uses: ./.github/actions/../../tools/pub2` (not normalised)

Result: `check_publish_gate: OK ... exit 0`. The module docstring says "A publish step can be
reached two ways", which is incomplete, and
`test_is_local_action_reference_accepts_only_local_actions_directory_paths`
(`test_check_publish_gate.py:649`) pins `./other/ship` as "not a local action", which locks the
bypass in. Impact is limited because PyPI trusted publishing still binds to the workflow file and
environment, but this is the hardening the phase claims to deliver.

**Fix:** Treat every `uses:` starting with `./` as a local action. Resolve it with
`(root / uses[2:]).resolve()`, refuse anything outside `root`, and read
`<dir>/action.yml|action.yaml` directly instead of globbing a single level. Key the flagged set by
resolved directory, not by basename. A `./` reference whose directory holds no readable action
file should be a violation (fail-closed). Update the test at line 649.

### WR-03: The ruleset preflight still counts pull-request workflows that never run for the gated branch

**File:** `.github/scripts/preflight_ruleset_apply.py:156-176, 239-245`

**Issue:** The change filters on event *names* only. A workflow with
`on: pull_request: {branches: [main]}` (or a `paths:` filter, or `types: [closed]`) never reports a
check on a pull request into `develop-gsd`. Its job name still counts as matchable for
`develop.json`, which is the same "required context nothing produces, branch unmergeable" failure
the change was written to refuse. Reproduced by calling `matchable_job_names` on a directory
holding `ci.yml` plus a `pull_request: {branches: [main], paths: ['nothing/**']}` workflow: the
returned set includes `'Main only check'`.

**Fix:** Pass the payload's `conditions.ref_name.include` (already read by `target_branch`) into
`matchable_job_names`. Skip a workflow whose `pull_request`/`pull_request_target` mapping has a
`branches` list that does not match the target branch (or a `branches-ignore` list that does). At
minimum, print a warning for `paths`/`paths-ignore`/`types` filters, because a required
path-filtered check blocks unrelated pull requests.

### WR-04: The `[tool.uv.sources]` nvidia index bindings have no effect; the RAPIDS packages lock from pypi.org

**File:** `pyproject.toml:113-138`, `uv.lock`

**Issue:** The comment block says the explicit nvidia index "contains dependency-confusion on the
RAPIDS names to the official index", and this phase's edit adds "which is why only those names
keep an index binding". In the committed lock, every RAPIDS package, including the directly bound
`cudf-cu12` (`uv.lock:315`) and `cuspatial-*`, has
`source = { registry = "https://pypi.org/simple" }`. `grep -c pypi.nvidia.com uv.lock` returns
`0`, and the base commit's lock also returned `0`. These names reach the project only through
`pchandler[cudaXX]`, and uv applies `tool.uv.sources` only to the project's own declared
dependencies. The comment at line 125 says "verify at `uv lock` ... the documented fallback is to
name them directly in the cuda extras". The verification shows the bindings did not take, and the
fallback was not applied. The trimmed list is therefore justified by a mechanism that is not
working.

**Fix:** Either name `cudf-cuXX`/`cuspatial-cuXX` directly in the `cuda11`/`cuda12` extras (the
documented fallback) so that the sources bind, then re-lock and confirm the `pypi.nvidia.com` URLs
appear. Or, if PyPI-hosted RAPIDS wheels are acceptable, delete the index and sources block and
correct the comment. Do not keep a claimed supply-chain control that is not working.

### WR-05: The overwrite docstring misstates the purge-refusal conditions, and setter-inserted entries can no longer be overwritten

**File:** `src/pc2img/image_cache/disk_backed_image_store.py:110-116`

**Issue:** The docstring reads "`StorePurgeRefusedError` ... for a symlinked adopted entry whose
target lies outside the cache directory **and** when the calling process is not the one that
constructed the store". These are independent conditions ("or"); as written, a reader concludes
that both must hold. It names the foreign-artefact subclass but omits
`StorePurgeAliasedArtefactError`, the second subclass that upstream raises for an in-cache link to
another key's artefact. It also omits a third refusal trigger that applies to pc2img's own
documented limit. Reproduced: an entry inserted with
`store["range"] = DiskBackedImageData(arr, cache_path=<outside>)` makes
`add_image_to_store("range", ...)` raise `StorePurgeForeignArtefactError` every time. That key can
no longer be overwritten through the store's overwrite verb, whereas 0.10.x allowed the overwrite.
BC-P2I-027 lists only the symlink case.

**Fix:** Reword to "...raises the `StorePurgeRefusedError` family when the calling process did not
construct the store, when a built artefact or a live entry's own `cache_path` resolves outside the
cache directory (`StorePurgeForeignArtefactError`), or when a built artefact links to another key's
artefact (`StorePurgeAliasedArtefactError`)". Add the setter-inserted-entry case to BC-P2I-027.

## Info

### IN-01: `integration_id` is dropped unconditionally, unlike every other read-filled key

**File:** `.github/scripts/ruleset_lib.py:550-575`

**Issue:** Rule (d) drops a read-filled key only when the committed payload is silent about it.
Rule (c) drops `integration_id` from both sides unconditionally. If the live ruleset has been
pinned to a different app (an edit made outside the apply), or a future payload deliberately pins
`15368`, the drift check cannot see it. That field decides which app may satisfy a required check.
This behaviour predates the phase, but the phase's docstring edit re-affirms it.

**Fix:** Drop only `null`, absent and `15368` live values when the committed side is `null`, and
compare in every other case.

### IN-02: The `PointCloudTile` docstring's list of illegal ids is incomplete

**File:** `src/pc2img/tiled_generator.py:34-42`

**Issue:** Measured `is_valid_store_key`: control characters (`"a\x00b"`, `"a\nb"`, `"a\tb"`) are
refused as well, and the docstring does not list them. Because the docstring states upstream's
rule, it should either quote the rule completely or point to it.

**Fix:** Add "a control character", or replace the enumeration with "anything
`GSEGUtils.lazy_disk_cache.is_valid_store_key` rejects".

### IN-03: Side item (b), the RULESETS.md "Five fields" bullet: consistent, but it gives no route for changing these fields

**File:** `RULESETS.md:32-35`

**Issue (checked):** Leaving out "Change them in the web UI if you need to" was correct, because
it contradicted "Never edit rulesets in the web UI". The remaining bullet matches `ruleset_lib`
(`PULL_REQUEST_READ_FILLED_KEYS` + `STATUS_CHECKS_READ_FILLED_KEYS`, dropped only when the
committed side is silent). Two gaps remain:

1. It does not say how a maintainer *should* change one of these fields. The only route that
   respects the web-UI ban is to set the field in the payload, and the bullet implies that only
   indirectly ("unless a payload sets one").
2. "Not governed by the apply" depends on GitHub keeping omitted fields on `PUT`. The repo's own
   `SENDABLE_KEYS` comment says the API "does not document whether omitted ones are preserved or
   reset".

**Fix:** Change the last sentence to "GitHub fills them on read and the drift check ignores them;
to govern one, set it in the payload." Optionally record that `PUT` semantics for omitted keys
were not verified.

### IN-04: Side item (a), the uv.lock package count: the committed lock is not stale; the difference is index drift. CI also never tests the versions a pip install resolves

**File:** `uv.lock`, `pyproject.toml:34-37`

**Issue (checked):** A fresh `uv lock` in a clean clone at `5ee3c80` resolves 138 packages. The
only new name is `cloudpickle`, and the only package that depends on it is **joblib 1.6.0**, which
the fresh lock picks under `joblib ~= 1.5`. The committed lock holds joblib 1.5.3, which has no
dependencies. The other differences are routine upgrades (alabaster, certifi, scipy
1.18.0→1.18.1, pydantic 2.13.4→2.13.5, …). `uv lock --check` is clean, so no transitive dependency
is missing.

Related observation: numpy locks at 2.2.6 in both locks because pchandler's `cuda11`/`cuda12`
extras cap `numpy<2.3` and a universal lock picks one numpy version for every fork. A plain
`pip install pc2img` resolves numpy 2.3.x and joblib 1.6.x (whose loky/cloudpickle split touches
the tiled path), and CI never runs those versions.

**Fix:** None required for the lock. Consider a CI job that tests the highest resolvable versions
(`uv sync --upgrade` or `--resolution highest` without the lock), or declare the numpy fork split.

### IN-05: Side item (c): agent and planning docs still state `numpy ~= 2.0`

**File:** `.claude/CLAUDE.md:68`, `.planning/codebase/STACK.md:50`

**Issue:** pyproject now pins `numpy >= 2.2, < 2.4`. Neither file ships. Noted only, as requested.

**Fix:** Update both at the next `/gsd-map-codebase` refresh.

## Checked and clean

- **`.readthedocs.yaml`.** Measured with the project's `[tool.setuptools_scm]` settings. A
  depth-1 clone that had `git fetch --tags --force` run but was never unshallowed resolves to
  `0.0.post1`, even with `v0.10.4` fetched, so the post-install `startswith('0.0.')` assertion
  catches exactly the failure mode the comment describes. A full clone resolves to
  `0.10.4.post1`. The floating `v0` tag does not match `--match 'v[0-9]*.[0-9]*.[0-9]*'`. The
  conditional unshallow, the forced tag fetch and the post-install checks are correct.
- **`tests/conftest.py` `_isolate_tempdir`.** It is restored by `monkeypatch`, does not leak into
  loky workers (they get a fresh interpreter), and the test that sets `tempfile.tempdir` itself
  correctly overrides it.
- **`tests/test_image_store.py`.** The escape-route matrix compares a snapshot of the whole tree
  before and after on every route, and the overwrite tests act as genuine sensors (each fails if
  `purge` is replaced by `del`). One gap: no test covers CR-02's untracked-orphan overwrite.
- **Publish-gate composite fixpoint.** It terminates on reference cycles, and an unreadable action
  fails closed. Both are correct within the `.github/actions/<name>` scope, apart from WR-02.
- **`ruleset_lib` rule (d).** The conditional drop matches its docstring and the RULESETS.md
  bullet.

---

_Reviewed: 2026-10-02T10:12:39Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
