---
phase: 4
reviewers: [codex]
reviewed_at: 2026-07-10T14:38:45Z
plans_reviewed: [04-01-PLAN.md, 04-02-PLAN.md, 04-03-PLAN.md, 04-04-PLAN.md, 04-05-PLAN.md, 04-06-PLAN.md, 04-07-PLAN.md]
---

# Cross-AI Plan Review — Phase 4

## Codex Review

## Summary

The phase structure is mostly sound: it separates mechanical hygiene fixes from behavioral bug fixes, stabilizes formatting before recording findings, and gives Phase 5 a canonical `04-FINDINGS.md` feeder. The main risks are execution-order/test-gating mistakes in early plans, one concrete source-level bug in the proposed `_TransformArray` fix, and overreliance on planning-doc claims that do not match the current tests.

## Strengths

- The plans correctly identify live source defects: duplicate `joblib` in [pyproject.toml](/scratch/31_pc2img/pyproject.toml:21) and [pyproject.toml](/scratch/31_pc2img/pyproject.toml:24), placeholder keywords at [pyproject.toml](/scratch/31_pc2img/pyproject.toml:9), broken `make_generator` at [registry.py](/scratch/31_pc2img/src/pc2img/registry.py:16), duplicate `convert_to_image` at [util.py](/scratch/31_pc2img/src/pc2img/util.py:58) and [util.py](/scratch/31_pc2img/src/pc2img/util.py:231).
- The fix/log boundary is appropriate. Behavioral bugs like `raise NotImplemented` in [disk_backed_image_data.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py:74), `extend_cache_paths` storing `None` via `dict.update()` in [tiled_generator.py](/scratch/31_pc2img/src/pc2img/tiled_generator.py:61), and orthographic projection’s 2-tuple return in [projection.py](/scratch/31_pc2img/src/pc2img/strategies/projection.py:181) are correctly left for Phase 5.
- The review scope covers the right math hot spots: Delaunay culling thresholds in [interpolation.py](/scratch/31_pc2img/src/pc2img/strategies/interpolation.py:235), `nanconv` input mutation/float16 in [util.py](/scratch/31_pc2img/src/pc2img/util.py:37), and hardcoded gradient spacing in [derivative_features.py](/scratch/31_pc2img/src/pc2img/features/derivative_features.py:30).
- The RRIM opt-in barrel exclusion is correct. `rrim.py` registers features on explicit import at [rrim.py](/scratch/31_pc2img/src/pc2img/features/rrim.py:470), while the default barrel only imports base/derivative features at [features/__init__.py](/scratch/31_pc2img/src/pc2img/features/__init__.py:7).

## Concerns

- **HIGH: 04-01’s new hygiene test is likely red in Wave 0.** The plan says `tests/test_hygiene.py` should assert non-placeholder keywords and a `viz` extra, but those are not changed until 04-02. Current evidence: keywords are still `["one", "two"]` at [pyproject.toml](/scratch/31_pc2img/pyproject.toml:9), and optional dependencies only contain `cuda12`, `cuda11`, and `rrim` at [pyproject.toml](/scratch/31_pc2img/pyproject.toml:51). Only the ruff check is planned as xfail, so `.venv/bin/pytest tests/test_hygiene.py -q` would fail immediately unless metadata/viz checks are also xfailed or deferred.
- **HIGH: 04-03’s `_TransformArray` fix will break runtime annotations unless annotations are postponed or quoted.** `projection.py` currently has no `from __future__ import annotations` at [projection.py](/scratch/31_pc2img/src/pc2img/strategies/projection.py:1), and the annotation uses `_TransformArray` at [projection.py](/scratch/31_pc2img/src/pc2img/strategies/projection.py:192). Moving the import under `if TYPE_CHECKING:` alone makes `_TransformArray` undefined when the class body is evaluated.
- **MEDIUM: 04-04 may accidentally auto-fix ERA001 before the deliberate review pass.** 04-02 intends `extend-select = ["ERA001"]`; then 04-04 Task 1 runs `ruff check --fix src/`. That full-config fix can include commented-code fixes before Task 2’s “enumerate then delete deliberately” pass. The repo has many commented-out code blocks, e.g. [interpolation.py](/scratch/31_pc2img/src/pc2img/strategies/interpolation.py:122), [disk_backed_image_data.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py:60), and [tiled_generator.py](/scratch/31_pc2img/src/pc2img/tiled_generator.py:30).
- **MEDIUM: 04-05/04-06 rely on xfail anchors that do not exist in current tests.** Current xfails cover null lazy cache config at [test_point_cloud_image_generator.py](/scratch/31_pc2img/tests/test_point_cloud_image_generator.py:35) and `DiskBackedImageData` lifecycle cases at [test_disk_backed_image_data.py](/scratch/31_pc2img/tests/test_disk_backed_image_data.py:50). I found no current test xfail for BUG-01 orthographic, BUG-03 `TIGSettings.extend_cache_paths`, or BUG-04 `rrim.__doc__`, despite the plans saying to cross-reference those xfail reasons.
- **MEDIUM: docs will become stale after the black→ruff swap.** 04-01 removes black from dev dependencies, but `CONTRIBUTING.md` still says the dev group includes black at [CONTRIBUTING.md](/scratch/31_pc2img/CONTRIBUTING.md:32). 04-02 writes a CUDA note but does not explicitly update this tooling text.
- **LOW: CI references appear inconsistent with the tree.** `CONTRIBUTING.md` references `.github/workflows/ci.yml` at [CONTRIBUTING.md](/scratch/31_pc2img/CONTRIBUTING.md:74), but `rg --files` found no `.github` workflow files. This is outside Phase 4’s scope, but it weakens validation claims that mention the Phase-3 CI baseline.
- **LOW: 04-05/04-06 say “multi-agent workflow” but the executable artifact is just markdown.** The plan may be fine in the intended GSD harness, but it should specify how raw reviewer/refuter outputs are produced and retained, otherwise execution can degrade into a single-reader pass while still satisfying superficial `test -s` checks.

## Suggestions

- Change 04-01 so metadata/viz assertions are either `xfail(strict=False)` until 04-02 or moved into 04-02 verification. Keep Wave 0 green by testing only what Wave 0 actually changes.
- In 04-03, fix `_TransformArray` by adding `from __future__ import annotations` or quoting the annotation as `NDArray | "_TransformArray"` while importing it only under `TYPE_CHECKING`.
- In 04-04, run safe autofixes as `ruff check --fix --ignore ERA001 src/`, then run `ruff check --select ERA001 src/` for manual deletion.
- Update 04-05/04-06 to stop claiming BUG-01/03/04 are encoded in current xfail reasons, or add an explicit source-only cross-reference path for those known bugs.
- Add a 04-02 task to update `CONTRIBUTING.md` dev-tool wording from black to ruff.
- Strengthen 04-07’s schema lint beyond grep. Even a small script/check that verifies each entry has all eight D-06 fields would be more reliable than checking for the words “severity”, “pillar”, and “proving”.

## Risk Assessment

**Overall risk: MEDIUM.** The plan set is directionally strong and targets the right files, but two issues can directly break execution: 04-01’s premature metadata test and 04-03’s annotation runtime failure. The later review plans also need tighter evidence handling so the final `04-FINDINGS.md` is not built on stale planning claims.

---

## Consensus Summary

Only one external reviewer (Codex) was invoked for this phase, so there is no cross-reviewer
consensus to synthesize. The section below distills Codex's source-grounded findings into
the items most worth acting on before execution. Every finding was verified by Codex against
the live working tree (concrete `file:line` anchors given), not against the plan text alone.

### Agreed Strengths
- Phase structure cleanly separates mechanical hygiene (04-01..04-04) from behavioral bug
  capture (deferred to Phase 5), and stabilizes formatting before recording findings.
- Plans target genuine, verified source defects: duplicate `joblib` pin, placeholder
  `pyproject` keywords, broken `make_generator`, duplicate `convert_to_image`.
- The fix-vs-log boundary is correct — behavioral bugs (`raise NotImplemented`,
  `extend_cache_paths` storing `None`, orthographic 2-tuple return) are correctly left for
  Phase 5 rather than fixed here.
- Math-review scope hits the right hot spots (Delaunay culling thresholds, `nanconv`
  mutation/float16, hardcoded gradient spacing).
- RRIM opt-in barrel exclusion is correctly modeled.

### Agreed Concerns (highest priority first)
- **HIGH — 04-01 hygiene test is likely red in Wave 0.** It asserts non-placeholder keywords
  and a `viz` extra, but those aren't introduced until 04-02. Only the ruff check is planned
  as xfail, so metadata/viz assertions would fail immediately. → Gate them as `xfail` until
  04-02, or move them into 04-02 verification. Keep Wave 0 testing only what Wave 0 changes.
- **HIGH — 04-03 `_TransformArray` fix will break runtime annotations.** `projection.py` has no
  `from __future__ import annotations`, so moving the import under `if TYPE_CHECKING:` leaves
  `_TransformArray` undefined when the class body evaluates. → Add
  `from __future__ import annotations` (or quote the annotation) alongside the TYPE_CHECKING move.
- **MEDIUM — 04-04 may auto-fix ERA001 before the deliberate review pass.** `ruff check --fix`
  with `extend-select = ["ERA001"]` can delete commented-code blocks before 04-04's manual
  "enumerate then delete" pass. → Run `ruff check --fix --ignore ERA001 src/` first, then
  `ruff check --select ERA001 src/` for the deliberate deletion.
- **MEDIUM — 04-05/04-06 reference xfail anchors that don't exist yet.** No current test xfail
  encodes BUG-01 (orthographic), BUG-03 (`extend_cache_paths`), or BUG-04 (`rrim.__doc__`),
  despite the plans instructing reviewers to cross-reference those xfail reasons. → Either stop
  claiming those bugs are in current xfails, or add an explicit source-only cross-reference path.
- **MEDIUM — docs go stale after black→ruff swap.** `CONTRIBUTING.md:32` still lists black in
  the dev group. → Add a 04-02 task to update the tooling wording.

### Divergent Views
- None — single reviewer.

### Lower-severity / out-of-scope notes
- **LOW** — `CONTRIBUTING.md:74` references `.github/workflows/ci.yml`, but no `.github`
  workflow files exist in the tree (out of Phase 4 scope, but weakens Phase-3 CI baseline claims).
- **LOW** — 04-05/04-06 describe a "multi-agent workflow" whose only executable artifact is
  markdown; specify how raw reviewer/refuter outputs are produced and retained so a `test -s`
  check can't be satisfied by a degraded single-reader pass.
- **Suggestion** — Strengthen 04-07's schema check beyond `grep`: verify each finding entry
  carries all eight D-06 fields rather than just the words "severity"/"pillar"/"proving".

**Overall risk (Codex): MEDIUM** — directionally strong, targets the right files, but two
issues (04-01 premature metadata test, 04-03 annotation runtime failure) can directly break
execution and should be fixed before running the phase.
