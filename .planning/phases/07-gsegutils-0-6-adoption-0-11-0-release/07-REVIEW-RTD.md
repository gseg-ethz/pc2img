---
phase: 07-gsegutils-0-6-adoption-0-11-0-release
reviewed: 2026-10-05T13:10:54Z
depth: quick
scope: "git diff e0cd06f..598ab2b -- .readthedocs.yaml (RTD post_install quoting fix)"
files_reviewed: 1
files_reviewed_list:
  - .readthedocs.yaml
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: issues_found
---

# Phase 7: Code Review Report (scoped: RTD quoting gap fix)

**Reviewed:** 2026-10-05T13:10:54Z
**Depth:** quick (scoped, with run-the-code checks)
**Files Reviewed:** 1
**Status:** issues_found (Info only; no blocker or warning survives)

## Summary

The diff `e0cd06f..598ab2b` touches only `.readthedocs.yaml`: it replaces the
`post_install` version assertion (line 35) and adds a 3-line comment (lines 32-34).
No other file or line changed.

All four checks were done by running code, not by reading it. The harness is at
`/tmp/claude-1000/-scratch-31-pc2img/8adb4905-a757-44d2-a417-1d0ec8df8e84/scratchpad/rtd/sim.py`.
It loads the real YAML, then runs each command three ways: as plain `sh -c`, with
RTD's wrapping (`/bin/sh -c '<cmd>'` shlex-split the way docker-py splits an exec
string), and with the same wrapping plus RTD's `PATH=...:$PATH;` bin-path prefix.

1. **Semantics match the old intent.** These results were identical in all three modes:
   - real install (`0.10.4.post559`) gives exit 0 and prints `pc2img 0.10.4.post559`
   - a fake `pc2img-0.11.0.dist-info` placed first on `PYTHONPATH` gives exit 0
   - a fake `pc2img-0.0.post7.dist-info` (setuptools_scm's tagless fallback shape under `version_scheme = "post-release"`) gives exit 1 and prints `setuptools_scm-fell-back-to-its-tagless-version` to stderr
   - package missing (`python -I -S`) gives exit 1 with `PackageNotFoundError`, so a missing package fails the job

   `sys.argv` maps to `['-c', 'pc2img', '0.0.', '<msg>']`, so the indices 1/2/3 are correct. The only output changes are cosmetic: the message is hyphenated, and the stdout label is `pc2img <v>` instead of `installed pc2img <v>`.
2. **No quote or escape hazard left.** None of the 6 job commands contains a single quote, backslash or backtick. All 6 come through RTD wrapping byte-identical (`shlex.split(f"/bin/sh -c '{c}'")[2] == c`, asserted for every command). The two `$(...)` uses are meant to be expanded by the inner `sh`, and they already ran fine on RTD build 34944436 (post_checkout passed). The new command's bare argv tokens (`pc2img`, `0.0.`, the hyphenated message) have no glob or shell metacharacters. The old command, run through the same harness, reproduces the RTD failure exactly: exit 2, `Syntax error: Unterminated quoted string`. So the harness models the real failure, and the fix is shown to hold, not just assumed to.
3. **YAML is valid** (`yaml.safe_load`: keys `version/build/sphinx`; jobs post_checkout=2, post_install=2, install=2). Nothing else changed (`git diff --stat`: 1 file, +4/-1).
4. **The comment is accurate.** RTD wraps each job in `/bin/sh -c '...'`. An inner `'` closes that string early, and the next word-split leaves an unterminated `"` for `sh`. That is the failure observed, and the harness confirms it.

## Info

### IN-01: The "no single quotes" rule is documented on one command, but it applies to every job command

**File:** `.readthedocs.yaml:32-34` (applies equally to lines 25-26, 36, 45-46)
**Issue:** The new comment says "No single quotes anywhere in **this** command". The wrapping hazard actually applies to every `build.jobs` entry. The `post_checkout` commands already use `"$(...)"` and are one edit away from the same failure: for example, a future `git describe --match 'v*'` or `grep 'x'` would break them. A local build would not catch it, because the hazard only appears under RTD's wrapping. This is not a defect today, since all 6 commands are clean (verified above), but the invariant is stated more narrowly than it really holds.
**Fix:** Move the sentence up to a single comment directly under `jobs:`, for example:
```yaml
  jobs:
    # Every command below is wrapped by RTD as /bin/sh -c '<command>': never use
    # a single quote in any job command (it ends RTD's quoting -> "Unterminated
    # quoted string"). Use double quotes, or pass strings as argv.
```
and shorten the post_install comment to "Strings are passed as argv (see the jobs: note)."

---

_Reviewed: 2026-10-05T13:10:54Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
