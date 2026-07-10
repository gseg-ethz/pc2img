---
phase: 03-test-ci-foundation
reviewed: 2026-07-09T00:00:00Z
depth: deep
files_reviewed: 5
files_reviewed_list:
  - .github/workflows/ci.yml
  - src/pc2img/features/rrim.py
  - tests/test_disk_backed_image_data.py
  - tests/test_point_cloud_image_generator.py
  - tests/test_rrim_features.py
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-07-09T00:00:00Z
**Depth:** deep
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the Phase 3 (Test & CI Foundation) artifacts at deep depth: the new PR CI
workflow, the RRIM feature module brought under version control unchanged, and the
three scoped test modules with their deliberate `xfail(strict=False)` triage markers.

Overall the phase deliverables are sound. The CI workflow correctly installs from a
committed frozen lock (`uv.lock` confirmed present), runs the scoped suite with a
branch-coverage gate that matches the `--cov-fail-under=21` floor recorded in
`CONTRIBUTING.md`, and applies a least-privilege `contents: read` token. The clever
detail — loading `rrim.py` from the real `src/` path under an alias package so it is
still attributed to `pc2img` by coverage `source=["pc2img"]` — checks out.

No BLOCKER-class defects found. Findings cluster around: (1) a genuine test-isolation
fragility in `test_rrim_features.py` that mutates global `sys.modules` without cleanup,
which — under a non-alphabetical collection order — could turn a *non-xfail* test into a
hard error; (2) a latent cache-key omission in `rrim.py` (pre-existing, unreachable via
the current name DSL); and (3) CI robustness gaps (no job timeout / concurrency).

The `xfail(strict=False)` markers were treated as intended triage per D-01 and are NOT
flagged. RRIM correctness findings are reported as **pre-existing** (the module was not
authored this phase) to feed Phase 4/5, per the review brief.

## Narrative Findings (AI reviewer)

_No `<structural_findings>` substrate was provided for this review; all findings below
are from direct code reading._

## Warnings

### WR-01: Global `pchandler` stub in `test_rrim_features.py` mutates `sys.modules` with no cleanup

**File:** `tests/test_rrim_features.py:29-55` (esp. 30-37), also relevant `tests/test_point_cloud_image_generator.py:6`
**Issue:**
`_load_rrim_modules()` runs at **module import / collection time** (line 55) and, when
`"pchandler" not in sys.modules`, installs a bare stub module whose `PointCloudData`
class takes no constructor arguments (`class PointCloudData: pass`). This stub is never
removed — there is no `conftest.py` and no teardown/monkeypatch (confirmed: `tests/` has
no `conftest.py`). The safety here depends entirely on collection order:

- `test_point_cloud_image_generator.py` binds the **real** `PointCloudData` at its own
  module top (`from pchandler import PointCloudData`, line 6) and calls
  `PointCloudData(np.empty((0, 3)))` (line 32).
- Because default pytest collection is alphabetical, `test_point_cloud...` (`p`) is
  collected before `test_rrim...` (`r`), so the real `pchandler` is already in
  `sys.modules` and the stub guard short-circuits. Safe *today*.
- If collection order is ever changed (custom ordering plugin, `-p randomly`, explicit
  file args like `pytest tests/test_rrim_features.py tests/test_point_cloud_image_generator.py`,
  or a future rename), the stub is installed first. `test_point_cloud...`'s real import
  would then resolve to the stub, and `PointCloudData(np.empty((0, 3)))` raises
  `TypeError` (stub takes no args). That test's second case,
  `test_constructor_normalizes_explicit_none_lazy_disk_cache_config` (line 56), is **not**
  xfail — so it would become a hard CI error, not a triaged xfail.

This is a latent "green suite depends on filename alphabetization" trap in exactly the
harness this phase exists to make trustworthy.

**Fix:** Isolate the stub so it cannot leak into other modules. Prefer a fixture that
saves/restores `sys.modules` state, or install the stub only under a guard that also
restores on teardown. Minimal robust form:

```python
# tests/conftest.py (new) — or scope inside test_rrim_features via a fixture
import sys, pytest

@pytest.fixture(autouse=True, scope="module")
def _preserve_sys_modules():
    saved = dict(sys.modules)
    yield
    # drop anything the module inserted (pchandler stub, rrim_testpkg.*)
    for name in list(sys.modules):
        if name not in saved:
            del sys.modules[name]
    sys.modules.update({k: v for k, v in saved.items() if k in ("pchandler",)})
```

Alternatively, since `rrim.py` only needs `pchandler.PointCloudData` transitively via
`features/core.py`, gate the stub install behind `importlib.util.find_spec("pchandler") is None`
so a real install is never shadowed.

### WR-02: RRIM `pack_feature_name()` omits `pixel_size` from the cache/dependency key (latent collision) — pre-existing

**File:** `src/pc2img/features/rrim.py:65-69` (with `280`-ish consumers `compute_openness` at 222-233, `_build_ray_offsets` at 180-204)
**Issue:**
`pack_feature_name()` encodes only `base_feature`, `max_distance` (`r`), `num_directions`
(`d`) and `z_factor` (`z`). The openness computation the pack memoizes also depends on
`pixel_size`: `_build_ray_offsets(num_directions, max_distance, pixel_size)` derives ray
`distance = hypot(dx*pixel_size[0], dy*pixel_size[1])`, and `compute_openness` feeds those
distances into the openness angles. Two `RRIMConfig`s that differ **only** in `pixel_size`
produce the same pack name, so a `DiskBackedImageStore` memoization keyed on that name
would return the wrong cached raster for the second config.

This is currently **unreachable via the feature-name DSL** — `_parse_option_token`
(lines 381-409) exposes no `pixel_size` token, so DSL-constructed configs always use the
default `(1.0, 1.0)`. It is a latent correctness hazard only for callers that build
`RRIMConfig`/call `compute_rrim` with a non-default `pixel_size` while relying on
pack-name-based memoization. Flagging for Phase 5 because it is a silent-wrong-result
class of bug, not a crash.

**Fix:** Include `pixel_size` (and, if pack semantics ever expand, any other
openness-affecting field) in the pack name, or assert that pack-keyed features never vary
`pixel_size`:

```python
def pack_feature_name(self) -> str:
    px = f"{_format_number(self.pixel_size[0])}x{_format_number(self.pixel_size[1])}"
    return (
        f"rrim_pack_({self.base_feature},"
        f"r{self.max_distance},d{self.num_directions},"
        f"z{_format_number(self.z_factor)},p{px})"
    )
```

Note this requires a matching token in the parser if the name must round-trip through the
registry; otherwise keep `pixel_size` off the DSL and document that pack memoization is
only valid at the default spacing.

### WR-03: CI job has no `timeout-minutes` — a hung test can hold a runner for the 6-hour default

**File:** `.github/workflows/ci.yml:16-19`
**Issue:**
The `tests` job sets no `timeout-minutes`. A deadlocked test or a hang in the
joblib/loky-backed code paths would run until GitHub's default 360-minute ceiling before
being killed, wasting the runner and delaying feedback. For a "lightweight PR CI" whose
whole point is fast signal, an explicit cap is cheap insurance.

**Fix:**
```yaml
jobs:
  tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

## Info

### IN-01: No `concurrency` group — redundant runs on rapid pushes

**File:** `.github/workflows/ci.yml:16-19`
**Issue:** Successive pushes to an open PR start parallel CI runs; earlier ones are not
auto-cancelled. Not a correctness issue, but a small cost/robustness improvement.
**Fix:**
```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

### IN-02: `astral-sh/setup-uv@v8.3.2` version-tag pin — verify it resolves on CI

**File:** `.github/workflows/ci.yml:27`
**Issue:** SHA-pinning is explicitly deferred to Phase 6, so a version-tag pin is
acceptable for this phase. Flagging only so someone confirms `v8.3.2` is a real published
tag of `astral-sh/setup-uv`; an unresolvable tag would fail every CI run. (`actions/checkout@v5`,
`actions/upload-artifact@v4` are standard.) A first green run on this branch is sufficient
verification.
**Fix:** Confirm the first CI run resolves the action; pin to a SHA in Phase 6.

### IN-03: Redundant coverage flags between CLI and config

**File:** `.github/workflows/ci.yml:43-45` vs `pyproject.toml:115-118`
**Issue:** `--cov-branch` on the CLI duplicates `branch = true` in `[tool.coverage.run]`,
and `--cov=pc2img` duplicates `source = ["pc2img"]`. Harmless and arguably deliberate
(keeps the CI command self-describing), but worth noting so the two do not drift apart —
e.g. a future edit to `source` would be silently overridden by the CLI `--cov=pc2img`.
**Fix:** Optional — either drop the redundant CLI flags and rely on config, or add a
comment that the CLI form is intentionally authoritative.

### IN-04: RRIM is a patented algorithm — IP/legal gate before any public push (pre-existing, already tracked)

**File:** `src/pc2img/features/rrim.py` (whole module)
**Issue:** "RRIM" (Red Relief Image Map) is a proprietary/patented visualization method
(Asia Air Survey). This is out of scope as a *code* defect, but it is a genuine
ship-blocker for the public-`main` push this milestone targets, and the repo already
carries a todo flagging it (commit `9992ce3`, "flag RRIM patent/IP review as blocking
before public push"). Recorded here so the code-review trail cross-references it; no code
change implied.
**Fix:** Resolve the IP review before stripping `.planning/` and publishing to `main`;
not a Phase 3 action.

---

_Reviewed: 2026-07-09T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
