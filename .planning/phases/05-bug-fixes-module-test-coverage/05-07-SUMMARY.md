---
phase: 05-bug-fixes-module-test-coverage
plan: 07
subsystem: testing
tags: [registry, RegistryLookupError, dependencies_for, feature-dsl, pyright, DSN-05, DSN-11, D-14, BUG-05, TEST-04, BC-01]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: "05-01 Wave-0 xfail sensor conventions; 05-04 derivative_features.py fixes (this plan adds dependencies_for overrides to the same file, hence wave-3 + depends_on 05-04 to avoid a same-wave collision)"
  - phase: 04-code-quality-algorithmic-soundness-review
    provides: "04-FINDINGS BUG-05 (registry divergence: KeyError vs RuntimeError; side-effectful double-construction in match()); DSN-05; DSN-11"
provides:
  - "RegistryLookupError(KeyError, RuntimeError) — single miss/duplicate exception shared by StrategyRegistry and FeatureRegistry; dual inheritance keeps every existing except KeyError / except RuntimeError caller catching it unchanged"
  - "dependencies_for(params) overridable classmethod on both feature ABCs — FeatureRegistry.match() now derives dependencies from the parsed groupdict WITHOUT constructing the feature (no more double __init__)"
  - "Per-class dependencies_for overrides on AverageFeature/SumFeature/NormFeature (split own regex group) and HillshadeFeature (optional base_feature defaults to range) so match() and construction agree"
  - "DSN-11: FeatureRegistry._default_cls typed type[BaseFeatureStrategy] | None; FeatureSpec attributes annotated; pyright on features/registry.py is clean (0 errors)"
  - "tests/test_feature_registry.py — TEST-04 feature-name DSL + registry-unification sensors (pure, no PCD)"
affects: [05-10, 05-11, 05-12, phase-6-BC-01, phase-6-D-17]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-inheritance unification: a single RegistryLookupError(KeyError, RuntimeError) collapses two divergent miss contracts while preserving 100% of existing catch behavior (zero caller edits)"
    - "Read-without-construct: an overridable dependencies_for classmethod reads deps from the regex groupdict, replacing a side-effectful double class construction in match()"
    - "Per-class override over generic name-branching (review concern #4): each split-list / defaulted-base family mirrors its own __init__ dep-derivation in its own dependencies_for override, rather than one base method branching on feature name"

key-files:
  created:
    - "src/pc2img/errors.py — RegistryLookupError(KeyError, RuntimeError) shared miss type"
    - "tests/test_feature_registry.py — 10 pure DSL/registry sensors (unified miss type, dual catch, dependencies_for no-construction, default-fallback preservation)"
  modified:
    - "src/pc2img/strategies/registry.py — miss/duplicate KeyError raises → RegistryLookupError (register, get_strategy, key_of); except KeyError callers untouched"
    - "src/pc2img/features/registry.py — RuntimeError raises → RegistryLookupError; match() uses cls.dependencies_for(spec.params) (no construction); default-fallback preserved; DSN-11 _default_cls typing + FeatureSpec annotations"
    - "src/pc2img/features/core.py — overridable dependencies_for classmethod on BaseFeatureStrategy and DerivativeFeatureStrategy (base handles the common base_feature grammar)"
    - "src/pc2img/features/derivative_features.py — dependencies_for overrides on AverageFeature/SumFeature/NormFeature (split own group) and HillshadeFeature (None→range)"

key-decisions:
  - "RegistryLookupError lives in a new leaf module src/pc2img/errors.py so both subpackages import it without a cycle"
  - "HillshadeFeature needed its OWN dependencies_for override (not in the plan's explicit list): its base_feature group is optional and defaults to 'range', which bare 'hillshade' relies on in scripts — the base impl returning [params['base_feature']]=[None] would have regressed it (Rule 2, honoring the must-have 'match() and construction agree')"
  - "FeatureSpec.cls and _default_cls annotated + a single cast to narrow the default (a base feature) satisfied the DSN-11 pyright gate to 0 errors without altering register() control flow"

patterns-established:
  - "Unify divergent exception contracts via dual inheritance rather than a breaking single-parent swap"
  - "match()/resolution reads structure from parsed params; construction is deferred to compute time"

requirements-completed: [BUG-05, TEST-04]

coverage:
  - id: D1
    description: "Both registries raise one miss type RegistryLookupError, still caught by existing except KeyError and except RuntimeError callers (D-14 / BUG-05)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_feature_registry.py#test_unknown_strategy_key_raises_unified_error_caught_as_keyerror"
        status: pass
      - kind: unit
        ref: "tests/test_feature_registry.py#test_ambiguous_feature_match_raises_unified_error_caught_as_runtimeerror"
        status: pass
      - kind: integration
        ref: "uv run --frozen pytest tests/ -q (103 passed, 1 xfailed — no existing caller broke)"
        status: pass
    human_judgment: false
  - id: D2
    description: "FeatureRegistry.match() derives dependencies via dependencies_for WITHOUT constructing the feature; per-class overrides on Average/Sum/Norm/Hillshade mirror their own derivation (DSN-05)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_feature_registry.py#test_dependencies_for_does_not_construct_the_feature"
        status: pass
      - kind: unit
        ref: "tests/test_feature_registry.py#test_match_derives_deps_via_dependencies_for_without_construction"
        status: pass
      - kind: unit
        ref: "tests/test_feature_registry.py#test_dependencies_for_average_splits_its_own_group (+ sum/norm/base variants)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Feature default-fallback preserved — unknown feature name resolves to the default pseudo-spec, never a raise (correction to the FINDINGS framing)"
    requirement: "BUG-05"
    verification:
      - kind: unit
        ref: "tests/test_feature_registry.py#test_unknown_feature_name_falls_back_to_default_without_raising"
        status: pass
    human_judgment: false
  - id: D4
    description: "DSN-11: _default_cls typed type[BaseFeatureStrategy] | None, confirmed optional by the pyright gate"
    requirement: "BUG-05"
    verification:
      - kind: other
        ref: "uv run --frozen pyright src/pc2img/features/registry.py (0 errors, 0 warnings)"
        status: pass
    human_judgment: false
  - id: D5
    description: "TEST-04: feature-name DSL / registry sensors (pure, no PCD) added"
    requirement: "TEST-04"
    verification:
      - kind: unit
        ref: "tests/test_feature_registry.py (10 passed)"
        status: pass
    human_judgment: false

# Metrics
duration: 11min
completed: 2026-07-11
status: complete
---

# Phase 05 Plan 07: Registry Unification + dependencies_for Summary

**Unified StrategyRegistry/FeatureRegistry onto a single dual-inheritance `RegistryLookupError(KeyError, RuntimeError)` and replaced match()'s side-effectful double class construction with an overridable `dependencies_for` classmethod, plus the DSN-11 `_default_cls` typing fix — all backward-compatible (zero caller edits).**

## Performance

- **Duration:** 11 min
- **Started:** 2026-07-11T05:00:18Z
- **Completed:** 2026-07-11T05:11:00Z
- **Tasks:** 2
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments
- Introduced `RegistryLookupError(KeyError, RuntimeError)` (new `src/pc2img/errors.py`) and routed every miss/duplicate raise in both registries through it. The dual inheritance means all pre-existing `except KeyError` (`_StrategyClass._validate`, `get_strategy`) and `except RuntimeError` handlers still catch it — the full suite (103 passed / 1 xfailed) confirms zero callers broke.
- Added an overridable `dependencies_for(params)` classmethod to both feature ABCs; `FeatureRegistry.match()` now reads dependencies from the parsed regex groupdict instead of constructing the feature class (eliminates the double `__init__` — DSN-05 / T-05-07a).
- Per-class overrides on `AverageFeature`/`SumFeature`/`NormFeature` (each splits its own `*_features` group) and `HillshadeFeature` (optional `base_feature` defaults to `range`), so `match()` and construction agree for every family — not one generic name-branching base (review concern #4).
- Preserved the feature default-fallback (unknown name → `ScalarFieldFeature` pseudo-spec, no raise), corrected from the FINDINGS framing.
- DSN-11: `_default_cls: type[BaseFeatureStrategy] | None`; `FeatureSpec` attributes annotated; `pyright src/pc2img/features/registry.py` now reports 0 errors.

## Task Commits

1. **Task 1: Author failing registry-unification + dependencies_for tests (TDD RED)** - `96b88d1` (test)
2. **Task 2: Introduce RegistryLookupError, unify miss sites, add dependencies_for, fix DSN-11** - `eb62a60` (refactor)

**Plan metadata:** _(final docs commit below)_

## Files Created/Modified
- `src/pc2img/errors.py` (created) - `RegistryLookupError(KeyError, RuntimeError)` shared miss type
- `tests/test_feature_registry.py` (created) - 10 pure DSL/registry sensors
- `src/pc2img/strategies/registry.py` - miss/duplicate raises → `RegistryLookupError`
- `src/pc2img/features/registry.py` - unified raises; `match()` via `dependencies_for`; DSN-11 typing; `FeatureSpec` annotations
- `src/pc2img/features/core.py` - overridable `dependencies_for` on both feature ABCs
- `src/pc2img/features/derivative_features.py` - `dependencies_for` overrides (Average/Sum/Norm/Hillshade)

## Decisions Made
- Placed `RegistryLookupError` in a new leaf module `src/pc2img/errors.py` so both `strategies/` and `features/` import it with no import cycle.
- Kept `register()` control flow byte-identical; used a single `cast("type[BaseFeatureStrategy]", c)` on the default-assignment (a default is by construction a per-point base feature) to satisfy the DSN-11 pyright gate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `HillshadeFeature` needed its own `dependencies_for` override**
- **Found during:** Task 2
- **Issue:** The plan explicitly lists only Average/Sum/Norm as `dependencies_for` overrides and says the base returns `[params["base_feature"]]`. But `HillshadeFeature`'s `base_feature` regex group is OPTIONAL and its `__init__` defaults `None → "range"`. Bare `hillshade` (used in `scripts/01`,`02`,`03`,`v2.0/01`) would have resolved to `[None]` under the base impl, regressing behavior and violating the must-have "match() and construction agree".
- **Fix:** Added a `HillshadeFeature.dependencies_for` override mirroring its `__init__` (None → "range"). Also hardened the base impl to return `[]` when there is no `base_feature` group (base features like `RangeFeature`/`ScalarFieldFeature` carry no such group), matching their `dependencies = []`.
- **Files modified:** src/pc2img/features/derivative_features.py, src/pc2img/features/core.py
- **Verification:** full suite 103 passed / 1 xfailed; `test_dependencies_for_base_feature_single_dep`
- **Committed in:** eb62a60

**2. [Rule 3 - Blocking] `FeatureSpec` typing + ruff-format of the new test file blocked the gates**
- **Found during:** Task 2
- **Issue:** (a) The DSN-11 pyright gate on `features/registry.py` was muddied by pre-existing `FeatureSpec.cls`/`_default_cls` inference errors (`self.cls = None` untyped → inferred `None`). (b) `ruff format --check` (via `test_hygiene.py`) flagged the newly-authored `tests/test_feature_registry.py`.
- **Fix:** Annotated `FeatureSpec` (`name`, `params`, `dependencies`, `cls`) and reworked its `base_feature` derivation to a None-safe `.get()`; ran `ruff format` on the test file. Pyright on the file is now 0 errors.
- **Files modified:** src/pc2img/features/registry.py, tests/test_feature_registry.py
- **Verification:** `pyright src/pc2img/features/registry.py` → 0 errors; `pytest tests/test_hygiene.py` → 4 passed
- **Committed in:** eb62a60

---

**Total deviations:** 2 auto-fixed (1 missing-critical, 1 blocking)
**Impact on plan:** Both necessary — the Hillshade override upholds the plan's own "match() and construction agree" must-have (a genuine gap in the plan's enumeration), and the typing/format fixes are what let the DSN-11 pyright gate and the hygiene gate pass. No scope creep beyond the four plan-listed files + the shared `errors.py`.

## Backward-Compatibility Note (BC-01 / D-17)
The registry **miss-exception type changed**: registry misses/duplicates now raise `RegistryLookupError` instead of a bare `KeyError` (strategies) or `RuntimeError` (features). Because `RegistryLookupError` subclasses BOTH, all observable catch behavior is preserved (grep-confirmed: no `pytest.raises(KeyError|RuntimeError)` on registry paths in tests/, and every in-repo handler catches a superclass). Only code matching on the EXACT class would notice — no such call site exists. Record for the Phase-6 D-17 running note.

## Issues Encountered
None beyond the two auto-fixed items above.

## Threat Flags
None — no new security surface; the plan's `mitigate` items (T-05-07a double-construction, T-05-07b divergent contracts) are addressed by `dependencies_for` and the unified error respectively.

## Known Stubs
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Registries unified; downstream plans (05-10/11/12) and Phase-6 BC-01/D-17 consumers can rely on `RegistryLookupError` and `dependencies_for`.
- No blockers.

## Self-Check: PASSED

- FOUND: src/pc2img/errors.py
- FOUND: tests/test_feature_registry.py
- FOUND: .planning/phases/05-bug-fixes-module-test-coverage/05-07-SUMMARY.md
- FOUND commit: 96b88d1 (Task 1)
- FOUND commit: eb62a60 (Task 2)

---
*Phase: 05-bug-fixes-module-test-coverage*
*Completed: 2026-07-11*
