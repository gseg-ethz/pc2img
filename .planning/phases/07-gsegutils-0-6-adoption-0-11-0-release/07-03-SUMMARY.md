---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 03
subsystem: tiled-orchestration
tags: [gsegutils-0.6, loky, known-limitation, xfail, upstream-issue, store-key]

requires:
  - phase: 07-01
    provides: "pc2img migrated onto GSEGUtils 0.6.0 (the locked environment the race is reproduced on)"
provides:
  - "gseg-ethz/GSEGUtils#82: root-cause report (fixed <key>.dat.tmp name raced by processes unpickling one DiskBackedStore), with inlined minimal repro and suggested fix direction"
  - "gseg-ethz/pc2img#24: user-facing tracking issue (symptom, affected configuration, workaround, upstream link, close condition)"
  - "tests/test_tiled_generator.py: xfail(strict=False, raises=(RuntimeError, OSError)) regression test for repeated generate() on one instance with n_jobs=2, citing both issue URLs"
  - "tests/test_tiled_generator.py: TIGSettings.extend_cache_paths('../x') -> ValueError pinned at the settings surface"
affects: [07-06 migration record (entry built from these URLs), 07-08 footer]

actuals:
  tokens: 3555
  tasks: 3
  commits: 4
plan_head_before: 9f32564bf1a3754f53696285674dbe2e1c3aac62
plan_head_after: a7d593d51f32d1f71c55a885d72cfe222002aa4d

tech-stack:
  added: []
  patterns:
    - "known limitation pinned by a non-strict xfail whose raises= names every known manifestation family of one race (RuntimeError for loky pool errors, OSError for the worker's re-raised FileNotFoundError) and no third"

key-files:
  created:
    - .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-ISSUE-gsegutils-dat-tmp-race.md
    - .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-ISSUE-pc2img-tiled-regenerate.md
  modified:
    - tests/test_tiled_generator.py

key-decisions:
  - "Owner decision O-1 applied literally: raises=(RuntimeError, OSError), never narrowed to what three local rounds showed and never widened"
  - "Owner edit at the review gate: the SIGBUS claim in the upstream report is softened to an attributed earlier observation, because it was not reproduced in the latest session"
  - "Upstream issue filed first, then the real URL substituted into the tracking draft before it was filed, so no placeholder URL ever shipped"

patterns-established:
  - "Public issue drafts live in the phase directory, are committed as filed, and are checked against the shipped-text vocabulary regexes"

requirements-completed: [DEP-05]

status: complete
---

# Phase 07 Plan 03: Tiled re-generation race recorded as a known limitation Summary

The loky tiled re-generation race on GSEGUtils 0.6.0 is reproduced on the locked environment, filed upstream (GSEGUtils#82) and downstream (pc2img#24) after owner approval, cross-linked, and pinned in the suite by a non-strict xfail test citing both URLs; the traversing-folder refusal is pinned at the settings surface.

## Filed issues

| Repo | Number | URL | State | Label |
|------|--------|-----|-------|-------|
| gseg-ethz/GSEGUtils | 82 | https://github.com/gseg-ethz/GSEGUtils/issues/82 | OPEN | bug |
| gseg-ethz/pc2img | 24 | https://github.com/gseg-ethz/pc2img/issues/24 | OPEN | bug |

Each was filed exactly once (checked with `gh issue list` before filing; both read back with `gh issue view --json state,title,labels`). The `bug` label existed on both repositories and applied without fallback. The upstream issue carries a comment linking the tracking issue (https://github.com/gseg-ethz/GSEGUtils/issues/82#issuecomment-5949613949).

## Task 1 measurements (PyPI re-check and reproduction)

- PyPI latest GSEGUtils is still 0.6.0 (precondition met, no upstream fix).
- Upstream-only repro on the locked 0.6.0: 12 of 12 rounds with at least one failing child. Failures were `FileNotFoundError` on `<key>.dat.tmp`, plus one child that exited without a result.
- Same script on 0.5.3 (isolated `uv run --no-project --with GSEGUtils==0.5.3`): 0 of 12.
- Worker traceback: `DiskBackedStore.__setstate__` -> `_load_entry` -> `LazyDiskCache.__init__` -> `_init_from_config` -> `_convert_to_memmap` -> `os.chmod(tmp_path, destination_mode)` at `lazy_disk_cache.py:615`.
- SIGBUS was not reproduced in the latest session (research-only observation). The owner softened the upstream report's wording accordingly before filing.
- pc2img level (two tiles, `n_jobs=2`, three `generate()` calls on one instance, three rounds, run twice in Task 1): `BrokenProcessPool` every round (6 of 6), failing on call 2. The `OSError` family was not seen at the pc2img level.
- Controls: `n_jobs=1` on a reused instance passes three calls; a fresh instance per call with `n_jobs=2` and a shared cache directory passes three calls.

## pc2img-level reproduction (exception types)

Re-run at the close of this plan (`_scrap/tiled_regenerate_repro.py 3`, gitignored scratch script):

```
round 0: joblib.externals.loky.process_executor.BrokenProcessPool bases=RuntimeError
round 1: joblib.externals.loky.process_executor.BrokenProcessPool bases=RuntimeError
round 2: joblib.externals.loky.process_executor.BrokenProcessPool bases=RuntimeError
```

OBSERVED_TYPES: joblib.externals.loky.process_executor.BrokenProcessPool

The marker does not derive from this record; it is fixed to `(RuntimeError, OSError)` by owner decision O-1. The record is quoted in the test docstring and the tracking issue.

## Task outcomes

1. Task 1 (commit 1dcbeba): reproduction and both drafts, as above.
2. Task 2 (owner checkpoint): the owner reviewed both drafts in full and replied "soften the SIGBUS line in the summary, then file". The one-sentence edit was applied exactly as specified and committed (d0cc2a0) before any filing.
3. Task 3: upstream issue filed; `UPSTREAM_ISSUE_URL` replaced in the tracking draft (2fc366f); tracking issue filed; cross-link comment posted; tests landed (a7d593d).

## Verification results

- Test file run (`pytest tests/test_tiled_generator.py -rxX`): 3 passed, 1 xfailed. The regression test reports XFAIL (the race fired); it did not XPASS or fail.
- Full suite: 367 passed, 1 xfailed.
- The placeholder token count is 0 in both the tracking draft and the test file; `raises=(RuntimeError, OSError)` appears exactly once.
- Hygiene vocabulary gate (`-k planning_vocabulary`): 82 passed. `ruff check` and `ruff format --check` on `tests`: clean.
- The xfail test's final assertion (`(tile_id, "range") in result` for both tiles) was checked on the working path (`n_jobs=1`, same three-call sequence): keys are `ImageKey(tile_id=..., feature='range')` and the membership holds, so the assertion that must hold once upstream is fixed is correct rather than accidentally unreachable.
- Note: verify commands in the plan use `uv run --frozen`; the sequential-execution instruction for this run specified `uv run --no-sync`, which was used throughout.

## Deviations from Plan

None - plan executed as written. Two additions beyond the plan text, both within its intent: a separate small commit for the owner's SIGBUS edit (d0cc2a0, required by the owner's response), and a separate commit for the URL substitution in the tracking draft (2fc366f, so the draft in the tree shows what was filed before the tracking issue was created).

## Requirements note

BC-01 is deliberately left Pending: this plan produced the URLs the migration record needs, but the record entry itself lands in 07-06, which finalises BC-01.

## Known Stubs

None.

## Threat Flags

None. No new network surface in shipped code; the issue filings were the gated outward writes (T-07-09), and both bodies and the test module pass the vocabulary gates (T-07-08).

## Self-Check: PASSED

- Files present: both `07-ISSUE-*.md` drafts, `tests/test_tiled_generator.py`.
- Commits present: 1dcbeba, d0cc2a0, 2fc366f, a7d593d (4 commits measured from the plan head ledger).
- Issues OPEN with label bug: GSEGUtils#82, pc2img#24.
