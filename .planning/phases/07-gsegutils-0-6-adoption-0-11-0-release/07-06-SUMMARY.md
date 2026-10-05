---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 06
subsystem: migration-record
tags: [migration-record, bc-entries, inline-verifier, gsegutils-0.6, known-limitation]

requires:
  - phase: 07-01
    provides: "the 0.6 pins, the re-locked environment and the thin DiskBackedImageStore the new entries describe (origin shas a69ca05, 1d1f9f2)"
  - phase: 07-02
    provides: "the whole-tree escape corpus and key-rule characterization (origin sha 8e6b0a5)"
  - phase: 07-03
    provides: "the two filed issue URLs and the xfail test BC-P2I-030 is written from (origin sha a7d593d)"
provides:
  - ".planning/MIGRATION-v0.11.md finalised at thirty entries (BC-P2I-001..030), target_ref v0.11.0, generated_at re-stamped"
  - "BC-P2I-002/012/017 amended so none of them states a 0.5-era fact that is false on the shipped pins"
  - "BC-P2I-026..030 appended (pin change, del vs purge, key/segment refusals, read-only store mapping, tiled re-generation known limitation)"
  - "inline verifier with Tier-2 probes for 026..029 and the StoreKeyError subtype pinned on 017; prints [ok] verified 30 entries on the locked 0.6.0 environment"
affects: [07-07 D-03 copy, 07-08 footer, 0.11.0 promotion, downstream iof3D reading the record from the branch]

actuals:
  tokens: 7710
  tasks: 2
  commits: 2
plan_head_before: 3ba2a171cd5bb31ff87a88b2656e3549428f6c46
plan_head_after: 19485ac4b4c17e5b353507fa5aab09f2e56784b7

tech-stack:
  added: []
  patterns:
    - "every new mechanical claim in the record gets a Tier-2 probe that fails when the claim is made false (checked by six single-line mutations of the extracted verifier)"
    - "known limitation recorded with the exception families taken from the committed xfail marker and both issue URLs read from the test file"

key-files:
  created: []
  modified:
    - .planning/MIGRATION-v0.11.md

key-decisions:
  - "BC-P2I-030 is classified dep-constraint / should-review: a user holding a reused tiled generator must act (fresh instance or n_jobs=1)"
  - "BC-P2I-029 (read-only store mapping) kept as signature-shape / should-review and cross-references BC-GSEG-007; BC-GSEG-006/007 and iof3D's handoff are cross-referenced, never restated"
  - "The summary's severity counts are derived from the final tables (20 should-review, 1 must-edit, 5 informational, 4 additive), not carried over from the plan's arithmetic"

requirements-completed: [BC-01]

coverage:
  - id: D1
    description: "Record finalised: target_ref v0.11.0, Target line names the tag, summary counts match the tables (30 entries), three stale entries amended"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "grep -c '^target_ref: \"v0.11.0\"$' -> 1; grep -c '^| BC-P2I-0\\(2[6-9]\\|30\\) |' -> 5; awk severity tally of the tables -> should-review 20, additive 4, informational 5, must-edit 1, total 30"
        status: pass
    human_judgment: false
  - id: D2
    description: "BC-P2I-030 names both exception families and both issue URLs, read from the committed xfail test; no placeholder token and no stale 0.5 claim survives"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "URL greps against tests/test_tiled_generator.py and the record (1/1); row-030 greps for BrokenProcessPool, FileNotFoundError, OSError (1/1/1); negative grep for the stale phrases and UPSTREAM_ISSUE_URL -> clean"
        status: pass
    human_judgment: false
  - id: D3
    description: "Inline verifier in sync (thirty ids, four new Tier-2 probes) and green on the locked environment"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "extracted _scrap/pc2img-migration-verifier.py -> '[ok] verified 30 entries'; ruff check --select E,F,W --ignore E501 -> All checks passed"
        status: pass
      - kind: other
        ref: "six single-line mutations of the extracted verifier each exit non-zero with the matching BC-P2I-NNN message"
        status: pass
    human_judgment: false
  - id: D4
    description: "Behavioural claims in the new entries reproduced by running code, not read"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "scratch probes on GSEGUtils 0.6.0 (exception MROs; del/pop/popitem/clear drop tracking only with the codec pair left and the key re-adopted; purge empties the directory; refused key corpus; read-only mappingproxy ops); scalar fields a/b, GPS:time, x. raise StoreKeyError at generate() on 0.6.0 and generate fine on 0.5.3 (pre-migration source overlaid on GSEGUtils 0.5.3)"
        status: pass
      - kind: e2e
        ref: "tests/test_tiled_generator.py -> 3 passed, 1 xfailed; pc2img-level repro BrokenProcessPool (RuntimeError) 2 of 2 rounds; controls reused n_jobs=1 and fresh-instance n_jobs=2 pass 3 of 3 rounds each"
        status: pass
    human_judgment: false

duration: ~12min
completed: 2026-10-02
status: complete
---

# Phase 7 Plan 06: Finalise the 0.11 migration record Summary

**`.planning/MIGRATION-v0.11.md` now describes 0.11.0 as it ships: three stale 0.5-era entries amended, five GSEGUtils 0.6 entries (pin change, `del` versus `purge`, key/segment refusals, read-only store mapping, tiled re-generation limitation) appended, the target stamped `v0.11.0`, and the inline verifier extended with runtime probes so it prints `[ok] verified 30 entries` on the locked 0.6.0 environment**

## Performance

- **Duration:** ~12 min (approximate; start time not captured)
- **Completed:** 2026-10-02
- **Tasks:** 2
- **Files modified:** 1 (`.planning/MIGRATION-v0.11.md`)

## Accomplishments

- Precondition checked before any edit: both issue URLs were present in `tests/test_tiled_generator.py` (GSEGUtils#82, pc2img#24) and `UPSTREAM_ISSUE_URL` counted 0.
- **Amended (Task 1, commit `9cd5c79`):**
  - BC-P2I-002 now states `pchandler >= 2.1.1, ~= 2.1`, `GSEGUtils ~= 0.6.0`, `numpy >= 2.2, < 2.4` and the trimmed cuda extras, and points to BC-P2I-026.
  - BC-P2I-012 keeps its history and points forward to BC-P2I-026.
  - BC-P2I-017 no longer claims nesting is allowed; it names `StoreKeyError`/`StoreContainmentError` (both `ValueError`) and every route.
- **Appended:** BC-P2I-026 (dep-constraint), -027 (semantic-change), -028 (error-behavior), -029 (signature-shape), -030 (dep-constraint), all `should-review`. Two Internal & sweep bullets added (deleted private overrides; `offload(features=...)` keyword name unchanged).
- **Verifier (Task 2, commit `19485ac`):** `BC_ENTRIES` carries thirty ids; new probes `_tier2_bc_p2i_026` (resolved GSEGUtils 0.6.x, pchandler >= 2.1.1, numpy >= 2.2, the 0.5.x private builder absent), `_027` (`del` leaves the codec pair and the key is re-adopted; `purge` removes both), `_028` (`StoreKeyError` for `a/b`, `GPS:time`, `x.`; `TIGSettings.extend_cache_paths("../x")` raises `ValueError`), `_029` (`store`/`image_data` are `MappingProxyType`, assignment raises `TypeError`); `_tier2_bc_p2i_017` now pins the `StoreKeyError` subtype. 030 has no runtime probe; its proof is the suite's xfail test, stated in a comment and in the module docstring.

## Verifier output

```
[ok] verified 30 entries
```

Final severity counts (derived from the tables): `should-review` 20, `must-edit` 1, `informational` 5, `additive` 4 (total 30). Categories: dep-constraint 8, error-behavior 6, semantic-change 5, additive-or-fixed 5, signature-shape 3, surface-removed 2, on-disk-format 1.

## Reproduced by running code

Scratch probes (in the gitignored `_scrap/`), all on the locked GSEGUtils 0.6.0 unless stated:

- Exception MROs: `StoreKeyError > ValueError`; `StoreContainmentError > StoreKeyError`; `StorePurgeRefusedError > RuntimeError`, `StorePurgeForeignArtefactError` below it; `StorePurgeIncompleteError > OSError`.
- `del`, `pop`, `popitem` and `clear` each leave `range.npy` and `range.meta.json` in place; the key is untracked, re-adopted by the next read, and tracked by a fresh store. `purge` leaves the directory empty and the key untracked. A re-add over a codec-offloaded key leaves only the new `range.dat`.
- Key corpus through `add_image_to_store`: `a/b`, `a\b`, `GPS:time`, `x.`, `x `, `''`, `.`, `..`, `CON`, `NUL`, `../x` raise `StoreKeyError`; `ok name` and `tile_03` are accepted.
- `.store` and `.image_data` are `mappingproxy`; `[]=` and `del` raise `TypeError`; `.pop`, `.clear`, `.update`, `.setdefault` raise `AttributeError`.
- Scalar-field names through a real `generate()`: `a/b`, `GPS:time`, `x.` raise `StoreKeyError` on 0.6.0; on GSEGUtils 0.5.3 (the pre-migration source at `49507b5` overlaid on GSEGUtils 0.5.3, scratch only) the same three generate and offload fine. `intensity` and `Scalar field` work on both.
- cuda extras: `pchandler` 2.1.1's own metadata lists `cudf-cu11/12`, `cuspatial-cu11/12`, `geopandas` and `numpy<2.3,>=2.2` under the cuda extras, which is what BC-P2I-002/026 state.
- Tiled limitation: the suite's xfail test reports XFAIL; the pc2img-level repro printed `BrokenProcessPool` (a `RuntimeError`) in 2 of 2 rounds; the two workarounds named in the entry (reused instance with `n_jobs=1`, fresh instance per call with `n_jobs=2` on a shared cache directory) passed 3 of 3 rounds each.
- Verifier sensitivity: six single-line mutations of the extracted verifier (purge instead of `del`; a legal key in the 028 probe; expecting GSEGUtils 0.5; a `dict` instead of `MappingProxyType`; the wrong exception in the 017 and 028 probes; a legal segment in the `extend_cache_paths` probe) each fail with the matching `BC-P2I-NNN` message. Against a 0.5.3 overlay the verifier exits non-zero (ImportError on the 0.6 names).

## Not measured (stated in the record)

A cache directory persisted by an older pc2img that holds a now-illegal key is expected to be left un-adopted rather than crash. This was not run and the record says so in BC-P2I-028.

## Task Commits

1. **Task 1: amend 002/012/017, append 026..030, re-stamp frontmatter and Summary** - `9cd5c79` `docs(migration)`
2. **Task 2: sync the inline verifier and run it green** - `19485ac` `docs(migration)`

**Plan metadata:** committed separately (docs: complete plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The record's original Summary miscounted `should-review` entries**
- **Found during:** Task 1 (re-deriving counts from the tables, as the plan instructed)
- **Issue:** The pre-existing Summary said sixteen `should-review` among twenty-five entries (16+1+5+4 = 26). The tables hold fifteen. The plan's own arithmetic suggested twenty-one after the additions, which would carry the error forward.
- **Fix:** Counts recomputed from the tables with an awk tally: twenty `should-review` (15 + the five new), one `must-edit`, five `informational`, four `additive`. The dominant-category sentence was also corrected (it said the bug-fix-pass entries dominated; `dep-constraint` has the most entries after the additions).
- **Files modified:** `.planning/MIGRATION-v0.11.md`
- **Commit:** `9cd5c79`

**2. [Rule 2 - Precision] Commit-message scope**
- The executor protocol's `{type}({phase}-{plan})` scope was replaced by the functional scope `migration`, because the project instructions forbid planning-ID tags in commit scopes.

**3. Wording nuance added to BC-P2I-027**
- The plan text says an offloaded key is re-adopted after `del`. The probe showed this holds for a key offloaded to the codec pair; a key that was never offloaded simply disappears. The entry now says "a key that was offloaded to [the codec pair]" instead of any offloaded key.

**Total deviations:** 1 auto-fixed bug, 1 convention-driven adjustment, 1 wording refinement. No scope change.

## Authentication Gates

None.

## Known Stubs

None.

## Threat Flags

None. The plan edits a planning record and its inline verifier; the verifier stays standalone (stdlib, numpy, GSEGUtils, pc2img; temp directories only; no network).

## Issues Encountered

- The research note put the verifier extraction/run command under `uv run --frozen`; `--frozen` ran fine here, and the other runs in this plan used `uv run --no-sync` as instructed.
- BC-P2I-026's rationale (a 0.6.0 minor withdrew private surface the old store wrapper called) rests on the 07-01 measurement of 30 failing tests on a plain 0.6.0 install of the old pins; that figure is not repeated in the record.

## Self-Check: PASSED

- `.planning/MIGRATION-v0.11.md` exists with `target_ref: "v0.11.0"`, five BC-P2I-026..030 rows, thirty `"id": "BC-P2I-0NN"` dicts and four registered Tier-2 probes (026..029).
- Commits `9cd5c79` and `19485ac` found in `git log`; `git rev-list --count 3ba2a17..HEAD` = 2 before this SUMMARY.
- All Task 1 and Task 2 `<automated>` checks re-run: pass. Full suite: 367 passed, 1 xfailed.

---
*Phase: 07-gsegutils-0-6-adoption-0-11-0-release*
*Completed: 2026-10-02*
