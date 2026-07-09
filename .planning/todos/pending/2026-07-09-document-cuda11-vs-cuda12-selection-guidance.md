---
created: 2026-07-09T14:04:12.000Z
title: Document how users choose cuda11 vs cuda12 (driver-based) and whether pc2img should carry both extras
area: docs
files:
  - pyproject.toml
  - CONTRIBUTING.md
source: Phase 2 execution decision checkpoint (02-02 universal lock; cuda11/cuda12 conflict resolution)
---

## Problem

Phase 2 resolved the universal-lock conflict between the `cuda11` and `cuda12`
extras by declaring them mutually exclusive via `[tool.uv] conflicts` (option a),
which locks **both** GPU variants and defers the pick to install time
(`pip install pc2img[cuda12]` vs `pc2img[cuda11]`). That is the correct layer for
the choice, but the repo does not yet **tell users how to make it**.

Open guidance questions surfaced during execution:

1. **What is the selection basis?** The choice is governed by the installed NVIDIA
   **driver** (and, on HPC, the cluster's pinned driver/module), not the system CUDA
   toolkit version. RAPIDS/PyTorch wheels bundle their own CUDA runtime and only call
   the driver's `libcuda`; drivers are backward compatible, so a newer driver (e.g.
   CUDA 13) runs older `cu12`/`cu11` wheels — which is why a CUDA-13 box runs `cu12`
   PyTorch fine. GPU compute capability matters only at the extremes.
   → `cuda12` is the right default on any modern driver; `cuda11` is for
   older-driver / older-cluster environments.

2. **Should pc2img even carry both extras?** Project docs note "GPU code paths are
   exercised through pchandler, not directly in pc2img source." The pc2img `cudaXX`
   extras are passthroughs to `pchandler[cudaXX]`. Decide whether maintaining both a
   symmetric `cuda11`/`cuda12` surface is worth it, or whether pc2img should track
   whatever pchandler recommends and document a single default.

## Solution

Add short user-facing guidance (README / CONTRIBUTING / install docs) that:
- States the driver-based selection rule and the "newer driver runs older CUDA
  wheels" backward-compat fact.
- Recommends `cuda12` as the default and explains when to pick `cuda11`.
- Revisits whether both extras should remain, in coordination with pchandler's own
  GPU-extra guidance (pchandler changes require human approval per project constraints).

Possibly warrants a small spike if the pchandler-alignment question turns out to be
non-trivial. Low urgency — the lock already covers both variants correctly.
