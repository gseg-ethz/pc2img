---
phase: 06-publication-hardening-downstream-migration-record
review_round: 4
review_scope: "late-phase fix diffs fb44899 (ruleset drift normalisation) + e9a3a98 (RTD tag fetch), git diff 4da8c6c..1b6751f"
reviewed: 2026-09-30T15:37:32Z
depth: deep
files_reviewed: 3
files_reviewed_list:
  - .github/scripts/ruleset_lib.py
  - .github/scripts/test_ruleset_lib.py
  - .readthedocs.yaml
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 6: Code Review Report (round 4: late-phase fix diffs fb44899 + e9a3a98)

**Reviewed:** 2026-09-30T15:37:32Z
**Depth:** deep
**Files Reviewed:** 3
**Status:** issues_found

This replaces the prior 06-REVIEW.md (kept in git at `f5d9037`). It reviews only the two fixes that landed after that review:

- `fb44899` `ci(rulesets): normalise the unattributed-changes approval key GitHub fills on read`
- `e9a3a98` `fix(docs): fetch tags on Read the Docs even when the clone is already complete`

It also covers the surrounding code those fixes touch: `check_ruleset_drift.py`, `ruleset-apply.yml`, the committed `.github/rulesets/*.json`, the `release-please.yml` floating-tag step, and the version guard in the `ci.yml` docs job.

## Summary

**How this was checked.** Every claim below was checked by running code, not by reading it. Scratch work is in `/tmp/claude-1000/-scratch-31-pc2img/rv3/`.

- `uv run --frozen pytest .github/scripts -q` gives **93 passed**.
- Both live rulesets were read with `gh api "repos/gseg-ethz/pc2img/rulesets/24237564?includes_parents=false"` and `.../24244420?...`. `check_ruleset_drift.py` then compared them against `main.json` and `develop.json`. Result: **exit 0**, 2 rulesets, 0 surviving differences, 31 normalised away.
- The same live read, run through the **pre-fix** `ruleset_lib.py` from `4da8c6c`, gives exit 1 on `require_extra_approval_for_unattributed_changes: live=true committed=<absent>`. So the fix is what closes that gap.

**fb44899: answers to the orchestrator's questions, all from running code** (probe script `rv3/probe.py`, applied to the real live payload):

- **Does a committed pin still compare?** Yes. With the committed side pinned to `true` and live `false`, it reports `live=false committed=true`. Pinned `true` with the key absent from live reports `live=<absent> committed=true`. Pinned `null` with live `true` also reports a difference. In every pinned case, nothing is recorded as removed.
- **Can a committed-side value be dropped silently?** No. `committed_rules` is indexed from the committed payload itself, so `_drop_keys` never removes a key from the committed side. Every rule (d) removal record is `[live]`.
- **Can normalising the key hide a weakening made in the GitHub UI?** Yes, and it is reproduced: live `false` with the committed side silent gives **0 differences**. The treatment matches the other four read-filled keys, which are just as blind:
  - `dismissal_restriction` turned on;
  - `required_reviewers` added;
  - `allowed_merge_methods` narrowed to `["merge"]` on a branch that requires linear history;
  - `do_not_enforce_on_create: true`.

  All four also read clean. The key is also **absent from GitHub's published REST OpenAPI description**, fetched today. The PUT schema for the `pull_request` rule lists only the other eight parameters. So whether the apply's PUT resets this key or preserves it is undocumented. See WR-01.
- **Keys the fixture does not model.** The measured live shapes differ from the fixture in two places (IN-01):
  - `dismissal_restriction` is live as `{"enabled": false, "allowed_actors": []}`; the fixture has `{}`;
  - live status-check entries carry **no** `integration_id` at all; the fixture has `15368`.

  Today's OpenAPI lists no further `pull_request` or `required_status_checks` parameters that are not already committed or in the drop list. The next such key will most likely be another undocumented one like this, which cannot be predicted from the spec.

**e9a3a98: RTD's clone sequence, reproduced locally** (`rv3/D`, `E`, `F`, `G`, `H`):

- **`main` (42 commits, complete at depth 50).** `--unshallow` fails fatally and `|| true` swallows it. `git fetch --tags` exits 0. setuptools_scm gives `0.10.4.post7`, matching the hosted build recorded in 06-12.
- **`develop-gsd` (473 commits past `v0.10.4`, the "more than 50 commits past the tag" case).** `--unshallow` does real work (379 to 508 commits). The tags resolve and the result is `0.10.4.post473`, which is correct.
- **PR-preview sequence (`pull/16/head:external-16`).** Unshallow succeeds, and the result is `0.10.4.post455`, which is correct. A fork PR uses the same `pull/N/head` refspec against the base repo, so the tags come from the base repo. This was not run with a real fork PR, because the repo has none.
- **Ordering.** RTD's own `--force --prune --prune-tags --depth 50` fetch is part of the checkout step, which runs before `post_checkout`. That is what RTD's build-job docs say, and it matches the order in the 06-12 hosted build log. So `--prune-tags` cannot delete tags that `post_checkout` fetched. This could not be re-run on RTD itself.
- **What remains broken.** `git fetch --tags` without `--force` now fails the build if a tag moves between the two fetches (reproduced; WR-02). `|| true` still swallows **every** unshallow failure, not only the complete-repository one. When unshallow fails, the result is a silently wrong version: reproduced as `0.10.4.post344` against the true `post473` (WR-03). The RTD build also has no equivalent of the CI job's tagless-version guard (WR-04).

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Normalising `require_extra_approval_for_unattributed_changes` makes post-apply verification blind to a protection weakening, and the key's PUT behaviour is unverified

**File:** `.github/scripts/ruleset_lib.py:41-46` (rule (d) in `_drop_keys`, lines 581-606; the claim is in the docstring at 279-286)

**Issue:** The owner chose to normalise this key rather than pin it (06-10 key-decisions), and the fix does what it says. The consequence has not been recorded anywhere, though.

- **Reproduced:** if live reads `false` and the committed payload is silent, the drift check exits clean. The name describes an approval requirement. It is `true` by default on both rulesets, and `false` is the weaker setting.
- The only caller of the check is `ruleset-apply.yml`'s post-apply read-back, which runs after a six-key PUT that never mentions this field.
- If GitHub's PUT **preserves** omitted fields, a UI change to `false` survives every apply, and the apply still reports `check_ruleset_drift: OK`. The workflow's own comment says "committed is authoritative" has to be literally true or it is nothing. It is not literally true for this field.
- The key is absent from GitHub's published OpenAPI description, so preserve-or-reset cannot be settled from documentation. **Not reproduced:** settling it by running code would mean writing to a production ruleset, and that was not attempted.
- Consistency: the other four read-filled keys are exactly as blind (probes P8-P11). One of them, `allowed_merge_methods` narrowed to `["merge"]` on `protect-main`, contradicts `required_linear_history`, and the check still reads clean.
- The `normalize` docstring justifies rule (d) as conditional precisely so that `allowed_merge_methods` would not be dropped unconditionally. But neither committed file pins **any** read-filled key, so in this repository rule (d) is unconditional in practice. That is the fail-open the docstring warns about.

**Fix:** Pick one of the following and record it.

- (a) Pin `"require_extra_approval_for_unattributed_changes": true`, and preferably `allowed_merge_methods`, in `main.json` and `develop.json`. Rule (d) then compares them (probe P2/P3 shows this works). `to_payload` already forwards a pinned key (probe P12). This only works once a PUT carrying the undocumented key has been shown to be accepted, so verify that first against a throwaway ruleset or repository.
- (b) Keep the normalisation, and state the blind set in RULESETS.md: five `pull_request`/`required_status_checks` fields that neither the apply nor its verification governs. That way "committed is authoritative" is scoped honestly.

### WR-02: Unforced `git fetch --tags` fails the RTD build when a floating tag moves during the build

**File:** `.readthedocs.yaml:20`

**Issue:** `release-please.yml` (lines 65-108) deletes and recreates the annotated floating tags `v0` and `v0.10` on every release. It does this right after release-please creates the release, which is also the moment the push to `main` and the new-tag webhook start RTD builds.

- If RTD's checkout fetch sees the old `v0` and the release step moves it before `post_checkout` runs, `git fetch --tags` refuses to update the existing tag. It exits 1 and fails the build.
- **Reproduced** against a local bare repo:

  ```
  ! [rejected] v0 -> v0 (would clobber existing tag)
  fetch_tags_rc=1
  ```

- The old combined command's `|| true` masked this. The split exposes it.
- Failing loudly is the right default for a network failure: the tags are needed, and a transient failure can simply be rebuilt. A clobber rejection is different. It says nothing about the fetch being unsafe, because the clone is ephemeral, and RTD's own fetch already runs with `--force`.

**Fix:**
```yaml
      - git fetch --tags --force
```

### WR-03: `git fetch --unshallow || true` still swallows every unshallow failure, not only the one it means to tolerate

**File:** `.readthedocs.yaml:16-19`

**Issue:** The comment says `|| true` exists for a single case: `--unshallow` on a complete repository. It suppresses every failure, though, including a network or server error on a clone that really is shallow, which is the case for `develop-gsd` or any branch more than 50 commits past its tag.

The build then continues shallow, and `git fetch --tags` still succeeds. **Reproduced** on `develop-gsd` with the unshallow step skipped:

- setuptools_scm prints only a `UserWarning: ... is shallow` during install;
- it derives `0.10.4.post344` instead of `0.10.4.post473`;
- the build passes, because `fail_on_warning` covers Sphinx warnings only.

If the tag is not reachable inside the shallow window, the version degrades to `0.0.postN`. That is the same silent failure this fix set out to remove.

**Fix:** Tolerate only the "already complete" state by checking it rather than swallowing the error:
```yaml
      - if [ "$(git rev-parse --is-shallow-repository)" = true ]; then git fetch --unshallow; fi
      - git fetch --tags --force
```

### WR-04: The RTD build has no tagless-version assertion, the guard that would have caught the original bug

**File:** `.readthedocs.yaml:21-30` (compare with `.github/workflows/ci.yml:330-351`)

**Issue:**

- The CI docs job asserts that `importlib.metadata.version("pc2img")` does not start with `0.0.`. Its own comment explains why: "a degraded version builds clean and reports success."
- The RTD config has no such check. Its first hosted build (34851945) rendered `pc2img 0.0.post41` and went green.
- e9a3a98 fixes that particular cause, but any future cause (WR-02 if forced but still failing, WR-03, a tag-glob change) will again publish a wrong version with a passing badge.
- Nothing in the RTD build checks that the tags actually resolved.

**Fix:** Add a `post_install` job after the install step:
```yaml
    post_install:
      - python -c "import importlib.metadata as m, sys; v = m.version('pc2img'); print('docs version:', v); sys.exit(1 if v.startswith('0.0.') else 0)"
      - test "$(git rev-parse --is-shallow-repository)" = false
```
The first line is the same `0.0.` check CI uses. The second turns WR-03's silent degradation into a failure.

## Info

### IN-01: The live fixture does not match the measured live shapes

**File:** `.github/scripts/test_ruleset_lib.py:117, 128-129`

**Issue:** The fixture's measured live shapes are out of date:

- **`dismissal_restriction`.** The fixture has `{}`. The live read today returns `{"enabled": false, "allowed_actors": []}` on both rulesets.
- **Status-check entries.** The fixture gives them `integration_id: 15368`. The live read now returns entries with **no** `integration_id` key, because `to_payload` (s2) strips the nulls on PUT.

Tests pass either way, but the fixture is described as "the shape the API actually returns".

**Fix:** Update the fixture to the measured shapes. Keep one test that has a live `integration_id: 15368` as the UI-created-ruleset case.

### IN-02: The rule (c) docstring and removal record describe a live value that no longer exists

**File:** `.github/scripts/ruleset_lib.py:266-268, 542-544, 557-561`

**Issue:** The docstring says "live returns the integer 15368". The actual live read has no `integration_id`, so every rule (c) record is now `[committed] ... integration_id differs live-vs-committed`. That wording claims a live value differs when none was read.

**Fix:** Change it to "live returns 15368 for a UI-created ruleset and omits the key after an apply; the committed files carry null". Make the record text neutral, for example "dropped `integration_id` (not compared)".

### IN-03: No test pins that the new key is compared when the committed side sets it

**File:** `.github/scripts/test_ruleset_lib.py:273-289`

**Issue:** The conditional-compare test only covers `allowed_merge_methods`. For this key, the probe shows correct behaviour (P2-P6). Still, the one key whose weakening matters most (WR-01) has only a drop test and no survive test.

**Fix:** Parametrise `test_read_filled_key_survives_when_the_committed_side_sets_it` over `PULL_REQUEST_READ_FILLED_KEYS` and `STATUS_CHECKS_READ_FILLED_KEYS`.

### IN-04: The "enumerated in full" contract does not list the rule (d) keys

**File:** `.github/scripts/ruleset_lib.py:11-14, 269`

**Issue:** The module docstring says the comparison contract is "enumerated in full in `normalize`", and rule (a) does list its eight keys. Rule (d) says only "Keys GitHub fills on read", and now covers five unnamed keys. A reader of the docstring cannot see that `require_extra_approval_for_unattributed_changes` is excluded from comparison.

**Fix:** List the five keys under (d), or reference `PULL_REQUEST_READ_FILLED_KEYS` / `STATUS_CHECKS_READ_FILLED_KEYS` by name there.

---

_Reviewed: 2026-09-30T15:37:32Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
