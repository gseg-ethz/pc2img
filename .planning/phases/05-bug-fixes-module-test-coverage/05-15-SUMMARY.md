---
phase: 05-bug-fixes-module-test-coverage
plan: 15
subsystem: image_cache + features/rrim + phase bookkeeping
tags: [security, path-containment, breaking-change-record, gap-closure, bookkeeping]
gap_closure: true
gap_round: 3
requires:
  - "05-14 (delegate-then-unlink __delitem__ ordering, commit f776011; docstring narrowing ce14b28)"
  - "05-14 (widened _Z_FACTOR_RE exponent grammar, commit 5dbd93e)"
provides:
  - "DiskBackedImageStore path-containment authority (ValueError on an escaping raster key)"
  - "05-BC-NOTES.md entries 15 and 16, both carrying into Phase 6 BC-01"
  - "05-UAT.md gap statuses reconciled with citable evidence (audit-uat 22 open -> 7)"
affects:
  - "Phase 6 BC-01 downstream migration record (two new entries to intake)"
  - "/gsd-ship gate (now reads 7 genuinely-outstanding items instead of 22 stale ones)"
tech-stack:
  added: []
  patterns:
    - "one containment authority inside the shared path builders rather than a per-call-site guard"
    - "characterization/pinning test for owner-accepted kept behaviour (CONTEXT two-bucket rule), xfail-first RED only for the genuine fix (D-12)"
key-files:
  created: []
  modified:
    - src/pc2img/image_cache/disk_backed_image_store.py
    - src/pc2img/features/rrim.py
    - tests/test_image_store.py
    - tests/test_rrim_features.py
    - .planning/phases/05-bug-fixes-module-test-coverage/05-BC-NOTES.md
    - .planning/phases/05-bug-fixes-module-test-coverage/05-UAT.md
    - .planning/phases/05-bug-fixes-module-test-coverage/05-VERIFICATION.md
decisions:
  - "Containment check placed inside _get_npy_path / _get_meta_path, not at the unlink sites — one authority over all four disk-touching routes, with __delitem__ left byte-identical to ce14b28"
  - "The resolved cache directory is NOT cached on the instance: the base store pickles its __dict__ wholesale for the joblib/loky tiled path; measured cost of not caching is ~45 us per path build"
  - "WR-03 landed as record + pin with zero behaviour change, per the locked owner decision — the regex, the parser and the precedence are untouched"
  - "The float32 scaling overflow reads status: deferred, not resolved, so it stays visible to audit-uat by design"
metrics:
  duration: 46min
  completed: 2026-07-28
  tasks: 3
  files: 7
  tests_before: 163
  tests_after: 175
  coverage: 61.88%
status: complete
---

# Phase 5 Plan 15: Round-3 Gap Closure — Store Path Containment, RRIM Precedence Record, Gap Bookkeeping Summary

Closed the two `major` round-1 findings with a single path-containment authority plus a
breaking-change record, and reconciled the phase's stale gap bookkeeping so `/gsd-ship`
reads the true state: `audit-uat` for `05-UAT.md` drops from **22 open items to 7**.

## What Was Built

| Task | Deliverable | Commit |
| --- | --- | --- |
| 1 (WR-02, major/security) | `DiskBackedImageStore._assert_within_cache_dir` + `_get_npy_path` / `_get_meta_path` overrides; 3 proving/characterization tests; BC-NOTES entry 15 | `03eb715` |
| 2 (WR-03, major/BC) | corrected `_Z_FACTOR_RE` comment + extended `RRIMConfig` grammar note; 2 pinning tests; BC-NOTES entry 16 + forward-only cross-reference on entry 14 | `b9b6a2e` |
| 3 (bookkeeping) | 16 per-gap `status:` flips with cited `evidence:`; appended round-3 closure record to `05-VERIFICATION.md` | `d0f0b14` |

## (1) WR-02 reproduction transcript — broader than the finding's own truth statement

The finding's truth is scoped to `unlink()`: *"A store key can never cause `unlink()` to
touch a file outside the configured cache directory."* Reproduced against HEAD on
2026-07-28, with a sentinel file one directory above the cache directory, the defect was
**wider than that** — the offload **wrote through the escaping path first**:

```
after offload, victim bytes: b"\x93NUMPY\x01\x00v\x00{'desc"
victim exists after delete:  False
```

So `add_image_to_store("../victim", arr)` + `offload_image_data_to_disk("../victim")`
**overwrote** a pre-existing file outside the cache directory with an NPY header, and
`del store["../victim"]` then **deleted** it. Arbitrary file *overwrite* (T-05-15a) as
well as arbitrary file *deletion* (T-05-15b). The `must_haves` truth for this plan was
written to cover both, and both are asserted by tests.

**Reachability, unchanged from the finding's honest framing:** not reachable from the
feature-name DSL today — every registered `regex_pattern` anchors on a literal prefix, so
no DSL-derived store key can begin with `..` or `/`. But `DiskBackedImageStore` is exported
from the public barrel `pc2img.image_cache.__all__`, and this phase (05-14, `f776011`) is
what turned `__delitem__` into a file-deletion primitive. Recorded as hardening of a public
API surface, not as a live exploit path from point-cloud metadata.

## (2) Why the check lives in the path builders, not at the unlink sites

The base store builds **every** on-disk path through `_get_npy_path` / `_get_meta_path` —
`add_data_to_store` at insertion (`disk_backed_store.py:326`), `_store_entry` at the offload
write (`:418-419`), `_load_entry` at read (`:483-484`), and this subclass's `__delitem__` at
unlink. Overriding those two methods is therefore **one authority covering all four routes**,
not a per-call-site patch. Two consequences that a guard at the unlink sites would not have
bought:

- The refusal for an insertion fires at `add_data_to_store`'s path build — **before any file
  outside the cache directory is created or truncated**. A delete-time-only guard would have
  left the *overwrite* half of the reproduction live.
- `__delitem__` is **byte-identical to `ce14b28`** (`git diff ce14b28 HEAD` shows zero changed
  lines in its body, ordering or docstring). The 05-14 delegate-then-unlink ordering, its
  single membership authority, and the just-reviewed docstring narrowing are preserved *by
  construction* rather than by re-editing a method that had been fixed and reviewed twice.
  This mattered given the phase's own history: this is the third consecutive round in which a
  review of a gap diff found defects the previous round's fixes introduced.

`_store_entry` also builds a `.meta.json.tmp` sidecar **directly from `self._cache_dir`**,
bypassing both helpers — which is exactly why the guard has to fire at insertion time and not
only at write time. The insertion refusal is what covers that gap.

`__setitem__` (`disk_backed_store.py:257`) bypasses `add_data_to_store` entirely, so a key can
become tracked without ever passing the insertion guard. The delete-time guard covers that
route, and `test_escaping_key_delete_refuses_and_leaves_outside_file_intact` deliberately
reaches the unlink through the mapping setter rather than through `add_image_to_store`.

## (3) The resolved cache directory is deliberately not cached on the instance

`_assert_within_cache_dir` re-resolves `self._cache_dir` on every call. `DiskBackedStore.__getstate__`
returns `self.__dict__.copy()` wholesale for the joblib/loky tiled path, so a resolved path
cached on the instance is state that can go stale across processes. Measured cost of not
caching, 20 000 iterations:

```
guarded=45.9us  base(unguarded)=0.8us  overhead=45.0us
```

~45 µs per **path build** — i.e. per raster, not per pixel. Against a raster interpolation
that is orders of magnitude more expensive, this is not a measurable cost, and it buys
correctness under pickling.

## (4) WR-03 — measured pre/post precedence and the verified migration path

All values measured against HEAD on 2026-07-28. The tests **pin observed behaviour, they do
not predict it** — both passed on their first run, before any source edit.

| Name | `base_feature` | `z_factor` |
| --- | --- | --- |
| `z1e5` (now) | `range` | `100000.0` |
| `z1e5` (pre-05-14) | `z1e5` | `1.0` |
| `z1E5` | `range` | `100000.0` |
| `z1` (rule predates the widening) | `range` | `1.0` |
| `z1e5x` (near miss) | `z1e5x` | `1.0` |
| `zx1e5` (near miss) | `zx1e5` | `1.0` |
| `scalar_field_z1e5` (migration) | `scalar_field_z1e5` | `1.0` |
| `scalar_field_z1e5,z2` (migration + options) | `scalar_field_z1e5` | `2.0` |
| `_parse_rrim_component("slope,z1e5")` | `range` | `100000.0` |

The pre-05-14 pattern `^z([+-]?\d+(?:\.\d+)?)$` does not match `z1e5` (verified by
instantiating it), which is what makes this a genuine reinterpretation: **the same public
name, resolving to the same cache key, now denotes a different computation.**

Per the locked owner decision this is a **record + pin, not a behaviour change** — the regex,
`_looks_like_option_token`, `_parse_rrim_config`, `_parse_rrim_component`, `_format_number`
and `pack_feature_name` are all untouched. `git diff src/pc2img/features/rrim.py` contains
only comment and docstring hunks, and the regex pattern is asserted unchanged in `<verify>`.

The mechanism worth naming for a future reader: widening `_Z_FACTOR_RE` is additive at the
**token** level, but `_looks_like_option_token(tokens[0])` turns that into a **name**-level
precedence change. The in-code comment previously claimed unqualified additivity; it now
states that option tokens take precedence over base-feature names and points at BC-NOTES
entry 16. Entry 14 was **not rewritten** — it gained one appended cross-reference line,
following the repository's own precedent (05-REVIEW.md CR-01, where the original text was
preserved and a correction appended beneath it).

## (5) Resulting `audit-uat` open count

```
open UAT items: 7 | deferred,failed,failed,failed,failed,failed,failed
```

Down from **22** measured on 2026-07-28. Sixteen `status:` fields were flipped **in place** —
`uat.cjs extractGapEntryFields` takes the FIRST occurrence of a key inside an entry, so adding
a second `status:` line would have changed nothing. Every flipped entry carries an `evidence:`
line naming a commit SHA, a test function, or a BC-NOTES entry number; none cites "verified" or
"fixed" without an artifact. All entries stay inside the single `## Gaps` heading (the parser
matches it with `/^gaps$/i`, so a `## Gaps — Round N` variant would make every entry below it
invisible).

Neither file's YAML frontmatter was touched — re-verification owns `status:` / `gaps_open:` /
`gaps_resolved:`.

## (6) Gaps that could not be tied to a commit

**None.** Sub-step (4) of Task 3 (the owner-confirmed scope addition covering the eight
2026-07-11 entries `review-G1`..`review-G8`) was executed in full. Every commit cited was
verified to exist and to carry the expected subject before being written into an evidence
line:

| Gap(s) | Commit | Subject (verified) |
| --- | --- | --- |
| G1 | `f2e5b12` (RED `f799ada`) | `fix(features): schedule RRIM base/pack deps via dependencies_for (G1 blocker)` |
| G2 / G4 / G7 | `80cb108` (RED `eca7499`) | `fix(projection): validate K, check rotation in float64, single-pass ortho gather` |
| G3 | `9148197` (RED `002e59d`) | `fix(image_cache): purge on-disk codec pair on delete/overwrite` |
| G5 / G6 / G8 | `46d679e` (tests `aedabcf`) | `refactor(features): single-source dep grammar, drop dead FeatureSpec derivation, centralize percentile bounds` |

The two deviations `05-VERIFICATION.md` already documents were carried into the evidence lines
rather than glossed: **G4's RED was not constructible** (the float32 check does not in fact
false-reject valid scipy rotations within 1e-6 across 20k seeds), so it landed as a passing
characterization test plus the float64 refactor; **G8 unified three divergent message strings**
with accept/reject outcomes unchanged.

Since both count gates held at their primary values (audit **7**, `status: resolved` **15**),
no gate edit was needed.

## (7) Findings deliberately left open, and the one deferred

So the next reviewer does not re-report them as new:

**Deferred to Phase 6 (1)** — `review-r1-42a7c0c6f8c7`, the RRIM float32 scaling-invariant
guard. Reads `status: deferred` with `deferred_to:`
`.planning/todos/pending/2026-07-27-rrim-float32-scaling-invariant-guard.md`
(`resolves_phase: 6`). Owner decision 2026-07-27 downgraded it blocker → warning: it is **not a
Phase-5 regression**, because the same all-NaN raster is reachable on the pre-05-14 grammar via
the long-form spelling (`z` + ~40 digits), so 05-14 changed ergonomics only. It **stays visible
to `audit-uat` by design** — the parser skips only `resolved`, and the work is dispositioned,
not done. Nothing in this plan's source diff touches it: no finiteness check, no
float32-representability guard, no `compute_slope` / `compute_openness` / `_validate_config` edit.

**Deliberately open (6)**, untouched by this plan:

| ID | Finding |
| --- | --- |
| `review-r1-a8cd7b4707b0` | WR-04 — RRIM end-to-end test does not assert `z_factor` influences the output |
| `review-r1-4939108716dd` | WR-05 — round-trip coverage omits the upper exponent boundary |
| `review-r1-c2b69f0885e7` | WR-06 — `test_delete_absent_key_does_not_raise` name misdescribes its contract |
| `review-r1-ab91c4469087` | IN-01 — dead module-level logger in `rrim.py` |
| `review-r1-8fb6b87813d1` | IN-02 — `_validate_clip` ignores its `name` parameter |
| `review-r1-8ff7171c6ca4` | IN-03 — ruff B008 on the store constructor default |

IN-03 is worth flagging for whoever runs the hygiene gate next: `ruff check` on
`src/pc2img/image_cache/disk_backed_image_store.py` **still reports one B008**. That is this
pre-existing deliberately-open finding, not a new failure introduced here — it was present
before this plan and was not "fixed while in the file", per the scope boundary.

## Verification Results

| Gate | Result |
| --- | --- |
| `pytest tests/test_image_store.py tests/test_disk_backed_image_data.py -q` | 40 passed, **0 xfail / 0 xpass** |
| `pytest tests/test_rrim_features.py -q` | 40 passed, 0 xfail |
| Full suite `pytest tests/ -q` | **175 passed**, 0 failed, **0 residual xfail** (baseline 163) |
| Coverage floor | **61.88%** vs `--cov-fail-under=55` — *"Required test coverage of 55% reached"* |
| `__delitem__` ordering assertion | passes — `super().__delitem__` precedes `unlink(`, and no `in self` pre-check exists |
| `__delitem__` vs `ce14b28` | byte-identical (0 changed lines) |
| Both path builders overridden + real containment check | passes |
| `grep -c 'cache_dir is not None'` in the store | `0` — the guard 05-14 removed was not reintroduced |
| `grep -c 'purely ADDITIVE'` in `rrim.py` | `0`; `grep -qi 'take precedence'` matches |
| `_Z_FACTOR_RE.pattern` unchanged | asserted equal to the 05-14 pattern |
| BC-NOTES | `## 15.` ×1, `| 15 |` ×1, `## 16.` ×1, `| 16 |` ×1, `Carry into Phase 6 BC-01` ×**5** |
| Entry 14 preserved | `git diff` shows **zero deletions** anywhere in `05-BC-NOTES.md` — every change is an append |
| `audit-uat` for `05-UAT.md` | **7** open (1 deferred + 6 deliberately open), down from 22 |
| `grep -c '^## Gaps'` | `1` — no variant heading introduced |
| `grep -c '^  status: resolved'` | `15` |
| `ruff check` `rrim.py` | clean; `ruff format --check` clean on all four touched files |
| `pyright` | **2 errors, both pre-existing** (`rrim.py` `Literal['structure']` `reportReturnType`; store `factory` `reportArgumentType`) — no new errors |
| Shipped plans/SUMMARYs 05-01..05-14 modified | **0** |

## Deviations from Plan

### Auto-fixed Issues

None — no Rule 1/2/3 deviation was needed. The plan's `<behavior>` values all reproduced
exactly as written against HEAD before any edit.

### Process incident (no effect on the delivered work)

While measuring the containment-guard overhead, the executor ran `git stash` inside a compound
command intended as a no-op, which stashed the uncommitted Task-1 working changes. Detected
immediately from the resulting file state; `git stash list` was inspected first, and only the
newly-created `stash@{0}` (on this branch, on top of `95fe38c`) was popped — a pre-existing
`stash@{1}` from `dev/v2` was left untouched. All changes were restored intact and re-verified
(guard helper present, test helper present, suite green) before proceeding. The timing
measurement was then redone without stashing, by calling `DiskBackedStore._get_npy_path(store, key)`
unbound as the unguarded baseline. No commit, no file, and no branch state was lost. Recorded
here because the global rules call out `git stash` as unsafe under worktree/parallel execution
and the incident should not be invisible.

## Known Stubs

None. No stub, placeholder, `TODO`/`FIXME`, or unwired data path was introduced by this plan.
No test was skipped and every `<verify>` command in the plan was run.

## Threat Flags

None. The plan's `<threat_model>` covers the full surface touched here: the two `high`
Tampering threats (T-05-15a offload-write overwrite, T-05-15b delete) are both **mitigated**
and proven by test; the DSN-09 deserialization posture (T-05-15c) is unchanged and its source
negative-grep sensor `test_store_source_has_no_arbitrary_deserialization_sink` still passes;
no new network endpoint, auth path, file-access pattern, or schema change at a trust boundary
was introduced. No package was installed.

## Follow-ups for the orchestrator

1. **This gap diff needs its own review before the phase re-verifies** — per the global
   review-discipline rule, `/gsd-code-review 05 --files src/pc2img/image_cache/disk_backed_image_store.py src/pc2img/features/rrim.py tests/test_image_store.py tests/test_rrim_features.py`.
   This is the third consecutive round in which a review of a gap diff found defects the
   previous round's fixes introduced; a phase is not closeable on a review → fix → verify
   sequence where nothing looked at the fix.
2. **Re-verification owns the frontmatter.** `05-UAT.md` and `05-VERIFICATION.md` still carry
   `status: diagnosed` / `status: gaps_found` and stale `gaps_open:` counts. This plan
   deliberately did not touch them; the body now records the true per-gap state underneath.
</content>
</invoke>

## Self-Check: PASSED

All eight modified/created files exist on disk. All four commits (`03eb715`, `b9b6a2e`,
`d0f0b14`, `8e5c145`) are present in git history. All five new test symbols plus the
`_escape_layout` helper are present in their named files, and all three new production
symbols (`_assert_within_cache_dir`, `_get_npy_path`, `_get_meta_path`) resolve on
`DiskBackedImageStore.__dict__` at runtime. No missing items.
