---
phase: 2
slug: dependency-adaptation-reproducible-environment
status: draft
nyquist_compliant: false
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
| 2-01-01 | 01 | 1 | DEP-03 | — / — | N/A | audit | `uv pip show pchandler GSEGUtils` | ❌ W0 | ⬜ pending |

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
