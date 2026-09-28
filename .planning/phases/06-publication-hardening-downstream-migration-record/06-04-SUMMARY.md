---
phase: 06-publication-hardening-downstream-migration-record
plan: 04
subsystem: docs
tags: [migration-record, breaking-changes, downstream-migration, verifier, ast, inspect]

# Dependency graph
requires:
  - phase: 05-bug-fixes-module-test-coverage
    provides: the 17-entry 05-BC-NOTES.md running note of Phase-5 public-API/behavior changes
provides:
  - MIGRATION-v0.11.md at the repo root, draft half of BC-01, in PCHandler's migration-spec format
  - A standalone, extractable inline Python verifier proving every surface-removed / signature-shape
    claim at runtime against the installed package
affects: [06-05, 06-06, 06-07, 06-08, 06-09, 06-10, 06-11, 06-12, 06-13, "Phase 7 (finalizes the record, appends GSEGUtils 0.6 entries, re-stamps target to v0.11.0)"]

# Actuals (#2632)
actuals:
  tokens: 8910
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns: [migration-spec format (frontmatter + 6 sections + inline extractable verifier), Tier-1 AST-walk of __all__ barrels + Tier-2 runtime getattr/inspect.signature probes, pin exception types by running the constructor rather than reading the source]

key-files:
  created:
    - MIGRATION-v0.11.md
  modified: []

key-decisions:
  - "BC-P2I-001 stays fixed as the tracer entry (registry-error unification, from the Phase-5 bug-fix pass); all later entries were numbered 002-025 in phase-of-origin order (dependency adaptation, hygiene review, bug-fix pass, gap-closure pass, publication pass), not renumbered retroactively"
  - "Entry 3 from 05-BC-NOTES.md (nanconv float16->float32 fix + compute_dtype opt-in) split into two BC-P2I rows by severity: BC-P2I-009 (should-review correctness fix) and BC-P2I-023 (additive opt-in param) — same rule PCHandler's own record documents (one entry per observable downstream effect)"
  - "Entries 5, 6 and 17 from 05-BC-NOTES.md (Hillshade aspect documentation, Delaunay culling kwargs, DiskBackedImageStore config-default sentinel) landed as Internal & sweep bullets, not table rows, per the plan's explicit read_first instruction — even though 05-BC-NOTES.md's own summary table marks entry 6 ADDITIVE, since their defaults are byte-identical and no public-surface actually changed for any existing caller"
  - "GSEGUtils's BC-GSEG-006 (store-key containment contract) is cross-referenced from BC-P2I-012, not restated — the two exception types (PerspectiveProjection 4x4 rotation -> TypeError; non-pinhole K -> ValueError) were pinned by running the constructor once and observing, not by reading the source, per the project's reproduce-don't-read rule"
  - "All origin cells were reworded during Task 3 to drop bare 'Phase N' phrasing (found by the vocabulary regex) in favor of plain-words causes (bug-fix pass, gap-closure pass, dependency adaptation, hygiene review, publication pass, consolidation of the 2.x branches) so the file reads as a public document"

patterns-established:
  - "A migration record's inline verifier splits BC-ID-keyed checks (TIER2_CHECKS, required for every surface-removed/signature-shape row) from unkeyed GENERAL_CHECKS for Internal & sweep items that carry no BC-ID"
  - "Root-guard pattern for a standalone extracted script: assert pyproject.toml with the expected `name = \"...\"` line exists in cwd before importing the package, so a wrong-directory run fails loudly instead of silently importing an unrelated installed package"

requirements-completed: [BC-01]

coverage:
  - id: D1
    description: "MIGRATION-v0.11.md exists at the repo root in PCHandler's migration-spec format: frontmatter type/spec_version/repo/baseline_ref/target_ref/generated_at/bc_id_prefix/milestone, six required section headings in order"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "PyYAML frontmatter assertion (bc_id_prefix=BC-P2I, baseline_ref=91b4ab6, repo=pc2img, type=migration-spec, target_ref matches [0-9a-f]{40}) — printed frontmatter-ok"
        status: pass
      - kind: other
        ref: "grep -n '^## ' MIGRATION-v0.11.md lists exactly Summary / Public API stability statement / Breaking changes & behavior changes / Additive changes / Internal & sweep changes / Verifier (inline), in order"
        status: pass
    human_judgment: false
  - id: D2
    description: "All 17 Phase-5 breaking-change notes transcribed (aggregated one entry per observable effect), plus earlier-milestone additions and this phase's own entries; 25 total rows, ids unique and monotonic, GSEGUtils's BC-GSEG-006 cross-referenced rather than restated"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "ROWS=25 (>= 22 required), DUPS=0; diff between table ids and verifier BC_ENTRIES ids is empty"
        status: pass
      - kind: other
        ref: "grep -c 'BC-GSEG-006' MIGRATION-v0.11.md == 1; grep -c 'must-edit' >= 1; grep -c 'surface-removed' >= 2; grep -c 'pc2img ~= 0.11' >= 1; Internal & sweep list has 5 bullets"
        status: pass
    human_judgment: false
  - id: D3
    description: "The inline verifier extracts and runs standalone from the repo root: Tier 1 AST-walks the four __init__.py __all__ lists, Tier 2 runtime-checks every surface-removed/signature-shape claim (getattr/inspect.signature/behaviour probes with observed, not guessed, exception types) and exits 0"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "awk/sed extraction + uv run --frozen python /tmp/pc2img-migration-verifier.py -> '[ok] verified 25 entries', exit 0"
        status: pass
      - kind: other
        ref: "Every surface-removed/signature-shape id (BC-P2I-004, 005, 008, 015) appears >=2x in the extracted script (once in BC_ENTRIES, once as a TIER2_CHECKS key); grep -cE 'inspect\\.signature|getattr\\(' == 7 (>=5 required)"
        status: pass
      - kind: other
        ref: "Root guard: uv run --frozen --project /scratch/31_pc2img (cwd /tmp) and bare python3 from /tmp both exit 1 with '[fail] cannot find a pc2img repository root'"
        status: pass
    human_judgment: false
  - id: D4
    description: "BC-P2I ids are unique and strictly monotonic (zero-padded to 3 digits); the verifier exits non-zero when its entry list is empty or a surface-removed entry names no symbol"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "Emptying BC_ENTRIES in a copy of the extracted verifier and running it: '[fail] BC_ENTRIES is empty — an empty record is a failure, never a vacuous pass', exit 1"
        status: pass
    human_judgment: false
  - id: D5
    description: "The file contains no planning vocabulary: origins cite commit shas and plain-words descriptions, never decision/requirement/phase ids"
    requirement: "BC-01"
    verification:
      - kind: other
        ref: "vocab-clean regex scan (BUG/DSN/QUAL/TEST/DEP/CICD/BC/PERF/BRANCH-N, M-N, D-N, T-NN-NN, SCN, .planning/, review-rN-<sha>, RESEARCH/CONTEXT/SUMMARY/VERIFICATION/UAT.md, phase-N references) printed vocab-clean"
        status: pass
    human_judgment: false

# Metrics
duration: 55min
completed: 2026-09-28
status: complete
---

# Phase 6 Plan 4: MIGRATION-v0.11.md draft (BC-01) Summary

**Drafted `MIGRATION-v0.11.md` — a 25-entry, publication-clean downstream migration record covering Phases 1-6 in PCHandler's migration-spec format, with a standalone inline verifier that mechanically proves every surface-removed/signature-shape claim (Tier 1 AST-walk of the four public `__init__.py` barrels + Tier 2 runtime `getattr`/`inspect.signature`/behaviour probes) against the installed package.**

## Performance

- **Duration:** ~55 min
- **Tasks:** 3 completed
- **Files modified:** 1 created (`MIGRATION-v0.11.md`)

## Accomplishments

- `MIGRATION-v0.11.md` carries the full migration-spec frontmatter (`type: migration-spec`,
  `baseline_ref: 91b4ab6`, `target_ref` = the full `origin/develop-gsd` HEAD sha
  `e9eb3c48354a73e294c0aff8718fac562215d958`, `bc_id_prefix: BC-P2I`, `milestone: v1.0`) and all six
  required sections in order.
- 25 `BC-P2I-NNN` rows (21 in "Breaking changes & behavior changes", 4 in "Additive changes"), ids
  unique and strictly monotonic, sourced from all 17 `05-BC-NOTES.md` entries plus earlier-milestone
  additions (`make_generator` removal, duplicate `convert_to_image` removal, `PerspectiveProjection`
  registration, the `viz` extra, dependency pins, the pchandler-2.x zero-call-site attestation) and
  this phase's own forward-looking entries (tag retirement, PyPI availability, README/CITATION
  metadata).
- An inline Python verifier (Tier 1 AST-walk of `src/pc2img/{__init__,features/__init__,
  strategies/__init__,image_cache/__init__}.py`'s `__all__` lists; Tier 2 runtime checks) extracts
  standalone via the documented `awk`/`sed` command and exits 0, printing `[ok] verified 25 entries`.
- Every `surface-removed`/`signature-shape` row (`BC-P2I-004`, `005`, `008`, `015`) has a dedicated
  Tier-2 runtime check; the two `PerspectiveProjection` exception types were **pinned by running the
  constructor once**, not guessed from reading: a 4×4 `rotation_matrix` raises `TypeError`, a
  non-pinhole `K` (bottom row ≠ `[0, 0, 1]`) raises `ValueError`.
- `GSEGUtils`'s `BC-GSEG-006` (store-key containment contract) is cross-referenced from
  `BC-P2I-012` rather than restated, per the plan's explicit instruction.
- The file is publication-clean: a vocabulary regex scan for planning IDs, decision/requirement/
  phase references and `.planning/` paths returns `vocab-clean`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Skeleton + verifier scaffold + ONE entry proven end to end** - `a4f995e` (docs)
2. **Task 2: Transcribe the full entry inventory** - `8c1b3c7` (docs)
3. **Task 3: Complete Tier-2 runtime checks; vocabulary check** - `457620f` (docs)

**Plan metadata:** (this commit)

## Files Created/Modified

- `MIGRATION-v0.11.md` - The draft BC-01 downstream migration record: frontmatter, six sections,
  25 `BC-P2I-NNN` entries, and a standalone inline verifier (675 lines total).

## Decisions Made

- `BC-P2I-001` stayed fixed as the tracer entry; all later ids (002-025) were assigned in
  phase-of-origin order rather than renumbered retroactively around it.
- 05-BC-NOTES.md's entry 3 (nanconv) was split by severity into `BC-P2I-009` (should-review
  correctness fix) and `BC-P2I-023` (additive opt-in param) — matching PCHandler's own aggregation
  rule ("one entry per observable downstream effect").
- Entries 5, 6 and 17 from 05-BC-NOTES.md landed as Internal & sweep bullets rather than table rows
  (per the plan's explicit `read_first` instruction), even though 05-BC-NOTES.md's own summary table
  marks entry 6 `ADDITIVE` — their defaults are byte-identical and no public-surface change is
  observable for any existing caller.
- Both `PerspectiveProjection` exception types (`BC-P2I-008`, `BC-P2I-015`) were confirmed by
  instantiating the class with the failing inputs before writing the Tier-2 check, per the project's
  "reproduce, don't read" rule — the observed types (`TypeError`, `ValueError`) matched what the
  source docstring/code implied, but the check pins the *observed* value.
- All origin cells were reworded during Task 3 to remove bare "Phase N" phrasing caught by the
  vocabulary regex, replaced with plain-words causes (`bug-fix pass`, `gap-closure pass`,
  `dependency adaptation`, `hygiene review`, `publication pass`, `consolidation of the 2.x branches`).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The first full-file draft (after Task 2) still contained bare "Phase N" references in origin
  cells and Internal & sweep bullets (`[bug-fix pass, Phase 5]:` etc.), which the Task 3 vocabulary
  regex correctly flagged. Fixed by rewording every occurrence to a plain-words cause with no phase
  number, then re-ran the full vocabulary scan to confirm `vocab-clean`. Not logged as a deviation
  (it is exactly the fix Task 3's own `<action>` instructs — "Fix any hit by rewording").

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `MIGRATION-v0.11.md` exists at the repo root, verifier-proven, and publication-clean — ready to
  ship to public `main` at the first filtered promotion (plans 06-05..06-13 handle CI/CD assembly,
  hygiene, and the promotion itself).
- The record is explicitly a **draft**: `target_ref` is `origin/develop-gsd` HEAD at draft time, not
  a release tag. Phase 7 finalizes it — appends the GSEGUtils 0.6 entries, re-stamps `target_ref` to
  the `v0.11.0` release, and re-runs the inline verifier (D-29).
- Whole-tree gates re-verified clean after this plan: `uv run --frozen pytest -q` (255 passed) and
  `uvx pre-commit run --all-files` (ruff check/format + hygiene hooks all Passed).

---
*Phase: 06-publication-hardening-downstream-migration-record*
*Completed: 2026-09-28*

## Self-Check: PASSED

- FOUND: MIGRATION-v0.11.md (675 lines, contains `bc_id_prefix: BC-P2I`)
- FOUND commit a4f995e in git log
- FOUND commit 8c1b3c7 in git log
- FOUND commit 457620f in git log
- Re-ran plan-level `<verification>`: extraction + `uv run --frozen python` -> `[ok] verified 25 entries`, exit 0; `ROWS=25 DUPS=0`, every table id mirrored in `BC_ENTRIES`; vocabulary regex scan -> `vocab-clean`
- `must_haves.truths` (from plan frontmatter) re-checked: frontmatter fields correct (yes); all 17
  Phase-5 notes + earlier/this-phase entries transcribed with categories/severities as specified
  (yes); GSEGUtils cross-referenced not restated (yes); verifier extracts and runs standalone,
  Tier 1 + Tier 2, exits 0 (yes); ids unique/monotonic (yes); empty-entry-list guard has teeth (yes,
  demonstrated by emptying `BC_ENTRIES` in a copy and observing exit 1); no planning vocabulary
  (yes, `vocab-clean`)
