---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 05
subsystem: ci
tags: [github-rulesets, drift-check, test-fixtures, docs]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "ruleset_lib.py comparator (rules (a)-(e)), test_ruleset_lib.py, test_check_ruleset_drift.py, RULESETS.md; the round-4 findings WR-01 and IN-01..IN-04"
provides:
  - "live-payload fixtures in the measured post-apply shapes, with exactly one UI-created case"
  - "read-filled-key-survives test parametrised over both read-filled tuples"
  - "rule (c)/(d) contract docstrings naming the measured shapes and the two tuples"
  - "one RULESETS.md maintainer bullet naming the five fields the apply does not govern"
affects: [0.11.0 promotion, ruleset drift check]

actuals:
  tokens: 3551
  tasks: 2
  commits: 2
plan_head_before: 03a24b3e52e8c8335f1b079bdf0ea1dbe932d116
plan_head_after: 80f2c507aa9d6e90f91e72edf9ebee7a90a6d18b

tech-stack:
  added: []
  patterns:
    - "parametrised test with explicit ids naming rule and key, and an in-test assertion that each case's key is a member of its rule's *_READ_FILLED_KEYS tuple"

key-files:
  created: []
  modified:
    - .github/scripts/ruleset_lib.py
    - .github/scripts/test_ruleset_lib.py
    - .github/scripts/test_check_ruleset_drift.py
    - RULESETS.md

key-decisions:
  - "RULESETS.md bullet omits the plan's suggested sentence 'Change them in the web UI if you need to': it contradicts the existing 'Never edit rulesets in the web UI' bullet two lines above. The five fields and the 'drift check ignores them unless a payload sets one' fact are kept."
  - "Apply-shaped live payload is the new default for live_payload(); the UI-created shape is opt-in via ui_created=True"

requirements-completed: [DEP-05]

coverage:
  - id: D1
    description: "Rule (d) compares a committed read-filled key for both tuples (pull_request allowed_merge_methods, required_status_checks do_not_enforce_on_create)"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: ".github/scripts/test_ruleset_lib.py::test_read_filled_key_survives_when_the_committed_side_sets_it[pull_request-allowed_merge_methods] and [required_status_checks-do_not_enforce_on_create]"
        status: pass
      - kind: other
        ref: "mutation: removing the `if key in committed_parameters: continue` guard in a scratch copy of _drop_keys fails both parametrised ids"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fixtures carry measured shapes; one UI-created case keeps integration_id 15368; apply-shaped payload normalises with no live-side rule (c) record and no surviving difference"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: ".github/scripts/test_ruleset_lib.py::test_rule_c_records_the_integration_id_removal_for_a_ui_created_ruleset, ::test_apply_shaped_live_payload_normalises_with_no_live_rule_c_removal"
        status: pass
      - kind: unit
        ref: ".github/scripts/test_check_ruleset_drift.py (all pass with the measured live fixture)"
        status: pass
    human_judgment: false
  - id: D3
    description: "ruleset_lib.py changed in docstrings only"
    requirement: "DEP-05"
    verification:
      - kind: other
        ref: "docstring-stripped ast.dump comparison of HEAD vs working file -> ruleset-lib-ast-identical; git diff e165b37^..e165b37 -- ruleset_lib.py shows docstring lines only"
        status: pass
    human_judgment: false
  - id: D4
    description: "RULESETS.md names the five ungoverned fields in plain repository-doc wording"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: "tests/test_hygiene.py (88 passed, includes test_shipped_file_has_no_planning_vocabulary for RULESETS.md)"
        status: pass
    human_judgment: true
    rationale: "Whether the one bullet reads clearly to an outside maintainer is a judgment no test asserts"

duration: 20min
completed: 2026-10-02
status: complete
---

# Phase 7 Plan 05: Ruleset comparator polish Summary

**Ruleset-comparator fixtures now match what GitHub reads back after an apply, the read-filled-key test covers both tuples, the rule (c)/(d) contract text is accurate, and RULESETS.md names the five fields the apply does not govern; no comparator verdict changed.**

## Accomplishments

- **IN-01.** `live_payload()` defaults to the measured post-apply shape: `dismissal_restriction` is `{"enabled": False, "allowed_actors": []}` and status-check entries carry no `integration_id`. A keyword `ui_created=True` restores `integration_id: 15368` on every entry. The drift-test fixture in `test_check_ruleset_drift.py` mirrors both shapes.
- **IN-01 tests.** Exactly one test uses the UI-created shape, `test_rule_c_records_the_integration_id_removal_for_a_ui_created_ruleset` (asserts two live-side rule (c) records and a clean diff). A new `test_apply_shaped_live_payload_normalises_with_no_live_rule_c_removal` asserts the apply shape records no live-side rule (c) removal and leaves no surviving difference.
- **IN-03.** `committed_payload()` gained `status_checks_parameters`. `test_read_filled_key_survives_when_the_committed_side_sets_it` is parametrised over `("pull_request", "allowed_merge_methods", ...)` and `("required_status_checks", "do_not_enforce_on_create", ...)` with ids `pull_request-allowed_merge_methods` and `required_status_checks-do_not_enforce_on_create`. Each case asserts the key is in its rule's `*_READ_FILLED_KEYS` tuple, survives on both normalised sides, is absent from the removal list and is named by the diff.
- **IN-02 / IN-04.** The `normalize` contract docstring now states that an applied ruleset reads back without `integration_id`, a UI-created one reads back 15368, and the committed files carry null. It names `PULL_REQUEST_READ_FILLED_KEYS` (four keys) and `STATUS_CHECKS_READ_FILLED_KEYS` (`do_not_enforce_on_create`), and gives the measured `dismissal_restriction` read-back shape. The `_clean_status_checks` docstring was reworded to match.
- **WR-01.** One bullet in RULESETS.md "For maintainers" (four lines) naming the five fields.

## Evidence (reproduced by running code)

- Suite: `uv run --frozen pytest .github/scripts/ -q` -> 120 passed (was 117; +1 parametrised case, +1 UI-created test, +1 apply-shaped test).
- Mutation check: in a scratch copy of `ruleset_lib.py`, deleting the `if key in committed_parameters: continue` guard in `_drop_keys` (rule (d) made unconditional) fails both parametrised ids. The new test is therefore sensitive to the fail-open it is meant to pin (T-07-16).
- AST identity (run against pre-edit HEAD before committing): `ruleset-lib-ast-identical`. Post-commit `git diff e165b37^..e165b37 -- .github/scripts/ruleset_lib.py` shows only docstring lines (rule (c) and (d) text in `normalize`, the body of `_clean_status_checks`'s docstring).
- `ruff check` and `ruff format --check` over `.github/scripts`: clean. `pre-commit run --all-files`: all hooks Passed. `tests/test_hygiene.py`: 88 passed.

## Task Commits

1. **Task 1: fixtures, parametrised test, rule (c)/(d) docstrings** - `e165b37` (test(rulesets))
2. **Task 2: RULESETS.md bullet** - `80f2c50` (docs(rulesets))

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Doc consistency] Dropped the plan's "Change them in the web UI" sentence from the RULESETS.md bullet**
- **Found during:** Task 2
- **Issue:** The plan's bullet text told maintainers to change the five fields in the web UI, while the "Changing a rule" bullet two lines above says "Never edit rulesets in the web UI". Shipping both would make the public doc contradict itself.
- **Fix:** Kept the five field names and the owner policy (comparator keeps ignoring them unless a payload sets one explicitly); omitted the web-UI sentence and the "expect the comparator to stay silent" sentence. The bullet is four lines (the acceptance cap is four).
- **Files modified:** RULESETS.md
- **Commit:** 80f2c50

**2. [Plan choice] Parametrised test builds the live side by mutating the default payload**
- The plan's `live_payload(...)` signature only carries `allowed_merge_methods`; for the `do_not_enforce_on_create` case the test sets the key on the live rule's parameters directly rather than widening `live_payload`'s signature again.

**Total deviations:** 1 auto-fixed (doc consistency), 1 plan choice. **Impact:** none on scope or comparator behaviour.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or trust-boundary surface; the plan edits tests, docstrings and one doc line.

## Issues Encountered

None. Note for the phase verifier: `_scrap/` (gitignored) holds `ruleset_lib.head.py`, the pre-edit copy used by the AST comparison.

## Self-Check: PASSED

- Files exist: `.github/scripts/ruleset_lib.py`, `.github/scripts/test_ruleset_lib.py`, `.github/scripts/test_check_ruleset_drift.py`, `RULESETS.md`.
- Commits found: `e165b37`, `80f2c50` (`git rev-list --count` over the ledger base = 2).
- Plan-level verification re-run: `.github/scripts` 120 passed; `ruleset_lib.py` AST identical; RULESETS.md hygiene-clean; pre-commit clean.
