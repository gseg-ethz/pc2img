# Spike Manifest

## Idea

Determine whether GSEGUtils can retire `DiskBackedStore`'s suffix-override extension
points (`_DBNDArrayFileExt`, `_DBNDArrayMetaExt`, `_LegacyPickleExt`, `_get_npy_path`)
without breaking pc2img — and, if so, what migration pc2img needs. The working
hypothesis is **absorption**: GSEGUtils phase-14 enforces containment natively at every
path builder, so pc2img's downstream `_get_npy_path` / `_get_meta_path` override (WR-02,
commit `03eb715`) is the class of downstream patch the upstream work exists to make
redundant. The spikes prove or disprove absorption by measurement, not by reading.

## Requirements

Design decisions established during spiking. Non-negotiable for the real build.

- **pc2img is private, pre-release alpha with no external consumers.** The GSEGUtils
  deprecation notice on `_get_npy_path` was self-granted leeway, not a third-party
  promise. Breaking changes are acceptable.
- **Do not argue to preserve the override.** Subclassing development in pc2img was
  deliberately stopped because it patched downstream what belonged upstream. The job is
  to prove or disprove absorption, not to defend the patch.
- **Import provenance must be asserted inside the test process**, not assumed from the
  shell. The installed wheel is GSEGUtils 0.5.3, which still routes through
  `self._get_npy_path` — running against it produces a false green. Every spike script
  prints `GSEGUtils.__file__`, `__version__`, and the
  `grep -c 'self\._get_npy_path' == 0` fingerprint before any assertion.
- **A partial survivor is the most valuable possible result.** Do not smooth one over.
- **Investigation only** — no pc2img source changes. Override removal is simulated by a
  local subclass, never by editing the tree.

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
| 000 | absorption-test | standard | Phase 5 escape corpus vs phase-14 with the override removed — every input still refused upstream (folds in the old 002 ground-truth cache listing) | ✓ VALIDATED | gsegutils, containment, wr-02, absorption, security |
| 001 | orphaned-override-hunt | standard | Every pc2img override of a GSEGUtils `self._*` method that upstream stopped calling — each hit is either absorbed (deletable) or an upstream gap. Includes the BC-GSEG-006 `extend_cache_path` drift re-derivation | PENDING | gsegutils, mro, bc-gseg-006, drift |
| 004 | blast-radius-phase14 | standard | pc2img's 175-test suite against phase-14 with the override removed — weak confirmation that nothing else was load-bearing | PENDING | gsegutils, regression, blast-radius |

**Dropped from the original decomposition:**

- **003 reopen-rescan-reliance** — dropped. Its trigger is a repointed
  `_DBNDArrayFileExt`; pc2img assigns none of the three suffix attributes anywhere
  repo-wide, so the D-26 adoption defect cannot fire here.
- **002 write-path-ground-truth** — folded into 000.
- The "simulated 0.6.0 with attributes deleted" arm of 004 — dropped; it measured a
  retirement-cost question that absorption already decides.
