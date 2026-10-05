---
phase: 7
reviewers: [codex, antigravity]
reviewed_at: 2026-10-01T16:17:26Z
plans_reviewed: [07-01-PLAN.md, 07-02-PLAN.md, 07-03-PLAN.md, 07-04-PLAN.md, 07-05-PLAN.md, 07-06-PLAN.md, 07-07-PLAN.md, 07-08-PLAN.md, 07-09-PLAN.md, 07-10-PLAN.md, 07-11-PLAN.md]
models:
  codex: "gpt-5.5 (reasoning=high)"
  antigravity: "unknown"
model_sources:
  codex: "banner"
  antigravity: "unknown"
---

# Cross-AI Plan Review — Phase 7

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts
<!-- gsd:plan-revision-conflicts:end -->

## Codex Review

## 07-01

**Summary** — Strong tracer plan. The proposed store migration matches the actual breakpoints: current `pyproject.toml` still admits GSEGUtils `<1.0` with old dependency pins, and `DiskBackedImageStore` really does call withdrawn private methods via `super()`.

**Strengths**
- Targets the real failure surface: old pins are present in [pyproject.toml](/scratch/31_pc2img/pyproject.toml:33), and the dangling `_get_npy_path` / `_get_meta_path` overrides are in [disk_backed_image_store.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py:118).
- Correctly replaces `del self[img_name]` in `add_image_to_store`; current code uses delete-on-overwrite at [disk_backed_image_store.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py:176).
- The D-11 table is unusually useful: it prevents the migration from becoming another open-ended hardening loop.
- The planned annotation change for `image_data` is justified; it currently claims `dict[...]` in [disk_backed_image_store.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py:241).

**Concerns**
- **LOW:** The plan relies on `get_npy_path(self.cache_dir, img_name)` as an intentional pre-check. That is locked by D-22 and reasonable, but it should be called out in the eventual public behavior text because it preserves double-fault precedence.
- **LOW:** The deferred bare-`assert` issue in [disk_backed_image_data.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py:27) is correctly triaged, but it remains a known optimized-Python gap.

**Suggestions**
- Keep the provenance check as an actual `uv run --frozen python` command in the summary, not just a described result.
- In the final docstring, avoid claiming full adversarial safety; the current docstring already overstates containment at [disk_backed_image_store.py](/scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py:24).

**Risk Assessment** — **MEDIUM.** Core behavior and published metadata change, but the plan is well-scoped and maps cleanly to the existing breakpoints.

## 07-02

**Summary** — Good follow-on test-hardening plan. It appears necessary because the existing image-store tests are still wired to private path builders and old delete semantics.

**Strengths**
- Rewrites tests that currently call removed helpers, e.g. [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:111), [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:130), and [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:450).
- Expands escape coverage beyond the current limited corpus in [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:290).
- The embedded traversal fix is real: `_escape_layout` creates only `cache_dir`, not `cache/a`, in [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:275).
- The tempfile hygiene item is grounded; current tests monkeypatch `tempfile.tempdir` locally in [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:591).

**Concerns**
- **MEDIUM:** Whole-tree snapshot tests can become noisy if unrelated temp files are created under the same root. The plan should make sure every subprocess/cache write stays under the test’s own `tmp_path`.
- **LOW:** The plan should explicitly verify the old “nesting allowed” expectation is removed; current symlink test still asserts `sub/nested` via `_get_npy_path` in [test_image_store.py](/scratch/31_pc2img/tests/test_image_store.py:552).

**Suggestions**
- Put the tree snapshot helper in `tests/test_image_store.py`, not a shared conftest, unless another module needs it.
- Add a narrow test for containment-before-shape precedence because D-22 depends on that line staying in `add_image_to_store`.

**Risk Assessment** — **MEDIUM.** Mostly tests, but they define the migration’s behavioral contract.

## 07-03

**Summary** — Sensible treatment of the tiled re-generation race under D-20: document, xfail, and file upstream/tracking issues rather than squeezing in a dispatch refactor.

**Strengths**
- The race mechanism is plausible in current code: `generate()` dispatches a bound method through joblib at [tiled_generator.py](/scratch/31_pc2img/src/pc2img/tiled_generator.py:134), and `_process_tile` reuses `self.image_generators` at [tiled_generator.py](/scratch/31_pc2img/src/pc2img/tiled_generator.py:164).
- Existing tiled tests explicitly avoid real joblib/loky process parallelism in [test_tiled_generator.py](/scratch/31_pc2img/tests/test_tiled_generator.py:17), so adding a regression marker fills a genuine blind spot.
- The plan’s refusal to “fix” upstream-owned behavior is consistent with D-11.

**Concerns**
- **MEDIUM:** The known-limitation wording should not narrow the failure to only `BrokenProcessPool` if the xfail also observes lower-level `OSError` / worker termination. The migration record and public footer must match the measured exception family.
- **LOW:** GitHub issue filing introduces an external dependency; the plan should specify labels/body fallback if labels do not exist or issue creation is denied.

**Suggestions**
- In the xfail reason, include both issue URLs and a concise mechanical trigger: reused generator, at least two tiles, `n_jobs >= 2`, GSEGUtils 0.6.0.
- Keep the xfail strict enough to fail if the bug disappears unexpectedly, but broad enough to avoid false failures from platform-specific worker errors.

**Risk Assessment** — **MEDIUM.** Accepting a supported-flow limitation is risky, but owner-approved and bounded.

## 07-04

**Summary** — Good security/release-hardening plan, but one verification detail for RTD shallow-clone simulation is likely flawed.

**Strengths**
- The publish gate gap is real: current patterns only catch PyPI action and twine upload in [check_publish_gate.py](/scratch/31_pc2img/.github/scripts/check_publish_gate.py:42), and `check_job` scans workflow job steps only at [check_publish_gate.py](/scratch/31_pc2img/.github/scripts/check_publish_gate.py:66).
- The preflight gap is real: current `matchable_job_names` collects jobs from all workflows, regardless of PR trigger, in [preflight_ruleset_apply.py](/scratch/31_pc2img/.github/scripts/preflight_ruleset_apply.py:145).
- RTD hardening is well targeted; current config uses `git fetch --unshallow || true` and non-forced tag fetch in [.readthedocs.yaml](/scratch/31_pc2img/.readthedocs.yaml:19).

**Concerns**
- **MEDIUM:** The RTD simulation plan uses `git clone --depth 50 "$S/origin.git"` in [07-04-PLAN.md](/scratch/31_pc2img/.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-04-PLAN.md:201). For local path clones, Git may ignore `--depth`; the “shallow” branch of the simulation can pass without testing a shallow repository.
- **MEDIUM:** Composite action scanning should consider nested local composite action references, not only direct workflow steps using a publishing composite.
- **LOW:** `uv publish` detection should avoid matching harmless prose in comments only if the parser currently treats `run:` script text as executable shell. The plan appears to scan steps, but tests should pin that.

**Suggestions**
- Use `git clone --depth 50 "file://$S/origin.git"` or `--no-local` in the RTD simulation.
- Add one test for composite action nesting or explicitly document single-level support if recursive scanning is intentionally out of scope.

**Risk Assessment** — **MEDIUM.** The target fixes are important and well chosen; the simulation weakness should be fixed before trusting the RTD proof.

## 07-05

**Summary** — Low-risk polish plan. It updates tests/docs around the ruleset comparator without changing comparator behavior.

**Strengths**
- Fixtures really are stale: `dismissal_restriction` is `{}` and `integration_id` is always present in [test_ruleset_lib.py](/scratch/31_pc2img/.github/scripts/test_ruleset_lib.py:117) and [test_ruleset_lib.py](/scratch/31_pc2img/.github/scripts/test_ruleset_lib.py:128).
- The read-filled test currently covers only one key path in [test_ruleset_lib.py](/scratch/31_pc2img/.github/scripts/test_ruleset_lib.py:281).
- The docstring change is justified: current rule text says live returns integer `15368` in [ruleset_lib.py](/scratch/31_pc2img/.github/scripts/ruleset_lib.py:262).
- RULESETS.md currently lacks the five ungoverned/read-filled fields in its maintainer section, which starts at [RULESETS.md](/scratch/31_pc2img/RULESETS.md:21).

**Concerns**
- **LOW:** The AST comparison must compare against the pre-edit version. The plan notes this, but it is easy to get wrong after committing.
- **LOW:** “Exactly one UI-created case” is good discipline, but ensure the test name makes that intent obvious.

**Suggestions**
- Add ids to the parametrized read-filled test cases for readable failures.
- Record the AST comparison command output in the summary exactly, since that is the proof that `ruleset_lib.py` executable behavior did not move.

**Risk Assessment** — **LOW.** Test/docs only, with appropriate verification.

## 07-06

**Summary** — Strong migration-record finalization plan. It correctly identifies the stale entries and ties new runtime facts to verifier checks.

**Strengths**
- Stale record claims are present: old pins in [MIGRATION-v0.11.md](/scratch/31_pc2img/.planning/MIGRATION-v0.11.md:53), old GSEGUtils floor in [MIGRATION-v0.11.md](/scratch/31_pc2img/.planning/MIGRATION-v0.11.md:63), and “nesting still allowed” in [MIGRATION-v0.11.md](/scratch/31_pc2img/.planning/MIGRATION-v0.11.md:68).
- The verifier currently has only 25 entries starting at [MIGRATION-v0.11.md](/scratch/31_pc2img/.planning/MIGRATION-v0.11.md:171), so expanding to 30 is mechanically checkable.
- Tightening `_tier2_bc_p2i_017` is appropriate; it currently only requires `ValueError` in [MIGRATION-v0.11.md](/scratch/31_pc2img/.planning/MIGRATION-v0.11.md:528).
- Cross-referencing upstream migration records instead of restating them keeps the pc2img record downstream-focused.

**Concerns**
- **MEDIUM:** BC-P2I-030 depends on issue URLs copied from `tests/test_tiled_generator.py`; that file currently has no such test or URLs. This is fine as a dependency on 07-03, but 07-06 must hard-stop if 07-03 did not land.
- **LOW:** The verifier’s `TIGSettings(... proj_cls="spherical", interp_cls="linear" ...)` should work because strategy class validators accept strings in [registry.py](/scratch/31_pc2img/src/pc2img/strategies/registry.py:123), but it is still a fragile import-heavy check for a markdown verifier.

**Suggestions**
- Keep Tier-2 checks small and isolated; avoid constructing point clouds in the verifier.
- Add a negative grep for “0.5.3” if the old pin wording should fully disappear outside historical notes.

**Risk Assessment** — **MEDIUM.** The record is release-critical, but the plan includes strong mechanical checks.

## 07-07

**Summary** — Good phase gate plan with the right emphasis on review and the unlocked-wheel check. One D-03 test-copy detail is fragile.

**Strengths**
- Re-runs the actual CI commands: CI uses coverage floor 55 in [.github/workflows/ci.yml](/scratch/31_pc2img/.github/workflows/ci.yml:260), script tests in [.github/workflows/ci.yml](/scratch/31_pc2img/.github/workflows/ci.yml:194), and docs build in [.github/workflows/ci.yml](/scratch/31_pc2img/.github/workflows/ci.yml:343).
- Requires independent review before promotion, which directly addresses the phase’s highest process risk.
- D-03 compares the shipped tree against the latest evidence SHA, preventing post-review/gap-round drift.

**Concerns**
- **MEDIUM:** The unlocked-wheel recipe copies only `tests/` and `pyproject.toml` in [07-07-PLAN.md](/scratch/31_pc2img/.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-07-PLAN.md:104), but `tests/test_rrim_features.py` references `src/pc2img/features/rrim.py` under the test root in [test_rrim_features.py](/scratch/31_pc2img/tests/test_rrim_features.py:16). It probably skips if `ruff` is unavailable, but the proof is fragile.
- **LOW:** The action lists docs and withdrawn-name grep, but the verify block samples only some gates. That is acceptable if recorded manually, but weaker as an automated guard.

**Suggestions**
- Add `-k "not test_rrim_module_docstring_clears_e402"` to the unlocked-wheel pytest command, or copy only the tests that validate installed behavior.
- Add an automated verify line for `! git grep -nE '_get_npy_path|_get_meta_path|_assert_within_cache_dir' -- src tests`.
- Record docs build output in the summary even if it is long; RTD changes are part of the release risk.

**Risk Assessment** — **MEDIUM-HIGH.** It gates the release path; conceptually strong, but D-03 should be made less brittle.

## 07-08

**Summary** — Solid integration and promotion-preparation plan. It treats promotion as a one-way public-history boundary and verifies the stripped tree carefully.

**Strengths**
- Matches the release procedure: `RELEASE.md` explicitly says promote from main with `.planning` / `.claude` stripped, then back-merge later in [RELEASE.md](/scratch/31_pc2img/RELEASE.md:28).
- The strip-list verification is important because `.planning/MIGRATION-v0.11.md` must not reach public main.
- The footer is self-contained, which matters because the migration record is stripped from main.
- The D03 tree-equivalence guard is a strong protection against shipping unmeasured fixes.

**Concerns**
- **LOW:** The vocabulary grep uses `xargs grep`; this is fine for current tracked paths, but would be brittle for filenames with whitespace.
- **LOW:** The public footer says the tiled race fails with `BrokenProcessPool`. If the committed xfail and BC entry use a broader exception family, the footer should match that wording.

**Suggestions**
- Generate the public footer from the final BC rows or copy-check it clause-by-clause in the summary.
- Use `git grep -lE ... -- $(git ls-files ...)` or `xargs -0` style if you want the vocabulary gate to be path-safe.

**Risk Assessment** — **MEDIUM.** Promotion is high impact, but the plan has good guardrails and a human gate.

## 07-09

**Summary** — Appropriate remote promotion/back-merge plan. It aligns with protected-branch constraints and correctly restores ancestry after main moves.

**Strengths**
- Main ruleset really requires Lint, Tests, and Docs, matching the plan’s check watch: [.github/rulesets/main.json](/scratch/31_pc2img/.github/rulesets/main.json:24).
- The release-please workflow is push-to-main driven in [.github/workflows/release-please.yml](/scratch/31_pc2img/.github/workflows/release-please.yml:25), so verifying PR #15 after promotion is necessary.
- The scheduled ancestry workflow exists and prints an OK line in [.github/workflows/scheduled-health.yml](/scratch/31_pc2img/.github/workflows/scheduled-health.yml:91).

**Concerns**
- **LOW:** The PR creation command uses shell process substitution in the plan. That is fine in zsh/bash, but less portable if the owner copies commands into a different shell.
- **LOW:** RTD polling by grepping a public page for `0.10.4.postN` can be brittle if theme text changes, though the post-install guard is the real protection.

**Suggestions**
- Use a temporary body file instead of `<(...)` for owner-copyable GitHub commands.
- Record both RTD badge status and the docs workflow context result; treat the rendered version string as supporting evidence, not the only proof.

**Risk Assessment** — **HIGH.** It changes public main and branch topology, but the plan is operationally careful.

## 07-10

**Summary** — Correctly treats publishing as the highest-risk gate. The environment and pending-publisher steps line up with the workflow’s OIDC identity.

**Strengths**
- Workflow uses environment `pypi` and PyPI URL at [.github/workflows/publish-pypi.yml](/scratch/31_pc2img/.github/workflows/publish-pypi.yml:87), matching the trusted-publisher tuple.
- Publish job has `id-token: write` and `attestations: write` in [.github/workflows/publish-pypi.yml](/scratch/31_pc2img/.github/workflows/publish-pypi.yml:94).
- Human gate requires PR #15 green, RTD green, migration verifier green, and D03 tree identity. That is the right set of preconditions.

**Concerns**
- **LOW:** `prevent_self_review: false` is pragmatic for a single-owner project, but it means the required reviewer gate is a deliberate human pause, not separation of duties.
- **LOW:** Pending trusted publisher cannot be read back through a simple API, so the plan necessarily relies on owner confirmation until the publish run proves it.

**Suggestions**
- Include the exact OIDC tuple in the summary after owner confirmation: project, owner, repo, workflow, environment.
- If possible, screenshot-free textual confirmation from PyPI is enough; no need to store secrets or screenshots.

**Risk Assessment** — **HIGH.** This is the irreversible publish decision, but the plan has the right human checkpoints.

## 07-11

**Summary** — Comprehensive release-evidence and cleanup plan. It verifies PyPI, attestations, fresh install, ancestry, migration target, and bookkeeping.

**Strengths**
- Attestation verification matches `RELEASE.md`, which already documents the PyPI integrity endpoint in [RELEASE.md](/scratch/31_pc2img/RELEASE.md:57).
- Fresh install check directly validates the phase’s core user story: plain `pip install pc2img==0.11.0`.
- Post-release back-merge is necessary because `RELEASE.md` explicitly says to back-merge again after the release PR merges in [RELEASE.md](/scratch/31_pc2img/RELEASE.md:36).
- Security follow-up annotation is scoped; it does not try to retire the accepted risks directly.

**Concerns**
- **MEDIUM:** The PyPI metadata grep in [07-11-PLAN.md](/scratch/31_pc2img/.planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-11-PLAN.md:97) expects exact `requires_dist` strings. Packaging metadata can normalize spaces/casing differently, so this could false-fail a valid release.
- **LOW:** The post-release back-merge allowlist should be checked against actual release-please output. Current plan assumes only `CHANGELOG.md` and `.release-please-manifest.json`; that is probably right, but should be verified live.
- **LOW:** The tag verifier runs `uv sync --frozen` in a tag worktree. If the tag is public main without `.planning`, extracting the verifier from develop-gsd is fine, but the summary should make that split explicit.

**Suggestions**
- Parse `requires_dist` with `packaging.requirements.Requirement` instead of exact grep strings.
- In the back-merge verification, print the actual changed file list and fail only if it includes unexpected source/test/workflow files.
- Record the published wheel filename and sdist filename alongside their attestation checks.

**Risk Assessment** — **MEDIUM-HIGH.** Mostly verification and cleanup, but it is the final chance to catch a bad public release. The plan is thorough; the metadata check should be made less brittle.


---

## Antigravity Review

# Implementation Plan Review: Phase 7 (GSEGUtils 0.6 Adoption & 0.11.0 Release)

This review evaluates the 11 execution plans of Phase 7 against the repository source at `/scratch/31_pc2img`. Every relative file path, code symbol, and line reference has been verified against the current codebase.

---

## 07-01

### 1. Summary
Plan 07-01 establishes the foundational dependency migration and core store rework as the phase tracer. It updates the dependency pins in [pyproject.toml](file:///scratch/31_pc2img/pyproject.toml#L33-L37) (`pchandler >= 2.1.1, ~= 2.1`, `GSEGUtils ~= 0.6.0`, `numpy >= 2.2, < 2.4`), updates the lockfile, validates in-process provenance to ensure a cached 0.5.x wheel is not loaded, deletes the three private path-builder/containment overrides and the `__delitem__` override from [`DiskBackedImageStore`](file:///scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py#L10), and rewrites [`tests/test_image_store.py`](file:///scratch/31_pc2img/tests/test_image_store.py) to adapt to the GSEGUtils 0.6 contract (`purge(key)`, read-only mapping, setter containment refusal).

### 2. Strengths
- **Rigorous in-process provenance check**: Task 2 verifies not only `importlib.metadata.version` and `GSEGUtils.__version__` but also inspects `hasattr(DiskBackedStore, '_get_npy_path') == False`, ensuring that the environment cannot silently use a cached 0.5.x build.
- **Systematic D-11/D-12 triage table**: Clearly disposes of historical and recent review findings (e.g. `review-r3-*`, `review-r4-*`), distinguishing between upstream-owned items, superseded code, and required migration tasks.
- **End-to-end smoke tracer**: Proves the migrated store via [`scripts/smoke_pipeline.py`](file:///scratch/31_pc2img/scripts/smoke_pipeline.py) and existing integration tests before downstream plans branch out.
- **Clean API boundary alignment**: Appropriately re-annotates `DiskBackedImageStore.image_data` from `dict[...]` to `Mapping[str, DiskBackedImageData | None]` in [disk_backed_image_store.py:241-244](file:///scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_store.py#L241-L244) to match the upstream `types.MappingProxyType` runtime contract.

### 3. Concerns
- **[MEDIUM] Dead source entries left in `[tool.uv.sources]`**: Upgrading to `pchandler >= 2.1.1` and `GSEGUtils ~= 0.6.0` drops transitive dependencies on the legacy RAPIDS stack (`cuml-cu12`, `cuproj-cu12`, `dask-cudf-cu12`), shrinking `uv.lock` from 193 to ~137 packages. However, [pyproject.toml:135-144](file:///scratch/31_pc2img/pyproject.toml#L135-L144) retains the explicit NVIDIA index source bindings for these dropped packages. While `uv lock` tolerates unreferenced sources, leaving stale source pins creates maintainer confusion regarding whether RAPIDS is still supported or needed.
- **[LOW] Pre-release version parsing brittleness**: In Task 2 verification, `p=tuple(int(x) for x in m.version('pchandler').split('.')[:3])` assumes standard dot-separated integers. If a pre-release like `2.1.1rc1` or `2.1.1b1` were ever resolved in an experimental resolve, `int('1rc1')` would raise a `ValueError`. Using `packaging.version.parse` would be more robust.
- **[LOW] Blocking human gate on pre-decided constants**: Task 1 is a `blocking-human` decision checkpoint asking the owner to confirm pin strings that were already locked in CONTEXT.md (`D-01`, `D-02`, `D-21`). This unnecessarily interrupts autonomous execution for a predetermined decision.

### 4. Suggestions
- Clean up or document the inert entries in `[tool.uv.sources]` ([pyproject.toml:135-144](file:///scratch/31_pc2img/pyproject.toml#L135-L144)) in Task 2 to reflect that only `cudf`, `cuspatial`, and `geopandas` are retained in pchandler 2.1.1.
- In Task 2 verification, replace manual string splitting of version strings with `packaging.version.Version(m.version('pchandler')) >= packaging.version.Version('2.1.1')`.

### 5. Risk Assessment
- **Overall Risk: MEDIUM**
- *Justification*: Moving foundational dependencies and deleting core store overrides introduces widespread potential blast radius across all caching layers. However, the risk is effectively mitigated by the strict in-process provenance gate and running the smoke pipeline immediately after migration.

---

## 07-02

### 1. Summary
Plan 07-02 expands test coverage around the migrated store and addresses test hygiene. It implements a 6-spelling × 6-route whole-tree snapshot test matrix in [`tests/test_image_store.py`](file:///scratch/31_pc2img/tests/test_image_store.py) asserting that no escaping key (`"../victim"`, `"/victim"`, `"a/../../victim"`, `""`, `"."`, `".."` across `add`, `setitem`, `add_then_offload`, `purge`, `getitem`, `add_data`) writes any file outside the cache directory. It pins the containment-before-shape check precedence (`StoreKeyError` before `AssertionError`), characterizes legal vs hostile key corpora, isolates temporary directory creation via an autouse fixture in [`tests/conftest.py`](file:///scratch/31_pc2img/tests/conftest.py), and adds docstrings describing store-key rules in [`src/pc2img/tiled_generator.py`](file:///scratch/31_pc2img/src/pc2img/tiled_generator.py#L33-L76).

### 2. Strengths
- **Exhaustive snapshot testing**: Snapshotting the full directory tree via `_tree(root)` before and after operations ensures that no route leaves stray files anywhere on the filesystem, eliminating silent file creation bugs.
- **Precedence re-pinning (`D-22`)**: Explicitly tests that calling `add_image_to_store("../victim", np.ones(4, dtype=np.float32))` raises `StoreKeyError` (a `ValueError`) rather than the `AssertionError` from [`_assert_image_shape`](file:///scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py#L16-L30), guaranteeing containment check precedence.
- **Deterministic test hygiene**: Eliminates system temp directory pollution (the 18 leaked `tmp*` directories) via an autouse fixture monkeypatching `tempfile.tempdir` to a pytest-managed `tmp_path / "_tmp"` directory.
- **AST verification for docstring changes**: Verifies that changes to [`src/pc2img/tiled_generator.py`](file:///scratch/31_pc2img/src/pc2img/tiled_generator.py) do not alter runtime AST structures by comparing AST dumps with blanked docstrings.

### 3. Concerns
- **[LOW] Broken symlink handling in `_tree` helper**: In Task 1, `_tree(root: Path)` maps every path under `root` to its bytes using `p.read_bytes()`. If a test creates a dangling or broken symlink (e.g. testing symlink escapes), `p.read_bytes()` or `p.is_file()` on Linux raises `FileNotFoundError` or `OSError`.
- **[LOW] Bare assert in `_assert_image_shape`**: While triage row `review-r4-da637a8dfe3c` is deferred by default in Task 2, [disk_backed_image_data.py:27](file:///scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py#L27) uses a bare `assert`, which disappears under Python optimized execution (`python -O`).

### 4. Suggestions
- In the `_tree` helper, wrap file reading in `try ... except OSError: return None` or record symlink targets explicitly with `os.readlink(p)` so dangling symlinks do not crash the snapshot assertion.
- Accept the owner flip for `review-r4-da637a8dfe3c` to replace `assert` with `if not (...): raise AssertionError(...)` in [disk_backed_image_data.py:27](file:///scratch/31_pc2img/src/pc2img/image_cache/disk_backed_image_data.py#L27).

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: The plan is primarily focused on unit test assertions, test fixtures, and docstrings with AST invariance validation.

---

## 07-03

### 1. Summary
Plan 07-03 addresses the loky tiled re-generation race condition discovered during research (`D-20`). The race occurs when `generate()` is called multiple times on the same [`TiledPointCloudImageGenerator`](file:///scratch/31_pc2img/src/pc2img/tiled_generator.py#L88) instance with `n_jobs >= 2`, because GSEGUtils 0.6.0 writes `.dat` files via a fixed `<key>.dat.tmp` filename and loky worker processes unpickle the entire generator state. The plan reproduces the race in an isolated scratch script, drafts two public GitHub issues (one upstream in `gseg-ethz/GSEGUtils` and one tracking issue in `gseg-ethz/pc2img`), gates on owner approval to file them, and adds an `xfail(strict=False)` regression test referencing the real issue URLs in [`tests/test_tiled_generator.py`](file:///scratch/31_pc2img/tests/test_tiled_generator.py).

### 2. Strengths
- **Measured exception typing**: Avoids guessing exception propagation by executing `_scrap/tiled_regenerate_repro.py 3` to capture the exact exception types (`BrokenProcessPool`, `TerminatedWorkerError`, `FileNotFoundError`) that bubble up through joblib.
- **Cross-repository traceability**: Establishes end-to-end traceability by embedding real GitHub issue URLs into the test `reason` and linking upstream to downstream tracking issues.
- **Appropriate boundary respect**: Complies with the core GSD guideline to avoid patching upstream architectural bugs locally when the root cause belongs in GSEGUtils' temporary memmap naming.

### 3. Concerns
- **[HIGH] Flaky CI failure from non-deterministic exception types**: Loky process pool failures are inherently timing-dependent. In Task 1, running 3 rounds might observe only `RuntimeError` (`BrokenProcessPool`), setting `XFAIL_RAISES = RuntimeError`. However, if on a multi-core CI runner a worker fails during file renaming before dying, joblib re-raises the underlying `FileNotFoundError` (an `OSError`). If `raises` in `pytest.mark.xfail` is restricted to `RuntimeError`, any run that surfaces `FileNotFoundError` will cause the test suite to FAIL instead of XFAIL.
- **[MEDIUM] External API dependency blocks automated execution**: Task 2 is a blocking human gate requiring `gh issue create` calls on public GitHub repositories (`gseg-ethz/GSEGUtils` and `gseg-ethz/pc2img`). If the execution environment lacks GitHub write credentials or network access, execution halts completely.

### 4. Suggestions
- Unconditionally define `raises=(RuntimeError, OSError)` for the xfail marker in [tests/test_tiled_generator.py](file:///scratch/31_pc2img/tests/test_tiled_generator.py) rather than restricting it solely to the types observed during the 3 test rounds, because both exception families are known manifestations of the same concurrency bug.
- Provide a mock issue URL fallback mechanism if running in an offline or sandboxed environment without GitHub CLI authentication.

### 5. Risk Assessment
- **Overall Risk: HIGH**
- *Justification*: Reliance on external GitHub API writes and the potential for non-deterministic multi-process exceptions to trigger test suite failures on CI make this plan high-risk.

---

## 07-04

### 1. Summary
Plan 07-04 implements release-path security hardening deferred from Phase 6 (`D-13`, `D-14`). In [`.github/scripts/check_publish_gate.py`](file:///scratch/31_pc2img/.github/scripts/check_publish_gate.py), it extends publish detection to `uv publish` and composite actions in `.github/actions/*` (closing `AR-07`). In [`.github/scripts/preflight_ruleset_apply.py`](file:///scratch/31_pc2img/.github/scripts/preflight_ruleset_apply.py), it restricts matchable job names to workflows triggered by pull-request events (closing `AR-08`). In [`.readthedocs.yaml`](file:///scratch/31_pc2img/.readthedocs.yaml), it hardens Git tag fetching with `--force`, ensures conditional unshallowing, and adds a `post_install` verification step, proven by an automated scratch-clone simulation script (`07-rtd-simulation.sh`).

### 2. Strengths
- **Comprehensive publish containment**: Detects publish steps embedded within local composite actions (`uses: ./.github/actions/...`), preventing security bypasses via indirection.
- **Preflight trigger event filtering**: Prevents repository deadlocks under strict rulesets by verifying that required status check contexts are produced by PR-triggered workflows, rather than scheduled or push-only jobs.
- **Empirical scratch-clone simulation**: Instead of relying on manual inspection of [`.readthedocs.yaml`](file:///scratch/31_pc2img/.readthedocs.yaml), `07-rtd-simulation.sh` creates real Git repositories, clones them with shallow and full depths, simulates tag moves, and executes the exact commands extracted from the configuration.

### 3. Concerns
- **[LOW] Minor phrasing inconsistency in Task 3**: The action description states: *"replace the two post_checkout commands with three: `- if [ \"$(git rev-parse --is-shallow-repository)\" = \"true\" ]; then git fetch --unshallow; fi` ... `- git fetch --tags --force`"*, but only lists two commands. The verification block and RTD schema correctly check for two commands.
- **[LOW] Path-filtered PR triggers**: In `preflight_ruleset_apply.py`, checking for `pull_request` in trigger events does not check if the workflow has path filters (e.g. `paths-ignore: ['docs/**']`). If a required check is defined in a path-filtered workflow, a documentation PR might still hang. (This is a standard GitHub limitation, but worth noting).

### 4. Suggestions
- Clarify the count in Task 3 description to explicitly state that the two existing `post_checkout` commands are replaced by two hardened commands (conditional unshallow and forced tag fetch).
- Ensure `07-rtd-simulation.sh` sets executable permissions (`chmod +x`) upon creation so that subsequent verify blocks can execute it cleanly without depending on `bash <path>`.

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: The changes harden security and CI scripts with isolated test coverage and standalone simulation verification.

---

## 07-05

### 1. Summary
Plan 07-05 addresses GitHub ruleset comparator polish items (`D-15`). It updates test fixtures in [`.github/scripts/test_ruleset_lib.py`](file:///scratch/31_pc2img/.github/scripts/test_ruleset_lib.py) and `test_check_ruleset_drift.py` with measured live GitHub API payload shapes (`dismissal_restriction` and `integration_id`), parametrizes the read-filled key test for `PULL_REQUEST_READ_FILLED_KEYS` and `STATUS_CHECKS_READ_FILLED_KEYS`, documents rule (c) and (d) contracts in [`.github/scripts/ruleset_lib.py`](file:///scratch/31_pc2img/.github/scripts/ruleset_lib.py), and adds maintainer documentation in [`RULESETS.md`](file:///scratch/31_pc2img/RULESETS.md#L21-L37) listing the five read-filled fields GitHub injects.

### 2. Strengths
- **Strict AST invariance validation**: Uses Python's `ast` module to strip docstrings and verify that `ruleset_lib.py` remains 100% AST-identical before and after editing, preventing accidental runtime regressions.
- **Transparent maintainer documentation**: Explicitly enumerates the five ungoverned read-filled fields in [RULESETS.md](file:///scratch/31_pc2img/RULESETS.md) (`allowed_merge_methods`, `dismissal_restriction`, `required_reviewers`, `require_extra_approval_for_unattributed_changes`, `do_not_enforce_on_create`), providing clarity for team operations.

### 3. Concerns
- **[LOW] Scratch directory prerequisite**: In Task 1 verification, `git show HEAD:.github/scripts/ruleset_lib.py > _scrap/ruleset_lib.head.py` assumes the `_scrap/` directory already exists. If `_scrap/` has not been created, this command will error with `No such file or directory`.

### 4. Suggestions
- Prefix the verification command with `mkdir -p _scrap` in Task 1 verify.

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: Non-executable changes to documentation, docstrings, and test fixtures verified with AST parsing.

---

## 07-06

### 1. Summary
Plan 07-06 finalizes [`.planning/MIGRATION-v0.11.md`](file:///scratch/31_pc2img/.planning/MIGRATION-v0.11.md) (`BC-01`). It amends existing entries `BC-P2I-002` (dependency pins), `BC-P2I-012` (GSEGUtils hook reference), and `BC-P2I-017` (correcting the stale claim that directory nesting was allowed). It appends new entries `BC-P2I-026` through `030` (`BC-P2I-026` dependency constraints, `027` `purge` delete verb, `028` key validation refusals, `029` read-only mapping, `030` tiled re-generation race limitation). It re-stamps `target_ref` to `"v0.11.0"`, updates summary tables, and extends the inline executable verifier with Tier-2 checks, asserting `[ok] verified 30 entries`.

### 2. Strengths
- **Executable documentation verification**: The embedded inline verifier executes Tier-2 checks verifying that exception types (`StoreKeyError`), read-only mappings (`MappingProxyType`), and delete semantics behave exactly as documented.
- **Correction of false historical claims**: Removes the outdated claim in `BC-P2I-017` ([MIGRATION-v0.11.md:68](file:///scratch/31_pc2img/.planning/MIGRATION-v0.11.md#L68)) that cache directory nesting was allowed, replacing it with the actual GSEGUtils 0.6 behavior where nested keys are refused.
- **Downstream consumer focus**: Incorporates grep insights from `/scratch/34_iof3d` to ensure breaking change descriptions provide clear, actionable instructions for dependent libraries.

### 3. Concerns
- **[LOW] Ordering coupling with Plan 07-03**: In Task 1, verification checks for real issue URLs: `U=$(grep -oE 'https://github\.com/gseg-ethz/GSEGUtils/issues/[0-9]+' tests/test_tiled_generator.py | head -1)`. If 07-03 failed to file real issues or used placeholder strings, 07-06 verification fails. This is mitigated by Wave 3 dependency ordering.

### 4. Suggestions
- Ensure that the inline verifier script extraction handles Windows line endings (`\r\n`) cleanly if executed across heterogeneous environments.

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: Thoroughly tested documentation finalization with an executable verification script.

---

## 07-07

### 1. Summary
Plan 07-07 serves as the phase gate (Wave 4). It runs all project verification gates (full test suite, branch coverage, hygiene checks, pre-commit, ruleset preflights, RTD simulation, migration verifier). It executes the `D-03` unlocked-wheel check: building a wheel from the branch tip, installing it into a fresh virtual environment from PyPI without `uv.lock`, and verifying that the full test suite passes. It concludes with a blocking human checkpoint to execute independent code reviews (`/gsd-code-review 7` and `/code-review origin/develop-gsd high`) and re-records the authoritative `D03_SHA` if any gap-closure round occurs.

### 2. Strengths
- **Clean-room unlocked resolution (`D-03`)**: Directly addresses the root vulnerability of Phase 7 (where `uv.lock` masked runtime incompatibilities between GSEGUtils 0.6 and pc2img) by building a standalone wheel and running tests against a fresh PyPI resolution.
- **Anti-tampering SHA pinning**: Records `D03_SHA` in `07-07-SUMMARY.md` and requires that downstream promotion plans (07-08 and 07-10) assert byte-for-byte tree identity between `main` and `D03_SHA`, preventing the release of unmeasured gap fixes.
- **Appropriate test scoping**: Excludes [`tests/test_hygiene.py`](file:///scratch/31_pc2img/tests/test_hygiene.py) from the unlocked wheel run, as that test specifically validates git-tracked repository structure rather than installed wheel behavior.

### 3. Concerns
- **[LOW] Test dependency completeness in unlocked venv**: Task 2 installs `pytest pyyaml` into the scratch venv before running the suite against the installed wheel. If any test transitively requires a dev dependency (e.g. `pytest-cov`), the command could fail. Verification of `tests/` confirmed no other packages are imported, but adding `--no-cov` explicitly ensures coverage plugins aren't expected.

### 4. Suggestions
- Add `--no-cov` to `_scrap/unl/bin/pytest tests/ --ignore=tests/test_hygiene.py -q` in Task 2 to prevent pytest from attempting to invoke coverage hooks in an environment where `pytest-cov` is not installed.

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: Pure verification gate with high rigor.

---

## 07-08

### 1. Summary
Plan 07-08 executes the merge of the phase branch into `develop-gsd` and prepares the promotion commit for `main`. In Task 1, it opens a pull request into `develop-gsd`, waits for CI, and merges using `--merge` to maintain a true two-parent merge commit. In Task 2, it constructs the single promotion commit `PROMOTION_SHA` in a scratch worktree based on `origin/main`, stripping `.planning/` and `.claude/`, verifying that the tree is identical to `develop-gsd` outside those paths, asserting zero planning vocabulary across all files, and formatting a conventional commit message with a `BREAKING CHANGE:` footer. Task 3 is a human decision checkpoint to approve opening the promotion PR.

### 2. Strengths
- **Isolated promotion synthesis**: Assembles the promotion commit in a clean worktree (`_scrap/pc2img-promotion`) detached from active branch working state, ensuring no untracked local artifacts leak into `main`.
- **Automated hygiene scanning**: Scans `git ls-files` with regex patterns for GSD IDs (`DEP-05`, `BC-01`, etc.) to guarantee that private planning artifacts do not contaminate public repository history.
- **Two-parent history preservation**: Enforces `--merge` when integrating into `develop-gsd`, preserving full development history while allowing a clean squashed promotion commit onto `main`.

### 3. Concerns
- **[LOW] File permission changes during tar extraction**: In Task 2, `git archive origin/develop-gsd | tar -x -C .` is used to populate the worktree. Depending on default umask, executable bits on script files (such as `.github/scripts/*.py`) might be altered. Using `git archive ... | tar --no-same-owner -x -C .` or checking `git diff --stat` ensures file modes match.

### 4. Suggestions
- Verify that file mode permissions (100755 for scripts, 100644 for source files) match `origin/develop-gsd` after the tar extraction.

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: Local Git operations and validation prior to remote branch push.

---

## 07-09

### 1. Summary
Plan 07-09 promotes the changes to public `main` and synchronizes `develop-gsd`. In Task 1, it pushes the promotion commit to a branch, opens a pull request into `main`, waits for checks, and squash-merges it with the reviewed `BREAKING CHANGE:` commit message. It then verifies that release-please PR #15 updates and tests that Read the Docs renders the new version on `latest`. In Task 2, it back-merges `main` into `develop-gsd` with a merge commit, dispatches the `scheduled-health.yml` workflow, and confirms that `main` is an ancestor of `develop-gsd`.

### 2. Strengths
- **Live production validation prior to release**: Validates the Read the Docs build on `main` immediately following promotion, ensuring documentation builds succeed in the production cloud environment before tagging.
- **Guaranteed ancestry synchronization**: Immediately restores ancestry via a merge commit and executes the remote `scheduled-health.yml` workflow to ensure no ancestry drift issues are triggered.
- **Conflict prevention precondition**: Asserts `git merge-tree --write-tree origin/develop-gsd origin/main` exits 0 before attempting the back-merge.

### 3. Concerns
- **[MEDIUM] Asynchronous RTD build latency**: In Task 1, `curl -s "https://readthedocs.org/projects/pc2img/badge/?version=latest" | grep -c passing` is executed immediately after merging the promotion PR. Read the Docs cloud builds typically take 1–3 minutes to queue, build, and deploy. Querying the badge immediately after merge risks inspecting the previous build or reading an `in_progress` state.
- **[LOW] Release-please run delay**: Merging the promotion PR triggers `release-please.yml` via GitHub webhook. Checking `gh run list --workflow release-please.yml` immediately can encounter race conditions where the workflow run has not yet been registered or is still queued.

### 4. Suggestions
- Add a polling loop with timeout (e.g. 5 minutes) when awaiting `release-please.yml` and the RTD badge status in Task 1.

### 5. Risk Assessment
- **Overall Risk: MEDIUM**
- *Justification*: Interacting with public branches and depending on asynchronous third-party cloud services (GitHub Actions, Read the Docs) introduces timing and network failure modes.

---

## 07-10

### 1. Summary
Plan 07-10 controls the release authorization gate. Task 1 creates the GitHub environment `pypi` with the owner as a required reviewer via the GitHub REST API (closing `AR-05`). Task 2 is a human action for the owner to register the PyPI pending trusted publisher (`pc2img / gseg-ethz / pc2img / publish-pypi.yml / pypi`). Task 3 is the final go/no-go release checkpoint: verifying PR #15 status, asserting byte-identical tree equality between `origin/main` and the latest `D03_SHA`, running the migration verifier, and merging release PR #15.

### 2. Strengths
- **Enforced human-in-the-loop publish gate**: Configures environment protection rules requiring human review before the production publish workflow can mint an OIDC token, fulfilling the core security promise of `AR-05`.
- **Cryptographic integrity gate**: Ensures that the code on `origin/main` is byte-identical to `D03_SHA` (excluding `.planning/` and `.claude/`), preventing any unverified commit from being tagged or published.
- **Clear separation of duties**: Separates environment setup (Claude) from pending publisher registration and release merge authorization (Owner).

### 3. Concerns
- **[LOW] GitHub API token permissions**: In Task 1, `gh api --method PUT repos/gseg-ethz/pc2img/environments/pypi` requires administrative permissions. If the active `gh` CLI token has repo write but not admin access, the API call will return 403 Forbidden. The plan includes an instruction fallback for the owner.

### 4. Suggestions
- No critical changes required; the verification commands and fallback mechanisms are properly structured.

### 5. Risk Assessment
- **Overall Risk: HIGH**
- *Justification*: Merging release PR #15 is an irreversible action that publishes `pc2img 0.11.0` to PyPI. Version numbers cannot be reused or replaced once uploaded.

---

## 07-11

### 1. Summary
Plan 07-11 conducts post-release verification, final back-merge, and bookkeeping. Task 1 monitors the PyPI publish workflow, verifies the package on PyPI, checks PEP 740 provenance attestations, validates the metadata `requires_dist`, and performs a clean install in a scratch environment. Task 2 executes the post-release back-merge of `main` into `develop-gsd` (bringing in release-please's CHANGELOG.md), checks ancestry with `scheduled-health.yml`, and verifies the migration record against a checkout of tag `v0.11.0`. Task 3 closes the three folded todos in [`.planning/todos/completed/`](file:///scratch/31_pc2img/.planning/todos/completed/) and annotates security follow-ups in [06-SECURITY.md](file:///scratch/31_pc2img/.planning/phases/06-publication-hardening-downstream-migration-record/06-SECURITY.md).

### 2. Strengths
- **Live PEP 740 provenance attestation checks**: Validates `https://pypi.org/integrity/pc2img/0.11.0/<file>/provenance` directly using `curl` and `jq`, confirming that cryptographically signed attestations are attached to both wheel and sdist.
- **Tag worktree migration verification**: Verifies that the migration record's verifier script executes cleanly (`[ok] verified 30 entries`) against a real checkout of the `v0.11.0` tag.
- **Thorough closure of paper trail**: Moves the three folded todos (`2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md`, `2026-09-25-phase-6-round-5-comment-and-test-hygiene.md`, `2026-09-30-phase-7-rtd-and-ruleset-hardening-round-4.md`) to `completed/` with commit shas and retargets deferred items.

### 3. Concerns
- **[MEDIUM] PyPI CDN cache propagation**: In Task 1, `curl -s https://pypi.org/pypi/pc2img/0.11.0/json` and `uv pip install 'pc2img==0.11.0'` are invoked immediately after the publish workflow reports success. PyPI's global CDN can take 30 to 90 seconds to propagate new index metadata. Without retry logic, immediate requests may encounter 404 responses.

### 4. Suggestions
- Implement a 60–120 second polling retry loop for the PyPI JSON endpoint and pip install commands in Task 1 to account for CDN replication delays.

### 5. Risk Assessment
- **Overall Risk: LOW**
- *Justification*: Post-release verification, documentation updating, and repository synchronization.

---

## Cross-Plan Findings & Risk Summary

1. **Phase Architecture & Completeness**: The 11 plans fully cover all requirements of Phase 7 (`DEP-05` and `BC-01`). The wave structure properly respects dependency constraints: Wave 1 establishes the 0.6.0 tracer, Wave 2 builds the escape route test matrix and handles the loky race, Wave 3 finalizes documentation, Wave 4 runs full quality gates, and Waves 5–8 execute the protected release sequence.
2. **Key Operational Vulnerability**: Non-deterministic exception types in Plan 07-03's loky tiled regeneration race could cause test failures on CI if `raises=` in `pytest.mark.xfail` is set too narrowly. Widening the marker to `raises=(RuntimeError, OSError)` resolves this risk.
3. **External Latency Management**: Plans 07-09 and 07-11 interface with external services (GitHub Actions webhooks, Read the Docs builds, and PyPI CDN). Adding bounded polling loops avoids intermittent false negatives during execution.


---

## Consensus Summary

Both reviewers cited `file:line` evidence throughout, so both are weighted as grounded reviews. Neither found a blocker against the phase goal. Both rate the plan set as achieving DEP-05 and BC-01, with the release path (07-09 and 07-10) correctly treated as the highest-risk, human-gated steps. Three defect claims were **reproduced by the orchestrator by running code** (marked ✔ below). The rest are reviewer assertions that have not been reproduced.

### Agreed Strengths
- The tracer in 07-01 targets the real breakpoints: the old pins, and the dangling `super()._get_npy_path` / `_get_meta_path` overrides. The in-process provenance check keeps a cached 0.5.x wheel from being loaded by mistake.
- The D-11/D-12 triage table stops the migration from turning into another open-ended hardening loop.
- The D-03 unlocked-wheel check, plus the `D03_SHA` comparison of the shipped tree at 07-08 and 07-10, prevents shipping fixes that were never measured.
- The promotion is assembled in an isolated worktree, with stripped-path and planning-vocabulary checks, and the BREAKING CHANGE footer is self-contained.
- 07-10 matches the workflow's OIDC identity: `environment: pypi`, `id-token: write` and `attestations: write`.

### Agreed Concerns
1. **The 07-03 xfail `raises=` and the known-limitation wording may be too narrow** (Codex MEDIUM, Antigravity HIGH).
   - Loky failures are timing-dependent. A run on CI can surface the worker's `FileNotFoundError` (an `OSError`) instead of `BrokenProcessPool` (a `RuntimeError`).
   - If `raises=` is set only from what three local rounds observed, the test can hard-fail in CI instead of xfailing.
   - Codex adds that the wording in BC-P2I-030 and in the 07-08 public footer must match whatever exception family the marker uses.
   - Antigravity suggests `raises=(RuntimeError, OSError)` unconditionally. This directly opposes the revision-1 rule "never wider than measured" and needs an owner call.
2. **The deferred bare `assert` in `_assert_image_shape` (`review-r4-da637a8dfe3c`)** is noted by both. Codex accepts the deferral. Antigravity recommends taking the owner flip, a one-line `raise AssertionError`.
3. **Brittle release-path verification checks** (different instances, same theme).
   - Codex: the `requires_dist` exact-string grep in 07-11 should parse with `packaging.requirements.Requirement`, because PyPI may normalize the text.
   - Antigravity: 07-09 checks RTD and release-please immediately after the merge, and 07-11 checks PyPI immediately after publish. Both need bounded polling loops to allow for webhook, build and CDN latency.

### Single-Reviewer Concerns Worth Acting On
- ✔ **07-04 RTD simulation, shallow case (Codex MEDIUM).** The plan uses `git clone --depth 50 "$S/origin.git"`, which is a local-path clone, and git ignores `--depth` on those. Reproduced: `warning: --depth is ignored in local clones; use file:// instead`. With `file://` the clone is shallow (`true`). As planned, the shallow case would test a complete clone and pass vacuously. Fix: use `file://` or `--no-local`.
- ✔ **07-07 D-03 unlocked-wheel run (Codex MEDIUM).** `tests/test_rrim_features.py` resolves `_REPO_ROOT / "src/pc2img/features/rrim.py"`, and that path does not exist when only `tests/` and `pyproject.toml` are copied. Confirmed that the reference exists. Whether the test skips or fails has not been reproduced. Fix: deselect the source-reading test(s) or copy what they need. Antigravity separately suggests `--no-cov`, because pytest-cov is absent from the unlocked venv.
- ✔ **07-01 stale `[tool.uv.sources]` (Antigravity MEDIUM).** `pyproject.toml` still routes `cuproj-cu1x`, `cuml-cu1x` and `dask-cudf-cu1x` to the NVIDIA index after pchandler 2.1.1 dropped them, and the comment above them still describes the `GSEGUtils >= 0.5.3, < 1.0` pin. Confirmed present. This fits D-11 step 4 (a one-line cleanup with no new behaviour) or a note in BC-P2I-026.
- **07-02 `_tree` snapshot helper (Antigravity LOW).** `read_bytes()` on a dangling symlink raises. Record symlinks with `os.readlink`.
- **07-04 nested composite actions (Codex MEDIUM).** Either scan nested local composite actions recursively, or document single-level support.
- **07-06 dependency on 07-03 URLs (Codex MEDIUM).** 07-06 should stop hard if the 07-03 URLs are absent. The wave ordering already implies this.
- **07-05 `_scrap/` may not exist (Antigravity LOW).** Add `mkdir -p _scrap` before the `git show … > _scrap/…`.
- **07-01 version parse (Antigravity LOW).** Use `packaging.version` instead of `int()` on split parts.
- **07-08 vocabulary grep (Codex LOW).** `xargs grep` breaks on whitespace in paths. Use `git grep` or `-z`/`-0`.
- **07-09 `<(...)` process substitution (Codex LOW).** Use a body file in any command the owner may copy.

### Divergent Views
- **07-03 risk:** Antigravity rates it HIGH (exception non-determinism and the dependency on `gh`). Codex rates it MEDIUM. The `gh` dependency is already verified (admin on both repos), so the real disagreement is the scope of `raises=`.
- **07-04 and 07-07 risk:** Antigravity rates both LOW. Codex rates them MEDIUM and MEDIUM-HIGH because of the two reproduced verification flaws above. Since those flaws reproduced, Codex's ratings hold.
- **07-01 Task 1 pin-confirmation gate:** Antigravity calls it an unnecessary interruption for constants already locked in CONTEXT. It is a deliberate reversibility gate (REVERSIBILITY_GATES on, pins one-way on PyPI) and doubles as the package-legitimacy confirmation, so keep it unless the owner says otherwise.

---

## Owner Dispositions (2026-10-01, binding for `/gsd-plan-phase 7 --reviews`)

| # | Finding | Owner decision | Plan(s) |
|---|---------|----------------|---------|
| O-1 | xfail `raises=` breadth (Agreed Concern 1) | **Widen** to `raises=(RuntimeError, OSError)`. This supersedes revision-1's "never wider than measured" rule. Keep the 07-03 Task 1 measurement and record what it observes. The xfail `reason=`, BC-P2I-030 and the 07-08 public footer must name both exception families (`BrokenProcessPool`/`TerminatedWorkerError` ⊂ `RuntimeError`; worker `FileNotFoundError` ⊂ `OSError`). Do not widen beyond these two families. | 07-03, 07-06, 07-08 |
| O-2 | `review-r4-da637a8dfe3c` bare `assert` (Agreed Concern 2) | **Keep deferred** (D-11 step 4) as currently planned. | 07-01 table (unchanged) |
| O-3 | Stale `[tool.uv.sources]` RAPIDS entries and the 0.5.3 pin comment | **Clean up in 07-01.** Delete the `cuproj-cu1x`, `cuml-cu1x` and `dask-cudf-cu1x` entries that pchandler 2.1.1 no longer pulls, rewrite the comment to describe the current pins, and re-lock in the same task. Add a row to the triage table (D-11 step 4, a one-line change with no behaviour change). | 07-01 |
| O-4 | Reproduced defects: 07-04 shallow clone (`file://`), 07-07 D-03 test-copy and `rrim.py` source path (+ `--no-cov`) | **Fix** (reproduced, no owner choice involved). | 07-04, 07-07 |
| O-5 | Remaining LOW/MEDIUM items (polling loops, `packaging` parsing for `requires_dist` and versions, `_tree` symlinks, nested composite actions, `mkdir -p _scrap`, `git grep`/`-z`, body file instead of `<(...)`, 07-06 hard-stop on missing URLs) | **Planner's discretion.** Incorporate, or defer or reject each one in the Review Dispositions Ledger with a reason. No new hardening loops (D-11). | various |
| O-6 | 07-01 Task 1 pin-confirmation gate called unnecessary (Antigravity) | **Keep** the gate: it is a reversibility gate and also serves as the package-legitimacy confirmation. | 07-01 |
