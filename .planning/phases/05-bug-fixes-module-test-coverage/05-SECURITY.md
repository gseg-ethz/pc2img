---
phase: 05
slug: bug-fixes-module-test-coverage
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-11
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register origin: `register_authored_at_plan_time: true` (all 12 PLANs carried a
> `<threat_model>` block). ASVS L1, `block_on: high`. Verified via L1 grep-depth
> evidence over the implementation plus the green full suite (111 passed).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| cache dir (disk) → process | GSEGUtils `DiskBackedStore` reloads offloaded rasters from `cache_path`/temp dir; a shared/attacker-controlled cache dir is the only untrusted surface in the library | serialized rasters (`.npy`) + `.meta.json` sidecars |
| caller → library API | numeric arrays, FoV objects, feature-name strings, and config cross the pydantic-coerced public API into pure-math projection/interpolation/feature code | numpy arrays, DSL strings (regex-validated), config objects |
| pip/uv install | dependency resolution surface | package names / versions |

All auth / session / access-control / crypto ASVS categories are **N/A** — pc2img is an importable scientific library with no server, no network I/O, and no secret handling.

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-09a (DSN-09 / T-04-J) | Tampering / RCE | image store arbitrary-object deserialization sink (ASVS V5) | high | mitigate | D-05: `DiskBackedImageStore` reparented onto GSEGUtils `DiskBackedStore` `.npy`+JSON `allow_pickle=False` codec + explicit class allow-list; arbitrary-code sink eliminated by construction, legacy `.pkl` refused as a cache miss (`src/pc2img/image_cache/disk_backed_image_store.py`) | closed |
| T-05-09b | Tampering | reload class resolution | high | mitigate | Class registered via explicit GSEGUtils allow-list hook; `_resolve_lazy_disk_cache_class` is a pure `_LAZY_DISK_CACHE_CLASS_REGISTRY` dict lookup raising `ValueError` on unknown names — **no importlib fallback**, crafted `.meta.json` cannot instantiate an unregistered class | closed |
| T-05-08a | Tampering / Elevation | reload class resolution (ASVS V5) | high | mitigate | New `register_lazy_disk_cache_class` hook only ADDS a registration API over the same explicit allow-list; D-02 posture preserved (no importlib), verified in installed GSEGUtils 0.5.3 | closed |
| T-05-05a | Tampering | silent interior NaN culling (M-06) | high | accept | KEPT-BEHAVIOR (D-06): intentional, downstream-validated; documented + characterization-pinned + thresholds now tunable (see Accepted Risks) | closed |
| T-05-10a | Tampering | silent `interp_kwargs` loss on tiled path (DSN-01/BUG-03) | high | mitigate | Build dict then assign (`extended_interp_kwargs = dict(...)`); no `.update()`→None trap (`src/pc2img/tiled_generator.py`) | closed |
| T-05-08b | Tampering | unreviewed cross-repo dependency edit | medium | mitigate | Blocking human-verify checkpoint (dependency-approval gate); owner APPROVED the GSEGUtils diff before 05-09 consumed it | closed |
| T-05-09c | Denial of Service | broken intermediate (reparent without store swap) | medium | mitigate | D-04+D-05 landed together in one plan; full-suite gate before merge (111 passed) | closed |
| T-05-02a | Tampering | SphericalProjection wrapping-FoV silent reversal | medium | mitigate | D-15: `_reject_wrapping_fov` converts silent reversed-columns into explicit `NotImplementedError` | closed |
| T-05-03a | Tampering | `nanconv` in-place mutation of caller array | medium | mitigate | M-07: copy input before zeroing NaNs (no side-effect corruption) | closed |
| T-05-03b | Denial of Service | `nanconv` float16 inf/nan on realistic magnitudes | medium | mitigate | M-08/D-09: accumulate/divide in float32 | closed |
| T-05-04a | Tampering | NormalizedFeature in-place mutation of cached raster | medium | mitigate | DSN-03: copy-before-mutate (no cache corruption on view returns) | closed |
| T-05-11b | Tampering | stale accumulated base-feature specs on generator reuse (DSN-04) | medium | mitigate | Reset `_base_features` per `request()` | closed |
| T-05-12a | Repudiation | undocumented breaking changes for downstream consumers | medium | mitigate | D-17: consolidated BC-01 note (`05-BC-NOTES.md`) records every public API/behavior/format change | closed |
| T-05-02b | Information Disclosure | perspective phantom behind-camera projections | low | mitigate | M-02 depth cull (`Z_c>0`) removes false in-bounds points | closed |
| T-05-04b | Improper Input Validation (ASVS V5) | commented-out percentile bounds check | low | mitigate | M-12: re-enable `0<=low<=high<=100` validation | closed |
| T-05-06a | Tampering | RRIM ray under-sampling (M-13) | low | accept | DEFER/LOG (D-16): opt-in feature, math CONFIRMED-CORRECT (see Accepted Risks) | closed |
| T-05-07a | Tampering | side-effectful double class construction in `match()` | low | mitigate | DSN-05: `dependencies_for` reads deps without instantiation | closed |
| T-05-07b | Repudiation | divergent miss-exception contracts confuse callers | low | mitigate | D-14: single `RegistryLookupError`; dual inheritance preserves catch behavior | closed |
| T-05-10b | Denial of Service | shared-mutable default config leak (DSN-07) | low | mitigate | None-sentinel default (no shared instance) | closed |
| T-05-11a | Denial of Service | unbounded recursion on cyclic feature graph (DSN-08) | low | mitigate | Visited-set guard raises clear `ValueError('dependency cycle: ...')` | closed |
| T-05-11c | Denial of Service | shared-mutable default config (DSN-07) | low | mitigate | None-sentinel default | closed |
| T-05-12b | Denial of Service | coverage floor overshoot blocking CI | low | mitigate | Ratchet to measured baseline minus documented xfail-volatility margin | closed |
| T-05-SC | Tampering | pip/uv installs | low | accept | No new packages installed this phase (05-RESEARCH.md Package Legitimacy Audit); GSEGUtils consumed via PyPI 0.5.3 pin (see Accepted Risks) | closed |
| T-05-13a | Denial of Service | RRIM feature family dependency resolution (gap G1) | high | mitigate | `dependencies_for` overrides on all three RRIM classes schedule the base+pack rasters; end-to-end `generate([...])` proving tests guard the regression class (05-13) | closed |
| T-05-13b | Tampering | PerspectiveProjection intrinsics K (gap G2) | high | mitigate | K validated 3×3 + pinhole bottom-row so the perspective divisor stays sign-aligned with the M-02 depth cull (no phantom mislocation) (05-13) | closed |
| T-05-13c | Tampering | DiskBackedImageStore overwrite/delete (gap G3) | medium | mitigate | `__delitem__` purges the `<key>.npy`+`.meta.json` codec pair so a re-scanned store never serves a stale raster (05-13) | closed |
| T-05-13d | Tampering | rotation orthonormality accept/reject boundary (gap G4) | low | mitigate | check moved to float64 so a valid double-precision rotation is not false-rejected (05-13) | closed |
| T-05-13e | Repudiation | duplicated dependency-grammar / percentile-bounds logic (gaps G5/G6/G8) | low | mitigate | single-sourced each rule so semantics cannot silently drift between call sites (05-13) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `block_on: high` count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-05a | Silent interior NaN culling in Delaunay interpolation is intentional, downstream-validated behavior (D-06); characterization-pinned by tests and thresholds are now tunable; refinement deferred | owner (Phase 05 disposition) | 2026-07-11 |
| AR-05-02 | T-05-06a | RRIM ray under-sampling affects sampling fidelity only on an opt-in feature; core math is CONFIRMED-CORRECT; logged as future improvement (D-16) | owner (Phase 05 disposition) | 2026-07-11 |
| AR-05-03 | T-05-SC | No new packages installed this phase; GSEGUtils reload-registration hook shipped in published 0.5.3 and is consumed via the `GSEGUtils >= 0.5.3, < 1.0` PyPI pin (git-rev bridge retired) | owner (Phase 05 disposition) | 2026-07-11 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-11 | 23 | 23 | 0 | /gsd-secure-phase (L1 short-circuit: register_authored_at_plan_time=true, asvs_level=1, threats_open=0) |
| 2026-07-11 | 28 | 28 | 0 | gap-closure 05-13 folded in (+5 threats T-05-13a..e, all mitigated; verified in-code + suite 135 passed) |

**Material security deliverable of the phase:** T-05-09a — elimination of the DSN-09
arbitrary-object deserialization sink by reparenting `DiskBackedImageData`/`DiskBackedImageStore`
onto GSEGUtils' hardened `DiskBackedStore` (`.npy` + JSON, `allow_pickle=False`, explicit class
allow-list with no importlib fallback). Verified at L1 grep-depth in the implementation and
exercised by the disk-backed round-trip suite (25 passed) within the green full suite (111 passed).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-11
