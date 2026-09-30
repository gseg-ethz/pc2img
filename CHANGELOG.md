# Changelog

## [0.11.0](https://github.com/gseg-ethz/pc2img/compare/v0.10.4...v0.11.0) (2026-09-30)


### ⚠ BREAKING CHANGES

* the 0.10 module layout is replaced wholesale by the 2.x architecture (strategies, features and image_cache packages). Registry misses raise RegistryLookupError; the never-functional make_generator factory and a dead duplicate convert_to_image are removed; matplotlib moves to the optional viz extra; the disk cache codec changes from pickle to .npy plus a JSON sidecar, so a cache directory persisted by an earlier build must be regenerated; a wrapping field of view, a 4x4 rotation_matrix and a non-pinhole intrinsics matrix are now rejected; nanconv accumulates in float32 and no longer mutates its input; DiskBackedImageData arithmetic returns a plain ndarray instead of raising; RRIM feature-name validation moves to request time and the z-factor token uses shortest round-trip formatting; numpy 2.x, pchandler 2.1 and GSEGUtils 0.5.3 or newer are required; the v2.0.0a5 tag is retired, so git-based pins on the 2.0.0a line must move to pc2img ~= 0.11 from PyPI.

### ✨ Features

* publish the 2.x architecture as the 0.11 release line ([0819b2b](https://github.com/gseg-ethz/pc2img/commit/0819b2b754672829f45ac7e169de4e4707821266))


### 🐛 Bug Fixes

* **docs:** fetch tags on Read the Docs even when the clone is already complete ([20ef688](https://github.com/gseg-ethz/pc2img/commit/20ef688c161804aed80ab7c3d5922cf6e013bf90))


### 📚 Documentation

* Create LICENSE ([f946268](https://github.com/gseg-ethz/pc2img/commit/f946268ed96ad64c4341734d4076150f03bc7ac3))


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
