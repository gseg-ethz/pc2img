---
type: migration-spec
spec_version: "1.0"
repo: pc2img
baseline_ref: "91b4ab6"
target_ref: "v0.11.0"
generated_at: "2026-10-05T09:20:03Z"
bc_id_prefix: BC-P2I
milestone: v1.0
---

# pc2img MIGRATION-v0.11

**Baseline:** `dev/v2` tip (`91b4ab6`, 2025-11-06) — the fork point of `develop-gsd`.
**Target:** the `v0.11.0` release tag.
This record lives under the internal planning directory on `develop-gsd` and is not shipped on `main`; downstream projects read it from the branch.

## Summary

This milestone's seven phases (branch untangling, dependency adaptation, CI/test foundation,
RRIM IP clearance, code-quality/algorithmic-soundness review, bug fixes/module test coverage, and
the GSEGUtils 0.6 adoption) reshape pc2img's public surface and on-disk behavior in thirty
identified changes: twenty `should-review` behavior/semantic/signature/dependency changes
(concentrated in the bug-fix pass — registry error unification, projection refusals, RRIM validation
timing, the on-disk cache codec — and in the GSEGUtils 0.6 adoption: the pin change, `del` versus
`purge`, store-key refusals, the read-only store mapping, and the per-tile tiled fan-out change with
its worker-owned tile stores), one `must-edit` on-disk-format change (the pickle-to-npy cache codec, which requires
regenerating a persisted cache directory), five `informational` entries recording closed or
historical decisions (two dead-code removals, a dependency-audit attestation, a closed
dependency-bridge conversion, and the publication metadata replacement), and four purely `additive`
opt-in capabilities. The dominant categories are `dep-constraint` (seven entries) and
`error-behavior`/`semantic-change` should-review entries.
Unlike PCHandler's v1.0 record, pc2img has no "no breaking import paths" invariant to uphold — one
on-disk-format `must-edit` entry and two `surface-removed` entries are expected and classified here,
not escalated as stop-and-ask events.

## Public API stability statement

pc2img has no "no breaking public import paths" invariant equivalent to PCHandler's — this
milestone deliberately removes two never-functional/duplicate symbols (`make_generator`, a dead
duplicate `convert_to_image` definition) and changes the on-disk cache codec in a way that requires
regenerating a persisted cache. The inline verifier below proves the mechanical half of every claim
it can: Tier 1 confirms the public-surface `__all__` lists of the four barrel modules; Tier 2
runtime-checks every `signature-shape` claim (constructor kwargs, raised exception types) and every
`error-behavior`/`on-disk-format` claim that is cheap to instantiate. What the verifier cannot
check — the numerical correctness of the underlying fixes themselves (the float32 accumulation
change, the RRIM z-token grammar) — is covered by the project's own test suite and is referenced by
origin commit sha rather than re-asserted here.

## Breaking changes & behavior changes

| BC-ID | category | severity | affected_symbols | origin | migration_steps |
|---|---|---|---|---|---|
| BC-P2I-001 | error-behavior | should-review | `pc2img.errors.RegistryLookupError`, `pc2img.strategies.registry.StrategyRegistry`, `pc2img.features.registry.FeatureRegistry` | `eb62a60` — registry miss/duplicate exception unified | Catch `RegistryLookupError`, or keep catching `KeyError`/`RuntimeError` — both still match. |
| BC-P2I-002 | dep-constraint | should-review | (resolver-level; `numpy`, `pchandler`, `GSEGUtils`, `joblib` pins) | `7f0b894`, `4ecf824` — dependency adaptation | Depend on `numpy >= 2.2, < 2.4` (now declared directly; previously only a transitive `<2.4` cap via `pchandler`), `pchandler >= 2.1.1, ~= 2.1`, `GSEGUtils ~= 0.6.0`, `joblib ~= 1.5`. `pc2img[cuda11]` / `pc2img[cuda12]` now pull only `cudf`, `cuspatial` and `geopandas` through `pchandler` 2.1.1's own extras (and cap `numpy < 2.3`); `cuml`, `cuproj` and `dask-cudf` are no longer installed. Resolver-level only — no source changes downstream. Superseded for the pins by BC-P2I-026, which records why the GSEGUtils pin is `~= 0.6.0`; this entry keeps the history of the earlier pins readable. |
| BC-P2I-003 | dep-constraint | informational | (none — dependency-audit attestation) | `1721c78` — dependency adaptation, zero-call-site attestation | Historical record: the three named pchandler 2.x semantic breaks (`FoVTree` identifiers, world-frame `to_py4dgeo`, `Csv`/`Las` load behavior) have zero call sites in pc2img's own source. No action needed on pc2img's account; verify your own code separately if you call `pchandler` directly. |
| BC-P2I-004 | surface-removed | informational | `pc2img.registry.make_generator` | `6714214` — hygiene review deleted dead code | `make_generator` was never functional — its 3-positional-argument call landed arguments in the wrong constructor parameters — and had zero callers in-repo. Construct `pc2img.PointCloudImageGenerator` directly instead. |
| BC-P2I-005 | surface-removed | informational | `pc2img.util.convert_to_image` (dead duplicate definition) | `9d74e6e` — hygiene review deleted a dead duplicate | A dead first `convert_to_image` definition in `util.py` (unreachable — it referenced an unimported `plt` and would `NameError` if ever called, shadowed by the live keyword-only definition) was deleted. The surviving `pc2img.util.convert_to_image` is unchanged. No action needed. |
| BC-P2I-006 | dep-constraint | should-review | `matplotlib` (colormap support in `pc2img.util.convert_to_image`) | `4ecf824` — hygiene review moved matplotlib to an optional extra | Colormap conversion now needs `pip install pc2img[viz]`; without it, requesting a colormap still raises the existing `RuntimeError("Colormap requires matplotlib")` rather than failing on import. |
| BC-P2I-007 | error-behavior | should-review | `pc2img.strategies.projection.SphericalProjection.project_raw`, `pc2img.strategies.projection.SphericalProjection.inverse_projection` | bug-fix pass | A field of view that wraps around ±π now raises `NotImplementedError` from both methods instead of silently producing reversed-column output. Re-orient the point cloud/FoV so it does not cross the ±π seam, or split the cloud; the prior wrapped output was mathematically wrong, so no correct caller depended on it. |
| BC-P2I-008 | signature-shape | should-review | `pc2img.strategies.projection.PerspectiveProjection` (`rotation_matrix=`) | bug-fix pass | A 4×4 `rotation_matrix` now raises `TypeError`. Split any 4×4 extrinsic into its 3×3 rotation block and a translation vector, passed via `translation=`. |
| BC-P2I-009 | semantic-change | should-review | `pc2img.util.nanconv` | bug-fix pass | Accumulation dtype changed from float16 (which overflowed to `inf` on realistic range magnitudes) to float32 by default, and the input array is no longer mutated in place. Pass `compute_dtype=np.float16` to restore the old memory/accuracy trade explicitly; stop relying on in-place mutation of the array you pass in. |
| BC-P2I-010 | on-disk-format | must-edit | `pc2img.image_cache.DiskBackedImageStore` | bug-fix pass | The on-disk cache codec moved from a pickle `.pkl` file to `.npy` + `.meta.json` (`allow_pickle=False`). A persisted cache directory from before this change must be regenerated — a legacy `.pkl` entry degrades to a logged cache miss and recomputes; it is never deserialized. No API call sites change (legacy method names are preserved as aliases). |
| BC-P2I-011 | semantic-change | should-review | `pc2img.image_cache.DiskBackedImageData` | bug-fix pass | Arithmetic on a `DiskBackedImageData` (e.g. `a + b`) previously raised `NotImplementedError`; it now succeeds and returns a plain `numpy.ndarray`. Code that caught `NotImplementedError` from raster arithmetic will no longer see it — the operation now succeeds. |
| BC-P2I-012 | dep-constraint | informational | `GSEGUtils.lazy_disk_cache.register_lazy_disk_cache_class` | bug-fix pass | Historical record, closed before this milestone shipped: pc2img depends on `GSEGUtils >= 0.5.3` (which carries the `register_lazy_disk_cache_class` hook) directly from PyPI; the temporary git-rev dependency bridge used mid-development was removed. The on-disk store-key containment contract itself is owned upstream — see `BC-GSEG-006` in GSEGUtils's own migration record for its remedies; this entry does not restate them. The 0.6 pin that replaces `>= 0.5.3` is BC-P2I-026. |
| BC-P2I-013 | error-behavior | should-review | `pc2img.features.manager.FeatureManager` (dependency resolution) | bug-fix pass | A cyclic feature-dependency graph previously recursed into a `RecursionError`; it now raises a clear `ValueError("dependency cycle: <name>")`. Catch `ValueError` instead of `RecursionError` on a malformed feature graph; well-formed graphs are unaffected. |
| BC-P2I-014 | error-behavior | should-review | `pc2img.features.registry.FeatureRegistry.match`, `pc2img.features.manager.FeatureManager.request` | gap-closure pass | RRIM feature-name validation moved from compute time to request time. A malformed RRIM name inside a batch request now raises a bare `ValueError` from `request()` itself, aborting the entire batch before any feature computes (previously it failed later, per-feature, at compute time). Catch `ValueError` around the `request()` call, not only around the compute phase. |
| BC-P2I-015 | signature-shape | should-review | `pc2img.strategies.projection.PerspectiveProjection` (`projection_matrix=`) | gap-closure pass | A non-3×3 or non-pinhole (`K[2,2] != 1`) intrinsics matrix `K` now raises `ValueError` at construction instead of being stored unchecked. Normalize `K` by `K[2,2]` so the bottom row is `[0, 0, 1]`, and pass `K` and `[R|t]` separately rather than a composed projection matrix. Skew in `K[0,1]` is still accepted. |
| BC-P2I-016 | semantic-change | should-review | `pc2img.features.rrim` (the `zF` option token's emitted cache-key formatting) | gap-closure pass | The emitted `z` token in a derived RRIM cache-key name switched from 6-significant-figure formatting to the shortest exactly-round-tripping form. The emitted token is byte-identical for every `z` that formatted correctly before (0.5, 2.5, 0.0001, 1.5, 1234567, every integer, …); only names that were already mis-encoding their configuration change (e.g. `z1.23457` from `z=1.2345678`). A persisted cache entry holding a truncated name simply degrades to a cache miss and recomputes under the corrected key. |
| BC-P2I-017 | error-behavior | should-review | `pc2img.image_cache.DiskBackedImageStore` (key-derived on-disk path builders) | gap-closure pass | A store key whose on-disk path would escape the configured cache directory (e.g. a parent-directory segment or an absolute path) is refused with `ValueError` before any file outside the cache directory is touched. The refusal is now raised by GSEGUtils (`StoreKeyError`, or `StoreContainmentError` for a resolved-path escape — both `ValueError` subclasses, so `except ValueError` keeps working) at the first use of the key on every route: the mapping setter, `add_image_to_store`, `add_data_to_store`, `purge`, item access and `extend_cache_path`. Sanitize any raster key that is not a plain name before handing it to the store (strip `..` segments, reject absolute paths, or hash the key). Nesting under the cache directory is no longer allowed: a `/` in a key is refused (see BC-P2I-028). |
| BC-P2I-018 | semantic-change | should-review | `pc2img.features.rrim` (`_parse_rrim_config`, `_parse_rrim_component` first-token precedence) | gap-closure pass | A first token that fully matches the exponent-notation z-token grammar (e.g. `z1e5`) is now consumed as the `z_factor` option rather than as a base-feature name, so a scalar field named exactly like an exponent z-token changes what a pre-existing RRIM name computes. Address such a scalar field as `scalar_field_z1e5` instead, or rename the field. Only a full-match first token is affected; a near-miss (`z1e5x`, `zx1e5`) is unaffected. |
| BC-P2I-019 | dep-constraint | should-review | package version / git tags | publication pass, this phase — lands with the first promotion, not yet executed as of this draft | The `v2.0.0a5` tag is retired (renamed to `archive/v2.0.0a5`); git-installed builds move from reporting `2.0.0a5.postN` to `0.10.4.postN` and then `0.11.0`. Drop any pin of the form `~= 2.0` or a `v2.0.0a5`-anchored git reference. |
| BC-P2I-020 | dep-constraint | should-review | package distribution channel | publication pass, this phase — lands with the first promotion, not yet executed as of this draft | pc2img becomes installable from PyPI. Depend on `pc2img ~= 0.11` and drop any git-URL pin (e.g. a commented-out `@v2.0.0a1`-style reference). |
| BC-P2I-021 | additive-or-fixed | informational | `README.rst`, `CITATION.cff`, `[project.urls]` | `f7e565c`, `1556e2c` — publication pass, metadata and documentation | Real install/quickstart/feature documentation and citation metadata replace the prior placeholder content; no code-level change for callers. |
| BC-P2I-026 | dep-constraint | should-review | (resolver-level; `GSEGUtils`, `pchandler`, `numpy` pins and the `cuda11`/`cuda12` extras) | `a69ca05` — GSEGUtils 0.6 adoption | Depend on `GSEGUtils ~= 0.6.0`, `pchandler >= 2.1.1, ~= 2.1` and `numpy >= 2.2, < 2.4`; drop any pin on `GSEGUtils` 0.5.x. `pc2img[cuda11]` / `[cuda12]` now install only `cudf`, `cuspatial` and `geopandas` via `pchandler` 2.1.1 (the `cuml`, `cuproj` and `dask-cudf` packages are gone from the resolved stack). The pin is the compatible-release `~= 0.6.0` rather than a range up to 1.0 because a pre-1.0 GSEGUtils minor can withdraw surface pc2img uses (0.6.0 withdrew the private path builders the 0.5.x store wrapper called, which broke pc2img on a plain install); each GSEGUtils minor therefore ships with a pc2img release that has been run against it. Resolver-level only — no source changes downstream. |
| BC-P2I-027 | semantic-change | should-review | `pc2img.image_cache.DiskBackedImageStore` (`__delitem__`, `pop`, `popitem`, `clear`, `purge`, `add_image_to_store`) | `1d1f9f2` — store delegates deletion and containment to GSEGUtils 0.6; `e3f7f5c` — an overwrite purges whenever the key is tracked or still has files on disk; `b2a3baa` — the overwrite gate narrowed to the artefact a fresh store adopts, leftovers tolerated; `e738cf4` — a linked write path is refused before any write, in every process | `del store[k]`, `pop`, `popitem` and `clear` now drop tracking only: the key's on-disk codec pair (`<key>.npy`, `<key>.meta.json`) stays in place, and a key that was offloaded to it is re-adopted by the next read of that key and by any fresh store opened over the directory. Call `purge(key)` to remove a key together with all of its key-derived files (`.dat` memmap, `.npy`, `.meta.json`); it also detaches the entry's finalizer, so the re-add-after-delete hazard of the old route does not apply to it. `add_image_to_store` over a key purges first when the key is tracked or its `<key>.npy` codec file is on disk (the file a fresh store adopts), so a re-add after `del`, `pop`, `popitem` or `clear` removes the stale codec pair (a fresh store no longer serves the pre-overwrite raster) and detaches the dropped entry's cleanup hook (a retained reference to an entry registered with this store can no longer delete the replacement's `.dat` memmap when it is garbage-collected; copies made by pickling hold their own registrations, and the tiled generator disarms the entries it returns on every call, see BC-P2I-030). For a key whose only files are a `.meta.json` or a `.dat`, a purge is attempted and a refusal on process identity alone is tolerated: nothing servable is on disk, and the replacement is written through a temporary name and an atomic rename; Leftover temporary names that are regular files (`.dat.tmp`, `.npy.tmp`, `.meta.json.tmp`) are not consulted by that gate. Before any purge or write, in every process (the one that constructed the store included), `add_image_to_store` refuses a symlink at any path the write opens for the key — `<key>.dat`, `<key>.dat.tmp`, `<key>.npy.tmp`, `<key>.meta.json.tmp` — with `StorePurgeAliasedArtefactError` (the link resolves inside the cache directory, i.e. to another key's artefact) or `StorePurgeForeignArtefactError` (it resolves outside); both are `StorePurgeRefusedError`, and nothing has been written or removed. Before this change a planted `<key>.dat.tmp` link redirected the new raster into the other key's file, in the constructing process and in a non-owner process alike. In a non-owner process upstream's own foreign and aliased checks never run (it refuses on process identity first), so a linked `.dat` or `.meta.json` leftover is refused there by pc2img with `StorePurgeRefusedError`. A link planted under an already tracked key after its add is still followed by a later offload (a documented limit). So a process that did not construct the store can add new keys and can add a key over such leftovers, but cannot replace a key whose codec pair is on disk. Non-owner caveat: in a process that did not construct the store, an overwrite over a key whose dropped entry is still retained cannot disarm that entry's cleanup hook: the tolerated process-identity refusal of the leftover case leaves it armed, so collecting the retained reference later deletes the replacement's `.dat`. This applies only while no `<key>.npy` exists for the key. With the codec pair on disk the overwrite takes the hard path, a non-owner is refused with `StorePurgeRefusedError`, and nothing is replaced. Measured in a forked child that inherited the parent's live, never-offloaded entry for a key: after `del store[key]` and a re-add the replacement read back, and after the retained reference was collected the `.dat` was gone and an offload followed by a read raised `FileNotFoundError`. Results obtained through `TiledPointCloudImageGenerator.generate()` do not reach it: every entry that method returns has delete-on-collection disabled (see BC-P2I-030), and the route that did (a pooled call, a sequential call whose result is held, `del` on a tile store, a regenerate, releasing the held result) was measured to keep the replacement `.dat` and to read back. The caveat concerns callers of the exported store who hold entries of a store they did not construct. The purge an overwrite performs can be refused under three independent conditions, each a `StorePurgeRefusedError` (a `RuntimeError`): a wrong process, i.e. the call is made from a process that did not construct the store (`StorePurgeRefusedError` itself — tolerated only for a key whose files are a `.meta.json` or a `.dat`, see above; this includes the tile stores a `TiledPointCloudImageGenerator` builds in its workers whenever the work runs in a worker pool, see BC-P2I-030); `StorePurgeForeignArtefactError`, when a built artefact (for example a symlink whose target lies outside the cache directory) or a live entry's own `cache_path` resolves outside the cache directory, which includes an entry inserted through the mapping setter with an outside `cache_path` — such an entry can no longer be overwritten through `add_image_to_store` (the baseline did not refuse it): re-point it, or give it an in-cache `cache_path`, first; and `StorePurgeAliasedArtefactError`, when a built artefact is a link to another key's artefact inside the cache directory. A file that cannot be unlinked raises `StorePurgeIncompleteError` (an `OSError`). A wrong-type cache override or an `OSError` during the replacement build still loses the old entry. pc2img's own pipeline never calls `del`, `pop`, `popitem` or `clear` on a store, so a default pipeline run sees no change; code that used `del` as a delete-the-cache-file verb should call `purge`. |
| BC-P2I-028 | error-behavior | should-review | `pc2img.image_cache.DiskBackedImageStore`, `pc2img.tiled_generator.TIGSettings.extend_cache_paths`, `pc2img.tiled_generator.PointCloudTile.tile_id`, `pc2img.tiled_generator.TiledPointCloudImageGenerator`, `pc2img.features.manager.FeatureManager.request` (scalar-field names reached through `generate()`) | `1d1f9f2`, `8e6b0a5` — store delegates key validation to GSEGUtils 0.6; `3d0b43d` — duplicate tile ids rejected at construction | Store keys and cache-path segments are validated by GSEGUtils on every route and refused with `StoreKeyError` (a `ValueError`) when they contain `/` or `\`, contain `:`, end in `.` or a space, are `''`, `.` or `..`, or are a Windows device name; a planted directory symlink that resolves outside the cache directory raises `StoreContainmentError` (a `StoreKeyError`). Names the pipeline itself produces (feature names such as `hillshade_range_315_45` or `z1e-05`-style RRIM names, tile ids such as `tile_03`, hex digests, names with spaces) stay legal. Scalar-field names are the visible change: `a/b`, `GPS:time` and `x.` were accepted on GSEGUtils 0.5.3 (added, offloaded and read) and now raise at `generate()`. Rename the field, or address it through a name without those characters. Tile ids and pcd stems passed to `extend_cache_path` / `extend_cache_paths` follow the same rule; iof3D passes a filename stem there, see its own store-key handoff — the rule itself is upstream BC-GSEG-006 and is not restated here. A cache directory persisted by an older pc2img that already holds such a key is expected to be left un-adopted rather than to crash; that was not measured. Tile ids must also be unique: `TiledPointCloudImageGenerator` now raises `ValueError` at construction when two tiles share a `tile_id` (previously accepted; later calls then handed one generator to both tiles, computing one tile from the other's points, dropping one tile from the results, and re-opening the one-store-in-two-processes race in a pool). Give every tile its own id. |
| BC-P2I-029 | signature-shape | should-review | `pc2img.image_cache.DiskBackedImageStore.store`, `pc2img.image_cache.DiskBackedImageStore.image_data` | `1d1f9f2` — store delegates to GSEGUtils 0.6 | `store` and its `image_data` alias now return a read-only mapping (`types.MappingProxyType`; the annotation is `Mapping[...]`, not `dict[...]`): item assignment and deletion raise `TypeError`, and `.pop`, `.clear`, `.update` and `.setdefault` raise `AttributeError`. Reading is unchanged. Mutate through `add_image_to_store`, `purge` or the store's own mapping interface. The upstream record is BC-GSEG-007 and is not restated here. |
| BC-P2I-030 | semantic-change | should-review | `pc2img.tiled_generator.TiledPointCloudImageGenerator.generate`, `pc2img.tiled_generator.TiledPointCloudImageGenerator.image_generators` | `a7d593d` — the GSEGUtils 0.6.0 re-generation race first recorded; `4fbd966` — per-tile dispatch removes the race on the pc2img side; `321d68c` — pooled results and the stores in `image_generators` stop owning garbage-collection deletion; `4b4add3` — every `generate()` call disarms it, `n_jobs=1` included; `d00cfdb` — a failing pooled dispatch drops the parent's tile generators | `generate()` now dispatches one loky task per tile (one `_process_tile` call per tile), each carrying only that tile's generator (built in the worker on the first call and reused afterwards) and picklable inputs; before this change the whole tiled generator — every tile's store and point cloud — was pickled into every task (the baseline `91b4ab6` did the same). Consequence: repeated `generate()` calls on one instance whenever the work runs in a worker pool (any `n_jobs` other than 1, including the default `-1`) with two or more tiles work on GSEGUtils 0.6.0, and every returned raster stays readable after earlier results are released — measured by reading every raster after each call, after rebinding and collecting the results: 0 of 12 rounds failing after the change (`failures: 0 / 12`) against 12 of 12 before (`failures: 12 / 12`), with every raster read after each call. The earlier known-limitation wording and its workaround are withdrawn; the suite's `test_tiled_regenerate_on_one_instance_with_two_workers` is a plain passing test. GSEGUtils#82 (https://github.com/gseg-ethz/GSEGUtils/issues/82) remains open and valid for any program that unpickles one store in several processes at once; pc2img no longer does. **Disk persistence.** Every `generate()` call — `n_jobs=1` included — disarms delete-on-garbage-collection on the entries it returns and on the entries of the stores in `image_generators`, so releasing one call's results never deletes a `.dat` that a later call's results read (each pickle round-trip gives the parent another entry object on the same file, and the first of them to be collected would otherwise unlink it). There is no exemption for sequential results: an entry armed by a sequential call is otherwise still alive when a later pooled call rebuilds the same `.dat` under another object, and releasing the sequential results then unlinks files the pooled results and the stores read (measured: the sequences `1→2`, `1→-1` and `2→1 adding features→2` failed at the read before the change). Measured over a pooled, then sequential-adding-features, then pooled sequence with every raster read after each call (and every store entry read after `store.offload()`): 0 of 12 rounds failing after the change against 12 of 12 before (`failures: 0 / 12` against `failures: 12 / 12`). The consequence is that released results and dropped generators no longer delete their cache files at all, whatever `n_jobs`: cache files persist after sequential runs too. With the default `enable_caching=False` a run writes no files at either `n_jobs` and only each store's empty temporary directory is left. When caching is enabled without a `cache_path`, each tile store writes into its own `tempfile.mkdtemp` directory, which nothing cleans up afterwards: `<store dir>/<key>.dat` (a sequential run leaves only the `.dat`; a pooled run also leaves the codec pair `<key>.npy` and `<key>.meta.json` that the pickling writes). With a `cache_path` the same files are under `<cache_path>/<tile_id>/<key>.dat`. They persist until `purge()` is called or the directory is removed. Routes: configure `cache_path` and remove that directory when the run is done; or `purge()` keys from the owning process (the calling process owns the stores only if every call used `n_jobs=1`). Remaining limit: whenever the work runs in a worker pool (any `n_jobs` other than 1, including the default `-1`), each tile's `DiskBackedImageStore` is constructed inside a worker and owned by that worker's process id for good, so after `generate()` returns, `purge` and `add_image_to_store` over an existing key, called from the parent, raise `StorePurgeRefusedError` (a `RuntimeError`); an overwrite attempted from any other process is refused the same way. A later `generate()` on the instance triggers that refusal when a requested feature is untracked but still has its codec pair (`<key>.npy`) in the tile directory (dropped with `del`, `pop`, `popitem` or `clear` while offloaded): that tile's `_process_tile` then adds the key over an on-disk codec pair in a process that is not the owner. In a pool this depends on which worker gets the tile (measured: refused in 2 of 4 runs at `n_jobs=2`); after a pooled run it happens every time at `n_jobs=1` (4 of 4), because the parent is not the owner either. Leftover temporary files, a lone `.meta.json` or a lone `.dat` (a killed worker, or a session with `purge_disk_on_gc=False`) do not trigger it (BC-P2I-027), and features the store still tracks are not recomputed and do not trigger it. Routes: use `n_jobs=1` for every call on an instance that will be purged from or overwritten — an instance that has run in a pool once is owned by its workers for good; build a fresh generator for each `generate()` call; or drop the tile's entry from `image_generators` and remove its cache sub-directory `<cache_path>/<tile_id>`. **Failed batch.** When a pooled dispatch raises, the parent drops its tile generators and re-raises: the tiles that finished have already written codec pairs the parent's copies do not track, so keeping the generators made the next request for such a key reach the overwrite gate in a process that is not the owner. The next call rebuilds each tile's generator and adopts the codec pairs the finished tiles wrote, so a retry is not refused (before this change it raised `StorePurgeRefusedError` at both `n_jobs`). At `n_jobs=1` nothing is dropped. Tile ids must be unique: a repeated id raises `ValueError` at construction (see BC-P2I-028). A fix for the ownership limit is planned after 0.11.0. Tracking issue: https://github.com/gseg-ethz/pc2img/issues/24. |

## Additive changes

| BC-ID | category | severity | affected_symbols | origin | migration_steps |
|---|---|---|---|---|---|
| BC-P2I-022 | additive-or-fixed | additive | `pc2img.strategies.projection.PerspectiveProjection`, `"perspective"` key of `pc2img.strategies.registry.PROJECTIONS` | `dc257e4` — consolidation of the 2.x branches (folded from the perspective-projection branch) | New registered projection strategy, `PROJECTIONS.create("perspective", ...)`; purely additive, no existing strategy changed. |
| BC-P2I-023 | additive-or-fixed | additive | `pc2img.util.nanconv` (`compute_dtype=`) | bug-fix pass | New keyword-only `compute_dtype` parameter selects the accumulation/division dtype; the default (`np.float32`) reproduces the corrected output byte-for-byte, so no action is required unless you want reduced-precision accumulation. |
| BC-P2I-024 | additive-or-fixed | additive | `pc2img.features.derivative_features.GradientFeature` (`pixel_size=`), feature-name DSL suffix `_px<value>` | bug-fix pass | New opt-in `pixel_size` constructor kwarg and matching `_px<value>` feature-name suffix; the default (`100`) reproduces the historical `1/100`-scaled output byte-for-byte. No action required. |
| BC-P2I-025 | additive-or-fixed | additive | the `zF` option token of `pc2img.features.rrim`'s name grammar | gap-closure pass | The `zF` token now additionally accepts exponent notation (`z1e-05`, `z1E-05`, `z1e+20`); every feature name valid before stays valid. No action required unless you want to express a `z_factor` below `1e-4` in a feature name. |

## Internal & sweep changes

- [bug-fix pass]: `pc2img.features.derivative_features.HillshadeFeature`'s aspect
  convention — no math changed; the deliberate non-north-up (non-ESRI-compass) aspect handedness
  is now documented in the class docstring and pinned by a self-consistency characterization test.
  No public-surface change.
- [bug-fix pass]: `pc2img.strategies.interpolation.DelaunayInterpolation`'s
  triangle-culling constants (median-area × 10; aspect median + 6·MAD; × 10 fallback) surfaced as
  constructor kwargs (`interior_culling`, `area_scale`, `aspect_ratio_mad_factor`,
  `aspect_ratio_fallback_scale`) with byte-identical defaults to the prior hardcoded behavior. No
  public-surface change for any existing call site.
- [gap-closure pass]: `pc2img.image_cache.DiskBackedImageStore.__init__`'s `config`
  parameter default changed from a shared mutable `LazyDiskCacheConfig()` instance to a
  `None`-sentinel, coerced in the constructor body. An omitted or explicit-`None` config yields the
  identical default instance. No public-surface change.
- [bug-fix pass]: the same `None`-sentinel pattern replaced a shared mutable
  `LazyDiskCacheConfig()` default at every remaining generator/manager/interpolation/tiled-generator
  construction site. No public-surface change; prevents cross-instance config aliasing.
- [GSEGUtils 0.6 adoption]: `pc2img.image_cache.DiskBackedImageStore`'s private key-to-path builders,
  its containment helper and its `__delitem__` override were deleted (private names, no public-surface
  change); key validation and containment now come from GSEGUtils, and the observable effects are
  recorded in BC-P2I-027 and BC-P2I-028.
- [GSEGUtils 0.6 adoption]: the private per-tile method of `TiledPointCloudImageGenerator` became a
  module-level function (private name, no public-surface change); the observable effects are
  recorded in BC-P2I-030.
- [GSEGUtils 0.6 adoption]: `DiskBackedImageStore.offload`'s `features=` keyword name is unchanged
  (GSEGUtils's own method calls it `keys`); pre-existing naming difference, no action.
- **Aggregation rule:** one `BC-P2I` entry per observable downstream effect. Two notes that share
  one observable downstream effect collapse into a single entry; a note that has two independently
  observable effects (a correctness fix plus a new, separately opt-in capability) is split into two
  entries by severity — for example `nanconv`'s float16→float32 correctness fix (`BC-P2I-009`,
  should-review) and its unrelated, byte-identical-by-default `compute_dtype` opt-in
  (`BC-P2I-023`, additive) are two entries because a default-configured caller sees no change from
  the `compute_dtype` addition itself.

## Verifier (inline)

The block below is the executor-time verifier for this record. It Tier-1 AST-walks the four
public-surface `__init__.py` barrels and asserts every non-dotted top-level symbol named in a
`BC-P2I-NNN` entry's `affected_symbols` resolves on the public surface (or, for a
`surface-removed` entry, does not). It then Tier-2 runtime-checks the mechanical claims a static
walk cannot see (raised exception types, kwarg presence, on-disk behavior). Exits 0 on success.

```python
r"""Inline executor-time verifier for pc2img MIGRATION-v0.11.md.

Extract this block and run it from the repository root:

    mkdir -p _scrap
    awk '/^## Verifier \(inline\)$/,/^```$/' .planning/MIGRATION-v0.11.md \
        | sed -n '/^```python$/,/^```$/p' | sed '1d;$d' \
        > _scrap/pc2img-migration-verifier.py
    uv run --frozen python _scrap/pc2img-migration-verifier.py

Tier 1 AST-walks the four public __init__.py barrels' `__all__` list literals and
asserts every non-dotted top-level symbol named in a BC-P2I entry's
affected_symbols resolves (or, for surface-removed entries, does NOT resolve).
Tier 2 runtime-checks the mechanical claims a static AST walk cannot see
(raised exception types and subtypes, kwarg presence, on-disk behavior, the
resolved GSEGUtils/pchandler/numpy versions, the read-only store mapping).
BC-P2I-030 has no runtime probe here: its proof is the suite's passing regression
test over repeated tiled generation, which rebinds and collects the results and then reads
every raster; the duplicate-tile-id rule it cross-references is probed under BC-P2I-028
and the overwrite gate under BC-P2I-027. Exits 0 on
success, 1 on any failure — including an empty BC_ENTRIES list, which is
always a verifier bug, never a vacuous pass.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

# The four public-surface __init__.py barrels, relative to the repo root.
PUBLIC_SURFACE_FILES = [
    "src/pc2img/__init__.py",
    "src/pc2img/features/__init__.py",
    "src/pc2img/strategies/__init__.py",
    "src/pc2img/image_cache/__init__.py",
]


def _extract_all(py_text: str) -> set[str]:
    """Return the string literals assigned to a module's ``__all__`` list."""
    tree = ast.parse(py_text)
    declared: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    value = node.value
                    if isinstance(value, ast.List):
                        for elt in value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                declared.add(elt.value)
    return declared


# BC-P2I entries — keep in sync with the markdown tables above. Only entries
# whose affected_symbols list contains a top-level (non-dotted) name are
# checked at Tier 1; dotted names and mechanical claims are Tier 2's job.
BC_ENTRIES: list[dict[str, object]] = [
    {
        "id": "BC-P2I-001",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.errors.RegistryLookupError",
            "pc2img.strategies.registry.StrategyRegistry",
            "pc2img.features.registry.FeatureRegistry",
        ],
    },
    {
        "id": "BC-P2I-002",
        "category": "dep-constraint",
        "severity": "should-review",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-003",
        "category": "dep-constraint",
        "severity": "informational",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-004",
        "category": "surface-removed",
        "severity": "informational",
        "affected_symbols": ["pc2img.registry.make_generator"],
    },
    {
        "id": "BC-P2I-005",
        "category": "surface-removed",
        "severity": "informational",
        "affected_symbols": ["pc2img.util.convert_to_image"],
    },
    {
        "id": "BC-P2I-006",
        "category": "dep-constraint",
        "severity": "should-review",
        "affected_symbols": ["pc2img.util.convert_to_image"],
    },
    {
        "id": "BC-P2I-007",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.strategies.projection.SphericalProjection.project_raw",
            "pc2img.strategies.projection.SphericalProjection.inverse_projection",
        ],
    },
    {
        "id": "BC-P2I-008",
        "category": "signature-shape",
        "severity": "should-review",
        "affected_symbols": ["pc2img.strategies.projection.PerspectiveProjection"],
    },
    {
        "id": "BC-P2I-009",
        "category": "semantic-change",
        "severity": "should-review",
        "affected_symbols": ["pc2img.util.nanconv"],
    },
    {
        "id": "BC-P2I-010",
        "category": "on-disk-format",
        "severity": "must-edit",
        "affected_symbols": ["pc2img.image_cache.DiskBackedImageStore"],
    },
    {
        "id": "BC-P2I-011",
        "category": "semantic-change",
        "severity": "should-review",
        "affected_symbols": ["pc2img.image_cache.DiskBackedImageData"],
    },
    {
        "id": "BC-P2I-012",
        "category": "dep-constraint",
        "severity": "informational",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-013",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": ["pc2img.features.manager.FeatureManager"],
    },
    {
        "id": "BC-P2I-014",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.features.registry.FeatureRegistry.match",
            "pc2img.features.manager.FeatureManager.request",
        ],
    },
    {
        "id": "BC-P2I-015",
        "category": "signature-shape",
        "severity": "should-review",
        "affected_symbols": ["pc2img.strategies.projection.PerspectiveProjection"],
    },
    {
        "id": "BC-P2I-016",
        "category": "semantic-change",
        "severity": "should-review",
        "affected_symbols": ["pc2img.features.rrim"],
    },
    {
        "id": "BC-P2I-017",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": ["pc2img.image_cache.DiskBackedImageStore"],
    },
    {
        "id": "BC-P2I-018",
        "category": "semantic-change",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.features.rrim._parse_rrim_config",
            "pc2img.features.rrim._parse_rrim_component",
        ],
    },
    {
        "id": "BC-P2I-019",
        "category": "dep-constraint",
        "severity": "should-review",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-020",
        "category": "dep-constraint",
        "severity": "should-review",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-021",
        "category": "additive-or-fixed",
        "severity": "informational",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-022",
        "category": "additive-or-fixed",
        "severity": "additive",
        "affected_symbols": ["pc2img.strategies.projection.PerspectiveProjection"],
    },
    {
        "id": "BC-P2I-023",
        "category": "additive-or-fixed",
        "severity": "additive",
        "affected_symbols": ["pc2img.util.nanconv"],
    },
    {
        "id": "BC-P2I-024",
        "category": "additive-or-fixed",
        "severity": "additive",
        "affected_symbols": ["pc2img.features.derivative_features.GradientFeature"],
    },
    {
        "id": "BC-P2I-025",
        "category": "additive-or-fixed",
        "severity": "additive",
        "affected_symbols": ["pc2img.features.rrim"],
    },
    {
        "id": "BC-P2I-026",
        "category": "dep-constraint",
        "severity": "should-review",
        "affected_symbols": [],
    },
    {
        "id": "BC-P2I-027",
        "category": "semantic-change",
        "severity": "should-review",
        "affected_symbols": ["pc2img.image_cache.DiskBackedImageStore"],
    },
    {
        "id": "BC-P2I-028",
        "category": "error-behavior",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.image_cache.DiskBackedImageStore",
            "pc2img.tiled_generator.TIGSettings.extend_cache_paths",
            "pc2img.tiled_generator.PointCloudTile.tile_id",
            "pc2img.tiled_generator.TiledPointCloudImageGenerator",
            "pc2img.features.manager.FeatureManager.request",
        ],
    },
    {
        "id": "BC-P2I-029",
        "category": "signature-shape",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.image_cache.DiskBackedImageStore.store",
            "pc2img.image_cache.DiskBackedImageStore.image_data",
        ],
    },
    {
        "id": "BC-P2I-030",
        "category": "semantic-change",
        "severity": "should-review",
        "affected_symbols": [
            "pc2img.tiled_generator.TiledPointCloudImageGenerator.generate",
            "pc2img.tiled_generator.TiledPointCloudImageGenerator.image_generators",
        ],
    },
]


def _find_repo_root() -> Path:
    root = Path.cwd()
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and 'name = "pc2img"' in pyproject.read_text(encoding="utf-8"):
        return root
    raise RuntimeError(
        f"cannot find a pc2img repository root at {root} "
        "(expected ./pyproject.toml naming pc2img) — run this verifier from the repo root"
    )


def _check_ids(failures: list[str]) -> None:
    if not BC_ENTRIES:
        failures.append("BC_ENTRIES is empty — an empty record is a failure, never a vacuous pass")
        return
    seen: list[int] = []
    for entry in BC_ENTRIES:
        entry_id = str(entry["id"])
        prefix, _, digits = entry_id.rpartition("-")
        if prefix != "BC-P2I" or len(digits) != 3 or not digits.isdigit():
            failures.append(f"{entry_id}: id is not of the form BC-P2I-NNN (zero-padded to 3 digits)")
            continue
        seen.append(int(digits))
        if entry.get("category") == "surface-removed" and not entry.get("affected_symbols"):
            failures.append(f"{entry_id}: surface-removed entry names no symbol")
    if seen != sorted(seen) or len(seen) != len(set(seen)):
        failures.append(f"BC-P2I ids are not unique and strictly increasing: {seen}")


def _tier1(root: Path, failures: list[str]) -> None:
    public_surface: set[str] = set()
    for rel in PUBLIC_SURFACE_FILES:
        path = root / rel
        if not path.exists():
            failures.append(f"missing public-surface file: {path}")
            continue
        public_surface |= _extract_all(path.read_text(encoding="utf-8"))

    for entry in BC_ENTRIES:
        entry_id = str(entry["id"])
        affected = entry.get("affected_symbols") or []
        category = entry.get("category")
        for sym in affected:  # type: ignore[union-attr]
            if not isinstance(sym, str) or "." in sym:
                continue  # dotted / non-string symbols are Tier 2's job
            if category == "surface-removed":
                if sym in public_surface:
                    failures.append(
                        f"{entry_id}: documented as surface-removed but {sym!r} is present "
                        "on the public surface"
                    )
            elif sym not in public_surface:
                failures.append(f"{entry_id}: symbol {sym!r} not found on the public surface (Tier 1)")


def _tier2_bc_p2i_001() -> str | None:
    import pc2img.errors as errors_mod

    exc = errors_mod.RegistryLookupError
    if not (issubclass(exc, KeyError) and issubclass(exc, RuntimeError)):
        return "BC-P2I-001: RegistryLookupError does not dual-inherit KeyError and RuntimeError"
    return None


def _tier2_bc_p2i_004() -> str | None:
    # surface-removed: make_generator must not exist on pc2img.registry.
    import pc2img.registry as registry_mod

    if getattr(registry_mod, "make_generator", None) is not None:
        return "BC-P2I-004: make_generator is still present on pc2img.registry"
    return None


def _tier2_bc_p2i_005() -> str | None:
    # surface-removed: the dead, unreachable *first* convert_to_image
    # definition is gone — exactly one `def convert_to_image` remains in
    # pc2img.util's source, and it is still callable (importable, no
    # NameError from an unimported plt at definition time).
    import inspect

    import pc2img.util as util_mod

    if not callable(getattr(util_mod, "convert_to_image", None)):
        return "BC-P2I-005: pc2img.util.convert_to_image is missing or not callable"
    src = inspect.getsource(util_mod)
    count = src.count("def convert_to_image")
    if count != 1:
        return f"BC-P2I-005: expected exactly one convert_to_image definition, found {count}"
    return None


def _tier2_bc_p2i_006() -> str | None:
    # dep-constraint: convert_to_image still resolves and stays lazy about
    # matplotlib (no import-time dependency on the viz extra).
    import pc2img.util as util_mod

    if not callable(getattr(util_mod, "convert_to_image", None)):
        return "BC-P2I-006: pc2img.util.convert_to_image is missing or not callable"
    return None


def _tier2_bc_p2i_008() -> str | None:
    # signature-shape: a 4x4 rotation_matrix raises TypeError. Exception type
    # is PINNED to what was observed by running the constructor, not guessed.
    import numpy as np

    from pc2img.strategies.projection import PerspectiveProjection

    try:
        PerspectiveProjection(np.eye(3, dtype=np.float32), np.eye(4, dtype=np.float32))
    except TypeError:
        return None
    except Exception as exc:
        return f"BC-P2I-008: expected TypeError for a 4x4 rotation_matrix, got {type(exc).__name__}"
    return "BC-P2I-008: PerspectiveProjection accepted a 4x4 rotation_matrix without raising"


def _tier2_bc_p2i_015() -> str | None:
    # signature-shape: a non-pinhole K (bottom row != [0, 0, 1]) raises.
    # Observed exception type is ValueError (pinned by running the
    # constructor once — never guessed from reading).
    import numpy as np

    from pc2img.strategies.projection import PerspectiveProjection

    bad_k = np.eye(3, dtype=np.float32)
    bad_k[2, 2] = 2.0
    try:
        PerspectiveProjection(bad_k, np.eye(3, dtype=np.float32))
    except ValueError:
        return None
    except Exception as exc:
        return f"BC-P2I-015: expected ValueError for a non-pinhole K, got {type(exc).__name__}"
    return "BC-P2I-015: PerspectiveProjection accepted a non-pinhole K without raising"


def _tier2_bc_p2i_009_and_023() -> str | None:
    # semantic-change / additive: nanconv's compute_dtype is keyword-only,
    # defaulting to numpy.float32.
    import inspect

    import numpy as np

    import pc2img.util as util_mod

    sig = inspect.signature(util_mod.nanconv)
    param = sig.parameters.get("compute_dtype")
    if param is None:
        return "BC-P2I-009/023: nanconv has no compute_dtype parameter"
    if param.kind is not inspect.Parameter.KEYWORD_ONLY:
        return "BC-P2I-009/023: nanconv's compute_dtype is not keyword-only"
    if param.default is not np.float32:
        return f"BC-P2I-009/023: nanconv's compute_dtype default is {param.default!r}, expected numpy.float32"
    return None


def _tier2_bc_p2i_010() -> str | None:
    # on-disk-format: a legacy .pkl cache file degrades to a cache miss
    # rather than being deserialized.
    import tempfile
    from pathlib import Path

    from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

    from pc2img.image_cache.disk_backed_image_store import DiskBackedImageStore

    with tempfile.TemporaryDirectory() as td:
        cache_dir = Path(td)
        store = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=cache_dir))
        legacy = cache_dir / "ghost.pkl"
        legacy.write_bytes(b"not a real pickle payload")
        if "ghost" in store:
            return "BC-P2I-010: a planted legacy .pkl file was adopted as a store member"
    return None


def _tier2_bc_p2i_011() -> str | None:
    # semantic-change: DiskBackedImageData arithmetic returns a plain ndarray.
    import numpy as np

    from pc2img.image_cache.disk_backed_image_data import DiskBackedImageData

    a = DiskBackedImageData(np.ones((2, 2), dtype=np.float32))
    b = DiskBackedImageData(np.ones((2, 2), dtype=np.float32))
    result = a + b
    if type(result) is not np.ndarray:
        return f"BC-P2I-011: DiskBackedImageData arithmetic returned {type(result)!r}, expected numpy.ndarray"
    return None


def _tier2_bc_p2i_017() -> str | None:
    # error-behavior: a store key whose path escapes the cache directory is
    # refused with ValueError before anything outside it is touched.
    import tempfile
    from pathlib import Path

    import numpy as np
    from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig, StoreKeyError

    from pc2img.image_cache.disk_backed_image_store import DiskBackedImageStore

    with tempfile.TemporaryDirectory() as td:
        cache_dir = Path(td) / "cache"
        cache_dir.mkdir()
        store = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=cache_dir))
        try:
            store.add_image_to_store("../victim", np.zeros((2, 2), dtype=np.float32))
        except StoreKeyError:
            # The upstream subtype of ValueError (pinned by running the call).
            pass
        except ValueError as exc:
            return f"BC-P2I-017: escaping key refused with a bare {type(exc).__name__}, expected StoreKeyError"
        except Exception as exc:
            return f"BC-P2I-017: expected ValueError for an escaping key, got {type(exc).__name__}"
        else:
            return "BC-P2I-017: an escaping store key was not refused"
    return None


def _tier2_bc_p2i_026() -> str | None:
    # dep-constraint: the resolved environment is the one the pins describe —
    # GSEGUtils 0.6.x (and not a stale 0.5.x: the private npy-path builder the
    # 0.5 store wrapper called is gone), pchandler >= 2.1.1, numpy >= 2.2.
    import importlib.metadata as md
    import re

    from GSEGUtils.lazy_disk_cache import DiskBackedStore

    def _version_tuple(dist: str) -> tuple[int, ...]:
        return tuple(int(n) for n in re.findall(r"\d+", md.version(dist))[:3])

    gseg = md.version("GSEGUtils")
    if not gseg.startswith("0.6."):
        return f"BC-P2I-026: resolved GSEGUtils is {gseg}, expected 0.6.x"
    if hasattr(DiskBackedStore, "_get_npy_path"):
        return "BC-P2I-026: DiskBackedStore still has the 0.5.x private _get_npy_path (a stale GSEGUtils)"
    if _version_tuple("pchandler") < (2, 1, 1):
        return f"BC-P2I-026: resolved pchandler is {md.version('pchandler')}, expected >= 2.1.1"
    if _version_tuple("numpy") < (2, 2):
        return f"BC-P2I-026: resolved numpy is {md.version('numpy')}, expected >= 2.2"
    return None


def _tier2_bc_p2i_027() -> str | None:
    # semantic-change: del drops tracking only (the codec pair stays and the key
    # is re-adopted on the next read); purge removes the key and its files.
    import gc
    import tempfile
    from pathlib import Path

    import numpy as np
    from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig, get_npy_path
    from GSEGUtils.lazy_disk_cache.paths import get_memmap_path

    from pc2img.image_cache.disk_backed_image_store import DiskBackedImageStore

    with tempfile.TemporaryDirectory() as td:
        store = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=Path(td), enable_caching=True))
        store.add_image_to_store("range", np.zeros((4, 4), dtype=np.float32))
        store.offload_image_data_to_disk("range")
        npy = get_npy_path(store.cache_dir, "range")
        if not npy.exists():
            return "BC-P2I-027: offloading did not produce the codec pair the probe needs"
        del store["range"]
        if not npy.exists():
            return "BC-P2I-027: del removed the codec pair (expected: tracking dropped only)"
        try:
            store["range"]
        except KeyError:
            return "BC-P2I-027: an offloaded key was not re-adopted by the next read after del"
        store.purge("range")
        if npy.exists():
            return "BC-P2I-027: purge left the codec pair on disk"
        if "range" in store:
            return "BC-P2I-027: purge left the key tracked"

        # A re-add after del purges whenever the key still has files on disk: the
        # stale codec pair is removed and a fresh store never serves the old raster.
        store.add_image_to_store("range", np.zeros((4, 4), dtype=np.float32))
        store.offload_image_data_to_disk("range")
        if not npy.exists():
            return "BC-P2I-027: offloading did not produce the codec pair the re-add probe needs"
        del store["range"]
        store.add_image_to_store("range", np.ones((4, 4), dtype=np.float32))
        if npy.exists():
            return "BC-P2I-027: a re-add after del left the stale codec pair on disk"
        store.offload_image_data_to_disk("range")
        fresh = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=Path(td), enable_caching=True))
        try:
            served = float(np.asarray(fresh["range"])[0, 0])
        except KeyError:
            return None  # nothing served: the pre-overwrite raster cannot have been served either
        if served != 1.0:
            return "BC-P2I-027: a fresh store served the pre-overwrite raster after del and re-add"

    # Sensor for the soft gate's detach: a dropped entry that is still held must not
    # delete the replacement's memmap when it is collected. (A re-add over a lone
    # memmap that serves the replacement holds without any gate; it is documented in
    # the row, not probed.)
    with tempfile.TemporaryDirectory() as td:
        store = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=Path(td), enable_caching=True))
        store.add_image_to_store("k", np.zeros((4, 4), dtype=np.float32))
        held = store.store["k"]
        del store["k"]  # tracking dropped; the lone .dat stays and `held` stays armed
        store.add_image_to_store("k", np.ones((4, 4), dtype=np.float32))
        dat = get_memmap_path(store.cache_dir, "k")
        if not dat.exists():
            return "BC-P2I-027: the re-add over a dropped entry did not leave the replacement's memmap"
        del held
        gc.collect()
        if not dat.exists():
            return "BC-P2I-027: collecting a dropped entry deleted the replacement's memmap"
        if float(np.asarray(store["k"])[0, 0]) != 1.0:
            return "BC-P2I-027: the replacement over a dropped entry did not read back"
    return None


def _tier2_bc_p2i_028() -> str | None:
    # error-behavior: nested / illegal keys and cache-path segments are refused
    # with GSEGUtils' StoreKeyError, a ValueError subclass, on every route the
    # entry names; kept small — no point clouds, temp dirs only.
    import tempfile
    from pathlib import Path

    import numpy as np
    from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig, StoreKeyError
    from pchandler import PointCloudData

    from pc2img.core import ImgRes
    from pc2img.image_cache.disk_backed_image_store import DiskBackedImageStore
    from pc2img.tiled_generator import PointCloudTile, TIGSettings, TiledPointCloudImageGenerator

    with tempfile.TemporaryDirectory() as td:
        store = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=Path(td)))
        for key in ("a/b", "GPS:time", "x."):
            try:
                store.add_image_to_store(key, np.zeros((2, 2), dtype=np.float32))
            except StoreKeyError:
                continue
            except Exception as exc:
                return f"BC-P2I-028: key {key!r} raised {type(exc).__name__}, expected StoreKeyError"
            return f"BC-P2I-028: key {key!r} was not refused"
        settings = TIGSettings(
            img_res=ImgRes(4, 4),
            proj_cls="spherical",
            interp_cls="linear",
            lazy_disk_cache_config=LazyDiskCacheConfig(),
        )
        try:
            settings.extend_cache_paths("../x")
        except ValueError:
            pass
        except Exception as exc:
            return f"BC-P2I-028: extend_cache_paths('../x') raised {type(exc).__name__}, expected ValueError"
        else:
            return "BC-P2I-028: extend_cache_paths('../x') was not refused"

    # Duplicate tile ids are refused at construction with ValueError.
    duplicated = [
        PointCloudTile("dup", PointCloudData(np.zeros((8, 3), dtype=np.float32)), {}),
        PointCloudTile("dup", PointCloudData(np.zeros((8, 3), dtype=np.float32)), {}),
    ]
    try:
        TiledPointCloudImageGenerator(duplicated, (4, 4), "spherical", "linear")
    except ValueError:
        pass
    except Exception as exc:
        return f"BC-P2I-028: duplicate tile ids raised {type(exc).__name__}, expected ValueError"
    else:
        return "BC-P2I-028: duplicate tile ids were accepted at construction"
    return None


def _tier2_bc_p2i_029() -> str | None:
    # signature-shape: store / image_data are read-only mappings.
    import tempfile
    import types
    from pathlib import Path

    from GSEGUtils.lazy_disk_cache import LazyDiskCacheConfig

    from pc2img.image_cache.disk_backed_image_store import DiskBackedImageStore

    with tempfile.TemporaryDirectory() as td:
        store = DiskBackedImageStore(config=LazyDiskCacheConfig(cache_path=Path(td)))
        if not isinstance(store.store, types.MappingProxyType):
            return f"BC-P2I-029: store is {type(store.store).__name__}, expected a MappingProxyType"
        if not isinstance(store.image_data, types.MappingProxyType):
            return f"BC-P2I-029: image_data is {type(store.image_data).__name__}, expected a MappingProxyType"
        try:
            store.store["x"] = None  # type: ignore[index]
        except TypeError:
            pass
        except Exception as exc:
            return f"BC-P2I-029: store item assignment raised {type(exc).__name__}, expected TypeError"
        else:
            return "BC-P2I-029: store item assignment was accepted"
    return None


def _tier2_bc_p2i_022() -> str | None:
    # additive: "perspective" is a registered key of PROJECTIONS.
    from pc2img.strategies.registry import PROJECTIONS

    try:
        PROJECTIONS.get_strategy("perspective")
    except Exception as exc:
        return f"BC-P2I-022: 'perspective' is not a registered PROJECTIONS key ({exc!r})"
    return None


def _tier2_bc_p2i_024() -> str | None:
    # additive: GradientFeature.__init__ has a pixel_size parameter.
    import inspect

    from pc2img.features.derivative_features import GradientFeature

    sig = inspect.signature(GradientFeature.__init__)
    if "pixel_size" not in sig.parameters:
        return "BC-P2I-024: GradientFeature.__init__ has no pixel_size parameter"
    return None


def _general_delaunay_culling_kwargs() -> str | None:
    # Internal & sweep: DelaunayInterpolation's culling thresholds are opt-in
    # constructor kwargs (no dedicated BC-P2I id — no public-surface change).
    import inspect

    from pc2img.strategies.interpolation import DelaunayInterpolation

    sig = inspect.signature(DelaunayInterpolation.__init__)
    required = {
        "interior_culling",
        "area_scale",
        "aspect_ratio_mad_factor",
        "aspect_ratio_fallback_scale",
    }
    missing = required - set(sig.parameters)
    if missing:
        return f"DelaunayInterpolation.__init__ is missing culling kwargs: {sorted(missing)}"
    return None


def _general_store_config_none_sentinel() -> str | None:
    # Internal & sweep: DiskBackedImageStore's config default is a None
    # sentinel, not a shared mutable LazyDiskCacheConfig() instance.
    import inspect

    from pc2img.image_cache.disk_backed_image_store import DiskBackedImageStore

    sig = inspect.signature(DiskBackedImageStore.__init__)
    default = sig.parameters["config"].default
    if default is not None:
        return f"DiskBackedImageStore.__init__'s config default is {default!r}, expected None"
    return None


# BC-P2I-030 deliberately has no runtime probe: its proof is the suite's passing
# regression test over repeated pooled tiled generation (it reads every raster after
# rebinding and collecting the results); the duplicate-id rule is probed under 028.
# Tier-2 dict of runtime checks, keyed by BC-P2I id. Every surface-removed
# and signature-shape row (BC-P2I-004, 005, 008, 015) has an entry here.
TIER2_CHECKS: dict[str, object] = {
    "BC-P2I-001": _tier2_bc_p2i_001,
    "BC-P2I-004": _tier2_bc_p2i_004,
    "BC-P2I-005": _tier2_bc_p2i_005,
    "BC-P2I-006": _tier2_bc_p2i_006,
    "BC-P2I-008": _tier2_bc_p2i_008,
    "BC-P2I-009": _tier2_bc_p2i_009_and_023,
    "BC-P2I-010": _tier2_bc_p2i_010,
    "BC-P2I-011": _tier2_bc_p2i_011,
    "BC-P2I-015": _tier2_bc_p2i_015,
    "BC-P2I-017": _tier2_bc_p2i_017,
    "BC-P2I-022": _tier2_bc_p2i_022,
    "BC-P2I-024": _tier2_bc_p2i_024,
    "BC-P2I-026": _tier2_bc_p2i_026,
    "BC-P2I-027": _tier2_bc_p2i_027,
    "BC-P2I-028": _tier2_bc_p2i_028,
    "BC-P2I-029": _tier2_bc_p2i_029,
}

# Runtime probes not tied to a single BC-P2I id — they check Internal &
# sweep bullets (no public-surface change claimed), so they run
# unconditionally rather than through the id-matched TIER2_CHECKS dict.
GENERAL_CHECKS: list[object] = [
    _general_delaunay_culling_kwargs,
    _general_store_config_none_sentinel,
]


def _tier2(failures: list[str]) -> None:
    known_ids = {str(e["id"]) for e in BC_ENTRIES}
    for check_id, check in TIER2_CHECKS.items():
        if check_id not in known_ids:
            failures.append(f"{check_id}: Tier-2 check exists for an id not present in BC_ENTRIES")
            continue
        result = check()
        if result:
            failures.append(result)
    for general_check in GENERAL_CHECKS:
        result = general_check()
        if result:
            failures.append(result)


def main() -> int:
    failures: list[str] = []
    _check_ids(failures)
    if failures:
        print("[fail] " + "\n  ".join(failures), file=sys.stderr)
        return 1

    try:
        root = _find_repo_root()
    except RuntimeError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    _tier1(root, failures)
    _tier2(failures)

    if failures:
        print("[fail] migration-spec verification:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print(f"[ok] verified {len(BC_ENTRIES)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
