# RRIM — ETH/Owner Good-Faith Sign-Off Record

**Prepared:** 2026-07-10
**Subject:** Publication-safety sign-off for `src/pc2img/features/rrim.py` — an
image-space implementation of the red-relief-image visualization technique.
**Status:** Approved / signed off (owner confirmation recorded 2026-07-10).

> **Disclaimer — this is not legal advice.** This record documents an internal,
> good-faith engineering sign-off by the pc2img maintainers / ETH Zurich. It is
> explicitly **non-binding** and does not substitute for, or constitute, legal
> counsel. It records that the responsible owner has reviewed the good-faith
> patent-status assessment and accepts the patent-expiry basis as the grounds for
> public redistribution.

---

## 1. What is being signed off

This record attests the **disposition executed in Phase 03.1**: keep `rrim.py` in
the distribution on a **patent-expiry basis**, behind an opt-in `rrim` extra, with
the shipped attribution `NOTICE`. The executed deliverables are:

- `docs/ip/rrim-ip-findings.md` — the good-faith patent-status review (findings
  doc), with the correct core patent number and the verbatim claim-1
  non-infringement reads for the two still-active AAS patents.
- The top-level `NOTICE` — the shipped legal attribution recording the
  patent-expiry basis, AAS/Chiba attribution, the openness prior-art citation, and
  the nominative-use trademark disclaimer.
- The ADR recording the keep-on-expiry decision.
- The opt-in `rrim` packaging extra.
- The reconciled `rrim.py` docstrings.

## 2. Publication-safety conclusion (plain terms)

- The **core RRIM patent family is expired** in every jurisdiction in which it was
  granted (Japan, China, Taiwan, United States). In particular the US member,
  **US 7,764,282 B2**, has an **adjusted expiration of 2025-10-05**, which is
  already in the past — Google Patents reports its legal status as
  "Expired - Lifetime". The claimed invention has therefore entered the **public
  domain on term expiry** and may be practiced and redistributed by anyone with
  **no AAS license required**.
- Two AAS patents on **different** inventions remain in force — **JP 5281518**
  (stereoscopic image generator, Japan-only, expires 2029-08-25) and
  **US 11,836,856** (super-resolution stereoscopic visualization, US-only, expires
  2040-07-30). A good-faith, non-binding, claim-by-claim read finds that `rrim.py`
  — which emits a single flat 2-D RGB raster with no CIE L\*a\*b\* second-composite
  synthesis and no super-resolution / elevation-smoothing step — **does not read
  on either**.
- The **"RRIM" trademark** is a distinct right that patent expiry does not release;
  it is handled by nominative-use attribution in the shipped `NOTICE`, not by a
  rename.

**Redistribution basis: public-domain-on-expiry. Disposition executed = keep with
NOTICE.**

The full factual basis, with citations and the verbatim still-active-patent claim
reads, is recorded in **`docs/ip/rrim-ip-findings.md`**, and the shipped
attribution is the top-level **`NOTICE`**. This sign-off record attests both.

## 3. Verification state at sign-off

- The CI-equivalent frozen, coverage-gated suite
  (`uv run --frozen pytest --cov=pc2img --cov-branch --cov-report=term-missing
  --cov-fail-under=35`) passes; the coverage floor (35) is unchanged — the keep
  disposition changes no coverage denominator.
- The shipped legal docs (`NOTICE`, `docs/ip/rrim-ip-findings.md`) are VCS-tracked
  and are therefore included in the sdist by setuptools_scm's file finder. (Wheel
  dist-info inclusion is deferred to Phase 6, Publication Hardening.)

---

## 4. Owner / ETH sign-off block

> This block records the responsible owner's acceptance of the patent-expiry
> basis as the publication-safety grounds (D-10). Filling this block clears the
> IP gate so Phase 3's live-CI push can proceed (D-07, resolve-then-push).

| Field    | Value                                          |
|----------|------------------------------------------------|
| Name     | Nicholas Meyer                                 |
| Role     | Owner / maintainer, ETH Zurich GSEG group      |
| Date     | 2026-07-10                                      |
| Approved | approved                                        |

**Sign-off statement (to be affirmed on approval):** I have reviewed the good-faith
patent-status assessment in `docs/ip/rrim-ip-findings.md` and the shipped `NOTICE`,
and I accept the patent-expiry basis as the internal, non-binding good-faith
grounds for publicly redistributing pc2img's RRIM feature.
