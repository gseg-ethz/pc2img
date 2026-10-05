---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 07
subsystem: release-gates
tags: [gates, d-03, unlocked-wheel, phase-review, release]
requires: [07-02, 07-03, 07-04, 07-05, 07-06]
provides:
  - gate record on the final reviewed tip (2c818e2)
  - D-03 unlocked-wheel check on the final reviewed tip
  - phase-diff review outcome (7 review rounds, 6 gap rounds)
affects: [07-08, 07-09, 07-10, 07-11]
key-files:
  created: []
  modified: []
decisions:
  - "D-03 re-taken after the gap rounds: the shipped tree changed between 5ee3c80 and 2c818e2 (pyproject.toml, disk_backed_image_store.py, tiled_generator.py, test_image_store.py, test_tiled_generator.py), so the latest D03_SHA is 2c818e2a453f39792931db4e7e255c5fa9f0551b"
  - "Owner decisions at the review checkpoint: stop downstream fix-on-fix on the GC-ownership mechanism; ship with conservative known-limitations docs; GSEGUtils#83 filed"
metrics:
  duration: "~25 min across two executor runs (original gates + re-run after gap rounds)"
  completed: 2026-10-05
status: complete
actuals:
  tokens: 0
  tasks: 3
  commits: 0
plan_head_before: 2c818e2a453f39792931db4e7e255c5fa9f0551b
plan_head_after: 2c818e2a453f39792931db4e7e255c5fa9f0551b
---

# Phase 07 Plan 07: Gate re-run, D-03 unlocked-wheel check, phase-diff review Summary

Every release gate is green on the final reviewed tip (2c818e2), the built wheel passes the whole suite in a fresh unlocked environment against today's PyPI (GSEGUtils 0.6.0, pchandler 2.1.1, numpy 2.3.5; 311 passed, identical to the locked total), and the phase diff was independently reviewed over seven rounds with 36 findings resolved with fix-commit evidence, 16 deferred with targets, and 0 open.

This plan has no task commits by design (`files_modified: []`); `commits: 0` is measured (`plan_head_before` equals `plan_head_after` at SUMMARY write, with no shipped-file changes by this plan). Its output is this record.

## Gate re-run

Original run, first executor, HEAD `5ee3c80d62b49c16913a77545e8536e9546e1b0f` (before any gap round):

| Gate | Result |
|------|--------|
| `uv lock --check` | rc 0, 137 packages |
| `check_publish_gate.py` | OK |
| `.github/scripts` suite | 120 passed |
| Full suite with coverage (`-m "not benchmark" --cov=pc2img --cov-branch --cov-fail-under=55`) | 367 passed, 1 xfailed; coverage 63.14% / 63.64% (floor 55%) |
| temp-leak count (TMPDIR on the pytest process only) | 0 |
| `uv build` | OK (pc2img-0.10.4.post522) |
| `twine check` | PASSED |
| migration verifier | `[ok] verified 30 entries` |
| `scripts/smoke_pipeline.py` | `OK shape=(260, 200)` |
| `pre-commit run --all-files` | rc 0 |
| withdrawn-name grep | empty |
| docs `sphinx-build -W` | build succeeded |
| pyright | not run (not in the locked env; informational, `continue-on-error` in CI) |

## Gate re-run (after gap rounds)

HEAD `2c818e2a453f39792931db4e7e255c5fa9f0551b` on `gsd/phase-07-gsegutils-0-6-adoption-0-11-0-release` (118 commits ahead of origin/develop-gsd). Re-taken because the gap rounds changed shipped files between 5ee3c80 and 2c818e2: `pyproject.toml`, `src/pc2img/image_cache/disk_backed_image_store.py`, `src/pc2img/tiled_generator.py`, `tests/test_image_store.py`, `tests/test_tiled_generator.py`.

| Gate | Result (verbatim tail) |
|------|------------------------|
| `uv lock --check` | `Resolved 137 packages in 1ms`, rc 0 |
| `check_publish_gate.py` | `check_publish_gate: OK — publish steps found only in allowed files + environments` |
| `uv run --frozen pytest .github/scripts/ -q` | `120 passed in 1.88s` |
| Full suite + coverage floor | `Required test coverage of 55% reached. Total coverage: 65.01%` / `403 passed, 94 warnings in 38.58s` (0 failed, 0 xfailed: the CR-01 xfail no longer exists) |
| temp-leak count | `leak: 0` (TMPDIR on the pytest process only; see Deviations) |
| `uv build` | `Successfully built dist/pc2img-0.10.4.post605.tar.gz` and `...post605-py3-none-any.whl` |
| `uvx twine check dist/*` | wheel `PASSED`, sdist `PASSED` |
| Migration verifier (extracted from `.planning/MIGRATION-v0.11.md`) | `[ok] verified 30 entries`, rc 0 |
| `scripts/smoke_pipeline.py` | `OK shape=(260, 200) finite_fraction=0.961 min=8.801 max=11.269 artifacts=['range.dat']` |
| `pre-commit run --all-files` | ruff check, ruff format, trailing whitespace, end-of-files, check yaml, check toml, large files: all `Passed`, rc 0; no tracked file modified |
| Withdrawn-name `git grep` over `src tests` | exit 1, empty result (`no-withdrawn-names`) |
| Docs `sphinx-build -W --keep-going -b html docs/source docs/_build/html` | `build succeeded.` (doc group already synced: `uv sync --frozen --group doc` reported `Checked 90 packages`, no change to the environment) |
| pyright | not run: `uv run --frozen pyright` fails to spawn (not in the locked env); informational only |

Reviewed scope: `git diff --stat origin/develop-gsd...HEAD` ends `97 files changed, 18262 insertions(+), 1300 deletions(-)` (all but 16 are under `.planning/`). Shipped files changed vs origin/develop-gsd:

```
.github/scripts/check_publish_gate.py
.github/scripts/preflight_ruleset_apply.py
.github/scripts/ruleset_lib.py
.github/scripts/test_check_publish_gate.py
.github/scripts/test_check_ruleset_drift.py
.github/scripts/test_preflight_ruleset_apply.py
.github/scripts/test_ruleset_lib.py
.readthedocs.yaml
RULESETS.md
pyproject.toml
src/pc2img/image_cache/disk_backed_image_store.py
src/pc2img/tiled_generator.py
tests/conftest.py
tests/test_image_store.py
tests/test_tiled_generator.py
uv.lock
```

`dist/` holds the wheel and sdist for pc2img-0.10.4.post605 built from this tip.

## D-03 unlocked-wheel check

Original run at `5ee3c80` (no lock, fresh venv, wheel pc2img-0.10.4.post522): resolved GSEGUtils 0.6.0, pchandler 2.1.1, numpy 2.3.5. Unlocked pytest: `275 passed, 1 deselected, 1 xfailed`, equal to the locked total under the same exclusions.

D03_SHA: 5ee3c80d62b49c16913a77545e8536e9546e1b0f

### Re-run after gap rounds

Fresh wheel (pc2img-0.10.4.post605), fresh unlocked venv `_scrap/unl` (`uv venv --python 3.12`; `uv pip install dist/pc2img-*.whl pytest pyyaml`, no lock, no `--frozen`), tests copied to `_scrap/unl_tests` (removed afterwards). Wheel is what imports: `/scratch/31_pc2img/_scrap/unl/lib/python3.12/site-packages/pc2img/__init__.py 0.10.4.post605`.

Resolved versions:

```
gsegutils         0.6.0
numpy             2.3.5
pc2img            0.10.4.post605
pchandler         2.1.1
```

Unlocked run (`../unl/bin/python -m pytest -q -p no:cacheprovider --ignore=tests/test_hygiene.py --ignore=tests/test_git_archival.py --deselect tests/test_rrim_features.py::test_rrim_module_docstring_clears_e402`):

```
311 passed, 1 deselected, 94 warnings in 21.30s
```

Locked run with the same exclusions (`uv run --frozen pytest -q -p no:cacheprovider` plus the same `--ignore`/`--deselect`):

```
311 passed, 1 deselected, 94 warnings in 21.75s
```

Totals match (311 passed + 0 xfailed + 0 xpassed on both sides; the earlier xfail is gone since CR-01 was fixed, so the original run's `275 passed + 1 xfailed = 276` is not comparable to this one). Shipped-tree diff `git diff --name-only <D03_SHA> HEAD -- . ':(exclude).planning' ':(exclude).claude'` against the new line: empty.

D03_SHA: 2c818e2a453f39792931db4e7e255c5fa9f0551b

## Review outcome

Owner reply at the checkpoint: "reviewed" (2026-10-05). Seven review rounds over the phase diff and six gap rounds:

| Round | Review | Report |
|-------|--------|--------|
| 1 | `/gsd-code-review 7` (deep, opus) plus `/code-review origin/develop-gsd high` over 9bb6b51..5ee3c80 (16 shipped files) | `07-REVIEW.md` |
| 2 | gap plans 07-12..07-14 | `07-REVIEW-GAP1.md` |
| 3 | gap plans 07-16..07-18 | `07-REVIEW-GAP2.md` |
| 4 | gap plans 07-19..07-21 | `07-REVIEW-GAP3.md` |
| 5 | docs-only gap plan 07-22 | `07-REVIEW-GAP4.md` |
| 6 | docs-only gap plan 07-23 | `07-REVIEW-GAP5.md` |
| 7 (scoped) | docs-only gap plan 07-24 | `07-REVIEW-GAP6.md` |

The reviewer-supplied clause fix `64655a6` was verified mechanically by owner decision.

Result in `07-UAT.md` `## Gaps`: 36 resolved (each with fix-commit evidence), 16 deferred with targets (GSEGUtils#83 / pc2img 0.11.1; post-0.11.0 backlog), 0 open, 0 `status: failed` of any severity. Plan 07-15 (the pc2img#24 comment) is on hold for a redraft and is not part of 07-07.

Owner decisions recorded: stop downstream fix-on-fix on the GC-ownership mechanism; ship with conservative known-limitations docs; GSEGUtils#83 filed.

Tasks 1-2 were re-run after the gap rounds (the gap rounds changed shipped files), and the latest `D03_SHA:` line above matches the tip: the shipped-tree diff against HEAD is empty.

## Deviations from Plan

1. **Dirty-tree precondition (Task 1), both runs.** The working tree is not literally clean: the pre-existing tracked modification `.planning/config.json` and a set of pre-existing untracked files (`.codex`, `.editorconfig`, `.gsd/`, `.planning/milestone.lock`, `.planning/state.json`, `.vscode/`, `_tests/`, `pyrightconfig.json`, `scripts/0*.py`, `scripts/v1.0/`, `scripts/v2.0/`, review diagnostics) exist outside the shipped tree. No tracked shipped file was modified; `pre-commit` left the tracked tree unchanged. The precondition was asserted by intent (tracked shipped tree equals HEAD), not by `git status --porcelain` being empty.
2. **TMPDIR on the pytest process only (Task 1).** `export TMPDIR=...` for the whole `uv run` made uv itself write `uv-<hash>.lock` into the directory, giving a false leak count of 1. Re-run with `uv run --frozen env TMPDIR=<dir> pytest ...`: leak count 0 (only `pytest-of-<user>`). Same approach as the original run.
3. **pyright not run (Task 1).** Not installed in the locked environment; informational (`continue-on-error` in CI), not gated.
4. **`check_ci_config.py` absent** (noted by the first executor); not part of the plan's gate list.
5. **No Task 1-2 commits.** `files_modified` is empty; the only commit from this plan is the SUMMARY and bookkeeping commit.
6. **xfail count.** The original run had 1 xfailed (CR-01 loky race test); that test was fixed in a gap round, so the re-run shows 0 xfailed and the D-03 comparison was made on 311 passed on both sides.

## Self-Check: PASSED

- Gate output blocks and D-03 lines recorded above; latest `D03_SHA` equals the tip run on (2c818e2a453f39792931db4e7e255c5fa9f0551b).
- `_scrap/unl_tests` removed; `_scrap/unl` retained until 07-11.
