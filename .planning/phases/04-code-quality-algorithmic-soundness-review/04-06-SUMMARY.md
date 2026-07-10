---
phase: 04-code-quality-algorithmic-soundness-review
plan: 06
subsystem: review / mathematical-algorithmic soundness (QUAL-03)
tags: [review, findings, math-audit, refute, numeric-probe, QUAL-03, wave-3]
requires:
  - "04-04 (ruff sweep; stable post-format line numbers; F901 rewrote __array_ufunc__)"
provides:
  - "04-FINDINGS-math.md (refuted, numerically-probed math findings in the D-06 schema)"
  - "04-FINDINGS-math-candidates.md (retained raw FIND-pass output; D-05 evidence)"
  - "math half of the FINDINGS input for 04-07 synthesis -> Phase 5 BUG-05"
affects:
  - "04-07 (synthesis merges design + math FINDINGS halves into canonical 04-FINDINGS.md)"
  - "Phase 5 (BUG-05 fixes: M-01..M-13 are proving-test-ready math inputs; BUG-01 = M-01)"
tech-stack:
  added: []
  patterns:
    - "two-file FIND/REFUTE split as retained adversarial-pass evidence (D-05)"
    - "cheap numpy/scipy numeric probes (5-line) as the decisive refutation instrument"
    - "stable M-* finding ids (no per-finding BUG-05.x IDs, per D-07)"
key-files:
  created:
    - ".planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS-math-candidates.md"
    - ".planning/phases/04-code-quality-algorithmic-soundness-review/04-FINDINGS-math.md"
  modified: []
decisions:
  - "BUG-01 confirmed by BOTH arity (2-tuple vs 4) AND extent/index math: xyz[mask,[0,1]] mixed indexing raises IndexError (M!=2) or silently returns the diagonal (M==2); logged as M-01"
  - "Delaunay over-culling (M-06) reproduced numerically: anisotropic sampling culls 140/468 interior triangles -> NaN holes; barycentric weights themselves proven CORRECT (err 7e-15) and NOT logged"
  - "Hillshade illumination magnitude formula CONFIRMED correct; only the aspect handedness (M-11, consistent 90-deg offset vs ESRI north-up) is logged as suspect/escalate - depends on the raster orientation convention Phase 5 must pin"
  - "nanconv int-dtype candidate DROPPED: np.isnan(int) returns all-False (no raise) under numpy 2.0.2 - honest refutation, not logged"
  - "Perspective Z_c<=0 guard (M-02) and missing translation t (M-03) logged reference-grounded (no standalone numpy probe without pchandler); M-02 flagged for 3rd-tiebreaker escalation per plan"
metrics:
  duration: 12min
  completed: 2026-07-10
status: complete
---

# Phase 04 Plan 06: Math-track Review (QUAL-03) Summary

Ran the QUAL-03 math half of the single orchestrated review (D-03) as a fan-out FIND pass across
the five math module sets (M1 projection, M2 interpolation/culling, M3 util/smoothing, M4
derivative features, M5 rrim) followed by an independent-refuter REFUTE pass driven by cheap
numpy/scipy numeric probes (D-05). Emitted **13 live `M-*` findings** in the D-06 schema, dropped
2 candidates the probes turned into passing counter-probes, and recorded 4 confirmed-correct items
so 04-07 does not re-open them — every `file:line` re-grepped against the live post-04-04 tree, with
the two-file FIND/REFUTE split retained on disk as the adversarial-pass evidence.

## What was built

- **`04-FINDINGS-math-candidates.md`** — retained raw FIND-pass output, grouped M1–M5, pre-refutation
  (D-05 evidence; distinct from the refuted file).
- **`04-FINDINGS-math.md`** — refuted, deduped math findings, most-severe first, each with the full
  D-06 schema (id / file:line / defect / why-wrong+reference / numeric repro / severity / pillar=math /
  LOG disposition / proving-test sketch) **and** the independent refuter's concrete probe verdict
  (inputs → output, survived / dropped / downgraded).

### Findings (most-severe first)

| id | file:line | sev | one-line |
|----|-----------|-----|----------|
| M-01 | projection.py:189/:79 | HIGH | orthographic 2-tuple arity + mixed row/col index (**BUG-01**) |
| M-06 | interpolation.py:221/:225/:233-236 | HIGH | Delaunay culling → interior NaN holes |
| M-02 | projection.py:217 | MED-HIGH | perspective no Z_c≤0 behind-camera guard (escalate) |
| M-07 | util.py:197 | MED | nanconv mutates caller input in place |
| M-08 | util.py:200-203 | MED | nanconv float16 divide overflows to inf |
| M-10 | derivative_features.py:29 | MED | GradientFeature magic-100 spacing |
| M-11 | derivative_features.py:135/:137 | MED | hillshade aspect handedness ~90° off (suspect) |
| M-03 | projection.py:216 | MED | perspective omits translation t |
| M-05 | projection.py:120-121/:82-85 | LOW-MED | spherical azimuth seam / inverted span |
| M-09 | util.py:385 | LOW-MED | convert_to_image all-NaN + normalize → ValueError |
| M-04 | projection.py:195/:216-217 | LOW | perspective dead project_raw + @pcd contract |
| M-12 | derivative_features.py:68/:80-81 | LOW | NormalizedFeature validation commented out |
| M-13 | rrim.py:196-204 | LOW | RRIM ray offsets under-sample near-axis |

### Numeric probes run this session (numpy 2.0.2 / scipy 1.18.0)

- **PROBE-M1a/b (M-01):** `xyz[mask,[0,1]]` → IndexError (M=3) / silent diagonal (M=2); 2-tuple
  unpack → `ValueError: expected 4, got 2`. **SURVIVED.**
- **PROBE-M2a (barycentric):** linear field `2x−3y+1.5` reproduced, max err `7.1e-15`. **CORRECT — not logged.**
- **PROBE-M2b' (M-06):** anisotropic scan sampling culls **140/468 interior triangles** → NaN holes. **SURVIVED.**
- **PROBE-M3b (M-07):** input NaN gone after call → caller corrupted. **SURVIVED.**
- **PROBE-M3d' (M-08):** value 12000 × 7×7 kernel → conv-sum ≈ 588000 → float16 `inf`. **SURVIVED.**
- **PROBE-M3e (M-09):** all-NaN + normalize=True → `ValueError: zero-size array … no identity`. **SURVIVED.**
- **PROBE-M4a (M-10):** unit ramp → `gradient(...,100)=0.01` vs true `1.0`. **SURVIVED.**
- **PROBE-M3' (M-11):** east/south-rising ramps → argmax azimuth consistently 90° off ESRI. **SURVIVED (suspect).**
- **PROBE-M3c (dropped):** `np.isnan(int)` → all-False, no raise. **DROPPED — not logged.**

### Confirmed-CORRECT (explicitly NOT logged as bugs)

Barycentric weights (`interpolation.py:262-265`); hillshade illumination magnitude formula
(`derivative_features.py:141-143`); RRIM differential-openness `structure=0.5·(pos−neg)`
(`rrim.py:376,498`); RRIM positive/negative openness + slope primitives (`rrim.py:219-220,265-291`).

## Deviations from Plan

### Auto-corrections during review (Rule 1 — correctness of the finding record)

- **[Rule 1 — honest refutation] `nanconv` int-dtype candidate dropped.** RESEARCH §3.5 posited int
  input breaks the mask math; the probe showed `np.isnan` on an int array returns all-False under
  numpy 2.0.2 (no raise). Logging it would assert a non-reproducing bug (Pitfall-1). Dropped and
  recorded in the "Dropped/downgraded" section rather than logged.
- **[Rule 1 — honest refutation] Hillshade kept as suspect, not a definite bug.** The illumination
  magnitude formula is provably correct; the 90° aspect offset is only wrong under a north-up raster
  assumption that may not hold for projected range images. Logged M-11 as MEDIUM/suspect with an
  escalation flag instead of overclaiming HIGH.
- **[Rule 1 — Pitfall 1 line-number drift] Interpolation culling anchors re-grepped.** RESEARCH cited
  `:235/:240` for the thresholds; the live post-04-04 tree has them inline in `interpolate()` at
  `:221` (area) and `:225` (aspect). Corrected in M-06. Barycentric-weight anchor corrected to
  `:262-265`. nanconv corrected to `:193-206` (`a[n]=0` at `:197`).

No architectural changes (Rule 4) and no source edits — this is a review/analysis plan that writes
markdown findings only (design-track sibling 04-05 owns the pickle/security surface; math track has
none — T-04-M2 tampering surfaced as M-06/M-07 per the plan threat register).

## Verification

- Task 1: `test -s 04-FINDINGS-math-candidates.md` — pass (10785 bytes).
- Task 2: `test -s 04-FINDINGS-math.md && grep -qiE "orthographic|project_raw"` — pass (21532 bytes);
  Delaunay-culling finding present; confirmed-correct items recorded.
- Two-file FIND/REFUTE split confirmed on disk (D-05 evidence retention).
- All numeric probes above executed against the project `.venv` (numpy 2.0.2, scipy 1.18.0).
- Every `file:line` re-grepped against the live post-04-04 tree (Pitfall 1); drifts corrected.

## Threat surface

Plan threat register T-04-M2 (Tampering / silent data corruption: Delaunay over-culling + nanconv
in-place mutation, disposition=mitigate/log) is surfaced as **M-06** and **M-07** with numeric repros,
fixed-with-a-proving-test in Phase 5 (D-02). No auth/session/network/crypto surface on the math track
(ASVS L1 N/A); the only cataloged security threat (pickle load) belongs to the design track (04-05).
No new security surface introduced (markdown-only outputs).

## Commits

- `843431b` docs(review): FIND-pass math candidates (M1-M5) for QUAL-03
- `2823673` docs(review): refuted math FINDINGS (QUAL-03) for Phase 4

## Notes for 04-07 synthesis

This is the **math half** only. The design half (QUAL-02, `04-FINDINGS-design.md`) is the sibling
plan 04-05; 04-07 merges both into canonical `04-FINDINGS.md`. `M-*` ids are stable and can be carried
forward verbatim (no collision with the design `DSN-*` ids). **M-01 == BUG-01** (orthographic) — a
source-only cross-reference, no pytest xfail encodes it. Escalation flags: **M-02** (perspective Z<0)
and **M-11** (hillshade handedness) are the HIGH-severity disagreements the plan reserves for a
3rd-tiebreaker; both are logged with the empirical/orientation question Phase 5 must resolve.

## Self-Check: PASSED

- Created files verified on disk: `04-FINDINGS-math-candidates.md`, `04-FINDINGS-math.md`, `04-06-SUMMARY.md`.
- Commits verified in git log: `843431b`, `2823673`.
