---
status: testing
phase: 03-test-ci-foundation
source: [03-VERIFICATION.md]
started: 2026-07-09T19:48:11Z
updated: 2026-07-09T19:48:11Z
---

## Current Test

number: 1
name: Live first-PR CI run
expected: |
  Opening a real pull request against develop-gsd (or main) causes the CI
  workflow to trigger, run to completion, and report a green pass/fail status
  check on the PR. The `CI / tests` check appears on the PR, installs from the
  frozen lock, runs the scoped suite (15 passed / 11 xfailed), the
  --cov-fail-under=35 gate passes (~37% total), and the check reports success.
awaiting: user response

## Tests

### 1. Live first-PR CI run
expected: Open a real pull request against develop-gsd (or main) and confirm the CI workflow triggers, runs to completion, and reports a green pass/fail status check on the PR. The `CI / tests` check appears, installs from the frozen lock, runs the scoped suite (15 passed / 11 xfailed), the `--cov-fail-under=35` gate passes (~37% total), and the check reports success.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
