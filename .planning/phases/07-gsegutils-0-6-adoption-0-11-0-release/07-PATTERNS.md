# Phase 7: GSEGUtils 0.6 Adoption & 0.11.0 Release - Pattern Map

**Mapped:** 2026-10-01
**Files analyzed:** 12 (code/test/config) + release-infra group
**Analogs found:** 10 / 12 (all analogs are git-tracked; `.planning/` is tracked on develop-gsd)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `src/pc2img/image_cache/disk_backed_image_store.py` (modify: delete 3 overrides + `__delitem__`, `purge`, docstring) | store wrapper | CRUD / file-I/O | itself (shrink); target = `.planning/spikes/001-orphaned-override-hunt/target_store.py` | exact |
| `tests/test_image_store.py` (rewrite 12 tests, escape-corpus re-pin, autouse tmp fixture) | test | file-I/O | itself (`tmp_path` + `LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path)` pattern, lines 64-170) | exact |
| `tests/conftest.py` (autouse `tempfile.tempdir` fixture, D-12) | test config | n/a | `tests/conftest.py` fixtures (lines 152-195) | role-match |
| `tests/test_tiled_generator.py` (new `n_jobs=2` xfail test) | test | event-driven (loky fan-out) | same file + `conftest.make_synthetic_pcd` | role-match |
| `pyproject.toml` (pins) | config | n/a | lines 33-37 of itself | exact |
| `uv.lock` | config | n/a | regenerate with `uv lock`; no analog | n/a |
| `.planning/MIGRATION-v0.11.md` (append entries, re-stamp target_ref) | docs/record | n/a | existing entries in the same file (read it for D-25 schema; not re-read here) | exact |
| `.github/scripts/check_publish_gate.py`, `preflight_ruleset_apply.py`, `test_ruleset_lib.py`, `ruleset_lib.py`, `RULESETS.md`, `.readthedocs.yaml` | CI scripts / config | request-response | each file itself (small targeted edits, D-13..D-15) | exact |
| `07-GSEGUTILS-ISSUE.md`, `07-TRACKING-ISSUE.md` (issue-body drafts, phase dir) | docs | n/a | none for drafts; see "Owner checkpoint with `gh`" | no analog |
| owner-checkpoint plan task (file issues, PyPI publisher) | plan task | request-response | `06-12-PLAN.md` lines 70-86, 116-132 | exact |

## Pattern Assignments

### `src/pc2img/image_cache/disk_backed_image_store.py` (store wrapper)

**Analog:** current file (267 lines) shrunk per RESEARCH "Recommended end state".
Delete: `_assert_within_cache_dir` (60-116), `_get_npy_path`/`_get_meta_path` (118-124), `__delitem__` (186-239), `from pathlib import Path` (line 1). Keep `__init__` (39-56, None-sentinel), `offload` (246-262), `offload_image_data_to_disk` (264-266).

**Imports target** (line 3 changes):
```python
from GSEGUtils.lazy_disk_cache import DiskBackedStore, LazyDiskCacheConfig, get_npy_path
```

**Core pattern to replace lines 174-177** (containment first, shape, purge on overwrite):
```python
get_npy_path(self.cache_dir, img_name)   # StoreKeyError (a ValueError) before anything else
_assert_image_shape(img_data)            # AssertionError
if img_name in self:
    self.purge(img_name)                 # replaces `del self[img_name]`
self.add_data_to_store(img_name, img_data, enable_caching_override=..., ...)
```
**Annotation fix** (lines 241-244): `image_data` returns read-only mapping; change `dict[str, DiskBackedImageData | None]` to `Mapping[...]`.
**Docstring**: replace the 24-37 containment invariant with one paragraph (containment upstream, construction-time, non-adversarial; entry-owned `cache_path` still not guarded). Update `offload` docstring (references `_get_npy_path`), `add_image_to_store` ordering paragraph (drop "del"/ABA text, mention `purge` refusals: `StorePurgeRefusedError` RuntimeError, `StorePurgeIncompleteError` OSError). Shipped text must avoid planning vocabulary (see Shared: hygiene gate).

### `tests/test_image_store.py` (test, file-I/O)

**Analog:** same file. Setup idiom (lines 78, 87):
```python
store = DiskBackedImageStore(config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))
```
Imports header (lines 16-26) already has `LazyDiskCacheConfig`, `Path`, `np`, `pytest`; add `from GSEGUtils.lazy_disk_cache import get_npy_path, get_meta_path, StoreKeyError`. `_gray(shape, dtype)` helper at line 33.
- 5 pure renames: `store._get_npy_path(k)` -> `get_npy_path(store.cache_dir, k)` (note `cache_dir` is the resolved property).
- 7 semantic rewrites: `del` drops tracking only; `purge` removes `.dat`+`.npy`+`.meta.json`; setter refuses escaping key (4 tests: assert `pytest.raises(ValueError)` at `store[key] = ...` and key untracked). Use RESEARCH Pattern 2 (`_tree(tmp_path)` whole-tree snapshot, 3 spellings x routes) and "Rewritten semantic tests" shape (RESEARCH lines 383-393). Keep `ValueError` as the asserted contract.
- `test_delete_absent_key...` (r4-84a2b5dff14c): fold or differentiate; now exercises upstream `__delitem__`.

### `tests/conftest.py` (autouse tmp isolation, r4-15a5c4928dc8)

**Analog:** `@pytest.fixture` style at conftest.py:152-195. Add:
```python
@pytest.fixture(autouse=True)
def _isolate_tempdir(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
```
(conftest has no autouse fixture today; `test_image_store.py` already imports `tempfile`.) Beware: a `_tree(tmp_path)` snapshot test will then see tempfile litter inside `tmp_path`; scope the snapshot to the cache dir plus victim paths, or give the fixture its own subdir (`tmp_path / "_tmp"`) and exclude it.

### `tests/test_tiled_generator.py` (new n_jobs=2 xfail test)

**Analog:** same file (docstring 1-20, imports 22-30, module has no fixtures; pure-object tests, one subprocess test at 59-70). Existing docstring states tests are "free of any joblib/loky process parallelism" -- update that sentence.
**Conventions found (measured):**
- `pyproject.toml:183-184`: `addopts = "--import-mode=importlib --strict-markers"`, `xfail_strict = false`. `[tool.pytest.ini_options]` registers NO custom `markers`. `xfail` is a builtin marker and needs no registration; `slow` / `loky` markers would NOT be accepted under `--strict-markers` unless a `markers = [...]` list is added to `[tool.pytest.ini_options]`.
- No `@pytest.mark.xfail(` decorator exists in tests today (earlier xfails were flipped; only docstrings mention them: test_feature_registry.py:9-11, test_manager.py:14-18, test_util.py:12). Closest convention: authored-xfail-first, `xfail_strict = false` so an XPASS (upstream fix) does not fail the suite. Use `strict=False` implicitly and a precise `raises`:
```python
@pytest.mark.xfail(
    reason="known limitation: GSEGUtils 0.6.0 writes every .dat via one <key>.dat.tmp; loky workers unpickling all tile stores race (see upstream issue #N)",
    raises=Exception,  # BrokenProcessPool / TerminatedWorkerError (joblib.externals.loky.process_executor)
)
def test_tiled_regenerate_n_jobs_2(tmp_path, synthetic_pcd): ...
```
- Build inputs with `synthetic_pcd` factory (`conftest.make_synthetic_pcd(n=..., seed=...)`, lines 100-149; fixture 152-163) and `PointCloudTile` tiles; `TiledPointCloudImageGenerator(pcd_tiles, ImgRes, "spherical", "linear", lazy_disk_cache_config=LazyDiskCacheConfig(enable_caching=True, cache_path=tmp_path))` (tiled_generator.py:104-122); call `generate(["range"], n_jobs=2)`, then 3-feature call, then `["range"]` again (RESEARCH repro: third call fails). Need >=2 tiles. Shipped text (test, reason string) must not say "phase 7"/IDs; reference only the issue number/URL.
- Because the failure is a race (11/12 upstream), `strict` xfail is wrong; keep non-strict.

### `pyproject.toml` (pins)

**Analog:** lines 33-37:
```toml
	"pchandler ~= 2.1",
	"GSEGUtils >= 0.5.3, < 1.0",
	"joblib ~= 1.5",
	"numpy ~= 2.0",
```
Target: `"pchandler >= 2.1.1, ~= 2.1"`, `"GSEGUtils ~= 0.6.0"`, `"numpy >= 2.2, < 2.4"`. Tab indentation. Update the stale comment block at lines 130-135 (mentions `GSEGUtils >= 0.5.3, < 1.0`). Then `uv lock && uv lock --check && uv sync`, then provenance check (RESEARCH lines 359-371). CLAUDE.md still says `numpy ~= 2.0`; the BC dep-constraint entry should mention the numpy floor move.

### Issue-body drafts (docs, phase dir)

No prior-phase draft analog (no `*draft*` file in Phase 6). Use plain markdown files in the phase dir (e.g. `07-UPSTREAM-ISSUE-DRAFT.md`, `07-TRACKING-ISSUE-DRAFT.md`) and `gh issue create --repo gseg-ethz/<repo> --title ... --body-file <file>`. Content source: RESEARCH "Surprise" section (traceback, 11/12 vs 0/12 repro, mechanism `_convert_to_memmap` -> `<key>.dat.tmp`, `_process_tile` bound-method pickling at tiled_generator.py:136, confirmation by intervention). Drafts live in `.planning/` (exempt from hygiene gate); the filed issue body should still read cleanly for outsiders.

### Owner checkpoint task that runs `gh` (plan structure)

**Analog:** `.planning/phases/06-publication-hardening-downstream-migration-record/06-12-PLAN.md`
- Owner-only account step, lines 70-86 (and 116-132):
```xml
<task type="checkpoint:human-action" gate="blocking">
  <name>Task N: Owner action — ...</name>
  <read_first>...</read_first>
  <action>...</action>
  <instructions>Already done by Claude: ... Please: ...</instructions>
  <verification>...</verification>
  <acceptance_criteria>...</acceptance_criteria>
  <resume-signal>Type "done" once ...</resume-signal>
</task>
```
- Claude-run `gh` step with automated verify, lines 88-114: `gh api --method PUT repos/gseg-ethz/pc2img/environments/testpypi`; verify `<automated>gh api repos/gseg-ethz/pc2img/environments --jq '.environments[].name' | grep -x testpypi</automated>` (line 99, 106).
- Other `gh` conventions: `gh issue list --repo gseg-ethz/pc2img --label ancestry-drift --state open --json number --jq length` (06-11-PLAN.md:143); `gh pr create --base ... --body ...` and `gh pr merge <n> --merge --delete-branch` (06-11:110). Pattern for the issue step: a `checkpoint:human-verify`/`human-action` where the owner approves the draft files, then an `auto` task runs `gh issue create --body-file`, with `<automated>gh issue view <n> --repo ... --json title --jq .title</automated>`; record the issue numbers/URLs (the xfail reason and BC entry reference them). Owner runs merges/POSTs per memory; do not have an agent file without the checkpoint.
- D-17 (PyPI trusted publisher + `pypi` environment) uses the same 06-12 Task 3 shape (tuple fields exact-match, RELEASE.md "Trusted publishing" table).

## Shared Patterns

### Shipped-text hygiene gate
**Source:** `tests/test_hygiene.py:165-195` (`_CODE_PATTERN`, `_PHASE_PLAN_PATTERN`). Applies to every git-tracked non-`.planning/` file incl. tests, docstrings, pyproject comments, xfail reasons: no `D-NN`, `BC-NN`, `DEP-NN`, `SC\d`, `review-rN-<hex>`, `phase N`, `gap-closure`, `this phase`, `.planning/`, `RESEARCH.md` etc. Cite upstream names (`StoreKeyError`, `purge`) and issue URLs instead.

### Lint / format
Ruff, line-length 120 (`pyproject.toml:147`); `tests/test_hygiene.py` shells `ruff check`/`format --check`. Run in every plan.

### Exception handling
Raise upstream exceptions unmodified; `ValueError` is pc2img's public contract (`StoreKeyError(ValueError)`, `StoreContainmentError(StoreKeyError)`). `purge` refusals are `RuntimeError`/`OSError` families (not `ValueError`).

### Provenance verification after any lock change
**Source:** RESEARCH lines 359-371 (assert `GSEGUtils.__version__ == "0.6.0"`, fingerprint `grep -c 'self\._get_npy_path' == 0`); D-03 unlocked-wheel recipe at RESEARCH 373-381 (run outside the repo; exclude `test_hygiene.py`, `test_git_archival.py`).

### Commit / branch convention
Functional conventional-commit scopes (`fix(store):`, `test(tiled):`, `build(deps):`), no planning IDs; work on a phase branch off `develop-gsd`; promotions via PR (merge commits, never squash on back-merge).

## No Analog Found

| File | Role | Reason |
|---|---|---|
| `uv.lock` | lock | generated |
| issue-body drafts | docs | no prior drafts in Phase 6; format is free-form markdown |
| `n_jobs>=2` loky test | test | no existing test uses `Parallel`/`n_jobs`/`xfail` marker; closest conventions above |

## Metadata

**Analog search scope:** `src/pc2img/image_cache/`, `src/pc2img/tiled_generator.py`, `tests/`, `pyproject.toml`, `.planning/phases/06-*`
**Not read in this pass (RESEARCH page 2, lines 442-692 not loaded; planner should read it for BC-entry material and release-path edit points):** `07-RESEARCH.md` tail, `MIGRATION-v0.11.md`, `.github/scripts/*`.
**Pattern extraction date:** 2026-10-01
