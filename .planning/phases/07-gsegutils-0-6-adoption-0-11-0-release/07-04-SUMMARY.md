---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
plan: 04
subsystem: ci
tags: [github-actions, publish-gate, ruleset-preflight, readthedocs, setuptools_scm, release-hardening]

requires:
  - phase: 06-publication-hardening-downstream-migration-record
    provides: "check_publish_gate.py, preflight_ruleset_apply.py, .readthedocs.yaml and the accepted risks AR-07 / AR-08 recorded in 06-SECURITY.md"
provides:
  - "publish containment gate that also matches `uv publish` and publish steps wrapped in local composite actions (nested chains followed to a fixpoint)"
  - "ruleset apply preflight that counts only job names of pull-request-triggered workflows as matchable contexts"
  - ".readthedocs.yaml with forced tag fetch, conditional unshallow and a post_install version/shallow assertion"
  - "07-rtd-simulation.sh: scratch-clone simulation running the committed RTD commands"
affects: [07 security verification (retires AR-07 / AR-08), 0.11.0 promotion]

actuals:
  tokens: 45374
  tasks: 3
  commits: 3
plan_head_before: ecdaf832c8a36b604a65b0188bd586c0f190cbc7
plan_head_after: b3347e4f5d01dc768cd705e1eb428bb8e5e9b783

tech-stack:
  added: []
  patterns:
    - "fixpoint closure over local composite-action references (terminates on cycles)"
    - "trigger-event filter on the matchable job-name set"
    - "release-config commands extracted from the committed YAML and run in scratch clones (file:// so --depth is honoured)"

key-files:
  created:
    - .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-rtd-simulation.sh
  modified:
    - .github/scripts/check_publish_gate.py
    - .github/scripts/test_check_publish_gate.py
    - .github/scripts/preflight_ruleset_apply.py
    - .github/scripts/test_preflight_ruleset_apply.py
    - .readthedocs.yaml

key-decisions:
  - "publish_composite_actions returns (flagged_names, unreadable_action_violations): an unreadable composite action is a named violation, mirroring the workflow rule, rather than a skip"
  - "A shell comment inside a run: body is flagged (step text matched as written, fail-closed); YAML comments outside step text are not (the loader drops them). Both pinned by tests and stated in the module docstring"
  - "pull_request_target counts as a pull-request trigger alongside pull_request; every other event (push, schedule, workflow_dispatch, release) contributes no matchable names"
  - "The shallow simulation case proves non-vacuity by asserting is-shallow-repository == true and commits-before < origin commits before running the commands"

patterns-established:
  - "Gate scripts under .github/scripts carry numpy-convention docstrings on every test (ruff per-file-ignores do not relax that directory)"

requirements-completed: [DEP-05]

coverage:
  - id: D1
    description: "Publish gate refuses `uv publish` and publish steps reached through (nested) local composite actions outside the allowed file/environment pairs; real tree stays clean"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: ".github/scripts/test_check_publish_gate.py (32 tests, incl. two-level chain, cycle, action.yaml, comment pair, real-tree)"
        status: pass
      - kind: other
        ref: "python .github/scripts/check_publish_gate.py -> check_publish_gate: OK"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ruleset preflight refuses a required context produced only by a schedule/push-only workflow; real main.json and develop.json still preflight OK"
    requirement: "DEP-05"
    verification:
      - kind: unit
        ref: ".github/scripts/test_preflight_ruleset_apply.py (30 tests, incl. real scheduled-health refusal)"
        status: pass
      - kind: other
        ref: "preflight_ruleset_apply.py main.json / develop.json against copied real workflows -> OK"
        status: pass
    human_judgment: false
  - id: D3
    description: ".readthedocs.yaml tag-fetch hardening proven by running the committed commands in scratch clones"
    requirement: "DEP-05"
    verification:
      - kind: other
        ref: "bash .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-rtd-simulation.sh -> rtd-sim-ok"
        status: pass
    human_judgment: true
    rationale: "The first real Read the Docs build after promotion is the only proof against RTD's own checkout; the simulation reproduces git behaviour, not RTD's container"

duration: 30min
completed: 2026-10-02
status: complete
---

# Phase 7 Plan 04: Release-path hardening Summary

**Publish gate now sees `uv publish` and composite-wrapped (even nested) publish steps, the ruleset preflight only trusts pull-request-triggered job names, and the RTD build forces tag fetches and asserts a real version, proven by a scratch-clone simulation.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-10-02
- **Tasks:** 3 (all `tdd`/auto, no checkpoints)
- **Files:** 6 (5 modified, 1 created)

## Accomplishments

- **AR-07 closed (T-06-17 / T-07-12).** `check_publish_gate.py` gained the `uv\s+publish` pattern, `ACTIONS_DIR` / `ACTION_FILE_GLOBS`, `is_local_action_reference`, and `publish_composite_actions`, which reads every local composite action (both `action.yml` and `action.yaml`), flags those with a publish step, and closes the flagged set under local `uses:` references until nothing changes (a reference cycle terminates). `check_job` / `collect_violations` take the flagged set; the violation names the wrapping action. An absent actions directory is a clean tree; an unreadable action file is a named violation.
- **AR-08 closed (T-06-31 / T-07-13).** `preflight_ruleset_apply.py` gained `PR_TRIGGER_EVENTS = ("pull_request", "pull_request_target")` and `trigger_events(block)` (string / list / mapping). `matchable_job_names` skips, with a stderr diagnostic, any workflow whose events are disjoint from that set. A payload requiring `Branch ancestry assertion` against the real `scheduled-health.yml` is now refused (it exited 0 before).
- **WR-02/03/04 closed (T-06-13 / T-07-14).** `.readthedocs.yaml` `post_checkout` is now the conditional unshallow (no `|| true`) plus `git fetch --tags --force`; a new `post_install` asserts the installed version does not start with `0.0.` and the clone is not shallow.
- **Simulation.** `07-rtd-simulation.sh` extracts the committed commands with awk, builds a fake origin from this repository, and exercises four cases plus negative controls over `file://` clones.

## Test counts

| Scope | Before | After |
|-------|--------|-------|
| `test_check_publish_gate.py` | 17 | 32 |
| `test_preflight_ruleset_apply.py` | (part of 93) | 30 (+9) |
| whole `.github/scripts` suite | 93 | 117 |

## Real-tree evidence

```
check_publish_gate: OK — publish steps found only in allowed files + environments
preflight_ruleset_apply: OK — `main.json` vs `refs/heads/main`, 3 required context(s) all matched a job name on the target tip; ...
preflight_ruleset_apply: OK — `develop.json` vs `refs/heads/develop-gsd`, 2 required context(s) all matched a job name on the target tip; ...
```
Diagnostics on stderr for the real tip: `publish-pypi.yml`, `publish-testpypi.yml`, `release-please.yml`, `ruleset-apply.yml`, `scheduled-health.yml` are skipped as non-pull-request triggers; `ci.yml` supplies all required contexts. ruff check and format are clean over `.github/scripts`; `tests/test_hygiene.py` passes (88).

## Simulation output (`07-rtd-simulation.sh`)

```
git version: git version 2.53.0
post_checkout[0]: if [ "$(git rev-parse --is-shallow-repository)" = "true" ]; then git fetch --unshallow; fi
post_checkout[1]: git fetch --tags --force
post_install[0]: python -c "import importlib.metadata as m; v = m.version('pc2img'); ... raise SystemExit(0 if not v.startswith('0.0.') else 'setuptools_scm fell back to its tagless version')"
post_install[1]: test "$(git rev-parse --is-shallow-repository)" = "false"
origin commits: 534
== case 1: shallow clone
is-shallow-repository before commands: true
commits before commands: 334 of 534
is-shallow-repository after commands: false
commits after commands: 534
case 1 ok: unshallowed to the full history, v0 present
== case 2: complete clone
is-shallow-repository before commands: false
control ok: unconditional --unshallow is fatal on a complete clone
case 2 ok: both commands exit 0 on a complete clone
== case 3: moved floating tag
control ok: plain 'git fetch --tags' rejects the moved tag
 t [tag update]      v0         -> v0
case 3 ok: v0 force-updated to ec7eb5b131a02121684f2e8b802233ec62c12ec5
== case 4: post_install assertions
shallow assertion ok: passes on a full clone, fails on a shallow one
installed pc2img 0.11.0
setuptools_scm fell back to its tagless version
installed pc2img 0.0.post41
version assertion ok: 0.11.0 passes, 0.0.post41 fails
rtd-sim-ok
```

## Task Commits

1. **Task 1: AR-07 publish gate** - `d8f2f0f` (ci(publish-gate))
2. **Task 2: AR-08 preflight trigger filter** - `ec7eb5b` (ci(ruleset-preflight))
3. **Task 3: RTD hardening + simulation** - `b3347e4` (ci(rtd))

Tests and implementation for each task landed in the one task commit, as the plan specifies.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Simulation's `v-old` outside-the-window tag assumption was false**
- **Found during:** Task 3 (first simulation runs)
- **Issue:** The first draft tagged an old commit and expected a `--depth 50` clone to lack it. A clone fetches tags and pulls the tagged commit in, so the tag (and, with merge-heavy history, 334 of 534 commits) was present; the case failed its own non-vacuity check. Separately, the origin copy already carries the real `v0` tag, so `git tag v0` was fatal and needed `-f`.
- **Fix:** Dropped the `v-old` tag; the shallow case now asserts commits-before (334) < origin (534) and commits-after == origin, in addition to the `is-shallow-repository` true/false assertions. Origin tags use `tag -f`.
- **Files modified:** 07-rtd-simulation.sh
- **Commit:** b3347e4

**2. [Plan choice] `publish_composite_actions` return shape**
- The plan left the unreadable-action handling open ("choose one and test it"). Chose a `(flagged, violations)` tuple so unreadable actions surface as named violations; `main` prepends them to the workflow violations. Covered by `test_an_unreadable_composite_action_is_a_named_violation`.

**Total deviations:** 1 auto-fixed (Rule 1, within the simulation script before commit), 1 plan-sanctioned choice. **Impact:** none on scope.

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths or trust-boundary schema changes; all edits tighten existing gates.

## Issues Encountered

- The first Read the Docs build after promotion remains the only check against RTD's real checkout (see coverage D3). Not blocking.

## Self-Check: PASSED

- Files exist: check_publish_gate.py, preflight_ruleset_apply.py, both test files, .readthedocs.yaml, 07-rtd-simulation.sh (mode 100755 in the index).
- Commits found: d8f2f0f, ec7eb5b, b3347e4 (`git rev-list --count` over the ledger base = 3).
- Plan-level verification re-run: `.github/scripts` 117 passed; publish gate OK; both real payloads preflight OK; `rtd-sim-ok`; ruff clean; hygiene 88 passed.
