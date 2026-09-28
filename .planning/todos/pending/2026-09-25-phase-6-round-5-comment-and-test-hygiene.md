---
created: 2026-09-25T12:00:00Z
title: Round-5 review carry-over — comment accuracy, leftover planning references, test hygiene
area: tests
severity: minor
resolves_phase: 6
files:
  - src/pc2img/image_cache/disk_backed_image_store.py
  - tests/test_image_store.py
  - tests/test_rrim_features.py
  - tests/test_feature_registry.py
  - tests/test_util.py
  - tests/conftest.py
source: 05-REVIEW.md round 5 (c93e045..dc7783d), consolidated as review-r4-* in 05-UAT.md
---

Owner triage 2026-09-25: none of these breaks the intended working path; they are hardening /
wording / hygiene. Deferred on the record instead of a sixth Phase-5 gap round.

- [ ] `review-r4-16ca6d81fd0c` — `__delitem__` docstring history (store :199-202) states a false mechanism
      (an unlink landing before a later ValueError); the real historical loss was in-memory membership.
      Suggested text is in 05-REVIEW.md WR-04.
- [ ] `review-r4-4a993aa1a335` — leftover planning references in shipped comments: test_rrim_features.py:236-237
      (a `.planning/todos` file name), test_feature_registry.py:60-61, test_image_store.py:51 ("Pitfall 6"),
      :439 ("this gap round"), disk_backed_image_store.py:34 ("carry-out"), :95 ("verdict VALIDATED").
      Also extend the sweep gate regex (see 05-REVIEW.md WR-06). Must be clean before the milestone
      squash to main.
- [ ] `review-r4-66d8cfa20681` — test docstring points at `DiskBackedImageData.__init__`; rule now lives in
      `_assert_image_shape`.
- [ ] `review-r4-ba69ab35c32e` — two `# Breadth: replace_nan` headers in tests/test_util.py (:123, :153) now
      parse as code for ruff ERA001; rephrase.
- [ ] `review-r4-84a2b5dff14c` — absent-key delete test is near-subset of the two-store sensor; fold or
      differentiate (e.g. a `.dat`-only peer entry).
- [ ] `review-r4-15a5c4928dc8` — 18 `tmp*` entries leaked per full run from 5 other test modules; add an
      autouse `tempfile.tempdir -> tmp_path` fixture in tests/conftest.py (fits the ruff/CI todo).
