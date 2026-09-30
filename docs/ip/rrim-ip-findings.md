# RRIM (Red Relief Image Map) — Intellectual-Property Findings

**Prepared:** 2026-07-10
**Subject:** `src/pc2img/features/rrim.py` — an image-space implementation of the
red-relief-image visualization technique.
**Status:** Good-faith engineering assessment supporting public redistribution of
`rrim.py` on a patent-expiry basis.

> **Disclaimer — this is not legal advice.** This document is a good-faith
> engineering and patent-status review by the pc2img maintainers. Neither the
> authors nor ETH Zurich are acting as legal counsel here. It records the factual
> patent record (with citations) and a good-faith, explicitly **non-binding**
> non-infringement read. It is not a legal opinion and confers no warranty.

---

## 1. Summary

The visualization technique commonly branded "RRIM" / "Red Relief Image Map"
was invented at **Asia Air Survey Co., Ltd. (AAS)** by **Tatsuro Chiba**, with a
first priority date of **2002-11-05**. The **core patent family** that actually
claims the technique — mapping terrain to a slope-reddened, openness-brightened
2-D image — **has expired in every jurisdiction in which it was granted**
(Japan, China, Taiwan, and the United States). The claimed invention has
therefore entered the **public domain on term expiry**, and it may be practiced
and redistributed by anyone without a license from AAS.

Two AAS patents on **different** inventions remain in force, but a good-faith
claim-by-claim read (Section 4) finds that `rrim.py` — which produces a single
flat 2-D RGB raster with no stereoscopic pair, no CIE L\*a\*b\* second-composite
synthesis, and no super-resolution / elevation-smoothing step — **does not read
on either**.

The "RRIM" name is a separate, **trademark** concern (Section 5) that patent
expiry does not release; it is handled by nominative-use attribution, not by a
rename.

**Redistribution basis: public-domain-on-expiry. No AAS license is required.**

---

## 2. Patent identity

| Field | Value |
|-------|-------|
| Assignee / holder | **Asia Air Survey Co., Ltd.** (アジア航測株式会社) |
| Inventor | **Tatsuro Chiba** |
| First priority | **2002-11-05** |

Sources: Google Patents `US7764282B2` (assignee "Asia Air Survey Co Ltd",
inventor "Tatsuro Chiba", priority 2002-11-05); the AAS official patent page at
`https://www.rrim.jp/en/patent/`.

> **Transcription hazard — cite the correct number.** The RRIM core US member is
> **US 7,764,282 B2**. **US 7,264,282** is an *unrelated thread-knotting patent*
> and must not be cited here. Cross-check every citation against assignee
> "Asia Air Survey" and inventor "Tatsuro Chiba"; a "visualizing system" whose
> abstract discusses thread or knots is the wrong document.

---

## 3. The core patent family is expired (public domain)

The core "Visualizing system, method, and program" invention — the one that
claims the slope-red + (positive − negative) openness-brightness composition
that `rrim.py` implements — was granted in four jurisdictions. **All four members
have expired** as of this writing (2026-07-10):

| Jurisdiction | Patent number | Status |
|--------------|---------------|--------|
| Japan | JP 3670274 | Expired |
| China | CN 1711568B | Expired |
| Taiwan | TW I285852 | Expired |
| United States | **US 7,764,282 B2** | **Expired — Lifetime; adjusted expiration 2025-10-05** |

Sources: AAS official patent page `https://www.rrim.jp/en/patent/` (JP / CN / TW
status); Google Patents `US7764282B2` legal status
(`https://patents.google.com/patent/US7764282B2/en`).

The US member's **adjusted expiration date of 2025-10-05 is already in the past**
relative to today (2026-07-10); Google Patents reports its legal status as
"Expired - Lifetime". A US utility patent with a 2002-11-05 priority reaching
term with a 2025-10-05 adjusted expiration is consistent with the
twenty-years-from-filing rule plus patent-term adjustment. On term expiry the
claimed invention passes into the **public domain**, and no license is needed to
practice or redistribute it.

**Conclusion:** the patent barrier that motivated a publication gate on
`rrim.py` has lapsed. Redistribution rests on public-domain-on-expiry, a basis
that (unlike a research/educational license) carries no field-of-use or
non-commercial restriction.

---

## 4. Still-active AAS patents — good-faith non-infringement read

AAS holds two patents that remain in force, each on a **different invention**.
This section walks the actual independent-claim text of each and maps its
distinguishing limitations to the fact that `rrim.py` performs none of them.

### What `rrim.py` actually computes (verified from source)

1. `compute_slope` — gradient magnitude of the raster (a universal, unpatentable
   primitive).
2. `compute_openness` — positive topographic openness (mean over ray directions
   of `90° − max elevation angle`) and negative openness
   (`90° − max depression angle`), i.e. the Yokoyama et al. (2002) openness
   measures (Section 6).
3. `structure = 0.5 · (positive − negative)` — the ridge/valley
   elevation-depression measure.
4. `compose_rrim_rgb` — normalize `structure` to a base gray brightness, boost
   the **red** channel by normalized slope, and `np.stack((red, base, base))`
   into a **single flat 2-D RGB raster**.

`rrim.py` produces **one plain RGB image**. It does **not** generate a stereo
pair or anaglyph, does **not** map channels into CIE L\*a\*b\* space, does **not**
form a second composite image, and does **not** perform any super-resolution
mesh refinement or elevation-smoothing step.

### 4.1 JP 5281518 — Independent-claim analysis (stereoscopic image generator)

- **Patent:** JP 5281518 B2, "Stereo image generator," assignee Asia Air Survey
  Co., Ltd. **Active — expires 2029-08-25. Japan only.**
- **Source:** `https://patents.google.com/patent/JP5281518B2/en`.
- **Claim quoted:** independent claim 1, in Google Patents' **machine-translated
  English** (labeled as such; the authoritative text is the original Japanese).

> **JP 5281518 B2, claim 1 (machine-translated English, verbatim from Google
> Patents):**
>
> "A point of interest is sequentially defined in the DEM data generated from
> three-dimensional digital data (X, Y, Z) to which an altitude value in a
> predetermined range is assigned, and the ground opening, the underground
> opening, and the slope for each point of interest. Means for obtaining a ground
> opening data group, an underground opening data group, and a gradient data
> group obtained over a certain range; The ground opening image (Dp) assigned a
> brighter color as the value of the ground opening, the underground opening
> image (Dq) assigned a darker color as the value of the underground opening,
> Means for obtaining an inclination-enhanced image (Dr) in which a color in
> which red is enhanced as the value of the degree of inclination is larger for
> each degree data; Means for obtaining a first composite image (Ki) obtained by
> superimposing the ground opening image (Dp), the underground opening image
> (Dq), and the inclination-enhanced image (Dr); Means for reading image data of
> the ground opening image (Dp), and obtaining a data assigned to the a\* channel
> for each reading; Means for reading the image data of the underground opening
> image (Dq), and obtaining b data assigned to the b\* channel for each reading;
> Means for reading out the image data of the tilt-enhanced image (Dr), and
> assigning it to the L\* channel for each reading to obtain L data; Each time the
> a data, b data, and L data are obtained, these data are defined in the
> L\*a\*b\* space so that the ground opening image (Dp) and the underground
> opening image (Dq) and means for obtaining Lab image data (Li) of the
> gradient-enhanced image (Dr), and generating a second composite image (KLi)
> that combines the Lab image (Li) and the first composite image (Ki). A
> stereoscopic image generating apparatus."

**Distinguishing limitations vs. `rrim.py`:** the claim's opening limitations
(ground opening image `Dp`, underground opening image `Dq`, red-enhanced
inclination image `Dr`) resemble the now-expired core composition. What makes
this claim a **different, still-live invention** is the tail: it additionally
requires (a) reading each component image into **CIE L\*a\*b\* channels**
(`Dp → a*`, `Dq → b*`, `Dr → L*`) to form an **Lab image `Li`**, and (b)
**generating a second composite image `KLi`** by combining that Lab image with
the first composite `Ki` — the mechanism that yields the claimed **stereoscopic**
apparatus. `rrim.py` performs neither: it never maps into L\*a\*b\* space and
never forms a second composite; it emits a single flat RGB raster. On a
good-faith read `rrim.py` **does not read on claim 1** — and the patent is in any
event **Japan-only**, whereas the maintainer is ETH Zurich (CH/EU).

### 4.2 US 11,836,856 B2 — Independent-claim analysis (super-resolution stereoscopic visualization)

- **Patent:** US 11,836,856 B2, "Super-resolution stereoscopic visualization
  processing system and program," assignee Asia Air Survey Co., Ltd.
  **Active — expires 2040-07-30. United States only.**
- **Source:** `https://patents.google.com/patent/US11836856B2/en`.
- **Claim quoted:** independent claim 1, **verbatim** English text.

> **US 11,836,856 B2, claim 1 (verbatim from Google Patents):**
>
> "1. A system of super-resolution stereoscopic visualization processing,
> comprising: (A) a logic circuit configured to define a cluster of meshes in a
> plane-rectangular coordinate to store in a plane-rectangular coordinate memory,
> after reading out the meshes, which are represented by latitude and longitude
> of a predetermined area in a digital elevation model, stored in a digital
> elevation model memory; (B) a logic circuit configured to calculate a
> divide-distance, to evenly divide a side along an X direction of each of the
> cluster of the meshes defined in the plane-rectangular coordinate, which is
> stored in the plane-rectangular coordinate memory, into an odd number other
> than one; (C) a logic circuit configured to define a two-dimensional plane
> (X-Y) of an area corresponding to the predetermined area to store in a memory,
> to define a plurality of fine grid-cells, each having a cell size of the
> divide-distance in the two-dimensional plane (X-Y), by dividing the
> two-dimensional plane (X-Y) with the divide-distance; (D) a logic circuit
> configured to determine interpolated elevation-values obtained by interpolating
> elevation-values of the fine grid-cells, by defining the cluster of the meshes
> in the plane-rectangular coordinate on the two-dimensional plane (X-Y); (E1) a
> logic circuit configured to generate smoothing meshes implemented by a cluster
> of smoothing grid-cells, which are two-dimensionally arranged by the odd
> number, by defining grid-cells each having a cell size of the divide-distance
> as the smoothing grid-cells; (E2) a logic circuit configured to sequentially
> designate the fine grid-cells defined in the two-dimensional plane (X-Y),
> defining the smoothing mesh in the two-dimensional plane (X-Y) by allocating a
> central smoothing grid-cell in the smoothing mesh to each of the designated
> fine grid-cells, and to assign smoothing elevation-values to the designated
> fine grid-cells, each of the smoothing elevation-values is obtained by
> smoothing based on interpolated elevation-values of each of the fine grid-cells
> in the smoothing mesh; and (F) a logic circuit configured to specify one of the
> fine grid-cells as a subject point, for each time the smoothing elevation-values
> are assigned to the respective fine grid-cells in the two-dimensional plane
> (X-Y), and to display elevation-depression degrees in gradation, after defining
> consideration distances from the subject point by a cell number of the fine
> grid-cells divided by the divide-distance to determine the elevation-depression
> degrees assigned to each of the subject point."

**Distinguishing limitations vs. `rrim.py`:** every substantive limitation of
this claim is a **super-resolution / elevation-smoothing** step that `rrim.py`
does not perform — (B) computing a **divide-distance** to sub-divide each mesh
into an **odd number** of cells; (C)–(D) defining and **interpolating fine
grid-cells** at that sub-mesh resolution; (E1)–(E2) generating **smoothing
meshes** and assigning **smoothing elevation-values**; (F) using multi-distance
**consideration distances** to render elevation-depression gradation. `rrim.py`
computes openness and slope directly on the input raster at its native
resolution, with no divide-distance sub-mesh, no interpolated fine grid-cells,
no smoothing meshes, and no super-resolution step. On a good-faith read
`rrim.py` **does not read on claim 1** — and the patent is **US-only**.

### 4.3 Read summary

Both still-active AAS patents add limitations `rrim.py` lacks (CIE L\*a\*b\*
second-composite stereoscopic synthesis for JP 5281518; super-resolution +
elevation-smoothing for US 11,836,856), and both are single-jurisdiction (JP and
US respectively). On this good-faith, non-binding read, a flat-RGB openness+slope
implementation such as `rrim.py` does not infringe either.

---

## 5. Trademark note

"**RRIM**" and "**Red Relief Image Map**" function as an **Asia Air Survey brand
(RRIM®)**. A **trademark** is a distinct right that patent expiry does **not**
release. pc2img's use of the term is **nominative / descriptive** — it names an
independent implementation of the published red-relief technique of Chiba et al.
pc2img is **not endorsed by, affiliated with, or sponsored by Asia Air Survey**,
and does not present itself as "RRIM®". The mitigation is attribution, not a
rename: the shipped NOTICE credits AAS / Chiba and states the nominative-use
position.

---

## 6. Openness is independent academic prior art

The brightness ingredient of `rrim.py` — positive and negative **topographic
openness** — is not AAS property. It is an independent academic method:

> **Yokoyama, R., Shirasawa, M., & Pike, R. J. (2002).** "Visualizing Topography
> by Openness: A New Application of Image Processing to Digital Elevation
> Models." *Photogrammetric Engineering & Remote Sensing* **68(3): 257–265.**

Openness has open-source implementations (e.g. the SAGA-GIS Topographic Openness
tool). That the openness primitive predates and is independent of the AAS RRIM
patents further weakens any suggestion that computing openness is proprietary.

Source: `https://www.asprs.org/wp-content/uploads/pers/2002journal/march/2002_mar_257-265.pdf`;
SAGA-GIS tool docs `https://saga-gis.sourceforge.io/saga_tool_doc/9.2.0/ta_lighting_5.html`.

---

## 7. Conclusion

- The **core RRIM patent family is expired** in JP / CN / TW / US; the technique
  `rrim.py` implements is in the **public domain on term expiry**.
- **No AAS license is required** to redistribute `rrim.py`; the redistribution
  basis is public-domain-on-expiry.
- A good-faith, non-binding claim-walk finds `rrim.py` **does not read on** either
  still-active AAS patent (JP 5281518, US 11,836,856).
- The "RRIM" **trademark** is handled by nominative-use attribution in the shipped
  NOTICE, not by a rename.

This supports keeping `rrim.py` in the distribution behind an opt-in extra that
carries the attribution NOTICE. **This assessment is a good-faith engineering
read and is not legal advice.**
