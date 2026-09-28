# Phase 6: Publication Hardening & Downstream Migration Record - Pattern Map

**Mapped:** 2026-09-28
**Files analyzed:** 24 (new/modified/deleted)
**Analogs found:** 24 / 24 (this phase is a template-assembly job — every file has an authoritative kit source, per D-07/D-09; PCHandler's live instance is reference-only and the kit wins on conflict, per canonical_refs)

**Tracked-source gate note:** all kit paths cited below live under
`~/gsd-workspaces/pchandler/.planning/git-strategy/template/` — this is the tracked source tree of the
sibling `pchandler` GSD workspace repo, not a gitignored mirror inside pc2img. All paths were confirmed
to exist on disk this session (`ls -la`, file sizes shown). PCHandler reference paths
(`/scratch/41_pchandler/...`) are a separate, independently-tracked repo, used only for document-shape
modeling (RULESETS.md/RELEASE.md/CITATION.cff/.readthedocs.yaml), never as the authoritative source —
the template always wins on conflict (explicit in 06-CONTEXT.md canonical_refs). No pc2img-internal
mirror path is used anywhere in this file.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | CI workflow (config) | event-driven | kit `core/.github/workflows/ci.yml` | exact — wholesale replacement |
| `.github/workflows/ruleset-apply.yml` | CI workflow (config) | event-driven, dispatch-only | kit `core/.github/workflows/ruleset-apply.yml` | exact — new file |
| `.github/workflows/scheduled-health.yml` | CI workflow (config) | event-driven, scheduled | kit `core/.github/workflows/scheduled-health.yml` | exact — new file |
| `.github/rulesets/main.json` | config (branch protection payload) | request-response (GitHub API payload) | kit `core/.github/rulesets/main.json` | exact — new file |
| `.github/rulesets/develop.json` | config | request-response | kit `core/.github/rulesets/develop.json` | exact — new file |
| `.github/scripts/ruleset_lib.py` | utility | CRUD (GitHub API) | kit `core/.github/scripts/ruleset_lib.py` | exact — copy verbatim |
| `.github/scripts/preflight_ruleset_apply.py` | utility | validation | kit `core/.github/scripts/preflight_ruleset_apply.py` | exact — copy verbatim |
| `.github/scripts/check_ruleset_drift.py` | utility | validation | kit `core/.github/scripts/check_ruleset_drift.py` | exact — copy verbatim |
| `.github/scripts/test_ruleset_lib.py` + 2 sibling test files | test | unit | kit `core/.github/scripts/test_*.py` | exact — copy verbatim, run once post-assembly |
| `.github/actions/classify-changes/action.yml` | config (composite action) | transform | kit `core/.github/actions/classify-changes/action.yml` | exact — copy verbatim |
| `.github/actions/setup-python-deps/action.yml` | config (composite action) | transform | kit `core/.github/actions/setup-python-deps/action.yml` | role-match — **must be adapted**, see Pattern Assignments |
| `.github/workflows/release-please.yml` | CI workflow (config) | event-driven | kit `optional/release-pypi/.github/workflows/release-please.yml`; **replaces** pc2img's existing `.github/workflows/release-please.yml` (tracked) | exact — wholesale replacement, no content salvaged |
| `.github/workflows/publish-pypi.yml` | CI workflow (config) | event-driven, publish | kit `optional/release-pypi/.github/workflows/publish-pypi.yml` | exact — new file |
| `.github/workflows/publish-testpypi.yml` | CI workflow (config) | event-driven, publish (dispatch-only) | kit `optional/release-pypi/.github/workflows/publish-testpypi.yml` | exact — new file |
| `.github/scripts/check_publish_gate.py` | utility | validation | kit `optional/release-pypi/.github/scripts/check_publish_gate.py` | exact — copy verbatim |
| `release-please-config.json` | config | CRUD (merge with existing) | kit `optional/release-pypi/release-please-config.json`; **merges into** pc2img's existing tracked `release-please-config.json` | role-match — single-key fix (`extra-files`), not a full overwrite |
| `.release-please-manifest.json` | config | CRUD (merge, NOT overwrite) | kit ships `{".": "0.0.0"}`; pc2img's existing tracked file has `{".": "0.10.4"}` | **anti-pattern — do NOT copy** (Pitfall 1); keep pc2img's existing value |
| `.pre-commit-config.yaml` | config | validation | none in kit (ships none, D-11); model on ruff's own recommended pre-commit config + `pre-commit/pre-commit-hooks` standard hygiene set | no analog in kit — hand-write, see Pattern Assignments |
| `docs/source/conf.py` | config (Sphinx) | transform | `/scratch/41_pchandler/docs/source/conf.py` (reference instance, read for shape) | role-match — reference only, pc2img content differs |
| `docs/source/index.rst` | documentation | transform | none — minimal new file | no close analog; RESEARCH.md's measured 7-module `automodule::` sample is the working draft |
| `.readthedocs.yaml` | config | transform | `/scratch/41_pchandler/.readthedocs.yaml` | role-match — **must be adapted** for PEP 735 `doc` group vs PCHandler's extras-based `doc` |
| `CITATION.cff` | metadata | transform | `/scratch/41_pchandler/CITATION.cff` | role-match — **authors differ** (D-14: pc2img keeps single-author, no Jon Allemand) |
| `RULESETS.md` | documentation (adoption record) | transform | `/scratch/41_pchandler/RULESETS.md` (reference, pre-template shape — content differs) + kit's `GIT-STRATEGY.md` *Verifying an assembly* section (the actual current answers) | role-match — structure reusable, **values must be pc2img's D-08 answers, not PCHandler's pre-template ones** |
| `RELEASE.md` | documentation (adoption record) | transform | `/scratch/41_pchandler/RELEASE.md` | role-match — structure reusable (Trusted Publisher Binding table, "What NOT to Rename") |
| `README.rst` | metadata | transform | pc2img's existing `README.rst` (currently `##Hello`, tracked) — no real analog in-repo; PCHandler's own README/docs intro is the closest content model but was not read this session (D-14 leaves structure to planner discretion) | weak — Claude's discretion per CONTEXT |
| `MIGRATION-v0.11.md` | documentation (migration-spec) | transform | `/scratch/41_pchandler/MIGRATION-v1.0.md` | exact — format exemplar, read in full by RESEARCH.md this session |
| `scripts/01_tiled_image_generation_from_pointcloud.py` | script | n/a | **DELETE** (D-22) — no analog needed | n/a |
| `scripts/smoke_pipeline.py` | script | n/a | pc2img's existing tracked file — **edit in place** (D-20 vocab sweep + ruff I001 fix) | n/a — modification, not new file |
| `docs/pchandler-2x-break-audit.md` | documentation | n/a | pc2img's existing tracked file — **move** to `.planning/phases/02-.../` (D-21) | n/a — relocation |

## Pattern Assignments

### `.github/workflows/ci.yml` (CI workflow, event-driven)

**Analog:** `~/gsd-workspaces/pchandler/.planning/git-strategy/template/core/.github/workflows/ci.yml` (17,913 bytes, read in full by RESEARCH.md this session)

**Copy verbatim, then apply exactly 3 in-place edits** (RESEARCH.md *In-place edit sites*, all three site line numbers cited against the kit file):

1. **Site 1 — `ci.yml:305`, docs job "Build docs" step.** Kit's literal text: `pip install .[doc]`.
   Must change — pc2img's `doc` group is currently `[dependency-groups]` (PEP 735), not a
   `[project.optional-dependencies]` extra. RESEARCH.md's own recommended fix (code example, already
   drafted):
   ```yaml
   - name: Build docs (warnings as errors)
     if: steps.classify.outputs.release-artifacts-only != 'true'
     working-directory: .
     run: |
       uv sync --frozen --group doc
       # ...version-assertion snippet unchanged...
       uv run sphinx-build -W --keep-going -b html docs/source docs/_build/html
   ```
   **However:** RESEARCH.md's Pitfall 3 / Assumption A3 flags that Read the Docs itself (a *separate*
   site, `.readthedocs.yaml`) cannot consume a PEP 735 group at all — only extras. D-31 (added at
   plan-phase, in `06-CONTEXT.md`) already resolves this in the owner's favor: `doc` **stays** a PEP 735
   group; CI installs it with `uv sync --frozen --group doc` (as drafted above) and `.readthedocs.yaml`
   uses an explicit `build.jobs` install step (not `extra_requirements`) to install the same group. Do
   not apply RESEARCH.md's Assumption A3 recommendation (converting `doc` to an extra) — it is
   superseded by D-31/D-32.
2. **Site 2 — `ci.yml:330`.** `sphinx-build -W --keep-going -b html docs/source docs/_build/html` — no
   edit needed; D-13's minimal layout already matches.
3. **Site 3 — `ci.yml:~318`, version-assertion snippet** (`tomllib.loads(...)["project"]["name"]`) — no
   edit needed; pc2img already uses `pyproject.toml` as its packaging manifest.

**Carry forward from pc2img's existing (tracked) `ci.yml`, per D-16:** the `--cov-fail-under=55` flag
on the `pytest` invocation — the kit's own Tests job has no coverage floor; add it as a recorded
addition, not a silent edit.

**GPU sites (3, in `gpu.yml`) do not apply** — `gpu-self-hosted` component declined (D-09).

---

### `.github/actions/setup-python-deps/action.yml` (composite action, transform)

**Analog:** kit `core/.github/actions/setup-python-deps/action.yml` (716 bytes)

**Adaptation required (D-10, recorded DEFAULT deviation):** the kit's composite installs with
`pip install .[dev]` (extras-based). Replace with `uv sync --frozen` against the committed `uv.lock`,
because pc2img's dev tooling is PEP 735 `[dependency-groups]`, not an extra — `pip install .[dev]`
would install **zero** dev tools (no ruff, pytest, coverage). Record this deviation both at the file
site (a comment) and in `RULESETS.md`/CI-CD adoption record (D-15).

---

### `.github/workflows/release-please.yml` (CI workflow, event-driven)

**Analog:** kit `optional/release-pypi/.github/workflows/release-please.yml` (5,658 bytes)

**Replaces pc2img's existing tracked file** (`/scratch/31_pc2img/.github/workflows/release-please.yml`
— currently `push: branches: [main]`, unpinned `actions/checkout@v4`, unpinned
`googleapis/release-please-action@v4`, default `GITHUB_TOKEN`, unguarded `git tag -d ... || true`).
**No content is salvaged** — wholesale replacement. The kit version differs in every load-bearing way:
SHA-pinned actions (`googleapis/release-please-action@45996ed1f6d02564a971a2fa1b5860e934307cf7`, v5.0.0),
App-token authentication via `actions/create-github-app-token`
(`bcd2ba49218906704ab6c1aa796996da409d3eb1`, v3.2.0) using the **release** App's secrets (distinct from
the ruleset-apply App's secrets — two separate Apps, template FLOOR), and status-checked tag
deletion/retag (`if ! git push origin ":refs/tags/$TAG"` replacing the old silent `|| true`).

---

### `release-please-config.json` / `.release-please-manifest.json` (config, CRUD)

**Analog:** kit `optional/release-pypi/release-please-config.json` and `.release-please-manifest.json`

**`release-please-config.json`:** [VERIFIED by RESEARCH.md this session] pc2img's existing tracked file
already matches the kit's **byte-for-byte** except the `extra-files` key (currently
`["docs/conf.py"]`, pointing at a file that has never existed). Single-key fix, per D-13's resolution:
remove the `extra-files` key entirely (recommended — the docs job's version assertion already derives
version dynamically via `importlib.metadata.version("pc2img")`, so there is no static version string
for the generic updater's marker mechanism to act on).

**`.release-please-manifest.json`:** **Do NOT copy the kit's file.** [Pitfall 1, RESEARCH.md] The kit
ships `{".": "0.0.0"}`, a fresh-project placeholder. pc2img's existing tracked file has
`{".": "0.10.4"}` — real release history. Treat this file as a merge conflict, not a template-copy
target: keep `0.10.4` and discard the kit's `0.0.0`. `git diff` after assembly must show this file
**unchanged**.

---

### `.pre-commit-config.yaml` (config, validation)

**No kit analog** (the kit ships none, D-11). Hand-write per D-11's spec: ruff check + ruff format
hooks, plus standard `pre-commit/pre-commit-hooks` hygiene hooks (`trailing-whitespace`,
`end-of-file-fixer`, `check-yaml`, `check-toml`, `check-added-large-files`). No mypy (pc2img uses
pyright, informational-only per D-12). No license-banner hook (owner declined). Lint scope: whole
shipped tree, matching the `Lint (pre-commit)` job's `<LINT_CONTEXT>` token.

**Ruff remediation surface** (measured this session by RESEARCH.md, ruff 0.15.12, whole tree minus
`.planning/`/`.claude/`): 13 hits net of the D-22 delete —
- `src/pc2img/features/derivative_features.py`: C901 ×4
- `src/pc2img/util.py`: C901 ×2
- `tests/test_disk_backed_image_data.py`: NPY002 ×2
- `tests/test_util.py`: ERA001 ×2 (the `# Breadth:` headers)
- `tests/test_tiled_generator.py:27`: F401 (unused `pytest` import)
- `tests/test_point_cloud_image_generator.py:1`: I001 (import sort)
- `scripts/smoke_pipeline.py:23`: I001 — **new, not in D-11's original 12**, autofixable

Format: `ruff format --check` flags `setup.py` (new finding, trivial 9-byte-stub, `ruff format setup.py`
fixes it) in addition to the file being deleted (`scripts/01_...`).

---

### `.readthedocs.yaml` (config, transform)

**Analog:** `/scratch/41_pchandler/.readthedocs.yaml` (read in full this session; reproduced below verbatim as the structural model):
```yaml
version: 2
build:
  os: ubuntu-24.04
  tools:
    python: "3.12"
sphinx:
  configuration: docs/source/conf.py
python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - doc
```
**Must be adapted per D-31** (this supersedes RESEARCH.md's own Assumption A3 recommendation to convert
`doc` to an extra): since `doc` stays a PEP 735 `[dependency-groups]` entry, replace the
`extra_requirements: [doc]` mechanism (which RTD's schema cannot resolve for a dependency-group) with
an explicit `build.jobs` install step that installs the `doc` group directly — e.g. `pip install
--group doc` (needs pip >= 25.1, confirmed present in this environment) or a `uv`-based install
mirroring CI's `uv sync --frozen --group doc`. This is the authoritative deviation site; record it in
the CI/CD adoption record per D-15/D-31.

---

### `CITATION.cff` (metadata, transform)

**Analog:** `/scratch/41_pchandler/CITATION.cff` (read in full this session; excerpt above under
Metadata / Build). Model the shape exactly: `cff-version: 1.2.0`, `authors` list (name/affiliation/
orcid), `repository-code`/`url`, `license: BSD-3-Clause`, a `message:` block describing the
main-branch-reflects-latest-release convention, and a `preferred-citation` block with a placeholder
Zenodo DOI (`10.5281/zenodo.XXXXXXX`) — pc2img has no archive DOI yet either.

**Differences from the analog (D-14):** **authors unchanged** — pc2img's `authors:` list is Nicholas
Meyer only (matches `pyproject.toml`'s existing single-author `[project.authors]`), unlike PCHandler's
two-author (`Nicholas Meyer` + `Jon Allemand`) file. `repository-code`/`url` point at
`https://github.com/gseg-ethz/pc2img` (not `PCHandler`). `title: pc2img`.

---

### `RULESETS.md` / `RELEASE.md` (documentation, adoption record)

**Analog:** `/scratch/41_pchandler/RULESETS.md` and `/scratch/41_pchandler/RELEASE.md` (both read in
full this session — excerpts above). **Structure is reusable** (Bypass List section, Approval Policy
section for RULESETS.md; Trusted Publisher Binding table + "What NOT to Rename" list for RELEASE.md).

**Content must NOT be copied** — PCHandler's own files describe **its own pre-template, pre-current
state** (e.g. its RULESETS.md still says "Configured: TBD — configured in Phase 11", describes a
0-required-approvals policy that pc2img's D-08 answers may differ from, and its bypass-list reasoning
is specific to PCHandler's release-please branch-targeting quirks). pc2img's `RULESETS.md`/`RELEASE.md`
must state pc2img's **own** D-08 interview answers (main/develop-gsd, `protect-main`/
`protect-develop-gsd`, `bypass_actors: []` on both per FLOOR, `strict_required_status_checks_policy`
true on `main` only) and D-09/D-10/D-11/D-31 deviations (components declined + cost of declining, the
`uv` deviation, the `doc`-group RTD deviation), per D-15. No planning IDs in the shipped text — D-15
requires it read as a clean adoption record, not a decision log.

**Trusted-publisher claim-field table (RELEASE.md pattern)**, reused verbatim in shape, values changed:
```
| Field | Value |
|-------|-------|
| Owner (GitHub) | gseg-ethz |
| Repository | pc2img |
| Workflow filename | publish-pypi.yml |
| Environment name | pypi |
```
(pc2img adds a second row for the TestPyPI dry run — `environment: testpypi`, `repository-url:
https://test.pypi.org/legacy/` — per D-05/D-30 item 3, since RELEASE.md's PCHandler exemplar only
documents the real-PyPI claim.)

---

### `MIGRATION-v0.11.md` (documentation, migration-spec)

**Analog:** `/scratch/41_pchandler/MIGRATION-v1.0.md` (233 lines, read in full by RESEARCH.md this
session). **Format exemplar, followed closely** per D-25:

- Frontmatter: `type: migration-spec`, `spec_version`, `repo: pc2img`, `baseline_ref: 91b4ab6`,
  `target_ref: <develop-gsd HEAD at plan-execution time — not a fixed SHA yet>`, `generated_at`,
  `bc_id_prefix: BC-P2I`, `milestone: v1.0`.
- Body section order (from the analog): `# pc2img MIGRATION-v0.11` heading restating Baseline/Target in
  prose → `## Summary` → `## Public API stability invariant` (states what the verifier proves, and
  cites pc2img's one deliberately-different framing vs. PCHandler per D-25: pc2img has no "no breaking
  import paths" invariant, so `must-edit`/`surface-removed` entries are **expected**, classified not
  escalated) → `## Breaking changes & behavior changes` (table: BC-ID / category / severity /
  affected_symbols / origin / migration_steps) → `## Additive changes` (same table shape, `additive`
  severity only) → `## Internal & sweep changes` (flat bullet list, not a table — each bullet states
  "no public-surface change") → `## Verifier (inline)` (fenced ` ```python ` block, runnable standalone).

**Primary entry source:** `.planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md` — 17
entries, read in full by RESEARCH.md this session, close to 1:1 onto `BC-P2I-NNN` rows. Entry 10 is
already **closed** (transcribe as `dep-constraint`/`informational` historical record). Entries 5, 6, 17
are "NO BEHAVIOR CHANGE" — land in *Internal & sweep changes*, not the breaking table.

**Verifier — adapted, not copied** (pc2img has no `.pyi` stubs, unlike PCHandler's Tier-1 AST-walk over
`__init__.pyi` files). RESEARCH.md already drafted the adapted Tier-1 extraction against pc2img's 4
`__init__.py` `__all__` lists — reuse this code block verbatim as the verifier's Tier-1 pass:
```python
import ast
import pathlib

PUBLIC_SURFACE_FILES = [
    "src/pc2img/__init__.py",
    "src/pc2img/features/__init__.py",
    "src/pc2img/strategies/__init__.py",
    "src/pc2img/image_cache/__init__.py",
]

def extract_all(py_text: str) -> set[str]:
    tree = ast.parse(py_text)
    declared: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__" and isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            declared.add(elt.value)
    return declared
```
Tier-2 runtime `getattr` checks per BC-note entry (already stated precisely enough to code directly by
RESEARCH.md): entry 7 (`RegistryLookupError` subclass check), entry 9 (`DiskBackedImageData.__add__`
returns `np.ndarray`, doesn't raise), entry 8 (legacy `.pkl` cache degrades to a miss — reuse
`tests/test_image_store.py:63`'s existing test pattern), entry 15 (path-traversal key raises
`ValueError` — reuse existing dedicated test assertions, don't re-derive).

---

### `scripts/smoke_pipeline.py` (script, modification — vocab sweep)

**Analog:** the file itself (pc2img's existing tracked file), edited in place — not a template copy.
D-20 vocab-sweep hits found this session (new, not in D-20's original known list): `D-10` (×2, lines 5
and 44), `D-09` (line 6), phase references "Phase 2"/"Phase 4/5" (lines 6-7, 60, 62). File **stays**
per D-22 (only `scripts/01_...` is deleted). Also carries a new ruff I001 hit (line 23, autofixable via
`ruff check --fix`).

---

## Shared Patterns

### SHA-pinning (FLOOR, applies to every new/replaced workflow file)
**Source:** kit's own `ci.yml`/`ruleset-apply.yml`/`release-please.yml`/`publish-*.yml`, already
SHA-pinned throughout (verified table in RESEARCH.md *Standard Stack*).
**Apply to:** all 6 new/replaced `.github/workflows/*.yml` files.
```yaml
# every third-party `uses:` line must show a 40-char hex SHA, never a tag ref, e.g.:
- uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd  # v5.0.1
```
Verification: `grep -rn 'uses:' .github/` — apply-time checklist item 9.

### `uv sync --frozen` instead of `pip install .[X]` (D-10/D-31 deviation)
**Source:** `.github/actions/setup-python-deps/action.yml` adaptation (dev) and `ci.yml` docs-job site 1
(doc). **Apply to:** `setup-python-deps/action.yml`, `ci.yml`'s docs job, `.readthedocs.yaml`'s
`build.jobs` step. Root cause: pc2img uses PEP 735 `[dependency-groups]` for both `dev` and `doc`, not
`[project.optional-dependencies]` extras (Pitfall 2/3 in RESEARCH.md).

### Two separate GitHub Apps, never shared secrets (FLOOR)
**Source:** kit's `ruleset-apply.yml` (`<APPLY_APP_ID_SECRET>`/`<APPLY_APP_KEY_SECRET>`) vs.
`release-please.yml` (`<RELEASE_APP_ID_SECRET>`/`<RELEASE_APP_KEY_SECRET>`).
**Apply to:** any workflow minting an App token via `actions/create-github-app-token`. The protection
App (`gseg-ruleset-admin`) and release App (`gseg-release-please`) credentials must never be the same
secret pair — a compromise of one must not grant the other's scope.

### `bypass_actors: []` present and empty, never absent (FLOOR)
**Source:** kit `core/.github/rulesets/main.json` / `develop.json`.
**Apply to:** both ruleset JSON payloads, verified by reading them back after apply (step 8 of Procedure
B) — an **absent** key is a hard failure distinct from an empty array.

### No planning vocabulary in shipped text (D-20, D-15, D-28)
**Source:** the D-20 gate regex, run this session by RESEARCH.md:
`\b(BUG|DSN|QUAL|TEST|DEP|CICD|BC)-[0-9]+\b|\bM-[0-9]{1,3}\b|\bD-[0-9]{1,3}\b` plus a phase-reference
pass and a literal `.planning` path pass.
**Apply to:** every file this phase writes or edits that lands on `main` — `RULESETS.md`, `RELEASE.md`,
`MIGRATION-v0.11.md`, `README.rst`, `CITATION.cff`, `pyproject.toml` comments, `CONTRIBUTING.md`,
`scripts/smoke_pipeline.py`, and any doc under `docs/` except the two IP files exempted by D-23.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `docs/source/index.rst` | documentation | transform | Genuinely new minimal content; RESEARCH.md's measured 7-module `automodule::` sample (built and warning-counted this session) is the closest working draft, not a copyable analog. |
| `README.rst` (content, not structure) | metadata | transform | pc2img's current file is a placeholder (`##Hello`); no in-repo analog exists. D-14 leaves structure/depth to Claude's discretion; PCHandler's own README content was not read this session — planner should pull install/quickstart/RRIM-notice/CUDA-extras content directly from pc2img's own existing docs (CONTRIBUTING.md, NOTICE, pyproject.toml extras) rather than PCHandler's README. |

## Metadata

**Analog search scope:** `~/gsd-workspaces/pchandler/.planning/git-strategy/template/{core,optional/release-pypi}/**` (kit, authoritative); `/scratch/41_pchandler/{.github/,RULESETS.md,RELEASE.md,.readthedocs.yaml,CITATION.cff,MIGRATION-v1.0.md}` (reference instance); `/scratch/31_pc2img/{.github/,pyproject.toml,release-please-config.json,.release-please-manifest.json,README.rst,scripts/smoke_pipeline.py}` (current pc2img tracked state).
**Files scanned:** kit — 20 files read in full by RESEARCH.md this session (per its Sources section); pc2img — 7 tracked files re-confirmed this session (`git ls-files` + direct reads).
**Pattern extraction date:** 2026-09-28
**Note on source freshness:** RESEARCH.md flags itself as "valid until short" — re-measure ruff/sphinx/git-tag state if more than ~7 days elapse before this PATTERNS.md is consumed by planning.
