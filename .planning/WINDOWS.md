---
schema_version: 1
open_count: 0
waived_count: 0
fixed_count: 2
total_count: 2
last_updated: 2026-09-30T15:31:19.177Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 06 | deviation | .github/actions/classify-changes/action.yml |  | Declined-component note (IN-04) placed between the description block and outputs: rather than inside the file's single run: script step, to preserve whole-document yaml.safe_load identity against the phase-PR merge commit; the plan's suggested line numbers (64-74) sit inside that run: block, where any comment edit changes the step's script string value under YAML's model. | fixed |  | 2026-09-29T08:32:37.675Z | 2026-09-29T08:33:14.130Z |
| 2 | 06 | unmet-truth | .planning/phases/06-publication-hardening-downstream-migration-record/06-13-SUMMARY.md |  | origin/main is not an ancestor of origin/develop-gsd (06-11's ancestry-graft invariant broke again after 06-12's second promotion to main); GitHub issue #21 (ancestry-drift) open, unresolved, not auto-fixed per no-git-push instruction | fixed |  | 2026-09-30T15:24:33.468Z | 2026-09-30T15:31:19.177Z |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "06",
    "file": ".github/actions/classify-changes/action.yml",
    "line": null,
    "description": "Declined-component note (IN-04) placed between the description block and outputs: rather than inside the file's single run: script step, to preserve whole-document yaml.safe_load identity against the phase-PR merge commit; the plan's suggested line numbers (64-74) sit inside that run: block, where any comment edit changes the step's script string value under YAML's model.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-29T08:32:37.675Z",
    "resolved_at": "2026-09-29T08:33:14.130Z",
    "milestone": "v1.0"
  },
  {
    "id": 2,
    "kind": "unmet-truth",
    "phase": "06",
    "file": ".planning/phases/06-publication-hardening-downstream-migration-record/06-13-SUMMARY.md",
    "line": null,
    "description": "origin/main is not an ancestor of origin/develop-gsd (06-11's ancestry-graft invariant broke again after 06-12's second promotion to main); GitHub issue #21 (ancestry-drift) open, unresolved, not auto-fixed per no-git-push instruction",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-30T15:24:33.468Z",
    "resolved_at": "2026-09-30T15:31:19.177Z",
    "milestone": "v1.0"
  }
]
````
