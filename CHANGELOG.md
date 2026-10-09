# Changelog

## [0.11.0](https://github.com/gseg-ethz/pc2img/compare/v0.10.4...v0.11.0) (2026-10-09)


### ⚠ BREAKING CHANGES

* pc2img now requires GSEGUtils 0.6 (pinned ~= 0.6.0), pchandler 2.1.1 or newer (~= 2.1) and numpy 2.2 or newer (below 2.4), and the cuda11/cuda12 extras no longer pull cuml, cuproj or dask-cudf. Store-key validation and cache-directory containment are enforced by GSEGUtils: a raster or scalar-field name, tile id or cache-path segment containing a path separator, a backslash or a colon, ending in a dot or a space, equal to an empty, '.' or '..' name, or naming a Windows device is refused with StoreKeyError (a ValueError), and nested keys are no longer accepted. TiledPointCloudImageGenerator now raises ValueError at construction when two tiles share a tile id. On DiskBackedImageStore, del, pop, popitem and clear only drop tracking and leave the key's files on disk (a fresh store re-adopts them), and purge(key) is the delete verb that removes every key-derived file; add_image_to_store over a key that is tracked or whose .npy file is on disk now purges the previous entry first; add_image_to_store refuses a symlink at any write path it opens for the key (StorePurgeAliasedArtefactError when the link resolves inside the cache directory, StorePurgeForeignArtefactError when it resolves outside); an entry inserted through the mapping setter with a cache_path outside the cache directory can no longer be overwritten through add_image_to_store; and DiskBackedImageStore.store and image_data return a read-only mapping. TiledPointCloudImageGenerator.generate() now dispatches one task per tile, so repeated generate() calls on one instance, and mixed n_jobs sequences, return readable rasters on GSEGUtils 0.6.0; if a pooled call fails, the generators that existed before it are dropped. After a successful call, released results no longer delete their cache files, whatever n_jobs: with caching enabled the files persist until purge() is called or the directory is removed, except as described in the known limitation below. After a pooled run the parent process can neither purge nor overwrite a tile's store (StorePurgeRefusedError); use n_jobs=1 for every call on an instance you will purge from or overwrite, or a fresh generator. Known limitation after a failed generate() call with caching enabled: the files of a retry may be deleted when the failed call's objects are garbage-collected, and a later read of a retried raster may raise FileNotFoundError (GSEGUtils#83, fix planned for pc2img 0.11.1); retry with a fresh TiledPointCloudImageGenerator over a fresh cache_path.
* the 0.10 module layout is replaced wholesale by the 2.x architecture (strategies, features and image_cache packages). Registry misses raise RegistryLookupError; the never-functional make_generator factory and a dead duplicate convert_to_image are removed; matplotlib moves to the optional viz extra; the disk cache codec changes from pickle to .npy plus a JSON sidecar, so a cache directory persisted by an earlier build must be regenerated; a wrapping field of view, a 4x4 rotation_matrix and a non-pinhole intrinsics matrix are now rejected; nanconv accumulates in float32 and no longer mutates its input; DiskBackedImageData arithmetic returns a plain ndarray instead of raising; RRIM feature-name validation moves to request time and the z-factor token uses shortest round-trip formatting; numpy 2.x, pchandler 2.1 and GSEGUtils 0.5.3 or newer are required; the v2.0.0a5 tag is retired, so git-based pins on the 2.0.0a line must move to pc2img ~= 0.11 from PyPI.

### ✨ Features

* adopt GSEGUtils 0.6 and harden the release path for 0.11.0 ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **deps:** pin GSEGUtils ~= 0.6.0, pchandler &gt;= 2.1.1 (~= 2.1) and numpy &gt;= 2.2, &lt; 2.4; drop cuml, cuproj and dask-cudf from the cuda extras ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **image_cache:** delegate store-key validation, cache-directory containment and file deletion to GSEGUtils 0.6; purge(key) becomes the delete verb while del, pop, popitem and clear only drop tracking ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **image_cache:** expose DiskBackedImageStore.store and image_data as read-only mappings ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* publish the 2.x architecture as the 0.11 release line ([0819b2b](https://github.com/gseg-ethz/pc2img/commit/0819b2b754672829f45ac7e169de4e4707821266))
* **tiled:** reject duplicate tile ids at TiledPointCloudImageGenerator construction ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))


### 🐛 Bug Fixes

* **ci:** count only pull-request-triggered jobs as matchable required-status contexts in the ruleset preflight ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **ci:** recognise uv publish and composite-wrapped publish steps in the publish gate ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **docs:** fetch tags on Read the Docs even when the clone is already complete ([20ef688](https://github.com/gseg-ethz/pc2img/commit/20ef688c161804aed80ab7c3d5922cf6e013bf90))
* **docs:** fetch tags with --force on Read the Docs and assert a real installed version after the install ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **image_cache:** purge the previous entry on add_image_to_store when the key is tracked or its .npy is on disk, so a fresh store never serves a stale raster ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **image_cache:** refuse symlinked write paths on add_image_to_store (aliased inside the cache directory or foreign outside it) ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **tiled:** dispatch one tile per loky task instead of pickling the whole generator, so repeated generate() calls and mixed n_jobs sequences return readable rasters ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))
* **tiled:** keep pooled results from deleting their cache files on release; files persist until purge() or directory removal ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))


### 📚 Documentation

* Create LICENSE ([f946268](https://github.com/gseg-ethz/pc2img/commit/f946268ed96ad64c4341734d4076150f03bc7ac3))
* **rulesets:** name the five read-filled ruleset fields the drift comparator ignores unless set ([a770746](https://github.com/gseg-ethz/pc2img/commit/a770746bb15b9a0c38faddf4d4ec092b2f798ee1))


### 🧹 Miscellaneous Chores

* **license:** switch from MIT to BSD-3-Clause ([ade40f8](https://github.com/gseg-ethz/pc2img/commit/ade40f85a18729290d50e05ce5da0c2d98f45c20))
* Merge branch 'main' of github.com:gseg-ethz/pc2img ([69224a9](https://github.com/gseg-ethz/pc2img/commit/69224a9644046386264d23dc568f9719b5a89da8))


### 🤖 Continuous Integration

* **rulesets:** normalise the unattributed-changes approval key GitHub fills on read ([6e759d3](https://github.com/gseg-ethz/pc2img/commit/6e759d3af5e0fe2862c7ffc7ef8606f716e4b575))

## [0.10.4](https://github.com/gseg-ethz/pc2img/compare/v0.10.3...v0.10.4) (2025-04-15)


### ✨ Features

* Updated the changelog sections ([d32f783](https://github.com/gseg-ethz/pc2img/commit/d32f78393fb60d589c14e2b17a8e7a4dea8871ce))


### 🐛 Bug Fixes

* added current version to manifest ([3441411](https://github.com/gseg-ethz/pc2img/commit/34414119ddf9185d29985ad7159d80bf0d8771e9))

## [0.10.3](https://github.com/gseg-ethz/pc2img/compare/v0.10.2...v0.10.3) (2025-04-15)


### 🐛 Bug Fixes

* Removed manifest file ([107ae10](https://github.com/gseg-ethz/pc2img/commit/107ae101f87f0f24d45b1c2e53926869fe8afdb3))

## [0.10.2](https://github.com/gseg-ethz/pc2img/compare/v0.10.1...v0.10.2) (2025-04-15)


### 🧰 Miscellaneous

* Added changelog decorators ([121eb55](https://github.com/gseg-ethz/pc2img/commit/121eb55b7e8ac9c8f4e8b1d63a8b8bf086b0520c))
* Added release-please.yml ([d09addb](https://github.com/gseg-ethz/pc2img/commit/d09addb55aeb50a226e91d1a99a9b90fcf1739e7))
* bootstrap releases for path: . ([80c1c1e](https://github.com/gseg-ethz/pc2img/commit/80c1c1ee922c4dfe2f15fae3427394ab1812266e))
* bootstrap releases for path: . ([c7a9623](https://github.com/gseg-ethz/pc2img/commit/c7a962305f63f72335ab1948a22fed9c2144b468))
* **main:** release 0.10.1 ([a62d8ca](https://github.com/gseg-ethz/pc2img/commit/a62d8cafcb8ed75a28feb4554e4d15b2859c1104))
* **main:** release 0.10.1 ([3843536](https://github.com/gseg-ethz/pc2img/commit/3843536a49736583b47325a22506ec9f6dcd4967))
* Merge branch 'feature/release-please' ([ab2f29c](https://github.com/gseg-ethz/pc2img/commit/ab2f29c1aa24718b52726b7670ca28e3a3155ec7))
* Merge pull request [#2](https://github.com/gseg-ethz/pc2img/issues/2) from gseg-ethz/release-please--branches--main ([a62d8ca](https://github.com/gseg-ethz/pc2img/commit/a62d8cafcb8ed75a28feb4554e4d15b2859c1104))
* Removed old semver strategy ([bcc4754](https://github.com/gseg-ethz/pc2img/commit/bcc4754dbb24d4a338c024473a31d382c0c06839))

## [0.10.1](https://github.com/gseg-ethz/pc2img/compare/v0.10.0...v0.10.1) (2025-04-15)


### 🧰 Miscellaneous

* Added changelog decorators ([121eb55](https://github.com/gseg-ethz/pc2img/commit/121eb55b7e8ac9c8f4e8b1d63a8b8bf086b0520c))
* Added release-please.yml ([d09addb](https://github.com/gseg-ethz/pc2img/commit/d09addb55aeb50a226e91d1a99a9b90fcf1739e7))
* bootstrap releases for path: . ([80c1c1e](https://github.com/gseg-ethz/pc2img/commit/80c1c1ee922c4dfe2f15fae3427394ab1812266e))
* bootstrap releases for path: . ([c7a9623](https://github.com/gseg-ethz/pc2img/commit/c7a962305f63f72335ab1948a22fed9c2144b468))
* Merge branch 'feature/release-please' ([ab2f29c](https://github.com/gseg-ethz/pc2img/commit/ab2f29c1aa24718b52726b7670ca28e3a3155ec7))
* Removed old semver strategy ([bcc4754](https://github.com/gseg-ethz/pc2img/commit/bcc4754dbb24d4a338c024473a31d382c0c06839))
