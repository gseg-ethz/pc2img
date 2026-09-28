# Phase 6: Publication Hardening & Downstream Migration Record - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 makes pc2img **publishable and protected**, and **drafts** the downstream migration
record. Concretely:

1. **CI/CD per the GSEG git-strategy template.** Assemble `GIT-STRATEGY.md`'s kit into pc2img via
   Procedure B (public repo): the core tier (branch protection + CI shape) plus the `release-pypi`
   component.
2. **Publication readiness.** Real package metadata (README, `CITATION.cff`, URLs), a minimal Sphinx
   docs site hosted on Read the Docs, and a TestPyPI dry run of the OIDC + PEP 740 publish path.
3. **First filtered promotion of `develop-gsd` → `main`.** Apply both rulesets, do the ancestry
   graft, and prove the nightly ancestry assertion. release-please then opens the 0.11.0 release PR,
   which **stays unmerged**: merging it is the milestone ship, not part of this phase.
4. **Public-tree hygiene before that promotion.** Strip planning vocabulary from every shipped file
   and remove or relocate planning-flavoured and broken files.
5. **Migration record draft.** `MIGRATION-v0.11.md` covering Phases 1–6.

**Explicitly NOT in this phase:** the code rework (GSEGUtils 0.6 adoption, containment-override
deletion, test hygiene). That moves to a **new Phase 7** (D-24). Phase 7 also finalises the
migration record, and its merge of the release PR ships 0.11.0 to PyPI.

</domain>

<decisions>
## Implementation Decisions

### Release identity and versioning
- **D-01:** Stay on the **0.x** line. The first PyPI release is **0.11.0**. Owner rationale:
  pre-1.0 honestly signals API instability, it is consistent with GSEGUtils (0.x, same
  release-please config), and it continues the only line that has GitHub Releases (0.10.1–0.10.4).
  The 2.0.0 option was rejected. — **Reversibility:** one-way — once 0.11.0 is on PyPI the number
  can never be reused, and moving to 2.x later is a new major line.
- **D-02:** Retire the `v2.0.0a5` tag from the version namespace. **Rename** it to
  `archive/v2.0.0a5`: push the archive name to origin **first**, then delete `v2.0.0a5` locally and
  on origin. This repo has `fetch.pruneTags = true`, which once silently pruned a local-only archive
  tag. Why: `2.0.0a5` sorts above `0.11.0`. Left in place, `develop-gsd` builds keep reporting
  `2.0.0a5.postN` (the squash to `main` never carries `v0.11.0` back), pip treats 0.11.0 as a
  downgrade for anyone with a git-installed build, and a `~= 0.11` pin rejects those builds.
  `setuptools_scm`'s `--match 'v[0-9]*.[0-9]*.[0-9]*'` ignores `archive/*`. Verify after the rename
  that `git describe` on `develop-gsd` reports `v0.10.4-N-g…`. — **Reversibility:** costly —
  downstream refs to the old tag name break (iof3D's `@v2.0.0a1` pin already fails to resolve).
- **D-03:** Mechanism for reaching 0.11.0. The first promotion squash to `main` uses a `feat!:`
  subject, a `BREAKING CHANGE:` footer pointing at `MIGRATION-v0.11.md`, **and** a
  `Release-As: 0.11.0` footer as a backstop. Verified against release-please source
  (`src/versioning-strategies/default.ts`, `determineReleaseType`): with the repo's
  `bump-minor-pre-major: true` plus `bump-patch-for-minor-pre-major: true`, a breaking commit bumps
  0.x **minor**, a plain `feat` bumps only **patch** (it would give 0.10.5), and `Release-As`
  overrides everything. The breaking marker also makes release-please write a "⚠ BREAKING CHANGES"
  section into `CHANGELOG.md`.
- **D-04:** Close the stale release-please PR **#6** ("chore(main): release 0.10.5", June 2025) and
  its branch `release-please--branches--main`. The new release-please flow regenerates its own PR.
- **D-05:** Publish depth in Phase 6: a **TestPyPI dry run** exercising the full OIDC trusted-publisher
  and PEP 740 attestation path. The real PyPI publish of 0.11.0 happens when the release PR is merged
  at milestone ship (after Phase 7). The name `pc2img` is currently unclaimed on both PyPI and
  TestPyPI (both returned 404, 2026-09-28).
- **D-06:** Future-release note for the owner: while on 0.x, a non-breaking `feat` bumps only the
  **patch**. Reaching 0.12 with a feature-only release needs `Release-As`.

### CI/CD: adopt the GSEG git-strategy template in full
- **D-07:** Adopt `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md` plus its kit
  (`.planning/git-strategy/template/`) **in full via Procedure B** (public repo). This
  **SUPERSEDES** the 2026-07-27 decision ("adopt the PCHandler security floor now, defer the flow
  mechanics to SEED-001"; todo `2026-07-27-phase-6-adopt-pchandler-security-floor-defer-redundant-ci.md`).
  The deferral no longer holds because the redesign has landed as this template: release-please is
  triggered directly by a push to `main` (no `workflow_run` chain), there is no post-merge run
  duplicating the PR run, strict up-to-date checks apply on `main`, and the fast path lives on steps,
  never as `paths` filters. The template's FLOOR / DEFAULT / ASK markers bind: any deviation from a
  FLOOR or DEFAULT is an ASK to the owner, and every DEFAULT deviation must be recorded where the
  next reader meets it.
- **D-08:** Template interview answers. Each question is an ASK in the template; these were answered
  by the owner on 2026-09-28 and are recorded here so they are not asked again:

  | Q | Parameter | Answer |
  |---|---|---|
  | 1 | `<MAIN_BRANCH>` | `main` |
  | 2 | `<DEV_BRANCH>` | `develop-gsd` |
  | 3 | Is `main` a true release branch? | **Filtered projection** of `develop-gsd`: promotion is a squash with planning paths stripped (the template's projection variant), not a plain merge |
  | 4 | `<PLANNING_PATHS>` | `.planning/`, `.claude/` (the only tracked agent/planning paths on `develop-gsd`) |
  | 5 | `<CHECK_CONTEXTS>` | `Lint (pre-commit)`, `Tests (pytest)` on both branches; `Docs (sphinx -W)` on `main` only |
  | 6 | Merge methods on `develop-gsd` | merge, squash and rebase all enabled today; **merge-commit MUST stay enabled** (back-merge and graft are true merges) |
  | 7 | Rulesets today | **none** (API returns `[]`, no legacy protection). Names: `<MAIN_RULESET_NAME>` = `protect-main`, `<DEV_RULESET_NAME>` = `protect-develop-gsd` |
  | — | `<IMPORT_PACKAGE>` vs `<PACKAGE>` | both `pc2img` |
  | — | `<OWNER>` / `<REPO>` | `gseg-ethz` / `pc2img` |
  | — | `<PYTHON_VERSION>` | `3.12` |
  | — | `<RELEASE_PLEASE_ENABLED>` | `True` |

  Consequences that follow from the template, not separate choices: `required_linear_history` on
  `main` only; `strict_required_status_checks_policy: true` on `main` and `false` on `develop-gsd`
  (the kit's recorded deviation); `bypass_actors: []` on both; a one-time true-merge ancestry graft
  `main` → `develop-gsd` done on the `develop-gsd` side after the `git merge-tree --write-tree
  --name-only` precondition (clean, no planning path); one back-merge per release using **"Create a
  merge commit"**; and the nightly ancestry assertion, observed passing once before it is trusted.
  `develop-gsd` does not currently contain old `main` as an ancestor (it forked from `dev/v2`), so
  the graft IS needed.
- **D-09:** Optional components: take **`release-pypi` only**. Declined: `config-self-inspection`,
  `continuous-enforcement` and `gpu-self-hosted` (pc2img has no GPU tests; its CUDA extras only pass
  through to pchandler). **Cost of declining, stated as the template's FLOOR requires:** every FLOOR
  and DEFAULT property in the apply-time checklist is verified **once**, at apply time, and never
  again. Later drift (a contributor adding a path filter, a ruleset edited in the UI) goes undetected
  until it bites. Owner accepted this trade.
- **D-10:** Adaptation (recorded DEFAULT deviation): the setup composite action
  (`.github/actions/setup-python-deps/action.yml`) installs with **`uv sync --frozen`** against the
  committed `uv.lock`, **not** the kit's `pip install .[dev]`. Reason: pc2img's dev tooling is
  PEP 735 `[dependency-groups]`, not an extra, so `pip install .[dev]` would install **no** ruff,
  pytest or coverage. The template permits a repo to adapt its own copy of this composite. Record
  the deviation at the site and in the CI/CD record (D-15).
- **D-11:** Lint is the template's pre-commit-shaped single job, `Lint (pre-commit)`. pc2img writes
  its own `.pre-commit-config.yaml` (the kit ships none) with ruff check + ruff format plus the
  standard hygiene hooks (trailing whitespace, end-of-file, check-yaml, check-toml,
  check-added-large-files). **No mypy** (pc2img uses pyright). **No license-banner hook** (owner
  declined). Lint scope must cover the whole shipped tree (see D-20). Current state, measured
  2026-09-28: `ruff format --check src tests` is clean; `ruff check src tests` reports **12** hits
  (6× C901 in `derivative_features.py`/`util.py`, 2× NPY002 in tests, 2× ERA001 on the
  `# Breadth:` headers in `tests/test_util.py`, plus F401 and I001). These must be fixed or given
  per-line/threshold config before lint becomes a required check. Folds todo
  `2026-07-09-move-to-ruff-lint-ci.md`.
- **D-12:** Tests job follows the template: pyright **informational** (continue-on-error, report
  artifact; currently 199 errors across `src`/`scripts`/`tests`) and a **Codecov** upload. The
  seeded-RNG grep is NOT added (not in the template; ruff NPY002 covers most of it).
- **D-13:** Docs job `Docs (sphinx -W)` is a core template context, required on `main` only. Build
  a **minimal Sphinx site**: `docs/source/conf.py`, an index page, and autodoc API pages generated
  from the existing NumPy-style docstrings, built with `sphinx-build -W --keep-going`. This also
  fixes `release-please-config.json`'s `extra-files: ["docs/conf.py"]`, which points at a file that
  does not exist; the planner must reconcile that path with the chosen docs layout. Host on **Read
  the Docs**, mirroring PCHandler's `.readthedocs.yaml`. The RTD project import is an owner account
  action.
- **D-14:** Metadata. Replace the placeholder `README.rst` (currently just `##Hello`, and it is the
  PyPI long description) with real content: install, quickstart, feature overview, the RRIM notice,
  and the CUDA extras. Add `CITATION.cff` modelled on PCHandler's. Add Repository, Issues and
  Changelog entries to `[project.urls]`. Point `documentation` at the RTD site. **Authors unchanged**
  (owner did not select adding Jon Allemand).
- **D-15:** Write the CI/CD adoption record where the next reader meets it, at the repo root,
  modelled on PCHandler's `RULESETS.md` / `RELEASE.md`. It states the interview answers, the
  components taken and declined (with the cost of declining), the `uv` deviation, and the fact that
  the 2026-07-27 floor-only decision was superseded. **Why:** the template's DEFAULT-deviation rule,
  and the original todo's requirement that the Phase 6 record must not read as an oversight. It must
  contain no planning IDs (it ships to `main`).
- **D-16:** Keep the existing coverage gate `--cov-fail-under=55` in the template's Tests job as a
  recorded addition. The template has none; dropping it would weaken an existing gate.

### Promotion to main and sequencing
- **D-17:** The first filtered promotion `develop-gsd` → `main` happens **inside Phase 6**, carrying
  the already-reviewed Phase 1–5 code plus the Phase 6 CI/CD, docs and metadata. Order per
  Procedure B, where each step is FLOOR unless marked: interview answered (D-08) → assemble core,
  then `release-pypi` (root-to-root copy) → substitute tokens, then read the six in-place edit
  sites → verification command (1) plus the apply-time checklist **with recorded evidence** → land
  the workflows on the protected branch **before** applying any payload that requires their
  contexts ("merge first, require second") → apply the rulesets via the dispatch-only apply
  workflow, `main` first, then `develop-gsd`, reading each back to confirm `bypass_actors` is
  present and empty → ancestry graft (DEFAULT) → enable the nightly assertion and observe it pass
  once. — **Reversibility:** one-way — code pushed to public `main` is published history.
- **D-18:** Because the owner does not want planning artifacts on public `main`, **all** public-tree
  hygiene (D-20..D-23) and the planning-reference sweep must land on `develop-gsd` **before** the
  first promotion.
- **D-19:** After Phase 6, release-please's 0.11.0 PR stays open and unmerged. Phase 7's changes
  reach `main` via a second promotion, and the release PR updates itself. Merging it = milestone
  ship = the real PyPI publish.

### Public-tree hygiene (before first promotion)
- **D-20:** Extend the planning-vocabulary sweep (ID families BUG-/DSN-/M-NN/D-NN/BC-NN/QUAL-/TEST-/
  DEP-/phase refs/`.planning` paths) to the **whole shipped tree**: every tracked path except
  `.planning/` and `.claude/`. Known hits: `pyproject.toml` comments (`D-06`, `D-08`, `D-11`,
  `D-12`, `D-17`, `QUAL-01`, `TEST-01`, `BC-01`), `CONTRIBUTING.md`, and the `docs/` files. Include
  the round-5 leftovers from todo item `review-r4-4a993aa1a335` (`test_rrim_features.py:236-237`,
  `test_feature_registry.py:60-61`, `test_image_store.py:51,:439`,
  `disk_backed_image_store.py:34,:95`). The gate regex scopes to "all tracked paths minus the
  stripped ones", not a directory list, so new files are covered automatically.
- **D-21:** Move `docs/pchandler-2x-break-audit.md` (a Phase 2 artifact) into
  `.planning/phases/02-dependency-adaptation-reproducible-environment/`. Its public substance (zero
  pc2img call sites for the pchandler 2.x breaks) resurfaces as `dep-constraint` entries in
  `MIGRATION-v0.11.md`.
- **D-22:** **Delete** `scripts/01_tiled_image_generation_from_pointcloud.py`. It imports
  `pc2img.tiled_image_generation`, which does not exist (the module is now `tiled_generator.py`).
  The README quickstart takes over its role. `scripts/smoke_pipeline.py` stays.
- **D-23:** Keep `docs/ip/rrim-eth-signoff.md` **verbatim**. It is a signed ETH IP-clearance record;
  editing it would weaken what it attests. Exempt it from the D-20 gate with the reason stated at
  the exemption. `docs/ip/rrim-ip-findings.md` is referenced by `NOTICE`; sweep it only if that does
  not alter the attested findings (planner's judgement, flag it if unsure).

### Roadmap restructure
- **D-24:** The code rework moves to a **new Phase 7**, to be inserted before milestone completion
  via `/gsd-phase` (a roadmap edit, not done in this discussion). Phase 7 covers: the GSEGUtils 0.6
  adoption and containment-override deletion (todo
  `2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md` → retarget
  `resolves_phase: 7`, including spikes 001/004, pin bump, re-lock, the exception-type check **by
  running code**, and the re-pinned escape tests); the **test-hygiene half** of todo
  `2026-09-25-phase-6-round-5-comment-and-test-hygiene.md`; finalising `MIGRATION-v0.11.md`; and the
  second promotion. Owner rationale: CI/CD is infrastructure that can land directly, while the code
  rework needs its own plan/review/verify gates (global Review Discipline). It will also be the
  first change to go through the new protected flow. pchandler's `GSEGUtils ~= 0.5` pin already
  admits 0.6, so there is no cross-repo conflict.

### Migration record (BC-01)
- **D-25:** Format: PCHandler's **migration-spec** schema. Frontmatter: `type: migration-spec`,
  `spec_version`, `repo: pc2img`, `baseline_ref`, `target_ref`, `generated_at`,
  `bc_id_prefix: BC-P2I`, `milestone: v1.0`. The 7 categories (`surface-removed`,
  `signature-shape`, `semantic-change`, `error-behavior`, `on-disk-format`, `dep-constraint`,
  `additive-or-fixed`) plus the `internal` track, and the 4 severities (`must-edit`,
  `should-review`, `additive`, `informational`). IDs are `BC-P2I-NNN`, monotonic, zero-padded to 3
  digits. Sections: Summary; Public API stability statement; Breaking & behavior changes; Additive
  changes; Internal & sweep changes; Verifier (inline). Entries caused by GSEGUtils changes
  cross-reference PCHandler's existing `BC-GSEG-NNN` IDs rather than restating them. **Difference
  from PCHandler:** pc2img has no "no breaking import paths" invariant, so `must-edit` /
  `surface-removed` entries are expected (for example the `.pkl` → `.npy` cache format and the
  unified `RegistryLookupError`). They are classified, **not** escalated as stop-and-ask events.
- **D-26:** Baseline `dev/v2` tip **`91b4ab6`** (2025-11-06), the exact fork point of `develop-gsd`.
  Target: `develop-gsd` HEAD for the Phase 6 draft, re-stamped to `v0.11.0` in Phase 7. Rejected:
  `v2.0.0a5` (6 commits and about 1,100 src lines older, so it would mix in pre-milestone features)
  and `v0.10.4` (the old flat layout, which nobody consumes).
- **D-27:** Coverage is the **whole milestone, Phases 1–6** (Phase 7 appends its own entries).
  Sources: `05-BC-NOTES.md` (17 entries, the bulk); re-audit Phases 1–4 from their `*-CONTEXT.md`
  decisions and `*-VERIFICATION.md`, plus a public-surface diff `91b4ab6..HEAD` (Phase 2 dependency
  pins and extras including `viz`/`rrim`/cuda; Phase 4 removals); plus Phase 6's own entries: tag
  retirement / version line, the move to PyPI (downstream should drop git pins and depend on
  `pc2img ~= 0.11`), and the README/metadata.
- **D-28:** File: **`MIGRATION-v0.11.md` at the repo root** (it survives the `main` strip; named by
  package version, with milestone `v1.0` in frontmatter to avoid implying a pc2img 1.0). The
  `BREAKING CHANGE:` footer of the promotion squash links to it. Must contain no planning IDs in
  prose (origins reference phases/commits in a form that does not dangle, or live in frontmatter;
  planner decides, consistent with D-20's gate).
- **D-29:** Timing: **draft in Phase 6**, finalised in Phase 7 (append the GSEGUtils 0.6 entries,
  re-stamp the target to `v0.11.0`, re-run the inline verifier).

### Docs dependencies (decided at plan-phase, 2026-09-28)
- **D-31:** `doc` **stays a PEP 735 `[dependency-groups]` entry**, the same mechanism as `dev`
  (consistent with D-10 and Phase 2's "tooling never in wheel metadata"). It is **not** converted to
  a `[project.optional-dependencies]` extra, even though PCHandler and the kit use extras. CI's docs
  job (the kit's in-place `pip install .[doc]` edit site) installs with `uv sync --frozen --group doc`.
  `.readthedocs.yaml` replaces PCHandler's `extra_requirements: [doc]` with a `build.jobs` install
  step that installs the `doc` group (`pip install --group doc` needs pip >= 25.1, or a uv-based
  install). Its first real RTD build (at the RTD-import checkpoint) is what proves it. Record this as
  a deviation from the kit/PCHandler at the site and in the CI/CD record (D-15). Why: the research
  (Pitfalls 2/3) found both the kit's docs job and RTD's `extra_requirements` are extras-only; the
  owner chose to keep pc2img's two tooling groups on one mechanism rather than match PCHandler.
- **D-32:** Align the docs toolchain with PCHandler: `doc = ["sphinx ~= 8.2.3, <8.3",
  "sphinx_rtd_theme"]` (PCHandler's pin blocks the 8.3 autosummary regression, sphinx-doc/sphinx#14166)
  instead of `sphinx ~= 5.1` with the default theme. This means a re-lock (`uv lock`). The research's
  13 `-W` warnings were measured under 5.3.0, so re-measure them under 8.2.x before sizing the
  docstring fixes.

### Owner account actions — prompted during execution
- **D-30:** Every owner-only account action is a `checkpoint:human-action` task **in execution**,
  placed immediately before the first step that needs it, and never collected during planning
  (owner request 2026-09-28; nothing in planning depends on them, since App and secret names are
  already known). Each prompt states the exact values to enter (App name, repo, secret names,
  environment names, and for trusted publishing the owner/repo/workflow filename/environment
  tuple), and the step right after it verifies the result by running something, not by asking.
  Order in Phase 6:
  1. Add pc2img to the `codecov` and `gseg-ruleset-admin` Apps and set the protection-App secrets
     (`<APPLY_APP_ID_SECRET>` / `<APPLY_APP_KEY_SECRET>` names per the template), plus the
     `CODECOV_TOKEN`: before the first CI run of the assembled workflows and before the ruleset
     apply workflow is dispatched.
  2. Import the project on Read the Docs: once the docs build green on the branch.
  3. Register the TestPyPI trusted publisher and create the `testpypi` GitHub environment: right
     before the TestPyPI dry run.
  4. Add pc2img to the `gseg-release-please` App and set the release-App secrets (a different App
     from the protection one, template FLOOR): before release-please first runs on `main` at the
     first promotion.

  Deferred to Phase 7: register the PyPI trusted publisher and create the `pypi` environment,
  right before the release PR is merged.

### Claude's Discretion
- Exact ruff remediation for the 12 hits (fix vs. per-line `noqa` vs. a C901 threshold in config),
  provided `Lint (pre-commit)` is green on the whole shipped tree.
- README structure and depth within D-14; the Sphinx theme and page layout within D-13.
- Plan/wave decomposition and ordering, subject to D-17/D-18 (hygiene before promotion; workflows
  before rulesets).
- The inline verifier's implementation (an AST-walk + runtime `getattr` pattern like PCHandler's),
  provided it mechanically checks every `surface-removed` / `signature-shape` claim.

### Folded Todos
- **`2026-07-27-phase-6-adopt-pchandler-security-floor-defer-redundant-ci.md`**: folded and
  **superseded by D-07** (full template adoption instead of floor-only). Its "write the divergence
  down" deliverable becomes D-15.
- **`2026-07-09-move-to-ruff-lint-ci.md`**: folded as D-11 (ruff inside `Lint (pre-commit)`).
- **`2026-09-25-phase-6-round-5-comment-and-test-hygiene.md`**: **split** (owner decision).
  Planning-reference item `review-r4-4a993aa1a335` plus the `__delitem__` docstring-history fix
  `review-r4-16ca6d81fd0c` and the stale docstring pointer `review-r4-66d8cfa20681` (comment
  accuracy on shipped text) → Phase 6 (D-20). The ERA001 `# Breadth:` item
  `review-r4-ba69ab35c32e` → Phase 6 (needed for a green lint, D-11). Test hygiene
  (`review-r4-84a2b5dff14c` fold/differentiate the absent-key test, `review-r4-15a5c4928dc8` tmp
  leak fixture) → Phase 7.
- **`2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md`**: folded into scope
  but **retargeted to Phase 7** (D-24).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CI/CD template (governing spec)
- `~/gsd-workspaces/pchandler/.planning/GIT-STRATEGY.md`: the procedure. Read in full: *Bindingness*
  (FLOOR/DEFAULT/ASK), *The default flow*, *The interview*, *The kit*, *Parameters*, *Assembling a
  repository*, *Verifying an assembly* (the apply-time checklist needs recorded evidence),
  *Component — branch protection*, *Component — CI shape and reuse*, *Component — release path*,
  **Procedure B** (public repo), *When the project is GSD-managed*, *Known limits*.
- `~/gsd-workspaces/pchandler/.planning/git-strategy/template/`: the kit. `core/` plus
  `optional/release-pypi/` only (D-09). Copy per component, root-to-root; never `cp -r` the kit root.
- `/scratch/41_pchandler/.github/`, `/scratch/41_pchandler/RULESETS.md`,
  `/scratch/41_pchandler/RELEASE.md`, `/scratch/41_pchandler/.readthedocs.yaml`,
  `/scratch/41_pchandler/CITATION.cff`: a live reference instance (pre-template shape in places,
  e.g. its `workflow_run` trigger; **the template wins on any conflict**).
- `~/gsd-workspaces/pchandler/.planning/release-please-token.md`: how the `gseg-release-please` App
  was provisioned (a bot-opened release PR needs an App token, not the default token).
- `~/gsd-workspaces/pchandler/.planning/seeds/SEED-001-streamline-branch-protection-cicd-release-flow.md`:
  history only; explains why the 07-27 floor-only decision existed and why D-07 supersedes it.

### Migration record format
- `/scratch/41_pchandler/MIGRATION-v1.0.md`: format exemplar (frontmatter, tables, inline verifier).
- `~/gsd-workspaces/pchandler/.planning/milestones/v1.0-phases/07-breaking-changes-downstream-migration-doc/07-CONTEXT.md`
  and `07-RESEARCH.md`: the category/severity vocabulary (D-01..D-04 there) and the verifier strategy.
- `~/gsd-workspaces/pchandler/.planning/MIGRATION-v1.0.md`, `~/gsd-workspaces/pchandler/.planning/MIGRATION-v1.2.md`:
  workspace synthesis; `BC-GSEG-006/007` (GSEGUtils 0.6.0) to cross-reference.
- `.planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md`: 17 Phase-5 entries (primary input).
- `.planning/phases/01-branch-untangling-mainline-consolidation/01-CONTEXT.md`, `01-VERIFICATION.md`
- `.planning/phases/02-dependency-adaptation-reproducible-environment/02-CONTEXT.md`, `02-VERIFICATION.md`
- `.planning/phases/03-test-ci-foundation/03-CONTEXT.md`, `03-VERIFICATION.md`
- `.planning/phases/03.1-rrim-red-relief-image-ip-status-clarification/03.1-CONTEXT.md`, `03.1-VERIFICATION.md`
- `.planning/phases/04-code-quality-algorithmic-soundness-review/04-CONTEXT.md`, `04-VERIFICATION.md`, `04-FINDINGS.md`
- `docs/pchandler-2x-break-audit.md` (moving under D-21): source for Phase-2 `dep-constraint` entries.

### Versioning
- release-please `src/versioning-strategies/default.ts` (`determineReleaseType`): the verified
  pre-1.0 bump semantics behind D-03/D-06.
- `release-please-config.json`, `.release-please-manifest.json` (0.10.4), `pyproject.toml`
  `[tool.setuptools_scm]` (tag regex / describe `--match`).

### Todos in scope
- `.planning/todos/pending/2026-07-27-phase-6-adopt-pchandler-security-floor-defer-redundant-ci.md` (superseded, D-07)
- `.planning/todos/pending/2026-07-09-move-to-ruff-lint-ci.md` (D-11)
- `.planning/todos/pending/2026-09-25-phase-6-round-5-comment-and-test-hygiene.md` (split, D-20 / Phase 7)
- `.planning/todos/pending/2026-09-24-phase-6-adopt-gsegutils-0.6-delete-containment-override.md` (→ Phase 7)

### IP / legal (do not alter)
- `NOTICE`, `docs/ip/rrim-ip-findings.md`, `docs/ip/rrim-eth-signoff.md` (verbatim, D-23)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.github/workflows/ci.yml`: current single `tests` job (uv `sync --frozen`, `fetch-depth: 0` for
  setuptools_scm, `--cov-fail-under=55`, coverage artifact). Its uv/scm details carry into the
  template's Tests job and setup composite (D-10, D-16).
- `.github/workflows/release-please.yml`: old shape (push-to-main, default `GITHUB_TOKEN`, unpinned
  actions). **Replaced** by the kit's `release-pypi` version.
- `release-please-config.json`: already matches the kit's config (same pre-major flags and
  changelog sections) except `extra-files: ["docs/conf.py"]` (D-13).
- `pyproject.toml`: ruff config already present (`line-length = 120`, E/F/W/I/B/C90/UP/NPY +
  ERA001, per-file ignores); `[dependency-groups] dev/doc` (sphinx ~= 5.1; may need a bump for the
  template's `sphinx -W` build); `[project.urls]` currently homepage + documentation only.
- `scripts/smoke_pipeline.py`: stays; referenced by `CONTRIBUTING.md`.

### Established Patterns
- Least-privilege `permissions: contents: read` already on CI. The template additionally requires
  **every third-party action pinned to a full 40-char SHA** (FLOOR). The current `ci.yml` uses tag
  refs (`actions/checkout@v5`, `astral-sh/setup-uv@v8.3.2`) that must be SHA-pinned.
- Phase PRs into `develop-gsd` use merge commits (retained, D-08 Q6). Promotion to `main` is a
  filtered squash.
- Commit scopes are functional (`ci(...)`, `docs(...)`, `build(...)`), never planning IDs.

### Integration Points / Environment facts (verified 2026-09-28)
- GitHub repo `gseg-ethz/pc2img`: **public**, default branch `main`, no rulesets, no branch
  protection; merge/squash/rebase all enabled.
- Org GitHub Apps exist (`gseg-release-please`, `gseg-ruleset-admin`, `codecov`) but are installed on
  **selected repos**. pc2img must be **added** to each, with the matching secrets (release App and
  protection App kept separate, template FLOOR). pc2img today has only
  `NIME_RELEASE_PLEASE_TOKEN` as a secret. **Owner account actions:** App installs + secrets;
  PyPI + TestPyPI trusted-publisher registration; `pypi` / `testpypi` GitHub environments; RTD
  project import; Codecov repo enable. The planner must put these at `checkpoint:human-action`
  tasks, ordered before the steps that need them.
- Tags on origin: `v0.10.0..v0.10.4`, moving `v0` / `v0.10`, `v2.0.0a5` (lightweight, `dev/v2`
  only), `archive/dev-perspective_projection-pre-fold`. `v2.0.0a1..a4` do not exist.
- Local `develop-gsd` is **behind** `origin/develop-gsd` (`e9eb3c4`, PR #12 merge). The Phase 6
  branch must start from `origin/develop-gsd`.
- `STATE.md` still contains a stale line ("Phase 6 is NOT the current phase…"), superseded since
  PR #12 merged. Clean it up with the state update.
- Downstream: iof3D (`/scratch/34_iof3d`) pins pc2img by a git ref (`@v2.0.0a1`, commented out and
  unresolvable). The migration record should direct it to `pc2img ~= 0.11` from PyPI.

</code_context>

<specifics>
## Specific Ideas

- The owner framed the split as "CI/CD goes directly as part of Phase 6; the code rework belongs
  with the milestone ship". The mechanical refinement agreed on: the split is **by time, not by
  content**, because `main` is a filtered projection, so any promotion carries all of
  `develop-gsd`. The first promotion carries the reviewed Phase 1–5 code, and Phase 7's rework
  becomes the first change through the new protected flow.
- Reproduce, don't read (project rule): the Phase 7 exception-type question (`StoreKeyError` /
  `StoreContainmentError` vs `ValueError`) must be settled by instantiating, not by reading GSEGUtils.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 7: GSEGUtils 0.6 Adoption & 0.11.0 Release** (D-24): ADDED to ROADMAP.md 2026-09-28 with
  new requirement DEP-05; BC-01 traced to Phases 6 (draft) and 7 (finalise). The 0.11.0 release-PR
  merge is Phase 7's last step, not part of `/gsd-complete-milestone`.
- Tag-protection ruleset on `refs/tags/v*`: deferred by the template itself (it would need a
  bypass actor for release-please's moving tags).
- Tighter review policy (1 required approval): the template's future-tightening item, for when a
  second routine reviewer exists.

### Reviewed Todos (not folded)
- `2026-07-27-rrim-float32-scaling-invariant-guard.md`: minor correctness hardening for absurd
  `z_factor`. Not publication work, so it stays pending (candidate for Phase 7 or a later milestone).
- `2026-07-09-document-cuda11-vs-cuda12-selection-guidance.md`: low urgency. The README's CUDA
  extras note (D-14) may cover the short version; the full guidance stays pending.
- `2026-07-09-guard-transformarray-module-import.md`: **already resolved** (import is under
  `TYPE_CHECKING` in `strategies/projection.py`). Close the todo.
- `2026-07-09-coerce-null-lazy-disk-cache-config.md`: **already resolved** (commit `0658181`,
  "coerce omitted config"). Close the todo.

</deferred>

---

*Phase: 06-publication-hardening-downstream-migration-record*
*Context gathered: 2026-09-28*
