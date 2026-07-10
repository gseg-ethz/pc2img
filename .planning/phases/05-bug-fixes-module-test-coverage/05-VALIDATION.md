---
phase: 5
slug: bug-fixes-module-test-coverage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-10
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `05-RESEARCH.md` § Validation Architecture. Test-first per D-12:
> genuine fixes ship as `xfail` proving tests first (flip to `pass` on fix);
> kept-behavior findings (M-06/M-10/M-11) ship as passing characterization tests.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `~=9.1` + pytest-cov `~=5.0` + coverage `~=7.0` |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `addopts="--import-mode=importlib --strict-markers"`) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ --cov=pc2img --cov-branch --cov-report=term-missing` |
| **Estimated runtime** | ~30 seconds (deterministic synthetic fixtures; no binary I/O) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q` (fast subset for the touched module)
- **After every plan wave:** Run `pytest tests/ --cov=pc2img --cov-branch`
- **Before `/gsd-verify-work`:** Full suite green + coverage re-measured and `--cov-fail-under` ratcheted up to the new baseline (D-10; current floor 35%, baseline 37%)
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

> Task IDs are assigned by the planner. Rows below map each phase requirement /
> finding to its behavioral sensor (from RESEARCH § Phase Requirements → Test Map).
> The planner MUST attach an `<automated>` verify command to each fix/coverage task
> that runs the corresponding test target below.

| Finding / REQ | Test type | Sensor sufficiency | Test target |
|---------------|-----------|--------------------|-------------|
| M-01 (BUG-01) | property (parametrized xy/yz/xz) | Equality to hand-computed normalized cols (not a diagonal) | `tests/test_projection.py` |
| DSN-02 (BUG-02) | simple assertion | `dbid + dbid == arr + arr`, result is plain ndarray; **offload→reload round-trip** | `tests/test_disk_backed_image_data.py`, `tests/test_image_store.py` |
| DSN-01 (BUG-03) | simple assertion | `extend_cache_paths` result `interp_kwargs` is a dict, not `None` | `tests/test_tiled_generator.py` |
| BUG-04 | simple assertion | `rrim.__doc__` is non-empty; no E402 | `tests/test_rrim_features.py` |
| M-02/M-03/M-04 | property + simple | Behind-camera (`Z_c≤0`) point masked; pixel == `K·[R\|t]·X`; dead override gone | `tests/test_projection.py` |
| M-05 (D-15) | simple assertion | Wrapping (`crosses_pi`) FoV raises in `project_raw` AND `inverse_projection` | `tests/test_projection.py` |
| M-06 (kept) | held-out oracle | `scipy.LinearNDInterpolator` reference (NaN iff `find_simplex==-1`); anisotropic grid triggers culling | `tests/test_interpolation.py` |
| M-07 | simple assertion | `nanconv` does not mutate input (`isnan` snapshot equal) | `tests/test_util.py` |
| M-08 | property (magnitudes {5e3,1.2e4,5e4} × kernels) | Finite & within float32 tol of float64 ref (overflow is magnitude-dependent) | `tests/test_util.py` |
| M-09 | simple assertion | all-NaN + `normalize=True` → valid uint8, no raise | `tests/test_util.py` |
| M-10 (kept) | characterization | Default output byte-identical; new `pixel_size` param default reproduces it | `tests/test_derivative_features.py` |
| M-11 (kept) | characterization | Hillshade internal self-consistency (azimuth sweep), NOT ESRI compass | `tests/test_derivative_features.py` |
| DSN-03 + M-12 | simple assertion | `NormalizedFeature` percentile bounds validated; input not mutated in place | `tests/test_derivative_features.py` |
| D-14 (DSN-05) | simple assertion | Unified miss type caught by `except KeyError`; `dependencies_for` returns deps without instantiation; feature default-fallback preserved | `tests/test_feature_registry.py` |
| DSN-06 | existing xfail flips | `test_point_cloud_image_generator.py:35` (omitted-config coercion) | `tests/test_point_cloud_image_generator.py` |
| DSN-09 (security) | simple assertion | Store no longer calls `pickle.load`; legacy `.pkl` → cache miss | `tests/test_image_store.py` |
| DSN-04/07/08/10/11 | simple assertions | Deterministic single-path checks (reset/default-identity/cycle-guard/import/typing) | `tests/test_manager.py`, `tests/test_tiled_generator.py` |
| TEST-03..06 | behavioral coverage | Each previously-untested module exercised via its behavioral sensors above | per-module test files |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — synthetic `PointCloudData(xyz)` factory (`synthetic_pcd(n=…, with_scalar_fields=…)`) + `fetch` stub + `fake_projection` helper (D-11). **Does not exist yet.**
- [ ] `tests/test_projection.py` — TEST-03 (real PCD): M-01, M-02/03/04, M-05
- [ ] `tests/test_interpolation.py` — TEST-03 (pure arrays): M-06, barycentric oracle
- [ ] `tests/test_derivative_features.py` — TEST-04 (fetch stub): M-10, M-11, DSN-03, M-12
- [ ] `tests/test_feature_registry.py` — TEST-04: DSL match, `dependencies_for`, unified miss type
- [ ] `tests/test_manager.py` — TEST-05 (minimal PCD): DSN-04, DSN-06, DSN-08
- [ ] `tests/test_tiled_generator.py` — TEST-05: DSN-01 (BUG-03), DSN-10
- [ ] `tests/test_util.py` — TEST-06 (pure arrays): M-07, M-08, M-09, `replace_nan`, `to_gray`
- [ ] `tests/test_image_store.py` — D-05: pickle-sink removed, legacy `.pkl` refused, offload→reload round-trip
- [ ] Flip existing xfails: `test_point_cloud_image_generator.py:35`; `test_disk_backed_image_data.py` :50,:115,:155,:175,:241

---

## Manual-Only Verifications

*None — all phase behaviors have automated (pytest) verification. The GSEGUtils
public class-registration change (D-05 Option A, owner-approved) is verified
indirectly by the `tests/test_image_store.py` offload→reload round-trip.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
