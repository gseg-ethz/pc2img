---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 23
subsystem: tiled-generator-and-image-store-docs
tags: [gap-closure, round-5, docs-only, migration-record, known-limitations, conservative-wording, GSEGUtils-83]
status: complete

requires:
  - phase: 07-22
    provides: "round-4 docstrings and BC-P2I-027/030 whose measured safe-case wording this round replaces"
provides:
  - "tiled_generator.py: Known-limitations text states the failed-call retry hazard for any failed tiled generate() with caching enabled and gives only the timing-independent route; pc2img's link check in its own paragraph; sidecar inheritance with 'may' (docstring-only, AST-identical)"
  - "disk_backed_image_store.py: dangling-link-uncleared claim removed; held-entry caveat stated generally; 'every successful call' (docstring-only, AST-identical)"
  - "tests/test_tiled_generator.py: armed-entries docstring no longer attributes the disarm gap to upstream (docstring-only, AST-identical)"
  - "MIGRATION-v0.11.md BC-P2I-030 and BC-P2I-027 carry the same conservative guidance; thirty entries; verifier green"
affects: [07-07 resume needs a new D03_SHA line (shipped files changed); a final reading-check review of this docs-only diff is an orchestrator/owner step before 07-07 resumes]

actuals:
  tokens: 9000
  tasks: 2
  commits: 2
plan_head_before: c43d6f0725ce29de15458859dacaaac1ab43ef75
plan_head_after: f6ec61a988637a2d26af7dd437ae6aed8905e291

tech-stack:
  added: []
  patterns:
    - "docs-only round: every touched .py file proven identical to HEAD with docstrings stripped from its AST"
    - "known-limitations text written as recommendations and 'may' statements, never as a list of configurations claimed safe"

key-files:
  created: []
  modified:
    - src/pc2img/tiled_generator.py
    - src/pc2img/image_cache/disk_backed_image_store.py
    - tests/test_tiled_generator.py
    - .planning/MIGRATION-v0.11.md

key-decisions:
  - "The shipped text names no configuration (n_jobs, cache_path, call history) as free of the failed-call retry hazard; the only stated non-hazard is the plain fact that the default enable_caching=False writes nothing to disk"
  - "Held entries taken from tile stores are advised against across a regenerate without the narrower 'after a pooled call' precondition (G4-WR-01)"
  - "pc2img's pre-write link check is described in its own paragraph, outside the GSEGUtils#83 heading, and marked as pc2img's own and to be revisited in 0.11.1 (G4-WR-02)"
  - "No new measurements were added to the shipped text; the figures cited below are the round-5 reviewer's, not re-measured here"

requirements-completed: []

coverage:
  - id: D1
    description: "Tiled and store docstrings carry the conservative failed-call guidance; docs-only proven by AST identity for all three .py files"
    requirement: "DEP-05"
    verification:
      - kind: other
        ref: "uv run --no-sync python (docstring-stripped AST compare of the three files against git HEAD) -> ast-identical"
        status: pass
      - kind: other
        ref: "grep stale-claim check from the plan (did not lose|lost nothing|cannot be cleared through|returns...) -> no-stale-claims"
        status: pass
    human_judgment: true
    rationale: "Whether the wording is accurate and claims no configuration safe needs a reader; the plan routes this diff to a final reading-check review"
  - id: D2
    description: "BC-P2I-030 and BC-P2I-027 match the docstrings; thirty entries; inline verifier green"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "awk-extracted inline verifier in .planning/MIGRATION-v0.11.md run with uv run --frozen -> [ok] verified 30 entries"
        status: pass
    human_judgment: true
    rationale: "The verifier checks structure and probes, not prose accuracy; the wording needs the reading-check review"
  - id: D3
    description: "Full suite still passes after the docstring edits"
    verification:
      - kind: unit
        ref: "uv run --no-sync pytest -q -p no:cacheprovider -> 403 passed"
        status: pass
    human_judgment: false
---

# Phase 7 Plan 23: Docs-only gap round 5 (conservative known-limitations wording) Summary

**Docstring-only (AST-identical) replacement of the round-4 measured safe-case limitation text with recommendation-and-"may" guidance for any failed tiled `generate()` call, mirrored in BC-P2I-030 and BC-P2I-027, with pc2img's own link check split out from the GSEGUtils#83 heading.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-10-05T10:53:02Z
- **Completed:** 2026-10-05T11:01:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- The tiled class docstring's Known limitations now say that, with caching enabled, a retry after any failed `generate()` call may lose its files, whatever `n_jobs`, `cache_path` or call history. The only routes given hold regardless of garbage-collection timing: do not retry inside the `except` block (and do not rely on `gc.collect()` there); let the exception go out of scope, call `gc.collect()`, then retry; or retry with a fresh `TiledPointCloudImageGenerator` over a fresh `cache_path`. Holding entries taken from tile stores across a regenerate is advised against generally (G4-CR-01, G4-CR-02, G4-WR-01).
- pc2img's own pre-write link check (aliased/foreign classification by link location, adopted-payload and dangling links refused, a symlink loop raising a bare `RuntimeError`) has its own paragraph, marked pc2img's own and to be revisited in 0.11.1. The test docstring no longer calls the armed entries an upstream limitation: the disarm runs only after a successful call, and the deletion that allows is GSEGUtils#83 (G4-WR-02).
- Sidecar inheritance is a "may" statement: after tiled runs a key's `.meta.json` may record `purge_disk_on_gc=False`, which later stores over the same directory inherit; no per-call rule (G4-WR-03).
- The claim that a dangling `<key>.dat` link cannot be cleared through `purge` is gone from every site (the tiled class, the store module docstring, the `_refuse_linked_write_path` docstring, `add_image_to_store`, BC-P2I-027 and BC-P2I-030) (G4-IN-01). "Only after a call returns" now reads "returns successfully", and "every call" in the store docstring and BC-P2I-027 reads "every successful call" (G4-IN-02).
- BC-P2I-030 (Known limitations, sidecar sentence, failed-batch tail) and BC-P2I-027 (non-owner caveat, link refusal) carry the same guidance. Thirty rows, `target_ref` unchanged, `generated_at` re-stamped, verifier prints `[ok] verified 30 entries`.

## Task Commits

1. **Task 1: Conservative wording in the tiled and store docstrings** - `485ba9e` (docs(tiled))
2. **Task 2: Conservative wording in BC-P2I-030 and BC-P2I-027** - `f6ec61a` (docs(migration))

**Plan metadata:** committed with this SUMMARY (docs(07-23): complete conservative known-limitations wording plan).

The plan's functional scope list also named `docs(image_store)`; the store-docstring edits shipped in the single Task 1 commit under `docs(tiled)` because the three `.py` files form one atomic docstring change proven together by one AST check.

## Files Created/Modified

- `src/pc2img/tiled_generator.py` - class docstring (sidecar paragraph, failed-batch tail, Known limitations split into upstream-rooted and pc2img's own link check) and `generate()` docstring; docstring-only
- `src/pc2img/image_cache/disk_backed_image_store.py` - `_refuse_linked_write_path`, class and `add_image_to_store` docstrings; docstring-only
- `tests/test_tiled_generator.py` - three docstring sentences (armed-entries attribution; two bare "returns" phrasings); docstring-only
- `.planning/MIGRATION-v0.11.md` - BC-P2I-027 and BC-P2I-030 rows; `generated_at`

## Decisions Made

See `key-decisions`. In short: no configuration is called safe anywhere in shipped text; no measurement was added to shipped text.

## Docs-only proof

Docstring-stripped AST of `src/pc2img/tiled_generator.py`, `src/pc2img/image_cache/disk_backed_image_store.py` and `tests/test_tiled_generator.py` compared against `git show HEAD:<file>` (HEAD = `c43d6f0`, the plan base): `ast-identical`, run before the Task 1 commit and again after the last wording edit. The `except`-handler code comment in `generate()` was left as it was. Full suite: `403 passed`. Verifier: `[ok] verified 30 entries`.

## Measurements recorded here, not in shipped text

Not re-measured in this run. The round-5 reading check (`07-REVIEW-GAP4.md`, scripts in its scratchpad `gap4/`) reported, with caching and a `cache_path`:

- retry inside the `except` block after a failing `n_jobs=1` first call: lost files in every run at retry `n_jobs=1, 2, -1`;
- failing pooled first call, retry inside the block: intermittent losses (2/12, 4/8, 2/16 runs);
- `gc.collect()` inside the `except` block: lost 3/3; after leaving the block, then retry: clean 3/3 and 6/6 across the tested shapes;
- fresh generator over a fresh `cache_path`: clean in the reviewer's runs;
- a held entry across a regenerate lost the replacement `.dat` after a prior pooled call and not with an all-sequential history (2/2 each); the shipped text does not use that narrower condition;
- `enable_caching=False`: no lost files in 8 of 8 runs.

These are why the shipped text is deliberately conservative: pooled failures and every retry `n_jobs` lose files intermittently, so no enumeration of safe shapes can be made reliable from sampling.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded benign "returns ..." phrasings so the plan's stale-claim grep passes**
- **Found during:** Task 1 verification
- **Issue:** The plan's second `<automated>` check pattern `returns,? +[a-z]` also matches unrelated docstring lines ("returns parent-side", "returns rasters", "it returns on every ...") that contain no stale claim, so the check could not print `no-stale-claims`.
- **Fix:** Reworded those phrases ("hands back", "gives", "entries of every successful call", "entries returned by a successful ... call") in docstrings only. No code and no claim changed.
- **Files modified:** `src/pc2img/tiled_generator.py` (`_release_gc_ownership` docstring), `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_tiled_generator.py`
- **Verification:** AST identity re-run (`ast-identical`); the grep prints nothing and `no-stale-claims` appears; suite 403 passed.
- **Committed in:** `485ba9e`

**2. [Rule 1 - Bug] "disarms the entries it returns on every call" was inaccurate**
- **Found during:** Task 1 (store docstring) and Task 2 (BC-P2I-027, "Disk persistence" in BC-P2I-030)
- **Issue:** The disarm runs only after a successful call, so "every call" contradicted the failed-call text in the same paragraph.
- **Fix:** "every successful call" / "Every successful `generate()` call" in the store docstring, BC-P2I-027 and BC-P2I-030.
- **Committed in:** `485ba9e`, `f6ec61a`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug), both wording-only.
**Impact on plan:** None on scope; no behaviour change.

## Issues Encountered

None. The only worktree-state notes: `.planning/config.json` was already modified before this plan and was left alone, and `_scrap/pc2img-migration-verifier.py` is gitignored.

## Known Stubs

None.

## Threat Flags

None. Docs-only; no new network, auth, file-access or schema surface. T-07-71 is mitigated: the shipped text contains recommendations and "may" statements only.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The diff of this round needs the final reading-check review named in the plan (`/gsd-code-review 7 --files` the three `.py` files, plus `/code-review <round base> high`) before 07-07 resumes; 07-07 Tasks 1-2 then re-run with a new `D03_SHA` line because the shipped files changed. 07-07, 07-15 and 07-07..07-11 were not touched.
- UAT statuses and requirements were not changed (`DEP-05` and `BC-01` stay open).

## Self-Check: PASSED

- Files present: `src/pc2img/tiled_generator.py`, `src/pc2img/image_cache/disk_backed_image_store.py`, `tests/test_tiled_generator.py`, `.planning/MIGRATION-v0.11.md`.
- Commits present: `485ba9e`, `f6ec61a`. `git rev-list --count c43d6f0..HEAD` = 2 at SUMMARY write.
- Plan acceptance criteria re-run: AST identity, no stale claims (docstrings and record), `gc.collect()` and `except` counts non-zero (2 and 4), 30 rows, `[ok] verified 30 entries`, 403 tests passed.

---
*Phase: 07-gsegutils-0-6-adoption-0-11-0-release*
*Completed: 2026-10-05*
