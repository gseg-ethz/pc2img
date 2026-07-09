---
phase: 2
slug: dependency-adaptation-reproducible-environment
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-09
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (dev group) + runnable smoke script (`uv run`) |
| **Config file** | none — smoke script is a plain `uv run` target; pytest promotion is Phase 3 |
| **Quick run command** | `uv run python scripts/smoke_pipeline.py` |
| **Full suite command** | `uv run python scripts/smoke_pipeline.py` (single-cloud smoke is the phase's runtime proof) |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run the smoke script if the pipeline/packaging surface changed
- **After every plan wave:** Run `uv sync` + smoke script
- **Before `/gsd-verify-work`:** Clean `uv sync` in a throwaway env + smoke script must exit 0
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | DEP-03 | T-02-01 | owner-verified PyPI pins; loose numpy | config-audit | `python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); ..."` (deps+cuda asserts) | ✅ pyproject.toml | ⬜ pending |
| 2-01-02 | 01 | 1 | DEP-04 | T-02-02 | explicit nvidia index binds RAPIDS only | config-audit | `python -c "..."` (groups + `[[tool.uv.index]]` + `[tool.uv.sources]` asserts) | ✅ pyproject.toml | ⬜ pending |
| 2-02-01 | 02 | 2 | DEP-04 (SC4) | T-02-04, T-02-05 | hash-pinned lock; official index only | lock round-trip | `uv lock --check && uv run python -c "import pc2img"` | ❌ W0 (uv.lock) | ⬜ pending |
| 2-02-02 | 02 | 2 | DEP-03 (SC3) | T-02-06 | no local-path leak into resolution | clean-room install | clean-room `uv sync --frozen` + `import pc2img/pchandler/GSEGUtils` | ❌ W0 (uv.lock) | ⬜ pending |
| 2-02-03 | 02 | 2 | DEP-04 (SC4) | — | dev-workflow doc only | doc-audit | `grep uv\ sync/uv\ lock/uv\ run/smoke_pipeline CONTRIBUTING.md` | ❌ W0 (CONTRIBUTING.md) | ⬜ pending |
| 2-03-01 | 03 | 3 | DEP-01, DEP-02 (SC1/SC2) | T-02-07 | seeded synthetic input; no untrusted I/O | runtime smoke | `uv run python scripts/smoke_pipeline.py` (exit 0, `OK`) | ❌ W0 (scripts/smoke_pipeline.py) | ⬜ pending |
| 2-03-02 | 03 | 3 | DEP-01, DEP-02 | T-02-08 | reproducible grep evidence | negative-audit | `! grep -rEn 'FoVTree\|to_py4dgeo\|...' src/pc2img/` + doc exists | ❌ W0 (docs/pchandler-2x-break-audit.md) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Planner: fill this map from the plan tasks; anchor each row to a DEP-0x requirement and the SC1-SC4 observable proof in 02-RESEARCH.md §Validation Architecture.*

---

## Wave 0 Requirements

- [ ] `scripts/smoke_pipeline.py` — SC1 runtime proof (synthetic cloud → spherical → Delaunay → `range`), passes explicit `LazyDiskCacheConfig(cache_path=…)` per the RESEARCH blocker
- [ ] `uv.lock` — committed universal lockfile enabling reproducible `uv sync`

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GPU-extra resolution into the universal lock (nvidia index) | DEP-04 (D-06) | Requires `pypi.nvidia.com` reachability at lock time; GPU-path validation deferred to GPU-01 (v2) | Run `uv lock` and confirm cuda11/cuda12 extras resolve; if the nvidia index misbehaves offline, flag to the owner per D-06 discretion |
| Three named semantic breaks resolved (BC-PCH-007/008, Csv/Las) | DEP-01, DEP-02 | Zero call sites in `src/pc2img/` (per RESEARCH audit) — deliverable is a documented negative-audit attestation, not a runtime assertion | Grep-audit call sites; document attestation in the smoke/audit artifact |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-09 (plan-checker: 0 blockers; Nyquist 8a–8e pass)
