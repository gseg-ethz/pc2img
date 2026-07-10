---
phase: 04-code-quality-algorithmic-soundness-review
plan: 07
subsystem: review / synthesis + phase gate (QUAL-02 + QUAL-03)
tags: [review, findings, synthesis, phase-gate, QUAL-02, QUAL-03, wave-4]
requires:
  - "04-05 (04-FINDINGS-design.md: DSN-01..DSN-11 + DSN-F1, refuted design findings)"
  - "04-06 (04-FINDINGS-math.md: M-01..M-13, refuted numeric-probed math findings)"
provides:
  - "04-FINDINGS.md (single canonical, schema-valid, most-severe-first findings log)"
  - "the Phase-5 BUG-05 feeder (D-06/D-07): 24 active findings + 1 FIXED anchor"
affects:
  - "Phase 5 (BUG-05 fixes-with-proving-tests: M-01..M-13 + DSN-01..DSN-11 are the specified inputs)"
tech-stack:
  added: []
  patterns:
    - "single canonical FINDINGS artifact stands alone; design/math/candidate fragments retained beside it as FIND/REFUTE evidence (D-05)"
    - "per-entry schema-lint: each finding is a **id:**-anchored block carrying all eight D-06 labels + a file.py:line anchor (whole-file grep is insufficient)"
    - "stable M-*/DSN-* ids carried verbatim; named legacy bugs cross-referenced inline (BUG-01=M-01, BUG-02=DSN-02, BUG-03=DSN-01, BUG-04=E402/rrim)"
key-files:
  created:
    - ".planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS.md"
  modified: []
decisions:
  - "BUG-01 recorded ONCE as M-01 (math-track confirmation of the design 'project/project_raw arity mismatch' anti-pattern), cross-referenced, not duplicated into a separate DSN entry"
  - "DSN-02/BUG-02 entry states BOTH the historically-observed TypeError (old `raise NotImplemented` singleton) AND the currently-observed NotImplementedError (04-04 F901 fix b478a34); Phase-5 proving test asserts NotImplementedError, NOT TypeError"
  - "Four design anchors present-or-fixed: #1 make_generator FIXED-with-smoke (04-03), #2 divergent registries DSN-05, #3 in-place raster mutation DSN-03, #4 dependency-cycle guard DSN-08 (LOW/latent)"
  - "Pickle-load T-04-J carried as DSN-09 surfaced-and-logged (trust boundary = process-local tempfile.mkdtemp); satisfies ASVS L1 block_on:high by logging"
  - "No per-finding BUG-05.N ids minted and no GSD todos created (D-07) — the file itself is the feeder"
metrics:
  duration: 9min
  completed: 2026-07-10
status: complete
---

# Phase 04 Plan 07: Synthesis + Phase Gate Summary

Merged the design half (`04-FINDINGS-design.md`, DSN-01..DSN-11 + DSN-F1) and the math half
(`04-FINDINGS-math.md`, M-01..M-13) into the single canonical `04-FINDINGS.md` — deduped,
most-severe-first, and schema-linted so **every** id-anchored entry (not just the file as a whole)
carries all eight D-06 fields plus a live `file.py:line` anchor. This is the one deliverable the
whole phase exists to produce: the Phase-5 BUG-05 work-list of fixes-with-proving-tests (D-06/D-07).

## What was built

- **`04-FINDINGS.md`** — 24 active findings (**4 HIGH · 1 MED-HIGH · 10 MED · 2 LOW-MED · 7 LOW**)
  plus 1 FIXED anchor, ordered most-severe-first, each written as a `**id:**`-anchored section with
  the eight canonical labels (`id`, `location`, `defect`, `why-wrong`, `repro`, `severity`,
  `pillar`, `proving-test`). Includes a FIXED section, a deferred-ruff/hygiene breadcrumb list, a
  CONFIRMED-CORRECT (do-not-re-open) list, and a most-severe-first summary table.

### Cross-track reconciliation (the point of the synthesis)

- **BUG-01 appears once.** Logged as **M-01** (math track), explicitly cross-referenced as the
  math-track confirmation of the design anti-pattern "`project()` / `project_raw()` return-arity
  mismatch". No duplicate DSN entry was minted.
- **BUG-02 exception-type reconciled.** The **DSN-02** entry states the historically-observed
  `TypeError` (the old `raise NotImplemented` singleton is not a `BaseException`) **and** the
  currently-observed `NotImplementedError` (04-04 ruff F901 autofix, commit `b478a34`), and flags
  that the Phase-5 proving test must assert `NotImplementedError` — the live defect is that the
  whole `NDArrayOperatorsMixin` arithmetic surface is dead, independent of the exception type.
- **Deferred ruff items carried as Phase-5 breadcrumbs:** E402×9 → **BUG-04** (rrim), C901×5
  complexity, B008×4 = **DSN-07** (seed E mutable default).

### Four required anchors (all present-or-fixed)

| Anchor | Entry | Disposition |
|--------|-------|-------------|
| #1 broken `make_generator` | DSN-F1 | **FIXED-with-smoke** in 04-03 (deleted, zero callers) |
| #2 divergent registries | DSN-05 | LOG (KeyError vs RuntimeError; side-effectful `match()`) |
| #3 in-place raster mutation | DSN-03 | LOG (masked today by `__array__` copy) |
| #4 dependency-cycle guard | DSN-08 | LOG, LOW/latent (no current feature graph can cycle) |

Security: **DSN-09** carries the pickle-load surface (STRIDE **T-04-J**, Tampering/RCE, high,
disposition=mitigate/log) with its trust boundary (process-local `tempfile.mkdtemp` cache dirs) —
satisfying the ASVS L1 `block_on:high` gate by surfacing-and-logging.

## Deviations from Plan

### Auto-fixed (Rule 1 — corrections to make the acceptance checks pass on the real interpreter)

- **[Rule 1 — broken verify command] Task-2 linter regex does not compile on Python ≥3.11.** The
  plan's verbatim linter uses `re.split(r'(?im)^#+\s*(?=id[:\s])|(?im)^(?=\*\*?id\b)', ...)` — a
  second `(?im)` inline flag mid-pattern. Confirmed to raise `re.error: global flags not at the
  start of the expression` on **both** the miniconda Python 3.13 and the project `.venv` Python
  3.12.13. I validated the artifact with the **semantically-identical** corrected regex (the single
  `(?im)` hoisted to the front — inline flags apply to the whole pattern regardless of position):
  `re.split(r'(?im)^#+\s*(?=id[:\s])|^(?=\*\*?id\b)', ...)`. Result: **24 findings, all 8 fields +
  anchor present.** Phase 5 / the verifier should use the hoisted-flag form.
- **[Rule 1 — verify collision in prose] Removed the literal `BUG-05.x` token from the header.** The
  Task-1 guard `! grep -q "BUG-05\."` (correctly enforcing D-07: no per-finding `BUG-05.N` ids) also
  matched my *descriptive* mention of "`BUG-05.x`" in the intro. Reworded to "BUG-05 sub-numbered
  requirement ids" so the guard passes and the D-07 intent is still stated. No finding uses a
  `BUG-05.N` id.
- **[Rule 1 — schema-linter false block] Reworded the intro schema sentence.** The per-entry linter
  splits on `**id`-lines and then filters blocks containing both the word `id` and `severity`; my
  intro listed a bare `` `id` `` label alongside "severity", so the header paragraph was mis-parsed
  as a finding block lacking a `.py:line` anchor. Reworded the eight-label enumeration to "an
  identifier, then a `location` …" (no standalone `id` token) so the header is no longer treated as
  an entry. All 24 real entries lint clean.

No source edits and no architectural changes (Rule 4) — this is a markdown synthesis plan.

## Verification

- **Task 1** (`grep -q make_generator && grep -q NotImplementedError && ! grep -q "BUG-05\."`) — **PASS**.
- **Task 2** per-entry schema linter (hoisted-flag corrected form; the plan's verbatim form does not
  compile on Python ≥3.11) — **PASS**: `24 findings, all 8 fields + anchor present`.
- Every `file:line` re-grepped against the live post-04-04 tree this session; confirmed anchors incl.
  M-01 `projection.py:189`/`:79`, M-06 `interpolation.py:221`/`:225`/`:236`, DSN-01
  `tiled_generator.py:66-68`, DSN-02 `disk_backed_image_data.py:63-64`, DSN-05 registries
  (`strategies/registry.py:38,63,92` vs `features/registry.py:33,39,48,65`), DSN-07 four B008 sites,
  DSN-09 pickle (`disk_backed_image_store.py:49`/`:38`/`:28`), M-13 `rrim.py:196-204`.

## Threat surface

T-04-J (pickle.load of arbitrary `*.pkl`, Tampering/RCE, high, disposition=mitigate/log) is carried
in the merged file as **DSN-09** with its mitigation and trust boundary — the ASVS L1
`block_on:high` gate is satisfied by surfacing-and-logging (fix + proving test is Phase 5/6 per
D-02). No new security surface introduced (markdown-only output).

## Commits

- `c9efec5` docs(review): synthesize canonical 04-FINDINGS.md (Phase-4 gate)

## Notes for Phase 5

`04-FINDINGS.md` is the standalone BUG-05 feeder. Consume it top-down (most-severe-first). The
`M-*` / `DSN-*` ids are stable; do **not** re-mint them as `BUG-05.N` requirement ids (D-07). Two
math items are flagged for a 3rd-tiebreaker / empirical resolution: **M-02** (perspective Z_c≤0
guard) and **M-11** (hillshade aspect handedness — depends on the raster orientation convention
Phase 5 must pin). The DiskBackedImageData/coerce-null xfails already encode DSN-06; BUG-01/03/04
remain source-only cross-references with no xfail. Use the **hoisted-flag** linter form to re-verify.

## Self-Check: PASSED

- Created file verified on disk: `04-FINDINGS.md` (exists, non-empty), `04-07-SUMMARY.md`.
- Commit verified in git log: `c9efec5`.
- Task 1 grep PASS; Task 2 per-entry linter (corrected form) PASS (24/24 entries schema-valid).
